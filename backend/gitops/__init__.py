"""Git-backed model repository automation for Epic G."""

from backend.gitops.operations import (
    CommitToModelResult,
    PullRequestResult,
    commit_to_model,
    model_repo_transaction,
    open_pull_request,
)
from backend.gitops.webhooks import WebhookResult, handle_pull_request_webhook

__all__ = [
    "CommitToModelResult",
    "PullRequestResult",
    "WebhookResult",
    "commit_to_model",
    "handle_pull_request_webhook",
    "model_repo_transaction",
    "open_pull_request",
]
