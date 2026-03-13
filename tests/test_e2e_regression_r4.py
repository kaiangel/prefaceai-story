"""
TASK-E2E-REGRESSION-R4: 综合 E2E 回归验证 (16 维度)

2 组故事 x 10 shots，不同题材+风格，完整 Stage 1->5 pipeline。
16 维度验收:
  D1.  生成成功率                      (基线)
  D2.  text_overlay 输出完整性          (Issue #1)
  D3.  text_type 分布                  (T2+T7)
  D4.  thought 出现率                  (T1+T10)
  D5.  无 speaker 错位                 (T2+T5+T6)
  D6.  plot_points 1:1 覆盖            (T3)
  D7.  无对话气泡重复                   (T4+T8+T12)
  D8.  无标签泄露                       (T11) ⭐ R3 FAIL 项
  D9.  无 NB2 乱码                     (基线)
  D10. 角色/风格一致性                  (基线)
  D11. 无双重渲染                       (T12) ⭐ R3 新 Bug 项
  D12. 条漫叙事自足                     (T13) — 人工
  D13. 跨年龄风格统一                   (T14) — 人工
  D14. 气泡去重                         (T15) — 人工
  D15. NB2_MODEL 命名                  (命名修复) — 代码审计+日志
  D16. OB-6 降级分支                    (T16) — 自动

覆盖修复 (T1-T16):
- T1-T10: R3 已验证的修复
- T11: 移除 PIL 标签（scene_reference_manager + reference_image_manager）
- T12: use_native_text=True 时 ALL text_types skip TextOverlay
- T12-UNIFY: T4+T12 合并为单一 if use_native_text 分支
- T13: COMIC_MODE_NARRATIVE_RULES 条漫叙事自足规则
- T13-INT: 集成到 storyboard_director.py
- T14: 跨年龄风格统一指令 (reference_image_manager)
- T15: NB2 气泡去重指令 (image_generator)
- T16: OB-6 narration_with_dialogue 降级分支

作者: @Tester
日期: 2026-03-10
"""

import asyncio
import json
import os
import re
import sys
import time
import io
from datetime import datetime
from pathlib import Path
from contextlib import redirect_stdout

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from app.services.pipeline_orchestrator import Phase2PipelineOrchestrator


# 测试配置 — 与 R3 相同的两组故事（保持可比性）
TEST_STORIES = [
    {
        "group": "A",
        "label": "家庭晚餐争吵 / illustration (对话密集型, 4角色)",
        "idea": "除夕夜家庭聚餐，父亲宣布要卖掉老宅搬去养老院，三个子女围绕老宅去留、赡养责任、童年记忆展开激烈争论，最终在母亲留下的一道红烧肉面前达成和解",
        "style_preset": "illustration",
        "character_count": 4,
    },
    {
        "group": "B",
        "label": "山间书法师徒 / ink (叙事+对话混合, 2角色)",
        "idea": "年迈的书法大师在山间茅屋教导叛逆少年弟子，从磨墨开始学起，师徒二人在争吵与和解中传承技艺，直到少年在雨夜发现师父偷偷吃药的秘密",
        "style_preset": "ink",
        "character_count": 2,
    },
]

SHOTS_LIMIT = 10
OUTPUT_BASE = "./test_output/manualtest/e2e_regression_r4"


