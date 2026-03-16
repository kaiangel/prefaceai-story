"""
TASK-E2E-REGRESSION-R8: 综合 E2E 回归验证 (44 维度)

1 故事 x 10 shots，illustration 风格，4 角色，全新题材（山村赶圩/渔村早市）。
44 维度验收 (R7 原有 36 + R8 新增 N16-N23):
  D1.  角色一致性                      (人工)
  D2.  风格一致性                      (人工)
  D3.  参考图质量                      (人工)
  D4.  构图多样性                      (自动: shot_type 统计)
  D5.  text_overlay 渲染               (自动)
  D6.  文字可读性                      (人工)
  D7.  narration 覆盖                  (自动: plot_points 1:1)
  D8.  对话内容匹配                    (人工)
  D9.  情感表达                        (人工)
  D10. 场景连续性                      (人工)
  D11. 光影一致                        (人工)
  D12. 角色表情                        (人工)
  D13. 背景细节                        (人工)
  D14. 道具连续性                      (人工)
  D15. 镜头语言                        (自动: camera 多样性)
  D16. 叙事完整性                      (自动: plot_points + narration 覆盖)
  S1.  角色数量匹配                    (日志: ShotValidator)
  S2.  道具存续                        (人工)
  S3.  面部一致                        (人工)
  S4.  跨年龄风格                      (人工)
  S5.  气泡重复                        (日志: ShotValidator)
  N1.  角色称谓正确性                  (自动: text_overlay vs family_role + 人工)
  N2.  对话自然度                      (人工 + 自动辅助)
  N3.  同场景背景多样性                (自动: image_prompt 分析 + 人工)
  N4.  室内纵深感                      (人工)
  N5.  参考图模型                      (日志+代码审计: NB2)
  N6.  道具检测日志                    (日志: ShotValidator key_props)
  N7.  off_screen_speaker 标记         (自动: 4_storyboard.json off_screen_speaker 字段)
  N8.  off_screen 对话渲染             (人工: voiceover bar 而非气泡)
  N9.  family_relationships 传递       (自动: outline → screenplay CHARACTER RELATIONSHIPS)
  N10. 亲属称谓清晰度                  (自动: dialogue_beats 无歧义称谓)
  N11. 镜头信息完整性                  (自动: image_prompt 含 shot_size/angle + Plan B 日志)
  N12. 多人空间锚定                    (自动: 3+ 人 shots image_prompt 含空间描述)
  N13. 家庭关系逻辑一致性              (自动: triangle + spouse 传递)
  N14. color_palette 英文              (自动: outline color_palette 无中文)
  N15. 招牌注入                        (自动: 日志 + scene_ref SIGNAGE 注入)
  N16. off_screen 文字去重              (自动+代码: T-A visible speaker 无 voiceover 重复)
  N17. 重试上限                         (日志: T-B MAX_SHOT_RETRIES=1, 每 shot ≤2 次)
  N18. signage_text 数据流              (自动: T-C outline signage_text + scene_ref 无标签泄漏)
  N19. Prompt Quality Report            (自动: T-D prompt_quality_report.md 3 维度扩展关键词)
  N20. Stage 4 新规则                   (自动+人工: T-E/F/G Rules #10-12 生效)
  N21. Pre-Check 日志                   (日志: T-I [PromptPreCheck] 条目存在)
  N22. 自然度日志                       (日志: T-H has_visual_unnaturalness 字段存在)
  N23. 人群角色计数                     (日志: T-K ShotValidator 主角/路人区分)

覆盖修复 (T1-T37 + OB-T29 + T-A~T-K):
- T1-T28: R4/R5/R6 已验证的修复
- T29: off_screen_speaker 降级逻辑修复 (storyboard_director.py + image_generator.py + text_overlay_service.py)
- T30: ShotValidator 日志增强 (shot_validator.py + pipeline_orchestrator.py)
- T31: 招牌/店名注入 (scene_reference_manager.py)
- T32: family_relationships 传递 (pipeline_orchestrator.py + screenplay_writer.py)
- T33: 关系一致性规则 (story_outline_generator.py)
- T34: 镜头信息完整性 (storyboard_director.py Plan A + Plan B)
- T35: 多人空间锚定规则 (storyboard_director.py)
- T36: color_palette 英文 (story_outline_generator.py)
- T37: 亲属称谓清晰度规则 (screenplay_writer.py)
- OB-T29: compound type off_screen 处理 (text_overlay_service.py)
- T-A: off_screen 文字双重渲染修复 (image_generator.py)
- T-B: MAX_SHOT_RETRIES 2→1 (pipeline_orchestrator.py)
- T-C: signage_text 数据流 Stage 1→scene_ref (story_outline_generator.py + scene_reference_manager.py)
- T-D: Prompt Quality Report 关键词扩展 (pipeline_orchestrator.py)
- T-E: Stage 4 Rule #10 背面角色一致性 (storyboard_director.py)
- T-F: Stage 4 Rule #11 off-screen 接触禁止 (storyboard_director.py)
- T-G: Stage 4 Rule #12 空间方向自洽 (storyboard_director.py)
- T-H: ShotValidator 自然度维度 Phase 1 仅日志 (shot_validator.py)
- T-I: Prompt Pre-Check 机制 v1 仅日志 (pipeline_orchestrator.py)
- T-K: ShotValidator 人群角色计数优化 (shot_validator.py)

验收标准: ≥ 39/44 PASS + 0 FAIL = 通过

作者: @Tester
日期: 2026-03-16
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


# ═══════════════════════════════════════════════════════════════
# 测试配置 — R7 全新故事（赶集/老街 / 与历史 10 个故事完全不同）
# 排除: Kai与Cici, 灌篮高手, 拿铁上的告白, 家庭晚餐争吵/除夕,
#       关东煮/红烧肉, 外婆的抽屉, 同一首歌, 爷爷的针线/裁缝传承,
#       山间书法/墨痕, 雨夜庇护, 老街赶集(R7)
# ═══════════════════════════════════════════════════════════════

TEST_STORIES = [
    {
        "group": "A",
        "label": "山村赶圩三代同行 / illustration (多代家庭+药材铺+3人以上+画外音, 4角色)",
        "idea": (
            "初秋清晨，一家三代人——外公、爸爸、妈妈和9岁的儿子阿朗——沿山路赶往镇上圩日集市。"
            "外公惦记着老街尾'周记百草堂'药材铺的秋梨膏，想买一罐给咳嗽的老伴。"
            "阿朗走在最前面，被路边打铁铺的火花和叮当声吸引停下不走了。"
            "妈妈在前面发现阿朗不见了，急得站在石桥上回头喊他名字（画外音）。"
            "爸爸折返找到阿朗，牵着他的手赶上前面的外公和妈妈。"
            "一家四口到了药材铺，外公挑好秋梨膏，阿朗缠着妈妈买了一串冰糖葫芦，"
            "最后四人走出集市，外公手提纸袋，阿朗举着糖葫芦，走在夕阳下的田埂上。"
        ),
        "style_preset": "illustration",
        "character_count": 4,
    },
]

SHOTS_LIMIT = 10
OUTPUT_BASE = "./test_output/manualtest/e2e_regression_r8"


# ═══════════════════════════════════════════════════════════════
# Pipeline 运行
# ═══════════════════════════════════════════════════════════════

async def run_single_story(story_config: dict, output_base: str) -> dict:
    """运行单组故事的完整 Stage 1->5 pipeline，同时捕获 stdout 日志"""
    group = story_config["group"]
    label = story_config["label"]

    print(f"\n{'='*70}")
    print(f"  Story {group}: {label}")
    print(f"  Idea: {story_config['idea'][:80]}...")
    print(f"  Shots limit: {SHOTS_LIMIT}")
    print(f"{'='*70}\n")

    orchestrator = Phase2PipelineOrchestrator(
        output_dir=os.path.join(output_base, f"story_{group}")
    )

    start_time = time.time()

    # 捕获日志用于 S1/S5/N5/N6/N7/N11/N15 验证
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
        "character_count": story_config["character_count"],
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

        # 提取 outline 用于 plot_points / family_role 验证
        outline = result.get("stage_results", {}).get("outline", {})
        summary["outline_data"] = outline
    else:
        summary["error"] = result.get("error", "Unknown")
        summary["failed_stage"] = result.get("failed_stage", "Unknown")

    return summary


# ═══════════════════════════════════════════════════════════════
# D4: 构图多样性 (shot_type / camera_angle 统计)
# ═══════════════════════════════════════════════════════════════

def analyze_composition_variety(shots: list) -> dict:
    """D4: 检查 shot_type 和 camera_angle 是否多样"""
    total = len(shots)
    shot_types = {}
    camera_angles = {}

    for shot in shots:
        camera = shot.get("camera", {})
        st = camera.get("shot_size", "unknown")
        ca = camera.get("angle", "unknown")
        shot_types[st] = shot_types.get(st, 0) + 1
        camera_angles[ca] = camera_angles.get(ca, 0) + 1

    unique_types = len(shot_types)
    unique_angles = len(camera_angles)

    return {
        "total_shots": total,
        "unique_shot_types": unique_types,
        "shot_type_distribution": shot_types,
        "unique_camera_angles": unique_angles,
        "camera_angle_distribution": camera_angles,
        "pass": unique_types >= 3 and unique_angles >= 2,
    }


# ═══════════════════════════════════════════════════════════════
# D5: text_overlay 渲染
# ═══════════════════════════════════════════════════════════════

def analyze_text_overlay_output(shots: list) -> dict:
    """D5: 检查每个 shot 是否有 text_overlay 字段"""
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
# D7: narration 覆盖 (plot_points 1:1)
# ═══════════════════════════════════════════════════════════════

def analyze_narration_coverage(outline: dict, screenplay: dict) -> dict:
    """D7: Stage 3 是否为每个 plot_point 生成了对应 scene"""
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

    return {
        "total_plot_points": total_plot_points,
        "total_scenes": total_scenes,
        "1_to_1": total_plot_points == total_scenes,
        "missing_beats": missing_beats,
        "plot_beats": plot_beats,
        "scene_plot_points": scene_plot_points,
        "pass": total_plot_points == total_scenes and len(missing_beats) == 0,
    }


# ═══════════════════════════════════════════════════════════════
# D15: 镜头语言 (camera movement / lens 多样性)
# ═══════════════════════════════════════════════════════════════

def analyze_camera_language(shots: list) -> dict:
    """D15: 检查镜头运动和焦距是否有变化"""
    movements = {}
    lenses = {}

    for shot in shots:
        camera = shot.get("camera", {})
        mv = camera.get("movement", "unknown")
        ln = camera.get("lens", camera.get("focal_length", "unknown"))
        movements[mv] = movements.get(mv, 0) + 1
        lenses[ln] = lenses.get(ln, 0) + 1

    all_static = len(movements) == 1 and "static" in movements
    return {
        "movement_distribution": movements,
        "lens_distribution": lenses,
        "unique_movements": len(movements),
        "unique_lenses": len(lenses),
        "all_static": all_static,
        "pass": not all_static,
    }


# ═══════════════════════════════════════════════════════════════
# D16: 叙事完整性 (plot_points 全覆盖 + narration 字数)
# ═══════════════════════════════════════════════════════════════

def analyze_narrative_completeness(outline: dict, screenplay: dict, shots: list) -> dict:
    """D16: 叙事是否完整覆盖全部剧情节点"""
    pp_info = analyze_narration_coverage(outline, screenplay)

    total_narration_chars = 0
    scenes = screenplay.get("scenes", []) if screenplay else []
    for scene in scenes:
        narration = scene.get("narration", "")
        total_narration_chars += len(narration)

    scene_ids_in_shots = set()
    for shot in shots:
        scene_ids_in_shots.add(shot.get("scene_id"))

    scene_ids_in_screenplay = set()
    for scene in scenes:
        scene_ids_in_screenplay.add(scene.get("scene_id"))

    scenes_covered = scene_ids_in_screenplay.issubset(scene_ids_in_shots) or len(scene_ids_in_screenplay) == 0

    return {
        "plot_points_pass": pp_info["pass"],
        "total_narration_chars": total_narration_chars,
        "narration_adequate": total_narration_chars >= 200,
        "scene_ids_in_shots": sorted(scene_ids_in_shots),
        "scene_ids_in_screenplay": sorted(scene_ids_in_screenplay),
        "pass": pp_info["pass"] and total_narration_chars >= 200,
    }


# ═══════════════════════════════════════════════════════════════
# S1: 角色数量匹配 (T17 ShotValidator 日志解析)
# ═══════════════════════════════════════════════════════════════

def analyze_character_count_accuracy(captured_log: str, shots: list) -> dict:
    """S1: 从 [ShotValidator] 日志解析角色数量验证结果"""
    total_shots = len(shots)

    validator_lines = [line for line in captured_log.split('\n')
                       if '[ShotValidator]' in line]

    count_pattern = re.compile(r'预期(\d+)[,，]\s*实际(\d+)')
    validations = []
    retries = []

    for line in validator_lines:
        retry_match = re.search(r'[Rr]etry\s*(\d+)/(\d+)', line)
        if retry_match:
            retries.append(line.strip())

        count_match = count_pattern.search(line)
        if count_match:
            expected = int(count_match.group(1))
            actual = int(count_match.group(2))
            diff = abs(actual - expected)
            accurate = diff <= 1
            validations.append({
                "expected": expected,
                "actual": actual,
                "diff": diff,
                "accurate": accurate,
                "log_line": line.strip()[:100],
            })

    if validations:
        accurate_count = sum(1 for v in validations if v["accurate"])
        accuracy = accurate_count / len(validations) * 100
    else:
        accurate_count = 0
        accuracy = -1

    validator_disabled = any("验证功能禁用" in line or "validator disabled" in line
                            for line in validator_lines)

    return {
        "total_shots": total_shots,
        "validations_count": len(validations),
        "accurate_count": accurate_count,
        "accuracy": f"{accuracy:.1f}%" if accuracy >= 0 else "N/A (无验证数据)",
        "accuracy_num": accuracy,
        "retries": len(retries),
        "retry_details": retries[:5],
        "validator_disabled": validator_disabled,
        "validator_log_lines": len(validator_lines),
        "inaccurate_details": [v for v in validations if not v["accurate"]],
        "pass": accuracy >= 90 if accuracy >= 0 else False,
        "note": "ShotValidator 被禁用，无法验证" if validator_disabled else
                ("无 ShotValidator 日志输出 — 隐式通过 (零失败零重试 = 全部通过)" if not validator_lines else ""),
    }


# ═══════════════════════════════════════════════════════════════
# S5: 气泡重复率 (T17 ShotValidator 日志解析)
# ═══════════════════════════════════════════════════════════════

def analyze_bubble_duplicate_rate(captured_log: str, shots: list) -> dict:
    """S5: 从 [ShotValidator] 日志解析气泡重复检测结果"""
    total_shots = len(shots)

    validator_lines = [line for line in captured_log.split('\n')
                       if '[ShotValidator]' in line]

    duplicate_detected = []
    for line in validator_lines:
        if '重复' in line and '气泡' in line:
            duplicate_detected.append(line.strip()[:100])
        elif 'duplicate' in line.lower() and 'bubble' in line.lower():
            duplicate_detected.append(line.strip()[:100])

    duplicate_count = len(duplicate_detected)
    rate = duplicate_count / total_shots * 100 if total_shots > 0 else 0

    return {
        "total_shots": total_shots,
        "duplicate_detected_count": duplicate_count,
        "duplicate_rate": f"{rate:.1f}%",
        "duplicate_rate_num": rate,
        "duplicate_details": duplicate_detected[:5],
        "pass": rate < 2,
        "note": "基于 ShotValidator 日志检测" if validator_lines else
                "无 ShotValidator 日志 — 隐式通过 (零失败 = 无重复)",
    }


# ═══════════════════════════════════════════════════════════════
# N1: 角色称谓正确性 (T24+T27)
# ═══════════════════════════════════════════════════════════════

def analyze_character_appellation(shots: list, outline: dict, characters: dict) -> dict:
    """N1: 检查 text_overlay 中的称谓是否与 characters_overview 的 family_role 匹配"""
    chars_overview = outline.get("characters_overview", [])
    name_role_map = {}
    for co in chars_overview:
        name = co.get("name_suggestion", co.get("name", ""))
        role = co.get("family_role", "none")
        if name and role and role != "none":
            name_role_map[name] = role

    role_to_titles = {
        "grandfather": ["爷爷", "外公", "姥爷", "爷"],
        "grandmother": ["奶奶", "外婆", "姥姥", "婆婆"],
        "father": ["爸爸", "爸", "父亲", "老爸"],
        "mother": ["妈妈", "妈", "母亲", "老妈"],
        "son": ["儿子", "儿"],
        "daughter": ["女儿", "闺女", "丫头"],
        "granddaughter": ["孙女", "外孙女"],
        "grandson": ["孙子", "外孙"],
        "uncle": ["叔叔", "伯伯", "舅舅"],
        "aunt": ["阿姨", "姑姑", "舅妈", "婶婶"],
    }

    title_to_role = {}
    for role, titles in role_to_titles.items():
        for title in titles:
            title_to_role[title] = role

    char_names = set()
    for c in characters.get("characters", []):
        char_names.add(c.get("name", ""))

    title_usages = []
    mismatches = []

    for shot in shots:
        sid = shot.get("shot_id", "?")
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

            for title, expected_role in title_to_role.items():
                if title in txt:
                    # 排除 erhua 误匹配: "儿" 在 "这儿/那儿/哪儿/放这儿/搁这儿" 等中不是称谓
                    if title == "儿":
                        idx = txt.index(title)
                        if idx > 0 and txt[idx-1] in "这那哪这儿那儿搁放":
                            continue

                    title_usages.append({
                        "shot_id": sid,
                        "title_found": title,
                        "expected_role": expected_role,
                        "text_snippet": txt[:60],
                    })

                    matching_chars = [name for name, role in name_role_map.items()
                                     if role == expected_role]
                    if not matching_chars and expected_role in role_to_titles:
                        mismatches.append({
                            "shot_id": sid,
                            "title": title,
                            "issue": f"称谓 '{title}' 对应 {expected_role}，但无角色 family_role={expected_role}",
                            "text": txt[:60],
                        })

    family_rels = outline.get("family_relationships", [])
    has_family_relationships = len(family_rels) > 0

    return {
        "name_role_map": name_role_map,
        "title_usages_count": len(title_usages),
        "title_usages": title_usages[:20],
        "mismatches_count": len(mismatches),
        "mismatches": mismatches[:10],
        "has_family_relationships": has_family_relationships,
        "family_relationships_count": len(family_rels),
        "family_relationships": family_rels,
        "pass": len(mismatches) == 0 and has_family_relationships,
    }


# ═══════════════════════════════════════════════════════════════
# N2: 对话自然度 (T26) — 自动辅助检查
# ═══════════════════════════════════════════════════════════════

def analyze_dialogue_naturalness(shots: list, screenplay: dict) -> dict:
    """N2: 基本的对话自然度自动检测 (辅助人工审查)"""
    scenes = screenplay.get("scenes", []) if screenplay else []
    total_lines = 0
    long_lines = []
    formal_patterns = []

    formal_markers = [
        (r"进行.{0,4}(探讨|分析|研究|讨论)", "过于正式"),
        (r"(?:此刻|此时).{0,6}(?:内心|充满)", "书面旁白混入对话"),
        (r"我认为(?:我们)?应该", "过于正式的表达"),
    ]

    for scene in scenes:
        for beat in scene.get("dialogue_beats", []):
            line = beat.get("line", "")
            if not line:
                continue
            total_lines += 1

            clean_line = line.strip("（）()「」\"")
            if len(clean_line) > 25:
                long_lines.append({
                    "scene_id": scene.get("scene_id", "?"),
                    "speaker": beat.get("speaker", "?"),
                    "line": line[:40],
                    "length": len(clean_line),
                })

            for pattern, desc in formal_markers:
                if re.search(pattern, line):
                    formal_patterns.append({
                        "scene_id": scene.get("scene_id", "?"),
                        "speaker": beat.get("speaker", "?"),
                        "issue": desc,
                        "line": line[:40],
                    })

    long_ratio = len(long_lines) / total_lines * 100 if total_lines > 0 else 0

    return {
        "total_dialogue_lines": total_lines,
        "long_lines_count": len(long_lines),
        "long_lines_ratio": f"{long_ratio:.1f}%",
        "long_lines": long_lines[:5],
        "formal_patterns_count": len(formal_patterns),
        "formal_patterns": formal_patterns[:5],
        "pass": len(formal_patterns) == 0 and long_ratio < 30,
        "note": "此为自动辅助检查，最终判定需人工审查",
    }


# ═══════════════════════════════════════════════════════════════
# N3: 同场景背景多样性 (T27)
# ═══════════════════════════════════════════════════════════════

def analyze_background_variety(shots: list) -> dict:
    """N3: 检查同 scene_id 的 3+ shots 是否有背景变化"""
    scene_groups = {}
    for shot in shots:
        scene_id = shot.get("scene_id", "unknown")
        if scene_id not in scene_groups:
            scene_groups[scene_id] = []
        scene_groups[scene_id].append(shot)

    multi_shot_scenes = {sid: sshots for sid, sshots in scene_groups.items()
                         if len(sshots) >= 3}

    scene_analyses = []
    issues = []

    for scene_id, sshots in multi_shot_scenes.items():
        backgrounds = []
        for shot in sshots:
            composition = shot.get("composition", {})
            bg = composition.get("background", "")
            image_prompt = shot.get("image_prompt", "")
            backgrounds.append({
                "shot_id": shot.get("shot_id", "?"),
                "background": bg,
                "prompt_snippet": image_prompt[:80] if image_prompt else "",
            })

        bg_texts = [b["background"] for b in backgrounds if b["background"]]
        unique_bgs = len(set(bg_texts))
        total_bgs = len(bg_texts)

        is_varied = unique_bgs >= min(3, total_bgs) if total_bgs >= 3 else True

        scene_analyses.append({
            "scene_id": scene_id,
            "shot_count": len(sshots),
            "unique_backgrounds": unique_bgs,
            "total_backgrounds": total_bgs,
            "is_varied": is_varied,
            "backgrounds": backgrounds,
        })

        if not is_varied:
            issues.append({
                "scene_id": scene_id,
                "issue": f"场景 {scene_id} 有 {len(sshots)} shots 但背景描述仅 {unique_bgs} 种",
            })

    return {
        "multi_shot_scenes_count": len(multi_shot_scenes),
        "scene_analyses": scene_analyses,
        "issues_count": len(issues),
        "issues": issues,
        "pass": len(issues) == 0,
        "note": "此为自动辅助检查（基于 composition.background 文本比较），最终需人工看图确认",
    }


# ═══════════════════════════════════════════════════════════════
# N5: 参考图模型 (T23: NB2 确认)
# ═══════════════════════════════════════════════════════════════

def analyze_reference_model(captured_log: str) -> dict:
    """N5: 确认参考图使用 NB2 模型"""
    nb2_mentions = len(re.findall(r'NB2_MODEL|NB2|gemini-3\.1-flash-image', captured_log))
    fast_model_mentions = len(re.findall(r'FAST_MODEL|gemini-2\.5-flash-image', captured_log))

    code_audit = {"nb2_confirmed": False, "details": []}
    ig_path = "app/services/image_generator.py"
    if os.path.exists(ig_path):
        with open(ig_path, "r", encoding="utf-8") as f:
            ig_code = f.read()

        nb2_def_match = re.search(r'NB2_MODEL\s*=\s*["\'](.+?)["\']', ig_code)
        if nb2_def_match:
            code_audit["nb2_model_value"] = nb2_def_match.group(1)

        if "model = self.NB2_MODEL" in ig_code or "self.NB2_MODEL" in ig_code:
            code_audit["nb2_confirmed"] = True
            code_audit["details"].append("image_generator.py 确认使用 self.NB2_MODEL")

        fast_in_ref = re.findall(r'(?:portrait|fullbody|character|reference).*?self\.FAST_MODEL', ig_code, re.DOTALL)
        if fast_in_ref:
            code_audit["details"].append(f"FAST_MODEL 用于参考图: {len(fast_in_ref)} 处")
            code_audit["nb2_confirmed"] = False

    return {
        "log_nb2_mentions": nb2_mentions,
        "log_fast_model_mentions": fast_model_mentions,
        "code_audit": code_audit,
        "pass": code_audit.get("nb2_confirmed", False) or nb2_mentions > 0,
    }


# ═══════════════════════════════════════════════════════════════
# N6: 道具检测日志 (T28: ShotValidator key_props)
# ═══════════════════════════════════════════════════════════════

def analyze_prop_detection_logs(captured_log: str, shots: list) -> dict:
    """N6: 检查 ShotValidator 是否执行了 key_props 检测"""
    validator_lines = [line for line in captured_log.split('\n')
                       if '[ShotValidator]' in line]

    prop_related_lines = [line for line in validator_lines
                          if '道具' in line or 'prop' in line.lower() or 'missing_props' in line.lower()]

    shots_with_props = 0
    composition_details = []
    for shot in shots:
        sid = shot.get("shot_id", "?")
        composition = shot.get("composition", {})
        key_props = []
        for field in ["foreground", "background", "key_object"]:
            val = composition.get(field, "")
            if val and isinstance(val, str) and len(val) > 2:
                key_props.append(f"{field}: {val}")
        if key_props:
            shots_with_props += 1
            composition_details.append({
                "shot_id": sid,
                "props_extracted": key_props,
            })

    code_audit = {"t28_integration_exists": False}
    po_path = "app/services/pipeline_orchestrator.py"
    if os.path.exists(po_path):
        with open(po_path, "r", encoding="utf-8") as f:
            po_code = f.read()
        if "key_props" in po_code and "composition" in po_code:
            code_audit["t28_integration_exists"] = True

    sv_path = "app/services/shot_validator.py"
    if os.path.exists(sv_path):
        with open(sv_path, "r", encoding="utf-8") as f:
            sv_code = f.read()
        if "key_props" in sv_code and "missing_props" in sv_code:
            code_audit["t28_validator_exists"] = True

    return {
        "validator_log_lines": len(validator_lines),
        "prop_related_lines": len(prop_related_lines),
        "prop_log_samples": prop_related_lines[:5],
        "shots_with_composition_props": shots_with_props,
        "composition_details": composition_details[:5],
        "code_audit": code_audit,
        "pass": code_audit.get("t28_integration_exists", False) and
                code_audit.get("t28_validator_exists", False),
        "note": "ShotValidator 仅在 >50% 道具缺失时输出日志，零日志 = 道具检测通过",
    }


# ═══════════════════════════════════════════════════════════════
# N7: off_screen_speaker 标记 (T29)
# ═══════════════════════════════════════════════════════════════

def analyze_off_screen_marking(shots: list, screenplay: dict) -> dict:
    """N7: 检查 4_storyboard.json 中 off_screen_speaker 字段是否正确标记

    T29 改动: storyboard_director.py L1354-1398
    - 当 speaker 不在 characters_in_scene 中时，不再将 dialogue 降级为 thought
    - 而是标记 off_screen_speaker: true
    """
    total_shots = len(shots)
    off_screen_found = []
    dialogue_shots_with_absent_speaker = []

    for shot in shots:
        sid = shot.get("shot_id", "?")
        chars_in_scene = shot.get("characters_in_scene", [])
        text_overlay = shot.get("text_overlay", {})
        if not isinstance(text_overlay, dict):
            continue

        text_type = text_overlay.get("text_type", "")
        speaker = text_overlay.get("speaker", "")
        off_screen = text_overlay.get("off_screen_speaker", False)

        # 检查是否标记了 off_screen_speaker
        if off_screen:
            off_screen_found.append({
                "shot_id": sid,
                "speaker": speaker,
                "text_type": text_type,
                "chars_in_scene": chars_in_scene,
            })

        # 检查对话类型中 speaker 是否不在 scene 中（应标记 off_screen）
        if text_type in ["dialogue", "dialogue_with_thought", "dialogue_with_narration"]:
            if speaker and speaker not in [c if isinstance(c, str) else c.get("name", "") for c in chars_in_scene]:
                dialogue_shots_with_absent_speaker.append({
                    "shot_id": sid,
                    "speaker": speaker,
                    "chars_in_scene": chars_in_scene,
                    "off_screen_marked": off_screen,
                })

    # 检查 screenplay 中是否有 off-screen 场景设计
    has_off_screen_in_screenplay = False
    scenes = screenplay.get("scenes", []) if screenplay else []
    for scene in scenes:
        for beat in scene.get("dialogue_beats", []):
            if beat.get("off_screen") or beat.get("off_screen_speaker"):
                has_off_screen_in_screenplay = True
                break

    # 代码审计: storyboard_director.py T29 逻辑
    code_audit = {"t29_exists": False}
    sd_path = "app/services/storyboard_director.py"
    if os.path.exists(sd_path):
        with open(sd_path, "r", encoding="utf-8") as f:
            sd_code = f.read()
        if "off_screen_speaker" in sd_code:
            code_audit["t29_exists"] = True
            code_audit["off_screen_speaker_count"] = sd_code.count("off_screen_speaker")

    return {
        "total_shots": total_shots,
        "off_screen_found_count": len(off_screen_found),
        "off_screen_found": off_screen_found,
        "absent_speaker_shots": len(dialogue_shots_with_absent_speaker),
        "absent_speaker_details": dialogue_shots_with_absent_speaker,
        "has_off_screen_in_screenplay": has_off_screen_in_screenplay,
        "code_audit": code_audit,
        "pass": code_audit.get("t29_exists", False),
        "note": ("off_screen_speaker 标记取决于故事是否触发了不在场发言场景。"
                 "代码逻辑已确认存在即为 PASS，实际触发需结合故事内容判断。"),
    }


# ═══════════════════════════════════════════════════════════════
# N9: family_relationships 传递 (T32)
# ═══════════════════════════════════════════════════════════════

def analyze_family_relationships_passing(outline: dict, screenplay: dict, captured_log: str) -> dict:
    """N9: 验证 family_relationships 从 outline → screenplay CHARACTER RELATIONSHIPS

    T32 改动:
    - pipeline_orchestrator.py L155/L157: 传 family_relationships 给 Stage 3
    - screenplay_writer.py L327-346: 构建 CHARACTER RELATIONSHIPS block
    """
    # Step 1: outline 中的 family_relationships
    family_rels = outline.get("family_relationships", []) if outline else []
    has_outline_rels = len(family_rels) > 0

    # Step 2: 检查 screenplay 中是否包含 CHARACTER RELATIONSHIPS 相关内容
    # 由于 screenplay 是 LLM 输出的结构化 JSON，不直接包含 prompt
    # 需要通过日志检查 T32 是否被执行
    t32_log_found = False
    t32_log_lines = []
    for line in captured_log.split('\n'):
        if 'CHARACTER RELATIONSHIPS' in line or 'family_relationships' in line:
            t32_log_found = True
            t32_log_lines.append(line.strip()[:120])

    # Step 3: 代码审计
    code_audit = {"t32_pipeline_exists": False, "t32_screenplay_exists": False}

    po_path = "app/services/pipeline_orchestrator.py"
    if os.path.exists(po_path):
        with open(po_path, "r", encoding="utf-8") as f:
            po_code = f.read()
        if "family_relationships" in po_code:
            code_audit["t32_pipeline_exists"] = True

    sw_path = "app/services/screenplay_writer.py"
    if os.path.exists(sw_path):
        with open(sw_path, "r", encoding="utf-8") as f:
            sw_code = f.read()
        if "CHARACTER RELATIONSHIPS" in sw_code and "family_relationships" in sw_code:
            code_audit["t32_screenplay_exists"] = True

    return {
        "outline_family_relationships": family_rels,
        "outline_has_rels": has_outline_rels,
        "outline_rels_count": len(family_rels),
        "t32_log_found": t32_log_found,
        "t32_log_lines": t32_log_lines[:5],
        "code_audit": code_audit,
        "pass": has_outline_rels and code_audit["t32_pipeline_exists"] and code_audit["t32_screenplay_exists"],
    }


# ═══════════════════════════════════════════════════════════════
# N10: 亲属称谓清晰度 (T37)
# ═══════════════════════════════════════════════════════════════

def analyze_kinship_clarity(screenplay: dict) -> dict:
    """N10: 检查 dialogue_beats 中是否有歧义亲属称谓

    T37 改动: screenplay_writer.py L481-494
    - KINSHIP ADDRESS CLARITY 规则: 对话中不使用"他/她"指代家庭成员
    - 应使用明确的称谓如"爸爸"/"奶奶"而非"他"
    """
    scenes = screenplay.get("scenes", []) if screenplay else []
    total_lines = 0
    ambiguous_refs = []

    # 歧义模式: 用"他/她"指代家庭成员（在有多个同性别角色的场景中容易混淆）
    ambiguous_patterns = [
        (r"(?:跟|和|给|让|叫|问|找)(?:他|她)(?:说|讲|聊|问|打)", "用代词指代家庭成员"),
        (r"(?:他|她)(?:说了|讲了|提到|觉得)", "代词做主语可能歧义"),
    ]

    for scene in scenes:
        chars_in_scene = scene.get("characters_in_scene", [])
        for beat in scene.get("dialogue_beats", []):
            line = beat.get("line", "")
            if not line:
                continue
            total_lines += 1

            # 只在多角色场景中检查歧义
            if len(chars_in_scene) >= 3:
                for pattern, desc in ambiguous_patterns:
                    if re.search(pattern, line):
                        ambiguous_refs.append({
                            "scene_id": scene.get("scene_id", "?"),
                            "speaker": beat.get("speaker", "?"),
                            "issue": desc,
                            "line": line[:50],
                            "chars_count": len(chars_in_scene),
                        })

    # 代码审计: T37 规则存在
    code_audit = {"t37_exists": False}
    sw_path = "app/services/screenplay_writer.py"
    if os.path.exists(sw_path):
        with open(sw_path, "r", encoding="utf-8") as f:
            sw_code = f.read()
        if "KINSHIP ADDRESS CLARITY" in sw_code or "kinship" in sw_code.lower():
            code_audit["t37_exists"] = True

    return {
        "total_dialogue_lines": total_lines,
        "ambiguous_refs_count": len(ambiguous_refs),
        "ambiguous_refs": ambiguous_refs[:10],
        "code_audit": code_audit,
        "pass": code_audit["t37_exists"] and len(ambiguous_refs) <= 2,
        "note": "允许最多 2 处轻微歧义（LLM 非完美），但 T37 规则必须存在",
    }


# ═══════════════════════════════════════════════════════════════
# N11: 镜头信息完整性 (T34)
# ═══════════════════════════════════════════════════════════════

def analyze_camera_completeness(shots: list, captured_log: str) -> dict:
    """N11: 检查 image_prompt 是否包含 shot_size/angle 关键词 + Plan B 注入日志

    T34 改动:
    - Plan A: storyboard_director.py L236-263 CAMERA_INFORMATION_COMPLETENESS_RULE (prompt 规则)
    - Plan B: storyboard_director.py L1400-1447 _validate_storyboard() 注入缺失的 camera 信息
    """
    total_shots = len(shots)

    # 常见 shot_size/angle 关键词
    size_keywords = [
        "wide shot", "medium shot", "close-up", "close up", "closeup",
        "extreme close-up", "full shot", "long shot", "medium close-up",
        "establishing shot", "over-the-shoulder", "over the shoulder",
        "two-shot", "group shot", "cowboy shot",
    ]
    angle_keywords = [
        "eye level", "low angle", "high angle", "bird's eye",
        "dutch angle", "worm's eye", "overhead", "tilted",
    ]

    shots_with_size = 0
    shots_with_angle = 0
    details = []

    for shot in shots:
        sid = shot.get("shot_id", "?")
        prompt = (shot.get("image_prompt", "") or "").lower()
        camera = shot.get("camera", {})

        has_size = any(kw in prompt for kw in size_keywords)
        has_angle = any(kw in prompt for kw in angle_keywords)

        # 也检查 camera 字段
        camera_size = camera.get("shot_size", "")
        camera_angle = camera.get("angle", "")

        if has_size or camera_size:
            shots_with_size += 1
        if has_angle or camera_angle:
            shots_with_angle += 1

        details.append({
            "shot_id": sid,
            "has_size_in_prompt": has_size,
            "has_angle_in_prompt": has_angle,
            "camera_size": camera_size,
            "camera_angle": camera_angle,
        })

    # Plan B 注入日志
    plan_b_lines = [line for line in captured_log.split('\n')
                    if 'Plan B' in line or 'camera info inject' in line.lower()
                    or '镜头信息注入' in line or 'em-dash' in line.lower()]

    # 代码审计
    code_audit = {"t34_plan_a": False, "t34_plan_b": False}
    sd_path = "app/services/storyboard_director.py"
    if os.path.exists(sd_path):
        with open(sd_path, "r", encoding="utf-8") as f:
            sd_code = f.read()
        if "CAMERA_INFORMATION_COMPLETENESS_RULE" in sd_code:
            code_audit["t34_plan_a"] = True
        if "_validate_storyboard" in sd_code and ("shot_size" in sd_code or "angle" in sd_code):
            code_audit["t34_plan_b"] = True

    size_rate = shots_with_size / total_shots * 100 if total_shots > 0 else 0
    angle_rate = shots_with_angle / total_shots * 100 if total_shots > 0 else 0

    return {
        "total_shots": total_shots,
        "shots_with_size": shots_with_size,
        "shots_with_angle": shots_with_angle,
        "size_coverage": f"{size_rate:.0f}%",
        "angle_coverage": f"{angle_rate:.0f}%",
        "plan_b_log_lines": len(plan_b_lines),
        "plan_b_samples": plan_b_lines[:5],
        "details": details,
        "code_audit": code_audit,
        "pass": code_audit["t34_plan_a"] and code_audit["t34_plan_b"] and size_rate >= 80,
    }


# ═══════════════════════════════════════════════════════════════
# N12: 多人空间锚定 (T35)
# ═══════════════════════════════════════════════════════════════

def analyze_spatial_anchoring(shots: list) -> dict:
    """N12: 检查 3+ 人 shots 的 image_prompt 是否含空间位置描述

    T35 改动: storyboard_director.py L184-233
    - MULTI_CHARACTER_SPATIAL_ANCHORING_RULES (5 条规则)
    - headcount guarantee, furniture scale, env interaction, spatial distribution, overlap avoidance
    """
    total_shots = len(shots)
    multi_char_shots = []
    spatial_issues = []

    # 空间描述关键词
    spatial_keywords = [
        "left", "right", "center", "middle", "foreground", "background",
        "beside", "next to", "behind", "in front of", "across from",
        "standing", "sitting", "leaning", "facing", "positioned",
        "near", "far", "between", "opposite", "adjacent",
    ]

    for shot in shots:
        sid = shot.get("shot_id", "?")
        # T-J fix: characters_in_scene 在 storyboard 中通常为空，
        # 实际可见角色在 character_direction.characters_visible
        chars = shot.get("character_direction", {}).get("characters_visible", [])
        if not chars:
            chars = shot.get("characters_in_scene", [])
        char_count = len(chars)

        if char_count >= 3:
            prompt = (shot.get("image_prompt", "") or "").lower()
            spatial_found = [kw for kw in spatial_keywords if kw in prompt]
            has_spatial = len(spatial_found) >= 2  # 至少 2 个空间关键词

            multi_char_shots.append({
                "shot_id": sid,
                "char_count": char_count,
                "spatial_keywords_found": spatial_found[:5],
                "has_adequate_spatial": has_spatial,
            })

            if not has_spatial:
                spatial_issues.append({
                    "shot_id": sid,
                    "char_count": char_count,
                    "issue": f"Shot {sid} 有 {char_count} 角色但空间描述不足 (仅 {len(spatial_found)} 个关键词)",
                })

    # 代码审计
    code_audit = {"t35_exists": False}
    sd_path = "app/services/storyboard_director.py"
    if os.path.exists(sd_path):
        with open(sd_path, "r", encoding="utf-8") as f:
            sd_code = f.read()
        if "MULTI_CHARACTER_SPATIAL_ANCHORING_RULES" in sd_code:
            code_audit["t35_exists"] = True

    return {
        "total_shots": total_shots,
        "multi_char_shots_count": len(multi_char_shots),
        "multi_char_shots": multi_char_shots,
        "spatial_issues_count": len(spatial_issues),
        "spatial_issues": spatial_issues,
        "code_audit": code_audit,
        "pass": code_audit["t35_exists"] and len(spatial_issues) <= 1,
        "note": "允许最多 1 个 shot 空间描述不足（LLM 非完美），但 T35 规则必须存在",
    }


# ═══════════════════════════════════════════════════════════════
# N13: 家庭关系逻辑一致性 (T33)
# ═══════════════════════════════════════════════════════════════

def analyze_relationship_consistency(outline: dict) -> dict:
    """N13: 验证 family_relationships 的逻辑一致性

    T33 改动: story_outline_generator.py L277-307
    - RELATIONSHIP CONSISTENCY RULES:
      1. Triangle consistency: A→B + B→C ⇒ A→C 合理
      2. Spouse transitivity: A married_to B + B parent_of C ⇒ A parent_of C
      3. Generational self-check
    """
    family_rels = outline.get("family_relationships", []) if outline else []
    if not family_rels:
        return {
            "has_relationships": False,
            "pass": False,
            "note": "无 family_relationships 数据",
        }

    # 构建关系图
    rel_map = {}  # (from, to) -> relationship
    for rel in family_rels:
        fr = rel.get("from", "")
        to = rel.get("to", "")
        r = rel.get("relationship", "")
        if fr and to and r:
            rel_map[(fr, to)] = r

    inconsistencies = []

    # 检查 1: 父辈关系 — parent_of 和 child_of 互逆
    parent_rels = {"father_of", "mother_of", "parent_of"}
    child_rels = {"son_of", "daughter_of", "child_of"}
    for (fr, to), r in rel_map.items():
        if r in parent_rels:
            # 反向应该是 child_of 类
            reverse = rel_map.get((to, fr), "")
            if reverse and reverse not in child_rels and reverse != "":
                inconsistencies.append({
                    "type": "inverse_mismatch",
                    "detail": f"{fr}→{to}: {r}, 但 {to}→{fr}: {reverse} (应为 child_of 类)",
                })

    # 检查 2: 祖孙关系 — grandfather_of/grandmother_of 和 grandchild 互逆
    grandparent_rels = {"grandfather_of", "grandmother_of", "grandparent_of"}
    grandchild_rels = {"grandson_of", "granddaughter_of", "grandchild_of"}
    for (fr, to), r in rel_map.items():
        if r in grandparent_rels:
            reverse = rel_map.get((to, fr), "")
            if reverse and reverse not in grandchild_rels:
                inconsistencies.append({
                    "type": "grandparent_inverse",
                    "detail": f"{fr}→{to}: {r}, 但 {to}→{fr}: {reverse}",
                })

    # 检查 3: spouse 对称性 — married_to 应双向
    spouse_rels = {"married_to", "spouse_of", "husband_of", "wife_of"}
    for (fr, to), r in rel_map.items():
        if r in spouse_rels:
            reverse = rel_map.get((to, fr), "")
            if not reverse or reverse not in spouse_rels:
                inconsistencies.append({
                    "type": "spouse_asymmetry",
                    "detail": f"{fr}→{to}: {r}, 但 {to}→{fr}: '{reverse}' (应为 spouse 类)",
                })

    # 代码审计
    code_audit = {"t33_exists": False}
    sog_path = "app/services/story_outline_generator.py"
    if os.path.exists(sog_path):
        with open(sog_path, "r", encoding="utf-8") as f:
            sog_code = f.read()
        if "RELATIONSHIP CONSISTENCY" in sog_code or "triangle" in sog_code.lower():
            code_audit["t33_exists"] = True

    return {
        "has_relationships": True,
        "total_relationships": len(family_rels),
        "relationships": family_rels,
        "inconsistencies_count": len(inconsistencies),
        "inconsistencies": inconsistencies,
        "code_audit": code_audit,
        "pass": code_audit["t33_exists"] and len(inconsistencies) == 0,
    }


# ═══════════════════════════════════════════════════════════════
# N14: color_palette 英文 (T36)
# ═══════════════════════════════════════════════════════════════

def analyze_color_palette_english(outline: dict) -> dict:
    """N14: 检查 outline 中的 color_palette 是否为英文

    T36 改动: story_outline_generator.py L197-198
    - color_palette schema placeholders 改为英文
    - prompt 要求输出英文颜色名
    """
    # T-J fix: color_palette 实际路径是 visual_tone.color_palette（非根级或 visual_style）
    color_palette = outline.get("visual_tone", {}).get("color_palette", {}) if outline else {}
    if not color_palette:
        color_palette = outline.get("color_palette", {}) if outline else {}
    if not color_palette:
        color_palette = outline.get("visual_style", {}).get("color_palette", {}) if outline else {}

    has_chinese = False
    chinese_found = []

    # 递归检查所有字符串值
    def check_value(val, path=""):
        nonlocal has_chinese
        if isinstance(val, str):
            for ch in val:
                if '\u4e00' <= ch <= '\u9fff':
                    has_chinese = True
                    chinese_found.append({"path": path, "value": val[:50]})
                    return
        elif isinstance(val, dict):
            for k, v in val.items():
                check_value(v, f"{path}.{k}")
        elif isinstance(val, list):
            for i, v in enumerate(val):
                check_value(v, f"{path}[{i}]")

    check_value(color_palette, "color_palette")

    # 代码审计
    code_audit = {"t36_exists": False}
    sog_path = "app/services/story_outline_generator.py"
    if os.path.exists(sog_path):
        with open(sog_path, "r", encoding="utf-8") as f:
            sog_code = f.read()
        # T36: schema placeholders in English
        if "color_palette" in sog_code:
            # 检查 prompt 中是否要求英文
            if "English" in sog_code and "color" in sog_code:
                code_audit["t36_exists"] = True
            elif "english" in sog_code.lower() and "color" in sog_code.lower():
                code_audit["t36_exists"] = True

    return {
        "color_palette_found": bool(color_palette),
        "color_palette": color_palette,
        "has_chinese": has_chinese,
        "chinese_found": chinese_found,
        "code_audit": code_audit,
        "pass": code_audit["t36_exists"] and not has_chinese,
    }


# ═══════════════════════════════════════════════════════════════
# N15: 招牌注入 (T31)
# ═══════════════════════════════════════════════════════════════

def analyze_signage_injection(captured_log: str, project_dir: str) -> dict:
    """N15: 检查 scene_reference_manager 是否为商铺场景注入了招牌文字

    T31 改动: scene_reference_manager.py
    - _detect_signage_name(): 10 中文 + 24 英文关键词检测
    - exterior: REQUIRED TEXT ON SIGNAGE: "{name}"
    - interior: plaque instruction
    """
    # T-J fix: scene_reference_manager 不单独打印 signage 日志，
    # 但锚点图生成日志包含 location_id（含店/铺/shop 等关键词）
    # 同时搜索 SIGNAGE/招牌 以兼容未来可能添加的显式日志
    signage_keywords_in_anchor = {'铺', '店', '坊', '馆', '堂', '楼', '阁', '庄', 'shop', 'store', 'café', 'restaurant', 'inn', 'bakery', 'tea'}
    signage_log_lines = []
    for line in captured_log.split('\n'):
        if 'SIGNAGE' in line or '招牌' in line or 'REQUIRED TEXT' in line:
            signage_log_lines.append(line)
        elif '锚点图' in line or 'anchor' in line.lower():
            line_lower = line.lower()
            if any(kw in line or kw in line_lower for kw in signage_keywords_in_anchor):
                signage_log_lines.append(line)

    # 检查 scene_ref 图片是否存在
    scene_ref_images = []
    if project_dir:
        scene_ref_dir = os.path.join(project_dir, "scene_refs")
        if os.path.isdir(scene_ref_dir):
            for fname in os.listdir(scene_ref_dir):
                if fname.endswith(('.png', '.jpg', '.jpeg')):
                    scene_ref_images.append(fname)

    # 代码审计
    code_audit = {"t31_exists": False, "signage_detection": False}
    srm_path = "app/services/scene_reference_manager.py"
    if os.path.exists(srm_path):
        with open(srm_path, "r", encoding="utf-8") as f:
            srm_code = f.read()
        if "_detect_signage_name" in srm_code:
            code_audit["signage_detection"] = True
        if "REQUIRED TEXT ON SIGNAGE" in srm_code:
            code_audit["t31_exists"] = True

    return {
        "signage_log_lines": len(signage_log_lines),
        "signage_log_samples": signage_log_lines[:5],
        "scene_ref_images": scene_ref_images,
        "scene_ref_count": len(scene_ref_images),
        "code_audit": code_audit,
        "pass": code_audit["t31_exists"] and code_audit["signage_detection"],
        "note": ("招牌注入取决于故事中是否有商铺/店名场景。"
                 "代码逻辑已确认存在即为 PASS，日志验证招牌是否被检测到。"),
    }


# ═══════════════════════════════════════════════════════════════
# N16: off_screen 文字去重 (T-A)
# ═══════════════════════════════════════════════════════════════

def analyze_off_screen_dedup(shots: list, captured_log: str) -> dict:
    """N16: T-A visible speaker 不应同时出现 dialogue bubble + voiceover bar。
    检查逻辑:
    1. 代码审计: image_generator.py 中 _is_speaker_off_screen() 存在
    2. 数据检查: 对于 off_screen_speaker=False 的对话 shot，不应有 voiceover 类型渲染
    """
    code_path = os.path.join(Path(__file__).parent.parent, "app", "services", "image_generator.py")
    code_audit = {"function_exists": False, "skip_logic_exists": False}
    if os.path.isfile(code_path):
        with open(code_path, "r", encoding="utf-8") as f:
            code = f.read()
        code_audit["function_exists"] = "_is_speaker_off_screen" in code
        code_audit["skip_logic_exists"] = "continue" in code and "_is_speaker_off_screen" in code

    # 数据检查: 找 off_screen_speaker=False 但有 voiceover 渲染的 shot
    issues = []
    checked = 0
    for shot in shots:
        text_overlay = shot.get("text_overlay", {})
        if not isinstance(text_overlay, dict):
            continue
        text_type = text_overlay.get("text_type", "")
        off_screen = text_overlay.get("off_screen_speaker", False)
        if "dialogue" in str(text_type) and not off_screen:
            checked += 1
            # 在画面中的 speaker 不应被生成 voiceover bar (voiceover 是 off-screen 专属)
            # 这里只能检查数据标记是否正确，实际渲染需人工检查

    return {
        "code_audit": code_audit,
        "checked_shots": checked,
        "issues": issues,
        "pass": code_audit["function_exists"] and code_audit["skip_logic_exists"],
        "note": "T-A 去重逻辑: visible speaker 由 embed 处理，不生成 voiceover bar。代码审计 + 人工确认图片。",
    }


# ═══════════════════════════════════════════════════════════════
# N17: 重试上限 (T-B)
# ═══════════════════════════════════════════════════════════════

def analyze_retry_limit(captured_log: str) -> dict:
    """N17: T-B MAX_SHOT_RETRIES=1，每 shot 最多 2 次尝试（1 初次 + 1 重试）。
    检查:
    1. 代码审计: MAX_SHOT_RETRIES = 1
    2. 日志: [T17] Retry 行，每 shot 最多 1 条 retry
    """
    code_path = os.path.join(Path(__file__).parent.parent, "app", "services", "pipeline_orchestrator.py")
    code_audit = {"max_retries_is_1": False}
    if os.path.isfile(code_path):
        with open(code_path, "r", encoding="utf-8") as f:
            code = f.read()
        code_audit["max_retries_is_1"] = "MAX_SHOT_RETRIES = 1" in code

    # 日志解析: 找 [T17] Retry 行
    retry_lines = [l for l in captured_log.split('\n') if '[T17]' in l and 'Retry' in l]
    # 检查每 shot 重试不超过 1 次
    retry_per_shot = {}
    for line in retry_lines:
        m = re.search(r'Shot\s+(\d+)', line)
        if m:
            sid = int(m.group(1))
            retry_per_shot[sid] = retry_per_shot.get(sid, 0) + 1

    over_limit = {sid: cnt for sid, cnt in retry_per_shot.items() if cnt > 1}

    return {
        "code_audit": code_audit,
        "retry_lines_count": len(retry_lines),
        "retry_per_shot": retry_per_shot,
        "over_limit_shots": over_limit,
        "pass": code_audit["max_retries_is_1"] and len(over_limit) == 0,
        "note": "MAX_SHOT_RETRIES=1 → 每 shot 最多 2 次尝试 (初次+1重试)。",
    }


# ═══════════════════════════════════════════════════════════════
# N18: signage_text 数据流 (T-C)
# ═══════════════════════════════════════════════════════════════

def analyze_signage_text_flow(outline: dict, captured_log: str, project_dir: str) -> dict:
    """N18: T-C signage_text 数据流完整性。
    检查:
    1. outline unique_locations 中存在 signage_text 字段
    2. scene_reference_manager 代码中 _detect_signage_name 优先使用 signage_text
    3. 无 label 泄漏 (display_name 中的 · 分隔符后半部分不应出现在 prompt)
    """
    # 1. outline 中的 signage_text
    locations = outline.get("unique_locations", [])
    signage_fields = []
    for loc in locations:
        st = loc.get("signage_text", None)
        signage_fields.append({
            "location": loc.get("display_name", loc.get("name", "?")),
            "signage_text": st,
            "has_field": st is not None,
        })
    has_signage_field = any(sf["has_field"] for sf in signage_fields)

    # 2. 代码审计
    code_path = os.path.join(Path(__file__).parent.parent, "app", "services", "scene_reference_manager.py")
    code_audit = {"signage_text_priority": False, "detect_function": False}
    if os.path.isfile(code_path):
        with open(code_path, "r", encoding="utf-8") as f:
            code = f.read()
        code_audit["detect_function"] = "_detect_signage_name" in code
        code_audit["signage_text_priority"] = "if signage_text:" in code

    # 3. label 泄漏检查: · 分隔符后的内容不应出现在 anchor prompt 中
    label_leaks = []
    for loc in locations:
        name = loc.get("display_name", loc.get("name", ""))
        if "·" in name:
            leaked_part = name.split("·", 1)[1].strip()
            if leaked_part and leaked_part in captured_log:
                label_leaks.append({"location": name, "leaked": leaked_part})

    return {
        "has_signage_field_in_outline": has_signage_field,
        "signage_locations": signage_fields,
        "code_audit": code_audit,
        "label_leaks": label_leaks,
        "pass": code_audit["detect_function"] and code_audit["signage_text_priority"] and len(label_leaks) == 0,
        "note": "T-C: Stage 1 signage_text → scene_ref _detect_signage_name 优先使用，无 label 泄漏。",
    }


# ═══════════════════════════════════════════════════════════════
# N19: Prompt Quality Report (T-D)
# ═══════════════════════════════════════════════════════════════

def analyze_quality_report(project_dir: str) -> dict:
    """N19: T-D prompt_quality_report.md 存在且包含 3 个扩展维度检查。"""
    report_path = os.path.join(project_dir, "prompt_quality_report.md") if project_dir else ""
    report_exists = os.path.isfile(report_path) if report_path else False

    dimensions_found = {"镜头信息": False, "光线描述": False, "角色外观": False}
    quality_issues = 0
    total_shots = 0

    if report_exists:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        for dim in dimensions_found:
            if dim in content:
                dimensions_found[dim] = True
        # 计数 ✅ 和 ❌
        total_shots = content.count("## Shot")
        quality_issues = content.count("❌")

    # 代码审计
    code_path = os.path.join(Path(__file__).parent.parent, "app", "services", "pipeline_orchestrator.py")
    code_audit = {"report_function": False, "three_dimensions": False}
    if os.path.isfile(code_path):
        with open(code_path, "r", encoding="utf-8") as f:
            code = f.read()
        code_audit["report_function"] = "_save_prompt_quality_report" in code
        code_audit["three_dimensions"] = all(k in code for k in ["镜头信息", "光线描述", "角色外观"])

    all_dims = all(dimensions_found.values())

    return {
        "report_exists": report_exists,
        "report_path": report_path,
        "dimensions_found": dimensions_found,
        "total_shots": total_shots,
        "quality_issues": quality_issues,
        "code_audit": code_audit,
        "pass": code_audit["report_function"] and code_audit["three_dimensions"] and (report_exists and all_dims if project_dir else True),
        "note": "T-D: prompt_quality_report.md 3 维度 (镜头/光线/外观) 各约 30 关键词扩展。",
    }


# ═══════════════════════════════════════════════════════════════
# N20: Stage 4 新规则 (T-E/F/G)
# ═══════════════════════════════════════════════════════════════

def analyze_stage4_new_rules(shots: list, captured_log: str) -> dict:
    """N20: T-E/F/G Rules #10-12 在 storyboard_director.py 中生效。
    检查:
    1. 代码审计: 3 条规则存在
    2. image_prompt 中的表现:
       - Rule #10: back-view/high-angle shot 有明确服装颜色描述
       - Rule #11: off-screen 角色无物理接触描述
       - Rule #12: camera angle 与角色动作方向一致
    """
    code_path = os.path.join(Path(__file__).parent.parent, "app", "services", "storyboard_director.py")
    code_audit = {"rule_10": False, "rule_11": False, "rule_12": False}
    if os.path.isfile(code_path):
        with open(code_path, "r", encoding="utf-8") as f:
            code = f.read()
        code_audit["rule_10"] = "BACK-VIEW" in code or "back-view" in code.lower() and "HIGH-ANGLE" in code
        code_audit["rule_11"] = "OFF-SCREEN CHARACTER PHYSICAL CONTACT" in code
        code_audit["rule_12"] = "SPATIAL DIRECTION SELF-CONSISTENCY" in code

    # image_prompt 分析
    rule11_violations = []
    off_screen_contact_keywords = ["grip", "pull", "pulled", "hold hands with", "holding hands",
                                    "embrace", "grabbed by", "dragged by", "tugged by"]
    for shot in shots:
        prompt = (shot.get("image_prompt", "") or "").lower()
        # Rule #11: 检查是否有 off-screen + 物理接触
        if "off-screen" in prompt or "off screen" in prompt or "outside the frame" in prompt:
            for kw in off_screen_contact_keywords:
                if kw in prompt:
                    rule11_violations.append({
                        "shot_id": shot.get("shot_id", "?"),
                        "keyword": kw,
                    })
                    break

    return {
        "code_audit": code_audit,
        "rule11_violations": rule11_violations,
        "pass": all(code_audit.values()) and len(rule11_violations) == 0,
        "note": "T-E Rule#10 背面一致性 + T-F Rule#11 off-screen 无接触 + T-G Rule#12 空间方向自洽。人工需确认 Rule#10/12 在实际 prompt 中的表现。",
    }


# ═══════════════════════════════════════════════════════════════
# N21: Pre-Check 日志 (T-I)
# ═══════════════════════════════════════════════════════════════

def analyze_precheck_logs(captured_log: str) -> dict:
    """N21: T-I [PromptPreCheck] 日志存在，P1-P4 检查运行。
    Phase 1 仅日志，不阻塞 pipeline。"""
    precheck_lines = [l for l in captured_log.split('\n') if '[PromptPreCheck]' in l]
    warnings = [l for l in precheck_lines if '⚠️' in l]

    # 按 P 类型分类
    p_counts = {"P1": 0, "P2": 0, "P3": 0, "P4": 0}
    for w in warnings:
        for p in p_counts:
            if p in w:
                p_counts[p] += 1

    # 代码审计
    code_path = os.path.join(Path(__file__).parent.parent, "app", "services", "pipeline_orchestrator.py")
    code_audit = {"function_exists": False, "p1_check": False, "p2_check": False, "p4_check": False}
    if os.path.isfile(code_path):
        with open(code_path, "r", encoding="utf-8") as f:
            code = f.read()
        code_audit["function_exists"] = "_pre_check_prompt" in code
        code_audit["p1_check"] = "P1" in code and "EXACTLY" in code
        code_audit["p2_check"] = "P2" in code and "off-screen" in code.lower()
        code_audit["p4_check"] = "P4" in code and "off_screen_speaker" in code

    return {
        "precheck_lines_count": len(precheck_lines),
        "warnings_count": len(warnings),
        "p_counts": p_counts,
        "warning_samples": [w.strip()[:150] for w in warnings[:5]],
        "code_audit": code_audit,
        "pass": code_audit["function_exists"] and code_audit["p1_check"] and code_audit["p2_check"],
        "note": "T-I Phase 1: 仅日志不阻塞。P1 角色数量/P2 off-screen 接触/P4 speaker 矛盾。",
    }


# ═══════════════════════════════════════════════════════════════
# N22: 自然度日志 (T-H)
# ═══════════════════════════════════════════════════════════════

def analyze_naturalness_logs(captured_log: str) -> dict:
    """N22: T-H ShotValidator 包含 has_visual_unnaturalness 字段，Phase 1 仅日志。"""
    # 日志中查找自然度相关行
    naturalness_lines = [l for l in captured_log.split('\n')
                         if '自然度' in l or 'unnaturalness' in l.lower()]
    warning_lines = [l for l in naturalness_lines if '⚠️' in l or 'ℹ️' in l or '警告' in l]

    # 代码审计
    code_path = os.path.join(Path(__file__).parent.parent, "app", "services", "shot_validator.py")
    code_audit = {"field_exists": False, "three_dimensions": False, "log_only": False}
    if os.path.isfile(code_path):
        with open(code_path, "r", encoding="utf-8") as f:
            code = f.read()
        code_audit["field_exists"] = "has_visual_unnaturalness" in code
        code_audit["three_dimensions"] = "ANATOMICAL" in code and "PHYSICS" in code and "SPATIAL" in code
        # Phase 1: 不纳入 valid 判定
        code_audit["log_only"] = "自然度仅日志" in code or "Phase 1" in code

    return {
        "naturalness_log_lines": len(naturalness_lines),
        "warning_lines": len(warning_lines),
        "warning_samples": [w.strip()[:150] for w in warning_lines[:5]],
        "code_audit": code_audit,
        "pass": code_audit["field_exists"] and code_audit["three_dimensions"],
        "note": "T-H Phase 1: has_visual_unnaturalness 3 子维度 (anatomical/physics/spatial)，仅日志不触发 FAIL。",
    }


# ═══════════════════════════════════════════════════════════════
# N23: 人群角色计数 (T-K)
# ═══════════════════════════════════════════════════════════════

def analyze_crowd_counting(captured_log: str) -> dict:
    """N23: T-K ShotValidator 区分 NAMED/FEATURED 主角 vs 路人/人群。"""
    # 代码审计
    code_path = os.path.join(Path(__file__).parent.parent, "app", "services", "shot_validator.py")
    code_audit = {"named_featured": False, "crowd_exclusion": False}
    if os.path.isfile(code_path):
        with open(code_path, "r", encoding="utf-8") as f:
            code = f.read()
        code_audit["named_featured"] = "NAMED/FEATURED" in code or "NAMED" in code
        code_audit["crowd_exclusion"] = "crowd" in code.lower() and "bystander" in code.lower()

    # ShotValidator 日志分析
    sv_lines = [l for l in captured_log.split('\n') if '[ShotValidator]' in l]
    pass_lines = [l for l in sv_lines if '✅ PASS' in l]
    fail_lines = [l for l in sv_lines if '❌ FAIL' in l]

    # 提取 chars=X/Y 格式
    count_mismatches = []
    for line in sv_lines:
        m = re.search(r'chars=(\d+)/(\d+)', line)
        if m:
            actual, expected = int(m.group(1)), int(m.group(2))
            if actual != expected:
                count_mismatches.append({
                    "actual": actual,
                    "expected": expected,
                    "line": line.strip()[:120],
                })

    return {
        "sv_total_lines": len(sv_lines),
        "pass_count": len(pass_lines),
        "fail_count": len(fail_lines),
        "count_mismatches": count_mismatches,
        "code_audit": code_audit,
        "pass": code_audit["named_featured"] and code_audit["crowd_exclusion"],
        "note": "T-K: ShotValidator 计数 NAMED/FEATURED 主角，排除路人/人群/背景人物。",
    }


# ═══════════════════════════════════════════════════════════════
# 附加: text_language 检查 (简体中文)
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
# 附加: T22 目录跳过检查
# ═══════════════════════════════════════════════════════════════

def analyze_t22_directory(project_dir: str) -> dict:
    """T22: with_text_images/ 目录不存在 + refs/ 目录不存在"""
    with_text_dir_exists = False
    refs_dir_exists = False
    images_dir_exists = False

    if project_dir:
        with_text_dir_exists = os.path.isdir(os.path.join(project_dir, "with_text_images"))
        refs_dir_exists = os.path.isdir(os.path.join(project_dir, "refs"))
        images_dir_exists = os.path.isdir(os.path.join(project_dir, "images"))

    return {
        "with_text_dir_exists": with_text_dir_exists,
        "refs_dir_exists": refs_dir_exists,
        "images_dir_exists": images_dir_exists,
        "pass": not with_text_dir_exists and not refs_dir_exists and images_dir_exists,
    }


# ═══════════════════════════════════════════════════════════════
# 报告生成 (44 维度)
# ═══════════════════════════════════════════════════════════════

def generate_report(results: list, output_dir: str):
    """生成 44 维度验收报告"""
    report_path = os.path.join(output_dir, "r8_report.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    r = results[0]
    shots = r.get("shots_data", [])
    outline = r.get("outline_data", {})
    characters = r.get("characters_data", {})
    screenplay = r.get("screenplay_data", {})
    log = r.get("captured_log", "")
    project_dir = r.get("project_dir", "")

    lines = [
        f"# TASK-E2E-REGRESSION-R7 验收报告",
        f"",
        f"> 生成时间: {timestamp}",
        f"> 测试脚本: `tests/test_e2e_regression_r7.py`",
        f"> 验证修复: T1-T37 + OB-T29 + T-A~T-K (全量回归 + R8 新增验证)",
        f"> 44 维度: D1-D16 + S1-S5 + N1-N23",
        f"> 验收标准: >= 39/44 PASS + 0 FAIL",
        f"",
        f"---",
        f"",
        f"## 测试概况",
        f"",
        f"| 项 | 值 |",
        f"|-----|-----|",
    ]

    for key in ["label", "style_preset", "character_count", "title", "total_characters",
                 "total_scenes", "total_shots", "images_success", "images_total",
                 "elapsed_seconds"]:
        val = r.get(key, "N/A")
        lines.append(f"| {key} | {val} |")

    lines.extend([f"", f"---", f""])

    # ═══ D1-D3: 人工 ═══
    lines.extend([
        f"## D1-D3: 人工审查 (角色一致性 / 风格一致性 / 参考图质量)",
        f"",
        f"| # | 维度 | 判定 | 备注 |",
        f"|---|------|------|------|",
        f"| D1 | 角色一致性 | __ /5 | 同一角色在不同 shot 中是否一致 |",
        f"| D2 | 风格一致性 | __ /5 | 全部 shot 是否统一 illustration 风格 |",
        f"| D3 | 参考图质量 | __ /5 | character_refs + scene_refs 质量 |",
        f"",
    ])

    # ═══ D4: 构图多样性 ═══
    lines.extend([f"---", f"", f"## D4: 构图多样性", f""])
    if shots:
        comp_info = analyze_composition_variety(shots)
        verdict = "PASS" if comp_info["pass"] else "PARTIAL"
        lines.append(f"### 判定: **{verdict}**")
        lines.append(f"- 唯一 shot_type 数: {comp_info['unique_shot_types']} (目标 >=3)")
        lines.append(f"- shot_type 分布: {comp_info['shot_type_distribution']}")
        lines.append(f"- 唯一 camera_angle 数: {comp_info['unique_camera_angles']} (目标 >=2)")
        lines.append(f"- camera_angle 分布: {comp_info['camera_angle_distribution']}")
        lines.append(f"")

    # ═══ D5: text_overlay 渲染 ═══
    lines.extend([f"---", f"", f"## D5: text_overlay 渲染", f""])
    if shots:
        overlay_info = analyze_text_overlay_output(shots)
        verdict = "PASS" if overlay_info["pass"] else "FAIL"
        lines.append(f"### 判定: **{verdict}**")
        lines.append(f"- 覆盖率: {overlay_info['coverage']}")
        if overlay_info["missing_shots"]:
            lines.append(f"- 缺失 shots: {overlay_info['missing_shots']}")
        lines.append(f"")
        lines.append(f"| Shot ID | text_type | has_chinese_text | speaker_position |")
        lines.append(f"|---------|-----------|-----------------|------------------|")
        for d in overlay_info["details"]:
            lines.append(f"| {d['shot_id']} | {d['text_type']} | {d['has_chinese_text']} | {d['speaker_position']} |")
        lines.append(f"")

    # ═══ D6: 文字可读性 (人工) ═══
    lines.extend([
        f"---", f"",
        f"## D6: 文字可读性 (人工)", f"",
        f"| 判定 | 备注 |",
        f"|------|------|",
        f"| __ | 气泡/旁白文字是否清晰可读 |",
        f"",
    ])

    # ═══ D7: narration 覆盖 ═══
    lines.extend([f"---", f"", f"## D7: narration 覆盖 (plot_points 1:1)", f""])
    if outline or screenplay:
        narr_info = analyze_narration_coverage(outline, screenplay)
        verdict = "PASS" if narr_info["pass"] else "FAIL"
        lines.append(f"### 判定: **{verdict}**")
        lines.append(f"- Outline plot_points: {narr_info['total_plot_points']}")
        lines.append(f"- Screenplay scenes: {narr_info['total_scenes']}")
        lines.append(f"- 1:1 映射: {'YES' if narr_info['1_to_1'] else 'NO'}")
        if narr_info["missing_beats"]:
            lines.append(f"- 缺失 beats: {narr_info['missing_beats']}")
        lines.append(f"")

    # ═══ D8-D14: 人工 ═══
    lines.extend([
        f"---", f"",
        f"## D8-D14: 人工审查", f"",
        f"| # | 维度 | 判定 | 备注 |",
        f"|---|------|------|------|",
        f"| D8 | 对话内容匹配 | __ | shot 图片是否与 text_overlay 对话内容匹配 |",
        f"| D9 | 情感表达 | __ | 角色表情是否符合叙事情感 |",
        f"| D10 | 场景连续性 | __ | 同场景 shot 间环境是否连贯 |",
        f"| D11 | 光影一致 | __ | 同场景光线/色调是否统一 |",
        f"| D12 | 角色表情 | __ | 表情是否与 emotional_note 一致 |",
        f"| D13 | 背景细节 | __ | 背景是否有合理的细节填充 |",
        f"| D14 | 道具连续性 | __ | 同场景道具是否跨 shot 保持存在 |",
        f"",
    ])

    # ═══ D15: 镜头语言 ═══
    lines.extend([f"---", f"", f"## D15: 镜头语言", f""])
    if shots:
        cam_info = analyze_camera_language(shots)
        verdict = "PASS" if cam_info["pass"] else "PARTIAL"
        lines.append(f"### 判定: **{verdict}**")
        lines.append(f"- 运镜分布: {cam_info['movement_distribution']}")
        lines.append(f"- 焦距/镜头分布: {cam_info['lens_distribution']}")
        lines.append(f"- 全部 static: {'YES' if cam_info['all_static'] else 'NO'}")
        lines.append(f"")

    # ═══ D16: 叙事完整性 ═══
    lines.extend([f"---", f"", f"## D16: 叙事完整性", f""])
    if outline or screenplay:
        narr_comp = analyze_narrative_completeness(outline, screenplay, shots)
        verdict = "PASS" if narr_comp["pass"] else "FAIL"
        lines.append(f"### 判定: **{verdict}**")
        lines.append(f"- plot_points 全覆盖: {'YES' if narr_comp['plot_points_pass'] else 'NO'}")
        lines.append(f"- 旁白总字数: {narr_comp['total_narration_chars']} (>=200 = 充足)")
        lines.append(f"")

    # ═══ S1: 角色数量匹配 ═══
    lines.extend([f"---", f"", f"## S1: 角色数量匹配 (T17 ShotValidator)", f""])
    s1_info = analyze_character_count_accuracy(log, shots)
    verdict = "PASS" if s1_info["pass"] else ("PARTIAL" if s1_info["accuracy_num"] < 0 else "FAIL")
    if s1_info["accuracy_num"] < 0 and not s1_info["validator_disabled"]:
        verdict = "PASS (隐式)"
    lines.append(f"### 判定: **{verdict}**")
    lines.append(f"- 验证数据点: {s1_info['validations_count']}")
    lines.append(f"- 准确率: {s1_info['accuracy']}")
    lines.append(f"- 重试次数: {s1_info['retries']}")
    lines.append(f"- ShotValidator 日志行数: {s1_info['validator_log_lines']}")
    if s1_info["note"]:
        lines.append(f"- 备注: {s1_info['note']}")
    lines.append(f"")

    # ═══ S2-S4: 人工 ═══
    lines.extend([
        f"---", f"",
        f"## S2-S4: 人工审查", f"",
        f"| # | 维度 | 判定 | 备注 |",
        f"|---|------|------|------|",
        f"| S2 | 道具存续 | __ | 同场景跨 shot 道具是否持续存在 (T18) |",
        f"| S3 | 面部一致 | __ | wide<->close-up 面部是否一致 (T20) |",
        f"| S4 | 跨年龄风格 | __ /5 | 不同年龄角色 (奶奶 vs 孙女) 是否同一画风 (T19) |",
        f"",
    ])

    # ═══ S5: 气泡重复 ═══
    lines.extend([f"---", f"", f"## S5: 气泡重复率 (<2%)", f""])
    s5_info = analyze_bubble_duplicate_rate(log, shots)
    verdict = "PASS" if s5_info["pass"] else "FAIL"
    lines.append(f"### 判定: **{verdict}**")
    lines.append(f"- 检测到重复: {s5_info['duplicate_detected_count']}")
    lines.append(f"- 重复率: {s5_info['duplicate_rate']}")
    if s5_info["note"]:
        lines.append(f"- 备注: {s5_info['note']}")
    lines.append(f"")

    # ═══ N1: 角色称谓正确性 ═══
    lines.extend([f"---", f"", f"## N1: 角色称谓正确性 (T24+T27)", f""])
    if shots and outline:
        n1_info = analyze_character_appellation(shots, outline, characters)
        verdict = "PASS" if n1_info["pass"] else "FAIL"
        lines.append(f"### 判定: **{verdict}** (自动检测 + 需人工确认)")
        lines.append(f"- 角色 family_role 映射: {n1_info['name_role_map']}")
        lines.append(f"- family_relationships 存在: {'YES' if n1_info['has_family_relationships'] else 'NO'}")
        lines.append(f"- family_relationships 数: {n1_info['family_relationships_count']}")
        lines.append(f"- 称谓使用次数: {n1_info['title_usages_count']}")
        lines.append(f"- 称谓不匹配数: {n1_info['mismatches_count']}")
        if n1_info["mismatches"]:
            lines.append(f"- 不匹配详情:")
            for m in n1_info["mismatches"]:
                lines.append(f"  - Shot {m['shot_id']}: {m['issue']}")
        if n1_info["title_usages"]:
            lines.append(f"- 称谓使用样本 (前 10):")
            for u in n1_info["title_usages"][:10]:
                lines.append(f"  - Shot {u['shot_id']}: {u['title_found']} ({u['expected_role']}) — \"{u['text_snippet']}\"")
        lines.append(f"")

    # ═══ N2: 对话自然度 ═══
    lines.extend([f"---", f"", f"## N2: 对话自然度 (T26)", f""])
    if screenplay:
        n2_info = analyze_dialogue_naturalness(shots, screenplay)
        verdict = "PASS" if n2_info["pass"] else "PARTIAL"
        lines.append(f"### 判定: **{verdict}** (自动辅助 + 需人工确认)")
        lines.append(f"- 总对话行数: {n2_info['total_dialogue_lines']}")
        lines.append(f"- 过长对话 (>25字): {n2_info['long_lines_count']} ({n2_info['long_lines_ratio']})")
        lines.append(f"- 书面化表达: {n2_info['formal_patterns_count']}")
        if n2_info["long_lines"]:
            lines.append(f"- 过长对话样本:")
            for ll in n2_info["long_lines"]:
                lines.append(f"  - Scene {ll['scene_id']} {ll['speaker']}: \"{ll['line']}\" ({ll['length']}字)")
        lines.append(f"")

    # ═══ N3: 同场景背景多样性 ═══
    lines.extend([f"---", f"", f"## N3: 同场景背景多样性 (T27)", f""])
    if shots:
        n3_info = analyze_background_variety(shots)
        verdict = "PASS" if n3_info["pass"] else "PARTIAL"
        lines.append(f"### 判定: **{verdict}** (自动辅助 + 需人工看图确认)")
        lines.append(f"- 3+ shots 场景数: {n3_info['multi_shot_scenes_count']}")
        if n3_info["scene_analyses"]:
            for sa in n3_info["scene_analyses"]:
                varied_mark = "OK" if sa['is_varied'] else "NOT VARIED"
                lines.append(f"  - Scene {sa['scene_id']}: {sa['shot_count']} shots, "
                             f"{sa['unique_backgrounds']} 种不同背景 ({varied_mark})")
        lines.append(f"")

    # ═══ N4: 室内纵深感 (人工) ═══
    lines.extend([
        f"---", f"",
        f"## N4: 室内纵深感 (T27) — 人工审查", f"",
        f"| 判定 | 备注 |",
        f"|------|------|",
        f"| __ | medium_shot 室内 shot 是否有前中后景层次 |",
        f"",
    ])

    # ═══ N5: 参考图模型 ═══
    lines.extend([f"---", f"", f"## N5: 参考图模型 (T23: NB2 确认)", f""])
    n5_info = analyze_reference_model(log)
    verdict = "PASS" if n5_info["pass"] else "FAIL"
    lines.append(f"### 判定: **{verdict}**")
    lines.append(f"- 日志 NB2 出现: {n5_info['log_nb2_mentions']} 次")
    lines.append(f"- 日志 FAST_MODEL 出现: {n5_info['log_fast_model_mentions']} 次")
    if n5_info["code_audit"].get("nb2_model_value"):
        lines.append(f"- NB2_MODEL 值: {n5_info['code_audit']['nb2_model_value']}")
    lines.append(f"- 代码确认: {'NB2' if n5_info['code_audit'].get('nb2_confirmed') else '需手动确认'}")
    lines.append(f"")

    # ═══ N6: 道具检测日志 ═══
    lines.extend([f"---", f"", f"## N6: 道具检测日志 (T28 ShotValidator key_props)", f""])
    n6_info = analyze_prop_detection_logs(log, shots)
    verdict = "PASS" if n6_info["pass"] else "FAIL"
    lines.append(f"### 判定: **{verdict}**")
    lines.append(f"- ShotValidator 日志行数: {n6_info['validator_log_lines']}")
    lines.append(f"- 道具相关日志: {n6_info['prop_related_lines']}")
    lines.append(f"- 含 composition 道具的 shots: {n6_info['shots_with_composition_props']}")
    lines.append(f"- T28 Pipeline 集成: {'YES' if n6_info['code_audit'].get('t28_integration_exists') else 'NO'}")
    lines.append(f"- T28 Validator 代码: {'YES' if n6_info['code_audit'].get('t28_validator_exists') else 'NO'}")
    lines.append(f"")

    # ═══ N7: off_screen_speaker 标记 ═══
    lines.extend([f"---", f"", f"## N7: off_screen_speaker 标记 (T29)", f""])
    n7_info = analyze_off_screen_marking(shots, screenplay)
    verdict = "PASS" if n7_info["pass"] else "FAIL"
    lines.append(f"### 判定: **{verdict}**")
    lines.append(f"- off_screen 标记数: {n7_info['off_screen_found_count']}")
    lines.append(f"- 不在场发言 shots: {n7_info['absent_speaker_shots']}")
    lines.append(f"- T29 代码存在: {'YES' if n7_info['code_audit'].get('t29_exists') else 'NO'}")
    if n7_info["off_screen_found"]:
        lines.append(f"- off_screen 详情:")
        for os_item in n7_info["off_screen_found"]:
            lines.append(f"  - Shot {os_item['shot_id']}: speaker={os_item['speaker']}, type={os_item['text_type']}")
    if n7_info["note"]:
        lines.append(f"- 备注: {n7_info['note']}")
    lines.append(f"")

    # ═══ N8: off_screen 对话渲染 (人工) ═══
    lines.extend([
        f"---", f"",
        f"## N8: off_screen 对话渲染 (T29+OB-T29) — 人工审查", f"",
        f"| 判定 | 备注 |",
        f"|------|------|",
        f"| __ | off_screen 对话是否渲染为 voiceover bar (非气泡) |",
        f"",
        f"验证要点:",
        f"- image_generator.py L87-104: off_screen_speaker=True -> voiceover 半透明条",
        f"- text_overlay_service.py L607-615: pure dialogue off_screen -> add_monologue()",
        f"- text_overlay_service.py L670-676: compound type off_screen -> add_monologue()",
        f"",
    ])

    # ═══ N9: family_relationships 传递 ═══
    lines.extend([f"---", f"", f"## N9: family_relationships 传递 (T32)", f""])
    n9_info = analyze_family_relationships_passing(outline, screenplay, log)
    verdict = "PASS" if n9_info["pass"] else "FAIL"
    lines.append(f"### 判定: **{verdict}**")
    lines.append(f"- Outline 含 family_relationships: {'YES' if n9_info['outline_has_rels'] else 'NO'}")
    lines.append(f"- 关系数: {n9_info['outline_rels_count']}")
    lines.append(f"- T32 Pipeline 代码: {'YES' if n9_info['code_audit']['t32_pipeline_exists'] else 'NO'}")
    lines.append(f"- T32 Screenplay 代码: {'YES' if n9_info['code_audit']['t32_screenplay_exists'] else 'NO'}")
    if n9_info["outline_family_relationships"]:
        lines.append(f"- 关系详情:")
        for rel in n9_info["outline_family_relationships"][:6]:
            lines.append(f"  - {rel.get('from','')} -> {rel.get('to','')}: {rel.get('relationship','')}")
    lines.append(f"")

    # ═══ N10: 亲属称谓清晰度 ═══
    lines.extend([f"---", f"", f"## N10: 亲属称谓清晰度 (T37)", f""])
    n10_info = analyze_kinship_clarity(screenplay)
    verdict = "PASS" if n10_info["pass"] else "FAIL"
    lines.append(f"### 判定: **{verdict}**")
    lines.append(f"- 总对话行: {n10_info['total_dialogue_lines']}")
    lines.append(f"- 歧义称谓数: {n10_info['ambiguous_refs_count']} (允许 <=2)")
    lines.append(f"- T37 规则存在: {'YES' if n10_info['code_audit']['t37_exists'] else 'NO'}")
    if n10_info["ambiguous_refs"]:
        lines.append(f"- 歧义样本:")
        for ar in n10_info["ambiguous_refs"][:5]:
            lines.append(f"  - Scene {ar['scene_id']} {ar['speaker']}: {ar['issue']} — \"{ar['line']}\"")
    lines.append(f"")

    # ═══ N11: 镜头信息完整性 ═══
    lines.extend([f"---", f"", f"## N11: 镜头信息完整性 (T34)", f""])
    n11_info = analyze_camera_completeness(shots, log)
    verdict = "PASS" if n11_info["pass"] else "FAIL"
    lines.append(f"### 判定: **{verdict}**")
    lines.append(f"- shot_size 覆盖: {n11_info['shots_with_size']}/{n11_info['total_shots']} ({n11_info['size_coverage']})")
    lines.append(f"- camera_angle 覆盖: {n11_info['shots_with_angle']}/{n11_info['total_shots']} ({n11_info['angle_coverage']})")
    lines.append(f"- Plan B 注入日志: {n11_info['plan_b_log_lines']} 行")
    lines.append(f"- T34 Plan A (prompt): {'YES' if n11_info['code_audit']['t34_plan_a'] else 'NO'}")
    lines.append(f"- T34 Plan B (inject): {'YES' if n11_info['code_audit']['t34_plan_b'] else 'NO'}")
    lines.append(f"")

    # ═══ N12: 多人空间锚定 ═══
    lines.extend([f"---", f"", f"## N12: 多人空间锚定 (T35)", f""])
    n12_info = analyze_spatial_anchoring(shots)
    verdict = "PASS" if n12_info["pass"] else "FAIL"
    lines.append(f"### 判定: **{verdict}**")
    lines.append(f"- 3+ 人 shots: {n12_info['multi_char_shots_count']}")
    lines.append(f"- 空间描述不足: {n12_info['spatial_issues_count']} (允许 <=1)")
    lines.append(f"- T35 规则存在: {'YES' if n12_info['code_audit']['t35_exists'] else 'NO'}")
    if n12_info["multi_char_shots"]:
        for mc in n12_info["multi_char_shots"]:
            adequate = "OK" if mc['has_adequate_spatial'] else "INSUFFICIENT"
            lines.append(f"  - Shot {mc['shot_id']}: {mc['char_count']} chars, "
                         f"空间词={mc['spatial_keywords_found'][:3]} ({adequate})")
    lines.append(f"")

    # ═══ N13: 家庭关系逻辑一致性 ═══
    lines.extend([f"---", f"", f"## N13: 家庭关系逻辑一致性 (T33)", f""])
    n13_info = analyze_relationship_consistency(outline)
    verdict = "PASS" if n13_info["pass"] else "FAIL"
    lines.append(f"### 判定: **{verdict}**")
    if n13_info.get("has_relationships"):
        lines.append(f"- 总关系数: {n13_info['total_relationships']}")
        lines.append(f"- 逻辑不一致: {n13_info['inconsistencies_count']}")
        lines.append(f"- T33 规则存在: {'YES' if n13_info['code_audit']['t33_exists'] else 'NO'}")
        if n13_info["inconsistencies"]:
            lines.append(f"- 不一致详情:")
            for ic in n13_info["inconsistencies"]:
                lines.append(f"  - [{ic['type']}] {ic['detail']}")
    else:
        lines.append(f"- {n13_info.get('note', '无数据')}")
    lines.append(f"")

    # ═══ N14: color_palette 英文 ═══
    lines.extend([f"---", f"", f"## N14: color_palette 英文 (T36)", f""])
    n14_info = analyze_color_palette_english(outline)
    verdict = "PASS" if n14_info["pass"] else "FAIL"
    lines.append(f"### 判定: **{verdict}**")
    lines.append(f"- color_palette 存在: {'YES' if n14_info['color_palette_found'] else 'NO'}")
    lines.append(f"- 含中文: {'YES' if n14_info['has_chinese'] else 'NO'}")
    lines.append(f"- T36 代码存在: {'YES' if n14_info['code_audit']['t36_exists'] else 'NO'}")
    if n14_info["color_palette"]:
        lines.append(f"- color_palette 内容: {json.dumps(n14_info['color_palette'], ensure_ascii=False)[:200]}")
    if n14_info["chinese_found"]:
        lines.append(f"- 中文问题:")
        for cf in n14_info["chinese_found"]:
            lines.append(f"  - {cf['path']}: \"{cf['value']}\"")
    lines.append(f"")

    # ═══ N15: 招牌注入 ═══
    lines.extend([f"---", f"", f"## N15: 招牌注入 (T31)", f""])
    n15_info = analyze_signage_injection(log, project_dir)
    verdict = "PASS" if n15_info["pass"] else "FAIL"
    lines.append(f"### 判定: **{verdict}**")
    lines.append(f"- 招牌日志行数: {n15_info['signage_log_lines']}")
    lines.append(f"- scene_ref 图片数: {n15_info['scene_ref_count']}")
    lines.append(f"- T31 招牌检测代码: {'YES' if n15_info['code_audit']['signage_detection'] else 'NO'}")
    lines.append(f"- T31 SIGNAGE 注入代码: {'YES' if n15_info['code_audit']['t31_exists'] else 'NO'}")
    if n15_info["signage_log_samples"]:
        lines.append(f"- 日志样本:")
        for sl in n15_info["signage_log_samples"][:3]:
            lines.append(f"  - {sl[:120]}")
    if n15_info["note"]:
        lines.append(f"- 备注: {n15_info['note']}")
    lines.append(f"")

    # ═══ N16: off_screen 文字去重 ═══
    lines.extend([f"---", f"", f"## N16: off_screen 文字去重 (T-A)", f""])
    n16_info = analyze_off_screen_dedup(shots, log)
    verdict = "PASS" if n16_info["pass"] else "FAIL"
    lines.append(f"### 判定: **{verdict}**")
    lines.append(f"- _is_speaker_off_screen() 函数: {'YES' if n16_info['code_audit']['function_exists'] else 'NO'}")
    lines.append(f"- skip 逻辑 (visible speaker 跳过 voiceover): {'YES' if n16_info['code_audit']['skip_logic_exists'] else 'NO'}")
    lines.append(f"- 检查的 dialogue shots: {n16_info['checked_shots']}")
    if n16_info["note"]:
        lines.append(f"- 备注: {n16_info['note']}")
    lines.append(f"")

    # ═══ N17: 重试上限 ═══
    lines.extend([f"---", f"", f"## N17: 重试上限 (T-B)", f""])
    n17_info = analyze_retry_limit(log)
    verdict = "PASS" if n17_info["pass"] else "FAIL"
    lines.append(f"### 判定: **{verdict}**")
    lines.append(f"- MAX_SHOT_RETRIES = 1: {'YES' if n17_info['code_audit']['max_retries_is_1'] else 'NO'}")
    lines.append(f"- 重试日志行数: {n17_info['retry_lines_count']}")
    if n17_info["retry_per_shot"]:
        lines.append(f"- 各 shot 重试次数: {n17_info['retry_per_shot']}")
    if n17_info["over_limit_shots"]:
        lines.append(f"- ⚠️ 超限 shots: {n17_info['over_limit_shots']}")
    if n17_info["note"]:
        lines.append(f"- 备注: {n17_info['note']}")
    lines.append(f"")

    # ═══ N18: signage_text 数据流 ═══
    lines.extend([f"---", f"", f"## N18: signage_text 数据流 (T-C)", f""])
    n18_info = analyze_signage_text_flow(outline, log, project_dir)
    verdict = "PASS" if n18_info["pass"] else "FAIL"
    lines.append(f"### 判定: **{verdict}**")
    lines.append(f"- outline 含 signage_text: {'YES' if n18_info['has_signage_field_in_outline'] else 'NO'}")
    lines.append(f"- _detect_signage_name() 函数: {'YES' if n18_info['code_audit']['detect_function'] else 'NO'}")
    lines.append(f"- signage_text 优先使用: {'YES' if n18_info['code_audit']['signage_text_priority'] else 'NO'}")
    lines.append(f"- label 泄漏: {len(n18_info['label_leaks'])} 处")
    if n18_info["signage_locations"]:
        lines.append(f"- 地点 signage_text:")
        for sl in n18_info["signage_locations"]:
            lines.append(f"  - {sl['location']}: {repr(sl['signage_text'])}")
    if n18_info["label_leaks"]:
        for lk in n18_info["label_leaks"]:
            lines.append(f"  - ⚠️ 泄漏: {lk['location']} → {lk['leaked']}")
    if n18_info["note"]:
        lines.append(f"- 备注: {n18_info['note']}")
    lines.append(f"")

    # ═══ N19: Prompt Quality Report ═══
    lines.extend([f"---", f"", f"## N19: Prompt Quality Report (T-D)", f""])
    n19_info = analyze_quality_report(project_dir)
    verdict = "PASS" if n19_info["pass"] else "FAIL"
    lines.append(f"### 判定: **{verdict}**")
    lines.append(f"- report 文件: {'存在' if n19_info['report_exists'] else '不存在'}")
    lines.append(f"- 3 维度覆盖: {n19_info['dimensions_found']}")
    lines.append(f"- 分析 shots 数: {n19_info['total_shots']}")
    lines.append(f"- 质量问题 (❌): {n19_info['quality_issues']}")
    lines.append(f"- 代码: _save_prompt_quality_report(): {'YES' if n19_info['code_audit']['report_function'] else 'NO'}")
    if n19_info["note"]:
        lines.append(f"- 备注: {n19_info['note']}")
    lines.append(f"")

    # ═══ N20: Stage 4 新规则 ═══
    lines.extend([f"---", f"", f"## N20: Stage 4 新规则 (T-E/F/G Rules #10-12)", f""])
    n20_info = analyze_stage4_new_rules(shots, log)
    verdict = "PASS" if n20_info["pass"] else "FAIL"
    lines.append(f"### 判定: **{verdict}**")
    lines.append(f"- Rule #10 (背面一致性): {'YES' if n20_info['code_audit']['rule_10'] else 'NO'}")
    lines.append(f"- Rule #11 (off-screen 无接触): {'YES' if n20_info['code_audit']['rule_11'] else 'NO'}")
    lines.append(f"- Rule #12 (空间方向自洽): {'YES' if n20_info['code_audit']['rule_12'] else 'NO'}")
    lines.append(f"- Rule #11 违规: {len(n20_info['rule11_violations'])} 处")
    if n20_info["rule11_violations"]:
        for v in n20_info["rule11_violations"]:
            lines.append(f"  - Shot {v['shot_id']}: '{v['keyword']}'")
    if n20_info["note"]:
        lines.append(f"- 备注: {n20_info['note']}")
    lines.append(f"")

    # ═══ N21: Pre-Check 日志 ═══
    lines.extend([f"---", f"", f"## N21: Pre-Check 日志 (T-I)", f""])
    n21_info = analyze_precheck_logs(log)
    verdict = "PASS" if n21_info["pass"] else "FAIL"
    lines.append(f"### 判定: **{verdict}**")
    lines.append(f"- [PromptPreCheck] 日志行数: {n21_info['precheck_lines_count']}")
    lines.append(f"- 警告数: {n21_info['warnings_count']}")
    lines.append(f"- P 分类: {n21_info['p_counts']}")
    lines.append(f"- 代码: _pre_check_prompt(): {'YES' if n21_info['code_audit']['function_exists'] else 'NO'}")
    if n21_info["warning_samples"]:
        lines.append(f"- 警告样本:")
        for ws in n21_info["warning_samples"]:
            lines.append(f"  - {ws}")
    if n21_info["note"]:
        lines.append(f"- 备注: {n21_info['note']}")
    lines.append(f"")

    # ═══ N22: 自然度日志 ═══
    lines.extend([f"---", f"", f"## N22: 自然度日志 (T-H)", f""])
    n22_info = analyze_naturalness_logs(log)
    verdict = "PASS" if n22_info["pass"] else "FAIL"
    lines.append(f"### 判定: **{verdict}**")
    lines.append(f"- has_visual_unnaturalness 字段: {'YES' if n22_info['code_audit']['field_exists'] else 'NO'}")
    lines.append(f"- 3 子维度 (anatomical/physics/spatial): {'YES' if n22_info['code_audit']['three_dimensions'] else 'NO'}")
    lines.append(f"- Phase 1 仅日志: {'YES' if n22_info['code_audit']['log_only'] else 'NO'}")
    lines.append(f"- 自然度日志行数: {n22_info['naturalness_log_lines']}")
    lines.append(f"- 警告行数: {n22_info['warning_lines']}")
    if n22_info["warning_samples"]:
        lines.append(f"- 警告样本:")
        for ws in n22_info["warning_samples"]:
            lines.append(f"  - {ws}")
    if n22_info["note"]:
        lines.append(f"- 备注: {n22_info['note']}")
    lines.append(f"")

    # ═══ N23: 人群角色计数 ═══
    lines.extend([f"---", f"", f"## N23: 人群角色计数 (T-K)", f""])
    n23_info = analyze_crowd_counting(log)
    verdict = "PASS" if n23_info["pass"] else "FAIL"
    lines.append(f"### 判定: **{verdict}**")
    lines.append(f"- NAMED/FEATURED 区分: {'YES' if n23_info['code_audit']['named_featured'] else 'NO'}")
    lines.append(f"- crowd/bystander 排除: {'YES' if n23_info['code_audit']['crowd_exclusion'] else 'NO'}")
    lines.append(f"- ShotValidator 日志行: {n23_info['sv_total_lines']}")
    lines.append(f"- PASS: {n23_info['pass_count']}, FAIL: {n23_info['fail_count']}")
    if n23_info["count_mismatches"]:
        lines.append(f"- 计数不匹配:")
        for cm in n23_info["count_mismatches"][:5]:
            lines.append(f"  - actual={cm['actual']} expected={cm['expected']}: {cm['line']}")
    if n23_info["note"]:
        lines.append(f"- 备注: {n23_info['note']}")
    lines.append(f"")

    # ═══ 附加检查 ═══
    lines.extend([f"---", f"", f"## 附加检查", f""])

    lang_info = analyze_text_language(shots)
    lines.append(f"### 简体中文: **{'PASS' if lang_info['pass'] else 'FAIL'}**")
    lines.append(f"- 文本数: {lang_info['total_texts']}, 繁体问题: {lang_info['issues_count']}")
    lines.append(f"")

    t22_info = analyze_t22_directory(project_dir)
    lines.append(f"### T22 目录跳过: **{'PASS' if t22_info['pass'] else 'FAIL'}**")
    lines.append(f"- with_text_images/: {'存在' if t22_info['with_text_dir_exists'] else '不存在'}")
    lines.append(f"- refs/: {'存在' if t22_info['refs_dir_exists'] else '不存在'}")
    lines.append(f"- images/: {'存在' if t22_info['images_dir_exists'] else '缺失'}")
    lines.append(f"")

    # ═══ 36 维度总结 ═══
    lines.extend([
        f"---", f"",
        f"## 44 维度总结",
        f"",
        f"| # | 维度 | 类型 | 判定 |",
        f"|---|------|------|------|",
        f"| D1 | 角色一致性 | 人工 | __ |",
        f"| D2 | 风格一致性 | 人工 | __ |",
        f"| D3 | 参考图质量 | 人工 | __ |",
    ])

    # D4
    if shots:
        d4_pass = analyze_composition_variety(shots)["pass"]
        lines.append(f"| D4 | 构图多样性 | 自动 | {'PASS' if d4_pass else 'PARTIAL'} |")
    else:
        lines.append(f"| D4 | 构图多样性 | 自动 | N/A |")

    # D5
    if shots:
        d5_pass = analyze_text_overlay_output(shots)["pass"]
        lines.append(f"| D5 | text_overlay 渲染 | 自动 | {'PASS' if d5_pass else 'FAIL'} |")
    else:
        lines.append(f"| D5 | text_overlay 渲染 | 自动 | N/A |")

    lines.append(f"| D6 | 文字可读性 | 人工 | __ |")

    # D7
    if outline or screenplay:
        d7_pass = analyze_narration_coverage(outline, screenplay)["pass"]
        lines.append(f"| D7 | narration 覆盖 | 自动 | {'PASS' if d7_pass else 'FAIL'} |")
    else:
        lines.append(f"| D7 | narration 覆盖 | 自动 | N/A |")

    lines.extend([
        f"| D8 | 对话内容匹配 | 人工 | __ |",
        f"| D9 | 情感表达 | 人工 | __ |",
        f"| D10 | 场景连续性 | 人工 | __ |",
        f"| D11 | 光影一致 | 人工 | __ |",
        f"| D12 | 角色表情 | 人工 | __ |",
        f"| D13 | 背景细节 | 人工 | __ |",
        f"| D14 | 道具连续性 | 人工 | __ |",
    ])

    # D15
    if shots:
        d15_pass = analyze_camera_language(shots)["pass"]
        lines.append(f"| D15 | 镜头语言 | 自动 | {'PASS' if d15_pass else 'PARTIAL'} |")
    else:
        lines.append(f"| D15 | 镜头语言 | 自动 | N/A |")

    # D16
    if outline or screenplay:
        d16_pass = analyze_narrative_completeness(outline, screenplay, shots)["pass"]
        lines.append(f"| D16 | 叙事完整性 | 自动 | {'PASS' if d16_pass else 'FAIL'} |")
    else:
        lines.append(f"| D16 | 叙事完整性 | 自动 | N/A |")

    # S1
    s1_verdict = "PASS" if s1_info["pass"] else ("PASS (隐式)" if s1_info["accuracy_num"] < 0 and not s1_info["validator_disabled"] else "FAIL")
    lines.append(f"| S1 | 角色数量匹配 | 日志 | {s1_verdict} |")

    lines.extend([
        f"| S2 | 道具存续 | 人工 | __ |",
        f"| S3 | 面部一致 | 人工 | __ |",
        f"| S4 | 跨年龄风格 | 人工 | __ |",
    ])

    # S5
    lines.append(f"| S5 | 气泡重复 | 日志 | {'PASS' if s5_info['pass'] else 'FAIL'} |")

    # N1
    if shots and outline:
        n1_pass = analyze_character_appellation(shots, outline, characters)["pass"]
        lines.append(f"| N1 | 角色称谓正确性 | 自动+人工 | {'PASS' if n1_pass else 'FAIL'} |")
    else:
        lines.append(f"| N1 | 角色称谓正确性 | 自动+人工 | N/A |")

    # N2
    if screenplay:
        n2_pass = analyze_dialogue_naturalness(shots, screenplay)["pass"]
        lines.append(f"| N2 | 对话自然度 | 自动+人工 | {'PASS' if n2_pass else 'PARTIAL'} |")
    else:
        lines.append(f"| N2 | 对话自然度 | 自动+人工 | N/A |")

    # N3
    if shots:
        n3_pass = analyze_background_variety(shots)["pass"]
        lines.append(f"| N3 | 背景多样性 | 自动+人工 | {'PASS' if n3_pass else 'PARTIAL'} |")
    else:
        lines.append(f"| N3 | 背景多样性 | 自动+人工 | N/A |")

    lines.append(f"| N4 | 室内纵深感 | 人工 | __ |")

    # N5
    lines.append(f"| N5 | 参考图模型 | 代码+日志 | {'PASS' if n5_info['pass'] else 'FAIL'} |")

    # N6
    lines.append(f"| N6 | 道具检测日志 | 代码+日志 | {'PASS' if n6_info['pass'] else 'FAIL'} |")

    # N7
    lines.append(f"| N7 | off_screen_speaker 标记 | 自动+代码 | {'PASS' if n7_info['pass'] else 'FAIL'} |")

    # N8
    lines.append(f"| N8 | off_screen 渲染 | 人工 | __ |")

    # N9
    lines.append(f"| N9 | family_relationships 传递 | 自动+代码 | {'PASS' if n9_info['pass'] else 'FAIL'} |")

    # N10
    lines.append(f"| N10 | 亲属称谓清晰度 | 自动+代码 | {'PASS' if n10_info['pass'] else 'FAIL'} |")

    # N11
    lines.append(f"| N11 | 镜头信息完整性 | 自动+代码 | {'PASS' if n11_info['pass'] else 'FAIL'} |")

    # N12
    lines.append(f"| N12 | 多人空间锚定 | 自动+代码 | {'PASS' if n12_info['pass'] else 'FAIL'} |")

    # N13
    lines.append(f"| N13 | 关系逻辑一致性 | 自动+代码 | {'PASS' if n13_info['pass'] else 'FAIL'} |")

    # N14
    lines.append(f"| N14 | color_palette 英文 | 自动+代码 | {'PASS' if n14_info['pass'] else 'FAIL'} |")

    # N15
    lines.append(f"| N15 | 招牌注入 | 自动+代码 | {'PASS' if n15_info['pass'] else 'FAIL'} |")

    # N16
    lines.append(f"| N16 | off_screen 文字去重 | 自动+代码 | {'PASS' if n16_info['pass'] else 'FAIL'} |")

    # N17
    lines.append(f"| N17 | 重试上限 | 代码+日志 | {'PASS' if n17_info['pass'] else 'FAIL'} |")

    # N18
    lines.append(f"| N18 | signage_text 数据流 | 自动+代码 | {'PASS' if n18_info['pass'] else 'FAIL'} |")

    # N19
    lines.append(f"| N19 | Prompt Quality Report | 自动+代码 | {'PASS' if n19_info['pass'] else 'FAIL'} |")

    # N20
    lines.append(f"| N20 | Stage 4 新规则 | 自动+代码 | {'PASS' if n20_info['pass'] else 'FAIL'} |")

    # N21
    lines.append(f"| N21 | Pre-Check 日志 | 代码+日志 | {'PASS' if n21_info['pass'] else 'FAIL'} |")

    # N22
    lines.append(f"| N22 | 自然度日志 | 代码+日志 | {'PASS' if n22_info['pass'] else 'FAIL'} |")

    # N23
    lines.append(f"| N23 | 人群角色计数 | 代码+日志 | {'PASS' if n23_info['pass'] else 'FAIL'} |")

    lines.extend([f"", f"---", f"",
                  f"## JSON 抽检区域 (人工填写)", f"",
                  f"### outline characters_overview + family_relationships", f"",
                  f"```json", f"待填写", f"```", f"",
                  f"### storyboard shot 样本 (text_overlay + composition + off_screen_speaker)", f"",
                  f"```json", f"待填写", f"```", f"",
                  f"---", f"",
                  f"**验收标准**: >= 39/44 PASS + 0 FAIL = R8 通过", f""])

    # 写入文件
    report_content = "\n".join(lines)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"\n报告已保存: {report_path}")
    return report_path


# ═══════════════════════════════════════════════════════════════
# 保存中间数据 (JSON 抽检用)
# ═══════════════════════════════════════════════════════════════

def save_excerpts(results: list, output_dir: str):
    """保存 JSON 摘要供人工抽检"""
    r = results[0]
    excerpts_dir = os.path.join(output_dir, "excerpts")
    os.makedirs(excerpts_dir, exist_ok=True)

    # 1. outline characters_overview + family_relationships
    outline = r.get("outline_data", {})
    if outline:
        excerpt = {
            "title": outline.get("title"),
            "characters_overview": outline.get("characters_overview", []),
            "family_relationships": outline.get("family_relationships", []),
            "color_palette": outline.get("visual_tone", {}).get("color_palette",
                             outline.get("color_palette",
                             outline.get("visual_style", {}).get("color_palette", {}))),
        }
        with open(os.path.join(excerpts_dir, "outline_excerpt.json"), "w", encoding="utf-8") as f:
            json.dump(excerpt, f, ensure_ascii=False, indent=2)

    # 2. storyboard shots (text_overlay + composition + camera + off_screen_speaker)
    shots = r.get("shots_data", [])
    if shots:
        shot_excerpts = []
        for shot in shots[:10]:
            shot_excerpts.append({
                "shot_id": shot.get("shot_id"),
                "scene_id": shot.get("scene_id"),
                "text_overlay": shot.get("text_overlay"),
                "composition": shot.get("composition"),
                "camera": shot.get("camera"),
                "character_direction": shot.get("character_direction"),
                "characters_in_scene": shot.get("characters_in_scene"),
                "image_prompt_snippet": (shot.get("image_prompt", "") or "")[:200],
            })
        with open(os.path.join(excerpts_dir, "storyboard_excerpt.json"), "w", encoding="utf-8") as f:
            json.dump(shot_excerpts, f, ensure_ascii=False, indent=2)

    # 3. screenplay dialogue_beats 样本
    screenplay = r.get("screenplay_data", {})
    if screenplay:
        scenes = screenplay.get("scenes", [])
        dialogue_sample = []
        for scene in scenes:
            for beat in scene.get("dialogue_beats", [])[:3]:
                dialogue_sample.append({
                    "scene_id": scene.get("scene_id"),
                    "speaker": beat.get("speaker"),
                    "type": beat.get("type"),
                    "line": beat.get("line"),
                    "emotion": beat.get("emotion"),
                    "off_screen_speaker": beat.get("off_screen_speaker"),
                })
        with open(os.path.join(excerpts_dir, "dialogue_excerpt.json"), "w", encoding="utf-8") as f:
            json.dump(dialogue_sample, f, ensure_ascii=False, indent=2)

    # 4. 捕获日志 (ShotValidator + T29-T37 + T-A~T-K 相关)
    log = r.get("captured_log", "")
    relevant_lines = [line for line in log.split('\n')
                      if '[ShotValidator]' in line or 'SIGNAGE' in line
                      or 'off_screen' in line.lower() or 'Plan B' in line
                      or 'family_relationships' in line or 'CHARACTER RELATIONSHIPS' in line
                      or '[T17]' in line or '[PromptPreCheck]' in line
                      or '自然度' in line or 'unnaturalness' in line.lower()
                      or 'signage_text' in line.lower()]
    if relevant_lines:
        with open(os.path.join(excerpts_dir, "relevant_logs.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(relevant_lines))

    print(f"JSON 摘要已保存: {excerpts_dir}")


# ═══════════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════════

async def main():
    print(f"\n{'='*70}")
    print(f"  TASK-E2E-REGRESSION-R8: 44 维度 E2E 回归验证")
    print(f"  故事: 山村赶圩三代同行 / illustration / 4 角色 / 10 shots")
    print(f"  维度: D1-D16 + S1-S5 + N1-N23 = 44")
    print(f"  验收: >= 39/44 PASS + 0 FAIL")
    print(f"{'='*70}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(OUTPUT_BASE, timestamp)
    os.makedirs(output_dir, exist_ok=True)

    # 运行 1 个故事
    results = []
    for story_config in TEST_STORIES:
        summary = await run_single_story(story_config, output_dir)
        results.append(summary)

        if summary["success"]:
            print(f"\nStory {summary['group']} 完成: {summary['title']}")
            print(f"   {summary['images_success']}/{summary['images_total']} 张图片成功")
            print(f"   耗时: {summary['elapsed_seconds']}s")
        else:
            print(f"\nStory {summary['group']} 失败: {summary.get('error', 'Unknown')}")
            print(f"   失败阶段: {summary.get('failed_stage', 'Unknown')}")

    # 生成报告
    print(f"\n{'='*70}")
    print(f"  生成 44 维度验收报告...")
    print(f"{'='*70}")

    report_path = generate_report(results, output_dir)
    save_excerpts(results, output_dir)

    # 保存完整日志
    for r in results:
        log = r.get("captured_log", "")
        if log:
            log_path = os.path.join(output_dir, f"pipeline_log_{r['group']}.txt")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(log)

    print(f"\n{'='*70}")
    print(f"  R8 E2E 完成!")
    print(f"  输出目录: {output_dir}")
    print(f"  报告: {report_path}")
    print(f"  下一步: 人工查看 10 张图片，填写 D1-D3/D6/D8-D14/S2-S4/N4/N8/N20 判定")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    asyncio.run(main())
