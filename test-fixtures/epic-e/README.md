# Epic E Synthetic Fixture

This fixture is sanitized demo evidence for Epic E ingestion smoke tests. It exists because Epic J's
full end-to-end evidence set is not implemented yet.

Expected minimum output:

- Motivation: `citizen-access-goal`, `regulatory-compliance-driver`
- Strategy: `digital-case-capability`, `online-service-course-of-action`
- Business: `citizen-applicant`, `permit-review-process`
- Application: `case-management-system`, `case-handling-service`, `case-api`, `case-record`
- Technology: `app-server-node`, `container-runtime`, `case-database-artifact`

Expected relationship behavior:

- `citizen-applicant` assigned to `permit-review-process` is written.
- `case-management-system` realizes `case-handling-service` is written.
- `case-handling-service` serves `permit-review-process` is written.
- The fixture includes one unsupported `Flow` candidate; it must be reported as skipped until Epic C
  approves that source-target relationship pair.
