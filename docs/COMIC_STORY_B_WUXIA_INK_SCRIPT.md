# 条漫完整故事脚本 - 故事B《断剑》

> **作者**: @AI-ML
> **日期**: 2026-01-27
> **关联任务**: TASK-VERIFY-001-B
> **用途**: 多风格通用性验证测试 - 古装武侠 + 水墨风格

---

## 故事信息

| 项目 | 内容 |
|------|------|
| **标题** | 断剑 (The Broken Sword) |
| **题材** | 古装武侠 |
| **主题** | 剑可断，义不可断 |
| **风格** | Chinese Ink Wash (水墨) |
| **色调** | 墨黑 (ink black)、宣纸白 (rice paper white)、淡灰 (light gray)、点缀暖褐 (subtle warm brown) |
| **图片数** | 15 |

---

## 角色设计 (Character Designs)

### 老剑客/师父 - 白川 (master_old)

| 字段 | 英文描述 |
|------|----------|
| **id** | master_old |
| **name** | 白川 |
| **name_en** | Bai Chuan |
| **type** | human |
| **gender** | male |
| **age_appearance** | elderly (60) |

**Physical Description:**
```
height: tall (180cm)
build: thin but wiry, lean from years of martial arts
skin_tone: weathered pale, like aged parchment
face_shape: angular with high cheekbones, gaunt
hair_color: pure white
hair_style: long white hair tied in traditional topknot (发髻), some loose strands framing face
hair_texture: fine, flowing
eye_color: deep gray, almost black
eye_shape: narrow, piercing
eye_size: small but intense
eyebrows: long white eyebrows, slightly drooping at ends
nose: straight, prominent bridge
lips: thin, often pressed in contemplation
distinctive_marks: deep vertical furrow between brows, prominent veins on hands, old sword scar on left cheek
facial_hair: long flowing white beard reaching chest
```

**Clothing:**
```
top: plain undyed hemp robe (麻布长袍) with wide sleeves, faded to cream-gray, simple cloth belt at waist
inner: simple white inner robe visible at collar
bottom: matching loose hemp trousers
footwear: black cloth shoes (布鞋)
accessories: ancient sword with worn leather-wrapped hilt at waist, jade pendant on simple cord
style: ascetic swordsman hermit
```

---

### 年轻白川 (master_young) - 回忆场景用

| 字段 | 英文描述 |
|------|----------|
| **id** | master_young |
| **name** | 白川 (年轻) |
| **name_en** | Bai Chuan (Young) |
| **type** | human |
| **gender** | male |
| **age_appearance** | adult (30) |

**Physical Description:**
```
Same base features as master_old, but:
height: tall (180cm)
build: athletic and strong, peak martial arts condition
skin_tone: healthy fair with slight tan
face_shape: angular with high cheekbones, fuller than old age
hair_color: jet black with bluish sheen
hair_style: long black hair tied in high topknot, sleek and well-groomed
eye_color: dark gray, intense and confident
eye_shape: narrow, sharp with arrogant gleam
eyebrows: thick black, angled upward showing pride
expression: confident, arrogant, full of vigor
distinctive_marks: no beard, clean-shaven jaw, no scar yet
```

**Clothing (Flashback - Peak Years):**
```
top: fine dark blue silk robe (深蓝绸袍) with subtle wave pattern, silver-trimmed edges
inner: white silk inner robe
bottom: matching dark blue silk trousers
footwear: black leather boots
accessories: famous sword "寒霜" (Frost) at waist - blade gleaming, jade hairpin holding topknot
style: renowned swordsman at height of fame
```

---

### 徒弟 - 林风 (disciple)

| 字段 | 英文描述 |
|------|----------|
| **id** | disciple |
| **name** | 林风 |
| **name_en** | Lin Feng |
| **type** | human |
| **gender** | male |
| **age_appearance** | young_adult (25) |

**Physical Description:**
```
height: medium-tall (175cm)
build: lean and athletic, lithe swordsman build
skin_tone: healthy fair with slight warmth
face_shape: oval with defined jawline
hair_color: jet black
hair_style: high ponytail (高马尾) tied with white ribbon, some loose strands
hair_texture: thick and slightly wavy
eye_color: bright brown, earnest
eye_shape: almond, wide and clear
eye_size: medium-large, expressive
eyebrows: straight and thick, showing determination
nose: straight, youthful
lips: natural, often set in determined expression
distinctive_marks: small scar on right hand from training
```

**Clothing:**
```
top: deep blue martial arts jacket (蓝色劲装) with mandarin collar, fitted cut for movement
inner: white inner shirt visible at collar
bottom: dark gray fitted trousers tucked into boots
footwear: black leather boots with cloth wrapping at ankles
accessories: white cloth belt (白色束带), plain steel sword at waist, white hair ribbon
style: disciplined martial arts student
```

