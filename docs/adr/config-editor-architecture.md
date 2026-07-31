# Local Configuration Editor Architecture

- **Status:** Accepted for implementation
- **Decision date:** 2026-07-22
- **Target release:** `0.2.0`
- **Decision scope:** Local configuration editing only

## Decision Summary

Horizon will add a local, browser-based configuration editor started with:

```console
uv run horizon-config
```

The editor will bind to `127.0.0.1:8765` by default and will not support remote
listening in the initial release. It will use a Python web server, server-rendered
HTML, and local static assets. It will not require an account, database, cloud
service, or Node.js build toolchain.

The configuration subsystem will distinguish two representations:

1. **Raw configuration** is the unexpanded JSON document and is the only
   representation that may be edited or persisted.
2. **Effective configuration** is an in-memory copy with environment-variable
   references resolved and validated through the existing Pydantic `Config`
   model. It must never be used as the source of a save operation.

This boundary prevents values referenced through `${VAR}` from being expanded
and accidentally written back to `data/config.json`.

## Context

Horizon configuration now spans AI providers, per-stage AI overrides, eight
source families, extractors, filtering and category quotas, email, webhooks, and
GitHub Pages. The interactive wizard is useful for first-time setup but is not a
complete editor for an existing configuration.

The current runtime loader expands `${VAR}` references before constructing the
Pydantic model. The current save path serializes a Pydantic model. A configuration
editor must not compose those operations directly because doing so would persist
expanded private values rather than the raw placeholders authored by the user.

The editor must also protect users from three additional forms of data loss:

- dropping keys not yet understood by the UI;
- overwriting a file modified by another editor after the page was loaded; and
- replacing the only valid configuration with an invalid or partially written
  document.

## Goals

The first generally available release will:

- provide a guided editor for every current top-level configuration section;
- retain an advanced raw JSON editor as an escape hatch;
- load existing configurations without requiring migration;
- report structural errors, cross-field warnings, and missing environment
  variables at precise JSON paths;
- preserve raw `${VAR}` references and unknown fields;
- show a redacted diff before saving;
- prevent stale browser sessions from silently overwriting newer file contents;
- create recoverable backups and write the active configuration atomically;
- run entirely on the user's machine with no telemetry or remote dependency;
- offer Simplified Chinese and English UI strings; and
- keep the existing `horizon`, `horizon-wizard`, and `horizon-mcp` entry points
  compatible.

## Non-Goals

The initial release will not provide:

- accounts, teams, permissions, or a shared configuration database;
- remote access or a `0.0.0.0` listening mode;
- cloud synchronization or GitHub Secrets management;
- an in-browser `.env` editor or the ability to read existing secret values;
- scheduling, pipeline execution, digest browsing, or observability dashboards;
- automatic AI calls while editing a field;
- a Node.js frontend build pipeline or CDN-hosted assets;
- Japanese UI localization; or
- automatic migration to a stricter `extra="forbid"` configuration schema.

Connection tests and test deliveries are part of the `0.2.0` completion plan,
but they are not required for the first editor beta. They must be explicit user
actions and must not run during page load, validation, or save.

## User Journeys

### First-time configuration

1. The user runs `uv run horizon-config`.
2. The server opens a loopback browser session.
3. When `data/config.json` is absent, the editor offers to initialize it from
   `data/config.example.json` or start with the minimum valid structure.
4. The user completes AI, source, filtering, and delivery sections.
5. The editor validates the candidate, reports missing environment variables,
   shows a diff, and saves after confirmation.

### Editing an existing configuration

1. The editor loads the raw JSON and computes a revision from the original
   bytes.
2. Form edits are represented as JSON Pointer patches applied to the raw
   document.
3. Unknown fields remain in the raw document unless the user explicitly changes
   them in the advanced editor.
4. The server validates an expanded in-memory copy and returns only sanitized
   diagnostics.
5. The save request succeeds only if the on-disk revision still matches the
   revision loaded by the browser.

