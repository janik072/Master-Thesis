# Masterarbeit — Detaillierter Umsetzungsplan

**Stand:** 31. Mai 2026
**Thesis-Titel:** Cost-Efficient Modeling of Multi-Stakeholder Problems via LLM-Based Agent Simulation

---

## Übersicht: Was existiert bereits

| Artefakt | Status | Pfad |
|---|---|---|
| Exposé (EN, LaTeX) | ✅ fertig | `Expose/Expose_Entwurf_EN.tex` |
| Architektur-Dokument (EN, LaTeX + TikZ) | ✅ fertig | `Architecture/architecture_draft.tex` |
| Architektur-Entwurf (DE, Markdown) | ✅ fertig | `Architecture/architecture_draft.md` |
| Betreuer-Codebase (Gift-Exchange ABM) | ✅ vorhanden | `P1-main/` |
| Framework-Code | ❌ noch nicht begonnen | — |

### Wiederverwendbar aus P1-main
- **YAML-Loader-Muster**: Config-Loading, Validation, Dot-Access, Snapshotting
- **Prompt-Builder-Muster**: Template-Rendering, Variablen-Konstruktion (→ Migration auf Jinja2)
- **Driver-Muster**: Batch-Execution, parallele Runs, Ordnerstruktur, Reproduzierbarkeits-Snapshots
- **Mistral-Client-Muster**: Retry/Backoff/Rate-Limiting (→ Generalisierung auf Multi-Provider)

### Nicht wiederverwendbar
- Gift-Exchange-Spiellogik, Photo-Treatment, Utility-Funktion, spielspezifische Visualisierung

---

## Phase 0: Projekt-Setup (3–4 Tage)

### 0.1 Repository-Struktur anlegen
```
mas-framework/                    # Neues Top-Level-Verzeichnis
├── pyproject.toml                # PEP 621, Dependencies, Scripts
├── README.md
├── .env.example                  # API-Key-Platzhalter (keine echten Keys!)
├── src/
│   └── mas/                      # Package-Name
│       ├── __init__.py
│       ├── cli.py                # Typer CLI: `mas run`, `mas validate`, `mas cost-report`
│       ├── schemas/              # Pydantic-Modelle + JSON-Schemas
│       ├── engine/               # Scenario Engine, Orchestrator
│       ├── persona/              # Persona Manager
│       ├── llm/                  # LLM Gateway, Provider-Adapter
│       ├── cost/                 # Cost Controller
│       ├── state/                # State Manager
│       ├── prompts/              # Jinja2-Templates
│       └── output/               # Logger, Manifest, Analysis
├── configs/                      # Beispiel-Szenarien
│   ├── scenarios/
│   ├── personas/
│   └── run_configs/
├── tests/
└── docs/
```

### 0.2 Tooling einrichten
- [ ] `pyproject.toml` mit allen Dependencies (siehe Architektur-Dokument)
- [ ] `uv` oder `pip` Virtual Environment
- [ ] Pre-commit hooks: `ruff` (Linting/Formatting), `mypy` (Type-Checking)
- [ ] pytest-Konfiguration mit `pytest-asyncio`
- [ ] `.env` Handling via `python-dotenv` (API-Keys niemals in YAML!)
- [ ] CI: GitHub Actions für Tests (optional, aber empfohlen)

### 0.3 Erster lauffähiger Smoke-Test
- [ ] `mas validate configs/scenarios/minimal.yaml` → validiert gegen JSON-Schema → Exit 0
- [ ] Sicherstellen, dass der gesamte Import-Graph funktioniert

**Deliverable:** Leeres aber lauffähiges Projekt mit `mas --help`

---

## Phase 1: Input Layer (4–5 Tage)

### 1.1 Pydantic-Schemas definieren
- [ ] `ScenarioConfig` — Rollen, Interaktionsregeln, Mechanismen, Rundenzahl, Topologie
- [ ] `PersonaConfig` — Name, Rolle, Hintergrund, Risikoprofil, Entscheidungsfaktoren (gewichtet), Persönlichkeits-Traits (0–1 Floats), Constraints
- [ ] `RunConfig` — Provider, Modell, Temperature, Routing-Regeln, Budget, Caching, Seed, Repetitions
- [ ] `ResolvedScenario` — Immutables Objekt nach Auflösung aller Referenzen

