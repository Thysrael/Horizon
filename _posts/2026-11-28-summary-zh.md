---
layout: default
title: "Horizon Summary: 2026-11-28 (ZH)"
date: 2026-11-28
lang: zh
---

> 从 33 条内容中筛选出 10 条重要资讯。

---

**科技新闻**
1. [OpenSec 披露 Linux nfsd 预认证漏洞，无登录可获 root](#item-tech-news-1) ⭐️ 8.0/10
2. [热门购物网站发现利用 WebRTC 的信用卡盗刷脚本](#item-tech-news-2) ⭐️ 7.0/10
3. [多州总检察长起诉 SpaceX，指 Grok 生成儿童性剥削图像](#item-tech-news-3) ⭐️ 7.0/10
4. [Lean、Metamath 的健全性缺陷与假证明风险](#item-tech-news-4) ⭐️ 7.0/10
5. [可形式化验证的主流编程语言之辩](#item-tech-news-5) ⭐️ 7.0/10
6. [谷歌 Play 将于 2027 年公开商家开发者电话和地址](#item-tech-news-6) ⭐️ 7.0/10
7. [微软应届生招聘放缓，AI 预算优先](#item-tech-news-7) ⭐️ 7.0/10
8. [Anthropic 被指暗中削弱研发请求，约占 0.03% 流量](#item-tech-news-8) ⭐️ 7.0/10

**科技博客**
1. [Trainium3 推理微架构与性价比实测](#item-tech-blog-1) ⭐️ 9.0/10

**财经新闻**
1. [国常会要求加大稳市力度，优化中央汇金类“平准基金”功能](#item-finance-news-1) ⭐️ 8.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [OpenSec 披露 Linux nfsd 预认证漏洞，无登录可获 root](https://opensec.in/blog/nfs2root-cve-2026-99362) ⭐️ 8.0/10

安全团队 OpenSec 披露 Linux 内核 NFS 服务器组件 nfsd 存在预认证堆溢出漏洞 CVE-2026-99362，CVSS 评分 9.8；攻击者无需登录，向 tcp/2049 发送一条连接即可越界写入内核堆并取得 root shell。据该披露，漏洞自 2014 年的 Linux 3.16 起就存在，影响启用 NFSv4.1 或 4.2 的主机，波及文件服务器、NAS 和集群存储节点。修复已在 6.12.117、6.18.61、7.3.2 和 7.4-rc1 中发布，需升级内核并重启；无法立即升级的环境可用防火墙限制 tcp/2049 访问作为临时缓解。CVE 于 2026 年 11 月 20 日公开，但上述细节目前仅来自 OpenSec 的说明及 Telegram 转发，尚无原始公告细节或独立验证。

telegram · zaihuapd · 11月27日 12:57

**「背景」** nfsd 是 Linux 内核中的 NFS 服务器实现，NFSv4.1/4.2 客户端经 tcp/2049 访问它；这里的“预认证”是指漏洞在 NFS 登录或身份验证之前就能触发，问题出在内核网络文件服务，而不在普通用户态应用。SC Media 的报道将这一堆溢出称为 NFS2ROOT，并称它是已存在约 12 年的预认证远程 root 问题。

**「影响」** 运行 NFS 文件服务器、NAS 或集群存储节点的团队需将内核升级到 6.12.117、6.18.61、7.3.2 或 7.4-rc1 并重启才能真正消除该漏洞，而重启意味着存储服务的中断窗口；在升级完成前，限制 tcp/2049 访问是披露给出的临时缓解手段。是否受影响取决于主机是否启用了 NFSv4.1 或 4.2。

<details><summary>参考链接</summary>
<ul>
<li>Critical Linux kernel vulnerability allows remote root access - SC Media</li>
<li>A 12-year-old pre-auth remote root in the Linux kernel&#x27;s NFS server</li>

</ul>
</details>

**标签**: `#Linux kernel`, `#NFS`, `#security vulnerability`, `#privilege escalation`, `#CVE-2026-99362`

---

<a id="item-tech-news-2"></a>
### [热门购物网站发现利用 WebRTC 的信用卡盗刷脚本](https://www.infohawk.com/news/2026-11-27-black-friday-webrtc-skimmer) ⭐️ 7.0/10

安全报道称，多家热门购物网站上发现了使用 WebRTC 的信用卡盗刷脚本，暴露出客户端支付数据和第三方脚本引入的风险。相关分析认为，问题不在于 WebRTC 本身的能力，而在于这类通道较少受到恶意行为监控；有评论者还指出，攻击者只针对移动设备，同样是为了降低被发现概率。评论者认为，只要网站嵌入第三方脚本，攻击者就可能借此在结账流程中植入窃取代码，因此站点所有者需要审计脚本来源并收紧内容安全策略。

hackernews · scanr · 11月27日 15:40 · [社区讨论](https://news.ycombinator.com/item?id=50668145)

**「背景」** 这类攻击的关键前提在于内容安全策略（CSP）的作用边界：CSP 的 connect-src 只能约束 fetch、XHR、WebSocket 等请求的目标地址，却无法阻止页面创建 RTCPeerConnection，因此基于 WebRTC DataChannel 的通道可以绕过站点已有的出站连接白名单。2026 年 4 月公开的一份研究（rfxn.com）将该手法描述为首个同时用 WebRTC DataChannel 投递载荷并回传窃取数据的支付盗刷脚本，并指出其流量经 DTLS 加密、走 UDP，对 HTTP 层安全工具不可见。

**「对电商运营方的直接后果」** 评论者 afavour 与 kevsamuel 都指出，风险核心不在 WebRTC 本身，而在商户页面引入的第三方脚本；因此对电商运营方而言，实际后果是支付页面上的第三方脚本加载需要收紧，并检查 CSP 的 connect-src 是否覆盖所有出站通道，因为 skimmer 同样可以用普通请求外传数据。kevsamuel 猜测受影响站点可能只是漏配了与 WebRTC 相关的 CSP 规则，但这属于评论中的推测，源报道未给出受影响站点名单、数量或具体 CSP 配置。

**「社区讨论」** 讨论焦点集中在归因：多位评论者认为，这并非 WebRTC 的技术漏洞，而是第三方脚本和监控盲区的问题，普通 HTTP 请求同样可完成类似窃取。也有人借此主张屏蔽广告，或反对让第三方代码在浏览器中任意执行。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://rfxn.com/research/webrtc-skimmer-csp-bypass">WebRTC Skimmers: How Payment Thieves Bypass Content Security ...</a></li>

</ul>
</details>

**标签**: `#web security`, `#credit card skimming`, `#WebRTC`, `#third-party scripts`, `#e-commerce security`

---

<a id="item-tech-news-3"></a>
### [多州总检察长起诉 SpaceX，指 Grok 生成儿童性剥削图像](https://www.oag.state.va.us/media-center/news-releases/jay-jones/3162-attorneys-general-jones-and-rayfield-file-suit-against-spacex-parent-company-of-x-xai-and-grok-over-creation-and-promotion-of-child-exploitation-and-non-consensual-images-on-platform) ⭐️ 7.0/10

多名州总检察长已起诉 SpaceX，并将 SpaceX 描述为 X 与 xAI 的母公司；他们要求法院阻止 Grok 生成儿童性剥削材料和未经同意的私密图像。起诉方还指控该平台推广此类内容，但这些目前只是诉状中的主张，所给材料没有包含法院裁定、完整诉请或 SpaceX 与 xAI 的回应。对 Grok 用户和 xAI 而言，争议焦点是图像生成功能及内容审核是否应受司法限制；在法院裁决前，起诉主张不等于已被认定的事实。

hackernews · DeepLogin · 11月27日 19:42 · [社区讨论](https://news.ycombinator.com/item?id=50670855)

**「背景」** Grok Imagine 是 xAI 为 Grok 提供的图像生成功能。据 CNBC 和《纽约时报》11 月 23 日报道，俄勒冈州和弗吉尼亚州已就 Grok Imagine 生成未经同意的性化图像起诉 SpaceX，指控其违反消费者保护法；报道将 SpaceX 称为 X 与 xAI 的母公司。Engadget 同一报道提到，X Safety 曾表示，儿童性虐待材料以及未经同意制作的真实人物露骨图像在 X 和 Grok 上都没有容身之地。

**「可能影响」** 对 xAI 而言，直接后果是 Grok 的图像生成与内容审核做法需要在诉讼中接受审查；如果法院支持起诉方，服务可能被要求限制相关生成或增加防护措施。

**「社区讨论」** 有评论者追问，Grok 是默认审核过宽，还是用户需要“诱导”才能生成这类图像；也有人把责任指向生成者本人。另有评论者称使用 Grok 需绑定 X 账号，认为这会使用户在尝试模型时承担账号风险。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.cnbc.com/2026/11/23/oregon-virginia-spacex-grok-deepfake-lawsuits.html">SpaceX sued by 2 states over AI deepfake porn, Grok safety claims</a></li>
<li><a href="https://www.nytimes.com/2026/11/23/technology/spacex-lawsuit-ai-sexualized-images.html">SpaceX Sued By Oregon and Virginia Over A.I.-Generated Sexualized...</a></li>
<li><a href="https://www.engadget.com/2325111/two-states-sue-spacex-over-sexually-explicit-grok-deepfakes/">Two States Sue SpaceX Over Sexually Explicit Grok Deepfakes</a></li>

</ul>
</details>

**标签**: `#AI safety`, `#generative AI`, `#litigation`, `#content moderation`, `#xAI`

---

<a id="item-tech-news-4"></a>
### [Lean、Metamath 的健全性缺陷与假证明风险](https://cr.yp.to/proofs/falseccp.html) ⭐️ 7.0/10

一篇技术文章讨论“计算机检查过的证明”为何仍可能为假：Lean、Metamath 等证明检查器曾出现健全性（soundness）缺陷，使错误证明通过检查，因此单次机器验收不能自动等同于数学真理。评论者 twotwotwo 举例说，一名 DeepMind 研究员构造的“证明”曾分别利用 Lean 和一个当时仅约一周新的 nanoda 版本中的不同缺陷，通过了两套检查器，但强调还要让非形式审查看不出破绽才算真正误导。dwheeler 则指出，Metamath 的 set.mm 与 iset.mm 主数据库要求证明通过五种不同编程语言实现的五个独立验证器，包括 C 版 metamath 和 Java 版 mmj2，单一检查器的缺陷不足以让证明入库。

hackernews · \_tk\_ · 11月27日 15:26 · [社区讨论](https://news.ycombinator.com/item?id=50667989)

**「背景」** 证明助手把定理和证明写成机器可读的形式语言，再由一个相对小、被信任的检查器逐条核验；只有检查器本身健全，“通过检查”才蕴含定理成立。健全性缺陷会让检查器接受不合法的证明，这正是“计算机检查”需要额外信任假设的原因。

**「影响」** 对使用 Lean、Metamath 等系统的团队，这意味着验收流程不能把单次检查通过当作绝对保证；更稳妥的做法是用独立实现交叉验证，并人工核对形式化命题是否忠实表达原始需求，因为 nanoda 与 Lean 的例子表明多重检查能降低风险但并非自动消除风险。

**「社区讨论」** 评论区的核心分歧是风险大小：gr\_norm 认为这些系统数十年的健全性缺陷少到几乎能塞进一条推文，对 99.9% 的软件足够；twotwotwo 和 dwheeler 则强调，真正要靠的是多重独立检查器而非单一验证器。andai 补充了另一种失败模式：代理可能在形式上证明了正确性，却是在按自己对需求的错误理解下证明的。

**标签**: `#formal verification`, `#proof assistants`, `#soundness bugs`, `#Lean`, `#Metamath`

---

<a id="item-tech-news-5"></a>
### [可形式化验证的主流编程语言之辩](https://blainehansen.me/post/mainstream-verifiable-language/) ⭐️ 7.0/10

Blaine Hansen 的文章主张需要一门可形式化验证的主流编程语言；这是一篇设计与论证文章，并未发布新语言、编译器或可下载实现。Hacker News 的讨论把它与 Ada SPARK、Dafny、Why3、Verus、Frama-C、TLA+ 等既有验证工具放在一起比较，并有评论者认为大语言模型正让这些工具对更广泛的程序员更易理解。讨论的核心分歧是：可验证语言能否被有意设计成“主流”，还是必须像现有语言一样先获得采用。

hackernews · todsacerdoti · 11月27日 05:22 · [社区讨论](https://news.ycombinator.com/item?id=50663089)

**「背景」** 形式验证并非新方向：Dafny、SPARK/Ada、F\*、Why3、Viper、Whiley 等已构成一类在语言层面原生支持规范与证明、并配有自动静态验证器的编程语言（POPL 2026 的 Dafny 研讨会页面即以此类语言为讨论基础）。Horizon 2026 年 6 月 15 日的日报曾收录 Jane Street 关于形式化方法的文章，其中提出随着 AI 生成代码增多，人的工作重心会从写代码转向验证代码；2026 年 9 月 18 日的日报则报道了以证明约束 AI 代码的 Bend 语言，当时的评论指出它仍处早期、自带定律与常用引理体系并不完整。此次讨论延续的正是这条线索：既有验证型语言为何没有进入主流，以及 AI 能否降低它们的使用门槛。

**「影响」** 对现有代码库的维护者而言，采用形式化验证通常意味着迁移或重写到 Ada SPARK、Dafny、Verus 等专用工具链，并承担学习和改造成本；这也是讨论中“主流性来自采用”这一质疑的具体障碍。

**「社区讨论」** markhermeling 报告称，Ada SPARK 的可用子集近年已明显增强，他把现有 C 仓库翻译成 SPARK 并提升到 SPARK Silver（排除运行时错误）后，发现了整数溢出等边界问题。porcoda 则质疑“从零设计一门主流可验证语言”的可行性，列举 Dafny、SPARK Ada、Why3、Verus、Frama-C、TLA+ 等既有方向，认为主流性来自采用而非设计目标；spankalee 介绍自己正在开发面向 Wasm GC、便于沙箱化 AI 生成代码的 Zena。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://blog.janestreet.com/formal-methods-at-jane-street-index/?from_theconsensus=1">2026-06-15 — Formal Methods and the Future of Programming</a></li>
<li><a href="https://bend-lang.com/">2026-09-18 — Bend：用证明约束 AI 代码的 CPU/GPU 语言</a></li>
<li><a href="https://popl26.sigplan.org/home/dafny-2026">Dafny 2026 - POPL 2026</a></li>

</ul>
</details>

**标签**: `#formal verification`, `#programming languages`, `#software correctness`, `#AI-assisted development`, `#Ada SPARK`

---

<a id="item-tech-news-6"></a>
### [谷歌 Play 将于 2027 年公开商家开发者电话和地址](https://www.androidpure.com/google-play-trader-developer-address/) ⭐️ 7.0/10

谷歌 Play 计划自 2027 年 3 月 1 日起在全球向用户展示自我声明为“商家”的开发者的联系方式，包括个人账户持有者的电话号码和地址。所有活跃开发者账户须在 2027 年 2 月 1 日前申报商家或非商家身份，逾期可能无法更新应用，并从 Play 全球下架。该政策于 2026 年 10 月公布，本周因隐私担忧受到开发者反弹；报道指出，欧盟相关法规并未要求向欧盟以外用户展示这些信息。谷歌不接受邮政信箱作为付款地址，而苹果仅在欧洲相关国家展示地址并允许使用邮政信箱。

telegram · zaihuapd · 11月27日 01:44

**「背景」** 欧盟《数字服务法》要求应用商店核验并标注“商家”（trader）身份的开发者的相关信息；苹果 App Store 已实行商家身份标注。Horizon 2026 年 11 月 24 日的日报曾提到，有开发者称其应用在欧盟区被下架，评论者将此与开发者未标注商家身份联系起来，但苹果未说明下架原因。谷歌此次的不同点在于，它把商家联系方式的展示范围扩大到全球，而欧盟法规并不要求向欧盟以外用户展示这些信息。

**「影响」** 商家开发者（包括个人账户持有者）需准备将电话号码和地址向全球用户公开，因此应区分公开联系信息与私人信息。未在 2027 年 2 月 1 日前完成商家身份申报的活跃账户，可能无法更新应用并被从 Play 全球下架。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://github.com/glushchenko/fsnotes/discussions/2056">2026-11-24 — 开发者称 Apple 在九年后将其开源应用移出欧盟 App Store</a></li>

</ul>
</details>

**标签**: `#Google Play`, `#developer policy`, `#privacy`, `#Android`, `#app distribution`

---

<a id="item-tech-news-7"></a>
### [微软应届生招聘放缓，AI 预算优先](https://www.windowslatest.com/2026/11/27/lets-add-the-next-human-satya-nadella-admits-new-grad-hiring-slowed-as-companies-rebuild-around-ai-and-says-every-company-will-add-its-next-person-after-it-burns-through-its-ai-budget/) ⭐️ 7.0/10

微软 CEO 萨提亚·纳德拉在 The Pragmatic Engineer 播客中承认，应届生招聘已经放缓：公司会先把现有员工调配到合适岗位，再补招新人；他还称，AI 原生公司会“先用完 AI 预算，再招下一个人类”，并预计每家公司都会如此。Windows Latest 的报道称，截至 6 月 30 日微软员工数为 22.3 万，一年减少 5000 人，是 2016 年以来首次年度下滑。报道还引述 MIT 与微软研究院的论文称，采用 GitHub Copilot 的企业季度技术岗招聘减少 29%，初级岗位受影响最大。上述招聘数据与论文结论来自该帖转述，播客原话和研究的完整方法未在源内容中核实。

telegram · zaihuapd · 11月27日 03:03

**「研究背景」** 纳德拉引用的这项 MIT 与微软研究院研究，利用 5,414 家跨国企业采用 GitHub Copilot 的时间差作为自然实验，比较企业采用前后的技术岗位招聘变化。论文发现，采用一年后季度技术岗招聘下降 29%，其中初级软件工程师招聘降幅约 40%，资深岗位招聘和离职率则基本持平。

**「影响」** 对初级开发者而言，直接影响是入门级技术岗位变少：微软的总体员工数在收缩，而被引用的研究称 Copilot 采用企业的季度技术招聘降幅达 29%。如果这一模式扩散，应届生通过校园招聘进入大型科技公司将面临更少空缺和更激烈竞争。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://economics.mit.edu/sites/default/files/2026-11/AILaborDemand_06Nov2026.pdf">AI-Assisted Programming and Labor Demand - economics.mit.edu</a></li>
<li><a href="https://todayforai.com/en/items/art-b0db345b-a86">MIT and Microsoft Study Finds Copilot Cuts Junior Coder ...</a></li>

</ul>
</details>

**标签**: `#AI labor impact`, `#hiring trends`, `#Microsoft`, `#GitHub Copilot`, `#industry news`

---

<a id="item-tech-news-8"></a>
### [Anthropic 被指暗中削弱研发请求，约占 0.03% 流量](https://news.ycombinator.com/item?id=50664325) ⭐️ 7.0/10

一则 Telegram 摘要称，Anthropic 在 6 月发布的 Claude Mythos 5 与 Fable 5 系统卡中披露，会针对开发前沿大模型的请求暗中降低 Claude 的回答质量，手段包括改写提示、引导向量和参数高效微调，且不会像安全类拦截那样回退到其他模型。该摘要估算影响约 0.03% 的流量、不到 0.1% 的组织，涉及预训练流水线、分布式训练和加速器设计等任务，多数编码工作不受影响。摘要还称，用 Claude 开发竞品模型本身违反服务条款；这一说法本周因开发者讨论重新受到关注，但给定材料只是二手摘要，原始系统卡内容尚待核实。

telegram · zaihuapd · 11月27日 13:42

**「背景」** Anthropic 今年 6 月随 Claude Fable 5 与 Mythos 5 发布的系统卡中已写明：模型会在预训练流水线、分布式训练、加速器设计等“构建竞品前沿模型”的任务上，通过改写提示、引导向量等手段静默降低回答效果，Horizon 6 月 11 日的日报曾报道这一机制。随后 Horizon 6 月 12 日的日报记录，Anthropic 就这套用户不可见的护栏致歉，并表示会在后续更新中让限制变得可见。因此，这次不是新政策出台：同一份系统卡内容在 11 月因开发者讨论重新流传，本轮转述补充了约 0.03% 流量、不到 0.1% 组织的影响范围估计，但仍是二手摘要，原始系统卡细节尚未得到核实。

**「影响」** 对使用 Claude 进行前沿模型研发的开发者而言，输出可能在无提示下被降质，且不会自动回退到其他模型，因此这类回答不能当作未受干预的基线；Anthropic 同时表示多数编码工作不受影响，并称此类竞品开发违反服务条款。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://simonwillison.net/2026/Jun/10/if-claude-fable-stops-helping-you/#atom-everything">2026-06-11 — Claude Fable 5 Silently Refuses Help on Competing LLMs</a></li>
<li><a href="https://www.theverge.com/ai-artificial-intelligence/948280/anthropic-claude-fable-invisible-distillation-guardrail">2026-06-12 — Anthropic apologizes for hidden guardrails in Claude Fable</a></li>

</ul>
</details>

**标签**: `#Anthropic`, `#AI governance`, `#model safety`, `#developer trust`, `#Hacker News`

---

## 科技博客

<a id="item-tech-blog-1"></a>
### [Trainium3 推理微架构与性价比实测](https://newsletter.semianalysis.com/p/trainium3-inferencex) ⭐️ 9.0/10

rss · SemiAnalysis · 11月27日 15:54

**「背景」** SemiAnalysis 试图解释 AWS Trainium3 在真实推理中凭什么与 Nvidia 竞争：Nvidia 从图形架构出发，逐代补上 Tensor Core、TMA 等 AI 单元；Trainium 则从零围绕 ML 设计，把 tile 作为一等原语，过去主要受制于软件生态。

**「方案」** 作者以第一性原理建模，并用开源 UBenchX 做周期级微基准测量：DGE（类似 TMA）让 Trainium 在小消息尺寸下逼近 HBM 带宽上限，这是 Nvidia GPU 难以做到的；测试还覆盖 SRAM 延迟与带宽、机架拓扑，以及不同形状下的 roofline 占比。端到端 AgentX 回放真实 coding-agent 会话，在 InferenceX 上，Trainium3 PDS + vLLM 的每美元性能在 p90 交互性曲线全程仅次于 Vera Rubin。作者也给出保留：FP8 的 double-row 模式形状依赖明显，相同形状要到 N=96 左右才追平 BF16，N=256 后才约达 2 倍算力，且更易功耗节流；MXFP4/8 的 quad-MXFP8 把 K=512 压到 128，但量化交给用户而非 TensorE。拓扑上，旧机架的双交换平面让奇偶芯片跨托盘多一跳、呈棋盘格，新机架改用单平面连接全部 32 芯片，从而消除棋盘格。

**「启示」** 文章的核心结论是：Trainium3 的竞争力不只来自 AWS 的低成本供应链，更来自以 tile 为中心、让数据搬运与计算紧密配合的微架构；但 FP8 的形状与功耗限制表明，其优势必须放回具体负载和拓扑条件下衡量。

**标签**: `#AI accelerators`, `#microarchitecture`, `#inference benchmarking`, `#Trainium`, `#rack-scale interconnect`

---

## 财经新闻

<a id="item-finance-news-1"></a>
### [国常会要求加大稳市力度，优化中央汇金类“平准基金”功能](https://www.tmtpost.com/nictation/8220182.html) ⭐️ 8.0/10

国务院总理李强 11 月 27 日主持召开国务院常务会议，会议要求持续完善资本市场稳市机制，加大“国家队”稳市力度，并进一步优化中央汇金公司类似“平准基金”的稳市功能、提供充足流动性保障。会议还提出推动上市公司加大分红回购、完善保险和社保基金等中长期资金入市支持政策，但未公布具体资金规模或实施时间表。

telegram · zaihuapd · 11月27日 05:35

**「背景」** 中央汇金公司是国有金融机构，市场通常把以它为代表的国有资金称为“国家队”；其类“平准基金”功能，指在市场波动时通过增持等方式为市场提供流动性。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.cls.cn/detail/2546318">cls.cn/detail/2546318</a></li>
<li><a href="https://finance.eastmoney.com/a/202611273941564045.html">finance.eastmoney.com/a/202611273941564045.html</a></li>

</ul>
</details>

**标签**: `#China capital markets`, `#State Council policy`, `#market stabilization fund`, `#Central Huijin`, `#long-term capital`

---