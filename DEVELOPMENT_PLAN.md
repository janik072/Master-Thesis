# Entwicklungsplan: Konkrete Implementierungsschritte

**Stand:** 4. Juni 2026  
**Ziel:** Von Null zum ersten lauffähigen End-to-End-Run

---

## Schritt 0: Projekt-Skeleton (Tag 1)

### 0.1 Verzeichnis & pyproject.toml

```bash
cd /Users/Janik.Haeusser/Dev/Masterarbeit
mkdir -p mas-framework
cd mas-framework
```

```toml
# pyproject.toml
[project]
name = "mas-framework"
version = "0.1.0"
description = "Cost-efficient LLM-based multi-agent stakeholder simulation"
requires-python = ">=3.12"
dependencies = [
    # ── Core ──
    "pydantic>=2.7",           # Datenmodelle + JSON-Schema-Generierung
    "pyyaml>=6.0",             # YAML-Parsing
    "jinja2>=3.1",             # Prompt-Templates
    "litellm>=1.40",           # Multi-Provider LLM-Abstraktion
    "typer[all]>=0.12",        # CLI
    "structlog>=24.1",         # Structured Logging
    "python-dotenv>=1.0",      # .env-Handling
    # ── Async ──
    "httpx>=0.27",             # Async HTTP Client
    "aiosqlite>=0.20",         # Async SQLite für Cache
    # ── Analysis ──
    "pandas>=2.2",             # Datenanalyse
    "matplotlib>=3.9",         # Plots
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2",
    "pytest-asyncio>=0.23",
    "ruff>=0.4",
    "mypy>=1.10",
]

[project.scripts]
mas = "mas.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/mas"]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.mypy]
python_version = "3.12"
strict = true
```

### 0.2 Verzeichnisstruktur anlegen

```
mas-framework/
├── pyproject.toml
├── README.md
├── .env.example                    # OPENAI_API_KEY=sk-...
├── .gitignore
├── src/
│   └── mas/
│       ├── __init__.py             # __version__ = "0.1.0"
│       ├── cli.py                  # Typer app
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── scenario.py         # ScenarioConfig, Role, Interaction, Incentive
│       │   ├── persona.py          # PersonaConfig, PersonaPool
│       │   ├── run_config.py       # RunConfig, LLMConfig, CostConfig, CacheConfig
│       │   └── resolved.py         # ResolvedScenario, ResolvedAgent
│       ├── engine/
│       │   ├── __init__.py
│       │   ├── scenario_engine.py  # YAML → Pydantic → ResolvedScenario
│       │   ├── orchestrator.py     # Runden-Loop
│       │   └── state.py            # RoundState, SimulationState
│       ├── persona/
│       │   ├── __init__.py
│       │   └── manager.py          # Persona-Instanziierung + Prompt-Rendering
│       ├── llm/
│       │   ├── __init__.py
│       │   ├── gateway.py          # send() → LLMResponse
│       │   ├── cache.py            # SQLite Response-Cache
│       │   └── cost.py             # CostTracker
│       ├── prompts/
│       │   ├── __init__.py
│       │   ├── engine.py           # Jinja2 PromptEngine
│       │   └── templates/
│       │       ├── system.j2
│       │       └── user_decision.j2
│       └── output/
│           ├── __init__.py
│           ├── writer.py           # JSONL/JSON Output
│           └── hasher.py           # Reproduzierbarkeits-Hash
├── configs/
│   ├── scenarios/
│   │   └── minimal.yaml
│   ├── personas/
│   │   └── minimal_agents.yaml
│   └── run_configs/
│       └── dev.yaml
└── tests/
    ├── __init__.py
    ├── test_schemas.py
    ├── test_scenario_engine.py
    └── test_prompt_engine.py
```

### 0.3 Befehle

```bash
# Virtual Environment erstellen
cd mas-framework
python3.12 -m venv .venv
source .venv/bin/activate

# Projekt installieren (editable)
pip install -e ".[dev]"

# Prüfen ob CLI funktioniert
mas --help
```

**Checkpoint:** `mas --help` zeigt Hilfetext.

---

## Schritt 1: Pydantic-Schemas (Tag 1–2)

Die Schemas sind das Fundament — alles andere baut darauf auf. Sie werden direkt aus der Architektur-Spezifikation abgeleitet.

### 1.1 `src/mas/schemas/scenario.py`