### 1.2 JSON-Schema-Generierung
- [ ] Automatische JSON-Schema-Generierung aus Pydantic-Modellen (`model_json_schema()`)
- [ ] Validierung: YAML laden → gegen Schema prüfen → Pydantic-Modell → `ResolvedScenario`
- [ ] Klare Fehlermeldungen bei Validierungsfehlern (Pfad, erwarteter Typ, erhaltener Wert)

### 1.3 Beispiel-Konfigurationen schreiben
- [ ] **Minimal-Szenario**: 2 Agenten, 3 Runden, 1 Mechanismus (zum Testen)
- [ ] **Peatland-Szenario**: 4–6 Agenten (2 Landwirte, 1 Behörde, 1 NGO, 1 Berater), 10 Runden, 3 Mechanismen
- [ ] **Benchmark-Szenario**: Ultimatum Game (2 Agenten, bekanntes Nash-Gleichgewicht)

### 1.4 Tests
- [ ] Schema-Validierung: gültige Configs → OK, ungültige → klarer Fehler
- [ ] Edge Cases: fehlende Felder, falsche Typen, leere Persona-Listen
- [ ] Round-Trip: YAML → Pydantic → dict → YAML → Pydantic (Gleichheit prüfen)

**Deliverable:** `mas validate scenario.yaml personas/ run_config.yaml` funktioniert fehlerfrei

---

## Phase 2: Core Engine — Grundgerüst (7–8 Tage)

### 2.1 Persona Manager
- [ ] Persona-YAML laden → Jinja2-System-Prompt rendern
- [ ] History-Verwaltung pro Agent (Liste von Runden-Snapshots)
- [ ] Methode: `get_context(agent_id, round_n)` → gibt relevanten Kontext zurück

### 2.2 Prompt Engine (Jinja2)
- [ ] Jinja2-Template-Loader mit Template-Verzeichnis
- [ ] System-Prompt-Template: Persona + Szenario-Kontext + Verhaltensregeln
- [ ] User-Prompt-Template: Rundenstatus + History + konkrete Entscheidungsfrage
- [ ] Output-Format-Template: JSON-Schema der erwarteten Antwort
- [ ] Tests: Template-Rendering mit Mock-Daten, alle Variablen aufgelöst

### 2.3 LLM Gateway (Basis-Version)
- [ ] Provider-Adapter-Interface: `async send(messages, model, temperature, **kwargs) → LLMResponse`
- [ ] `LLMResponse` Pydantic-Modell: `content`, `input_tokens`, `output_tokens`, `model`, `latency_ms`, `cached`
- [ ] **Ein** Provider implementieren (OpenAI via `openai` SDK) — reicht für Phase 2
- [ ] litellm-Integration als Alternative evaluieren (1 Adapter statt N)
- [ ] Retry-Logik mit exponential Backoff (aus P1-main übernehmen)

### 2.4 Interaction Orchestrator (Basis-Version)
- [ ] Runden-Loop: `for round in range(n_rounds):`
- [ ] Pro Runde: Agenten selektieren → Prompts bauen → LLM-Calls (sequenziell erstmal) → Responses parsen → State updaten
- [ ] Topologie: erstmal nur `all_to_all` implementieren
- [ ] Termination: fixe Rundenzahl (erweiterte Abbruchbedingungen später)
- [ ] Structured Output Parsing: JSON aus LLM-Response extrahieren + Pydantic-Validierung

### 2.5 State Manager
- [ ] `RoundState`: Immutable Snapshot pro Runde (alle Agenten-Entscheidungen, Zeitstempel)
- [ ] `SimulationState`: Liste aller `RoundState`s + Metadaten
- [ ] History-Zugriff: `state.get_history(agent_id, last_n=5)` für Prompt-Kontext

### 2.6 Erster End-to-End-Run
- [ ] Minimal-Szenario (2 Agenten, 3 Runden) läuft durch mit echtem API-Call
- [ ] Output: `decisions.jsonl` wird geschrieben
- [ ] Token-Counts werden korrekt erfasst

**Deliverable:** `mas run configs/scenarios/minimal.yaml configs/personas/ configs/run_configs/dev.yaml` → produziert `decisions.jsonl`

---

## Phase 3: Cost Controller & Tracking (3–4 Tage)

### 3.1 Token-Preis-Tabelle
- [ ] Statische Preistabelle: `{model: {input_per_1k: $, output_per_1k: $}}` für alle relevanten Modelle
- [ ] Konfigurierbar via `run_config.yaml` (eigene Preise für lokale Modelle)

