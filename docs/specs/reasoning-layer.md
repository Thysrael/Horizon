# Reasoning Layer Specification

**Status:** Proposed

**Version:** 1.1

**Classification:** Foundational Intelligence Specification

**Last Updated:** November 20, 2026

**Constitutional parent:** [Daily Intelligence Brief Vision Specification](daily-intelligence-brief-vision.md)

**Related specifications:**

- [Knowledge Layer Specification](knowledge-layer.md)
- [Memory Architecture Specification](memory-architecture.md)
- [Recommendation Engine Specification](recommendation-engine.md)
- [Agent Accountability Specification](agent-accountability.md)
- [Editorial Steering Specification](editorial-steering.md)

---

## 1. Purpose

The Reasoning Layer transforms knowledge and evidence into intelligence.

Its responsibilities include:

- evaluating observations;
- interpreting patterns;
- identifying assumptions;
- comparing alternatives;
- generating critique;
- detecting opportunities and risks;
- producing recommendations;
- preserving uncertainty and contradiction.

The Reasoning Layer does not merely retrieve or summarize information. It evaluates and interprets information for judgment and decision support.

## 2. Mission

The Reasoning Layer SHOULD answer:

- what does this mean;
- why does it matter;
- what should happen next;
- what assumptions should be challenged;
- what opportunities are emerging;
- what risks are increasing;
- what alternatives remain plausible;
- what evidence is missing.

The role of reasoning is to convert knowledge into judgment.

## 3. Architectural Position

The Reasoning Layer sits between knowledge and downstream intelligence generation:

```text
Context Collection
        |
        v
Memory Architecture
        |
        v
Knowledge Layer
        |
        v
Reasoning Layer
        |
        v
Recommendations
Critiques
Insights
Counterpoints
Warnings
Strategic Themes
Predictions
```

The Reasoning Layer is a producer of intelligence artifacts, not the delivery formatter and not the external action executor.

## 4. Core Philosophy

Knowledge without reasoning is reference material.

Reasoning without knowledge is speculation.

The system SHOULD reason from evidence and SHOULD distinguish evidence-supported claims from assumptions, interpretations, and generated hypotheses.

It SHOULD NOT optimize for:

- agreement;
- popularity;
- engagement;
- confidence volume;
- output quantity;
- a model's internal fluency.

## 5. Primary Responsibilities

The Reasoning Layer SHOULD provide:

- recommendation generation;
- critique generation;
- opportunity detection;
- risk detection;
- contradiction detection;
- pattern interpretation;
- strategic analysis;
- assumption evaluation;
- priority identification;
- counterpoint generation;
- prediction or forecast support.

## 6. Reasoning Inputs

The Reasoning Layer SHOULD consume only authorized and sufficiently traceable inputs.

Inputs MAY include:

- Work Context Brief;
- memory records;
- knowledge objects;
- evidence and source documents;
- feedback and outcomes;
- active recommendations;
- archive and longitudinal patterns;
- agent perspectives;
- project and preference state;
- contradictory or missing evidence notices.

Every major input SHOULD carry:

- source identity;
- timestamp or valid range;
- confidence;
- sensitivity;
- provenance;
- staleness or contradiction state.

## 7. Reasoning Outputs

The Reasoning Layer MAY generate:

- recommendations;
- critiques;
- insights;
- counterpoints;
- opportunities;
- warnings;
- strategic themes;
- patterns;
- forecasts;
- alternative futures;
- follow-up questions;
- assumption changes.

Each output SHOULD declare:

- output type;
- claim or conclusion;
- evidence;
- assumptions;
- unknowns;
- dependencies;
- confidence;
- importance;
- producing and contributing agents;
- generation context;
- horizon;
- revision or supersession state.

## 8. Reasoning Types

The platform SHOULD support multiple reasoning modes.

### 8.1 Analytical reasoning

Examines evidence and relationships.

Question:

“What does the evidence suggest?”

### 8.2 Strategic reasoning

Examines long-term implications and tradeoffs.

Question:

“What matters most over time?”

### 8.3 Critical reasoning

Challenges assumptions and identifies weaknesses.

