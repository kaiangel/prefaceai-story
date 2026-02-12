"""
条漫完整故事测试脚本 - 《最后一碗面》
15张图完整故事测试，验证端到端能力

故事脚本: docs/COMIC_FULL_STORY_SCRIPT.md
风格: Ghibli-inspired warm illustration

任务: HANDOFF-2026-01-22-009 / TASK-B
作者: @Backend
日期: 2026-01-22
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple

from PIL import Image, ImageDraw, ImageFont

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.image_generator import ImageGenerator
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
USE_PRO_MODEL = False  # 先用Flash测试

# 输出目录
OUTPUT_DIR = Path(__file__).parent.parent / "test_output" / "comic_full_story_test"
NO_TEXT_DIR = OUTPUT_DIR / "no_text_images"
WITH_TEXT_DIR = OUTPUT_DIR / "with_text_images"
COMPARISON_DIR = OUTPUT_DIR / "comparison"

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
# 角色定义 (从 COMIC_FULL_STORY_SCRIPT.md)
# =============================================================================

CHARACTERS = {
    # 女儿 - 现在 (28岁)
    "daughter_present": {
        "name": "陈小雨",
        "name_en": "Chen Xiaoyu",
        "age": 28,
        "physical": "young woman with short modern bob cut black hair slightly above shoulders, dark brown almond gentle eyes, fair skin with warm undertone, oval face with soft features, small mole below left ear",
        "clothing_default": "beige wool trench coat over crisp white blouse, black slim-fit dress pants, black leather flats, small gold stud earrings, simple black leather watch",
        "clothing_hospital": "soft cream sweater with sleeves rolled up",
        "clothing_kitchen": "simple white blouse with sleeves rolled up",
        "clothing_apron": "simple white blouse with a white apron"
    },
    # 女儿 - 童年 (10岁)
    "daughter_child": {
        "name": "陈小雨(童年)",
        "name_en": "Young Xiaoyu",
        "age": 10,
        "physical": "little girl with black twin pigtails tied with red ribbons, rounder more childlike face, bright innocent eyes full of energy",
        "clothing": "white short-sleeve school uniform shirt with red neckerchief, navy blue pleated skirt, white canvas shoes"
    },
    # 女儿 - 青春期 (18岁)
    "daughter_teen": {
        "name": "陈小雨(青春期)",
        "name_en": "Teenage Xiaoyu",
        "age": 18,
        "physical": "teenage girl with black high ponytail slightly messy, more defined face than childhood, rebellious defiant expression",
        "clothing": "oversized gray hoodie, dark blue jeans with rips at knees, worn white sneakers"
    },
    # 父亲 - 现在 (55岁)
    "father_present": {
        "name": "陈国强",
        "name_en": "Chen Guoqiang",
        "age": 55,
        "physical": "elderly man with salt and pepper gray mostly white short neat hair thinning on top, thin slightly frail build, weathered tan skin, angular face with prominent cheekbones, deep-set gentle dark brown warm eyes, bushy graying eyebrows, deep smile lines, weathered hands",
        "clothing_hospital": "light blue hospital gown, hospital wristband",
        "clothing_home": "faded green plaid flannel shirt, gray cotton pants, brown cloth slippers, reading glasses on cord around neck"
    },
    # 父亲 - 回忆 (40岁)
    "father_young": {
        "name": "陈国强(年轻)",
        "name_en": "Young Guoqiang",
        "age": 40,
        "physical": "middle-aged man with jet black hair with few gray strands, sturdy strong build from years of physical work, tanned skin from work, fuller healthier face, warm hardworking content expression",
        "clothing": "white sleeveless undershirt with white cotton apron slightly stained from cooking, simple dark blue work pants, black cloth shoes, white towel over shoulder"
    }
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
TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy
"""

# =============================================================================
# 15图完整脚本定义
# =============================================================================

