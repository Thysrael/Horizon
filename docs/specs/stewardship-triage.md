# Specification Stewardship Triage

**Status:** Proposed

**Version:** 1.0

**Classification:** Stewardship Record

**Last Updated:** November 20, 2026

**Scope:** Initial review of the Daily Intelligence Brief specification corpus under `docs/specs/`.

---

## 1. Review Result

The specification corpus is structurally complete enough to guide a vertical-slice implementation, but it is not yet implementation-ready as a whole.

The documents consistently preserve the same constitutional direction:

- local-first operation;
- traceability;
- advisory rather than autonomous behavior;
- anti-echo-chamber safeguards;
- privacy and deletion control;
- bounded, durable, and revisable artifacts;
- human authority;
- separation of collection, memory, knowledge, reasoning, orchestration, and delivery.

The primary remaining work is integration, priority, and missing implementation contracts.

## 2. Corpus Health

| Area | Assessment |
| --- | --- |
| Vision and principles | Stable enough to govern subordinate specifications. |
| Product boundaries | Generally consistent across delivery and non-goal documents. |
| Core data concepts | Present, but not yet unified by canonical schemas. |
| Cross-spec lifecycle rules | Partially overlapping and requiring reconciliation. |
| Privacy and retention | Strong but distributed across multiple documents. |
| MVP priority | Not yet established. |
| Implementation migration | Horizon's existing pipeline is not yet mapped into the future architecture. |

## 3. Priority Triage

### P0 - Required before implementation planning

#### P0-1. Add a vertical-slice MVP specification

Create a subordinate specification that defines one complete first release:

```text
authorized source collection
  -> context summary
  -> one edition
  -> feedback
  -> persisted outcome
  -> next edition improvement
```

The MVP specification SHOULD select:

- the first supported source;
- the canonical edition format;
- the minimum context fields;
- the minimum feedback fields;
- the minimum persistence model;
- fallback behavior;
- privacy behavior;
- success metrics;
- explicit non-goals.

Without this document, the architecture can be implemented in multiple incompatible ways.

**Disposition:** Required.

#### P0-2. Define canonical artifact schemas and identifiers

The corpus uses similar concepts but does not define a shared contract for:

- IDs;
- timestamps and valid-time ranges;
- confidence and importance;
- sensitivity;
- provenance;
- lifecycle state;
- revision and supersession;
- relationship types;
- source and model identity.

Create a cross-cutting data contract specification or schema set. It SHOULD be referenced by all artifact-producing documents.

**Disposition:** Required.

#### P0-3. Reconcile recommendation lifecycle terminology

The Feedback Learning Specification and Recommendation Engine Specification both describe recommendation lifecycle states, with overlapping but not identical terms.

A canonical recommendation lifecycle specification SHOULD define:

- valid states;
- allowed transitions;
- terminal and deferred states;
- retry behavior;
- revision versus replacement;
- supersession and invalidation;
- publication versus implementation versus outcome.

**Disposition:** Required before recommendation storage or workflow implementation.

#### P0-4. Reconcile memory, archive, knowledge, and context boundaries

The boundaries are conceptually clear but need a source-of-truth matrix.

The next architecture document or schema contract SHOULD define:

| Artifact | Primary owner | Mutability | Normal retrieval | Historical use |
| --- | --- | --- | --- | --- |
| Activity Record | Collection | Append/update | Low | Source evidence |
| Work Context Brief | Context pipeline | Superseded snapshot | High and bounded | Context drift |
| Memory | Memory system | Revisable | Medium | Episodic and historical |
| Knowledge | Knowledge system | Revisable | High | Pattern and concept |
| Edition | Delivery archive | Immutable publication | By date or navigation | Longitudinal review |
| Recommendation | Recommendation engine | Revisable lifecycle | Active and deferred | Outcome history |

**Disposition:** Required to prevent duplication and conflicting updates.

#### P0-5. Create a privacy and retention policy specification

The corpus repeats privacy and deletion requirements across collection, memory, archive, delivery, feedback, and orchestration.

The common policy SHOULD define:

- classification levels;
- raw evidence retention;
- derived-memory retention;
- archive retention;
- deletion propagation;
- source revocation;
- export;
- encryption;
- notification of cloud processing;
- public and private channel separation.

**Disposition:** Required before introducing persistent storage or external providers.

### P1 - Required before full implementation

#### P1-1. Add an MVP data migration specification

Map existing Horizon capabilities to the future architecture:

- source collection and scrapers;
- profile routing;
- scoring and filtering;
- deduplication;
- Markdown and Pages delivery;
- email and webhook delivery;
- history and web search;
- MCP operations.

The migration specification SHOULD identify:

- reuse;
- adaptation;
- deprecation;
- explicit incompatibility;
- data migration steps.

**Disposition:** Required for implementation compatibility.

#### P1-2. Define success baselines and experiments

Current success criteria are broadly stated and use candidate targets.

Add baselines for:

- edition relevance;
- lead-story relevance;
- counterpoint utility;
- recommendation value;
- outcome-positive rate;
- false-positive and false-negative rates;
- context correction rate;
- exploration utility;
- memory retrieval quality.

The MVP specification SHOULD define one primary outcome metric and a small set of guardrails.

