"""
TASK-SHOT-QUALITY-BUGFIX 回归验证

验证 4 个 Bug 修复 + SQ-1~SQ-8 改进未回退。
参数与 Step 7 B 组完全相同。

4 Bug 专项验证:
  Bug #1 (P1): 场景标签 — 应为英文 (如 "Scene: loc_001 Interior"), 无 □ 方块
  Bug #2 (P2): Prompt 指令泄漏 — shot 图中无 "opacity"/"px" 文字
  Bug #3 (P2): 神秘路人 — 路人出现率从 25% (6/24) 显著下降, 目标 ≤ 1/24
  Bug #4 (P3): Validator 字段名 — "consecutive eye_level" 假阳性从 22/35 显著下降

7 维度常规验证 (SQ 改进未回退):
  综合评分 ≥ 4.0/5

作者: @Tester
日期: 2026-03-04
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
from app.services.storyboard_service import validate_shot_transitions
from app.models.style_config import ProjectStyleConfig


# =========== 配置 ===========
OUTPUT_BASE = "./test_output/manualtest/bugfix_regression"
STYLE_PRESET = "illustration"

# 设置 RESUME_DIR 为已有输出目录，跳过 Stage 1-4，仅重跑 Stage 5 (shots)
# 设为 None 则全部重跑
RESUME_DIR = "./test_output/manualtest/bugfix_regression/20260304_162910"

# 与 Step 7 B 组完全相同的 idea
STORY_IDEA = (
    "年夜饭上，爷爷坚持孙子必须考公务员，父亲想让儿子接管家族生意，"
    "而22岁的孙子只想辞职去做独立游戏开发。三代人的晚餐从敬酒变成了激烈争吵。"
)

# Step 7 B 组结果 (用于对比)
STEP7_B_SCORES = {
    "overall": 4.27,
    "dim1_dialogue": 4.5,
    "dim2_props": 4.5,
    "dim3_depth": 4.0,
    "dim4_camera": 4.5,
    "dim6_continuity": 3.8,
    "dim7_consistency": 4.3,
    "bystander_rate": 0.25,  # 6/24 = 25%
    "validator_eye_level_false_positives": 22,
}


# =========== 工具函数 ===========

def load_json(filepath: str) -> dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(filepath: str, data) -> None:
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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


def analyze_camera_diversity(shots: list, group_label: str) -> dict:
    """分析运镜多样性"""
    total = len(shots)
    if total == 0:
        return {"consecutive_same_size": 0, "consecutive_same_angle": 0, "unique_sizes": 0, "unique_angles": 0}

    shot_sizes = []
    camera_angles = []
    for shot in shots:
        camera = shot.get("camera", {})
        size = camera.get("shot_size") or shot.get("shot_type", "unknown")
        angle = camera.get("angle") or camera.get("camera_angle", "unknown")
        shot_sizes.append(size)
        camera_angles.append(angle)

    unique_sizes = len(set(shot_sizes))
    unique_angles = len(set(camera_angles))

    consecutive_same_size = 0
    for i in range(2, total):
        if shot_sizes[i] == shot_sizes[i-1] == shot_sizes[i-2]:
            consecutive_same_size += 1

    consecutive_same_angle = 0
    for i in range(2, total):
        if camera_angles[i] == camera_angles[i-1] == camera_angles[i-2]:
            consecutive_same_angle += 1

    size_dist = {}
    for s in shot_sizes:
        size_dist[s] = size_dist.get(s, 0) + 1

    angle_dist = {}
    for a in camera_angles:
        angle_dist[a] = angle_dist.get(a, 0) + 1

    print(f"\n  {group_label} 运镜分析:")
    print(f"    景别种类: {unique_sizes}, 分布: {size_dist}")
    print(f"    角度种类: {unique_angles}, 分布: {angle_dist}")
    print(f"    3+连续相同景别: {consecutive_same_size} 次")
    print(f"    3+连续相同角度: {consecutive_same_angle} 次")

    return {
        "unique_sizes": unique_sizes,
        "unique_angles": unique_angles,
        "consecutive_same_size": consecutive_same_size,
        "consecutive_same_angle": consecutive_same_angle,
        "size_distribution": size_dist,
        "angle_distribution": angle_dist,
        "shot_sizes": shot_sizes,
        "camera_angles": camera_angles
    }


def check_sq5_fields(shots: list) -> dict:
    """检查 SQ-5 新增 JSON 字段"""
    has_focal = 0
    has_fg = 0
    has_bg = 0
    has_depth = 0
    total = len(shots)

    for shot in shots:
        camera = shot.get("camera", {})
        composition = shot.get("composition", {})
        if camera.get("focal_length"):
            has_focal += 1
        if composition.get("foreground"):
            has_fg += 1
        if composition.get("background"):
            has_bg += 1
        if composition.get("depth_layers"):
            has_depth += 1

    return {
        "has_focal_length": f"{has_focal}/{total}",
        "has_foreground": f"{has_fg}/{total}",
        "has_background": f"{has_bg}/{total}",
        "has_depth_layers": f"{has_depth}/{total}",
        "focal_count": has_focal,
        "foreground_count": has_fg,
        "background_count": has_bg,
        "depth_count": has_depth
    }


def analyze_bug4_validator(transition_warnings: list) -> dict:
    """Bug #4 专项: 分析 Validator 中 eye_level 假阳性"""
    total = len(transition_warnings)
    eye_level_warnings = [w for w in transition_warnings if "eye_level" in str(w).lower()]
    other_warnings = [w for w in transition_warnings if "eye_level" not in str(w).lower()]

    return {
        "total_warnings": total,
        "eye_level_count": len(eye_level_warnings),
        "other_count": len(other_warnings),
        "step7_eye_level": STEP7_B_SCORES["validator_eye_level_false_positives"],
        "improved": len(eye_level_warnings) < STEP7_B_SCORES["validator_eye_level_false_positives"],
        "eye_level_warnings": eye_level_warnings,
        "other_warnings": other_warnings
    }


