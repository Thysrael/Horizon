---
layout: default
title: Scoring System
---

# Scoring System

A release announcement and an engineering deep dive earn their place for
different reasons. Horizon routes each item to one profile and scores it from
0 to 10 using that profile's rubric. You choose the threshold for each profile
in the runtime configuration.

## Pipeline

1. **Profile resolution** — An explicit source profile is used directly. A
   missing profile or `"auto"` is matched by AI using all loaded `match.md`
   prompts; a candidate array limits that choice to the listed profiles.
2. **Content preparation** — The profile's `content.analysis_max_chars` and
   `content.sampling` control how much article text reaches the model. Sampling
   keeps either the opening or excerpts from the beginning, middle, and end.
   Available comments and engagement metadata are added separately.
3. **Profile analysis** — The selected profile's `analysis.md` prompt evaluates
   the item and returns a score, reason, one-sentence summary, and tags.
4. **Validation and retry** — Responses are parsed as JSON. Failed AI calls are
   retried with exponential backoff. An invalid analysis response gets one repair
   attempt; if it still fails validation, the analysis is stored with a null score.
5. **Profile filtering** — If a runtime threshold is configured for the resolved
   profile, only items meeting it continue. Without a threshold, analyzed items
   continue without score filtering.
6. **Digest selection** — Topic deduplication runs within each profile. Optional
   category quotas and a final item cap select the items to enrich.

Analysis and enrichment concurrency are configured through
`ai.analysis_concurrency` and `ai.enrichment_concurrency`. Result order is
preserved during analysis.

## Profile Rubrics

Each profile defines its own rubric in `analysis.md`. The built-in `tech-news`
profile uses this scale:

| Score | Tier | Description |
| --- | --- | --- |
| 9-10 | Groundbreaking | Major breakthroughs, paradigm shifts, major versions, significant research, or industry-changing announcements |
| 7-8 | High value | Important developments, technical deep-dives, novel approaches, insightful analysis, or valuable tools |
| 5-6 | Interesting | Incremental improvements, useful tutorials, moderate community interest, or useful but non-urgent developments |
| 3-4 | Low priority | Routine updates, common knowledge, shallow treatment, or promotion-dominated content |
| 0-2 | Noise | Spam, off-topic material, trivial updates, or purely promotional content |

Its prompt considers technical depth, novelty, likely impact, source quality,
relevance, concrete evidence, and substantive community discussion. Other
profiles can define different criteria for different content forms.

## Filtering

Thresholds belong to the runtime configuration and are keyed by profile ID:

```json
{
  "processing": {
    "profile_settings": {
      "tech-news": {
        "threshold": 8.0
      }
    }
  }
}
```

`threshold` accepts values from 0 to 10. Items at or above the threshold
continue. To analyze content without dropping it by score, use `null` or omit
the profile's settings:

```json
{
  "processing": {
    "profile_settings": {
      "tech-news": {
        "threshold": null
      }
    }
  }
}
```

A threshold passed to an MCP operation overrides all configured profile
thresholds for that operation. Analysis still produces scores when filtering is
disabled; only score-based filtering is bypassed. Topic deduplication and digest
limits still apply when configured.

Collection and balanced digest settings remain in the runtime configuration:

```json
{
  "collection": {
    "time_window_hours": 24
  },
  "digest": {
    "max_items": 20,
    "category_groups": {
      "ai": {
        "limit": 5,
        "categories": ["ai-news", "ai-tools", "machine-learning"]
      }
    },
    "default_group": "other",
    "default_group_limit": 3
  }
}
```

`collection.time_window_hours` controls the fetch window. `category_groups`
limits each configured category group independently, and `max_items` caps the
merged result. These digest limits run after per-profile filtering and topic
deduplication, but before enrichment.

## Enrichment And Output

Selected items are enriched according to the profile's `enrichment.md` prompt
and block contract. A block can call a tool only when that tool is declared in
the block's `tools` list. The only built-in tool is `web_search`.

For every configured language, Horizon produces a localized title, section
blocks, and references when tool sources are cited. The renderer groups these
artifacts by profile and builds the Markdown briefing without a final AI call.
See [Processing Profiles](profiles.md) for the complete schema and output behavior.
