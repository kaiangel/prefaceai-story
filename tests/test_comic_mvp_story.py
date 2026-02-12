"""
条漫MVP故事测试脚本
测试 gemini-2.5-flash-image 的文字内嵌能力

参考案例: still_image_storyref/IMG_0804-0818.jpg (15张都市情感条漫)
Prompt模板: docs/COMIC_MVP_PROMPT_TEMPLATES.md
验收标准: docs/COMIC_MVP_TEST_ACCEPTANCE_CRITERIA.md

作者: @Backend
日期: 2026-01-22
任务: HANDOFF-2026-01-22-003
修改: @Tester 2026-01-22 - 修复图像生成API调用方式，使用项目的ImageGenerator服务
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.image_generator import ImageGenerator
from app.services.style_enforcer import StyleEnforcer

# =============================================================================
# 配置
# =============================================================================

GEMINI_MODEL = "gemini-2.5-flash-image"  # Flash模型，用于测试文字内嵌能力
USE_PRO_MODEL = False  # 条漫MVP测试先用Flash，降低成本
OUTPUT_DIR = Path(__file__).parent.parent / "test_output" / "comic_mvp_test"
REFERENCE_DIR = Path(__file__).parent.parent / "still_image_storyref"

# =============================================================================
# 角色定义 (基于验收标准中的角色设定)
# =============================================================================

CHARACTERS = {
    "female_lead": {
        "name": "女主",
        "name_en": "Female Lead",
        "physical": "young woman in her mid-20s with red-brown wavy long hair reaching past shoulders, small mole on left cheek, elegant willow-leaf eyebrows, fair porcelain skin, delicate oval face, expressive almond eyes",
        "clothing": "light blue soft cardigan over white camisole, elegant pearl necklace, carrying a small crossbody bag"
    },
    "male_lead": {
        "name": "男主",
        "name_en": "Male Lead",
        "physical": "young man in his mid-20s with black slightly messy short hair, sharp sword eyebrows, warm brown eyes, handsome defined face with gentle features",
        "clothing": "dark blue casual jacket over gray crew neck shirt, blue jeans"
    },
    "ex_boyfriend": {
        "name": "前任",
        "name_en": "Ex-boyfriend",
        "physical": "young man with dark brown long hair past ears, silver earring in left ear, cold sharp eyes with distant gaze, chiseled jawline, aloof intimidating expression",
        "clothing": "dark burgundy shirt with collar, mysterious dark atmosphere"
    }
}

# =============================================================================
# 风格前缀 (illustration风格)
# =============================================================================

STYLE_PREFIX = """
═══════════════════════════════════════════════════════════
MANDATORY STYLE REQUIREMENT - DO NOT IGNORE THIS SECTION
═══════════════════════════════════════════════════════════
STYLE: Korean Webtoon / Chinese Manhua Illustration

MUST INCLUDE: digital illustration, webtoon style, soft pastel colors, clean defined lines,
detailed expressive faces, manhwa aesthetic, romantic comic style, beautiful character designs

DO NOT USE: photorealistic, photograph, 3D render, anime chibi, pixel art,
abstract, sketch, watercolor, oil painting

This is a romantic urban webtoon. Characters should be beautifully drawn with
detailed expressions and emotions. Background should be soft and atmospheric.
═══════════════════════════════════════════════════════════

"""

# =============================================================================
# Prompt模板函数 (基于 COMIC_MVP_PROMPT_TEMPLATES.md)
# =============================================================================

def build_speech_bubble_prompt(scene_desc: str, speaker: str, dialogue: str, bubble_position: str = "upper right") -> str:
    """对话气泡模板"""
    return f"""{scene_desc}

TEXT OVERLAY REQUIREMENT:
A white rounded rectangular speech bubble with a pointed tail directed at {speaker}.
Inside the bubble, display Chinese text '{dialogue}' in black font, centered alignment.
The bubble should be positioned {bubble_position} in the frame, with the tail pointing toward the speaker's mouth.

