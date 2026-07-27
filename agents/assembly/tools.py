from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from agents.assembly.reconciler import reconcile_model_tree
from agents.assembly.validator import validate_reconciled_model


@tool
def reconcile_model_tree_tool(systems_root: str, system_id: str, run_id: str) -> dict[str, Any]:
    """Reconcile duplicate model elements and write reconciliation reports."""
    report = reconcile_model_tree(Path(systems_root), system_id, run_id)
    return report.model_dump(mode="json")


@tool
def validate_reconciled_model_tool(
    systems_root: str,
    system_id: str,
    run_id: str,
) -> dict[str, Any]:
    """Validate reconciled model elements and write validation reports."""
    report = validate_reconciled_model(Path(systems_root), system_id, run_id)
    return report.model_dump(mode="json")