# =========== 回归测试主体 ===========

async def run_regression_test():
    """运行 TASK-SHOT-QUALITY-BUGFIX 回归验证"""
    total_start = datetime.now()

    # Resume 模式: 复用已有 Stage 1-4 输出, 仅重跑参考图 + shots
    resume_mode = RESUME_DIR is not None and os.path.isdir(RESUME_DIR)

    if resume_mode:
        project_dir = RESUME_DIR
        project_id = os.path.basename(RESUME_DIR)
        print("=" * 70)
        print("TASK-SHOT-QUALITY-BUGFIX 回归验证 (RESUME 模式)")
        print("=" * 70)
        print(f"复用 Stage 1-4 from: {RESUME_DIR}")
    else:
        project_id = total_start.strftime("%Y%m%d_%H%M%S")
        project_dir = os.path.join(OUTPUT_BASE, project_id)
        os.makedirs(project_dir, exist_ok=True)
        print("=" * 70)
        print("TASK-SHOT-QUALITY-BUGFIX 回归验证")
        print("=" * 70)

    print(f"Project ID: {project_id}")
    print(f"Story idea: {STORY_IDEA}")
    print(f"Style: {STYLE_PRESET} (场域式, 代码默认)")
    print(f"Model: Stage 1-4 Sonnet 4.6 / Stage 5 NB2")
    print(f"Output: {project_dir}")
    print(f"Bug fixes to verify: #1(场景标签) #2(指令泄漏) #3(路人) #4(Validator)")
    print("=" * 70)

    if resume_mode:
        # ============================================================
        # RESUME: 从已有 JSON 加载 Stage 1-4
        # ============================================================
        print(f"\n{'='*50}")
        print("RESUME: 加载已有 Stage 1-4 输出")
        print(f"{'='*50}")

        outline = load_json(os.path.join(project_dir, "1_outline.json"))
        print(f"  ✅ Stage 1 loaded: {outline.get('title', 'N/A')}")

        characters = load_json(os.path.join(project_dir, "2_characters.json"))
        char_list = characters.get("characters", [])
        char_names = [c.get("name", "?") for c in char_list]
        print(f"  ✅ Stage 2 loaded: {', '.join(char_names)}")

        screenplay = load_json(os.path.join(project_dir, "3_screenplay.json"))
        print(f"  ✅ Stage 3 loaded: {len(screenplay.get('scenes', []))} scenes")

        storyboard = load_json(os.path.join(project_dir, "4_storyboard.json"))
        print(f"  ✅ Stage 4 loaded: {len(storyboard.get('shots', []))} shots")

    else:
        # ============================================================
        # Stage 1: 故事大纲
        # ============================================================
        print(f"\n{'='*50}")
        print("Stage 1: 生成故事大纲")
        print(f"{'='*50}")

        stage1_start = time.time()
        outline_gen = StoryOutlineGenerator()
        outline = None
        for attempt in range(3):
            try:
                outline = await outline_gen.generate(
                    idea=STORY_IDEA,
                    style_preset=STYLE_PRESET,
                    target_duration_minutes=3,
                    language="zh-CN",
                    character_count=3
                )
                break
            except ValueError as e:
                print(f"  ⚠️ Stage 1 尝试 {attempt+1}/3 失败: {e}")
                if attempt < 2:
                    await asyncio.sleep(5)
        if outline is None:
            raise RuntimeError("Stage 1 连续 3 次失败")
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
        characters = None
        for attempt in range(3):
            try:
                characters = await char_designer.design(outline)
                break
            except (ValueError, Exception) as e:
                print(f"  ⚠️ Stage 2 尝试 {attempt+1}/3 失败: {e}")
                if attempt < 2:
                    await asyncio.sleep(5)
        if characters is None:
            raise RuntimeError("Stage 2 连续 3 次失败")
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
        screenplay = None
        for attempt in range(3):
            try:
                screenplay = await screenplay_writer.write(outline, characters)
                break
            except (ValueError, Exception) as e:
                print(f"  ⚠️ Stage 3 尝试 {attempt+1}/3 失败: {e}")
                if attempt < 2:
                    await asyncio.sleep(5)
        if screenplay is None:
            raise RuntimeError("Stage 3 连续 3 次失败")
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
        storyboard = None
        for attempt in range(3):
            try:
                storyboard = await storyboard_director.direct(
                    screenplay=screenplay,
                    characters=characters,
                    visual_tone=visual_tone,
                    style_preset=STYLE_PRESET
                )
                break
            except (ValueError, Exception) as e:
                print(f"  ⚠️ Stage 4 尝试 {attempt+1}/3 失败: {e}")
                if attempt < 2:
                    await asyncio.sleep(5)
        if storyboard is None:
            raise RuntimeError("Stage 4 连续 3 次失败")
        stage4_time = time.time() - stage4_start

        save_json(os.path.join(project_dir, "4_storyboard.json"), storyboard)
        print(f"✅ Stage 4 完成 ({stage4_time:.1f}s)")

    shots = storyboard.get("shots", [])
    shot_count = len(shots)
    print(f"  Storyboard: {shot_count} shots")

    # ============================================================
    # SQ-5 新字段检查
    # ============================================================
    sq5_fields = check_sq5_fields(shots)
    print(f"\n  SQ-5 新字段检查:")
    print(f"    focal_length: {sq5_fields['has_focal_length']}")
    print(f"    foreground:    {sq5_fields['has_foreground']}")
    print(f"    background:    {sq5_fields['has_background']}")
    print(f"    depth_layers:  {sq5_fields['has_depth_layers']}")

    # ============================================================
    # Bug #4 专项: SQ-6 运镜过渡验证
    # ============================================================
    print(f"\n  Bug #4 专项 — SQ-6 运镜过渡验证:")
    transition_warnings = validate_shot_transitions(shots)
    bug4_analysis = analyze_bug4_validator(transition_warnings)
    print(f"    总 warnings: {bug4_analysis['total_warnings']}")
    print(f"    eye_level 假阳性: {bug4_analysis['eye_level_count']} (Step 7: {bug4_analysis['step7_eye_level']})")
    print(f"    其他 warnings: {bug4_analysis['other_count']}")
    print(f"    Bug #4 改善: {'✅ YES' if bug4_analysis['improved'] else '❌ NO'}")
    if transition_warnings:
        for w in transition_warnings:
            print(f"      - {w}")

    # ============================================================
    # Stage 5a: 生成参考图
    # ============================================================
    print(f"\n{'='*50}")
    print("Stage 5a: 生成参考图")
    print(f"{'='*50}")

    refs_start = time.time()
    image_generator = ImageGenerator()
    project_style = ProjectStyleConfig(style_preset=STYLE_PRESET)

    # 角色参考图
    print("\n--- 角色参考图 ---")
    ref_manager = ReferenceImageManager()

    for char in char_list:
        char_name = char.get("name", char.get("id", "unknown"))
        print(f"  生成 {char_name} 参考图...", end=" ", flush=True)
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
    # Bug #1 专项: 参考图标签验证
    # ============================================================
    print(f"\n  Bug #1 专项 — 参考图标签检查:")
    test_char_ids = [c.get("id") for c in char_list if c.get("id")]
    if test_char_ids:
        smart_refs = ref_manager.get_smart_references_for_scene(test_char_ids, "medium_shot")
        print(f"    角色 smart_refs: {len(smart_refs)} 张 (SQ-2: 每角色 1 张)")

        labeled_refs_dir = os.path.join(project_dir, "labeled_refs")
        os.makedirs(labeled_refs_dir, exist_ok=True)
        for idx, ref_img in enumerate(smart_refs):
            ref_img.save(os.path.join(labeled_refs_dir, f"smart_ref_{idx+1}.png"))
        print(f"    标注后参考图已保存: {labeled_refs_dir}/")

    # 场景参考图标签检查 — Bug #1 核心验证点
    if scene_ref_manager and unique_locations:
        print(f"    场景标签检查:")
        for loc in unique_locations:
            loc_id = loc.get("location_id")
            if loc_id:
                scene_refs_labeled = scene_ref_manager.get_references_for_location(loc_id)
                print(f"      {loc_id}: {len(scene_refs_labeled)} 张参考图 (标签应为英文)")
                # 保存带标签的场景参考图
                for idx, sref in enumerate(scene_refs_labeled):
                    sref.save(os.path.join(labeled_refs_dir, f"scene_labeled_{loc_id}_{idx+1}.png"))

    # ============================================================
    # Stage 5b: 生成所有 shots
    # ============================================================
    print(f"\n{'='*50}")
    print(f"Stage 5b: 生成 shots — {shot_count} shots")
    print(f"{'='*50}")

    shots_dir = os.path.join(project_dir, "shots")
    # Resume 模式: 清空旧 shots, 重新生成
    if resume_mode and os.path.isdir(shots_dir):
        import shutil
        shutil.rmtree(shots_dir)
        print("  (旧 shots 已清空)")
    os.makedirs(shots_dir, exist_ok=True)

    stage5_start = time.time()
    shot_results = []

    for i, shot in enumerate(shots):
        shot_id = shot.get("shot_id", i + 1)
        text_type = shot.get("text_overlay", {}).get("text_type", "none")

        print(f"\n  Shot {shot_id:02d}/{shot_count} ({text_type})...", flush=True)

        # SQ-2: 智能参考图选择
        char_direction = shot.get("character_direction", {})
        chars_in_scene = char_direction.get("characters_visible", [])
        shot_type = shot.get("camera", {}).get("shot_size", "medium_shot")
        char_refs = ref_manager.get_smart_references_for_scene(chars_in_scene, shot_type)

        # 场景参考图
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
        shot_result = {
            "shot_id": shot_id,
            "text_type": text_type,
            "chars_in_scene": chars_in_scene,
            "char_refs_count": len(char_refs),
            "scene_refs_count": len(scene_refs),
            "shot_type": shot_type,
            "success": False,
            "generation_time": 0.0
        }

        try:
            # SQ-8 (DEC-014): 不传 previous_shot_image / previous_shot
            result = await image_generator.generate_shot_image_phase2(
                shot=shot,
                storyboard=storyboard,
                characters=characters,
                style_preset=STYLE_PRESET,
                reference_images=all_refs,
                screenplay=screenplay,
                aspect_ratio="2:3",
                use_native_text=True
            )
            gen_time = time.time() - gen_start
            shot_result["generation_time"] = round(gen_time, 2)

            if result.get("success"):
                img = result["pil_image"]
                img_path = os.path.join(shots_dir, f"shot_{shot_id:02d}.png")
                img.save(img_path)
                shot_result["success"] = True
                shot_result["size"] = f"{img.size[0]}x{img.size[1]}"
                shot_result["image_path"] = img_path
                print(f"    ✅ ({gen_time:.1f}s, {img.size[0]}x{img.size[1]}, "
                      f"char_refs={len(char_refs)}, scene_refs={len(scene_refs)})")
            else:
                shot_result["error"] = result.get("error", "Unknown")
                print(f"    ❌ {shot_result['error']}")
        except Exception as e:
            gen_time = time.time() - gen_start
            shot_result["generation_time"] = round(gen_time, 2)
            shot_result["error"] = f"CRASH: {type(e).__name__}: {str(e)}"
            print(f"    💥 CRASH: {type(e).__name__}: {e}")

        shot_results.append(shot_result)
        await asyncio.sleep(2)

    stage5_time = time.time() - stage5_start

    success_count = sum(1 for r in shot_results if r.get("success"))
    gen_times = [r["generation_time"] for r in shot_results if r.get("success")]
    avg_time = sum(gen_times) / len(gen_times) if gen_times else 0

    print(f"\n  生成完成: {success_count}/{shot_count} 成功")
    print(f"  平均生图: {avg_time:.1f}s/张")
    print(f"  Stage 5 总耗时: {stage5_time:.1f}s")

    # 运镜分析
    camera_analysis = analyze_camera_diversity(shots, "Regression")

    # ============================================================
    # 汇总
    # ============================================================
    end_time = datetime.now()
    total_duration = (end_time - total_start).total_seconds()

    print(f"\n{'='*70}")
    print("回归验证生成完成!")
    print(f"{'='*70}")
    print(f"  Shots: {success_count}/{shot_count} 成功")
    print(f"  角色: {', '.join(char_names)}")
    print(f"  平均生图: {avg_time:.1f}s/张")
    print(f"  总耗时: {total_duration:.1f}s ({total_duration/60:.1f}min)")

    # Bug #4 汇总
    print(f"\n  --- Bug #4 Validator 改善 ---")
    print(f"    Step 7: {bug4_analysis['step7_eye_level']} eye_level 假阳性")
    print(f"    回归: {bug4_analysis['eye_level_count']} eye_level 假阳性")
    print(f"    改善: {'✅' if bug4_analysis['improved'] else '❌'}")

    # SQ-5 字段
    print(f"\n  --- SQ-5 新字段 ---")
    print(f"    focal_length: {sq5_fields['has_focal_length']}")
    print(f"    foreground: {sq5_fields['has_foreground']}")
    print(f"    background: {sq5_fields['has_background']}")
    print(f"    depth_layers: {sq5_fields['has_depth_layers']}")

    # ============================================================
    # 保存结果文件
    # ============================================================

    regression_results = {
        "task": "TASK-SHOT-QUALITY-BUGFIX Regression",
        "project_id": project_id,
        "test_date": end_time.strftime("%Y-%m-%d"),
        "story_idea": STORY_IDEA,
        "style_preset": STYLE_PRESET,
        "shot_count": shot_count,
        "success_count": success_count,
        "characters": char_names,
        "avg_gen_time": round(avg_time, 2),
        "stage_times": {
            "stage1": "resumed" if resume_mode else round(stage1_time, 2),
            "stage2": "resumed" if resume_mode else round(stage2_time, 2),
            "stage3": "resumed" if resume_mode else round(stage3_time, 2),
            "stage4": "resumed" if resume_mode else round(stage4_time, 2),
            "stage5_refs": round(refs_time, 2),
            "stage5_shots": round(stage5_time, 2)
        },
        "total_duration_seconds": round(total_duration, 2),
        "total_duration_minutes": round(total_duration / 60, 1),
        "bug_checks": {
            "_note": "Bug #1/#2/#3 需人工逐帧审查后填写, Bug #4 自动检测",
            "bug1_scene_labels": {
                "description": "场景标签应为英文, 无 □ 方块",
                "result": None,
                "notes": "检查 labeled_refs/scene_labeled_*.png + shots/ 中有无 □ 文字"
            },
            "bug2_prompt_leakage": {
                "description": "shot 图中无 opacity/px 泄漏文字",
                "result": None,
                "notes": "逐帧检查所有 shot 图, 搜索 opacity/px/technical 英文"
            },
            "bug3_bystanders": {
                "description": "路人出现率从 25% 显著下降, 目标 ≤ 1/N",
                "result": None,
                "step7_rate": "6/24 = 25%",
                "regression_rate": None,
                "bystander_shots": [],
                "notes": ""
            },
            "bug4_validator": {
                "description": "eye_level 假阳性从 22 显著下降",
                "result": "PASS" if bug4_analysis["improved"] else "FAIL",
                "step7_eye_level": bug4_analysis["step7_eye_level"],
                "regression_eye_level": bug4_analysis["eye_level_count"],
                "regression_total_warnings": bug4_analysis["total_warnings"],
                "all_warnings": transition_warnings,
                "improved": bug4_analysis["improved"]
            }
        },
        "sq_checks": {
            "sq5_fields": sq5_fields,
            "camera_analysis": {
                "unique_sizes": camera_analysis["unique_sizes"],
                "unique_angles": camera_analysis["unique_angles"],
                "consecutive_same_size": camera_analysis["consecutive_same_size"],
                "consecutive_same_angle": camera_analysis["consecutive_same_angle"],
                "size_distribution": camera_analysis["size_distribution"],
                "angle_distribution": camera_analysis["angle_distribution"]
            },
            "transition_warnings_count": len(transition_warnings)
        },
        "evaluation": {
            "_note": "以下维度评分需人工审查后填写",
            "dimensions": {
                "1_dialogue_clarity": {"score": None, "step7_score": 4.5},
                "2_narrative_props": {"score": None, "step7_score": 4.5},
                "3_spatial_depth": {"score": None, "step7_score": 4.0},
                "4_camera_diversity": {"score": None, "step7_score": 4.5},
                "5_ref_quality": {"result": None, "step7_result": "PASS"},
                "6_env_continuity": {"score": None, "step7_score": 3.8},
                "7_char_consistency": {"score": None, "step7_score": 4.3}
            },
            "overall": {"score": None, "step7_score": 4.27, "pass": None}
        },
        "shot_results": shot_results
    }

    save_json(os.path.join(project_dir, "bugfix_regression_results.json"), regression_results)
    print(f"\n  bugfix_regression_results.json 已保存")

    summary = {
        "task": "TASK-SHOT-QUALITY-BUGFIX Regression",
        "conclusion": "待人工审查后填写",
        "pass_criteria": {
            "bug1_pass": None,
            "bug2_pass": None,
            "bug3_pass": None,
            "bug4_pass": "PASS" if bug4_analysis["improved"] else "FAIL",
            "overall_ge_4": None,
            "no_new_regression": None,
            "all_pass": None
        }
    }

    save_json(os.path.join(project_dir, "bugfix_regression_summary.json"), summary)
    print(f"  bugfix_regression_summary.json 已保存")

    print(f"\n  输出目录: {project_dir}/")
    print(f"    shots/           — shot 图片 (Bug #2/#3 逐帧审查)")
    print(f"    character_refs/  — 角色参考图")
    print(f"    scene_refs/      — 场景参考图 (原始)")
    print(f"    labeled_refs/    — 标注后参考图 (Bug #1 验证)")
    print(f"{'='*70}")

    return regression_results


if __name__ == "__main__":
    asyncio.run(run_regression_test())
