# 条漫完整故事脚本 - 故事C《最后的记忆商人》

> **作者**: @AI-ML
> **日期**: 2026-01-28
> **关联任务**: TASK-VERIFY-001-B
> **用途**: 多风格通用性验证测试 - 赛博朋克 + 霓虹风格

---

## 故事信息

| 项目 | 内容 |
|------|------|
| **标题** | 最后的记忆商人 (The Last Memory Dealer) |
| **题材** | 赛博朋克 / 反乌托邦 |
| **主题** | 在真相被抹杀的世界，守护记忆就是守护人性 |
| **风格** | Cyberpunk (赛博朋克) |
| **色调** | 霓虹粉 (neon pink)、青色 (cyan)、紫色 (purple)、暗灰 (dark gray)、黑色 (black) |
| **图片数** | 15 |

---

## 角色设计 (Character Designs)

### 主角：林夜 (char_001)

| 字段 | 英文描述 |
|------|----------|
| **id** | char_001 |
| **name** | 林夜 |
| **name_en** | Lin Ye |
| **type** | human |
| **gender** | male |
| **age_appearance** | adult (32) |

**Physical Description:**
```
ethnicity: East Asian
height: medium (175cm)
build: lean athletic, lithe and quick
skin_tone: pale, rarely sees natural sunlight
face_shape: angular with sharp features
hair_color: jet black
hair_style: short sides shaved with longer top slicked back
hair_texture: straight
eye_color: dark brown right eye, SILVER CYBERNETIC LEFT EYE with faint blue glow
eye_shape: sharp, calculating
eye_size: medium
eyebrows: thick straight
nose: straight
lips: thin, often pressed
distinctive_marks: silver cybernetic left eye with blue glow, thin scar on right cheek, glowing neural port on left wrist
```

**Clothing:**
```
top: dark gray synthetic leather jacket over black turtleneck
bottom: black tactical cargo pants with multiple pockets
footwear: black combat boots with metal accents
accessories: glowing neural interface port on left wrist, dark hood attached to jacket
style: cyberpunk street, practical and anonymous
```

**Visual Identity Markers (CRITICAL):**
```
- SILVER CYBERNETIC LEFT EYE with BLUE GLOW (must be visible in all shots)
- Thin scar on right cheek
- Dark gray leather jacket + black turtleneck combo
- Glowing wrist neural port (when visible)
```

---

### 配角：老陈 (char_002)

| 字段 | 英文描述 |
|------|----------|
| **id** | char_002 |
| **name** | 老陈 |
| **name_en** | Old Chen |
| **type** | human |
| **gender** | male |
| **age_appearance** | elderly (78) |

**Physical Description:**
```
ethnicity: East Asian
height: medium (170cm, stooped)
build: frail, thin from age
skin_tone: weathered pale with age spots
face_shape: gaunt with hollow cheeks
hair_color: white
hair_style: thin white hair combed back
hair_texture: wispy and sparse
eye_color: clouded gray (natural, no implants)
eye_shape: hooded with heavy lids
eye_size: small
eyebrows: sparse white
nose: prominent thin
lips: thin dry
distinctive_marks: deep wrinkles, oxidized old-model neural ports on back of hands (aged technology), age spots
```

**Clothing:**
```
top: faded blue worker jumpsuit with old tech company logo patch (partially peeled)
bottom: same jumpsuit pants
footwear: worn gray utility shoes
accessories: metal walking cane with worn rubber grip, old memory chip on cord around neck
style: worn utilitarian, remnant of old world
```

**Visual Identity Markers (CRITICAL):**
```
- WHITE HAIR (thin, wispy)
- FADED BLUE JUMPSUIT with old company logo
- METAL WALKING CANE
- OXIDIZED NEURAL PORTS on hands
- MEMORY CHIP on cord around neck
```

---

### 反派：凯拉 (char_003)

| 字段 | 英文描述 |
|------|----------|
| **id** | char_003 |
| **name** | 凯拉 |
| **name_en** | Kayla |
| **type** | human |
| **gender** | female |
| **age_appearance** | young_adult (28) |

**Physical Description:**
```
ethnicity: mixed Euro-Asian
height: tall (175cm)
build: athletic, military posture
skin_tone: fair
face_shape: angular with high cheekbones
hair_color: silver white
hair_style: short asymmetrical side-parted
hair_texture: sleek
eye_color: RED CYBERNETIC COMBAT EYES (BOTH EYES)
eye_shape: almond, predatory
eye_size: medium
eyebrows: thin arched
nose: straight refined
lips: full with perpetual slight smirk
distinctive_marks: BOTH eyes are RED cybernetic combat implants, RIGHT ARM is FULL CHROME CYBERNETIC LIMB with hidden weapon, small corporate barcode tattoo on neck
```

**Clothing:**
```
top: black corporate tactical armor vest with glowing RED CORPORATE LOGO
bottom: black tactical pants with armored knee pads
footwear: black armored combat boots
accessories: full chrome right cybernetic arm (with hidden blade), tactical earpiece, holstered energy pistol on hip
style: corporate security elite, intimidating and efficient
```

