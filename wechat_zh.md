# 微信推送（iLink Bot）

[English](wechat.md)

Horizon 可以通过微信官方的 **iLink Bot API**（`https://ilinkai.weixin.qq.com`，即腾讯 `openclaw-weixin` 渠道所用的协议）把每日日报直接推送到你的个人微信。不需要 Webhook 地址、不需要注册应用、不需要公网服务器：扫一次码，Horizon 就直接和微信服务器通信。

本文是操作手册；配置字段的速查见[配置指南](configuration.md#wechat-notification)。

---

## 1. 工作原理

```
你 ──(任意消息)──▶ 微信机器人会话 ──▶ ilinkai.weixin.qq.com ◀──(getupdates / sendmessage)── Horizon
```

- **登录。** `horizon-wechat login` 获取二维码，扫码后微信在你的账号下绑定一个机器人，并给 Horizon 一个 `bot_token`。
- **会话令牌（context_token）。** 你发给机器人的每条消息都带一个 `context_token`。机器人只能带着收到过的令牌发消息，所以 Horizon 必须先收到你一条消息才能推送，并把最新的令牌保存在本地。
- **回复额度。** 微信把机器人消息当作"回复"：**你每发一条消息，机器人最多回 10 条。** 第 11 条会被拒绝（`ret=-2 prepare failed`），直到你再给机器人发任意消息。这是微信侧的规则，机器人无法绕开；Horizon 会替你管理额度（见[第 5 节](#5-回复额度)）。
- **两次运行之间 Horizon 不在线。** 定时任务连上、推送、退出；聊天指令要等下一次读收件箱时才会被回复——只有同时运行 `horizon-wechat listen` 才是即时的（见[第 3 节](#重要指令什么时候会被回复)）。
- **渲染。** 机器人会话支持 Markdown 子集：标题、加粗、链接、行内/围栏代码、表格、引用、分隔线。原始 HTML 会原样显示，也没有任何折叠能力，所以 Horizon 发送前会拍平 HTML 块、去掉图片、去掉中文斜体标记。

Horizon 需要的东西都在数据目录里：

| 文件 | 用途 |
|------|------|
| `data/wechat_session.json` | bot token、你的用户 ID、当前会话令牌、回复计数、选择的样式。**属于凭据**——`data/wechat_*.json` 已被 git 忽略，文件权限 `0600`。 |
| `data/wechat_briefing-<lang>.json` | 上一次推送的日报缓存，供「日报」指令原样重放，无需重新抓取或调用 AI。 |

## 2. 配置与接入

### 2.1 在 `config.json` 中启用

```json
{
  "wechat": {
    "enabled": true,
    "style": "summary",
    "languages": ["zh"]
  }
}
```

`style` 是默认样式（`summary` 或 `overview`，见[第 4 节](#4-消息样式)）；`languages` 限定微信只推送 `ai.languages` 中的部分语言。其余字段没有特殊需要就保持默认。

### 2.2 连接你的微信

```bash
uv run horizon-wechat login
```

1. 终端打印二维码（同时给出备用链接，可在手机上打开）。用微信扫码并确认。
2. 微信会出现一个机器人会话。**给机器人发一条任意消息**——发 `hi` 就行。这让 Horizon 拿到第一个会话令牌。
3. Horizon 回一条简短欢迎语，说明指令和回复额度，并保存 `data/wechat_session.json`。

终端显示不了二维码就用打印出的链接。若微信要求输入验证码，命令会提示你输入。`--force` 在已有会话时强制重新登录；如果这个机器人已绑定到本机的 token，微信会返回"已连接"，现有会话会被保留。

### 2.3 检查与测试

```bash
uv run horizon-wechat status              # 会话、样式、剩余额度
uv run horizon-wechat test --dry-run      # 预览将要发送的内容
uv run horizon-wechat test --lang zh      # 发送一份示例日报（需 wechat.enabled = true）
uv run horizon-wechat test --style overview   # 仅本次测试试用另一种样式
```

示例发送不会覆盖「日报」的重放缓存，测试不会顶掉真实日报。

### 2.4 定时运行

微信是"投递目标"，不是"触发器"：每一次定时执行的 `horizon` 都会在邮件、Webhook 之后把当天日报推到微信。推送前它会先花约 8 秒检查机器人收件箱，拿到更新的会话令牌以及上次运行之后你发的指令。定时任务配好之后，你不需要手动运行任何命令。

```bash
# 常开机器上的 cron，每天 08:00
0 8 * * * cd /path/to/Horizon && uv run horizon --hours 24 >> logs/horizon.log 2>&1
```

也可以由宿主机 cron 执行 `docker compose run --rm horizon`。唯一的要求：**数据目录必须在两次运行之间持久保存**，因为会话文件里有会变化的状态（会话令牌、回复计数、收件箱游标）。因此像仓库自带的 GitHub Actions 工作流那种一次性运行器不适用，除非你自行持久化 `data/`；服务器、NAS、树莓派或 Docker 主机才是微信通道的合适宿主。

## 3. 聊天指令

在机器人会话里直接发。中英文写法等价；你的语言里包含 `zh` 时机器人用中文回复，否则用英文。

| 你发 | 机器人做什么 | 耗额度？ |
|------|-------------|:--:|
| `日报` · `新闻` · `news` | 按当前样式重发上一次推送的日报 | 是（1–N 条） |
| `1` | 切到 `summary`（整份日报一条消息） | 是（1） |
| `2` | 切到 `overview`（先总览，再逐条） | 是（1） |
| `切换` · `switch` | 在两种样式间轮换 | 是（1） |
| `样式` · `/style` · `s` | 显示样式菜单，标出当前样式和剩余额度 | 是（1） |
| `帮助` · `/help` · `h` · `?` | 说明指令并显示剩余额度 | 是（1） |
| 其它任何内容 | 不做任何事——不回复，但你的消息会重置回复额度 | 否 |

样式选择保存在会话文件里，优先于 `wechat.style`，从下一次日报起生效。指令只有在 Horizon 读取收件箱时才会被应答：每日任务运行时、执行 `horizon-wechat status --refresh` 时，或者运行下面的监听器时即时应答。

### 重要：指令什么时候会被回复

> **两次运行之间 Horizon 是不在线的。** 每日 `horizon` 任务连上、推送、退出。你在会话里发的指令只有在"有东西去读收件箱"时才会被看到。想让机器人**即时**回应，就必须额外常驻运行一个进程：`horizon-wechat listen`。

| | 只有每日任务 | 每日任务 **+ `horizon-wechat listen`** |
|---|---|---|
| 收日报 | ✅ 每天推送 | ✅ 每天推送 |
| `1` / `2` 切样式 | 下次运行时生效（当天日报已是新样式，但没有即时确认） | 秒级回复"已切换"，当天日报生效 |
| 「日报」重放 | 下次运行时才发——而那时本来就要推新日报，意义不大 | 秒级重发 |
| 「帮助」/「样式」 | 下次运行时回复 | 秒级回复 |
| 额度重置 | 相同（微信侧规则，与 Horizon 是否在线无关） | 相同 |

所以监听器是**可选的体验增强**，每天收日报从不依赖它。运行代价很低——一个空闲的 Python 进程挂着一条长轮询 HTTP 连接：

```bash
uv run horizon-wechat listen
```

和定时任务放在同一台机器上，并用能自动重启的方式托管：systemd 服务、`tmux` 会话，或 `docker-compose.yml` 里注释掉的 `horizon-wechat` 服务（`restart: unless-stopped`）。它与 `horizon` 共用会话文件，`horizon` 每次推送前都会重新读取，所以你在聊天里切换的样式当晚推送就会生效。每个数据目录只跑**一个**监听器——两个会争抢同一个收件箱游标。

一个可能的后续改进是让监听器兼任调度（`horizon-wechat listen --daily-at 08:00`），一个进程同时负责回指令和跑日报。

## 4. 消息样式

| 样式 | 每期消息数 | 适合 |
|------|-----------|------|
| `summary`（默认） | 1–4 条（整份日报，按 `chunk_size` 分块） | 大多数人。消息最少，额度用得最久。 |
| `overview` | 1 + 资讯条数 | 快速浏览：总览列出每条资讯的分数和链接，随后每条资讯单独一条消息，想停就停。 |

两种样式发送的都是 Horizon 写入 `data/summaries/`、发布到 GitHub Pages 的同一份 Markdown，只是包装方式不同。

## 5. 回复额度

因为微信规定你每发一条消息机器人最多回 10 条：

- 会话文件记录本轮已发条数，你给机器人发消息时计数归零。`horizon-wechat status`、`帮助`、`样式` 都会显示剩余条数。
- 当一期日报需要的消息数超过剩余额度时，`overview` 会把多条资讯合并进更少的消息（每条仍 ≤ `chunk_size`），保证日报不会发一半断掉。
- 当推送后剩余额度 ≤ 2 时，最后一条消息末尾附一句提醒：*回复任意内容即可继续接收 Horizon 推送*。
- 如果微信仍然拒绝，`horizon` 会在日志里说明原因；你回复之后的下一次运行就会成功。

经验法则：用 `summary` 样式，一个从不回复的读者大约能连续收 3 天；随手回一个 `1`、`日报` 或 `hi` 就能重置。欢迎语和低额度提醒都写明了这一点。

## 6. 故障排查

| 现象 | 原因 | 处理 |
|------|------|------|
| `WeChat enabled but 'data/wechat_session.json' does not exist` | 尚未登录 | `horizon-wechat login` |
| `WeChat session not ready (no context token yet …)` | 你还没给机器人发过消息 | 发一条任意消息，然后 `horizon-wechat status --refresh` |
| `WeChat refused the message (ret=-2)` | 本轮回复额度已用完 | 给机器人发任意消息，Horizon 下次运行即可成功 |
| 收件箱检查报 `errcode -14 session timeout` | 微信关闭了机器人的*接收*会话（在长轮询被强行中断后出现过）。发送通常仍可用，所以日报照常推送；只是会话恢复前读不到聊天指令 | 等一会儿——微信会自行重开；或 `horizon-wechat login --force` 换一个全新会话 |
| 消息到了但显示不对 | HTML 或不支持的 Markdown | 请反馈——微信相关的清洗逻辑在 `src/services/wechat.py` 的 `format_markdown_for_wechat` |
| 指令要到下一次每日任务才有回复 | 两次运行之间 Horizon 不在线，且没有监听器 | 在定时任务旁边常驻运行 `horizon-wechat listen`（见第 3 节） |

## 7. 协议要点（供贡献者）

以下均已对照腾讯参考实现 `@tencent-weixin/openclaw-weixin` 2.4.9 及其 `docs/protocol_zh_CN.md` 核实：

- 端点：`POST ilink/bot/get_bot_qrcode?bot_type=3`、`GET ilink/bot/get_qrcode_status`、`POST ilink/bot/getupdates`（长轮询约 35 秒）、`POST ilink/bot/sendmessage`。
- 请求头：`AuthorizationType: ilink_bot_token`、`Authorization: Bearer <bot_token>`、`X-WECHAT-UIN`（随机 uint32 十进制字符串的 base64）、`iLink-App-Id: bot`、`iLink-App-ClientVersion`。所有鉴权 POST 都带 `base_info: {channel_version, bot_agent}`；Horizon 以 `Horizon/<version>` 自报身份。
- 文本消息：`message_type: 2`、`message_state: 2`、`item_list: [{type: 1, text_item: {text}}]`，外加 `context_token`。单条文本实际上限约 4000 字。
- 实测限制（2026-09）：每条用户消息最多 10 条机器人回复；超出返回 `ret=-2`；bot token 失效返回 `errcode -14`。额度是否也按自然日重置尚未确认。
- 不支持：卡片、按钮、折叠内容、HTML 渲染，以及任何"用户没发消息也能推送"的方式。"关注一次、长期接收"属于公众号或企业微信应用消息，是另外的产品。

客户端代码：`src/services/wechat.py`（`ILinkClient`、`WeChatSession`、`WeChatNotifier`）；命令行：`src/services/wechat_cli.py`；与 Webhook 共用的消息拆分：`src/services/delivery.py`。
