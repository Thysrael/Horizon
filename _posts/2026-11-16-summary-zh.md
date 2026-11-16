---
layout: default
title: "Horizon Summary: 2026-11-16 (ZH)"
date: 2026-11-16
lang: zh
---

> 从 24 条内容中筛选出 6 条重要资讯。

---

**科技新闻**
1. [美团开源 LongCat-2.5：称全程用华为升腾训练](#item-tech-news-1) ⭐️ 8.0/10
2. [MacBook Pro OLED 屏幕 PWM 频闪问题引发讨论](#item-tech-news-2) ⭐️ 7.0/10
3. [位置嵌入文章引发群表示论讨论](#item-tech-news-3) ⭐️ 7.0/10
4. [德国酒店氯气事故被指与 Microsoft 365 邮件中断有关](#item-tech-news-4) ⭐️ 7.0/10
5. [特斯拉 Cybercab 条款：月费 299 美元方可运行](#item-tech-news-5) ⭐️ 7.0/10
6. [FAA 全国停飞：铜线换光纤升级引发路由故障](#item-tech-news-6) ⭐️ 7.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [美团开源 LongCat-2.5：称全程用华为升腾训练](https://the-decoder.com/meituan-releases-a-1-6-trillion-parameter-agent-model-that-never-touched-an-nvidia-gpu/) ⭐️ 8.0/10

美团 LongCat 团队在模型发布一周后开源了总参数量 1.6 万亿的 LongCat-2.5。该模型面向可自主执行长链路、多步骤任务的智能体，尤其侧重编程；官方称其每个 token 激活约 480 亿参数，并支持文本、图像和视频输入。权重以 MIT 许可证发布、允许商用，官方还称训练全程使用华为升腾加速卡，未使用英伟达 GPU。在 Terminal Bench v2.1 上，LongCat-2.5 得 88.4 分，略低于 Claude Opus 5 的 89.1 分；上述训练与基准结果均来自发布方，尚未在本文中获得独立验证。

telegram · zaihuapd · 11月15日 11:08

**「背景」** LongCat-2.5 是美团 LongCat 团队面向长程智能体任务推出的原生多模态 MoE 模型：总参数为 1.6 万亿，但每个 token 只激活约 480 亿参数，模型卡将代码智能体列为主要场景。此次开放权重距离该模型正式发布约一周，属于先发布模型、后公开权重的节奏。

**「影响」** 对开发者和企业来说，MIT 许可证允许直接商用、修改和再分发权重，降低了基于该模型构建编程智能体的许可障碍；但采用前应自行复现 Terminal Bench v2.1 结果，并核查升腾训练栈的复现与部署条件，因为关键性能与硬件声明目前只有官方说法。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://huggingface.co/meituan-longcat/LongCat-2.5">meituan - longcat / LongCat - 2 . 5 · Hugging Face</a></li>

</ul>
</details>

**标签**: `#open-source AI`, `#large language models`, `#agentic coding`, `#Huawei Ascend`, `#AI hardware`

---

<a id="item-tech-news-2"></a>
### [MacBook Pro OLED 屏幕 PWM 频闪问题引发讨论](https://macanorak.com/the-macbook-pros-oled-pwm-problem-when-a-better-display-becomes-worse-to-use/) ⭐️ 7.0/10

一篇技术文章讨论 MacBook Pro OLED 显示屏的 PWM 调光频闪，以及这种调光方式可能给对频闪敏感的用户带来的使用问题。现有材料未提供可独立核验的测量细节，相关频率结论仍存在争议。

hackernews · MacAnorak · 11月15日 13:15 · [社区讨论](https://news.ycombinator.com/item?id=50506719)

**「背景」** Horizon 10 月 29 日的日报曾报道，苹果为新一代 14/16 英寸 MacBook Pro 首次采用串联 OLED 的 PROLED XDR 屏，并称峰值亮度达 2000 尼特；这些是 Apple 公布、当时尚待独立实测的规格。PWM 调光通过快速切换像素亮度来调节明暗，频率越低，部分敏感用户越容易感到闪烁并出现头痛或眼疲劳；AppleInsider 11 月 10 日报道称，该机的 PWM 频率为 240Hz、闪烁幅度为 56%，并强调这与屏幕刷新率不是同一指标。

**「对闪烁敏感用户的影响」** 对闪烁敏感的用户而言，这块屏幕是否可用取决于实际 PWM 调光行为，而评论区对频率的测算仍有分歧（240 Hz、480 Hz 甚至有效 960 Hz），因此单凭一个标称数字无法判断。RTINGS 的测试说明也指出，PWM 引入的闪烁对敏感人群可能非常干扰；这类用户在购买前应实地体验样机，而不是只看规格或单一测评结论。

**「社区讨论」** 评论者 legitronics 对 240Hz 的测量说法提出异议，认为串联 OLED 可能在 480Hz、180 度反相下形成最高 960Hz 的有效频闪，并质疑测试设备是否只是输出了 240Hz；这属于评论者的推测，未获独立确认。xp84 则描述了更严重的个体体验：家人对吊扇与灯光形成的轻微闪烁也会出现恶心和头痛，说明不同人对频闪的敏感程度差异很大。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.apple.com/newsroom/2026/10/apple-unveils-groundbreaking-macbook-pro-with-proled-xdr-display/">2026-10-29 — Apple 新款 MacBook Pro 首发 PROLED XDR 屏并加入触控</a></li>
<li><a href="https://appleinsider.com/articles/26/11/10/if-youre-getting-dizzy-using-proled-macbook-pro-you-are-not-alone">Pulse width modulation on MacBook Pro with PROLED - AppleInsider</a></li>
<li><a href="https://www.rtings.com/tv/tests/motion/pwm-flicker">Our TV Motion Tests: PWM Flicker - RTINGS.com</a></li>

</ul>
</details>

**标签**: `#OLED displays`, `#PWM flicker`, `#MacBook Pro`, `#display ergonomics`, `#hardware accessibility`

---

<a id="item-tech-news-3"></a>
### [位置嵌入文章引发群表示论讨论](https://magazine.sebastianraschka.com/p/understanding-positional-embeddings) ⭐️ 7.0/10

一篇题为《Understanding Positional Embeddings in Modern LLMs》的技术文章已发布，面向希望了解现代大语言模型位置嵌入实现方式的读者。文章重点在实现层面；Hacker News 讨论中的评论则认为，要真正理解位置嵌入还需要其群表示论基础。当前提供的材料未给出文章涉及的具体模型、版本或实验数据。

hackernews · vismit2000 · 11月15日 12:14 · [社区讨论](https://news.ycombinator.com/item?id=50506376)

**「背景」** 位置嵌入用于让 Transformer 在没有循环结构的情况下区分 token 的先后顺序。原始 Transformer 使用正弦位置嵌入，之后出现可学习的绝对位置嵌入，而现代 LLM 更常用 RoPE（旋转位置嵌入），因为它更自然地融入注意力机制，并且在扩展性上优于旧的绝对位置方案。

**「社区讨论」** 评论者 programjames 认为，文章只讲实现不足以真正理解位置嵌入，因为位置嵌入本质上是群表示，掌握这套理论才能找到并参数化可学习的位置嵌入。该评论以旋转位置嵌入为例，称其是平移群的表示。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://sebastianraschka.com/llms-from-scratch/ch04/10_rope/">Rotary Positional Embeddings (RoPE) | Sebastian Raschka , PhD</a></li>
<li><a href="https://simonhalvdansson.github.io/posts/llm-training/">Five minute LLMs | Simon Halvdansson</a></li>

</ul>
</details>

**标签**: `#positional embeddings`, `#LLMs`, `#transformer architecture`, `#machine learning education`

---

<a id="item-tech-news-4"></a>
### [德国酒店氯气事故被指与 Microsoft 365 邮件中断有关](https://www1.wdr.de/nrw/rheinland/rhein-erft-kreis/technischer-defekt-chlor-phantasialand-100.html) ⭐️ 7.0/10

德国 WDR 报道，Phantasialand 酒店发生氯气泄漏，导致 15 名住客受伤；酒店方面称，此事与 Microsoft 365 中断期间未收到安全警报邮件有关。据该公司向 WDR 说明，泳池自动加氯系统投加了过量氯，而桑拿区域维护安全系统此前发出的邮件警报无人看到。目前这一因果链只有运营方说法，缺少独立验证，应视为已报告的事故关联，而非已确认的唯一原因。

hackernews · DeepLogin · 11月15日 18:36 · [社区讨论](https://news.ycombinator.com/item?id=50509411)

**「背景」** 据 Tom&\#x27;s Hardware 与 WDR 的转述，这起事件发生在德国 Phantasialand 的酒店桑拿与泳池区域：自动加氯系统投加了过量氯，维护安全系统随后发出了一封电子邮件告警，但当时 Microsoft 365 邮件服务正在发生故障，因此没有人看到这封告警。这类泳池水质监控通常依靠闭环加氯和传感器告警；如果告警通道只有电子邮件，没有独立的冗余路径，云服务的可用性就直接关系到人身安全。

**「影响」** 对依赖云端邮件发送安全警报的泳池、桑拿等设施，运营方需要配置不依赖 Microsoft 365 的本地声光报警、短信或电话升级和人工复核；否则单一邮件通道中断时，加氯过量等故障可能无人及时处置。

**「社区讨论」** 多位评论者认为责任在酒店而非 Microsoft，批评把可能造成人身伤害的警报只交给电子邮件、没有备份或二次确认；一名自称在 Azure 工作的评论者还强调，这不是为服务中断辩护，且自己没有阅读原文。另有评论从闭环加氯系统角度指出，传感器故障常表现为测得余氯偏低或为零，从而触发过量投加，因此需要独立于自动系统的安全保护。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.tomshardware.com/tech-industry/data-centers/microsoft-365-outage-leads-to-chlorine-gas-poisoning-of-15-hotel-guests-email-warning-system-fails-40-first-responders-deployed-for-triage-four-hospitalized">Microsoft 365 outage leads to chlorine gas poisoning of 15 hotel ...</a></li>
<li><a href="https://news.ycombinator.com/item?id=50509411">Microsoft 365 outage leads to chlorine gas poisoning of 15 hotel ...</a></li>

</ul>
</details>

**标签**: `#cloud reliability`, `#safety-critical systems`, `#incident analysis`, `#Microsoft 365`, `#system resilience`

---

<a id="item-tech-news-5"></a>
### [特斯拉 Cybercab 条款：月费 299 美元方可运行](https://www.tesla.com/configurator/api/v4/terms?category=autonomy_subs&amp;amp;locale=en_US&amp;amp;model=cc&amp;amp;saleType=Sale) ⭐️ 7.0/10

一份被报道的特斯拉 Cybercab 订阅条款显示，车辆售价为 29,990 美元，但车主必须每月支付 299 美元的自动驾驶订阅费，否则车辆无法运行。条款还规定，特斯拉可提前一个月通知调价；欠费或违规使用可导致订阅被暂停或取消，累计三次警告则停用自动驾驶一周。车辆被限制在指定区域运行，未经授权不得接入网约车、配送或租赁平台。上述条款来自媒体报道，尚未见独立验证。

telegram · zaihuapd · 11月15日 01:10

**「背景」** Cybercab 是特斯拉为无人驾驶运营设计的双座车型，没有方向盘和踏板；Horizon 4 月 25 日的日报曾报道，特斯拉已于 2026 年 2 月在北美工厂启动其量产。此次披露的协议把个人车主的使用与每月 299 美元的自动驾驶订阅绑定，并限定车辆只能在指定区域运行。

**「影响」** 对车主而言，29,990 美元的购车价并不包含持续使用成本；一旦订阅欠费，车辆就不能运行。地理围栏和平台接入限制也意味着，Cybercab 不能被自由用于网约车、配送或租赁运营。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://weibo.com/3615027564/QCheybgVu">2026-04-25 — Tesla Cybercab Enters Production in North America</a></li>

</ul>
</details>

**标签**: `#Tesla`, `#Cybercab`, `#autonomous driving`, `#subscription model`, `#robotaxi`

---

<a id="item-tech-news-6"></a>
### [FAA 全国停飞：铜线换光纤升级引发路由故障](https://www.theverge.com/transportation/1033898/faa-ground-stop-sean-duffy-faa-copper-wire) ⭐️ 7.0/10

美国交通部长 Sean Duffy 在 11 月 14 日表示，FAA 周五下令的全国停飞源于一处偏远设施在例行维护中将老旧铜线更换为光纤，新装路由器随后发生故障，导致数千架次航班停飞。Duffy 称根本原因尚未查明，可能是硬件故障、配置错误或承包商 L3Harris 的操作失误；该路由器每 4 到 5 秒向其他路由器发出逾千次连接请求，干扰了雷达信号和飞机通信。上述停飞原因属于官方初步说明，并非已确认的最终调查结论。

telegram · zaihuapd · 11月15日 02:10

**「背景」** FAA 的空管通信仍依赖大量老旧电信线路：Horizon 2026 年 9 月 22 日的日报曾报道，FAA 因一条光纤线路被切断而暂停美国东海岸多个繁忙机场的部分航班，说明通信链路故障会直接传导为航班运行中断。据 CNBC 报道，本次涉事设施位于阿肯色州南部，升级对象是承包商 L3Harris 维护的一套较旧通信系统。

**「对航空运营的影响」** 对航空公司和旅客的直接后果是：一个偏远站点的路由器异常即可触发全国停飞，导致数千航班停飞。鉴于根因仍未确定（可能是硬件故障、配置错误或承包商 L3Harris 操作失误），FAA 在继续铜改光纤时应把新路由器隔离测试、连接请求限速和快速回退设为割接放行条件，否则同类例行升级仍可能再次干扰雷达与地空通信。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.reuters.com/world/us/faa-halts-some-us-east-coast-flights-due-communication-issues-2026-09-21/">2026-09-22 — FAA 称光纤被切断，美国东海岸多个机场航班暂停</a></li>
<li><a href="https://www.cnbc.com/2026/11/14/faa-ground-stop-flights-resume-delays.html">Duffy ties router in southern Arkansas to nationwide ground stop</a></li>
<li><a href="https://www.cnn.com/2026/11/13/us/live-news/flights-ground-stop-faa">November 13, 2026 — Some US flights resume after... | CNN</a></li>

</ul>
</details>

**标签**: `#FAA`, `#network outage`, `#air traffic control`, `#routing failure`, `#critical infrastructure`

---