FULL_STORY_SHOTS = [
    # Shot 01: 城市办公室 - 接到电话
    {
        "shot_id": 1,
        "scene": "城市办公室 - 接到电话",
        "text_type": "narration",
        "speaker_position": "top",
        "chinese_text": "那天接到电话，世界突然安静了",
        "image_prompt": f"""{GHIBLI_STYLE_PREFIX}
---

A young professional woman with short black bob haircut, wearing a beige trench coat, standing in a modern office space. She is holding a phone to her ear, her expression shifting from neutral to deeply concerned. Her dark brown almond eyes widen slightly, lips parted in shock. One hand grips the phone tightly while the other hangs limply at her side.

The office has large windows letting in afternoon light, modern desks and computers visible in the soft-focus background. Warm afternoon sunlight streams through the windows, creating long shadows.

EMOTIONAL ATMOSPHERE:
The scene conveys sudden shock and dawning worry.
Character shows concerned, worried expression with widened eyes, slightly trembling hand holding phone, body frozen mid-motion.

{TEXT_FREE_REQUIREMENT}

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the TOP (0-15% of image height) for narrative text overlay
- This area should have simple ceiling/window background for text readability
- Ensure character's face and worried expression remain clearly visible
- Character positioned in center-right of frame
"""
    },
    # Shot 02: 火车车窗 - 发呆
    {
        "shot_id": 2,
        "scene": "火车车窗 - 发呆",
        "text_type": "thought",
        "speaker_position": "bottom",
        "chinese_text": "三年没回去了...",
        "image_prompt": f"""{GHIBLI_STYLE_PREFIX}
---

A young woman with short black bob haircut sitting by a train window, her reflection faintly visible in the glass. She wears a beige trench coat, her posture slightly slumped. Her face shows distant, melancholic expression as she gazes out at the passing countryside - green rice fields and distant mountains blurred by the train's motion.

Late afternoon golden light streams through the window, casting warm shadows across her face. The train interior has worn but clean seats in muted green fabric. Other passengers are barely visible in soft blur.

EMOTIONAL ATMOSPHERE:
The scene conveys quiet anxiety and guilt, lost in worried thoughts.
Character shows pensive, distant expression with unfocused gaze, slight furrow between brows, hands clasped tightly in lap.

{TEXT_FREE_REQUIREMENT}

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the BOTTOM (82-100% height) for thought text overlay
- This area should show simple train floor or seat edge for text readability
- Ensure character's profile and the window scenery remain the visual focus
- Character positioned in left side of frame, window taking right portion
"""
    },
    # Shot 03: 乡村街道 - 冷清的面馆
    {
        "shot_id": 3,
        "scene": "乡村街道 - 冷清的面馆",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "记忆中总是热气腾腾的地方，如今门可罗雀",
        "image_prompt": f"""{GHIBLI_STYLE_PREFIX}
---

A quiet small-town street in rural China. In the center stands a modest noodle shop with a faded wooden sign (no text visible, weathered blank sign board). The shop entrance has traditional sliding doors, now closed. Dust motes float in the late afternoon light.

A young woman with short black bob haircut in beige trench coat stands before the closed shop, viewed from behind at a distance. Her small figure emphasizes the emptiness of the once-busy establishment. Wilted plants in pots flank the entrance. A few fallen leaves scattered on the ground.

The surrounding buildings are old but charming - whitewashed walls with dark wooden beams, traditional tile roofs. The street is nearly empty, creating a melancholic atmosphere.

NARRATIVE MOMENT:
This scene establishes the contrast between memory and present - the once-vibrant shop now quiet.
Visual focus on the closed shop and the daughter's small figure facing it.

{TEXT_FREE_REQUIREMENT}

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the BOTTOM (82-100% height) for narrative text overlay
- This area should show simple ground/street surface for text readability
- The shop facade and daughter's figure should be in upper-center of frame
- Background buildings provide context without cluttering
"""
    },
    # Shot 04: 医院病房 - 见到父亲
    {
        "shot_id": 4,
        "scene": "医院病房 - 见到父亲",
        "text_type": "dialogue",
        "speaker_position": "left,right",
        "chinese_text": ["爸...", "回来啦，别担心，小毛病"],
        "image_prompt": f"""{GHIBLI_STYLE_PREFIX}
---

A hospital room scene. An elderly man with salt-and-pepper gray hair sits propped up in a hospital bed, wearing a light blue hospital gown. He has a thin, weathered face with deep smile lines, but his dark brown eyes are warm and gentle as he looks at his daughter. Despite being ill, he manages a reassuring smile.

A young woman with short black bob haircut in beige trench coat stands at the bedside, her expression showing shock at seeing her father so thin, mixed with guilt and relief. Her hands grip the bed railing, eyes glistening with unshed tears.

Soft afternoon light filters through white hospital curtains. Medical equipment visible but not prominent. A simple vase with wildflowers on the bedside table adds a touch of warmth.

CHARACTER EXPRESSION FOCUS:
Father: gentle, reassuring smile despite fatigue, warm eyes showing happiness at seeing his daughter.
Daughter: emotional turmoil - relief, guilt, sadness - eyes slightly red, lips pressed together to hold back tears.

{TEXT_FREE_REQUIREMENT}

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space in upper left corner for daughter's dialogue bubble
- Leave clean space in upper right corner for father's dialogue bubble
- Both characters' faces should be clearly visible
- Hospital room background should be simple enough for text contrast
"""
    },
    # Shot 05: 医院走廊 - 和医生交谈
    {
        "shot_id": 5,
        "scene": "医院走廊 - 和医生交谈",
        "text_type": "narration",
        "speaker_position": "top",
        "chinese_text": "医生说要注意休息，我却不知道他一个人撑了多久",
        "image_prompt": f"""{GHIBLI_STYLE_PREFIX}
---

A hospital corridor with soft fluorescent lighting. A young woman with short black bob haircut in beige trench coat listens intently to a doctor in white coat. Her body language shows concern - arms crossed protectively, shoulders slightly hunched, brow furrowed.

The doctor, a middle-aged woman with glasses and hair in a neat bun, holds a clipboard and speaks with professional but compassionate expression. They stand near a window where afternoon light creates a warm contrast to the clinical surroundings.

The corridor stretches behind them with soft-focus hospital elements - a nurse walking past, a wheelchair against the wall. The atmosphere conveys the weight of medical conversations.

EMOTIONAL ATMOSPHERE:
The scene conveys anxious concern and the heaviness of receiving difficult news.
Character shows worried expression with tight jaw, hands clasped nervously, leaning in to catch every word.

{TEXT_FREE_REQUIREMENT}

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the TOP (0-15% of image height) for narrative text overlay
- Ceiling area should be simple for text readability
- Both figures should be visible in mid-frame
- Window light provides visual interest without cluttering text area
"""
    },
    # Shot 06: 老屋客厅 - 看到全家福
    {
        "shot_id": 6,
        "scene": "老屋客厅 - 看到全家福",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "照片里的我们，笑得多开心",
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

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the BOTTOM (82-100% height) for narrative text overlay
- Floor area should be simple for text readability
- The photo frame should be clearly visible in upper portion of frame
- Daughter positioned to show her emotional reaction to the photo
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

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space in upper right corner for child's dialogue bubble
- Leave clean space in upper left area for father's reply bubble
- Little girl should be prominent in foreground
- Father visible in background for context
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

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the BOTTOM (82-100% height) for narrative text overlay
- Floor/table area should be simple for text readability
- Father and the bowl of noodles should dominate the upper-center frame
- Steam and light effects add emotional warmth
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

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the CENTER (40-60% height) for emphasized dialogue
- This area will have RED HIGHLIGHT text showing the daughter's hurtful words
- Both figures should be visible, daughter more prominent
- Background simple enough for text contrast
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

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the BOTTOM (82-100% height) for narrative text overlay
- Platform ground area should be simple for text readability
- Both figures walking, father slightly behind, emphasizes the emotional distance
- Train in background provides context
"""
    },
    # Shot 11: 现实 - 厨房发现笔记本
    {
        "shot_id": 11,
        "scene": "现实 - 厨房发现笔记本",
        "text_type": "narration",
        "speaker_position": "top",
        "chinese_text": "在厨房角落，我看到一本旧笔记本",
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

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the TOP (0-15% of image height) for narrative text overlay
- Ceiling/upper cabinet area should be simple for text readability
- Character kneeling with notebook should be in center-lower frame
- The notebook is the key visual element - should be clearly visible
"""
    },
    # Shot 12: 特写 - 笔记本内容
    {
        "shot_id": 12,
        "scene": "特写 - 笔记本内容",
        "text_type": "narration",
        "speaker_position": "top",
        "chinese_text": '"女儿喜欢的口味"——不爱香菜、多放葱花、汤要清淡...',
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

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the TOP (0-18% height) for narrative text overlay
- This area should show blurred background for text readability
- The notebook pages should fill most of the frame
- Hands visible at edges to show human connection to the object
"""
    },
    # Shot 13: 现实 - 泪流满面
    {
        "shot_id": 13,
        "scene": "现实 - 泪流满面",
        "text_type": "thought",
        "speaker_position": "bottom",
        "chinese_text": '原来每一碗面，都是他在说"我爱你"',
        "image_prompt": f"""{GHIBLI_STYLE_PREFIX}
---

An emotionally powerful scene. The daughter (28, short black bob) sits on the kitchen floor, back against the cabinets, knees drawn up. The notebook rests in her lap. Tears stream down her face freely, her expression showing deep emotional release - not dramatic sobbing, but quiet, profound tears of realization and regret.

Her eyes are red-rimmed, looking down at the notebook but seeing something beyond it - understanding finally what her father's love looked like. One hand covers her mouth, the other clutches the notebook.

Evening light creates a warm glow, but shadows fill the corners of the kitchen. The atmosphere is intimate, private - a moment of transformation.

EMOTIONAL ATMOSPHERE:
The scene conveys catharsis, revelation, and the bittersweet pain of understanding too late.
Character shows deep emotion - tears, slightly shaking shoulders, the weight of years of distance suddenly clear.

{TEXT_FREE_REQUIREMENT}

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the BOTTOM (82-100% height) for thought text overlay
- Floor area should provide contrast for text
- Character fills most of the frame, emphasizing emotional intensity
- The notebook visible in her lap connects to previous shot
"""
    },
    # Shot 14: 医院病房 - 端面给父亲
    {
        "shot_id": 14,
        "scene": "医院病房 - 端面给父亲",
        "text_type": "dialogue",
        "speaker_position": "left,right",
        "chinese_text": ["爸，我煮的，你尝尝", "...还是那个味道"],
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

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space in upper left corner for daughter's dialogue bubble
- Leave clean space in upper right area for father's response bubble
- Both faces should be clearly visible with their emotional expressions
- The bowl of noodles between them serves as visual bridge
"""
    },
    # Shot 15: 面馆门口 - 新店招亮起
    {
        "shot_id": 15,
        "scene": "面馆门口 - 新店招亮起",
        "text_type": "narration",
        "speaker_position": "bottom",
        "chinese_text": "有些爱从不说出口，却记在心里一辈子",
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

COMPOSITION GUIDANCE FOR TEXT OVERLAY:
- Leave clean space at the BOTTOM (82-100% height) for narrative text overlay (the key quote)
- Ground/street area should be simple for the important closing text
- The shop facade and daughter in doorway should fill upper portion
- Warm light and atmosphere emphasize hopeful resolution
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

async def generate_image(prompt: str, shot_id: int, output_dir: Path) -> dict:
    """生成无文字图像"""
    try:
        image_gen = get_image_generator()
        result = await image_gen.generate_image(
            prompt=prompt,
            aspect_ratio="9:16",
            use_pro_model=USE_PRO_MODEL,
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
                    "shot_id": shot_id
                }
            return {"success": False, "error": "No PIL image"}
        else:
            return {"success": False, "error": result.get("error", "Unknown error")}

    except Exception as e:
        return {"success": False, "error": str(e)}

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

async def run_full_story_test():
    """运行完整故事测试"""

    print("=" * 70)
    print("条漫完整故事测试 - 《最后一碗面》")
    print("15张图完整故事，Ghibli-inspired风格")
    print("=" * 70)

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    NO_TEXT_DIR.mkdir(parents=True, exist_ok=True)
    WITH_TEXT_DIR.mkdir(parents=True, exist_ok=True)
    COMPARISON_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n输出目录: {OUTPUT_DIR}")

    # 初始化服务
    try:
        text_service = TextOverlayService()
        print(f"字体: {text_service.font_path}")
    except RuntimeError as e:
        print(f"❌ 初始化失败: {e}")
        return

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

        print(f"\n[Shot {shot_id:02d}] {scene}")
        if is_memory:
            print(f"  📷 回忆场景（柔光处理）")
        if emphasis:
            print(f"  🔴 情感强调: {emphasis}")

        # 保存prompt日志
        prompts_log.append({
            "shot_id": shot_id,
            "scene": scene,
            "text_type": shot["text_type"],
            "speaker_position": shot["speaker_position"],
            "chinese_text": shot["chinese_text"],
            "is_memory": is_memory,
            "emphasis": emphasis,
            "prompt": shot["image_prompt"]
        })

        # 生成无文字图像
        result = await generate_image(shot["image_prompt"], shot_id, NO_TEXT_DIR)

        if result["success"]:
            print(f"  ✅ 图像生成成功")

            # 叠加文字
            original_image = result["pil_image"]
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
                "emphasis": emphasis
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

    # 统计
    success_count = sum(1 for r in results if r.get("success"))
    memory_count = sum(1 for r in results if r.get("is_memory") and r.get("success"))
    emphasis_count = sum(1 for r in results if r.get("emphasis") and r.get("success"))

    print("\n" + "=" * 70)
    print("测试完成!")
    print("=" * 70)
    print(f"成功: {success_count}/{len(FULL_STORY_SHOTS)}")
    print(f"回忆场景: {memory_count}/4")
    print(f"情感强调: {emphasis_count}/1")

    print(f"\n输出目录:")
    print(f"  无文字图片: {NO_TEXT_DIR}")
    print(f"  叠加文字后: {WITH_TEXT_DIR}")
    print(f"  对比图: {COMPARISON_DIR}")

    print("\n验收要点:")
    print("  1. 角色一致性：女儿和父亲在所有图中可识别")
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

    asyncio.run(run_full_story_test())
