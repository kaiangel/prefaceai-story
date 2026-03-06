"""
TASK-PROMPT-BUBBLE-FOLLOWUP 任务 1: 精确 prompt 尺寸测量

选 dialogue_dense_illustration 的 Shot 1（纯 dialogue）和 Shot 5（dialogue_with_thought 复合类型），
分别用优化前/后逻辑生成完整 prompt，逐模块测量字符数。

运行: python tests/test_prompt_size_measurement.py
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.prompts.storyboard_prompts import Phase2PromptBuilder, build_system_instruction_phase2
from app.services.style_enforcer import StyleEnforcer
from app.services.image_generator import build_native_text_prompt, build_dialogue_scene_embed


# ============================================================
# 加载测试数据
# ============================================================

SOURCE_DIR = "./test_output/manualtest/prompt_bubble/dialogue_dense_illustration"
OUTPUT_DIR = "./test_output/manualtest/prompt_bubble/prompts"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_full_prompt_before(shot, storyboard, characters, style_preset, screenplay):
    """
    优化前逻辑：还原 TASK-PROMPT-BUBBLE 之前的 prompt 组装方式。
    - System Instruction: 原版（含 Style Enforcement + Aspect Ratio + 4 CRITICAL REQUIREMENTS）
    - Quality Suffix: 启用 (add_quality_suffix=True)
    - dialogue: 通过 TEXT OVERLAY REQUIREMENT 追加在 prompt 末尾
    """
    prompt_builder = Phase2PromptBuilder(
        storyboard=storyboard,
        characters=characters,
        style_preset=style_preset
    )

    # 计算参考图数量
    char_direction = shot.get("character_direction", {})
    characters_in_shot = char_direction.get("characters_visible", [])
    char_refs_count = len(characters_in_shot) * 1
    scene_ref_count = 2  # 假设 2 张场景参考图

    prompt_package = prompt_builder.build_full_prompt(
        shot=shot, screenplay=screenplay,
        include_system_instruction=True,
        scene_ref_count=scene_ref_count
    )

    # --- 还原优化前的 System Instruction ---
    gvd = storyboard.get("global_visual_direction", {})
    style = gvd.get("style_enforcement", "realistic_cinematic")
    aspect_ratio = gvd.get("aspect_ratio", "2:3")
    color_grade = gvd.get("color_grade", "neutral")
    lighting = gvd.get("overall_lighting", "natural")
    lens_style = gvd.get("lens_style", "35mm")

    system_instruction_before = f"""GLOBAL VISUAL DIRECTION:
Style Enforcement: {style}
Aspect Ratio: {aspect_ratio} (portrait orientation for mobile/Douyin)
Color Grade: {color_grade} | Lighting: {lighting} | Lens: {lens_style}

