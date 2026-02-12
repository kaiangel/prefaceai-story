#!/usr/bin/env python3
"""
teststory6.3.7 - 验证P1.2修复效果（强制变体机制）

新增修复内容（相比6.3.6）：
- P1.2: 强制分配不同变体（不再依赖mood推断）
  - _get_forced_variation(): 6种interior变体 + 5种exterior变体
  - 重写prompt，使用强制性语言（MANDATORY, CRITICAL, MUST）
  - 添加诊断日志打印实际变体值

验收标准（6张interior应该明显不同）：
1. 至少1张鸟瞰图（从天花板看下去）
2. 至少1张低角度图（从货架下方看上去）
3. 至少1张侧面图（从店铺侧面看过去）
4. 每张图的构图必须明显不同，但能看出是同一家店

输出目录: test_output/manualtest/teststory6.3.7/
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
OUTPUT_DIR = Path("test_output/manualtest/teststory6.3.7")

# 使用teststory6.3.5的story.json（已有完整的scene_style信息）
STORY_JSON_PATH = Path("test_output/manualtest/teststory6.3.5/story.json")


async def run_forced_variation_test():
    """运行强制变体测试"""

    print("="*80)
    print("teststory6.3.7 - 验证P1.2修复效果（强制变体机制）")
    print("="*80)
    print("\n新增修复内容（P1.2）：")
    print("  - 强制分配不同变体（不再依赖mood推断）")
    print("  - 6种interior变体 + 5种exterior变体")
    print("  - 重写prompt，使用强制性语言（MANDATORY, CRITICAL, MUST）")
    print("  - 添加诊断日志打印实际变体值")
    print("\n验收标准（6张interior应该明显不同）：")
    print("  1. 至少1张鸟瞰图（从天花板看下去）")
    print("  2. 至少1张低角度图（从货架下方看上去）")
    print("  3. 至少1张侧面图（从店铺侧面看过去）")
    print("  4. 每张图构图明显不同，但能看出是同一家店")
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

    # ===== P1.2修复核心：强制变体机制 =====
    print("\n" + "="*60)
    print("开始生成强制变体场景参考图（P1.2修复核心）")
    print("="*60)
    print("📎 关键改动: 强制分配不同景别+角度组合")
    print("📎 预期日志: '📐 强制变体: 鸟瞰全景 | shot=...'")

    scene_results = await scene_ref_manager.generate_all_scene_references_chained(
        scenes=scenes,
        project_style=style_config,
        image_generator=image_gen,
        delay=3.0
    )

    # 手动保存所有场景参考图
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
        "test_name": "teststory6.3.7",
        "description": "验证P1.2修复效果（强制变体机制）",
        "fixes_tested": [
            "P1.2: 强制分配不同变体",
            "_get_forced_variation(): 6种interior + 5种exterior变体",
            "重写prompt使用强制性语言",
            "诊断日志打印实际变体值"
        ],
        "acceptance_criteria": [
            "至少1张鸟瞰图（从天花板看下去）",
            "至少1张低角度图（从货架下方看上去）",
            "至少1张侧面图（从店铺侧面看过去）",
            "每张图构图明显不同，但能看出是同一家店"
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
    print("🔍 请手动验证以下关键点（P1.2强制变体验证）：")
    print("="*80)
    print("\n📌 Interior验收标准（6张应该明显不同）：")
    print("  1. ✅ 至少1张鸟瞰图（从天花板看下去，看到整个店铺布局）")
    print("  2. ✅ 至少1张低角度图（从货架下方看上去，仰视角度）")
    print("  3. ✅ 至少1张侧面图（从店铺侧面看过去，收银台视角）")
    print("  4. ✅ 每张图构图明显不同")
    print("  5. ✅ 所有图都能看出是同一家便利店")

    print("\n📌 日志检查（应该看到以下输出）：")
    print('  - "📐 强制变体: 鸟瞰全景 | shot=extreme wide shot, bird\'s eye view"')
    print('  - "📐 强制变体: 平视饮料区 | shot=medium shot"')
    print('  - "📐 强制变体: 低角度仰视货架 | shot=close-up shot"')
    print('  - "📐 强制变体: 收银台侧面 | shot=wide shot"')
    print("  等不同变体的日志")
    print("="*80)

    # 列出生成的文件
    print("\n📂 生成的文件列表:")
    interior_count = 0
    exterior_count = 0
    for f in sorted(scene_refs_dir.glob("*.png")):
        print(f"  - {f.name}")
        if "interior" in f.name:
            interior_count += 1
        elif "exterior" in f.name:
            exterior_count += 1

    print(f"\n📊 统计: {interior_count} 张interior, {exterior_count} 张exterior")

    return results


if __name__ == "__main__":
    result = asyncio.run(run_forced_variation_test())
    print("\n测试结束")
