"""Pydantic models for persona definitions."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class RiskProfile(str, Enum):
    RISK_AVERSE = "risk_averse"
    RISK_NEUTRAL = "risk_neutral"
    RISK_SEEKING = "risk_seeking"


class DecisionFactor(BaseModel):
    factor: str
    weight: str  # "low" | "medium" | "high"
    threshold: str | None = None
    preference: str | None = None
    sensitivity: str | None = None
    note: str | None = None


class PersonalityTraits(BaseModel):
    stubbornness: float = Field(ge=0.0, le=1.0, default=0.5)
    reciprocity: float = Field(ge=0.0, le=1.0, default=0.5)
    environmental_concern: float = Field(ge=0.0, le=1.0, default=0.5)


class PersonaConfig(BaseModel):
    id: str
    label: str
    role: str
    background: str
    goals: dict[str, str]
    risk_profile: RiskProfile = RiskProfile.RISK_NEUTRAL
    decision_factors: list[DecisionFactor] = Field(default_factory=list)
    personality_traits: PersonalityTraits = Field(default_factory=PersonalityTraits)
    constraints: list[str] = Field(default_factory=list)


class PersonaPool(BaseModel):
    """Top-level model for a personas/*.yaml file."""

    personas: list[PersonaConfig] = Field(min_length=1)
