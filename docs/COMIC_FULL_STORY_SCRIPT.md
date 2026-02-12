# 条漫完整故事脚本 - 《最后一碗面》

> **作者**: @AI-ML
> **日期**: 2026-01-22
> **关联任务**: HANDOFF-2026-01-22-009 / TASK-A
> **用途**: 配合 TextOverlayServiceV2 测试完整故事生成

---

## 故事信息

| 项目 | 内容 |
|------|------|
| **标题** | 最后一碗面 (The Last Bowl of Noodles) |
| **题材** | 父女亲情 |
| **主题** | 有些爱从不说出口，却记在心里一辈子 |
| **风格** | Ghibli-inspired warm illustration |
| **色调** | 暖黄 (warm yellow)、米白 (cream white)、浅褐 (light brown) |
| **图片数** | 15 |

---

## 角色设计 (Character Designs)

### 女儿 - 陈小雨 (Chen Xiaoyu)

#### 现在时期 (28岁)

| 字段 | 英文描述 |
|------|----------|
| **name** | Chen Xiaoyu |
| **name_en** | Chen Xiaoyu |
| **type** | human |
| **gender** | female |
| **age_appearance** | young_adult (28) |

**Physical Description:**
```
height: medium (165cm)
build: slim
skin_tone: fair with warm undertone
face_shape: oval with soft features
hair_color: jet black
hair_style: short modern bob cut, slightly above shoulders
hair_texture: straight and silky
eye_color: dark brown
eye_shape: almond, gentle
eye_size: medium
eyebrows: natural arch, well-groomed
nose: small and delicate
lips: soft pink, natural
distinctive_marks: small mole below left ear
```

**Clothing (Present Day):**
```
top: beige wool trench coat over crisp white blouse
bottom: black slim-fit dress pants
footwear: black leather flats
accessories: small gold stud earrings, simple black leather watch
style: urban professional elegant
```

#### 童年时期 (10岁)

**Physical Description:**
```
Same base features as adult, but:
face_shape: rounder, more childlike
hair_style: black twin pigtails with red hair ties
expression: bright, innocent, full of energy
```

**Clothing (Childhood Flashback):**
```
top: white short-sleeve school uniform shirt with red neckerchief
bottom: navy blue pleated skirt
footwear: white canvas shoes
accessories: red hair ties, simple backpack
style: elementary school uniform
```

#### 青春期 (18岁)

**Physical Description:**
```
Same base features, but:
face_shape: more defined than childhood
hair_style: black high ponytail, slightly messy
expression: rebellious, defiant
```

**Clothing (Teenage Flashback):**
```
top: oversized gray hoodie
bottom: dark blue jeans with rips at knees
footwear: worn white sneakers
accessories: simple black hair tie
style: casual rebellious teenager
```

---

### 父亲 - 陈国强 (Chen Guoqiang)

#### 现在时期 (55岁)

| 字段 | 英文描述 |
|------|----------|
| **name** | Chen Guoqiang |
| **name_en** | Chen Guoqiang |
| **type** | human |
| **gender** | male |
| **age_appearance** | middle_aged (55) |

**Physical Description:**
```
height: medium (170cm)
build: thin, slightly frail
skin_tone: weathered tan
face_shape: angular with prominent cheekbones
hair_color: salt and pepper gray, mostly white
hair_style: short and neat, thinning on top
hair_texture: coarse
eye_color: dark brown, warm
eye_shape: deep-set, gentle
eye_size: medium
eyebrows: bushy, graying
nose: straight, prominent
lips: thin, often curved in gentle smile
distinctive_marks: deep smile lines, weathered hands
```

**Clothing (Hospital):**
```
top: light blue hospital gown
bottom: hospital gown
footwear: none (in bed)
accessories: hospital wristband
style: patient attire
```

**Clothing (Home/Recovery):**
```
top: faded green plaid flannel shirt, well-worn
bottom: gray cotton pants
footwear: brown cloth slippers
accessories: reading glasses on a cord around neck
style: comfortable homewear
```

#### 回忆时期 (40岁)

**Physical Description:**
```
Same base features, but:
build: sturdy, strong from years of physical work
hair_color: jet black with few gray strands
face_shape: fuller, healthier
skin_tone: tanned from work
expression: warm, hardworking, content
```

**Clothing (Flashback - Noodle Shop):**
```
top: white sleeveless undershirt with white cotton apron, slightly stained from cooking
bottom: simple dark blue work pants
footwear: black cloth shoes
accessories: white towel over shoulder
style: working class noodle shop owner
```

---

## 风格指令 (Style Instructions)

### Ghibli-inspired 风格前缀

所有 image_prompt 开头必须添加：

```
STYLE: Ghibli-inspired warm illustration

Hand-drawn animation aesthetic inspired by Studio Ghibli.
Soft watercolor textures, warm color palette dominated by cream yellow, soft white, and light brown tones.
Gentle lighting with golden hour warmth. Detailed backgrounds with lived-in feeling.
Characters with expressive but understated emotions. Nostalgic, heartwarming atmosphere.

MUST INCLUDE: hand-drawn style, soft edges, warm color palette, gentle lighting, detailed backgrounds, nostalgic atmosphere
DO NOT USE: photorealistic, 3D render, harsh lighting, neon colors, Korean webtoon style, sharp digital lines
```

