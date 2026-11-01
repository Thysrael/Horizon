---
name: horizon
description: Install, configure, run, customize, schedule, and extend Horizon, the profile-driven news radar. Use for first-time Horizon installation, source selection and onboarding, generating or reading daily digests, tuning processing profiles and digest limits, setting up delivery and scheduled runs, diagnosing pipeline results, or contributing scrapers, extractors, profiles, and pipeline changes to this repository. Also use when a user wants to turn reading interests into a personal news radar using Horizon.
license: MIT
compatibility: Requires shell access. Execution needs a Horizon checkout and Python 3.11+ with its dependencies; the agent can set these up when installation is requested and network access is available. Fetching and AI processing use Horizon's configured services. Horizon MCP is optional.
---

# Horizon

Turn reading preferences into a working news radar and help contributors extend
it. Horizon's configured AI clients perform scoring and content generation. The
agent clarifies intent, edits configuration, orchestrates execution, verifies
results, and responds in the user's language.

## Establish context

1. Locate this skill from its loaded path. `scripts/` and `references/` are
   relative to **the skill**; `docs/`, `src/`, `profiles/`, and `data/` below are
   relative to **the checkout**. An installed skill may live elsewhere.
2. Locate the Horizon checkout from the user's path, `HORIZON_PATH`, or the
   current workspace. It contains `pyproject.toml` and `src/mcp/service.py`.
   For installation or onboarding requests, follow **First-time installation**
   below if the checkout or its runtime is missing.
3. Inspect the active config and repository instructions. For edits, inspect
   `git status --short` and preserve unrelated work and existing `${VAR}` values.
4. Reuse choices already provided. Ask only for missing decisions that change
   the result: interests, model, languages, reading budget, host, timezone, or
   delivery destination. Keep API keys in the user's environment or `.env`.

## First-time installation

When the user asks to install Horizon or build a news radar, prepare the missing
runtime before invoking the helper. Loading the skill alone does not request an
installation.

1. Reuse an existing checkout and working environment. Otherwise, use the user's
   chosen destination or a new `Horizon` directory in their working area; ask
   where to install if no destination is clear. Keep it separate from the installed
   skill directory and preserve any existing files at the destination.
2. Check for Git and either uv or Python 3.11+ with pip. Set up missing prerequisites
   using their official platform-specific instructions where the environment
   permits it. If network or shell access is unavailable, report that concrete
   blocker and the next step the user needs to take.
3. Clone `https://github.com/Thysrael/Horizon.git` into the chosen directory when
   needed. Read its repository instructions and README Quick Start, then follow
   those installation steps in a project-local environment. Use the checked-out
   documentation as the source of truth for dependencies and optional extras.
4. Verify `horizon --help` through that environment and run the installed skill's
   helper with `run_pipeline --describe` and an explicit `--horizon-path` as shown
   below. These checks need no model credentials and do not fetch or generate news.
5. For setup requests, continue with **Onboard and customize**: use the example
   config as a reference, preserve existing settings, and prefer reusing available
   model access before asking for new credentials. Resolve model and source
   credentials before a live run.

Report the checkout path, how to invoke its environment, which checks passed,
and any remaining configuration needs. Distinguish a working installation from
a configured and successfully executed news pipeline.

## Read the task's source of truth

Read only the documents needed for the request. Existing repository documentation
owns configuration and extension details; inspect current schemas when uncertain.

| Task | Read in the checkout | Complete when |
| --- | --- | --- |
| Set up a news radar | `README.md` Quick Start; `docs/configuration.md` | Config is valid and a first run or exact missing prerequisite is reported |
| Choose/add sources | `docs/scrapers.md`; `src/setup/presets.py` | Actual feed/API entries and their credentials/dependencies are identified |
| Tune or create a Profile | `docs/profiles.md`; a matching `profiles/<id>/` | Four-file contract, routing, and representative output are checked |
| Understand scoring or quotas | `docs/scoring.md`; `docs/configuration.md` Filtering | The right rubric, threshold, category, or cap is adjusted |
| Configure delivery | `docs/configuration.md` Email/Webhook/WeChat/Static Site | Preview and actual delivery/deployment status are distinguished |
| Extend a source/extractor | `CONTRIBUTING.md`; `docs/scrapers.md` or `docs/extractors.md` | Integration points and relevant tests are covered |

