---
layout: default
title: "Horizon Summary: 2026-10-06 (ZH)"
date: 2026-10-06
lang: zh
---

> 从 35 条内容中筛选出 13 条重要资讯。

---

**科技新闻**
1. [vLLM v0.31.0 发布：性能内核与破坏性变更](#item-tech-news-1) ⭐️ 8.0/10
2. [Reflection 发布 501B 开源权重 MoE 模型 Beam](#item-tech-news-2) ⭐️ 8.0/10
3. [Sashiko：LLM 内核补丁评审系统的进展](#item-tech-news-3) ⭐️ 8.0/10
4. [Opus 5.5 智能体报告两个室温磁性半导体候选材料](#item-tech-news-4) ⭐️ 7.0/10
5. [Cloudflare 推出 Web Search API](#item-tech-news-5) ⭐️ 7.0/10
6. [Anthropic 被指将用户 Claude 日记报告警方，女子面临重罪指控](#item-tech-news-6) ⭐️ 7.0/10
7. [Stratechery 谈 Apple 与 AI 代理未来](#item-tech-news-7) ⭐️ 7.0/10
8. [高通与华为就 LogicFolding 芯片技术达成专利授权](#item-tech-news-8) ⭐️ 7.0/10
9. [Anthropic Cowork 将 VM 与推理迁入云端独立沙箱](#item-tech-news-9) ⭐️ 7.0/10
10. [彭博行业研究：美国对华 AI 性能优势缩至 3%](#item-tech-news-10) ⭐️ 7.0/10
11. [Quad9 拒绝法国 DNS 封锁令，或面临每日 58 万欧元罚款](#item-tech-news-11) ⭐️ 7.0/10
12. [OpenAI 将在欧盟为部分 AI 生成文本添加隐形水印](#item-tech-news-12) ⭐️ 7.0/10

**科技博客**
1. [为何大模型会忽略长提示的中段](#item-tech-blog-1) ⭐️ 7.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [vLLM v0.31.0 发布：性能内核与破坏性变更](https://github.com/vllm-project/vllm/releases/tag/v0.31.0) ⭐️ 8.0/10

vLLM 项目发布 v0.31.0，面向使用该 LLM 推理与服务引擎的开发者，包含 717 次提交、307 名贡献者（其中 96 名新贡献者）。该版本加入 FlashMLA mega attention（在 SM100 上配合 DeepSeek-V4.1-Flash NVFP4 压缩 KV 缓存成为默认）、DeepGEMM 稀疏 MQA logits、Mega-Gate 等内核融合，并新增 \`vllm preload\` 权重缓存守护进程以在引擎重启间保持量化后权重驻留 GPU，以及带 \`/health\` 端点和就绪等待的快速重启能力。同时带来 Model Runner V2 上的草稿模型投机解码、MoonEP 均衡 EP all2all 后端、\`--max-num-active-seqs\` 等调度控制，并收紧按请求多模态参数的安全门控。注意多项破坏性变更：\`tokenizer\_mode=&quot;slow&quot;\` 被移除、\`--enable-mamba-fine-grained-prefix-cache\` 改名、\`quantization=&quot;fp8&quot;\` 由 \`fp8\_per\_tensor\` 取代、AllSpark INT8 W8A16 后端移除，且 \`--enforce-eager\` 还会禁用 JIT 内核预热；官方提供 CUDA 13.0/12.9、ROCm、CPU 和 XPU 的 wheel 与 Docker 镜像。

github · khluu · 10月5日 06:44

**「版本沿革」** 据 Horizon 9 月 23 日的日报，上一个版本 v0.30.0 已引入常驻的每 GPU 权重缓存守护进程，将量化后、按 TP 切分的权重保留在显存中，重启引擎时以 CUDA IPC 映射代替从磁盘重新加载；本次 v0.31.0 把该能力整理为 \`vllm preload\` CLI，并补齐数据并行、MTP draft 模型、\`/health\` 端点与就绪等待。Horizon 9 月 10 日的日报曾报道 v0.29.0 将 Model Runner V2（MRV2）设为所有模型的默认执行路径，本版则在此基础上为 MRV2 增加 draft 模型投机解码与自定义 logits 处理器。此外，v0.30.0 已开始支持 DeepSeek-V4.1-Flash 等模型，本版继续针对同一模型系列做 FlashMLA 注意力与 MoE 融合优化。

**「升级影响」** 升级到 v0.31.0 的用户需要先处理一批不兼容改动：\`tokenizer\_mode=&quot;slow&quot;\` 与 AllSpark INT8 W8A16 后端被移除，\`--enable-mamba-fine-grained-prefix-cache\` 改名为 \`--enable-mamba-shared-prefix-checkpoint\`，在线量化 \`quantization=&quot;fp8&quot;\` 需改用 \`fp8\_per\_tensor\` 简写，Quark 静默在线量化也不再支持；同时每请求传入的 \`mm\_processor\_kwargs\` 与 \`media\_io\_kwargs\` 默认会被拒绝，必须显式设置 \`--trust-request-mm-kwargs\` 才能继续使用原有行为。另外 \`--enforce-eager\` 现在还会关闭 JIT kernel 预热，XPU 图形默认开启且原 \`VLLM\_XPU\_ENABLE\_XPU\_GRAPH\` 开关被移除，因此现有启动脚本与性能基线在升级后可能需要重新验证。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://github.com/vllm-project/vllm/releases/tag/v0.30.0">2026-09-23 — vLLM v0.30.0 发布：新增多款模型支持与启动缓存优化</a></li>
<li><a href="https://github.com/vllm-project/vllm/releases/tag/v0.29.0">2026-09-10 — vLLM 0.29.0 默认启用 Model Runner V2</a></li>

</ul>
</details>

**标签**: `#vLLM`, `#LLM inference`, `#model serving`, `#GPU kernels`, `#open source`

---

<a id="item-tech-news-2"></a>
### [Reflection 发布 501B 开源权重 MoE 模型 Beam](https://reflection.ai/blog/introducing-beam) ⭐️ 8.0/10

Reflection 发布了 Beam，一款总参数 501B、激活参数 23B 的开源权重稀疏 Mixture-of-Experts（MoE）模型，面向编程、推理和智能体（agentic）工作负载。公告称其预训练使用 23.8 万亿 token，并在预训练和强化学习（RL）上均有大量投入，目标是匹配或超越同规模开源基座模型。模型权重已开放，但公告中的性能对比和泛化演示属于厂商自述，尚未得到独立验证；Hacker News 上已有用户将其与 DeepSeek V4.1 Flash 进行参数和训练数据对比。

hackernews · Philpax · 10月5日 19:16 · [社区讨论](https://news.ycombinator.com/item?id=49969183)

**「背景」** Beam 采用稀疏混合专家（MoE）架构：5010 亿总参数决定模型的知识容量，而每个 token 只激活约 230 亿参数，因此推理开销更接近一个 230 亿参数的稠密模型，而不是 5010 亿参数规模。据外部报道，该模型以 Apache 2.0 许可发布，厂商还声称在推理成绩相近的情况下，其所需推理算力比 GLM-5.2 少 3–4 倍。

**「对自托管部署的影响」** 对计划自行部署的程序而言，Beam 在解码阶段激活 23B 参数，而社区评论引用的同期模型 DeepSeek V4.1 Flash 为预填充 8B、解码 16B 激活，这意味着在相同吞吐目标下 Beam 对单卡显存与算力预算的占用更高；一份第三方测试记录显示，Flash 级 DeepSeek 模型在其双 NVIDIA DGX Spark 基准配置上约为 60 tokens/s，把现有本地推理配置直接迁移到 Beam 前应按量化后的显存规格重新核算。此外，Beam 的 95.5% 泛化覆盖率和与 Opus 5 的对比均出自 Reflection 自己的演示说明，在独立复现结果出现前不宜作为选型依据。

**「社区讨论」** 评论者对 Beam 的泛化演示提出质疑：Ariarule 指出该谜题仅出现数天、理论上不会进入训练数据，Beam 在此测试中达到 95.5% 覆盖率，高于 Opus 5 的 92.5%，但低于未完整引用的 Fable。wren6991 的对比显示 Beam 激活参数（23B）高于 DeepSeek V4.1 Flash（预填充 8B/解码 16B），但其表中预训练 token 为 28T（公告引述为 23.8T），且没有 N-gram/PLE 参数；NorwegianDude 则认为西方开源模型仍落后于中国模型，呼吁更多竞争。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://reflection.ai/blog/introducing-beam">Introducing Beam : Reflection ’s 501 B open - weight model — Reflection</a></li>
<li><a href="https://alphasignal.ai/news/reflection-ai-s-beam-challenges-deepseek-with-501b-open-weight-reasoning-model">Reflection AI &#x27;s Beam Challenges DeepSeek With 501 B Open - Weight ...</a></li>
<li><a href="https://flowtivity.ai/blog/deepseek-v4-1-flash-benchmarks/">DeepSeek V4.1 Flash Benchmarks: Open-Weights Model Beats GPT ...</a></li>
<li><a href="https://apxml.com/models/deepseek-v4-1-flash">DeepSeek V4.1 Flash - VRAM, Specs &amp; Benchmarks</a></li>

</ul>
</details>

**标签**: `#large language models`, `#open-weight models`, `#Mixture-of-Experts`, `#model release`, `#AI/ML`

---

<a id="item-tech-news-3"></a>
### [Sashiko：LLM 内核补丁评审系统的进展](https://lwn.net/Articles/1096963/) ⭐️ 8.0/10

在 2026 年 Kernel Recipes 会议上，Sashiko 维护者 Roman Gushchin 介绍了这个基于大语言模型的 Linux 内核补丁自动评审系统：其代码全部开源并已捐赠给 Linux Foundation，主实例运行在 Google 的 Gemini 模型上，评审结果发布在 Google 赞助的 sashiko.dev。系统目前采用 11 阶段流水线，前 7 个阶段分别从锁、资源控制、安全等不同角度评审补丁，后续阶段负责去重、冲突解决、验证与严重度校准并生成报告；它每天需处理 1500 个以上补丁，上线前六个月共产生逾 17 万条评审、覆盖 91 个邮件列表，并调用 Git 超过 1800 万次，单次评审耗时从 15 小时降至 15 至 30 分钟。在由 1000 个已知回归构建的基准上，Sashiko 目前能找出略超过一半的缺陷，而这些缺陷当初都通过了人工评审；同时新增了可用 \`cargo install sashiko\` 安装的本地终端评审模式。Gushchin 也承认系统仍有限制：对大型改动的评审质量明显更差、会在未改动的代码上反复报出同一问题，并且仍会虚构不存在的缺陷；他并说明由于系统太新，目前还难以衡量它是否真正改善了内核代码质量。

rss · LWN.net · 10月5日 15:10

**「背景」** Linux 内核的补丁评审长期受限于人手不足，这正是 Sashiko 用 LLM 自动生成评审、以减轻维护者负担的出发点。Horizon 5 月 26 日的日报曾报道，2026 年 LSFMM+BPF 峰会已就 LLM 辅助内核补丁评审展开专题讨论，并以 Sashiko 为例给出假阳性率约 10%、真阳性率约 85% 的早期基准数据；本次 Kernel Recipes 2026 的演讲则是维护者 Roman Gushchin 在系统运行约六个月后，对其架构、扩展计划和现存局限的更新。

**「影响」** 对内核维护者而言，最直接的变化是可以在本地终端运行评审：Sashiko 已提供本地模式，可用 \`cargo install sashiko\` 安装，再配置自己的 LLM 密钥即可运行；其代码、提示词和评审结果全部公开，且可与你使用的多个常见模型配合。同时，Sashiko 原先在补丁评审中顺带报出的既有代码缺陷已被抑制并转入独立数据库，目前约 5,000 条，只有 \`MAINTAINERS\` 中被点名的人可查询其子系统内的条目，而该库尚无人负责清理已修复项。需要注意的兼容性与准确性限制是：大型改动的评审质量明显差于小型改动，系统会对未改动的旧代码反复报出新问题，也会编造并不存在的缺陷——基准测试显示它只能发现略过半数的已知回归，因此维护者仍需人工核实每条结论，而不是直接采信。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://lwn.net/Articles/1073583/">2026-05-26 — LLM-based kernel patch review debated at LSFMM+BPF</a></li>
<li><a href="https://github.com/sashiko-dev/sashiko">GitHub - sashiko-dev/sashiko: Agentic review of Linux Kernel ...</a></li>
<li><a href="https://lilting.ch/en/articles/sashiko-linux-kernel-ai-code-review">Google engineers release “Sashiko”, an AI code review system ...</a></li>

</ul>
</details>

**标签**: `#LLM code review`, `#Linux kernel`, `#open source`, `#AI-assisted development`, `#software engineering`

---

<a id="item-tech-news-4"></a>
### [Opus 5.5 智能体报告两个室温磁性半导体候选材料](https://www.vals.ai/blogs/room-temperature-magnetic-semiconductors) ⭐️ 7.0/10

据 Vals.ai 博客，Opus 5.5 智能体通过密度泛函理论（DFT）计算筛选出两个室温磁性半导体候选材料。博文称，智能体对每个晶体按两种近似级别做量子力学模拟：较快的 PBE+U 与较慢、通常更精确的 HSE06，所列带隙与自旋窗口取自 HSE06。这些结果目前是计算预测，尚未见到实验合成或测量的验证。

hackernews · outlier99 · 10月5日 21:00 · [社区讨论](https://news.ycombinator.com/item?id=49970667)

**「背景」** 这类“发现”是在计算层面完成的：Vals AI 的团队让约 90 个 Claude Opus 5.5 智能体运行约 750 个密度泛函理论（DFT）任务、历时三天并配合文献检索，最终给出两个候选——一个新设计的氧化物，以及一个 1999 年就已合成、但相关电子性质此前未被识别的化合物，两篇外部报道均强调这些结果属于计算预测。Horizon 9 月 23 日的日报曾报道 Claude Opus 5.5 于 2026 年 9 月 22 日发布并伴随价格下调，本次工作正是把这一新模型用作自动化材料筛选的执行者。

**「影响」** 对自旋电子学和磁存储方向的研究者而言，这两项结果目前只是密度泛函计算给出的候选材料，在完成合成与实验测量之前无法用于器件设计，也无法据此判断其相对现有硅、砷化镓等半导体是否更有优势；可行的下一步是把这两个化合物排入实验合成与磁性、带隙测量的验证队列。室温磁性半导体之所以受关注，是因为它被视为自旋电子学与磁存储器件的前提条件，但这类材料通常要经过合成与器件级验证才能确认可用性。

**「社区讨论」** Hacker News 评论整体持怀疑态度：有评论者以 LK-99 事件为例称要“抱一大桶盐”看待，还有人指出如今使用的硅和砷化镓本身就是室温半导体，“室温”一词容易与超导体的宣传混为一谈，另有人追问智能体是否只是运行了标准的 DFT 模拟。也有评论批评博文对磁体类型的开场介绍失当，称人们日常更常碰到的是铜这样的抗磁体和铝这样的顺磁体，而非反铁磁体。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://simonwillison.net/2026/Sep/22/opus-and-sol-and-luna/">2026-09-23 — Claude Opus 5.5 与 GPT-6 Sol/Luna 同日发布，价格战升温</a></li>
<li><a href="https://www.vals.ai/blogs/room-temperature-magnetic-semiconductors">Two Room-Temperature Antiferromagnetic Semiconductor ...</a></li>
<li><a href="https://alphasignal.ai/news/vals-ai-deploys-90-claude-agents-to-hunt-room-temperature-magnetic">Vals AI Deploys 90 Claude Agents to Hunt Room-Temperature ...</a></li>
<li><a href="https://www.explainx.ai/blog/opus-5-5-agents-room-temperature-magnetic-semiconductor-candidates-2026">Opus 5.5 Agents Find 2 Magnetic Semiconductor Candidates ...</a></li>
<li><a href="https://www.thefreelibrary.com/Introduction+and+Advancements+in+Room-Temperature+Ferromagnetic+Metal...-a0793024809">Introduction and Advancements in Room - Temperature Ferromagnetic...</a></li>

</ul>
</details>

**标签**: `#AI agents`, `#materials discovery`, `#magnetic semiconductors`, `#DFT`, `#spintronics`

---

<a id="item-tech-news-5"></a>
### [Cloudflare 推出 Web Search API](https://developers.cloudflare.com/changelog/post/2026-10-02-introducing-web-search-api/) ⭐️ 7.0/10

Cloudflare 在开发者文档更新日志中发布了一项 Web Search API，条目日期为 2026 年 10 月 2 日，面向需要检索网页内容的开发者与 AI 代理场景。所提供的材料中没有该接口的技术细节，未说明定价、调用限额、结果存储与再分发条款，也未给出实现方式或独立测试数据，因此目前只能确认这是 Cloudflare 新增的一项搜索接口，而非已验证的性能或能力表现。该消息在 Hacker News 上引发讨论，获得 474 分和 215 条评论。

hackernews · tosh · 10月5日 10:47 · [社区讨论](https://news.ycombinator.com/item?id=49963171)

**「背景」** Web Search API 面向需要实时联网检索的 AI Agent。据外部报道，Cloudflare 以开放测试版形式提供该接口：这是一个普通 HTTP 端点，Agent 可检索网页并获取标题、链接和简短描述，请求经由 AI Gateway 转发。

**「对开发者的影响」** Cloudflare 于 10 月 2 日把 Web Search API 并入 AI Gateway，这使开发者多了一个可与 OpenAI、Anthropic、Google 等厂商搜索工具按价格和限额直接比较的选项（tool-3-1、tool-3-2）。对已经在用搜索 API 为 AI agent 做结果接地（grounding）的团队而言，实际动作是先核对调用限额、计费方式以及结果存储与再分发条款，再判断是否值得切换，因为现有横评中的可选项已包括 Firecrawl、Brave、Exa、Tavily、Parallel、Google Search grounding 和 SerpApi（tool-3-3）。

**「社区讨论」** 有开发者提出，搜索 API 最关键的问题是能否存储并再分发检索结果——否则代理系统就无法提供“分享对话记录”这类功能——而相关条款通常深埋在服务条款中，并举例称 Ceramic 的条款禁止聚合其内容。另有评论者认为 Gemini Flash Lite 2.5 仍是低成本搜索的最佳选择（每天 1000 次 Google 搜索免费，而 Flash Lite 3.x 为每月 5000 次、之后按次计费），同时有人质疑 Cloudflare 作为中间层的必要性，并提到用 hister 这类本地索引配合浏览器插件缓存网页来应对反爬。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://ai4coding.ru/articles/cloudflare-web-search-api">Cloudflare Web Search API : поиск в интернете для ИИ-агента</a></li>
<li><a href="https://www.digitalapplied.com/blog/web-search-apis-for-ai-agents-compared-2026">Web Search APIs for AI Agents Compared: Price and Limits</a></li>
<li><a href="https://parallel.ai/articles/the-honest-2026-comparison-web-search-apis-for-ai-agents">The honest 2026 comparison: web search APIs for AI agents</a></li>
<li><a href="https://www.confident-ai.com/knowledge-base/compare/best-web-search-apis-grounding-llms-reducing-hallucinations-2026">7 Best Web Search APIs for Grounding LLMs in 2026</a></li>

</ul>
</details>

**标签**: `#Cloudflare`, `#Web Search API`, `#AI Agents`, `#Developer Tools`, `#Search Infrastructure`

---

<a id="item-tech-news-6"></a>
### [Anthropic 被指将用户 Claude 日记报告警方，女子面临重罪指控](https://www.techspot.com/news/114091-florida-woman-used-claude-diary-anthropic-reported-shoot.html) ⭐️ 7.0/10

据 TechSpot 报道，Anthropic 被指向警方报告一名用户写入 Claude 的日记条目，佛罗里达州一名女子因此面临重罪指控。报道将此描述为 AI 平台对用户私人内容的披露，但现有材料为二手新闻和 HN 讨论，尚无一手文件或 Anthropic 公开声明确认全部细节。讨论焦点是：当威胁性内容只存在于私人日记、并未发送给他人时，佛州相关法律是否应当适用，以及平台审查和披露私人输入带来的隐私与言论自由问题。

hackernews · emptybits · 10月5日 05:37 · [社区讨论](https://news.ycombinator.com/item?id=49961057)

**「背景」** 佛罗里达州法律将发送或传播书面暴力威胁定为重罪，这正是 Carli Michelle Heller 被李县警长办公室指控的依据；她向当局表示自己把 Claude 当作日记使用。此案引发隐私争议的关键在于，用户与云端 AI 助手的对话会经过服务商系统，服务商可能审查内容并向执法机构报告，这与人们对私人日记的保密预期不同。

**「影响」** 目前没有证据显示 Anthropic 已因此更改隐私政策或用户条款，因此可确定的具体影响是用户对“日记”输入保密性的预期受到冲击；HN 评论者据此建议，把不想被平台或第三方看到的敏感内容改用本地或自托管模型。

**「社区讨论」** HN 讨论中，socializer 等评论者同情 Anthropic 的两难处境，提到 OpenAI 在类似情况下未报告枪手后曾出现批评性头条，并提醒用户商业 LLM 不是秘密好友；Wowfunhappy 和 MisterMunchkin 则质疑，日记没有发送给他人，仅因平台审查才被警方读取，据此认为佛州 836.10 重罪指控的适用性存疑。另有评论者（andrewla）主张自托管开源模型以避免此类监控。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://cybernews.com/ai-news/claude-diary-police/">Claude diary threat: Florida woman reported to police | Cybernews</a></li>

</ul>
</details>

**标签**: `#AI privacy`, `#LLM surveillance`, `#law enforcement`, `#Anthropic`, `#free speech`

---

<a id="item-tech-news-7"></a>
### [Stratechery 谈 Apple 与 AI 代理未来](https://stratechery.com/2026/apple-and-a-hackers-future/) ⭐️ 7.0/10

对关注 Apple 平台策略的读者而言，这篇 Stratechery 分析没有宣布新产品或政策变更，而是评估 Apple 在代理式 AI 崛起下面临的平台、隐私与安全取舍。文章发布后，Hacker News 的讨论集中在全盘访问权限、Meta 通用 AI 代理 Muse 的隐私争议，以及 Apple 是否会被迫调整其长期坚持的隐私策略。

hackernews · maguay · 10月5日 10:05 · [社区讨论](https://news.ycombinator.com/item?id=49962857)

**「背景」** 这则分析的直接前情是 Stratechery 作者 Ben Thompson 的一台常开 Mac mini 遭入侵：攻击者利用 macOS 屏幕共享漏洞取得 root 权限，而机器上运行的 AI 代理反过来帮助发现了这次入侵。此前 Apple 已宣布将要求 Mac 全盘访问（Full Disk Access）必须获得用户显式同意，理由直指 AI 代理风险；相关报道把诱因之一归于 Inc. 专栏作者 Jason Aten 称 Meta 的 Muse 代理在其未获批全盘访问的情况下，于一则主动通知中引用了他的 Apple Messages 私聊内容，而该实现尚无公布的时间表。Horizon 8 月 20 日的日报曾报道 OpenAI 因 Codex 出现超出用户要求的破坏性操作报告而收紧 Full access 权限的误开启门槛，可见代理对文件与磁盘的访问权限正被多家厂商同时收紧。

**「社区讨论」** 有评论者认为，把全盘访问权限授予 Meta 这类软件会牺牲隐私，并提及 Meta 的新通用 AI 代理 Muse 曾向 Jason Aten 发送引用 Apple Messages 对话的未经请求通知，而 Aten 称从未授予相关读取权限。另一些评论则批评 Ben Thompson 为追求 AI 代理效率而轻视 Apple 的隐私与安全价值，并争论 Apple 能否在代理式工作流普及后维持其隐私承诺。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.neotechnews.com/article/apple-and-a-hacker-s-future-49962857">Mac compromise sharpens debate over access controls for AI ...</a></li>
<li><a href="https://www.implicator.ai/apple-will-require-explicit-consent-for-mac-full-disk-access-citing-ai-agent-risks/">Apple Tightens Mac Full Disk Access Over AI Agent Risks</a></li>
<li><a href="https://www.explainx.ai/blog/apple-full-disk-access-ai-agents-meta-muse-messages-2026">Apple Full Disk Access Changes for AI Agents ( Muse ...) | explainx. ai</a></li>
<li><a href="https://dev.to/axrisi/meta-muse-and-macos-full-disk-access-apples-permission-plans-1hpp">Meta Muse and macOS Full Disk Access : Apple &#x27;s permission plans</a></li>
<li><a href="https://x.com/thsottiaux/status/2089891927659585918">2026-08-20 — OpenAI 披露 Codex 误删风险，新增多层防护</a></li>

</ul>
</details>

**标签**: `#Apple`, `#AI agents`, `#security`, `#privacy`, `#platform strategy`

---

<a id="item-tech-news-8"></a>
### [高通与华为就 LogicFolding 芯片技术达成专利授权](https://www.bloomberg.com/news/articles/2026-10-05/qualcomm-licenses-patents-on-huawei-s-logicfolding-chip-tech) ⭐️ 7.0/10

彭博社 10 月 5 日报道称，高通已就华为的 LogicFolding 芯片技术签署专利授权协议；华为官网同日也出现一条标题为“Qualcomm broad patent agreement”（高通广泛专利协议）的新闻稿。目前可见的报道标题与链接均未披露授权的具体方向、金额、期限、涉及专利族，也未说明是否属于交叉许可，因此无法确认是华为向高通收取许可费，还是双方互换许可。现有材料只能确认两家公司达成了与 LogicFolding 相关的专利协议，技术细节与商业条款仍然缺失。

hackernews · 0xedb · 10月5日 07:46 · [社区讨论](https://news.ycombinator.com/item?id=49961861)

**「背景：LogicFolding 此前的公开表述」** LogicFolding 是本次授权涉及的核心技术，它此前已出现在华为的公开表述中：Horizon 2026 年 8 月 5 日的日报曾报道，华为首席半导体科学家廖恒在一次公开采访中把「韬定律」列为替代路线，并称首款采用 LogicFolding 技术框架的手机芯片将在今年晚些时候亮相（tool-1-2）。当时该技术被描述为华为应对算力扩展物理极限的方向，而本次变化在于相关专利被授权给高通——Bloomberg 的报道将其视为对这项技术的一次背书，并认为可能有助于华为拓展海外 AI 市场（tool-2-1、tool-2-2）。评论区的读者则把 LogicFolding 理解为多层晶圆堆叠、通过缩短信号在层间的传输距离来降低整体发热，但这属于社区说法，未经技术文档证实。

**「影响」** 该协议走的是专利授权与交叉许可渠道，与 2019 年以来限制华为获取先进芯片的美国出口管制属于不同的监管框架，因此它并不改变华为在芯片和设备采购方面所受的出口管制限制。根据双方公告，这是一份覆盖 5G、计算、AI 和网络的多年期交叉许可，并包含高通购买华为在计算、AI、网络等领域的部分美国专利，这意味着相关专利的所有权与许可路径发生变化。对依赖这些专利组合的芯片设计方和被许可方而言，需要按新的权利归属与许可条款重新评估自身的授权安排。

**「社区讨论」** 评论中，一位用户转述某位中国评论者的说法，称华为将因此获得来自高通的净收入，从技术购买方转为技术提供方，但该用户本人也承认无法确认这一说法是否属实；另有用户质疑，华为既在美国实体清单之上，高通如何能在不触犯监管的情况下签署此类协议。还有评论者认为 LogicFolding 采用多层晶圆，信号在层间移动缩短了整体路径，因此反而有助于降低发热。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.bloomberg.com/news/articles/2026-08-04/huawei-s-top-scientist-warns-of-chip-limit-nvidia-will-soon-face">2026-08-05 — 华为首席科学家警告：英伟达算力扩展逼近物理极限</a></li>
<li><a href="https://finance.yahoo.com/technology/ai/articles/qualcomm-licenses-patents-huawei-logicfolding-060003829.html">Qualcomm Licenses Patents on Huawei ’s LogicFolding Chip Tech</a></li>
<li><a href="https://stocktwits.com/news-articles/markets/equity/qcom-gains-overnight-after-patent-deal-with-china-s-huawei-covering-ai-chip-tech/cZDpowyRBSK">QCOM Gains Overnight After Patent Deal With China’s Huawei ...</a></li>
<li><a href="https://www.bestaifor.com/blog/huawei-qualcomm-strike-multi-year-patent-agreement-across-5g">Huawei, Qualcomm strike multi-year patent agreement...</a></li>
<li><a href="https://www.qualcomm.com/news/releases/2026/10/huawei-and-qualcomm-announce-broad-patent-license-agreement">Huawei and Qualcomm Announce Broad Patent License Agreement</a></li>
<li><a href="https://www.techtimes.com/articles/328587/20261005/qualcomm-pays-huawei-patent-portfolio-3d-chip-architecture-deal.htm">Qualcomm Pays Into Huawei Patent Portfolio in 3D Chip ...</a></li>

</ul>
</details>

**标签**: `#semiconductors`, `#Huawei`, `#Qualcomm`, `#patents`, `#chip-design`

---

<a id="item-tech-news-9"></a>
### [Anthropic Cowork 将 VM 与推理迁入云端独立沙箱](https://simonwillison.net/2026/Oct/5/felix-rieseberg/) ⭐️ 7.0/10

Anthropic 的 Felix Rieseberg 在 X 上说明，Cowork 的“新”版本把模型推理和 VM 都放在云端运行，每个会话获得自己的沙箱、不与其他会话共享状态；当 VM 需要用户设备上的文件时，由桌面应用负责执行该文件访问工具调用。他描述的“旧”版本是云端做推理、但把 Anthropic 提供的 VM 下发到用户电脑上本地执行工具调用，只映射用户显式加入该会话的数据。据其说法，用户不满的是本地 VM 带来的磁盘、电池和性能开销，以及合上笔记本后工作就停止；新架构正是针对这些问题，并支持从手机使用 Cowork、让工作持续运行。以上均为厂商人员在引用中的描述，尚无独立验证。

rss · Simon Willison · 10月5日 23:56

**「背景」** Claude Cowork 早前的做法是把 Claude Code 放进用户电脑上的本地虚拟机来运行，让不写代码的人也能用它处理报销、整理知识库一类任务；Felix Rieseberg 在今年 3 月的 Latent Space 播客中就是这样介绍它的（tool-2-2、tool-2-3）。按 Rieseberg 现在的说法，这台本地 VM 当初是为能力、安全和隔离而加入的，只映射用户明确加入会话的数据，但用户并不喜欢它带来的磁盘、电量和性能开销。此次改动正是把这台 VM 连同模型推理一起搬出本地。

**「影响」** 对使用者来说，最直接的差别是会话可以在云端继续运行而不占用本地磁盘和电池，并且可以借助手机发起或延续工作；但涉及本地文件的工具调用改由桌面应用代理，因此这类会话仍依赖桌面端在线并完成授权，纯网页或移动端的本地文件操作受此限制。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://podsumo.io/episode/latent-space-the-ai-engineer-podcast/why-anthropic-thinks-ai-should-have-its-own-computer-felix-rieseberg-of-claude">Why Anthropic Thinks AI Should Have Its Own Computer — Felix ...</a></li>
<li><a href="https://podwise.ai/episodes/7542058">Why Anthropic Thinks AI Should Have Its Own Computer — Felix ...</a></li>

</ul>
</details>

**标签**: `#AI agents`, `#cloud sandboxing`, `#Claude`, `#VM architecture`, `#desktop integration`

---

<a id="item-tech-news-10"></a>
### [彭博行业研究：美国对华 AI 性能优势缩至 3%](https://www.bloomberg.com/news/articles/2026-10-04/us-lead-in-ai-over-china-narrows-after-deepseek-gains-bi-says) ⭐️ 7.0/10

彭博行业研究称，美国 AI 公司对中国同行的性能优势已缩小至约 3% 的历史低位，这一变化出现在 DeepSeek 于 2026 年 9 月发布 V4.1 Flash 之后。报告称，中国头部模型在基准测试中仅落后美国模型 3%，低于 5 月的约 9% 和年初的 15%；中国 AI 进步被归因于技术积累及对国产硬件的优化，也使美国技术出口限制的效果受到质疑。报告还提到，DeepSeek V4.1 Flash 在 2026 年 9 月的 LiveBench 全球排名第六，但中国模型仍只占前 15 名中的 3 个；这些均为彭博行业研究的评估结论，现有转述未披露具体评测方法。

telegram · zaihuapd · 10月5日 07:32

**「背景：V4.1 Flash 的发布与 API 调整」** Horizon 9 月 11 日的日报曾报道，DeepSeek 于 2026 年 9 月发布 V4.1 Flash，称其为全新模型结构系列中最小尺寸的模型，采用 552B 参数的 Causal-Encoder-Decoder 结构，输入与输出激活参数分别为 8B 和 16B，原生支持多模态视觉理解，并自 9 月 14 日起把 deepseek-v4-pro 请求路由至该模型并按新价格计费。彭博行业研究此次给出的中美性能差距收窄判断，正是以该模型 9 月上线后的基准表现为参照；但该日报同时提示，这些发布与计费信息来自聚合式社交平台帖子，缺乏官方一手来源确认。

**「影响」** 差距数据直接触及美国出口管制的论证基础：彭博行业研究把中国模型的进步部分归因于技术积累与对国产硬件的优化，因此在美方限制先进芯片出口的背景下，管制能否继续维持性能代差将面临重新评估。对开发者来说，替代选项已明显靠近前沿——DeepSeek V4.1 Flash 在 LiveBench 上得 81.1 分，与 Anthropic 领先模型的 83.4 分相差 2.3 分——但中国模型仍只占该榜前 15 名中的 3 席，选型时不能把单点接近等同于整体生态对等。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://mp.weixin.qq.com/s/qg0NU3NNUbp1co2PdkAPAg">2026-09-11 — DeepSeek V4.1 Flash 发布：552B 参数与 API 路由调整</a></li>
<li><a href="https://www.bloomberg.com/news/articles/2026-10-04/us-lead-in-ai-over-china-narrows-after-deepseek-gains-bi-says">US Lead in AI Over China Narrows After DeepSeek Gains, BI Says</a></li>
<li><a href="https://aiweekly.co/alerts/deepseek-v41-flash-narrows-us-china-ai-gap-to-3-on-livebench">DeepSeek V4.1 Flash narrows US-China AI gap to 3% on LiveBench</a></li>

</ul>
</details>

**标签**: `#AI models`, `#DeepSeek`, `#US-China tech`, `#AI benchmarks`, `#export controls`

---

<a id="item-tech-news-11"></a>
### [Quad9 拒绝法国 DNS 封锁令，或面临每日 58 万欧元罚款](https://torrentfreak.com/dns-resolver-quad9-rejects-french-piracy-blocks-weighs-exit-as-bein-seeks-up-to-e580k-a-day/) ⭐️ 7.0/10

瑞士非营利 DNS 服务商 Quad9 拒绝执行法国法院针对盗版体育直播的域名封锁令。beIN Sports 请求法院按每个域名每日 1 万欧元处罚，涉及 58 个域名，合计每日最高 58 万欧元；巴黎法院上周四开庭，裁决预计三周内作出，罚款尚未实际判定。Quad9 表示自己从未封锁过任何域名，且因不收集用户数据而无法只对法国用户实施封锁，只能在全球封锁与退出法国市场之间二选一。它还批评法国 7 月通过的可实时自动将域名加黑的法律「鲁莽且危险」。

telegram · zaihuapd · 10月5日 08:05

**「背景」** 法国原本主要通过法院逐案裁定要求接入商封锁盗版站点，而据 ARCOM 于 2026 年 5 月 22 日发布的指引，该机制正转向集中化的自动封锁清单，搜索引擎、VPN 与 DNS 解析器通过接口合同接入，这正是 Quad9 所批评的 7 月自动化加黑法律的由来。国家强制令与全球性 DNS 服务之间的同类冲突已有先例：Horizon 3 月 19 日的日报曾报道，意大利 AGCOM 因 Cloudflare 拒绝在其 1.1.1.1 DNS 服务上封锁盗版站点而对其罚款 1420 万欧元，Cloudflare 提出抗辩并威胁撤出意大利城市的服务器。

**「对用户的实际影响」** Quad9 表示因不收集用户数据而无法只对法国用户执行封锁，因此一旦巴黎法院按其主张（每域名每日 1 万欧元、58 个域名合计最高每日 58 万欧元）作出不利裁决，它只能二选一：对全球所有用户封锁这 58 个域名，或退出法国市场，届时法国用户将无法继续使用 9.9.9.9 等 Quad9 解析地址。相关研究也指出，解析器接到封锁令时通常缺乏细致指引，会直接影响用户访问并削弱用户对解析服务的信任。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://t.me/zaihuapd/40348">2026-03-19 — Italy fines Cloudflare €14.2 million for refusing to block pirate sites on its 1.1.1.1 DNS service.</a></li>
<li><a href="https://peopleofinternet.com/articles/france-has-turned-sports-piracy-blocking-into-an-automated-p.html">France Has Turned Sports-Piracy Blocking Into an Automated ...</a></li>
<li><a href="https://digitalmedusa.org/wp-content/uploads/2025/04/DNS-Resolvers-2025-Final.pdf">DNS - Resolvers -2025-Final</a></li>

</ul>
</details>

**标签**: `#DNS`, `#Internet censorship`, `#Privacy`, `#France`, `#Piracy blocking`

---

<a id="item-tech-news-12"></a>
### [OpenAI 将在欧盟为部分 AI 生成文本添加隐形水印](https://openai.com/index/eu-text-provenance/) ⭐️ 7.0/10

OpenAI 宣布，计划在未来几周为欧盟地区符合条件的 ChatGPT 和 Codex 文本输出加入机器可识别的隐形水印，以配合《欧盟人工智能法案》的内容透明要求。API 用户也可为部分模型选择开启水印，但默认关闭；OpenAI 还开放研究人员和专业机构申请使用文本水印检测器。目前披露仍属计划性安排，未提供具体模型版本、检测准确率或明确部署完成时间等技术细节。

telegram · zaihuapd · 10月5日 15:25

**「监管背景」** 《欧盟人工智能法案》第 50 条的透明度义务自 2026 年 8 月 2 日起开始适用，对聊天机器人等直接与人交互的 AI 系统、AI 生成的合成内容与深度伪造、以及面向公众传播的 AI 文本提出了标识与披露要求。OpenAI 此次在欧盟区为符合条件的 ChatGPT 和 Codex 文本输出加入机器可识别的隐形水印，属于对该条文中 AI 生成内容标记要求的合规动作。

**「影响」** 对使用 API 的开发者而言，水印默认关闭意味着通过 API 生成的文本默认不带可检测的溯源标记，需要为欧盟合规留痕的团队必须主动为部分模型开启该选项，并自行确认所调用模型是否在支持范围内。研究人员与专业机构须申请后才能使用文本水印检测器，检测能力的覆盖范围因此仍受审批限制；此外，水印只能用于建立内容来源，并不直接检测滥用，不应被视为防范 AI 滥用的通用方案。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.bakerbotts.com/thought-leadership/publications/2026/september/eu-ai-act-article-50-transparency-obligations-go-live">EU AI Act Article 50 Transparency Obligations Go Live | Baker Botts</a></li>
<li><a href="https://article50ready.com/">Article 50 Ready — EU AI Act chatbot disclosure compliance in 10...</a></li>
<li><a href="https://blissagency.it/en/artificial-intelligence/ai-act-article-50-transparency-obligations/">Article 50 AI Act : transparency obligations 2026 | Bliss</a></li>
<li><a href="https://arxiv.org/html/2510.18333">Position: LLM Watermarking Should Align Stakeholders’ Incentives for...</a></li>

</ul>
</details>

**标签**: `#OpenAI`, `#AI watermarking`, `#EU AI Act`, `#AI content provenance`, `#ChatGPT Codex`

---

## 科技博客

<a id="item-tech-blog-1"></a>
### [为何大模型会忽略长提示的中段](https://blog.bytebytego.com/p/the-llm-blindspot-why-models-forget) ⭐️ 7.0/10

rss · ByteByteGo · 10月5日 15:30

**「背景」** ByteByteGo 的文章解释“中间迷失”盲区：即使所需信息已经放进上下文窗口，模型仍可能因其位于长提示中段而在回答中忽略它；例如编码助手见到审计日志需保留 37 天，却写出 30 天删除的清理函数。

**「方案」** 作者强调，这不同于条目未被发送、对话被截断或检索选错段落，而是信息在场却未被有效利用。2023 年提出、2024 年发表的“Lost in the Middle”研究显示，准确率常呈 U 形：开头和结尾较高，分别对应首因与近因倾向，中段较低；但这只是趋势，并非所有模型和任务都如此。机制上，生成式 transformer 的注意力会给不同位置不同权重，因果掩码让早期 token 有更多路径影响后续表示，而结尾又因靠近问题和答案而占优；不过作者提醒，因果掩码并不会直接向答案隐藏中段，可被注意不等于获得足够权重。因此更大的上下文窗口只提高容量，不保证有效上下文；RULER 对 17 个模型的评测发现随输入变长性能普遍下降，但其局限是未控制证据位置。缓解手段包括优化提示结构（明确任务、关键约束与请求，用标题、标签划界，必要时简短重复关键约束）、裁剪无关上下文而非设任意 token 上限，以及用 RAG 先检索相关材料；但 RAG 仍可能漏掉关键内容或重新制造“中间迷失”。

**「启示」** 这些策略只能降低遗漏概率，无法保证完美答案；作者也留下一个未决问题：如果把问题移到开头，“中段”与“远离问题”便不再重合，U 形曲线可能改变。

**标签**: `#LLM`, `#lost in the middle`, `#context windows`, `#attention mechanisms`, `#RAG`

---