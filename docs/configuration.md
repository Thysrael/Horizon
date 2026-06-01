---
layout: default
title: Configuration Guide
---

# Configuration Guide

Horizon is configured through two files: a `.env` file for API keys and a `data/config.json` file for sources, AI provider, and filtering options.

## AI Providers

Configure which AI model scores and summarizes your content.

`api_key_env` is always an environment variable name, not the API key value.
Store secrets in `.env` or your shell environment, then point `api_key_env` at
that variable:

```bash
OPENAI_API_KEY=sk-your-key
GOOGLE_API_KEY=your-gemini-key
```

When Horizon starts, environment variables have priority because
`data/config.json` does not store the secret. For local VS Code runs, create
`.env` in the repository root and launch Horizon from that same root directory.

Common API key variable names:

| Provider | `api_key_env` value |
| --- | --- |
| Anthropic | `ANTHROPIC_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Azure OpenAI | `AZURE_OPENAI_API_KEY` |
| Gemini | `GOOGLE_API_KEY` |
| MiniMax | `MINIMAX_API_KEY` |
| Aliyun DashScope | `DASHSCOPE_API_KEY` |
| Doubao | `DOUBAO_API_KEY` |
| DeepSeek | `DEEPSEEK_API_KEY` |

**Anthropic Claude**:

```json
{
  "ai": {
    "provider": "anthropic",
    "model": "claude-sonnet-4.5-20250929",
    "api_key_env": "ANTHROPIC_API_KEY",
    "throttle_sec": 0
  }
}
```

**OpenAI**:

```json
{
  "ai": {
    "provider": "openai",
    "model": "gpt-4",
    "api_key_env": "OPENAI_API_KEY",
    "throttle_sec": 0
  }
}
```

**Gemini**:

```json
{
  "ai": {
    "provider": "gemini",
    "model": "gemini-2.0-flash",
    "api_key_env": "GOOGLE_API_KEY",
    "throttle_sec": 0
  }
}
```

**Azure OpenAI**:

```json
{
  "ai": {
    "provider": "azure",
    "model": "gpt-4o-production",
    "api_key_env": "AZURE_OPENAI_API_KEY",
    "azure_endpoint_env": "AZURE_OPENAI_ENDPOINT",
    "api_version": "2024-10-21",
    "throttle_sec": 0
  }
}
```

Set `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` in your `.env`. The `model` field should be your Azure deployment name, not just the base model family name.

**MiniMax**:

```json
{
  "ai": {
    "provider": "minimax",
    "model": "MiniMax-M3",
    "api_key_env": "MINIMAX_API_KEY",
    "throttle_sec": 0
  }
}
```

Available models: `MiniMax-M3`, `MiniMax-M2.7`, `MiniMax-M2.7-highspeed`

**Aliyun DashScope** (OpenAI-compatible):

```json
{
  "ai": {
    "provider": "ali",
    "model": "qwen-plus",
    "api_key_env": "DASHSCOPE_API_KEY",
    "throttle_sec": 0
  }
}
```

Use the [DashScope compatible-mode](https://help.aliyun.com/zh/dashscope/developer-reference/use-dashscope-by-calling-openai-api) endpoint. Set `DASHSCOPE_API_KEY` in your `.env`. Optional: set `base_url` to override the default `https://dashscope.aliyuncs.com/compatible-mode/v1`.

### AI throttling

If your model has a strict per-minute request cap, you can slow the scorer down in `data/config.json`:

```json
{
  "ai": {
    "throttle_sec": 4.5
  }
}
```

- `throttle_sec`: Pause between scored items in seconds. Default is `0`.
- `4.5` is a reasonable starting point for free-tier models capped around 15 requests per minute.
- Set it back to `0` if you have enough throughput headroom and want maximum speed.

### AI Concurrency

By default, AI scoring and enrichment run one item at a time. If your API endpoint supports concurrent requests, you can increase throughput:

```json
{
  "ai": {
    "analysis_concurrency": 4,
    "enrichment_concurrency": 2
  }
}
```

- `analysis_concurrency`: Number of items scored in parallel. Default is `1`.
- `enrichment_concurrency`: Number of high-scoring items enriched in parallel. Default is `1`.
- Both values are clamped to a minimum of `1`.
- Preserve the existing retry behavior per item.
- Result ordering is preserved regardless of concurrency.
- If you also use `throttle_sec`, each concurrent task sleeps independently after finishing an item.