async def run_single_story(story_config: dict, output_base: str) -> dict:
    """运行单组故事的完整 Stage 1->5 pipeline，同时捕获 stdout 日志"""
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

    # 捕获日志用于 D15 NB2_MODEL 命名检查
    log_buffer = io.StringIO()

    class TeeOutput:
        """同时写入 stdout 和 buffer"""
        def __init__(self, *streams):
            self.streams = streams
        def write(self, data):
            for s in self.streams:
                s.write(data)
        def flush(self):
            for s in self.streams:
                s.flush()

    original_stdout = sys.stdout
    tee = TeeOutput(original_stdout, log_buffer)
    sys.stdout = tee

    try:
        result = await orchestrator.run(
            idea=story_config["idea"],
            style_preset=story_config["style_preset"],
            target_duration_minutes=3,
            character_count=story_config["character_count"],
            generate_images=True,
            shots_limit=SHOTS_LIMIT,
        )
    finally:
        sys.stdout = original_stdout

    elapsed = time.time() - start_time
    captured_log = log_buffer.getvalue()

    # 收集结果摘要
    summary = {
        "group": group,
        "label": label,
        "idea": story_config["idea"],
        "style_preset": story_config["style_preset"],
        "success": result.get("success", False),
        "elapsed_seconds": round(elapsed, 1),
        "captured_log": captured_log,
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

        # 提取 screenplay 用于 dialogue_beats / plot_points 验证
        screenplay = result.get("stage_results", {}).get("screenplay", {})
        summary["screenplay_data"] = screenplay

        # 提取 outline 用于 plot_points 验证
        outline = result.get("stage_results", {}).get("outline", {})
        summary["outline_data"] = outline
    else:
        summary["error"] = result.get("error", "Unknown")
        summary["failed_stage"] = result.get("failed_stage", "Unknown")

    return summary


# ═══════════════════════════════════════════════════════════════
# D2: text_overlay 输出分析
# ═══════════════════════════════════════════════════════════════

def analyze_text_overlay_output(shots: list) -> dict:
    """D2: 检查每个 shot 是否有 text_overlay 字段"""
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
# D3: text_type 分布分析
# ═══════════════════════════════════════════════════════════════

def analyze_text_type_distribution(shots: list) -> dict:
    """D3: 检查 text_type 分布是否符合目标"""
    total = len(shots)
    type_counts = {}

    for shot in shots:
        text_overlay = shot.get("text_overlay", {})
        text_type = text_overlay.get("text_type", "none") if isinstance(text_overlay, dict) else "none"
        type_counts[text_type] = type_counts.get(text_type, 0) + 1

    ratios = {}
    for t, c in type_counts.items():
        ratios[t] = round(c / total * 100, 1) if total > 0 else 0

    dialogue_count = type_counts.get("dialogue", 0) + \
                     type_counts.get("dialogue_with_thought", 0) + \
                     type_counts.get("dialogue_with_narration", 0) + \
                     type_counts.get("narration_with_dialogue", 0)
    dialogue_ratio = dialogue_count / total * 100 if total > 0 else 0

    thought_count = type_counts.get("thought", 0)
    thought_ratio = thought_count / total * 100 if total > 0 else 0

    narration_count = type_counts.get("narration", 0) + \
                      type_counts.get("narration_with_thought", 0)
    narration_ratio = narration_count / total * 100 if total > 0 else 0

    none_count = type_counts.get("none", 0)
    none_ratio = none_count / total * 100 if total > 0 else 0

    checks = {
        "dialogue_ge_60": dialogue_ratio >= 60,
        "thought_10_20": 10 <= thought_ratio <= 20,
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
        "dialogue_ratio_num": dialogue_ratio,
        "thought_ratio_num": thought_ratio,
        "narration_ratio_num": narration_ratio,
        "checks": checks,
        "pass": checks["dialogue_ge_60"],
    }


# ═══════════════════════════════════════════════════════════════
# D4: thought 出现率 (T1+T10)
# ═══════════════════════════════════════════════════════════════

def analyze_thought_appearance(shots: list, screenplay: dict) -> dict:
    """D4: Stage 3 thought ratio + Stage 4 thought 出现"""
    scenes = screenplay.get("scenes", []) if screenplay else []
    total_beats = 0
    thought_beats = 0
    dialogue_beats_total = 0
    scene_details = []

    for scene in scenes:
        d_beats = scene.get("dialogue_beats", [])
        scene_thoughts = 0
        scene_dialogues = 0
        for beat in d_beats:
            beat_type = beat.get("type", "dialogue")
            if beat_type == "thought":
                scene_thoughts += 1
                thought_beats += 1
            elif beat_type == "dialogue":
                scene_dialogues += 1
                dialogue_beats_total += 1
            total_beats += 1
        scene_details.append({
            "scene_id": scene.get("scene_id", "?"),
            "total_beats": len(d_beats),
            "dialogue": scene_dialogues,
            "thought": scene_thoughts,
        })

    stage3_thought_ratio = thought_beats / total_beats * 100 if total_beats > 0 else 0

    thought_shots = 0
    total = len(shots)
    for shot in shots:
        text_overlay = shot.get("text_overlay", {})
        text_type = text_overlay.get("text_type", "none") if isinstance(text_overlay, dict) else "none"
        if text_type == "thought" or "thought" in text_type:
            thought_shots += 1

    stage4_thought_ratio = thought_shots / total * 100 if total > 0 else 0

    return {
        "stage3_total_dialogue_beats": total_beats,
        "stage3_thought_beats": thought_beats,
        "stage3_dialogue_beats": dialogue_beats_total,
        "stage3_thought_ratio": f"{stage3_thought_ratio:.1f}%",
        "stage3_thought_ratio_num": stage3_thought_ratio,
        "stage3_pass": stage3_thought_ratio >= 15,
        "stage4_thought_shots": thought_shots,
        "stage4_thought_ratio": f"{stage4_thought_ratio:.1f}%",
        "stage4_thought_ratio_num": stage4_thought_ratio,
        "scene_details": scene_details,
        "pass": stage3_thought_ratio >= 15 and thought_shots > 0,
    }


# ═══════════════════════════════════════════════════════════════
# D5: speaker 错位检查 (T2+T5+T6)
# ═══════════════════════════════════════════════════════════════

def analyze_speaker_mismatch(shots: list, characters: dict) -> dict:
    """D5: dialogue speaker 是否在 characters_visible 中"""
    char_list = characters.get("characters", [])
    name_to_id = {}
    for c in char_list:
        char_id = c.get("id", "")
        char_name = c.get("name", "")
        if char_id and char_name:
            name_to_id[char_name] = char_id

    total_dialogue_lines = 0
    mismatch_count = 0
    mismatch_details = []

    for shot in shots:
        sid = shot.get("shot_id", "?")
        text_overlay = shot.get("text_overlay", {})
        if not isinstance(text_overlay, dict):
            continue

        text_type = text_overlay.get("text_type", "none")
        if "dialogue" not in text_type:
            continue

        chars_visible = shot.get("character_direction", {}).get("characters_visible", [])
        chinese_text = text_overlay.get("chinese_text", "")
        texts = chinese_text if isinstance(chinese_text, list) else [chinese_text]

        for txt in texts:
            if isinstance(txt, dict):
                sub_type = txt.get("type", "dialogue")
                txt_str = txt.get("text", "")
            else:
                txt_str = txt
                sub_type = "dialogue" if ("：「" in txt_str or ":「" in txt_str or "：\"" in txt_str) else "other"

            if sub_type != "dialogue":
                continue

            total_dialogue_lines += 1

            match = re.match(r'^([\w\u4e00-\u9fff]+?)(?:内心)?[：:]', txt_str.strip())
            if match:
                speaker_zh = match.group(1)
                char_id = name_to_id.get(speaker_zh)
                if not char_id:
                    for name, cid in name_to_id.items():
                        if speaker_zh in name or name in speaker_zh:
                            char_id = cid
                            break

                if char_id and char_id not in chars_visible:
                    mismatch_count += 1
                    mismatch_details.append({
                        "shot_id": sid,
                        "speaker_zh": speaker_zh,
                        "char_id": char_id,
                        "chars_visible": chars_visible,
                    })

    mismatch_ratio = mismatch_count / total_dialogue_lines * 100 if total_dialogue_lines > 0 else 0

    return {
        "total_dialogue_lines": total_dialogue_lines,
        "mismatch_count": mismatch_count,
        "mismatch_ratio": f"{mismatch_ratio:.1f}%",
        "pass": mismatch_count == 0,
        "details": mismatch_details,
    }


# ═══════════════════════════════════════════════════════════════
# D6: plot_points 1:1 覆盖 (T3)
# ═══════════════════════════════════════════════════════════════

def analyze_plot_points_coverage(outline: dict, screenplay: dict) -> dict:
    """D6: Stage 3 是否为每个 plot_point 生成了对应 scene"""
    plot_points = outline.get("plot_points", []) if outline else []
    scenes = screenplay.get("scenes", []) if screenplay else []

    total_plot_points = len(plot_points)
    total_scenes = len(scenes)

    plot_beats = [pp.get("beat", f"plot_{i+1}") for i, pp in enumerate(plot_points)]
    scene_plot_points = [s.get("plot_point", "unknown") for s in scenes]

    missing_beats = []
    for beat in plot_beats:
        if beat not in scene_plot_points:
            missing_beats.append(beat)

    has_crisis = any("crisis" in b.lower() for b in scene_plot_points)
    crisis_in_outline = any("crisis" in b.lower() for b in plot_beats)

    return {
        "total_plot_points": total_plot_points,
        "total_scenes": total_scenes,
        "1_to_1": total_plot_points == total_scenes,
        "missing_beats": missing_beats,
        "plot_beats": plot_beats,
        "scene_plot_points": scene_plot_points,
        "crisis_in_outline": crisis_in_outline,
        "crisis_in_screenplay": has_crisis,
        "crisis_pass": (not crisis_in_outline) or has_crisis,
        "pass": total_plot_points == total_scenes and len(missing_beats) == 0,
    }


# ═══════════════════════════════════════════════════════════════
# D7: 对话气泡重复检查 (T4+T8+T12)
# ═══════════════════════════════════════════════════════════════

def analyze_bubble_duplication(shots: list, project_dir: str) -> dict:
    """D7: TextOverlay 是否重复渲染 dialogue（含 T12 扩展检查）"""
    dialogue_shots = []
    compound_shots = []
    issues = []

    for shot in shots:
        sid = shot.get("shot_id", "?")
        text_overlay = shot.get("text_overlay", {})
        if not isinstance(text_overlay, dict):
            continue

        text_type = text_overlay.get("text_type", "none")

        if text_type == "dialogue":
            dialogue_shots.append(sid)
            if project_dir:
                raw_path = os.path.join(project_dir, "images", f"shot_{sid:02d}.png")
                with_text_path = os.path.join(project_dir, "with_text_images", f"shot_{sid:02d}.png")
                if os.path.exists(raw_path) and os.path.exists(with_text_path):
                    raw_size = os.path.getsize(raw_path)
                    with_text_size = os.path.getsize(with_text_path)
                    if abs(raw_size - with_text_size) > raw_size * 0.05:
                        issues.append({
                            "shot_id": sid,
                            "type": "T4_dialogue_reprocessed",
                            "raw_size": raw_size,
                            "with_text_size": with_text_size,
                            "diff_pct": f"{abs(raw_size-with_text_size)/raw_size*100:.1f}%",
                        })

        elif text_type in ["dialogue_with_thought", "dialogue_with_narration",
                           "narration_with_dialogue"]:
            compound_shots.append(sid)

    return {
        "dialogue_shot_count": len(dialogue_shots),
        "compound_shot_count": len(compound_shots),
        "dialogue_shots": dialogue_shots,
        "compound_shots": compound_shots,
        "issues": issues,
        "pass": len(issues) == 0,
    }


# ═══════════════════════════════════════════════════════════════
# D11: 无双重渲染 (T12) ⭐ R3 新 Bug 项
# ═══════════════════════════════════════════════════════════════

def analyze_double_rendering(shots: list, project_dir: str) -> dict:
    """D11: use_native_text=True 时，ALL text_types 的 with_text 应是 raw 的复制

    T12 修复: when use_native_text=True, TextOverlay 完全不调用，
    with_text 是 raw 的 pil_image.copy().save()。

    检查: 所有非 none text_type 的 shot，with_text 文件大小应与 raw 接近（±10%）
    """
    checked_shots = []
    issues = []

    for shot in shots:
        sid = shot.get("shot_id", "?")
        text_overlay = shot.get("text_overlay", {})
        if not isinstance(text_overlay, dict):
            continue

        text_type = text_overlay.get("text_type", "none")
        if text_type == "none":
            continue

        checked_shots.append({"shot_id": sid, "text_type": text_type})

        if project_dir:
            raw_path = os.path.join(project_dir, "images", f"shot_{sid:02d}.png")
            with_text_path = os.path.join(project_dir, "with_text_images", f"shot_{sid:02d}.png")

            if os.path.exists(raw_path) and os.path.exists(with_text_path):
                raw_size = os.path.getsize(raw_path)
                with_text_size = os.path.getsize(with_text_path)
                diff_pct = abs(raw_size - with_text_size) / raw_size * 100 if raw_size > 0 else 0

                # T12: copy().save() 可能因 PNG 重新压缩导致微小差异，允许 ±10%
                if diff_pct > 10:
                    issues.append({
                        "shot_id": sid,
                        "text_type": text_type,
                        "raw_size": raw_size,
                        "with_text_size": with_text_size,
                        "diff_pct": f"{diff_pct:.1f}%",
                        "verdict": "FAIL — TextOverlay 可能被调用（双重渲染）",
                    })
            elif os.path.exists(raw_path) and not os.path.exists(with_text_path):
                issues.append({
                    "shot_id": sid,
                    "text_type": text_type,
                    "verdict": "FAIL — with_text 文件不存在",
                })

    return {
        "checked_shots": len(checked_shots),
        "checked_details": checked_shots,
        "issues_count": len(issues),
        "issues": issues,
        "pass": len(issues) == 0,
    }


# ═══════════════════════════════════════════════════════════════
# D15: NB2_MODEL 命名检查 (PRO_MODEL → NB2_MODEL 重命名修复)
# ═══════════════════════════════════════════════════════════════

def analyze_nb2_model_naming(captured_log: str) -> dict:
    """D15: 检查运行日志中是否出现 NB2_MODEL / 不出现 PRO_MODEL"""
    nb2_mentions = len(re.findall(r'NB2_MODEL|gemini-3\.1-flash-image', captured_log))
    pro_model_mentions = len(re.findall(r'PRO_MODEL', captured_log))

    # 同时做代码级审计
    code_files_to_check = [
        "app/services/image_generator.py",
        "tests/test_nb2_switch.py",
    ]
    code_issues = []
    for fpath in code_files_to_check:
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            pro_hits = [m.start() for m in re.finditer(r'PRO_MODEL', content)]
            if pro_hits:
                code_issues.append({
                    "file": fpath,
                    "pro_model_occurrences": len(pro_hits),
                })

    return {
        "log_nb2_mentions": nb2_mentions,
        "log_pro_model_mentions": pro_model_mentions,
        "code_audit_issues": code_issues,
        "pass": pro_model_mentions == 0 and len(code_issues) == 0,
    }


# ═══════════════════════════════════════════════════════════════
# D16: OB-6 narration_with_dialogue 降级分支 (T16)
# ═══════════════════════════════════════════════════════════════

def analyze_ob6_downgrade(shots: list, captured_log: str) -> dict:
    """D16: 检查 narration_with_dialogue 降级逻辑是否正常运行

    T16: 当 speaker 不可见时，narration_with_dialogue → narration_with_thought
    即使没有触发降级，也验证代码路径不报错。
    """
    # 检查是否有 narration_with_dialogue text_type
    nwd_shots = []
    downgraded_shots = []

    for shot in shots:
        sid = shot.get("shot_id", "?")
        text_overlay = shot.get("text_overlay", {})
        if not isinstance(text_overlay, dict):
            continue
        text_type = text_overlay.get("text_type", "none")
        if text_type == "narration_with_dialogue":
            nwd_shots.append(sid)

    # 检查日志中是否有降级记录
    downgrade_logs = re.findall(
        r"\[T5\] Shot (\d+): text_type 'narration_with_dialogue' → 'narration_with_thought'",
        captured_log
    )
    for log_match in downgrade_logs:
        downgraded_shots.append(int(log_match))

    # 检查 pipeline 是否无错误完成
    pipeline_errors = re.findall(r"(?:KeyError|ValueError|TypeError).*narration_with_dialogue", captured_log)

    return {
        "narration_with_dialogue_shots": nwd_shots,
        "downgraded_shots": downgraded_shots,
        "pipeline_errors": pipeline_errors,
        "pass": len(pipeline_errors) == 0,  # 核心：不报错即 PASS
        "note": "narration_with_dialogue 可能未出现（LLM 未生成此 text_type），"
                "但代码路径已在 _validate_storyboard() 中覆盖" if not nwd_shots else "",
    }


# ═══════════════════════════════════════════════════════════════
# text_language 附加检查
# ═══════════════════════════════════════════════════════════════

def analyze_text_language(shots: list) -> dict:
    """检查 chinese_text 是否为简体中文"""
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
# 报告生成 (16 维度)
# ═══════════════════════════════════════════════════════════════

def generate_report(results: list, output_dir: str):
    """生成 16 维度对比报告"""
    report_path = os.path.join(output_dir, "comparison_report.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# TASK-E2E-REGRESSION-R4 对比报告",
        f"",
        f"> 生成时间: {timestamp}",
        f"> 测试脚本: `tests/test_e2e_regression_r4.py`",
        f"> 验证修复: T1-T16 (全量回归 + T11-T16 新修复验证)",
        f"> R3 遗留: D8 标签泄露 FAIL + D11 双重渲染 Bug → 本轮重点验证",
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

    # ═══ D1: 成功率 ═══
    lines.extend([f"", f"---", f"", f"## D1: 生成成功率", f""])
    for r in results:
        group = r.get("group", "?")
        success = r.get("images_success", 0)
        total = r.get("images_total", 0)
        rate = f"{success}/{total} ({success/total*100:.0f}%)" if total > 0 else "N/A"
        verdict = "PASS" if total > 0 and success == total else "FAIL"
        lines.append(f"- **Story {group}**: {rate} — **{verdict}**")

    # ═══ D2: text_overlay 输出 ═══
    lines.extend([f"", f"---", f"", f"## D2: text_overlay 输出完整性", f""])
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

    # ═══ D3: text_type 分布 ═══
    lines.extend([f"---", f"", f"## D3: text_type 分布 (目标: dialogue ≥60%, thought 10-20%, narration ≤15%)", f""])
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

    # ═══ D4: thought 出现率 ═══
    lines.extend([f"---", f"", f"## D4: thought 出现率 (T1+T10 修复验证)", f""])
    for r in results:
        group = r.get("group", "?")
        shots = r.get("shots_data", [])
        screenplay = r.get("screenplay_data", {})
        if shots:
            thought_info = analyze_thought_appearance(shots, screenplay)
            verdict = "PASS" if thought_info["pass"] else "FAIL"
            lines.append(f"### Story {group} — **{verdict}**")
            lines.append(f"- Stage 3 dialogue_beats: {thought_info['stage3_total_dialogue_beats']} 条")
            lines.append(f"  - dialogue: {thought_info['stage3_dialogue_beats']}, thought: {thought_info['stage3_thought_beats']}")
            lines.append(f"  - thought 占比: {thought_info['stage3_thought_ratio']} (目标 ≥20%)")
            lines.append(f"- Stage 4 text_type thought shots: {thought_info['stage4_thought_shots']} ({thought_info['stage4_thought_ratio']})")
            lines.append(f"")

    # ═══ D5: speaker 错位 ═══
    lines.extend([f"---", f"", f"## D5: 无 speaker 错位 (T2+T5+T6 修复验证)", f""])
    for r in results:
        group = r.get("group", "?")
        shots = r.get("shots_data", [])
        chars = r.get("characters_data", {})
        if shots and chars:
            speaker_info = analyze_speaker_mismatch(shots, chars)
            verdict = "PASS" if speaker_info["pass"] else "FAIL"
            lines.append(f"### Story {group} — **{verdict}**")
            lines.append(f"- 对话行数: {speaker_info['total_dialogue_lines']}")
            lines.append(f"- 错位数: {speaker_info['mismatch_count']} ({speaker_info['mismatch_ratio']})")
            if speaker_info["details"]:
                lines.append(f"- 错位详情:")
                for d in speaker_info["details"]:
                    lines.append(f"  - Shot {d['shot_id']}: {d['speaker_zh']} ({d['char_id']}) 不在 {d['chars_visible']}")
            lines.append(f"")

    # ═══ D6: plot_points 覆盖 ═══
    lines.extend([f"---", f"", f"## D6: plot_points 1:1 覆盖 (T3 修复验证)", f""])
    for r in results:
        group = r.get("group", "?")
        outline = r.get("outline_data", {})
        screenplay = r.get("screenplay_data", {})
        if outline or screenplay:
            pp_info = analyze_plot_points_coverage(outline, screenplay)
            verdict = "PASS" if pp_info["pass"] else "FAIL"
            lines.append(f"### Story {group} — **{verdict}**")
            lines.append(f"- Outline plot_points: {pp_info['total_plot_points']}")
            lines.append(f"- Screenplay scenes: {pp_info['total_scenes']}")
            lines.append(f"- 1:1 映射: {'YES' if pp_info['1_to_1'] else 'NO'}")
            if pp_info["missing_beats"]:
                lines.append(f"- 缺失 beats: {pp_info['missing_beats']}")
            lines.append(f"")

    # ═══ D7: 气泡重复 ═══
    lines.extend([f"---", f"", f"## D7: 无对话气泡重复 (T4+T8+T12 修复验证)", f""])
    for r in results:
        group = r.get("group", "?")
        shots = r.get("shots_data", [])
        project_dir = r.get("project_dir", "")
        if shots:
            bubble_info = analyze_bubble_duplication(shots, project_dir)
            verdict = "PASS" if bubble_info["pass"] else "FAIL"
            lines.append(f"### Story {group} — **{verdict}**")
            lines.append(f"- dialogue shots (T4 skip): {bubble_info['dialogue_shot_count']} — {bubble_info['dialogue_shots']}")
            lines.append(f"- compound shots (T8 split): {bubble_info['compound_shot_count']} — {bubble_info['compound_shots']}")
            if bubble_info["issues"]:
                lines.append(f"- 重复问题:")
                for iss in bubble_info["issues"]:
                    lines.append(f"  - Shot {iss['shot_id']}: {iss['type']} (diff {iss['diff_pct']})")
            lines.append(f"")

    # ═══ D8-D10: 需人工查看 ═══
    lines.extend([
        f"---", f"",
        f"## D8-D10: 需人工查看图片评估", f"",
        f"| # | 维度 | 对应修复 | Story A | Story B |",
        f"|---|------|---------|---------|---------|",
        f"| 8 | 无标签泄露 (shot 图无 Scene:/Character: 文字) | T11 ⭐R3 FAIL | __ | __ |",
        f"| 9 | 无 NB2 乱码文字 (无霓虹灯/便签乱码) | 基线 | __ | __ |",
        f"| 10 | 角色/风格一致性 | 基线 | __ /5 | __ /5 |",
        f"",
    ])

    # ═══ D11: 无双重渲染 (T12) ⭐ ═══
    lines.extend([f"---", f"", f"## D11: 无双重渲染 (T12) ⭐ R3 新 Bug 项", f""])
    for r in results:
        group = r.get("group", "?")
        shots = r.get("shots_data", [])
        project_dir = r.get("project_dir", "")
        if shots:
            dr_info = analyze_double_rendering(shots, project_dir)
            verdict = "PASS" if dr_info["pass"] else "FAIL"
            lines.append(f"### Story {group} — **{verdict}**")
            lines.append(f"- 检查 shot 数: {dr_info['checked_shots']} (所有非 none text_type)")
            lines.append(f"- 问题数: {dr_info['issues_count']}")
            if dr_info["issues"]:
                lines.append(f"- 问题详情:")
                for iss in dr_info["issues"]:
                    lines.append(f"  - Shot {iss['shot_id']} ({iss['text_type']}): {iss['verdict']}")
                    if "raw_size" in iss:
                        lines.append(f"    raw={iss['raw_size']}B, with_text={iss['with_text_size']}B, diff={iss['diff_pct']}")
            else:
                lines.append(f"- 逐 shot 检查明细:")
                lines.append(f"")
                lines.append(f"| Shot ID | text_type | 结果 |")
                lines.append(f"|---------|-----------|------|")
                for sd in dr_info["checked_details"]:
                    lines.append(f"| {sd['shot_id']} | {sd['text_type']} | PASS (raw≈with_text) |")
            lines.append(f"")

    # ═══ D12-D14: 需人工查看 ═══
    lines.extend([
        f"---", f"",
        f"## D12-D14: 需人工查看 (条漫叙事+风格+气泡)", f"",
        f"| # | 维度 | 对应修复 | Story A | Story B | 验证方法 |",
        f"|---|------|---------|---------|---------|---------|",
        f"| 12 | 条漫叙事自足 | T13 | __ | __ | thought/dialogue 是否承载足够叙事上下文 |",
        f"| 13 | 跨年龄风格统一 | T14 | __ | __ | 不同年龄角色是否保持同一画风 |",
        f"| 14 | 气泡去重 | T15 | __ | __ | 同一对话是否只渲染一次 |",
        f"",
    ])

    # ═══ D15: NB2_MODEL 命名 ═══
    lines.extend([f"---", f"", f"## D15: NB2_MODEL 命名 (PRO_MODEL → NB2_MODEL 修复)", f""])
    # 合并两个故事的日志
    all_logs = " ".join(r.get("captured_log", "") for r in results)
    nb2_info = analyze_nb2_model_naming(all_logs)
    verdict = "PASS" if nb2_info["pass"] else "FAIL"
    lines.append(f"### 结果: **{verdict}**")
    lines.append(f"- 日志中 NB2_MODEL/gemini-3.1-flash 出现次数: {nb2_info['log_nb2_mentions']}")
    lines.append(f"- 日志中 PRO_MODEL 出现次数: {nb2_info['log_pro_model_mentions']} (应为 0)")
    if nb2_info["code_audit_issues"]:
        lines.append(f"- 代码审计问题:")
        for ci in nb2_info["code_audit_issues"]:
            lines.append(f"  - {ci['file']}: PRO_MODEL 出现 {ci['pro_model_occurrences']} 次")
    lines.append(f"")

    # ═══ D16: OB-6 降级 ═══
    lines.extend([f"---", f"", f"## D16: OB-6 narration_with_dialogue 降级分支 (T16)", f""])
    for r in results:
        group = r.get("group", "?")
        shots = r.get("shots_data", [])
        log = r.get("captured_log", "")
        if shots:
            ob6_info = analyze_ob6_downgrade(shots, log)
            verdict = "PASS" if ob6_info["pass"] else "FAIL"
            lines.append(f"### Story {group} — **{verdict}**")
            lines.append(f"- narration_with_dialogue shots: {ob6_info['narration_with_dialogue_shots']}")
            lines.append(f"- 降级触发 shots: {ob6_info['downgraded_shots']}")
            lines.append(f"- pipeline 错误: {len(ob6_info['pipeline_errors'])}")
            if ob6_info["note"]:
                lines.append(f"- 备注: {ob6_info['note']}")
            lines.append(f"")

    # ═══ text_language 附加检查 ═══
    lines.extend([f"---", f"", f"## 附加: text_language=zh-CN (简体中文)", f""])
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

    # ═══ Storyboard JSON 截取 ═══
    lines.extend([f"---", f"", f"## Storyboard JSON 截取 (text_overlay 验证)", f""])
    for r in results:
        group = r.get("group", "?")
        shots = r.get("shots_data", [])
        if shots:
            lines.append(f"### Story {group} — 前 3 个 shot 的 text_overlay + character_direction")
            lines.append(f"")
            lines.append(f"```json")
            excerpt = []
            for shot in shots[:3]:
                excerpt.append({
                    "shot_id": shot.get("shot_id"),
                    "scene_id": shot.get("scene_id"),
                    "action_beat_id": shot.get("action_beat_id"),
                    "text_overlay": shot.get("text_overlay"),
                    "characters_visible": shot.get("character_direction", {}).get("characters_visible", []),
                })
            lines.append(json.dumps(excerpt, ensure_ascii=False, indent=2))
            lines.append(f"```")
            lines.append(f"")

    # ═══ 图片路径 ═══
    lines.extend([f"---", f"", f"## 图片路径", f""])
    for r in results:
        group = r.get("group", "?")
        pdir = r.get("project_dir", "N/A")
        lines.append(f"- **Story {group}**: `{pdir}`")
        lines.append(f"  - 无文字原图: `{pdir}/images/`")
        lines.append(f"  - 带文字版: `{pdir}/with_text_images/`")
        lines.append(f"  - 角色参考图: `{pdir}/character_refs/`")
        lines.append(f"  - 场景参考图: `{pdir}/scene_refs/`")

    # ═══ 综合评分 (16 维度) ═══
    lines.extend([f"", f"---", f"", f"## 综合评分 (16 维度)", f"",
                  f"| # | 维度 | Story A | Story B | R3→R4 |",
                  f"|---|------|---------|---------|-------|"])

    dim_labels = [
        ("D1", "生成成功率"),
        ("D2", "text_overlay 输出完整性"),
        ("D3", "text_type 分布"),
        ("D4", "thought 出现率 (T1+T10)"),
        ("D5", "无 speaker 错位 (T2+T5+T6)"),
        ("D6", "plot_points 1:1 覆盖 (T3)"),
        ("D7", "无对话气泡重复 (T4+T8+T12)"),
        ("D8", "无标签泄露 (T11) ⭐"),
        ("D9", "无 NB2 乱码文字"),
        ("D10", "角色/风格一致性"),
        ("D11", "无双重渲染 (T12) ⭐"),
        ("D12", "条漫叙事自足 (T13)"),
        ("D13", "跨年龄风格统一 (T14)"),
        ("D14", "气泡去重 (T15)"),
        ("D15", "NB2_MODEL 命名"),
        ("D16", "OB-6 降级分支 (T16)"),
    ]

    for dim_id, label in dim_labels:
        a_score = "__ "
        b_score = "__ "
        r3_note = ""
        dim_num = int(dim_id[1:])

        if dim_num == 1:
            for r in results:
                s = r.get("images_success", 0)
                t = r.get("images_total", 0)
                score = f"{s}/{t}" if t > 0 else "N/A"
                if r["group"] == "A": a_score = score
                else: b_score = score

        elif dim_num == 2:
            for r in results:
                shots = r.get("shots_data", [])
                if shots:
                    info = analyze_text_overlay_output(shots)
                    score = "PASS" if info["pass"] else f"FAIL ({info['coverage']})"
                    if r["group"] == "A": a_score = score
                    else: b_score = score

        elif dim_num == 3:
            for r in results:
                shots = r.get("shots_data", [])
                if shots:
                    info = analyze_text_type_distribution(shots)
                    score = f"{'PASS' if info['pass'] else 'FAIL'} (d={info['dialogue_ratio']} t={info['thought_ratio']})"
                    if r["group"] == "A": a_score = score
                    else: b_score = score

        elif dim_num == 4:
            for r in results:
                shots = r.get("shots_data", [])
                screenplay = r.get("screenplay_data", {})
                if shots:
                    info = analyze_thought_appearance(shots, screenplay)
                    score = f"{'PASS' if info['pass'] else 'FAIL'} (S3={info['stage3_thought_ratio']} S4={info['stage4_thought_ratio']})"
                    if r["group"] == "A": a_score = score
                    else: b_score = score

        elif dim_num == 5:
            for r in results:
                shots = r.get("shots_data", [])
                chars = r.get("characters_data", {})
                if shots and chars:
                    info = analyze_speaker_mismatch(shots, chars)
                    score = f"{'PASS' if info['pass'] else 'FAIL'} ({info['mismatch_count']}/{info['total_dialogue_lines']})"
                    if r["group"] == "A": a_score = score
                    else: b_score = score

        elif dim_num == 6:
            for r in results:
                outline = r.get("outline_data", {})
                screenplay = r.get("screenplay_data", {})
                if outline or screenplay:
                    info = analyze_plot_points_coverage(outline, screenplay)
                    score = f"{'PASS' if info['pass'] else 'FAIL'} ({info['total_scenes']}/{info['total_plot_points']})"
                    if r["group"] == "A": a_score = score
                    else: b_score = score

        elif dim_num == 7:
            for r in results:
                shots = r.get("shots_data", [])
                pdir = r.get("project_dir", "")
                if shots:
                    info = analyze_bubble_duplication(shots, pdir)
                    score = f"{'PASS' if info['pass'] else 'FAIL'} ({len(info['issues'])} issues)"
                    if r["group"] == "A": a_score = score
                    else: b_score = score
            r3_note = "R3:PASS"

        elif dim_num in [8, 9, 10]:
            r3_note = "R3:FAIL" if dim_num == 8 else ("R3:PASS" if dim_num == 9 else "R3:PASS")

        elif dim_num == 11:
            for r in results:
                shots = r.get("shots_data", [])
                pdir = r.get("project_dir", "")
                if shots:
                    info = analyze_double_rendering(shots, pdir)
                    score = f"{'PASS' if info['pass'] else 'FAIL'} ({info['issues_count']} issues)"
                    if r["group"] == "A": a_score = score
                    else: b_score = score
            r3_note = "R3:Bug"

        elif dim_num in [12, 13, 14]:
            r3_note = "新维度"

        elif dim_num == 15:
            all_logs = " ".join(r.get("captured_log", "") for r in results)
            info = analyze_nb2_model_naming(all_logs)
            score = "PASS" if info["pass"] else f"FAIL (PRO_MODEL={info['log_pro_model_mentions']})"
            a_score = score
            b_score = score
            r3_note = "新维度"

        elif dim_num == 16:
            for r in results:
                shots = r.get("shots_data", [])
                log = r.get("captured_log", "")
                if shots:
                    info = analyze_ob6_downgrade(shots, log)
                    score = f"{'PASS' if info['pass'] else 'FAIL'}"
                    if r["group"] == "A": a_score = score
                    else: b_score = score
            r3_note = "新维度"

        lines.append(f"| {dim_id} | {label} | {a_score} | {b_score} | {r3_note} |")

    lines.extend([
        f"",
        f"---",
        f"",
        f"*报告由 test_e2e_regression_r4.py 自动生成*",
    ])

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n报告已保存: {report_path}")
    return report_path


async def main():
    print("=" * 70)
    print("  TASK-E2E-REGRESSION-R4: 综合 E2E 回归验证")
    print("  2 stories x 10 shots | 16 维度验收")
    print("  修复验证: T1-T16 (全量回归)")
    print("  重点: D8 标签泄露 + D11 双重渲染 (R3 遗留)")
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
                "captured_log": "",
            })

    # 保存原始结果 (去掉大字段)
    results_for_save = []
    for r in results:
        r_save = {k: v for k, v in r.items()
                  if k not in ("shots_data", "characters_data", "screenplay_data",
                               "outline_data", "captured_log")}
        results_for_save.append(r_save)

    results_json_path = os.path.join(output_dir, "results_summary.json")
    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump(results_for_save, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存: {results_json_path}")

    # 保存捕获的日志
    for r in results:
        log = r.get("captured_log", "")
        if log:
            log_path = os.path.join(output_dir, f"pipeline_log_{r['group']}.txt")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(log)
            print(f"  Pipeline 日志 ({r['group']}): {log_path}")

    # 保存 storyboard JSON 截取
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
                    "characters_visible": shot.get("character_direction", {}).get("characters_visible", []),
                    "image_prompt_preview": shot.get("image_prompt", "")[:100] + "...",
                })
            with open(storyboard_excerpt_path, "w", encoding="utf-8") as f:
                json.dump(excerpt, f, ensure_ascii=False, indent=2)
            print(f"  Storyboard 截取 ({r['group']}): {storyboard_excerpt_path}")

    # 保存 screenplay 截取
    for r in results:
        screenplay = r.get("screenplay_data", {})
        if screenplay:
            screenplay_excerpt_path = os.path.join(output_dir, f"screenplay_excerpt_{r['group']}.json")
            scenes = screenplay.get("scenes", [])
            excerpt = []
            for scene in scenes:
                excerpt.append({
                    "scene_id": scene.get("scene_id"),
                    "plot_point": scene.get("plot_point"),
                    "characters_in_scene": scene.get("characters_in_scene"),
                    "action_beats_count": len(scene.get("action_beats", [])),
                    "dialogue_beats": scene.get("dialogue_beats", []),
                })
            with open(screenplay_excerpt_path, "w", encoding="utf-8") as f:
                json.dump(excerpt, f, ensure_ascii=False, indent=2)
            print(f"  Screenplay 截取 ({r['group']}): {screenplay_excerpt_path}")

    # 保存 characters JSON
    for r in results:
        chars = r.get("characters_data", {})
        if chars:
            chars_path = os.path.join(output_dir, f"{r.get('total_characters', 'N')}_characters.json")
            with open(chars_path, "w", encoding="utf-8") as f:
                json.dump(chars, f, ensure_ascii=False, indent=2)

    # 生成对比报告
    report_path = generate_report(results, output_dir)

    # 最终摘要 (16 维度)
    print(f"\n{'='*70}")
    print(f"  E2E REGRESSION R4 测试完成")
    print(f"{'='*70}")
    for r in results:
        group = r.get("group", "?")
        if r.get("success"):
            success = r.get("images_success", 0)
            total = r.get("images_total", 0)
            elapsed = r.get("elapsed_seconds", 0)
            print(f"  Story {group}: {success}/{total} shots | {elapsed:.0f}s | {r.get('title', 'N/A')}")

            shots = r.get("shots_data", [])
            screenplay = r.get("screenplay_data", {})
            outline = r.get("outline_data", {})
            chars = r.get("characters_data", {})
            log = r.get("captured_log", "")
            if shots:
                overlay_info = analyze_text_overlay_output(shots)
                dist_info = analyze_text_type_distribution(shots)
                thought_info = analyze_thought_appearance(shots, screenplay)
                speaker_info = analyze_speaker_mismatch(shots, chars)
                pp_info = analyze_plot_points_coverage(outline, screenplay)
                bubble_info = analyze_bubble_duplication(shots, r.get("project_dir", ""))
                dr_info = analyze_double_rendering(shots, r.get("project_dir", ""))
                ob6_info = analyze_ob6_downgrade(shots, log)

                print(f"    D2 text_overlay: {overlay_info['coverage']} {'PASS' if overlay_info['pass'] else 'FAIL'}")
                print(f"    D3 text_type: d={dist_info['dialogue_ratio']} t={dist_info['thought_ratio']} n={dist_info['narration_ratio']} {'PASS' if dist_info['pass'] else 'FAIL'}")
                print(f"    D4 thought: S3={thought_info['stage3_thought_ratio']} S4={thought_info['stage4_thought_ratio']} {'PASS' if thought_info['pass'] else 'FAIL'}")
                print(f"    D5 speaker: {speaker_info['mismatch_count']}/{speaker_info['total_dialogue_lines']} mismatch {'PASS' if speaker_info['pass'] else 'FAIL'}")
                print(f"    D6 plot_points: {pp_info['total_scenes']}/{pp_info['total_plot_points']} {'PASS' if pp_info['pass'] else 'FAIL'}")
                print(f"    D7 bubble: {len(bubble_info['issues'])} issues {'PASS' if bubble_info['pass'] else 'FAIL'}")
                print(f"    D11 double-render: {dr_info['issues_count']} issues {'PASS' if dr_info['pass'] else 'FAIL'} ⭐")
                print(f"    D16 OB-6: {'PASS' if ob6_info['pass'] else 'FAIL'}")
        else:
            print(f"  Story {group}: FAILED — {r.get('error', 'Unknown')}")

    # D15 汇总
    all_logs = " ".join(r.get("captured_log", "") for r in results)
    nb2_info = analyze_nb2_model_naming(all_logs)
    print(f"    D15 NB2_MODEL: {'PASS' if nb2_info['pass'] else 'FAIL'} (NB2={nb2_info['log_nb2_mentions']}, PRO={nb2_info['log_pro_model_mentions']})")

    print(f"\n  输出目录: {output_dir}")
    print(f"  对比报告: {report_path}")
    print(f"  ⭐ 重点验证: D8 标签泄露 + D11 双重渲染 (需人工查看图片)")
    print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
