# Work Context Brief Specification

**Status:** Proposed

**Version:** 1.1

**Classification:** Core Intelligence Specification

**Last Updated:** November 20, 2026

**Constitutional parent:** [Daily Intelligence Brief Vision Specification](daily-intelligence-brief-vision.md)

**Related specifications:**

- [Context Collection Specification](context-collection.md)
- [Editorial Steering Specification](editorial-steering.md)
- [Recommendation Engine Specification](recommendation-engine.md)

---

## 1. Purpose

The Work Context Brief is the primary compact operational snapshot consumed by downstream intelligence systems.

It represents what is currently active, what is changing, what decisions are unresolved, and what context may influence a relevant brief or recommendation.

The Work Context Brief is not:

- a memory system;
- a conversation archive;
- a project database;
- a complete record of activity;
- a hidden user profile.

It is a bounded, versioned, reviewable snapshot derived from collected context and historical intelligence.

## 2. Mission

The Work Context Brief SHOULD answer:

“What does a downstream system need to know about the user's current work world?”

It SHOULD surface:

- active projects;
- meaningful recent decisions;
- open questions;
- blockers;
- technologies receiving sustained attention;
- strategic themes;
- current interests;
- stable presentation preferences;
- uncertainty and source gaps.

The brief SHOULD improve downstream reasoning without requiring systems to reprocess raw activity.

## 3. Design Principles

### 3.1 Compactness

The brief SHOULD prioritize information density.

Every field SHOULD justify its use by supporting:

- relevance;
- editorial framing;
- recommendation generation;
- risk detection;
- project continuity;
- historical comparison.

The brief SHOULD avoid activity transcripts and low-value operational detail.

### 3.2 Signal over volume

A small number of high-signal project insights SHOULD be preferred to many conversational fragments.

The brief SHOULD preserve meaning and decision relevance rather than completeness.

### 3.3 Current awareness

The brief SHOULD primarily represent current operational context.

Historical material SHOULD appear only if it remains:

- operationally relevant;
- necessary for comparison;
- necessary to explain a recurring risk or project state;
- requested for strategic review.

### 3.4 Model agnostic

The Work Context Brief SHOULD be consumable by any authorized reasoning system.

It SHOULD not require a provider-specific format, model, or memory implementation.

### 3.5 Portable and versioned

The brief SHOULD be:

- human readable;
- machine readable;
- versionable;
- transportable within authorized environments;
- reconstructable with supporting evidence.

### 3.6 Explainable

The brief SHOULD distinguish:

- directly observed context;
- inferred project context;
- summarized context;
- historical context;
- preferences;
- uncertainty.

It SHOULD preserve enough provenance to permit correction and deletion.

## 4. Architectural Position

The Work Context Brief sits between collection and intelligence systems:

```text
Activity Sources
        |
        v
Activity Records
        |
        v
Context Summaries
        |
        v
Work Context Brief
        |
        v
Editorial Steering
        |
        v
Recommendation and Editorial Systems
        |
        v
Daily Intelligence Brief
```

The brief is the primary operational handoff artifact. Downstream systems SHOULD be able to consume it without access to raw source histories.

## 5. Inputs

The Work Context Brief SHOULD be generated from:

- normalized Activity Records;
- project metadata;
- open and closed decisions;
- active blockers;
- preference summaries;
- recommendation history;
- feedback state;
- historical intelligence that remains operationally relevant;
- source coverage and collection health.

The Work Context Brief SHOULD not consume unrelated raw source data merely because it is available.

## 6. Canonical Schema

A Work Context Brief SHOULD support at least:

