"""
条漫完整故事测试脚本 - 故事B《断剑》
古装武侠 + Chinese Ink Wash (水墨) 风格

多风格通用性验证测试 (TASK-VERIFY-001-C)

故事脚本: docs/COMIC_STORY_B_WUXIA_INK_SCRIPT.md
风格: Chinese Ink Wash Painting (水墨画)

作者: @Backend
日期: 2026-01-27
"""

import asyncio
import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass, field

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

# 输出目录 - Story B: Wuxia Ink 武侠水墨
OUTPUT_DIR = Path(__file__).parent.parent / "test_output" / "comic_full_story_v2_wuxia_ink"
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
# 角色定义 (4个角色: 老剑客、年轻剑客、徒弟、仇人)
# =============================================================================

CHARACTERS = {
    # 老剑客/师父 - 白川 (60岁)
    "master_old": {
        "id": "master_old",
        "name": "白川",
        "name_en": "Bai Chuan",
        "character_type": "human",
        "gender": "male",
        "age_appearance": "elderly",
        "physical": {
            "height": "tall",
            "build": "thin but wiry, lean from years of martial arts",
            "skin_tone": "weathered pale, like aged parchment",
            "face_shape": "angular with high cheekbones, gaunt",
            "hair_color": "pure white",
            "hair_style": "long white hair tied in traditional topknot (发髻), some loose strands framing face",
            "hair_texture": "fine, flowing",
            "eye_color": "deep gray, almost black",
            "eye_shape": "narrow, piercing",
            "eye_description": "deep gray piercing eyes with years of wisdom and regret",
            "eyebrows": "long white eyebrows, slightly drooping at ends",
            "nose": "straight, prominent bridge",
            "lips": "thin, often pressed in contemplation",
            "distinctive_marks": ["deep vertical furrow between brows", "old sword scar on left cheek", "long flowing white beard reaching chest"]
        },
        "clothing": {
            "top": "plain undyed hemp robe (麻布长袍) with wide sleeves, faded to cream-gray, simple cloth belt at waist",
            "inner": "simple white inner robe visible at collar",
            "bottom": "matching loose hemp trousers",
            "footwear": "black cloth shoes (布鞋)",
            "accessories": ["ancient sword with worn leather-wrapped hilt at waist", "jade pendant on simple cord"],
            "style": "ascetic swordsman hermit"
        }
    },
    # 年轻白川 (30岁) - 回忆场景用
    "master_young": {
        "id": "master_young",
        "name": "白川(年轻)",
        "name_en": "Bai Chuan (Young)",
        "character_type": "human",
        "gender": "male",
        "age_appearance": "adult",
        "physical": {
            "height": "tall",
            "build": "athletic and strong, peak martial arts condition",
            "skin_tone": "healthy fair with slight tan",
            "face_shape": "angular with high cheekbones, fuller than old age",
            "hair_color": "jet black with bluish sheen",
            "hair_style": "long black hair tied in high topknot, sleek and well-groomed",
            "hair_texture": "thick, lustrous",
            "eye_color": "dark gray, intense and confident",
            "eye_shape": "narrow, sharp with arrogant gleam",
            "eye_description": "dark gray sharp eyes with confident arrogant gleam",
            "eyebrows": "thick black, angled upward showing pride",
            "nose": "straight, prominent bridge",
            "lips": "full, often curved in confident smirk",
            "distinctive_marks": ["no beard, clean-shaven jaw", "no scar yet"]
        },
        "clothing": {
            "top": "fine dark blue silk robe (深蓝绸袍) with subtle wave pattern, silver-trimmed edges",
            "inner": "white silk inner robe",
            "bottom": "matching dark blue silk trousers",
            "footwear": "black leather boots",
            "accessories": ["famous sword 寒霜 (Frost) at waist with gleaming blade", "jade hairpin holding topknot"],
            "style": "renowned swordsman at height of fame"
        }
    },
    # 徒弟 - 林风 (25岁)
    "disciple": {
        "id": "disciple",
        "name": "林风",
        "name_en": "Lin Feng",
        "character_type": "human",
        "gender": "male",
        "age_appearance": "young_adult",
        "physical": {
            "height": "medium-tall",
            "build": "lean and athletic, lithe swordsman build",
            "skin_tone": "healthy fair with slight warmth",
            "face_shape": "oval with defined jawline",
            "hair_color": "jet black",
            "hair_style": "high ponytail (高马尾) tied with white ribbon, some loose strands",
            "hair_texture": "thick and slightly wavy",
            "eye_color": "bright brown, earnest",
            "eye_shape": "almond, wide and clear",
            "eye_description": "bright brown earnest eyes full of determination",
            "eyebrows": "straight and thick, showing determination",
            "nose": "straight, youthful",
            "lips": "natural, often set in determined expression",
            "distinctive_marks": ["small scar on right hand from training"]
        },
        "clothing": {
            "top": "deep blue martial arts jacket (蓝色劲装) with mandarin collar, fitted cut for movement",
            "inner": "white inner shirt visible at collar",
            "bottom": "dark gray fitted trousers tucked into boots",
            "footwear": "black leather boots with cloth wrapping at ankles",
            "accessories": ["white cloth belt (白色束带)", "plain steel sword at waist", "white hair ribbon"],
            "style": "disciplined martial arts student"
        }
    },
    # 蒙面仇人 - 周沧 (50岁)
    "enemy": {
        "id": "enemy",
        "name": "周沧",
        "name_en": "Zhou Cang",
        "character_type": "human",
        "gender": "male",
        "age_appearance": "middle_aged",
        "physical": {
            "height": "medium",
            "build": "lean but powerful, compact and dangerous",
            "skin_tone": "weathered tan, sun-damaged",
            "face_shape": "square jaw, harsh features",
            "hair_color": "iron gray with black streaks",
            "hair_style": "pulled back tight, hidden under hood/mask",
            "hair_texture": "coarse",
            "eye_color": "dark brown, filled with cold hatred",
            "eye_shape": "narrow, cold",
            "eye_description": "narrow dark brown eyes filled with three decades of cold hatred",
            "eyebrows": "thick, perpetually furrowed",
            "nose": "crooked, broken once",
            "lips": "thin, cruel set",
            "distinctive_marks": ["deep crow's feet from years of hatred", "burn scar on left hand"]
        },
        "clothing": {
            "top": "black night-traveling clothes (黑色夜行衣), fitted and practical",
            "face_covering": "black cloth mask covering lower face, black hood covering hair",
            "bottom": "black fitted trousers",
            "footwear": "soft black cloth shoes for silent movement",
            "accessories": ["thin black sword (细长黑剑) on back", "throwing knives hidden in sleeves"],
            "style": "assassin/avenger"
        }
    }
}

