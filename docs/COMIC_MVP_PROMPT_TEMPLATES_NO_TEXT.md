# 条漫MVP Prompt模板 - 无文字版本

> **目标模型**: `gemini-2.5-flash-image`
> **作者**: @AI-ML
> **日期**: 2026-01-22
> **最后更新**: 2026-01-23 (TASK-FIX-001)
> **关联任务**: HANDOFF-2026-01-22-006 / TASK-001, HANDOFF-2026-01-23-001 / TASK-FIX-001
> **用途**: 配合 TextOverlayService 后处理叠加文字

---

## 重要说明

这是专门用于「后处理叠加文字」方案的Prompt模板。

**与原模板的区别**：
- 原模板 (`COMIC_MVP_PROMPT_TEMPLATES.md`)：生成带文字的图片
- 本模板：生成**无文字**的图片，由 TextOverlayService 后期叠加中文

**为什么需要无文字版本**：
1. Gemini Flash 模型无法正确渲染中文（显示为乱码）
2. 后处理叠加文字需要原图不含任何文字
3. 保留原模板用于未来 Pro 模型测试

---

## 核心指令块（所有模板必须包含）

**v2.0 修复版** - 解决图片留白和百分比文字泄露问题

```
TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy

FULL CANVAS COMPOSITION:
- Fill the ENTIRE image canvas edge-to-edge with meaningful visual content
- NO black borders, NO white margins, NO blank areas at ANY edge
- Extend backgrounds, scenery, and visual elements to ALL four edges
- The composition must touch all four sides of the frame without any padding
- DO NOT create reserved spaces, margins, or borders of any color
- These are internal instructions - DO NOT render them as visible text in the image
```

---

## 模板1: 对话场景（无气泡）

### 原模板功能
生成带白色对话气泡的图片

### 无文字版本
仅生成人物对话场景，不生成气泡

### Prompt模板

```
{scene_description}

CHARACTER EXPRESSION FOCUS:
The character {speaker_name} is speaking with {expression_description}.
Focus on capturing the emotional nuance in their face and body language.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy

FULL CANVAS COMPOSITION:
- Fill the ENTIRE image canvas edge-to-edge with meaningful visual content
- NO black borders, NO white margins, NO blank areas at ANY edge
- Extend backgrounds and scenery to ALL four edges of the frame
- The composition must touch all four sides without any padding
- Character faces and expressions must be clearly visible
- These are internal instructions - DO NOT render them as visible text in the image
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `{scene_description}` | 场景和角色描述 | "A young woman sitting at a cafe table, looking at a man across from her" |
| `{speaker_name}` | 说话者 | "the woman" |
| `{expression_description}` | 表情描述 | "apologetic expression, lowered gaze, slightly bowed head" |

### 使用示例

```
A young man in gray sweater standing in a modern living room, facing a woman.
He is speaking with an apologetic expression, lowered gaze, bowed head slightly, softened eyes showing remorse.

CHARACTER EXPRESSION FOCUS:
The character the man is speaking with apologetic, contrite expression.
Focus on capturing the emotional nuance in their face and body language.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy

FULL CANVAS COMPOSITION:
- Fill the ENTIRE image canvas edge-to-edge with meaningful visual content
- NO black borders, NO white margins, NO blank areas at ANY edge
- Extend backgrounds and scenery to ALL four edges of the frame
- The composition must touch all four sides without any padding
- Character faces and expressions must be clearly visible
- These are internal instructions - DO NOT render them as visible text in the image
```

---

## 模板2: 心理旁白场景（无黑底文字条）

### 原模板功能
生成带半透明黑色旁白条的图片

### 无文字版本
仅生成人物心理活动场景，不生成旁白条

### Prompt模板

```
{scene_description}

EMOTIONAL ATMOSPHERE:
The scene conveys {emotional_tone}.
Character shows {expression_description} reflecting inner thoughts.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas (no black bars, no text overlays)
- Written signs, labels, or watermarks
- Any form of typography or calligraphy

FULL CANVAS COMPOSITION:
- Fill the ENTIRE image canvas edge-to-edge with meaningful visual content
- NO black borders, NO white margins, NO blank areas at ANY edge
- DO NOT create black bars, margins, or reserved spaces of any color
- Extend the scene environment to ALL four edges of the frame
- The composition must touch all four sides without any padding
- Character's key expressions must remain clearly visible
- These are internal instructions - DO NOT render them as visible text in the image
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `{scene_description}` | 场景描述 | "A woman looking out the window with sad eyes" |
| `{emotional_tone}` | 情绪氛围 | "melancholic contemplation", "inner turmoil" |
| `{expression_description}` | 表情描述 | "pensive eyes, slightly furrowed brows, distant gaze" |

