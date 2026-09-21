# WeChat Delivery (iLink Bot)

[中文](wechat_zh.md)

Horizon can push the daily briefing straight into your personal WeChat through
the official **iLink Bot API** (`https://ilinkai.weixin.qq.com`) — the protocol
behind Tencent's `openclaw-weixin` channel. There is no webhook URL, no app
registration and no public server: you scan a QR code once, and Horizon talks
to WeChat's servers directly.

This guide is the operations manual. Configuration fields are summarised in the
[Configuration Guide](configuration.md#wechat-notification).

---

## 1. How it works

```
you ──(any message)──▶ WeChat bot chat ──▶ ilinkai.weixin.qq.com ◀──(getupdates / sendmessage)── Horizon
```

- **Login.** `horizon-wechat login` fetches a QR code. Scanning it binds a bot to
  your WeChat account and gives Horizon a `bot_token`.
- **Context token.** Every message you send the bot carries a `context_token`.
  A bot may only send messages that echo a token it received, so Horizon must
  hear from you once before it can push, and it keeps the newest token on disk.
- **Reply budget.** WeChat treats bot messages as replies: **for each message
  you send, the bot may send at most 10 messages back.** The 11th is refused
  (`ret=-2 prepare failed`) until you send the bot anything again. This is
  enforced by WeChat and cannot be lifted from the bot side; Horizon budgets
  around it (see [§5](#5-the-reply-budget)).
- **Horizon is offline between runs.** The scheduled job connects, delivers
  and exits; chat commands are answered when the inbox is next read — instantly
  only if you also run `horizon-wechat listen` (see [§3](#important-when-commands-are-answered)).
- **Rendering.** Bot chats render a Markdown subset: headings, bold, links,
  inline and fenced code, tables, quotes and rules. Raw HTML is shown as text
  and nothing can be folded, so Horizon flattens its HTML blocks, drops images
  and unwraps italics around Chinese text before sending.

Everything Horizon needs lives in the data directory:

| File | Purpose |
|------|---------|
| `data/wechat_session.json` | Bot token, your user id, current context token, reply counter, chosen style. **A credential** — `data/wechat_*.json` is git-ignored and written with mode `0600`. |
| `data/wechat_briefing-<lang>.json` | The last delivered briefing, cached so the `日报` command can replay it without fetching or calling the AI. |

## 2. Setup

### 2.1 Enable it in `config.json`

```json
{
  "wechat": {
    "enabled": true,
    "style": "summary",
    "languages": ["zh"]
  }
}
```

`style` is the default layout (`summary` or `overview`, see [§4](#4-message-styles));
`languages` limits WeChat to some of your `ai.languages`. Leave the rest at
their defaults unless you have a reason not to.

### 2.2 Connect your WeChat

```bash
uv run horizon-wechat login
```

1. A QR code is printed (plus a fallback link you can open on a phone). Scan it
   with WeChat and confirm.
2. WeChat opens a bot chat. **Send the bot any message** — `hi` is fine. This
   gives Horizon its first context token.
3. Horizon replies with a short welcome that explains the commands and the
   reply budget, and saves `data/wechat_session.json`.

If the terminal cannot show the QR code, use the printed link. If WeChat asks
for a verification code, the command prompts for it. `--force` logs in again
even when a session exists; if the bot is already bound to this machine's
token, WeChat reports that and the existing session is kept.

### 2.3 Check and test

```bash
uv run horizon-wechat status              # session, style, replies left
uv run horizon-wechat test --dry-run      # preview exactly what would be sent
uv run horizon-wechat test --lang zh      # send a sample briefing (needs wechat.enabled)
uv run horizon-wechat test --style overview   # try the other layout for this test only
```

Sample sends never overwrite the `日报` replay cache, so testing does not
replace a real briefing.

### 2.4 Run it on a schedule

WeChat is a delivery target, not a trigger: every scheduled `horizon` run
delivers that day's briefing right after email and webhook delivery. Before
sending it briefly checks the bot inbox (about 8 seconds) to pick up a newer
context token and any commands you sent since the last run. You never need to
run anything by hand once the schedule is in place.

```bash
# cron on an always-on machine, 08:00 every day
0 8 * * * cd /path/to/Horizon && uv run horizon --hours 24 >> logs/horizon.log 2>&1
```

or `docker compose run --rm horizon` from the host's cron. One requirement:
the **data directory must persist between runs**, because the session file
carries mutable state (context token, reply counter, cursor). That rules out
ephemeral runners such as the stock GitHub Actions workflow unless you persist
`data/` yourself; a server, NAS, Raspberry Pi or Docker host is the natural
home for the WeChat channel.

## 3. Chat commands

Type these in the bot chat. Chinese and English forms are equivalent; the bot
answers in Chinese when `zh` is among your languages, otherwise in English.

| You send | Bot does | Costs a reply? |
|----------|----------|:--:|
| `日报` · `新闻` · `news` | Re-sends the last delivered briefing in your current style | yes (1–N) |
| `1` | Switch to `summary` (whole briefing in one message) | yes (1) |
| `2` | Switch to `overview` (overview, then one message per item) | yes (1) |
| `切换` · `switch` | Toggle between the two styles | yes (1) |
| `样式` · `/style` · `s` | Show the style menu with the current style marked and replies left | yes (1) |
| `帮助` · `/help` · `h` · `?` | Explain the commands and show replies left | yes (1) |
| anything else | Nothing — no reply, but your message resets the reply budget | no |

Style changes are stored in the session file, take precedence over
`wechat.style`, and apply from the next briefing. Replies are only answered
when Horizon reads the inbox — at the daily run, on `horizon-wechat status
--refresh`, or immediately when the listener below is running.

### Important: when commands are answered

> **Horizon is not online between runs.** The daily `horizon` job connects,
> delivers, and exits. Commands you type in the chat are only *seen* when
> something reads the inbox. If you want the bot to answer **instantly**, you
> must keep a second, long-running process alive: `horizon-wechat listen`.

| | Daily job only | Daily job **+ `horizon-wechat listen`** |
|---|---|---|
| Receiving the briefing | ✅ every day | ✅ every day |
| `1` / `2` style switch | applied at the next run (that day's briefing already uses the new style, but there is no immediate confirmation) | confirmed within seconds, applied to that day's briefing |
| `日报` replay | sent at the next run — which delivers a fresh briefing anyway, so of little use | sent within seconds |
| `帮助` / `样式` | answered at the next run | answered within seconds |
| Reply budget reset | identical (a WeChat-side rule; it does not depend on Horizon being online) | identical |

So the listener is an **optional experience upgrade**; receiving the daily
briefing never depends on it. Running it is cheap — an idle Python process
holding one long-poll HTTP connection:

```bash
uv run horizon-wechat listen
```

Keep it on the same machine as the cron job, supervised so it restarts: a
systemd service, a `tmux` session, or the commented `horizon-wechat` service
in `docker-compose.yml` (`restart: unless-stopped`). It shares the session file
with `horizon`, which re-reads the file before every delivery, so a style you
switch in chat is honoured by that night's push. Exactly one listener per data
directory — two would compete for the same inbox cursor.

A possible follow-up is letting the listener also run the daily job
(`horizon-wechat listen --daily-at 08:00`), so a single process covers both.

## 4. Message styles

| Style | Messages per briefing | Best for |
|-------|-----------------------|----------|
| `summary` (default) | 1–4 (whole briefing, split at `chunk_size`) | Most people. Fewest messages, so the budget lasts longest. |
| `overview` | 1 + number of items | Skimming: the overview lists every item with its score and link; each item follows as its own message, so you can stop reading at any point. |

Both are the same Markdown Horizon writes to `data/summaries/` and publishes
to GitHub Pages; only the packaging differs.

## 5. The reply budget

Because WeChat allows 10 bot replies per message you send:

- The session file counts the messages sent in the current conversation and
  resets the count whenever you message the bot. `horizon-wechat status`,
  `帮助` and `样式` all show the remaining number.
- When a briefing needs more messages than remain, `overview` items are packed
  into fewer messages (each still ≤ `chunk_size`) so the briefing is never cut
  off halfway.
- When two or fewer replies would remain after a delivery, the last message
  ends with a reminder: *reply with anything to keep receiving Horizon*.
- If WeChat still refuses a message, `horizon` logs the reason; the next run
  after you reply succeeds.

Practical rule of thumb: with `summary`, a reader who never replies keeps
receiving briefings for about three days; a single `1`, `日报` or `hi` resets
the clock. The welcome message and the low-budget footer both say so.

## 6. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `WeChat enabled but 'data/wechat_session.json' does not exist` | Not logged in | `horizon-wechat login` |
| `WeChat session not ready (no context token yet …)` | You never messaged the bot | Send it any message, then `horizon-wechat status --refresh` |
| `WeChat refused the message (ret=-2)` | Reply budget for this conversation used up | Send the bot any message; Horizon's next run succeeds |
| `errcode -14 session timeout` on the inbox check | WeChat closed the bot's *receive* session (seen after long polls were dropped abruptly). Sending usually still works, so the briefing is still delivered; chat commands are not read until the session is back | Wait — WeChat re-opens it after a while — or `horizon-wechat login --force` for a fresh session |
| Messages arrive but look wrong | HTML or unsupported Markdown | Report it — `format_markdown_for_wechat` in `src/services/wechat.py` is where WeChat-specific cleanup lives |
| Commands are answered only at the next daily run | Horizon is offline between runs; no listener | Keep `horizon-wechat listen` running alongside the cron job (see §3) |

## 7. Protocol notes (for contributors)

Verified against Tencent's reference client `@tencent-weixin/openclaw-weixin`
2.4.9 and its `docs/protocol_zh_CN.md`:

- Endpoints: `POST ilink/bot/get_bot_qrcode?bot_type=3`, `GET ilink/bot/get_qrcode_status`,
  `POST ilink/bot/getupdates` (long poll, ~35 s), `POST ilink/bot/sendmessage`.
- Headers: `AuthorizationType: ilink_bot_token`, `Authorization: Bearer <bot_token>`,
  `X-WECHAT-UIN` (base64 of a random uint32 decimal string), `iLink-App-Id: bot`,
  `iLink-App-ClientVersion`. Every authenticated POST carries
  `base_info: {channel_version, bot_agent}`; Horizon identifies itself as `Horizon/<version>`.
- Text messages: `message_type: 2`, `message_state: 2`, `item_list: [{type: 1, text_item: {text}}]`,
  plus `context_token`. Practical text limit 4000 characters.
- Observed limits (2026-09): 10 bot replies per inbound user message; `ret=-2`
  when exceeded; `errcode -14` for a stale bot token. Whether the budget also
  resets on a calendar day has not been confirmed.
- Not available: cards, buttons, collapsible content, HTML rendering, or any
  way to push without a prior user message. "Follow once, receive forever"
  semantics belong to Official Accounts or WeCom application messages, which
  are different products.

Client code: `src/services/wechat.py` (`ILinkClient`, `WeChatSession`,
`WeChatNotifier`), CLI: `src/services/wechat_cli.py`, message splitting shared
with webhooks: `src/services/delivery.py`.
