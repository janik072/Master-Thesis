"""Structured output generation: JSONL logs, manifest, summary."""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from mas.engine.state import SimulationState
from mas.llm.cost import CostTracker
from mas.schemas.resolved import ResolvedScenario


class OutputWriter:
    def __init__(self, resolved: ResolvedScenario):
        self.resolved = resolved

    def _create_output_dir(self) -> Path:
        base = Path(self.resolved.run_config.output.base_dir)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        run_dir = base / f"{self.resolved.config_hash}_{timestamp}"
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def write_all(self, state: SimulationState, cost_tracker: CostTracker) -> Path:
        output_dir = self._create_output_dir()

        self._write_decisions(output_dir, state)
        cost_tracker.write_cost_log(output_dir / "cost_log.jsonl")
        self._write_manifest(output_dir)
        self._write_summary(output_dir, state, cost_tracker)

        return output_dir

    def _write_decisions(self, output_dir: Path, state: SimulationState) -> None:
        with open(output_dir / "decisions.jsonl", "w") as f:
            for round_state in state.rounds:
                for dec in round_state.decisions:
                    f.write(json.dumps(asdict(dec)) + "\n")

    def _write_manifest(self, output_dir: Path) -> None:
        manifest = {
            "config_hash": self.resolved.config_hash,
            "scenario_id": self.resolved.scenario.id,
            "seed": self.resolved.run_config.seed,
            "framework_version": "0.1.0",
            "python_version": sys.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_count": len(self.resolved.agents),
            "default_model": self.resolved.run_config.llm.default_model,
        }
        with open(output_dir / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)

    def _write_summary(
        self,
        output_dir: Path,
        state: SimulationState,
        cost_tracker: CostTracker,
    ) -> None:
        summary: dict = {
            "total_rounds": len(state.rounds),
            "total_cost_usd": round(cost_tracker.total_cost, 6),
            "total_input_tokens": cost_tracker.total_input_tokens,
            "total_output_tokens": cost_tracker.total_output_tokens,
            "total_calls": len(cost_tracker.calls),
            "per_agent": {},
        }
        for agent in self.resolved.agents:
            agent_decisions = [
                d
                for r in state.rounds
                for d in r.decisions
                if d.agent_id == agent.agent_id
            ]
            summary["per_agent"][agent.agent_id] = {
                "decisions": [d.decision for d in agent_decisions],
                "total_cost": round(sum(d.cost_usd for d in agent_decisions), 6),
            }
        with open(output_dir / "run_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
