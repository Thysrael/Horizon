---
layout: default
title: "Horizon Summary: 2026-11-02 (ZH)"
date: 2026-11-02
lang: zh
---

> 从 20 条内容中筛选出 5 条重要资讯。

---

**科技新闻**
1. [Mathematics has changed. Let&\#x27;s act like it](#item-tech-news-1) ⭐️ 8.0/10
2. [The AI cost of JavaScript frameworks](#item-tech-news-2) ⭐️ 7.0/10
3. [联想指纹 U 盘被指内部只是未加密 SD 卡](#item-tech-news-3) ⭐️ 7.0/10
4. [CLEAR 报告：部分语言 AI 分词成本最高相差 17 倍](#item-tech-news-4) ⭐️ 7.0/10

**科技博客**
1. [数据中心反弹跨党派：中期选举与 2028 年管道风险](#item-tech-blog-1) ⭐️ 7.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [Mathematics has changed. Let&\#x27;s act like it](https://terrytao.wordpress.com/2026/11/01/mathematics-has-changed-lets-act-like-it/) ⭐️ 8.0/10

A Terry Tao essay argues that AI has fundamentally changed mathematical practice and that the field must adapt its norms around proof, verification, and credit.

hackernews · smilelamp · 11月1日 18:28 · [社区讨论](https://news.ycombinator.com/item?id=50328251)

**标签**: `#AI in mathematics`, `#proof verification`, `#research culture`, `#human-AI collaboration`, `#scientific credit`

---

<a id="item-tech-news-2"></a>
### [The AI cost of JavaScript frameworks](https://nolanlawson.com/2026/10/28/the-ai-cost-of-javascript-frameworks/) ⭐️ 7.0/10

An analysis of how AI coding agents affect the costs and tradeoffs of JavaScript frameworks, accompanied by community debate about framework value, hiring, and long-running project maintainability.

hackernews · luu · 11月1日 06:06 · [社区讨论](https://news.ycombinator.com/item?id=50323088)

**标签**: `#JavaScript frameworks`, `#AI coding agents`, `#web development`, `#software architecture`, `#developer productivity`

---

<a id="item-tech-news-3"></a>
### [联想指纹 U 盘被指内部只是未加密 SD 卡](https://www.reddit.com/r/technology/comments/1xl2pr3/lenovos_encrypted_fingerprint_usb_drive_is_just/) ⭐️ 7.0/10

有报道称，联想一款以加密和指纹认证为卖点的 USB 存储设备，内部只是一张未加密的 SD 卡装在外壳里，存储介质本身并没有受到加密保护。对购买该产品的用户而言，这意味着不能把设备宣传的“加密”当作数据保护依据；在联想回应或独立验证出现前，相关安全性仍属未证实。

hackernews · entryleveljobsc · 11月1日 14:34 · [社区讨论](https://news.ycombinator.com/item?id=50326099)

**「背景」** 联想以 ThinkPlus FU 100 的名称销售这款指纹 U 盘，并宣称其具备 AES-256 硬件加密。据 Tom&\#x27;s Hardware 报道，安全研究员 Xiusheng Li 在 3 月的一次会议演讲中称，该产品的指纹模块只控制 U 盘与电脑的连接，内部实际是一张存放未加密文件的普通 SD 卡，因此能接触设备的人可直接取出存储卡读取数据。

**「实际影响」** 如果该发现成立，已购买者应把该设备当作未加密存储处理，改用操作系统或可信工具创建的加密卷保护敏感文件，而不是依赖指纹锁。

**「社区讨论」** 评论者质疑联想为何还能被信任制造安全硬件，有人认为这已不是普通漏洞，而是设计审查和产品审批失效；也有评论主张不要依赖厂商的封闭加密，而应在设备之上使用自由软件加密。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.tomshardware.com/tech-industry/cyber-security/lenovo-fingerprint-usb-stick-sold-as-aes-256-encrypted-had-a-plain-sd-card-inside-ai-assisted-follow-up-finds-a-backdoor-and-hardcoded-keys-in-other-secure-usb-products">Lenovo &#x27;s &#x27; encrypted &#x27; fingerprint USB drive is just... | Tom &#x27; s ...</a></li>
<li><a href="https://dzen.ru/a/audnrfxZjwBIzYOC">Lenovo ThinkPlus FU 100 с отпечатком пальца хранила... | Дзен</a></li>

</ul>
</details>

**标签**: `#hardware security`, `#encryption`, `#consumer electronics`, `#Lenovo`, `#fingerprint authentication`

---

<a id="item-tech-news-4"></a>
### [CLEAR 报告：部分语言 AI 分词成本最高相差 17 倍](https://clear-languages.org/blog/the-tokenizer-tax) ⭐️ 7.0/10

CLEAR 研究联盟发布的报告称，主流 AI 模型的分词器明显偏向英语和高资源语言，不同语言处理相同内容时的 Token 消耗差距最高达 17 倍。报告举例称，同一句话用英语需 13 个 Token，用马拉雅拉姆语需 26 个，用阿姆哈拉语则需 78 个；研究覆盖约 200 种语言。报告指出，这种“分词器税”会推高按 Token 计费场景下的使用成本，并增加响应延迟、压缩模型的有效上下文容量。

telegram · zaihuapd · 11月1日 16:06

**「背景」** 分词器会把文本切成模型实际处理的子词单元，其词表规模和训练语料决定了同一段内容会消耗多少 token；英语等高资源语言通常能获得更细、更高效的切分。CLEAR 的报告正是基于这一机制比较约 200 种语言，而 arXiv 上一项相关研究的摘要称，改用 XLM-R、o200k\_base 等多语言分词器可把 Indic 语言的分词器税平均降低 73%，说明差距部分来自词表设计，而非语言本身。

**「实际影响」** 对面向多语言用户的开发者而言，同样的语义内容在部分语言下会占用更大的 Token 预算和上下文窗口，按 Token 计费时成本更高；在规划多语言产品、定价和上下文长度时，需要把分词器差异计入容量与费用估算。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://arxiv.org/abs/2607.24276">[2607.24276] The Tokenizer Tax : Quantifying and Explaining the...</a></li>

</ul>
</details>

**标签**: `#tokenization`, `#multilingual AI`, `#LLM cost`, `#AI fairness`, `#NLP research`

---

## 科技博客

<a id="item-tech-blog-1"></a>
### [数据中心反弹跨党派：中期选举与 2028 年管道风险](https://newsletter.semianalysis.com/p/the-datacenter-backlash-goes-bipartisan) ⭐️ 7.0/10

rss · SemiAnalysis · 11月1日 18:40

**「背景」** 美国数据中心建设正遭遇跨党派反弹，而 11 月 3 日中期选举将改选多个关键州的州长、议会和公用事业委员会，进而影响未开工产能的审批、税收与电价规则。

**「方案」** 作者用 SemiAnalysis 模型把已开工的 2027 年管道与尚未开工的 2028 年管道分开：前 20 州 33.8GW 中约四分之三已开工，因此 2027 年全球+50GW 预测受选举影响有限；真正的风险在 2028 年美国 62.2GW 净新增，其中 13 个重点州占 43.5GW（70%），10 个州将选州长。近期三项变化加剧了风险：得州 TCEQ 于 9 月 21 日暂停许可、俄勒冈于 10 月 9 日把州土地冻结扩大到空气和水排放许可，以及 20 名候选人中 9 人主张暂停新建、11 人主张附加条件，且两党分布大致均衡。作者判断最大近端风险是得州许可冻结拖延——该州占 2028 年美国新增近 30%；若 ERCOT 在 12 月 10 日报告后重启，中断较短，若 Hinojosa 当选并把审批冻结到 2027 年会期立法（1 月 12 日至 5 月 31 日），则从 9 月起约八个月、新规落地后接近一年，比 12 月重启多五到九个月。若所有主张暂停的候选人胜选，约 30GW 的 2028 年计划产能面临审批暴露；若较宽松候选人胜选则降至 5.7GW，但税收优惠减少、更多并网成本由开发商承担仍会恶化环境。作者按未开工产能和政治可变性分三档，并提醒候选人承诺被按字面采信，实际延迟取决于项目所处阶段和许可是否被卡。

**「启示」** 作者的核心结论是：选举挡不住已开工的 2027 年建设，却可能通过州级许可冻结显著推迟 2028 年尚未开工的管道；影响大小取决于哪个决策者能改变规则、冻结持续多久，以及项目是否正好卡在需要该许可的阶段。

**标签**: `#datacenter policy`, `#power infrastructure`, `#permitting risk`, `#US midterms`, `#capacity forecasting`

---