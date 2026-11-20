# Memory Architecture Specification

**Status:** Proposed

**Version:** 1.1

**Classification:** Foundational Intelligence Specification

**Last Updated:** November 20, 2026

**Constitutional parent:** [Daily Intelligence Brief Vision Specification](daily-intelligence-brief-vision.md)

**Related specifications:**

- [Context Collection Specification](context-collection.md)
- [Work Context Brief Specification](work-context-brief.md)
- [Archive and Longitudinal Intelligence Specification](archive-longitudinal-intelligence.md)
- [Feedback Learning Specification](feedback-learning.md)

---

## 1. Purpose

The Memory Architecture preserves, organizes, retrieves, governs, and maintains durable intelligence across time.

Its purpose is useful recall, not maximum retention.

A memory system SHOULD improve future reasoning by surfacing the right information at the right time while minimizing noise, bloat, corruption, and unsupported inference.

## 2. Mission

The memory system SHOULD answer:

- what should the platform remember;
- what should it forget or deprioritize;
- what should surface now;
- what should remain dormant;
- what memories conflict;
- what relationships support or invalidate a conclusion.

## 3. Core Philosophy

More memory is not better. Better memory is better.

The objective is optimal recall, not maximum retention.

The platform SHOULD distinguish:

- a source observation;
- a summary;
- an inference;
- a memory;
- a preference;
- a strategic principle;
- a historical snapshot.

These forms have different confidence, retention, and retrieval behavior.

A retrieved memory SHOULD be useful, relevant, current where required, and explainable.

## 4. Design Principles

### 4.1 Relevance over volume

The system SHOULD retain information that continues to create value or support future decisions.

Accumulation without retrieval value SHOULD be treated as an archive or ephemeral data problem, not automatically as memory.

### 4.2 Retrieval over storage

Memory success SHOULD be measured by retrieval quality rather than storage capacity.

Candidate retrieval quality measures include:

- precision;
- recall;
- usefulness;
- context match;
- contradiction awareness;
- latency;
- provenance availability.

### 4.3 Explainable recall

Every retrieved memory SHOULD expose:

- why it was retrieved;
- its confidence;
- its importance;
- its source and age;
- its relationship to the query or context;
- any contradictions;
- any staleness or supersession.

The system SHOULD not present a memory as direct truth unless its evidence supports that interpretation.

### 4.4 Healthy decay

Not every memory deserves equal permanence.

Memory strength SHOULD evolve through:

- time;
- retrieval;
- confirmation;
- contradiction;
- feedback;
- outcomes;
- project lifecycle;
- explicit correction.

### 4.5 Governance

Unmanaged memory degrades reasoning and privacy.

Memory governance SHOULD include:

- formation rules;
- promotion and demotion;
- retention;
- consolidation;
- archive and purge rules;
- validation;
- contradiction handling;
- deletion and export.

## 5. Architectural Layers

The memory system SHOULD contain separate layers:

```text
Working Memory
        |
        v
Episodic Memory
        |
        v
Semantic Memory
        |
        v
Strategic Memory
        |
        v
Archived Memory
```

Each layer SHOULD have distinct formation, decay, retrieval, and governance behavior.

The layers MAY share storage but SHOULD remain logically distinct.

## 6. Working Memory

Working Memory supports current reasoning.

Candidate horizon:

- minutes to days.

Examples include:

- active projects;
- current investigations;
- open decisions;
- immediate blockers;
- recently requested work;
- temporary task state.

Working Memory SHOULD be volatile, versioned, and bounded.

It SHOULD expire or consolidate instead of automatically becoming strategic knowledge.

The Work Context Brief is a snapshot derived from current context and memory. It is not itself the memory store.

## 7. Episodic Memory

Episodic Memory preserves experiences and events.

Candidate horizon:

- days to years.

Examples include:

- meaningful conversations;
- decisions;
- project milestones;
- recommendations and outcomes;
- completed investigations;
- significant errors or corrections.

Episodic Memory answers:

“What happened, when, and in what context?”

Episodic memories SHOULD remain linked to source evidence and SHOULD not be rewritten retroactively.

## 8. Semantic Memory

Semantic Memory preserves concepts and knowledge independently of a single event.

Examples include:

- definitions;
- architectural patterns;
- technology knowledge;
- stable relationships;
- governing principles;
- verified factual knowledge.

Semantic Memory answers:

“What does the platform know or believe about this subject?”

Semantic memories SHOULD:

- distinguish verified knowledge from inference;
- include source and confidence;
- remain revisable;
- preserve contradiction and supersession;
- avoid absorbing transient project state.

## 9. Strategic Memory

Strategic Memory preserves high-value long-term intelligence.

Examples include:

- core goals;
- enduring principles;
- strategic themes;
- major decisions;
- validated lessons;
- stable user-confirmed preferences.

Strategic Memory changes slowly.

It SHOULD require stronger evidence and stronger promotion rules than episodic or working memories.

Inferred identity or personality claims MUST NOT enter Strategic Memory merely because a model repeats them.

## 10. Archived Memory

Archived Memory preserves history without allowing ordinary retrieval to treat it as current.

Examples include:

- completed projects;
- obsolete recommendations;
- superseded architectures;
- historical decisions;
- old assumptions;
- resolved investigations.

Archived Memory SHOULD remain searchable and usable for historical analysis.

It SHOULD have low normal retrieval influence and SHOULD become visible when:

- a historical comparison requires it;
- a project or decision is revisited;
- the user requests it;
- it remains necessary for outcome or contradiction analysis.

## 11. Memory Objects

Every memory SHOULD be represented as a first-class object.

A memory object SHOULD include at least:

- memory ID;
- memory type;
- memory layer;
- created and updated timestamps;
- valid time range;
- confidence;
- importance;
- evidence and provenance;
- source references;
- sensitivity;
- relationships;
- lifecycle state;
- retrieval state;
- revision or supersession state.

An example shape is:

```json
{
  "memory_id": "mem_2026-11-20_001",
  "memory_type": "decision",
  "memory_layer": "episodic",
  "created_at": "2026-11-20T09:00:00Z",
  "confidence": 0.91,
  "importance": 0.88,
  "valid_until": null,
  "relationships": [],
  "sensitivity": "private",
  "lifecycle": "active"
}
```

The example is conceptual. Subordinate specifications MUST define identifiers, ranges, relationships, and validation.

## 12. Memory Types

Supported memory types SHOULD include:

- observation;
- decision;
- project;
- conversation summary;
- recommendation;
- critique;
- insight;
- risk;
- opportunity;
- goal;
- preference;
- assumption;
- outcome;
- source or evidence record;
- correction;
- pattern or theme.

Memory types MAY expand, but a new type SHOULD preserve provenance and retrieval semantics.

## 13. Importance and Confidence

Importance and confidence are separate dimensions.

### 13.1 Importance

Importance measures the potential value of the memory.

Factors MAY include:

- strategic relevance;
- outcome impact;
- user-confirmed value;
- project dependence;
- repeated retrieval;
- governance or safety significance.

Importance SHOULD not increase merely because the memory is recent or frequently repeated.

### 13.2 Confidence

Confidence measures how trustworthy or accurate the memory appears.

Factors MAY include:

- source quality;
- evidence independence;
- confirmation;
- contradiction;
- retrieval provenance;
- age;
- user correction.

Confidence SHOULD not imply importance, and importance SHOULD not imply truth.

## 14. Memory Relationships

Memories SHOULD support typed relationships.

Candidate types include:

- supports;
- contradicts;
- extends;
- depends on;
- derived from;
- related to;
- supersedes;
- revises;
- applies to;
- caused or influenced;
- belongs to.

Relationships SHOULD carry:

- source memory;
- target memory;
- relationship type;
- evidence;
- confidence;
- created and valid times;
- lifecycle state.

Absence of a relationship SHOULD be distinguishable from an unknown relationship.

## 15. Knowledge Graphs

The platform MAY use graph storage or graph-like indexes.

An example structure is:

```text
Project
    |
    v
Decision
    |
    v
Recommendation
    |
    v
Outcome
```

Graphs MAY support:

- relationship retrieval;
- lineage;
- contradiction detection;
- dependency analysis;
- historical reasoning;
- evidence and source traceability.

Graph visualization SHOULD not replace provenance or correction controls.

## 16. Retrieval Architecture

The platform SHOULD support multiple retrieval modes.

