# 个人 AI 知识日报（Codex Cloud）

本目录是一套可提交的配置，不包含凭据。适用于本仓库上游提交
`cdd95f8e881673057e3e201717836da4b8e2e0e7`。
从仓库根目录运行以下命令；云端路径为 `/workspace/Horizon`。

## 阅读规则

六类 Profile 位于本目录的 `profiles/` 下，每类包含项目真实支持的
`profile.json`、`match.md`、`analysis.md`、`enrichment.md`。
没有修改原有 Profile、应用源码、依赖或锁文件。

- 简体中文输出；24 小时采集窗口；按证据、分析深度与解释价值评分。
- 达到 7 分才入选，启用同主题去重；总计**最多 15 条**，每类最多 3 条。
  这是上限，不为凑数降低标准，也不保证每天六类都有新内容。
- 每条包含要点、背景、证据与局限；材料支持时再加入不同观点。
- 保留原始标题链接及来源名称；区分报道、评论、研究与机构声明。
- 对政治、经济与伦理争议采用一致证据标准，不因立场偏好改变评分，
  不给失实说法机械分配同等权重。
- 未启用邮件、微信、Webhook 或 GitHub Actions 定时任务。

多来源和编辑提示词有助于减少单一视角，但不等于逐事件交叉核查。
Horizon 当前会逐条分析和去重，不能保证自动收集每个议题的所有重要观点。
本配置不启用 web_search、历史搜索或全文提取，避免引入未经验证的搜索结果、
额外网络目的地和当前云端本地 DNS 限制。只有 RSS 摘录时必须明确材料局限，
不能声称读过全文。后续可在网络及模型验证后逐步启用全文抓取。

## 信息源

| 兴趣 | 订阅 | 阅读定位 |
| --- | --- | --- |
| 国际政治与国际关系 | BBC World、Al Jazeera、UN News | 跨地区报道与国际机构原始立场；机构声明不等于独立核实 |
| 世界历史与文明 | JSTOR Daily | 研究导向的历史与人文文章；按历史相关度筛选 |
| 哲学、伦理学与思想史 | Aeon、Daily Nous | 思想与论证，以及学界动态；过滤纯行政新闻 |
| 经济、社会与公共政策 | LSE Business Review、Our World in Data | 政策论证、研究与可追溯数据；关注方法及局限 |
| 文学与文化 | Literary Hub、Public Books | 文学评论、作品与文化语境；过滤商业推广 |
| 人工智能和科技 | Simon Willison、Hugging Face Blog、llama.cpp releases | 实践、研究与原始发布记录；降低营销和琐碎版本更新评分 |

准确端点见 `config.json`。首次云端检查：GitHub Atom 返回 HTTP 200、10 条带原始链接的记录；
其余 12 个端点被云代理拒绝，**尚未验证可用性、重定向或内容质量**，不能把这些候选源视为已通过验收。
应用 `network-allowlist.txt` 所列白名单后，需重新探测并根据实际结果替换失效端点。
域名放行也不保证远端站点接受访问。

## 安装与配置检查

```bash
cd /workspace/Horizon
export UV_CACHE_DIR=/workspace/.cache/uv
uv sync --frozen --extra dev
.venv/bin/python configs/personal/check.py validate
.venv/bin/python configs/personal/check.py feeds
.venv/bin/python -m pytest configs/personal/test_config.py
.venv/bin/python -m pytest
```

`validate` 仅检查 JSON、Profile 及引用；`model_selected: false` 表示尚未选择账户可用模型。
模板中的 `${HORIZON_CHATGPT_MODEL}` 不是可用模型名，也不是凭据。
`feeds` 使用真实 HTTP 请求解析 RSS/Atom，任何一个源失败都会以非零状态退出。
首次上游全量测试的已知 DNS 失败见 `VALIDATION.md`；不要关闭 URL 安全检查或改写 DNS 来让测试变绿。

## ChatGPT 订阅：本机登录与云端迁移

项目支持 `anthropic`、`openai`、`openai-chatgpt`、`azure`、`ali`、`gemini`、
`doubao`、`minimax`、`deepseek`、`ollama`。订阅授权使用 `openai-chatgpt`，
与使用 API 计费的 `openai` 不同。账号、工作区、模型和当前预览资格决定是否可用。
Codex 的 GitHub 连接与 ChatGPT 登录不会自动给 Horizon 授权。