### 回忆场景特殊处理 (Shots 07-10)

回忆场景需要添加：

```
MEMORY SCENE TREATMENT:
- Soft golden glow around edges (vignette effect)
- Slightly desaturated colors compared to present-day scenes
- Dreamlike soft focus on background elements
- Warmer, more nostalgic color temperature
- Gentle lens flare or light particles floating in air
```

---

## 15图完整脚本 (Complete Script)

---

### Shot 01: 城市办公室 - 接到电话

**场景**: 现代办公室，女儿接到电话，表情凝重

| 字段 | 内容 |
|------|------|
| **shot_id** | 1 |
| **text_type** | narration |
| **speaker_position** | top |

**image_prompt:**
```
STYLE: Ghibli-inspired warm illustration

Hand-drawn animation aesthetic inspired by Studio Ghibli.
Soft watercolor textures, warm color palette dominated by cream yellow, soft white, and light brown tones.
Gentle lighting with golden hour warmth. Detailed backgrounds with lived-in feeling.
Characters with expressive but understated emotions. Nostalgic, heartwarming atmosphere.

MUST INCLUDE: hand-drawn style, soft edges, warm color palette, gentle lighting, detailed backgrounds, nostalgic atmosphere
DO NOT USE: photorealistic, 3D render, harsh lighting, neon colors, Korean webtoon style, sharp digital lines

---

A young professional woman with short black bob haircut, wearing a beige trench coat, standing in a modern office space. She is holding a phone to her ear, her expression shifting from neutral to deeply concerned. Her dark brown almond eyes widen slightly, lips parted in shock. One hand grips the phone tightly while the other hangs limply at her side.

The office has large windows letting in afternoon light, modern desks and computers visible in the soft-focus background. Warm afternoon sunlight streams through the windows, creating long shadows.

EMOTIONAL ATMOSPHERE:
The scene conveys sudden shock and dawning worry.
Character shows concerned, worried expression with widened eyes, slightly trembling hand holding phone, body frozen mid-motion.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the TOP (0-15% of image height) for narrative text overlay
- This area should have simple ceiling/window background for text readability
- Ensure character's face and worried expression remain clearly visible
- Character positioned in center-right of frame
```

**中文文字:**
```
那天接到电话，世界突然安静了
```

---

### Shot 02: 火车车窗 - 发呆

**场景**: 火车车厢内，女儿望着窗外发呆

| 字段 | 内容 |
|------|------|
| **shot_id** | 2 |
| **text_type** | thought |
| **speaker_position** | bottom |

**image_prompt:**
```
STYLE: Ghibli-inspired warm illustration

Hand-drawn animation aesthetic inspired by Studio Ghibli.
Soft watercolor textures, warm color palette dominated by cream yellow, soft white, and light brown tones.
Gentle lighting with golden hour warmth. Detailed backgrounds with lived-in feeling.
Characters with expressive but understated emotions. Nostalgic, heartwarming atmosphere.

MUST INCLUDE: hand-drawn style, soft edges, warm color palette, gentle lighting, detailed backgrounds, nostalgic atmosphere
DO NOT USE: photorealistic, 3D render, harsh lighting, neon colors, Korean webtoon style, sharp digital lines

---

A young woman with short black bob haircut sitting by a train window, her reflection faintly visible in the glass. She wears a beige trench coat, her posture slightly slumped. Her face shows distant, melancholic expression as she gazes out at the passing countryside - green rice fields and distant mountains blurred by the train's motion.

Late afternoon golden light streams through the window, casting warm shadows across her face. The train interior has worn but clean seats in muted green fabric. Other passengers are barely visible in soft blur.

EMOTIONAL ATMOSPHERE:
The scene conveys quiet anxiety and guilt, lost in worried thoughts.
Character shows pensive, distant expression with unfocused gaze, slight furrow between brows, hands clasped tightly in lap.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the BOTTOM (82-100% height) for thought text overlay
- This area should show simple train floor or seat edge for text readability
- Ensure character's profile and the window scenery remain the visual focus
- Character positioned in left side of frame, window taking right portion
```

**中文文字:**
```
三年没回去了...
```

---

### Shot 03: 乡村街道 - 冷清的面馆

**场景**: 小镇街道，面馆门口冷清

| 字段 | 内容 |
|------|------|
| **shot_id** | 3 |
| **text_type** | narration |
| **speaker_position** | bottom |

