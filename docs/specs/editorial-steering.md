# Editorial Steering Specification

**Status:** Proposed

**Version:** 1.1

**Classification:** Core Intelligence Specification

**Last Updated:** November 20, 2026

**Constitutional parent:** [Daily Intelligence Brief Vision Specification](daily-intelligence-brief-vision.md)

**Related specifications:** [Feedback Learning Specification](feedback-learning.md)

---

## 1. Purpose

The Editorial Steering Engine determines which information deserves attention, how strongly it should be emphasized, and how it should be framed within the Daily Intelligence Brief.

Its purpose is to translate current activity, accumulated preferences, historical context, and strategic objectives into advisory editorial guidance. It determines relevance and presentation. It does not determine truth.

The Steering Engine sits after context construction and before recommendation and editorial generation:

```text
Context Processing
        |
        v
Editorial Steering
        |
        v
Ranking and Recommendation
        |
        v
Editorial Framing
        |
        v
Daily Intelligence Brief
```

## 2. Objectives

The Steering Engine SHOULD answer:

“Given everything the platform currently knows about the user, what information may deserve attention today?”

It SHOULD increase relevance without sacrificing novelty, diversity, accuracy, or intellectual challenge.

The engine MUST NOT act as an engagement optimizer or a permanent truth filter.

## 3. Steering Principles

### 3.1 Advisory, not controlling

Steering signals SHOULD guide ranking, enrichment, framing, and recommendation emphasis. They MUST NOT become a hard exclusion rule.

The system SHOULD be able to present a valuable item even when it falls outside:

- the active project list;
- established topic preferences;
- recent activity;
- the user's likely agreement.

The engine MUST preserve an explicit mechanism for discovery and counterpoint.

### 3.2 Recency

Recent activity SHOULD influence steering more strongly than older activity. Current effort is generally a stronger short-term signal than a historic interest.

Recency MUST NOT erase established preferences immediately. A single conversation or implementation session MUST NOT drastically change editorial behavior.

### 3.3 Stability

The steering system SHOULD resist one-event oscillation.

A steering input SHOULD require enough context or confidence to justify a material change. Noise, repeated prompts, and transient browsing activity MUST NOT produce large shifts.

### 3.4 Diversity

The engine SHOULD preserve serendipity, adjacent learning, and constructive challenge.

The distribution of relevance, adjacency, and novelty is a policy input, not a ranking model's automatic result.

### 3.5 Explainability

Steering decisions SHOULD expose enough information for auditing and debugging.

For each edition or ranking pass, the system SHOULD be able to identify:

- context version;
- preference version;
- active mode;
- major steering factors;
- inferred project status;
- decay weights;
- exploration budget;
- material ranking influences.

The user MAY receive a simpler explanation. The system SHOULD retain a more complete operational record.

## 4. Core Inputs

The Steering Engine SHOULD consume the following intelligence artifacts:

| Input | Purpose |
| --- | --- |
| Work context brief | Represents current projects, decisions, open questions, blockers, and recent effort. |
| Preference profile | Represents durable topics, presentation preferences, recommendation patterns, and learned feedback. |
| Recommendation history | Prevents repetition and identifies implemented, ignored, deferred, and recurring recommendations. |
| Historical intelligence | Identifies recurring risks, strategic drift, repeated decisions, and long-term patterns. |
| Source and evidence quality | Adjusts confidence and framing without replacing editorial judgment. |
| Feedback state | Represents explicit and outcome feedback, including confidence and decay. |
| Project and mode state | Identifies pinned projects and whether the edition is focused, exploratory, or strategic. |

Inputs SHOULD be versioned and SHOULD carry timestamps and confidence.

## 5. Work Context Brief

The Work Context Brief is the primary short-term steering artifact.

A brief SHOULD contain:

- active projects;
- technologies or domains in use;
- recent decisions;
- open questions;
- blockers;
- recent deliverables;
- relevant deadlines or milestones;
- confidence and evidence for inferred items;
- time bounds.

