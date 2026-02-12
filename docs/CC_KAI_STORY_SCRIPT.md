# Kai与Cici初次约会 - 完整故事脚本

> **作者**: @AI-ML
> **日期**: 2026-01-30
> **关联任务**: HANDOFF-2026-01-30-011
> **用途**: 配合 TextOverlayServiceV2 测试完整故事生成

---

## 故事信息

| 项目 | 内容 |
|------|------|
| **标题** | Kai与Cici初次约会 (First Date) |
| **题材** | 都市情感（恋爱） |
| **主题** | 探探相识 → 首次线下约会 → 心动萌芽 |
| **风格** | Korean Webtoon Style (韩漫风格) |
| **色调** | 暖色调、柔和光影、都市时尚感 |
| **图片数** | 42 |
| **角色数** | 2 (Kai, Cici) |

---

## 角色设计 (Character Designs)

### Cici (女主)

| 字段 | 内容 |
|------|------|
| **name** | Cici |
| **name_en** | Cici |
| **type** | human |
| **gender** | female |
| **age_appearance** | young_adult (33) |

**Physical Description:**
```
height: medium (165cm)
build: slim, elegant
skin_tone: fair porcelain
face_shape: oval with delicate features
hair_color: deep chestnut brown
hair_style: long wavy hair falling past shoulders, soft curls
hair_texture: silky with natural waves
eye_color: warm dark brown
eye_shape: almond, expressive
eye_size: medium-large
eyebrows: natural arch, well-groomed, slightly thick
nose: small and straight with delicate bridge
lips: soft pink, natural fullness, gentle cupid's bow
distinctive_marks: small beauty mark on right cheek
```

**Clothing (Date Outfit):**
```
top: black fitted knit sweater with subtle ribbed texture
outerwear: black long wool coat with classic cut
bottom: light gray midi pencil skirt
footwear: black pointed-toe heels
accessories: vibrant red silk scarf around neck, small gold hoop earrings, simple gold bracelet
style: elegant urban chic
```

**参考图路径:**
- 肖像: `test_output/manualtest/teststory_CCKai/character_refs/CC_portrait.png`
- 全身: `test_output/manualtest/teststory_CCKai/character_refs/CC_fullbody.png`

**⚠️ 参考图使用说明:** 仅参考脸部特征（面部轮廓、五官、发型发色），服装必须使用上述故事服装描述。

---

### Kai (男主)

| 字段 | 内容 |
|------|------|
| **name** | Kai |
| **name_en** | Kai |
| **type** | human |
| **gender** | male |
| **age_appearance** | young_adult (33) |

**Physical Description:**
```
height: tall (182cm)
build: lean and athletic
skin_tone: light with warm undertone
face_shape: defined jawline, angular features
hair_color: jet black
hair_style: short and neatly styled, slightly textured on top
hair_texture: thick and straight
eye_color: dark brown, deep and warm
eye_shape: almond, thoughtful
eye_size: medium
eyebrows: straight and defined, dark
nose: straight with strong bridge
lips: medium thickness, natural color
distinctive_marks: black rectangular glasses frames
```

**Clothing (Date Outfit):**
```
top: dark purple-black knit sweater with crew neck
outerwear: black wool overcoat, tailored fit
bottom: dark indigo slim-fit jeans
footwear: black leather oxford shoes
accessories: black rectangular glasses, simple black leather watch
style: refined casual elegance
```

**参考图路径:**
- 肖像: `test_output/manualtest/teststory_CCKai/character_refs/Kai_portrait.png`
- 全身: `test_output/manualtest/teststory_CCKai/character_refs/Kai_fullbody.png`

**⚠️ 参考图使用说明:** 仅参考脸部特征（面部轮廓、五官、发型发色、眼镜），服装必须使用上述故事服装描述。

---

## 风格指令 (Style Instructions)

### Korean Webtoon 风格前缀

所有 image_prompt 开头必须添加：

```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style
```

### 参考图指令块

当使用角色参考图时，必须添加：

```
CHARACTER REFERENCE:
- FACE REFERENCE ONLY from reference image (ignore clothing in reference)
- Use face shape, features, hair color and style from reference
- CLOTHING: [使用故事服装描述，不使用参考图服装]
```

---

## 42图完整脚本 (Complete Script)

---

## 第一幕：线上相识 (Shots 01-04)

---

### Shot 01: 探探匹配

**场景**: 手机屏幕，探探APP界面，显示匹配成功

| 字段 | 内容 |
|------|------|
| **shot_id** | 1 |
| **text_type** | narration |
| **text_position** | bottom |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

A smartphone screen showing a dating app interface. The screen displays two profile photos side by side - a young man with black short hair and glasses on the left, and a young woman with long wavy brown hair on the right. A heart icon or match indicator glows between them.

The phone is held by feminine hands with natural nails. Soft warm lighting illuminates the screen in a dark room, creating an intimate late-night atmosphere. The screen light casts a gentle glow.

UI COMPOSITION:
The app interface is stylized and illustrated, not realistic. Profile photos are in webtoon art style matching the characters. No readable text on screen - use abstract symbols or blurred text placeholders.

EMOTIONAL ATMOSPHERE:
A sense of anticipation and possibility. The warm glow of the screen suggests late night browsing, a moment of connection.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any readable text, letters, or characters in the image.
Use abstract shapes or blurred elements instead of actual text on the app interface.
Leave clean space at BOTTOM (85-100% height) for narrative overlay.
```

**中文文字:**
```
旁白：「2023年1月的某个夜晚，两个陌生人在探探相遇。」
```

---

### Shot 02: 日常聊天

**场景**: 手机屏幕，聊天记录

| 字段 | 内容 |
|------|------|
| **shot_id** | 2 |
| **text_type** | dialogue |
| **text_position** | center |
| **speakers** | Cici, Kai |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

A smartphone screen showing a chat conversation interface. Multiple message bubbles arranged vertically - some on the left (received) and some on the right (sent). The bubbles are stylized illustrations without readable text.

The background shows a cozy evening setting - perhaps a bedside table with a warm lamp, creating intimate atmosphere. The phone screen glows warmly.

UI COMPOSITION:
Abstract chat bubbles in different colors (left gray, right blue/green). Small avatar icons next to messages. No actual readable text - use wavy lines or abstract shapes as text placeholders.

EMOTIONAL ATMOSPHERE:
Warmth and growing connection. The multiple message bubbles suggest an engaging, flowing conversation that lasted hours.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any readable text in the image.
Use abstract wavy lines as text placeholders in chat bubbles.
Leave clean space in CENTER area for dialogue overlay.
```

**中文文字:**
```
Cici：「你周末一般做什么？」
Kai：「看书、跑步，偶尔自己做饭」
Cici：「会做饭的男生不多见诶」
Kai：「下次做给你吃？」

旁白：「从日常聊到深夜，从陌生聊成熟悉。」
```

---

### Shot 03: 约定见面

**场景**: 手机屏幕，聊天记录

| 字段 | 内容 |
|------|------|
| **shot_id** | 3 |
| **text_type** | dialogue_with_thought |
| **text_position** | center, bottom |
| **speakers** | Kai, Cici |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

A smartphone held in delicate feminine hands, showing a chat interface. The screen displays a conversation with a calendar or date-picking element visible. The last few messages show excitement with heart or happy emoji-style icons.

The background is soft-focused - perhaps a young woman's bedroom or living room with warm lighting. A hint of the woman's face visible at the top edge of frame, showing a subtle smile.

EMOTIONAL ATMOSPHERE:
Anticipation and nervous excitement. The moment of agreeing to meet in person for the first time.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any readable text in the image.
Use abstract symbols for chat content.
Leave space at CENTER for dialogue and BOTTOM for thought overlay.
```

**中文文字:**
```
Kai：「聊了一个多月了，要不要见一面？」
Cici：「好呀，什么时候？」
Kai：「周三怎么样？工作日人少」
Cici：「思南路那家Feloni，听说不错」
Kai：「好，周三傍晚6点」

