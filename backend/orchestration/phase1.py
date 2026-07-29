from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from agents.assembly.orchestrator import create_assembly_orchestrator
from agents.ingestion.model_io import validate_model_tree
from agents.ingestion.orchestrator import create_ingestion_orchestrator
from agents.runtime.filesystem import RuntimePaths, resolve_runtime_path
from backend.config.settings import Settings
from backend.gitops.operations import (
    CommitToModelResult,
    PullRequestResult,
    commit_to_model,
    open_pull_request,
)


class PipelineError(RuntimeError):
    """Raised when the Phase 1 pipeline must halt before a valid PR is produced."""


@dataclass(frozen=True)
class AsIsIngestionResult:
    system_id: str
    run_id: str
    status: str
    validation_status: str
    reconciliation_report_path: str
    validation_report_path: str
    commit: CommitToModelResult
    pull_request: PullRequestResult

    def model_dump(self) -> dict[str, Any]:
        return {
            "system_id": self.system_id,
            "run_id": self.run_id,
            "status": self.status,
            "validation_status": self.validation_status,
            "reconciliation_report_path": self.reconciliation_report_path,
            "validation_report_path": self.validation_report_path,
            "commit": self.commit.__dict__,
            "pull_request": self.pull_request.__dict__,
        }


def run_as_is_ingestion(
    system_id: str,
    evidence_path: str,
    *,
    run_id: str,
    settings: Settings,
    session: Session,
) -> AsIsIngestionResult:
    paths = RuntimePaths.from_settings(settings)
    resolved_evidence_path = _resolve_evidence_path(evidence_path, paths.evidence_root)
    if not resolved_evidence_path.exists():
        raise PipelineError(f"Evidence path does not exist: {resolved_evidence_path}")
    evidence_route = _evidence_route(resolved_evidence_path, paths.evidence_root)

    _run_ingestion_agent(
        system_id=system_id,
        run_id=run_id,
        evidence_route=evidence_route,
        settings=settings,
    )
    _validate_ingestion_outputs(paths.systems_root, system_id)
    _run_assembly_agent(system_id=system_id, run_id=run_id, systems_root=paths.systems_root)

    reconciliation_report_path = _report_path(
        paths.systems_root,
        system_id,
        run_id,
        "reconciliation",
    )
    validation_report_path = _report_path(paths.systems_root, system_id, run_id, "validation")
    validation = _load_report(validation_report_path)
    validation_status = validation.get("status", "unknown")
    if int(validation.get("total_elements", 0)) < 1:
        raise PipelineError(
            "Epic E produced zero valid model elements; halting before GitHub PR creation."
        )
    if validation_status != "passed":
        raise PipelineError(
            "Epic F validation failed; halting before GitHub PR creation. "
            f"See {validation_report_path}"
        )

    commit_result = commit_to_model(settings, system_id, run_id)
    if not commit_result.pushed:
        raise PipelineError(f"Model commit was not pushed: {commit_result.message}")
    pull_request = open_pull_request(
        settings,
        session,
        commit_result,
        validation_report_path,
        reconciliation_report_path,
    )
    return AsIsIngestionResult(
        system_id=system_id,
        run_id=run_id,
        status="succeeded",
        validation_status=validation_status,
        reconciliation_report_path=str(reconciliation_report_path),
        validation_report_path=str(validation_report_path),
        commit=commit_result,
        pull_request=pull_request,
    )


