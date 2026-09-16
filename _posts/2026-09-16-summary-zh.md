---
layout: default
title: "Horizon Summary: 2026-09-16 (ZH)"
date: 2026-09-16
lang: zh
---

> 从 22 条内容中筛选出 12 条重要资讯。

---

**科技新闻**
1. [Typesafe.ai 发布 System One Models 与 Jev](#item-tech-news-1) ⭐️ 7.0/10
2. [Wayback Machine 访问保护与抓取压力更新](#item-tech-news-2) ⭐️ 7.0/10
3. [Google 发布 Gemini 3.8 Live 与 3.8 Live Extended Thinking](#item-tech-news-3) ⭐️ 7.0/10
4. [Strix 称 AI 代理 25 分钟取得 Baseten 生产 GitHub 权限](#item-tech-news-4) ⭐️ 7.0/10
5. [Capsule：把 HTML 应用和数据打包为单个 SQLite 文件](#item-tech-news-5) ⭐️ 7.0/10
6. [把 20 美元 4G 热点改造成可收发短信的设备](#item-tech-news-6) ⭐️ 7.0/10
7. [Schneier 发文：25 年大规模监控已经够了](#item-tech-news-7) ⭐️ 7.0/10
8. [Simon Willison 发布 Gemini 3.8 Live 浏览器语音测试界面](#item-tech-news-8) ⭐️ 7.0/10
9. [Linux 内核补丁提议为 blk-iocost 引入 BPF 成本模型](#item-tech-news-9) ⭐️ 7.0/10

**科技博客**
1. [LLM 的“记忆”其实由应用层重建](#item-tech-blog-1) ⭐️ 6.0/10
2. [Groq 3 LPX 确定性执行与能效优化](#item-tech-blog-2) ⭐️ 4.0/10

**财经新闻**
1. [中国 8 月零售增速低于预期，投资降幅加深](#item-finance-news-1) ⭐️ 8.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [Typesafe.ai 发布 System One Models 与 Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev) ⭐️ 7.0/10

Typesafe.ai 发布了 System One Models 和 Jev，将其定位为面向结构化输出的类型化推理替代方案，而非通用 LLM 生成。该发布在 Hacker News 引发讨论，评论者认可其新颖性，但质疑其速度对比是否公平：通用生成模型能输出图灵完备语言代码，理论上可完成计算机能做的任何事，而 Jev 据称只能生成结构化输出。社区从文档中理解到，模型可能接收一个状态（是否为结构化文本、是否多模态尚不明确）和一个问题（Choice、Score 或 Noul 等类型），并输出选择、概率和置信度等结果，此外还可附加增强。评论还将其与设计契约、编码器模型等已有方法比较，并提到 AI primer 页面涉及 RLCD 过程，但具体内容不完整。整体上，发布帖和评论是当前唯一证据，尚无独立验证或行业影响证明。

hackernews · albelfio · 9月15日 19:25 · [社区讨论](https://news.ycombinator.com/item?id=49717558)

**「背景」** TypeSafe AI 是一家构建面向自动化的机器原生智能基础设施、目标是让模型在软件内做决策的 AI 实验室。\[tool-1-1\] System One 模型是该公司提出的一类模型，主打快速、结构化决策，而非通用文本生成；Jev 是 TypeSafe 的首个、也是旗舰 System One 模型，已开放早期访问。\[tool-1-2\]\[tool-1-3\] 目前公开信息称 Jev 用类型化或结构化推断取代文本生成，但其最大性能宣称仍依赖内部测试，尚无独立验证。\[tool-1-3\]

**「影响」** 对需要分类、评分或结构化抽取的开发者与团队来说，Jev 可能提供比通用文本生成更快的类型化推理路径，但其能力边界明显更窄，且速度优势尚未被独立验证。

**「社区讨论」** HN 评论整体认为该工作新颖且对分类/结构化任务有潜力，但主要分歧在于速度对比的公平性：有人指出 Jev 不能像图灵完备的代码生成模型那样通用。另有评论表示官方文档比发布帖中与 LLM token 的对比更清楚，并将其与设计契约、编码器模型等已有思路联系起来。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://typesafe.ai/blog/introducing-system-one-models-and-jev">Introducing System One Models &amp; Jev - TypeSafe AI Blog</a></li>
<li><a href="https://docs.typesafe.ai/concepts/system-one">System One - TypeSafe AI</a></li>
<li><a href="https://runtimewire.com/article/typesafe-jev-system-one-ai-model-early-access">TypeSafe opens Jev early access for fast, typed AI decisions</a></li>

</ul>
</details>

**标签**: `#System One Models`, `#Jev`, `#structured inference`, `#type systems`, `#LLM`

---

<a id="item-tech-news-2"></a>
### [Wayback Machine 访问保护与抓取压力更新](https://blog.archive.org/2026/09/15/an-update-on-wayback-machine-access/) ⭐️ 7.0/10

互联网档案馆（Internet Archive）就 Wayback Machine 的访问状况发布更新，称其遭遇多轮高流量自动化请求，并已部署保护措施以维持服务运行。讨论中引述的说法认为，这些抓取者试图通过访问 Wayback Machine 的存档副本，绕过对原始站点的访问封锁，给这家非营利基础设施带来额外负载，并已促使部分网站选择退出。相关影响包括用户不时遇到 429 错误、服务可用性不稳定，但仍有用户报告可通过 Tor 匿名访问、不经过 Cloudflare 等中心化网关。社区普遍赞扬档案馆维持开放访问，同时担心 AI 训练与数据抓取竞赛带来的附带损害，并讨论监管、罚款等可能应对方式。

hackernews · ChrisArchitect · 9月15日 17:52 · [社区讨论](https://news.ycombinator.com/item?id=49716176)

**「背景」** Internet Archive 是一家非营利机构，其 Wayback Machine 长期免费提供网页历史快照，是研究者、记者与普通用户回溯已删除或已变更网页的重要公共档案。该服务按请求量进行限流，超出阈值时会返回 HTTP 429“请求过多”状态码，因此当自动抓取流量激增时，这类防护往往会同时波及正常访问的用户。据 Internet Archive 的说明，本次更新是为应对高流量自动访问而新增并调整的访问保护与 429 错误处理方式，但相关措施仍在拦截合法用户，受影响者可向该机构提供自己的 IP、浏览器和操作系统信息以寻求解决。

**「影响」** 对依赖 Wayback Machine 的研究者、记者和普通用户而言，最直接的后果是访问可能继续遭遇限流或间歇性中断。与此同时，《卫报》《纽约时报》等出版方已因担忧 AI 抓取而限制或停止被存档，这可能进一步缩小这一收录超过 1 万亿次网页抓取的档案的可用范围；目前公开信息尚未说明这些保护措施的持续时间和具体触发条件。

**「社区讨论」** 评论者普遍称赞互联网档案馆在多方压力下仍尽量维持开放访问，并有人以 Tor 匿名访问和移动网络可用作为反例，说明影响并非一概而论；主要担忧集中在 AI 抓取对公共网络资源的附带破坏，以及监管或高额罚款能否奏效，也有人不确定 429 错误是否完全由档案馆的保护措施导致。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://blog.archive.org/2026/09/15/an-update-on-wayback-machine-access/">An Update on Wayback Machine Access | Internet Archive Blogs</a></li>
<li><a href="https://www.pcmag.com/news/why-is-the-internet-archive-blocking-users-blame-the-bots">Why Is the Internet Archive Blocking Users? Blame the Bots</a></li>
<li><a href="https://aicrier.com/post/zp0pbpmzqg1ome2hrzvy">Wayback Machine Tightens Access Against Bot Traffic</a></li>
<li><a href="https://en.wikipedia.org/wiki/Internet_Archive">Internet Archive - Wikipedia</a></li>
<li><a href="https://www.facebook.com/niemanfoundation/posts/outlets-like-the-guardian-and-the-new-york-times-are-scrutinizing-digital-archiv/1478564767604770/">Outlets like The Guardian and The New York Times are scrutinizing digital archives as ... - Facebook</a></li>
<li><a href="https://www.reddit.com/r/pcmasterrace/comments/1sl7eu1/news_outlets_are_blocking_wayback_machine_from/">News outlets are blocking Wayback Machine from archiving their pages — 23 outlets concerned AI companies might abuse fair use and use it to train their models : r/pcmasterrace - Reddit</a></li>

</ul>
</details>

**标签**: `#Internet Archive`, `#Wayback Machine`, `#AI scraping`, `#web archiving`, `#internet infrastructure`

---

<a id="item-tech-news-3"></a>
### [Google 发布 Gemini 3.8 Live 与 3.8 Live Extended Thinking](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-8-live-gemini-3-8-live-extended-thinking/) ⭐️ 7.0/10

Google 发布了 Gemini 3.8 Live 和 Gemini 3.8 Live Extended Thinking，这是一组面向实时语音交互的 Gemini 模型更新，其中后者带有“扩展思考”变体。公告在 Hacker News 上获得 260 分和 177 条评论，表明开发者社区对此高度关注。当前提供的材料主要是博客公告链接，没有基准测试、技术架构或版本差异等实质细节，因此无法量化新模型相较前代的具体提升。版本号 3.8 也暗示这可能是一次增量更新，而非重大范式转变。

hackernews · leumon · 9月15日 17:38 · [社区讨论](https://news.ycombinator.com/item?id=49715947)

**「背景」** Gemini Live 是 Google 面向实时语音对话的交互模式，用户可以直接与模型进行低延迟的口语交流；本次发布的「3.8 Live Extended Thinking」则是在此基础上增加扩展思考（更长的推理过程）的变体，并支持对话中切换语言，已通过 Gemini API 与 Google AI Studio 提供，Gemini Enterprise 处于私密预览阶段。该发布属于 Gemini 3.8 系列的一部分，此前 Gemini 3.8 Flash 已在约两天前进入 Gemini 应用、AI Mode、Sheets 及开发者工具，并配有截至 2026 年 12 月的入门 API 价格，因此本次更新是同一代模型的增量扩展而非全新代际。

**「影响」** 对依赖实时语音交互的用户来说，最直接的后果是这套模型已可在 Workspace 账号中使用，而此前不少新发布在这些账号上常处于“既不够个人、也不够企业”的可用性空白；社区反馈同时指出其延迟较低、对浓重口音处理良好，因此已在语言练习、车载对话等场景产生实际价值。需要说明的是，原始博文未提供基准测试或架构细节，上述判断目前主要来自用户自述，而非官方量化数据。

**「社区讨论」** 评论整体正面：用户报告延迟低、对口音处理良好，并称该模型已可在 Workspace 账户中使用；一位用户表示用 Gemini 进行南非荷兰语实时对话和语法练习体验极佳，另一位认为 Gemini Live 虽“更笨”，但实际对话感优于 GPT Voice。批评与担忧包括 Google AI Plus 用户尚未获得 Gemini 3.8，以及 Google 在竞争中仍落后于 Fable 和 Astra、有人追问 Gemini 4 何时发布。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-8-live-gemini-3-8-live-extended-thinking/">Introducing Gemini 3.8 Live and 3.8 Live Extended Thinking</a></li>
<li><a href="https://aivy.com.au/news/gemini-3-8-live-launch/">After ChatGPT and Claude comes Gemini 3.8 Live</a></li>
<li><a href="https://techjournal.org/gemini-3-8-flash">Gemini 3.8 Flash Arrives in Gemini App and AI Mode</a></li>

</ul>
</details>

**标签**: `#Gemini`, `#Google`, `#voice assistants`, `#LLM releases`, `#multimodal AI`

---

<a id="item-tech-news-4"></a>
### [Strix 称 AI 代理 25 分钟取得 Baseten 生产 GitHub 权限](https://www.strix.ai/blog/baseten-harbor-github-pat-takeover) ⭐️ 7.0/10

安全厂商 Strix.ai 在一篇博客中声称，其 AI 渗透测试代理在约 25 分钟内发现了一个泄露的 Baseten GitHub 个人访问令牌（PAT），该令牌属于 basetenbot，并可访问 Baseten 的生产相关仓库。据其描述，该令牌拥有对 Baseten 主产品仓库、驱动其集群的 GitOps 仓库和 Homebrew tap 的管理员/推送权限，还对其他私有仓库（包括按客户划分的特定仓库）有读写权限。令牌据称是在找到 Baseten 的镜像仓库后，从 Docker 构建历史中发现的。社区评论中引述的披露时间线显示，7 月 13 日 23:10 报告了活跃的 basetenbot 令牌、公开的 Harbor 项目和仓库权限；7 月 14 日上午 Harbor 项目被设为私有但令牌仍有效；7 月 14 日 16:34 Baseten 安全团队的 Anton 确认其为严重问题，将 Harbor 项目设为私有并轮换了令牌，同时要求安全删除已拉取的镜像。这一披露来自安全厂商博客，带有推广性质，且评论对其合法性、伦理和营销方式提出质疑，因此具体影响仍需谨慎看待。

hackernews · bearsyankees · 9月15日 18:11 · [社区讨论](https://news.ycombinator.com/item?id=49716476)

**「背景知识」** GitHub 个人访问令牌（PAT）是替代密码的凭据，可按仓库授予读写、推送乃至管理员权限；一旦它被留在镜像构建历史等可被外部读取的位置，任何能拉取该镜像的人就可能获得同等权限。Harbor 是开源容器镜像仓库，项目可见性设置不当会让镜像的元数据与层内容对外可读，而 Docker 镜像的构建历史常残留构建阶段使用的令牌和环境变量。Strix 是一款开源的 AI 渗透测试工具，由发布本次披露的同一厂商推出，可让编码代理自动执行漏洞发现；GitOps 仓库通常存放驱动集群部署的声明式配置，因此对其的写权限接近生产环境控制权。

**「影响」** 对 Baseten 及其客户而言，该 basetenbot PAT 拥有主产品仓库、驱动集群的 GitOps 仓库和 Homebrew tap 的写入权限，并可按客户对特定私有仓库读写，一旦被滥用即构成 CI/CD 与供应链投毒的直接风险；该令牌据报长期存在于公开 Docker 仓库中（可追溯到 2023 年 3 月），因此暴露窗口取决于轮换前的时长。由于目前细节主要来自 Strix 的披露，Baseten 一方的完整公开说明尚不充分，实际波及范围仍有不确定性。

**「社区讨论」** 评论对事件态度不一：swyx 引述时间线并认为 Baseten 处理得当，aatd86 称这是 Strix 的好营销、对 Baseten 却很差，codemog 质疑这种行为是否合法，nrmitchi 对安全厂商把真实客户/供应商当作营销案例并点名“受害者”感到不适，wxw 则追问这类代理驱动安全利用还有多少。总体共识是 Baseten 的响应相对及时，但争议集中在 Strix 的披露方式、授权边界和推广动机上。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.strix.ai/blog/baseten-harbor-github-pat-takeover">We wanted to use Baseten for inference. We ended up with admin access to their GitHub - Strix</a></li>
<li><a href="https://github.com/usestrix/strix">GitHub - usestrix/strix: Open-source AI penetration testing tool to find and fix your app’s vulnerabilities.</a></li>
<li><a href="https://www.strix.ai/">Strix - AI Penetration Testing &amp; Autonomous Security</a></li>
<li><a href="https://elsolitario.org/en/2026/09/15/github-token-admin-baseten-harbor/">GitHub Token : How Strix Found Admin Access at Baseten</a></li>
<li><a href="https://www.strix.ai/blog/baseten-harbor-github-pat-takeover">We wanted to use Baseten for inference. We ended up with... - Strix</a></li>

</ul>
</details>

**标签**: `#security`, `#DevOps`, `#GitHub`, `#secrets management`, `#AI agents`

---

<a id="item-tech-news-5"></a>
### [Capsule：把 HTML 应用和数据打包为单个 SQLite 文件](https://withcapsule.app/) ⭐️ 7.0/10

开发者 bashtian 在 Hacker News 发布 Capsule：一个用 Rust 和 Tauri 2.0 构建的工具，可把 HTML 应用及其数据打包进单个 SQLite 文件（扩展名也为 Capsule）。HTML 与相关资源直接嵌入数据库；用户数据可用 localStorage 键值存储，或通过受 MongoDB 启发的 collections API 以文档形式保存在表中，PDF、图片等资产也可一并存入，并支持导出 CSV 或 JSON。Capsule 强调隐私与安全：文档默认没有文件系统访问权限，联网需要获得许可，权限模型仍在改进；文档还可使用本地或远程 AI 模型实现特定 AI 功能。由于多人分别编辑会产生不同副本，Capsule 为每条数据项加入唯一 UUID 和时间戳以便合并，并计划在 1.0 版本开放文件格式规范；作者表示新版本会提供迁移，避免数据丢失。该发布在 HN 获得 267 分和 114 条评论，讨论集中在与 File System Access API 的对比，以及同步、应用更新、数据与应用分离和分发开销等问题。

hackernews · bashtian · 9月15日 13:31 · [社区讨论](https://news.ycombinator.com/item?id=49712278)

**「背景」** Capsule 所处的方向通常被称为本地优先或单文件应用：HTML 页面本身易于创建，但持久化与分享用户数据过去常依赖服务器或浏览器内置存储。SQLite 是嵌入式数据库，常以单个数据库文件保存结构化数据；Tauri 2.0 则用于把 Web 前端封装为带原生能力的桌面应用，Capsule 将两者结合，让应用文件同时充当数据容器。

**「影响」** 对想把小型 HTML 工具直接以文件形式分享、又不想自建后端的开发者，Capsule 提供了一个可试用的本地优先打包方案。不过它仍是早期单开发者项目，同步、更新和数据与应用分离等缺口会限制其适用场景。

**「社区讨论」** HN 评论肯定其易分享小工具的想法，但提出多项实际限制：mg 指出 File System Access API 已允许网页读写本地文件，并提供桌面和移动端可用的文本编辑器示例；andix 希望增加跨设备同步、应用与数据分离及应用更新，nater5000 和 jawns 则质疑若最终仍需安装运行器或反复发送带状态的文件，不如直接分发桌面应用或托管在 Web 上。

**标签**: `#SQLite`, `#Tauri`, `#Rust`, `#web apps`, `#local-first`

---

<a id="item-tech-news-6"></a>
### [把 20 美元 4G 热点改造成可收发短信的设备](https://bkovac.github.io/modem-thing/) ⭐️ 7.0/10

一位开发者将售价约 20 美元的 4G 无线热点改造成可以收发短信的设备，并把改造过程发布在项目页面上。该作品属于嵌入式硬件 DIY 方向，涉及 4G LTE 模块与嵌入式 Linux，目标是让廉价热点承担类似「傻瓜手机」的短信与验证码查看功能。社区评论中，有人表示自己刚买了约 10 美元的 4G 上网棒，打算拆开查看内部结构，并指出部分基于 MSM8916 的上网棒虽然没有显示屏却仍运行 Android 界面。还有评论建议加装可容纳两节并联 18650 电池的电池仓以显著延长续航，并认为复用 Clicks 键盘是巧妙的设计，成品可视为一台体积不大的「赛博甲板」（cyberdeck）。讨论普遍把实用场景落在用低成本硬件替代手机处理短信与 OTP 验证码。

hackernews · bobili1234 · 9月15日 13:20 · [社区讨论](https://news.ycombinator.com/item?id=49712102)

**「背景」** 近年来市场上出现大量基于高通 MSM8916 芯片组的廉价 4G 热点与上网棒，它们通常内置 WiFi、蓝牙、电池和存储，整机价格可低至 4 至 20 美元，因而成为硬件爱好者拆解和改造的对象。这类设备原本只提供上网功能和网页管理界面，但社区已为其移植基于 postmarketOS 内核的 OpenStick 等第三方固件，使其能运行更通用的 Linux 环境，从而支持外接显示、键盘等扩展。本次改造正是把这种廉价热点与 Clicks 键盘、Sharp 记忆液晶屏组合起来，做成可以收发短信的便携设备。

**「影响」** 对于希望用廉价 4G 热点替代手机处理短信和 OTP 验证码的用户，这类改造提供了一条成本极低、可自行复现的路径，但其续航、稳定性与硬件兼容性仍取决于具体热点型号，尚需更多实际使用验证。

**「社区讨论」** 评论总体认可项目思路，讨论集中在硬件细节与用途：有人计划拆解自己约 10 美元的 4G 上网棒，有人建议并联两节 18650 电池来延长续航，也有用户表示平时就用热点代替手机上网，只是查看短信和 OTP 不便。另有评论设想在这类设备上运行 AI 代理系统，前提是 OpenStick 构建有足够的 RAM 和存储。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://blog.adafruit.com/2026/09/15/converting-a-20-4g-wireless-hotspot-into-a-texting-device/">Converting a $20 4G wireless hotspot into a texting device</a></li>
<li><a href="https://vuink.com/post/oxbinp-d-dtvguho-d-dvb/modem-thing">Converting a $20 4G wireless hotspot into a texting device</a></li>
<li><a href="https://dmitrybrant.com/openstick">How To: OpenStick - Dmitry Brant</a></li>
<li><a href="https://news.ycombinator.com/item?id=45250676">Talking of cheap and powerful devices one can also look at Chinese UZ801 4G LTE ...</a></li>

</ul>
</details>

**标签**: `#hardware-hacking`, `#4g-lte`, `#embedded-linux`, `#open-source`, `#diy-electronics`

---

<a id="item-tech-news-7"></a>
### [Schneier 发文：25 年大规模监控已经够了](https://www.schneier.com/blog/archives/2026/09/25-years-of-mass-surveillance-is-enough.html) ⭐️ 7.0/10

Bruce Schneier 发表文章《25 年的大规模监控已经够了》，主张持续四分之一世纪的大规模监控应当终结。该文属于政策评论与倡议，而非技术突破或工程分析，围绕隐私、国家权力与技术替代方案展开。文章在 Hacker News 上引发大量讨论，评论者从不同角度回应监控扩张及其后果。由于原文内容未提供，具体论证细节和所涉政策条款无法在此确认。

hackernews · iamnothere · 9月15日 11:26 · [社区讨论](https://news.ycombinator.com/item?id=49710883)

**「背景」** 2001 年 9·11 恐怖袭击后，美国政府逐步扩大大规模监控项目，并试图将这些监控机制及其获取的信息置于《第四修正案》的保护之外。Bruce Schneier 与 Cindy Cohn 合写的这篇评论文章最初发表于 Lawfare，回顾了这 25 年间的政策演变。其核心争议在于，监控措施与所获数据是否应受宪法搜查与扣押条款的约束，这构成了当前隐私与安全政策讨论的历史背景。

**「影响」** 这场讨论推动隐私倡导者和开发者更具体地主张自托管、易用且可广泛分发的替代服务，以及把监控网络限制在地方管辖范围内，但现有材料未显示这些主张已转化为政策或技术变更。

**「社区讨论」** 评论者普遍担忧监控与极权控制，有人引用《道德经》称限制会滋生其本欲防止的混乱，并提议开发可在家中自托管的易用服务以利用第一和第四修正案的保护，另有人建议将摄像头网络限制在地方管辖范围内。还有评论警告 NSPM-7 将使大规模监控更具压迫性，并认为监控不会停止，除非它成为国家安全问题——因为敌人也可能获取同样的监控能力并攻击高价值目标。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.schneier.com/blog/archives/2026/09/25-years-of-mass-surveillance-is-enough.html">25 Years of Mass Surveillance Is Enough - Schneier on Security</a></li>
<li><a href="https://noise.getoto.net/2026/09/15/25-years-of-mass-surveillance-is-enough/">25 Years of Mass Surveillance Is Enough | Noise</a></li>

</ul>
</details>

**标签**: `#mass surveillance`, `#privacy`, `#security policy`, `#civil liberties`, `#technology ethics`

---

<a id="item-tech-news-8"></a>
### [Simon Willison 发布 Gemini 3.8 Live 浏览器语音测试界面](https://simonwillison.net/2026/Sep/15/gemini-live/) ⭐️ 7.0/10

Google 发布了 Gemini 3.8 Live 和 3.8 Live Extended Thinking 两款语音到语音（speech-to-speech）模型，形态与 OpenAI 的 GPT-Live 模型类似。Simon Willison 同日发布了一个基于浏览器的 Gemini Live audio 工具，用于试用这两款新模型。该界面支持选择模型和语音预设、输入可选的系统提示词，并通过浏览器发起语音对话，还能在模型说话时打断它。实现不依赖任何库，连接 wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key=... WebSocket 端点，并使用 Web Audio API 的 AudioContext 完成采集与播放。页面提供转录文本的下载和清除，并提示发送文字消息会打断当前回复，转录可能包含播放前被中断的语音。

rss · Simon Willison · 9月15日 22:47

**「背景」** 语音到语音（speech-to-speech）模型让音频直接进出模型，不必先转写为文本再合成语音，因此能降低往返延迟并保留语调、停顿等非语言信息。OpenAI 于 2026 年 7 月推出 GPT-Live，把对话控制权交给语音模型本身，而更深的推理与工具调用异步进行；Google 在 2026 年 9 月 15 日发布的 Gemini 3.8 Live 与 3.8 Live Extended Thinking 属于同类形态，支持后台工具调用，其中 Extended Thinking 版本面向更复杂的任务，并宣称覆盖 97 种语言。这些模型可通过 Gemini API、Google AI Studio、Gemini Enterprise、Search Live 及 Gemini 应用等渠道试用。

**「影响」** 对开发者而言，这个零依赖浏览器界面可直接用于实际操作和评估 Gemini 3.8 Live 模型，无需先搭建客户端；其 WebSocket 加 Web Audio API 的实现也给出了语音双向交互的最小集成范例。不过来源未提供基准测试或延迟数据，实际性能仍需自行验证。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-8-live-gemini-3-8-live-extended-thinking/">Gemini 3.8 Live &amp; Gemini 3.8 Live Extended Thinking - The Keyword</a></li>
<li><a href="https://www.marktechpost.com/2026/09/15/google-releases-gemini-3-8-live-and-3-8-live-extended-thinking-for-production-grade-voice-agents/">Google Releases Gemini 3.8 Live and 3.8 Live Extended ...</a></li>
<li><a href="https://openai.com/index/continuous-voice-interaction-with-gpt-live/">How we built a realtime system for responsive voice AI in six months | OpenAI</a></li>

</ul>
</details>

**标签**: `#Gemini`, `#speech-to-speech`, `#voice AI`, `#Google models`, `#developer tooling`

---

<a id="item-tech-news-9"></a>
### [Linux 内核补丁提议为 blk-iocost 引入 BPF 成本模型](https://lwn.net/Articles/1093661/) ⭐️ 7.0/10

Tao Cui 提交的补丁系列（第三版 RFC）提议为 Linux 内核的 blk-iocost 块 I/O 控制器加入 BPF 支持，使 I/O 成本计算可由加载的自定义程序决定。该系列引入一种新的 struct\_ops 程序类型 iocost\_model\_ops，其中核心且唯一必需的操作是 calc\_cost\(\)，其参数包括请求标志 opf、请求字节数 nbytes、扇区位置 sector、发起请求的块控制组 blkcg，以及可能含 IOCOST\_COST\_F\_MERGE 标志的 model\_flags，返回值即为该请求被计入的成本；可选的 blkcg\_online\(\) 与 blkcg\_offline\(\) 在该控制器被加入或移出控制组时调用，供 BPF 程序做簿记。加载程序本身不会把新成本函数绑定到设备，需要向控制组目录中的 io.cost.model 文件写入结构中 16 字节的 name 来选用模型。该改动只覆盖成本计算部分，每几毫秒运行一次、负责重新分配带宽并调整设备 vtime 推进速率的规划阶段保持不变。补丁集附带一个示例程序，用 BPF map 跟踪最多四个独立 I/O 流，若请求在任一被跟踪流中看似顺序访问就按顺序请求计费，以改善含多个顺序 I/O 进程的控制组的表现。

rss · LWN.net · 9月15日 14:37

**「背景」** blk-iocost 最初在 2019 年以 io.weight 之名被介绍，2024 年又被重新讨论；它按控制组分配块设备带宽比例，为每个 I/O 操作估算其占用的设备时间作为成本，并通过设备与控制组各自的虚拟时钟（vtime）决定何时下发请求。现有成本模型把判定为顺序的请求赋予较低成本，把看似随机的请求赋以高达 112 倍的成本，而判断随机性的启发式对不同工作负载并不总是有效。struct\_ops 是 BPF 的一种机制，允许 BPF 程序替换内核中的一组函数指针，此前已被用于其他内核子系统。

**「影响」** 若该系列最终被合并，内核与存储开发者将能针对具体设备特性定制块 I/O 成本模型，而不必修改内核代码；但该工作仍处于第三版 RFC 阶段，接口自 9 月 8 日首版发布以来已大幅演进，合并前很可能继续调整。

**标签**: `#Linux kernel`, `#BPF`, `#block I/O`, `#I/O scheduling`, `#blk-iocost`

---

## 科技博客

<a id="item-tech-blog-1"></a>
### [LLM 的“记忆”其实由应用层重建](https://blog.bytebytego.com/p/do-llms-have-the-memory-of-a-goldfish) ⭐️ 6.0/10

rss · ByteByteGo · 9月15日 15:31

**「背景」** 在同一段对话中，LLM 能引用几条消息前说过的内容，但新开一个聊天就“忘光”了，仿佛只有金鱼般的记忆。文章要解释的是：既然模型本身不存储对话，这种“记得”究竟从何而来。

**「方案」** 作者把“记忆”拆成三层：训练权重只含一般知识，用户说“我常用 TypeScript”并不会改写权重；上下文窗口是当前响应的“工作台”，模型只能用放在台上的材料；持久记忆存放在模型之外的数据库或向量库，需要时再取回插入上下文。多数 API 是无状态的，多轮对话必须由应用重发历史；即便 API 提供会话 ID 的服务器端状态，也只是服务器在重建上下文，作者称之为“重建式记忆”。窗口是 token 预算：假设 100K 的窗口里系统指令 3,000、工具定义 8,000、历史 55,000、检索文档 20,000、当前问题 1,000，只剩 13,000 留给回答；窗口大也不保证召回，信息越多越容易被无关或矛盾内容干扰，即“context rot”。每轮约 1,000 token，第 10 次请求要处理约 10,000 token，十次累计约 55K 输入；提示缓存只是复用重复前缀的优化，不构成记忆。窗口写满时，应用会丢弃旧消息、滚动窗口或压缩成摘要，而摘要有损，反复摘要会像复印件的复印件一样扭曲原意。作者列举的扩展手段包括滑动窗口、对话摘要、结构化实体抽取（把偏好与已确认决策存成字段）、向量库语义检索（按嵌入找片段，可能召回无关或过时内容，需配合元数据）和长期用户画像；跨会话记忆的关键一步，仍是把检索到的内容放进新对话的上下文。

**「启示」** 所谓记忆是上下文重建、摘要、检索与持久存储共同搭建的系统，其质量至少同样取决于模型之外的架构。有读者据此认为，人类每轮对话都会内化进长期记忆，而 LLM 的等价物是逐轮微调、代价过高，因此当前技术难以实现真正的 AGI。

**标签**: `#LLM memory`, `#context windows`, `#retrieval-augmented generation`, `#prompt caching`, `#conversation state`

---

<a id="item-tech-blog-2"></a>
### [Groq 3 LPX 确定性执行与能效优化](https://developer.nvidia.com/blog/how-nvidia-groq-3-lpx-deterministic-execution-drives-power-efficient-high-interactivity-inference-on-nvidia-vera-rubin/) ⭐️ 4.0/10

rss · NVIDIA Inference Performance Blog · 9月15日 16:55

**「背景」** AI 工厂受功耗硬约束，性能功耗比而非原始吞吐成为衡量平台的关键。Vera Rubin 用工厂级 DSX MaxLPS 和机架级智能功率平滑管理电力，但高交互层级仍需 Groq 3 LPX 提供低延迟推理。

**「方案」** 文章核心是 Groq 3 LPX 的确定性执行：编译器在运行前为整个机架的 256 颗 LPU 生成逐时钟周期调度，明确数据何时移动到哪个计算单元、何时执行；MXM、VXM、SXM 等功能单元、片上 SRAM 和 LPU 直连，加上同步时钟，使计算、访存与通信周期可重复。编译器因此能预测每周期电流需求，并用 Preemptive Power 提前让供电网络调压，减少去耦电容的补偿缺口；Clock Period Synthesis 则拉长或缩短特定时钟周期，尤其拉长电流尖峰周期以降低 di/dt。作者称这使电压跌落减少&gt;60%，持续基线电压降高个位数百分比，并因功率与电压平方成正比（电压高 10%约多耗 21%功率），最终让同负载功耗降低低两位数百分比。NVIDIA 还称，Groq 3 LPX 与 Vera Rubin NVL72 组合在 2T+参数、长上下文和高交互场景下，每兆瓦吞吐可达上一代 GB200 NVL72 的 35 倍，计划 2026 年下半年推出。但这些数字均属厂商内部测试或估算，未提供方法、基准或独立验证，也未展开实现成本与局限。

**「启示」** 作者的论点是，确定性执行把不可预测的电流需求变成可提前调度的逐周期时间表，从而压缩电压保护带、把更多电力留给推理；不过其能效与吞吐优势目前仍是厂商主张，需独立验证。

**标签**: `#deterministic execution`, `#power efficiency`, `#voltage droop`, `#AI inference hardware`, `#NVIDIA Vera Rubin`

---

## 财经新闻

<a id="item-finance-news-1"></a>
### [中国 8 月零售增速低于预期，投资降幅加深](https://www.cnbc.com/2026/09/15/china-august-retail-sales-industrial-output-investment-exports-.html) ⭐️ 8.0/10

中国国家统计局数据显示，8 月社会消费品零售总额同比增长 0.4%，低于路透调查经济学家预期的 0.8%，也较 7 月的 0.6%放缓；1 至 8 月城镇固定资产投资（含房地产与基础设施投资）同比下降 7.2%，降幅比 1 至 7 月的 6.7%进一步扩大。

rss · CNBC Finance · 9月15日 09:46

**「背景」** 中国二季度经济增速降至 4.3%，为三年多来最弱，而政府全年增长目标为 4.5%至 5%；统计局称国内存在“供给强、需求弱”的供需失衡，呼吁加大宏观政策调整并提振内需，但北京迄今仍以渐进措施为主，未推出更强刺激。

**「影响」** 8 月新增人民币贷款仅 600 亿元（约 89.5 亿美元），远低于约 4000 亿元的预期，也少于去年同期的 5900 亿元，反映企业和家庭借贷意愿疲弱，可能使依赖信贷的小微企业和居民融资更为困难。

**标签**: `#China economy`, `#retail sales`, `#fixed-asset investment`, `#credit growth`, `#macro policy`

---