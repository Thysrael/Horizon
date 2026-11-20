# Feedback Learning Specification

**Status:** Proposed

**Version:** 1.1

**Classification:** Core Intelligence Specification

**Last Updated:** November 20, 2026

**Constitutional parent:** [Daily Intelligence Brief Vision Specification](daily-intelligence-brief-vision.md)

---

## 1. Purpose

The Feedback Learning System transforms user reactions, behavior, outcomes, and preferences into durable, inspectable intelligence that improves future recommendations.

The system does not optimize for agreement, popularity, or engagement. It learns what creates value, improves decision quality, helps the user think better, and leads to favorable outcomes.

This specification defines the feedback signals, learning targets, recommendation lifecycle, preference model, decay behavior, safeguards, and success criteria used across the Daily Intelligence Platform.

## 2. Objectives

The system SHOULD continuously improve its understanding of:

- which topics and sources consistently create value;
- how information should be presented;
- which recommendations help with decisions;
- which agents or perspectives contribute useful insights;
- which decision outcomes validate or invalidate recommendations;
- where dissent, challenge, or unfamiliar topics prove useful.

The system MUST distinguish value, agreement, accuracy, novelty, and engagement. These measures MAY correlate, but they MUST NOT be treated as interchangeable.

## 3. Scope

The Feedback Learning System governs learning from editions and other intelligence objects produced by the platform.

It MAY collect feedback for:

- articles and stories;
- recommendations;
- critiques;
- counterpoints;
- topics;
- projects;
- source and evidence quality;
- memories;
- inference and reasoning steps;
- producing agents or model configurations.

It MUST NOT convert every interaction into a permanent preference. Raw events remain separate from learned preferences, and no learned preference is created without an applicable policy and evidence threshold.

## 4. Guiding Principles

### 4.1 Outcomes over agreement

A familiar or agreeable item MAY create little value. A contrary, uncomfortable, or unfamiliar item MAY create substantial value.

The learning system MUST prioritize observed outcomes and explicit judgments over agreement or engagement.

### 4.2 Weak behavioral signals

Behavioral observations are evidence of attention, not proof of quality or value.

Examples include opening an article, revisiting it, expanding a section, archiving it without reading, or spending time with it. These observations MUST be treated as weak signals.

Dwell time MUST NOT be used alone to label an item as helpful or harmful. High dwell time can indicate interest, confusion, frustration, or inaccessibility. Low dwell time can indicate efficient consumption, a poor match, or an interrupted session.

### 4.3 Explicit feedback precedence

When explicit feedback conflicts with inferred behavior, explicit feedback SHOULD have higher precedence.

Examples:

| Signal | Default precedence |
| --- | --- |
| Verified outcome | Highest |
| Explicit correctness or usefulness judgment | High |
| Direct topic or presentation preference | High |
| Repeated longitudinal behavior | Medium |
| Single behavioral interaction | Low |
| Dwell time or impression count | Lowest |

Precedence values are policy defaults. Subordinate specifications MUST document how a value becomes durable, how conflicting evidence is resolved, and how it may be reversed.

### 4.4 Inspectability and reversibility

The user MUST be able to understand and correct material learned preferences.

For each durable preference, the system SHOULD expose:

- the preference or conclusion;
- source feedback and supporting evidence;
- confidence;
- first observed and last updated times;
- decay status;
- contributing targets;
- actions that remove or reverse it.

Deleting a feedback event SHOULD invalidate or recalculate affected preferences where practical.

### 4.5 No engagement optimization

The platform MUST NOT optimize toward maximizing opens, dwell time, return visits, or consumption. Reading behavior is input to judgment quality, not the objective itself.

## 5. Learning Sources

### 5.1 Explicit feedback

The system SHOULD accept direct user judgments such as:

- Helpful;
- Not Helpful;
- More Like This;
- Less Like This;
- Implemented;
- Incorrect;
- Incomplete;
- Not Yet;
- Suppress Topic;
- Re-enable Topic.

Explicit feedback SHOULD include a stable target identifier and SHOULD support an optional correction or reason.

### 5.2 Behavioral feedback

The system MAY infer low-confidence signals from interactions such as:

- opening or revisiting an item;
- expanding or collapsing detail;
- copying or sharing an item;
- archiving or dismissing an item;
- saving an item for later;
- applying a user filter or suppression.

Dismissal MUST NOT automatically mean low quality. It MAY mean duplication, lack of timeliness, poor presentation, low current priority, or user preference.

### 5.3 Outcome feedback

Outcome feedback SHOULD include an observation linked to a recommendation or decision.

Examples include:

- a recommendation was implemented;
- a project milestone was completed;
- a predicted risk materialized or did not materialize;
- a decision was reversed;
- a source remained useful after a significant period;
- a recommendation created a measurable benefit or cost.

An outcome MUST remain evaluable over time. A recommendation should not be marked successful merely because it was viewed or implemented.

### 5.4 Longitudinal feedback

The system MAY derive medium-confidence patterns across repeated observations, for example:

- frequently revisited topics;
- consistently implemented recommendations;
- repeatedly ignored recommendations;
- preferences that remain stable across projects;
- recurring false assumptions.

