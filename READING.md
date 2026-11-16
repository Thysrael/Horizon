# Jam's Reading List

基于 [Horizon](https://github.com/Thysrael/Horizon) 的个人候选阅读清单。
网站：https://horizon.fullstackjam.com

## 阅读流程

RSS 候选 → 提取原文 → 按长期阅读价值评分 → 每期最多 5 篇 → 网页推荐 → 手动收进 Notion。
阅读价值由 AI 按 `profiles/reading/analysis.md` 评分，最低入选分数为 **7.5 分（含）**，不按技术、生活等分类限制数量。每次从达到门槛的候选文章中按分数从高到低选择最多 5 篇；不足 5 篇就按实际数量输出，没有达标文章就保留已发布清单。分析失败、没有有效评分的条目不进入推荐，并保留分析错误日志。网页抓取失败时，来源行会标注使用 RSS 内容；确认正文缺失或被截断时，推荐说明需标注“正文缺失或被截断，无法可靠评价”。完整的短文或链接清单应说明其形式和局限，不能仅因内容短、论证少就声称正文缺失或抓取失败。
候选时间范围是上次运行以来的新文章（首次运行回溯 7 天）。这不保证每天有 5 篇候选文章，也不会自动补入此前未推荐的旧文章。
已导入 2026-10-27 的 Feedly OPML：45 条订阅去重为 44 个源，保留 Programming / Life 分组（跨组重复的「胡涂说」归入 Life）。Netflix、Cloudflare、伪架构师和 Scott’s Weblog 使用已验证的现行 Feed 地址。
这是订阅快照，之后在 Feedly 增删订阅不会自动同步；未来文章按运行间隔采集，不会一次回溯所有历史文章。
导入时本机检查：37 个源返回可解析的 Feed。当时读不到的 7 个源（酷壳、Application Security、Uber Engineering Blog、piglei、plantegg、WY’Blogs、数字移民）已在 2026-10-29 移除，之后又补入一批验证过的 Scour 源，当前为 52 个源（engineering 44、life 8）。该结果不保证 GitHub runner 的网络访问情况相同。
公开页面只发布生成的短简介、推荐理由和原文链接，不发布 Notion 收藏或抓取的完整正文。

## 配置

- `data/reading.json`：信源、DeepSeek 模型、数量和分组上限。
- `profiles/reading/`：跨领域、注重长期价值的评分与推荐文案规则。
- `site/style.css`、`scripts/build_reading_site.py`：静态页面。
- `.github/workflows/reading.yml`：抓取、生成摘要、构建网站并发布到 `gh-pages`。工作流不再发送阅读清单邮件。
- 定时由 GitHub Actions `schedule` 触发，cron 为 `50 0 * * *`（UTC 00:50，北京时间 08:50，每天）。不套用节假日或调休表。GitHub 可能延迟调度。cron-job.org 不再需要。
- GitHub Actions Secret `DEEPSEEK_API_KEY`：运行时提供，不能放进配置文件。

`gh-pages` 保存网站和 `summaries/` Markdown 历史；每轮先恢复历史，再生成、构建和发布。
首页显示最新一期，`/archive/` 列出所有往期。已发布的中文摘要保持 `https://horizon.fullstackjam.com/summaries/horizon-YYYY-MM-DD-zh.md` 这个路径和文件名。上次成功运行时间用于确定下一次采集窗口；没有新文章或没有文章达到评分门槛时正常结束，保留已有清单并更新采集时间。
同一天重新生成会更新当天一期，所有版本仍可在 Git 历史中找回。

## 定时触发

GitHub Actions `schedule` 现在是定时触发，cron-job.org 不再需要。cron 为 `50 0 * * *`，即 UTC 00:50、北京时间每天 08:50。不套用节假日或调休表。GitHub 可能延迟实际开始时间，开始时间也受 runner 排队影响。
定时运行会抓取并生成推荐，效果与手动运行且 `refresh=true` 相同。向 `main` 推送样式或配置仍只构建网页，不调用模型。

生成和发布是否成功，查看 [Reading list 的运行记录](https://github.com/fullstackjam/horizon/actions/workflows/reading.yml)。

手动 API 触发仍然可用，但不是定时所依赖的方式：

1. 请求：`POST https://api.github.com/repos/fullstackjam/horizon/actions/workflows/reading.yml/dispatches`。
2. 请求头：`Accept: application/vnd.github+json`、`Content-Type: application/json`、`Authorization: Bearer <dedicated-token>`。
3. 请求体：`{"ref":"main","inputs":{"refresh":true}}`。
4. 专用 fine-grained GitHub token 仅选择 `fullstackjam/horizon`，授予 `Actions: Read and write`；token 保存在密码库中，不放进仓库或 URL。

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
