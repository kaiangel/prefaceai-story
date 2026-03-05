"""
TASK-AB-STYLE-DESC: 场域式 vs 命令式 style_description A/B 测试

A组: 命令式 style_description（当前 slam_dunk preset，不改代码）
B组: 场域式 style_description（AI-ML 改写版本，临时覆盖）

控制变量: mandatory_keywords + forbidden_keywords 两组完全相同，仅 style_description 不同

评估维度:
  1. 风格一致性 — 5 shots 之间视觉风格的统一程度
  2. 风格准确度 — 与 slam_dunk（灌篮高手/井上雄彦）的匹配度
  3. 风格漂移   — 是否出现与目标风格不符的元素

复用 Stage 1-4 数据和参考图，5 个代表性 shots × 2 组

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
from typing import List

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from PIL import Image
from app.services.image_generator import ImageGenerator
from app.services.style_enforcer import StyleEnforcer


# =========== 配置 ===========
SOURCE_DIR = "./test_output/manualtest/model_upgrade_retest_slamdunk"
E2E_DIR = "./test_output/manualtest/e2e_slamdunk/20260227_140414"
OUTPUT_BASE = "./test_output/manualtest/ab_style_desc"
STYLE_PRESET = "slam_dunk"

# 选定的 5 个代表性 shots（与 NB2-TEXT-TEST 相同，便于横向对比）
SELECTED_SHOTS = [1, 6, 9, 13, 17]

# 场景 → location_id 映射（从 3_screenplay.json）
SCENE_LOCATION_MAP = {
    1: "locker_room_pregame",
    2: "gymnasium_main_court",
    3: "sideline_bench_area",
    4: "gymnasium_main_court",
    5: "gymnasium_main_court",
    6: "gymnasium_main_court",
}

# =========== A/B 组 style_description ===========

# A 组: 命令式（当前代码中的 slam_dunk style_description，原样使用）
STYLE_DESC_A = (
    "This image MUST be in Slam Dunk manga style inspired by Takehiko Inoue. "
    "Realistic human proportions with athletic builds, strong dynamic linework, "
    "dramatic contrast with rich color palette, screentone shading, expressive character acting, "
    "and cinematic composition. NOT cute/chibi anime — this is mature, realistic manga art. "
    "MUST be in FULL COLOR."
)

# B 组: 场域式（AI-ML 2026-02-27 17:44 提供，PM 2026-02-28 10:25 审核通过）
STYLE_DESC_B = (
    "You are drawing in the tradition of Takehiko Inoue, where basketball manga becomes cinema. "
    "Every body carries real athletic weight — muscles defined under fabric, postures shaped by "
    "exhaustion and resolve, faces holding the full depth of human emotion. Bold ink strokes for "
    "power, fine hatching for shadow, screentone gradients building atmosphere like a film score. "
    "Light is the silent storyteller: gymnasium fluorescents carving sharp shadows, golden hour "
    "warming courts in amber. Rich, saturated color grounds every panel in vivid reality. Each "
    "composition finds the cinematic angle that makes the viewer feel the impact — a dunk's slam, "
    "a free throw's silence, the weight of unspoken rivalry."
)


def load_json(filepath: str) -> dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(filepath: str, data) -> None:
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_reference_images(
    char_ids: List[str],
    scene_id: int,
    char_refs_dir: str,
    scene_refs_dir: str
) -> List[Image.Image]:
    """加载角色参考图和场景参考图"""
    refs = []

    # 角色参考图：portrait + fullbody
    for char_id in char_ids:
        portrait_path = os.path.join(char_refs_dir, f"{char_id}_portrait.png")
        fullbody_path = os.path.join(char_refs_dir, f"{char_id}_fullbody.png")
        if os.path.exists(portrait_path):
            refs.append(Image.open(portrait_path))
        if os.path.exists(fullbody_path):
            refs.append(Image.open(fullbody_path))

    # 场景参考图
    location_id = SCENE_LOCATION_MAP.get(scene_id)
    if location_id:
        for fname in sorted(os.listdir(scene_refs_dir)):
            if location_id in fname and fname.endswith('.png'):
                refs.append(Image.open(os.path.join(scene_refs_dir, fname)))

    return refs


async def generate_group(
    group_name: str,
    style_desc: str,
    shots: list,
    storyboard: dict,
    characters: dict,
    screenplay: dict,
    image_generator: ImageGenerator,
    char_refs_dir: str,
    scene_refs_dir: str,
    output_dir: str
) -> list:
    """为一组生成 5 shots"""
    results = []

    # 临时覆盖 style_description
    original_desc = StyleEnforcer.STYLE_ENFORCEMENTS[STYLE_PRESET].style_description
    StyleEnforcer.STYLE_ENFORCEMENTS[STYLE_PRESET].style_description = style_desc

    try:
        for shot in shots:
            shot_id = shot.get("shot_id")
            text_type = shot.get("text_overlay", {}).get("text_type", "none")

            print(f"\n  [{group_name}] Shot {shot_id:02d} ({text_type})...")

            # 获取参考图
            char_direction = shot.get("character_direction", {})
            chars_in_scene = char_direction.get("characters_visible", [])
            scene_id = shot.get("scene_id")

            ref_images = load_reference_images(
                chars_in_scene, scene_id,
                char_refs_dir, scene_refs_dir
            )

            gen_start = time.time()
            result = await image_generator.generate_shot_image_phase2(
                shot=shot,
                storyboard=storyboard,
                characters=characters,
                style_preset=STYLE_PRESET,
                reference_images=ref_images,
                previous_shot_image=None,
                previous_shot=None,
                screenplay=screenplay,
                aspect_ratio="2:3",
                use_native_text=True
            )
            gen_time = time.time() - gen_start

            shot_result = {
                "shot_id": shot_id,
                "text_type": text_type,
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
                print(f"    ✅ 成功 ({gen_time:.1f}s, {img.size[0]}x{img.size[1]})")
            else:
                shot_result["error"] = result.get("error", "Unknown")
                print(f"    ❌ 失败: {shot_result['error']}")

            results.append(shot_result)
            await asyncio.sleep(3)  # 避免限流

    finally:
        # 恢复原始 style_description
        StyleEnforcer.STYLE_ENFORCEMENTS[STYLE_PRESET].style_description = original_desc

    return results


async def run_ab_style_desc_test():
    """运行场域式 vs 命令式 style_description A/B 测试"""
    start_time = datetime.now()
    project_id = start_time.strftime("%Y%m%d_%H%M%S")
    project_dir = os.path.join(OUTPUT_BASE, project_id)

    # 创建输出目录
    group_a_dir = os.path.join(project_dir, "group_a_command")
    group_b_dir = os.path.join(project_dir, "group_b_field")
    for d in [group_a_dir, group_b_dir]:
        os.makedirs(d, exist_ok=True)

    print("=" * 70)
    print("TASK-AB-STYLE-DESC: 场域式 vs 命令式 style_description A/B 测试")
    print("=" * 70)
    print(f"Project ID: {project_id}")
    print(f"Selected shots: {SELECTED_SHOTS}")
    print(f"Style: {STYLE_PRESET}")
    print(f"Model: NB2 (gemini-3.1-flash-image-preview)")
    print(f"use_native_text: True")
    print(f"Output: {project_dir}")
    print()
    print(f"A 组 (命令式): {STYLE_DESC_A[:80]}...")
    print(f"B 组 (场域式): {STYLE_DESC_B[:80]}...")
    print()
    print("控制变量: mandatory_keywords + forbidden_keywords 两组完全相同")
    print("=" * 70)

    # 1. 加载 Stage 1-4 数据
    print("\n--- 加载 Stage 1-4 数据 ---")
    outline = load_json(os.path.join(SOURCE_DIR, "1_outline.json"))
    characters = load_json(os.path.join(SOURCE_DIR, "2_characters.json"))
    screenplay = load_json(os.path.join(SOURCE_DIR, "3_screenplay.json"))
    storyboard = load_json(os.path.join(SOURCE_DIR, "4_storyboard.json"))

    shots_all = storyboard.get("shots", [])
    char_list = characters.get("characters", [])

    print(f"  故事: {outline.get('title', '?')}")
    print(f"  角色: {len(char_list)}, 总镜头: {len(shots_all)}")

    # 2. 初始化服务
    image_generator = ImageGenerator()

    # 参考图目录（复用 E2E 测试的参考图）
    char_refs_dir = os.path.join(E2E_DIR, "character_refs")
    scene_refs_dir = os.path.join(E2E_DIR, "scene_refs")

    if not os.path.exists(char_refs_dir):
        print(f"❌ 参考图目录不存在: {char_refs_dir}")
        return None

    # 3. 选择 shots
    selected = [s for s in shots_all if s.get("shot_id") in SELECTED_SHOTS]
    print(f"\n  已选择 {len(selected)} 个 shots:")
    for s in selected:
        text_overlay = s.get("text_overlay", {})
        text_type = text_overlay.get("text_type", "none")
        print(f"    Shot {s['shot_id']:02d}: {text_type}")

    # 4. 保存两组 style_description 用于对比审查
    desc_compare_path = os.path.join(project_dir, "style_description_comparison.txt")
    with open(desc_compare_path, 'w', encoding='utf-8') as f:
        f.write("=== TASK-AB-STYLE-DESC: style_description 对比 ===\n\n")
        f.write("--- A 组: 命令式 (Command Style) ---\n")
        f.write(STYLE_DESC_A + "\n\n")
        f.write("--- B 组: 场域式 (Field Style) ---\n")
        f.write(STYLE_DESC_B + "\n\n")
        f.write("--- 控制变量 (两组相同) ---\n")
        enforcement = StyleEnforcer.STYLE_ENFORCEMENTS[STYLE_PRESET]
        f.write(f"mandatory_keywords: {enforcement.mandatory_keywords}\n")
        f.write(f"forbidden_keywords: {enforcement.forbidden_keywords}\n")
        f.write(f"quality_keywords: {enforcement.quality_keywords}\n")

    # 5. 生成 A 组（命令式）
    print(f"\n{'='*60}")
    print("A 组: 命令式 style_description")
    print(f"{'='*60}")
    a_results = await generate_group(
        group_name="A组 命令式",
        style_desc=STYLE_DESC_A,
        shots=selected,
        storyboard=storyboard,
        characters=characters,
        screenplay=screenplay,
        image_generator=image_generator,
        char_refs_dir=char_refs_dir,
        scene_refs_dir=scene_refs_dir,
        output_dir=group_a_dir
    )

    # 6. 生成 B 组（场域式）
    print(f"\n{'='*60}")
    print("B 组: 场域式 style_description")
    print(f"{'='*60}")
    b_results = await generate_group(
        group_name="B组 场域式",
        style_desc=STYLE_DESC_B,
        shots=selected,
        storyboard=storyboard,
        characters=characters,
        screenplay=screenplay,
        image_generator=image_generator,
        char_refs_dir=char_refs_dir,
        scene_refs_dir=scene_refs_dir,
        output_dir=group_b_dir
    )

    # 7. 保存结果 JSON
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    a_success = sum(1 for r in a_results if r.get("success"))
    b_success = sum(1 for r in b_results if r.get("success"))

    a_times = [r["generation_time"] for r in a_results if r.get("success")]
    b_times = [r["generation_time"] for r in b_results if r.get("success")]

    summary = {
        "task": "TASK-AB-STYLE-DESC",
        "project_id": project_id,
        "project_dir": project_dir,
        "model": "gemini-3.1-flash-image-preview (NB2)",
        "style_preset": STYLE_PRESET,
        "use_native_text": True,
        "selected_shots": SELECTED_SHOTS,
        "total_shots": len(selected),
        "group_a": {
            "name": "命令式 style_description (Command Style)",
            "style_description": STYLE_DESC_A,
            "success_count": a_success,
            "avg_generation_time": round(sum(a_times) / len(a_times), 2) if a_times else 0,
            "results": a_results
        },
        "group_b": {
            "name": "场域式 style_description (Field Style)",
            "style_description": STYLE_DESC_B,
            "success_count": b_success,
            "avg_generation_time": round(sum(b_times) / len(b_times), 2) if b_times else 0,
            "results": b_results
        },
        "pipeline_duration_seconds": round(duration, 2),
        "timestamp": end_time.isoformat()
    }
    save_json(os.path.join(project_dir, "ab_style_desc_results.json"), summary)

    # 8. 打印汇总
    print(f"\n{'='*70}")
    print("TASK-AB-STYLE-DESC 生成完成!")
    print(f"{'='*70}")
    print(f"  输出目录: {project_dir}")
    print(f"  A组 (命令式): {a_success}/{len(selected)} 成功, 平均 {summary['group_a']['avg_generation_time']:.1f}s")
    print(f"  B组 (场域式): {b_success}/{len(selected)} 成功, 平均 {summary['group_b']['avg_generation_time']:.1f}s")
    print(f"  总耗时: {duration:.1f}秒")
    print(f"\n  📁 A组结果: {group_a_dir}/")
    print(f"  📁 B组结果: {group_b_dir}/")
    print(f"  📄 对比文件: {desc_compare_path}")
    print(f"{'='*70}")

    return summary


if __name__ == "__main__":
    asyncio.run(run_ab_style_desc_test())