Speech bubble style: clean white fill, thin black outline (1-2px), rounded corners (radius ~15px),
triangular tail pointing to speaker. Text should be clearly legible against white background."""


def build_black_monologue_prompt(scene_desc: str, monologue: str, bar_position: str = "at the bottom", bar_height: str = "18%") -> str:
    """心理旁白 - 黑底白字模板"""
    return f"""{scene_desc}

TEXT OVERLAY REQUIREMENT:
A semi-transparent black bar ({bar_position}) spanning the full width of the image, height approximately {bar_height} of frame.
Display Chinese text '{monologue}' in white font, centered alignment.
The black overlay should have approximately 70-80% opacity, allowing slight visibility of background.

Inner monologue style: represents character's private thoughts, contemplative mood."""


def build_white_narrative_prompt(scene_desc: str, narrative: str, bar_position: str = "at the top", bar_height: str = "15%") -> str:
    """叙事旁白 - 白底黑字模板"""
    return f"""{scene_desc}

TEXT OVERLAY REQUIREMENT:
A semi-transparent white/cream colored bar ({bar_position}) spanning the full width of the image, height approximately {bar_height} of frame.
Display Chinese text '{narrative}' in black font, centered alignment.
The white overlay should have approximately 80-85% opacity with soft edges.

Narrative caption style: objective narration, establishes context or provides insight."""


def build_split_screen_prompt(left_scene: str, left_emotion: str, right_scene: str, right_emotion: str, narrative_purpose: str) -> str:
    """分屏效果模板"""
    return f"""SPLIT SCREEN COMPOSITION:

LEFT HALF: {left_scene}
The left character shows {left_emotion} expression.

RIGHT HALF: {right_scene}
The right character shows {right_emotion} expression.

Visual style: Clear vertical division down the center of the image.
Sharp clean line separating the two scenes.
Both halves should have similar lighting style for visual coherence while showing contrasting content.

Split screen purpose: {narrative_purpose}"""


def build_memory_fragment_prompt(main_char_desc: str, fragments: list, emotional_tone: str) -> str:
    """回忆碎片效果模板"""
    fragment_lines = "\n".join([f"Fragment {i+1}: {f}" for i, f in enumerate(fragments)])
    return f"""{main_char_desc}

MEMORY FRAGMENT EFFECT:
Surrounding the main character, floating memory fragments showing glimpses of the past.
Fragment shapes: jagged glass shards with glowing edges
Number of visible fragments: {len(fragments)}

Fragment contents:
{fragment_lines}

Fragment visual treatment: slightly desaturated colors, soft ethereal glow at edges, dreamlike quality

The fragments should appear to float in space around the character, creating a dreamlike, nostalgic atmosphere.
Main character remains in sharp focus while fragments have soft blur and slight transparency.

Emotional tone: {emotional_tone}"""


def build_picture_in_picture_prompt(main_scene: str, device_type: str, pip_content: str, device_position: str = "center of frame", device_size: str = "40%") -> str:
    """画中画效果模板"""
    return f"""{main_scene}

PICTURE-IN-PICTURE ELEMENT:
{device_type} showing: {pip_content}

Device details:
- Position: {device_position}
- Size: approximately {device_size} of frame
- Screen content clearly visible and in focus
- Modern smartphone with thin black bezels, slight screen reflection visible

The embedded screen should show {pip_content} with realistic device frame and subtle screen glow.

Visual relationship: viewer sees both the holder's reaction and the screen content, creating emotional connection."""


def get_character_desc(char_id: str) -> str:
    """获取角色完整描述"""
    char = CHARACTERS.get(char_id)
    if not char:
        return ""
    return f"{char['physical']}, {char['clothing']}"