```json
{
  "brief_id": "wcb_2026-11-20_090000",
  "generated_at": "2026-11-20T09:00:00Z",
  "valid_from": "2026-11-20T09:00:00Z",
  "valid_until": "2026-11-21T09:00:00Z",
  "window": {
    "start": "2026-11-18T09:00:00Z",
    "end": "2026-11-20T09:00:00Z"
  },
  "active_projects": [],
  "recent_decisions": [],
  "open_questions": [],
  "current_blockers": [],
  "technologies": [],
  "strategic_themes": [],
  "presentation_preferences": [],
  "interest_signals": [],
  "sparse_sources": [],
  "confidence": 0.86,
  "sensitivity": "local_only",
  "provenance": []
}
```

Future fields MAY be added. Existing fields SHOULD retain stable meaning or receive an explicit version transition.

Subordinate specifications MUST define:

- field types;
- confidence semantics;
- sensitivity inheritance;
- provenance schema;
- versioning;
- validity and expiration;
- serialization.

## 7. Active Projects

Active projects are the most important portion of the brief.

Each project SHOULD include:

- project ID;
- name or stable label;
- status;
- momentum;
- confidence;
- last active timestamp;
- recent decisions;
- open questions;
- blockers;
- associated technologies;
- evidence references;
- inferred or pinned origin;
- staleness state.

An example shape is:

```json
{
  "project_id": "project_spec_stewardship",
  "name": "Specification Stewardship",
  "status": "active",
  "momentum": "high",
  "confidence": 0.91,
  "last_active_at": "2026-11-20T08:45:00Z",
  "recent_decisions": [],
  "open_questions": [],
  "blockers": []
}
```

Projects SHOULD be ranked by a combination of:

- current relevance;
- evidence confidence;
- momentum;
- priority;
- explicit project state;
- material open decisions or blockers.

Activity volume alone MUST NOT determine project importance.

## 8. Momentum

Project momentum SHOULD describe observed activity rather than importance.

Candidate classifications include:

- high;
- medium;
- low;
- dormant;
- unknown.

Momentum SHOULD be derived from:

- recent meaningful activity;
- decision or deliverable changes;
- source coverage;
- active blockers;
- explicit project milestones.

It SHOULD NOT be inferred from chat message count or source activity volume alone.

## 9. Recent Decisions

The brief SHOULD identify meaningful decisions rather than every minor choice.

Candidate decisions include:

- architectural choices;
- strategic tradeoffs;
- project direction changes;
- explicit rejection or prioritization;
- revised assumptions;
- superseded plans.

A decision SHOULD include:

- decision summary;
- project or theme;
- decision status;
- timestamp;
- confidence;
- supporting evidence;
- unresolved consequences.

The brief SHOULD avoid recording speculative discussion as a decision.

## 10. Open Questions

Open questions are unresolved issues that may require thought, research, action, or further evidence.

Candidate fields include:

- question text;
- project or strategic theme;
- importance;
- urgency;
- confidence;
- source evidence;
- unresolved since;
- related blockers;
- possible follow-up types.

Open questions SHOULD receive elevated steering consideration, but SHOULD NOT be presented as facts or decisions.

## 11. Current Blockers

The brief SHOULD identify meaningful friction.

Examples include:

- repository ambiguity;
- missing specifications;
- conflicting architecture decisions;
- unresolved technical dependencies;
- missing evidence;
- waiting on an external outcome;
- prohibited or unavailable source access.

Each blocker SHOULD identify:

- affected project or theme;
- confidence;
- severity;
- age;
- evidence;
- recommended next step category;
- resolution state.

Transient conversation friction SHOULD NOT become a project blocker without evidence.

## 12. Technologies

The brief SHOULD identify technologies or domains receiving sustained attention.

Each technology signal SHOULD include:

- name or stable identifier;
- associated project or theme;
- evidence;
- confidence;
- first and latest observation;
- momentum or staleness;
- current or historical status.

Technology names SHOULD remain topical steering signals, not assumptions about user preference or proficiency.

## 13. Strategic Themes

Strategic themes represent ideas that span projects or persist across time.

Examples include:

- memory governance;
- specification stewardship;
- agent accountability;
- knowledge management;
- decision quality;
- repository health.