def _run_ingestion_agent(
    *,
    system_id: str,
    run_id: str,
    evidence_route: str,
    settings: Settings,
) -> None:
    paths = RuntimePaths.from_settings(settings)
    prompt = f"""
Run Epic E ingestion for this Phase 1 As-Is job.

Create and maintain a todo list with these steps:
1. Run strategy-analyst.
2. Run business-analyst.
3. Run code-analyzer.
4. Run infra-analyzer.
5. Run integration-mapper last.

Inputs:
- system_id: {system_id}
- run_id: {run_id}
- evidence root: {evidence_route}
- writable model output: /systems/{system_id}/as-is/
- deterministic systems_root for ingestion tools: {paths.systems_root}

Exact subagent task contract:
- Every task description must include the full system_id: {system_id}
- Every task description must include the full run_id: {run_id}
- Every task description must include this exact systems_root: {paths.systems_root}
- Never shorten, redact, or replace those values.
- Tell each subagent to copy systems_root exactly into write_model_element_tool or
  append_model_relationship_tool calls.

Use the task tool for every ingestion subagent. The first four may run independently, but the
integration-mapper must run after element extraction. All accepted model files must be written under
/systems/{system_id}/as-is/<layer>/ by calling write_model_element_tool. Relationship updates must
be made by calling append_model_relationship_tool. Do not use write_file or edit_file for model
JSON. Stop and report an error if a schema, evidence, path, or ArchiMate rule cannot be satisfied.

When ingestion is complete, reply with exactly: epic-h-ingestion-ok.
"""
    agent = create_ingestion_orchestrator()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config=_trace_config(system_id=system_id, run_id=run_id, step="ingestion"),
    )
    _require_marker(result, "epic-h-ingestion-ok")


def _run_assembly_agent(*, system_id: str, run_id: str, systems_root: Path) -> None:
    prompt = f"""
Run Epic F assembly for this Phase 1 As-Is job.

Create and maintain a todo list with these steps:
1. Run reconciler.
2. Run validator.

Inputs:
- systems_root: {systems_root}
- system_id: {system_id}
- run_id: {run_id}

Use the task tool to call the reconciler subagent first and the validator subagent second. Each
subagent must call its deterministic tool exactly once with the exact values above. If validation
fails, state that downstream GitHub PR creation must halt.

After both subagents finish, reply with exactly: epic-h-assembly-ok.
"""
    agent = create_assembly_orchestrator()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config=_trace_config(system_id=system_id, run_id=run_id, step="assembly"),
    )
    _require_marker(result, "epic-h-assembly-ok")


def _trace_config(*, system_id: str, run_id: str, step: str) -> dict[str, Any]:
    return {
        "configurable": {"thread_id": f"phase1-{system_id}-{run_id}-{step}"},
        "metadata": {"system_id": system_id, "phase": "as-is", "run_id": run_id, "step": step},
        "tags": ["phase1", "as-is", f"system:{system_id}", f"run:{run_id}", f"step:{step}"],
    }


def _resolve_evidence_path(value: str, evidence_root: Path) -> Path:
    if value.startswith("/evidence/") or value == "/evidence":
        relative = value.removeprefix("/evidence/").strip("/")
        return (evidence_root / relative).resolve() if relative else evidence_root.resolve()
    return resolve_runtime_path(value)


def _evidence_route(path: Path, evidence_root: Path) -> str:
    try:
        relative = path.resolve().relative_to(evidence_root.resolve())
    except ValueError as exc:
        raise PipelineError(
            f"Evidence path must be inside configured EVIDENCE_ROOT: {evidence_root}"
        ) from exc
    return "/evidence/" if str(relative) == "." else f"/evidence/{relative.as_posix()}/"


def _report_path(systems_root: Path, system_id: str, run_id: str, report_type: str) -> Path:
    path = systems_root / system_id / "reports" / run_id / f"{report_type}-report.json"
    if not path.exists():
        raise PipelineError(f"Expected Epic F report was not written: {path}")
    return path


def _load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_ingestion_outputs(systems_root: Path, system_id: str) -> None:
    try:
        elements = validate_model_tree(systems_root, system_id)
    except ValueError as exc:
        raise PipelineError(
            f"Epic E wrote invalid model JSON; halting before assembly: {exc}"
        ) from exc
    if not elements:
        raise PipelineError(
            "Epic E produced zero valid model elements; halting before assembly "
            "and GitHub PR creation."
        )


def _require_marker(result: Any, marker: str) -> None:
    text = _latest_text(result)
    if marker not in text:
        raise PipelineError(f"Expected agent marker '{marker}' was missing. Last response: {text}")


def _latest_text(result: Any) -> str:
    messages = result.get("messages", []) if isinstance(result, dict) else []
    if not messages:
        return ""
    latest = messages[-1]
    content = (
        latest.get("content", "") if isinstance(latest, dict) else getattr(latest, "content", "")
    )
    return content if isinstance(content, str) else str(content)
