"""
TASK-NB2-TEXT-TEST: NB2 中文渲染 A/B 对比测试

A组: NB2 + no-text prompt + TextOverlay 后处理（当前方案）
B组: NB2 + with-text prompt（模型原生渲染中文）

复用 Stage 1-4 数据和参考图，5 个代表性 shots × 2 组

评估维度:
  1. 中文可读性
  2. 文图融合
  3. 气泡/旁白质量
  4. 跨风格稳定性
  5. 角色一致性

选定 shots:
  Shot 01: thought (心理独白) — "那双手……为什么还在抖。"
  Shot 06: narration (旁白) — "教练没有出声。那种沉默，比任何话都重。"
  Shot 09: dialogue (双对话) — "你投篮的时候，眼睛是闭着的——" + "你怕自己成功。"
  Shot 13: narration_with_thought (混合) — 旁白 + "……林峰。"
  Shot 17: dialogue_with_thought (混合) — "你他妈的，终于。" + "……接住了。"

作者: @Tester
日期: 2026-02-27
"""

import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from PIL import Image
from app.services.image_generator import ImageGenerator
from app.services.text_overlay_service import TextOverlayService


# =========== 配置 ===========
SOURCE_DIR = "./test_output/manualtest/model_upgrade_retest_slamdunk"
E2E_DIR = "./test_output/manualtest/e2e_slamdunk/20260227_140414"
OUTPUT_BASE = "./test_output/manualtest/nb2_text_test"
STYLE_PRESET = "slam_dunk"

# 选定的 5 个代表性 shots（覆盖所有 text_type）
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


def load_json(filepath: str) -> dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(filepath: str, data) -> None:
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def strip_speaker(text: str) -> str:
    """剥离说话者前缀，提取纯文字内容"""
    pattern = r'^[\w\u4e00-\u9fff]+(?:内心|（[^）]*）)?[：:]\s*[「"『]?(.+?)[」"』]?$'
    match = re.match(pattern, text.strip())
    if match:
        return match.group(1)
    return text