def get_emotion_desc(emotion_key: str) -> str:
    """获取表情描述 (基于表情词库)"""
    emotions = {
        "displeased": "furrowed brows, slightly narrowed eyes, tight-lipped, jaw slightly clenched",
        "hurt": "glistening eyes almost teary, slightly trembling lower lip, brows drawn together and upward, pained expression",
        "confused": "raised eyebrows one higher than other, tilted head, squinted eyes, slightly open mouth, questioning gaze",
        "apologetic": "lowered gaze, bowed head slightly, softened eyes, pressed lips, humble posture",
        "shocked": "wide eyes, raised eyebrows high, open mouth jaw dropped, frozen expression, dilated pupils",
        "indifferent": "neutral flat expression, half-lidded eyes, relaxed facial muscles, distant gaze, emotionally guarded",
        "relieved": "soft gentle smile, relaxed brows, warm eyes, tension released from face, serene expression",
        "happy": "genuine smile reaching eyes with crow's feet, raised cheeks, bright sparkling eyes, visible teeth in smile"
    }
    return emotions.get(emotion_key, emotion_key)


# =============================================================================
# 15张测试用例定义 (基于参考图 804-818)
# =============================================================================

STORY_SHOTS = [
    # Shot 1 - IMG_0804: 对话气泡 + 顶部黑底旁白
    {
        "shot_id": 1,
        "ref_image": "IMG_0804",
        "prompt_type": "speech_bubble_with_top_monologue",
        "scene": "urban street at dusk, city buildings in background, warm evening light",
        "characters": ["female_lead", "male_lead"],
        "female_emotion": "displeased",
        "male_emotion": "confused",
        "dialogue": "你说句话呀宝宝…",
        "dialogue_speaker": "male_lead",
        "monologue": "那天和男朋友逛街，让他帮我拍照，拍了好多张没一张能看的！！！",
        "monologue_position": "at the top"
    },
    # Shot 2 - IMG_0805: 底部黑底旁白 + 问号符号
    {
        "shot_id": 2,
        "ref_image": "IMG_0805",
        "prompt_type": "black_monologue_with_emotion_symbol",
        "scene": "same street scene, close-up two shot",
        "characters": ["female_lead", "male_lead"],
        "female_emotion": "hurt",
        "male_emotion": "confused",
        "monologue": "他完全不理解我为什么生气...",
        "monologue_position": "at the bottom",
        "emotion_symbol": "question marks floating near male character's head"
    },
    # Shot 3 - IMG_0806: 顶部+底部黑底旁白
    {
        "shot_id": 3,
        "ref_image": "IMG_0806",
        "prompt_type": "dual_monologue",
        "scene": "street corner, evening atmosphere",
        "characters": ["female_lead"],
        "female_emotion": "indifferent",
        "top_monologue": "我选择了沉默",
        "bottom_monologue": "用冷漠回应他的关心"
    },
    # Shot 4 - IMG_0807: 对话气泡 + 底部黑底旁白
    {
        "shot_id": 4,
        "ref_image": "IMG_0807",
        "prompt_type": "speech_bubble_with_bottom_monologue",
        "scene": "street scene, male character looking worried",
        "characters": ["female_lead", "male_lead"],
        "female_emotion": "indifferent",
        "male_emotion": "apologetic",
        "dialogue": "你到底怎么了？跟我说说好不好？",
        "dialogue_speaker": "male_lead",
        "monologue": "他越是追问，我越不想回答"
    },
    # Shot 5 - IMG_0808: 对话气泡 + 汗滴符号
    {
        "shot_id": 5,
        "ref_image": "IMG_0808",
        "prompt_type": "speech_bubble_with_sweat_drop",
        "scene": "street scene, male character pleading",
        "characters": ["male_lead"],
        "male_emotion": "apologetic",
        "dialogue": "对不起对不起！我下次一定好好拍！",
        "emotion_symbol": "sweat drops near head, hands pressed together in apologetic gesture"
    },
    # Shot 6 - IMG_0809: 回忆碎片效果 ⭐ 重点测试
    {
        "shot_id": 6,
        "ref_image": "IMG_0809",
        "prompt_type": "memory_fragments",
        "scene": "female lead standing alone, dark atmospheric background with soft lights",
        "characters": ["female_lead"],
        "female_emotion": "shocked",
        "monologue": "这一幕我突然觉得似曾相识。",
        "fragments": [
            "A couple arguing, the man looking away coldly",
            "A woman sitting alone crying at night",
            "Two people walking separately on a street",
            "A man's cold indifferent face in shadow"
        ],
        "emotional_tone": "déjà vu, haunting realization, painful memories surfacing"
    },
    # Shot 7 - IMG_0810: 左侧黑底旁白
    {
        "shot_id": 7,
        "ref_image": "IMG_0810",
        "prompt_type": "side_monologue",
        "scene": "female lead alone in contemplation, moody lighting",
        "characters": ["female_lead"],
        "female_emotion": "shocked",
        "monologue": "以前那段感情里，我也是这样被对待的...",
        "monologue_position": "left side vertical"
    },
    # Shot 8 - IMG_0811: 分屏效果 ⭐ 重点测试
    {
        "shot_id": 8,
        "ref_image": "IMG_0811",
        "prompt_type": "split_screen",
        "left_scene": f"Female lead ({get_character_desc('female_lead')}) with cold distant expression, gray-blue color tone",
        "left_emotion": "indifferent, aloof, emotionally closed off",
        "right_scene": f"Ex-boyfriend ({get_character_desc('ex_boyfriend')}) with cold intimidating gaze, dark red moody lighting",
        "right_emotion": "cold, dismissive, emotionally unavailable",
        "narrative_purpose": "showing how female lead has become like her ex, using silence as weapon",
        "center_monologue": "可是现在，我发现我越来越像他了。我仗着对方的紧张和在意，堂而皇之的关闭了自己的沟通渠道。"
    },
    # Shot 9 - IMG_0812: 对话气泡×2 + 黑底旁白
    {
        "shot_id": 9,
        "ref_image": "IMG_0812",
        "prompt_type": "multiple_speech_bubbles",
        "scene": "couple facing each other, female lead starting to open up",
        "characters": ["female_lead", "male_lead"],
        "female_emotion": "relieved",
        "male_emotion": "attentive",
        "dialogues": [
            {"speaker": "female_lead", "text": "其实...我只是想让你认真对待", "position": "upper left"},
            {"speaker": "male_lead", "text": "我懂了，以后我会用心的", "position": "upper right"}
        ],
        "monologue": "我终于开口说出了心里话"
    },
    # Shot 10 - IMG_0813: 大对话气泡
    {
        "shot_id": 10,
        "ref_image": "IMG_0813",
        "prompt_type": "large_speech_bubble",
        "scene": "close-up of female lead speaking earnestly",
        "characters": ["female_lead"],
        "female_emotion": "relieved",
        "dialogue": "我不想用沉默来惩罚你，那样只会让我们都难受",
        "bubble_size": "large, taking up significant portion of frame"
    },
    # Shot 11 - IMG_0814: 标准对话气泡
    {
        "shot_id": 11,
        "ref_image": "IMG_0814",
        "prompt_type": "speech_bubble",
        "scene": "male lead responding with gentle smile",
        "characters": ["male_lead"],
        "male_emotion": "happy",
        "dialogue": "谢谢你愿意告诉我",
        "bubble_position": "upper center"
    },
    # Shot 12 - IMG_0815: 画中画（手机）+ 对话气泡 ⭐ 重点测试
    {
        "shot_id": 12,
        "ref_image": "IMG_0815",
        "prompt_type": "picture_in_picture_with_bubble",
        "scene": "male lead holding phone, taking photo of female lead who is smiling happily",
        "characters": ["female_lead", "male_lead"],
        "female_emotion": "happy",
        "male_emotion": "happy",
        "dialogue": "好。",
        "pip_content": "the phone screen showing female lead's smiling face being photographed, beautiful composition",
        "device_type": "smartphone held by male lead"
    },
    # Shot 13 - IMG_0816: 画中画 + 底部白底旁白 ⭐ 重点测试
    {
        "shot_id": 13,
        "ref_image": "IMG_0816",
        "prompt_type": "picture_in_picture_with_white_narrative",
        "scene": "couple taking selfie together, close intimate framing, warm lighting",
        "characters": ["female_lead", "male_lead"],
        "female_emotion": "happy",
        "male_emotion": "happy",
        "pip_content": "phone screen showing their happy selfie together, both smiling warmly",
        "device_type": "smartphone held showing camera app",
        "narrative": "想起了一句话：请不要默默在心里给他扣分，这样真的很不公平。",
        "narrative_position": "at the bottom"
    },
    # Shot 14 - IMG_0817: 顶部白底旁白 ⭐ 重点测试
    {
        "shot_id": 14,
        "ref_image": "IMG_0817",
        "prompt_type": "white_narrative_top",
        "scene": "couple walking away together hand in hand on a lamplit street at evening, seen from behind, romantic atmosphere",
        "characters": ["female_lead", "male_lead"],
        "narrative": "如果我爱你，就一定会尽可能告诉你，我为什么生气，要学会大大方方的表达爱意。",
        "narrative_position": "at the top"
    },
    # Shot 15 - IMG_0818: 中部白底旁白
    {
        "shot_id": 15,
        "ref_image": "IMG_0818",
        "prompt_type": "white_narrative_center",
        "scene": "warm ending shot, couple silhouette against sunset/evening sky, hopeful atmosphere",
        "characters": ["female_lead", "male_lead"],
        "narrative": "爱情里，沟通永远比沉默更有力量。",
        "narrative_position": "center of frame"
    }
]