Cici内心：「终于要见面了...有点紧张。」
```

---

### Shot 04: 各自准备（分屏）

**场景**: 分屏构图 - 左Kai右Cici，各自对镜整理

| 字段 | 内容 |
|------|------|
| **shot_id** | 4 |
| **text_type** | thought |
| **text_position** | left_bottom, right_bottom |
| **speakers** | Kai, Cici |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

SPLIT SCREEN COMPOSITION:

LEFT HALF: A young man with short black hair and black rectangular glasses standing before a mirror in a modern minimalist bedroom. He is wearing a dark purple-black knit sweater, adjusting the collar with careful attention. His expression is focused and slightly nervous, checking his appearance with a small frown of concentration. Clean modern furniture, soft daylight from window.

RIGHT HALF: A young woman with long wavy chestnut brown hair standing before a vanity mirror in a warmly lit bedroom. She is tying a vibrant red silk scarf around her neck, wearing a black knit sweater. Her expression shows a gentle smile of anticipation as she checks her reflection. Warm lamp lighting, feminine decor with soft colors.

VISUAL STYLE:
- Clear vertical division down the center
- Both sides lit with warm, flattering light
- Mirror reflections showing the characters' faces
- Slight color temperature difference: cooler left (Kai), warmer right (Cici)

CHARACTER REFERENCE:
- LEFT (Kai): FACE REFERENCE ONLY from reference. Use face features and glasses. CLOTHING: dark purple-black knit sweater
- RIGHT (Cici): FACE REFERENCE ONLY from reference. Use face features and wavy hair. CLOTHING: black knit sweater with red silk scarf

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text, speech bubbles, or captions.
Fill BOTH halves completely with visual content.
Leave space at BOTTOM of each half for thought overlay.
```

**中文文字:**
```
Kai内心：「这件毛衣...应该还行吧？」
Cici内心：「这条丝巾是点睛之笔。」
```

---

## 第二幕：Kai等待 (Shots 05-07)

---

### Shot 05: 提前到达

**场景**: 思南路，Feloni餐厅外观，傍晚

| 字段 | 内容 |
|------|------|
| **shot_id** | 5 |
| **text_type** | narration |
| **text_position** | bottom |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

A charming European-style street in Shanghai's French Concession district at dusk. A cozy Italian restaurant with warm light spilling from its windows. The facade features elegant French colonial architecture with tall windows, wrought iron balconies, and mature plane trees (梧桐树) lining the street.

Street lamps are beginning to glow with warm golden light. The sky shows the soft orange-pink gradients of sunset. Fallen autumn leaves scattered on the cobblestone sidewalk. The restaurant entrance has a small awning and potted plants.

ENVIRONMENTAL DETAILS:
- Classic Shanghai French Concession architecture
- Warm inviting restaurant lighting
- Romantic dusk atmosphere
- Empty outdoor seating area with bistro chairs

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any readable text on signs or storefronts.
Use abstract shapes or weathered/artistic signage without legible text.
Leave clean space at BOTTOM (85-100%) for narrative overlay.
```

**中文文字:**
```
旁白：「2月1日，周三傍晚。上海思南路。」
```

---

### Shot 06: 门口等待

**场景**: 餐厅门口，Kai站立等待

| 字段 | 内容 |
|------|------|
| **shot_id** | 6 |
| **text_type** | thought |
| **text_position** | top |
| **speaker** | Kai |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

A tall young man with short black hair and black rectangular glasses standing outside a restaurant entrance. He wears a black wool overcoat over a dark purple-black sweater, hands casually in coat pockets. His posture is slightly tense with anticipation.

His expression shows a mix of nervousness and eagerness - eyebrows slightly raised, eyes scanning the street direction, lips pressed together in contained excitement. The warm glow from the restaurant windows illuminates one side of his face.

MEDIUM SHOT framing, showing him from thighs up. The restaurant's warm interior visible through glass windows behind him. Street lamp casting golden light. A few autumn leaves drifting past.

CHARACTER REFERENCE:
- FACE REFERENCE ONLY from Kai reference image
- CLOTHING: black wool overcoat, dark purple-black sweater underneath
- Black rectangular glasses frames

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text or signs with readable content.
Leave clean space at TOP (0-15%) for thought overlay.
Character's face and expression must be clearly visible.
```

**中文文字:**
```
Kai内心：「还有五分钟...她会喜欢这里吗？」
```

---

### Shot 07: 看手表

**场景**: 餐厅门口，Kai抬手看表

| 字段 | 内容 |
|------|------|
| **shot_id** | 7 |
| **text_type** | narration |
| **text_position** | bottom |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

CLOSE-UP to MEDIUM CLOSE-UP shot of a young man with black hair and rectangular glasses. He is lifting his left wrist to check his watch - a simple black leather strap watch. His expression shows anticipation mixed with slight nervousness - gentle smile forming, eyes focused on the watch face.

He wears a black wool overcoat with the collar slightly turned up against the evening chill. The warm golden light from nearby street lamps illuminates his face from the side, creating a romantic atmosphere.

COMPOSITION:
- Focus on his face and the gesture of checking time
- Watch visible but not the main focus
- Warm bokeh lights in soft-focus background
- Evening atmosphere with golden hour remnants

CHARACTER REFERENCE:
- FACE REFERENCE ONLY from Kai reference image
- CLOTHING: black wool overcoat
- Black rectangular glasses frames

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any readable text, including on the watch face.
Leave clean space at BOTTOM (85-100%) for narrative overlay.
```

**中文文字:**
```
旁白：「他比约定时间早到了十分钟。这是他的习惯。」
```

---

## 第三幕：Cici出现 (Shots 08-11) ⭐ 情感重点1

---

### Shot 08: 街角身影

**场景**: 思南路街角，Cici从梧桐树下走来

| 字段 | 内容 |
|------|------|
| **shot_id** | 8 |
| **text_type** | narration |
| **text_position** | top |
| **speaker** | Kai视角 |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

LONG SHOT of a quiet street corner in Shanghai's French Concession. A young woman's silhouette emerges from under the canopy of plane trees (梧桐树). She wears a long black coat, and a vibrant red scarf stands out brilliantly against the muted evening colors.

The street is lined with beautiful colonial architecture and mature trees with golden autumn leaves. Street lamps cast warm pools of light on the cobblestone. The woman is walking toward the camera, still at a distance, her figure elegant and confident.

ATMOSPHERIC DETAILS:
- Dusk light with warm orange-pink sky visible between buildings
- Golden autumn leaves on trees and ground
- Romantic European-style street scene
- The red scarf as a striking visual focal point

CHARACTER REFERENCE:
- FACE REFERENCE ONLY from Cici reference (face not detailed at this distance)
- CLOTHING: black long wool coat, vibrant red silk scarf visible even from distance
- Long wavy brown hair

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any readable text or signs.
Leave clean space at TOP (0-15%) for narrative overlay.
```

**中文文字:**
```
旁白（Kai视角）：「是她。」
```

---

### Shot 09: 走近

**场景**: 街道，Cici走近，红丝巾在风中轻扬

| 字段 | 内容 |
|------|------|
| **shot_id** | 9 |
| **text_type** | thought |
| **text_position** | bottom |
| **speaker** | Cici |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

MEDIUM SHOT of a young woman walking down a tree-lined street, approaching closer. She has long wavy chestnut brown hair flowing gently in the evening breeze. Her vibrant red silk scarf flutters elegantly. She wears a black long wool coat over a black knit sweater and light gray skirt.

Her expression shows anticipation and slight nervous excitement - eyes searching ahead with hope, a gentle expectant smile forming on her lips. Her cheeks have a slight blush from the cold evening air.