An example shape is:

```json
{
  "active_projects": [
    {
      "id": "project_daily_brief",
      "name": "Daily Intelligence Brief",
      "confidence": 0.92,
      "source": "pinned",
      "last_active_at": "2026-11-20T08:30:00Z"
    }
  ],
  "recent_decisions": [],
  "open_questions": [],
  "blockers": [],
  "as_of": "2026-11-20T09:00:00Z"
}
```

The example is conceptual. Subordinate specifications MUST define validation, identifiers, privacy, and retention.

The Work Context Brief SHOULD be compact enough for normal model consumption. Context density SHOULD take priority over completeness. It SHOULD omit stale, low-confidence, or irrelevant observations rather than including every collected activity.

## 6. Steering Sources

Activity source identity SHOULD be preserved, but a source SHOULD contribute evidence rather than receiving a fixed permanent authority.

Examples include:

- repositories and implementation activity;
- AI conversations and planning activity;
- research and discovery sessions;
- notes and specifications;
- repository decisions and blockers;
- explicitly imported project data.

The engine SHOULD avoid using source labels alone to determine importance. It SHOULD consider the meaning, recency, confidence, and relation of the evidence.

## 7. Steering Factors

The following factors MAY influence ranking and editorial emphasis:

| Factor | Intended influence |
| --- | --- |
| Active projects | Elevate directly relevant developments and unresolved project questions. |
| Open questions | Elevate information that may answer or materially revise a current question. |
| Active technologies | Elevate closely related technical or market developments. |
| Recent decisions | Elevate follow-up evidence and contrary information. |
| Preference history | Elevate established valuable topics and presentation patterns moderately. |
| Emerging risks | Elevate risk-related content even when it is outside immediate interest. |
| Repeated topics | Support continuity, but reduce redundant presentation. |
| Historical patterns | Elevate genuine reversals, drift, and recurring concerns. |
| Counterevidence | Elevate credible challenges to active assumptions. |
| Source quality | Adjust confidence and prominence, not the factuality of the claim. |
| Outcome feedback | Elevate methods and perspectives that have demonstrated value. |
| Exploration policy | Reserve attention for adjacent and challenging subjects. |

Steering factors are not a scoring formula in this specification. Subordinate ranking specifications SHOULD define weights, confidence handling, and safeguards.

## 8. Editorial Influence

The Steering Engine MAY influence:

- story ranking;
- headline emphasis;
- summaries;
- context sections;
- related topics;
- recommendation prominence;
- article framing;
- edition ordering;
- discovery and counterpoint selection.

The same story SHOULD be able to receive a different frame according to verified context.

For example, a software architecture article MAY be framed around:

- memory architecture;
- specification stewardship;
- agent systems;
- repository maintainability;
- an active project’s current blocker.

Framing MUST remain grounded in the article and active context. The system MUST NOT imply that source material endorses a project or conclusion not supported by evidence.

## 9. Steering Outputs

The engine SHOULD produce bounded, versioned output structures.

| Output | Purpose |
| --- | --- |
| Priority signals | Relative editorial relevance and confidence. |
| Context signals | Active project and decision awareness. |
| Editorial signals | Framing suggestions and emphasis. |
| Preference signals | Durable preference summaries that may affect selection or presentation. |
| Exploration targets | Subjects or perspectives reserved for controlled discovery. |
| Diversity constraints | Limits that prevent one topic, source, or perspective from crowding out others. |
| Audit metadata | Input versions, factors, decay, and mode. |

The output SHOULD influence editorial selection but SHOULD NOT serve as an opaque substitute for explainable source evidence.

## 10. Exploration Budget

The Steering Engine MUST preserve an exploration budget.

An initial editorial target MAY be:

- 70 percent high relevance;
- 20 percent adjacent interests;
- 10 percent challenge or novelty.