Longitudinal conclusions SHOULD include sample size and time bounds.

## 6. Feedback Targets

Feedback MUST support multiple targets rather than attaching only to a whole article.

| Target | Example |
| --- | --- |
| Story or article | “This presentation was useful.” |
| Recommendation | “This action created value.” |
| Critique | “This identified a real blind spot.” |
| Counterpoint | “This credible alternative changed my assessment.” |
| Agent or model | “Recommendations from this source are frequently useful.” |
| Topic | “I want more semiconductor industry analysis.” |
| Project | “I need more strategic visibility into this project.” |
| Source | “This source consistently provides weak evidence.” |
| Memory | “This recalled context was stale or misleading.” |
| Inference | “This conclusion relied on a faulty assumption.” |

A feedback event SHOULD identify the type of target, target ID, edition or session context, and the feedback source.

## 7. Feedback Model

### 7.1 Feedback event

A feedback event SHOULD contain at least:

```json
{
  "event_id": "fdbk_...",
  "target_type": "recommendation",
  "target_id": "rec_...",
  "feedback_type": "helpful",
  "evidence": "implemented",
  "confidence": "high",
  "source": "explicit",
  "created_at": "2026-11-20T15:30:00Z",
  "context_id": "edition_...",
  "correction": null
}
```

Fields are conceptual. Subordinate storage specifications MUST define identifiers, timestamps, validation, encryption, and deletion behavior.

### 7.2 Feedback types

The platform MAY support:

| Feedback type | Learning meaning |
| --- | --- |
| Helpful | Created value or improved understanding. |
| Not Helpful | Failed to create value or understanding. |
| More Like This | Increase relevant similarity without creating an exact-topic filter. |
| Less Like This | Reduce similarity or frequency while preserving diversity. |
| Implemented | The user or an explicitly authorized system acted on the recommendation. |
| Incorrect | A factual or logical claim was wrong. |
| Incomplete | Missing evidence or context materially affected usefulness. |
| Outdated | The item was useful once but no longer reflects current context. |
| Not Yet | Defer evaluation until an outcome is observable. |
| Suppress | Temporarily reduce a target or pattern. |

The system MUST NOT treat “Not Helpful” as an instruction to eliminate every related perspective. Suppression is a bounded preference, not a blanket truth filter.

## 8. Feedback Collection

Every story or recommendation SHOULD expose a low-friction feedback mechanism within the edition.

Candidate controls include:

- Helpful;
- Not Helpful;
- More Like This;
- Less Like This;
- Implemented;
- Incorrect;
- Not Yet.

Each action SHOULD require at most one interaction for the initial judgment. Optional explanation, correction, or outcome recording SHOULD remain available without blocking the core action.

The interface SHOULD be able to preserve feedback context after an edition is archived or a recommendation changes status.

## 9. Recommendation Lifecycle

Recommendations are first-class learning objects.

```text
Drafted
  |
  v
Published
  |
  v
Viewed
  |
  v
Evaluated
  |
  +--> Deferred
  |
  v
Implemented
  |
  v
Outcome Observed
```

Lifecycle states SHOULD include:

- **Drafted:** generated but not yet considered complete;
- **Published:** presented to the user;
- **Viewed:** exposed through the edition or archive;
- **Evaluated:** the user has supplied an explicit judgment;
- **Deferred:** outcome is not yet measurable;
- **Implemented:** action was taken;
- **Outcome Observed:** an outcome was recorded;
- **Closed:** no further outcome evaluation is expected;
- **Superseded:** a later recommendation invalidates or replaces the prior recommendation.

Publication alone MUST NOT imply implementation or success.

## 10. Outcome Tracking

For each durable recommendation, the platform SHOULD preserve:

- recommendation ID;
- creation and publication timestamps;
- confidence and importance;
- producing agents or models;
- supporting context and evidence;
- current lifecycle state;
- explicit feedback;
- observed outcome;
- outcome confidence;
- supersession or invalidation records.

An outcome SHOULD be recorded as structured evidence rather than free text alone. Text observations MAY supplement structured fields.

Outcome attribution MUST be conservative. The system MUST NOT claim that an outcome resulted from a recommendation when the relationship is unobserved or causal evidence is weak.

## 11. Agent Accountability

The platform SHOULD preserve generating agent or model information on every meaningful recommendation or critique.

Agents MAY accumulate the following statistics:

- evaluated recommendation count;
- acceptance rate;
- implementation rate;
- corrected fact or logic count;
- positive and negative outcome counts;
- explicit usefulness score;
- dissent usefulness score;
- data quality issues.

Agent metrics MUST use time windows and sample sizes. Raw acceptance percentage MUST NOT be interpreted as quality when the sample is small or outcomes are sparse.

Future agent selection MAY use these metrics, but metrics MUST remain advisory and MUST NOT create an undisclosed quality or perspective monopoly.

## 12. Preference Profile

The preference profile represents accumulated, user-owned understanding of valuable topics, presentation, projects, recommendations, and sources.

It SHOULD contain:

- topic preferences;
- project preferences;
- presentation preferences;
- recommendation preferences;
- source preferences;
- confidence and evidence metadata;
- creation and update timestamps;
- decay parameters;
- exploration controls.

