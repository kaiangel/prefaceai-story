"""
条漫MVP故事测试脚本 - 无文字版本
生成不含任何文字的图片，用于后续TextOverlayService叠加中文

参考模板: docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md
原测试脚本: tests/test_comic_mvp_story.py

作者: @Backend
日期: 2026-01-22
任务: HANDOFF-2026-01-22-008 / TASK-003
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
USE_PRO_MODEL = False  # 条漫MVP测试先用Flash
OUTPUT_DIR = Path(__file__).parent.parent / "test_output" / "comic_mvp_test" / "no_text_images"

# =============================================================================
# 角色定义 (与原脚本相同)
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
# 风格前缀 (与原脚本相同)
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
# TEXT-FREE 核心指令块 (来自 COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md)
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
# 表情词库 (与原脚本相同)
# =============================================================================

def get_emotion_desc(emotion_key: str) -> str:
    """获取表情描述"""
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


def get_character_desc(char_id: str) -> str:
    """获取角色完整描述"""
    char = CHARACTERS.get(char_id)
    if not char:
        return ""
    return f"{char['physical']}, {char['clothing']}"

# =============================================================================
# 5张测试用例定义 (shot_01, 06, 08, 12, 14)
# 覆盖所有文字类型：对话气泡、黑底旁白(顶/底/中)、白底旁白、画中画
# =============================================================================

TEST_SHOTS = [
    # Shot 1 - 对话气泡 + 顶部黑底旁白
    {
        "shot_id": 1,
        "ref_image": "IMG_0804",
        "description": "对话场景 + 顶部旁白预留",
        "scene": "urban street at dusk, city buildings in background, warm evening light",
        "characters": ["female_lead", "male_lead"],
        "female_emotion": "displeased",
        "male_emotion": "confused",
        "speaking_character": "male_lead",
        "reserve_areas": ["top", "bubble_right"],
        "overlay_config": {
            "top_monologue": "那天和男朋友逛街，让他帮我拍照，拍了好多张没一张能看的！！！",
            "speech_bubble": {"text": "你说句话呀宝宝…", "speaker": "right"}
        }
    },
    # Shot 6 - 回忆碎片效果 + 底部旁白
    {
        "shot_id": 6,
        "ref_image": "IMG_0809",
        "description": "回忆碎片效果 + 底部旁白预留",
        "scene": "female lead standing alone, dark atmospheric background with soft lights",
        "characters": ["female_lead"],
        "female_emotion": "shocked",
        "fragments": [
            "A couple arguing, the man looking away coldly",
            "A woman sitting alone crying at night",
            "Two people walking separately on a street",
            "A man's cold indifferent face in shadow"
        ],
        "emotional_tone": "déjà vu, haunting realization, painful memories surfacing",
        "reserve_areas": ["bottom"],
        "overlay_config": {
            "bottom_monologue": "这一幕我突然觉得似曾相识。"
        }
    },
    # Shot 8 - 分屏效果 + 中央旁白
    {
        "shot_id": 8,
        "ref_image": "IMG_0811",
        "description": "分屏效果 + 中央旁白预留",
        "left_scene": "Female lead with cold distant expression, gray-blue color tone, sitting alone",
        "left_emotion": "indifferent, aloof, emotionally closed off",
        "right_scene": "Ex-boyfriend with cold intimidating gaze, dark red moody lighting",
        "right_emotion": "cold, dismissive, emotionally unavailable",
        "reserve_areas": ["center"],
        "overlay_config": {
            "center_monologue": "可是现在，我发现我越来越像他了。我仗着对方的紧张和在意，堂而皇之的关闭了自己的沟通渠道。"
        }
    },
    # Shot 12 - 画中画 + 对话气泡
    {
        "shot_id": 12,
        "ref_image": "IMG_0815",
        "description": "画中画(手机) + 对话气泡预留",
        "scene": "male lead holding phone, taking photo of female lead who is smiling happily",
        "characters": ["female_lead", "male_lead"],
        "female_emotion": "happy",
        "male_emotion": "happy",
        "pip_content": "the phone screen showing female lead's smiling face being photographed, beautiful composition",
        "device_type": "smartphone held by male lead",
        "reserve_areas": ["bubble_left"],
        "overlay_config": {
            "speech_bubble": {"text": "好。", "speaker": "left"}
        }
    },
    # Shot 14 - 顶部白底旁白
    {
        "shot_id": 14,
        "ref_image": "IMG_0817",
        "description": "叙事场景 + 顶部白底旁白预留",
        "scene": "couple walking away together hand in hand on a lamplit street at evening, seen from behind, romantic atmosphere",
        "characters": ["female_lead", "male_lead"],
        "reserve_areas": ["top"],
        "overlay_config": {
            "top_narrative": "如果我爱你，就一定会尽可能告诉你，我为什么生气，要学会大大方方的表达爱意。"
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

    # Shot 1: 对话场景（无气泡）
    if shot_id == 1:
        char_descs = []
        for char_id in shot.get("characters", []):
            char = CHARACTERS.get(char_id)
            emotion_key = shot.get(f"{char_id.split('_')[0]}_emotion", "")
            emotion_desc = get_emotion_desc(emotion_key) if emotion_key else ""
            char_desc = f"{char['name_en']} ({char['physical']}, {char['clothing']})"
            if emotion_desc:
                char_desc += f", showing {emotion_desc}"
            char_descs.append(char_desc)

        scene_desc = f"{shot['scene']}. Characters: {'; '.join(char_descs)}."

        speaking_char = CHARACTERS[shot["speaking_character"]]

        parts.append(f"""{scene_desc}