### 16.1 Semantic retrieval

Retrieval by meaning or conceptual similarity.

### 16.2 Episodic retrieval

Retrieval based on events, experiences, or time.

### 16.3 Temporal retrieval

Retrieval based on recency and valid time.

### 16.4 Strategic retrieval

Retrieval based on goals, principles, or long-term themes.

### 16.5 Relationship retrieval

Retrieval based on typed graph connections.

Retrieval SHOULD combine modes only when the combination improves relevance and remains explainable.

## 17. Memory Formation

Not every observation SHOULD become memory.

Memory formation SHOULD consider:

- novelty;
- importance;
- repetition;
- outcome impact;
- strategic relevance;
- user confirmation;
- evidence quality;
- contradiction;
- sensitivity;
- retention policy.

Memory SHOULD be earned through sufficiently meaningful evidence and policy.

Transient chat activity SHOULD not automatically become strategic or semantic memory.

## 18. Consolidation

The system SHOULD consolidate repeated or related memories into stronger knowledge structures.

Example:

```text
Five observations
        |
        v
One documented pattern
        |
        v
Source-linked evidence and confidence
```

Consolidation SHOULD:

- preserve source memories or references;
- declare what was merged;
- retain uncertainty;
- preserve contradictions;
- create a replacement or derived relationship;
- support deconsolidation or correction.

No consolidation SHOULD silently destroy source evidence.

## 19. Memory Strength

Memory strength SHOULD evolve through:

- retrieval usefulness;
- confirmation;
- utility;
- outcome validation;
- explicit feedback;
- repeated independent evidence;
- relationship support.

Strength SHOULD not increase solely because a source repeats the same claim.

Independent confirmation SHOULD be distinguished from repeated reuse of dependent or generated evidence.

## 20. Memory Decay

Memory strength SHOULD decrease through:

- inactivity;
- irrelevance;
- contradiction;
- lack of retrieval;
- project completion;
- outdated evidence;
- source deprecation;
- explicit feedback.

Decay SHOULD vary by memory layer:

- Working Memory decays quickly;
- Episodic Memory retains historical context but loses normal influence;
- Semantic Memory remains persistent when confirmed;
- Strategic Memory changes slowly;
- Archived Memory is visible for history, not current recommendation by default.

Decay SHOULD reduce retrieval priority and confidence before deleting a memory.

## 21. Promotion and Demotion

Promotion SHOULD require:

- sufficient evidence;
- stable value;
- policy compliance;
- low contradiction;
- appropriate sensitivity;
- explicit or well-supported formation criteria.

Examples include promotion from:

- working to episodic;
- episodic to semantic;
- semantic to strategic;
- active to archived.

Demotion SHOULD occur for:

- contradiction;
- stale evidence;
- completed projects;
- failed outcomes;
- user correction;
- low retrieval utility;
- policy or privacy change.

Promotion SHOULD remain visible and reversible.

## 22. Strategic Purging

The system SHOULD support deliberate forgetting.

Purging MAY apply to:

- obsolete recommendations;
- invalid assumptions;
- superseded architectures;
- proven false information;
- completed sensitive context;
- deleted or revoked sources;
- memories without a valid retention purpose.

Purging SHOULD distinguish:

- deletion;
- archival;
- anonymization;
- de-indexing;
- invalidation;
- supersession.

Purging SHOULD not silently erase historical contradiction or audit records unless policy explicitly allows it.

## 23. Memory Poisoning Defense

The platform SHOULD defend against corrupted or false memories.

Potential sources include:

- bad data;
- incorrect assumptions;
- hallucinated conclusions;
- repeated misinformation;
- compromised sources;
- stale derived summaries.

Defense SHOULD include:

- source provenance;
- confidence ceilings;
- contradiction detection;
- independent validation where practical;
- quarantine of low-evidence material;
- user correction;
- revision and supersession;
- no automatic promotion from derived output alone.

Memory poisoning SHOULD be detected and surfaced rather than hidden.

## 24. Contradiction Management

Memories MAY conflict.

Example:

```text
Memory A:
Approach X worked.

Memory B:
Approach X failed.

Memory C:
Approach X worked only in Project Y.
```

Contradictions SHOULD be preserved until the evidence is resolved.

The system SHOULD:

- identify both claims;
- preserve source and time;
- lower or bound confidence;
- avoid averaging conflicting claims into false certainty;
- surface unresolved contradictions;
- permit supersession or scoped reconciliation.

Historical truth may differ from current truth.

## 25. Memory Auditing

The platform SHOULD support questions such as:

- why does this memory exist;
- how was it formed;
- why was it retrieved;
- what evidence supports it;
- what depends on it;
- what contradictions exist;
- when was it changed;
- who or what approved or inferred it;
- how is it governed.

Audit records SHOULD be privacy-aware and SHOULD preserve source lineage.

## 26. Privacy and Deletion

Memory is potentially sensitive.

The system MUST:

- keep core memory local unless explicitly authorized;
- disclose external memory or model-provider usage;
- support export and deletion;
- support source revocation;
- prevent private memories from public or shared output;
- separate raw evidence, memory, preferences, and derived intelligence.

The user SHOULD be able to:

- view important memories;
- correct or reject memories;
- archive or purge memories;
- set sensitivity and retention;
- disable inferred memory formation;
- delete a source and derived memory relationships;
- export memory and provenance.

Deleting a source SHOULD trigger the applicable treatment of derived memory. It SHOULD not leave hidden memory links that continue to influence future reasoning.

## 27. Retrieval Failure Modes

The platform SHOULD mitigate:

### 27.1 Irrelevant retrieval

Memories surface despite weak relation to the current context.

Mitigations include:

- semantic and temporal constraints;
- confidence thresholds;
- relationship checks;
- source freshness;
- user correction.

### 27.2 Stale retrieval

Old context is presented as current.

Mitigations include:

- valid time;
- staleness labels;
- project lifecycle;
- supersession;
- archival demotion.

### 27.3 Fragmented retrieval

Related memories are returned separately.

Mitigations include:

- consolidation;
- relationship retrieval;
- grouped evidence;
- deduplication.

### 27.4 Hallucinated memory

The system treats a model-generated inference as established fact.

Mitigations include:

- provenance;
- confidence ceilings;
- direct-evidence requirements;
- inference labels;
- promotion review.

### 27.5 Contradiction averaging

Conflicting memories are blended into false certainty.

Mitigations include:

- typed contradiction;
- confidence bounds;
- conflict-aware ranking;
- user and model-visible resolution state.

## 28. Memory Health Metrics

Examples include:

- memory count by layer;
- retrieval success;
- retrieval precision;
- useful recall;
- stale recall;
- contradiction rate;
- memory poisoning indicators;
- consolidation rate;
- purge and archival activity;
- derived-memory density;
- source coverage;
- correction frequency;
- deletion success.

Health metrics SHOULD not expose memory content or sensitive identities.

## 29. Success Criteria

The Memory Architecture succeeds when:

- useful information is retrieved reliably;
- retrieval quality improves over time;
- noise decreases;
- stale and contradictory information is visible;
- memory poisoning is minimized;
- strategic knowledge persists;
- memories are inspectable and reversible;
- privacy and deletion remain trustworthy;
- long-term intelligence quality improves.

Candidate measurements include:

- retrieval precision and usefulness;
- stale-memory retrieval rate;
- contradiction resolution time;
- memory correction and deletion success;
- consolidation quality;
- strategic memory stability;
- retrieval latency;
- privacy and source-revocation compliance.

## 30. Architectural Boundaries

The Memory Architecture SHOULD remain separate from:

- raw Activity Records;
- live source collection;
- Work Context Brief snapshots;
- recommendation lifecycle;
- feedback storage;
- final editorial formatting;
- external action execution.

Subordinate specifications SHOULD define:

- memory object schemas;
- memory layers;
- retrieval interfaces;
- relationship types;
- promotion and decay;
- consolidation;
- contradiction handling;
- deletion and export;
- privacy and observability.

## 31. Governance

Changes to memory formation, promotion, decay, purging, relationship semantics, or retrieval SHOULD:

- identify affected vision requirements;
- preserve provenance;
- preserve contradiction and supersession;
- document privacy and deletion impact;
- define migration behavior;
- include rollback and audit procedures.

The memory system MAY evolve storage and retrieval strategies. Its role is selective, governed, evidence-aware preservation in service of future intelligence.
