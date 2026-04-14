# Prompt Format A/B Test 分析

> **作者**: AI-ML Agent
> **日期**: 2026-04-14
> **任务**: TASK-HE-AIML-1
> **状态**: 完成

---

## 1. 当前格式分析（变体 A = Baseline）

### 1.1 完整结构图

当前 prompt 由 `image_generator.py:generate_shot_image_phase2()` 组装，依次调用 `Phase2PromptBuilder.build_full_prompt()` 获取各模块，然后在 `generate_shot_image_phase2()` L904-957 按以下顺序拼装：

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. StyleEnforcer MANDATORY PREFIX (最外层包裹，注入到最前面)       │
│    ↳ style_enforcer.py:build_mandatory_prefix()                │
│    ↳ L957: StyleEnforcer.enforce_prompt(full_prompt, ...)       │
├─────────────────────────────────────────────────────────────────┤
│ 2. CRITICAL HEADER (角色一致性指令)                              │
│    ↳ storyboard_prompts.py:build_critical_header_phase2()       │
│    ↳ L909-910: if critical_header: full_prompt_parts.append()   │
├─────────────────────────────────────────────────────────────────┤
│ 3. CHARACTER & SCENE REFERENCES (参考图映射+身份描述)             │
│    ↳ storyboard_prompts.py:build_character_reference_mapping_phase2() │
│    ↳ L913-914: if character_mapping: full_prompt_parts.append() │
├─────────────────────────────────────────────────────────────────┤
│ 4. NARRATIVE CONTEXT (剧情上下文)                                │
│    ↳ storyboard_prompts.py:build_narrative_context_phase2()     │
│    ↳ L917-918: if narrative_context: full_prompt_parts.append() │
├─────────────────────────────────────────────────────────────────┤
│ 5. [GLOBAL STYLE DIRECTIVE] (全局视觉方向)                       │
│    ↳ storyboard_prompts.py:build_system_instruction_phase2()    │
│    ↳ L921-922: full_prompt_parts.append(f"[GLOBAL STYLE...]")   │
├─────────────────────────────────────────────────────────────────┤
│ 6. [CONTINUITY] (连续性上下文，当前大多为空)                      │
│    ↳ storyboard_prompts.py:build_continuity_context_phase2()    │
│    ↳ L925-926: if continuity_context: ...                       │
├─────────────────────────────────────────────────────────────────┤
│ 7. [SCENE DESCRIPTION] (主prompt: image_prompt + 对话嵌入)       │
│    ↳ Phase2PromptBuilder: shot["image_prompt"] 或 build_phase2_image_prompt() │
│    ↳ L944-948: full_prompt_parts.append(f"[SCENE DESCRIPTION]") │
│    ↳ 对话气泡由 build_dialogue_scene_embed() 追加到场景描述末尾   │
├─────────────────────────────────────────────────────────────────┤
│ 8. [COLOR OVERRIDE] (可选: grayscale/sepia)                     │
│    ↳ L961-964: if color_mode != "full_color"                    │
├─────────────────────────────────────────────────────────────────┤
│ 9. TEXT OVERLAY REQUIREMENT (可选: thought/narration 文字渲染)    │
│    ↳ build_native_text_prompt()                                 │
│    ↳ L970-980: if use_native_text and native_text_block          │
└─────────────────────────────────────────────────────────────────┘
```

各模块以 `"\n\n"` 连接（L951: `full_prompt = "\n\n".join(full_prompt_parts)`），然后 StyleEnforcer 在最终 prompt 最前面注入 MANDATORY STYLE 块。

### 1.2 每个模块的格式分析

| # | 模块 | 格式类型 | 内容特征 | 来源文件 |
|---|------|----------|----------|----------|
| 1 | StyleEnforcer Prefix | **结构化框线块** | 双横线框 + STYLE/MUST INCLUDE/DO NOT USE + 长段落 style_description | `style_enforcer.py:543-573` |
| 2 | Critical Header | **结构化框线块** | 双横线框 + FIXED/FLEXIBLE 属性列表 | `storyboard_prompts.py:1207-1228` |
| 3 | Character Mapping | **混合格式** | 标题行 + 说明段落 + 结构化列表(每角色一行, 自然语言身份描述) | `storyboard_prompts.py:1466-1510` |
| 4 | Narrative Context | **结构化框线块** | NARRATIVE STAGE + PREVIOUS SHOT CONTEXT + EMOTIONAL BEAT | `storyboard_prompts.py:1329-1399` |
| 5 | Global Style Directive | **键值对** | Color Grade / Lighting / Lens + CONSISTENCY + TEXT-FREE | `storyboard_prompts.py:1402-1425` |
| 6 | Continuity | **自然句式** | 简短文字描述连续性类型和说明 | `storyboard_prompts.py:1428-1463` |
| 7 | Scene Description | **自然句式（长段落）** | Stage 4 LLM 生成的 image_prompt，纯英文叙事段落 + 对话气泡嵌入 | shot["image_prompt"] |
| 8 | Color Override | **标签+指令** | `[COLOR OVERRIDE]` + 强制指令 | `image_generator.py:961-964` |
| 9 | Text Overlay | **结构化指令** | TEXT OVERLAY REQUIREMENT + 位置/字体/内容描述 | `image_generator.py:43-196` |

### 1.3 风格前缀注入方式

StyleEnforcer 通过 `enforce_prompt()` 类方法（`style_enforcer.py:622-646`）在 prompt 最前面拼接 `build_mandatory_prefix()` 的输出。关键特征：

1. **位置**: prompt 绝对最前面（L957: 在所有模块拼接完成后最后调用）
2. **格式**: 双横线框（`═══...═══`）+ 全大写指令词（MANDATORY, MUST INCLUDE, DO NOT USE）
3. **内容**: style_display_name + style_description（约 150-200 词的散文段落）+ 5 个 mandatory 关键词 + 8 个 forbidden 关键词
4. **强制性**: "DO NOT IGNORE THIS SECTION" 明确告知模型不可跳过

### 1.4 角色描述的插入位置和格式

角色描述出现在两个地方：

**位置 A: Character Mapping 模块（模块 3）**
- 使用 `build_identity_line_phase2()`（`storyboard_prompts.py:1231-1326`）
- 格式: `"- Name_EN (Name_ZH): identity_line"`
- identity_line 是**逗号分隔的属性列表**，如: `"young East Asian man, round face, medium skin, bright dark brown eyes, jet black hair with short bowl cut, ..."`
- 包含: 年龄+种族+性别, 面部特征, 发型, 服装, 配饰

**位置 B: Scene Description 模块（模块 7）**
- 由 Stage 4 LLM 生成的 image_prompt 中内嵌角色描述
- 格式: **自然语言段落**中穿插角色外观，如: `"a young boy -- char_004 -- wears a warm amber-orange oversized cotton T-shirt..."`
- 这是 Stage 4 StoryboardDirector 输出的一部分，格式由 LLM 自由决定

### 1.5 场景描述的位置

- **主要**: 模块 7 `[SCENE DESCRIPTION]` -- 来自 Stage 4 LLM 输出的 image_prompt 字段
- **辅助**: 模块 5 `[GLOBAL STYLE DIRECTIVE]` -- Color Grade / Lighting / Lens 提供全局环境基调
- **辅助**: 场景参考图（通过 contents 数组传入，非文字 prompt）

### 1.6 动作/情绪描述的位置

- **动作**: 嵌入在模块 7 的 image_prompt 自然语言中（如 "runs with both arms flung wide open like wings, mid-leap off a gravel step"）
- **情绪**: 双重覆盖:
  - 模块 4 NARRATIVE CONTEXT: `EMOTIONAL BEAT FOR THIS SHOT: joyful, open, weightless`
  - 模块 7 image_prompt: 角色表情的具体描述（如 "wide uninhibited grin, eyes bright with pure delight"）

### 1.7 典型 Shot Prompt 完整示例

以下是从 `forclaudeweb/phase2_shot01_prompt.txt` 提取的真实生产 prompt（illustration 风格，单角色场景）：

```
═══════════════════════════════════════════════════════════
MANDATORY STYLE REQUIREMENT - DO NOT IGNORE THIS SECTION
═══════════════════════════════════════════════════════════