### Recovering a previous configuration

1. The user opens the backup page and selects a version.
2. The editor shows a redacted diff against the active configuration.
3. After explicit confirmation, the current file is backed up and the selected
   version is restored atomically.

## Architecture

```text
Browser UI
    |
    v
Local editor server (127.0.0.1:8765)
    |
    v
ConfigApplicationService
    |-- RawConfigDocument ------> data/config.json
    |-- EffectiveConfigResolver -> environment variables -> Pydantic Config
    |-- ConfigValidator --------> errors, warnings, missing environment names
    |-- RedactedDiff
    `-- BackupStore ------------> data/config-backups/

Later integration:
    horizon-wizard --\
    horizon-mcp -----+----------> ConfigApplicationService
    horizon runtime -/           EffectiveConfigResolver
```

### Components

#### `RawConfigDocument`

The raw document owns:

- the resolved configuration path;
- the original UTF-8 source text;
- the parsed but unexpanded JSON object; and
- a SHA-256 revision computed from the original file bytes.

The editor API returns the raw JSON because placeholders must remain editable.
Access to that API requires an authenticated local session because a user may
have placed private literals directly in the file.

#### `EffectiveConfigResolver`

The resolver:

1. deep-copies raw JSON;
2. discovers every `${VAR}` reference;
3. expands only the copy;
4. validates the copy with the existing Pydantic `Config` model; and
5. returns the model plus referenced and missing environment-variable names.

Expanded values must not be stored on a long-lived application object, returned
to the browser, placed in validation errors, or written to logs.

#### `ConfigValidator`

Validation produces issues with this stable shape:

```json
{
  "severity": "error",
  "path": "/sources/rss/2/url",
  "code": "invalid_url",
  "message": "Enter a valid HTTP or HTTPS feed URL."
}
```

Pydantic error inputs are not returned to the client. Cross-field rules that
would reject configurations accepted by the current runtime will initially be
warnings. They may become errors only in a separately reviewed configuration
version change.

#### `ConfigApplicationService`

This is the single application-facing boundary for:

- reading raw configuration;
- validating a candidate;
- applying JSON Pointer patches;
- producing a redacted structured diff;
- saving with optimistic concurrency;
- listing backups; and
- restoring a backup.

`StorageManager` remains a compatibility facade while the wizard and MCP tools
are migrated to the shared service in later implementation phases.

## File and Save Semantics

### Configuration path

- The default path is `data/config.json`, matching the current CLI behavior.
- `--config PATH` may select another file explicitly at process startup.
- The browser cannot change the active path after startup.
- Every path is resolved once on the server and all backup operations remain
  within the configured backup directory.

### Optimistic concurrency

Every write request includes the revision returned by the latest read. The server
recomputes the revision immediately before saving.

- Matching revisions allow validation and save to continue.
- Mismatched revisions return HTTP `409 Conflict` and do not modify the file.
- The UI then offers to reload or compare the browser candidate with the new
  on-disk document.

### Unknown fields

Form submissions use JSON Pointer patches applied to the raw document rather
than rebuilding the document from the Pydantic model. This preserves unknown
top-level and nested keys. The editor reports unknown keys as warnings and shows
them in the advanced JSON editor.

The wire format is an RFC 6902 JSON Patch document. The editor needs `add`,
`replace`, `remove`, and `move` operations; `move` supports reordering repeated
source entries without rebuilding their containing objects. The advanced editor
may replace the root document after the user has reviewed the resulting diff.

### Atomic write

After validation and backup, the server writes to a temporary file in the target
directory and replaces the destination atomically using the existing file
utility. If replacement fails, the current destination remains unchanged.

### Backup policy

The backup directory is:

```text
data/config-backups/
```

The frozen policy is:

- create one timestamped backup of the active file before every successful save
  and before every restore;
- include a short content revision in the backup filename;
- retain the 20 newest backups;
- prune older backups only after the new active file has been written and
  reloaded successfully;
- never delete the only backup;
- add the backup directory to `.gitignore`; and
- require an explicit confirmation before restore.

The existing single `config.json.bak` behavior remains available to older code
until all writers use the new application service.

## Web Technology

The editor will use:

- FastAPI for the local HTTP application and JSON API;
- Uvicorn for the local server;
- Jinja2 for page layout;
- local CSS and native JavaScript modules for dynamic fields; and
- Pydantic JSON Schema plus curated UI metadata for field types, defaults,
  labels, ordering, conditional visibility, and help text.

FastAPI, Uvicorn, and Jinja2 will be declared as direct project dependencies.
No behavior may rely on an undeclared transitive dependency from MCP packages.

All browser assets are packaged inside the Python wheel. The editor must work
without internet access and must not load scripts, fonts, styles, or icons from a
CDN.

## UI Information Architecture

```text
+-----------------------------------------------------------------------+
| Horizon Configuration                         Valid | zh-CN | Save     |
+----------------------+------------------------------------------------+
| Overview             | Configuration health                         |
| Quick setup          | - AI: OpenAI / gpt-4                         |
| AI                   | - 12 enabled sources                         |
| Sources              | - 2 missing environment variables            |
| Extractors           | - 1 warning                                  |
| Filtering            |                                               |
| Delivery             | [Review issues] [Preview changes]             |
| Advanced JSON        |                                               |
| Backups              |                                               |
+----------------------+------------------------------------------------+
```

### Overview

Shows validity, the effective AI model names, enabled source counts, output
languages, missing environment-variable names, warnings, current path, revision,
and latest save time. It never shows environment-variable values.

### Quick setup

Covers only the minimum valid configuration: default AI provider and model,
output languages, and at least one source. It does not reset advanced fields that
the user did not edit.

### AI

Provides default provider settings and collapsible overrides for analysis,
deduplication, enrichment, translation, and source recommendation.

### Sources

Uses repeatable cards grouped by source type. Cards support add, duplicate,
enable/disable, delete, and reorder. Conditional fields depend on source mode.

### Extractors and filtering

Supports named extractor definitions, RSS extractor references, category groups,
group limits, default-group handling, and total item limits.

### Delivery

Contains GitHub Pages, email, and webhook settings. Template fields use a
multiline or JSON-aware editor. Test delivery is not automatic and requires a
separate confirmation.

### Advanced JSON

Edits the same raw document used by forms. It supports formatting, validation,
and navigation to a reported JSON path. It does not offer a force-save action for
an invalid document.

### Save flow

```text
Edit -> Validate -> Review issues -> Preview redacted diff -> Confirm -> Save
```

The UI always shows whether there are unsaved changes and warns before closing or
navigating away.

## API Draft

The page shell and health endpoint contain no configuration data and may be
loaded before session bootstrap. All configuration APIs require an authenticated
local session.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/healthz` | Local process health only; returns no configuration data |
| `GET` | `/` | Static editor shell; returns no configuration data |
| `POST` | `/api/v1/session/bootstrap` | Exchange the one-time fragment token for a process-local session |
| `GET` | `/api/v1/session` | Return session status and a CSRF token |
| `GET` | `/api/v1/config` | Raw JSON, path metadata, revision, and sanitized summary |
| `GET` | `/api/v1/schema` | Pydantic JSON Schema and curated UI metadata |
| `POST` | `/api/v1/config/validate` | Validate a raw candidate without writing |
| `POST` | `/api/v1/config/diff` | Produce a redacted structured diff |
| `PATCH` | `/api/v1/config` | Apply raw-document patches and save with a revision |
| `GET` | `/api/v1/backups` | List backup metadata without returning contents |
| `GET` | `/api/v1/backups/{id}/diff` | Redacted diff between a backup and the active file |
| `POST` | `/api/v1/backups/{id}/restore` | Restore after revision check and confirmation |

