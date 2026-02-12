#!/usr/bin/env python3
"""
teststory6.3.9 - 通用性测试：武侠水墨风格

验证P2.0架构能否支持不同故事类型：
- 故事类型：武侠
- 视觉风格：水墨 (chinese_ink)
- 场景：竹林、山巅
- 角色：剑客、师父

输出目录: test_output/manualtest/teststory6.3.9_wuxia/
"""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.shot_prompt_generator import ShotPromptGenerator


# 输出目录
OUTPUT_DIR = Path("test_output/manualtest/teststory6.3.9_wuxia")

# 武侠水墨风格测试数据
WUXIA_STORY = {
    "title": "竹林决",
    "genre": "武侠",
    "overall_mood": "苍茫、悲壮、师徒情深",
    "style_preset": "ink",
    "characters": [
        {
            "id": "char_001",
            "name": "李青云",
            "name_en": "Li Qingyun",
            "type": "human",
            "gender": "male",
            "age_appearance": "young_adult",
            "role": "protagonist",
            "physical": {
                "height": "tall",
                "build": "lean and agile",
                "skin_tone": "fair",
                "face_shape": "angular",
                "hair_color": "jet black",
                "hair_style": "long, tied in a high ponytail with a simple ribbon",
                "eye_color": "dark brown",
                "eye_shape": "sharp and determined",
                "distinctive_marks": ["a small scar on left eyebrow"]
            },
            "clothing": {
                "top": "white flowing hanfu with wide sleeves",
                "bottom": "white loose trousers",
                "footwear": "black cloth boots",
                "accessories": ["a jade pendant on waist", "sword sheath on back"],
                "style": "traditional Chinese swordsman"
            }
        },
        {
            "id": "char_002",
            "name": "玄清道人",
            "name_en": "Master Xuanqing",
            "type": "human",
            "gender": "male",
            "age_appearance": "elderly",
            "role": "mentor",
            "physical": {
                "height": "medium",
                "build": "thin but sturdy",
                "skin_tone": "weathered tan",
                "face_shape": "long",
                "hair_color": "white",
                "hair_style": "long white hair and beard, partially tied up",
                "eye_color": "gray",
                "eye_shape": "wise and calm",
                "distinctive_marks": ["deep wrinkles around eyes"]
            },
            "clothing": {
                "top": "dark gray Daoist robe with cloud patterns",
                "bottom": "dark gray loose pants",
                "footwear": "straw sandals",
                "accessories": ["wooden prayer beads", "ancient sword at waist"],
                "style": "Daoist master"
            }
        }
    ],
    "scenes": [
        {
            "scene_id": 1,
            "location": "翠竹林深处，晨雾缭绕",
            "time": "清晨",
            "mood": "宁静、紧张",
            "narration": "晨雾如纱，竹影婆娑。李青云独立林间，手握长剑，静待师父的到来。",
            "visual_description": "Young swordsman standing alone in misty bamboo forest at dawn",
            "characters_in_scene": ["char_001"],
            "scene_style": {
                "time_of_day": "dawn",
                "lighting": "soft diffused morning light through mist",
                "weather": "misty"
            }
        },
        {
            "scene_id": 2,
            "location": "翠竹林深处",
            "time": "清晨",
            "mood": "庄严、决绝",
            "narration": "玄清道人踏雾而来，白发飘动。师徒二人对视，无需多言。",
            "visual_description": "Master walking through mist toward disciple, both facing each other",
            "characters_in_scene": ["char_001", "char_002"],
            "scene_style": {
                "time_of_day": "dawn",
                "lighting": "backlit silhouette effect",
                "weather": "misty"
            }
        },
        {
            "scene_id": 3,
            "location": "翠竹林深处，剑气纵横",
            "time": "清晨",
            "mood": "激烈、悲壮",
            "narration": "剑光如虹，竹叶纷飞。师徒二人身影交错，每一招都是多年的传承与诀别。",
            "visual_description": "Intense sword fight between master and disciple, bamboo leaves flying",
            "characters_in_scene": ["char_001", "char_002"],
            "scene_style": {
                "time_of_day": "dawn",
                "lighting": "dramatic light beams through bamboo",
                "weather": "clear"
            }
        },
        {
            "scene_id": 4,
            "location": "翠竹林边缘，山巅可见",
            "time": "日出",
            "mood": "释然、传承",
            "narration": "剑落，师父含笑倒下。远处山巅，朝阳初升，映红了李青云的泪眼。",
            "visual_description": "Master falling with peaceful smile, disciple catching him, sunrise on mountain peak",
            "characters_in_scene": ["char_001", "char_002"],
            "scene_style": {
                "time_of_day": "sunrise",
                "lighting": "golden sunrise light",
                "weather": "clear"
            }
        }
    ]
}

# 模拟的锚点图描述（水墨风格）
ANCHOR_DESCRIPTIONS = {
    "exterior_anchor": """
Chinese ink wash painting style bamboo forest scene.
Tall bamboo stalks with delicate leaves, rendered in varying shades of black ink.
Misty atmosphere with white negative space creating depth.
Traditional sumi-e brush strokes, minimalist composition.
Mountains visible in far background through the mist.
""",
    "exterior_anchor_dawn": """
Chinese ink wash painting of bamboo forest at dawn.
Soft gradients suggesting morning light filtering through mist.
Silhouettes of bamboo against lighter background.
Traditional East Asian artistic style with careful use of empty space.
Ethereal and contemplative atmosphere.
"""
}