**image_prompt:**
```
STYLE: Ghibli-inspired warm illustration

Hand-drawn animation aesthetic inspired by Studio Ghibli.
Soft watercolor textures, warm color palette dominated by cream yellow, soft white, and light brown tones.
Gentle lighting with golden hour warmth. Detailed backgrounds with lived-in feeling.
Characters with expressive but understated emotions. Nostalgic, heartwarming atmosphere.

MUST INCLUDE: hand-drawn style, soft edges, warm color palette, gentle lighting, detailed backgrounds, nostalgic atmosphere
DO NOT USE: photorealistic, 3D render, harsh lighting, neon colors, Korean webtoon style, sharp digital lines

---

A quiet small-town street in rural China. In the center stands a modest noodle shop with a faded wooden sign (no text visible, weathered blank sign board). The shop entrance has traditional sliding doors, now closed. Dust motes float in the late afternoon light.

A young woman with short black bob haircut in beige trench coat stands before the closed shop, viewed from behind at a distance. Her small figure emphasizes the emptiness of the once-busy establishment. Wilted plants in pots flank the entrance. A few fallen leaves scattered on the ground.

The surrounding buildings are old but charming - whitewashed walls with dark wooden beams, traditional tile roofs. The street is nearly empty, creating a melancholic atmosphere.

NARRATIVE MOMENT:
This scene establishes the contrast between memory and present - the once-vibrant shop now quiet.
Visual focus on the closed shop and the daughter's small figure facing it.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the BOTTOM (82-100% height) for narrative text overlay
- This area should show simple ground/street surface for text readability
- The shop facade and daughter's figure should be in upper-center of frame
- Background buildings provide context without cluttering
```

**中文文字:**
```
记忆中总是热气腾腾的地方，如今门可罗雀
```

---

### Shot 04: 医院病房 - 见到父亲

**场景**: 医院病房，父女重逢

| 字段 | 内容 |
|------|------|
| **shot_id** | 4 |
| **text_type** | dialogue |
| **speaker_position** | left,right |

**image_prompt:**
```
STYLE: Ghibli-inspired warm illustration

Hand-drawn animation aesthetic inspired by Studio Ghibli.
Soft watercolor textures, warm color palette dominated by cream yellow, soft white, and light brown tones.
Gentle lighting with golden hour warmth. Detailed backgrounds with lived-in feeling.
Characters with expressive but understated emotions. Nostalgic, heartwarming atmosphere.

MUST INCLUDE: hand-drawn style, soft edges, warm color palette, gentle lighting, detailed backgrounds, nostalgic atmosphere
DO NOT USE: photorealistic, 3D render, harsh lighting, neon colors, Korean webtoon style, sharp digital lines

---

A hospital room scene. An elderly man with salt-and-pepper gray hair sits propped up in a hospital bed, wearing a light blue hospital gown. He has a thin, weathered face with deep smile lines, but his dark brown eyes are warm and gentle as he looks at his daughter. Despite being ill, he manages a reassuring smile.

A young woman with short black bob haircut in beige trench coat stands at the bedside, her expression showing shock at seeing her father so thin, mixed with guilt and relief. Her hands grip the bed railing, eyes glistening with unshed tears.

Soft afternoon light filters through white hospital curtains. Medical equipment visible but not prominent. A simple vase with wildflowers on the bedside table adds a touch of warmth.

CHARACTER EXPRESSION FOCUS:
Father: gentle, reassuring smile despite fatigue, warm eyes showing happiness at seeing his daughter.
Daughter: emotional turmoil - relief, guilt, sadness - eyes slightly red, lips pressed together to hold back tears.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space in upper left corner for daughter's dialogue bubble
- Leave clean space in upper right corner for father's dialogue bubble
- Both characters' faces should be clearly visible
- Hospital room background should be simple enough for text contrast
```

**中文文字:**
```
爸...

回来啦，别担心，小毛病
```

---

### Shot 05: 医院走廊 - 和医生交谈

**场景**: 医院走廊，女儿和医生谈话

| 字段 | 内容 |
|------|------|
| **shot_id** | 5 |
| **text_type** | narration |
| **speaker_position** | top |

**image_prompt:**
```
STYLE: Ghibli-inspired warm illustration

Hand-drawn animation aesthetic inspired by Studio Ghibli.
Soft watercolor textures, warm color palette dominated by cream yellow, soft white, and light brown tones.
Gentle lighting with golden hour warmth. Detailed backgrounds with lived-in feeling.
Characters with expressive but understated emotions. Nostalgic, heartwarming atmosphere.

MUST INCLUDE: hand-drawn style, soft edges, warm color palette, gentle lighting, detailed backgrounds, nostalgic atmosphere
DO NOT USE: photorealistic, 3D render, harsh lighting, neon colors, Korean webtoon style, sharp digital lines

---

A hospital corridor with soft fluorescent lighting. A young woman with short black bob haircut in beige trench coat listens intently to a doctor in white coat. Her body language shows concern - arms crossed protectively, shoulders slightly hunched, brow furrowed.

The doctor, a middle-aged woman with glasses and hair in a neat bun, holds a clipboard and speaks with professional but compassionate expression. They stand near a window where afternoon light creates a warm contrast to the clinical surroundings.

The corridor stretches behind them with soft-focus hospital elements - a nurse walking past, a wheelchair against the wall. The atmosphere conveys the weight of medical conversations.

EMOTIONAL ATMOSPHERE:
The scene conveys anxious concern and the heaviness of receiving difficult news.
Character shows worried expression with tight jaw, hands clasped nervously, leaning in to catch every word.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the TOP (0-15% of image height) for narrative text overlay
- Ceiling area should be simple for text readability
- Both figures should be visible in mid-frame
- Window light provides visual interest without cluttering text area
```