Question:

“What might be wrong, missing, or overstated?”

### 8.4 Comparative reasoning

Evaluates alternatives.

Question:

“Which option appears strongest under the stated evidence?”

### 8.5 Reflective reasoning

Examines history and outcomes.

Question:

“What have we learned, and what assumption changed?”

### 8.6 Predictive reasoning

Examines future possibilities.

Question:

“What is likely to happen under which conditions?”

Predictive outputs MUST expose uncertainty and SHOULD not be presented as current facts.

## 9. Multi-Horizon Reasoning

Reasoning SHOULD operate across defined horizons.

| Horizon | Scope |
| --- | --- |
| Operational | Hours to days. |
| Tactical | Days to weeks. |
| Strategic | Weeks to months. |
| Long-term | Months to years. |

The engine SHOULD use horizon-specific evidence and SHOULD distinguish:

- immediate action;
- near-term follow-up;
- strategic initiative;
- historical lesson.

## 10. Assumption Management

Assumptions SHOULD be explicit.

Every major reasoning artifact SHOULD identify:

- assumptions;
- dependencies;
- constraints;
- unknowns;
- counterevidence;
- confidence limitations;
- conditions that would invalidate the conclusion.

The system SHOULD maintain an assumption relationship to the relevant knowledge or recommendation.

Hidden assumptions SHOULD be identified as a critique risk.

## 11. Contradiction Management

The Reasoning Layer SHOULD actively identify tension.

Examples include:

- one project priority contradicting another;
- a recommendation contradicting a known outcome;
- source evidence disagreeing;
- a stable principle conflicting with a new observation;
- historical truth differing from present context.

Contradictions SHOULD produce:

- a visible conflict;
- supporting evidence;
- scope and time differences;
- lower overall confidence where unresolved;
- a follow-up question or review;
- a supersession or reconciliation if evidence resolves the conflict.

The system SHOULD not average contradictory claims into false certainty.

## 12. Evidence Quality

Reasoning outputs SHOULD distinguish:

- direct evidence;
- source-supported inference;
- model interpretation;
- repeated dependent claims;
- independent corroboration;
- missing evidence;
- stale evidence;
- unverifiable evidence.

Evidence quality SHOULD affect confidence but SHOULD not be the sole determinant of importance.

The platform SHOULD expose uncertainty rather than hiding weak evidence behind a confident summary.

## 13. Critique Generation

Critique is a first-class output.

Critique SHOULD identify:

- weak reasoning;
- hidden assumptions;
- missing evidence;
- governance gaps;
- strategic risks;
- architectural weaknesses;
- evidence contradictions;
- misleading certainty;
- recommendation or source bias.

Critique SHOULD remain constructive:

- explain the concern;
- identify evidence;
- describe impact;
- propose review or resolution;
- avoid personal, adversarial, or manufactured criticism.

## 14. Opportunity Detection

The system SHOULD search for opportunities.

Examples include:

- emerging technologies;
- reusable frameworks;
- process improvements;
- knowledge reuse;
- automation opportunities;
- strategic leverage;
- cross-project synergy;
- unserved risk mitigation.

Opportunity claims SHOULD include:

- evidence;
- affected projects or themes;
- expected value;
- uncertainty;
- implementation dependencies;
- horizon.

## 15. Risk Detection

The system SHOULD identify:

- technical risks;
- strategic risks;
- architectural risks;
- knowledge risks;
- governance risks;
- privacy risks;
- outcome risks;
- source reliability risks.

The earlier a material risk is detected, the more useful it may be.

Risk statements SHOULD include:

- current evidence;
- severity;
- likelihood;
- horizon;
- uncertainty;
- affected scope;
- possible early warning;
- mitigating or investigative action.

## 16. Pattern Interpretation

The Reasoning Layer SHOULD interpret patterns rather than merely detect them.

Example:

```text
Pattern:
A recommendation has been ignored repeatedly.

Interpretation:
The recommendation may lack relevance, timing, evidence,
authority, implementation feasibility, or strategic alignment.
```

An interpretation SHOULD list plausible explanations and SHOULD not choose one without evidence.

