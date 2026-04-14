# 变体 D 设计：李继刚式压缩共振格式

> **设计者**: PM
> **日期**: 2026-04-14
> **灵感来源**: 李继刚 Prompt 哲学 — 压缩、场域、共振、种子原则
> **目标**: 在保持角色一致性的前提下，最大化信息密度，省 token，提升生成质量

---

## 设计原则

### 从李继刚学到的

1. **压缩**："把想表达的话使劲压缩，意思不变，用极少字符表达"
   - 删除所有装饰性框线（`═══`）
   - 删除所有"DO NOT IGNORE"类恐吓性冗余
   - 每一个 token 都必须携带语义

2. **场域**："与其直接下达指令，不如创造一个能够自然唤起该模式的情境"
   - 不说 "MANDATORY STYLE: Digital Illustration"
   - 而是直接进入：`Digital illustration. Vibrant colors, clean lines, detailed artwork.`
   - 让模型通过描述自然进入风格场域，而非被命令

3. **人+事**："一个什么样的人（鲜活成立），做一件什么样的事（信息完善）"
   - 角色描述保持完整（identity_line 不动）
   - 但去掉外层包装（CRITICAL INSTRUCTIONS、FIXED/FLEXIBLE 属性列表）
   - 用一句话替代："Character appearance MUST match reference images."

4. **种子**："拿到种子，需要压缩。种子生长，需要自由"
   - Prompt 是种子，不是施工图纸
   - 给足关键信息（角色、场景、动作、风格），然后让模型自由生长画面
   - 不过度规定每个像素（当前 prompt 的 foreground/background/depth_layers 过于详尽）

5. **得意忘言**：结构是脚手架，不是牢笼
   - `[TAG]` 标签保留（帮助模型解析信息边界）
   - 但标签内的内容极度精练

---

## 变体 D 格式模板

```
{style_name}. {3-5 mandatory keywords}. Not: {3-5 forbidden keywords}.

[REF] Character/Scene reference images are labeled on-image. Match exactly.

[{char1_name_en} ({char1_name_zh})]
{identity_line: physical + clothing, comma-separated, one line}

[{char2_name_en} ({char2_name_zh})] (if applicable)
{identity_line}

[SHOT]
{camera_specs}. {image_prompt_core — scene + action + emotion + lighting}.

[TEXT] {text_overlay_instruction, if any}
Appearance: fixed. Expression/pose: flexible. No text in image unless above.
```

### 关键设计决策

| 决策 | 变体 A (当前) | 变体 B' (AI-ML) | 变体 D (李继刚) | 理由 |
|------|-------------|----------------|---------------|------|
| 风格块 | 6 行框线 + 150 词散文 | 首行框线 + 50 词 | **1 行关键词** | 散文被模型部分忽略；关键词精准锁定 |
| 角色一致性指令 | 6 行框线 FIXED/FLEXIBLE | 2 行压缩 | **1 句话** | "Match exactly" = FIXED 的全部语义 |
| 参考图说明 | 5 行段落 | `[REFERENCES]` 块 | **1 行 `[REF]`** | 模型只需知道"图上有标签，照着来" |
| identity_line | 完整保留 | 完整保留 | **完整保留** | 这是角色一致性生命线，不能压 |
| 场景描述 | Stage 4 原文 | Stage 4 原文 | **Stage 4 原文** | 核心语义，不动 |
| 末尾约束 | 无独立约束行 | `[CONSTRAINTS]` 块 | **1 行浓缩** | 所有约束压到一行 |
| 框线装饰符 | ~300 token | ~20 token | **0 token** | 零语义贡献 |

---

## 变体 D 真实 Prompt 示例（Shot 1 — 阿朗故事）

### 输入数据（来自 sq_upgrade_ab_test 4_storyboard.json）

```
角色: Lin Yichen (char_001) — 深蓝色薄毛衣+白衬衫, 黑色皮筋手环
风格: Digital Illustration
Shot: medium_close_up, slightly_high, 85mm, static
场景: 家庭年夜饭, 林逸晨低头看白米饭, 三秒沉默的重量
```

### 变体 D Prompt

```
Digital illustration. Vibrant colors, detailed artwork, clean lines. Not: photorealistic, photograph, 3D render.

[REF] Character/Scene reference images are labeled on-image. Match exactly.

[Lin Yichen (林逸晨)]
Young East Asian man, oval face, fair skin, dark brown almond eyes, jet black short slightly messy hair, deep navy blue thin-knit crew-neck sweater over white collared shirt, black rubber band on left wrist.

[SHOT]
Medium close-up, slightly high angle, 85mm, shallow depth of field. Lin Yichen head bowed completely, eyes fixed on half-eaten bowl of white rice below — gaze locked as if unable to look elsewhere. Jaw set, throat tensing, Adam's apple rolling in suppressed swallow. Shoulders drawn inward, posture caved, three seconds of silence made physical. Foreground: blurred rim of white rice bowl anchors bottom of frame. Background: warm amber dining room, steam from dishes, deep crimson blur of father's shirt at right edge. Overhead warm pendant light carving shadow beneath his brow, chiaroscuro.

[TEXT] Bottom thought bubble: "说出来……就说出来。"
Appearance: fixed. Expression/pose: flexible. No other text in image.
```

### Token 估算

