# Epic F Fixture

Synthetic fixture data for deterministic model assembly.

- `reconciliation/` adds an exact normalized-name duplicate and an ambiguous near-match.
- `broken/` contains deliberately invalid model JSON for validator tests and demonstrations.

Expected reconciliation result:

- `payment-service` remains canonical.
- `paymentservice` is merged into `payment-service`.
- `payment-services` is flagged as ambiguous and not merged.
- Relationships pointing at `paymentservice` are rewritten to `payment-service`.
