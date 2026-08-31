from __future__ import annotations

import json
from contextlib import nullcontext
from pathlib import Path

import pytest

from backend.config.settings import Settings
from backend.gitops.operations import CommitToModelResult, PullRequestResult
from backend.orchestration import phase1
from backend.orchestration.phase1 import PipelineError, run_as_is_ingestion


@pytest.fixture(autouse=True)
def fake_model_repo_transaction(monkeypatch):
    monkeypatch.setattr(
        phase1,
        "model_repo_transaction",
        lambda settings: nullcontext(object()),
    )


def test_run_as_is_ingestion_calls_pipeline_in_order(session, monkeypatch, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_model_element(settings, "demo")
    _write_report(settings, "demo", "run-1", validation_status="passed")
    calls = []
    monkeypatch.setattr(
        phase1,
        "_run_ingestion_agent",
        lambda **kwargs: calls.append(("ingestion", kwargs["system_id"], kwargs["run_id"])),
    )
    monkeypatch.setattr(
        phase1,
        "_run_assembly_agent",
        lambda **kwargs: calls.append(("assembly", kwargs["system_id"], kwargs["run_id"])),
    )
    monkeypatch.setattr(
        phase1,
        "commit_to_model",
        lambda settings, system_id, run_id, transaction: _commit(system_id, run_id),
    )

    def fake_open_pull_request(
        settings,
        session,
        commit_result,
        validation_report_path,
        reconciliation_report_path,
    ):
        return _pull_request(commit_result)

    monkeypatch.setattr(phase1, "open_pull_request", fake_open_pull_request)

    result = run_as_is_ingestion(
        "demo",
        str(Path(settings.evidence_root)),
        run_id="run-1",
        settings=settings,
        session=session,
    )

    assert calls == [("ingestion", "demo", "run-1"), ("assembly", "demo", "run-1")]
    assert result.validation_status == "passed"
    assert result.pull_request.pr_number == 7


def test_run_as_is_ingestion_stops_before_git_when_validation_fails(
    session,
    monkeypatch,
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    _write_model_element(settings, "demo")
    _write_report(settings, "demo", "run-1", validation_status="failed")
    monkeypatch.setattr(phase1, "_run_ingestion_agent", lambda **kwargs: None)
    monkeypatch.setattr(phase1, "_run_assembly_agent", lambda **kwargs: None)
    git_calls = []
    monkeypatch.setattr(
        phase1,
        "commit_to_model",
        lambda settings, system_id, run_id, transaction: git_calls.append(run_id),
    )

    with pytest.raises(PipelineError, match="validation failed"):
        run_as_is_ingestion(
            "demo",
            str(Path(settings.evidence_root)),
            run_id="run-1",
            settings=settings,
            session=session,
        )

    assert git_calls == []


def test_run_as_is_ingestion_stops_before_assembly_when_ingestion_writes_no_elements(
    session,
    monkeypatch,
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    monkeypatch.setattr(phase1, "_run_ingestion_agent", lambda **kwargs: None)
    assembly_calls = []
    monkeypatch.setattr(
        phase1,
        "_run_assembly_agent",
        lambda **kwargs: assembly_calls.append(kwargs["run_id"]),
    )

    with pytest.raises(PipelineError, match="zero valid model elements"):
        run_as_is_ingestion(
            "demo",
            str(Path(settings.evidence_root)),
            run_id="run-1",
            settings=settings,
            session=session,
        )

    assert assembly_calls == []


def test_run_as_is_ingestion_stops_before_git_when_validation_has_zero_elements(
    session,
    monkeypatch,
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    _write_model_element(settings, "demo")
    _write_report(settings, "demo", "run-1", validation_status="passed", total_elements=0)
    monkeypatch.setattr(phase1, "_run_ingestion_agent", lambda **kwargs: None)
    monkeypatch.setattr(phase1, "_run_assembly_agent", lambda **kwargs: None)
    git_calls = []
    monkeypatch.setattr(
        phase1,
        "commit_to_model",
        lambda settings, system_id, run_id, transaction: git_calls.append(run_id),
    )

    with pytest.raises(PipelineError, match="zero valid model elements"):
        run_as_is_ingestion(
            "demo",
            str(Path(settings.evidence_root)),
            run_id="run-1",
            settings=settings,
            session=session,
        )

    assert git_calls == []


def test_run_as_is_ingestion_rejects_missing_evidence_path(session, tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    with pytest.raises(PipelineError, match="Evidence path does not exist"):
        run_as_is_ingestion(
            "demo",
            str(tmp_path / "missing"),
            run_id="run-1",
            settings=settings,
            session=session,
        )


def test_trace_config_contains_run_metadata() -> None:
    config = phase1._trace_config(system_id="demo", run_id="run-1", step="ingestion")

    assert config["configurable"]["thread_id"] == "phase1-demo-run-1-ingestion"
    assert config["metadata"] == {
        "system_id": "demo",
        "phase": "as-is",
        "run_id": "run-1",
        "step": "ingestion",
    }


def test_ingestion_prompt_contains_strict_subagent_task_contract(
    monkeypatch,
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    captured = {}

    class FakeAgent:
        def invoke(self, payload, config):
            captured["prompt"] = payload["messages"][0]["content"]
            captured["config"] = config
            return {"messages": [{"content": "epic-h-ingestion-ok"}]}

    monkeypatch.setattr(phase1, "create_ingestion_orchestrator", lambda: FakeAgent())

    phase1._run_ingestion_agent(
        system_id="demo",
        run_id="as-is-12345678-abcd-4321-abcd-123456789abc",
        evidence_route="/evidence/",
        settings=settings,
    )

    assert "Exact subagent task contract" in captured["prompt"]
    assert "as-is-12345678-abcd-4321-abcd-123456789abc" in captured["prompt"]
    assert str(Path(settings.model_repo_checkout) / "systems") in captured["prompt"]
    assert "Never shorten, redact, or replace those values" in captured["prompt"]


def test_ingestion_agent_rejected_tool_event_halts_pipeline(monkeypatch, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    events = (
        Path(settings.model_repo_checkout)
        / "systems"
        / "demo"
        / "reports"
        / "run-1"
        / "ingestion-tool-events.jsonl"
    )
    events.parent.mkdir(parents=True)
    events.write_text(
        json.dumps(
            {
                "tool": "append_model_relationship_tool",
                "status": "rejected",
                "written": False,
                "source_id": "case-handling-service",
                "reason": "Relationship target id 'missing-process' does not exist",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    class FakeAgent:
        def invoke(self, payload, config):
            return {"messages": [{"content": "epic-h-ingestion-ok"}]}

    monkeypatch.setattr(phase1, "create_ingestion_orchestrator", lambda: FakeAgent())

    with pytest.raises(PipelineError, match="ingestion tool rejected"):
        phase1._run_ingestion_agent(
            system_id="demo",
            run_id="run-1",
            evidence_route="/evidence/",
            settings=settings,
        )


def _settings(tmp_path: Path) -> Settings:
    evidence_root = tmp_path / "evidence"
    model_repo = tmp_path / "model"
    evidence_root.mkdir(parents=True)
    (model_repo / "systems").mkdir(parents=True)
    return Settings(
        evidence_root=str(evidence_root),
        model_repo_checkout=str(model_repo),
        github_model_repo="example/repo",
        github_token="token",
        backend_api_key="api-key",
    )


def _write_report(
    settings: Settings,
    system_id: str,
    run_id: str,
    *,
    validation_status: str,
    total_elements: int = 1,
) -> None:
    report_dir = Path(settings.model_repo_checkout) / "systems" / system_id / "reports" / run_id
    report_dir.mkdir(parents=True)
    (report_dir / "reconciliation-report.json").write_text(
        json.dumps({"status": "completed"}),
        encoding="utf-8",
    )
    (report_dir / "validation-report.json").write_text(
        json.dumps({"status": validation_status, "total_elements": total_elements}),
        encoding="utf-8",
    )


def _write_model_element(settings: Settings, system_id: str) -> None:
    model_path = (
        Path(settings.model_repo_checkout)
        / "systems"
        / system_id
        / "as-is"
        / "business"
        / "permit-review-process.json"
    )
    model_path.parent.mkdir(parents=True)
    model_path.write_text(
        json.dumps(
            {
                "id": "permit-review-process",
                "layer": "business",
                "archimate_type": "Business Process",
                "name": "Permit Review Process",
                "documentation": "The permit review process checks applications.",
                "confidence": "observed",
                "evidence": [
                    {
                        "source_type": "fixture",
                        "locator": "/evidence/business/interview-transcript.md:1",
                        "excerpt": "The permit review process checks applications.",
                    }
                ],
                "relationships": [],
            }
        ),
        encoding="utf-8",
    )


def _commit(system_id: str, run_id: str) -> CommitToModelResult:
    return CommitToModelResult(
        system_id=system_id,
        run_id=run_id,
        branch=f"feature/ingest-{system_id}-{run_id}",
        commit_sha="sha",
        status="pushed",
        pushed=True,
        message="ok",
    )


def _pull_request(commit: CommitToModelResult) -> PullRequestResult:
    return PullRequestResult(
        system_id=commit.system_id,
        run_id=commit.run_id,
        branch=commit.branch,
        commit_sha=commit.commit_sha,
        pr_number=7,
        pr_url="https://github.com/example/repo/pull/7",
        artifact_version_id="artifact-1",
        status="created",
    )
