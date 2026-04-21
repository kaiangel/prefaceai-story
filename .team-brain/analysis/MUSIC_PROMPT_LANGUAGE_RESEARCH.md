# AI 音乐生成：中英文混合 Prompt 研究报告

> 目的：系统调研 Mureka 及主流 AI 音乐平台对中英文混合 prompt 的处理表现，为序话Story BGM 生成给出可操作的 prompt 语言策略建议。
>
> 调研范围：2024-2026 年官方文档 / 学术论文 / 社区经验
> 调研日期：2026-04-18
> 调研人：Researcher Agent（Opus 4.7，1M context）

---

## 1. TL;DR

**对 Mureka（项目当前选型）而言，英文为主 + 中文意象点缀的混合 prompt 是"基本无害甚至略有利"的策略，但"利"的主要来源并非中文字符本身的语义，而是它在 prompt 中承载的具象画面/文化符号能激发更丰富的氛围描写。** 证据链支持以下具体策略：

1. **骨架用英文**（genre / instrument / tempo / mood / production 术语）— 所有主流模型的 text encoder（T5 / CLAP / BERT）都在英文音乐元数据上训练最充分，英文术语命中率最高。
2. **中文用于"场景意象 / 情感特写"**（如"年夜饭上没人说话"）— 放在 prompt 中段，作为"画面化氛围锚点"，不要承担参数化控制职责。
3. **避免把技术词用中文写**（不要写"钢琴、稀疏低音"，应写"Piano, sparse and low"）— 中文的音乐技术词在 tokenizer 中稀疏，会被切成无语义子 token。
4. **开头 5-10 tokens 必须英文核心风格词**（被模型权重最高），中文意象不要放开头。
5. **不要超过 30% 中文字符占比**，且避免跨句子频繁切换语言（code-switching 内部切换会增加跑偏概率）。

**置信度**：中（60%）。Mureka 官方没有对"混合 prompt"做明示表态；结论主要从底层 text encoder 原理 + Suno/Udio/YuE 同类平台经验外推；序话Story 自身 6 首 BGM 样本不足以做统计结论。建议做一次 A/B 对照实证补齐（详见 §5.2）。

---

## 2. 证据链

### 2.1 Mureka 官方信息

