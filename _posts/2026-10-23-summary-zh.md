---
layout: default
title: "Horizon Summary: 2026-10-23 (ZH)"
date: 2026-10-23
lang: zh
---

> 从 42 条内容中筛选出 16 条重要资讯。

---

**科技新闻**
1. [eMudhra 宣布退出全球 SSL/TLS 证书业务](#item-tech-news-1) ⭐️ 8.0/10
2. [Switch 2 越狱与 LLM 代理自动化漏洞研究](#item-tech-news-2) ⭐️ 8.0/10
3. [Quad9 因 DNS 封锁争议拟退出法国](#item-tech-news-3) ⭐️ 8.0/10
4. [澳法院令苹果 2027 年开放第三方应用商店](#item-tech-news-4) ⭐️ 8.0/10
5. [OpenShell：面向自主 AI 代理集群的受控运行时](#item-tech-news-5) ⭐️ 7.0/10
6. [Earstrip 三角剖分 370 万地图多边形耗时 489 毫秒](#item-tech-news-6) ⭐️ 7.0/10
7. [Getting ready to operate GNU Taler in Germany](#item-tech-news-7) ⭐️ 7.0/10
8. [GitHub 项目声称在 Android 与 QEMU 上运行 iOS 16.5](#item-tech-news-8) ⭐️ 7.0/10
9. [Anthropic 将 Agent Skills 标准捐赠给 Agentic AI Foundation](#item-tech-news-9) ⭐️ 7.0/10
10. [KeePassXC 2.8.0 发布，迁移 Qt6 并支持 Wayland 自动输入](#item-tech-news-10) ⭐️ 7.0/10
11. [研究：部分智能电视关闭 ACR 后仍上传观看数据](#item-tech-news-11) ⭐️ 7.0/10
12. [米哈游与清华开源 GameScaling 键鼠操作模型](#item-tech-news-12) ⭐️ 7.0/10
13. [333 个 Tor 出口节点因 Ebury 后门被下线](#item-tech-news-13) ⭐️ 7.0/10
14. [报告称中国国资融资购入禁运的英伟达 B300 服务器](#item-tech-news-14) ⭐️ 7.0/10

**科技博客**
1. [软件慢在设计，而非慢语言](#item-tech-blog-1) ⭐️ 6.0/10

**财经新闻**
1. [沪深 300 较 6 月高点回落 20%，A 股逼近熊市](#item-finance-news-1) ⭐️ 8.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [eMudhra 宣布退出全球 SSL/TLS 证书业务](https://emudhra.com/en/press-release/emudhra-to-exit-global-ssl-tls-certificate-business) ⭐️ 8.0/10

eMudhra 宣布将退出全球 SSL/TLS 证书业务，这一决定出现在该公司因一起事件受到审查之际。公司称，围绕该事件的社交媒体放大带来了与其 SSL/TLS 业务占比不相称的审查，并强调其全球 SSL/TLS 基础设施与其他业务隔离运行。公司还表示，受影响 CA 未签发终端实体证书。

hackernews · bo0tzz · 10月22日 13:33 · [社区讨论](https://news.ycombinator.com/item?id=50195110)

**「事件背景」** Horizon 10 月 21 日的日报曾报道，社区指认 eMudhra 的 8 个中间 CA 私钥都只有一个字节，并初步将其归因于生成 ECC 签发者时使用的 KGC 脚本缺陷；这些说法当时尚未获独立验证，而 Firefox 已通过 OneCRL 在数小时内自动吊销相关证书。此后 Chrome 与 Firefox 撤销对 eMudhra ECC 根的信任，直接影响其全球 TLS 证书被浏览器接受，这也构成公司宣布退出该业务、并承诺维持吊销和证书状态服务直至所有已签发证书过期或被替换的背景。

**「影响」** 对依赖 eMudhra 全球 TLS 证书的网站运营方来说，直接后果是需要另选 CA、重签证书并更新信任链；同时应核对现有证书的有效期，以及浏览器和操作系统对其根证书的信任状态。

**「社区讨论」** 评论者批评 eMudhra 以“社交媒体放大”解释外界审查，却没有说明事件是人为错误还是流程错误；也有人质疑“受影响 CA 未签发终端实体证书”的说法，称任何人都可以从受影响的 CA 签发证书。另有评论指向 Chrome 团队在 Mozilla Bugzilla 上对该公司的公开质询。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://emudhra.we-have-a-problem.com/">2026-10-21 — eMudhra 中间 CA 私钥被指仅一字节</a></li>
<li><a href="https://thehackernews.com/2026/10/emudhra-to-exit-global-ssltls-business.html">eMudhra to Exit Global SSL/TLS Business After 8 Intermediate ...</a></li>
<li><a href="https://emudhra.com/en/press-release/emudhra-to-exit-global-ssl-tls-certificate-business">eMudhra to Exit global SSL/TLS Certificate Business</a></li>

</ul>
</details>

**标签**: `#SSL/TLS`, `#certificate authorities`, `#PKI security`, `#browser trust stores`, `#security incidents`

---

<a id="item-tech-news-2"></a>
### [Switch 2 越狱与 LLM 代理自动化漏洞研究](https://pepsipu.com/blog/2026-10-switch2-jailbreak-ns2jb/) ⭐️ 8.0/10

一篇 10 月 22 日发布的博客文章公开描述了针对 Nintendo Switch 2 的越狱，并介绍了为自动化漏洞研究搭建的硬件与 LLM 代理环境。文章称使用 JetKVM 通过 USB 向主机发送手柄输入、通过 HDMI 获取视频输出，让 Codex 参与研究流程，并在主机崩溃时用蓝牙开关装置按压电源键重启。材料未提供原文内容，也未给出所利用漏洞、适用固件版本或独立复现结果，因此这些说法目前只能视为博客作者的自述。

hackernews · ledoge · 10月22日 08:01 · [社区讨论](https://news.ycombinator.com/item?id=50192536)

**「背景」** 据 GBAtemp 和 Notebookcheck 报道，此次披露的 ns2jb 是一个纯软件的用户态（userland）漏洞利用，据称可在最新的 23.0.1 固件上运行，能够加载自制程序和游戏模组，但属于需要重新触发的「有线」（tethered）利用，重启后并非永久有效。用户态意味着代码运行在游戏应用所在的权限层，而不是 bootrom 或内核层，因此这类利用在持久性和可修补性上与硬件漏洞不同。此前 8 月的日报曾报道，任天堂在同一天向 GitHub 提交 7 份 DMCA 通知，下架了 400 多个 Switch 模拟器仓库（仅针对 suyu 的就有 311 个），显示其对该生态的法律执行力度。

**「实际影响」** 对 Switch 2 用户而言，这个纯软件、系留式（tethered）越狱可在最新固件上运行任意原生代码，从而支持自制程序、修改游戏和备份存档；但它的临时性意味着设备重启后需要重新建立越狱环境，不能当作永久性破解。

**「社区讨论」** 评论者 hturan 认为，若博客所述可解密并以读写方式挂载 \`fs\` 属实，Switch 2 游戏转储可能很快出现，并可能通过 recomp/decomp 在非原生硬件上运行；这是有条件的推测，而非已证实的结果。另一名评论者 rootsudo 则报告了相反的使用体验，称 Codex 在调查旧 Android ROM 的 CVE 时拒绝配合，但在 Microsoft 漏洞赏金相关任务中可以使用，引发了对这类代理安全研究限制的讨论。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://torrentfreak.com/nintendo-wipes-out-400-switch-emulator-repos-in-single-day-github-sweep/">2026-08-23 — 任天堂单日下架 400 余个 Switch 模拟器仓库，suyu 占 311 个</a></li>
<li><a href="https://gbatemp.net/news/switch-2-jailbreak-ns2jb-released-software-only-exploit-tethered.685698/">Switch 2 jailbreak &quot;ns2jb&quot; released. Software-only exploit ...</a></li>
<li><a href="https://www.notebookcheck.net/The-Nintendo-Switch-2-has-reportedly-been-jailbroken-through-a-software-only-exploit.1431060.0.html">The Nintendo Switch 2 has reportedly been jailbroken through ...</a></li>
<li><a href="https://wccftech.com/nintendo-switch-2-hacked-jailbreak/">The Nintendo Switch 2 Has Been Hacked, As First Jailbreak Blows...</a></li>

</ul>
</details>

**标签**: `#console hacking`, `#security research`, `#LLM agents`, `#hardware automation`, `#Nintendo Switch 2`

---

<a id="item-tech-news-3"></a>
### [Quad9 因 DNS 封锁争议拟退出法国](https://quad9.net/news/blog/au-revoir-france/) ⭐️ 8.0/10

Quad9 计划退出法国，此前该国法院围绕 DNS 封锁产生纠纷，并对其处以藐视法庭罚款。Quad9 首席技术官（CTO）在评论中表示，公司很可能在 11 月 24 日之后用 geoIP 过滤阻止法国用户访问其服务，并承认这与「geoIP 无法按域名选择性封锁」的立场存在冲突。评论中引述的案情称，Sony Music 曾通过 VPN 从德国访问被封锁内容，法院据此认定 Quad9 未遵守命令。

hackernews · farrokhi · 10月22日 14:32 · [社区讨论](https://news.ycombinator.com/item?id=50195959)

**「背景」** 10 月 6 日的 Horizon 日报曾报道，Quad9 拒绝执行法国法院针对盗版体育直播的域名封锁令；beIN Sports 请求按每个域名每日 1 万欧元、共 58 个域名处罚，合计最高每日 58 万欧元，当时裁决尚未作出。Quad9 当时表示，由于不收集用户数据，它无法按国家精确执行针对特定域名的封锁，只能在全球封锁与退出法国市场之间选择。

**「影响」** 若该计划执行，法国用户届时将无法通过 Quad9 解析域名，需要改用其他公共 DNS；对解析器运营者而言，在法国提供服务可能因未执行域名封锁而面临法律处罚。

**「社区讨论」** 评论中，有人把处罚 DNS 解析器比作因电话簿收录罪犯号码而惩罚电话簿公司，质疑让解析器承担封锁责任是否合理；另有人指出 Sony 用 VPN 绕过 geoIP 后 Quad9 仍被罚，认为这暴露了 geoIP 封锁的局限。也有评论主张，Quad9 应停止解析起诉方相关的域名作为回应。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://torrentfreak.com/dns-resolver-quad9-rejects-french-piracy-blocks-weighs-exit-as-bein-seeks-up-to-e580k-a-day/">2026-10-06 — Quad9 拒绝法国 DNS 封锁令，或面临每日 58 万欧元罚款</a></li>

</ul>
</details>

**标签**: `#DNS`, `#internet infrastructure`, `#geo-blocking`, `#legal policy`, `#Quad9`

---

<a id="item-tech-news-4"></a>
### [澳法院令苹果 2027 年开放第三方应用商店](https://9to5mac.com/2026/10/21/apple-must-open-iphone-to-alternative-app-stores-in-australia-after-epic-games-ruling/) ⭐️ 8.0/10

澳大利亚联邦法院在 Epic Games 提起的反垄断诉讼中裁定，苹果须自 2027 年 3 月 1 日起允许澳大利亚 iPhone 用户通过第三方应用商店及网站安装应用，并开放替代支付方式和外部支付链接。法官认定苹果在 iOS 应用分发与支付市场拥有实质性市场力量，相关限制违反澳大利亚竞争法；Fortnite 也将立即重返澳大利亚 App Store。苹果表示将上诉并申请暂缓执行，因此这些开放措施能否按期落地仍存在不确定性。

telegram · zaihuapd · 10月22日 06:54

**「背景」** 这起澳大利亚诉讼是 Epic 与苹果围绕 iOS 应用分发和支付规则长期法律纠纷的一部分。4 月 8 日的日报曾报道，苹果已就美国法院要求其开放外部支付且不得收取高额佣金的裁决获准暂缓执行，并寻求最高法院审查；在本案中，苹果同样表示将上诉并申请暂缓执行。

**「实施时间仍存变数」** 若裁决按期生效，澳大利亚 iPhone 用户从 2027 年 3 月 1 日起可通过第三方应用商店和网站安装应用，开发者也能接入替代支付和外部支付链接，这将改变其在澳区的分发与抽成安排。苹果已表示将上诉并申请暂缓执行，时间表仍可能变动，计划依赖这些新渠道的开发者应把法律与合规不确定性纳入排期。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://techcrunch.com/2026/04/06/apple-epic-games-lawsuit-supreme-court-appeal-app-store-commission/">2026-04-08 — 苹果寻求最高法院审查 App Store 收费裁决，已获暂停执行许可</a></li>
<li><a href="https://www.resetera.com/threads/apple-ordered-to-open-the-app-store-to-alternate-stores-in-australia.1667204/">Apple ordered to open the App Store to alternate stores in Australia</a></li>

</ul>
</details>

**标签**: `#Apple`, `#antitrust`, `#app stores`, `#Australia`, `#Epic Games`

---

<a id="item-tech-news-5"></a>
### [OpenShell：面向自主 AI 代理集群的受控运行时](https://github.com/NVIDIA/OpenShell) ⭐️ 7.0/10

NVIDIA 在 GitHub 上开源了 OpenShell，一个面向需要批量运行自主 AI 代理的团队的受控运行时。它的目标是在代理读取文件、安装软件包、调用 API 和使用凭据时施加访问控制，而不是让它们无限制地接触数据、密钥和网络。项目将其定位为安全、私密的代理运行环境，但当前公开材料未提供独立技术验证，也未说明具体的隔离强度、支持平台或版本兼容性。

hackernews · niemandhier · 10月22日 17:44 · [社区讨论](https://news.ycombinator.com/item?id=50198675)

**「背景」** Horizon 2026 年 9 月 29 日日报曾报道，英伟达发布 Open Agent Safety Platform，其中 OpenShell 是运行在 CPU 上、用于限制智能体可执行操作的组件，Sentry 则负责网络层监控；当时报道指出尚无具体版本、开放时间或独立验证结果。此次条目指向 GitHub 上的 OpenShell 仓库，把它作为面向成批自主智能体的独立运行时，提供受控的文件、软件包、API 与凭据访问。

**「采用影响」** 对需要让代理读取文件、安装软件包并调用外部 API 的团队，采用 OpenShell 时需要按文件、凭据、进程和网络分别编写逐代理策略；这能收紧默认权限，但按社区反馈，仅按域名限制出网仍无法阻止经受信任域名的数据外泄，因此还应叠加独立的数据外泄防护。

**「社区讨论」** 评论者肯定这类运行时的实用价值：mfro 认为代理本就应该跑在容器里，而 OpenShell 提供了管理这些容器的方式；razuba 表示已在用 OpenShell，并在其上增加团队策略、安全 Git 使用和 SCA/SAST 层。另一些评论指出限制仍未被完全解决：fennecbutt 说按域名限制网络和替换凭据仍难以阻止代码库等数据外泄，smallnix 则认为“给足权限又保持安全”存在张力，项目描述容易显得过度承诺。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://developer.nvidia.com/blog/nvidia-open-agent-safety-platform-a-reference-for-continuous-in-silicon-agent-monitoring/">2026-09-29 — 英伟达发布 Open Agent Safety Platform 智能体安全平台</a></li>
<li><a href="https://bravenewcoin.com/insights/nvidia-launches-ai-agents-kill-switch-to-monitor-quarantine-and-stop-rogue-ai-systems">Nvidia Launches AI Agents Kill Switch to Monitor, Quarantine, and...</a></li>

</ul>
</details>

**标签**: `#AI agents`, `#agent security`, `#sandboxed runtime`, `#container isolation`, `#NVIDIA`

---

<a id="item-tech-news-6"></a>
### [Earstrip 三角剖分 370 万地图多边形耗时 489 毫秒](https://globus.software/blog/2026/10/16/cutting-map-polygons/) ⭐️ 7.0/10

一篇性能导向的工程文章展示了评论中称为 Earstrip 的三角剖分库：作者称其在约 370 万个地图多边形组成的语料上完成剖分仅用 489 毫秒，快于广泛使用的 earcut。文章公开了数据集，earcut 作者也参与了技术讨论；这仍是作者自测的基准，尚非独立复现的通用结论。对处理大规模 GIS 或图形几何的开发者，这一结果值得用自己的数据复测，并同时考察包体积与输出三角形质量。

hackernews · molind · 10月22日 09:31 · [社区讨论](https://news.ycombinator.com/item?id=50193170)

**「背景：地图多边形三角剖分与 earcut」** 三角剖分是把带孔洞的多边形拆成三角形、交给 GPU 渲染的关键一步；earcut 是这一环节最常用的 JavaScript 库之一。earcut 作者在讨论中提到，该库压缩后约 4.1 kB，在 Mapbox GL JS 等实际场景中已经够快，并称他有意放弃了一些优化以控制包体积。此次基准针对 3.7M 个地图多边形给出 489 ms 的结果并公开了数据集，而评论中的另一位三角剖分库作者（Delaunay32，采用分治而非增量插入）也表示希望在同一语料上对比，可见算法类别与包体积是这类库取舍的核心变量。

**「影响」** 对考虑替换 earcut 的团队，评估时不能只看 489 毫秒，还要把 WASM 包体积和输出三角形质量纳入同一基准；earcut 作者强调 4.1 kB min/gz 的小体积是其刻意取舍，另有评论者质疑大量细长三角形对 GPU 光栅化的影响。

**「社区讨论」** earcut 作者 mourner 称会看看是否有技巧可借用到 JS 版本，但指出自己为控制包体积（4.1 kB min/gz）刻意拒绝了一些优化；Delaunay32 作者 morishuz 则希望在同一语料上比较分治式约束 Delaunay 三角剖分。stymaar 还质疑结果中大量细长三角形是否不利于 GPU 光栅化。

**标签**: `#computational-geometry`, `#triangulation`, `#performance-optimization`, `#webassembly`, `#gis`

---

<a id="item-tech-news-7"></a>
### [Getting ready to operate GNU Taler in Germany](https://www.taler.net/en/news/2026-13.html) ⭐️ 7.0/10

GNU Taler is preparing for operation in Germany, drawing community debate over privacy, offline expiration, and regulatory constraints.

hackernews · dewey · 10月22日 16:14 · [社区讨论](https://news.ycombinator.com/item?id=50197404)

**标签**: `#GNU Taler`, `#digital payments`, `#privacy`, `#open source`, `#Germany`

---

<a id="item-tech-news-8"></a>
### [GitHub 项目声称在 Android 与 QEMU 上运行 iOS 16.5](https://github.com/oosexgang/hackios-xnu-kernel) ⭐️ 7.0/10

一个名为 hackios-xnu-kernel 的 GitHub 项目声称可在 Android 设备与 QEMU 上运行完整 iOS 16.5 固件/XNU 内核；提交者在 Hacker News 称，它已在 QEMU、POCO X5 Pro 5G 及部分小米设备上工作。现有材料中未见独立验证或详细技术说明，且有评论者称该项目是“研究台而非 ROM”：每次会话仅持续设定的秒数，随后内核返回加载器并交出日志。因此这更像是受控环境中的实验演示，而不是可供日常使用的 iOS 移植。

hackernews · aghuang · 10月22日 15:26 · [社区讨论](https://news.ycombinator.com/item?id=50196718)

**「背景」** XNU 是 iOS 的底层内核，要把它和 iOS 用户空间搬到 Android 硬件上，需要自行补齐引导链、内核补丁和设备驱动，而不是安装一个普通 ROM。Horizon 10 月 20 日的日报曾记录过同一方向的尝试：将 XNU 移植到红米 Note 10 Pro 并启动未修改的 iPhone X 版 iOS 16.7.16 用户空间；当时触摸和实体按键可用、画面由 CPU 渲染，但 GPU、Wi-Fi 和相机仍不可用，属于早期概念验证。当前仓库列出了 XNU 补丁、EFI 加载器、UEFI 移植、Wi-Fi、QEMU 脚本及预编译的 kernel/loader/UEFI，表明它同样是一套面向引导与硬件适配的研究工具链。

**「影响」** 按现有描述，这套方案不是可刷入并日常使用的 ROM，普通用户无法依赖它获得完整的 iOS 应用与手机功能兼容性。开发者的关注点更可能集中在受控会话中的启动流程、内核日志以及 QEMU 复现实验。

**「社区讨论」** 评论区的关键区别在于它究竟算不算“运行 iOS”：提交者强调 QEMU 与多款小米设备上的启动效果，而有评论者强调它只是限时返回日志的研究台，并非可用的 ROM。另有人提醒，这类演示可能让二手市场上的仿冒 iPhone 更难辨认。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://github.com/oosexgang/hackios-xnu-kernel">GitHub - oosexgang/ hackios - xnu - kernel · GitHub</a></li>
<li><a href="https://www.reddit.com/r/hackintosh/comments/1x95qq0/ios_16716_booting_on_a_snapdragon_732g_redmi_note/?sort=new">2026-10-20 — XNU 内核移植红米 Note 10 Pro，启动 iOS 16.7.16</a></li>

</ul>
</details>

**标签**: `#iOS`, `#Android`, `#XNU`, `#QEMU`, `#systems hacking`

---

<a id="item-tech-news-9"></a>
### [Anthropic 将 Agent Skills 标准捐赠给 Agentic AI Foundation](https://simonwillison.net/2026/Oct/22/donating-agent-skills/) ⭐️ 7.0/10

Anthropic 宣布把 Agent Skills 标准捐赠给 Linux 基金会旗下的 Agentic AI Foundation（AAIF），目标是让这一智能体互操作标准保持开放、由社区驱动并保持厂商中立。该基金会由 Anthropic 去年与 Block、OpenAI 共同创立，Anthropic 此前已把 Model Context Protocol（MCP）捐赠给它。Simon Willison 指出，他在 2025 年 12 月 Anthropic 首次称 Agent Skills 为“开放标准”时就预料到会如此。此次公告未说明移交的时间表、具体治理规则或技术变更。

rss · Simon Willison · 10月22日 18:09

**「背景：从 MCP 到 Agent Skills 的标准化路径」** MCP（Model Context Protocol）是 Anthropic 此前提出的智能体上下文与工具连接规范；据 Anthropic 说明，它去年与 Block、OpenAI 共同创立 Agentic AI Foundation（AAIF），并将 MCP 捐赠给这家由 Linux 基金会支持的机构。此次将 Agent Skills 移交 AAIF，走的是同一条路径：Anthropic 于 2025 年 12 月首次把 Agent Skills 称为“开放标准”，而 Simon Willison 当时就预测该规范会进入 AAIF。

**「影响」** 对实现或依赖 Agent Skills 的开发者来说，标准演进的控制权从单一厂商转交给一个多方基金会的治理流程，因此后续的规范制定和兼容性决策将不再由 Anthropic 单方面制定；但公告未给出过渡安排，现阶段无法判断现有实现的兼容性是否会受影响。

**标签**: `#AI agents`, `#open standards`, `#Anthropic`, `#Linux Foundation`, `#Model Context Protocol`

---

<a id="item-tech-news-10"></a>
### [KeePassXC 2.8.0 发布，迁移 Qt6 并支持 Wayland 自动输入](https://lwn.net/Articles/1102270/) ⭐️ 7.0/10

KeePassXC 2.8.0 已发布，核心变化包括从 Qt5 迁移到 Qt6、在 Linux 上支持 Wayland Auto-Type，以及可配置键盘快捷键。该版本还加入通过外部工具进行远程数据库同步、macOS 上的密码快速解锁和 Linux 上基于 Polkit 的快速解锁。它同时是项目首次提供 Windows 原生 ARM64 构建，并附带实验性的 Linux AArch64 AppImage；官方公告称新版本还包含多项安全更新，完整列表见更新日志。

rss · LWN.net · 10月22日 13:34

**「版本背景」** KeePassXC 2.8 系列并非一步到位：项目于 2026 年 9 月 23 日先发布 2.8.0 Beta 1，当时公布的主要特性与本次一致，包括 Qt5 到 Qt6 的迁移、Wayland 下的 Auto-Type、可配置快捷键、借助外部工具进行远程数据库同步，以及 macOS 密码快速解锁和 Linux 上的 Polkit 快速解锁。此次 2.8.0 是在 Beta 发布约一个月后推出的该系列首个稳定版本。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://keepassxc.org/blog/2026-10-21-2.8.0-released/">KeePassXC 2.8.0 (Stable) released</a></li>
<li><a href="https://keepassxc.org/blog/2026-09-23-2.8.0-beta1-released/">KeePassXC 2.8.0 (Beta 1) released</a></li>

</ul>
</details>

**标签**: `#open source`, `#password management`, `#security`, `#Linux`, `#software release`

---

<a id="item-tech-news-11"></a>
### [研究：部分智能电视关闭 ACR 后仍上传观看数据](https://watchingthewatchers.github.io/watchingthewatchers/index.html) ⭐️ 7.0/10

Watching the Watchers 的一项实测研究对 10 家厂商的 12 台美国智能电视进行了 5,943 次受控实验，发现部分机型在用户关闭自动内容识别（ACR）后仍会发送与观看内容相关的流量。研究称，VIDAA OS 的数据通过明文 MQTT 传输，包含不可重置的设备 ID 和音频指纹；Vizio 的 WatchFree+ 则把节目名写入未加密的域名查询，且用户无法关闭。对测试涉及的机型而言，仅关闭 ACR 开关不足以阻止这些观看相关数据外传。

telegram · zaihuapd · 10月22日 09:50

**「背景」** ACR（自动内容识别）是智能电视用来判断用户正在观看什么内容的技术：电视会截取屏幕画面或录制音频片段，再将其发送到远程服务器进行匹配。由于这套机制运行在系统层，设置中的“关闭”开关是否真正停止采集和上传，取决于厂商的具体实现，这也正是此类实测研究要验证的问题。

**「影响」** 对受影响的 VIDAA 和 Vizio 用户而言，电视设置中的 ACR 开关不能作为停止观看数据外传的保证：前者在关闭后仍发送含不可重置设备 ID 和音频指纹的明文 MQTT 数据，后者把节目名暴露在无法关闭的未加密 DNS 查询中。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://trashbox.ru/link/2026-10-22-otkaz-ot-slezhki-ne-srabotal-televizory-samsung-i-vizio-prodolzhili-otpravlyat-d">Смарт-телевизоры Samsung и Vizio продолжают отправлять...</a></li>

</ul>
</details>

**标签**: `#智能电视`, `#ACR`, `#隐私安全`, `#IoT`, `#明文传输`

---

<a id="item-tech-news-12"></a>
### [米哈游与清华开源 GameScaling 键鼠操作模型](https://arxiv.org/abs/2610.28698v1) ⭐️ 7.0/10

米哈游崩坏 AI 团队与清华大学等合作者发布并开源 GameScaling：一套基于 Qwen3.5 视觉语言模型继续预训练的游戏键鼠操作模型，参数规模覆盖 0.8B 至 27B，每次预测未来 200 毫秒的键盘和鼠标动作。团队以 Apache-2.0 开放八个检查点和推理客户端，但未包含训练代码。论文称，用 120 组训练配置发现，数据量增加会提升同源游戏表现，数据多样性有助于迁移到相近游戏，但对差异较大的游戏提升有限。

telegram · zaihuapd · 10月22日 11:32

**「背景」** 视觉语言模型原本以图像加文本为输入、以文本为输出，要让这类模型直接操作游戏，就需要额外训练，把屏幕画面映射为键盘和鼠标动作。GameScaling 的做法是在 Qwen3.5 上做继续预训练，让模型每次预测未来 200 毫秒内的键鼠动作序列；这样一来，模型输出的是连续控制，而不是单帧指令，因此动作预测的时间跨度又会与模型规模、训练数据量和数据多样性相互影响。

**「对开发者的实际影响」** 开发者可用 Apache-2.0 检查点和推理客户端做逐帧推理：输入当前画面及短历史，输出 6 个 33 ms 动作步和整段鼠标位移、滚轮操作；但官方未开放训练代码，若要复现其继续预训练流程或迁移到自有游戏，需自行重建训练管线。论文报告的多样性收益主要限于相近游戏，跨类型迁移仍需单独验证。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://github.com/THUSI-Lab/GameScaling">GitHub - THUSI-Lab/GameScaling: Scaling in Games: Continued ...</a></li>

</ul>
</details>

**标签**: `#game AI`, `#vision-language models`, `#open source`, `#model scaling`, `#keyboard-mouse control`

---

<a id="item-tech-news-13"></a>
### [333 个 Tor 出口节点因 Ebury 后门被下线](https://kaba.cx/posts/20261020_Tor/) ⭐️ 7.0/10

一名 Tor 运营者扫描约 3000 个出口中继后发现，333 个（约 10%）被植入 Ebury 后门，可将 22 端口 SSH 连接劫持至 12 台拦截服务器以窃取凭据。这些节点于 10 月 4 日被标记为 BadExit，次日全部下线。攻击者据称今年 8 月已入侵相关服务器，并屏蔽部分端口以专门收集未加密邮件流量，但入侵途径尚无定论。上述细节来自单一运营者扫描和 Telegram 聚合帖，尚待独立验证。

telegram · zaihuapd · 10月22日 14:52

**「背景：Tor 出口中继与 BadExit 标记」** Tor 出口中继是客户端链路中的最后一跳，实际负责把流量发往目标服务，因此出口运营者能够观察甚至篡改未经加密的流量。Tor 目录管理机构可以对行为恶意的出口打上 BadExit 标记，客户端会据此避开这些节点。此次事件中，涉事节点正是通过被植入的 Ebury 后门，把 22 端口的 SSH 连接劫持到 12 台拦截服务器上。

**「对使用者的影响」** 这些节点被标记 BadExit 后，Tor 客户端会自动避开它们作为出口，因此相关中继虽仍在线但已不再承载出口流量。对使用者而言，8 月至 10 月初经 Tor 发起过 SSH 连接的人应视为凭据可能已泄露，需尽快更换密码或密钥；运营商也可据此检查自己的中继是否被列入 BadExit。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://kaba.cx/posts/20261020_Tor/">How I got over 300 Tor exit nodes removed - KABA</a></li>
<li><a href="https://support.torproject.org/relay-operators/">Relay Operators | Tor Project | Support</a></li>

</ul>
</details>

**标签**: `#Tor`, `#网络安全`, `#Ebury后门`, `#SSH凭据窃取`, `#出口节点`

---

<a id="item-tech-news-14"></a>
### [报告称中国国资融资购入禁运的英伟达 B300 服务器](https://theinference.org/article/china-s-state-money-bought-banned-nvidia-b300-servers-then-redacted-the-receipts) ⭐️ 7.0/10

据 The Inference 报道（消息经 Telegram 频道转发，相关说法未获独立核实），一家中国国资控股的半导体租赁集团为 AI 公司荣耀视图科技提供融资，购入 32 台搭载英伟达 B300 芯片的华硕服务器；这批服务器属于 700 余台服务器交易的一部分，总额超过 30 亿元人民币，计划部署于中国移动宁夏枢纽。B300 属于美国最严格的对华出口管制层级，对华基本禁运。相关备案在受到关注后被重新提交，硬件描述被抹去。英伟达表示正与代工伙伴共同调查，华硕则称遵守出口管制规定。

telegram · zaihuapd · 10月22日 15:22

**「背景」** B300 芯片受美国对华出口管制中最严格层级限制，目前基本处于禁运状态。此前在 2026 年 8 月，台湾检方已起诉 9 人，指其将 130 台搭载 B300 的 AI 服务器经印度尼西亚和日本转运至中国大陆，其中 74 台已交付中国买家、56 台在边境被查扣。

**「实际影响」** 据报道，Nvidia 已表示正联合代工伙伴调查此事，华硕则称遵守出口管制；这意味着涉事的华硕服务器与 B300 芯片流向将成为供应商合规审查的焦点，而非仅是媒体报道层面的争议。对参与该笔交易的中资租赁方与中国移动宁夏枢纽而言，重新提交的备案文件删去了硬件描述，使监管机构与出资方难以核实设备是否属于受控物项，相关 32 台服务器乃至 700 余台交易中其余部分的交付、验收和上电部署都可能因此被推迟或追加审查。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://geniustechlab.com/posts/2026-08-26-nvidia-supermicro-b300-smuggling-taiwan-china-export-controls-2026">Taiwan Indicts 9: The Nvidia B300 Server Smuggling Case That ...</a></li>

</ul>
</details>

**标签**: `#Nvidia B300`, `#export controls`, `#AI hardware`, `#China`, `#semiconductor supply chain`

---

## 科技博客

<a id="item-tech-blog-1"></a>
### [软件慢在设计，而非慢语言](https://seangoedecke.com/software-is-slow-because-of-bad-design-not-slow-languages/) ⭐️ 6.0/10

rss · Sean Goedecke · 10月23日 00:00

**「背景」** 近来不少人期待让 AI 把软件重写成 C 或 Rust 来大幅提速。Sean Goedecke 认为这条路通常走不通：C 也许比 Python 快五十倍，但重写并不会带来五十倍加速。

**「方案」** 他的核心论据是，真实程序多为 I/O 密集型——一次 CRUD 请求可能有约一半时间花在数据库查询上，重写只能作用于剩余部分（即 Amdahl 定律），实际大概只有 1.5 倍提升。即便是明显的 CPU 密集工作，慢语言也往往已通过 cmark-gfm、NumPy 与 GPU 这类库把计算交给高度优化的 C 或汇编；tiktoken 的汇编重写虽在作者笔记本上约快 5 倍，但作者认为这更多来自去掉正则依赖的重设计，且分词只占推理时间的一小部分。Bryan Cantrill 曾试图把一段精心优化的 C 程序直译为 Rust，因借用检查器受阻后改用朴素写法，结果反而快 30%，原因是 Rust 默认的 B 树比二叉搜索树更缓存友好——即便在 CPU 密集场景，设计也压过语言。作者自己经历的显著提速几乎都来自让程序少做工作：缓存慢调用、把慢操作异步化或移出请求周期、并行化、合并 N+1 查询、换掉慢 SQL、跳过不必要的取数；而高级语言反而更容易一眼看出这些机会。

**「启示」** 因此，语言重写并不是严肃的优化手段；更有效的做法是让 AI 去剖析性能热点并重设计程序，只有在罕见的、无法再减少工作量的 CPU 热点上，才值得局部改写。

**标签**: `#performance-optimization`, `#software-design`, `#amdahls-law`, `#profiling`, `#io-bound`

---

## 财经新闻

<a id="item-finance-news-1"></a>
### [沪深 300 较 6 月高点回落 20%，A 股逼近熊市](https://www.bloomberg.com/news/articles/2026-10-22/china-stocks-set-for-bear-market-as-ai-trade-policy-hopes-fade) ⭐️ 8.0/10

10 月 22 日，沪深 300 指数盘中一度下跌 1.7%，较 6 月高点累计回落 20%，A 股逼近熊市；同日创业板指连续 16 个交易日下跌，恒生科技指数跌幅超过 4.5%。此轮下跌的背景是实质性财政刺激缺位和业绩不及预期，宁德时代季度利润增速低于预期后，周三股价大跌 12%；有策略师称，若无新政策或科技催化，这种震荡行情可能延续至 2027 年初。

telegram · zaihuapd · 10月22日 05:05

**「背景」** “熊市”通常指股指较近期高点下跌至少 20%；沪深 300 此次正是从 6 月高点回落并达到这一门槛。

**「受影响群体」** 冲击更集中在持有创业板、光模块等 AI 硬件股和宁德时代股票的投资者：这类高估值成长股对业绩不及预期更敏感，宁德时代利润增速低于预期后单日跌 12%，新易盛、中际旭创跌幅也居前。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.cnbc.com/2026/10/22/chinas-stock-market-csi-300-bear-market.html">China &#x27;s stock market : CSI 300 , bear market</a></li>

</ul>
</details>

**标签**: `#China A-shares`, `#CSI 300`, `#bear market`, `#Hang Seng Tech`, `#CATL earnings`

---