**Custom Base URL** (for proxies):

```json
{
  "ai": {
    "provider": "anthropic",
    "base_url": "https://your-proxy.com/v1",
    ...
  }
}
```

For OpenAI-compatible gateways, Horizon sends `temperature` by default. If a newer reasoning-style model rejects that parameter with an error such as `temperature is deprecated for this model`, Horizon retries once without it and remembers that capability for later requests.

## Information Sources

All sources are configured under the top-level `sources` key in `config.json`.

### GitHub

```json
{
  "sources": {
    "github": [
      {
        "type": "user_events",
        "username": "gvanrossum",
        "enabled": true
      },
      {
        "type": "repo_releases",
        "owner": "python",
        "repo": "cpython",
        "enabled": true
      }
    ]
  }
}
```

### Hacker News

```json
{
  "sources": {
    "hackernews": {
      "enabled": true,
      "fetch_top_stories": 30,
      "min_score": 100
    }
  }
}
```

### RSS Feeds

```json
{
  "sources": {
    "rss": [
      {
        "name": "Blog Name",
        "url": "https://example.com/feed.xml",
        "enabled": true,
        "category": "ai-ml"
      }
    ]
  }
}
```

### Reddit

```json
{
  "sources": {
    "reddit": {
      "enabled": true,
      "fetch_comments": 5,
      "subreddits": [
        {
          "subreddit": "MachineLearning",
          "sort": "hot",
          "fetch_limit": 25,
          "min_score": 10
        }
      ],
      "users": [
        {
          "username": "spez",
          "sort": "new",
          "fetch_limit": 10
        }
      ]
    }
  }
}
```

### Telegram

Telegram scraping uses the public web preview at `https://t.me/s/<channel>`, so no API key is required. Only public channels are supported.

```json
{
  "sources": {
    "telegram": {
      "enabled": true,
      "channels": [
        {
          "channel": "zaihuapd",
          "enabled": true,
          "fetch_limit": 20
        }
      ]
    }
  }
}
```

- `enabled` — enable or disable Telegram fetching globally
- `channels` — list of public Telegram channels to monitor
- `channel` — Telegram channel username only, without `@` or the full `https://t.me/` URL
- `fetch_limit` — maximum number of recent messages to inspect per channel per run (default: `20`)

### Twitter

