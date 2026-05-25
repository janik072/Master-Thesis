# Exposé (Entwurf) — Masterarbeit

## Arbeitstitel

**Effiziente Modellierung ökonomischer Fragestellungen mittels LLM-basierter Multi-Agenten-Simulation: Entwurf, Implementierung und Evaluation eines kostenoptimierten Frameworks**

*(Alternativtitel: "A Cost-Efficient Framework for LLM-Based Agent Simulations in Computational Economics")*

---

## 1. Problemstellung & Motivation

Large Language Models (LLMs) haben in den letzten Jahren bemerkenswerte Fähigkeiten in der Nachahmung menschlicher Entscheidungsfindung gezeigt. Gleichzeitig wächst das Interesse, diese Modelle als synthetische Akteure in sozialwissenschaftlichen und ökonomischen Experimenten einzusetzen — etwa zur Simulation von Verhandlungen, Spieltheorie-Experimenten oder Marktdynamiken (vgl. Horton 2023, "Large Language Models as Simulated Economic Agents").

Bestehende Ansätze sind jedoch häufig:
- **ad hoc**: auf ein spezifisches Experiment zugeschnitten, ohne Wiederverwendbarkeit,
- **kostenintensiv**: durch ineffiziente Prompt-Strategien und fehlende Optimierung des API-Verbrauchs,
- **schwer reproduzierbar**: durch mangelnde Standardisierung der Experimental-Pipeline.

Es fehlt ein **generisches, kosteneffizientes Framework**, das es Forschern ermöglicht, beliebige (insbesondere ökonomische) Fragestellungen deklarativ zu definieren und mittels LLM-basierter Agenten systematisch zu simulieren und zu analysieren.

---

## 2. Zielsetzung

Ziel dieser Arbeit ist der Entwurf, die Implementierung und die Evaluation eines Frameworks für LLM-basierte Multi-Agenten-Simulationen mit folgenden Kerneigenschaften:

1. **Deklarative Szenario-Definition**: Forschungsfragen, Stakeholder, Personas, Constraints und Zielfunktionen werden über eine strukturierte Konfiguration (YAML/JSON-Schema) spezifiziert — ohne Code-Änderungen.

2. **Kostenoptimierung**: Systematische Reduktion der API-Kosten durch:
   - Prompt-Kompression und Token-Budgetierung
   - Intelligentes Modell-Routing (günstigere Modelle für einfachere Sub-Tasks)
   - Prompt-Caching und Response-Memoization
   - Structured Output Modes (Reduktion von Parsing-Fehlern und Retries)

3. **Performanz & Skalierbarkeit**: Effiziente Parallelisierung, Batching und Rate-Limit-Management für große Kohorten.

4. **Wissenschaftliche Rigorosität**: Reproduzierbarkeit durch Seed-Kontrolle, Konfigurationssnapshotting, vollständiges Audit-Trail und standardisierte Analyse-Pipeline.

5. **Multi-Provider-Unterstützung**: Abstraktion der LLM-Schnittstelle zur Unterstützung verschiedener Anbieter (OpenAI, Anthropic, Mistral, lokale Modelle via Ollama).

---

## 3. Forschungsfragen

**Hauptfrage:**
> Wie lässt sich ein generisches Framework für LLM-basierte Multi-Agenten-Simulationen gestalten, das zugleich kosteneffizient, performant und wissenschaftlich reproduzierbar ist?

**Teilfragen:**

- **F1 (Effizienz):** Welche Prompt-Engineering- und API-Optimierungsstrategien reduzieren die Kosten pro Simulation signifikant, ohne die Qualität der Agenten-Entscheidungen zu beeinträchtigen?

- **F2 (Validität):** Inwiefern können LLM-basierte Agenten bekannte spieltheoretische Gleichgewichte (Nash, Pareto) reproduzieren, und wie sensitiv sind die Ergebnisse gegenüber Modellwahl, Temperatur und Prompt-Variationen?

- **F3 (Generalisierbarkeit):** Wie muss die Framework-Architektur gestaltet sein, damit verschiedene Interaktionstypen (Verhandlung, Auktion, iteratives Spiel, Debatte) ohne Kerncode-Änderungen abgebildet werden können?

- **F4 (Skalierung):** Wie skalieren Kosten und Laufzeit mit der Anzahl der Agenten, Runden und Komplexität der Szenarien, und welche architektonischen Entscheidungen beeinflussen dies?

---

## 4. Methodik

### 4.1 Design Science Research

Die Arbeit folgt dem **Design Science Research**-Paradigma (Hevner et al. 2004): Entwurf eines IT-Artefakts (Framework), Implementierung, und systematische Evaluation.

### 4.2 Technische Umsetzung

