from __future__ import annotations

from agents.ingestion.profiles import INGESTION_SUBAGENT_NAMES, build_ingestion_subagents
from agents.runtime.deep_agent import BASE_SYSTEM_PROMPT, create_base_agent

INGESTION_ORCHESTRATOR_PROMPT = BASE_SYSTEM_PROMPT + """

You are orchestrating Epic E ingestion.
Call the ingestion subagents in this order:
1. strategy-analyst
2. business-analyst
3. code-analyzer
4. infra-analyzer
5. integration-mapper

The first four subagents may run independently. The integration-mapper must run last because it
references IDs produced by the other subagents.
After each subagent runs, summarize written elements, skipped candidates, and evidence gaps.
Never proceed past an invalid schema, missing evidence citation, or unsupported ArchiMate rule.

Tool-use contract:
- When using write_todos, each todo must have exactly content and status fields.
- Use status values pending, in_progress, or completed only.
- When using the task tool, copy the system_id, run_id, evidence root, writable model output, and
  systems_root values exactly from the user prompt. Do not shorten UUIDs or replace paths.
- The task description must explicitly tell each subagent which evidence roots it may read and
  that model output must be written only through its assigned ingestion tool.
- Do not ask subagents to write files directly.
"""


def create_ingestion_orchestrator():
    return create_base_agent(
        subagents=build_ingestion_subagents(),
        system_prompt=INGESTION_ORCHESTRATOR_PROMPT,
    )


def ingestion_subagent_order() -> list[str]:
    return list(INGESTION_SUBAGENT_NAMES)
