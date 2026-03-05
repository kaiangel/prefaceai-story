"""
TASK-CROSS-STYLE-TEST: illustration 跨风格完整 E2E + 场域式 vs 命令式 A/B 测试

完整 E2E (Stage 1→5, ~18 shots) + 都市情感题材

控制变量:
  - Stage 1→4 只跑一次生成 storyboard
  - Stage 5 用同一个 storyboard + 同一套参考图跑两次
  - A组: 命令式 style_description (当前 illustration preset)
  - B组: 场域式 style_description (AI-ML 改写版本, PM 核验通过)
  - mandatory_keywords + forbidden_keywords 两组完全相同

评估维度 (4项):
  1. 风格准确度 — 是否贴合 illustration 风格特征
  2. 色彩与光影 — 颜色运用、明暗层次、光影叙事
  3. 细节与质感 — 画面精细度、材质表现
  4. 角色一致性 — 同一角色跨 shot 外观稳定性

text_type 分布统计 (DIALOGUE-SYSTEM 首次真实 E2E 验证):
  - dialogue(含混合类型) ≥60%?
  - narration ≤10%?
  - none = 0%?

一石三鸟: 场域式泛化性 + DIALOGUE-SYSTEM 对话占比 + NB2 跨风格表现

作者: @Tester
日期: 2026-02-28
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from PIL import Image
from app.services.story_outline_generator import StoryOutlineGenerator
from app.services.character_designer import CharacterDesigner
from app.services.screenplay_writer import ScreenplayWriter
from app.services.storyboard_director import StoryboardDirector
from app.services.image_generator import ImageGenerator
from app.services.reference_image_manager import ReferenceImageManager
from app.services.scene_reference_manager import SceneReferenceManager
from app.services.style_enforcer import StyleEnforcer
from app.models.style_config import ProjectStyleConfig


# =========== 配置 ===========
OUTPUT_BASE = "./test_output/manualtest/cross_style_test"
STYLE_PRESET = "illustration"

# 故事 idea — 都市情感 (PM 指定: 都市情感或家庭生活, 不用篮球)
STORY_IDEA = (
    "三十岁的咖啡馆老板娘暗恋来店里写代码的程序员三年，"
    "某天他带着另一个女孩来，她鼓起勇气在咖啡拉花上写下了一直未说出口的话"
)

# A 组: 命令式 (当前 illustration preset style_description, 不改代码)
STYLE_DESC_A = (
    "This image MUST be in polished digital illustration style "
    "with vibrant colors, clean lines, and rich details."
)

# B 组: 场域式 (AI-ML 提供, PM 2026-02-28 核验通过)
STYLE_DESC_B = (
    "You are creating in the tradition of the finest digital illustrators — artists who treat "
    "every frame as a painting that tells a story. Light pours through windows and catches in hair, "
    "pooling in warm gradients that guide the eye to what matters most. Colors breathe with intention: "
    "warm ambers for intimacy, cool blues for solitude, saturated accents that anchor emotion. Every "
    "surface carries just enough texture to feel alive — the weave of fabric, the sheen of rain-wet "
    "pavement, the soft glow of a phone screen in twilight. Characters inhabit their world through "
    "posture, micro-expression, and the charged space between them. Each composition balances clarity "
    "with depth, placing the viewer exactly where the feeling lives."
)


# =========== 工具函数 ===========

def load_json(filepath: str) -> dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(filepath: str, data) -> None:
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def analyze_text_type_distribution(storyboard: dict) -> dict:
    """
    分析 storyboard 中 text_type 分布
    PM 要求: dialogue(含混合) >= 60%, narration <= 10%, none = 0%
    """
    shots = storyboard.get("shots", [])
    total = len(shots)

    type_counts = {}
    dialogue_family = 0   # dialogue + dialogue_with_thought + dialogue_with_narration + narration_with_dialogue
    narration_family = 0  # narration + narration_with_thought (不含含 dialogue 的混合类型)

    for shot in shots:
        text_overlay = shot.get("text_overlay", {})
        text_type = text_overlay.get("text_type", "none")
        type_counts[text_type] = type_counts.get(text_type, 0) + 1

        # dialogue 家族: 包含 "dialogue" 的所有类型
        if "dialogue" in text_type:
            dialogue_family += 1
        # narration 家族: 纯 narration / narration_with_thought (不含 dialogue 的)
        elif text_type in ["narration", "narration_with_thought"]:
            narration_family += 1

    dialogue_pct = (dialogue_family / total * 100) if total > 0 else 0
    narration_pct = (narration_family / total * 100) if total > 0 else 0
    none_count = type_counts.get("none", 0)

    return {
        "total_shots": total,
        "type_counts": type_counts,
        "dialogue_family_count": dialogue_family,
        "dialogue_family_pct": round(dialogue_pct, 1),
        "narration_family_count": narration_family,
        "narration_family_pct": round(narration_pct, 1),
        "none_count": none_count,
        "dialogue_ge_60": dialogue_pct >= 60,
        "narration_le_10": narration_pct <= 10,
        "none_eq_0": none_count == 0
    }


def get_location_id_for_scene(
    scene_id: int,
    screenplay: dict,
    unique_locations: list
) -> Optional[str]:
    """从 scene_id 获取 location_id (复用 pipeline_orchestrator 逻辑)"""
    if not scene_id or not screenplay:
        return None

    screenplay_location_id = None
    for scene in screenplay.get("scenes", []):
        if scene.get("scene_id") == scene_id:
            screenplay_location_id = scene.get("location_id")
            break

    if not screenplay_location_id:
        return None

    if not unique_locations:
        return screenplay_location_id

    # 精确匹配
    for loc in unique_locations:
        if loc.get("location_id") == screenplay_location_id:
            return screenplay_location_id

    # fallback
    if unique_locations:
        return unique_locations[0].get("location_id")

    return screenplay_location_id


# =========== 核心: A/B 组 shot 生成 ===========

async def generate_all_shots(
    group_name: str,
    style_desc: str,
    shots: list,
    storyboard: dict,
    characters: dict,
    screenplay: dict,
    image_generator: ImageGenerator,
    ref_manager: ReferenceImageManager,
    scene_ref_manager: Optional[SceneReferenceManager],
    unique_locations: list,
    output_dir: str
) -> list:
    """
    为一组生成所有 shots (完整 Stage 5)

    临时覆盖 style_description, 生成完恢复, 确保 A/B 组互不污染
    维护 previous_shot_image 链保证 shot 间连续性
    """
    results = []

    # 临时覆盖 style_description (仅改 style_description, mandatory/forbidden 不动)
    original_desc = StyleEnforcer.STYLE_ENFORCEMENTS[STYLE_PRESET].style_description
    StyleEnforcer.STYLE_ENFORCEMENTS[STYLE_PRESET].style_description = style_desc

    previous_shot_image = None
    previous_shot = None

    try:
        for i, shot in enumerate(shots):
            shot_id = shot.get("shot_id", i + 1)
            text_type = shot.get("text_overlay", {}).get("text_type", "none")

            print(f"\n  [{group_name}] Shot {shot_id:02d}/{len(shots)} ({text_type})...")

            # 获取角色参考图
            char_direction = shot.get("character_direction", {})
            chars_in_scene = char_direction.get("characters_visible", [])
            char_refs = ref_manager.get_references_for_scene(chars_in_scene)

            # 获取场景参考图
            scene_refs = []
            location_id = None
            if scene_ref_manager:
                scene_id = shot.get("scene_id")
                location_id = get_location_id_for_scene(
                    scene_id, screenplay, unique_locations
                )
                if location_id:
                    scene_refs = scene_ref_manager.get_references_for_location(location_id)

            all_refs = char_refs + scene_refs

            gen_start = time.time()
            result = await image_generator.generate_shot_image_phase2(
                shot=shot,
                storyboard=storyboard,
                characters=characters,
                style_preset=STYLE_PRESET,
                reference_images=all_refs,
                previous_shot_image=previous_shot_image,
                previous_shot=previous_shot,
                screenplay=screenplay,
                aspect_ratio="2:3",
                use_native_text=True
            )
            gen_time = time.time() - gen_start

            shot_result = {
                "shot_id": shot_id,
                "text_type": text_type,
                "chars_in_scene": chars_in_scene,
                "char_refs_count": len(char_refs),
                "scene_refs_count": len(scene_refs),
                "success": False,
                "generation_time": round(gen_time, 2)
            }

            if result.get("success"):
                img = result["pil_image"]
                img_path = os.path.join(output_dir, f"shot_{shot_id:02d}.png")
                img.save(img_path)
                shot_result["success"] = True
                shot_result["size"] = f"{img.size[0]}x{img.size[1]}"
                shot_result["image_path"] = img_path

                # 更新前序 shot (连续性链)
                previous_shot_image = img
                previous_shot = shot

                print(f"    ✅ ({gen_time:.1f}s, {img.size[0]}x{img.size[1]}, refs={len(all_refs)})")
            else:
                shot_result["error"] = result.get("error", "Unknown")
                print(f"    ❌ {shot_result['error']}")

            results.append(shot_result)
            await asyncio.sleep(2)

    finally:
        # 恢复原始 style_description
        StyleEnforcer.STYLE_ENFORCEMENTS[STYLE_PRESET].style_description = original_desc

    return results


# =========== 主测试流程 ===========

async def run_cross_style_test():
    """运行 TASK-CROSS-STYLE-TEST 完整 E2E + A/B 测试"""
    total_start = datetime.now()
    project_id = total_start.strftime("%Y%m%d_%H%M%S")
    project_dir = os.path.join(OUTPUT_BASE, project_id)
    os.makedirs(project_dir, exist_ok=True)

    print("=" * 70)
    print("TASK-CROSS-STYLE-TEST: illustration 跨风格 E2E + A/B 测试")
    print("=" * 70)
    print(f"Project ID: {project_id}")
    print(f"Story idea: {STORY_IDEA}")
    print(f"Style: {STYLE_PRESET}")
    print(f"Model: NB2 (gemini-3.1-flash-image-preview)")
    print(f"use_native_text: True")
    print(f"Output: {project_dir}")
    print()
    print(f"A 组 (命令式): {STYLE_DESC_A}")
    print(f"B 组 (场域式): {STYLE_DESC_B[:80]}...")
    print()
    print("控制变量: Stage 1→4 一次 → Stage 5 两次 (A/B)")
    print("评估: 风格准确度 + 色彩与光影 + 细节与质感 + 角色一致性")
    print("=" * 70)

    # ============================================================
    # Stage 1: 故事大纲
    # ============================================================
    print(f"\n{'='*50}")
    print("Stage 1: 生成故事大纲")
    print(f"{'='*50}")

    stage1_start = time.time()
    outline_gen = StoryOutlineGenerator()
    outline = await outline_gen.generate(
        idea=STORY_IDEA,
        style_preset=STYLE_PRESET,
        target_duration_minutes=3,
        language="zh-CN",
        character_count=3
    )
    stage1_time = time.time() - stage1_start

    save_json(os.path.join(project_dir, "1_outline.json"), outline)
    print(f"✅ Stage 1 完成 ({stage1_time:.1f}s): {outline.get('title', 'N/A')}")

    # ============================================================
    # Stage 2: 角色设计
    # ============================================================
    print(f"\n{'='*50}")
    print("Stage 2: 设计角色")
    print(f"{'='*50}")

    stage2_start = time.time()
    char_designer = CharacterDesigner()
    characters = await char_designer.design(outline)
    stage2_time = time.time() - stage2_start

    save_json(os.path.join(project_dir, "2_characters.json"), characters)
    char_names = [c.get("name", "?") for c in characters.get("characters", [])]
    print(f"✅ Stage 2 完成 ({stage2_time:.1f}s): {', '.join(char_names)}")

    # ============================================================
    # Stage 3: 分场剧本
    # ============================================================
    print(f"\n{'='*50}")
    print("Stage 3: 编写分场剧本")
    print(f"{'='*50}")

    stage3_start = time.time()
    screenplay_writer = ScreenplayWriter()
    screenplay = await screenplay_writer.write(outline, characters)
    stage3_time = time.time() - stage3_start

    save_json(os.path.join(project_dir, "3_screenplay.json"), screenplay)
    scene_count = len(screenplay.get("scenes", []))
    print(f"✅ Stage 3 完成 ({stage3_time:.1f}s): {scene_count} 场戏")

    # ============================================================
    # Stage 4: 分镜脚本
    # ============================================================
    print(f"\n{'='*50}")
    print("Stage 4: 创建分镜脚本")
    print(f"{'='*50}")

    stage4_start = time.time()
    storyboard_director = StoryboardDirector()
    visual_tone = outline.get("visual_tone", {})
    storyboard = await storyboard_director.direct(
        screenplay=screenplay,
        characters=characters,
        visual_tone=visual_tone,
        style_preset=STYLE_PRESET
    )
    stage4_time = time.time() - stage4_start

    save_json(os.path.join(project_dir, "4_storyboard.json"), storyboard)
    shot_count = len(storyboard.get("shots", []))
    print(f"✅ Stage 4 完成 ({stage4_time:.1f}s): {shot_count} 个镜头")

    # ============================================================
    # text_type 分布分析 (DIALOGUE-SYSTEM 首次真实 E2E 验证)
    # ============================================================
    print(f"\n{'='*50}")
    print("text_type 分布分析 (DIALOGUE-SYSTEM 验证)")
    print(f"{'='*50}")

    text_dist = analyze_text_type_distribution(storyboard)

    print(f"  总镜头数: {text_dist['total_shots']}")
    print(f"  各类型分布:")
    for t, c in sorted(text_dist["type_counts"].items(), key=lambda x: -x[1]):
        pct = c / text_dist["total_shots"] * 100
        print(f"    {t}: {c} ({pct:.1f}%)")
    print()
    print(f"  dialogue 家族 (含混合): {text_dist['dialogue_family_count']} ({text_dist['dialogue_family_pct']}%)")
    print(f"    >= 60%? {'PASS' if text_dist['dialogue_ge_60'] else 'FAIL'}")
    print(f"  narration 家族 (纯叙述): {text_dist['narration_family_count']} ({text_dist['narration_family_pct']}%)")
    print(f"    <= 10%? {'PASS' if text_dist['narration_le_10'] else 'FAIL'}")
    print(f"  none 类型: {text_dist['none_count']}")
    print(f"    = 0? {'PASS' if text_dist['none_eq_0'] else 'FAIL'}")

    save_json(os.path.join(project_dir, "text_type_distribution.json"), text_dist)

    # ============================================================
    # Stage 5a: 生成参考图 (角色 + 场景, 只跑一次)
    # ============================================================
    print(f"\n{'='*50}")
    print("Stage 5a: 生成参考图 (角色 + 场景)")
    print(f"{'='*50}")

    refs_start = time.time()
    image_generator = ImageGenerator()
    project_style = ProjectStyleConfig(style_preset=STYLE_PRESET)

    # 角色参考图
    print("\n--- 角色参考图 ---")
    ref_manager = ReferenceImageManager()
    char_list = characters.get("characters", [])

    for char in char_list:
        char_name = char.get("name", char.get("id", "unknown"))
        print(f"  生成 {char_name} 参考图...", end=" ")
        try:
            await ref_manager.generate_character_multi_refs(
                character=char,
                project_style=project_style,
                image_generator=image_generator
            )
            print("OK")
        except Exception as e:
            print(f"FAIL: {e}")

    char_refs_dir = os.path.join(project_dir, "character_refs")
    os.makedirs(char_refs_dir, exist_ok=True)
    ref_manager.save_all_references(char_refs_dir)
    print(f"  角色参考图已保存: {char_refs_dir}")

    # 场景参考图
    print("\n--- 场景参考图 ---")
    unique_locations = outline.get("unique_locations", [])
    scene_ref_manager = None

    if unique_locations:
        scene_ref_manager = SceneReferenceManager()
        print(f"  共 {len(unique_locations)} 个场景位置")

        try:
            scene_anchors = await scene_ref_manager.generate_anchor_images(
                scenes=[],
                project_style=project_style,
                image_generator=image_generator,
                unique_locations=unique_locations,
                delay=3.0
            )

            scene_refs_dir = os.path.join(project_dir, "scene_refs")
            os.makedirs(scene_refs_dir, exist_ok=True)
            for anchor_key, anchor_data in scene_anchors.items():
                img = anchor_data.get('image')
                if img:
                    img.save(os.path.join(scene_refs_dir, f"{anchor_key}.png"))

            print(f"  场景参考图已保存: {len(scene_anchors)} 张 → {scene_refs_dir}")
        except Exception as e:
            print(f"  场景参考图失败: {e}")
            scene_ref_manager = None
    else:
        print("  无 unique_locations, 跳过场景参考图")

    refs_time = time.time() - refs_start
    print(f"\n  参考图生成总耗时: {refs_time:.1f}s")

    # ============================================================
    # 保存 A/B style_description 对比文件
    # ============================================================
    desc_compare_path = os.path.join(project_dir, "style_description_comparison.txt")
    with open(desc_compare_path, 'w', encoding='utf-8') as f:
        f.write("=== TASK-CROSS-STYLE-TEST: style_description A/B 对比 ===\n\n")
        f.write("--- A 组: 命令式 (Command Style) ---\n")
        f.write(STYLE_DESC_A + "\n\n")
        f.write("--- B 组: 场域式 (Field Style) ---\n")
        f.write(STYLE_DESC_B + "\n\n")
        f.write("--- 控制变量 (两组相同) ---\n")
        enforcement = StyleEnforcer.STYLE_ENFORCEMENTS[STYLE_PRESET]
        f.write(f"mandatory_keywords: {enforcement.mandatory_keywords}\n")
        f.write(f"forbidden_keywords: {enforcement.forbidden_keywords}\n")
        f.write(f"quality_keywords: {enforcement.quality_keywords}\n")

    # ============================================================
    # Stage 5b-A: 生成 shots — A 组 (命令式)
    # ============================================================
    shots = storyboard.get("shots", [])

    group_a_dir = os.path.join(project_dir, "group_a_command")
    group_b_dir = os.path.join(project_dir, "group_b_field")
    os.makedirs(group_a_dir, exist_ok=True)
    os.makedirs(group_b_dir, exist_ok=True)

    print(f"\n{'='*50}")
    print(f"Stage 5b-A: A 组 (命令式) — {len(shots)} shots")
    print(f"{'='*50}")

    stage5a_start = time.time()
    a_results = await generate_all_shots(
        group_name="A组 命令式",
        style_desc=STYLE_DESC_A,
        shots=shots,
        storyboard=storyboard,
        characters=characters,
        screenplay=screenplay,
        image_generator=image_generator,
        ref_manager=ref_manager,
        scene_ref_manager=scene_ref_manager,
        unique_locations=unique_locations,
        output_dir=group_a_dir
    )
    stage5a_time = time.time() - stage5a_start

    a_success = sum(1 for r in a_results if r.get("success"))
    print(f"\n  A 组完成: {a_success}/{len(shots)} 成功, {stage5a_time:.1f}s")

    # ============================================================
    # Stage 5b-B: 生成 shots — B 组 (场域式)
    # ============================================================
    print(f"\n{'='*50}")
    print(f"Stage 5b-B: B 组 (场域式) — {len(shots)} shots")
    print(f"{'='*50}")

    stage5b_start = time.time()
    b_results = await generate_all_shots(
        group_name="B组 场域式",
        style_desc=STYLE_DESC_B,
        shots=shots,
        storyboard=storyboard,
        characters=characters,
        screenplay=screenplay,
        image_generator=image_generator,
        ref_manager=ref_manager,
        scene_ref_manager=scene_ref_manager,
        unique_locations=unique_locations,
        output_dir=group_b_dir
    )
    stage5b_time = time.time() - stage5b_start

    b_success = sum(1 for r in b_results if r.get("success"))
    print(f"\n  B 组完成: {b_success}/{len(shots)} 成功, {stage5b_time:.1f}s")

    # ============================================================
    # 汇总
    # ============================================================
    end_time = datetime.now()
    total_duration = (end_time - total_start).total_seconds()

    a_times = [r["generation_time"] for r in a_results if r.get("success")]
    b_times = [r["generation_time"] for r in b_results if r.get("success")]

    summary = {
        "task": "TASK-CROSS-STYLE-TEST",
        "project_id": project_id,
        "project_dir": project_dir,
        "story_idea": STORY_IDEA,
        "story_title": outline.get("title", ""),
        "model": "gemini-3.1-flash-image-preview (NB2)",
        "style_preset": STYLE_PRESET,
        "use_native_text": True,
        "total_shots": len(shots),
        "characters": char_names,
        "stage_times": {
            "stage1_outline": round(stage1_time, 2),
            "stage2_characters": round(stage2_time, 2),
            "stage3_screenplay": round(stage3_time, 2),
            "stage4_storyboard": round(stage4_time, 2),
            "stage5_refs": round(refs_time, 2),
            "stage5a_group_a": round(stage5a_time, 2),
            "stage5b_group_b": round(stage5b_time, 2)
        },
        "text_type_distribution": text_dist,
        "group_a": {
            "name": "命令式 (Command Style)",
            "style_description": STYLE_DESC_A,
            "success_count": a_success,
            "total_count": len(shots),
            "avg_generation_time": round(sum(a_times) / len(a_times), 2) if a_times else 0,
            "results": a_results
        },
        "group_b": {
            "name": "场域式 (Field Style)",
            "style_description": STYLE_DESC_B,
            "success_count": b_success,
            "total_count": len(shots),
            "avg_generation_time": round(sum(b_times) / len(b_times), 2) if b_times else 0,
            "results": b_results
        },
        "total_duration_seconds": round(total_duration, 2),
        "timestamp": end_time.isoformat()
    }

    save_json(os.path.join(project_dir, "cross_style_test_results.json"), summary)

    # 打印汇总
    print(f"\n{'='*70}")
    print("TASK-CROSS-STYLE-TEST 完成!")
    print(f"{'='*70}")
    print(f"  故事: {outline.get('title', '?')}")
    print(f"  角色: {', '.join(char_names)}")
    print(f"  总镜头: {len(shots)}")
    print()
    print(f"  --- text_type 分布 (DIALOGUE-SYSTEM) ---")
    for t, c in sorted(text_dist["type_counts"].items(), key=lambda x: -x[1]):
        pct = c / text_dist["total_shots"] * 100
        print(f"    {t}: {c} ({pct:.1f}%)")
    print(f"    dialogue家族: {text_dist['dialogue_family_pct']}% {'PASS' if text_dist['dialogue_ge_60'] else 'FAIL'} (>=60%)")
    print(f"    narration家族: {text_dist['narration_family_pct']}% {'PASS' if text_dist['narration_le_10'] else 'FAIL'} (<=10%)")
    print(f"    none: {text_dist['none_count']} {'PASS' if text_dist['none_eq_0'] else 'FAIL'} (=0)")
    print()
    print(f"  --- A/B 组生成结果 ---")
    print(f"    A组 (命令式): {a_success}/{len(shots)} 成功, 平均 {summary['group_a']['avg_generation_time']:.1f}s/张")
    print(f"    B组 (场域式): {b_success}/{len(shots)} 成功, 平均 {summary['group_b']['avg_generation_time']:.1f}s/张")
    if a_times and b_times:
        speed_diff = (summary['group_b']['avg_generation_time'] / summary['group_a']['avg_generation_time'] - 1) * 100
        print(f"    速度差异: B组比A组{'慢' if speed_diff > 0 else '快'} {abs(speed_diff):.0f}%")
    print()
    print(f"  --- 耗时明细 ---")
    print(f"    Stage 1 大纲:     {stage1_time:.1f}s")
    print(f"    Stage 2 角色:     {stage2_time:.1f}s")
    print(f"    Stage 3 剧本:     {stage3_time:.1f}s")
    print(f"    Stage 4 分镜:     {stage4_time:.1f}s")
    print(f"    Stage 5 参考图:   {refs_time:.1f}s")
    print(f"    Stage 5 A组:      {stage5a_time:.1f}s")
    print(f"    Stage 5 B组:      {stage5b_time:.1f}s")
    print(f"    总耗时:           {total_duration:.1f}s ({total_duration/60:.1f}min)")
    print()
    print(f"  输出目录: {project_dir}/")
    print(f"    group_a_command/  — A组 (命令式)")
    print(f"    group_b_field/   — B组 (场域式)")
    print(f"    character_refs/  — 角色参考图")
    print(f"    scene_refs/      — 场景参考图")
    print(f"{'='*70}")

    return summary


if __name__ == "__main__":
    asyncio.run(run_cross_style_test())
