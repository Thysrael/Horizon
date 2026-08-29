---
layout: default
title: "Horizon Summary: 2026-08-29 (ZH)"
date: 2026-08-29
lang: zh
---

> 从 28 条内容中筛选出 13 条重要资讯。

---

**科技新闻**
1. [Anthropic 发布模型硬件标准预览：AI 操控设备集成缩至分钟级](#item-tech-news-1) ⭐️ 8.0/10
2. [腾讯开源 Hy4 preview 发布，盲测小胜 GLM-5.3 与 Kimi K3](#item-tech-news-2) ⭐️ 8.0/10
3. [Triton 3.8.0 发布：公共聚合类型、tl.topk 升序与后端增强](#item-tech-news-3) ⭐️ 7.0/10
4. [Rust rnull 块驱动达到与 C null\_blk 功能对等](#item-tech-news-4) ⭐️ 7.0/10
5. [八个稳定内核版本修复可致内核崩溃的漏洞](#item-tech-news-5) ⭐️ 7.0/10
6. [谷歌 Gemini Omni 1.1 Flash：40 秒视频生成与 4K 输出](#item-tech-news-6) ⭐️ 7.0/10
7. [OpenAI 开发常驻 Codex 代理，可自主续作直至休眠](#item-tech-news-7) ⭐️ 7.0/10
8. [美国法官叫停五角大楼拉黑 Anthropic](#item-tech-news-8) ⭐️ 7.0/10
9. [智谱开源 GLM-5.3，专注智能体编程与网络防御](#item-tech-news-9) ⭐️ 7.0/10

**财经新闻**
1. [玉米和小麦价格跃升至三年多来最高](#item-finance-news-1) ⭐️ 8.0/10
2. [第九巡回法院裁定体育赛事合约不属于联邦监管掉期](#item-finance-news-2) ⭐️ 8.0/10
3. [PayPal 盘前暴跌近 16%，Affirm 与 Gap 大涨](#item-finance-news-3) ⭐️ 8.0/10
4. [两部门：个人住房贷款期限上限从 30 年延长至 40 年](#item-finance-news-4) ⭐️ 8.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [Anthropic 发布模型硬件标准预览：AI 操控设备集成缩至分钟级](https://www.anthropic.com/news/model-hardware-standard-research-preview) ⭐️ 8.0/10

Anthropic 开放了模型硬件标准（MHS）的研究预览，使 AI 智能体能够安全地操控显微镜、液体处理器、机械臂等设备，并并行执行复杂任务。这一标准将设备集成时间从数周至数月缩短到几小时甚至几分钟。首批合作方覆盖生物技术、机器人、量子计算等领域，包括基因泰克、卡内基梅隆大学和 QuEra 等机构。QuEra 的 AI 控制器可在 99.3% 的情况下无需人工干预恢复量子计算机的激光锁定。Anthropic 表示，在完成安全评估后将开源该标准。

telegram · zaihuapd · 8月28日 01:38

**「背景」** 传统上，实验室和工业设备要接入 AI 控制系统，通常需要为每类设备进行定制化适配和编程，耗时从数周到数月不等。模型硬件标准（MHS）旨在为 AI 智能体与物理设备之间提供统一的接口和协议，让设备可以更快速地被 AI 识别、连接和控制，从而降低自动化的集成门槛。

**「影响」** 对基因泰克、卡内基梅隆大学、QuEra 等合作机构以及更广泛的实验室自动化生态系统而言，这一预览意味着设备接入周期可从数周大幅缩短至分钟级，并为后续硬件厂商采用统一 AI 控制接口提供了实际参考依据。

**标签**: `#AI`, `#hardware`, `#Anthropic`, `#model hardware standard`, `#robotics`

---

<a id="item-tech-news-2"></a>
### [腾讯开源 Hy4 preview 发布，盲测小胜 GLM-5.3 与 Kimi K3](https://mp.weixin.qq.com/s/ymr3X878B8oa2XP15CH8TQ) ⭐️ 8.0/10

2026 年 8 月 28 日，腾讯发布迄今最强的开源模型 Hy4 preview。该模型总参数量 770B、活跃参数 49B、上下文窗口达 1M token，主要面向长周期软件工程、文档办公与科学研究场景，并已在腾讯云、GitHub、HuggingFace、ModelScope、AtomGit、OpenRouter 等渠道上线。在 203 个工程任务的盲评中，Hy4 preview 以 2.99 分小幅领先 GLM 5.3 的 2.92 分和 Kimi K3 的 2.94 分。API 定价为每 1M tokens 输入 0.834 美元、输出 2.501 美元。

telegram · zaihuapd · 8月28日 06:11

**「背景」** 腾讯混元于 2026 年 8 月 28 日发布并开源新一代大语言模型 Hy4 preview，总参数量 770B、激活参数 49B，上下文窗口超过 1M token，重点面向长周期软件工程、文档办公与科学研究等生产场景。在 203 个工程任务的盲评中，Hy4 preview 得分 2.99，略高于 GLM 5.3（2.92）和 Kimi K3（2.94），API 定价为每 1M tokens 输入 0.834 美元、输出 2.501 美元，并已上线腾讯云、GitHub、HuggingFace、ModelScope、AtomGit、OpenRouter 等渠道。此次发布延续了国内大模型厂商以开源方式推进模型能力竞争的趋势，为开发者在长上下文和工程任务上提供了新的可选基座。

**「影响」** 对开发者和企业而言，Hy4 preview 提供了一个总参数 770B、上下文 1M token 的开源模型选项，其盲测得分和 API 价格可直接作为选型参考。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://technode.com/2026/08/28/tencent-open-sources-hy4-preview-with-770b-parameters-and-a-1m-token-context/">Tencent open-sources Hy4 preview with 770B parameters and a 1M-token context · TechNode</a></li>
<li><a href="https://www.kucoin.com/news/flash/tencent-hunyuan-releases-and-opens-source-hy4-preview-with-770b-total-parameters">Tencent HunYuan releases and open-sources the Hy4 preview with 770 billion total parameters. | KuCoin</a></li>
<li><a href="https://www.tencent.com/tencent-releases-and-open-sources-tencent-hy4-preview/">Tencent Releases and Open-Sources Tencent Hy4 preview - Tencent</a></li>

</ul>
</details>

**标签**: `#AI`, `#Open Source`, `#LLM`, `#Tencent`, `#Model Release`

---

<a id="item-tech-news-3"></a>
### [Triton 3.8.0 发布：公共聚合类型、tl.topk 升序与后端增强](https://github.com/triton-lang/triton/releases/tag/v3.8.0) ⭐️ 7.0/10

Triton 语言与编译器发布 3.8.0 版本。本次更新将 @triton.aggregate 与 @gluon.aggregate 提升为公开 API，支持继承字段、默认值、自动构造函数、不可变实例与 aggregate\_replace\(\)；tl.topk 新增 descending 参数，可返回最小值；张量描述符现在可放入元组形式的内核参数中，解释器也支持 tl.dot\_scaled。编译器后端更新了固定的 LLVM 修订版，修复 GFX950 BF16 错误编译与 SLP 向量化问题，并将多 CTA 支持扩展到布局转换、归约、本地 gather/scatter、TMA 等操作；tma.store\_wait 新增 read\_only 参数。AMD/HIP 后端扩展了 gfx1250（CDNA 5）的张量数据移动、WMMA、原子操作与 warp 流水线支持。新增 FpSan、GSan、ConSan 等检测/消毒器改进，FpSan 支持 NVIDIA 及 AMD gfx942/gfx950/gfx1250，GSan 为实验性数据竞争检测器，ConSan 增加 AMD 与多 CTA 覆盖。此外，JIT 缓存键改为确定性生成，autotuning 监听器可报告配置、耗时与磁盘缓存状态。

github · warrendeng · 8月28日 18:25

**「背景」** Triton 是一种开源的、以 Python 嵌入的 GPU 编程语言与编译器，最初由 OpenAI 在 2021 年发布，目标是让不熟悉 CUDA 的研究者也能编写接近专家性能的深度神经网络计算内核。它在 MLIR 基础上发展出多种方言（如 Triton 方言和 Gluon 方言），并针对 AMD/HIP、NVIDIA 等不同后端做代码生成。3.8.0 是该项目的一个次要版本，主要带来前端方言、后端编译、AMD/NVIDIA 支持及性能剖析方面的更新。

**「影响」** 使用 Triton 编写 GPU kernel 的开发者可直接使用公共聚合类型、tl.topk 升序选项，并借助扩展后的 FpSan/GSan/ConSan 工具定位浮点一致性与数据竞争问题，同时 AMD gfx1250 用户获得更完整的张量操作支持。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://openai.com/index/triton/">Introducing Triton : Open-source GPU programming for... | OpenAI</a></li>
<li><a href="https://triton-lang.org/main/">Welcome to Triton ’s documentation! — Triton documentation</a></li>
<li><a href="https://aiwiki.ai/wiki/openai_triton">Triton (OpenAI GPU programming language ) | AI Wiki</a></li>

</ul>
</details>

**标签**: `#Triton`, `#GPU compiler`, `#release`, `#AI infrastructure`, `#open source`

---

<a id="item-tech-news-4"></a>
### [Rust rnull 块驱动达到与 C null\_blk 功能对等](https://lwn.net/Articles/1090378/) ⭐️ 7.0/10

2026 年 6 月，Andreas Hindborg 发布一组补丁，将基于 Rust 的 rnull 块驱动提升到与 C 语言 null\_blk 相同的功能水平。该驱动接受所有请求并尽快完成，用于块层基准测试；此前主线路内核已包含最小版 rnull，这组补丁补齐了剩余的 Rust 抽象。驱动使用 pin\_init\_scope\(\)进行固定初始化，通过 Operations trait 和\#\[vtable\]宏生成与 C 实现不可区分的操作表，并实现 configfs 属性，包括 badblocks 等错误注入配置。核心请求处理函数 queue\_rq\_internal\(\)负责处理 flush、轮询和直接完成等路径。这一进展表明 Rust 内核 API 已经足以编写功能完整的块驱动，并支持 Rust 与 C 实现的直接比较。

rss · LWN.net · 8月28日 18:26

**「背景」** null\_blk 是一个人为接受所有请求并立即完成的小型块驱动，主要用于基准测试块层实现。Rust 编写的 rnull 驱动是它的对应物，目的是展示可以用 Rust 内核 API 编写块驱动并便于直接对比；最小版 rnull 早已合入主线，本次补丁集让其达到功能对等。

**「影响」** 这一进展使内核开发者现在有了一个与 C null\_blk 功能对等的 Rust 参考实现，可直接用于评估 Rust 块驱动 API 的成熟度并指导后续 Rust 块驱动的开发。

**标签**: `#rust`, `#linux-kernel`, `#block-driver`, `#kernel-development`, `#systems-programming`

---

<a id="item-tech-news-5"></a>
### [八个稳定内核版本修复可致内核崩溃的漏洞](https://lwn.net/Articles/1091118/) ⭐️ 7.0/10

Greg Kroah-Hartman 宣布发布 8 个稳定内核版本：7.2.2、7.1.12、6.18.48、6.12.107、6.6.155、6.1.186、5.15.219 和 5.10.268。每个版本均包含对 CVE-2026-80590 的单一修复，该漏洞允许将 IPv4 或 IPv6 分片标记为 GSO（通用分段卸载），非特权用户可利用其触发内核崩溃。此漏洞自 Linux 2.6.27 以来一直存在，官方建议用户尽快升级。

rss · LWN.net · 8月28日 13:42

**「背景」** GSO（通用分段卸载）是一种内核网络优化技术，允许将较大的网络数据包交给网卡在硬件中分段，以提升传输性能。该漏洞利用畸形 IPv4/IPv6 分片被错误标记为 GSO 的条件，使内核在处理时陷入崩溃；由于相关代码路径早在 Linux 2.6.27 中就已引入，因此影响多个长期支持分支。

**「影响」** 运行上述稳定分支的系统管理员应尽快升级到对应的修复版本，否则本地非特权用户可通过发送精心构造的 IPv4/IPv6 分片触发内核崩溃，造成拒绝服务。

**标签**: `#linux kernel`, `#security`, `#CVE`, `#stable release`, `#networking`

---

<a id="item-tech-news-6"></a>
### [谷歌 Gemini Omni 1.1 Flash：40 秒视频生成与 4K 输出](https://blog.google/innovation-and-ai/technology/developers-tools/build-with-gemini-omni-1-1-flash/) ⭐️ 7.0/10

谷歌宣布面向开发者推出 Gemini Omni 1.1 Flash，可通过 Gemini API 和 Google AI Studio 使用。该模型支持视频场景扩展：可参考此前生成的 10 秒画面，按 10 秒递增延长至累计 40 秒。开发者还可指定首尾关键帧、生成 360p 草稿，并输出 1080p 或 4K 高清视频。此次更新为 AI 视频创作提供更强的创意控制与更长时长支持。

telegram · zaihuapd · 8月28日 01:00

**「背景」** Gemini Omni 1.1 Flash 是谷歌推出的多模态 AI 模型，面向开发者提供视频生成与编辑能力。该版本允许以 10 秒为增量将场景扩展至最长 40 秒，支持指定首尾关键帧来控制内容，并可先生成 360p 草稿再放大到 1080p 或 4K 高清输出。模型通过 Gemini API、Google AI Studio 等渠道提供，开发者可将其集成到应用中。

**「影响」** 使用 Gemini API 或 Google AI Studio 的开发者现在可以生成最长 40 秒、最高 4K 的视频，并通过关键帧控制提升前后段衔接一致性。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://explainx.ai/blog/gemini-omni-1-1-flash-video-generation-update-august-2026">Gemini Omni 1.1 Flash: 40s Extensions, $0.03/s Drafts (Aug ...</a></li>
<li><a href="https://www.gadgets360.com/ai/news/google-gemini-omni-1-1-flash-with-4k-video-40-second-extension-support-11970476">Google Unveils Gemini Omni 1.1 Flash With 4K Video and 40 ...</a></li>
<li><a href="https://blog.google/innovation-and-ai/technology/developers-tools/build-with-gemini-omni-1-1-flash/">Build with Gemini Omni 1.1 Flash - The Keyword</a></li>

</ul>
</details>

**标签**: `#Gemini`, `#video generation`, `#Google AI`, `#AI models`, `#creative tools`

---

<a id="item-tech-news-7"></a>
### [OpenAI 开发常驻 Codex 代理，可自主续作直至休眠](https://www.wired.com/story/openai-is-developing-a-persistent-ai-agent/) ⭐️ 7.0/10

据 WIRED 审查的代码，OpenAI 正在为命令行版 Codex 添加“常驻模式”，让代理持续工作直至被“休眠”，不同于现有模式在几分钟或几小时后即停止。该模式内置“主动性”设定，可在回答请求后自行创建后续任务，跨会话执行，并依据对用户的了解决定工作内容；但改动用户系统之外的东西仍需事先批准。OpenAI 确认正在测试该功能，但暂无近期上线计划。这一进展表明 AI 代理正从单次交互转向持续自主运行，对软件工程和自动化工作流具有潜在意义。

telegram · zaihuapd · 8月28日 02:47

**「背景」** OpenAI 的 Codex 是一款面向软件开发者的命令行 AI 代理，此前版本的代理会话通常在几分钟或几小时后结束。据 WIRED 审查的代码，OpenAI 开始为其添加“常驻模式”（Persistent mode），该模式会让代理持续工作直到被用户“休眠”，并能创建后续任务跨会话执行，同时仍需事先批准才能修改用户系统之外的内容。OpenAI 已确认正在测试这一功能，但尚未公布上线时间表。

**「影响」** 该功能若落地，将让使用命令行 Codex 的开发者获得可自主规划并跨会话执行任务的常驻代理，可能显著改变 AI 辅助编程和自动化工作流；但 OpenAI 未公布上线时间，实际能力与限制仍待验证。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.wired.com/story/openai-is-developing-a-persistent-ai-agent/">OpenAI Is Developing a ‘Persistent’ AI Agent | WIRED</a></li>

</ul>
</details>

**标签**: `#AI agents`, `#OpenAI`, `#Codex`, `#software engineering`, `#autonomous systems`

---

<a id="item-tech-news-8"></a>
### [美国法官叫停五角大楼拉黑 Anthropic](https://www.bloomberg.com/news/articles/2026-08-28/anthropic-wins-court-challenge-to-us-supply-chain-risk-label?srnd=phx-technology) ⭐️ 7.0/10

美国旧金山地区法官裁定，特朗普政府必须解除对 Anthropic 人工智能技术用于联邦机构的禁令，理由是国防部将 Claude 开发商列为供应链风险缺乏充分依据，且可能意在因其批评政府而“杀鸡儆猴”。Anthropic 表示欢迎裁决，并称将继续与政府合作。此前 Anthropic 与五角大楼的军事 AI 谈判破裂后被列入供应链风险名单，随后提起诉讼。该裁决为 Anthropic 在政府市场的准入扫清障碍，但案件后续发展仍待观察。

telegram · zaihuapd · 8月28日 03:15

**「背景」** 供应链风险标签是美国政府用于限制特定科技公司与联邦机构合作的机制，通常以国家安全为由实施。Anthropic 是开发 Claude 系列大模型的公司，曾试图与五角大楼开展军事 AI 合作，但谈判破裂后被列入禁令名单，进而引发法律挑战。

**「影响」** 该裁决直接要求国防部解除对 Anthropic 技术的禁令，意味着联邦机构可重新使用其 AI 服务；但若政府上诉或后续程序推翻裁决，实际效果仍不确定。

**标签**: `#AI regulation`, `#Anthropic`, `#government procurement`, `#legal`, `#Claude`

---

<a id="item-tech-news-9"></a>
### [智谱开源 GLM-5.3，专注智能体编程与网络防御](http://z.ai/) ⭐️ 7.0/10

智谱 AI 发布了开源模型 GLM-5.3，主要面向智能体编程与网络防御场景，权重已开放下载、运行和定制。该模型与 GLM-5.2 共用同一基础模型，全部提升来自后训练，在复杂编程和长周期任务上表现明显增强：Terminal Bench 2.1 得分 88.2，DeepSWE 得分 66.9，均大幅领先 GLM-5.2。GLM-5.3 采用自定义的 GLM-5.3 License，个人与中小企业可自由使用、微调与商用，但连续 12 个月营收超 100 亿美元且对外提供模型即服务的公司，须先通过 Z.AI 的安全审查。目前消息来自 Telegram 转发，具体技术细节仍较简略。

telegram · zaihuapd · 8月28日 15:32

**「背景」** GLM-5.3 是智谱 AI（Z.ai）在 GLM-5 系列下继 GLM-5.2 之后发布的开源权重旗舰模型，主打智能体编程与网络防御场景，官方称其为目前最强的开源权重编程模型，支持 100 万 token 上下文和 12.8 万 token 最大输出。此次改进与 GLM-5.2 共用基础模型，全部提升来自后训练，并且在 Terminal Bench、DeepSWE 等公开基准上取得开源领先成绩；模型可通过 GLM Coding Plan 使用，并兼容 ZCode、Claude Code、OpenCode 等编程代理。

**「影响」** 该开源模型为开发者提供了在智能体编程和网络防御场景下能力显著提升的选项，同时通过分层许可让个人和中小企业免费商用，而大型模型服务提供商需接受 Z.AI 安全审查，这可能影响企业选择和使用该模型的方式。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://github.com/zai-org/GLM-5">GitHub - zai-org/GLM-5: GLM-5: From Vibe Coding to Agentic Engineering · GitHub</a></li>
<li><a href="https://glm5.app/glm-5-3">GLM 5.3 Chat &amp; API: Z.ai New Flagship Model | GLM 5</a></li>
<li><a href="https://the-decoder.com/zhipu-ai-releases-glm-5-3-claims-its-the-strongest-open-weights-coding-model/">Zhipu AI releases GLM-5.3, claims it&#x27;s the strongest open-weights coding model</a></li>

</ul>
</details>

**标签**: `#GLM`, `#open-source`, `#AI model`, `#agentic programming`, `#Zhipu AI`

---

## 财经新闻

<a id="item-finance-news-1"></a>
### [玉米和小麦价格跃升至三年多来最高](https://www.cnbc.com/2026/08/28/corn-and-wheat-prices-jump-to-highest-prices-in-more-than-three-years.html) ⭐️ 8.0/10

玉米和小麦期货价格跃升至三年多来最高：周五小麦结算价报每蒲式耳 784 美分，周涨 12.1%，为 2022 年 3 月以来最大单周涨幅；玉米结算价报每蒲式耳 536.5 美分，周涨 5.5%。两者年迄今分别上涨 54.5%和 21.8%。

rss · CNBC Finance · 8月28日 20:00

**「背景」** 上涨原因不同：小麦主要受俄罗斯与乌克兰在黑海地区的紧张局势和出口中断影响，玉米则主要受美国供应前景疲弱及乌克兰出口受限影响。

**「影响」** 由于俄罗斯和乌克兰合计占全球小麦出口超过四分之一，供应中断可能加剧依赖进口国家的粮食供应压力。

**标签**: `#wheat`, `#corn`, `#commodities`, `#agriculture`, `#supply disruption`

---

<a id="item-finance-news-2"></a>
### [第九巡回法院裁定体育赛事合约不属于联邦监管掉期](https://www.cnbc.com/2026/08/28/appeals-court-rules-against-prediction-markets-tees-up-scotus-fight.html) ⭐️ 8.0/10

美国第九巡回上诉法院裁定，预测市场上的体育赛事合约不属于联邦监管的“掉期”，州博彩监管机构有权阻止相关平台运营。这一裁决与第三巡回法院先前的判决相冲突，为最高法院受理创造了条件。

rss · CNBC Finance · 8月28日 21:57

**「背景」** 此案起因于内华达州博彩控制委员会要求 Kalshi、Crypto.com 和 Robinhood 停止体育赛事合约交易，州方认为这属于体育博彩；商品期货交易委员会（CFTC）则主张所有赛事合约都是由其专属监管的掉期。

**「影响」** 该裁决意味着 Kalshi 等平台可能无法在内华达州等州提供此类体育赛事合约，而 DraftKings 和 Flutter 等体育博彩运营商被视为受益者。

**标签**: `#prediction markets`, `#CFTC`, `#regulation`, `#sports betting`, `#circuit split`

---

<a id="item-finance-news-3"></a>
### [PayPal 盘前暴跌近 16%，Affirm 与 Gap 大涨](https://www.cnbc.com/2026/08/28/stocks-making-the-biggest-moves-premarket-pypl-afrm-gap-mrvl.html) ⭐️ 8.0/10

8 月 28 日盘前，PayPal 股价重挫近 16%，因有报道称 Advent 和 Stripe 放弃收购；Affirm 和 Gap 分别上涨 13%和近 15%，前者季度营收超预期，后者上季盈利超预期并宣布 Old Navy 新任 CEO。

rss · CNBC Finance · 8月28日 11:43

**「背景」** 报道援引知情人士称，若交易完成，这本可能成为规模最大的杠杆收购（即以借贷资金为主的大型收购）之一。

**标签**: `#earnings`, `#acquisitions`, `#fintech`, `#stock movers`, `#guidance`

---

<a id="item-finance-news-4"></a>
### [两部门：个人住房贷款期限上限从 30 年延长至 40 年](https://news.ifeng.com/c/8vxm6huJOMR) ⭐️ 8.0/10

中国人民银行与国家金融监督管理总局 28 日联合印发意见，将个人住房贷款期限由最长 30 年延长至最长 40 年。新规给予借贷双方更大灵活度，具体期限由购房人与商业银行协商确定。

telegram · zaihuapd · 8月28日 12:16

**「背景」** 中国人民银行与国家金融监督管理总局于 28 日联合印发《关于改革完善房地产信贷管理 推动加快构建房地产发展新模式的意见》，将个人住房贷款期限上限由 30 年延长至 40 年，具体期限由购房人与商业银行协商确定；配套安排还涉及存量贷款可协商调整还款安排、住房租赁团体购房贷款期限最长 30 年等。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://wallstreetcn.com/articles/3780570">两部门： 个 人 住 房 贷 款 期 限 由最 长 30 年 延 长 至最 长 40 ...</a></li>
<li><a href="https://www.163.com/dy/article/L5ER3MJ00512D03F.html?clickfrom=w_house">163.com/dy/article/L5ER3MJ00512D03F.html?clickfrom=w_house</a></li>

</ul>
</details>

**标签**: `#China`, `#real estate`, `#mortgage policy`, `#central bank`, `#housing loans`

---