#!/usr/bin/env python3
"""
teststory6 - 验证prompt策略优化

测试目标：
1. 验证新的 _build_shot_prompt 输出格式正确
2. 验证 _build_brief_identifier 输出简短标识
3. 用3人场景(shot 6, 7)测试角色一致性是否改善
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.storyboard_service import StoryboardService
from app.services.image_generator import ImageGenerator

# 输入：使用已有的teststory6.3.9数据
INPUT_DIR = Path("test_output/manualtest/teststory6.3.9")
# 输出：新的测试目录
OUTPUT_DIR = Path("test_output/manualtest/teststory6_verify_fixes")


def test_brief_identifier():
    """测试 _build_brief_identifier 方法"""
    print("=" * 60)
    print("测试 _build_brief_identifier")
    print("=" * 60)

    service = StoryboardService()

    # 测试用例
    test_characters = [
        {
            "name": "林小雨",
            "name_en": "Lin Xiaoyu",
            "gender": "female",
            "age_appearance": "young_adult",
            "clothing": {
                "top": "oversized cream-colored knit sweater with thumb holes"
            }
        },
        {
            "name": "张远",
            "name_en": "Zhang Yuan",
            "gender": "male",
            "age_appearance": "adult",
            "clothing": {
                "top": "navy blue button-up shirt with sleeves rolled"
            }
        },
        {
            "name": "陈婉",
            "name_en": "Chen Wan",
            "gender": "female",
            "age_appearance": "middle_aged",
            "clothing": {
                "top": "burgundy apron over cream-colored long-sleeve blouse"
            }
        }
    ]

    print("\n简短标识符输出：")
    for char in test_characters:
        brief_id = service._build_brief_identifier(char)
        print(f"  {char['name']} → {brief_id}")

    return True


def test_new_prompt_structure():
    """测试新的 _build_shot_prompt 输出结构"""
    print("\n" + "=" * 60)
    print("测试 _build_shot_prompt 新结构")
    print("=" * 60)

    service = StoryboardService()

    # 加载真实数据
    with open(INPUT_DIR / "story.json", 'r', encoding='utf-8') as f:
        story = json.load(f)

    with open(INPUT_DIR / "shots.json", 'r', encoding='utf-8') as f:
        shots = json.load(f)

    characters = story.get('characters', [])

    # 测试3人场景 (shot 6 和 7)
    test_shots = [shots[5], shots[6]]  # index 5, 6 = shot 6, 7

    print("\n新prompt结构示例：")
    for shot in test_shots:
        shot_id = shot.get('shot_id', '?')
        chars_in_scene = shot.get('characters_in_scene', [])

        new_prompt = service._build_shot_prompt(
            shot=shot,
            characters=characters,
            style_preset="realistic",
            location="咖啡馆",
            time="深夜",
            mood="温馨",
            scene_style=shot.get('scene_style', {}),
            characters_in_scene=chars_in_scene
        )

        print(f"\n{'='*40}")
        print(f"Shot {shot_id} (角色: {len(chars_in_scene)}人)")
        print(f"{'='*40}")
        print(f"characters_in_scene: {chars_in_scene}")
        print(f"\n新prompt ({len(new_prompt)} chars):")
        print("-" * 40)
        print(new_prompt)

    return True


async def generate_verification_images():
    """生成验证图片"""
    print("\n" + "=" * 60)
    print("生成验证图片 (3人场景)")
    print("=" * 60)

    # 加载数据
    with open(INPUT_DIR / "story.json", 'r', encoding='utf-8') as f:
        story = json.load(f)

    with open(INPUT_DIR / "shots.json", 'r', encoding='utf-8') as f:
        shots = json.load(f)

    characters = story.get('characters', [])

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    images_dir = OUTPUT_DIR / "images"
    images_dir.mkdir(exist_ok=True)
    debug_dir = OUTPUT_DIR / "debug"
    debug_dir.mkdir(exist_ok=True)

    # 加载参考图
    char_refs_dir = INPUT_DIR / "character_refs"
    char_ref_images = {}

    for char in characters:
        char_id = char.get('id')
        portrait_path = char_refs_dir / f"{char_id}_portrait.png"
        fullbody_path = char_refs_dir / f"{char_id}_fullbody.png"

        if portrait_path.exists() and fullbody_path.exists():
            char_ref_images[char_id] = {
                'portrait': Image.open(portrait_path),
                'fullbody': Image.open(fullbody_path)
            }
            print(f"   ✅ 加载 {char_id} 参考图")

    # 加载场景参考图
    scene_refs_dir = INPUT_DIR / "scene_refs"
    scene_ref_image = None
    if scene_refs_dir.exists():
        for ref_file in scene_refs_dir.glob("*.png"):
            scene_ref_image = Image.open(ref_file)
            print(f"   ✅ 加载场景参考图: {ref_file.name}")
            break

    # 初始化服务
    service = StoryboardService()
    image_gen = ImageGenerator()

    # 测试shot 6和7（3人场景）
    test_shot_indices = [5, 6]  # shot 6, 7
    results = []

    for idx in test_shot_indices:
        shot = shots[idx]
        shot_id = shot.get('shot_id', idx + 1)
        chars_in_scene = shot.get('characters_in_scene', [])

        print(f"\n{'='*60}")
        print(f"生成 Shot {shot_id}")
        print(f"角色: {chars_in_scene}")
        print(f"{'='*60}")

        # 构建新prompt
        new_prompt = service._build_shot_prompt(
            shot=shot,
            characters=characters,
            style_preset="realistic",
            location="咖啡馆",
            time="深夜",
            mood="温馨",
            scene_style=shot.get('scene_style', {}),
            characters_in_scene=chars_in_scene
        )

        # 保存新prompt到debug目录
        prompt_file = debug_dir / f"shot_{shot_id:02d}_new_prompt.txt"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(f"Shot {shot_id} 新Prompt\n")
            f.write(f"生成时间: {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n\n")
            f.write(new_prompt)
            f.write(f"\n\n{'='*60}\n")
            f.write(f"Prompt长度: {len(new_prompt)} 字符\n")
            f.write(f"角色数: {len(chars_in_scene)}\n")
        print(f"   💾 保存prompt: {prompt_file.name}")

        # 准备参考图（按顺序：角色portrait+fullbody，然后场景）
        all_refs = []
        for char_id in chars_in_scene:
            if char_id in char_ref_images:
                refs = char_ref_images[char_id]
                all_refs.append(refs['portrait'])
                all_refs.append(refs['fullbody'])

        if scene_ref_image:
            all_refs.append(scene_ref_image)

        print(f"   📎 参考图数量: {len(all_refs)}")

        # 更新shot的image_prompt为新格式
        shot_copy = shot.copy()
        shot_copy['image_prompt'] = new_prompt
        shot_copy['negative_prompt'] = "blurry, low quality, distorted, deformed, bad anatomy, extra limbs, missing limbs, mutated hands, extra fingers, fewer fingers, text, watermark, signature, logo, cropped, out of frame, duplicate, ugly, disfigured, malformed, cartoon, anime, illustration, painting, drawn, 3d render"

        # 生成图像
        result = await image_gen.generate_shot_image(
            shot=shot_copy,
            reference_images=all_refs[:14],
            aspect_ratio="16:9",
            use_llm_translation=False
        )

        if result.get('success'):
            image_path = images_dir / f"shot_{shot_id:02d}_new.png"
            result['pil_image'].save(str(image_path))
            print(f"   ✅ 生成成功: {image_path.name}")
            results.append({'shot_id': shot_id, 'success': True, 'path': str(image_path)})
        else:
            print(f"   ❌ 生成失败: {result.get('error', 'unknown')}")
            results.append({'shot_id': shot_id, 'success': False, 'error': result.get('error')})

        await asyncio.sleep(3.0)

    # 保存结果摘要
    summary_file = OUTPUT_DIR / "verification_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("Prompt策略优化验证结果\n")
        f.write(f"测试时间: {datetime.now().isoformat()}\n")
        f.write("=" * 60 + "\n\n")

        f.write("## 修改内容\n")
        f.write("1. _build_brief_identifier: 生成简短角色标识\n")
        f.write("2. _build_shot_prompt: 新prompt结构\n")
        f.write("   - REFERENCE IMAGES: 简短标识 + 索引\n")
        f.write("   - SCENE: 动作和位置\n")
        f.write("   - ATMOSPHERE: 氛围和光线\n")
        f.write("   - COMPOSITION: 构图信息\n\n")

        f.write("## 测试结果\n")
        for r in results:
            status = "✅" if r['success'] else "❌"
            f.write(f"{status} Shot {r['shot_id']}: ")
            if r['success']:
                f.write(f"{r['path']}\n")
            else:
                f.write(f"失败 - {r.get('error', 'unknown')}\n")

    print(f"\n💾 保存摘要: {summary_file}")
    return results


async def main():
    """主测试流程"""
    print("=" * 80)
    print("teststory6 - 验证Prompt策略优化")
    print(f"时间: {datetime.now().isoformat()}")
    print("=" * 80)

    # 1. 测试简短标识符
    test_brief_identifier()

    # 2. 测试新prompt结构
    test_new_prompt_structure()

    # 3. 生成验证图片
    results = await generate_verification_images()

    print("\n" + "=" * 80)
    success_count = sum(1 for r in results if r['success'])
    print(f"验证完成: {success_count}/{len(results)} 张图片生成成功")
    print("=" * 80)

    print(f"\n请查看以下目录对比效果：")
    print(f"  旧版本: {INPUT_DIR}/images/")
    print(f"  新版本: {OUTPUT_DIR}/images/")


if __name__ == "__main__":
    asyncio.run(main())
