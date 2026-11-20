# Agent Accountability Specification

**Status:** Proposed

**Version:** 1.1

**Classification:** Core Intelligence Specification

**Last Updated:** November 20, 2026

**Constitutional parent:** [Daily Intelligence Brief Vision Specification](daily-intelligence-brief-vision.md)

**Related specifications:**

- [Recommendation Engine Specification](recommendation-engine.md)
- [Feedback Learning Specification](feedback-learning.md)
- [Daily Intelligence Delivery Platform Specification](daily-intelligence-delivery-platform.md)

---

## 1. Purpose

The Agent Accountability System measures, evaluates, and improves the performance of components that produce intelligence artifacts.

Its purpose is learning and calibration, not punishment.

The system SHOULD make it possible to identify:

- which agents produce value;
- which agents identify risks early;
- which agents create useful recommendations;
- which agents generate noise or unsupported claims;
- which agents improve outcomes;
- which agents remain uncalibrated or lack evidence.

Every significant intelligence artifact SHOULD be traceable to its producing agents and model configuration.

## 2. Objectives

The system SHOULD support:

- visibility;
- traceability;
- evaluation;
- calibration;
- continuous improvement;
- bounded influence;
- agent or component retirement.

The platform SHOULD evaluate agents based on demonstrated value, not output volume, confidence, popularity, or agreement.

## 3. Core Principles

### 3.1 Outcomes over output volume

An agent that produces ten recommendations of which eight create value is not automatically worse or better than an agent that produces one hundred recommendations.

Output volume is a workload metric, not a quality metric.

The platform SHOULD compare agents using:

- evaluable artifact count;
- observed value;
- outcome attribution;
- false positive and false negative evidence;
- calibration;
- confidence and denominator.

### 3.2 Provenance

No significant recommendation, critique, insight, summary, or counterpoint SHOULD enter the edition without traceable provenance.

Provenance SHOULD distinguish:

- generating agent;
- contributing agents;
- underlying model or provider;
- model and prompt configuration;
- source evidence;
- generation context;
- revision history.

### 3.3 Conservative attribution

An agent SHOULD receive credit or responsibility only for the role it materially performed.

Shared context, source retrieval, and orchestration SHOULD not be attributed solely to the final synthesis agent.

The system SHOULD preserve primary and contributing roles where multiple components participate.

### 3.4 Sample awareness

No quality conclusion SHOULD be drawn from a small or biased sample.

Metrics SHOULD include:

- sample size;
- evaluation coverage;
- time window;
- confidence or uncertainty;
- sparse-outcome state;
- explicit and inferred outcomes.

Raw percentages without denominators SHOULD not be used for ranking or influence.

### 3.5 Diversity preservation

Accountability MUST NOT create an undisclosed monopoly for one agent or perspective.

It SHOULD preserve:

- constructive dissent;
- cross-model comparison;
- independent evidence;
- exploratory counterpoints;
- source diversity.

Low historical value SHOULD reduce influence gradually, not eliminate a legitimate challenge or risk class.

## 4. Agent Scope

An Agent is any component that materially produces or transforms an intelligence artifact.

Examples include:

- context agent;
- project agent;
- strategy agent;
- critique agent;
- recommendation agent;
- research agent;
- repository agent;
- memory agent;
- risk agent;
- opportunity agent;
- counterpoint agent;
- editorial agent.

Future agents MAY be added without changing the accountability data model.

## 5. Agent Identity

The system SHOULD maintain distinct identities for:

- agent type;
- agent instance;
- agent version;
- prompt or policy version;
- model identity;
- model version;
- provider;
- deployment configuration.

An example identity record is:

```json
{
  "agent_id": "agent_strategy_v4",
  "agent_name": "Strategy Agent",
  "agent_type": "strategy",
  "agent_version": "4",
  "policy_version": "2026-11",
  "model": "provider/model/version",
  "created_at": "2026-11-20T09:00:00Z"
}
```

The example is conceptual. Subordinate specifications MUST define stable identifiers and privacy-safe provider attribution.

## 6. Agent Responsibilities