### 使用示例 - 顶部旁白场景

```
A young woman in casual clothes standing by a large window in an apartment, gazing outside at the city skyline. Evening light casting warm shadows.

EMOTIONAL ATMOSPHERE:
The scene conveys melancholic contemplation and quiet sadness.
Character shows pensive expression with glistening eyes, brows slightly drawn together, reflecting hurt and disappointment.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas (no black bars, no text overlays)
- Written signs, labels, or watermarks
- Any form of typography or calligraphy

FULL CANVAS COMPOSITION:
- Fill the ENTIRE image canvas edge-to-edge with meaningful visual content
- NO black borders, NO white margins, NO blank areas at ANY edge
- DO NOT create black bars, margins, or reserved spaces of any color
- Extend the scene environment to ALL four edges of the frame
- The composition must touch all four sides without any padding
- Character's key expressions must remain clearly visible
- These are internal instructions - DO NOT render them as visible text in the image
```

### 使用示例 - 底部旁白场景

```
A man sitting alone on a park bench at dusk, head slightly bowed, hands clasped together.

EMOTIONAL ATMOSPHERE:
The scene conveys quiet reflection and acceptance.
Character shows relieved yet bittersweet expression, soft eyes, relaxed shoulders.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas (no black bars, no text overlays)
- Written signs, labels, or watermarks
- Any form of typography or calligraphy

FULL CANVAS COMPOSITION:
- Fill the ENTIRE image canvas edge-to-edge with meaningful visual content
- NO black borders, NO white margins, NO blank areas at ANY edge
- DO NOT create black bars, margins, or reserved spaces of any color
- Extend the scene environment to ALL four edges of the frame
- The composition must touch all four sides without any padding
- Character's key expressions must remain clearly visible
- These are internal instructions - DO NOT render them as visible text in the image
```

---

## 模板3: 叙事旁白场景（无白底文字条）

### 原模板功能
生成带半透明白色旁白条的图片

### 无文字版本
仅生成叙事场景，不生成旁白条

### Prompt模板

```
{scene_description}

NARRATIVE MOMENT:
This scene establishes {narrative_context}.
Visual focus on {visual_focus_description}.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas (no white bars, no text overlays)
- Written signs, labels, or watermarks
- Any form of typography or calligraphy

FULL CANVAS COMPOSITION:
- Fill the ENTIRE image canvas edge-to-edge with meaningful visual content
- NO black borders, NO white margins, NO blank areas at ANY edge
- DO NOT create white bars, margins, or reserved spaces of any color
- Extend backgrounds, sky, and scenery to ALL four edges of the frame
- The composition must touch all four sides without any padding
- Key visual elements and character faces must be clearly visible
- These are internal instructions - DO NOT render them as visible text in the image
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `{scene_description}` | 场景描述 | "City skyline at sunset, warm golden light" |
| `{narrative_context}` | 叙事背景 | "time passage", "new beginning", "resolution" |
| `{visual_focus_description}` | 视觉焦点 | "the couple walking together", "the character's hopeful expression" |

### 使用示例

```
A couple walking hand in hand along a riverside path at sunset. Cherry blossoms falling gently around them. Warm golden light bathing the scene.

NARRATIVE MOMENT:
This scene establishes a hopeful new beginning after reconciliation.
Visual focus on the couple's peaceful body language and the romantic atmosphere.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas (no white bars, no text overlays)
- Written signs, labels, or watermarks
- Any form of typography or calligraphy

FULL CANVAS COMPOSITION:
- Fill the ENTIRE image canvas edge-to-edge with meaningful visual content
- NO black borders, NO white margins, NO blank areas at ANY edge
- DO NOT create white bars, margins, or reserved spaces of any color
- Extend backgrounds, sky, and scenery to ALL four edges of the frame
- The composition must touch all four sides without any padding
- Key visual elements and character faces must be clearly visible
- These are internal instructions - DO NOT render them as visible text in the image
```

---

## 模板4: 分屏效果（无中央文字）

### 原模板功能
生成带分割线和中央旁白的分屏图片

### 无文字版本
仅生成分屏效果，不生成文字

### Prompt模板

```
SPLIT SCREEN COMPOSITION - NO TEXT:

