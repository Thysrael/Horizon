# 验证记录：无 AI 授权准备

2026-11-04（北京时间），当前 Codex Cloud 实例。
上游基线 `cdd95f8e881673057e3e201717836da4b8e2e0e7`。
本次停止全部 ChatGPT 凭据迁移；没有请求用户登录文件、Cookie 或登录令牌，
没有读取、删除或迁移用户已有登录材料，没有模型调用、服务采购或定时任务。

| 检查 | 实际结果 |
| --- | --- |
| Python / uv | Python 3.12.14 / uv 0.13.4 |
| 冻结依赖 | `UV_CACHE_DIR=/workspace/.cache/uv uv sync --frozen --extra dev` 成功；94 个包检查通过 |
| 配置与 Profile | 6 类 Profile 引用有效；仅启用 RSS；中文、最多 15 条、每类最多 3 条 |
| 全量测试 | **884 通过、0 失败、0 跳过**：上游 879 项 + 个性化 5 项 |
| 安全回归 | 原有 URL/SSRF 测试通过；新增缺 Secret、非 HTTPS 接口时拒绝启动的检查通过 |
| RSS 探测 | GitHub Atom HTTP 200、10 条带标题与链接的记录；12 个其他端点被代理拒绝 |
| 原生纯采集 | `check.py collect --hours 168` 保存 10 条真实原始记录，1 源成功、12 源失败，返回非零状态表示部分失败 |
| 落盘数据 | 已重新读取 raw JSON，核对 10 条记录、原始链接、来源名称及 Profile；`ai_called=false` |
| 模型环境变量 | 仅检查存在性；三个变量当前均未设置 |
| 真实 AI 日报 | **未运行、未生成**；模型方案及使用额度待用户确认 |
| Cloud Secrets | 工具支持安全值输入、指定变量和 HTTPS 目的地绑定；未创建模型绑定，实际注入与推理尚未验证 |

测试命令：

```bash
.venv/bin/python -m pytest tests configs/personal/test_config.py \
  --junitxml=/workspace/horizon-state/validation/api-preparation.xml
```

原有 21 项失败来自 HTTP 模拟测试遗漏 DNS 模拟，导致访问 `example.com` 的本地 DNS。
本次增加显式 fixture，仅对两个 HTTP 模拟测试模块启用，限定 `example.com` 和重定向样例
`new-url.com`，未知域名查找直接令测试失败。URL 安全验证仍照常运行，专门的 SSRF
测试未使用该 fixture；没有改写系统 DNS、修改生产代码或屏蔽断言。
首次修复重跑暴露一个重定向样例遗漏，补齐后全量 884 项通过。
这证明单元测试及现有安全断言通过，不代表真实 Webhook 或全文提取已完成联网验收。

原始采集与日志位于仓库外 `/workspace/horizon-state/`；未提交到 Git。
合成中文渲染测试只验证格式、条数与出处链接，不能替代真实推理。

## 外部前提与后续

1. 新闻域名白名单草稿尚未应用到当前实例，12 个 feed 仍受阻。
   需在环境设置保存并应用，再复验端点、重定向和远端可用性；不绕过代理。
2. 待用户确认服务商、准确模型、已有额度与预算，再通过 Cloud Secrets 安全填写
   `HORIZON_AI_KEY`，绑定实际 API 主机；普通变量设置模型和 HTTPS 兼容接口地址。
   当前仅保存变量要求和启动说明，没有添加任何特定模型 Secret 或 API 域名。
3. 实际运行阶段验证安全绑定和一次小请求后，再执行 `check.py run`。
   只有生成新的真实中文 Markdown 且验收内容、来源及上限后，才能称日报流程可用。

环境草稿保存不等于运行配置已应用、环境已发布或新实例恢复已经验证。
