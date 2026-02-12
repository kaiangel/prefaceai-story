# 条漫MVP Prompt模板

> **目标模型**: `gemini-2.5-flash-image`
> **作者**: @AI-ML
> **日期**: 2026-01-22
> **关联任务**: HANDOFF-2026-01-22-002

---

## 使用说明

1. 所有Prompt模板为**英文**（图像生成Prompt必须英文）
2. 中文文字内嵌：使用 `with Chinese text '具体文字'` 格式
3. 模板中的 `{variable}` 需要替换为实际值
4. 建议与 `StyleEnforcer` 配合使用，风格推荐 `illustration`

---

## 模板1: 对话气泡 (Speech Bubble)

### 视觉特征
- 白色圆角矩形气泡框
- 尖角指向说话者
- 黑色中文文字居中
- 气泡位置根据说话者位置调整

### Prompt模板

```
{scene_description}

TEXT OVERLAY REQUIREMENT:
A white rounded rectangular speech bubble with a pointed tail directed at {speaker_name}.
Inside the bubble, display Chinese text '{dialogue_text}' in black font, centered alignment.
The bubble should be positioned {bubble_position} in the frame, with the tail pointing toward the speaker's mouth.

Speech bubble style: clean white fill, thin black outline (1-2px), rounded corners (radius ~15px),
triangular tail pointing to speaker. Text should be clearly legible against white background.
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `{scene_description}` | 场景和角色描述 | "A young woman sitting at a cafe table, looking surprised" |
| `{speaker_name}` | 说话者名称 | "the woman" |
| `{dialogue_text}` | 对话内容（中文） | "对不起" |
| `{bubble_position}` | 气泡位置 | "upper right", "upper left", "center top" |

### 使用示例

```
A young man in gray sweater standing in a modern living room, looking apologetic with slightly bowed head and concerned eyes.

TEXT OVERLAY REQUIREMENT:
A white rounded rectangular speech bubble with a pointed tail directed at the man.
Inside the bubble, display Chinese text '对不起，我不是故意的' in black font, centered alignment.
The bubble should be positioned upper right in the frame, with the tail pointing toward the speaker's mouth.

Speech bubble style: clean white fill, thin black outline (1-2px), rounded corners (radius ~15px),
triangular tail pointing to speaker. Text should be clearly legible against white background.
```

---

## 模板2: 心理旁白 - 黑底白字 (Inner Monologue - Black Background)

### 视觉特征
- 半透明黑色背景条（位于画面顶部或底部）
- 白色中文文字
- 用于表达角色内心想法

### Prompt模板

```
{scene_description}

TEXT OVERLAY REQUIREMENT:
A semi-transparent black bar ({bar_position}) spanning the full width of the image, height approximately {bar_height} of frame.
Display Chinese text '{monologue_text}' in white font, {text_alignment} alignment.
The black overlay should have approximately 70-80% opacity, allowing slight visibility of background.

Inner monologue style: represents character's private thoughts, contemplative mood.
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `{scene_description}` | 场景和角色描述 | "A woman looking out the window with sad eyes" |
| `{bar_position}` | 黑条位置 | "at the top", "at the bottom" |
| `{bar_height}` | 黑条高度比例 | "15%", "20%" |
| `{monologue_text}` | 内心独白（中文） | "他为什么要这样对我..." |
| `{text_alignment}` | 文字对齐 | "centered", "left" |

### 使用示例

```
A young woman in casual clothes standing by a large window in an apartment, gazing outside with melancholic expression, eyes showing disappointment and hurt.

TEXT OVERLAY REQUIREMENT:
A semi-transparent black bar (at the bottom) spanning the full width of the image, height approximately 18% of frame.
Display Chinese text '他为什么要这样对我...' in white font, centered alignment.
The black overlay should have approximately 70-80% opacity, allowing slight visibility of background.

Inner monologue style: represents character's private thoughts, contemplative mood.
```

---

## 模板3: 叙事旁白 - 白底黑字 (Narrative Caption - White Background)

### 视觉特征
- 半透明白色/浅色背景条
- 黑色中文文字
- 用于叙述性说明或时间地点标注

### Prompt模板

