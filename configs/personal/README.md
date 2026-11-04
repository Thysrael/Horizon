> 最新选择：已准备使用 GitHub Repository Secret `DEEPSEEK_API_KEY` 的手动测试工作流。
> 真实调用仅在 GitHub Actions 执行，详见 [DeepSeek Actions 指南](DEEPSEEK_ACTIONS.md)。
> 下面的通用 Cloud Secrets 方案作为备选保留；不会要求迁移 ChatGPT 登录资料。

# 个人 AI 知识日报：DeepSeek Actions 与 Cloud 备用方案

已选择通过 GitHub Actions 使用已有 DeepSeek Repository Secret 进行有上限的真实测试，
执行和结果要求见上方指南。**不进行 ChatGPT 登录或凭据迁移，不开通额外服务。**
不要提供登录文件、Cookie 或登录令牌。下方 Cloud Secrets 方案仅作未启用的备选。

## 已配置的阅读规则

六类独立 Profile：国际政治与国际关系、世界历史与文明、哲学与伦理及思想史、
经济社会与公共政策、文学与文化、人工智能与科技。
每类使用项目真实支持的四文件格式，位于 `configs/personal/profiles/`。

- 简体中文，24 小时窗口，7 分及以上入选，启用主题去重。
- 总计最多 15 条，每类最多 3 条；这是上限，不保证凑满或每日六类齐全。
- 保留原始出处和文章链接；区分事实、观点、机构声明、预测及证据局限。
- 对争议采用一致的证据标准，材料支持时比较不同观点；不虚构反方、不机械制造对称。
- 仅启用选定 RSS/Atom；邮件、Webhook、微信及其他默认来源关闭，未配置定时任务。
- 未启用全文抓取和网络搜索。RSS 摘要不足时应说明局限，不能声称读过全文。
  多来源不等于逐事件自动交叉核查。

| 兴趣 | 候选信息源 |
| --- | --- |
| 国际关系 | BBC World、Al Jazeera、UN Press（联合国官方会议报道与新闻稿） |
| 历史文明 | JSTOR Daily |
| 哲学伦理 | Aeon、Daily Nous |
| 经济社会 | LSE Business Review、Our World in Data |
| 文学文化 | Literary Hub、Public Books |
| AI 与科技 | Simon Willison、Hugging Face Blog、llama.cpp releases |

联合国来源已改用官方 UN Press RSS（`https://press.un.org/en/rss.xml`）。当前 Cloud 代理拒绝该域名，替代端点尚待在线验证；其机构新闻稿与独立报道应区分阅读。

端点见 `config.json`。GitHub Atom 已实际通过；其余 12 个端点被云代理拒绝，
尚未验证远端有效性、重定向和内容质量。环境设置中应用 `network-allowlist.txt` 所列
新闻域名后需重新探测，不能把保存白名单草稿等同于网络已生效。保留现有其他所需白名单。

## 无需 AI 的安装、检查与采集

从 `/workspace/Horizon` 运行：

```bash
export UV_CACHE_DIR=/workspace/.cache/uv
uv sync --frozen --extra dev
.venv/bin/python configs/personal/check.py validate
.venv/bin/python configs/personal/check.py feeds
.venv/bin/python configs/personal/check.py collect --hours 168
.venv/bin/python -m pytest tests configs/personal/test_config.py
```

`validate` 检查格式、Profile 和引用；环境占位符未填写不代表模型已经可用。
`feeds` 检查真实 RSS/Atom；`collect` 使用原生 RSSScraper，不创建任何 AI 客户端。
任一来源失败时返回非零退出码，同时保留成功来源的结果和诊断，不能将部分成功说成全部成功。
`--hours 168` 用于首次采集低频内容；省略后使用配置中的 24 小时。
原始数据保存在 `/workspace/horizon-state/personal/raw/`，不进入 Git。

## 已确认的 Cloud Secrets 能力

