# 当前验证记录：DeepSeek Actions 测试准备

2026-11-04（北京时间）。用户已选择 DeepSeek，并报告在 GitHub Repository Secrets 添加
`DEEPSEEK_API_KEY`；密钥没有提供给 Codex，也没有被读取或打印。

| 检查 | 实际结果 |
| --- | --- |
| Python / uv / 依赖 | Python 3.12.14、uv 0.13.4，冻结依赖已验证 |
| 六类阅读规则 | 保持中文、7 分门槛、主题去重、每天最多 15 条、每类最多 3 条 |
| DeepSeek 原生支持 | Horizon 默认 `deepseek` / `deepseek-chat` / `https://api.deepseek.com`；独立覆盖配置已验证 |
| 最新在线模型目录 | 尚未查询；Actions 必须先确认别名存在于账户 `/models` 目录，不能自动换模型 |
| 全量离线测试 | **892 通过、0 失败、0 跳过**：879 个上游测试、5 个个人配置测试、8 个 DeepSeek 测试 |
| 工作流语法 | actionlint 1.7.7 通过；官方发布包下载后校验 SHA256 成功 |
| 真实候选上限 | 在 AI 阶段之前最多 5 个；测试覆盖去重、内容不足排除及跨 Profile 选择 |
| 费用保护 | 最多 16 次完成请求、每次最多 2048 输出 Token、提示词字符限制、SDK 自动重试关闭 |
| 用量/估算逻辑 | 使用合成数据验证缓存命中、未命中、输出 Token 的费用公式；不是实际模型用量 |
| 既有无 AI 采集 | 10 条 GitHub Atom 记录成功；12 个其他端点在 Cloud 被代理拒绝 |
| GitHub API | `api.github.com` 在 CONNECT 阶段被代理以 403 拒绝 |
| DeepSeek 官方文档 | `api-docs.deepseek.com` 在 CONNECT 阶段被代理以 403 拒绝 |
| 远端默认分支 | 检查时仍为上游基线；只有 deploy-docs.yml 和禁用的旧日报工作流，没有新手动工作流 |
| 真实 Actions 测试 | **尚未执行**；无 run ID、真实模型 Token、费用或新日报可报告 |

测试命令：

```bash
.venv/bin/python -m pytest tests configs/personal/test_config.py \
  configs/personal/test_deepseek_smoke.py \
  --junitxml=/workspace/horizon-state/validation/deepseek-offline.xml
```

原始 XML 与日志在仓库外 `/workspace/horizon-state/validation/`，没有纳入提交。
原先的 21 项 DNS 依赖测试失败已通过显式 fixture 修复；仅限两个 HTTP 模拟测试模块，
没有更改系统 DNS 或生产代码，专用 URL/SSRF 安全测试仍通过。

## 真正运行仍需的外部前提

1. 环境设置中保存并应用 `api.github.com` 和 `api-docs.deepseek.com` 的白名单草稿。
   这些访问用于查看/触发 Actions 和读取官方文档，不用于把 Repository Secret 搬到 Cloud。
   原有新闻源域名已保留。保存草稿不等于网络生效或环境已发布。
2. 默认分支注册 `workflow_dispatch` 工作流。先把分支合并到自己的默认分支，
   不启用旧的 `.disabled` 定时工作流；合并新工作流本身不会发起模型请求。
3. 只触发一次 **Horizon DeepSeek smoke test**，候选最多 5 条，
   查看实际模型目录、采集日志及 artifact，再报告真实结果。

Artifacts 的 `digest-zh.md` 是待人工审读的真实中文日报，
`report.json` 给出源链接状态、分析与必需区块检查、实际 API 用量及费用估算/未知状态。
估算仅在官方价格与真实响应足够明确时填写；账单以服务商为准。
自动检查不是事实核查或人工内容审读的替代；没有运行证据不得宣称日报成功。

本次没有设置 schedule、推送触发器、Pages 发布、消息推送或额外收费服务。