Requires an [Apify](https://apify.com) account. Set `APIFY_TOKEN` in your `.env` file. The free tier includes $5/month of credit, enough for roughly 20,000 tweets.

```json
{
  "sources": {
    "twitter": {
      "enabled": true,
      "users": ["karpathy", "ylecun"],
      "fetch_limit": 10,
      "fetch_reply_text": false,
      "max_replies_per_tweet": 3,
      "max_tweets_to_expand": 10,
      "reply_min_likes": 5
    }
  }
}
```

- `users` — Twitter screen names to monitor, without the `@` prefix
- `fetch_limit` — maximum tweets to fetch per run (across all users combined; minimum 100 due to actor constraint)
- `fetch_reply_text` — when `true`, fetch actual reply bodies for important tweets and append them under `--- Top Comments ---` so the AI can factor in community discussion. Disabled by default.
- `max_replies_per_tweet` — maximum reply lines to append per tweet (default: 3)
- `max_tweets_to_expand` — cap on how many tweets get reply expansion per run, to control Apify credit usage (default: 10)
- `reply_min_likes` — only include replies with at least this many likes (default: 0)

The scraper uses the `altimis/scweet` actor by default. You can override it with `actor_id` if needed.

### OpenBB Financial News

OpenBB is useful when you want equity or macro news from providers such as yfinance, Benzinga, FMP, Intrinio, Tiingo, SEC, or Federal Reserve through one SDK.

Install the optional dependency before enabling the source:

```bash
uv sync --extra openbb
```

If your platform struggles to build transitive dependencies, prefer:

```bash
uv pip install --only-binary=:all: openbb openbb-benzinga
```

```json
{
  "sources": {
    "openbb": {
      "enabled": true,
      "watchlists": [
        {
          "name": "megacaps",
          "enabled": true,
          "provider": "yfinance",
          "fetch_limit": 20,
          "category": "equities",
          "symbols": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"]
        }
      ]
    }
  }
}
```

- `enabled` — enable or disable the OpenBB source globally
- `watchlists` — list of named ticker groups; each watchlist becomes one `news.company()` call per run
- `name` — label shown in Horizon metadata and selection breakdowns
- `provider` — OpenBB provider name such as `yfinance` or `benzinga`
- `fetch_limit` — maximum news rows requested for that watchlist
- `category` — optional tag stored on fetched items
- `symbols` — ticker symbols to fetch together; group symbols by provider to keep requests efficient

OpenBB provider credentials are handled by the OpenBB SDK itself, using its own environment variables or user settings. Horizon does not pass those secrets through `data/config.json`.

### OSS Insight (Trending GitHub Repos)

Pulls top star-gain repositories from the [OSS Insight](https://ossinsight.io) public API, which aggregates GitHub WatchEvents. Useful for surfacing repos that are gaining stars right now without needing to scrape GitHub Trending or query BigQuery.

```json
{
  "sources": {
    "ossinsight": {
      "enabled": true,
      "period": "past_24_hours",
      "languages": ["All", "Python", "TypeScript"],
      "keywords": [],
      "min_stars": 10,
      "max_items": 30
    }
  }
}
```

- `period` — time window for star-gain ranking. Supported: `past_24_hours`, `past_28_days`. (`past_7_days` is currently broken upstream.)
- `languages` — primary language buckets to query. Use `"All"` for the full ranking, or any GitHub language label such as `"Python"`, `"TypeScript"`, `"Rust"`, `"Jupyter Notebook"`. The scraper fans out one request per language and merges results.
- `keywords` — optional case-insensitive substrings matched against `description`, `collection_names`, and `repo_name`. Only repos containing at least one keyword pass through. Leave empty to ingest everything trending.
- `min_stars` — drop repos with fewer than this many stars gained in the period.
- `max_items` — final cap after merging and sorting by `stars_gained` descending.

No API key is required.

## Filtering

Content is scored 0-10:

- **9-10**: Groundbreaking - Major breakthroughs, paradigm shifts
- **7-8**: High Value - Important developments, deep technical content
- **5-6**: Interesting - Worth knowing but not urgent
- **3-4**: Low Priority - Generic or routine content
- **0-2**: Noise - Spam, off-topic, or trivial

```json
{
  "filtering": {
    "ai_score_threshold": 7.0,
    "time_window_hours": 24
  }
}
```

- `ai_score_threshold`: Only include content scoring >= this value
- `time_window_hours`: Fetch content from last N hours

## Environment Variable Substitution

Any string value in `data/config.json` supports `${VAR_NAME}` syntax. Variables are expanded at runtime from the environment (including values loaded from `.env`). This lets you keep secrets, tenant-specific endpoints, and private URLs out of the checked-in JSON file.

Example:

```json
{
  "ai": {
    "base_url": "${HORIZON_AI_BASE_URL}"
  },
  "sources": {
    "rss": [
      {
        "name": "LWN.net",
        "url": "https://lwn.net/headlines/full_text?key=${LWN_KEY}",
        "enabled": true
      }
    ]
  },
  "webhook": {
    "url_env": "HORIZON_WEBHOOK_URL",
    "headers": "Authorization: Bearer ${HORIZON_WEBHOOK_TOKEN}"
  }
}
```

- `${NAME}` is replaced only when `NAME` is a valid identifier like `LWN_KEY` or `HORIZON_AI_BASE_URL`.
- Unset variables are left as `${NAME}` instead of becoming an empty string, so configuration mistakes fail loudly downstream.
- Expansion is recursive through dicts, lists, and tuples; non-string values are left unchanged.

## Email Subscription

Email delivery is optional and disabled unless `email.enabled` is `true`. Horizon uses SMTP to send daily summaries and IMAP to check subscribe/unsubscribe requests.

```json
{
  "email": {
    "enabled": true,
    "smtp_server": "smtp.qq.com",
    "smtp_port": 465,
    "smtp_username": null,
    "imap_enabled": true,
    "imap_server": "imap.qq.com",
    "imap_port": 993,
    "email_address": "xxx@qq.com",
    "password_env": "EMAIL_PASSWORD",
    "sender_name": "Horizon Daily",
    "subscribe_keyword": "SUBSCRIBE",
    "unsubscribe_keyword": "UNSUBSCRIBE"
  }
}
```

- `enabled`: Turns email subscription handling and daily email delivery on or off.
- `smtp_server` / `smtp_port`: SMTP server used to send emails.
- `smtp_username`: Optional SMTP login username. If omitted, Horizon uses `email_address`.
- `imap_enabled`: Turns IMAP subscribe/unsubscribe checks on or off. Set it to `false` for send-only SMTP providers.
- `imap_server` / `imap_port`: IMAP server used to scan incoming subscription requests when `imap_enabled` is `true`.
- `email_address`: Sender account and mailbox checked for subscription requests.
- `password_env`: Environment variable containing the email password or app password. Defaults to `EMAIL_PASSWORD`.
- `sender_name`: Display name shown in sent emails.
- `subscribe_keyword` / `unsubscribe_keyword`: Keywords Horizon looks for in incoming email subjects.

Resend SMTP example:

```json
{
  "email": {
    "enabled": true,
    "smtp_server": "smtp.resend.com",
    "smtp_port": 465,
    "smtp_username": "resend",
    "password_env": "RESEND_API_KEY",
    "imap_enabled": false,
    "imap_server": "",
    "imap_port": 993,
    "email_address": "noreply@example.com",
    "sender_name": "Horizon Daily"
  }
}
```

Set `RESEND_API_KEY` in `.env`. Recipients are loaded from `data/subscribers.json`.

## Webhook Notification

Webhook notification is optional and disabled unless `webhook.enabled` is `true`. Horizon can call Feishu/Lark, DingTalk, Slack, Discord, or any custom webhook endpoint when the pipeline succeeds or fails.

```json
{
  "webhook": {
    "enabled": true,
    "url_env": "HORIZON_WEBHOOK_URL",
    "delivery": "summary",
    "overview_position": "first",
    "platform": "generic",
    "layout": "markdown",
    "fallback_layout": "markdown",
    "languages": null,
    "request_body": {
      "text": "#{message_title}\n#{summary}"
    },
    "headers": ""
  }
}
```

- `enabled`: Turns webhook delivery on or off. The default is `false`.
- `url_env`: Environment variable that contains the webhook URL. For example, set `HORIZON_WEBHOOK_URL=https://...` in `.env`.
- `delivery`: Controls how messages are sent. Use `summary` for one full message, or `summary_and_items` for one overview message followed by one message per selected item.
- `overview_position`: Controls where the overview is sent in `summary_and_items` mode. Use `first` for the traditional order, or `last` to send item details in reverse and keep the overview as the newest chat message.
- `platform`: Optional webhook platform hint. Use `generic` by default, or `feishu` / `lark` to enable platform-specific card rendering.
- `layout`: Controls the message layout. Use `markdown` for templated Markdown delivery, or `collapsible` with `platform: "feishu"` / `"lark"` for a single Feishu Card JSON 2.0 message with each item in a collapsed panel.
- `fallback_layout`: Reserved fallback layout for unsupported platform/layout combinations. The current safe fallback is `markdown`.
- `languages`: Optional webhook-only language filter. Use `["zh"]` or `["en"]` to send only selected languages; use `null` or omit it to send all configured `ai.languages`.
- `request_body`: Optional request body. If empty, Horizon sends a `GET` request. If provided, Horizon sends a `POST` request.
- `headers`: Optional custom headers, one `Key: Value` pair per line.

When `request_body` is a JSON object or array, Horizon renders placeholders and serializes it as JSON. When it is a string, Horizon renders it directly and detects JSON if the rendered string is valid JSON.

### Delivery Modes And Layouts

`delivery` controls how many webhook messages Horizon sends:

- `summary`: Sends one message containing the full daily summary. This is simple, but some chat platforms may reject long messages.
- `summary_and_items`: Sends one overview message plus one message per selected item. In each item message, `#{summary}` contains only that item's Markdown body. This is useful for platforms that reject or truncate long messages.

`layout` controls how each message is rendered:

- `markdown`: Uses your `request_body` template for each message. This is the default and works with generic webhooks, DingTalk, Slack, Discord, Feishu, and Lark.
- `collapsible`: Currently supported for `platform: "feishu"` or `"lark"`. Horizon ignores `request_body` and builds one Feishu/Lark Card JSON 2.0 message with each item in a collapsed panel.

For platforms without a platform-specific layout, keep `layout: "markdown"` and choose the message count with `delivery`.

Example `summary_and_items` Markdown delivery config:

```json
{
  "webhook": {
    "enabled": true,
    "url_env": "HORIZON_WEBHOOK_URL",
    "delivery": "summary_and_items",
    "overview_position": "last",
    "platform": "generic",
    "layout": "markdown",
    "request_body": {
      "text": "#{message_title}\n\n#{summary?limit=3000&split=---}"
    }
  }
}
```

With `summary_and_items`, Horizon sends one overview plus one message per selected item. `overview_position: "last"` sends item messages first and keeps the overview as the newest chat message; omit it or set `"first"` to send the overview first.

### Webhook Templates

Available variables:

| Variable | Description |
|----------|-------------|
| `#{date}` | Report date, for example `2026-04-24` |
| `#{language}` | Language code, such as `en` or `zh` |
| `#{important_items}` | Number of items that passed the score threshold |
| `#{all_items}` | Total number of fetched items |
| `#{result}` | `success` or `failed` |
| `#{timestamp}` | Unix timestamp |
| `#{message_title}` | Message title, such as the daily title, overview title, or item title |
| `#{message_kind}` | Message kind: `summary`, `overview`, `item`, `failure`, or `manual` |
| `#{summary}` | Message Markdown. In `summary_and_items` mode this is the overview or one item body, depending on the message |

When `delivery` is `summary_and_items`, item messages also include:

| Variable | Description |
|----------|-------------|
| `#{item_index}` | 1-based item number |
| `#{item_count}` | Total number of item messages |
| `#{item_title}` | Current item title |
| `#{item_url}` | Current item URL |
| `#{item_score}` | Current item AI score |

For webhook delivery, Horizon flattens HTML disclosure blocks such as `<details><summary>...</summary>` in `#{summary}` into plain Markdown link lists. This makes the generated summary easier to render in chat products. Saved Markdown files, GitHub Pages, and email content are unchanged.

Use `#{key?limit=N&split=DELIM}` to truncate long values by splitting on `DELIM` and keeping segments until the total character count reaches `N`.

```text
#{summary?limit=3000&split=---}
```

### DingTalk

In DingTalk, create a custom group robot and use a custom keyword such as `Horizon`. The keyword must appear in the body content.

```json
{
  "msgtype": "markdown",
  "markdown": {
    "title": "Horizon #{date} Daily",
    "text": "Horizon result: #{result}\n\nHorizon important items: #{important_items}/#{all_items}\n\n#{summary}"
  }
}
```

### Feishu / Lark

In Feishu or Lark, create a custom group robot and use a custom keyword such as `Horizon`. The keyword must appear in the body content.

Use Card JSON 2.0 for Markdown rendering. The card must include `"schema": "2.0"` and put rich-text Markdown components under `card.body.elements`.

To keep the group chat compact while still allowing readers to browse the full briefing inside Feishu, use the collapsible layout:

```json
{
  "webhook": {
    "enabled": true,
    "url_env": "HORIZON_WEBHOOK_URL",
    "platform": "feishu",
    "layout": "collapsible",
    "fallback_layout": "markdown",
    "languages": ["zh"]
  }
}
```

With this layout, Horizon sends one interactive card containing the overview and one collapsed panel per selected item. Each panel can be expanded in Feishu to read the full item detail. The regular `request_body` template is ignored for this rendered card.

```json
{
  "msg_type": "interactive",
  "card": {
    "schema": "2.0",
    "config": {
      "wide_screen_mode": true
    },
    "header": {
      "title": {
        "tag": "plain_text",
        "content": "#{message_title}"
      },
      "template": "blue"
    },
    "body": {
      "elements": [
        {
          "tag": "markdown",
          "content": "Horizon result: #{result}\nHorizon important items: #{important_items}/#{all_items}"
        },
        {
          "tag": "hr"
        },
        {
          "tag": "markdown",
          "content": "#{summary}"
        }
      ]
    }
  }
}
```

## Static Site

Horizon writes generated summaries to `data/summaries/` and copies publishable Markdown into `docs/` for the GitHub Pages site. The repository includes a ready-to-use workflow at `.github/workflows/daily-summary.yml`.

To use GitHub Pages, enable Pages for the repository and run the scheduled workflow or trigger it manually. The generated site is built from the `docs/` directory.

## MCP Server

Horizon includes an MCP server for AI assistants and MCP-compatible clients.

```bash
uv run horizon-mcp
```

Available tools include `hz_validate_config`, `hz_fetch_items`, `hz_score_items`, `hz_filter_items`, `hz_enrich_items`, `hz_generate_summary`, and `hz_run_pipeline`.

See [`src/mcp/README.md`](../src/mcp/README.md) for the full tool reference and [`src/mcp/integration.md`](../src/mcp/integration.md) for client setup.
