# DeepSeek：仅手动触发的首次真实日报测试

## 已选择的接入

本仓库 Horizon 的原生支持项是 `AIProvider.DEEPSEEK`，默认配置为
`deepseek-chat`、`https://api.deepseek.com` 和变量名 `DEEPSEEK_API_KEY`
（见 `src/models.py` 的 `AI_PROVIDER_DEFAULTS`）。
`deepseek-smoke.json` 使用这些原生设置，不覆盖六类 Profile、中文输出、7 分门槛、
主题去重或每天最多 15 条的常规规则。它是测试用 AI 配置覆盖层，不改变常规配置模板。

当前 Codex Cloud 的代理拒绝 DeepSeek 官方文档和 GitHub API，
因此没有把 Horizon 中的默认别名冒充为已经完成最新在线模型验证。
Actions 会使用同一 API Key 只读查询 `/models`，**确认准确的 `deepseek-chat` 别名存在后**
才允许完成请求，不会自动切换到其他或更贵模型。
官方价格页 `https://api-docs.deepseek.com/quick_start/pricing` 也会归档到 artifact；
如果官方文档访问失败，测试在推理前停止。模型目录查询不是额外的试验性完成请求。

## 密钥与触发

用户已在自己的 `kkkkdoyoloveme/Horizon` 添加 Repository Secret `DEEPSEEK_API_KEY`。
工作流 `.github/workflows/deepseek-smoke.yml` 通过
`${{ secrets.DEEPSEEK_API_KEY }}` 注入单独的真实测试步骤。
安装和离线测试步骤不接收该 Secret；不读取 Secret 值、不打印环境、不复制到文件或 artifact。
不要向聊天提供密钥，不把 GitHub Repository Secret 当成 Codex Cloud 中可直接读取的变量。
本次不新增任何付费服务、第三方模型或定时触发器。

1. 将包含本工作流与脚本的分支合并到自己的默认分支 `main`，以便注册 `workflow_dispatch`。
   工作流只有手动触发，不会因合并立即调用模型。不要启用 `.disabled` 的旧定时工作流。
2. GitHub → Actions → **Horizon DeepSeek smoke test** → **Run workflow**。
   选择包含本次代码的分支，候选数量选 1–5，默认 5。只触发一次，避免重复费用。
3. 如 CLI/API 已获准访问，也可运行：

   ```bash
   gh workflow run deepseek-smoke.yml --repo kkkkdoyoloveme/Horizon \
     --ref config/personal-knowledge-daily -f candidate_limit=5
   ```

   如果 Actions 被禁用或组织策略要求批准，需在 GitHub 中启用/批准该工作流；
   无须向 Codex 提供 API Key。Codex 当前 API 访问受代理限制，保存白名单草稿不等于已解除限制。
4. 检查 workflow run 的 Summary 和 artifact `horizon-deepseek-smoke-RUN_ID-ATTEMPT`。
   Artifacts 保留 7 天，不发布 Pages、不提交日报到仓库，也不发送通知。

GitHub 官方手动工作流说明：
https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow

## 费用与候选约束

采集器可免费获取超过 5 条 RSS 记录，但在任何 AI 分析或分类前：
先去除重复链接和明显缺少内容的条目，按 Profile 轮流选择，**硬截断至最多 5 个候选**。
首次用最近 7 天的内容覆盖低频文章。只有经 URL 安全校验且原文链接实际返回成功状态的候选
会进入 AI；失败链接不会被悄悄当成有效链接，也不会通过关闭验证绕过限制。
新闻源在 GitHub 托管 runner 的网络中重新采集，不绕过 Codex 的网络白名单。

- 每次完成请求最多输出 2048 tokens；总完成请求最多 16 次（含修复或重试）。
- SDK 自动重试关闭；API 错误会停止 AI 阶段，不重复耗费每个候选的请求。
- 单请求 system+user 字符数不超过 24000；不是精确的输入 Token 或美元硬预算。
- 显式 Profile 路由省去自动分类调用；没有额外的收费连接测试、网络搜索或备用模型。
- 评分和富化可能需要多次请求，因此 5 个候选**不等于 5 次 API 请求**。
- 保留门槛；如果没有条目达标，运行失败并记录原因，不生成“成功”的空日报。

`report.json` 包含每次成功响应的输入、输出、缓存命中/未命中 Token（API 返回时）、
实际完成请求尝试次数、原生用量累计，以及官方价格来源。
价格解析只接受准确模型列、明确美元符号和每百万 Token 单位。
能取得三种单价及缓存用量时按以下公式估算：

`USD = (缓存命中输入 × 命中单价 + 未命中输入 × 未命中单价 + 输出 × 输出单价) / 1,000,000`

若官方表格结构变化或用量缺失，费用标为未知，保留原始官方价格文本供核对。
报价不是实际账单，未报告 usage 的失败请求可能仍有费用，以 DeepSeek 控制台为准。

## 日报验收

成功 artifact 包含 `digest-zh.md`、`report.json`、`summary.md` 和 `pricing-reference.txt`。
自动检查候选上限、原生分析成功、评分筛选、中文标题、必需分析区块、来源名称、
原始链接在 Markdown 中保留，以及入选原文 HTTP 可达。
`report.json` 的候选与入选记录能追溯到具体文章和 Profile。
人工还需阅读日报，确认概括忠实、不同观点有依据、不把摘要说成全文。
没有生成 artifact、没有真实内容或没有实际推理记录，均不得报告已完成真实日报。

## 当前执行状态

工作流与脚本已准备，但实际触发仍需 GitHub API 网络访问及默认分支注册。
当前没有 Actions run ID、真实日报或真实 Token/费用结果；不能用本地合成测试代替。
详细离线验证结果见 `VALIDATION.md`。