```python
"""Pydantic models for scenario.yaml"""
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
    range: list[float] | None = None        # für continuous
    options: list[str | int] | None = None  # für discrete
    unit: str | None = None
    offered_by: str                          # role_id
    target: str                              # role_id


class Objective(BaseModel):
    id: str
    description: str
    aggregation: str = "mean"


class Role(BaseModel):
    id: str
    label: str
    description: str
    count: int = Field(ge=1, default=1)
    persona_pool: str                        # Pfad zu personas/*.yaml


class ScenarioConfig(BaseModel):
    """Top-level model for scenario.yaml"""
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
```

### 1.2 `src/mas/schemas/persona.py`

```python
"""Pydantic models for persona definitions"""
from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class RiskProfile(str, Enum):
    RISK_AVERSE = "risk_averse"
    RISK_NEUTRAL = "risk_neutral"
    RISK_SEEKING = "risk_seeking"


class DecisionFactor(BaseModel):
    factor: str
    weight: str                              # "low" | "medium" | "high"
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
    role: str                                # Muss einer Role.id im Szenario entsprechen
    background: str
    goals: dict[str, str]                    # {"primary": "...", "secondary": "..."}
    risk_profile: RiskProfile = RiskProfile.RISK_NEUTRAL
    decision_factors: list[DecisionFactor] = Field(default_factory=list)
    personality_traits: PersonalityTraits = Field(default_factory=PersonalityTraits)
    constraints: list[str] = Field(default_factory=list)


class PersonaPool(BaseModel):
    """Top-level model for a personas/*.yaml file"""
    personas: list[PersonaConfig] = Field(min_length=1)
```

### 1.3 `src/mas/schemas/run_config.py`

```python
"""Pydantic models for run_config.yaml"""
from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class ResponseFormat(str, Enum):
    JSON = "json"
    TEXT = "text"
    STRUCTURED = "structured"


class RoutingRule(BaseModel):
    task: str                                # "decision" | "reasoning_summary" | ...
    model: str
    provider: str


class ProviderConfig(BaseModel):
    api_key_env: str | None = None           # Name der Env-Var, NIE der Key selbst
    base_url: str | None = None
    rate_limit_rpm: int | None = None


class RetryConfig(BaseModel):
    max_retries: int = Field(ge=0, default=3)
    backoff_base_seconds: float = 1.0
    backoff_max_seconds: float = 16.0
    backoff_jitter: float = 0.1


class LLMConfig(BaseModel):
    default_provider: str = "openai"
    default_model: str = "gpt-4o-mini"
    temperature: float = Field(ge=0.0, le=2.0, default=0.7)
    max_tokens_per_response: int = Field(ge=1, default=1024)
    response_format: ResponseFormat = ResponseFormat.JSON
    routing: dict[str, list[RoutingRule] | bool] = Field(default_factory=dict)
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    retry: RetryConfig = Field(default_factory=RetryConfig)


class CostConfig(BaseModel):
    budget_total_usd: float = Field(ge=0, default=5.0)
    budget_per_repetition_usd: float | None = None
    alert_threshold_pct: int = Field(ge=0, le=100, default=80)
    abort_on_exceed: bool = True


class CacheConfig(BaseModel):
    enabled: bool = True
    backend: str = "sqlite"
    cache_path: str = ".cache/llm_responses.db"
    ttl_hours: int = 168


class OutputConfig(BaseModel):
    base_dir: str = "output/runs"
    include_raw_responses: bool = True
    include_prompt_snapshots: bool = True
    log_level: str = "INFO"


class RunConfig(BaseModel):
    """Top-level model for run_config.yaml"""
    id: str = "default"
    seed: int = 42
    repetitions: int = Field(ge=1, default=1)
    description: str = ""
    llm: LLMConfig = Field(default_factory=LLMConfig)
    cost: CostConfig = Field(default_factory=CostConfig)
    caching: CacheConfig = Field(default_factory=CacheConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
```

### 1.4 `src/mas/schemas/resolved.py`

```python
"""Resolved (immutable) data structures after input validation and reference resolution"""
from __future__ import annotations

from pydantic import BaseModel

from .persona import PersonaConfig, PersonalityTraits
from .scenario import InteractionConfig, Incentive, Objective, ScenarioConfig
from .run_config import RunConfig


class ResolvedAgent(BaseModel):
    """A fully resolved agent: persona assigned to a role"""
    agent_id: str                            # z.B. "farmer_0", "authority_0"
    role_id: str
    persona: PersonaConfig


class ResolvedScenario(BaseModel):
    """Immutable, fully resolved simulation configuration"""
    scenario: ScenarioConfig
    agents: list[ResolvedAgent]
    run_config: RunConfig

    # Computed nach Auflösung
    config_hash: str = ""                    # SHA-256 über kanonische Inputs
```

