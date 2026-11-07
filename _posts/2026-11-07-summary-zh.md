---
layout: default
title: "Horizon Summary: 2026-11-07 (ZH)"
date: 2026-11-07
lang: zh
---

> 从 41 条内容中筛选出 9 条重要资讯。

---

**科技新闻**
1. [长江存储拟建第四厂，国产设备占比最高 70%](#item-tech-news-1) ⭐️ 8.0/10
2. [Jev 按需求助 Opus，身份解析成本降至约四分之一](#item-tech-news-2) ⭐️ 7.0/10
3. [Linux 内核锁定下的休眠兼容补丁提案](#item-tech-news-3) ⭐️ 7.0/10
4. [月之暗面据称洽谈在欧洲租用逾 8000 颗 Blackwell GPU](#item-tech-news-4) ⭐️ 7.0/10
5. [百度开源文心 5.5 Flash Base：2800 亿参数 MoE、支持百万级上下文](#item-tech-news-5) ⭐️ 7.0/10
6. [淘宝 MNN 开源 0.3B 手机端离线模型](#item-tech-news-6) ⭐️ 7.0/10

**科技博客**
1. [与设计师协作的收益与代价](#item-tech-blog-1) ⭐️ 7.0/10
2. [FLUX 3 Image Klein 的 Blackwell 推理优化实测](#item-tech-blog-2) ⭐️ 7.0/10
3. [Reshard 集合通信加速强化学习权重重载](#item-tech-blog-3) ⭐️ 7.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [长江存储拟建第四厂，国产设备占比最高 70%](https://www.reuters.com/world/china/chinas-top-flash-memory-chipmaker-targets-more-homegrown-tools-new-factory-2026-11-06/) ⭐️ 8.0/10

长江存储计划在武汉建设第四座工厂，拟于 2027 年开工，目标将国产设备采购比例提高到至少 60%、最高 70%，高于第三座工厂目前超过 50%的水平。新厂将生产 300 层以上的 NAND 闪存，主要面向数据中心和人工智能存储需求。报道称，美国出口管制正推动其加快设备国产化，清洗、抛光和刻蚀设备是主要增量，但光刻和检测等先进设备仍依赖海外供应商。长江存储在中国 NAND 市场的份额已升至 38.5%、超过三星，三座新厂全部投产后整体产能有望翻倍。

telegram · zaihuapd · 11月6日 08:34

**「背景」** 长江存储的产能扩张与设备国产化是同步推进的：Horizon 4 月 23 日的日报曾报道，该公司 2026 年一季度收入突破 200 亿元，计划把总产能提升一倍以上，并且武汉三期晶圆厂的国产设备占比首次超过 50%；这为第四座工厂设定 60%–70% 的目标提供了参照基准。NAND 闪存的堆叠层数是衡量存储密度的核心指标，层数越高，单颗芯片的容量就越大，并且对刻蚀、沉积等环节的工艺要求也越高。美国出口管制使设备采购来源成为产能规划中的关键变量，因此国产化比例本身就成了新工厂的一项可量化指标。

**「影响」** 国产清洗、抛光和刻蚀设备供应商是这一计划最直接的相关方：若 60%至 70%的采购目标落地，它们将面对新增的验证和供货需求。与此同时，新厂的光刻和检测设备仍须依赖海外供应商，相关环节的扩产会继续受美国出口管制约束。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.guancha.cn/economy/2026_04_20_814211.shtml">2026-04-23 — 长江存储一季度收入超 200 亿元，计划将产能翻番</a></li>

</ul>
</details>

**标签**: `#semiconductors`, `#NAND flash`, `#China tech`, `#supply chain localization`, `#AI storage`

---

<a id="item-tech-news-2"></a>
### [Jev 按需求助 Opus，身份解析成本降至约四分之一](https://hightouch.com/blog/llm-judges-identity-resolution) ⭐️ 7.0/10

一篇技术博客介绍了一种面向身份解析的 LLM 评审器方案：让 Jev 模型在需要时升级调用 Opus，只在部分样本上求助，从而在该任务上接近直接使用 Opus 的准确率，同时把成本降至约四分之一。该结果来自特定的身份解析实验，并不构成对通用能力或编码代理改进的证明。

hackernews · theanomaly · 11月6日 19:48 · [社区讨论](https://news.ycombinator.com/item?id=50397429)

**「背景」** LLM 裁判是用一个模型给另一个模型的输出打分或做判定的评估方式；Horizon 2026 年 9 月 15 日的日报曾回顾该领域从黄金数据集向 LLM 裁判的演进。身份解析则需要判断不同记录是否指向同一实体，Hightouch 的实验把裁判模型用于这一任务，并测试 Jev 与 GPT-6 Luna 作为裁判、在不确定时升级给 Claude Opus 的混合方案。

**「影响」** 对构建 LLM 评审或数据处理管道的团队而言，这一案例说明可以把强模型调用集中在部分样本上，以较低成本获得接近的判定质量；但采用前应使用自己的身份数据验证升级触发条件和错误分布，因为文中只报告了单一任务的结果。

**「社区讨论」** Hacker News 评论者将这一做法视为模型路由架构的又一实例，核心争点在于弱模型如何判断自己需要升级，尤其是面对未知的未知和知识缺口时。也有人强调这只是身份解析这一特定任务的基准结果，不能外推到通用用法或编码代理；另有评论者报告了类似的级联体验，认为 Jev 多数时候能正确决定是否升级，但指出模型经济性变化很快，最佳做法高度依赖具体任务。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://blog.bytebytego.com/p/llms-as-a-judge-how-to-know-if-your">2026-09-15 — LLM 评估：从黄金数据集到 LLM 裁判</a></li>
<li><a href="https://hightouch.com/blog/llm-judges-identity-resolution">LLM Judges for Identity Resolution at 4x Lower Cost | Hightouch</a></li>

</ul>
</details>

**标签**: `#LLM judges`, `#model cascading`, `#cost optimization`, `#identity resolution`, `#AI evaluation`

---

<a id="item-tech-news-3"></a>
### [Linux 内核锁定下的休眠兼容补丁提案](https://lwn.net/Articles/1103190/) ⭐️ 7.0/10

Matthew Garrett 提交了一组 Linux 内核补丁，旨在让启用 kernel lockdown 的系统重新支持休眠，并防止休眠镜像被篡改或遭降级攻击。由于 lockdown 目前会禁用休眠，补丁改用 TPM 保护签名密钥：内核启动存根先向 PCR 5 写入标记，UEFI 在调用 ExitBootServices\(\) 时封顶该 PCR 以阻止用户空间伪造，随后内核通过可审计的 TPM 会话生成签名密钥和摘要，并用该密钥签名休眠数据。恢复时内核会校验 TPM 签名、重放会话摘要、核对 PCR 5 的当前值以及休眠镜像签名；该方案目前只是提案中的补丁集，尚未合并。

rss · LWN.net · 11月6日 18:51

**「背景」** 内核 lockdown 是一项可选的安全特性，用于阻止对运行中内核的修改；此前它一直禁用休眠，原因是内核无法验证从磁盘读回的内存是否已被篡改。TPM 的平台配置寄存器（PCR）在系统启动时被清零，此后只能由软件以哈希方式“扩展”，因而能反映从固件、引导程序到内核的启动链状态。

**「影响」** 在补丁合入前，启用 lockdown 的系统仍需继续禁用休眠；若按当前设计合入，只有具备可用 TPM、且固件在 ExitBootServices\(\) 时封顶 PCR 5 的设备才能获得这一保护，缺少 TPM 或启动度量链不完整的设备无法满足同样条件。

**标签**: `#Linux kernel`, `#hibernation`, `#kernel security`, `#lockdown`, `#patch set`

---

<a id="item-tech-news-4"></a>
### [月之暗面据称洽谈在欧洲租用逾 8000 颗 Blackwell GPU](https://www.cnbc.com/2026/11/05/moonshot-ai-nvidia-chips-europe-china.html) ⭐️ 7.0/10

据 CNBC 援引知情人士报道，月之暗面正洽谈从欧洲新兴云厂商的数据中心租用逾 8000 颗 Nvidia Blackwell GPU，主要用于推理，也涉及训练。美国出口管制禁止向中国进口 Blackwell，而通过海外云服务远程使用被视为可能的绕行路径。白宫今年 7 月曾称该公司经泰国设施获取过 Blackwell 芯片。报道称，方案之一要求月之暗面比非中国买家多支付 30% 至 50% 的预付款；相关条款仍在洽谈，报道依赖未具名消息源，尚未得到公司或交易对手确认。

telegram · zaihuapd · 11月6日 05:02

**「背景」** Blackwell 是 Nvidia 面向数据中心的 GPU 架构，neocloud 则指专门对外出租 GPU 算力的新型云厂商。Horizon 5 月 15 日日报曾报道，美国商务部批准向约 10 家中国公司出售 Nvidia H200，但当时尚无交付，中方也未批准采购；相比之下，Blackwell 仍在美国对华出口禁令范围内，直接进口被禁止。

**「成本与合规双重风险」** 如果交易成行，月之暗面将需要比非中国买家多付 30%–50% 的预付款来锁定这批欧洲算力，并把主要推理负载放在境外数据中心，因此成本与政策风险会同时上升。美国现行管制针对的是芯片对华出货，而经海外数据中心远程调用被视为一个可绕开的缺口，已有美国议员在讨论堵塞这一“云访问”漏洞；若规则收紧，此类跨境租用可能中断，依赖该路径的开发者需提前准备替代算力方案。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.reuters.com/business/retail-consumer/us-clears-h200-chip-sales-10-china-firms-nvidia-ceo-looks-breakthrough-2026-05-14/">2026-05-15 — US Approves H200 Chip Sales to Chinese Tech Giants</a></li>
<li><a href="https://www.cnbc.com/2026/11/05/moonshot-ai-nvidia-chips-europe-china.html">China&#x27;s Moonshot AI sought Nvidia chip access in Europe amid ...</a></li>
<li><a href="https://www.cnbc.com/2026/08/19/china-ai-nvidia-chips-us-export-controls.html">China AI firms tap Nvidia power overseas as U.S ... - CNBC</a></li>

</ul>
</details>

**标签**: `#Nvidia Blackwell`, `#AI export controls`, `#Moonshot AI`, `#AI compute infrastructure`, `#GPU cloud`

---

<a id="item-tech-news-5"></a>
### [百度开源文心 5.5 Flash Base：2800 亿参数 MoE、支持百万级上下文](https://www.news.cn/info/20261105/f3bbdb6854f5441ca9fb34062f213875/c.html) ⭐️ 7.0/10

百度宣布正式开源基座模型文心 5.5 Flash Base。该模型采用 MoE 架构，总参数量 2800 亿，每个 Token 激活 140 亿参数，预训练使用 33.5 万亿 Token，预训练上下文最长为 128K，微调与推理阶段支持最长 100 万 Token 上下文。报道称，模型围绕“效率”在注意力机制、专家路由和训练目标等环节做了系统性优化，以提升资源利用效率。新华网的报道未披露许可证条款、权重下载方式或基准测试成绩，因此暂时无法独立判断其实际能力与可用范围。

telegram · zaihuapd · 11月6日 05:41

**「背景」** Horizon 5 月 10 日的日报曾报道，百度发布文心 5.1，称其以约为同类模型 6% 的预训练成本取得领先性能。此次开源的文心 5.5 Flash Base 同属文心基座模型序列，采用 2800 亿总参数、每 Token 激活 140 亿参数的 MoE 架构，并支持最长 100 万 Token 的微调与推理上下文。

**「影响」** 对开发者而言，2800 亿总参数只激活 140 亿，意味着单次推理的算力占用更接近一个 140 亿参数的稠密模型；再加上微调与推理可支持最长 100 万 Token 上下文，它适合处理长文档和长代码库这类场景。但能否真正用于生产，仍取决于百度后续公布的权重获取方式与开源许可证条款，这两项在当前报道中均缺失。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://mp.weixin.qq.com/s/_I9ziafHheXiJpA-QY2F7A">2026-05-10 — Baidu Releases ERNIE 5.1 with Record Efficiency</a></li>

</ul>
</details>

**标签**: `#open-source models`, `#Baidu ERNIE`, `#Mixture-of-Experts`, `#long context`, `#LLMs`

---

<a id="item-tech-news-6"></a>
### [淘宝 MNN 开源 0.3B 手机端离线模型](https://www.ithome.com/1/023/212.htm) ⭐️ 7.0/10

淘宝 MNN 团队开源了约 3 亿参数的端侧模型 MNN-Pocket-0.3B，面向手机完全离线推理。该模型在 iPhone 18 Pro 上报告平均解码约 350 token/s，INT4 部署文件为 173 MB；团队设定的目标是峰值内存低于 300 MB、解码超过 200 token/s。模型采用 28 层结构，词表由 151K 精简到 64K，并按预训练、后训练和端侧部署分别开源了多个版本。

telegram · zaihuapd · 11月6日 15:13

**「端侧小模型的定位」** 0.3B 属于亚十亿参数模型。其 Hugging Face 模型卡将目标用途列为端侧助手、数据抽取和轻量级智能体流水线，并明确不推荐用于高等数学、长时间代码生成等推理密集型任务。

**「影响」** 对端侧开发者来说，173 MB 的 INT4 文件和 64K 词表意味着更小的下载与存储占用，可优先在内存受限的手机应用中试用；不过 350 token/s 和低于 300 MB 的目标来自团队在 iPhone 18 Pro 上的报告，其他机型的实际速度和峰值内存仍需实测。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://huggingface.co/taobao-mnn/MNN-Pocket-0.3B">taobao-mnn/MNN-Pocket-0.3B · Hugging Face</a></li>

</ul>
</details>

**标签**: `#on-device AI`, `#open-source models`, `#mobile inference`, `#MNN`, `#quantization`

---

## 科技博客

<a id="item-tech-blog-1"></a>
### [与设计师协作的收益与代价](https://seangoedecke.com/working-with-designers/) ⭐️ 7.0/10

rss · Sean Goedecke · 11月7日 00:00

**「背景」** 作者基于自身经历指出，设计师与工程师的文化距离较远，却常能立刻展现价值；但一个团队配置多名设计师会带来麻烦，而公司用来规模化设计的设计系统也有实际代价。

**「方案」** 作者描述，设计师看到工程师自制的占位 UI 后，能给出明显更好、甚至超出工程师想象的方案，这种价值几乎一眼可见；他们不来自工程背景，也较少像工程师出身的产品经理那样做秘密技术判断，反而更容易建立信任。但他在多个团队反复遇到多设计师同队的麻烦：三名设计师先全盘重做产品，导致前端样式大改，随后又对每页反复推翻彼此，团队只能不断实现新版本，最后靠管理层在截止日前冻结设计；他猜测原因是工程分歧能落在延迟、缺陷等指标上，设计只能靠品味，而且任何设计改动都会影响用户感知的整个产品。设计系统本为规模化一致性而生，却存在激励冲突：维护方追求组件永远优雅，产品团队要满足不优雅的客户需求，嵌入设计师的细微改动又逼工程师用 CSS 补丁或重写组件。兼容性同样棘手：设计系统常基于最新 React，而公司前端混杂着纯 HTML/CSS 或旧版本，设计师看到的版本和工程师可用的版本不完全一致，工程师只能做功能翻译，还要解释整体升级并不容易。作者仍认为设计系统优于替代方案，在版本跟上且设计师没有怪需求时很好用；他也指出并非所有产品都需要设计师，API、账单对账、Markdown/PDF 渲染等没有真正的视觉设计需求。

**「启示」** 作者的核心判断是：设计师能显著提升产品，但团队应一次只配一位，并把设计系统视为必要却会加重前端负担的基础设施；设计并非所有软件的业务关键。

**标签**: `#design systems`, `#designer-engineer collaboration`, `#frontend engineering`, `#team dynamics`

---

<a id="item-tech-blog-2"></a>
### [FLUX 3 Image Klein 的 Blackwell 推理优化实测](https://developer.nvidia.com/blog/speed-up-image-generation-with-flux-3-image-klein-on-nvidia-blackwell-gpus/) ⭐️ 7.0/10

rss · NVIDIA CUDA Technical Blog · 11月6日 22:20

**「背景」** 高分辨率扩散模型需要把数十亿参数的网络反复去噪，注意力成本又随分辨率上升，部署时延迟成为核心约束。FLUX 3 Image Klein 由黑森林实验室提供 Base 与蒸馏检查点，分别权衡延迟与保真度；本文用 TensorRT LLM VisualGen 在 NVIDIA Blackwell 上逐项优化其推理。

**「方案」** 作者先测出 2048×2048 下单张 B200 的去噪占总生成时间 84%–98%，因此重点加速 DiT。NVFP4 相对 BF16 已有 1.62× T2I、1.58× I2I 提升；叠加 torch.compile、PrimsTS 融合 GEMM、VC-Attention FP8、Sol-Attention 与 Cache-DiT 后，Base 端到端达 3.46× T2I（22.36→6.46 秒）和 4.45× I2I（54.64→12.28 秒），蒸馏版最高 2.34×。作者用 LPIPS 量化代价：VC-Attention FP8 为 1.18×/1.16×、LPIPS 0.086/0.151，Cache-DiT 为 1.94×/1.20×、LPIPS 0.038/0.036。八卡 DGX B200 以 CFG 分组和 Ulysses 并行把 Base 中位 T2I 从 14.90 降到 3.00 秒、蒸馏版从 2.73 降到 1.08 秒，但蒸馏版约一半时间不在去噪，限制端到端收益；CUDA Graphs 则在较小分辨率降低内核启动开销。作者也提醒提高 Sol-Attention 的 τ 会损质量却几乎不增速度，RTX PRO 6000 Blackwell 上同类组合为 1.73–3.25×。

**「启示」** 作者的结论是：把 NVFP4、融合内核、量化/稀疏注意力、步缓存、并行与 CUDA Graphs 分层叠加，能在 Blackwell 上把 FLUX 3 推理延迟降低数倍；但收益依赖分辨率、模型变体和流水线阶段，且必须以 LPIPS 等指标显式权衡画质，优化并非无条件免费。

**标签**: `#diffusion-model-inference`, `#tensorrt-llm`, `#quantization`, `#attention-optimization`, `#gpu-performance`

---

<a id="item-tech-blog-3"></a>
### [Reshard 集合通信加速强化学习权重重载](https://developer.nvidia.com/blog/accelerating-reinforcement-learning-weight-refit-with-the-reshard-collective/) ⭐️ 7.0/10

rss · NVIDIA NCCL Technical Blog · 11月6日 18:03

**「背景」** 在分离式强化学习后训练中，训练与推理运行在不同 GPU 上，推理侧需在每个训练步后接收最新策略权重，这一过程称为 refit。由于两侧采用不同的数据、张量、专家和流水线并行布局，且每次要搬运约等于整个模型大小的权重，现有先 all-gather 再 broadcast 的做法会把通信量放大到约两倍模型大小。

**「方案」** NVIDIA 作者提出把 refit 重新表述为 DTensor 到 DTensor 的 reshard：只需给出源、目标布局，系统就按分片交集只传输目标 GPU 真正需要的区域，而不必先还原完整张量。其开源参考实现 NCCL M2N Reshard 进一步按 NVLink 域组织传输：同一份源分片跨网络只发一次，再在域内用 NVLink 均衡交换补齐副本，并把网络传输与本地复制流水化。为兼顾工程覆盖，NeMo RL 采用混合路径——占参数约 95% 的前馈投影权重走 reshard，QKV、mamba 等小权重仍走传统 gather-broadcast。作者在 DGX H100 与 GB200 上报告相对传统方案 2.7x–5.7x 的加速，例如 DeepSeek v3 671B 从 14.9 秒降至 2.6 秒；2.4T BF16 模型微基准为 4.3 秒。这些数据来自厂商自测，原帖未深入交代基线调优、边界条件与更广泛权衡。

**「启示」** 作者的核心论点是：把权重重载抽象成布局感知的集合通信，可以消除 gather-broadcast 的冗余流量，使万亿参数模型的频繁 refit 更可行；混合路径则表明，性能优化仍需与功能覆盖折中。

**标签**: `#reinforcement learning`, `#weight refit`, `#DTensor`, `#NCCL collectives`, `#distributed training`

---