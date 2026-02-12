"""
Kai与Cici初次约会 - 条漫故事测试脚本

故事: 探探相识 → 首次线下约会 → 心动萌芽
风格: Korean Webtoon Style (韩漫风格)
图片数: 42张 (12幕结构)

关键特点:
1. 使用现有参考图（仅脸部特征），不重新生成
2. 服装使用故事描述，不使用参考图服装
3. 支持对话气泡位置检测 (Haiku AI推荐)

任务: HANDOFF-2026-01-30-011
作者: @Backend
日期: 2026-01-30
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

# 加载环境变量
load_dotenv(Path(__file__).parent.parent / ".env")

from app.services.image_generator import ImageGenerator
from app.models.style_config import ProjectStyleConfig
from app.prompts.character_position_detection import (
    build_prompt as build_position_detection_prompt,
    extract_character_description_for_haiku,
)
# ARCH-3: 使用统一的主服务
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
USE_PRO_MODEL = False  # 韩漫风格使用Flash即可

# 输出目录（v3版本，V5修复后验收）
OUTPUT_DIR = Path(__file__).parent.parent / "test_output" / "comic_cc_kai_story_v3"
NO_TEXT_DIR = OUTPUT_DIR / "no_text_images"
WITH_TEXT_DIR = OUTPUT_DIR / "with_text_images"
COMPARISON_DIR = OUTPUT_DIR / "comparison"

# 现有参考图目录（直接加载，不重新生成）
EXISTING_REF_DIR = Path(__file__).parent.parent / "test_output" / "manualtest" / "teststory_CCKai" / "character_refs"

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
# 角色定义 (仅用于Haiku角色位置检测)
# =============================================================================

CHARACTERS = {
    "Cici": {
        "id": "Cici",
        "name": "Cici",
        "name_en": "Cici",
        "character_type": "human",
        "gender": "female",
        "age_appearance": "young_adult",
        "physical": {
            "height": "medium (165cm)",
            "build": "slim, elegant",
            "skin_tone": "fair porcelain",
            "face_shape": "oval with delicate features",
            "hair_color": "deep chestnut brown",
            "hair_style": "long wavy hair falling past shoulders, soft curls",
            "hair_texture": "silky with natural waves",
            "eye_color": "warm dark brown",
            "eye_shape": "almond, expressive",
            "eye_size": "medium-large",
            "eyebrows": "natural arch, well-groomed",
            "nose": "small and straight with delicate bridge",
            "lips": "soft pink, natural fullness",
            "distinctive_marks": ["small beauty mark on right cheek"]
        },
        "clothing": {
            "top": "black fitted knit sweater with subtle ribbed texture",
            "outerwear": "black long wool coat with classic cut",
            "bottom": "light gray midi pencil skirt",
            "footwear": "black pointed-toe heels",
            "accessories": ["vibrant red silk scarf around neck", "small gold hoop earrings", "simple gold bracelet"],
            "style": "elegant urban chic"
        }
    },
    "Kai": {
        "id": "Kai",
        "name": "Kai",
        "name_en": "Kai",
        "character_type": "human",
        "gender": "male",
        "age_appearance": "young_adult",
        "physical": {
            "height": "tall (182cm)",
            "build": "lean and athletic",
            "skin_tone": "light with warm undertone",
            "face_shape": "defined jawline, angular features",
            "hair_color": "jet black",
            "hair_style": "short and neatly styled, slightly textured on top",
            "hair_texture": "thick and straight",
            "eye_color": "dark brown, deep and warm",
            "eye_shape": "almond, thoughtful",
            "eye_size": "medium",
            "eyebrows": "straight and defined, dark",
            "nose": "straight with strong bridge",
            "lips": "medium thickness, natural color",
            "distinctive_marks": ["black rectangular glasses frames"]
        },
        "clothing": {
            "top": "dark purple-black knit sweater with crew neck",
            "outerwear": "black wool overcoat, tailored fit",
            "bottom": "dark indigo slim-fit jeans",
            "footwear": "black leather oxford shoes",
            "accessories": ["black rectangular glasses", "simple black leather watch"],
            "style": "refined casual elegance"
        }
    }
}

# Shot到角色的映射
SHOT_CHARACTER_MAPPING = {
    1: [],  # 手机屏幕
    2: [],  # 手机屏幕
    3: [],  # 手机屏幕
    4: ["Kai", "Cici"],  # 分屏
    5: [],  # 街景
    6: ["Kai"],
    7: ["Kai"],
    8: ["Cici"],
    9: ["Cici"],
    10: ["Kai", "Cici"],
    11: ["Kai", "Cici"],
    12: ["Kai", "Cici"],
    13: ["Cici"],
    14: ["Kai", "Cici"],
    15: [],  # 餐厅内景
    16: ["Kai", "Cici"],
    17: ["Kai", "Cici"],
    18: ["Kai", "Cici"],
    19: ["Kai", "Cici"],
    20: ["Cici"],
    21: ["Kai"],
    22: ["Kai", "Cici"],
    23: ["Kai", "Cici"],
    24: ["Kai", "Cici"],
    25: ["Kai", "Cici"],
    26: ["Kai", "Cici"],
    27: ["Kai", "Cici"],
    28: [],  # 手部特写
    29: [],  # 手部特写
    30: ["Kai", "Cici"],
    31: ["Kai", "Cici"],
    32: ["Kai", "Cici"],
    33: ["Kai", "Cici"],
    34: ["Kai"],
    35: ["Cici"],
    36: ["Kai", "Cici"],
    37: ["Kai", "Cici"],
    38: ["Kai", "Cici"],
    39: ["Kai", "Cici"],
    40: ["Kai", "Cici"],
    41: ["Kai"],
    42: ["Kai", "Cici"],
}

# =============================================================================
# 韩漫风格前缀
# =============================================================================

KOREAN_WEBTOON_STYLE_PREFIX = """STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MUST INCLUDE: manhwa style, Korean webtoon, full color, detailed backgrounds, modern aesthetic, refined features, soft lighting, emotional expressions
DO NOT USE: photorealistic, photograph, 3D render, anime cel-shading, harsh shadows, Western comic style

---

"""

TEXT_FREE_REQUIREMENT = """
ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Any visible text will cause this image to FAIL validation

