# Chief of Staff Orchestration Specification

**Status:** Proposed

**Version:** 1.1

**Classification:** Core System Orchestration Specification

**Last Updated:** November 20, 2026

**Constitutional parent:** [Daily Intelligence Brief Vision Specification](daily-intelligence-brief-vision.md)

**Related specifications:**

- [Context Collection Specification](context-collection.md)
- [Memory Architecture Specification](memory-architecture.md)
- [Knowledge Layer Specification](knowledge-layer.md)
- [Reasoning Layer Specification](reasoning-layer.md)
- [Recommendation Engine Specification](recommendation-engine.md)
- [Daily Intelligence Delivery Platform Specification](daily-intelligence-delivery-platform.md)
- [Feedback Learning Specification](feedback-learning.md)

---

## 1. Purpose

The Chief of Staff Orchestration Layer coordinates intelligence activities across the platform.

It does not replace context collection, memory, knowledge, reasoning, recommendation, delivery, or feedback.

It determines:

- what workflows run;
- when and why they run;
- what dependencies apply;
- how agents contribute;
- how outputs are produced and validated;
- how failures are isolated;
- how feedback and learning are incorporated.

## 2. Mission

The orchestration system SHOULD answer:

- what should happen next;
- what intelligence work is warranted now;
- what dependencies must complete;
- what quality gates apply;
- how partial or failed work should proceed;
- what remains under human authority.

The orchestration layer should transform independent subsystems into a coherent operating system.

## 3. Architectural Position

The orchestration layer coordinates the major platform domains:

```text
Context Collection
        |
        v
Memory
        |
        v
Knowledge
        |
        v
Reasoning
        |
        v
Recommendations and Critiques
        |
        v
Delivery
        |
        v
Feedback
        |
        v
Learning and Historical Review
```

The orchestrator should remain replaceable and SHOULD not embed domain logic belonging to these subsystems.

## 4. Core Principles

### 4.1 Workflow, not tool collection

The platform SHOULD operate as an intelligence organization rather than an unrelated collection of tools.

Work SHOULD flow through defined stages, dependencies, and quality gates.

### 4.2 Evidence before action

The orchestrator SHOULD collect sufficient evidence before starting consequential work.

It SHOULD avoid executing a workflow merely because a trigger occurred when the required context or authorization is missing.

### 4.3 Human authority

The user remains the final authority for decisions and consequential actions.

The platform MAY recommend, investigate, critique, and prepare work.

It MUST NOT claim execution, approval, or outcome ownership without explicit authorization.

### 4.4 Isolation

A failure in one source or agent SHOULD not invalidate the entire intelligence cycle.

The orchestrator SHOULD support:

- partial workflows;
- degraded outputs;
- fallback data;
- explicit missing data;
- later retries;
- no false success.

### 4.5 Explainability

Every workflow run SHOULD expose:

- trigger;
- workflow version;
- dependencies;
- participating agents;
- source and context versions;
- quality gates;
- outcomes;
- failures;
- delivery state.

## 5. Intelligence Lifecycle

The core lifecycle SHOULD be:

```text
Observe
    |
    v
Remember
    |
    v
Understand
    |
    v
Reason
    |
    v
Recommend
    |
    v
Deliver
    |
    v
Learn
    |
    v
Review
```

Subordinate workflows SHOULD map back to these stages.

The lifecycle is a conceptual dependency model, not a requirement that every run execute every stage.

## 6. Core Workflows

### 6.1 Daily intelligence workflow

A typical daily workflow SHOULD:

1. collect current authorized activity;
2. validate collection state;
3. update memory and project context;
4. update relevant knowledge;
5. refresh the Work Context Brief;
6. run editorial steering;
7. generate recommendations and critiques;
8. run quality gates;
9. generate the edition;
10. deliver authorized channels;
11. capture feedback;
12. update learning records;
13. archive the edition and context versions.

### 6.2 Weekly workflow

The weekly workflow SHOULD aggregate daily intelligence to identify:

- repeated recommendations;
- active projects;
- emerging themes;
- unresolved blockers;
- recommendation outcomes;
- new or fading risks;
- strategic drift;
- positive or negative trends.

