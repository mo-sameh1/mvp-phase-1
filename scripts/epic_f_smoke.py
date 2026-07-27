from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from agents.assembly.orchestrator import create_assembly_orchestrator
from agents.assembly.validator import validate_reconciled_model
from agents.ingestion.fixture_runner import run_fixture_ingestion
from agents.runtime.filesystem import repository_root
from agents.runtime.llm import missing_required_env, selected_provider


def main() -> int:
    args = parse_args()
    missing = _missing_provider_env()
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        return 1

    _seed_smoke_model(args)
    try:
        _run_live_assembly(args)
    except Exception as exc:
        print(f"Epic F live smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    reconciliation = _load_report(args, "reconciliation-report.json")
    validation = _load_report(args, "validation-report.json")
    _assert_smoke_expectations(reconciliation, validation)
    _print_summary(reconciliation, validation)

    if args.include_broken_demo:
        _run_broken_demo(args)

    return 0


def parse_args() -> argparse.Namespace:
    root = repository_root()
    parser = argparse.ArgumentParser(
        description="Run the live Epic F assembly subagent smoke test."
    )
    parser.add_argument(
        "--systems-root",
        type=Path,
        default=root / "tmp" / "epic-f-smoke" / "systems",
    )
    parser.add_argument(
        "--system-id",
        default=os.getenv("MODEL_REPO_SYSTEM_ID", "demo-legacy-system"),
    )
    parser.add_argument("--run-id", default=os.getenv("EPIC_F_RUN_ID", "epic-f-smoke"))
    parser.add_argument("--include-broken-demo", action="store_true")
    return parser.parse_args()


def _missing_provider_env() -> list[str]:
    provider = selected_provider()
    try:
        return missing_required_env(provider)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return ["LLM_PROVIDER"]


def _seed_smoke_model(args: argparse.Namespace) -> None:
    root = repository_root()
    if args.systems_root.exists():
        shutil.rmtree(args.systems_root)
    run_fixture_ingestion(
        fixture_root=root / "test-fixtures" / "epic-e",
        systems_root=args.systems_root,
        system_id=args.system_id,
    )
    source = root / "test-fixtures" / "epic-f" / "reconciliation" / "systems" / args.system_id
    target = args.systems_root / args.system_id
    shutil.copytree(source, target, dirs_exist_ok=True)


def _run_live_assembly(args: argparse.Namespace) -> None:
    prompt = f"""
Run Epic F assembly for this exact model tree.

systems_root: {args.systems_root}
system_id: {args.system_id}
run_id: {args.run_id}

Use the task tool to call the reconciler subagent first.
Then use the task tool to call the validator subagent.
Each subagent must call its deterministic tool exactly once with the exact values above.
After both subagents finish, reply with exactly: epic-f-smoke-ok.
"""
    agent = create_assembly_orchestrator()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config={"configurable": {"thread_id": f"epic-f-smoke-{args.run_id}"}},
    )
    text = _latest_text(result)
    if "epic-f-smoke-ok" not in text:
        raise RuntimeError(f"Missing final smoke marker. Last response: {text}")


def _latest_text(result: Any) -> str:
    messages = result.get("messages", []) if isinstance(result, dict) else []
    if not messages:
        return ""
    latest = messages[-1]
    content = (
        latest.get("content", "") if isinstance(latest, dict) else getattr(latest, "content", "")
    )
    return content if isinstance(content, str) else str(content)


def _load_report(args: argparse.Namespace, filename: str) -> dict[str, Any]:
    path = args.systems_root / args.system_id / "reports" / args.run_id / filename
    if not path.exists():
        raise RuntimeError(f"Expected report was not written: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_smoke_expectations(reconciliation: dict[str, Any], validation: dict[str, Any]) -> None:
    merged_ids = {
        merged_id
        for decision in reconciliation["merge_decisions"]
        for merged_id in decision["merged_ids"]
    }
    if "paymentservice" not in merged_ids:
        raise RuntimeError("Expected paymentservice to be merged during reconciliation")
    ambiguous_ids = {item["right_id"] for item in reconciliation["ambiguous_conflicts"]} | {
        item["left_id"] for item in reconciliation["ambiguous_conflicts"]
    }
    if "payment-services" not in ambiguous_ids:
        raise RuntimeError("Expected payment-services to be flagged as ambiguous")
    if validation["status"] != "passed":
        raise RuntimeError(f"Expected validation to pass, got {validation['status']}")


def _print_summary(reconciliation: dict[str, Any], validation: dict[str, Any]) -> None:
    print("Epic F smoke passed")
    print(f"  merges: {len(reconciliation['merge_decisions'])}")
    print(f"  ambiguous_conflicts: {len(reconciliation['ambiguous_conflicts'])}")
    print(f"  validation_status: {validation['status']}")
    print(f"  validation_violations: {len(validation['violations'])}")


def _run_broken_demo(args: argparse.Namespace) -> None:
    root = repository_root()
    broken_root = root / "tmp" / "epic-f-broken-demo" / "systems"
    if broken_root.exists():
        shutil.rmtree(broken_root)
    source = root / "test-fixtures" / "epic-f" / "broken" / "systems" / args.system_id
    shutil.copytree(source, broken_root / args.system_id, dirs_exist_ok=True)
    report = validate_reconciled_model(broken_root, args.system_id, f"{args.run_id}-broken")
    print(f"Broken fixture validation status: {report.status}")
    print(f"Broken fixture violations: {len(report.violations)}")
    if report.status != "failed":
        raise RuntimeError("Broken fixture demonstration should fail validation")


if __name__ == "__main__":
    raise SystemExit(main())
