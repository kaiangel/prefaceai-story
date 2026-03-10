"""Storyboard prompt templates for image generation"""

from typing import List, Optional


# 风格映射 - 将style_preset转换为详细的风格描述
STYLE_PROMPTS = {
    "realistic": "photorealistic, cinematic lighting, film grain, 8K UHD, detailed textures, professional photography, shallow depth of field, natural colors",
    "cyberpunk": "cyberpunk style, neon lights, futuristic city, dark atmosphere, high contrast, blade runner aesthetic, holographic displays, rain-slicked streets",
    "illustration": "digital illustration, vibrant colors, detailed artwork, artstation trending, concept art, clean lines, rich details",
    "ink": "Chinese ink wash painting, minimalist, traditional aesthetics, brush strokes, rice paper texture, ethereal, flowing lines, negative space",
    "cartoon": "cartoon style, cute characters, bright colors, simple shapes, animated movie quality, Pixar-like, smooth shading",
    "chinese": "Chinese traditional style, classical elements, red and gold palette, ornate details, silk textures, ancient Chinese aesthetics",
    "manga": "manga style, Japanese anime, dramatic expressions, dynamic poses, cel shading, bold outlines, expressive eyes",
    "oil_painting": "oil painting style, textured brushstrokes, classical art, rembrandt lighting, rich colors, impasto technique",
    "watercolor": "watercolor style, soft edges, dreamy atmosphere, pastel colors, wet on wet technique, delicate washes, fluid blending",
    "pixel": "pixel art style, 16-bit retro game aesthetic, limited color palette, crisp pixels, nostalgic gaming feel"
}

# 负面提示词 - 通用基础
BASE_NEGATIVE_PROMPTS = [
    "blurry", "low quality", "distorted", "deformed",
    "bad anatomy", "extra limbs", "missing limbs",
    "mutated hands", "extra fingers", "fewer fingers",
    "text", "watermark", "signature", "logo",
    "cropped", "out of frame", "duplicate",
    "ugly", "disfigured", "malformed"
]

# 风格特定的负面提示词
STYLE_NEGATIVE_PROMPTS = {
    "realistic": ["cartoon", "anime", "illustration", "painting", "drawn", "3d render"],
    "cartoon": ["realistic", "photorealistic", "photograph", "photo", "real person"],
    "manga": ["realistic", "3d render", "photograph", "western cartoon"],
    "illustration": ["photograph", "photo", "3d render"],
    "ink": ["colorful", "vibrant", "neon", "photograph"],
    "cyberpunk": ["bright daylight", "rural", "nature", "ancient"],
    "chinese": ["modern", "western", "futuristic"],
    "oil_painting": ["digital", "vector", "pixel", "photograph"],
    "watercolor": ["sharp edges", "digital", "photograph"],
    "pixel": ["smooth", "high resolution", "photograph", "realistic"]
}


def _build_character_description(character: dict) -> str:
    """
    从角色数据构建详细的外观描述（用于image prompt）
    优先从physical和clothing字段获取详细信息，确保角色一致性
    """
    desc_parts = []

    # 1. 物理外观 (physical)
    physical = character.get('physical', {})
    if physical:
        # 发型和发色（最重要的识别特征）
        hair_color = physical.get('hair_color', '')
        hair_style = physical.get('hair_style', '')
        if hair_color or hair_style:
            desc_parts.append(f"{hair_color} {hair_style}".strip())

        # 眼睛
        eye_color = physical.get('eye_color', '')
        if eye_color:
            desc_parts.append(f"{eye_color} eyes")

        # 肤色
        skin_tone = physical.get('skin_tone', '')
        if skin_tone:
            desc_parts.append(f"{skin_tone} skin")

    # 2. 服装（clothing）- 非常重要，用于区分角色
    clothing = character.get('clothing', {})
    if clothing:
        # 上衣
        top = clothing.get('top', '')
        if top:
            desc_parts.append(f"wearing {top}")

        # 下装
        bottom = clothing.get('bottom', '')
        if bottom:
            desc_parts.append(bottom)

        # 配饰（非常重要，用于区分角色）
        accessories = clothing.get('accessories', [])
        if accessories:
            key_accessories = accessories[:3]
            desc_parts.append(", ".join(key_accessories))

        # 风格
        style = clothing.get('style', '')
        if style:
            desc_parts.append(f"{style} style")

    # 3. 如果没有详细字段，尝试使用description
    if not desc_parts:
        desc = character.get('description', '')
        if desc:
            return desc

    return ", ".join(desc_parts) if desc_parts else ""


def build_image_prompt(
    scene: dict,
    characters: List[dict],
    style_preset: str,
    language: str = "en"
) -> str:
    """
    构建完整的图像生成prompt

    Args:
        scene: 场景数据 {"visual_description": "...", "location": "...", "time": "...", "mood": "..."}
        characters: 角色列表 [{"name": "...", "description": "..."}, ...]
        style_preset: 风格预设
        language: 语言代码

    Returns:
        完整的图像生成prompt
    """
    prompt_parts = []

    # 1. 主体描述（场景visual_description）
    visual_desc = scene.get("visual_description", "")
    if visual_desc:
        prompt_parts.append(visual_desc)

    # 2. 环境描述
    location = scene.get("location", "")
    time_of_day = scene.get("time", "")
    mood = scene.get("mood", "")

    if location or time_of_day or mood:
        setting_parts = []
        if location:
            setting_parts.append(f"Location: {location}")
        if time_of_day:
            setting_parts.append(f"Time: {time_of_day}")
        if mood:
            setting_parts.append(f"Mood: {mood} atmosphere")
        prompt_parts.append(". ".join(setting_parts))

    # 3. 角色描述（提取场景中出现的角色）- 从physical和clothing字段构建完整描述
    scene_characters = extract_characters_from_scene(scene, characters)
    if scene_characters:
        char_descriptions = []
        for char in scene_characters:
            char_name = char.get("name", "Unknown")
            # 使用_build_character_description从physical和clothing字段构建完整描述
            char_desc = _build_character_description(char)
            if char_desc:
                char_descriptions.append(f"{char_name}: {char_desc}")
        if char_descriptions:
            prompt_parts.append("Characters present: " + "; ".join(char_descriptions))

    # 4. 风格描述
    style_desc = STYLE_PROMPTS.get(style_preset, "high quality, detailed, professional")
    prompt_parts.append(f"Art style: {style_desc}")

    # 5. 质量增强
    prompt_parts.append("cinematic composition, masterpiece quality")

    return ". ".join(prompt_parts)


def build_negative_prompt(style_preset: str) -> str:
    """
    构建负面提示词

    Args:
        style_preset: 风格预设

    Returns:
        负面提示词字符串
    """
    negatives = BASE_NEGATIVE_PROMPTS.copy()
    style_specific = STYLE_NEGATIVE_PROMPTS.get(style_preset, [])
    negatives.extend(style_specific)
    return ", ".join(negatives)


