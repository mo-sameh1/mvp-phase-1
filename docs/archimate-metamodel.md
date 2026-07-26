# ArchiMate Metamodel Skill

Epic C introduces a source-grounded ArchiMate 3.2 metamodel foundation.

## Files

```text
agents/skills/archimate-metamodel/SKILL.md
agents/skills/archimate-metamodel/REVIEW_CHECKLIST.md
agents/skills/archimate-metamodel/data/elements.json
agents/skills/archimate-metamodel/data/relationships.json
agents/skills/archimate-metamodel/data/sources.json
agents/archimate_metamodel/
```

## Source Policy

The primary authority is The Open Group ArchiMate 3.2 Specification. The Open Group N221 reference cards are used as an official vocabulary cross-check. The provided 7Bots learning PDF is supporting material only and is not treated as normative authority for relationship validity.

The official specification PDF/book should stay outside git, for example in a local ignored `reference/` directory or a personal Downloads folder.

## Validation Policy

The metamodel fails closed:

- unknown element types are invalid
- wrong layer/type pairs are invalid
- unknown relationship types are invalid
- unknown relationship pairs are invalid
- candidate examples marked `needs_review` are invalid until reviewed against the official Appendix B relationship matrix

Current approved relationship validation is intentionally conservative. It includes same-type `Specialization`; the full Appendix B matrix still requires human extraction and review before Epic E relies on broad relationship validation.

## Python API

```python
from agents.archimate_metamodel import (
    explain_rule,
    is_valid_element_type,
    is_valid_relationship,
    list_element_types,
)
```

