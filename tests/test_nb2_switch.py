"""
TASK-NB2-SWITCH 验证: Nano Banana 2 (gemini-3.1-flash-image-preview) Shot 生成测试

复用 Stage 1-4 数据，只生成前 5 张 shot，验证：
1. 图片正常生成（848x1264, 2:3）
2. 参考图正确传入
3. 角色可辨识
4. 记录生成速度（预期比 Pro 快 3-5 倍）

作者: @Backend
日期: 2026-02-27
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from app.services.image_generator import ImageGenerator
from app.services.reference_image_manager import ReferenceImageManager
from app.services.scene_reference_manager import SceneReferenceManager
from app.models.style_config import ProjectStyleConfig

SOURCE_DIR = "./test_output/manualtest/model_upgrade_retest_slamdunk"
OUTPUT_DIR = "./test_output/manualtest/nb2_switch_verify"
STYLE_PRESET = "slam_dunk"
MAX_SHOTS = 5  # 只测 5 张


def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_location_id_for_scene(scene_id, screenplay, unique_locations=None):
    if not scene_id or not screenplay:
        return None
    for scene in screenplay.get("scenes", []):
        if scene.get("scene_id") == scene_id:
            loc_id = scene.get("location_id")
            if unique_locations:
                for loc in unique_locations:
                    if loc.get("location_id") == loc_id:
                        return loc_id
                return unique_locations[0].get("location_id") if unique_locations else loc_id
            return loc_id
    return None


async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("TASK-NB2-SWITCH 验证: Nano Banana 2 Shot 生成")
    print("=" * 60)

    # 确认模型
    ig = ImageGenerator()
    print(f"  NB2_MODEL = {ig.NB2_MODEL}")
    assert "3.1-flash" in ig.NB2_MODEL, f"模型未切换！当前: {ig.NB2_MODEL}"
    print("  ✅ 模型已切换到 Nano Banana 2")

    # 加载数据
    outline = load_json(os.path.join(SOURCE_DIR, "1_outline.json"))
    characters = load_json(os.path.join(SOURCE_DIR, "2_characters.json"))
    screenplay = load_json(os.path.join(SOURCE_DIR, "3_screenplay.json"))
    storyboard = load_json(os.path.join(SOURCE_DIR, "4_storyboard.json"))

    shots = storyboard.get("shots", [])[:MAX_SHOTS]
    char_list = characters.get("characters", [])
    unique_locations = outline.get("unique_locations", [])

    print(f"  测试 {len(shots)}/{len(storyboard.get('shots', []))} shots")

    project_style = ProjectStyleConfig(style_preset=STYLE_PRESET)

    # 生成角色参考图
    print("\n--- 生成角色参考图 ---")
    ref_manager = ReferenceImageManager()
    for char in char_list:
        name = char.get("name", "?")
        print(f"  {name}...", end=" ", flush=True)
        await ref_manager.generate_character_multi_refs(
            character=char,
            project_style=project_style,
            image_generator=ig
        )
        print("✅")

    # 生成场景参考图
    print("\n--- 生成场景参考图 ---")
    scene_ref_manager = None
    if unique_locations:
        scene_ref_manager = SceneReferenceManager()
        scene_anchors = await scene_ref_manager.generate_anchor_images(
            scenes=[],
            project_style=project_style,
            image_generator=ig,
            unique_locations=unique_locations,
            delay=3.0
        )
        print(f"  ✅ {len(scene_anchors)} 张场景参考图")

    # 生成 shots
    print(f"\n--- 生成 {len(shots)} 张 Shot (NB2) ---")
    results = []
    gen_times = []
    previous_shot_image = None
    previous_shot = None

    for i, shot in enumerate(shots):
        shot_id = shot.get("shot_id", i + 1)
        print(f"\n  Shot {shot_id}...", end=" ", flush=True)

        # 参考图
        chars_visible = shot.get("character_direction", {}).get("characters_visible", [])
        char_refs = ref_manager.get_references_for_scene(chars_visible)
        scene_refs = []
        if scene_ref_manager:
            loc_id = get_location_id_for_scene(
                shot.get("scene_id"), screenplay, unique_locations
            )
            if loc_id:
                scene_refs = scene_ref_manager.get_references_for_location(loc_id)

        all_refs = char_refs + scene_refs
        print(f"refs={len(all_refs)}", end=" ", flush=True)

        t0 = time.time()
        result = await ig.generate_shot_image_phase2(
            shot=shot,
            storyboard=storyboard,
            characters=characters,
            style_preset=STYLE_PRESET,
            reference_images=all_refs,
            previous_shot_image=previous_shot_image,
            previous_shot=previous_shot,
            screenplay=screenplay,
            aspect_ratio="2:3"
        )
        elapsed = time.time() - t0

        if result.get("success"):
            img = result["pil_image"]
            w, h = img.size
            img_path = os.path.join(OUTPUT_DIR, f"shot_{shot_id:02d}.png")
            img.save(img_path)
            previous_shot_image = img
            previous_shot = shot
            gen_times.append(elapsed)
            results.append({
                "shot_id": shot_id,
                "success": True,
                "size": f"{w}x{h}",
                "time_seconds": round(elapsed, 1),
                "refs": len(all_refs)
            })
            print(f"✅ {w}x{h} {elapsed:.1f}s")
        else:
            results.append({
                "shot_id": shot_id,
                "success": False,
                "error": result.get("error", "?")
            })
            print(f"❌ {result.get('error')}")

        await asyncio.sleep(0.5)

    # 汇总
    success = sum(1 for r in results if r.get("success"))
    avg_time = sum(gen_times) / len(gen_times) if gen_times else 0

    print(f"\n{'='*60}")
    print("NB2 验证结果")
    print(f"{'='*60}")
    print(f"  模型: {ig.NB2_MODEL}")
    print(f"  成功: {success}/{len(shots)}")
    print(f"  平均生成时间: {avg_time:.1f}s/张")
    print(f"  总耗时: {sum(gen_times):.1f}s (仅 shot 生成)")

    for r in results:
        if r.get("success"):
            print(f"  Shot {r['shot_id']}: {r['size']} | {r['time_seconds']}s | refs={r['refs']}")

    save_json(os.path.join(OUTPUT_DIR, "nb2_verify_results.json"), {
        "model": ig.NB2_MODEL,
        "shots_tested": len(shots),
        "success_count": success,
        "avg_generation_time": round(avg_time, 1),
        "results": results
    })

    print(f"\n  输出目录: {OUTPUT_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