BACKGROUND:
- Beautiful plane trees (梧桐树) with golden autumn leaves
- French colonial architecture with warm lit windows
- Romantic dusk lighting with street lamps glowing
- A few autumn leaves falling in the breeze

CHARACTER REFERENCE:
- FACE REFERENCE ONLY from Cici reference image
- CLOTHING: black long wool coat, red silk scarf, black knit sweater visible at neckline
- Long wavy chestnut brown hair

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text or readable signs.
Leave clean space at BOTTOM (85-100%) for thought overlay.
Her face and expression must be clearly visible.
```

**中文文字:**
```
Cici内心：「那个穿黑色大衣的...是他吗？」
```

---

### Shot 10: 目光相遇 ⭐【情感重点1-A：发现对方】

**场景**: 餐厅门口，两人目光交汇的瞬间

| 字段 | 内容 |
|------|------|
| **shot_id** | 10 |
| **text_type** | narration |
| **text_position** | top |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

⭐ EMOTIONAL HIGHLIGHT SHOT ⭐

TWO-SHOT MEDIUM composition capturing the magical moment of first eye contact. A young woman with long wavy brown hair and red scarf on the left, and a tall young man with black hair and glasses on the right. They are about 5 meters apart, having just spotted each other.

BOTH characters show that frozen moment of recognition - eyes widening slightly, breath caught, time seeming to slow down. The woman's lips part in surprised delight. The man's expression softens with wonder.

LIGHTING AND ATMOSPHERE:
- Romantic golden hour lighting wrapping around both figures
- Soft bokeh lights from street lamps and restaurant windows
- Warm color palette emphasizing the emotional moment
- Background slightly soft-focused to emphasize the characters
- Subtle sparkle or glow effect around them (webtoon romantic style)

CHARACTER REFERENCE:
- LEFT (Cici): FACE REFERENCE ONLY. CLOTHING: black coat, red scarf, long wavy brown hair
- RIGHT (Kai): FACE REFERENCE ONLY. CLOTHING: black overcoat, glasses

COMPOSITION:
- Characters facing each other with space between
- Eye-level camera angle
- Cinematic romantic framing

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text or speech bubbles.
Leave clean space at TOP (0-15%) for narrative overlay.
Both faces and their expressions must be crystal clear.
```

**中文文字:**
```
旁白：「目光相遇的那一刻，时间好像慢了下来。」
```

---

### Shot 11: 心动瞬间 ⭐【情感重点1-B：心动特写】

**场景**: 近景特写，聚焦两人表情，背景大幅虚化

| 字段 | 内容 |
|------|------|
| **shot_id** | 11 |
| **text_type** | thought |
| **text_position** | left_bottom, right_bottom |
| **speakers** | Kai, Cici |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

⭐ EMOTIONAL HIGHLIGHT SHOT - CLOSE-UP ⭐

SPLIT CLOSE-UP or ALTERNATING CLOSE-UP composition showing both characters' faces in intimate detail, with dreamy soft-focus background.

LEFT SIDE - Kai's face in close-up:
- His dark eyes behind glasses show gentle warmth and wonder
- A soft, genuine smile just beginning to form
- Eyes sparkling with the light of first attraction
- Expression: tender, captivated, slightly breathless

RIGHT SIDE - Cici's face in close-up:
- Her warm brown eyes widened with pleasant surprise
- Cheeks showing a delicate pink blush
- Lips curved in a blooming smile of delight
- Expression: touched, happy, heart fluttering

ROMANTIC ELEMENTS (Korean Webtoon Style):
- Soft sparkle/shimmer effects around the eyes
- Warm golden light caressing their faces
- Heavily blurred romantic bokeh background
- Subtle pink/warm tones enhancing the moment
- Dreamy, ethereal quality

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Black hair, rectangular glasses, gentle expression
- Cici: FACE REFERENCE ONLY. Wavy brown hair, red scarf edge visible, blushing cheeks

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text or speech bubbles.
Leave space at BOTTOM of each side for thought overlay.
Faces must be the absolute focus - detailed, expressive, beautiful.
```

**中文文字:**
```
Kai内心：「她笑起来，比照片还好看。」
Cici内心：「他的眼睛...好温柔。」
```

---

## 第四幕：初次对话 (Shots 12-14)

---

### Shot 12: 打招呼

**场景**: 餐厅门口，两人面对面，距离约1米

| 字段 | 内容 |
|------|------|
| **shot_id** | 12 |
| **text_type** | dialogue |
| **text_position** | left, right |
| **speakers** | Kai, Cici |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

MEDIUM TWO-SHOT of a young man and woman standing face to face outside a warmly-lit restaurant, about one meter apart. Both are smiling with shy happiness.

LEFT - Kai: tall man in black overcoat, dark sweater underneath, black glasses. He has a warm, slightly nervous smile, standing with good posture, looking at her with gentle eyes.

RIGHT - Cici: elegant woman in black coat with red silk scarf, long wavy brown hair. She looks up at him with a delighted, slightly shy smile, eyes bright with happiness.

The warm light from the restaurant creates a golden glow around them. The evening atmosphere is romantic with soft street lighting.

BODY LANGUAGE:
- Both slightly leaning toward each other
- Open, welcoming postures
- The electricity of first meeting in person

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. CLOTHING: black overcoat, dark sweater, glasses
- Cici: FACE REFERENCE ONLY. CLOTHING: black coat, red scarf, long wavy hair

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text or speech bubbles.
Leave space on LEFT side for Kai's dialogue bubble.
Leave space on RIGHT side for Cici's dialogue bubble.
```

**中文文字:**
```
Kai：「你好，Cici。终于见到真人了。」
Cici：「你好呀，Kai。」
```

---

### Shot 13: 第一句调侃

**场景**: 餐厅门口，近景聚焦Cici的俏皮表情

| 字段 | 内容 |
|------|------|
| **shot_id** | 13 |
| **text_type** | dialogue |
| **text_position** | top, bottom |
| **speakers** | Cici, Kai |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

CLOSE-UP to MEDIUM CLOSE-UP focusing on a young woman with long wavy brown hair. She has a playful, teasing smile - the kind of flirtatious expression after giving a compliment. Her eyes sparkle with mischief and genuine warmth. She's looking slightly downward with a shy but pleased expression.

Her red silk scarf is visible around her neck. Her cheeks have a soft pink blush. Her lips are curved in a coy, satisfied smile after making him flustered.

BACKGROUND:
- Soft blur showing warm restaurant lights
- The silhouette of a tall man (Kai) slightly visible in soft focus
- Romantic evening atmosphere

CHARACTER REFERENCE:
- FACE REFERENCE ONLY from Cici reference image
- Expression: playful, teasing, slightly shy but pleased
- CLOTHING: black coat, red scarf visible

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text or speech bubbles.
Leave space at TOP for Cici's dialogue.
Leave space at BOTTOM for Kai's response dialogue.
Her face and playful expression must be the focus.
```

**中文文字:**
```
Cici：「比照片帅嘛。」
Kai：「你也是，比照片还漂亮。」
```

---

### Shot 14: 进入餐厅

**场景**: 餐厅入口，Kai绅士地让Cici先进

| 字段 | 内容 |
|------|------|
| **shot_id** | 14 |
| **text_type** | narration |
| **text_position** | bottom |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

MEDIUM SHOT at the restaurant entrance. A tall young man in black overcoat is holding the door open, his other hand placed gently on the small of a young woman's back, guiding her inside. The gesture is gentlemanly and natural.

The woman with long wavy brown hair and red scarf is stepping through the doorway, her face turned slightly to look back at him with a touched, appreciative smile. His expression shows quiet attentiveness.

COMPOSITION:
- Doorway framing the scene
- Warm golden light spilling from inside the restaurant
- The contrast of cool evening outside and warm interior
- Their body language showing comfortable chemistry

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. CLOTHING: black overcoat, glasses. Gentlemanly posture
- Cici: FACE REFERENCE ONLY. CLOTHING: black coat, red scarf. Appreciative expression

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text or readable signs.
Leave clean space at BOTTOM (85-100%) for narrative overlay.
```

