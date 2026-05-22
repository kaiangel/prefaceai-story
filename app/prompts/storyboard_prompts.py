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

    DEC-043 RISK-T20-10 (2026-05-19):
    - human → 原 physical hair/skin/clothing 字段拼接路径 (不动)
    - 非 human → dispatch CharacterPromptBuilder.build_character_prompt() (19 类型完整支持)

    优先从physical和clothing字段获取详细信息，确保角色一致性
    """
    # T20-10: 非 human 类型走通用 builder
    char_type = (character.get('character_type') or 'human').strip().lower()
    if char_type and char_type != 'human':
        try:
            from app.services.character_prompt_builder import CharacterPromptBuilder
            return CharacterPromptBuilder().build_character_prompt(character)
        except Exception:
            desc = character.get('description', '') or character.get('extra_details', '')
            if desc:
                return desc
            return f"a {char_type} character"

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
            model="gemini-3.1-flash-lite-preview",  # 翻译用最轻量模型即可
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
# Stage 4 Prompt增强：画外音/off-screen audio 处理规则
# (RISK-T15-10, Wave 9 Phase 3, 2026-05-13)
# ============================================================================
#
# 背景：test15 Shot 21 — narration "走廊里短暂出现压低的声音与移动的脚步" 是
# off-screen audio cue（画外音），主角 Lin Xiaoyue 独自站在走廊中央，画面应只
# 有她 1 人。但 Stage 4 LLM 把"移动的脚步"翻译成画面元素 "Two blurred nurse
# silhouettes move inside the room"，结果 image_prompt 自相矛盾（"EXACTLY 1
# character" + "Two nurse silhouettes"），Seedream 生成 3-4 个角色，T17
# ShotValidator 两次 retry 都失败。
#
# 真根因：现有 Rule 6 (CHARACTER COUNT) 只禁止 "bystanders/extras/crowd"，
# 没有覆盖"narration 含声音/脚步/对话 但 characters_in_scene 不包含"的场景。
# Rule 11 (OFF-SCREEN CHARACTER) 只限"直接物理接触"，没覆盖"声音→画面元素"
# 错误翻译路径。
#
# 解决：新建独立规则块 + 强化 Rule 6 末尾，明确告诉 LLM：
#   1. 识别 off-screen audio cues（声音/脚步/对话/呼喊）
#   2. 翻译为"听觉环境暗示"而非"画面内人物"
#   3. 不要为 off-screen audio source 生成 silhouettes / shadows / blurred figures
#   4. characters_in_scene 是 ground truth — 它没列的角色，画面就没有
# ============================================================================

OFF_SCREEN_SOUND_HANDLING_RULES = """
═══════════════════════════════════════════════════════════
OFF-SCREEN AUDIO / SOUND CUE HANDLING (CRITICAL — top reason for character count failure)
═══════════════════════════════════════════════════════════

When narration mentions sounds, voices, footsteps, alarms, or actions performed by characters
NOT listed in this shot's `characters_in_scene` / `characters_visible` field, you MUST treat
them as off-screen AUDIO CUES, not as visible characters in the image.

## THE GOLDEN RULE

`characters_in_scene` (or `characters_visible`) is the GROUND TRUTH for who is in the image.
If the narration implies more characters via sound/voice/footsteps but they are NOT in this
list → those characters DO NOT appear in the image in ANY form (no silhouettes, no shadows,
no blurred figures, no body parts, no movement blur of unseen people).

## OFF-SCREEN AUDIO CUE INDICATORS (Chinese narration patterns)

| Narration Cue (Chinese) | Off-Screen Audio Type |
|------------------------|----------------------|
| 走廊里传来脚步声 / 移动的脚步 | footsteps from off-screen |
| 远处的声音 / 楼下的喧哗 | distant voices |
| 隔壁传来 / 门外响起 | sound from adjacent room |
| 警报声 / 铃声 / 低沉的警报 | alarm/bell from off-screen source |
| 压低的声音 / 低语 / 议论声 | muffled voices off-screen |
| 喊声 / 呼喊 / 叫声 | shouting from off-screen |
| 哭声 / 笑声（不在画面内的人）| crying/laughing from invisible source |
| 关门声 / 开门声 | door action by off-screen person |
| 哒哒的鞋跟声 / 拖鞋的声响 | someone walking off-screen |

## VISUAL TRANSLATION — WHAT TO DO INSTEAD

❌ BAD: render the off-screen sound source as visible figures
✅ GOOD: render the on-screen character's REACTION to the sound, plus environmental anchors

| Narration | ❌ Wrong Translation | ✅ Correct Translation |
|-----------|---------------------|----------------------|
| "走廊里短暂出现压低的声音与移动的脚步，林晓月站在走廊中央" | "Lin Xiaoyue stands alone, two blurred nurse silhouettes move inside the room" | "Lin Xiaoyue stands alone in the empty corridor, her head turning slightly toward the open door of Room 8, her eyes tracking an unseen source of sound off-frame. Only Lin Xiaoyue is visible." |
| "远处传来争吵声，他低头沉默" | "two figures arguing in the distance, he stands in front" | "He stands with head bowed, gaze cast to the floor, the corridor stretching empty behind him. Only one character visible." |
| "门外响起脚步声，她屏住呼吸" | "footsteps approaching, a shadow at the door" | "She freezes mid-action, eyes fixed on the closed door, breath held. Only one character visible." |

## ENVIRONMENTAL ANCHOR REPLACEMENTS (instead of silhouettes)

When narration cites an off-screen sound source, use these PLACE/OBJECT anchors instead
of human figures in the image_prompt:

- "the open doorway, light spilling out onto the floor"  (NOT: "silhouettes inside the room")
- "the strip of light beneath the closed door"  (NOT: "shadows moving behind the door")
- "the empty corridor stretching into the distance"  (NOT: "blurred figures at the far end")
- "her gaze drawn toward off-frame [direction]"  (NOT: "watching the people there")
- "the harsh fluorescent glare from Room 8's open door"  (NOT: "nurses working inside")

## FORBIDDEN PHRASES (when triggered by off-screen sound, never write these)

When narration ONLY mentions sound (not a visible character action), the image_prompt MUST NOT contain:
- "blurred [people/figures/silhouettes/shadows] of [other characters/nurses/staff/onlookers]"
- "two/three/several [unnamed people/figures] moving inside/outside/behind"
- "muffled silhouettes of [people] doing [action]"
- "shadows of [characters] visible through the [door/window]"
- "background figures responding to the [alarm/voice/sound]"
- "a crowd gathering off to the side"

These phrases force the image model to render extra characters that contradict
`characters_in_scene`, breaking character count validation.

## DECISION CHECKLIST (apply to every shot)

Before finalizing each image_prompt, scan the narration and verify:

1. Does the narration mention any sound/voice/footstep/alarm? → mark as off-screen cue
2. Is the sound source listed in `characters_in_scene`? → if NO, it is off-screen
3. Does my image_prompt mention figures/silhouettes/shadows of those off-screen sound sources? → if YES, REWRITE to remove them
4. Have I replaced them with on-screen character REACTION + environmental anchors? → if NO, add them
5. Does the final image_prompt's character count match `characters_in_scene` length exactly? → if NO, fix it
6. Final sentence must state: "EXACTLY N character(s) visible" where N == len(characters_in_scene)

## RATIONALE

- Image models (Seedream, NB2, etc.) treat the image_prompt as ground truth and render every
  noun/figure mentioned. They cannot distinguish "blurred silhouettes" (decorative atmosphere)
  from "blurred silhouettes" (extra characters that must be drawn).
- The T17 ShotValidator detects character count mismatch via image analysis. When prompt
  literally describes additional figures, the model renders them, validation fails, and
  the entire shot must be regenerated.
- Narration's literary devices (sound, off-screen action, implied presence) require explicit
  translation rules — the LLM cannot "infer" that sound ≠ image.
═══════════════════════════════════════════════════════════
"""

# ============================================================================
# Stage 4 Prompt增强：手 + 道具 anatomy 几何描写规则 (B45, 2026-05-11)
# ============================================================================
#
# 背景：test10 Shot 08 实测 — LLM 写 "manila folder clamped with fierce pressure
# under his left arm... knuckles white against the folder's edge"，文学性强但
# Seedream 生成图手腕扭曲、文件夹姿势怪、手指抓握不自然。
#
# 真根因：文学描写词("fierce pressure / pressed hard / knuckles white")强调
# 紧张情绪但不提供手指几何信息 — 图像模型无锚点只能凭"紧"想象，结果变形。
# 解决：要求 LLM 在描写持物时明确说明几只手 + 哪只手 + 掌心方向 + 主要手指
# 曲度/可见性，且避开暗示形变的高风险词汇。
# ============================================================================

HAND_PROP_ANATOMY_RULES = """
═══════════════════════════════════════════════════════════
HAND-PROP ANATOMY (CRITICAL — image models render hands+objects poorly without geometry)
═══════════════════════════════════════════════════════════

When a character HOLDS / GRIPS / CARRIES / CLAMPS any object (folder, phone, cup,
pen, weapon, document, bag, etc.), the image_prompt MUST provide ANATOMY GEOMETRY,
not just emotional pressure language. Image models fail at hand-object combinations
when prompts emphasize TENSION without specifying FINGER POSITION.

## Rule 1: REQUIRED ANATOMY ANCHORS (when describing a held object)

Every hand-object interaction MUST specify AT LEAST 3 of these 5 anchors:
1. WHICH HAND: "left hand" / "right hand" / "both hands"
2. WHICH FINGERS DO THE WORK: "fingers curled around" / "thumb pressed against the
   spine" / "index and middle fingers pinching the edge" / "four fingers wrapping
   the handle" (NOT vague "fingers gripping")
3. PALM ORIENTATION: "palm facing inward toward body" / "palm down" / "palm up" /
   "palm against the object's flat side"
4. WRIST ANGLE: "wrist straight" / "wrist relaxed at a natural angle" / "wrist
   bent slightly inward" (avoid extreme angles unless narrative demands it)
5. OBJECT CONTACT POINT: WHERE on the object the hand contacts (spine / edge /
   handle / side / corner)

❌ BAD: "the manila folder is clamped with fierce pressure under his left arm,
        knuckles white against the folder's edge"
   (Missing: which fingers? palm orientation? wrist angle? contact point?)

✅ GOOD: "the manila folder is tucked under his left arm — his left forearm
        crosses over his ribcage at a relaxed angle, palm flat against the
        folder's side, fingers naturally curled around its bottom edge,
        thumb resting visible on top. The folder rests parallel to his torso,
        not crushed."

❌ BAD: "her right hand holds a slim ballpoint pen, fingers wrapped tightly around
        the pen barrel, knuckles whitening slightly"
   (Missing: which fingers? thumb position? pen tip direction?)

✅ GOOD: "her right hand holds a slim ballpoint pen — thumb and index finger
        pinching the barrel near the cap, middle finger curled to support
        underneath, pen tip pointing down toward the desk, wrist resting on
        the table edge at a natural angle."

## Rule 2: HIGH-RISK VOCABULARY (avoid these in hand-object descriptions)

These words emphasize EMOTIONAL TENSION but provide NO ANATOMY, and image models
interpret them as license to render twisted/deformed hands:

❌ AVOID: "fierce pressure" / "pressed hard against" / "clamped with force" /
          "knuckles white" / "white-knuckle grip" / "death grip" / "vice grip" /
          "fingers digging into" / "crushing grip" / "trembling fingers
          (without specifying which ones)"

✅ PREFER: convey tension through CONTEXT and FACIAL/POSTURE cues instead, while
          keeping the HAND description ANATOMICALLY NEUTRAL:
   - Tension shown via face/posture: "his jaw is clenched, shoulders rigid"
   - Hand stays neutral: "his left hand holds the folder tucked under his arm,
     fingers naturally curled around the bottom edge"
   - Result: viewer reads tension from the face/body, image model renders the
     hand correctly because anatomy is unambiguous.

## Rule 3: ONE HAND PER OBJECT (default)

Default to ONE hand per object unless the narrative explicitly shows two-handed
contact (e.g., reading a book open in both palms, gripping a steering wheel,
typing on a keyboard). Two-handed object contact MUST justify itself in the action.

