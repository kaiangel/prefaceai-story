#!/usr/bin/env python3
"""
teststory6.3.8 - 验证P2.0新架构（锚点图 + ShotPromptGenerator）

新架构核心改动：
1. scene_refs简化：每种类型只生成1张锚点图（不再尝试差异化）
2. shots差异化：使用ShotPromptGenerator为每个shot生成定制化prompt
3. 差异化由shots阶段的prompt决定，而不是scene_refs

测试流程：
1. 加载teststory6.3.5的story.json
2. 使用P2.0的generate_anchor_images()生成锚点图（应该只有2-4张）
3. 使用ShotPromptGenerator为前几个shot生成prompt
4. 验证prompts的差异化质量

输出目录: test_output/manualtest/teststory6.3.8/
"""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.image_generator import ImageGenerator
from app.services.scene_reference_manager import SceneReferenceManager
from app.services.shot_prompt_generator import ShotPromptGenerator
from app.models.style_config import ProjectStyleConfig


# 输出目录
OUTPUT_DIR = Path("test_output/manualtest/teststory6.3.8")

# 使用teststory6.3.5的story.json
STORY_JSON_PATH = Path("test_output/manualtest/teststory6.3.5/story.json")


async def run_p2_architecture_test():
    """运行P2.0新架构测试"""

    print("="*80)
    print("teststory6.3.8 - 验证P2.0新架构")
    print("="*80)
    print("\nP2.0核心改动：")
    print("  1. scene_refs简化：每种类型只生成1张锚点图")
    print("  2. shots差异化：使用ShotPromptGenerator生成定制化prompt")
    print("  3. 差异化发生在shots阶段，不在scene_refs阶段")
    print("="*80)

    # 检查story.json是否存在
    if not STORY_JSON_PATH.exists():
        print(f"\n❌ 找不到story.json: {STORY_JSON_PATH}")
        print("请先运行 test_story6_3_5.py 生成story.json")
        return None

    # 加载story.json
    with open(STORY_JSON_PATH, 'r', encoding='utf-8') as f:
        story = json.load(f)

    scenes = story.get('scenes', [])
    characters = story.get('characters', [])
    unique_locations = story.get('unique_locations', None)  # 新格式支持
    print(f"\n✅ 加载story.json: {len(scenes)} scenes, {len(characters)} characters")
    if unique_locations:
        print(f"   📍 发现 unique_locations: {len(unique_locations)} 个独特场景")

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "scene_refs").mkdir(exist_ok=True)
    (OUTPUT_DIR / "shot_prompts").mkdir(exist_ok=True)

    # 初始化服务
    image_gen = ImageGenerator()
    scene_ref_manager = SceneReferenceManager()
    shot_prompt_gen = ShotPromptGenerator()
    style_config = ProjectStyleConfig(style_preset="realistic")

    # ===== 阶段1：P2.0锚点图生成 =====
    print("\n" + "="*60)
    print("阶段1：P2.0锚点图生成（简化版）")
    print("="*60)
    print("📎 核心改动: 每种类型只生成1张高质量锚点图")
    print("📎 预期: 2-4张锚点图（interior/exterior各1张，可能有dawn版）")

    anchor_results = await scene_ref_manager.generate_anchor_images(
        scenes=scenes,
        project_style=style_config,
        image_generator=image_gen,
        unique_locations=unique_locations,  # 传递新格式数据（如果有）
        delay=3.0
    )

    # 保存锚点图
    scene_refs_dir = OUTPUT_DIR / "scene_refs"
    anchor_descriptions = {}

    for anchor_key, result in anchor_results.items():
        if 'image' in result:
            filename = f"{anchor_key}.png"
            filepath = scene_refs_dir / filename
            result['image'].save(str(filepath))
            print(f"  💾 保存锚点图: {filename}")
            anchor_descriptions[anchor_key] = result.get('description', '')

    print(f"\n✅ 锚点图生成完成: {len([r for r in anchor_results.values() if 'image' in r])} 张")

    # ===== 阶段2：ShotPromptGenerator测试 =====
    print("\n" + "="*60)
    print("阶段2：ShotPromptGenerator测试")
    print("="*60)
    print("📎 核心功能: 为每个shot生成定制化的图像prompt")
    print("📎 测试: 为前6个shot生成prompts，验证差异化质量")

    # 构建测试用的shots（从scenes中提取或模拟）
    test_shots = []
    for scene in scenes[:6]:  # 取前6个scene
        scene_id = scene.get('scene_id')
        shot = {
            'shot_id': scene_id,
            'scene_id': scene_id,
            'location': scene.get('location', ''),
            'narration': scene.get('narration', ''),
            'visual_description': scene.get('visual_description', ''),
            'mood': scene.get('mood', ''),
            'time': scene.get('time', ''),
            'scene_style': scene.get('scene_style', {}),
            'characters_in_scene': scene.get('characters_in_scene', []),
            # 模拟不同的shot类型
            'shot_type': ['wide shot', 'medium shot', 'close-up', 'medium close-up', 'wide shot', 'close-up'][scene_id - 1] if scene_id <= 6 else 'medium shot',
            'camera_angle': ['high angle', 'eye level', 'low angle', 'eye level', 'dutch angle', 'eye level'][scene_id - 1] if scene_id <= 6 else 'eye level',
        }
        test_shots.append(shot)

    # 生成prompts
    story_context = {
        "genre": story.get('genre', '都市情感'),
        "overall_mood": story.get('overall_mood', ''),
        "title": story.get('title', '凌晨便利店')
    }

    style_settings = {
        "style_preset": "realistic"
    }

    generated_prompts = []
    for i, shot in enumerate(test_shots):
        print(f"\n  生成Shot {shot['shot_id']} prompt...")

        # 确定使用哪个锚点
        location = shot.get('location', '')
        location_type = scene_ref_manager._infer_location_type(location, {})
        if location_type == 'exterior':
            anchor_desc = anchor_descriptions.get('exterior_anchor', '')
        else:
            anchor_desc = anchor_descriptions.get('interior_anchor', '')

        prompt = await shot_prompt_gen.generate_single_shot_prompt_for_test(
            shot_info=shot,
            scene_ref_description=anchor_desc,
            characters=characters,
            style_preset="realistic"
        )

        generated_prompts.append({
            'shot_id': shot['shot_id'],
            'shot_type': shot.get('shot_type', ''),
            'camera_angle': shot.get('camera_angle', ''),
            'mood': shot.get('mood', ''),
            'time': shot.get('time', ''),
            'prompt': prompt,
            'prompt_length': len(prompt)
        })

        # 保存prompt到文件
        prompt_file = OUTPUT_DIR / "shot_prompts" / f"shot_{shot['shot_id']:02d}_prompt.txt"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(f"=== Shot {shot['shot_id']} ===\n")
            f.write(f"Location: {shot.get('location', '')}\n")
            f.write(f"Time: {shot.get('time', '')}\n")
            f.write(f"Mood: {shot.get('mood', '')}\n")
            f.write(f"Shot Type: {shot.get('shot_type', '')}\n")
            f.write(f"Camera Angle: {shot.get('camera_angle', '')}\n")
            f.write(f"\n{'='*60}\n")
            f.write(f"GENERATED PROMPT:\n{'='*60}\n\n")
            f.write(prompt)

        print(f"    ✅ Shot {shot['shot_id']} prompt生成完成 ({len(prompt)} 字符)")

        # 避免API速率限制
        await asyncio.sleep(1.0)

    print(f"\n✅ Shot prompts生成完成: {len(generated_prompts)} 个")

    # ===== 阶段3：Prompt质量分析 =====
    print("\n" + "="*60)
    print("阶段3：Prompt质量分析")
    print("="*60)

    # 检查关键要素
    print("\n📊 Prompt结构检查:")
    for p in generated_prompts:
        shot_id = p['shot_id']
        prompt = p['prompt'].lower()

        checks = {
            'has_scene_section': '[scene' in prompt or 'scene consistency' in prompt.lower(),
            'has_shot_specs': 'shot' in prompt,
            'has_camera': 'angle' in prompt or 'camera' in prompt,
            'has_lighting': 'light' in prompt,
            'has_style': 'photo' in prompt or 'cinematic' in prompt or 'realistic' in prompt,
            'has_exclude': 'no ' in prompt or 'exclude' in prompt.lower(),
        }

        passed = sum(checks.values())
        print(f"  Shot {shot_id}: {passed}/6 要素 | {p['prompt_length']} 字符")

    # 保存结果摘要
    results = {
        "test_name": "teststory6.3.8",
        "description": "验证P2.0新架构（锚点图 + ShotPromptGenerator）",
        "architecture_changes": [
            "scene_refs简化：每种类型只生成1张锚点图",
            "ShotPromptGenerator：为每个shot动态生成prompt",
            "差异化发生在shots阶段"
        ],
        "anchor_images_count": len([r for r in anchor_results.values() if 'image' in r]),
        "anchor_keys": list(anchor_results.keys()),
        "shot_prompts_count": len(generated_prompts),
        "prompt_lengths": {p['shot_id']: p['prompt_length'] for p in generated_prompts}
    }

    results_path = OUTPUT_DIR / "verification_results.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 复制story.json
    with open(OUTPUT_DIR / "story.json", 'w', encoding='utf-8') as f:
        json.dump(story, f, ensure_ascii=False, indent=2)

    # 打印验证指南
    print("\n" + "="*80)
    print("测试完成总结")
    print("="*80)

    print(f"\n📁 输出目录: {OUTPUT_DIR}")
    print(f"\n📊 生成结果:")
    print(f"  - scene_refs/: ✅ ({len([r for r in anchor_results.values() if 'image' in r])} 张锚点图)")
    print(f"  - shot_prompts/: ✅ ({len(generated_prompts)} 个prompt文件)")
    print(f"  - story.json: ✅")
    print(f"  - verification_results.json: ✅")

    print("\n" + "="*80)
    print("🔍 验证要点:")
    print("="*80)
    print("\n📌 锚点图验证:")
    print("  1. 应该只有2-4张图（interior + exterior，可能有dawn版）")
    print("  2. 图片应该是高质量的全景/建立镜头")
    print("  3. 无人物，纯场景")

    print("\n📌 Shot Prompts验证:")
    print("  1. 查看 shot_prompts/ 目录下的.txt文件")
    print("  2. 每个prompt应该包含：")
    print("     - 场景一致性指令")
    print("     - 具体的景别和角度")
    print("     - 角色描述（如果有）")
    print("     - 光线和氛围")
    print("     - 风格关键词")
    print("  3. 不同shot的prompt应该有明显差异（景别/角度/焦点不同）")
    print("="*80)

    return results


if __name__ == "__main__":
    result = asyncio.run(run_p2_architecture_test())
    print("\n测试结束")
