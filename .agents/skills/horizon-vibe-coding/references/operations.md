# Operations and troubleshooting

Treat Notion as the user-facing state and local evidence as the authoritative
execution trace.

## State interpretation

| Notion state | Interpretation |
|---|---|
| `Ready for Codex` | Awaiting webhook delivery or queue claim |
| `Coding` | Claimed; may be preparing, running Codex, verifying, or publishing |
| `Review` | Draft PR created and written back |
| `Blocked` | A gate or execution step failed; inspect `Agent Result` |

`Coding` alone does not prove that Codex is currently generating code. Confirm
with `pgrep -af '[c]odex[[:space:]]+exec'`, queue state, or a growing
`codex.jsonl`. The bracketed process pattern avoids matching the inspection
command itself.

## Health and queue

Run:

```bash
bash .agents/skills/horizon-vibe-coding/scripts/check-health.sh
```

Interpret the results:

- Local and public healthy: Listener and Tunnel route are reachable.
- Local healthy, public failed: diagnose Cloudflare Tunnel or DNS.
- Both failed: diagnose the Windows listener task or WSL first.
- If a sandbox could be blocking local or network access, retry the read-only
  check with narrowly scoped approval before declaring the service unhealthy.
- `queue.running=1`: one event is being processed.
- `queue.queued>0`: work is waiting behind the single worker.
- `queue.failed>0`: at least one durable event failed; correlate with Notion.

## Local run evidence

Fetch the page's `Agent Run ID` from Notion, then inspect that exact run:

```bash
bash .agents/skills/horizon-vibe-coding/scripts/inspect-run.sh \
  --run-id local-00000000-0000-0000-0000-000000000000
```

Follow Codex or verification output:

```bash
bash .agents/skills/horizon-vibe-coding/scripts/inspect-run.sh \
  --run-id local-00000000-0000-0000-0000-000000000000 \
  --follow
```

Use the latest local run only when exact task identity is not material:

```bash
bash .agents/skills/horizon-vibe-coding/scripts/inspect-run.sh --latest
```

Run directories live under `.codex-runtime/notion-agent/runs/`. Important
artifacts are:

| Artifact | Evidence |
|---|---|
| `task.json` | Page claimed |
| `prompt.md` | Trusted implementation prompt rendered |
| `codex.jsonl` | Codex JSONL execution stream |
| `codex-result.json` | Structured Codex result completed |
| `verification.log` | Trusted verification started |
| `pr-body.md` | PR metadata prepared |

Do not expose the full `task.json` when its page body may contain private
product information.

## Stalled tasks

For `Ready for Codex` that does not move:

1. Verify local and public health.
2. Confirm the webhook subscription still has the required event types.
3. Inspect queue counts.
4. Confirm the page belongs to the configured data source.
5. Make one harmless property update only if a fresh webhook event is required.

For `Coding` that appears stalled:

1. Match `Agent Run ID` to the local run directory.
2. Check `pgrep -af '[c]odex[[:space:]]+exec'`.
3. Follow `codex.jsonl`; if Codex completed, follow `verification.log`.
4. Check Git/network state only after local execution evidence.
5. Do not manually reset the page while its durable queue item is running.

## Blocked recovery

Read `Agent Result` and the preserved run logs. Common causes are missing
Allowed Paths, non-low risk, out-of-scope file changes, structured-result
failure, verification failure, or GitHub publication failure.

Apply the smallest safe correction. Re-triggering a page can create a new run
and potentially a new draft PR, so check for an existing PR before setting the
page to `Ready for Codex` again.

### Reserved-address DNS failures

If many URL-security, extractor, or webhook tests fail because a documentation
hostname such as `example.com` resolves into `198.18.0.0/15`, treat it as test
environment or test-isolation evidence. Confirm with:

```bash
getent ahostsv4 example.com
```

Do not allow the reserved range through the SSRF guard and do not weaken the
trusted verification command. Tests that mock HTTP must also mock the DNS or
URL-safety boundary deterministically. Keep the task `Blocked` until the test
isolation is fixed and the trusted suite passes.

## Review handoff

At `Review`, report the draft PR URL, changed files, verification evidence, and
remaining risks. Keep merge, deployment, and production actions manual unless
the user separately authorizes them.
