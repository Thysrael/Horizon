---
layout: default
title: "Horizon Summary: 2026-11-23 (ZH)"
date: 2026-11-23
lang: zh
---

> 从 26 条内容中筛选出 4 条重要资讯。

---

**科技新闻**
1. [OpenAI 讨论困惑度与智能，社区争论评估方法](#item-tech-news-1) ⭐️ 7.0/10
2. [分析预测：2028 年 Anthropic 电力 87%来自天然气、11%来自煤炭](#item-tech-news-2) ⭐️ 7.0/10

**科技博客**
1. [不确定时，不妨有章法地乱试](#item-tech-blog-1) ⭐️ 6.0/10

**财经新闻**
1. [美股科技股大跌 亚洲多地推出稳市措施](#item-finance-news-1) ⭐️ 9.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [OpenAI 讨论困惑度与智能，社区争论评估方法](https://openai.com/index/perplexity-and-intelligence/) ⭐️ 7.0/10

OpenAI 网站刊出《Perplexity and Intelligence》，面向关注语言模型评估的读者讨论困惑度与模型“智能”的关系，并把交叉熵损失与强化学习在评估中的角色纳入讨论。现有可见材料没有显示新模型、版本发布或可独立复现的基准结果，文章本身也未定义“困惑度”这一核心术语。Hacker News 上的讨论因此集中在困惑度能否作为能力指标，以及特定能力是否会在某个困惑度阈值“涌现”。

hackernews · acossta · 11月22日 17:06 · [社区讨论](https://news.ycombinator.com/item?id=50601525)

**「背景」** 困惑度（perplexity）是对数交叉熵损失取指数后的结果，用来衡量模型在给定文本序列上预测下一个 token 的不确定性：数值越低，说明模型对文本的压缩和预测越好，最差情形等于词表大小，最好情形为 1。它长期是预训练阶段的核心指标，但随着 RL 后训练和各类基准测试兴起，业界已较少用它横向比较模型能力。OpenAI 首席科学家 Jakub Pachocki 在 11 月 22 日发表的文章中主张，固定留出集上的对数困惑度能够一致地反映模型底层能力的进展，并呼吁前沿实验室采用同一指标。

**「影响」** 对使用困惑度筛选模型或判断能力是否出现的开发者，评论中的反例提示应把困惑度与目标任务评测分开：在数学等专门数据上训练的小模型，可能在目标任务上表现好，却在其他任务上保持较高困惑度。

**「社区讨论」** 有评论者指出文章没有定义“困惑度”，并补充它是模型预测下一个 token 时的惊讶程度：最佳为 1，最差为词表大小；另一名评论者则惊讶于强化学习普及后交叉熵损失与能力的趋势仍如此清晰，认为这种简单基准比日益复杂的评测更有价值。也有评论者质疑“特定能力在特定困惑度涌现”的说法，理由是专门训练数学的小模型在目标任务上可能很强，但在其他任务上的通用困惑度会更高。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://openai.com/index/perplexity-and-intelligence/">Perplexity and Intelligence - OpenAI</a></li>
<li><a href="https://community.openai.com/t/perplexity-and-intelligence/1419510">Perplexity and Intelligence - Community - OpenAI Developer ...</a></li>
<li><a href="https://www.explainx.ai/blog/openai-pachocki-perplexity-intelligence-pacing-safety-november-2026">OpenAI Perplexity Metric: GPT Log-Loss Curve (Nov 2026 ...</a></li>

</ul>
</details>

**标签**: `#AI/ML`, `#language models`, `#perplexity`, `#model evaluation`, `#OpenAI`

---

<a id="item-tech-news-2"></a>
### [分析预测：2028 年 Anthropic 电力 87%来自天然气、11%来自煤炭](https://betterdatacenterproject.com/2026/11/16/how-ai-is-powered-a-breakdown-of-byop-and-grid-power/) ⭐️ 7.0/10

一篇分析预测，到 2028 年 Anthropic 数据中心的电力将有 87%来自天然气、11%来自煤炭。这是单一来源的预测，并非 Anthropic 已公布的采购数据或第三方实测结果，现有材料也未说明所覆盖的具体设施、地区口径和其余电力来源。对关注 AI 基础设施能耗及数据中心周边环境影响的读者来说，争议点在于化石能源依赖和当地污染等外部性。

hackernews · happosai · 11月22日 08:57 · [社区讨论](https://news.ycombinator.com/item?id=50597612)

**「背景」** 这项 87%/11% 的拆分来自 Better Data Center Project 于 2026 年 11 月 16 日发布的案例研究：测算对象是 Anthropic 在美国签约的数据中心，基于约 15 吉瓦已签约算力，并计入现场燃气轮机等供电方式；其中间情景估计年排放约 1700 万至 3800 万吨二氧化碳当量。thebureauinvestigates.com 2026 年 8 月的一篇调查报道此前已指出，Anthropic 的扩张依赖其租用的孟菲斯 Colossus 数据中心，该设施引发了当地居民不满。因而这些比例应视为对 2028 年供电结构的前瞻性情景估算，而非已经发生的用电统计。

**「影响」** 如果该 2028 年电力结构预测成立，最先承担后果的会是数据中心所在社区与地方电网。公开记录显示，Colossus 数据中心在电网接入和永久发电设施完工前，依靠临时燃气轮机快速上线，这在孟菲斯地区引发了人们对 NOx、甲醛和雾霾等空气质量问题的担忧，同时也带来了每天数百万加仑的用水需求，并给当地电网造成压力；有评论者称 Anthropic 租用了同一处 Colossus 1。对采购 AI 算力的组织而言，这意味着选址和排放许可可能比电价更早成为硬性约束，现场污染控制和社区沟通需要被纳入部署计划，而不能只体现在财务核算中。

**「社区讨论」** 评论者批评 Anthropic 在化石能源依赖和社区污染上的表现，特别提到其租用 Colossus 1 与孟菲斯当地污染，并称其在美国没有作出可再生能源承诺；这些均为评论者观点。另有评论认为企业自愿行动不足，需要监管把环境和健康外部性计入成本，也有人指出美国天然气大量是页岩油伴生、未捕获时会被放空燃烧。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://explainx.ai/blog/anthropic-data-center-power-gas-coal-byop-2028-better-datacenter-november-2026">Anthropic Power Mix: 87% Gas, 11% Coal by 2028 (Study ...</a></li>
<li><a href="https://www.thebureauinvestigates.com/stories/2026-08-14/misaligned-colossus-musks-data-empire-anthropic">How Musk’s toxic data empire is powering Anthropic’s ...</a></li>
<li><a href="https://en.wikipedia.org/wiki/Colossus_%28data_center%29">Colossus ( data center ) - Wikipedia</a></li>
<li><a href="https://www.politico.com/news/magazine/2026/08/02/the-new-luddites-01017824">Anger Over Data Centers Is Fueling a New Political... - POLITICO</a></li>
<li><a href="https://www.motherjones.com/politics/2026/06/xai-data-center-neighbors-angry-spacex-ipo-gas-turbines-colossus-pm2-5-elon-musk-trillionaire-pollution-asthma/">People Living Near xAI’s Dirty Data Centers Are Right Pissed About...</a></li>

</ul>
</details>

**标签**: `#AI infrastructure`, `#data center energy`, `#Anthropic`, `#climate impact`, `#Hacker News discussion`

---

## 科技博客

<a id="item-tech-blog-1"></a>
### [不确定时，不妨有章法地乱试](https://seangoedecke.com/when-in-doubt-flail-about/) ⭐️ 6.0/10

rss · Sean Goedecke · 11月23日 00:00

**「背景」** 面对没有明确指引、也不知道什么才有用的局面，作者认为谨慎等待、先弄清再动手通常不是最优解，主动“乱试一通”反而更快。他也承认这是危险建议：乱试得不好会损害声誉。

**「方案」** 他把有效的乱试归纳为三点：大量尝试、紧盯反馈、无情砍掉没有正反馈的方案。多试是为了直接接触现实，也因为多数想法注定糟糕——试十个才可能有一个可行；方案多才不会过度投入，才舍得放弃。这适用于三类场景：产品尚未找到市场契合时，他在已退役的 GitHub Models 上做了许多不奏效的功能，其中“用 GitHub Actions token 运行 AI 推理”意外有黏性，成为“Continuous AI”的种子；系统过于复杂时，与其通读全局，不如做一批投机性改动看效果再决定深入或放弃，AI agent 很适合批量生成重构方案供筛选；组织层面，当两个团队不沟通、或总监/VP 说不清某团队为何不满时，可自动化手工工作、主动接手任务、提出长期方案。组织场景最需要对反馈敏感：及时放弃失败方案能积累信任，忽视反馈则会让不满转向自己。他坚持叫“乱试”，是因为从内部感受看确实像反复失败、像出丑，但上级看到的可能是一个主动实验的工程师。

**「启示」** 在信息不足时，带着对反馈的高度敏感快速试错、果断放弃，比等待完整理解更有效；那种“我在乱试”的难堪是过程的一部分，而非出问题的信号。

**标签**: `#engineering-advice`, `#experimentation`, `#uncertainty`, `#product-development`, `#organizational-dynamics`

---

## 财经新闻

<a id="item-finance-news-1"></a>
### [美股科技股大跌 亚洲多地推出稳市措施](https://news.bjd.com.cn/2026/11/22/12039852.shtml) ⭐️ 9.0/10

据新华社、韩联社和中央社报道，美国 AI 科技股周五遭大规模抛售，纳斯达克指数单日下跌 5.28%，费城半导体指数重挫近 11%。随后中国内地将融资保证金最低比例下调至 80%，韩国自 11 月 24 日起为期 3 个月放宽上市公司每日回购订单数量限制，中国台湾地区自 11 月 23 日起禁止平盘以下卖空，并将融券保证金比例由 130%提高至 150%。

telegram · zaihuapd · 11月22日 13:24

**「背景」** 11 月初，纳斯达克综合指数曾因科技股抛售单日下跌 5.5%，较近期高点回落逾 10%；费城半导体指数追踪 30 家主要美国上市芯片公司，是观察芯片股走势的行业基准。

**「影响」** 这些调整将直接改变中国内地融资交易者、韩国通过回购护盘的上市公司以及中国台湾地区卖空和借券参与者的交易成本与操作空间。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.nytimes.com/2026/11/05/business/stocks-midterms-artificial-intelligence.html">Stocks Erase Post-Midterm Elections Rally, Dragged Down by Tech ...</a></li>
<li><a href="https://www.gate.com/crypto-wiki/article/semiconductor-index-crash-largest-sox-declines">Semiconductor Index Selloffs : Largest SOX Declines | Gate Wiki</a></li>

</ul>
</details>

**标签**: `#US tech stocks`, `#market selloff`, `#Asian markets`, `#short-selling rules`, `#financial regulation`

---