```
{scene_description}

TEXT OVERLAY REQUIREMENT:
A semi-transparent white/cream colored bar ({bar_position}) spanning the full width of the image, height approximately {bar_height} of frame.
Display Chinese text '{narrative_text}' in black font, {text_alignment} alignment.
The white overlay should have approximately 80-85% opacity with soft edges.

Narrative caption style: objective narration, establishes context or time passage.
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `{scene_description}` | 场景描述 | "City skyline at sunset" |
| `{bar_position}` | 白条位置 | "at the top", "at the bottom" |
| `{bar_height}` | 白条高度比例 | "12%", "15%" |
| `{narrative_text}` | 叙事文字（中文） | "三天后——" |
| `{text_alignment}` | 文字对齐 | "centered", "left" |

### 使用示例

```
A busy city street corner in the morning, people walking to work, sunlight casting long shadows.

TEXT OVERLAY REQUIREMENT:
A semi-transparent white/cream colored bar (at the top) spanning the full width of the image, height approximately 12% of frame.
Display Chinese text '三天后，城市的另一边' in black font, centered alignment.
The white overlay should have approximately 80-85% opacity with soft edges.

Narrative caption style: objective narration, establishes context or time passage.
```

---

## 模板4: 分屏效果 (Split Screen)

### 视觉特征
- 画面垂直分割为左右两部分
- 各展示不同场景/角色/时间
- 用于对比或平行叙事

### Prompt模板

```
SPLIT SCREEN COMPOSITION:

LEFT HALF: {left_scene_description}
The left character shows {left_emotion} expression.

RIGHT HALF: {right_scene_description}
The right character shows {right_emotion} expression.

Visual style: Clear vertical division down the center of the image.
{division_style}
Both halves should have similar lighting style for visual coherence while showing contrasting content.

Split screen purpose: {narrative_purpose}
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `{left_scene_description}` | 左侧场景描述 | "A man in office, looking stressed" |
| `{right_scene_description}` | 右侧场景描述 | "A woman at home, looking worried" |
| `{left_emotion}` | 左侧人物表情 | "frustrated, tense" |
| `{right_emotion}` | 右侧人物表情 | "anxious, concerned" |
| `{division_style}` | 分割线风格 | "Sharp clean line", "Soft gradient blend", "Jagged torn paper edge" |
| `{narrative_purpose}` | 叙事目的 | "showing simultaneous events", "comparing past and present" |

### 使用示例

```
SPLIT SCREEN COMPOSITION:

LEFT HALF: A young man in business suit sitting at office desk late at night, computer screen glowing, papers scattered, looking exhausted and stressed.
The left character shows frustrated, tense expression with furrowed brows.

RIGHT HALF: A young woman in home clothes sitting on sofa in a cozy living room, holding phone, looking at it with worried expression.
The right character shows anxious, concerned expression with slightly pursed lips.

Visual style: Clear vertical division down the center of the image.
Sharp clean line separating the two scenes.
Both halves should have similar lighting style for visual coherence while showing contrasting content.

Split screen purpose: showing two people in different locations thinking about each other simultaneously.
```

---

## 模板5: 回忆碎片效果 (Memory Fragment)

### 视觉特征
- 主体人物在中央或一侧
- 周围漂浮着碎片状的回忆画面
- 碎片呈现玻璃碎片/拼图块/照片残片效果
- 回忆画面可能带有模糊或褪色效果

### Prompt模板

```
{main_character_description}

MEMORY FRAGMENT EFFECT:
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
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `{main_character_description}` | 主角描述 | "A woman standing alone, looking down pensively" |
| `{fragment_style}` | 碎片形状 | "jagged glass shards", "soft-edged photo pieces", "puzzle pieces" |
| `{fragment_count}` | 碎片数量 | "4-6", "3-4" |
| `{fragment_X_description}` | 每个碎片内容 | "Fragment 1: A happy couple holding hands" |
| `{fragment_treatment}` | 碎片视觉处理 | "slightly desaturated, soft glow edges", "sepia toned" |
| `{focus_style}` | 焦点风格 | "soft blur and slight transparency", "sharp but faded colors" |
| `{emotional_tone}` | 情绪基调 | "melancholic nostalgia", "bittersweet memories" |

### 使用示例

```
A young woman in casual dress standing in an empty park at dusk, head slightly bowed, eyes closed, one hand over her heart, expression showing deep sadness and longing.

MEMORY FRAGMENT EFFECT:
Surrounding the main character, floating memory fragments showing glimpses of the past.
Fragment shapes: jagged glass shards with glowing edges
Number of visible fragments: 4-5