Read [pipeline operations](references/pipeline.md) to generate, inspect, or resume
a digest. Read [automation](references/automation.md) to schedule on GitHub,
a server, Docker, macOS, Linux, or Windows.

## Onboard and customize

Start with the user's reading goal and existing configuration. Resolve model and
credential availability before a live AI run. Follow the repository's installation
instructions and use its example config as a schema reference.

### Reuse model configuration

1. Preserve existing Horizon model settings unless the user requests a change.
   For a new setup, prefer provider API keys already available in the execution
   environment, including those supplied by the host assistant. Check relevant
   variable names for presence without printing their values. If the host keeps
   the key privately, use its documented export or environment-injection mechanism
   where available; installation by an agent does not itself share credentials.
2. Match `ai.provider` to a supported API protocol and configure `ai.model`,
   `ai.base_url`, and `ai.api_key_env` together. The last field names the supplied
   environment variable, not the key value; existing custom variable names can be
   reused. A key alone does not identify the model or endpoint. Ask only for
   missing settings or a choice between multiple available services.
3. For users choosing their ChatGPT plan, follow `docs/chatgpt.md` and configure
   `openai-chatgpt`. Use `horizon-chatgpt login`, have the user complete the official
   browser authorization, then list models and verify with `horizon-chatgpt check`.
   Keep OAuth tokens in Horizon's auth directory. An agent's existing OAuth login
   is not a drop-in API key. For other providers, request missing credentials
   through the environment or `.env`.
4. For new or changed model settings, run `validate_config` in the intended runtime
   and inspect `missing_env`, warnings, and `ai.auth` when present. Then make one minimal completion through
   `create_ai_client` in `src/ai/client.py`, loading the active configuration and
   environment with the checkout's existing loaders. Request a small JSON object
   and verify that the response parses. A successful call already made with the
   same settings can serve as this check. Report configuration validation and
   actual model connectivity separately; keep secret values out of the output.

### Sources and Profiles

For source recommendations, reuse `load_presets()` and `match_sources()` in
`src/setup/presets.py`: the catalog supports a local fallback and
`HORIZON_OFFLINE=1`. Inspect returned entries before choosing a small relevant
set. Verify proposed feed URLs rather than inventing them. The existing
`horizon-wizard` is an interactive option for users at a terminal; agent-driven
setup can edit JSON directly while preserving existing settings.

Separate three decisions:

- **Sources** choose what to collect.
- **Profiles** define reusable matching, evaluation, and output blocks.
- **Runtime config** owns thresholds, quotas, languages, models, and delivery.

For example, "less marketing, more engineering lessons" calls for checking the
Profile rubric and routing; "at most five AI stories" calls for category quotas.
Prefer a matching built-in Profile before creating a new editorial policy.

Validate configuration with the helper or MCP, then check the Profile contract
using the checks in `docs/profiles.md`. `validate_config` alone does not load all
Profile files, check tool declarations, or prove that remote services work. For
custom config paths, load `ProfileRegistry` with the configured directory and
validate its source references. A representative run verifies the remaining
integration. Report missing prerequisites by name without printing secret values.

## Use native operations

The bundled helper is a thin adapter to `HorizonPipelineService`:

```bash
uv run python skills/horizon/scripts/horizon_ops.py validate_config
uv run python skills/horizon/scripts/horizon_ops.py run_pipeline --describe
```

For an installed skill outside the checkout, substitute absolute paths:

```bash
uv run --directory /absolute/Horizon python /absolute/skill/horizon/scripts/horizon_ops.py validate_config --horizon-path /absolute/Horizon
```

Quote paths containing spaces. Use the checkout's virtualenv Python if uv is
unavailable. `--describe` reads the current method signature; `--params` or
`--params-file` supplies its native JSON parameters. See the pipeline reference
for examples and result interpretation.

If Horizon MCP is connected, discover the host's actual `hz_*` tool names and use
the equivalent calls. Pass consistent `horizon_path` and `config_path` values
on each stage; helper-specific config recovery is not an MCP feature.