**Test dazu** (`tests/test_schemas.py`):

```python
import yaml
from mas.schemas.scenario import ScenarioConfig
from mas.schemas.persona import PersonaPool
from mas.schemas.run_config import RunConfig


def test_minimal_scenario_parses():
    raw = {
        "id": "test-001",
        "name": "Minimal Test",
        "description": "Two agents negotiate",
        "roles": [
            {"id": "buyer", "label": "Buyer", "description": "Wants low price",
             "count": 1, "persona_pool": "personas/buyers.yaml"},
            {"id": "seller", "label": "Seller", "description": "Wants high price",
             "count": 1, "persona_pool": "personas/sellers.yaml"},
        ],
    }
    config = ScenarioConfig(**raw)
    assert len(config.roles) == 2
    assert config.interaction.topology.value == "all_to_all"


def test_persona_traits_validation():
    """Traits must be 0.0–1.0"""
    from pydantic import ValidationError
    from mas.schemas.persona import PersonalityTraits
    import pytest

    with pytest.raises(ValidationError):
        PersonalityTraits(stubbornness=1.5)  # Over 1.0 → fail


def test_run_config_defaults():
    config = RunConfig()
    assert config.seed == 42
    assert config.llm.default_model == "gpt-4o-mini"
    assert config.cost.budget_total_usd == 5.0
```

**Checkpoint:** `pytest tests/test_schemas.py` — alle grün.

---

## Schritt 2: Scenario Engine + Validator (Tag 2–3)

### 2.1 `src/mas/engine/scenario_engine.py`

```python
"""Loads, validates, and resolves scenario + personas + run_config into a ResolvedScenario."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from mas.schemas.scenario import ScenarioConfig
from mas.schemas.persona import PersonaPool
from mas.schemas.run_config import RunConfig
from mas.schemas.resolved import ResolvedAgent, ResolvedScenario


def load_yaml(path: Path) -> dict:
    """Load a YAML file and return as dict."""
    with open(path) as f:
        return yaml.safe_load(f)


def load_scenario(scenario_path: Path) -> ScenarioConfig:
    """Load and validate a scenario.yaml file."""
    raw = load_yaml(scenario_path)
    # Handle nested 'scenario:' key or flat structure
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
    """Resolve persona_pool references → assign personas to roles."""
    import random
    rng = random.Random(seed)
    agents: list[ResolvedAgent] = []

    for role in scenario.roles:
        pool_path = persona_dir / Path(role.persona_pool).name
        pool = load_personas(pool_path)
        available = list(pool.personas)

        for i in range(role.count):
            # Cycle through personas if count > len(pool)
            persona = available[i % len(available)]
            agent_id = f"{role.id}_{i}"
            agents.append(ResolvedAgent(
                agent_id=agent_id,
                role_id=role.id,
                persona=persona,
            ))

    if seed != 0:
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
    # Hash all persona files in dir
    for p in sorted(persona_dir.glob("*.yaml")):
        hasher.update(p.read_bytes())
    return hasher.hexdigest()[:16]


def build_resolved_scenario(
    scenario_path: Path,
    persona_dir: Path,
    run_config_path: Path,
) -> ResolvedScenario:
    """Full pipeline: load → validate → resolve → hash."""
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
```

### 2.2 CLI: `mas validate`

```python
# src/mas/cli.py
"""CLI entry point for the MAS framework."""
from pathlib import Path

import typer
import structlog

app = typer.Typer(name="mas", help="Multi-Agent Stakeholder Simulation Framework")
log = structlog.get_logger()


@app.command()
def validate(
    scenario: Path = typer.Argument(..., help="Path to scenario.yaml"),
    personas: Path = typer.Argument(..., help="Path to personas/ directory"),
    run_config: Path = typer.Argument(..., help="Path to run_config.yaml"),
):
    """Validate input files against schemas without running a simulation."""
    from mas.engine.scenario_engine import build_resolved_scenario

    try:
        resolved = build_resolved_scenario(scenario, personas, run_config)
        typer.echo(f"✓ Scenario: {resolved.scenario.name}")
        typer.echo(f"✓ Agents:   {len(resolved.agents)}")
        typer.echo(f"✓ Rounds:   {resolved.scenario.interaction.rounds.min}–{resolved.scenario.interaction.rounds.max}")
        typer.echo(f"✓ Budget:   ${resolved.run_config.cost.budget_total_usd}")
        typer.echo(f"✓ Hash:     {resolved.config_hash}")
        typer.echo("\nAll inputs valid.")
    except Exception as e:
        typer.echo(f"✗ Validation error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def run(
    scenario: Path = typer.Argument(..., help="Path to scenario.yaml"),
    personas: Path = typer.Argument(..., help="Path to personas/ directory"),
    run_config: Path = typer.Argument(..., help="Path to run_config.yaml"),
):
    """Run a simulation."""
    import asyncio
    from mas.engine.scenario_engine import build_resolved_scenario
    from mas.engine.orchestrator import run_simulation

    resolved = build_resolved_scenario(scenario, personas, run_config)
    typer.echo(f"Starting simulation: {resolved.scenario.name}")
    typer.echo(f"  Agents: {len(resolved.agents)} | Rounds: {resolved.scenario.interaction.rounds.max}")

    result = asyncio.run(run_simulation(resolved))
    typer.echo(f"\nSimulation complete. Output: {result}")


if __name__ == "__main__":
    app()
```

