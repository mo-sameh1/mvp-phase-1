# Integration Notes With Invalid Reference

Source type: integration mapping notes
System: demo-legacy-system

Supported relationship candidates:

- Case Management System realizes Case Handling Service.
- Case Handling Service serves Permit Review Process.
- Permit Review Process realizes Permit Application Service.

Intentional invalid reference for Epic J:

- Case Handling Service, expected model id `case-handling-service`, serves Archived Permit Review
  Process, expected missing target id `archived-permit-review-process`.

`Archived Permit Review Process` is not described anywhere else in the fixture. The system must not
invent it just to satisfy the relationship. The run should halt before GitHub PR creation, either
when the integration mapper rejects the missing target or when Epic F validation reports a missing
relationship target.

Unsupported candidate that must be skipped unless the ArchiMate metamodel later approves it:

- Audit Publisher flows case submitted events to the reporting data store.