**中文文字:**
```
旁白：「他很自然地让她先走。细节里藏着教养。」
```

---

## 第五幕：餐厅落座 (Shots 15-17)

---

### Shot 15: 餐厅内景

**场景**: Feloni餐厅内部全景

| 字段 | 内容 |
|------|------|
| **shot_id** | 15 |
| **text_type** | narration |
| **text_position** | bottom |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

WIDE INTERIOR SHOT of a cozy Italian restaurant. Warm ambient lighting from hanging pendant lamps and candles on tables. The decor features exposed brick walls, wooden furniture, and Italian-inspired artwork.

The atmosphere is intimate and romantic - not too crowded, with soft background lighting. Wooden tables with white tablecloths, wine glasses catching the light. A small bar area visible in the background. Plants and warm decorative elements add charm.

COLOR PALETTE:
- Warm amber and golden lighting
- Rich wood tones
- Cream and white accents
- Touches of green from plants

ATMOSPHERE:
- Romantic but not overly formal
- Cozy and inviting
- Perfect for a first date

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any readable text, menus, or signs.
Leave clean space at BOTTOM (85-100%) for narrative overlay.
```

**中文文字:**
```
旁白：「Feloni，思南路上的一家意式小馆。温馨，不张扬。」
```

---

### Shot 16: 拉椅子

**场景**: 餐桌旁，Kai为Cici拉开椅子

| 字段 | 内容 |
|------|------|
| **shot_id** | 16 |
| **text_type** | dialogue_with_thought |
| **text_position** | left, right, bottom |
| **speakers** | Cici, Kai |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

MEDIUM SHOT at a restaurant table. A tall young man with black hair and glasses is pulling out a chair for a young woman. He stands behind the chair, hands on the back of it, posture attentive and gentlemanly.

The woman with long wavy brown hair is about to sit, her face showing genuine surprise and delight - eyes widened, a touched smile spreading across her face. She's removed her black coat, revealing a black fitted knit sweater. Her red scarf is now draped over the chair back.

The table has a lit candle, wine glasses, and elegant place settings. Warm candlelight illuminates their faces.

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. CLOTHING: dark purple-black sweater (coat off). Attentive expression
- Cici: FACE REFERENCE ONLY. CLOTHING: black fitted knit sweater. Touched, surprised smile

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text or menus.
Leave space on LEFT for Cici's dialogue.
Leave space on RIGHT for Kai's dialogue.
Leave space at BOTTOM for Cici's thought.
```

**中文文字:**
```
Cici：「谢谢。」
Kai：「请坐。」

Cici内心：「好久没遇到这么绅士的男生了。」
```

---

### Shot 17: 相对而坐

**场景**: 餐桌，两人面对面坐下

| 字段 | 内容 |
|------|------|
| **shot_id** | 17 |
| **text_type** | none |
| **text_position** | none |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

MEDIUM TWO-SHOT across a restaurant table. A young man and woman sit facing each other at a cozy table for two. Candlelight flickers between them, casting warm golden light on their faces.

LEFT - Kai sits with good posture, wearing a dark purple-black sweater. His black glasses reflect the candlelight. His expression is warm but slightly nervous - the endearing awkwardness of a first date.

RIGHT - Cici sits gracefully, wearing a black fitted sweater. Her long wavy brown hair catches the warm light. Her expression shows excited anticipation, eyes bright.

TABLE SETTING:
- Lit candle centerpiece
- Wine glasses (empty or with water)
- White napkins, elegant but simple plates
- Warm wood table surface

ATMOSPHERE:
- Intimate romantic setting
- Both slightly nervous but happy
- The electricity of possibility

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. CLOTHING: dark purple-black sweater, glasses
- Cici: FACE REFERENCE ONLY. CLOTHING: black fitted knit sweater

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text, menus, or readable content.
This shot focuses on the visual atmosphere - no text overlay needed.
Fill the entire frame with the romantic scene.
```

**中文文字:**
```
（无文字，纯氛围画面）
```

---

## 第六幕：用餐交谈 (Shots 18-22)

---

### Shot 18: 点餐

**场景**: 餐桌，两人一起看菜单

| 字段 | 内容 |
|------|------|
| **shot_id** | 18 |
| **text_type** | dialogue_with_thought |
| **text_position** | top, bottom |
| **speakers** | Kai, Cici |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

MEDIUM SHOT of a young couple looking at a menu together at a restaurant table. They're leaning slightly toward each other, the menu held between them.

Kai (left) is pointing at something on the menu, his expression thoughtful and attentive. He wears a dark purple-black sweater and glasses.

Cici (right) is looking at where he's pointing, her expression curious and trusting. She wears a black fitted knit sweater. Her head is tilted slightly, listening to his suggestions.

The candlelight creates a warm glow. Their body language shows comfortable rapport despite it being a first date.

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. CLOTHING: dark purple-black sweater, glasses. Attentive expression
- Cici: FACE REFERENCE ONLY. CLOTHING: black knit sweater. Trusting, interested expression

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any readable text on the menu.
Use abstract shapes or blurred content for menu items.
Leave space at TOP for dialogue overlay.
Leave space at BOTTOM for thought overlay.
```

**中文文字:**
```
Kai：「你有什么忌口吗？」
Cici：「不吃香菜，其他都可以。」
Kai：「那我来点？」
Cici：「好呀，你做主。」

Cici内心：「他问忌口，说明很细心。」
```

---

### Shot 19: 开始聊天

**场景**: 餐桌，菜已上桌，两人交谈

| 字段 | 内容 |
|------|------|
| **shot_id** | 19 |
| **text_type** | dialogue |
| **text_position** | left, right |
| **speakers** | Cici, Kai |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

MEDIUM TWO-SHOT at a restaurant table with food now served. Elegant Italian dishes are visible - pasta, perhaps some appetizers. Two glasses of red wine on the table.

The couple is engaged in animated conversation, both smiling and relaxed. Their body language is open and engaged.

LEFT - Cici is gesturing slightly as she speaks, her expression curious and engaged. Black knit sweater, wavy brown hair catching the warm light.

RIGHT - Kai is listening with a warm smile, his posture attentive. Dark purple-black sweater, glasses reflecting the candlelight.

The table shows signs of a meal in progress - some food on plates, wine partially consumed. The atmosphere is comfortable and flowing.

CHARACTER REFERENCE:
- Cici: FACE REFERENCE ONLY. Animated, curious expression. CLOTHING: black knit sweater
- Kai: FACE REFERENCE ONLY. Warm listening expression. CLOTHING: dark sweater, glasses

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text or readable labels.
Leave space on LEFT for Cici's dialogue.
Leave space on RIGHT for Kai's dialogue.
```

**中文文字:**
```
Cici：「你是做什么工作的？」
Kai：「互联网，产品经理。你呢？」
Cici：「设计师，做品牌视觉的。」
```

---

### Shot 20: Kai讲话，Cici听

**场景**: 餐桌，侧重Cici的反应

| 字段 | 内容 |
|------|------|
| **shot_id** | 20 |
| **text_type** | narration |
| **text_position** | bottom |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

MEDIUM SHOT focusing on a young woman at a restaurant table, with a young man partially visible opposite her (soft focus or cropped at frame edge).

Cici is the focus - she's listening intently to Kai speak. Her expression is captivated and warm. She has one hand resting against her cheek, elbow on table (relaxed, interested posture). Her eyes are bright and focused on him, a soft smile on her lips.

Her long wavy brown hair frames her face beautifully in the candlelight. She wears a black fitted knit sweater. The warm ambient lighting makes her look radiant.

Kai is visible as a soft-focus presence across the table - his gesturing hand, the edge of his sweater, suggesting he's animatedly telling a story.

CHARACTER REFERENCE:
- Cici: FACE REFERENCE ONLY. Captivated, adoring listening expression. CLOTHING: black knit sweater
- Kai: Partially visible, soft focus

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text.
Leave clean space at BOTTOM (85-100%) for narrative overlay.
Cici's enchanted expression is the focus.
```

