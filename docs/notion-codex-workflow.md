# Notion → Local Codex workflow

Horizon can receive Notion connection webhooks on a local computer, queue each
event durably, and start `codex exec` only when a page is actually ready for
implementation. Codex uses the ChatGPT login already present on that computer;
the workflow does not require `OPENAI_API_KEY` or a GitHub Actions runner.

The local executor pins each implementation run to `gpt-5.6-sol` with `xhigh`
reasoning through `CODEX_MODEL` and `CODEX_REASONING_EFFORT`. It passes both
values directly to `codex exec`; user-level Codex configuration is intentionally
ignored so unattended runs do not drift when local defaults change.

The automation creates a dedicated Git worktree and branch, runs deterministic
verification, pushes the branch, opens a draft pull request, and writes the
result back to Notion. It never merges or deploys automatically.

## Architecture

```text
Notion connection webhook
        |
        v
Cloudflare Tunnel (public HTTPS)
        |
        v
127.0.0.1:4782/notion/webhook
        |
        +--> HMAC and source validation
        +--> SQLite event queue and event-ID deduplication
        |
        v
single local worker
        |
        +--> claim page: Ready for Codex -> Coding
        +--> create worktree and feature branch
        +--> codex exec with local ChatGPT OAuth
        +--> enforce protected paths and Allowed Paths
        +--> run trusted verification command
        +--> commit, push, and create draft PR
        +--> update page: Review or Blocked
```

Webhook requests are acknowledged after validation and durable enqueueing. The
long-running coding task is never executed inside the HTTP request.

## Repository files

- `src/notion_agent/config.py`: trusted configuration and local token storage
- `src/notion_agent/queue.py`: durable SQLite queue
- `src/notion_agent/webhook.py`: FastAPI webhook endpoint
- `src/notion_agent/executor.py`: Codex, worktree, test, and PR orchestration
- `src/notion_agent/cli.py`: listener, preflight, status, and queue commands
- `scripts/notion_coding.py`: shared Notion page parsing and status updates
- `.agents/skills/horizon-vibe-coding/`: explicit-use task authoring and
  operations skill
- `.github/codex/prompts/notion-task.md`: trusted Codex prompt
- `.github/codex/schemas/notion-result.schema.json`: structured result schema
- `config/notion-agent.env.example`: configuration template
- `scripts/install_notion_agent.ps1`: Windows logon task installer

`.codex-runtime/` and `.env.notion-agent` are ignored. Runtime logs, webhook
payloads, verification evidence, SQLite state, failed worktrees, and captured
verification tokens remain local.

## 1. Prepare the local environment

Copy the template without committing the result:

```bash
cp config/notion-agent.env.example .env.notion-agent
```

Set at least:

```dotenv
HORIZON_REPO_ROOT=/mnt/c/path/to/Horizon
NOTION_TOKEN=secret_...
NOTION_DATA_SOURCE_ID=...
NOTION_WORKSPACE_ID=...
NOTION_WEBHOOK_BOOTSTRAP_SECRET=...
GITHUB_REPOSITORY=owner/Horizon
GITHUB_DEFAULT_BRANCH=main
```

The Notion token must belong to an integration that can read page content and
update the task database. A secret stored only in GitHub Secrets is not
available to the local process; configure it again in the ignored local file or
an equivalent local secret store.

Do not copy Codex authentication files. Log in normally on this computer:

```bash
codex login
codex login status
```

Authenticate GitHub CLI for branch pushes and draft PR creation:

```bash
gh auth login
gh auth status
```

Run the complete preflight:

```bash
uv run horizon-notion-agent \
  --env-file .env.notion-agent \
  preflight
```

## 2. Start the listener

Start locally:

```bash
uv run horizon-notion-agent \
  --env-file .env.notion-agent \
  serve
```

Health is available only on loopback by default:

```text
http://127.0.0.1:4782/healthz
```

The Notion webhook endpoint is:

```text
http://127.0.0.1:4782/notion/webhook
```

Keep the listener bound to `127.0.0.1`. Publish only this local port through a
managed HTTPS tunnel. Do not bind the service directly to the LAN or forward a
router port.

## 3. Create the Cloudflare Tunnel

For a temporary smoke test:

```bash
cloudflared tunnel --url http://127.0.0.1:4782
```

Quick Tunnel URLs change after restart and have no uptime guarantee. Use a
named tunnel and stable hostname for normal operation, for example:

After a Quick Tunnel test, delete its temporary Notion webhook subscription
because the random URL cannot be reused.

```text
https://horizon-agent.example.com/notion/webhook
```

Create the named tunnel while logged into the Cloudflare account that manages
the chosen domain:

```bash
cloudflared tunnel login
cloudflared tunnel create horizon-notion-agent
cloudflared tunnel route dns horizon-notion-agent horizon-agent.example.com
```

Then create `~/.cloudflared/config.yml` using the UUID and credential path
printed by `tunnel create`:

```yaml
tunnel: <tunnel-uuid>
credentials-file: /home/<user>/.cloudflared/<tunnel-uuid>.json

ingress:
  - hostname: horizon-agent.example.com
    service: http://127.0.0.1:4782
  - service: http_status:404
```

Verify it before installing startup tasks:

```bash
cloudflared tunnel run horizon-notion-agent
```

Configure `cloudflared` as a service separately from the listener so each
process can restart independently.

## 4. Create the Notion webhook subscription

In the Notion integration settings:

1. Open **Webhooks** and create a subscription.
2. Generate a one-time bootstrap secret locally:

   ```bash
   openssl rand -hex 32
   ```