def build_text_overlay_prompt(text_overlay: dict) -> str:
    """
    根据 text_overlay 数据构建 TEXT OVERLAY REQUIREMENT 指令块
    用于 B 组 prompt（让 NB2 原生渲染中文文字）
    """
    text_type = text_overlay.get("text_type", "none")
    chinese_text = text_overlay.get("chinese_text", "")
    position = text_overlay.get("speaker_position", "bottom")

    if text_type == "none" or not chinese_text:
        return ""

    blocks = []

    if text_type == "thought":
        text = chinese_text if isinstance(chinese_text, str) else chinese_text[0]
        clean = strip_speaker(text)
        blocks.append(
            f"TEXT OVERLAY REQUIREMENT:\n"
            f"A semi-transparent black bar (at the {position}) spanning the full width of the image, "
            f"height approximately 18% of frame.\n"
            f"Display Chinese text '{clean}' in white font, centered alignment.\n"
            f"The black overlay should have approximately 70-80% opacity, allowing slight visibility of background.\n"
            f"Inner monologue style: represents character's private thoughts."
        )

    elif text_type == "narration":
        text = chinese_text if isinstance(chinese_text, str) else chinese_text[0]
        clean = strip_speaker(text)
        blocks.append(
            f"TEXT OVERLAY REQUIREMENT:\n"
            f"A semi-transparent black bar (at the {position}) spanning the full width of the image, "
            f"height approximately 18% of frame.\n"
            f"Display Chinese text '{clean}' in white font, centered alignment.\n"
            f"The black overlay should have approximately 70-80% opacity.\n"
            f"Narrative caption style: objective narration."
        )

    elif text_type == "dialogue":
        texts = chinese_text if isinstance(chinese_text, list) else [chinese_text]
        for i, txt in enumerate(texts):
            clean = strip_speaker(txt)
            pos_desc = "upper left" if i == 0 else "upper right"
            blocks.append(
                f"TEXT OVERLAY REQUIREMENT (Bubble {i+1}):\n"
                f"A white rounded rectangular speech bubble positioned {pos_desc} in the frame.\n"
                f"Inside the bubble, display Chinese text '{clean}' in black font, centered alignment.\n"
                f"Speech bubble style: clean white fill, thin black outline (1-2px), rounded corners (radius ~15px),\n"
                f"triangular tail pointing to speaker. Text should be clearly legible against white background."
            )

    elif text_type in ["dialogue_with_thought", "narration_with_thought",
                        "narration_with_dialogue", "dialogue_with_narration"]:
        texts = chinese_text if isinstance(chinese_text, list) else [chinese_text]
        bubble_idx = 0
        for i, txt in enumerate(texts):
            clean = strip_speaker(txt)
            if "内心" in txt:
                blocks.append(
                    f"TEXT OVERLAY REQUIREMENT ({i+1} - Inner monologue):\n"
                    f"A semi-transparent black bar (at the bottom) spanning the full width, "
                    f"height approximately 15% of frame.\n"
                    f"Display Chinese text '{clean}' in white font, centered.\n"
                    f"The overlay should have approximately 70-80% opacity."
                )
            elif "旁白" in txt or txt.startswith("「"):
                blocks.append(
                    f"TEXT OVERLAY REQUIREMENT ({i+1} - Narration):\n"
                    f"A semi-transparent black bar (at the bottom) spanning the full width, "
                    f"height approximately 15% of frame.\n"
                    f"Display Chinese text '{clean}' in white font, centered.\n"
                    f"The overlay should have approximately 70-80% opacity."
                )
            elif "：「" in txt or ":「" in txt:
                pos_desc = "upper left" if bubble_idx == 0 else "upper right"
                blocks.append(
                    f"TEXT OVERLAY REQUIREMENT ({i+1} - Dialogue bubble):\n"
                    f"A white rounded rectangular speech bubble positioned {pos_desc}.\n"
                    f"Inside the bubble, display Chinese text '{clean}' in black font, centered.\n"
                    f"Speech bubble style: clean white fill, black outline, rounded corners, tail pointing to speaker."
                )
                bubble_idx += 1

    return "\n\n".join(blocks)


def load_reference_images(
    char_ids: List[str],
    scene_id: int,
    char_refs_dir: str,
    scene_refs_dir: str
) -> List[Image.Image]:
    """加载角色参考图和场景参考图"""
    refs = []

    # 角色参考图：portrait + fullbody（与 pipeline 一致）
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
        for fname in os.listdir(scene_refs_dir):
            if location_id in fname and fname.endswith('.png'):
                refs.append(Image.open(os.path.join(scene_refs_dir, fname)))

    return refs


