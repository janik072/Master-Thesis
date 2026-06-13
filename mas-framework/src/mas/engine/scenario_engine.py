"""Loads, validates, and resolves scenario + personas + run_config into a ResolvedScenario."""
from __future__ import annotations

import hashlib
import random
from pathlib import Path

import yaml

from mas.schemas.persona import PersonaPool
from mas.schemas.resolved import ResolvedAgent, ResolvedScenario
from mas.schemas.run_config import RunConfig
from mas.schemas.scenario import ScenarioConfig


def load_yaml(path: Path) -> dict:
    """Load a YAML file and return as dict."""
    with open(path) as f:
        return yaml.safe_load(f)


def load_scenario(scenario_path: Path) -> ScenarioConfig:
    """Load and validate a scenario.yaml file."""
    raw = load_yaml(scenario_path)
    data = raw.get("scenario", raw)
    return ScenarioConfig(**data)


def load_personas(persona_path: Path) -> PersonaPool:
    """Load and validate a personas/*.yaml file."""
    raw = load_yaml(persona_path)
    return PersonaPool(**raw)


def load_run_config(run_config_path: Path) -> RunConfig:
    """Load and validate a run_config.yaml file."""
    raw = load_yaml(run_config_path)
    return RunConfig(**raw)


def resolve_agents(
    scenario: ScenarioConfig,
    persona_dir: Path,
    seed: int,
) -> list[ResolvedAgent]:
    """Resolve persona_pool references and assign personas to roles."""
    rng = random.Random(seed)
    agents: list[ResolvedAgent] = []

    for role in scenario.roles:
        pool_path = persona_dir / Path(role.persona_pool).name
        pool = load_personas(pool_path)
        # Filter personas matching this role; fall back to full pool
        matching = [p for p in pool.personas if p.role == role.id]
        available = matching if matching else list(pool.personas)

        for i in range(role.count):
            persona = available[i % len(available)]
            agent_id = f"{role.id}_{i}"
            agents.append(
                ResolvedAgent(
                    agent_id=agent_id,
                    role_id=role.id,
                    persona=persona,
                )
            )

    rng.shuffle(agents)
    return agents


def compute_config_hash(
    scenario_path: Path,
    persona_dir: Path,
    run_config_path: Path,
) -> str:
    """SHA-256 hash over canonical input files for reproducibility."""
    hasher = hashlib.sha256()
    for p in sorted([scenario_path, run_config_path]):
        hasher.update(p.read_bytes())
    for p in sorted(persona_dir.glob("*.yaml")):
        hasher.update(p.read_bytes())
    return hasher.hexdigest()[:16]


def build_resolved_scenario(
    scenario_path: Path,
    persona_dir: Path,
    run_config_path: Path,
) -> ResolvedScenario:
    """Full pipeline: load -> validate -> resolve -> hash."""
    scenario = load_scenario(scenario_path)
    run_config = load_run_config(run_config_path)
    agents = resolve_agents(scenario, persona_dir, run_config.seed)
    config_hash = compute_config_hash(scenario_path, persona_dir, run_config_path)

    return ResolvedScenario(
        scenario=scenario,
        agents=agents,
        run_config=run_config,
        config_hash=config_hash,
    )