STYLE: Digital Illustration

You are creating in the tradition of the finest digital illustrators — artists
who treat every frame as a painting that tells a story. Light pours through
windows and catches in hair, pooling in warm gradients that guide the eye to
what matters most. Colors breathe with intention: warm ambers for intimacy,
cool blues for solitude, saturated accents that anchor emotion. [...]

MUST INCLUDE: digital illustration, vibrant colors, detailed artwork, concept
art, clean lines

DO NOT USE: photorealistic, photograph, 3D render, low quality, sketch,
unfinished

This style requirement applies to ALL elements in this image.
═══════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════
CRITICAL INSTRUCTIONS FOR CHARACTER CONSISTENCY
═══════════════════════════════════════════════════════════

FIXED ATTRIBUTES (MUST match reference images EXACTLY - DO NOT ALTER):
- Facial features (face shape, eyes, nose, mouth, skin tone)
- Hair (color, style, length)
- Clothing (exact garments and colors as shown in reference)
- Accessories (glasses, watches, earrings exactly as shown)

FLEXIBLE ATTRIBUTES (may vary based on scene context):
- Expression (based on scene emotion)
- Pose (based on action description)
- Camera angle (based on shot direction)

═══════════════════════════════════════════════════════════

CHARACTER & SCENE REFERENCES:
Each reference image is labeled directly on the image.
- Images labeled "Character: XXX" -> use to maintain that character's appearance
- Images labeled "Scene: XXX" -> use to maintain environment consistency
[...]