**中文文字:**
```
医生说要注意休息，我却不知道他一个人撑了多久
```

---

### Shot 06: 老屋客厅 - 看到全家福

**场景**: 老屋客厅，看到墙上全家福，触发回忆

| 字段 | 内容 |
|------|------|
| **shot_id** | 6 |
| **text_type** | narration |
| **speaker_position** | bottom |

**image_prompt:**
```
STYLE: Ghibli-inspired warm illustration

Hand-drawn animation aesthetic inspired by Studio Ghibli.
Soft watercolor textures, warm color palette dominated by cream yellow, soft white, and light brown tones.
Gentle lighting with golden hour warmth. Detailed backgrounds with lived-in feeling.
Characters with expressive but understated emotions. Nostalgic, heartwarming atmosphere.

MUST INCLUDE: hand-drawn style, soft edges, warm color palette, gentle lighting, detailed backgrounds, nostalgic atmosphere
DO NOT USE: photorealistic, 3D render, harsh lighting, neon colors, Korean webtoon style, sharp digital lines

---

PICTURE-IN-PICTURE ELEMENT - PHOTO FRAME:

A modest but cozy living room in an old Chinese home. Cream-colored walls slightly yellowed with age, dark wooden furniture. A young woman with short black bob haircut stands with her back partially to the viewer, looking up at a wall where a framed family photo hangs.

The photo frame (visible as element within the scene, no text on it) shows: a younger version of the father (black hair, sturdy build, white apron), a smiling woman (the late mother), and a little girl with twin pigtails, all standing in front of the noodle shop. The photo has faded, warm sepia tones.

Golden evening light streams through a window with lace curtains, dust motes floating in the beams. The room shows signs of a life lived alone - a single tea cup on the table, an old calendar, worn armchair.

The daughter reaches toward the photo, her expression showing nostalgia and dawning realization.

NARRATIVE MOMENT:
This scene establishes the transition into memory - the photo triggers flashback.
Visual focus on the contrast between the daughter's present form and the happy family in the photo.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the BOTTOM (82-100% height) for narrative text overlay
- Floor area should be simple for text readability
- The photo frame should be clearly visible in upper portion of frame
- Daughter positioned to show her emotional reaction to the photo
```

**中文文字:**
```
照片里的我们，笑得多开心
```

---

### Shot 07: 回忆 - 童年等待煮面

**场景**: 回忆场景，小女孩趴在桌上等爸爸煮面

| 字段 | 内容 |
|------|------|
| **shot_id** | 7 |
| **text_type** | dialogue |
| **speaker_position** | right,left |

**image_prompt:**
```
STYLE: Ghibli-inspired warm illustration

Hand-drawn animation aesthetic inspired by Studio Ghibli.
Soft watercolor textures, warm color palette dominated by cream yellow, soft white, and light brown tones.
Gentle lighting with golden hour warmth. Detailed backgrounds with lived-in feeling.
Characters with expressive but understated emotions. Nostalgic, heartwarming atmosphere.

MUST INCLUDE: hand-drawn style, soft edges, warm color palette, gentle lighting, detailed backgrounds, nostalgic atmosphere
DO NOT USE: photorealistic, 3D render, harsh lighting, neon colors, Korean webtoon style, sharp digital lines

MEMORY SCENE TREATMENT:
- Soft golden glow around edges (vignette effect)
- Slightly desaturated colors compared to present-day scenes
- Dreamlike soft focus on background elements
- Warmer, more nostalgic color temperature
- Gentle lens flare or light particles floating in air

---

A warm, nostalgic flashback scene inside a small noodle shop. A young girl (about 10 years old) with black twin pigtails tied with red ribbons, wearing a white school uniform shirt with red neckerchief, leans on a wooden table. Her chin rests on her folded arms, eyes bright with anticipation, a wide innocent smile on her round face.

Behind the counter in soft focus, her father (younger, 40 years old, with black hair and sturdy build) works at the stove. He wears a white sleeveless undershirt with a white apron, a towel draped over his shoulder. Steam rises from the cooking pots.

The shop interior is simple but warm - wooden tables and stools, steam rising, afternoon sun streaming through the open front. Paper lanterns hang from the ceiling (no text). The air seems filled with golden light particles, emphasizing the dreamlike quality of memory.

CHARACTER EXPRESSION FOCUS:
Little girl: eager anticipation, pure joy, bright eyes looking toward father.
Father: glimpsed in background, posture showing care and concentration on cooking.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space in upper right corner for child's dialogue bubble
- Leave clean space in upper left area for father's reply bubble
- Little girl should be prominent in foreground
- Father visible in background for context
```

**中文文字:**
```
爸爸，面好了吗？

马上好！
```

