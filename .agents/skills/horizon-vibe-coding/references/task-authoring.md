# Task authoring

Use the connected Notion app to find the `Horizon · Codex Tasks` data source.
Fetch its current schema before writing because property types and available
status options are external state.

## Properties

Populate these properties when available:

| Property | Content |
|---|---|
| `Task` | Short, single-purpose implementation title |
| `Status` | Keep non-triggering while editing; use `Ready for Codex` last |
| `Risk` | `Low` only for bounded unattended work |
| `Allowed Paths` | Comma- or newline-separated repository-relative globs |
| `Verification` | Descriptive acceptance evidence, not a shell command |
| `Agent Run ID` | Worker-owned; do not invent |
| `Agent Result` | Worker-owned after triggering |
| `PR URL` | Worker-owned after publication |

The worker recognizes `Ready for Codex`, `Coding`, `Review`, and `Blocked`.
When authoring without triggering, preserve the existing non-ready status. For
a new page, use an available non-triggering intake status; if the schema has no
intake status, use `Blocked` and explain in the page that the task is a draft.

## Page body

Use this concise structure:

```markdown
## Background

Why this change is needed.

## Goal

One concrete behavior to implement.

## Acceptance criteria

- [ ] Observable behavior one
- [ ] Relevant error or boundary behavior
- [ ] Tests or deterministic evidence are updated

## Constraints

- Compatibility, dependency, architecture, or UX constraints

## Non-goals

- Explicitly excluded work
```

Do not hide required decisions in prose. If a product decision materially
changes the implementation, keep the task non-ready and ask for that decision.

## Allowed Paths

Inspect the repository with `rg --files` and relevant symbol searches before
choosing paths. Prefer the narrowest set that can satisfy the acceptance
criteria:

```text
src/export/**
tests/test_export.py
docs/export.md
```

Use exact filenames for isolated changes. Use a directory glob only when the
task can reasonably touch multiple files in that directory.

`**` permits every non-protected repository path, but only use it after an
explicit user request. It does not bypass the protected control-plane and
secret paths, and the default 50-file publication limit still applies.

Protected paths include any `AGENTS.md`, `.agents/skills/**`, `.codex/**`,
`.github/workflows/**`, `.github/codex/**`, protected environment files, and
private-key extensions.

## Risk classification

Use `Low` only when the task is bounded, reversible through Git, reviewable in
a draft PR, and does not require sensitive data or consequential external
actions. Treat security policy changes, credential handling, destructive data
changes, production changes, and unclear cross-system behavior as non-low.
Never lower risk solely to pass the unattended gate.

## Trigger checklist

Before setting `Ready for Codex`, confirm:

- The user explicitly requested execution, not only task creation.
- The title and body describe one implementable outcome.
- Acceptance criteria are testable.
- No material product decision is missing.
- Risk is present and allowed by local policy.
- Allowed Paths is present, repository-relative, and as narrow as practical.
- The Listener and public Tunnel health checks pass.

Set `Ready for Codex` as the final Notion edit.