---

### 蒙面仇人 - 周沧 (enemy)

| 字段 | 英文描述 |
|------|----------|
| **id** | enemy |
| **name** | 周沧 |
| **name_en** | Zhou Cang |
| **type** | human |
| **gender** | male |
| **age_appearance** | middle_aged (50) |

**Physical Description:**
```
height: medium (170cm)
build: lean but powerful, compact and dangerous
skin_tone: weathered tan, sun-damaged
face_shape: square jaw, harsh features (revealed in Shot 14)
hair_color: iron gray with black streaks
hair_style: pulled back tight, hidden under hood/mask
eye_color: dark brown, filled with cold hatred (only visible part when masked)
eye_shape: narrow, cold
eye_size: small, intense
eyebrows: thick, perpetually furrowed
nose: crooked, broken once
lips: thin, cruel set (when unmasked)
distinctive_marks: deep crow's feet from years of hatred, burn scar on left hand
```

**Clothing (Masked):**
```
top: black night-traveling clothes (黑色夜行衣), fitted and practical
face_covering: black cloth mask covering lower face, black hood covering hair
bottom: black fitted trousers
footwear: soft black cloth shoes for silent movement
accessories: thin black sword (细长黑剑) on back, throwing knives hidden in sleeves
style: assassin/avenger
```

**Clothing (Unmasked - Shot 14-15):**
```
Same outfit but mask and hood removed, revealing aged weathered face
expression shifts from cold hatred to complex emotions - grief, recognition, reluctant respect
```

---

## 风格指令 (Style Instructions)

### Chinese Ink Wash (水墨) 风格前缀

所有 image_prompt 开头必须添加：

```
STYLE: Chinese Ink Wash Painting (水墨画)

Traditional Chinese ink wash aesthetic (sumi-e inspired).
Brush stroke textures, ink gradients from deep black to pale gray.
Rice paper texture background with intentional white space (留白).
Minimal color - primarily black, gray, white with occasional subtle warm accents.
Flowing, dynamic brush energy. Atmospheric perspective through ink density.
Characters rendered with bold decisive strokes. Backgrounds fade into mist.

MUST INCLUDE: brush stroke texture, ink wash gradients, rice paper feel, intentional white space, atmospheric depth, flowing lines, traditional Chinese aesthetic
DO NOT USE: photorealistic, colorful, neon, 3D render, Western art style, digital art look, sharp clean lines, bright saturated colors
```

### 回忆场景特殊处理 (Shots 04-06)

回忆场景需要添加：

```
MEMORY SCENE TREATMENT:
- Warmer sepia-tinted ink tones
- Softer brush strokes with more blur
- Dreamlike quality with hazier edges
- Lighter overall ink density
- Subtle golden warmth mixed into grays
```

### 动作场景处理 (Shots 10-11)

动作场景需要添加：

```
ACTION SCENE TREATMENT:
- Dynamic brush strokes showing movement
- Ink splatter effects for impact
- White space used to represent sword flash/speed
- Bamboo leaves scattered in motion
- Energy lines through negative space
```

---

## 15图完整脚本 (Complete Script)

---

### Shot 01: 雪夜独坐

**场景**: 山间凉亭，大雪纷飞，老剑客独坐回忆

| 字段 | 内容 |
|------|------|
| **shot_id** | 1 |
| **text_type** | narration |
| **speaker_position** | top |
| **characters_in_scene** | master_old |

**image_prompt:**
```
STYLE: Chinese Ink Wash Painting (水墨画)

Traditional Chinese ink wash aesthetic (sumi-e inspired).
Brush stroke textures, ink gradients from deep black to pale gray.
Rice paper texture background with intentional white space (留白).
Minimal color - primarily black, gray, white with occasional subtle warm accents.
Flowing, dynamic brush energy. Atmospheric perspective through ink density.
Characters rendered with bold decisive strokes. Backgrounds fade into mist.

MUST INCLUDE: brush stroke texture, ink wash gradients, rice paper feel, intentional white space, atmospheric depth, flowing lines, traditional Chinese aesthetic
DO NOT USE: photorealistic, colorful, neon, 3D render, Western art style, digital art look, sharp clean lines, bright saturated colors

---

A distant view of a simple wooden pavilion (凉亭) in a mountain bamboo grove during heavy snowfall. An elderly swordsman with long white hair tied in topknot and flowing white beard sits alone inside, his back slightly hunched, gazing at an ancient sword across his lap.

The bamboo stalks are rendered in bold vertical brush strokes, fading into misty white at the top. Snow falls as scattered white dots against the gray ink sky. The pavilion is a dark silhouette providing shelter from the elements.

The old man's hemp robe drapes heavily, his posture conveying decades of solitude and regret. Moonlight filters through clouds, creating subtle silver highlights on the snow.

EMOTIONAL ATMOSPHERE:
Deep solitude, heavy memories, the weight of three decades of guilt.
The vast empty space around the small pavilion emphasizes isolation.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
三十年了，那一剑，始终刺在我心里。
```