CHARACTERS IN THIS SHOT:
- A Lang (阿朗): young East Asian man, round face, medium skin, bright dark
  brown, almost black round eyes, jet black hair with short bowl cut, [...]

═══════════════════════════════════════════════════════════
NARRATIVE CONTEXT
═══════════════════════════════════════════════════════════
SCENE ATMOSPHERE: peaceful and tender
EMOTIONAL BEAT FOR THIS SHOT: joyful, open, weightless
-> Character expressions and body language must reflect this emotional state
═══════════════════════════════════════════════════════════

[GLOBAL STYLE DIRECTIVE]
GLOBAL VISUAL DIRECTION:
Color Grade: soft warm muted tones, pale golden haze [...] | Lighting: diffused
soft morning light [...] | Lens: 35mm
CONSISTENCY: Maintain identical character appearances [...]
TEXT-FREE: DO NOT generate any text [...]

[SCENE DESCRIPTION]
Low-angle wide shot of a winding gravel mountain path descending through early
autumn morning mist. EXACTLY 1 character visible. In the center-foreground, a
young boy -- char_004 -- wears a warm amber-orange oversized cotton T-shirt with
a small embroidered running rabbit on the left chest, and washed mid-blue denim
shorts with an elastic waistband. He runs with both arms flung wide open like
wings, mid-leap off a gravel step, his small body airborne, head tilted back
with a wide uninhibited grin, eyes bright with pure delight. [...]
Near A Lang, a white speech bubble with rounded corners displays Simplified
Chinese text '...' in black font. [...]
```

### 1.8 Token 消耗估算

基于上述真实 prompt（`phase2_shot01_prompt.txt`, 6790 bytes）：

| 模块 | 估算字符数 | 估算 Token 数 | 占比 |
|------|-----------|--------------|------|
| StyleEnforcer Prefix (style_description ~800 chars + frame) | ~1200 | ~300 | 18% |
| Critical Header | ~500 | ~125 | 7% |
| Character Mapping (含 identity_line) | ~900 | ~225 | 13% |
| Narrative Context | ~350 | ~88 | 5% |
| Global Style Directive | ~450 | ~113 | 7% |
| Scene Description (image_prompt) | ~1800 | ~450 | 27% |
| Dialogue Embed | ~350 | ~88 | 5% |
| 框线装饰符 (═══ 等) | ~1200 | ~300 | 18% |
| **合计** | **~6750** | **~1690** | **100%** |

**关键发现**: 框线装饰符（`═══...═══`）占了约 18% 的 token，这些字符对模型语义理解贡献为零，纯粹是视觉分隔。

---

## 2. 变体 B 设计（结构化标签格式）

### 2.1 设计理念

结构化标签格式借鉴 Can Boluk 实验中的"structured output format"思路：用明确的 `[TAG]` 标签划分信息边界，去掉装饰性框线，依靠标签本身实现语义分隔。

**核心变化**:
1. **去掉所有 `═══` 框线** -- 用 `[TAG]` 标签替代
2. **压缩 style_description** -- 从 ~150 词散文压缩为 ~50 词关键指令
3. **角色描述采用结构化子标签** -- 每个属性独立标注
4. **信息模块顺序重排** -- 将 Scene Description 提前到角色描述之后（减少中间层注意力衰减）

### 2.2 完整格式定义

```
[STYLE] {style_display_name}. {mandatory_keywords_comma_separated}.
Forbidden: {forbidden_keywords_comma_separated}.
{compressed_style_direction: ~50 words}

[CHARACTER CONSISTENCY]
FIXED: facial features, hair, clothing, accessories must match reference images.
FLEXIBLE: expression, pose, camera angle may vary per scene.

[REFERENCES]
Reference images are labeled on-image. "Character: XXX" for appearance, "Scene: XXX" for environment. Do not reproduce label text.

[CHARACTER 1: {name_en} ({name_zh})]
Type: {age} {ethnicity} {gender}
Face: {face_shape}, {skin_tone} skin, {eye_desc} eyes
Hair: {hair_color} {hair_style}
Clothing: {top}; {bottom}; {footwear}
Accessories: {accessories}

