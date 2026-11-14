---
layout: default
title: "Horizon Summary: 2026-11-14 (ZH)"
date: 2026-11-14
lang: zh
---

> 从 39 条内容中筛选出 9 条重要资讯。

---

**科技新闻**
1. [XRAID 首发：面向分区式存储的 XFS 集成 RAID](#item-tech-news-1) ⭐️ 8.0/10
2. [Haskell 生态技术愿景引发讨论](#item-tech-news-2) ⭐️ 7.0/10
3. [微软 Outlook、Teams 全球宕机超 12 小时](#item-tech-news-3) ⭐️ 7.0/10
4. [DeepSeek 据称开放应用 API 全家桶并开源聊天 Demo](#item-tech-news-4) ⭐️ 7.0/10
5. [OpenAI 推出 ChatGPT Wallet，Pro 用户可由智能体代付](#item-tech-news-5) ⭐️ 7.0/10

**科技博客**
1. [GPU 加速黑洞干涉测量：cuPhoton.xBeam 解析](#item-tech-blog-1) ⭐️ 7.0/10
2. [在 Jetson AGX Orin 上用 cuDLA 从 Python 运行 DLA 推理](#item-tech-blog-2) ⭐️ 6.0/10
3. [双 DGX Station 上的 GLM-5.3 vLLM 部署](#item-tech-blog-3) ⭐️ 6.0/10

**财经新闻**
1. [CNBC：卢特尼克因坎托与英伟达关系受审视](#item-finance-news-1) ⭐️ 8.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [XRAID 首发：面向分区式存储的 XFS 集成 RAID](https://lwn.net/Articles/1107473/) ⭐️ 8.0/10

Christoph Hellwig 宣布 XRAID 首次公开发布，这是一种集成到 XFS 的去聚集式奇偶校验 RAID，主要面向 SMR 硬盘等分区式存储设备，同时也支持传统硬盘和 SSD。当前实现支持 0 到 2 个奇偶校验盘；对更多奇偶校验的支持已列入计划，代码也为此做了准备，但此前用 SnapRAID 奇偶校验库做的实验版本并未包含在这次发布中。Hellwig 表示项目已开发一年半，但远未达到提交上游的条件，现在希望获得更广泛的反馈和测试；xfsprogs 分支包含 mkfs 支持以及新的 xraid 管理、检查工具，Zonar 也已扩展以显示逻辑区到物理区的映射。Hellwig 还称写入速度最高可达 mdraid 的 20 倍，但这是开发者说法，且项目并未以优化 SSD 性能为重点，尚待独立验证。

rss · LWN.net · 11月13日 14:39

**「背景」** 像 SMR 硬盘这类分区存储（zoned）设备要求写入在分区内基本顺序进行，这让传统的条带化校验 RAID 布局难以直接套用；而 Linux 长期使用的软件 RAID 实现 mdraid 并不感知分区，校验 RAID 本身还存在写入漏洞等数据完整性隐患。XRAID 正是为同时解决这两点而设计：在分区设备上实现校验 RAID，并提供不带固有完整性问题的快速实现，同时与已支持分区设备的 XFS 集成，也能用于普通硬盘和 SSD。

**「影响」** 对希望评估 XRAID 的开发者而言，当前入口是 xfsprogs 的 XRAID 分支：mkfs 可创建文件系统，xraid 工具用于管理设备和检查文件系统；但代码尚未提交上游且只支持 0 到 2 个奇偶校验盘，应视为实验性功能而非生产依赖。

**标签**: `#XFS`, `#RAID`, `#Linux kernel`, `#zoned storage`, `#SMR`

---

<a id="item-tech-news-2"></a>
### [Haskell 生态技术愿景引发讨论](https://discourse.haskell.org/t/a-technical-vision-for-the-haskell-ecosystem/15078) ⭐️ 7.0/10

Haskell 社区在 Discourse 上发布了一份面向生态系统的技术愿景，并在 Hacker News 上引发讨论；但源帖正文未提供，因此愿景中的具体提案、目标版本或实施时间表无法核实。现有信息只能确认这是一份社区讨论性质的愿景，而非已经交付的编译器、工具链或库更新。对 Haskell 用户和工具链维护者而言，当前可确认的是讨论方向；Hacker News 条目显示 171 分和 78 条评论，讨论主要围绕采用情况、跨平台能力和开发体验展开。

hackernews · cosmic\_quanta · 11月13日 14:43 · [社区讨论](https://news.ycombinator.com/item?id=50484235)

**「背景」** 这份技术愿景由 Haskell Foundation 新组建的技术领导委员会发布，该委员会表示已完成筹备、正式运作，并将主动提出其认为需要资金与执行力的倡议和提案。据第三方摘要，文件围绕更快的迭代速度、调试与入门体验、生态安全、长期稳定性等方向提出目标，但性质上是一组愿景与征求提案、资金的邀请，而非详细的执行计划。

**「社区讨论」** 评论者从不同角度指出生态短板：有人主张 Haskell 的简洁语法和严格类型系统适合 AI 生成代码，也有人认为它缺少类似 JavaScript 那样覆盖桌面、移动和 Web 的通用性；另有开发者强调增量编译比单纯关注编译时间更关键。还有评论者分享了为 Haskell VR 合成器加入运行时单步调试的实践，认为交互式调试在 Haskell 生态中被低估。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://discourse.haskell.org/t/a-technical-vision-for-the-haskell-ecosystem/15078">A technical vision for the Haskell ecosystem</a></li>
<li><a href="https://daily.dev/posts/a-technical-vision-for-the-haskell-ecosystem-vy0hywfpm">A technical vision for the Haskell ecosystem - daily.dev</a></li>
<li><a href="https://proomt.com/item/a-technical-vision-for-the-haskell-ecosystem-8c342688-a8c3-4b1e-9690-145967b4e1d8">A technical vision for the Haskell ecosystem · proomt</a></li>

</ul>
</details>

**标签**: `#Haskell`, `#programming languages`, `#open source`, `#language ecosystem`, `#developer tooling`

---

<a id="item-tech-news-3"></a>
### [微软 Outlook、Teams 全球宕机超 12 小时](https://www.reuters.com/technology/microsoft-365-outlook-down-thousands-us-users-downdetector-shows-2026-11-12/) ⭐️ 7.0/10

11 月 13 日，微软 Outlook、Teams 和 Copilot 的全球宕机持续超过 12 小时，扰乱企业、政府机构和金融机构的通信；微软称故障源于服务器问题，未发现恶意活动，并表示已扩大修复范围、出现回稳迹象。澳大利亚、日本和美国部分政府机构受到影响，Euronext 的邮件受阻，台湾有金融机构改用传真确认交易。此次中断是微软 365 服务今年第二次中断。

telegram · zaihuapd · 11月13日 12:21

**「背景」** 微软 365 把 Outlook 邮件、Teams 聊天与会议、Copilot 等托管在同一套云端服务上，企业客户没有可自行保底的本地部署版本，因此服务端出现故障时，多个产品和多个地区会同时受影响。据源报道，这已是微软 365 服务今年第二次中断，但源未提供上一次中断的时间、持续时长与原因。

**「实际影响」** 对依赖 Microsoft 365 的机构而言，此次故障的直接后果是邮件与协作通信中断，部分交易确认等关键流程被迫改用传真等替代渠道；在微软仅报告回稳迹象、未宣布完全恢复的情况下，受影响组织仍需依赖替代通信方式。

**标签**: `#Microsoft 365 outage`, `#Outlook`, `#Teams`, `#cloud service reliability`, `#global outage`

---

<a id="item-tech-news-4"></a>
### [DeepSeek 据称开放应用 API 全家桶并开源聊天 Demo](https://mp.weixin.qq.com/s/78KBHc4-4N5b2vfL9SkutQ) ⭐️ 7.0/10

据微信公众号“科技圈”投稿，DeepSeek 据称已开放“全家桶”应用 API：开发者在原有 API 中开启相应参数，即可使用深度思考搜索、文件输入、链接阅读和语音等对话能力，工具调用与上下文拼接由服务端完成。帖子称 V4.1-Flash 模型已在三个接口中支持这些能力，Search、Fetch、OCR、ASR、TTS 也可单独调用。DeepSeek 还开源了可导入历史对话的前端 chat-demo，并给出 GitHub Pages 体验地址；上述消息来自简短聚合帖，尚未见独立验证。

telegram · zaihuapd · 11月13日 14:27

**「背景」** Horizon 9 月 11 日的日报曾报道，DeepSeek 发布 V4.1 Flash，描述其为 552B 参数、采用 Causal-Encoder-Decoder 结构的模型，输入与输出激活参数分别为 8B 和 16B，原生支持多模态视觉理解，并以 deepseek-flash 的模型名上线 API；不过该摘要来自聚合式帖子，发布与计费安排当时仍待官方确认。10 月 18 日的日报又记录了 DeepSeek-V4.1-Flash-1017 小版本更新，社区称其在推理、编码与智能体任务上有所改进，但提交材料未附基准方法，相关数字无法独立核验。此次变化发生在同一模型线之上：据 DeepSeek API 文档，V4.1-Flash 在 Messages、Responses 与 Chat Completions 三个接口获得搜索、抓取、OCR、ASR、TTS 及服务端工具调用能力，而此前的报道只涉及模型本身与 API 路由、定价。

**「影响」** 开发者可直接调用搜索、抓取、OCR 和语音等单项能力，也可基于开源的 chat-demo 本地部署类似网页端的对话界面；实际可用范围和接口限制仍需以 DeepSeek 官方文档为准。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://mp.weixin.qq.com/s/qg0NU3NNUbp1co2PdkAPAg">2026-09-11 — DeepSeek V4.1 Flash 发布：552B 参数与 API 路由调整</a></li>
<li><a href="https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017">2026-10-18 — DeepSeek-V4.1-Flash-1017 发布，社区讨论编码基准与速度</a></li>
<li><a href="https://api-docs.deepseek.com/news/news261113/">The full DeepSeek App experience, now via API | DeepSeek API Docs</a></li>

</ul>
</details>

**标签**: `#DeepSeek`, `#AI APIs`, `#multimodal AI`, `#open-source tools`, `#developer platform`

---

<a id="item-tech-news-5"></a>
### [OpenAI 推出 ChatGPT Wallet，Pro 用户可由智能体代付](https://openai.com/index/introducing-chatgpt-wallet/) ⭐️ 7.0/10

OpenAI 发布 ChatGPT Wallet，面向美国 18 岁以上的 ChatGPT Pro 订阅用户开放，且必须使用美国发行的银行卡。用户可让智能体代为购买，但每笔交易都要由用户核对商品和金额，并通过 Face ID 或指纹确认。支付时由美国运通、万事达和 Visa 的网络下发替代真实卡号的支付令牌，智能体不接触用户的真实卡号。OpenAI 表示，该功能自发布当日起通过 dots 开放。

telegram · zaihuapd · 11月13日 15:43

**「背景」** 代理支付要落地，需要同时解决“代理可发起”和“用户可控制”两个问题：支付网络用一次性或设备专属令牌替代真实卡号，用户则在每笔交易上确认。Horizon 9 月 29 日的日报曾提到面向 AI 代理的 HTTP 402 支付协议 MPP，说明代理付款此前已作为协议层议题出现；此次 ChatGPT Wallet 的不同点在于，OpenAI 通过美国运通、万事达和 Visa 的支付令牌及逐笔生物识别确认，把这一能力开放给美国 ChatGPT Pro 订阅用户。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://blog.bytebytego.com/p/ai-agents-can-think-now-they-can">2026-09-29 — MPP：AI 代理的 HTTP 402 支付协议</a></li>

</ul>
</details>

**标签**: `#OpenAI`, `#AI agents`, `#payments`, `#digital wallet`, `#security`

---

## 科技博客

<a id="item-tech-blog-1"></a>
### [GPU 加速黑洞干涉测量：cuPhoton.xBeam 解析](https://developer.nvidia.com/blog/run-gpu-powered-black-hole-interferometry-with-nvidia-cuphoton/) ⭐️ 7.0/10

rss · NVIDIA CUDA Technical Blog · 11月13日 21:17

**「背景」** 拍摄黑洞需要把全球射电望远镜连成 VLBI 阵列：EHT 用 13 个站点同步记录毫米波电压，M87\* 的环仅约 42 微角秒，原始数据达 PB 级，台站两两相关处理成为瓶颈。

**「方案」** NVIDIA 作者介绍的 cuPhoton v0.1.3 中的 xBeam 是 GPU FX 相关器：它先把 VDIF 帧按时间、线程和物理位置建成 .vdix 旁路索引，读取时直接定位而不重写原始记录；相关时按作业给定的延迟模型做整数样本对齐和条纹旋转，FFT 分频后再补频率相关的分数延迟相位，随后对台站与极化对交叉相乘、按积分时间累加，输出 DiFX SWIN 或 xbeam-v1 可见度。相位校正、FFT 和交叉相乘都在 GPU 上执行，数据可走锁页主机内存或 GPUDirect Storage 的 cuFile 路径；多 GPU 按时间切片，单节点用 --devices，多节点用 --shard-count/--shard-index 并以 merge-shards 合并。作者报告在 Vera Rubin NVL72 的 64 张 GPU 上，10 TB 数据端到端处理 70 秒，约为 x86 CPU 基线 31,992 秒的 460 倍，读取带宽从 4 GPU 的 20 GB/s 增至 64 GPU 的 170 GB/s。作者同时限定：延迟来自作业文件而非由台站位置计算，xBeam 不追踪黑洞附近光路，缺失样本不会被恢复，缓冲策略只影响后续样本的时间与权重分配，可见度之后的校准和成像不在教程范围内。

**「启示」** 作者的核心论点是，把 FX 相关拆成可索引、可并行、可合并的 GPU 流水线，能把海量干涉数据的相关处理从数小时压到约一分钟。需要记住，460 倍是 NVIDIA 自报的端到端基准，延迟模型、校准和成像仍依赖外部工具。

**标签**: `#GPU correlator`, `#VLBI`, `#Event Horizon Telescope`, `#GPUDirect Storage`, `#scientific computing`

---

<a id="item-tech-blog-2"></a>
### [在 Jetson AGX Orin 上用 cuDLA 从 Python 运行 DLA 推理](https://developer.nvidia.com/blog/run-native-dla-inference-in-python-on-nvidia-jetson-agx-orin-using-cudla/) ⭐️ 6.0/10

rss · NVIDIA CUDA Technical Blog · 11月13日 18:57

**「背景」** 边缘 AI 要在有限算力和功耗下并行运行多个网络；Jetson AGX Orin 的 DLA 可把受支持算子从 GPU 卸载，但运行时管理此前多依赖 C++。作者探讨能否用 Python 完成原生 DLA 推理的完整生命周期。

**「方案」** 答案是 cuda.bindings.cudla：cuda-bindings 13.3.0 引入的薄 Cython 封装，把 cuDLA C++ API 暴露给 Python，并以 CUDA\_DLA 混合模式让 DLA 任务通过 CUDA 流与 GPU 工作排序；运行时只需 JetPack 自带的 libcudla.so，TensorRT 只在编译 loadable 时需要。示例用 trtexec 的 --useDLACore=0、--buildDLAStandalone 和 CHW16 I/O 生成独立 loadable；TensorRT 11 从模型张量类型推导精度，已不支持 --fp16/--int8，DLA 不兼容层还常需在 ONNX 图中裁剪。Python 侧创建设备、按字节加载 loadable，再查询输入输出描述符，用其中的 size\_、shape、name、stride 和格式驱动分配与预处理，因此无需硬编码张量尺寸；随后分配并注册 GPU 缓冲区，构造 Task 提交到流，同步后拷回 NumPy，最后逐一注销和销毁资源。cuDLA 失败会抛出 CudlaError，作者建议用 try/finally 清理，因为设备句柄不会随垃圾回收释放；该版本也不支持需要 NvSci 的 standalone 模式，而整条路径对网络结构基本无关，只有张量名、尺寸和前后处理随模型变化。

**「启示」** 作者的核心结论是，cuda.bindings.cudla 让 Python 能完成从加载 loadable、注册缓冲区到提交任务和清理的完整 DLA 推理生命周期，同时保留 DLA 与 GPU 共用 CUDA 流的混合执行方式。这降低了在 Jetson 边缘应用中把受支持层卸载到 DLA 的集成门槛，但效率收益缺乏实测验证。

**标签**: `#NVIDIA Jetson`, `#cuDLA`, `#Python bindings`, `#Edge inference`, `#TensorRT`

---

<a id="item-tech-blog-3"></a>
### [双 DGX Station 上的 GLM-5.3 vLLM 部署](https://developer.nvidia.com/blog/when-one-gpu-isnt-enough-serving-glm-5-3-across-two-nvidia-dgx-stations-with-vllm/) ⭐️ 6.0/10

rss · NVIDIA Inference Performance Blog · 11月13日 17:00

**「背景」** GLM-5.3 NVFP4 是 753B 参数的 MoE 模型，每 token 激活 40B，但 464 GB 权重超过单块 GB300 的 252 GB HBM3e，本地部署必须跨机。

**「方案」** NVIDIA 教程把两台经 ConnectX-8 RDMA 互联的 DGX Station 用 vLLM 张量并行 TP=2 组成一个服务：权重和计算分到两块 GB300，Station A 提供单个 OpenAI 兼容 API，两机共同处理每个请求。两机各存一份约 464 GB 检查点并固定相同镜像；启动时需将 NCCL 绑定到选定 RoCE rail，配置 GID、HCA、超时，并用 98304 token 上下文、0.93 显存利用率、MTP 四 token 投机解码、FP8 KV 缓存和前缀缓存平衡资源。启动后每 GPU 约承载 218 GiB 权重，NCCL 日志须确认走 GPU Direct RDMA 而非 TCP 回退。SPEED-Bench Coding 测试显示，总吞吐在并发 16 时达 607.8 tok/s，并发 32 反降至 385.0 tok/s，平均延迟 453.5 s，单用户吞吐从 115.3 降至 13.0 tok/s；这给出了调优基线，但流程绑定特定 NVIDIA 栈，缺少独立比较。

**「启示」** 作者的结论是：超大 MoE 模型已能跨两节点以张量并行提供可用的本地端点，真正需要按负载调的是并发点，而非能否启动。

**标签**: `#vLLM`, `#tensor parallelism`, `#multi-node inference`, `#NCCL/RDMA`, `#LLM serving`

---

## 财经新闻

<a id="item-finance-news-1"></a>
### [CNBC：卢特尼克因坎托与英伟达关系受审视](https://www.cnbc.com/2026/11/13/howard-lutnick-nvidia-jensen-huang-china-cantor-fitzgerald.html) ⭐️ 8.0/10

据 CNBC 报道，美国商务部长霍华德·卢特尼克因前公司坎托·菲茨杰拉德与英伟达的深厚关系受到审视，申报文件显示坎托持有的英伟达股票数量在 2025 年 9 月至 2026 年 3 月间下降 49%。Axios 报道称，卢特尼克曾收到涉及英伟达 CEO 黄仁勋与一名疑似中国间谍关系的情报警告，并多次抵制对涉嫌向中国走私英伟达芯片的公司采取行动，这些报道内容尚未得到证实；黄仁勋已于周四辞职。

rss · CNBC Finance · 11月13日 23:42

**「背景」** 英伟达 CEO 黄仁勋于 2026 年 11 月 12 日辞职，此前有报道称他与一名被怀疑为中国间谍的女性存在婚外情，公司首席财务官 Colette Kress 暂时接任；他和商务部长卢特尼克均被要求下月到参议院委员会作证。卢特尼克在 2025 年 2 月出任商务部长前执掌华尔街投行 Cantor Fitzgerald，该公司现由其子布兰登和凯尔领导。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.nytimes.com/live/2026/11/12/business/nvidia-jensen-huang-resigns">Nvidia Updates: Huang ’s Resignation Reverberates Through...</a></li>
<li><a href="https://www.theguardian.com/technology/2026/nov/12/nvidia-ceo-jensen-huang-resigns">Jensen Huang resigns as Nvidia CEO after alleged... | The Guardian</a></li>

</ul>
</details>

**标签**: `#Nvidia`, `#Howard Lutnick`, `#China export controls`, `#Cantor Fitzgerald`, `#conflict of interest`

---