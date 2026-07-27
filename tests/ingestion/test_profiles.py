from agents.archimate_metamodel import list_element_types
from agents.ingestion.profiles import (
    INGESTION_SUBAGENT_NAMES,
    build_ingestion_subagents,
    get_ingestion_profile,
    list_ingestion_profiles,
)


def test_ingestion_subagent_names_match_epic_e_order() -> None:
    profiles = list_ingestion_profiles()

    assert [profile.name for profile in profiles] == INGESTION_SUBAGENT_NAMES
    assert INGESTION_SUBAGENT_NAMES == [
        "strategy-analyst",
        "business-analyst",
        "code-analyzer",
        "infra-analyzer",
        "integration-mapper",
    ]


def test_profiles_declare_required_evidence_roots_and_layers() -> None:
    assert get_ingestion_profile("strategy-analyst").evidence_roots == (
        "/evidence/strategy/",
        "/evidence/motivation/",
    )
    assert get_ingestion_profile("strategy-analyst").output_layers == (
        "motivation",
        "strategy",
    )
    assert get_ingestion_profile("business-analyst").output_layers == ("business",)
    assert get_ingestion_profile("code-analyzer").output_layers == ("application",)
    assert get_ingestion_profile("infra-analyzer").output_layers == ("technology",)
    assert get_ingestion_profile("integration-mapper").evidence_roots == (
        "/evidence/integration/",
        "/systems/",
    )


def test_profile_allowed_types_are_derived_from_epic_c_metamodel() -> None:
    expected_layers_by_profile = {
        "strategy-analyst": ("motivation", "strategy"),
        "business-analyst": ("business",),
        "code-analyzer": ("application",),
        "infra-analyzer": ("technology",),
    }

    for profile_name, layers in expected_layers_by_profile.items():
        profile = get_ingestion_profile(profile_name)
        assert profile.allowed_types_by_layer == {
            layer: tuple(list_element_types(layer)) for layer in layers
        }


def test_prompts_include_grounding_and_fail_closed_rules() -> None:
    for profile in list_ingestion_profiles():
        prompt = profile.system_prompt

        assert "archimate-metamodel skill" in prompt
        assert "agents.schema.ModelElement" in prompt
        assert "Reject and skip any candidate that lacks a specific evidence excerpt" in prompt
        assert "Never invent element types, relationship types, IDs" in prompt

    assert "line or line range" in get_ingestion_profile("code-analyzer").system_prompt
    assert "line or line range" in get_ingestion_profile("infra-analyzer").system_prompt
    integration_prompt = get_ingestion_profile("integration-mapper").system_prompt
    assert "target IDs that already exist" in integration_prompt
    assert "reported as skipped" in integration_prompt


def test_build_ingestion_subagents_returns_deep_agent_ready_profiles() -> None:
    subagents = build_ingestion_subagents()

    assert [subagent["name"] for subagent in subagents] == INGESTION_SUBAGENT_NAMES
    for subagent in subagents:
        assert subagent["skills"] == ["/skills/"]
        assert subagent["system_prompt"]
        assert subagent["description"]