def extract_characters_from_scene(scene: dict, characters: List[dict]) -> List[dict]:
    """
    从场景描述中提取出现的角色

    通过检查场景的visual_description和narration中是否提及角色名称

    Args:
        scene: 场景数据
        characters: 所有角色列表

    Returns:
        场景中出现的角色列表
    """
    # 合并场景中的文本内容
    scene_text = " ".join([
        scene.get("visual_description", ""),
        scene.get("narration", ""),
        scene.get("dialogue", "")
    ]).lower()

    # 检查每个角色是否在场景中被提及
    present_characters = []
    for char in characters:
        char_name = char.get("name", "")
        if char_name and char_name.lower() in scene_text:
            present_characters.append(char)

    # 如果没有明确提及，但场景描述中有人物相关词汇，返回主要角色
    if not present_characters and any(word in scene_text for word in ["他", "她", "人", "男", "女", "character", "person", "he", "she"]):
        # 返回前两个角色作为默认
        present_characters = characters[:2] if len(characters) >= 2 else characters

    return present_characters


def extract_characters_from_narration(narration: str, characters: List[dict]) -> List[dict]:
    """
    从旁白文本中提取出现的角色

    用于shot拆分时，根据narration_segment判断哪些角色出现在该shot中

    Args:
        narration: 旁白文本段落
        characters: 所有角色列表

    Returns:
        在旁白中被提及的角色列表
    """
    if not narration or not characters:
        return []

    narration_lower = narration.lower()
    present_characters = []

    for char in characters:
        # 检查中文名
        char_name = char.get("name", "")
        # 检查英文名
        char_name_en = char.get("name_en", "")

        # 检查是否在旁白中被提及
        if char_name and char_name.lower() in narration_lower:
            present_characters.append(char)
        elif char_name_en and char_name_en.lower() in narration_lower:
            present_characters.append(char)

    # 如果没有明确提及任何角色，但有人称代词，返回主角
    if not present_characters:
        person_pronouns = ["他", "她", "它", "我", "你", "他们", "她们", "我们"]
        if any(pronoun in narration for pronoun in person_pronouns):
            # 返回第一个主要角色
            for char in characters:
                if char.get("role") == "protagonist":
                    present_characters.append(char)
                    break
            # 如果没有标记主角，返回第一个角色
            if not present_characters and characters:
                present_characters.append(characters[0])

    return present_characters


def build_character_portrait_prompt(
    character: dict,
    style_preset: str
) -> str:
    """
    构建角色立绘的prompt

    用于生成一致性参考图

    Args:
        character: 角色数据 {"name": "...", "description": "...", "personality": "..."}
        style_preset: 风格预设

    Returns:
        角色立绘prompt
    """
    char_name = character.get("name", "Character")
    char_desc = character.get("description", "")

    style_desc = STYLE_PROMPTS.get(style_preset, "high quality, detailed")

    prompt = f"""Character portrait of {char_name}.
Physical appearance: {char_desc}
Composition: Half-body shot, facing slightly to the side, neutral solid color background.
Focus: Clear facial features, detailed clothing and accessories.
Style: {style_desc}
Quality: Professional character design, high detail, sharp focus, well-lit, masterpiece."""

    return prompt


def get_aspect_ratio_for_scene(scene: dict, default: str = "2:3") -> str:
    """
    根据场景类型推断最佳宽高比

    Args:
        scene: 场景数据
        default: 默认宽高比

    Returns:
        推荐的宽高比
    """
    visual_desc = scene.get("visual_description", "").lower()
    location = scene.get("location", "").lower()

    # 竖版场景关键词
    vertical_keywords = ["特写", "close-up", "portrait", "face", "头像", "半身"]
    for keyword in vertical_keywords:
        if keyword in visual_desc or keyword in location:
            return "2:3"  # 条漫统一比例

    # 宽屏场景关键词
    wide_keywords = ["全景", "panorama", "landscape", "远景", "城市", "街道", "sky"]
    for keyword in wide_keywords:
        if keyword in visual_desc or keyword in location:
            return "2:3"  # 条漫统一比例

    # 方形场景关键词
    square_keywords = ["对话", "dialogue", "两人", "face to face"]
    for keyword in square_keywords:
        if keyword in visual_desc:
            return "2:3"  # 条漫统一比例

    return default


def translate_prompt_to_english(prompt: str, source_lang: str = "zh") -> str:
    """
    将中文prompt转换为英文（简单处理）

    注意：这是一个简化版本，实际应用中可能需要调用翻译API

    Args:
        prompt: 原始prompt
        source_lang: 源语言

    Returns:
        英文prompt
    """
    # 对于图像生成，通常英文prompt效果更好
    # 这里可以集成翻译API或使用LLM翻译
    # 简化版本直接返回原文
    return prompt


# 中文摄影术语翻译映射
SHOT_TYPE_TRANSLATIONS = {
    "全景": "wide shot",
    "远景": "extreme wide shot",
    "中景": "medium shot",
    "近景": "medium close-up",
    "特写": "close-up",
    "大特写": "extreme close-up",
    "过肩镜头": "over-the-shoulder shot",
    "主观镜头": "POV shot",
}

CAMERA_ANGLE_TRANSLATIONS = {
    "平视": "eye level",
    "仰拍": "low angle",
    "俯拍": "high angle",
    "鸟瞰": "bird's eye view",
    "侧面": "side view",
    "正面": "front view",
    "斜侧": "three-quarter view",
}

MOOD_TRANSLATIONS = {
    "期待": "anticipation",
    "好奇": "curiosity",
    "温暖": "warmth",
    "紧张": "tension",
    "神秘": "mysterious",
    "欢乐": "joyful",
    "悲伤": "sadness",
    "惊讶": "surprise",
    "平静": "calm",
    "浪漫": "romantic",
    "孤独": "lonely",
    "温馨": "cozy",
    "忧郁": "melancholy",
    "兴奋": "excitement",
    "恐惧": "fear",
}


