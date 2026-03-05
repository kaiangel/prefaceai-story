"""
Step 4: ink + realistic 场域式小规模验证

目的: 确认场域式 style_description 跨风格泛化性
- 已测: slam_dunk, illustration (3 轮 A/B 全胜)
- 本轮: ink (中国水墨) + realistic (写实摄影) — 差异最大的 2 个风格

测试参数 (PM 派发 03-03 17:18):
  - 风格: ink + realistic, 各 5 shots
  - 题材: 都市情感 (与 cross-style-test 同题材便于对比)
  - 模型: Stage 1-4 Sonnet 4.6 / Stage 5 NB2
  - 文字: use_native_text=True
  - 宽高比: 2:3
  - 篇幅: flash (~10 shots), 取 5 shots 子集

验收维度 (4 项, 每项 ≥ 3.5/5):
  1. 风格一致性 — 5 shots 视觉风格统一, 无漂移
  2. 场域式效果 — 光影叙事力、质感密度、构图电影感
  3. 角色一致性 — 同一角色跨 shots 可识别
  4. 文字渲染 — NB2 原生中文可读

注意: style_enforcer.py 已包含场域式 style_description (TASK-STYLE-DESC-REWRITE 完成)
      无需 override, 直接使用即可

作者: @Tester
日期: 2026-03-03
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

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
OUTPUT_BASE = "./test_output/manualtest/style_verify_step4"
STYLES = ["ink", "realistic"]
SHOTS_PER_STYLE = 5

# 都市情感题材 (PM 指定, 与 cross-style-test 同题材便于对比)
STORY_IDEA = (
    "大雨夜，一个独自加班的年轻建筑师发现对面写字楼有一扇窗户总是亮到深夜。"
    "一周后他们在楼下便利店第一次面对面，发现彼此都是城市里孤独的夜归人。"
)


# =========== 工具函数 ===========

def load_json(filepath: str) -> dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(filepath: str, data) -> None:
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def select_shots(shots: list, count: int = 5) -> list:
    """
    从 storyboard 中均匀选取 count 个 shots
    策略: 首 + 均匀分布 + 尾, 覆盖故事开头/中间/结尾
    """
    n = len(shots)
    if n <= count:
        return shots

    indices = []
    for i in range(count):
        idx = round(i * (n - 1) / (count - 1))
        indices.append(idx)

    indices = sorted(set(indices))
    return [shots[i] for i in indices]


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


# =========== 单风格生成 ===========

async def generate_shots_for_style(
    style_preset: str,
    screenplay: dict,
    characters: dict,
    outline: dict,
    output_dir: str
) -> dict:
    """
    为单个风格完成 Stage 4 + Stage 5 (参考图 + shots)

    Stage 4 per style: image_prompt 随风格变化 (ink 会写 brush strokes, realistic 写 natural lighting)
    Stage 5 per style: 参考图 + shot 生成使用该风格

    注意: 不覆盖 style_description — style_enforcer.py 已含场域式
    """
    style_start = time.time()
    style_dir = os.path.join(output_dir, style_preset)
    shots_dir = os.path.join(style_dir, "shots")
    os.makedirs(shots_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"风格: {style_preset}")
    print(f"{'='*60}")

    # 确认当前 style_description 是场域式
    enforcement = StyleEnforcer.STYLE_ENFORCEMENTS.get(style_preset)
    if enforcement:
        desc_preview = enforcement.style_description[:100]
        print(f"  style_description: {desc_preview}...")
        print(f"  mandatory: {enforcement.mandatory_keywords[:3]}...")
        print(f"  forbidden: {enforcement.forbidden_keywords[:3]}...")

    # ---- Stage 4: 分镜脚本 (per style) ----
    print(f"\n  --- Stage 4: 分镜脚本 ({style_preset}) ---")
    s4_start = time.time()
    storyboard_director = StoryboardDirector()
    visual_tone = outline.get("visual_tone", {})
    storyboard = await storyboard_director.direct(
        screenplay=screenplay,
        characters=characters,
        visual_tone=visual_tone,
        style_preset=style_preset
    )
    s4_time = time.time() - s4_start

    save_json(os.path.join(style_dir, "4_storyboard.json"), storyboard)
    all_shots = storyboard.get("shots", [])
    total_shots = len(all_shots)
    print(f"    ✅ ({s4_time:.1f}s): {total_shots} 个镜头")

    # 选取 5 shots
    selected = select_shots(all_shots, SHOTS_PER_STYLE)
    selected_ids = [s.get("shot_id", i + 1) for i, s in enumerate(selected)]
    print(f"    选取 {len(selected)} shots: {selected_ids}")

    # text_type 分布 (辅助信息)
    type_counts = {}
    for shot in all_shots:
        tt = shot.get("text_overlay", {}).get("text_type", "none")
        type_counts[tt] = type_counts.get(tt, 0) + 1
    print(f"    text_type 分布: {type_counts}")

    unique_locations = outline.get("unique_locations", [])

    # ---- Stage 5a: 参考图 ----
    print(f"\n  --- Stage 5a: 参考图 ({style_preset}) ---")
    image_generator = ImageGenerator()
    project_style = ProjectStyleConfig(style_preset=style_preset)

    # 角色参考图
    ref_manager = ReferenceImageManager()
    char_list = characters.get("characters", [])

    for char in char_list:
        char_name = char.get("name", char.get("id", "?"))
        print(f"    角色 {char_name}...", end=" ")
        try:
            await ref_manager.generate_character_multi_refs(
                character=char,
                project_style=project_style,
                image_generator=image_generator
            )
            print("OK")
        except Exception as e:
            print(f"FAIL: {e}")

    char_refs_dir = os.path.join(style_dir, "character_refs")
    os.makedirs(char_refs_dir, exist_ok=True)
    ref_manager.save_all_references(char_refs_dir)

    # 场景参考图
    scene_ref_manager = None
    if unique_locations:
        scene_ref_manager = SceneReferenceManager()
        try:
            scene_anchors = await scene_ref_manager.generate_anchor_images(
                scenes=[],
                project_style=project_style,
                image_generator=image_generator,
                unique_locations=unique_locations,
                delay=3.0
            )
            scene_refs_dir = os.path.join(style_dir, "scene_refs")
            os.makedirs(scene_refs_dir, exist_ok=True)
            for key, data in scene_anchors.items():
                img = data.get('image')
                if img:
                    img.save(os.path.join(scene_refs_dir, f"{key}.png"))
            print(f"    场景参考图: {len(scene_anchors)} 张")
        except Exception as e:
            print(f"    场景参考图失败: {e}")
            scene_ref_manager = None

    # ---- Stage 5b: 生成 shots ----
    print(f"\n  --- Stage 5b: 生成 {len(selected)} shots ({style_preset}) ---")

    previous_shot_image = None
    previous_shot = None
    shot_results = []

    for i, shot in enumerate(selected):
        shot_id = shot.get("shot_id", i + 1)
        text_overlay = shot.get("text_overlay", {})
        text_type = text_overlay.get("text_type", "none")
        chinese_text = text_overlay.get("chinese_text", "")
        text_preview = ""
        if isinstance(chinese_text, str):
            text_preview = chinese_text[:25]
        elif isinstance(chinese_text, list):
            text_preview = str(chinese_text[0])[:25] if chinese_text else ""

        print(f"    Shot {shot_id:02d} ({text_type}) [{text_preview}]...", end=" ")

        # 角色参考
        char_direction = shot.get("character_direction", {})
        chars_visible = char_direction.get("characters_visible", [])
        char_refs = ref_manager.get_references_for_scene(chars_visible)

        # 场景参考
        scene_refs = []
        if scene_ref_manager:
            scene_id = shot.get("scene_id")
            loc_id = get_location_id_for_scene(scene_id, screenplay, unique_locations)
            if loc_id:
                scene_refs = scene_ref_manager.get_references_for_location(loc_id)

        all_refs = char_refs + scene_refs

        gen_start = time.time()
        try:
            result = await image_generator.generate_shot_image_phase2(
                shot=shot,
                storyboard=storyboard,
                characters=characters,
                style_preset=style_preset,
                reference_images=all_refs,
                previous_shot_image=previous_shot_image,
                previous_shot=previous_shot,
                screenplay=screenplay,
                aspect_ratio="2:3",
                use_native_text=True
            )
            gen_time = time.time() - gen_start

            if result.get("success"):
                img = result["pil_image"]
                img_path = os.path.join(shots_dir, f"shot_{shot_id:02d}.png")
                img.save(img_path)

                previous_shot_image = img
                previous_shot = shot

                print(f"✅ ({gen_time:.1f}s, {img.size[0]}x{img.size[1]}, refs={len(all_refs)})")
                shot_results.append({
                    "shot_id": shot_id,
                    "text_type": text_type,
                    "chinese_text_preview": text_preview,
                    "success": True,
                    "gen_time": round(gen_time, 2),
                    "size": f"{img.size[0]}x{img.size[1]}",
                    "refs": len(all_refs)
                })
            else:
                print(f"❌ {result.get('error', 'Unknown')}")
                shot_results.append({
                    "shot_id": shot_id,
                    "text_type": text_type,
                    "success": False,
                    "error": result.get("error", "Unknown")
                })
        except Exception as e:
            gen_time = time.time() - gen_start
            print(f"❌ Exception: {e}")
            shot_results.append({
                "shot_id": shot_id,
                "text_type": text_type,
                "success": False,
                "error": str(e)
            })

        await asyncio.sleep(2)

    style_time = time.time() - style_start
    success_count = sum(1 for r in shot_results if r.get("success"))
    gen_times = [r["gen_time"] for r in shot_results if r.get("success")]
    avg_time = sum(gen_times) / len(gen_times) if gen_times else 0

    style_result = {
        "style_preset": style_preset,
        "stage4_shots": total_shots,
        "selected_shot_ids": selected_ids,
        "shots_generated": len(selected),
        "success_count": success_count,
        "avg_gen_time": round(avg_time, 2),
        "stage4_time": round(s4_time, 2),
        "total_time": round(style_time, 2),
        "text_type_distribution": type_counts,
        "shot_results": shot_results
    }

    save_json(os.path.join(style_dir, "results.json"), style_result)

    print(f"\n  [{style_preset}] 完成: {success_count}/{len(selected)} 成功, "
          f"平均 {avg_time:.1f}s/张, 总耗时 {style_time:.1f}s")

    return style_result


# =========== 主测试流程 ===========

async def run_style_verify_step4():
    """Step 4: ink + realistic 场域式小规模验证"""
    total_start = datetime.now()
    project_id = total_start.strftime("%Y%m%d_%H%M%S")
    project_dir = os.path.join(OUTPUT_BASE, project_id)
    os.makedirs(project_dir, exist_ok=True)

    print("=" * 70)
    print("Step 4: ink + realistic 场域式小规模验证")
    print("=" * 70)
    print(f"Project ID: {project_id}")
    print(f"Story idea: {STORY_IDEA}")
    print(f"Styles: {', '.join(STYLES)}")
    print(f"Shots per style: {SHOTS_PER_STYLE}")
    print(f"Model: Stage 1-4 Sonnet 4.6 / Stage 5 NB2")
    print(f"use_native_text: True | aspect_ratio: 2:3")
    print(f"Output: {project_dir}")
    print("=" * 70)

    # ============================================================
    # Stage 1: 故事大纲 (共享)
    # ============================================================
    print(f"\n{'='*50}")
    print("Stage 1: 生成故事大纲 (共享)")
    print(f"{'='*50}")

    s1_start = time.time()
    outline_gen = StoryOutlineGenerator()
    outline = await outline_gen.generate(
        idea=STORY_IDEA,
        style_preset="illustration",
        target_duration_minutes=1,
        language="zh-CN",
        character_count=2
    )
    s1_time = time.time() - s1_start
    save_json(os.path.join(project_dir, "1_outline.json"), outline)
    print(f"✅ Stage 1 ({s1_time:.1f}s): {outline.get('title', 'N/A')}")

    char_overview = outline.get("characters_overview", [])
    if char_overview:
        for c in char_overview:
            print(f"  - {c.get('name', '?')}: {c.get('role', '?')}")

    # ============================================================
    # Stage 2: 角色设计 (共享)
    # ============================================================
    print(f"\n{'='*50}")
    print("Stage 2: 设计角色 (共享)")
    print(f"{'='*50}")

    s2_start = time.time()
    char_designer = CharacterDesigner()
    characters = await char_designer.design(outline)
    s2_time = time.time() - s2_start
    save_json(os.path.join(project_dir, "2_characters.json"), characters)
    char_names = [c.get("name", "?") for c in characters.get("characters", [])]
    print(f"✅ Stage 2 ({s2_time:.1f}s): {', '.join(char_names)}")

    # ============================================================
    # Stage 3: 分场剧本 (共享)
    # ============================================================
    print(f"\n{'='*50}")
    print("Stage 3: 编写分场剧本 (共享)")
    print(f"{'='*50}")

    s3_start = time.time()
    screenplay_writer = ScreenplayWriter()
    screenplay = await screenplay_writer.write(outline, characters)
    s3_time = time.time() - s3_start
    save_json(os.path.join(project_dir, "3_screenplay.json"), screenplay)
    scene_count = len(screenplay.get("scenes", []))
    print(f"✅ Stage 3 ({s3_time:.1f}s): {scene_count} 场戏")

    # ============================================================
    # Stage 4 + 5: per style (ink → realistic)
    # ============================================================
    all_style_results = {}

    for style in STYLES:
        result = await generate_shots_for_style(
            style_preset=style,
            screenplay=screenplay,
            characters=characters,
            outline=outline,
            output_dir=project_dir
        )
        all_style_results[style] = result

    # ============================================================
    # 汇总
    # ============================================================
    end_time = datetime.now()
    total_seconds = (end_time - total_start).total_seconds()

    summary = {
        "task": "Step 4: ink + realistic 场域式小规模验证",
        "project_id": project_id,
        "story_idea": STORY_IDEA,
        "story_title": outline.get("title", ""),
        "characters": char_names,
        "styles": STYLES,
        "shots_per_style": SHOTS_PER_STYLE,
        "model": {
            "stage_1_4": "Claude Sonnet 4.6",
            "stage_5": "NB2 (gemini-3.1-flash-image-preview)"
        },
        "use_native_text": True,
        "aspect_ratio": "2:3",
        "shared_stage_times": {
            "stage1_outline": round(s1_time, 2),
            "stage2_characters": round(s2_time, 2),
            "stage3_screenplay": round(s3_time, 2)
        },
        "style_results": all_style_results,
        "total_duration_seconds": round(total_seconds, 2),
        "total_duration_minutes": round(total_seconds / 60, 1),
        "timestamp": end_time.isoformat()
    }

    save_json(os.path.join(project_dir, "step4_summary.json"), summary)

    # 打印汇总
    print(f"\n{'='*70}")
    print("Step 4 验证完成!")
    print(f"{'='*70}")
    print(f"  故事: {outline.get('title', '?')}")
    print(f"  角色: {', '.join(char_names)}")
    print()

    for style, result in all_style_results.items():
        sc = result["success_count"]
        total = result["shots_generated"]
        avg = result["avg_gen_time"]
        s4t = result["stage4_time"]
        tt = result["total_time"]
        print(f"  [{style:12s}] {sc}/{total} 成功 | 平均 {avg:.1f}s/张 | "
              f"Stage4 {s4t:.1f}s | 总 {tt:.1f}s")
        print(f"               text_type: {result['text_type_distribution']}")

    print(f"\n  总耗时: {total_seconds:.1f}s ({total_seconds/60:.1f}min)")
    print(f"\n  输出目录: {project_dir}/")
    for style in STYLES:
        print(f"    {style}/")
        print(f"      shots/           — shot 图片 (5 张)")
        print(f"      character_refs/  — 角色参考图")
        print(f"      scene_refs/      — 场景参考图")
        print(f"      4_storyboard.json")
        print(f"      results.json")
    print(f"{'='*70}")

    return summary


if __name__ == "__main__":
    asyncio.run(run_style_verify_step4())