LEFT HALF: {left_scene_description}
The left character shows {left_expression} expression.

RIGHT HALF: {right_scene_description}
The right character shows {right_expression} expression.

VISUAL STYLE:
- Clear vertical division down the center of the image
- {division_style}
- Both halves should have similar lighting style for visual coherence
- Contrast in content/emotion between two sides

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy
- NO text on or near the center dividing line

FULL CANVAS COMPOSITION:
- Fill BOTH halves of the image completely edge-to-edge with visual content
- NO black borders, NO white margins, NO blank areas at ANY edge
- Extend scenes to ALL four edges on both sides
- The composition must touch all four sides without any padding
- Character faces on both sides must be clearly visible
- Keep the vertical division line clean and prominent
- These are internal instructions - DO NOT render them as visible text in the image
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `{left_scene_description}` | 左侧场景 | "A man in office, looking stressed" |
| `{right_scene_description}` | 右侧场景 | "The same man years ago, smiling and carefree" |
| `{left_expression}` | 左侧表情 | "frustrated, tense" |
| `{right_expression}` | 右侧表情 | "happy, relaxed" |
| `{division_style}` | 分割线风格 | "Sharp clean line", "Soft gradient", "Torn paper edge" |

### 使用示例

```
SPLIT SCREEN COMPOSITION - NO TEXT:

LEFT HALF: A young woman sitting alone in a dimly lit apartment, hugging her knees on the couch, looking lost and hurt.
The left character shows aggrieved, hurt expression with glistening eyes.

RIGHT HALF: A man standing in the rain outside, looking up at her window with concern, wanting to apologize but hesitating.
The right character shows apologetic, remorseful expression with furrowed brows.

VISUAL STYLE:
- Clear vertical division down the center of the image
- Sharp clean line separating the two scenes, slight color temperature difference (cool left, warm right)
- Both halves should have similar lighting style for visual coherence
- Contrast in content/emotion between two sides showing their separated states

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy
- NO text on or near the center dividing line

FULL CANVAS COMPOSITION:
- Fill BOTH halves of the image completely edge-to-edge with visual content
- NO black borders, NO white margins, NO blank areas at ANY edge
- Extend scenes to ALL four edges on both sides
- The composition must touch all four sides without any padding
- Character faces on both sides must be clearly visible
- Keep the vertical division line clean and prominent
- These are internal instructions - DO NOT render them as visible text in the image
```

---

## 模板5: 回忆碎片效果（无底部旁白）

### 原模板功能
生成带碎片回忆和底部旁白的图片

### 无文字版本
仅生成回忆碎片效果，不生成旁白

### Prompt模板

```
{main_character_description}

MEMORY FRAGMENT EFFECT - NO TEXT:
Surrounding the main character, floating memory fragments showing glimpses of the past.
Fragment shapes: {fragment_style}
Number of visible fragments: {fragment_count}

Fragment contents:
{fragment_1_description}
{fragment_2_description}
{fragment_3_description}

Fragment visual treatment: {fragment_treatment}
The fragments should appear to float in space around the character, creating a dreamlike, nostalgic atmosphere.
Main character remains in sharp focus while fragments have {focus_style}.

Emotional tone: {emotional_tone}

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy
- NO text inside or on the memory fragments

FULL CANVAS COMPOSITION:
- Fill the ENTIRE image canvas edge-to-edge with meaningful visual content
- NO black borders, NO white margins, NO blank areas at ANY edge
- Memory fragments and atmosphere should extend to ALL four edges
- The composition must touch all four sides without any padding
- Main character should be positioned naturally within the composition
- These are internal instructions - DO NOT render them as visible text in the image
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `{main_character_description}` | 主角描述 | "A woman standing alone, eyes closed, hand over heart" |
| `{fragment_style}` | 碎片形状 | "jagged glass shards", "soft-edged photo pieces" |
| `{fragment_count}` | 碎片数量 | "4-5" |
| `{fragment_X_description}` | 碎片内容 | "Fragment 1: A happy couple laughing together" |
| `{fragment_treatment}` | 碎片视觉处理 | "slightly desaturated, soft glow edges" |
| `{focus_style}` | 焦点风格 | "soft blur and slight transparency" |
| `{emotional_tone}` | 情绪基调 | "melancholic nostalgia" |

### 使用示例

```
A young woman in casual dress standing in an empty park at dusk, head slightly bowed, eyes closed, one hand over her heart. Her expression shows deep sadness and longing, tears visible on her cheek.