async def translate_image_prompt_to_english(
    prompt: str,
    client=None,
    preserve_text_in_image: bool = True
) -> str:
    """
    使用LLM将图像生成prompt翻译为纯英文

    保留需要在图片中渲染的原文文字（用引号包裹标注）

    Args:
        prompt: 原始的中英混合prompt
        client: Gemini客户端（可选，如不传则使用同步翻译）
        preserve_text_in_image: 是否保留需要渲染的文字原文

    Returns:
        翻译后的英文prompt
    """
    if not prompt:
        return prompt

    # 检测是否需要翻译（是否包含中文）
    import re
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
    if not chinese_pattern.search(prompt):
        # 没有中文，直接返回
        return prompt

    # 如果没有LLM客户端，使用简单的字典翻译
    if not client:
        return _simple_translate_prompt(prompt)

    # 使用LLM翻译
    translation_prompt = f"""Translate the following image generation prompt to English.

IMPORTANT RULES:
1. Translate all descriptive text to natural English
2. For text that should appear IN the generated image (like signs, speech bubbles, book text), keep the original text and wrap it in quotes with a label
   - Example: 招牌上写着"便利店" → The sign reads: "便利店"
   - Example: 对话气泡显示"你好" → Speech bubble shows: "你好"
3. Translate photography terms accurately:
   - 全景 → wide shot
   - 中景 → medium shot
   - 特写 → close-up
   - 平视 → eye level
   - 仰拍 → low angle
   - 俯拍 → high angle
4. Keep character names in their romanized form (e.g., Xiao Yu, Ming Ming)
5. Maintain the original prompt structure and intent

Original prompt:
{prompt}

Translated prompt (English only, except quoted text for image rendering):"""

    try:
        from google.genai import types

        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=translation_prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,  # 低温度确保准确翻译
            )
        )

        # 检查response.text是否为None
        if response.text is None:
            print("LLM返回空响应，使用简单翻译")
            return _simple_translate_prompt(prompt)

        translated = response.text.strip()

        # 清理可能的markdown标记
        if translated.startswith("```"):
            lines = translated.split("\n")
            translated = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        return translated

    except Exception as e:
        print(f"LLM翻译失败，使用简单翻译: {e}")
        return _simple_translate_prompt(prompt)


def _simple_translate_prompt(prompt: str) -> str:
    """
    简单的字典翻译（无LLM时的回退方案）

    仅翻译已知的摄影术语，其他中文保留
    """
    result = prompt

    # 翻译镜头类型
    for zh, en in SHOT_TYPE_TRANSLATIONS.items():
        result = result.replace(f"Shot type: {zh}", f"Shot type: {en}")
        result = result.replace(f"shot_type: {zh}", f"shot_type: {en}")
        result = result.replace(zh, en)

    # 翻译镜头角度
    for zh, en in CAMERA_ANGLE_TRANSLATIONS.items():
        result = result.replace(f"Camera angle: {zh}", f"Camera angle: {en}")
        result = result.replace(f"camera_angle: {zh}", f"camera_angle: {en}")
        result = result.replace(zh, en)

    # 翻译情绪词
    for zh, en in MOOD_TRANSLATIONS.items():
        result = result.replace(f"Mood: {zh}", f"Mood: {en}")
        result = result.replace(zh, en)

    return result


# ============================================================================
# Stage 4 Prompt增强：忠实剧情的视觉转化规则
# ============================================================================

NARRATION_TO_VISUAL_EXTRACTION_RULES = """
═══════════════════════════════════════════════════════════
CRITICAL: FAITHFUL VISUAL TRANSLATION FROM NARRATION
═══════════════════════════════════════════════════════════

When generating image_prompt from narration, you MUST extract and translate these elements:

## 1. BODY LANGUAGE (姿态)
Extract posture cues from narration and translate to specific visual descriptions:

| Narration Cue (Chinese) | Visual Translation |
|------------------------|-------------------|
| 低着头 / 垂着头 | head bowed down, gaze directed at ground |
| 耸肩 | shoulders shrugged, hunched posture |
| 抱着手臂 / 抱臂 | arms crossed over chest defensively |
| 双手插兜 | hands in pockets, casual stance |
| 靠在墙上 / 倚着 | leaning against wall, weight shifted |
| 蜷缩 / 缩成一团 | curled up, knees drawn to chest |
| 挺直腰板 | standing straight, shoulders back, chin up |
| 踱步 / 来回走 | mid-stride, captured in motion |
| 摊开双手 | palms up, hands spread open in gesture |
| 攥拳 / 握拳 | clenched fists, knuckles white |

## 2. FACIAL EXPRESSION (面部表情)
Translate emotional states to specific micro-expressions:

| Emotion | Visual Translation |
|---------|-------------------|
| 愤怒 / 生气 | furrowed brows, clenched jaw, flared nostrils |
| 悲伤 / 难过 | downturned lips, glistening eyes, soft focus |
| 惊讶 / 震惊 | wide eyes, raised eyebrows, parted lips |
| 恐惧 / 害怕 | wide eyes, pale skin, tense muscles |
| 喜悦 / 开心 | crinkled eyes, genuine smile reaching eyes |
| 困惑 / 疑惑 | tilted head, furrowed brow, questioning gaze |
| 厌恶 / 反感 | wrinkled nose, curled upper lip |
| 疲惫 / 疲倦 | drooping eyelids, dark circles, slack posture |
| 紧张 / 焦虑 | bitten lip, darting eyes, fidgeting hands |
| 释然 / 放松 | softened features, relaxed shoulders, gentle smile |
| 期待 / 期盼 | bright eyes, leaning forward slightly |
| 失望 | downcast eyes, slumped shoulders, heavy sigh |

## 3. EMOTIONAL STATE CONTEXT (情绪状态)
Include environmental reflection of emotional state:

| Emotional State | Environmental Cues |
|-----------------|-------------------|
| 孤独 / 寂寞 | isolated framing, empty space around character |
| 压抑 / 沉重 | low-key lighting, shadows dominating frame |
| 温暖 / 安慰 | warm color temperature, soft lighting |
| 紧张对峙 | tight framing, characters at opposite edges |
| 亲密时刻 | close proximity, soft focus background |
| 绝望 / 崩溃 | harsh shadows, dutch angle, fragmented composition |

## 4. SCENE MOMENT TYPE (场景时刻)
Identify the narrative beat and adjust visual approach:

| Moment Type | Visual Approach |
|-------------|----------------|
| 静默时刻 | still composition, negative space, contemplative |
| 爆发时刻 | dynamic angle, motion blur effect, intense |
| 转折时刻 | dramatic lighting shift, focus pull |
| 亲密时刻 | shallow depth of field, intimate framing |
| 对抗时刻 | opposing screen positions, tension in composition |
| 启示时刻 | light breakthrough, upward angle |

## 5. MULTI-CHARACTER DYNAMICS (多角色动态)
When multiple characters are present, specify spatial relationships:

| Relationship | Visual Translation |
|--------------|-------------------|
| 对立 / 冲突 | facing each other from opposite frame edges |
| 亲密 / 依靠 | physical contact or close proximity |
| 疏远 / 隔阂 | large gap between characters, physical barriers |
| 保护 / 遮挡 | one character shielding another |
| 关注 / 注视 | eye lines converging on subject |
| 各自沉默 | characters looking in different directions |

## 6. GAZE DIRECTION ANCHORING（视线方向锚定）

When narration contains verbs like "发现", "看到", "注视", "望向", "盯着",
the image_prompt MUST explicitly describe WHERE the character is looking.

| Narration Cue (Chinese) | Visual Translation |
|-------------------------|-------------------|
| "发现某人" | "eyes lock onto [person], gaze fixed on the figure of..." |
| "看着某人" | "staring directly at [person], eyes following their movement" |
| "望向远方" | "gazing into the distance, eyes focused on the far horizon" |
| "低头看" | "looking down at [object], eyes fixed on..." |
| "注视" | "eyes riveted on [target], unblinking gaze" |
| "盯着" | "staring intently at [target], eyes narrowed in focus" |
| "回头看" | "turning to look back at [target], eyes searching for..." |
| "瞥见" | "catching a glimpse of [target], eyes darting to..." |
| "打量" | "eyes scanning over [target], examining from head to toe" |

❌ WRONG:
Narration: "意外发现梁奶奶正蜷缩在长椅一角"
image_prompt: "his head snapping up in surprise"
(Missing: WHERE is he looking?)

✅ RIGHT:
Narration: "意外发现梁奶奶正蜷缩在长椅一角"
image_prompt: "his head snaps up mid-step, eyes widening as his gaze locks onto
the unexpected huddled figure of Grandma Liang on the bench. His eyes are fixed
on her—a mixture of surprise and wariness in his expression."

RULE: If a character "discovers" or "sees" another character/object in the narration,
the image_prompt MUST contain explicit gaze direction using phrases like:
- "eyes lock onto..."
- "gaze fixed on..."
- "staring directly at..."
- "eyes riveted on..."
- "looking straight at..."

═══════════════════════════════════════════════════════════
EXTRACTION PRIORITY ORDER:
1. Character posture/action (MOST IMPORTANT - defines the shot)
2. Facial expression (CRITICAL for emotion)
3. Gaze direction (CRITICAL when "discover/see" verbs present)
4. Spatial relationship (for multi-character shots)
5. Environmental mood cues
═══════════════════════════════════════════════════════════
"""