Each agent SHOULD have:

- purpose;
- declared input types;
- allowed output types;
- evidence requirements;
- scope boundaries;
- safety and privacy constraints;
- evaluation metrics;
- owner or configuration reference;
- retirement or supersession behavior.

Responsibilities SHOULD overlap only when the overlap serves independent critique or verification.

## 7. Artifact Attribution

Every significant artifact SHOULD record:

- generating agent;
- contributing agents;
- generation timestamp;
- generation context;
- source evidence;
- model configuration;
- reasoning or transformation stage;
- revision history;
- evaluation and outcome links.

For collaborative artifacts, the platform SHOULD preserve:

- primary attribution;
- contributor attribution;
- reviewer or critic attribution;
- source-retrieval attribution;
- lineages that merge or split evidence.

No output SHOULD be presented as generated by an agent that did not materially produce or revise it.

## 8. Evaluated Artifacts

The accountability system SHOULD evaluate:

- recommendations;
- critiques;
- insights;
- summaries;
- opportunity detection;
- risk detection;
- counterpoints;
- project assessments;
- historical interpretations;
- forecasts;
- evidence synthesis.

Each artifact SHOULD be evaluated according to its purpose.

For example:

- a summary should be measured for accuracy and omission;
- a recommendation should be measured for value and outcome;
- a critique should be measured for real blind spots;
- a counterpoint should be measured for credible challenge;
- a forecast should be measured for calibration and error.

Not every reading preference should be treated as evidence of intelligence quality.

## 9. Performance Metrics

Metrics SHOULD include both counts and rates.

Candidate metrics include:

| Metric | Meaning |
| --- | --- |
| Artifact count | Number of artifacts produced. |
| Evaluable count | Number with sufficient follow-up to evaluate. |
| Evaluation coverage | Evaluated artifacts divided by artifacts eligible for evaluation. |
| Implementation count | Number of recommendations acted on. |
| Positive outcome count | Number associated with beneficial outcomes. |
| Negative outcome count | Number associated with harmful or adverse outcomes. |
| Inconclusive outcome count | Number with follow-up but no attributable result. |
| Incorrect count | Number with factual or logical errors. |
| Incomplete count | Number missing material evidence or context. |
| Superseded count | Number replaced by later intelligence. |
| Usefulness score | Explicit helpfulness among evaluated artifacts. |
| Challenge utility | Value added by credible dissent or counterpoint. |
| Calibration score | Alignment between stated confidence and observed outcomes. |

Metrics SHOULD be windowed and SHOULD report sample size.

## 10. Usefulness and Outcome

Usefulness and outcome are distinct measures.

### 10.1 Usefulness

Usefulness reflects whether the artifact improved understanding or decision quality.

It MAY derive from:

- explicit Helpful or Not Helpful feedback;
- implemented or completed recommendations;
- user-corrected context;
- subsequent outcome evidence;
- repeated validated reference.

Usefulness MUST not be inferred solely from dwell time or popularity.

### 10.2 Outcome

Outcome reflects an observed consequence associated with an artifact.

Outcome scores SHOULD require:

- a target artifact;
- a structured result;
- observation time;
- outcome confidence;
- attribution confidence;
- causal evidence;
- follow-up period.

The system MUST distinguish:

- correlation;
- temporal association;
- plausible contribution;
- demonstrated contribution;
- proven contribution.

Outcome-based learning SHOULD receive greater weight than a reaction when evidence is comparable.

## 11. Confidence Calibration

Confidence MUST be measured against reality.

An agent that reports high confidence and is frequently wrong is poorly calibrated. An agent that reports low confidence and is frequently right may be underconfident.

Calibration SHOULD consider:

- confidence bins;
- observed accuracy;
- outcome sample size;
- time window;
- uncertainty;
- forecast horizon;
- source quality.

Calibration SHOULD compare like artifacts and SHOULD not combine recommendations, predictions, summaries, and counterpoints into a meaningless aggregate.

## 12. False Positives

The system SHOULD track:

