"""
条漫完整故事测试脚本 - 故事C《最后的记忆商人》
赛博朋克 + Neo-Noir 风格

多风格通用性验证测试 (TASK-VERIFY-001-C)

故事脚本: docs/COMIC_STORY_C_CYBERPUNK_SCRIPT.md
风格: Cyberpunk / Neo-Noir

作者: @Backend
日期: 2026-01-29
"""

import asyncio
import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

import anthropic
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 加载 .env 文件中的环境变量
load_dotenv(Path(__file__).parent.parent / ".env")

from app.services.image_generator import ImageGenerator
from app.services.reference_image_manager import ReferenceImageManager
from app.models.style_config import ProjectStyleConfig
from app.prompts.character_position_detection import (
    build_prompt as build_position_detection_prompt,
    extract_character_description_for_haiku,
)
from app.services.text_overlay_service import (
    TextOverlayService,
    strip_speaker_prefix,
    get_bubble_position_for_index,
    detect_overlay_collision,
)

# =============================================================================
# 配置
# =============================================================================

GEMINI_MODEL = "gemini-2.5-flash-image"
USE_PRO_MODEL = False  # 条漫插画风格继续用Flash

# 输出目录 - Story C: Cyberpunk 赛博朋克
OUTPUT_DIR = Path(__file__).parent.parent / "test_output" / "comic_full_story_v2_cyberpunk"
NO_TEXT_DIR = OUTPUT_DIR / "no_text_images"
WITH_TEXT_DIR = OUTPUT_DIR / "with_text_images"
COMPARISON_DIR = OUTPUT_DIR / "comparison"
REFERENCE_DIR = OUTPUT_DIR / "reference_images"

# 字体配置
FONT_PATHS = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
]

# 字体大小
DEFAULT_FONT_SIZE = 42
SPEECH_BUBBLE_FONT_SIZE = 36
EMPHASIS_FONT_SIZE = 52
EMPHASIS_COLOR = "#FF4444"

# =============================================================================
# 角色定义 (3个角色: 林夜、老陈、凯拉)
# =============================================================================

CHARACTERS = {
    # 主角：林夜 (char_001) - 32岁记忆商人
    "lin_ye": {
        "id": "lin_ye",
        "name": "林夜",
        "name_en": "Lin Ye",
        "character_type": "human",
        "gender": "male",
        "age_appearance": "adult",
        "physical": {
            "height": "medium (175cm)",
            "build": "lean athletic, lithe and quick",
            "skin_tone": "pale, rarely sees natural sunlight",
            "face_shape": "angular with sharp features",
            "hair_color": "jet black",
            "hair_style": "short sides shaved with longer top slicked back",
            "hair_texture": "straight",
            "eye_color": "dark brown right eye, SILVER CYBERNETIC LEFT EYE with faint blue glow",
            "eye_shape": "sharp, calculating",
            "eye_size": "medium",
            "eye_description": "SILVER CYBERNETIC LEFT EYE with BLUE GLOW, dark brown right eye",
            "eyebrows": "thick straight",
            "nose": "straight",
            "lips": "thin, often pressed",
            "distinctive_marks": ["SILVER CYBERNETIC LEFT EYE with BLUE GLOW", "thin scar on right cheek", "glowing neural port on left wrist"]
        },
        "clothing": {
            "top": "dark gray synthetic leather jacket over black turtleneck",
            "bottom": "black tactical cargo pants with multiple pockets",
            "footwear": "black combat boots with metal accents",
            "accessories": ["glowing neural interface port on left wrist", "dark hood attached to jacket"],
            "style": "cyberpunk street, practical and anonymous"
        }
    },
    # 配角：老陈 (char_002) - 78岁老人
    "old_chen": {
        "id": "old_chen",
        "name": "老陈",
        "name_en": "Old Chen",
        "character_type": "human",
        "gender": "male",
        "age_appearance": "elderly",
        "physical": {
            "height": "medium (170cm, stooped)",
            "build": "frail, thin from age",
            "skin_tone": "weathered pale with age spots",
            "face_shape": "gaunt with hollow cheeks",
            "hair_color": "white",
            "hair_style": "thin white hair combed back",
            "hair_texture": "wispy and sparse",
            "eye_color": "clouded gray (natural, no implants)",
            "eye_shape": "hooded with heavy lids",
            "eye_size": "small",
            "eye_description": "clouded gray natural eyes, hooded with heavy lids",
            "eyebrows": "sparse white",
            "nose": "prominent thin",
            "lips": "thin dry",
            "distinctive_marks": ["deep wrinkles", "oxidized old-model neural ports on back of hands", "age spots"]
        },
        "clothing": {
            "top": "faded blue worker jumpsuit with old tech company logo patch (partially peeled)",
            "bottom": "same jumpsuit pants",
            "footwear": "worn gray utility shoes",
            "accessories": ["metal walking cane with worn rubber grip", "old memory chip on cord around neck"],
            "style": "worn utilitarian, remnant of old world"
        }
    },
    # 反派：凯拉 (char_003) - 28岁企业安全官
    "kayla": {
        "id": "kayla",
        "name": "凯拉",
        "name_en": "Kayla",
        "character_type": "human",
        "gender": "female",
        "age_appearance": "young_adult",
        "physical": {
            "height": "tall (175cm)",
            "build": "athletic, military posture",
            "skin_tone": "fair",
            "face_shape": "angular with high cheekbones",
            "hair_color": "silver white",
            "hair_style": "short asymmetrical side-parted",
            "hair_texture": "sleek",
            "eye_color": "RED CYBERNETIC COMBAT EYES (BOTH EYES)",
            "eye_shape": "almond, predatory",
            "eye_size": "medium",
            "eye_description": "BOTH EYES are RED CYBERNETIC COMBAT IMPLANTS, always glowing",
            "eyebrows": "thin arched",
            "nose": "straight refined",
            "lips": "full with perpetual slight smirk",
            "distinctive_marks": ["BOTH eyes are RED cybernetic combat implants", "RIGHT ARM is FULL CHROME CYBERNETIC LIMB with hidden weapon", "small corporate barcode tattoo on neck"]
        },
        "clothing": {
            "top": "black corporate tactical armor vest with glowing RED CORPORATE LOGO",
            "bottom": "black tactical pants with armored knee pads",
            "footwear": "black armored combat boots",
            "accessories": ["full chrome right cybernetic arm (with hidden blade)", "tactical earpiece", "holstered energy pistol on hip"],
            "style": "corporate security elite, intimidating and efficient"
        }
    }
}