# =============================================================================
# Shot到角色的映射
# =============================================================================

SHOT_CHARACTER_MAPPING = {
    1: ["master_old"],
    2: ["master_old"],
    3: ["master_old", "master_young"],
    4: ["master_young"],  # 回忆
    5: ["master_young"],  # 回忆
    6: ["master_young"],  # 回忆
    7: ["disciple"],
    8: ["enemy"],
    9: ["master_old", "disciple", "enemy"],
    10: ["master_old", "enemy"],  # 动作
    11: ["master_old", "enemy"],  # 动作
    12: ["master_old", "enemy"],
    13: ["master_old", "disciple"],
    14: ["enemy"],
    15: ["disciple"],
}

# =============================================================================
# 风格定义 (Chinese Ink Wash 水墨画)
# =============================================================================

INK_WASH_STYLE_PREFIX = """
STYLE: Chinese Ink Wash Painting (水墨画)

Traditional Chinese ink wash aesthetic (sumi-e inspired).
Brush stroke textures, ink gradients from deep black to pale gray.
Rice paper texture background with intentional white space (留白).
Minimal color - primarily black, gray, white with occasional subtle warm accents.
Flowing, dynamic brush energy. Atmospheric perspective through ink density.
Characters rendered with bold decisive strokes. Backgrounds fade into mist.

MUST INCLUDE: brush stroke texture, ink wash gradients, rice paper feel, intentional white space, atmospheric depth, flowing lines, traditional Chinese aesthetic
DO NOT USE: photorealistic, colorful, neon, 3D render, Western art style, digital art look, sharp clean lines, bright saturated colors

"""