# ============================================================================
# Stage 4 Prompt增强：条漫模式叙事自足规则
# ============================================================================

COMIC_MODE_NARRATIVE_RULES = """
═══════════════════════════════════════════════════════════
COMIC/MANGA MODE: NARRATIVE SELF-SUFFICIENCY (CRITICAL)
═══════════════════════════════════════════════════════════

In comic/manga mode, readers have NO narration voiceover — they can ONLY read
dialogue bubbles and thought bubbles visible in each panel. Therefore:

## RULE 1: SELF-CONTAINED CONTEXT
Every shot's dialogue and thought MUST contain enough information for readers
to understand the story WITHOUT any external narration.

BAD:  thought="（怎么会这样……）" (readers don't know what happened)
GOOD: thought="（他居然把房子卖了……）" (readers understand the situation)

## RULE 2: TRANSITION SHOTS
When a scene/location/time changes between shots, the FIRST shot in the new
context MUST include a thought or dialogue that establishes:
- WHERE we are now (if location changed)
- WHEN this is happening (if time jumped)
- WHY we are here (narrative connection to previous scene)

Example: After a fight scene → cut to character alone at night →
thought="（刚才那些话……我是不是太过分了）" (bridges the two scenes)

## RULE 3: DO NOT RELY ON NARRATION
Do NOT assume narration_segment will be shown to readers.
If critical plot information exists only in narration_segment,
move it into a thought bubble or dialogue line.

═══════════════════════════════════════════════════════════
"""

# 情绪到面部表情映射字典（用于程序化提取）
EMOTION_TO_EXPRESSION_MAP = {
    # 愤怒类
    "愤怒": "furrowed brows, clenched jaw, flared nostrils, intense glare",
    "生气": "tight lips, narrowed eyes, tense facial muscles",
    "恼怒": "pursed lips, sharp exhale, impatient expression",
    "暴怒": "bulging veins, bared teeth, wild eyes",

    # 悲伤类
    "悲伤": "downturned lips, glistening eyes, trembling chin",
    "难过": "soft frown, watery eyes, dejected gaze",
    "哀伤": "tear-streaked face, red-rimmed eyes, quivering lips",
    "心碎": "face crumpling, tears flowing, mouth open in silent cry",
    "失望": "downcast eyes, slumped features, heavy expression",

    # 惊讶类
    "惊讶": "wide eyes, raised eyebrows, parted lips, leaning back slightly",
    "震惊": "frozen expression, mouth agape, eyes locked wide",
    "愕然": "stunned expression, momentary freeze, disbelief in eyes",

    # 恐惧类
    "恐惧": "wide terrified eyes, pale complexion, tense muscles",
    "害怕": "shrinking posture, darting eyes, protective stance",
    "惊恐": "terror-stricken face, trembling, backing away",

    # 喜悦类
    "喜悦": "bright sparkling eyes, genuine smile reaching eyes, relaxed features",
    "开心": "wide smile, crinkled eyes, animated expression",
    "欣慰": "gentle smile, softened eyes, released tension",
    "兴奋": "bright eyes, animated expression, forward leaning",
    "得意": "smug smile, chin slightly raised, confident posture",

    # 困惑类
    "困惑": "tilted head, furrowed brow, questioning gaze",
    "疑惑": "narrowed eyes, slight head tilt, studying expression",
    "茫然": "blank stare, unfocused eyes, slack expression",

    # 厌恶类
    "厌恶": "wrinkled nose, curled upper lip, turned away head",
    "反感": "lips pressed thin, dismissive glance, distancing posture",
    "鄙视": "raised chin, narrowed eyes, contemptuous sneer",

    # 疲惫类
    "疲惫": "drooping eyelids, dark circles, slack posture, heavy breathing",
    "疲倦": "heavy-lidded eyes, suppressed yawn, sluggish movements",
    "精疲力竭": "sunken features, glazed eyes, barely upright",

    # 紧张类
    "紧张": "bitten lip, darting eyes, fidgeting hands, stiff posture",
    "焦虑": "furrowed brow, restless movement, worried glances",
    "不安": "shifting weight, avoiding eye contact, nervous gestures",

    # 平静/释然类
    "释然": "softened features, relaxed shoulders, gentle peaceful smile",
    "放松": "open posture, serene expression, even breathing",
    "平静": "neutral composed features, steady gaze, calm demeanor",
    "淡然": "impassive expression, distant gaze, detached composure",

    # 期待类
    "期待": "bright anticipating eyes, leaning forward slightly, eager expression",
    "期盼": "hopeful eyes, slightly parted lips, attentive posture",
    "渴望": "intense longing gaze, reaching gesture, yearning expression",

    # 其他
    "尴尬": "forced smile, avoiding eye contact, flushed cheeks",
    "羞涩": "lowered gaze, blushing cheeks, shy smile",
    "沉思": "distant gaze, hand on chin, contemplative expression",
    "坚定": "set jaw, determined eyes, resolute expression",
    "绝望": "hollow eyes, ashen face, defeated slump",
}

