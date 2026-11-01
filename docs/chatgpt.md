---
layout: default
title: Sign in with ChatGPT
---

# Use your ChatGPT plan

Horizon supports OpenAI's official **Sign in with ChatGPT / ChatGPT plan usage**
preview through the optional `openai-chatgpt` provider. Eligible Plus and Pro
users can authorize Horizon to use their plan without setting `OPENAI_API_KEY`.
Availability depends on the selected account, workspace, model, and OpenAI's
current eligibility rules. The regular `openai` provider continues to use API billing.

## Connect and verify

Update the project environment with `uv sync`, then run:

```bash
uv run horizon-chatgpt login
uv run horizon-chatgpt models
uv run horizon-chatgpt check --model MODEL_SLUG
```

The login command opens the system browser. Authorize ChatGPT plan usage there;
identity sign-in alone does not grant inference access. Use the exact model slug
returned by `models`, rather than an API model name from another configuration.
`check` performs one real, small JSON request using your plan and verifies that
the response completed successfully.

For interactive setup, choose `openai-chatgpt` in `uv run horizon-wizard`. It
handles login and shows the account's model catalog. For manual setup, replace
the `ai` section in your existing configuration:

```json
{
  "ai": {
    "provider": "openai-chatgpt",
    "model": "MODEL_SLUG",
    "languages": ["zh"]
  }
}
```

`api_key_env` is omitted or empty. `ai.chatgpt_account` can optionally name a
saved client ID from `horizon-chatgpt accounts`; the wizard records it so the
configuration stays tied to the selected registration. Without it, a new run
uses the active account. Refresh the model selection after switching accounts.
The CLI keeps that account across its AI stages; staged MCP runs retain the
selected registration ID in run metadata so changing the active account does
not redirect an existing run.

## Account commands

```bash
uv run horizon-chatgpt status
uv run horizon-chatgpt accounts
uv run horizon-chatgpt login --new-account
uv run horizon-chatgpt select CLIENT_ID
uv run horizon-chatgpt login --account CLIENT_ID
uv run horizon-chatgpt logout --account CLIENT_ID
```

`status`, `models`, and `check` also accept `--account CLIENT_ID`. If plan usage
was not granted, explicitly request it with `login --enable-plan` (plus
`--account` when needed). `login --no-browser` prints a URL to open in a browser
on the same machine. The callback uses `127.0.0.1` on an available local port.

Logout attempts to revoke the renewable session, clears local tokens, and keeps
the registration and host ID for reconnecting. If remote revocation could not be
confirmed, the command reports it. Access and limits can also be managed at
[ChatGPT Settings → Usage](https://chatgpt.com/settings/usage).

## Storage, scheduled runs, and self-hosting

By default, state lives in `~/.config/horizon/chatgpt/`, or under
`$XDG_CONFIG_HOME/horizon/chatgpt/`. `HORIZON_CHATGPT_AUTH_DIR` overrides this
location. `credentials.json` contains account registrations and tokens;
`host.json` contains this installation's stable host ID. Keep both outside the
repository. Credential writes are atomic and owner-only on Unix, and a file lock
serializes refreshes across threads and processes.

Access tokens expire after one hour. Horizon refreshes them near expiry and saves
the replacement refresh token. Current refresh tokens last 30 days, with a new
30-day lifetime after a successful refresh. Revoked or expired sessions require
login again. Network failures retain saved credentials.

For a persistent self-hosted VM or container, follow the
[official VM procedure](https://developers.openai.com/siwc/token-sharing-open-source/self-hosted-vms):

1. Run `uv run horizon-chatgpt init` on the destination to create its own host ID.
2. Complete OAuth locally using Horizon and the intended account/workspace.
3. Transfer `credentials.json` to the destination over SSH or another protected
   channel. Preserve its owner-only access and the destination's `host.json`.
4. Let the destination own subsequent token refreshes. Avoid using the copied
   session from two independent credential stores; reconnect locally if needed.
5. Run `check` from the actual scheduled account/container before scheduling a digest.

Persist the auth directory across container restarts. The scheduled process must
use the same auth directory and have write access for refreshes. A VM callback
URL cannot be completed simply by opening it on a different computer.

This integration targets user-operated local and self-hosted installations.
OpenAI documents a separate access process for paid or remotely hosted apps.

## Preview behavior and failures

Horizon uses `POST https://api.openai.com/v1/responses`, `store: false`, and
`stream: true`. It maps the system prompt to `instructions`, waits for
`response.completed`, and returns text to the existing classification, scoring,
enrichment, and JSON-validation code. Partial, failed, and incomplete responses
are never accepted as completed results.

The current preview does not accept `temperature` or `max_output_tokens`.
Consequently, Horizon's `temperature` and `max_tokens` settings (including
per-call overrides) are not sent by this provider. Custom API endpoints and
`extra_body` are rejected. Model choices come from the connected account's catalog.

Plan usage is subject to shared and app-specific limits. On a usage-limit,
permission, or account-eligibility failure, Horizon stops the AI stage instead of
retrying every item or switching that request to API billing. In-flight batch
tasks are cancelled; requests already accepted by the server may still consume
usage. Temporary service failures retain bounded stage retries. These failure
conditions can arrive after streaming has started.

If configuring `provider_chain`, set `ai.provider` to `openai-chatgpt` to supply
its selected model and account. Terminal plan/authentication errors stop the
chain; ordinary transient failures follow the explicitly configured fallback chain.

MCP/Skill `validate_config` reports local connection and permission state in
`ai.auth`; it does not prove account eligibility, current allowance, or successful
inference. Use `horizon-chatgpt check` for that verification.

## References

- [Official overview](https://developers.openai.com/siwc/token-sharing-open-source)
- [Registration and sign-in](https://developers.openai.com/siwc/token-sharing-open-source/sign-in)
- [Accounts and token renewal](https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions)
- [Models and inference](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference)
- [Preview limitations](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations)

The implementation follows the public protocol and uses the Python OpenAI SDK,
PyJWT, and filelock. It does not incorporate the Node.js SIWC DevKit source.