**Disposition:** Required before making exploration or steering a release gate.

#### P1-3. Reconcile confidence semantics

Several specifications assign confidence to:

- Activity Records;
- project inference;
- Work Context Brief fields;
- recommendations;
- memories;
- knowledge;
- reasoning outputs;
- outcomes;
- drift and patterns.

Create a shared confidence model defining:

- numeric range;
- qualitative labels;
- evidence independence;
- source quality;
- contradiction;
- calibration;
- staleness;
- whether confidence may be aggregated.

**Disposition:** Required for consistent data contracts.

#### P1-4. Define agent and model accountability minimums

Agent accountability should begin with minimum attribution rather than full ranking.

The first implementation SHOULD record:

- generating agent;
- primary and contributing role;
- model and provider version;
- prompt or policy version;
- source evidence;
- revision and outcome links.

Trust, influence, and retirement can remain deferred.

**Disposition:** Implement after canonical artifacts exist.

#### P1-5. Validate the exploration budget empirically

The 70/20/10 proposals should not become hidden constants before baseline data exists.

Implementation SHOULD support:

- configurable totals;
- per-section controls;
- user override;
- explicit audit metadata;
- a trial period;
- feedback-based evaluation.

**Disposition:** Keep configurable; do not encode as a universal requirement.

### P2 - Post-MVP enhancements

- knowledge graph visualization;
- autonomous research missions;
- dynamic agent creation;
- agent debate and consensus;
- predictive retrieval;
- audio editions;
- voice feedback;
- scenario planning;
- cross-model comparative dashboards;
- multi-provider cloud synchronization.

These capabilities should remain future options until the MVP proves the core loop.

## 4. Cross-Spec Consistency Findings

### Finding C-1: Lifecycle naming

The recommendation lifecycle appears in both Feedback Learning and Recommendation Engine.

**Risk:** two implementations may interpret equivalent states differently.

**Resolution:** one canonical lifecycle, with any presentation-specific labels in delivery only.

### Finding C-2: Memory versus archive

The documents define memory as selective recall and the archive as longitudinal preservation. This boundary is sound, but no shared deletion propagation is defined.

**Risk:** deleted source evidence may continue influencing derived memory or recommendations.

**Resolution:** common retention and invalidation contract.

### Finding C-3: Recommendation versus outcome attribution

The specs correctly require conservative causal attribution, but no shared outcome schema or follow-up status is specified.

**Risk:** positive outcomes could be inferred inconsistently across feedback, recommendation, agent, and archive systems.

**Resolution:** a canonical outcome artifact linked to recommendation, evidence, observation time, and causal confidence.

### Finding C-4: Work Context Brief versus memory

The WCB is described as a snapshot derived from current context and memory. This is consistent, but snapshot invalidation and correction propagation is incomplete.

**Resolution:** snapshots must be immutable or superseding, while active context remains a separately recomputable view.

### Finding C-5: Steering and feedback budgets

Feedback Learning and Editorial Steering both propose exploration budgets. Both may be valid at different levels, but they need a shared precedence rule.

**Resolution:** selection policy owns the edition distribution; feedback updates policy inputs within bounded limits.

### Finding C-6: Agent accountability is deferred

Agent accountability is now a large capability before there is an artifact-producing MVP.

**Resolution:** MVP should capture attribution and outcome links; dashboard ranking and influence should follow evidence.

## 5. Missing Specifications

The following subordinate specifications would materially reduce implementation ambiguity:

1. **MVP Vertical Slice**
2. **Cross-Cutting Artifact and ID Contract**
3. **Privacy and Retention Policy**
4. **Data Migration and Horizon Integration**
5. **Confidence and Calibration Model**
6. **Recommendation Lifecycle and Outcome Contract**
7. **Source Authorization and Revocation**
8. **Quality Gate and Release Contract**
9. **Observability and Audit Event Contract**
10. **Testing and Evaluation Specification**

The first five are P0/P1 foundations. The others should follow during implementation design.

## 6. Recommended Review Sequence

The corpus SHOULD be reviewed and implemented in this order:

1. Governance and vision;
2. MVP vertical-slice behavior;
3. data and ID contract;
4. privacy and retention;
5. Horizon migration;
6. context collection and Work Context Brief;
7. feedback and recommendation lifecycle;
8. delivery and archive;
9. memory and knowledge;
10. reasoning and orchestration;
11. agent accountability and advanced longitudinal analysis.

This sequence minimizes duplicated storage and prevents premature agent architecture.

## 7. Stewardship Decisions

The following decisions are recommended:

- **Do not implement all layered systems in the initial release.**
- **Use one complete daily-brief loop as the MVP proof.**
- **Keep memory and knowledge logically distinct even if the MVP uses shared storage.**
- **Keep the archive as a reviewable publication and outcome store.**
- **Make recommendation and outcome schemas canonical before agent accounting.**
- **Keep exploration budgets configurable and experimental.**
- **Defer trust-score dashboards until sufficient outcomes exist.**
- **Preserve every refined specification as a proposed architectural contract.**
- **Add implementation specifications rather than weakening the vision corpus.**

## 8. Stewardship Status

The corpus is suitable for the next stage:

**MVP specification, cross-cutting contracts, and implementation migration planning.**