---

### Shot 02: 凝视断剑

**场景**: 凉亭内，特写老剑客手持有裂痕的古剑

| 字段 | 内容 |
|------|------|
| **shot_id** | 2 |
| **text_type** | thought |
| **speaker_position** | bottom |
| **characters_in_scene** | master_old |

**image_prompt:**
```
STYLE: Chinese Ink Wash Painting (水墨画)

Traditional Chinese ink wash aesthetic (sumi-e inspired).
Brush stroke textures, ink gradients from deep black to pale gray.
Rice paper texture background with intentional white space (留白).
Minimal color - primarily black, gray, white with occasional subtle warm accents.
Flowing, dynamic brush energy. Atmospheric perspective through ink density.
Characters rendered with bold decisive strokes. Backgrounds fade into mist.

MUST INCLUDE: brush stroke texture, ink wash gradients, rice paper feel, intentional white space, atmospheric depth, flowing lines, traditional Chinese aesthetic
DO NOT USE: photorealistic, colorful, neon, 3D render, Western art style, digital art look, sharp clean lines, bright saturated colors

---

Close-up view of an elderly swordsman's weathered hands holding an ancient sword. The blade has a visible crack running along its length - a permanent wound in the steel. His long white beard partially visible, his gaunt face with scar on left cheek shown in profile, piercing gray eyes filled with sorrow gazing at the damaged blade.

The sword's worn leather-wrapped hilt shows decades of use. His hands are thin with prominent veins, trembling slightly. Snow continues falling outside the pavilion frame.

Ink rendering focuses on the hands and sword with fine detailed brush work, while the background fades to misty gray. A single tear track suggested on his weathered cheek.

EMOTIONAL ATMOSPHERE:
Guilt, regret, the physical reminder of an irreversible mistake.
The crack in the sword mirrors the crack in his heart.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
这道裂痕，是我亲手造成的...
```

---

### Shot 03: 记忆浮现

**场景**: 雪花中浮现年轻剑客的虚影，过渡到回忆

| 字段 | 内容 |
|------|------|
| **shot_id** | 3 |
| **text_type** | narration |
| **speaker_position** | bottom |
| **characters_in_scene** | master_old, master_young |

**image_prompt:**
```
STYLE: Chinese Ink Wash Painting (水墨画)

Traditional Chinese ink wash aesthetic (sumi-e inspired).
Brush stroke textures, ink gradients from deep black to pale gray.
Rice paper texture background with intentional white space (留白).
Minimal color - primarily black, gray, white with occasional subtle warm accents.
Flowing, dynamic brush energy. Atmospheric perspective through ink density.
Characters rendered with bold decisive strokes. Backgrounds fade into mist.

MUST INCLUDE: brush stroke texture, ink wash gradients, rice paper feel, intentional white space, atmospheric depth, flowing lines, traditional Chinese aesthetic
DO NOT USE: photorealistic, colorful, neon, 3D render, Western art style, digital art look, sharp clean lines, bright saturated colors

---

A transition scene showing the old swordsman looking toward swirling snow, within which a ghostly vision appears - his younger self. The old man with white hair and beard sits in the pavilion corner (rendered in solid dark ink), while in the snowy void before him, a translucent figure of a young swordsman with black hair in high topknot emerges from the snowflakes.

The young vision wears fine dark blue silk robes, standing proudly with hand on famous sword, expression confident and arrogant. This phantom is rendered in lighter, hazier brush strokes - barely there, a memory taking shape.

The contrast between the hunched old man and his proud young ghost creates visual tension. Snowflakes swirl between them like the years that have passed.

EMOTIONAL ATMOSPHERE:
Nostalgia, painful memory surfacing, the unbridgeable gap between past and present self.
Past glory haunting present regret.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
那一年，我还是江湖人人敬仰的"白川一剑"...
```

---

### Shot 04: 年少意气 (回忆)

**场景**: 三十年前，热闹的江湖客栈，年轻白川意气风发

| 字段 | 内容 |
|------|------|
| **shot_id** | 4 |
| **text_type** | dialogue |
| **speaker_position** | center |
| **characters_in_scene** | master_young |