**Phase 1 — Analyse & Anforderungen**
- Systematische Analyse bestehender Frameworks (AutoGen, CrewAI, LangGraph, CAMEL) und Abgrenzung
- Anforderungserhebung anhand von Referenz-Szenarien aus der experimentellen Ökonomie
- Analyse des bestehenden ABM-Prototypen (Gift-Exchange-Simulation mit Mistral)

**Phase 2 — Architektur & Implementierung**
- Entwurf einer modularen Architektur mit folgenden Komponenten:
  - **Scenario Engine**: Parst deklarative Szenario-Definitionen
  - **Agent Manager**: Instantiiert und verwaltet heterogene Agenten mit individuellen Personas
  - **Interaction Orchestrator**: Steuert Kommunikationstopologien und Rundenlogik
  - **LLM Abstraction Layer**: Provider-agnostische API-Schicht mit Retry, Caching, Routing
  - **Cost Controller**: Token-Tracking, Budget-Enforcement, Modell-Routing-Logik
  - **Analysis Pipeline**: Standardisierte Metriken, Visualisierungen, Export
- Implementierung in Python mit Fokus auf Erweiterbarkeit und Testbarkeit

**Phase 3 — Evaluation**
- **Benchmark-Szenarien**: Prisoner's Dilemma, Ultimatum Game, Gift Exchange, Public Goods Game — Vergleich der Agenten-Entscheidungen mit theoretischen Gleichgewichten
- **Kostenvergleich**: Messung der API-Kosten (Tokens, $) mit vs. ohne Optimierungen über identische Szenarien
- **Sensitivitätsanalyse**: Variation von Modell, Temperatur, Prompt-Strategie, Kohortengrößen
- **Reproduzierbarkeitstest**: Wiederholung identischer Konfigurationen und statistische Auswertung der Varianz

### 4.3 Evaluation-Kriterien

| Kriterium | Metrik |
|---|---|
| Kosteneffizienz | Tokens/Simulation, $/Simulation, Tokens/Entscheidung |
| Performanz | Latenz/Runde, Gesamtdauer, Durchsatz (Simulationen/Stunde) |
| Validität | Abweichung von theoretischen Gleichgewichten (MSE, Korrelation) |
| Reproduzierbarkeit | Varianz über identische Runs (Konfidenzintervalle) |
| Generalisierbarkeit | Anzahl unterstützter Szenariotypen ohne Code-Änderung |
| Usability | Lines of Config pro Szenario, Time-to-First-Result |

---

## 5. Abgrenzung zu bestehenden Arbeiten

| Framework/Arbeit | Fokus | Abgrenzung dieser Arbeit |
|---|---|---|
| AutoGen (Microsoft) | Multi-Agent Conversations für Software-Tasks | Kein Fokus auf wissenschaftliche Simulation, keine Kostenoptimierung |
| CrewAI | Task-orientierte Agent-Teams | Workflow-Orchestrierung, nicht wissenschaftliche Reproduzierbarkeit |
| LangGraph | Zustandsbasierte Agent-Graphen | Generisches Tool, kein Domain-spezifisches Szenario-Schema |
| CAMEL | Kommunikative Agenten | Role-Playing fokussiert, keine ökonomische Evaluation |
| Horton (2023) | LLMs als ökonomische Agenten | Einzelexperimente, kein Framework |
| Bestehendes ABM-Tool (Betreuer) | Gift-Exchange-Simulation | Domänenspezifisch, single-provider, keine Kostenoptimierung |
| **Diese Arbeit** | **Generisches, kostenoptimiertes Simulations-Framework** | **Deklarativ, multi-provider, kostenoptimiert, reproduzierbar** |

---

## 6. Vorläufige Gliederung

1. **Einleitung**
   - 1.1 Motivation und Problemstellung
   - 1.2 Zielsetzung und Forschungsfragen
   - 1.3 Aufbau der Arbeit

2. **Grundlagen**
   - 2.1 Large Language Models: Architektur, APIs, Kostenmodelle
   - 2.2 Agentenbasierte Modellierung (ABM)
   - 2.3 Spieltheorie und experimentelle Ökonomie
   - 2.4 Bewertung von LLM-Agenten: Validität, Reproduzierbarkeit

3. **Stand der Forschung**
   - 3.1 LLMs als simulierte ökonomische Akteure
   - 3.2 Multi-Agenten-Frameworks (AutoGen, CrewAI, LangGraph, CAMEL)
   - 3.3 Kostenoptimierung bei LLM-Anwendungen
   - 3.4 Forschungslücke und Beitrag dieser Arbeit