当前连接的云环境配置工具支持安全 Secret 绑定：变量名、HTTPS 目的地域名及安全值输入；
运行时通过网络代理向指定目的地注入凭据。代理占位符不等同于本地可读取的明文 API Key。
当前没有配置模型 Secret，也没有验证真实凭据注入或模型调用。

普通 Environment Variables 只放非秘密设置。API Key 必须在环境设置的 **Secrets / 密钥**
入口填写，不要贴到聊天、JSON、脚本、普通变量建议值、PR、日志或仓库 `.env`。
这不是对当前产品中所有 Codex Cloud 环境生命周期的保证；不同任务阶段是否注入密钥，
必须在实际运行阶段验证。本项目通过 `api_key_env` 从环境读取，未硬编码任何密钥。

## 待用户确认后的 API Key 接入

`ai.provider: openai` 在这里表示项目的 **OpenAI 兼容协议适配器**，不代表已选购 OpenAI 服务。
目前预留三个变量，均没有真实值或默认付费模型：

| 名称 | 保存位置 | 内容 |
| --- | --- | --- |
| `HORIZON_AI_MODEL` | 普通环境变量 | 所选账户实际支持的准确模型 ID |
| `HORIZON_AI_BASE_URL` | 普通环境变量 | 服务商公开的 HTTPS OpenAI 兼容接口地址 |
| `HORIZON_AI_KEY` | Secrets / 密钥 | 用户已有且允许该模型调用的 API Key |

先确认服务商、账户额度、模型和预算；再创建名称为 `HORIZON_AI_KEY` 的安全绑定，
将允许的 HTTPS 目的地限制为实际 API 主机名，并将该主机加入网络白名单。
例如用户若明确选择 OpenAI，通常是 `https://api.openai.com/v1`、目的地 `api.openai.com`；
其他兼容服务必须使用该服务商公布的地址与模型。此例不是已选方案，不会自动启用或购买。
ChatGPT 订阅并不自动提供 API Key 或 API 余额；不要提交任何 ChatGPT 登录材料。
若选择 Anthropic、Gemini 等非兼容协议，需另行修改项目支持的 `ai.provider`，再配置相应目的地。

Cloud 备用方案尚未启用；不向 Codex Cloud 添加模型 Secret，也不在 Cloud 执行认证探测或推理。
已停止使用旧的 `HORIZON_CHATGPT_*` 变量；如环境设置仍显示旧要求，可在设置中移除。
没有删除或读取任何用户已有登录文件。

## 确认方案后生成首份真实日报

仅在用户确认模型方案并允许实际调用后操作：

1. 安全填写上述变量与 Secret，保存并应用环境设置，确认实际运行阶段可用。
2. 通过 `check.py feeds` 完成信息源复验，处理失效链接或站点拒绝。
3. 在所选模型上先验证一次小请求，再运行：

   ```bash
   cd /workspace/Horizon
   .venv/bin/python configs/personal/check.py run
   ```

   当前缺失任一模型变量或密钥时，入口会在创建模型客户端之前退出。
   这条命令会进行真实推理，可能使用服务商额度或产生费用；本次没有执行。

4. 检查 `/workspace/horizon-state/personal/summaries/horizon-YYYY-MM-DD-zh.md` 是本次新生成，
   正文含真实内容、不超过 15 条，并保留原始出处和链接。上游日期按 UTC 计算。
   日志检查采集、认证、额度、JSON 和区块生成错误。
   上游 CLI 也会写入 Git 忽略的 `docs/_posts/`，不要提交运行产物。

15 是最终入选上限，不是待评分数量、推理请求数或费用上限。
本次没有生成真实 AI 日报；无 AI 的原始采集和合成渲染测试不能替代真实推理验收。

## GitHub

分支 `config/personal-knowledge-daily` 保存于自己的 fork `kkkkdoyoloveme/Horizon`。
提交包括公共配置、提示词、检查工具、文档和必要的测试隔离修复；不包含凭据、原始数据或缓存。
在 GitHub 比较该分支与自己的 `main` 创建 PR；查看测试结果和差异后合并。
合并不会购买服务、发布环境或设置自动调度。