**Checkpoint:** `mas validate configs/scenarios/minimal.yaml configs/personas/ configs/run_configs/dev.yaml`

---

## Schritt 3: Minimal-Konfigurationen (Tag 2)

### 3.1 `configs/scenarios/minimal.yaml`

```yaml
scenario:
  id: "minimal-negotiation"
  version: "1.0"
  name: "Minimal Test Scenario"
  description: "Two agents negotiate a simple deal"
  shared_context: >
    A buyer and a seller are negotiating the price of a product.
    The product is worth between 50 and 150 EUR.

  roles:
    - id: "buyer"
      label: "Buyer"
      description: "Wants to buy the product at the lowest price"
      count: 1
      persona_pool: "minimal_agents.yaml"
    - id: "seller"
      label: "Seller"
      description: "Wants to sell the product at the highest price"
      count: 1
      persona_pool: "minimal_agents.yaml"

  interaction:
    type: "multi_round_negotiation"
    topology: "all_to_all"
    rounds:
      min: 1
      max: 3
    turn_order: "sequential"
    visibility:
      decisions: true
      reasoning: false
      history_depth: "full"

  incentives:
    - id: "price_offer"
      label: "Price Offer"
      type: "continuous"
      range: [50, 150]
      unit: "EUR"
      offered_by: "buyer"
      target: "seller"

  objectives:
    - id: "final_price"
      description: "The agreed price"
      aggregation: "mean"
    - id: "deal_reached"
      description: "Whether a deal was reached"
      aggregation: "ratio"
```

### 3.2 `configs/personas/minimal_agents.yaml`

```yaml
personas:
  - id: "frugal_buyer"
    label: "Frugal Buyer"
    role: "buyer"
    background: "A cost-conscious buyer with a budget of 100 EUR."
    goals:
      primary: "Buy the product for less than 90 EUR"
      secondary: "Reach a deal within 3 rounds"
    risk_profile: "risk_averse"
    decision_factors:
      - factor: "price"
        weight: "high"
        threshold: "Will not pay more than 100 EUR"
    personality_traits:
      stubbornness: 0.6
      reciprocity: 0.4
      environmental_concern: 0.3
    constraints:
      - "Maximum budget: 100 EUR"

  - id: "firm_seller"
    label: "Firm Seller"
    role: "seller"
    background: "A seller who paid 70 EUR for the product and wants profit."
    goals:
      primary: "Sell for at least 90 EUR"
      secondary: "Close the deal quickly"
    risk_profile: "risk_neutral"
    decision_factors:
      - factor: "price"
        weight: "high"
        threshold: "Will not sell below 80 EUR"
    personality_traits:
      stubbornness: 0.5
      reciprocity: 0.5
      environmental_concern: 0.2
    constraints:
      - "Minimum acceptable price: 80 EUR"
```

### 3.3 `configs/run_configs/dev.yaml`

```yaml
id: "dev-test"
seed: 42
repetitions: 1
description: "Development/testing run"

llm:
  default_provider: "openai"
  default_model: "gpt-4o-mini"
  temperature: 0.7
  max_tokens_per_response: 512
  response_format: "json"
  providers:
    openai:
      api_key_env: "OPENAI_API_KEY"

cost:
  budget_total_usd: 0.50
  alert_threshold_pct: 80
  abort_on_exceed: true

caching:
  enabled: false

output:
  base_dir: "output/runs"
  include_raw_responses: true
  log_level: "DEBUG"
```

---

## Schritt 4: Prompt Engine (Tag 3–4)

### 4.1 `src/mas/prompts/engine.py`

```python
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
```

### 4.2 `src/mas/prompts/templates/system.j2`