MEMORY FRAGMENT EFFECT - NO TEXT:
Surrounding the main character, floating memory fragments showing glimpses of the past.
Fragment shapes: jagged glass shards with glowing golden edges
Number of visible fragments: 4-5

Fragment contents:
Fragment 1: A happy couple laughing together at a cafe, holding hands across the table
Fragment 2: Two hands interlinked, one wearing a simple silver ring
Fragment 3: A man's warm smile looking directly at the viewer with love in his eyes
Fragment 4: Two silhouettes walking together on a beach at sunset

Fragment visual treatment: slightly desaturated colors with warm golden glow at edges, ethereal and dreamlike quality
The fragments should appear to float in space around the character, creating a dreamlike, nostalgic atmosphere.
Main character remains in sharp focus while fragments have soft blur and slight transparency.

Emotional tone: melancholic nostalgia, remembering lost love, bittersweet acceptance

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy
- NO text inside or on the memory fragments

FULL CANVAS COMPOSITION:
- Fill the ENTIRE image canvas edge-to-edge with meaningful visual content
- NO black borders, NO white margins, NO blank areas at ANY edge
- Memory fragments and atmosphere should extend to ALL four edges
- The composition must touch all four sides without any padding
- Main character should be positioned naturally within the composition
- These are internal instructions - DO NOT render them as visible text in the image
```

---

## 模板6: 画中画效果（无气泡/旁白）

### 原模板功能
生成带手机屏幕和对话气泡/旁白的图片

### 无文字版本
仅生成画中画效果，不生成文字元素

### Prompt模板

```
{main_scene_description}

PICTURE-IN-PICTURE ELEMENT - NO TEXT:
{device_type} showing: {pip_content_description}

Device details:
- Position: {device_position}
- Size: approximately {device_size} of frame
- Screen content clearly visible and in focus
- {device_specific_details}

The embedded screen should show {pip_content_description} with realistic device frame.
Do NOT include any text, labels, or UI elements on the device screen.

Visual relationship: {relationship_description}

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy
- NO text on the device screen, NO app UI text, NO notification text

FULL CANVAS COMPOSITION:
- Fill the ENTIRE image canvas edge-to-edge with meaningful visual content
- NO black borders, NO white margins, NO blank areas at ANY edge
- Extend backgrounds and environment to ALL four edges of the frame
- The composition must touch all four sides without any padding
- Device screen and holder's expression must both be clearly visible
- These are internal instructions - DO NOT render them as visible text in the image
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `{main_scene_description}` | 主场景描述 | "A person's hands holding a smartphone" |
| `{device_type}` | 设备类型 | "smartphone screen", "laptop screen", "photo frame" |
| `{pip_content_description}` | 画中画内容 | "a selfie photo of a smiling woman at the beach" |
| `{device_position}` | 设备位置 | "center of frame", "lower right" |
| `{device_size}` | 设备占画面比例 | "40%", "30%" |
| `{device_specific_details}` | 设备细节 | "modern smartphone with thin black bezels" |
| `{relationship_description}` | 视觉关系 | "viewer sees both the holder's reaction and the screen content" |

### 使用示例

```
A young man's hands holding a smartphone in a dimly lit room, the phone screen illuminating his face which is partially visible at the top of frame showing a delighted, surprised expression with wide eyes and a growing smile.

PICTURE-IN-PICTURE ELEMENT - NO TEXT:
Smartphone screen showing: a selfie photo of a young woman smiling brightly at the camera, wearing a white sundress, with a beautiful beach sunset in the background. Her expression is warm and inviting.

Device details:
- Position: center of frame, taking up significant visual space
- Size: approximately 45% of frame
- Screen content clearly visible and in focus
- Modern smartphone with thin black bezels, slight screen glow reflecting on holder's face

The embedded screen should show the woman's selfie with realistic device frame and subtle screen reflection.
Do NOT include any text, labels, or UI elements on the device screen.

Visual relationship: viewer sees the photo on screen and can glimpse the man's joyful reaction, creating emotional connection between the two images

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy
- NO text on the device screen, NO app UI text, NO notification text

FULL CANVAS COMPOSITION:
- Fill the ENTIRE image canvas edge-to-edge with meaningful visual content
- NO black borders, NO white margins, NO blank areas at ANY edge
- Extend backgrounds and environment to ALL four edges of the frame
- The composition must touch all four sides without any padding
- Device screen and holder's expression must both be clearly visible
- These are internal instructions - DO NOT render them as visible text in the image
```