# =============================================================================
# Prompt构建器
# =============================================================================

def build_full_prompt(shot: dict) -> str:
    """根据shot定义构建完整prompt"""

    prompt_type = shot.get("prompt_type", "")
    parts = [STYLE_PREFIX]

    # 构建角色描述
    char_descs = []
    for char_id in shot.get("characters", []):
        char = CHARACTERS.get(char_id)
        if char:
            emotion_key = shot.get(f"{char_id.split('_')[0]}_emotion", "")
            emotion_desc = get_emotion_desc(emotion_key) if emotion_key else ""
            char_desc = f"{char['name_en']} ({char['physical']}, {char['clothing']})"
            if emotion_desc:
                char_desc += f", showing {emotion_desc}"
            char_descs.append(char_desc)

    # 场景描述
    scene_base = shot.get("scene", "")
    if char_descs:
        scene_desc = f"{scene_base}. Characters: {'; '.join(char_descs)}."
    else:
        scene_desc = scene_base

    # 根据类型构建prompt
    if prompt_type == "speech_bubble_with_top_monologue":
        # 对话气泡 + 顶部黑底旁白
        bubble_prompt = build_speech_bubble_prompt(
            scene_desc,
            CHARACTERS[shot["dialogue_speaker"]]["name_en"],
            shot["dialogue"],
            "upper right"
        )
        monologue_prompt = f"""
ADDITIONAL TEXT OVERLAY:
A semi-transparent black bar (at the top) spanning the full width, height approximately 20% of frame.
Display Chinese text '{shot["monologue"]}' in white font, centered.
The black overlay should have 75% opacity."""
        parts.append(bubble_prompt + monologue_prompt)

    elif prompt_type == "black_monologue_with_emotion_symbol":
        # 黑底旁白 + 情感符号
        monologue_prompt = build_black_monologue_prompt(scene_desc, shot["monologue"], shot["monologue_position"])
        if shot.get("emotion_symbol"):
            monologue_prompt += f"\n\nEMOTION SYMBOL: {shot['emotion_symbol']}"
        parts.append(monologue_prompt)

    elif prompt_type == "dual_monologue":
        # 顶部+底部双旁白
        parts.append(f"""{scene_desc}

TEXT OVERLAY REQUIREMENT - DUAL BARS:
1. TOP BAR: Semi-transparent black bar at the top, height ~15% of frame.
   Display Chinese text '{shot["top_monologue"]}' in white font, centered.

2. BOTTOM BAR: Semi-transparent black bar at the bottom, height ~15% of frame.
   Display Chinese text '{shot["bottom_monologue"]}' in white font, centered.

Both bars should have 70-80% opacity, creating frame effect.""")

    elif prompt_type == "speech_bubble_with_bottom_monologue":
        bubble_prompt = build_speech_bubble_prompt(
            scene_desc,
            CHARACTERS[shot["dialogue_speaker"]]["name_en"],
            shot["dialogue"]
        )
        monologue_prompt = f"""
ADDITIONAL TEXT OVERLAY:
A semi-transparent black bar (at the bottom) spanning the full width, height approximately 18% of frame.
Display Chinese text '{shot["monologue"]}' in white font, centered."""
        parts.append(bubble_prompt + monologue_prompt)

    elif prompt_type == "speech_bubble_with_sweat_drop":
        bubble_prompt = build_speech_bubble_prompt(scene_desc, "the man", shot["dialogue"], "upper center")
        parts.append(bubble_prompt + f"\n\nEMOTION SYMBOL: {shot['emotion_symbol']}")

    elif prompt_type == "memory_fragments":
        # 回忆碎片效果 ⭐
        char = CHARACTERS["female_lead"]
        main_desc = f"{char['name_en']} ({char['physical']}, {char['clothing']}), standing with {get_emotion_desc(shot['female_emotion'])} expression, {shot['scene']}"
        fragment_prompt = build_memory_fragment_prompt(main_desc, shot["fragments"], shot["emotional_tone"])
        monologue_add = f"""
TEXT OVERLAY:
A semi-transparent black bar at the bottom, height ~18% of frame.
Display Chinese text '{shot["monologue"]}' in white font, centered."""
        parts.append(fragment_prompt + monologue_add)

    elif prompt_type == "side_monologue":
        parts.append(f"""{scene_desc}

TEXT OVERLAY REQUIREMENT:
A semi-transparent black vertical bar on the left side, width approximately 25% of frame.
Display Chinese text '{shot["monologue"]}' in white font, vertical text layout reading top to bottom.
The black overlay should have 75% opacity.""")

    elif prompt_type == "split_screen":
        # 分屏效果 ⭐
        split_prompt = build_split_screen_prompt(
            shot["left_scene"],
            shot["left_emotion"],
            shot["right_scene"],
            shot["right_emotion"],
            shot["narrative_purpose"]
        )
        center_text = f"""
TEXT OVERLAY:
A semi-transparent black bar in the center, spanning full width, height ~20% of frame.
Display Chinese text '{shot["center_monologue"]}' in white font, centered.
Position this bar at the vertical center where the two halves meet."""
        parts.append(split_prompt + center_text)

    elif prompt_type == "multiple_speech_bubbles":
        parts.append(f"""{scene_desc}

MULTIPLE SPEECH BUBBLES:""")
        for d in shot["dialogues"]:
            speaker = CHARACTERS[d["speaker"]]["name_en"]
            parts.append(f"""
- Speech bubble at {d["position"]} with tail pointing to {speaker}:
  Chinese text '{d["text"]}' in black font on white bubble.""")
        parts.append(f"""
ADDITIONAL TEXT OVERLAY:
Black bar at bottom, height ~15%, with Chinese text '{shot["monologue"]}' in white.""")

    elif prompt_type == "large_speech_bubble":
        parts.append(f"""{scene_desc}

LARGE SPEECH BUBBLE:
A prominent white speech bubble, {shot.get("bubble_size", "large")}, with tail pointing to the speaker.
Inside display Chinese text '{shot["dialogue"]}' in black font.
The bubble should be visually prominent but not obscure the character's expression.""")

    elif prompt_type == "speech_bubble":
        parts.append(build_speech_bubble_prompt(scene_desc, "the character", shot["dialogue"], shot.get("bubble_position", "upper right")))

    elif prompt_type == "picture_in_picture_with_bubble":
        # 画中画 + 对话气泡 ⭐
        pip_prompt = build_picture_in_picture_prompt(scene_desc, shot["device_type"], shot["pip_content"])
        bubble_add = f"""
SPEECH BUBBLE:
A small white speech bubble near {CHARACTERS['female_lead']['name_en']}, displaying Chinese text '{shot["dialogue"]}'."""
        parts.append(pip_prompt + bubble_add)

    elif prompt_type == "picture_in_picture_with_white_narrative":
        # 画中画 + 白底叙事 ⭐
        pip_prompt = build_picture_in_picture_prompt(scene_desc, shot["device_type"], shot["pip_content"], "center of frame", "45%")
        narrative_add = f"""
NARRATIVE TEXT OVERLAY:
A semi-transparent white/cream bar at the bottom, height ~18% of frame.
Display Chinese text '{shot["narrative"]}' in black font, centered.
The overlay should have 85% opacity with soft edges."""
        parts.append(pip_prompt + narrative_add)

    elif prompt_type == "white_narrative_top":
        # 顶部白底旁白 ⭐
        parts.append(build_white_narrative_prompt(scene_desc, shot["narrative"], "at the top", "18%"))

    elif prompt_type == "white_narrative_center":
        parts.append(build_white_narrative_prompt(scene_desc, shot["narrative"], "in the center", "15%"))

    else:
        # 默认：场景描述
        parts.append(scene_desc)

    return "\n".join(parts)