FULL CANVAS COMPOSITION:
- Fill the ENTIRE image canvas edge-to-edge with meaningful visual content
- NO black borders, NO white margins, NO blank areas at ANY edge
- Extend backgrounds, scenery, and visual elements to ALL four edges
- The composition must touch all four sides of the frame without any padding
- DO NOT create reserved spaces, margins, or borders of any color
"""

# =============================================================================
# 42图完整脚本定义
# =============================================================================

FULL_STORY_SHOTS = [
    # === 第一幕：线上相识 (Shots 01-04) ===
    {
        "shot_id": 1,
        "scene": "探探匹配",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "「2023年1月的某个夜晚，两个陌生人在探探相遇。」",
        "characters": [],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
A smartphone screen showing a dating app interface. The screen displays two profile photos side by side - a young man with black short hair and glasses on the left, and a young woman with long wavy brown hair on the right. A heart icon or match indicator glows between them.

The phone is held by ONE PAIR of feminine hands with natural nails (two hands from one person). Soft warm lighting illuminates the screen in a dark room, creating an intimate late-night atmosphere. The screen light casts a gentle glow.

UI COMPOSITION:
The app interface is stylized and illustrated, not realistic. Profile photos are in webtoon art style matching the characters. No readable text on screen - use abstract symbols or blurred text placeholders.

EMOTIONAL ATMOSPHERE:
A sense of anticipation and possibility. The warm glow of the screen suggests late night browsing, a moment of connection.

ANATOMY REQUIREMENT:
- Only ONE pair of hands visible (belonging to ONE person)
- Each hand must have exactly 5 fingers
- Both hands must connect to the SAME pair of wrists/arms
- No duplicate limbs or floating body parts

{TEXT_FREE_REQUIREMENT}
"""
    },
    {
        "shot_id": 2,
        "scene": "日常聊天",
        "text_type": "dialogue_with_narration",
        "speaker_position": "center",
        "chinese_text": [
            "Cici：「你周末一般做什么？」",
            "Kai：「看书、跑步，偶尔自己做饭」",
            "Cici：「会做饭的男生不多见诶」",
            "Kai：「下次做给你吃？」",
            "旁白：「从日常聊到深夜，从陌生聊成熟悉。」"
        ],
        "characters": [],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
A smartphone screen showing a chat conversation interface. Multiple message bubbles arranged vertically - some on the left (received) and some on the right (sent). The bubbles are stylized illustrations without readable text.

The background shows a cozy evening setting - perhaps a bedside table with a warm lamp, creating intimate atmosphere. The phone screen glows warmly.

UI COMPOSITION:
Abstract chat bubbles in different colors (left gray, right blue/green). Small avatar icons next to messages. No actual readable text - use wavy lines or abstract shapes as text placeholders.

EMOTIONAL ATMOSPHERE:
Warmth and growing connection. The multiple message bubbles suggest an engaging, flowing conversation that lasted hours.

{TEXT_FREE_REQUIREMENT}
"""
    },
    {
        "shot_id": 3,
        "scene": "约定见面",
        "text_type": "dialogue_with_thought",
        "speaker_position": "center,bottom",
        "chinese_text": [
            "Kai：「聊了一个多月了，要不要见一面？」",
            "Cici：「好呀，什么时候？」",
            "Kai：「周三怎么样？工作日人少」",
            "Cici：「思南路那家Feloni，听说不错」",
            "Kai：「好，周三傍晚6点」",
            "Cici内心：「终于要见面了...有点紧张。」"
        ],
        "characters": [],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
A smartphone held in delicate feminine hands, showing a chat interface. The screen displays a conversation with a calendar or date-picking element visible. The last few messages show excitement with heart or happy emoji-style icons.

The background is soft-focused - perhaps a young woman's bedroom or living room with warm lighting. A hint of the woman's face visible at the top edge of frame, showing a subtle smile.

EMOTIONAL ATMOSPHERE:
Anticipation and nervous excitement. The moment of agreeing to meet in person for the first time.

ANATOMY REQUIREMENT:
- Hands must have exactly 5 fingers per hand
- All visible body parts must be anatomically correct
- No duplicate limbs or distorted proportions

{TEXT_FREE_REQUIREMENT}
"""
    },
    {
        "shot_id": 4,
        "scene": "各自准备（分屏）",
        "text_type": "thought",
        "speaker_position": "left_bottom,right_bottom",
        "chinese_text": ["Kai内心：「这件毛衣...应该还行吧？」", "Cici内心：「这条丝巾是点睛之笔。」"],
        "characters": ["Kai", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
SPLIT SCREEN COMPOSITION:

LEFT HALF: A young man with short black hair and black rectangular glasses standing before a mirror in a modern minimalist bedroom. He is wearing a dark purple-black knit sweater, adjusting the collar with careful attention. His expression is focused and slightly nervous, checking his appearance with a small frown of concentration. Clean modern furniture, soft daylight from window.

RIGHT HALF: A young woman with long wavy chestnut brown hair standing before a vanity mirror in a warmly lit bedroom. She is tying a vibrant red silk scarf around her neck, wearing a black knit sweater. Her expression shows a gentle smile of anticipation as she checks her reflection. Warm lamp lighting, feminine decor with soft colors.

VISUAL STYLE:
- Clear vertical division down the center
- Both sides lit with warm, flattering light
- Mirror reflections showing the characters' faces
- Slight color temperature difference: cooler left (Kai), warmer right (Cici)

CHARACTER REFERENCE:
- LEFT (Kai): FACE REFERENCE ONLY from reference. Use face features and glasses. CLOTHING: dark purple-black knit sweater
- RIGHT (Cici): FACE REFERENCE ONLY from reference. Use face features and wavy hair. CLOTHING: black knit sweater with red silk scarf

{TEXT_FREE_REQUIREMENT}
"""
    },
    # === 第二幕：Kai等待 (Shots 05-07) ===
    {
        "shot_id": 5,
        "scene": "提前到达",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "「2月1日，周三傍晚。上海思南路。」",
        "characters": [],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
A charming European-style street in Shanghai's French Concession district at dusk. A cozy Italian restaurant with warm light spilling from its windows. The facade features elegant French colonial architecture with tall windows, wrought iron balconies, and mature plane trees lining the street.

Street lamps are beginning to glow with warm golden light. The sky shows the soft orange-pink gradients of sunset. Fallen autumn leaves scattered on the cobblestone sidewalk. The restaurant entrance has a small awning and potted plants.

ENVIRONMENTAL DETAILS:
- Classic Shanghai French Concession architecture
- Warm inviting restaurant lighting
- Romantic dusk atmosphere
- Empty outdoor seating area with bistro chairs

{TEXT_FREE_REQUIREMENT}
DO NOT include any readable text on signs or storefronts.
"""
    },
    {
        "shot_id": 6,
        "scene": "门口等待",
        "text_type": "thought",
        "speaker_position": "top",
        "chinese_text": "Kai内心：「还有五分钟...她会喜欢这里吗？」",
        "characters": ["Kai"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
A tall young man with short black hair and black rectangular glasses standing outside a restaurant entrance. He wears a black wool overcoat over a dark purple-black sweater, hands casually in coat pockets. His posture is slightly tense with anticipation.

His expression shows a mix of nervousness and eagerness - eyebrows slightly raised, eyes scanning the street direction, lips pressed together in contained excitement. The warm glow from the restaurant windows illuminates one side of his face.

MEDIUM SHOT framing, showing him from thighs up. The restaurant's warm interior visible through glass windows behind him. Street lamp casting golden light. A few autumn leaves drifting past.

CHARACTER REFERENCE:
- FACE REFERENCE ONLY from Kai reference image
- CLOTHING: black wool overcoat, dark purple-black sweater underneath
- Black rectangular glasses frames

{TEXT_FREE_REQUIREMENT}
"""
    },
    {
        "shot_id": 7,
        "scene": "看手表",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "「他比约定时间早到了十分钟。这是他的习惯。」",
        "characters": ["Kai"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
CLOSE-UP to MEDIUM CLOSE-UP shot of a young man with black hair and rectangular glasses. He is lifting his left wrist to check his watch - a simple black leather strap watch. His expression shows anticipation mixed with slight nervousness - gentle smile forming, eyes focused on the watch face.

He wears a black wool overcoat with the collar slightly turned up against the evening chill. The warm golden light from nearby street lamps illuminates his face from the side, creating a romantic atmosphere.

COMPOSITION:
- Focus on his face and the gesture of checking time
- Watch visible but not the main focus
- Warm bokeh lights in soft-focus background
- Evening atmosphere with golden hour remnants

CHARACTER REFERENCE:
- FACE REFERENCE ONLY from Kai reference image
- CLOTHING: black wool overcoat
- Black rectangular glasses frames

{TEXT_FREE_REQUIREMENT}
DO NOT include any readable text, including on the watch face.
"""
    },
    # === 第三幕：Cici出现 (Shots 08-11) ⭐ 情感重点1 ===
    {
        "shot_id": 8,
        "scene": "街角身影",
        "text_type": "narration",
        "speaker_position": "top",
        "chinese_text": "「是她。」",
        "characters": ["Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
LONG SHOT of a quiet street corner in Shanghai's French Concession. A young woman's silhouette emerges from under the canopy of plane trees. She wears a long black coat, and a vibrant red scarf stands out brilliantly against the muted evening colors.

The street is lined with beautiful colonial architecture and mature trees with golden autumn leaves. Street lamps cast warm pools of light on the cobblestone. The woman is walking toward the camera, still at a distance, her figure elegant and confident.

ATMOSPHERIC DETAILS:
- Dusk light with warm orange-pink sky visible between buildings
- Golden autumn leaves on trees and ground
- Romantic European-style street scene
- The red scarf as a striking visual focal point

CHARACTER REFERENCE:
- FACE REFERENCE ONLY from Cici reference (face not detailed at this distance)
- CLOTHING: black long wool coat, vibrant red silk scarf visible even from distance
- Long wavy brown hair

{TEXT_FREE_REQUIREMENT}
"""
    },
    {
        "shot_id": 9,
        "scene": "走近",
        "text_type": "thought",
        "speaker_position": "bottom",
        "chinese_text": "Cici内心：「那个穿黑色大衣的...是他吗？」",
        "characters": ["Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
MEDIUM SHOT of a young woman walking down a tree-lined street, approaching closer. She has long wavy chestnut brown hair flowing gently in the evening breeze. Her vibrant red silk scarf flutters elegantly. She wears a black long wool coat over a black knit sweater and light gray skirt.

Her expression shows anticipation and slight nervous excitement - eyes searching ahead with hope, a gentle expectant smile forming on her lips. Her cheeks have a slight blush from the cold evening air.

BACKGROUND:
- Beautiful plane trees with golden autumn leaves
- French colonial architecture with warm lit windows
- Romantic dusk lighting with street lamps glowing
- A few autumn leaves falling in the breeze

CHARACTER REFERENCE:
- FACE REFERENCE ONLY from Cici reference image
- CLOTHING: black long wool coat, red silk scarf, black knit sweater visible at neckline
- Long wavy chestnut brown hair

{TEXT_FREE_REQUIREMENT}
"""
    },
    {
        "shot_id": 10,
        "scene": "目光相遇 ⭐【情感重点1-A】",
        "text_type": "narration",
        "speaker_position": "top",
        "chinese_text": "「目光相遇的那一刻，时间好像慢了下来。」",
        "characters": ["Kai", "Cici"],
        "is_emotional_highlight": True,
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
⭐ EMOTIONAL HIGHLIGHT SHOT ⭐

TWO-SHOT MEDIUM composition capturing the magical moment of first eye contact. A young woman with long wavy brown hair and red scarf on the left, and a tall young man with black hair and glasses on the right. They are about 5 meters apart, having just spotted each other.

BOTH characters show that frozen moment of recognition - eyes widening slightly, breath caught, time seeming to slow down. The woman's lips part in surprised delight. The man's expression softens with wonder.

LIGHTING AND ATMOSPHERE:
- Romantic golden hour lighting wrapping around both figures
- Soft bokeh lights from street lamps and restaurant windows
- Warm color palette emphasizing the emotional moment
- Background slightly soft-focused to emphasize the characters
- Subtle sparkle or glow effect around them (webtoon romantic style)

CHARACTER REFERENCE:
- LEFT (Cici): FACE REFERENCE ONLY. CLOTHING: black coat, red scarf, long wavy brown hair
- RIGHT (Kai): FACE REFERENCE ONLY. CLOTHING: black overcoat, glasses

COMPOSITION:
- Characters facing each other with space between
- Eye-level camera angle
- Cinematic romantic framing

{TEXT_FREE_REQUIREMENT}
Both faces and their expressions must be crystal clear.
"""
    },
    {
        "shot_id": 11,
        "scene": "心动瞬间 ⭐【情感重点1-B】",
        "text_type": "thought",
        "speaker_position": "left_bottom,right_bottom",
        "chinese_text": ["Kai内心：「她笑起来，比照片还好看。」", "Cici内心：「他的眼睛...好温柔。」"],
        "characters": ["Kai", "Cici"],
        "is_emotional_highlight": True,
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
⭐ EMOTIONAL HIGHLIGHT SHOT - CLOSE-UP ⭐

SPLIT CLOSE-UP or ALTERNATING CLOSE-UP composition showing both characters' faces in intimate detail, with dreamy soft-focus background.

LEFT SIDE - Kai's face in close-up:
- His dark eyes behind glasses show gentle warmth and wonder
- A soft, genuine smile just beginning to form
- Eyes sparkling with the light of first attraction
- Expression: tender, captivated, slightly breathless

RIGHT SIDE - Cici's face in close-up:
- Her warm brown eyes widened with pleasant surprise
- Cheeks showing a delicate pink blush
- Lips curved in a blooming smile of delight
- Expression: touched, happy, heart fluttering

ROMANTIC ELEMENTS (Korean Webtoon Style):
- Soft sparkle/shimmer effects around the eyes
- Warm golden light caressing their faces
- Heavily blurred romantic bokeh background
- Subtle pink/warm tones enhancing the moment
- Dreamy, ethereal quality

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Black hair, rectangular glasses, gentle expression
- Cici: FACE REFERENCE ONLY. Wavy brown hair, red scarf edge visible, blushing cheeks

{TEXT_FREE_REQUIREMENT}
Faces must be the absolute focus - detailed, expressive, beautiful.
"""
    },
    # === 第四幕：初次对话 (Shots 12-14) ===
    {
        "shot_id": 12,
        "scene": "打招呼",
        "text_type": "dialogue",
        "speaker_position": "left,right",
        "chinese_text": ["Kai：「你好，Cici。终于见到真人了。」", "Cici：「你好呀，Kai。」"],
        "characters": ["Kai", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
MEDIUM TWO-SHOT of a young man and woman standing face to face outside a warmly-lit restaurant, about one meter apart. Both are smiling with shy happiness.

LEFT - Kai: tall man in black overcoat, dark sweater underneath, black glasses. He has a warm, slightly nervous smile, standing with good posture, looking at her with gentle eyes.

RIGHT - Cici: elegant woman in black coat with red silk scarf, long wavy brown hair. She looks up at him with a delighted, slightly shy smile, eyes bright with happiness.

The warm light from the restaurant creates a golden glow around them. The evening atmosphere is romantic with soft street lighting.

BODY LANGUAGE:
- Both slightly leaning toward each other
- Open, welcoming postures
- The electricity of first meeting in person

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. CLOTHING: black overcoat, dark sweater, glasses
- Cici: FACE REFERENCE ONLY. CLOTHING: black coat, red scarf, long wavy hair

{TEXT_FREE_REQUIREMENT}
"""
    },
    {
        "shot_id": 13,
        "scene": "第一句调侃",
        "text_type": "dialogue",
        "speaker_position": "top,bottom",
        "chinese_text": ["Cici：「比照片帅嘛。」", "Kai：「你也是，比照片还漂亮。」"],
        "characters": ["Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
CLOSE-UP to MEDIUM CLOSE-UP focusing on a young woman with long wavy brown hair. She has a playful, teasing smile - the kind of flirtatious expression after giving a compliment. Her eyes sparkle with mischief and genuine warmth. She's looking slightly downward with a shy but pleased expression.

Her red silk scarf is visible around her neck. Her cheeks have a soft pink blush. Her lips are curved in a coy, satisfied smile after making him flustered.

BACKGROUND:
- Soft blur showing warm restaurant lights
- The silhouette of a tall man (Kai) slightly visible in soft focus
- Romantic evening atmosphere

CHARACTER REFERENCE:
- FACE REFERENCE ONLY from Cici reference image
- Expression: playful, teasing, slightly shy but pleased
- CLOTHING: black coat, red scarf visible

{TEXT_FREE_REQUIREMENT}
Her face and playful expression must be the focus.
"""
    },
    {
        "shot_id": 14,
        "scene": "进入餐厅",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "「他很自然地让她先走。细节里藏着教养。」",
        "characters": ["Kai", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
MEDIUM SHOT at the restaurant entrance. A tall young man in black overcoat is holding the door open, his other hand placed gently on the small of a young woman's back, guiding her inside. The gesture is gentlemanly and natural.

The woman with long wavy brown hair and red scarf is stepping through the doorway, her face turned slightly to look back at him with a touched, appreciative smile. His expression shows quiet attentiveness.

COMPOSITION:
- Doorway framing the scene
- Warm golden light spilling from inside the restaurant
- The contrast of cool evening outside and warm interior
- Their body language showing comfortable chemistry

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. CLOTHING: black overcoat, glasses. Gentlemanly posture
- Cici: FACE REFERENCE ONLY. CLOTHING: black coat, red scarf. Appreciative expression

{TEXT_FREE_REQUIREMENT}
"""
    },
    # === 第五幕：餐厅落座 (Shots 15-17) ===
    {
        "shot_id": 15,
        "scene": "餐厅内景",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "「Feloni，思南路上的一家意式小馆。温馨，不张扬。」",
        "characters": [],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
WIDE INTERIOR SHOT of a cozy Italian restaurant. Warm ambient lighting from hanging pendant lamps and candles on tables. The decor features exposed brick walls, wooden furniture, and Italian-inspired artwork.

The atmosphere is intimate and romantic - not too crowded, with soft background lighting. Wooden tables with white tablecloths, wine glasses catching the light. A small bar area visible in the background. Plants and warm decorative elements add charm.

COLOR PALETTE:
- Warm amber and golden lighting
- Rich wood tones
- Cream and white accents
- Touches of green from plants

ATMOSPHERE:
- Romantic but not overly formal
- Cozy and inviting
- Perfect for a first date

{TEXT_FREE_REQUIREMENT}
DO NOT include any readable text, menus, or signs.
"""
    },
    {
        "shot_id": 16,
        "scene": "拉椅子",
        "text_type": "dialogue_with_thought",
        "speaker_position": "left,right,bottom",
        "chinese_text": ["Cici：「谢谢。」", "Kai：「请坐。」", "Cici内心：「好久没遇到这么绅士的男生了。」"],
        "characters": ["Kai", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
MEDIUM SHOT at a restaurant table. A tall young man with black hair and glasses is pulling out a chair for a young woman. He stands behind the chair, hands on the back of it, posture attentive and gentlemanly.

The woman with long wavy brown hair is about to sit, her face showing genuine surprise and delight - eyes widened, a touched smile spreading across her face. She's removed her black coat, revealing a black fitted knit sweater. Her red scarf is now draped over the chair back.

The table has a lit candle, wine glasses, and elegant place settings. Warm candlelight illuminates their faces.

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. CLOTHING: dark purple-black sweater (coat off). Attentive expression
- Cici: FACE REFERENCE ONLY. CLOTHING: black fitted knit sweater. Touched, surprised smile

{TEXT_FREE_REQUIREMENT}
"""
    },
    {
        "shot_id": 17,
        "scene": "相对而坐",
        "text_type": "none",
        "speaker_position": "none",
        "chinese_text": "",
        "characters": ["Kai", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
MEDIUM TWO-SHOT across a restaurant table. A young man and woman sit facing each other at a cozy table for two. Candlelight flickers between them, casting warm golden light on their faces.

LEFT - Kai sits with good posture, wearing a dark purple-black sweater. His black glasses reflect the candlelight. His expression is warm but slightly nervous - the endearing awkwardness of a first date.

RIGHT - Cici sits gracefully, wearing a black fitted sweater. Her long wavy brown hair catches the warm light. Her expression shows excited anticipation, eyes bright.

TABLE SETTING:
- Lit candle centerpiece
- Wine glasses (empty or with water)
- White napkins, elegant but simple plates
- Warm wood table surface

ATMOSPHERE:
- Intimate romantic setting
- Both slightly nervous but happy
- The electricity of possibility

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. CLOTHING: dark purple-black sweater, glasses
- Cici: FACE REFERENCE ONLY. CLOTHING: black fitted knit sweater

{TEXT_FREE_REQUIREMENT}
This shot focuses on the visual atmosphere - no text overlay needed.
Fill the entire frame with the romantic scene.
"""
    },
    # === 第六幕：用餐交谈 (Shots 18-22) ===
    {
        "shot_id": 18,
        "scene": "点餐",
        "text_type": "dialogue_with_thought",
        "speaker_position": "top,bottom",
        "chinese_text": [
            "Kai：「你有什么忌口吗？」",
            "Cici：「不吃香菜，其他都可以。」",
            "Kai：「那我来点？」",
            "Cici：「好呀，你做主。」",
            "Cici内心：「他问忌口，说明很细心。」"
        ],
        "characters": ["Kai", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
MEDIUM SHOT of a young couple looking at a menu together at a restaurant table. They're leaning slightly toward each other, the menu held between them.

Kai (left) is pointing at something on the menu, his expression thoughtful and attentive. He wears a dark purple-black sweater and glasses.

Cici (right) is looking at where he's pointing, her expression curious and trusting. She wears a black fitted knit sweater. Her head is tilted slightly, listening to his suggestions.

The candlelight creates a warm glow. Their body language shows comfortable rapport despite it being a first date.

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. CLOTHING: dark purple-black sweater, glasses. Attentive expression
- Cici: FACE REFERENCE ONLY. CLOTHING: black knit sweater. Trusting, interested expression

{TEXT_FREE_REQUIREMENT}
DO NOT include any readable text on the menu.
Use abstract shapes or blurred content for menu items.
"""
    },
    {
        "shot_id": 19,
        "scene": "开始聊天",
        "text_type": "dialogue",
        "speaker_position": "left,right",
        "chinese_text": ["Cici：「你是做什么工作的？」", "Kai：「互联网，产品经理。你呢？」", "Cici：「设计师，做品牌视觉的。」"],
        "characters": ["Kai", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
MEDIUM TWO-SHOT at a restaurant table with food now served. Elegant Italian dishes are visible - pasta, perhaps some appetizers. Two glasses of red wine on the table.

The couple is engaged in animated conversation, both smiling and relaxed. Their body language is open and engaged.

LEFT - Cici is gesturing slightly as she speaks, her expression curious and engaged. Black knit sweater, wavy brown hair catching the warm light.

RIGHT - Kai is listening with a warm smile, his posture attentive. Dark purple-black sweater, glasses reflecting the candlelight.

The table shows signs of a meal in progress - some food on plates, wine partially consumed. The atmosphere is comfortable and flowing.

CHARACTER REFERENCE:
- Cici: FACE REFERENCE ONLY. Animated, curious expression. CLOTHING: black knit sweater
- Kai: FACE REFERENCE ONLY. Warm listening expression. CLOTHING: dark sweater, glasses

{TEXT_FREE_REQUIREMENT}
"""
    },
    {
        "shot_id": 20,
        "scene": "Kai讲话，Cici听",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "「他讲话的时候，她喜欢看着他的眼睛。」",
        "characters": ["Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
MEDIUM SHOT focusing on a young woman at a restaurant table, with a young man partially visible opposite her (soft focus or cropped at frame edge).

Cici is the focus - she's listening intently to Kai speak. Her expression is captivated and warm. She has one hand resting against her cheek, elbow on table (relaxed, interested posture). Her eyes are bright and focused on him, a soft smile on her lips.

Her long wavy brown hair frames her face beautifully in the candlelight. She wears a black fitted knit sweater. The warm ambient lighting makes her look radiant.

Kai is visible as a soft-focus presence across the table - his gesturing hand, the edge of his sweater, suggesting he's animatedly telling a story.

CHARACTER REFERENCE:
- Cici: FACE REFERENCE ONLY. Captivated, adoring listening expression. CLOTHING: black knit sweater
- Kai: Partially visible, soft focus

{TEXT_FREE_REQUIREMENT}
Cici's enchanted expression is the focus.
"""
    },
    {
        "shot_id": 21,
        "scene": "Cici讲话，Kai听",
        "text_type": "thought",
        "speaker_position": "bottom",
        "chinese_text": "Kai内心：「她讲话的样子真好看。」",
        "characters": ["Kai"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
MEDIUM SHOT focusing on a young man at a restaurant table, with a young woman partially visible opposite him (soft focus or cropped at frame edge).

Kai is the focus - he's listening to Cici with complete attention. His expression is warm and tender, a gentle smile on his lips. His eyes behind his glasses are soft and admiring. He's leaning slightly forward, completely engaged.

He wears a dark purple-black sweater. The candlelight reflects in his glasses and illuminates his attentive expression.

Cici is visible as a soft-focus presence - her gesturing hands, the movement of her hair as she speaks animatedly about something.

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Tender, admiring listening expression. CLOTHING: dark purple-black sweater, glasses
- Cici: Partially visible, soft focus. CLOTHING: BLACK knit sweater (NOT beige, NOT brown, NOT cream!)

CHARACTER CONSISTENCY REQUIREMENT:
- If Cici is visible (even partially), she MUST wear BLACK knit sweater
- DO NOT substitute with beige, brown, cream, or any light-colored sweater
- Her wavy brown hair should be visible

{TEXT_FREE_REQUIREMENT}
Kai's gentle, admiring expression is the focus.
"""
    },
    {
        "shot_id": 22,
        "scene": "眼神交汇",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "「有些瞬间，不需要言语。」",
        "characters": ["Kai", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
CLOSE-UP TWO-SHOT capturing an intimate moment of eye contact across the table. Both characters' faces in frame, looking at each other with a moment of shared connection.

The moment captures that electric instant when both happen to look up at the same time - a beat of surprised recognition, then soft smiles spreading on both faces.

LEFT - Cici's face in close-up, her warm brown eyes meeting his gaze, a gentle surprised smile, cheeks slightly flushed.

RIGHT - Kai's face in close-up, his eyes behind glasses showing warmth and connection, a matching smile forming.

ROMANTIC ATMOSPHERE:
- Soft candlelight between them (visible in lower frame)
- Warm color tones
- The air feels charged with unspoken attraction
- Korean webtoon style soft glow/sparkle effects subtle around their eyes

CHARACTER REFERENCE:
- Cici: FACE REFERENCE ONLY. Soft surprised smile, warm eyes. CLOTHING: BLACK fitted knit sweater (NOT beige, NOT teal, NOT any light color!)
- Kai: FACE REFERENCE ONLY. Gentle smile, warm gaze through glasses. CLOTHING: dark purple-black sweater

{TEXT_FREE_REQUIREMENT}
Their eyes and expressions are the absolute focus.
"""
    },
    # === 第七幕：甜点时光 (Shots 23-24) ===
    {
        "shot_id": 23,
        "scene": "甜点上桌",
        "text_type": "dialogue",
        "speaker_position": "left,right",
        "chinese_text": ["Kai：「你试试这个，他们家招牌。」", "Cici：「看起来好好吃！」"],
        "characters": ["Kai", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
MEDIUM SHOT of a restaurant table with dessert just served. A beautiful tiramisu sits in the center, with two cups of coffee. The main dinner plates have been cleared.

LEFT - Kai gestures toward the tiramisu with a recommending expression, looking at Cici. He wears a dark purple-black sweater, glasses.

RIGHT - Cici looks at the dessert with delighted eyes and an excited smile. Her expression is like a child seeing a treat. Black knit sweater, wavy brown hair.

The lighting is warm and intimate. The tiramisu looks delicious - layers of coffee-soaked ladyfingers and cream visible.

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Recommending, pleased expression. CLOTHING: dark purple-black sweater, glasses
- Cici: FACE REFERENCE ONLY. Delighted, excited expression. CLOTHING: BLACK knit sweater (NOT beige, NOT brown!)

CHARACTER CONSISTENCY REQUIREMENT:
- Kai: MUST wear dark purple-black sweater with glasses
- Cici: MUST wear BLACK knit sweater - NO color substitution
- Both characters' clothing must match their established appearance in this restaurant scene

{TEXT_FREE_REQUIREMENT}
"""
    },
    {
        "shot_id": 24,
        "scene": "喂食瞬间",
        "text_type": "dialogue_with_thought",
        "speaker_position": "top,bottom",
        "chinese_text": ["Kai：「尝尝。」", "Cici内心：「这也太自然了...我们才第一次见面诶。」"],
        "characters": ["Kai", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
CLOSE to MEDIUM SHOT of an intimate moment. A young man is extending a spoon with a small piece of tiramisu toward a young woman across the table. The gesture is natural and caring.

Kai's expression is gentle and encouraging, holding the spoon steadily. He wears a dark purple-black sweater, glasses.

Cici's reaction shows surprised delight mixed with shyness - eyes widened, a slight blush on her cheeks, leaning forward slightly to accept. Her lips are parted, about to accept the offered bite. Expression is flustered but happy. Black knit sweater, wavy brown hair.

The candlelight adds romantic warmth. The moment feels natural despite it being a first date.

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Gentle, caring expression. CLOTHING: dark sweater, glasses
- Cici: FACE REFERENCE ONLY. Surprised, shy but pleased expression. CLOTHING: black knit sweater

{TEXT_FREE_REQUIREMENT}
"""
    },
    # === 第八幕：餐后散步 (Shots 25-29) ⭐ 情感重点2 ===
    {
        "shot_id": 25,
        "scene": "离开餐厅",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "「晚餐结束，谁都没有提要回家。」",
        "characters": ["Kai", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
MEDIUM SHOT of a young couple stepping out of a warmly-lit restaurant onto the evening street. Both have put their coats back on.

Kai holds the door, wearing his black overcoat over dark sweater, glasses catching the light. His expression is content and happy.

Cici steps out beside him, wearing her black long coat with red scarf visible. Her wavy brown hair moves slightly in the cool evening air. She looks up at the night sky, expression peaceful and reluctant for the evening to end.

The restaurant's warm light spills out behind them. The street is dark but romantic with street lamps glowing. The night has fully fallen.

INTIMACY LEVEL CONSTRAINT (First Date):
- This is a FIRST DATE scenario - characters have just met today
- Maintain appropriate physical distance (arm's length minimum)
- Body language should be warm but reserved, NOT overtly romantic
- They are walking side by side with natural personal space
- NO embracing, NO hand-holding, NO arm linking, NO leaning into each other
- The mood is "getting to know each other" NOT "established couple"

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Content expression. CLOTHING: black overcoat, glasses
- Cici: FACE REFERENCE ONLY. Peaceful, slightly wistful expression. CLOTHING: black coat, red scarf

{TEXT_FREE_REQUIREMENT}
"""
    },
    {
        "shot_id": 26,
        "scene": "漫步思南路",
        "text_type": "narration",
        "speaker_position": "top",
        "chinese_text": "「他们沿着思南路慢慢走，聊着天，不想这个夜晚结束。」",
        "characters": ["Kai", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
WIDE to MEDIUM SHOT of a young couple walking side by side down a beautiful tree-lined street at night. The famous plane trees of Shanghai's French Concession create a canopy above.

Street lamps cast warm golden pools of light. The colonial architecture creates a romantic European atmosphere. Fallen autumn leaves scattered on the cobblestones. The couple walks with comfortable personal space between them.

Kai is on the left, tall in his black overcoat, hands in pockets. Cici is on the right, her red scarf bright against the night, hair flowing behind her. Both are talking and smiling, comfortable with each other.

INTIMACY LEVEL CONSTRAINT (First Date):
- This is a FIRST DATE scenario - characters have just met today
- Maintain appropriate physical distance (arm's length between them)
- Body language should be warm but reserved, NOT overtly romantic
- They walk side by side with clear personal space, NOT pressed together
- NO embracing, NO hand-holding, NO arm linking, NO leaning into each other
- Expressions should show curiosity and gentle interest, NOT passion
- The mood is "getting to know each other" NOT "established couple"

ATMOSPHERIC DETAILS:
- Beautiful night scene with warm lamp light
- Romantic European-style architecture
- Autumn leaves and bare tree branches
- Intimate but public setting

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Relaxed, happy expression. CLOTHING: black overcoat
- Cici: FACE REFERENCE ONLY. Animated, happy expression. CLOTHING: black coat, red scarf

{TEXT_FREE_REQUIREMENT}
"""
    },
    {
        "shot_id": 27,
        "scene": "靠近",
        "text_type": "thought",
        "speaker_position": "bottom",
        "chinese_text": "Cici内心：「过马路的时候，他轻轻护着我...好贴心。」",
        "characters": ["Kai", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
MEDIUM SHOT from the side, capturing a sweet moment as a young couple crosses a nighttime street. Kai instinctively places his hand gently on Cici's back - a natural protective gesture as they cross together.

Kai on the left in black overcoat, his right hand lightly touching Cici's upper back, guiding her across. Cici on the right in black coat with red scarf. This is a PROTECTIVE TOUCH, not romantic - the gesture of someone naturally watching out for another.

Cici's expression shows pleasant surprise at his thoughtfulness - eyes widening slightly, a small smile forming. Kai's expression is calm and attentive, looking ahead to check for traffic while keeping her safe.

INTIMACY LEVEL CONSTRAINT (First Date):
- This is a FIRST DATE scenario - characters have just met today
- The touch is PROTECTIVE (like helping someone cross street), NOT romantic
- This is a gentleman's instinct, NOT a couple's intimacy
- NO arm linking, NO hand-holding, NO leaning into each other
- Body language shows care and respect, NOT passion or possession
- The mood is "he's looking out for her" NOT "they're a couple"

STREET CROSSING SCENE:
- They are crossing at a street or intersection
- Warm street lamp light from above
- Romantic French Concession architecture
- Night time, quiet street
- Their breath visible in cool air (subtle)

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Calm protective expression, watching ahead. CLOTHING: black overcoat
- Cici: FACE REFERENCE ONLY. Pleasant surprise, touched by his gesture. CLOTHING: black coat, red scarf

{TEXT_FREE_REQUIREMENT}
"""
    },
    {
        "shot_id": 28,
        "scene": "牵手前奏",
        "text_type": "thought",
        "speaker_position": "top",
        "chinese_text": "Kai内心：「我可以...牵她的手吗？」",
        "characters": [],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
CLOSE-UP SHOT of two hands walking side by side on a nighttime street. A quiet moment of closeness between two people.

LEFT - A man's hand with relaxed fingers, swinging naturally while walking. Simple black leather watch visible at wrist. Black coat sleeve.

RIGHT - A woman's hand with delicate fingers, relaxed in natural walking posture. Simple gold bracelet visible. Black coat sleeve.

The two hands are close together, walking in comfortable closeness. A moment of quiet anticipation.

BACKGROUND:
- Soft focus cobblestone street
- Warm lamp light creating highlights on their hands
- Romantic bokeh lights in background

CHARACTER DETAILS:
- Kai's hand: masculine but gentle, relaxed at his side
- Cici's hand: feminine and graceful, natural position

ANATOMY REQUIREMENT:
- Each hand must have exactly 5 fingers
- Wrists must connect naturally to arms
- No duplicate or distorted limbs

{TEXT_FREE_REQUIREMENT}
The hands and the gentle moment are the focus.
"""
    },
    {
        "shot_id": 29,
        "scene": "牵手 ⭐【情感重点2】",
        "text_type": "narration_with_thought",
        "speaker_position": "top,bottom",
        "chinese_text": [
            "旁白：「他握住了她的手。她没有松开。」",
            "Kai内心：「她的手好软...好温暖。」",
            "Cici内心：「心跳好快...但是，好安心。」"
        ],
        "characters": [],
        "is_emotional_highlight": True,
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
⭐ EMOTIONAL HIGHLIGHT SHOT ⭐

DUAL COMPOSITION combining hand close-up and couple silhouette:

PRIMARY FOCUS - CLOSE-UP of two hands now clasped together, fingers interlaced. The moment of connection captured beautifully.
- His hand: larger, protective, gently holding
- Her hand: smaller, delicate, holding back with equal tenderness
- Warm light highlighting the point of contact
- His black watch, her gold bracelet visible

SECONDARY (upper portion or inset) - The silhouettes of the couple walking hand in hand under the glow of a street lamp. Romantic night atmosphere, bare winter trees framing them.

ROMANTIC ELEMENTS:
- Warm golden light emphasizing the connected hands
- Subtle sparkle effect (Korean webtoon style)
- The contrast between intimate close-up and wider context
- Night atmosphere with warm lamp glow

CHARACTER REFERENCE:
- Kai: defined masculine hand, black coat, leather watch
- Cici: delicate feminine hand, black coat, RED scarf visible, gold bracelet

CHARACTER CONSISTENCY REQUIREMENT:
- Kai: MUST wear BLACK wool overcoat
- Cici: MUST wear BLACK long coat with RED silk scarf (scarf MUST be visible in silhouette)
- DO NOT substitute colors - Cici's scarf is RED, not any other color
- In silhouette view, ensure the red scarf is recognizable

{TEXT_FREE_REQUIREMENT}
The connected hands are the emotional center.
"""
    },
    # === 第九幕：地铁站前 (Shots 30-31) ===
    {
        "shot_id": 30,
        "scene": "到达地铁站",
        "text_type": "dialogue",
        "speaker_position": "right",
        "chinese_text": "Cici：「地铁站到了...我该回去了。」",
        "characters": ["Kai", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
MEDIUM SHOT of a young couple standing at a metro station entrance at night. They're still holding hands, both looking reluctant.

The metro entrance is visible in background - modern architecture with descending stairs and lighting from below. Other pedestrians are distant, giving them privacy.

Kai stands on the left, his expression showing he doesn't want the evening to end. He holds her hand gently.

Cici on the right looks torn - part of her knows she should go, but her body language (leaning slightly toward him, reluctant expression) shows she doesn't want to.

Both are in their coats - his black overcoat, her black coat with red scarf. Their joined hands are visible at center frame.

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Reluctant, hopeful expression. CLOTHING: black overcoat
- Cici: FACE REFERENCE ONLY. Torn, reluctant expression. CLOTHING: black coat, red scarf

{TEXT_FREE_REQUIREMENT}
"""
    },
    {
        "shot_id": 31,
        "scene": "提议送她",
        "text_type": "dialogue",
        "speaker_position": "left,right",
        "chinese_text": ["Kai：「我开车送你吧。这个点地铁挤。」", "Cici：「可是...你不顺路吧？」", "Kai：「送你回家，就是最顺的路。」"],
        "characters": ["Kai", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
CLOSE TWO-SHOT of the couple facing each other near the metro entrance. The moment Kai offers to drive her home.

Kai's expression is earnest and gentlemanly, looking at her with warmth. He gestures slightly toward another direction (where his car might be parked).

Cici's expression shows being "swept off her feet" - surprised, touched, a blush spreading across her cheeks, eyes bright with happiness. The classic Korean romance moment of being charmed.

Night lighting creates dramatic shadows. Their faces are well-lit, emotional.

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Earnest, charming expression. CLOTHING: black overcoat, glasses
- Cici: FACE REFERENCE ONLY. Flustered, touched, blushing expression. CLOTHING: black coat, red scarf

{TEXT_FREE_REQUIREMENT}
"""
    },
    # === 第十幕：车内时光 (Shots 32-35) ===
    {
        "shot_id": 32,
        "scene": "走向车边",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "「他的车停在不远处。」",
        "characters": ["Kai", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
MEDIUM to WIDE SHOT of a young couple walking through a quiet parking area at night. Kai leads slightly, looking back at Cici with a warm expression. She follows with a happy, trusting smile.

The setting is a small street-side parking area, not an enclosed garage. Street lamps provide warm lighting. A modest, clean car (sedan, dark color) is visible nearby - nothing flashy, just practical and well-maintained.

Both are in winter coats. Their body language shows comfortable companionship - not holding hands in this shot, but walking close together.

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Looking back warmly. CLOTHING: black overcoat
- Cici: FACE REFERENCE ONLY. Happy, trusting smile. CLOTHING: black coat, red scarf

{TEXT_FREE_REQUIREMENT}
DO NOT include any readable text or license plates.
"""
    },
    {
        "shot_id": 33,
        "scene": "开车门",
        "text_type": "dialogue_with_thought",
        "speaker_position": "left,bottom",
        "chinese_text": ["Kai：「请上车。」", "Cici内心：「今晚被照顾得太好了...」"],
        "characters": ["Kai", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
MEDIUM SHOT of Kai holding open the passenger door of his car for Cici. The chivalrous gesture captured mid-action.

Kai stands by the open door with a gentle, inviting expression, gesturing for her to enter. His posture is attentive and caring.

Cici is stepping toward the car, her expression showing touched appreciation - a soft smile, eyes warm with gratitude. She's looking at him with affection.

The car interior light illuminates them both warmly. Night setting with street lamps in background.

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Gentle, inviting expression. CLOTHING: black overcoat
- Cici: FACE REFERENCE ONLY. Touched, appreciative expression. CLOTHING: black coat, red scarf

{TEXT_FREE_REQUIREMENT}
"""
    },
    {
        "shot_id": 34,
        "scene": "车内对话",
        "text_type": "dialogue",
        "speaker_position": "left,right",
        "chinese_text": ["Cici：「你开车很稳。」", "Kai：「副驾有贵客，当然要稳。」"],
        "characters": ["Kai"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
INTERIOR CAR SHOT from Cici's POV (passenger seat perspective). Shows Kai in the driver's seat, hands on the wheel, driving smoothly. His profile is visible, expression focused but relaxed.

The dashboard provides soft illumination. Outside the windshield, city lights blur past. The atmosphere inside is warm and intimate despite the car being in motion.

Kai wears his dark sweater (coat off while driving). His glasses reflect the passing lights. He occasionally glances toward the passenger seat (toward camera) with a warm smile.

COMPOSITION REQUIREMENT:
- Frame ends at center console - do NOT show passenger seat area
- Cici is NOT VISIBLE in this shot (camera is from her POV)
- Do NOT include partial body parts at frame edges
- All visible body parts must be complete and natural

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Focused but happy while driving. CLOTHING: dark purple-black sweater, glasses

{TEXT_FREE_REQUIREMENT}
DO NOT include any readable dashboard text or signs.
"""
    },
    {
        "shot_id": 35,
        "scene": "窗外夜景",
        "text_type": "narration_with_thought",
        "speaker_position": "top,bottom",
        "chinese_text": ["旁白：「窗外是流动的灯光，车内是安心的沉默。」", "Cici内心：「原来，和对的人在一起，沉默也很舒服。」"],
        "characters": ["Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
INTERIOR CAR SHOT focusing on Cici in the passenger seat. She's gazing out the window, her face partially reflected in the glass. Her expression is peaceful and content, a soft smile on her lips.

Through the window, the Shanghai night cityscape flows by in beautiful bokeh - neon lights, building silhouettes, the magic of the city at night. Her reflection overlays these lights.

She wears her black knit sweater, coat draped over her lap. Her long wavy brown hair frames her face. The passing lights create changing illumination on her features.

EMOTIONAL ATMOSPHERE:
- Dreamy, peaceful contentment
- The city lights as backdrop to her thoughts
- Intimate car interior versus expansive city
- The quiet comfort of being with the right person

CHARACTER REFERENCE:
- Cici: FACE REFERENCE ONLY. Peaceful, content, dreamy expression. CLOTHING: black knit sweater

{TEXT_FREE_REQUIREMENT}
"""
    },
    # === 第十一幕：告别 (Shots 36-41) ⭐ 情感重点3、4 ===
    {
        "shot_id": 36,
        "scene": "到达楼下",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "「太快了。她家到了。」",
        "characters": ["Kai", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
WIDE SHOT of a residential area entrance at night. A car is parked by the curb, and both figures have just gotten out, standing by the vehicle.

The residential entrance shows a modern Shanghai apartment complex - clean, well-lit entrance with some greenery. A security booth with soft light. The neighborhood is quiet, peaceful.

Both are back in their coats, standing close together by the car. Their body language shows reluctance to part - facing each other rather than walking toward the entrance.

Street lamps provide warm lighting. The night is deep but not too cold.

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Standing by car. CLOTHING: black overcoat
- Cici: FACE REFERENCE ONLY. Standing close to him. CLOTHING: black coat, red scarf

{TEXT_FREE_REQUIREMENT}
"""
    },
    {
        "shot_id": 37,
        "scene": "依依不舍",
        "text_type": "dialogue",
        "speaker_position": "left,right",
        "chinese_text": ["Cici：「今天...真的很开心。谢谢你。」", "Kai：「我也是。谢谢你愿意来见我。」"],
        "characters": ["Kai", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
MEDIUM TWO-SHOT of the couple standing face to face under a street lamp near the residential entrance. The warm lamp light creates an intimate golden pool around them.

Both their expressions show reluctance to say goodbye - lingering, not wanting this moment to end.

Cici looks up at him with soft, grateful eyes. Her expression is tender, with a touch of sadness that the night is ending.

Kai looks down at her with warmth and the unspoken wish for more time. His expression is gentle, protective.

The quiet night surrounds them. Only the hum of the city in the far background.

CHARACTER REFERENCE:
- Cici: FACE REFERENCE ONLY. Tender, grateful, slightly sad expression. CLOTHING: black coat, red scarf
- Kai: FACE REFERENCE ONLY. Warm, protective, reluctant expression. CLOTHING: black overcoat, glasses

{TEXT_FREE_REQUIREMENT}
"""
    },
    {
        "shot_id": 38,
        "scene": "拥抱 ⭐【情感重点3】",
        "text_type": "narration_with_thought",
        "speaker_position": "top,bottom",
        "chinese_text": ["旁白：「她上前一步，抱住了他。没有犹豫。」", "Kai内心：「她身上有淡淡的香味...像是...柑橘和茉莉。」"],
        "characters": ["Kai", "Cici"],
        "is_emotional_highlight": True,
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
⭐ EMOTIONAL HIGHLIGHT SHOT ⭐

MEDIUM SHOT of an embrace under the warm glow of a street lamp. Cici has stepped forward and wrapped her arms around Kai. He embraces her back, his arms gentle around her.

The moment is tender and natural - not overly dramatic, but deeply emotional. Her face is pressed against his chest or shoulder. His chin might rest near the top of her head, expression showing touched surprise turning to gentle happiness.

VISUAL DETAILS:
- Warm golden street lamp light enveloping them
- Her long wavy hair visible
- IMPORTANT: Cici wears a BLACK wool coat (NOT red!) with a vibrant red silk SCARF around her neck
- Their body language shows comfort and trust
- Subtle mist or gentle bokeh in the night air adds romance

EMOTIONAL QUALITY:
- The courage of making the first move (her)
- The warmth of acceptance (him)
- A milestone moment in their connection

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Touched, gentle happiness. CLOTHING: BLACK wool overcoat (not any other color)
- Cici: FACE REFERENCE ONLY (if visible). Content, brave. CLOTHING: BLACK long wool coat (NOT red, NOT teal, NOT any other color!), vibrant red silk SCARF at neck only

{TEXT_FREE_REQUIREMENT}
The embrace is the emotional center.
"""
    },
    {
        "shot_id": 39,
        "scene": "分开后对视",
        "text_type": "none",
        "speaker_position": "none",
        "chinese_text": "",
        "characters": ["Kai", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
CLOSE TWO-SHOT of the couple's faces very close together, having just separated from the embrace. The distance between them is only about 20 centimeters. The air between them is charged with tension and possibility.

Cici's eyes shine with emotion, looking up at him. Her expression holds warmth and something unspoken - the courage building for what comes next.

Kai's eyes behind his glasses are soft and deep, looking down at her. His expression shows tender wonder and restrained longing.

INTIMATE ATMOSPHERE:
- Extremely close proximity
- Warm street lamp lighting on their faces
- The suggestion of possibility hanging in the air
- Korean webtoon romantic tension - the moment before something happens
- Subtle sparkle effects around their eyes

CHARACTER REFERENCE:
- Cici: FACE REFERENCE ONLY. Emotional, eyes shining, courage building. CLOTHING: BLACK long wool coat (NOT teal, NOT any other color!), red silk scarf at neck
- Kai: FACE REFERENCE ONLY. Tender wonder, restrained longing. CLOTHING: BLACK wool overcoat, glasses

{TEXT_FREE_REQUIREMENT}
This is a pure atmosphere shot - no text overlay needed.
Their eyes and the tension between them are everything.
"""
    },
    {
        "shot_id": 40,
        "scene": "脸颊之吻 ⭐【情感重点4】",
        "text_type": "narration_with_dialogue",
        "speaker_position": "top,bottom",
        "chinese_text": ["旁白：「他鼓起勇气，在她脸颊偷偷落下一吻。」", "Cici：「...晚安。」"],
        "characters": ["Kai", "Cici"],
        "is_emotional_highlight": True,
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
⭐ EMOTIONAL HIGHLIGHT SHOT - THE KISS ⭐

CLOSE-UP SHOT capturing the moment Kai leans in to steal a gentle kiss on Cici's cheek - a sweet, spontaneous gesture of affection.

His lips are lightly touching her cheek - a soft, quick peck. His eyes are gently closed in the tender moment. His glasses slightly tilted from leaning in.

Her expression is captured in the moment of surprised delight - eyes widening, frozen in pleasant shock, a blush spreading across her cheeks, a smile just beginning to form. Her long wavy hair frames her face, red scarf visible.

ROMANTIC ELEMENTS:
- He leans down slightly to reach her cheek (sweet height difference)
- Soft warm lighting on both faces
- Korean webtoon sparkle/glow effects
- The sweetness and innocence of a first kiss on the cheek
- His brave initiative, her charmed and flustered reaction

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Eyes gently closed, leaning in for the kiss. CLOTHING: BLACK wool overcoat, glasses
- Cici: FACE REFERENCE ONLY. Surprised delight, blushing, eyes wide. CLOTHING: BLACK long wool coat (NOT red, NOT teal!), vibrant red silk SCARF at neck

{TEXT_FREE_REQUIREMENT}
The kiss on the cheek is the absolute focus - beautiful and tender.
"""
    },
    {
        "shot_id": 41,
        "scene": "Kai的反应",
        "text_type": "thought",
        "speaker_position": "bottom",
        "chinese_text": "Kai内心：「这一刻，我知道...她就是那个人。」",
        "characters": ["Kai"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
CLOSE-UP on Kai's face, capturing his reaction right after he kissed Cici's cheek. He's watching her reaction with nervous anticipation.

His expression shows a mix of emotions: the bold courage fading into nervous hope, his eyes searching her face for her response. His eyes behind his glasses are wide and expectant, a shy but hopeful smile forming.

He's slightly pulling back after the kiss, watching to see if she's upset or happy. His expression is vulnerable - he took a risk and now awaits the verdict. A blush visible on his own cheeks from the bold move he just made.

BACKGROUND:
- Soft blur of the night scene
- Warm street lamp glow
- Cici's blurred figure in front of him

EMOTIONAL QUALITY:
- Nervous anticipation after taking a bold step
- Hopeful vulnerability
- The moment of "did I do the right thing?"

CHARACTER REFERENCE:
- Kai: FACE REFERENCE ONLY. Nervous hopeful expression, slight blush, watching for her reaction. CLOTHING: black overcoat, glasses

{TEXT_FREE_REQUIREMENT}
His vulnerable, hopeful expression is the focus.
"""
    },
    # === 第十二幕：余韵 (Shot 42) ===
    {
        "shot_id": 42,
        "scene": "目送与回眸",
        "text_type": "narration_with_dialogue",
        "speaker_position": "top,bottom",
        "chinese_text": ["Cici：「明天聊！」", "旁白：「那个冬夜，思南路的风很轻，两颗心却跳得很快。」", "旁白：「这是他们的开始。」"],
        "characters": ["Kai", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
WIDE to MEDIUM SHOT showing the final moment of the night. Two figures separated by some distance near the residential entrance.

IN FOREGROUND: Kai stands watching, his expression a soft, content smile. He raises one hand in a gentle wave.

IN BACKGROUND/MIDGROUND: Cici has walked toward the entrance but has turned back, waving at him. Her expression is radiant, happy, already looking forward to next time.

The scene captures the bittersweet beauty of parting - the physical distance between them contrasted with the emotional closeness they've built.

ATMOSPHERIC DETAILS:
- Warm street lamp creating pools of golden light
- The residential entrance softly lit behind Cici
- Perhaps bare winter trees framing the scene
- The romantic atmosphere of a winter night

CHARACTER REFERENCE:
- Kai (foreground): FACE REFERENCE ONLY. Content, soft smile, waving. CLOTHING: black overcoat
- Cici (background): FACE REFERENCE ONLY. Radiant smile, waving, turned back. CLOTHING: black coat, red scarf

{TEXT_FREE_REQUIREMENT}
The distance between them and their shared smiles tell the story.
"""
    },
]

# =============================================================================
# 数据类型定义
# =============================================================================

@dataclass
class TextSegment:
    text: str
    emphasis: str = "none"

@dataclass
class TextEmphasis:
    original_text: str
    segments: List[TextSegment] = field(default_factory=list)

# =============================================================================
# 文字叠加服务 - 已迁移到主服务
# =============================================================================
# ARCH-3: TextOverlayService、strip_speaker_prefix、get_bubble_position_for_index、
#         detect_overlay_collision 现在从 app.services.text_overlay_service 导入
# 这确保了所有故事（Kai与Cici、武侠、赛博朋克等）使用相同的实现

# =============================================================================
# 图像生成
# =============================================================================

_image_generator = None

def get_image_generator():
    global _image_generator
    if _image_generator is None:
        _image_generator = ImageGenerator()
    return _image_generator

def load_existing_reference_images() -> Dict[str, Image.Image]:
    """加载现有的参考图文件"""
    ref_images = {}

    # Cici fullbody
    cici_path = EXISTING_REF_DIR / "CC_fullbody.png"
    if cici_path.exists():
        ref_images["Cici"] = Image.open(cici_path)
        print(f"  ✅ 加载 Cici 参考图: {cici_path}")
    else:
        print(f"  ⚠️ Cici 参考图不存在: {cici_path}")

    # Kai fullbody
    kai_path = EXISTING_REF_DIR / "Kai_fullbody.png"
    if kai_path.exists():
        ref_images["Kai"] = Image.open(kai_path)
        print(f"  ✅ 加载 Kai 参考图: {kai_path}")
    else:
        print(f"  ⚠️ Kai 参考图不存在: {kai_path}")

    return ref_images

def build_character_reference_instruction(characters_in_shot: List[str]) -> str:
    """构建角色参考图指令"""
    if not characters_in_shot:
        return ""

    instructions = ["\nCHARACTER REFERENCE IMAGES:"]
    instructions.append("The following reference images show the characters' FACE FEATURES ONLY.")
    instructions.append("CRITICAL: Use face shape, features, hair from reference. IGNORE clothing in reference images.")
    instructions.append("")

    for i, char_id in enumerate(characters_in_shot):
        char = CHARACTERS.get(char_id)
        if char:
            instructions.append(f"Reference Image {i + 1}: {char['name_en']}")
            physical = char.get('physical', {})
            clothing = char.get('clothing', {})

            # 脸部特征
            instructions.append(f"  - FACE: {physical.get('face_shape', '')}, {physical.get('hair_color', '')} {physical.get('hair_style', '')}")
            if "glasses" in str(physical.get('distinctive_marks', [])):
                instructions.append(f"  - DISTINCTIVE: black rectangular glasses")

            # 故事服装（不是参考图服装）
            instructions.append(f"  - CLOTHING (USE THIS, NOT REFERENCE): {clothing.get('top', '')}, {clothing.get('outerwear', '')}")
            if clothing.get('accessories'):
                instructions.append(f"  - ACCESSORIES: {', '.join(clothing['accessories'][:2])}")

    instructions.append("")
    instructions.append("IMPORTANT: Maintain consistent character appearance throughout the story.")

    return "\n".join(instructions)

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

async def run_cc_kai_story_test():
    """运行Kai与Cici故事测试"""

    print("=" * 70)
    print("Kai与Cici初次约会 - 条漫故事测试")
    print("42张图完整故事，Korean Webtoon风格")
    print("使用现有参考图（仅脸部特征），服装使用故事描述")
    print("=" * 70)

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    NO_TEXT_DIR.mkdir(parents=True, exist_ok=True)
    WITH_TEXT_DIR.mkdir(parents=True, exist_ok=True)
    COMPARISON_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n输出目录: {OUTPUT_DIR}")

    # 初始化文字叠加服务
    try:
        text_service = TextOverlayService()
        print(f"字体: {text_service.font_path}")
    except RuntimeError as e:
        print(f"❌ 初始化失败: {e}")
        return

    # Step 1: 加载现有参考图
    print("\n" + "=" * 70)
    print("Step 1: 加载现有参考图")
    print("=" * 70)

    ref_images = load_existing_reference_images()
    print(f"\n参考图加载完成: {len(ref_images)}/2")

    if len(ref_images) < 2:
        print("⚠️ 警告：部分参考图缺失，角色一致性可能受影响")

    # Step 2: 生成故事图
    print("\n" + "=" * 70)
    print("Step 2: 生成故事图 (42张)")
    print("=" * 70)

    results = []
    success_count = 0
    fail_count = 0

    print(f"\n开始生成 {len(FULL_STORY_SHOTS)} 张图...")
    print("-" * 70)

    for shot in FULL_STORY_SHOTS:
        shot_id = shot["shot_id"]
        scene = shot["scene"]
        char_ids = shot.get("characters", [])
        is_highlight = shot.get("is_emotional_highlight", False)

        print(f"\n[Shot {shot_id:02d}] {scene}")
        if is_highlight:
            print(f"  ⭐ 情感重点镜头")
        if char_ids:
            print(f"  👥 角色: {', '.join(char_ids)}")

        # 收集参考图
        reference_images = []
        for char_id in char_ids:
            if char_id in ref_images:
                reference_images.append(ref_images[char_id])
                print(f"  📷 使用 {char_id} 参考图")

        # 构建角色参考指令
        char_instruction = build_character_reference_instruction(char_ids)

        # 生成无文字图像
        result = await generate_image_with_refs(
            prompt=shot["image_prompt"],
            shot_id=shot_id,
            output_dir=NO_TEXT_DIR,
            reference_images=reference_images,
            char_instruction=char_instruction
        )

        if result["success"]:
            success_count += 1
            print(f"  ✅ 图像生成成功 (使用 {result.get('ref_count', 0)} 张参考图)")

            original_image = result["pil_image"]

            # 叠加文字
            processed_image = text_service.process_shot(original_image, shot)

            # 保存带文字版本
            with_text_path = WITH_TEXT_DIR / f"shot_{shot_id:02d}.png"
            processed_image.save(with_text_path)
            print(f"  ✅ 文字叠加完成")

            # 创建对比图
            comparison = create_comparison(original_image, processed_image, f"Shot {shot_id:02d}: {scene}")
            comparison_path = COMPARISON_DIR / f"comparison_{shot_id:02d}.png"
            comparison.save(comparison_path)

            results.append({
                "shot_id": shot_id,
                "scene": scene,
                "success": True,
                "no_text_path": str(result["image_path"]),
                "with_text_path": str(with_text_path),
                "comparison_path": str(comparison_path),
                "ref_count": result.get("ref_count", 0)
            })
        else:
            fail_count += 1
            print(f"  ❌ 生成失败: {result.get('error', 'Unknown error')}")
            results.append({
                "shot_id": shot_id,
                "scene": scene,
                "success": False,
                "error": result.get("error", "Unknown error")
            })

        # 延迟避免API限流
        await asyncio.sleep(2)

    # Step 3: 生成报告
    print("\n" + "=" * 70)
    print("Step 3: 生成测试报告")
    print("=" * 70)

    report = {
        "test_name": "Kai与Cici初次约会",
        "timestamp": datetime.now().isoformat(),
        "total_shots": len(FULL_STORY_SHOTS),
        "success_count": success_count,
        "fail_count": fail_count,
        "success_rate": f"{success_count / len(FULL_STORY_SHOTS) * 100:.1f}%",
        "style": "Korean Webtoon Style",
        "model": GEMINI_MODEL,
        "use_pro_model": USE_PRO_MODEL,
        "results": results
    }

    report_path = OUTPUT_DIR / "test_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"报告保存: {report_path}")

    # 打印摘要
    print("\n" + "=" * 70)
    print("测试完成摘要")
    print("=" * 70)
    print(f"总图片数: {len(FULL_STORY_SHOTS)}")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"成功率: {success_count / len(FULL_STORY_SHOTS) * 100:.1f}%")
    print(f"\n输出目录: {OUTPUT_DIR}")
    print(f"  - 无文字图片: {NO_TEXT_DIR}")
    print(f"  - 带文字图片: {WITH_TEXT_DIR}")
    print(f"  - 对比图: {COMPARISON_DIR}")

    return report

# =============================================================================
# 入口点
# =============================================================================

if __name__ == "__main__":
    asyncio.run(run_cc_kai_story_test())