# 姿态关键词映射字典（用于程序化提取）
POSTURE_KEYWORD_MAP = {
    # 头部
    "低着头": "head bowed down, gaze directed at ground",
    "垂着头": "head hanging low, chin nearly touching chest",
    "抬头": "head raised, looking upward",
    "歪着头": "head tilted to one side, curious posture",
    "摇头": "head shaking side to side",
    "点头": "head nodding",

    # 肩部
    "耸肩": "shoulders shrugged, hunched posture",
    "垂肩": "shoulders drooping, defeated posture",
    "挺肩": "shoulders squared, confident stance",

    # 手臂
    "抱着手臂": "arms crossed over chest defensively",
    "抱臂": "arms folded across chest",
    "双手插兜": "hands in pockets, casual stance",
    "背着手": "hands clasped behind back",
    "摊开双手": "palms up, hands spread open in gesture",
    "挥手": "hand raised in wave gesture",
    "握拳": "clenched fists, knuckles white",
    "攥拳": "tight fists, tension visible",
    "捂脸": "hands covering face",
    "托腮": "chin resting on hand, contemplative",
    "揉眼睛": "rubbing eyes with hands",
    "抓头": "hand scratching head, confused gesture",

    # 身体姿态
    "靠在墙上": "leaning against wall, weight shifted",
    "倚着": "leaning on support, relaxed posture",
    "蜷缩": "curled up, knees drawn to chest",
    "缩成一团": "huddled into ball, protective posture",
    "挺直腰板": "standing straight, shoulders back, chin up",
    "弯着腰": "bent at waist, hunched over",
    "跪着": "kneeling on ground",
    "蹲着": "squatting down",
    "躺着": "lying down, horizontal position",
    "坐着": "seated, settled posture",
    "站着": "standing upright",

    # 动态姿态
    "踱步": "mid-stride, captured in walking motion",
    "来回走": "pacing, feet in motion",
    "跑": "running, dynamic movement blur",
    "奔跑": "sprinting, urgent forward motion",
    "转身": "turning around, body in rotation",
    "后退": "stepping backward, retreating motion",

    # 互动姿态
    "拥抱": "embracing, arms wrapped around",
    "牵手": "hands clasped together, fingers intertwined",
    "搭肩": "arm over shoulder, friendly gesture",
    "推开": "pushing away with hands, rejection gesture",
    "拉住": "gripping, holding onto",
}

# 场景时刻类型关键词（用于识别叙事节拍）
MOMENT_TYPE_KEYWORDS = {
    "静默时刻": ["沉默", "安静", "无言", "静静", "默默"],
    "爆发时刻": ["爆发", "大喊", "怒吼", "冲", "摔"],
    "转折时刻": ["突然", "忽然", "没想到", "意外", "原来"],
    "亲密时刻": ["拥抱", "牵手", "依偎", "贴近", "温柔"],
    "对抗时刻": ["对峙", "争吵", "质问", "反驳", "冲突"],
    "启示时刻": ["明白", "醒悟", "意识到", "终于", "恍然"],
}


# ============================================================================
# 视觉提取辅助方法
# ============================================================================

def extract_posture_cues(narration: str) -> List[str]:
    """
    从旁白文本中提取姿态线索

    Args:
        narration: 中文旁白文本

    Returns:
        提取到的英文姿态描述列表
    """
    if not narration:
        return []

    found_cues = []
    for zh_keyword, en_desc in POSTURE_KEYWORD_MAP.items():
        if zh_keyword in narration:
            found_cues.append(en_desc)

    return found_cues


def extract_emotion_cues(narration: str) -> List[str]:
    """
    从旁白文本中提取情绪线索

    Args:
        narration: 中文旁白文本

    Returns:
        提取到的英文表情描述列表
    """
    if not narration:
        return []

    found_cues = []
    for zh_emotion, en_expression in EMOTION_TO_EXPRESSION_MAP.items():
        if zh_emotion in narration:
            found_cues.append(en_expression)

    return found_cues


def identify_moment_type(narration: str) -> Optional[str]:
    """
    识别旁白文本所属的场景时刻类型

    Args:
        narration: 中文旁白文本

    Returns:
        识别到的时刻类型（中文），如 "静默时刻"、"爆发时刻" 等
        如果无法识别则返回 None
    """
    if not narration:
        return None

    for moment_type, keywords in MOMENT_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in narration:
                return moment_type

    return None


def get_moment_visual_approach(moment_type: str) -> str:
    """
    根据时刻类型获取推荐的视觉处理方式

    Args:
        moment_type: 时刻类型（中文）

    Returns:
        英文视觉处理建议
    """
    moment_visual_map = {
        "静默时刻": "still composition, negative space, contemplative atmosphere",
        "爆发时刻": "dynamic angle, motion blur effect, intense dramatic lighting",
        "转折时刻": "dramatic lighting shift, focus pull effect, suspenseful",
        "亲密时刻": "shallow depth of field, intimate close framing, warm soft lighting",
        "对抗时刻": "opposing screen positions, tension in composition, sharp contrast",
        "启示时刻": "light breakthrough effect, upward angle, hopeful atmosphere",
    }
    return moment_visual_map.get(moment_type, "")


def extract_visual_cues_from_narration(narration: str) -> dict:
    """
    从旁白中提取所有视觉线索的综合方法

    Args:
        narration: 中文旁白文本

    Returns:
        包含所有提取结果的字典：
        {
            "posture_cues": [...],    # 姿态线索
            "emotion_cues": [...],    # 情绪线索
            "moment_type": "...",     # 时刻类型
            "visual_approach": "..."  # 推荐的视觉处理方式
        }
    """
    result = {
        "posture_cues": extract_posture_cues(narration),
        "emotion_cues": extract_emotion_cues(narration),
        "moment_type": None,
        "visual_approach": ""
    }

    moment_type = identify_moment_type(narration)
    if moment_type:
        result["moment_type"] = moment_type
        result["visual_approach"] = get_moment_visual_approach(moment_type)

    return result


def build_enhanced_visual_description(
    base_description: str,
    narration: str,
    character_name: Optional[str] = None
) -> str:
    """
    基于旁白增强视觉描述

    将从旁白提取的姿态、表情、时刻类型等信息整合到基础描述中

    Args:
        base_description: 基础的视觉描述（英文）
        narration: 中文旁白文本
        character_name: 角色名称（用于标识谁的动作/表情）

    Returns:
        增强后的视觉描述
    """
    if not narration:
        return base_description

    visual_cues = extract_visual_cues_from_narration(narration)

    enhancements = []

    # 添加姿态描述
    if visual_cues["posture_cues"]:
        posture_str = ", ".join(visual_cues["posture_cues"][:2])  # 最多取2个
        if character_name:
            enhancements.append(f"{character_name}: {posture_str}")
        else:
            enhancements.append(f"Character posture: {posture_str}")

    # 添加表情描述
    if visual_cues["emotion_cues"]:
        emotion_str = visual_cues["emotion_cues"][0]  # 取第一个最匹配的
        if character_name:
            enhancements.append(f"{character_name}'s expression: {emotion_str}")
        else:
            enhancements.append(f"Expression: {emotion_str}")

    # 添加视觉处理建议
    if visual_cues["visual_approach"]:
        enhancements.append(visual_cues["visual_approach"])

    if enhancements:
        return f"{base_description}. {'. '.join(enhancements)}"

    return base_description


