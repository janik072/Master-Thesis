"""Jinja2-based prompt rendering engine."""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from mas.schemas.resolved import ResolvedAgent, ResolvedScenario


class PromptEngine:
    def __init__(self, template_dir: Path | None = None):
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(default=False),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_system_prompt(
        self,
        agent: ResolvedAgent,
        scenario: ResolvedScenario,
    ) -> str:
        template = self.env.get_template("system.j2")
        return template.render(
            agent=agent,
            persona=agent.persona,
            scenario=scenario.scenario,
        )

    def render_user_prompt(
        self,
        agent: ResolvedAgent,
        scenario: ResolvedScenario,
        round_num: int,
        history: list[dict],
        other_decisions: list[dict],
    ) -> str:
        template = self.env.get_template("user_decision.j2")
        return template.render(
            agent=agent,
            persona=agent.persona,
            scenario=scenario.scenario,
            round_num=round_num,
            max_rounds=scenario.scenario.interaction.rounds.max,
            history=history,
            other_decisions=other_decisions,
            incentives=scenario.scenario.incentives,
        )
