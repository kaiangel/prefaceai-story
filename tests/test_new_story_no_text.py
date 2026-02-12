"""
新故事完整测试 - 古风武侠 + 中国水墨风格
用于验证 TextOverlay V2 在不同内容和风格下的效果

作者: @Tester
日期: 2026-01-22
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

# =============================================================================
# 配置
# =============================================================================

GEMINI_MODEL = "gemini-2.5-flash-image"
USE_PRO_MODEL = False
OUTPUT_DIR = Path(__file__).parent.parent / "test_output" / "comic_mvp_test" / "new_story_test"

# =============================================================================
# 新故事：古风武侠 - 《剑心》
# =============================================================================

CHARACTERS = {
    "female_warrior": {
        "name": "剑心",
        "name_en": "Jian Xin (Sword Heart)",
        "physical": "young woman in early twenties with long flowing black hair tied with a red ribbon, delicate phoenix eyes with sharp determined gaze, fair porcelain skin, graceful oval face with beauty mark under left eye, athletic elegant build",
        "clothing": "flowing white hanfu robe with dark blue trim, silver embroidered crane patterns, martial arts belt around waist, ancient Chinese sword at her side"
    },
    "master": {
        "name": "云老",
        "name_en": "Master Yun",
        "physical": "elderly man in his seventies with long white hair and beard flowing in wind, wise deep-set eyes with kind wrinkles, weathered but kind face, tall dignified bearing",
        "clothing": "traditional gray daoist robe with cloud patterns, wooden prayer beads around neck, bamboo walking staff"
    },
    "enemy": {
        "name": "魔尊",
        "name_en": "Demon Lord",
        "physical": "imposing man with long wild black hair streaked with white, fierce crimson eyes with vertical pupils, sharp angular face with scar across left cheek, powerful muscular build",
        "clothing": "flowing black robe with red flame embroidery, dark metal armor plates on shoulders, blood-red cape billowing"
    }
}

# =============================================================================
# 风格前缀 - 中国水墨风格
# =============================================================================

STYLE_PREFIX = """
═══════════════════════════════════════════════════════════
MANDATORY STYLE REQUIREMENT - DO NOT IGNORE THIS SECTION
═══════════════════════════════════════════════════════════
STYLE: Chinese Ink Wash Painting / Sumi-e Art Style

MUST INCLUDE: traditional Chinese ink wash, brush strokes visible, misty atmospheric perspective,
monochromatic with subtle color accents, rice paper texture, flowing graceful lines,
martial arts wuxia aesthetic, poetic mood, negative space emphasis

DO NOT USE: photorealistic, photograph, 3D render, anime style, pixel art,
Western oil painting, watercolor, modern digital art, cartoon

This is a wuxia martial arts story with traditional Chinese ink painting aesthetics.
Characters should have graceful flowing robes and elegant poses.
Backgrounds should feature misty mountains, bamboo forests, ancient temples.
═══════════════════════════════════════════════════════════