---

### Shot 08: 回忆 - 父亲端面

**场景**: 回忆场景，父亲端着热腾腾的面走来

| 字段 | 内容 |
|------|------|
| **shot_id** | 8 |
| **text_type** | narration |
| **speaker_position** | bottom |

**image_prompt:**
```
STYLE: Ghibli-inspired warm illustration

Hand-drawn animation aesthetic inspired by Studio Ghibli.
Soft watercolor textures, warm color palette dominated by cream yellow, soft white, and light brown tones.
Gentle lighting with golden hour warmth. Detailed backgrounds with lived-in feeling.
Characters with expressive but understated emotions. Nostalgic, heartwarming atmosphere.

MUST INCLUDE: hand-drawn style, soft edges, warm color palette, gentle lighting, detailed backgrounds, nostalgic atmosphere
DO NOT USE: photorealistic, 3D render, harsh lighting, neon colors, Korean webtoon style, sharp digital lines

MEMORY SCENE TREATMENT:
- Soft golden glow around edges (vignette effect)
- Slightly desaturated colors compared to present-day scenes
- Dreamlike soft focus on background elements
- Warmer, more nostalgic color temperature
- Gentle lens flare or light particles floating in air

---

A heartwarming flashback scene. The father (40 years old, black hair, sturdy build) walks toward the viewer carrying a large bowl of steaming noodles. He wears a white sleeveless undershirt with white apron, towel over shoulder. His face shows a warm, proud smile - the smile of a father providing for his child.

Steam rises from the bowl, creating a soft, ethereal effect. Golden afternoon light backlights the scene, creating a halo effect around the father's figure. The background shows the simple noodle shop interior in soft focus.

The perspective is from the child's point of view, looking up at this approaching figure. The bowl of noodles is prominently featured - simple but lovingly prepared.

EMOTIONAL ATMOSPHERE:
The scene conveys pure warmth, unconditional love, and the simple happiness of childhood.
The father's expression shows gentle pride and love, eyes crinkled with a warm smile.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the BOTTOM (82-100% height) for narrative text overlay
- Floor/table area should be simple for text readability
- Father and the bowl of noodles should dominate the upper-center frame
- Steam and light effects add emotional warmth
```

**中文文字:**
```
那时候觉得，这是世界上最好吃的面
```

---

### Shot 09: 回忆 - 青春期争吵

**场景**: 回忆场景，18岁的女儿冲父亲喊叫

| 字段 | 内容 |
|------|------|
| **shot_id** | 9 |
| **text_type** | dialogue |
| **speaker_position** | center |
| **emphasis** | red_highlight |

**image_prompt:**
```
STYLE: Ghibli-inspired warm illustration

Hand-drawn animation aesthetic inspired by Studio Ghibli.
Soft watercolor textures, warm color palette dominated by cream yellow, soft white, and light brown tones.
Gentle lighting with golden hour warmth. Detailed backgrounds with lived-in feeling.
Characters with expressive but understated emotions. Nostalgic, heartwarming atmosphere.

MUST INCLUDE: hand-drawn style, soft edges, warm color palette, gentle lighting, detailed backgrounds, nostalgic atmosphere
DO NOT USE: photorealistic, 3D render, harsh lighting, neon colors, Korean webtoon style, sharp digital lines

MEMORY SCENE TREATMENT:
- Soft golden glow around edges (vignette effect)
- Slightly desaturated colors compared to present-day scenes
- Dreamlike soft focus on background elements
- Warmer, more nostalgic color temperature
- This scene has heavier, more melancholic tone within the memory palette

---

An emotionally intense flashback scene. A teenage girl (18 years old) with black high ponytail, wearing an oversized gray hoodie and ripped jeans, stands in the old family home. Her posture is aggressive - shoulders squared, fists clenched, mouth open in a shout. Her expression shows teenage rebellion and frustration - eyes blazing, brows drawn together in anger.

Facing her, the father (40 years old) stands with slumped shoulders, still in his work apron. His expression shows hurt mixed with patience - eyes sad but understanding, weathered face showing the pain of a parent watching their child pull away.

The living room setting is simple. Evening light casts long shadows. The atmosphere is tense, a moment frozen in time that clearly haunts the daughter's memory.

CHARACTER EXPRESSION FOCUS:
Teenage daughter: defiant anger, shouting, rebellious fire in eyes - but underneath, a scared child wanting to escape small-town life.
Father: deeply hurt but restrained, the pain of unconditional love being rejected visible in his slumped posture.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the CENTER (40-60% height) for emphasized dialogue
- This area will have RED HIGHLIGHT text showing the daughter's hurtful words
- Both figures should be visible, daughter more prominent
- Background simple enough for text contrast
```

**中文文字:**
```
我长大后一定要离开这个破地方！！！
```

**文字效果说明:**
- 使用红色高亮效果（red_highlight）
- "！！！" 触发情感强调
- 字体略大，表达强烈情感

---

### Shot 10: 回忆 - 车站送别

**场景**: 回忆场景，父亲在车站送女儿