### 3.2 Per-Call Cost Tracking
- [ ] Jeder LLM-Call → Eintrag in `cost_log.jsonl`: Zeitstempel, Agent, Runde, Modell, Input-Tokens, Output-Tokens, Kosten, Latenz, gecacht
- [ ] Laufende Summe pro Run

### 3.3 Budget Enforcement
- [ ] Warnung bei 80% des Budgets (→ Logging)
- [ ] Hard-Stop bei 100% (→ Run abbrechen, bisherige Ergebnisse speichern)
- [ ] Konfigurierbares Budget in `run_config.yaml`

### 3.4 Cost-Report CLI
- [ ] `mas cost-report output/run_20260601/` → Zusammenfassung: Gesamtkosten, Kosten/Runde, Kosten/Agent, Kosten/Token, teuerster Agent, teuerste Runde

**Deliverable:** Jeder Run produziert automatisch `cost_log.jsonl` + Budget wird enforced

---

## Phase 4: Kostenoptimierungs-Strategien (10–12 Tage) ⭐ FORSCHUNGSKERN

Dies ist der zentrale Beitrag der Arbeit. Jede Strategie wird als **isolierbares Feature** implementiert, das per Config ein/ausgeschaltet wird.

### 4.1 Baseline messen
- [ ] Peatland-Szenario mit GPT-4o, voller History, Freitext-Output, kein Caching
- [ ] 10 Runs → Baseline-Kosten, Baseline-Ergebnisse (Akzeptanzrate, Verteilung)
- [ ] Das ist der **Referenzpunkt** für alle weiteren Strategien

### 4.2 Strategie 1: Structured Output
- [ ] JSON-Mode / Function-Calling für Antworten erzwingen
- [ ] Messung: Output-Token-Reduktion, Parse-Fehler-Rate, Ergebnis-Delta zum Baseline

**Config-Flag:** `run_config.yaml → optimization.structured_output: true/false`

### 4.3 Strategie 2: Prompt-Kompression
- [ ] **Sliding Window**: Nur letzte N Runden im Kontext (konfigurierbar: `context_window: 3`)
- [ ] **Summary Mode**: LLM-generierte Zusammenfassung der bisherigen History statt vollem Log
- [ ] **Hybrid**: Volle letzte 2 Runden + Summary der älteren
- [ ] Messung: Input-Token-Reduktion, Ergebnis-Delta

**Config-Flag:** `run_config.yaml → optimization.context_strategy: full | sliding_window | summary | hybrid`

### 4.4 Strategie 3: Model Routing
- [ ] Regel-basiert: „Runde 1–2 = cheap model, Runde 3+ = strong model"
- [ ] Task-basiert: „Zusammenfassung = cheap, Entscheidung = strong"
- [ ] Routing-Regeln in `run_config.yaml` konfigurierbar
- [ ] Messung: Kostenreduktion, Ergebnis-Delta

**Config-Flag:** `run_config.yaml → optimization.model_routing: [{rounds: [1,2], model: gpt-4o-mini}, {rounds: "rest", model: gpt-4o}]`

### 4.5 Strategie 4: Response Caching
- [ ] SHA-256 Hash über (System-Prompt + User-Prompt + Model + Temperature)
- [ ] SQLite Cache: Hash → Response (mit TTL)
- [ ] Hit-Rate tracking
- [ ] Messung: Cache-Hit-Rate, gesparte Calls, Auswirkung auf Ergebnisvarianz

**Config-Flag:** `run_config.yaml → optimization.caching: {enabled: true, ttl_hours: 72}`

### 4.6 Strategie 5: Lokale Modelle
- [ ] Ollama-Integration (Llama-3, Mistral-small)
- [ ] Vergleich: Welche Tasks funktionieren lokal, welche nicht?
- [ ] Messung: Kosten = $0, aber Qualitäts-Delta und Latenz

**Config-Flag:** `run_config.yaml → llm.provider: ollama, llm.model: llama3:8b`

### 4.7 Waterfall-Experiment
- [ ] Alle 5 Strategien kumulativ anwenden (Stufe 1 bis Stufe 5)
- [ ] Pro Stufe messen: Kosten, Qualität, Latenz
- [ ] **Ergebnis-Tabelle**: Die zentrale Tabelle der Thesis