"""

# =============================================================================
# TEXT-FREE 核心指令块
# =============================================================================

TEXT_FREE_REQUIREMENT = """
TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy
"""

def get_composition_guidance(reserve_areas: list) -> str:
    """获取文字区域预留指令"""
    guidance = "\nCOMPOSITION GUIDANCE FOR TEXT OVERLAY:\n"

    if "top" in reserve_areas:
        guidance += "- Leave clean space at the TOP (0-15% of image height) for top text overlay\n"
    if "bottom" in reserve_areas:
        guidance += "- Leave clean space at the BOTTOM (80-100% of image height) for bottom text overlay\n"
    if "center" in reserve_areas:
        guidance += "- Leave clean space at the CENTER (40-60% of image height) for center text overlay\n"
    if "bubble_right" in reserve_areas:
        guidance += "- Leave clean space in upper right corner for speech bubble overlay\n"
    if "bubble_left" in reserve_areas:
        guidance += "- Leave clean space in upper left corner for speech bubble overlay\n"

    guidance += "- Ensure character faces and key expressions are NOT obstructed by reserved areas\n"
    guidance += "- Background in reserved areas should be relatively simple for text readability\n"

    return guidance

# =============================================================================
# 表情词库 - 武侠风格
# =============================================================================

def get_emotion_desc(emotion_key: str) -> str:
    """获取表情描述"""
    emotions = {
        "determined": "resolute unwavering gaze, firmly set jaw, focused intense eyes, warrior's composure",
        "sorrowful": "eyes glistening with unshed tears, brows drawn together, downcast gaze, profound grief",
        "fierce": "blazing intense eyes, gritted teeth, fierce scowl, battle-ready tension",
        "peaceful": "serene gentle smile, half-closed meditative eyes, relaxed features, inner harmony",
        "shocked": "wide startled eyes, raised eyebrows, slightly parted lips, frozen in surprise",
        "wise": "deep knowing eyes, gentle wrinkles from smiling, patient kind expression, sage-like calm",
        "menacing": "cruel cold smile, narrowed predatory eyes, dark intimidating aura, malicious intent",
        "grateful": "warm appreciative eyes, soft genuine smile, humble bowed head, deep respect"
    }
    return emotions.get(emotion_key, emotion_key)


def get_character_desc(char_id: str) -> str:
    """获取角色完整描述"""
    char = CHARACTERS.get(char_id)
    if not char:
        return ""
    return f"{char['physical']}, {char['clothing']}"

# =============================================================================
# 5张测试用例 - 古风武侠故事
# =============================================================================

TEST_SHOTS = [
    # Shot 1 - 对话场景：师徒告别
    {
        "shot_id": 1,
        "description": "师徒告别场景 + 顶部旁白",
        "scene": "ancient mountain temple courtyard at dawn, misty bamboo forest in background, cherry blossom petals drifting in wind",
        "characters": ["female_warrior", "master"],
        "female_emotion": "sorrowful",
        "master_emotion": "wise",
        "speaking_character": "master",
        "reserve_areas": ["top", "bubble_right"],
        "overlay_config": {
            "top_monologue": "那一天，师父站在山门前，说了我此生难忘的话。",
            "speech_bubble": {"text": "剑心，记住，真正的剑道不在剑上...", "speaker": "right"}
        }
    },
    # Shot 2 - 回忆碎片：往昔修炼
    {
        "shot_id": 2,
        "description": "回忆碎片效果 + 底部旁白",
        "scene": "female warrior standing on cliff edge, wind blowing her hair and robes, overlooking vast misty mountain range",
        "characters": ["female_warrior"],
        "female_emotion": "determined",
        "fragments": [
            "A young girl practicing sword forms in moonlight",
            "Master teaching a child to hold a wooden sword",
            "Training under a waterfall in summer rain",
            "Meditating in a snowy mountain cave"
        ],
        "emotional_tone": "nostalgia, determination, the weight of years of training",
        "reserve_areas": ["bottom"],
        "overlay_config": {
            "bottom_monologue": "十年寒暑，一剑一心。"
        }
    },
    # Shot 3 - 分屏：正邪对峙
    {
        "shot_id": 3,
        "description": "分屏效果 + 中央旁白",
        "left_scene": "Female warrior in white robes standing in bright sunlight, righteous aura, mountain peaks behind",
        "left_emotion": "determined, righteous, calm before battle",
        "right_scene": "Demon Lord shrouded in dark mist, red demonic energy swirling, ruined temple behind",
        "right_emotion": "menacing, cruel, powerful dark presence",
        "reserve_areas": ["center"],
        "overlay_config": {
            "center_monologue": "光与暗，正与邪，这一战，避无可避。"
        }
    },
    # Shot 4 - 画中画：水中倒影
    {
        "shot_id": 4,
        "description": "画中画效果 + 对话气泡",
        "scene": "female warrior kneeling by ancient pond in temple garden, gazing at her reflection, lotus flowers floating on water",
        "characters": ["female_warrior"],
        "female_emotion": "peaceful",
        "pip_content": "her reflection in the pond shows a younger version of herself with innocent eyes and a bright smile",
        "device_type": "ancient bronze mirror-like pond surface",
        "reserve_areas": ["bubble_left"],
        "overlay_config": {
            "speech_bubble": {"text": "那个天真的我，早已不在了...", "speaker": "left"}
        }
    },
    # Shot 5 - 叙事场景：归来
    {
        "shot_id": 5,
        "description": "叙事场景 + 顶部白底旁白",
        "scene": "female warrior walking through village gate at sunset, villagers welcoming her with joy, warm golden light, peaceful rural Chinese village with traditional architecture",
        "characters": ["female_warrior"],
        "female_emotion": "grateful",
        "reserve_areas": ["top"],
        "overlay_config": {
            "top_narrative": "归来时，方知离去的意义。守护一方安宁，便是我的剑道。"
        }
    }
]

# =============================================================================
# Prompt构建 - 无文字版本
# =============================================================================

def build_no_text_prompt(shot: dict) -> str:
    """构建无文字版本的prompt"""

    parts = [STYLE_PREFIX]

    shot_id = shot["shot_id"]

    # Shot 1: 对话场景（师徒告别）
    if shot_id == 1:
        char_descs = []
        for char_id in shot.get("characters", []):
            char = CHARACTERS.get(char_id)
            if char_id == "female_warrior":
                emotion_key = shot.get("female_emotion", "")
            elif char_id == "master":
                emotion_key = shot.get("master_emotion", "")
            else:
                emotion_key = ""
            emotion_desc = get_emotion_desc(emotion_key) if emotion_key else ""
            char_desc = f"{char['name_en']} ({char['physical']}, {char['clothing']})"
            if emotion_desc:
                char_desc += f", showing {emotion_desc}"
            char_descs.append(char_desc)

        scene_desc = f"{shot['scene']}. Characters: {'; '.join(char_descs)}."

        speaking_char = CHARACTERS[shot["speaking_character"]]

        parts.append(f"""{scene_desc}

