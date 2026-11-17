# Jam's Reading List

基于 [Horizon](https://github.com/Thysrael/Horizon) 的个人候选阅读清单。
网站：https://horizon.fullstackjam.com

## 阅读流程

RSS 候选 → 提取原文 → 按长期阅读价值评分 → 达到 7.5 分即入选 → 网页推荐 → 手动收进 Notion。
阅读价值由 AI 按 `profiles/reading/analysis.md` 评分，最低入选分数为 **7.5 分（含）**，不按技术、生活等分类限制数量。凡达到门槛的候选文章全部入选，按分数从高到低排列，不设固定条数；没有达标文章就保留已发布清单。分析失败、没有有效评分的条目不进入推荐，并保留分析错误日志。网页抓取失败时，来源行会标注使用 RSS 内容；确认正文缺失或被截断时，推荐说明需标注“正文缺失或被截断，无法可靠评价”。完整的短文或链接清单应说明其形式和局限，不能仅因内容短、论证少就声称正文缺失或抓取失败。
候选时间范围是上次运行以来的新文章（首次运行回溯 7 天）。这不保证每天都有达标文章，也不会自动补入此前未推荐的旧文章。
已导入 2026-10-27 的 Feedly OPML：45 条订阅去重为 44 个源，保留 Programming / Life 分组（跨组重复的「胡涂说」归入 Life）。Netflix、Cloudflare、伪架构师和 Scott’s Weblog 使用已验证的现行 Feed 地址。
这是订阅快照，之后在 Feedly 增删订阅不会自动同步；未来文章按运行间隔采集，不会一次回溯所有历史文章。
导入时本机检查：37 个源返回可解析的 Feed。当时读不到的 7 个源（酷壳、Application Security、Uber Engineering Blog、piglei、plantegg、WY’Blogs、数字移民）已在 2026-10-29 移除，之后又补入一批验证过的 Scour 源，当前为 52 个源（engineering 44、life 8）。该结果不保证 GitHub runner 的网络访问情况相同。
公开页面只发布生成的短简介、推荐理由和原文链接，不发布 Notion 收藏或抓取的完整正文。

## 配置

- `data/reading.json`：信源、DeepSeek 模型、数量和分组上限。
- `profiles/reading/`：跨领域、注重长期价值的评分与推荐文案规则。
- `site/style.css`、`scripts/build_reading_site.py`：静态页面。
- `.github/workflows/reading.yml`：抓取、生成摘要、构建网站并发布到 `gh-pages`。工作流不再发送阅读清单邮件。
- 定时由 cron-job.org 每天 08:50（北京时间）调用 `workflow_dispatch` 触发，不套用节假日或调休表。GitHub Actions 自带的 `schedule` 已移除，见「定时触发」。
- GitHub Actions Secret `DEEPSEEK_API_KEY`：运行时提供，不能放进配置文件。

`gh-pages` 保存网站和 `summaries/` Markdown 历史；每轮先恢复历史，再生成、构建和发布。
首页显示最新一期，`/archive/` 列出所有往期。已发布的中文摘要保持 `https://horizon.fullstackjam.com/summaries/horizon-YYYY-MM-DD-zh.md` 这个路径和文件名。上次成功运行时间用于确定下一次采集窗口；没有新文章或没有文章达到评分门槛时正常结束，保留已有清单并更新采集时间。
同一天重新生成会更新当天一期，所有版本仍可在 Git 历史中找回。

## 定时触发

定时由 cron-job.org 的每日任务调用 GitHub 的 `workflow_dispatch` 接口触发，不再依赖 GitHub Actions 的 `schedule`。

原因是 `schedule` 的开始时间晚 6 小时以上。cron 原为 `50 0 * * *`（UTC 00:50，北京时间 08:50），2026-11-10 到 11-16 的实际开始时间落在 UTC 07:05–07:48，即北京时间 15:05–15:48。`reading.yml` 因此删掉了 `schedule`：如果外部触发和 GitHub 调度同时保留，同一天会跑两遍，第二遍只有约一小时的采集窗口，会把当天一期覆盖成更短的清单。

cron-job.org 任务配置：

| 项 | 值 |
| --- | --- |
| URL | `https://api.github.com/repos/fullstackjam/horizon/actions/workflows/reading.yml/dispatches` |
| 方法 | `POST` |
| 计划 | 每天 08:50，时区 `Asia/Shanghai` |
| 请求头 | `Accept: application/vnd.github+json`、`Content-Type: application/json`、`Authorization: Bearer <token>` |
| 请求体 | `{"ref":"main","inputs":{"refresh":true}}` |

token 用 fine-grained GitHub token 现建：GitHub 的 *Settings → Developer settings → Fine-grained personal access tokens*，Resource owner 选 `fullstackjam`，Repository access 只选 `fullstackjam/horizon`，Repository permissions 里把 `Actions` 设为 `Read and write`（`Metadata` 会自动带上只读）。有效期最长一年，到期后任务会静默失败，需要换新 token 并更新任务。token 只保存在密码库和 cron-job.org 的任务配置里，不放进仓库、URL 或任务名称；它能触发并读取该仓库的 Actions，泄露后要立即吊销重建。

cron-job.org 侧除了上表的 URL、方法、计划、请求头和请求体，还要注意：

- 时区选 `Asia/Shanghai`，否则 08:50 会按 UTC 解释。
- 打开失败邮件通知。连续失败 25 次后 cron-job.org 会自动停用任务，邮件是唯一的告警。
- 打开「保存响应」，方便在执行历史里看状态码；历史只保留最近 50 次，响应头和正文保留 2 天。
- 免费计划单次请求 30 秒超时，dispatch 通常 1 秒内返回，不受影响，但不要指望它等整个工作流跑完。
- 免费计划失败不重试。GitHub 恰好不可用时，当天这一期就跳过。

GitHub 接受请求时返回 `204 No Content`，cron-job.org 把非 2xx 记为失败。cron-job.org 的成功只说明请求被接收，不说明生成和发布完成；实际是否跑完、是否发布了新一期，看 [Reading list 的运行记录](https://github.com/fullstackjam/horizon/actions/workflows/reading.yml)。

建好任务后先用 `refresh=false` 的请求体点一次 Test run：返回 `204`，且 Actions 里多出一条 `workflow_dispatch` 运行，说明配置正确。确认后再把请求体改回 `{"ref":"main","inputs":{"refresh":true}}` 保存。

手动触发和定时走同一个入口：`refresh=true` 采集并生成推荐，`false` 只重新构建网页。向 `main` 推送样式或配置仍只构建网页，不调用模型。

## 本地运行

```bash
uv sync --extra dev
# Set DEEPSEEK_API_KEY in the process environment.
uv run horizon --config data/reading.json --hours 168
uv run python scripts/build_reading_site.py
uv run python -m http.server 8765 --directory public
```

在 Actions 页面手动运行 `Reading list`，`refresh=true` 重新采集推荐，`false` 只重新发布网页。
调整样式后 push `main` 只构建网页，不调用模型。

## 单独给链接打分

给任意文章链接打分，而不写入每日摘要或网站：

```bash
uv run horizon score --urls https://example.com/article --config data/reading.json
```

MCP 工具 `hz_score_urls` 做同一件事。`profile` 默认是 `reading`，评分规则仍是 `profiles/reading/analysis.md`。`DEEPSEEK_API_KEY` 留在 Horizon 进程环境里，不作为参数传入。单篇抓取或分析失败只记在该 URL 上，不会把这些链接写进已发布的每日清单。

## 已知边界

Horizon 提取失败时会退回 RSS 内容；本项目用评分规则排除明显残缺的摘要，但尚未增加程序级的正文完整性门禁。
推荐条目会标明网页正文提取、RSS 内容或网页失败后的 RSS 回退，不能把回退内容当作已验证的全文。
长文章输入上限为 100,000 字符，超过上限会取头、中、尾；不能保证每篇逐字阅读全文。
原始文章未来失效时，本站保留的是推荐内容和链接，完整正文归档仍由收录流程负责。
