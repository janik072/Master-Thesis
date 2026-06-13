"""Tests for the Jinja2 prompt engine."""
from pathlib import Path

from mas.engine.scenario_engine import build_resolved_scenario
from mas.prompts.engine import PromptEngine

CONFIGS = Path(__file__).parent.parent / "configs"


def test_system_prompt_renders():
    resolved = build_resolved_scenario(
        CONFIGS / "scenarios" / "minimal.yaml",
        CONFIGS / "personas",
        CONFIGS / "run_configs" / "dev.yaml",
    )
    engine = PromptEngine()
    agent = resolved.agents[0]
    prompt = engine.render_system_prompt(agent, resolved)

    assert agent.persona.label in prompt
    assert agent.persona.background in prompt
    assert "JSON" in prompt


def test_user_prompt_renders():
    resolved = build_resolved_scenario(
        CONFIGS / "scenarios" / "minimal.yaml",
        CONFIGS / "personas",
        CONFIGS / "run_configs" / "dev.yaml",
    )
    engine = PromptEngine()
    agent = resolved.agents[0]
    prompt = engine.render_user_prompt(
        agent=agent,
        scenario=resolved,
        round_num=1,
        history=[],
        other_decisions=[],
    )

    assert "Round 1 of 3" in prompt
    assert "decision" in prompt


def test_user_prompt_includes_history():
    resolved = build_resolved_scenario(
        CONFIGS / "scenarios" / "minimal.yaml",
        CONFIGS / "personas",
        CONFIGS / "run_configs" / "dev.yaml",
    )
    engine = PromptEngine()
    agent = resolved.agents[0]

    history = [
        {"round": 1, "own_decision": "counter_offer", "own_reasoning": "Too expensive"},
    ]
    other_decisions = [
        {"round": 1, "agent_label": "seller_0", "summary": "counter_offer (value: 120)"},
    ]

    prompt = engine.render_user_prompt(
        agent=agent,
        scenario=resolved,
        round_num=2,
        history=history,
        other_decisions=other_decisions,
    )

    assert "Round 2 of 3" in prompt
    assert "seller_0" in prompt
    assert "counter_offer" in prompt
