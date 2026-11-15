---
layout: default
title: "Horizon Summary: 2026-11-15 (ZH)"
date: 2026-11-15
lang: zh
---

> 从 25 条内容中筛选出 4 条重要资讯。

---

**科技新闻**
1. [Lovable 应用因 RLS 不足泄露护照信息和 20 万条私信](#item-tech-news-1) ⭐️ 8.0/10
2. [星舰第 15 次试飞首次由发射塔捕获飞船](#item-tech-news-2) ⭐️ 8.0/10
3. [PyPI 改版项目页面上线，突出安全与来源信号](#item-tech-news-3) ⭐️ 7.0/10
4. [意大利因 Facebook 相册访问罚 Meta 8.05 亿欧元](#item-tech-news-4) ⭐️ 7.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [Lovable 应用因 RLS 不足泄露护照信息和 20 万条私信](https://www.crissyfield.de/research/lovable-en/) ⭐️ 8.0/10

Crissy Field 的研究人员披露，多个用 Lovable 构建的应用因行级安全（RLS）配置不足，暴露了护照信息和超过 20 万条私信。Lovable 安全负责人 Igor 在讨论中确认，根本原因就是 RLS 配置不足；他还表示，平台会在发布前自动扫描所有应用，并提供对所有用户免费的深度 SAST 扫描。发现问题后，用户可点击“Fix”修复，或开启后台自动修复。现有材料没有说明受影响应用的具体数量、泄露持续时间，也没有证明自动扫描能覆盖已经发布的应用。

hackernews · armcat · 11月14日 17:43 · [社区讨论](https://news.ycombinator.com/item?id=50499017)

**「背景」** Lovable 生成的应用通常依托 Supabase 的 Postgres 与 Data API：表通过 anon、authenticated 等角色暴露给前端，而 Row-Level Security（RLS）策略决定哪些行可被读写；若表有访问授权却缺少或写错 RLS，浏览器端就能直接取到数据。Supabase 自 2026 年 10 月 30 日起不再自动把 public schema 中的新表授权给 anon、authenticated 和 service\_role，因此新表需显式授权后 Data API 才能访问；这一默认变更降低了新项目误暴露的风险，但并不能替代为已有表配置正确的 RLS。

**「影响」** 对使用 Lovable 发布应用的开发者，最直接的后果是必须逐表核对 RLS 策略和公开 API 的可读范围，不能把“发布前自动扫描”当作安全保证；Lovable 的修复功能是否默认开启、能否覆盖既有应用，现有材料未说明。已暴露护照信息的应用还应评估通知受影响用户，并收紧数据访问权限。

**「社区讨论」** 评论区的争论集中在责任归属：有评论者认为，Supabase 早期为降低上手门槛而设定的默认权限也难辞其咎，并称相关默认值据称已在 10 月 30 日修复，但已有项目可能仍沿用旧设置；也有评论者强调，AI 生成应用数量多，攻击者无需复杂黑客技术，仅通过浏览器检查网络请求就可能发现暴露，平台应改为默认拒绝并加入自动化认证测试。Lovable 安全负责人则把根本原因归于应用层 RLS 配置不足，并强调发布前扫描和免费修复流程。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.putthrough.com/blog/supabase-permission-denied-for-table">Supabase “permission denied for table” (42501): the safe fix</a></li>

</ul>
</details>

**标签**: `#security`, `#row-level-security`, `#supabase`, `#ai-code-generation`, `#data-breach`

---

<a id="item-tech-news-2"></a>
### [星舰第 15 次试飞首次由发射塔捕获飞船](https://www.spacex.com/launches/starship-flight-15) ⭐️ 8.0/10

SpaceX 宣布，星舰第 15 次试飞中，飞船在轨约 22.5 小时、绕地球约 14 圈后返回得克萨斯州星舰基地，首次由发射塔机械臂直接捕获；SpaceX 称这是首次由发射塔机械臂捕获完成轨道返回的轨道级飞船。任务还部署了 26 颗 Starlink V3 卫星，其中 3 颗带摄像头用于检查隔热瓦。超重型助推器未按计划返回发射塔，因技术问题改在墨西哥湾受控溅落并爆炸，具体原因未公布，因此两级同时回收尚未实现。

hackernews · ls612 · 11月14日 21:22 · [社区讨论](https://news.ycombinator.com/item?id=50500963)

**「背景」** 星舰复用方案的关键环节是让返回的飞行器降到发射塔旁，由机械臂夹住承接点，而不是依靠着陆腿落地。10 月 22 日的 Horizon 日报曾报道，马斯克称 SpaceX 计划在 11 月首次同时尝试塔捕星舰飞船和超重型助推器，并提醒首次尝试不保证成功；当时他还提到，前一次发射因一台发动机提前关机，助推器和飞船均未回收。Flight 15 把这一计划推进了一步：飞船完成塔捕，但助推器未能返塔，两级同时回收仍未实现。

**「影响」** 对复用流程而言，关键限制仍在助推器：本次它未返回发射塔；后续需要验证助推器塔捕、两级同时回收，以及捕获后的飞船复飞，才能验证完全复用。

**「社区讨论」** 有评论者认为，星舰相当于把航天飞机方案做对：助推器完全复用且不带固体助推器，轨道器置于顶部，并以流水线方式生产。也有人强调，只有隔热瓦经受住再入、助推器同样实现塔捕并复飞同一艘飞船后，低成本入轨才会成立；另有评论指出最终入轨质量比仍不清楚。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.theverge.com/science/1014913/spacex-will-try-catching-starship-and-its-booster-for-first-time-musk-says">2026-10-22 — SpaceX 下月首次尝试同时回收星舰与助推器</a></li>

</ul>
</details>

**标签**: `#SpaceX`, `#Starship`, `#reusable rockets`, `#spaceflight`, `#hardware`

---

<a id="item-tech-news-3"></a>
### [PyPI 改版项目页面上线，突出安全与来源信号](https://blog.pypi.org/posts/2026-11-06-ui-updates-complete/) ⭐️ 7.0/10

PyPI 已完成项目页面改版并正式上线，新界面把安全与来源（provenance）信息更醒目地呈现给访问者。社区成员举例说明了实际效果：dlt 的项目文件页没有 provenance 记录，而 datasette 的文件页带有 provenance 标记，说明该信号按项目逐个显示。此次更新面向所有浏览 PyPI 的 Python 开发者，属于在既有页面上增加信任提示的增量改动，而非新的发布或签名机制。

hackernews · rbanffy · 11月14日 15:40 · [社区讨论](https://news.ycombinator.com/item?id=50497892)

**「背景：信任发布与来源证明」** 新版项目页所展示的来源（provenance）信号，建立在 PyPI 近年推行的“信任发布”（trusted publishing）机制之上。Horizon 6 月 10 日的日报曾报道，Python 软件基金会的 Mike Fiedler 在北美开源峰会上介绍，信任发布用基于 OpenID Connect 的短期凭证取代长期有效的 API 令牌，以降低凭证被窃取的供应链攻击风险，当时该机制已覆盖 PyPI 超过 36% 的上传。正是这类通过 OIDC 完成的上传才能生成可供页面展示的证明记录，本次改版把这些原本偏底层的安全信息呈现到了项目页面上。

**「对使用者的影响」** 开发者现在可以在安装前查看项目文件页上的 provenance 标记，以此判断某个发行包是否带有可追溯的构建来源；未生成 provenance 的项目在该页面上不会显示这一信号。对维护者而言，这意味着是否能展示来源信息取决于其发布流程是否产出了相应的证明，评论区提到的 Trusted Publishing 可复用工作流支持仍是待解决的问题。

**「社区讨论」** 有评论者（time4tea）质疑整个信任链条本质上是中心化的，依赖“大型云厂商”并可能造成锁定，认为这有违 Python 社区的风格；另一些人则支持 Sigstore 式“无密钥”短时签名，希望出现更多托管 CI/CD 提供商来满足 OIDC 要求（samhclark），并呼吁 Trusted Publishing 尽快支持可复用工作流（mhils）。cowlevel 则指出该机制的检测范围有限：它能发现原有正常项目被入侵但私钥未泄露的情况，并不能识别本身就是恶意的项目。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://lwn.net/Articles/1076205/">2026-06-10 — Trusted Publishing Replaces Long-Lived Credentials</a></li>

</ul>
</details>

**标签**: `#PyPI`, `#supply-chain-security`, `#provenance`, `#sigstore`, `#open-source`

---

<a id="item-tech-news-4"></a>
### [意大利因 Facebook 相册访问罚 Meta 8.05 亿欧元](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/10321080) ⭐️ 7.0/10

意大利隐私监管机构 Garante Privacy 对 Meta 处以 8.05 亿欧元罚款，指其 Facebook Android 应用在未取得具体同意的情况下读取约 2000 万意大利用户的相册照片、视频和元数据。涉事功能是 2023 年上线的相册推荐，默认开启且授权提示笼统。监管机构要求 Meta 在 60 天内将其改为默认关闭并单独征得同意，否则不得向未有效授权的用户启用该功能。

telegram · zaihuapd · 11月14日 14:37

**「背景」** 本案的关键概念是“具体同意”：监管机构认为，笼统的授权提示不足以覆盖读取相册照片、视频和元数据这一独立目的。Garante Privacy 因此把合规要求落到产品层面，要求该功能默认关闭并就此单独征得用户同意。

**「影响」** 这项命令要求 Meta 调整 Android 应用的相册访问默认值和授权流程，而不只是更新隐私政策；若 60 天内未满足条件，相册推荐不得对未有效授权的用户启用。

**标签**: `#privacy regulation`, `#Meta`, `#Android permissions`, `#user consent`, `#Italy`

---