Fragment contents:
Fragment 1: A happy couple laughing together at a cafe table
Fragment 2: Two hands interlinked, one wearing a simple ring
Fragment 3: A man's warm smile, looking directly at viewer
Fragment 4: Two people walking together on a beach at sunset

Fragment visual treatment: slightly desaturated colors, soft golden glow at edges, ethereal quality

The fragments should appear to float in space around the character, creating a dreamlike, nostalgic atmosphere.
Main character remains in sharp focus while fragments have soft blur and slight transparency.

Emotional tone: melancholic nostalgia, remembering lost love
```

---

## 模板6: 画中画效果 (Picture-in-Picture)

### 视觉特征
- 主画面中嵌入另一个画面（通常是手机/电脑/电视屏幕）
- 内嵌画面内容清晰可见
- 用于展示视频通话、看照片、回忆等

### Prompt模板

```
{main_scene_description}

PICTURE-IN-PICTURE ELEMENT:
{device_type} showing: {pip_content_description}

Device details:
- Position: {device_position}
- Size: approximately {device_size} of frame
- Screen content clearly visible and in focus
- {device_specific_details}

The embedded screen should show {pip_content_description} with realistic device frame and screen reflection/glow.

Visual relationship: {relationship_description}
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `{main_scene_description}` | 主场景描述 | "A person's hands holding a smartphone" |
| `{device_type}` | 设备类型 | "smartphone screen", "laptop screen", "TV screen", "photo frame" |
| `{pip_content_description}` | 画中画内容 | "a video call with a smiling woman" |
| `{device_position}` | 设备位置 | "center of frame", "lower right" |
| `{device_size}` | 设备占画面比例 | "40%", "30%" |
| `{device_specific_details}` | 设备细节 | "modern smartphone with thin bezels", "vintage photo frame with wooden border" |
| `{relationship_description}` | 视觉关系 | "viewer sees both the holder's reaction and the screen content" |

### 使用示例

```
A young man's hands holding a smartphone in a dimly lit room, the phone screen illuminating his face partially visible at the top of frame, expression showing surprise and joy.

PICTURE-IN-PICTURE ELEMENT:
Smartphone screen showing: a selfie photo of a young woman smiling brightly at the camera, wearing a sundress, with a beach sunset background.

Device details:
- Position: center of frame, taking up significant visual space
- Size: approximately 45% of frame
- Screen content clearly visible and in focus
- Modern smartphone with thin black bezels, slight screen reflection visible

The embedded screen should show the woman's selfie photo with realistic device frame and subtle screen glow.

Visual relationship: viewer sees the photo on screen and can glimpse the man's delighted reaction, creating emotional connection between the two images.
```

---

## 表情细腻度描述词库

### 8种核心表情及其英文描述