MEMORY_SCENE_TREATMENT = """
MEMORY SCENE TREATMENT:
- Warmer sepia-tinted ink tones
- Softer brush strokes with more blur
- Dreamlike quality with hazier edges
- Lighter overall ink density
- Subtle golden warmth mixed into grays
"""

ACTION_SCENE_TREATMENT = """
ACTION SCENE TREATMENT:
- Dynamic brush strokes showing movement
- Ink splatter effects for impact
- White space used to represent sword flash/speed
- Bamboo leaves scattered in motion
- Energy lines through negative space
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
            hair_desc = f"{physical.get('hair_color', '')} {physical.get('hair_style', '')}"
            instructions.append(f"  - Hair: {hair_desc.strip()}")
            if clothing.get('top'):
                instructions.append(f"  - Clothing: {clothing['top']}")
            if physical.get('distinctive_marks'):
                marks = physical['distinctive_marks']
                if isinstance(marks, list):
                    instructions.append(f"  - Distinctive: {', '.join(marks[:2])}")

    instructions.append("")
    instructions.append("IMPORTANT: Maintain consistent character appearance throughout the story.")

    return "\n".join(instructions)

# =============================================================================
# 15图完整脚本定义 (武侠水墨风格)
# =============================================================================

FULL_STORY_SHOTS = [
    # Shot 01: 雪夜独坐
    {
        "shot_id": 1,
        "scene": "雪夜独坐 - 山间凉亭",
        "text_type": "narration",
        "speaker_position": "top",
        "chinese_text": "三十年了，那一剑，始终刺在我心里。",
        "characters": ["master_old"],
        "image_prompt": f"""{INK_WASH_STYLE_PREFIX}
---

A distant view of a simple wooden pavilion (凉亭) in a mountain bamboo grove during heavy snowfall. An elderly swordsman with long white hair tied in topknot and flowing white beard sits alone inside, his back slightly hunched, gazing at an ancient sword across his lap.

The bamboo stalks are rendered in bold vertical brush strokes, fading into misty white at the top. Snow falls as scattered white dots against the gray ink sky. The pavilion is a dark silhouette providing shelter from the elements.

The old man's hemp robe drapes heavily, his posture conveying decades of solitude and regret. Moonlight filters through clouds, creating subtle silver highlights on the snow.

