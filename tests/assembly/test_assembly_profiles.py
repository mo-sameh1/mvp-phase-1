from agents.assembly import orchestrator
from agents.assembly.profiles import (
    ASSEMBLY_SUBAGENT_NAMES,
    assembly_subagent_order,
    build_assembly_subagents,
)


def test_assembly_subagent_order_matches_epic_f() -> None:
    assert assembly_subagent_order() == ["reconciler", "validator"]
    assert ASSEMBLY_SUBAGENT_NAMES == ["reconciler", "validator"]


def test_assembly_subagents_have_archimate_skill_and_deterministic_tools() -> None:
    subagents = build_assembly_subagents()

    assert [subagent["name"] for subagent in subagents] == ["reconciler", "validator"]
    assert subagents[0]["skills"] == ["/skills/"]
    assert subagents[1]["skills"] == ["/skills/"]
    assert [tool.name for tool in subagents[0]["tools"]] == ["reconcile_model_tree_tool"]
    assert [tool.name for tool in subagents[1]["tools"]] == ["validate_reconciled_model_tool"]


def test_assembly_subagent_prompts_require_tool_use() -> None:
    for subagent in build_assembly_subagents():
        prompt = subagent["system_prompt"]
        assert "must call" in prompt
        assert "deterministic tool is the authority" in prompt
        assert "free-form reasoning" in prompt


def test_create_assembly_orchestrator_wires_subagents(monkeypatch) -> None:
    calls = {}

    def fake_create_base_agent(**kwargs):
        calls.update(kwargs)
        return "assembly-agent"

    monkeypatch.setattr(orchestrator, "create_base_agent", fake_create_base_agent)

    agent = orchestrator.create_assembly_orchestrator()

    assert agent == "assembly-agent"
    assert [subagent["name"] for subagent in calls["subagents"]] == ["reconciler", "validator"]
    assert "reconciler" in calls["system_prompt"]
    assert "validator" in calls["system_prompt"]
