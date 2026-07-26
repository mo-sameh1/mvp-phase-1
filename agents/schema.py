from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from agents.archimate_metamodel import is_valid_element_type, list_relationship_types

ArchimateLayer = Literal["motivation", "strategy", "business", "application", "technology"]
ConfidenceLevel = Literal["observed", "inferred"]

SLUG_PATTERN = r"^[a-z0-9][a-z0-9-]*$"


class EvidenceCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: str = Field(min_length=1)
    locator: str = Field(min_length=1)
    excerpt: str = Field(min_length=1)


class RelationshipRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(pattern=SLUG_PATTERN)
    type: str = Field(min_length=1)
    evidence: list[EvidenceCitation] = Field(min_length=1)

    @field_validator("type")
    @classmethod
    def relationship_type_must_be_archimate(cls, value: str) -> str:
        valid_types = set(list_relationship_types())
        if value not in valid_types:
            supported = ", ".join(sorted(valid_types))
            raise ValueError(
                f"Unknown ArchiMate relationship type '{value}'. Supported: {supported}"
            )
        return value


class ModelElement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=SLUG_PATTERN)
    layer: ArchimateLayer
    archimate_type: str = Field(min_length=1)
    name: str = Field(min_length=1)
    documentation: str = Field(min_length=1)
    confidence: ConfidenceLevel
    evidence: list[EvidenceCitation] = Field(min_length=1)
    relationships: list[RelationshipRef] = Field(default_factory=list)

    @model_validator(mode="after")
    def archimate_type_must_match_layer(self) -> ModelElement:
        if not is_valid_element_type(self.layer, self.archimate_type):
            raise ValueError(
                f"ArchiMate type '{self.archimate_type}' is not valid for layer '{self.layer}'"
            )
        return self