Deferred until the diagnostics implementation phase:

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/tests/source` | Perform a bounded, read-only source check |
| `POST` | `/api/v1/tests/ai` | Make an explicitly confirmed minimal AI request |
| `POST` | `/api/v1/tests/email` | Send an explicitly confirmed test email |
| `POST` | `/api/v1/tests/webhook` | Send an explicitly confirmed test webhook |

API errors use stable codes and sanitized details. A stale revision uses HTTP
`409`; invalid input uses `422`; an invalid session uses `401`; and a missing or
invalid CSRF token uses `403`.

A save request uses this envelope:

```json
{
  "revision": "sha256:...",
  "operations": [
    {
      "op": "replace",
      "path": "/filtering/ai_score_threshold",
      "value": 7.5
    }
  ],
  "acknowledge_warnings": true
}
```

The server applies the patch to a fresh read of the raw document, repeats all
validation, and rejects any save containing errors. A candidate containing only
warnings may be saved only when `acknowledge_warnings` is true. A missing value
named by a credential field such as `api_key_env` is normally a warning; an
unresolved `${VAR}` that prevents a typed field from validating is an error.

## Local Server Security

The initial release has these mandatory controls:

- bind only to `127.0.0.1`;
- default to port `8765` and accept an explicit `--port` override;
- fail with an actionable message if the requested port is occupied;
- do not implement a remote-listening flag;
- allow only `localhost`, `127.0.0.1`, and `[::1]` Host headers;
- do not enable CORS;
- issue a random, single-use bootstrap token at startup and place it only in the
  URL fragment, for example `#bootstrap=<token>`, so it is not sent in an HTTP
  request or access log;