The profile is a learned model, not a permanent statement of identity or a hidden score assigned to the user.

The system SHOULD keep preferences separate from:

- immutable personal data;
- raw feedback events;
- observed activity;
- agent metrics;
- outcome records.

This separation allows deletion, correction, export, and recomputation without erasing unrelated history.

## 13. Preference Decay

Durable preferences MUST decay over time.

Decay exists because interests change, projects end, priorities shift, evidence changes, and older behavior becomes less predictive.

The system SHOULD use recent evidence as a stronger signal than older evidence and SHOULD reduce confidence rather than immediately deleting a preference.

Decay SHOULD consider:

- evidence age;
- evidence strength;
- continued relevance;
- project status;
- contradictory feedback;
- intervening outcomes;
- an explicitly chosen retention or decay policy.

The system SHOULD disclose when a preference was learned from old or sparse evidence.

## 14. Anti-Echo-Chamber Safeguards

Feedback learning MUST preserve intellectual diversity.

The system MUST NOT learn from feedback as:

- “show only agreement”;
- “hide every contrary view”;
- “exclude unfamiliar domains permanently.”

The learning system SHOULD:

- maintain a bounded exploration allocation;
- continue surfacing credible counterpoints;
- distinguish an unwanted topic from an unwanted viewpoint;
- preserve deliberate challenge in the presence of strong explicit agreement;
- retry exploration cautiously rather than expanding indefinitely after repeated dismissal.

### 14.1 Proposed exploration budget

An initial editorial budget MAY be:

- 70 percent highly relevant coverage;
- 20 percent adjacent interests;
- 10 percent challenge or novelty.

The percentages MUST be configurable and SHOULD be reviewed empirically. The principle is fixed: personalization SHALL not eliminate challenge and discovery.

This budget SHOULD apply to edition selection, not to factual or source coverage that is necessary to understand an active project or risk.

## 15. Privacy and Control

Feedback data MAY reveal sensitive topics, beliefs, health, finances, employment, or relationships.

The platform MUST:

- keep learning data local unless cloud processing is explicitly enabled;
- disclose what feedback leaves the local environment;
- require separate authorization for external model fine-tuning or external personalization;
- support export and deletion of feedback events and learned preferences;
- support recomputation or invalidation after preference deletion;
- prevent unrelated personal context from entering shared or public outputs.

The platform SHOULD separate:

- feedback export;
- context export;
- generated content export;
- model provider telemetry.

Deleting a recommendation from the interface SHOULD NOT be the only way to remove associated learned data.

## 16. Learning Boundaries

The system SHOULD NOT:

- infer sensitive traits or protected characteristics;
- infer mental health or vulnerability states;
- optimize for persuasion;
- convert silence or confusion into a strongly negative judgment;
- expose agent metrics in a way that rewards homogeneous reasoning;
- replace human judgment with a learned score;
- execute a recommendation solely because its historical confidence is high.

Agent diversity, contrary evidence, and source quality SHOULD remain dimensions of the editorial and reasoning process rather than hidden optimization targets.

## 17. Success Criteria

The Feedback Learning System succeeds when:

- recommendation quality improves over representative time periods;
- user trust increases without increasing blanket agreement;
- implemented recommendations correlate with positive outcomes at a meaningful confidence level;
- useful dissenting perspectives continue to appear;
- intellectual diversity is preserved;
- personalization can be inspected, corrected, and reversed;
- learning is not based primarily on engagement duration or exposure.

Success measurements MUST include uncertainty and MUST distinguish correlation from causation.

Candidate measurements include:

| Measure | Interpretation |
| --- | --- |
| Positive outcome rate | Outcomes classified as beneficial among recommendations with sufficient follow-up. |
| Corrective feedback rate | Frequency of incorrect, incomplete, stale, or superseded recommendations. |
| Implementation follow-through | Implemented recommendations that remain evaluable and receive an outcome. |
| Exploration utility | User value from adjacent or challenging items. |
| Diversity retention | Whether coverage remains beyond the user's strongest current preferences. |
| Preference stability | Whether durable preferences change only with substantial, explainable evidence. |

These measures are hypotheses until baseline rates and confidence intervals are established.

## 18. Architectural Responsibilities

Feedback is a cross-cutting intelligence capability. It SHOULD integrate through explicit interfaces with:

- the newspaper presentation layer;
- recommendation and critique generation;
- memory and knowledge storage;
- agent execution records;
- outcome tracking;
- privacy and export controls;
- evaluation and reporting.

Subordinate specifications SHOULD define event schemas, storage, retention, aggregation, model-provider boundaries, and calibration behavior.

## 19. Governance

Changes to learning weights, exploration budgets, retention, or outcome definitions MUST:

- identify the affected vision requirements;
- describe rationale and empirical evidence;
- preserve or explicitly revise anti-echo-chamber behavior;
- preserve user control and traceability;
- include a migration or recalculation strategy for existing preferences.

The system MAY evolve individual models and interfaces. The principles in this specification remain stable unless amended through the same governance process used for the foundational vision specification.
