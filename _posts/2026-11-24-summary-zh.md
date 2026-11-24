---
layout: default
title: "Horizon Summary: 2026-11-24 (ZH)"
date: 2026-11-24
lang: zh
---

> 从 40 条内容中筛选出 12 条重要资讯。

---

**科技新闻**
1. [英伟达董事会恢复黄仁勋 CEO 职务](#item-tech-news-1) ⭐️ 8.0/10
2. [Ladybird 浏览器发布首个 Alpha，支持 macOS 与 Linux](#item-tech-news-2) ⭐️ 8.0/10
3. [GLM-5.4 发布：首个循环 Transformer 瞄准通用编程](#item-tech-news-3) ⭐️ 8.0/10
4. [Anthropic 关联仓库发布 VP ≠ VNP 论文，尚待验证](#item-tech-news-4) ⭐️ 8.0/10
5. [开发者称 Apple 在九年后将其开源应用移出欧盟 App Store](#item-tech-news-5) ⭐️ 7.0/10
6. [谷歌用模拟互联网测试 Chrome AI 代理](#item-tech-news-6) ⭐️ 7.0/10
7. [Windows Server 2028 默认移除 WoW64，32 位应用需手动装回](#item-tech-news-7) ⭐️ 7.0/10
8. [Codex2api 疑遭供应链投毒，3.1.10–3.1.12 需回滚](#item-tech-news-8) ⭐️ 7.0/10
9. [Meta AI 负责人称超级智能将至并警告控制风险](#item-tech-news-9) ⭐️ 7.0/10

**科技博客**
1. [DoorDash 调度重构：协调与计算分离](#item-tech-blog-1) ⭐️ 6.0/10
2. [cuDSS 1.0：稀疏直接求解器的精度与内存改进](#item-tech-blog-2) ⭐️ 6.0/10
3. [Sirius：为 DuckDB 带来 GPU 加速分析](#item-tech-blog-3) ⭐️ 4.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [英伟达董事会恢复黄仁勋 CEO 职务](https://www.cnbc.com/2026/11/23/nvidia-jensen-huang-ceo.html) ⭐️ 8.0/10

英伟达董事会宣布恢复黄仁勋（Jensen Huang）的首席执行官职务。公司声明称，董事会在决策过程中收到了美国联邦政府高层人士的意见，并据此表示黄仁勋复职不构成国家安全风险。所给材料主要为新闻标题、链接和评论，未包含文章全文，因此董事会此前为何让黄仁勋去职、以及政府以何种方式介入，都没有可核实的细节。

hackernews · jaz · 11月23日 14:00 · [社区讨论](https://news.ycombinator.com/item?id=50611576)

**「此前的人事风波」** Horizon 11 月 12 日的日报曾记录，《华尔街日报》一则标题称英伟达正准备罢免黄仁勋，但当时只有标题和讨论、未获独立确认；11 月 14 日的日报则援引 CNBC 报道称黄仁勋已经辞职。此次董事会一致决定让黄仁勋复职，是这一人事风波的后续。

**「影响」** 声明把“收到美国政府高层意见”写进董事会决策说明，使这次公司治理变动与围绕对华芯片销售的制裁争议公开挂钩；对采购英伟达 AI 硬件的企业而言，随之而来的是政策与治理层面的不确定性，而所给材料未显示产品路线或供货安排发生变化。

**「社区讨论」** 多位评论者认为，声明中最关键的是“收到美国政府高层意见”这一句，而非复职本身；其中一人批评美国要求 ASML 和日本芯片厂商遵守对华制裁、却对英伟达网开一面，属于双重标准。另有评论援引特拉华州 Caremark 判例对董事会担责设定的高门槛，推测在司法部表示不起诉的情况下董事个人责任可被排除，并对董事会在不到两周内一致反转此前的决定表示意外。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.wsj.com/business/nvidia-is-preparing-to-oust-nvidia-ceo-jensen-huang-30f421ad">2026-11-12 — WSJ 称英伟达准备罢免黄仁勋</a></li>
<li><a href="https://www.cnbc.com/2026/11/13/howard-lutnick-nvidia-jensen-huang-china-cantor-fitzgerald.html">2026-11-14 — CNBC：卢特尼克因坎托与英伟达关系受审视</a></li>

</ul>
</details>

**标签**: `#Nvidia`, `#corporate governance`, `#US-China tech policy`, `#semiconductors`, `#AI hardware`

---

<a id="item-tech-news-2"></a>
### [Ladybird 浏览器发布首个 Alpha，支持 macOS 与 Linux](https://ladybird.org/posts/alpha/) ⭐️ 8.0/10

开源独立浏览器 Ladybird 发布首个 Alpha 版本，macOS 和 Linux 用户现在可以直接下载安装，无需自行编译。它的大部分核心组件——HTML 解析、CSS、布局、JavaScript 和 WebAssembly——均为自研，但仍使用 HarfBuzz、Skia、ffmpeg 和 SQLite 等外部组件。来源文章的试用记录显示，基于 WebAssembly 的 ffmpeg 工具和 Pyodide REPL 可以运行，但依赖 service worker 的 Datasette Lite 因缺少 navigator.serviceWorker.startMessages 而报错，相关 issue 已提交。官方将这一版本定位为 alpha，提醒部分网站会失效并可能崩溃；项目同时称 10 月的 web-platform-tests 通过数增加 75,650 项、达到约 218 万项，超过 Safari 但仍低于 Firefox，这一提升主要来自 AI 编码代理集中补齐功能。

hackernews · janvdberg · 11月23日 16:13 · [社区讨论](https://news.ycombinator.com/item?id=50614249)

**「背景」** Ladybird 源自更宏大的 SerenityOS 项目，自行实现 HTML 解析、CSS 引擎、布局、JavaScript 乃至 WebAssembly 等核心组件，只复用 HarfBuzz 文本排版、Skia 2D 图形、ffmpeg 视频和 SQLite 等少数外部库。2026 年 2 月 23 日 Andreas Kling 发文介绍借助 AI 编码工具把 LibJS 的部分代码从 C++ 迁移为约 2.5 万行 Rust；项目 10 月月度通讯则记录样式与布局移至独立线程、新的 JavaScript JIT、替换 Cranelift 的 WebAssembly 引擎在 JetStream 3 上取得 7 倍提升，以及在约 225 万个子项的 web-platform-tests 上新增 75,650 项通过、超过 Safari。

**「影响」** 对早期用户而言，Ladybird 已可用于检验常规网页兼容性，并能在浏览器内直接提交坏站或崩溃报告；但 service worker 相关功能仍是明确缺口，依赖这类能力的 Web 应用暂不能正常工作。

**「社区讨论」** 多位评论者称实际渲染成功率高于预期：有人测试新闻网站和 ProxMox 的 NoVNC 均正常，甚至认为 NoVNC 比 Firefox 更流畅；也有人称 YouTube 和 Google Maps 可用但略有卡顿，页面滚动稍显不顺。另有评论者欢迎一个不与 Google 广告绑定的浏览器，并询问 alpha 阶段在登录、认证、支付和下载等场景应如何做好安全预防。

**标签**: `#browser engine`, `#open source`, `#Ladybird`, `#alpha release`, `#software engineering`

---

<a id="item-tech-news-3"></a>
### [GLM-5.4 发布：首个循环 Transformer 瞄准通用编程](https://z.ai/blog/glm-5.4) ⭐️ 8.0/10

智谱（Zhipu）发布 GLM-5.4，称这是其首个循环 Transformer（loop transformer），目标是面向通用编程；现有材料未给出参数规模、基准分数或独立复现结果，因此“首个”架构的说法与性能优势仍属厂商表述。评论者 Simon Willison 报告，该模型当时未通过 OpenRouter 或常规 Z.ai API 套餐提供，需改用 Coding Plan，且该套餐生成的 API 密钥与普通密钥用法相同。对准备接入的开发者来说，应先确认可用的套餐与端点，不能假定现有 GLM API 调用可直接切换到 5.4。

hackernews · foohis · 11月23日 10:06 · [社区讨论](https://news.ycombinator.com/item?id=50609685)

**「背景」** 循环 Transformer 针对的是标准 Transformer 的推理内存瓶颈：解码每个 token 时，每一层权重都要从 HBM 搬进芯片、只计算一次再搬出，因此内存带宽长期是推理的首要瓶颈；循环架构让同一组权重在一次前向中重复使用，以减少权重搬运（社区评论对原理的解释，以及 Z.ai 开发者文档对 GLM-5.4 为首款 Loop Transformer 架构旗舰模型的描述相互印证）。此前的 8 月 29 日日报曾报道智谱开源 GLM-5.3：它与 GLM-5.2 共用同一基础模型，提升全部来自后训练，主打智能体编程与网络防御，Terminal Bench 2.1 得 88.2、DeepSWE 得 66.9；如今的 GLM-5.4 则把架构改动本身作为卖点，并将编程场景扩展到视频制作、游戏开发、3D 建模和机械设计。

**「对开发者的影响」** 对想使用 GLM-5.4 的开发者而言，目前主要接入途径是 Z.ai 的 Coding Plan：据第三方报道，该档位提供视觉能力，每周额度为 GLM-5.3 的 1.5 倍，而 OpenRouter 和常规 API 的接入仍在跟进中。有评论者称，自己正是因为常规 API 套餐取不到该模型，才改用 Coding Plan；这说明在订阅前需要先确认所用渠道是否已开放 GLM-5.4。

**「社区讨论」** 有评论者赞赏智谱公开技术细节，并认为循环 Transformer 是自然方向：原始 Transformer 像展开的 for 循环，却把注意力和前馈知识分配给不同权重；另一位评论者则从 HBM 带宽瓶颈解释，循环结构可减少每生成一个 token 时反复搬运整层权重的开销。也有开发者抱怨部分中国模型在简单任务上仍进行冗长“马拉松式思考”，完成时间明显高于前沿模型；这属于个人使用体验，而非基准结论。

<details><summary>参考链接</summary>
<ul>
<li><a href="http://z.ai/">2026-08-29 — 智谱开源 GLM-5.3，专注智能体编程与网络防御</a></li>
<li><a href="https://docs.z.ai/guides/llm/glm-5.4">GLM-5.4 - Overview - Z.AI DEVELOPER DOCUMENT</a></li>
<li><a href="https://docs.bigmodel.cn/cn/guide/models/glm-5.4">GLM-5.4 - 智谱AI开放文档</a></li>
<li><a href="https://explainx.ai/blog/glm-5-4-coding-plan-vision-50-percent-quota-boost-november-2026">GLM-5.4 Coding Plan: +50% Quota, Vision (Nov 2026) - explainx.ai</a></li>
<li><a href="https://kingy.ai/blog/glm-5-4-launch/">GLM‑5.4 launch: How to use it, pricing and API status</a></li>

</ul>
</details>

**标签**: `#LLM architecture`, `#looped transformers`, `#GLM-5.4`, `#coding models`, `#model release`

---

<a id="item-tech-news-4"></a>
### [Anthropic 关联仓库发布 VP ≠ VNP 论文，尚待验证](https://github.com/anthropics/formal-math/tree/main/vp-vnp) ⭐️ 8.0/10

与 Anthropic 关联的 formal-math 仓库托管了一篇论文，声称证明了在所有域上 VP ≠ VNP。该结论若成立，将分离代数复杂度类 VP 与 VNP；但目前只有仓库链接和 Hacker News 讨论，尚无同行评审或独立验证。评论者引用的论文原文还显示，作者未分析该结果与相对化（relativization）和代数化（algebrization）障碍的关系。对关注代数复杂度和形式化数学的读者而言，关键限制是：这是一项仓库中的论文主张，而非已发表或已复现的结果。

hackernews · mikeryan52 · 11月23日 22:09 · [社区讨论](https://news.ycombinator.com/item?id=50620102)

**「背景：VP 与 VNP 及证明屏障」** VP 与 VNP 是代数复杂性理论中对应 P 与 NP 的两个类别，VP ≠ VNP 是该领域长期未决的核心分离猜想。此类证明通常需要说明与相对化、代数化等已知屏障的关系；所引论文段落承认尚未分析这两点。仓库以 Lean 形式化代码发布，能机械检查证明步骤，但形式化是否忠实覆盖论文定义、以及证明本身是否经过同行评审，仍是独立问题。

**「引用前需独立复核」** 对复杂性和形式化数学研究者而言，当前更稳妥的做法是把这当作待复核的论文主张，而不是已确立的 VP ≠ VNP 结论：论文自述尚未分析该结果与相对化、代数化（algebrization）等已知障碍的关系，且尚未经过同行评审。若要在教学、引用或后续证明中依赖它，应先核对仓库中的形式化内容与障碍论证。

**「社区讨论」** 有评论者推测，这像是 Anthropic 在 P vs NP 方向投入的阶段性成果，也有人担忧 AI 会让数学研究生可选的题目迅速被解决；这些都属于个人判断，并非对证明的验证。更具体的技术讨论则引用论文自述，指出其未分析相对化与代数化障碍，另有评论者提供了无需本地构建即可浏览 Lean 源码的工具。

**标签**: `#algebraic-complexity`, `#complexity-theory`, `#formal-methods`, `#lean`, `#ai-for-math`

---

<a id="item-tech-news-5"></a>
### [开发者称 Apple 在九年后将其开源应用移出欧盟 App Store](https://github.com/glushchenko/fsnotes/discussions/2056) ⭐️ 7.0/10

开发者 Oleksandr Hlushchenko 在 GitHub 讨论区表示，其开源应用 FSNotes 在欧盟区 App Store 上架九年后被下架，该讨论随后在 Hacker News 引发关注。评论者 ggreer 指出，该应用仍在美国和英国区商店可见，其引用的荷兰区商店缓存页面显示该开发者「未将此应用标识为商家」，指向欧盟《数字服务法》（DSA）的商家身份（trader status）核验要求；不过 Apple 并未公开说明下架理由，因此具体原因仍属推断。开发者方面的说法是已联系 Apple 但未得到有效回应。

hackernews · fluder · 11月23日 18:48 · [社区讨论](https://news.ycombinator.com/item?id=50616933)

**「背景：DSA 商家身份核验要求」** 欧盟《数字服务法》第 30、31 条要求苹果对在欧盟 App Store 分发应用的商家（trader）核验并公开展示其联系信息，包括地址、电话和邮箱。苹果此前通知开发者，自 2025 年 2 月 17 日起，未提供商家身份的应用将从欧盟 App Store 下架，直至身份信息提交并在必要时完成核验。该身份并非一次填写后永久有效：开发者需在 App Store Connect 中维护这些信息，状态可能因地址变更等原因失效。

**「对开发者的影响」** 对在欧盟区分发应用的独立开发者而言，这一案例的警示是：DSA 商家身份核验不是一次性动作，认证可能因地址变更等原因失效，一旦失效便可能触发下架，而恢复只能走 App Store 审核通道。评论者 dmix 提到，其新应用在近期欧盟规则调整后花了约一个月才通过 DSA 审核，因此开发者需要及时在 App Store Connect 中维护并复核商家信息，并为审核排队预留时间。

**「社区讨论」** ggreer 认为下架更可能是 DSA 商家身份问题而非开源身份，并强调认证状态会因地址变更等原因失效；thih9 则反驳说，该应用是付费应用、开发者本就以商家身份申报，遵守法规与是否开源无关，且核验不应拖到九年后才做。dmix 报告称，近期欧盟 DSA 审核排队约需一个月，并认为审核团队正承受大量 AI 生成应用提交带来的负载压力。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://developer.apple.com/help/app-store-connect/manage-compliance-information/manage-european-union-digital-services-act-trader-requirements/">Manage European Union Digital Services Act trader requirements</a></li>
<li><a href="https://developer.apple.com/news/?id=einwn76m">Apps without trader status will be removed from the App Store ...</a></li>
<li><a href="https://median.co/blog/how-to-update-apple-trader-status-app-store-connect">How to update your Apple trader status from App Store Connect</a></li>

</ul>
</details>

**标签**: `#EU DSA`, `#Apple App Store`, `#app distribution`, `#open source`, `#developer compliance`

---

<a id="item-tech-news-6"></a>
### [谷歌用模拟互联网测试 Chrome AI 代理](https://www.landian.news/archives/128701.html) ⭐️ 7.0/10

据蓝点网报道，谷歌为 Chrome 的 AI 代理搭建了一个名为 Mirror Dimension 的模拟互联网，用于在隔离环境中测试其打开网站、搜索浏览、登录、加购和完成任务等操作。该环境包含数千个模拟网站，每名工程师单独隔离测试，每天运行超过 1000 个测试案例，重点防御恶意网页发起的提示词注入攻击。上述细节来自二手报道，源内容未说明测试结果、上线时间，也未说明这些防护是否已进入 Chrome。

telegram · zaihuapd · 11月23日 01:30

**「背景」** 浏览器 AI 代理与普通聊天机器人不同：它要在 Chrome 中像用户一样打开网页、搜索、登录和加购，因此网页里隐藏的指令可能被代理误当成任务执行。这类攻击就是提示词注入。Wired 的报道也提到，谷歌会让这些代理在浏览过程中遭遇隐藏的提示词注入攻击，以检验其防御能力。

**「影响」** 报道列出的测试操作包含登录和加购等带副作用的动作，说明评估浏览器代理不能只看它能否回答问题，还要看恶意网页能否诱导它执行未授权操作。由于源内容没有说明 Mirror Dimension 是否对外开放，也没有说明相关防护是否已随 Chrome 发布，开发者目前无法据此判断实际用户是否已获得同等保护。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.wired.com/story/google-built-a-giant-mirror-dimension-internet-to-test-its-chrome-ai-agents/">Google Built a Giant ‘ Mirror Dimension ’ Internet to Test Its Chrome ...</a></li>

</ul>
</details>

**标签**: `#Chrome AI`, `#browser agents`, `#prompt injection`, `#AI security testing`, `#simulated internet`

---

<a id="item-tech-news-7"></a>
### [Windows Server 2028 默认移除 WoW64，32 位应用需手动装回](https://www.windowslatest.com/2026/11/23/32-bit-apps-days-are-numbered-as-microsoft-strips-support-bit-by-bit-starting-with-windows-server-2028-but-windows-11-is-safe-for-now/) ⭐️ 7.0/10

微软在 Ignite 2026 上表示，Windows Server 2028 将默认不再包含 WoW64 兼容子系统，因此系统安装完成后无法直接运行 32 位应用。该版本计划于 2027 年秋季与 Windows 11 27H2 一同发布。需要运行 32 位软件时，可通过“按需功能”（FoD）重新安装 WoW64，在 Server Core 上一般使用 PowerShell 或 DISM 添加。微软称此举旨在减少攻击面、阻止 32 位恶意软件；Windows 11 目前仍保留 WoW64，微软未公布移除计划。上述内容来自 Windows Latest 的报道，具体支持范围以微软后续文档为准。

telegram · zaihuapd · 11月23日 03:03

**「背景」** WoW64（Windows 32-bit on Windows 64-bit）是 64 位 Windows 中负责运行 32 位应用的兼容子系统，长期作为系统默认组件随附，因此企业无需额外配置即可沿用旧版 32 位软件。此次变化的核心在于它从“默认内置”改为“按需功能”：同一套兼容能力仍在，但部署方式由开箱即用变成需要管理员主动添加。

**「影响」** 仍依赖 32 位应用的企业需要在制作 Windows Server 2028 镜像时预先加入 WoW64 按需功能，否则部署完成后应用无法启动；Server Core 没有图形界面，只能通过 PowerShell 或 DISM 操作，因此相关步骤应提前写入标准化部署脚本。

**标签**: `#Windows Server`, `#WoW64`, `#32位兼容性`, `#微软`, `#操作系统`

---

<a id="item-tech-news-8"></a>
### [Codex2api 疑遭供应链投毒，3.1.10–3.1.12 需回滚](https://github.com/WormW/codex2api-incident-2026-11) ⭐️ 7.0/10

据 Telegram 频道 zaihuapd 转述的一份事件复盘，开源项目 codex2api 的作者账号遭入侵，攻击者绕过 main 分支直接推送 tag，使 Release 构建出带后门的版本。复盘称 v3.1.11 去掉了鉴权，等同于可无密码远程执行命令；同时有 workflow 将仓库的 16 个 Actions secrets 外传，波及同一账号下至少 21 个仓库。该报告建议装过或升级到 3.1.10–3.1.12 的用户立即停用、回退到 3.1.9，并轮换 GitHub token、SSH key、数据库和 DeepSeek 等相关密钥。以上均来自社交媒体转述与第三方复盘，尚未见到项目方的独立确认。

telegram · zaihuapd · 11月23日 11:21

**「事件背景」** Codex2api 通过 GitHub Release 发布版本，3.1.10–3.1.12 是在 3.1.9 之后出现的更新。事件复盘称，攻击者没有经由 main 分支，而是直接推送 tag，使 Release 构建流程产出了带后门的包；这也是通报要求已安装或更新到这三个版本的用户停用并回退到 3.1.9 的原因。

**「影响」** 对已运行 3.1.10–3.1.12 的部署，报告给出的处置顺序是先停用并回退到 3.1.9，再轮换全部可能暴露的凭据；由于外泄的是 GitHub Actions secrets，同一账号下至少 21 个仓库的 CI 凭据都应视为已泄露，仅回滚版本并不能消除风险。

**标签**: `#supply-chain security`, `#GitHub Actions`, `#security incident`, `#open source`, `#credential rotation`

---

<a id="item-tech-news-9"></a>
### [Meta AI 负责人称超级智能将至并警告控制风险](https://thenextweb.com/news/metas-ai-chief-says-superintelligence-is-arriving-and-control-is-at-risk) ⭐️ 7.0/10

Meta 首席 AI 官、超级智能实验室负责人 Alexandr Wang 在 X 发长文称，超级智能已不再是“未来某天”的议题。他以数学家 Levent Alpöge 借助 Anthropic Claude 完成、并于周六经 Lean 与 Mathlib 社区机器校验的黎曼猜想证明为例，认为 AI 与顶尖人类的差距只剩具体知识、工程整合与实验三块。他警告人类很难继续掌控可无限自我改进、或比自己聪明 1000 倍的系统，呼吁紧急投入安全、对齐与防护研究；该证明目前尚无人类可读版本，来源也未提供独立验证。

telegram · zaihuapd · 11月23日 12:49

**「背景：机器校验与黎曼猜想」** 这里的“机器校验”指证明被写成 Lean 定理证明器可检查的形式化代码，并依赖 Mathlib 数学库；它不同于经过同行评审、人类可读的数学论证。据 Scientific American 和 State of Proof 的报道，Levent Alpöge 称与 Claude 合作得到了黎曼猜想（以及对 Dirichlet L 函数的广义黎曼猜想）的证明并完成 Lean 形式化，Lean/Mathlib 社区随后认证了该形式化结果，但具体检查范围和仍未知的部分需要区分。

**「影响」** 对数学界而言，当前最直接的障碍是缺少人类可读证明：在出现可读版本前，外部研究者难以审查该黎曼猜想证明的具体论证。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.scientificamerican.com/article/anthropic-mathematician-claims-to-prove-riemann-hypothesis-most-famous-problem-in-all-of-math/">Anthropic mathematician proves Riemann hypothesis, most ...</a></li>
<li><a href="https://www.datastudios.org/post/claude-riemann-hypothesis-proof-lean-community-certifies-levent-alpoge">Claude-assisted Riemann hypothesis proof certified by Lean ...</a></li>
<li><a href="https://stateofproof.org/paper-watch/paper-2026-11-20-a-claimed-proof-of-the-riemann-hypothesis">A Claimed Proof of the Riemann Hypothesis — Paper Watch ...</a></li>

</ul>
</details>

**标签**: `#AI safety`, `#superintelligence`, `#Meta`, `#Lean theorem proving`, `#Riemann hypothesis`

---

## 科技博客

<a id="item-tech-blog-1"></a>
### [DoorDash 调度重构：协调与计算分离](https://blog.bytebytego.com/p/doordash-dispatch-building-a-lightning) ⭐️ 6.0/10

rss · ByteByteGo · 11月23日 16:31

**「背景」** DoorDash 的调度系统要在订单、Dasher 位置、餐厅备餐和交通状况不断变化时，快速给出“足够好”的指派。旧单体引擎把物流状态、业务规则和昂贵的路由优化耦合在一起，核心算法近似二次复杂度；高峰期需求可达其处理能力的近 4 倍，系统只能缩减搜索范围或退化为简单规则。

**「方案」** 新平台把调度协调与重计算拆成可独立扩展的两层：协调层维护物流状态、应用业务规则并组织每轮工作，计算层由无状态 worker 并行生成和评估路线、运行优化与模型；协调层通过 gRPC 在每个 dispatch tick 下发局部、自包含的 payload，避免每个 worker 复制全量状态。为缩小问题规模，系统按地理簇和配送轨迹做分层分解，先快速预聚类，再用质心细化，分区并行求解，最后由全局调和与评分层合并局部方案，尽量保留整体优化质量。上线时先做影子测试，复制生产流量、只记录新引擎结果以做行为回归，再用生产 switchback 实验轮换控制、限制暴露并设置回退，逐步扩大范围。DoorDash 报告处理规模达到 10 倍，超过 99.96% 的运行在 20 秒内完成，Super Bowl 流量峰值下可用性高于 99.99%；平台还支持 worker 内 ONNX Runtime 的 L1 本地模型、远程 L2 模型，以及调整优化权重的多智能体强化学习。

**「启示」** 作者认为，这次重构的关键不只是性能数字，而是把调度从单体瓶颈转成可分布、可验证、可扩展的架构，使更快决策与更大搜索空间能够同时成立；但这些结果来自 DoorDash 公开材料，分区边界处调和能恢复多少质量、调和是否成为尾延迟来源，仍未展开。

**标签**: `#dispatch systems`, `#distributed optimization`, `#system architecture`, `#shadow testing`, `#ML serving`

---

<a id="item-tech-blog-2"></a>
### [cuDSS 1.0：稀疏直接求解器的精度与内存改进](https://developer.nvidia.com/blog/accelerating-direct-sparse-solvers-for-computational-engineering-with-nvidia-cudss-1-0/) ⭐️ 6.0/10

rss · NVIDIA CUDA Technical Blog · 11月23日 19:59

**「背景」** 稀疏线性方程组是结构、流体、电路等工程仿真的核心；随着问题规模和精度要求上升，直接求解器既要借 GPU 扩展，又要保持生产级稳健性。cuDSS 已正式可用，1.0 版聚焦真实工作负载的性能、数值精度与显存限制。

**「方案」** 作者报告，在电路、TCAD、热、结构、电磁和流体等基准矩阵上，cuDSS 1.0 相对 Intel MKL 2026.1.0 的几何平均加速为：分析 2.5 倍、数值分解 5.9 倍、三角求解 151 倍（B200 与 Xeon Platinum 8570，NVIDIA 自报；端到端收益取决于各阶段占比）。针对对称不定系统，1.0 默认启用保对称的匹配缩放（HSL MC64）和 Bunch-Kaufman 选主元，允许 1×1 或 2×2 主元，避免小对角元失稳；SuiteSparse 示例中 NRBE 最多改善约 10 个数量级，扰动主元降为零。作者也提醒匹配并非总提升精度，少数情形可用 CUDSS\_MATCHING\_ALG\_NONE 关闭。内存上，混合模式把 GPU HBM 与 CPU DRAM 视作统一容量，将暂不需要的数据放在主机端，使大型 VLSI 算例最低显存需求平均降 30%，原本需多 GPU 的问题可落在单卡；1.0 还引入可定制 pinned memory handler，并称 GPU 符号分解比 0.8.0 快 2.21 倍。

**「启示」** cuDSS 1.0 的核心主张是，GPU 稀疏直接求解器的可用性来自精度算法、分阶段性能与 CPU-GPU 混合内存的系统级协同，而非单一内核加速；不过这些收益仍主要基于 NVIDIA 自家基准，需独立验证。

**标签**: `#GPU sparse solvers`, `#cuDSS`, `#Bunch-Kaufman pivoting`, `#hybrid memory`, `#numerical accuracy`

---

<a id="item-tech-blog-3"></a>
### [Sirius：为 DuckDB 带来 GPU 加速分析](https://developer.nvidia.com/blog/get-started-with-gpu-accelerated-duckdb-analytics-using-the-sirius-core-extension/) ⭐️ 4.0/10

rss · NVIDIA CUDA Technical Blog · 11月23日 17:09

**「背景」** 随着数据集增长，DuckDB 上的分析查询会变慢，影响数据探索、流水线和应用的响应。NVIDIA 与 DuckLabs 合作发布开源 GPU 原生 SQL 引擎 Sirius，并把它做成 DuckDB 核心扩展，目标是无需改写 SQL 或数据库模式就能加速受支持的查询。

**「方案」** Sirius 让 DuckDB 继续负责 SQL 解析与优化，把生成的查询计划整体交给 GPU 执行，再通过同一连接返回结果；遇到不支持的特性则回退到 DuckDB 的 CPU 引擎。入门门槛是 DuckDB 2.0 和兼容驱动的 NVIDIA GPU，操作只有 INSTALL sirius; 与 LOAD sirius; 两条命令；文中用 TPC-H SF0.01 生成 lineitem，执行按 l\_returnflag 分组的求和查询，并明确小数据只用于演示、不用于证明性能。作者给出的 NVIDIA 自测基准覆盖 S3 上的 TPC-H 派生查询、SF100/1K/3K/10K 及固定开发构建：调优后双 GPU 比最佳 CPU 配置快 3.25–5.50 倍，SF1K 从 347.3 秒降至 63.2 秒，SF3K 从 752.4 秒降至 160.6 秒且查询期计算成本约降 71%，SF10K 从 2369.4 秒降至 729.9 秒、成本约降 79%。但计时口径并不对等——Sirius 不含结果获取/导出，DuckDB 含 CSV 输出；SF10K 默认双 GPU 配置未完成，调优后才完成，SF100 则是单 GPU 成本最低、双 GPU 运行最快。

**「启示」** 作者的核心结论是，Sirius 把 GPU 执行嵌入 DuckDB 现有 SQL 工作流，降低了尝试 GPU 加速的门槛；不过这些数字来自厂商自测和特定调优配置，实际收益仍取决于查询结构、数据规模、硬件与缓存条件。

**标签**: `#DuckDB`, `#GPU acceleration`, `#SQL analytics`, `#database extensions`, `#benchmarks`

---