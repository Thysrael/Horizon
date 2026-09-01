---
layout: default
title: "Horizon Summary: 2026-09-01 (ZH)"
date: 2026-09-01
lang: zh
---

> 从 42 条内容中筛选出 14 条重要资讯。

---

**科技新闻**
1. [谷歌移除 MV2 扩展，uBlock Origin 下架](#item-tech-news-1) ⭐️ 8.0/10
2. [Linux 7.3 合并窗口收官：提交量创历史第二](#item-tech-news-2) ⭐️ 8.0/10
3. [库克卸任苹果 CEO，特努斯接棒主打 AI 与折叠屏](#item-tech-news-3) ⭐️ 8.0/10
4. [NAT 与互联网中心化：历史反思与技术争论](#item-tech-news-4) ⭐️ 7.0/10
5. [OpenClaw 2.0：史上最大更新，1.6 万 PR](#item-tech-news-5) ⭐️ 7.0/10
6. [DeepSeek 发布 V4-Flash 视觉实验版权重](#item-tech-news-6) ⭐️ 7.0/10
7. [寒序科技公布 MRAM 推理路线：uHBM 带宽 24TB/s](#item-tech-news-7) ⭐️ 7.0/10
8. [欧盟将 ChatGPT、Reddit、Roblox 列为超大型服务](#item-tech-news-8) ⭐️ 7.0/10

**科技博客**
1. [按下回车后，聊天机器人内部发生了什么](#item-tech-blog-1) ⭐️ 8.0/10
2. [Claude Science 与 BioNeMo NIM 的蛋白质结构预测工作流](#item-tech-blog-2) ⭐️ 8.0/10

**财经新闻**
1. [沃什鹰派讲话后，市场大幅押注美联储 9 月加息](#item-finance-news-1) ⭐️ 8.0/10
2. [Aon 以 170 亿美元收购 USI，打造美国中端市场保险平台](#item-finance-news-2) ⭐️ 8.0/10
3. [华为 2026 年上半年净利润同比降 37%](#item-finance-news-3) ⭐️ 8.0/10
4. [中国法院冻结安世半导体约 3 亿美元资产，闻泰索赔 80 亿元](#item-finance-news-4) ⭐️ 8.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [谷歌移除 MV2 扩展，uBlock Origin 下架](https://webiterate.dev/google-removed-extensions-ublock-origin-108/) ⭐️ 8.0/10

谷歌已从 Chrome 应用商店移除基于 Manifest V2 的扩展，包括知名的广告拦截扩展 uBlock Origin，标志着向 Manifest V3 强制迁移的里程碑。Chrome 用户不再能安装或继续使用这类 MV2 扩展，广告拦截、隐私保护和在线安全能力因此受到削弱。社区普遍建议改用 Firefox，并指出 uBlock Origin 在 Firefox 上表现最佳。此次变更虽已预告多年，但实际执行仍引发对单一浏览器厂商主导网络广告过滤的担忧。

hackernews · twapi · 8月31日 21:10 · [社区讨论](https://news.ycombinator.com/item?id=49514878)

**「背景」** Chrome 扩展程序长期采用 Manifest V2 规范，而 Manifest V3 是 Google 推动的新一代扩展架构，对后台脚本和网络请求拦截能力施加了更多限制。Google 一直在推进从 Manifest V2 到 Manifest V3 的迁移，并逐步停止对旧版扩展的支持。据相关报道，Chrome Web Store 已于 8 月 31 日移除剩余的 Manifest V2 扩展列表，其中包括广受欢迎的广告拦截器 uBlock Origin；Chrome 浏览器也因此不再运行这些扩展，并建议用户将其移除，尽管 uBlock Origin 子版块中已出现可暂时重新启用扩展的方法，但有效期仅到 2025 年 6 月。

**「影响」** 受影响最大的 Chrome 用户将无法再依赖 uBlock Origin 等 MV2 扩展拦截恶意广告，广告与钓鱼风险上升；评论者建议改用 Firefox 以保留完整拦截能力。

**「社区讨论」** 评论者一致认为应改用 Firefox，多位用户表示早在 Google 宣布 MV2 计划时就已迁移，并强调 uBlock Origin 在 Firefox 中表现最佳。也有人批评 Google 对网络信息拥有单方面控制权，并担心恶意广告成为更严重的网络安全问题。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://bumbletap.com/blog/chrome-manifest-v2-extensions-removed">Chrome Deletes the Last Manifest V 2 Extensions on August 31</a></li>
<li><a href="https://www.ghostery.com/blog/ublock-origin-not-supported-chrome">uBlock Origin No Longer Supported On Chrome : Best Fixes | Ghostery</a></li>

</ul>
</details>

**标签**: `#chrome`, `#manifest-v3`, `#ad-blocking`, `#ublock-origin`, `#firefox`

---

<a id="item-tech-news-2"></a>
### [Linux 7.3 合并窗口收官：提交量创历史第二](https://lwn.net/Articles/1089791/) ⭐️ 8.0/10

Linux 内核在 7.3 合并窗口结束时发布了 7.3-rc1，共合入 15,267 个非合并变更集，成为内核历史上 -rc1 提交数第二高的版本，仅次于包含近 3,000 个 bcachefs 历史提交的 6.7-rc1；其中约 13,000 个提交是在上一份合并窗口总结之后进入主线的。该版本包含大量架构与子系统更新：s390 新增基于通用 cpuidle 框架的子系统及 Clang 控制流完整性支持；BPF 新增 KF\_SPINLOCK\_SAFE 标志、通过 \_\_arena/\_\_arena\_\_nullable 后缀简化 arena 指针传递、全局 per-CPU 数据访问以及更详细的验证器报错；sched\_ext 的子调度器功能被宣布完成。内核还改进了基于 BTF 的动态探针类型转换、虚拟机的 working-set 跟踪（被认为是迄今合入的最大一块 LLM 辅助核心代码）、DAMON 的数据属性监控以及 kexec 交接时对启动期大页的处理。文件系统方面，ntfs3 支持备用数据流，ntfs 增加 WOF 压缩只读支持，NFS 服务器支持目录委托的 CB\_NOTIFY，Btrfs 移除了版本 1 空闲空间缓存和 usebackuproot 选项，ksmbd 增加 Time Machine 等功能，FUSE 与 io\_uring 结合时改善缓冲池和零拷贝 I/O，F2FS 可动态移除和恢复分区。

rss · LWN.net · 8月31日 14:12

**「背景」** Linux 内核的合并窗口是每个发布周期开始时的一段短时间，用于将各子系统的新功能合入主线，随后进入 -rc 候选版本和稳定阶段。7.3 的合并窗口承接此前已开始的工作，包括 sched\_ext 子调度器、BPF 基础设施以及多项文件系统与架构改进。

**「影响」** 对于内核开发者和发行版/云厂商，7.3 带来的 BPF per-CPU 数据与 arena 指针、完整的 sched\_ext 子调度器以及改进的跟踪设施可直接用于构建调度器和可观测性工具；而 Btrfs 用户则需要通过 btrfstune 把旧文件系统转换到版本 2 空闲空间缓存，否则可能因移除 v1 缓存而遇到性能下降。

**标签**: `#linux-kernel`, `#merge-window`, `#operating-systems`, `#kernel-development`, `#lwn`

---

<a id="item-tech-news-3"></a>
### [库克卸任苹果 CEO，特努斯接棒主打 AI 与折叠屏](https://www.bloomberg.com/news/articles/2026-08-30/apple-s-new-ceo-john-ternus-takes-reins-from-tim-cook-focusing-on-ai) ⭐️ 8.0/10

库克于 8 月 31 日卸任苹果 CEO，51 岁的硬件工程老将约翰·特努斯自 9 月 1 日起接任，库克留任执行主席。新 CEO 的首要任务是推动 AI 落地，弥补 Siri 升级延期等短板。9 月 9 日秋季发布会上，苹果首款折叠屏 iPhone 将亮相，据称配备 12GB RAM 并深度集成 Siri AI，可结合屏幕、日历与相机理解现实场景。

telegram · zaihuapd · 8月31日 10:21

**「背景」** 约翰·特努斯（John Ternus）自 2021 年起担任苹果硬件工程高级副总裁，是公司核心硬件业务的负责人；苹果于 2026 年 4 月已宣布库克将转任执行主席、特努斯接任 CEO，此次交接是计划中的领导层更替。库克自 2011 年起执掌苹果，期间公司市值和产品线大幅扩张，但在生成式 AI 浪潮中 Siri 升级多次延期，新 CEO 的首要任务即补齐这一短板。特努斯接任后，首款折叠屏 iPhone 也被视为苹果在 AI 与硬件形态上同时发力的标志。

**「影响」** 此次换帅意味着苹果将由硬件工程负责人约翰·特努斯主导 AI 战略落地，Siri 升级和首款折叠屏 iPhone 的推进节奏成为短期关注焦点；外界普遍预期 9 月发布会将正式亮相折叠屏 iPhone，但分析师对发布时间、售价（约 2000–2500 美元）、首发地区（可能有美国独占阶段）以及销量（机构预计 2027 财年约 1400 万部）仍存在较大不确定性。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://en.wikipedia.org/wiki/John_Ternus">John Ternus - Wikipedia</a></li>
<li><a href="https://www.apple.com/newsroom/2026/04/tim-cook-to-become-apple-executive-chairman-john-ternus-to-become-apple-ceo/">Tim Cook to become Apple Executive Chairman John Ternus to become Apple CEO - Apple</a></li>
<li><a href="https://www.macrumors.com/roundup/iphone-fold/">iPhone Fold: Everything We Know | MacRumors</a></li>
<li><a href="https://www.cnet.com/tech/mobile/iphone-fold-what-we-know-so-far-about-apples-2026-foldable/">Apple&#x27;s Foldable iPhone Ultra: Release Date, Price, and Leaks</a></li>
<li><a href="https://finance.biggo.com/news/84b35251-63c5-487d-b84b-b2f5ca54ea64">Apple&#x27;s First Foldable iPhone May Launch in U.S. Only, Delaying Global Sales for Months — BigGo Finance</a></li>

</ul>
</details>

**标签**: `#Apple`, `#CEO transition`, `#AI strategy`, `#foldable iPhone`, `#Siri`

---

<a id="item-tech-news-4"></a>
### [NAT 与互联网中心化：历史反思与技术争论](https://dreamstation.systems/personal/ntppost.html) ⭐️ 7.0/10

这篇文章反思 NAT（网络地址转换）在互联网中心化过程中的作用，认为 NAT 是早期关键因素：它使运行服务器不再简单，并让用户习惯客户端-服务器模式。作者指出公网端点的消失削弱了互联网最初的对等承载能力。评论中，当前 Linux NAT 系统的实现者 RustyRussell 坦言，当年为最大化单 IP 连接数而避免端口预留，导致来自不同地址的入站流量无法路由，实际上成为“穷人防火墙”，侵蚀了传统服务器能力。文章在 Hacker News 上引发了关于 NAT 是否应被视作“原罪”、CGNAT 与普通 NAT 的区别以及安全影响的讨论。

hackernews · robinpie · 8月31日 02:23 · [社区讨论](https://news.ycombinator.com/item?id=49504905)

**「背景」** NAT 是缓解 IPv4 地址短缺的一种地址转换机制，允许多个私有网络设备共享一个公网 IP。在 IPv6 普及不彻底和地址资源紧张的背景下，NAT 变得普遍；它默认阻断未经请求的入站连接，也因此被当作简易防火墙。理解这一点有助于评估 NAT 对互联网开放性和服务器托管的长期影响。

**「影响」** 具体而言，依赖自建服务器、P2P 和对等连接的用户与开发者持续承受 NAT 带来的入站连接障碍，这进一步巩固了云计算与客户端-服务器模式的主导地位。

**「社区讨论」** 评论者普遍认可 NAT 削弱了公网端点和自托管能力，但对“原罪”定性有分歧：RustyRussell 承认自己的 Linux 实现为塞入更多连接牺牲了从新地址入站的可路由性；elric 则认为普通 NAT 可控、真正有害的是 CGNAT，并指 NAT 反而保护了大量不安全设备；也有人把问题归因于互联网设计者将现实世界安全假设照搬进网络空间。

**标签**: `#NAT`, `#networking`, `#internet architecture`, `#centralization`, `#systems`

---

<a id="item-tech-news-5"></a>
### [OpenClaw 2.0：史上最大更新，1.6 万 PR](https://openclaw.ai/blog/openclaw-2-accidentally) ⭐️ 7.0/10

OpenClaw 于 8 月 30 日发布 2.0 版，这是其史上最大更新，由 933 名贡献者（含 569 名首次参与者）完成，汇集逾 1.6 万个拉取请求，约占项目全部拉取请求的一半。团队为此近七周未发布新版本，更新覆盖安装、消息、记忆、技能、模型、浏览器、插件与安全等全部环节。新版本简化了安装流程，重建浏览器端体验，并新增共享云端会话，支持多人协作。此次发布对开源 AI 助手生态意义重大，但官方描述未提供更深入的技术细节。

telegram · zaihuapd · 8月31日 04:38

**「背景」** OpenClaw 是一个免费开源、可在本机运行的自主人工智能助手，主要依托消息平台作为用户界面，由奥地利开发者 Peter Steinberger（曾用名 Warelay）于 2025 年 11 月首次发布，并衍生自 Clawd（现名 Molty）。其定位是让个人或团队通过已有的聊天应用使用 AI 助手，支持多种操作系统与平台。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://en.wikipedia.org/wiki/OpenClaw">OpenClaw - Wikipedia</a></li>
<li><a href="https://openclaw.ai/">OpenClaw — Open-Source AI Assistant</a></li>

</ul>
</details>

**标签**: `#open source`, `#AI assistant`, `#software release`, `#collaboration`

---

<a id="item-tech-news-6"></a>
### [DeepSeek 发布 V4-Flash 视觉实验版权重](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-Vision-Exp) ⭐️ 7.0/10

DeepSeek 发布了 DeepSeek-V4-Flash-Vision-Exp 权重，这是 V4 系列首款实验性多模态模型。它在 V4-Flash 架构上加入视觉模块并继续训练，使多模态 agent 能力大幅提升，ApexBench 分数从 26.2 升至 36.5，而文本 agent 任务表现基本持平。目前该权重已在 Hugging Face 上公开，可供开发者下载和测试。作为实验版本，它尚未达到完整稳定版水平，但展示了 DeepSeek 在多模态方向上的进展。

telegram · zaihuapd · 8月31日 11:41

**「背景」** DeepSeek-V4-Flash 是 DeepSeek V4 系列的文本模型，侧重高效推理；本次发布的 DeepSeek-V4-Flash-Vision-Exp 是在该架构中加入视觉模块后继续训练的试验版本，用于探索多模态能力。ApexBench 是衡量模型在真实界面环境中执行多模态 agent 任务的基准，旧版 V4-Flash-0731 在该测试中会忽略输入中的多模态元素，而新模型可以直接处理图像信息，因此得分从 26.2 升至 36.5。

**「影响」** 该实验权重为开发者和研究者提供了直接在 V4-Flash 基础上测试视觉理解与多模态 agent 性能的途径；由于是实验版本，实际生产使用仍需谨慎评估其稳定性与兼容性。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-Vision-Exp">deepseek -ai/ DeepSeek - V 4 - Flash - Vision - Exp · Hugging Face</a></li>
<li><a href="https://officechai.com/ai/deepseek-releases-v4-flash-vision-exp-matches-opus-4-8-on-some-multimodal-benchmarks/">DeepSeek Releases V 4 - Flash - Vision - Exp , Matches Opus 4.8 On...</a></li>

</ul>
</details>

**标签**: `#deepseek`, `#multimodal`, `#vision-language-model`, `#machine-learning`, `#huggingface`

---

<a id="item-tech-news-7"></a>
### [寒序科技公布 MRAM 推理路线：uHBM 带宽 24TB/s](https://mp.weixin.qq.com/s/adyFanNueXUHKnxr9m64kg) ⭐️ 7.0/10

国内首家 MRAM 磁计算公司寒序科技公布了面向 AI 推理的 uHBM 与 uLPU 架构路线图。首代 uHBM 片内读带宽设计值为 24 TB/s；uLPU 面向 4B 多模态模型提出超 2000 Tokens/s Decode 目标。方案将模型权重驻留在 Persistent MRAM 阵列，并在同片完成矩阵-向量运算以减少权重搬运。验证芯片 SpinPU-ED01 已通过第三方检测及 24 小时稳定运行验证。公司披露了从芯片到 2U Tray 及 Rack 的产品路线，但相关性能目标仍属自报，尚无独立验证。

telegram · zaihuapd · 8月31日 13:41

**「背景」** MRAM（磁阻随机存取存储器）是一种非易失性存储技术，与 DRAM/SRAM 相比可在断电后保留数据，并具备较高读写速度。寒序科技是国内首家将 MRAM 与计算单元深度整合的芯片公司；其验证芯片 SpinPU-ED01 集成 120 个 MRAM Bank，实测片上访存带宽密度约 0.105 TB/\(mm²·s\)。这类“权重驻留计算”思路旨在让模型权重常驻存储阵列并在同片完成矩阵-向量运算，从而减少推理时反复搬运权重。

**「影响」** 对 AI 硬件观察者而言，这项路线图显示了 MRAM 在推理侧减少权重搬运、提高能效的潜力；实际带宽与吞吐仍需等量产产品验证。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.sohu.com/a/1070079029_121948416">2000 Tokens/s！寒序科技推出国产LPU推理芯片：让权重不再“搬家”</a></li>
<li><a href="https://news.qq.com/rain/a/20260831A07BY700">寒序科技，重新发明“HBM”_腾讯新闻</a></li>
<li><a href="https://www.icviews.cn/news/35216/7">寒序科技，重新发明“HBM”</a></li>

</ul>
</details>

**标签**: `#MRAM`, `#AI inference`, `#hardware`, `#uHBM`, `#processing-in-memory`

---

<a id="item-tech-news-8"></a>
### [欧盟将 ChatGPT、Reddit、Roblox 列为超大型服务](https://www.euronews.com/next/2026/08/31/eu-places-chatgpt-reddit-and-roblox-under-strictest-digital-safety-rules) ⭐️ 7.0/10

欧盟委员会 8 月 31 日依据《数字服务法》认定 ChatGPT 为超大型在线搜索引擎，并将 Reddit 和 Roblox 列为超大型在线平台，原因是这三项服务在欧盟的月均活跃用户均超过 4500 万人。三者将有四个月的过渡期，随后须开展年度系统性风险评估、接受独立审计，并向监管机构及经审核的研究人员共享数据，重点涉及非法内容、未成年人保护和用户身心健康等。此举意味着这三家科技公司将在内容审核、风险管理和数据透明度方面承担比普通网络服务更严格的义务，标志着欧盟对 AI 聊天机器人和新兴在线社区监管的进一步收紧。

telegram · zaihuapd · 8月31日 14:39

**「背景」** 欧盟《数字服务法》为月均活跃用户超过 4500 万的在线平台和搜索引擎设定了“超大型”门槛，要求它们承担系统性风险评估、独立审计、数据共享等更严格的合规义务。该法案旨在加强网络内容治理，保护用户免受非法内容和有害信息侵害，同时提高平台透明度。ChatGPT 被认定为超大型在线搜索引擎，说明欧盟将人工智能对话服务纳入《数字服务法》监管范围，而 Reddit 和 Roblox 则分别作为在线社区和游戏平台面临类似的高级别监管。

**「影响」** ChatGPT、Reddit 和 Roblox 的欧盟用户将看到平台在未成年保护、非法内容处置和用户身心健康等方面采取更严格的机制，平台可能需要调整功能设计或内容审核规则以满足合规要求。

**标签**: `#EU regulation`, `#Digital Services Act`, `#ChatGPT`, `#online platforms`, `#tech policy`

---

## 科技博客

<a id="item-tech-blog-1"></a>
### [按下回车后，聊天机器人内部发生了什么](https://blog.bytebytego.com/p/what-happens-inside-an-ai-chatbot) ⭐️ 8.0/10

rss · ByteByteGo · 8月31日 15:31

**「背景」** 作者从用户按下回车后的短暂停顿切入，指出典型 LLM 在输出首字前要经过约十几个阶段，模型没有记忆，屏幕上的对话历史每一轮都要从零重建，共享硬件和批处理也会影响结果。

**「方案」** 到达模型的并非用户输入本身，而是由系统提示、工具定义、记忆、检索文档、完整历史和最新消息拼装成的上下文文档；这个拼装过程就是上下文工程，它决定了不同产品用同一模型为何给出不同答案。模型无状态，每轮都必须重发全部历史，因此长对话的输入成本随轮次滚雪球，常用丢旧消息、摘要压缩或外部检索来缓解。安全层是独立的小模型，通过级联设计把开销压到约 1%，正常请求误拒率降到 0.05%。随后文本被切成 token（一个 token 约 0.75 个英文词），不同语言同一内容的 token 数可相差 15 倍。请求进入队列并与其他用户共享硬件：连续批处理在单个步骤级别调度，吞吐量最高可提升 23 倍，但数值运算对批大小敏感，相同请求也可能得到不同结果。生成分两阶段：预填并行读取全部输入，决定停顿时长；解码逐 token 串行输出，受内存带宽限制，决定打字速度。预填产生的 KV 缓存被分块按需分配，缓存浪费从 60-80%降到 4%以下，吞吐提升 2-4 倍；前缀缓存让稳定内容放开头，且缓存费率约为普通输入的一折。输出可流式返回，但输出安全校验与流式存在矛盾。工具调用则形成循环：模型只生成调用文本，应用执行后把结果放回上下文，让整个流程重新走一遍，多次搜索会让成本和延迟显著放大。

**「启示」** 作者的核心结论是：用户感知到的“对话”其实是模型每轮冷读整份重建文档，这解释了长聊天为什么会变慢、变贵并丢失细节。

**标签**: `#LLM inference`, `#context engineering`, `#tokenization`, `#KV cache`, `#AI systems`

---

<a id="item-tech-blog-2"></a>
### [Claude Science 与 BioNeMo NIM 的蛋白质结构预测工作流](https://developer.nvidia.com/blog/run-nvidia-bionemo-nim-microservices-for-protein-structure-prediction-in-claude-science/) ⭐️ 8.0/10

rss · NVIDIA CUDA Technical Blog · 8月31日 16:30

**「背景」** 作者指出，科研智能体需要调用专门工具，但不同模型的运行环境和接口差异很大，通用智能体难以自行决定使用哪个模型、如何格式化请求以及哪些参数重要。BioNeMo Agent Toolkit 将生命科学模型封装为可调用的技能，并接入 Claude Science，从而让智能体能够直接编排蛋白质结构预测等复杂流程。

**「方案」** 作者在配备 NVIDIA L40S 或 H100 的机器上配置了 msa-search、OpenFold3 和 Boltz-2 三个 NIM 端点，并以 Seh1 和预测的 Mio 家族伙伴 C1HCX1 为例，先生成单链与配对 MSA，再用两个独立模型分别预测单体和复合物。核心发现是 MSA 是承载信息的输入：有 MSA 时异源二聚体的界面 iPTM 达到 0.85（OpenFold3）和 0.82（Boltz-2），去掉 MSA 后分别跌至 0.14 和 0.19；增加采样步数无法弥补，两个不同架构的模型却彼此吻合。结构比对显示，两个模型都把 C1HCX1 的 β 链插入 Seh1 的 WD40 开放边缘，核心 Cα-RMSD 约 0.65–0.68 Å，重现了论文 Figure 4e 的观察。作者强调，这仍是预测出的相互作用假说，并未经实验证实，需谨慎解读置信度分数并保留样本供后续验证。

**「启示」** 作者的结论是，这套工作流的真正价值不在于证明两个蛋白一定结合，而在于提供一条可复现、有证据支撑的路径来生成并检查结构假说；最终的判断仍需交给实验验证。

**标签**: `#protein structure prediction`, `#multiple sequence alignment`, `#BioNeMo`, `#agentic AI`, `#Claude Science`

---

## 财经新闻

<a id="item-finance-news-1"></a>
### [沃什鹰派讲话后，市场大幅押注美联储 9 月加息](https://www.cnbc.com/2026/08/31/markets-see-warsh-endorsing-a-rate-hike-in-september-not-everyone-is-convinced.html) ⭐️ 8.0/10

美联储主席沃什在杰克逊霍尔研讨会上表示，近期通胀回落不足以说明趋势明显改善，市场随即大幅上调加息预期。据 CME FedWatch，联邦公开市场委员会 9 月 15-16 日会议加息的市场隐含概率周一升至 66.1%，约为讲话前的两倍；但财政部长贝森特等官员和分析师认为，目前没有充分理由加息。

rss · CNBC Finance · 8月31日 19:38

**「背景」** 7 月 FOMC 会议并未形成加息共识，12 名投票委员中只有 3 人支持加息；此后个人消费支出价格指数（PCE）通胀仍高于 2%目标，但达拉斯联储剔除两端极端值后的通胀指标为 2.3%，且非农就业已连续三个月偏弱。沃什强调，必须看到潜在通胀明确且足够快地回到目标，否则美联储“还有工作要做”。

**标签**: `#Federal Reserve`, `#monetary policy`, `#interest rates`, `#inflation`, `#market expectations`

---

<a id="item-finance-news-2"></a>
### [Aon 以 170 亿美元收购 USI，打造美国中端市场保险平台](https://www.cnbc.com/2026/08/31/aon-ceo-says-usi-deal-seeks-to-build-premiere-middle-market-insurance-platform.html) ⭐️ 8.0/10

保险经纪商 Aon 宣布将以 170 亿美元（通过新增债务融资）从私募股权公司 KKR 手中收购美国第十大保险经纪商 USI Insurance Services，交易预计在第四季度完成，尚需监管批准。Aon CEO Greg Case 表示，合并将建立“美国中端市场领先平台”，覆盖约 20 万家美国中端市场企业及其 4800 万员工。

rss · CNBC Finance · 8月31日 15:15

**「背景」** KKR 在 2017 年以约 43 亿美元估值投资 USI，之后逐步扩大持股；Aon 此前在 2024 年收购了另一家美国中端市场保险经纪公司 NFP，本次交易延续了这一布局。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.businesswire.com/news/home/20260831081134/en/KKR-To-Sell-USI-to-Aon-plc-in-$17-Billion-Transaction">KKR To Sell USI to Aon plc in $17 Billion Transaction</a></li>
<li><a href="https://aon.mediaroom.com/2026-08-31-Aon-to-acquire-USI-to-establish-the-premier-U-S-middle-market-platform">Aon to acquire USI to establish the premier U.S. middle ...</a></li>

</ul>
</details>

**标签**: `#Aon`, `#USI`, `#mergers and acquisitions`, `#insurance brokerage`, `#middle market`

---

<a id="item-finance-news-3"></a>
### [华为 2026 年上半年净利润同比降 37%](https://mp.weixin.qq.com/s/gfpojf6yfdmneU0iZ1xpbQ) ⭐️ 8.0/10

华为发布 2026 年上半年业绩：营收 4678 亿元，同比增长约 9.6%；净利润 234.27 亿元，同比下滑约 37%。公司称利润下滑主要因存储芯片涨价和加大半导体研发投入。

telegram · zaihuapd · 8月31日 11:10

**「背景」** 华为持续加码自研芯片投入，而存储芯片是手机等产品的重要部件，价格大涨会直接压缩硬件厂商的利润空间。

**「影响」** 为应对存储芯片涨价，华为上半年囤购原材料，导致现金流为负 399 亿元，这会直接减少其可用于后续投资和运营的现金储备。

**标签**: `#Huawei`, `#earnings`, `#semiconductors`, `#smartphones`, `#cash flow`

---

<a id="item-finance-news-4"></a>
### [中国法院冻结安世半导体约 3 亿美元资产，闻泰索赔 80 亿元](https://www.reuters.com/world/asia-pacific/chinese-court-freezes-dutch-chipmaker-nexperia-bvs-stakes-four-china-units-2026-08-31/) ⭐️ 8.0/10

中国东莞一家法院在闻泰科技提起的诉讼中，冻结荷兰芯片商安世半导体及其设备子公司最高 21.4 亿元人民币（约 3 亿美元）资产。此前闻泰去年被荷兰当局剥夺对安世的控制权，今年 5 月起诉安世等方执行歧视性荷兰限制，索赔 80 亿元；冻结措施于 8 月 20 日至 25 日生效，持续到 2029 年 8 月。

telegram · zaihuapd · 8月31日 12:26

**「背景」** 事件源于荷兰当局去年剥夺了中国闻泰科技对荷兰芯片商安世半导体（Nexperia）的控制权；荷兰政府与中国会谈后虽暂停了部分运营限制，但股权归属仍待荷兰法院审理。闻泰今年 5 月指控安世执行歧视性荷兰限制并索赔 80 亿元，本次中国法院的资产冻结是该诉讼中的保全措施。

**「影响」** 冻结涉及安世半导体在四家中国企业的持股，包括其中国、无锡、上海半导体业务及设备子公司的无锡独资企业，冻结期间这些股权可能无法处置，或影响相关中国业务的股权交易。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.caixinglobal.com/2025-11-20/netherlands-suspends-nexperia-asset-freeze-after-talks-with-china-102384737.html">Netherlands Suspends Nexperia Asset Freeze After... - Caixin Global</a></li>

</ul>
</details>

**标签**: `#semiconductor`, `#asset freeze`, `#litigation`, `#Nexperia`, `#Wingtech`

---