**image_prompt:**
```
STYLE: Chinese Ink Wash Painting (水墨画)

Traditional Chinese ink wash aesthetic (sumi-e inspired).
Brush stroke textures, ink gradients from deep black to pale gray.
Rice paper texture background with intentional white space (留白).
Minimal color - primarily black, gray, white with occasional subtle warm accents.
Flowing, dynamic brush energy. Atmospheric perspective through ink density.
Characters rendered with bold decisive strokes. Backgrounds fade into mist.

MUST INCLUDE: brush stroke texture, ink wash gradients, rice paper feel, intentional white space, atmospheric depth, flowing lines, traditional Chinese aesthetic
DO NOT USE: photorealistic, colorful, neon, 3D render, Western art style, digital art look, sharp clean lines, bright saturated colors

MEMORY SCENE TREATMENT:
- Warmer sepia-tinted ink tones
- Softer brush strokes with more blur
- Dreamlike quality with hazier edges
- Lighter overall ink density
- Subtle golden warmth mixed into grays

---

Interior of a bustling ancient Chinese tavern (客栈). A young swordsman with jet black hair in high topknot stands confidently in the center, one hand on his famous gleaming sword. He wears fine dark blue silk robes with silver trim, his posture radiating arrogance and supreme confidence. His narrow eyes gleam with pride.

Around him, other martial artists sit at wooden tables, looking up with mixed expressions of admiration and wariness. Lanterns hang from wooden beams. Wine jars and cups on tables. The atmosphere is lively but tense with anticipation.

The young Bai Chuan's confident smirk and raised chin show a man who believes himself invincible. His sword hand rests casually but ready.

EMOTIONAL ATMOSPHERE:
Peak arrogance, supreme confidence, the hubris before the fall.
A champion who has never known defeat.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
天下剑客，谁敢与我一战？
```

---

### Shot 05: 意外发生 (回忆)

**场景**: 比剑瞬间，剑光闪过，意外刺中少年

| 字段 | 内容 |
|------|------|
| **shot_id** | 5 |
| **text_type** | narration |
| **speaker_position** | top |
| **characters_in_scene** | master_young |

**image_prompt:**
```
STYLE: Chinese Ink Wash Painting (水墨画)

Traditional Chinese ink wash aesthetic (sumi-e inspired).
Brush stroke textures, ink gradients from deep black to pale gray.
Rice paper texture background with intentional white space (留白).
Minimal color - primarily black, gray, white with occasional subtle warm accents.
Flowing, dynamic brush energy. Atmospheric perspective through ink density.
Characters rendered with bold decisive strokes. Backgrounds fade into mist.

MUST INCLUDE: brush stroke texture, ink wash gradients, rice paper feel, intentional white space, atmospheric depth, flowing lines, traditional Chinese aesthetic
DO NOT USE: photorealistic, colorful, neon, 3D render, Western art style, digital art look, sharp clean lines, bright saturated colors

MEMORY SCENE TREATMENT:
- Warmer sepia-tinted ink tones
- Softer brush strokes with more blur
- Dreamlike quality with hazier edges
- Lighter overall ink density
- Subtle golden warmth mixed into grays

---

A dynamic frozen moment of tragedy. The young swordsman with black hair has lunged forward, his gleaming sword extended in a thrust. His face shows the first flash of shock as he realizes - too late - that his blade has found the wrong target.

The composition uses dramatic white space to represent the sword's deadly path. Motion lines in ink suggest the unstoppable speed of the strike. The young man's dark blue robes billow with arrested momentum.

Only hints of the victim visible at the edge of frame - a youthful figure, a spray of ink suggesting blood. The focus is on the swordsman's expression transforming from triumph to horror.

EMOTIONAL ATMOSPHERE:
The split-second when everything changes. Triumph turning to tragedy.
The point of no return.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
那一剑，我收不住了。
```

---

### Shot 06: 好友之弟倒下 (回忆)

**场景**: 俯视，少年倒在血泊中，年轻白川跪地绝望

| 字段 | 内容 |
|------|------|
| **shot_id** | 6 |
| **text_type** | thought |
| **speaker_position** | bottom |
| **characters_in_scene** | master_young |

**image_prompt:**
```
STYLE: Chinese Ink Wash Painting (水墨画)

Traditional Chinese ink wash aesthetic (sumi-e inspired).
Brush stroke textures, ink gradients from deep black to pale gray.
Rice paper texture background with intentional white space (留白).
Minimal color - primarily black, gray, white with occasional subtle warm accents.
Flowing, dynamic brush energy. Atmospheric perspective through ink density.
Characters rendered with bold decisive strokes. Backgrounds fade into mist.

MUST INCLUDE: brush stroke texture, ink wash gradients, rice paper feel, intentional white space, atmospheric depth, flowing lines, traditional Chinese aesthetic
DO NOT USE: photorealistic, colorful, neon, 3D render, Western art style, digital art look, sharp clean lines, bright saturated colors

MEMORY SCENE TREATMENT:
- Warmer sepia-tinted ink tones
- Softer brush strokes with more blur
- Dreamlike quality with hazier edges
- Lighter overall ink density
- Subtle golden warmth mixed into grays

EMOTIONAL EMPHASIS:
- This is a moment of devastating realization
- The red emphasis should be subtle - just a dark pool spreading on the floor

---

Overhead view looking down at the tavern floor. A young man in dark blue silk robes has dropped to his knees, his famous sword fallen beside him, his hands shaking. Before him lies a young boy of about sixteen, motionless. A dark spreading pool surrounds the fallen youth, rendered in deeper ink tones.

The kneeling swordsman's face is turned downward, anguish visible in his hunched shoulders, his fists clenched against his thighs. His proud topknot has come partially loose, black hair falling over his face.

Other figures are frozen in the background, rendered as faint suggestions. All attention focuses on this tableau of tragedy - the killer kneeling before his victim.

EMOTIONAL ATMOSPHERE:
Absolute devastation, irreversible guilt, the death of innocence.
A man's entire world collapsing in a single moment.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
他才十六岁...是周沧的亲弟弟...！！！
```

