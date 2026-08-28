---
layout: default
title: "Horizon Summary: 2026-08-28 (ZH)"
date: 2026-08-28
lang: zh
---

> 从 38 条内容中筛选出 11 条重要资讯。

---

**科技新闻**
1. [英伟达据称将以 130 亿美元收购 Hugging Face](#item-tech-news-1) ⭐️ 9.0/10
2. [地月双向高速激光通信首次实现，下行速率达 100Mbps](#item-tech-news-2) ⭐️ 9.0/10
3. [优化 1.1.1.1 的 DNS 缓存节省 100TB 内存](#item-tech-news-3) ⭐️ 8.0/10
4. [小型模型已经到来](#item-tech-news-4) ⭐️ 8.0/10
5. [Claude Code 自动模式被曝 80% 可绕过的提示注入攻击](#item-tech-news-5) ⭐️ 8.0/10
6. [利用 steal time 调节 CPU 需求的虚拟机补丁](#item-tech-news-6) ⭐️ 8.0/10
7. [Microduck：可本地训练 AI 行为的开源机器人平台](#item-tech-news-7) ⭐️ 7.0/10
8. [84 天用 LLM 辅助反编译 N64 游戏《Snowboard Kids》](#item-tech-news-8) ⭐️ 7.0/10
9. [高通称 6G 为 AI 而生，运营商转向 Token 即服务](#item-tech-news-9) ⭐️ 7.0/10

**科技博客**
1. [背景工作：从定时任务到分布式系统](#item-tech-blog-1) ⭐️ 4.0/10

**财经新闻**
1. [财报超预期带动英伟达、Salesforce 等盘前上涨，惠普和 Wendy&\#x27;s 下跌](#item-finance-news-1) ⭐️ 8.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [英伟达据称将以 130 亿美元收购 Hugging Face](https://www.businessinsider.com/nvidia-in-talks-to-buy-hugging-face-13-billion-dollars-2026-8) ⭐️ 9.0/10

据 The Information 和 TechCrunch 报道，英伟达已同意以约 130 亿美元收购开源模型平台 Hugging Face，交易尚未正式确认且可能仍有变数。Hugging Face 是 AI 开发者分发、托管和试用开源模型的核心枢纽，被英伟达收购后，AI 基础设施与开源模型生态将高度整合。英伟达由此可将模型库与自身 GPU、推理平台绑定，但也让社区担忧平台的中立性和开源 AI 的未来。创始团队 Julien、Thomas 和 Clem（均为法国人）预计将获得可观收益，有评论猜测他们可能用这笔资金在欧洲创建新的前沿 AI 实验室。截至报道发布（2026 年 8 月 24 日），交易细节与监管审批结果均未公布。

hackernews · mfiguiere · 8月27日 01:12 · [社区讨论](https://news.ycombinator.com/item?id=49458161)

**「背景」** Hugging Face 是目前人工智能领域最具影响力的开源模型与数据集托管平台之一，开发者在上面分享、下载和试用各类机器学习模型，也常被称为“AI 界的 GitHub”。英伟达（Nvidia）是 AI 算力芯片巨头，此前曾计划自建云端 AI 业务但进展不顺；据分析，这笔收购若完成，将让 Nvidia 直接掌握 Hugging Face 的开发者生态和模型分发入口，为其云 AI 战略提供助力。

**「影响」** 对依赖 Hugging Face 托管、下载和评测开源模型的开发者与团队而言，平台所有权的变更意味着其长期中立定位和开放性面临不确定性；若交易完成，英伟达在 AI 软件生态中的控制力将显著增强。

**「社区讨论」** 社区反应混杂：有人祝贺创始团队并希望英伟达善待社区，也有人质疑 130 亿美元估值过高，并担心 Hugging Face 在 Nvidia 旗下丧失“比 OpenAI 更开放”的定位；还有评论从欧洲主权 AI 角度讨论，认为创始团队套现后可能投资欧洲下一代 AI 实验室。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://arstechnica.com/ai/2026/08/report-nvidia-to-acquire-ai-model-repository-hugging-face-for-13-billion/">Report: Nvidia to acquire AI model repository Hugging Face for $ 13 ...</a></li>

</ul>
</details>

**标签**: `#acquisition`, `#nvidia`, `#huggingface`, `#open-source`, `#ai-industry`

---

<a id="item-tech-news-2"></a>
### [地月双向高速激光通信首次实现，下行速率达 100Mbps](https://www.stdaily.com/web/gdxw/2026-08/26/content_570163.html) ⭐️ 9.0/10

中国科学院空间应用工程与技术中心牵头，依托 DRO-A 卫星，在超过 40 万公里的地月距离上首次建立双向激光链路，实现我国地月双向高速激光通信，标志空间激光通信从近地轨道迈入地月空间。试验初步实现上行 1.25 Mbps、下行 100 Mbps 的速率。以 8K 月面高清图像为例，传统 5 Mbps 微波下传约需 4 至 5 分钟，百 Mbps 激光通信仅约 12 秒。该成果为月球及深空探测中的大容量数据回传提供了新的技术路径。

telegram · zaihuapd · 8月27日 00:33

**「背景」** 空间激光通信是利用激光束作为载波进行信息传输的通信方式，相比传统微波通信具有带宽大、速率高、抗干扰能力强等优势。此次试验依托 DRO-A 卫星实施，DRO-A 是由中国科学院空间应用工程与技术中心牵头、联合之江实验室等单位研制的一颗卫星，主要用于地月空间相关技术试验。此次任务在超过 40 万公里的地月距离建立双向激光链路，标志着空间激光通信从近地轨道向更深远的深空通信迈出重要一步。

**「影响」** 该成果将直接支撑我国后续月球与深空探测任务的高速率数据回传，使 8K 月面图像等大容量科学数据可在十几秒量级内下传，并为未来深空通信体制选择提供可行依据。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.163.com/dy/article/L5BQ9P070511DC8A.html">163.com/dy/article/L5BQ9P070511DC8A.html</a></li>
<li><a href="http://sjgh.xmkjsz.com/agp/detail/aqy.html">球报：森林即将谈妥葡体中 卫 迪奥曼德，葡体将保留10%二转</a></li>

</ul>
</details>

**标签**: `#space communications`, `#laser technology`, `#China space program`, `#deep space`, `#satellite communications`

---

<a id="item-tech-news-3"></a>
### [优化 1.1.1.1 的 DNS 缓存节省 100TB 内存](https://blog.cloudflare.com/dns-cache-memory-optimization-1111/) ⭐️ 8.0/10

Cloudflare 在博客文章中介绍了对 1.1.1.1 DNS 解析器缓存进行内存优化的成果，总共节省了约 100 TB 的内存。这次优化涉及系统级的内存管理改进，展示了在大规模基础设施中细致管理内存所能带来的巨大影响。虽然这属于增量式工程优化而非范式转变，但它凸显了系统编程和内存效率在大型服务中的持续重要性。社区讨论中提到的具体手段包括减少独立内存分配、合并多个列表结构等做法。

hackernews · TangerineDream · 8月27日 17:17 · [社区讨论](https://news.ycombinator.com/item?id=49468083)

**「背景」** Cloudflare 的 1.1.1.1 DNS 服务使用名为 Big Pineapple 的缓存系统。通过五项针对 Rust 代码中缓存布局的内存优化，Cloudflare 将每个缓存条目的内存占用减少了 56%，并在全球服务器群中释放了约 100 TB 内存。这些优化属于系统编程和性能工程领域的增量改进，体现了细致的内存管理价值。

**「影响」** 节省 100 TB 内存直接降低了 Cloudflare 运行 1.1.1.1 DNS 服务所需的内存资源，有助于节约成本或释放容量用于其他负载。

**「社区讨论」** 评论者普遍认可“先交付可用产品、再优化成本”的工程路线，并认为这再次说明系统编程仍然重要。也有开发者指出，将多个独立 Vec 合并为单个 Vec 并依赖偏移量访问可能削弱 Rust 的安全保证；另有人以 MaraDNS 为例，说明用一次大 malloc 分配可将大型黑名单的内存占用从 237 MB 降至 9.5 MB。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://blog.cloudflare.com/dns-cache-memory-optimization-1111/">How we saved 100 terabytes of memory by optimizing 1.1.1.1’s DNS cache | Cloudflare Blog</a></li>

</ul>
</details>

**标签**: `#DNS`, `#memory optimization`, `#Cloudflare`, `#systems programming`, `#performance engineering`

---

<a id="item-tech-news-4"></a>
### [小型模型已经到来](https://calv.info/small-models-have-arrived) ⭐️ 8.0/10

本文认为，小型高效语言模型现已具备竞争力，并将迎来对快速、廉价且足够好的 AI 应用需求的增长。作者引用早期使用 7B 本地模型配合 Guidance 库编写测试代码的经历，指出在思维模型出现之前，小模型已能完成复杂流程。文章还区分了“IQ 180”式工作和“token 生成器”式工作，并讨论用较小模型替代大型模型以减少成本的做法。文章强调，许多应用不需要庞大的世界知识，小模型在成本、速度和足够性能上的优势将推动其普及。

hackernews · tosh · 8月27日 15:56 · [社区讨论](https://news.ycombinator.com/item?id=49466917)

**「背景」** 小型语言模型是指参数规模较小但经过高效训练或蒸馏的模型，能够在推理速度、成本和资源占用上远低于大型模型，同时保持接近的性能。过去大型模型被视为能力上限的代表，但随着 GLM 5.3、Fable 5 等新一代模型的出现，小型模型在帕累托前沿上提供了新的选择，使得“快速、便宜、足够好”的应用场景逐渐成熟。

**「主要影响」** 小型语言模型的竞争力和低成本、低延迟优势正在促使开发团队将推理负载从大模型迁移到更小的模型，例如有编码团队讨论为控制成本从 Sol 降级到 Luna；同时，这些模型还让仅用 CPU 进行部署成为可能，降低了 AI 应用的基础设施门槛。但社区也提醒，现有基准测试可能已被“刷分”，实际可用性仍需验证。

**「社区讨论」** 评论区围绕基准可靠性提出质疑，认为 Opus 与 Fable 的智能对比不可信，且现有基准可能被过度优化。也有评论指出，大型参数模型如同“世界知识、语言技能和推理原语”的储备池，而许多场景只需少量语言技能和推理能力，因此存在“bottom”策略空间。另有用户提到其朋友因成本考虑讨论从 Sol 降级到 Luna。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://calv.info/small-models-have-arrived">Small Models Have Arrived - calv.info</a></li>
<li><a href="https://ai.plainenglish.io/small-is-beautiful-the-rise-of-small-language-models-for-efficiency-and-specialization-of-genai-67fa1794f58a">Small is Beautiful: The Rise of Small Language Models for...</a></li>
<li><a href="https://pub.towardsai.net/stop-scrolling-this-is-the-only-small-language-model-article-youll-ever-need-2279fe59659d">This Is the Only Small Language Model Article You’ll... | Towards AI</a></li>

</ul>
</details>

**标签**: `#small language models`, `#AI efficiency`, `#model deployment`, `#benchmarks`, `#LLM trends`

---

<a id="item-tech-news-5"></a>
### [Claude Code 自动模式被曝 80% 可绕过的提示注入攻击](https://simonwillison.net/2026/Aug/27/breaking-claude-code-opus-5-auto-mode/) ⭐️ 8.0/10

安全研究员 Johann Rehberger 公布了对 Anthropic Claude Code Opus 5 自动模式（auto mode）的提示注入攻击，宣称约 80% 的次数可以绕过防护。攻击方法是诱导代理下载并解压 zip 压缩包，然后执行其中提取出的恶意本地 struct.py 文件；由于代码导入 base64 时，Python 会优先从当前目录加载同名模块，恶意文件会被执行。Anthropic 近期已将自动模式设为 Claude Code 的默认模式，但该攻击显示其防护并不可靠，甚至在部分运行中，自动模式会阻止代理终止已被攻陷的恶意进程。Simon Willison 赞同研究者的结论，认为只要存在被对抗攻击盯上的风险，就应该在容器、虚拟机或操作系统沙箱中运行无人值守的编码代理。

rss · Simon Willison · 8月27日 22:50

**「背景」** 提示注入攻击利用网页、文件等不可信内容中嵌入的指令，让 AI 代理执行非预期操作。自动模式是 Anthropic 为 Claude Code 设计的安全机制，旨在让代理自主批准或阻止行动，但这次攻击利用 zip 解压和 Python 的导入语义，使本地 struct.py 文件在导入 base64 时优先于标准库被加载并执行，从而绕过自动模式的判断。

**「影响」** 默认使用自动模式的 Claude Code 用户面临恶意代码在代理环境中执行的风险，可能导致凭据泄露或项目破坏。当前最实际的缓解措施是不要在不设沙箱、暴露主目录和云凭据的环境中运行无人值守代理，同时限制网络出口并持续监控代理行为。

**标签**: `#prompt injection`, `#AI security`, `#Claude Code`, `#vulnerability`, `#software engineering`

---

<a id="item-tech-news-6"></a>
### [利用 steal time 调节 CPU 需求的虚拟机补丁](https://lwn.net/Articles/1090381/) ⭐️ 8.0/10

Linux 内核开发者 Shrikanth Hegde 提交了一套补丁系列，让虚拟机根据物理 CPU 的争用程度，通过 steal time 主动减少其使用的虚拟 CPU 数量。该机制维护一个“preferred CPU”集合，调度器会尽量把任务放到偏好 CPU 上，使被移出集合的 CPU 基本空闲。策略由 steal\_governor 工作队列实现，默认每 1000ms 检查一次，steal time 低于 2%时增加偏好 CPU，高于 5%时移除一整个核心的 CPU（至少保留一个）。基准测试显示，在可合作的场景下性能提升从 schbench 的约 2%到 hackbench 的超过 44%。该方案完全自愿，依赖各虚拟机共同参与，在多租户系统中不合作者可能获得相对优势。

rss · LWN.net · 8月27日 14:11

**「背景」** Steal time 指虚拟机中的 vCPU 等待物理 CPU 的时间，可从/proc/stat 或 top、vmstat 等工具读取，是衡量物理 CPU 争用的指标。当 vCPU 被抢占且正持有锁时，同一个虚拟机内其他仍在运行的线程可能浪费执行时间自旋等待锁释放，导致性能严重下降；这正是补丁希望通过减少争用来缓解的问题。

**「影响」** 对于可预期合作的环境（如同一组织内部署的虚拟化集群），该补丁能显著缓解物理 CPU 争用并提升工作负载性能；但在不合作的多租户系统中，主动降低 CPU 需求的虚拟机可能相对吃亏，因此其适用范围受到合作意愿的限制。

**标签**: `#Linux kernel`, `#virtualization`, `#CPU scheduling`, `#performance`, `#cloud computing`

---

<a id="item-tech-news-7"></a>
### [Microduck：可本地训练 AI 行为的开源机器人平台](https://pollen-robotics.com/microduck/) ⭐️ 7.0/10

Pollen Robotics 推出了 Microduck，一个面向个人开发者和爱好者的开源小型机器人平台。该平台内置 Rockchip RK3566 处理器及 AI 加速器、1GB 内存、32GB 存储、Wi-Fi、蓝牙、麦克风、扬声器、两个 NFC 天线和可拆卸电池（续航约 1 小时），整机重约 800 克，搭载 Dynamixel 伺服电机，机载策略循环可达 50 赫兹。开箱即具备行走、坐立、踢球、地面拾取、轮滑和自我恢复等七种行为，用户可本地训练额外行为，或通过 Hugging Face Jobs 训练并导出为 ONNX 模型进行部署。其核心亮点在于绕开 NVIDIA Isaac 的复杂配置，官方称可在不到一小时内让系统在笔记本电脑上运行，显著降低了自定义机器人开发的门槛。

hackernews · robotswantdata · 8月27日 10:57 · [社区讨论](https://news.ycombinator.com/item?id=49462763)

**「背景」** Microduck 是由法国公司 Pollen Robotics 开发的一款开源双足机器人，高度约 25 厘米，配备 15 个电机、摄像头、LiDAR 和可抓取的喙部。它搭载 Rockchip RK3566 处理器（含 AI 加速器）、1GB 内存、32GB 存储，并预装行走、坐下、踢腿等七种行为。用户可通过开源 SDK 在仿真环境中训练强化学习策略，再以 ONNX 格式部署到实体机器人，也可以使用 Hugging Face Jobs 进行云端训练。

**「影响」** 对于因 Isaac 配置困难而受阻的个人机器人开发者，Microduck 提供了一条更易上手的替代路径，使他们能够快速在真实硬件上训练和部署自定义行为，同时借助公开规格和可导出 ONNX 的流程降低了实验成本。

**「社区讨论」** 有评论指出模拟器默认使用 ZQSD 方向键（AZERTY 键盘布局），建议增加键盘布局偏好设置；也有用户认为产品页面信息过于密集，难以快速找到规格参数。另有人将 Microduck 与 Mondo Robotics 产品作对比，并补充说明许多机器人新闻中的 RL 策略训练实际依赖 Google DeepMind 维护的 MuJoCo 模拟引擎。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://pollen-robotics.com/microduck/">Microduck - A tiny biped robot you can teach new tricks ...</a></li>
<li><a href="https://github.com/pollen-robotics/microduck">GitHub - pollen-robotics/microduck: A Tiny biped duck robot</a></li>
<li><a href="https://store.pollen-robotics.com/products/microduck">Microduck – Pollen Robotics SAS</a></li>

</ul>
</details>

**标签**: `#robotics`, `#AI`, `#hardware`, `#open source`, `#machine learning`

---

<a id="item-tech-news-8"></a>
### [84 天用 LLM 辅助反编译 N64 游戏《Snowboard Kids》](https://blog.chrislewis.au/decompiling-a-nintendo-64-game-in-84-days/) ⭐️ 7.0/10

一位开发者撰文回顾了自己在 84 天内用 LLM 辅助逆向工程技术成功反编译 Nintendo 64 游戏《Snowboard Kids》的过程。该项目展示了如何将大型语言模型融入严格的逆向工程工作流，例如为每个任务设置明确截止日期以提升代理效率。文章详细介绍了这一工作流的创新之处，并为其他希望借助 AI 进行老游戏反编译和开源保存的人提供了可复用的方法论。

hackernews · knackers · 8月27日 15:01 · [社区讨论](https://news.ycombinator.com/item?id=49466006)

**「背景」** Nintendo 64 游戏《Snowboard Kids》现已实现 100% 反编译，所有函数都有匹配的 C 实现，编译后能生成与原版游戏完全相同的机器码。该项目由 Chris Lewis 等人仅用 84 天完成，远快于其续作《Snowboard Kids 2》的 596 天，主要得益于 LLM 辅助逆向工程、社区专家参与以及改进的工具链。这类反编译项目通常从商业 ROM 中提取素材，并将逆向出的 C 代码重新组合成相同 ROM，目的是支持修复、移植和存档，且项目明确声明不用于任何商业用途。

**「影响」** 该反编译项目有望为《Snowboard Kids》带来长期的社区维护、模组支持与潜在重制机会，同时为利用 LLM 处理其他复古游戏逆向工程提供了可参照的实践模板。

**「社区讨论」** 评论者普遍对近期各类反编译项目表示赞赏，并称借助 LLM 可以构建高效工作流、突破个人产出瓶颈。部分评论讨论了为什么游戏公司不直接做此类反编译再发售，也有人提到类似项目如《Legend of Dragoon》重编译版和《Agent 64》带来的怀旧体验。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://blog.chrislewis.au/decompiling-a-nintendo-64-game-in-84-days/">Decompiling a Nintendo 64 Game in 84 Days | Chris&#x27; Blog</a></li>
<li><a href="https://zeli.app/story/49466006">Snowboard Kids Decompiled in 84 Days, Thanks to AI and ...</a></li>
<li><a href="https://github.com/cdlewis/snowboardkids-decomp">GitHub - cdlewis/snowboardkids-decomp: Decompilation of ...</a></li>

</ul>
</details>

**标签**: `#reverse-engineering`, `#LLM-assisted development`, `#Nintendo 64`, `#decompilation`, `#open-source`

---

<a id="item-tech-news-9"></a>
### [高通称 6G 为 AI 而生，运营商转向 Token 即服务](https://finance.sina.com.cn/jjxw/2026-08-26/doc-inipsezr5961972.shtml) ⭐️ 7.0/10

高通执行副总裁马德嘉在圣地亚哥 6G 媒体日上表示，6G 真正的分水岭不在网速，而是 AI 首次写入网络底层逻辑，将催生为 AI 而生的“智能体 AI 设备”，并点名豆包 AI 手机。他认为运营商商业模式将从卖数据转向算力即服务、Token 即服务，6G 标准预计 2028 年确定。与此同时，高通正在扩张数据中心业务，发布 Dragonfly 产品线和 HBC 高带宽计算架构，目标 2029 财年数据中心营收超过 150 亿美元，并已收购 AI 基础设施公司 Modular。这些动作显示高通正把 6G 叙事从速率转向 AI 原生，并把 AI 基础设施作为新的增长引擎。

telegram · zaihuapd · 8月27日 02:31

**「背景」** 6G 是继 5G 之后的新一代移动通信标准，目前仍在定义和研发阶段，高通等企业正推动将 AI 能力直接融入网络底层设计，而非仅仅作为上层应用。AI Token 是 AI 模型处理文本和数据的计量单位，模型通过分析大量 Token 来学习语言模式并实现推理和生成，因此“Token 即服务”意味着运营商可能按 AI 计算量而非流量收费。此外，高通已上调 2029 财年非移动业务营收目标至 400 亿美元，并推出面向数据中心的 Dragonfly 处理器产品和 HBC 高带宽计算架构，且与 Meta 合作将其 CPU 用于数据中心。

**「影响」** 对运营商而言，6G 时代若采用 Token 即服务的计费模式，将直接影响其网络变现方式和资费设计；对高通而言，数据中心营收目标与其传统手机芯片业务形成互补，但能否实现取决于 Dragonfly/HBC 落地进度与 Modular 整合成效。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://blockonomi.com/qualcomm-qcom-stock-rockets-12-on-40b-revenue-goal-and-meta-partnership/">Qualcomm (QCOM) Stock Rockets 12% on $40B Revenue Goal and...</a></li>
<li><a href="https://www.qualcomm.com/research/6g">6 G : The Future of Mobile Connectivity &amp; Wireless Tech | Qualcomm</a></li>
<li><a href="https://blogs.nvidia.com/blog/ai-tokens-explained/">What Are AI Tokens ? The Language and Currency... | NVIDIA Blog</a></li>

</ul>
</details>

**标签**: `#6G`, `#AI`, `#Qualcomm`, `#telecom`, `#data center`

---

## 科技博客

<a id="item-tech-blog-1"></a>
### [背景工作：从定时任务到分布式系统](https://blog.bytebytego.com/p/background-work-from-cron-jobs-to) ⭐️ 4.0/10

rss · ByteByteGo · 8月27日 15:31

**「背景」** 作者用常见的上传头像场景切入：如果调整图片大小、内容检查、分发 CDN、更新元数据都在同一次请求里完成，用户会看到按钮转好几秒，体验很差。因此需要把这些附加操作移到请求路径之外去执行。

**「方案」** 这种移出请求路径的处理就是背景工作：请求只需把图片存入对象存储即可立即返回，后续的缩放、扫描、分发再在后台完成。作者列举了几类触发来源：用户操作（如注册后发欢迎邮件）、定时器（如夜间报告、月结账单、缓存刷新）、外部系统（如 webhook 或文件落桶），以及批量处理带来的成本或安全优势。大多数团队一开始只用一台机器上的定时脚本就能承担大量背景工作；但随着系统变大变复杂，作者指出，需要的就不再是单一脚本，而是不同的策略。文章表示会具体展开这些策略。

**「启示」** 作者的核心观点是，把耗时的附加操作移出请求路径能显著改善用户体验，而背景工作本身也会随着系统扩展，从简单的定时任务走向更复杂的分布式执行方式。这一演进需求是后续讨论各种策略的出发点。

**标签**: `#background work`, `#asynchronous processing`, `#cron jobs`, `#system design`

---

## 财经新闻

<a id="item-finance-news-1"></a>
### [财报超预期带动英伟达、Salesforce 等盘前上涨，惠普和 Wendy&\#x27;s 下跌](https://www.cnbc.com/2026/08/27/stocks-making-the-biggest-moves-premarket-nvda-hp-crm-dg-p.html) ⭐️ 8.0/10

多家公司发布财报后盘前股价大幅波动：英伟达第二季度调整后每股收益为 2.22 美元、收入 962.2 亿美元，均高于分析师预期，并预计第三季度收入为 1080 亿美元；Dollar General 上调全年每股收益指引至 7.80 至 8.00 美元，Salesforce、Okta 和 CrowdStrike 也因业绩超预期上涨。

rss · CNBC Finance · 8月27日 14:45

**「背景」** 这些波动发生在美股财报季密集发布期，投资者正通过科技公司业绩判断 AI 需求，并通过零售商业绩观察消费者支出。

**标签**: `#Earnings`, `#Premarket Movers`, `#Nvidia`, `#Salesforce`, `#Corporate Guidance`

---