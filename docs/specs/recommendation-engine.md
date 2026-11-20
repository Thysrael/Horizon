# Recommendation Engine Specification

**Status:** Proposed

**Version:** 1.1

**Classification:** Core Intelligence Specification

**Last Updated:** November 20, 2026

**Constitutional parent:** [Daily Intelligence Brief Vision Specification](daily-intelligence-brief-vision.md)

**Related specifications:**

- [Feedback Learning Specification](feedback-learning.md)
- [Editorial Steering Specification](editorial-steering.md)

---

## 1. Purpose

The Recommendation Engine generates, evaluates, tracks, and improves recommendations throughout the Daily Intelligence Platform.

A recommendation is candidate decision support: an action to consider, an investigation to run, a risk to address, an opportunity to examine, a perspective to challenge, or a reflection to undertake. It is not merely a sentence in a brief.

The engine exists to improve decision quality, strategic awareness, and outcome effectiveness. It MUST NOT optimize for engagement, agreement, or popularity.

## 2. Objectives

The Recommendation Engine SHOULD transform observations, patterns, risks, opportunities, and historical intelligence into useful recommendations that help answer:

- what deserves attention;
- what should be investigated;
- what should be challenged;
- what should be prioritized;
- what opportunities are emerging;
- what risks are increasing;
- what assumptions no longer hold.

## 3. Advisory Role

Recommendations are suggestions for consideration. They MUST NOT be treated as commands or autonomous decisions.

The engine MUST distinguish:

- a proposed action;
- an authorized action;
- an implemented action;
- an observed outcome;
- a completed recommendation;
- a superseded recommendation.

The platform MUST NOT execute consequential external actions solely because a recommendation has high confidence or importance.

## 4. Recommendation as a First-Class Artifact

A recommendation MUST persist independently of editions, chat sessions, and presentation containers.

A recommendation SHOULD contain:

- stable recommendation ID;
- title and description;
- primary category;
- confidence;
- importance;
- urgency;
- strategic value;
- challenge or novelty value;
- suggested outcome;
- reasoning summary;
- evidence and provenance;
- producing agents or model configurations;
- current lifecycle state;
- first and latest appearance;
- revisions;
- evaluation and outcome records;
- lineage and supersession links.

An example shape is:

```json
{
  "recommendation_id": "rec_2026-11-20_014",
  "title": "Consolidate overlapping stewardship specifications",
  "description": "Merge duplicate ownership and lifecycle rules into the constitutional specification.",
  "category": "action",
  "confidence": 0.84,
  "importance": 0.91,
  "urgency": 0.34,
  "strategic_value": 0.89,
  "challenge_score": 0.42,
  "status": "proposed",
  "created_at": "2026-11-20T09:30:00Z",
  "revision": 1
}
```

The example is conceptual. Subordinate specifications MUST define ranges, identifiers, validation, and serialization.

## 5. Recommendation Categories

Every recommendation SHOULD have one primary category and MAY have secondary tags.

| Category | Purpose | Examples |
| --- | --- | --- |
| Action | A specific action the user may take. | Consolidate specifications, schedule a review, archive obsolete artifacts. |
| Investigation | A question that requires additional understanding. | Research a technology, validate an assumption, compare architectures. |
| Risk | A potential threat or failure mode requiring attention. | Technical debt, fragmented knowledge, governance gaps. |
| Opportunity | A potential future advantage. | Reusable architecture, an emerging capability, a process improvement. |
| Counterpoint | A credible challenge to existing thinking. | Alternative strategies, contradictory evidence, competing frameworks. |
| Reflection | Deliberate reconsideration of priorities or assumptions. | Revisit long-term direction, review missed opportunities, evaluate progress. |

Categories MUST not be used to obscure a recommendation's underlying claim or evidence.

## 6. Recommendation Structure

### 6.1 Identity

The platform SHOULD preserve:

- recommendation ID;
- created timestamp;
- revision number;
- edition or source session of first appearance;
- current status;
- lifecycle history.

### 6.2 Content

The recommendation SHOULD contain:

- concise title;
- explanation;
- suggested outcome;
- proposed next step;
- scope and assumptions;
- uncertainty and unresolved questions;
- reason for attention now;
- expected horizon.

An expected horizon MUST be separate from urgency. A long-term recommendation MAY have low urgency and high strategic value.

### 6.3 Scoring

