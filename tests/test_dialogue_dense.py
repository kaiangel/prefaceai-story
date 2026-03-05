"""
TASK-DIALOGUE-DENSE-TEST: 家庭晚餐争吵 E2E 测试 — DIALOGUE-SYSTEM 验证

验证 DIALOGUE-SYSTEM 在对话密集型题材中的表现:
- 上轮暗恋题材 dialogue 家族仅 28.1% (EXPECTED FAIL)
- 本轮家庭争吵题材应大幅提升 (目标 >=60%)
- 区分 "题材结构性" vs "SELF-CHECK 机制不足"

测试参数 (PM 指定, 无歧义):
  - 故事: 年夜饭三代人争吵
  - 风格: illustration + 场域式 B 组 style_description
  - 模型: Stage 1-4 Sonnet 4.6 / Stage 5 NB2
  - 文字渲染: NB2 原生 (use_native_text=True)
  - 宽高比: 2:3
  - 规模: 32 shots (中篇)

7 项验收指标:
  1. dialogue 占比 >= 60%
  2. text_type 完整分布
  3. 角色一致性 >= 90% (3代人外貌区分+一致性)
  4. NB2 文字渲染 >= 80% 可读
  5. 场景连续性 (同一餐桌环境)
  6. 情感表达 (争吵氛围)
  7. 完整性 32/32 shots

作者: @Tester
日期: 2026-03-02
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
OUTPUT_BASE = "./test_output/manualtest/dialogue_dense_test"
STYLE_PRESET = "illustration"

# 故事 idea — 家庭晚餐争吵 (Founder 指定: 对话密集型, 三代人观念冲突)
STORY_IDEA = (
    "年夜饭上，爷爷坚持孙子必须考公务员，父亲想让儿子接管家族生意，"
    "而22岁的孙子只想辞职去做独立游戏开发。三代人的晚餐从敬酒变成了激烈争吵。"
)

# 场域式 style_description (AI-ML 提供, PM 核验通过, Founder 确认方向)
# 在测试脚本中 override, 不改 style_enforcer.py 代码
STYLE_DESC_FIELD = (
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
    PM 验收标准: dialogue(含混合) >= 60%, narration <= 30%, thought <= 15%, none 5-10%
    """
    shots = storyboard.get("shots", [])
    total = len(shots)

    type_counts = {}
    dialogue_family = 0   # dialogue + dialogue_with_thought + dialogue_with_narration + narration_with_dialogue
    narration_family = 0  # narration + narration_with_thought (不含含 dialogue 的混合类型)
    thought_count = 0     # thought (纯内心独白)
    none_count = 0

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
        # thought: 纯内心独白
        elif text_type == "thought":
            thought_count += 1
        # none
        elif text_type == "none":
            none_count += 1

    dialogue_pct = (dialogue_family / total * 100) if total > 0 else 0
    narration_pct = (narration_family / total * 100) if total > 0 else 0
    thought_pct = (thought_count / total * 100) if total > 0 else 0
    none_pct = (none_count / total * 100) if total > 0 else 0

    return {
        "total_shots": total,
        "type_counts": type_counts,
        "dialogue_family_count": dialogue_family,
        "dialogue_family_pct": round(dialogue_pct, 1),
        "narration_family_count": narration_family,
        "narration_family_pct": round(narration_pct, 1),
        "thought_count": thought_count,
        "thought_pct": round(thought_pct, 1),
        "none_count": none_count,
        "none_pct": round(none_pct, 1),
        "dialogue_ge_60": dialogue_pct >= 60,
        "narration_le_30": narration_pct <= 30,
        "thought_le_15": thought_pct <= 15,
        "none_5_10": 5 <= none_pct <= 10 if total > 0 else False
    }


def get_location_id_for_scene(
    scene_id: int,
    screenplay: dict,
    unique_locations: list
) -> Optional[str]:
    """从 scene_id 获取 location_id"""
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

    for loc in unique_locations:
        if loc.get("location_id") == screenplay_location_id:
            return screenplay_location_id

    if unique_locations:
        return unique_locations[0].get("location_id")

    return screenplay_location_id


# =========== Shot 生成 ===========

