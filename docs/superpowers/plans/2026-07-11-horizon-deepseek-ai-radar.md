# Horizon + DeepSeek AI Information Radar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Configure the local Horizon checkout as a Chinese AI-engineering news radar powered by the official DeepSeek API, with local Markdown output, Feishu delivery, Codex MCP access, and a daily 08:30 run.

**Architecture:** Keep Horizon's upstream application code unchanged. Store non-secret runtime choices in ignored `data/config.json`, store secrets only in ignored `.env`, register the built-in stdio MCP server in project `.codex/config.toml`, and create the daily automation only after one verified live run.

**Tech Stack:** Python 3.11+, uv, Horizon, DeepSeek OpenAI-compatible API, Codex MCP, Feishu webhook, Markdown

---

## File map

- Create `data/config.json`: ignored local runtime configuration for DeepSeek, sources, filtering, and Feishu.
- Create `.codex/config.toml`: tracked project configuration that registers the Horizon MCP server; contains no secrets.
- Create `.env`: ignored local secret file created by the user through silent terminal input.
- Produce `data/summaries/*.md`: ignored generated Chinese daily reports.
- Produce `data/mcp-runs/`: ignored staged MCP artifacts.
- Modify no files under `src/` or `tests/`.

### Task 1: Establish the clean baseline

**Files:**
- Verify: `pyproject.toml`
- Verify: `.gitignore`
- Test: `tests/`

- [ ] **Step 1: Confirm the toolchain and repository state**

Run:

```bash
cd /Users/tianzhize/.codex/worktrees/770a/workbench/Horizon
uv --version
git status --short
```

Expected: `uv 0.10.8` or newer; only plan/design documentation is tracked and committed; no unrelated changes.

- [ ] **Step 2: Install the project and development dependencies**

Run:

```bash
uv sync --extra dev
```

Expected: uv creates or updates `.venv` using Python 3.11+ and installs Horizon plus pytest dependencies without an error.

- [ ] **Step 3: Run the upstream test suite**

Run:

```bash
uv run pytest
```

Expected: all existing tests pass. If a test fails, stop configuration work and diagnose the baseline failure before changing project files.

### Task 2: Create the ignored Horizon runtime configuration

**Files:**
- Create: `data/config.json`
- Verify: `src/models.py`
- Verify: `src/ai/client.py`

- [ ] **Step 1: Create `data/config.json` with the approved settings**

Write exactly this JSON:

```json
{
  "version": "1.0",
  "ai": {
    "provider": "deepseek",
    "model": "deepseek-v4-flash",
    "base_url": "https://api.deepseek.com",
    "api_key_env": "DEEPSEEK_API_KEY",
    "temperature": 0.3,
    "max_tokens": 8192,
    "throttle_sec": 1,
    "languages": ["zh"],
    "analysis_concurrency": 3,
    "enrichment_concurrency": 2
  },
  "sources": {
    "github": [
      {
        "type": "user_events",
        "username": "karpathy",
        "enabled": true
      },
      {
        "type": "repo_releases",
        "owner": "openai",
        "repo": "codex",
        "enabled": true
      },
      {
        "type": "repo_releases",
        "owner": "openai",
        "repo": "openai-agents-python",
        "enabled": true
      },
      {
        "type": "repo_releases",
        "owner": "modelcontextprotocol",
        "repo": "servers",
        "enabled": true
      },
      {
        "type": "repo_releases",
        "owner": "vllm-project",
        "repo": "vllm",
        "enabled": true
      },
      {
        "type": "repo_releases",
        "owner": "sgl-project",
        "repo": "sglang",
        "enabled": true
      }
    ],
    "hackernews": {
      "enabled": true,
      "fetch_top_stories": 30,
      "min_score": 100
    },
    "rss": [
      {
        "name": "Simon Willison",
        "url": "https://simonwillison.net/atom/everything/",
        "enabled": true,
        "category": "ai-engineering"
      },
      {
        "name": "GitHub Trending Daily",
        "url": "https://mshibanami.github.io/GitHubTrendingRSS/daily/all.xml",
        "enabled": true,
        "category": "developer-tools"
      },
      {
        "name": "SemiAnalysis",
        "url": "https://newsletter.semianalysis.com/feed",
        "enabled": true,
        "category": "ai-infrastructure"
      }
    ],
    "reddit": {
      "enabled": true,
      "subreddits": [
        {
          "subreddit": "MachineLearning",
          "enabled": true,
          "sort": "hot",
          "time_filter": "day",
          "fetch_limit": 10,
          "min_score": 30
        },
        {
          "subreddit": "LocalLLaMA",
          "enabled": true,
          "sort": "hot",
          "time_filter": "day",
          "fetch_limit": 10,
          "min_score": 30
        }
      ],
      "users": [],
      "fetch_comments": 5
    },
    "telegram": {
      "enabled": true,
      "channels": [
        {
          "channel": "zaihuapd",
          "enabled": true,
          "fetch_limit": 20
        }
      ]
    },
    "ossinsight": {
      "enabled": true,
      "period": "past_24_hours",
      "languages": ["Python", "TypeScript", "Rust"],
      "keywords": ["agent", "llm", "mcp", "ai", "model", "inference"],
      "min_stars": 10,
      "max_items": 25
    },
    "gdelt": {
      "enabled": false,
      "query": "artificial intelligence",
      "mode": "ArtList",
      "max_records": 75,
      "timespan": null,
      "language": null,
      "country": null,
      "category": "news"
    },
    "google_news": {
      "enabled": false,
      "query": "artificial intelligence",
      "language": "en",
      "country": "US",
      "ceid": null,
      "max_results": 100,
      "category": "news"
    }
  },
  "filtering": {
    "ai_score_threshold": 7.5,
    "time_window_hours": 24,
    "max_items": 15,
    "category_groups": {},
    "default_group": "other",
    "default_group_limit": null
  },
  "webhook": {
    "enabled": true,
    "url_env": "HORIZON_WEBHOOK_URL",
    "delivery": "summary_and_items",
    "overview_position": "last",
    "platform": "feishu",
    "layout": "collapsible",
    "fallback_layout": "markdown",
    "languages": ["zh"],
    "request_body": {},
    "headers": ""
  }
}
```

- [ ] **Step 2: Validate JSON syntax without reading secrets**

Run:

```bash
uv run python -m json.tool data/config.json >/dev/null
```

Expected: exit code 0 and no output.

- [ ] **Step 3: Confirm the runtime configuration is ignored**

Run:

```bash
git check-ignore -v data/config.json
git status --short
```

Expected: `.gitignore` reports the `data/config.json` rule and Git does not list the runtime config.

### Task 3: Register Horizon as a project MCP server

**Files:**
- Create: `.codex/config.toml`
- Test: `scripts/check_mcp.py`

- [ ] **Step 1: Create the project Codex configuration**

Write exactly:

```toml
[mcp_servers.horizon]
command = "uv"
args = ["run", "horizon-mcp"]
cwd = "/Users/tianzhize/.codex/worktrees/770a/workbench/Horizon"
```

- [ ] **Step 2: Run Horizon's MCP smoke check**

Run:

```bash
uv run python scripts/check_mcp.py
```

Expected: the script reports successful module import, path resolution, config loading, and metrics access. A missing `DEEPSEEK_API_KEY` may be reported only if the script attempts provider initialization; do not add a fake key.

- [ ] **Step 3: Commit only the non-secret Codex configuration**

Run:

```bash
git add .codex/config.toml
git diff --cached --check
git commit -m "chore: register Horizon MCP for Codex"
```

Expected: one commit containing only `.codex/config.toml`.

### Task 4: Collect secrets through local silent input

**Files:**
- Create: `.env`

- [ ] **Step 1: Ask the user to create the ignored secret file locally**

The user runs this in their own terminal from the repository root; secrets are never pasted into chat:

```zsh
cd /Users/tianzhize/.codex/worktrees/770a/workbench/Horizon
umask 077
read -s "DEEPSEEK_API_KEY?DeepSeek API Key: "; echo
read -s "HORIZON_WEBHOOK_URL?Feishu webhook URL: "; echo
printf 'DEEPSEEK_API_KEY=%s\nHORIZON_WEBHOOK_URL=%s\n' "$DEEPSEEK_API_KEY" "$HORIZON_WEBHOOK_URL" > .env
unset DEEPSEEK_API_KEY HORIZON_WEBHOOK_URL
chmod 600 .env
```

Expected: the terminal does not echo either value and creates a mode-600 `.env` file.

- [ ] **Step 2: Verify secret presence without printing values**

Run:

```bash
test "$(stat -f '%Lp' .env)" = "600"
awk -F= '$1=="DEEPSEEK_API_KEY" && length($2)>8 {deepseek=1} $1=="HORIZON_WEBHOOK_URL" && length($2)>20 {feishu=1} END {exit !(deepseek && feishu)}' .env
git check-ignore -v .env
```

Expected: all commands exit 0, `.gitignore` identifies the `.env` rule, and no secret value is printed.

### Task 5: Validate the configured pipeline

**Files:**
- Verify: `data/config.json`
- Verify: `.env`
- Test: `scripts/check_mcp.py`

- [ ] **Step 1: Run the MCP/configuration smoke check with real environment variables**

Run:

```bash
uv run python scripts/check_mcp.py
```

Expected: all smoke checks pass.

- [ ] **Step 2: Confirm no secret-bearing file is tracked**

Run:

```bash
git ls-files --error-unmatch .env >/dev/null 2>&1 && exit 1 || true
git ls-files --error-unmatch data/config.json >/dev/null 2>&1 && exit 1 || true
git status --short
```

Expected: neither ignored file is tracked; only intentional tracked changes, if any, are shown.

### Task 6: Perform the first live DeepSeek and Feishu run

**Files:**
- Produce: `data/summaries/*.md`
- Produce: `data/seen.json`

- [ ] **Step 1: Run a bounded first collection**

Run:

```bash
uv run horizon --hours 24
```

Expected: Horizon fetches enabled sources, calls `deepseek-v4-flash`, selects at most 15 items, generates Chinese Markdown, and reports Feishu delivery success.

- [ ] **Step 2: Verify a non-empty Chinese report without dumping its contents**

Run:

```bash
latest="$(find data/summaries -type f -name '*.md' -print | sort | tail -1)"
test -n "$latest"
test -s "$latest"
LC_ALL=C grep -q '[^ -~]' "$latest"
printf '%s\n' "$latest"
```

Expected: exit code 0 and one relative Markdown path is printed.

- [ ] **Step 3: Ask the user to confirm Feishu receipt**

Expected: the user confirms that one collapsible Chinese Horizon card arrived. If local Markdown exists but Feishu failed, preserve the report and diagnose only the webhook stage.

### Task 7: Create the verified daily automation

**Files:**
- External Codex automation record; no repository file change.

- [ ] **Step 1: Create the recurring task only after Task 6 passes**

Create a daily automation at 08:30 in `Asia/Shanghai` with this prompt:

```text
在 /Users/tianzhize/.codex/worktrees/770a/workbench/Horizon 运行 `uv run horizon --hours 24`。验证 data/summaries 下生成了非空中文 Markdown，并检查飞书推送结果。成功时报告生成文件路径和入选条目数；失败时说明失败阶段，保留已生成的本地产物，不修改信息源或密钥配置。
```

Expected: automation is enabled, scheduled daily at 08:30, and points to this Horizon checkout.

- [ ] **Step 2: Final verification**

Run:

```bash
git status --short
git log -3 --oneline
```

Expected: the repository is clean; design, plan, and Codex MCP commits are present; `.env`, `data/config.json`, summaries, and MCP run artifacts remain ignored.