### 6.3 Monthly workflow

The monthly workflow SHOULD emphasize:

- goals;
- direction;
- project momentum;
- opportunity and risk balance;
- assumption changes;
- major decisions;
- recommendation outcomes.

### 6.4 Quarterly workflow

The quarterly workflow SHOULD support executive review:

- themes defining the quarter;
- investments and outcomes;
- failed or invalidated assumptions;
- projects creating value;
- strategic shifts;
- major unresolved risks.

### 6.5 Annual workflow

The annual workflow SHOULD support transformation review:

- year-over-year priorities;
- capability and knowledge changes;
- recurring weaknesses;
- major decisions;
- project and theme evolution;
- persistent opportunities and risks.

### 6.6 Special report workflow

On explicit user request or a validated strategic trigger, the orchestrator MAY produce:

- research reports;
- risk reviews;
- architecture reviews;
- project postmortems;
- assumption reviews;
- scenario analyses;
- counterpoint briefs.

The requested scope and evidence should determine the workflow.

## 7. Trigger Types

Workflows MAY be triggered by:

### 7.1 Scheduled events

Examples include:

- morning edition;
- weekly review;
- monthly review;
- quarterly review;
- outcome follow-up.

Schedules SHOULD be user-configurable and SHOULD have timezone, duplication, and missed-run behavior.

### 7.2 Activity events

Examples include:

- new significant activity;
- project change;
- major decision;
- blocker resolution;
- source availability restoration.

Activity triggers SHOULD be thresholded to avoid noisy workflows.

### 7.3 User events

Examples include:

- manual edition request;
- research request;
- investigation request;
- archive review;
- feedback submission;
- explicit correction.

### 7.4 Strategic events

Examples include:

- risk threshold exceeded;
- recommendation repeated;
- project momentum collapse;
- contradictory evidence;
- recommendation invalidation;
- outcome requiring follow-up.

Strategic triggers SHOULD include confidence thresholds and evidence scope.

## 8. Workflow Structure

A workflow SHOULD be represented as a versioned dependency graph.

Each workflow step SHOULD define:

- step ID;
- domain or agent;
- required inputs;
- produced outputs;
- prerequisites;
- timeout;
- retry behavior;
- idempotency;
- quality gates;
- privacy and authorization;
- failure policy;
- observability.

The orchestrator SHOULD validate the graph before execution.

## 9. Idempotency

Every workflow run SHOULD have a stable run ID.

Repeat execution SHOULD not:

- duplicate editions;
- duplicate recommendations;
- duplicate feedback events;
- duplicate memory records;
- duplicate delivery;
- append false activity.

The system SHOULD support:

- already-completed step detection;
- retry after partial failure;
- explicit rerun or regeneration;
- replacement and supersession.

## 10. Agent Coordination

Agents SHOULD operate as specialists.

Examples include:

- research agent;
- memory agent;
- project agent;
- strategy agent;
- critique agent;
- recommendation agent;
- opportunity agent;
- risk agent;
- editorial agent.

Coordination SHOULD define:

- role;
- input contract;
- output contract;
- confidence and evidence requirements;
- timeout;
- authority;
- attribution;
- retry policy;
- privacy boundary.

The orchestrator SHOULD not grant an agent more authority than its domain requires.

## 11. Multi-Agent Collaboration

No single agent SHOULD own all reasoning.

Collaborative products SHOULD preserve:

- primary agent;
- contributing agents;
- reviewer or critique agent;
- disagreements;
- source evidence;
- revision state;
- agent attribution.

Independent critique SHOULD remain possible even when the orchestrator strongly favors a primary recommendation.

## 12. Workflow Prioritization

Not all work is equally important.

The orchestrator SHOULD prioritize:

- material and evidenced risks;
- strategic opportunities;
- pending decisions;
- active projects;
- long-term goals;
- repeated unresolved recommendations;
- outcome follow-up;
- user-requested work.

Urgency alone SHOULD not determine priority.

The orchestrator SHOULD expose priority reasons and SHOULD avoid silent starvation of lower-priority work.

## 13. Context Refresh

Context refresh SHOULD use explicit cadences.

Candidate cadences include:

