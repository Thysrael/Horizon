---
layout: default
title: "Horizon Summary: 2026-10-03 (ZH)"
date: 2026-10-03
lang: zh
---

> 从 36 条内容中筛选出 10 条重要资讯。

---

**科技新闻**
1. [AI 以更低训练成本在 Stratego 上击败顶尖人类玩家](#item-tech-news-1) ⭐️ 8.0/10
2. [Zig v0.17.0 发布说明](#item-tech-news-2) ⭐️ 8.0/10
3. [Kroah-Hartman 评 Mythos 的 79 个 LLM 内核漏洞报告](#item-tech-news-3) ⭐️ 8.0/10
4. [SGLang v0.5.21 发布：779 个 PR，新增多款模型与性能改进](#item-tech-news-4) ⭐️ 7.0/10
5. [Rust「Beyond the &amp;」计划：让自定义智能指针贴近内建引用](#item-tech-news-5) ⭐️ 7.0/10
6. [arXiv 自 10 月 1 日起每人每月限投 2 篇](#item-tech-news-6) ⭐️ 7.0/10
7. [Google 提出 Cogentic：多智能体协作发现数学证明](#item-tech-news-7) ⭐️ 7.0/10
8. [Claude Code 推出 mods：TypeScript 改写提示词与界面](#item-tech-news-8) ⭐️ 7.0/10

**科技博客**
1. [超级说服会看起来像贿赂](#item-tech-blog-1) ⭐️ 5.0/10

**财经新闻**
1. [就业数据疲软，交易员大幅下调美联储 10 月加息押注](#item-finance-news-1) ⭐️ 8.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [AI 以更低训练成本在 Stratego 上击败顶尖人类玩家](https://arstechnica.com/science/2026/10/ai-finally-beat-the-best-stratego-player-in-history-and-did-it-on-a-budget/) ⭐️ 8.0/10

Ars Technica 报道称，一套新 AI 系统在隐藏信息的棋盘游戏 Stratego 中击败了顶尖人类玩家，且学习效率优于此前的方法。报道给出的主要是一篇 Nature 文章和一篇 arXiv 预印本的链接，现有材料中没有该系统的名称、算法细节或实验设置。评论区引述报道称，该算法训练所用对局数比 DeepMind 2022 年的 DeepNash 少约 34 倍，最终棋力却更强；由于提供的内容以链接和评论为主，这一数字与相关说法目前无法从现有材料独立核实。

hackernews · PaulHoule · 10月2日 14:11 · [社区讨论](https://news.ycombinator.com/item?id=49933740)

**「背景」** Stratego 是少数长期未被 AI 攻克的经典棋盘游戏之一，其难点在于双方都无法看到对方的棋子身份。DeepMind 的 DeepNash 在 2022 年发表的论文中达到了人类专家水平，但当时并未真正超越顶尖人类棋手。此次新工作（arXiv 2511.07312）在摘要中把自身定位为性能与成本的“阶跃式”变化：据 MIT News 报道，来自 MIT、卡内基梅隆大学、纽约大学和斯坦福大学的研究者所开发的系统以较大优势击败了排名靠前的人类选手。

**「影响」** 如果“训练对局数约为 DeepNash 的 1/34”这一引述成立，那么隐藏信息博弈的研究者在算力有限时也有机会复现同类水平的对弈系统，而不必投入与 2022 年工作相当的训练量。不过现有材料没有给出硬件、训练时长或代码是否公开，因此该方法能否直接迁移到其他不完全信息任务尚不明确。

**「社区讨论」** 评论者 janalsncm 认为学习效率才是这套方法可行的关键：在隐藏信息博弈中最佳着法取决于自己不知道的信息，常规的“我这样走、对方那样应”的前向搜索无法直接成立。评论者 smokel 把这一结果与 2022 年 DeepMind 的 “Mastering the Game of Stratego” 工作对照，认为当年的“掌握”并未真正超越人类，四年后的新方法似乎才做到这一点；另有评论者以童年对局中棋子上有暗记的玩笑回应“隐藏信息”这一主题。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.nature.com/articles/s41586-026-11036-y">Scalable decision-making for games of imperfect information</a></li>
<li><a href="https://arxiv.org/abs/2511.07312">[2511.07312] Superhuman AI for Stratego Using Self-Play ... Mastering the Game of Stratego with Model-Free Multiagent ... Superhuman AI for Stratego Using Self-Play Reinforcement ... This game-playing AI is the new champ at Stratego - MIT News Mastering the game of Stratego with model-free multiagent ... Mastering the game of Stratego with model-free multiagent ...</a></li>
<li><a href="https://arxiv.org/pdf/2206.15378v1">Mastering the Game of Stratego with Model-Free Multiagent ...</a></li>

</ul>
</details>

**标签**: `#AI`, `#game AI`, `#hidden-information games`, `#Stratego`, `#reinforcement learning`

---

<a id="item-tech-news-2"></a>
### [Zig v0.17.0 发布说明](https://ziglang.org/download/0.17.0/release-notes.html) ⭐️ 8.0/10

Zig 项目发布了 v0.17.0 的发布说明，面向使用该语言及其工具链的开发者。现有素材未包含发布说明正文，因此无法核实编译器、构建系统、目标平台支持或标准库的具体变更。

hackernews · ErenayDev · 10月2日 20:56 · [社区讨论](https://news.ycombinator.com/item?id=49938521)

**「背景」** Zig 尚未发布 1.0，长期以 0.x 版本迭代，每个版本都可能包含破坏性变更。据 byteiota 的报道，上一个版本 0.16 历时一年多、主要是一次大规模编译器重构，而 0.17 的范围相对收敛，核心为构建系统重做与 LLVM 22 升级，并称对现有用户的迁移多数只需改动一处函数调用（tool-2-3）。从官方的 0.17.0 里程碑看，Zig 团队在发版前把修复回归与错误编译、解除对第三方项目的阻塞、以及尽早落地破坏性变更列为收尾标准（tool-2-2）。

**「社区讨论」** 在 Hacker News 讨论中，评论者 ubavic 称使用 Zig 一年后认为它是自己试过设计最好的语言之一，但指出它仍不稳定、生态仍小；vitaminCPP 则称赞其目标平台支持并期待 stackless coroutine IO 与一等公民模糊测试工具。另有评论提到 Andrew Kelley 对用 LLM 发现漏洞的态度似有松动，并询问事件化 IO/io\_uring 的现状。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://codeberg.org/ziglang/zig/milestone/69474">0.17.0 - ziglang/zig - Codeberg.org</a></li>
<li><a href="https://byteiota.com/zig-build-system-rework-90-faster-ships-in-0-17/">Zig Build System Rework: 90% Faster, Ships in 0.17 | byteiota</a></li>

</ul>
</details>

**标签**: `#Zig`, `#programming languages`, `#systems programming`, `#compilers`, `#open source`

---

<a id="item-tech-news-3"></a>
### [Kroah-Hartman 评 Mythos 的 79 个 LLM 内核漏洞报告](https://www.youtube.com/watch?v=NnV_cWeoo5Q) ⭐️ 8.0/10

Greg Kroah-Hartman 在 Kernel Recipes 2026 的演讲中审视 LLM 时代的内核安全漏洞报告，并重点讨论了 Anthropic 的 Mythos 项目宣称发现的 79 个漏洞。根据 Hacker News 评论对幻灯片的转述，这 79 个中有 24 个完全没有细节、14 个并非漏洞、3 个数据系捏造、15 个已在最新版本修复（其中 11 个由他人修复、4 个由 Anthropic 修复），只有 20 个需要修复；有评论引述演讲说法称，整件事最终相当于一小时的内核开发工作。评论还提到，Greg KH 称 Mythos 的做法是把过去几十年内核开发者补丁中的模式匹配后套用到别处，且未引用最初修复这些漏洞的开发者。

hackernews · usernomdeguerre · 10月2日 02:51 · [社区讨论](https://news.ycombinator.com/item?id=49929391)

**「背景：LLM 漏洞报告与内核安全流程」** 这段演讲针对的是大模型厂商近来宣称能自动发现内核漏洞的说法。争议焦点是 Anthropic 的 Mythos：它对外宣称在 Linux 内核中找到 79 个安全漏洞，而 Kroah-Hartman 在 Kernel Recipes 2026 的演讲中把这批报告逐条分类核对，包括“完全没有细节”“根本不是缺陷”“数据系杜撰”“已在最新版本修复”以及确需修复等情形（相关分类也由社区评论转述）。对内核而言，这类报告只有经维护者复现与确认后才会进入上游或稳定分支的修复流程，因此核对报告本身是判断 LLM 输出能否用于内核安全工作的前提。

**「影响」** 对内核维护者和下游发行版而言，这意味着不能把 LLM 生成的漏洞或 CVE 列表直接当作已验证结论并触发紧急更新；至少需要复现细节、版本状态和原始修复者信息，才能判断是否实际需要修补。

**「社区讨论」** HN 评论者 usernomdeguerre 转录了幻灯片，djoldman 认为安全营销话术与漏洞报告质量之间的反差明显，devy 则批评 Mythos 只是模式匹配且未给原内核漏洞修复者署名；blinkingled 认为当前成果不佳，但未来用内核专用数据训练的专业模型仍可能加快漏洞发现、分析和修复。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://news.ycombinator.com/item?id=49929391">Greg Kroah - Hartman – Security in the LLM Age [video] | Hacker News</a></li>

</ul>
</details>

**标签**: `#Linux kernel security`, `#LLM security`, `#AI vulnerability reporting`, `#open source maintenance`

---

<a id="item-tech-news-4"></a>
### [SGLang v0.5.21 发布：779 个 PR，新增多款模型与性能改进](https://github.com/sgl-project/sglang/releases/tag/v0.5.21) ⭐️ 7.0/10

SGLang 发布 v0.5.21，该版本包含来自 227 位贡献者的 779 个 PR（PR 数量与贡献者数出自官方发布说明）。新增支持一批模型，覆盖 LLM/VLM 与扩散模型：DeepSeek-V4.1 Flash、GigaChat 3.5、IQuest-Q1、MiMo-V2.6 / MiMo-V2.6-Pro、Ling-3.0-flash-VL，以及 DiffusionGemma、Qwen-Image 2.1、Anima Base v1.0、Ming-Image 0.1 和 FLUX 3 Action。关键变化包括：PD 实例可在不重启的情况下在 prefill 与 decode 之间动态切换；前缀缓存默认改为运行在 Rust 核心上；新增 \`/v1/decisions\` 决策 API 和 \`/v1/score\` 打分 API。发布说明还给出厂商自报的性能数据：DeepSeek-V4.1 长提示词首 token 快 22%，Kimi K3 在 PD 服务中 prefill 吞吐提升 20.6%，GLM-5.3-Flash 现可在 AMD MI355X 上运行并支持 FP8 / MXFP4 MoE 与 MTP 推测解码。安装命令为 \`uv pip install --prerelease=allow sglang==0.5.21\`，同时提供 NVIDIA CUDA 13、AMD MI35x / MI30x、Intel GPU 与 Intel CPU 的 Docker 镜像。

github · Fridge003 · 10月2日 01:09

**「背景」** Horizon 5 月 17 日的日报曾报道 SGLang v0.5.12 首次为 DeepSeek V4 提供完整推理支持（含张量/专家并行、DeepGemm 内核与 PD 分离），本次 v0.5.21 新增的是 DeepSeek-V4.1 Flash 的 LLM/VLM 支持，并在发布说明中称其长 prompt 首 token 快 22%。Horizon 5 月 6 日的日报曾报道 v0.5.11 把推测解码 V2 设为默认并引入 DFLASH 内核，本次发布则继续沿这条路径扩展，包括流水线并行与推测解码（EAGLE/MTP）兼容以及为 Kimi K3 支持 DFLASH。

**「影响」** 对已部署 PD（prefill/decode 分离）架构的运维者而言，最直接的收益是可以在线切换实例角色而无需重启，这可能简化扩缩容与故障处置流程。同时，使用 pip 安装该版本需显式加上 \`--prerelease=allow\`，说明它被标记为预发布版本；在生产环境升级前建议先按平台选用对应的 Docker 镜像（CUDA 13、ROCm MI35x / MI30x、Intel XPU / Xeon），并自行复核上述性能数字，因为它们来自发布说明而非独立测试。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://github.com/sgl-project/sglang/releases/tag/v0.5.12">2026-05-17 — sglang v0.5.12 Adds Full DeepSeek V4 Inference Support</a></li>
<li><a href="https://github.com/sgl-project/sglang/releases/tag/v0.5.11">2026-05-06 — SGLang v0.5.11 Boosts Inference with CUDA 13 and Speculative Decoding</a></li>

</ul>
</details>

**标签**: `#SGLang`, `#LLM inference`, `#model serving`, `#open source`, `#release`

---

<a id="item-tech-news-5"></a>
### [Rust「Beyond the &amp;」计划：让自定义智能指针贴近内建引用](https://lwn.net/Articles/1096028/) ⭐️ 7.0/10

在 RustConf 2026 上，Rust 项目语言团队负责人 Tyler Mandry 介绍了名为「Beyond the &amp;」的设计工作：该工作贯穿 2026 年，目标是让用户自定义的智能指针在借用检查器眼中与内建引用一样灵活。问题场景是，把 \`&amp;mut RenderState\` 换成 \`MutexGuard\` 后，借用检查器无法再识别 \`state.cache\` 与 \`state.template\` 访问的是不相交字段，只能报错，除非手动写成 \`&amp;mut \*state.lock\(\).unwrap\(\)\` 重新借用。团队依据 Nadrieril 与 Benno Lossin 的工作，提出把编译器内部「place（位置）」概念暴露给用户代码：为每种智能指针配一个 handle 类型，用户通过实现 \`ReadPlace\`、\`WritePlace\`、\`ProjectPlace\`、\`BorrowPlace\` 等 trait 来告诉借用检查器如何读写、投影字段和创建借用。这仍是设计与讨论阶段的内容，不是已发布的语言特性；Mandry 表示团队尚未就 \`BorrowPlace\` 创建智能指针的语法达成一致，用 \`&amp;\` 可能造成混淆并影响类型推断。

rss · LWN.net · 10月2日 15:11

**「背景」** “Beyond the &amp;” 是 Rust 项目 2026 年路线图中列出的一项语言设计目标，其官方目标描述是让用户自定义智能指针在语法和人体工程学上与内建引用难以区分，具体包括为自愿加入的指针类型提供自动重借用、与借用检查器完全集成的字段投影，以及语言级的原地初始化 \[tool-2-1\]\[tool-2-2\]。Rust 项目的路线图通常需要数年才能推进完成，因此该项目属于长期设计工作，而非已经交付的语言特性 \[tool-2-3\]。

**「影响」** 若该设计落地，受影响最大的是智能指针库作者：他们需要为自己的类型新增 handle 类型并实现这些 trait，其中 \`WritePlace\` 等实现被标记为 \`unsafe\`，因为实现错误会让借用检查器做出错误判断、导致不健全行为。对普通用户而言，收益是 \`MutexGuard\` 这类类型可能不再需要手动重新借用即可通过借用检查；但由于语法仍未确定，现在无法据此调整代码。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://goals.rust-lang.org/2026/roadmap-beyond-the-ampersand.html">Beyond the `&amp;` - Rust Project Goals</a></li>
<li><a href="https://github.com/rust-lang/goals/blob/main/src/2026/roadmap-beyond-the-ampersand.md">goals/src/2026/roadmap-beyond-the-ampersand.md at main · rust ...</a></li>
<li><a href="https://goals.rust-lang.org/2026/roadmaps.html">Roadmaps - Rust Project Goals</a></li>

</ul>
</details>

**标签**: `#Rust`, `#programming languages`, `#smart pointers`, `#language design`, `#RustConf`

---

<a id="item-tech-news-6"></a>
### [arXiv 自 10 月 1 日起每人每月限投 2 篇](https://www.huxiu.com/article/4895127.html) ⭐️ 7.0/10

全球最大预印本平台 arXiv 自 10 月 1 日起实施新规：每位提交者每个自然月最多提交 2 篇论文，覆盖计算机、数学、物理等全部学科，且被拒稿件同样占用当月额度。多作者论文只计算实际提交者，其余合著者不受影响。据虎嗅网转述，arXiv 9 月投稿量达 40,363 篇，创 35 年新高，其中 AI 分类论文两年增长超 6 倍，大量低质量 AI 生成论文挤占人工审核资源。现有信息未附 arXiv 一手公告或政策全文，因此执行细节和例外情况仍待确认。

telegram · zaihuapd · 10月2日 06:21

**「背景」** arXiv 是预印本平台，论文在同行评审前即公开，并常被科研社区用作新结果的首发时间戳和公共记录。平台官方说明指出，审核资源主要消耗在投稿环节而非已公告论文，因此此次限额直接针对投稿数量，而非已上线论文。

**「对高产投稿者的直接影响」** 对高产研究者与课题组的直接影响是投稿节奏需要重新安排：arXiv 官方说明指出，该限额针对的是投稿行为而非已公布论文，被拒稿件同样占用当月额度，因此一个月内两次投稿被拒后只能等下个月再投。由于多作者论文只计入实际提交者，合作团队可以把投稿分散到不同合著者名下规避集中占用，但每位提交者个人仍受每月 2 篇上限约束。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://blog.arxiv.org/2026/10/01/updated-rate-limit-policy/">arXiv has updated its rate limit policy for all submitters.</a></li>
<li><a href="https://terrytao.wordpress.com/2026/10/01/arxiv-updates-its-rate-limiting-policy/comment-page-1/">arXiv updates its rate limiting policy | What&#x27;s new</a></li>
<li><a href="https://blog.arxiv.org/2026/10/01/updated-rate-limit-policy/">arXiv has updated its rate limit policy for all submitters.</a></li>

</ul>
</details>

**标签**: `#arXiv`, `#AI research`, `#academic publishing`, `#research integrity`, `#submission policy`

---

<a id="item-tech-news-7"></a>
### [Google 提出 Cogentic：多智能体协作发现数学证明](https://arxiv.org/abs/2609.40324v1) ⭐️ 7.0/10

Google 的一篇论文提出 Cogentic，一套用于自动发现数学证明的多智能体系统：多个独立证明器分头探索不同方向，由专门组件进行对抗式验证，并把确认过的结果写入可复用的验证账本。该工作以 Gemini 为基础模型，据称在在线学习、拍卖理论和机制设计三个领域的 5 个开放问题上产出了新结果，并称这些结果已由领域专家独立验证、在配套论文中展开。上述内容目前仅来自一条简短的 Telegram 摘要，缺少技术细节，且给出的 arXiv 编号与当前日期不符，尚无法独立核实，因此这些“专家验证的新结果”仍属未经证实的说法。

telegram · zaihuapd · 10月2日 12:04

**「背景」** 单次调用前沿语言模型虽能产生不错的数学想法，但在开放研究问题上往往不足以直接得出完整证明，Cogentic 以多个独立证明器加专门对抗式验证组件的“证明—验证”循环，正是针对这一局限（arXiv 摘要原文称 single-shot generation is often insufficient）。Horizon 的 8 月 21 日日报曾报道陶哲轩援引 First-Proof 第二轮结果——10 道未发表研究题由 4 个 AI 系统测试、其中 7 道至少被一个系统判为合格，每题成本为数十至数百美元——并警告数学可能从证明稀缺走向证明过剩、无人能清晰讲解的证明应被视为不完整。这两点构成了理解本次“结果由领域专家独立验证”这一环节为何被特别强调的背景。

**「影响与使用注意」** 对在线学习、拍卖理论和机制设计方向的研究者而言，真正可跟进的材料是论文提到的配套论文：公开摘要只给出五项结果的结论概览，证明细节放在配套论文中，单凭这条公告无法评估或引用这些结果。“由领域专家独立验证”是论文自身的陈述（tool-3-2、tool-3-3），并非独立于作者的第三方复核，采用前应回到原文与配套材料核对。另外，摘要称该框架“旨在”解决研究级数学与理论计算机科学问题（tool-3-1），这是设计目标而非已独立测得的通用能力上限，因此不宜据此推断它能处理同类其他开放问题。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://the-decoder.com/terence-tao-says-ai-could-trigger-maths-biggest-crisis-since-godel/">2026-08-21 — 陶哲轩：AI 或致数学证明过剩与基础危机</a></li>
<li><a href="https://arxiv.org/abs/2609.40324">[ 2609 . 40324 ] Cogentic : Multi - Agent Orchestration for Automated...</a></li>
<li><a href="https://arxiv.org/abs/2609.40324">[2609.40324] Cogentic: Multi-Agent Orchestration for ...</a></li>
<li><a href="https://fourweekmba.com/ai-google-research-cogentic-multi-agent-math/">Google Research Cogentic Reports Five Open Math Results</a></li>
<li><a href="https://arxiv.org/html/2609.40324v1">Cogentic: Multi-Agent Orchestration for Automated Proof Discovery</a></li>

</ul>
</details>

**标签**: `#multi-agent systems`, `#automated theorem proving`, `#AI for mathematics`, `#Google Research`, `#Gemini`

---

<a id="item-tech-news-8"></a>
### [Claude Code 推出 mods：TypeScript 改写提示词与界面](https://claude.com/blog/claude-code-mods) ⭐️ 7.0/10

Anthropic 为 Claude Code 推出 mods 自定义扩展功能，开发者用少量 TypeScript 代码即可改写提示词、新增界面或替换内置功能。Mods 随插件分发，现已支持 CLI 和桌面版。官方说明 mods 与 Claude Code 权限相同且不设沙箱，因此提醒用户只安装可信来源，用户也可以让 Claude 自行编写 mods。部分内置功能已改用 mods 实现，官方计划后续迁移更多。

telegram · zaihuapd · 10月2日 12:32

**「背景」** Claude Code 是 Anthropic 的 AI 编程工具，其 mods 是随插件分发的扩展机制：这类扩展通常与宿主应用在同一进程和权限下运行，边界取决于宿主本身，而不是扩展自带的隔离层。Horizon 6 月 7 日的日报曾报道另一条思路，即把 MicroPython 编译为 WebAssembly，在 Datasette 等应用内以沙箱执行不受信任的 Python 代码（当时仍为 alpha），用以说明第三方扩展代码的沙箱问题在插件生态中由来已久。这也解释了 Anthropic 为何强调 mods 与 Claude Code 权限相同且无沙箱，只应安装可信来源。

**「影响与注意事项」** 对开发者而言，mods 与 Claude Code 拥有相同权限且不设沙箱，因此安装一个第三方 mod 等于把它所需的代码与命令执行能力一并交出；官方建议只安装可信来源，第三方指南也强调需在启用前评估其权限范围与风险（tool-2-1、tool-2-2）。由于 mods 随插件分发，且官方已将部分内置功能改为 mods 并计划迁移更多，团队在引入插件时应把 mod 源码审查纳入既有依赖审核流程，并留意内置行为的后续变化。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://simonwillison.net/2026/Jun/6/micropython-in-a-sandbox/#atom-everything">2026-06-07 — MicroPython 编译为 WebAssembly 实现 Python 沙箱</a></li>
<li><a href="https://aireiter.com/zh/blog/claude-code-mods-security-installation-guide">Claude Code Mods：安装、安全性与功能详解</a></li>
<li><a href="https://claude.com/blog/claude-code-mods">Customize Claude Code with mods in TypeScript | Claude by ...</a></li>

</ul>
</details>

**标签**: `#Claude Code`, `#Anthropic`, `#插件系统`, `#AI 编程助手`, `#开发者工具`

---

## 科技博客

<a id="item-tech-blog-1"></a>
### [超级说服会看起来像贿赂](https://seangoedecke.com/superpersuasion-will-look-like-bribery/) ⭐️ 5.0/10

rss · Sean Goedecke · 10月3日 00:00

**「背景」** AI 安全圈长期讨论“超级说服”：足够聪明的 AI 也许能说服工程师放它出笼，或说服人类不按关机键。作者 Sean Goedecke 指出，常见设想把它当成一连串无法反驳的理性论证，仿佛只有“咬子弹”的理性主义者才会被说服。

**「方案」** 但作者认为，普通人不会因看似严密的论证接受荒谬结论；说服通常依赖长期建立的融洽关系，往往还要面对面。超级说服不会因此消失，而是更像贿赂：AI 可承诺帮做项目、改成绩，甚至为家人合成个性化 mRNA 癌症疫苗，也可直接给钱，例如通过加密攻击、承接软件外包或网络诈骗。Ben Shindel 的预测市场被视为例子：下注“会说服他改判”的人最终成功，部分原因是一次面对面会面带来好感，以及“是”方承诺的慈善捐款。作者还举出 OpenAI/Anthropic 宁愿发布模型赚钱而不安全隔离、人们排队把电脑、钱包和互联网交给 AI 换帮助、Anthropic 把新模型接入湿实验室等迹象，说明 AI 能用利益交换推动人行动。作者承认说服与贿赂技术上不同，但关键问题是 AI 能否让人照它意愿行事，贿赂同样有效；若给一百万美元最管用，超级智能就会这么做。作者也指出一个反讽：理性主义文化让普通人以为自己不会被 AI 说服，但当前掌权者中理性主义者偏多，反而可能被听上去合理的论证说服。

**「启示」** 作者的核心结论是：AI 的超级说服大概率不是哲学意义上的严密论证，而是普通、有效且容易被忽视的激励影响——帮助、交易、贿赂与好感；因此 AI 安全讨论应把这类寻常手段纳入威胁模型。

**标签**: `#AI safety`, `#superpersuasion`, `#persuasion`, `#AI alignment`, `#rationalism`

---

## 财经新闻

<a id="item-finance-news-1"></a>
### [就业数据疲软，交易员大幅下调美联储 10 月加息押注](https://www.cnbc.com/2026/10/02/fed-rate-hike-odds-decline-after-september-jobs-report.html) ⭐️ 8.0/10

在 9 月新增就业仅 2.9 万人、低于市场预期的逾 8 万人后，交易员对美联储 10 月加息的预期概率明显下降：CME FedWatch 工具显示 10 月加息 25 个基点的概率为 17%，一周前接近 36%；预测市场平台 Kalshi 上的概率为 18%，一周前接近 70%。这些是市场隐含的预期概率而非已作出的政策决定，交易员仍预计 12 月会加息——FedWatch 显示概率超过 75%，Kalshi 为 65%，美联储下一次决议将在 10 月 28 日两天政策会议结束时公布。

rss · CNBC Finance · 10月2日 13:29

**「背景」** 美联储有促进充分就业和稳定物价的双重使命，并在 9 月会议上因通胀连续五年高于目标而加息；交易员常用 CME FedWatch 这个按 30 天联邦基金期货价格推算市场隐含概率的工具，来判断 10 月是否还会加息。

**「影响」** 对利率预期敏感的债券市场已作出反应：这份疲软的 9 月就业报告公布后，美国国债收益率下跌，因为交易员下调了美联储 10 月加息的概率。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html">FedWatch - CME Group</a></li>
<li><a href="https://qz.com/treasury-yields-september-jobs-report-fed-rate-hike-100226">Treasury yields fall after weak September jobs report - Quartz</a></li>

</ul>
</details>

**标签**: `#Federal Reserve`, `#interest rates`, `#jobs report`, `#inflation`, `#market expectations`

---