# Archive and Longitudinal Intelligence Specification

**Status:** Proposed

**Version:** 1.1

**Classification:** Core Intelligence Specification

**Last Updated:** November 20, 2026

**Constitutional parent:** [Daily Intelligence Brief Vision Specification](daily-intelligence-brief-vision.md)

**Related specifications:**

- [Work Context Brief Specification](work-context-brief.md)
- [Recommendation Engine Specification](recommendation-engine.md)
- [Agent Accountability Specification](agent-accountability.md)
- [Daily Intelligence Delivery Platform Specification](daily-intelligence-delivery-platform.md)

---

## 1. Purpose

The Archive and Longitudinal Intelligence System preserves, organizes, analyzes, and learns from intelligence over time.

It is not merely a storage system.

Its purpose is accumulated understanding: identifying patterns, change, drift, repeated risks, recurring opportunities, assumption changes, and outcome evidence that are invisible within a single edition.

The platform should become progressively more useful as history grows, while remaining correct, private, searchable, and reversible.

## 2. Mission

The system SHOULD transform historical records into longitudinal intelligence that answers:

- what patterns are recurring;
- what recommendations repeatedly appear;
- which risks are increasing;
- which projects are stalling;
- which assumptions have changed;
- what creates value over time;
- what decisions, recommendations, or opportunities have been forgotten.

One briefing may be informative. A maintained archive of comparisons, outcomes, and evolving context can support more durable judgment.

## 3. Design Principles

### 3.1 Durable value

Information is temporary, but some patterns are durable.

The archive SHOULD preserve artifacts that support:

- future decisions;
- historical reasoning;
- recommendation evaluation;
- outcome tracking;
- project continuity;
- drift detection;
- audit and correction.

The archive SHOULD distinguish evidence from an interpretation of that evidence.

### 3.2 Insight over storage

The archive SHOULD support analysis and comparison, not only retrieval.

The system SHOULD prefer derived summaries and navigable relationships over accumulating undifferentiated records.

### 3.3 Historical context

Current recommendations SHOULD be informed by relevant past observations.

Historical context SHOULD remain clearly dated and SHOULD not become an implicit present fact.

### 3.4 Accumulation with governance

The platform MAY become more useful with age.

It MUST remain subject to:

- privacy and deletion;
- retention;
- source revocation;
- sensitivity;
- correction;
- user export;
- legal or security requirements.

No historical benefit overrides the user's right to control or delete data.

### 3.5 Long-term horizons

The archive SHOULD support:

- daily review;
- weekly trends;
- monthly movement;
- quarterly strategy;
- annual transformation;
- cross-year comparisons.

## 4. Architectural Scope

The archive SHOULD preserve and link:

- delivered editions;
- Work Context Brief snapshots;
- recommendations and revisions;
- critiques and counterpoints;
- insights and historical observations;
- project and theme records;
- decision records;
- assumptions and contradictions;
- feedback events;
- outcome records;
- agent evaluations;
- source collection summaries;
- retention and correction events.

The archive SHOULD not ingest or duplicate raw source transcripts solely because the canonical artifact already carries sufficient evidence and provenance.

## 5. Archive Artifact Types

### 5.1 Immutable publication artifacts

Immutable publication artifacts include:

- delivered daily editions;
- finalized weekly, monthly, quarterly, or annual reviews;
- source-facing edition snapshots;
- signed or hashed publication records where applicable.

An immutable artifact SHOULD remain reproducible even if its source data later becomes unavailable or changes sensitivity.

### 5.2 Durable intelligence artifacts

Durable artifacts include:

- recommendations;
- critiques;
- insights;
- decisions;
- assumptions;
- project narratives;
- theme records;
- outcome records;
- agent evaluations.

Durable artifacts SHOULD remain revisable but SHOULD preserve historical revisions.

### 5.3 Derived summaries

Derived summaries include:

- weekly reviews;
- monthly trend summaries;
- quarterly strategic summaries;
- annual narratives;
- theme summaries;
- project evolution summaries.

Derived summaries SHOULD identify:

- source artifact range;
- generation time;
- model or system version;
- confidence;
- contradictions;
- superseding summaries.

### 5.4 Ephemeral operational data