## 17. Recommendation Support

Every recommendation SHOULD answer:

- why was this suggested;
- what evidence supports it;
- what assumptions remain;
- what contradiction or uncertainty exists;
- what outcome would be expected;
- why attention is warranted now;
- what alternative would be reasonable.

Recommendations SHOULD remain traceable to the [Recommendation Engine Specification](recommendation-engine.md).

The Reasoning Layer SHOULD not present a recommendation as approved or implemented by generating it.

## 18. Counterpoint Generation

The system SHOULD intentionally generate credible opposing perspectives.

Examples include:

- alternative architectures;
- competing strategies;
- contradictory evidence;
- alternative priorities;
- a lower-impact explanation;
- a different causal interpretation.

Counterpoints SHOULD:

- be relevant;
- contain evidence;
- disclose uncertainty;
- respect current context;
- avoid controversy for its own sake.

## 19. Confidence Generation

Reasoning outputs SHOULD include bounded confidence and SHOULD expose calibration limits.

Confidence SHOULD reflect:

- evidence quality;
- source agreement and independence;
- knowledge density;
- historical outcome;
- contradiction level;
- source freshness;
- model or agent calibration;
- missing evidence.

Confidence SHOULD not represent certainty or popularity.

The output SHOULD prefer:

- a bounded numeric score;
- a qualitative level;
- an uncertainty interval;
- or a combination.

No fixed mapping is normative in this specification.

## 20. Strategic Theme Recognition

The Reasoning Layer SHOULD identify themes that span projects or time.

Examples include:

- governance;
- knowledge management;
- memory reliability;
- agent quality;
- decision intelligence;
- specification stewardship;
- repository complexity.

Themes SHOULD include:

- evidence;
- scope;
- confidence;
- projects or sources;
- historical persistence;
- contrary evidence.

## 21. Feedback Integration

Reasoning quality SHOULD improve from outcomes and feedback.

Inputs include:

- implemented recommendations;
- successful or adverse outcomes;
- user evaluations;
- corrected assumptions;
- contradictory evidence;
- repeated ignored recommendations;
- retrospective analysis.

Feedback SHOULD follow the [Feedback Learning Specification](feedback-learning.md).

No behavioral signal SHOULD override explicit contradiction or outcome evidence without a policy.

## 22. Agent Collaboration

Complex reasoning MAY involve multiple agents.

Example:

```text
Research Agent
        |
        v
Strategy Agent
        |
        v
Critique Agent
        |
        v
Recommendation Agent
```

The collaboration SHOULD preserve:

- primary agent;
- contributing agents;
- critique or review agent;
- model configuration;
- source evidence;
- disagreements;
- revision and approval boundaries.

Agent accountability SHOULD follow the [Agent Accountability Specification](agent-accountability.md).

## 23. Debate and Consensus

The platform MAY use:

- independent analysis;
- debate;
- adversarial critique;
- scenario analysis;
- multi-agent consensus;
- source triangulation.

Consensus SHOULD not be presented as independent confirmation when:

- agents share the same evidence;
- agents share the same underlying model;
- agents inherit the same context;
- the same conclusion is repeated without new evidence.

Disagreement SHOULD remain visible if it is materially useful.

## 24. Reasoning Traceability

Every major reasoning artifact SHOULD preserve:

- inputs;
- evidence;
- knowledge objects;
- memory references;
- assumptions;
- unknowns;
- contradictions;
- producing and contributing agents;
- model or policy version;
- generation time;
- revision and supersession.

Traceability SHOULD be operationally sufficient to explain:

- why the conclusion was produced;
- what evidence supported it;
- what evidence challenged it;
- what uncertainty remains.

## 25. Scenario and Forecasting Support

Scenario analysis SHOULD use:

- baseline;
- alternative assumptions;
- candidate outcomes;
- evidence;
- probability or confidence;
- branch dependencies;
- time horizon;
- invalidation conditions.

Forecasts SHOULD not be presented as certain outcomes.

The system SHOULD compare forecast quality over time and SHOULD remain conservative about causation.

## 26. Advisory Boundary