**Visual Identity Markers (CRITICAL):**
```
- SILVER-WHITE SHORT HAIR (asymmetrical)
- BOTH EYES are RED CYBERNETIC (combat model, always glowing)
- FULL CHROME RIGHT ARM (metal, visible joints)
- BLACK TACTICAL ARMOR with RED CORPORATE LOGO
- Cold calculating smirk
```

---

## 风格指令 (Style Instructions)

### Cyberpunk 风格前缀

所有 image_prompt 开头必须添加：

```
STYLE: Cyberpunk / Neo-Noir

Cinematic cyberpunk aesthetic inspired by Blade Runner and Ghost in the Shell.
Dramatic neon lighting in pink, cyan, and purple against dark backgrounds.
Wet streets reflecting holographic advertisements. High-tech dystopian atmosphere.
Dense urban environments with towering buildings and holographic billboards.
Surveillance drones, neural interfaces, and cybernetic enhancements as visual elements.
Dark, moody atmosphere with pockets of vibrant neon color.

MUST INCLUDE: neon lights (pink, cyan, purple), wet reflective surfaces, holographic displays, dark atmosphere, futuristic technology, dense urban environment, dramatic lighting contrasts
DO NOT USE: bright daylight, natural colors, pastoral scenes, cartoon style, anime style, watercolor, hand-drawn look, clean bright environments
```

### 记忆场景特殊处理 (Shot 14)

记忆场景（旧世界回忆）需要添加：

```
MEMORY/OLD WORLD SCENE TREATMENT:
- CONTRASTING with the cyberpunk aesthetic
- Bright natural sunlight, clear blue sky
- Warm golden tones, natural greens
- Clean air, no neon, no corporate logos
- Genuine human expressions and connections
- Beautiful lost world preserved in forbidden memory
- This scene should feel like a breath of fresh air after the dark dystopian world
```

### 追逐场景处理 (Shots 10-11)

追逐/动作场景需要添加：

```
CHASE/ACTION SCENE TREATMENT:
- Dynamic motion blur on running figures
- Rain streaks through neon light beams
- Urgency conveyed through composition
- Drone searchlights sweeping
- Reflections on wet pavement
```

---

## 15图完整脚本 (Complete Script)

---

### Shot 01: 城市远景

**场景**: 未来城市天际线，巨型全息广告，反乌托邦开场

| 字段 | 内容 |
|------|------|
| **shot_id** | 1 |
| **text_type** | narration |
| **speaker_position** | top |
| **characters_in_scene** | (none) |

**image_prompt:**
```
STYLE: Cyberpunk / Neo-Noir

Cinematic cyberpunk aesthetic inspired by Blade Runner and Ghost in the Shell.
Dramatic neon lighting in pink, cyan, and purple against dark backgrounds.
Wet streets reflecting holographic advertisements. High-tech dystopian atmosphere.
Dense urban environments with towering buildings and holographic billboards.
Surveillance drones, neural interfaces, and cybernetic enhancements as visual elements.
Dark, moody atmosphere with pockets of vibrant neon color.

MUST INCLUDE: neon lights (pink, cyan, purple), wet reflective surfaces, holographic displays, dark atmosphere, futuristic technology, dense urban environment, dramatic lighting contrasts
DO NOT USE: bright daylight, natural colors, pastoral scenes, cartoon style, anime style, watercolor, hand-drawn look, clean bright environments

---

Establishing wide shot of Neo City at night. A vast cyberpunk metropolis stretches to the horizon. Towering skyscrapers pierce the dark overcast sky, their surfaces covered with massive holographic advertisements casting pink and cyan light across the urban canyon.

Surveillance drones patrol in formation against the clouds. Rain falls through beams of neon light. A dominant corporate tower rises above all others, its giant glowing logo visible for miles. Streets far below are packed with anonymous crowds, rendered as streams of light and movement.

The atmosphere is oppressive yet hauntingly beautiful - a civilization that has sacrificed humanity for technology. No stars visible through the perpetual smog and light pollution.

EMOTIONAL ATMOSPHERE:
Dystopian grandeur, oppressive corporate dominance, a world where everything has a price.
The beautiful nightmare of unchecked technological progress.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
2089年，新城。在这里，一切都可以被购买。包括记忆。
```

---

### Shot 02: 林夜登场

**场景**: 霓虹街区街道，林夜穿行人群，义眼扫描

| 字段 | 内容 |
|------|------|
| **shot_id** | 2 |
| **text_type** | narration |
| **speaker_position** | bottom |
| **characters_in_scene** | char_001 |