Operational logs, temporary collection status, failed exports, and intermediate model outputs SHOULD remain separate from durable archive artifacts.

Ephemeral data SHOULD follow shorter retention and MAY be deleted without changing historical intelligence.

## 6. Intelligence Timeline

The platform SHOULD maintain an evolving timeline:

```text
Activity
    |
    v
Context
    |
    v
Recommendation or Insight
    |
    v
Publication
    |
    v
Evaluation
    |
    v
Implementation
    |
    v
Outcome
    |
    v
Retrospective Pattern or Assumption Change
```

No artifact SHOULD exist in isolation when relevant relationships can be preserved.

## 7. Review Hierarchy

The archive SHOULD support hierarchical reviews:

```text
Daily
    |
    v
Weekly
    |
    v
Monthly
    |
    v
Quarterly
    |
    v
Annual
```

Higher-level review SHOULD derive from lower-level artifacts, but SHOULD not silently merge contradictory evidence.

Each review SHOULD identify:

- source periods;
- active and resolved projects;
- recurring risks;
- repeated recommendations;
- material outcomes;
- new, faded, or changed themes;
- strategic drift;
- confidence and unresolved uncertainty.

## 8. Daily Intelligence

Daily editions SHOULD capture immediate awareness:

- what changed;
- what matters now;
- what decision or risk emerged;
- what remains unresolved;
- what information challenges current context.

Daily editions SHOULD remain retrievable and SHOULD link to supporting evidence.

## 9. Weekly Intelligence

Weekly reviews SHOULD identify short-term patterns:

- repeated recommendations;
- active and dormant projects;
- emerging blockers;
- new opportunities;
- changes in priorities;
- recommendations implemented or ignored;
- weekly outcome evidence.

## 10. Monthly Intelligence

Monthly reviews SHOULD focus on strategic movement:

- project evolution;
- technology and theme trends;
- learning progress;
- recommendation outcomes;
- unresolved assumptions;
- recurring blind spots.

## 11. Quarterly Intelligence

Quarterly reviews SHOULD provide a broader strategic perspective:

- major shifts;
- long-term risks;
- persistent challenges;
- major opportunities;
- project transition;
- changed priorities;
- agent or source performance.

## 12. Annual Intelligence

Annual reviews SHOULD focus on transformation:

- growth and capability changes;
- strategic progress;
- recurring weaknesses;
- major decisions;
- changed interests;
- long-lived recommendations;
- cross-year patterns.

The annual review SHOULD not rewrite earlier evidence. It SHOULD provide a dated synthesis.

## 13. Recommendation History

The archive SHOULD preserve each recommendation with:

- first appearance;
- latest appearance;
- revisions;
- associated projects;
- associated agents;
- evaluation status;
- implementation status;
- outcome;
- supersession;
- lineage.

Recommendation history SHOULD support the [Recommendation Engine Specification](recommendation-engine.md).

## 14. Recommendation Evolution

Recommendations MAY evolve through stages.

Example:

```text
Improve memory architecture
        |
        v
Define episodic and durable memory rules
        |
        v
Add governance and deletion controls
        |
        v
Implement memory hygiene
```

The archive SHOULD preserve parent, child, merge, split, and supersession relationships.

It SHOULD distinguish a revised recommendation from a separate historical recommendation.

## 15. Pattern Detection

The archive SHOULD support detection of:

### 15.1 Repeated risks

Examples include recurring technical debt, governance gaps, security risks, or knowledge fragmentation.

### 15.2 Repeated opportunities

Examples include automation opportunities, reusable architectures, emerging technologies, or process improvements.

### 15.3 Repeated recommendations

Repeated recommendations MAY indicate an unresolved issue, an ignored opportunity, strategic misalignment, or recurring user preference.

Repetition alone SHOULD not be treated as proof.

### 15.4 Repeated false positives

The archive SHOULD detect patterns of unsupported risks or recommendations.

### 15.5 Repeated false negatives

The archive SHOULD identify later outcomes that appear to have been missed, with uncertainty and evidence.

## 16. Pattern Confidence

Every longitudinal pattern SHOULD include:

- pattern definition;
- sample size;
- time range;
- source coverage;
- evidence strength;
- confidence;
- contradicting examples;
- alternative explanations;
- source and generation versions.

