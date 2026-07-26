# ArchiMate Metamodel Review Checklist

Use this checklist before Epic E ingestion agents rely on the metamodel for production validation.

## Source Review

- [ ] Confirm the official ArchiMate 3.2 Specification is available to the reviewer.
- [ ] Confirm the repository does not commit the official PDF/book.
- [ ] Confirm every element in `data/elements.json` maps to the official 3.2 specification and N221 reference cards.
- [ ] Confirm every relationship type in `data/relationships.json` maps to the official 3.2 specification and N221 reference cards.

## Relationship Matrix Review

- [ ] Extract Appendix B - Relationships Normative from the official 3.2 specification.
- [ ] Add only source-target relationship pairs that are explicitly present in the official normative table, official generic rules, or the accepted 7Bots ArchiMate learning PDF.
- [ ] Add section/page citations for each approved rule.
- [ ] Keep ambiguous entries as `needs_review`.
- [ ] Confirm `candidate_examples` are not used by `is_valid_relationship`.

## Fail-Closed Review

- [ ] Unknown element types return invalid.
- [ ] Wrong layer/type pairs return invalid.
- [ ] Unknown relationship types return invalid.
- [ ] Unknown relationship source-target pairs return invalid.
- [ ] `needs_review` examples return invalid until approved.

## Human Sign-Off

Reviewer:

Date:

Notes:
