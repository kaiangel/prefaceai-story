"""
条漫完整故事测试脚本 V2 - 《最后一碗面》
集成 ReferenceImageManager 提升角色一致性

变更说明 (对比 v1):
1. 添加 ReferenceImageManager 为5个角色变体生成参考图
2. 生成 shot 时传入对应角色的参考图
3. 优化红色强调检测（同时支持 !!! 和 ！！！）
4. 继续使用 Flash 模型（创始人指示：条漫插画不需要Pro）

故事脚本: docs/COMIC_FULL_STORY_SCRIPT.md
风格: Ghibli-inspired warm illustration

任务: TASK-FIX-002
作者: @Backend
日期: 2026-01-23
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

# 加载 .env 文件中的环境变量 (包括 ANTHROPIC_API_KEY, GEMINI_API_KEY 等)
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
USE_PRO_MODEL = False  # 创始人指示: 条漫插画风格继续用Flash

# 输出目录 - TASK-OPT-005-C 泡泡遮挡问题验收
OUTPUT_DIR = Path(__file__).parent.parent / "test_output" / "comic_full_story_v2_20260127_opt005"
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

# V2 字体大小
DEFAULT_FONT_SIZE = 42
SPEECH_BUBBLE_FONT_SIZE = 36
EMPHASIS_FONT_SIZE = 52
EMPHASIS_COLOR = "#FF4444"

# =============================================================================
# 角色定义 (ReferenceImageManager 格式)
# 5个角色变体: 女儿现在/童年/青春期 + 父亲现在/年轻
# =============================================================================

CHARACTERS = {
    # 女儿 - 现在 (28岁)
    "daughter_present": {
        "id": "daughter_present",
        "name": "陈小雨",
        "name_en": "Chen Xiaoyu",
        "character_type": "human",
        "gender": "female",
        "age_appearance": "young_adult",
        "physical": {
            "height": "medium",
            "build": "slim",
            "skin_tone": "fair with warm undertone",
            "face_shape": "oval with soft features",
            "hair_color": "black",
            "hair_style": "short modern bob cut slightly above shoulders",
            "hair_texture": "straight silky",
            "eye_color": "dark brown",
            "eye_shape": "almond",
            "eye_description": "gentle dark brown almond eyes",
            "eyebrows": "natural shaped",
            "nose": "small straight",
            "lips": "natural",
            "distinctive_marks": ["small mole below left ear"]
        },
        "clothing": {
            "top": "beige wool trench coat over crisp white blouse",
            "bottom": "black slim-fit dress pants",
            "footwear": "black leather flats",
            "accessories": ["small gold stud earrings", "simple black leather watch"],
            "style": "professional modern"
        }
    },
    # 女儿 - 童年 (10岁)
    "daughter_child": {
        "id": "daughter_child",
        "name": "陈小雨(童年)",
        "name_en": "Young Xiaoyu",
        "character_type": "human",
        "gender": "female",
        "age_appearance": "child",
        "physical": {
            "height": "short child height",
            "build": "slim child build",
            "skin_tone": "fair with warm undertone",
            "face_shape": "round childlike",
            "hair_color": "black",
            "hair_style": "twin pigtails tied with red ribbons",
            "hair_texture": "straight",
            "eye_color": "dark brown",
            "eye_shape": "large round",
            "eye_description": "bright innocent eyes full of energy",
            "eyebrows": "thin natural",
            "nose": "small button nose",
            "lips": "small",
            "distinctive_marks": []
        },
        "clothing": {
            "top": "white short-sleeve school uniform shirt with red neckerchief",
            "bottom": "navy blue pleated skirt",
            "footwear": "white canvas shoes",
            "accessories": [],
            "style": "school uniform"
        }
    },
    # 女儿 - 青春期 (18岁)
    "daughter_teen": {
        "id": "daughter_teen",
        "name": "陈小雨(青春期)",
        "name_en": "Teenage Xiaoyu",
        "character_type": "human",
        "gender": "female",
        "age_appearance": "teenager",
        "physical": {
            "height": "medium",
            "build": "slim teenager",
            "skin_tone": "fair with warm undertone",
            "face_shape": "more defined than childhood",
            "hair_color": "black",
            "hair_style": "high ponytail slightly messy",
            "hair_texture": "straight",
            "eye_color": "dark brown",
            "eye_shape": "almond",
            "eye_description": "rebellious defiant expression in eyes",
            "eyebrows": "natural slightly furrowed",
            "nose": "straight",
            "lips": "natural",
            "distinctive_marks": []
        },
        "clothing": {
            "top": "oversized gray hoodie",
            "bottom": "dark blue jeans with rips at knees",
            "footwear": "worn white sneakers",
            "accessories": [],
            "style": "casual rebellious"
        }
    },
    # 父亲 - 现在 (55岁)
    "father_present": {
        "id": "father_present",
        "name": "陈国强",
        "name_en": "Chen Guoqiang",
        "character_type": "human",
        "gender": "male",
        "age_appearance": "elderly",
        "physical": {
            "height": "medium",
            "build": "thin slightly frail",
            "skin_tone": "weathered tan",
            "face_shape": "angular with prominent cheekbones",
            "hair_color": "salt and pepper gray mostly white",
            "hair_style": "short neat thinning on top",
            "hair_texture": "straight",
            "eye_color": "dark brown",
            "eye_shape": "deep-set",
            "eye_description": "gentle dark brown warm eyes",
            "eyebrows": "bushy graying",
            "nose": "straight",
            "lips": "thin",
            "distinctive_marks": ["deep smile lines", "weathered hands"]
        },
        "clothing": {
            "top": "light blue hospital gown",
            "bottom": "hospital pants",
            "footwear": "hospital slippers",
            "accessories": ["hospital wristband", "reading glasses on cord around neck"],
            "style": "hospital patient"
        }
    },
    # 父亲 - 回忆 (40岁)
    "father_young": {
        "id": "father_young",
        "name": "陈国强(年轻)",
        "name_en": "Young Guoqiang",
        "character_type": "human",
        "gender": "male",
        "age_appearance": "middle_aged",
        "physical": {
            "height": "medium",
            "build": "sturdy strong from years of physical work",
            "skin_tone": "tanned from work",
            "face_shape": "fuller healthier",
            "hair_color": "jet black with few gray strands",
            "hair_style": "short neat",
            "hair_texture": "straight",
            "eye_color": "dark brown",
            "eye_shape": "warm",
            "eye_description": "warm hardworking content expression",
            "eyebrows": "thick black",
            "nose": "straight",
            "lips": "full",
            "distinctive_marks": []
        },
        "clothing": {
            "top": "white sleeveless undershirt with white cotton apron slightly stained from cooking",
            "bottom": "simple dark blue work pants",
            "footwear": "black cloth shoes",
            "accessories": ["white towel over shoulder"],
            "style": "working noodle shop owner"
        }
    }
}

# =============================================================================
# Shot到角色的映射
# =============================================================================

SHOT_CHARACTER_MAPPING = {
    1: ["daughter_present"],
    2: ["daughter_present"],
    3: ["daughter_present"],
    4: ["daughter_present", "father_present"],
    5: ["daughter_present"],
    6: ["daughter_present"],
    7: ["daughter_child", "father_young"],  # 回忆
    8: ["father_young"],                     # 回忆
    9: ["daughter_teen", "father_young"],    # 回忆
    10: ["daughter_teen", "father_young"],   # 回忆
    11: ["daughter_present"],
    12: ["daughter_present"],
    13: ["daughter_present"],
    14: ["daughter_present", "father_present"],
    15: ["daughter_present"],
}

# =============================================================================
# 风格定义 (Ghibli-inspired)
# =============================================================================

GHIBLI_STYLE_PREFIX = """
STYLE: Ghibli-inspired warm illustration

Hand-drawn animation aesthetic inspired by Studio Ghibli.
Soft watercolor textures, warm color palette dominated by cream yellow, soft white, and light brown tones.
Gentle lighting with golden hour warmth. Detailed backgrounds with lived-in feeling.
Characters with expressive but understated emotions. Nostalgic, heartwarming atmosphere.

MUST INCLUDE: hand-drawn style, soft edges, warm color palette, gentle lighting, detailed backgrounds, nostalgic atmosphere
DO NOT USE: photorealistic, 3D render, harsh lighting, neon colors, Korean webtoon style, sharp digital lines

"""

MEMORY_SCENE_TREATMENT = """
MEMORY SCENE TREATMENT:
- Soft golden glow around edges (vignette effect)
- Slightly desaturated colors compared to present-day scenes
- Dreamlike soft focus on background elements
- Warmer, more nostalgic color temperature
- Gentle lens flare or light particles floating in air
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
            # 添加关键外观提示
            physical = char.get('physical', {})
            clothing = char.get('clothing', {})
            hair_desc = f"{physical.get('hair_color', '')} {physical.get('hair_style', '')}"
            instructions.append(f"  - Hair: {hair_desc.strip()}")
            if clothing.get('top'):
                instructions.append(f"  - Clothing: {clothing['top']}")

    instructions.append("")
    instructions.append("IMPORTANT: Maintain consistent character appearance throughout the story.")

    return "\n".join(instructions)

# =============================================================================
# 15图完整脚本定义 (带角色映射)
# =============================================================================