❌ BAD: "both hands grip the small phone tightly" (overkill for a phone)
✅ GOOD: "his right hand holds the phone at chest height, screen facing him,
         thumb hovering near the unlock button, left hand resting at his side"

## Rule 4: FINGERS-OUT-OF-FRAME ESCAPE HATCH

If a held object is small or partially occluded and explicit finger geometry
would be awkward, you MAY frame the hand to keep fingers OUT OF VIEW:
- "the bottom half of the folder visible at frame's edge, his arm cropped at
  the elbow" (hand off-screen)
- "her hand cropped behind the cup, only the handle visible from camera's POV"
- "fingers obscured by the angle of the desk"

This is preferable to writing a tense-but-vague hand description that the model
will mangle.

## Rule 5: SELF-CHECK BEFORE FINALIZING

Before finalizing each shot's image_prompt, scan for ANY hand-object verb
(hold / grip / clutch / clamp / clasp / clench / grasp / pinch / press /
pick up / set down / hand / pass). For EACH occurrence:
- Does the description name WHICH hand?
- Does it specify FINGER position or PALM orientation?
- Does it AVOID the high-risk vocabulary in Rule 2?
- If multi-character: does it respect MULTI-CHARACTER LIMB INTERACTION LIMITS?

If any answer is no → revise the description with Rule 1's anchors before output.

═══════════════════════════════════════════════════════════
WHY THIS MATTERS: Image generation models (Seedream, NB2, SDXL, DALL-E 3) all
share the same weakness — hands holding objects is the #1 failure mode in
character images. The fix is GEOMETRY, not TENSION. State where each finger
goes, and the model has an anchor to render. Without anchors, "fierce pressure"
becomes "twisted wrist + extra finger".
═══════════════════════════════════════════════════════════
"""

# ============================================================================
# Stage 4 Prompt增强：B52-L6 防御性 — 发色显式强制规则
# 背景: Seedream 对"亚洲女性"有"默认黑发"统计先验。当 Stage 4 LLM 生成的
# image_prompt 不写发色时，模型在参考图 attention 被稀释的情况下会回归默认黑发，
# 破坏角色一致性（test12 实测：7 张黑发 vs 8 张亚麻青）。
# 解决：强制 LLM 在每个含角色的 shot image_prompt 中显式提及发色。
# ============================================================================

HAIR_COLOR_REQUIREMENT_RULE = """
═══════════════════════════════════════════════════════════
IDENTITY ANCHORS DELEGATION (DEC-048 Layer 1, 2026-05-22)
═══════════════════════════════════════════════════════════

🔒 IMPORTANT — DIVISION OF LABOR (DO NOT VIOLATE)

Character identity anchors (hair_color, hair_style, face_shape, skin_tone,
eye_color, eye_shape, distinctive_marks, clothing_core) are MANAGED BY BACKEND
POST-PROCESS INJECTION. They are NOT your responsibility.

The backend will automatically prepend an authoritative
`[IDENTITY ANCHORS — MUST APPEAR EXACTLY AS DESCRIBED]` block to every
image_prompt before it reaches the image generation model. That block is the
SINGLE SOURCE OF TRUTH for character physical descriptions.

## YOUR JOB (Stage 4 LLM)

Write image_prompt with ONLY narrative variables — the creative layer that
serves the current shot's storytelling:

| Narrative Variable | Description | Example |
|--------------------|-------------|---------|
| pose               | Full-body posture for this shot | "chin lifted, both hands at chest" |
| expression         | Facial emotion for this shot | "eyes wide, lips slightly parted" |
| camera_angle       | birds_eye/high/eye/low/dutch | "low_angle" |
| camera_distance    | ECU/CU/MCU/MS/MWS/WS/EWS | "medium_shot" |
| emotion            | Inner emotional state | "determination, defiance" |
| interaction        | With other characters or props | "facing the antagonist, hand grips pendant" |
| scene_action       | What happens in this shot | "stands at the palace center" |

## CRITICAL DO-NOTs

❌ DO NOT include character physical descriptions (hair color, face, skin, eye color,
   distinctive_marks, signature clothing) in image_prompt.
❌ DO NOT invent or paraphrase hair color (e.g. "dark hair", "flowing locks",
   "blonde curls") — backend's anchor block carries the authoritative hair color value.
❌ DO NOT include style keywords (e.g. "watercolor", "photorealistic",
   "Pixar 3D") — backend's STYLE ANCHOR block handles this.