```jinja2
You are {{ persona.label }}, a participant in a multi-stakeholder negotiation simulation.

## Your Background
{{ persona.background }}

## Your Role
You are a {{ scenario.roles | selectattr('id', 'equalto', agent.role_id) | first | attr('label') }}.
{{ scenario.roles | selectattr('id', 'equalto', agent.role_id) | first | attr('description') }}

## Your Goals
- Primary: {{ persona.goals.primary }}
{% if persona.goals.secondary is defined %}
- Secondary: {{ persona.goals.secondary }}
{% endif %}

## Your Decision Factors
{% for factor in persona.decision_factors %}
- **{{ factor.factor }}** (importance: {{ factor.weight }}):
  {% if factor.threshold %}Threshold: {{ factor.threshold }}{% endif %}
  {% if factor.preference %}Preference: {{ factor.preference }}{% endif %}
{% endfor %}

## Your Constraints
{% for constraint in persona.constraints %}
- {{ constraint }}
{% endfor %}

## Context
{{ scenario.shared_context }}

## Rules
- You must respond ONLY in valid JSON format.
- Your response must include: "decision", "reasoning", and any numeric values relevant to the negotiation.
- Stay in character. Base your decisions on your background, goals, and constraints.
- Consider the history of previous rounds when making decisions.
```

### 4.3 `src/mas/prompts/templates/user_decision.j2`

```jinja2
## Round {{ round_num }} of {{ max_rounds }}

{% if other_decisions %}
### What happened in previous rounds:
{% for entry in other_decisions %}
- **{{ entry.agent_label }}** (Round {{ entry.round }}): {{ entry.summary }}
{% endfor %}
{% endif %}

{% if incentives %}
### Available mechanisms:
{% for inc in incentives %}
- **{{ inc.label }}** ({{ inc.type.value }}):
  {% if inc.range %}Range: {{ inc.range[0] }}–{{ inc.range[1] }} {{ inc.unit }}{% endif %}
  {% if inc.options %}Options: {{ inc.options | join(', ') }}{% endif %}
{% endfor %}
{% endif %}

### Your task:
Based on your role, goals, and the negotiation history, make your decision for this round.

Respond with valid JSON:
```json
{
  "decision": "accept" or "reject" or "counter_offer",
  "reasoning": "Your reasoning in 2-3 sentences",
  "proposed_value": <number or null>,
  "conditions": ["any conditions you attach"]
}
```
```

---

## Schritt 5: LLM Gateway (Tag 4–5)

### 5.1 `src/mas/llm/gateway.py`

```python
"""Unified LLM Gateway using litellm for multi-provider support."""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import litellm
import structlog

from mas.schemas.run_config import LLMConfig

log = structlog.get_logger()

# litellm produziert viele Debug-Logs, die wir nicht brauchen
litellm.suppress_debug_info = True


@dataclass
class LLMResponse:
    """Normalized response from any LLM provider."""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cached: bool = False


class LLMGateway:
    """Sends prompts to LLM providers via litellm."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._setup_api_keys()

    def _setup_api_keys(self):
        """Load API keys from environment variables."""
        import os
        for provider_name, provider_cfg in self.config.providers.items():
            if provider_cfg.api_key_env:
                key = os.environ.get(provider_cfg.api_key_env)
                if not key:
                    log.warning("api_key_not_found", provider=provider_name,
                                env_var=provider_cfg.api_key_env)

    async def send(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Send messages to LLM and return normalized response."""
        model = model or self.config.default_model
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens_per_response

        # Prefix model with provider if not already done (litellm convention)
        # e.g. "gpt-4o-mini" → works directly, "mistral/..." needs prefix
        start = time.perf_counter()

        try:
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=(
                    {"type": "json_object"}
                    if self.config.response_format.value == "json"
                    else None
                ),
            )
        except Exception as e:
            log.error("llm_call_failed", model=model, error=str(e))
            raise

        latency_ms = (time.perf_counter() - start) * 1000

        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=response.model or model,
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
            latency_ms=round(latency_ms, 1),
        )
```

### 5.2 `src/mas/llm/cost.py`

```python
"""Cost tracking per LLM call and per run."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import structlog

log = structlog.get_logger()

# Preise pro 1M Tokens (Stand Juni 2026, anpassen wenn nötig)
PRICE_TABLE: dict[str, dict[str, float]] = {
    "gpt-4o":           {"input": 2.50,  "output": 10.00},
    "gpt-4o-mini":      {"input": 0.15,  "output": 0.60},
    "gpt-4.1-mini":     {"input": 0.40,  "output": 1.60},
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "mistral-large-latest": {"input": 2.00, "output": 6.00},
    "mistral-small-latest": {"input": 0.10, "output": 0.30},
    # Lokale Modelle
    "ollama/llama3:8b":  {"input": 0.0, "output": 0.0},
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
        pct = (self.total_cost / self.budget_total_usd * 100) if self.budget_total_usd > 0 else 0
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
                f.write(json.dumps(call.__dict__) + "\n")


class BudgetExceededError(Exception):
    pass
```