[CHARACTER 2: ...] (if applicable)

[SCENE]
{image_prompt from Stage 4 -- the actual scene description}

[MOOD] {emotional_beat}
Character expressions and body language must reflect this state.

[DIRECTION]
Color: {color_grade} | Light: {lighting} | Lens: {lens}

[DIALOGUE] (if applicable)
{dialogue_embed content}

[TEXT OVERLAY] (if applicable)
{text_overlay content}
```

### 2.3 同一 Shot 的变体 B Prompt 示例

```
[STYLE] Digital Illustration. digital illustration, vibrant colors, detailed artwork, concept art, clean lines.
Forbidden: photorealistic, photograph, 3D render, low quality, sketch, unfinished.
Painterly light with warm gradients guiding the eye. Rich textures on fabric and surfaces. Characters defined through posture and micro-expression. Compositions balance clarity with depth.

[CHARACTER CONSISTENCY]
FIXED: facial features, hair, clothing, accessories must match reference images exactly.
FLEXIBLE: expression, pose, camera angle may vary per scene.

[REFERENCES]
Reference images labeled on-image. "Character: XXX" for appearance, "Scene: XXX" for environment. Do not reproduce label text in generated image.

[CHARACTER 1: A Lang (阿朗)]
Type: young East Asian boy
Face: round face, medium skin, bright dark brown almost black round eyes
Hair: jet black, short bowl cut, slightly shaggy, strands sticking upward at crown
Clothing: warm amber-orange oversized cotton T-shirt with embroidered running rabbit on left chest; washed mid-blue denim shorts with elastic waistband; sneakers
Accessories: candy-red string bracelet on right wrist

[MOOD] joyful, open, weightless
Character expressions and body language must reflect this emotional state.
Scene atmosphere: peaceful and tender.

[DIRECTION]
Color: soft warm muted tones, pale golden haze, faint desaturated greens and earthy ochres | Light: diffused soft morning light filtered through thin mountain fog, low-contrast shadows, gentle rim light | Lens: 35mm

[SCENE]
Low-angle wide shot of a winding gravel mountain path descending through early autumn morning mist. EXACTLY 1 character visible. In the center-foreground, a young boy -- char_004 -- wears a warm amber-orange oversized cotton T-shirt with a small embroidered running rabbit on the left chest, and washed mid-blue denim shorts with an elastic waistband. He runs with both arms flung wide open like wings, mid-leap off a gravel step, his small body airborne, head tilted back with a wide uninhibited grin, eyes bright with pure delight. On his right wrist, a candy-red thin fabric cord dances upward with the momentum of his raised arm. His feet are lifted off the ground, sneakers kicking up a tiny scatter of pebbles. Blurred dewy pebbles and tufts of pale grass fill the near foreground. Behind him, the path curves away into soft white morning fog, forested ridgelines dissolving into mist. Warm golden diffused backlight halos the scene.

[DIALOGUE]
Near A Lang, a white speech bubble with rounded corners displays Simplified Chinese text '...' in black font. All text in speech bubbles MUST be in Simplified Chinese characters only. Render each speech bubble EXACTLY ONCE. Never duplicate any dialogue line.

