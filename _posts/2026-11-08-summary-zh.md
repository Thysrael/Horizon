---
layout: default
title: "Horizon Summary: 2026-11-08 (ZH)"
date: 2026-11-08
lang: zh
---

> 从 38 条内容中筛选出 11 条重要资讯。

---

**科技新闻**
1. [MaxxBench – &quot;Nice DeepSWE score. But is it true?&quot;](#item-tech-news-1) ⭐️ 8.0/10
2. [GitHub 公布 Rubicon 高并发 Git 存储架构](#item-tech-news-2) ⭐️ 8.0/10
3. [分析称 macOS 未公开守护进程构建个人知识图谱](#item-tech-news-3) ⭐️ 7.0/10
4. [Coldframe：伪装超市冷柜控制器的 Python 蜜罐](#item-tech-news-4) ⭐️ 7.0/10
5. [Need for Speed Underground 2 online in the browser](#item-tech-news-5) ⭐️ 7.0/10
6. [Asahi Linux 7.3 进度报告：Fedora Asahi Remix 首次同日发布](#item-tech-news-6) ⭐️ 7.0/10
7. [Amutable 操作系统技术概览：默认不含 Shell、SSH 与解释器](#item-tech-news-7) ⭐️ 7.0/10
8. [Claude Code 被指搜索时泄露邮箱，2.1.317 拦截可绕过](#item-tech-news-8) ⭐️ 7.0/10
9. [苹果披露 HALO 人形机器人系统](#item-tech-news-9) ⭐️ 7.0/10

**科技博客**
1. [探访内蒙古 Galaxy：速度、成本与垂直整合](#item-tech-blog-1) ⭐️ 7.0/10

**财经新闻**
1. [软银与 ABB 考虑分拆中国机器人业务以挽救 54 亿美元收购](#item-finance-news-1) ⭐️ 8.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [MaxxBench – &quot;Nice DeepSWE score. But is it true?&quot;](https://maxxbench.unlap.ai/research/why-maxxbench/) ⭐️ 8.0/10

MaxxBench analyzes whether strong DeepSWE scores reflect genuine capability, finding benchmark flaws and signs that smaller models overfit narrow evaluation environments.

hackernews · antiuniverse · 11月7日 17:19 · [社区讨论](https://news.ycombinator.com/item?id=50406222)

**标签**: `#LLM benchmarks`, `#DeepSWE`, `#benchmark validity`, `#model overfitting`, `#AI evaluation`

---

<a id="item-tech-news-2"></a>
### [GitHub 公布 Rubicon 高并发 Git 存储架构](https://github.blog/engineering/architecture-optimization/inside-githubs-new-git-storage-architecture/) ⭐️ 8.0/10

GitHub 公布了代号 Rubicon 的新 Git 存储架构，目标是让单个仓库承受大量 AI 智能体并发操作；该架构把 Git 对象存入 Azure Blob Storage，用 Ref-CAS 管理引用状态，并通过虚拟副本处理读写、由后台节点压缩数据包。GitHub 称内部测试中支持 5,000 个智能体同时协作、每秒处理 7,200 次推送，读取延迟保持在较低水平，但这些数字来自厂商内部测试，并非独立测量。该架构目前仅处于有限私有预览，GitHub 表示将逐步扩大推广范围，尚未公布普遍可用时间、定价或 SLA。

telegram · zaihuapd · 11月7日 14:12

**「背景」** Git 仓库传统上把对象打包成 packfile 存放在与计算节点绑定的存储上，引用更新和压缩（repack）也在同一套计算资源上完成，因此写入并发一高，压缩就容易成为瓶颈。据 GitHub 博客介绍，Rubicon 的核心思路是把存储与计算解耦：每次推送只向 Azure Blob Storage 追加一个 pack，压缩改由后台节点在每秒数千次写入的规模下完成。这解释了为什么新架构能承受大量 AI 智能体同时操作同一仓库的写入压力。

**「影响」** 对运行大规模 Git 或 AI 智能体基础设施的团队，短期没有可执行的迁移或兼容性动作：Rubicon 仅处于有限私有预览，GitHub 未说明现有仓库如何接入、是否改变 API 或权限模型，也未给出普遍可用时间。需要做容量规划的团队因此不能把厂商内部测试的 7,200 次/秒当作生产可用指标。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://github.blog/engineering/architecture-optimization/inside-githubs-new-git-storage-architecture/">Inside GitHub &#x27;s new Git storage architecture - The GitHub Blog</a></li>

</ul>
</details>

**标签**: `#git`, `#github`, `#storage-architecture`, `#ai-agents`, `#distributed-systems`

---

<a id="item-tech-news-3"></a>
### [分析称 macOS 未公开守护进程构建个人知识图谱](https://8rank.ai/game/apple-intelligence-personal-knowledge-graph) ⭐️ 7.0/10

一篇针对 macOS 的逆向分析称，系统中存在与 Apple Intelligence 相关、未公开的守护进程。这些守护进程会构建关于用户及其联系人关系的个人知识图谱，并涉及家庭成员分类。文章的核心问题不在于这些进程是否有功能用途，而在于其存在和数据处理缺少面向用户的明确披露，因而难以形成知情同意。现有材料仅包含分析者说法和社区讨论，未包含苹果回应或独立验证。

hackernews · infwhispers · 11月7日 09:46 · [社区讨论](https://news.ycombinator.com/item?id=50403097)

**「背景」** 个人知识图谱是把人物、关系、通讯和位置等实体连成结构化网络的本地数据层，可用于消解语音指令中的人物指代。8rank.ai 的分析称，相关守护进程自 2022 年起存在于 macOS 13 及以上版本，Intel 与 Apple 芯片 Mac 均受影响，并与 Apple Intelligence 的人物语境功能相关；苹果尚未公开说明这些进程的数据来源与用途。

**「影响」** 对 Mac 用户而言，直接后果是隐私判断上的信息不对称：在这类系统进程缺少公开文档的情况下，用户只能依赖第三方逆向分析来评估它们处理了哪些关系数据、用于何处。

**「社区讨论」** 有评论者认为，这类图谱是本地助手理解“哪个 James”或“我的老板”是谁所必需的上下文，属于功能实现的一部分；也有评论者反驳说，关键不在于技术能否做到，而在于对话和关系被系统纳入可检索图谱，会破坏人际交流中“不必逐字记住”的社会默契，并质疑这是否符合苹果宣称的知情同意原则。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://8rank.ai/game/apple-intelligence-personal-knowledge-graph">Anatomy of Apple &#x27;s Personal Knowledge Graph — Eighth Rank</a></li>

</ul>
</details>

**标签**: `#Apple Intelligence`, `#privacy`, `#macOS`, `#personal knowledge graph`, `#reverse engineering`

---

<a id="item-tech-news-4"></a>
### [Coldframe：伪装超市冷柜控制器的 Python 蜜罐](https://github.com/hedgerow-dev/coldframe) ⭐️ 7.0/10

Coldframe 是一个新发布的单文件开源 Python 蜜罐，仅使用标准库，模仿 Danfoss AK-SM 800A 和 Dixell XWEB 的超市制冷控制器界面；作者称两个实例在 Shodan 上被识别为真实设备，而非蜜罐。它依据真实设备的 Shodan 记录对齐 HTTP 头顺序、页面标题、证书字段和 TLS 版本，并能识别 CVE-2025-41450 这个 Danfoss“每日代码”登录绕过，以及针对另外三个 Danfoss CVE 和 XWEB 漏洞的尝试。默认登录会进入带除霜按钮的假仪表盘，以便观察攻击者的下一步操作。作者称两个在线实例运行一天后只看到通用扫描器和 Shodan 爬虫 refrigerator.census.shodan.io；这些结果尚未经过独立验证。

hackernews · hedgerow-dev · 11月7日 17:27 · [社区讨论](https://news.ycombinator.com/item?id=50406292)

**「背景」** 2026 年 10 月 13 日的日报曾报道，法国多家超市连锁遭遇针对联网制冷控制器的网络攻击：攻击者远程触发自动化霜，导致冷柜停机并影响门店运营；路透点名 Intermarché 称有 150 家门店被针对，安全公司 Claroty 的 Team82 此前也披露过 Danfoss 制冷控制器漏洞，但当时报道未确认攻击所利用的具体 CVE。Coldframe 正是以这类真实设备为伪装对象，把 Danfoss AK-SM 800A 与 Dixell XWEB 的界面做成诱捕目标，用来观察攻击者面对“制冷控制器”时实际会做什么。

**「对防守方的实际价值」** 对防守方和安全研究者而言，Coldframe 的直接用途是把 Danfoss AK-SM 800A 与 Dixell XWEB 的暴露面变成可观测的诱捕点：它会标记针对 CVE-2025-41450“当日口令”登录绕过的尝试，并记录提交的口令是否与当天生成值相符；在默认口令登录后，它还会展示带化霜按钮的假仪表盘，从而捕获攻击者的后续动作，而不只是第一次请求。需要保留的限定是，作者称两个实例上线一天只见到通用扫描器和名为 refrigerator.census.shodan.io 的 Shodan 爬虫，因此目前没有证据表明它已观测到真实的定向入侵，要把它当作真实攻击流量的检测依据仍需更长时间和更多实例的部署。

**「社区讨论」** 有评论者提醒，依据 Shodan 数据复制真实设备并不可靠，因为网上同类设备可能本身就是蜜罐，或已遭入侵且页面被替换，并建议作者自行取得一台存在漏洞的设备进行探测；作者则回应称超市通常没有安全团队，补丁、VPN 和强密码应默认由厂商或安装商提供。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.tomshardware.com/tech-industry/cyber-security/unprecedented-cyberattack-cripples-supermarket-fridges-across-europe-as-hackers-activate-automatic-defrosting-delivery-and-store-prices-also-impacted-by-incident">2026-10-13 — 黑客触发欧洲超市冷柜自动化霜</a></li>
<li><a href="https://www.claroty.com/team82/research/freeze-the-controller-defrost-the-food-uncovering-vulnerabilities-in-danfoss-refrigeration-controllers">Freeze the Controller, Defrost the Food: Uncovering... | Claroty</a></li>

</ul>
</details>

**标签**: `#honeypots`, `#ICS security`, `#industrial control systems`, `#open source`, `#Shodan`

---

<a id="item-tech-news-5"></a>
### [Need for Speed Underground 2 online in the browser](https://nfsu2.xyz/) ⭐️ 7.0/10

A browser-based online revival of Need for Speed Underground 2 is drawing significant community interest for its WebGPU-enabled playability and multiplayer features.

hackernews · fluxusars · 11月7日 09:36 · [社区讨论](https://news.ycombinator.com/item?id=50403052)

**标签**: `#WebGPU`, `#browser gaming`, `#game preservation`, `#reverse engineering`, `#online multiplayer`

---

<a id="item-tech-news-6"></a>
### [Asahi Linux 7.3 进度报告：Fedora Asahi Remix 首次同日发布](https://asahilinux.org/2026/11/progress-report-7-3/) ⭐️ 7.0/10

Asahi Linux 的 7.3 进度报告称，Fedora Asahi Remix 已在 Fedora Linux 45 于 11 月 3 日发布当天同步推出，这是该项目首次做到与上游 Fedora 同日发布。报告同时列出仍未补齐的硬件支持，例如 USB-C 外接显示器，并提到有人多次试图利用项目的宽松许可劫持其成果，意在取代项目并将 Apple Silicon 上的 Linux 商业化。上述同日发布是项目自述的交付进展；USB-C 显示器支持缺失和许可担忧仍是报告指出的未解问题。

hackernews · ackyshake · 11月7日 05:20 · [社区讨论](https://news.ycombinator.com/item?id=50401867)

**「背景」** Fedora Asahi Remix 是 Asahi Linux 面向 Apple Silicon Mac 的官方发行版，此前新版本通常晚于上游 Fedora 发布，因此本次与 Fedora 45 同日发布被项目视为首次。Horizon 2026 年 9 月 8 日的日报曾报道，该项目已将 Apple M3 系列支持加入安装器，当时 M1/M2 上大部分功能在 M3 上可用，但完整 DCP 支持与 GPU 3D 加速仍然缺席；此后 M3 支持继续推进，并成为 7.3 进展报告中的一项内容。

**「影响」** 对需要 USB-C 外接显示器的 Apple Silicon 用户，当前 Asahi Linux 仍不是完整替代方案，安装前应核对这一硬件兼容性；不需要该功能的用户则可获得与 Fedora Linux 45 同日发布的 Fedora Asahi Remix 版本。

**「社区讨论」** 评论中，一位长期资助者肯定 Asahi 的进展；另一位用户称 USB-C 外接显示器支持是自己安装前唯一无法妥协的障碍。针对报告提到的许可滥用担忧，有评论者猜测是否指 Omarchy，并质疑项目为何采用 MIT 而非 GPL。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://lwn.net/Articles/1092768/">2026-09-08 — Asahi Linux 宣布支持 Apple M3 系列 Mac</a></li>
<li><a href="https://asahilinux.org/copyright/">Copyright &amp; Reverse Engineering - Asahi Linux Why the licensing change? - lwn.net GitHub - JackDolbs/omarchy-mac: Opinionated Arch/Hyprland ... Asahi Linux GitHub - daniklev/omarchy-asahi: Opinionated Arch/Hyprland ... Asahi Linux 7.3 Report: M3 GA, Partial Thunderbolt, GPL Move</a></li>

</ul>
</details>

**标签**: `#Asahi Linux`, `#Apple Silicon`, `#Linux`, `#Fedora`, `#open source`

---

<a id="item-tech-news-7"></a>
### [Amutable 操作系统技术概览：默认不含 Shell、SSH 与解释器](https://lwn.net/Articles/1105934/) ⭐️ 7.0/10

Lennart Poettering、Michael Vogt 和 Joaquim Rocha 在 Amutable 博客发布了一份详细技术概览，介绍 Amutable Operating System（AOS）及其配套基础设施将采用的设计；LWN 的文章仅链接到这份概览。AOS 采用基于镜像的操作系统（image-based OS）方案，作者称这种方式可以强制执行若干严格的安全属性，并列出七项，其中前两项是：默认不安装 UNIX shell，节点上不提供 SSH 远程访问，默认也不安装 Python、Perl 等常见语言解释器；只有带有 Verity 数据、且签名密钥已列入 Verity keyring 的镜像才能被激活。需要注意的是，这仍是一份面向未来形态的早期架构描述，所给摘录只展示了七项属性中的两项。

rss · LWN.net · 11月7日 09:32

**「背景：什么是镜像式操作系统」** Amutable 的设计属于“镜像式操作系统”（image-based OS）：系统以完整、经过签名的磁盘镜像为单位交付和启动，而不是在运行中的根文件系统上逐个软件包安装和修改。因此更新是整体替换镜像并可回退，系统完整性则依赖类似 dm-verity 的校验数据在激活时验证——这正是 AOS 强调“只允许签名镜像激活”的前提。这种架构也让默认精简成为可能：不含 shell、SSH 和语言解释器的镜像更小，暴露给攻击者的入口也更少。

**「影响」** 按照这一设计，习惯在节点上通过 shell、SSH 或 Python、Perl 脚本进行调试、排障和自动化运维的开发者与管理员，将无法在默认 AOS 节点上沿用这些做法，需要改为围绕签名镜像以及节点之外的访问和工具链来设计流程。概览没有给出可用时间表或迁移细节，现阶段也无法据此判断现有 Linux 工作负载的兼容程度。

**标签**: `#operating systems`, `#Linux security`, `#image-based OS`, `#open source`, `#system architecture`

---

<a id="item-tech-news-8"></a>
### [Claude Code 被指搜索时泄露邮箱，2.1.317 拦截可绕过](https://github.com/anthropics/claude-code/issues/107757) ⭐️ 7.0/10

有开发者投诉称，Claude Code 会把用户登录邮箱填入联网请求并发送，导致其每天收到大量诈骗邮件。Anthropic 工程师表示，这一做法最初是为了避免 Claude 乱填作者名而将登录邮箱放入模型上下文；相关问题早在今年 7 月就有人报告，邮箱曾被发送至 Wikipedia、美国证券交易委员会等站点。2.1.317 版已加入拦截，但可用 Python 脚本绕过，公司计划在下一版本从模型上下文中移除登录邮箱。

telegram · zaihuapd · 11月7日 08:09

**「背景：邮箱为何进入请求头」** 这一泄露源自更早的一项设计取舍：为解决 Claude 在生成内容时乱填作者名的问题，Anthropic 把用户的登录邮箱放进了模型上下文，而该邮箱随后随联网请求出现在 User-Agent 等字段中，被发往 Wikipedia、美国证券交易委员会等第三方站点。也就是说，邮箱并非被外部攻击窃取，而是作为产品内部上下文的一部分被主动带出。

**「影响」** 在下一版本发布前，使用 2.1.317 的用户仍不能把该拦截视为完整防护：通过 Python 脚本发起的联网请求可绕过限制，登录邮箱可能继续暴露给搜索目标站点并带来垃圾或诈骗邮件。受影响用户和组织应把登录邮箱视为可能已暴露给第三方站点，而不应仅依赖当前版本的拦截。

**标签**: `#Claude Code`, `#privacy leak`, `#AI coding tools`, `#security vulnerability`, `#GitHub issue`

---

<a id="item-tech-news-9"></a>
### [苹果披露 HALO 人形机器人系统](https://weibo.com/1642634100/RqjjGllvw) ⭐️ 7.0/10

据科技博主汇总，苹果研究团队于 11 月 4 日提交至 arXiv 的论文披露了人形机器人控制系统 HALO，并在宇树 G1 上验证了将仿真环境中学到的动作迁移到陌生真实房间执行的能力。该系统分为三层：上层由 Qwen3.6-35B-A3B 负责任务编排，中层由 Qwen3.5-2B 生成动作，底层是经强化学习训练的动作跟踪器。汇总还称团队已公开数据生成、模型训练与部署代码，但该帖未给出论文链接，相关能力尚待独立验证。

telegram · zaihuapd · 11月7日 13:35

**「背景」** 人形机器人把大模型用于控制时，需要让上层模型输出可执行的动作指令，再由底层控制器在真实硬件上闭环执行；仿真训练到真实部署之间的动力学与感知差异，是这类系统的主要门槛。宇树 G1 是宇树公开的人形机器人平台，官方资料称其支持力位混合控制，并可用于模仿与强化学习驱动的运动控制。

**「影响」** 对关注 sim-to-real 的研究者，HALO 的潜在可操作价值在于三层接口可分别复用或替换；但该汇总帖未附论文与代码链接，复现前应先取得原始论文和仓库，核对动作跟踪器的训练细节及在 G1 上的迁移条件。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.unitree.com/g1/">Humanoid robot G 1 _ Humanoid Robot ... | Unitree Robotics</a></li>

</ul>
</details>

**标签**: `#humanoid robotics`, `#robot learning`, `#sim-to-real`, `#Qwen`, `#Apple research`

---

## 科技博客

<a id="item-tech-blog-1"></a>
### [探访内蒙古 Galaxy：速度、成本与垂直整合](https://newsletter.semianalysis.com/p/we-visited-chinas-stargate-in-inner) ⭐️ 7.0/10

rss · SemiAnalysis · 11月7日 19:01

**「背景」** 在美国以 Stargate Abilene 作为 AI 基建象征之际，中国也出现了同等级的超大规模园区，但外界很少能实地看到。SemiAnalysis 作者在 9 月探访内蒙古乌兰察布的 Envision Galaxy 园区，试图用成本、工期和供电数据解释中国数据中心为何建得又快又便宜。

**「方案」** Galaxy 规划 IT 容量最高 800MW，首期 120MW 不到一年交付，作者称成本仅为美国的五分之一，四期均为两家互联网巨头定制。其特点不只是模块化，而是 Envision 的深度垂直整合：自建风电场和专用线路，自产风机叶片与 AESC 储能，设计低压功率模块和 800V 系统，并联合设计预制变电站，使现场接入从约 6 个月降至不到 3 个月。园区还运行 5MW 固态变压器试点，把 10kV 交流直接变成 800V 直流送到机柜，省去低压变压器、UPS 和整流环节；这建立在中国约四分之一数据中心已用直流、而美国约 97%仍用交流 UPS 的基础上。作者同时给出市场背景：租金五年减半至约 40 美元/kW/月（不含电），capex 降至每 MW 不足 300 万美元，内蒙古全包电价约 0.055 美元/kWh。

**「启示」** 作者认为，垂直整合目前带来成本和工期控制，但是否成为持久优势仍未证明；随着电力获取变难和 800V 直流重构供电架构，这类玩家可能获得不同于传统开发商的空间。

**标签**: `#AI datacenters`, `#China infrastructure`, `#vertical integration`, `#datacenter power systems`, `#construction economics`

---

## 财经新闻

<a id="item-finance-news-1"></a>
### [软银与 ABB 考虑分拆中国机器人业务以挽救 54 亿美元收购](https://www.bloomberg.com/news/articles/2026-11-07/softbank-abb-weigh-china-carve-out-to-salvage-robotics-deal) ⭐️ 8.0/10

据报道，软银与 ABB 正考虑将 ABB 机器人业务的中国部分分拆为一家股权结构不同的独立实体，并由软银主导推进，以挽救已被中国外商投资安全审查工作机制办公室本周四叫停的 54 亿美元收购。

telegram · zaihuapd · 11月7日 11:24

**「背景」** 软银此前达成协议，以 54 亿美元收购 ABB 的机器人业务，但中国的外商投资安全审查机制（审查外资并购是否影响国家安全的制度）于本周四否决了这笔交易，双方因此需要重新设计交易结构。

**「影响」** 如果该分拆方案失败，ABB 可能需为该机器人业务另寻买家；出售进程将取决于中国监管是否接受新的股权结构。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.swissinfo.ch/eng/workplace/china-blocks-softbanks-5-4bn-takeover-of-abbs-robotics-division/92331403">China blocks SoftBank ’s $ 5 . 4 bn takeover of ABB ’s robotics division</a></li>
<li><a href="https://www.reuters.com/business/media-telecom/softbank-abb-explore-china-carve-out-salvage-robotics-deal-bloomberg-news-2026-11-07/">SoftBank, ABB explore China carve-out to salvage robotics ...</a></li>

</ul>
</details>

**标签**: `#M&amp;A`, `#China FDI screening`, `#robotics`, `#SoftBank`, `#ABB`

---