# Horizon MCP

Horizon includes a built-in MCP server that exposes the native Horizon pipeline as staged tools and read-only resources.

The MCP layer does not reimplement Horizon business logic. It reuses the existing fetch, score, filter, enrich, and summarize modules from the main codebase.

## Tools

| Tool | Description |
| --- | --- |
| `hz_validate_config` | Validate Horizon config and required environment variables |
| `hz_fetch_items` | Fetch and deduplicate content into the `raw` stage |
| `hz_score_items` | Score items from a stage into `scored` |
| `hz_filter_items` | Filter scored items into `filtered` |
| `hz_enrich_items` | Enrich filtered items into `enriched` |
| `hz_generate_summary` | Generate markdown from a stage |
| `hz_run_pipeline` | Run fetch -> score -> filter -> enrich -> summarize |
| `hz_list_runs` | List recent run artifacts |
| `hz_get_run_meta` | Read metadata for a run |
| `hz_get_run_stage` | Read items from a run stage |
| `hz_get_run_summary` | Read a generated summary |
| `hz_get_metrics` | Read in-memory server metrics |

## Resources

- `horizon://server/info`
- `horizon://metrics`
- `horizon://runs`
- `horizon://runs/{run_id}/meta`
- `horizon://runs/{run_id}/items/{stage}`
- `horizon://runs/{run_id}/summary/{language}`
- `horizon://config/effective`

## Install and Start

```bash
uv sync
uv run horizon-mcp
```

| Option | Default | Description |
|--------|---------|-------------|
| `-l`, `--log-level LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL) |

The server runs over stdio and is intended to be launched by an MCP client. Stdout is reserved for the MCP protocol; progress, logs, warnings, and errors are written to stderr through one shared Rich console.

### Workspace and application version

The server uses the Horizon version that launched `horizon-mcp`. `horizon_path`
(or `HORIZON_PATH`) selects the workspace for configuration, Profiles, and
credentials; it does not switch the running Python modules. An explicitly
selected workspace needs to be an existing directory, but does not need to
contain Python source. A missing explicit path is an error.

The default config is `<workspace>/data/config.json`. Relative Profile paths are
resolved from the workspace. To use another Horizon code revision, launch the
server with that revision's environment.

## Run Artifacts

Each run writes artifacts under `data/mcp-runs/<run_id>/`:

- `meta.json`
- `raw_items.json`
- `scored_items.json`
- `filtered_items.json`
- `enriched_items.json`
- `summary-<lang>.md`

Fetch responses and run metadata include `fetch_status` and `fetch_report`.
Source reports preserve named failures, including partial failures within a
source type (for example, one unavailable RSS feed among several working feeds).

## Design Principles

1. Keep Horizon as the single source of business logic.
2. Preserve staged re-entry so a run can continue from intermediate artifacts.
3. Default to no extra side effects unless explicitly requested.

## Client Setup

See [integration.md](integration.md).