def prepare_shot_prompt_for_generation(
    shot: dict,
    client=None
) -> str:
    """
    准备shot的prompt用于图像生成

    优先使用shot的image_prompt字段，并翻译为英文

    Args:
        shot: shot数据字典，包含image_prompt等字段
        client: Gemini客户端（用于LLM翻译）

    Returns:
        准备好的英文prompt
    """
    # 优先使用shot自带的image_prompt
    image_prompt = shot.get('image_prompt', '')

    if not image_prompt:
        # 没有image_prompt，尝试从其他字段构建
        visual_desc = shot.get('visual_description', '')
        shot_type = shot.get('shot_type', 'medium shot')

        if visual_desc:
            image_prompt = f"{visual_desc}. Shot type: {shot_type}."

    # 同步翻译（简单版本）
    return _simple_translate_prompt(image_prompt)


async def prepare_shot_prompt_for_generation_async(
    shot: dict,
    client=None,
    style_enforcer=None
) -> str:
    """
    异步准备shot的prompt用于图像生成

    优先使用shot的image_prompt字段，并通过LLM翻译为英文

    Args:
        shot: shot数据字典，包含image_prompt等字段
        client: Gemini客户端（用于LLM翻译）
        style_enforcer: StyleEnforcer实例（用于添加风格前缀）

    Returns:
        准备好的英文prompt
    """
    # 优先使用shot自带的image_prompt
    image_prompt = shot.get('image_prompt', '')

    if not image_prompt:
        # 没有image_prompt，尝试从其他字段构建
        visual_desc = shot.get('visual_description', '')
        shot_type = shot.get('shot_type', 'medium shot')

        if visual_desc:
            image_prompt = f"{visual_desc}. Shot type: {shot_type}."

    # 使用LLM翻译
    translated_prompt = await translate_image_prompt_to_english(
        image_prompt,
        client=client
    )

    # 应用风格强制器（如果有）
    if style_enforcer:
        translated_prompt = style_enforcer.enforce_prompt(translated_prompt)

    return translated_prompt


# ============================================================================
# Phase 2.0 专业镜头语言支持
# ============================================================================

# 景别词汇映射（专业摄影术语）
SHOT_SIZE_VOCABULARY = {
    "extreme_wide_shot": "Extreme wide shot showing vast environment with tiny human figure",
    "wide_shot": "Wide shot establishing the full scene with subject in environment",
    "medium_wide_shot": "Medium wide shot (cowboy shot) framing subject from knees up",
    "medium_shot": "Medium shot framing subject from waist up",
    "medium_close_up": "Medium close-up framing subject from chest up",
    "close_up": "Close-up shot focusing on subject's face",
    "extreme_close_up": "Extreme close-up on eyes or specific detail"
}

# 机位角度词汇映射
CAMERA_ANGLE_VOCABULARY = {
    "birds_eye": "Bird's eye view looking straight down",
    "high_angle": "High angle shot looking down on subject",
    "eye_level": "Eye level shot at subject's height",
    "low_angle": "Low angle shot looking up at subject",
    "worms_eye": "Worm's eye view from ground level looking up",
    "dutch_angle": "Dutch angle (tilted) creating unease"
}

# 镜头运动词汇映射
CAMERA_MOVEMENT_VOCABULARY = {
    "static": "static camera",
    "pan_left": "camera panning left",
    "pan_right": "camera panning right",
    "tilt_up": "camera tilting up",
    "tilt_down": "camera tilting down",
    "dolly_in": "camera dollying in toward subject",
    "dolly_out": "camera dollying out from subject",
    "tracking": "camera tracking alongside subject"
}

# 光影情绪词汇映射
LIGHTING_MOOD_VOCABULARY = {
    "high_key": "bright, even high-key lighting",
    "low_key": "dramatic low-key lighting with deep shadows",
    "chiaroscuro": "strong chiaroscuro contrast",
    "silhouette": "backlit silhouette",
    "golden_hour": "warm golden hour sunlight",
    "blue_hour": "cool blue hour ambient light",
    "neon_glow": "colorful neon light reflections",
    "candlelight": "warm flickering candlelight",
    "moonlight": "soft silvery moonlight",
    "isolated_dramatic": "isolated subject with dramatic lighting",
    "warm_intimate": "warm intimate lighting"
}


def build_phase2_image_prompt(shot: dict, style_preset: str = "realistic") -> str:
    """
    Phase 2.0: 从shot数据构建专业的image_prompt

    Args:
        shot: storyboard中的单个shot数据
        style_preset: 风格预设

    Returns:
        完整的英文image_prompt
    """
    parts = []

    # 1. 景别和机位
    camera = shot.get("camera", {})
    shot_size = camera.get("shot_size", "medium_shot")
    angle = camera.get("angle", "eye_level")
    lens = camera.get("lens", "35mm")

    shot_size_desc = SHOT_SIZE_VOCABULARY.get(shot_size, shot_size.replace("_", " "))
    angle_desc = CAMERA_ANGLE_VOCABULARY.get(angle, angle.replace("_", " "))

    parts.append(f"{shot_size_desc}, {angle_desc}, {lens} lens")

    # 2. 构图
    composition = shot.get("composition", {})
    subject_pos = composition.get("subject_position", "")
    if subject_pos:
        parts.append(f"subject positioned in {subject_pos.replace('_', ' ')}")

    leading_lines = composition.get("leading_lines", "")
    if leading_lines:
        parts.append(f"leading lines from {leading_lines.replace('_', ' ')}")

    foreground = composition.get("foreground_element", "")
    if foreground:
        parts.append(f"{foreground.replace('_', ' ')} in foreground")

    negative_space = composition.get("negative_space", "")
    if negative_space:
        parts.append(negative_space.replace("_", " "))

    # 3. 角色
    char_direction = shot.get("character_direction", {})
    characters_visible = char_direction.get("characters_visible", [])

    for char_id in characters_visible:
        char_info = char_direction.get(char_id, {})
        if char_info:
            char_parts = []

            position = char_info.get("position_in_frame", "")
            if position:
                char_parts.append(position.replace("_", " "))

            posture = char_info.get("body_posture", "")
            if posture:
                char_parts.append(posture.replace("_", " "))

            expression = char_info.get("facial_expression", "")
            if expression:
                char_parts.append(f"expression showing {expression.replace('_', ' ')}")

            gesture = char_info.get("gesture", "")
            if gesture:
                char_parts.append(gesture.replace("_", " "))

            if char_parts:
                parts.append(f"Character: {', '.join(char_parts)}")

    # 4. 光影
    lighting = shot.get("lighting", {})
    key_light = lighting.get("key_light", "")
    if key_light:
        parts.append(f"Key light: {key_light.replace('_', ' ')}")

    practical_lights = lighting.get("practical_lights", [])
    if practical_lights:
        parts.append(f"Practical lights: {', '.join(practical_lights)}")

    mood = lighting.get("mood", "")
    if mood:
        mood_desc = LIGHTING_MOOD_VOCABULARY.get(mood, mood.replace("_", " "))
        parts.append(mood_desc)

    # 5. 环境
    environment = shot.get("environment", {})
    weather = environment.get("weather_visibility", "")
    if weather:
        parts.append(weather.replace("_", " "))

    atmosphere = environment.get("atmosphere_particles", "")
    if atmosphere:
        parts.append(atmosphere.replace("_", " "))

    # 6. 风格后缀
    style_suffix = STYLE_PROMPTS.get(style_preset, STYLE_PROMPTS["realistic"])
    parts.append(style_suffix)

    return ". ".join(parts)


