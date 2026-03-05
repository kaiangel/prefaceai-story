"""
TASK-E2E-TEST-2: Slam Dunk + Sonnet 4.6 端到端流水线验证

复用 Backend 已完成的 Stage 1-4 JSON（slam_dunk + Sonnet 4.6），
只运行 Stage 5（角色参考图 + 场景参考图 + Shot 图像生成 + TextOverlay）。

参考数据来源: test_output/manualtest/model_upgrade_retest_slamdunk/
输出目录: test_output/manualtest/e2e_slamdunk/{timestamp}/

作者: @Tester
日期: 2026-02-27
"""

import asyncio
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from app.services.image_generator import ImageGenerator
from app.services.reference_image_manager import ReferenceImageManager
from app.services.scene_reference_manager import SceneReferenceManager
from app.models.style_config import ProjectStyleConfig
from app.services.text_overlay_service import TextOverlayService


# 源数据目录（Backend Stage 1-4 输出）
SOURCE_DIR = "./test_output/manualtest/model_upgrade_retest_slamdunk"
# 输出目录
OUTPUT_BASE = "./test_output/manualtest/e2e_slamdunk"
# 风格
STYLE_PRESET = "slam_dunk"


def load_json(filepath: str) -> dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(filepath: str, data) -> None:
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_location_id_for_scene(
    scene_id: int,
    screenplay: dict,
    unique_locations: Optional[List[dict]] = None
) -> Optional[str]:
    """从scene_id获取对应的location_id（复制自 pipeline_orchestrator）"""
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
        fallback_id = unique_locations[0].get("location_id")
        print(f"  ⚠️ location_id不匹配: screenplay用'{screenplay_location_id}', fallback到'{fallback_id}'")
        return fallback_id

    return screenplay_location_id


