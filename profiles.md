---
layout: default
title: Processing Profiles
---

# Processing Profiles

News needs context. An engineering deep dive needs an explanation of the solution.
A profile tells Horizon what to look for, how to judge it, and what to write—using
Markdown prompts and a JSON block definition.

Profiles define reusable editorial rules. Your sources, AI model, score thresholds,
digest limits, languages, and delivery channels stay in the runtime configuration.
Each item is routed to one profile; a candidate list lets AI choose among several,
rather than process the item with all of them.

## Built-in Profiles

| Profile | What it looks for | What it produces |
| --- | --- | --- |
| `tech-news` | Releases, incidents, research results, and technology-industry developments | Summary and background; impact and community discussion when useful |
| `tech-blog` | Engineering deep dives, tutorials, investigations, and retrospectives | Background, solution, and takeaways |
| `finance-news` | Markets, macroeconomics, company finance, and economically material policy | Summary and background; direct impact when useful |
| `ai-creator` | AI developments with potential for content creation | Summary; timely hooks, content angles, and community discussion when useful |

Start with a built-in profile, then adjust its prompts or blocks to match your reading needs.

## Directory Layout

Each profile lives under `profiles/<id>/` with the same four-file layout:

```text
profiles/tech-blog/
|-- profile.json
|-- match.md
|-- analysis.md
`-- enrichment.md
```

- `profile.json` defines the profile contract.
- `match.md` tells automatic routing what content belongs to the profile.
- `analysis.md` defines the first-pass analysis and scoring rubric.
- `enrichment.md` defines how to write the localized output blocks.

## Try a Different Reading Style

For an engineering feed, use `tech-blog` to extract the problem, solution, and
lessons. Add an entry like this to `sources.rss`:

```json
{
  "name": "NVIDIA CUDA Technical Blog",
  "url": "https://developer.nvidia.com/blog/tag/cuda/feed/",
  "profile": "tech-blog",
  "content_extractor": "trafilatura"
}
```

`trafilatura` is included in the base install. It fetches the article body;
extraction failures fall back to the feed excerpt. The blog profile uses larger
input budgets and head-middle-tail sampling for long articles.

To create your own profile:

1. Copy a profile directory and give its `profile.json` a unique `id` and name.
2. Edit `match.md` and `analysis.md` to describe the content and evaluation criteria.
3. Set the output blocks in `profile.json` and their writing instructions in `enrichment.md`.
4. Set a source's `profile` to your new ID, then tune its threshold under `processing.profile_settings`.

No Python changes are needed when using the existing block type and tools. Each
new profile also joins the candidates for unrestricted automatic routing.

## Contributing a Profile

A profile is a reusable editorial policy for a content domain, not a user
account, source list, or collection of personal interests. It tells Horizon:

1. which items belong to the domain (`match.md`),
2. how to evaluate and score them (`analysis.md`), and
3. which content blocks to produce and how to write them (`profile.json` and
   `enrichment.md`).

To contribute a built-in profile, add `profiles/<id>/` with those four files and
open a focused pull request. No Python changes are normally required.

Before submitting, check that the profile:

- covers a clear content domain that is useful to more than one source list or
  individual user,
- has a meaningful routing, evaluation, or output difference from existing
  profiles,
- states both what belongs and what does not belong in `match.md`,
- defines a concrete 0-10 rubric in `analysis.md`,
- keeps generated blocks specific, non-overlapping, and grounded in supplied
  content or declared tools,
- contains no credentials, private sources, or user-specific thresholds, and
- passes `uv run pytest tests/test_profiles.py tests/test_prompting.py -q`.

Built-in profiles are loaded as automatic-routing candidates, so maintainers may
ask contributors to narrow ambiguous matching rules or clarify overlap before a
profile is merged.

Configure discovery in `data/config.json`:

```json
{
  "processing": {
    "profiles_dir": "profiles",
    "default_profile": "tech-news",
    "profile_settings": {
      "tech-news": {
        "threshold": 7.0,
        "topic_dedup": true
      },
      "tech-blog": {
        "threshold": 4.0,
        "topic_dedup": false
      }
    }
  }
}
```

`default_profile` must name a loaded profile. Horizon fails to start if no
profiles are found or the default does not exist.

## Profile Schema

```json
{
  "id": "tech-news",
  "name": "Technology News",
  "display_names": {
    "zh": "科技新闻"
  },
  "match": "match.md",
  "analysis": "analysis.md",
  "content": {
    "analysis_max_chars": 1000,
    "enrichment_max_chars": 8000,
    "sampling": "prefix"
  },
  "enrichment": {
    "prompt": "enrichment.md",
    "blocks": [
      {
        "id": "summary",
        "type": "section",
        "tools": [],
        "primary": true
      },
      {
        "id": "background",
        "type": "section",
        "tools": ["web_search"]
      },
      {
        "id": "community_discussion",
        "type": "section",
        "tools": [],
        "optional": true
      }
    ]
  }
}
```

| Field | Description |
| --- | --- |
| `id` | Unique profile ID. It starts with a lowercase letter and may contain lowercase letters, digits, `_`, and `-`. |
| `name` | Human-readable name used in the matching catalog. |
| `display_names` | Optional language-keyed names used as digest section headings. |
| `match` | Profile-relative path to the matching prompt. |
| `analysis` | Profile-relative path to the analysis prompt. |
| `content` | Input budgets and long-content sampling strategy for AI stages. |
| `enrichment.prompt` | Profile-relative path to the enrichment prompt. |
| `enrichment.blocks` | Contract for localized output blocks. At least one block is required. |

Block IDs use the same format as profile IDs and must be unique within a
profile. The only supported block `type` is `"section"`. Blocks are required by
default; set `optional` to `true` when they may be omitted.

| Block field | Description |
| --- | --- |
| `id` | Unique block ID within the profile. |
| `type` | Must be `"section"`. |
| `tools` | Tools allowed for this block. Declare it on every block; use `[]` when none are allowed. |
| `optional` | Whether output may omit the block. Defaults to `false`. |
| `primary` | Render this required block directly below the item title without a block heading. At most one block may be primary. Defaults to `false`. |

Prompt paths cannot escape their profile directory. Unknown fields are rejected
in profile JSON.

## Source Routing

Set `profile` on a source entry to route its items directly:

```json
{
  "sources": {
    "rss": [
      {
        "name": "Example",
        "url": "https://example.com/feed.xml",
        "profile": "tech-news"
      }
    ]
  }
}
```

Set `profile` to an array to restrict automatic matching to a candidate subset:

```json
{
  "channel": "zaihuapd",
  "profile": ["tech-news", "finance-news"]
}
```

Routing follows these rules:

1. An explicit profile ID uses that profile and skips AI matching.
2. A missing `profile` or `"auto"` invokes AI matching against every loaded
   profile's `match.md`.
3. A non-empty profile array invokes AI matching only against those candidates.
4. Unknown, duplicate, blank, or `"auto"` entries in a candidate array are errors.
5. If candidate matching fails, Horizon uses `processing.default_profile` when
   it is a candidate, otherwise the first candidate. Unrestricted matching falls
   back to `processing.default_profile`.

All source types support profile routing. For sources with nested entries, put
`profile` on the item-producing configuration, such as a GitHub entry, RSS feed,
Reddit subreddit or user, or OpenBB watchlist. Top-level single configurations,
such as Hacker News, Twitter, OSS Insight, GDELT, and Google News, carry the
field directly.

## Analysis

After routing, Horizon sends the item to the selected profile's `analysis.md`
prompt. A successful analysis contains a 0-10 score, a reason, a one-sentence
summary, and tags. A failed analysis may be stored with a null score. The profile
owns the rubric, so profiles can evaluate different content forms by different
standards.

## Filtering

Filtering is a user preference configured by profile ID under
`processing.profile_settings`:

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

`threshold` must be between 0 and 10. Horizon keeps items whose analysis score
is greater than or equal to that threshold. Set it to `null` or omit settings for
a profile to bypass score filtering. An MCP threshold supplied for a single
operation takes precedence over these configured values.

The top-level `collection` configuration controls `time_window_hours`. Optional
balanced digest limits such as `category_groups` and `max_items` belong to the
top-level `digest` configuration and run after profile filtering and topic
deduplication.

## Enrichment Blocks And Tools

`enrichment.blocks` defines the exact block IDs available to output.
Required blocks must be present; optional blocks can be omitted when they add no
useful content. Generated output cannot contain unknown or duplicate blocks.

Tools are allowed per block through its `tools` array. The only built-in tool is
`web_search`, and a block may use it only when that block explicitly declares
`"tools": ["web_search"]`. Use an empty array for blocks that need no tools.
Unknown tools are rejected when the enricher is initialized.

Tool planning receives each block's required or optional status. For required
blocks with tools, the prompt asks the model to use a tool unless the source
already provides enough evidence. A search is not guaranteed; tool failures do
not make a required block optional.

Search-backed statements cite tool results through source references. Horizon
rejects references that were not returned by a tool call.

## Content Selection

Profiles can control how much source content each AI stage receives:

```json
{
  "content": {
    "analysis_max_chars": 16000,
    "enrichment_max_chars": 24000,
    "sampling": "head-middle-tail"
  }
}
```

`sampling` accepts `"prefix"` or `"head-middle-tail"`. Prefix sampling preserves
the compact behavior used by news profiles. Head-middle-tail sampling keeps the
opening, a middle excerpt, and the conclusion of long-form content. Both limits
must be between 500 and 100000 characters.

## Topic Deduplication

AI topic deduplication is also a runtime preference. Disable it for profiles
where different treatments of the same subject should remain separate:

```json
{
  "processing": {
    "profile_settings": {
      "tech-blog": {
        "topic_dedup": false
      }
    }
  }
}
```

`topic_dedup` defaults to `true` when it or the profile's settings are omitted.

Topic deduplication runs within each resolved profile. Disabling it does not
disable the orchestrator's earlier URL deduplication: items with the same
normalized URL and requested profile or candidate list are still merged before
analysis. Different requested routes stay separate at that stage; individual
scrapers may also deduplicate their results before routing.

## Localized Output

For each language in `ai.languages`, enrichment produces a localized artifact
with:

- a title;
- the profile's required and applicable optional section blocks; and
- cited external sources referenced by those blocks.

Artifacts generated for `zh` are normalized to Simplified Chinese before they
are stored and rendered, including older artifacts read during rendering.

The Markdown briefing renders a block marked `primary` directly below the item
title and before the source line, without a redundant block heading. Profiles
without a primary block show the source first and then render every block under
its bold localized title on the same line as its content. External references
follow the blocks when used. Items
are grouped by Profile: the briefing title is H1, localized Profile names are H2
sections, and items are H3 headings. Set `digest.profile_order` to control the H2
section priority. When this list is non-empty, loaded Profiles omitted from it
are appended in discovery order; unknown or duplicate IDs are rejected. With an
empty or omitted list, sections follow the order in which profiles first appear
in the selected items. The final Markdown is rendered by code, without another
AI summarization call.