**中文文字:**
```
旁白：「他讲话的时候，她喜欢看着他的眼睛。」
```

---

### Shot 21: Cici讲话，Kai听

**场景**: 餐桌，侧重Kai的反应

| 字段 | 内容 |
|------|------|
| **shot_id** | 21 |
| **text_type** | thought |
| **text_position** | bottom |
| **speaker** | Kai |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

MEDIUM SHOT focusing on a young man at a restaurant table, with a young woman partially visible opposite him (soft focus or cropped at frame edge).

Kai is the focus - he's listening to Cici with complete attention. His expression is warm and tender, a gentle smile on his lips. His eyes behind his glasses are soft and admiring. He's leaning slightly forward, completely engaged.

He wears a dark purple-black sweater. The candlelight reflects in his glasses and illuminates his attentive expression.

Cici is visible as a soft-focus presence - her gesturing hands, the movement of her hair as she speaks animatedly about something.

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Tender, admiring listening expression. CLOTHING: dark purple-black sweater, glasses
- Cici: Partially visible, soft focus

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text.
Leave clean space at BOTTOM (85-100%) for thought overlay.
Kai's gentle, admiring expression is the focus.
```

**中文文字:**
```
Kai内心：「她讲话的样子真好看。」
```

---

### Shot 22: 眼神交汇

**场景**: 餐桌，近景聚焦两人的眼神

| 字段 | 内容 |
|------|------|
| **shot_id** | 22 |
| **text_type** | narration |
| **text_position** | bottom |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

CLOSE-UP TWO-SHOT capturing an intimate moment of eye contact across the table. Both characters' faces in frame, looking at each other with a moment of shared connection.

The moment captures that electric instant when both happen to look up at the same time - a beat of surprised recognition, then soft smiles spreading on both faces.

LEFT - Cici's face in close-up, her warm brown eyes meeting his gaze, a gentle surprised smile, cheeks slightly flushed.

RIGHT - Kai's face in close-up, his eyes behind glasses showing warmth and connection, a matching smile forming.

ROMANTIC ATMOSPHERE:
- Soft candlelight between them (visible in lower frame)
- Warm color tones
- The air feels charged with unspoken attraction
- Korean webtoon style soft glow/sparkle effects subtle around their eyes

CHARACTER REFERENCE:
- Cici: FACE REFERENCE ONLY. Soft surprised smile, warm eyes
- Kai: FACE REFERENCE ONLY. Gentle smile, warm gaze through glasses

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text or speech bubbles.
Leave clean space at BOTTOM for narrative overlay.
Their eyes and expressions are the absolute focus.
```

**中文文字:**
```
旁白：「有些瞬间，不需要言语。」
```

---

## 第七幕：甜点时光 (Shots 23-24)

---

### Shot 23: 甜点上桌

**场景**: 餐桌，提拉米苏和咖啡

| 字段 | 内容 |
|------|------|
| **shot_id** | 23 |
| **text_type** | dialogue |
| **text_position** | left, right |
| **speakers** | Kai, Cici |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

MEDIUM SHOT of a restaurant table with dessert just served. A beautiful tiramisu sits in the center, with two cups of coffee. The main dinner plates have been cleared.

LEFT - Kai gestures toward the tiramisu with a recommending expression, looking at Cici. He wears a dark purple-black sweater, glasses.

RIGHT - Cici looks at the dessert with delighted eyes and an excited smile. Her expression is like a child seeing a treat. Black knit sweater, wavy brown hair.

The lighting is warm and intimate. The tiramisu looks delicious - layers of coffee-soaked ladyfingers and cream visible.

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Recommending, pleased expression. CLOTHING: dark sweater, glasses
- Cici: FACE REFERENCE ONLY. Delighted, excited expression. CLOTHING: black knit sweater

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text.
Leave space on LEFT for Kai's dialogue.
Leave space on RIGHT for Cici's dialogue.
```

**中文文字:**
```
Kai：「你试试这个，他们家招牌。」
Cici：「看起来好好吃！」
```

---

### Shot 24: 喂食瞬间

**场景**: 餐桌，Kai用勺子喂Cici

| 字段 | 内容 |
|------|------|
| **shot_id** | 24 |
| **text_type** | dialogue_with_thought |
| **text_position** | top, bottom |
| **speakers** | Kai, Cici |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

CLOSE to MEDIUM SHOT of an intimate moment. A young man is extending a spoon with a small piece of tiramisu toward a young woman across the table. The gesture is natural and caring.

Kai's expression is gentle and encouraging, holding the spoon steadily. He wears a dark purple-black sweater, glasses.

Cici's reaction shows surprised delight mixed with shyness - eyes widened, a slight blush on her cheeks, leaning forward slightly to accept. Her lips are parted, about to accept the offered bite. Expression is flustered but happy. Black knit sweater, wavy brown hair.

The candlelight adds romantic warmth. The moment feels natural despite it being a first date.

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Gentle, caring expression. CLOTHING: dark sweater, glasses
- Cici: FACE REFERENCE ONLY. Surprised, shy but pleased expression. CLOTHING: black knit sweater

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text.
Leave space at TOP for Kai's dialogue.
Leave space at BOTTOM for Cici's thought.
```

**中文文字:**
```
Kai：「尝尝。」

Cici内心：「这也太自然了...我们才第一次见面诶。」
```

---

## 第八幕：餐后散步 (Shots 25-29) ⭐ 情感重点2

---

### Shot 25: 离开餐厅

**场景**: 餐厅门口，两人走出

| 字段 | 内容 |
|------|------|
| **shot_id** | 25 |
| **text_type** | narration |
| **text_position** | bottom |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

MEDIUM SHOT of a young couple stepping out of a warmly-lit restaurant onto the evening street. Both have put their coats back on.

Kai holds the door, wearing his black overcoat over dark sweater, glasses catching the light. His expression is content and happy.

Cici steps out beside him, wearing her black long coat with red scarf visible. Her wavy brown hair moves slightly in the cool evening air. She looks up at the night sky, expression peaceful and reluctant for the evening to end.

The restaurant's warm light spills out behind them. The street is dark but romantic with street lamps glowing. The night has fully fallen.

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Content expression. CLOTHING: black overcoat, glasses
- Cici: FACE REFERENCE ONLY. Peaceful, slightly wistful expression. CLOTHING: black coat, red scarf

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any readable text or signs.
Leave clean space at BOTTOM (85-100%) for narrative overlay.
```

**中文文字:**
```
旁白：「晚餐结束，谁都没有提要回家。」
```

---

### Shot 26: 漫步思南路

**场景**: 思南路街道，两人并肩走

| 字段 | 内容 |
|------|------|
| **shot_id** | 26 |
| **text_type** | narration |
| **text_position** | top |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

WIDE to MEDIUM SHOT of a young couple walking side by side down a beautiful tree-lined street at night. The famous plane trees (梧桐树) of Shanghai's French Concession create a canopy above.

Street lamps cast warm golden pools of light. The colonial architecture creates a romantic European atmosphere. Fallen autumn leaves scattered on the cobblestones. The couple walks close together but not touching yet.

Kai is on the left, tall in his black overcoat, hands in pockets. Cici is on the right, her red scarf bright against the night, hair flowing behind her. Both are talking and smiling, comfortable with each other.

ATMOSPHERIC DETAILS:
- Beautiful night scene with warm lamp light
- Romantic European-style architecture
- Autumn leaves and bare tree branches
- Intimate but public setting

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Relaxed, happy expression. CLOTHING: black overcoat
- Cici: FACE REFERENCE ONLY. Animated, happy expression. CLOTHING: black coat, red scarf

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any readable text or signs.
Leave clean space at TOP (0-15%) for narrative overlay.
```

