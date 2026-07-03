# GitHub Actions 部署指南

使用 GitHub Actions 自动运行 Horizon（基于 Agnes AI），并通过邮件推送日报。

---

## 目录

1. [前置准备](#1-前置准备)
2. [Fork 仓库](#2-fork-仓库)
3. [配置 Secrets](#3-配置-secrets)
4. [配置邮件推送](#4-配置邮件推送)
5. [自定义数据源](#5-自定义数据源)
6. [启用 GitHub Pages](#6-启用-github-pages)
7. [工作流说明](#7-工作流说明)
8. [手动触发](#8-手动触发)
9. [验证部署](#9-验证部署)
10. [故障排查](#10-故障排查)

---

## 1. 前置准备

- **GitHub 账号** — 免费版即可
- **Agnes AI API Key** — 从 https://agnes-ai.com 获取
- **163 邮箱**（SMTP 发信 + IMAP 收订阅请求）— 用于邮件推送
- （可选）**Webhook URL** — 飞书/Discord/Slack 推送

---

## 2. Fork 仓库

1. 访问 https://github.com/Thysrael/Horizon
2. 点击右上角 **Fork** → **Create fork**
3. 在复刻后的仓库中操作

> 私有仓库也可用，GitHub Actions 完全支持。

---

## 3. 配置 Secrets

进入你的仓库 **Settings → Secrets and variables → Actions**，点击 **New repository secret**。

### 必需

| Secret | 对应配置 | 获取方式 |
|--------|---------|---------|
| `AGNES_API_KEY` | AI 推理密钥 | 在 https://agnes-ai.com 注册获取 |

### 可选

| Secret | 对应配置 | 说明 |
|--------|---------|------|
| `EMAIL_PASSWORD` | 163 邮箱授权码 | 163 邮箱 → 设置 → POP3/SMTP/IMAP → 新增授权码 |
| `HORIZON_WEBHOOK_URL` | Webhook 推送地址 | 飞书/Discord/Slack Bot |

---

## 4. 配置邮件推送

### 4.1 整体流程

```
订阅者 (outlook.com) ──── SUBSCRIBE 邮件 ────→ 163 邮箱 (IMAP)
                                                        ↓
163 邮箱 (SMTP) ──────── 日报 ──────────────→ 订阅者 (outlook.com)
```

Horizon 只登录 **163 邮箱**（同时负责 SMTP 发信和 IMAP 收订阅请求）。订阅者用任意邮箱（如 Outlook）发送 SUBSCRIBE 邮件到 163 邮箱即可，Horizon **不会登录订阅者的邮箱**。

### 4.2 获取 163 授权码

1. 登录 163 邮箱 → **设置** → **POP3/SMTP/IMAP**
2. 开启 **IMAP/SMTP 服务**（需两者都开）
3. 按提示新增**授权码**（16 位字母，记下它）
4. 将该授权码添加为 GitHub Secret，名称 `EMAIL_PASSWORD`

### 4.3 修改配置文件

编辑 `data/config.github.json`，SMTP 和 IMAP 都用 163 邮箱：

```json
"email": {
  "enabled": true,
  "smtp_server": "smtp.163.com",
  "smtp_port": 465,
  "imap_server": "imap.163.com",
  "imap_port": 993,
  "email_address": "你的163邮箱@163.com",
  "sender_name": "Horizon Daily",
  "password_env": "EMAIL_PASSWORD",
  "subscribe_keyword": "SUBSCRIBE",
  "unsubscribe_keyword": "UNSUBSCRIBE",
  "imap_enabled": true
}
```

### 4.4 订阅机制

- 订阅者用任意邮箱向 `你的163邮箱@163.com` 发送主题为 `SUBSCRIBE` 的邮件 → 自动加入订阅列表
- 发送主题为 `UNSUBSCRIBE` 的邮件 → 自动移除
- 每次运行后，Horizon 通过 163 SMTP 向所有订阅者发送日报

---

## 5. 自定义数据源

### 5.1 编辑配置文件

`data/config.github.json` 的 `sources` 字段控制数据源：

```json
{
  "sources": {
    "github": [
      { "type": "user_events", "username": "karpathy", "enabled": true },
      { "type": "repo_releases", "owner": "torvalds", "repo": "linux", "enabled": true }
    ],
    "hackernews": { "enabled": true, "fetch_top_stories": 30, "min_score": 150 },
    "rss": [
      { "name": "My Blog", "url": "https://example.com/feed.xml", "enabled": true }
    ],
    "reddit": {
      "enabled": true,
      "subreddits": [
        { "subreddit": "MachineLearning", "enabled": true, "sort": "hot", "fetch_limit": 10, "min_score": 60 }
      ]
    },
    "telegram": {
      "enabled": true,
      "channels": [
        { "channel": "zaihuapd", "enabled": true, "fetch_limit": 20 }
      ]
    }
  }
}
```

### 5.2 使用预设源

参考 `data/presets.json`（278 条预设，覆盖 AI/ML、开源、系统、中文技术等领域），将喜欢的源复制到 `config.github.json`。

---

## 6. 启用 GitHub Pages

1. 进入仓库 **Settings → Pages**
2. **Source** 选择 **Deploy from a branch**
3. **Branch** 选择 `gh-pages`，目录选 `/ (root)`
4. 点击 **Save**

工作流会自动将日报推送到 `gh-pages` 分支。首次部署后约 1-2 分钟生效。

---

## 7. 工作流说明

### `daily-summary.yml` — 每日运行 + 邮件推送

| 属性 | 值 |
|------|-----|
| 触发时间 | 每日 UTC 00:17（北京时间 08:17） |
| 手动触发 | 支持 `workflow_dispatch` |
| 运行环境 | `ubuntu-latest`，Python 3.12 |
| AI 模型 | Agnes 2.0 Flash（OpenAI 兼容 API） |
| 输出 | 邮件推送 + GitHub Pages + Webhook（可选） |

**完整流程**：

```
Checkout → Setup Python → Install uv → uv sync →
复制 config.github.json → 运行 horizon --hours 24 →
检查邮件订阅 → 发送日报邮件 → 部署 docs/ 到 gh-pages
```

### `deploy-docs.yml` — 文档部署

推送 `main` 分支的 `docs/**` 变更时触发，用于文档更新。

---

## 8. 手动触发

1. 进入仓库 **Actions** 标签页
2. 左侧选择 **Daily Horizon Summary**
3. 点击 **Run workflow** → **Run workflow**

运行耗时 3-10 分钟，取决于数据源数量和 AI 响应速度。

---

## 9. 验证部署

- **邮件**：检查订阅邮箱是否收到日报
- **GitHub Pages**：访问 `https://<你的用户名>.github.io/Horizon/`
- **Webhook**：检查对应平台是否收到通知
- **日志**：Actions → 运行记录 → 查看各步骤日志

---

## 10. 故障排查

### Agnes AI 调用失败

- 确认 `AGNES_API_KEY` Secret 已设置且值正确
- 确认 `config.github.json` 中 `base_url` 为 `https://apihub.agnes-ai.com/v1`
- 确认 `model` 为 `agnes-2.0-flash`
- 检查 Actions 日志中搜索 `ERROR` 或 `401`/`429`

### 邮件推送失败

- 确认 `EMAIL_PASSWORD` Secret 已设置（163 邮箱使用**授权码**，非登录密码）
- 确认 `config.github.json` 中 `email_address` 已改为真实地址
- 确认 163 邮箱已同时开启 **SMTP 服务**和 **IMAP 服务**
- 日志中搜索 `SMTP Error` 或 `Error checking subscriptions` 定位具体原因

### GitHub Pages 未更新

- 确认 **Settings → Pages** 已配置为 `gh-pages` 分支
- Pages 部署有 1-2 分钟延迟

### RSS 源报错

- 确认 RSS URL 可直接访问（Actions 运行在美国机房，部分国内源可能受限）

### 调整运行频率

修改 `daily-summary.yml` 中的 cron 表达式：

```yaml
on:
  schedule:
    - cron: '0 6 * * *'  # 每天 UTC 06:00（北京时间 14:00）
```

---

> 遇到其他问题？请提交 Issue：https://github.com/Thysrael/Horizon/issues