FULL_STORY_SHOTS = [
    # Shot 01: 城市办公室 - 接到电话
    {
        "shot_id": 1,
        "scene": "城市办公室 - 接到电话",
        "text_type": "narration",
        "speaker_position": "top",
        "chinese_text": "那天接到电话，世界突然安静了",
        "characters": ["daughter_present"],
        "image_prompt": f"""{GHIBLI_STYLE_PREFIX}
---

A young professional woman with short black bob haircut, wearing a beige trench coat, standing in a modern office space. She is holding a phone to her ear, her expression shifting from neutral to deeply concerned. Her dark brown almond eyes widen slightly, lips parted in shock. One hand grips the phone tightly while the other hangs limply at her side.

The office has large windows letting in afternoon light, modern desks and computers visible in the soft-focus background. Warm afternoon sunlight streams through the windows, creating long shadows.

EMOTIONAL ATMOSPHERE:
The scene conveys sudden shock and dawning worry.
Character shows concerned, worried expression with widened eyes, slightly trembling hand holding phone, body frozen mid-motion.

{TEXT_FREE_REQUIREMENT}

"""
    },
    # Shot 02: 火车车窗 - 发呆
    {
        "shot_id": 2,
        "scene": "火车车窗 - 发呆",
        "text_type": "thought",
        "speaker_position": "bottom",
        "chinese_text": "三年没回去了...",
        "characters": ["daughter_present"],
        "image_prompt": f"""{GHIBLI_STYLE_PREFIX}
---

A young woman with short black bob haircut sitting by a train window, her reflection faintly visible in the glass. She wears a beige trench coat, her posture slightly slumped. Her face shows distant, melancholic expression as she gazes out at the passing countryside - green rice fields and distant mountains blurred by the train's motion.

Late afternoon golden light streams through the window, casting warm shadows across her face. The train interior has worn but clean seats in muted green fabric. Other passengers are barely visible in soft blur.

EMOTIONAL ATMOSPHERE:
The scene conveys quiet anxiety and guilt, lost in worried thoughts.
Character shows pensive, distant expression with unfocused gaze, slight furrow between brows, hands clasped tightly in lap.

{TEXT_FREE_REQUIREMENT}

"""
    },
    # Shot 03: 乡村街道 - 冷清的面馆
    {
        "shot_id": 3,
        "scene": "乡村街道 - 冷清的面馆",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "记忆中总是热气腾腾的地方，如今门可罗雀",
        "characters": ["daughter_present"],
        "image_prompt": f"""{GHIBLI_STYLE_PREFIX}
---

A quiet small-town street in rural China. In the center stands a modest noodle shop with a faded wooden sign (no text visible, weathered blank sign board). The shop entrance has traditional sliding doors, now closed. Dust motes float in the late afternoon light.

A young woman with short black bob haircut in beige trench coat stands before the closed shop, viewed from behind at a distance. Her small figure emphasizes the emptiness of the once-busy establishment. Wilted plants in pots flank the entrance. A few fallen leaves scattered on the ground.

The surrounding buildings are old but charming - whitewashed walls with dark wooden beams, traditional tile roofs. The street is nearly empty, creating a melancholic atmosphere.

NARRATIVE MOMENT:
This scene establishes the contrast between memory and present - the once-vibrant shop now quiet.
Visual focus on the closed shop and the daughter's small figure facing it.

{TEXT_FREE_REQUIREMENT}

"""
    },
    # Shot 04: 医院病房 - 见到父亲
    {
        "shot_id": 4,
        "scene": "医院病房 - 见到父亲",
        "text_type": "dialogue",
        "speaker_position": "left,right",
        "chinese_text": ["爸...", "回来啦，别担心，小毛病"],
        "characters": ["daughter_present", "father_present"],
        "image_prompt": f"""{GHIBLI_STYLE_PREFIX}
---

A hospital room scene. An elderly man with salt-and-pepper gray hair sits propped up in a hospital bed, wearing a light blue hospital gown. He has a thin, weathered face with deep smile lines, but his dark brown eyes are warm and gentle as he looks at his daughter. Despite being ill, he manages a reassuring smile.

A young woman with short black bob haircut in beige trench coat stands at the bedside, her expression showing shock at seeing her father so thin, mixed with guilt and relief. Her hands grip the bed railing, eyes glistening with unshed tears.

Soft afternoon light filters through white hospital curtains. Medical equipment visible but not prominent. A simple vase with wildflowers on the bedside table adds a touch of warmth.

CHARACTER EXPRESSION FOCUS:
Father: gentle, reassuring smile despite fatigue, warm eyes showing happiness at seeing his daughter.
Daughter: emotional turmoil - relief, guilt, sadness - eyes slightly red, lips pressed together to hold back tears.

{TEXT_FREE_REQUIREMENT}

"""
    },
    # Shot 05: 医院走廊 - 和医生交谈
    {
        "shot_id": 5,
        "scene": "医院走廊 - 和医生交谈",
        "text_type": "narration",
        "speaker_position": "top",
        "chinese_text": "医生说要注意休息，我却不知道他一个人撑了多久",
        "characters": ["daughter_present"],
        "image_prompt": f"""{GHIBLI_STYLE_PREFIX}
---

A hospital corridor with soft fluorescent lighting. A young woman with short black bob haircut in beige trench coat listens intently to a doctor in white coat. Her body language shows concern - arms crossed protectively, shoulders slightly hunched, brow furrowed.

The doctor, a middle-aged woman with glasses and hair in a neat bun, holds a clipboard and speaks with professional but compassionate expression. They stand near a window where afternoon light creates a warm contrast to the clinical surroundings.

The corridor stretches behind them with soft-focus hospital elements - a nurse walking past, a wheelchair against the wall. The atmosphere conveys the weight of medical conversations.

EMOTIONAL ATMOSPHERE:
The scene conveys anxious concern and the heaviness of receiving difficult news.
Character shows worried expression with tight jaw, hands clasped nervously, leaning in to catch every word.

{TEXT_FREE_REQUIREMENT}

"""
    },
    # Shot 06: 老屋客厅 - 看到全家福
    {
        "shot_id": 6,
        "scene": "老屋客厅 - 看到全家福",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "照片里的我们，笑得多开心",
        "characters": ["daughter_present"],
        "image_prompt": f"""{GHIBLI_STYLE_PREFIX}
---

PICTURE-IN-PICTURE ELEMENT - PHOTO FRAME:

A modest but cozy living room in an old Chinese home. Cream-colored walls slightly yellowed with age, dark wooden furniture. A young woman with short black bob haircut stands with her back partially to the viewer, looking up at a wall where a framed family photo hangs.

The photo frame (visible as element within the scene, no text on it) shows: a younger version of the father (black hair, sturdy build, white apron), a smiling woman (the late mother), and a little girl with twin pigtails, all standing in front of the noodle shop. The photo has faded, warm sepia tones.

Golden evening light streams through a window with lace curtains, dust motes floating in the beams. The room shows signs of a life lived alone - a single tea cup on the table, an old calendar, worn armchair.

The daughter reaches toward the photo, her expression showing nostalgia and dawning realization.

NARRATIVE MOMENT:
This scene establishes the transition into memory - the photo triggers flashback.
Visual focus on the contrast between the daughter's present form and the happy family in the photo.

{TEXT_FREE_REQUIREMENT}

"""
    },
    # Shot 07: 回忆 - 童年等待煮面 (回忆场景)
    {
        "shot_id": 7,
        "scene": "回忆 - 童年等待煮面",
        "text_type": "dialogue",
        "speaker_position": "right,left",
        "chinese_text": ["爸爸，面好了吗？", "马上好！"],
        "is_memory": True,
        "characters": ["daughter_child", "father_young"],
        "image_prompt": f"""{GHIBLI_STYLE_PREFIX}
{MEMORY_SCENE_TREATMENT}
---

A warm, nostalgic flashback scene inside a small noodle shop. A young girl (about 10 years old) with black twin pigtails tied with red ribbons, wearing a white school uniform shirt with red neckerchief, leans on a wooden table. Her chin rests on her folded arms, eyes bright with anticipation, a wide innocent smile on her round face.

Behind the counter in soft focus, her father (younger, 40 years old, with black hair and sturdy build) works at the stove. He wears a white sleeveless undershirt with a white apron, a towel draped over his shoulder. Steam rises from the cooking pots.

The shop interior is simple but warm - wooden tables and stools, steam rising, afternoon sun streaming through the open front. Paper lanterns hang from the ceiling (no text). The air seems filled with golden light particles, emphasizing the dreamlike quality of memory.

CHARACTER EXPRESSION FOCUS:
Little girl: eager anticipation, pure joy, bright eyes looking toward father.
Father: glimpsed in background, posture showing care and concentration on cooking.

{TEXT_FREE_REQUIREMENT}

"""
    },
    # Shot 08: 回忆 - 父亲端面 (回忆场景)
    {
        "shot_id": 8,
        "scene": "回忆 - 父亲端面",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "那时候觉得，这是世界上最好吃的面",
        "is_memory": True,
        "characters": ["father_young"],
        "image_prompt": f"""{GHIBLI_STYLE_PREFIX}
{MEMORY_SCENE_TREATMENT}
---

A heartwarming flashback scene. The father (40 years old, black hair, sturdy build) walks toward the viewer carrying a large bowl of steaming noodles. He wears a white sleeveless undershirt with white apron, towel over shoulder. His face shows a warm, proud smile - the smile of a father providing for his child.

Steam rises from the bowl, creating a soft, ethereal effect. Golden afternoon light backlights the scene, creating a halo effect around the father's figure. The background shows the simple noodle shop interior in soft focus.

The perspective is from the child's point of view, looking up at this approaching figure. The bowl of noodles is prominently featured - simple but lovingly prepared.

EMOTIONAL ATMOSPHERE:
The scene conveys pure warmth, unconditional love, and the simple happiness of childhood.
The father's expression shows gentle pride and love, eyes crinkled with a warm smile.

{TEXT_FREE_REQUIREMENT}

"""
    },
    # Shot 09: 回忆 - 青春期争吵 (回忆场景 + 情感强调)
    {
        "shot_id": 9,
        "scene": "回忆 - 青春期争吵",
        "text_type": "dialogue",
        "speaker_position": "center",
        "chinese_text": "我长大后一定要离开这个破地方！！！",
        "is_memory": True,
        "emphasis": "red_highlight",
        "characters": ["daughter_teen", "father_young"],
        "image_prompt": f"""{GHIBLI_STYLE_PREFIX}
{MEMORY_SCENE_TREATMENT}
---

An emotionally intense flashback scene. A teenage girl (18 years old) with black high ponytail, wearing an oversized gray hoodie and ripped jeans, stands in the old family home. Her posture is aggressive - shoulders squared, fists clenched, mouth open in a shout. Her expression shows teenage rebellion and frustration - eyes blazing, brows drawn together in anger.

Facing her, the father (40 years old) stands with slumped shoulders, still in his work apron. His expression shows hurt mixed with patience - eyes sad but understanding, weathered face showing the pain of a parent watching their child pull away.

The living room setting is simple. Evening light casts long shadows. The atmosphere is tense, a moment frozen in time that clearly haunts the daughter's memory.

CHARACTER EXPRESSION FOCUS:
Teenage daughter: defiant anger, shouting, rebellious fire in eyes - but underneath, a scared child wanting to escape small-town life.
Father: deeply hurt but restrained, the pain of unconditional love being rejected visible in his slumped posture.

{TEXT_FREE_REQUIREMENT}

"""
    },
    # Shot 10: 回忆 - 车站送别 (回忆场景)
    {
        "shot_id": 10,
        "scene": "回忆 - 车站送别",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "他什么都没说，只是帮我拎行李",
        "is_memory": True,
        "characters": ["daughter_teen", "father_young"],
        "image_prompt": f"""{GHIBLI_STYLE_PREFIX}
{MEMORY_SCENE_TREATMENT}
---

A poignant flashback at a small-town train station. The father (40 years old, black hair, wearing his simple dark work clothes) walks alongside his daughter (18, in casual clothes with a large travel bag). He carries her heavy suitcase, his posture slightly bent under its weight.

The platform is simple - concrete with a faded yellow safety line, old wooden bench, a single lamp post. Early morning light creates long shadows. In the background, an old green train waits.

The father's expression shows restrained emotion - he doesn't look at his daughter, focusing on the task of carrying her luggage, but his jaw is tight and his eyes show deep sadness. He's the type who shows love through action, not words.

The teenage daughter walks slightly ahead, already looking toward the train, toward her future - not seeing her father's quiet heartbreak.

EMOTIONAL ATMOSPHERE:
The scene conveys unspoken love, the pain of letting go, and the gulf between generations.
Visual focus on the father's silent devotion - carrying her bags even after being hurt by her words.

{TEXT_FREE_REQUIREMENT}

"""
    },
    # Shot 11: 现实 - 厨房发现笔记本
    {
        "shot_id": 11,
        "scene": "现实 - 厨房发现笔记本",
        "text_type": "narration",
        "speaker_position": "top",
        "chinese_text": "在厨房角落，我看到一本旧笔记本",
        "characters": ["daughter_present"],
        "image_prompt": f"""{GHIBLI_STYLE_PREFIX}
---

Back to present day. An old kitchen in the family home - simple wooden cabinets, gas stove, well-worn countertops. Everything speaks of years of cooking, of a life dedicated to the noodle shop.

The daughter (28, short black bob, now in a simple white blouse with sleeves rolled up) kneels by an open cabinet, having discovered a weathered notebook on a shelf. She holds it with both hands, her expression showing curiosity turning to realization.

The notebook is old and worn - yellowed pages, faded cover, clearly used for many years. Evening light streams through a small window, dust motes floating in the golden beam.

Around her, the kitchen shows signs of her father's life - jars of dried ingredients, worn cooking utensils, a calendar several months behind.

EMOTIONAL ATMOSPHERE:
The scene conveys discovery and dawning realization.
Character shows surprised, curious expression with slightly parted lips, eyes widening as she begins to understand the notebook's significance.

{TEXT_FREE_REQUIREMENT}

"""
    },
    # Shot 12: 特写 - 笔记本内容
    {
        "shot_id": 12,
        "scene": "特写 - 笔记本内容",
        "text_type": "narration",
        "speaker_position": "top",
        "chinese_text": '"女儿喜欢的口味"——不爱香菜、多放葱花、汤要清淡...',
        "characters": ["daughter_present"],
        "image_prompt": f"""{GHIBLI_STYLE_PREFIX}
---

A close-up shot of an opened, weathered notebook held in feminine hands. The pages are yellowed with age, filled with neat but simple handwriting (DO NOT show actual text - only suggest handwriting through abstract line patterns that resemble writing but are not legible).

The hands holding the notebook show slight trembling - delicate fingers with short nails, a small gold watch visible on the wrist. The hands press the pages open with gentle reverence.

The notebook pages show various abstract elements suggesting content: neat lines suggesting a list format, small symbols suggesting check marks or notes, occasional darker marks suggesting emphasis - all without any actual readable text.

Warm golden light illuminates the pages. A single tear drop has fallen on the page, creating a small water mark. The background is soft blur of the wooden kitchen surface.

EMOTIONAL ATMOSPHERE:
The scene conveys revelation and emotional impact.
The focus is on the artifact of love - the notebook representing years of silent care.

{TEXT_FREE_REQUIREMENT}

"""
    },
    # Shot 13: 现实 - 泪流满面
    {
        "shot_id": 13,
        "scene": "现实 - 泪流满面",
        "text_type": "thought",
        "speaker_position": "bottom",
        "chinese_text": '原来每一碗面，都是他在说"我爱你"',
        "characters": ["daughter_present"],
        "image_prompt": f"""{GHIBLI_STYLE_PREFIX}
---

An emotionally powerful scene. The daughter (28, short black bob) sits on the kitchen floor, back against the cabinets, knees drawn up. The notebook rests in her lap. Tears stream down her face freely, her expression showing deep emotional release - not dramatic sobbing, but quiet, profound tears of realization and regret.

Her eyes are red-rimmed, looking down at the notebook but seeing something beyond it - understanding finally what her father's love looked like. One hand covers her mouth, the other clutches the notebook.

Evening light creates a warm glow, but shadows fill the corners of the kitchen. The atmosphere is intimate, private - a moment of transformation.

EMOTIONAL ATMOSPHERE:
The scene conveys catharsis, revelation, and the bittersweet pain of understanding too late.
Character shows deep emotion - tears, slightly shaking shoulders, the weight of years of distance suddenly clear.

{TEXT_FREE_REQUIREMENT}

"""
    },
    # Shot 14: 医院病房 - 端面给父亲
    {
        "shot_id": 14,
        "scene": "医院病房 - 端面给父亲",
        "text_type": "dialogue",
        "speaker_position": "left,right",
        "chinese_text": ["爸，我煮的，你尝尝", "...还是那个味道"],
        "characters": ["daughter_present", "father_present"],
        "image_prompt": f"""{GHIBLI_STYLE_PREFIX}
---

A warm, redemptive scene in the hospital room. The daughter (28, short black bob, wearing a soft cream sweater) stands beside her father's hospital bed, carefully holding out a bowl of steaming noodles wrapped in a cloth to keep warm.

Her expression shows nervous hope - a small, vulnerable smile, eyes seeking approval, posture slightly leaning forward. She's made this simple dish with all her love, trying to give back what she received.

The father (55, gray hair, in hospital gown but sitting up stronger than before) looks at the bowl with genuine surprise, then up at his daughter. His eyes glisten with emotion, deep smile lines crinkling as he begins to smile - not at the food, but at his daughter's gesture of love.

Morning sunlight streams through the window, creating a warm, hopeful atmosphere. The simple hospital room feels transformed by this moment of connection.

CHARACTER EXPRESSION FOCUS:
Daughter: hopeful, vulnerable, seeking connection - a child again wanting to please her father.
Father: deeply moved, surprised, overflowing with unspoken emotion - seeing his daughter truly for the first time in years.

{TEXT_FREE_REQUIREMENT}

"""
    },
    # Shot 15: 面馆门口 - 新店招亮起
    {
        "shot_id": 15,
        "scene": "面馆门口 - 新店招亮起",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "有些爱从不说出口，却记在心里一辈子",
        "characters": ["daughter_present"],
        "image_prompt": f"""{GHIBLI_STYLE_PREFIX}
---

The final scene - a hopeful new beginning. The small-town noodle shop, now revitalized. The building has been cleaned and refreshed, maintaining its traditional charm but with new life. Warm light glows from within, steam visible through the windows. Plants in new pots flank the entrance.

A new wooden sign hangs above the door (no text visible - just a clean, fresh wooden board suggesting renewal). Paper lanterns glow with warm light. The shop door is open, inviting.

The daughter (28, now wearing a simple white blouse with a white apron - echoing her father's work attire) stands in the doorway, arms at her sides, looking out at the street with a peaceful, determined expression. Her posture is straight, confident - she has found her place.

Golden hour sunlight bathes the scene in warm amber tones. A few villagers walk past, glancing at the reopened shop with interest. The atmosphere conveys hope, continuity, and the cycle of love passing between generations.

NARRATIVE MOMENT:
This scene establishes resolution - the daughter carrying on her father's legacy, love expressed through action.
Visual focus on the transformed shop and the daughter's new role as its keeper.

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
    """
    为所有角色生成参考图

    修复: 正确处理 ReferenceImageManager.generate_character_multi_refs() 返回格式
    返回格式: {'portrait': {...}, 'fullbody': {...}} 而非 {'success': ...}
    """
    reference_results = {}

    print("\n" + "=" * 50)
    print("生成角色参考图 (5个角色变体)")
    print("=" * 50)

    for char_id, char_data in characters.items():
        print(f"\n[参考图] {char_data['name']} ({char_id})")

        try:
            # generate_character_multi_refs 返回:
            # {'portrait': {'success': bool, 'pil_image': Image}, 'fullbody': {...}}
            result = await ref_manager.generate_character_multi_refs(
                character=char_data,
                project_style=style_config,
                image_generator=image_gen,
                delay=2.0  # 避免API限流
            )

            # 正确解析嵌套结构 (参考 teststory6.4)
            portrait_result = result.get('portrait', {})
            fullbody_result = result.get('fullbody', {})

            portrait_img = portrait_result.get('pil_image') if portrait_result.get('success') else None
            fullbody_img = fullbody_result.get('pil_image') if fullbody_result.get('success') else None

            # 保存参考图到磁盘
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

            # 存储结果 (包含PIL对象供后续使用)
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

        await asyncio.sleep(1)  # 额外延迟

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

        # 将参考图指令添加到prompt
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
# 角色位置检测 (TASK-OPT-002-B)
# =============================================================================

async def detect_character_positions(
    shot_image: Image.Image,
    characters_in_scene: List[str],
    reference_images: Dict[str, Path],
    characters: List[dict],
    debug_mode: bool = False
) -> Dict[str, Dict[str, int]]:
    """
    使用 Claude 4.5 Haiku 检测角色并推荐泡泡位置

    TASK-OPT-002-B: 集成AI-ML的Prompt模板实现动态对话气泡定位
    TASK-OPT-004-B: 改为返回百分比坐标 (0-100) 实现精确定位
    TASK-OPT-005-B: 升级为AI直接推荐泡泡位置(bubble_x_percent, bubble_y_percent)

    Args:
        shot_image: 生成的shot图像
        characters_in_scene: 场景中的角色ID列表
        reference_images: {char_id: fullbody_path} 参考图路径字典
        characters: 完整的角色数据列表
        debug_mode: 是否返回识别依据

    Returns:
        {char_id: {"bubble_x_percent": int, "bubble_y_percent": int}} 泡泡位置推荐
    """
    if not characters_in_scene:
        return {}

    # 过滤出有参考图的角色
    chars_with_refs = [c for c in characters_in_scene if c in reference_images]
    if not chars_with_refs:
        print("  ⚠️ 无可用参考图，跳过角色位置检测")
        return {}

    try:
        client = anthropic.AsyncAnthropic()

        # 构建角色描述字典
        char_descriptions = {}
        for char in characters:
            char_id = char.get('id', '')
            if char_id in chars_with_refs:
                char_descriptions[char_id] = extract_character_description_for_haiku(char)

        # 构建 Prompt
        prompt_text = build_position_detection_prompt(
            characters_in_scene=chars_with_refs,
            character_descriptions=char_descriptions,
            debug_mode=debug_mode
        )

        # 构建多图输入
        content = []

        # Image 1: 场景图
        import io
        shot_buffer = io.BytesIO()
        shot_image.save(shot_buffer, format="PNG")
        shot_b64 = base64.standard_b64encode(shot_buffer.getvalue()).decode()
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": shot_b64}
        })

        # Image 2+: 按顺序添加参考图
        for char_id in chars_with_refs:
            ref_path = reference_images.get(char_id)
            if ref_path and Path(ref_path).exists():
                with open(ref_path, "rb") as f:
                    ref_b64 = base64.standard_b64encode(f.read()).decode()
                content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/png", "data": ref_b64}
                })

        # 添加 Prompt 文本
        content.append({"type": "text", "text": prompt_text})

        # 调用 Haiku
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": content}]
        )

        # 解析响应
        response_text = response.content[0].text

        # 处理可能的 markdown 代码块包装
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        result = json.loads(response_text.strip())

        # Debug模式返回完整结果
        if debug_mode:
            return result

        # 标准模式：提取泡泡位置 {char_id: {"bubble_x_percent": int, "bubble_y_percent": int}}
        # TASK-OPT-005-B: AI直接推荐泡泡位置
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

async def run_full_story_test_v2():
    """运行完整故事测试 V2（带参考图）"""

    print("=" * 70)
    print("条漫完整故事测试 V2 - 《最后一碗面》")
    print("15张图完整故事，Ghibli-inspired风格")
    print("新增: ReferenceImageManager 角色一致性增强")
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

    # 初始化图像生成器
    image_gen = get_image_generator()

    # 初始化参考图管理器 (不需要参数，参考图通过方法生成)
    ref_manager = ReferenceImageManager()

    # 风格配置 - 使用 ProjectStyleConfig 类型
    style_config = ProjectStyleConfig(
        style_preset="ghibli",
        color_palette="warm",
        dominant_colors=["cream", "golden", "soft_brown"],
        lighting_style="soft",
        rendering="painterly"
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

    # 统计参考图生成结果
    ref_success_count = sum(1 for r in ref_results.values() if r.get("success"))
    print(f"\n参考图生成完成: {ref_success_count}/{len(CHARACTERS)}")

    # Step 2: 生成故事图
    print("\n" + "=" * 70)
    print("Step 2: 生成故事图 (带参考图)")
    print("=" * 70)

    # 存储结果
    results = []
    prompts_log = []

    print(f"\n开始生成 {len(FULL_STORY_SHOTS)} 张图...")
    print("-" * 70)

    # 生成每张图
    for shot in FULL_STORY_SHOTS:
        shot_id = shot["shot_id"]
        scene = shot["scene"]
        is_memory = shot.get("is_memory", False)
        emphasis = shot.get("emphasis")
        char_ids = shot.get("characters", [])

        print(f"\n[Shot {shot_id:02d}] {scene}")
        if is_memory:
            print(f"  📷 回忆场景（柔光处理）")
        if emphasis:
            print(f"  🔴 情感强调: {emphasis}")
        print(f"  👥 角色: {', '.join(char_ids)}")

        # 收集参考图
        reference_images = []
        for char_id in char_ids:
            ref_result = ref_results.get(char_id)
            if ref_result and ref_result.get("success"):
                # 使用全身图作为参考
                fullbody_img = ref_result.get("fullbody_image")
                if fullbody_img:
                    reference_images.append(fullbody_img)
                    print(f"  📷 使用 {char_id} 参考图")

        # 构建角色参考指令
        char_instruction = build_character_reference_instruction(char_ids)

        # 保存prompt日志
        prompts_log.append({
            "shot_id": shot_id,
            "scene": scene,
            "text_type": shot["text_type"],
            "speaker_position": shot["speaker_position"],
            "chinese_text": shot["chinese_text"],
            "is_memory": is_memory,
            "emphasis": emphasis,
            "characters": char_ids,
            "reference_count": len(reference_images),
            "prompt": shot["image_prompt"]
        })

        # 生成无文字图像（带参考图）
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

            # TASK-OPT-002-B + TASK-OPT-004-B: 对话类型shot使用Haiku检测角色位置（百分比坐标）
            if shot["text_type"] == "dialogue" and len(char_ids) > 0:
                # 构建参考图路径字典
                ref_paths = {}
                for cid in char_ids:
                    ref_result = ref_results.get(cid)
                    if ref_result and ref_result.get("fullbody_path"):
                        ref_paths[cid] = ref_result["fullbody_path"]

                if ref_paths:
                    # 将CHARACTERS字典转换为列表供检测函数使用
                    char_list = [{"id": k, **v} for k, v in CHARACTERS.items() if k in char_ids]

                    detected_positions = await detect_character_positions(
                        shot_image=original_image,
                        characters_in_scene=char_ids,
                        reference_images=ref_paths,
                        characters=char_list,
                        debug_mode=False
                    )

                    # TASK-OPT-005-B: 存储AI推荐的泡泡位置
                    # detected_positions格式: {char_id: {"bubble_x_percent": int, "bubble_y_percent": int}}
                    if detected_positions:
                        shot["bubble_positions"] = detected_positions

            # 叠加文字
            processed_image = text_service.process_shot(original_image, shot)

            # 保存叠加后的图片
            with_text_path = WITH_TEXT_DIR / f"shot_{shot_id:02d}.png"
            processed_image.save(with_text_path)
            print(f"  ✅ 文字叠加完成: {with_text_path.name}")

            # 创建对比图
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

        # 避免API限流
        await asyncio.sleep(2)

    # 保存日志
    prompts_path = OUTPUT_DIR / "prompts_log.json"
    with open(prompts_path, 'w', encoding='utf-8') as f:
        json.dump(prompts_log, f, ensure_ascii=False, indent=2)

    results_path = OUTPUT_DIR / "results.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 保存参考图结果
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
    emphasis_count = sum(1 for r in results if r.get("emphasis") and r.get("success"))
    with_refs_count = sum(1 for r in results if r.get("reference_count", 0) > 0)

    print("\n" + "=" * 70)
    print("测试完成! (V2 - 带参考图)")
    print("=" * 70)
    print(f"参考图生成: {ref_success_count}/{len(CHARACTERS)}")
    print(f"故事图生成: {success_count}/{len(FULL_STORY_SHOTS)}")
    print(f"使用参考图的shot: {with_refs_count}/{len(FULL_STORY_SHOTS)}")
    print(f"回忆场景: {memory_count}/4")
    print(f"情感强调: {emphasis_count}/1")

    print(f"\n输出目录:")
    print(f"  参考图: {REFERENCE_DIR}")
    print(f"  无文字图片: {NO_TEXT_DIR}")
    print(f"  叠加文字后: {WITH_TEXT_DIR}")
    print(f"  对比图: {COMPARISON_DIR}")

    print("\n验收要点:")
    print("  1. 角色一致性：女儿和父亲在所有图中可识别（重点检查）")
    print("  2. 风格一致性：15张图保持Ghibli温暖插画风格")
    print("  3. 文字可读性：所有中文清晰可读")
    print("  4. 情感强调：Shot 09 '破地方！！！' 红色高亮")
    print("  5. 回忆场景：Shot 07-10 有柔光/怀旧效果")
    print("  6. 故事完整性：阅读体验流畅，情感触动")

    return results

# =============================================================================
# 入口
# =============================================================================

if __name__ == "__main__":
    # 加载环境变量
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

    asyncio.run(run_full_story_test_v2())