```
| Stufe | Strategie           | Kosten/Run | Δ Kosten | Qualität (r²) | Δ Qualität |
|-------|---------------------|------------|----------|----------------|------------|
| 0     | Baseline            | $X.XX      | —        | 1.00           | —          |
| 1     | + Structured Output | $X.XX      | -XX%     | 0.XX           | -X%        |
| 2     | + Prompt Compress.  | $X.XX      | -XX%     | 0.XX           | -X%        |
| 3     | + Model Routing     | $X.XX      | -XX%     | 0.XX           | -X%        |
| 4     | + Caching           | $X.XX      | -XX%     | 0.XX           | -X%        |
| 5     | + Local Models      | $X.XX      | -XX%     | 0.XX           | -X%        |
```

**Deliverable:** Jede Strategie per Config-Flag schaltbar, Waterfall-Ergebnis-Tabelle

---

## Phase 5: Output & Analyse-Pipeline (4–5 Tage)

### 5.1 Output-Formate finalisieren
- [ ] `decisions.jsonl` — Agent, Runde, Entscheidung, Reasoning, Tokens, Kosten, Modell, Latenz
- [ ] `cost_log.jsonl` — Granulare Kosten pro Call
- [ ] `manifest.json` — Config-Hash, Seed, Framework-Version, Git-Commit, Python-Version, Model-Versions
- [ ] `run_summary.json` — Aggregierte Ergebnisse pro Agent
- [ ] `config_snapshot/` — Exakte Kopie aller Input-Dateien