**image_prompt:**
```
STYLE: Cyberpunk / Neo-Noir

Cinematic cyberpunk aesthetic inspired by Blade Runner and Ghost in the Shell.
Dramatic neon lighting in pink, cyan, and purple against dark backgrounds.
Wet streets reflecting holographic advertisements. High-tech dystopian atmosphere.
Dense urban environments with towering buildings and holographic billboards.
Surveillance drones, neural interfaces, and cybernetic enhancements as visual elements.
Dark, moody atmosphere with pockets of vibrant neon color.

MUST INCLUDE: neon lights (pink, cyan, purple), wet reflective surfaces, holographic displays, dark atmosphere, futuristic technology, dense urban environment, dramatic lighting contrasts
DO NOT USE: bright daylight, natural colors, pastoral scenes, cartoon style, anime style, watercolor, hand-drawn look, clean bright environments

---

Medium shot of Lin Ye (char_001) moving through a crowded neon-lit street. He is a lean man in his early 30s with jet black hair (short sides, longer top slicked back), wearing a dark gray synthetic leather jacket over black turtleneck. His hood is pulled up partially.

CRITICAL: His LEFT EYE is a SILVER CYBERNETIC IMPLANT with a FAINT BLUE GLOW, scanning his surroundings. A thin scar marks his right cheek. His expression is alert but composed.

Around him, crowds in synthetic raincoats and VR visors pass by anonymously. Neon signs in Chinese and English cast pink and cyan reflections on the wet pavement. Street vendors sell synthetic food from cramped stalls. A surveillance drone hovers overhead.

Lin Ye moves with predatory grace, constantly scanning, never fully relaxed. The neon light catches his cybernetic eye, making it gleam.

EMOTIONAL ATMOSPHERE:
Tense alertness, practiced anonymity, a man who survives by seeing everything.
Navigating danger as routine.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
林夜，黑市记忆商人。他的工作是交易那些不被允许存在的记忆。
```

---

### Shot 03: 地下入口

**场景**: 废弃地铁站入口，林夜准备进入地下

| 字段 | 内容 |
|------|------|
| **shot_id** | 3 |
| **text_type** | narration |
| **speaker_position** | bottom |
| **characters_in_scene** | char_001 |

**image_prompt:**
```
STYLE: Cyberpunk / Neo-Noir

Cinematic cyberpunk aesthetic inspired by Blade Runner and Ghost in the Shell.
Dramatic neon lighting in pink, cyan, and purple against dark backgrounds.
Wet streets reflecting holographic advertisements. High-tech dystopian atmosphere.
Dense urban environments with towering buildings and holographic billboards.
Surveillance drones, neural interfaces, and cybernetic enhancements as visual elements.
Dark, moody atmosphere with pockets of vibrant neon color.

MUST INCLUDE: neon lights (pink, cyan, purple), wet reflective surfaces, holographic displays, dark atmosphere, futuristic technology, dense urban environment, dramatic lighting contrasts
DO NOT USE: bright daylight, natural colors, pastoral scenes, cartoon style, anime style, watercolor, hand-drawn look, clean bright environments

---

Medium shot of an abandoned metro station entrance. Lin Ye (char_001) stands at the top of a broken escalator that descends into darkness. He is silhouetted against the neon glow from the street above, his dark gray jacket and black turtleneck barely visible.

CRITICAL: His SILVER CYBERNETIC LEFT EYE glows BRIGHTER BLUE as it scans for surveillance. Thin scar visible on right cheek.

The escalator is broken and rusted. Graffiti covers the walls - both gang tags and revolutionary slogans. Old transit signs hang crooked, their displays dead. Blue light emanates from somewhere below - the glow of the underground market.

The scene captures the transition from the open street to the hidden world below. Rain drips down through the entrance.

EMOTIONAL ATMOSPHERE:
Anticipation, entering the underground, crossing into the shadow economy.
The threshold between two worlds.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
今晚，有一笔特殊的交易在等着他。
```

---

### Shot 04: 记忆交易所

**场景**: 地下空间全貌，服务器蓝光，交易隔间

| 字段 | 内容 |
|------|------|
| **shot_id** | 4 |
| **text_type** | narration |
| **speaker_position** | top |
| **characters_in_scene** | char_001 |

**image_prompt:**
```
STYLE: Cyberpunk / Neo-Noir

Cinematic cyberpunk aesthetic inspired by Blade Runner and Ghost in the Shell.
Dramatic neon lighting in pink, cyan, and purple against dark backgrounds.
Wet streets reflecting holographic advertisements. High-tech dystopian atmosphere.
Dense urban environments with towering buildings and holographic billboards.
Surveillance drones, neural interfaces, and cybernetic enhancements as visual elements.
Dark, moody atmosphere with pockets of vibrant neon color.

MUST INCLUDE: neon lights (pink, cyan, purple), wet reflective surfaces, holographic displays, dark atmosphere, futuristic technology, dense urban environment, dramatic lighting contrasts
DO NOT USE: bright daylight, natural colors, pastoral scenes, cartoon style, anime style, watercolor, hand-drawn look, clean bright environments

---

Wide shot revealing the Memory Exchange - an underground black market in a converted metro station. The vast space is filled with dealer booths - small partitioned areas with neural interface chairs and server equipment. Blue light emanates from server racks lining the walls, casting the entire space in eerie illumination.

Lin Ye (char_001) enters from the background, his figure small against the scale of the illicit marketplace. Dark gray jacket, black turtleneck, SILVER CYBERNETIC LEFT EYE with BLUE GLOW visible even at distance.

Hooded figures conduct quiet transactions in shadowy corners. LED strips provide minimal additional lighting. Armed guards stand watch in the shadows. The atmosphere is one of illegal commerce - dangerous but organized.

Graffiti and old-world posters cover sections of the walls - remnants of the past mixed with present desperation.

EMOTIONAL ATMOSPHERE:
Underground commerce, necessary evil, the shadow economy where forbidden memories change hands.
A cathedral of the black market.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
记忆交易所——新城最大的黑市。
```

---