| Context type | Candidate refresh |
| --- | --- |
| Activity | Near real-time or source-dependent. |
| Work Context Brief | Daily or on meaningful change. |
| Strategic themes | Weekly or on evidence threshold. |
| Knowledge review | Monthly or on contradiction. |
| Memory governance | Scheduled and event-driven. |

The orchestrator SHOULD preserve source completeness and SHOULD mark stale context.

## 14. Recommendation Workflow

Recommendations SHOULD follow:

```text
Create
    |
    v
Evaluate
    |
    v
Publish
    |
    v
Track
    |
    v
Measure Outcome
    |
    v
Learn
```

Recommendation generation SHOULD not be considered complete merely because an edition was generated.

The workflow SHOULD support:

- deferred evaluation;
- implementation feedback;
- outcome follow-up;
- supersession;
- repeated recommendation suppression;
- evidence invalidation.

## 15. Critique Workflow

Critique SHOULD operate independently of recommendation generation.

Example:

```text
Recommendation or Insight
        |
        v
Critique Review
        |
        v
Weaknesses or Contradictions
        |
        v
Refinement or Rejection
```

The critique SHOULD not be a rubber stamp.

It SHOULD:

- identify missing evidence;
- challenge hidden assumptions;
- compare alternatives;
- identify privacy or safety issues;
- preserve unresolved disagreement.

## 16. Learning Workflow

Learning MAY occur through:

- feedback;
- outcomes;
- behavior;
- agent performance;
- contradiction resolution;
- source quality;
- preference changes.

Learning updates SHOULD define:

- target preference or model;
- evidence;
- confidence;
- decay;
- reversibility;
- recomputation behavior.

The orchestrator SHOULD coordinate learning but SHOULD not embed model-specific learning logic.

## 17. Quality Gates

Major intelligence products SHOULD pass quality gates before publication.

Candidate checks include:

- traceability;
- source and collection completeness;
- confidence;
- duplication;
- contradictions;
- staleness;
- privacy and sensitivity;
- recommendation lifecycle;
- counterpoint coverage;
- delivery authorization.

A gate failure SHOULD:

- block publication;
- quarantine the artifact;
- request a retry or review;
- produce a degraded edition with explicit disclosure;
- preserve a failure record.

The orchestrator SHOULD not silently convert a gate failure into success.

## 18. Escalation

Some findings SHOULD receive additional visibility.

Candidate escalation includes:

- repeated risks;
- repeated outcome failures;
- strategic drift;
- critical opportunity;
- imminent project deadline;
- privacy or safety concern;
- evidence contradiction;
- loss of source coverage.

Escalation SHOULD define:

- trigger;
- evidence threshold;
- priority;
- notification mode;
- expiry;
- acknowledgment;
- follow-up.

Escalation SHOULD not bypass user control or turn advice into action.

## 19. Human Override

Users SHOULD be able:

- to pause workflows;
- to cancel a run;
- to delay or suppress publication;
- to correct context;
- to pin or unpin projects;
- to revise priorities;
- to disable a source or agent;
- to approve or reject a plan;
- to defer or retire recommendations.

Human override SHOULD:

- preserve audit context;
- invalidate or re-run affected steps;
- prevent false completion;
- explain downstream impact.

## 20. Failure Recovery

### 20.1 Collection failure

Continue with available sources and mark the missing context.

Where configured, use clearly labeled last-known context. Do not present stale context as current.

### 20.2 Memory or knowledge failure

Regenerate from valid source artifacts where practical.

If regeneration fails, mark affected memory or knowledge unavailable and continue conservatively.

### 20.3 Agent failure

Continue with remaining agents if the product remains valid.

The orchestrator SHOULD:

- mark missing perspective;
- lower confidence;
- avoid false consensus;
- retry according to policy.

### 20.4 Reasoning failure

Use a source-backed fallback such as an insight-free edition or a last-known valid edition only if the delivery policy permits it.

No unsupported new intelligence should be published.

### 20.5 Delivery failure

Preserve the edition in the archive and isolate channel retries.

A failed email or push provider should not mark the full edition failed.

### 20.6 Feedback or learning failure

