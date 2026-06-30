# Horizon

## What this is
Horizon is a configurable content aggregation and summarization pipeline that fetches source items, analyzes them with an AI model, filters by importance/category, and emits daily summaries.

## Setup
Use `uv sync` to install the project environment, provide runtime credentials through environment variables rather than config secrets, then run tests with `uv run pytest` before changing behavior.

## How it works
Scrapers emit `ContentItem` records, the orchestrator merges and analyzes them, `StorageManager` persists summaries and auditable run artifacts, and optional delivery integrations send the resulting digest.

## Lessons / gotchas
Keep user-specific source choices, private list IDs, cookies, and curation preferences in local config; keep upstreamable code changes generic, small, isolated, and covered by tests to reduce rebase conflicts.
