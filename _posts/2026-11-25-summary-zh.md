---
layout: default
title: "Horizon Summary: 2026-11-25 (ZH)"
date: 2026-11-25
lang: zh
---

> 从 34 条内容中筛选出 10 条重要资讯。

---

**科技新闻**
1. [Check Point 管理服务器遭入侵：V8 随机数状态被重建](#item-tech-news-1) ⭐️ 8.0/10
2. [Anthropic 称 Claude 发现 VP≠VNP 并发布 Lean 4 证明](#item-tech-news-2) ⭐️ 8.0/10
3. [Ternary Bonsai 2.5 27B：三元量化模型本地测速引讨论](#item-tech-news-3) ⭐️ 7.0/10
4. [Quad9 因法国法律限制停用法国 DNS 服务](#item-tech-news-4) ⭐️ 7.0/10
5. [Brendan Gregg 方法讨论：确定性 VM 与剖析局限](#item-tech-news-5) ⭐️ 7.0/10
6. [Simon Willison 复盘十二个月内 LLM 的三个能力拐点](#item-tech-news-6) ⭐️ 7.0/10
7. [百度开源文心 5.5 Flash Preview：280B MoE、Apache 2.0](#item-tech-news-7) ⭐️ 7.0/10
8. [诺华 CEO：AI 十年内难治愈癌症，研发周期或缩短 4 年](#item-tech-news-8) ⭐️ 7.0/10
9. [Broadcom 修复 VMware 23 个漏洞，含 vCenter vmdir 9.8 分免鉴权绕过](#item-tech-news-9) ⭐️ 7.0/10

**科技博客**
1. [旋转即可借用：跨 LLM 的事实回忆表征迁移](#item-tech-blog-1) ⭐️ 9.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [Check Point 管理服务器遭入侵：V8 随机数状态被重建](https://www.greynoise.io/blog/check-point-security-management-servers-intrusion-campaign) ⭐️ 8.0/10

GreyNoise 报告了一起针对 Check Point 安全管理服务器的活跃入侵活动。按其描述，攻击者反复请求 HFS 的 loginSrp1 端点，收集会话 Cookie 中由 JavaScript Math.random\(\) 生成的 sid，据此重建 Node.js V8 PRNG 的内部状态，恢复 HFS 会话 Cookie 的签名密钥，并伪造管理员会话 Cookie。评论中引用的时间线称扫描和利用始于 2026-10-02 13:17:45 UTC；CVE-2026-16232 被评论者视为可能的初始入口，但所给材料没有确认这一归因，也没有说明受影响的服务器是否都暴露在互联网上。

hackernews · louiereederson · 11月24日 16:32 · [社区讨论](https://news.ycombinator.com/item?id=50630594)

**「背景」** 此前 Rapid7 在 2026 年 7 月 28 日发布的技术分析已将 CVE-2026-16232 归因为 Check Point SmartConsole 登录流程中的认证绕过，影响 Security Management Server 与 Multi-Domain Security Management Server（MDS）。另有报道称，该攻击链还涉及 Rejetto HFS 的 CVE-2026-61500：攻击者反复请求 loginSrp1 端点，收集足够的会话 ID 输出以重建 V8 PRNG 内部状态，进而恢复会话 Cookie 签名密钥并伪造管理员会话。

**「处置影响」** 对运行相关 HFS 的 Check Point 管理服务器，攻击者取得签名密钥后可伪造管理员会话，因此处置时需要轮换会话签名密钥并排查异常管理员会话，不能只清理已观察到的扫描流量。

**「社区讨论」** 评论中，20after4 主张应让 Math.random 等随机数生成器默认安全，而不是要求大量应用各自正确使用；omh 则追问初始访问路径，并推测 CVE-2026-16232 可能是入口，但这意味着相关管理服务器曾可从互联网访问。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://daily.dev/posts/cyberattack-campaign-compromising-check-point-servers-across-22-organizations-h69zools2">Cyberattack campaign compromising Check Point servers...</a></li>
<li><a href="https://www.rapid7.com/blog/post/ra-check-point-smartconsole-authentication-bypass-technical-analysis-cve-2026-16232/">Check Point SmartConsole Authentication Bypass Technical ...</a></li>

</ul>
</details>

**标签**: `#security`, `#vulnerabilities`, `#exploit-techniques`, `#threat-intelligence`, `#check-point`

---

<a id="item-tech-news-2"></a>
### [Anthropic 称 Claude 发现 VP≠VNP 并发布 Lean 4 证明](https://github.com/anthropics/formal-math/blob/main/vp-vnp/README.md) ⭐️ 8.0/10

Anthropic 于 11 月 24 日公开论文《VP ≠ VNP over every field》及 Lean 4 形式化证明，称结果由内部研究用 Claude 模型发现，论文与代码均由 AI 撰写。论文给出哈密顿圈多项式的超多项式算术电路下界，据此推出 VP 是 VNP 的真子类；若成立，将解决 Valiant 1979 年的代数复杂度猜想，但不涉及 P 与 NP。团队称已通过三条标准公理审计和独立内核 nanoda 复核，除预留文件外无 sorry；但尚无人类数学家通读，Lean 无法确认形式化陈述与所声称命题一致，附录 Q 仍列出出入，结果有待独立审阅。

telegram · zaihuapd · 11月24日 06:02

**「背景」** Valiant 在 1979 年提出的猜想断言代数复杂度类 VP 是 VNP 的真子集，常被看作 P≠NP 的代数类比；有向哈密顿圈多项式在投影归约下是 VNP 完全的，因此若能证明计算该多项式需要超多项式大小的算术电路，就可推出 VP≠VNP（tool-2-1、tool-2-3）。Anthropic 此前公开过用 AI 智能体形式化已知数学的工作：Horizon 2026 年 9 月 5 日日报曾报道，其团队用 Lean 完成费马大定理的形式化证明，代码库约含 1300 万行 Lean 代码和 2.95 万个中间定理（tool-1-3）。这次的不同点是，Anthropic 声称 Claude 得到的是一项新的数学结果，而不只是把已有证明交给证明助手检查。

**「对研究者的实际影响」** 对代数复杂度研究者而言，目前的实际工作是先核对 Lean 4 形式化中的定理陈述是否确实表达 Valiant 1979 年猜想所要求的 VP 与 VNP 分离，并逐条检查附录 Q 列出的出入。Lean 内核只能保证证明与所形式化的陈述一致，无法保证该陈述就是论文所声称的命题，因此在完成这一比对前，该结果还不能作为已被证明的下界引用。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.anthropic.com/research/formalizing-fermats-last-theorem">2026-09-05 — Anthropic 智能体用 Lean 形式化费马大定理</a></li>
<li><a href="https://mathworld.wolfram.com/ValiantsConjecture.html">Valiant&#x27;s Conjecture -- from Wolfram MathWorld</a></li>
<li><a href="https://blog.computationalcomplexity.org/2026/11/vp-vnp.html">Computational Complexity: VP ≠ VNP</a></li>
<li><a href="https://interestingengineering.com/ai-robotics/claude-proves-vp-not-vnp-valiant-conjecture">Claude claims to prove VP VNP in Valiant&#x27;s 47-year-old conjecture</a></li>

</ul>
</details>

**标签**: `#代数复杂度`, `#Lean 4`, `#形式化验证`, `#AI 科研`, `#Anthropic`

---

<a id="item-tech-news-3"></a>
### [Ternary Bonsai 2.5 27B：三元量化模型本地测速引讨论](https://prismml.com/news/bonsai-2-5-27b) ⭐️ 7.0/10

Ternary Bonsai 2.5 27B 是一款三元量化的 27B 本地模型，讨论焦点是它在 Apple Silicon 上的推理速度和长上下文代理式编程潜力。Hacker News 用户报告，在 24GB 内存的 Mac Mini M5 Pro 上以 Q2 GGUF 运行时可达到约 22–25 tok/s，并能轻松容纳 128k 上下文；这些是个人测速，不是厂商基准或独立复现。另有评论称其 SWE-bench Verified 表现接近 Opus 4.6，但该说法未经验证，评论者也对基准代表性提出保留。

hackernews · b0m · 11月24日 20:08 · [社区讨论](https://news.ycombinator.com/item?id=50633922)

**「背景」** 据 PrismML 的模型文档，Ternary Bonsai 2.5 27B 基于 Qwen3.8-27B 构建、架构未改，是 Bonsai 系列中面向长序列工具调用、真实代码库编码和多步任务的 27B 语言模型。三值量化用三个离散权重取值来压缩模型；PrismML 表示 2.5 27B 仍保持 5.9GB 的模型占用。

**「实际影响」** 对 24GB 统一内存的 Apple Silicon 用户而言，Q2 GGUF 量化版可在常驻 128k 上下文的同时维持约 22 tok/s 的生成速度（社区在 Mac Mini M5 Pro 上的单机实测），使本地批量 agentic 编码具备实际可行性。但同一用户的长任务自测显示，Bonsai 2.5 与上一版同样只通过 8 项中的 5 项，改进体现在步数减少 17%、耗时减少 29%，说明提速并不等于可靠性提升，部署时仍需对输出做人工校验。另有评论者追问，除 FPGA 之外是否存在对 ternary 权重的原生硬件加速；若没有，当前速度优势可能主要来自反量化后的通用内核，而这一点尚缺官方说明。

**「社区讨论」** 评论者分享了自建长程任务基准：Bonsai 2.5 与 Bonsai 2 都通过 8 项中的 5 项，但步骤减少 17%、耗时减少 29%。同时有人要求补充与同尺寸 Qwen 等小模型的直接对比，并追问除 FPGA 外是否存在三元权重的硬件加速。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://docs.prismml.com/models/bonsai-2-5-27b">Ternary Bonsai 2.5 27B - Bonsai - docs.prismml.com</a></li>
<li><a href="https://prismml.com/news/bonsai-2-5-27b">PrismML — Introducing Ternary Bonsai 2.5 27B: Powering ...</a></li>

</ul>
</details>

**标签**: `#ternary quantization`, `#local LLMs`, `#agentic coding`, `#GGUF`, `#Apple Silicon`

---

<a id="item-tech-news-4"></a>
### [Quad9 因法国法律限制停用法国 DNS 服务](https://quad9.net/news/blog/quad9-service-deactivation-in-france/) ⭐️ 7.0/10

Quad9 已将其 DNS 服务从法国撤下，理由是其所述的法国法律约束。一名评论者称，自 2026 年 11 月 24 日起，向 9.9.9.9 发起的查询会返回 REFUSED，并附带 EDE 18（Prohibited）及“Service unavailable due to French legal constraints”说明。现有材料未给出所涉法律的具体条款或服务恢复时间。

hackernews · farrokhi · 11月24日 08:33 · [社区讨论](https://news.ycombinator.com/item?id=50625384)

**「背景」** Horizon 10 月 6 日的日报曾报道，Quad9 拒绝执行法国法院针对盗版体育直播的域名封锁令，beIN Sports 请求法院按 58 个域名每日最高 58 万欧元处罚。10 月 23 日的日报随后报道，Quad9 计划在 11 月 24 日后退出法国，其首席技术官表示可能用 geoIP 过滤阻止法国用户访问，并承认这与其“无法按域名选择性封锁”的立场存在冲突。

**「影响」** 在法国依赖 Quad9 作为上游解析器的用户需要改用其他 DNS 服务或转发代理，否则相关查询会被拒绝；有评论者报告，其 AdGuard Home 因无法连接上游而导致局域网断网。

**「社区讨论」** 一位评论者搭建了支持 DoH、DoT 和 Do53（UDP/TCP，IPv4/IPv6）的开放 Quad9 转发代理，供法国用户作为近似替代方案；另一位用户则报告其 AdGuard Home 因上游不可用而出现断网。这些是社区提供的临时方案和个别体验，并非 Quad9 官方支持。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://quad9.net/news/blog/au-revoir-france/">2026-10-23 — Quad9 因 DNS 封锁争议拟退出法国</a></li>
<li><a href="https://torrentfreak.com/dns-resolver-quad9-rejects-french-piracy-blocks-weighs-exit-as-bein-seeks-up-to-e580k-a-day/">2026-10-06 — Quad9 拒绝法国 DNS 封锁令，或面临每日 58 万欧元罚款</a></li>

</ul>
</details>

**标签**: `#DNS`, `#internet privacy`, `#internet governance`, `#France`, `#Quad9`

---

<a id="item-tech-news-5"></a>
### [Brendan Gregg 方法讨论：确定性 VM 与剖析局限](https://fzakaria.com/2026/11/12/worshipping-at-the-altar-of-brendan-gregg) ⭐️ 7.0/10

一篇在 Hacker News 上被链接的评论文章以 Brendan Gregg 的性能分析方法为切入点，讨论确定性 VM、flamegraph 和异步工作负载剖析。由于原文正文未提供，现有信息主要来自评论：有人提到该 VM 为单线程，担心它难以准确分析高吞吐多线程管线；也有人认为 flamegraph 无法清楚呈现跨线程依赖。讨论还涉及该方案与 rr 记录回放的异同，以及 C++ 协程、fiber、future 等异步代码的临界路径定位问题。

hackernews · kqr · 11月24日 10:50 · [社区讨论](https://news.ycombinator.com/item?id=50626413)

**「背景」** 这篇随笔把 Brendan Gregg 作为性能分析方法的参照点；作者 Farid Zakaria 在文中说，他把欣赏多年的想法用在一个确定性虚拟机上，做出 Rewind，使每次运行都可被记录，并在事后精确分析。确定性虚拟机的基本特点是相同输入下执行可重复，这正是回放式性能分析赖以成立的前提。

**「异步工作负载的可观测性」** 对于使用 C++ 协程、fiber 或 future 的异步服务，有评论者认为，这类确定性 VM 和火焰图分析无法直接给出跨线程、跨任务的 critical path；如果不在框架层嵌入 request context 等关联信息，后续任务就很难归因到同一请求。因此，团队在采用此类 profiling 方案前，应把应用层追踪改造计入成本，而不能假定录制回放会自动还原异步依赖。

**「社区讨论」** 有评论者肯定确定性 VM 的思路，但质疑单线程设计能否代表高吞吐多线程管线，并认为 flamegraph 难以呈现跨线程依赖；还有人将其与 rr 记录回放作比较。异步工作负载方面，读者指出若不修改框架、嵌入请求上下文，协程、fiber 或 future 的临界路径很难定位。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://fzakaria.com/2026/11/12/worshipping-at-the-altar-of-brendan-gregg">Worshipping at the altar of Brendan Gregg - fzakaria.com</a></li>

</ul>
</details>

**标签**: `#performance analysis`, `#flamegraphs`, `#deterministic execution`, `#profiling`, `#async concurrency`

---

<a id="item-tech-news-6"></a>
### [Simon Willison 复盘十二个月内 LLM 的三个能力拐点](https://simonwillison.net/2026/Nov/24/llm-inflection-points/) ⭐️ 7.0/10

Simon Willison 在 AI Engineer Code Summit 主题演讲后的文章里提出，过去十二个月 LLM 与编码智能体出现了三个能力拐点；他的依据是个人日常使用体验，而非基准测试。第一个拐点在 2025 年 11 月：Claude Opus 4.5（11 月 24 日发布，文章写作时恰为一周年）与同期 OpenAI 的 GPT-5.1-Codex、GPT-5.1-Codex-Max，让 Claude Code 和 Codex 首次在他多数日常编码任务上默认给出正确结果；此前他因需频繁纠正而未把 Claude Code 当作主力。第二个拐点在 2026 年 6—7 月的“Fable 类”模型：他把“给定目标并提供工具就能靠蛮力解决”的模型归入此类，名单包括 Claude Fable 5/5.1/5.2、被他称作“便宜版 Fable”的 Opus 5.5、GPT-6 Astra，Gemini 4 Neon 可能也算；其中 Fable 5 是 4 月因网络安全能力过强而未发布的 Mythos 的去危险化版本，6 月发布三天后受出口管制下架，7 月 1 日才恢复。第三个拐点在 2026 年 9—10 月的 3D 建模与游戏开发：9 月 22 日发布的 Opus 5.5 响应“让游戏有趣得多”的指令，自动试玩并重做平衡 12 小时，把他的一款即时战略游戏从乏味改到可玩。文章在“Fable 5.2 是否也是拐点”一节处截断，未能看到作者对该问题的结论。

rss · Simon Willison · 11月24日 23:02

**「背景」** 这篇文章的时间线前提是 Claude Code 的成熟过程：Anthropic 于 2025 年 2 月 24 日随 Claude 3.7 Sonnet 一同发布 Claude Code，因此到 2025 年 11 月 24 日 Opus 4.5 上线时，它只有约九个月大；作者称在此之前的默认表现需要频繁纠正，不足以当作日常主力。Horizon 2026 年 3 月 28 日的日报显示，Opus 4.5 后来成为衡量编码能力的参照：智谱开源的 GLM-5.1 在 SWE-bench-Verified 上取得 77.8 分，被描述为已接近 Claude Opus 4.5 的水平。

**「对使用者的影响」** 按他的判断，评估编码智能体的标准已从“补全是否正确”转向“拿到目标和工具后能否自主搭建所需手段”：他举例说，Fable 在修 Safari 显示问题时自行拉起 pyobjc-framework-Quartz 截图机制和带 CORS 的本地日志服务器，又在最近一次实验里用五个 WebAudio 麦克风把房间中的神秘蜂鸣定位到约 40 厘米范围内。这些都是单一用户的轶事记录，没有基准分数或可复现数据支撑，读者难以据此直接比较模型。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://i.redd.it/ewzmimtzmlrg1.png">2026-03-28 — GLM-5.1 launches with coding performance matching Claude Opus 4.5</a></li>

</ul>
</details>

**标签**: `#LLM`, `#coding agents`, `#AI engineering`, `#model releases`, `#industry analysis`

---

<a id="item-tech-news-7"></a>
### [百度开源文心 5.5 Flash Preview：280B MoE、Apache 2.0](https://x.com/Baidu_Inc/status/2125077484442190137) ⭐️ 7.0/10

百度 11 月 24 日通过官方 X 账号宣布开源文心 5.5 Flash Preview，模型权重以 Apache 2.0 协议在 Hugging Face 和 ModelScope 上开放，可用 vLLM 或 SGLang 部署与微调。模型采用 MoE 架构，总参数 280B，每 token 激活 14B，上下文窗口为 1M token，是首个基于 ERNIE 5.5 Flash Base 训练的后训练模型。流传的基准图表显示其 Terminal-Bench 4.0 得 46.5 分、DeepSWE v1.1 得 71.2 分，但百度未说明这些数字是否经过第三方独立验证。名为 Preview 的版本定位与未经验证的跑分意味着，目前可确认的是权重、许可证与部署路径，性能表现仍待独立复现。

telegram · zaihuapd · 11月24日 07:32

**「背景：文心 5.5 Flash 基座先行开源」** 文心 5.5 Flash Base 基座模型此前已经先行开源：据 11 月 7 日的 Horizon 日报，该模型采用 MoE 架构，总参数 2800 亿、每个 token 激活 140 亿，预训练使用 33.5 万亿 token，预训练上下文为 128K，微调和推理阶段支持最长 100 万 token；但当时的报道未披露许可证条款、权重获取方式和基准成绩，因此无法判断其可用范围。此次发布的 Preview 正是基于该 Base 训练的首个后训练模型，并补充了 Apache 2.0 许可、Hugging Face 与 ModelScope 权重开放，以及 vLLM 和 SGLang 部署等此前缺失的信息。

**「影响」** 对希望自建推理服务的团队而言，Apache 2.0 允许商用与修改，但 280B 总参数意味着即使每 token 仅激活 14B，部署仍需按完整权重规划显存与多卡并行，并需依赖 vLLM 或 SGLang 而非任意推理栈；在把官方流传的基准分数用于选型前，应先在自身负载上复现。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.news.cn/info/20261105/f3bbdb6854f5441ca9fb34062f213875/c.html">2026-11-07 — 百度开源文心 5.5 Flash Base：2800 亿参数 MoE、支持百万级上下文</a></li>

</ul>
</details>

**标签**: `#open-source AI`, `#LLM`, `#Baidu ERNIE`, `#Mixture-of-Experts`, `#Apache 2.0`

---

<a id="item-tech-news-8"></a>
### [诺华 CEO：AI 十年内难治愈癌症，研发周期或缩短 4 年](https://www.ft.com/content/1e5a9d70-221d-461d-ae03-dc235b1db340) ⭐️ 7.0/10

诺华 CEO 万思瀚（同时担任 Anthropic 董事）表示，AI 在 5 到 10 年内不会治愈癌症；即便只是把平均 12 年的药物研发周期压缩到 8 年，也大约需要十年。他把最明确的提速放在人体试验前的早期发现阶段：这一阶段通常耗时 4 年，最多可缩短 2 年；同时预计进入人体试验的成功率从 8% 提高到 12%，但动物实验和临床试验无法跳过。这一判断与 Anthropic CEO 所称癌症等疾病将在十年内成为“历史遗迹”相左，礼来 CEO 也公开表示怀疑。

telegram · zaihuapd · 11月24日 08:54

**「研发流程背景」** 药物研发分为人体试验前的早期发现和随后的人体临床试验；后者用于验证安全性与有效性，不能仅靠计算模拟跳过。诺华 CEO 的判断正基于这一流程差异：AI 主要作用于早期发现，而整体周期和最终成功率仍受临床试验制约。

**「实际影响」** 对 AI 制药团队和投资者而言，诺华给出的可验证收益集中在临床前发现：4 年阶段最多节省 2 年，并将人体试验成功率预期从 8% 提到 12%；评估 AI 价值时因此应看这些环节的实际节省，而不能把动物实验和临床试验视为可跳过。

**标签**: `#AI drug discovery`, `#pharma R&amp;D`, `#healthcare AI`, `#AI limitations`, `#industry commentary`

---

<a id="item-tech-news-9"></a>
### [Broadcom 修复 VMware 23 个漏洞，含 vCenter vmdir 9.8 分免鉴权绕过](https://thehackernews.com/2026/11/vmware-vcenter-hit-by-another-critical.html) ⭐️ 7.0/10

Broadcom 为 VMware 产品线发布补丁，共修复 23 个漏洞，其中包括 vCenter 目录服务（vmdir）中的鉴权绕过漏洞 CVE-2026-123903，CVSS 评分 9.8。据报，攻击者只要能访问 vCenter，就可在不提供凭据的情况下绕过认证并进入系统，属于免鉴权漏洞。The Hacker News 的报道称，该漏洞在补丁发布前几天已被作为零日漏洞利用。由于提供的仅为简讯摘要，受影响的具体版本范围、利用细节和缓解措施尚未明确。

telegram · zaihuapd · 11月24日 14:50

**「背景」** vmdir 是 vCenter 内置的目录服务，vCenter 的单点登录与身份认证都构建在它之上；因此一旦该服务存在鉴权绕过，只要能访问 vCenter，就可能绕过认证直接进入系统。Broadcom 在 2026 年 11 月 24 日的 VMSA-2026-0011 公告中将 CVE-2026-123903 评为 CVSS 9.8，并明确说明没有可用的临时缓解措施，只有修复版本。

**「影响」** 对运维者最直接的后果是：vCenter 管理接口能否被网络访问，本身就构成了唯一的攻击门槛——在完成修补之前，任何可路由到 vCenter 的地址都应视为可被直接绕过认证进入，应依靠网络隔离和访问控制收窄暴露面，而不能指望登录凭据挡住攻击。这次修复批次覆盖 ESX、vCenter、Workstation、Fusion 和 Avi Load Balancer 上的 23 个漏洞，同批其他组件也需一并升级；但需注意公开漏洞库页面标注“暂无已知利用”，与消息中“几天前刚被零日利用”的说法相互矛盾，实际在野利用情况仍不确定。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://brandefense.io/knowledge-hub/vulnerabilities/cve-2026-123903/">CVE-2026-123903: vCenter Auth Bypass, Fix Status</a></li>
<li><a href="https://sn1persecurity.com/wordpress/cve-2026-123903-vmware-vcenter-auth-bypass-detection-with-sn1per/">CVE-2026-123903: vCenter Auth Bypass, Patch Again | Sn1per</a></li>
<li><a href="https://vulners.com/cve/CVE-2026-123903">CVE-2026-123903 - vulnerability database | Vulners.com</a></li>
<li><a href="https://thehackernews.com/2026/11/vmware-vcenter-hit-by-another-critical.html">VMware vCenter Hit by Another Critical 9.8-Rated Auth Bypass ...</a></li>
<li><a href="https://securityonline.info/cve-watchtower/cve-2026-123903/">CVE-2026-123903: VMware vCenter, CVSS 9.8</a></li>

</ul>
</details>

**标签**: `#security`, `#vmware`, `#vulnerability`, `#zero-day`, `#enterprise-infrastructure`

---

## 科技博客

<a id="item-tech-blog-1"></a>
### [旋转即可借用：跨 LLM 的事实回忆表征迁移](https://hazyresearch.stanford.edu/blog/2026-11-24-platos-key) ⭐️ 9.0/10

rss · Stanford Hazy Research Blog · 11月24日 07:00

**「背景」** 柏拉图表示假说认为，独立训练的神经网络会收敛到关于现实的共享表征；既有研究已发现模型间表征在几何上相似，但相似并不等于可以互换。作者由此追问：不做任何梯度下降，一个 LLM 能否直接把另一个 LLM 的隐状态拿来用？

**「方案」** 作者把事实回忆看作键值查找：早中层为 subject（如“France”）构造键，后层据此从权重中取回值（“Paris”），因此只替换最后一个 subject token 处的键，让接收模型用自己的后续层生成答案。跨模型映射仅为一个闭式拟合的旋转加上一个全局缩放——中心化供体键、用薄 SVD 求解正交 Procrustes 旋转，再按接收方整体尺度缩放并加回其均值。在 12 个 1.5B–27B 基础模型（8 个家族）、20 个模型对和按 subject 划分的 8,800 条事实上，迁移准确率中位数为 41%，相当于自替换 55% 的 73%，随机或打乱旋转等对照不超过 2.2%，岭回归、白化旋转和 MLP 也仅在 7% 的对比中显著更优。反直觉的是，按 mKNN 相似度选层只有 4.5%，按迁移准确率选层则为 44%。链式旋转达到直接映射的 99%，每模型仅保留 256 个主成分仍有 74%；在 2,600 个漏答中 56% 属于“暗记忆”，旋转后的供体键无需更新权重即找回 18%，对照不超过 1.1%。作者也承认局限：目前仅限基础模型与事实回忆，绝对迁移幅度有限，暗记忆恢复只是概念验证。

**「启示」** 这些结果表明，独立训练的 LLM 之间不只是表征相似，而是部分可互换；事实回忆失败可能源于检索键不佳而非知识缺失，并指向共享的低维几何与潜空间通信。

**标签**: `#mechanistic interpretability`, `#representation alignment`, `#cross-model transfer`, `#factual recall`, `#orthogonal Procrustes`

---