Preserve feedback locally and retry according to policy.

No learning update should claim success until its evidence and target are persisted.

## 21. Scheduling and Concurrency

The orchestrator SHOULD support:

- one-time runs;
- recurring schedules;
- event triggers;
- manual runs;
- bounded concurrency;
- run serialization;
- missed-run policy;
- timezone handling;
- no duplicate delivery.

Concurrent workflows SHOULD avoid conflicting updates to:

- memories;
- preferences;
- recommendations;
- editions;
- project state;
- learning models.

Versioned writes or conflict resolution SHOULD be defined.

## 22. Observability

The orchestrator SHOULD record:

- workflow run ID;
- trigger;
- workflow version;
- start and completion time;
- step dependency status;
- agent contributions;
- input and output versions;
- quality gates;
- failures;
- retries;
- delivery status;
- learning updates;
- cancellation or override.

Operational logs SHOULD not expose private context in shared or public interfaces.

## 23. Privacy and Security

Orchestration may coordinate sensitive data.

The system MUST:

- keep core workflows local unless explicitly authorized;
- enforce source and data sensitivity;
- disclose cloud or external agent use;
- isolate credentials;
- prevent private context from public workflows;
- support deletion or invalidation;
- preserve audit access.

The orchestrator SHOULD enforce the principle of least privilege for:

- source access;
- memory retrieval;
- agent tools;
- external delivery;
- external action.

No workflow SHOULD use a broad source or tool scope merely for convenience.

## 24. External Actions

Autonomous investigations MAY be supported.

Consequential external actions MUST remain outside default orchestration unless explicitly authorized.

An action workflow SHOULD define:

- target system;
- requested action;
- authorization;
- reversible or irreversible status;
- confirmation;
- audit trail;
- rollback;
- outcome record.

The platform SHOULD stop at a proposal or approval boundary unless the user or a separately authorized policy permits execution.

## 25. Failure and Partial Delivery

Partial delivery SHOULD be explicit.

An edition MAY be published without optional enrichment if:

- the base edition remains valid;
- missing components are disclosed;
- stale or failed recommendations are not presented as current;
- the quality gates permit degradation;
- the user or policy allows partial delivery.

No partial workflow SHOULD claim the full daily, weekly, or quarterly product.

## 26. Success Criteria

The Chief of Staff Orchestration Layer succeeds when:

- intelligence products are produced reliably;
- systems remain coordinated;
- recommendation and outcome workflows complete;
- feedback drives bounded adaptation;
- agent collaboration improves quality;
- failures remain isolated;
- users retain final authority;
- long-term learning occurs without hidden automation.

Candidate measures include:

- successful workflow completion;
- partial and failed run rate;
- retry and recovery success;
- edition freshness;
- quality-gate pass rate;
- duplicate edition or recommendation rate;
- agent contribution completeness;
- delivery reliability;
- feedback incorporation success;
- unauthorized action count.

## 27. Future Capabilities

Future orchestration MAY support:

- bounded autonomous investigations;
- multi-agent debate;
- strategic simulation;
- scenario planning;
- agent specialization;
- dynamic agent creation;
- repeatable research missions.

All future capabilities MUST preserve:

- advisory boundaries;
- authorization;
- traceability;
- privacy;
- human override;
- failure isolation.

## 28. Architectural Boundaries

The orchestration layer SHOULD remain separate from:

- source-specific collection logic;
- memory and knowledge implementation;
- recommendation data structures;
- final editorial rendering;
- provider SDK details;
- external action execution.

Subordinate specifications SHOULD define:

- workflow schemas;
- trigger and schedule semantics;
- step and dependency contracts;
- retry and idempotency;
- quality gates;
- agent routing;
- observability;
- security and authorization.

## 29. Governance

Changes to workflow stages, triggers, quality gates, priorities, or authorization MUST:

- identify affected vision requirements;
- preserve human authority;
- document privacy and external-action impact;
- preserve audit and retry behavior;
- include migration and rollback;
- define whether existing runs or editions are affected.

The orchestrator MAY evolve scheduling and agent systems. Its role as a coordinated, observable, failure-isolated, and human-controlled intelligence workflow SHOULD remain stable.