---

### Shot 07: 徒弟练剑

**场景**: 现在，山间小屋前，年轻徒弟挥剑练习

| 字段 | 内容 |
|------|------|
| **shot_id** | 7 |
| **text_type** | none |
| **speaker_position** | none |
| **characters_in_scene** | disciple |

**image_prompt:**
```
STYLE: Chinese Ink Wash Painting (水墨画)

Traditional Chinese ink wash aesthetic (sumi-e inspired).
Brush stroke textures, ink gradients from deep black to pale gray.
Rice paper texture background with intentional white space (留白).
Minimal color - primarily black, gray, white with occasional subtle warm accents.
Flowing, dynamic brush energy. Atmospheric perspective through ink density.
Characters rendered with bold decisive strokes. Backgrounds fade into mist.

MUST INCLUDE: brush stroke texture, ink wash gradients, rice paper feel, intentional white space, atmospheric depth, flowing lines, traditional Chinese aesthetic
DO NOT USE: photorealistic, colorful, neon, 3D render, Western art style, digital art look, sharp clean lines, bright saturated colors

---

A young swordsman with jet black hair in high ponytail tied with white ribbon practices sword forms in a clearing before a modest mountain hut. He wears a deep blue martial arts jacket with white cloth belt, his stance wide and sword extended in a precise horizontal cut.

The morning sun creates dappled light through bamboo leaves. The simple wooden hut has a thatched roof, its door open. A small vegetable garden grows nearby. The scene conveys peace and disciplined training.

Lin Feng's expression is focused, determined, his bright brown eyes fixed on an imaginary opponent. His movements are rendered with flowing brush strokes suggesting grace and skill. White ribbon flutters with the motion.

EMOTIONAL ATMOSPHERE:
Youth, dedication, morning tranquility before the storm.
A brief moment of peace that will soon be shattered.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
无
```

---

### Shot 08: 黑衣人现身

**场景**: 山间竹林边缘，黑衣蒙面人居高临下出现

| 字段 | 内容 |
|------|------|
| **shot_id** | 8 |
| **text_type** | dialogue |
| **speaker_position** | top |
| **characters_in_scene** | enemy |

**image_prompt:**
```
STYLE: Chinese Ink Wash Painting (水墨画)

Traditional Chinese ink wash aesthetic (sumi-e inspired).
Brush stroke textures, ink gradients from deep black to pale gray.
Rice paper texture background with intentional white space (留白).
Minimal color - primarily black, gray, white with occasional subtle warm accents.
Flowing, dynamic brush energy. Atmospheric perspective through ink density.
Characters rendered with bold decisive strokes. Backgrounds fade into mist.

MUST INCLUDE: brush stroke texture, ink wash gradients, rice paper feel, intentional white space, atmospheric depth, flowing lines, traditional Chinese aesthetic
DO NOT USE: photorealistic, colorful, neon, 3D render, Western art style, digital art look, sharp clean lines, bright saturated colors

---

Low angle view looking up at a menacing figure standing on a rocky outcrop at the edge of the bamboo forest. A man in all-black night-traveling clothes, face covered by black cloth mask, only his cold hate-filled eyes visible. A thin black sword is strapped to his back.

His black robes and hood merge with the ink-dark shadows of the forest behind him. He stands utterly still, radiating deadly intent. The bamboo stalks frame him like prison bars - or like swords.

Wind rustles his clothes slightly. His narrow eyes burn with three decades of hatred, fixed on something below (the hut, off-frame).

EMOTIONAL ATMOSPHERE:
Menace, long-awaited confrontation, the arrival of retribution.
Death has come calling.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
白川，三十年了，我终于找到你了。
```

---

### Shot 09: 师徒对峙仇人

**场景**: 小屋前，三人对峙，三角构图

| 字段 | 内容 |
|------|------|
| **shot_id** | 9 |
| **text_type** | dialogue |
| **speaker_position** | left |
| **characters_in_scene** | master_old, disciple, enemy |