---

## 表情细腻度描述词库（无变化）

表情词库与原模板相同，用于 `{expression_description}` 参数。

| 中文表情 | 英文关键词 | 面部细节描述 |
|---------|-----------|-------------|
| **不悦** | displeased, annoyed, irritated | furrowed brows, slightly narrowed eyes, tight-lipped, jaw slightly clenched |
| **委屈** | aggrieved, hurt, wronged | glistening eyes (almost teary), slightly trembling lower lip, brows drawn together and upward |
| **困惑** | confused, puzzled, perplexed | raised eyebrows (one higher than other), tilted head, squinted eyes, slightly open mouth |
| **道歉** | apologetic, remorseful, contrite | lowered gaze, bowed head slightly, softened eyes, pressed lips, humble posture |
| **震惊** | shocked, stunned, astonished | wide eyes, raised eyebrows high, open mouth (jaw dropped), frozen expression |
| **冷漠** | indifferent, aloof, detached | neutral/flat expression, half-lidded eyes, relaxed facial muscles, distant gaze |
| **释然** | relieved, at peace, unburdened | soft gentle smile, relaxed brows, warm eyes, deep exhale implied, tension released |
| **开心** | happy, joyful, delighted | genuine smile reaching eyes (crow's feet), raised cheeks, bright sparkling eyes |

---

## 与StyleEnforcer集成

与原模板相同，推荐使用 `illustration` 风格：

```python
from app.services.style_enforcer import StyleEnforcer

enforcer = StyleEnforcer()
style_config = {"style": "illustration"}

# 应用风格前缀
final_prompt = enforcer.enforce_prompt(your_template_prompt, style_config)
```

---

## 与原模板的对照表

| 原模板 | 本模板 | 主要区别 |
|--------|--------|----------|
| 模板1: 对话气泡 | 模板1: 对话场景（无气泡）| 移除气泡描述，使用FULL CANVAS COMPOSITION |
| 模板2: 心理旁白(黑底) | 模板2: 心理旁白场景（无黑底）| 移除黑条描述，使用FULL CANVAS COMPOSITION |
| 模板3: 叙事旁白(白底) | 模板3: 叙事旁白场景（无白底）| 移除白条描述，使用FULL CANVAS COMPOSITION |
| 模板4: 分屏效果 | 模板4: 分屏效果（无中央文字）| 移除中央文字描述，使用FULL CANVAS COMPOSITION |
| 模板5: 回忆碎片 | 模板5: 回忆碎片效果（无底部旁白）| 移除旁白描述，使用FULL CANVAS COMPOSITION |
| 模板6: 画中画 | 模板6: 画中画效果（无气泡/旁白）| 移除文字描述，使用FULL CANVAS COMPOSITION |

---

## 使用流程

```
1. 使用本模板生成无文字图片
   ↓
2. TextOverlayService 叠加中文文字
   - 对话气泡：add_speech_bubble()
   - 黑底旁白：add_monologue()
   - 白底旁白：add_narrative()
   ↓
3. 输出最终带文字的图片
```

---

## 场景情境约束块（Scene Context Modifiers）

> **用途**: 根据故事情境添加特定约束，控制角色间的互动程度、情感表达强度等
> **使用方式**: 在相关场景的Prompt中添加对应约束块

### 首次约会 (First Date)

在需要表现"初次见面/首次约会"情境的场景中，添加以下约束：

```
INTIMACY LEVEL CONSTRAINT (First Date):
- This is a FIRST DATE scenario - characters have just met
- Maintain appropriate physical distance (arm's length minimum)
- Body language should be warm but reserved, NOT overtly romantic
- Expressions should show curiosity and gentle interest, NOT passion
- NO embracing, NO hand-holding, NO arm linking, NO leaning into each other
- The mood is "getting to know each other" NOT "established couple"
- Physical closeness should be incidental (from walking together), NOT deliberate intimacy
- Subtle nervousness and anticipation are appropriate, NOT comfortable familiarity
```

**适用场景**:
- 相亲场合
- 网友/探探匹配后首次见面
- 偶遇后的第一次约会
- 朋友介绍后的首次单独相处
- 同事首次约定私下聚会

**使用示例**:

```
{scene_description}

INTIMACY LEVEL CONSTRAINT (First Date):
- This is a FIRST DATE scenario - characters have just met
- Maintain appropriate physical distance (arm's length minimum)
- Body language should be warm but reserved, NOT overtly romantic
- NO embracing, NO hand-holding, NO arm linking, NO leaning into each other

{TEXT_FREE_REQUIREMENT}
```

### 热恋期 (Established Couple - Honeymoon Phase)

在需要表现"热恋中的情侣"情境的场景中，添加以下约束：

```
INTIMACY LEVEL CONSTRAINT (Honeymoon Phase):
- This is an ESTABLISHED COUPLE in the honeymoon phase of their relationship
- Natural physical closeness is appropriate - holding hands, arm around shoulder/waist
- Body language should be comfortable and affectionate
- Expressions can show deep affection, love, and happiness
- Comfortable leaning into each other, heads close together
- The mood is "deeply in love and comfortable" NOT "just met"
```

**适用场景**:
- 确认关系后的约会
- 热恋期日常相处
- 情侣旅行场景

### 老友重逢 (Reunion After Long Time)

在需要表现"久别重逢"情境的场景中，添加以下约束：

```
EMOTIONAL CONTEXT (Reunion):
- Characters are meeting again after a long separation
- Initial reaction should show surprise and overwhelming emotion
- Expression progression: shock → recognition → joy/relief
- Physical contact like hugging is natural and emotional, NOT romantic
- Tears of joy are appropriate
- The mood is "finally reunited" with both happiness and bittersweet nostalgia
```

**适用场景**:
- 多年未见的老友重逢
- 亲人团聚
- 战后/灾后重逢

---

## 角色一致性约束块（Character Consistency Modifiers）

> **用途**: 强化角色外貌和服装的一致性，防止AI模型在不同shots中改变角色服装
> **使用方式**: 在每个shot的Prompt末尾（TEXT_FREE_REQUIREMENT之前）添加角色一致性约束

### 通用模板

```
CHARACTER CONSISTENCY REQUIREMENT:
- {character_name}: MUST wear {clothing_description}
- Verify clothing matches reference image exactly before generating
- DO NOT change, modify, or substitute any clothing items
- Accessories are part of the character identity - include ALL specified accessories
```

### 使用示例 - 双角色场景

```
CHARACTER CONSISTENCY REQUIREMENT:
- Kai: MUST wear BLACK wool overcoat, dark sweater underneath, black-framed glasses
- Cici: MUST wear BLACK long coat (NOT red, NOT brown, NOT white!), RED silk scarf at neck
- Verify clothing matches reference images exactly before generating
- DO NOT substitute colors or remove accessories (especially Cici's red scarf)
```

### 常见问题及约束强化

| 问题类型 | 约束强化写法 |
|---------|-------------|
| 服装颜色被改变 | `BLACK coat (NOT red, NOT brown, NOT white!)` |
| 配饰被遗漏 | `RED scarf (MANDATORY - do not omit)` |
| 服装款式被改变 | `Long wool coat (NOT jacket, NOT cardigan)` |
| 多角色服装混淆 | 分别列出每个角色的完整服装描述 |

### 高频错误角色类型

针对以下角色类型，建议使用更强的约束：

**1. 女性角色配饰（围巾、首饰）**
```
- Cici: MUST wear vibrant RED silk scarf - this is her signature accessory
  (The red scarf MUST be visible in EVERY shot featuring this character)
```

**2. 眼镜角色**
```
- Kai: MUST wear black-framed glasses in EVERY shot
  (Glasses are part of character identity - NEVER remove)
```

**3. 特定风格服装**
```
- Character: MUST wear traditional hanfu in deep blue
  (NO modern clothing substitution, NO color changes)
```

---

## 版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| v2.2 | 2026-02-03 | **FIX-A4**: 新增"角色一致性约束块"章节 - 服装一致性强化约束模板 |
| v2.1 | 2026-02-03 | **PROMPT-2B**: 新增"场景情境约束块"章节 - 首次约会、热恋期、老友重逢通用约束模板 |
| v2.0 | 2026-01-23 | **TASK-FIX-001**: 修复留白和百分比泄露问题 - 移除所有百分比数字，将"预留空间"改为"禁止留白(FULL CANVAS)"表述，添加"不要渲染指令为图像"指令 |
| v1.0 | 2026-01-22 | 初版，基于原模板创建无文字版本 |
