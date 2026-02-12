#!/usr/bin/env python3
"""
teststory6.3.6 - 验证P1.1修复效果（scene_refs差异化生成）

新增修复内容（相比6.3.5）：
- P1.1: SceneReferenceManager差异化生成
  - 每个scene独立生成一张scene_ref（不再去重）
  - 保留完整的场景上下文：time, mood, scene_style
  - 根据上下文推断不同的景别和角度
  - 根据lighting/atmosphere/time_of_day调整光线描述

验证重点：
1. scene_refs差异化：
   - 同类型（interior/exterior）的图应该是同一个场景，但角度/景别/光线不同
   - 能看出时间变化（如凌晨2:15 vs 凌晨5:30）
   - 能看出氛围变化（如sterile_lonely vs heartwarming_hopeful）
2. scene_refs一致性（继承自P1）：
   - 同类型场景参考图仍然看起来是同一家便利店
3. 生成数量：应该是8个scene，每个scene一张参考图

输出目录: test_output/manualtest/teststory6.3.6/
"""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.image_generator import ImageGenerator
from app.services.scene_reference_manager import SceneReferenceManager
from app.services.style_enforcer import StyleEnforcer
from app.models.style_config import ProjectStyleConfig


# 输出目录
OUTPUT_DIR = Path("test_output/manualtest/teststory6.3.6")

# 使用teststory6.3.5的story.json（已有完整的scene_style信息）
STORY_JSON_PATH = Path("test_output/manualtest/teststory6.3.5/story.json")


async def run_scene_ref_differentiation_test():
    """运行场景参考图差异化测试"""

    print("="*80)
    print("teststory6.3.6 - 验证P1.1修复效果（scene_refs差异化生成）")
    print("="*80)
    print("\n新增修复内容（P1.1）：")
    print("  - 每个scene独立生成一张scene_ref")
    print("  - 保留完整场景上下文: time, mood, scene_style")
    print("  - 根据上下文推断不同景别/角度")
    print("  - 根据lighting/atmosphere调整光线描述")
    print("\n验证重点：")
    print("  1. 差异化: 同类型图应该角度/景别/光线不同")
    print("  2. 一致性: 同类型图仍然是同一家店")
    print("  3. 数量: 8个scene应生成8+张参考图")
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
    print(f"\n✅ 加载story.json: {len(scenes)} scenes")

    # 打印每个scene的差异化信息
    print("\n" + "="*60)
    print("场景差异化信息预览")
    print("="*60)
    for scene in scenes:
        scene_id = scene.get('scene_id')
        location = scene.get('location', '')[:30]
        time = scene.get('time', '')
        mood = scene.get('mood', '')[:20]
        scene_style = scene.get('scene_style', {})
        lighting = scene_style.get('lighting', '')
        atmosphere = scene_style.get('atmosphere', '')
        time_of_day = scene_style.get('time_of_day', '')

        print(f"  Scene {scene_id}: {location}...")
        print(f"    时间: {time}, time_of_day: {time_of_day}")
        print(f"    氛围: {mood}, atmosphere: {atmosphere}")
        print(f"    光线: {lighting}")

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "scene_refs").mkdir(exist_ok=True)

    # 初始化服务
    image_gen = ImageGenerator()
    scene_ref_manager = SceneReferenceManager()
    style_config = ProjectStyleConfig(style_preset="realistic")

    # ===== P1.1修复核心：使用差异化链式生成 =====
    print("\n" + "="*60)
    print("开始生成差异化场景参考图（P1.1修复核心）")
    print("="*60)
    print("📎 关键改动: 每个scene独立生成，使用场景上下文差异化")

    scene_results = await scene_ref_manager.generate_all_scene_references_chained(
        scenes=scenes,
        project_style=style_config,
        image_generator=image_gen,
        delay=3.0
    )

    # 手动保存所有场景参考图（因为新格式使用scene_id区分）
    scene_refs_dir = OUTPUT_DIR / "scene_refs"
    saved_count = 0

    for key, views in scene_ref_manager.scene_references.items():
        for view_key, image in views.items():
            filename = f"{key}_{view_key}.png"
            filepath = scene_refs_dir / filename
            image.save(str(filepath))
            saved_count += 1
            print(f"  💾 保存: {filename}")

    # 统计生成结果
    scene_ref_count = saved_count
    print(f"\n✅ 场景参考图生成完成: {scene_ref_count} 张")

    # 复制story.json到输出目录
    with open(OUTPUT_DIR / "story.json", 'w', encoding='utf-8') as f:
        json.dump(story, f, ensure_ascii=False, indent=2)

    # 保存结果摘要
    results = {
        "test_name": "teststory6.3.6",
        "description": "验证P1.1修复效果（scene_refs差异化生成）",
        "fixes_tested": [
            "P1.1: scene_ref差异化生成",
            "每个scene独立生成",
            "使用场景上下文(time, mood, scene_style)差异化",
            "推断不同景别和角度"
        ],
        "scene_count": len(scenes),
        "scene_ref_count": scene_ref_count,
        "scene_results": {k: {"views": list(v.keys()) if isinstance(v, dict) else "error"} for k, v in scene_results.items()}
    }

    results_path = OUTPUT_DIR / "verification_results.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 打印验证指南
    print("\n" + "="*80)
    print("测试完成总结")
    print("="*80)

    print(f"\n📁 输出目录: {OUTPUT_DIR}")
    print(f"\n📊 生成结果:")
    print(f"  - scene_refs/: ✅ ({scene_ref_count} 张)")
    print(f"  - story.json: ✅ (复制)")
    print(f"  - verification_results.json: ✅")

    print("\n" + "="*80)
    print("🔍 请手动验证以下关键点（P1.1修复核心验证）：")
    print("="*80)
    print("  1. 差异化验证: scene_refs/目录中的同类型图片")
    print("     - 是否有不同的角度？（wide shot vs medium shot vs close shot）")
    print("     - 是否有不同的视角？（eye level vs high angle vs dutch angle）")
    print("     - 是否能看出时间变化？（midnight vs dawn的光线差异）")
    print("     - 是否能看出氛围变化？（sterile vs hopeful的色调差异）")
    print("  2. 一致性验证:")
    print("     - 同类型图片是否仍然看起来是同一家便利店？")
    print("     - 墙面颜色、货架布局、灯具样式是否一致？")
    print("  3. 日志检查: 是否看到了以下日志？")
    print('     - "📎 启用链式生成 + 差异化（根据时间/氛围/光线）"')
    print('     - "凌晨2:15分, midnight, sterile_lonely" 等差异化标签')
    print('     - "🔗 设为interior/exterior锚点图"')
    print('     - "📸 使用参考图 + 差异化上下文"')
    print("="*80)

    # 列出生成的文件
    print("\n📂 生成的文件列表:")
    for f in sorted(scene_refs_dir.glob("*.png")):
        print(f"  - {f.name}")

    return results


if __name__ == "__main__":
    result = asyncio.run(run_scene_ref_differentiation_test())
    print("\n测试结束")
