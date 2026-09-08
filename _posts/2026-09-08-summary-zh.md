---
layout: default
title: "Horizon Summary: 2026-09-08 (ZH)"
date: 2026-09-08
lang: zh
---

> 从 35 条内容中筛选出 7 条重要资讯。

---

**科技新闻**
1. [Asahi Linux 宣布支持 Apple M3 系列 Mac](#item-tech-news-1) ⭐️ 8.0/10
2. [华为发布麒麟 9050 Pro 芯片](#item-tech-news-2) ⭐️ 8.0/10
3. [LG 智能电视隐私争议：屏幕关闭仍记录音频并嗅探局域网](#item-tech-news-3) ⭐️ 7.0/10
4. [CERN 从 CentOS Linux 迁移至 Debian](#item-tech-news-4) ⭐️ 7.0/10
5. [用 RSEQ 操作修复 TCMalloc 在 Linux 6.19 的回归](#item-tech-news-5) ⭐️ 7.0/10
6. [最高法发布 AI 纠纷司法解释，明确换脸与算法杀熟责任](#item-tech-news-6) ⭐️ 7.0/10

**科技博客**
1. [LLM 应用错误处理的韧性设计](#item-tech-blog-1) ⭐️ 6.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [Asahi Linux 宣布支持 Apple M3 系列 Mac](https://lwn.net/Articles/1092768/) ⭐️ 8.0/10

Asahi Linux 项目宣布已将 Apple M3 系列芯片的支持加入其安装程序。官方称，M1/M2 机器上可用的大部分功能现在在 M3 上也能工作，包括摄像头、内置麦克风、USB（最高支持 USB 3 10Gb/s）、包括 AV1 在内的硬件视频解码、WiFi 和蓝牙。目前主要例外仍是完整的 DCP 支持和 GPU，官方明确表示现在不要期待有高性能或低功耗的 3D 加速体验。该公告还提到博客中有其他 M3 支持的限制说明。

rss · LWN.net · 9月7日 12:25

**「背景」** Asahi Linux 是一个致力于将 Linux 移植到 Apple Silicon（M1 及后续芯片）Mac 上的项目，此前已支持 M1 和 M2 系列的大多数机型，并计划逐步扩展到未来芯片。Apple 的 M3 系列是继 M1、M2 之后的新一代 SoC。此次公告意味着 Asahi Linux 安装程序现已加入 M3 系列芯片支持，使这些 Mac 能够安装并运行 Linux，尽管仍缺少完整的 GPU 加速支持。

**「影响」** 对 M3 系列 Mac 用户来说，最直接的变化是可以通过 Asahi 安装程序运行 Linux，但当前阶段应避免依赖 GPU 的 3D 加速工作负载，因为其性能和功耗表现尚不理想。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://en.wikipedia.org/wiki/Asahi_Linux">Asahi Linux - Wikipedia</a></li>
<li><a href="https://asahilinux.org/about/">About - Asahi Linux</a></li>
<li><a href="https://appleinsider.com/articles/26/09/06/asahi-linux-rolls-out-support-for-m3-apple-silicon">Asahi Linux rolls out support for M3 Apple Silicon</a></li>

</ul>
</details>

**标签**: `#Asahi Linux`, `#Apple Silicon`, `#Linux`, `#M3`, `#Hardware Support`

---

<a id="item-tech-news-2"></a>
### [华为发布麒麟 9050 Pro 芯片](https://www.news.cn/20260907/adf46c5c003240d28cc3cf6de54f9b5f/c.html) ⭐️ 8.0/10

华为 9 月 7 日在广州发布 Mate XT 2 三折叠手机，并首次为其搭载麒麟 9050 Pro 芯片。该芯片采用逻辑折叠技术，在单芯片内分层排布逻辑单元，并增设垂直互联通道，官方称信号传输路径更短、时延更低、性能更好。这是继华为 Mate40 系列全球发布会后，华为时隔六年再次在旗舰发布会上推出全新麒麟芯片。目前尚无第三方独立的技术拆解与跑分数据验证这些指标。

telegram · zaihuapd · 9月7日 08:20

**「背景」** 华为上一次在旗舰手机发布会上推出全新麒麟芯片，还要追溯到约六年前搭载麒麟 9000 的 Mate40 系列。此次发布的麒麟 9050 Pro 是继任者，据称首次在单芯片内将逻辑单元做分层立体排布，并增设垂直互联通道来缩短信号传输路径，从而降低时延、提升性能；公开报道称其综合性能较前代提升约 42%，并用于 Mate XT 2 三折叠手机上。

**「影响」** 对华为旗舰手机用户和半导体行业而言，该芯片若经独立验证，将代表华为在高端移动处理器领域时隔六年的回归，并可能通过三维堆叠设计改善性能与功耗；但目前尚无第三方基准或量产细节佐证。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://nokiapoweruser.com/huawei-mate-xt-2-trifold-kirin-9050-pro-launch/">Huawei Launches Mate XT 2 Tri-Fold with Kirin 9050 Pro ...</a></li>
<li><a href="https://english.news.cn/20260907/566d283cf6704be9879f7a27506b9d38/c.html">Huawei unveils high-performance Kirin 9050 Pro chip</a></li>

</ul>
</details>

**标签**: `#hardware`, `#semiconductors`, `#Huawei`, `#chip-design`, `#mobile-computing`

---

<a id="item-tech-news-3"></a>
### [LG 智能电视隐私争议：屏幕关闭仍记录音频并嗅探局域网](https://www.youtube.com/watch?v=6IFVTcM28KA) ⭐️ 7.0/10

一则新闻报道和社区讨论指出，LG 智能电视在屏幕关闭状态下仍可能记录音频，并扫描本地网络中的设备，从而引发重大隐私担忧。报道基于 NotebookCheck 的测试，称这些行为与 LG 服务条款中要求用户自行获得第三方同意等严苛条款并存。事件凸显了智能电视作为 IoT 设备在数据采集与联网监控方面的风险，也促使消费者重新审视 LG 电视的语音识别与网络功能。标题中提到的“216M”通常被理解为涉及约 2.16 亿台智能电视，但该数字的来源和具体影响范围仍有待进一步核实。

hackernews · treve · 9月7日 00:22 · [社区讨论](https://news.ycombinator.com/item?id=49592375)

**「背景」** 智能电视厂商常通过语音助手、内容推荐和广告服务收集用户数据，LG 电视使用 webOS 系统并提供语音识别功能。部分用户为保护隐私会选择拒绝服务条款并禁用网络功能，但默认情况下设备联网时会持续与厂商服务器通信。此次讨论涉及的 LG 服务条款还要求用户通知并取得屋内其他人士的同意。

**「影响」** 对使用默认设置并联网的 LG 智能电视用户而言，这一披露意味着他们的语音环境和局域网内其他设备信息可能被采集并传输至 LG 或第三方，且用户可能需要承担向访客告知的法定义务。具体数据处理范围、是否涉及第三方共享等仍待 LG 官方说明。

**「社区讨论」** 评论者普遍认为这些做法“疯狂”且可能违反多方监听法律，有人晒出 LG 苛刻的服务条款，强调用户必须通知屋内的第三方；也有长期使用者表示自己第一天就拔掉了 WiFi/BT 芯片或一直禁用网络功能，并因此曾感到被朋友嘲笑，最终却证明谨慎是有道理的。

**标签**: `#privacy`, `#smart TV`, `#LG`, `#IoT security`, `#surveillance`

---

<a id="item-tech-news-4"></a>
### [CERN 从 CentOS Linux 迁移至 Debian](https://lwn.net/Articles/1092512/) ⭐️ 7.0/10

据 LWN 报道，CERN 正计划将其部分系统从 CentOS Linux 迁移到 Debian。这一话题是 MiniDebConf Winterthur 2026 上一场主题演讲的内容，由 CERN 员工 Federico Vaga 和 Nikos Tsipinakis 于 2026 年 8 月 30 日介绍。CERN 的加速器控制系统高度定制且对稳定性要求极高，涉及约 2,200 台控制计算机和约 17,000 台设备；此前该系统曾基于 Scientific Linux 和 CentOS Linux。在 Red Hat 宣布以 CentOS Stream 取代传统的 CentOS Linux 后，CERN 评估了包括 CentOS Stream 9 在内的 RHEL 衍生方案，文章指出其迁移目标是 Debian。演讲的视频和幻灯片已公开。

rss · LWN.net · 9月7日 16:57

**「背景」** CentOS Linux 曾是 Red Hat Enterprise Linux（RHEL）的免费重建版本，许多追求稳定兼容性的机构都采用它。CERN 曾与 Fermilab 合作维护 Scientific Linux，后转向使用上游的 CentOS Linux 以减少自行维护成本；当 Red Hat 将开发重点转向滚动发布的 CentOS Stream 后，CERN 需要为高度依赖稳定周期的加速器控制系统寻找新的发行版。Debian 是一个以稳定性著称、由社区维护的通用 Linux 发行版，常被部署在需要长期可预测运维的基础设施中。

**「影响」** 此次迁移将直接改变 CERN 约 2,200 台加速器控制计算机的操作系统基础，相关系统管理员需要把基于 RHEL 衍生的部署与维护流程调整到 Debian 环境，并重新验证自定义 PCI 等硬件设备的兼容性。

**标签**: `#Debian`, `#CentOS`, `#migration`, `#CERN`, `#Linux`

---

<a id="item-tech-news-5"></a>
### [用 RSEQ 操作修复 TCMalloc 在 Linux 6.19 的回归](https://lwn.net/Articles/1092555/) ⭐️ 7.0/10

Linux 6.19 合入的 restartable sequences（RSEQ）性能优化移除了对 struct rseq 中 cpu\_id\_start 字段的无条件设置，破坏了 TCMalloc 依赖该字段被内核重置来检测线程中断的未文档化用法，造成回归。Olivier Dion 提出为 RSEQ API 增加“RSEQ operations”机制：用户空间通过 prctl\(\) 的 PR\_RSEQ\_OP\_REGISTER/UNREGISTER 注册操作，内核在每次返回用户空间时执行 RSEQ\_OP\_RESET 或按 CPU/虚拟 CPU ID 步进的写操作，从而在不让未使用该特性的线程付出性能代价的前提下恢复 TCMalloc 所需行为。该补丁把操作节点链表留在用户空间内存，总数上限为 2048，目前仍处于 RFC 阶段，尚未收到大量评审意见。提案刻意避开需要 CAP\_BPF 的 BPF 方案，但已有维护者担心它会逐渐演变成另一个字节码解释器。

rss · LWN.net · 9月7日 14:33

**「背景」** 可重启序列是一种内核与用户空间共享 struct rseq 的机制，用户空间可以执行无锁操作，若在操作期间被抢占，内核会通知其重新执行；cpu\_id\_start 字段由内核维护并应视为只读。TCMalloc 却向该字段写入哨兵值，并通过内核将其重置为有效 CPU 号来感知线程执行被打断；6.19 的 RSEQ 优化不再无条件设置该字段，因此破坏了这一技巧，内核目前需为旧 API 使用者保留兼容行为，造成代码复杂度和性能损失。

**「影响」** 若该 API 被合入，TCMalloc 将可迁移到当前 RSEQ 接口，恢复与 glibc 的兼容性，并消除现有兼容路径带来的代码复杂度和性能损失；由于补丁仍处 RFC 阶段，最终接口形态和是否合入尚不确定。

**标签**: `#Linux kernel`, `#TCMalloc`, `#restartable sequences`, `#memory allocation`, `#performance`

---

<a id="item-tech-news-6"></a>
### [最高法发布 AI 纠纷司法解释，明确换脸与算法杀熟责任](https://www.cnr.cn/news/20260907/t20260907_527806795.shtml) ⭐️ 7.0/10

最高人民法院于 9 月 7 日发布人工智能纠纷案件司法解释，共 5 部分 24 条，聚焦 AI 换脸、算法杀熟、冒充他人代言、自动驾驶和知识产权等问题。解释明确，未经同意利用 AI 制作可识别的人脸、声音等可能构成人格权侵权；算法价格歧视侵害权益的应承担责任；AI 冒充他人代言诱导消费的，可依法支持惩罚性赔偿请求。此外，解释还依法规制利用人工智能实施“网络开盒”“人肉搜索”等侵害自然人隐私权的行为。这一司法解释为 AI 相关民事纠纷提供了更明确的法律依据。

telegram · zaihuapd · 9月7日 09:32

**「背景」** 此前最高人民法院于 2022 年 12 月发布《关于规范和加强人工智能司法应用的意见》，主要规范法院自身运用人工智能技术、建设智慧法院，并未系统规定 AI 换脸、算法杀熟等外部应用场景下的侵权责任。该文件之后，人工智能技术在商业和社会场景中引发的纠纷缺少统一的司法解释口径。此次发布的 24 条解释将 AI 生成内容、算法决策等行为纳入人格权、消费者权益和隐私保护的裁判框架，为法院处理相关民事诉讼提供了更明确的依据。

**「影响」** 该司法解释将直接约束 AI 深度合成、算法定价及自动化决策相关产品的开发与运营，相关企业和开发者需要重新评估合规风险，尤其是涉及人脸、声音处理及用户画像的场景，并需在技术部署中加强授权管理和算法透明度。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://ipc.court.gov.cn/zh-cn/news/view-2131.html">最高人民法院发布《关于规范和加强人工智能司法应用的意见》 - 最高人民法院知识产权法庭</a></li>

</ul>
</details>

**标签**: `#AI regulation`, `#deepfakes`, `#algorithmic discrimination`, `#privacy`, `#China`

---

## 科技博客

<a id="item-tech-blog-1"></a>
### [LLM 应用错误处理的韧性设计](https://blog.bytebytego.com/p/how-to-deal-with-errors-and-failures) ⭐️ 6.0/10

rss · ByteByteGo · 9月7日 15:31

**「背景」** 作者指出，LLM 应用与普通软件的关键差异在于输出是概率性的：同一提示可能每次都不同，且 API 请求即便返回成功，结果也可能不可用甚至完全错误。因此，除网络超时等技术失败外，应用还必须处理“技术上成功、语义上失败”的独特类别。

**「方案」** 作者给出的核心方法是先分类失败再行动：瞬时错误（网络问题、限流 429、部分 5xx）可用指数退避与抖动重试有限次数；永久错误（凭据无效、非法输入）应报警而不是重试；语义错误（错误 JSON、幻觉信息、违反业务规则）需要结构化输出、校验、修复或人工介入。系统层面可借用传统韧性手段：按降级链依次使用主模型、备用模型、缓存或转人工，并尽量让备用路径不依赖同一供应商；断路器通过开、半开、闭三态避免持续请求压垮故障服务；速率限制、并发控制和队列防止突发请求耗尽配额。作者特别强调工具调用中的部分成功与幂等性：若支付成功但确认丢失，盲目重试可能重复扣款，因此需要状态追踪与幂等键。最难觉察的失败是“合法 JSON、语气自信、内容错误”的幻觉响应，它不会抛出异常，只能靠额外校验、可信数据源或人工审查来拦截。

**「启示」** 作者的结论是：LLM 应用不能把模型当作普通组件，而应把语义正确性与系统可用性一起纳入韧性设计，先对失败分类，再配合重试、降级、断路器等传统方法，否则看似成功的错误响应会直接穿透应用。

**标签**: `#LLM applications`, `#error handling`, `#resiliency`, `#retries`, `#circuit breakers`

---