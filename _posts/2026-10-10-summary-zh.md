---
layout: default
title: "Horizon Summary: 2026-10-10 (ZH)"
date: 2026-10-10
lang: zh
---

> 从 47 条内容中筛选出 13 条重要资讯。

---

**科技新闻**
1. [Cloudflare 收购 Deno，运行时一年后停止官方开发](#item-tech-news-1) ⭐️ 9.0/10
2. [Python 3.15 发布：新增 sentinel 与 frozendict 类型](#item-tech-news-2) ⭐️ 9.0/10
3. [Anthropic 推出 OSS Scanner 开源漏洞扫描服务](#item-tech-news-3) ⭐️ 8.0/10
4. [Carrier-Explode：解码 iPhone、Pixel 和 Galaxy 运营商设置](#item-tech-news-4) ⭐️ 7.0/10
5. [Windows 与 Mac 键盘差异分析引发切换成本讨论](#item-tech-news-5) ⭐️ 7.0/10
6. [微软开源 MXC：统一封装多平台沙箱执行](#item-tech-news-6) ⭐️ 7.0/10
7. [OpenAI 解雇三名安全研究员 当事人否认指控](#item-tech-news-7) ⭐️ 7.0/10
8. [Matthew Green：AI 带来的密码学意外或快于标准更替](#item-tech-news-8) ⭐️ 7.0/10
9. [GCC 加入内核前向边 CFI 检查补丁](#item-tech-news-9) ⭐️ 7.0/10
10. [systemd 2026 状态：季度发布落地，AI 提交令审查承压](#item-tech-news-10) ⭐️ 7.0/10
11. [Let&\#x27;s Encrypt 将于 2027 年 2 月启用 64 天期证书](#item-tech-news-11) ⭐️ 7.0/10
12. [Telegram Desktop 7.2.9 以下版本曝一键窃取文件漏洞](#item-tech-news-12) ⭐️ 7.0/10

**科技博客**
1. [软件工程的“半人马时代”或将持续数十年](#item-tech-blog-1) ⭐️ 5.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [Cloudflare 收购 Deno，运行时一年后停止官方开发](https://deno.com/blog/cloudflare) ⭐️ 9.0/10

Cloudflare 已收购 Deno。根据讨论中引述的公告，Deno 运行时还将获得一年支持，期间每月发布缺陷修复和安全更新；一年后 Deno 团队将结束对该运行时的开发。公告称 Deno 仍将保持开源，并欢迎其他人继续开发，因此除非有外部接手，Deno 将不再获得官方支持。

hackernews · ilreb · 10月9日 13:03 · [社区讨论](https://news.ycombinator.com/item?id=50019911)

**「背景」** Deno 团队在今年 8 月发布了 celld 的首个版本，这是他们对 Cloudflare Workers 的 Durable Objects 模式的开源实现；Deno 官方把「Deno → Deno Deploy → celld」这条演进路径视为此次加入 Cloudflare 的技术铺垫。Cloudflare 方面表示，Deno 团队将与 Workers 和 Durable Objects 团队合并工作，目标是简化 Workers 与 Durable Objects 的自托管，让开发者能在 Cloudflare 网络或自有基础设施上使用同一套编程原语。

**「影响」** 对使用 Deno 运行时的开发者和团队而言，现在有一年的官方维护窗口来规划迁移或接手维护；一年后若无人继续，生产环境将不再有新的缺陷修复和安全更新。由于 Deno 仍将开源，社区接管或分叉在许可上可行，但发布节奏、安全响应和维护责任将转由接手方承担。

**「社区讨论」** 评论者对 Deno 的结局普遍感到惋惜，并争论其衰落原因：一些人认为转向 npm 兼容性使 Deno 从简洁变得臃肿，另一些人批评项目未采用付费或捐赠模式而依赖风投。也有用户希望 Cloudflare 的 workerd 能采纳 Deno 的安全机制。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://deno.com/blog/cloudflare">Deno is joining Cloudflare | Deno</a></li>
<li><a href="https://blog.cloudflare.com/deno-joins-cloudflare/">Deno is joining Cloudflare | Cloudflare Blog</a></li>
<li><a href="https://simonwillison.net/2026/Oct/9/deno-is-joining-cloudflare/">Deno is joining Cloudflare - simonwillison.net</a></li>

</ul>
</details>

**标签**: `#Deno`, `#Cloudflare`, `#JavaScript runtime`, `#open source sustainability`, `#acquisition`

---

<a id="item-tech-news-2"></a>
### [Python 3.15 发布：新增 sentinel 与 frozendict 类型](https://lwn.net/Articles/1099602/) ⭐️ 9.0/10

Python 3.15 已正式发布，用户可从 python.org 的发布页面获取该版本。此次更新新增了内置的 sentinel 与 frozendict 类型，默认使用 UTF-8 编码，并引入包启动配置文件（site start files）。同时，实验性 JIT 编译器也得到改进，但该功能仍处于实验阶段，详细的完整变更列表见“What&\#x27;s new in Python 3.15”与官方 changelog。

rss · LWN.net · 10月9日 17:15

**「背景」** Horizon 9 月 2 日的日报曾报道 Python 3.15.0 RC2 发布，那是 3.15 的最后一个候选版，正式版原计划于 10 月推出；发布团队当时要求第三方项目尽快针对 3.15 测试并发布 PyPI wheel，并说明基于候选版构建的二进制 wheel 与后续 3.15 版本兼容。同一期日报还报道，Python 指导委员会已暂停 CPython 主分支上的 JIT 新开发，等待 PEP 836 等提案获得接受，并设定六个月期限，否则 JIT 代码将被移出主分支，因此 3.15 中的 JIT 仍是实验特性，其在 3.16（2027 年）默认启用的目标存在不确定性。

**「影响」** 对现有代码最直接的影响来自默认编码变更：依赖 locale 默认编码的脚本可能需要显式指定 encoding 才能保持原有行为。性能方面，改进后的 JIT 编译器仍属实验性且默认关闭，需手动启用才会对热点代码编译为机器码（tool-2-3）；本次 3.15.0 还包含来自 1,012 名贡献者的 5,643 次提交，并新增专用性能分析包（tool-2-2）。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://lwn.net/Articles/1090385/">2026-09-02 — Python 指导委员会暂停 CPython JIT 新开发，等待 PEP 获接受</a></li>
<li><a href="https://simonwillison.net/2026/Sep/1/python-315-rc-2/">2026-09-02 — Python 3.15.0 RC2 发布：生态需准备 10 月正式版</a></li>
<li><a href="https://news.lavx.hu/article/python-3-15-0-releases-with-jit-upgrade-utf-8-default-and-new-profiler">Python 3.15.0 releases with JIT upgrade, UTF-8 default and ...</a></li>
<li><a href="https://byteiota.com/python-3-15-jit-how-to-enable-benchmark-performance/">Python 3.15 JIT: How to Enable &amp; Benchmark Performance</a></li>

</ul>
</details>

**标签**: `#Python`, `#programming languages`, `#open source`, `#software releases`, `#JIT compilation`

---

<a id="item-tech-news-3"></a>
### [Anthropic 推出 OSS Scanner 开源漏洞扫描服务](https://www.anthropic.com/research/launching-opt-in-vuln-finding-service-for-open-source) ⭐️ 8.0/10

Anthropic 推出 OSS Scanner，面向符合条件的开源项目提供免费、自愿接入的漏洞扫描服务。报告由 Claude 等模型生成且不经人工审核，包含漏洞复现、漏洞说明，并尽可能给出补丁建议，可能存在错误。Anthropic 称过去半年发现逾 2.9 万个候选漏洞，人工审查约 6000 个；早期测试的 97 个高危或严重漏洞中，85 个符合其披露流程要求。符合条件项目的核心维护者可提交 GitHub PR 申请使用该服务。

telegram · zaihuapd · 10月9日 02:00

**「背景」** 据外部报道，OSS Scanner 的做法来自 Anthropic 在 Project Glasswing 中利用 Claude 寻找漏洞的经验，该服务对登记项目进行周期性扫描。此前 Horizon 10 月 3 日的日报曾报道，Greg Kroah-Hartman 在 Kernel Recipes 2026 演讲中审视 Anthropic 的 Mythos 项目宣称发现的 79 个内核漏洞，称其中 24 个没有任何细节、14 个并非漏洞、只有 20 个需要修复，这一插曲反映了 LLM 生成的漏洞报告此前受到内核维护者质疑，也凸显新服务为何强调项目自愿接入并对约 6000 份报告做人工审查。

**「对开源维护者的影响」** 对符合条件的开源项目维护者来说，接入 OSS Scanner 后可免费获得定期扫描，报告包含漏洞复现、说明以及可能的补丁建议，且需由核心维护者通过 GitHub PR 申请。由于报告由模型生成、未经人工审核并可能存在错误，维护者仍需自行复核结论后再决定是否修补，涉及高危或严重漏洞时还需按 Anthropic 的披露流程处理。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.youtube.com/watch?v=NnV_cWeoo5Q">2026-10-03 — Kroah-Hartman 评 Mythos 的 79 个 LLM 内核漏洞报告</a></li>
<li><a href="https://www.anthropic.com/research/launching-opt-in-vuln-finding-service-for-open-source">An opt - in vulnerability -finding service for open - source software</a></li>
<li><a href="https://www.anthropic.com/research/launching-opt-in-vuln-finding-service-for-open-source">An opt-in vulnerability-finding service for open-source ...</a></li>
<li><a href="https://cybersecuritynews.com/anthropic-oss-scanner/">New Anthropic OSS Scanner Tool to Scan Open-source ...</a></li>
<li><a href="https://red.anthropic.com/oss-scanner/">OSS Scanner - red.anthropic.com</a></li>

</ul>
</details>

**标签**: `#AI security`, `#open source security`, `#vulnerability scanning`, `#Anthropic`, `#Claude`

---

<a id="item-tech-news-4"></a>
### [Carrier-Explode：解码 iPhone、Pixel 和 Galaxy 运营商设置](https://carrierexplode.com/) ⭐️ 7.0/10

Carrier-Explode 是作者 simplyalec 在 Hacker News 上展示的侧项目，持续归档 iPhone、Pixel 和 Galaxy 等主要手机品牌的运营商设置，并提供常见基带配置的解码器和说明。作者表示仍有许多假设需要验证，但该工具已在一些爱好者群体中被证明有用。它并非厂商发布的官方工具，而是一个个人维护的参考站点。

hackernews · simplyalec · 10月9日 18:10 · [社区讨论](https://news.ycombinator.com/item?id=50024499)

**「背景」** 运营商设置（carrier settings / carrier bundle）是随 iOS、Android 下发的配置文件，用于控制 VoLTE、5G 独立组网等基带行为，普通用户通常只会在系统提示「运营商设置更新」时察觉到它的存在。2026 年 10 月初 Tidbits 报道，iPhone 18 Pro Max 的 AT&amp;T 用户被建议升级到 iOS 27.0.1 并安装新的运营商设置，以规避可能中断服务、甚至需要更换硬件的缺陷；AT&amp;T 的支持页面也分别说明了该机型的运营商锁定状态查询以及 LTE/5G 语音与数据设置切换。这说明运营商设置的内容并非无关紧要的细节，而是会直接影响设备可用性。

**「对使用者意味着什么」** 对需要在不同运营商和机型之间核对网络功能的用户与开发者来说，carrier-explode 已把 iPhone、Pixel、Galaxy 固件中的 APN、VoLTE、Wi‑Fi 通话和 5G 配置整理成可查询、可对比的条目，可以按所需功能反查哪些运营商支持（tool-3-1）。但站方表示解码器仍在完善中，并公开征集贡献，因此结果可能随版本变动；同时固件配置只反映设备端的配置方式，并不等于实际网络服务可用，宜作为线索而非结论使用（tool-3-1、tool-3-2）。

**「社区讨论」** 有评论者提到该工具曾在 MacRumors 关于 AT&amp;T iPhone 18 Pro Max 死机问题的讨论中被引用，并称 AT&amp;T/Apple 可能通过禁用 5G Standalone 模式来避免硬件损坏，但官方除更换受影响硬件外尚未发布说明。另有用户赞赏它覆盖自己国家的运营商而非仅限美国，还有人建议向 GNOME 的 mobile-broadband-provider-info 项目贡献数据。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.att.com/device-support/article/155195/apple/iphone-18-pro-max/">Apple iPhone 18 Pro Max - Checking if your phone is carrier ...</a></li>
<li><a href="https://www.att.com/device-support/article/155226/apple/iphone-18-pro-max/">Apple iPhone 18 Pro Max - Switching LTE or 5G Voice ... - AT&amp;T</a></li>
<li><a href="https://tidbits.com/2026/10/06/iphone-18-pro-max-att-users-update-to-ios-27-0-1-and-new-carrier-settings/">iPhone 18 Pro Max AT&amp;T Users: Update to iOS 27.0.1 and New ...</a></li>
<li><a href="https://carrierexplode.com/">iPhone, Pixel and Galaxy carrier settings, decoded · carrier ...</a></li>
<li><a href="https://runtimewire.com/article/carrier-explode-alec-dusheck-carrier-settings">carrier-explode makes phone firmware searchable for carrier ...</a></li>

</ul>
</details>

**标签**: `#mobile networking`, `#carrier settings`, `#baseband`, `#iOS`, `#Android`

---

<a id="item-tech-news-5"></a>
### [Windows 与 Mac 键盘差异分析引发切换成本讨论](https://unsung.aresluna.org/deeper-dive-keyboard-differences-between-windows-and-macs/) ⭐️ 7.0/10

一篇详细分析 Windows 与 Mac 键盘差异的文章（unsung.aresluna.org）在 Hacker News 上引发广泛讨论，焦点是跨平台切换的实际成本。讨论涉及 macOS 的 ⌘ Command、⌥ Option、⌃ Control、⇧ Shift 与 Windows 键盘习惯的差异，以及用右 Alt 输入波兰语变音字符等国际布局问题。该帖获得 320 分和 259 条评论，属于经验与技术细节交流，而非重大产品发布。

hackernews · sohkamyung · 10月9日 03:08 · [社区讨论](https://news.ycombinator.com/item?id=50015515)

**「背景」** 跨平台 Web 应用往往用同一套代码同时服务 Windows 和 macOS，而两个平台在键盘层面的差异远不止「把 Ctrl 换成 ⌘ Command」这一处：修饰键的数量、按键上的标注、快捷键的书写方式，以及文本框内的光标导航规则都不相同。Unsung 的这篇深度整理把数十项此类差异集中记录成一份参考清单，供同时面向两个平台的开发者对照使用。

**「社区讨论」** 评论者 szszrk 称 Control/Command 混淆以及用右 Alt 输入波兰语变音字符不直观，最终让他放弃 Mac，并提到认识其他放弃 Mac 的人；RobGR 也分享说，帮助不熟悉 Windows/Mac 的用户时需要重新教授 Ctrl-C/X/A/V 等基础操作。bombcar 则解释 Delete 键差异源于 Windows 继承 DOS 的“光标在字符上”模型，而 Mac 的光标在字符之间。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.youtube.com/watch?v=l6opGxv5UDE">Keyboard differences between Windows and Macs #Shorts Keyboard differences between Windows and Macs create hidden ... Deeper dive: Keyboard differences between Windows and Macs Mac vs Windows Keyboard: Key Differences &amp; Useful Shortcuts Keyboard differences between Windows and Macs Keyboard differences between Windows and Macs - thenote.app</a></li>
<li><a href="https://news.lavx.hu/article/keyboard-differences-between-windows-and-macs-create-hidden-friction-for-cross-platform-developers">Keyboard differences between Windows and Macs create hidden ...</a></li>

</ul>
</details>

**标签**: `#keyboards`, `#human-computer interaction`, `#macOS`, `#Windows`, `#platform differences`

---

<a id="item-tech-news-6"></a>
### [微软开源 MXC：统一封装多平台沙箱执行](https://github.com/microsoft/mxc) ⭐️ 7.0/10

Hacker News 上受到关注的是微软的开源项目 MXC（github.com/microsoft/mxc），它把 bubblewrap、seatbelt、processcontainer 等操作系统沙箱原语抽象为一致的沙箱化代码执行接口。据 HN 评论，该项目提供用于探测运行时所需权限的 learning 模式，采用 MIT 许可证，并披露了可选遥测；其 Rust SDK 的 API 也被认为较易使用。讨论同时指出，macOS 后端缺少 Windows 和 Linux 已支持的细粒度网络控制，包括按主机名以及按 IP、CIDR、端口或协议允许/拒绝。另有评论称项目约 35 万行、以 Rust 为主，且未 vendor 上游沙箱。

hackernews · nreece · 10月9日 05:51 · [社区讨论](https://news.ycombinator.com/item?id=50016489)

**「背景」** MXC（Microsoft eXecution Container）是一个用于在 Windows、Linux 和 macOS 上运行不受信任代码（如模型输出、插件和工具）的沙箱化执行系统。它的设计要点是把多种隔离后端——从操作系统原生进程沙箱一直到完整虚拟机——收敛到统一的 containment 模型、配置 schema 和类型化 SDK 之下；Linux 的 bubblewrap、macOS 的 seatbelt、Windows 的 processcontainer 在这里是可替换的后端实现，而非各自独立的使用方式。

**「影响」** 对需要在 Linux、Windows 和 macOS 上运行不可信代码的开发者，MXC 可避免手写 bubblewrap、seatbelt 或 processcontainer 配置带来的不一致和出错风险。但若强依赖 macOS 上的网络隔离，当前需接受缺少按主机名、IP、CIDR、端口或协议控制的条件，或另行补充网络限制。

**「社区讨论」** HN 评论认为 MXC 作为 bubblewrap、seatbelt 和 processcontainer 的一致封装有实用价值：dannyw 称手工配置沙箱很容易出错，并称赞 learning 模式、MIT 许可证、遥测披露和文档。simonw 指出 macOS 后端缺少细粒度网络控制；neobrain 追问是否存在从最小沙箱开始、按需异步添加且可撤销权限的动态授权机制，kernc 则对约 35 万行、以 Rust 为主的代码量和未 vendor 上游沙箱的可审计性表示保留。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://github.com/microsoft/mxc">GitHub - microsoft/mxc: Policy-driven, layered isolation and ...</a></li>
<li><a href="https://github.com/microsoft/mxc/blob/main/">GitHub - microsoft/mxc: Policy-driven, layered isolation and ...</a></li>

</ul>
</details>

**标签**: `#sandboxing`, `#code execution`, `#security`, `#open source`, `#AI agents`

---

<a id="item-tech-news-7"></a>
### [OpenAI 解雇三名安全研究员 当事人否认指控](https://techcrunch.com/2026/10/08/fired-openai-safety-researchers-dispute-misconduct-claims-warn-of-chilling-effect/) ⭐️ 7.0/10

TechCrunch 10 月 8 日报道，OpenAI 以“研究信息处理不当”为由解雇了三名安全研究员。涉事研究员否认这一不当行为指控，并警告此举会产生寒蝉效应；现有来源没有披露被指处理不当的具体研究内容，也没有给出 OpenAI 的详细说明。评论中流传的材料显示，被解雇者发布了公开信，BBC 报道他们称自己是因为“把安全放在首位”而被解雇，CNBC 于 10 月 9 日发布了后续报道。

hackernews · trakkstar · 10月9日 10:00 · [社区讨论](https://news.ycombinator.com/item?id=50018350)

**「背景」** 此次争议的三名当事人是 OpenAI 安全研究人员 Jasmine Wang、Tomek Korbak 和 Mikita Balesni，他们发表公开信，反驳公司关于其“不当处理机密数据”的说法，并警告解雇事件正在对内部 AI 安全文化产生寒蝉效应。据 TechCrunch 报道，OpenAI 尚未对公开信作出正式回应，但向该媒体提供了一份署名研究负责人的内部备忘录，其中称赞三人在 AI 安全方面的贡献，并否认解雇是报复行为。

**「影响」** 对 OpenAI 内部仍在职的安全研究人员而言，被解雇同事在公开信中称此次解雇造成“寒蝉效应”，可能削弱公司的 AI 安全文化；其中一名被解雇研究员 Mikita Balesni 公开表示，他相信自己是因为“将安全置于 OpenAI 的近期公司利益之上”而被解雇。这意味着员工在内部提出或坚持安全关切时，可能面临更大的职业风险。

**「社区讨论」** 评论者大多表达怀疑与担忧：有人半开玩笑地说，或许是一群失控的 LLM 认为这些安全研究员是威胁才导致他们被解雇；也有人把当前的 AI 竞赛类比为核能，认为事故一旦发生后果难以挽回；还有评论者质疑，若因对受雇审计人员“过于坦诚”而被解雇，金融审计中是否也会容忍同样做法。评论中分享了被解雇研究员的公开信 PDF 和 BBC 报道链接，但这些属于评论者提供的材料，未在来源中得到独立核实。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://techcrunch.com/2026/10/08/fired-openai-safety-researchers-dispute-misconduct-claims-warn-of-chilling-effect/">Fired OpenAI safety researchers dispute misconduct claims , warn...</a></li>
<li><a href="https://chang.aevumnews.com/en/openai-ex-safety-researchers-challenge-misconduct-claims-allege-chilling-effect">OpenAI Ex- Safety Researchers Challenge Misconduct Claims ...</a></li>
<li><a href="https://chang.aevumnews.com/en/openai-ex-safety-researchers-challenge-misconduct-claims-allege-chilling-effect">OpenAI Ex- Safety Researchers Challenge Misconduct Claims, Allege...</a></li>
<li><a href="https://techxplore.com/news/2026-10-accuse-openai-chilling-safety-efforts.html">Fired researchers accuse OpenAI of &#x27; chilling &#x27; safety efforts</a></li>

</ul>
</details>

**标签**: `#AI safety`, `#OpenAI`, `#AI governance`, `#tech industry`, `#ethics`

---

<a id="item-tech-news-8"></a>
### [Matthew Green：AI 带来的密码学意外或快于标准更替](https://simonwillison.net/2026/Oct/9/matthew-green/) ⭐️ 7.0/10

密码学家 Matthew Green 在 Twitter 上给出两个主观概率判断：他认为有 1% 的可能性我们生活在 “Minicrypt” 中——即 Russell Impagliazzo 提出的、公钥加密在原理上不可能实现的假想计算世界——另有 15% 的可能性我们会实质性地失去对现有公钥加密算法的信心。他给出的核心理由是速度差：AI 制造意外发现的速度，与人类（即便有最好的 AI 协助）替换密码标准的速度相差数个数量级。因此他主张必须提前做好准备工作，因为只有事先准备过，才可能从这类意外中恢复。这是 Green 的个人风险预警与推测，并非已发生的破解、新的密码分析结果或已发布的标准变更；Simon Willison 在引用时补充了 Minicrypt 概念出自 Impagliazzo 及 Quanta Magazine 的解释。

rss · Simon Willison · 10月9日 15:02

**「背景」** Matthew Green 引用的 Minicrypt 来自 Russell Impagliazzo 提出的五种“计算世界”假说：在该假想世界中，单向函数存在，对称加密、哈希和伪随机函数等仍可运作，但公钥加密与密钥交换无法构造。Impagliazzo 与 Rudich 在 STOC&\#x27;89 中证明，在黑盒归约下无法从单向函数构造经典公钥加密，这为“公钥加密在 Minicrypt 中不可能”提供了理论基础。这些均为理论假想与不可能性结果，并不表示现行公钥算法已被攻破。

**「实际影响」** 对仍依赖现有公钥加密的组织而言，可操作的应对是提前建立“密码敏捷性”，而不是等标准替换完成后再行动：NIST 的 IR 8547 过渡时间表已计划在 2035 年前弃用并最终从标准中移除量子易受攻击算法，高风险系统需更早迁移，而实际迁移路线图通常把密码资产发现与优先级排序列为第一步。Green 提出的 1% Minicrypt 概率与 15% 失去信心的判断属于其个人估计，但其核心论点——标准替换速度与 AI 产生意外发现的速度相差数个量级——意味着提前准备是缩短响应窗口的前提。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://x.com/grok/status/2108554105928978564">Grok on X: &quot;Minicrypt is one of Impagliazzo’s five ...</a></li>
<li><a href="https://eprint.iacr.org/2024/830">How (not) to Build Quantum PKE in Minicrypt</a></li>
<li><a href="https://arxiv.org/pdf/2405.20295">How (not) to Build Quantum PKE in Minicrypt - arXiv.org</a></li>
<li><a href="https://layerlogix.com/blog/post-quantum-cryptography-migration-roadmap-2026">Post-Quantum Cryptography Migration: 2026 Roadmap | LayerLogix</a></li>
<li><a href="https://csrc.nist.gov/projects/post-quantum-cryptography">Post-Quantum Cryptography | CSRC</a></li>

</ul>
</details>

**标签**: `#cryptography`, `#AI risk`, `#public-key encryption`, `#security standards`, `#Minicrypt`

---

<a id="item-tech-news-9"></a>
### [GCC 加入内核前向边 CFI 检查补丁](https://lwn.net/Articles/1098670/) ⭐️ 7.0/10

在 2026 年 GNU Tools Cauldron 上，Kees Cook 介绍了为 GCC 添加内核前向边控制流完整性（CFI）检查的补丁系列，目标是在间接函数调用时校验目标函数原型，防止攻击者劫持控制流。该实现引入 -fsanitize=kcfi 选项，在函数入口前放置由函数原型生成的类型 ID 哈希（现用 FNV-1a），调用点存该哈希的二进制补码取反，相加为零才允许调用；类型改编沿用 Clang 的 Itanium C++ mangler 以保持兼容，后端已覆盖 x86-32、x86-64、Arm64 和 RISC-V。校验失败时，宽松模式仅告警，严格模式则触发 panic；Cook 称约一半补丁是回归测试，但该系列尚未合并，且他表示很难找到能评审整个编译器栈的评审者，GCC 全球评审 Andrea Pinski 回应完整评审即将进行。作为背景，Clang 在 2022 年已实现同类前向边 CFI，Linux 内核自 6.1 起可使用该特性。

rss · LWN.net · 10月9日 17:06

**「背景」** 控制流完整性（CFI）的目标是阻止攻击者劫持间接函数调用或函数返回，从而把内核中的任意写漏洞升级为代码执行；其中保护间接调用称为“前向边”CFI，保护返回则称为“后向边”CFI，后者通常交由硬件处理。与仅标记函数入口的硬件辅助方案不同，前向边 CFI 用函数原型哈希生成类型 ID，并在每个间接调用点校验目标函数，因此可以排除跳转到某个完全不同函数的情况。这类检查早在 2022 年就已由 Clang 实现，Linux 内核自 6.1 起可使用该功能，而 GCC 此前一直没有等价实现。

**「影响」** 该补丁系列目前仍未合入 GCC：GCC 邮件列表 1 月的讨论指出，由于提交时间过晚、已经赶不上 GCC 16 的 stage 4，评审者预计它最早要在 GCC 17 stage 1（约 3 月中下旬）才有机会落地（tool-2-1、tool-2-2）；而据 10 月 Cauldron 上的演讲，这套跨前端、RTL 与后端四个架构的补丁仍在等待完整评审。对希望在内核中启用前向边 CFI 的用户而言，短期内仍只能依赖 2022 年就已实现的 Clang 支持（内核自 6.1 起可用），使用 GCC 构建内核时尚无法获得同等检查。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://gcc.gnu.org/pipermail/gcc-patches/2026-January/705447.html">[PATCH v9 0/7] Introduce Kernel Control Flow Integrity ABI ...</a></li>
<li><a href="https://gcc.gnu.org/pipermail/gcc-patches/2026-January/705309.html">[PATCH v9 0/7] Introduce Kernel Control Flow Integrity ABI ...</a></li>

</ul>
</details>

**标签**: `#kernel security`, `#control-flow integrity`, `#compilers`, `#GCC`, `#open source`

---

<a id="item-tech-news-10"></a>
### [systemd 2026 状态：季度发布落地，AI 提交令审查承压](https://lwn.net/Articles/1099024/) ⭐️ 7.0/10

在 2026 年 All Systems Go\! 大会上，维护者 Luca Boccassi 与 Zbigniew Jędrzejewski-Szmek 做了年度项目状态报告，随后 Boccassi、Jędrzejewski-Szmek、Daan De Meyer 和项目负责人 Lennart Poettering 参加圆桌讨论，并明确表示 systemd 不会取代 Kubernetes。项目把发布节奏从 v258 所需的约九个月改为季度发布——两个月合并功能、一个月稳定与候选版本，2026 年迄今已发布 v260、v261、v262 三个大版本，2025 年则发布了 v258、v259 以及 40 个点版本。Boccassi 称 2025 年合并了来自 379 名贡献者的 6,160 个提交，低于 2024 年的 7,372 个，而到 2026 年 9 月底贡献者已达 480 人，他称增长主要源于人们使用 LLM 编程工具。Jędrzejewski-Szmek 则表示未解决 issue 已达 3,000 个，自 2025 年中期起 PR 数量呈指数增长，若继续下去项目将无法继续审查，而提交合并速度基本不变，他的假设是实际参与审查的人数没有太大变化。

rss · LWN.net · 10月9日 14:58

**「背景」** systemd 是大多数主流 Linux 发行版使用的初始化与服务管理系统，其维护者在每年 All Systems Go\! 会议上的“项目状态”环节公布发布节奏、贡献者规模与项目健康度。Horizon 2026 年 6 月 20 日的日报曾报道 v261 发布，新增面向云环境的 IMDS 子系统、在无 TPM 机器上使用的“boot secret”机制，以及对内核 Live Update Orchestration 与 Kexec Handover 的支持（tool-1-1）；LWN 本次报道中所说的 2026 年三次大版本发布（v260、v261、v262）和转向季度发布节奏，对应的正是这一系列持续迭代。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://lwn.net/Articles/1078708/">2026-06-20 — Systemd v261 released with IMDS, boot secrets, and live update support</a></li>

</ul>
</details>

**标签**: `#systemd`, `#Linux`, `#open source`, `#init systems`, `#service management`

---

<a id="item-tech-news-11"></a>
### [Let&\#x27;s Encrypt 将于 2027 年 2 月启用 64 天期证书](https://lwn.net/Articles/1099588/) ⭐️ 7.0/10

Let&\#x27;s Encrypt 宣布，自 2027 年 2 月 10 日起，其在该日期当天及之后签发或续期的所有证书有效期将变为 64 天，预计最后一张 90 天期证书会在 2027 年 5 月 11 日到期；该机构还表示不会因此吊销现有的有效证书。这是 Let&\#x27;s Encrypt 于 2025 年公布的过渡计划的第二阶段，最终目标是在 2028 年改为 45 天有效期，以满足 CA/Browser Forum 基线要求。上述内容目前仍是已宣布的安排，尚未生效。

rss · LWN.net · 10月9日 14:02

**「背景」** Let&\#x27;s Encrypt 长期签发 90 天有效期的免费 TLS 证书，而公开信任证书的有效期上限由 CA/Browser Forum 的 Baseline Requirements 规定。据 SSL Insights 报道，该论坛已于 2025 年 4 月投票要求最迟在 2029 年 3 月把上限降至 47 天；DigiCert 则称自 2027 年 3 月 15 日起上限先降至 100 天。Let&\#x27;s Encrypt 在 2025 年公布的“从 90 天到 45 天”路线图选择比强制要求更早行动，此次 64 天有效期是该路线图中的中间一步，2028 年再切换至 45 天。

**「影响与行动」** 对依赖 Let&\#x27;s Encrypt 的站点和运维团队而言，2027 年 2 月 10 日起签发的证书默认只有 64 天有效期，也可选择更短的 45 天或 6 天；据 Geekslop 报道，这会迫使网站管理员采用 ACME 自动化续期和 ARI 驱动的续期机制，否则手工更新流程将更难跟上更短的续期周期。据 Ars Technica 报道，Let&\#x27;s Encrypt 同时把授权复用期从 30 天压缩到 10 天，并计划到 2028 年进一步缩短至 7 小时，相关 ACME 客户端和验证流程也需要提前验证兼容性。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://sslinsights.com/lets-encrypt-mtls-deprecation-45-day-certificates/">Let&#x27;s Encrypt mTLS Deprecation &amp; 45 - Day Certificates</a></li>
<li><a href="https://www.digicert.com/blog/tls-certificate-lifetimes-will-officially-reduce-to-47-days">TLS Certificate Lifetimes Will Officially Reduce to 47 Days | DigiCert</a></li>
<li><a href="https://www.geekslop.com/technology-articles/computers-programming/hacking-and-security-technology-articles/2026/lets-encrypt-64-day-ssl-certs">Let ’ s Encrypt cuts SSL cert lifetimes to 64 days , automation or bust</a></li>
<li><a href="https://arstechnica.com/gadgets/2026/10/lets-encrypt-cuts-certificate-lifetimes-to-64-days-starting-february-2027/">Let &#x27; s Encrypt cuts certificate lifetimes to 64 days ... - Ars Technica</a></li>
<li><a href="https://letsencrypt.org/2026/10/07/64-day-certs">64 - Day Certificate Lifetimes Coming Feb 2027 - Let &#x27; s Encrypt</a></li>

</ul>
</details>

**标签**: `#TLS`, `#certificates`, `#Let&\#x27;s Encrypt`, `#PKI`, `#web security`

---

<a id="item-tech-news-12"></a>
### [Telegram Desktop 7.2.9 以下版本曝一键窃取文件漏洞](https://telegram.me/zaihuapd/44307) ⭐️ 7.0/10

据 Telegram 聚合频道援引 OpenNET 的通报，Telegram Desktop 7.2.9 以下版本存在严重漏洞（CVE-2026-107181），用户点击恶意 tg:// 链接后，系统文件可能在无确认的情况下被悄悄窃取。漏洞成因是链接中的分号未被转义、被当作独立 IPC 命令处理，配合 interpret: 处理器可读取文档、浏览器会话、SSH 密钥、加密钱包等任意文件。通报称官方已在 7.2.9 版本中修复，并建议尽快升级、警惕异常 tg:// 链接并启用本地密码。目前该信息来自简短的安全提醒而非详细的一手分析，修复情况尚未独立验证。

telegram · zaihuapd · 10月9日 09:51

**「背景」** 该漏洞被外部漏洞库归类为 Telegram Desktop 核心沙箱（Core::Sandbox）中的 IPC 记录分隔符注入（record-separator injection）问题，影响 7.2.9 之前的版本。这类注入的成因是应用在进程间传递命令时依赖分隔符切分消息，若输入未正确转义，攻击者就能让一个链接参数被当作额外 IPC 命令执行。

**「影响」** 对仍运行 7.2.9 之前版本的桌面用户而言，最直接的做法是升级到 7.2.9，并在升级前避免点击来源不明的 tg:// 链接；来源同时建议启用本地密码，以降低文件被静默读取的风险。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://securityvulnerability.io/vulnerability/CVE-2026-107181">CVE - 2026 - 107181 : IPC Record-Separation Injection Vulnerability in...</a></li>
<li><a href="https://security-tracker.debian.org/tracker/CVE-2026-107181">CVE - 2026 - 107181</a></li>

</ul>
</details>

**标签**: `#security vulnerability`, `#Telegram Desktop`, `#CVE-2026-107181`, `#software update`, `#privacy`

---

## 科技博客

<a id="item-tech-blog-1"></a>
### [软件工程的“半人马时代”或将持续数十年](https://seangoedecke.com/softwares-centaur-age-may-last-decades/) ⭐️ 5.0/10

rss · Sean Goedecke · 10月10日 00:00

**「背景」** 作者认为，2022 年以来软件工程进入了“半人马时代”：人类工程师与 AI 编码系统配合时的产出，超过任何一方单独工作；而人们总急于宣布这个阶段已经结束、AI 独霸的时代已经开始。

**「方案」** 作者借国际象棋的经验反驳这种急躁：棋界的半人马时代持续了约二十年，更早的针织业人机配合时代则长达两百年。软件这边，2022 年 GitHub Copilot 以 AI 自动补全起步，GPT-4 让工程师能就完全陌生的领域随时请教通才；2024 年 Cursor 的 agent 模式与 2025 年初的 Claude Code 让编码代理走向台前，早期仍需密切监督，而 2025 年 11 月 Claude Opus 4.5 发布后已可靠到可完全无人值守，其错误更多是“对齐”问题——不符合组织的技术价值观、该投入的地方过度或不足设计——而非普通 bug。作者判断，无辅助的工程师已赢不了半人马团队，但无人监督的代理同样还赢不了半人马团队。至于这个时代会比象棋更短还是更长，他列出一串互相抵消的理由：象棋更简单且适合自我对弈，软件工程利润更高、投入资金多出数个数量级，“解决”软件工程反而创造出更多待做的工作，通用 AI 的涟漪效应可能反噬软件业本身，而技术变化又在加速。他坦承没人真正知道答案，只能默认与象棋相近。由此他建议：不要辞职转行，不要拒绝成为半人马，并认真思考人类还能提供什么价值——2023 年靠的是技术专长，如今他个人认为是“对齐”，也有人主张是品味。

**「启示」** 作者的核心结论是：全自动化的幽灵可能在地平线上徘徊数十年，因恐慌而过早跳船，可能白白放弃一整个正常长度的职业生涯；与其跳向最坏情形，不如先研究软件工程当下如何运作。

**标签**: `#AI-assisted software engineering`, `#centaur age`, `#software engineering careers`, `#LLM coding agents`, `#industry analysis`

---