EMOTIONAL ATMOSPHERE:
Deep solitude, heavy memories, the weight of three decades of guilt.
The vast empty space around the small pavilion emphasizes isolation.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 02: 凝视断剑
    {
        "shot_id": 2,
        "scene": "凝视断剑 - 凉亭内特写",
        "text_type": "thought",
        "speaker_position": "bottom",
        "chinese_text": "这道裂痕，是我亲手造成的...",
        "characters": ["master_old"],
        "image_prompt": f"""{INK_WASH_STYLE_PREFIX}
---

Close-up view of an elderly swordsman's weathered hands holding an ancient sword. The blade has a visible crack running along its length - a permanent wound in the steel. His long white beard partially visible, his gaunt face with scar on left cheek shown in profile, piercing gray eyes filled with sorrow gazing at the damaged blade.

The sword's worn leather-wrapped hilt shows decades of use. His hands are thin with prominent veins, trembling slightly. Snow continues falling outside the pavilion frame.

Ink rendering focuses on the hands and sword with fine detailed brush work, while the background fades to misty gray. A single tear track suggested on his weathered cheek.

EMOTIONAL ATMOSPHERE:
Guilt, regret, the physical reminder of an irreversible mistake.
The crack in the sword mirrors the crack in his heart.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 03: 记忆浮现
    {
        "shot_id": 3,
        "scene": "记忆浮现 - 雪花中虚影",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": '那一年，我还是江湖人人敬仰的"白川一剑"...',
        "characters": ["master_old", "master_young"],
        "image_prompt": f"""{INK_WASH_STYLE_PREFIX}
---

A transition scene showing the old swordsman looking toward swirling snow, within which a ghostly vision appears - his younger self. The old man with white hair and beard sits in the pavilion corner (rendered in solid dark ink), while in the snowy void before him, a translucent figure of a young swordsman with black hair in high topknot emerges from the snowflakes.

The young vision wears fine dark blue silk robes, standing proudly with hand on famous sword, expression confident and arrogant. This phantom is rendered in lighter, hazier brush strokes - barely there, a memory taking shape.

The contrast between the hunched old man and his proud young ghost creates visual tension. Snowflakes swirl between them like the years that have passed.

EMOTIONAL ATMOSPHERE:
Nostalgia, painful memory surfacing, the unbridgeable gap between past and present self.
Past glory haunting present regret.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 04: 年少意气 (回忆)
    {
        "shot_id": 4,
        "scene": "年少意气 - 三十年前客栈",
        "text_type": "dialogue",
        "speaker_position": "center",
        "chinese_text": "天下剑客，谁敢与我一战？",
        "is_memory": True,
        "characters": ["master_young"],
        "image_prompt": f"""{INK_WASH_STYLE_PREFIX}
{MEMORY_SCENE_TREATMENT}
---

Interior of a bustling ancient Chinese tavern (客栈). A young swordsman with jet black hair in high topknot stands confidently in the center, one hand on his famous gleaming sword. He wears fine dark blue silk robes with silver trim, his posture radiating arrogance and supreme confidence. His narrow eyes gleam with pride.

Around him, other martial artists sit at wooden tables, looking up with mixed expressions of admiration and wariness. Lanterns hang from wooden beams. Wine jars and cups on tables. The atmosphere is lively but tense with anticipation.

The young Bai Chuan's confident smirk and raised chin show a man who believes himself invincible. His sword hand rests casually but ready.

EMOTIONAL ATMOSPHERE:
Peak arrogance, supreme confidence, the hubris before the fall.
A champion who has never known defeat.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 05: 意外发生 (回忆)
    {
        "shot_id": 5,
        "scene": "意外发生 - 剑光闪过",
        "text_type": "narration",
        "speaker_position": "top",
        "chinese_text": "那一剑，我收不住了。",
        "is_memory": True,
        "characters": ["master_young"],
        "image_prompt": f"""{INK_WASH_STYLE_PREFIX}
{MEMORY_SCENE_TREATMENT}
---

A dynamic frozen moment of tragedy. The young swordsman with black hair has lunged forward, his gleaming sword extended in a thrust. His face shows the first flash of shock as he realizes - too late - that his blade has found the wrong target.

The composition uses dramatic white space to represent the sword's deadly path. Motion lines in ink suggest the unstoppable speed of the strike. The young man's dark blue robes billow with arrested momentum.

Only hints of the victim visible at the edge of frame - a youthful figure, a spray of ink suggesting blood. The focus is on the swordsman's expression transforming from triumph to horror.

EMOTIONAL ATMOSPHERE:
The split-second when everything changes. Triumph turning to tragedy.
The point of no return.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 06: 好友之弟倒下 (回忆 + 情感强调)
    {
        "shot_id": 6,
        "scene": "好友之弟倒下 - 俯视绝望",
        "text_type": "thought",
        "speaker_position": "bottom",
        "chinese_text": "他才十六岁...是周沧的亲弟弟...！！！",
        "is_memory": True,
        "emphasis": "red_highlight",
        "characters": ["master_young"],
        "image_prompt": f"""{INK_WASH_STYLE_PREFIX}
{MEMORY_SCENE_TREATMENT}

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

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 07: 徒弟练剑 (无文字)
    {
        "shot_id": 7,
        "scene": "徒弟练剑 - 山间小屋",
        "text_type": "none",
        "speaker_position": "none",
        "chinese_text": "",
        "characters": ["disciple"],
        "image_prompt": f"""{INK_WASH_STYLE_PREFIX}
---

A young swordsman with jet black hair in high ponytail tied with white ribbon practices sword forms in a clearing before a modest mountain hut. He wears a deep blue martial arts jacket with white cloth belt, his stance wide and sword extended in a precise horizontal cut.

The morning sun creates dappled light through bamboo leaves. The simple wooden hut has a thatched roof, its door open. A small vegetable garden grows nearby. The scene conveys peace and disciplined training.

Lin Feng's expression is focused, determined, his bright brown eyes fixed on an imaginary opponent. His movements are rendered with flowing brush strokes suggesting grace and skill. White ribbon flutters with the motion.

EMOTIONAL ATMOSPHERE:
Youth, dedication, morning tranquility before the storm.
A brief moment of peace that will soon be shattered.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 08: 黑衣人现身
    {
        "shot_id": 8,
        "scene": "黑衣人现身 - 竹林边缘",
        "text_type": "dialogue",
        "speaker_position": "top",
        "chinese_text": "白川，三十年了，我终于找到你了。",
        "characters": ["enemy"],
        "image_prompt": f"""{INK_WASH_STYLE_PREFIX}
---

Low angle view looking up at a menacing figure standing on a rocky outcrop at the edge of the bamboo forest. A man in all-black night-traveling clothes, face covered by black cloth mask, only his cold hate-filled eyes visible. A thin black sword is strapped to his back.

His black robes and hood merge with the ink-dark shadows of the forest behind him. He stands utterly still, radiating deadly intent. The bamboo stalks frame him like prison bars - or like swords.

Wind rustles his clothes slightly. His narrow eyes burn with three decades of hatred, fixed on something below (the hut, off-frame).

EMOTIONAL ATMOSPHERE:
Menace, long-awaited confrontation, the arrival of retribution.
Death has come calling.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 09: 师徒对峙仇人
    {
        "shot_id": 9,
        "scene": "师徒对峙仇人 - 三角构图",
        "text_type": "dialogue",
        "speaker_position": "left",
        "chinese_text": "林风，退下。这是我的债，该我来还。",
        "characters": ["master_old", "disciple", "enemy"],
        "image_prompt": f"""{INK_WASH_STYLE_PREFIX}
---

A tense three-way standoff in front of the mountain hut. Triangle composition with three figures.

In the foreground left, the old swordsman with white hair, beard, and hemp robe has stepped out from the hut, his ancient cracked sword drawn. His weathered face shows grim acceptance, not fear. He positions himself protectively before his disciple.

Behind him center-right, the young disciple in blue martial jacket has drawn his sword, his expression showing confusion and readiness to fight. His stance is defensive but alert.

Facing them from a distance, the black-clad masked figure stands with hand on his sword hilt, radiating cold menace. Only his hate-filled eyes visible above the mask.

The bamboo forest provides the backdrop. Tension crackles in the white space between them.

EMOTIONAL ATMOSPHERE:
Confrontation, protection, fate arriving.
The old man facing his past to protect his future (the disciple).

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 10: 竹林决战起手 (动作场景)
    {
        "shot_id": 10,
        "scene": "竹林决战起手",
        "text_type": "narration",
        "speaker_position": "top",
        "chinese_text": "三十年的恩怨，就在今夜了结。",
        "is_action": True,
        "characters": ["master_old", "enemy"],
        "image_prompt": f"""{INK_WASH_STYLE_PREFIX}
{ACTION_SCENE_TREATMENT}
---

Wide shot of the bamboo forest clearing. Two swordsmen face each other across a gap of several meters. The old swordsman in hemp robes on the left, cracked sword raised. The black-clad avenger on the right, thin black sword drawn.

Both are captured in the instant before movement - bodies coiled with potential energy. The space between them is charged with killing intent, rendered as swirling ink patterns and scattered bamboo leaves suspended mid-fall.

Moonlight cuts through the bamboo canopy, creating dramatic strips of light and shadow. The bamboo stalks form vertical lines of varying ink density, creating depth. Snow begins to fall lightly.

EMOTIONAL ATMOSPHERE:
The calm before violence, thirty years distilled to this moment.
Two men who have waited for this night.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 11: 激战中 (动作场景，无文字)
    {
        "shot_id": 11,
        "scene": "激战中 - 剑光交错",
        "text_type": "none",
        "speaker_position": "none",
        "chinese_text": "",
        "is_action": True,
        "characters": ["master_old", "enemy"],
        "image_prompt": f"""{INK_WASH_STYLE_PREFIX}
{ACTION_SCENE_TREATMENT}
---

The duel at its peak intensity. Two figures blur together in a dance of death, their swords meeting in a shower of sparks rendered as white spots against dark ink. The white-haired old man and black-clad avenger are interlocked mid-strike.

Bamboo leaves explode outward from the force of their clash. Several bamboo stalks have been cut clean through, toppling. Ink splatter radiates from the center of combat, suggesting impact and violence.

Motion blur and dynamic brush strokes make the figures almost merge into abstract shapes of conflict - white robes and black robes, two swords crossed. The combat is rendered more as energy and motion than clear detail.

EMOTIONAL ATMOSPHERE:
Peak violence, skills perfectly matched, life and death balanced on blade's edge.
Two masters giving everything they have.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 12: 身中数剑
    {
        "shot_id": 12,
        "scene": "身中数剑 - 战斗尾声",
        "text_type": "dialogue",
        "speaker_position": "left",
        "chinese_text": "周沧...我等这一剑...等了三十年...",
        "characters": ["master_old", "enemy"],
        "image_prompt": f"""{INK_WASH_STYLE_PREFIX}
---

The aftermath of the duel. The old swordsman stands barely upright, his hemp robe torn and dark with blood from multiple wounds. Several throwing knives protrude from his body. Yet his eyes remain clear, fixed on his opponent, his cracked sword still gripped in one hand.

Opposite him, the black-clad man has also taken damage - his mask torn partially away, revealing a cruel mouth set in grimace. He breathes heavily, wounded but less critically.

Both men are surrounded by fallen bamboo, scattered leaves, disturbed snow now stained dark. The old man's white hair has come loose, streaming behind him. Blood drips from his wounds to the snow.

EMOTIONAL ATMOSPHERE:
Defiance in defeat, a man who has achieved what he needed to.
Speaking his enemy's name at last - acknowledging their shared history.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 13: 断剑托付
    {
        "shot_id": 13,
        "scene": "断剑托付 - 徒弟赶到",
        "text_type": "dialogue",
        "speaker_position": "left",
        "chinese_text": "这把剑...和我欠下的债...都交给你了...",
        "characters": ["master_old", "disciple"],
        "image_prompt": f"""{INK_WASH_STYLE_PREFIX}
---

The young disciple kneels in the snow, cradling his fallen master in his arms. Lin Feng's face shows anguish, tears streaming down his cheeks. His blue martial jacket is stained with his master's blood.

The old swordsman looks up at his student with peaceful, fading eyes. With trembling hands, he offers his cracked sword - the blade with the thirty-year-old wound. His white beard is matted with blood, but his expression holds no regret, only a gentle passing of responsibility.

Snow falls heavily around them. The wounded enemy stands at a distance, watching (suggested in background). Fallen bamboo and disturbed snow tell the story of the battle just ended.

EMOTIONAL ATMOSPHERE:
Transmission of legacy, peaceful death, a burden passed to the next generation.
The student becoming the master.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 14: 真相大白
    {
        "shot_id": 14,
        "scene": "真相大白 - 周沧摘面具",
        "text_type": "dialogue",
        "speaker_position": "center",
        "chinese_text": "白川...这三十年，你比我更痛苦...",
        "characters": ["enemy"],
        "image_prompt": f"""{INK_WASH_STYLE_PREFIX}
---

Close-up of the avenger removing his mask and hood, revealing his face fully for the first time. Zhou Cang is a man of fifty with iron-gray hair, square jaw, and harsh weathered features. His crooked nose was broken long ago. Deep crow's feet mark decades of hatred.

But his expression is transforming. The cold hatred in his eyes is cracking, replaced by something more complex - grief, recognition of shared pain, reluctant respect. Tears cut tracks through the dirt and blood on his face.

His black clothes are torn, wounds visible. He holds the torn mask in one trembling hand. Behind him, snow falls on the battlefield. In the soft-focus background, the disciple cradles the fallen master.

EMOTIONAL ATMOSPHERE:
The lifting of masks - literal and emotional. Recognition that hatred has not brought peace.
Realizing the enemy suffered as much as you.

{TEXT_FREE_REQUIREMENT}
"""
    },
    # Shot 15: 剑断义存
    {
        "shot_id": 15,
        "scene": "剑断义存 - 大远景天地苍茫",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "剑可断，义不可断。师父，我明白了。",
        "characters": ["disciple"],
        "image_prompt": f"""{INK_WASH_STYLE_PREFIX}
---

Vast landscape composition showing a lone figure standing in a snow-covered mountain clearing. The young swordsman Lin Feng, now bearing his master's legacy, stands with back to viewer, holding the cracked sword before him - examining the wound in the blade that tells its story.

The world stretches out around him - misty mountains fading into white, bamboo forest reduced to gray shadows, snow falling from an endless pale sky. The figure is small against the immensity of landscape, yet his posture shows resolve, not defeat.

Dawn light begins to warm the eastern horizon, the faintest hint of gold among the grays. A new day, a new beginning. The white ribbon in his ponytail flutters in the wind.

In the snow at his feet, two sets of departing footprints lead away - Zhou Cang has gone, the feud ended. A mound of disturbed snow suggests a fresh grave.

EMOTIONAL ATMOSPHERE:
Inheritance, continuation, hope emerging from tragedy.
The sword may be broken, but righteousness endures.

{TEXT_FREE_REQUIREMENT}
"""
    }
]

# =============================================================================
# 注意：TextOverlayService已迁移到 app/services/text_overlay_service.py
# 本文件导入主服务以保持向后兼容
# =============================================================================

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
    print("生成角色参考图 (4个角色)")
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

async def run_story_b_wuxia_ink_test():
    """运行故事B武侠水墨测试"""

    print("=" * 70)
    print("条漫完整故事测试 - 故事B《断剑》")
    print("15张图完整故事，Chinese Ink Wash (水墨) 风格")
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

    # 风格配置 - 水墨风格
    style_config = ProjectStyleConfig(
        style_preset="ink",
        color_palette="monochrome",
        dominant_colors=["ink_black", "rice_paper_white", "light_gray"],
        lighting_style="atmospheric",
        rendering="brush_stroke"
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
        is_action = shot.get("is_action", False)
        emphasis = shot.get("emphasis")
        char_ids = shot.get("characters", [])

        print(f"\n[Shot {shot_id:02d}] {scene}")
        if is_memory:
            print(f"  📷 回忆场景（暖色调处理）")
        if is_action:
            print(f"  ⚔️ 动作场景（动态笔触）")
        if emphasis:
            print(f"  🔴 情感强调: {emphasis}")
        if shot["text_type"] == "none":
            print(f"  🔇 无文字场景")
        print(f"  👥 角色: {', '.join(char_ids)}")

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
            "is_action": is_action,
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
                "is_action": is_action,
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
    action_count = sum(1 for r in results if r.get("is_action") and r.get("success"))
    emphasis_count = sum(1 for r in results if r.get("emphasis") and r.get("success"))
    with_refs_count = sum(1 for r in results if r.get("reference_count", 0) > 0)

    print("\n" + "=" * 70)
    print("测试完成! 故事B《断剑》- 武侠水墨风格")
    print("=" * 70)
    print(f"参考图生成: {ref_success_count}/{len(CHARACTERS)}")
    print(f"故事图生成: {success_count}/{len(FULL_STORY_SHOTS)}")
    print(f"使用参考图的shot: {with_refs_count}/{len(FULL_STORY_SHOTS)}")
    print(f"回忆场景: {memory_count}/3 (Shots 04-06)")
    print(f"动作场景: {action_count}/2 (Shots 10-11)")
    print(f"情感强调: {emphasis_count}/1 (Shot 06)")

    print(f"\n输出目录:")
    print(f"  参考图: {REFERENCE_DIR}")
    print(f"  无文字图片: {NO_TEXT_DIR}")
    print(f"  叠加文字后: {WITH_TEXT_DIR}")
    print(f"  对比图: {COMPARISON_DIR}")

    print("\n验收要点 (TASK-VERIFY-001-C):")
    print("  1. 角色一致性：老剑客(白发/麻布袍/左颊疤痕)在所有图中可识别")
    print("  2. 年龄一致性：master_young 与 master_old 特征相符")
    print("  3. 古装服饰：符合中国古代剑客形象，无现代元素")
    print("  4. 水墨风格：笔触感、留白、墨色浓淡层次、宣纸质感")
    print("  5. 情感表达：悲壮、愧疚、传承等情绪的面部表情")
    print("  6. 动作场景：剑术对决的动态感 (Shots 10-11)")
    print("  7. 回忆场景：暖色调柔光处理 (Shots 04-06)")
    print("  8. 红色强调：Shot 06 '！！！' 红色高亮")
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

    asyncio.run(run_story_b_wuxia_ink_test())