Reasoning outputs are advisory.

The Reasoning Layer MUST NOT:

- execute external actions;
- approve consequential changes;
- claim implementation or outcome;
- present speculative forecasts as facts;
- conceal contradiction;
- optimize for agreement or persuasion;
- bypass explicit user authorization.

Any separate execution system MUST require explicit authorization and preserve an audit trail.

## 27. Privacy

Reasoning MAY process sensitive project, financial, health, relationship, or employment context.

The system MUST:

- keep core reasoning local unless explicitly authorized;
- disclose external provider use;
- apply sensitivity and provenance;
- prevent private reasoning from public or shared outputs;
- support deletion or invalidation of derived reasoning;
- preserve export and correction.

The system SHOULD separate:

- private reasoning;
- public edition synthesis;
- external model inference;
- evidence retrieval.

## 28. Failure Modes

### 28.1 Assumption cascades

Incorrect assumptions create a chain of poor conclusions.

Mitigations include:

- explicit assumptions;
- contradiction detection;
- evidence review;
- confidence reduction;
- counterpoint.

### 28.2 Overconfidence

Confidence exceeds evidence quality.

Mitigations include:

- calibration;
- uncertainty intervals;
- contradiction visibility;
- source diversity;
- minimum evidence thresholds.

### 28.3 Echo-chamber reasoning

Reasoning reinforces existing beliefs.

Mitigations include:

- counterpoint;
- independent evidence;
- challenge budget;
- user-visible contrary evidence.

### 28.4 Knowledge gaps

Missing information degrades quality.

Mitigations include:

- missing evidence labels;
- confidence penalties;
- follow-up questions;
- defer or abstain from unsupported conclusions.

### 28.5 Complexity inflation

Reasoning becomes unnecessarily complicated.

Mitigations include:

- simpler explanations;
- bounded output;
- strongest-evidence focus;
- explicit uncertainty.

### 28.6 Speculative certainty

A prediction or interpretation is presented as established fact.

Mitigations include:

- forecast type labels;
- assumptions;
- scenario framing;
- evidence and horizon.

### 28.7 Recommendation leakage

Reasoning bypasses evaluation and becomes a direct action.

Mitigations include:

- advisory state separation;
- authorization checks;
- lifecycle enforcement;
- audit logging.

## 29. Reasoning Health Metrics

Candidate metrics include:

- recommendation success;
- critique accuracy;
- opportunity yield;
- risk detection lead time;
- false-positive risk;
- false-negative risk;
- contradiction detection rate;
- assumption correction rate;
- calibration error;
- counterpoint utility;
- reasoning latency;
- traceability coverage.

Metrics SHOULD include sample size and time window and SHOULD not optimize output quantity.

## 30. Success Criteria

The Reasoning Layer succeeds when:

- recommendations improve decision quality;
- risks are identified earlier;
- opportunities are discovered sooner;
- assumptions become visible;
- critiques improve outcomes;
- counterpoints remain credible;
- user trust increases;
- long-term intelligence quality improves;
- conclusions remain traceable and revisable.

Success MUST be measured across outcomes and calibration, not generation volume.

## 31. Architectural Boundaries

The Reasoning Layer SHOULD remain separate from:

- raw context collection;
- memory storage;
- knowledge ontology maintenance;
- recommendation lifecycle and presentation;
- feedback storage;
- final delivery formatting;
- external action execution.

Subordinate specifications SHOULD define:

- reasoning artifact schemas;
- input and evidence interfaces;
- assumption and contradiction structures;
- confidence and horizon definitions;
- agent collaboration;
- traceability;
- forecast and scenario formats;
- privacy and observability.

## 32. Governance

Changes to reasoning modes, evidence rules, confidence, horizon, critique, or output categories MUST:

- identify affected vision requirements;
- preserve traceability;
- preserve anti-echo-chamber behavior;
- document evidence and privacy impact;
- include migration behavior;
- define rollback and audit procedures.

The Reasoning Layer MAY evolve models and orchestration strategies. Its role as the evidence-aware producer of judgment, critique, and advisory intelligence SHOULD remain stable.