The engine SHOULD use independent dimensions.

#### Confidence

Measures whether the recommendation is well supported.

Question: “How likely is this recommendation valid given the available evidence?”

Confidence SHOULD be based on:

- evidence quality;
- source agreement and independence;
- provenance;
- memory support;
- historical accuracy;
- contrary evidence;
- agent consensus.

Agreement among dependent agents or models MUST NOT be presented as independent confidence.

Confidence MUST NOT be calculated from popularity alone.

#### Importance

Measures the potential magnitude of impact if the recommendation is correct.

Question: “How much would this matter?”

#### Urgency

Measures time sensitivity.

Question: “How quickly does this require attention?”

Urgency SHOULD decline as the window for effective action passes unless an explicit external deadline renews it.

#### Strategic value

Measures long-term significance.

Question: “Would this improve future options, judgment, or outcomes?”

#### Challenge score

Measures intellectual and perspective value.

Question: “How strongly does this challenge a current assumption or expose a blind spot?”

Challenge score SHOULD NOT increase for hostility or contrarianism alone.

### 6.4 Scoring constraints

Scores SHOULD be:

- bounded;
- calibrated;
- comparable across recommendations;
- traceable to evidence;
- revised when evidence changes.

A numerical score SHOULD NOT imply greater precision than its evidence supports.

The engine SHOULD prefer an explicit uncertainty interval or qualitative confidence label when the evidence cannot justify a precise score.

## 7. Recommendation Provenance

Every recommendation SHOULD preserve traceability.

The system SHOULD answer:

- why was this recommendation created;
- what evidence supports it;
- what evidence contradicts it;
- which context and memories influenced it;
- which source documents or activities were used;
- which agent or model generated or revised it;
- what assumptions remain unresolved.

Provenance SHOULD include source identity and retrieval or observation time, not only a generated summary.

The system SHOULD distinguish:

- direct evidence;
- inferential context;
- model-generated reasoning;
- stale memory;
- unverified claims.

## 8. Recommendation Sources

Recommendations MAY originate from:

- context and project analysis;
- historical memory;
- knowledge and evidence stores;
- external information;
- agent reasoning;
- source critique;
- feedback outcomes;
- contradiction or counterpoint analysis;
- emerging risk or opportunity detection.

A source SHOULD provide evidence to the recommendation. It SHOULD NOT receive an authority multiplier merely because it is the most recently used or most trusted source.

## 9. Recommendation Lifecycle

The Recommendation Engine SHOULD use explicit lifecycle states.

```text
Generated
    |
    v
Drafted
    |
    v
Published
    |
    v
Viewed
    |
    v
Acknowledged
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

Possible terminal or alternate states include:

- **Rejected:** the user or an authorized process found the recommendation unsuitable;
- **Completed:** the action or investigation reached a defined end;
- **Dormant:** the recommendation remains valid but is not currently active;
- **Expired:** the recommendation's relevance window ended;
- **Superseded:** a newer recommendation replaces it;
- **Invalidated:** evidence disproves or materially weakens the recommendation;
- **Closed:** no further outcome evaluation is expected.

Lifecycle state SHOULD remain historically visible. A superseded state MUST preserve the previous recommendation and its replacement link.

## 10. Persistence and Repetition

Recommendations MUST survive beyond an edition or session.

The platform SHOULD understand:

- when a recommendation first appeared;
- how often it appears;
- whether it is acknowledged or acted on;
- whether it produces value;
- whether it remains unresolved;
- whether it has become stale or superseded.

Repeated presentation SHOULD require a defined reason:

- material context changed;
- the risk or opportunity became more urgent;
- the user requested follow-up;
- the recommendation's outcome remains unresolved;
- the recommendation has distinct lineages or stages;
- the recommendation is being reconsidered as a historical pattern.

Merely repeating the same recommendation because it was previously ignored SHOULD NOT be permitted.

## 11. Recommendation Lineage

Recommendations MAY evolve through a coherent lineage.

Example:

```text
Review memory architecture
        |
        v
Define episodic and durable memory rules
        |
        v
Implement memory retention and deletion policies
        |
        v