| 中文表情 | 英文关键词 | 面部细节描述 |
|---------|-----------|-------------|
| **不悦** | displeased, annoyed, irritated | furrowed brows, slightly narrowed eyes, tight-lipped, jaw slightly clenched, nostrils slightly flared |
| **委屈** | aggrieved, hurt, wronged | glistening eyes (almost teary), slightly trembling lower lip, brows drawn together and upward, pained expression, vulnerable look |
| **困惑** | confused, puzzled, perplexed | raised eyebrows (one higher than other), tilted head, squinted eyes, slightly open mouth, questioning gaze |
| **道歉** | apologetic, remorseful, contrite | lowered gaze, bowed head slightly, softened eyes, pressed lips, humble posture, shoulders slightly hunched |
| **震惊** | shocked, stunned, astonished | wide eyes, raised eyebrows high, open mouth (jaw dropped), frozen expression, dilated pupils, face slightly pale |
| **冷漠** | indifferent, aloof, detached | neutral/flat expression, half-lidded eyes, relaxed facial muscles, distant gaze, slight downturn of lips, emotionally guarded |
| **释然** | relieved, at peace, unburdened | soft gentle smile, relaxed brows, warm eyes, deep exhale implied, tension released from face, serene expression |
| **开心** | happy, joyful, delighted | genuine smile reaching eyes (crow's feet), raised cheeks, bright sparkling eyes, relaxed open expression, visible teeth in smile |

### 表情强度修饰词

| 强度 | 英文修饰词 |
|------|-----------|
| 轻微 | slightly, subtly, hint of, touch of |
| 中等 | noticeably, clearly, visibly |
| 强烈 | intensely, deeply, overwhelmingly, extremely |
| 压抑 | suppressed, restrained, barely contained |
| 混合 | mixed with, tinged with, underlying |

### 表情组合示例

```
# 委屈中带着倔强
"hurt and wronged expression with glistening eyes, yet chin lifted defiantly,
a mix of vulnerability and stubborn pride"

# 震惊转为愤怒
"initial shock with wide eyes transitioning to anger, brows furrowing,
jaw tightening, disbelief mixing with rising fury"

# 压抑的悲伤
"suppressed sadness, eyes slightly red-rimmed, forcing a weak smile,
pain visible beneath the composed exterior"

# 释然中的苦涩
"relieved expression tinged with bitterness, a sad smile, eyes showing
both peace and lingering hurt, letting go with difficulty"
```

---

## 组合使用示例

### 示例1: 对话气泡 + 表情

```
A young woman in white blouse sitting across from a man at a small cafe table. She shows an aggrieved, hurt expression with glistening eyes almost teary, brows drawn together and upward, slightly trembling lower lip, looking at the man with a vulnerable, pained look.

TEXT OVERLAY REQUIREMENT:
A white rounded rectangular speech bubble with a pointed tail directed at the woman.
Inside the bubble, display Chinese text '你怎么能这样说...' in black font, centered alignment.
The bubble should be positioned upper left in the frame, with the tail pointing toward the speaker's mouth.

Speech bubble style: clean white fill, thin black outline (1-2px), rounded corners (radius ~15px),
triangular tail pointing to speaker. Text should be clearly legible against white background.
```

### 示例2: 黑底旁白 + 回忆碎片

```
A young man standing alone on a rooftop at night, city lights behind him, looking up at the sky with a relieved expression tinged with bitterness, a sad smile on his face, eyes showing both peace and lingering hurt.

MEMORY FRAGMENT EFFECT:
Surrounding the man, floating memory fragments showing glimpses of happier times.
Fragment shapes: soft-edged photo pieces with slightly torn edges
Number of visible fragments: 3-4

Fragment contents:
Fragment 1: Two people sharing an umbrella in the rain, laughing
Fragment 2: A woman's hand placing a small gift box on a table
Fragment 3: Sunset seen through a car window, two silhouettes visible

Fragment visual treatment: warm sepia tone, soft glow edges, fading at boundaries

TEXT OVERLAY REQUIREMENT:
A semi-transparent black bar (at the bottom) spanning the full width of the image, height approximately 15% of frame.
Display Chinese text '有些人，注定只能陪你走一段路' in white font, centered alignment.
The black overlay should have approximately 75% opacity.

Emotional tone: bittersweet farewell, acceptance mixed with loss
```

---

## 与StyleEnforcer集成

推荐使用 `illustration` 风格，与参考案例风格一致：

```python
from app.services.style_enforcer import StyleEnforcer

enforcer = StyleEnforcer()
style_config = {"style": "illustration"}

# 应用风格前缀
final_prompt = enforcer.enforce_prompt(your_template_prompt, style_config)
```

StyleEnforcer会在prompt开头注入：
```
═══════════════════════════════════════════════════════════
MANDATORY STYLE REQUIREMENT - DO NOT IGNORE THIS SECTION
═══════════════════════════════════════════════════════════
STYLE: Digital Illustration
MUST INCLUDE: digital illustration, vibrant colors, detailed artwork, concept art, clean lines
DO NOT USE: photorealistic, photograph, real photo, 3D render, low quality
═══════════════════════════════════════════════════════════
```

---

## 验收对照

| 模板 | 对应参考图 | 验收重点 |
|------|-----------|---------|
| 对话气泡 | IMG_0804, 0808 | 气泡形状、尖角方向、文字清晰度 |
| 心理旁白(黑底) | IMG_0804, 0805, 0807 | 黑条透明度、文字可读性、位置 |
| 叙事旁白(白底) | IMG_0816, 0817 | 白条柔和度、文字对比度 |
| 分屏效果 | IMG_0811 | 分割清晰度、两侧内容平衡 |
| 回忆碎片 | IMG_0809 | 碎片形态、漂浮感、情绪氛围 |
| 画中画 | IMG_0815, 0816 | 设备真实感、屏幕内容清晰度 |
| 表情词库 | IMG_0805, 0807, 0808 | 表情准确性、细腻度 |

---

## 版本历史

| 版本 | 日期 | 修改内容 |
|------|------|---------|
| v1.0 | 2026-01-22 | 初版，6个模板 + 表情词库 |