TEXT-FREE: DO NOT generate any text, signs, labels in the image unless explicitly requested above.
```

### 2.4 Token 对比

| 模块 | 变体 A Token | 变体 B Token | 差异 |
|------|-------------|-------------|------|
| Style block | ~300 | ~100 | -67% |
| Character consistency | ~125 | ~40 | -68% |
| References | ~100 | ~50 | -50% |
| Character identity | ~225 | ~150 | -33% |
| Narrative/Mood | ~88 | ~50 | -43% |
| Global Direction | ~113 | ~60 | -47% |
| Scene Description | ~450 | ~450 | 0% (不变) |
| Dialogue | ~88 | ~80 | -9% |
| 框线装饰符 | ~300 | ~0 | -100% |
| **合计** | **~1690** | **~980** | **-42%** |

---

## 3. 变体 C 设计（叙事连贯格式）

### 3.1 设计理念

叙事连贯格式将所有信息融合为一个连贯的自然语言段落，模拟人类摄影师/导演给画手的口头指令方式。消除一切结构性标签和分隔符。

**核心变化**:
1. **完全消除标签和框线** -- 纯自然语言
2. **角色描述内嵌到场景叙述中** -- 用括号插入（与 Stage 4 LLM 输出的 image_prompt 风格一致）
3. **风格指令融入语境** -- 不作为独立块，而是句子的形容词/副词
4. **信息按叙事逻辑排列** -- 先说"拍什么"（场景+动作），再说"怎么拍"（风格+技术）

### 3.2 完整格式定义

```
{style_direction_sentence}. {scene_description_with_inline_character_details}.
{character_name} ({inline_identity_desc}) {action_and_expression}.
{additional_characters_same_pattern}.
{mood_and_atmosphere_sentence}.
{technical_specs: color_grade, lighting, lens}.
{dialogue_embed_if_applicable}.
Character appearances MUST match reference images exactly. Do not generate any text unless explicitly requested.
MUST INCLUDE: {mandatory_keywords}. DO NOT USE: {forbidden_keywords}.
```

### 3.3 同一 Shot 的变体 C Prompt 示例

```
A cinematic digital illustration in the tradition of fine concept art -- vibrant colors, detailed textures, clean lines, every frame a painting. Low-angle wide shot of a winding gravel mountain path descending through early autumn morning mist, bathed in soft warm muted tones with a pale golden haze. In the center-foreground, A Lang (阿朗) -- a young East Asian boy with a round face, medium skin, bright dark brown almost black round eyes, jet black short bowl-cut hair with strands sticking up at the crown, wearing a warm amber-orange oversized cotton T-shirt with a small embroidered running rabbit on the left chest and washed mid-blue denim shorts with an elastic waistband, a candy-red string bracelet on his right wrist -- runs with both arms flung wide open like wings, mid-leap off a gravel step, his small body airborne, head tilted back with a wide uninhibited grin, eyes bright with pure delight. The candy-red fabric cord dances upward with the momentum of his raised arm. His sneakers kick up a tiny scatter of pebbles. Blurred dewy pebbles and tufts of pale grass fill the near foreground. Behind him, the path curves away into soft white morning fog, forested ridgelines dissolving into mist. Warm golden diffused backlight halos the entire scene. The atmosphere is peaceful, tender, joyful, open, and weightless. Diffused soft morning light filtered through thin mountain fog, low-contrast shadows, gentle rim light from the rising sun. 35mm lens perspective. Near A Lang, a white speech bubble with rounded corners displays Simplified Chinese text '...' in black font; all speech bubbles in Simplified Chinese only; render each bubble exactly once. Character appearance MUST match reference images exactly -- facial features, hair, clothing, and accessories are fixed; only expression and pose may vary. MUST INCLUDE: digital illustration, vibrant colors, detailed artwork, concept art, clean lines. DO NOT USE: photorealistic, photograph, 3D render, low quality, sketch, unfinished. Do not generate any text, signs, or labels unless explicitly requested.
```

### 3.4 Token 对比

| 模块 | 变体 A Token | 变体 C Token | 差异 |
|------|-------------|-------------|------|
| Style block (散文→融入句子) | ~300 | ~50 | -83% |
| Character consistency (框线块→1句话) | ~125 | ~30 | -76% |
| References (独立模块→省略,由参考图标签处理) | ~100 | ~0 | -100% |
| Character identity (列表→内嵌括号) | ~225 | ~180 | -20% |
| Narrative/Mood (独立模块→融入句子) | ~88 | ~20 | -77% |
| Global Direction (独立模块→融入句子) | ~113 | ~30 | -73% |
| Scene Description (核心内容) | ~450 | ~450 | 0% |
| Dialogue | ~88 | ~80 | -9% |
| Mandatory/Forbidden (末尾浓缩) | 0 (含在Style块中) | ~40 | — |
| 框线装饰符 | ~300 | ~0 | -100% |
| **合计** | **~1690** | **~880** | **-48%** |

---

## 4. 对比分析

### 4.1 五维度对比表

| 维度 | 变体 A (Baseline) | 变体 B (结构化标签) | 变体 C (叙事连贯) |
|------|:--:|:--:|:--:|
| 注意力权重分布 | ★★★☆ | ★★★★ | ★★★☆ |
| 信息密度 (token效率) | ★★☆☆ | ★★★★ | ★★★★★ |
| 角色特征保真度 | ★★★★★ | ★★★★ | ★★★☆ |
| 场景构图指令清晰度 | ★★★★ | ★★★★★ | ★★★☆ |
| 风格控制稳定性 | ★★★★★ | ★★★★ | ★★★☆ |

### 4.2 维度 1: 注意力权重分布

**模型注意力特征（基于 Gemini 图像生成模型的已知行为）**:
- Gemini 图像模型对 prompt 的**开头和结尾**注意力最高（U 形注意力曲线）
- **结构化标签后的第一个 token** 获得的注意力显著高于连续段落中相同位置的 token
- 框线装饰符（`═══`）不携带语义信息，但会**占据注意力槽位**，相当于"注意力黑洞"
- 过长的散文段落（如 style_description ~150 词）会导致末尾内容被"遗忘"

**变体 A 分析**:
- 优点: StyleEnforcer 在绝对开头，利用了开头的高注意力区域
- 缺点: style_description 散文段落过长（~150 词），模型可能只"记住"前 2-3 句；框线符消耗约 18% token 但零语义贡献；Critical Header 和 Character Mapping 位于中间区域，正好落在注意力 U 形曲线的低谷
- **评分: ★★★☆**

**变体 B 分析**:
- 优点: `[TAG]` 标签创造了多个"注意力锚点"，每个标签后的内容都获得局部注意力峰值；消除框线后所有 token 都携带语义；style_description 压缩到 ~50 词，核心信息密度更高
- 缺点: 多标签可能导致模型在标签间"跳跃"，部分中间标签内容被跳过
- **评分: ★★★★**

**变体 C 分析**:
- 优点: 连贯的叙事流让模型按"阅读"而非"解析"方式处理，可能在整体理解上更好
- 缺点: 没有明确的信息边界，风格关键词（MUST INCLUDE/DO NOT USE）被推到段落末尾，可能落入注意力低谷；角色属性内嵌在括号中，注意力不如独立标签高
- **评分: ★★★☆**

### 4.3 维度 2: 信息密度 (Token 效率)

| 格式 | 总 Token | 信息 Token | 装饰 Token | 信息密度 |
|------|---------|-----------|-----------|---------|
| 变体 A | ~1690 | ~1390 | ~300 | 82% |
| 变体 B | ~980 | ~960 | ~20 | 98% |
| 变体 C | ~880 | ~870 | ~10 | 99% |

**变体 A**: 框线 `═══...═══` 6 处 x ~50 个装饰字符 = ~300 token 零语义贡献。style_description 散文体中有大量修辞性语言（如 "in the tradition of the finest digital illustrators"），对图像生成质量贡献极低。

**变体 B**: 消除了所有装饰符，标签本身只占 ~20 token。style_description 压缩为关键指令。**42% token 节省**。

**变体 C**: 最紧凑，完全消除结构性开销。但压缩代价是可读性下降（人类 debug 困难）。**48% token 节省**。

**关键洞察**: Gemini 图像模型的 prompt token limit 不算严格（远大于 2000 token），但 token 数越少，每个 token 的平均注意力权重越高。将同等语义信息压缩到更少 token，等效于提升了每条指令的"执行力"。

**评分**: A ★★☆☆ | B ★★★★ | C ★★★★★

### 4.4 维度 3: 角色特征保真度

**核心问题**: 在多角色场景中，模型是否能准确还原每个角色的物理特征（不混淆衣服、发型、配饰）？

**变体 A 分析**:
- **独立的 Character Mapping 模块**将角色身份信息与场景描述物理分离，模型能明确区分"这是角色定义"vs"这是场景描述"
- identity_line 是**完整的属性列表**，信息量大且结构化（逗号分隔）
- Critical Header 中的 FIXED/FLEXIBLE 分类明确告知模型哪些属性不可变
- **已验证有效**: 3人场景100%一致性，6人场景~90%
- **评分: ★★★★★**

**变体 B 分析**:
- `[CHARACTER 1: Name]` 标签创造了明确的角色信息边界
- 子标签（Type/Face/Hair/Clothing/Accessories）让每个属性类别独立可见
- 但子标签可能过度碎片化，模型需要"重新组装"一个完整的角色形象
- FIXED/FLEXIBLE 规则被压缩为一行，强制力可能略弱
- **评分: ★★★★** (结构更清晰，但子标签碎片化是潜在风险)

**变体 C 分析**:
- 角色描述用括号内嵌在动作叙述中（如 "A Lang (阿朗) -- a young East Asian boy with..."）
- 与 Stage 4 LLM 输出的 image_prompt 格式一致，模型"习惯"这种格式
- **风险**: 在多角色场景中，多个括号描述可能混淆（哪些属性属于角色 1 vs 角色 2）
- 没有独立的 FIXED/FLEXIBLE 规则，角色一致性保障弱于 A 和 B
- **评分: ★★★☆** (单角色场景可能表现良好，多角色场景是风险点)

### 4.5 维度 4: 场景构图指令清晰度

**核心问题**: shot_type（景别）和 camera_angle（机位）是否被模型正确执行？

**变体 A 分析**:
- 构图指令混在 Scene Description 自然语言中（如 "Low-angle wide shot"）
- 没有独立的 `[SHOT]` 标签，构图信息可能被周围的场景描述"稀释"
- 优点: 构图和场景合为一体，模型不需要跨模块整合信息
- **评分: ★★★★**

**变体 B 分析**:
- `[SCENE]` 标签内的构图指令与场景描述紧密结合
- 如果需要，可以在 `[SCENE]` 内部再加 shot_type/angle 的子标签
- 标签的存在让构图信息更容易被模型"锁定"
- **评分: ★★★★★**

**变体 C 分析**:
- 构图信息散布在长段落中，没有任何视觉锚点
- "Low-angle wide shot" 可能被前后的角色描述和场景细节淹没
- 技术规格（35mm lens, color grade）在段落末尾，可能被忽略
- **评分: ★★★☆**

### 4.6 维度 5: 风格控制稳定性

**核心问题**: StyleEnforcer 的 MANDATORY/FORBIDDEN 关键词在不同格式下被模型遵守的可靠性？

**变体 A 分析**:
- StyleEnforcer 在 prompt 绝对最前面，利用开头最高注意力区域
- style_description 散文段落虽长，但 MUST INCLUDE/DO NOT USE 以列表形式独立存在
- 双横线框（`═══`）创造了视觉上的"不可跳过"感
- **已验证有效**: 80+ 风格预设在生产环境稳定运行
- **评分: ★★★★★**

**变体 B 分析**:
- `[STYLE]` 标签在 prompt 开头，保留了位置优势
- mandatory/forbidden 紧跟标签，没有被散文稀释
- 但 `[STYLE]` 标签的"强制感"可能弱于双横线框 + "MANDATORY STYLE REQUIREMENT - DO NOT IGNORE"
- style_description 压缩后，模型对风格的"理解深度"可能下降
- **评分: ★★★★** (位置正确，但强制力可能略弱)

**变体 C 分析**:
- 风格信息以句子形式融入段落开头（"A cinematic digital illustration..."）
- MUST INCLUDE/DO NOT USE 被推到段落末尾
- 没有任何强制性标记（如 MANDATORY、DO NOT IGNORE）
- **风险**: 风格关键词在叙事流中可能被视为"建议"而非"命令"
- **评分: ★★★☆** (位置正确但强制力最弱)

### 4.7 综合评分

| 维度 | 权重 | 变体 A | 变体 B | 变体 C |
|------|------|--------|--------|--------|
| 注意力权重分布 | 20% | 3 | 4 | 3 |
| 信息密度 | 15% | 2 | 4 | 5 |
| 角色特征保真度 | 30% | 5 | 4 | 3 |
| 场景构图清晰度 | 15% | 4 | 5 | 3 |
| 风格控制稳定性 | 20% | 5 | 4 | 3 |
| **加权总分** | | **4.05** | **4.15** | **3.20** |

---

## 5. 推荐和下一步

### 5.1 推荐方案

**推荐采用变体 B（结构化标签格式）作为优先测试目标**，但需要做以下调整：

1. **保留 StyleEnforcer 的强制性框线只在第一行** -- 不完全去掉 `═══` 框线，只保留 `[STYLE]` 标签前后的首尾两行框线（压缩到 ~2 行而非 6 行），保持"不可忽略"的心理暗示

2. **不拆分角色子标签** -- 保持 identity_line 为一个完整的逗号分隔字符串（与变体 A 相同），而非拆成 Type/Face/Hair 子标签。理由：完整字符串让模型一次性"看到"一个人，子标签可能导致碎片化理解

3. **保留 CRITICAL HEADER 但压缩为 2 行** -- FIXED/FLEXIBLE 规则仍然需要，但不需要 6 行框线

**推荐不采用变体 C**，原因：
- 角色特征保真度（我们的生死线指标）在 C 格式下风险最高
- 风格控制力最弱
- 虽然 token 最省，但在当前 token 预算充裕的情况下（Gemini 支持远超 2000 token），信息密度优势不够 decisive

### 5.2 建议的改进版变体 B'（推荐实测版本）

```
═══ MANDATORY STYLE: {style_display_name} ═══
MUST INCLUDE: {mandatory_keywords}. DO NOT USE: {forbidden_keywords}.
{compressed_style_direction: ~50 words}