| 模块 | 变体 A | 变体 B' | 变体 D |
|------|:------:|:------:|:------:|
| 风格块 | ~300 | ~120 | **~25** |
| 角色一致性指令 | ~125 | ~40 | **~12** |
| 参考图说明 | ~100 | ~50 | **~15** |
| 角色 identity | ~225 | ~225 | **~225** (不动) |
| 叙事/情绪 | ~88 | ~50 | **0** (融入 SHOT) |
| 全局方向 | ~113 | ~60 | **0** (融入 SHOT) |
| 场景描述 | ~450 | ~450 | **~400** (微压缩) |
| 对话嵌入 | ~88 | ~80 | **~30** |
| 框线装饰 | ~300 | ~20 | **0** |
| 末尾约束 | 0 | ~30 | **~15** |
| **合计** | **~1690** | **~1050** | **~720** |
| **vs A** | — | -38% | **-57%** |

---

## 命令式 vs 描述式：核心假设分析

### 假设

> Gemini 图像模型对"描述式"（自然融入风格的场景语言）的响应质量 ≥ "命令式"（MANDATORY/DO NOT/MUST 指令），且更省 token。

### 支持证据（来自我们自己的生产数据）

1. **Stage 4 的 image_prompt 本身就是描述式的**
   - StoryboardDirector (Claude Sonnet 4.6) 生成的 image_prompt 是纯自然语言："Medium close-up, slightly high angle... Lin Yichen head bowed completely..."
   - 这段描述式文本是**实际画面的主要来源**——模型真正"画"的是这段话
   - 外层的 MANDATORY 框架是"指挥交通"，内层的描述才是"画图的信息"

2. **StyleEnforcer 的成功可能不是因为"命令"，而是因为"位置"**
   - StyleEnforcer 在 prompt **最前面**——利用了注意力 U 曲线的开头高峰
   - 它成功可能是因为位置优势，不是因为 `MANDATORY` 和 `═══` 的命令语气
   - 验证方法：变体 D 也把风格放最前面，但不用命令语气——如果风格一样稳，说明是位置决定的

3. **"DO NOT USE" 的有效性存疑**
   - 在 LLM 文本生成中，negative prompts 的效果因模型而异
   - Gemini 图像模型的文档没有明确支持 negative prompts 的语法
   - 我们的 forbidden_keywords 是用自然语言 "DO NOT USE: photorealistic..." 传递的
   - 等效写法 "Not: photorealistic..." 语义完全相同，省了 "DO NOT USE" 的命令框架

4. **Can Boluk 实验的启示**
   - Boluk 发现：**格式**比**内容**更重要——同样的信息，不同格式，性能差 10x
   - 我们的 A→B'→D 也是同样的信息，不同格式
   - 关键变量不是"有没有说 MANDATORY"，而是"信息是否在注意力高峰区"

### 反对证据

1. **当前 prompt 在生产环境已经稳定运行**
   - 80+ 风格预设，角色一致性 ~95%（NB2），风格漂移极少
   - "如果没坏，为什么要修？"

2. **图像生成模型 ≠ 文本 LLM**
   - 图像模型的 prompt 处理方式可能不同于 Claude/GPT
   - 可能对 "MUST"/"DO NOT" 有专门的注意力机制
   - 没有实际 A/B 数据，这是猜测

3. **角色一致性不能冒险**
   - identity_line 不变是安全的
   - 但如果去掉 FIXED/FLEXIBLE 框架后，模型对参考图的遵从度下降，代价极高

### 结论

**假设大概率成立**（60-70% 信心度），原因：
- Stage 4 的描述式 image_prompt 才是画面的真正来源，命令式框架是"包装纸"
- 风格稳定可能归因于位置而非语气
- Can Boluk 的实验和我们自己的历史优化都表明：格式 > 命令

**但必须用 10-shot 实测验证**，因为：
- 图像模型的内部机制不透明
- 角色一致性风险太高（生命线），不能靠理论分析做最终判断
- 需要至少 10 shots 的盲测对比（PM + Founder 不知道哪组是哪个变体）

---

## 10-Shot 三方对比设计

### 数据源

使用 `test_output/manualtest/sq_upgrade_ab_test/20260304_113630/` 的 25 shots storyboard 数据，选取 shot 1-10。

### 对比方案

| 变体 | 来源 | 核心差异 |
|------|------|---------|
| A (Baseline) | 当前 `image_generator.py` 组装 | 命令式框线 + 完整散文 |
| B' (AI-ML 推荐) | AI-ML 分析文档中的模板 | 标签式 + 压缩散文 + 首行框线 |
| D (李继刚式) | 本文档模板 | 关键词种子 + 自然描述 + 零框线 |

### 每个 shot 需要生成的内容

1. 三个变体的完整 prompt 文本
2. 每个 prompt 的精确 token 数（用 tiktoken 或字符估算）
3. 结构性差异标注（哪些信息在哪个位置）

### 评估维度（无需 API，纯分析）

| 维度 | 分析方法 |
|------|---------|
| Token 效率 | 精确计数 + 信息密度比 |
| 注意力位置 | 关键信息（风格/角色/动作）在 prompt 中的相对位置 |
| 信息完整性 | 三个变体是否包含相同的语义信息（逐项对照） |
| 风险点标注 | D 中被删除的内容，如果造成质量下降，会表现在哪里 |

### 实测建议（需 API，后续阶段）

如果分析结论支持 D，建议：
- 用 NB2 模型跑 10 shots × 3 variants = 30 张图
- 盲测评分（PM + Founder 不知道 A/B'/D 归属）
- 评分维度：角色一致性(1-5) + 构图质量(1-5) + 风格一致性(1-5)
- API 费用 ~$2.80
