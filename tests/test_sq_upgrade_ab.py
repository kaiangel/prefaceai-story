"""
TASK-SHOT-QUALITY-UPGRADE Step 7: A/B 对比验证 — SQ-1~SQ-8 改进效果

A 组: 复用 DIALOGUE-DENSE-TEST 已有输出 (29 shots, illustration, 3人年夜饭争吵)
B 组: 同 idea 同参数新跑 (含全部 SQ-1~SQ-8 改进)

7 维度评估:
  1. 对话明确性 (SQ-3)
  2. 叙事性视觉道具 (SQ-4)
  3. 空间纵深 (SQ-4)
  4. 运镜差异化 (SQ-5+6)
  5. 参考图质量 (SQ-1+2) — PASS/FAIL
  6. 环境连续性 (SQ-8)
  7. 角色一致性 (整体)

通过标准:
  - B 综合 >= 4.0/5 且 B >= A
  - 维度 5 PASS
  - 维度 4 B > A
  - 维度 6 B >= 3.5

关键 SQ 代码变更 (B 组将验证):
  - SQ-1: 参考图 PIL 文字标注 (_label_reference_image / _label_scene_image)
  - SQ-2: 智能参考图选择 (get_smart_references_for_scene → 每角色1张)
  - SQ-3: 对话明确化规则 (screenplay_writer.py)
  - SQ-4: 叙事视觉道具 + 空间纵深 (storyboard_director.py)
  - SQ-5: 运镜差异化规则 + 新 JSON 字段 (focal_length/foreground/background/depth_layers)
  - SQ-6: validate_shot_transitions() 运镜验证器
  - SQ-8: 移除 previous_shot_image (DEC-014)

注意: B 组使用原始 DIALOGUE-DENSE-TEST idea (3人年夜饭, 非 PM 派发中的6人卖房).
  原因: PM 指定 "唯一差异 = 代码改进" + "B 组 idea 必须完全相同",
  公平 A/B 对比必须使用相同 idea. PM 派发中的 idea 文本是不同故事.

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
OUTPUT_BASE = "./test_output/manualtest/sq_upgrade_ab_test"
STYLE_PRESET = "illustration"

# A 组 baseline 路径 (DIALOGUE-DENSE-TEST 已有输出)
A_GROUP_DIR = "./test_output/manualtest/dialogue_dense_test/20260302_165748"

# B 组 idea — 与 A 组完全相同 (公平 A/B 对比)
STORY_IDEA = (
    "年夜饭上，爷爷坚持孙子必须考公务员，父亲想让儿子接管家族生意，"
    "而22岁的孙子只想辞职去做独立游戏开发。三代人的晚餐从敬酒变成了激烈争吵。"
)


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


# =========== A 组分析 ===========

def analyze_a_group() -> dict:
    """分析 A 组 baseline (DIALOGUE-DENSE-TEST 已有输出)"""
    print(f"\n{'='*60}")
    print("A 组分析: DIALOGUE-DENSE-TEST baseline")
    print(f"{'='*60}")

    a_dir = A_GROUP_DIR

    # 加载 A 组数据
    storyboard = load_json(os.path.join(a_dir, "4_storyboard.json"))
    results = load_json(os.path.join(a_dir, "dialogue_dense_test_results.json"))
    shots = storyboard.get("shots", [])

    print(f"  A 组 shots 数: {len(shots)}")
    print(f"  A 组角色: {results.get('characters', [])}")

    # 维度 4 分析: 运镜差异化 (A 组 baseline)
    camera_analysis = analyze_camera_diversity(shots, "A")

    # 维度 5 分析: 参考图 (A 组无 PIL 标注)
    a_char_refs_dir = os.path.join(a_dir, "character_refs")
    a_ref_files = os.listdir(a_char_refs_dir) if os.path.isdir(a_char_refs_dir) else []
    print(f"\n  A 组参考图: {len(a_ref_files)} 张 (预期无 PIL 标注)")

    # 检查 storyboard JSON 是否有 SQ-5 新字段 (A 组预期没有)
    sq5_fields = check_sq5_fields(shots)
    print(f"  A 组 SQ-5 新字段: focal_length={sq5_fields['has_focal_length']}, "
          f"foreground={sq5_fields['has_foreground']}, "
          f"background={sq5_fields['has_background']}, "
          f"depth_layers={sq5_fields['has_depth_layers']}")

    return {
        "dir": a_dir,
        "shot_count": len(shots),
        "characters": results.get("characters", []),
        "storyboard": storyboard,
        "camera_analysis": camera_analysis,
        "ref_count": len(a_ref_files),
        "sq5_fields": sq5_fields,
        "shots": shots
    }


def analyze_camera_diversity(shots: list, group_label: str) -> dict:
    """分析运镜多样性 — 维度 4"""
    total = len(shots)
    if total == 0:
        return {"consecutive_same_size": 0, "consecutive_same_angle": 0, "unique_sizes": 0, "unique_angles": 0}

    # 统计景别和角度
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

    # 统计 3+ 连续相同景别
    consecutive_same_size = 0
    for i in range(2, total):
        if shot_sizes[i] == shot_sizes[i-1] == shot_sizes[i-2]:
            consecutive_same_size += 1

    # 统计 3+ 连续相同角度
    consecutive_same_angle = 0
    for i in range(2, total):
        if camera_angles[i] == camera_angles[i-1] == camera_angles[i-2]:
            consecutive_same_angle += 1

    # 景别分布
    size_dist = {}
    for s in shot_sizes:
        size_dist[s] = size_dist.get(s, 0) + 1

    angle_dist = {}
    for a in camera_angles:
        angle_dist[a] = angle_dist.get(a, 0) + 1

    print(f"\n  {group_label} 组运镜分析:")
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


# =========== B 组生成 ===========

async def generate_b_group(project_dir: str) -> dict:
    """
    B 组完整 Stage 1→5 新跑 (含 SQ-1~SQ-8 改进)

    关键差异 vs A 组:
    - SQ-2: get_smart_references_for_scene() 替代 get_references_for_scene()
    - SQ-8: 不传 previous_shot_image / previous_shot (DEC-014)
    - SQ-1: 参考图自动带 PIL 文字标注
    - SQ-3/4/5: Stage 3+4 prompt 已内含改进规则
    - SQ-6: validate_shot_transitions() 手动调用检查
    """

    # ============================================================
    # Stage 1: 故事大纲
    # ============================================================
    print(f"\n{'='*50}")
    print("B 组 Stage 1: 生成故事大纲")
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
    print("B 组 Stage 2: 设计角色")
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
    # Stage 3: 分场剧本 (含 SQ-3 对话明确化规则)
    # ============================================================
    print(f"\n{'='*50}")
    print("B 组 Stage 3: 编写分场剧本 (SQ-3 对话明确化)")
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
    # Stage 4: 分镜脚本 (含 SQ-4 视觉道具 + SQ-5 运镜差异化)
    # ============================================================
    print(f"\n{'='*50}")
    print("B 组 Stage 4: 创建分镜脚本 (SQ-4 道具 + SQ-5 运镜)")
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
    shots = storyboard.get("shots", [])
    shot_count = len(shots)
    print(f"✅ Stage 4 完成 ({stage4_time:.1f}s): {shot_count} 个镜头")

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
    # SQ-6 运镜过渡验证
    # ============================================================
    print(f"\n  SQ-6 运镜过渡验证:")
    transition_warnings = validate_shot_transitions(shots)
    if transition_warnings:
        print(f"    ⚠️ {len(transition_warnings)} 个警告:")
        for w in transition_warnings:
            print(f"      - {w}")
    else:
        print(f"    ✅ 0 个警告 — 所有运镜过渡规则通过")

    # ============================================================
    # Stage 5a: 生成参考图 (SQ-1 PIL 标注 + SQ-2 智能选择)
    # ============================================================
    print(f"\n{'='*50}")
    print("B 组 Stage 5a: 生成参考图 (SQ-1 标注 + SQ-2 智能选择)")
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
    # SQ-1 验证: 参考图 PIL 标注检查
    # ============================================================
    print(f"\n  SQ-1 参考图标注验证:")
    # 通过 get_smart_references_for_scene 获取标注后的参考图并检查
    test_char_ids = [c.get("id") for c in char_list if c.get("id")]
    if test_char_ids:
        smart_refs = ref_manager.get_smart_references_for_scene(test_char_ids, "medium_shot")
        print(f"    get_smart_references_for_scene({test_char_ids}, 'medium_shot'): {len(smart_refs)} 张")
        print(f"    SQ-2 验证: 每角色 1 张 (预期 {len(test_char_ids)} 张, 实际 {len(smart_refs)} 张)")

        # 保存标注后的参考图用于人工审查
        labeled_refs_dir = os.path.join(project_dir, "labeled_refs")
        os.makedirs(labeled_refs_dir, exist_ok=True)
        for idx, ref_img in enumerate(smart_refs):
            ref_img.save(os.path.join(labeled_refs_dir, f"smart_ref_{idx+1}.png"))
        print(f"    标注后参考图已保存: {labeled_refs_dir}/ (供人工审查 PIL 标签)")

    # ============================================================
    # Stage 5b: 生成所有 shots (SQ-8: 无 previous_shot)
    # ============================================================
    print(f"\n{'='*50}")
    print(f"B 组 Stage 5b: 生成 shots — {shot_count} shots (SQ-8: 无 previous_shot)")
    print(f"{'='*50}")

    shots_dir = os.path.join(project_dir, "shots")
    os.makedirs(shots_dir, exist_ok=True)

    stage5_start = time.time()
    shot_results = []

    # B 组不需要 override style_description — 场域式已在 style_enforcer.py 中
    # (A 组 test_dialogue_dense.py 的 override 与代码默认值完全一致)

    for i, shot in enumerate(shots):
        shot_id = shot.get("shot_id", i + 1)
        text_type = shot.get("text_overlay", {}).get("text_type", "none")

        print(f"\n  Shot {shot_id:02d}/{shot_count} ({text_type})...", flush=True)

        # SQ-2: 智能参考图选择 (替代旧 get_references_for_scene)
        char_direction = shot.get("character_direction", {})
        chars_in_scene = char_direction.get("characters_visible", [])
        shot_type = shot.get("camera", {}).get("shot_size", "medium_shot")
        char_refs = ref_manager.get_smart_references_for_scene(chars_in_scene, shot_type)

        # 场景参考图 (SQ-1: 自动带 PIL 标注)
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

        shot_result = {
            "shot_id": shot_id,
            "text_type": text_type,
            "chars_in_scene": chars_in_scene,
            "char_refs_count": len(char_refs),
            "scene_refs_count": len(scene_refs),
            "shot_type": shot_type,
            "success": False,
            "generation_time": round(gen_time, 2)
        }

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

        shot_results.append(shot_result)
        await asyncio.sleep(2)

    stage5_time = time.time() - stage5_start

    success_count = sum(1 for r in shot_results if r.get("success"))
    gen_times = [r["generation_time"] for r in shot_results if r.get("success")]
    avg_time = sum(gen_times) / len(gen_times) if gen_times else 0

    print(f"\n  B 组生成完成: {success_count}/{shot_count} 成功")
    print(f"  平均生图: {avg_time:.1f}s/张")
    print(f"  Stage 5 总耗时: {stage5_time:.1f}s")

    # 运镜分析
    camera_analysis = analyze_camera_diversity(shots, "B")

    return {
        "dir": project_dir,
        "shot_count": shot_count,
        "characters": char_names,
        "outline": outline,
        "storyboard": storyboard,
        "screenplay": screenplay,
        "shots": shots,
        "shot_results": shot_results,
        "camera_analysis": camera_analysis,
        "sq5_fields": sq5_fields,
        "transition_warnings": transition_warnings,
        "success_count": success_count,
        "avg_gen_time": round(avg_time, 2),
        "stage_times": {
            "stage1": round(stage1_time, 2),
            "stage2": round(stage2_time, 2),
            "stage3": round(stage3_time, 2),
            "stage4": round(stage4_time, 2),
            "stage5_refs": round(refs_time, 2),
            "stage5_shots": round(stage5_time, 2)
        }
    }


# =========== 主测试流程 ===========

async def run_ab_test():
    """运行 Step 7 A/B 对比验证"""
    total_start = datetime.now()
    project_id = total_start.strftime("%Y%m%d_%H%M%S")
    project_dir = os.path.join(OUTPUT_BASE, project_id)
    os.makedirs(project_dir, exist_ok=True)

    print("=" * 70)
    print("TASK-SHOT-QUALITY-UPGRADE Step 7: A/B 对比验证")
    print("=" * 70)
    print(f"Project ID: {project_id}")
    print(f"Story idea: {STORY_IDEA}")
    print(f"Style: {STYLE_PRESET} (场域式, 代码默认)")
    print(f"Model: Stage 1-4 Sonnet 4.6 / Stage 5 NB2")
    print(f"A 组: {A_GROUP_DIR}")
    print(f"B 组: {project_dir}")
    print(f"SQ 改进: SQ-1~SQ-8 全部启用")
    print("=" * 70)

    # ============================================================
    # Phase 1: A 组分析
    # ============================================================
    a_data = analyze_a_group()

    # ============================================================
    # Phase 2: B 组生成
    # ============================================================
    b_data = await generate_b_group(project_dir)

    # ============================================================
    # Phase 3: A/B 对比汇总
    # ============================================================
    end_time = datetime.now()
    total_duration = (end_time - total_start).total_seconds()

    print(f"\n{'='*70}")
    print("Step 7 A/B 对比完成!")
    print(f"{'='*70}")
    print(f"  A 组: {a_data['shot_count']} shots, 角色: {a_data['characters']}")
    print(f"  B 组: {b_data['shot_count']} shots, 角色: {b_data['characters']}")
    print(f"  B 组成功: {b_data['success_count']}/{b_data['shot_count']}")
    print(f"  B 组平均生图: {b_data['avg_gen_time']}s/张")

    # 运镜对比
    print(f"\n  --- 运镜差异化对比 (维度 4) ---")
    a_cam = a_data["camera_analysis"]
    b_cam = b_data["camera_analysis"]
    print(f"    景别种类: A={a_cam['unique_sizes']} → B={b_cam['unique_sizes']}")
    print(f"    角度种类: A={a_cam['unique_angles']} → B={b_cam['unique_angles']}")
    print(f"    3+连续同景别: A={a_cam['consecutive_same_size']} → B={b_cam['consecutive_same_size']}")
    print(f"    3+连续同角度: A={a_cam['consecutive_same_angle']} → B={b_cam['consecutive_same_angle']}")

    # SQ-5 新字段对比
    print(f"\n  --- SQ-5 新字段对比 ---")
    a_sq5 = a_data["sq5_fields"]
    b_sq5 = b_data["sq5_fields"]
    print(f"    focal_length: A={a_sq5['has_focal_length']} → B={b_sq5['has_focal_length']}")
    print(f"    foreground:    A={a_sq5['has_foreground']} → B={b_sq5['has_foreground']}")
    print(f"    background:    A={a_sq5['has_background']} → B={b_sq5['has_background']}")
    print(f"    depth_layers:  A={a_sq5['has_depth_layers']} → B={b_sq5['has_depth_layers']}")

    # SQ-6 validator
    print(f"\n  --- SQ-6 运镜验证器 ---")
    tw = b_data.get("transition_warnings", [])
    print(f"    B 组 warnings: {len(tw)}")

    # 参考图对比
    print(f"\n  --- 参考图 (维度 5) ---")
    print(f"    A 组: {a_data['ref_count']} 张 (每角色 2 张, 无 PIL 标注)")
    print(f"    B 组: 每角色 1 张 (SQ-2 智能选择), 有 PIL 标注 (SQ-1)")

    print(f"\n  --- 耗时 ---")
    st = b_data["stage_times"]
    print(f"    B 组 Stage 1 大纲:   {st['stage1']}s")
    print(f"    B 组 Stage 2 角色:   {st['stage2']}s")
    print(f"    B 组 Stage 3 剧本:   {st['stage3']}s")
    print(f"    B 组 Stage 4 分镜:   {st['stage4']}s")
    print(f"    B 组 Stage 5 参考图: {st['stage5_refs']}s")
    print(f"    B 组 Stage 5 shots:  {st['stage5_shots']}s")
    print(f"    总耗时: {total_duration:.1f}s ({total_duration/60:.1f}min)")

    # ============================================================
    # 保存结果文件
    # ============================================================

    # step7_ab_results.json — 详细结果 (评分部分需人工填写)
    ab_results = {
        "task": "TASK-SHOT-QUALITY-UPGRADE Step 7",
        "project_id": project_id,
        "test_date": end_time.strftime("%Y-%m-%d"),
        "story_idea": STORY_IDEA,
        "style_preset": STYLE_PRESET,
        "a_group": {
            "source": "DIALOGUE-DENSE-TEST (20260302_165748)",
            "dir": A_GROUP_DIR,
            "shot_count": a_data["shot_count"],
            "characters": a_data["characters"],
            "camera_analysis": {
                "unique_sizes": a_cam["unique_sizes"],
                "unique_angles": a_cam["unique_angles"],
                "consecutive_same_size": a_cam["consecutive_same_size"],
                "consecutive_same_angle": a_cam["consecutive_same_angle"],
                "size_distribution": a_cam["size_distribution"],
                "angle_distribution": a_cam["angle_distribution"]
            },
            "sq5_fields": a_sq5,
            "ref_count": a_data["ref_count"],
            "has_pil_labels": False
        },
        "b_group": {
            "source": "新跑 (SQ-1~SQ-8 全部启用)",
            "dir": project_dir,
            "shot_count": b_data["shot_count"],
            "characters": b_data["characters"],
            "success_count": b_data["success_count"],
            "avg_gen_time": b_data["avg_gen_time"],
            "stage_times": b_data["stage_times"],
            "camera_analysis": {
                "unique_sizes": b_cam["unique_sizes"],
                "unique_angles": b_cam["unique_angles"],
                "consecutive_same_size": b_cam["consecutive_same_size"],
                "consecutive_same_angle": b_cam["consecutive_same_angle"],
                "size_distribution": b_cam["size_distribution"],
                "angle_distribution": b_cam["angle_distribution"]
            },
            "sq5_fields": b_sq5,
            "transition_warnings": tw,
            "shot_results": b_data["shot_results"],
            "has_pil_labels": True
        },
        "evaluation": {
            "_note": "以下评分需人工审查图片后填写",
            "dimensions": {
                "1_dialogue_clarity": {"a_score": None, "b_score": None, "sq": "SQ-3", "notes": ""},
                "2_narrative_props": {"a_score": None, "b_score": None, "sq": "SQ-4", "notes": "", "b_props_ratio": ""},
                "3_spatial_depth": {"a_score": None, "b_score": None, "sq": "SQ-4", "notes": ""},
                "4_camera_diversity": {
                    "a_score": None, "b_score": None, "sq": "SQ-5+6",
                    "notes": "",
                    "a_consecutive_same_size": a_cam["consecutive_same_size"],
                    "b_consecutive_same_size": b_cam["consecutive_same_size"],
                    "a_consecutive_same_angle": a_cam["consecutive_same_angle"],
                    "b_consecutive_same_angle": b_cam["consecutive_same_angle"]
                },
                "5_ref_quality": {"a_result": "FAIL (无 PIL 标注)", "b_result": None, "sq": "SQ-1+2", "notes": ""},
                "6_env_continuity": {"a_score": None, "b_score": None, "sq": "SQ-8", "notes": ""},
                "7_char_consistency": {"a_score": None, "b_score": None, "sq": "整体", "notes": "", "deviations": []}
            },
            "overall": {"a_score": None, "b_score": None, "pass": None}
        },
        "total_duration_seconds": round(total_duration, 2),
        "total_duration_minutes": round(total_duration / 60, 1)
    }

    save_json(os.path.join(project_dir, "step7_ab_results.json"), ab_results)
    print(f"\n  step7_ab_results.json 已保存 (评分部分待人工填写)")

    # step7_summary.json — 汇总 (评分部分需人工填写)
    summary = {
        "task": "TASK-SHOT-QUALITY-UPGRADE Step 7",
        "conclusion": "待人工审查后填写",
        "pass_criteria": {
            "overall_b_ge_4": None,
            "overall_b_ge_a": None,
            "dim5_pass": None,
            "dim4_b_gt_a": None,
            "dim6_b_ge_3_5": None,
            "all_pass": None
        },
        "ab_comparison": {
            "a_overall": None,
            "b_overall": None,
            "improvement": None
        },
        "key_findings": [],
        "sq_verification": {
            "SQ-1_pil_labels": "待验证",
            "SQ-2_smart_refs": f"B 组每角色 1 张 vs A 组每角色 2 张",
            "SQ-3_dialogue_clarity": "待审查 screenplay",
            "SQ-4_visual_props": "待审查 shots",
            "SQ-5_new_fields": {
                "focal_length": b_sq5["has_focal_length"],
                "foreground": b_sq5["has_foreground"],
                "background": b_sq5["has_background"],
                "depth_layers": b_sq5["has_depth_layers"]
            },
            "SQ-6_validator_warnings": len(tw),
            "SQ-8_no_previous_shot": "已确认 (代码不传 previous_shot_image)"
        },
        "notes": [
            "B 组使用原始 DIALOGUE-DENSE-TEST idea (3人年夜饭), 非 PM 派发中的 6 人卖房 idea",
            "原因: PM 指定 '唯一差异=代码改进', 公平 A/B 对比必须同 idea"
        ]
    }

    save_json(os.path.join(project_dir, "step7_summary.json"), summary)
    print(f"  step7_summary.json 已保存 (结论待人工审查后填写)")

    print(f"\n  输出目录: {project_dir}/")
    print(f"    shots/           — B 组 shot 图片")
    print(f"    character_refs/  — B 组角色参考图 (原始)")
    print(f"    scene_refs/      — B 组场景参考图")
    print(f"    labeled_refs/    — B 组标注后参考图 (SQ-1 验证)")
    print(f"{'='*70}")

    return ab_results


if __name__ == "__main__":
    asyncio.run(run_ab_test())
