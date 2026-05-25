# Architektur-Entwurf: LLM-Agenten-Simulationsframework

> **Status**: Konzeptphase — Arbeitsdokument zur Masterarbeit  
> **Stand**: Mai 2026

---

## Inhaltsverzeichnis

1. [Überblick](#1-überblick)
2. [Input-Schicht: Schema-Definitionen](#2-input-schicht)
3. [Kernarchitektur](#3-kernarchitektur)
4. [Output-Schicht: Ergebnis-Schemata](#4-output-schicht)
5. [Technologie-Stack](#5-technologie-stack)
6. [Datenfluss End-to-End](#6-datenfluss)
7. [Kostenoptimierungs-Mechanismen](#7-kostenoptimierung)
8. [Reproduzierbarkeit & Hashing](#8-reproduzierbarkeit)

---

## 1. Überblick

```
┌─────────────────────────────────────────────────────────────────┐
│                        INPUT LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │  Scenario     │  │  Personas    │  │  Run Config        │    │
│  │  Definition   │  │  Definition  │  │  (LLM, Budget,     │    │
│  │  (YAML)       │  │  (YAML)      │  │   Seed, Provider)  │    │
│  └──────┬───────┘  └──────┬───────┘  └────────┬───────────┘    │
│         └─────────────────┼───────────────────┘                 │
│                           │                                     │
│                    ┌──────▼───────┐                              │
│                    │   Validator  │  JSON Schema Validation      │
│                    └──────┬───────┘                              │
└───────────────────────────┼─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                     CORE ENGINE                                  │
│                                                                  │
│  ┌────────────────┐   ┌──────────────────┐   ┌───────────────┐  │
│  │ Scenario       │   │ Persona          │   │ Prompt        │  │
│  │ Engine         │──▶│ Manager          │──▶│ Engine        │  │
│  │                │   │                  │   │               │  │
│  └────────────────┘   └──────────────────┘   └───────┬───────┘  │
│                                                      │          │
│  ┌────────────────┐   ┌──────────────────┐   ┌───────▼───────┐  │
│  │ Cost           │◀──│ Interaction      │◀──│ LLM           │  │
│  │ Controller     │──▶│ Orchestrator     │──▶│ Gateway       │  │
│  │                │   │                  │   │               │  │
│  └────────────────┘   └──────────────────┘   └───────────────┘  │
│                              │                                   │
│                       ┌──────▼───────┐                           │
│                       │ State        │                            │
│                       │ Manager      │                            │
│                       └──────────────┘                            │
└──────────────────────────────┼──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                       OUTPUT LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │  Decision     │  │  Cost &      │  │  Reproducibility   │    │
│  │  Log (JSONL)  │  │  Token Log   │  │  Manifest (JSON)   │    │
│  └──────────────┘  └──────────────┘  └────────────────────┘    │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │  Analysis     │  │  Raw LLM     │  │  Run Summary       │    │
│  │  Artifacts    │  │  Responses   │  │  (JSON)            │    │
│  └──────────────┘  └──────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Input-Schicht: Schema-Definitionen

Das Framework nimmt **drei YAML-Dateien** als Input, die jeweils gegen ein JSON-Schema validiert werden.

### 2.1 Szenario-Definition (`scenario.yaml`)

Beschreibt die Fragestellung, Stakeholder-Rollen, Interaktionsregeln und Anreizmechanismen — **domänenagnostisch**.

```yaml
# scenario.yaml — Beispiel: Moor-Wiedervernässung
scenario:
  id: "peatland-rewetting-negotiation"
  version: "1.0"
  name: "Moor-Wiedervernässungs-Verhandlung"
  description: >
    Simulation von Verhandlungen zwischen Landwirten und öffentlichen 
    Einrichtungen über die Wiedervernässung von Moorböden. Ziel ist die
    Identifikation wirksamer Anreizmechanismen für verschiedene Landwirt-Typen.

  # ── Kontext, der allen Agenten zugänglich ist ──
  shared_context: >
    In Deutschland sind ca. 92% der Moorflächen entwässert und 
    landwirtschaftlich genutzt. Entwässerte Moore emittieren jährlich 
    ca. 53 Mio. Tonnen CO₂-Äquivalente. Die Bundesregierung strebt an,
    bis 2030 mindestens 50.000 ha Moorböden wiederzuvernässen.

  # ── Stakeholder-Rollen (Referenzen auf Personas) ──
  roles:
    - id: "farmer"
      label: "Landwirt/Landbesitzer"
      description: "Besitzt entwässerte Moorflächen und bewirtschaftet diese."
      count: 4                        # Anzahl Agenten mit dieser Rolle
      persona_pool: "personas/farmers.yaml"  # Datei mit Persona-Varianten

    - id: "public_authority"
      label: "Öffentliche Einrichtung"
      description: "Bietet Kompensationen und regulatorische Rahmenbedingungen."
      count: 1
      persona_pool: "personas/authorities.yaml"

    - id: "ngo"
      label: "Umweltorganisation"
      description: "Vertritt Klimaschutzinteressen, kann Kooperationen anbieten."
      count: 1
      persona_pool: "personas/ngos.yaml"

  # ── Interaktionsregeln ──
  interaction:
    type: "multi_round_negotiation"  # Enum: single_shot | multi_round_negotiation | auction | debate
    topology: "all_to_all"           # Enum: all_to_all | pairwise | hub_spoke | custom
    rounds:
      min: 3
      max: 10
      termination_condition: "consensus_or_max_rounds"  # Enum oder Custom-Expression
    turn_order: "simultaneous"       # Enum: sequential | simultaneous | random

    # Was sehen Agenten voneinander?
    visibility:
      decisions: true                # Sehen andere Agenten die Entscheidungen?
      reasoning: false               # Sehen andere die Begründungen?
      history_depth: "full"          # Enum: none | last_round | full

  # ── Incentive-Mechanismen (szenariospezifisch) ──
  incentives:
    - id: "compensation"
      label: "Kompensationszahlung"
      type: "continuous"             # Enum: continuous | discrete | binary
      range: [0, 2000]               # €/ha/Jahr
      unit: "EUR_per_ha_per_year"
      offered_by: "public_authority"
      target: "farmer"

    - id: "contract_duration"
      label: "Vertragslaufzeit"
      type: "discrete"
      options: [5, 10, 15, 20, 30]
      unit: "years"
      offered_by: "public_authority"
      target: "farmer"

    - id: "paludiculture_support"
      label: "Paludikultur-Beratung & Förderung"
      type: "binary"
      offered_by: "ngo"
      target: "farmer"

    - id: "regulatory_pressure"
      label: "Regulatorischer Druck"
      type: "discrete"
      options: ["none", "voluntary_reporting", "mandatory_timeline", "ban_drainage"]
      offered_by: "public_authority"
      target: "farmer"

  # ── Zielmetriken (was soll gemessen werden?) ──
  objectives:
    - id: "acceptance_rate"
      description: "Anteil der Landwirte, die der Wiedervernässung zustimmen"
      aggregation: "ratio"

    - id: "min_compensation"
      description: "Minimale Kompensation, bei der Zustimmung erfolgt"
      aggregation: "per_agent"

    - id: "negotiation_rounds"
      description: "Anzahl Runden bis zur Einigung (oder Scheitern)"
      aggregation: "mean"

  # ── Constraints ──
  constraints:
    - "Die öffentliche Einrichtung hat ein Gesamtbudget von 500.000 EUR/Jahr."
    - "Landwirte können nur vollständig oder gar nicht zustimmen (keine Teilflächen)."
    - "Jeder Agent trifft Entscheidungen unabhängig."
```

### 2.2 Persona-Definition (`personas/*.yaml`)

Beschreibt individuelle Agenten-Persönlichkeiten innerhalb einer Rolle. Getrennt vom Szenario, um Wiederverwendung und kombinatorische Studien zu ermöglichen.

```yaml
# personas/farmers.yaml
personas:
  - id: "conventional_large"
    label: "Konventioneller Großbetrieb"
    role: "farmer"
    background: >
      Betreibt einen 200ha-Ackerbaubetrieb, davon 60ha auf entwässertem Moorboden.
      Haupteinnahme durch Mais- und Getreideanbau. Hohe Investitionen in 
      Drainage-Infrastruktur. Zwei Angestellte, Betriebsnachfolge unsicher.
    goals:
      primary: "Wirtschaftliche Stabilität des Betriebs sichern"
      secondary: "Betrieb für nächste Generation erhalten"
    risk_profile: "risk_averse"       # Enum: risk_averse | risk_neutral | risk_seeking
    decision_factors:
      - factor: "compensation_level"
        weight: "high"
        threshold: "Mindestens 1200 EUR/ha/Jahr, um Ernteausfall zu kompensieren"
      - factor: "contract_duration"
        weight: "medium"
        preference: "Kürzer bevorzugt (max. 10 Jahre), wegen Planungsunsicherheit"
      - factor: "regulatory_risk"
        weight: "medium"
        sensitivity: "Reagiert stark auf regulatorischen Druck"
    personality_traits:
      stubbornness: 0.7               # 0.0–1.0: Wie schwer umzustimmen
      reciprocity: 0.3                # 0.0–1.0: Reagiert auf Fairness/Gegenseitigkeit
      environmental_concern: 0.2      # 0.0–1.0: Eigenmotivation für Umweltschutz
    constraints:
      - "Kann maximal 40ha wiedervernässen (restliche 20ha grenzen an Gebäude)"
      - "Benötigt mindestens 3 Monate Vorlauf für Umstellung"

  - id: "small_diversified"
    label: "Kleiner diversifizierter Betrieb"
    role: "farmer"
    background: >
      45ha-Betrieb mit Milchviehhaltung und Grünland, davon 15ha auf Moorboden.
      Nebeneinkünfte durch Direktvermarktung und Ferienwohnungen. Aufgeschlossen
      gegenüber Paludikultur (Schilf, Torfmooskultivierung).
    goals:
      primary: "Diversifizierung der Einkommensquellen"
      secondary: "Ökologisches Image stärken"
    risk_profile: "risk_neutral"
    decision_factors:
      - factor: "paludiculture_support"
        weight: "high"
        preference: "Besonders interessiert an alternativer Bewirtschaftung"
      - factor: "compensation_level"
        weight: "medium"
        threshold: "Ab 600 EUR/ha/Jahr interessant"
      - factor: "contract_duration"
        weight: "low"
        preference: "Längere Verträge akzeptabel bei guter Kompensation"
    personality_traits:
      stubbornness: 0.3
      reciprocity: 0.6
      environmental_concern: 0.7
    constraints:
      - "Möchte mindestens 50% der Milchvieh-Weidefläche behalten"

  - id: "ecological_pioneer"
    label: "Ökologischer Pionierbetrieb"
    role: "farmer"
    background: >
      Bio-Betrieb mit 80ha, bereits teilweise extensiv bewirtschaftet.
      Aktiv in regionalen Naturschutzprojekten. Moorvernässung grundsätzlich
      positiv bewertet, aber wirtschaftliche Absicherung nötig.
    goals:
      primary: "Vorreiterrolle im Klimaschutz einnehmen"
      secondary: "Wirtschaftlich tragfähiges Modell für Moorschutz entwickeln"
    risk_profile: "risk_seeking"
    decision_factors:
      - factor: "compensation_level"
        weight: "medium"
        threshold: "Ab 400 EUR/ha/Jahr umsetzbar"
      - factor: "paludiculture_support"
        weight: "high"
        preference: "Will Pilotprojekt für Paludikultur starten"
      - factor: "public_recognition"
        weight: "medium"
        preference: "Öffentliche Anerkennung und Modellprojekt-Status"
    personality_traits:
      stubbornness: 0.2
      reciprocity: 0.8
      environmental_concern: 0.9
    constraints: []

  - id: "skeptical_traditional"
    label: "Skeptischer Traditionsbetrieb"
    role: "farmer"
    background: >
      Familienbetrieb in dritter Generation, 120ha Ackerbau auf Moorboden.
      Tiefes Misstrauen gegenüber staatlichen Programmen. Erfahrungen mit
      gebrochenen politischen Versprechen. "Das ist unser Land seit 1950."
    goals:
      primary: "Betrieb unverändert weiterführen"
      secondary: "Eigentumsrechte und Entscheidungsfreiheit bewahren"
    risk_profile: "risk_averse"
    decision_factors:
      - factor: "compensation_level"
        weight: "high"
        threshold: "Müsste über 1800 EUR/ha/Jahr liegen"
      - factor: "regulatory_pressure"
        weight: "high"
        sensitivity: "Reagiert mit Widerstand auf Zwang, aber akzeptiert bei Alternativlosigkeit"
      - factor: "trust"
        weight: "high"
        note: "Vertraut nur langfristigen, verbindlichen Zusagen"
    personality_traits:
      stubbornness: 0.9
      reciprocity: 0.2
      environmental_concern: 0.1
    constraints:
      - "Akzeptiert nur wenn Eigentum unangetastet bleibt"
      - "Keine Verpflichtung ohne Ausstiegsklausel"
```

### 2.3 Run-Konfiguration (`run_config.yaml`)

Steuert die technischen Aspekte: LLM-Provider, Kostenbudgets, Parallelisierung, Reproduzierbarkeit.

```yaml
# run_config.yaml
run:
  id: "peatland-exp-001"
  seed: 42
  repetitions: 10                    # Wie oft das identische Setup wiederholt wird
  description: "Baseline-Run: Alle Anreize aktiv, Kompensation 800-1500 EUR"

llm:
  default_provider: "openai"
  default_model: "gpt-4o-mini"
  temperature: 0.7
  max_tokens_per_response: 1024
  response_format: "json"           # Enum: json | text | structured (tool_use)

  # Modell-Routing: Günstigere Modelle für einfache Tasks
  routing:
    enabled: true
    rules:
      - task: "decision"             # Kernantwort des Agenten
        model: "gpt-4o"              # Stärkstes Modell für wichtigste Entscheidung
        provider: "openai"
      - task: "reasoning_summary"    # Zusammenfassung der Begründung
        model: "gpt-4o-mini"         # Günstigeres Modell reicht
        provider: "openai"
      - task: "sentiment_check"      # Stimmungsanalyse der Verhandlung
        model: "mistral-small-latest"
        provider: "mistral"

  # Provider-Konfiguration
  providers:
    openai:
      api_key_env: "OPENAI_API_KEY"  # Nur Env-Var-Name, nie der Key selbst
      base_url: null                 # Default
      rate_limit_rpm: 500
    mistral:
      api_key_env: "MISTRAL_API_KEY"
      rate_limit_rpm: 120
    anthropic:
      api_key_env: "ANTHROPIC_API_KEY"
      rate_limit_rpm: 300
    ollama:
      base_url: "http://localhost:11434"
      rate_limit_rpm: null           # Lokal, kein Limit

  # Retry & Resilience
  retry:
    max_retries: 3
    backoff_base_seconds: 1.0
    backoff_max_seconds: 16.0
    backoff_jitter: 0.1
    retryable_errors: ["rate_limit", "timeout", "server_error"]

cost:
  budget_total_usd: 5.00             # Hard limit für gesamten Run
  budget_per_repetition_usd: 0.50    # Soft limit pro Wiederholung
  alert_threshold_pct: 80            # Warnung bei 80% Verbrauch
  abort_on_exceed: true              # Run abbrechen bei Budgetüberschreitung
  track_granularity: "per_call"      # Enum: per_call | per_round | per_repetition

caching:
  enabled: true
  strategy: "content_hash"           # Enum: content_hash | semantic_similarity
  backend: "sqlite"                  # Enum: sqlite | redis | filesystem
  cache_path: ".cache/llm_responses.db"
  ttl_hours: 168                     # 7 Tage

parallelism:
  max_workers: 4                     # Parallele Agenten-Calls
  batch_size: null                   # null = alle gleichzeitig (bei simultaneous turns)

output:
  base_dir: "output/runs"
  format: "auto"                     # Erstellt Unterordner mit Timestamp + Run-ID
  include_raw_responses: true
  include_prompt_snapshots: true
  log_level: "INFO"                  # Enum: DEBUG | INFO | WARNING
```

### 2.4 JSON-Schema-Validierung

Jede YAML-Datei wird beim Einlesen gegen ein JSON-Schema validiert. Das stellt sicher, dass Konfigurationsfehler sofort gemeldet werden — nicht erst nach teuren API-Calls.

```
input_schemas/
├── scenario.schema.json      # Validiert scenario.yaml
├── personas.schema.json      # Validiert personas/*.yaml
└── run_config.schema.json    # Validiert run_config.yaml
```

Validierte Aspekte:
- Pflichtfelder vorhanden (`scenario.id`, `roles[].id`, `personas[].background`, ...)
- Enum-Werte korrekt (`interaction.type` ∈ `{single_shot, multi_round_negotiation, ...}`)
- Referenzielle Integrität (`roles[].persona_pool` zeigt auf existierende Datei)
- Typ-Checks (numerische Ranges, String-Formate)
- Constraint: Summe der `roles[].count` ≥ 2 (mindestens 2 Agenten)

---

## 3. Kernarchitektur

### 3.1 Komponentenübersicht

```
framework/
├── cli.py                     # CLI Entry Point (click/typer)
├── core/
│   ├── scenario_engine.py     # Parst & validiert Szenario + Personas
│   ├── persona_manager.py     # Instantiiert Agenten aus Persona-Defs
│   ├── orchestrator.py        # Steuerung der Interaktionsrunden
│   ├── state.py               # Immutable Round State
│   └── types.py               # Pydantic-Modelle für alle Datenstrukturen
├── llm/
│   ├── gateway.py             # Unified LLM Interface
│   ├── providers/
│   │   ├── base.py            # Abstract Provider
│   │   ├── openai.py          # OpenAI-Implementierung
│   │   ├── anthropic.py       # Anthropic-Implementierung
│   │   ├── mistral.py         # Mistral-Implementierung
│   │   └── ollama.py          # Lokale Modelle
│   ├── router.py              # Modell-Routing-Logik
│   ├── cache.py               # Response-Cache
│   └── cost_tracker.py        # Token- & Kosten-Tracking
├── prompts/
│   ├── engine.py              # Prompt-Rendering (Jinja2)
│   ├── templates/             # Basis-Templates
│   │   ├── system.j2          # System-Prompt-Template
│   │   ├── user_decision.j2   # User-Prompt für Entscheidungsrunde
│   │   └── user_respond.j2    # User-Prompt für Reaktion auf Angebote
│   └── compression.py         # Prompt-Kompression / Zusammenfassung
├── output/
│   ├── writer.py              # Strukturierte Output-Erzeugung
│   ├── schemas.py             # Output-Schemata (Pydantic)
│   ├── hasher.py              # Reproduzierbarkeits-Hashing
│   └── analysis.py            # Aggregation & Basisvisualisierungen
└── utils/
    ├── config.py              # Config-Loading & Merging
    ├── validation.py          # JSON-Schema-Validierung
    └── logging.py             # Structured Logging Setup
```

### 3.2 Scenario Engine

Verantwortlich für das Parsen und Auflösen der Szenario-Definition.

```
scenario.yaml + personas/*.yaml + run_config.yaml
                    │
                    ▼
         ┌─────────────────┐
         │ YAML Parser     │  PyYAML / ruamel.yaml
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Schema Validator │  jsonschema / Pydantic
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Reference        │  Löst persona_pool-Referenzen auf,
         │ Resolver         │  weist Personas zu Rollen zu
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Scenario         │  Immutable Datenstruktur:
         │ Object           │  - ResolvedScenario
         └─────────────────┘  - List[ResolvedAgent]
                              - InteractionConfig
                              - List[Incentive]
```

**Schlüsselentscheidung**: Die Zuordnung von Personas zu Rollen kann deterministisch (Reihenfolge) oder randomisiert (mit Seed) erfolgen. Bei `repetitions > 1` werden Persona-Zuordnungen variiert, um über Persona-Effekte zu mitteln.

### 3.3 Persona Manager

Erzeugt aus jeder `ResolvedAgent`-Definition einen lauffähigen Agenten mit:
- System-Prompt (gerendert aus Persona + Szenario-Kontext)
- Conversation History (anfangs leer)
- Decision Memory (vergangene eigene Entscheidungen)
- Metadata (ID, Rolle, Metriken)

```python
# Pseudocode — Persona-Instantiierung
@dataclass(frozen=True)
class AgentInstance:
    agent_id: str
    role_id: str
    persona_id: str
    system_prompt: str          # Gerendert aus Template + Persona + Szenario
    history: list[Message]      # Wächst mit jeder Runde
    decisions: list[Decision]   # Eigene vergangene Entscheidungen
    metadata: AgentMetadata     # Token-Verbrauch, Kosten, etc.
```

### 3.4 Interaction Orchestrator

Der Orchestrator ist das Herzstück — er steuert den Ablauf der Simulation.

```
┌─────────────────────────────────────────────────────┐
│               ORCHESTRATOR LOOP                      │
│                                                      │
│  for round in 1..max_rounds:                         │
│    │                                                 │
│    ├── 1. Build Round Context                        │
│    │   └── Für jeden Agenten: Sichtbare Infos        │
│    │       zusammenstellen (History, Entscheidungen   │
│    │       anderer, Anreize, eigene Constraints)      │
│    │                                                 │
│    ├── 2. Prompt Assembly                            │
│    │   └── Prompt Engine: System + User Prompt       │
│    │       mit allen Variablen rendern               │
│    │                                                 │
│    ├── 3. LLM Calls (parallel oder sequenziell)      │
│    │   └── Gateway → Router → Provider → Response    │
│    │       Cache prüfen → ggf. cached Response       │
│    │       Cost Controller: Budget prüfen            │
│    │                                                 │
│    ├── 4. Response Parsing & Validation              │
│    │   └── JSON extrahieren, Schema validieren,      │
│    │       Constraints prüfen, ggf. Retry            │
│    │                                                 │
│    ├── 5. State Update                               │
│    │   └── Entscheidungen in State schreiben,        │
│    │       History aktualisieren, Metriken updaten   │
│    │                                                 │
│    ├── 6. Logging                                    │
│    │   └── Decision Log, Token Log, Raw Response     │
│    │                                                 │
│    └── 7. Termination Check                          │
│        └── Konsens erreicht? Budget erschöpft?       │
│            Max Rounds? → Break oder Continue         │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Interaktionstopologien:**

| Topologie | Beschreibung | Use Case |
|---|---|---|
| `all_to_all` | Jeder Agent sieht alle Entscheidungen | Gruppenverhandlung |
| `pairwise` | Agenten verhandeln in Paaren | Bilaterale Verhandlung |
| `hub_spoke` | Ein zentraler Agent verhandelt mit allen | Authority negotiiert mit jedem Farmer einzeln |
| `custom` | Adjazenzmatrix definiert Sichtbarkeit | Komplexe Netzwerke |

### 3.5 LLM Gateway & Provider-Abstraktion

```
┌──────────────────────────────────────────────────┐
│                 LLM GATEWAY                       │
│                                                   │
│  ┌──────────┐    ┌──────────┐    ┌────────────┐  │
│  │  Cache    │    │  Router  │    │  Cost      │  │
│  │  Check    │───▶│  (Model  │───▶│  Check     │  │
│  │          │    │  Select) │    │  (Budget)  │  │
│  └──────────┘    └──────────┘    └──────┬─────┘  │
│       │ HIT          │                   │        │
│       │              │                   ▼        │
│       │         ┌────▼───────────────────────┐    │
│       │         │     Provider Interface     │    │
│       │         │  ┌────────┐ ┌──────────┐   │    │
│       │         │  │ OpenAI │ │ Anthropic│   │    │
│       │         │  └────────┘ └──────────┘   │    │
│       │         │  ┌────────┐ ┌──────────┐   │    │
│       │         │  │Mistral │ │  Ollama  │   │    │
│       │         │  └────────┘ └──────────┘   │    │
│       │         └────────────┬───────────────┘    │
│       │                      │                    │
│       │              ┌───────▼──────┐             │
│       └─────────────▶│  Normalize   │             │
│                      │  Response    │             │
│                      └───────┬──────┘             │
│                              │                    │
│                      ┌───────▼──────┐             │
│                      │  Log Token   │             │
│                      │  Usage       │             │
│                      └──────────────┘             │
└──────────────────────────────────────────────────┘
```

**Provider Interface** (abstrakt):

```python
class LLMProvider(Protocol):
    async def complete(
        self,
        messages: list[Message],
        model: str,
        temperature: float,
        max_tokens: int,
        response_format: ResponseFormat,
    ) -> LLMResponse:
        """Sendet Messages an LLM, gibt normalisierte Response zurück."""
        ...

@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: TokenUsage          # prompt_tokens, completion_tokens, total_tokens
    latency_ms: float
    cached: bool
    cost_usd: float            # Berechnet aus Token-Count × Preis
    request_id: str            # Provider-seitige Request-ID
    timestamp: datetime
```

Jeder Provider implementiert dieses Interface. Der Gateway normalisiert alle Responses auf dasselbe Format, unabhängig vom Anbieter.

### 3.6 Prompt Engine

Verwendet **Jinja2** statt einfacher `string.Template`-Substitution — ermöglicht Conditionals, Loops und Filter.

```jinja2
{# templates/system.j2 — System-Prompt-Template #}
Du bist {{ agent.persona.label }}.

## Dein Hintergrund
{{ agent.persona.background }}

## Deine Ziele
- Primär: {{ agent.persona.goals.primary }}
{% if agent.persona.goals.secondary %}
- Sekundär: {{ agent.persona.goals.secondary }}
{% endif %}

## Kontext der Verhandlung
{{ scenario.shared_context }}

## Teilnehmer
{% for other in visible_agents %}
- {{ other.label }} ({{ other.role }}): {{ other.public_description }}
{% endfor %}

## Deine Constraints
{% for c in agent.persona.constraints %}
- {{ c }}
{% endfor %}

## Antwortformat
Antworte ausschließlich im folgenden JSON-Format:
```json
{{ response_schema_example }}
```
```

**Prompt-Kompression**: Für fortgeschrittene Runden wird die History komprimiert:
- Runden 1–3: Vollständig im Prompt
- Runden 4–n: Zusammengefasst durch ein günstiges Modell oder algorithmisch (letzte 2 Runden voll + Summary der früheren)

### 3.7 Cost Controller

```
┌───────────────────────────────────────┐
│          COST CONTROLLER              │
│                                       │
│  Budget: $5.00    Spent: $3.27        │
│  ████████████████░░░░░  65.4%         │
│                                       │
│  Per-Call Tracking:                   │
│  ┌─────────────────────────────────┐  │
│  │ call_id: abc123                 │  │
│  │ model: gpt-4o                   │  │
│  │ prompt_tokens: 1,847            │  │
│  │ completion_tokens: 312          │  │
│  │ cost: $0.0142                   │  │
│  │ cached: false                   │  │
│  └─────────────────────────────────┘  │
│                                       │
│  Preistabelle (konfigurierbar):       │
│  gpt-4o:      $2.50/$10.00 per 1M    │
│  gpt-4o-mini: $0.15/$0.60  per 1M    │
│  mistral-sm:  $0.10/$0.30  per 1M    │
│  ollama:      $0.00/$0.00  per 1M    │
│                                       │
│  Actions:                             │
│  - WARN at 80% budget                │
│  - ABORT at 100% budget              │
│  - LOG every call                    │
└───────────────────────────────────────┘
```

### 3.8 State Manager

Der State ist **immutable per Round** — jede Runde erzeugt einen neuen State-Snapshot. Das ermöglicht:
- Vollständige Nachvollziehbarkeit
- Einfaches Debugging (State einer beliebigen Runde inspizieren)
- Parallelisierung ohne Mutexes

```python
@dataclass(frozen=True)
class RoundState:
    round_number: int
    agents: tuple[AgentState, ...]
    decisions: tuple[Decision, ...]
    metrics: RoundMetrics
    timestamp: datetime

@dataclass(frozen=True)  
class SimulationState:
    scenario_id: str
    repetition: int
    seed: int
    rounds: tuple[RoundState, ...]     # Append-only History
    cost_accumulated: CostSummary
    status: SimulationStatus           # running | completed | aborted | error
```

---

## 4. Output-Schicht: Ergebnis-Schemata

### 4.1 Output-Verzeichnisstruktur

```
output/runs/peatland-exp-001_20260525_143022/
├── manifest.json                    # Reproduzierbarkeits-Manifest
├── run_summary.json                 # Aggregierte Ergebnisse
├── config_snapshot/                 # Exakte Kopie aller Input-Dateien
│   ├── scenario.yaml
│   ├── personas/
│   │   ├── farmers.yaml
│   │   ├── authorities.yaml
│   │   └── ngos.yaml
│   └── run_config.yaml
├── repetitions/
│   ├── rep_001/
│   │   ├── decisions.jsonl          # Eine Zeile pro Agenten-Entscheidung
│   │   ├── rounds.json             # Runden-Zusammenfassungen
│   │   ├── cost_log.jsonl          # Token/Kosten pro API-Call
│   │   ├── agent_histories/
│   │   │   ├── farmer_conventional_large.json
│   │   │   ├── farmer_small_diversified.json
│   │   │   ├── ...
│   │   │   └── ngo_main.json
│   │   └── raw_responses/          # Ungefilterte LLM-Antworten
│   │       ├── round_01/
│   │       │   ├── farmer_conventional_large.json
│   │       │   └── ...
│   │       └── round_02/
│   │           └── ...
│   ├── rep_002/
│   │   └── ...
│   └── ...
├── analysis/
│   ├── acceptance_by_persona.csv    # Akzeptanzrate pro Persona-Typ
│   ├── cost_breakdown.csv           # Kosten nach Modell, Phase, Runde
│   ├── convergence.csv              # Runden bis Einigung
│   └── sensitivity.csv              # Ergebnisse pro Parameter-Variation
└── logs/
    ├── framework.log                # Strukturierter Anwendungslog
    └── errors.log                   # Fehler und Warnungen
```

### 4.2 Decision Log Schema (`decisions.jsonl`)

Jede Zeile ist ein eigenständiges JSON-Objekt — eine Agenten-Entscheidung pro Runde.

```jsonl
{
  "decision_id": "d_001_r01_farmer_conv",
  "run_id": "peatland-exp-001",
  "repetition": 1,
  "round": 1,
  "agent_id": "farmer_conventional_large",
  "role": "farmer",
  "persona_id": "conventional_large",
  "timestamp": "2026-05-25T14:30:45.123Z",
  
  "decision": {
    "accept_rewetting": false,
    "conditions": {
      "min_compensation": 1400,
      "max_contract_years": 10,
      "requires_exit_clause": true,
      "requires_paludiculture_support": false
    },
    "message_to_others": "Die aktuell angebotene Kompensation deckt nicht einmal meine Ernteausfälle. Ich brauche mindestens 1400 EUR pro Hektar und Jahr."
  },
  
  "reasoning": "Als Großbetrieb mit 60ha Moorfläche wäre der Ernteausfall bei Wiedervernässung erheblich. Die aktuell angebotenen 800 EUR/ha liegen deutlich unter meinem Break-Even von ca. 1200 EUR/ha.",
  
  "prompt_tokens": 2134,
  "completion_tokens": 287,
  "model": "gpt-4o",
  "cost_usd": 0.0167,
  "latency_ms": 1423,
  "cached": false,
  "parse_retries": 0
}
```

### 4.3 Cost Log Schema (`cost_log.jsonl`)

```jsonl
{
  "call_id": "c_001_r01_farmer_conv_decision",
  "timestamp": "2026-05-25T14:30:45.123Z",
  "repetition": 1,
  "round": 1,
  "agent_id": "farmer_conventional_large",
  "task": "decision",
  "provider": "openai",
  "model": "gpt-4o",
  "prompt_tokens": 2134,
  "completion_tokens": 287,
  "total_tokens": 2421,
  "cost_usd": 0.0167,
  "latency_ms": 1423,
  "cached": false,
  "cache_key_hash": "sha256:a1b2c3...",
  "retry_count": 0,
  "error": null
}
```

### 4.4 Reproduzierbarkeits-Manifest (`manifest.json`)

Enthält alles, was nötig ist, um den Run exakt zu reproduzieren.

```json
{
  "manifest_version": "1.0",
  "run_id": "peatland-exp-001",
  "timestamp_start": "2026-05-25T14:30:22Z",
  "timestamp_end": "2026-05-25T14:47:13Z",
  "duration_seconds": 1011,
  
  "reproducibility": {
    "seed": 42,
    "config_hash": "sha256:e4f5a6b7...",
    "scenario_hash": "sha256:1a2b3c4d...",
    "personas_hash": "sha256:5e6f7a8b...",
    "framework_version": "0.1.0",
    "framework_git_commit": "abc1234",
    "python_version": "3.12.4",
    "dependency_lock_hash": "sha256:9c0d1e2f..."
  },
  
  "environment": {
    "os": "macOS 15.2",
    "cpu": "Apple M3 Pro",
    "ram_gb": 18
  },

  "llm_models_used": [
    {
      "provider": "openai",
      "model": "gpt-4o",
      "model_version": "gpt-4o-2024-08-06",
      "tasks": ["decision"],
      "total_calls": 120,
      "total_tokens": 287400,
      "total_cost_usd": 2.14
    },
    {
      "provider": "openai",
      "model": "gpt-4o-mini",
      "tasks": ["reasoning_summary"],
      "total_calls": 40,
      "total_tokens": 52000,
      "total_cost_usd": 0.08
    }
  ],
  
  "totals": {
    "repetitions_completed": 10,
    "repetitions_failed": 0,
    "total_rounds": 73,
    "total_api_calls": 160,
    "total_tokens": 339400,
    "total_cost_usd": 2.22,
    "cache_hit_rate": 0.12
  },
  
  "results_summary": {
    "acceptance_rate_mean": 0.58,
    "acceptance_rate_std": 0.09,
    "rounds_to_consensus_mean": 6.2,
    "rounds_to_consensus_std": 1.8
  }
}
```

### 4.5 Run Summary (`run_summary.json`)

Aggregierte Ergebnisse über alle Wiederholungen hinweg.

```json
{
  "run_id": "peatland-exp-001",
  "scenario_id": "peatland-rewetting-negotiation",
  
  "per_persona_results": [
    {
      "persona_id": "conventional_large",
      "role": "farmer",
      "acceptance_rate": 0.30,
      "avg_min_compensation_demanded": 1380,
      "avg_rounds_to_decision": 7.2,
      "most_effective_incentive": "regulatory_pressure",
      "decision_variance": 0.15
    },
    {
      "persona_id": "small_diversified",
      "role": "farmer",
      "acceptance_rate": 0.80,
      "avg_min_compensation_demanded": 650,
      "avg_rounds_to_decision": 3.8,
      "most_effective_incentive": "paludiculture_support",
      "decision_variance": 0.08
    },
    {
      "persona_id": "ecological_pioneer",
      "role": "farmer",
      "acceptance_rate": 1.00,
      "avg_min_compensation_demanded": 420,
      "avg_rounds_to_decision": 2.1,
      "most_effective_incentive": "compensation",
      "decision_variance": 0.03
    },
    {
      "persona_id": "skeptical_traditional",
      "role": "farmer",
      "acceptance_rate": 0.20,
      "avg_min_compensation_demanded": 1850,
      "avg_rounds_to_decision": 9.1,
      "most_effective_incentive": "regulatory_pressure",
      "decision_variance": 0.22
    }
  ],
  
  "aggregate": {
    "overall_acceptance_rate": 0.575,
    "cost_per_simulation_usd": 0.222,
    "tokens_per_decision": 2421,
    "avg_rounds_to_termination": 6.2
  }
}
```

---

## 5. Technologie-Stack

| Komponente | Technologie | Begründung |
|---|---|---|
| Sprache | Python 3.12+ | Ökosystem, LLM-Libraries, wissenschaftliche Libs |
| Datenmodelle | Pydantic v2 | Validierung, Serialisierung, JSON-Schema-Generierung |
| Prompt-Templates | Jinja2 | Conditionals, Loops, Filter — mächtiger als string.Template |
| LLM-Clients | `openai`, `anthropic`, `mistralai` SDKs | Offizielle SDKs für Typsicherheit und Streaming |
| Async I/O | `asyncio` + `httpx` | Parallele API-Calls ohne Thread-Overhead |
| Config | `PyYAML` + `jsonschema` | YAML-Parsing + strikte Schema-Validierung |
| Caching | SQLite (`aiosqlite`) | Leichtgewichtig, kein externer Service nötig |
| CLI | `typer` | Modernes CLI mit Auto-Dokumentation |
| Logging | `structlog` | JSON-Logging für maschinelle Auswertbarkeit |
| Testing | `pytest` + `pytest-asyncio` | Standard, async-fähig |
| Analyse | `pandas` + `matplotlib` | Basis-Analyse und Visualisierung |

### Optionale Erweiterungen (nicht im Kern)

| Komponente | Technologie | Wenn nötig für... |
|---|---|---|
| Experiment-Tracking | MLflow oder Weights & Biases | Vergleich über viele Runs hinweg |
| Dashboard | Streamlit | Interactive Exploration der Ergebnisse |
| Distributed Caching | Redis | Hohe Parallelisierung, Multi-Maschinen |

---

## 6. Datenfluss End-to-End

```
USER
  │
  ▼
  $ framework run --scenario scenario.yaml --config run_config.yaml
  │
  ▼
┌──────────────────────────────────────────────────────────┐
│ 1. INIT                                                   │
│    ├── Load & validate scenario.yaml                      │
│    ├── Load & validate personas/*.yaml                    │
│    ├── Load & validate run_config.yaml                    │
│    ├── Resolve persona → role assignments (seeded)        │
│    ├── Initialize Cost Controller (budget = $5.00)        │
│    ├── Initialize Cache (SQLite)                          │
│    ├── Initialize LLM Gateway (providers, routing)        │
│    ├── Create output directory                            │
│    └── Snapshot configs to output/config_snapshot/         │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│ 2. SIMULATION LOOP (per repetition)                       │
│                                                           │
│    for rep in 1..repetitions:                             │
│      ├── Seed RNG with (base_seed + rep)                  │
│      ├── Instantiate agents (render system prompts)       │
│      │                                                    │
│      │   for round in 1..max_rounds:                      │
│      │     ├── Build per-agent round context               │
│      │     ├── Render user prompts (Jinja2)               │
│      │     ├── Check cache (content hash of messages)     │
│      │     ├── Route to model (router rules)              │
│      │     ├── Check budget (abort if exceeded)           │
│      │     ├── Call LLM (async, parallel for simultaneous)│
│      │     ├── Parse response → Decision (Pydantic)       │
│      │     │   └── On parse error: retry (max 3x)         │
│      │     ├── Validate decision against constraints      │
│      │     ├── Update state (immutable new RoundState)    │
│      │     ├── Write decision log (JSONL append)          │
│      │     ├── Write cost log (JSONL append)              │
│      │     ├── Write raw response (JSON)                  │
│      │     └── Check termination condition                │
│      │         └── consensus? max_rounds? budget?         │
│      │                                                    │
│      └── Write repetition summary                         │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│ 3. AGGREGATION & ANALYSIS                                 │
│    ├── Aggregate decisions across repetitions              │
│    ├── Compute per-persona acceptance rates                │
│    ├── Compute cost breakdown (per model, per round)      │
│    ├── Compute convergence metrics                        │
│    ├── Generate CSV exports                               │
│    ├── Generate basic plots (optional)                    │
│    └── Write run_summary.json + manifest.json             │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│ 4. OUTPUT                                                 │
│    output/runs/peatland-exp-001_20260525_143022/           │
│    ├── manifest.json         ← Reproduzierbarkeit         │
│    ├── run_summary.json      ← Aggregierte Ergebnisse     │
│    ├── config_snapshot/      ← Exakte Input-Kopie         │
│    ├── repetitions/          ← Detaildaten pro Rep        │
│    ├── analysis/             ← CSV + Plots                │
│    └── logs/                 ← Framework-Logs             │
└──────────────────────────────────────────────────────────┘
```

---

## 7. Kostenoptimierungs-Mechanismen

### 7.1 Übersicht der Strategien

```
                  KOSTEN PRO SIMULATION
                  ══════════════════════

  Baseline (naiv)              $0.45/sim
  ├── + Structured JSON Mode   $0.38/sim  (-16%)  weniger Retries
  ├── + Prompt Compression     $0.29/sim  (-24%)  weniger Input-Tokens
  ├── + Model Routing          $0.19/sim  (-34%)  günstigere Modelle für Sub-Tasks
  ├── + Response Caching       $0.17/sim  (-11%)  identische Prompts wiederverwenden
  └── + History Summarization  $0.14/sim  (-18%)  kompakter Kontext in späten Runden
                               ─────────
  Gesamt-Reduktion:            ~69%
  
  (Hypothetische Werte — exakte Messung ist Teil der Evaluation)
```

### 7.2 Detaillierte Mechanismen

| # | Strategie | Wie | Erwarteter Impact |
|---|---|---|---|
| 1 | **Structured Output** | `response_format: json` / Tool-Use statt Free-Text-Parsing | Eliminiert Parse-Retries (geschätzt 5–15% der Calls) |
| 2 | **Prompt Compression** | History in späten Runden zusammenfassen statt voll einzubetten | Reduziert Input-Tokens um 30–60% ab Runde 4+ |
| 3 | **Model Routing** | Entscheidungs-Task → starkes Modell; Zusammenfassung → günstiges Modell | 40–70% Kostenreduktion für Sub-Tasks |
| 4 | **Response Cache** | SHA-256 über (system_prompt + user_prompt) → Cache-Lookup | Effektiv bei `repetitions > 1` mit ähnlichen Prompts |
| 5 | **Token Budget** | Hard Limit pro Response (`max_tokens`), pro Runde, pro Run | Verhindert Runaway-Kosten durch verbose Responses |
| 6 | **Batch-API** | OpenAI Batch API (50% Rabatt, 24h SLA) für nicht-zeitkritische Runs | 50% Kostenreduktion bei akzeptabler Latenz |
| 7 | **Lokale Modelle** | Ollama-Fallback für Entwicklung/Testing, kein API-Cost | $0 für Iteration während Entwicklung |

---

## 8. Reproduzierbarkeit & Hashing

### 8.1 Config-Hashing

Jeder Run erhält einen deterministischen Hash über alle Inputs:

```
config_hash = SHA-256(
    canonical_json(scenario.yaml) +
    canonical_json(personas/*.yaml) +    # sortiert nach Dateiname
    canonical_json(run_config.yaml)
)
```

**Canonical JSON**: YAML wird in sortiertes, indentation-normalisiertes JSON konvertiert, bevor gehashed wird. Damit sind kosmetische YAML-Änderungen (Kommentare, Einrückung) irrelevant.

### 8.2 Seed-Strategie

```
base_seed (aus run_config.yaml, z.B. 42)
  │
  ├── Repetition 1: seed = hash(base_seed, 1) → deterministic RNG
  │   ├── Persona-Zuordnung
  │   ├── Turn-Order (bei random)
  │   └── Tie-Breaking
  │
  ├── Repetition 2: seed = hash(base_seed, 2) → deterministic RNG
  │   └── ...
  └── ...
```

**Wichtig**: Der LLM selbst ist *nicht* deterministisch (auch bei temperature=0 gibt es Varianz). Deshalb `repetitions > 1` für statistische Aussagekraft. Der Seed kontrolliert nur die *Framework-seitigen* Zufallsentscheidungen.

### 8.3 Was wird geloggt für Reproduzierbarkeit?

| Artefakt | Zweck |
|---|---|
| `config_snapshot/` | Exakte Eingabe-Dateien |
| `manifest.json → config_hash` | Identifikation identischer Setups |
| `manifest.json → framework_git_commit` | Framework-Version |
| `manifest.json → dependency_lock_hash` | Exakte Dependency-Versionen |
| `manifest.json → llm_models_used[].model_version` | Exakte Modellversion |
| `raw_responses/` | Ungefilterte API-Antworten |
| `cost_log.jsonl → cache_key_hash` | Nachvollziehbar welche Calls gecached wurden |

---

## Offene Design-Entscheidungen

> Zu klären während der Implementierung:

1. **Prompt-Sprache**: Jinja2 ist mächtig aber komplex. Reicht ein einfacherer Mechanismus (z.B. Python f-strings mit Sandboxing)?
2. **State-Persistenz**: Soll der State während des Runs gespeichert werden (für Crash-Recovery), oder nur am Ende?
3. **Streaming**: Sollen LLM-Responses gestreamt werden (für Live-Monitoring) oder reicht Batch-Collection?
4. **Plugin-System**: Soll es ein Plugin-Interface für custom Topologien, Provider, Metriken geben, oder reicht Vererbung?
5. **Szenario-Validierung**: Soll das Framework domänenspezifische Constraints validieren (z.B. "Budget der Authority reicht für angebotene Kompensation"), oder ist das Sache des Szenario-Autors?
6. **Multi-Language Prompts**: Sollen Prompts auf Deutsch oder Englisch sein? Sprachabhängigkeit der Ergebnisse als Evaluationspunkt?
