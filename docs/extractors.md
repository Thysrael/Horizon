---
layout: default
title: Content Extractors
---

# Content Extractors

Extractors fetch and parse the full text of a linked article, replacing the brief excerpt a feed normally provides. They are opt-in per RSS source via the `content_extractor` field.

## How it works

1. The RSS scraper parses the feed as usual.
2. For each entry whose source has `content_extractor` set, the scraper calls the named extractor with the entry's link URL.
3. If the extractor returns text, it replaces the feed-provided content. If extraction fails for any reason, the feed content is used as a fallback.

Extractors are defined under the top-level `extractors` section of `config.json` and referenced by name from individual RSS sources.

## Configuration

```json
{
  "extractors": {
    "full-text": {
      "type": "trafilatura",
      "favor_precision": true
    }
  },
  "sources": {
    "rss": [
      {
        "name": "Simon Willison",
        "url": "https://simonwillison.net/atom/everything/",
        "content_extractor": "full-text"
      }
    ]
  }
}
```

Each entry under `extractors` is a named extractor configuration. The `type` field determines the implementation. An RSS source references an extractor by its name via `content_extractor`.

Using a type name directly (e.g. `"content_extractor": "trafilatura"`) also works — each type is pre-registered as a default extractor with default settings, so no explicit entry in `extractors` is required for the basic case.

## Extractor types

### `trafilatura`

**File**: `src/extractors/trafilatura.py`

Uses the [trafilatura](https://trafilatura.readthedocs.io/) library to extract main article text from HTML. Requires the `trafilatura` optional dependency:

```bash
# Local
uv sync --extra trafilatura

# Docker
docker compose build --build-arg EXTRAS=trafilatura horizon
```

**Config fields**:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `type` | string | `"trafilatura"` | Extractor type identifier |
| `favor_precision` | bool | `false` | Prefer fewer but more relevant results |
| `favor_recall` | bool | `false` | Prefer more results, accepting some noise |

`favor_precision` and `favor_recall` are mutually exclusive. Setting both has undefined behavior (trafilatura's own default applies).

**Timeout and retry**: the extractor reuses the shared `httpx.AsyncClient` and inherits whatever timeout and connection settings are configured on it.

## Adding a new extractor type

1. Add an entry to `ExtractorType` in `src/models.py`.
2. Add a config class (e.g. `MyExtractorConfig`) with `type: Literal[ExtractorType.MY_TYPE]`.
3. Add the new config to the `ExtractorConfig` union in `src/models.py`.
4. Implement the class in `src/extractors/my_extractor.py`, subclassing `BaseExtractor`.
5. Export it from `src/extractors/__init__.py`.
6. Add a `case MyExtractorConfig()` branch in `_build()` in `src/extractors/registry.py`.
7. Add a default entry to `_DEFAULTS` in `src/extractors/registry.py`.