### Shot 05: 老陈出现

**场景**: 交易所角落，老陈从阴影中走出

| 字段 | 内容 |
|------|------|
| **shot_id** | 5 |
| **text_type** | narration |
| **speaker_position** | bottom |
| **characters_in_scene** | char_002 |

**image_prompt:**
```
STYLE: Cyberpunk / Neo-Noir

Cinematic cyberpunk aesthetic inspired by Blade Runner and Ghost in the Shell.
Dramatic neon lighting in pink, cyan, and purple against dark backgrounds.
Wet streets reflecting holographic advertisements. High-tech dystopian atmosphere.
Dense urban environments with towering buildings and holographic billboards.
Surveillance drones, neural interfaces, and cybernetic enhancements as visual elements.
Dark, moody atmosphere with pockets of vibrant neon color.

MUST INCLUDE: neon lights (pink, cyan, purple), wet reflective surfaces, holographic displays, dark atmosphere, futuristic technology, dense urban environment, dramatic lighting contrasts
DO NOT USE: bright daylight, natural colors, pastoral scenes, cartoon style, anime style, watercolor, hand-drawn look, clean bright environments

---

Medium close-up of Old Chen (char_002) stepping forward from shadow into a pool of blue light. He is a frail elderly man of 78 with thin WHITE HAIR combed back, wearing a FADED BLUE WORKER JUMPSUIT with an old tech company logo patch.

He grips a METAL WALKING CANE with worn rubber grip in one trembling hand. His face is deeply wrinkled, gaunt cheeks, clouded gray eyes burning with desperate urgency. OXIDIZED OLD-MODEL NEURAL PORTS are visible on the back of his weathered, age-spotted hands.

Around his neck hangs an OLD MEMORY CHIP on a simple cord - catching the blue light. His expression shows a mixture of fear and determination. He has been waiting for this meeting.

The harsh overhead light creates dramatic shadows on his face, emphasizing his age and desperation.

EMOTIONAL ATMOSPHERE:
Desperate urgency, last chance, a man with something precious and dangerous to pass on.
The weight of secret knowledge.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
委托人是个老人。他的眼神里有种林夜很少见到的东西——真诚的恐惧。
```

---

### Shot 06: 对话

**场景**: 交易隔间，林夜和老陈面对面

| 字段 | 内容 |
|------|------|
| **shot_id** | 6 |
| **text_type** | dialogue |
| **speaker** | char_002 |
| **speaker_position** | right |
| **characters_in_scene** | char_001, char_002 |

**image_prompt:**
```
STYLE: Cyberpunk / Neo-Noir

Cinematic cyberpunk aesthetic inspired by Blade Runner and Ghost in the Shell.
Dramatic neon lighting in pink, cyan, and purple against dark backgrounds.
Wet streets reflecting holographic advertisements. High-tech dystopian atmosphere.
Dense urban environments with towering buildings and holographic billboards.
Surveillance drones, neural interfaces, and cybernetic enhancements as visual elements.
Dark, moody atmosphere with pockets of vibrant neon color.

MUST INCLUDE: neon lights (pink, cyan, purple), wet reflective surfaces, holographic displays, dark atmosphere, futuristic technology, dense urban environment, dramatic lighting contrasts
DO NOT USE: bright daylight, natural colors, pastoral scenes, cartoon style, anime style, watercolor, hand-drawn look, clean bright environments

---

Over-the-shoulder shot in a small trading booth. Lin Ye (char_001) and Old Chen (char_002) face each other across a narrow space. Blue glow from neural interface equipment illuminates their faces from below.

Lin Ye (char_001): dark gray jacket, black turtleneck, SILVER CYBERNETIC LEFT EYE with BLUE GLOW, thin scar on right cheek. His expression is shifting from professional skepticism to genuine concern as he listens.

Old Chen (char_002): frail, WHITE HAIR, FADED BLUE JUMPSUIT, holds up a YELLOWED OLD MEMORY CHIP with trembling hands. His clouded gray eyes are intense with desperate purpose. The OXIDIZED NEURAL PORTS on his hands are visible.

The booth contains a neural interface chair with cables and a small server unit. Shadows and blue light create an intimate, conspiratorial atmosphere.

EMOTIONAL ATMOSPHERE:
Secret transaction, passing of forbidden knowledge, trust being established.
The moment before everything changes.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
我要把这个交给你保管。这是关于"大崩溃"的真相。
```

---

### Shot 07: 记忆芯片特写

**场景**: 特写老陈颤抖的手举着泛黄的记忆芯片

| 字段 | 内容 |
|------|------|
| **shot_id** | 7 |
| **text_type** | narration |
| **speaker_position** | bottom |
| **characters_in_scene** | char_002 |