3. Store it as `NOTION_WEBHOOK_BOOTSTRAP_SECRET` and set the public URL to:

   ```text
   https://horizon-agent.example.com/notion/webhook?setup=<bootstrap-secret>
   ```

   The query secret prevents an arbitrary public request from capturing the
   unsigned initial verification token. Never commit or paste it into chat.

4. Subscribe to:
   - `page.created`
   - `page.properties_updated`
   - `page.content_updated`
5. Notion sends an initial `verification_token` request.
6. The listener stores that token with user-only permissions under
   `.codex-runtime/notion-agent/`.
7. Print it locally and paste it into the Notion verification dialog:

   ```bash
   uv run horizon-notion-agent \
     --env-file .env.notion-agent \
     verification-token
   ```

8. After verification, remove `?setup=...` from the subscription URL if Notion
   permits editing it, and remove `NOTION_WEBHOOK_BOOTSTRAP_SECRET` from the
   local environment. Signed event delivery does not need the bootstrap value.

Never paste the verification token into a pull request, issue, chat, or
committed env file. After setup, set `NOTION_INTEGRATION_ID` from a verified
event for the narrowest source validation.

Every normal event must contain a valid `X-Notion-Signature`. The listener also
checks the configured workspace, integration, event type, data source, and page
entity before enqueueing.

## 5. Configure the Notion database

Required properties:

| Property | Type | Purpose |
|---|---|---|
| `Task` | Title | Short implementation title |
| `Status` | Select or Status | Intake and result state |

Status values:

- `Ready for Codex`
- `Coding`
- `Review`
- `Blocked`

Recommended optional properties:

| Property | Type |
|---|---|
| `Agent Run ID` | Rich text |
| `PR URL` | URL |
| `Agent Result` | Rich text |
| `Risk` | Select |
| `Allowed Paths` | Rich text |
| `Verification` | Rich text |

`Allowed Paths` accepts comma- or newline-separated Git globs, for example:

```text
src/**
tests/**
```

`Allowed Paths` is required by default. Changed files outside those patterns
block publication, and more than 50 changed files blocks publication by
default.

`Verification` is untrusted task context. The command that actually runs comes
only from trusted local `CODEX_VERIFICATION_COMMAND`.

Only `Risk=Low` runs unattended by default. Missing, Medium, or High risk tasks
move to `Blocked` before Codex starts. These gates are locally configurable,
but widening them should be a deliberate human decision.

## 6. Install Windows startup

From PowerShell:

```powershell
.\scripts\install_notion_agent.ps1 `
  -Distro Ubuntu `
  -LinuxRepoPath /mnt/c/path/to/Horizon `
  -LinuxEnvFile .env.notion-agent `
  -CloudflaredTunnelName horizon-notion-agent `
  -StartNow
```

The script registers separate listener and tunnel tasks at user logon, with
restart-on-failure settings. They run with the current user's Codex, GitHub,
Notion, and Cloudflare credentials. The computer, WSL, and network connection
must remain available.

## 7. Operate and diagnose

Invoke the repository skill from an interactive Codex session to author,
trigger, monitor, or troubleshoot a task:

```text
$horizon-vibe-coding create and run a low-risk Notion task for Horizon
```

The skill is explicit-use only. The background `codex exec` implementation run
does not invoke it implicitly.

Inspect queue counts:

```bash
uv run horizon-notion-agent \
  --env-file .env.notion-agent \
  status
```

Process at most one queued event manually:

```bash
uv run horizon-notion-agent \
  --env-file .env.notion-agent \
  process-once
```

Successful worktrees are removed after PR creation. Failed worktrees and logs
are preserved by default under `.codex-runtime/notion-agent/`. Set
`NOTION_AGENT_KEEP_FAILED_WORKTREES=false` only after the failure diagnostics
are reliably collected elsewhere.

## Security and publication gates

- Webhook signatures are computed from the raw request body with HMAC-SHA256.
- Notion event IDs are the durable deduplication key.
- A single worker prevents simultaneous local claims.
- A restarted worker can resume only its own `Coding` page by matching the
  persisted `Agent Run ID`; it cannot take over another run's claim.
- Events caused by the agent's own status updates are harmless: the page is no
  longer `Ready for Codex`, so they finish as ignored.
- Notion content is untrusted product input and cannot override `AGENTS.md`,
  local configuration, sandboxing, or publication gates.
- Automated tasks cannot modify any `AGENTS.md`, `.codex/**`,
  `.agents/skills/**`, `.github/workflows/**`, `.github/codex/**`, secret env
  file, or private-key path.
- `Allowed Paths` is enforced after Codex finishes and before staging.
- Missing Allowed Paths, non-low risk, or excessive changed-file counts block
  publication with the default local policy.
- The structured Codex result must be valid, have status `success`, and not
  require human input.
- The trusted verification command must exit zero.
- `git diff --cached --check` must pass.
- Pull requests are always created as drafts.
- There is no automatic merge or deployment.

## First end-to-end test

1. Keep the existing smoke page out of `Ready for Codex`.
2. Start the listener and stable tunnel.
3. Verify the Notion webhook subscription.
4. Run `preflight` until every row is `OK`.
5. Create a tiny low-risk page with narrow `Allowed Paths`.
6. Change its status to `Ready for Codex`.
7. Confirm the listener returns the page to `Coding`.
8. Review local `codex.jsonl` and `verification.log`.
9. Confirm a draft PR is created.
10. Confirm Notion contains the PR URL and status `Review`.

Do not enable unattended high-risk tasks until several small tasks have
completed correctly.
