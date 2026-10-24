---
layout: default
title: "Horizon Summary: 2026-10-24 (ZH)"
date: 2026-10-24
lang: zh
---

> 从 11 条内容中筛选出 5 条重要资讯。

---

**科技新闻**
1. [Kimi K3.1 Pro 上线 API，权重定于 11 月 4 日前开放](#item-tech-news-1) ⭐️ 8.0/10
2. [Block 的 Dessa 全双工语音模型宣称可本地运行](#item-tech-news-2) ⭐️ 7.0/10
3. [iPhone 攻破演示引来越狱、锁定模式与安全研究访问权争论](#item-tech-news-3) ⭐️ 7.0/10
4. [LPC 2026：Linux 内核尝试缩小 16KB 线程栈](#item-tech-news-4) ⭐️ 7.0/10

**科技博客**
1. [Trainium3 训练栈体验：原生 PyTorch 与 Neuron Explorer](#item-tech-blog-1) ⭐️ 6.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [Kimi K3.1 Pro 上线 API，权重定于 11 月 4 日前开放](https://simonwillison.net/2026/Oct/23/kimi-k31-pro/) ⭐️ 8.0/10

Moonshot 已在 Kimi API 上线 Kimi K3.1 Pro，但模型权重尚未开放，公司承诺 2026 年 11 月 4 日前发布完整权重。API 定价为每百万输入 token 2 美元、每百万输出 token 10 美元，与 GPT-6.1 Sol 相同，为 Claude Opus 5.5 的一半；另有一个速度快 2–3 倍的 Highspeed 版本，价格翻倍，但输入 token 缓存命中的价格不变。Moonshot 自行发布的基准显示其与 Opus 5.5、GPT-6 Astra 大致相当；第三方 Artificial Analysis 给出 55 分，低于 Opus 5.5 的 58 分，高于 Claude Fable 5.1、GPT-6 Astra 和 Gemini 4 Argon 的 53 分。作者称，这是首个即将开放权重的模型在对前沿模型的评测中达到如此高的分数。

rss · Simon Willison · 10月23日 19:40

**「此前脉络」** Kimi K3.1 Pro 是 K3 系列的迭代版本：8 月 9 日的日报曾记录，SGLang v0.5.17 为 Kimi K3 提供 day-0 支持，当时披露的规格包括 2.8T 总参数的 LatentMoE 架构与 1M token 上下文。Moonshot 此前已有先开源、后迭代的做法，例如 6 月 13 日的日报报道其开源了编码模型 K2.7-Code。因此，本次「11 月 4 日前发布完整权重」的承诺延续了这条开放权重路线，但 K3.1 Pro 目前只能通过 Kimi API 调用。

**「影响」** 对需要通过 API 选型的开发者，K3.1 Pro 现已可用，并可按作者演示的方式通过 OpenAI 兼容端点接入，按每百万 token 2/10 美元计费；若需要低延迟，Highspeed 版本的成本翻倍，缓存输入除外。由于权重只是承诺在 11 月 4 日前开放，在此之前无法自托管，需等待实际发布后再评估本地部署。

**「社区讨论」** 有评论称 Kimi 的回答比美国模型更直白、更好争辩；另有用户报告，其 99 美元/月订阅在单次会话进行到 47 分钟时就触发了 5 小时配额，提醒订阅额度可能与预期不符。一位评论者分享的 Pac-Man 测试结果显示，K3.1 Pro 与 Claude Sonnet 5.5 同为 93 分，但成本 0.68 美元、耗时 11 分钟，低于 Sonnet 5.5 的 1.61 美元和 14 分钟。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://mp.weixin.qq.com/s/NBw1VAA9MjpKv-Rirq9qDg">2026-06-13 — Kimi open-sources coding model K2.7-Code with benchmark gains</a></li>
<li><a href="https://github.com/sgl-project/sglang/releases/tag/v0.5.17">2026-08-09 — SGLang v0.5.17 发布：支持 Kimi K3 与 MiniMax-H3</a></li>

</ul>
</details>

**标签**: `#large language models`, `#model release`, `#Moonshot AI`, `#AI benchmarks`, `#API pricing`

---

<a id="item-tech-news-2"></a>
### [Block 的 Dessa 全双工语音模型宣称可本地运行](https://block.xyz/dessa) ⭐️ 7.0/10

Block 宣布推出 Dessa 全双工语音模型，其特点是能同时听说，而不是传统的轮流发言。据评论引述的帖子内容，Dessa 具备低延迟本地推理能力，可在 MacBook Pro M4 Max 或更高配置上运行，并仅用一台 NVIDIA GB200 NVL72 完成训练。上述性能、硬件门槛和训练效率均来自公布方说法；目前公开材料以宣传为主，缺少可独立验证的技术细节和复现结果。

hackernews · dsr12 · 10月23日 19:09 · [社区讨论](https://news.ycombinator.com/item?id=50213925)

**「背景」** 全双工语音指模型可以边听边说，不必等对方说完再轮流发言，并能处理打断和附和。Horizon 2026 年 9 月 12 日的日报曾报道，OpenAI 将可同时听说的 GPT‑Live‑1 上线 API，并称其在 Full Duplex Bench 上较 GPT‑Realtime‑2.1 提升 30 个百分点，该数据出自 OpenAI 自身说法；2026 年 8 月 6 日的日报则报道，字节跳动的音视频全双工模型 SeedRealtime 已在豆包 App 全量上线。

**「影响」** 对语音代理开发者而言，最直接的可操作结论是先验证硬件门槛：帖子把本地运行限定在 M4 Max 或更高配置，训练则称只需一台 GB200 NVL72；在独立复现前，不应把低延迟和表现力当作已交付的部署保证。

**「社区讨论」** Hacker News 评论对演示效果看法不一：有人对低延迟、表现力和本地运行所需硬件感到惊讶，也有人认为同时说话、频繁打断的演示显得人工化，并担心这类语音技术的主要用途会变成冒充真人。一位评论者表示，会用只有熟人知道的共享记忆问题来筛查可疑来电。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://openai.com/index/introducing-gpt-live-1-in-the-api/">2026-09-12 — OpenAI API 上线 GPT-Live-1 实时语音模型</a></li>
<li><a href="https://seed.bytedance.com/zh/blog/seedrealtime-%E9%9F%B3%E8%A7%86%E9%A2%91%E5%85%A8%E5%8F%8C%E5%B7%A5%E5%A4%A7%E6%A8%A1%E5%9E%8B%E5%8F%91%E5%B8%83-%E8%B5%B0%E5%90%91%E5%85%A8%E6%A8%A1%E6%80%81%E8%87%AA%E7%84%B6%E4%BA%A4%E4%BA%92">2026-08-06 — 豆包上线原生音视频全双工模型 SeedRealtime</a></li>

</ul>
</details>

**标签**: `#full-duplex-speech`, `#voice-ai`, `#local-inference`, `#model-efficiency`

---

<a id="item-tech-news-3"></a>
### [iPhone 攻破演示引来越狱、锁定模式与安全研究访问权争论](https://blog.calif.io/p/iphone) ⭐️ 7.0/10

博客文章《Today, we hacked what we&\#x27;d set out to hack: the iPhone》（blog.calif.io，10 月 23 日）宣称完成了一次针对 iPhone 的攻破演示，并在 Hacker News 上引发大量讨论。所提供材料只有标题和评论，没有披露具体的漏洞链、受影响的 iOS 版本、利用条件，也没有说明是否真正获得 root 权限，因此该演示的技术细节和可复现性目前无法核实。评论区把焦点放在三件事上：越狱是否会导致 Apple 封锁 iCloud、iMessage 等云服务，Lockdown Mode 对这类攻击是否实际有效，以及前沿实验室只向少数合作方开放“受信任网络访问”是否让外部研究者难以参与。

hackernews · pavel\_lishin · 10月23日 16:21 · [社区讨论](https://news.ycombinator.com/item?id=50211474)

**「背景」** Calif 在巴黎 Hexacon 安全会议上公布的是四组 iPhone 攻击演示，而非立即公开的完整利用代码；博文点名了 Signal 一键利用和 iMessage 攻击面，并称细节将“在适当时候”发布。此前同一账号还发布过 iPhone Duo 越狱视频，说明这次演示延续了其围绕 iPhone 越狱与漏洞利用的公开展示路线。

**「实际影响」** 对普通 iPhone 用户来说，一个直接而未决的问题是这个演示所用的手法在开启 Lockdown Mode 后是否仍然奏效：有评论者明确提出了这一点，但材料中没有给出任何验证结果，所以不能据此判断该模式的现实防护效果。对安全研究者而言，讨论指向准入门槛问题（某评论者称之为“护城河而非保障”），即前沿模型的红队访问权限只向特定机构开放，外部人员难以复现同类研究。

**「社区讨论」** 有评论者（reacharavindh）认为，如今生态锁定使得越狱代价过高：即便不升级系统，Apple 也能检测到越狱并切断 iCloud、iMessage 等服务，设备会退化成“高级 iPod touch”。另有人（slowin）表示希望获得手机 root 权限，并询问这样做是否会阻止 Apple 推送更新或移除该改动；jeroenhd 则追问 Lockdown Mode 是否真能挡住这些漏洞利用，这些疑问在材料中均未得到回答。jinseokim 从研究者角度批评前沿实验室的“受信任网络访问”计划只惠及圈内公司，使圈外安全研究者无法参与。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://blog.calif.io/p/iphone">iPhone - Calif Newsletter</a></li>
<li><a href="https://news.ycombinator.com/item?id=50211474">&quot; Today , we hacked what we &#x27; d set out to hack : the iPhone .&quot;</a></li>

</ul>
</details>

**标签**: `#iPhone security`, `#jailbreaking`, `#exploit research`, `#Lockdown Mode`, `#AI security access`

---

<a id="item-tech-news-4"></a>
### [LPC 2026：Linux 内核尝试缩小 16KB 线程栈](https://lwn.net/Articles/1100271/) ⭐️ 7.0/10

在 2026 年 Linux Plumbers Conference 的内存管理微会议上，Will Deacon 讨论了 64 位 Arm 和 x86 上每个线程固定占用 16KB 不可分页内存的内核栈；Android 空闲设备就可能有 5,000 个线程，云端大规模线程也会放大这项开销。用 8KB 栈构建的内核通过了大部分测试，但在内存压力测试中失败，并在涉及直接回收（direct reclaim）的路径上崩溃；4KB 栈则无法启动。会上提到的补丁系列允许通过内核命令行设置栈大小，目前可运行 12KB 栈；另有专用异常栈和把直接回收移到工作线程的方案，目标是为 8KB 铺路。默认配置仍是 16KB，这些属于会上介绍的补丁方向。

rss · LWN.net · 10月23日 14:59

**「背景」** Arm64 在 3.7 内核（2012 年）合并时使用 8KB 栈，3.11（2013 年）因 SpecWeb 基准测试失败增至 16KB；x86 在 3.16 跟进，理由包括 Arm64 已这样做，以及部分 GCC 版本会生成更大的栈帧。4.14 引入虚拟映射内核栈后，又要求内核栈按 32KB 对齐，使缩小栈更复杂。

**「影响」** 若 8KB 栈最终进入主线，Android 和云厂商每个线程的内核栈内存可减半；但 8KB 内核目前在内存压力下仍会崩溃，短期内可先尝试 12KB 等过渡方案，而且厂商现有的树外动态栈实现难以在通用内核镜像（GKI）上通过 vendor hooks 落地。

**标签**: `#Linux kernel`, `#kernel stacks`, `#memory management`, `#Linux Plumbers Conference`, `#Arm/x86`

---

## 科技博客

<a id="item-tech-blog-1"></a>
### [Trainium3 训练栈体验：原生 PyTorch 与 Neuron Explorer](https://newsletter.semianalysis.com/p/amazons-trainium-takes-a-strike-at) ⭐️ 6.0/10

rss · SemiAnalysis · 10月23日 19:06

**「背景」** Trainium 已在推理侧得到验证——Anthropic 在 Trainium2/3 上跑生产推理和 RL rollout——但研究训练要覆盖快速迭代的架构、消融实验和更广的 API 面，旧栈难以胜任。

**「方案」** 作者认为 AWS 的关键转向是 TorchNeuron：放弃 PyTorch/XLA 的惰性图和 xm.step\(\)，改为 eager、torch.compile 与标准 API 的原生 PyTorch 体验，并挖来 Google 原生 Torch on TPU 负责人。SemiAnalysis 试用 Trainium3 数周，称方向很好但仍有 bug、远不及 CUDA 成熟；AWS 用最多 8 万物理核做自动化质控，并靠 agentic coding 加速修复。文章把训练视为通用性问题：数千算子都要反向传播，还要兼容偶然出现的高精度算子。因此 AWS 用 10 万+ Hugging Face 模型覆盖不同 normalization、MLP、MoE 与 attention 布局，除崩溃外还测性能、CPU fallback、graph break，并与 CPU/Nvidia 基线比对张量数值和 loss 曲线；作者强调，MFU 再高若数值出错也无意义。剖析器上，作者称 Neuron Explorer 优于 Nvidia/AMD 工具，并展示其细粒度剖析；Nsight Compute 偏聚合指标，QuACK 的 intra-kernel 剖析最接近但仍需定制 Perfetto 集成。但摘录中的这些优势多为体验性断言，关键演示和细节在付费墙后。

**「启示」** 作者的核心判断是，Trainium 正从“推理可用”转向“能承载研究训练”，关键不在峰值效率，而在原生 PyTorch 体验、训练通用性与数值正确性。方向已获其认可，但离 CUDA 级成熟仍有距离，相关优势也尚待更完整证据。

**标签**: `#AWS Trainium`, `#PyTorch`, `#ML training`, `#profiling`, `#hardware accelerators`

---