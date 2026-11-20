# Context Collection Specification

**Status:** Proposed

**Version:** 1.1

**Classification:** Core Intelligence Specification

**Last Updated:** November 20, 2026

**Constitutional parent:** [Daily Intelligence Brief Vision Specification](daily-intelligence-brief-vision.md)

**Related specifications:**

- [Editorial Steering Specification](editorial-steering.md)
- [Recommendation Engine Specification](recommendation-engine.md)

---

## 1. Purpose

The Context Collection System gathers, normalizes, validates, and prepares activity data for downstream intelligence processing.

The purpose of collection is not archival completeness. It is awareness: understanding what the user is working on, thinking about, deciding, investigating, or reconsidering.

The system SHOULD continuously answer:

- what the user is working on;
- what problems are currently active;
- what decisions are unresolved;
- what investigations are underway;
- what topics or technologies are receiving attention;
- what material changed recently;
- what context is stale.

## 2. Scope

Context Collection is the observational layer of the platform. It transforms activity from user-facing systems into source-agnostic intelligence artifacts.

Examples include:

- AI conversations;
- coding sessions;
- repositories and commits;
- specifications and notes;
- research sessions;
- decisions and blockers;
- planning systems;
- project documentation;
- calendars or task systems when explicitly enabled.

Collection SHOULD not perform editorial ranking, recommendation, or final synthesis. It SHOULD provide normalized evidence and metadata for those layers.

## 3. Context Collection Principles

### 3.1 Local first

Collection and normalization SHOULD occur locally whenever possible.

Raw activity MUST remain under the user's control. Cloud synchronization is optional. Collection, normalization, and memory generation MUST remain capable of operating without a cloud service.

### 3.2 Explicit source authorization

The platform MUST obtain explicit authorization before enabling a source.

Authorization SHOULD identify:

- source identity;
- data categories collected;
- collection frequency;
- local or remote processing;
- retention;
- export or synchronization behavior;
- method of revocation.

Revoking a source SHOULD stop future collection and SHOULD trigger the applicable deletion or preservation policy.

### 3.3 Source agnostic downstream processing

Each source SHOULD be isolated behind an adapter.

Downstream systems SHOULD consume normalized Activity Records, project summaries, and evidence references rather than source-specific exports or raw source formats.

Source-specific intelligence SHOULD not leak into downstream interfaces unless the source is represented in provenance.

### 3.4 Context over archival

The system SHOULD favor relevant, decision-capable context over complete archival retention.

Raw history MAY be retained, but it SHOULD not be analyzed indefinitely without a retention and purpose justification.

### 3.5 Incremental processing

The system SHOULD process changes incrementally.

It SHOULD avoid repeatedly analyzing unchanged content and SHOULD preserve enough version identity to detect:

- new activity;
- edited content;
- deleted content;
- superseding evidence;
- stale or invalid records.

### 3.6 Graceful degradation

Failure of one source MUST not disable intelligence generation for all sources.

The system SHOULD:

- preserve partial context;
- mark missing or stale sources;
- continue with available evidence;
- expose collection errors;
- avoid presenting partial context as complete.

### 3.7 Data minimization

Collection SHOULD capture only the content, metadata, and evidence needed for the authorized context function.

The system SHOULD NOT collect broad content merely because it is accessible.

## 4. Collection Architecture

The collection pipeline SHOULD follow these stages:

```text
Source Systems
        |
        v
Authorized Adapters
        |
        v
Normalization
        |
        v
Validation and Classification
        |
        v
Sensitivity and Redaction
        |
        v
Activity Records
        |
        v
Incremental Summarization
        |
        v
Project and Work Context Updates
```

Each stage SHOULD remain independently replaceable.

Adapters MAY normalize data but MUST NOT perform editorial ranking, recommendation, or learning.

## 5. Source Adapters

Each source SHOULD be isolated behind an adapter with a source-specific contract.