# =============================================================================
# Shot到角色的映射
# =============================================================================

SHOT_CHARACTER_MAPPING = {
    1: [],  # 城市远景，无角色
    2: ["lin_ye"],
    3: ["lin_ye"],
    4: ["lin_ye"],
    5: ["old_chen"],
    6: ["lin_ye", "old_chen"],
    7: ["old_chen"],  # 特写手部
    8: ["lin_ye"],
    9: ["kayla"],
    10: ["lin_ye", "old_chen"],  # 追逐
    11: ["lin_ye", "old_chen"],  # 追逐
    12: ["lin_ye", "old_chen"],
    13: ["lin_ye", "old_chen"],
    14: [],  # 记忆场景，无角色
    15: ["lin_ye", "old_chen"],
}

# =============================================================================
# 风格定义 (Cyberpunk / Neo-Noir)
# =============================================================================

CYBERPUNK_STYLE_PREFIX = """
STYLE: Cyberpunk / Neo-Noir

Cinematic cyberpunk aesthetic inspired by Blade Runner and Ghost in the Shell.
Dramatic neon lighting in pink, cyan, and purple against dark backgrounds.
Wet streets reflecting holographic advertisements. High-tech dystopian atmosphere.
Dense urban environments with towering buildings and holographic billboards.
Surveillance drones, neural interfaces, and cybernetic enhancements as visual elements.
Dark, moody atmosphere with pockets of vibrant neon color.

MUST INCLUDE: neon lights (pink, cyan, purple), wet reflective surfaces, holographic displays, dark atmosphere, futuristic technology, dense urban environment, dramatic lighting contrasts
DO NOT USE: bright daylight, natural colors, pastoral scenes, cartoon style, anime style, watercolor, hand-drawn look, clean bright environments

"""

MEMORY_SCENE_TREATMENT = """
MEMORY/OLD WORLD SCENE TREATMENT:
- CONTRASTING with the cyberpunk aesthetic
- Bright natural sunlight, clear blue sky
- Warm golden tones, natural greens
- Clean air, no neon, no corporate logos
- Genuine human expressions and connections
- Beautiful lost world preserved in forbidden memory
- This scene should feel like a breath of fresh air after the dark dystopian world
"""

CHASE_SCENE_TREATMENT = """
CHASE/ACTION SCENE TREATMENT:
- Dynamic motion blur on running figures
- Rain streaks through neon light beams
- Urgency conveyed through composition
- Drone searchlights sweeping
- Reflections on wet pavement
"""

TEXT_FREE_REQUIREMENT = """
ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
"""

# =============================================================================
# 构建角色参考图指令
# =============================================================================

def build_character_reference_instruction(characters_in_shot: List[str]) -> str:
    """构建角色参考图指令，告诉模型如何使用参考图"""
    if not characters_in_shot:
        return ""

    instructions = ["\nCHARACTER REFERENCE IMAGES:"]
    instructions.append("The following reference images show the characters that should appear in this scene.")
    instructions.append("CRITICAL: Match each character's appearance EXACTLY as shown in their reference images.")
    instructions.append("")

    for i, char_id in enumerate(characters_in_shot):
        char = CHARACTERS.get(char_id)
        if char:
            instructions.append(f"Reference Image {i + 1}: {char['name_en']} ({char['name']})")
            physical = char.get('physical', {})
            clothing = char.get('clothing', {})

            # 头发描述
            hair_desc = f"{physical.get('hair_color', '')} {physical.get('hair_style', '')}"
            instructions.append(f"  - Hair: {hair_desc.strip()}")

            # 眼睛描述（赛博朋克关键）
            eye_desc = physical.get('eye_description', '')
            if eye_desc:
                instructions.append(f"  - Eyes: {eye_desc}")

            # 服装
            if clothing.get('top'):
                instructions.append(f"  - Clothing: {clothing['top']}")

            # 特殊标记（赛博朋克关键）
            if physical.get('distinctive_marks'):
                marks = physical['distinctive_marks']
                if isinstance(marks, list):
                    instructions.append(f"  - CRITICAL MARKERS: {', '.join(marks[:3])}")

    instructions.append("")
    instructions.append("IMPORTANT: Cybernetic enhancements (eyes, limbs, ports) MUST be visible and correct.")
    instructions.append("IMPORTANT: Maintain consistent character appearance throughout the story.")

    return "\n".join(instructions)

# =============================================================================
# 15图完整脚本定义 (赛博朋克风格)
# =============================================================================