async def run_wuxia_generality_test():
    """运行武侠水墨风格通用性测试"""

    print("=" * 80)
    print("teststory6.3.9 - 通用性测试：武侠水墨风格")
    print("=" * 80)
    print("\n测试目标：验证P2.0 ShotPromptGenerator能否适应不同故事类型")
    print("  - 故事类型：武侠")
    print("  - 视觉风格：水墨 (ink)")
    print("  - 场景：竹林、山巅")
    print("  - 角色：年轻剑客、道家师父")
    print("=" * 80)

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "shot_prompts").mkdir(exist_ok=True)

    # 初始化ShotPromptGenerator
    shot_prompt_gen = ShotPromptGenerator()

    # 构建story context
    story_context = {
        "genre": WUXIA_STORY["genre"],
        "overall_mood": WUXIA_STORY["overall_mood"],
        "title": WUXIA_STORY["title"]
    }

    style_config = {
        "style_preset": "ink"  # 水墨风格
    }

    characters = WUXIA_STORY["characters"]
    scenes = WUXIA_STORY["scenes"]

    # 构建测试shots
    test_shots = []
    shot_configs = [
        {"shot_type": "extreme wide shot", "camera_angle": "high angle"},  # 建立镜头
        {"shot_type": "medium shot", "camera_angle": "eye level"},          # 对峙
        {"shot_type": "wide shot", "camera_angle": "low angle"},            # 打斗
        {"shot_type": "close-up", "camera_angle": "eye level"},             # 情感特写
    ]

    for i, scene in enumerate(scenes):
        shot = {
            **scene,
            "shot_id": scene["scene_id"],
            "shot_type": shot_configs[i]["shot_type"],
            "camera_angle": shot_configs[i]["camera_angle"],
            "characters_in_shot": scene.get("characters_in_scene", [])
        }
        test_shots.append(shot)

    # 生成prompts
    print("\n" + "=" * 60)
    print("生成武侠水墨风格Shot Prompts")
    print("=" * 60)

    generated_prompts = []
    for shot in test_shots:
        print(f"\n  生成Shot {shot['shot_id']} prompt...")
        print(f"    场景: {shot['location'][:30]}...")
        print(f"    景别: {shot['shot_type']}, 角度: {shot['camera_angle']}")

        # 选择锚点描述
        anchor_desc = ANCHOR_DESCRIPTIONS.get("exterior_anchor_dawn", "")

        prompt = await shot_prompt_gen.generate_single_shot_prompt_for_test(
            shot_info=shot,
            scene_ref_description=anchor_desc,
            characters=characters,
            style_preset="ink"  # 水墨风格
        )

        generated_prompts.append({
            "shot_id": shot["shot_id"],
            "shot_type": shot["shot_type"],
            "camera_angle": shot["camera_angle"],
            "location": shot["location"],
            "mood": shot["mood"],
            "prompt": prompt,
            "prompt_length": len(prompt)
        })

        # 保存prompt到文件
        prompt_file = OUTPUT_DIR / "shot_prompts" / f"shot_{shot['shot_id']:02d}_prompt.txt"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(f"=== Shot {shot['shot_id']} ===\n")
            f.write(f"Location: {shot['location']}\n")
            f.write(f"Time: {shot.get('time', '')}\n")
            f.write(f"Mood: {shot['mood']}\n")
            f.write(f"Shot Type: {shot['shot_type']}\n")
            f.write(f"Camera Angle: {shot['camera_angle']}\n")
            f.write(f"Characters: {shot.get('characters_in_shot', [])}\n")
            f.write(f"\n{'=' * 60}\n")
            f.write(f"GENERATED PROMPT:\n{'=' * 60}\n\n")
            f.write(prompt)

        print(f"    ✅ prompt生成完成 ({len(prompt)} 字符)")

        await asyncio.sleep(1.0)

    # 质量验证
    print("\n" + "=" * 60)
    print("Prompt质量验证（武侠水墨风格特征检查）")
    print("=" * 60)

    for p in generated_prompts:
        prompt_lower = p["prompt"].lower()

        # 检查水墨风格关键词
        ink_keywords = ["ink", "brush", "sumi", "chinese", "traditional", "minimalist"]
        wuxia_keywords = ["sword", "bamboo", "hanfu", "master", "disciple", "martial"]

        ink_found = sum(1 for k in ink_keywords if k in prompt_lower)
        wuxia_found = sum(1 for k in wuxia_keywords if k in prompt_lower)

        print(f"\n  Shot {p['shot_id']}:")
        print(f"    水墨风格词: {ink_found}/{len(ink_keywords)}")
        print(f"    武侠元素词: {wuxia_found}/{len(wuxia_keywords)}")
        print(f"    Prompt长度: {p['prompt_length']} 字符")

    # 保存story数据
    with open(OUTPUT_DIR / "story.json", 'w', encoding='utf-8') as f:
        json.dump(WUXIA_STORY, f, ensure_ascii=False, indent=2)

    # 保存结果
    results = {
        "test_name": "teststory6.3.9_wuxia",
        "description": "通用性测试：武侠水墨风格",
        "story_type": "武侠",
        "style_preset": "ink",
        "shot_count": len(generated_prompts),
        "prompts": generated_prompts
    }

    with open(OUTPUT_DIR / "test_results.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
    print(f"\n📁 输出目录: {OUTPUT_DIR}")
    print(f"📊 生成了 {len(generated_prompts)} 个shot prompts")
    print("\n🔍 验证要点:")
    print("  1. 查看shot_prompts/目录下的.txt文件")
    print("  2. 确认prompts包含水墨风格关键词 (ink wash, brush strokes, etc.)")
    print("  3. 确认prompts包含武侠元素 (sword, bamboo, hanfu, etc.)")
    print("  4. 确认角色描述正确 (剑客白衣, 道人灰袍)")
    print("=" * 80)

    return results


if __name__ == "__main__":
    result = asyncio.run(run_wuxia_generality_test())
    print("\n测试结束")