**image_prompt:**
```
STYLE: Chinese Ink Wash Painting (水墨画)

Traditional Chinese ink wash aesthetic (sumi-e inspired).
Brush stroke textures, ink gradients from deep black to pale gray.
Rice paper texture background with intentional white space (留白).
Minimal color - primarily black, gray, white with occasional subtle warm accents.
Flowing, dynamic brush energy. Atmospheric perspective through ink density.
Characters rendered with bold decisive strokes. Backgrounds fade into mist.

MUST INCLUDE: brush stroke texture, ink wash gradients, rice paper feel, intentional white space, atmospheric depth, flowing lines, traditional Chinese aesthetic
DO NOT USE: photorealistic, colorful, neon, 3D render, Western art style, digital art look, sharp clean lines, bright saturated colors

---

A tense three-way standoff in front of the mountain hut. Triangle composition with three figures.

In the foreground left, the old swordsman with white hair, beard, and hemp robe has stepped out from the hut, his ancient cracked sword drawn. His weathered face shows grim acceptance, not fear. He positions himself protectively before his disciple.

Behind him center-right, the young disciple in blue martial jacket has drawn his sword, his expression showing confusion and readiness to fight. His stance is defensive but alert.

Facing them from a distance, the black-clad masked figure stands with hand on his sword hilt, radiating cold menace. Only his hate-filled eyes visible above the mask.

The bamboo forest provides the backdrop. Tension crackles in the white space between them.

EMOTIONAL ATMOSPHERE:
Confrontation, protection, fate arriving.
The old man facing his past to protect his future (the disciple).

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
林风，退下。这是我的债，该我来还。
```

---

### Shot 10: 竹林决战（起手）

**场景**: 竹林深处，两人相距数丈，剑气交错

| 字段 | 内容 |
|------|------|
| **shot_id** | 10 |
| **text_type** | narration |
| **speaker_position** | top |
| **characters_in_scene** | master_old, enemy |

**image_prompt:**
```
STYLE: Chinese Ink Wash Painting (水墨画)

Traditional Chinese ink wash aesthetic (sumi-e inspired).
Brush stroke textures, ink gradients from deep black to pale gray.
Rice paper texture background with intentional white space (留白).
Minimal color - primarily black, gray, white with occasional subtle warm accents.
Flowing, dynamic brush energy. Atmospheric perspective through ink density.
Characters rendered with bold decisive strokes. Backgrounds fade into mist.

MUST INCLUDE: brush stroke texture, ink wash gradients, rice paper feel, intentional white space, atmospheric depth, flowing lines, traditional Chinese aesthetic
DO NOT USE: photorealistic, colorful, neon, 3D render, Western art style, digital art look, sharp clean lines, bright saturated colors

ACTION SCENE TREATMENT:
- Dynamic brush strokes showing movement
- Ink splatter effects for impact
- White space used to represent sword flash/speed
- Bamboo leaves scattered in motion
- Energy lines through negative space

---

Wide shot of the bamboo forest clearing. Two swordsmen face each other across a gap of several meters. The old swordsman in hemp robes on the left, cracked sword raised. The black-clad avenger on the right, thin black sword drawn.

Both are captured in the instant before movement - bodies coiled with potential energy. The space between them is charged with killing intent, rendered as swirling ink patterns and scattered bamboo leaves suspended mid-fall.

Moonlight cuts through the bamboo canopy, creating dramatic strips of light and shadow. The bamboo stalks form vertical lines of varying ink density, creating depth. Snow begins to fall lightly.

EMOTIONAL ATMOSPHERE:
The calm before violence, thirty years distilled to this moment.
Two men who have waited for this night.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
三十年的恩怨，就在今夜了结。
```

---

### Shot 11: 激战中

**场景**: 竹林，竹叶纷飞，剑光交错，激烈对战

| 字段 | 内容 |
|------|------|
| **shot_id** | 11 |
| **text_type** | none |
| **speaker_position** | none |
| **characters_in_scene** | master_old, enemy |

**image_prompt:**
```
STYLE: Chinese Ink Wash Painting (水墨画)

Traditional Chinese ink wash aesthetic (sumi-e inspired).
Brush stroke textures, ink gradients from deep black to pale gray.
Rice paper texture background with intentional white space (留白).
Minimal color - primarily black, gray, white with occasional subtle warm accents.
Flowing, dynamic brush energy. Atmospheric perspective through ink density.
Characters rendered with bold decisive strokes. Backgrounds fade into mist.

MUST INCLUDE: brush stroke texture, ink wash gradients, rice paper feel, intentional white space, atmospheric depth, flowing lines, traditional Chinese aesthetic
DO NOT USE: photorealistic, colorful, neon, 3D render, Western art style, digital art look, sharp clean lines, bright saturated colors

ACTION SCENE TREATMENT:
- Dynamic brush strokes showing movement
- Ink splatter effects for impact
- White space used to represent sword flash/speed
- Bamboo leaves scattered in motion
- Energy lines through negative space

---

The duel at its peak intensity. Two figures blur together in a dance of death, their swords meeting in a shower of sparks rendered as white spots against dark ink. The white-haired old man and black-clad avenger are interlocked mid-strike.

Bamboo leaves explode outward from the force of their clash. Several bamboo stalks have been cut clean through, toppling. Ink splatter radiates from the center of combat, suggesting impact and violence.

Motion blur and dynamic brush strokes make the figures almost merge into abstract shapes of conflict - white robes and black robes, two swords crossed. The combat is rendered more as energy and motion than clear detail.

EMOTIONAL ATMOSPHERE:
Peak violence, skills perfectly matched, life and death balanced on blade's edge.
Two masters giving everything they have.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
无
```

