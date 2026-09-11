---
layout: default
title: "Horizon Summary: 2026-09-11 (ZH)"
date: 2026-09-11
lang: zh
---

> 从 43 条内容中筛选出 13 条重要资讯。

---

**科技新闻**
1. [Shopify 从 React Native 迁回 Swift 与 Kotlin](#item-tech-news-1) ⭐️ 8.0/10
2. [微软将 Rust 列为一级语言](#item-tech-news-2) ⭐️ 8.0/10
3. [Nix 包可通过浏览器内的 qemu-wasm 虚拟机直接启动](#item-tech-news-3) ⭐️ 8.0/10
4. [Calif Research 发布 WeWorm 零点击微信通话蠕虫演示](#item-tech-news-4) ⭐️ 8.0/10
5. [Forgejo 16.0.4 与 15.0.8 修复严重 RCE 漏洞](#item-tech-news-5) ⭐️ 8.0/10
6. [PostgreSQL 19 后期补丁质量引担忧，新增一个 beta](#item-tech-news-6) ⭐️ 8.0/10
7. [OpenAI 与未发表数学：研究者的信任争议](#item-tech-news-7) ⭐️ 7.0/10
8. [Julia 1.13 发布：加快包预编译并改进 REPL](#item-tech-news-8) ⭐️ 7.0/10
9. [DeepSeek V4.1 Flash 发布：552B 参数与 API 路由调整](#item-tech-news-9) ⭐️ 7.0/10
10. [HBM 短缺推高中国 AI 芯片价格](#item-tech-news-10) ⭐️ 7.0/10
11. [腾讯混元发布开源音频编辑模型 AuK 与 AuK-Flash](#item-tech-news-11) ⭐️ 7.0/10

**科技博客**
1. [BioIR 高通量蛋白质结构预测教程与基准](#item-tech-blog-1) ⭐️ 6.0/10
2. [Nemotron 3 Ultra NIM 全栈优化的 2.5 倍吞吐](#item-tech-blog-2) ⭐️ 4.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [Shopify 从 React Native 迁回 Swift 与 Kotlin](https://shopify.engineering/back-to-native) ⭐️ 8.0/10

Shopify 工程博客宣布，将其移动应用从 React Native 迁回原生 Swift 和 Kotlin。此举之所以受关注，是因为它来自一家大型生产级应用，直接触及跨平台共享代码与原生开发之间的长期权衡。由于本条未附原文正文，除迁移方向外，具体迁移范围、时间表、性能数据与版本信息无法从现有材料确认。该话题在 Hacker News 获得 704 分和 467 条评论，讨论集中在原生性能、共享代码维护成本以及 LLM 辅助迁移等议题。

hackernews · fnthawar2 · 9月10日 14:09 · [社区讨论](https://news.ycombinator.com/item?id=49643982)

**「背景」** React Native 是 Meta 推出的跨平台移动开发框架，其核心卖点是让 iOS 和 Android 共用一套 JavaScript 代码，开发者无需为同一功能分别用 Swift 和 Kotlin 各写一遍。Shopify 当年正是基于这一逻辑采用 React Native 的，其理由包括：不再重复构建同一功能、让开发者跨全栈而非困在单一平台、减少追逐功能对齐的时间以便更快交付。2026 年 9 月 10 日，Shopify 发布工程文章《Native is now the future of mobile at Shopify》，说明其移动应用正从 React Native 迁回原生 Swift 与 Kotlin。

**「对移动开发团队的影响」** 对采用 React Native 的移动团队而言，Shopify 以编码智能体大幅降低双端原生开发成本为由回迁 Swift 与 Kotlin，意味着“共享代码库必然更省成本”这一默认假设需要重新评估，其 iOS 工程师甚至可借助智能体驱动 Kotlin 迁移。但 Shopify 披露的验证仅是一名工程师一周的智能体辅助原型（接近但尚未达到生产可用），因此该结论能否推广到其他团队和更复杂应用仍待证实。

**「社区讨论」** 评论中对迁回原生或新项目直接采用原生总体偏向支持，一名 iOS 工程师称这验证了自己长期反对单纯追求共享代码库的立场；但关于 LLM 是否使这类迁移变得可行存在明显分歧。有人用 Codex 等工具在一夜之间完成约 15–20 个屏幕的小型应用迁移，也有人指出自己参与的中型 React Native 转 Swift/Kotlin 迁移主要发生在 2026 年 1 月前且没有 LLM 代码辅助，另有评论警告不能因 AI 而低估复杂度成本。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://shopify.engineering/back-to-native">Native is now the future of mobile at Shopify (2026) - Shopify</a></li>
<li><a href="https://dev.to/jamilxt/shopify-is-moving-its-mobile-apps-back-to-native-coding-agents-made-it-cheaper-to-build-twice-than-4bf9">Shopify Is Moving Its Mobile Apps Back to Native . - DEV Community</a></li>
<li><a href="https://shopify.engineering/back-to-native">Native is now the future of mobile at Shopify (2026) - Shopify</a></li>
<li><a href="https://dev.to/jamilxt/shopify-is-moving-its-mobile-apps-back-to-native-coding-agents-made-it-cheaper-to-build-twice-than-4bf9">Shopify Is Moving Its Mobile Apps Back to Native. Coding Agents Made It Cheaper to Build Twice Than to Share One Codebase. - DEV Community</a></li>
<li><a href="https://shopify.engineering/shop-app-migration">Migrating Shop app from React Native to native (2026) - Shopify</a></li>

</ul>
</details>

**标签**: `#React Native`, `#Swift`, `#Kotlin`, `#mobile development`, `#cross-platform`

---

<a id="item-tech-news-2"></a>
### [微软将 Rust 列为一级语言](https://rustfoundation.org/media/guest-post-rust-is-tier-1-language-at-microsoft/) ⭐️ 8.0/10

微软已将 Rust 列为一级（tier-1）语言，这一消息来自 Rust 基金会网站上的一篇客座文章。对于系统编程和软件工程而言，这被视为重要行业信号，可能影响 Rust 在微软产品与 MSVC 工具链中的采用，并强化内存安全优先级。不过，当前提供的内容没有给出微软官方支持范围、版本、时间表或具体产品，因此尚不能确认这一级别划分在实际开发流程中的约束与承诺。相关讨论还提到微软大规模将 C/C++ 代码迁移到 Rust 的目标，但这些属于社区转述与延伸，需以官方信息为准。

hackernews · mmastrac · 9月10日 13:39 · [社区讨论](https://news.ycombinator.com/item?id=49643546)

**「背景」** Rust 是一种通用编程语言，强调性能、类型安全、并发和内存安全。微软将 Rust 列为 Tier-1 语言，意味着它在微软内部获得与既有主流语言同等的支持级别；不过 C++ 在数十年积累后仍占主导，且微软的生产软件需要经过严格的安全与质量流程。

**「影响」** 获得 Tier-1 工程地位后，Microsoft 内部团队和 Windows 平台的 Rust 开发者将得到从本地开发到生产的受支持路径，包括安全工具链构建、生产力工具、质量流程、SDL 合规以及直连 MSVC 后端，从而能在 Windows 上以更原生的方式使用 Rust 进行系统编程，而不必维持并行的 LLVM 栈。

**「社区讨论」** 评论者普遍认为这是重要信号：有人提到微软设定了到 2030 年通过自动化工具将 10 亿行代码转换为 Rust 的目标（“1 名工程师、1 个月、100 万行代码”），以及 DARPA 资助的 6 支团队尝试自动把 C 代码转成 Rust；也有人强调 Rust 已是成熟、可与 C++/C\# 竞争的“更好 C/C++”选择。另有评论关注 MSVC 集成传闻，称这次变化的关键是改用 MSVC 后端而非 LLVM，并引用 Azure CTO Mark Russinovich 关于 70% CVE 属于内存安全问题的说法。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://en.wikipedia.org/wiki/Rust_%28programming_language%29">Rust (programming language ) - Wikipedia</a></li>
<li><a href="https://rustfoundation.org/media/guest-post-rust-is-tier-1-language-at-microsoft/">Guest Post : Rust Is Tier - 1 Language at Microsoft</a></li>
<li><a href="https://rustfoundation.org/media/guest-post-rust-is-tier-1-language-at-microsoft/">Guest Post: Rust Is Tier-1 Language at Microsoft</a></li>
<li><a href="https://mangodeveloper.com/articles/microsoft-makes-rust-a-tier-1-language-ships-custom-msvc-backend">Microsoft Makes Rust a Tier-1 Language, Ships Custom MSVC ...</a></li>

</ul>
</details>

**标签**: `#Rust`, `#Microsoft`, `#systems programming`, `#memory safety`, `#programming languages`

---

<a id="item-tech-news-3"></a>
### [Nix 包可通过浏览器内的 qemu-wasm 虚拟机直接启动](https://simonwillison.net/2026/Sep/10/trynix/) ⭐️ 8.0/10

Farid Zakaria 发布了 trynix.dev，他称其为自己在 Nix 工作上的“magnum opus”（代表作）。该站点基于 ktock 的 qemu-wasm，在浏览器中通过 WebAssembly 完整运行一台 x86\_64 Linux 虚拟机，无需任何服务器，并可载入过去 13 年间的任意 Nix 包。页面采用 URL 寻址，例如访问 https://trynix.dev/?pkg=python3%403.6.2 并点击“Load”，即可获得一个运行 2017 年 Python 3.6.2 的交互式 shell。Zakaria 还在此基础上构建了 trynix-preview：这是一个 GitHub Action，会在 pull request 上评论一条链接，让评审者直接在浏览器中启动该 PR 的构建并进行评审。Simon Willison 转述了这一进展。

rss · Simon Willison · 9月10日 23:44

**「背景」** Nix 是声明式包管理与构建系统，其包集合 nixpkgs 历年由 Hydra 等持续集成构建出的二进制产物保存在 Nix 二进制缓存中，因此可以按具体版本回溯取回某个包精确的 store 路径。QEMU-WASM 把 QEMU 模拟器编译为 WebAssembly，使 x86\_64 Linux 内核与虚拟机能够在浏览器标签页内运行，完全不需要服务器端支持。trynix 在此基础上结合 nixpkgs-multiverse 索引，将包及其依赖闭包放入内存中的 Nix store，而包本身通过普通 HTTP 从 Nix 二进制缓存下载。

**「影响」** 对 Nix 开发者而言，trynix-preview 这一 GitHub Action 会在拉取请求上自动评论一个链接，使审查者无需检出分支或自备服务器，即可在浏览器标签页中直接启动该 PR 的构建产物。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://trynix.dev/">trynix</a></li>
<li><a href="https://techaiwire.com/articles/trynix-nix-packages-in-browser-wasm/">TryNix runs any Nix package in a browser tab</a></li>
<li><a href="https://fzakaria.com/2026/09/04/any-nix-package-live-in-your-browser">Any Nix package, live in your browser | Farid Zakaria’s Blog</a></li>
<li><a href="https://github.com/marketplace/actions/trynix-preview">trynix preview · Actions · GitHub Marketplace · GitHub</a></li>
<li><a href="https://fzakaria.com/2026/09/09/review-a-pull-request-by-booting-it">Review a pull request by booting it | Farid Zakaria’s Blog</a></li>

</ul>
</details>

**标签**: `#nix`, `#webassembly`, `#virtualization`, `#developer-tools`, `#reproducible-builds`

---

<a id="item-tech-news-4"></a>
### [Calif Research 发布 WeWorm 零点击微信通话蠕虫演示](https://simonwillison.net/2026/Sep/10/calif-research/) ⭐️ 8.0/10

Calif Research 发布了名为 WeWorm 的演示，声称这是首个通过微信通话在 iOS 和 Android 上传播的零点击蠕虫。据其描述，受害者无需接听电话或对手机做任何操作；即使接听，也听不到声音，漏洞利用依然成功。该团队表示，他们借助 AI 在大约两天内找到了漏洞并写出首个远程代码执行（RCE）利用，随后又用一周时间构建出蠕虫。他们称，过去这种规模的蠕虫需要更大团队花费数月，而 AI 已能完成大部分工作，团队只负责目标判断与安全测试。目前这只是一段缺乏详细技术说明且未经独立验证的演示声明。

rss · Simon Willison · 9月10日 00:56

**「背景概念」** 零点击（zero-click）攻击指受害者完全不与设备交互即被攻陷；WeWorm 的传播载体是微信通话，受害者无需接听、甚至无需碰手机，若接听也听不到任何声音，利用仍会成功，且据称同时影响 iOS 与 Android。微信是腾讯运营的即时通讯应用，用户基数庞大，而蠕虫的关键特征是劫持受害者账号后自动向其联系人继续拨打电话，从而实现自我扩散。Calif Research 称，其团队借助 AI 约两天内定位漏洞并写出首个远程代码执行（RCE）利用程序，随后再花约一周构建蠕虫，并强调人类负责判断目标与安全测试；这类规模的工作过去往往需要更大团队数月完成，但上述说法目前主要来自研究方自述及安全媒体转述，尚待独立验证。

**「影响」** 若该演示获得独立验证，iOS 与 Android 上的微信用户将面临无需接听、无需任何操作即可被蠕虫感染并接管账号的零点击风险，潜在波及规模可达十亿级账户；但当前仅有厂商自行发布的演示，缺少技术细节与第三方复现，且“零点击”攻击仍以受害软件处理攻击者可控输入为前提。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://calif.io/research/weworm">WeWorm | Calif</a></li>
<li><a href="https://www.helpnetsecurity.com/2026/09/08/wechat-weworm-vulnerability-exploit-account-hijacking/">&quot;Zero-click&quot; WeChat worm could hijack accounts and spread via a single call - Help Net Security</a></li>
<li><a href="https://blog.calif.io/p/weworm">WeWorm</a></li>
<li><a href="https://www.techtimes.com/articles/327153/20260910/wechat-zero-click-worm-built-ai-days-voip-bug-put-billion-accounts-risk.htm">WeChat Zero - Click Worm Built by AI in Days: VoIP Bug Put Billion...</a></li>
<li><a href="https://www.1950.ai/post/wechat-zero-click-worm-how-ai-turned-a-voip-vulnerability-into-a-self-spreading-account-hijacking-t">WeChat Zero - Click Worm : How AI Turned a VoIP Vulnerability Into...</a></li>

</ul>
</details>

**标签**: `#AI security`, `#zero-click exploit`, `#WeChat`, `#remote code execution`, `#AI-assisted exploitation`

---

<a id="item-tech-news-5"></a>
### [Forgejo 16.0.4 与 15.0.8 修复严重 RCE 漏洞](https://lwn.net/Articles/1093671/) ⭐️ 8.0/10

Forgejo 软件托管项目发布了 16.0.4 和 15.0.8 两个版本，修复了两个安全漏洞，其中一个是可导致远程代码执行（RCE）的严重缺陷。该问题出在从模板仓库生成新仓库的流程中：Forgejo 会克隆模板仓库、删除其 .git 目录、对 .forgejo/template 中列出的文件执行变量模板展开，然后初始化一个新的 git 仓库。恶意模板仓库可借助变量模板展开重新创建一个 .git 目录，git 在初始化新仓库时会接收并采用该目录，从而使攻击者能够读取 Forgejo 主机上的任意数据，并以 RCE 方式在主机上执行任意进程。修复措施是在变量展开完成后、初始化 git 仓库之前，删除目录中任何已存在的 .git 目录。项目建议用户尽快升级到最新版本。

rss · LWN.net · 9月10日 20:05

**「背景」** Forgejo 是一个自托管、轻量级的软件协作平台（software forge），用于托管 Git 仓库与项目协作，并由 Codeberg e.V. 非营利组织框架下的社区维护。它最初源自 Gitea 项目，因与 Gitea Ltd. 的分歧而独立发展。模板仓库是 Forgejo 的一项功能，允许用户基于预置文件和变量生成新仓库；本次漏洞正发生在生成新仓库时对模板内容及 \`.git\` 目录的处理流程中。

**「影响」** 运行受影响版本（16.0.4 与 15.0.8 之前的版本）的 Forgejo 实例，任何能创建或使用恶意模板仓库的用户都可能在服务器上读取任意数据并执行任意进程，因此管理员应尽快升级。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://forgejo.org/">Forgejo – Beyond coding. We forge .</a></li>
<li><a href="https://awesome.ecosyste.ms/projects/codeberg.org/forgejo/forgejo">https://codeberg.org/ forgejo / forgejo | Ecosyste.ms: Awesome</a></li>
<li><a href="https://lionel-peramo.com/posts/forgejo-git-tool/">Forgejo : Discover 6 keys to master this Git platform</a></li>
<li><a href="https://noise.getoto.net/2026/09/10/forgejo-16-0-4-and-15-0-8-address-critical-security-vulnerability/">Forgejo 16.0.4 and 15.0.8 address critical security vulnerability | Noise</a></li>
<li><a href="https://lwn.net/Articles/1093671/">Forgejo 16.0.4 and 15.0.8 address critical security vulnerability [LWN.net]</a></li>

</ul>
</details>

**标签**: `#Forgejo`, `#security vulnerability`, `#remote code execution`, `#open source`, `#Git`

---

<a id="item-tech-news-6"></a>
### [PostgreSQL 19 后期补丁质量引担忧，新增一个 beta](https://lwn.net/Articles/1092003/) ⭐️ 8.0/10

PostgreSQL 19 原定于 2026 年 9 月发布，但在 4 月 8 日进入功能冻结后，多项后期补丁暴露出异常多的缺陷，引发开发者对发布质量的担忧。8 月 25 日，贡献者 Robert Haas 发出主题为“scary patch contest”的邮件，称他让 Claude 根据冻结后修复缺陷的数量和类型评估哪些 v19 补丁最“吓人”。被点名的包括：Amit Langote 与 Junwang Zhao 的外键快速路径补丁，冻结后约需 16 次修复，涉及跨类型、域、列顺序、可空键、非 btree 索引等五类外键约束错误，并重新设计了事务模型，其中批处理部分已从 19 移除但保留在 20 开发分支；Antonín Houska 的 REPACK 与 REPACK CONCURRENTLY 补丁累计 28 次修复，含数据丢失和两处安全相关 ACL 修复；以及 Daniel Gustafsson 与 Magnus Hagander 的在线启用或禁用数据校验和补丁，约 25 次实质性修复，包括误报校验和失败。目前至少一个补丁已被回退，多个补丁仍在密集修订，并额外增加了一个 beta 版用于测试。

rss · LWN.net · 9月10日 17:29

**「背景」** PostgreSQL 每年发布一个大版本，开发周期超过一年：补丁先在 CommitFest 接受评审，随后进入功能冻结，再经过若干 beta 与候选版本，最终发布正式版（GA）。冻结后的稳定化阶段通常以缺陷修复为主，而本次争议的核心正是若干在冻结后仍需反复修正的功能是否已足够可靠。

**「影响」** 对于计划升级到 PostgreSQL 19 的用户和运维团队，这意味着 REPACK、在线数据校验和开关以及外键批处理等功能可能被回退或推迟，正式发布前也将多出一个 beta 测试窗口。

**标签**: `#PostgreSQL`, `#database`, `#open source`, `#release engineering`, `#software quality`

---

<a id="item-tech-news-7"></a>
### [OpenAI 与未发表数学：研究者的信任争议](https://mathstodon.xyz/@andreasthom/117240535270608201) ⭐️ 7.0/10

一个 Hacker News 讨论帖汇集了多位研究者与开发者的担忧：在研究人员把未发表的数学工作交给 OpenAI 模型协作之后，OpenAI 是否值得信任，涉及署名、数据使用与研究伦理。质疑方把 OpenAI 比作人类合作者，认为若一位人类研究者利用合作中获得的思路发表成果却不予署名，会被视为严重不道德。也有评论者主张两件事可以同时成立：聊天记录可能进入预训练并提升模型的潜在表示；而在可验证数学任务上做强化学习并投入大规模算力，模型也可能自行发现与具体聊天内容关系不大的解题技巧。讨论中提及 OpenAI 曾为至少 10 万名研究者提供免费访问，以及有说法称其内部模型正以异常快的速度解决开放问题；还有人质疑 OpenAI 在得知某重要数学证明可能已存在于训练数据后，仍从训练中的模型生成 3000 亿输出 token。由于原帖只是链接聚合、没有一手技术说明，上述指控与解释均未获得独立证实。

hackernews · pred\_ · 9月10日 06:49 · [社区讨论](https://news.ycombinator.com/item?id=49639408)

**「背景」** 这场争论的背景是 OpenAI 宣称在纳维-斯托克斯方程相关问题上取得突破，而该问题由克莱数学研究所于 2000 年列为七个千禧年难题之一，据《卫报》报道其 GPT-6 Astra 用约 17 小时验证了该解。数学家 Tristan Buckmaster 在 9 月 7 日发布的四页声明中称，他此前在与 OpenAI 通话时询问过该模型“是否被训练于、或能够访问我们在 Codex 中的会话”；据报道他与 Alpöge 在研究中确实使用过包括 Claude 和 Codex 在内的多个 AI 模型，而 OpenAI 方面的 Sébastien Bubeck 则提出可以让 Buckmaster 先发表结果。由此引出的核心信任问题是：研究人员能否安全地把未发表成果交给前沿实验室的工具，以及大型语言模型究竟只能调用训练数据中的既有想法，还是能把“思考过程”迁移到全新问题上——这一分歧目前仍无定论。

**「影响」** 对考虑与 OpenAI 共享未发表数学成果的研究者而言，这场讨论凸显出署名与数据使用规则不透明所带来的实际风险，可能促使他们在合作前要求更明确的归属与保密条款。

**「社区讨论」** 评论区并未形成共识：一方认为不署名地使用合作中获得的思路在伦理上不可接受，另一方强调预训练记忆与强化学习自发发现的技巧是两回事、需要分别评估，也有人用“平行构造”来形容 OpenAI 的一系列举动看起来可疑。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://news.ycombinator.com/item?id=49639408">More questions about whether researchers can trust OpenAI with ...</a></li>
<li><a href="https://www.progressiverobot.com/2026/09/10/openai-math-mathematicians-want-proof-didnt-use-their-work/">OpenAI Math Risk: Mathematicians Want Definitive Proof</a></li>
<li><a href="https://www.banandre.com/blog/openai-navier-stokes-millennium-problem-ai-proof-controversy">OpenAI Cracked a 90-Year-Old Math Problem in 88 Hours. - Banandre</a></li>
<li><a href="https://www.nytimes.com/2026/09/10/science/tristan-buckmaster-openai-math-navier-stokes.html">The Mathematician Crushed Between OpenAI and Anthropic Over...</a></li>
<li><a href="https://www.businessinsider.com/openai-navier-stokes-math-breakthrough-drama-2026-9">OpenAI &#x27;s Big Math Breakthrough Claim Sparks... - Business Insider</a></li>
<li><a href="https://www.theguardian.com/science/2026/sep/08/openai-claims-to-have-solved-maths-problem-that-stumped-humans-for-decades">OpenAI claims to have solved maths problem that... | The Guardian</a></li>

</ul>
</details>

**标签**: `#OpenAI`, `#research ethics`, `#AI math`, `#attribution`, `#research trust`

---

<a id="item-tech-news-8"></a>
### [Julia 1.13 发布：加快包预编译并改进 REPL](https://lwn.net/Articles/1093567/) ⭐️ 7.0/10

Julia 编程语言 1.13 版已发布，官方公布的亮点包括更快的包预编译、REPL 的改进，以及为版本管理器 Juliaup 提供的图形界面。完整变更清单收录在该版本的发布说明（NEWS.md）中。LWN 曾于 2025 年 11 月报道 Julia 1.12。目前公布的摘要较为简短，具体性能提升幅度、REPL 各项改动细节及 Juliaup 图形界面的功能范围均未在本条目中给出，需查阅官方发布说明与亮点博客确认。

rss · LWN.net · 9月10日 13:23

**「背景」** Julia 是一门面向科学计算与数值分析的开源动态编程语言，其 1.12 版本于 2025 年 11 月发布。包预编译指在安装或首次加载包时提前完成 Julia 代码的编译并缓存产物，其耗时长期是影响用户体验的环节。Juliaup 是 Julia 的安装器兼版本管理器，可安装指定 Julia 版本、在新版本发布时提醒用户，并提供发布渠道（channel）抽象；它最早以 Windows 应用商店分发的方式出现，主要用于管理同一系统上的多个 Julia 版本。

**「影响」** 对 Julia 用户和依赖其工具链的开发者而言，1.13 的包预编译提速可直接缩短安装与加载包的等待时间，从而加快开发迭代；Juliaup 新增图形界面则使不习惯命令行的用户也能管理多个 Julia 版本。具体提速幅度与兼容性影响尚待官方发布说明核实。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://julialang.org/blog/2026/09/julia-1.13-highlights/index.html">Julia 1.13 Highlights</a></li>
<li><a href="https://github.com/JuliaLang/juliaup">GitHub - JuliaLang/ juliaup : Julia installer and version manager</a></li>
<li><a href="https://discourse.julialang.org/t/ann-juliaup-preview-julia-version-manager-and-windows-store-installer/61920">[ANN] Juliaup Preview - Julia version manager and Windows Store...</a></li>

</ul>
</details>

**标签**: `#Julia`, `#Programming Languages`, `#Open Source`, `#Release`, `#REPL`

---

<a id="item-tech-news-9"></a>
### [DeepSeek V4.1 Flash 发布：552B 参数与 API 路由调整](https://mp.weixin.qq.com/s/qg0NU3NNUbp1co2PdkAPAg) ⭐️ 7.0/10

DeepSeek 发布 V4.1 Flash，称其为全新模型结构系列中最小尺寸的模型，采用 552B 参数的 Causal-Encoder-Decoder 结构，输入与输出激活参数分别为 8B 和 16B，并原生支持多模态视觉理解。该模型已上线 DeepSeek API，模型名为 deepseek-flash。新价格于 2026 年 9 月 10 日 12:00 生效；2026 年 9 月 14 日 12:00 后，deepseek-v4-pro 请求将路由至 V4.1 Flash，并按 V4.1 Flash 的价格计费。所给信息来自聚合式 Telegram/微信帖子，包含推广措辞，且没有提供官方一手来源确认，因此上述发布与计费安排仍需以 DeepSeek 官方公告为准。

telegram · zaihuapd · 9月10日 05:54

**「背景」** DeepSeek 此前已发布 V4 系列模型（如 V4 Pro），据外部报道其总参数约 1.6T、推理时激活参数约 49B，属于混合专家（MoE）架构：模型虽拥有庞大规模参数，但每次推理只激活其中一小部分，以此控制算力与成本。V4.1 Flash 延续这一思路，官方称其采用新的 Causal Encoder–Decoder 架构，总参数 552B，输入侧仅激活 8B、输出侧激活 16B，从而在规模缩小的同时降低成本。官方资料还显示，该模型原生处理图像与文本并自回归生成文本，支持的上下文长度最高达 100 万 token；这也解释了为何此前使用 deepseek-v4-pro 的请求会被统一路由到这一更小、更便宜的模型。

**「影响」** 自 2026 年 9 月 14 日 12:00（北京时间）起，调用 deepseek-v4-pro 的请求将被自动路由至 V4.1 Flash 并按 Flash 价格计费，直至未来 V4.1 Pro 发布，这意味着既有 Pro 集成的开发者无需改动代码就会切换到另一模型，同时按更低价格结算。不过据第三方报道，该模型的基准测试数据尚未公布，实际能力差异仍需验证。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash">deepseek-ai/DeepSeek-V4.1-Flash · Hugging Face</a></li>
<li><a href="https://www.progressiverobot.com/2026/09/10/deepseek-v4-1-flash-552b-moe-model-hugging-face/">DeepSeek V4.1 Flash: Powerful 552B MoE at a Surprising Price</a></li>
<li><a href="https://www.deepseek.com/en/news/deepseek-v4-1-flash/">DeepSeek | Introducing DeepSeek-V4.1-Flash: smarter, faster, more efficient.</a></li>
<li><a href="https://api-docs.deepseek.com/quick_start/pricing/">Models &amp; Pricing | DeepSeek API Docs</a></li>
<li><a href="https://www.digitalapplied.com/blog/deepseek-v4-1-flash-pro-routing-prices-early-tests">DeepSeek V4.1 Flash: Pro Routing, Prices and Early Tests</a></li>
<li><a href="https://www.intelligentliving.co/deepseek-flash-release-pricing/">DeepSeek V4.1 Flash: Release Date, Pricing, and Pro Routing Explained</a></li>

</ul>
</details>

**标签**: `#DeepSeek`, `#large language models`, `#model release`, `#multimodal`, `#API pricing`

---

<a id="item-tech-news-10"></a>
### [HBM 短缺推高中国 AI 芯片价格](https://www.reuters.com/world/asia-pacific/chinas-ai-chipmakers-raise-prices-high-bandwidth-memory-shortage-bites-2026-09-10/) ⭐️ 7.0/10

全球高带宽存储器（HBM）供应紧张正持续冲击中国 AI 芯片产业，华为、寒武纪等厂商已开始上调产品价格。报道称，华为升腾 950DT 芯片报价较两个月前上涨约 20%—50%，部分老款芯片价格上涨约 30%；寒武纪新一代思元 690 价格预计上涨约 20%—30%。HBM 主要由 SK 海力士、三星和美光供应，美国出口限制进一步加剧了中国市场的供应压力。随着国内 AI 算力需求增长，HBM 短缺正成为制约国产 AI 芯片扩张的重要瓶颈。

telegram · zaihuapd · 9月10日 09:29

**「背景」** 高带宽存储器（HBM）通过堆叠 DRAM 裸片并与 GPU、AI 加速器封装在一起，提供远超普通内存的带宽，是训练和运行大模型的关键部件。该市场长期由 SK 海力士、三星和美光三家供应，产能扩张周期长、集中度高。美国的出口限制进一步压缩了中国厂商获取先进 HBM 的渠道，使这一环节的紧缺直接传导为国产 AI 芯片的成本与报价上涨，华为升腾 950 DT 等产品报价已升至 25 万元人民币以上。

**「影响」** 对采购国产 AI 算力的中国云厂商与企业用户而言，芯片采购成本短期内将明显上升，国产算力扩张节奏可能受制于 HBM 供给而非芯片设计或制造能力。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://moderndiplomacy.eu/2026/09/10/china-ai-chips-hbm-shortage-prices/">China ’s AI Chipmakers Raise Prices as HBM Shortage Squeezes...</a></li>
<li><a href="https://www.msn.com/en-us/technology/hardware-and-devices/china-ai-chipmakers-raise-prices-amid-hbm-shortage/vi-AA2bXQwL">China AI chipmakers raise prices amid HBM shortage</a></li>
<li><a href="https://techgolly.com/news/chinese-ai-chipmakers-hike-processor-prices-as-high-bandwidth-memory-shortage-bites">Chinese AI Chipmakers Hike Processor Prices as... - TechGolly</a></li>

</ul>
</details>

**标签**: `#AI chips`, `#HBM`, `#semiconductor supply chain`, `#China`, `#export controls`

---

<a id="item-tech-news-11"></a>
### [腾讯混元发布开源音频编辑模型 AuK 与 AuK-Flash](https://x.com/TencentHunyuan/status/2097996926876795197) ⭐️ 7.0/10

腾讯混元宣布正式发布开源音频编辑模型 AuK。该模型可通过自然语言指令与参考音频统一完成语音生成与编辑，支持零样本文本转语音、音色/风格/情绪编辑、去口音及多人语音分离等功能。同时发布的 AuK-Flash 采用 4 步推理，在匹配条件下速度约提升 4.5 倍；代码、模型权重和演示均已上线。不过官方此次仅发布简短说明，未提供论文、基准测试或独立验证结果。

telegram · zaihuapd · 9月10日 11:56

**「背景」** 语音生成（如零样本文本转语音）与语音编辑以往通常由不同模型分别处理，AuK 则试图用同一套自然语言指令接口统一这些任务。据第三方解读，AuK 是一个 1.5B 参数的语音基础模型，训练数据包含 30.3 亿条指令—音频实例和 195 万小时监督数据，覆盖 TTS、内容编辑、增强分离与副语言编辑；其训练方式枚举同一说话人的成对语句且不提供提示音频的转写，从而迫使模型解耦说话人特征与语句级信息，这也是它能用几秒参考音频克隆音色的基础。AuK-Flash 是配套的蒸馏版本，采用 4 步推理，权重以 MIT 协议发布。

**「影响」** 对音频与语音开发者而言，AuK 以开源形式提供统一的生成与编辑能力，并附带权重与演示，可能降低构建语音编辑应用的门槛，但其实际性能因缺乏基准测试与独立验证仍需自行评估。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.aimodeling.com/news/slug/tencent-hunyuan-auk-speech-editing">腾讯混元开源AuK:1.5B语音模型统一生成与编辑,4步推理快4.5倍</a></li>
<li><a href="https://www.cnblogs.com/foxcharon/p/22918448">AuK：腾讯混元开源的语音生成与编辑统一基础模型深度解读 - fox_charo...</a></li>
<li><a href="https://ai-bot.cn/auk/">AuK - 腾讯混元开源的语音生成与编辑基础模型 | AI工具集</a></li>

</ul>
</details>

**标签**: `#audio editing`, `#text-to-speech`, `#open source`, `#Tencent Hunyuan`, `#speech synthesis`

---

## 科技博客

<a id="item-tech-blog-1"></a>
### [BioIR 高通量蛋白质结构预测教程与基准](https://developer.nvidia.com/blog/high-throughput-structure-prediction-with-bionemo-inference-runtime/) ⭐️ 6.0/10

rss · NVIDIA CUDA Technical Blog · 9月10日 15:00

**「背景」** 蛋白质结构预测已在蛋白质组规模运行，真正的挑战是如何高效吞吐整个工作列表。NVIDIA BioNeMo Inference Runtime（BioIR）面向 NVIDIA GPU 加速受支持的生物分子结构预测模型，同时保留 PyTorch 工作流。

**「方案」** 作者以 Boltz-2 为例演示端到端处理器：输入需带 A3M MSA，可选模板，流程覆盖解析、分词、特征生成、GPU 推理到 PDB/mmCIF 写出；可先用串行执行器验证单条记录，再用 Ray 在每个可见 GPU 上放置完整模型副本并行处理独立输入。Ray 流水线按 Parser→Tokenizer→Feature generator→Folding engine→Writer 五阶段配置 compute、num\_cpus、memory 和 num\_gpus，容量规则为 engine\_stage.compute × num\_gpus ≤ 可见 GPU 数，且该教程只覆盖单节点。作者把优化分为内核选择、optimize\(\) CUDA Graph 模块优化和 Ray 流水线扩展：前两者减少单副本模型前向时间，Ray 用 CPU/GPU 重叠和多副本提高吞吐，但不会把单次前向拆到多卡。受控基准在 8×H100 上跑 1,000 个人类二聚体目标（总长低于 2,800 残基，3 次 recycle、200 采样步、5 个 diffusion 样本），作者报告 BioIR 的 Boltz-2 达 58.5K 残基/GPU 小时，公开实现为 20.2K，约 2.90×，后者有 29 个目标 OOM。作者还外推到百万目标，估计折叠阶段 11 vs 35 MWh（TDP）或 21 vs 64 MWh（整机最大功率），但强调这是估算，排除 MSA 生成、预处理、存储、重试和工程开销。BioIR 也曾用于 AFDB 扩展，覆盖 4,777 个蛋白质组、约 3,100 万候选复合物，其中 181 万为高置信预测。

**「启示」** 文章的核心论点是：BioIR 同时提供单副本模型前向加速和流水线级吞吐扩展，但二者必须分开度量；受控折叠基准能证明其效率优势，端到端部署收益仍需按真实工作列表和工程开销单独验证。

**标签**: `#BioNeMo Inference Runtime`, `#protein structure prediction`, `#Ray`, `#GPU throughput`, `#benchmarking`

---

<a id="item-tech-blog-2"></a>
### [Nemotron 3 Ultra NIM 全栈优化的 2.5 倍吞吐](https://developer.nvidia.com/blog/how-full-stack-nim-optimizations-deliver-2-5x-more-users-on-nemotron-3-ultra/) ⭐️ 4.0/10

rss · NVIDIA Inference Performance Blog · 9月10日 16:55

**「背景」** 部署大语言模型只是第一步，生产团队还要在现有 GPU 上尽可能多地服务并发用户，同时保持交互延迟；对代理式 AI 而言，长提示、跨步骤复用上下文和流式长响应让这一权衡更尖锐。

**「方案」** NVIDIA NIM 把模型与 GPU 感知的推理优化封装为可部署微服务，让团队从验证过的配置出发，同时保留用自有流量做基准测试的空间；NIM Certified 还提供推理栈更新、CVE 处理、硬件验证和商业支持。其 Nemotron 3 Ultra 案例在 4 张 B200 上，以 64K/400/76% KV 复用/50 TPS 每用户（20 ms ITL）的代理式负载为定义，对比未启用 NIM 的基线 718 tok/s 与启用 NIM 2.0.12 优化栈的 1,997 tok/s，作者称达到约 2.5 倍吞吐。作者强调增益来自相互作用的配置组合，而非可简单相加的开关：包括自动调优的 MoE/Mamba 内核与精度、张量并行及专家感知执行、前缀缓存/部分前缀匹配和 Mamba 状态缓存、调度/批处理/显存分配调优，以及 MTP 推测解码。作者建议把公开曲线当作起点，用 Mooncake JSONL 轨迹或受控请求、AIPerf 和固定镜像版本回放代表流量，并扫描并发以选择满足 SLO 的 Pareto 点。

**「启示」** 作者的结论是，全栈、模型与硬件协同的推理工程能在给定延迟目标下显著提升并发服务能力，因此经过验证的 NIM 配置可作为代理式负载的生产起点；但适配度最终仍要用自己的流量与 SLO 来验证。

**标签**: `#NVIDIA NIM`, `#LLM inference serving`, `#benchmarking`, `#speculative decoding`, `#agentic AI`

---