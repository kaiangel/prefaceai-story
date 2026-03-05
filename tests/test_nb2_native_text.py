"""
TASK-NB2-NATIVE-TEXT 验证测试

验证 use_native_text=True 开关生效：
- NB2 模型原生渲染中文文字（旁白/对话/心理描述）
- 5 个代表性 shots 覆盖所有 text_type
- 确认图像生成成功 + prompt 中包含 TEXT OVERLAY REQUIREMENT

作者: @Backend
日期: 2026-02-27
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from PIL import Image
from app.services.image_generator import ImageGenerator, build_native_text_prompt


# =========== 配置 ===========
SOURCE_DIR = "./test_output/manualtest/model_upgrade_retest_slamdunk"
E2E_DIR = "./test_output/manualtest/e2e_slamdunk/20260227_140414"
OUTPUT_DIR = "./test_output/manualtest/nb2_native_text_verify"

# 选定的 5 个代表性 shots（覆盖所有 text_type）
SELECTED_SHOTS = [1, 6, 9, 13, 17]

# 场景 → location_id 映射
SCENE_LOCATION_MAP = {
    1: "locker_room_pregame",
    2: "gymnasium_main_court",
    3: "sideline_bench_area",
    4: "gymnasium_main_court",
    5: "gymnasium_main_court",
    6: "gymnasium_main_court",
}


def load_json(filepath: str) -> dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_reference_images(
    char_ids: List[str],
    scene_id: int,
    char_refs_dir: str,
    scene_refs_dir: str
) -> List[Image.Image]:
    """加载角色参考图和场景参考图"""
    refs = []
    for char_id in char_ids:
        portrait_path = os.path.join(char_refs_dir, f"{char_id}_portrait.png")
        fullbody_path = os.path.join(char_refs_dir, f"{char_id}_fullbody.png")
        if os.path.exists(portrait_path):
            refs.append(Image.open(portrait_path))
        if os.path.exists(fullbody_path):
            refs.append(Image.open(fullbody_path))

    location_id = SCENE_LOCATION_MAP.get(scene_id)
    if location_id and os.path.exists(scene_refs_dir):
        for fname in os.listdir(scene_refs_dir):
            if location_id in fname and fname.endswith('.png'):
                refs.append(Image.open(os.path.join(scene_refs_dir, fname)))

    return refs


async def run_verification():
    """运行 NB2 原生文字渲染验证测试"""
    start_time = datetime.now()
    project_id = start_time.strftime("%Y%m%d_%H%M%S")
    project_dir = os.path.join(OUTPUT_DIR, project_id)
    os.makedirs(project_dir, exist_ok=True)

    print("=" * 70)
    print("TASK-NB2-NATIVE-TEXT: 原生文字渲染验证测试")
    print("=" * 70)
    print(f"Project ID: {project_id}")
    print(f"Selected shots: {SELECTED_SHOTS}")
    print(f"Model: gemini-3.1-flash-image-preview (NB2)")
    print(f"use_native_text: True")
    print(f"Output: {project_dir}")
    print("=" * 70)

    # 1. 加载 Stage 1-4 数据
    print("\n--- 加载 Stage 1-4 数据 ---")
    storyboard = load_json(os.path.join(SOURCE_DIR, "4_storyboard.json"))
    characters = load_json(os.path.join(SOURCE_DIR, "2_characters.json"))
    screenplay = load_json(os.path.join(SOURCE_DIR, "3_screenplay.json"))

    shots = storyboard.get("shots", [])
    print(f"  总镜头: {len(shots)}")

    # 2. 初始化
    image_generator = ImageGenerator()
    char_refs_dir = os.path.join(E2E_DIR, "character_refs")
    scene_refs_dir = os.path.join(E2E_DIR, "scene_refs")

    if not os.path.exists(char_refs_dir):
        print(f"  WARNING: 参考图目录不存在: {char_refs_dir}, 将无参考图生成")

    # 3. 选择 shots
    selected = [s for s in shots if s.get("shot_id") in SELECTED_SHOTS]
    print(f"\n  已选择 {len(selected)} 个 shots:")
    for s in selected:
        text_overlay = s.get("text_overlay", {})
        text_type = text_overlay.get("text_type", "none")
        # 验证 build_native_text_prompt 输出
        text_block = build_native_text_prompt(text_overlay)
        has_text = "YES" if text_block else "NO"
        print(f"    Shot {s['shot_id']:02d}: {text_type:25s} | native_prompt={has_text}")

    # 4. 逐 shot 生成
    results = []
    success_count = 0
    gen_times = []

    for shot in selected:
        shot_id = shot.get("shot_id")
        text_overlay = shot.get("text_overlay", {})
        text_type = text_overlay.get("text_type", "none")

        print(f"\n{'='*60}")
        print(f"Shot {shot_id:02d} ({text_type}) - use_native_text=True")
        print(f"{'='*60}")

        # 获取参考图
        char_direction = shot.get("character_direction", {})
        chars_in_scene = char_direction.get("characters_visible", [])
        scene_id = shot.get("scene_id")

        ref_images = load_reference_images(
            chars_in_scene, scene_id,
            char_refs_dir, scene_refs_dir
        )
        print(f"  参考图: {len(ref_images)} 张")

        # 生成（use_native_text=True，NB2 原生渲染中文）
        gen_start = time.time()
        result = await image_generator.generate_shot_image_phase2(
            shot=shot,
            storyboard=storyboard,
            characters=characters,
            style_preset="slam_dunk",
            reference_images=ref_images,
            previous_shot_image=None,
            previous_shot=None,
            screenplay=screenplay,
            aspect_ratio="2:3",
            use_native_text=True
        )
        gen_time = time.time() - gen_start

        if result.get("success"):
            img = result["pil_image"]
            img_path = os.path.join(project_dir, f"shot_{shot_id:02d}.png")
            img.save(img_path)
            success_count += 1
            gen_times.append(gen_time)
            print(f"  OK ({gen_time:.1f}s, {img.size[0]}x{img.size[1]})")
            results.append({
                "shot_id": shot_id,
                "text_type": text_type,
                "success": True,
                "generation_time": round(gen_time, 2),
                "size": f"{img.size[0]}x{img.size[1]}",
                "image_path": img_path
            })
        else:
            print(f"  FAIL: {result.get('error', '?')}")
            results.append({
                "shot_id": shot_id,
                "text_type": text_type,
                "success": False,
                "error": result.get("error", "Unknown")
            })

        await asyncio.sleep(3)

    # 5. 汇总
    duration = (datetime.now() - start_time).total_seconds()
    avg_time = round(sum(gen_times) / len(gen_times), 1) if gen_times else 0

    summary = {
        "task": "TASK-NB2-NATIVE-TEXT-VERIFY",
        "project_id": project_id,
        "model": "gemini-3.1-flash-image-preview (NB2)",
        "use_native_text": True,
        "total_shots": len(selected),
        "success_count": success_count,
        "avg_generation_time": avg_time,
        "total_duration": round(duration, 2),
        "results": results,
        "timestamp": datetime.now().isoformat()
    }

    with open(os.path.join(project_dir, "verify_results.json"), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*70}")
    print("TASK-NB2-NATIVE-TEXT 验证完成!")
    print(f"{'='*70}")
    print(f"  成功: {success_count}/{len(selected)}")
    print(f"  平均生成时间: {avg_time}s")
    print(f"  总耗时: {duration:.1f}s")
    print(f"  输出: {project_dir}/")
    print(f"{'='*70}")

    return summary


if __name__ == "__main__":
    asyncio.run(run_verification())