### 5.2 Reproduzierbarkeits-Hash
- [ ] SHA-256 über (scenario.yaml + personas/*.yaml + run_config.yaml + Framework-Version)
- [ ] Gleicher Hash = gleiche Konfiguration = vergleichbarer Run
- [ ] Hash als Ordnername: `output/runs/{hash_prefix}_{timestamp}/`

### 5.3 Analyse-Skripte
- [ ] Cost-Quality-Tradeoff-Plot (X: Kosten, Y: Qualitätsmetrik)
- [ ] Strategie-Vergleich: Grouped Bar Chart
- [ ] Varianz-Analyse: Boxplots über N Runs pro Strategie
- [ ] Export: CSV + matplotlib-Plots + LaTeX-Tabelle

### 5.4 Batch-Execution
- [ ] `mas batch configs/experiments/waterfall.yaml` → führt alle Strategiestufen automatisch aus
- [ ] Parallele Runs via `asyncio.gather` oder `ProcessPoolExecutor`
- [ ] Aggregierter Batch-Report

**Deliverable:** Vollständige Output-Pipeline, reproduzierbare Runs, Analyse-Plots

---

## Phase 6: Evaluation & Experimente (8–10 Tage) ⭐ FORSCHUNGSKERN

### 6.1 Experiment 1: Waterfall-Kostenoptimierung
- [ ] Baseline + 5 Strategiestufen × 10 Runs = 60 Runs
- [ ] Ergebnis: Cost-Quality-Tradeoff-Kurve (→ **zentrale Abbildung der Thesis**)
- [ ] Statistische Signifikanztests: Unterscheiden sich die Ergebnisse zwischen Stufen?

### 6.2 Experiment 2: Model-Vergleich
- [ ] Gleiches Szenario mit GPT-4o, GPT-4o-mini, Claude Sonnet, Mistral Large, Llama-3 lokal
- [ ] Pro Modell: 10 Runs → Kosten, Qualität, Latenz
- [ ] Ergebnis: Welches Modell bietet bestes Preis-Leistungs-Verhältnis?

### 6.3 Experiment 3: Peatland Use Case
- [ ] Vollständiges Szenario: 4–6 Agenten, 10 Runden, 3 Mechanismen (Pauschale, erfolgsbasiert, Hybrid)
- [ ] Pro Mechanismus: 10 Runs
- [ ] Ergebnis: Welcher Mechanismus → höchste Akzeptanzrate? (explorativer Charakter)

### 6.4 Experiment 4: Reproduzierbarkeit
- [ ] 30 Runs mit identischer Config (Seed fest, Temperature = 0.0 vs. 0.3 vs. 0.7)
- [ ] Ergebnis: Varianz-Koeffizient der Akzeptanzrate → „Wie reproduzierbar ist das?"

### 6.5 (Optional) Experiment 5: Benchmark-Validierung
- [ ] Ultimatum Game / Prisoner's Dilemma mit bekanntem theoretischem Ergebnis
- [ ] Weichen LLM-Agenten vom Nash-Gleichgewicht ab? In welche Richtung?
- [ ] Niedrige Priorität — nur wenn Zeit übrig

**Deliverable:** Alle Ergebnistabellen und Plots für die Thesis

---

## Phase 7: Thesis schreiben (parallel ab Phase 4, Fokus letzte 4–6 Wochen)

### 7.1 Kapitelstruktur (aus Exposé)
1. Introduction — Motivation, RQs, Contribution, Outline
2. Foundations — LLMs, ABM, Game Theory, Peatland Domain
3. Related Work — Horton, Park et al., AutoGen, CrewAI, CAMEL, LLM-Kostenoptimierung
4. Requirements — Funktionale/Nicht-funktionale Anforderungen, Use Case
5. Framework Design — Architektur, Schemas, Orchestrierung, LLM-Abstraktion, Kostenoptimierung
6. Implementation — Tech Stack, Core Components, Prompt Engineering, Caching, Tests
7. Evaluation — Alle Experimente, Ergebnisse, Diskussion
8. Conclusion — Zusammenfassung, Limitationen, Future Work

### 7.2 Schreib-Reihenfolge (empfohlen)
1. **Kap. 5 (Design)** — schon fast fertig (Architektur-Dokument anpassen)
2. **Kap. 6 (Implementation)** — parallel zur Implementierung mitschreiben
3. **Kap. 2 (Foundations)** — Literatur sammeln, parallel lesen
4. **Kap. 7 (Evaluation)** — sobald Experimente laufen
5. **Kap. 3 (Related Work)** — nach Evaluation (dann weißt du, wogegen du dich abgrenzt)
6. **Kap. 4 (Requirements)** — aus Exposé übernehmen + erweitern
7. **Kap. 1 (Introduction)** — ganz zum Schluss
8. **Kap. 8 (Conclusion)** — ganz zum Schluss

### 7.3 LaTeX-Setup
- [ ] Thesis-Template der Hochschule besorgen (oder eigenes auf Basis von Exposé)
- [ ] BibTeX-Datei mit allen Referenzen aus Exposé anlegen
- [ ] Abbildungen: TikZ für Architektur (existiert bereits), matplotlib-Export für Plots

---

## Zeitplan (Grobe Schätzung, 6 Monate)

```
Juni 2026    ████░░░░░░░░░░░░░░░░ Phase 0+1: Setup + Input Layer
Juli 2026    ░░████████░░░░░░░░░░ Phase 2: Core Engine Grundgerüst
Aug  2026    ░░░░░░░░████████░░░░ Phase 3+4: Cost Controller + Optimierungsstrategien
Sep  2026    ░░░░░░░░░░░░████████ Phase 4 (Rest) + Phase 5: Output + Analyse
Okt  2026    ░░░░░░░░░░░░░░██████ Phase 6: Experimente
Nov  2026    ░░░░░░░░░░░░░░░░████ Phase 7: Thesis schreiben (Hauptphase)
Dez  2026    ░░░░░░░░░░░░░░░░░░██ Finalisierung + Abgabe
```

**Thesis-Schreiben läuft parallel ab August!** Nicht alles auf November schieben.

---

## Risiken & Mitigationen

| Risiko | Wahrscheinlichkeit | Mitigation |
|---|---|---|
| API-Kosten explodieren | Mittel | Budget-Limits im Cost Controller, lokale Modelle für Dev |
| LLM-Antworten nicht parsebar | Hoch (am Anfang) | Structured Output + Retry + Fallback + robuste JSON-Extraktion |
| Ergebnisse nicht reproduzierbar | Mittel | Temperature=0.0 als Option, Varianz messen statt ignorieren |
| Peatland-Szenario zu komplex | Niedrig | Minimal-Szenario als Fallback, Peatland ist explorativ |
| Zeitdruck beim Schreiben | Hoch | Kapitel 5+6 parallel zur Implementierung schreiben |
| Provider-API-Änderungen | Niedrig | litellm abstrahiert, Gateway-Pattern isoliert Änderungen |

---

## Sofort nächste Schritte (diese Woche)

1. **`mas-framework/` Projekt anlegen** — `pyproject.toml`, Verzeichnisstruktur, Dependencies
2. **Pydantic-Schemas** für `ScenarioConfig`, `PersonaConfig`, `RunConfig` schreiben
3. **Minimal-Szenario YAML** schreiben (2 Agenten, 3 Runden)
4. **`mas validate`** CLI-Command implementieren
5. **Erster Test**: `pytest tests/test_schemas.py` — Schema-Validierung läuft