CHARACTER EXPRESSION FOCUS:
The character {speaking_char['name_en']} is speaking with {get_emotion_desc(shot['master_emotion'])} expression.
Focus on capturing the emotional nuance in their face and body language.
The other character shows {get_emotion_desc(shot['female_emotion'])} expression in response.

This is a solemn farewell scene between master and disciple.
The atmosphere is bittersweet with morning mist and falling petals.
""")

    # Shot 2: 回忆碎片效果
    elif shot_id == 2:
        char = CHARACTERS["female_warrior"]
        main_desc = f"{char['name_en']} ({char['physical']}, {char['clothing']}), standing with {get_emotion_desc(shot['female_emotion'])} expression, {shot['scene']}"

        fragment_lines = "\n".join([f"Fragment {i+1}: {f}" for i, f in enumerate(shot["fragments"])])

        parts.append(f"""{main_desc}

MEMORY FRAGMENT EFFECT - NO TEXT:
Surrounding the main character, floating memory fragments showing glimpses of the past.
Fragment shapes: ink-splash shapes with soft glowing edges, like water droplets in ink wash painting
Number of visible fragments: {len(shot['fragments'])}

Fragment contents:
{fragment_lines}

Fragment visual treatment: faded sepia tones with soft ink edges, ethereal and dreamlike quality
The fragments should appear to float in misty space around the character.
Main character remains in sharp focus while fragments have soft blur and slight transparency.

Emotional tone: {shot['emotional_tone']}
""")

    # Shot 3: 分屏效果（正邪对峙）
    elif shot_id == 3:
        female_char = CHARACTERS["female_warrior"]
        enemy_char = CHARACTERS["enemy"]

        parts.append(f"""SPLIT SCREEN COMPOSITION - NO TEXT:

LEFT HALF: {female_char['name_en']} ({female_char['physical']}, {female_char['clothing']}), {shot['left_scene']}
The left character shows {shot['left_emotion']} expression.
Bright ethereal lighting with white mist, representing righteousness.

RIGHT HALF: {enemy_char['name_en']} ({enemy_char['physical']}, {enemy_char['clothing']}), {shot['right_scene']}
The right character shows {shot['right_emotion']} expression.
Dark ominous atmosphere with red mist, representing evil.

VISUAL STYLE:
- Clear vertical division down the center of the image
- Sharp contrast: left side bright/white tones, right side dark/red tones
- Yin-yang visual balance representing good vs evil
- Both characters should appear equally powerful and imposing
- NO text on or near the center dividing line
""")

    # Shot 4: 画中画效果（水中倒影）
    elif shot_id == 4:
        char = CHARACTERS["female_warrior"]

        parts.append(f"""{shot['scene']}