The system SHOULD label a pattern as:

- emerging;
- repeated;
- established;
- fading;
- contradicted;
- unresolved;
- insufficient evidence.

The system SHOULD not present correlation as causation or repetition as truth.

## 17. Strategic Drift

The platform SHOULD compare stated goals, project decisions, actual outcomes, and future direction.

Example:

```text
Goal:
Reduce specification complexity.

Observed:
Specification count and cross-reference density continue increasing.

Status:
Potential strategic drift.
```

Drift detections SHOULD include:

- baseline;
- stated or inferred goal;
- observed change;
- time period;
- confidence;
- alternate explanations;
- evidence gaps.

An inferred goal MUST be labeled as inferred and SHOULD remain reversible.

## 18. Project Evolution

Projects SHOULD retain longitudinal histories.

Candidate states include:

- created;
- growing;
- stable;
- declining;
- dormant;
- completed;
- archived;
- superseded.

The archive SHOULD preserve narratives:

- initial purpose;
- major decisions;
- blockers;
- milestones;
- reversals;
- outcome;
- learned lessons.

A project status should not erase earlier project context.

## 19. Theme Analysis

Themes SHOULD emerge from repeated, meaningful evidence rather than token matching alone.

Examples include:

- knowledge management;
- recommendation quality;
- governance;
- memory architecture;
- agent orchestration;
- repository health.

Themes SHOULD support:

- topic growth or decline;
- cross-project relationships;
- historical comparisons;
- user correction;
- merge and split.

## 20. Forgotten or Dormant Intelligence

The system MAY identify:

- recommendations no longer discussed;
- projects abandoned unintentionally;
- opportunities not revisited;
- decisions awaiting outcome;
- assumptions that are no longer challenged;
- high-value evidence that disappeared from active focus.

Such items SHOULD remain labeled as dormant or forgotten only after a meaningful confidence threshold.

A forgotten item SHOULD not be resurfaced merely for engagement.

It SHOULD include a reason for reconsideration and current evidence.

## 21. Outcome and Decision History

The archive SHOULD preserve:

- recommendation;
- implementation;
- outcome;
- confidence;
- source observation;
- decision context;
- later correction;
- supersession.

Major decisions SHOULD become historical artifacts.

Examples include:

- architectural decisions;
- governance decisions;
- strategic changes;
- technology choices;
- explicit assumption changes.

Future recommendations SHOULD understand decision history, but SHOULD not treat it as permanently fixed.

## 22. Assumption Tracking

The platform SHOULD support an assumption registry.

An assumption SHOULD contain:

- claim;
- scope;
- project or theme;
- evidence;
- confidence;
- created and changed timestamps;
- counterevidence;
- outcome;
- superseding assumption.

Example:

```text
Assumption:
Large memory systems improve intelligence.

Counterevidence:
Retrieval effectiveness can decrease with irrelevant or stale memory.

Status:
Reconsideration required.
```

Assumptions SHOULD be revisitable and SHOULD never become silently authoritative.

## 23. Search and Navigation

Users SHOULD be able to search or navigate by:

- date;
- project;
- theme;
- technology;
- recommendation;
- agent or model;
- outcome;
- risk;
- opportunity;
- confidence;
- source;
- assumption;
- decision;
- supersession state.

Search results SHOULD identify whether they contain:

- source evidence;
- an edition;
- a recommendation;
- a derived summary;
- feedback;
- an outcome;
- an assumption;
- a historical interpretation.

Search SHOULD make contradictions and revisions visible.

## 24. Cross-Artifact Relationships

The archive SHOULD preserve relationships such as:

- edition contains article;
- article links to evidence;
- recommendation derives from insight;
- recommendation has lineage;
- implementation has outcome;
- outcome validates or invalidates assumption;
- project contains decisions;
- theme spans projects;
- agent produces artifacts;
- feedback evaluates target;
- summary derives from source period.

Relationships SHOULD be typed and versioned.

The absence of a relationship SHOULD be distinguishable from an unknown relationship.

## 25. Retention and Deletion

The archive SHOULD support user-controlled retention.

Examples include:

- edition retention;
- recommendation retention;
- outcome retention;
- raw-source retention;
- derived-summary retention;
- agent metric retention;
- deletion on source revocation;
- account or local-data deletion.

The system SHOULD NOT default to permanent retention for all raw or sensitive data.

The archive MAY retain selected durable intelligence if it is permitted and does not violate deletion or privacy requirements.

For every deletion, the system SHOULD define:

- deleted data;
- retained derived data;
- broken or removed relationships;
- replacement or correction behavior;
- export before deletion;
- audit event.

A privacy deletion SHOULD invalidate or remove derived artifacts that would preserve prohibited personal context, not merely hide them.

## 26. Export and Portability

The archive SHOULD support export of:

- editions;
- recommendations;
- decisions;
- outcomes;
- feedback;
- project and theme histories;
- Work Context Brief snapshots;
- provenance and relationships.

Export SHOULD preserve:

- timestamps;
- revision state;
- sensitivity classification;
- source identity;
- relationship data;
- schema version.

Export SHOULD not include private or restricted artifacts unless the user explicitly selects them.

## 27. Failure Modes

### 27.1 Historical bloat

The archive contains too much low-value detail.

Mitigations include:

- derived summaries;
- retention tiers;
- artifact deduplication;
- project and theme aggregation;
- explicit source minimization.

### 27.2 Context loss

Relationships disappear as artifacts age.

Mitigations include:

- lineage records;
- typed relationships;
- persistent identifiers;
- migration validation;
- relationship export.

### 27.3 Recent-event distortion

Recent events dominate historical interpretation.

Mitigations include:

- multi-horizon analysis;
- time-weighted comparisons;
- historical baselines;
- uncertainty labels;
- explicit source coverage.

### 27.4 Archive fragmentation

Related intelligence remains isolated.

Mitigations include:

- cross-linking;
- project and theme indexes;
- recommendation lineage;
- periodic derived reviews.

### 27.5 Pattern overclaiming

A coincidence or small sample is presented as durable.

Mitigations include:

- confidence thresholds;
- sample and time bounds;
- contradictory evidence;
- alternate explanations;
- insufficient-evidence labels.

### 27.6 Retroactive rewriting

Existing historical artifacts are silently modified.

Mitigations include:

- immutable publications;
- revisions;
- supersession;
- correction records;
- exportable change history.

## 28. Observability

The archive SHOULD expose:

- artifact counts by type;
- coverage by time window;
- relationship completeness;
- unresolved outcomes;
- derived review freshness;
- stale or contradicted patterns;
- deletion and export status;
- search performance;
- migration or schema issues.

Archive metrics SHOULD not expose private artifact content in public or shared logs.

## 29. Success Criteria

The Archive and Longitudinal Intelligence System succeeds when:

- historical intelligence remains useful;
- trends become visible;
- repeated risks are identified earlier;
- strategic drift is detected;
- recommendations improve over time;
- long-term decision quality improves;
- the platform becomes more useful without becoming more intrusive;
- corrections and deletions remain trustworthy;
- users can explain how a historical conclusion was formed.

Candidate measurements include:

- historical retrieval usefulness;
- pattern validation rate;
- false-pattern correction rate;
- repeated-risk lead time;
- recommendation outcome follow-through;
- drift detection accuracy;
- archive migration integrity;
- deletion and export reliability;
- derived-review freshness.

## 30. Architectural Boundaries

The archive SHOULD remain separate from:

- raw source collection;
- live Work Context Brief generation;
- feedback collection;
- final delivery formatting;
- external action execution.

Subordinate specifications SHOULD define:

- artifact schemas;
- lineage and relationship types;
- retention and deletion;
- review generation;
- pattern confidence;
- search indexes;
- export format;
- snapshot and migration behavior.

## 31. Governance

Changes to retention, artifact types, pattern analysis, review levels, or relationship semantics MUST:

- identify affected vision requirements;
- document privacy and deletion impact;
- preserve historical provenance;
- preserve correction and supersession;
- include migration behavior;
- define rollback and audit procedures.

The archive MAY evolve its derived analyses and storage strategy. Its role as the longitudinal, user-controlled, lineage-preserving memory of decisions and outcomes SHOULD remain stable.