# =============================================================================
# 图像生成（使用项目的ImageGenerator服务）
# =============================================================================

# 全局ImageGenerator实例
_image_generator = None

def get_image_generator():
    """获取或创建ImageGenerator实例"""
    global _image_generator
    if _image_generator is None:
        _image_generator = ImageGenerator()
    return _image_generator


async def generate_image(prompt: str, shot_id: int, output_dir: Path) -> dict:
    """使用项目的ImageGenerator服务生成图像"""

    try:
        image_gen = get_image_generator()

        # 生成图像
        result = await image_gen.generate_image(
            prompt=prompt,
            aspect_ratio="9:16",  # 条漫竖版
            use_pro_model=USE_PRO_MODEL,
        )

        if result.get("success"):
            # 保存图像
            image_path = output_dir / f"shot_{shot_id:02d}.png"
            pil_image = result.get("pil_image")
            if pil_image:
                pil_image.save(image_path)
                return {
                    "success": True,
                    "image_path": str(image_path),
                    "shot_id": shot_id,
                    "width": result.get("width"),
                    "height": result.get("height"),
                    "model_used": result.get("model_used"),
                    "generation_time": result.get("generation_time_seconds")
                }
            return {"success": False, "error": "No PIL image in result"}
        else:
            return {"success": False, "error": result.get("error", "Unknown error")}

    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# 主测试流程
