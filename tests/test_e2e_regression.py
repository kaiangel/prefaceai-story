"""
TASK-E2E-REGRESSION: 综合 E2E 回归测试

2 组故事 x 10 shots，不同题材+风格，完整 Stage 1->5 pipeline。
7 维度验收: 成功率 / 角色一致性 / 风格一致性 / 对话气泡 / speaker_format / text_language / 场景准确性

覆盖变更:
- TASK-PROMPT-BUBBLE 全链路 (build_dialogue_scene_embed)
- speaker_format='english' + text_language='zh-CN'
- SQ-1~SQ-8 shot 质量改进
- DEC-014 previous_shot_image 移除
- System Instruction 精简 + Quality Suffix 禁用

作者: @Tester
日期: 2026-03-06
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from app.services.pipeline_orchestrator import Phase2PipelineOrchestrator


# 测试配置
TEST_STORIES = [
    {
        "group": "A",
        "label": "都市情感 / illustration",
        "idea": "深夜便利店，一个独居程序员和便利店夜班女孩，从每晚的一碗关东煮开始的温暖故事",
        "style_preset": "illustration",
        "character_count": 2,
    },
    {
        "group": "B",
        "label": "古装武侠 / ink",
        "idea": "江湖传闻中的神秘剑客，为了寻找失踪的师父，踏上了一段充满恩怨的武林之旅",
        "style_preset": "ink",
        "character_count": 3,
    },
]

SHOTS_LIMIT = 10
OUTPUT_BASE = "./test_output/manualtest/e2e_regression"


async def run_single_story(story_config: dict, output_base: str) -> dict:
    """运行单组故事的完整 Stage 1->5 pipeline"""
    group = story_config["group"]
    label = story_config["label"]

    print(f"\n{'='*70}")
    print(f"  Story {group}: {label}")
    print(f"  Idea: {story_config['idea']}")
    print(f"  Shots limit: {SHOTS_LIMIT}")
    print(f"{'='*70}\n")

    orchestrator = Phase2PipelineOrchestrator(
        output_dir=os.path.join(output_base, f"story_{group}")
    )

    start_time = time.time()

    result = await orchestrator.run(
        idea=story_config["idea"],
        style_preset=story_config["style_preset"],
        target_duration_minutes=3,
        character_count=story_config["character_count"],
        generate_images=True,
        shots_limit=SHOTS_LIMIT,
    )

    elapsed = time.time() - start_time

    # 收集结果摘要
    summary = {
        "group": group,
        "label": label,
        "idea": story_config["idea"],
        "style_preset": story_config["style_preset"],
        "success": result.get("success", False),
        "elapsed_seconds": round(elapsed, 1),
    }

    if result.get("success"):
        r_summary = result["summary"]
        summary.update({
            "project_dir": r_summary["project_dir"],
            "title": r_summary["title"],
            "total_characters": r_summary["total_characters"],
            "total_scenes": r_summary["total_scenes"],
            "total_shots": r_summary["total_shots"],
        })

        # 统计图像生成结果
        images = result.get("stage_results", {}).get("images", [])
        success_count = sum(1 for img in images if img.get("success"))
        with_text_count = sum(1 for img in images if img.get("with_text_path"))
        summary["images_success"] = success_count
        summary["images_total"] = len(images)
        summary["with_text_count"] = with_text_count

        # 提取 storyboard 用于 prompt 分析
        storyboard = result.get("stage_results", {}).get("storyboard", {})
        shots = storyboard.get("shots", [])[:SHOTS_LIMIT]
        summary["shots_data"] = shots
        summary["characters_data"] = result.get("stage_results", {}).get("characters", {})
    else:
        summary["error"] = result.get("error", "Unknown")
        summary["failed_stage"] = result.get("failed_stage", "Unknown")

    return summary


def analyze_dialogue_bubbles(shots: list) -> dict:
    """分析 shots 中对话气泡相关数据"""
    total = len(shots)
    dialogue_shots = 0
    dialogue_types = {}

    for shot in shots:
        text_overlay = shot.get("text_overlay", {})
        text_type = text_overlay.get("text_type", "none")
        dialogue_types[text_type] = dialogue_types.get(text_type, 0) + 1

        if "dialogue" in text_type:
            dialogue_shots += 1

    return {
        "total_shots": total,
        "dialogue_shots": dialogue_shots,
        "dialogue_ratio": f"{dialogue_shots}/{total} ({dialogue_shots/total*100:.0f}%)" if total > 0 else "N/A",
        "type_distribution": dialogue_types,
    }


def analyze_speaker_format(shots: list, characters: dict) -> dict:
    """分析 speaker_format=english 是否在 prompt 中体现"""
    char_list = characters.get("characters", [])
    name_en_map = {}
    for c in char_list:
        name_zh = c.get("name", "")
        name_en = c.get("name_en", "")
        if name_zh and name_en:
            name_en_map[name_zh] = name_en

    results = []
    for shot in shots:
        text_overlay = shot.get("text_overlay", {})
        text_type = text_overlay.get("text_type", "none")
        if "dialogue" not in text_type:
            continue

        chinese_text = text_overlay.get("chinese_text", "")
        texts = chinese_text if isinstance(chinese_text, list) else [chinese_text]

        for txt in texts:
            if isinstance(txt, dict):
                txt = txt.get("text", "")
            # 检测是否有说话者标记
            for sep in ["：「", ":「", "：\"", ":\"", "："]:
                if sep in txt:
                    speaker_zh = txt.split(sep)[0].strip()
                    expected_en = name_en_map.get(speaker_zh, speaker_zh)
                    results.append({
                        "shot_id": shot.get("shot_id"),
                        "speaker_zh": speaker_zh,
                        "expected_en": expected_en,
                        "has_en_name": speaker_zh in name_en_map,
                    })
                    break

    return {
        "total_dialogue_lines": len(results),
        "speakers_with_en_name": sum(1 for r in results if r["has_en_name"]),
        "details": results[:10],  # 只记录前10条
        "name_en_map": name_en_map,
    }


def generate_report(results: list, output_dir: str):
    """生成对比报告"""
    report_path = os.path.join(output_dir, "comparison_report.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# TASK-E2E-REGRESSION 对比报告",
        f"",
        f"> 生成时间: {timestamp}",
        f"> 测试脚本: `tests/test_e2e_regression.py`",
        f"",
        f"---",
        f"",
        f"## 测试概况",
        f"",
        f"| 项 | Story A | Story B |",
        f"|-----|---------|---------|",
    ]

    for key in ["label", "idea", "style_preset", "title", "total_characters",
                 "total_scenes", "total_shots", "images_success", "images_total",
                 "with_text_count", "elapsed_seconds"]:
        a_val = results[0].get(key, "N/A") if len(results) > 0 else "N/A"
        b_val = results[1].get(key, "N/A") if len(results) > 1 else "N/A"
        lines.append(f"| {key} | {a_val} | {b_val} |")

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 维度 1: 成功率",
        f"",
    ])

    for r in results:
        group = r.get("group", "?")
        success = r.get("images_success", 0)
        total = r.get("images_total", 0)
        rate = f"{success}/{total} ({success/total*100:.0f}%)" if total > 0 else "N/A"
        lines.append(f"- **Story {group}**: {rate}")

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 维度 4: 对话气泡分析",
        f"",
    ])

    for r in results:
        group = r.get("group", "?")
        shots = r.get("shots_data", [])
        if shots:
            bubble_info = analyze_dialogue_bubbles(shots)
            lines.append(f"### Story {group}")
            lines.append(f"- 对话 shots: {bubble_info['dialogue_ratio']}")
            lines.append(f"- 类型分布: {bubble_info['type_distribution']}")
            lines.append(f"")

    lines.extend([
        f"---",
        f"",
        f"## 维度 5: speaker_format=english 分析",
        f"",
    ])

    for r in results:
        group = r.get("group", "?")
        shots = r.get("shots_data", [])
        chars = r.get("characters_data", {})
        if shots and chars:
            speaker_info = analyze_speaker_format(shots, chars)
            lines.append(f"### Story {group}")
            lines.append(f"- 对话行数: {speaker_info['total_dialogue_lines']}")
            lines.append(f"- 有英文名映射: {speaker_info['speakers_with_en_name']}")
            lines.append(f"- 角色名映射: {speaker_info['name_en_map']}")
            lines.append(f"")

    lines.extend([
        f"---",
        f"",
        f"## 维度 2/3/6/7: 需人工检查",
        f"",
        f"以下维度需要 PM/Founder 查看图片后评分:",
        f"",
        f"| # | 维度 | Story A | Story B |",
        f"|---|------|---------|---------|",
        f"| 2 | 角色一致性 | __ /5 | __ /5 |",
        f"| 3 | 风格一致性 | __ /5 | __ /5 |",
        f"| 6 | text_language=zh-CN | __ | __ |",
        f"| 7 | 场景描述准确性 | __ /5 | __ /5 |",
        f"",
        f"---",
        f"",
        f"## 图片路径",
        f"",
    ])

    for r in results:
        group = r.get("group", "?")
        pdir = r.get("project_dir", "N/A")
        lines.append(f"- **Story {group}**: `{pdir}`")
        lines.append(f"  - 无文字原图: `{pdir}/images/`")
        lines.append(f"  - 带文字版: `{pdir}/with_text_images/`")
        lines.append(f"  - 角色参考图: `{pdir}/character_refs/`")
        lines.append(f"  - 场景参考图: `{pdir}/scene_refs/`")

    lines.extend([
        f"",
        f"---",
        f"",
        f"*报告由 test_e2e_regression.py 自动生成*",
    ])

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n报告已保存: {report_path}")
    return report_path


async def main():
    print("=" * 70)
    print("  TASK-E2E-REGRESSION: 综合 E2E 回归测试")
    print("  2 stories x 10 shots | 7 维度验收")
    print("=" * 70)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(OUTPUT_BASE, timestamp)
    os.makedirs(output_dir, exist_ok=True)

    results = []

    for story in TEST_STORIES:
        try:
            result = await run_single_story(story, output_dir)
            results.append(result)
        except Exception as e:
            print(f"\n{'!'*70}")
            print(f"  Story {story['group']} FAILED: {e}")
            print(f"{'!'*70}")
            import traceback
            traceback.print_exc()
            results.append({
                "group": story["group"],
                "label": story["label"],
                "success": False,
                "error": str(e),
            })

    # 保存原始结果 (去掉 shots_data 和 characters_data 避免过大)
    results_for_save = []
    for r in results:
        r_save = {k: v for k, v in r.items() if k not in ("shots_data", "characters_data")}
        results_for_save.append(r_save)

    results_json_path = os.path.join(output_dir, "results_summary.json")
    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump(results_for_save, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存: {results_json_path}")

    # 生成对比报告
    report_path = generate_report(results, output_dir)

    # 最终摘要
    print(f"\n{'='*70}")
    print(f"  E2E REGRESSION 测试完成")
    print(f"{'='*70}")
    for r in results:
        group = r.get("group", "?")
        if r.get("success"):
            success = r.get("images_success", 0)
            total = r.get("images_total", 0)
            elapsed = r.get("elapsed_seconds", 0)
            print(f"  Story {group}: {success}/{total} shots | {elapsed:.0f}s | {r.get('title', 'N/A')}")
        else:
            print(f"  Story {group}: FAILED — {r.get('error', 'Unknown')}")

    print(f"\n  输出目录: {output_dir}")
    print(f"  对比报告: {report_path}")
    print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