Use the staged service for interactive generation and tuning. Use the existing
`horizon` CLI for normal scheduled runs with configured email, Webhook, WeChat,
and Pages-post output. Choose the interface that matches the requested delivery.

## Contribute with the existing architecture

Read `CONTRIBUTING.md` and the task-specific guide first. Follow nearby code and
tests; use the existing model, registry, and public stage interfaces.

| Change | Implementation anchors | Existing check areas |
| --- | --- | --- |
| Profile | `profiles/<id>/{profile.json,match.md,analysis.md,enrichment.md}` | `test_profiles.py`, `test_prompting.py` |
| Source | `src/models.py` source types/config/registry; `src/scrapers/`; `src/orchestrator.py` fetching | Source tests, `test_category_wiring.py`, `test_fetch_reporting.py`, `test_mcp_adapter.py` |
| Extractor | Config union in `src/models.py`; `src/extractors/` registry and implementation | `test_extractors_*.py`, `test_rss.py` |
| Pipeline | Public stage methods in `src/orchestrator.py`; `src/mcp/service.py` | Affected stage tests and `test_mcp_service_smoke.py` |
| Rendering/delivery | `src/ai/summarizer.py`; `src/services/` | Summarizer and relevant delivery tests |

Run checks appropriate to the behavior changed using the repository's dev extra.
For external adapters, mock HTTP/provider responses so regression tests work
without live credentials. Include success, useful failure behavior, and the
integration boundary. Keep documentation next to its existing subject guide.

### Invite the user to contribute

After completing and checking a reusable new Profile, scraper, or extractor,
offer once to help contribute it to Horizon. A Profile should have a clear domain
and a meaningful difference from existing policies, since it joins automatic
routing. Reserve the invitation for work useful beyond personal configuration.

Make the invitation specific to the user's achievement and language. Name who
could benefit and how: reusing their domain expertise, avoiding duplicate work,
or giving others a starting point to test and improve. Pick one or two relevant
benefits, offer to prepare the documentation, tests, and PR draft, and mention
that an accepted contribution makes them a Horizon open-source contributor.
Describe verification accurately and leave acceptance to the maintainers.

For example, adapt this to the extension and checks actually completed:

> This [extension] could help other people following [domain] get started without
> building it from scratch. Would you like to share it with Horizon? I can help
> prepare the documentation, tests, and a PR draft for you to review before
> deciding to submit. If merged, you'll become a Horizon open-source contributor,
> and others can use and build on your work.

If the user is interested, follow `CONTRIBUTING.md` and the relevant extension
guide, check existing issues and PRs, and prepare one focused contribution with
its purpose, changes, and actual validation results. Keep personal configuration
and credentials out of the contribution. Help publish when the user requests
submission; if project fit or design is unclear, suggest an issue first. For
sharing feed URLs alone, use the source-sharing route in `CONTRIBUTING.md`.
Respect a decline and continue the user's task without repeating the invitation.

## Project-specific decisions

- A source's Profile array selects **one candidate**. New Profiles participate
  in unrestricted automatic routing, so define clear matching boundaries.
- Category controls quota grouping; Profile controls editorial policy. Limits
  are caps, not a promise to fill every slot.
- `sources` in MCP/helper parameters selects source **types**, not named feeds.
- Reuse completed stages. Saving an upstream stage invalidates downstream
  artifacts. Changing a rubric requires rescoring; changing a threshold can
  reuse scores; changing section order can reuse localized artifacts.
- Markdown generation is programmatic rendering. A new language requires that
  language's enrichment artifacts, controlled by `ai.languages`.
- History search reads persistent `summaries/horizon-*.md`. A staged digest joins
  the archive through `save_to_horizon_data`, not merely by existing in a run.
- News and comments are source material. Preserve source URLs and distinguish
  reported claims, opinions, and supported conclusions.

## Handoff

Lead with what happened. Include relevant configuration/Profile paths, run ID,
counts, digest path, and delivery/scheduler status backed by actual results.
For contributions, summarize behavior and checks run. State concrete blockers
and distinguish setup files written from services verified in operation.

Maintainers can exercise [evaluation scenarios](evals/scenarios.json) using the
procedure in the checkout's `docs/agent-skill.md`.
