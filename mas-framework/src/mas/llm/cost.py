"""Cost tracking per LLM call and per run."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import structlog

log = structlog.get_logger()

# Prices per 1M tokens (as of June 2026 — update as needed)
PRICE_TABLE: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "mistral-large-latest": {"input": 2.00, "output": 6.00},
    "mistral-small-latest": {"input": 0.10, "output": 0.30},
    "ollama/llama3:8b": {"input": 0.0, "output": 0.0},
    "ollama/gemma4:latest": {"input": 0.0, "output": 0.0},
}


@dataclass
class CallCost:
    """Cost record for a single LLM call."""

    agent_id: str
    round_num: int
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float
    cached: bool


class BudgetExceededError(Exception):
    pass


@dataclass
class CostTracker:
    """Tracks cumulative costs and enforces budget limits."""

    budget_total_usd: float
    alert_threshold_pct: int = 80
    abort_on_exceed: bool = True
    calls: list[CallCost] = field(default_factory=list)

    @property
    def total_cost(self) -> float:
        return sum(c.cost_usd for c in self.calls)

    @property
    def total_input_tokens(self) -> int:
        return sum(c.input_tokens for c in self.calls)

    @property
    def total_output_tokens(self) -> int:
        return sum(c.output_tokens for c in self.calls)

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        prices = PRICE_TABLE.get(model, {"input": 1.0, "output": 3.0})
        return (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000

    def record_call(
        self,
        agent_id: str,
        round_num: int,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        cached: bool = False,
    ) -> CallCost:
        cost_usd = self.estimate_cost(model, input_tokens, output_tokens)
        call = CallCost(
            agent_id=agent_id,
            round_num=round_num,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            cached=cached,
        )
        self.calls.append(call)

        # Budget check
        if self.budget_total_usd > 0:
            pct = self.total_cost / self.budget_total_usd * 100
            if pct >= 100 and self.abort_on_exceed:
                raise BudgetExceededError(
                    f"Budget exceeded: ${self.total_cost:.4f} / ${self.budget_total_usd}"
                )
            if pct >= self.alert_threshold_pct:
                log.warning("budget_alert", pct=round(pct, 1), total=self.total_cost)

        return call

    def write_cost_log(self, path: Path) -> None:
        with open(path, "w") as f:
            for call in self.calls:
                record = {
                    "agent_id": call.agent_id,
                    "round_num": call.round_num,
                    "model": call.model,
                    "input_tokens": call.input_tokens,
                    "output_tokens": call.output_tokens,
                    "cost_usd": call.cost_usd,
                    "latency_ms": call.latency_ms,
                    "cached": call.cached,
                }
                f.write(json.dumps(record) + "\n")