**image_prompt:**
```
STYLE: Cyberpunk / Neo-Noir

Cinematic cyberpunk aesthetic inspired by Blade Runner and Ghost in the Shell.
Dramatic neon lighting in pink, cyan, and purple against dark backgrounds.
Wet streets reflecting holographic advertisements. High-tech dystopian atmosphere.
Dense urban environments with towering buildings and holographic billboards.
Surveillance drones, neural interfaces, and cybernetic enhancements as visual elements.
Dark, moody atmosphere with pockets of vibrant neon color.

MUST INCLUDE: neon lights (pink, cyan, purple), wet reflective surfaces, holographic displays, dark atmosphere, futuristic technology, dense urban environment, dramatic lighting contrasts
DO NOT USE: bright daylight, natural colors, pastoral scenes, cartoon style, anime style, watercolor, hand-drawn look, clean bright environments

---

Extreme close-up of Old Chen's aged trembling hands holding a YELLOWED OLD-MODEL MEMORY CHIP. The chip's surface is scratched and worn, showing its decades of age - obsolete technology that has somehow survived.

The OXIDIZED NEURAL PORTS on the back of his weathered hands are clearly visible - old-generation implants, discolored with age, surrounded by age spots. The hands tremble slightly but grip the chip with fierce determination.

Blue light catches the edges of the chip, making it gleam. The background is blurred but blue-tinged, suggesting the trading booth environment.

This small, fragile object contains the most dangerous thing in Neo City - truth.

EMOTIONAL ATMOSPHERE:
Preciousness, danger, a fragment of forbidden history held in trembling hands.
Something worth dying for.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
那是一块旧式记忆芯片。在今天，它比任何武器都危险。
```

---

### Shot 08: 警报

**场景**: 红色警报灯亮起，人群骚动，林夜警觉

| 字段 | 内容 |
|------|------|
| **shot_id** | 8 |
| **text_type** | narration |
| **speaker_position** | top |
| **characters_in_scene** | char_001 |

**image_prompt:**
```
STYLE: Cyberpunk / Neo-Noir

Cinematic cyberpunk aesthetic inspired by Blade Runner and Ghost in the Shell.
Dramatic neon lighting in pink, cyan, and purple against dark backgrounds.
Wet streets reflecting holographic advertisements. High-tech dystopian atmosphere.
Dense urban environments with towering buildings and holographic billboards.
Surveillance drones, neural interfaces, and cybernetic enhancements as visual elements.
Dark, moody atmosphere with pockets of vibrant neon color.

MUST INCLUDE: neon lights (pink, cyan, purple), wet reflective surfaces, holographic displays, dark atmosphere, futuristic technology, dense urban environment, dramatic lighting contrasts
DO NOT USE: bright daylight, natural colors, pastoral scenes, cartoon style, anime style, watercolor, hand-drawn look, clean bright environments

---

Medium shot of Lin Ye (char_001) in the Memory Exchange as chaos erupts. RED WARNING LIGHTS flash across the space, mixing harshly with the usual blue glow. Panicked dealers scramble in the background, shadows scattering.

Lin Ye's posture shifts to high alert - body coiled, ready to move. His SILVER CYBERNETIC LEFT EYE blazes BRIGHT BLUE as it processes threat data, scanning toward the entrance. His dark gray jacket and black turtleneck frame his tense figure. Thin scar on right cheek.

His expression shows controlled alarm - not panic, but instant tactical assessment. One hand moves instinctively to protect the pocket where the memory chip now rests.

The space that was ominously quiet moments ago is now chaos - but Lin Ye remains a still point, calculating.

EMOTIONAL ATMOSPHERE:
Sudden danger, instinct taking over, the moment when the trap springs.
Fight or flight decision.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
企业的人来了。
```

---

### Shot 09: 凯拉登场

**场景**: 仰角，凯拉带队冲入，红色义眼扫描

| 字段 | 内容 |
|------|------|
| **shot_id** | 9 |
| **text_type** | narration |
| **speaker_position** | bottom |
| **characters_in_scene** | char_003 |

**image_prompt:**
```
STYLE: Cyberpunk / Neo-Noir

Cinematic cyberpunk aesthetic inspired by Blade Runner and Ghost in the Shell.
Dramatic neon lighting in pink, cyan, and purple against dark backgrounds.
Wet streets reflecting holographic advertisements. High-tech dystopian atmosphere.
Dense urban environments with towering buildings and holographic billboards.
Surveillance drones, neural interfaces, and cybernetic enhancements as visual elements.
Dark, moody atmosphere with pockets of vibrant neon color.

MUST INCLUDE: neon lights (pink, cyan, purple), wet reflective surfaces, holographic displays, dark atmosphere, futuristic technology, dense urban environment, dramatic lighting contrasts
DO NOT USE: bright daylight, natural colors, pastoral scenes, cartoon style, anime style, watercolor, hand-drawn look, clean bright environments

---

Low angle shot looking up at Kayla (char_003) as she strides through the Memory Exchange entrance. She is backlit by neon glow from above, creating a menacing silhouette that steps into focus.

CRITICAL: SILVER-WHITE SHORT HAIR in asymmetrical side-parted style. BOTH EYES are RED CYBERNETIC COMBAT IMPLANTS, glowing intensely as they scan the crowd. Her RIGHT ARM is a FULL CHROME CYBERNETIC LIMB with visible joints, fingers flexing to reveal hidden blade mechanisms.

She wears BLACK TACTICAL ARMOR with a GLOWING RED CORPORATE LOGO on her chest. Her expression is a cold calculating smirk. Behind her, a security team follows in formation.

Her posture radiates military precision and lethal efficiency. She moves like a predator who knows exactly where her prey is.

EMOTIONAL ATMOSPHERE:
Menace, corporate authority, the arrival of overwhelming force.
The hunter has found her target.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
凯拉，企业安全官。她的眼里只有目标。
```