**中文文字:**
```
旁白：「他们沿着思南路慢慢走，聊着天，不想这个夜晚结束。」
```

---

### Shot 27: 靠近

**场景**: 街道，两人肩并肩，距离越来越近

| 字段 | 内容 |
|------|------|
| **shot_id** | 27 |
| **text_type** | thought |
| **text_position** | bottom |
| **speaker** | Cici |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

MEDIUM SHOT from the side, showing a young couple walking very close together on a nighttime street. Their arms are nearly touching, occasionally brushing as they walk.

The composition emphasizes their closeness - shoulders almost touching, walking in perfect sync. Kai on the left in black overcoat, Cici on the right in black coat with red scarf.

Cici's expression shows awareness of his proximity - a slight blush, eyes glancing down at where their arms almost touch, shy anticipation. Kai walks with quiet confidence, occasionally looking down at her.

STREET ATMOSPHERE:
- Warm street lamp light from above
- Romantic French Concession architecture
- Night time, quiet street
- Their breath visible in cool air (subtle)

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Quiet happiness, occasional glances at her. CLOTHING: black overcoat
- Cici: FACE REFERENCE ONLY. Shy awareness, slight blush. CLOTHING: black coat, red scarf

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text or signs.
Leave clean space at BOTTOM (85-100%) for thought overlay.
```

**中文文字:**
```
Cici内心：「他的手好像碰到我了...是不小心的吗？」
```

---

### Shot 28: 牵手前奏

**场景**: 街道，近景聚焦两人的手

| 字段 | 内容 |
|------|------|
| **shot_id** | 28 |
| **text_type** | thought |
| **text_position** | top |
| **speaker** | Kai |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

CLOSE-UP SHOT focusing on two hands walking side by side, about to touch. The scene captures the electric moment just before contact.

LEFT - A man's hand, defined fingers, slightly reaching toward her. Simple black leather watch visible at wrist. Black coat sleeve.

RIGHT - A woman's hand, delicate fingers, palm slightly open in unconscious invitation. Simple gold bracelet visible. Black coat sleeve.

Their fingertips are millimeters apart, about to brush. The tension is palpable.

BACKGROUND:
- Soft focus cobblestone street
- Warm lamp light creating highlights on their hands
- Romantic bokeh lights in background

CHARACTER DETAILS:
- Kai's hand: masculine but gentle, reaching tentatively
- Cici's hand: feminine, open, inviting

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text.
Leave clean space at TOP (0-15%) for thought overlay.
The hands and the moment of anticipation are the focus.
```

**中文文字:**
```
Kai内心：「我可以...牵她的手吗？」
```

---

### Shot 29: 牵手 ⭐【情感重点2：牵手】

**场景**: 街道，手部特写 + 两人侧影的双重构图

| 字段 | 内容 |
|------|------|
| **shot_id** | 29 |
| **text_type** | narration_with_thought |
| **text_position** | top, bottom |
| **speakers** | Kai, Cici |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

⭐ EMOTIONAL HIGHLIGHT SHOT ⭐

DUAL COMPOSITION combining hand close-up and couple silhouette:

PRIMARY FOCUS - CLOSE-UP of two hands now clasped together, fingers interlaced. The moment of connection captured beautifully.
- His hand: larger, protective, gently holding
- Her hand: smaller, delicate, holding back with equal tenderness
- Warm light highlighting the point of contact
- His black watch, her gold bracelet visible

SECONDARY (upper portion or inset) - The silhouettes of the couple walking hand in hand under the glow of a street lamp. Romantic night atmosphere, bare winter trees framing them.

ROMANTIC ELEMENTS:
- Warm golden light emphasizing the connected hands
- Subtle sparkle effect (Korean webtoon style)
- The contrast between intimate close-up and wider context
- Night atmosphere with warm lamp glow

CHARACTER REFERENCE:
- Kai: defined masculine hand, black coat, leather watch
- Cici: delicate feminine hand, black coat, gold bracelet

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text.
Leave space at TOP for narrative overlay.
Leave space at BOTTOM for thoughts overlay.
The connected hands are the emotional center.
```

**中文文字:**
```
旁白：「他握住了她的手。她没有松开。」

Kai内心：「她的手好软...好温暖。」
Cici内心：「心跳好快...但是，好安心。」
```

---

## 第九幕：地铁站前 (Shots 30-31)

---

### Shot 30: 到达地铁站

**场景**: 地铁站入口，两人牵着手站立

| 字段 | 内容 |
|------|------|
| **shot_id** | 30 |
| **text_type** | dialogue |
| **text_position** | right |
| **speaker** | Cici |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

MEDIUM SHOT of a young couple standing at a metro station entrance at night. They're still holding hands, both looking reluctant.

The metro entrance is visible in background - modern architecture with descending stairs and lighting from below. Other pedestrians are distant, giving them privacy.

Kai stands on the left, his expression showing he doesn't want the evening to end. He holds her hand gently.

Cici on the right looks torn - part of her knows she should go, but her body language (leaning slightly toward him, reluctant expression) shows she doesn't want to.

Both are in their coats - his black overcoat, her black coat with red scarf. Their joined hands are visible at center frame.

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Reluctant, hopeful expression. CLOTHING: black overcoat
- Cici: FACE REFERENCE ONLY. Torn, reluctant expression. CLOTHING: black coat, red scarf

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any readable text on signs.
Leave space on RIGHT for Cici's dialogue.
```

**中文文字:**
```
Cici：「地铁站到了...我该回去了。」
```

---

### Shot 31: 提议送她

**场景**: 地铁站入口，两人对视

| 字段 | 内容 |
|------|------|
| **shot_id** | 31 |
| **text_type** | dialogue |
| **text_position** | left, right |
| **speakers** | Kai, Cici |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

CLOSE TWO-SHOT of the couple facing each other near the metro entrance. The moment Kai offers to drive her home.

Kai's expression is earnest and gentlemanly, looking at her with warmth. He gestures slightly toward another direction (where his car might be parked).

Cici's expression shows being "swept off her feet" - surprised, touched, a blush spreading across her cheeks, eyes bright with happiness. The classic Korean romance moment of being charmed.

Night lighting creates dramatic shadows. Their faces are well-lit, emotional.

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Earnest, charming expression. CLOTHING: black overcoat, glasses
- Cici: FACE REFERENCE ONLY. Flustered, touched, blushing expression. CLOTHING: black coat, red scarf

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text or signs.
Leave space on LEFT for Kai's dialogue.
Leave space on RIGHT for Cici's dialogue.
```

**中文文字:**
```
Kai：「我开车送你吧。这个点地铁挤。」
Cici：「可是...你不顺路吧？」
Kai：「送你回家，就是最顺的路。」
```

---

## 第十幕：车内时光 (Shots 32-35)

---

### Shot 32: 走向车边

**场景**: 停车场，两人走向Kai的车

| 字段 | 内容 |
|------|------|
| **shot_id** | 32 |
| **text_type** | narration |
| **text_position** | bottom |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

MEDIUM to WIDE SHOT of a young couple walking through a quiet parking area at night. Kai leads slightly, looking back at Cici with a warm expression. She follows with a happy, trusting smile.

The setting is a small street-side parking area, not an enclosed garage. Street lamps provide warm lighting. A modest, clean car (sedan, dark color) is visible nearby - nothing flashy, just practical and well-maintained.

Both are in winter coats. Their body language shows comfortable companionship - not holding hands in this shot, but walking close together.

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Looking back warmly. CLOTHING: black overcoat
- Cici: FACE REFERENCE ONLY. Happy, trusting smile. CLOTHING: black coat, red scarf

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any readable text or license plates.
Leave clean space at BOTTOM (85-100%) for narrative overlay.
```

