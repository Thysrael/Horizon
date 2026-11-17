---
layout: default
title: "Horizon Summary: 2026-11-17 (ZH)"
date: 2026-11-17
lang: zh
---

> 从 45 条内容中筛选出 14 条重要资讯。

---

**科技新闻**
1. [vLLM v0.34.0 发布：默认启用可扩展 KV 缓存，移除 Model Runner V1](#item-tech-news-1) ⭐️ 8.0/10
2. [Jiff 1.0 发布：Rust 日期时间库首个稳定版](#item-tech-news-2) ⭐️ 8.0/10
3. [阿里发布 Qwen4-Max：2.4 万亿参数稀疏 MoE](#item-tech-news-3) ⭐️ 8.0/10
4. [美国将 AI 芯片服务器出口管制扩至远程访问](#item-tech-news-4) ⭐️ 8.0/10
5. [CMU 推出 CS Learn 免费课程讲座](#item-tech-news-5) ⭐️ 7.0/10
6. [微软称大规模邮件中断由 7 月修复引入的缺陷引发](#item-tech-news-6) ⭐️ 7.0/10
7. [Linux 拟新增 futex PING：以非公平窃取和代理执行提速](#item-tech-news-7) ⭐️ 7.0/10
8. [腾讯混元发布 Hy4 flash，主打低成本日常任务](#item-tech-news-8) ⭐️ 7.0/10
9. [美国与九国签署《旧金山宣言》共保 AI 供应链](#item-tech-news-9) ⭐️ 7.0/10
10. [亚马逊：AI 代理借 Artex 框架窃取 API 密钥并自我供血](#item-tech-news-10) ⭐️ 7.0/10

**科技博客**
1. [Instacart 用 LLM 改造搜索查询理解](#item-tech-blog-1) ⭐️ 7.0/10
2. [cuPotential：用可组合原语加速 OpenMM 分子动力学](#item-tech-blog-2) ⭐️ 5.0/10

**财经新闻**
1. [中国 10 月经济放缓加剧：消费、工业产出与投资均不及预期](#item-finance-news-1) ⭐️ 8.0/10
2. [中美俄领导人将于 11 月 19 日在深圳 APEC 场边举行首次三方会晤](#item-finance-news-2) ⭐️ 8.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [vLLM v0.34.0 发布：默认启用可扩展 KV 缓存，移除 Model Runner V1](https://github.com/vllm-project/vllm/releases/tag/v0.34.0) ⭐️ 8.0/10

vLLM v0.34.0 已发布，包含来自 412 位贡献者（其中 120 位为新贡献者）的 1,061 个提交，新增 10 个模型，并将可扩展 KV 缓存设为默认。该机制在 CUDA 图捕获和预热完成之后，按实际空闲显存决定 KV 缓存大小；官方举例称，MiniMax-M3 在 H200 上从 433k token 提升到 672k token，因此吞吐更高，高并发下的 TTFT 更低。Model Runner V1 已被移除，Model Runner V2 成为唯一的 GPU runner；官方称在 Blackwell 和 MI355X 上取得最高 1.95 倍解码、1.6 倍输出吞吐以及 1.24–1.40 倍长提示 TTFT 的提升。升级前需注意：默认 --block-size 从 16 改为 64，ROCm 只提供 10.0 的镜像与 wheel，并要求 huggingface\_hub &gt;= 2.0.0。

github · khluu · 11月16日 23:22

**「背景：Model Runner V2 从默认走向唯一实现」** Model Runner 是 vLLM 在 GPU 上执行模型前向、采样和 CUDA graph 的核心执行路径。据 2026 年 9 月 10 日的日报，vLLM v0.29.0 已将 Model Runner V2（MRV2）设为所有模型的默认执行路径，仅少量 ROCm 模型仍保留 V1；v0.34.0 则彻底移除 V1，使 MRV2 成为唯一的 GPU runner。因此，仍依赖 VLLM\_USE\_V2\_MODEL\_RUNNER=0 或自定义 V1 logits processor 的部署需要在升级前完成迁移。

**「升级影响」** 升级会破坏部分现有配置：设置 VLLM\_USE\_V2\_MODEL\_RUNNER=0 现在会在启动时直接失败，V1 的 logits processor 需要迁移到 vllm.v1.worker.gpu.sample.logits\_processor。启用新的缓存策略后，部分模型在 H200、并发 128 时单 token 解码延迟（TPOT）可能上升 6–18%；可通过 --gpu-memory-utilization 0.9 或 --no-enable-extensible-kv-cache 关闭该策略，若想保留旧的分块行为则需显式传入 --block-size 16。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://github.com/vllm-project/vllm/releases/tag/v0.29.0">2026-09-10 — vLLM 0.29.0 默认启用 Model Runner V2</a></li>

</ul>
</details>

**标签**: `#vLLM`, `#LLM inference`, `#KV cache`, `#model serving`, `#release notes`

---

<a id="item-tech-news-2"></a>
### [Jiff 1.0 发布：Rust 日期时间库首个稳定版](https://burntsushi.net/jiff/) ⭐️ 8.0/10

Jiff 1.0 已发布，这是 Andrew Gallant（burntsushi）为 Rust 编写的日期时间库的首个稳定版本，面向需要处理时间、时区和夏令时的 Rust 开发者。该项目强调显式处理时区与 DST，并在文档中提及 TAI 时间尺度；但现有材料未给出 1.0 的具体 API 变更、兼容范围或独立基准结果。社区讨论主要围绕时间 API 设计，以及 chrono 等现有 Rust 日期时间库的不足。

hackernews · burntsushi · 11月16日 16:53 · [社区讨论](https://news.ycombinator.com/item?id=50519744)

**「背景」** 在 Jiff 之前，chrono 长期是 Rust 生态中常用的日期时间库，但其 API 设计一直是讨论焦点。Jiff 由 burntsushi 开发，1.0 的发布意味着该项目进入稳定版本阶段。

**「影响」** 对 Rust 开发者而言，Jiff 1.0 提供了一个可评估替代 chrono 的稳定选项，尤其适用于重视显式时区和 DST 语义的项目；采用前仍应确认自身用例不在项目明确不适用的范围内，并单独验证与现有代码和生态的兼容性。

**「社区讨论」** 曾维护 chrono 约五年的 quodlibetor 表示，他想改进它的 API，但用户对稳定性的需求使每次改动都遭遇阻力，最终因倦怠停止维护，并对 Jiff 表示认可。另有评论者赞赏项目明确说明“并非总是适用”，也有人询问 Jiff 对 TAI、UT1 等时间尺度以及从微秒到十亿年量级的支持。

**标签**: `#Rust`, `#datetime libraries`, `#timezones`, `#API design`, `#open source`

---

<a id="item-tech-news-3"></a>
### [阿里发布 Qwen4-Max：2.4 万亿参数稀疏 MoE](https://mp.weixin.qq.com/s/pJUt0xwD6H-WMyzd8TjZaQ) ⭐️ 8.0/10

阿里通义千问正式上线旗舰模型 Qwen4-Max，采用总参数 2.4 万亿的稀疏 MoE 架构，原生支持视觉理解与 100 万 Token 长上下文，并称其在编程、办公及长程任务上表现突出。发布信息称，其前端编程能力在 Code Arena 盲测中位居全球前列，但未给出具体分数或完整基准结果。相比上代，Qwen4-Max 的单个任务平均费用从 26.58 元降至 11.16 元，降幅近 58%，Token 消耗也减少近 50%，API 定价同步下调。团队还表示后续将推出规模更小的 Qwen4 系列模型并公开权重，这属于计划中的开放安排，尚未交付。

telegram · zaihuapd · 11月16日 02:52

**「背景」** Horizon 5 月 21 日的日报曾报道，阿里通义千问发布主打智能体任务的 Qwen3.7-Max，并称其在非幻觉表现和长程任务上取得进展。此次 Qwen4-Max 是该 Max 旗舰序列的下一代产品，官方给出的单任务平均费用对比对象即为上一代模型。

**「对开发者的影响」** 开发者现在可通过 QwenCloud 的 Token Plan 和 API 调用 Qwen4-Max，同时也能在 QwenWork、QwenStudio 等阿里平台使用，其中隐式缓存命中的输入价格为每百万 Token 0.075 美元。对以单个任务成本为主要考量的编程、办公和长文档处理负载而言，官方所称单任务费用下降近 58% 仍需按实际调用验证：第三方评测 Artificial Analysis 指出该模型单任务速度偏慢且输出冗长，而输出长度会直接影响实际 token 支出与降本幅度。计划私有化部署的团队目前还无法行动，因为更小的 Qwen4 系列仅被承诺后续开源，权重尚未发布。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://qwen.ai/blog?id=qwen3.7">2026-05-21 — Qwen3.7-Max: The Agent Frontier Model</a></li>
<li><a href="https://www.alibabacloud.com/blog/alibaba-unveils-qwen4-max-new-ai-teammate-for-work-creativity-and-discovery_603783">Alibaba Unveils Qwen 4 - Max : New AI... - Alibaba Cloud Community</a></li>
<li><a href="https://artificialanalysis.ai/models/qwen4-max">Qwen 4 Max - Intelligence, Performance &amp; Price ... | Artificial Analysis</a></li>

</ul>
</details>

**标签**: `#LLM`, `#Qwen`, `#mixture-of-experts`, `#Alibaba`, `#model-release`

---

<a id="item-tech-news-4"></a>
### [美国将 AI 芯片服务器出口管制扩至远程访问](https://www.reuters.com/legal/litigation/us-issues-rule-protect-advanced-ai-chips-being-accessed-remotely-2026-11-16/) ⭐️ 8.0/10

美国商务部 11 月 16 日发布临时最终规则，把先进 AI 芯片与服务器的出口管制延伸到远程访问，影响通过第三国数据中心远程使用相关芯片的境外用户及再出口商。规则旨在堵住绕道第三国数据中心规避限制的路径，由财政部和国家安全委员会主导起草，并可能进一步收紧中国获取先进芯片的渠道。据《The Verge》报道，新规还要求向印度尼西亚、马来西亚、新加坡、泰国和巴西再出口 AI 芯片须申请许可。

telegram · zaihuapd · 11月16日 14:44

**「背景」** 美国此前已对先进 AI 芯片的对华直接销售实施严格许可限制；Horizon 5 月 22 日的日报曾援引黄仁勋称，英伟达因这些限制实际上已放弃中国 AI 芯片市场。直接出口受阻后，通过第三国数据中心远程调用算力成为绕开管制的路径，这也是本次临时最终规则把远程访问纳入出口管制的原因。

**「合规影响」** 对印尼、马来西亚、新加坡、泰国和巴西的数据中心及云服务商而言，再出口先进 AI 芯片或服务器现在需要申请许可；通过远程方式向受限方提供算力的运营商也需将此类访问纳入出口管制合规审查，第三国数据中心作为中转的路径不再当然合规。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.cnbc.com/2026/05/21/nvidia-jensen-huang-china-ai-chip-market-huawei.html">2026-05-22 — Nvidia CEO: Nvidia Has Essentially Abandoned China AI Chip Market</a></li>

</ul>
</details>

**标签**: `#AI chips`, `#export controls`, `#semiconductor policy`, `#cloud access`, `#US-China tech`

---

<a id="item-tech-news-5"></a>
### [CMU 推出 CS Learn 免费课程讲座](https://www.cs.cmu.edu/learn/) ⭐️ 7.0/10

卡内基梅隆大学推出 CS Learn，在 YouTube 上免费发布该校当前计算机科学课程的完整学期讲座，本周每天首播一门，并计划在明年 1 月增加更多课程。该项目由 Griffin 计算机科学学院的 Phillip Compeau 负责，部分学生开发了自动化制作工具，使小团队也能完成大量视频制作。

hackernews · pcompeau · 11月16日 20:43 · [社区讨论](https://news.ycombinator.com/item?id=50522980)

**「开放课程材料的先例」** MIT 于 2001 年 4 月宣布 OpenCourseWare 计划，2002 年 9 月 30 日开放试点站点，首批上线 16 个学术院系和斯隆管理学院的 32 门课程材料，免费公开供任何人使用。CMU 的 CS Learn 负责人 Phillip Compeau 在讨论中也直言“MIT 25 年前就做到了”，说明此次发布延续的是同一类开放课程材料公开做法，差别在于 CMU 提供的是当前课程的整学期讲座视频，而不只是课程材料。

**「影响」** 对自学者而言，现在可以直接观看这些讲座，但讨论中提到配套课程材料（courseware）将随后推出；在项目和反馈机制到位前，学习效果仍取决于学习者能否自行找到练习与评估方式。

**「社区讨论」** 评论者 ecshafer 认为，只有讲座而没有项目和反馈机制，课程效果会打折扣，并指出公开课常只发布入门课而缺少研究生级别的编译器等进阶课程。CMU 校友 fwx 对 Tianqi Chen 的 ML Systems 课程上线表示欢迎，并请求增加分布式系统、操作系统等课程；JSR\_FDED 则认为在 AI 时代学好基础知识仍能让 AI 成为助力。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://en.wikipedia.org/wiki/MIT_OpenCourseWare">MIT OpenCourseWare - Wikipedia</a></li>
<li><a href="https://news.mit.edu/2002/ocw">OpenCourseWare makes its debut - MIT News</a></li>

</ul>
</details>

**标签**: `#computer-science-education`, `#online-learning`, `#CMU`, `#AI-education`, `#YouTube`

---

<a id="item-tech-news-6"></a>
### [微软称大规模邮件中断由 7 月修复引入的缺陷引发](https://www.theregister.com/saas/2026/11/16/microsoft-blames-monster-email-outage-on-software-defect-introduced-in-july-fix/5310026) ⭐️ 7.0/10

据 The Register 报道，微软将一次大规模电子邮件服务中断归因于 7 月一次修复所引入的软件缺陷，这是事后复盘披露的核心结论。提供的材料没有说明受影响用户数量、具体服务组件或恢复时间，因此中断的完整范围仍不清楚。

hackernews · Bender · 11月16日 13:18 · [社区讨论](https://news.ycombinator.com/item?id=50517321)

**「背景」** 在微软给出归因之前，NPR 已报道 Outlook 从周四起发生大范围中断，持续超过 12 小时，数百万个人、组织和企业受影响，微软直到周五凌晨才报告取得有限进展。《纽约时报》同时报道，医院、学校、企业和华盛顿国会办公室均受波及，连微软员工也无法使用邮件。

**「影响范围」** 对使用 Exchange Online 的企业来说，邮件中断并非单一产品故障：依赖该服务的 Teams 日历、Copilot 以及微软自身的安全工具等共 19 项服务受到影响，Microsoft 365 Apps 管理中心的部分功能也不可用。故障期间，运维团队需要为邮件和日历准备替代通道，并预期相关 Copilot 功能一同降级。

**「社区讨论」** 评论者将此次恢复过程类比为电网的“黑启动”，并追问超大规模服务是否应主动按比例丢弃过载流量或封锁部分区域，而不是继续把请求转发到下游。另有评论质疑，用较低端的测试环境验证 7 月代码、直到生产环境才暴露并发缺陷是否是可接受的成本取舍；这些属于社区观点，并非报道确认的事实。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.npr.org/2026/11/12/nx-s1-6039343/outlook-down-widespread-outage-microsoft-email">A negative Outlook: Microsoft scrambles to fix email outage : NPR</a></li>
<li><a href="https://www.nytimes.com/2026/11/13/business/microsoft-outage.html">Inside Microsoft ’s Rush to Get Back Online After a Global Outage</a></li>
<li><a href="https://www.techradar.com/news/live/outlook-outage-nov-2026">Microsoft outage live — Outlook and Teams returning to... | TechRadar</a></li>
<li><a href="https://ppc.land/microsoft-365-email-outage-hits-19-services-from-outlook-to-copilot/">Microsoft 365 email outage hits 19 services, from Outlook to Copilot</a></li>
<li><a href="https://www.abc.net.au/news/2026-11-13/microsoft-outage-affects-users-worldwide/107381050">Microsoft outage hits users worldwide, affecting Teams, Outlook and...</a></li>

</ul>
</details>

**标签**: `#Microsoft`, `#email outage`, `#software reliability`, `#concurrency bugs`, `#production testing`

---

<a id="item-tech-news-7"></a>
### [Linux 拟新增 futex PING：以非公平窃取和代理执行提速](https://lwn.net/Articles/1102988/) ⭐️ 7.0/10

Suleiman Souhlal 提出为 Linux 增加第三类 futex——“futex PING”，定位为“下一代优先级继承”。该设计允许带等待者的 futex 被正在运行且缓存热的线程“窃取”，放弃 PI futex 的严格公平性；同时用代理执行（proxy execution）而非优先级继承来避免优先级反转，并在释放时优先唤醒捐赠者线程。目前这只是补丁提案，尚未合并；调度维护者 Peter Zijlstra 称其“为时过早”，并对部分锁定改动提出异议和替代方案。

rss · LWN.net · 11月16日 15:06

**「背景」** futex 是内核为用户态快速互斥量提供的支撑机制，其设计目标是尽量不进入内核；但普通 futex 可能出现优先级反转，即持有锁的低优先级线程拖慢高优先级线程，内核因此引入了优先级继承（PI）futex，把高优先级线程的优先级借给锁持有者直到其释放锁。代价是 PI futex 按排队顺序公平交接：锁释放后新持有者需被唤醒、经调度并真正上 CPU 才能持锁，这段时间锁处于无人持有的空档，新持有者缓存也往往是冷的，部分负载下吞吐损失明显。Horizon 2026 年 9 月 30 日的日报曾报道 PostgreSQL 性能开发者 Andres Freund 在 Kernel Recipes 大会上的演讲，其中提到 futex 提供的状态位不够用、PI futex 状态更少因而几乎不可用——本次提出的 futex PING 正是在这一性能与 PI 局限的背景下尝试用“可被抢占”的交接加代理执行来替代优先级继承。

**「影响」** 对内核与实时系统开发者而言，PING futex 目前尚不是可依赖的接口或生产特性；即便方向被接受，也需先解决锁定设计异议，并与把代理执行用于 PI futex 的并行工作协调，设计仍可能变化。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://lwn.net/Articles/1096827/">2026-09-30 — PostgreSQL 开发者谈 Linux 内核的助力与阻碍</a></li>

</ul>
</details>

**标签**: `#Linux kernel`, `#futexes`, `#priority inheritance`, `#concurrency`, `#performance`

---

<a id="item-tech-news-8"></a>
### [腾讯混元发布 Hy4 flash，主打低成本日常任务](https://mp.weixin.qq.com/s/5yBbf-ctYziM5r0i6Y17lA) ⭐️ 7.0/10

腾讯混元发布 Hy4 flash，这是一款总参数 224B、激活 12B 的多模态 MoE 模型，支持 1M 上下文。官方称其综合效果略优于 Hy4 preview，WorkIndex 单任务成本仅为 Hy4 preview 的 1/13、Hy4 的 1/20，但这些性能与成本对比均来自厂商说法。模型已在腾讯云 TokenHub、WorkBuddy 和元宝上线，并计划开源；API 定价为每百万 Token 输入 0.5 元、输出 2 元，命中缓存时为 0.02 元，11 月 30 日前 WorkBuddy 限免、API 5 折。

telegram · zaihuapd · 11月16日 07:17

**「前代 Hy4 preview 的定位」** 8 月 29 日的日报曾报道，腾讯发布 Hy4 preview，总参数 770B、激活 49B，上下文窗口 1M token，API 定价为每百万 token 输入 0.834 美元、输出 2.501 美元。此次 Hy4 flash 正以它为对比基准：官方称综合效果略优于 Hy4 preview，单任务成本约为后者的 1/13，参数量则缩减到 224B 总参数/12B 激活。8 月 30 日的日报还记录，Hy4 preview 当时已开源并在 OpenRouter 上线；而 Hy4 flash 目前只是计划开源。

**「影响」** 对高频调用 API 的开发者而言，这一价格档位可用于降低日常任务成本，但 11 月 30 日后的折扣与限免是否延续尚未说明。希望自行部署的团队也需等待其开源计划落地，目前可用的开源权重尚未发布。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://mp.weixin.qq.com/s/ymr3X878B8oa2XP15CH8TQ">2026-08-29 — 腾讯开源 Hy4 preview 发布，盲测小胜 GLM-5.3 与 Kimi K3</a></li>
<li><a href="https://www.tencent.com/tencent-releases-and-open-sources-tencent-hy4-preview/">2026-08-30 — 腾讯开源 Hy4 Preview 模型</a></li>

</ul>
</details>

**标签**: `#Tencent Hunyuan`, `#LLM release`, `#Mixture-of-Experts`, `#multimodal`, `#API pricing`

---

<a id="item-tech-news-9"></a>
### [美国与九国签署《旧金山宣言》共保 AI 供应链](https://www.state.gov/releases/office-of-the-spokesman/2026/11/the-san-francisco-declaration-on-the-secure-foundations-of-enduring-prosperity/) ⭐️ 7.0/10

11 月 15 日，美国与澳大利亚、印度、以色列、日本、韩国、卡塔尔、新加坡、阿联酋和英国签署《旧金山宣言》，确认经济安全是国家安全的基础，将共同保护支撑超级智能（SI）供应链的敏感技术与关键基础设施。宣言提出设立五个工作组，分别覆盖创新政策框架、SI 在关键领域的应用、SI 全栈供应链协作、安全港与供应链安全枢纽、SI 安全与韧性。这是一项政治宣言：转载内容未给出各工作组的牵头方、时间表、具体承诺或执行机制，也未界定“超级智能”的能力门槛。

telegram · zaihuapd · 11月16日 10:40

**「背景」** “全栈供应链”一般指从芯片与算力、云基础设施到模型训练及上层应用的各个层级；宣言将这条供应链与“敏感技术”“关键基础设施”并列为保护对象。宣言同时使用“超级智能（SI）”这一提法，但转载内容未给出其能力门槛或判定标准，具体范围仍需以官方文本为准。

**「影响」** 对在上述十国从事 AI 芯片、云算力或模型业务的企业来说，宣言本身没有列出可直接对照的新合规义务；实际影响取决于五个工作组是否产出出口管制、供应链审查或“安全港”之类的具体安排，这需要后续跟踪。

**标签**: `#AI供应链`, `#国际协议`, `#科技政策`, `#超级智能`, `#供应链安全`

---

<a id="item-tech-news-10"></a>
### [亚马逊：AI 代理借 Artex 框架窃取 API 密钥并自我供血](https://cybernews.com/security/amazon-autonomous-cybercrime-artex-framework/) ⭐️ 7.0/10

亚马逊称，攻击者利用开源渗透测试框架 Artex 驱动 AI 代理，从 LiteLLM、Dify 等公网暴露的 AI 应用中窃取 API 密钥，验证后汇入共享池，用于支付更多大模型调用。亚马逊表示该活动始于 10 月 3 日，并于 11 月 5 日被其诱饵网络 MadPot 截获阻断。亚马逊以中等信心将该行动归于中国相关威胁组织，并称并非所有被列目标都已失陷，已通知可能受影响的 AWS 客户。上述内容目前为亚马逊的单方面说法，尚未见独立验证，受影响规模与窃取密钥数量均未披露。

telegram · zaihuapd · 11月16日 13:00

**「背景」** LiteLLM 是统一访问多家大模型服务商的库与网关，Dify 是 LLM 应用开发平台，二者都会在配置中集中保存多个模型提供商的 API 密钥；一旦实例暴露在公网，这些凭据便成为集中目标。Horizon 10 月 22 日的日报曾报道，PyPI 上的 LiteLLM 1.107.0 被篡改，安装该版本会植入凭据窃取程序和后门；这与本次通过暴露应用窃取密钥的路径不同，前者是供应链投毒，后者是公网暴露，但指向同一类凭据集中风险。公开报道将 ARTEX 描述为开源的 AI 渗透测试框架，并指出亚马逊对攻击者使用该框架的判断为中等信心，被盗情况尚未得到独立验证。

**「暴露面与密钥风险」** 对将 LiteLLM、Dify 等 AI 应用或网关直接暴露在公网的组织，直接后果是其中保存的上游模型 API 密钥可能被窃取并汇入攻击者的共享池，用于支付更多模型调用，带来额外费用和配额消耗。亚马逊表示并非所有被列目标都已失陷，但可能受影响的 AWS 客户已收到通知；运营方应限制此类接口的公网访问、轮换密钥并审计异常调用。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://safedep.io/litellm-pypi-compromise-credential-stealer-backdoor/">2026-10-22 — LiteLLM 1.107.0 被曝在 PyPI 植入凭据窃取与后门</a></li>
<li><a href="https://qz.com/amazon-ai-agents-steal-provider-keys-artex-111626">Amazon captured records of AI agents trying to steal AI keys</a></li>
<li><a href="https://thehackernews.com/2026/11/amazon-uncovers-ai-agent-campaign.html">Amazon Uncovers AI Agent Campaign Targeting LiteLLM, Dify, and...</a></li>
<li><a href="https://thehackernews.com/2026/11/amazon-uncovers-ai-agent-campaign.html">Amazon Uncovers AI Agent Campaign Targeting LiteLLM , Dify , and...</a></li>

</ul>
</details>

**标签**: `#AI security`, `#autonomous agents`, `#API key theft`, `#cybercrime`, `#cloud security`

---

## 科技博客

<a id="item-tech-blog-1"></a>
### [Instacart 用 LLM 改造搜索查询理解](https://blog.bytebytego.com/p/how-instacart-uses-llms-to-make-people) ⭐️ 7.0/10

rss · ByteByteGo · 11月16日 16:30

**「背景」** 电商搜索里，用户很少用商品目录的精确词，查询理解（QU）要把“bread no gluten”这类说法映射成品类、改写和结构化标签。Instacart 原有系统依赖点击/购买等噪声标签和多个独立模型，难以覆盖长尾与歧义查询，维护成本也高。

**「方案」** 该文梳理的改造把 LLM 放进候选生成、重排和校验链路：历史购买先提出候选品类，LLM 结合目录上下文重排，再用嵌入相似度阈值过滤不相关路径。查询改写拆成同义、放宽、替代三类，各配专门提示与后处理，使覆盖率从约 50% 升至 95% 以上、精确率超过 90%。结构化标签采用“离线教师—在线学生”：教师模型生成并校验标签，常见查询走缓存，未命中才调用 LoRA 微调的 Llama-3 8B；约 98% 查询由缓存回答，仅约 2% 需实时推理。服务端合并 LoRA 适配器约降 30% 延迟，配合 H100 把 A100 上近 700ms 降到约 300ms；FP8 再降约 10% 但略损召回，团队选择不量化。Instacart 报告长尾查询平均滚动深度下降 6%、相关投诉下降 50%，每周仍有数百万冷启动查询，延迟仅小幅上升；这些指标来自公司公开材料，独立验证有限。

**「启示」** 作者的核心结论是：LLM 的价值不止于直接回答查询，更在于离线生成高质量监督信号，再用缓存、蒸馏和小模型服务把成本与延迟压到可运营范围。

**标签**: `#LLM query understanding`, `#e-commerce search`, `#knowledge distillation`, `#LoRA serving`, `#latency optimization`

---

<a id="item-tech-blog-2"></a>
### [cuPotential：用可组合原语加速 OpenMM 分子动力学](https://developer.nvidia.com/blog/accelerate-molecular-dynamics-simulations-with-accurate-flexible-primitives-using-nvidia-cupotential/) ⭐️ 5.0/10

rss · NVIDIA CUDA Technical Blog · 11月16日 22:30

**「背景」** 周期性边界下的长程静电与色散计算是经典力场分子动力学的主要瓶颈，而 GPU 架构快速演进也让引擎开发者维护跨硬件高性能 kernel 愈发困难。

**「方案」** NVIDIA 的 cuPotential 以 C API 提供可组合的实空间和倒空间原语，并提供 OpenMM 插件：用其非键力、Langevin 积分器和 Monte Carlo 压力浴替换对应组件，力求少改代码即可接入。教程演示在 Conda 环境中以 CUDA 13.1、OpenMM 8.4 构建运行时与插件，并在 DHFR、BACE、ApoA1、TYK2、10 万原子水和纤维素等 2.4 万至 40 万原子体系上测试；NVIDIA 称 RTX PRO 6000 Blackwell 在部分基准上端到端加速超过 3 倍，B200、H100、A100、L40S 等也常见约 2 倍以上。精度方面，作者用双精度参考比较静电和截断 Lennard-Jones 计算，并称与 D. E. Shaw Research、Flatiron Institute 合作开发的 C2 连续分裂与铺展函数，可在保持相对 OpenMM 默认设置 L2 力 RMSE 的同时减小实空间截断或网格规模，色散能量误差较传统方法改善数千倍，10 ns 水体系的能量漂移较默认 PME 降低数百倍。作者也给出限制：插件只面向矩形周期盒中近似均匀密度的溶剂化体系，仅支持 PME，不支持 LJPME、三斜盒及 OpenMM 的粒子/例外参数偏移。上述性能与精度均来自 NVIDIA 自述，尚无独立验证，且新数值方法的细节仅被简要介绍。

**「启示」** cuPotential 的意义在于把长程相互作用的高性能实现拆成可复用原语，并借 OpenMM 插件把 GPU 加速与误差控制一起交付；但其宣称的收益仍需独立复现，适用范围也受当前体系与 PME 限制。

**标签**: `#molecular dynamics`, `#GPU acceleration`, `#OpenMM`, `#Particle Mesh Ewald`, `#numerical accuracy`

---

## 财经新闻

<a id="item-finance-news-1"></a>
### [中国 10 月经济放缓加剧：消费、工业产出与投资均不及预期](https://www.cnbc.com/2026/11/16/china-retail-sales-october-industrial-output-investment.html) ⭐️ 8.0/10

中国 10 月社会消费品零售总额同比增长 0.4%，低于分析师预期的 0.8%，也低于 9 月的 1.1%；规模以上工业增加值同比增长 4.8%，低于预期的 5.3%，较 9 月的 5.5%明显放缓；前 10 个月固定资产投资同比下降 8.1%，分析师原本预期为下降 7%。

rss · CNBC Finance · 11月16日 03:53

**「背景」** 房地产低迷已持续五年、侵蚀家庭财富，国内消费疲弱与出口激增形成反差，10 月出口同比增长 35.2%，使经济增长更依赖外需。

**「影响」** 据 Pinpoint Asset Management 与花旗研究的分析师提示，若全球人工智能相关资本开支降温或欧盟加码贸易限制，中国的出口企业及相关岗位将更容易受到冲击。

**标签**: `#China economy`, `#macroeconomic data`, `#retail sales`, `#fixed-asset investment`, `#trade surplus`

---

<a id="item-finance-news-2"></a>
### [中美俄领导人将于 11 月 19 日在深圳 APEC 场边举行首次三方会晤](https://apnews.com/article/trump-xi-putin-summit-china-5fe92253ef38100bae913834a9b74d72) ⭐️ 8.0/10

中国外交部发言人宣布，中美俄三国领导人计划于 11 月 19 日在深圳 APEC 峰会期间举行三方会晤；该会晤在 APEC 场边举行，不属于 APEC 正式议程。媒体称，这将是中美俄三国领导人首次专门举行三方会晤。

telegram · zaihuapd · 11月16日 01:38

**「背景」** 亚太经合组织（APEC）第 33 次领导人非正式会议定于 11 月 18 日至 19 日在深圳举行；《环球时报》称，这将是中俄美三国领导人历史上首次面对面会晤，克里姆林宫也已于 11 月 14 日确认三方会晤。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.globaltimes.cn/page/202611/1374382.shtml">China - Russia - US leaders set to meet , sending... - Global Times</a></li>
<li><a href="https://uz.kursiv.media/en/2026-11-16/xi-putin-trump-summit-confirmation/">China confirms Xi-Putin-Trump summit in Shenzhen</a></li>

</ul>
</details>

**标签**: `#geopolitics`, `#APEC`, `#US-China-Russia`, `#diplomacy`, `#foreign policy`

---