---

### Shot 10: 逃亡

**场景**: 后通道，林夜拉着老陈奔跑

| 字段 | 内容 |
|------|------|
| **shot_id** | 10 |
| **text_type** | narration |
| **speaker_position** | top |
| **characters_in_scene** | char_001, char_002 |

**image_prompt:**
```
STYLE: Cyberpunk / Neo-Noir

Cinematic cyberpunk aesthetic inspired by Blade Runner and Ghost in the Shell.
Dramatic neon lighting in pink, cyan, and purple against dark backgrounds.
Wet streets reflecting holographic advertisements. High-tech dystopian atmosphere.
Dense urban environments with towering buildings and holographic billboards.
Surveillance drones, neural interfaces, and cybernetic enhancements as visual elements.
Dark, moody atmosphere with pockets of vibrant neon color.

MUST INCLUDE: neon lights (pink, cyan, purple), wet reflective surfaces, holographic displays, dark atmosphere, futuristic technology, dense urban environment, dramatic lighting contrasts
DO NOT USE: bright daylight, natural colors, pastoral scenes, cartoon style, anime style, watercolor, hand-drawn look, clean bright environments

CHASE/ACTION SCENE TREATMENT:
- Dynamic motion blur on running figures
- Urgency conveyed through composition
- Blue emergency lights strobing
- Pursuit visible in background

---

Tracking shot through a narrow maintenance corridor. Lin Ye (char_001) pulls Old Chen (char_002) along, supporting the frail old man as they flee. Blue emergency lights strobe along the corridor.

Lin Ye: dark gray jacket, black turtleneck, SILVER CYBERNETIC LEFT EYE glowing as he looks back over his shoulder. Thin scar on right cheek. Expression shows focused determination.

Old Chen: struggles to keep pace, his METAL CANE barely keeping up with his shuffling feet. One hand grips his FADED BLUE JUMPSUIT where the memory chip hangs. WHITE HAIR disheveled, face showing exhausted determination.

Pipes and cables line the industrial walls. Behind them, shouts and footsteps echo - the pursuit is close. The corridor stretches ahead into uncertain darkness.

EMOTIONAL ATMOSPHERE:
Desperate flight, protection, racing against time.
Two men carrying something more valuable than their lives.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
林夜带着老陈从后门逃离。但他知道，企业的追踪器不会放过他们。
```

---

### Shot 11: 街头追逐

**场景**: 雨中霓虹街道，林夜和老陈在人群中穿梭

| 字段 | 内容 |
|------|------|
| **shot_id** | 11 |
| **text_type** | narration |
| **speaker_position** | bottom |
| **characters_in_scene** | char_001, char_002 |

**image_prompt:**
```
STYLE: Cyberpunk / Neo-Noir

Cinematic cyberpunk aesthetic inspired by Blade Runner and Ghost in the Shell.
Dramatic neon lighting in pink, cyan, and purple against dark backgrounds.
Wet streets reflecting holographic advertisements. High-tech dystopian atmosphere.
Dense urban environments with towering buildings and holographic billboards.
Surveillance drones, neural interfaces, and cybernetic enhancements as visual elements.
Dark, moody atmosphere with pockets of vibrant neon color.

MUST INCLUDE: neon lights (pink, cyan, purple), wet reflective surfaces, holographic displays, dark atmosphere, futuristic technology, dense urban environment, dramatic lighting contrasts
DO NOT USE: bright daylight, natural colors, pastoral scenes, cartoon style, anime style, watercolor, hand-drawn look, clean bright environments

CHASE/ACTION SCENE TREATMENT:
- Dynamic motion blur on running figures
- Rain streaks through neon light beams
- Urgency conveyed through composition
- Drone searchlights sweeping
- Reflections on wet pavement

---

Dynamic shot of a rainy neon street at night. Lin Ye (char_001) and Old Chen (char_002) push through a crowded street, rain falling through neon light beams creating prismatic streaks.

Lin Ye: supports exhausted Old Chen, weaving between oblivious crowds in synthetic raincoats. Dark gray jacket, SILVER CYBERNETIC LEFT EYE scanning behind them. Checking over his shoulder for pursuit. Thin scar on right cheek visible in neon light.

Old Chen: FADED BLUE JUMPSUIT soaked, clinging to Lin Ye's arm for support. WHITE HAIR plastered to his head. METAL CANE gripped fiercely. Exhausted but determined.

Neon signs in pink and cyan reflect off the wet pavement in beautiful streaks. Far behind them, searchlights sweep from pursuing DRONES - visible as ominous lights cutting through the rain.

EMOTIONAL ATMOSPHERE:
Desperate flight through beautiful dystopia, racing against corporate hunters.
Running for truth in a world of lies.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
霓虹灯下，每个人都在奔跑。但只有他们在为真相奔跑。
```

---

### Shot 12: 藏身处

**场景**: 老陈的藏身处，窗外城市天际线，旧照片墙

| 字段 | 内容 |
|------|------|
| **shot_id** | 12 |
| **text_type** | narration |
| **speaker_position** | top |
| **characters_in_scene** | char_001, char_002 |