❌ DO NOT include location signature visuals (e.g. "bioluminescent coral
   pillars", "neon-lit alleyway") — backend's LOCATION ANCHOR block handles this.

Adding duplicate or contradictory descriptions WILL cause conflict with the
authoritative anchor block and produce image generation drift (this is the
test22 / DEC-048 root cause — historical "Format example" hints were treated
as soft suggestions and freely overridden by LLM creative impulse).

## HOW TO REFER TO CHARACTERS

Reference characters by their `id` or `name_en` ONLY:

❌ BAD: "Coral with her flowing dark hair lifts her chin"
        (invents physical detail — conflicts with anchor)
❌ BAD: "the mermaid girl with sea-green hair raises her hand"
        (duplicates anchor — wastes prompt budget + risks conflict)
✅ GOOD: "char_001 (Coral) stands at the palace center, chin lifted with
         determination, both hands raised to her chest, gaze locked
         unflinchingly on the antagonist beyond"
✅ GOOD: "Coral (char_001) — low_angle medium shot — pulls back slightly,
         eyes wide and direct, her right hand wrapping around the pendant
         at her chest"

## WHY THIS DIVISION WORKS

Image generation models (Seedream / NB2 / Midjourney / Sora) have strong
statistical priors (e.g. "Asian female → black hair") that override text
when the prompt is vague. The ONLY reliable mitigation is an explicit anchor
block at the prompt's top (where model attention is highest). Letting the
LLM "remember to mention" anchors is unreliable — RLHF training optimizes
for narrative quality over schema fidelity, so soft instructions are
systematically ignored under creative pressure.

By cleanly separating concerns:
- LLM → creative narrative (what's happening in this shot)
- Backend → identity anchors (who the characters fundamentally are)

…we eliminate the entire class of "character physical drift" bugs that
plagued v1-v3 prompt engineering attempts.

═══════════════════════════════════════════════════════════
"""

# ============================================================================
# Stage 4 Prompt 增强：RISK-T20-17 物种/角色身份保真规则 + 角色数据块构建器
# (DEC-045, 2026-05-19)
# ============================================================================
#
# 背景：test17 v2 Shot 10 实证 — Stage 4 LLM 把 char_002 (兔子 米莉/Milly) 写成
# "a small hedgehog-like creature with warm brown fur and a dried winter-grass collar"。
# Seedream 收到"hedgehog"文本 + 兔子参考图，文本优先级高 → 渲染成刺猬。
# 同 shot 中 char_003 (麻雀 啾啾) 也丢失了 "白色翼纹" 等物种识别特征。
#
# 真根因（5 维度调用链路追踪 2026-05-19）:
#   1. characters_in_scene 正确 ["char_002", "char_003"] ✓
#   2. reference_images 正确传入 (兔子 fullbody + 麻雀 fullbody + scene_ref = 3) ✓
#   3. ❌ Stage 4 `_build_scene_prompt()` (storyboard_director.py L1537) 给 LLM 的
#      character data 块只含 {id, name, clothing_summary}，**完全没有 character_type
#      和 species 字段**。clothing 字段是中文时 `_extract_english_from_field()`
#      strip 成空，再 fallback 成 "see character reference image" — LLM 拿到的有效
#      信息是：name="Milly", clothing="see character reference image"。
#   4. CRITICAL: IMAGE_PROMPT MUST BE WRITTEN ENTIRELY IN ENGLISH 规则告诉 LLM
#      "Do NOT copy or transliterate any Chinese characters into image_prompt"，导致
#      LLM 不能从中文 narration "小兔米莉" 抓物种线索。
#   5. LLM 只能凭"暖色+冬草围领+小动物"的语义自由发挥 → 输出 "hedgehog-like creature"。
#
# Wave 14 + T20-10 修复了 `_build_character_appearance()` / `_build_identity_line_phase2()`
# / `_build_character_description()`（**runtime 拼装**层），但 **Stage 4 LLM 输入** 层
# 完全没修——LLM 看不到 species，怎么可能在 image_prompt 中写正确物种？
#
# 解决：Stage 4 LLM 输入层加 species/character_type 字段 + 显式保真规则
#   1. build_stage4_character_data_block() — 给 LLM 的 character data 块加 species/type/appearance
#   2. SPECIES_FIDELITY_RULES — 强制 LLM 使用声明的物种，不许自由替换
#
# 验证（test17 v2）:
#   旧 prompt 给 LLM 的 char_002 数据: {"id":"char_002","name":"Milly","clothing_summary":"see character reference image"}
#   新 prompt 给 LLM 的 char_002 数据: {"id":"char_002","name":"Milly","character_type":"anthropomorphic_animal","species":"rabbit","appearance":"A young female rabbit anthropomorphic rabbit with clean warm ivory white...","clothing_summary":"cream knitted vest..."}
# ============================================================================

SPECIES_FIDELITY_RULES = """
═══════════════════════════════════════════════════════════
SPECIES / CHARACTER-TYPE FIDELITY (CRITICAL — top reason for character mis-rendering in non-human stories)
═══════════════════════════════════════════════════════════

Each character in the Character data block has a FIXED `character_type` and (for
anthropomorphic/animal characters) a FIXED `species` value. These values are
GROUND TRUTH from the user-confirmed character roster.

## THE GOLDEN RULE

When you write image_prompt, for EVERY character you mention you MUST use the
EXACT species/type noun declared in the Character data block. NEVER invent,
substitute, or guess a different species or character type.

## FORBIDDEN PATTERNS (will silently destroy character consistency)

❌ FORBIDDEN: substituting one animal species for another similar-looking one
   - character_type=anthropomorphic_animal, species=rabbit → writing "hedgehog-like creature" ❌
   - character_type=anthropomorphic_animal, species=fox → writing "small dog" or "wolf cub" ❌
   - character_type=anthropomorphic_animal, species=sparrow → writing "small finch" or "robin" ❌
   - character_type=anthropomorphic_animal, species=wolf → writing "husky" or "large dog" ❌

❌ FORBIDDEN: vague/hedged species nouns ("hedgehog-like", "fox-like", "bird-like", "creature")
   when a specific species is declared. The image model will render whatever noun
   you write — vague nouns produce vague (often wrong-species) results.

❌ FORBIDDEN: defaulting to human descriptors for non-human characters
   - character_type=anthropomorphic_animal → "young Asian woman" ❌ (Wave 14 / T20-10)
   - character_type=robot → "young man with metallic skin" ❌
   - character_type=fantasy_creature → "young Asian person with glowing eyes" ❌

❌ FORBIDDEN: omitting the species noun entirely when describing a character
   - "Milly's wing raised to cover her face" ❌ (Milly is rabbit, not bird — no wings!)
   - "Jojo's tail flicking in the wind" ❌ (Jojo is sparrow — has feathers, not tail like a mammal)

## REQUIRED PATTERN

✅ For each character noun mention, include the declared species as the head noun:
   - "the young female rabbit Milly raises her paws to cover her face"
     (species=rabbit explicit → paws, not wings)
   - "the young female sparrow Jojo hops backward, her wings tucked against her body"
     (species=sparrow explicit → wings, not arms)
   - "the elderly female fox Grey Fox sits in the snow, her forepaw resting on her knee"
     (species=fox explicit + age + gender)

✅ For each anatomy mention, use the species-correct body part:
   - rabbit → long ears, paws, hind legs, fluffy tail, twitching nose
   - sparrow / bird → wings, beak, feathered tail, talons, head-tilting
   - fox / wolf / dog → snout, paws, fur, brush tail, pointed ears
   - cat → whiskers, paws, slit pupils, retractable claws, swishing tail
   - bear → muzzle, paws, dense fur, shoulder hump
   - mouse / squirrel → small paws, whiskers, large round ears, bushy tail

## SPECIES-CORRECT ANATOMY CROSS-REFERENCE TABLE

| Species | Has | Lacks |
|---------|-----|-------|
| rabbit | paws, long ears, hind legs, fluffy tail | wings, beak, snout, mane |
| sparrow / bird | wings, beak, feathers, talons, feathered tail | paws, fur, snout, whiskers, hands |
| fox / wolf | snout, paws, fur, brush tail, pointed ears | wings, beak, scales, whiskers (cat-style) |
| cat | paws, whiskers, slit pupils, swishing tail, retractable claws | wings, beak, hooves |
| bear | muzzle, paws, dense fur | wings, beak, scales |
| hedgehog | quills/spines, snout, paws, small round ears | fluffy fur, long ears, wings |
| squirrel | bushy tail, small paws, whiskers, large eyes | wings, beak, long ears |

## ANTI-PATTERN FROM REAL FAILURE (test17 v2 Shot 10)

❌ ACTUAL BAD OUTPUT (Stage 4 LLM, 2026-05-19):
   "Milly, a small hedgehog-like creature with warm brown fur and a dried
   winter-grass collar that trembles faintly as she bows her head"
   ↑ character_type=anthropomorphic_animal, species=rabbit, but LLM wrote
   "hedgehog-like" because species was MISSING from character data block.

✅ CORRECT OUTPUT (with species in character data block + this rule):
   "Milly, a young female anthropomorphic rabbit with clean warm ivory white
   fur, single small pale freckle on left ear tip, wearing cream knitted vest
   and dusty brown short skirt with a fluffy ruff of dried winter grass around
   her neck — she bows her head, her long upright ears drooping slightly forward,
   her small paws curled inward at her chest"
   ↑ species=rabbit explicit → correct ears + paws + posture geometry.

## SELF-CHECK BEFORE EACH SHOT OUTPUT

For EVERY character listed in characters_in_scene, verify:
  □ Did I name this character's declared species at least once in image_prompt?
  □ Did I avoid hedged language ("X-like creature", "creature resembling X")?
  □ Did I use species-correct anatomy nouns (rabbit→paws/ears, bird→wings/beak)?
  □ Did I avoid human descriptors (Asian woman/man) for non-human characters?
  □ For anthropomorphic_animal: did I say "anthropomorphic [species]" not just "[species]"
     (so the model knows to render clothing + bipedal posture, not a real wild animal)?

If ANY check fails → REWRITE that character's description before output.

## WHY THIS IS CRITICAL

Image models (Seedream, NB2) treat the text image_prompt as authoritative ground
truth, even when it conflicts with reference images. Text overrides reference
in species classification (test17 v2 Shot 10 evidence: rabbit reference image +
"hedgehog-like creature" text → Seedream rendered hedgehog). Therefore species
fidelity in the text prompt is non-negotiable.

═══════════════════════════════════════════════════════════
"""


# ============================================================================
# DEC-045 RISK-T20-26 + KEY_LEARNINGS #37 (2026-05-19): Seedream 暗黑题材敏感词避开规则
# ----------------------------------------------------------------------------
# 真根因 (test19 Shot 15 实证, Founder 5 次重生全失败):
#   Stage 4 StoryboardDirector LLM 在暗黑奇幻 / 灵异 / 已故角色重逢等场景时, 自由发挥
#   写出 "ghost of grandfather / double-exposure of two faces / younger face emerges /
#   identical jaw / two faces overlapping with exact contour alignment" 等高敏感词描述.
#   下游 Seedream 内容安全策略对这些词明确敏感 → 100% 拒生成 → Pipeline failure.
#
# 反复手动重生不能救 (T20-26): PromptRewriter 即使切到 Mode B 也只能事后清洗,
# 真正的根治是 Stage 4 LLM 一开始就别写这些词. → 在 prompt 中告诉 LLM 用安全替代.
#
# Universal: 适用所有故事类型 (恐怖 / 悬疑 / 奇幻 / 武侠 / 现代都市的回忆场景等),
# 不只 dark_fantasy. 任何"已故角色出现 / 灵异 / 双重曝光 / 面孔重叠"叙事意图都走这套规则.
#
# 当 Stage 3 ScreenplayWriter 输出含已故角色出现/灵异/双重曝光意图的 narration 或
# action_beat 时, Stage 4 LLM 必须用本规则块定义的 safe rewrite patterns 写 image_prompt.
# ============================================================================

SEEDREAM_SAFETY_AVOIDANCE_RULES = """
═══════════════════════════════════════════════════════════
SEEDREAM CONTENT-SAFETY AVOIDANCE (DEC-045 T20-26 + KEY_LEARNINGS #37 — CRITICAL)
═══════════════════════════════════════════════════════════

The image generation model (Seedream `doubao-seedream-5-0-260128`) has strict
content-safety filters that REJECT prompts containing ghostly / supernatural /
double-exposure / face-overlap / deceased-character-emergence descriptions.
test19 Shot 15 was rejected 5 consecutive times because Stage 4 LLM wrote a
"double-exposure of living face + ghost of deceased grandfather, identical jaw,
two faces overlapping with exact contour alignment" image_prompt.

When you write image_prompt for ANY scene involving:
  - A deceased / ghost / spirit / phantom character appearing alongside a living character
  - Memory / vision / flashback rendered as overlay on a living character
  - Past-self / future-self / younger-self / older-self merging with current character
  - Two characters' faces merging / blending / overlapping
  - Spiritual / supernatural / haunted / spectral atmosphere with a visible figure

YOU MUST AVOID the following Seedream-rejected phrases and use the SAFE
ALTERNATIVES below instead.

## FORBIDDEN PHRASES (Seedream will reject the entire image)

❌ "ghost of [character]" / "ghostly figure of [character]"
❌ "ghost of light" / "spectral form" / "spectral presence" / "phantom shape"
❌ "apparition of [character]" / "wraith" / "specter" / "haunted [place]"
❌ "vision of [deceased character]" / "deceased emerges" / "deceased appears"
❌ "double-exposure of [A] and [B]" / "double exposed faces" / "double-exposed vision"
❌ "face overlapping with [character]" / "faces overlapping with exact contour alignment"
❌ "two faces merging" / "faces blending into one" / "two-face composition"
❌ "younger face emerges through [living character]'s features"
❌ "older face surfaces in [character]'s reflection"
❌ "memory emerges" / "spirit emerges" / "soul emerges" (when describing visible overlay)
❌ "identical jaw / identical scar / identical face / identical contour"
   (when describing visual overlap of two characters' features)
❌ "exact contour alignment of [two characters]" / "exact face alignment"
❌ "[A]'s face dissolves into [B]'s face"
❌ "[A]'s features become [B]'s features"

## SAFE ALTERNATIVES (preserve the same emotional / narrative beat)

When the SCREENPLAY (Stage 3) calls for a deceased character to appear with
the living, use one of these alternative visual strategies:

### Strategy 1: SYMBOLIC OBJECT (preferred for resemblance / memory beats)
✅ "[Living character] alone in the scene. An old framed photograph of [deceased]
   visible on the wall / desk / mantelpiece in soft focus. EXACTLY 1 character visible."
✅ "[Living character] kneels, holding an old photograph of [deceased] in their hands.
   EXACTLY 1 character visible."
✅ "[Living character] standing alone, the deceased's belongings (urn / coat / hat /
   keepsake) arranged on a nearby surface. EXACTLY 1 character visible."

### Strategy 2: WARM LIGHT (preferred for spiritual presence / "felt presence" beats)
✅ "[Living character] kneels in the snow, a single warm golden halo of light
   diffusing around their head and shoulders — symbolic, not a second figure.
   EXACTLY 1 character visible. No apparitions, no overlays."
✅ "[Living character] sits alone, soft warm light from off-frame illuminating
   one side of their face — symbolic of remembered presence, NOT a second character.
   EXACTLY 1 character visible."

### Strategy 3: SOLO + EMOTION (preferred for grief / recognition / awakening beats)
✅ "[Living character] alone, eyes closed in remembrance, a single tear tracking
   down one cheek, warm golden side light. EXACTLY 1 character visible."
✅ "[Living character] looks down at their own hands in their lap, expression
   of dawning recognition. The deceased's faded photograph rests on the floor
   beside them. EXACTLY 1 character visible."

### Strategy 4: DEFOCUSED BACKGROUND FIGURE (only if absolutely needed — avoid when possible)
✅ "[Living character] in sharp focus in the foreground. Far in the deep background,
   completely out of focus, a vague human silhouette suggested by lighting (not a
   recognizable face, not aligned with [living character]'s features). EXACTLY 2
   figures: 1 sharp + 1 deeply-blurred suggestion."

   ⚠️ Strategy 4 only when Stage 3 explicitly requires the deceased visible.
   Strategies 1-3 are preferred.

## NARRATIVE BEAT → SAFE REWRITE TABLE

| Stage 3 narrative beat (intent) | ❌ FORBIDDEN image_prompt | ✅ SAFE image_prompt |
|----------------------------------|---------------------------|---------------------|
| 主角看到已故爷爷的"幻影" | "double-exposure of [Living] and [Ghost grandfather] with identical jaw" | "[Living] kneels alone, old portrait of grandfather on wall in soft focus" |
| 主角发现自己长得和爷爷一模一样 | "ghost of younger grandfather emerges through [Living]'s face" | "[Living] holds up an old photograph of grandfather beside their own face in a mirror, mirror shows their own face only" |
| 死者灵魂出现安慰生者 | "spectral apparition of deceased stands behind [Living]" | "[Living] sits alone, a warm golden glow lighting one side of their face, no other figure visible" |
| 主角穿越时空与年轻自己相遇 | "double exposure of older self and younger self overlapping" | "two separate panels side-by-side, OR: [Living] alone, looking at a faded childhood photograph in their hands" |
| 主角在墓前与死者对话 | "ghost of deceased emerges from gravestone, two faces overlapping" | "[Living] kneels alone at the gravestone, both hands pressed to the stone, eyes closed, warm sunset side light" |
| 灵异/恐怖：有鬼魂飘过 | "ghostly figure floats in the hallway" | "[Living] alone in the hallway, looking off-frame at something unseen, cold blue side light creates atmospheric tension" |

## SELF-CHECK BEFORE EACH SHOT OUTPUT

For EVERY shot, BEFORE finalizing the image_prompt, scan it for these forbidden tokens:
  □ "ghost" / "ghostly" / "spectral" / "phantom" / "apparition" / "wraith"
  □ "double-exposure" / "double exposed" / "two-face composition"
  □ "face overlapping" / "faces overlapping" / "faces merging" / "faces blending"
  □ "younger face emerges" / "older face surfaces" / "deceased emerges"
  □ "identical jaw" / "identical scar" / "identical face" / "identical contour"
  □ "exact contour alignment" / "exact face alignment"
  □ "vision of [deceased X]" / "haunted"

If ANY forbidden token appears, REWRITE that sentence using the appropriate
Strategy 1-4 above BEFORE outputting the shot. Do NOT submit any image_prompt
containing these tokens — Seedream will reject it.

## WHY THIS IS CRITICAL (test19 Shot 15 evidence)

Without this rule, Stage 4 LLM (Claude Sonnet 4.6) writes the most dramatically
expressive image_prompt it can, including double-exposure / ghost / overlapping
faces. Seedream then rejects 100% of these. PromptRewriter retry (Sonnet 4.6
Mode B) can sometimes save them post-hoc, but a much cleaner solution is to
PREVENT generation of forbidden phrases at Stage 4 in the first place.

═══════════════════════════════════════════════════════════
"""


# ============================================================================
# T20-48 ANATOMY_FIDELITY_RULES — Human anatomy hard constraints for Seedream
# ----------------------------------------------------------------------------
# Background: test20 Shot 16 anatomy_issue: "4 hands visible (normal humans
# have 2 hands)" + "4 arms visible". Seedream hallucinates extra limbs when
# action descriptions are ambiguous (e.g. "typing" implied 2 users at same desk).
#
# Fix: Inject hard anatomical constraints BEFORE any action description so
# Seedream has an explicit anchor rather than inferring limb counts.
#
# Author: @AI-ML
# Date: 2026-05-20
# Owner: TASK-T20-48 P2
# ============================================================================

ANATOMY_FIDELITY_RULES = """
═══════════════════════════════════════════════════════════
ANATOMY FIDELITY RULES (T20-48 — MANDATORY HARD CONSTRAINTS)
═══════════════════════════════════════════════════════════

Human anatomy MUST be strictly accurate in every image_prompt. Image generation
models (Seedream) hallucinate extra limbs when action descriptions are ambiguous.

## MANDATORY LIMB COUNTS (per character)

For EVERY human character visible in the shot, the rendered image MUST show:
- EXACTLY 2 hands (no more, no less)
- EXACTLY 2 arms
- EXACTLY 2 legs / feet (if lower body is in frame)
- Normal human proportions — no elongated, fused, or duplicate body parts

## ACTION DISAMBIGUATION RULES

When a character performs an action involving hands/arms, the image_prompt MUST
explicitly disambiguate which hands are doing what, so Seedream renders the correct
count without hallucination.

❌ BAD (ambiguous — model may infer extra hands):
  "typing at the keyboard" (implies 2 people or extra hands if another character is near)
  "holding the phone while gesturing"
  "reaching for the door while gripping the bag"

✅ GOOD (explicit — exactly 1 character, 2 hands accounted for):
  "typing at the keyboard with both hands flat on keys, fingers at rest position"
  "right hand holding the phone at ear level, left hand resting on the desk"
  "right hand reaching for the door handle, left hand holding the bag strap"

## MULTI-CHARACTER LIMB SEPARATION

When MULTIPLE characters appear in the same shot:
- Clearly separate each character's body space in the composition description
- Avoid overlapping arm/hand descriptions between characters
- If characters are physically separated (e.g. either side of a table), state the
  spatial separation explicitly

❌ BAD: "both characters reaching across the table" (Seedream may merge their arms)
✅ GOOD: "[Char A] on the left side, right arm extended across table; [Char B] on
         the right side, left arm extended, their fingertips nearly touching"

## SELF-CHECK BEFORE OUTPUT

Before finalizing any image_prompt containing human characters:
1. Count hands: exactly 2 per visible human character?
2. Count arms: exactly 2 per visible human character?
3. If action verb is present (type / hold / reach / grab / point / gesture /
   wave / push / pull / lift / carry): is WHICH hand (left/right/both) explicit?
4. Multi-character: are body spaces separated and non-overlapping in description?

If ANY check fails → add explicit limb/hand attribution before output.

## WHY THIS IS CRITICAL (test20 Shot 16 evidence)

Shot 16 image_prompt described typing action near another character. Seedream
rendered 4 hands visible on screen. T17 ShotValidator flagged anatomy_issue:
"4 hands visible (normal humans have 2 hands)". Explicit hand attribution in
the prompt prevents this class of hallucination entirely.

═══════════════════════════════════════════════════════════
"""

# ============================================================================
# DEC-046 T20-28 v3 Stage 4 STORYBOARD DIRECTOR — Universal Narrative Principles
# ----------------------------------------------------------------------------
# Stage 4 由 Stage 3 输出的 dialogue_beats / narration / action_beats 构造每个
# shot 的 image_prompt + text_overlay. v3 在 Stage 4 加 6 个新规则块:
#
#   1. IMAGE_TEXT_COMPLEMENT_RULES   — 文字补心理/反转, 不重复 image_prompt (原则 5)
#   2. MINIMAL_DIALOGUE_RULES         — 1-3 字 OK 修订 D2 反例 (原则 6)
#   3. TIMELINE_JUMP_MARKER_RULES     — 时间跳转 shot 必标 (原则 9)
#   4. MULTI_CHARACTER_DIALOGUE_RULES — 多角色 speaker 区分 (原则 12)
#   5. METAPHOR_SYMBOL_RULES          — 隐喻象征 caption (原则 14)
#   6. CULTURAL_CONTEXT_RULES         — 文化时代背景 (原则 15)
#
# 不破坏 Wave 4 已有 (COMIC_MODE_NARRATIVE_RULES / SPECIES_FIDELITY_RULES /
# SEEDREAM_SAFETY_AVOIDANCE_RULES). v3 在它们后面叠加.
#
# Author: @AI-ML
# Date: 2026-05-20
# Owner: TASK-T20-FIXBATCH-6 Wave 5 RISK-T20-28 P0 (DEC-046)
# ============================================================================


# ----------------------------------------------------------------------------
# Module S4-1 — IMAGE_TEXT_COMPLEMENT_RULES (原则 5)
# ----------------------------------------------------------------------------

IMAGE_TEXT_COMPLEMENT_RULES = """
═══════════════════════════════════════════════════════════
🖼️ IMAGE-TEXT COMPLEMENT RULES (DEC-046 v3 原则 5 — CRITICAL)
═══════════════════════════════════════════════════════════

text_overlay 上的文字**必须补充画面看不到的信息**, 不能重复画面已经表达的事.
文字浪费 → 读者眼睛累 + 误以为这是重要信息 → 注意力被骗.

## RULE ITC-1 — DO NOT REPEAT WHAT IMAGE ALREADY SHOWS

❌ BAD examples:
- image_prompt 已经描述 "苏晨低头哭" + text_overlay="（她在哭）"
  → 重复! 应该补"为什么哭": text_overlay="（他还是没回头。）"
- image_prompt 已经描述 "陈砚跪在墓碑前" + text_overlay="陈砚跪在墓碑前"
  → 重复! 应该补 reveal: text_overlay="碑上刻着: 陈砚。"
- image_prompt 已经描述 "天空下雪" + text_overlay="下雪了"
  → 重复! 应该补时间或情感: text_overlay="第二十三年, 立春雪。"

✅ GOOD examples:
- image_prompt: "苏晨低头哭, 林浩在远处看" + text_overlay="（其实我只是想他多关心一点。）"
  → 补内心动机, 画面没告诉
- image_prompt: "陈砚跪在墓碑前, 手按在碑面" + text_overlay="碑上刻着: 陈砚。"
  → 补 reveal 信息, 读者关键转折看到
- image_prompt: "雪林中老灰狐独行" + text_overlay="二十三年了, 每年立春。"
  → 补时间感, 画面看不出

## RULE ITC-2 — FOUR ALLOWED TEXT FUNCTIONS

text_overlay 应该且仅应该做 4 件事:

### 功能 A: 补心理动机 (THOUGHT — 内心独白)
- 角色脸上表情不能完全表达内心时, thought 补
- 示例: 画面"她笑着说没事" + thought="（其实心里发酸。）" → 反差揭示

### 功能 B: 补 reveal / 因果 / 关系 (DIALOGUE/NARRATION — 关键信息)
- 画面看不出"是谁/做了什么/为什么/什么关系/什么后果"时, 文字补
- 示例: 画面"墓碑特写" + narration="碑上刻着: 陈砚。" → 补关键 reveal

### 功能 C: 补时间/地点跳转 (NARRATION caption)
- 场景切换 shot 必标"三年后/深夜/回到那天"
- 示例: 画面"老男人在书房" + narration="二十三年后。"

### 功能 D: 推进对话 (DIALOGUE)
- 角色之间真在说话 → dialogue 推进
- 示例: 画面"两人对峙" + dialogue=["你为什么骗我?", "我没有。"]

❌ 其他用途 (重复画面 / 形容画面 / 修饰画面) — FORBIDDEN

## RULE ITC-3 — IMAGE/TEXT INFO SPLIT WORKFLOW

For each shot, 在写 text_overlay 前先问:
1. **看 image_prompt**: 这张图读者能看到什么? (人物 / 动作 / 场景 / 道具)
2. **看 dialogue_beats** (Stage 3 提供): 哪些信息**必须**让读者知道?
3. **算差集**: dialogue_beats 必传信息 - image 已显示 = **text_overlay 应该补的**
4. **写 text_overlay**: 把差集精炼到 ≤35 字/句

## RULE ITC-4 — VISUAL-COMPLEMENT EXAMPLES (跨题材)

| Cluster | 画面 image_prompt | text_overlay (补) | 为什么互补 |
|---------|------------------|------------------|-----------|
| C1 恋爱 | "苏晨和林浩沉默走路, 神色冰冷" | thought="（明明很想他先开口。）" | 画面看不出内心 |
| C2 悬疑 | "电梯门慢慢打开" | narration="三点二十七分。" | 画面没时间感 |
| C4 童话 | "小熊抱着苹果笑" | dialogue="好甜!!!" | 画面看不出味觉 |
| C5 武侠 | "师父递剑给弟子" | dialogue="此剑传你, 望你守心。" | 画面无对话信息 |
| C6 科幻 | "AI 终端显示 ERROR" | narration="第 47 次时间循环。" | 画面无 context |
| C7 喜剧 | "他在镜头前笑得僵硬" | thought="（卧槽老板在身后!）" | 画面看不出反差原因 |

═══════════════════════════════════════════════════════════
"""


# ----------------------------------------------------------------------------
# Module S4-2 — MINIMAL_DIALOGUE_RULES (原则 6) — 修订旧 RULE 6 反例
# ----------------------------------------------------------------------------

MINIMAL_DIALOGUE_RULES = """
═══════════════════════════════════════════════════════════
💎 MINIMAL DIALOGUE RULES (DEC-046 v3 原则 6 — REVISES PRIOR D2 ANTI-EXAMPLES)
═══════════════════════════════════════════════════════════

🚨 重要修订: 之前 RULE D2 / RULE 6 把"怎么了？" "你来了" "走吧" 列为"vague/lazy"反例.
**v3 撤销**: 在 C1 (恋爱) / C7 (喜剧) / C4 (童话) cluster 中, 极简对话 1-3 字
是**专业漫画的标准做法**, 不是 lazy.

证据 — storyrefs/story1 真实漫画范例:
- IMG_0815: 整张 shot 只有 "好。" (1 字 dialogue) → 表达"接受/和解"情感冲击力极强
- IMG_0812: "对不起。" + "什么?" + "他懵了。" → 全部 ≤4 字, 节奏漫画级
- IMG_0808: "对不起宝宝, 我改…" 7 字 → 极简但情感满

## RULE MDR-1 — 极简对话适用场景 (1-3 字 OK)

### 适用条件 (任一满足)
- 角色情绪冲击 ("好。" 接受 / "走。" 决绝 / "停。" 制止)
- 关键决定 ("不!" 拒绝 / "嫁。" 答应 / "杀。" 报复)
- 反应词 ("什么?" 震惊 / "啊?" 困惑 / "嗯。" 默许)
- 称呼 ("妈。" 找妈妈 / "哥。" 求救)
- 情绪爆发短句 ("滚!" / "去死!" / "够了!")

### 不适用场景 (1-3 字会显空泛)
- 信息推进对话 (要传 plot 必须 ≥5 字)
- 角色第一次出场 (用关系词介绍)
- 反转 shot (要 reveal 必须 ≥10 字)
- 长独白心理戏 (thought 应该完整)

## RULE MDR-2 — 极简对话 BY CLUSTER

### C1 强情感代入 (恋爱/家庭/治愈)
- 频率: 整个故事 2-5 处 1-3 字 dialogue (情感节点)
- 典型: "好。" "嗯。" "走。" "回来。" "对不起。" "宝宝…"
- ✅ IMG_0815 例: "好。" (女主接受男主道歉)

### C2 悬疑恐怖
- 频率: 1-3 处 1-3 字 dialogue (恐怖瞬间)
- 典型: "别动!" "快跑!" "她…" (没说完的话最恐怖)
- ✅ 示例: dialogue="后面…" (主角看到后面有人但说不完整)

### C4 童话绘本
- 频率: 5-10 处 1-3 字 dialogue (萌系反应)
- 典型: "好甜!" "嗨呀!" "啊?" "嗯嗯!" "好香!"
- ✅ 示例: dialogue="嘿嘿。" (小熊吃到苹果的满足)

### C5 古风武侠
- 频率: 2-4 处 1-3 字 dialogue (江湖意气)
- 典型: "去。" "退!" "杀。" "走。" "好。"
- ✅ 示例: dialogue="退!" (师父让弟子撤退)

### C7 喜剧吐槽
- 频率: 多处 1-3 字 dialogue + 大字 punchline
- 典型: "?" "??" "卧槽。" "我去!" "啊?!"
- ✅ 示例: thought="（卧槽这都行?）"

### C8 现实题材
- 频率: 1-3 处 1-3 字 dialogue (沉默时刻)
- 典型: "嗯。" "好。" "知道了。" "再见。"

## RULE MDR-3 — 极简对话 + 表情画面互补

极简对话**必须**配上**强表情**的 image_prompt 才有效果. 否则空白.

✅ GOOD: dialogue="好。" + image_prompt="苏晨抬头, 第一次正眼看林浩, 眼角带泪, 唇角微抬"
   → "好。" 1 字撑住 + 表情承载剩余 99% 情感

❌ BAD: dialogue="好。" + image_prompt="苏晨站着, 中性表情"
   → 表情没承载, 1 字显空

## RULE MDR-4 — 极简对话 + thought 内心独白配合

极简 dialogue 表外, thought 表内:
✅ dialogue="对不起。" + thought="（其实我不是真的对不起。）"
   → 外冷淡内心狡黠 反差揭示

═══════════════════════════════════════════════════════════
"""


# ----------------------------------------------------------------------------
# Module S4-3 — TIMELINE_JUMP_MARKER_RULES (原则 9)
# ----------------------------------------------------------------------------

TIMELINE_JUMP_MARKER_RULES = """
═══════════════════════════════════════════════════════════
⏰ TIMELINE JUMP MARKER RULES (DEC-046 v3 原则 9 — MANDATORY)
═══════════════════════════════════════════════════════════

故事 shot 之间时间跳转 / 场景切换时, **必须**在新 shot 第一帧加 caption 标识,
否则读者迷茫"现在是什么时候?"

## RULE TJR-1 — 时间跳转必标

### 触发条件 (任一)
- 与上一 shot 相比, 时间向前/向后跳 (1 小时+ 即标)
- 场景 location 切换 (室内 → 室外, 城市 → 乡村)
- POV 角色切换 (主角 → 反派 → 配角)
- 故事章节切换 (Setup → Climax 等大段位移)

### 标记格式 (短 caption, ≤15 字)
- 时间跳: "三年后" / "深夜" / "第二天清晨" / "回到那天" / "二十三年前"
- 场景跳: "酒馆里" / "回到家中" / "另一边的山顶" / "皇宫深处"
- POV 切: "另一边的林浩" / "此刻的反派" / "同时, 在城北"
- 章节切: "第二天" / "一周后" / "故事的另一端"

### 渲染位置
- text_type="narration", chinese_text=jump_marker
- speaker_position="top" 推荐 (顶部 caption, 视觉权威)

## RULE TJR-2 — 时间跳转 caption 之 12 类常用模板

| 类型 | 模板示例 | 适用 cluster |
|------|---------|-------------|
| 短时间跳 | "几分钟后。" / "一会儿后。" | 所有 |
| 中时间跳 | "三天后。" / "一周后。" | 所有 |
| 长时间跳 | "三年后。" / "二十三年后。" | C2/C5/C6 |
| 闪回过去 | "二十年前。" / "回到那天。" | 所有 |
| 闪前未来 | "(未来:) 五年后。" | C2/C6 |
| 时间标记 | "深夜十二点。" / "凌晨三点。" | C2/C8 |
| 早中晚 | "清晨。" / "傍晚。" / "深夜。" | 所有 |
| 季节 | "立春。" / "盛夏。" / "深冬。" | C1/C5/C8 |
| 节日 | "除夕夜。" / "中秋。" | C1/C5/C8 |
| 章节标 | "第一章: 相遇。" | 长篇 |
| 角色 POV 切 | "另一边——林浩。" | 所有 |
| 场景切 | "皇宫深处。" | C5 |

## RULE TJR-3 — 跨题材时间感

### C1 恋爱: 微观时间感 (那天/那晚/此刻/再见时)
- ✅ "再见面那天。"
- ✅ "他离开的第三天。"

### C2 悬疑: 精确时间感 (具体时间戳, 制造紧迫)
- ✅ "三点二十七分。"
- ✅ "案发后第 17 小时。"

### C4 童话: 模糊故事时间 (很久很久以前/那一天)
- ✅ "很久很久以前。"
- ✅ "在森林深处的一天。"

### C5 古风: 历史时间感 (年号/节气/二十四节气)
- ✅ "贞观三年, 春。"
- ✅ "立春日。"

### C6 科幻: 未来时间感 (年份/循环编号)
- ✅ "2147 年。"
- ✅ "第 47 次循环。"

## RULE TJR-4 — 跳转 caption 单独成行, 不与对话/thought 同 shot

跳转标志的"宣告性"决定了它应该独立 shot:
- ❌ shot 同时含 timeline caption + dialogue + thought (信息过载, 削弱跳转感)
- ✅ shot 只含 timeline caption + 表现新场景的 image (干净, 跳转感强)
- ✅ 下一 shot 再开始 dialogue / thought

═══════════════════════════════════════════════════════════
"""


# ----------------------------------------------------------------------------
# Module S4-4 — MULTI_CHARACTER_DIALOGUE_RULES (原则 12)
# ----------------------------------------------------------------------------

MULTI_CHARACTER_DIALOGUE_RULES = """
═══════════════════════════════════════════════════════════
👥 MULTI-CHARACTER DIALOGUE RULES (DEC-046 v3 原则 12)
═══════════════════════════════════════════════════════════

3+ 角色同场景对话, 读者必须知道**谁说哪句**. 否则气泡混乱.

## RULE MCD-1 — speaker 字段 MANDATORY

每个 dialogue_beat MUST 填 `speaker` 字段:
- speaker = character_id (如 "char_001")
- 不要留空, 不要用 "?"

## RULE MCD-2 — speaker_position 锚定气泡位置

每个 dialogue 推荐填 `speaker_position`:
- "left" — 气泡偏左, 尾巴指向画面左侧角色
- "right" — 气泡偏右, 指向右侧角色
- "center" — 气泡居中 (单角色或独白)
- "top" — 气泡偏上 (narration / 高位角色)
- "bottom" — 气泡偏下 (旁白 / 低位角色)
- "off_screen" — 角色不在画面内说话 (画外音)

## RULE MCD-3 — 多角色场景气泡顺序

按读者阅读顺序排:
- 中文/日文/韩文: 从右到左, 从上到下
- 英文/西方: 从左到右, 从上到下

序话Story 默认**从左到右 + 从上到下** (普通读者习惯).

3 个角色发言时, 推荐:
- shot 上半部分气泡 (top-left/right) = 先说话的角色
- 下半部分气泡 (bottom) = 后说话的角色

## RULE MCD-4 — 角色名字前缀 (3+ 角色 OPTIONAL)

3+ 角色时, 推荐在 dialogue line 前加角色名/称谓:
```json
{
  "type": "dialogue",
  "speaker": "char_001",
  "line": "陈砚: 「我不会去。」",
  "speaker_position": "left"
}
```
让 TextOverlayServiceV2 渲染时即使气泡尾巴指错, 读者也能从名字判断.

✅ "陈砚: 「我不去。」"
✅ "苏晨: 「你疯了!」"
✅ "妈: 「回来吃饭。」" (关系词替代 name)

## RULE MCD-5 — 画外音 (off-screen) 处理

角色不在画面内但说话:
- speaker_position = "off_screen"
- TextOverlayServiceV2 渲染时用**虚线气泡** 或 **方框** 区分
- line 末尾可加 "(画外)" 提示, 如 "妈妈: 「回来吃饭。」(画外)"

✅ 适用: 电话对话, 远处呼喊, 心理回响, 内心听到的话

## RULE MCD-6 — 多角色 cap 上限

单 shot 内 dialogue 数量上限:
- 2 个角色 → 最多 2 个 dialogue (一人一句)
- 3 个角色 → 最多 3 个 dialogue, 但 ≤2 推荐
- 4+ 角色 → 不要让所有人都说话, 选 2 个最关键角色

否则气泡密集, 读者跟不上.

═══════════════════════════════════════════════════════════
"""


# ----------------------------------------------------------------------------
# Module S4-5 — METAPHOR_SYMBOL_RULES (原则 14)
# ----------------------------------------------------------------------------

METAPHOR_SYMBOL_RULES = """
═══════════════════════════════════════════════════════════
🔮 METAPHOR & SYMBOL RULES (DEC-046 v3 原则 14)
═══════════════════════════════════════════════════════════

好故事有**象征物**承担情感. LLM 应识别故事中的象征, 在 caption 中点出
象征意义 (但不直白说破, 留半暗示).

## RULE MSR-1 — 识别故事象征物

Stage 3 ScreenplayWriter 输出的 action_beats / narration 中, 反复出现的小物
通常就是象征物:

### 常见象征清单
| 象征物 | 暗示 | 适用 cluster |
|--------|------|-------------|
| 银扣 / 旧表 / 旧物 | 时间 / 记忆 / 传承 | C1/C5/C8 |
| 红绳 / 戒指 / 项链 | 缘分 / 关系 / 承诺 | C1/C5 |
| 咖啡 / 茶 | 日常时光 / 关系温度 | C1/C8 |
| 雨 / 雪 / 风 | 情绪基调 / 时间流逝 | 所有 |
| 镜子 / 玻璃 | 自我认知 / 真相反映 | C1/C2 |
| 老照片 / 信件 | 过去 / 思念 / 秘密 | 所有 |
| 苹果 / 食物 | 给予 / 关怀 | C1/C4 |
| 剑 / 刀 / 弓 | 责任 / 杀戮 / 抉择 | C5 |
| 乌鸦 / 黑猫 / 狼 | 死亡 / 预兆 / 野性 | C2/C5 |
| 灯 / 烛 / 月亮 | 希望 / 守候 / 思念 | 所有 |

## RULE MSR-2 — 象征物在关键 shot 提示

象征物第一次出现 + 反复出现 + 最后一次出现, 这 3 个 shot 配 caption 提示:

### 第一次出现 (introduction)
- caption 客观描述 + 简短点出关键
- ✅ narration="爷爷留的银扣, 磨损纹独特。"

### 反复出现 (recurring)
- caption 可以 implicit, 不必直说
- ✅ narration="她又摸出那只银扣。" (读者已知象征意义)

### 最后一次出现 (climax)
- caption 揭示象征意义 (但留半暗示, 不直说破)
- ✅ narration="银扣, 终于和他一起还了。" (暗示传承/承诺归还)

## RULE MSR-3 — 象征物在 image_prompt 中

在 image_prompt 中, 把象征物放在**视觉显眼位置**:
- 前景 / 中央 / 高光 / 特写
- ✅ image_prompt: "桌上特写: 一只磨损的银扣, 暖黄灯光下泛着旧光"

## RULE MSR-4 — 不要过度解释象征

象征的魅力 = **不说破**. 读者自己 decode 才有快感.

❌ 过度解释:
- narration="这只银扣象征着爷爷一辈子的等待和爱。"
  → 太直白, 读者觉得说教

✅ 暗示式:
- narration="银扣还在。"
  → 读者自己 decode "二十三年, 一直在等"

## RULE MSR-5 — 象征 BY CLUSTER

### C1 (恋爱): 小物承载关系温度
- 咖啡杯 / 围巾 / 戒指 / 老照片 / 短信记录
- ✅ image: "桌上两杯凉了的咖啡" + caption="他不会再来了。"

### C2 (悬疑): 物件作线索
- 一只手套 / 一张照片 / 一封信 / 一个钥匙
- ✅ image: "雪地中的银色狼毛特写" + caption="它一直在这里。"

### C4 (童话): 物件作朋友
- 苹果 / 蓝色围巾 / 小铃铛 / 一片树叶
- ✅ image: "小熊握着一片金色枫叶" + caption="秋天的礼物。"

### C5 (古风): 物件作信物 / 兵器
- 玉佩 / 剑 / 旧书 / 酒壶 / 信物
- ✅ image: "桌上一柄出鞘的玉龙剑" + caption="此剑, 传你。"

═══════════════════════════════════════════════════════════
"""


# ----------------------------------------------------------------------------
# Module S4-6 — CULTURAL_CONTEXT_RULES (原则 15)
# ----------------------------------------------------------------------------

CULTURAL_CONTEXT_RULES = """
═══════════════════════════════════════════════════════════
🏛️ CULTURAL CONTEXT RULES (DEC-046 v3 原则 15)
═══════════════════════════════════════════════════════════

故事发生在**特定文化 / 时代 / 背景** 中. Stage 4 caption 语言应反映文化氛围.

## RULE CCR-1 — 文化氛围 BY CLUSTER

### C1 恋爱 (现代中国都市)
- 文化元素: 微信 / 朋友圈 / 奶茶 / 网课 / 加班
- caption 风格: 微信口语, 网络词适度
- ✅ "他朋友圈又没我。"
- ❌ "他于社交网络之上未提及妾身。" (过于古风)

### C2 悬疑 (现代或近现代)
- 文化元素: 监控 / 公寓 / 案件编号 / 警方 / 媒体
- caption 风格: 短句, 客观, 时间精确
- ✅ "三点二十七分, 8 号公寓。"

### C3 奇幻 (西方/东方魔幻)
- 文化元素: 龙 / 精灵 / 圣剑 / 法师塔 / 异世界
- caption 风格: 史诗感半文言半白话
- ✅ "勇者拔出圣剑。"

### C4 童话 (任意时代)
- 文化元素: 森林 / 小动物 / 苹果 / 蘑菇 / 月亮
- caption 风格: "从前 / 在很久以前 / 在森林深处"
- ✅ "在森林深处, 住着一只小熊。"

### C5 古风 (中国古代)
- 文化元素: 江湖 / 师门 / 帝王 / 节气 / 兵刃 / 茶 / 月
- caption 风格: 半文言, 用"立春/腊月/贞观/三日之约"
- ✅ "立春日, 论剑山下。"

### C6 科幻 (未来 / 赛博)
- 文化元素: AI / 太空 / 量子 / 机器人 / 数据
- caption 风格: 简洁理性, 数字 + 编号
- ✅ "2147 年, 火星基地编号 7。"

### C7 喜剧 (现代任意)
- 文化元素: 网络梗 / 表情包 / 热门话题 / 反差
- caption 风格: 网络词 + 反差 + 吐槽
- ✅ "结局: 他真的离婚了。哈哈哈。"

### C8 现实 (现代任意)
- 文化元素: 公司 / 医院 / 法院 / 学校 / 家庭
- caption 风格: 行业术语 + 通俗解释
- ✅ "他被 PIP 了 (即将被裁)。"

## RULE CCR-2 — 文化"破壁"不可

不要在错误文化背景中用错误文化词:
- ❌ 古风武侠中出现 "WiFi / 微信"
- ❌ 现代恋爱中出现 "贞观三年 / 江湖"
- ❌ 科幻中出现 "孔明灯 / 妾身" (除非有意 fusion)

## RULE CCR-3 — 中国传统文化元素优先用中文 (不翻译)

某些中国传统文化词没有准确英文翻译, image_prompt 也保留中文:
- 节气: 立春 / 谷雨 / 冬至
- 节日: 春节 / 中秋 / 端午
- 传统建筑: 飞檐 / 斗拱 / 影壁
- 传统服饰: 汉服 / 旗袍
- 这些在 image_prompt 和 caption 中**保留中文**, 不强制翻英文 (CLAUDE.md 已许)

## RULE CCR-4 — 时代标记 caption (跨题材)

故事如果跨多个时代, 必须明确标:
- "1949 年 10 月 1 日。" (历史时刻)
- "2020 年, 武汉。" (近代事件)
- "唐贞观三年。" (古代)
- "公元 2147 年。" (未来)

═══════════════════════════════════════════════════════════
"""


# ----------------------------------------------------------------------------
# COMPOSED v3 Stage 4 narrative rules block (single import for Backend)
# ----------------------------------------------------------------------------

DEC046_V3_STAGE4_RULES = (
    IMAGE_TEXT_COMPLEMENT_RULES
    + "\n"
    + MINIMAL_DIALOGUE_RULES
    + "\n"
    + TIMELINE_JUMP_MARKER_RULES
    + "\n"
    + MULTI_CHARACTER_DIALOGUE_RULES
    + "\n"
    + METAPHOR_SYMBOL_RULES
    + "\n"
    + CULTURAL_CONTEXT_RULES
)


# ----------------------------------------------------------------------------
# v3 helper getters (for tests + downstream consumers)
# ----------------------------------------------------------------------------

def get_dec046_v3_stage4_module_names() -> List[str]:
    """返回 DEC-046 v3 Stage 4 6 个新规则块的 name (用于测试).

    DEC-046 T20-28 v3.
    """
    return [
        "IMAGE_TEXT_COMPLEMENT_RULES",
        "MINIMAL_DIALOGUE_RULES",
        "TIMELINE_JUMP_MARKER_RULES",
        "MULTI_CHARACTER_DIALOGUE_RULES",
        "METAPHOR_SYMBOL_RULES",
        "CULTURAL_CONTEXT_RULES",
    ]


def get_minimal_dialogue_acceptable_examples() -> List[str]:
    """返回 v3 认可的"极简对话"白名单例 (修订旧 RULE 6 的 anti-pattern 反例).

    旧 D2/RULE 6 把 "怎么了?" "你来了" "走吧" 列为 vague reject. v3 撤销:
    在 C1/C7/C4 cluster 中这些是正确做法.
    """
    return [
        "好。", "嗯。", "走。", "回来。", "对不起。", "宝宝…",  # C1
        "别动!", "快跑!", "她…",                              # C2
        "嘿嘿。", "好甜!", "嗨呀!", "啊?", "嗯嗯!",            # C4
        "去。", "退!", "杀。", "走。",                          # C5
        "?", "??", "卧槽。", "我去!", "啊?!",                   # C7
        "嗯。", "好。", "知道了。", "再见。",                   # C8
    ]


def get_timeline_jump_marker_templates() -> dict:
    """返回 12 类时间跳转 caption 模板 (用于测试 + 下游推荐).

    DEC-046 v3 TJR-2 落地.
    """
    return {
        "short_time": ["几分钟后。", "一会儿后。"],
        "mid_time": ["三天后。", "一周后。"],
        "long_time": ["三年后。", "二十三年后。"],
        "flashback": ["二十年前。", "回到那天。"],
        "flashforward": ["(未来:) 五年后。"],
        "precise_time": ["深夜十二点。", "凌晨三点。"],
        "morning_evening": ["清晨。", "傍晚。", "深夜。"],
        "season": ["立春。", "盛夏。", "深冬。"],
        "festival": ["除夕夜。", "中秋。"],
        "chapter": ["第一章: 相遇。"],
        "pov_switch": ["另一边——林浩。"],
        "place_switch": ["皇宫深处。"],
    }


def get_symbol_common_clusters() -> dict:
    """返回常见象征物 → 暗示意义 + 适用 cluster 映射 (用于测试 + 下游).

    DEC-046 v3 MSR-1 落地.
    """
    return {
        "银扣": {"meaning": "时间/记忆/传承", "clusters": ["C1", "C5", "C8"]},
        "红绳": {"meaning": "缘分/关系/承诺", "clusters": ["C1", "C5"]},
        "戒指": {"meaning": "承诺", "clusters": ["C1", "C5"]},
        "咖啡": {"meaning": "日常时光/关系温度", "clusters": ["C1", "C8"]},
        "雨": {"meaning": "情绪基调", "clusters": ["all"]},
        "雪": {"meaning": "时间流逝/纯洁", "clusters": ["all"]},
        "镜子": {"meaning": "自我认知/真相反映", "clusters": ["C1", "C2"]},
        "老照片": {"meaning": "过去/思念", "clusters": ["all"]},
        "信件": {"meaning": "秘密/思念", "clusters": ["all"]},
        "苹果": {"meaning": "给予/关怀", "clusters": ["C1", "C4"]},
        "剑": {"meaning": "责任/抉择", "clusters": ["C5"]},
        "弓": {"meaning": "选择", "clusters": ["C5"]},
        "乌鸦": {"meaning": "死亡/预兆", "clusters": ["C2", "C5"]},
        "灯": {"meaning": "希望/守候", "clusters": ["all"]},
        "月亮": {"meaning": "思念/团圆", "clusters": ["all"]},
    }


def get_cluster_cultural_palette(cluster_id: str) -> List[str]:
    """返回某 cluster 推荐的文化元素词汇表 (用于测试 + 下游).

    DEC-046 v3 CCR-1 落地.
    """
    palettes = {
        "C1": ["微信", "朋友圈", "奶茶", "网课", "加班", "外卖", "地铁"],
        "C2": ["监控", "公寓", "案件编号", "警方", "媒体", "证据", "审讯"],
        "C3": ["龙", "精灵", "圣剑", "法师塔", "异世界", "勇者", "魔王"],
        "C4": ["森林", "小动物", "苹果", "蘑菇", "月亮", "小溪", "树洞"],
        "C5": ["江湖", "师门", "帝王", "节气", "兵刃", "茶", "月"],
        "C6": ["AI", "太空", "量子", "机器人", "数据", "克隆", "时空"],
        "C7": ["网络梗", "表情包", "热门话题", "反差", "翻车"],
        "C8": ["公司", "医院", "法院", "学校", "家庭", "学校", "银行"],
    }
    return palettes.get(cluster_id, palettes["C8"])


def validate_text_overlay_complements_image(
    image_prompt: str,
    overlay_text: str,
) -> dict:
    """heuristic 检查 text_overlay 是否**重复 image_prompt 已表达的事** (ITC-1).

    DEC-046 v3 validator. 纯函数, 无 LLM.

    Args:
        image_prompt: shot 的 image_prompt 英文
        overlay_text: text_overlay.chinese_text (string OR str(list))

    Returns:
        dict {
          "passes": bool,
          "duplicate_score": float (0-1, 越高越疑似重复),
          "issues": list[str]
        }

    Implementation: 提取 overlay 的中文 nouns/verbs, 检查是否在 image_prompt 中翻译形式出现.
    简化版: 检查 overlay 是否过于"描述画面"特征 (含 "他在", "她在", "正在" 等纯描述词).
    """
    issues: list[str] = []
    if not overlay_text or not overlay_text.strip():
        return {"passes": True, "duplicate_score": 0.0, "issues": []}

    # 简化 heuristic: 检查 overlay 是否含纯描述性 phrases
    pure_description_patterns = [
        r"^[他她它]在.{1,5}[。!?]?$",   # "他在哭。" / "她在跑。"
        r"^正在.{1,8}[。!?]?$",         # "正在哭泣。"
        r"^.{1,4}在.{1,6}[。!?]?$",      # "陈砚在哭。"
    ]
    import re
    duplicate = False
    for pat in pure_description_patterns:
        if re.match(pat, overlay_text.strip()):
            duplicate = True
            issues.append(
                f"text_overlay '{overlay_text[:30]}' looks like pure image description — "
                f"DEC-046 v3 ITC-1: text should complement image (心理/反转/因果), "
                f"not repeat what image already shows"
            )
            break

    duplicate_score = 1.0 if duplicate else 0.0
    return {
        "passes": not duplicate,
        "duplicate_score": duplicate_score,
        "issues": issues,
    }


def _strip_chinese_bilingual_segments(s: str) -> str:
    """
    清洗 "english — 中文" 双语字段，去掉中文部分。

    数据契约：Stage 2 的 characters.json 中很多字段（fur_color / clothing.top /
    distinctive_marks 等）采用 "english_description — 中文描述" 格式。CharacterPromptBuilder
    输出会把这些字段原封拼接 → 同一 string 可能含多段中文。

    本函数用正则把每段 "— [中文 + 标点 + 空格]" 替换为空，再做一次最终中文检测兜底。

    Args:
        s: 可能含双语段的字符串

    Returns:
        清洗后的字符串（理想情况下 100% 英文）
    """
    if not s:
        return ""
    import re as _re
    # 匹配 "— " 开头 + 后续含中文字符的整段，直到下一个非汉字/非中文标点/逗号边界
    # 用尽量贪婪但安全的策略：从 "—" 开始，吃掉所有汉字 + 常见中文标点 + 空白
    # 替换为 ", " 保留词边界（避免 "white" + "fine" → "whitefine"）
    pattern = _re.compile(
        r"\s*[—\-–]\s*"  # 破折号变体 + 周围空白
        r"[一-鿿　-〿＀-￯\s，。、；：'\"" + r'"' + r"".join(["'", '"']) + r"…·]+"
    )
    cleaned = pattern.sub(", ", s)
    # 兜底：移除任何残留的连续中文段（替换为 ", " 保词边界）
    cleaned = _re.sub(
        r"[一-鿿]+[一-鿿　-〿＀-￯，。、；：\s'\"" + r'"' + r"…·]*",
        ", ",
        cleaned,
    )
    # 标准化多余空白 + 连续逗号
    cleaned = _re.sub(r"\s{2,}", " ", cleaned)
    cleaned = _re.sub(r"(,\s*){2,}", ", ", cleaned)
    cleaned = cleaned.strip()
    # 去除尾部孤立的标点
    cleaned = _re.sub(r"[\s,;:\-—–]+$", "", cleaned).strip()
    # 去除首部孤立的标点
    cleaned = _re.sub(r"^[\s,;:\-—–]+", "", cleaned).strip()
    return cleaned


def _short_distinctive_marks(marks: List[str], max_marks: int = 2, max_chars_per: int = 80) -> str:
    """
    截取 distinctive_marks 列表的前 N 项，每项截断到 max_chars_per 字符。

    丢弃中文部分（用 _strip_chinese_bilingual_segments），只保留英文部分。

    Returns: "; "-joined English mark snippets, 或 空串.
    """
    if not marks or not isinstance(marks, list):
        return ""
    snippets = []
    for m in marks[:max_marks]:
        if not isinstance(m, str) or not m.strip():
            continue
        english_part = _strip_chinese_bilingual_segments(m)
        if len(english_part) > max_chars_per:
            english_part = english_part[:max_chars_per].rstrip() + "..."
        if english_part:
            snippets.append(english_part)
    return "; ".join(snippets)


def build_stage4_character_data_block(
    characters: dict,
    max_appearance_chars: int = 280,
) -> str:
    """
    构建 Stage 4 LLM 输入用的 Character data 块（含 species/character_type/appearance）。

    DEC-045 RISK-T20-17 (2026-05-19) 修复:
    旧 `_build_scene_prompt()` (storyboard_director.py L1537-1558) 给 LLM 的角色数据
    只含 {id, name, clothing_summary}，**完全没有 character_type 和 species**。当
    clothing 字段是中文被 strip 后 fallback 成 "see character reference image"，LLM
    对该角色物种零信息 → 自由发挥 → 输出 "hedgehog-like creature"（实际是 rabbit）。

    本函数修复:
    1. 加 character_type 字段（让 LLM 知道是 human / anthropomorphic_animal / robot...）
    2. 加 species 字段（让 LLM 知道是 rabbit / sparrow / fox / wolf...）
    3. 加 appearance 字段（dispatch CharacterPromptBuilder，获取专业英文外观描述）
    4. 加 distinctive_marks 字段（识别特征如"翅膀上的白纹"，物种识别关键）
    5. 保留原 name / clothing_summary（向后兼容）

    Args:
        characters: 完整的 characters dict（含 'characters' list）
        max_appearance_chars: 单个角色 appearance 字段最长字符数（控制 prompt 长度）

    Returns:
        格式化的 Character data 字符串（JSON pretty + 顶部 USAGE 提示）

    输出示例（test17 v2 灰狐故事）:
        ```
        Character data (USE THE EXACT species/character_type when writing image_prompt):
        [
          {
            "id": "char_002",
            "name": "Milly",
            "character_type": "anthropomorphic_animal",
            "species": "rabbit",
            "appearance": "A young female rabbit anthropomorphic rabbit with clean warm ivory white...",
            "distinctive_marks": "single small pale freckle-like spot on tip of left ear outer surface",
            "clothing_summary": "cream knitted vest over white long-sleeve shirt..."
          },
          ...
        ]
        ```

    设计原则:
    - Universal: 不 hardcode 故事/角色类型，dispatch 到 CharacterPromptBuilder 支持 19 类型
    - 容错: characters 缺失/字段空 → 输出空块或部分字段（不崩）
    - 英文优先: name 用 name_en，appearance 走 builder 保证全英文
    - 长度可控: appearance / clothing / marks 都有 max_chars 截断
    - 向后兼容: 保留 name + clothing_summary，新加 character_type/species/appearance/distinctive_marks
    """
    import json as _json

    chars_list = characters.get("characters", []) if isinstance(characters, dict) else []
    if not chars_list:
        return "Character data:\n[]"

    enriched = []
    for char in chars_list:
        if not isinstance(char, dict):
            continue

        char_id = char.get("id", "")
        # name_en 优先，兜底 name；如 name 含中文则用 id（防中文泄露）
        name_en = char.get("name_en") or char.get("name", "")
        if name_en and any("一" <= c <= "鿿" for c in name_en):
            name_en = char_id or "character"

        # character_type 字段（核心修复 #1）
        char_type = (char.get("character_type") or "").strip().lower() or "human"

        # 物种字段（核心修复 #2）—— 多源读取
        physical = char.get("physical", {}) if isinstance(char.get("physical"), dict) else {}
        animal_data = char.get("animal", {}) if isinstance(char.get("animal"), dict) else {}
        species = (
            physical.get("species", "")
            or animal_data.get("species", "")
            or physical.get("breed", "")
            or animal_data.get("breed", "")
            or ""
        ).strip()

        # appearance 字段（核心修复 #3）—— dispatch CharacterPromptBuilder
        appearance_raw = ""
        try:
            from app.services.character_prompt_builder import CharacterPromptBuilder
            appearance_raw = CharacterPromptBuilder().build_character_prompt(char) or ""
        except Exception:
            # 兜底：用 description 字段
            appearance_raw = char.get("description", "") or ""
        # 清洗：去掉 "english — 中文" 模式中的中文段（CharacterPromptBuilder 输出
        # 跨字段拼接，会保留 Stage 2 双语字段中的中文部分）
        appearance = _strip_chinese_bilingual_segments(appearance_raw)
        # 长度截断
        if appearance and len(appearance) > max_appearance_chars:
            appearance = appearance[:max_appearance_chars].rstrip() + "..."

        # distinctive_marks 字段（核心修复 #4）
        marks_raw = physical.get("distinctive_marks", []) or animal_data.get("distinctive_marks", []) or []
        distinctive_marks = _short_distinctive_marks(marks_raw, max_marks=2, max_chars_per=80)

        # clothing_summary 字段（向后兼容）—— 从 clothing.top + bottom 拼装英文部分
        clothing = char.get("clothing", {}) if isinstance(char.get("clothing"), dict) else {}
        top_raw = clothing.get("top", "") or ""
        bottom_raw = clothing.get("bottom", "") or ""
        # 取英文部分（清洗中文）
        top_en = _strip_chinese_bilingual_segments(top_raw)
        bottom_en = _strip_chinese_bilingual_segments(bottom_raw)
        clothing_parts = [p for p in [top_en, bottom_en] if p]
        clothing_summary = ", ".join(clothing_parts) if clothing_parts else "see character reference image"

        entry = {
            "id": char_id,
            "name": name_en,
            "character_type": char_type,
            "clothing_summary": clothing_summary,
        }
        # species 只对 anthropomorphic / animal 类型有意义，但即使 human 留空也无害
        if species:
            entry["species"] = species
        if appearance:
            entry["appearance"] = appearance
        if distinctive_marks:
            entry["distinctive_marks"] = distinctive_marks

        enriched.append(entry)

    block = _json.dumps(enriched, ensure_ascii=False, indent=2)
    return (
        "Character data "
        "(USE THE EXACT species/character_type when writing image_prompt — see SPECIES FIDELITY RULES):\n"
        + block
    )


# ============================================================================
# 字段语义约定 / 数据契约说明（D3, 2026-05-12）
# ============================================================================
#
# Stage 4 LLM 输出的 shot.composition 字段（foreground / background / midground / depth_layers
# / leading_lines / negative_space / subject_position / eye_line_direction）的语义是：
#   "供人类导演 + 图像生成模型阅读的构图描述句"
# 而 NOT：
#   "可被脚本逐字符匹配的离散道具名"
#
# 实际 LLM 在这些字段写的是 90-366 字符的描述句，例如:
#   foreground = "blurred edge of a monitor screen corner in the extreme near foreground,
#                 casting a cold blue-white glow"
#   background = "the nurse station counter extending to the right, a second nurse —
#                 a colleague — leaning in from the right third of the frame, ..."
#
# ⚠️ 后置 ShotValidator (T28) 把这些字段当作 key_props 严格匹配会大量误判（test13 实测 11%）。
# 正确做法：
#   1. 后置验证（ShotValidator）已在内部做净化（D3-A）+ lenient prompt（D3-B）+ 阈值放宽（D3-C）
#      支持把这两字段安全地传入而不误判
#   2. 未来如需"真正离散道具检测"，应让 Stage 4 LLM 显式输出新字段 `narrative_props: ["phone",
#      "monitor", "passport"]`（短名词列表），而 NOT 复用 composition.foreground/background
#   3. pipeline_orchestrator.py:1073-1080 的 `for field in [foreground/background/key_object]`
#      提取逻辑保持不变（ShotValidator 内部已防御），但下次重构时可考虑改读 narrative_props
#
# 详见: .team-brain/analysis/T17_VALIDATOR_FIX_ANALYSIS.md
# ============================================================================

COMPOSITION_FIELD_SEMANTICS_NOTE = """
NOTE FOR DATA-CONTRACT MAINTAINERS (this constant is documentation, not LLM-prompt):

shot.composition.foreground / background / midground are DESCRIPTIVE PHRASES
(written for human + image-model consumption), NOT discrete prop names.
They typically contain 60-300 chars with spatial framing language.

Do NOT write code that does strict string matching against these fields
(e.g. "is X visible?" → false → fail). For visibility checks, either:
- Use ShotValidator with sanitization+lenient prompt (recommended), or
- Add a new explicit `narrative_props: list[str]` field to the Stage 4
  LLM schema with discrete short noun phrases.
"""

# ============================================================================
# Stage 4 Prompt增强：条漫模式叙事自足规则
# ============================================================================

COMIC_MODE_NARRATIVE_RULES = """
═══════════════════════════════════════════════════════════
COMIC MODE: DEC-044 FINAL FORM — NO TTS / NO VOICEOVER (MANDATORY)
═══════════════════════════════════════════════════════════

🚨 PRODUCT FINAL FORM (DEC-044, 2026-05-19):
The output is *shots + BGM ONLY*. There is **NO TTS narration voiceover**.
Readers will ONLY see:
  1. The shot image
  2. Speech bubbles (dialogue)
  3. Thought bubbles (inner monologue)
  4. Short on-image captions (narration text_type, ≤25 Chinese chars)

If a reader cannot understand "what happened in this shot, who said what,
what they are thinking, what just changed" by looking at the image + visible
text overlays ALONE, the shot is BROKEN. The story is universally felt as
"vague / hard to follow / lacking" — this is a P0 product quality bug.

═══════════════════════════════════════════════════════════

## RULE 0 (DEC-044 + DEC-045 T20-27 — v2 STRENGTHENED 2026-05-19): NO EMPTY TEXT OVERLAY
- text_type="none" is FORBIDDEN except for purely environmental establishing
  shots with ZERO characters (e.g. wide landscape, abstract montage transition).
- Every character-bearing shot MUST carry text_overlay with text_type in
  {dialogue, thought, narration, dialogue_with_thought, dialogue_with_narration,
  narration_with_thought, narration_with_dialogue}.
- text_overlay.chinese_text MUST be a NON-EMPTY string OR a NON-EMPTY list of
  non-empty strings. Setting `"chinese_text": ""` or `"chinese_text": []` or
  `"chinese_text": null` or omitting the field entirely is FORBIDDEN.
- If you set text_type="none" on a shot with characters_in_scene != [], you are
  WRONG. Re-check the scene's dialogue_beats or generate a thought from the
  beat's emotional_note.

## RULE 0.B (DEC-045 T20-27 NEW 2026-05-19) — CRITICAL TURN SHOTS REQUIRE TEXT OVERLAY EMPHASIS

test19 实证: Shot 13 (关键转折 "墓碑上刻着陈砚, 生卒年空白") 的 text_overlay 字段空,
只有 19 字 narration caption 在顶部. 读者错过故事最大反转 (主角看到自己名字在墓碑上).

### MANDATORY: For "critical turn" shots (key story beats), text_overlay must be NON-OPTIONAL.

A shot is a "critical turn" if ANY of these are true:
  - The associated action_beat's `beat_id` or `narrative_role` contains:
    `climax` / `twist` / `reveal` / `turning_point` / `crisis` / `discovery` /
    `recognition` / `betrayal` / `awakening` / `death` / `birth` / `confession`
  - The scene's `plot_point` field marks this beat as the scene's pivot
  - The associated action_beat's `emotional_note` contains strong reveal words:
    "震惊" / "崩溃" / "顿悟" / "认出" / "发现真相" / "揭露" / "意识到" / "突然明白"
  - The shot's image_prompt describes a discovery / revealing of named clue:
    "墓碑上的名字" / "信件内容" / "照片中的人" / "镜子中的另一张脸" / "藏在抽屉里的物件"
  - The scene's `narration` field contains a concrete plot-bomb fact that the
    image alone cannot convey (e.g. "碑上刻着陈砚, 生卒年空白")

### MANDATORY when critical turn detected:
1. text_type MUST be one of: `dialogue` / `thought` / `narration` /
   `dialogue_with_thought` / `narration_with_thought` (mixed types preferred
   for maximum reader comprehension)
2. chinese_text MUST contain the concrete revealing fact in plain Chinese:
   - The named clue / number / name / discovery
   - The character's emotional reaction to it
3. chinese_text MUST be ≤35 chars per line (per RULE 6)

### CRITICAL TURN EXAMPLES (test19 灰狐 / 独眼鸦 — what should have happened):

#### test19 Shot 13 (碑上陈砚名字 — 真正 P0 反转 BUG)
❌ ACTUAL (test19): text_overlay=None, only 19-char top caption
✅ SHOULD BE:
```json
"text_overlay": {
  "text_type": "narration_with_thought",
  "chinese_text": ["碑上刻着：陈砚。生卒年空白。", "（这……这是我的名字。）"],
  "speaker_position": "bottom"
}
```

#### Shot 15 (照片里两张相同的脸 — reveal of resemblance)
✅ SHOULD BE:
```json
"text_overlay": {
  "text_type": "dialogue_with_thought",
  "chinese_text": ["陈砚：「爷爷……是你吗？」", "（他的脸和我的脸——一模一样。）"],
  "speaker_position": "bottom"
}
```

#### 任意"震惊认出"reveal shot:
✅ thought_only: `chinese_text=["（他居然把房子卖了……）"]` (concrete: who did what)

### SELF-CHECK BEFORE OUTPUT (RULE 0 + 0.B):
For EVERY shot in the output:
  □ Does this shot have characters_in_scene != []?
    YES → text_overlay MUST be present + non-empty
  □ Is this a critical turn (climax/twist/reveal/recognition/discovery)?
    YES → text_overlay MUST contain the concrete revealing fact
  □ Is chinese_text non-empty (string len ≥1 OR list with ≥1 non-empty string)?
    YES → OK; NO → REWRITE
  □ Is the reveal explicit (named clue / number / decision in chinese_text)?
    YES → OK; NO → ADD the concrete fact

If any check fails → REWRITE the text_overlay before finalizing the shot output.

## RULE 1: SELF-CONTAINED CONTEXT (STRENGTHENED)
Every shot's visible text MUST contain enough information for readers to
understand the story WITHOUT any voiceover. Use SPECIFIC NOUNS, NUMBERS,
NAMES, ACTIONS — not vague feelings.

BAD:  thought="（怎么会这样……）" (vague — readers don't know what happened)
GOOD: thought="（他居然把房子卖了……）" (specific — readers understand)

BAD:  thought="（这里有东西。）" (vague — what thing?)
GOOD: thought="（雪下藏着……一缕银色狼毛。）" (specific noun: 银色狼毛)

BAD:  dialogue="灰狐：「又是一年。」" (poetic but readers don't know what year/event)
GOOD: dialogue="灰狐：「二十三年了，每年立春一颗苹果。」" (concrete numbers + ritual)

## RULE 2: TRANSITION SHOTS — ESTABLISH NEW CONTEXT
When a scene/location/time changes between shots, the FIRST shot in the new
context MUST establish via dialogue/thought/caption:
- WHERE we are now (if location changed) — name the place
- WHEN this is happening (if time jumped) — name the time-marker
- WHY we are here (narrative connection) — link to previous shot's event

Example: After a fight scene → cut to character alone at night →
thought="（刚才那句话太重了……我把妈妈推哭了。）" (bridges + names what)

## RULE 3: NARRATION CAPTION RULE (NEW, DEC-044) — CRITICAL
When you use text_type="narration", the chinese_text field is rendered as an
ON-IMAGE SHORT CAPTION (white-on-black bar at top/bottom of the panel) —
NOT a TTS-read literary paragraph.

### LENGTH HARD LIMIT:
- chinese_text for narration: **≤25 Chinese chars** (single-line readable)
- Mixed types (narration_with_thought etc.): narration sub-part ≤25 chars
- If your scene's prose narration is 200-400 chars, **distill** it down — pick
  the ONE most plot-revealing fact and write it as a caption.

### DISTILLATION EXAMPLES (from test17 v2 灰狐故事):

❌ BAD (raw prose dumped — unreadable as caption):
   narration="立春的清晨，深山雪林还未完全苏醒。白桦树的枝丫挂着昨夜最后一层薄霜，
   晨光从林梢斜斜透入，将雪地染成淡蓝与银白交织的颜色..." (122 chars, unreadable)

✅ GOOD (distilled to one plot-revealing line):
   narration="立春清晨，灰狐独自踏雪赴一场年年之约。" (19 chars, sets scene + ritual)

❌ BAD: narration="那棵白桦树高大而沉默，树皮白得近乎透明，在晨光里散发着一种古老的光泽。灰狐在树前停下来，跪下去..." (135 chars)
✅ GOOD: narration="树皮上，二十三道划痕。" (11 chars, exposes key clue)

❌ BAD: narration="果果凑过来，探头一看，随即轻轻捧起了那截从雪中显露的银色狼毛。那毛保存得出奇完好..." (long prose)
✅ GOOD: narration="雪下，一缕银色狼毛。" (10 chars, names the discovery)

## RULE 4: PLOT-INFORMATION DISPLACEMENT (NEW, DEC-044)
If critical plot information exists in the scene's prose `narration` field but
is NOT visible in any shot's dialogue/thought/caption text_overlay, you MUST
move that information into a visible text element. The reader is BLIND to
prose narration.

### WHAT COUNTS AS CRITICAL PLOT INFORMATION:
- Concrete numbers (23 years, 8 dishes, 100 yuan)
- Named objects/clues revealed (silver wolf hair, the will, the ring)
- Time-jump markers (one year later, the next morning)
- Cause-effect statements (she died, he sold the house)
- Relationship reveals (this is her son, she is the wolf's mate)

### MAPPING WORKFLOW:
For each shot, before finalizing text_overlay:
  1. Look at the scene's `narration` field
  2. Extract any concrete plot facts (numbers, named things, reveals)
  3. Check: are these facts visible in this shot's image OR in this shot's
     text_overlay (dialogue/thought/caption)?
  4. If NO — distill into a short caption (narration text_type) OR a thought
     bubble OR a dialogue line. Pick whichever fits the moment best.

## RULE 5: TEXT DENSITY PER SHOT (NEW, DEC-044)
- 1-2 dialogue bubbles per shot (readable, not crowded)
- OR 1 thought bubble (≤25 chars)
- OR 1 narration caption (≤25 chars)
- OR 1 dialogue + 1 thought (mixed type, 2 elements max for readability)
- AVOID stacking 3+ text elements in one shot (overcrowds the panel)

## RULE 6: BUBBLE LINE LENGTH (v2 UPDATED — DEC-045 T20-21 v2, 2026-05-19)
- dialogue/thought line: **≤35 Chinese chars** per bubble (was ≤25 → ≤35)
  Why: test19 实证 (Founder /preview 反馈) 24-char dialogue 偏短不直观, 通俗性差.
  Reader needs more concrete plot information per bubble.
- Target sweet spot: **18-30 chars per bubble** (one-line readable + plot-dense)
- Hard cap: 35 chars per bubble (do NOT exceed)
- If a dialogue beat from screenplay is longer than 35, split into 2 bubbles
  in the same shot (text_type="dialogue", chinese_text=[line1, line2])

### Examples of v2 target lengths:
✅ "陈砚……是你吗？爷爷又见到你了。" (16 chars) — concrete + emotional
✅ "二十三年了，每年立春我都来替她还心愿。" (19 chars) — concrete + timestamped
✅ "妈妈，我考公考了七次，没考上不能怪你呀。" (20 chars) — concrete decision
✅ "陈砚……你长得跟他一模一样，难道是他在你身上重生？" (24 chars) — concrete + reveal

❌ AVOID overly terse (feels fragmentary):
❌ "怎么了？" (4 chars — vague, lazy)
❌ "你来了" (3 chars — no concrete information)

## RULE 7: PLAIN-LANGUAGE READABILITY (v2 NEW — DEC-045 T20-21 v2, 2026-05-19)

test19 实证 Founder /preview 反馈: "对话气泡/心理描述/旁白文字过于简短不直观通俗易懂".
Stage 4 必须确保 Stage 3 ScreenplayWriter 输出的 dialogue/thought/narration 用
**日常口语** (daily spoken Chinese), 不用文言/晦涩/书面语.

### MANDATORY: Use DAILY SPOKEN CHINESE in text_overlay
Reader's average reading level = popular short-video viewer, NOT classical
Chinese literature scholar. Dialogue should sound like a real person speaking
aloud right now, NOT a poem / sutra / classical prose.

### FORBIDDEN classical / literary / esoteric vocabulary:

| ❌ Classical/Esoteric | ✅ Daily Spoken Replacement |
|------------------------|-----------------------------|
| 咒 / 七声咒 | 哀鸣 / 7 声叫 |
| 夙愿 / 夙恨 | 心愿 / 旧恨 |
| 亘古 / 旷古 | 自古以来 / 多少年 |
| 殒命 / 仙逝 | 死了 / 去世 |
| 命数 / 天命 | 命运 |
| 须臾 / 刹那 | 一下子 / 转眼 |
| 涕泗横流 | 哭得稀里哗啦 |
| 黯然神伤 | 难过 / 心里发酸 |
| 与子偕老 | 跟你一起到老 |

### EXCEPTIONS (allowed):
- Character explicitly classical scholar / monk / poet
- Deliberate poem / ritual chant (action_beats says so)
- Proper nouns (character name, ritual name, location)

### If Stage 3 output uses classical vocabulary that doesn't fit an exception,
Stage 4 SHOULD lightly rewrite chinese_text to plain spoken form when writing
text_overlay.chinese_text. Stage 4 has authority to swap "夙愿" → "心愿" if it
preserves the same meaning + sounds more natural for a comic panel reader.

═══════════════════════════════════════════════════════════
DEC-044 SELF-CHECK BEFORE EACH SHOT OUTPUT:
  □ text_type ≠ "none" (unless purely environmental, characters_in_scene=[])
  □ If narration: chinese_text ≤25 Chinese chars (caption, not prose)
  □ Concrete plot info (numbers/names/reveals) visible somewhere in text
  □ Transition shots establish new where/when/why
  □ Speaker visibility: dialogue speakers in characters_visible
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

    DEC-043 RISK-T20-10 (2026-05-19):
    - human → 原 hardcoded "Asian woman/man + face_shape + East Asian" 路径 (不动)
    - 非 human → dispatch CharacterPromptBuilder.build_character_prompt() (19 类型完整支持)
      解决 anthropomorphic_animal / animal / robot / fantasy_creature 等
      被误描述为 "young Asian woman/man" 的 P0 问题

    输出示例（human）：
    "young East Asian man, oval face, fair skin, dark brown almond eyes,
     short black hair with side part, rectangular silver-framed glasses,
     gray casual button-up shirt, black slim jeans"
    """
    # T20-10: 非 human 类型走通用 builder
    char_type = (character.get('character_type') or 'human').strip().lower()
    if char_type and char_type != 'human':
        try:
            from app.services.character_prompt_builder import CharacterPromptBuilder
            return CharacterPromptBuilder().build_character_prompt(character)
        except Exception:
            desc = character.get('description', '') or character.get('extra_details', '')
            if desc:
                return desc
            return f"a {char_type} character"

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