# =============================================================================

async def run_comic_mvp_test():
    """运行条漫MVP测试"""

    print("=" * 60)
    print("条漫MVP故事测试")
    print(f"模型: {GEMINI_MODEL}")
    print(f"测试用例: {len(STORY_SHOTS)} 张图")
    print("=" * 60)

    # 创建输出目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_DIR / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n输出目录: {run_dir}")

    # 存储结果
    results = []
    prompts_log = []

    # 生成每张图
    for shot in STORY_SHOTS:
        shot_id = shot["shot_id"]
        ref_image = shot["ref_image"]

        print(f"\n[{shot_id:02d}/15] 生成 {ref_image}...")
        print(f"  类型: {shot['prompt_type']}")

        # 构建prompt
        prompt = build_full_prompt(shot)

        # 保存prompt
        prompts_log.append({
            "shot_id": shot_id,
            "ref_image": ref_image,
            "prompt_type": shot["prompt_type"],
            "prompt": prompt
        })

        # 生成图像
        result = await generate_image(prompt, shot_id, run_dir)

        if result["success"]:
            print(f"  ✅ 成功: {result['image_path']}")
        else:
            print(f"  ❌ 失败: {result['error']}")

        results.append({
            "shot_id": shot_id,
            "ref_image": ref_image,
            "prompt_type": shot["prompt_type"],
            **result
        })

        # 避免API限流
        await asyncio.sleep(2)

    # 保存prompts日志
    prompts_path = run_dir / "prompts_log.json"
    with open(prompts_path, 'w', encoding='utf-8') as f:
        json.dump(prompts_log, f, ensure_ascii=False, indent=2)
    print(f"\nPrompts保存至: {prompts_path}")

    # 保存结果
    results_path = run_dir / "results.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"结果保存至: {results_path}")

    # 统计
    success_count = sum(1 for r in results if r.get("success"))
    print("\n" + "=" * 60)
    print("测试完成!")
    print(f"成功: {success_count}/{len(STORY_SHOTS)}")
    print(f"失败: {len(STORY_SHOTS) - success_count}/{len(STORY_SHOTS)}")
    print("=" * 60)

    # 生成简易验收报告
    report = generate_acceptance_report(results, run_dir)
    report_path = run_dir / "acceptance_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"验收报告: {report_path}")

    return results