async def generate_all_shots(
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
    生成所有 shots (完整 Stage 5)
    临时覆盖 style_description 为场域式, 生成完恢复
    """
    results = []

    # 临时覆盖 style_description (仅改 style_description, mandatory/forbidden 不动)
    original_desc = StyleEnforcer.STYLE_ENFORCEMENTS[STYLE_PRESET].style_description
    StyleEnforcer.STYLE_ENFORCEMENTS[STYLE_PRESET].style_description = STYLE_DESC_FIELD

    previous_shot_image = None
    previous_shot = None

    try:
        for i, shot in enumerate(shots):
            shot_id = shot.get("shot_id", i + 1)
            text_type = shot.get("text_overlay", {}).get("text_type", "none")

            print(f"\n  Shot {shot_id:02d}/{len(shots)} ({text_type})...")

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

async def run_dialogue_dense_test():
    """运行 TASK-DIALOGUE-DENSE-TEST 完整 E2E 测试"""
    total_start = datetime.now()
    project_id = total_start.strftime("%Y%m%d_%H%M%S")
    project_dir = os.path.join(OUTPUT_BASE, project_id)
    os.makedirs(project_dir, exist_ok=True)

    print("=" * 70)
    print("TASK-DIALOGUE-DENSE-TEST: 家庭晚餐争吵 E2E 测试")
    print("=" * 70)
    print(f"Project ID: {project_id}")
    print(f"Story idea: {STORY_IDEA}")
    print(f"Style: {STYLE_PRESET} (场域式)")
    print(f"Model: Stage 1-4 Sonnet 4.6 / Stage 5 NB2")
    print(f"use_native_text: True")
    print(f"Output: {project_dir}")
    print(f"核心指标: dialogue 家族 >= 60%")
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
    char_list = characters.get("characters", [])
    char_names = [c.get("name", "?") for c in char_list]
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
    # text_type 分布分析 (DIALOGUE-SYSTEM 核心验证)
    # ============================================================
    print(f"\n{'='*50}")
    print("text_type 分布分析 (DIALOGUE-SYSTEM 核心验证)")
    print(f"{'='*50}")

    text_dist = analyze_text_type_distribution(storyboard)

    print(f"  总镜头数: {text_dist['total_shots']}")
    print(f"  各类型分布:")
    for t, c in sorted(text_dist["type_counts"].items(), key=lambda x: -x[1]):
        pct = c / text_dist["total_shots"] * 100
        print(f"    {t}: {c} ({pct:.1f}%)")
    print()
    print(f"  dialogue 家族 (含混合): {text_dist['dialogue_family_count']} ({text_dist['dialogue_family_pct']}%)")
    print(f"    >= 60%? {'✅ PASS' if text_dist['dialogue_ge_60'] else '❌ FAIL'}")
    print(f"  narration 家族 (纯叙述): {text_dist['narration_family_count']} ({text_dist['narration_family_pct']}%)")
    print(f"    <= 30%? {'✅ PASS' if text_dist['narration_le_30'] else '❌ FAIL'}")
    print(f"  thought (纯内心独白): {text_dist['thought_count']} ({text_dist['thought_pct']}%)")
    print(f"    <= 15%? {'✅ PASS' if text_dist['thought_le_15'] else '❌ FAIL'}")
    print(f"  none: {text_dist['none_count']} ({text_dist['none_pct']}%)")

    save_json(os.path.join(project_dir, "text_type_distribution.json"), text_dist)

    # ============================================================
    # 逐 shot text_type 明细
    # ============================================================
    print(f"\n  --- 逐 shot text_type 明细 ---")
    shots = storyboard.get("shots", [])
    shot_text_types = []
    for shot in shots:
        sid = shot.get("shot_id", "?")
        text_overlay = shot.get("text_overlay", {})
        tt = text_overlay.get("text_type", "none")
        chinese_text = text_overlay.get("chinese_text", "")
        # 截取前30字
        text_preview = ""
        if isinstance(chinese_text, str):
            text_preview = chinese_text[:30]
        elif isinstance(chinese_text, list):
            text_preview = str(chinese_text[0])[:30] if chinese_text else ""
        print(f"    Shot {sid:02d}: {tt:30s} | {text_preview}...")
        shot_text_types.append({"shot_id": sid, "text_type": tt, "text_preview": text_preview})

    save_json(os.path.join(project_dir, "shot_text_types.json"), shot_text_types)

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
    # Stage 5b: 生成所有 shots (场域式)
    # ============================================================
    print(f"\n{'='*50}")
    print(f"Stage 5b: 生成 shots (场域式) — {shot_count} shots")
    print(f"{'='*50}")

    shots_dir = os.path.join(project_dir, "shots")
    os.makedirs(shots_dir, exist_ok=True)

    stage5_start = time.time()
    shot_results = await generate_all_shots(
        shots=shots,
        storyboard=storyboard,
        characters=characters,
        screenplay=screenplay,
        image_generator=image_generator,
        ref_manager=ref_manager,
        scene_ref_manager=scene_ref_manager,
        unique_locations=unique_locations,
        output_dir=shots_dir
    )
    stage5_time = time.time() - stage5_start

    success_count = sum(1 for r in shot_results if r.get("success"))
    gen_times = [r["generation_time"] for r in shot_results if r.get("success")]
    avg_time = sum(gen_times) / len(gen_times) if gen_times else 0

    print(f"\n  生成完成: {success_count}/{shot_count} 成功")
    print(f"  平均生图: {avg_time:.1f}s/张")
    print(f"  Stage 5 总耗时: {stage5_time:.1f}s")

    # ============================================================
    # 汇总
    # ============================================================
    end_time = datetime.now()
    total_duration = (end_time - total_start).total_seconds()

    summary = {
        "task": "TASK-DIALOGUE-DENSE-TEST",
        "project_id": project_id,
        "project_dir": project_dir,
        "story_idea": STORY_IDEA,
        "story_title": outline.get("title", ""),
        "model": {
            "stage_1_4": "Claude Sonnet 4.6",
            "stage_5": "gemini-3.1-flash-image-preview (NB2)"
        },
        "style_preset": STYLE_PRESET,
        "style_description": "场域式 (Field Style)",
        "use_native_text": True,
        "aspect_ratio": "2:3",
        "total_shots": shot_count,
        "characters": char_names,
        "stage_times": {
            "stage1_outline": round(stage1_time, 2),
            "stage2_characters": round(stage2_time, 2),
            "stage3_screenplay": round(stage3_time, 2),
            "stage4_storyboard": round(stage4_time, 2),
            "stage5_refs": round(refs_time, 2),
            "stage5_shots": round(stage5_time, 2)
        },
        "text_type_distribution": text_dist,
        "shot_results": {
            "success_count": success_count,
            "total_count": shot_count,
            "avg_generation_time": round(avg_time, 2),
            "results": shot_results
        },
        "total_duration_seconds": round(total_duration, 2),
        "total_duration_minutes": round(total_duration / 60, 1),
        "timestamp": end_time.isoformat()
    }

    save_json(os.path.join(project_dir, "dialogue_dense_test_results.json"), summary)

    # 打印汇总
    print(f"\n{'='*70}")
    print("TASK-DIALOGUE-DENSE-TEST 完成!")
    print(f"{'='*70}")
    print(f"  故事: {outline.get('title', '?')}")
    print(f"  角色: {', '.join(char_names)}")
    print(f"  总镜头: {shot_count}")
    print()
    print(f"  --- DIALOGUE-SYSTEM 核心指标 ---")
    for t, c in sorted(text_dist["type_counts"].items(), key=lambda x: -x[1]):
        pct = c / text_dist["total_shots"] * 100
        print(f"    {t}: {c} ({pct:.1f}%)")
    print(f"    dialogue家族: {text_dist['dialogue_family_pct']}% {'✅ PASS' if text_dist['dialogue_ge_60'] else '❌ FAIL'} (>=60%)")
    print(f"    narration家族: {text_dist['narration_family_pct']}% {'✅ PASS' if text_dist['narration_le_30'] else '❌ FAIL'} (<=30%)")
    print(f"    thought: {text_dist['thought_pct']}% {'✅ PASS' if text_dist['thought_le_15'] else '❌ FAIL'} (<=15%)")
    print(f"    none: {text_dist['none_count']} ({text_dist['none_pct']}%)")
    print()
    print(f"  --- 生成结果 ---")
    print(f"    成功: {success_count}/{shot_count}")
    print(f"    平均生图: {avg_time:.1f}s/张")
    print()
    print(f"  --- 耗时明细 ---")
    print(f"    Stage 1 大纲:     {stage1_time:.1f}s")
    print(f"    Stage 2 角色:     {stage2_time:.1f}s")
    print(f"    Stage 3 剧本:     {stage3_time:.1f}s")
    print(f"    Stage 4 分镜:     {stage4_time:.1f}s")
    print(f"    Stage 5 参考图:   {refs_time:.1f}s")
    print(f"    Stage 5 shots:    {stage5_time:.1f}s")
    print(f"    总耗时:           {total_duration:.1f}s ({total_duration/60:.1f}min)")
    print()
    print(f"  输出目录: {project_dir}/")
    print(f"    shots/           — 生成的 shot 图片")
    print(f"    character_refs/  — 角色参考图")
    print(f"    scene_refs/      — 场景参考图")
    print(f"{'='*70}")

    return summary


if __name__ == "__main__":
    asyncio.run(run_dialogue_dense_test())