Adapter responsibilities include:

- source authorization;
- data extraction;
- source event identity;
- timestamp normalization;
- source metadata preservation;
- incremental change detection;
- validation and error reporting;
- sensitive-data classification;
- export or import failure handling.

Candidate future sources include:

- AI coding and chat systems;
- Git and repository platforms;
- issue and project systems;
- email and calendar systems;
- notes;
- local documents;
- specification repositories;
- research and browser systems.

Adapter support SHOULD be additive. Introducing a new source MUST NOT require downstream systems to understand source-specific formats.

## 6. Activity Record

The Activity Record is the canonical normalized collection artifact.

Every record SHOULD contain:

- stable activity ID;
- source ID and source type;
- source event or document ID;
- observed timestamp;
- collected timestamp;
- source revision or update state;
- activity type;
- normalized summary;
- project association and confidence;
- technologies or topics;
- open questions or decisions;
- sensitivity classification;
- collection status;
- evidence or source reference;
- content hash or change identity;
- retention status.

An example shape is:

```json
{
  "activity_id": "act_2026-11-20_001",
  "source_type": "coding",
  "source_id": "claude_code",
  "source_event_id": "conversation_...",
  "observed_at": "2026-11-20T08:00:00Z",
  "collected_at": "2026-11-20T08:05:00Z",
  "project": {
    "id": "project_spec_stewardship",
    "confidence": 0.91,
    "source": "inferred"
  },
  "activity_type": "implementation",
  "summary": "Expanded recommendation lifecycle and evaluation architecture.",
  "topics": ["specifications", "recommendations", "governance"],
  "sensitivity": "private",
  "status": "active"
}
```

This shape is conceptual. Subordinate specifications MUST define validation, identifiers, retention, and storage.

## 7. Activity Types

An Activity Record SHOULD include one primary activity classification:

- research;
- planning;
- implementation;
- debugging;
- architecture;
- review;
- critique;
- decision;
- documentation;
- learning;
- investigation;
- discussion;
- maintenance;
- outcome observation.

Additional tags MAY supplement the primary classification. The primary value SHOULD describe the activity, not the source or channel.

## 8. Source Semantics

Different sources represent different kinds of cognitive and implementation activity.

Examples include:

| Source type | Typical evidence |
| --- | --- |
| Coding agent | Implementation, debugging, architecture, repository execution. |
| Chat agent | Reasoning, planning, decision analysis, exploration. |
| Applied coding system | Development activity and troubleshooting. |
| Research system | Discovery, external comparison, market or technical investigation. |
| Alternative reasoning system | Competing approaches, technical critique, alternative designs. |
| Repository platform | Changed code, reviews, issues, and repository state. |

Source semantics MAY inform confidence or aggregation. They MUST NOT become a fixed permanent ranking of an agent or source.

## 9. Normalization

Normalization SHOULD:

- parse source-specific fields;
- canonicalize timestamps;
- remove source-only presentation artifacts;
- identify changed content;
- preserve source references;
- classify activity;
- extract project, topic, decision, and blocker candidates;
- assign confidence and sensitivity;
- omit content that is not needed for downstream context.

Normalized summaries MUST not silently modify source meaning. The original source reference SHOULD remain available according to retention policy.

## 10. Incremental Updates

For mutable source content, the system SHOULD maintain:

- source revision;
- content or semantic change identity;
- prior normalized state;
- update timestamp;
- activity status;
- supersession or deletion state.

The system SHOULD distinguish:

- a new activity;
- a modification;
- a repeated observation;
- a duplicate;
- a deletion;
- a stale source event.

Incremental processing SHOULD not convert repeated synchronization into repeated user activity.

## 11. Project Inference

The collection system SHOULD attempt to identify project boundaries.

Project inference MAY use:

- repository identity;
- repeated terminology;
- conversation clustering;
- source project metadata;
- repeated references;
- issue or milestone context;
- specification relationships.

