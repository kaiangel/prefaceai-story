#!/usr/bin/env python3
"""
teststory6.3.9.1 - 验证新prompt策略

测试目标：验证"参考图做主，文字做辅"策略对3人场景的效果
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

# 输入：使用teststory6.3.9的数据
INPUT_DIR = Path("test_output/manualtest/teststory6.3.9")
# 输出：新目录
OUTPUT_DIR = Path("test_output/manualtest/teststory6.3.9.1")


async def main():
    """主测试流程"""
    print("=" * 80)
    print("teststory6.3.9.1 - 新Prompt策略验证")
    print(f"时间: {datetime.now().isoformat()}")
    print("=" * 80)

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    images_dir = OUTPUT_DIR / "images"
    images_dir.mkdir(exist_ok=True)
    debug_dir = OUTPUT_DIR / "debug"
    debug_dir.mkdir(exist_ok=True)

    # 加载数据
    with open(INPUT_DIR / "story.json", 'r', encoding='utf-8') as f:
        story = json.load(f)

    with open(INPUT_DIR / "shots.json", 'r', encoding='utf-8') as f:
        shots = json.load(f)

    characters = story.get('characters', [])
    print(f"✅ 加载数据: {len(shots)} shots, {len(characters)} characters")

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
    scene_ref_name = None
    if scene_refs_dir.exists():
        for ref_file in scene_refs_dir.glob("*.png"):
            scene_ref_image = Image.open(ref_file)
            scene_ref_name = ref_file.name
            print(f"   ✅ 加载场景参考图: {ref_file.name}")
            break

    # 初始化服务
    service = StoryboardService()
    image_gen = ImageGenerator()

    # 测试简短标识符
    print("\n" + "=" * 60)
    print("简短标识符测试")
    print("=" * 60)
    for char in characters:
        brief_id = service._build_brief_identifier(char)
        print(f"  {char['name']} → {brief_id}")

    # 测试shot 6和7（3人场景）
    test_shot_indices = [5, 6]  # shot 6, 7
    results = []

    for idx in test_shot_indices:
        shot = shots[idx]
        shot_id = shot.get('shot_id', idx + 1)
        chars_in_scene = shot.get('characters_in_scene', [])

        print(f"\n{'='*60}")
        print(f"生成 Shot {shot_id} (3人场景)")
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

        print(f"\n新prompt ({len(new_prompt)} chars):")
        print("-" * 40)
        # 只打印前500字符
        print(new_prompt[:500] + "..." if len(new_prompt) > 500 else new_prompt)

        # 保存完整prompt
        prompt_file = debug_dir / f"shot_{shot_id:02d}_prompt.txt"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(f"Shot {shot_id} 新Prompt\n")
            f.write(f"生成时间: {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n\n")
            f.write(new_prompt)
            f.write(f"\n\n{'='*60}\n")
            f.write(f"Prompt长度: {len(new_prompt)} 字符\n")
            f.write(f"角色数: {len(chars_in_scene)}\n")

        # 准备参考图
        all_refs = []
        ref_sources = []
        for char_id in chars_in_scene:
            if char_id in char_ref_images:
                refs = char_ref_images[char_id]
                all_refs.append(refs['portrait'])
                ref_sources.append(f"{char_id}_portrait")
                all_refs.append(refs['fullbody'])
                ref_sources.append(f"{char_id}_fullbody")

        if scene_ref_image:
            all_refs.append(scene_ref_image)
            ref_sources.append(scene_ref_name)

        print(f"\n参考图 ({len(all_refs)}张): {ref_sources}")

        # 更新shot
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
            image_path = images_dir / f"shot_{shot_id:02d}.png"
            result['pil_image'].save(str(image_path))
            print(f"\n✅ 生成成功: {image_path.name}")
            results.append({'shot_id': shot_id, 'success': True, 'path': str(image_path)})
        else:
            print(f"\n❌ 生成失败: {result.get('error', 'unknown')}")
            results.append({'shot_id': shot_id, 'success': False, 'error': result.get('error')})

        await asyncio.sleep(3.0)

    # 保存摘要
    summary_file = OUTPUT_DIR / "summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("teststory6.3.9.1 - 新Prompt策略验证\n")
        f.write(f"测试时间: {datetime.now().isoformat()}\n")
        f.write("=" * 60 + "\n\n")

        f.write("## 修改内容\n")
        f.write("策略: 参考图做主，文字做辅\n\n")
        f.write("1. _build_brief_identifier: 简短角色标识\n")
        f.write("   例: 'young woman in cream sweater'\n\n")
        f.write("2. _build_shot_prompt: 新结构\n")
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

        f.write("\n## 对比目录\n")
        f.write(f"旧版本: {INPUT_DIR}/images/\n")
        f.write(f"新版本: {OUTPUT_DIR}/images/\n")

    print(f"\n💾 保存摘要: {summary_file}")

    print("\n" + "=" * 80)
    success_count = sum(1 for r in results if r['success'])
    print(f"验证完成: {success_count}/{len(results)} 张图片生成成功")
    print("=" * 80)

    print(f"\n对比目录：")
    print(f"  旧版本: {INPUT_DIR}/images/shot_06.png, shot_07.png")
    print(f"  新版本: {OUTPUT_DIR}/images/")


if __name__ == "__main__":
    asyncio.run(main())