The exact distribution SHOULD be configurable and MUST remain subordinate to accuracy and importance.

The exploration policy SHOULD be applied to article selection and framing. It SHOULD NOT displace necessary coverage of an active project, material risk, or high-impact uncertainty.

The system SHOULD support explicit feedback from the [Feedback Learning Specification](feedback-learning.md) to adjust adjacency and exploration within policy bounds.

## 11. Counterpoint Steering

The engine SHOULD seek opportunities for constructive challenge.

Counterpoint candidates MAY include:

- alternative viewpoints;
- competing frameworks;
- contradictory evidence;
- emerging critiques;
- outcome records that conflict with prior assumptions.

Counterpoint content SHOULD be:

- credible;
- relevant;
- traceable;
- respectful;
- high signal;
- sufficiently contextual for the reader to assess.

The engine SHOULD challenge assumptions without becoming adversarial or manufacturing controversy.

## 12. Project Awareness

The platform SHOULD identify projects from:

- repository activity;
- repeated specification or planning references;
- conversation patterns;
- explicit project declarations;
- durable project memory;
- recently implemented recommendations.

Project inference MUST be probabilistic. The system SHOULD retain the evidence and confidence used to form or update a project.

### 12.1 Manual project control

Users SHOULD be able to:

- pin a project;
- unpin a project;
- merge or rename inferred projects;
- mark a project complete or inactive;
- correct project associations;
- set project priority.

A pinned project SHOULD override weakly inferred project associations for that project. It SHOULD NOT become an absolute exclusion filter for unrelated or contrary information.

### 12.2 Project lifecycle

A project SHOULD have:

- active;
- inactive;
- completed;
- archived;
- superseded.

Status SHOULD affect recency and relevance, not erase historical context. Archived or completed projects SHOULD remain available for longitudinal analysis.

## 13. Time Horizon Management

Different signals MUST decay at different rates.

Candidate horizons include:

| Context type | Candidate horizon | Expected influence |
| --- | --- | --- |
| Immediate activity | 24 to 72 hours | Strong, if confident. |
| Active project | 7 to 30 days | Moderate, with project-specific decay. |
| Learning preference | 30 days to years | Weak to moderate, with feedback-dependent decay. |
| Historical intelligence | Months to years | Weak, persistent, and pattern-oriented. |

Horizon values are initial policy ranges, not universal constants. Subordinate specifications SHOULD document the selected decay function and the conditions for reset or acceleration.

The system SHOULD support:

- recent activity fallback;
- project end or archive decay;
- repeated confirmation;
- contradiction by later evidence;
- explicit feedback reset;
- different decay by confidence and source quality.

## 14. Steering Modes

The platform SHOULD support multiple modes.

### 14.1 Normal

The default balanced mode.

Normal mode SHOULD combine active context, preferences, discovery, and counterpoint within a baseline exploration budget.

### 14.2 Focus

Focus mode SHOULD emphasize current projects and open questions while reducing exploratory allocation.

It MUST NOT eliminate credible risk, counterevidence, or unrelated high-impact developments.

### 14.3 Exploration

Exploration mode SHOULD increase novelty and expand adjacent learning.

It SHOULD remain traceable and SHOULD avoid presenting exploratory content as an active project priority.

### 14.4 Strategic Review

Strategic Review mode SHOULD reduce daily activity weighting and increase:

- historical comparisons;
- recurring risk patterns;
- strategic drift;
- unresolved decisions;
- long-term outcomes.

The current context SHOULD remain visible but SHOULD not dominate all historical analysis.

The selected mode SHOULD be explicit and reversible. It SHOULD NOT persist silently beyond the edition or reporting period unless the user confirms a persistent mode.

## 15. Failure Modes

The Steering Engine SHOULD detect and mitigate:

### 15.1 Over-steering

Symptoms include repetitive articles, reduced discovery, strong echo-chamber behavior, and repeated recommendations.