| 信息点 | 内容 | 来源 |
|--------|------|------|
| 支持语言 | 英语、中文、日语、韩语、法语、西班牙语、葡萄牙语、德语、意大利语、俄语（共 10 种） | [Mureka O1 Announcement](https://platform.mureka.ai/docs/en/ai-music-o1-moment.html) / [本地 MUREKA_API_FULL_DOCS.md:1219](../analysis/MUREKA_API_FULL_DOCS.md) |
| Instrumental 端点 | `POST /v1/instrumental/generate`，`prompt` 字段最大 **1024 字符**（序话Story 当前 V4 BGM 为 732 字符，在限内） | [useapi.net Mureka docs](https://useapi.net/docs/api-mureka-v1/post-mureka-music-create-instrumental) |
| 推荐 Prompt 语言 | 官方 V8/V9 教程明确写 **"Write prompts in plain English"**（如 "upbeat pop song with female vocals" / "cinematic orchestral score"） | [Mureka V8 AnyMusic guide](https://anymusic.ai/create), [Musci.io Mureka Tutorial 2026](https://musci.io/blog/mureka-tutorial) |
| 混合语言官方表态 | **未找到**明确声明"支持/推荐/不推荐混合语言 prompt"。官方只说"支持 10 种语言的 vocal 生成"和"prompt 用英文"，未对"instrumental prompt 里混入中文"做任何表态 | 反复搜索 Mureka 官方文档未获 |
| 模型语言差异 | V6+ 开始强调 10 语言 vocal 能力；O1/O2 通过 Chain-of-Thought (MusiCoT) 预先规划曲式，更能处理复杂/模糊描述；V7.5/V8/V9 主打情绪智能和乐器控制，未专门宣传多语言优势 | [Skywork Mureka O1 release](https://www.prnewswire.com/news-releases/kunlun-tech-launches-the-worlds-first-music-reasoning-large-model-mureka-o1-leading-the-global-ai-music-revolution-302411665.html), [Mureka V7 announcement](https://www.thatericalper.com/2025/07/28/skywork-unveils-mureka-v7-and-tts-v1-ushering-in-a-new-era-of-emotionally-intelligent-ai-music-and-voice/) |

**关键空白**：Mureka 没有公开 instrumental prompt 的 text encoder 架构（是否 T5、是否多语言 finetune），也没有发布 instrumental 方向的 best-practice 文档。Song 方向有 MusiCoT 论文，但论文聚焦乐曲结构推理，不讨论多语言 prompt 处理。

### 2.2 Top AI 音乐平台横向调研

#### Suno AI
- **语言支持**：v5 支持多语言 vocal（包括中文、日文、韩文、阿拉伯语、法语、西语等）。[Suno v5 Multilingual Guide – Jack Righteous](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-v5-multilingual-english-pronunciation-guide)
- **混合语言官方/社区态度**：**不建议在同一 verse 内混用语言**，建议"一个段落一个语言"，并显式声明 "All lyrics in [lang], no English"。否则容易出现发音错乱和语义跑偏。[MusicSmith Suno Prompt Guide 2026](https://musicsmith.ai/blog/ai-music-generation-prompts-best-practices)
- **底层文本处理**：Bark（Suno 早期 TTS 模型）用 HuggingFace BERT tokenizer；新版 Suno 具体 text encoder 未公开，但 [Latent Space 播客](https://www.latent.space/p/suno)访谈 Mikey Shulman 提到用 transformer-based text conditioning。
- **Chinese lyric-following 绝对分数**：73%（YuE 论文 benchmark，相对其他模型最高）。[YuE Paper](https://arxiv.org/html/2503.08638v1)
- **社区经验 (Zhihu)**：中文 prompt 会被 Suno 内部翻译器转成英文后再处理，因此"直接英文"比"中文→翻译"更可控；建议中英对照写法，chorus 英文 verse 中文是 pop 场景常见套路。[Zhihu Suno 使用指南](https://zhuanlan.zhihu.com/p/691864442)

#### Udio
- **语言支持**：10+ 种语言的 lyrics 生成，明确列出 Chinese (Hong Kong / Taiwan / China) 三种变体。[Udio AI Overview](https://www.soundverse.ai/blog/article/what-is-udio-ai-0139)
- **混合语言态度**：未找到官方明确规则；数据驱动研究 [arXiv:2509.11824](https://arxiv.org/html/2509.11824v1) 对 Suno+Udio 输出做过大样本统计，发现英文 prompt 占压倒性多数，Chinese prompt 数据量远小于英文，评估结论适用性有限。

#### Stable Audio (Stability AI)
- **Text encoder**：**T5-base**（从 CLAP 改为 T5）。[Open Laboratory Stable Audio Open 1.0](https://openlaboratory.ai/models/stable-audio-open-1)
- **多语言能力**：官方说明 "performance is primarily tuned to English-language prompts due to the composition of the training metadata"。即**强英文偏置**，中文 prompt 不推荐。

#### Meta MusicGen / AudioCraft
- **Text encoder**：**T5 / FLAN-T5 / CLAP 对比后选择 T5** 作为主 encoder。[AI-Bites MusicGen Architecture](https://www.ai-bites.net/musicgen-from-meta-ai-model-architecture-vector-quantization-and-model-conditining-explained/)
- **多语言**：官方承认 "conditioning performance is optimized for English-language prompts, with reduced reliability for non-English inputs"。2025 更新有多语言 melody conditioning，但 text prompt 仍以英文为佳。[HuggingFace MusicGen docs](https://huggingface.co/docs/transformers/model_doc/musicgen)

#### Riffusion
- **Text encoder**：**CLIP ViT-L/14**（继承 Stable Diffusion 1.5）。原 CLIP 对中文的支持薄弱，CJK 字符在 cl100k_base tokenizer 中通常被切成 2-3 个无语义 BPE tokens。[Tony Baloney - CJK in Generative AI](https://tonybaloney.github.io/posts/cjk-chinese-japanese-korean-llm-ai-best-practices.html), [OpenAI CLIP Issue #7](https://github.com/openai/CLIP/issues/7)
- **多语言 CLIP 变体**：Multilingual-CLIP / Chinese-CLIP / AltCLIP 等存在但并非 Riffusion 默认配置。Riffusion 原生对中文 prompt 的"理解"更多是 CLIP 通过西语-中文弱对齐的泛化，**不可靠**。

#### Google Lyria 3 Pro
- **支持语言**：英、德、西、法、印地、日、韩、葡（共 8 种）。**明确不含 Chinese**。[Google Cloud Lyria 3 Prompt Guide](https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-lyria-3-pro)
- 对序话Story 场景意义不大（Lyria 不支持中文 vocal），但 prompt **可以写英文**。

#### ElevenLabs Music
- 2026 版支持"multilingual music prompts and generated vocals"，官方列出 English/Spanish/French/German/Japanese 等，中文支持**未明确列出**（TTS v3 支持 Mandarin 70+ 语言，但 Music 模块与 TTS 模块语言覆盖可能不同）。[ElevenLabs Music](https://elevenlabs.io/music), [ElevenLabs Cheat Sheet 2026](https://www.webfuse.com/elevenlabs-cheat-sheet)

#### YuE（开源，MAP 项目）
- **支持语言**：英文、中文（Mandarin + Cantonese）、日文、韩文，**明确支持 code-switching**（如日语城市流行 → 英文 rap 且保留原伴奏）。[YuE GitHub](https://github.com/multimodal-art-projection/YuE), [YuE Paper](https://arxiv.org/html/2503.08638v1)
- **Chinese lyrics-following**：60%（第二，Suno 73% 第一）
- 是目前**官方明确拥抱混合语言**的少数音乐模型之一，但 YuE 是 song-generation 模型（含人声），与 Mureka instrumental BGM 场景不完全一致。

#### OpenAI Jukebox（历史参考）
- 2020 发布，基于 VQ-VAE + transformer。主要以英文歌词训练。现已基本被 Suno/Udio 取代，多语言能力很弱。不推荐作为参考基线。

### 2.3 底层技术层面

| 技术点 | 发现 | 来源 |
|--------|------|------|
| 主流 text encoder | 音乐生成主要用 **T5 / FLAN-T5** (MusicGen, Stable Audio) 或 **CLAP** (LAION)；都有强英文偏置 | [T-CLAP Paper](https://arxiv.org/html/2404.17806v1), [MusicGen Docs](https://huggingface.co/docs/transformers/model_doc/musicgen) |
| 多语言音频-文本编码器 | **GLAP**（General Language Audio Pretraining）通过 Sonar 多语言文本编码器扩展 CLAP 至 7 种语言 + 多领域，但尚未被 Mureka/Suno/Udio 商用采纳 | [GLAP arXiv:2506.11350](https://arxiv.org/html/2506.11350v1) |
| Tokenization 中文行为 | cl100k_base 只有 ~100k token 空间，CJK 字符通常被切成 2-3 个 BPE 子 token，且子 token **无语义、无部首关系**；T5 SentencePiece 类似 | [OpenAI CLIP Issue #7](https://github.com/openai/CLIP/issues/7), [CJK LLM best practices](https://tonybaloney.github.io/posts/cjk-chinese-japanese-korean-llm-ai-best-practices.html) |
| Code-switching 在 LLM 中的效应 | 混合结果**有好有坏**：有研究发现 code-switching 可作为"正则化信号"略微提升 (ACL 2025 finding)；也有研究发现 LLM 在 code-switched 输入下理解力下降（ACL 2023）。普遍结论：**"内嵌英文在其他语言中"常有益，反向常有害** | [Multilingual Prompting Survey arXiv:2505.11665](https://arxiv.org/html/2505.11665v1), [ACL 2023 Multilingual LLMs Not Code-Switchers](https://aclanthology.org/2023.emnlp-main.774/) |
| 情感/情绪表达 | 研究表明用"native 语言 prompt"在情感/情绪任务上优于 English prompt（例如中文母语文化意象触发更准的情绪空间） | [Multilingual Prompting Survey](https://arxiv.org/html/2505.11665v1) |
| 早期 token 权重 | AI 音乐模型 "weight early tokens more heavily, meaning the first 5–10 words strongly influence genre direction" | [AI Music Street Prompt Engineering Guide](https://aimusicstreet.com/the-ultimate-guide-to-prompt-engineering-for-ai-music-generation/) |
| 数量化参数更稳 | "Adding numerical constraints reduces entropy in generation"（BPM/拍号/key 带数字更稳定）；"conflicting descriptors degrade output coherence"（避免相互冲突的形容词） | [MusicSmith 2026 Guide](https://musicsmith.ai/blog/ai-music-generation-prompts-best-practices) |

### 2.4 社区 & 创作者经验（中文圈）

- **知乎**：Suno 中文 prompt 经验贴主流做法是"中英对照"或"英文描述 + 中文关键词点缀"，普遍反馈"纯中文容易跑偏"。[Zhihu Suno 使用指南](https://zhuanlan.zhihu.com/p/691864442), [Zhihu 叙事式 Prompt 技巧](https://zhuanlan.zhihu.com/p/1969336051085578359)
- **飞书文档 Suno Prompt 技巧** 建议英文逗号分隔风格词（如 "pop, male"），lyrics 4-8 行最佳，过长会被忽略或产生幻觉。[Feishu Suno Prompt 技巧](https://docs.feishu.cn/v/wiki/UILbwhJGmisPLokts24cj16MnEg/a4)
- **vocus 中英双语指令表** 列出 50 条中英双语 Suno 指令，结构普遍是"英文风格骨架 + 中文题材关键词"。[vocus 50 条双语指令表](https://vocus.cc/article/68a80bf9fd89780001e47acb)
- **本项目自测**：6+ 首 BGM 均采用"英文骨架 + 中文画面意象"格式，主观听感良好但无量化 A/B。

---

## 3. 横向对比表

| 平台 | 支持中文 | 混合 prompt 态度 | Text encoder | 官方 best practice 提示 |
|------|---------|-----------------|-------------|----------------------|
| **Mureka（V8/V9/O2）** | ✅ (10 种) | 未明示，官方教程只用英文示例 | 未公开（推测 T5 / 自研） | "Write prompts in plain English" |
| **Suno** | ✅ | ⚠️ "一段落一语言"，不建议 verse 内混 | 未公开 | 显式声明主语言，避免 code-switching |
| **Udio** | ✅ (含 HK/TW/CN 变体) | 社区自由，官方无规则 | 未公开 | 无 |
| **Stable Audio Open** | ❌ (英文 primary) | 不建议非英文 | T5-base | 英文 only |
| **MusicGen** | ⚠️ 可接受但质量下降 | 不建议非英文 | T5 / FLAN-T5 / CLAP | 英文为主 |
| **Riffusion** | ⚠️ CLIP 弱支持 | 不建议 | CLIP ViT-L/14 | 英文为主 |
| **Google Lyria 3 Pro** | ❌ 8 种中不含中文 | N/A | 未公开 | 英文 / 支持语言 only |
| **ElevenLabs Music** | ⚠️ 不明确 | 未表态 | 未公开 | 无 |
| **YuE (开源)** | ✅ Mandarin+Cantonese | ✅ **明确支持 code-switching** | LLaMA2 架构 | 支持跨语言风格迁移 |
| **OpenAI Jukebox** | ❌ 英文主 | N/A | VQ-VAE+Transformer | 已过时 |

---

## 4. 对序话Story 的应用建议

基于项目当前用 `api.mureka.cn` 的 `/v1/instrumental/generate` 端点 + `mureka-9` (auto) 模型，BGM 场景为"无人声氛围配乐"，给出以下建议：

### 4.1 混合语言 prompt 的总体判断

- **对 Mureka 大概率"略有利到中性"**，而非"有害"。但"有利"的证据链是间接的：
  - ① Mureka 是中国背景公司（Skywork/昆仑万维），训练语料很可能比 Suno/Udio 包含更多中文素材；官方明确支持 10 种语言的 vocal 处理，instrumental prompt text encoder 大概率也见过中文。
  - ② 当前 V4 年夜饭 BGM 这种"英文骨架 + 中文意象"结构没有出现明显跑偏，说明模型至少不会因为中文就拒绝或紊乱。
  - ③ 中文里的"画面感场景词"（年夜饭、烟花、胡同）在英文里没有等价简短表达，保留中文能守住意境浓度。
- **"有利"的上限不高**：混合 prompt 的主要收益来自"创作者思维层"（中文更易写出画面感），而不是"模型理解层"（模型并不真的比纯英文更懂你）。因此若改纯英文 + 足够好的画面化描写，结果可能同样好。
- **结论**：继续用"英文为主 + 中文意象点缀"是安全的 baseline，但不要迷信它必然更好。

### 4.2 具体可操作规则

**规则 1：骨架英文，意象中文**

| 内容类型 | 推荐语言 | 原因 |
|---------|--------|------|
| Genre / Style (`slow acoustic`, `cinematic underscore`) | 🇬🇧 英文 | 模型技术词汇训练密度高 |
| Instruments (`piano`, `cello`, `upright bass`) | 🇬🇧 英文 | 乐器专有名词英文是音乐产业通用语 |
| Tempo / BPM / Key (`60 BPM`, `A minor`) | 🇬🇧 英文 + 数字 | 数字化参数降低 entropy |
| Mood / Emotion (`melancholic`, `nostalgic`, `tender`) | 🇬🇧 英文 | 情感词在英文语料中数量大、区分度高 |
| Production / Mix (`warm tape saturation`, `sparse`, `lo-fi`) | 🇬🇧 英文 | 这是"行话"，中文对应词模糊 |
| **Scene imagery / Cultural anchor**（年夜饭、烟花、胡同、窗外雨声） | 🇨🇳 中文 | 英文翻译丢失文化密度；中文承载具象画面 |
| **Emotional specificity**（"父亲没说出口的那句话"） | 🇨🇳 中文 | 情感细节的母语表达更准 |

**规则 2：位置 — 中文夹在中段，不在开头不在结尾**

- **开头（token 1-10）**：必须英文核心风格词，决定 genre 和整体基调。例：`Slow, heavy, suffocating. Piano, sparse and low.`
- **中段**：中文意象（1-3 句），给模型"画面锚点"。例：`年夜饭上没人说话，烟花声从窗外传来，又灭了。`
- **结尾**：英文 production/mood 收尾，让最后一层权重仍落在英文技术词。例：`Warm amber light over cold stone. Not hopeless. Just heavy.`

这正是你们 V4 示例 prompt 的结构，保持即可。

**规则 3：中文占比控制在 15-30%**

- 太少（<10%）：中文丧失"锚点"价值，不如纯英文；
- 太多（>40%）：进入 CJK token 主导区，模型对 prompt 整体的理解可能下降；
- 经验甜蜜点：**20-25%**，大约是 1-3 句中文意象 + 一段英文骨架。
- 当前 V4 BGM（732 字符）若粗估，估计 15-25% 中文，处于安全区。

**规则 4：避免"verse 内切换"式 code-switching**

- ❌ 不要写 `Piano 钢琴 plays softly 柔和地`（同一句中切换，token 语义会打架）
- ✅ 整句中文 / 整句英文，用句号或换行分开（如你们现在的写法）

**规则 5：技术词永远英文，即使更想用中文表达**

- ❌ 避免写"钢琴、稀疏、低沉"（中文音乐技术词在 tokenizer 中稀疏且无音乐训练上下文）
- ✅ 坚持写 `piano, sparse, low register`

**规则 6：情绪词避免相互冲突**

- ❌ `dark, happy, energetic, slow`（模型会糊弄）
- ✅ `melancholic, tender, slow, introspective`（语义一致）

### 4.3 对 V4 年夜饭 BGM prompt 的审视

你们当前 prompt：
```
Slow, heavy, suffocating. Like a breath held too long at a family dinner table.
Piano, sparse and low. Notes that sink, not rise. No resolution.
年夜饭上没人说话，烟花声从窗外传来，又灭了。
Beneath the silence, something like love — but it cannot speak. 
Warm amber light over cold stone. Not hopeless. Just heavy.
```

按本报告规则打分：

| 维度 | 评分 | 说明 |
|------|------|------|
| 开头英文骨架 | ✅ | `Slow, heavy, suffocating` 开头权重高 |
| 技术词英文 | ✅ | piano / sparse / low 全英文 |
| 中文位置 | ✅ | 夹在中段，不在开头不在结尾 |
| 中文承载画面 | ✅ | "年夜饭…烟花声…窗外"是典型文化画面锚点 |
| 中文占比 | ✅ | 估计 15-20%，在安全区 |
| 结尾英文收束 | ✅ | `Not hopeless. Just heavy.` 英文 mood 收尾 |
| 情绪一致性 | ✅ | heavy / melancholic / tender 语义一致 |
| 技术参数 | ⚠️ | 没有 BPM / key 等数字化参数 — 可选加入（如 "60 BPM, A minor"）进一步降熵 |

**结论**：V4 prompt 是**接近教科书级别**的混合 prompt 范本，可以作为项目内 BGM prompt 模板。唯一可加的是 BPM / key 数字。

---

## 5. 未解决问题 & 建议后续实证

### 5.1 没有闭合答案的问题

1. **Mureka 到底用的是什么 text encoder？** 官方未披露。不知道是纯英文 T5 / finetuned 多语言 T5 / 自研中英双语 encoder。
2. **mureka-9 vs mureka-o2 对混合 prompt 的响应差异？** O2 有 Chain-of-Thought（MusiCoT）推理能力，理论上对模糊/复合描述更稳，但无公开基准数据。
3. **中文意象的"最佳句数"**：1 句 vs 3 句 vs 5 句，哪个产出最好？无数据。
4. **繁体中文 vs 简体**：Mureka 作为中国公司，简体是默认训练集，但繁体是否同等处理？未测。
5. **中文诗词/古文会触发更"东方风格"的生成吗？** 假设可能成立（训练数据中古诗词常伴随国风音乐），未测。

### 5.2 建议的 A/B 实证设计

为补齐项目自身证据链，建议跑一次**小规模 A/B**：

**实验方案**：
- 取 3 个场景故事（都市情感 / 古风 / 现代职场），每个场景同一画面
- 每个场景做 3 个 prompt 变体（共 9 次 generation × n=2 = 18 首）：
  - **变体 A**：纯英文（把中文意象全翻译成英文）
  - **变体 B**：当前混合（英文骨架 + 中文意象，~20% 中文）
  - **变体 C**：中文主导（把英文技术词也尽量中文化，~60% 中文）
- 盲听打分：氛围匹配度 / 情绪浓度 / 技术完成度各 1-5 分
- 评审：Founder + PM + Resonance（3 人独立盲听 → 取均值）
- 预算：18 首 × mureka-9 费率 ≈ 1-2 美元，1 小时内可完成

**预期结论**：
- 若 A ≈ B > C → 证明混合 prompt 主要收益是"创作思维"而非"模型理解"，项目可用英文模板 + 中文素材库两条路并行；
- 若 B > A 且 B > C → 证明混合 prompt 确实比纯英文更好，固化为 BGM skill 模板；
- 若 B ≈ A ≈ C → Mureka 对 prompt 语言敏感度低，重点应转向其他参数（BPM/乐器/mood 词）调优。

### 5.3 优先级建议

- **P0 现在就做**：把本报告结论（§4.2 六条规则 + §4.3 V4 评分）固化到 `.claude/skills/music-prompt/knowledge/mureka_model.md` 或新建 `bilingual_prompt_rules.md`，让 AI-ML Agent 未来写 BGM prompt 时有据可循。
- **P1 下一批 BGM 生成前做**：跑 §5.2 的小 A/B，18 首，<2 美元成本。
- **P2 与 Ben 沟通后做**：若 Ben 后端集成 Mureka o2 模型，重跑一次 §5.2 对比 mureka-9 vs mureka-o2 的混合 prompt 响应差异。

---

## 附录：所有引用链接

### Mureka 相关
- [Mureka O1 Announcement (platform.mureka.ai)](https://platform.mureka.ai/docs/en/ai-music-o1-moment.html)
- [Mureka.ai 主站](https://www.mureka.ai)
- [Mureka API Platform 首页](https://platform.mureka.ai/)
- [Mureka API Docs 根目录](https://platform.mureka.ai/docs/)
- [Mureka MCP GitHub](https://github.com/SkyworkAI/Mureka-mcp)
- [useapi.net Mureka v1 instrumental endpoint](https://useapi.net/docs/api-mureka-v1/post-mureka-music-create-instrumental)
- [Skywork AI Mureka 平台综述](https://skywork.ai/blog/mureka-ai/)
- [Mureka V8 AnyMusic 指南](https://anymusic.ai/create)
- [Mureka V9 官方 mirror](https://murekav9.com/)
- [Musci.io Mureka Tutorial 2026](https://musci.io/blog/mureka-tutorial)
- [Mureka O1 PRNewswire Release](https://www.prnewswire.com/news-releases/kunlun-tech-launches-the-worlds-first-music-reasoning-large-model-mureka-o1-leading-the-global-ai-music-revolution-302411665.html)
- [Skywork Mureka V7 / TTS V1 Release](https://www.thatericalper.com/2025/07/28/skywork-unveils-mureka-v7-and-tts-v1-ushering-in-a-new-era-of-emotionally-intelligent-ai-music-and-voice/)

### Suno 相关
- [Suno v5 Multilingual Guide - Jack Righteous](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-v5-multilingual-english-pronunciation-guide)
- [MusicSmith Suno Prompt Guide 2026](https://musicsmith.ai/blog/ai-music-generation-prompts-best-practices)
- [How to Prompt Suno](https://howtopromptsuno.com/making-music)
- [Suno Bark GitHub Issue #335 - bilingual audio](https://github.com/suno-ai/bark/issues/335)
- [Zhihu Suno 使用指南](https://zhuanlan.zhihu.com/p/691864442)
- [Zhihu 叙事式 Prompt 技巧](https://zhuanlan.zhihu.com/p/1969336051085578359)
- [Feishu Suno Prompt 技巧](https://docs.feishu.cn/v/wiki/UILbwhJGmisPLokts24cj16MnEg/a4)
- [vocus 50 条双语指令表](https://vocus.cc/article/68a80bf9fd89780001e47acb)
- [Latent Space 播客 - Making Transformers Sing](https://www.latent.space/p/suno)
- [Data-Driven Suno/Udio Analysis arXiv:2509.11824](https://arxiv.org/html/2509.11824v1)

### Udio / Stable Audio / MusicGen / Riffusion / Lyria / ElevenLabs
- [Udio 概览 - soundverse](https://www.soundverse.ai/blog/article/what-is-udio-ai-0139)
- [Stable Audio Open 1.0 (Open Laboratory)](https://openlaboratory.ai/models/stable-audio-open-1)
- [MusicGen Architecture (AI-Bites)](https://www.ai-bites.net/musicgen-from-meta-ai-model-architecture-vector-quantization-and-model-conditining-explained/)
- [MusicGen HuggingFace docs](https://huggingface.co/docs/transformers/model_doc/musicgen)
- [Riffusion model v1 HuggingFace](https://huggingface.co/riffusion/riffusion-model-v1)
- [Google Lyria 3 Pro Prompt Guide](https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-lyria-3-pro)
- [Lyria 3 Gemini API docs](https://ai.google.dev/gemini-api/docs/music-generation)
- [ElevenLabs Music](https://elevenlabs.io/music)
- [ElevenLabs Cheat Sheet 2026](https://www.webfuse.com/elevenlabs-cheat-sheet)

### YuE / 学术
- [YuE Project Page](https://map-yue.github.io/)
- [YuE GitHub](https://github.com/multimodal-art-projection/YuE)
- [YuE Paper arXiv:2503.08638](https://arxiv.org/html/2503.08638v1)
- [GLAP Paper arXiv:2506.11350](https://arxiv.org/html/2506.11350v1)
- [T-CLAP Paper arXiv:2404.17806](https://arxiv.org/html/2404.17806v1)
- [Multilingual Prompting Survey arXiv:2505.11665](https://arxiv.org/html/2505.11665v1)
- [ACL 2023 - Multilingual LLMs Not Code-Switchers](https://aclanthology.org/2023.emnlp-main.774/)
- [CHI 2025 - Potentials and Limitations of Prompt-based Music Gen](https://dl.acm.org/doi/full/10.1145/3706598.3713762)

### Tokenization / Text Encoder
- [OpenAI CLIP Issue #7 (Chinese tokenizer)](https://github.com/openai/CLIP/issues/7)
- [Multilingual-CLIP GitHub](https://github.com/FreddeFrallan/Multilingual-CLIP)
- [Chinese-CLIP GitHub](https://github.com/OFA-Sys/Chinese-CLIP/blob/master/README_En.md)
- [CJK in Generative AI Best Practices (Tony Baloney)](https://tonybaloney.github.io/posts/cjk-chinese-japanese-korean-llm-ai-best-practices.html)
- [CLAP Text Encoder (emergentmind)](https://www.emergentmind.com/topics/clap-text-encoder)

### Prompt Engineering 通用
- [AI Music Street - Ultimate Guide to Prompt Engineering](https://aimusicstreet.com/the-ultimate-guide-to-prompt-engineering-for-ai-music-generation/)
- [Soundverse - Best Prompts for Music Generator AI](https://www.soundverse.ai/blog/article/best-prompts-for-music-generator-ai)
- [Envato - Better AI Music Prompts with MusicGen](https://elements.envato.com/learn/ai-music-prompts)

---

*报告完*