CRITICAL REQUIREMENTS:
1. Each character must look EXACTLY as described in their reference images
2. Maintain consistent color palette and lighting mood across all shots
3. Follow the specified camera angle and shot size precisely
4. Preserve the emotional tone indicated in the lighting description"""

    critical_header = prompt_package.get("critical_header", "")
    character_mapping = prompt_package.get("character_mapping", "")
    main_prompt = prompt_package.get("image_prompt", "")
    continuity_context = prompt_package.get("continuity_context", "")
    narrative_context = prompt_package.get("narrative_context", "")

    # 组装（优化前逻辑）
    full_prompt_parts = []
    if critical_header:
        full_prompt_parts.append(critical_header)
    if character_mapping:
        full_prompt_parts.append(character_mapping)
    if narrative_context:
        full_prompt_parts.append(narrative_context)
    if system_instruction_before:
        full_prompt_parts.append(f"[GLOBAL STYLE DIRECTIVE]\n{system_instruction_before}")
    if continuity_context:
        full_prompt_parts.append(f"[CONTINUITY]\n{continuity_context}")
    # 优化前：场景描述不含对话嵌入
    full_prompt_parts.append(f"[SCENE DESCRIPTION]\n{main_prompt}")

    full_prompt = "\n\n".join(full_prompt_parts)

    # StyleEnforcer WITH quality suffix（优化前）
    full_prompt = StyleEnforcer.enforce_prompt(full_prompt, style_preset, add_quality_suffix=True)

    # 优化前：dialogue 通过 TEXT OVERLAY REQUIREMENT 追加在 prompt 末尾
    text_overlay = shot.get("text_overlay", {})
    native_text_block_before = build_native_text_prompt_before(text_overlay)
    if native_text_block_before:
        full_prompt += "\n\n" + native_text_block_before

    # 各模块字符数
    modules = {
        "system_instruction": system_instruction_before,
        "quality_suffix": StyleEnforcer.build_quality_suffix(style_preset),
        "text_overlay_dialogue": native_text_block_before,
        "dialogue_scene_embed": "",  # 优化前不存在
        "critical_header": critical_header,
        "character_mapping": character_mapping,
        "narrative_context": narrative_context,
        "continuity_context": continuity_context,
        "scene_description": main_prompt,
        "style_enforcer_prefix": StyleEnforcer.build_mandatory_prefix(style_preset),
    }

    return full_prompt, modules


def build_native_text_prompt_before(text_overlay: dict) -> str:
    """优化前的 build_native_text_prompt(): dialogue 也生成 TEXT OVERLAY REQUIREMENT"""
    import re
    text_type = text_overlay.get("text_type", "none")
    chinese_text = text_overlay.get("chinese_text", "")
    position = text_overlay.get("speaker_position", "bottom")

    if text_type == "none" or not chinese_text:
        return ""

    def strip_speaker(text):
        pattern = r'^[\w\u4e00-\u9fff]+(?:内心|（[^）]*）)?[：:]\s*[「"『]?(.+?)[」"』]?$'
        match = re.match(pattern, text.strip())
        if match:
            return match.group(1)
        return text

    def extract_speaker(text):
        match = re.match(r'^([\w\u4e00-\u9fff]+?)(?:内心)?[：:]', text.strip())
        if match:
            return match.group(1)
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
            f"Narrative caption style: objective narration."
        )

    elif text_type == "dialogue":
        # 优化前: dialogue 也通过 TEXT OVERLAY REQUIREMENT 渲染
        texts = chinese_text if isinstance(chinese_text, list) else [chinese_text]
        for i, txt in enumerate(texts):
            if isinstance(txt, dict):
                txt = txt.get('text', '')
            clean = strip_speaker(txt)
            speaker = extract_speaker(txt)
            if speaker:
                blocks.append(
                    f"TEXT OVERLAY REQUIREMENT ({i+1} - Speech bubble):\n"
                    f"A white rounded speech bubble near {speaker}, "
                    f"with pointer/tail directed toward the speaker.\n"
                    f"Display Chinese text '{clean}' in black font inside the bubble."
                )
            else:
                blocks.append(
                    f"TEXT OVERLAY REQUIREMENT ({i+1} - Speech bubble):\n"
                    f"A white rounded speech bubble at {position}.\n"
                    f"Display Chinese text '{clean}' in black font inside the bubble."
                )

    elif text_type in ["dialogue_with_thought", "narration_with_thought",
                        "narration_with_dialogue", "dialogue_with_narration"]:
        texts = chinese_text if isinstance(chinese_text, list) else [chinese_text]
        for i, item in enumerate(texts):
            if isinstance(item, dict) and "type" in item:
                sub_type = item["type"]
                txt = item.get("text", "")
            else:
                txt = item
                if "内心：" in txt or "内心:" in txt:
                    sub_type = "thought"
                elif txt.startswith("旁白：") or txt.startswith("「"):
                    sub_type = "narration"
                elif "：「" in txt or ":「" in txt or "：\"" in txt:
                    sub_type = "dialogue"
                else:
                    sub_type = "narration"

            clean = strip_speaker(txt)

            if sub_type == "thought":
                blocks.append(
                    f"TEXT OVERLAY REQUIREMENT ({i+1} - Inner monologue):\n"
                    f"A semi-transparent black bar (at the bottom) spanning the full width, "
                    f"height approximately 15% of frame.\n"
                    f"Display Chinese text '{clean}' in white font, centered."
                )
            elif sub_type == "narration":
                blocks.append(
                    f"TEXT OVERLAY REQUIREMENT ({i+1} - Narration):\n"
                    f"A semi-transparent black bar (at the bottom) spanning the full width, "
                    f"height approximately 15% of frame.\n"
                    f"Display Chinese text '{clean}' in white font, centered."
                )
            elif sub_type == "dialogue":
                # 优化前：dialogue 子项也通过 TEXT OVERLAY
                speaker = extract_speaker(txt)
                if speaker:
                    blocks.append(
                        f"TEXT OVERLAY REQUIREMENT ({i+1} - Speech bubble):\n"
                        f"A white rounded speech bubble near {speaker}, "
                        f"with pointer/tail directed toward the speaker.\n"
                        f"Display Chinese text '{clean}' in black font inside the bubble."
                    )
                else:
                    blocks.append(
                        f"TEXT OVERLAY REQUIREMENT ({i+1} - Speech bubble):\n"
                        f"A white rounded speech bubble at bottom.\n"
                        f"Display Chinese text '{clean}' in black font inside the bubble."
                    )

    return "\n\n".join(blocks)


def build_full_prompt_after(shot, storyboard, characters, style_preset, screenplay):
    """
    优化后逻辑：当前 TASK-PROMPT-BUBBLE 代码的 prompt 组装方式。
    - System Instruction: 精简版（Color Grade | Lighting | Lens + CONSISTENCY）
    - Quality Suffix: 禁用 (add_quality_suffix=False)
    - dialogue: 嵌入 [SCENE DESCRIPTION]，不走 TEXT OVERLAY
    """
    prompt_builder = Phase2PromptBuilder(
        storyboard=storyboard,
        characters=characters,
        style_preset=style_preset
    )

    char_direction = shot.get("character_direction", {})
    characters_in_shot = char_direction.get("characters_visible", [])
    char_refs_count = len(characters_in_shot) * 1
    scene_ref_count = 2

    prompt_package = prompt_builder.build_full_prompt(
        shot=shot, screenplay=screenplay,
        include_system_instruction=True,
        scene_ref_count=scene_ref_count
    )

    system_instruction = prompt_package.get("system_instruction", "")  # 已经是精简版
    critical_header = prompt_package.get("critical_header", "")
    character_mapping = prompt_package.get("character_mapping", "")
    main_prompt = prompt_package.get("image_prompt", "")
    continuity_context = prompt_package.get("continuity_context", "")
    narrative_context = prompt_package.get("narrative_context", "")

    # 对话嵌入
    text_overlay = shot.get("text_overlay", {})
    dialogue_embed = build_dialogue_scene_embed(text_overlay)

    full_prompt_parts = []
    if critical_header:
        full_prompt_parts.append(critical_header)
    if character_mapping:
        full_prompt_parts.append(character_mapping)
    if narrative_context:
        full_prompt_parts.append(narrative_context)
    if system_instruction:
        full_prompt_parts.append(f"[GLOBAL STYLE DIRECTIVE]\n{system_instruction}")
    if continuity_context:
        full_prompt_parts.append(f"[CONTINUITY]\n{continuity_context}")
    # 优化后：场景描述含对话嵌入
    if dialogue_embed:
        full_prompt_parts.append(f"[SCENE DESCRIPTION]\n{main_prompt}\n{dialogue_embed}")
    else:
        full_prompt_parts.append(f"[SCENE DESCRIPTION]\n{main_prompt}")

    full_prompt = "\n\n".join(full_prompt_parts)

    # StyleEnforcer WITHOUT quality suffix（优化后）
    full_prompt = StyleEnforcer.enforce_prompt(full_prompt, style_preset, add_quality_suffix=False)

    # 优化后：thought/narration 仍走 TEXT OVERLAY
    native_text_block = build_native_text_prompt(text_overlay)
    if native_text_block:
        full_prompt += "\n\n" + native_text_block

    modules = {
        "system_instruction": system_instruction,
        "quality_suffix": "",  # 优化后禁用
        "text_overlay_dialogue": "",  # 优化后 dialogue 不走 TEXT OVERLAY
        "text_overlay_other": native_text_block,  # thought/narration 仍保留
        "dialogue_scene_embed": dialogue_embed,
        "critical_header": critical_header,
        "character_mapping": character_mapping,
        "narrative_context": narrative_context,
        "continuity_context": continuity_context,
        "scene_description": main_prompt,
        "style_enforcer_prefix": StyleEnforcer.build_mandatory_prefix(style_preset),
    }

    return full_prompt, modules


def measure_and_report(shot, shot_label, storyboard, characters, style_preset, screenplay):
    """对一个 shot 生成 before/after 报告"""
    print(f"\n{'='*60}")
    print(f"Shot: {shot_label}")
    print(f"text_type: {shot.get('text_overlay', {}).get('text_type', 'none')}")
    print(f"{'='*60}")

    before_prompt, before_modules = build_full_prompt_before(shot, storyboard, characters, style_preset, screenplay)
    after_prompt, after_modules = build_full_prompt_after(shot, storyboard, characters, style_preset, screenplay)

    # 输出表格
    print(f"\n{'模块':<35} {'优化前':>8} {'优化后':>8} {'差异':>8}")
    print("-" * 65)

    rows = []

    def row(label, before_key, after_key=None):
        bv = len(before_modules.get(before_key, ""))
        av = len(after_modules.get(after_key or before_key, ""))
        diff = av - bv
        rows.append((label, bv, av, diff))
        print(f"{label:<35} {bv:>8} {av:>8} {diff:>+8}")

    row("StyleEnforcer mandatory prefix", "style_enforcer_prefix", "style_enforcer_prefix")
    row("Critical Header", "critical_header", "critical_header")
    row("Character Mapping", "character_mapping", "character_mapping")
    row("Narrative Context", "narrative_context", "narrative_context")
    row("System Instruction", "system_instruction", "system_instruction")
    row("Continuity Context", "continuity_context", "continuity_context")
    row("Scene Description (image_prompt)", "scene_description", "scene_description")
    row("Quality Suffix", "quality_suffix", "quality_suffix")

    # TEXT OVERLAY 优化前
    before_text_overlay = len(before_modules.get("text_overlay_dialogue", ""))
    # TEXT OVERLAY 优化后（只有 thought/narration）
    after_text_overlay = len(after_modules.get("text_overlay_other", ""))
    diff_text = after_text_overlay - before_text_overlay
    rows.append(("TEXT OVERLAY REQUIREMENT", before_text_overlay, after_text_overlay, diff_text))
    print(f"{'TEXT OVERLAY REQUIREMENT':<35} {before_text_overlay:>8} {after_text_overlay:>8} {diff_text:>+8}")

    # Dialogue Scene Embed（优化后新增）
    dialogue_embed_len = len(after_modules.get("dialogue_scene_embed", ""))
    rows.append(("Dialogue Scene Embed (新增)", 0, dialogue_embed_len, dialogue_embed_len))
    print(f"{'Dialogue Scene Embed (新增)':<35} {0:>8} {dialogue_embed_len:>8} {dialogue_embed_len:>+8}")

    print("-" * 65)
    before_total = len(before_prompt)
    after_total = len(after_prompt)
    diff_total = after_total - before_total
    pct = diff_total / before_total * 100
    print(f"{'总 prompt 长度':<35} {before_total:>8} {after_total:>8} {diff_total:>+8}")
    print(f"{'净变化百分比':<35} {'':>8} {'':>8} {pct:>+7.1f}%")

    return {
        "shot_label": shot_label,
        "text_type": shot.get("text_overlay", {}).get("text_type", "none"),
        "before_total": before_total,
        "after_total": after_total,
        "diff": diff_total,
        "pct": round(pct, 1),
        "rows": rows,
        "before_prompt": before_prompt,
        "after_prompt": after_prompt,
    }


def main():
    # 加载数据
    storyboard = load_json(os.path.join(SOURCE_DIR, "4_storyboard.json"))
    characters = load_json(os.path.join(SOURCE_DIR, "2_characters.json"))
    screenplay = load_json(os.path.join(SOURCE_DIR, "3_screenplay.json"))
    style_preset = "illustration"

    shots = storyboard.get("shots", [])

    # 选 Shot 1 (dialogue) 和 Shot 5 (dialogue_with_thought)
    shot_1 = next(s for s in shots if s["shot_id"] == 1)
    shot_5 = next(s for s in shots if s["shot_id"] == 5)

    results = []
    results.append(measure_and_report(shot_1, "Shot 1 (dialogue)", storyboard, characters, style_preset, screenplay))
    results.append(measure_and_report(shot_5, "Shot 5 (dialogue_with_thought)", storyboard, characters, style_preset, screenplay))

    # 保存 prompt 文本
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for r in results:
        label = r["shot_label"].replace(" ", "_").replace("(", "").replace(")", "")
        with open(os.path.join(OUTPUT_DIR, f"{label}_BEFORE.txt"), "w", encoding="utf-8") as f:
            f.write(r["before_prompt"])
        with open(os.path.join(OUTPUT_DIR, f"{label}_AFTER.txt"), "w", encoding="utf-8") as f:
            f.write(r["after_prompt"])
        print(f"\n已保存: {label}_BEFORE.txt + {label}_AFTER.txt")

    # 生成 markdown 报告
    report_lines = [
        "# TASK-PROMPT-BUBBLE-FOLLOWUP 任务 1: 精确 Prompt 尺寸测量",
        "",
        f"测试数据: dialogue_dense_illustration (illustration 风格)",
        "",
    ]

    for r in results:
        report_lines.append(f"## {r['shot_label']} (text_type: {r['text_type']})")
        report_lines.append("")
        report_lines.append(f"| 模块 | 优化前 (chars) | 优化后 (chars) | 差异 |")
        report_lines.append(f"|------|---------------|---------------|------|")
        for label, bv, av, diff in r["rows"]:
            report_lines.append(f"| {label} | {bv} | {av} | {diff:+d} |")
        report_lines.append(f"| **总 prompt 长度** | **{r['before_total']}** | **{r['after_total']}** | **{r['diff']:+d}** |")
        report_lines.append(f"| **净变化** | | | **{r['pct']:+.1f}%** |")
        report_lines.append("")

    report_lines.append("## Prompt 文本文件")
    report_lines.append("")
    report_lines.append("保存位置: `test_output/manualtest/prompt_bubble/prompts/`")
    report_lines.append("")
    for r in results:
        label = r["shot_label"].replace(" ", "_").replace("(", "").replace(")", "")
        report_lines.append(f"- `{label}_BEFORE.txt` ({r['before_total']} chars)")
        report_lines.append(f"- `{label}_AFTER.txt` ({r['after_total']} chars)")

    report_path = os.path.join(OUTPUT_DIR, "size_measurement_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"\n报告已保存: {report_path}")


if __name__ == "__main__":
    main()
