"""
TASK-PROMPT-BUBBLE-FOLLOWUP-R2 任务 A: 补测 A/B/C（修复参考图 bug）

R1 Bug: 每组 new ReferenceImageManager()，但参考图只在第一组生成，
        B/C 组的 ref_manager 实例为空 -> 无参考图。
R2 Fix: 在循环外生成参考图，所有组共用同一个 ref_manager 实例。

控制唯一变量: speaker_format (chinese / english / char_id)
其他条件完全相同: 同一组 shot 数据、同一套参考图、同一风格

运行: python3 tests/test_speaker_format_abc_r2.py
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
OUTPUT_BASE = "./test_output/manualtest/prompt_bubble/speaker_format_test_r2"

FORMATS = [
    {"name": "A_chinese", "format": "chinese", "label": "A (Chinese Name)"},
    {"name": "B_english", "format": "english", "label": "B (English Name)"},
    {"name": "C_char_id", "format": "char_id", "label": "C (char_ID)"},
]

MAX_SHOTS = 10


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def generate_shared_refs(chars_list, outline, style_preset):
    """生成所有组共用的参考图（修复 R1 bug 的核心）"""
    from app.services.image_generator import ImageGenerator
    from app.services.reference_image_manager import ReferenceImageManager
    from app.services.scene_reference_manager import SceneReferenceManager
    from app.models.style_config import ProjectStyleConfig

    image_generator = ImageGenerator()
    project_style = ProjectStyleConfig(style_preset=style_preset)
    ref_manager = ReferenceImageManager()
    scene_ref_manager = SceneReferenceManager()

    print("\n--- Generating shared reference images (all groups use the same refs) ---")
    for char in chars_list:
        name = char.get("name", "?")
        print(f"  {name}...", end=" ", flush=True)
        try:
            await ref_manager.generate_character_multi_refs(
                character=char,
                project_style=project_style,
                image_generator=image_generator
            )
            print("OK")
        except Exception as e:
            print(f"FAIL {e}")

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
            print("  Scene refs: OK")
        except Exception as e:
            print(f"  Scene refs: FAIL {e}")

    # 验证参考图已生成
    total_refs = sum(len(v) for v in ref_manager.character_references.values())
    print(f"  Total character refs in memory: {total_refs} images for {len(ref_manager.character_references)} characters")

    return ref_manager, scene_ref_manager


async def run_group(group_config, test_shots, storyboard, characters, screenplay,
                    style_preset, ref_manager, scene_ref_manager):
    """运行一组测试（使用共享的 ref_manager）"""
    from app.services.image_generator import ImageGenerator, build_dialogue_scene_embed
    import app.services.image_generator as img_mod

    group_name = group_config["name"]
    speaker_format = group_config["format"]
    label = group_config["label"]
    chars_list = characters.get("characters", [])

    print(f"\n{'='*60}")
    print(f"{label} -- speaker_format='{speaker_format}'")
    print(f"{'='*60}")

    # 创建输出目录
    group_dir = os.path.join(OUTPUT_BASE, group_name)
    images_dir = os.path.join(group_dir, "images")
    prompts_dir = os.path.join(group_dir, "prompts")
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(prompts_dir, exist_ok=True)

    image_generator = ImageGenerator()

    # 验证参考图可用
    sample_char_ids = list(ref_manager.character_references.keys())[:3]
    sample_refs = ref_manager.get_references_for_scene(sample_char_ids)
    print(f"  Ref check: {len(sample_refs)} images for {len(sample_char_ids)} chars")

    print(f"\n--- Generating {len(test_shots)} shots ({label}) ---")
    results = []
    start_time = datetime.now()

    # 保存原始函数
    original_func = img_mod.build_dialogue_scene_embed

    for i, shot in enumerate(test_shots):
        shot_id = shot.get("shot_id", i + 1)
        text_type = shot.get("text_overlay", {}).get("text_type", "none")

        # 预览对话嵌入文本
        dialogue_embed = build_dialogue_scene_embed(
            shot.get("text_overlay", {}),
            characters=chars_list,
            speaker_format=speaker_format,
            text_language="zh-CN"
        )

        print(f"\n  Shot {shot_id} (text_type={text_type})")
        if dialogue_embed:
            print(f"    embed: {dialogue_embed[:120]}...")

        # 获取参考图
        chars_in_scene = shot.get("character_direction", {}).get("characters_visible", [])
        char_refs = ref_manager.get_references_for_scene(chars_in_scene)
        location_id = shot.get("location_id", "")
        scene_refs = scene_ref_manager.get_references_for_location(location_id) if location_id else []
        all_refs = char_refs + scene_refs

        print(f"    refs: {len(char_refs)} char + {len(scene_refs)} scene = {len(all_refs)} total")

        try:
            # Monkey-patch: 让生产代码内部调用也使用指定的 speaker_format + text_language
            def patched_embed(text_overlay, characters=None, speaker_format_arg="chinese", text_language="zh-CN"):
                return original_func(
                    text_overlay,
                    characters=chars_list,
                    speaker_format=speaker_format,
                    text_language="zh-CN"
                )

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

                # 保存 prompt 文本
                prompt_path = os.path.join(prompts_dir, f"shot_{shot_id:02d}_prompt.txt")
                full_prompt = result.get("prompt", "")
                if full_prompt:
                    with open(prompt_path, "w", encoding="utf-8") as f:
                        f.write(full_prompt)

                print(f"    OK saved")
                results.append({
                    "shot_id": shot_id,
                    "text_type": text_type,
                    "dialogue_embedded": bool(dialogue_embed),
                    "dialogue_text": dialogue_embed[:150] if dialogue_embed else "",
                    "ref_count": len(all_refs),
                    "success": True,
                })
            else:
                print(f"    FAIL: {result.get('error', 'unknown')}")
                img_mod.build_dialogue_scene_embed = original_func
                results.append({
                    "shot_id": shot_id,
                    "text_type": text_type,
                    "ref_count": len(all_refs),
                    "success": False,
                    "error": result.get("error", "unknown"),
                })
        except Exception as e:
            img_mod.build_dialogue_scene_embed = original_func
            print(f"    ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "shot_id": shot_id,
                "text_type": text_type,
                "ref_count": len(all_refs),
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
    avg_refs = sum(r.get("ref_count", 0) for r in results) / max(total, 1)

    print(f"\n--- {label} stats ---")
    print(f"  Success: {success}/{total}")
    print(f"  Dialogue embedded: {dialogue_count}, success: {dialogue_success}/{dialogue_count}")
    print(f"  Avg refs/shot: {avg_refs:.1f}")
    print(f"  Time: {elapsed:.0f}s")

    return {
        "group_name": group_name,
        "label": label,
        "speaker_format": speaker_format,
        "total": total,
        "success": success,
        "dialogue_count": dialogue_count,
        "dialogue_success": dialogue_success,
        "avg_refs": avg_refs,
        "elapsed": elapsed,
        "results": results,
    }


def generate_report(all_results):
    """生成 A/B/C 对比报告"""
    lines = [
        "# TASK-PROMPT-BUBBLE-FOLLOWUP-R2: Speaker Format A/B/C (with Reference Images)",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Data: dialogue_dense_illustration (illustration, 10 shots)",
        "",
        "## R1 vs R2 Difference",
        "",
        "| | R1 | R2 (this test) |",
        "|---|---|---|",
        "| Reference images | A: yes, B/C: NO (bug) | A/B/C: all YES |",
        "| Language constraint | none | Simplified Chinese (zh-CN) |",
        "| Controlled variable | speaker_format (unfair) | speaker_format (fair) |",
        "",
        "## Results Summary",
        "",
        "| Group | Success | Dialogue Embed | Avg Refs/Shot | Time |",
        "|---|---|---|---|---|",
    ]

    for r in all_results:
        lines.append(
            f"| {r['label']} | {r['success']}/{r['total']} | "
            f"{r['dialogue_success']}/{r['dialogue_count']} | "
            f"{r['avg_refs']:.1f} | {r['elapsed']:.0f}s |"
        )

    lines.append("")

    # 每组详情
    for r in all_results:
        lines.append(f"## {r['label']} (speaker_format='{r['speaker_format']}')")
        lines.append("")
        lines.append("| Shot | text_type | Dialogue | Refs | OK | Embed Text |")
        lines.append("|---|---|---|---|---|---|")
        for sr in r["results"]:
            embed = "Y" if sr.get("dialogue_embedded") else "-"
            success = "Y" if sr.get("success") else "N"
            refs = sr.get("ref_count", 0)
            text = sr.get("dialogue_text", "")[:80]
            error = sr.get("error", "")[:40]
            lines.append(
                f"| {sr['shot_id']} | {sr['text_type']} | {embed} | {refs} | "
                f"{success} | {text or error} |"
            )
        lines.append("")

    lines.extend([
        "## Manual Review Dimensions",
        "",
        "| Dimension | What to check |",
        "|---|---|",
        "| Bubble presence | Which group has most stable bubble rendering |",
        "| Bubble positioning | Bubbles near correct speaker |",
        "| Text accuracy | Chinese text correct, Simplified (not Traditional) |",
        "| Character consistency | With refs, all groups should be consistent |",
        "| Ghost bubbles | C group char_id may cause ghost bubbles (R1 issue) |",
        "| Multi-speaker | Shot 8 dual-dialogue positioning comparison |",
    ])

    return "\n".join(lines)


async def main():
    storyboard = load_json(os.path.join(SOURCE_DIR, "4_storyboard.json"))
    characters = load_json(os.path.join(SOURCE_DIR, "2_characters.json"))
    screenplay = load_json(os.path.join(SOURCE_DIR, "3_screenplay.json"))
    outline = load_json(os.path.join(SOURCE_DIR, "1_outline.json"))
    style_preset = "illustration"

    chars_list = characters.get("characters", [])
    shots = storyboard.get("shots", [])

    # 筛选含对话的 shots 优先
    dialogue_shots = [s for s in shots if s.get("text_overlay", {}).get("text_type", "none") in
                      ["dialogue", "dialogue_with_thought", "narration_with_dialogue", "dialogue_with_narration"]]
    other_shots = [s for s in shots if s not in dialogue_shots]
    test_shots = dialogue_shots[:MAX_SHOTS]
    remaining = MAX_SHOTS - len(test_shots)
    if remaining > 0:
        test_shots.extend(other_shots[:remaining])

    dialogue_in_test = len([s for s in test_shots
                            if s.get("text_overlay", {}).get("text_type", "none") != "none"])
    print(f"Test shots: {len(test_shots)} (with dialogue: {dialogue_in_test})")

    os.makedirs(OUTPUT_BASE, exist_ok=True)

    # R2 FIX: 生成参考图一次，所有组共用
    ref_manager, scene_ref_manager = await generate_shared_refs(chars_list, outline, style_preset)

    all_results = []
    total_start = datetime.now()

    for fmt_config in FORMATS:
        r = await run_group(
            fmt_config, test_shots, storyboard, characters, screenplay,
            style_preset, ref_manager, scene_ref_manager
        )
        all_results.append(r)

    total_elapsed = (datetime.now() - total_start).total_seconds()

    # 生成报告
    report = generate_report(all_results)
    report_path = os.path.join(OUTPUT_BASE, "comparison_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    # 保存汇总 JSON
    summary = {
        "test_name": "TASK-PROMPT-BUBBLE-FOLLOWUP-R2",
        "generated_at": datetime.now().isoformat(),
        "r2_fixes": ["shared ref_manager across groups", "text_language=zh-CN constraint"],
        "total_elapsed": total_elapsed,
        "groups": [{k: v for k, v in r.items() if k != "results"} for r in all_results],
    }
    with open(os.path.join(OUTPUT_BASE, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"R2 A/B/C test complete")
    print(f"Total time: {total_elapsed:.0f}s")
    print(f"Report: {report_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
