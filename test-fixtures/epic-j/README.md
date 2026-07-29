# Epic J End-To-End Acceptance Fixture

This fixture is the small, fictional legacy-system evidence set used for the final Phase 1 demo.
It is safe to commit and contains no client data.

The fixture has two variants:

- `invalid/evidence/`: use first to prove the pipeline fails closed before GitHub PR automation when
  the evidence asks for a relationship to a missing target.
- `approved/evidence/`: use second for the clean acceptance run that opens a PR, gets merged, fires
  the webhook, refreshes the model index, and appears in the frontend.

Both variants cover all five Epic E ingestion subagents:

| Subagent | Evidence folders | What the files exercise |
| --- | --- | --- |
| `strategy-analyst` | `motivation/`, `strategy/` | Drivers, goals, capabilities, and courses of action. |
| `business-analyst` | `business/` | Business actors, services, processes, and an intentional duplicate naming opportunity. |
| `code-analyzer` | `code/` | Application components, application services, APIs, and data objects from code/schema evidence. |
| `infra-analyzer` | `infra/` | Technology nodes, system software, and deployed artifacts from Terraform evidence. |
| `integration-mapper` | `integration/` | Cross-layer relationship candidates with supported, unsupported, and invalid cases. |

## Intentional Edge Cases

1. Duplicate reconciliation opportunity: the business transcript names the same business process as
   `Permit Review Process` and `PermitReviewProcess`. Epic F should merge exact normalized-name
   duplicates only when both are extracted as the same layer and ArchiMate type.
2. Unsupported relationship candidate: the integration notes mention an audit event flow. Epic E/Epic C
   should skip unsupported relationship pairs instead of inventing a rule.
3. Invalid reference demo: `invalid/evidence/integration/api-integrations.md` contains a relationship
   candidate to `Archived Permit Review Process`, which is not present in the evidence. The run should
   halt before PR creation, either when the integration mapper rejects the missing target or when Epic F
   validation detects a missing relationship target.

## Recommended Manual Acceptance Order

1. Set `EVIDENCE_ROOT=test-fixtures/epic-j/invalid/evidence`.
2. Start the backend, frontend, and GitHub webhook tunnel.
3. Trigger ingestion from the frontend with an empty evidence-path field.
4. Confirm the job fails or validation halts without opening a GitHub PR.
5. Clean DB and model repo state.
6. Set `EVIDENCE_ROOT=test-fixtures/epic-j/approved/evidence`.
7. Trigger ingestion from the frontend again.
8. Confirm the job opens a GitHub PR, then merge it in GitHub.
9. Confirm the webhook updates the artifact version to `approved` and the Model page shows indexed elements.

Run J2 twice from a clean DB and clean model repo state for the reliability requirement.