Audit recommendation traceability
```

The system SHOULD preserve:

- parent and child recommendations;
- revision relationships;
- supersession reasons;
- merge and split operations;
- stage dependencies;
- shared evidence.

Lineage SHOULD remain distinct from feedback history. A revision is a changed recommendation, not a new feedback event.

## 12. Recommendation Memory

Recommendations SHOULD become memory objects or link to memory artifacts.

This enables future reasoning such as:

- what recommendations were ignored;
- what recommendations succeeded;
- which recommendations repeatedly reappear;
- what themes continue to emerge;
- which assumptions proved incorrect;
- where recommendations led to negative or positive outcomes.

Recommendation memory MUST follow the memory, privacy, retention, and feedback policies of their parent specifications.

Raw publication history SHOULD not be inferred as success, trust, or preference.

## 13. Recommendation Evaluation

Recommendations SHOULD remain evaluable after publication.

Candidate evaluations include:

- helpful;
- not helpful;
- implemented;
- incorrect;
- incomplete;
- stale;
- later;
- already completed;
- superseded;
- outcome positive;
- outcome negative;
- outcome inconclusive.

Evaluation SHOULD identify whether it is:

- explicit;
- inferred;
- outcome-based;
- agent-generated;
- user-corrected.

The engine SHOULD use the precedence and privacy rules in the [Feedback Learning Specification](feedback-learning.md).

## 14. Outcome Tracking

Outcome tracking is the highest-quality learning source, but it is not automatic.

For every outcome, the system SHOULD preserve:

- the linked recommendation;
- outcome statement;
- structured result;
- observed timestamp;
- observation source;
- outcome confidence;
- causal evidence;
- corrective or superseding recommendation;
- whether the result remains provisional.

Example outcome:

```text
Recommendation: Consolidate specifications
Status: Implemented
Result: Repository documentation duplication reduced
Outcome: Positive
Causal evidence: Before-and-after review and repository complexity comparison
```

The engine MUST distinguish:

- correlation;
- temporal association;
- plausible contribution;
- demonstrated contribution;
- proven contribution.

It MUST NOT claim success solely because an action was implemented.

## 15. Deduplication and Consolidation

The engine SHOULD identify duplicate or overlapping recommendations.

Deduplication SHOULD consider:

- equivalent intended outcome;
- shared evidence;
- shared scope;
- category and lineage;
- repeated title or description;
- semantic proximity;
- project context.

Deduplicated recommendations SHOULD:

- preserve all source links;
- identify the canonical recommendation;
- expose merged evidence;
- retain history;
- avoid silently deleting evaluation or outcome records.

The engine SHOULD not merge recommendations merely because they use similar language. A similar action in unrelated projects or horizons SHOULD remain distinct.

## 16. Recommendation Fatigue

The engine SHOULD prevent repeated low-value or stale recommendations.

Retirement SHOULD consider:

- repeated ignoring with no changing context;
- low explicit usefulness;
- negative or inconclusive outcomes;
- expired time sensitivity;
- supersession;
- invalidation;
- reduced evidence confidence;
- project completion or inactivity;
- repeated presentation without outcome.

The platform SHOULD lower prominence gradually and MAY retire a recommendation. Retirement MUST remain visible and reversible.

A low-confidence challenge recommendation SHOULD NOT be retired simply because it was uncomfortable or contradicted existing beliefs.

## 17. Strategic Recommendations

Strategic recommendations MAY persist across months or years.

Examples include:

- architectural migrations;
- knowledge governance initiatives;
- specification stewardship;
- risk reduction programs;
- process modernization;
- major investments.

Strategic recommendations SHOULD:

- maintain long-term milestones;
- reduce urgency where no immediate action is possible;
- remain connected to historical evidence;
- support periodic review;
- avoid continuous resurfacing without new evidence.

## 18. Agent Accountability

Every recommendation SHOULD preserve generating agent or model information.

An agent SHOULD not receive sole credit for a recommendation derived largely from shared context or another agent. The platform SHOULD preserve:

- generating agent;
- contributing agents;
- reviewer or critique agents;
- model configuration;
- source model or provider;
- revision authorship.

Candidate accountability metrics include:

- view and evaluation count;
- acceptance rate;
- implementation rate;
- positive and negative outcome count;
- incorrect or incomplete finding count;
- supersession and invalidation count;
- dissent usefulness;
- sample size and time window.

Agent metrics MUST be advisory and MUST use sufficient evidence. They MUST NOT create a hidden quality monopoly or suppress perspective diversity.

## 19. Quality Metrics

The platform SHOULD track:

- generated;
- published;
- viewed;
- acknowledged;
- evaluated;
- implemented;
- completed;
- rejected;
- incorrect;
- incomplete;
- expired;
- superseded;
- outcome positive;
- outcome negative;
- outcome inconclusive;
- repeated;
- retired.

Metrics MUST include denominator and time window.

Publication counts SHOULD NOT be treated as quality metrics.

Acceptance counts SHOULD not be conflated with outcome quality.

## 20. Privacy and Control

Recommendations MAY reveal sensitive projects, assumptions, beliefs, finances, relationships, or employment concerns.

The system MUST:

- keep core recommendation data local unless cloud processing is explicitly enabled;
- disclose external provider usage;
- support deletion of recommendations and associated derived data;
- support export of recommendation history;
- preserve provenance when a recommendation is corrected;
- prevent private recommendations from entering public or shared output.

The user SHOULD be able to:

- dismiss or defer a recommendation;
- mark it incorrect or outdated;
- link a recommendation to an outcome;
- merge or split it;
- correct its project or source;
- suppress a topic or category without deleting the underlying knowledge.

## 21. Failure Modes

The Recommendation Engine SHOULD detect and mitigate:

### 21.1 Recommendation flooding

Symptoms include too many suggestions, low evaluation rates, and repeated urgency.

Mitigations include:

- severity thresholds;
- edition budgets;
- consolidation;
- urgency recalibration;
- deferred recommendations.

### 21.2 Repetition fatigue

Symptoms include the same recommendation with little contextual change.

Mitigations include:

- recommendation history checks;
- lineage awareness;
- recency and progress checks;
- explicit follow-up only.

### 21.3 False confidence

Symptoms include precise scores based on weak or dependent evidence.

Mitigations include:

- independent evidence checks;
- uncertainty intervals;
- source diversity;
- contradiction visibility;
- confidence decay.

### 21.4 Outcome overclaiming

Symptoms include labeling a recommendation successful without causal evidence.

Mitigations include:

- structured outcome types;
- causal confidence;
- follow-up observations;
- explicit inconclusive state.

### 21.5 Convenience bias

Symptoms include repeatedly recommending easy or familiar actions while neglecting consequential risks.

Mitigations include:

- importance and strategic value separate from urgency;
- active risk and counterpoint review;
- coverage diversity constraints;
- user-visible scoring rationale.

## 22. Success Criteria

The Recommendation Engine succeeds when:

- recommendation quality improves over representative periods;
- acceptance and outcome quality improve;
- users perceive recommendations as valuable rather than distracting;
- useful recommendations remain traceable;
- strategic opportunities are surfaced earlier;
- preventable risks are identified before materialization;
- feedback measurably improves future recommendations;
- repeated low-value recommendations decline;
- successful recommendations are distinguished from merely implemented ones.

Candidate measures include:

| Measure | Interpretation |
| --- | --- |
| Outcome-positive rate | Recommendations with sufficient follow-up that are associated with beneficial outcomes. |
| Implementation follow-through | Implemented recommendations that receive structured outcomes. |
| Repeated recommendation rate | A repeated recommendation remains relevant after accounting for context changes. |
| Invalidation rate | Recommendations disproved or materially weakened by new evidence. |
| Early-risk lead time | Delay between recommendation and material risk outcome. |
| Traceability rate | Recommendations with inspectable evidence and provenance. |
| Dismissal correction rate | User corrections that improve later recommendation quality. |

These metrics require baselines and confidence intervals before they become release gates.

## 23. Architectural Boundaries

The Recommendation Engine SHOULD remain separate from:

- raw activity collection;
- context summarization;
- memory storage;
- editorial ranking;
- final presentation;
- feedback storage;
- external action execution.

Subordinate specifications SHOULD define:

- recommendation schemas;
- category and score validation;
- lineage and deduplication rules;
- lifecycle transitions;
- evaluation and outcome schemas;
- agent attribution;
- ranking interfaces;
- privacy and retention behavior.

## 24. Governance

Changes to recommendation categories, scoring, lifecycle, fatigue rules, or agent metrics MUST:

- identify affected vision requirements;
- document empirical rationale;
- preserve advisory and traceability behavior;
- preserve anti-echo-chamber protections;
- include migration behavior for existing recommendations;
- define rollback or recalibration procedures.

The engine MAY evolve individual models and ranking strategies. Recommendations remain persistent, inspectable, revisable decision-support artifacts unless amended through governance.