按项目 [ChatGPT 文档](../../docs/chatgpt.md) 和
[官方自托管 VM 流程](https://developers.openai.com/siwc/token-sharing-open-source/self-hosted-vms) 操作：

1. 在有浏览器的个人电脑检出本分支，运行 `uv sync --frozen`。
   为云端创建专用登录目录，避免迁移其他已有会话：

   ```bash
   export HORIZON_CHATGPT_AUTH_DIR="$HOME/.config/horizon-personal-cloud"
   mkdir -p "$HORIZON_CHATGPT_AUTH_DIR"
   chmod 700 "$HORIZON_CHATGPT_AUTH_DIR"
   uv run --frozen horizon-chatgpt login --enable-plan
   uv run --frozen horizon-chatgpt models
   ```

   浏览器中批准 **ChatGPT plan usage**。仅完成身份登录还不够。
   `--no-browser` 仍使用本机 `127.0.0.1` 回调，不能只把云端登录 URL 放到自己电脑打开。
   从 `models` 返回的目录选择准确 slug，再在本机执行：

   ```bash
   export HORIZON_CHATGPT_MODEL='从账户模型目录复制的准确 slug'
   uv run --frozen horizon-chatgpt check --model "$HORIZON_CHATGPT_MODEL"
   ```

   上面引号内是说明占位符，必须替换；不要猜测模型名。

2. 云端目标目录使用 `/workspace/horizon-private/chatgpt`，在仓库之外且权限为 700。
   本次已执行初始化，只生成目标主机的 `host.json`，未生成登录凭据。
   新实例可幂等初始化：

   ```bash
   export HORIZON_CHATGPT_AUTH_DIR=/workspace/horizon-private/chatgpt
   mkdir -p "$HORIZON_CHATGPT_AUTH_DIR"
   chmod 700 "$HORIZON_CHATGPT_AUTH_DIR"
   .venv/bin/horizon-chatgpt init
   ```

3. **先发布不含账号凭据的开发环境，再迁移登录文件。**
   仅通过受保护的文件传输（例如环境确实提供的 SSH/SFTP）传输专用本机目录中的
   `credentials.json` 到云端同名路径，设权限 600；保留云端自己生成的 `host.json`。
   不要复制本机 `host.json`，不要提交、粘贴、打印或通过普通聊天附件发送凭据。
   这套工具当前没有提供云环境 SSH/SFTP 地址或个人安全文件挂载入口，
   因而**迁移尚未完成，不能假定 Cloud 支持该流程**。
   如果产品没有安全文件入口，请使用个人持久 VM 运行订阅流程，或改用云端支持的 API 密钥绑定。
   不要把凭据编码到普通环境变量、配置草稿或安装脚本中，也不要将登录后的目录发布为共享快照。

4. 迁移后让云端独占该会话的刷新；本机不要继续使用复制出去的同一登录存储。
   云端环境设置中保存两个非秘密变量：
   `HORIZON_CHATGPT_AUTH_DIR=/workspace/horizon-private/chatgpt` 和
   `HORIZON_CHATGPT_MODEL=<models 返回的准确 slug>`。
   在实际云端重新验证：

   ```bash
   .venv/bin/horizon-chatgpt status
   .venv/bin/horizon-chatgpt models
   .venv/bin/horizon-chatgpt check --model "$HORIZON_CHATGPT_MODEL"
   ```

   `connected` 和 `plan_usage` 必须为 true；`check` 必须完成真实 JSON 推理。
   单看本地状态不能证明推理权限。授权有刷新、过期及额度限制，重新登录时仍需用户交互。
   可在 https://chatgpt.com/settings/usage 管理或撤销授权。

### 如果改用 API Key

这是备选方式，本配置当前没有启用 API 计费回退，也没有添加不需要的密钥要求。
改用时将 `ai.provider` 改为 `openai`、`ai.model` 改为账户可用的 API 模型，
并设 `ai.api_key_env` 为自定义变量名如 `HORIZON_AI_KEY`。
在云环境的安全密钥设置中填写值、将 HTTPS 目的地限定为 `api.openai.com`；不要在聊天中发送值。
部分平台保留 `OPENAI_` 前缀，因此使用上述自定义名称。
代理注入的凭据只应通过支持的 HTTPS 目的地使用，不能把它当作可写入本地文件的明文密钥。
验证一次小请求后再生成日报。订阅额度与 API 账单相互独立。

## 首份真实日报

先完成域名放行、feed 探测和云端 `horizon-chatgpt check`。然后从仓库根目录运行：

```bash
.venv/bin/python configs/personal/check.py run
```

该入口在模型未选择或订阅未授权时提前退出，不会把空日报当作成功。
需要首次覆盖低频历史、哲学和文学文章时，可一次性使用 `run --hours 168`；
正式日常配置仍为 24 小时。采集和逐条 AI 评分的数量可能超过 15，15 是最终入选上限，
不是 API 请求数或费用上限；首次可先用 24 小时窗口控制用量。

运行状态与日报在 `/workspace/horizon-state/personal/`，日志可保存在该目录之外的
`/workspace/horizon-state/validation/`，都位于仓库之外。
最终文件模式为 `summaries/horizon-YYYY-MM-DD-zh.md`，日期由项目当前实现按 UTC 计算。
上游 CLI 还会写入已被 Git 忽略的 `docs/_posts/`；不要提交生成内容或运行缓存。
验收时核对文件是本次创建、正文有真实条目、条数不超过 15、包含原始出处和链接，
并查看日志中各源失败、AI 权限/额度、解析和区块生成错误。
本次尚未生成真实日报，不以合成渲染测试替代模型推理验收。

## GitHub 交付

目标是自己的 fork `kkkkdoyoloveme/Horizon`，不是向上游仓库推送个人偏好。
分支：`config/personal-knowledge-daily`。
只提交本目录配置、提示词、验证工具、测试及说明；不提交外部状态和凭据。

分支推送成功后，在 fork 的 GitHub 页面选择 **Compare & pull request**，
base repository 选自己的 fork，base 选 `main`，compare 选此分支。
查看差异与测试说明；完成网络和真实推理验收后再合并。
合并不会自动发布云环境，也不会配置定时任务。