Character: {char['name_en']} ({char['physical']}, {char['clothing']}), showing {get_emotion_desc(shot['female_emotion'])} expression

PICTURE-IN-PICTURE ELEMENT - NO TEXT:
{shot['device_type']} showing: {shot['pip_content']}

Reflection details:
- Position: lower portion of frame, in the pond water
- The reflection shows her younger self from years ago
- Water surface has subtle ripples and floating lotus petals
- Slight distortion from water movement

Visual relationship: The present warrior gazes at her innocent past self
This creates a contemplative, introspective mood.
Do NOT include any text or calligraphy in the image.
""")

    # Shot 5: 叙事场景（归来）
    elif shot_id == 5:
        char = CHARACTERS["female_warrior"]

        parts.append(f"""{shot['scene']}
Character: {char['name_en']} ({char['physical']}, {char['clothing']}), showing {get_emotion_desc(shot['female_emotion'])} expression

NARRATIVE MOMENT:
This scene establishes her triumphant return home after years of training and battle.
The villagers are joyful, children running towards her, elders bowing with respect.
Golden sunset light creates a warm, hopeful atmosphere.
Her journey is complete, finding peace and purpose.

Visual focus on the emotional reunion and the peaceful rural village setting.
Traditional Chinese architecture: curved tile roofs, wooden gates, paper lanterns.
""")

    # 添加 TEXT-FREE 和 COMPOSITION GUIDANCE
    parts.append(TEXT_FREE_REQUIREMENT)
    parts.append(get_composition_guidance(shot.get("reserve_areas", [])))

    return "\n".join(parts)


# =============================================================================
# 图像生成
# =============================================================================

_image_generator = None

def get_image_generator():
    """获取或创建ImageGenerator实例"""
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
            aspect_ratio="9:16",  # 条漫竖版
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

async def run_no_text_generation():
    """运行无文字图像生成"""

    print("=" * 60)
    print("新故事测试 - 古风武侠《剑心》+ 中国水墨风格")
    print(f"模型: {GEMINI_MODEL}")
    print(f"测试用例: {len(TEST_SHOTS)} 张图")
    print("=" * 60)

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n输出目录: {OUTPUT_DIR}")

    # 存储结果
    results = []
    prompts_log = []

    # 生成每张图
    for shot in TEST_SHOTS:
        shot_id = shot["shot_id"]
        desc = shot["description"]

        print(f"\n[Shot {shot_id:02d}] 生成中...")
        print(f"  描述: {desc}")

        # 构建prompt
        prompt = build_no_text_prompt(shot)

        # 保存prompt
        prompts_log.append({
            "shot_id": shot_id,
            "description": desc,
            "reserve_areas": shot.get("reserve_areas", []),
            "overlay_config": shot.get("overlay_config", {}),
            "prompt": prompt
        })

        # 生成图像
        result = await generate_image(prompt, shot_id, OUTPUT_DIR)

        if result["success"]:
            print(f"  ✅ 成功: {result['image_path']}")
        else:
            print(f"  ❌ 失败: {result['error']}")

        results.append({
            "shot_id": shot_id,
            "description": desc,
            **result
        })

        # 避免API限流
        await asyncio.sleep(2)

    # 保存prompts日志
    prompts_path = OUTPUT_DIR / "prompts_log.json"
    with open(prompts_path, 'w', encoding='utf-8') as f:
        json.dump(prompts_log, f, ensure_ascii=False, indent=2)
    print(f"\nPrompts保存至: {prompts_path}")

    # 保存结果
    results_path = OUTPUT_DIR / "results.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"结果保存至: {results_path}")

    # 统计
    success_count = sum(1 for r in results if r.get("success"))
    print("\n" + "=" * 60)
    print("生成完成!")
    print(f"成功: {success_count}/{len(TEST_SHOTS)}")
    print(f"失败: {len(TEST_SHOTS) - success_count}/{len(TEST_SHOTS)}")
    print("=" * 60)

    return results


# =============================================================================
# 入口
# =============================================================================

if __name__ == "__main__":
    # 检查环境变量
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

    asyncio.run(run_no_text_generation())