CHARACTER EXPRESSION FOCUS:
The character {speaking_char['name_en']} is speaking with {get_emotion_desc(shot['male_emotion'])} expression.
Focus on capturing the emotional nuance in their face and body language.
The other character shows {get_emotion_desc(shot['female_emotion'])} expression in response.
""")

    # Shot 6: 回忆碎片效果（无旁白）
    elif shot_id == 6:
        char = CHARACTERS["female_lead"]
        main_desc = f"{char['name_en']} ({char['physical']}, {char['clothing']}), standing with {get_emotion_desc(shot['female_emotion'])} expression, {shot['scene']}"

        fragment_lines = "\n".join([f"Fragment {i+1}: {f}" for i, f in enumerate(shot["fragments"])])

        parts.append(f"""{main_desc}

MEMORY FRAGMENT EFFECT - NO TEXT:
Surrounding the main character, floating memory fragments showing glimpses of the past.
Fragment shapes: jagged glass shards with glowing golden edges
Number of visible fragments: {len(shot['fragments'])}

Fragment contents:
{fragment_lines}

Fragment visual treatment: slightly desaturated colors with warm golden glow at edges, ethereal and dreamlike quality
The fragments should appear to float in space around the character, creating a dreamlike, nostalgic atmosphere.
Main character remains in sharp focus while fragments have soft blur and slight transparency.

Emotional tone: {shot['emotional_tone']}
""")

    # Shot 8: 分屏效果（无中央文字）
    elif shot_id == 8:
        female_char = CHARACTERS["female_lead"]
        ex_char = CHARACTERS["ex_boyfriend"]

        parts.append(f"""SPLIT SCREEN COMPOSITION - NO TEXT:

LEFT HALF: {female_char['name_en']} ({female_char['physical']}, {female_char['clothing']}), {shot['left_scene']}
The left character shows {shot['left_emotion']} expression.

RIGHT HALF: {ex_char['name_en']} ({ex_char['physical']}, {ex_char['clothing']}), {shot['right_scene']}
The right character shows {shot['right_emotion']} expression.

VISUAL STYLE:
- Clear vertical division down the center of the image
- Sharp clean line separating the two scenes, slight color temperature difference (cool left, warm right)
- Both halves should have similar lighting style for visual coherence
- Contrast in content/emotion between two sides showing their separated emotional states
- NO text on or near the center dividing line
""")

    # Shot 12: 画中画效果（无气泡/旁白）
    elif shot_id == 12:
        char_descs = []
        for char_id in shot.get("characters", []):
            char = CHARACTERS.get(char_id)
            emotion_key = shot.get(f"{char_id.split('_')[0]}_emotion", "")
            emotion_desc = get_emotion_desc(emotion_key) if emotion_key else ""
            char_desc = f"{char['name_en']} ({char['physical']}, {char['clothing']})"
            if emotion_desc:
                char_desc += f", showing {emotion_desc}"
            char_descs.append(char_desc)

        scene_desc = f"{shot['scene']}. Characters: {'; '.join(char_descs)}."

        parts.append(f"""{scene_desc}

PICTURE-IN-PICTURE ELEMENT - NO TEXT:
{shot['device_type']} showing: {shot['pip_content']}

Device details:
- Position: center of frame, taking up significant visual space
- Size: approximately 40% of frame
- Screen content clearly visible and in focus
- Modern smartphone with thin black bezels, slight screen glow

The embedded screen should show {shot['pip_content']} with realistic device frame.
Do NOT include any text, labels, or UI elements on the device screen.

Visual relationship: viewer sees the photo on screen and the character's joyful reaction
""")

    # Shot 14: 叙事场景（无白底旁白）
    elif shot_id == 14:
        char_descs = []
        for char_id in shot.get("characters", []):
            char = CHARACTERS.get(char_id)
            char_desc = f"{char['name_en']} ({char['physical']}, {char['clothing']})"
            char_descs.append(char_desc)

        parts.append(f"""{shot['scene']}
Characters seen from behind: {'; '.join(char_descs)}

NARRATIVE MOMENT:
This scene establishes a hopeful new beginning after reconciliation.
Visual focus on the couple's peaceful body language and the romantic evening atmosphere.
The scene should feel warm, hopeful, and emotionally resolved.
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
    print("条漫MVP - 无文字图像生成")
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
        ref_image = shot["ref_image"]
        desc = shot["description"]

        print(f"\n[Shot {shot_id:02d}] 生成 {ref_image}...")
        print(f"  描述: {desc}")

        # 构建prompt
        prompt = build_no_text_prompt(shot)

        # 保存prompt
        prompts_log.append({
            "shot_id": shot_id,
            "ref_image": ref_image,
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
            "ref_image": ref_image,
            "description": desc,
            **result
        })

        # 避免API限流
        await asyncio.sleep(2)

    # 保存prompts日志（包含overlay配置，用于后续TextOverlay测试）
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

    print("\n下一步：")
    print("1. 使用 TextOverlayService V2 在这些图片上叠加文字")
    print("2. 运行 tests/test_text_overlay_v2.py 进行验收")

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
