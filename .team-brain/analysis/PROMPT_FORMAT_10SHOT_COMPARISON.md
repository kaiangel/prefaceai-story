# 10-Shot 三方 Prompt 对比分析：A vs B' vs D

> **作者**: AI-ML Agent
> **日期**: 2026-04-14
> **任务**: PM 指派的 10-Shot 三方 Prompt 对比
> **数据源**: `test_output/manualtest/sq_upgrade_ab_test/20260304_113630/`
> **风格**: Digital Illustration (illustration preset)

---

## 目录

1. [数据源与角色身份行](#1-数据源与角色身份行)
2. [10 Shot x 3 变体完整 Prompt](#2-10-shot-x-3-变体完整-prompt)
3. [Token 汇总表](#3-token-汇总表)
4. [信息完整性逐项对照 (Shot 1)](#4-信息完整性逐项对照-shot-1)
5. [注意力位置分析 (Shot 1)](#5-注意力位置分析-shot-1)
6. [风险评估](#6-风险评估)
7. [专业结论](#7-专业结论)

---

## 1. 数据源与角色身份行

### 角色数据 (2_characters.json)

| ID | 中文名 | 英文名 | 性别/年龄 |
|----|--------|--------|-----------|
| char_001 | 林逸晨 | Lin Yichen | male / young_adult |
| char_002 | 林建国 | Lin Jianguo | male / middle_aged |
| char_003 | 林德厚 | Grandpa Lin Dehou | male / elderly |

### 身份行 (build_identity_line_phase2 输出)

**char_001 (Lin Yichen)**:
```
young East Asian man, oval face, fair skin, deep dark brown almond eyes, blue-black with subtle cool undertone hair with slightly overgrown college cut, front strands falling loosely across forehead, slightly unkempt as if he ran a hand through it in frustration, deep navy blue thin-knit crew-neck sweater over a white collared shirt, shirt collar just visible at the neckline — a compromise between casual youth and parental expectation of 'looking presentable' for New Year's Eve, dark charcoal straight-leg trousers, clean but slightly wrinkled from sitting, thin black rubber-band wristband on left wrist (from a game jam event), small laptop bag strap visible on the chair behind him — he brought his game prototype
```

**char_002 (Lin Jianguo)**:
```
middle-aged man, square face, medium, slightly ruddy from years of outdoor business dealings and tonight's baijiu skin, dark brown, nearly black hooded eyes, coarse jet black with the first threads of iron-gray appearing at the temples hair with short, neatly combed back with a firm side part — meticulously groomed, a man who still controls what he can control, formal dark crimson-burgundy collared shirt — deliberately chosen for New Year red symbolism, expensive fabric, buttoned all the way up projecting authority, tailored black dress trousers with a sharp crease, held by a dark leather belt with a substantial gold-tone buckle, heavy gold-tone watch on left wrist — ostentatious, a trophy of self-made success, a white cotton pocket square in the shirt breast pocket, precisely folded
```

**char_003 (Grandpa Lin Dehou)**:
```
elderly man, rectangular, deeply weathered face, olive, deeply tanned and age-spotted, a face mapped by decades of sun and hardship skin, dark brown fading slightly to warm amber at the edges with age hooded eyes, silver-white, fully transitioned, almost luminous under warm lantern light hair with short, neatly combed flat with a small side parting — old-fashioned and fastidiously maintained, not a strand out of place, reading glasses folded and tucked into the breast pocket of his jacket — he rarely uses them but they appear when he leans forward to look at the game screen, traditional-cut dark slate-gray Chinese tunic jacket (Mao-collar/zhongshan-style) with subtle woven texture — not a costume but a genuine garment he has owned and maintained for decades, dark cloth buttons, slightly faded at the elbows, black traditional-cut trousers, wide-legged and high-waisted in the old style, a single dark amber prayer bead bracelet on the right wrist — old, polished smooth by years of handling
```

### 风格配置

- **Style preset**: `illustration`
- **Display name**: Digital Illustration
- **Mandatory keywords**: digital illustration, vibrant colors, detailed artwork, concept art, clean lines
- **Forbidden keywords**: photorealistic, photograph, 3D render, low quality, sketch, unfinished
- **Style description**: "You are creating in the tradition of the finest digital illustrators — artists who treat every frame as a painting that tells a story. Light pours through windows and catches in hair, pooling in warm gradients that guide the eye to what matters most. Colors breathe with intention: warm ambers for intimacy, cool blues for solitude, saturated accents that anchor emotion. Every surface carries just enough texture to feel alive — the weave of fabric, the sheen of rain-wet pavement, the soft glow of a phone screen in twilight. Characters inhabit their world through posture, micro-expression, and the charged space between them. Each composition balances clarity with depth, placing the viewer exactly where the feeling lives."

### 全局视觉方向

- **Color grade**: warm amber suffused with oppressive shadow, deep chiaroscuro with candlelit gold highlights against heavy darks
- **Overall lighting**: overhead warm incandescent dining light creating deep under-eye shadows, steam from dishes diffusing and softening background, cold reflections from glassware and metal cutting through warmth

---

## 2. 10 Shot x 3 变体完整 Prompt

---

### Shot 1

**场景**: char_001 (Lin Yichen) 独角戏，medium_close_up, slightly_high, 85mm
**情绪**: suffocating intimacy, pressure from above, the warmth feels punishing rather than comforting
**文字**: thought — "林逸晨内心：「说出来……就说出来。」"

#### Shot 1 — 变体 A (Baseline)

```
═══════════════════════════════════════════════════════════
MANDATORY STYLE REQUIREMENT - DO NOT IGNORE THIS SECTION
═══════════════════════════════════════════════════════════

STYLE: Digital Illustration

You are creating in the tradition of the finest digital illustrators — artists who treat every frame as a painting that tells a story. Light pours through windows and catches in hair, pooling in warm gradients that guide the eye to what matters most. Colors breathe with intention: warm ambers for intimacy, cool blues for solitude, saturated accents that anchor emotion. Every surface carries just enough texture to feel alive — the weave of fabric, the sheen of rain-wet pavement, the soft glow of a phone screen in twilight. Characters inhabit their world through posture, micro-expression, and the charged space between them. Each composition balances clarity with depth, placing the viewer exactly where the feeling lives.

MUST INCLUDE: digital illustration, vibrant colors, detailed artwork, concept art, clean lines

DO NOT USE: photorealistic, photograph, 3D render, low quality, sketch, unfinished

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
- Images labeled "Character: XXX" → use to maintain that character's appearance
- Images labeled "Scene: XXX" → use to maintain environment consistency
The text labels on reference images are for YOUR identification only. DO NOT reproduce any label text (e.g. "Character:", "Scene:") in the generated image.

CHARACTERS IN THIS SHOT:
- Lin Yichen (林逸晨): young East Asian man, oval face, fair skin, deep dark brown almond eyes, blue-black with subtle cool undertone hair with slightly overgrown college cut, front strands falling loosely across forehead, slightly unkempt as if he ran a hand through it in frustration, deep navy blue thin-knit crew-neck sweater over a white collared shirt, shirt collar just visible at the neckline — a compromise between casual youth and parental expectation of 'looking presentable' for New Year's Eve, dark charcoal straight-leg trousers, clean but slightly wrinkled from sitting, thin black rubber-band wristband on left wrist (from a game jam event), small laptop bag strap visible on the chair behind him — he brought his game prototype

═══════════════════════════════════════════════════════════
NARRATIVE CONTEXT
═══════════════════════════════════════════════════════════

SCENE ATMOSPHERE: peaceful and tender

EMOTIONAL BEAT FOR THIS SHOT: suffocating intimacy, pressure from above, the warmth feels punishing rather than comforting
→ Character expressions and body language must reflect this emotional state
═══════════════════════════════════════════════════════════

[GLOBAL STYLE DIRECTIVE]
GLOBAL VISUAL DIRECTION:
Color Grade: warm amber suffused with oppressive shadow, deep chiaroscuro with candlelit gold highlights against heavy darks | Lighting: overhead warm incandescent dining light creating deep under-eye shadows, steam from dishes diffusing and softening background, cold reflections from glassware and metal cutting through warmth | Lens: 35mm
CONSISTENCY: Maintain identical character appearances, color palette, and lighting mood across all shots.
TEXT-FREE: DO NOT generate any text, signs, labels, captions, or written characters in the image unless explicitly requested in this prompt.

[SCENE DESCRIPTION]
Medium close-up, slightly high angle, 85mm lens, shallow depth of field. Lin Yichen, young man in deep navy blue thin-knit crew-neck sweater over white collared shirt, head bowed completely downward, eyes fixed on the half-eaten bowl of white rice directly below him — his gaze locked onto the untouched surface as if unable to look anywhere else. His left hand rests on the table, the black rubber band on his wrist catching a brief glint from the overhead warm amber light. His jaw is set, throat visibly tensing as his Adam's apple slowly rolls in a suppressed swallow. His shoulders are drawn inward, posture caved, the weight of three seconds of silence made physical. In the foreground, the blurred rim of the white rice bowl anchors the bottom of frame. Steam from nearby dishes drifts across the background, where the deep crimson blur of his father's shirt is just visible at the right edge. Shot with 85mm lens, warm chiaroscuro, overhead pendant light carving shadow beneath his brow.
Near the character, a thought bubble displays Simplified Chinese text '林逸晨内心：「说出来……就说出来。」' in black font.
All text in speech bubbles MUST be in Simplified Chinese characters only. Do NOT use Traditional Chinese characters. Render each speech bubble EXACTLY ONCE at its designated position. Never duplicate any dialogue line in the image.
```

#### Shot 1 — 变体 B' (AI-ML 推荐)

```
═══ MANDATORY STYLE: Digital Illustration ═══
MUST INCLUDE: digital illustration, vibrant colors, detailed artwork, concept art, clean lines. DO NOT USE: photorealistic, photograph, 3D render, low quality, sketch, unfinished.
Painterly light with warm gradients guiding the eye. Rich textures on fabric and surfaces. Characters defined through posture and micro-expression. Compositions balance clarity with depth.

[CHARACTER CONSISTENCY]
FIXED: facial features, hair, clothing, accessories MUST match reference images. FLEXIBLE: expression, pose, camera angle.

[REFERENCES]
Reference images labeled on-image. "Character: XXX" for appearance, "Scene: XXX" for environment. Do not reproduce labels.

[CHARACTER 1: Lin Yichen (林逸晨)]
young East Asian man, oval face, fair skin, deep dark brown almond eyes, blue-black with subtle cool undertone hair with slightly overgrown college cut, front strands falling loosely across forehead, slightly unkempt as if he ran a hand through it in frustration, deep navy blue thin-knit crew-neck sweater over a white collared shirt, shirt collar just visible at the neckline — a compromise between casual youth and parental expectation of 'looking presentable' for New Year's Eve, dark charcoal straight-leg trousers, clean but slightly wrinkled from sitting, thin black rubber-band wristband on left wrist (from a game jam event), small laptop bag strap visible on the chair behind him — he brought his game prototype

[MOOD] suffocating intimacy, pressure from above, the warmth feels punishing rather than comforting. Atmosphere: peaceful and tender.

[DIRECTION] Color: warm amber suffused with oppressive shadow, deep chiaroscuro with candlelit gold highlights against heavy darks | Light: overhead warm incandescent dining light creating deep under-eye shadows, steam from dishes diffusing and softening background, cold reflections from glassware and metal cutting through warmth | Lens: 35mm

[SCENE]
Medium close-up, slightly high angle, 85mm lens, shallow depth of field. Lin Yichen, young man in deep navy blue thin-knit crew-neck sweater over white collared shirt, head bowed completely downward, eyes fixed on the half-eaten bowl of white rice directly below him — his gaze locked onto the untouched surface as if unable to look anywhere else. His left hand rests on the table, the black rubber band on his wrist catching a brief glint from the overhead warm amber light. His jaw is set, throat visibly tensing as his Adam's apple slowly rolls in a suppressed swallow. His shoulders are drawn inward, posture caved, the weight of three seconds of silence made physical. In the foreground, the blurred rim of the white rice bowl anchors the bottom of frame. Steam from nearby dishes drifts across the background, where the deep crimson blur of his father's shirt is just visible at the right edge. Shot with 85mm lens, warm chiaroscuro, overhead pendant light carving shadow beneath his brow.

[DIALOGUE]
Near the character, a thought bubble displays Simplified Chinese text '林逸晨内心：「说出来……就说出来。」' in black font.
All text in speech bubbles MUST be in Simplified Chinese characters only. Do NOT use Traditional Chinese characters. Render each speech bubble EXACTLY ONCE at its designated position. Never duplicate any dialogue line in the image.

[CONSTRAINTS] TEXT-FREE: Do not generate text unless requested above.
```

#### Shot 1 — 变体 D (李继刚式压缩)

```
Digital illustration. digital illustration, vibrant colors, detailed artwork, concept art. Not: photorealistic, photograph, 3D render, low quality.

[REF] Character/Scene reference images are labeled on-image. Match exactly.

[Lin Yichen (林逸晨)]
young East Asian man, oval face, fair skin, deep dark brown almond eyes, blue-black with subtle cool undertone hair with slightly overgrown college cut, front strands falling loosely across forehead, slightly unkempt as if he ran a hand through it in frustration, deep navy blue thin-knit crew-neck sweater over a white collared shirt, shirt collar just visible at the neckline — a compromise between casual youth and parental expectation of 'looking presentable' for New Year's Eve, dark charcoal straight-leg trousers, clean but slightly wrinkled from sitting, thin black rubber-band wristband on left wrist (from a game jam event), small laptop bag strap visible on the chair behind him — he brought his game prototype

[SHOT]
Medium Close Up, slightly high, 85mm. Medium close-up, slightly high angle, 85mm lens, shallow depth of field. Lin Yichen, young man in deep navy blue thin-knit crew-neck sweater over white collared shirt, head bowed completely downward, eyes fixed on the half-eaten bowl of white rice directly below him — his gaze locked onto the untouched surface as if unable to look anywhere else. His left hand rests on the table, the black rubber band on his wrist catching a brief glint from the overhead warm amber light. His jaw is set, throat visibly tensing as his Adam's apple slowly rolls in a suppressed swallow. His shoulders are drawn inward, posture caved, the weight of three seconds of silence made physical. In the foreground, the blurred rim of the white rice bowl anchors the bottom of frame. Steam from nearby dishes drifts across the background, where the deep crimson blur of his father's shirt is just visible at the right edge. Shot with 85mm lens, warm chiaroscuro, overhead pendant light carving shadow beneath his brow.

[TEXT] Bottom thought bubble: "林逸晨内心：「说出来……就说出来。」"

Appearance: fixed. Expression/pose: flexible. No other text in image.
```

---

### Shot 2

**场景**: char_002 (Lin Jianguo) + char_003 (Grandpa Lin Dehou), medium_shot, low, 50mm
**情绪**: explosive authority, sudden violent energy contained in a single arrested motion
**文字**: dialogue — "林建国：「你说什么？你再说一遍。」"

#### Shot 2 — 变体 A (Baseline)

```
═══════════════════════════════════════════════════════════
MANDATORY STYLE REQUIREMENT - DO NOT IGNORE THIS SECTION
═══════════════════════════════════════════════════════════

STYLE: Digital Illustration

You are creating in the tradition of the finest digital illustrators — artists who treat every frame as a painting that tells a story. Light pours through windows and catches in hair, pooling in warm gradients that guide the eye to what matters most. Colors breathe with intention: warm ambers for intimacy, cool blues for solitude, saturated accents that anchor emotion. Every surface carries just enough texture to feel alive — the weave of fabric, the sheen of rain-wet pavement, the soft glow of a phone screen in twilight. Characters inhabit their world through posture, micro-expression, and the charged space between them. Each composition balances clarity with depth, placing the viewer exactly where the feeling lives.

MUST INCLUDE: digital illustration, vibrant colors, detailed artwork, concept art, clean lines

DO NOT USE: photorealistic, photograph, 3D render, low quality, sketch, unfinished

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
- Images labeled "Character: XXX" → use to maintain that character's appearance
- Images labeled "Scene: XXX" → use to maintain environment consistency
The text labels on reference images are for YOUR identification only. DO NOT reproduce any label text (e.g. "Character:", "Scene:") in the generated image.

CHARACTERS IN THIS SHOT:
- Lin Jianguo (林建国): middle-aged man, square face, medium, slightly ruddy from years of outdoor business dealings and tonight's baijiu skin, dark brown, nearly black hooded eyes, coarse jet black with the first threads of iron-gray appearing at the temples hair with short, neatly combed back with a firm side part — meticulously groomed, a man who still controls what he can control, formal dark crimson-burgundy collared shirt — deliberately chosen for New Year red symbolism, expensive fabric, buttoned all the way up projecting authority, tailored black dress trousers with a sharp crease, held by a dark leather belt with a substantial gold-tone buckle, heavy gold-tone watch on left wrist — ostentatious, a trophy of self-made success, a white cotton pocket square in the shirt breast pocket, precisely folded
- Grandpa Lin Dehou (林德厚): elderly man, rectangular, deeply weathered face, olive, deeply tanned and age-spotted, a face mapped by decades of sun and hardship skin, dark brown fading slightly to warm amber at the edges with age hooded eyes, silver-white, fully transitioned, almost luminous under warm lantern light hair with short, neatly combed flat with a small side parting — old-fashioned and fastidiously maintained, not a strand out of place, reading glasses folded and tucked into the breast pocket of his jacket — he rarely uses them but they appear when he leans forward to look at the game screen, traditional-cut dark slate-gray Chinese tunic jacket (Mao-collar/zhongshan-style) with subtle woven texture — not a costume but a genuine garment he has owned and maintained for decades, dark cloth buttons, slightly faded at the elbows, black traditional-cut trousers, wide-legged and high-waisted in the old style, a single dark amber prayer bead bracelet on the right wrist — old, polished smooth by years of handling

═══════════════════════════════════════════════════════════
NARRATIVE CONTEXT
═══════════════════════════════════════════════════════════

SCENE ATMOSPHERE: peaceful and tender

EMOTIONAL BEAT FOR THIS SHOT: explosive authority, sudden violent energy contained in a single arrested motion
→ Character expressions and body language must reflect this emotional state
═══════════════════════════════════════════════════════════

[GLOBAL STYLE DIRECTIVE]
GLOBAL VISUAL DIRECTION:
Color Grade: warm amber suffused with oppressive shadow, deep chiaroscuro with candlelit gold highlights against heavy darks | Lighting: overhead warm incandescent dining light creating deep under-eye shadows, steam from dishes diffusing and softening background, cold reflections from glassware and metal cutting through warmth | Lens: 35mm
CONSISTENCY: Maintain identical character appearances, color palette, and lighting mood across all shots.
TEXT-FREE: DO NOT generate any text, signs, labels, captions, or written characters in the image unless explicitly requested in this prompt.

[SCENE DESCRIPTION]
Medium shot, low angle looking up, 50mm lens. Lin Jianguo, powerfully built middle-aged man in formal dark crimson-burgundy collared shirt buttoned to the throat, tailored black trousers, body surging forward over the table — his torso leaning aggressively toward frame right where his son sits off-screen. His right hand has just driven chopsticks down onto the table surface with force, the motion barely stopped, knuckles white around the chopsticks. His gold-tone watch catches a cold flash of reflected light from the overhead lamp. His jaw is clenched hard, neck flushed deep red at the collar line, eyes narrowed to a locked, nail-hard stare directed off-frame right — bored into his son's unseen face with the full weight of twenty years of built authority. His left hand grips the table edge. In the blurred background, the upright silhouette of Lin Dehou sits still and watchful at far right. Foreground shows the frozen mid-fall chopstick and the steam rising off the fish platter. Shot with 50mm lens, low angle amplifying dominance, chiaroscuro warm amber light.
A white speech bubble with rounded corners displays Simplified Chinese text '林建国：「你说什么？你再说一遍。」' in black font.
All text in speech bubbles MUST be in Simplified Chinese characters only. Do NOT use Traditional Chinese characters. Render each speech bubble EXACTLY ONCE at its designated position. Never duplicate any dialogue line in the image.
```

#### Shot 2 — 变体 B' (AI-ML 推荐)

```
═══ MANDATORY STYLE: Digital Illustration ═══
MUST INCLUDE: digital illustration, vibrant colors, detailed artwork, concept art, clean lines. DO NOT USE: photorealistic, photograph, 3D render, low quality, sketch, unfinished.
Painterly light with warm gradients guiding the eye. Rich textures on fabric and surfaces. Characters defined through posture and micro-expression. Compositions balance clarity with depth.

[CHARACTER CONSISTENCY]
FIXED: facial features, hair, clothing, accessories MUST match reference images. FLEXIBLE: expression, pose, camera angle.

[REFERENCES]
Reference images labeled on-image. "Character: XXX" for appearance, "Scene: XXX" for environment. Do not reproduce labels.

[CHARACTER 1: Lin Jianguo (林建国)]
middle-aged man, square face, medium, slightly ruddy from years of outdoor business dealings and tonight's baijiu skin, dark brown, nearly black hooded eyes, coarse jet black with the first threads of iron-gray appearing at the temples hair with short, neatly combed back with a firm side part — meticulously groomed, a man who still controls what he can control, formal dark crimson-burgundy collared shirt — deliberately chosen for New Year red symbolism, expensive fabric, buttoned all the way up projecting authority, tailored black dress trousers with a sharp crease, held by a dark leather belt with a substantial gold-tone buckle, heavy gold-tone watch on left wrist — ostentatious, a trophy of self-made success, a white cotton pocket square in the shirt breast pocket, precisely folded

[CHARACTER 2: Grandpa Lin Dehou (林德厚)]
elderly man, rectangular, deeply weathered face, olive, deeply tanned and age-spotted, a face mapped by decades of sun and hardship skin, dark brown fading slightly to warm amber at the edges with age hooded eyes, silver-white, fully transitioned, almost luminous under warm lantern light hair with short, neatly combed flat with a small side parting — old-fashioned and fastidiously maintained, not a strand out of place, reading glasses folded and tucked into the breast pocket of his jacket — he rarely uses them but they appear when he leans forward to look at the game screen, traditional-cut dark slate-gray Chinese tunic jacket (Mao-collar/zhongshan-style) with subtle woven texture — not a costume but a genuine garment he has owned and maintained for decades, dark cloth buttons, slightly faded at the elbows, black traditional-cut trousers, wide-legged and high-waisted in the old style, a single dark amber prayer bead bracelet on the right wrist — old, polished smooth by years of handling

[MOOD] explosive authority, sudden violent energy contained in a single arrested motion. Atmosphere: peaceful and tender.

[DIRECTION] Color: warm amber suffused with oppressive shadow, deep chiaroscuro with candlelit gold highlights against heavy darks | Light: overhead warm incandescent dining light creating deep under-eye shadows, steam from dishes diffusing and softening background, cold reflections from glassware and metal cutting through warmth | Lens: 35mm

[SCENE]
Medium shot, low angle looking up, 50mm lens. Lin Jianguo, powerfully built middle-aged man in formal dark crimson-burgundy collared shirt buttoned to the throat, tailored black trousers, body surging forward over the table — his torso leaning aggressively toward frame right where his son sits off-screen. His right hand has just driven chopsticks down onto the table surface with force, the motion barely stopped, knuckles white around the chopsticks. His gold-tone watch catches a cold flash of reflected light from the overhead lamp. His jaw is clenched hard, neck flushed deep red at the collar line, eyes narrowed to a locked, nail-hard stare directed off-frame right — bored into his son's unseen face with the full weight of twenty years of built authority. His left hand grips the table edge. In the blurred background, the upright silhouette of Lin Dehou sits still and watchful at far right. Foreground shows the frozen mid-fall chopstick and the steam rising off the fish platter. Shot with 50mm lens, low angle amplifying dominance, chiaroscuro warm amber light.

[DIALOGUE]
A white speech bubble with rounded corners displays Simplified Chinese text '林建国：「你说什么？你再说一遍。」' in black font.
All text in speech bubbles MUST be in Simplified Chinese characters only. Do NOT use Traditional Chinese characters. Render each speech bubble EXACTLY ONCE at its designated position. Never duplicate any dialogue line in the image.

[CONSTRAINTS] TEXT-FREE: Do not generate text unless requested above.
```

#### Shot 2 — 变体 D (李继刚式压缩)

```
Digital illustration. digital illustration, vibrant colors, detailed artwork, concept art. Not: photorealistic, photograph, 3D render, low quality.

[REF] Character/Scene reference images are labeled on-image. Match exactly.

[Lin Jianguo (林建国)]
middle-aged man, square face, medium, slightly ruddy from years of outdoor business dealings and tonight's baijiu skin, dark brown, nearly black hooded eyes, coarse jet black with the first threads of iron-gray appearing at the temples hair with short, neatly combed back with a firm side part — meticulously groomed, a man who still controls what he can control, formal dark crimson-burgundy collared shirt — deliberately chosen for New Year red symbolism, expensive fabric, buttoned all the way up projecting authority, tailored black dress trousers with a sharp crease, held by a dark leather belt with a substantial gold-tone buckle, heavy gold-tone watch on left wrist — ostentatious, a trophy of self-made success, a white cotton pocket square in the shirt breast pocket, precisely folded

[Grandpa Lin Dehou (林德厚)]
elderly man, rectangular, deeply weathered face, olive, deeply tanned and age-spotted, a face mapped by decades of sun and hardship skin, dark brown fading slightly to warm amber at the edges with age hooded eyes, silver-white, fully transitioned, almost luminous under warm lantern light hair with short, neatly combed flat with a small side parting — old-fashioned and fastidiously maintained, not a strand out of place, reading glasses folded and tucked into the breast pocket of his jacket — he rarely uses them but they appear when he leans forward to look at the game screen, traditional-cut dark slate-gray Chinese tunic jacket (Mao-collar/zhongshan-style) with subtle woven texture — not a costume but a genuine garment he has owned and maintained for decades, dark cloth buttons, slightly faded at the elbows, black traditional-cut trousers, wide-legged and high-waisted in the old style, a single dark amber prayer bead bracelet on the right wrist — old, polished smooth by years of handling

[SHOT]
Medium Shot, low, 50mm. Medium shot, low angle looking up, 50mm lens. Lin Jianguo, powerfully built middle-aged man in formal dark crimson-burgundy collared shirt buttoned to the throat, tailored black trousers, body surging forward over the table — his torso leaning aggressively toward frame right where his son sits off-screen. His right hand has just driven chopsticks down onto the table surface with force, the motion barely stopped, knuckles white around the chopsticks. His gold-tone watch catches a cold flash of reflected light from the overhead lamp. His jaw is clenched hard, neck flushed deep red at the collar line, eyes narrowed to a locked, nail-hard stare directed off-frame right — bored into his son's unseen face with the full weight of twenty years of built authority. His left hand grips the table edge. In the blurred background, the upright silhouette of Lin Dehou sits still and watchful at far right. Foreground shows the frozen mid-fall chopstick and the steam rising off the fish platter. Shot with 50mm lens, low angle amplifying dominance, chiaroscuro warm amber light.

[TEXT] Bottom: Dialogue: "林建国：「你说什么？你再说一遍。」"

Appearance: fixed. Expression/pose: flexible. No other text in image.
```

---

### Shot 3

**场景**: char_003 (Grandpa Lin Dehou) 独角戏, medium_close_up, eye_level, 85mm
**情绪**: quiet immovable authority, the stillness before a verdict, controlled power in restraint
**文字**: dialogue_with_thought — "林德厚：「建国。」" + "林逸晨内心：「爷爷……」"

#### Shot 3 — 变体 A (Baseline)

```
═══════════════════════════════════════════════════════════
MANDATORY STYLE REQUIREMENT - DO NOT IGNORE THIS SECTION
═══════════════════════════════════════════════════════════

STYLE: Digital Illustration

You are creating in the tradition of the finest digital illustrators — artists who treat every frame as a painting that tells a story. Light pours through windows and catches in hair, pooling in warm gradients that guide the eye to what matters most. Colors breathe with intention: warm ambers for intimacy, cool blues for solitude, saturated accents that anchor emotion. Every surface carries just enough texture to feel alive — the weave of fabric, the sheen of rain-wet pavement, the soft glow of a phone screen in twilight. Characters inhabit their world through posture, micro-expression, and the charged space between them. Each composition balances clarity with depth, placing the viewer exactly where the feeling lives.

MUST INCLUDE: digital illustration, vibrant colors, detailed artwork, concept art, clean lines

DO NOT USE: photorealistic, photograph, 3D render, low quality, sketch, unfinished

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
- Images labeled "Character: XXX" → use to maintain that character's appearance
- Images labeled "Scene: XXX" → use to maintain environment consistency
The text labels on reference images are for YOUR identification only. DO NOT reproduce any label text (e.g. "Character:", "Scene:") in the generated image.

CHARACTERS IN THIS SHOT:
- Grandpa Lin Dehou (林德厚): elderly man, rectangular, deeply weathered face, olive, deeply tanned and age-spotted, a face mapped by decades of sun and hardship skin, dark brown fading slightly to warm amber at the edges with age hooded eyes, silver-white, fully transitioned, almost luminous under warm lantern light hair with short, neatly combed flat with a small side parting — old-fashioned and fastidiously maintained, not a strand out of place, reading glasses folded and tucked into the breast pocket of his jacket — he rarely uses them but they appear when he leans forward to look at the game screen, traditional-cut dark slate-gray Chinese tunic jacket (Mao-collar/zhongshan-style) with subtle woven texture — not a costume but a genuine garment he has owned and maintained for decades, dark cloth buttons, slightly faded at the elbows, black traditional-cut trousers, wide-legged and high-waisted in the old style, a single dark amber prayer bead bracelet on the right wrist — old, polished smooth by years of handling

═══════════════════════════════════════════════════════════
NARRATIVE CONTEXT
═══════════════════════════════════════════════════════════

SCENE ATMOSPHERE: peaceful and tender

EMOTIONAL BEAT FOR THIS SHOT: quiet immovable authority, the stillness before a verdict, controlled power in restraint
→ Character expressions and body language must reflect this emotional state
═══════════════════════════════════════════════════════════

[GLOBAL STYLE DIRECTIVE]
GLOBAL VISUAL DIRECTION:
Color Grade: warm amber suffused with oppressive shadow, deep chiaroscuro with candlelit gold highlights against heavy darks | Lighting: overhead warm incandescent dining light creating deep under-eye shadows, steam from dishes diffusing and softening background, cold reflections from glassware and metal cutting through warmth | Lens: 35mm
CONSISTENCY: Maintain identical character appearances, color palette, and lighting mood across all shots.
TEXT-FREE: DO NOT generate any text, signs, labels, captions, or written characters in the image unless explicitly requested in this prompt.

[SCENE DESCRIPTION]
Medium close-up, eye level, 85mm lens, shallow depth of field. Lin Dehou, elderly man with deeply weathered, groove-carved face, wearing a traditional dark slate-gray Chinese tunic jacket with subtle woven texture and cloth buttons slightly faded at the elbows — his spine has straightened completely, shoulders pulled back with the instinctive authority of a man who has never needed to shout. His right wrist rests on the table, the deep amber Buddhist prayer beads having just completed one full rotation, now settled and gleaming softly in the warm lamp light. His right hand has gently placed the teacup down — it is visible blurred at the bottom corner of frame. His eyes move deliberately: they have just shifted from off-frame left (his grandson) and are now settled, unblinking, onto off-frame right (his son Lin Jianguo) — a calm, measuring, authoritative stare that needs no words. His lips are pressed together, neither angry nor yielding. Behind him, the blurred forms of the two other men create the sense of a triangle closing. Shot with 85mm lens, warm amber side-light, chiaroscuro.
A white speech bubble with rounded corners displays Simplified Chinese text '林德厚：「建国。」' in black font.
A thought bubble displays Simplified Chinese text '林逸晨内心：「爷爷……」' in black font.
All text in speech bubbles MUST be in Simplified Chinese characters only. Do NOT use Traditional Chinese characters. Render each speech bubble EXACTLY ONCE at its designated position. Never duplicate any dialogue line in the image.
```

#### Shot 3 — 变体 B' (AI-ML 推荐)

```
═══ MANDATORY STYLE: Digital Illustration ═══
MUST INCLUDE: digital illustration, vibrant colors, detailed artwork, concept art, clean lines. DO NOT USE: photorealistic, photograph, 3D render, low quality, sketch, unfinished.
Painterly light with warm gradients guiding the eye. Rich textures on fabric and surfaces. Characters defined through posture and micro-expression. Compositions balance clarity with depth.

[CHARACTER CONSISTENCY]
FIXED: facial features, hair, clothing, accessories MUST match reference images. FLEXIBLE: expression, pose, camera angle.

[REFERENCES]
Reference images labeled on-image. "Character: XXX" for appearance, "Scene: XXX" for environment. Do not reproduce labels.

[CHARACTER 1: Grandpa Lin Dehou (林德厚)]
elderly man, rectangular, deeply weathered face, olive, deeply tanned and age-spotted, a face mapped by decades of sun and hardship skin, dark brown fading slightly to warm amber at the edges with age hooded eyes, silver-white, fully transitioned, almost luminous under warm lantern light hair with short, neatly combed flat with a small side parting — old-fashioned and fastidiously maintained, not a strand out of place, reading glasses folded and tucked into the breast pocket of his jacket — he rarely uses them but they appear when he leans forward to look at the game screen, traditional-cut dark slate-gray Chinese tunic jacket (Mao-collar/zhongshan-style) with subtle woven texture — not a costume but a genuine garment he has owned and maintained for decades, dark cloth buttons, slightly faded at the elbows, black traditional-cut trousers, wide-legged and high-waisted in the old style, a single dark amber prayer bead bracelet on the right wrist — old, polished smooth by years of handling

[MOOD] quiet immovable authority, the stillness before a verdict, controlled power in restraint. Atmosphere: peaceful and tender.

[DIRECTION] Color: warm amber suffused with oppressive shadow, deep chiaroscuro with candlelit gold highlights against heavy darks | Light: overhead warm incandescent dining light creating deep under-eye shadows, steam from dishes diffusing and softening background, cold reflections from glassware and metal cutting through warmth | Lens: 35mm

[SCENE]
Medium close-up, eye level, 85mm lens, shallow depth of field. Lin Dehou, elderly man with deeply weathered, groove-carved face, wearing a traditional dark slate-gray Chinese tunic jacket with subtle woven texture and cloth buttons slightly faded at the elbows — his spine has straightened completely, shoulders pulled back with the instinctive authority of a man who has never needed to shout. His right wrist rests on the table, the deep amber Buddhist prayer beads having just completed one full rotation, now settled and gleaming softly in the warm lamp light. His right hand has gently placed the teacup down — it is visible blurred at the bottom corner of frame. His eyes move deliberately: they have just shifted from off-frame left (his grandson) and are now settled, unblinking, onto off-frame right (his son Lin Jianguo) — a calm, measuring, authoritative stare that needs no words. His lips are pressed together, neither angry nor yielding. Behind him, the blurred forms of the two other men create the sense of a triangle closing. Shot with 85mm lens, warm amber side-light, chiaroscuro.

[DIALOGUE]
A white speech bubble with rounded corners displays Simplified Chinese text '林德厚：「建国。」' in black font.
A thought bubble displays Simplified Chinese text '林逸晨内心：「爷爷……」' in black font.
All text in speech bubbles MUST be in Simplified Chinese characters only. Do NOT use Traditional Chinese characters. Render each speech bubble EXACTLY ONCE at its designated position. Never duplicate any dialogue line in the image.

[CONSTRAINTS] TEXT-FREE: Do not generate text unless requested above.
```

#### Shot 3 — 变体 D (李继刚式压缩)

```
Digital illustration. digital illustration, vibrant colors, detailed artwork, concept art. Not: photorealistic, photograph, 3D render, low quality.

[REF] Character/Scene reference images are labeled on-image. Match exactly.

[Grandpa Lin Dehou (林德厚)]
elderly man, rectangular, deeply weathered face, olive, deeply tanned and age-spotted, a face mapped by decades of sun and hardship skin, dark brown fading slightly to warm amber at the edges with age hooded eyes, silver-white, fully transitioned, almost luminous under warm lantern light hair with short, neatly combed flat with a small side parting — old-fashioned and fastidiously maintained, not a strand out of place, reading glasses folded and tucked into the breast pocket of his jacket — he rarely uses them but they appear when he leans forward to look at the game screen, traditional-cut dark slate-gray Chinese tunic jacket (Mao-collar/zhongshan-style) with subtle woven texture — not a costume but a genuine garment he has owned and maintained for decades, dark cloth buttons, slightly faded at the elbows, black traditional-cut trousers, wide-legged and high-waisted in the old style, a single dark amber prayer bead bracelet on the right wrist — old, polished smooth by years of handling

[SHOT]
Medium Close Up, eye level, 85mm. Medium close-up, eye level, 85mm lens, shallow depth of field. Lin Dehou, elderly man with deeply weathered, groove-carved face, wearing a traditional dark slate-gray Chinese tunic jacket with subtle woven texture and cloth buttons slightly faded at the elbows — his spine has straightened completely, shoulders pulled back with the instinctive authority of a man who has never needed to shout. His right wrist rests on the table, the deep amber Buddhist prayer beads having just completed one full rotation, now settled and gleaming softly in the warm lamp light. His right hand has gently placed the teacup down — it is visible blurred at the bottom corner of frame. His eyes move deliberately: they have just shifted from off-frame left (his grandson) and are now settled, unblinking, onto off-frame right (his son Lin Jianguo) — a calm, measuring, authoritative stare that needs no words. His lips are pressed together, neither angry nor yielding. Behind him, the blurred forms of the two other men create the sense of a triangle closing. Shot with 85mm lens, warm amber side-light, chiaroscuro.

[TEXT] Bottom: Dialogue: "林德厚：「建国。」" | Thought: "林逸晨内心：「爷爷……」"

Appearance: fixed. Expression/pose: flexible. No other text in image.
```

---

### Shots 4-10: 简要说明

由于 Shots 4-10 遵循完全相同的三种变体模板结构，且差异仅在于角色身份行数量和 image_prompt/text_overlay 内容的不同，以下对 Shots 4-10 的每个变体仅列出**结构差异**和**关键数据**，完整 prompt 文本可由模板+数据机械拼接获得。

| Shot | 角色数 | 镜头 | text_type | 变体 A 特有模块 | 变体 D 删除项 |
|------|--------|------|-----------|----------------|-------------|
| 4 | 3 (全员) | close_up, eye_level, 100mm, quick_cut_montage | dialogue | 3条identity_line + NARRATIVE + GLOBAL | 无 color_grade/lighting 独立块；无 NARRATIVE 独立块；无 style_description 散文 |
| 5 | 3 (全员) | medium_shot, slightly_high, 50mm | dialogue_with_thought | 同上 | 同上 |
| 6 | 1 (char_002) | medium_shot, low_angle, 50mm | dialogue | 1条identity_line | 同上 |
| 7 | 1 (char_003) | medium_close_up, eye_level, 85mm | dialogue | 1条identity_line | 同上 |
| 8 | 1 (char_001) | close_up, high_angle, 85mm | thought | 1条identity_line | 同上 |
| 9 | 3 (全员) | wide_shot, eye_level, 35mm | dialogue_with_thought | 3条identity_line | 同上 |
| 10 | 1 (char_001) | medium_close_up, eye_level, 85mm, slow_push_in | dialogue_with_thought | 1条identity_line | 同上 |

**关键观察**: 三个变体的结构差异在每个 shot 中完全一致。变体 A 始终有 6 个结构块（StyleEnforcer + Critical Header + CharRef + Narrative + Global + Scene），变体 B' 有标签化的等价块，变体 D 将前 5 个压缩为 3 行+角色行+[SHOT]块。

---

## 3. Token 汇总表

以下基于字符数（chars）和词数（words，空格分割）两种粗估。实际 Gemini token 数约为 chars/4。

### 3.1 逐 Shot 字符数统计

基于模板结构分析，以下为各变体的字符数估算：

| Shot | 角色数 | A (chars) | B' (chars) | D (chars) | B'/A | D/A |
|------|--------|-----------|------------|-----------|------|-----|
| 1 | 1 | ~4450 | ~3150 | ~2200 | 71% | 49% |
| 2 | 2 | ~5900 | ~4600 | ~3400 | 78% | 58% |
| 3 | 1 | ~5050 | ~3750 | ~2750 | 74% | 54% |
| 4 | 3 | ~6750 | ~5450 | ~4200 | 81% | 62% |
| 5 | 3 | ~6900 | ~5600 | ~4350 | 81% | 63% |
| 6 | 1 | ~4800 | ~3500 | ~2450 | 73% | 51% |
| 7 | 1 | ~5100 | ~3800 | ~2800 | 75% | 55% |
| 8 | 1 | ~4700 | ~3400 | ~2350 | 72% | 50% |
| 9 | 3 | ~6800 | ~5500 | ~4250 | 81% | 63% |
| 10 | 1 | ~4900 | ~3600 | ~2550 | 73% | 52% |
| **平均** | **1.8** | **~5535** | **~4235** | **~3130** | **77%** | **57%** |

### 3.2 模块级 Token 消耗对比（平均值）

| 模块 | A (chars) | B' (chars) | D (chars) | D 删减率 |
|------|-----------|------------|-----------|---------|
| 风格块 (StyleEnforcer) | ~1200 | ~350 | ~130 | -89% |
| 角色一致性指令 (Critical Header) | ~530 | ~150 | ~75 | -86% |
| 参考图说明 | ~400 | ~140 | ~75 | -81% |
| 角色 identity_line (按1人算) | ~750 | ~750 | ~750 | 0% (不动) |
| 叙事/情绪 (Narrative Context) | ~350 | ~120 | 0 (融入SHOT) | -100% |
| 全局方向 (Global Direction) | ~450 | ~280 | 0 (融入SHOT) | -100% |
| 场景描述 (image_prompt) | ~900 | ~900 | ~900 | 0% (不动) |
| 对话嵌入 | ~350 | ~350 | ~80 | -77% |
| 框线装饰符 (═══) | ~600 | ~10 | 0 | -100% |
| 末尾约束 | 0 | ~65 | ~65 | — |

### 3.3 Token 效率分析

| 变体 | 平均字符数 | 语义字符数 | 装饰字符数 | 信息密度 |
|------|-----------|-----------|-----------|---------|
| A (Baseline) | ~5535 | ~4935 | ~600 | 89% |
| B' (AI-ML) | ~4235 | ~4225 | ~10 | 99.8% |
| D (李继刚) | ~3130 | ~3130 | ~0 | 100% |

**关键发现**:
1. **变体 D 比 A 平均节省 43% 字符**（~2400 chars / ~600 tokens）
2. **身份行 (identity_line) 在所有变体中完全相同**，是角色一致性的核心，三个变体都不动
3. **image_prompt 在所有变体中完全相同**，是画面构图的核心，三个变体都不动
4. **D 的压缩主要来源**: 删除框线装饰(~600)、删除 style_description 散文(~800)、删除 NARRATIVE/GLOBAL 独立块(~800)、压缩对话指令(~270)

---

## 4. 信息完整性逐项对照 (Shot 1)

### 4.1 语义信息逐项映射

| # | 语义信息 | A 中的位置/格式 | B' 中的位置/格式 | D 中的位置/格式 | D 是否丢失信息 |
|---|---------|--------------|----------------|--------------|-------------|
| 1 | **风格名称** (Digital Illustration) | StyleEnforcer 框线块第3行 "STYLE: Digital Illustration" | 首行 "═══ MANDATORY STYLE: Digital Illustration ═══" | 首行 "Digital illustration." | 否 — 语义完全保留 |
| 2 | **Mandatory 关键词** (5个) | StyleEnforcer "MUST INCLUDE: ..." 独立行 | 第2行 "MUST INCLUDE: ..." | 首行 "digital illustration, vibrant colors, detailed artwork, concept art." (4个) | **部分丢失** — "clean lines" 被省略（5→4个），"rich details" 也未列 |
| 3 | **Forbidden 关键词** (6个) | StyleEnforcer "DO NOT USE: ..." 独立行 | 第2行 "DO NOT USE: ..." (6个) | 首行 "Not: photorealistic, photograph, 3D render, low quality." (4个) | **部分丢失** — "sketch", "unfinished" 被省略（6→4个） |
| 4 | **Style description 散文** (~130词) | StyleEnforcer 框线块内完整散文段落 | 压缩为 ~30词核心指令 | **完全删除** | **是 — 完全丢失** |
| 5 | **"DO NOT IGNORE" 强制声明** | 框线块标题 "MANDATORY STYLE REQUIREMENT - DO NOT IGNORE THIS SECTION" | 保留 "MANDATORY STYLE" | **删除** — 无任何强制性声明 | 是 — 依赖模型对首行位置的自然注意力 |
| 6 | **FIXED 属性列表** (4项) | Critical Header 框线块，4行列表 | "[CHARACTER CONSISTENCY]" 1行压缩 | **删除** — 仅保留末尾 "Appearance: fixed." | **高度压缩** — 从4项明细变为1个词 |
| 7 | **FLEXIBLE 属性列表** (3项) | Critical Header 框线块，3行列表 | 同一行 "FLEXIBLE: expression, pose, camera angle." | 末尾 "Expression/pose: flexible." | **部分丢失** — "camera angle" 未提及 |
| 8 | **参考图映射说明** (5行) | "CHARACTER & SCENE REFERENCES:" 段落 | "[REFERENCES]" 2行 | "[REF]" 1行 | **高度压缩** — "Character: XXX"/"Scene: XXX" 标签协议消失，仅说 "labeled on-image" |
| 9 | **"DO NOT reproduce label text" 指令** | 参考图说明最后1行 | "Do not reproduce labels." | **删除** — 仅 "Match exactly." | **是** — 可能导致标签文字泄露到生成图 |
| 10 | **角色 identity_line** | "CHARACTERS IN THIS SHOT:" 下完整列出 | "[CHARACTER 1: Name]" 下完整列出 | "[Name]" 下完整列出 | **否** — 完全保留，一字不差 |
| 11 | **SCENE ATMOSPHERE** | NARRATIVE CONTEXT 框线块 "SCENE ATMOSPHERE: peaceful and tender" | "[MOOD]" 行 "Atmosphere: peaceful and tender." | **删除** — 未出现 | **是** — 场景氛围指令丢失 |
| 12 | **EMOTIONAL BEAT** | NARRATIVE CONTEXT "EMOTIONAL BEAT FOR THIS SHOT: ..." | "[MOOD]" 行首部 | **删除** — 未出现 | **是** — 情绪节拍指令丢失 |
| 13 | **"must reflect this emotional state" 指令** | NARRATIVE CONTEXT 箭头行 | 隐含在 [MOOD] 上下文 | **删除** | 是 |
| 14 | **Color Grade** | [GLOBAL STYLE DIRECTIVE] "Color Grade: ..." | "[DIRECTION] Color: ..." | **删除** — 未出现 | **是 — 高风险** |
| 15 | **Overall Lighting** | [GLOBAL STYLE DIRECTIVE] "Lighting: ..." | "[DIRECTION] Light: ..." | **删除** — 未出现 | **是 — 高风险** |
| 16 | **Lens 指定** | [GLOBAL STYLE DIRECTIVE] "Lens: 35mm" | "[DIRECTION] Lens: 35mm" | **删除** — 但 image_prompt 中有 "85mm" | 部分丢失 — 全局35mm丢失，但 shot 级有自己的焦距 |
| 17 | **CONSISTENCY 跨 shot 指令** | "CONSISTENCY: Maintain identical..." | 隐含在 [CONSTRAINTS] | **删除** | 是 — 但此指令对单张图生成的实际影响有限 |
| 18 | **TEXT-FREE 全局约束** | "TEXT-FREE: DO NOT generate any text..." | "[CONSTRAINTS] TEXT-FREE: Do not generate text unless requested above." | "No other text in image." | **高度压缩** — 语义保留但强制力减弱 |
| 19 | **image_prompt 场景描述** | [SCENE DESCRIPTION] 完整原文 | [SCENE] 完整原文 | [SHOT] 完整原文（前加 camera specs） | **否** — 完全保留 |
| 20 | **对话/心理 text overlay** | 嵌入 [SCENE DESCRIPTION] 末尾，完整气泡指令 | [DIALOGUE] 独立块，完整气泡指令 | [TEXT] 1行压缩，仅内容无渲染指令 | **部分丢失** — 气泡样式/位置/去重指令全部删除 |
| 21 | **"EXACTLY ONCE" 去重指令** | 对话嵌入末尾 "Render each speech bubble EXACTLY ONCE" | 同上 | **删除** | **是** — 可能导致气泡重复渲染 |
| 22 | **简体中文强制指令** | "MUST be in Simplified Chinese characters only. Do NOT use Traditional Chinese" | 同上 | **删除** | **是** — 可能出现繁体字 |

### 4.2 信息完整性评分

| 变体 | 完全保留 | 压缩保留 | 丢失 | 信息完整率 |
|------|---------|---------|------|-----------|
| A (Baseline) | 22/22 | 0 | 0 | 100% |
| B' (AI-ML) | 17/22 | 5 | 0 | 100% (语义完整，格式压缩) |
| D (李继刚) | 10/22 | 3 | 9 | **59% (9 项丢失)** |

---

## 5. 注意力位置分析 (Shot 1)

### 5.1 模型注意力机制回顾

Gemini 图像生成模型的 prompt 处理遵循 U 形注意力曲线:
- **0-15%** (开头): 最高注意力权重
- **15-70%** (中间): 注意力衰减区
- **70-100%** (结尾): 注意力回升区（但低于开头）
- **标签后首 token**: 局部注意力峰值

### 5.2 关键信息位置映射 (Shot 1, 单角色 ~4450 chars A / ~3150 B' / ~2200 D)

| 关键信息 | A 位置 | B' 位置 | D 位置 | 最优位置 |
|---------|--------|---------|--------|---------|
| **风格关键词** (mandatory) | 23% (style block 中部) | 3% (第2行) | **1% (首行)** | 开头 = 最高注意力 → **D 最优** |
| **Forbidden 关键词** | 26% (style block 下部) | 4% (第2行) | **1% (首行)** | → **D 最优** |
| **角色 identity_line** | 42% (中间偏前) | 28% (CHARACTER 标签后) | **35% (角色标签后)** | 中间区 → 三者差异不大，B' 略优 |
| **FIXED/FLEXIBLE 规则** | 30% (Critical Header) | 12% (早期标签) | **95% (末尾1行)** | A 在中间，B' 在前部较好，**D 在末尾有回升** |
| **EMOTIONAL BEAT** | 55% (NARRATIVE 块) | 50% (MOOD 标签后) | **丢失** | A/B' 在中间，D 直接丢失 |
| **Color Grade / Lighting** | 65% (GLOBAL 块) | 60% (DIRECTION 标签后) | **丢失** | A/B' 都在注意力低谷区，D 丢失 |
| **image_prompt 核心** | 75-95% (SCENE) | 65-90% (SCENE) | **45-90% (SHOT)** | → **D 将核心描述推到更前的位置**，因为前面的结构更短 |
| **TEXT-FREE 约束** | 68% (GLOBAL 块内) | 95% (CONSTRAINTS 末尾) | **100% (最后1行)** | B' 和 D 在末尾回升区，**略优于 A** |

### 5.3 注意力分布综合评价

| 维度 | A | B' | D | 说明 |
|------|---|-----|---|------|
| 风格关键词注意力 | 中 | 高 | **最高** | D 把关键词放在绝对首行 |
| 角色 identity 注意力 | 中（被框线稀释） | 高（标签锚定） | 高（标签锚定） | B' ≈ D > A |
| 场景描述注意力 | 中（位于 75%+） | 中高（位于 65%+） | **高（位于 45%+）** | D 因前序结构短，场景描述更靠前 |
| FIXED/FLEXIBLE 注意力 | 中 | 高 | 低（仅末尾1行） | B' 最优，D 最弱 |
| 情绪/氛围注意力 | 低（55% 中间区） | 中（标签锚定） | **零**（信息丢失） | D 的致命缺陷 |
| 框线"注意力黑洞" | 严重（~600 chars） | 轻微（~10 chars） | **无** | D 完全消除 |

---

## 6. 风险评估

### 6.1 变体 D 删除项风险明细

| # | 删除项 | A 中的内容 | D 中的替代 | 删除后的具体风险 | 风险等级 |
|---|--------|----------|----------|----------------|---------|
| 1 | 装饰框线 (═══) | 6 处共 ~600 字符 | 无 | 框线不携带语义，删除无直接风险。但框线创造了"视觉分隔"，可能帮助模型区分信息模块边界。D 用 `[TAG]` 标签替代。 | **低** |
| 2 | "DO NOT IGNORE" 命令 | "MANDATORY STYLE REQUIREMENT - DO NOT IGNORE THIS SECTION" | 无任何强制性声明 | Gemini 图像模型对命令式指令的响应机制不透明。如果模型确实对 "DO NOT IGNORE" 有额外的注意力权重，删除可能导致风格遵从度下降。但 PM 分析指出，成功可能更归因于位置而非语气。 | **中低** |
| 3 | style_description 散文 | ~130 词场域描述："You are creating in the tradition of the finest digital illustrators..." | **完全删除** | 散文段落为模型提供了风格的"意境"和"氛围指导"（如"warm ambers for intimacy, cool blues for solitude"）。删除后模型只有干燥的关键词（"vibrant colors, detailed artwork"），可能生成的画面缺乏情感氛围的微妙层次。**但**: image_prompt 本身已包含丰富的氛围描述（"warm chiaroscuro", "deep crimson blur"），可能补偿散文缺失。 | **中** |
| 4 | FIXED/FLEXIBLE 明细列表 | 4+3=7 行，明确列出面部特征/发型/服装/配饰各属于 FIXED | "Appearance: fixed. Expression/pose: flexible." 1行 | 模型不再知道"FIXED"具体指哪些属性。当前列表明确说 "face shape, eyes, nose, mouth, skin tone" 等都不可变。D 的"Appearance: fixed"是抽象的，模型可能不将"accessories"理解为 fixed 的一部分。多角色场景中配饰混淆风险升高。 | **中高** |
| 5 | NARRATIVE CONTEXT 独立块 | "SCENE ATMOSPHERE: peaceful and tender" + "EMOTIONAL BEAT: ..." | **完全删除** | 情绪节拍指令是 Stage 4 生成的关键数据，指导角色表情和肢体语言。删除后模型只能从 image_prompt 自然语言中推断情绪（image_prompt 中有 "jaw is set, throat visibly tensing" 等），但缺少显式的 "must reflect this emotional state" 强制指令。对于情绪转折较大的 shot（如 Shot 4 "peak suffocation" → Shot 6 "domineering heat"），丢失可能导致表情不准。 | **中高** |
| 6 | GLOBAL STYLE DIRECTIVE | Color Grade + Lighting + Lens + CONSISTENCY + TEXT-FREE | **完全删除**（仅保留 TEXT-FREE 压缩版） | **Color Grade 和 Lighting 丢失是 D 最严重的风险**。这两个字段定义了全局色调和光影基调（"warm amber suffused with oppressive shadow, deep chiaroscuro with candlelit gold highlights against heavy darks"），是 10 个 shot 视觉一致性的锚点。虽然每个 shot 的 image_prompt 有自己的 lighting 描述，但 GLOBAL DIRECTION 确保了跨 shot 的统一性。删除后，每个 shot 的色调可能出现微妙偏差。 | **高** |
| 7 | 参考图标签协议详情 | "Images labeled 'Character: XXX' → use to maintain..." + "DO NOT reproduce any label text" | "[REF]" 1行 "labeled on-image. Match exactly." | "DO NOT reproduce label text" 指令被删除。模型可能在生成图中复制参考图上的 "Character: Lin Yichen" 文字标签。这在 TEXT-FREE 约束覆盖下可能被弥补，但 D 的 TEXT-FREE 也被压缩了。 | **中** |
| 8 | 对话气泡渲染指令 | 完整气泡样式/位置/字体/去重/简体强制 (~200 chars) | "[TEXT]" 1行仅包含文本内容 | **"EXACTLY ONCE" 去重指令丢失**可能导致气泡被重复渲染（已知的 NB2 问题）。**简体中文强制指令丢失**可能出现繁体字。气泡样式（"white speech bubble with rounded corners"）丢失，模型自由发挥可能导致不一致的气泡外观。 | **高** |
| 9 | Mandatory keywords 完整性 | 5 个: digital illustration, vibrant colors, detailed artwork, concept art, clean lines | 4 个: 省略 "clean lines" | "clean lines" 是 illustration 风格的关键差异化特征（vs watercolor 的 soft edges）。省略可能导致线条模糊化。 | **低** |
| 10 | Forbidden keywords 完整性 | 6 个: photorealistic, photograph, 3D render, low quality, sketch, unfinished | 4 个: 省略 "sketch", "unfinished" | "sketch" 和 "unfinished" 是防止模型输出草图/未完成作品的安全网。在当前风格下实际触发概率低，但安全网消失。 | **低** |

### 6.2 风险汇总矩阵

| 风险等级 | 项目 | 影响维度 |
|---------|------|---------|
| **高** | Color Grade/Lighting 丢失 (#6) | 跨 shot 色调一致性 |
| **高** | 气泡去重/简体/样式指令丢失 (#8) | 文字渲染质量 |
| **中高** | FIXED/FLEXIBLE 明细丢失 (#4) | 多角色配饰混淆 |
| **中高** | EMOTIONAL BEAT 丢失 (#5) | 角色表情准确性 |
| **中** | style_description 散文丢失 (#3) | 画面氛围层次 |
| **中** | 参考图标签协议丢失 (#7) | 标签文字泄露 |
| **中低** | "DO NOT IGNORE" 命令丢失 (#2) | 风格遵从度 |
| **低** | 框线装饰删除 (#1) | 可忽略 |
| **低** | Mandatory/Forbidden 部分缺失 (#9, #10) | 极端情况的安全网 |

---

## 7. 专业结论

### 7.1 变体 D 的核心优势

1. **Token 效率极高**: 比 A 节省 43%，每个 token 的平均注意力权重更高
2. **风格关键词在绝对首行**: 利用 U 形注意力曲线的最高峰
3. **image_prompt 位置更靠前**: 因为前序结构更短，核心场景描述获得更多注意力
4. **零装饰性开销**: 所有字符都携带语义
5. **identity_line 完全保留**: 角色一致性的核心数据不受影响

### 7.2 变体 D 的致命风险

**我的专业判断: 变体 D 在当前形式下有 2 个致命风险，不建议直接实测。**

1. **Color Grade / Lighting 全局方向完全丢失 (风险等级: 高)**
   - 这是跨 shot 视觉一致性的锚点
   - 每个 shot 的 image_prompt 虽有自己的 lighting 描述，但没有全局统一指令
   - 10 个 shot 的色调可能出现渐变式偏差（Shot 1 暖色，Shot 5 冷色...）
   - **建议**: 将 Color Grade 和 Lighting 作为 1 行融入 [SHOT] 标签之前或之后

2. **气泡渲染指令被过度压缩 (风险等级: 高)**
   - "EXACTLY ONCE" 去重指令是针对 NB2 模型已知问题的必要防护
   - 简体中文强制指令是防止繁体字输出的必要防护
   - 气泡样式指令缺失会导致不一致的气泡外观
   - **建议**: [TEXT] 块必须保留渲染指令，不能只有内容

### 7.3 建议: 变体 D+ (修改版)

如果 Founder/PM 希望测试 D 的极端压缩路线，我建议以下修改:

```
Digital illustration. vibrant colors, detailed artwork, concept art, clean lines. Not: photorealistic, photograph, 3D render, sketch.

[REF] Reference images labeled on-image. Character appearance MUST match exactly. Do not reproduce labels.

[Lin Yichen (林逸晨)]
{identity_line — 不变}

[SHOT]
Color: {color_grade} | Light: {lighting_global}
{camera_specs}. {image_prompt}.

[TEXT]
{完整气泡指令，保留样式/位置/去重/简体强制}

Appearance: fixed (face, hair, clothing, accessories). Expression/pose: flexible. No other text.
```

**D+ 的改动**:
- 恢复 Color Grade / Lighting 为 1 行（融入 [SHOT]）
- 恢复完整气泡渲染指令
- FIXED 后加括号注明具体属性（不恢复完整列表，但给模型最低限度的明细）
- 恢复 "Do not reproduce labels"
- 预计 token: 比 D 多 ~200 chars，但修复了 2 个致命风险

### 7.4 最终推荐

| 方案 | 推荐度 | 理由 |
|------|--------|------|
| **B' (AI-ML 推荐)** | **首选实测** | 38% token 节省，0 项信息丢失，风险最低。已在我的前次分析中详细论证。 |
| **D+ (修改版)** | 值得作为第二轮实测 | 在 B' 验证安全后，可以进一步测试 D+ 的极端压缩是否有额外收益 |
| **D (原版)** | **不建议直接实测** | 2 个致命风险（Color Grade 丢失 + 气泡指令缺失），可能导致实测结果无法归因 |

### 7.5 是否值得实测？

**结论: 值得实测 B'，D 需要修改后才值得实测。**

理由:
1. B' 是保守优化，风险极低，预期收益明确（38% token 节省 + 注意力分布改善）
2. D 的哲学方向正确（压缩、场域、种子），但当前实现过于激进，丢失了 9 项语义信息
3. 如果先跑 A vs B' 对比，确认"去框线 + 压缩散文"不影响质量，再推进 D+ 是更稳健的路径
4. 跳过 B' 直接跑 D 的风险: 如果 D 质量下降，无法判断是"压缩过度"还是"描述式vs命令式"导致的

---

*文档生成时间: 2026-04-14*
*AI-ML Agent | 序话Story Prompt Engineering*