Project inference MUST be probabilistic. An inferred project SHOULD include:

- project candidate;
- confidence;
- evidence;
- first and latest activity;
- known technologies;
- related topics;
- status;
- manual override state.

The system SHOULD prevent one source or session from creating a project when the evidence remains weak.

Manual project control SHOULD permit:

- pinning;
- merging;
- splitting;
- renaming;
- archival;
- reassociation;
- override of inferred confidence.

Project inference behavior is governed by the [Editorial Steering Specification](editorial-steering.md).

## 12. Session Aggregation

Sessions SHOULD NOT automatically become intelligence artifacts.

Many sessions MAY represent one project or activity. The collection system SHOULD aggregate related activity before downstream processing.

Aggregation SHOULD preserve:

- source sessions;
- material state changes;
- decisions;
- open questions;
- blockers;
- deliverables;
- contradictions;
- confidence.

An aggregate SHOULD not erase the source evidence needed for traceability.

## 13. Context Freshness

Recent activity SHOULD receive preferential treatment.

Context collection SHOULD support an initial short horizon, such as 24 to 72 hours, and SHOULD not use one universal horizon for every activity type.

Freshness SHOULD vary by:

- project lifecycle;
- decision state;
- topic persistence;
- source reliability;
- explicit deadlines;
- user feedback;
- outcome observations;
- archival or completion state.

A stale record SHOULD remain available for historical reasoning but SHOULD be marked as stale before it influences current context.

Adaptive freshness MUST not create a rapid oscillation in project or topic relevance.

## 14. Context Weighting

Signals MAY decay over time.

Candidate influence categories include:

- current day: strong;
- recent week: moderate;
- recent month: weak;
- older quarter: historical.

These categories are policy examples, not fixed numerical requirements.

Weighting SHOULD consider meaning, confidence, source quality, repetition, project state, and contradiction. It SHOULD NOT rely on activity volume alone.

## 15. Summarization

Raw Activity Records SHOULD be distilled into concise project and work-context summaries.

Summaries SHOULD capture:

- what changed;
- what decisions occurred;
- what questions remain open;
- what blockers exist;
- what deliverables or milestones changed;
- what evidence remains uncertain;
- what context became stale.

Summaries SHOULD emphasize decision relevance over activity volume.

A summary SHOULD identify that it is generated and SHOULD preserve links to supporting records.

## 16. Sensitivity Classification

Activity Records SHOULD receive a sensitivity classification.

Candidate classifications include:

- public;
- internal;
- private;
- restricted;
- local only.

The final schema SHOULD support:

- source-defined sensitivity;
- content-derived sensitivity;
- user-defined sensitivity;
- sensitivity inheritance;
- overrides and correction;
- export and synchronization restrictions.

Sensitivity classification is not a substitute for authorization or encryption.

## 17. Redaction and Data Minimization

Sensitive information SHOULD be removed or transformed before downstream summarization whenever practical.

Examples include:

- credentials;
- API keys;
- customer identifiers;
- financial information;
- health or family information;
- personal identifiers;
- confidential or restricted source material.

Redaction SHOULD occur according to explicit classification rules and SHOULD record:

- whether redaction occurred;
- category of redacted content;
- redaction policy version;
- whether raw content remains locally retained;
- whether redacted data can be restored.

The system SHOULD NOT claim that information is deleted from a source when only a derived summary or exported copy was removed.

Raw collection and derived summaries SHOULD have separate retention controls.

## 18. Provenance

Every summarized or inferred context value SHOULD retain enough provenance to answer:

- what source supplied it;
- at what time;
- under what revision;
- with what confidence;
- whether it was inferred or directly stated;
- whether it was redacted;
- whether it has been corrected or superseded.

Collection provenance is mandatory for project inference and recommended context. It SHOULD also support later deletion and correction.

## 19. Failure Modes

The system SHOULD tolerate the following failures:

### 19.1 Missing source

The source becomes unavailable or authorization expires.

The system SHOULD:

- record the failure;
- stop repeated collection after a bounded retry policy;
- mark affected context stale;
- continue using available sources;
- avoid falsely presenting complete context.

### 19.2 Empty context

No significant activity is detected.

The system SHOULD:

- fall back to preference and historical context;
- reduce confidence in inferred projects;
- provide a sparse-context state;
- avoid inventing activity.

### 19.3 Misclassified project

Project inference produces inaccurate grouping.

The system SHOULD:

- allow manual correction;
- invalidate or revise derived context;
- preserve source records;
- recalculate affected summaries when practical.

### 19.4 Export failure

A source export is incomplete or fails.

The system SHOULD:

- log the failure;
- retain known valid records;
- mark an incomplete collection window;
- avoid combining partial records into a complete historical view.

### 19.5 Redaction failure

The system cannot confidently classify or redact sensitive content.

The system SHOULD:

- fail closed for downstream processing;
- retain only where explicitly authorized;
- notify the user or operator according to policy;
- prevent the content from entering an enabled cloud provider.

### 19.6 Adapter drift

A source changes format or semantics.

The system SHOULD:

- version adapter behavior;
- isolate the failure;
- retain source data where policy permits;
- mark derived records stale or invalid.

## 20. Privacy and Control

The system MUST:

- keep collection and normalization local unless explicitly enabled;
- disclose which sources and fields leave the local environment;
- require source-specific authorization;
- support export and deletion;
- support source revocation;
- prevent private or restricted records from entering public or shared output.

The user SHOULD be able to:

- enable or disable each source;
- inspect collected activity summaries;
- correct or remove project associations;
- set source-specific retention;
- delete raw and derived records;
- change sensitivity classifications;
- export collected context.

Collection controls SHOULD take effect for future collection and SHOULD initiate a defined treatment of existing collected data.

## 21. Observability

Collection operations SHOULD expose metrics such as:

- activities collected;
- activities updated or deleted;
- duplicates prevented;
- projects identified;
- project confidence distribution;
- source availability;
- collection errors;
- collection latency;
- summaries produced;
- context age;
- redaction events;
- incomplete collection windows;
- average context confidence.

Operational metrics SHOULD not expose activity content or sensitive project names in public logs.

## 22. Success Criteria

The Context Collection System succeeds when:

- active projects are accurately identified;
- intelligence reflects current verified work;
- collection remains source agnostic;
- new sources can be integrated without changing downstream contracts;
- context remains concise and relevant;
- stale or partial context is visible;
- sensitive information is protected;
- raw and derived data can be deleted or exported;
- collection failures degrade locally rather than disable the platform.

Candidate measurements include:

- project identification precision and recall;
- stale project reference rate;
- source availability;
- collection completeness;
- duplicate and missed update rate;
- redaction coverage;
- manual project correction rate;
- downstream recommendation quality by context quality.

## 23. Architectural Boundaries

Context Collection SHOULD remain separate from:

- memory storage;
- preference learning;
- editorial steering;
- recommendation generation;
- critique or reasoning agents;
- final briefing presentation;
- external action execution.

Subordinate specifications SHOULD define:

- adapter interfaces;
- Activity Record schemas;
- source authorization;
- project inference;
- redaction rules;
- incremental update semantics;
- retention and deletion;
- observability formats;
- source and project correction.

## 24. Governance

Changes to collection scope, source semantics, sensitivity, retention, or project inference MUST:

- identify affected vision requirements;
- document source and privacy impact;
- preserve source revocation and deletion;
- preserve downstream source agnosticism;
- include migration behavior for existing Activity Records;
- define rollback or correction procedures.

The collection pipeline MAY evolve. The system remains a source-agnostic, consent-based observational layer whose downstream value depends on normalized, traceable, and minimally retained context.