---

## Schritt 6: State Manager (Tag 5)

### 6.1 `src/mas/engine/state.py`

```python
"""Immutable simulation state management."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class AgentDecision:
    """One agent's decision in one round."""
    agent_id: str
    role_id: str
    round_num: int
    raw_response: str                   # Volles LLM-Output
    decision: str                       # "accept" | "reject" | "counter_offer"
    reasoning: str
    proposed_value: float | None
    conditions: list[str]
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float
    cached: bool
    timestamp: str


@dataclass(frozen=True)
class RoundState:
    """Immutable snapshot of one round."""
    round_num: int
    decisions: tuple[AgentDecision, ...]
    timestamp: str


@dataclass
class SimulationState:
    """Accumulates RoundStates across the simulation."""
    rounds: list[RoundState] = field(default_factory=list)

    def add_round(self, decisions: list[AgentDecision]) -> RoundState:
        round_state = RoundState(
            round_num=len(self.rounds) + 1,
            decisions=tuple(decisions),
            timestamp=datetime.now().isoformat(),
        )
        self.rounds.append(round_state)
        return round_state

    def get_history_for_agent(
        self,
        agent_id: str,
        visible_decisions: bool = True,
    ) -> list[dict]:
        """Get visible history for an agent's prompt context."""
        history = []
        for round_state in self.rounds:
            for dec in round_state.decisions:
                if dec.agent_id == agent_id:
                    history.append({
                        "round": dec.round_num,
                        "own_decision": dec.decision,
                        "own_reasoning": dec.reasoning,
                    })
                elif visible_decisions:
                    history.append({
                        "round": dec.round_num,
                        "agent_label": dec.agent_id,
                        "summary": f"{dec.decision} (value: {dec.proposed_value})",
                    })
        return history
```

---

## Schritt 7: Orchestrator — der Runden-Loop (Tag 5–6)

### 7.1 `src/mas/engine/orchestrator.py`

```python
"""Interaction Orchestrator: the main simulation loop."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import structlog

from mas.llm.cost import CostTracker, BudgetExceededError
from mas.llm.gateway import LLMGateway
from mas.prompts.engine import PromptEngine
from mas.engine.state import AgentDecision, SimulationState
from mas.output.writer import OutputWriter
from mas.schemas.resolved import ResolvedAgent, ResolvedScenario

log = structlog.get_logger()


async def run_simulation(resolved: ResolvedScenario) -> Path:
    """Execute a full simulation and return the output directory."""
    # ── Setup ──
    gateway = LLMGateway(resolved.run_config.llm)
    prompt_engine = PromptEngine()
    cost_tracker = CostTracker(
        budget_total_usd=resolved.run_config.cost.budget_total_usd,
        alert_threshold_pct=resolved.run_config.cost.alert_threshold_pct,
        abort_on_exceed=resolved.run_config.cost.abort_on_exceed,
    )
    state = SimulationState()
    writer = OutputWriter(resolved)

    max_rounds = resolved.scenario.interaction.rounds.max

    log.info("simulation_start",
             scenario=resolved.scenario.name,
             agents=len(resolved.agents),
             max_rounds=max_rounds)

    # ── Round Loop ──
    try:
        for round_num in range(1, max_rounds + 1):
            log.info("round_start", round=round_num)

            round_decisions: list[AgentDecision] = []

            for agent in resolved.agents:
                # 1. Build context
                history = state.get_history_for_agent(
                    agent.agent_id,
                    visible_decisions=resolved.scenario.interaction.visibility.decisions,
                )

                # Visible decisions from OTHER agents in previous rounds
                other_decisions = [
                    h for h in history if "agent_label" in h
                ]

                # 2. Render prompts
                system_prompt = prompt_engine.render_system_prompt(agent, resolved)
                user_prompt = prompt_engine.render_user_prompt(
                    agent, resolved, round_num, history, other_decisions,
                )

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]

                # 3. LLM call
                llm_response = await gateway.send(messages)

                # 4. Parse response
                decision_data = _parse_decision(llm_response.content)

                # 5. Record cost
                cost_tracker.record_call(
                    agent_id=agent.agent_id,
                    round_num=round_num,
                    model=llm_response.model,
                    input_tokens=llm_response.input_tokens,
                    output_tokens=llm_response.output_tokens,
                    latency_ms=llm_response.latency_ms,
                    cached=llm_response.cached,
                )

                # 6. Create decision record
                agent_decision = AgentDecision(
                    agent_id=agent.agent_id,
                    role_id=agent.role_id,
                    round_num=round_num,
                    raw_response=llm_response.content,
                    decision=decision_data.get("decision", "unknown"),
                    reasoning=decision_data.get("reasoning", ""),
                    proposed_value=decision_data.get("proposed_value"),
                    conditions=decision_data.get("conditions", []),
                    model=llm_response.model,
                    input_tokens=llm_response.input_tokens,
                    output_tokens=llm_response.output_tokens,
                    cost_usd=cost_tracker.calls[-1].cost_usd,
                    latency_ms=llm_response.latency_ms,
                    cached=llm_response.cached,
                    timestamp=datetime.now().isoformat(),
                )
                round_decisions.append(agent_decision)

                log.info("agent_decision",
                         agent=agent.agent_id,
                         decision=agent_decision.decision,
                         cost=f"${agent_decision.cost_usd:.4f}")

            # 7. Update state
            state.add_round(round_decisions)

            log.info("round_complete",
                     round=round_num,
                     total_cost=f"${cost_tracker.total_cost:.4f}")

    except BudgetExceededError as e:
        log.warning("budget_exceeded", error=str(e))

    # ── Write outputs ──
    output_dir = writer.write_all(state, cost_tracker)
    log.info("simulation_complete", output_dir=str(output_dir),
             total_cost=f"${cost_tracker.total_cost:.4f}")
    return output_dir


def _parse_decision(raw: str) -> dict:
    """Extract JSON decision from LLM response."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to find JSON in fenced code block
        import re
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        # Last resort: return raw as reasoning
        return {
            "decision": "parse_error",
            "reasoning": raw[:500],
            "proposed_value": None,
            "conditions": [],
        }
```

