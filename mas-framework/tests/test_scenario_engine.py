"""Tests for scenario engine: loading, validation, resolution."""
from pathlib import Path

from mas.engine.scenario_engine import (
    build_resolved_scenario,
    load_personas,
    load_run_config,
    load_scenario,
)

CONFIGS = Path(__file__).parent.parent / "configs"


def test_load_scenario():
    scenario = load_scenario(CONFIGS / "scenarios" / "minimal.yaml")
    assert scenario.id == "minimal-negotiation"
    assert len(scenario.roles) == 2


def test_load_personas():
    pool = load_personas(CONFIGS / "personas" / "minimal_agents.yaml")
    assert len(pool.personas) == 2
    assert pool.personas[0].id == "frugal_buyer"


def test_load_run_config():
    config = load_run_config(CONFIGS / "run_configs" / "dev.yaml")
    assert config.id == "dev-test"
    assert config.seed == 42


def test_build_resolved_scenario():
    resolved = build_resolved_scenario(
        CONFIGS / "scenarios" / "minimal.yaml",
        CONFIGS / "personas",
        CONFIGS / "run_configs" / "dev.yaml",
    )
    assert len(resolved.agents) == 2
    assert resolved.config_hash != ""
    assert len(resolved.config_hash) == 16


def test_config_hash_deterministic():
    hash1 = build_resolved_scenario(
        CONFIGS / "scenarios" / "minimal.yaml",
        CONFIGS / "personas",
        CONFIGS / "run_configs" / "dev.yaml",
    ).config_hash
    hash2 = build_resolved_scenario(
        CONFIGS / "scenarios" / "minimal.yaml",
        CONFIGS / "personas",
        CONFIGS / "run_configs" / "dev.yaml",
    ).config_hash
    assert hash1 == hash2