---

### Shot 12: 身中数剑

**场景**: 战斗尾声，老剑客身中数剑但仍站立，点名仇人

| 字段 | 内容 |
|------|------|
| **shot_id** | 12 |
| **text_type** | dialogue |
| **speaker_position** | left |
| **characters_in_scene** | master_old, enemy |

**image_prompt:**
```
STYLE: Chinese Ink Wash Painting (水墨画)

Traditional Chinese ink wash aesthetic (sumi-e inspired).
Brush stroke textures, ink gradients from deep black to pale gray.
Rice paper texture background with intentional white space (留白).
Minimal color - primarily black, gray, white with occasional subtle warm accents.
Flowing, dynamic brush energy. Atmospheric perspective through ink density.
Characters rendered with bold decisive strokes. Backgrounds fade into mist.

MUST INCLUDE: brush stroke texture, ink wash gradients, rice paper feel, intentional white space, atmospheric depth, flowing lines, traditional Chinese aesthetic
DO NOT USE: photorealistic, colorful, neon, 3D render, Western art style, digital art look, sharp clean lines, bright saturated colors

---

The aftermath of the duel. The old swordsman stands barely upright, his hemp robe torn and dark with blood from multiple wounds. Several throwing knives protrude from his body. Yet his eyes remain clear, fixed on his opponent, his cracked sword still gripped in one hand.

Opposite him, the black-clad man has also taken damage - his mask torn partially away, revealing a cruel mouth set in grimace. He breathes heavily, wounded but less critically.

Both men are surrounded by fallen bamboo, scattered leaves, disturbed snow now stained dark. The old man's white hair has come loose, streaming behind him. Blood drips from his wounds to the snow.

EMOTIONAL ATMOSPHERE:
Defiance in defeat, a man who has achieved what he needed to.
Speaking his enemy's name at last - acknowledging their shared history.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
周沧...我等这一剑...等了三十年...
```

---

### Shot 13: 断剑托付

**场景**: 雪地，徒弟赶到，老剑客倒在徒弟怀中，托付断剑

| 字段 | 内容 |
|------|------|
| **shot_id** | 13 |
| **text_type** | dialogue |
| **speaker_position** | left |
| **characters_in_scene** | master_old, disciple |

**image_prompt:**
```
STYLE: Chinese Ink Wash Painting (水墨画)

Traditional Chinese ink wash aesthetic (sumi-e inspired).
Brush stroke textures, ink gradients from deep black to pale gray.
Rice paper texture background with intentional white space (留白).
Minimal color - primarily black, gray, white with occasional subtle warm accents.
Flowing, dynamic brush energy. Atmospheric perspective through ink density.
Characters rendered with bold decisive strokes. Backgrounds fade into mist.

MUST INCLUDE: brush stroke texture, ink wash gradients, rice paper feel, intentional white space, atmospheric depth, flowing lines, traditional Chinese aesthetic
DO NOT USE: photorealistic, colorful, neon, 3D render, Western art style, digital art look, sharp clean lines, bright saturated colors

---

The young disciple kneels in the snow, cradling his fallen master in his arms. Lin Feng's face shows anguish, tears streaming down his cheeks. His blue martial jacket is stained with his master's blood.

The old swordsman looks up at his student with peaceful, fading eyes. With trembling hands, he offers his cracked sword - the blade with the thirty-year-old wound. His white beard is matted with blood, but his expression holds no regret, only a gentle passing of responsibility.

Snow falls heavily around them. The wounded enemy stands at a distance, watching (suggested in background). Fallen bamboo and disturbed snow tell the story of the battle just ended.

EMOTIONAL ATMOSPHERE:
Transmission of legacy, peaceful death, a burden passed to the next generation.
The student becoming the master.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
这把剑...和我欠下的债...都交给你了...
```

---

### Shot 14: 真相大白

**场景**: 雪地，黑衣人摘下面具，原来是周沧，眼中有泪