FULL_STORY_SHOTS = [
    # Shot 01: 城市远景
    {
        "shot_id": 1,
        "scene": "城市远景 - 未来城市天际线",
        "text_type": "narration",
        "speaker_position": "top",
        "chinese_text": "2089年，新城。在这里，一切都可以被购买。包括记忆。",
        "characters": [],
        "image_prompt": f"""{CYBERPUNK_STYLE_PREFIX}
---

Establishing wide shot of Neo City at night. A vast cyberpunk metropolis stretches to the horizon. Towering skyscrapers pierce the dark overcast sky, their surfaces covered with massive holographic advertisements casting pink and cyan light across the urban canyon.

Surveillance drones patrol in formation against the clouds. Rain falls through beams of neon light. A dominant corporate tower rises above all others, its giant glowing logo visible for miles. Streets far below are packed with anonymous crowds, rendered as streams of light and movement.

The atmosphere is oppressive yet hauntingly beautiful - a civilization that has sacrificed humanity for technology. No stars visible through the perpetual smog and light pollution.

EMOTIONAL ATMOSPHERE:
Dystopian grandeur, oppressive corporate dominance, a world where everything has a price.
The beautiful nightmare of unchecked technological progress.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 02: 林夜登场
    {
        "shot_id": 2,
        "scene": "林夜登场 - 霓虹街区",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "林夜，黑市记忆商人。他的工作是交易那些不被允许存在的记忆。",
        "characters": ["lin_ye"],
        "image_prompt": f"""{CYBERPUNK_STYLE_PREFIX}
---

Medium shot of Lin Ye (lin_ye) moving through a crowded neon-lit street. He is a lean man in his early 30s with jet black hair (short sides, longer top slicked back), wearing a dark gray synthetic leather jacket over black turtleneck. His hood is pulled up partially.

CRITICAL: His LEFT EYE is a SILVER CYBERNETIC IMPLANT with a FAINT BLUE GLOW, scanning his surroundings. A thin scar marks his right cheek. His expression is alert but composed.

Around him, crowds in synthetic raincoats and VR visors pass by anonymously. Neon signs in Chinese and English cast pink and cyan reflections on the wet pavement. Street vendors sell synthetic food from cramped stalls. A surveillance drone hovers overhead.

Lin Ye moves with predatory grace, constantly scanning, never fully relaxed. The neon light catches his cybernetic eye, making it gleam.

EMOTIONAL ATMOSPHERE:
Tense alertness, practiced anonymity, a man who survives by seeing everything.
Navigating danger as routine.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 03: 地下入口
    {
        "shot_id": 3,
        "scene": "地下入口 - 废弃地铁站",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "今晚，有一笔特殊的交易在等着他。",
        "characters": ["lin_ye"],
        "image_prompt": f"""{CYBERPUNK_STYLE_PREFIX}
---

Medium shot of an abandoned metro station entrance. Lin Ye (lin_ye) stands at the top of a broken escalator that descends into darkness. He is silhouetted against the neon glow from the street above, his dark gray jacket and black turtleneck barely visible.

CRITICAL: His SILVER CYBERNETIC LEFT EYE glows BRIGHTER BLUE as it scans for surveillance. Thin scar visible on right cheek.

The escalator is broken and rusted. Graffiti covers the walls - both gang tags and revolutionary slogans. Old transit signs hang crooked, their displays dead. Blue light emanates from somewhere below - the glow of the underground market.

The scene captures the transition from the open street to the hidden world below. Rain drips down through the entrance.

EMOTIONAL ATMOSPHERE:
Anticipation, entering the underground, crossing into the shadow economy.
The threshold between two worlds.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 04: 记忆交易所
    {
        "shot_id": 4,
        "scene": "记忆交易所 - 地下空间",
        "text_type": "narration",
        "speaker_position": "top",
        "chinese_text": "记忆交易所——新城最大的黑市。",
        "characters": ["lin_ye"],
        "image_prompt": f"""{CYBERPUNK_STYLE_PREFIX}
---

Wide shot revealing the Memory Exchange - an underground black market in a converted metro station. The vast space is filled with dealer booths - small partitioned areas with neural interface chairs and server equipment. Blue light emanates from server racks lining the walls, casting the entire space in eerie illumination.

Lin Ye (lin_ye) enters from the background, his figure small against the scale of the illicit marketplace. Dark gray jacket, black turtleneck, SILVER CYBERNETIC LEFT EYE with BLUE GLOW visible even at distance.

Hooded figures conduct quiet transactions in shadowy corners. LED strips provide minimal additional lighting. Armed guards stand watch in the shadows. The atmosphere is one of illegal commerce - dangerous but organized.

Graffiti and old-world posters cover sections of the walls - remnants of the past mixed with present desperation.

EMOTIONAL ATMOSPHERE:
Underground commerce, necessary evil, the shadow economy where forbidden memories change hands.
A cathedral of the black market.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 05: 老陈出现
    {
        "shot_id": 5,
        "scene": "老陈出现 - 交易所角落",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "委托人是个老人。他的眼神里有种林夜很少见到的东西——真诚的恐惧。",
        "characters": ["old_chen"],
        "image_prompt": f"""{CYBERPUNK_STYLE_PREFIX}
---

Medium close-up of Old Chen (old_chen) stepping forward from shadow into a pool of blue light. He is a frail elderly man of 78 with thin WHITE HAIR combed back, wearing a FADED BLUE WORKER JUMPSUIT with an old tech company logo patch.

He grips a METAL WALKING CANE with worn rubber grip in one trembling hand. His face is deeply wrinkled, gaunt cheeks, clouded gray eyes burning with desperate urgency. OXIDIZED OLD-MODEL NEURAL PORTS are visible on the back of his weathered, age-spotted hands.

Around his neck hangs an OLD MEMORY CHIP on a simple cord - catching the blue light. His expression shows a mixture of fear and determination. He has been waiting for this meeting.

The harsh overhead light creates dramatic shadows on his face, emphasizing his age and desperation.

EMOTIONAL ATMOSPHERE:
Desperate urgency, last chance, a man with something precious and dangerous to pass on.
The weight of secret knowledge.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 06: 对话
    {
        "shot_id": 6,
        "scene": "对话 - 交易隔间",
        "text_type": "dialogue",
        "speaker_position": "right",
        "chinese_text": "我要把这个交给你保管。这是关于「大崩溃」的真相。",
        "characters": ["lin_ye", "old_chen"],
        "image_prompt": f"""{CYBERPUNK_STYLE_PREFIX}
---

Over-the-shoulder shot in a small trading booth. Lin Ye (lin_ye) and Old Chen (old_chen) face each other across a narrow space. Blue glow from neural interface equipment illuminates their faces from below.

Lin Ye (lin_ye): dark gray jacket, black turtleneck, SILVER CYBERNETIC LEFT EYE with BLUE GLOW, thin scar on right cheek. His expression is shifting from professional skepticism to genuine concern as he listens.

Old Chen (old_chen): frail, WHITE HAIR, FADED BLUE JUMPSUIT, holds up a YELLOWED OLD MEMORY CHIP with trembling hands. His clouded gray eyes are intense with desperate purpose. The OXIDIZED NEURAL PORTS on his hands are visible.

The booth contains a neural interface chair with cables and a small server unit. Shadows and blue light create an intimate, conspiratorial atmosphere.

EMOTIONAL ATMOSPHERE:
Secret transaction, passing of forbidden knowledge, trust being established.
The moment before everything changes.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 07: 记忆芯片特写
    {
        "shot_id": 7,
        "scene": "记忆芯片特写",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "那是一块旧式记忆芯片。在今天，它比任何武器都危险。",
        "characters": ["old_chen"],
        "image_prompt": f"""{CYBERPUNK_STYLE_PREFIX}
---

Extreme close-up of Old Chen's aged trembling hands holding a YELLOWED OLD-MODEL MEMORY CHIP. The chip's surface is scratched and worn, showing its decades of age - obsolete technology that has somehow survived.

The OXIDIZED NEURAL PORTS on the back of his weathered hands are clearly visible - old-generation implants, discolored with age, surrounded by age spots. The hands tremble slightly but grip the chip with fierce determination.

Blue light catches the edges of the chip, making it gleam. The background is blurred but blue-tinged, suggesting the trading booth environment.

This small, fragile object contains the most dangerous thing in Neo City - truth.

EMOTIONAL ATMOSPHERE:
Preciousness, danger, a fragment of forbidden history held in trembling hands.
Something worth dying for.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 08: 警报
    {
        "shot_id": 8,
        "scene": "警报 - 红色警报灯亮起",
        "text_type": "narration",
        "speaker_position": "top",
        "chinese_text": "企业的人来了。",
        "characters": ["lin_ye"],
        "image_prompt": f"""{CYBERPUNK_STYLE_PREFIX}
---

Medium shot of Lin Ye (lin_ye) in the Memory Exchange as chaos erupts. RED WARNING LIGHTS flash across the space, mixing harshly with the usual blue glow. Panicked dealers scramble in the background, shadows scattering.

Lin Ye's posture shifts to high alert - body coiled, ready to move. His SILVER CYBERNETIC LEFT EYE blazes BRIGHT BLUE as it processes threat data, scanning toward the entrance. His dark gray jacket and black turtleneck frame his tense figure. Thin scar on right cheek.

His expression shows controlled alarm - not panic, but instant tactical assessment. One hand moves instinctively to protect the pocket where the memory chip now rests.

The space that was ominously quiet moments ago is now chaos - but Lin Ye remains a still point, calculating.

EMOTIONAL ATMOSPHERE:
Sudden danger, instinct taking over, the moment when the trap springs.
Fight or flight decision.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 09: 凯拉登场
    {
        "shot_id": 9,
        "scene": "凯拉登场 - 企业安全官",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "凯拉，企业安全官。她的眼里只有目标。",
        "characters": ["kayla"],
        "image_prompt": f"""{CYBERPUNK_STYLE_PREFIX}
---

Low angle shot looking up at Kayla (kayla) as she strides through the Memory Exchange entrance. She is backlit by neon glow from above, creating a menacing silhouette that steps into focus.

CRITICAL: SILVER-WHITE SHORT HAIR in asymmetrical side-parted style. BOTH EYES are RED CYBERNETIC COMBAT IMPLANTS, glowing intensely as they scan the crowd. Her RIGHT ARM is a FULL CHROME CYBERNETIC LIMB with visible joints, fingers flexing to reveal hidden blade mechanisms.

She wears BLACK TACTICAL ARMOR with a GLOWING RED CORPORATE LOGO on her chest. Her expression is a cold calculating smirk. Behind her, a security team follows in formation.

Her posture radiates military precision and lethal efficiency. She moves like a predator who knows exactly where her prey is.

EMOTIONAL ATMOSPHERE:
Menace, corporate authority, the arrival of overwhelming force.
The hunter has found her target.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 10: 逃亡 (追逐场景)
    {
        "shot_id": 10,
        "scene": "逃亡 - 后通道",
        "text_type": "narration",
        "speaker_position": "top",
        "chinese_text": "林夜带着老陈从后门逃离。但他知道，企业的追踪器不会放过他们。",
        "is_chase": True,
        "characters": ["lin_ye", "old_chen"],
        "image_prompt": f"""{CYBERPUNK_STYLE_PREFIX}
{CHASE_SCENE_TREATMENT}
---

Tracking shot through a narrow maintenance corridor. Lin Ye (lin_ye) pulls Old Chen (old_chen) along, supporting the frail old man as they flee. Blue emergency lights strobe along the corridor.

Lin Ye: dark gray jacket, black turtleneck, SILVER CYBERNETIC LEFT EYE glowing as he looks back over his shoulder. Thin scar on right cheek. Expression shows focused determination.

Old Chen: struggles to keep pace, his METAL CANE barely keeping up with his shuffling feet. One hand grips his FADED BLUE JUMPSUIT where the memory chip hangs. WHITE HAIR disheveled, face showing exhausted determination.

Pipes and cables line the industrial walls. Behind them, shouts and footsteps echo - the pursuit is close. The corridor stretches ahead into uncertain darkness.

EMOTIONAL ATMOSPHERE:
Desperate flight, protection, racing against time.
Two men carrying something more valuable than their lives.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 11: 街头追逐 (追逐场景)
    {
        "shot_id": 11,
        "scene": "街头追逐 - 雨中霓虹街道",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "霓虹灯下，每个人都在奔跑。但只有他们在为真相奔跑。",
        "is_chase": True,
        "characters": ["lin_ye", "old_chen"],
        "image_prompt": f"""{CYBERPUNK_STYLE_PREFIX}
{CHASE_SCENE_TREATMENT}
---

Dynamic shot of a rainy neon street at night. Lin Ye (lin_ye) and Old Chen (old_chen) push through a crowded street, rain falling through neon light beams creating prismatic streaks.

Lin Ye: supports exhausted Old Chen, weaving between oblivious crowds in synthetic raincoats. Dark gray jacket, SILVER CYBERNETIC LEFT EYE scanning behind them. Checking over his shoulder for pursuit. Thin scar on right cheek visible in neon light.

Old Chen: FADED BLUE JUMPSUIT soaked, clinging to Lin Ye's arm for support. WHITE HAIR plastered to his head. METAL CANE gripped fiercely. Exhausted but determined.

Neon signs in pink and cyan reflect off the wet pavement in beautiful streaks. Far behind them, searchlights sweep from pursuing DRONES - visible as ominous lights cutting through the rain.

EMOTIONAL ATMOSPHERE:
Desperate flight through beautiful dystopia, racing against corporate hunters.
Running for truth in a world of lies.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 12: 藏身处
    {
        "shot_id": 12,
        "scene": "藏身处 - 老陈的公寓",
        "text_type": "narration",
        "speaker_position": "top",
        "chinese_text": "老陈的藏身处。这里保存着被抹杀的世界。",
        "characters": ["lin_ye", "old_chen"],
        "image_prompt": f"""{CYBERPUNK_STYLE_PREFIX}
---

Wide shot of Old Chen's cluttered hideout apartment. A large window shows the neon city skyline with distant corporate holographic logos. The room is filled with OLD TECHNOLOGY - vintage computers, memory equipment, tangled wires piled everywhere.

One wall is covered with FADED PHOTOGRAPHS and clippings from BEFORE THE GREAT COLLAPSE - images of green parks, blue skies, people with genuine smiles. A preserved museum of the lost world.

In the center, an OLD BUT WELL-MAINTAINED MEMORY TRANSFER PLATFORM glows softly, waiting.

Lin Ye (lin_ye) helps exhausted Old Chen (old_chen) through the door, his eyes wide with wonder at the preserved history. Dark gray jacket, SILVER CYBERNETIC LEFT EYE reflecting the room's contents. Old Chen (WHITE HAIR, FADED BLUE JUMPSUIT) leans against the doorframe, catching his breath, gesturing at his sanctuary.

EMOTIONAL ATMOSPHERE:
Temporary refuge, a hidden archive of truth, awe at what has been preserved.
A pocket of the past surviving in the future.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 13: 记忆传输
    {
        "shot_id": 13,
        "scene": "记忆传输 - 传递遗产",
        "text_type": "dialogue",
        "speaker_position": "left",
        "chinese_text": "把它传给你。让真相活下去。",
        "characters": ["lin_ye", "old_chen"],
        "image_prompt": f"""{CYBERPUNK_STYLE_PREFIX}
---

Medium shot of the memory transfer platform at the center of the room. Old Chen (old_chen) lies on the old platform, neural cables connected to the OXIDIZED PORTS on his hands. His face is peaceful, eyes closed in acceptance. WHITE HAIR spread on the platform, FADED BLUE JUMPSUIT visible.

Lin Ye (lin_ye) stands at the control panel, connecting his own GLOWING WRIST NEURAL PORT. His expression is grave and reverent, understanding the weight of what he is about to receive. Dark gray jacket, SILVER CYBERNETIC LEFT EYE dimmed in concentration, thin scar on right cheek.

Soft amber glow from the platform mixes with the usual cyberpunk lighting. Old photographs on the wall behind them watch over this sacred moment of memory transmission.

EMOTIONAL ATMOSPHERE:
Solemn ritual, transmission of legacy, sacred responsibility being passed.
A dying man's final gift.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 14: 记忆画面（旧世界）- 特殊风格对比
    {
        "shot_id": 14,
        "scene": "记忆画面 - 旧世界",
        "text_type": "thought",
        "speaker_position": "bottom",
        "chinese_text": "原来……我们曾经拥有过这样的世界。",
        "is_memory": True,
        "characters": [],
        "image_prompt": f"""{MEMORY_SCENE_TREATMENT}
---

A vision of the old world before the Great Collapse. CLEAR BLUE SKY with white fluffy clouds. BRIGHT NATURAL SUNLIGHT bathes the scene in warm golden tones.

A PARK scene with GREEN GRASS and healthy TREES. Families laughing genuinely, children playing freely without surveillance. People making eye contact and SMILING REAL SMILES - not the guarded expressions of the corporate dystopia.

No corporate logos, no surveillance drones, no neon signs. CLEAN AIR, natural light, organic colors. People wearing simple, natural clothing in soft colors.

This is not the cyberpunk world - this is what was lost. Beautiful, innocent, human. A memory of what humanity gave up.

The style shifts completely from dark cyberpunk to bright, warm, almost dreamlike natural beauty. This contrast should be stark and emotionally moving.

EMOTIONAL ATMOSPHERE:
Revelation, mourning for what was lost, understanding why this memory is worth dying for.
The beautiful world that was erased.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 15: 新的开始
    {
        "shot_id": 15,
        "scene": "新的开始 - 使命延续",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "老陈走了。但他的记忆，将成为新城地下最危险的秘密。林夜知道，他的战斗才刚刚开始。",
        "characters": ["lin_ye", "old_chen"],
        "image_prompt": f"""{CYBERPUNK_STYLE_PREFIX}
---

The window of the hideout overlooking the neon cityscape. Lin Ye (lin_ye) stands silhouetted against the glass, the MEMORY CHIP held in his hand. Neon light from outside casts pink and cyan on his face.

His SILVER CYBERNETIC LEFT EYE reflects the city lights. His expression shows determination mixed with grief. Dark gray jacket, thin scar on right cheek visible in the neon glow.

Behind him, Old Chen (old_chen) lies peacefully on the platform, eyes closed, his life's mission complete. His WHITE HAIR and FADED BLUE JUMPSUIT visible. The old world photographs on the wall watch over them both like silent witnesses.

The composition shows Lin Ye looking out at the dystopian city he must now fight to change, armed with the truth. A new purpose born from an old man's sacrifice.

EMOTIONAL ATMOSPHERE:
Determination, bittersweet grief, new purpose. The battle is just beginning.
Carrying forward a sacred mission.

{TEXT_FREE_REQUIREMENT}
"""
    }
]

# =============================================================================
# 图像生成
# =============================================================================

_image_generator = None

def get_image_generator():
    global _image_generator
    if _image_generator is None:
        _image_generator = ImageGenerator()
    return _image_generator

async def generate_reference_images(
    ref_manager: ReferenceImageManager,
    image_gen: ImageGenerator,
    characters: Dict[str, dict],
    style_config: ProjectStyleConfig,
    output_dir: Path
) -> Dict[str, Dict[str, Any]]:
    """为所有角色生成参考图"""
    reference_results = {}

    print("\n" + "=" * 50)
    print("生成角色参考图 (3个角色)")
    print("=" * 50)

    for char_id, char_data in characters.items():
        print(f"\n[参考图] {char_data['name']} ({char_id})")

        try:
            result = await ref_manager.generate_character_multi_refs(
                character=char_data,
                project_style=style_config,
                image_generator=image_gen,
                delay=2.0
            )

            portrait_result = result.get('portrait', {})
            fullbody_result = result.get('fullbody', {})

            portrait_img = portrait_result.get('pil_image') if portrait_result.get('success') else None
            fullbody_img = fullbody_result.get('pil_image') if fullbody_result.get('success') else None

            portrait_path = None
            fullbody_path = None

            if portrait_img:
                portrait_path = output_dir / f"{char_id}_portrait.png"
                portrait_img.save(str(portrait_path))
                print(f"  ✅ 肖像: {portrait_path.name}")

            if fullbody_img:
                fullbody_path = output_dir / f"{char_id}_fullbody.png"
                fullbody_img.save(str(fullbody_path))
                print(f"  ✅ 全身: {fullbody_path.name}")

            if portrait_img or fullbody_img:
                reference_results[char_id] = {
                    "success": True,
                    "portrait_image": portrait_img,
                    "fullbody_image": fullbody_img,
                    "portrait_path": str(portrait_path) if portrait_path else None,
                    "fullbody_path": str(fullbody_path) if fullbody_path else None
                }
            else:
                print(f"  ❌ 失败: 肖像和全身图都生成失败")
                reference_results[char_id] = {
                    "success": False,
                    "error": "Both portrait and fullbody generation failed"
                }

        except Exception as e:
            print(f"  ❌ 异常: {e}")
            reference_results[char_id] = {"success": False, "error": str(e)}

        await asyncio.sleep(1)

    return reference_results

async def generate_image_with_refs(
    prompt: str,
    shot_id: int,
    output_dir: Path,
    reference_images: List[Image.Image],
    char_instruction: str = ""
) -> dict:
    """生成无文字图像（带参考图）"""
    try:
        image_gen = get_image_generator()

        full_prompt = prompt
        if char_instruction:
            full_prompt = char_instruction + "\n\n" + prompt

        result = await image_gen.generate_image(
            prompt=full_prompt,
            aspect_ratio="9:16",
            use_pro_model=USE_PRO_MODEL,
            reference_images=reference_images if reference_images else None
        )

        if result.get("success"):
            image_path = output_dir / f"shot_{shot_id:02d}.png"
            pil_image = result.get("pil_image")
            if pil_image:
                pil_image.save(image_path)
                return {
                    "success": True,
                    "image_path": str(image_path),
                    "pil_image": pil_image,
                    "shot_id": shot_id,
                    "ref_count": len(reference_images) if reference_images else 0
                }
            return {"success": False, "error": "No PIL image"}
        else:
            return {"success": False, "error": result.get("error", "Unknown error")}

    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# 角色位置检测
# =============================================================================

async def detect_character_positions(
    shot_image: Image.Image,
    characters_in_scene: List[str],
    reference_images: Dict[str, Path],
    characters: List[dict],
    debug_mode: bool = False
) -> Dict[str, Dict[str, int]]:
    """使用 Claude 4.5 Haiku 检测角色并推荐泡泡位置"""
    if not characters_in_scene:
        return {}

    chars_with_refs = [c for c in characters_in_scene if c in reference_images]
    if not chars_with_refs:
        print("  ⚠️ 无可用参考图，跳过角色位置检测")
        return {}

    try:
        client = anthropic.AsyncAnthropic()

        char_descriptions = {}
        for char in characters:
            char_id = char.get('id', '')
            if char_id in chars_with_refs:
                char_descriptions[char_id] = extract_character_description_for_haiku(char)

        prompt_text = build_position_detection_prompt(
            characters_in_scene=chars_with_refs,
            character_descriptions=char_descriptions,
            debug_mode=debug_mode
        )

        content = []

        import io
        shot_buffer = io.BytesIO()
        shot_image.save(shot_buffer, format="PNG")
        shot_b64 = base64.standard_b64encode(shot_buffer.getvalue()).decode()

        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": shot_b64}
        })

        for char_id in chars_with_refs:
            ref_path = reference_images.get(char_id)
            if ref_path and Path(ref_path).exists():
                with open(ref_path, "rb") as f:
                    ref_b64 = base64.standard_b64encode(f.read()).decode()
                content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/png", "data": ref_b64}
                })

        content.append({"type": "text", "text": prompt_text})

        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": content}]
        )

        response_text = response.content[0].text

        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        result = json.loads(response_text.strip())

        if debug_mode:
            return result

        simplified = {}
        for char_id, data in result.items():
            if isinstance(data, dict) and "bubble_x_percent" in data:
                simplified[char_id] = {
                    "bubble_x_percent": int(data["bubble_x_percent"]),
                    "bubble_y_percent": int(data.get("bubble_y_percent", 10))
                }

        print(f"  ✅ 泡泡位置推荐完成: {simplified}")
        return simplified

    except Exception as e:
        print(f"  ⚠️ 角色位置检测失败: {e}")
        return {}


# =============================================================================
# 对比图生成
# =============================================================================

def create_comparison(original: Image.Image, processed: Image.Image, shot_name: str) -> Image.Image:
    """创建对比图"""
    width, height = original.size
    comparison = Image.new('RGB', (width * 2 + 20, height + 60), color='white')

    if original.mode == 'RGBA':
        original_rgb = Image.new('RGB', original.size, 'white')
        original_rgb.paste(original, mask=original.split()[3])
        original = original_rgb

    if processed.mode == 'RGBA':
        processed_rgb = Image.new('RGB', processed.size, 'white')
        processed_rgb.paste(processed, mask=processed.split()[3])
        processed = processed_rgb

    comparison.paste(original, (0, 30))
    comparison.paste(processed, (width + 20, 30))

    draw = ImageDraw.Draw(comparison)
    try:
        label_font = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 20)
    except:
        label_font = ImageFont.load_default()

    draw.text((width // 2 - 50, 5), "无文字原图", font=label_font, fill="black")
    draw.text((width + 20 + width // 2 - 70, 5), "叠加文字后", font=label_font, fill="black")
    draw.text((width - 50, height + 35), shot_name, font=label_font, fill="gray")

    return comparison

# =============================================================================
# 主测试流程
# =============================================================================

async def run_story_c_cyberpunk_test():
    """运行故事C赛博朋克测试"""

    print("=" * 70)
    print("条漫完整故事测试 - 故事C《最后的记忆商人》")
    print("15张图完整故事，Cyberpunk / Neo-Noir 风格")
    print("任务: TASK-VERIFY-001-C 多风格通用性验证")
    print("=" * 70)

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    NO_TEXT_DIR.mkdir(parents=True, exist_ok=True)
    WITH_TEXT_DIR.mkdir(parents=True, exist_ok=True)
    COMPARISON_DIR.mkdir(parents=True, exist_ok=True)
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n输出目录: {OUTPUT_DIR}")

    # 初始化服务
    try:
        text_service = TextOverlayService()
        print(f"字体: {text_service.font_path}")
    except RuntimeError as e:
        print(f"❌ 初始化失败: {e}")
        return

    image_gen = get_image_generator()
    ref_manager = ReferenceImageManager()

    # 风格配置 - 赛博朋克风格
    style_config = ProjectStyleConfig(
        style_preset="cyberpunk",
        color_palette="neon",
        dominant_colors=["neon_pink", "cyan", "purple", "dark_gray", "black"],
        lighting_style="dramatic_neon",
        rendering="cinematic"
    )

    # Step 1: 生成参考图
    print("\n" + "=" * 70)
    print("Step 1: 生成角色参考图")
    print("=" * 70)

    ref_results = await generate_reference_images(
        ref_manager=ref_manager,
        image_gen=image_gen,
        characters=CHARACTERS,
        style_config=style_config,
        output_dir=REFERENCE_DIR
    )

    ref_success_count = sum(1 for r in ref_results.values() if r.get("success"))
    print(f"\n参考图生成完成: {ref_success_count}/{len(CHARACTERS)}")

    # Step 2: 生成故事图
    print("\n" + "=" * 70)
    print("Step 2: 生成故事图 (带参考图)")
    print("=" * 70)

    results = []
    prompts_log = []

    print(f"\n开始生成 {len(FULL_STORY_SHOTS)} 张图...")
    print("-" * 70)

    for shot in FULL_STORY_SHOTS:
        shot_id = shot["shot_id"]
        scene = shot["scene"]
        is_memory = shot.get("is_memory", False)
        is_chase = shot.get("is_chase", False)
        emphasis = shot.get("emphasis")
        char_ids = shot.get("characters", [])

        print(f"\n[Shot {shot_id:02d}] {scene}")
        if is_memory:
            print(f"  🌅 记忆场景（明亮自然光 - 风格对比）")
        if is_chase:
            print(f"  🏃 追逐场景（动态效果）")
        if emphasis:
            print(f"  🔴 情感强调: {emphasis}")
        if shot["text_type"] == "none":
            print(f"  🔇 无文字场景")
        if char_ids:
            print(f"  👥 角色: {', '.join(char_ids)}")
        else:
            print(f"  👥 角色: (无)")

        # 收集参考图
        reference_images = []
        for char_id in char_ids:
            ref_result = ref_results.get(char_id)
            if ref_result and ref_result.get("success"):
                fullbody_img = ref_result.get("fullbody_image")
                if fullbody_img:
                    reference_images.append(fullbody_img)
                    print(f"  📷 使用 {char_id} 参考图")

        char_instruction = build_character_reference_instruction(char_ids)

        prompts_log.append({
            "shot_id": shot_id,
            "scene": scene,
            "text_type": shot["text_type"],
            "speaker_position": shot["speaker_position"],
            "chinese_text": shot["chinese_text"],
            "is_memory": is_memory,
            "is_chase": is_chase,
            "emphasis": emphasis,
            "characters": char_ids,
            "reference_count": len(reference_images),
            "prompt": shot["image_prompt"]
        })

        result = await generate_image_with_refs(
            prompt=shot["image_prompt"],
            shot_id=shot_id,
            output_dir=NO_TEXT_DIR,
            reference_images=reference_images,
            char_instruction=char_instruction
        )

        if result["success"]:
            print(f"  ✅ 图像生成成功 (使用 {result.get('ref_count', 0)} 张参考图)")

            original_image = result["pil_image"]

            # 对话类型且有角色时检测位置
            if shot["text_type"] == "dialogue" and len(char_ids) > 0:
                ref_paths = {}
                for cid in char_ids:
                    ref_result = ref_results.get(cid)
                    if ref_result and ref_result.get("fullbody_path"):
                        ref_paths[cid] = ref_result["fullbody_path"]

                if ref_paths:
                    char_list = [{"id": k, **v} for k, v in CHARACTERS.items() if k in char_ids]

                    detected_positions = await detect_character_positions(
                        shot_image=original_image,
                        characters_in_scene=char_ids,
                        reference_images=ref_paths,
                        characters=char_list,
                        debug_mode=False
                    )

                    if detected_positions:
                        shot["bubble_positions"] = detected_positions

            # 叠加文字
            processed_image = text_service.process_shot(original_image, shot)

            with_text_path = WITH_TEXT_DIR / f"shot_{shot_id:02d}.png"
            processed_image.save(with_text_path)
            print(f"  ✅ 文字叠加完成: {with_text_path.name}")

            comparison = create_comparison(original_image, processed_image, f"Shot {shot_id:02d}")
            comparison_path = COMPARISON_DIR / f"shot_{shot_id:02d}_comparison.png"
            comparison.save(comparison_path)

            results.append({
                "shot_id": shot_id,
                "scene": scene,
                "success": True,
                "no_text_path": result["image_path"],
                "with_text_path": str(with_text_path),
                "comparison_path": str(comparison_path),
                "is_memory": is_memory,
                "is_chase": is_chase,
                "emphasis": emphasis,
                "characters": char_ids,
                "reference_count": result.get("ref_count", 0)
            })
        else:
            print(f"  ❌ 失败: {result['error']}")
            results.append({
                "shot_id": shot_id,
                "scene": scene,
                "success": False,
                "error": result["error"]
            })

        await asyncio.sleep(2)

    # 保存日志
    prompts_path = OUTPUT_DIR / "prompts_log.json"
    with open(prompts_path, 'w', encoding='utf-8') as f:
        json.dump(prompts_log, f, ensure_ascii=False, indent=2)

    results_path = OUTPUT_DIR / "results.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    ref_log = {}
    for char_id, result in ref_results.items():
        ref_log[char_id] = {
            "success": result.get("success", False),
            "portrait_path": result.get("portrait_path"),
            "fullbody_path": result.get("fullbody_path"),
            "error": result.get("error")
        }

    ref_log_path = OUTPUT_DIR / "reference_images_log.json"
    with open(ref_log_path, 'w', encoding='utf-8') as f:
        json.dump(ref_log, f, ensure_ascii=False, indent=2)

    # 统计
    success_count = sum(1 for r in results if r.get("success"))
    memory_count = sum(1 for r in results if r.get("is_memory") and r.get("success"))
    chase_count = sum(1 for r in results if r.get("is_chase") and r.get("success"))
    emphasis_count = sum(1 for r in results if r.get("emphasis") and r.get("success"))
    with_refs_count = sum(1 for r in results if r.get("reference_count", 0) > 0)

    print("\n" + "=" * 70)
    print("测试完成! 故事C《最后的记忆商人》- 赛博朋克风格")
    print("=" * 70)
    print(f"参考图生成: {ref_success_count}/{len(CHARACTERS)}")
    print(f"故事图生成: {success_count}/{len(FULL_STORY_SHOTS)}")
    print(f"使用参考图的shot: {with_refs_count}/{len(FULL_STORY_SHOTS)}")
    print(f"记忆场景: {memory_count}/1 (Shot 14 - 明亮自然光对比)")
    print(f"追逐场景: {chase_count}/2 (Shots 10-11)")
    print(f"情感强调: {emphasis_count}/0")

    print(f"\n输出目录:")
    print(f"  参考图: {REFERENCE_DIR}")
    print(f"  无文字图片: {NO_TEXT_DIR}")
    print(f"  叠加文字后: {WITH_TEXT_DIR}")
    print(f"  对比图: {COMPARISON_DIR}")

    print("\n验收要点 (TASK-VERIFY-001-C):")
    print("  1. 角色一致性：林夜(银色左眼义眼+蓝光)在所有图中可识别")
    print("  2. 角色一致性：老陈(白发/蓝色工装/金属拐杖)在所有图中可识别")
    print("  3. 角色一致性：凯拉(双红眼义眼/银白短发/金属右臂)在所有图中可识别")
    print("  4. 赛博朋克风格：霓虹灯(粉/青/紫)、湿地反光、全息广告、暗黑氛围")
    print("  5. 科技元素：赛博义眼、神经接口、金属义肢正确渲染")
    print("  6. 记忆对比：Shot 14 明亮自然光风格与其他暗黑镜头形成强烈对比")
    print("  7. 追逐场景：Shot 10-11 的动态感和紧迫感")
    print("  8. 情感表达：紧张、绝望、希望等情绪的面部表情")
    print("  9. 泡泡位置：AI推荐位置不遮挡角色脸部")

    return results

# =============================================================================
# 入口
# =============================================================================

if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
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

    asyncio.run(run_story_c_cyberpunk_test())
