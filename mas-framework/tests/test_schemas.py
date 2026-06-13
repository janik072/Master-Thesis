"""Tests for Pydantic schemas."""
import pytest
from pydantic import ValidationError

from mas.schemas.persona import PersonaConfig, PersonaPool, PersonalityTraits
from mas.schemas.run_config import RunConfig
from mas.schemas.scenario import ScenarioConfig


def test_minimal_scenario_parses():
    raw = {
        "id": "test-001",
        "name": "Minimal Test",
        "description": "Two agents negotiate",
        "roles": [
            {
                "id": "buyer",
                "label": "Buyer",
                "description": "Wants low price",
                "count": 1,
                "persona_pool": "personas/buyers.yaml",
            },
            {
                "id": "seller",
                "label": "Seller",
                "description": "Wants high price",
                "count": 1,
                "persona_pool": "personas/sellers.yaml",
            },
        ],
    }
    config = ScenarioConfig(**raw)
    assert len(config.roles) == 2
    assert config.interaction.topology.value == "all_to_all"
    assert config.interaction.rounds.max == 10


def test_scenario_requires_at_least_one_role():
    with pytest.raises(ValidationError):
        ScenarioConfig(
            id="test",
            name="Empty",
            description="No roles",
            roles=[],
        )


def test_persona_traits_in_range():
    traits = PersonalityTraits(stubbornness=0.0, reciprocity=1.0, environmental_concern=0.5)
    assert traits.stubbornness == 0.0
    assert traits.reciprocity == 1.0


def test_persona_traits_rejects_out_of_range():
    with pytest.raises(ValidationError):
        PersonalityTraits(stubbornness=1.5)

    with pytest.raises(ValidationError):
        PersonalityTraits(reciprocity=-0.1)


def test_persona_pool_requires_at_least_one():
    with pytest.raises(ValidationError):
        PersonaPool(personas=[])


def test_persona_config_full():
    persona = PersonaConfig(
        id="test_agent",
        label="Test Agent",
        role="buyer",
        background="A test agent",
        goals={"primary": "Test goal"},
        risk_profile="risk_averse",
        decision_factors=[],
        personality_traits=PersonalityTraits(stubbornness=0.8),
        constraints=["Max budget: 100"],
    )
    assert persona.risk_profile.value == "risk_averse"
    assert persona.personality_traits.stubbornness == 0.8


def test_run_config_defaults():
    config = RunConfig()
    assert config.seed == 42
    assert config.llm.default_model == "gpt-4o-mini"
    assert config.cost.budget_total_usd == 5.0
    assert config.caching.enabled is True


def test_run_config_budget_validation():
    with pytest.raises(ValidationError):
        RunConfig(cost={"budget_total_usd": -1})