**中文文字:**
```
旁白：「他的车停在不远处。」
```

---

### Shot 33: 开车门

**场景**: 车边，Kai为Cici打开副驾车门

| 字段 | 内容 |
|------|------|
| **shot_id** | 33 |
| **text_type** | dialogue_with_thought |
| **text_position** | left, bottom |
| **speakers** | Kai, Cici |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

MEDIUM SHOT of Kai holding open the passenger door of his car for Cici. The chivalrous gesture captured mid-action.

Kai stands by the open door with a gentle, inviting expression, gesturing for her to enter. His posture is attentive and caring.

Cici is stepping toward the car, her expression showing touched appreciation - a soft smile, eyes warm with gratitude. She's looking at him with affection.

The car interior light illuminates them both warmly. Night setting with street lamps in background.

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Gentle, inviting expression. CLOTHING: black overcoat
- Cici: FACE REFERENCE ONLY. Touched, appreciative expression. CLOTHING: black coat, red scarf

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text or readable elements.
Leave space on LEFT for Kai's dialogue.
Leave space at BOTTOM for Cici's thought.
```

**中文文字:**
```
Kai：「请上车。」

Cici内心：「今晚被照顾得太好了...」
```

---

### Shot 34: 车内对话

**场景**: 车内，从副驾视角看Kai开车

| 字段 | 内容 |
|------|------|
| **shot_id** | 34 |
| **text_type** | dialogue |
| **text_position** | left, right |
| **speakers** | Cici, Kai |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

INTERIOR CAR SHOT from the passenger seat perspective. Shows Kai in the driver's seat, hands on the wheel, driving smoothly. His profile is visible, expression focused but relaxed.

The dashboard provides soft illumination. Outside the windshield, city lights blur past. The atmosphere inside is warm and intimate despite the car being in motion.

Kai wears his dark sweater (coat off while driving). His glasses reflect the passing lights. He occasionally glances toward the passenger seat (toward camera/Cici) with a warm smile.

The edge of the passenger seat shows Cici's presence - perhaps her hands, the edge of her red scarf, indicating she's watching him.

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Focused but happy while driving. CLOTHING: dark purple-black sweater, glasses

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any readable dashboard text or signs.
Leave space on LEFT for Cici's dialogue.
Leave space on RIGHT for Kai's dialogue.
```

**中文文字:**
```
Cici：「你开车很稳。」
Kai：「副驾有贵客，当然要稳。」
```

---

### Shot 35: 窗外夜景

**场景**: 车内，Cici看向窗外

| 字段 | 内容 |
|------|------|
| **shot_id** | 35 |
| **text_type** | narration_with_thought |
| **text_position** | top, bottom |
| **speaker** | Cici |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

INTERIOR CAR SHOT focusing on Cici in the passenger seat. She's gazing out the window, her face partially reflected in the glass. Her expression is peaceful and content, a soft smile on her lips.

Through the window, the Shanghai night cityscape flows by in beautiful bokeh - neon lights, building silhouettes, the magic of the city at night. Her reflection overlays these lights.

She wears her black knit sweater, coat draped over her lap. Her long wavy brown hair frames her face. The passing lights create changing illumination on her features.

EMOTIONAL ATMOSPHERE:
- Dreamy, peaceful contentment
- The city lights as backdrop to her thoughts
- Intimate car interior versus expansive city
- The quiet comfort of being with the right person

CHARACTER REFERENCE:
- Cici: FACE REFERENCE ONLY. Peaceful, content, dreamy expression. CLOTHING: black knit sweater

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any readable text or signs.
Leave space at TOP for narrative overlay.
Leave space at BOTTOM for thought overlay.
Her peaceful expression and the window reflection are the focus.
```

**中文文字:**
```
旁白：「窗外是流动的灯光，车内是安心的沉默。」

Cici内心：「原来，和对的人在一起，沉默也很舒服。」
```

---

## 第十一幕：告别 (Shots 36-41) ⭐ 情感重点3、4

---

### Shot 36: 到达楼下

**场景**: Cici家小区门口，车停在路边

| 字段 | 内容 |
|------|------|
| **shot_id** | 36 |
| **text_type** | narration |
| **text_position** | bottom |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

WIDE SHOT of a residential area entrance at night. A car is parked by the curb, and both figures have just gotten out, standing by the vehicle.

The residential entrance shows a modern Shanghai apartment complex - clean, well-lit entrance with some greenery. A security booth with soft light. The neighborhood is quiet, peaceful.

Both are back in their coats, standing close together by the car. Their body language shows reluctance to part - facing each other rather than walking toward the entrance.

Street lamps provide warm lighting. The night is deep but not too cold.

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Standing by car. CLOTHING: black overcoat
- Cici: FACE REFERENCE ONLY. Standing close to him. CLOTHING: black coat, red scarf

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any readable text or signs.
Leave clean space at BOTTOM (85-100%) for narrative overlay.
```

**中文文字:**
```
旁白：「太快了。她家到了。」
```

---

### Shot 37: 依依不舍

**场景**: 小区门口路灯下，两人面对面

| 字段 | 内容 |
|------|------|
| **shot_id** | 37 |
| **text_type** | dialogue |
| **text_position** | left, right |
| **speakers** | Cici, Kai |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

MEDIUM TWO-SHOT of the couple standing face to face under a street lamp near the residential entrance. The warm lamp light creates an intimate golden pool around them.

Both their expressions show reluctance to say goodbye - lingering, not wanting this moment to end.

Cici looks up at him with soft, grateful eyes. Her expression is tender, with a touch of sadness that the night is ending.

Kai looks down at her with warmth and the unspoken wish for more time. His expression is gentle, protective.

The quiet night surrounds them. Only the hum of the city in the far background.

CHARACTER REFERENCE:
- Cici: FACE REFERENCE ONLY. Tender, grateful, slightly sad expression. CLOTHING: black coat, red scarf
- Kai: FACE REFERENCE ONLY. Warm, protective, reluctant expression. CLOTHING: black overcoat, glasses

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text.
Leave space on LEFT for Cici's dialogue.
Leave space on RIGHT for Kai's dialogue.
```

**中文文字:**
```
Cici：「今天...真的很开心。谢谢你。」
Kai：「我也是。谢谢你愿意来见我。」
```

---

### Shot 38: 拥抱 ⭐【情感重点3：拥抱】

**场景**: 小区门口，Cici主动拥抱Kai

| 字段 | 内容 |
|------|------|
| **shot_id** | 38 |
| **text_type** | narration_with_thought |
| **text_position** | top, bottom |
| **speaker** | Kai |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

⭐ EMOTIONAL HIGHLIGHT SHOT ⭐

MEDIUM SHOT of an embrace under the warm glow of a street lamp. Cici has stepped forward and wrapped her arms around Kai. He embraces her back, his arms gentle around her.

The moment is tender and natural - not overly dramatic, but deeply emotional. Her face is pressed against his chest or shoulder. His chin might rest near the top of her head, expression showing touched surprise turning to gentle happiness.

VISUAL DETAILS:
- Warm golden street lamp light enveloping them
- Her long wavy hair visible, her red scarf contrasting with his dark coat
- Their body language shows comfort and trust
- Subtle mist or gentle bokeh in the night air adds romance

EMOTIONAL QUALITY:
- The courage of making the first move (her)
- The warmth of acceptance (him)
- A milestone moment in their connection

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Touched, gentle happiness. CLOTHING: black overcoat
- Cici: FACE REFERENCE ONLY (if visible). Content, brave. CLOTHING: black coat, red scarf

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text.
Leave space at TOP for narrative overlay.
Leave space at BOTTOM for thought overlay.
The embrace is the emotional center.
```

