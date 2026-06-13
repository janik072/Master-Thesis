"""Pydantic models for scenario.yaml."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class InteractionType(str, Enum):
    SINGLE_SHOT = "single_shot"
    MULTI_ROUND = "multi_round_negotiation"
    AUCTION = "auction"
    DEBATE = "debate"


class Topology(str, Enum):
    ALL_TO_ALL = "all_to_all"
    PAIRWISE = "pairwise"
    HUB_SPOKE = "hub_spoke"
    CUSTOM = "custom"


class TurnOrder(str, Enum):
    SEQUENTIAL = "sequential"
    SIMULTANEOUS = "simultaneous"
    RANDOM = "random"


class HistoryDepth(str, Enum):
    NONE = "none"
    LAST_ROUND = "last_round"
    FULL = "full"


class Visibility(BaseModel):
    decisions: bool = True
    reasoning: bool = False
    history_depth: HistoryDepth = HistoryDepth.FULL


class RoundConfig(BaseModel):
    min: int = Field(ge=1, default=1)
    max: int = Field(ge=1, default=10)
    termination_condition: str = "max_rounds"


class InteractionConfig(BaseModel):
    type: InteractionType = InteractionType.MULTI_ROUND
    topology: Topology = Topology.ALL_TO_ALL
    rounds: RoundConfig = Field(default_factory=RoundConfig)
    turn_order: TurnOrder = TurnOrder.SIMULTANEOUS
    visibility: Visibility = Field(default_factory=Visibility)


class IncentiveType(str, Enum):
    CONTINUOUS = "continuous"
    DISCRETE = "discrete"
    BINARY = "binary"


class Incentive(BaseModel):
    id: str
    label: str
    type: IncentiveType
    range: list[float] | None = None
    options: list[str | int] | None = None
    unit: str | None = None
    offered_by: str
    target: str


class Objective(BaseModel):
    id: str
    description: str
    aggregation: str = "mean"


class Role(BaseModel):
    id: str
    label: str
    description: str
    count: int = Field(ge=1, default=1)
    persona_pool: str


class ScenarioConfig(BaseModel):
    """Top-level model for scenario.yaml."""

    id: str
    version: str = "1.0"
    name: str
    description: str
    shared_context: str = ""
    roles: list[Role] = Field(min_length=1)
    interaction: InteractionConfig = Field(default_factory=InteractionConfig)
    incentives: list[Incentive] = Field(default_factory=list)
    objectives: list[Objective] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