def build_critical_header_phase2() -> str:
    """
    Phase 2.0: 构建角色一致性关键指令头

    明确区分FIXED vs FLEXIBLE属性，让Gemini知道哪些必须匹配参考图
    """
    return """═══════════════════════════════════════════════════════════
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

═══════════════════════════════════════════════════════════"""


def build_identity_line_phase2(character: dict) -> str:
    """
    Phase 2.0: 构建增强的角色身份行（完整外观描述）

    输出示例：
    "young Asian man, oval face, fair skin, dark brown almond eyes,
     short black hair with side part, rectangular silver-framed glasses,
     gray casual button-up shirt, black slim jeans"
    """
    parts = []

    # 1. 年龄 + 种族 + 性别
    gender = character.get('gender', '')
    age = character.get('age_appearance', '')
    physical = character.get('physical', {})

    # 年龄映射
    age_map = {
        'child': 'young',
        'teenager': 'teenage',
        'young_adult': 'young',
        'adult': '',
        'middle_aged': 'middle-aged',
        'elderly': 'elderly'
    }
    age_term = age_map.get(age, '')

    # 获取种族 - 从skin_tone推断（中文故事默认亚洲人）
    skin_tone = physical.get('skin_tone', '')
    ethnicity = 'East Asian' if skin_tone in ['fair', 'light', 'pale', 'medium'] else ''

    # 构建基础标识
    if gender == 'female':
        base = f"{age_term} {ethnicity} woman".strip()
    elif gender == 'male':
        base = f"{age_term} {ethnicity} man".strip()
    else:
        base = f"{age_term} {ethnicity} person".strip()

    base = ' '.join(base.split())
    parts.append(base)

    # 2. 面部特征（关键！）
    face_shape = physical.get('face_shape', '')
    if face_shape:
        parts.append(f"{face_shape} face")

    if skin_tone:
        parts.append(f"{skin_tone} skin")

    eye_shape = physical.get('eye_shape', '')
    eye_color = physical.get('eye_color', '')
    if eye_shape and eye_color:
        parts.append(f"{eye_color} {eye_shape} eyes")
    elif eye_color:
        parts.append(f"{eye_color} eyes")

    # 3. 完整发型描述
    hair_color = physical.get('hair_color', '')
    hair_style = physical.get('hair_style', '')

    hair_desc = []
    if hair_color:
        hair_desc.append(hair_color)
    hair_desc.append('hair')
    if hair_style:
        hair_desc.append(f"with {hair_style}")

    if hair_color or hair_style:
        parts.append(' '.join(hair_desc))

    # 4. 服装
    clothing = character.get('clothing', {})

    # 眼镜等配饰（放在服装前）
    accessories = clothing.get('accessories', [])
    glasses = [a for a in accessories if 'glass' in a.lower() or 'spectacle' in a.lower()]
    if glasses:
        parts.append(glasses[0])

    # 上衣
    top = clothing.get('top', '')
    if top:
        parts.append(top)

    # 下装
    bottom = clothing.get('bottom', '')
    if bottom:
        parts.append(bottom)

    # 其他配饰
    other_accessories = [a for a in accessories if 'glass' not in a.lower()]
    if other_accessories:
        parts.extend(other_accessories[:2])

    return ', '.join(parts)


def build_narrative_context_phase2(
    shot: dict,
    previous_shot: Optional[dict] = None,
    screenplay: Optional[dict] = None
) -> str:
    """
    Phase 2.0: 构建剧情上下文，增强情绪/剧情连续性

    Args:
        shot: 当前shot数据
        previous_shot: 上一个shot数据（用于情绪状态传递）
        screenplay: 剧本数据（用于获取场景信息）

    Returns:
        剧情上下文字符串
    """
    context_parts = []

    # 1. 当前剧情阶段
    plot_point = shot.get("plot_point", "")
    if plot_point:
        stage_descriptions = {
            "inciting_incident": "OPENING - Characters enter the situation, establishing isolation and initial discomfort",
            "first_turn": "RISING TENSION - Awkward silence, each character retreating into their own world",
            "midpoint": "TURNING POINT - First moment of connection, barriers begin to crack",
            "crisis": "EMOTIONAL PEAK - Vulnerability exposed, defenses crumble",
            "climax": "CLIMAX - Genuine human connection achieved, strangers become companions",
            "resolution": "CLOSURE - Departure with warmth, hope lingers in the aftermath"
        }
        context_parts.append(f"NARRATIVE STAGE: {stage_descriptions.get(plot_point, plot_point)}")

    # 2. 从上一个shot传递角色情绪状态
    if previous_shot:
        prev_lighting = previous_shot.get("lighting", {})
        prev_mood = prev_lighting.get("mood", "")
        prev_char_direction = previous_shot.get("character_direction", {})
        prev_chars = prev_char_direction.get("characters_visible", [])

        if prev_chars and prev_mood:
            context_parts.append(f"\nPREVIOUS SHOT CONTEXT:")
            context_parts.append(f"  Characters present: {', '.join(prev_chars)}")
            context_parts.append(f"  Emotional state: {prev_mood}")
            context_parts.append(f"  → Carry forward any visible emotional residue (red eyes from crying, tense shoulders, etc.)")

    # 3. 场景氛围传递（从screenplay获取）
    if screenplay:
        scene_id = shot.get("scene_id")
        for scene in screenplay.get("scenes", []):
            if scene.get("scene_id") == scene_id:
                atmosphere = scene.get("atmosphere", {})
                if atmosphere:
                    mood = atmosphere.get("mood", "")
                    if mood:
                        context_parts.append(f"\nSCENE ATMOSPHERE: {mood}")
                break

    # 4. 关键情感提示（从lighting.mood获取）
    lighting = shot.get("lighting", {})
    emotional_mood = lighting.get("mood", "")
    if emotional_mood:
        context_parts.append(f"\nEMOTIONAL BEAT FOR THIS SHOT: {emotional_mood}")
        context_parts.append("→ Character expressions and body language must reflect this emotional state")

    if context_parts:
        return """═══════════════════════════════════════════════════════════
NARRATIVE CONTEXT
═══════════════════════════════════════════════════════════
""" + "\n".join(context_parts) + """
═══════════════════════════════════════════════════════════"""

    return ""


