from __future__ import annotations

import argparse
import os
from pathlib import Path

from agents.ingestion.fixture_runner import (
    FixtureRunResult,
    compare_repeated_counts,
    run_fixture_ingestion,
)
from agents.ingestion.model_io import validate_model_tree
from agents.runtime.filesystem import repository_root


def main() -> int:
    args = parse_args()
    results = []
    for index in range(1, args.repeat + 1):
        result = run_fixture_ingestion(
            fixture_root=args.fixture_root,
            systems_root=args.systems_root,
            system_id=args.system_id,
            repeat_index=index,
        )
        validate_model_tree(args.systems_root, args.system_id)
        results.append(result)
        print_result(result)

    compare_repeated_counts(results, tolerance=1)
    print(f"Epic E smoke passed for {args.repeat} run(s)")
    return 0


def parse_args() -> argparse.Namespace:
    root = repository_root()
    parser = argparse.ArgumentParser(description="Run the deterministic Epic E fixture smoke test.")
    parser.add_argument(
        "--fixture-root",
        type=Path,
        default=root / "test-fixtures" / "epic-e",
    )
    parser.add_argument(
        "--systems-root",
        type=Path,
        default=root / "tmp" / "epic-e-smoke" / "systems",
    )
    parser.add_argument(
        "--system-id",
        default=os.getenv("MODEL_REPO_SYSTEM_ID", "demo-legacy-system"),
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=int(os.getenv("EPIC_E_REPEAT", "1")),
    )
    args = parser.parse_args()
    if args.repeat < 1:
        parser.error("--repeat must be at least 1")
    return args


def print_result(result: FixtureRunResult) -> None:
    print(f"Epic E fixture run {result.repeat_index}")
    print(f"  system_id: {result.system_id}")
    print(f"  systems_root: {result.systems_root}")
    print(f"  elements: {result.element_count}")
    for layer, count in result.element_counts_by_layer.items():
        print(f"  {layer}: {count}")
    written = [decision for decision in result.relationship_decisions if decision.written]
    skipped = [decision for decision in result.relationship_decisions if not decision.written]
    print(f"  relationships_written: {len(written)}")
    for decision in written:
        print(
            f"    wrote {decision.source_id} --{decision.relationship_type}--> "
            f"{decision.target_id}"
        )
    print(f"  relationships_skipped: {len(skipped)}")
    for decision in skipped:
        print(
            f"    skipped {decision.source_id} --{decision.relationship_type}--> "
            f"{decision.target_id}: {decision.reason}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
