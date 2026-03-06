"""
TASK-PROMPT-BUBBLE-FOLLOWUP 任务 2: Near {speaker} 命名格式 A/B/C 对比

使用 dialogue_dense_illustration 的 10 shots（含对话），分别用三种命名格式生图对比：
- A 组: 中文名（Near 顾建国）— 当前实现
- B 组: 英文名（Near Gu Jianguo）
- C 组: char_ID（Near char_002）

对比维度: 气泡出现率、气泡位置准确性、台词内容正确性

运行: python tests/test_speaker_format_abc.py
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


SOURCE_DIR = "./test_output/manualtest/prompt_bubble/dialogue_dense_illustration"
OUTPUT_BASE = "./test_output/manualtest/prompt_bubble/speaker_format_test"

FORMATS = [
    {"name": "A_chinese", "format": "chinese", "label": "A 组 (中文名)"},
    {"name": "B_english", "format": "english", "label": "B 组 (英文名)"},
    {"name": "C_char_id", "format": "char_id", "label": "C 组 (char_ID)"},
]

MAX_SHOTS = 10


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def run_group(group_config, test_shots, storyboard, characters, screenplay, style_preset):
    """运行一组测试"""
    from app.services.image_generator import ImageGenerator, build_dialogue_scene_embed
    from app.services.reference_image_manager import ReferenceImageManager
    from app.services.scene_reference_manager import SceneReferenceManager
    from app.models.style_config import ProjectStyleConfig

    group_name = group_config["name"]
    speaker_format = group_config["format"]
    label = group_config["label"]
    chars_list = characters.get("characters", [])

    print(f"\n{'='*60}")
    print(f"{label} — speaker_format='{speaker_format}'")
    print(f"{'='*60}")

    # 创建输出目录
    group_dir = os.path.join(OUTPUT_BASE, group_name)
    images_dir = os.path.join(group_dir, "images")
    prompts_dir = os.path.join(group_dir, "prompts")
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(prompts_dir, exist_ok=True)

    # 初始化
    image_generator = ImageGenerator()
    project_style = ProjectStyleConfig(style_preset=style_preset)
    ref_manager = ReferenceImageManager()
    scene_ref_manager = SceneReferenceManager()

    # 生成参考图（每组共用，只生成第一组时做）
    ref_cache_file = os.path.join(OUTPUT_BASE, "_refs_generated.flag")
    if not os.path.exists(ref_cache_file):
        print(f"\n--- 生成参考图 (仅首次) ---")

        outline = load_json(os.path.join(SOURCE_DIR, "1_outline.json"))

        for char in chars_list:
            print(f"  生成 {char.get('name', '?')}...", end=" ")
            try:
                await ref_manager.generate_character_multi_refs(
                    character=char,
                    project_style=project_style,
                    image_generator=image_generator
                )
                print("✅")
            except Exception as e:
                print(f"❌ {e}")

        unique_locations = outline.get("unique_locations", [])
        if unique_locations:
            try:
                await scene_ref_manager.generate_anchor_images(
                    scenes=[],
                    project_style=project_style,
                    image_generator=image_generator,
                    unique_locations=unique_locations,
                    delay=3.0
                )
                print("  ✅ 场景参考图完成")
            except Exception as e:
                print(f"  ❌ 场景参考图: {e}")

        with open(ref_cache_file, "w") as f:
            f.write("done")

    # 生成 shots
    print(f"\n--- 生成 {len(test_shots)} shots ({label}) ---")
    results = []
    start_time = datetime.now()

    for i, shot in enumerate(test_shots):
        shot_id = shot.get("shot_id", i + 1)
        text_type = shot.get("text_overlay", {}).get("text_type", "none")

        # 用指定格式生成对话嵌入文本（预览）
        dialogue_embed = build_dialogue_scene_embed(
            shot.get("text_overlay", {}),
            characters=chars_list,
            speaker_format=speaker_format
        )

        print(f"\n  Shot {shot_id} (text_type={text_type})")
        if dialogue_embed:
            print(f"    嵌入: {dialogue_embed[:100]}...")

        # 参考图
        chars_in_scene = shot.get("character_direction", {}).get("characters_visible", [])
        char_refs = ref_manager.get_references_for_scene(chars_in_scene)
        location_id = shot.get("location_id", "")
        scene_refs = scene_ref_manager.get_references_for_location(location_id) if location_id else []
        all_refs = char_refs + scene_refs

        try:
            # 临时 monkey-patch build_dialogue_scene_embed 传入 characters 和 speaker_format
            # 因为 generate_shot_image_phase2 内部调用 build_dialogue_scene_embed 不传这些参数
            # 我们需要在 shot 数据中临时存储格式信息
            import app.services.image_generator as img_mod
            original_func = img_mod.build_dialogue_scene_embed

            def patched_embed(text_overlay, characters=None, speaker_format_arg="chinese"):
                return original_func(text_overlay, characters=chars_list, speaker_format=speaker_format)

            img_mod.build_dialogue_scene_embed = patched_embed

            result = await image_generator.generate_shot_image_phase2(
                shot=shot,
                storyboard=storyboard,
                characters=characters,
                style_preset=style_preset,
                reference_images=all_refs,
                screenplay=screenplay,
                aspect_ratio="2:3",
                use_native_text=True
            )

            # 恢复原函数
            img_mod.build_dialogue_scene_embed = original_func

            if result.get("success"):
                img_path = os.path.join(images_dir, f"shot_{shot_id:02d}.png")
                result["pil_image"].save(img_path)
                print(f"    ✅ 已保存")

                results.append({
                    "shot_id": shot_id,
                    "text_type": text_type,
                    "dialogue_embedded": bool(dialogue_embed),
                    "dialogue_text": dialogue_embed[:120] if dialogue_embed else "",
                    "success": True,
                })
            else:
                print(f"    ❌ 失败: {result.get('error', 'unknown')}")
                results.append({
                    "shot_id": shot_id,
                    "text_type": text_type,
                    "success": False,
                    "error": result.get("error", "unknown"),
                })
        except Exception as e:
            print(f"    ❌ 异常: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "shot_id": shot_id,
                "text_type": text_type,
                "success": False,
                "error": str(e),
            })

        await asyncio.sleep(1)

    elapsed = (datetime.now() - start_time).total_seconds()

    # 保存结果
    with open(os.path.join(group_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    total = len(results)
    success = sum(1 for r in results if r.get("success"))
    dialogue_count = sum(1 for r in results if r.get("dialogue_embedded"))
    dialogue_success = sum(1 for r in results if r.get("dialogue_embedded") and r.get("success"))

    print(f"\n--- {label} 统计 ---")
    print(f"  成功: {success}/{total}")
    print(f"  对话嵌入: {dialogue_count}, 成功: {dialogue_success}/{dialogue_count}")
    print(f"  耗时: {elapsed:.0f}s")

    return {
        "group_name": group_name,
        "label": label,
        "speaker_format": speaker_format,
        "total": total,
        "success": success,
        "dialogue_count": dialogue_count,
        "dialogue_success": dialogue_success,
        "elapsed": elapsed,
        "results": results,
    }


def generate_report(all_results):
    """生成 A/B/C 对比报告"""
    lines = [
        "# TASK-PROMPT-BUBBLE-FOLLOWUP 任务 2: Near {speaker} 命名格式 A/B/C 对比",
        "",
        f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"测试数据: dialogue_dense_illustration (illustration 风格, 10 shots)",
        "",
        "## 测试设计",
        "",
        "| 组 | speaker_format | 示例 |",
        "|---|---|---|",
        "| A | chinese (当前) | Near 顾建国, a white speech bubble... |",
        "| B | english | Near Gu Jianguo, a white speech bubble... |",
        "| C | char_id | Near char_002, a white speech bubble... |",
        "",
        "## 结果汇总",
        "",
        "| 组 | 成功率 | 对话嵌入成功 | 耗时 |",
        "|---|---|---|---|",
    ]

    for r in all_results:
        lines.append(
            f"| {r['label']} | {r['success']}/{r['total']} | "
            f"{r['dialogue_success']}/{r['dialogue_count']} | {r['elapsed']:.0f}s |"
        )

    lines.append("")

    # 每组详情
    for r in all_results:
        lines.append(f"## {r['label']} — speaker_format='{r['speaker_format']}'")
        lines.append("")
        lines.append("| Shot | text_type | 对话嵌入 | 成功 | 嵌入文本 |")
        lines.append("|---|---|---|---|---|")
        for sr in r["results"]:
            embed = "✅" if sr.get("dialogue_embedded") else "-"
            success = "✅" if sr.get("success") else "❌"
            text = sr.get("dialogue_text", "")[:60]
            error = sr.get("error", "")[:40]
            lines.append(f"| {sr['shot_id']} | {sr['text_type']} | {embed} | {success} | {text or error} |")
        lines.append("")

    lines.extend([
        "## 待人工检查维度",
        "",
        "| 维度 | 检查项 |",
        "|---|---|",
        "| 气泡出现率 | 三组中哪组气泡出现最稳定 |",
        "| 气泡定位 | 气泡是否靠近正确说话者 |",
        "| 台词正确性 | 中文文字是否准确 |",
        "| 多说话者场景 | Shot 8 双人对话定位对比 |",
    ])

    return "\n".join(lines)


async def main():
    storyboard = load_json(os.path.join(SOURCE_DIR, "4_storyboard.json"))
    characters = load_json(os.path.join(SOURCE_DIR, "2_characters.json"))
    screenplay = load_json(os.path.join(SOURCE_DIR, "3_screenplay.json"))
    style_preset = "illustration"

    shots = storyboard.get("shots", [])

    # 筛选含对话的 shots 优先
    dialogue_shots = [s for s in shots if s.get("text_overlay", {}).get("text_type", "none") in
                      ["dialogue", "dialogue_with_thought", "narration_with_dialogue", "dialogue_with_narration"]]
    other_shots = [s for s in shots if s not in dialogue_shots]
    test_shots = dialogue_shots[:MAX_SHOTS]
    remaining = MAX_SHOTS - len(test_shots)
    if remaining > 0:
        test_shots.extend(other_shots[:remaining])

    print(f"测试 shots: {len(test_shots)} (含对话: {len([s for s in test_shots if s.get('text_overlay', {}).get('text_type', 'none') != 'none'])})")

    os.makedirs(OUTPUT_BASE, exist_ok=True)

    # 清除之前的参考图标记（强制重新生成）
    ref_flag = os.path.join(OUTPUT_BASE, "_refs_generated.flag")
    if os.path.exists(ref_flag):
        os.remove(ref_flag)

    all_results = []
    total_start = datetime.now()

    for fmt_config in FORMATS:
        r = await run_group(fmt_config, test_shots, storyboard, characters, screenplay, style_preset)
        all_results.append(r)

    total_elapsed = (datetime.now() - total_start).total_seconds()

    # 生成报告
    report = generate_report(all_results)
    report_path = os.path.join(OUTPUT_BASE, "comparison_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n{'='*60}")
    print(f"A/B/C 对比测试完成")
    print(f"总耗时: {total_elapsed:.0f}s")
    print(f"报告: {report_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