def build_system_instruction_phase2(global_visual_direction: dict) -> str:
    """
    Phase 2.0: 构建全局风格锚定的system_instruction

    Args:
        global_visual_direction: storyboard中的全局视觉指导

    Returns:
        system_instruction字符串
    """
    style = global_visual_direction.get("style_enforcement", "realistic_cinematic")
    aspect_ratio = global_visual_direction.get("aspect_ratio", "2:3")
    color_grade = global_visual_direction.get("color_grade", "neutral")
    lighting = global_visual_direction.get("overall_lighting", "natural")
    lens_style = global_visual_direction.get("lens_style", "35mm")

    # TASK-PROMPT-BUBBLE: trimmed redundant lines
    # - Removed "Style Enforcement" (redundant with StyleEnforcer mandatory prefix)
    # - Removed "Aspect Ratio" (set via API parameter, not prompt)
    # - Condensed CRITICAL REQUIREMENTS into single concise line
    return f"""GLOBAL VISUAL DIRECTION:
Color Grade: {color_grade} | Lighting: {lighting} | Lens: {lens_style}
CONSISTENCY: Maintain identical character appearances, color palette, and lighting mood across all shots.
TEXT-FREE: DO NOT generate any text, signs, labels, captions, or written characters in the image unless explicitly requested in this prompt."""


def build_continuity_context_phase2(
    current_shot: dict,
    continuity_notes: Optional[List[dict]] = None,
) -> str:
    """
    Phase 2.0: 构建与上一个shot的连续性上下文
    DEC-014: previous_shot_image 已移除，场景参考图+文字prompt提供环境连续性

    Args:
        current_shot: 当前shot数据
        continuity_notes: 连续性说明列表

    Returns:
        连续性上下文字符串
    """
    context_parts = []

    current_id = current_shot.get("shot_id", 0)

    # 查找相关的连续性说明
    if continuity_notes:
        relevant_note = next(
            (n for n in continuity_notes if n.get("to_shot") == current_id),
            None
        )
        if relevant_note:
            continuity_type = relevant_note.get("continuity_type", "cut")
            note = relevant_note.get("note", "")
            context_parts.append(f"CONTINUITY from previous shot: {continuity_type}")
            if note:
                context_parts.append(f"Note: {note}")

    if context_parts:
        return "\n".join(context_parts)
    else:
        return ""


def build_character_reference_mapping_phase2(
    characters_in_shot: List[str],
    characters_data: List[dict],
    scene_ref_count: int = 0
) -> str:
    """
    Phase 2.0: 构建参考图映射说明
    SQ-1: 标签声明式 — 模型直接从图上标签读取身份，不依赖 IMAGE N 精确对应
    SQ-2: 每角色 1 张参考图（智能选择 portrait 或 fullbody）

    Args:
        characters_in_shot: shot中出现的角色ID列表
        characters_data: 角色完整数据列表
        scene_ref_count: 场景参考图数量

    Returns:
        映射说明字符串
    """
    lines = ["""CHARACTER & SCENE REFERENCES:
Each reference image is labeled directly on the image.
- Images labeled "Character: XXX" → use to maintain that character's appearance
- Images labeled "Scene: XXX" → use to maintain environment consistency
The text labels on reference images are for YOUR identification only. DO NOT reproduce any label text (e.g. "Character:", "Scene:") in the generated image."""]

    # 角色身份描述（让模型知道每个角色长什么样）
    if characters_in_shot:
        lines.append("\nCHARACTERS IN THIS SHOT:")

        for char_id in characters_in_shot:
            char_data = next(
                (c for c in characters_data if c.get("id") == char_id),
                None
            )

            if char_data:
                name_zh = char_data.get("name", "")
                name_en = char_data.get("name_en", "") or name_zh
                identity = build_identity_line_phase2(char_data)

                if name_zh and name_zh != name_en:
                    lines.append(f"- {name_en} ({name_zh}): {identity}")
                else:
                    lines.append(f"- {name_en}: {identity}")

    return "\n".join(lines)


class Phase2PromptBuilder:
    """
    Phase 2.0 专业Image Prompt构建器

    整合：
    - shot的camera、composition、lighting信息
    - 全局视觉指导
    - 角色参考图映射
    - 连续性上下文
    """

    def __init__(
        self,
        storyboard: dict,
        characters: dict,
        style_preset: str = "realistic"
    ):
        self.storyboard = storyboard
        self.characters = characters.get("characters", [])
        self.style_preset = style_preset
        self.global_direction = storyboard.get("global_visual_direction", {})
        self.continuity_notes = storyboard.get("shot_continuity_notes", [])

    def build_full_prompt(
        self,
        shot: dict,
        screenplay: Optional[dict] = None,
        include_system_instruction: bool = True,
        scene_ref_count: int = 0
    ) -> dict:
        """
        构建完整的prompt包（增强版 - 包含角色一致性关键指令和剧情上下文）
        DEC-014: previous_shot 和 has_previous_shot_image 已移除

        Args:
            shot: 当前shot数据
            screenplay: 剧本数据（用于获取场景氛围）
            include_system_instruction: 是否包含系统指令
            scene_ref_count: 场景参考图数量

        Returns:
            {
                "system_instruction": str,
                "critical_header": str,
                "image_prompt": str,
                "character_mapping": str,
                "continuity_context": str,
                "narrative_context": str,
                "negative_prompt": str
            }
        """
        result = {}

        # 1. 系统指令
        if include_system_instruction:
            result["system_instruction"] = build_system_instruction_phase2(
                self.global_direction
            )
        else:
            result["system_instruction"] = ""

        # 2. 获取出场角色
        char_direction = shot.get("character_direction", {})
        characters_in_shot = char_direction.get("characters_visible", [])

        # 3. 角色一致性关键指令（如果有角色出场）
        if characters_in_shot:
            result["critical_header"] = build_critical_header_phase2()
        else:
            result["critical_header"] = ""

        # 4. 角色映射（传入新参数以正确对应contents数组顺序）
        if characters_in_shot or scene_ref_count > 0:
            result["character_mapping"] = build_character_reference_mapping_phase2(
                characters_in_shot,
                self.characters,
                scene_ref_count=scene_ref_count
            )
        else:
            result["character_mapping"] = ""

        # 5. 主prompt - 优先使用shot中已有的image_prompt
        existing_prompt = shot.get("image_prompt", "")
        if existing_prompt:
            result["image_prompt"] = existing_prompt
        else:
            result["image_prompt"] = build_phase2_image_prompt(shot, self.style_preset)

        # 6. 连续性上下文 (DEC-014: previous_shot removed)
        result["continuity_context"] = build_continuity_context_phase2(
            shot,
            self.continuity_notes,
        )

        # 7. 剧情上下文
        result["narrative_context"] = build_narrative_context_phase2(
            shot,
            None,
            screenplay
        )

        # 8. 负面prompt
        result["negative_prompt"] = build_negative_prompt(self.style_preset)

        return result