4. **Anforderungsanalyse**
   - 4.1 Funktionale Anforderungen
   - 4.2 Nicht-funktionale Anforderungen (Kosten, Performanz, Reproduzierbarkeit)
   - 4.3 Referenz-Szenarien und Benchmark-Definition

5. **Framework-Entwurf**
   - 5.1 Architekturübersicht
   - 5.2 Szenario-Definitionssprache (Schema-Entwurf)
   - 5.3 Agent-Lifecycle und Persona-Modellierung
   - 5.4 Interaktions-Orchestrierung und Topologien
   - 5.5 LLM-Abstraktionsschicht und Multi-Provider-Integration
   - 5.6 Kostenoptimierungsstrategien
   - 5.7 Analyse- und Reporting-Pipeline

6. **Implementierung**
   - 6.1 Technologie-Stack und Projektstruktur
   - 6.2 Kernkomponenten und Schnittstellen
   - 6.3 Prompt-Engineering-Strategien
   - 6.4 Caching, Batching und Parallelisierung
   - 6.5 Testabdeckung und Qualitätssicherung

7. **Evaluation**
   - 7.1 Experimentelles Setup
   - 7.2 Benchmark-Ergebnisse: Validität der Agenten-Entscheidungen
   - 7.3 Kostenanalyse: Optimiert vs. Baseline
   - 7.4 Performanz-Benchmarks: Latenz und Durchsatz
   - 7.5 Reproduzierbarkeitsanalyse
   - 7.6 Usability: Szenario-Definition und Time-to-Result
   - 7.7 Diskussion und Limitationen

8. **Fazit und Ausblick**
   - 8.1 Zusammenfassung der Ergebnisse
   - 8.2 Beantwortung der Forschungsfragen
   - 8.3 Limitationen
   - 8.4 Ausblick und zukünftige Arbeiten

---

## 7. Vorläufiger Zeitplan

| Phase | Zeitraum | Aufgaben |
|---|---|---|
| **1. Analyse** | Monat 1–2 | Literaturrecherche, Anforderungsanalyse, Benchmark-Definition, Analyse des Prototypen |
| **2. Entwurf** | Monat 2–3 | Architektur-Design, Schema-Entwurf, Technologieauswahl |
| **3. Implementierung** | Monat 3–5 | Kernframework, LLM-Integration, Kostenoptimierungen, Tests |
| **4. Evaluation** | Monat 4–5 | Benchmark-Experimente, Kostenvergleiche, Sensitivitätsanalysen |
| **5. Schreiben** | Monat 5–6 | Verschriftlichung, Review, Überarbeitung |

*(Annahme: 6 Monate Bearbeitungszeit, ggf. anpassen)*

---

## 8. Erwarteter Beitrag

1. **Praxisbeitrag**: Ein Open-Source-Framework, das Forschern ermöglicht, LLM-basierte Simulationen ohne tiefgreifende Programmierkenntnisse durchzuführen.
2. **Wissenschaftlicher Beitrag**: Systematische Evaluation von Kostenoptimierungsstrategien für LLM-Agentensysteme mit quantitativen Benchmarks.
3. **Methodischer Beitrag**: Entwurfsmuster und Best Practices für reproduzierbare LLM-basierte Experimentalsimulationen.

---

## 9. Vorläufige Literatur

- Horton, J. J. (2023). "Large Language Models as Simulated Economic Agents: What Can We Learn from Homo Silicus?" *NBER Working Paper*.
- Park, J. S. et al. (2023). "Generative Agents: Interactive Simulacra of Human Behavior." *UIST '23*.
- Aher, G. V. et al. (2023). "Using Large Language Models to Simulate Multiple Humans and Replicate Human Subject Studies." *ICML '23*.
- Li, G. et al. (2023). "CAMEL: Communicative Agents for 'Mind' Exploration of Large Language Model Society." *NeurIPS '23*.
- Wu, Q. et al. (2023). "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation." *arXiv preprint*.
- Hevner, A. R. et al. (2004). "Design Science in Information Systems Research." *MIS Quarterly*.
- Teubner, T. & Camacho, S. (2025). [Referenz für Gift-Exchange-Studien mit LLMs — Quelle beim Betreuer erfragen].
- Chen, L. et al. (2023). "FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance." *arXiv preprint*.

---

## 10. Benötigte Ressourcen

- LLM-API-Zugang (OpenAI, Anthropic, Mistral) — geschätztes Budget: 50–200€ für Evaluation
- Compute: Lokaler Rechner für Framework-Entwicklung; ggf. GPU für lokale Modelle (Ollama)
- Zugang zum bestehenden Prototyp-Repository des Betreuers
- Zugang zu relevanter Literatur (Universitätsbibliothek)

---

*Stand: Mai 2026 — Entwurf zur Diskussion mit dem Betreuer*
