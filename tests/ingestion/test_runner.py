from __future__ import annotations

from pathlib import Path

import pytest

from agents.ingestion import runner
from agents.ingestion.profiles import INGESTION_SUBAGENT_NAMES
from backend.config.settings import Settings


class FakeAgent:
    def __init__(self, name: str, calls: list[tuple[str, dict, dict]]) -> None:
        self.name = name
        self.calls = calls

    def invoke(self, payload, *, config):
        self.calls.append((self.name, payload, config))
        return {"messages": [{"content": f"{self.name}-ok"}]}


def test_run_ingestion_subagents_uses_python_owned_order(monkeypatch, tmp_path: Path) -> None:
    create_calls = []
    invoke_calls: list[tuple[str, dict, dict]] = []

    def fake_create_base_agent(**kwargs):
        create_calls.append(kwargs)
        return FakeAgent(kwargs["name"], invoke_calls)

    monkeypatch.setattr(runner, "create_base_agent", fake_create_base_agent)

    results = runner.run_ingestion_subagents(
        system_id="demo",
        run_id="run-1",
        evidence_route="/evidence/",
        systems_root=tmp_path / "model" / "systems",
        settings=_settings(tmp_path),
        trace_config_factory=lambda name: {"metadata": {"step": name}},
    )

    assert [result.name for result in results] == INGESTION_SUBAGENT_NAMES
    assert [call["name"] for call in create_calls] == [
        f"epic-e-{name}" for name in INGESTION_SUBAGENT_NAMES
    ]
    assert [call[0] for call in invoke_calls] == [
        f"epic-e-{name}" for name in INGESTION_SUBAGENT_NAMES
    ]
    first_prompt = invoke_calls[0][1]["messages"][0]["content"]
    assert "Do not call task" in first_prompt
    assert "Do not call write_todos" in first_prompt
    assert "write_model_element_tool" in first_prompt
    integration_prompt = invoke_calls[-1][1]["messages"][0]["content"]
    assert "append_model_relationship_tool" in integration_prompt


def test_run_ingestion_subagents_retries_transient_provider_errors(
    monkeypatch,
    tmp_path: Path,
) -> None:
    attempts = {"count": 0}
    first_profile = runner.list_ingestion_profiles()[0]

    class FlakyAgent:
        def invoke(self, payload, *, config):
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise RuntimeError("Internal Server Error (status code: 500)")
            return {"messages": [{"content": "ok"}]}

    monkeypatch.setattr(runner, "list_ingestion_profiles", lambda: [first_profile])
    monkeypatch.setattr(runner, "create_base_agent", lambda **kwargs: FlakyAgent())

    results = runner.run_ingestion_subagents(
        system_id="demo",
        run_id="run-1",
        evidence_route="/evidence/",
        systems_root=tmp_path / "model" / "systems",
        settings=_settings(tmp_path),
        trace_config_factory=lambda name: {"metadata": {"step": name}},
        retry_attempts=2,
    )

    assert attempts["count"] == 2
    assert results[0].attempts == 2


def test_run_ingestion_subagents_wraps_repeated_provider_errors(
    monkeypatch,
    tmp_path: Path,
) -> None:
    first_profile = runner.list_ingestion_profiles()[0]

    class FailingAgent:
        def invoke(self, payload, *, config):
            raise RuntimeError("Internal Server Error (status code: 500)")

    monkeypatch.setattr(runner, "list_ingestion_profiles", lambda: [first_profile])
    monkeypatch.setattr(runner, "create_base_agent", lambda **kwargs: FailingAgent())

    with pytest.raises(runner.IngestionRuntimeError, match="strategy-analyst failed"):
        runner.run_ingestion_subagents(
            system_id="demo",
            run_id="run-1",
            evidence_route="/evidence/",
            systems_root=tmp_path / "model" / "systems",
            settings=_settings(tmp_path),
            trace_config_factory=lambda name: {"metadata": {"step": name}},
            retry_attempts=2,
        )


def _settings(tmp_path: Path) -> Settings:
    evidence_root = tmp_path / "evidence"
    model_repo = tmp_path / "model"
    evidence_root.mkdir(parents=True, exist_ok=True)
    (model_repo / "systems").mkdir(parents=True, exist_ok=True)
    return Settings(
        evidence_root=str(evidence_root),
        model_repo_checkout=str(model_repo),
        github_model_repo="example/repo",
        github_token="token",
        backend_api_key="api-key",
    )
