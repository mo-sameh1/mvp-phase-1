---
name: archimate-metamodel
description: Source-grounded ArchiMate 3.2 metamodel vocabulary and conservative relationship validation policy for legacy modernization agents.
---

# ArchiMate Metamodel Skill

Use this skill whenever an agent extracts, classifies, reconciles, or validates ArchiMate elements or relationships.

## Source Of Truth

The primary authority is **The Open Group ArchiMate 3.2 Specification**. The official Open Group N221 reference cards are used as an official cross-check for element names and relationship type definitions.

Structured data files are the validator authority:

- `data/elements.json`
- `data/relationships.json`
- `data/sources.json`

Do not rely on memory, training data, or plausible-sounding enterprise architecture patterns when a rule is not present in the structured data.

## Fail-Closed Policy

- If an element type is not listed for the requested layer, treat it as invalid.
- If a relationship rule is not listed with `review_status = "approved"`, treat it as not established.
- `candidate_examples` are not valid rules. They are review backlog items only.
- Never infer that a relationship is valid because it “sounds right”.
- When uncertain, say: `not established by the ArchiMate metamodel skill`.

## Supported MVP Layers

The MVP uses these ArchiMate 3.2 layers:

- Motivation
- Strategy
- Business
- Application
- Technology

Physical elements listed on the official Technology Layer reference cards are stored under `technology` for this MVP.

## Element Types

Use `agents.archimate_metamodel` utilities or inspect `data/elements.json` for the authoritative vocabulary.

Layer summaries:

- Motivation: Stakeholder, Driver, Assessment, Goal, Outcome, Principle, Requirement, Constraint, Meaning, Value
- Strategy: Resource, Capability, Value Stream, Course of Action
- Business: Business Actor, Business Role, Business Collaboration, Business Interface, Business Process, Business Function, Business Interaction, Business Event, Business Service, Business Object, Contract, Representation, Product
- Application: Application Component, Application Collaboration, Application Interface, Application Function, Application Interaction, Application Process, Application Event, Application Service, Data Object
- Technology: Node, Device, System Software, Technology Collaboration, Technology Interface, Path, Communication Network, Technology Function, Technology Process, Technology Interaction, Technology Event, Technology Service, Artifact, Equipment, Facility, Distribution Network, Material

## Relationship Types

The supported ArchiMate 3.2 relationship vocabulary is:

- Composition
- Aggregation
- Assignment
- Realization
- Serving
- Access
- Influence
- Association
- Triggering
- Flow
- Specialization

The current approved deterministic relationship rule is intentionally conservative:

- `Specialization` is valid only when source and target normalize to the same ArchiMate element type.

All other source-target relationship pairs require extraction and review against the official ArchiMate 3.2 Appendix B normative relationship table before they can be marked approved.

## Required Behavior For Agents

When producing model fragments:

- Use only exact element type names from `data/elements.json`.
- Include evidence citations for every extracted architecture fact.
- Do not create custom element types.
- Do not create custom relationship types.
- Do not validate relationship pairs from intuition.
- Flag unsupported or unknown relationship pairs for human review instead of writing them as valid.