- let the local page script exchange that token through
  `/api/v1/session/bootstrap`, invalidate it immediately, and remove the fragment
  with `history.replaceState`;
- store sessions only in process memory and expire all sessions when the editor
  process exits;
- return an `HttpOnly`, `SameSite=Strict` session cookie after bootstrap;
- require a per-session CSRF token on every state-changing request;
- require a loopback `Origin` on every state-changing request;
- set a restrictive Content Security Policy with local assets only;
- exclude request bodies, raw configuration, headers, query strings, and
  environment values from application logs; and
- sanitize exception responses before returning them to the browser.

The server may open the fragment URL automatically. `--no-browser` disables that
behavior and prints the single-use fragment URL for manual opening. Browser
auto-open failure is non-fatal and prints the same URL. The bootstrap token is no
longer usable after its first successful exchange.

## Threat Model

| Threat | Example | Required mitigation |
|---|---|---|
| Expanded secret persistence | `${FEED_TOKEN}` becomes a literal token on save | Separate raw and effective representations; only raw documents are writable |
| Secret disclosure in diagnostics | Pydantic includes the rejected input value | Remove error inputs and sanitize all errors before serialization |
| Cross-site request forgery | A website posts changes to the loopback server | SameSite session, CSRF token, no CORS, strict Origin/Host checks |
| DNS rebinding or hostile Host | A remote origin reaches the loopback process | Fixed loopback bind and Host allowlist |
| Stale overwrite | The file changes after the browser loads it | SHA-256 revision and HTTP `409` optimistic-concurrency response |
| Unknown-field loss | A new config key is omitted by generated forms | Patch the raw document and test unknown-key preservation |
| Partial write | The process exits during save | Same-directory temporary file and atomic replacement |
| Backup path traversal | A crafted backup ID escapes the backup directory | Server-generated opaque IDs and resolved-path containment checks |
| Accidental external side effect | Validation sends an email or calls a paid model | Pure validation; separate explicitly confirmed test endpoints |
| Dependency on remote assets | A CDN is unavailable or compromised | Package all browser assets in the wheel and enforce CSP |
| Sensitive access logging | URL, body, or headers contain private values | Log only method, route template, status, duration, and request ID |

## Localization and Accessibility

The first release includes English and Simplified Chinese strings. The browser
locale selects the initial language, and the user's explicit selection is stored
locally. Configuration values are never translated.