Themes SHOULD emerge from repeated, meaningful evidence and SHOULD include:

- theme identity;
- supporting projects or activities;
- confidence;
- first and latest observation;
- current relevance;
- potentially related historical patterns.

## 14. Presentation Preferences

Presentation preferences describe stable, explicitly learned or confirmed preferences that affect editorial style.

Examples include:

- concise or detailed content;
- structured reasoning;
- constructive challenge;
- technical depth;
- use of tables or timelines.

The system SHOULD NOT infer personality traits or protected characteristics.

Presentation preferences SHOULD:

- remain separate from topic interests;
- carry confidence and provenance;
- be inspectable and reversible;
- decay or be changed by contradictory feedback.

User-visible preferences SHOULD not be used to soften, hide, or distort material evidence.

## 15. Interest Signals

Interest signals represent current curiosity or sustained professional interest.

Examples include:

- memory architecture;
- agent systems;
- knowledge graphs;
- recommendation systems;
- decision intelligence.

Each interest SHOULD include:

- topic or stable identifier;
- confidence;
- evidence;
- first and latest observation;
- recency;
- explicit or inferred origin;
- exploration budget status.

Interest signals SHOULD have higher turnover than presentation preferences and SHOULD not become permanent identities.

## 16. Confidence

The brief SHOULD expose a bounded overall confidence and SHOULD also preserve field-level confidence where practical.

Overall confidence SHOULD reflect:

- signal quantity;
- source agreement;
- source independence;
- project certainty;
- recency;
- contradictory evidence;
- collection completeness.

Overall confidence SHOULD decrease when sources are missing, stale, or contradictory.

A precise overall score SHOULD NOT imply that weakly supported fields have precise confidence.

Subordinate specifications SHOULD prefer:

- bounded numeric values;
- qualitative confidence labels;
- uncertainty intervals;
- or a combination of these.

No fixed score is considered normative in this specification.

## 17. Token and Size Budget

The brief SHOULD be compact enough for normal model consumption and downstream ranking.

A target SHOULD be 300 to 500 content units and a maximum SHOULD be established per implementation, while allowing a review mode or expansion mode to exceed the default target.

Exceeding the normal budget SHOULD require:

- a declared context mode;
- explicit prioritization;
- removal of low-confidence or low-relevance fields;
- a reason for the expanded content.

Token count alone SHOULD not be the only compactness constraint. Information density and relevance SHOULD be measured.

## 18. Snapshot Persistence

Work Context Briefs are snapshots, not mutable memory.

Each generated brief SHOULD preserve:

- brief ID;
- generation time;
- valid time window;
- source collection versions;
- project and preference versions;
- context confidence;
- snapshot hash;
- sensitivity;
- generation provenance.

The platform SHOULD archive or retain snapshots according to policy. It SHOULD support:

- comparison between snapshots;
- supersession;
- correction;
- deletion;
- export.

A downstream correction SHOULD create a new snapshot or correction record. It SHOULD NOT silently rewrite historical snapshots.

## 19. Context Drift

Comparisons between Work Context Briefs SHOULD support:

- emerging projects;
- fading interests;
- strategic shifts;
- new or resolved blockers;
- changed decisions;
- project completion or inactivity;
- confidence changes;
- contradictory evidence.

Drift detection SHOULD distinguish:

- a real change;
- a source coverage gap;
- a stale inference;
- a manually corrected project;
- a temporary fluctuation.

Drift conclusions SHOULD include evidence and time bounds.

## 20. Generation Process

Brief generation SHOULD include:

1. validate collection state;
2. select relevant records;
3. classify missing and stale sources;
4. aggregate project and decision evidence;
5. merge historical context where operationally relevant;
6. apply preference and presentation context;
7. calculate field-level and overall confidence;
8. redact or block sensitive fields;
9. rank fields within the budget;
10. create a versioned snapshot;
11. preserve generation provenance.

The process SHOULD fail closed when required context cannot be safely summarized.