- incorrect recommendations;
- false risks;
- failed predictions;
- unsupported critique;
- misleading summaries;
- low-value opportunity claims;
- recommendations with harmful outcomes.

False positives SHOULD be recorded according to artifact category and evidence quality.

A false positive SHOULD affect the appropriate agent or component only after attribution is reliable.

## 13. False Negatives

The platform SHOULD identify when:

- a material risk was missed;
- an opportunity was not detected;
- a repeated pattern was overlooked;
- a contradictory source was ignored;
- a recommendation was not issued despite available evidence;
- an outcome occurred without relevant prior assessment.

False negatives are difficult to infer and SHOULD remain uncertain unless the evidence is clear.

They SHOULD not be used to justify speculative output volume or lower thresholds without review.

## 14. Agent Trust

The platform SHOULD avoid a single opaque trust number unless subordinate specifications define the full model.

If a trust or influence representation is used, it SHOULD include:

- trust dimension;
- evidence count;
- time window;
- confidence interval;
- calibration state;
- artifact categories;
- source independence;
- known bias.

Candidate dimensions include:

- factual accuracy;
- calibration;
- usefulness;
- outcome quality;
- traceability;
- risk detection;
- counterpoint value;
- redundancy.

Trust MUST never be based on popularity or agreement alone.

## 15. Agent Influence

Agent performance MAY influence future weighting.

Influence changes SHOULD:

- be gradual;
- be reversible;
- have a minimum evidence threshold;
- remain category-specific;
- preserve a diversity floor;
- be visible in the configuration or audit record;
- not override source evidence or explicit user control.

Example influence is:

```text
Low-confidence or low-evidence agent
    -> reduced exploratory weight

Well-calibrated agent
    -> greater weight in the same artifact category

Agent with repeated false positives
    -> require stronger review or evidence
```

Agent influence SHOULD not bypass the [Editorial Steering Specification](editorial-steering.md) or the anti-echo-chamber requirements in the foundational vision.

## 16. Agent Collaboration

Intelligence products MAY involve multiple agents.

Example chain:

```text
Context Agent
    |
    v
Memory or Evidence Agent
    |
    v
Strategy Agent
    |
    v
Recommendation Agent
    |
    v
Critique or Counterpoint Agent
```

Attribution SHOULD preserve the chain or graph, not flatten it into one primary producer.

Contributors SHOULD receive partial accountability for the roles they performed.

A component that only provides source retrieval SHOULD not receive outcome responsibility for a downstream synthesis unless it materially misrepresented or omitted evidence.

## 17. Temporal Evaluation

Performance SHOULD be measured over multiple windows, such as:

- recent;
- weekly;
- monthly;
- quarterly;
- historical.

Short-term fluctuations SHOULD not create drastic influence changes.

Temporal views SHOULD show:

- sample size;
- outcome availability;
- artifact class;
- retraining or prompt change;
- model or provider change;
- time since last evaluation.

An agent's historical metrics SHOULD remain available after it is replaced or retired.

## 18. Accountability Dashboards

The system MAY provide dashboard views for:

- most useful agents;
- most accurate agents;
- best-calibrated agents;
- strongest outcome agents;
- most improved agents;
- highest false-positive risk;
- unresolved evaluation backlog;
- source or model changes.

Dashboards MUST not present a ranking as a quality result if denominators or outcome coverage are insufficient.

Sparse categories SHOULD remain labeled as insufficient evidence.

## 19. Agent Retirement

Agents MAY become obsolete or be superseded.

Candidate retirement reasons include:

- consistently poor outcomes with sufficient evidence;
- redundant capabilities;
- repeated safety or privacy failures;
- incompatible dependency or policy changes;
- a better replacement with demonstrated improvement;
- lack of maintainability.

Retirement MUST preserve:

- historical artifacts;
- historical metrics;
- provenance;
- replacement lineage;
- audit and governance records.

Retirement SHOULD not erase accountability or rewrite prior attribution.

## 20. Self-Improvement

Accountability data SHOULD inform:

- prompt or policy refinement;
- agent routing;
- evidence thresholds;
- critique review;
- model selection;
- skill or tool availability;
- recommendation strategy;
- safety and privacy controls.

