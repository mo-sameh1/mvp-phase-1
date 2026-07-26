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

The primary authority is The Open Group ArchiMate 3.2 Specification. The Open Group N221 reference cards are used as an official vocabulary cross-check. The provided 7Bots learning PDF is accepted as a project source of truth when it explicitly states MVP relationship examples or element mappings.

The official specification PDF/book should stay outside git, for example in a local ignored `reference/` directory or a personal Downloads folder.

## Validation Policy

The metamodel fails closed:

- unknown element types are invalid
- wrong layer/type pairs are invalid
- unknown relationship types are invalid
- unknown relationship pairs are invalid
- examples not explicitly supported by an accepted source remain invalid until reviewed

Current approved relationship validation is intentionally conservative. It includes same-type `Specialization` plus the explicit relationship examples stated in the 7Bots learning PDF: `Business Role` assigned to `Business Process`, `Application Component` realizes `Application Service`, and `Application Service` serves `Business Process`.

## Python API

```python
from agents.archimate_metamodel import (
    explain_rule,
    is_valid_element_type,
    is_valid_relationship,
    list_element_types,
)
```