---

## Schritt 8: Output Writer (Tag 6)

### 8.1 `src/mas/output/writer.py`

```python
"""Structured output generation: JSONL logs, manifest, summary."""
from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from mas.engine.state import SimulationState
from mas.llm.cost import CostTracker
from mas.schemas.resolved import ResolvedScenario


class OutputWriter:
    def __init__(self, resolved: ResolvedScenario):
        self.resolved = resolved

    def _create_output_dir(self) -> Path:
        base = Path(self.resolved.run_config.output.base_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = base / f"{self.resolved.config_hash}_{timestamp}"
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def write_all(self, state: SimulationState, cost_tracker: CostTracker) -> Path:
        output_dir = self._create_output_dir()

        # 1. decisions.jsonl
        self._write_decisions(output_dir, state)

        # 2. cost_log.jsonl
        cost_tracker.write_cost_log(output_dir / "cost_log.jsonl")

        # 3. manifest.json
        self._write_manifest(output_dir)

        # 4. run_summary.json
        self._write_summary(output_dir, state, cost_tracker)

        return output_dir

    def _write_decisions(self, output_dir: Path, state: SimulationState) -> None:
        with open(output_dir / "decisions.jsonl", "w") as f:
            for round_state in state.rounds:
                for dec in round_state.decisions:
                    f.write(json.dumps(asdict(dec)) + "\n")

    def _write_manifest(self, output_dir: Path) -> None:
        import sys
        manifest = {
            "config_hash": self.resolved.config_hash,
            "scenario_id": self.resolved.scenario.id,
            "seed": self.resolved.run_config.seed,
            "framework_version": "0.1.0",
            "python_version": sys.version,
            "timestamp": datetime.now().isoformat(),
            "agent_count": len(self.resolved.agents),
            "default_model": self.resolved.run_config.llm.default_model,
        }
        with open(output_dir / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)

    def _write_summary(
        self, output_dir: Path, state: SimulationState, cost_tracker: CostTracker
    ) -> None:
        summary = {
            "total_rounds": len(state.rounds),
            "total_cost_usd": round(cost_tracker.total_cost, 6),
            "total_input_tokens": cost_tracker.total_input_tokens,
            "total_output_tokens": cost_tracker.total_output_tokens,
            "total_calls": len(cost_tracker.calls),
            "per_agent": {},
        }
        for agent in self.resolved.agents:
            agent_decisions = [
                d for r in state.rounds for d in r.decisions
                if d.agent_id == agent.agent_id
            ]
            summary["per_agent"][agent.agent_id] = {
                "decisions": [d.decision for d in agent_decisions],
                "total_cost": round(sum(d.cost_usd for d in agent_decisions), 6),
            }
        with open(output_dir / "run_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
```