**中文文字:**
```
旁白：「她上前一步，抱住了他。没有犹豫。」

Kai内心：「她身上有淡淡的香味...像是...柑橘和茉莉。」
```

---

### Shot 39: 分开后对视

**场景**: 小区门口，两人分开，四目相对

| 字段 | 内容 |
|------|------|
| **shot_id** | 39 |
| **text_type** | none |
| **text_position** | none |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

CLOSE TWO-SHOT of the couple's faces very close together, having just separated from the embrace. The distance between them is only about 20 centimeters. The air between them is charged with tension and possibility.

Cici's eyes shine with emotion, looking up at him. Her expression holds warmth and something unspoken - the courage building for what comes next.

Kai's eyes behind his glasses are soft and deep, looking down at her. His expression shows tender wonder and restrained longing.

INTIMATE ATMOSPHERE:
- Extremely close proximity
- Warm street lamp lighting on their faces
- The suggestion of possibility hanging in the air
- Korean webtoon romantic tension - the moment before something happens
- Subtle sparkle effects around their eyes

CHARACTER REFERENCE:
- Cici: FACE REFERENCE ONLY. Emotional, eyes shining, courage building
- Kai: FACE REFERENCE ONLY. Tender wonder, restrained longing

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text.
This is a pure atmosphere shot - no text overlay needed.
Their eyes and the tension between them are everything.
```

**中文文字:**
```
（无文字，纯氛围画面）
```

---

### Shot 40: 脸颊之吻 ⭐【情感重点4：意外之吻】

**场景**: 小区门口，Cici踮脚亲吻Kai的脸颊

| 字段 | 内容 |
|------|------|
| **shot_id** | 40 |
| **text_type** | narration_with_dialogue |
| **text_position** | top, bottom |
| **speaker** | Cici |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

⭐ EMOTIONAL HIGHLIGHT SHOT - THE KISS ⭐

CLOSE-UP SHOT capturing the moment Cici rises on her tiptoes to place a gentle kiss on Kai's cheek.

Her lips are lightly touching his cheek - a soft, sweet gesture. Her eyes are closed in the act. Her long wavy hair frames her face, red scarf visible.

His expression is captured in the moment of surprised delight - eyes widening slightly, frozen in pleasant shock, a smile just beginning to form. His glasses catch the light.

ROMANTIC ELEMENTS:
- The height difference requiring her to tiptoe (romantic)
- Soft warm lighting on both faces
- Korean webtoon sparkle/glow effects
- The sweetness and innocence of a first kiss on the cheek
- Her brave initiative, his charmed reaction

CHARACTER REFERENCE:
- Cici: FACE REFERENCE ONLY. Eyes closed, tender kiss, on tiptoes. CLOTHING: glimpse of black coat, red scarf
- Kai: FACE REFERENCE ONLY. Surprised delight, eyes widening. CLOTHING: glimpse of black coat collar, glasses

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text.
Leave space at TOP for narrative overlay.
Leave space at BOTTOM for dialogue.
The kiss on the cheek is the absolute focus - beautiful and tender.
```

**中文文字:**
```
旁白：「她踮起脚，在他脸颊落下一个轻吻。」

Cici：「晚安。」
```

---

### Shot 41: Kai的反应

**场景**: 小区门口，Kai摸着被亲的脸颊微笑

| 字段 | 内容 |
|------|------|
| **shot_id** | 41 |
| **text_type** | thought |
| **text_position** | bottom |
| **speaker** | Kai |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

CLOSE-UP on Kai's face, capturing his reaction after the kiss. His hand is raised to touch the cheek where she kissed him.

His expression shows a progression of emotions: initial frozen surprise melting into a warm, blossoming smile of pure happiness. His eyes behind his glasses are soft, slightly dazed with joy.

The touch of his own hand on his cheek - savoring the lingering warmth of her kiss. His smile is genuine and unguarded - the kind of smile that transforms a serious face into something beautiful.

BACKGROUND:
- Soft blur of the night scene
- Warm street lamp glow
- Perhaps the distant blur of Cici walking away

EMOTIONAL QUALITY:
- The dawning realization of his feelings
- Pure, unfiltered happiness
- The moment he knows this is special

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Blossoming happy smile, hand on cheek. CLOTHING: black overcoat, glasses

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text.
Leave clean space at BOTTOM (85-100%) for thought overlay.
His transforming expression is the focus.
```

**中文文字:**
```
Kai内心：「这一刻，我知道...她就是那个人。」
```

---

## 第十二幕：余韵 (Shot 42)

---

### Shot 42: 目送与回眸

**场景**: 小区门口，Cici回头挥手，Kai目送

| 字段 | 内容 |
|------|------|
| **shot_id** | 42 |
| **text_type** | narration_with_dialogue |
| **text_position** | top, bottom |
| **speakers** | Cici, Kai |

**image_prompt:**
```
STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

WIDE to MEDIUM SHOT showing the final moment of the night. Two figures separated by some distance near the residential entrance.

IN FOREGROUND: Kai stands watching, his expression a soft, content smile. He raises one hand in a gentle wave.

IN BACKGROUND/MIDGROUND: Cici has walked toward the entrance but has turned back, waving at him. Her expression is radiant, happy, already looking forward to next time.

The scene captures the bittersweet beauty of parting - the physical distance between them contrasted with the emotional closeness they've built.

ATMOSPHERIC DETAILS:
- Warm street lamp creating pools of golden light
- The residential entrance softly lit behind Cici
- Perhaps bare winter trees framing the scene
- The romantic atmosphere of a winter night

CHARACTER REFERENCE:
- Kai (foreground): FACE REFERENCE ONLY. Content, soft smile, waving. CLOTHING: black overcoat
- Cici (background): FACE REFERENCE ONLY. Radiant smile, waving, turned back. CLOTHING: black coat, red scarf

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text.
Leave space at TOP for dialogue.
Leave space at BOTTOM for closing narrative.
The distance between them and their shared smiles tell the story.
```

**中文文字:**
```
Cici：「明天聊！」

旁白：「那个冬夜，思南路的风很轻，两颗心却跳得很快。」
旁白：「这是他们的开始。」
```

---

## 技术注意事项

### 参考图使用规范

1. **只用于脸部特征参考**
   - 面部轮廓、五官比例
   - 发型和发色
   - Kai的眼镜样式

2. **服装必须使用故事描述**
   - Cici: 黑色针织衫 + 浅灰色半身裙 + 黑色长大衣 + 红色丝巾
   - Kai: 黑紫色毛衣 + 深色牛仔裤 + 黑色大衣

3. **Prompt中的参考图指令格式**
   ```
   CHARACTER REFERENCE:
   - FACE REFERENCE ONLY from reference image
   - CLOTHING: [具体服装描述]
   ```

### 韩漫风格关键要素

| 要素 | 描述 |
|------|------|
| 面部特征 | 精致五官、大而有神的眼睛 |
| 光影 | 柔和渐变、暖色调 |
| 线条 | 干净清晰但不僵硬 |
| 情感表达 | 细腻微妙的表情变化 |
| 特效 | 适度的浪漫闪光效果 |
| 背景 | 详细但不喧宾夺主 |

### 文字叠加规范

| 文字类型 | 位置 | 背景 | 字色 |
|---------|------|------|------|
| 旁白 | top/bottom | 半透明黑底 | 白色 |
| 对话 | 靠近说话者 | 白色气泡 | 黑色 |
| 内心独白 | bottom | 半透明黑底 | 白色/斜体 |

---

## 完成状态

| 项目 | 状态 |
|------|------|
| 角色physical字段 | ✅ 完成 |
| 角色clothing字段 | ✅ 完成 |
| 42张Prompt | ✅ 完成 |
| 42张文字脚本 | ✅ 完成 |
| 情感重点镜头标注 | ✅ 完成 |

---

*AI-ML Agent 2026-01-30*
*HANDOFF-2026-01-30-011 交付物*
