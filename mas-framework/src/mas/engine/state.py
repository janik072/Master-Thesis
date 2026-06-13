"""Immutable simulation state management."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class AgentDecision:
    """One agent's decision in one round."""

    agent_id: str
    role_id: str
    round_num: int
    raw_response: str
    decision: str
    reasoning: str
    proposed_value: float | None
    conditions: list[str]
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float
    cached: bool
    timestamp: str


@dataclass(frozen=True)
class RoundState:
    """Immutable snapshot of one round."""

    round_num: int
    decisions: tuple[AgentDecision, ...]
    timestamp: str


@dataclass
class SimulationState:
    """Accumulates RoundStates across the simulation."""

    rounds: list[RoundState] = field(default_factory=list)

    def add_round(self, decisions: list[AgentDecision]) -> RoundState:
        round_state = RoundState(
            round_num=len(self.rounds) + 1,
            decisions=tuple(decisions),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.rounds.append(round_state)
        return round_state

    def get_history_for_agent(
        self,
        agent_id: str,
        visible_decisions: bool = True,
    ) -> list[dict]:
        """Get visible history for an agent's prompt context."""
        history: list[dict] = []
        for round_state in self.rounds:
            for dec in round_state.decisions:
                if dec.agent_id == agent_id:
                    history.append(
                        {
                            "round": dec.round_num,
                            "own_decision": dec.decision,
                            "own_reasoning": dec.reasoning,
                            "own_value": dec.proposed_value,
                        }
                    )
                elif visible_decisions:
                    history.append(
                        {
                            "round": dec.round_num,
                            "agent_label": dec.agent_id,
                            "summary": f"{dec.decision}"
                            + (f" (value: {dec.proposed_value})" if dec.proposed_value else ""),
                        }
                    )
        return history
