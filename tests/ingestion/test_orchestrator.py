from agents.ingestion import orchestrator
from agents.ingestion.profiles import INGESTION_SUBAGENT_NAMES


def test_create_ingestion_orchestrator_wires_real_epic_e_subagents(monkeypatch) -> None:
    calls = {}

    def fake_create_base_agent(**kwargs):
        calls.update(kwargs)
        return "ingestion-agent"

    monkeypatch.setattr(orchestrator, "create_base_agent", fake_create_base_agent)

    agent = orchestrator.create_ingestion_orchestrator()

    assert agent == "ingestion-agent"
    assert [subagent["name"] for subagent in calls["subagents"]] == INGESTION_SUBAGENT_NAMES
    assert "strategy-analyst" in calls["system_prompt"]
    assert "integration-mapper must run last" in calls["system_prompt"]


def test_ingestion_subagent_order_matches_epic_e_sequence() -> None:
    assert orchestrator.ingestion_subagent_order() == INGESTION_SUBAGENT_NAMES
