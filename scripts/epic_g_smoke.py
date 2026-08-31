from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from agents.assembly.reconciler import reconcile_model_tree
from agents.assembly.validator import validate_reconciled_model
from agents.ingestion.fixture_runner import run_fixture_ingestion
from backend.config.settings import Settings, get_settings
from backend.database.session import build_sessionmaker
from backend.gitops.operations import commit_to_model, model_repo_transaction, open_pull_request
from backend.repository.systems import create_legacy_system, get_legacy_system


def main() -> int:
    args = parse_args()
    settings = get_settings()
    missing = _missing_live_config(settings)
    if missing:
        print(f"Missing required Epic G config: {', '.join(missing)}", file=sys.stderr)
        return 1

    repo = Path(settings.model_repo_checkout).expanduser().resolve()
    try:
        with model_repo_transaction(settings) as transaction:
            reconciliation_report_path, validation_report_path = _seed_model_repo(
                settings=settings,
                repo=repo,
                system_id=args.system_id,
                run_id=args.run_id,
            )
            commit_result = commit_to_model(
                settings,
                args.system_id,
                args.run_id,
                transaction=transaction,
            )
            SessionLocal = build_sessionmaker()
            with SessionLocal() as session:
                if get_legacy_system(session, args.system_id) is None:
                    create_legacy_system(
                        session,
                        system_id=args.system_id,
                        name=args.system_id,
                        description="Epic G smoke system.",
                    )
                pr_result = open_pull_request(
                    settings,
                    session,
                    commit_result,
                    validation_report_path,
                    reconciliation_report_path,
                )
                session.commit()
    except Exception as exc:
        print(f"Epic G smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print("Epic G smoke passed")
    print(f"  branch: {commit_result.branch}")
    print(f"  commit_status: {commit_result.status}")
    print(f"  commit_sha: {commit_result.commit_sha}")
    print(f"  pr_status: {pr_result.status}")
    print(f"  pr_number: {pr_result.pr_number}")
    print(f"  pr_url: {pr_result.pr_url}")
    print(f"  artifact_version_id: {pr_result.artifact_version_id}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the live Epic G GitHub PR smoke test.")
    parser.add_argument("--system-id", default=get_settings().model_repo_system_id)
    parser.add_argument("--run-id", default="epic-g-smoke")
    return parser.parse_args()


def _missing_live_config(settings: Settings) -> list[str]:
    checks = {
        "GITHUB_TOKEN": settings.github_token,
        "GITHUB_MODEL_REPO": settings.github_model_repo,
        "MODEL_REPO_CHECKOUT": settings.model_repo_checkout,
    }
    return [
        name
        for name, value in checks.items()
        if not value or value.endswith("_placeholder") or value == "github_pat_placeholder"
    ]


def _seed_model_repo(
    *,
    settings: Settings,
    repo: Path,
    system_id: str,
    run_id: str,
) -> tuple[Path, Path]:
    systems_root = repo / "systems"
    run_fixture_ingestion(
        fixture_root=Path("test-fixtures/epic-e"),
        systems_root=systems_root,
        system_id=system_id,
    )
    epic_f_source = (
        Path("test-fixtures/epic-f") / "reconciliation" / "systems" / settings.model_repo_system_id
    )
    shutil.copytree(epic_f_source, systems_root / system_id, dirs_exist_ok=True)
    reconciliation = reconcile_model_tree(systems_root, system_id, run_id)
    validation = validate_reconciled_model(systems_root, system_id, run_id)
    if validation.status != "passed":
        raise RuntimeError("Seeded Epic G smoke model did not pass Epic F validation")
    return Path(reconciliation.report_paths[0]), Path(validation.report_paths[0])


if __name__ == "__main__":
    raise SystemExit(main())
