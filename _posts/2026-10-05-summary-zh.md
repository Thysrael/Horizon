---
layout: default
title: "Horizon Summary: 2026-10-05 (ZH)"
date: 2026-10-05
lang: zh
---

> 从 18 条内容中筛选出 1 条重要资讯。

---

**科技新闻**
1. [Strata 在 RTX 4090 上以 100+ tokens/s 运行 125B Qwen 3.8 Flash Next](#item-tech-news-1) ⭐️ 7.0/10

---

## 科技新闻

<a id="item-tech-news-1"></a>
### [Strata 在 RTX 4090 上以 100+ tokens/s 运行 125B Qwen 3.8 Flash Next](https://github.com/Niko1221/Strata) ⭐️ 7.0/10

GitHub 项目 Strata 被发布在 Hacker News 上，声称可在消费级 GPU 上运行 125B 的 Qwen 3.8 Flash Next，并在 RTX 4090 上达到 100 tokens/s 以上。Hacker News 用户 snehesht 称在自己的 RTX 4090、128GB DDR5、Ryzen 7950X3D 机器上实测 124 tokens/s，但该结果尚未获得独立验证。同一讨论中，Jackson\_\_ 报告在相同 GGUF 与视觉适配器权重下，Strata 在 50 张图像的坐标定位基准中位误差为 154.8 像素、平均 168.8 像素，而 llama.cpp 分别为 46.5 和 81.4 像素，提示低比特推理可能带来质量退化。a11r 也对低于 4-bit 的量化表示怀疑，并称 4-bit 量化在 RTX Pro 6000 上足以处理困难但范围明确的编码任务。

hackernews · snehesht · 10月4日 12:51 · [社区讨论](https://news.ycombinator.com/item?id=49953495)

**「背景：Qwen3.8-Flash-Next 的架构由来」** 当前讨论的 Qwen3.8-Flash-Next 是阿里通义此前发布并开源的多模态 MoE 模型：据 8 月 27 日的日报报道，它采用 125B 主模型加 51B N-gram 嵌入、每 token 仅激活 6B 参数的架构，原生上下文为 262K，并被官方定位为 Qwen4 架构的预览。该模型的 Hugging Face 页面也确认了这一 125B 参数、6B 激活（外加 4B MTP）的配置。正因为每个 token 只激活很小一部分参数，本地推理工具才有机会尝试在消费级显卡上以高吞吐运行它。

**「影响与部署注意」** 对打算在自己机器上部署该模型的人，关键动作是按具体任务验证输出质量，而不是只看吞吐量：一位评论者用同一份 GGUF 与视觉适配器权重做 50 张图片的坐标定位测试，Strata 的中位误差为 154.8 像素，而在 llama.cpp 下为 46.5 像素（该数据为评论者自测，未经独立复核）。兼容性方面，社区已提到 ds4/Dwarfstar 等替代推理栈同样支持该模型，Strata 仓库则自述目标是让该模型在普通 PC 上本地运行，并称速度数据是在“两台普通游戏 PC”上测得，部署前应确认所选工具链与量化方案对目标任务的实际表现。

**「社区讨论」** 评论区的分歧集中在速度与质量能否兼得：Jackson\_\_ 的视觉基准显示 Strata 相比 llama.cpp 误差更大，而 a11r 认为低于 4-bit 的量化可能显著降低质量。与此同时，AntiRush 报告在 RTX 6000 Pro 上使用 ds4 的 Q4 量化可达到 255.26 tokens/s 解码并支持 4 路并发，kamranjon 也称 ds4 的 Q4 量化日常表现良好。

<details><summary>参考链接</summary>
<ul>
<li><a href="https://qwen.ai/blog?id=qwen3.8-flash-next">2026-08-27 — Qwen3.8-Flash-Next：新架构以 1/9 成本超越 Qwen3.7-Plus</a></li>
<li><a href="https://huggingface.co/Qwen/Qwen3.8-Flash-Next">Qwen / Qwen 3 . 8 - Flash - Next · Hugging Face</a></li>
<li><a href="https://github.com/Niko1221/Strata">GitHub - Niko1221/Strata: Qwen3.8-Flash-Next on any consumer ...</a></li>

</ul>
</details>

**标签**: `#LLM inference`, `#quantization`, `#consumer hardware`, `#open source`, `#model deployment`

---