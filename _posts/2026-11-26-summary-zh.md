---
layout: default
title: "Horizon Summary: 2026-11-26 (ZH)"
date: 2026-11-26
lang: zh
---

> 从 35 条内容中筛选出 10 条重要资讯。

---

**科技新闻**
1. [1Password 发布 2026 年 11 月安全事件说明](#item-tech-news-1) ⭐️ 8.0/10
2. [Google 发布 Cogentic 整数分解与离散对数论文](#item-tech-news-2) ⭐️ 8.0/10
3. [Anthropic 相关 GRH 的 Lean 验证出现缩短版](#item-tech-news-3) ⭐️ 8.0/10
4. [Minecraft Java 版曝高危 RCE，1.20.5 起受影响](#item-tech-news-4) ⭐️ 8.0/10
5. [Aaronson 称 AI 加速数学进展，社区质疑证明验证](#item-tech-news-5) ⭐️ 7.0/10
6. [腾讯开源 Hy4 flash GGUF 量化权重，最小版可运行于 64GB Mac mini](#item-tech-news-6) ⭐️ 7.0/10

**科技博客**
1. [简单旋转迁移大模型事实回忆表征](#item-tech-blog-1) ⭐️ 9.0/10
2. [NVFP4 注意力寄存器回收优化](#item-tech-blog-2) ⭐️ 8.0/10

**财经新闻**
1. [美商务部被曝施压英特尔交出 10%股份](#item-finance-news-1) ⭐️ 9.0/10
2. [美国拟依据 301 条款对 14 个贸易伙伴加征国别关税](#item-finance-news-2) ⭐️ 8.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [1Password 发布 2026 年 11 月安全事件说明](https://1password.com/blog/update-on-nov-2026-security-incident) ⭐️ 8.0/10

1Password 官网发布了针对 2026 年 11 月安全事件的更新说明；据现有帖文摘要，事件涉及恶意代码被推送到其后端服务。当前材料没有提供受影响用户数量、具体后端系统、代码进入生产环境的路径，以及分支保护是否被绕过等关键细节。因此，对其云端服务用户而言，尚无法从现有信息判断加密保险库内容或账户数据是否受到影响，需要等待 1Password 的完整时间线和影响范围说明。

hackernews · lxhrstn · 11月25日 17:18 · [社区讨论](https://news.ycombinator.com/item?id=50644817)

**「事件起点与攻击路径」** 据 1Password 通报，调查始于 2026 年 11 月 19 日：公司发现有攻击者取得了某员工的 GitHub 企业账号访问权，并利用该账号读取源代码、向内部后端服务推送恶意代码，这些服务随后下载了与客户相关的管理类数据（TechCrunch 转述的通报称客户密码本身未受影响）。这条路径的关键前提在于代码仓库权限与部署流水线相连——攻破一名开发者的账号，就可能获得向生产环境投放代码的能力。

**「影响」** 1Password 表示客户保险库未受影响、内容仍然安全，这限定了事件对普通用户的实际影响范围。对企业技术团队而言，公告把攻击入口指向一名员工的企业 GitHub 账户，因此应复核 GitHub 账户的强认证、分支保护与部署审批，确认单个被入侵的开发账户无法把代码直接推送到生产后端。

**「社区讨论」** 评论中，tptacek 认为遭入侵的开发者设备向生产环境推送代码是 SaaS 公司的核心攻击面，并称员工越多、某台笔记本被攻陷的概率越接近 1；ctidd 则追问 1Password 是否禁用了向 main 分支推送，或分支保护规则为何未能阻止此次推送。另有长期用户表示因此继续使用仅本地保存的保险库，并要求公司更明确说明加密保险库未被下载。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://1password.com/blog/update-on-nov-2026-security-incident">Update on a security incident involving 1Password’s backend ...</a></li>
<li><a href="https://techcrunch.com/2026/11/25/1password-said-hackers-broke-into-its-internal-systems-but-customer-passwords-are-safe/">1Password said hackers broke into its internal systems, but ...</a></li>
<li><a href="https://1password.com/blog/update-on-nov-2026-security-incident">Update on a security incident involving... | 1 Password</a></li>

</ul>
</details>

**标签**: `#security incident`, `#password managers`, `#supply chain security`, `#SaaS security`, `#branch protection`

---

<a id="item-tech-news-2"></a>
### [Google 发布 Cogentic 整数分解与离散对数论文](https://github.com/google-research/google-research/tree/master/cogentic_research_papers) ⭐️ 8.0/10

Google Research 的 GitHub 仓库新增了一组名为 Cogentic 的研究论文，主题包括整数分解、离散对数及相关方向；当前条目只提供仓库链接，未给出论文正文、性能数据或可复现实验。就现有信息看，这属于研究论文的公开发布，并不能据此认定现有密码系统已被实际攻破。

hackernews · rgwohlbold · 11月25日 13:33 · [社区讨论](https://news.ycombinator.com/item?id=50642086)

**「背景」** Horizon 2026 年 10 月 3 日的日报曾报道，Google 的一篇论文提出 Cogentic：一套让多个独立证明器分头探索、再由对抗式验证组件筛选结果的多智能体证明发现系统；当时所称的专家验证结果尚无法独立核实（tool-1-1）。此次公开的是同一研究计划下的一组论文，范围扩展到整数分解和离散对数等密码学问题；社区讨论提到的 GNFS 是当前最好的通用整数分解方法之一，但它依赖未经证明的启发式假设，这也是判断这批结果实际意义的前提。

**「对现有加密部署的直接影响有限」** 对使用 RSA 或有限域离散对数的开发者来说，目前没有证据支持调整密钥长度或启动迁移。评论者 gukoff 指出，该整数分解结果建立在通用数域筛法（GNFS）之上，而 GNFS 的渐近复杂度本来就好得多；Cogentic 并未证明 GNFS 依赖的那几个启发式猜想，只是替换了其中部分环节，并为此付出了较大的复杂度代价。论文条目宣称给出无条件、零错误的经典分解算法，并附有固定特征有限域离散对数的次拟多项式时间结果，但仓库目前只发布 PDF，尚无独立复现或实现层面的性能测量；在出现可运行实现和第三方基准之前，实际风险不变，也无需据此调整现有参数。

**「社区讨论」** 评论中最具体的技术意见来自 gukoff：该整数分解工作建立在 GNFS 之上，而 GNFS 的渐近复杂度本就更优；Cogentic 没有证明 GNFS 依赖的启发式假设，只是替换相关部分并承担显著复杂度代价，因此实际密码学意义仍不清楚。另有评论将此类进展与近期 AI 数学发现联系起来，但那属于个人推测，不是论文结论。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://arxiv.org/abs/2609.40324v1">2026-10-03 — Google 提出 Cogentic：多智能体协作发现数学证明</a></li>
<li>Google releases Cogentic papers on integer factorization, discrete logs ...</li>
<li><a href="https://github.com/google-research/google-research/tree/master/cogentic_research_papers">Google Releases Cogentic Papers on Integer Factorization ...</a></li>
<li><a href="https://magica.com/news/google-cogentic-six-math-papers-factoring-proof-claim">Google Cogentic claims new factoring bound in six math papers ...</a></li>

</ul>
</details>

**标签**: `#cryptography`, `#integer-factorization`, `#discrete-logarithms`, `#research-papers`, `#google-research`

---

<a id="item-tech-news-3"></a>
### [Anthropic 相关 GRH 的 Lean 验证出现缩短版](https://github.com/lsernau/grh-lean) ⭐️ 8.0/10

GitHub 仓库 lsernau/grh-lean 提供了一个显著缩短的 GRH Lean 形式化/验证版本，与 Anthropic 的相关工作有关。评论称该版本把规模从约 1700 万行降到约 7.6 万行，并提到另一个更易读、带“已知数学/新数学”划分和文档的约 30 万行版本；这些行数只来自社区评论且口径不一致，不能视为已确认的官方数据。现有材料能确认的是该仓库和围绕 Lean 可读性、AI 辅助证明压缩的讨论，尚不能确认压缩方法或外部验证情况。

hackernews · nb-t · 11月25日 21:48 · [社区讨论](https://news.ycombinator.com/item?id=50648050)

**「背景」** Horizon 11 月 21 日的日报曾报道，Levent Alpöge 于 11 月 20 日发布一份声称证明广义黎曼猜想的 PDF，并附带约 1.3GB、约 1500 万行的 Lean 形式化；当时该声明尚未经过同行评审或独立验证，而且形式化体量本身并不能说明所形式化的命题就是广义黎曼猜想。维基百科条目称，发布次日 Lean FRO 与 Mathlib Initiative 宣布独立验证成功，但至今仍没有完整的人类可读证明说明。据仓库自述，本条目指向的 grh-lean 正是该证明的一个更短版本，其中可读版本约 30 万行。

**「影响」** 如果 Lean 用户要审阅或复用该形式化，他们的主要工作会从应付千万行级代码，转为判断缩减后的代码是否仍可人工理解和核验；评论中已有人贴出代码片段并质疑可读性，而仓库文档及“已知/新数学”划分被支持者视为缓解办法。

**「社区讨论」** 有评论者赞赏较短版本附带的文档和“已知数学/新数学”划分，认为这有助于消化形式化内容；也有人贴出具体代码片段，追问人类究竟能否读懂并核验。另有评论把这次大幅压缩归因于 Anthropic 投入的算力和内部模型，并对此前大量资源只换来小幅改进表达了讽刺。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://alpo.ge/remark.pdf">2026-11-21 — Alpöge 发布广义黎曼猜想证明声明与大型 Lean 形式化</a></li>
<li><a href="https://en.wikipedia.org/wiki/Alp%C3%B6ge&#x27;s_proof_of_the_Riemann_hypothesis">Alpöge&#x27;s proof of the Riemann hypothesis - Wikipedia</a></li>
<li><a href="https://github.com/lsernau/grh-lean">GitHub - lsernau / grh - lean : A short Lean 4 proof of the Generalized...</a></li>

</ul>
</details>

**标签**: `#Lean`, `#formal verification`, `#AI-assisted theorem proving`, `#proof compression`, `#Anthropic`

---

<a id="item-tech-news-4"></a>
### [Minecraft Java 版曝高危 RCE，1.20.5 起受影响](https://github.com/bikini/minecraft2shell) ⭐️ 8.0/10

11 月 22 日公开的 minecraft2shell 显示，Minecraft Java 版服务器资源包中的特制 TrueType 字体可触发 FreeType 2.14.3 及更早版本的原生越界写，并在 Java 版 26.3 Windows 客户端上执行任意代码。受影响版本为 1.20.5 至 1.21.10 以及 26.1 至 26.4 快照；1.20.4 及更早版本和基岩版不受影响。Mojang 目前仍使用 lwjgl-freetype 3.4.3，尚无官方补丁；社区于 11 月 24 日发布 m2sfix 1.0.0，通过 Java agent 或 mod 关闭 hinting 作为临时缓解。

telegram · zaihuapd · 11月25日 12:46

**「前置背景」** 服务器资源包（server resource pack）是多人服务器在玩家加入时推送、由客户端下载并应用的资源集合，字体文件也在其中；客户端会把 TrueType 字体交给随游戏打包的原生 FreeType 库（Mojang 目前使用 lwjgl-freetype 3.4.3）做字形栅格化，因此畸形字体触发的越界写发生在 JVM 之外的原生代码中。公开的 minecraft2shell 仓库称，其验证对象是 Mojang 签名的 Minecraft Java 26.3 Windows 客户端以及该客户端随附的 FreeType 2.14.3 x64 这一具体构建。来源未解释受影响版本下限为何定在 1.20.5，仅说明 1.20.4 及更早版本与基岩版不受影响。

**「影响与应对」** 在官方修复前，多人服务器管理员应将资源包权限设为“禁用”，或安装 m2sfix 1.0.0；投稿人还建议玩家不要添加任何资源包，因为服务器提供恶意字体资源包就可能触发代码执行。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://github.com/bikini/minecraft2shell">GitHub - bikini/ minecraft 2 shell : Minecraft to native RCE · GitHub</a></li>

</ul>
</details>

**标签**: `#security-vulnerability`, `#Minecraft`, `#RCE`, `#FreeType`, `#mitigation`

---

<a id="item-tech-news-5"></a>
### [Aaronson 称 AI 加速数学进展，社区质疑证明验证](https://scottaaronson.blog/?p=10379) ⭐️ 7.0/10

这篇 Hacker News 热帖指向 Scott Aaronson 的博客文章；文章声称近期出现一波 AI 辅助解决数学与理论计算机科学开放问题的进展，并另链到一篇标题为《矩阵乘法指数是 9/4》的论文。现有材料只有博客标题、链接和讨论，没有给出可核验的具体结果、证明或复现实验，因此这些成果的规模与正确性仍属待确认的主张，而不是已确立的范式转变。对数学与理论计算机科学研究者而言，真正可检验的问题是这些证明能否在 Lean/Mathlib 中复核，以及其中多少来自 LLM 而非算力与形式化库。

hackernews · Kotlopou · 11月25日 19:11 · [社区讨论](https://news.ycombinator.com/item?id=50646108)

**「背景」** 这类宣称所依托的基础设施是 Lean 4 与 Mathlib 生态：形式化证明可以被机器逐行检查，近年还出现了专门面向 Lean 4 的代码智能体，例如 Horizon 3 月 17 日日报记录的 Mistral 开源模型 Leanstral-2603（119B 总参数、每 token 激活 6.5B）。但“AI 解决开放数学问题”并非首次出现：Horizon 10 月 7 日日报报道，OpenAI 发布《Sharing AI Progress in Mathematics》并在 GitHub 公开预印本，宣称证明了 Barnette 猜想等结果、解决了 proofatlas.ai 前 500 个开放问题中的 90 个，而当时既无独立验证，也无同行评审结论。此次与那批宣称相衔接的具体文献是矩阵乘法指数 ω ≤ 9/4：arXiv 论文 2610.28627 称 OpenAI 此前以非构造性论证在复数精确标量算术模型下建立了该上界，该论文则给出自包含的构造性证明。

**「对算法研究者的直接影响」** 如果 11 月 24 日预印本《The matrix multiplication exponent is nine fourths》所声称的、对任意域上方阵乘法的匹配上界与下界成立，那么矩阵乘法的渐进复杂度就被钉死在 2.25，研究人员继续寻找更低渐进指数的空间随之关闭，精力应转向常数因子优化与实际实现。不过该结论目前仍是研究者自行发布、尚未经同行评审的预印本；评论区也提醒，机器生成的 Lean 证明常出现与非形式化证明不一致或包含未使用段落等问题，因此在 Lean 校验通过之前不宜把它当作已定论。

**「社区讨论」** 评论者 utopiah 质疑，同样的结果有多少可能只靠 Lean、Mathlib 和大量算力、而不靠 LLM 取得；onetimeusename 则强调，不能把 Lean 证明与 informal proof 的差异或未使用部分当作“琐事”，机器生成证明的可靠性问题由来已久。也有评论者担心这类能力若只适用于可验证任务尚可，外溢到不可验证领域会带来更大不确定性。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://huggingface.co/mistralai/Leanstral-2603">2026-03-17 — Mistral AI releases Leanstral-2603, an open-source code agent for Lean 4 proof assistant</a></li>
<li><a href="https://openai.com/index/sharing-ai-progress-in-mathematics/">2026-10-07 — OpenAI 发布数学 AI 进展，宣称证明多个开放问题</a></li>
<li><a href="https://arxiv.org/abs/2610.28627">[2610.28627] Matrix Multiplication from Polynomial Packings ...</a></li>
<li><a href="https://interestingengineering.com/culture/openai-exact-2-25-matrix-multiplication-exponent">OpenAI establishes exact 2.25 exponent for matrix multiplication</a></li>
<li><a href="https://www.alphaxiv.org/abs/2611.matrix-multiplication-exponent-lower-bound">The Matrix Multiplication Exponent Is Nine Fourths | alphaXiv</a></li>

</ul>
</details>

**标签**: `#AI for mathematics`, `#LLM reasoning`, `#Lean theorem proving`, `#complexity theory`, `#Hacker News discussion`

---

<a id="item-tech-news-6"></a>
### [腾讯开源 Hy4 flash GGUF 量化权重，最小版可运行于 64GB Mac mini](https://mp.weixin.qq.com/s/o0xxShVQX6g2UllrrEv1WQ) ⭐️ 7.0/10

腾讯混元通过大模型压缩加速工具箱 AngelSlim 开源了 224B 参数模型 Hy4 flash 的 GGUF 量化权重。原权重约 410.27GiB，最小 IQ2-AH 版本为 125.73GiB，约为原版的 30%；发布信息称，借助 Strata offload 框架，该版本可在 64GB Mac mini 上运行。发布数据还显示，48GB 显存设备在 10K 上下文下每秒生成 89 个 token，M5 Max 128GB 在 Q3\_K 版本、32K 上下文下每秒生成 47 个 token；Q3\_K 在 DeepSWE v1.1 等评测中与原模型得分差距不超过 0.4 分。上述性能和精度数字尚未见独立验证。

telegram · zaihuapd · 11月25日 09:29

**「背景」** GGUF 是 llama.cpp 生态中常用的模型文件格式，量化通过降低权重精度来压缩模型体积。Offload 则把部分计算或权重放到显存之外的内存或存储中，以缓解本地硬件显存不足的问题。

**「影响」** 对本地部署者而言，复现发布数据需要匹配对应的量化版本和运行配置：89 token/s 对应 48GB 显存设备与 10K 上下文，47 token/s 对应 M5 Max 128GB、Q3\_K 与 32K 上下文。最小版能否在 64GB Mac mini 上达到可用速度，还取决于 Strata offload 的具体配置。

**标签**: `#LLM quantization`, `#Tencent Hunyuan`, `#GGUF`, `#model offloading`, `#consumer hardware`

---

## 科技博客

<a id="item-tech-blog-1"></a>
### [简单旋转迁移大模型事实回忆表征](https://hazyresearch.stanford.edu/blog/2026-11-25-platos-key) ⭐️ 9.0/10

rss · Stanford Hazy Research Blog · 11月25日 07:00

**「背景」** 柏拉图表征假说认为，不同神经网络会收敛到对现实的共享表征；已有工作显示模型间几何相似，但相似并不等于可互换。作者要回答：一个冻结的大模型能否直接使用另一个模型的事实回忆表征，而无需梯度更新？

**「方案」** 作者把事实回忆看作键值检索，在主语末 token 的键上做替换而非改权重：用正交 Procrustes 旋转（薄 SVD）加一个全局缩放，以少量双方都能答对的事实闭式拟合映射。实验覆盖 8 个家族、1.5B–27B 的 12 个基座模型、20 个模型对和 8,800 条事实（16 种关系），迁移准确率中位数为 41%，而以模型自身另一事实键替换的自交换为 55%，前者保留后者 73%。更灵活的岭回归、白化旋转或 MLP 仅在 7% 的比较中显著更优；按互近邻相似度选层仅得 4.5%，远低于按迁移准确率选层。旋转还能串联，链式映射保留直接映射 99% 的准确率；每模型取 256 个主成分仍有 74%。作者把 2,600 次失败中的 56% 判为“暗记忆”——模型存储却未能回忆的事实，再用旋转后的供体键恢复其中 18%，对照方法不超过 1.1%。作者也提醒，绝对迁移准确率仍属中等，结论限于基座模型的事实回忆。

**「启示」** 作者据此认为，大模型的事实表征不仅几何相似，而且至少部分可功能互换，并指向共享的低维几何；这也提示部分回忆失败源于表征或键无效，而非知识缺失，为跨模型知识迁移与潜在通信提供了研究方向。

**标签**: `#LLM representations`, `#representation alignment`, `#factual recall`, `#mechanistic interpretability`, `#model interoperability`

---

<a id="item-tech-blog-2"></a>
### [NVFP4 注意力寄存器回收优化](https://developer.nvidia.com/blog/how-to-optimize-nvfp4-attention-on-nvidia-rtx-blackwell-through-register-recycling/) ⭐️ 8.0/10

rss · NVIDIA Inference Performance Blog · 11月25日 19:30

**「背景」** RTX PRO 6000 Blackwell（SM120）的长序列注意力受 BF16 MMA 吞吐限制，且其 Tensor Core 架构与数据中心 GPU 不同，FlashAttention3/4 无法直接移植。NVFP4 可提高 4-bit 矩阵乘吞吐，但 softmax、数据搬运和中间存储若不能重叠，Tensor Core 仍会空转。

**「方案」** 作者以 SageAttention3 的 CTA 为基线：4 个生产者 warp 和 8 个消费者 warp 对每个 N128 tile 串行执行 QK、softmax/量化和 PV，softmax 阶段留下 Tensor Core 空档；寄存器已占约 95.3%，无法再放完整 score tile。优化保留相同 warp 配置和 N128 K/V 加载，把 score tile 拆成两个 N64 寄存器槽：先对完整 N128 更新 online-softmax，一半完成指数化与 NVFP4 量化后，立即复用其寄存器计算下一 tile 对应半边的 QK，再与当前 tile 的 PV 交错，形成跨 tile 的 ping-pong。这样无需第二块完整 score buffer 就能填缝；相同输入下 kernel 加速约 1.17–1.64 倍，Reactor 生产端到端延迟降低约 1.1%–15.3%，长序列 OmniDreams 约 15%，Helios 约 1.3%。

**「启示」** 作者的核心论点是：在寄存器近乎耗尽的 SM120 上，拆分 score tile 并在量化后回收寄存器，可在不增加完整 score 缓冲区的条件下，把相邻 tile 的 QK 与当前 tile 的 softmax/PV 重叠，从而提升 NVFP4 注意力吞吐；该优化已进入 FlashInfer 主分支。

**标签**: `#NVFP4 attention`, `#SM120`, `#GPU kernel optimization`, `#register recycling`, `#FlashInfer`

---

## 财经新闻

<a id="item-finance-news-1"></a>
### [美商务部被曝施压英特尔交出 10%股份](https://www.wired.com/story/inside-trumps-demands-to-another-chips-ceo/) ⭐️ 9.0/10

据法庭文件报道，2025 年 8 月美国商务部律师在电话中警告英特尔首席财务官，董事会可以拒绝交出股份，但将面临“无法预测的后果”；几天后，英特尔董事会交出了美方要求的股份。特朗普随后称，美国政府“完全拥有并控制”英特尔 10%的股份且未为此付款，这批股份现值约 110 亿美元。

telegram · zaihuapd · 11月25日 13:25

**「背景」** 据《纽约时报》报道，特朗普政府正通过交易取得英特尔等私营企业的股份，相关交易规模已达数十亿美元，且这一不同寻常的做法没有放缓迹象。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://www.nytimes.com/2025/11/25/us/politics/trump-intel-steel-minerals-china.html">Trump Administration Is Taking Billions in Stakes in Firms Like Intel ...</a></li>

</ul>
</details>

**标签**: `#Intel`, `#US government`, `#semiconductor industry`, `#equity stake`, `#industrial policy`

---

<a id="item-finance-news-2"></a>
### [美国拟依据 301 条款对 14 个贸易伙伴加征国别关税](https://www.cnbc.com/2026/11/25/us-tariffs-trump-section-301.html) ⭐️ 8.0/10

美国据报计划依据 1974 年《贸易法》第 301 条，对中国、欧盟、日本、印度等 14 个贸易伙伴加征按国别设定的新关税，理由是应对制造业结构性产能过剩。中国将在 2018 年已加征的 25%关税之上再加征 20%；若中国未遵守 2025 年 10 月在韩国釜山达成的贸易休战协议，对华新关税可能升至 40%。

telegram · zaihuapd · 11月25日 13:59

**「背景」** 美国《1974 年贸易法》第 301 条授权总统针对被认定损害美国商业的外国贸易做法采取加征关税等报复措施。此次提及的釜山贸易休战，是 2025 年 10 月 30 日特朗普与中国国家主席习近平在韩国釜山达成的为期一年的关税与出口管制缓和安排。

**「影响」** 若上述计划实施，中国相关出口商将在现有 25%关税之外多承担 20%，美国进口商也可能面临更高采购成本。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://en.wikipedia.org/wiki/Section_301_of_the_Trade_Act_of_1974">Section 301 of the Trade Act of 1974 - Wikipedia</a></li>
<li><a href="https://en.wikipedia.org/wiki/Busan_Summit">Busan Summit - Wikipedia</a></li>
<li><a href="https://www.cfr.org/articles/united-states-and-china-agree-trade-truce">United States and China Agree to Trade Truce | Council on ...</a></li>

</ul>
</details>

**标签**: `#US tariffs`, `#Section 301`, `#China trade`, `#EU trade`, `#trade policy`

---