async def run_nb2_text_test():
    """运行 NB2 中文渲染 A/B 对比测试"""
    start_time = datetime.now()
    project_id = start_time.strftime("%Y%m%d_%H%M%S")
    project_dir = os.path.join(OUTPUT_BASE, project_id)

    # 创建输出目录
    group_a_dir = os.path.join(project_dir, "group_a_textoverlay")
    group_b_dir = os.path.join(project_dir, "group_b_native")
    group_a_raw_dir = os.path.join(project_dir, "group_a_raw")
    for d in [group_a_dir, group_b_dir, group_a_raw_dir]:
        os.makedirs(d, exist_ok=True)

    print("=" * 70)
    print("TASK-NB2-TEXT-TEST: NB2 中文渲染 A/B 对比测试")
    print("=" * 70)
    print(f"Project ID: {project_id}")
    print(f"Selected shots: {SELECTED_SHOTS}")
    print(f"Style: {STYLE_PRESET}")
    print(f"Model: gemini-3.1-flash-image-preview (NB2)")
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

    print(f"  故事: {outline.get('title', '?')}")
    print(f"  角色: {len(char_list)}, 镜头: {len(shots)}")

    # 2. 初始化服务
    image_generator = ImageGenerator()
    text_overlay_service = TextOverlayService()

    # 参考图目录（复用 E2E 测试的参考图）
    char_refs_dir = os.path.join(E2E_DIR, "character_refs")
    scene_refs_dir = os.path.join(E2E_DIR, "scene_refs")

    if not os.path.exists(char_refs_dir):
        print(f"❌ 参考图目录不存在: {char_refs_dir}")
        return None

    # 3. 选择 shots
    selected = [s for s in shots if s.get("shot_id") in SELECTED_SHOTS]
    print(f"\n  已选择 {len(selected)} 个 shots:")
    for s in selected:
        text_overlay = s.get("text_overlay", {})
        text_type = text_overlay.get("text_type", "none")
        chinese_text = text_overlay.get("chinese_text", "")
        text_preview = str(chinese_text)[:60] + "..." if len(str(chinese_text)) > 60 else str(chinese_text)
        print(f"    Shot {s['shot_id']:02d}: {text_type:25s} | {text_preview}")

    # 4. 逐 shot 生成 A/B 两组
    results = []

    for shot in selected:
        shot_id = shot.get("shot_id")
        text_overlay = shot.get("text_overlay", {})
        text_type = text_overlay.get("text_type", "none")

        print(f"\n{'='*60}")
        print(f"Shot {shot_id:02d} ({text_type})")
        print(f"{'='*60}")

        # 获取参考图
        char_direction = shot.get("character_direction", {})
        chars_in_scene = char_direction.get("characters_visible", [])
        scene_id = shot.get("scene_id")

        ref_images = load_reference_images(
            chars_in_scene, scene_id,
            char_refs_dir, scene_refs_dir
        )
        print(f"  参考图: {len(ref_images)} 张 (角色: {chars_in_scene})")

        shot_result = {
            "shot_id": shot_id,
            "text_type": text_type,
            "chinese_text": text_overlay.get("chinese_text", ""),
            "group_a": None,
            "group_b": None
        }

        # ========== A 组: NB2 + no-text prompt + TextOverlay ==========
        print(f"\n  [A组] NB2 + TextOverlay 后处理...")

        a_start = time.time()
        a_result = await image_generator.generate_shot_image_phase2(
            shot=shot,
            storyboard=storyboard,
            characters=characters,
            style_preset=STYLE_PRESET,
            reference_images=ref_images,
            previous_shot_image=None,
            previous_shot=None,
            screenplay=screenplay,
            aspect_ratio="2:3"
        )
        a_gen_time = time.time() - a_start

        if a_result.get("success"):
            raw_image = a_result["pil_image"]

            # 保存无文字原图
            raw_path = os.path.join(group_a_raw_dir, f"shot_{shot_id:02d}_raw.png")
            raw_image.save(raw_path)

            # 应用 TextOverlay 后处理
            with_text_image = text_overlay_service.process_shot(
                raw_image.copy(), text_overlay,
                characters_in_scene=chars_in_scene,
                characters_data=char_list
            )
            a_path = os.path.join(group_a_dir, f"shot_{shot_id:02d}.png")
            with_text_image.save(a_path)

            print(f"    ✅ A组成功 ({a_gen_time:.1f}s, {raw_image.size[0]}x{raw_image.size[1]})")
            shot_result["group_a"] = {
                "success": True,
                "generation_time": round(a_gen_time, 2),
                "size": f"{raw_image.size[0]}x{raw_image.size[1]}",
                "raw_path": raw_path,
                "with_text_path": a_path
            }
        else:
            print(f"    ❌ A组失败: {a_result.get('error', '?')}")
            shot_result["group_a"] = {
                "success": False,
                "error": a_result.get("error", "Unknown")
            }

        # 等待避免限流
        await asyncio.sleep(3)

        # ========== B 组: NB2 + with-text prompt (原生渲染) ==========
        print(f"\n  [B组] NB2 原生中文渲染...")

        # 构建 B 组 prompt：原始 image_prompt + TEXT OVERLAY REQUIREMENT
        text_block = build_text_overlay_prompt(text_overlay)

        # 保存 B 组 prompt 用于调试
        prompt_debug_path = os.path.join(project_dir, f"b_prompt_shot_{shot_id:02d}.txt")
        with open(prompt_debug_path, 'w', encoding='utf-8') as f:
            f.write(f"=== Shot {shot_id} B组 Prompt (原始 image_prompt + TEXT OVERLAY) ===\n\n")
            f.write(f"--- 原始 image_prompt ---\n{shot['image_prompt']}\n\n")
            f.write(f"--- TEXT OVERLAY REQUIREMENT ---\n{text_block}\n")

        # 创建 B 组 shot（修改 image_prompt 以包含文字指令）
        b_shot = shot.copy()
        b_shot["image_prompt"] = shot["image_prompt"] + "\n\n" + text_block

        b_start = time.time()
        b_result = await image_generator.generate_shot_image_phase2(
            shot=b_shot,
            storyboard=storyboard,
            characters=characters,
            style_preset=STYLE_PRESET,
            reference_images=ref_images,
            previous_shot_image=None,
            previous_shot=None,
            screenplay=screenplay,
            aspect_ratio="2:3"
        )
        b_gen_time = time.time() - b_start

        if b_result.get("success"):
            b_image = b_result["pil_image"]
            b_path = os.path.join(group_b_dir, f"shot_{shot_id:02d}.png")
            b_image.save(b_path)

            print(f"    ✅ B组成功 ({b_gen_time:.1f}s, {b_image.size[0]}x{b_image.size[1]})")
            shot_result["group_b"] = {
                "success": True,
                "generation_time": round(b_gen_time, 2),
                "size": f"{b_image.size[0]}x{b_image.size[1]}",
                "image_path": b_path,
                "text_prompt_preview": text_block[:200] + "..." if len(text_block) > 200 else text_block
            }
        else:
            print(f"    ❌ B组失败: {b_result.get('error', '?')}")
            shot_result["group_b"] = {
                "success": False,
                "error": b_result.get("error", "Unknown")
            }

        results.append(shot_result)
        await asyncio.sleep(3)  # 避免限流

    # 5. 保存结果 JSON
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    a_success = sum(1 for r in results if r.get("group_a", {}).get("success"))
    b_success = sum(1 for r in results if r.get("group_b", {}).get("success"))

    a_times = [r["group_a"]["generation_time"] for r in results if r.get("group_a", {}).get("success")]
    b_times = [r["group_b"]["generation_time"] for r in results if r.get("group_b", {}).get("success")]

    summary = {
        "task": "TASK-NB2-TEXT-TEST",
        "project_id": project_id,
        "project_dir": project_dir,
        "model": "gemini-3.1-flash-image-preview (NB2)",
        "style_preset": STYLE_PRESET,
        "selected_shots": SELECTED_SHOTS,
        "total_shots": len(selected),
        "group_a": {
            "name": "NB2 + TextOverlay 后处理",
            "success_count": a_success,
            "avg_generation_time": round(sum(a_times) / len(a_times), 2) if a_times else 0,
        },
        "group_b": {
            "name": "NB2 原生中文渲染",
            "success_count": b_success,
            "avg_generation_time": round(sum(b_times) / len(b_times), 2) if b_times else 0,
        },
        "pipeline_duration_seconds": round(duration, 2),
        "timestamp": end_time.isoformat(),
        "results": results
    }
    save_json(os.path.join(project_dir, "nb2_text_test_results.json"), summary)

    # 6. 打印汇总
    print(f"\n{'='*70}")
    print("TASK-NB2-TEXT-TEST 生成完成!")
    print(f"{'='*70}")
    print(f"  输出目录: {project_dir}")
    print(f"  A组 (TextOverlay): {a_success}/{len(selected)} 成功, 平均 {summary['group_a']['avg_generation_time']:.1f}s")
    print(f"  B组 (原生渲染):    {b_success}/{len(selected)} 成功, 平均 {summary['group_b']['avg_generation_time']:.1f}s")
    print(f"  总耗时: {duration:.1f}秒")
    print(f"\n  📁 A组结果: {group_a_dir}/")
    print(f"  📁 A组原图: {group_a_raw_dir}/")
    print(f"  📁 B组结果: {group_b_dir}/")
    print(f"{'='*70}")

    return summary


if __name__ == "__main__":
    asyncio.run(run_nb2_text_test())