| 字段 | 内容 |
|------|------|
| **shot_id** | 10 |
| **text_type** | narration |
| **speaker_position** | bottom |

**image_prompt:**
```
STYLE: Ghibli-inspired warm illustration

Hand-drawn animation aesthetic inspired by Studio Ghibli.
Soft watercolor textures, warm color palette dominated by cream yellow, soft white, and light brown tones.
Gentle lighting with golden hour warmth. Detailed backgrounds with lived-in feeling.
Characters with expressive but understated emotions. Nostalgic, heartwarming atmosphere.

MUST INCLUDE: hand-drawn style, soft edges, warm color palette, gentle lighting, detailed backgrounds, nostalgic atmosphere
DO NOT USE: photorealistic, 3D render, harsh lighting, neon colors, Korean webtoon style, sharp digital lines

MEMORY SCENE TREATMENT:
- Soft golden glow around edges (vignette effect)
- Slightly desaturated colors compared to present-day scenes
- Dreamlike soft focus on background elements
- Warmer, more nostalgic color temperature
- Bittersweet, poignant atmosphere

---

A poignant flashback at a small-town train station. The father (40 years old, black hair, wearing his simple dark work clothes) walks alongside his daughter (18, in casual clothes with a large travel bag). He carries her heavy suitcase, his posture slightly bent under its weight.

The platform is simple - concrete with a faded yellow safety line, old wooden bench, a single lamp post. Early morning light creates long shadows. In the background, an old green train waits.

The father's expression shows restrained emotion - he doesn't look at his daughter, focusing on the task of carrying her luggage, but his jaw is tight and his eyes show deep sadness. He's the type who shows love through action, not words.

The teenage daughter walks slightly ahead, already looking toward the train, toward her future - not seeing her father's quiet heartbreak.

EMOTIONAL ATMOSPHERE:
The scene conveys unspoken love, the pain of letting go, and the gulf between generations.
Visual focus on the father's silent devotion - carrying her bags even after being hurt by her words.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the BOTTOM (82-100% height) for narrative text overlay
- Platform ground area should be simple for text readability
- Both figures walking, father slightly behind, emphasizes the emotional distance
- Train in background provides context
```

**中文文字:**
```
他什么都没说，只是帮我拎行李
```

---

### Shot 11: 现实 - 厨房发现笔记本

**场景**: 回到现实，女儿在老屋厨房发现泛黄笔记本

| 字段 | 内容 |
|------|------|
| **shot_id** | 11 |
| **text_type** | narration |
| **speaker_position** | top |

**image_prompt:**
```
STYLE: Ghibli-inspired warm illustration

Hand-drawn animation aesthetic inspired by Studio Ghibli.
Soft watercolor textures, warm color palette dominated by cream yellow, soft white, and light brown tones.
Gentle lighting with golden hour warmth. Detailed backgrounds with lived-in feeling.
Characters with expressive but understated emotions. Nostalgic, heartwarming atmosphere.

MUST INCLUDE: hand-drawn style, soft edges, warm color palette, gentle lighting, detailed backgrounds, nostalgic atmosphere
DO NOT USE: photorealistic, 3D render, harsh lighting, neon colors, Korean webtoon style, sharp digital lines

---

Back to present day. An old kitchen in the family home - simple wooden cabinets, gas stove, well-worn countertops. Everything speaks of years of cooking, of a life dedicated to the noodle shop.

The daughter (28, short black bob, now in a simple white blouse with sleeves rolled up) kneels by an open cabinet, having discovered a weathered notebook on a shelf. She holds it with both hands, her expression showing curiosity turning to realization.

The notebook is old and worn - yellowed pages, faded cover, clearly used for many years. Evening light streams through a small window, dust motes floating in the golden beam.

Around her, the kitchen shows signs of her father's life - jars of dried ingredients, worn cooking utensils, a calendar several months behind.

EMOTIONAL ATMOSPHERE:
The scene conveys discovery and dawning realization.
Character shows surprised, curious expression with slightly parted lips, eyes widening as she begins to understand the notebook's significance.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy
- NO text visible on the notebook cover

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the TOP (0-15% of image height) for narrative text overlay
- Ceiling/upper cabinet area should be simple for text readability
- Character kneeling with notebook should be in center-lower frame
- The notebook is the key visual element - should be clearly visible
```

**中文文字:**
```
在厨房角落，我看到一本旧笔记本
```

---

### Shot 12: 特写 - 笔记本内容

**场景**: 特写镜头，笔记本翻开的内页

| 字段 | 内容 |
|------|------|
| **shot_id** | 12 |
| **text_type** | narration |
| **speaker_position** | top |