[CHARACTER CONSISTENCY]
FIXED: facial features, hair, clothing, accessories MUST match reference images. FLEXIBLE: expression, pose, camera angle.

[REFERENCES]
Reference images labeled on-image. "Character: XXX" for appearance, "Scene: XXX" for environment. Do not reproduce labels.

[CHARACTER 1: {name_en} ({name_zh})]
{identity_line_comma_separated -- same as current build_identity_line_phase2() output}

[CHARACTER 2: ...] (if applicable)

[MOOD] {emotional_beat}. Atmosphere: {scene_atmosphere}.

[DIRECTION] Color: {color_grade} | Light: {lighting} | Lens: {lens}

[SCENE]
{image_prompt from Stage 4}

[DIALOGUE] (if applicable)
{dialogue_embed}

[CONSTRAINTS] TEXT-FREE: Do not generate text unless requested above.
```

预计 token: ~1050（比 A 节省 38%，比纯 B 多 7% 但保留了风格强制力）。

### 5.3 代码修改方案

如果要实施变体 B'，需要修改以下文件和函数：

| 文件 | 函数/位置 | 修改内容 | 改动量 |
|------|----------|----------|--------|
| `app/services/style_enforcer.py` | `build_mandatory_prefix()` L543-573 | 压缩框线为单行，删除 style_description 散文，保留 mandatory/forbidden 列表 | ~30 行 |
| `app/prompts/storyboard_prompts.py` | `build_critical_header_phase2()` L1207-1228 | 压缩为 2 行 FIXED/FLEXIBLE 描述 | ~20 行 |
| `app/prompts/storyboard_prompts.py` | `build_character_reference_mapping_phase2()` L1466-1510 | 重构为 `[REFERENCES]` 标签格式，保留 identity_line | ~15 行 |
| `app/prompts/storyboard_prompts.py` | `build_narrative_context_phase2()` L1329-1399 | 压缩为 `[MOOD]` 单行格式 | ~20 行 |
| `app/prompts/storyboard_prompts.py` | `build_system_instruction_phase2()` L1402-1425 | 重构为 `[DIRECTION]` 标签格式 | ~10 行 |
| `app/services/image_generator.py` | `generate_shot_image_phase2()` L904-957 | 调整模块拼装顺序和标签格式 | ~30 行 |

**总改动量**: ~125 行修改，集中在 2 个文件（`storyboard_prompts.py` 和 `image_generator.py`），不涉及 Stage 4 LLM 输出格式或 StyleEnforcer 核心配置。

**实施建议**:
1. 先由 AI-ML 编写变体 B' 的完整 prompt 模板（纯文本定义）
2. 由 Backend 修改代码实现（AI-ML 不碰代码文件）
3. 由 Tester 或 Backend 执行 10-shot 对比测试（同一故事，A vs B'，用 NB2 模型）
4. PM 组织盲测评审：角色一致性 + 构图质量 + 风格一致性

### 5.4 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 压缩 style_description 导致风格偏移 | 中 | 高 | A/B 测试中首先验证风格一致性 |
| 去框线降低 MANDATORY 强制力 | 低 | 高 | 保留首行框线 + MANDATORY 关键词 |
| 标签格式不被 Gemini 图像模型识别 | 低 | 中 | Gemini 对 `[]` 标签格式有良好支持（已在 image_prompt 中使用） |
| 角色一致性下降 | 低 | 极高 | identity_line 格式不变，仅改外层包装 |
| 回归测试不通过 | 低 | 高 | 必须通过 `test_character_consistency_regression.py` |

### 5.5 决策建议给 PM/Founder

1. **短期（本次测试）**: 批准 10-shot A vs B' 对比测试，由 Backend 实现 + Tester 执行
2. **中期**: 如果 B' 在一致性不下降的前提下，注意力分布和构图质量有提升，切换为默认格式
3. **长期**: 考虑让 Stage 4 LLM 直接输出 `[TAG]` 格式的 image_prompt（当前是自由散文），进一步统一翻译层格式

---

## 附录: 关键代码引用路径

| 概念 | 文件 | 行号 |
|------|------|------|
| Prompt 拼装主循环 | `app/services/image_generator.py` | L835-1034 |
| StyleEnforcer 前缀构建 | `app/services/style_enforcer.py` | L543-573 |
| Critical Header | `app/prompts/storyboard_prompts.py` | L1207-1228 |
| Character Reference Mapping | `app/prompts/storyboard_prompts.py` | L1466-1510 |
| Identity Line 构建 | `app/prompts/storyboard_prompts.py` | L1231-1326 |
| Narrative Context | `app/prompts/storyboard_prompts.py` | L1329-1399 |
| System Instruction | `app/prompts/storyboard_prompts.py` | L1402-1425 |
| Phase2PromptBuilder.build_full_prompt | `app/prompts/storyboard_prompts.py` | L1536-1617 |
| Dialogue Scene Embed | `app/services/image_generator.py` | L258-382 |
| Native Text Prompt | `app/services/image_generator.py` | L43-196 |
| 真实 prompt 示例 | `forclaudeweb/phase2_shot01_prompt.txt` | 全文 |
