"""Interaction Orchestrator: the main simulation loop."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import structlog

from mas.engine.state import AgentDecision, SimulationState
from mas.llm.cost import BudgetExceededError, CostTracker
from mas.llm.gateway import LLMGateway
from mas.output.writer import OutputWriter
from mas.prompts.engine import PromptEngine
from mas.schemas.resolved import ResolvedScenario

log = structlog.get_logger()


async def run_simulation(resolved: ResolvedScenario) -> Path:
    """Execute a full simulation and return the output directory."""
    gateway = LLMGateway(resolved.run_config.llm)
    prompt_engine = PromptEngine()
    cost_tracker = CostTracker(
        budget_total_usd=resolved.run_config.cost.budget_total_usd,
        alert_threshold_pct=resolved.run_config.cost.alert_threshold_pct,
        abort_on_exceed=resolved.run_config.cost.abort_on_exceed,
    )
    state = SimulationState()
    writer = OutputWriter(resolved)

    max_rounds = resolved.scenario.interaction.rounds.max

    log.info(
        "simulation_start",
        scenario=resolved.scenario.name,
        agents=len(resolved.agents),
        max_rounds=max_rounds,
    )

    try:
        for round_num in range(1, max_rounds + 1):
            log.info("round_start", round=round_num)
            round_decisions: list[AgentDecision] = []

            for agent in resolved.agents:
                # 1. Build context
                history = state.get_history_for_agent(
                    agent.agent_id,
                    visible_decisions=resolved.scenario.interaction.visibility.decisions,
                )
                other_decisions = [h for h in history if "agent_label" in h]

                # 2. Render prompts
                system_prompt = prompt_engine.render_system_prompt(agent, resolved)
                user_prompt = prompt_engine.render_user_prompt(
                    agent, resolved, round_num, history, other_decisions
                )


                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]

                # 3. LLM call
                llm_response = await gateway.send(messages)

                # 4. Parse response
                decision_data = _parse_decision(llm_response.content)

                # 5. Record cost
                cost_tracker.record_call(
                    agent_id=agent.agent_id,
                    round_num=round_num,
                    model=llm_response.model,
                    input_tokens=llm_response.input_tokens,
                    output_tokens=llm_response.output_tokens,
                    latency_ms=llm_response.latency_ms,
                    cached=llm_response.cached,
                )

                # 6. Create decision record
                agent_decision = AgentDecision(
                    agent_id=agent.agent_id,
                    role_id=agent.role_id,
                    round_num=round_num,
                    raw_response=llm_response.content,
                    decision=decision_data.get("decision", "unknown"),
                    reasoning=decision_data.get("reasoning", ""),
                    proposed_value=decision_data.get("proposed_value"),
                    conditions=decision_data.get("conditions", []),
                    model=llm_response.model,
                    input_tokens=llm_response.input_tokens,
                    output_tokens=llm_response.output_tokens,
                    cost_usd=cost_tracker.calls[-1].cost_usd,
                    latency_ms=llm_response.latency_ms,
                    cached=llm_response.cached,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                round_decisions.append(agent_decision)

                log.info(
                    "agent_decision",
                    agent=agent.agent_id,
                    decision=agent_decision.decision,
                    cost=f"${agent_decision.cost_usd:.4f}",
                )

            # 7. Update state
            state.add_round(round_decisions)

            log.info(
                "round_complete",
                round=round_num,
                total_cost=f"${cost_tracker.total_cost:.4f}",
            )

    except BudgetExceededError as e:
        log.warning("budget_exceeded", error=str(e))

    # Write outputs
    output_dir = writer.write_all(state, cost_tracker)
    log.info(
        "simulation_complete",
        output_dir=str(output_dir),
        total_cost=f"${cost_tracker.total_cost:.4f}",
    )
    return output_dir


def _parse_decision(raw: str) -> dict:
    """Extract JSON decision from LLM response."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        return {
            "decision": "parse_error",
            "reasoning": raw[:500],
            "proposed_value": None,
            "conditions": [],
        }