**image_prompt:**
```
STYLE: Ghibli-inspired warm illustration

Hand-drawn animation aesthetic inspired by Studio Ghibli.
Soft watercolor textures, warm color palette dominated by cream yellow, soft white, and light brown tones.
Gentle lighting with golden hour warmth. Detailed backgrounds with lived-in feeling.
Characters with expressive but understated emotions. Nostalgic, heartwarming atmosphere.

MUST INCLUDE: hand-drawn style, soft edges, warm color palette, gentle lighting, detailed backgrounds, nostalgic atmosphere
DO NOT USE: photorealistic, 3D render, harsh lighting, neon colors, Korean webtoon style, sharp digital lines

---

A close-up shot of an opened, weathered notebook held in feminine hands. The pages are yellowed with age, filled with neat but simple handwriting (DO NOT show actual text - only suggest handwriting through abstract line patterns that resemble writing but are not legible).

The hands holding the notebook show slight trembling - delicate fingers with short nails, a small gold watch visible on the wrist. The hands press the pages open with gentle reverence.

The notebook pages show various abstract elements suggesting content: neat lines suggesting a list format, small symbols suggesting check marks or notes, occasional darker marks suggesting emphasis - all without any actual readable text.

Warm golden light illuminates the pages. A single tear drop has fallen on the page, creating a small water mark. The background is soft blur of the wooden kitchen surface.

EMOTIONAL ATMOSPHERE:
The scene conveys revelation and emotional impact.
The focus is on the artifact of love - the notebook representing years of silent care.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy
- DO NOT include any legible writing - only abstract patterns suggesting handwriting

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the TOP (0-18% height) for narrative text overlay
- This area should show blurred background for text readability
- The notebook pages should fill most of the frame
- Hands visible at edges to show human connection to the object
```

**中文文字:**
```
"女儿喜欢的口味"——不爱香菜、多放葱花、汤要清淡...
```

---

### Shot 13: 现实 - 泪流满面

**场景**: 女儿在厨房泪流满面

| 字段 | 内容 |
|------|------|
| **shot_id** | 13 |
| **text_type** | thought |
| **speaker_position** | bottom |

**image_prompt:**
```
STYLE: Ghibli-inspired warm illustration

Hand-drawn animation aesthetic inspired by Studio Ghibli.
Soft watercolor textures, warm color palette dominated by cream yellow, soft white, and light brown tones.
Gentle lighting with golden hour warmth. Detailed backgrounds with lived-in feeling.
Characters with expressive but understated emotions. Nostalgic, heartwarming atmosphere.

MUST INCLUDE: hand-drawn style, soft edges, warm color palette, gentle lighting, detailed backgrounds, nostalgic atmosphere
DO NOT USE: photorealistic, 3D render, harsh lighting, neon colors, Korean webtoon style, sharp digital lines

---

An emotionally powerful scene. The daughter (28, short black bob) sits on the kitchen floor, back against the cabinets, knees drawn up. The notebook rests in her lap. Tears stream down her face freely, her expression showing deep emotional release - not dramatic sobbing, but quiet, profound tears of realization and regret.

Her eyes are red-rimmed, looking down at the notebook but seeing something beyond it - understanding finally what her father's love looked like. One hand covers her mouth, the other clutches the notebook.

Evening light creates a warm glow, but shadows fill the corners of the kitchen. The atmosphere is intimate, private - a moment of transformation.

EMOTIONAL ATMOSPHERE:
The scene conveys catharsis, revelation, and the bittersweet pain of understanding too late.
Character shows deep emotion - tears, slightly shaking shoulders, the weight of years of distance suddenly clear.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the BOTTOM (82-100% height) for thought text overlay
- Floor area should provide contrast for text
- Character fills most of the frame, emphasizing emotional intensity
- The notebook visible in her lap connects to previous shot
```

**中文文字:**
```
原来每一碗面，都是他在说"我爱你"
```

---

### Shot 14: 医院病房 - 端面给父亲

**场景**: 女儿端着亲手做的面给住院的父亲

| 字段 | 内容 |
|------|------|
| **shot_id** | 14 |
| **text_type** | dialogue |
| **speaker_position** | left,right |

**image_prompt:**
```
STYLE: Ghibli-inspired warm illustration

Hand-drawn animation aesthetic inspired by Studio Ghibli.
Soft watercolor textures, warm color palette dominated by cream yellow, soft white, and light brown tones.
Gentle lighting with golden hour warmth. Detailed backgrounds with lived-in feeling.
Characters with expressive but understated emotions. Nostalgic, heartwarming atmosphere.

MUST INCLUDE: hand-drawn style, soft edges, warm color palette, gentle lighting, detailed backgrounds, nostalgic atmosphere
DO NOT USE: photorealistic, 3D render, harsh lighting, neon colors, Korean webtoon style, sharp digital lines

---

A warm, redemptive scene in the hospital room. The daughter (28, short black bob, wearing a soft cream sweater) stands beside her father's hospital bed, carefully holding out a bowl of steaming noodles wrapped in a cloth to keep warm.

Her expression shows nervous hope - a small, vulnerable smile, eyes seeking approval, posture slightly leaning forward. She's made this simple dish with all her love, trying to give back what she received.

The father (55, gray hair, in hospital gown but sitting up stronger than before) looks at the bowl with genuine surprise, then up at his daughter. His eyes glisten with emotion, deep smile lines crinkling as he begins to smile - not at the food, but at his daughter's gesture of love.

Morning sunlight streams through the window, creating a warm, hopeful atmosphere. The simple hospital room feels transformed by this moment of connection.

CHARACTER EXPRESSION FOCUS:
Daughter: hopeful, vulnerable, seeking connection - a child again wanting to please her father.
Father: deeply moved, surprised, overflowing with unspoken emotion - seeing his daughter truly for the first time in years.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space in upper left corner for daughter's dialogue bubble
- Leave clean space in upper right area for father's response bubble
- Both faces should be clearly visible with their emotional expressions
- The bowl of noodles between them serves as visual bridge
```

