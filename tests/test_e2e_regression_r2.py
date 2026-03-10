"""
TASK-E2E-REGRESSION-R2: 综合 E2E 回归验证 (9 维度)

2 组故事 x 10 shots，不同题材+风格，完整 Stage 1->5 pipeline。
9 维度验收:
  1. 生成成功率
  2. text_overlay 输出 (Issue #1 P0 修复验证)
  3. text_type 分布 (dialogue ≥60%)
  4. 对话气泡渲染 (NB2 原生 + speaker_format=english)
  5. text_language=zh-CN (简体中文)
  6. 无标签泄露 (Issue #3 P1)
  7. 无 NB2 乱码文字 (Issue #5 P2)
  8. 手部正常 (Issue #4 P2, 单角色无三手)
  9. 角色/风格一致性 (基线)

覆盖修复:
- Issue #1 [P0] text_overlay 缺失 → schema + mapping rules + dialogue_beats 传入
- Issue #2 [P1] DEC-012 模型配置 → claude-sonnet-4-6 主 / gemini-3-flash-preview 备用
- Issue #3 [P1] SQ-1 标签泄露 → DO NOT reproduce label text
- Issue #4 [P2] 单角色三手 → Rule #9 SINGLE-CHARACTER HAND ACTION LIMIT
- Issue #5 [P2] NB2 乱码文字 → TEXT-FREE system instruction
- TASK-BACKUP-MODEL-FLASH: Stage 1-4 备用统一 gemini-3-flash-preview

作者: @Tester
日期: 2026-03-09
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
        "label": "家庭晚餐争吵 / illustration (对话密集型)",
        "idea": "除夕夜家庭聚餐，父亲宣布要卖掉老宅搬去养老院，三个子女围绕老宅去留、赡养责任、童年记忆展开激烈争论，最终在母亲留下的一道红烧肉面前达成和解",
        "style_preset": "illustration",
        "character_count": 4,
    },
    {
        "group": "B",
        "label": "江湖师徒 / ink (叙事+对话混合)",
        "idea": "年迈的书法大师在山间茅屋教导叛逆少年弟子，从磨墨开始学起，师徒二人在争吵与和解中传承技艺，直到少年在雨夜发现师父偷偷吃药的秘密",
        "style_preset": "ink",
        "character_count": 2,
    },
]

SHOTS_LIMIT = 10
OUTPUT_BASE = "./test_output/manualtest/e2e_regression_r2"


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

        # 提取 storyboard 用于分析
        storyboard = result.get("stage_results", {}).get("storyboard", {})
        shots = storyboard.get("shots", [])[:SHOTS_LIMIT]
        summary["shots_data"] = shots
        summary["characters_data"] = result.get("stage_results", {}).get("characters", {})

        # 提取 screenplay 用于 dialogue_beats 验证
        screenplay = result.get("stage_results", {}).get("screenplay", {})
        summary["screenplay_data"] = screenplay
    else:
        summary["error"] = result.get("error", "Unknown")
        summary["failed_stage"] = result.get("failed_stage", "Unknown")

    return summary


# ═══════════════════════════════════════════════════════════════
# 维度 2: text_overlay 输出分析
# ═══════════════════════════════════════════════════════════════

def analyze_text_overlay_output(shots: list) -> dict:
    """维度 2: 检查每个 shot 是否有 text_overlay 字段"""
    total = len(shots)
    has_overlay = 0
    missing_shots = []
    overlay_details = []

    for shot in shots:
        sid = shot.get("shot_id", "?")
        text_overlay = shot.get("text_overlay")

        if text_overlay and isinstance(text_overlay, dict):
            has_overlay += 1
            overlay_details.append({
                "shot_id": sid,
                "text_type": text_overlay.get("text_type", "MISSING"),
                "has_chinese_text": bool(text_overlay.get("chinese_text")),
                "speaker_position": text_overlay.get("speaker_position", "MISSING"),
            })
        else:
            missing_shots.append(sid)

    return {
        "total_shots": total,
        "has_overlay": has_overlay,
        "coverage": f"{has_overlay}/{total} ({has_overlay/total*100:.0f}%)" if total > 0 else "N/A",
        "missing_shots": missing_shots,
        "pass": has_overlay == total,
        "details": overlay_details,
    }


# ═══════════════════════════════════════════════════════════════
# 维度 3: text_type 分布分析
# ═══════════════════════════════════════════════════════════════

def analyze_text_type_distribution(shots: list) -> dict:
    """维度 3: 检查 text_type 分布是否符合目标"""
    total = len(shots)
    type_counts = {}

    for shot in shots:
        text_overlay = shot.get("text_overlay", {})
        text_type = text_overlay.get("text_type", "none") if isinstance(text_overlay, dict) else "none"
        type_counts[text_type] = type_counts.get(text_type, 0) + 1

    # 计算各类型占比
    ratios = {}
    for t, c in type_counts.items():
        ratios[t] = round(c / total * 100, 1) if total > 0 else 0

    # 判断对话占比 (dialogue + dialogue_with_thought 算对话)
    dialogue_count = type_counts.get("dialogue", 0) + type_counts.get("dialogue_with_thought", 0)
    dialogue_ratio = dialogue_count / total * 100 if total > 0 else 0

    thought_count = type_counts.get("thought", 0)
    thought_ratio = thought_count / total * 100 if total > 0 else 0

    narration_count = type_counts.get("narration", 0)
    narration_ratio = narration_count / total * 100 if total > 0 else 0

    none_count = type_counts.get("none", 0)
    none_ratio = none_count / total * 100 if total > 0 else 0

    # 目标: dialogue ≥60%, thought 10-20%, narration ≤15%, none ≤5%
    checks = {
        "dialogue_ge_60": dialogue_ratio >= 60,
        "narration_le_15": narration_ratio <= 15,
        "none_le_5": none_ratio <= 5,
    }

    return {
        "total_shots": total,
        "type_counts": type_counts,
        "type_ratios": ratios,
        "dialogue_ratio": f"{dialogue_ratio:.1f}%",
        "thought_ratio": f"{thought_ratio:.1f}%",
        "narration_ratio": f"{narration_ratio:.1f}%",
        "none_ratio": f"{none_ratio:.1f}%",
        "checks": checks,
        "pass": checks["dialogue_ge_60"],  # 核心指标: dialogue ≥60%
    }


# ═══════════════════════════════════════════════════════════════
# 维度 4: 对话气泡渲染 + speaker_format 分析
# ═══════════════════════════════════════════════════════════════

def analyze_dialogue_bubbles(shots: list, characters: dict) -> dict:
    """维度 4: 分析对话气泡数据和 speaker_format"""
    char_list = characters.get("characters", [])
    name_en_map = {}
    for c in char_list:
        name_zh = c.get("name", "")
        name_en = c.get("name_en", "")
        if name_zh and name_en:
            name_en_map[name_zh] = name_en

    dialogue_shots = []
    speaker_entries = []

    for shot in shots:
        text_overlay = shot.get("text_overlay", {})
        if not isinstance(text_overlay, dict):
            continue

        text_type = text_overlay.get("text_type", "none")
        if "dialogue" not in text_type:
            continue

        sid = shot.get("shot_id", "?")
        chinese_text = text_overlay.get("chinese_text", "")
        speaker_position = text_overlay.get("speaker_position", "")

        texts = chinese_text if isinstance(chinese_text, list) else [chinese_text]
        dialogue_shots.append({
            "shot_id": sid,
            "text_type": text_type,
            "lines": len(texts),
            "speaker_position": speaker_position,
        })

        for txt in texts:
            if isinstance(txt, dict):
                txt = txt.get("text", "")
            if not isinstance(txt, str):
                continue
            for sep in ["：「", ":「", "：\"", ":\"", "："]:
                if sep in txt:
                    speaker_zh = txt.split(sep)[0].strip()
                    speaker_entries.append({
                        "shot_id": sid,
                        "speaker_zh": speaker_zh,
                        "expected_en": name_en_map.get(speaker_zh, "N/A"),
                        "has_en_name": speaker_zh in name_en_map,
                    })
                    break

    return {
        "dialogue_shot_count": len(dialogue_shots),
        "total_dialogue_lines": len(speaker_entries),
        "speakers_with_en_name": sum(1 for e in speaker_entries if e["has_en_name"]),
        "name_en_map": name_en_map,
        "dialogue_shots": dialogue_shots[:10],
        "speaker_details": speaker_entries[:15],
    }


# ═══════════════════════════════════════════════════════════════
# 维度 5: text_language=zh-CN 检查
# ═══════════════════════════════════════════════════════════════

def analyze_text_language(shots: list) -> dict:
    """维度 5: 检查 chinese_text 是否为简体中文"""
    # 繁体常见字
    traditional_chars = set("這個們說時來後為從對點過現開問進請給麼會學對應門間裡號條報書電話機錯關東車長點員場開間還買賣"
                          "認識農業環區劃經濟計畫藝術圖書館運動場發達國際組織機構會議廳處辦導師範學報紙雜誌總統選舉")

    issues = []
    total_texts = 0

    for shot in shots:
        text_overlay = shot.get("text_overlay", {})
        if not isinstance(text_overlay, dict):
            continue

        chinese_text = text_overlay.get("chinese_text", "")
        texts = chinese_text if isinstance(chinese_text, list) else [chinese_text]

        for txt in texts:
            if isinstance(txt, dict):
                txt = txt.get("text", "")
            if not isinstance(txt, str) or not txt:
                continue
            total_texts += 1
            found_traditional = [c for c in txt if c in traditional_chars]
            if found_traditional:
                issues.append({
                    "shot_id": shot.get("shot_id", "?"),
                    "text": txt[:50],
                    "traditional_chars": "".join(found_traditional[:5]),
                })

    return {
        "total_texts": total_texts,
        "issues_count": len(issues),
        "pass": len(issues) == 0,
        "issues": issues[:10],
    }


# ═══════════════════════════════════════════════════════════════
# 报告生成
# ═══════════════════════════════════════════════════════════════

def generate_report(results: list, output_dir: str):
    """生成 9 维度对比报告"""
    report_path = os.path.join(output_dir, "comparison_report.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# TASK-E2E-REGRESSION-R2 对比报告",
        f"",
        f"> 生成时间: {timestamp}",
        f"> 测试脚本: `tests/test_e2e_regression_r2.py`",
        f"> 验证修复: Issue #1(P0 text_overlay) / #2(P1 模型) / #3(P1 标签泄露) / #4(P2 三手) / #5(P2 乱码)",
        f"",
        f"---",
        f"",
        f"## 测试概况",
        f"",
        f"| 项 | Story A | Story B |",
        f"|-----|---------|---------|",
    ]

    for key in ["label", "style_preset", "title", "total_characters",
                 "total_scenes", "total_shots", "images_success", "images_total",
                 "with_text_count", "elapsed_seconds"]:
        a_val = results[0].get(key, "N/A") if len(results) > 0 else "N/A"
        b_val = results[1].get(key, "N/A") if len(results) > 1 else "N/A"
        lines.append(f"| {key} | {a_val} | {b_val} |")

    # ═══ 维度 1: 成功率 ═══
    lines.extend([
        f"",
        f"---",
        f"",
        f"## 维度 1: 生成成功率",
        f"",
    ])

    for r in results:
        group = r.get("group", "?")
        success = r.get("images_success", 0)
        total = r.get("images_total", 0)
        rate = f"{success}/{total} ({success/total*100:.0f}%)" if total > 0 else "N/A"
        verdict = "PASS" if total > 0 and success == total else "FAIL"
        lines.append(f"- **Story {group}**: {rate} — **{verdict}**")

    # ═══ 维度 2: text_overlay 输出 ═══
    lines.extend([
        f"",
        f"---",
        f"",
        f"## 维度 2: text_overlay 输出 (Issue #1 P0 修复验证)",
        f"",
    ])

    for r in results:
        group = r.get("group", "?")
        shots = r.get("shots_data", [])
        if shots:
            overlay_info = analyze_text_overlay_output(shots)
            verdict = "PASS" if overlay_info["pass"] else "FAIL"
            lines.append(f"### Story {group} — **{verdict}**")
            lines.append(f"- 覆盖率: {overlay_info['coverage']}")
            if overlay_info["missing_shots"]:
                lines.append(f"- 缺失 shots: {overlay_info['missing_shots']}")
            lines.append(f"- 逐 shot 明细:")
            lines.append(f"")
            lines.append(f"| Shot ID | text_type | has_chinese_text | speaker_position |")
            lines.append(f"|---------|-----------|-----------------|------------------|")
            for d in overlay_info["details"]:
                lines.append(f"| {d['shot_id']} | {d['text_type']} | {d['has_chinese_text']} | {d['speaker_position']} |")
            lines.append(f"")

    # ═══ 维度 3: text_type 分布 ═══
    lines.extend([
        f"---",
        f"",
        f"## 维度 3: text_type 分布 (目标: dialogue ≥60%)",
        f"",
    ])

    for r in results:
        group = r.get("group", "?")
        shots = r.get("shots_data", [])
        if shots:
            dist_info = analyze_text_type_distribution(shots)
            verdict = "PASS" if dist_info["pass"] else "FAIL"
            lines.append(f"### Story {group} — **{verdict}**")
            lines.append(f"- dialogue: {dist_info['dialogue_ratio']} (目标 ≥60%)")
            lines.append(f"- thought: {dist_info['thought_ratio']} (目标 10-20%)")
            lines.append(f"- narration: {dist_info['narration_ratio']} (目标 ≤15%)")
            lines.append(f"- none: {dist_info['none_ratio']} (目标 ≤5%)")
            lines.append(f"- 类型计数: {dist_info['type_counts']}")
            lines.append(f"- 达标检查: {dist_info['checks']}")
            lines.append(f"")

    # ═══ 维度 4: 对话气泡渲染 ═══
    lines.extend([
        f"---",
        f"",
        f"## 维度 4: 对话气泡渲染 + speaker_format=english",
        f"",
    ])

    for r in results:
        group = r.get("group", "?")
        shots = r.get("shots_data", [])
        chars = r.get("characters_data", {})
        if shots and chars:
            bubble_info = analyze_dialogue_bubbles(shots, chars)
            lines.append(f"### Story {group}")
            lines.append(f"- 对话 shots: {bubble_info['dialogue_shot_count']}")
            lines.append(f"- 对话行数: {bubble_info['total_dialogue_lines']}")
            lines.append(f"- 有英文名映射: {bubble_info['speakers_with_en_name']}")
            lines.append(f"- 角色名映射: {bubble_info['name_en_map']}")
            lines.append(f"")
            if bubble_info["dialogue_shots"]:
                lines.append(f"| Shot ID | text_type | 对话行数 | speaker_position |")
                lines.append(f"|---------|-----------|---------|-----------------|")
                for ds in bubble_info["dialogue_shots"]:
                    lines.append(f"| {ds['shot_id']} | {ds['text_type']} | {ds['lines']} | {ds['speaker_position']} |")
                lines.append(f"")
            if bubble_info["speaker_details"]:
                lines.append(f"**说话者详情 (前15条)**:")
                lines.append(f"")
                lines.append(f"| Shot | 中文名 | 英文名 | 有映射? |")
                lines.append(f"|------|--------|--------|---------|")
                for sd in bubble_info["speaker_details"]:
                    lines.append(f"| {sd['shot_id']} | {sd['speaker_zh']} | {sd['expected_en']} | {sd['has_en_name']} |")
                lines.append(f"")

    # ═══ 维度 5: text_language=zh-CN ═══
    lines.extend([
        f"---",
        f"",
        f"## 维度 5: text_language=zh-CN (简体中文)",
        f"",
    ])

    for r in results:
        group = r.get("group", "?")
        shots = r.get("shots_data", [])
        if shots:
            lang_info = analyze_text_language(shots)
            verdict = "PASS" if lang_info["pass"] else "FAIL"
            lines.append(f"### Story {group} — **{verdict}**")
            lines.append(f"- 文本总数: {lang_info['total_texts']}")
            lines.append(f"- 繁体问题数: {lang_info['issues_count']}")
            if lang_info["issues"]:
                for iss in lang_info["issues"]:
                    lines.append(f"  - Shot {iss['shot_id']}: \"{iss['text']}\" (繁体字: {iss['traditional_chars']})")
            lines.append(f"")

    # ═══ 维度 6/7/8/9: 需人工检查 ═══
    lines.extend([
        f"---",
        f"",
        f"## 维度 6-9: 需人工查看图片评估",
        f"",
        f"| # | 维度 | 对应修复 | Story A | Story B |",
        f"|---|------|---------|---------|---------|",
        f"| 6 | 无标签泄露 (shot 图无 Scene:/Character: 文字) | Issue #3 [P1] | __ | __ |",
        f"| 7 | 无 NB2 乱码文字 (无霓虹灯/便签乱码) | Issue #5 [P2] | __ | __ |",
        f"| 8 | 手部正常 (单角色无三手/多手) | Issue #4 [P2] | __ | __ |",
        f"| 9 | 角色/风格一致性 | 基线 | __ /5 | __ /5 |",
        f"",
    ])

    # ═══ Storyboard JSON 截取 ═══
    lines.extend([
        f"---",
        f"",
        f"## Storyboard JSON 截取 (text_overlay 验证)",
        f"",
    ])

    for r in results:
        group = r.get("group", "?")
        shots = r.get("shots_data", [])
        if shots:
            lines.append(f"### Story {group} — 前 3 个 shot 的 text_overlay")
            lines.append(f"")
            lines.append(f"```json")
            excerpt = []
            for shot in shots[:3]:
                excerpt.append({
                    "shot_id": shot.get("shot_id"),
                    "action_beat_id": shot.get("action_beat_id"),
                    "text_overlay": shot.get("text_overlay"),
                })
            lines.append(json.dumps(excerpt, ensure_ascii=False, indent=2))
            lines.append(f"```")
            lines.append(f"")

    # ═══ 图片路径 ═══
    lines.extend([
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

    # ═══ 综合评分 ═══
    lines.extend([
        f"",
        f"---",
        f"",
        f"## 综合评分",
        f"",
        f"| # | 维度 | Story A | Story B |",
        f"|---|------|---------|---------|",
    ])

    dim_labels = [
        "生成成功率",
        "text_overlay 输出",
        "text_type 分布",
        "对话气泡渲染",
        "text_language=zh-CN",
        "无标签泄露",
        "无 NB2 乱码文字",
        "手部正常",
        "角色/风格一致性",
    ]

    # 自动填充可分析的维度
    for i, label in enumerate(dim_labels, 1):
        a_score = "__ "
        b_score = "__ "

        if i == 1:  # 成功率
            for r in results:
                s = r.get("images_success", 0)
                t = r.get("images_total", 0)
                score = f"{s}/{t}" if t > 0 else "N/A"
                if r["group"] == "A":
                    a_score = score
                else:
                    b_score = score

        elif i == 2:  # text_overlay
            for r in results:
                shots = r.get("shots_data", [])
                if shots:
                    info = analyze_text_overlay_output(shots)
                    score = "PASS" if info["pass"] else f"FAIL ({info['coverage']})"
                    if r["group"] == "A":
                        a_score = score
                    else:
                        b_score = score

        elif i == 3:  # text_type 分布
            for r in results:
                shots = r.get("shots_data", [])
                if shots:
                    info = analyze_text_type_distribution(shots)
                    score = f"{'PASS' if info['pass'] else 'FAIL'} (dialogue {info['dialogue_ratio']})"
                    if r["group"] == "A":
                        a_score = score
                    else:
                        b_score = score

        elif i == 5:  # text_language
            for r in results:
                shots = r.get("shots_data", [])
                if shots:
                    info = analyze_text_language(shots)
                    score = "PASS" if info["pass"] else f"FAIL ({info['issues_count']} issues)"
                    if r["group"] == "A":
                        a_score = score
                    else:
                        b_score = score

        lines.append(f"| {i} | {label} | {a_score} | {b_score} |")

    lines.extend([
        f"",
        f"---",
        f"",
        f"*报告由 test_e2e_regression_r2.py 自动生成*",
    ])

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n报告已保存: {report_path}")
    return report_path


async def main():
    print("=" * 70)
    print("  TASK-E2E-REGRESSION-R2: 综合 E2E 回归验证")
    print("  2 stories x 10 shots | 9 维度验收")
    print("  修复验证: #1 text_overlay / #2 模型 / #3 标签泄露 / #4 三手 / #5 乱码")
    print("=" * 70)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(OUTPUT_BASE, timestamp)
    os.makedirs(output_dir, exist_ok=True)

    results = []

    for story in TEST_STORIES:
        try:
            result = await run_single_story(story, output_dir)
            results.append(result)
            print(f"\n  Story {story['group']} 完成: {'SUCCESS' if result.get('success') else 'FAILED'}")
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

    # 保存原始结果 (去掉大字段)
    results_for_save = []
    for r in results:
        r_save = {k: v for k, v in r.items() if k not in ("shots_data", "characters_data", "screenplay_data")}
        results_for_save.append(r_save)

    results_json_path = os.path.join(output_dir, "results_summary.json")
    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump(results_for_save, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存: {results_json_path}")

    # 保存 storyboard JSON 截取 (完整 text_overlay 数据)
    for r in results:
        shots = r.get("shots_data", [])
        if shots:
            storyboard_excerpt_path = os.path.join(output_dir, f"storyboard_excerpt_{r['group']}.json")
            excerpt = []
            for shot in shots:
                excerpt.append({
                    "shot_id": shot.get("shot_id"),
                    "scene_id": shot.get("scene_id"),
                    "action_beat_id": shot.get("action_beat_id"),
                    "text_overlay": shot.get("text_overlay"),
                    "image_prompt_preview": shot.get("image_prompt", "")[:100] + "...",
                })
            with open(storyboard_excerpt_path, "w", encoding="utf-8") as f:
                json.dump(excerpt, f, ensure_ascii=False, indent=2)
            print(f"  Storyboard 截取 ({r['group']}): {storyboard_excerpt_path}")

    # 生成对比报告
    report_path = generate_report(results, output_dir)

    # 最终摘要
    print(f"\n{'='*70}")
    print(f"  E2E REGRESSION R2 测试完成")
    print(f"{'='*70}")
    for r in results:
        group = r.get("group", "?")
        if r.get("success"):
            success = r.get("images_success", 0)
            total = r.get("images_total", 0)
            elapsed = r.get("elapsed_seconds", 0)
            print(f"  Story {group}: {success}/{total} shots | {elapsed:.0f}s | {r.get('title', 'N/A')}")

            # 快速打印维度 2/3
            shots = r.get("shots_data", [])
            if shots:
                overlay_info = analyze_text_overlay_output(shots)
                dist_info = analyze_text_type_distribution(shots)
                print(f"    维度2 text_overlay: {overlay_info['coverage']} {'PASS' if overlay_info['pass'] else 'FAIL'}")
                print(f"    维度3 text_type: dialogue {dist_info['dialogue_ratio']} {'PASS' if dist_info['pass'] else 'FAIL'}")
        else:
            print(f"  Story {group}: FAILED — {r.get('error', 'Unknown')}")

    print(f"\n  输出目录: {output_dir}")
    print(f"  对比报告: {report_path}")
    print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