Mitigations include:

- exploration budget enforcement;
- diversity constraints;
- recommendation history suppression;
- lower short-term context weight;
- explicit challenge selection.

### 15.2 Under-steering

Symptoms include generic editions and weak personalization.

Mitigations include:

- stronger verified context weighting;
- preference-profile fallback;
- focused project context;
- improved context summarization.

### 15.3 Stale context

Symptoms include references to completed work or inactive projects.

Mitigations include:

- project lifecycle updates;
- context decay;
- source freshness checks;
- low-confidence inferences removal.

### 15.4 Activity gaps

Symptoms include insufficient recent activity.

Mitigations include:

- preference-driven fallback;
- conservative historical context;
- exploratory coverage;
- explicit notice that inferred context is sparse.

### 15.5 Context oscillation

Symptoms include rapid shifts due to unrelated conversations or one-time activity.

Mitigations include:

- evidence thresholds;
- context clustering;
- damping;
- recency decay;
- stable project state.

## 16. Observability

The platform SHOULD log steering operations at sufficient detail for debugging and audit.

Operational records SHOULD include:

- edition or ranking run ID;
- context version;
- preference version;
- selected mode;
- work context summary;
- major steering factors;
- input confidence;
- applied decay;
- ranking influence;
- exploration allocation;
- diversity constraints;
- final result or superseding result.

Logs SHOULD be protected according to the sensitivity of the underlying context. Steering logs MUST NOT expose collected personal context in shared or public interfaces.

## 17. Privacy and Control

Steering context MAY reveal sensitive work, beliefs, finances, health, or relationships.

The system MUST:

- keep core steering local unless the user enables a cloud integration;
- disclose external model or service usage;
- support deletion of steering context and derived summaries;
- allow users to inspect and correct active project context;
- support export of user-owned steering state;
- prevent unrelated personal context from entering public or shared output.

The user SHOULD be able to disable:

- inferred project tracking;
- behavioral steering;
- remote steering providers;
- one or more activity sources.

Disabling a source MUST prevent future use in steering unless the user explicitly restores it.

## 18. Success Criteria

The Steering Engine succeeds when:

- edition relevance improves over representative periods;
- useful information outside active projects is discovered;
- feedback quality improves;
- repeated or stale recommendations decline;
- project relevance remains current;
- intellectual diversity is retained;
- echo chambers do not emerge;
- steering decisions can be explained and corrected.

Candidate measurements SHOULD include:

| Measure | Interpretation |
| --- | --- |
| Lead-story relevance | A lead story is materially relevant to active work or meaningful preferences. |
| Adjacent discovery utility | A novel or adjacent item is judged useful by the user. |
| Counterpoint utility | A challenging view adds value or improves a decision. |
| Recommendation diversity | Coverage remains distributed across multiple topics and perspectives. |
| Repetition rate | Similar recommendations recur before the underlying context changes. |
| Steering correction rate | How often inferred context or project state is manually corrected. |
| Preference stability | Whether context shifts remain stable rather than oscillating. |

Success criteria are initial hypotheses and require baselines and confidence intervals before becoming release gates.

## 19. Architectural Boundaries

The Steering Engine SHOULD remain separate from:

- raw activity collection;
- memory and knowledge storage;
- truth determination;
- source acquisition;
- feedback storage;
- final editorial rendering.

Subordinate specifications SHOULD define the Work Context Brief schema, ranking interfaces, project lifecycle, decay policies, context versioning, observability format, and mode behavior.

## 20. Governance

Changes to steering weights, time horizons, exploration budgets, project inference, or mode behavior MUST:

- identify affected vision requirements;
- document the rationale and evidence;
- preserve explainability and reversibility;
- retain anti-echo-chamber behavior;
- include migration behavior for existing context and preferences;
- define a rollback or review mechanism.

The advisory role of the Steering Engine is stable. Ranking implementations and model strategies MAY evolve independently.
