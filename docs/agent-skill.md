---
layout: default
title: Agent Skill
---

# Horizon Agent Skill

The [Horizon skill](https://github.com/Thysrael/Horizon/tree/main/skills/horizon)
helps an AI assistant configure a news radar, generate and tune digests, create
Profiles, schedule delivery, and contribute code. Horizon continues to run the
AI pipeline with the model and credentials in its own configuration.

## Install

Choose one of the installation methods below. You can install the skill first,
then ask your assistant to install and configure Horizon. With shell and network
access, the assistant can prepare a checkout and its Python environment using
the [README](https://github.com/Thysrael/Horizon#quick-start). Running tasks needs
Python 3.11+ and Horizon's dependencies. The skill and checkout may live at
different paths.

### Install with Skills CLI

With Node.js 22.20 or later, run:

```bash
npx skills add Thysrael/Horizon --skill horizon -g
```

The [Skills CLI](https://github.com/vercel-labs/skills) discovers the skill in this
repository and installs it for supported assistants such as Claude Code, Codex,
OpenCode, and OpenClaw. Follow the agent-selection prompts when shown; `-g`
installs at user level. To target a specific assistant, add its agent flag, for
example `-a opencode`.

### Download a skill package

[Download horizon-skill.zip](https://thysrael.github.io/Horizon/downloads/horizon-skill.zip).
The archive contains the complete `horizon/` skill directory, including scripts,
references, and the project license. Import it using your assistant's local-package
installer, or extract it and place the `horizon/` directory in the destination
listed below.

### Copy from a checkout

Copy the **entire** `skills/horizon` directory into your agent's skill directory:

| Agent | Personal skill destination | Reference |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/horizon/` | [Skills](https://code.claude.com/docs/en/skills) |
| Codex | `~/.agents/skills/horizon/` | [Skills](https://developers.openai.com/codex/skills) |
| OpenCode V2 | `~/.config/opencode/skills/horizon/` | [Skills](https://opencode.ai/v2/docs/skills/) |
| OpenClaw | `~/.openclaw/skills/horizon/` | [Skills](https://docs.openclaw.ai/tools/skills) |

For example, from the checkout, when the destination does not already exist:

```bash
mkdir -p ~/.claude/skills
cp -R skills/horizon ~/.claude/skills/horizon
```

Use your agent's project-level installation or extra-directory configuration if
preferred. For example, OpenCode V2 can load the checkout directly by adding its
absolute `skills` directory to the existing configuration's `skills` array.
This avoids maintaining a second copy.

### Start using the skill

Follow the host's refresh/reload behavior and verify that `horizon` appears in
its available skills. For a first-time setup, say:

> Use the Horizon skill to install and configure Horizon in my workspace, then
> help me set up a Chinese news radar for AI and open-source projects.

The assistant checks for an existing installation, prepares missing prerequisites,
and helps configure the model and sources. Importing the skill alone does not run
an installer.

For model setup, the assistant preserves existing Horizon settings and prefers
reusing an available provider API key before asking for new credentials. The
provider, model, API endpoint, and key environment variable must match. A key
stored privately by the host agent needs to be supplied to Horizon's process;
an OAuth or subscription login is not a drop-in API key. New model settings are
checked with a minimal JSON completion, since configuration validation alone
does not verify connectivity. Scheduled jobs and containers also need access
to the credentials in their own runtime environment.

Eligible ChatGPT users can instead choose Horizon's dedicated
[Sign in with ChatGPT](chatgpt.md) provider. The assistant can run the login and
model-discovery commands while the user completes browser authorization.

If Horizon is already installed, tell the assistant where the checkout is, or set
`HORIZON_PATH`. MCP is optional. A sandboxed agent needs access to the checkout
and its runtime.

## Try it

- "Use Horizon to build a Chinese news radar for AI inference and open-source
  tools, with at most ten stories a day."
- "Read today's Horizon digest and give me the original links."
- "Make a Profile for engineering write-ups that emphasizes solutions and
  tradeoffs."
- "Schedule Horizon at 08:00 Asia/Shanghai and send the digest to Feishu."
- "Add an optional content extractor following this repository's conventions."

The helper can also be inspected directly:

```bash
uv run python skills/horizon/scripts/horizon_ops.py run_pipeline --describe
uv run python skills/horizon/scripts/horizon_ops.py validate_config --params '{"check_env": false}'
```

Use `--params-file` for JSON parameters when shell quoting is inconvenient.
`--describe` reads current service parameters without executing the operation.
`ok: true` means the call returned; inspect native results for missing environment
variables and partial failures. See the skill's pipeline reference for details.

## Maintain and evaluate

Maintain one copy under `skills/horizon`. Configuration knowledge belongs in the
existing subject docs, and pipeline behavior belongs in Horizon. The helper
forwards native method parameters and results rather than maintaining another
CLI schema or reimplementing the pipeline. Only its operation allowlist needs
updating when intentionally exposing a new service method.

The `Deploy Docs` workflow packages the tracked `skills/horizon` directory and
project license with `git archive`, publishing `downloads/horizon-skill.zip`
alongside the Pages site. Changes to the skill trigger a deployment; the workflow
can also be run manually. The download link becomes available once that
deployment completes.

Run the adapter's offline regression tests after changing it:

```bash
uv sync --extra dev
uv run pytest tests/test_horizon_skill.py -q
```

For behavioral evaluation, use `skills/horizon/evals/scenarios.json` in temporary
checkouts with example configuration and fixture artifacts. Run a scenario with
the skill and in a fresh session without it, using the same model, tools, and
inputs. Record changed files, chosen operations, outputs, and whether each
expected behavior was met. Include the non-trigger examples when checking the
description. Fixture or mocked runs should cover routine evaluation; distinguish
these from live provider and delivery checks.

Adapted design principles: [Agent Skills specification](https://agentskills.io/specification),
[Anthropic skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator),
and [OpenAI skill-creator](https://github.com/openai/skills/tree/main/skills/.system/skill-creator).