| 字段 | 内容 |
|------|------|
| **shot_id** | 14 |
| **text_type** | dialogue |
| **speaker_position** | center |
| **characters_in_scene** | enemy |

**image_prompt:**
```
STYLE: Chinese Ink Wash Painting (水墨画)

Traditional Chinese ink wash aesthetic (sumi-e inspired).
Brush stroke textures, ink gradients from deep black to pale gray.
Rice paper texture background with intentional white space (留白).
Minimal color - primarily black, gray, white with occasional subtle warm accents.
Flowing, dynamic brush energy. Atmospheric perspective through ink density.
Characters rendered with bold decisive strokes. Backgrounds fade into mist.

MUST INCLUDE: brush stroke texture, ink wash gradients, rice paper feel, intentional white space, atmospheric depth, flowing lines, traditional Chinese aesthetic
DO NOT USE: photorealistic, colorful, neon, 3D render, Western art style, digital art look, sharp clean lines, bright saturated colors

---

Close-up of the avenger removing his mask and hood, revealing his face fully for the first time. Zhou Cang is a man of fifty with iron-gray hair, square jaw, and harsh weathered features. His crooked nose was broken long ago. Deep crow's feet mark decades of hatred.

But his expression is transforming. The cold hatred in his eyes is cracking, replaced by something more complex - grief, recognition of shared pain, reluctant respect. Tears cut tracks through the dirt and blood on his face.

His black clothes are torn, wounds visible. He holds the torn mask in one trembling hand. Behind him, snow falls on the battlefield. In the soft-focus background, the disciple cradles the fallen master.

EMOTIONAL ATMOSPHERE:
The lifting of masks - literal and emotional. Recognition that hatred has not brought peace.
Realizing the enemy suffered as much as you.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
白川...这三十年，你比我更痛苦...
```

---

### Shot 15: 剑断义存

**场景**: 大远景，林风站在雪中手持断剑，天地苍茫

| 字段 | 内容 |
|------|------|
| **shot_id** | 15 |
| **text_type** | narration |
| **speaker_position** | bottom |
| **characters_in_scene** | disciple |

**image_prompt:**
```
STYLE: Chinese Ink Wash Painting (水墨画)

Traditional Chinese ink wash aesthetic (sumi-e inspired).
Brush stroke textures, ink gradients from deep black to pale gray.
Rice paper texture background with intentional white space (留白).
Minimal color - primarily black, gray, white with occasional subtle warm accents.
Flowing, dynamic brush energy. Atmospheric perspective through ink density.
Characters rendered with bold decisive strokes. Backgrounds fade into mist.

MUST INCLUDE: brush stroke texture, ink wash gradients, rice paper feel, intentional white space, atmospheric depth, flowing lines, traditional Chinese aesthetic
DO NOT USE: photorealistic, colorful, neon, 3D render, Western art style, digital art look, sharp clean lines, bright saturated colors

---

Vast landscape composition showing a lone figure standing in a snow-covered mountain clearing. The young swordsman Lin Feng, now bearing his master's legacy, stands with back to viewer, holding the cracked sword before him - examining the wound in the blade that tells its story.

The world stretches out around him - misty mountains fading into white, bamboo forest reduced to gray shadows, snow falling from an endless pale sky. The figure is small against the immensity of landscape, yet his posture shows resolve, not defeat.

Dawn light begins to warm the eastern horizon, the faintest hint of gold among the grays. A new day, a new beginning. The white ribbon in his ponytail flutters in the wind.

In the snow at his feet, two sets of departing footprints lead away - Zhou Cang has gone, the feud ended. A mound of disturbed snow suggests a fresh grave.

EMOTIONAL ATMOSPHERE:
Inheritance, continuation, hope emerging from tragedy.
The sword may be broken, but righteousness endures.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
剑可断，义不可断。师父，我明白了。
```

---

## 技术验证重点

| 验证项 | 说明 |
|--------|------|
| **角色一致性** | 老剑客在15张图中外貌统一（白发、麻布长袍、古剑、左颊疤痕） |
| **年龄一致性** | master_young 与 master_old 特征相符（身高、脸型、眼睛） |
| **古装服饰** | 符合中国古代剑客形象，无现代元素泄露 |
| **水墨风格** | 笔触感、留白、墨色浓淡层次、宣纸质感 |
| **情感表达** | 悲壮、愧疚、传承等情绪的面部表情 |
| **动作场景** | 剑术对决的动态感（Shot 10-12） |
| **时间线叙事** | 回忆(Shot 04-06) vs 现在的视觉区分 |
| **泡泡位置** | AI推荐的bubble_x/y_percent不遮挡角色脸部 |

---

## 下一步

1. @Backend 根据本脚本执行测试生成
2. @Tester 验收
3. @PM 继续设计故事C（赛博朋克）

**预期输出目录**: `test_output/comic_full_story_v2_wuxia_ink/`
