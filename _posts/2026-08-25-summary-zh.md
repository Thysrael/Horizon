---
layout: default
title: "Horizon Summary: 2026-08-25 (ZH)"
date: 2026-08-25
lang: zh
---

> 从 43 条内容中筛选出 11 条重要资讯。

---

**科技新闻**
1. [MS Paint 与 Photos 为 AI 图片添加隐形 GUID 水印](#item-tech-news-1) ⭐️ 8.0/10
2. [seL4 完成 AArch64 架构正式安全证明](#item-tech-news-2) ⭐️ 8.0/10
3. [AI 编码依赖将削弱编程专业技能](#item-tech-news-3) ⭐️ 8.0/10
4. [旧金山整座城市被做成可交互 3D 网页演示](#item-tech-news-4) ⭐️ 7.0/10
5. [你的可执行文件可以是 SQLite 数据库](#item-tech-news-5) ⭐️ 7.0/10
6. [量子计算威胁 ECDSA，软件需提前迁移后量子密码](#item-tech-news-6) ⭐️ 7.0/10
7. [Emacs 31.1 发布：移除 dumper，新增用户 Lisp 目录](#item-tech-news-7) ⭐️ 7.0/10
8. [阿里云 Wan3.0 正式上线：30 秒视频生成 API 最低 0.3 元/秒](#item-tech-news-8) ⭐️ 7.0/10

**科技博客**
1. [AI 时代代码验证为何更加关键](#item-tech-blog-1) ⭐️ 7.0/10
2. [Groq 3 LPX：确定性调度解锁长上下文高交互推理](#item-tech-blog-2) ⭐️ 7.0/10

**财经新闻**
1. [阿里巴巴配股筹资 102 亿美元用于 AI，股价大跌](#item-finance-news-1) ⭐️ 8.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [MS Paint 与 Photos 为 AI 图片添加隐形 GUID 水印](https://xusheng.dev/posts/reversing/mspaint_invisible_watermark/main/) ⭐️ 8.0/10

据 xusheng.dev 的逆向工程分析，微软的 MS Paint 和 Microsoft Photos 会在经 AI 编辑的图片中静默嵌入基于 GUID 的隐形水印。这一行为即使在完全使用本地模型执行编辑时也会发生。可见水印可以被关闭，但隐形水印无法禁用，并且用户不会得到任何提示。作者指出目前尚不清楚 AI 增强的背景删除或移除等操作是否也会触发该水印。该发现引发隐私担忧，因为唯一标识可能将图像与用户的微软账户关联。

hackernews · ComputerGuru · 8月24日 15:28 · [社区讨论](https://news.ycombinator.com/item?id=49421158)

**「背景」** 微软的画图（MS Paint）和照片（Photos）应用在本地生成 AI 图像时，会先向 Azure Front Door 端点发送一次强制远程审核请求，获得一个服务器下发的 GUID。研究员通过逆向 Watermarker.dll 确认，该 GUID 会被编码成不可见水印（约 18 字节载荷），分散嵌入到大约 74%的图像像素中；如果水印嵌入步骤失败，画图会直接取消图像生成。用户只能关闭可见水印，无法禁用这种静默的隐形标记，即使 AI 操作完全在本地完成也不例外。

**「影响」** 最直接的后果是，使用 MS Paint 或 Photos 进行 AI 编辑的用户会在不知情且无法关闭的情况下获得带唯一 GUID 的图片；这可能让图片与微软账户产生关联，从而削弱匿名性并带来隐私风险。目前尚不清楚触发范围，因此影响存在不确定性。

**「社区讨论」** 评论中多数人认为真正的风险不是 AI 功能本身，而是每张图片被偷偷加入唯一标识；有人举出微软此前将 Azure DevOps 提交错误标记为 Copilot 水印的案例，并建议避免使用 Paint 等应用。也有用户称自己曾遇到误触发，但相关评论被截断。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://xusheng.dev/posts/reversing/mspaint_invisible_watermark/main/">Microsoft Paint and Photos Embed Server-Issued GUIDs as ...</a></li>
<li><a href="https://mangodeveloper.com/articles/microsoft-paint-embeds-invisible-guid-watermarks-in-local-ai-images-via-remote-moderation-server">Microsoft Paint Embeds Invisible GUID Watermarks in Local AI ...</a></li>
<li><a href="https://byteiota.com/ms-paint-invisible-server-guid-watermark-ai-image/">MS Paint Embeds Invisible Server GUIDs in Every AI Image</a></li>

</ul>
</details>

**标签**: `#privacy`, `#watermarking`, `#microsoft`, `#AI`, `#image processing`

---

<a id="item-tech-news-2"></a>
### [seL4 完成 AArch64 架构正式安全证明](https://proofcraft.systems/news-2026/#2026-08-21) ⭐️ 8.0/10

2026 年 8 月 21 日，seL4 微内核的正式安全证明已在 AArch64 架构上完成，将可验证的高保证覆盖扩展到 ARM 64 位系统。这是操作系统形式化验证领域的一项重要工程里程碑，但属于对既有证明方法的增量扩展，而非全新范式。当前证明仅覆盖非 MCS（混合关键性系统）单核配置，尚未包含多核架构及 MCS 扩展。该进展有助于增强汽车、军事等嵌入式领域基于 seL4 的系统的安全论证基础，并延续了该项目在 x86、RISC-V 等架构上的验证工作。

hackernews · snvzz · 8月24日 11:32 · [社区讨论](https://news.ycombinator.com/item?id=49418255)

**「背景」** seL4 是一个经过形式化验证的微内核，其核心设计目标是通过数学证明确保安全隔离等关键安全属性。此前，seL4 的验证工作主要覆盖 32 位架构，而 AArch64（64 位 ARM 架构）上的完整安全证明是新里程碑。该证明确认 seL4 在 AArch64 上的实现代码能够强制执行应用程序之间的安全隔离，但需满足特定的假设条件，包括非 MCS（混合关键性系统）配置和单核（unicore）环境。

**「影响」** 这项里程碑完成了 seL4 在 AArch64 架构上的形式化安全证明，即 seL4 实现代码能够在所列假设下强制执行运行于其上的应用之间的安全隔离；这使得 AArch64 在功能正确性保证上与 Arm 32 位、RISC-V 64 位和 Intel x86 64 位处于同等水平，为在 ARM 64 位平台上使用 seL4 的系统安全关键型用户提供了更强的高保证依据，但仍需注意其前提条件（如非 MCS、单核）限制。

**「社区讨论」** 评论中有用户提醒该证明的适用范围有限，仅覆盖非 MCS 单核配置；也有观点认为侧信道时序攻击可能完全颠覆这一安全结论。另有用户讨论 seL4 的实际部署与前景，提到 GenodeOS、LionsOS、某中国车企将其用作汽车超管理器，并认为嵌入式与军事市场仍会持续资助，但若想真正提升系统安全性，需要原生 seL4/Linux 方案，而安全启动虚拟化平台已屡见不鲜。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://lists.sel4.systems/hyperkitty/list/announce@sel4.systems/thread/ZL6HYXH3PKI6XUVKMPTLIPKQMWJW7N7M/">seL 4 security proofs now complete on AArch 64 ... - lists. sel 4 .systems</a></li>
<li><a href="https://sel4.systems/">The seL4 Microkernel | seL4</a></li>
<li><a href="https://sel4.systems/Summit/2024/abstracts2024.html">seL4 Summit 2024 Abstracts | seL4</a></li>

</ul>
</details>

**标签**: `#seL4`, `#formal verification`, `#operating systems`, `#AArch64`, `#security`

---

<a id="item-tech-news-3"></a>
### [AI 编码依赖将削弱编程专业技能](https://larsfaye.com/articles/ai-coding-will-prevent-expertise) ⭐️ 8.0/10

观点文章作者 larsfaye 认为，过度依赖 AI 编码工具会侵蚀程序员的深层专业技能，导致“编码专业知识崩溃”。文章指出，工程师正在以超出人类理解和审查能力的速度生产代码，而长期技能形成所需的“摩擦”正被 LLM 消除。该文在 Hacker News 上引发广泛讨论，获得 426 分和 424 条评论，反映出从业者对此话题的高度共鸣。虽然文章并非突破性研究，但提供了有价值的视角，并促使人们思考 AI 辅助开发对专业能力发展的影响。

hackernews · larsfaye · 8月24日 15:52 · [社区讨论](https://news.ycombinator.com/item?id=49421554)

**「背景」** 这篇文章由 Lars Faye 撰写，核心观点是过度依赖 AI 编码工具会削弱开发者的深度专业技能，作者称之为“管线崩塌”（pipeline collapse）：如果大语言模型能够编写和调试代码，代理工作流也能基于训练数据中的大量模式进行系统设计，那么人类掌握这些知识的目的何在。文章还讨论了长期技能形成中对“摩擦”（friction）的需求，即学习过程中适当的困难和挫折是成长所必需的。社区对此展开了热烈讨论，有人赞同企业层面已出现“手动写代码就是错”的现象，也有人认为结合 LLM 的引导式编码（guided coding）比纯 AI 编码更高效且质量更高，而另一些人则担忧 AI 生成的劣质代码会让保持清醒的开发者不堪重负。

**「影响」** 在企业管理层强制推广 AI 编码工具的趋势下，开发者正以超出人工审查能力的速度产出代码，这可能让大量未经充分审查的 AI 生成代码进入生产系统，并削弱工程师长期积累的深度调试与系统设计能力；现有研究虽然显示 AI 助手能提升生产效率和部分企业指标，但专业开发者对其长期职业影响仍存在明显担忧。

**「社区讨论」** 评论中呈现明显分歧：ryandvm 指出企业层面已出现“手工写代码就是错”的领导指令，但工程师产出代码的速度远超人类理解和审查能力；apatheticonion 则强调引导式编码（guided coding）结合 LLM 能兼具高效率和高质量，而 LandoCalrissian 担忧“蛇咬自己尾巴”的循环不可持续；xyzelement 提出长期技能形成需要持续摩擦，部分人会在新位置寻找摩擦；作为技术教育者的 TonyAlicea10 完全同意文章观点。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://news.ycombinator.com/item?id=49421554">Coding expertise is going to collapse from AI reliance | Hacker News</a></li>
<li><a href="https://larsfaye.com/articles/ai-coding-will-prevent-expertise">AI Coding will Prevent Expertise | Lars Faye</a></li>
<li><a href="https://forum.devtalk.com/t/ai-coding-will-prevent-expertise-lars-faye/248226">AI Coding will Prevent Expertise | Lars Faye - AI In The News - Devtalk</a></li>
<li><a href="https://arxiv.org/html/2605.23135v1">The Impact of AI Coding Assistants on Software Engineering: A ...</a></li>
<li><a href="https://www.semanticscholar.org/paper/The-Impact-of-AI-Coding-Assistants-on-Software-A-Vella-Blincoe/37bd54722fc53256a6914728096a50eb119e41c2">[PDF] The Impact of AI Coding Assistants on Software ...</a></li>
<li><a href="https://worldmetrics.org/ai-coding-assistant-industry-statistics/">Ai Coding Assistant Industry: 2026 Verified Stats</a></li>

</ul>
</details>

**标签**: `#AI coding`, `#software engineering expertise`, `#LLM impact`, `#developer productivity`, `#skill formation`

---

<a id="item-tech-news-4"></a>
### [旧金山整座城市被做成可交互 3D 网页演示](https://sf.thijs.gg/) ⭐️ 7.0/10

一个名为 sf.thijs.gg 的网页应用将旧金山市渲染成可交互的 3D 环境，结合高程、建筑等地理空间数据，并支持驾驶车辆、收集金币等简单玩法，引发大量开发者讨论。该项目展示了用开源地理数据构建城市级 Web 3D 场景的潜力，但并非重大技术突破。社区反馈包括希望加入街景纹理、街道名称、地标、地址传送和更高分辨率本地版本，也有人提到 Safari 下会卡死且难以关闭页面。相关链接由用户 @cdngdev 在 Twitter 上分享。

hackernews · centrosphere · 8月24日 17:05 · [社区讨论](https://news.ycombinator.com/item?id=49422784)

**「背景」** 该网页应用将旧金山整座城市渲染为可交互的 3D 环境，用户可以在其中探索街道、建筑和地形，项目还提供了细节模式选项。这类项目通常基于地理空间数据构建，并可通过浏览器或移动端访问；该项目的相关应用也可在 Google Play 上获取。

**「影响」** 对 Web 开发者和地图技术爱好者而言，这个演示是了解城市级 3D 数据管线与渲染实现的直观范例；但 Safari 用户需谨慎，因为在部分新款 MacBook Pro 上它会冻结浏览器并可能难以关闭标签页。

**「社区讨论」** 评论者普遍赞赏该项目，有位在旧金山居住近 20 年的用户称在虚拟街区中漫步让他感动；同时有人建议加入街景纹理、街道名称、地址传送和实时多人玩法，也有人报告 Safari 崩溃并提供规避方法。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://sf.thijs.gg/">San Francisco -- The Game</a></li>
<li><a href="https://progscrape.com/?search=sf.thijs.gg">progscrape: sf . thijs . gg</a></li>

</ul>
</details>

**标签**: `#3D rendering`, `#geospatial data`, `#web graphics`, `#interactive maps`, `#demo`

---

<a id="item-tech-news-5"></a>
### [你的可执行文件可以是 SQLite 数据库](https://simonwillison.net/2026/Aug/24/your-executable-is-a-sqlite-database/) ⭐️ 7.0/10

Farid Zakaria 发布了一种 Linux 技巧，让 SQLite 数据库文件能直接作为可执行程序运行。他在 SQLite 文件格式偏移 68 字节的 4 字节应用 ID 中写入“SELF”（代表 Structured Executable &amp; Linkable Format），并把 ELF 可执行格式的各组件安排进多个 SQLite 表，配合 self-exec 解释器（C 代码）提取并执行相应部分。还可以通过 binfmt\_misc 注册模式，让内核在遇到匹配的二进制时自动调用解释器，例如在 NixOS 或使用类似 echo 到 /proc/sys/fs/binfmt\_misc/register 的方式。这项技巧提供了一种新颖的程序打包方式，把数据库既当作数据存储又当作可执行文件。

rss · Simon Willison · 8月24日 11:38

**「背景」** SQLite 数据库文件有固定文件头和应用 ID 字段；ELF 是 Linux 可执行文件的标准格式。binfmt\_misc 是 Linux 内核机制，可以按文件头模式把非原生二进制交给指定解释器执行。该技巧将 ELF 结构拆解为 SQLite 表，利用应用 ID 作为识别标记，从而让数据库文件本身具有可执行性。

**「影响」** 这项技术让 Linux 开发者能把程序组件存储在 SQLite 表中并直接以数据库文件作为可执行程序，为工具分发和自包含程序提供了一种新的打包思路，但需要额外注册 binfmt\_misc 才能在没有定制加载逻辑的系统上运行。

**标签**: `#sqlite`, `#linux`, `#executables`, `#binfmt-misc`, `#low-level software`

---

<a id="item-tech-news-6"></a>
### [量子计算威胁 ECDSA，软件需提前迁移后量子密码](https://lwn.net/Articles/1088305/) ⭐️ 7.0/10

量子计算对 ECDSA 等公钥密码的实际威胁正在加速：2026 年有研究展示量子分解 ECDSA 密钥所需内存大幅下降，最佳逻辑量子比特数从 1425 降至 1154，同时 IBM 宣称其 Kookaburra 处理器（1386 物理量子比特）将在 2026 年底完成。因此软件需要提前迁移到后量子密码学。主流浏览器已默认启用 X25519MLKEM768 混合密钥交换，Firefox 132、Chrome 131、Safari 26 均支持；OpenSSL 3.5.0 起支持后量子密钥交换，更早版本可借助 oqs-provider。量子纠错仍需约 500 物理量子比特模拟 1 个逻辑量子比特，实际攻击距离仍存在不确定性。

rss · LWN.net · 8月24日 14:57

**「背景」** 现代互联网公钥加密依赖大整数分解或离散对数等经典困难问题，而量子计算机可高效求解这些特定问题。后量子密码学基于尚无已知量子算法的数学问题，NIST 已标准化 ML-KEM 等方案；混合方案同时使用传统椭圆曲线和新后量子算法，只要其中一个安全即可保证整体安全。

**「影响」** 对运维和开发者的直接影响是：应尽快将 TLS 服务器迁移到 OpenSSL 3.5.0+ 或使用 oqs-provider 启用 X25519MLKEM768，以保护当前加密流量免受未来量子破解和“先收集、后解密”攻击。

**标签**: `#quantum computing`, `#cryptography`, `#ECDSA`, `#post-quantum security`, `#security`

---

<a id="item-tech-news-7"></a>
### [Emacs 31.1 发布：移除 dumper，新增用户 Lisp 目录](https://lwn.net/Articles/1090308/) ⭐️ 7.0/10

Emacs 31.1 已正式发布，主要变化包括移除 Emacs dumper、新增用户 Lisp 目录支持，并在 context-menu-mode 中添加“发送到…”菜单项。该版本提供 gzip 和 xz 格式的签名 tarball，可从 GNU 镜像下载，并附有 SHA256/SHA512 校验值；完整变更记录见 etc/NEWS 文件，可在 Emacs 内按 C-h n 或在线查看。移除 dumper 是一次重要的内部结构调整，可能影响依赖旧转储机制的启动流程；用户 Lisp 目录则改善了第三方 Lisp 代码的组织和加载。Mastering Emacs 作者 Mickey Petersen 也撰文介绍了此次发布中的诸多生活质量改进。

rss · LWN.net · 8月24日 13:36

**「背景」** Emacs 是一款历史悠久的可扩展文本编辑器，其功能大多通过内置的 Emacs Lisp 实现。31.1 是一个主要版本，移除了传统的 unexec/dumper 机制，并新增了用户 Lisp 目录：将 Lisp 文件放入配置目录下的 user-lisp/ 子文件夹后，Emacs 会自动递归字节编译它们并将其加入 load-path，同时自动设置 autoload，方便管理独立于 init.el 的配置包。

**「影响」** 需要基于 Emacs dumper 进行启动优化或定制构建的开发者应当评估并迁移到新的机制；普通用户升级后可以利用新增的用户 Lisp 目录和“发送到…”菜单项。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.linuxcompatible.org/story/gnu-emacs-311-released-terminal-mouse-support-editable-grep-and-a-major-completion-overhaul">GNU Emacs 31.1 Released: Terminal Mouse Support, Editable Grep, and a Major Completion Overhaul</a></li>
<li><a href="https://www.warp2search.net/story/gnu-emacs-311-released-terminal-mouse-support-editable-grep-and-a-major-completion-overhaul">GNU Emacs 31.1 Released: Terminal Mouse Support, Editable Grep, and a Major Completion Overhaul</a></li>

</ul>
</details>

**标签**: `#emacs`, `#editor`, `#software-release`, `#open-source`, `#lisp`

---

<a id="item-tech-news-8"></a>
### [阿里云 Wan3.0 正式上线：30 秒视频生成 API 最低 0.3 元/秒](https://mp.weixin.qq.com/s/peeeU6cBz4AaROvFe1zqQQ) ⭐️ 7.0/10

阿里云今日正式上线视频生成模型 Wan3.0，支持最长 30 秒视频生成，并在人物质感、参考精准一致性和非写实风格化方面表现突出。用户可通过阿里云百炼、万相官网、千问 APP 等平台体验。API 价格按分辨率计费：480P 为 0.3 元/秒，720P 为 0.6 元/秒，1080P 为 1.2 元/秒。8 月 24 日至 9 月 23 日，阿里云百炼和千问 AI 平台提供 API 限时 7 折优惠。

telegram · zaihuapd · 8月24日 10:14

**「背景信息」** 万相（Wan）是阿里云推出的视频生成模型系列，Wan3.0 为该系列的最新版本，已于 2026 年 8 月 6 日开启公测并被官方称为“最强视频模型”。与以往版本相比，Wan3.0 单次可生成最长 30 秒视频，并首次支持 doc、xls、ppt、pdf、md 等文档格式输入，无需重新格式化即可用于视频生成。

**「影响」** 对于需要生成短视频的开发者与企业，Wan3.0 提供了分辨率分层且带限时折扣的 API 选项，可能降低视频生成的集成成本；当前 7 折优惠窗口至 9 月 23 日结束。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://aihot.virxact.com/story/a99af99d-0dff-4752-a453-37de2d1a0c65">Alibaba Cloud releases Wan 3 . 0 · AI HOT</a></li>
<li><a href="https://juejin.cn/post/7670593377075724339">juejin.cn/post/7670593377075724339</a></li>

</ul>
</details>

**标签**: `#阿里云`, `#视频生成`, `#AI模型`, `#产品发布`, `#API`

---

## 科技博客

<a id="item-tech-blog-1"></a>
### [AI 时代代码验证为何更加关键](https://blog.bytebytego.com/p/why-code-verification-matters-more) ⭐️ 7.0/10

rss · ByteByteGo · 8月24日 15:31

**「背景」** 作者观察到，随着 AI 编程工具让代码生成变得又快又便宜，软件开发的瓶颈正在从“写出代码”转向“验证代码”。作者认为，验证是一整套建立信任的检查工作，而且信任只能逐步挣来，不能一次授予。

**「方案」** 作者把代码验证比作一组叠放的过滤器：类型检查与 lint 最先且成本最低，单元测试捕捉行为错误，人工评审处理机器难以判断的架构与上下文问题，生产监控兜底。这些检查分为静态分析与动态分析，且每个过滤器都必须在误报与漏报之间权衡；同一问题越晚发现成本越高，所以“左移”价值真实存在。作者援引 DORA 研究指出采用 AI 后交付稳定性下降，METR 试验也显示 AI 辅助任务耗时更长。AI 的冲击体现在两个方向：一是代码量激增、单次改动变大，评审负担上升；二是模型更擅长生成能运行的代码，但安全缺陷并未同步减少。作者提醒，让 AI 复查 AI 可能只是把同一种盲点重复一遍，因此成熟流程需要共享上下文、多层次自动化检查，并将验证深度按风险调节。团队还可以把检查提前到粘贴代码前的终端，防止密钥随 AI 会话泄露。

**「启示」** 作者的结论是，软件开发的中心正在从生成代码转向验证代码；当写代码变便宜，工程师真正稀缺的是判断力、风险校准与对“该构建什么”的理解。代码验证因此不是可以被跳过的步骤，而是 AI 时代保证软件可信的核心能力。

**标签**: `#code-verification`, `#ai-code-review`, `#software-quality`, `#static-analysis`, `#shift-left-testing`

---

<a id="item-tech-blog-2"></a>
### [Groq 3 LPX：确定性调度解锁长上下文高交互推理](https://developer.nvidia.com/blog/how-nvidia-groq-3-lpx-unlocks-ultrafast-interactivity-at-long-context-on-nvidia-vera-rubin/) ⭐️ 7.0/10

rss · NVIDIA Inference Performance Blog · 8月24日 15:00

**「背景」** 智能体会话是多轮推理，每轮输出都会追加到不断增长的上下文中，后期模型必须反复处理全部历史；因此真正可用的智能体既要快，也要在长上下文中保持速度。作者指出，传统推理系统在极小批量下难以同时满足这两点。

**「方案」** 作者解释，Groq 3 LPX 的关键不是更快的网络，而是编译器调度的确定性执行。编译器在运行前掌握 256 个 LPU、128GB SRAM 和每芯片 96 条 112Gbps C2C 链路，把每次数据传输安排到时钟周期，省去实时仲裁，把首比特延迟压到最低；每个 LPU 还可作为路由器转发数据。同时，调度以 320 字节向量为单位，把矩阵乘拆成点积，算出部分列后立刻通过 C2C 发送，从而在很小粒度上重叠计算与通信，让张量并行在小批量高交互场景下也能获得数量级加速。作者给出的第三方基准显示，在 Artificial Analysis 的 100K 上下文测试中，Gemma 4 31B 达到 3431 输出 token/秒，10K 上下文为 3382 token/秒；SPEED-Bench 中位数为 4767 token/秒。实际部署可把 Groq 3 LPX 与 Vera Rubin NVL72 配对，用 prefill-decode 分离、attention-FFN 分离或外部草稿模型投机解码，让各机架专注各自擅长的部分。

**「启示」** 作者认为，确定性调度加上细粒度通信重叠，使低延迟、小批量的长上下文推理首次接近吞吐级优化系统的效果；这是让超大规模参数智能体在长会话中保持互动性的关键。

**标签**: `#AI inference`, `#long context`, `#tensor parallelism`, `#hardware accelerator`, `#benchmark`

---

## 财经新闻

<a id="item-finance-news-1"></a>
### [阿里巴巴配股筹资 102 亿美元用于 AI，股价大跌](https://www.cnbc.com/2026/08/24/alibaba-share-placement-drop-ai-hong-kong.html) ⭐️ 8.0/10

阿里巴巴在港股公布以每股 112.70 港元配售 7.1 亿股新股，筹资 800 亿港元（约 102 亿美元）用于 AI 基础设施。配售价较上周五收盘价 123 港元折让约 8.4%，消息令股价周一盘中一度下跌 10%。

rss · CNBC Finance · 8月24日 08:21

**「背景」** 该公司此前公布的 6 月季度利润同比下跌 75%，资本开支同比增长 75%至 677 亿元人民币，并计划未来三年在云和 AI 基础设施投入至少 3800 亿元人民币。中国科技同业也在加大 AI 支出，腾讯季度资本开支环比增长 65%至 528 亿元人民币。

**「影响」** 此次配售将摊薄现有股东持股；公司称募资将全部投入 AI 能力建设，分析师认为短期利润可能继续承压，但有助于其抓住 AI 增长机会。

**标签**: `#Alibaba`, `#share placement`, `#AI investment`, `#Hong Kong stocks`, `#technology sector`

---