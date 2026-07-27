from __future__ import annotations

from agents.assembly.profiles import ASSEMBLY_SUBAGENT_NAMES, build_assembly_subagents
from agents.runtime.deep_agent import BASE_SYSTEM_PROMPT, create_base_agent

ASSEMBLY_ORCHESTRATOR_PROMPT = BASE_SYSTEM_PROMPT + """

You are orchestrating Epic F model assembly after Epic E ingestion.
Call the assembly subagents in this exact order:
1. reconciler
2. validator

Pass the same systems_root, system_id, and run_id values to both subagents. The validator must run
after reconciliation because it validates the reconciled model tree and reports.
"""


def create_assembly_orchestrator():
    return create_base_agent(
        subagents=build_assembly_subagents(),
        system_prompt=ASSEMBLY_ORCHESTRATOR_PROMPT,
    )


def assembly_subagent_order() -> list[str]:
    return list(ASSEMBLY_SUBAGENT_NAMES)
