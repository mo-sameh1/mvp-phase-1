from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol


class ReportModel(Protocol):
    def model_dump(self, *, mode: str = "python") -> dict: ...

    def to_markdown(self) -> str: ...


def report_dir(systems_root: Path, system_id: str, run_id: str) -> Path:
    return systems_root / system_id / "reports" / run_id


def report_pair_paths(systems_root: Path, system_id: str, run_id: str, stem: str) -> list[Path]:
    directory = report_dir(systems_root, system_id, run_id)
    return [directory / f"{stem}.json", directory / f"{stem}.md"]


def write_report_pair(
    *,
    systems_root: Path,
    system_id: str,
    run_id: str,
    stem: str,
    report: ReportModel,
) -> list[Path]:
    json_path, markdown_path = report_pair_paths(systems_root, system_id, run_id, stem)
    directory = json_path.parent
    directory.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(report.to_markdown() + "\n", encoding="utf-8")
    return [json_path, markdown_path]
