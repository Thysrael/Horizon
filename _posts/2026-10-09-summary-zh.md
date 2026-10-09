---
layout: default
title: "Horizon Summary: 2026-10-09 (ZH)"
date: 2026-10-09
lang: zh
---

> 从 36 条内容中筛选出 6 条重要资讯。

---

**科技新闻**
1. [中国团队实现钍-229 核光钟稳定运行](#item-tech-news-1) ⭐️ 8.0/10
2. [DeepSeek 4.1 Flash 为何未引发行业恐慌](#item-tech-news-2) ⭐️ 7.0/10
3. [Linux 内核 vswap 与 xswap 的 swap 虚拟化方案分歧未决](#item-tech-news-3) ⭐️ 7.0/10
4. [OpenAI 封禁俄伊两起 ChatGPT 影响行动](#item-tech-news-4) ⭐️ 7.0/10

**财经新闻**
1. [人社部就新就业形态劳动者权益保障办法公开征求意见](#item-finance-news-1) ⭐️ 8.0/10
2. [美政府以欺诈指控暂停微软绿卡申请资格](#item-finance-news-2) ⭐️ 8.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [中国团队实现钍-229 核光钟稳定运行](https://www.nature.com/articles/s41586-026-11122-1) ⭐️ 8.0/10

清华大学研究团队利用自主研制的 148 纳米连续波真空紫外激光和掺钍-229 氟化钙晶体，报告研制出核光钟并实现稳定运行，成果发表于《自然》。该时钟以钍-229 原子核能级跃迁为计时基准，有望成为新一代时间频率基准。这是研究团队在《自然》论文中报告的实验结果，尚非已部署的计时标准。

telegram · zaihuapd · 10月8日 05:19

**「背景」** 原子钟以原子外层电子的能级跃迁作为计时基准，核光钟则改用原子核内部的能级跃迁，理论上对外界电磁扰动更不敏感。钍-229 的特殊之处在于它存在能量异常低的核跃迁，对应 148 纳米真空紫外波段，可在掺钍晶体中以激光激发；《自然》刊出的相关研究已分别实现该跃迁的连续波激光吸收谱测量，以及将连续波激光锁定到这一核跃迁的反馈方案（tool-2-1、tool-2-2、tool-2-3）。

**「影响」** 对时间频率计量和卫星导航等领域的研发者来说，该成果把钍-229 核跃迁推进到稳定运行的核光钟阶段；不过现有证据仅来自论文报告，尚未显示其已替代或兼容现有原子钟体系。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.nature.com/articles/s41586-026-11084-4">A thorium-229 optical nuclear clock with feedback loop | Nature</a></li>
<li><a href="https://www.nature.com/articles/s41586-026-11011-7">Continuous-wave laser absorption spectroscopy of the thorium ...</a></li>
<li><a href="https://arxiv.org/html/2606.04997">A thorium-229 optical nuclear clock with feedback loop</a></li>

</ul>
</details>

**标签**: `#nuclear clock`, `#thorium-229`, `#precision timing`, `#metrology`, `#hardware`

---

<a id="item-tech-news-2"></a>
### [DeepSeek 4.1 Flash 为何未引发行业恐慌](https://www.dgt.is/blog/2026-10-07-deepseek-freek-out/) ⭐️ 7.0/10

一篇 dgt.is 博客文章与随后的 Hacker News 讨论提出疑问：DeepSeek 4.1 Flash 推出后，为什么没有像其他前沿模型那样引发业界警觉。评论者给出的主要解释是，多数用户实际使用的是厂商大幅补贴的订阅套餐，而按 OpenRouter 等平台的 API 价格直接调用并不便宜——有评论者称几天就花掉了 50 美元。另一条线索是开放权重模型对显存的要求：评论者列举出 FP16 约 1664 GB、INT8 约 832 GB、INT4 约 416 GB，但这些数字以及该模型的具体规格在讨论中都没有官方来源。

hackernews · jonotime · 10月8日 00:14 · [社区讨论](https://news.ycombinator.com/item?id=50000488)

**「背景」** Horizon 2026 年 9 月 11 日的日报曾报道，DeepSeek 发布 V4.1 Flash，称其为该全新模型结构系列中尺寸最小的模型，采用 552B 参数的 Causal-Encoder-Decoder 结构（输入与输出激活参数分别为 8B 和 16B），原生支持多模态视觉理解；该模型以 deepseek-flash 之名上线 API，新价格自 2026 年 9 月 10 日生效，并计划在 9 月 14 日后把 deepseek-v4-pro 请求路由至 V4.1 Flash 并按新价格计费（该条目来自聚合式帖子，当时未获官方一手来源确认）。更早的 2026 年 8 月 5 日日报则报道上一代 V4 Flash 凭借原生 MXFP4 量化装入单块 144GB 的 AMD MI300X、以约每秒 150 token 运行，显示量化精度与部署硬件成本一直是围绕该系列模型的讨论焦点。

**「影响」** 对使用 DeepSeek API 的开发者来说，最直接的后果是模型标识变更：官方公告称 V4-Flash 与 V4-Flash-Vision-Exp 已退役，需要把请求中的模型改为 deepseek-flash，并可按需启用原生多模态能力（tool-3-2）。在 OpenRouter 上该模型的定价为每百万输入 token 0.02 美元、每百万输出 token 0.60 美元（tool-3-3），这一 API 价格也抬高了自托管的门槛——有评论者按精度估算，FP16 推理约需 1664 GB 显存、INT8 约 832 GB、INT4 约 416 GB，意味着需要多卡服务器集群。

**「社区讨论」** 围绕“为何不恐慌”，一方以亲身体验支持补贴论：有评论者称高强度使用 DeepSeek 4.1 Flash 一个多月，全天运行每天仅花 1–2 美元且速度很快，不再像 20 美元套餐下那样很快撞上 Claude/Codex 的 5 小时额度，但认为它不擅长通过追问来敲定技术决策；另一位评论者则表示，一旦补贴停止，开放权重模型就难以竞争。反方认为在同样使用补贴订阅时成本差距并不明显（如 Z.ai 100 美元/月的 GLM 5.3 对 Claude 100 美元/月的 Opus 5.5），并质疑后者的前沿模型地位——这些都属于个人使用经验，而非独立评测。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://mp.weixin.qq.com/s/qg0NU3NNUbp1co2PdkAPAg">2026-09-11 — DeepSeek V4.1 Flash 发布：552B 参数与 API 路由调整</a></li>
<li><a href="https://github.com/ryanzhou/deepseek-v4-flash-mi300x">2026-08-05 — DeepSeek V4 Flash 在单块 AMD MI300X 上以约 150 tokens/s 运行</a></li>
<li><a href="https://www.deepseek.com/en/news/deepseek-v4-1-flash/">Introducing DeepSeek -V 4 . 1 - Flash : smarter, faster, more efficient.</a></li>
<li><a href="https://openrouter.ai/deepseek/deepseek-v4.1-flash">DeepSeek V 4 . 1 Flash - API Pricing &amp; Benchmarks | OpenRouter</a></li>

</ul>
</details>

**标签**: `#DeepSeek`, `#GPU VRAM`, `#AI model pricing`, `#open-weight models`, `#LLM deployment`

---

<a id="item-tech-news-3"></a>
### [Linux 内核 vswap 与 xswap 的 swap 虚拟化方案分歧未决](https://lwn.net/Articles/1098399/) ⭐️ 7.0/10

Linux 内核交换层中 swap cache 槽位与持久 swap 文件空间直接绑定的问题仍未解决，Nhat Pham 的 vswap 与 Baoquan He、Chris Li 的 xswap 两个竞争方案都尚未达到可合并状态。问题核心在于，zswap 中的每个 folio 仍必须在持久 swap 设备上占用一个槽位，即使该空间通常用不到，这会让大型数据中心为实际不落盘的数据预留大量闪存。vswap 在现有 swap 设备上增加虚拟化层，用 xarray 跟踪可映射到物理 swap 文件、zswap 或无槽位的虚拟槽位，并且其 swap 区域可随负载动态伸缩；xswap 则提供一个没有后备存储的虚拟 swap 设备，用稀疏映射地址范围做簿记，但要求一开始就预留完整地址空间，因而限制设备最大容量和 zswap 可存放的 folio 数。关于合并顺序的讨论未达成结论，He 最近发布了三部分的新 xswap 实现，其中第 2 部分补上了此前缺失的物理回写，讨论仍在继续。

rss · LWN.net · 10月8日 13:43

**「背景」** zswap 的工作方式是拦截原本要写入交换文件的 folio，把内容压缩后留在内存里，但现行设计仍要求每个 folio 在持久交换设备上占有一个槽位，这部分存储空间通常被闲置浪费；vswap 与 xswap 的分歧正是围绕如何解除这一绑定展开。Horizon 在 2026 年 8 月 17 日的日报中曾报道 Linux 7.2 正式发布并包含 swap 子系统改进，说明该层在过去一年已有多项改动落地，而本次讨论涉及的问题属于其中尚未解决的部分。

**「影响」** 对于运行 zswap 的系统管理员，这一未决状态意味着仍需为每个进入 zswap 的 folio 预留持久 swap 空间，大型数据中心可能继续为实际不落盘的压缩页配置并占用闪存容量。在任一方案被主线接受之前，尚无内核级修复可用。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://lwn.net/Articles/1088991/">2026-08-17 — Linux 内核 7.2 发布：引入 BPF、调度器及文件系统多项改进</a></li>

</ul>
</details>

**标签**: `#Linux kernel`, `#memory management`, `#zswap`, `#swap subsystem`, `#open source`

---

<a id="item-tech-news-4"></a>
### [OpenAI 封禁俄伊两起 ChatGPT 影响行动](https://openai.com/index/disrupting-ai-enabled-false-front-operations/) ⭐️ 7.0/10

OpenAI 表示已封禁两起利用 ChatGPT 的隐蔽影响行动：俄罗斯行动涉嫌冒用身份控制拉美一个“研究平台”，传播损害乌克兰声誉并影响当地政治的虚假内容；伊朗行动以 7 个“记者”人设向全球中小网络媒体投稿，并批量生成社交媒体评论。OpenAI 将俄罗斯行动评为影响行动突破量表的第 5 类，称这是其开始报告以来首次；伊朗行动为第 4 类，产出近 100 篇署名文章。两起行动都结合传统手段与 AI，部分内容进入了主流媒体；上述严重级别与影响描述来自 OpenAI。

telegram · zaihuapd · 10月8日 15:52

**「背景」** OpenAI 此前已多次发布报告，披露并封禁利用其模型的国家关联影响行动：其首份模型滥用报告称阻断了来自俄罗斯、中国和伊朗等方的五个行动，之后又披露过俄罗斯冒用一家以色列智库名义、推广亲俄叙事并批评西方的隐蔽 campaign。OpenAI 在报告中用一套影响行动突破量表对封禁行动评级。

**「影响」** 对接收投稿的媒体和平台而言，具体后果是已发布内容不会随 ChatGPT 账号封禁自动消失：伊朗行动产出的近 100 篇署名文章和俄罗斯行动的部分内容已进入主流媒体，因此相关编辑部需要回溯核查这些投稿的作者身份、来源和事实。OpenAI 的处置主要限制相关账户使用 ChatGPT，不等于已发表内容已被撤回或更正。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://openai.com/index/disrupting-malicious-uses-of-ai-influence-campaign-russia/">Disrupting a new covert influence campaign from Russia | OpenAI</a></li>
<li><a href="https://therecord.media/openai-report-china-russia-iran-influence-operations">OpenAI models used in nation-state influence campaigns, company...</a></li>

</ul>
</details>

**标签**: `#AI misuse`, `#influence operations`, `#OpenAI`, `#disinformation`, `#platform governance`

---

## 财经新闻

<a id="item-finance-news-1"></a>
### [人社部就新就业形态劳动者权益保障办法公开征求意见](https://mp.weixin.qq.com/s/saqkOXlhe0wX7qD83vdkRw) ⭐️ 8.0/10

10 月 8 日，人力资源社会保障部发布《新就业形态劳动者权益保障办法（征求意见稿）》，即日起至 11 月 8 日公开征求意见，适用对象包括网约车司机、外卖骑手、网络主播等新就业形态劳动者。征求意见稿提出正常劳动报酬不得低于当地最低工资标准、连续工作 4 小时应保障适当休息，并要求停止派单、封禁账号等重大决定须经人工审核、不得由算法自动作出，同时明确不得滥用罚款等惩罚性措施。

telegram · zaihuapd · 10月8日 09:23

**「背景」** 此前，人社部等部门曾在 2021 年发布《关于维护新就业形态劳动者劳动保障权益的指导意见》，为网约车司机、外卖骑手等新就业形态劳动者提供基础性保障框架；此次征求意见稿拟在此基础上进一步细化平台劳动规则、最低工资和休息等要求。

**「影响」** 若该征求意见稿最终落地，网约车、外卖、直播等平台企业及其招募和管理劳动者的用工合作企业将需调整派单算法与劳动规则、落实最低工资和休息要求，并把停派单、封号等重大决定改为人工审核，相关从业者则相应获得这些保障。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://laodonglaw.com/jygl/620.html">关于维护 新 就 业 形 态 劳 动 者 劳 动 保 障 权 益 的 指 导 意 见 ( 人 社 部 发〔 2021 ...)</a></li>
<li><a href="https://www.chinanews.com.cn/gn/2026/10-08/10709310.shtml">新 就 业 形 态 劳 动 者 权 益 保 障 办 法 公开 征 求 意 见 -中 新 网</a></li>
<li><a href="https://www.jiemian.com/article/15168747.html">jiemian.com/article/15168747.html</a></li>
<li><a href="https://www.bjnews.com.cn/detail/1791445703129602.html">新 就 业 形 态 劳 动 者 权 益 保 障 办 法 公开 征 求 意 见 — 新 京报</a></li>

</ul>
</details>

**标签**: `#新就业形态`, `#劳动者权益`, `#平台经济监管`, `#算法治理`, `#中国政策`

---

<a id="item-finance-news-2"></a>
### [美政府以欺诈指控暂停微软绿卡申请资格](https://apnews.com/article/h1b-visa-program-vance-microsoft-e7b3a407f822702b269ee277d21343ea) ⭐️ 8.0/10

特朗普政府宣布暂停微软参与外籍劳工绿卡申请项目，理由是欺诈指控；副总统万斯称微软去年裁员 6000 名美国员工，却获得 6300 份 H-1B 签证和近 3000 张绿卡，并指责其先发布虚假招聘广告再以外籍劳工替换美国员工。微软尚未回应，上述欺诈说法目前仍属政府一方的指控，未经证实。

telegram · zaihuapd · 10月9日 00:00

**「背景」** H-1B 签证是美国雇主雇用外籍专业人员的临时工作许可，绿卡则代表永久居留；此次被暂停的是微软为持 H-1B 员工申请绿卡的通道，相关欺诈指控由副总统万斯在记者会上提出。

**「影响」** 在微软（据媒体报道还包括 Adobe）持 H-1B 签证的外籍员工，其由雇主担保转为永久居民（绿卡）的路径将被阻断，因为被暂停的劳工认证（PERM）是就业类绿卡申请的第一步。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.nytimes.com/2026/10/08/us/politics/microsoft-visas-green-cards.html">Trump Administration Suspends Microsoft From Green Card ...</a></li>
<li><a href="https://www.nbcnews.com/politics/trump-administration/microsoft-suspended-green-cards-h-1b-visa-j-1-visa-vance-rcna602314">The Trump administration is suspending Microsoft from a green ...</a></li>
<li><a href="https://www.visaverge.com/news/trump-administration-suspends-microsoft-from-h-1b-green-card-program/">Microsoft H-1B Green Card Suspension: What It Means</a></li>
<li><a href="https://www.theguardian.com/technology/2026/oct/08/jd-vance-microsoft-visa-workers-green-card-suspension">Microsoft suspended from applying for green cards for H-1B ...</a></li>
<li><a href="https://www.tomshardware.com/tech-industry/policy/u-s-suspends-green-card-path-for-h-1b-workers-at-microsoft-and-adobe-labor-certification-program-blocked-due-to-alleged-fraud">U.S. suspends green card path for H-1B workers at Microsoft ...</a></li>

</ul>
</details>

**标签**: `#immigration policy`, `#H-1B visas`, `#Microsoft`, `#tech industry`, `#labor market`

---