from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_pr_description(
    *,
    system_id: str,
    run_id: str,
    commit_sha: str,
    validation_report_path: Path,
    reconciliation_report_path: Path,
) -> str:
    validation = _load_report(validation_report_path)
    reconciliation = _load_report(reconciliation_report_path)
    lines = [
        f"# As-Is Model Update: {system_id}",
        "",
        f"- Run ID: `{run_id}`",
        f"- Commit SHA: `{commit_sha}`",
        f"- Validation status: `{validation.get('status', 'unknown')}`",
        f"- Elements: `{validation.get('total_elements', 0)}`",
        f"- Relationships: `{validation.get('total_relationships', 0)}`",
        "",
        "## Counts By Layer",
        "",
    ]
    for layer, count in validation.get("counts_by_layer", {}).items():
        lines.append(f"- `{layer}`: {count}")

    lines.extend(["", "## Validation Violations", ""])
    violations = validation.get("violations", [])
    if not violations:
        lines.append("- None")
    for violation in violations:
        lines.append(f"- `{violation.get('code', 'unknown')}`: {violation.get('message', '')}")

    lines.extend(["", "## Reconciliation", ""])
    lines.append(f"- Merges: `{len(reconciliation.get('merge_decisions', []))}`")
    conflicts = reconciliation.get("ambiguous_conflicts", [])
    lines.append(f"- Ambiguous conflicts: `{len(conflicts)}`")
    for conflict in conflicts:
        lines.append(
            f"- Review `{conflict.get('left_id')}` vs `{conflict.get('right_id')}` "
            f"({conflict.get('similarity')})"
        )

    return "\n".join(lines)


def _load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
