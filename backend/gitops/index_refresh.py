from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from agents.ingestion.model_io import load_model_element
from backend.gitops.local_git import GitRunner, checkout_base_branch, current_commit
from backend.repository.model_elements import (
    delete_model_elements_except,
    upsert_model_element_index,
)


def refresh_model_element_index(
    session: Session,
    *,
    model_repo_checkout: Path,
    github_repo: str,
    github_token: str,
    system_id: str,
    base_branch: str = "main",
) -> int:
    runner = GitRunner(model_repo_checkout, github_repo, github_token)
    checkout_base_branch(runner, base_branch)
    commit_sha = current_commit(runner)
    retained_ids: set[str] = set()
    system_root = model_repo_checkout / "systems" / system_id / "as-is"
    for path in sorted(system_root.glob("*/*.json")) if system_root.exists() else []:
        element = load_model_element(path)
        retained_ids.add(element.id)
        upsert_model_element_index(
            session,
            element_id=element.id,
            system_id=system_id,
            layer=element.layer,
            archimate_type=element.archimate_type,
            name=element.name,
            git_path=str(path.relative_to(model_repo_checkout)),
            current_commit=commit_sha,
        )
    delete_model_elements_except(session, system_id=system_id, retained_ids=retained_ids)
    return len(retained_ids)
