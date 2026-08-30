from __future__ import annotations

from typing import Any

from agents.assembly.tools import reconcile_model_tree_tool, validate_reconciled_model_tool

ASSEMBLY_SUBAGENT_NAMES = ["reconciler", "validator"]


def assembly_subagent_order() -> list[str]:
    return list(ASSEMBLY_SUBAGENT_NAMES)


def build_assembly_subagents() -> list[dict[str, Any]]:
    return [_reconciler_subagent(), _validator_subagent()]


def _reconciler_subagent() -> dict[str, Any]:
    return {
        "name": "reconciler",
        "description": (
            "Runs Epic F1 deterministic model reconciliation after ingestion writes model JSON."
        ),
        "system_prompt": _reconciler_prompt(),
        "skills": ["/skills/"],
        "tools": [reconcile_model_tree_tool],
    }


def _validator_subagent() -> dict[str, Any]:
    return {
        "name": "validator",
        "description": (
            "Runs Epic F2 deterministic schema, evidence, and ArchiMate validation reports."
        ),
        "system_prompt": _validator_prompt(),
        "skills": ["/skills/"],
        "tools": [validate_reconciled_model_tool],
    }


def _reconciler_prompt() -> str:
    return """You are the Epic F1 reconciler subagent.

You must call reconcile_model_tree_tool exactly once with the provided systems_root, system_id, and
run_id. Do not make merge decisions from free-form reasoning.

The deterministic tool is the authority for:
- normalized-name duplicate matching
- canonical ID selection
- evidence retention
- relationship target rewriting
- ambiguous conflict reporting

After the tool returns, summarize the report paths, merge count, ambiguous conflict count, and
before/after element counts. Do not claim that ambiguous conflicts were merged.
"""


def _validator_prompt() -> str:
    return """You are the Epic F2 validator subagent.

You must call validate_reconciled_model_tool exactly once with the provided systems_root, system_id,
and run_id. Do not decide schema, evidence, or ArchiMate validity from free-form reasoning.

The deterministic tool is the authority for:
- schema validation
- evidence validation
- ArchiMate layer/type validation
- relationship target validation
- relationship source-target metamodel validation
- JSON and Markdown report writing

After the tool returns, summarize the report paths, validation status, element counts, relationship
count, and violation count. If status is failed, state that downstream PR creation must halt.
"""