All controls require associated labels, keyboard access, visible focus states,
and text descriptions that do not rely on color alone. Dynamic validation must
use an accessible live region. Desktop layout is primary, but editing must remain
usable on a narrow viewport without horizontal page scrolling.

## Delivery Sequence

Implementation will use focused task branches and pull requests:

1. `codex/config-document-core`
2. `codex/config-ui-shell`
3. `codex/config-ui-editor`
4. `codex/config-ui-diagnostics`
5. `codex/config-ui-integration`

Later branches depend on the preceding delivery. Each branch must contain only
its own files or hunks and must pass focused tests before publication.

## Validation and Release Gates

### Core gate

- Raw placeholders survive load, form patch, validation, diff, and save.
- Unknown top-level and nested fields survive normal form edits.
- Expanded values do not appear in API results, errors, logs, or saved JSON.
- Revision conflicts and failed atomic replacements leave the active file intact.

### Editor beta gate

- `data/config.example.json` completes an edit-and-save round trip.
- Every current model field is reachable from a form or Advanced JSON.
- The editor launches from an installed wheel on Windows and Linux.
- All browser assets load with the network disabled.

### `0.2.0` gate

- The wizard, MCP validation, runtime, and editor share resolution and diagnostic
  behavior.
- Explicit connection and delivery tests are bounded and sanitized.
- The complete test suite, package smoke test, and browser workflow pass.
- English, Chinese, security, and troubleshooting documentation is published.

## Alternatives Considered

### Extend only the terminal wizard

Rejected as the primary solution. It remains useful for onboarding, but nested
repeatable forms, diffs, conditional fields, template editing, and recovery are
more usable in a browser interface.

### Hosted configuration service

Rejected for the initial release because it would require authentication,
authorization, remote secret handling, storage, deployment, and a much larger
threat model.

### React or Vue single-page application

Deferred. It would add a second build toolchain and generated frontend artifacts
before the interaction model is proven. The API boundary allows a richer client
to replace the initial server-rendered interface later.

### Generate every form directly from JSON Schema

Rejected as the sole approach. JSON Schema covers types and defaults but does not
encode all user-facing grouping, conditional visibility, source-specific help,
or template-editor behavior. The chosen design combines generated schema with
curated UI metadata.

### Save the effective Pydantic model

Rejected because it can persist expanded environment-variable values and discard
unknown fields.

## Consequences

### Positive

- Configuration becomes discoverable and safer to edit.
- Runtime validation remains centralized in Pydantic.
- Raw/effective separation closes an existing round-trip safety gap.
- The API permits future TUI, desktop, or richer web clients without changing the
  configuration domain layer.
- The feature remains opt-in and does not change normal Horizon execution.

### Costs

- The project gains a small local web stack and packaged browser assets.
- UI metadata must remain synchronized with Pydantic models.
- Backup lifecycle and local-session security add ongoing maintenance.
- English and Chinese strings must be updated when fields or pages change.

## Frozen Decisions

The following decisions are closed for the implementation of `0.2.0` unless a
new ADR supersedes this document:

- local browser editor rather than hosted administration;
- loopback-only binding;
- default port `8765`;
- FastAPI, Uvicorn, Jinja2, and native local browser assets;
- raw configuration as the only persisted representation;
- effective configuration as an in-memory validation/runtime representation;
- RFC 6902 JSON Patch operations with JSON Pointer paths for normal form edits;
- optimistic concurrency based on a content revision;
- timestamped backups in `data/config-backups/`;
- retention of the 20 newest backups;
- no `.env` editing in the initial release;
- English and Simplified Chinese in the initial release; and
- no Node.js build pipeline for the initial client.

## Deferred Decisions

These decisions are intentionally outside the implementation-critical path and
may be handled by later ADRs:

- whether a future release permits authenticated remote access;
- whether `.env` editing can be added safely;
- whether the UI should move to a compiled frontend framework;
- when Japanese localization enters the release plan;
- whether configuration version `2.0` should reject unknown fields; and
- whether backup retention becomes user-configurable.