## 21. Failure Modes

The system SHOULD mitigate:

### 21.1 Empty context

No significant recent activity is detected.

The system SHOULD:

- fall back to preference and historical context;
- mark context as sparse;
- reduce project confidence;
- avoid inventing active work.

### 21.2 Excessive context

Too many projects or themes compete for the brief.

The system SHOULD:

- prioritize current verified work;
- merge or de-emphasize weak projects;
- retain low-confidence context as discovery only;
- surface excess context count when useful.

### 21.3 Project fragmentation

Related activity appears as multiple projects.

The system SHOULD:

- cluster related evidence;
- preserve merge suggestions;
- avoid deleting source associations;
- permit manual merge or split.

### 21.4 Stale dominance

Historical information overwhelms current context.

The system SHOULD:

- strengthen recency weighting;
- label historical fields;
- reduce stale project confidence;
- archive inactive projects.

### 21.5 Source incompleteness

One or more authorized sources could not collect.

The system SHOULD:

- mark source coverage;
- reduce affected confidence;
- avoid implying complete context;
- continue with available evidence.

### 21.6 Contradictory context

Sources disagree on project state or a recent decision.

The system SHOULD:

- preserve both interpretations;
- identify the contradiction;
- lower confidence;
- avoid choosing one arbitrarily.

## 22. Privacy and Sensitivity

The brief MAY contain sensitive work, financial, health, relationship, or employment context.

The system MUST:

- keep core brief generation local unless explicitly authorized;
- apply source and field sensitivity;
- disclose external provider usage;
- support export and deletion;
- prevent restricted fields from entering public or shared outputs;
- preserve redaction provenance.

The user SHOULD be able to:

- inspect or hide active projects;
- correct project and theme labels;
- remove interest or presentation signals;
- set brief sensitivity;
- delete historical snapshots;
- disable inferred context.

Deleting a source or project SHOULD trigger the applicable treatment of existing derived fields. Historical snapshots MAY be deleted rather than silently rewritten.

## 23. Observability

Brief generation SHOULD record or expose:

- projects identified;
- active and stale project count;
- open questions and blockers;
- selected content size;
- generation time;
- field-level confidence;
- overall confidence;
- source coverage;
- missing or stale sources;
- excluded content count;
- redaction events;
- drift signals;
- generation model or engine where permitted.

Logs SHOULD not expose sensitive project or source content in public interfaces.

## 24. Success Criteria

The Work Context Brief succeeds when:

- it accurately represents verified current work;
- it remains compact;
- it improves relevance and recommendation quality;
- downstream systems can consume it without raw source archives;
- stale and missing context are visible;
- inferred projects can be corrected;
- it remains model agnostic;
- it requires minimal manual maintenance.

Candidate measurements include:

- project correction rate;
- stale project reference rate;
- recommendation relevance attributable to context;
- source coverage completeness;
- contradiction and blocker accuracy;
- brief usefulness rating;
- average field confidence calibration;
- downstream token and latency cost.

## 25. Architectural Boundaries

The Work Context Brief SHOULD remain separate from:

- raw Activity Records;
- conversation and document archives;
- memory consolidation;
- preference learning;
- recommendation lifecycle;
- feedback storage;
- final briefing formatting.

Subordinate specifications SHOULD define:

- the canonical schema;
- project and decision records;
- confidence and sensitivity rules;
- snapshot retention;
- drift algorithms;
- generation budgets;
- provenance and correction.

## 26. Governance

Changes to brief fields, size budgets, project scoring, confidence, or snapshot semantics MUST:

- identify affected vision requirements;
- document downstream compatibility;
- preserve traceability and sensitivity;
- define migration and schema version behavior;
- include manual correction support;
- preserve historical snapshots or explicit deletion behavior.

The brief is a replaceable operational snapshot. Its role as the compact, versioned handoff between collection and downstream intelligence SHOULD remain stable.