**image_prompt:**
```
STYLE: Cyberpunk / Neo-Noir

Cinematic cyberpunk aesthetic inspired by Blade Runner and Ghost in the Shell.
Dramatic neon lighting in pink, cyan, and purple against dark backgrounds.
Wet streets reflecting holographic advertisements. High-tech dystopian atmosphere.
Dense urban environments with towering buildings and holographic billboards.
Surveillance drones, neural interfaces, and cybernetic enhancements as visual elements.
Dark, moody atmosphere with pockets of vibrant neon color.

MUST INCLUDE: neon lights (pink, cyan, purple), wet reflective surfaces, holographic displays, dark atmosphere, futuristic technology, dense urban environment, dramatic lighting contrasts
DO NOT USE: bright daylight, natural colors, pastoral scenes, cartoon style, anime style, watercolor, hand-drawn look, clean bright environments

---

Wide shot of Old Chen's cluttered hideout apartment. A large window shows the neon city skyline with distant corporate holographic logos. The room is filled with OLD TECHNOLOGY - vintage computers, memory equipment, tangled wires piled everywhere.

One wall is covered with FADED PHOTOGRAPHS and clippings from BEFORE THE GREAT COLLAPSE - images of green parks, blue skies, people with genuine smiles. A preserved museum of the lost world.

In the center, an OLD BUT WELL-MAINTAINED MEMORY TRANSFER PLATFORM glows softly, waiting.

Lin Ye (char_001) helps exhausted Old Chen (char_002) through the door, his eyes wide with wonder at the preserved history. Dark gray jacket, SILVER CYBERNETIC LEFT EYE reflecting the room's contents. Old Chen (WHITE HAIR, FADED BLUE JUMPSUIT) leans against the doorframe, catching his breath, gesturing at his sanctuary.

EMOTIONAL ATMOSPHERE:
Temporary refuge, a hidden archive of truth, awe at what has been preserved.
A pocket of the past surviving in the future.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
老陈的藏身处。这里保存着被抹杀的世界。
```

---

### Shot 13: 记忆传输

**场景**: 记忆传输台，老陈躺下，林夜操作设备

| 字段 | 内容 |
|------|------|
| **shot_id** | 13 |
| **text_type** | dialogue |
| **speaker** | char_002 |
| **speaker_position** | left |
| **characters_in_scene** | char_001, char_002 |

**image_prompt:**
```
STYLE: Cyberpunk / Neo-Noir

Cinematic cyberpunk aesthetic inspired by Blade Runner and Ghost in the Shell.
Dramatic neon lighting in pink, cyan, and purple against dark backgrounds.
Wet streets reflecting holographic advertisements. High-tech dystopian atmosphere.
Dense urban environments with towering buildings and holographic billboards.
Surveillance drones, neural interfaces, and cybernetic enhancements as visual elements.
Dark, moody atmosphere with pockets of vibrant neon color.

MUST INCLUDE: neon lights (pink, cyan, purple), wet reflective surfaces, holographic displays, dark atmosphere, futuristic technology, dense urban environment, dramatic lighting contrasts
DO NOT USE: bright daylight, natural colors, pastoral scenes, cartoon style, anime style, watercolor, hand-drawn look, clean bright environments

---

Medium shot of the memory transfer platform at the center of the room. Old Chen (char_002) lies on the old platform, neural cables connected to the OXIDIZED PORTS on his hands. His face is peaceful, eyes closed in acceptance. WHITE HAIR spread on the platform, FADED BLUE JUMPSUIT visible.

Lin Ye (char_001) stands at the control panel, connecting his own GLOWING WRIST NEURAL PORT. His expression is grave and reverent, understanding the weight of what he is about to receive. Dark gray jacket, SILVER CYBERNETIC LEFT EYE dimmed in concentration, thin scar on right cheek.

Soft amber glow from the platform mixes with the usual cyberpunk lighting. Old photographs on the wall behind them watch over this sacred moment of memory transmission.

EMOTIONAL ATMOSPHERE:
Solemn ritual, transmission of legacy, sacred responsibility being passed.
A dying man's final gift.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
把它传给你。让真相活下去。
```

---

### Shot 14: 记忆画面（旧世界）

**场景**: 记忆中的旧世界——蓝天、绿树、真诚的笑容

| 字段 | 内容 |
|------|------|
| **shot_id** | 14 |
| **text_type** | thought |
| **speaker** | char_001 |
| **speaker_position** | bottom |
| **characters_in_scene** | (none - memory vision) |

**image_prompt:**
```
MEMORY/OLD WORLD SCENE TREATMENT:
- CONTRASTING with the cyberpunk aesthetic
- Bright natural sunlight, clear blue sky
- Warm golden tones, natural greens
- Clean air, no neon, no corporate logos
- Genuine human expressions and connections
- Beautiful lost world preserved in forbidden memory
- This scene should feel like a breath of fresh air after the dark dystopian world

---

A vision of the old world before the Great Collapse. CLEAR BLUE SKY with white fluffy clouds. BRIGHT NATURAL SUNLIGHT bathes the scene in warm golden tones.

A PARK scene with GREEN GRASS and healthy TREES. Families laughing genuinely, children playing freely without surveillance. People making eye contact and SMILING REAL SMILES - not the guarded expressions of the corporate dystopia.

No corporate logos, no surveillance drones, no neon signs. CLEAN AIR, natural light, organic colors. People wearing simple, natural clothing in soft colors.

This is not the cyberpunk world - this is what was lost. Beautiful, innocent, human. A memory of what humanity gave up.

The style shifts completely from dark cyberpunk to bright, warm, almost dreamlike natural beauty. This contrast should be stark and emotionally moving.

EMOTIONAL ATMOSPHERE:
Revelation, mourning for what was lost, understanding why this memory is worth dying for.
The beautiful world that was erased.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
原来……我们曾经拥有过这样的世界。
```