def generate_acceptance_report(results: list, run_dir: Path) -> str:
    """生成验收报告模板"""

    success_count = sum(1 for r in results if r.get("success"))

    report = f"""# 条漫MVP故事测试验收报告

**测试日期**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**测试模型**: {GEMINI_MODEL}
**输出目录**: {run_dir}
**验收人**: @Tester (待填写)

## 总体结果

- 生成成功: {success_count}/{len(results)}
- 生成失败: {len(results) - success_count}/{len(results)}

## 总体评价 (待验收人填写)

| 维度 | 得分 | 评价 |
|------|------|------|
| 文字内嵌效果 | /5 | |
| 合成效果 | /5 | |
| 表情细腻度 | /5 | |
| 风格一致性 | /5 | |
| 角色一致性 | /5 | |
| **综合分** | **/5** | 通过/不通过 |

## 逐图验收

"""

    for r in results:
        shot_id = r["shot_id"]
        ref = r["ref_image"]
        ptype = r["prompt_type"]
        status = "✅ 生成成功" if r.get("success") else f"❌ 生成失败: {r.get('error', 'unknown')}"

        report += f"""### 图{shot_id} (对应{ref})

- **类型**: {ptype}
- **状态**: {status}
- 文字内嵌: ⬜ (待验收)
- 表情: ⬜ (待验收)
- 角色一致性: ⬜ (待验收)
- 备注:

---

"""

    report += """## 问题汇总

### 严重问题 (影响发布)
1. (待填写)

### 一般问题 (可接受)
1. (待填写)

## 结论

- [ ] 通过 - 可进入下一阶段
- [ ] 不通过 - 需要优化后重测
- [ ] 部分通过 - (说明哪些能力达标)

## 优化建议

1. (待填写)
"""

    return report


# =============================================================================
# 入口
# =============================================================================

if __name__ == "__main__":
    # 检查环境变量
    if not os.environ.get("GEMINI_API_KEY"):
        # 尝试从 .env 加载
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        key = line.strip().split("=", 1)[1]
                        os.environ["GEMINI_API_KEY"] = key
                        break

    if not os.environ.get("GEMINI_API_KEY"):
        print("错误: 未设置 GEMINI_API_KEY 环境变量")
        sys.exit(1)

    asyncio.run(run_comic_mvp_test())