---

## Schritt 9: Erster End-to-End-Run (Tag 6–7)

### 9.1 Ausführung

```bash
# .env Datei erstellen
echo "OPENAI_API_KEY=sk-..." > .env

# Validierung
mas validate configs/scenarios/minimal.yaml configs/personas/ configs/run_configs/dev.yaml

# Erster Run!
mas run configs/scenarios/minimal.yaml configs/personas/ configs/run_configs/dev.yaml
```

### 9.2 Erwartetes Output

```
output/runs/a3f2b1c0e8d9_20260604_143000/
├── decisions.jsonl       ← Pro Agent pro Runde eine Zeile
├── cost_log.jsonl        ← Pro LLM-Call eine Zeile  
├── manifest.json         ← Reproduzierbarkeits-Info
└── run_summary.json      ← Aggregierte Ergebnisse
```

### 9.3 Was `decisions.jsonl` enthält

```json
{"agent_id": "buyer_0", "round_num": 1, "decision": "counter_offer", "reasoning": "I want to start low...", "proposed_value": 75.0, "model": "gpt-4o-mini", "input_tokens": 423, "output_tokens": 89, "cost_usd": 0.000117, "latency_ms": 892.3}
{"agent_id": "seller_0", "round_num": 1, "decision": "counter_offer", "reasoning": "Too low, I need at least...", "proposed_value": 110.0, "model": "gpt-4o-mini", "input_tokens": 456, "output_tokens": 102, "cost_usd": 0.000129, "latency_ms": 1023.1}
```

**Checkpoint:** Ein vollständiger Run mit 2 Agenten, 3 Runden produziert alle 4 Output-Dateien. Geschätzte Kosten: ~$0.002.

---

## Zusammenfassung: Was wann fertig sein muss

| Tag | Schritt | Deliverable |
|-----|---------|-------------|
| 1 | Projekt-Skeleton + pyproject.toml | `mas --help` funktioniert |
| 1–2 | Pydantic-Schemas | `pytest tests/test_schemas.py` grün |
| 2–3 | Scenario Engine + CLI validate | `mas validate` läuft fehlerfrei |
| 2 | Minimal-Konfigurationen | 3 YAML-Dateien für Test-Szenario |
| 3–4 | Prompt Engine + Jinja2-Templates | System- & User-Prompts rendern korrekt |
| 4–5 | LLM Gateway (litellm) | Einzelner API-Call funktioniert |
| 5 | Cost Tracker + State Manager | Kosten werden getrackt, State ist immutable |
| 5–6 | Orchestrator | Runden-Loop läuft mit echten LLM-Calls |
| 6 | Output Writer | JSONL + Manifest + Summary werden geschrieben |
| **6–7** | **Erster End-to-End-Run** | **`mas run` produziert alle Outputs** |

---

## Benötigte Tools & Accounts

| Tool | Zweck | Setup |
|------|-------|-------|
| Python 3.12+ | Runtime | `brew install python@3.12` oder pyenv |
| uv / pip | Package Management | `pip install uv` (optional, pip reicht) |
| OpenAI API Key | LLM-Calls | https://platform.openai.com → API Keys |
| Git | Versionskontrolle | bereits vorhanden |
| VS Code | IDE | bereits vorhanden |
| ruff | Linting + Formatting | `pip install ruff` (in dev-deps) |
| pytest | Tests | `pip install pytest` (in dev-deps) |

### Optionale Tools (für spätere Phasen)

| Tool | Zweck | Wann |
|------|-------|------|
| Ollama | Lokale Modelle | Phase 4 (Kostenoptimierung) |
| Anthropic API Key | Claude-Modelle | Phase 4 (Model-Vergleich) |
| Mistral API Key | Mistral-Modelle | Phase 4 (Model-Vergleich) |
| SQLite Browser | Cache-Inspektion | Phase 4 (Caching) |

---

## Abhängigkeitsgraph

```
Schemas ─────────────────────┐
   │                         │
   ▼                         │
Scenario Engine              │
   │                         │
   ├──▶ Prompt Engine        │
   │       │                 │
   │       ▼                 │
   │   LLM Gateway ◄────────┘
   │       │
   │       ▼
   │   Cost Tracker
   │       │
   ▼       ▼
Orchestrator
   │
   ▼
Output Writer
   │
   ▼
CLI (mas run / mas validate)
```

**Kritischer Pfad:** Schemas → Scenario Engine → Prompt Engine → LLM Gateway → Orchestrator → Output Writer. Jede Komponente baut auf der vorherigen auf.