---

### Shot 15: 新的开始

**场景**: 窗边，林夜握着记忆芯片，老陈在身后安详离去

| 字段 | 内容 |
|------|------|
| **shot_id** | 15 |
| **text_type** | narration |
| **speaker_position** | bottom |
| **characters_in_scene** | char_001, char_002 |

**image_prompt:**
```
STYLE: Cyberpunk / Neo-Noir

Cinematic cyberpunk aesthetic inspired by Blade Runner and Ghost in the Shell.
Dramatic neon lighting in pink, cyan, and purple against dark backgrounds.
Wet streets reflecting holographic advertisements. High-tech dystopian atmosphere.
Dense urban environments with towering buildings and holographic billboards.
Surveillance drones, neural interfaces, and cybernetic enhancements as visual elements.
Dark, moody atmosphere with pockets of vibrant neon color.

MUST INCLUDE: neon lights (pink, cyan, purple), wet reflective surfaces, holographic displays, dark atmosphere, futuristic technology, dense urban environment, dramatic lighting contrasts
DO NOT USE: bright daylight, natural colors, pastoral scenes, cartoon style, anime style, watercolor, hand-drawn look, clean bright environments

---

The window of the hideout overlooking the neon cityscape. Lin Ye (char_001) stands silhouetted against the glass, the MEMORY CHIP held in his hand. Neon light from outside casts pink and cyan on his face.

His SILVER CYBERNETIC LEFT EYE reflects the city lights. His expression shows determination mixed with grief. Dark gray jacket, thin scar on right cheek visible in the neon glow.

Behind him, Old Chen (char_002) lies peacefully on the platform, eyes closed, his life's mission complete. His WHITE HAIR and FADED BLUE JUMPSUIT visible. The old world photographs on the wall watch over them both like silent witnesses.

The composition shows Lin Ye looking out at the dystopian city he must now fight to change, armed with the truth. A new purpose born from an old man's sacrifice.

EMOTIONAL ATMOSPHERE:
Determination, bittersweet grief, new purpose. The battle is just beginning.
Carrying forward a sacred mission.

ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

**中文文字:**
```
老陈走了。但他的记忆，将成为新城地下最危险的秘密。林夜知道，他的战斗才刚刚开始。
```

---

## 技术验证重点

| 验证项 | 说明 |
|--------|------|
| **角色一致性** | 林夜的银色左眼义眼（蓝光）、凯拉的红色双义眼、老陈的白发蓝工装 |
| **赛博朋克风格** | 霓虹灯、湿地反光、全息广告、暗黑氛围持续稳定 |
| **科技元素** | 赛博义眼、神经接口、金属义肢正确渲染 |
| **记忆对比** | Shot 14 明亮自然光风格与其他暗黑镜头形成强烈对比 |
| **追逐场景** | Shot 10-11 的动态感和紧迫感 |
| **情感表达** | 紧张、绝望、希望等情绪的面部表情 |
| **泡泡位置** | AI推荐的bubble_x/y_percent不遮挡角色脸部 |

---

## 角色识别标记 (Character Identity Markers)

### 林夜 (char_001) - 必须在每张图中可见

| 标记 | 描述 |
|------|------|
| **义眼** | 左眼银色赛博义眼，有蓝色光芒（最关键标记） |
| **疤痕** | 右脸颊淡疤 |
| **服装** | 深灰色合成皮夹克 + 黑色高领 |
| **神经端口** | 左手腕发光神经接口（部分镜头可见） |

### 老陈 (char_002) - 必须在每张图中可见

| 标记 | 描述 |
|------|------|
| **头发** | 白发稀疏后梳 |
| **服装** | 褪色蓝色工装服（有旧公司标志） |
| **拐杖** | 金属拐杖，橡胶握柄磨损 |
| **神经端口** | 手背氧化的旧式神经端口 |
| **项链** | 旧记忆芯片挂在绳子上 |

### 凯拉 (char_003) - 必须在每张图中可见

| 标记 | 描述 |
|------|------|
| **头发** | 银白色短发，不对称侧分 |
| **义眼** | 双眼都是红色战斗型赛博义眼（最关键标记） |
| **义肢** | 右臂是全金属义肢（有隐藏武器） |
| **服装** | 黑色企业战术装甲 + 红色企业标志发光 |
| **表情** | 冷淡的计算性冷笑 |

---

## 下一步

1. @Backend 根据本脚本执行测试生成
2. @Tester 验收
3. 完成后 TASK-VERIFY-001 多风格验证全部完成

**预期输出目录**: `test_output/comic_full_story_v2_cyberpunk/`
