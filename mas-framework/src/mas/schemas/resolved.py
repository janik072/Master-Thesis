"""Resolved (immutable) data structures after input validation and reference resolution."""
from __future__ import annotations

from pydantic import BaseModel

from .persona import PersonaConfig
from .scenario import ScenarioConfig
from .run_config import RunConfig


class ResolvedAgent(BaseModel):
    """A fully resolved agent: persona assigned to a role."""

    agent_id: str
    role_id: str
    persona: PersonaConfig


class ResolvedScenario(BaseModel):
    """Immutable, fully resolved simulation configuration."""

    scenario: ScenarioConfig
    agents: list[ResolvedAgent]
    run_config: RunConfig
    config_hash: str = ""
