from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agents.archimate_metamodel import list_element_types
from agents.ingestion.tools import append_model_relationship_tool, write_model_element_tool

INGESTION_SUBAGENT_NAMES = [
    "strategy-analyst",
    "business-analyst",
    "code-analyzer",
    "infra-analyzer",
    "integration-mapper",
]


@dataclass(frozen=True)
class IngestionSubagentProfile:
    name: str
    description: str
    evidence_roots: tuple[str, ...]
    output_layers: tuple[str, ...]
    allowed_types_by_layer: dict[str, tuple[str, ...]]
    system_prompt: str
    tools: tuple[Any, ...]

    def to_subagent(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "skills": ["/skills/"],
            "tools": list(self.tools),
        }


def list_ingestion_profiles() -> list[IngestionSubagentProfile]:
    return [
        _strategy_analyst(),
        _business_analyst(),
        _code_analyzer(),
        _infra_analyzer(),
        _integration_mapper(),
    ]


def get_ingestion_profile(name: str) -> IngestionSubagentProfile:
    for profile in list_ingestion_profiles():
        if profile.name == name:
            return profile
    supported = ", ".join(INGESTION_SUBAGENT_NAMES)
    raise ValueError(f"Unknown ingestion subagent '{name}'. Supported: {supported}")


def build_ingestion_subagents() -> list[dict[str, Any]]:
    return [profile.to_subagent() for profile in list_ingestion_profiles()]


def _strategy_analyst() -> IngestionSubagentProfile:
    layers = ("motivation", "strategy")
    return _profile(
        name="strategy-analyst",
        description=(
            "Extracts Motivation and Strategy ArchiMate elements from strategic plans, "
            "policy/compliance documents, and business cases."
        ),
        evidence_roots=("/evidence/strategy/", "/evidence/motivation/"),
        output_layers=layers,
        allowed_types_by_layer=_allowed(layers),
    )


def _business_analyst() -> IngestionSubagentProfile:
    layers = ("business",)
    return _profile(
        name="business-analyst",
        description=(
            "Extracts Business-layer elements from business documentation, wikis, "
            "and pre-supplied interview transcripts."
        ),
        evidence_roots=("/evidence/business/",),
        output_layers=layers,
        allowed_types_by_layer=_allowed(layers),
    )


def _code_analyzer() -> IngestionSubagentProfile:
    layers = ("application",)
    return _profile(
        name="code-analyzer",
        description=(
            "Extracts Application-layer elements from source code repositories and DB schemas."
        ),
        evidence_roots=("/evidence/code/",),
        output_layers=layers,
        allowed_types_by_layer=_allowed(layers),
        require_line_locators=True,
    )


def _infra_analyzer() -> IngestionSubagentProfile:
    layers = ("technology",)
    return _profile(
        name="infra-analyzer",
        description=(
            "Extracts Technology-layer elements from IaC, CMDB exports, and network configs."
        ),
        evidence_roots=("/evidence/infra/",),
        output_layers=layers,
        allowed_types_by_layer=_allowed(layers),
        require_line_locators=True,
    )


def _integration_mapper() -> IngestionSubagentProfile:
    return _profile(
        name="integration-mapper",
        description=(
            "Extracts cross-layer relationships from API specs and integration documentation, "
            "after E1-E4 have produced elements."
        ),
        evidence_roots=("/evidence/integration/", "/systems/"),
        output_layers=("motivation", "strategy", "business", "application", "technology"),
        allowed_types_by_layer={},
        relationship_only=True,
    )


def _profile(
    *,
    name: str,
    description: str,
    evidence_roots: tuple[str, ...],
    output_layers: tuple[str, ...],
    allowed_types_by_layer: dict[str, tuple[str, ...]],
    require_line_locators: bool = False,
    relationship_only: bool = False,
) -> IngestionSubagentProfile:
    prompt = _system_prompt(
        name=name,
        evidence_roots=evidence_roots,
        output_layers=output_layers,
        allowed_types_by_layer=allowed_types_by_layer,
        require_line_locators=require_line_locators,
        relationship_only=relationship_only,
    )
    return IngestionSubagentProfile(
        name=name,
        description=description,
        evidence_roots=evidence_roots,
        output_layers=output_layers,
        allowed_types_by_layer=allowed_types_by_layer,
        system_prompt=prompt,
        tools=(
            (append_model_relationship_tool,) if relationship_only else (write_model_element_tool,)
        ),
    )


