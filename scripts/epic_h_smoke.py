from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient

from agents.runtime.llm import missing_required_env, selected_provider
from backend.api.app import create_app
from backend.config.settings import Settings, get_settings
from backend.database.session import build_sessionmaker
from backend.repository.artifacts import list_artifact_versions
from backend.repository.jobs import get_job


def main() -> int:
    args = parse_args()
    settings = get_settings()
    missing = _missing_live_config(settings)
    if missing:
        print(f"Missing required Epic H config: {', '.join(missing)}", file=sys.stderr)
        return 1

    evidence_path = args.evidence_path or settings.evidence_root
    if not Path(evidence_path).expanduser().resolve().exists():
        print(f"Evidence path does not exist: {evidence_path}", file=sys.stderr)
        return 1

    client = TestClient(create_app())
    response = client.post(
        f"/systems/{args.system_id}/ingest",
        headers={"X-API-Key": settings.backend_api_key},
        json={"evidence_path": evidence_path},
    )
    if response.status_code != 202:
        print(f"Epic H API trigger failed: {response.status_code} {response.text}", file=sys.stderr)
        return 1

    payload = response.json()
    job = _wait_for_terminal_job(settings, payload["job_id"], timeout_seconds=args.timeout_seconds)
    if job is None:
        print(f"Epic H job did not finish before timeout: {payload['job_id']}", file=sys.stderr)
        return 1
    if job.status != "succeeded":
        print(f"Epic H job failed: {job.error_message}", file=sys.stderr)
        return 1

    artifacts = _artifacts_for_run(settings, args.system_id, job.run_id)
    latest = artifacts[0] if artifacts else None

    print("Epic H smoke passed")
    print(f"  job_id: {job.id}")
    print(f"  status: {job.status}")
    print(f"  run_id: {job.run_id}")
    if latest is not None:
        print(f"  commit_sha: {latest.commit_sha}")
        print(f"  pr_number: {latest.pr_number}")
        print(f"  pr_url: {latest.pr_url}")
        print(f"  approval_status: {latest.approval_status}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the live Epic H API orchestration smoke test."
    )
    parser.add_argument("--system-id", default=get_settings().model_repo_system_id)
    parser.add_argument("--evidence-path")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    return parser.parse_args()


def _missing_live_config(settings: Settings) -> list[str]:
    missing = []
    for name, value in {
        "BACKEND_API_KEY": settings.backend_api_key,
        "GITHUB_TOKEN": settings.github_token,
        "GITHUB_MODEL_REPO": settings.github_model_repo,
        "MODEL_REPO_CHECKOUT": settings.model_repo_checkout,
        "EVIDENCE_ROOT": settings.evidence_root,
    }.items():
        if not value or value.endswith("_placeholder"):
            missing.append(name)

    try:
        provider = selected_provider()
        missing.extend(missing_required_env(provider))
    except ValueError as exc:
        missing.append(str(exc))
    return missing


def _wait_for_terminal_job(settings: Settings, job_id: str, *, timeout_seconds: int):
    deadline = time.monotonic() + timeout_seconds
    SessionLocal = build_sessionmaker(settings.database_url)
    while time.monotonic() < deadline:
        with SessionLocal() as session:
            job = get_job(session, job_id)
            if job is not None and job.status in {"succeeded", "failed"}:
                return job
        time.sleep(2)
    return None


def _artifacts_for_run(settings: Settings, system_id: str, run_id: str | None):
    SessionLocal = build_sessionmaker(settings.database_url)
    with SessionLocal() as session:
        artifacts = list_artifact_versions(session, system_id=system_id)
        return [artifact for artifact in artifacts if artifact.run_id == run_id]


if __name__ == "__main__":
    raise SystemExit(main())
