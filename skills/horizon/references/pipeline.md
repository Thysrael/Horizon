# Pipeline operations

## Interface and paths

Run `scripts/horizon_ops.py` with Horizon's project Python. Operation names and
JSON parameters come directly from `src/mcp/service.py`; use `--describe` to read
the installed revision's signature. No separate parameter schema is maintained.

Examples below run from the checkout:

```bash
uv run python skills/horizon/scripts/horizon_ops.py validate_config --params '{"check_env": false}'
uv run python skills/horizon/scripts/horizon_ops.py fetch_items --params '{"hours": 24, "sources": ["rss"]}'
```

For custom configurations, include `"config_path": "/absolute/data/config.json"`.
Paths supplied through the helper are checkout-relative or absolute. When a stage
has a `run_id` and no explicit config path, the helper recovers it from run
metadata. An explicit config path overrides that recovery. Keep the checkout
consistent with the run being resumed.

The default run store is `<checkout>/data/mcp-runs`; `--runs-root` can select
another store. Continue using that store on subsequent calls and remember that
an MCP server may be using its own default store. Stage read operations do not
require a working config or API key.

For shell quoting portability, put parameters in a JSON file:

```bash
uv run python skills/horizon/scripts/horizon_ops.py fetch_items --params-file /absolute/fetch-params.json
```

The helper uses the native service's storage rule: archived summaries are in
`summaries/` beside the active config. The normal CLI instead separates
`--config` from `--data-dir`. Consult `docs/configuration.md` Configuration Paths
when switching interfaces.

## Generate or reuse a digest

1. For a read request, look for an existing matching digest using `list_runs`,
   `get_run_meta`, and `get_run_summary`, or inspect persistent summaries. Check
   its date, language, config, and time window before presenting it as current.
2. For a new run, call `validate_config`. Inspect `missing_env`, `warnings`, and
   `unknown_sources`. This checks selected environment names, not connectivity
   or every optional provider credential. Ollama may use an empty `api_key_env`;
   consult its provider configuration rather than requesting an empty-name key.
   For `openai-chatgpt`, inspect `ai.auth.plan_usage` and follow `docs/chatgpt.md`
   for login and a completed-inference check. Stop on account or plan-limit errors
   instead of retrying the batch or replacing the configured billing method.
3. Use `run_pipeline` for a configured, understood setup. For first-run diagnosis
   or tuning, use the separate stages in the table below and inspect each result.
4. Set the requested `hours` explicitly when it differs from the native default.
   Ensure `ai.languages` includes the requested enrichment languages. The
   `languages` argument on `run_pipeline` only selects summary rendering.
5. Read the actual generated summary, not just its preview. Report counts,
   coverage gaps, original links, and the file path.

| Operation | Example native parameters | Result to inspect |
| --- | --- | --- |
| `fetch_items` | `{"hours":24,"sources":["rss","hackernews"]}` | `run_id`, `fetched`, `fetch_status`, `fetch_report` |
| `score_items` | `{"run_id":"RUN_ID"}` | `score_distribution`, including `unscored` |
| `filter_items` | `{"run_id":"RUN_ID","threshold":7.0}` | `kept`, dedup/removal counts, group counts |
| `enrich_items` | `{"run_id":"RUN_ID"}` | `status`, `failed`, `failed_ids`, artifact presence |
| `generate_summary` | `{"run_id":"RUN_ID","language":"zh","source_stage":"enriched"}` | `summary_path`, `items_used`, source stage |
| `get_run_stage` | `{"run_id":"RUN_ID","stage":"scored","max_items":5}` | Representative items; `truncated` means the response is a sample |
| `get_run_summary` | `{"run_id":"RUN_ID","language":"zh"}` | Complete Markdown |

Replace `RUN_ID` with the returned value. Use the configured per-Profile
thresholds when no one-off override is requested. Filtering may invoke AI topic
deduplication or discussion expansion; it is not necessarily an offline stage.

## Interpret failures and continue

`ok: true` and exit 0 mean the method returned. They do **not** assert that every
source, model call, or environment check succeeded. The helper preserves native
results, just like MCP. An exception produces `ok: false` and exit 1; argument
syntax errors use argparse's exit 2.

- **Empty fetch:** distinguish no matching entries from reported fetch failures.
  Read source diagnostics before changing thresholds. `run_pipeline` cannot
  score an empty input; locate its new run with `list_runs` if it stops there.
- **Nothing selected:** inspect scores, thresholds, category caps, and routing.
  Skip enrichment for an empty filtered stage; render it to report the outcome.
- **Partial enrichment:** report failed items and inspect language artifacts.
  For total enrichment failure, the service removes the enriched stage; an
  explicit render from `filtered` yields a reduced digest. Label that result.
- **Changed threshold/quota:** reuse `scored`, then filter, enrich, and render.
- **Changed rubric/routing:** rescore `raw`, then regenerate downstream stages.
- **Changed enrichment prompt/languages:** reuse `filtered`, then enrich/render.
- **Changed section order:** render existing localized artifacts again.

Saving an upstream stage invalidates downstream files and summaries. Read any
comparison outputs first. `get_run_meta` and stage availability establish what
can actually be reused; config files themselves are not immutable snapshots.

Use `save_to_horizon_data: true` on summary generation or the full pipeline to
archive the digest for history search. This is a local archive export, not email,
Webhook, WeChat, or website deployment. For normal scheduled delivery, use the
`horizon` CLI and the existing delivery guide.
