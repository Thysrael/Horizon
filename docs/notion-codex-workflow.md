# Notion → Codex 自动开发工作流

Horizon 包含一套实验性的、以 Notion 数据库为任务入口的自动开发流程：

1. GitHub Actions 每 15 分钟查询一次 Notion data source。
2. 工作流认领最早一条状态为 `Ready for Codex` 的任务，并把状态改为
   `Coding`。
3. Codex 在 GitHub-hosted runner 的 `workspace-write` sandbox 中读取任务、
   修改代码并运行验证。
4. 只有 Codex 返回成功、产生非空 Patch、且仓库的确定性测试通过时，工作流
   才创建 Draft Pull Request。
5. 工作流把 PR URL 和最终状态回写到 Notion；失败时把任务标记为
   `Blocked`。

第一版采用轮询而不是实时 Webhook，因此不需要部署额外的公网服务。每次
Workflow Run 最多处理一个任务。

## 1. 创建 Notion data source

新建一个 Notion 数据库，并创建以下属性。属性名可以通过 GitHub Repository
Variables 覆盖，但建议先使用默认值。

| 属性 | 类型 | 必需 | 说明 |
|---|---|---:|---|
| `Task` | Title | 是 | PR 标题和任务名称 |
| `Status` | Status | 是 | 必须包含下面列出的状态 |
| `Agent Run ID` | Text | 否 | 记录认领任务的 Workflow Run |
| `PR URL` | URL | 否 | 自动回写 Draft PR 地址 |
| `Agent Result` | Text | 否 | 自动回写执行结果 |
| `Risk` | Select | 否 | 例如 `Low`、`Medium`、`High` |
| `Allowed Paths` | Multi-select 或 Text | 否 | 供 Agent 判断范围，不是权限边界 |
| `Verification` | Text | 否 | 需求方建议的检查，仅作为上下文，不会直接执行 |

`Status` 至少包含：

- `Ready for Codex`
- `Coding`
- `Review`
- `Blocked`

在每个任务页面正文中写清：

- 目标和背景
- 明确不做什么
- 可验证的验收标准
- 必须保留的兼容性
- 必要的示例或复现步骤

只有把状态手动改成 `Ready for Codex` 才会触发开发。不要在 Notion 页面中
存放密钥、Token、`.env` 内容或生产数据。

## 2. 创建 Notion integration

1. 在 Notion 的 Integrations/Connections 设置中创建一个 Internal
   Integration。
2. 为它启用读取内容和更新内容的能力。
3. 在数据库页面的连接菜单中，把该 Integration 添加到数据库。
4. 记录 Integration Token。
5. 从数据库/data source 设置或 API 响应中取得 `data_source_id`。工作流使用
   当前 Notion API 的 `/v1/data_sources/{data_source_id}/query` 接口，而不是
   已弃用的 database query 接口。

## 3. 配置 GitHub Secrets

在仓库的 **Settings → Secrets and variables → Actions** 中添加：

| Secret | 必需 | 用途 |
|---|---:|---|
| `NOTION_TOKEN` | 是 | Notion Integration Token |
| `NOTION_DATA_SOURCE_ID` | 是 | 任务数据库的 data source ID |
| `OPENAI_API_KEY` | 是 | 仅提供给 Codex 实现 Job |
| `CODEX_GITHUB_TOKEN` | 推荐 | 推送 Agent 分支和创建 PR |

推荐把 `CODEX_GITHUB_TOKEN` 配置为权限受限的 GitHub App installation token
或 fine-grained PAT，仅授予此仓库 Contents 写入和 Pull Requests 写入权限。
不配置时工作流回退到内置 `GITHUB_TOKEN`。

如果使用内置 `GITHUB_TOKEN`，需要在仓库 Actions 设置中允许 Workflow
创建 Pull Request。还要注意，由 `GITHUB_TOKEN` 产生的事件通常不会再次
触发普通 Workflow；希望 Draft PR 正常触发全部 PR 检查时，应使用
`CODEX_GITHUB_TOKEN`。

Secret 被拆分到不同 Job：

- `NOTION_TOKEN` 只进入任务认领和最终回写 Job。
- `OPENAI_API_KEY` 只进入 Codex 实现 Job。
- GitHub 写 Token 只进入发布 PR Job。

Codex 实现 Job 本身没有仓库写权限。

## 4. 可选 GitHub Variables

默认值适合上面的表结构。需要改名时添加对应 Repository Variable：

| Variable | 默认值 |
|---|---|
| `NOTION_TITLE_PROPERTY` | `Task` |
| `NOTION_STATUS_PROPERTY` | `Status` |
| `NOTION_READY_STATUS` | `Ready for Codex` |
| `NOTION_WORKING_STATUS` | `Coding` |
| `NOTION_REVIEW_STATUS` | `Review` |
| `NOTION_BLOCKED_STATUS` | `Blocked` |
| `NOTION_RUN_ID_PROPERTY` | `Agent Run ID` |
| `NOTION_PR_URL_PROPERTY` | `PR URL` |
| `NOTION_RESULT_PROPERTY` | `Agent Result` |
| `NOTION_RISK_PROPERTY` | `Risk` |
| `NOTION_ALLOWED_PATHS_PROPERTY` | `Allowed Paths` |
| `NOTION_VERIFICATION_PROPERTY` | `Verification` |
| `CODEX_VERIFICATION_COMMAND` | `uv run pytest` |

`CODEX_VERIFICATION_COMMAND` 是可信仓库配置，会在发布 PR 前真正执行。
Notion 页面中的 `Verification` 仅作为需求上下文，绝不会直接作为 Shell
命令运行。

## 5. 首次验证

Scheduled Workflow 只从默认分支运行，因此先合并本配置 PR。然后：

1. 在 Notion 数据库中新建一条非常小的任务，例如只新增一个测试。
2. 填写验收标准，把 `Risk` 设置为 `Low`。
3. 保持任务状态不变，先在 GitHub Actions 中手动运行
   **Notion to Codex**，并填写该页面的 Page ID。
4. 确认页面依次变成 `Coding` 和 `Review`，并出现 Draft PR URL。
5. 确认 Draft PR 的改动、测试证据和风险说明都正确。
6. 再创建一条任务，把状态改成 `Ready for Codex`，验证 15 分钟轮询路径。

## 安全与失败语义

- Notion 正文是不可信输入，不能覆盖仓库的 `AGENTS.md`、可信 Prompt、Sandbox
  或 CI 权限。
- Notion 任务禁止修改 `AGENTS.md`、`.codex/**`、`.github/workflows/**` 和
  `.github/codex/**`；Workflow 在发布前还会机械检查这些路径以及常见密钥文件。
- 没有 Patch、结构化结果不是 `success`、或 `CODEX_VERIFICATION_COMMAND`
  返回非零时，都不会创建 PR。
- 失败的执行证据会保留为 GitHub Actions Artifact 14 天，任务状态变为
  `Blocked`。
- 当前流程不会自动合并或部署；Draft PR 必须经过人工审查。
- GitHub Actions 的 concurrency group 防止同一仓库内两个 Run 同时认领任务。
  Notion API 本身没有条件更新，因此不要让其他系统同时消费同一状态队列。

## 相关文件

- `.github/workflows/notion-codex.yml`
- `.github/codex/prompts/notion-task.md`
- `.github/codex/schemas/notion-result.schema.json`
- `scripts/notion_coding.py`
- `tests/test_notion_coding.py`
