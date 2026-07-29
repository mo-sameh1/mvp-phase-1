from agents.runtime import deep_agent
from agents.runtime.subagents import PLACEHOLDER_SUBAGENT_NAMES, build_placeholder_subagents
from backend.config.settings import Settings


def test_create_base_agent_passes_runtime_contract(monkeypatch, tmp_path):
    calls = {}
    model = object()
    backend = object()

    def fake_create_deep_agent(**kwargs):
        calls.update(kwargs)
        return "agent"

    monkeypatch.setattr(deep_agent, "build_chat_model", lambda: model)
    monkeypatch.setattr(deep_agent, "build_runtime_backend", lambda paths: backend)
    monkeypatch.setattr(deep_agent, "create_deep_agent", fake_create_deep_agent)

    settings = Settings(
        evidence_root=str(tmp_path / "evidence"),
        model_repo_checkout=str(tmp_path / "model-repo"),
    )

    agent = deep_agent.create_base_agent(settings=settings)

    assert agent == "agent"
    assert calls["model"] is model
    assert calls["backend"] is backend
    assert calls["skills"] == ["/skills/"]
    assert calls["name"] == "phase1-base-agent"
    assert calls["subagents"] is None
    assert calls["permissions"][0].mode == "deny"


def test_placeholder_subagent_names_match_epic_e_contract():
    subagents = build_placeholder_subagents()

    assert [subagent["name"] for subagent in subagents] == PLACEHOLDER_SUBAGENT_NAMES
    assert PLACEHOLDER_SUBAGENT_NAMES == [
        "strategy-analyst",
        "business-analyst",
        "code-analyzer",
        "infra-analyzer",
        "integration-mapper",
    ]
    assert all(
        subagent["system_prompt"] == "Respond with exactly: stub-ok" for subagent in subagents
    )
