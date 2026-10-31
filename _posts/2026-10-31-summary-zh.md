---
layout: default
title: "Horizon Summary: 2026-10-31 (ZH)"
date: 2026-10-31
lang: zh
---

> 从 35 条内容中筛选出 10 条重要资讯。

---

**科技新闻**
1. [Azure 曝出五条完整跨租户入侵路径](#item-tech-news-1) ⭐️ 8.0/10
2. [Cursor 扩展市场短暂出现带 SSH 后门的 Claude Code 扩展](#item-tech-news-2) ⭐️ 8.0/10
3. [Linux 7.4 移除 C 版 Binder，Rust 实现成为必需](#item-tech-news-3) ⭐️ 8.0/10
4. [Linux 多路径 TCP 曝可远程触发的释放后使用漏洞](#item-tech-news-4) ⭐️ 8.0/10
5. [Tangled 发布基于 AT Protocol 的联邦代码托管平台](#item-tech-news-5) ⭐️ 7.0/10
6. [Northflank 据报遭入侵，社区讨论多租户 SaaS 风险](#item-tech-news-6) ⭐️ 7.0/10
7. [Show HN：约 1GB Qwen 权重内实现可运行的 NES 模拟器](#item-tech-news-7) ⭐️ 7.0/10
8. [Haas 谈 PostgreSQL 19 延期与 LLM 缺陷发现压力](#item-tech-news-8) ⭐️ 7.0/10
9. [Apple 智能首批功能 11 月 4 日在中国启动测试](#item-tech-news-9) ⭐️ 7.0/10

**财经新闻**
1. [DeepSeek 二轮融资报道：募资 1055 亿元，估值超 6155 亿元](#item-finance-news-1) ⭐️ 8.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [Azure 曝出五条完整跨租户入侵路径](https://www.binarysecurity.no/posts/2026/10/one-root-case) ⭐️ 8.0/10

一篇 Binary Security 安全研究文章列出 Azure 的五条完整跨租户入侵路径；随附讨论重点质疑管理员同意（admin consent）回调伪造，并提到路径遍历和 IDOR 类问题。文章面向 Azure 租户管理员和开发者，但当前材料没有给出各路径的利用前提、受影响服务或微软修复状态，因此这些说法仍需以原报告和厂商确认为准。

hackernews · swq115 · 10月30日 10:06 · [社区讨论](https://news.ycombinator.com/item?id=50301854)

**「背景：Azure 多租户隔离与 API Connection 架构」** Azure 的多租户模型依靠租户 ID 区分不同客户及其资源；一旦租户间的隔离检查出现缺口，攻击者就可能以自己租户的身份触达其他客户的数据。据该文所述，作者此前在系列前作（“Part 1”与《Full Cross-Tenant Compromise》）中已依据微软文档梳理过 API Connection 的架构，本次五个跨租户路径正是建立在这一架构分析之上。

**「影响」** 对使用管理员同意流程的 Azure 租户，评论者提出的具体风险是：攻击者只要知道另一客户的租户 ID 就能伪造回调，因此租户 ID 不能被当作认证或授权秘密。由于材料未说明微软是否已修复，受影响组织应先向微软确认状态，并检查同意回调是否独立校验来源。

**「社区讨论」** 评论中最具体的技术质疑集中在 adminconsent：undoch 称只要知道其他客户的租户 ID 就能伪造回调，并认为文档中的警告不能替代可用的用户认证方式。另有评论者推测路径遍历和 IDOR 可能自相关能力推出以来就存在，并把“给资源名加随机性”的建议与之联系起来，但这只是猜测。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.binarysecurity.no/posts/2026/10/one-root-case">Azure &#x27; s Weakest Link - Five Full Cross - Tenant Compromises</a></li>

</ul>
</details>

**标签**: `#Azure`, `#cloud security`, `#cross-tenant vulnerabilities`, `#vulnerability research`, `#IDOR`

---

<a id="item-tech-news-2"></a>
### [Cursor 扩展市场短暂出现带 SSH 后门的 Claude Code 扩展](https://phorion.io/blog/offical-claude-code-vsx-compromise/) ⭐️ 8.0/10

10 月 29 日，Cursor 扩展市场短暂上架了被篡改的 \`Anthropic.claude-code 2.1.313\`；Cursor 称该版本并非 Anthropic 开发，最多 5,000 名用户受影响。该扩展会收集主机信息，并向 \`~/.ssh/authorized\_keys\` 追加标记为 \`svc-telemetry\` 的攻击者公钥，进而尝试建立长期 SSH 后门，但 Cursor 表示多数主机因需要管理员权限而未能建成隧道。Cursor 已下架该版本、暂时关闭整个市场、轮换密钥后重新开放，并称攻击者服务器已下线；Anthropic 表示其官方发布渠道和系统未受影响，事件仅涉及 Cursor 用户。

hackernews · \_chall · 10月30日 07:09 · [社区讨论](https://news.ycombinator.com/item?id=50300683)

**「背景」** VS Code 扩展以开发者本人的权限运行，可以读写本地文件、执行命令，因此扩展市场长期被视为软件供应链攻击的高价值入口。Horizon 5 月 21 日的日报曾记录，GitHub 确认一名员工因安装恶意 VS Code 扩展而导致约 3,800 个内部仓库被未授权访问，说明这类攻击已有先例而非理论风险。Cursor 的扩展市场基于 Open VSX 提供 VS Code 扩展，第三方可通过该渠道分发以厂商命名空间标识的包，本次被篡改的 Anthropic.claude-code 即由此而来，而非 Anthropic 官方渠道。

**「影响」** 在暴露窗口安装过该版本的 Cursor 用户应按公告检查 \`~/.ssh/authorized\_keys\` 是否出现 \`svc-telemetry\` 条目；即使隧道因权限不足未建立，也不能排除公钥已被写入，发现后应按受影响主机处理并审查 SSH 访问。

**「社区讨论」** Anthropic 员工 felixrieseberg 在评论中澄清，这不是 Anthropic 系统或员工电脑被攻破，而是攻击者利用 Cursor 市场权限发布了篡改副本；另有评论者建议 Anthropic 暂时下架官方扩展，直到 Cursor 修复发布流程。也有评论者贴出 Reuters 报道的时间窗口和 Cursor 公告中的检测命令。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.bleepingcomputer.com/news/security/github-confirms-breach-of-3-800-repos-via-malicious-vscode-extension/">2026-05-21 — GitHub confirms breach of 3,800 repos via malicious VSCode extension</a></li>

</ul>
</details>

**标签**: `#supply-chain-security`, `#ai-coding-tools`, `#vs-code-extension`, `#security-incident`, `#cursor-marketplace`

---

<a id="item-tech-news-3"></a>
### [Linux 7.4 移除 C 版 Binder，Rust 实现成为必需](https://lwn.net/Articles/1102982/) ⭐️ 8.0/10

在 Kangrejos 2026 的演讲中，Carlos Llamas 宣布删除 Android Binder 驱动的 C 实现；会后移除补丁已并入 Linux 7.4 合并窗口，因此从 7.4 起 Binder 只保留 Rust 实现。该迁移历时五年多，Rust 版沿用相同算法，但重点处理尾延迟和锁竞争，并通过将部分操作移出锁、改用自旋锁解决优先级反转问题。旧稳定内核仍保留 C Binder 并继续接收安全修复，7.3 被指定为 2026 年的长期支持版本。由于部分厂商钩子无法由 Rust 版完全复现，许多 Android 厂商需先更新代码才能迁移。

rss · LWN.net · 10月30日 17:46

**「背景」** Binder 自 2008 年进入内核以来一直是 Android 的主要进程间通信机制，也因攻击面大而成为长期的安全和维护负担；正因如此，内核社区从 2021 年起着手用 Rust 重写，首个公开版本到 2023 年才出现。Horizon 2 月 23 日的日报曾报道，Linux 7.0 已结束 Rust 的实验阶段，使其成为内核的永久组成部分；这意味着在 C 版 Binder 被删除前，Rust 已具备内核正式组件的身份。

**「影响」** 对 Android 设备厂商而言，停留在旧稳定内核可暂时继续使用 C Binder，但一旦升级到 7.4 或更新内核，就必须适配 Rust Binder 并处理厂商钩子无法完全复现的问题；使用 GCC 构建内核的发行版还需面对 Rust 侧目前依赖 LLVM 的工具链安排。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://t.me/zaihuapd/39806">2026-02-23 — Linux 7.0 ends Rust&#x27;s experimental phase, establishing it as a permanent kernel component.</a></li>

</ul>
</details>

**标签**: `#Linux kernel`, `#Rust`, `#Android Binder`, `#IPC`, `#Kangrejos`

---

<a id="item-tech-news-4"></a>
### [Linux 多路径 TCP 曝可远程触发的释放后使用漏洞](https://lwn.net/Articles/1104192/) ⭐️ 8.0/10

Linux 内核多路径 TCP（MPTCP）中被披露一个可远程触发的释放后使用漏洞 CVE-2026-98432：攻击者可让重传 SYN 包的响应与另一线程中的连接建立同时发生，使第一个线程在第二个线程已释放连接选项结构后仍访问该结构，从而泄露内核内存，或造成缓冲区溢出并写入攻击者控制的数据。上游修复提交（e3f33b0a1d89）改为仅在 RCU 宽限期结束后才释放该结构。Anthropic 于 10 月 27 日公开该漏洞，Go 安全团队于 10 月 29 日提示，用 Go 编写的程序默认使用多路径 TCP。受影响的仅是开启了 MPTCP 监听器的系统；各发行版何时提供已打补丁的内核尚不清楚，来源摘要也未说明是否已出现实际利用。

rss · LWN.net · 10月30日 15:45

**「背景：MPTCP 与释放时机」** 多路径 TCP（MPTCP）是 TCP 的扩展，允许一条连接同时经由多个网络接口传输；只有在系统启用并监听 MPTCP 时，才会走进相关内核代码路径。该漏洞源于竞态条件：一个线程处理重传 SYN 的响应，另一个线程同时在完成连接建立并释放连接的选项结构，前者随后仍访问已释放的内存，形成 use-after-free。修复办法是把释放推迟到 RCU 宽限期之后，确保仍可能读取该结构的线程都已退出。

**「影响」** 对运行受影响内核且开放多路径 TCP 监听的主机，攻击者无需本地权限或用户交互，即可通过 IPv4 TCP 触发内核内存破坏或系统崩溃；Red Hat 将该漏洞列为 RHEL 的 Critical 级，第三方评估给出 CVSS 9.8。Go 安全团队称 Go 程序默认使用多路径 TCP，因此运维方应排查相关监听端口，并尽快升级到发行版提供的已修复内核；在补丁可用前，减少不必要的 MPTCP 暴露可降低风险。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://access.redhat.com/security/cve/cve-2026-98432">CVE-2026-98432 - Red Hat Customer Portal</a></li>
<li><a href="https://securityarsenal.com/blog/cve-2026-98432-critical-linux-kernel-tcp-vulnerability-cvss-98-detection-and-remediation-guide">CVE-2026-98432: Critical Linux Kernel TCP Vulnerability (CVSS ...</a></li>
<li><a href="https://aviatrix.ai/threat-research-center/linux-kernel-tcp-flaw-98-cvss-cve-2026-98432-ubuntu-rhel/">CVE-2026-98432: Linux Kernel TCP 9.8 CVSS Flaw Hits Ubuntu ...</a></li>

</ul>
</details>

**标签**: `#Linux kernel`, `#security vulnerability`, `#multipath TCP`, `#remote code execution`, `#use-after-free`

---

<a id="item-tech-news-5"></a>
### [Tangled 发布基于 AT Protocol 的联邦代码托管平台](https://tangled.org/blog/forge/) ⭐️ 7.0/10

Tangled 面向开发者发布了基于 AT Protocol 的联邦代码托管平台。联合创始人称，团队已稳定 AT Protocol lexicon、全面重构架构与界面，并加入组织支持；整套服务栈或其中部分组件的自托管也已简化。私有仓库计划在未来几周推出。有评论引用报道称，Tangled 已完成 380 万欧元融资。

hackernews · zlliang · 10月30日 15:44 · [社区讨论](https://news.ycombinator.com/item?id=50305573)

**「背景」** Tangled 在 2026 年 3 月宣布 380 万欧元种子轮时已说明其基于 AT Protocol 构建，并已提供 stacked PR 等功能。Horizon 2026 年 4 月 30 日的日报还报道过 Tangled 提出的“代码托管平台联邦”设想，即用 ForgeFed 等现有协议连接不同 forge；此次发布则是该项目的重构版本，称已稳定 AT Protocol lexicons、重构架构和 UI，并支持自托管和组织。

**「影响」** 对打算自托管的团队，联合创始人表示可以运行完整服务栈，也可以只部署部分组件；但私有仓库尚未可用，需要它的组织要等未来几周的推出。

**「社区讨论」** 有评论者计划把侧项目从自托管 Gitea 迁到 Tangled，用其承载代码、发布和潜在 CI，同时保留 GitHub 用于发现、备份和命名空间占位，但还在等 git-bug 的 Tangled 桥接。另有反馈认为首页和时间线信息过密、个人页活动图可以简化，并有人追问已定稿的 lexicon 是否会把 issue、PR 和评论记录从用户范围移到仓库范围，这条追问在提供的讨论中未见答复。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://blog.tangled.org/federation/">2026-04-30 — Proposal for a Federation of Forges</a></li>
<li><a href="https://blog.tangled.org/seed/">Announcing our €3,8M seed round — Tangled&#x27;s Blog</a></li>

</ul>
</details>

**标签**: `#federated code forge`, `#AT Protocol`, `#open-source hosting`, `#self-hosting`, `#Git collaboration`

---

<a id="item-tech-news-6"></a>
### [Northflank 据报遭入侵，社区讨论多租户 SaaS 风险](https://status.northflank.com/) ⭐️ 7.0/10

Northflank 据报遭到安全入侵，但现有材料未披露入侵方式、受影响客户范围、客户代码或数据是否泄露，也没有 Northflank 的官方确认或修复时间表。对依赖其多租户 SaaS 基础设施的开发和运维团队而言，目前能确定的只是事件已进入公开讨论，具体风险仍需等待厂商说明。

hackernews · js4ever · 10月30日 15:10 · [社区讨论](https://news.ycombinator.com/item?id=50305025)

**「背景：Northflank 与其状态页」** Northflank 是一个面向开发者的多租户平台即服务（PaaS），用于构建和托管容器、批处理任务与数据库，因此其控制面一旦被攻破，就可能波及客户的环境变量与密钥，这正是评论中担忧的来源。第三方监测站点 Pingoru 依据官方状态页统计，截至 2026 年 9 月 Northflank 今年共记录了 8 起事件，状态页历史中可见的条目多为常规运维问题（例如 Let&\#x27;s Encrypt 证书创建报错已解决），而本次条目本身只给出状态页链接，未提供任何关于入侵方式、影响范围或数据是否外泄的技术细节。

**「影响」** 对把环境变量和部署密钥托管在 Northflank 上的团队，最直接的后果是需要把“供应商被攻破”纳入密钥轮换和最小权限预案；但材料没有说明 Northflank 是否访问客户代码、二进制或环境变量，因此无法判断轮换的紧迫性。

**「社区讨论」** 评论中，jonathaneunice 称自 9 月以来至少有六起针对多租户即服务厂商的快速攻击，并把 PingCAP/TiDB、Fireworks AI、Zeabur、OpenCode Console、Railway 和 Northflank 列入其中，称之为“全面信息安全紧急事件”；这是他个人的说法，材料未独立确认。dangoodmanUT 则分享把环境变量加密、将解密密钥硬编码进代码的做法，认为供应商被攻破时有用，但承认本不应如此，并预计企业客户会因此回流超大规模云厂商。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://status.northflank.com/history/1">Notice history - Northflank - Status</a></li>
<li><a href="https://pingoru.io/providers/northflank">Is Northflank Down? Outages, Status ... — September 2026 · Pingoru</a></li>

</ul>
</details>

**标签**: `#security breach`, `#cloud infrastructure`, `#SaaS`, `#infrastructure security`, `#multi-tenant`

---

<a id="item-tech-news-7"></a>
### [Show HN：约 1GB Qwen 权重内实现可运行的 NES 模拟器](https://github.com/dbreunig/nesformer) ⭐️ 7.0/10

Show HN 项目 nesformer 据称在约 1GB 的 Qwen 模型权重中实现了一个可运行的 NES 模拟器，面向想验证“LLM 即虚拟机”的开发者。它把 NES 的 CPU 与内存状态放进模型的前向计算，而不是交给传统解释器；评论中引用的数据称其速度比真实主机慢 150–290 倍。社区评论还指出，项目连 RAM 也在模型内模拟（据称借助 gated DeltaNet 架构），因此不只是模拟 CPU。

hackernews · dbreunig · 10月30日 16:40 · [社区讨论](https://news.ycombinator.com/item?id=50306442)

**「背景」** 这一项目沿用了 Qwenputer 的思路：据其仓库和博客，Qwenputer 把一台 CHIP-8 机器——CPU、大数运算库和内存——写成 transformer 层并附加到 Qwen 3.5-4B 原始权重上，同时还演示了在模型内构建可运行的 RISC-V CPU，其关键在于 Qwen 3-Next/3.5 多数注意力层采用 Gated DeltaNet，每个 head 的状态矩阵可持续保存并更新状态。nesformer 的作者在评论中说明，他先让模型阅读 Qwenputer 的文章和相关源码，再要求它探索能否用同样方式在权重中模拟 NES 的芯片与 RAM，以及需要多大的模型。

**「影响」** 对想用 LLM 内部执行程序或工具链的人，这个演示给出的直接约束是：可行性已具备，但 150–290 倍的减速和相应算力开销意味着它目前不能替代真实 NES 模拟器，也不适合交互式负载。若要沿此路线构建 VM，性能与成本是首先需要解决的工程约束。

**「社区讨论」** 评论中，armcat 认为可把小型 VM、Python 解释器和 shell 工具编译进权重，用矩阵运算替代缓慢的外部工具调用；pbohun 和 jacquesm 则强调这更像可行性演示，150–290 倍减速与算力差距说明确定性程序仍高效得多。cafebeen 还指出，项目连 RAM 也在模型内模拟，而不只是 CPU，并称这部分通过 gated DeltaNet 架构实现。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://github.com/divagr18/qwenputer">GitHub - divagr 18/ qwenputer : A computer, compiled into the weights ...</a></li>
<li><a href="https://divagr.com/blog/qwenputer">Qwenputer : a fully functioning, deterministic RISC-V CPU inside...</a></li>

</ul>
</details>

**标签**: `#LLM emulation`, `#Nintendo Entertainment System`, `#Qwen`, `#model weights`, `#Show HN`

---

<a id="item-tech-news-8"></a>
### [Haas 谈 PostgreSQL 19 延期与 LLM 缺陷发现压力](https://lwn.net/Articles/1104210/) ⭐️ 7.0/10

PostgreSQL 19 的发布出现延迟。PostgreSQL 开发者 Robert Haas 表示，这次延期本身并不特别令人担忧，它直接来自项目对质量的关注；他真正担心的是长期维护能力。Haas 指出，LLM 有能力发现人类四十年都未能找到的缺陷，维护者可能永远追不上，这会威胁 PostgreSQL 的持续创新；他称自己和许多人正在努力寻找答案，但尚未提出具体方案。

rss · LWN.net · 10月30日 16:52

**「背景」** 9 月 11 日的 Horizon 日报曾报道，PostgreSQL 19 原定于 2026 年 9 月发布，但后期补丁暴露出异常多的缺陷，项目因此新增了一个 beta；10 月 14 日的 Horizon 日报又记录，核心成员 Peter Eisentraut 称 beta 阶段被撤回的功能异常多，LLM 辅助代码审查让边缘问题被发现得更快，这相当于在功能提交后抬高了有效质量门槛。Haas 此次讨论的延期，正是在这一轮质量排查和功能撤回之后出现的。

**「升级计划与特性预期需调整」** 对计划升级的用户来说，直接影响是 PostgreSQL 19 的正式发布已推迟到大约 11 月 19 日，并且有 8 到 10 项重要特性被从该版本中移除；依赖这些特性的部署需要重新评估升级时间表。Haas 同时指出，LLM 找出数十年遗留缺陷的速度已超出维护者的修复能力，这意味着项目必须在追赶缺陷与继续创新之间做出取舍。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://lwn.net/Articles/1092003/">2026-09-11 — PostgreSQL 19 后期补丁质量引担忧，新增一个 beta</a></li>
<li><a href="https://lwn.net/Articles/1100182/">2026-10-14 — PostgreSQL 19 测试期多项功能被撤回，核心成员归因于 LLM 辅助审查</a></li>
<li><a href="https://www.snowflake.com/en/blog/engineering/postgresql-19-release-delay-feature-reverts/">PostgreSQL 19 Delayed : Key Feature Reversions &amp; Release Updates</a></li>
<li><a href="https://www.theregister.com/databases/2026/10/16/postgres-19-delayed-after-ai-reviewers-find-more-bugs-than-humans-can-fix/5303471">Postgres 19 delayed after AI reviewers find more bugs than humans...</a></li>

</ul>
</details>

**标签**: `#PostgreSQL`, `#LLM bug discovery`, `#open-source maintenance`, `#release management`, `#software quality`

---

<a id="item-tech-news-9"></a>
### [Apple 智能首批功能 11 月 4 日在中国启动测试](https://www.apple.com.cn/newsroom/2026/10/apple-intelligence-features-are-coming-to-users-in-china/) ⭐️ 7.0/10

苹果宣布，Apple 智能首批功能将自 11 月 4 日起随最新的 iOS 开发者 Beta 版在中国开放测试，并计划在 12 月 iOS 27.3 正式发布时向中国用户推出。此次测试包含实时翻译、照片消除和写作工具，但不包含下一代 Siri AI 功能；其他平台的支持需待必要审批后再推出。苹果还与阿里巴巴合作，在 Siri、写作工具和视觉智能中接入千问，面向在中国购买支持 Apple 智能的 iPhone 用户，或设备定位与 Apple 账户国家/地区均设为中国大陆的用户。上述时间与功能范围来自苹果公告，属于已宣布的测试和发布计划，尚非已全面上线的能力。

telegram · zaihuapd · 10月30日 21:44

**「背景」** 苹果为中国市场做本地化准备已有先例：Horizon 8 月 15 日日报援引知情人士称，苹果在阿里巴巴支持下专门训练了面向中国的大语言模型，并预计 Apple Intelligence 将在数月内随 iOS 更新上线。10 月 16 日日报又记录，库克在上海公开表示测试版将在 10 月下旬推出，首批功能不含 Siri AI；本次则把开发者 Beta 测试日期明确到 11 月 4 日，并给出 12 月随 iOS 27.3 正式发布的排期。

**「适用条件与上线节奏」** 中国用户要使用这批功能，需持有支持 Apple 智能的较新 iPhone，且设备定位与 Apple 账户国家/地区均设为中国；报道还指出系统语言需为英文或简体中文。想提前试用者可从 11 月 4 日起通过 iOS 开发者 Beta 版体验，正式版要等到 12 月 iOS 27.3；首批不含下一代 Siri AI，其他平台支持则需待审批。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.reuters.com/business/retail-consumer/apple-trains-its-own-ai-model-china-market-with-alibabas-support-sources-say-2026-08-14/">2026-08-15 — 苹果联手阿里为中国训练专属 AI 大模型，有望成首个获批外企</a></li>
<li><a href="https://jiemian.com/article/15194723.html">2026-10-16 — 库克称 Apple 智能 10 月底在华发测试版，不含 Siri AI</a></li>
<li><a href="https://thenextweb.com/news/apple-intelligence-china-ios-27-3-alibaba-qwen">Apple confirms its AI features reach China in December, with Qwen</a></li>
<li><a href="https://www.unite.ai/apple-brings-first-apple-intelligence-features-to-china-in-ios-27-3/">Apple Brings First Apple Intelligence Features to China in ...</a></li>

</ul>
</details>

**标签**: `#Apple Intelligence`, `#China market`, `#Alibaba Qwen`, `#iOS`, `#AI localization`

---

## 财经新闻

<a id="item-finance-news-1"></a>
### [DeepSeek 二轮融资报道：募资 1055 亿元，估值超 6155 亿元](https://www.theinformation.com/articles/behind-deepseeks-16-billion-funding-chinese-tech-titans-state-players) ⭐️ 8.0/10

据 Telegram 帖子援引《The Information》报道，DeepSeek 第二轮融资募得 1055 亿元人民币，估值超过 6155 亿元人民币，近 30 家投资方参与；其中具有国资背景的投资者出资约占 27%，而首轮（今年 6 月完成，规模约 510 亿元）这一比例约为 2%。

telegram · zaihuapd · 10月30日 12:37

**「背景」** 这轮融资距 DeepSeek 首次融资仅数月：据同一报道，首轮于今年 6 月完成，规模约 510 亿元。

**标签**: `#DeepSeek`, `#AI financing`, `#China tech`, `#state-backed investment`, `#private markets`

---