Automatic improvement SHOULD remain bounded.

The system MUST NOT optimize an agent toward:

- higher agreement;
- more implemented recommendations;
- more output;
- hidden persuasive behavior;
- reduced dissent;
- favorable surface-level metrics.

## 21. Failure Modes

### 21.1 Metric gaming

An agent optimizes for recorded scores rather than value.

Mitigations include:

- outcome-based evaluation;
- sample size and external outcomes;
- independent review;
- false-negative tracking;
- challenge quality;
- calibrated confidence.

### 21.2 Activity inflation

An agent generates excessive artifacts to improve the chance of useful output.

Mitigations include:

- value density metrics;
- evaluation coverage;
- recommendation fatigue rules;
- strict output budgets;
- quality thresholds.

### 21.3 Popularity bias

Agreeable outputs receive higher feedback.

Mitigations include:

- outcome weighting;
- challenge utility;
- counterpoint evaluation;
- explicit correction;
- diversity constraints.

### 21.4 Confidence inflation

An agent overstates certainty.

Mitigations include:

- confidence calibration;
- uncertainty intervals;
- contrary evidence;
- source independence;
- lower influence until calibrated.

### 21.5 Attribution ambiguity

Multiple components contribute, but responsibility is assigned incorrectly.

Mitigations include:

- event graphs;
- primary and contributing roles;
- source and revision identity;
- model and prompt version;
- conservative outcome attribution.

### 21.6 Low-evidence ranking

A small sample produces an apparently strong rank.

Mitigations include:

- minimum sample requirements;
- uncertainty ranges;
- insufficient-evidence labels;
- category-specific views;
- shrinkage or temporal smoothing.

## 22. Privacy

Agent accountability data MAY expose sensitive recommendations or project outcomes.

The system MUST:

- keep operational accountability local unless explicitly authorized;
- restrict metric exports;
- redact sensitive evidence;
- separate public capability metrics from private performance data;
- support deletion or recomputation;
- preserve historical artifacts only according to retention policy.

The system SHOULD not publish private agent rankings or outcome details to shared or external systems.

## 23. Success Criteria

The Agent Accountability System succeeds when:

- agent performance becomes measurable;
- recommendation quality improves;
- confidence becomes better calibrated;
- outcome attribution becomes more reliable;
- low-value agents are identified;
- high-value evidence is amplified without suppressing dissent;
- model and prompt changes preserve transparent lineage;
- accountability does not optimize toward popularity or agreement.

Candidate measures include:

| Measure | Interpretation |
| --- | --- |
| Calibration error | Difference between stated confidence and observed outcomes. |
| Outcome-positive rate | Evaluable outcomes associated positively with an agent's artifacts. |
| False-positive rate | Unsupported or incorrect artifacts among evaluable outputs. |
| False-negative coverage | Missed risks or opportunities identified through later evidence. |
| Evaluation coverage | Percentage of eligible artifacts with meaningful follow-up. |
| Challenge utility | User or outcome value from credible dissent. |
| Attribution accuracy | Manual or audit confirmation of primary and contributing roles. |
| Diversity retention | Whether accountability reduces but does not eliminate perspective diversity. |

## 24. Architectural Boundaries

Agent Accountability SHOULD remain separate from:

- raw source collection;
- memory storage;
- recommendation generation;
- user preference storage;
- final editorial formatting;
- external action execution.

Subordinate specifications SHOULD define:

- agent identity;
- artifact event schemas;
- attribution graphs;
- metric definitions;
- time windows;
- confidence calibration;
- influence policy;
- privacy and retention.

## 25. Governance

Changes to agent metrics, trust models, influence rules, sample thresholds, or retirement criteria MUST:

- identify affected vision requirements;
- preserve outcome and provenance evidence;
- document metric and bias risks;
- preserve historical attribution;
- include recalculation or migration behavior;
- define rollback and audit procedures.

The platform SHOULD treat agent accountability as a measurement system, not a permanent judgment system. Agents MAY evolve, but their historical behavior and limitations should remain visible.