**中文文字:**
```
爸，我煮的，你尝尝

...还是那个味道
```

---

### Shot 15: 面馆门口 - 新店招亮起

**场景**: 面馆重新开张，新店招亮起，女儿站在门口

| 字段 | 内容 |
|------|------|
| **shot_id** | 15 |
| **text_type** | narration |
| **speaker_position** | bottom |

**image_prompt:**
```
STYLE: Ghibli-inspired warm illustration

Hand-drawn animation aesthetic inspired by Studio Ghibli.
Soft watercolor textures, warm color palette dominated by cream yellow, soft white, and light brown tones.
Gentle lighting with golden hour warmth. Detailed backgrounds with lived-in feeling.
Characters with expressive but understated emotions. Nostalgic, heartwarming atmosphere.

MUST INCLUDE: hand-drawn style, soft edges, warm color palette, gentle lighting, detailed backgrounds, nostalgic atmosphere
DO NOT USE: photorealistic, 3D render, harsh lighting, neon colors, Korean webtoon style, sharp digital lines

---

The final scene - a hopeful new beginning. The small-town noodle shop, now revitalized. The building has been cleaned and refreshed, maintaining its traditional charm but with new life. Warm light glows from within, steam visible through the windows. Plants in new pots flank the entrance.

A new wooden sign hangs above the door (no text visible - just a clean, fresh wooden board suggesting renewal). Paper lanterns glow with warm light. The shop door is open, inviting.

The daughter (28, now wearing a simple white blouse with a white apron - echoing her father's work attire) stands in the doorway, arms at her sides, looking out at the street with a peaceful, determined expression. Her posture is straight, confident - she has found her place.

Golden hour sunlight bathes the scene in warm amber tones. A few villagers walk past, glancing at the reopened shop with interest. The atmosphere conveys hope, continuity, and the cycle of love passing between generations.

NARRATIVE MOMENT:
This scene establishes resolution - the daughter carrying on her father's legacy, love expressed through action.
Visual focus on the transformed shop and the daughter's new role as its keeper.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy
- NO text on the shop sign - just a blank wooden board

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the BOTTOM (82-100% height) for narrative text overlay (the key quote)
- Ground/street area should be simple for the important closing text
- The shop facade and daughter in doorway should fill upper portion
- Warm light and atmosphere emphasize hopeful resolution
```

**中文文字:**
```
有些爱从不说出口，却记在心里一辈子
```

---

## 文字叠加配置汇总

| Shot | text_type | speaker_position | emphasis | 预留区域 |
|------|-----------|------------------|----------|----------|
| 01 | narration | top | - | TOP (0-15%) |
| 02 | thought | bottom | - | BOTTOM (82-100%) |
| 03 | narration | bottom | - | BOTTOM (82-100%) |
| 04 | dialogue | left,right | - | upper-left, upper-right |
| 05 | narration | top | - | TOP (0-15%) |
| 06 | narration | bottom | - | BOTTOM (82-100%) |
| 07 | dialogue | right,left | - | upper-right, upper-left |
| 08 | narration | bottom | - | BOTTOM (82-100%) |
| 09 | dialogue | center | **red_highlight** | CENTER (40-60%) |
| 10 | narration | bottom | - | BOTTOM (82-100%) |
| 11 | narration | top | - | TOP (0-15%) |
| 12 | narration | top | - | TOP (0-18%) |
| 13 | thought | bottom | - | BOTTOM (82-100%) |
| 14 | dialogue | left,right | - | upper-left, upper-right |
| 15 | narration | bottom | - | BOTTOM (82-100%) |

---

## 技术验证覆盖

| 验证项 | 对应Shot | 说明 |
|--------|----------|------|
| 叙事旁白（顶部） | 01, 05, 11, 12 | 黑底白字，顶部 |
| 叙事旁白（底部） | 03, 06, 08, 10, 15 | 黑底白字，底部 |
| 心理描写 | 02, 13 | 第一人称内心独白 |
| 对话气泡（单人） | - | 本故事未使用 |
| 对话气泡（双人） | 04, 07, 14 | 父女对话 |
| **情感强调** | **09** | "破地方!!!" **红色高亮**（英文感叹号触发） |
| 回忆场景 | 07-10 | 柔光/褪色处理 |
| 画中画 | 06 | 全家福照片 |
| 特写镜头 | 12 | 笔记本内容 |

---

## 版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| v1.0 | 2026-01-22 | 初版，15图完整脚本 |
