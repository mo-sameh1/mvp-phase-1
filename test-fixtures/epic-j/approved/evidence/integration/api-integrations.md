# Integration Notes

Source type: integration mapping notes
System: demo-legacy-system

Supported relationship candidates:

- Case Management System realizes Case Handling Service.
- Case Handling Service serves Permit Review Process.
- Permit Review Process realizes Permit Application Service.

Unsupported candidate that must be skipped unless the ArchiMate metamodel later approves it:

- Audit Publisher flows case submitted events to the reporting data store.

The approved acceptance run intentionally does not include references to missing target elements.