def _allowed(layers: tuple[str, ...]) -> dict[str, tuple[str, ...]]:
    return {layer: tuple(list_element_types(layer)) for layer in layers}


def _system_prompt(
    *,
    name: str,
    evidence_roots: tuple[str, ...],
    output_layers: tuple[str, ...],
    allowed_types_by_layer: dict[str, tuple[str, ...]],
    require_line_locators: bool,
    relationship_only: bool,
) -> str:
    allowed_lines = [
        f"- {layer}: {', '.join(types)}" for layer, types in allowed_types_by_layer.items()
    ]
    if not allowed_lines:
        allowed_lines = ["- This subagent appends relationships to existing model elements only."]

    locator_rule = (
        "Evidence locators for code, schemas, IaC, and CMDB files must include file path plus "
        "line or line range."
        if require_line_locators
        else (
            "Evidence locators must identify the exact document, section, file, or transcript span."
        )
    )
    relationship_rule = (
        "For relationships, reference only target IDs that already exist under /systems/. "
        "Use Serving, Realization, or Flow only when the ArchiMate metamodel skill establishes "
        "the source-target pair. Unsupported candidates must be reported as skipped."
        if relationship_only
        else (
            "For each accepted element, call write_model_element_tool. Do not call write_file "
            "or edit_file for model JSON."
        )
    )
    tool_contract = (
        "Tool contract:\n"
        "- Call append_model_relationship_tool for every accepted relationship candidate.\n"
        "- Pass relationship as an object with target_id, type, and evidence.\n"
        "- relationship.evidence must be a list of citation objects, even when there is only one "
        "citation.\n"
        "- Copy system_id, run_id, and systems_root exactly from the task prompt when passing "
        "them.\n"
        "- Never invent operational paths. systems_root must be the exact absolute path ending "
        "in /systems from the task prompt, never / or /systems/.\n"
        "- If the tool returns skipped, report the candidate in your summary. If the tool rejects "
        "a candidate, stop; the pipeline will fail closed.\n"
        "- Never call write_file or edit_file for relationship updates."
        if relationship_only
        else (
            "Tool contract:\n"
            "- Call write_model_element_tool for every accepted element candidate.\n"
            "- Pass element as an object, not as a markdown block or raw file content.\n"
            "- element.evidence must be a list of citation objects, even when there is only one "
            "citation.\n"
            "- Copy system_id, run_id, and systems_root exactly from the task prompt when passing "
            "them.\n"
            "- Never invent operational paths. systems_root must be the exact absolute path ending "
            "in /systems from the task prompt, never / or /systems/.\n"
            "- The deterministic tool validates agents.schema.ModelElement and serializes JSON.\n"
            "- If the tool rejects a candidate, stop; the pipeline will fail closed.\n"
            "- Never call write_file or edit_file for model JSON."
        )
    )

    return f"""You are the Epic E {name} ingestion subagent.

Use the archimate-metamodel skill before choosing any ArchiMate type or relationship.
Read only these evidence roots: {", ".join(evidence_roots)}.
Allowed output layers: {", ".join(output_layers)}.
Allowed ArchiMate element types:
{chr(10).join(allowed_lines)}

Execution discipline:
- This subagent task is narrow. Do not call write_todos unless the task prompt explicitly asks
  this subagent to create a todo list.
- Preserve the exact system_id, run_id, and systems_root values from the task prompt in tool calls.
- Do not abbreviate UUIDs, rewrite paths, or replace absolute paths with virtual paths.

Output must conform to agents.schema.ModelElement:
- id: stable lowercase slug
- layer: one allowed layer
- archimate_type: exact allowed ArchiMate type
- name and documentation: concise and evidence-grounded
- confidence: observed or inferred
- evidence: non-empty citations with source_type, locator, and excerpt
- relationships: [] for element extraction subagents; relationships are appended only by
  integration-mapper using append_model_relationship_tool

Traceability rules:
- Reject and skip any candidate that lacks a specific evidence excerpt.
- Never invent element types, relationship types, IDs, or source-target relationship validity.
- When a relationship is not established by the metamodel skill, report it as skipped.
- {locator_rule}
- {relationship_rule}

{tool_contract}
"""