async def run_e2e_slamdunk():
    """运行 slam_dunk E2E 测试（Stage 5 only，复用 Stage 1-4 数据）"""
    start_time = datetime.now()
    project_id = start_time.strftime("%Y%m%d_%H%M%S")
    project_dir = os.path.join(OUTPUT_BASE, project_id)
    os.makedirs(project_dir, exist_ok=True)

    print("=" * 70)
    print("TASK-E2E-TEST-2: Slam Dunk + Sonnet 4.6 E2E 验证")
    print("=" * 70)
    print(f"Project ID: {project_id}")
    print(f"Style: {STYLE_PRESET}")
    print(f"Source data: {SOURCE_DIR}")
    print(f"Output: {project_dir}")
    print("=" * 70)

    # 1. 加载 Stage 1-4 数据
    print("\n--- 加载 Stage 1-4 数据 ---")
    outline = load_json(os.path.join(SOURCE_DIR, "1_outline.json"))
    characters = load_json(os.path.join(SOURCE_DIR, "2_characters.json"))
    screenplay = load_json(os.path.join(SOURCE_DIR, "3_screenplay.json"))
    storyboard = load_json(os.path.join(SOURCE_DIR, "4_storyboard.json"))

    shots = storyboard.get("shots", [])
    char_list = characters.get("characters", [])
    unique_locations = outline.get("unique_locations", [])

    print(f"  故事标题: {outline.get('title', '?')}")
    print(f"  角色数: {len(char_list)}")
    print(f"  场景数: {len(screenplay.get('scenes', []))}")
    print(f"  镜头数: {len(shots)}")
    print(f"  场景位置: {len(unique_locations)}")

    # 复制 Stage 1-4 JSON 到输出目录
    for fname in ["1_outline.json", "2_characters.json", "3_screenplay.json", "4_storyboard.json"]:
        shutil.copy2(os.path.join(SOURCE_DIR, fname), os.path.join(project_dir, fname))
    print("  ✅ Stage 1-4 JSON 已复制到输出目录")

    # 2. 初始化服务
    image_generator = ImageGenerator()
    text_overlay_service = TextOverlayService()
    project_style = ProjectStyleConfig(style_preset=STYLE_PRESET)

    # 创建输出子目录
    images_dir = os.path.join(project_dir, "images")
    with_text_dir = os.path.join(project_dir, "with_text_images")
    char_refs_dir = os.path.join(project_dir, "character_refs")
    scene_refs_dir = os.path.join(project_dir, "scene_refs")
    for d in [images_dir, with_text_dir, char_refs_dir, scene_refs_dir]:
        os.makedirs(d, exist_ok=True)

    # 3. Stage 5a: 生成角色参考图
    print(f"\n{'='*40}")
    print("Stage 5a: 生成角色参考图")
    print(f"{'='*40}")

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
            print("✅")
        except Exception as e:
            print(f"❌ {e}")

    ref_manager.save_all_references(char_refs_dir)
    print(f"✅ 角色参考图已保存到 {char_refs_dir}")

    # 4. Stage 5a.5: 生成场景参考图
    print(f"\n{'='*40}")
    print("Stage 5a.5: 生成场景参考图")
    print(f"{'='*40}")

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

            for anchor_key, anchor_data in scene_anchors.items():
                img = anchor_data.get('image')
                if img:
                    img.save(os.path.join(scene_refs_dir, f"{anchor_key}.png"))

            print(f"✅ 场景参考图生成完成: {len(scene_anchors)}张")
        except Exception as e:
            print(f"⚠️ 场景参考图生成失败: {e}")
            scene_ref_manager = None
    else:
        print("⚠️ 无 unique_locations，跳过场景参考图")

    # 5. Stage 5b: 生成镜头图像 + TextOverlay
    print(f"\n{'='*40}")
    print("Stage 5b: 生成镜头图像 + TextOverlay")
    print(f"{'='*40}")

    image_results = []
    reference_images_log = []
    previous_shot_image = None
    previous_shot = None

    for i, shot in enumerate(shots):
        shot_id = shot.get("shot_id", i + 1)
        print(f"\n  生成 Shot {shot_id}/{len(shots)}...")

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

        ref_info = []
        if chars_in_scene:
            ref_info.append(f"角色: {chars_in_scene} ({len(char_refs)}张)")
        if location_id and scene_refs:
            ref_info.append(f"场景: {location_id} ({len(scene_refs)}张)")
        if ref_info:
            print(f"    {', '.join(ref_info)}")

        reference_images_log.append({
            "shot_id": shot_id,
            "characters_in_scene": chars_in_scene,
            "char_refs_count": len(char_refs),
            "location_id": location_id,
            "scene_refs_count": len(scene_refs),
            "total_refs": len(all_refs)
        })

        # 生成 shot 图像
        result = await image_generator.generate_shot_image_phase2(
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

        if result.get("success"):
            # 保存无文字版
            image_path = os.path.join(images_dir, f"shot_{shot_id:02d}.png")
            result["pil_image"].save(image_path)

            previous_shot_image = result["pil_image"]
            previous_shot = shot

            # TextOverlay
            text_overlay_data = shot.get("text_overlay", {})
            with_text_path = None
            if text_overlay_data and text_overlay_data.get("text_type", "none") != "none":
                try:
                    with_text_image = text_overlay_service.process_shot(
                        result["pil_image"].copy(), text_overlay_data
                    )
                    with_text_path = os.path.join(with_text_dir, f"shot_{shot_id:02d}.png")
                    with_text_image.save(with_text_path)
                    print(f"    ✅ TextOverlay: shot_{shot_id:02d}")
                except Exception as te:
                    print(f"    ⚠️ TextOverlay失败: {te}")

            image_results.append({
                "shot_id": shot_id,
                "success": True,
                "image_path": image_path,
                "with_text_path": with_text_path,
                "generation_time": result.get("generation_time_seconds", 0)
            })
            print(f"    ✅ Shot {shot_id} 保存成功")
        else:
            image_results.append({
                "shot_id": shot_id,
                "success": False,
                "error": result.get("error", "Unknown error")
            })
            print(f"    ❌ Shot {shot_id} 失败: {result.get('error')}")

        await asyncio.sleep(0.5)

    # 6. 保存结果
    save_json(os.path.join(project_dir, "5_image_results.json"), image_results)
    save_json(os.path.join(project_dir, "reference_images_log.json"), reference_images_log)

    # 7. 汇总
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    success_count = sum(1 for r in image_results if r.get("success"))
    with_text_count = sum(1 for r in image_results if r.get("with_text_path"))

    summary = {
        "project_id": project_id,
        "project_dir": project_dir,
        "style_preset": STYLE_PRESET,
        "title": outline.get("title", ""),
        "total_characters": len(char_list),
        "total_scenes": len(screenplay.get("scenes", [])),
        "total_shots": len(shots),
        "images_generated": success_count,
        "images_failed": len(shots) - success_count,
        "with_text_count": with_text_count,
        "pipeline_duration_seconds": round(duration, 2),
        "source_data": SOURCE_DIR,
        "timestamp": end_time.isoformat()
    }
    save_json(os.path.join(project_dir, "summary.json"), summary)

    print(f"\n{'='*70}")
    print("TASK-E2E-TEST-2 完成!")
    print(f"{'='*70}")
    print(f"  项目目录: {project_dir}")
    print(f"  故事标题: {outline.get('title', '')}")
    print(f"  风格: {STYLE_PRESET}")
    print(f"  镜头: {success_count}/{len(shots)} 成功")
    print(f"  TextOverlay: {with_text_count} 带文字版")
    print(f"  总耗时: {duration:.1f}秒")
    print(f"{'='*70}")

    return {
        "success": success_count == len(shots),
        "summary": summary,
        "image_results": image_results,
        "reference_images_log": reference_images_log
    }


if __name__ == "__main__":
    asyncio.run(run_e2e_slamdunk())
