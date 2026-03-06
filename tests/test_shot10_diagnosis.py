"""
TASK-SHOT10-REGEN 诊断脚本

全维度对比 shot_10（我的脚本生成）和 shot_11（pipeline 生成）的：
1. 完整 prompt 内容
2. 参考图标注内容
3. 所有传入参数
4. 代码路径差异

目的：确认角色一致性差异是模型随机性还是代码/prompt 问题。
"""

import json
import os
import sys
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.image_generator import ImageGenerator, build_native_text_prompt
from app.services.reference_image_manager import _label_reference_image
from app.services.scene_reference_manager import _label_scene_image
from app.prompts.storyboard_prompts import Phase2PromptBuilder
from app.services.style_enforcer import StyleEnforcer

PROJECT_DIR = "test_output/manualtest/bugfix_regression/20260304_162910"
DIAG_DIR = "test_output/manualtest/shot10_diagnosis"


def load_data():
    with open(f"{PROJECT_DIR}/2_characters.json", "r", encoding="utf-8") as f:
        characters = json.load(f)
    with open(f"{PROJECT_DIR}/3_screenplay.json", "r", encoding="utf-8") as f:
        screenplay = json.load(f)
    with open(f"{PROJECT_DIR}/4_storyboard.json", "r", encoding="utf-8") as f:
        storyboard = json.load(f)
    return characters, screenplay, storyboard


def build_refs_for_shot(shot, characters, location_id):
    """模拟我的脚本的参考图构建方式"""
    chars_in_scene = shot.get("character_direction", {}).get("characters_visible", [])
    char_names = {}
    for c in characters.get("characters", []):
        char_names[c["id"]] = c.get("name_en", c["id"])

    refs = []
    ref_labels = []
    for char_id in chars_in_scene:
        fullbody_path = f"{PROJECT_DIR}/character_refs/{char_id}_fullbody.png"
        if os.path.exists(fullbody_path):
            img = Image.open(fullbody_path)
            name_en = char_names.get(char_id, char_id)
            label = f"Character: {name_en}"
            labeled = _label_reference_image(img, label)
            refs.append(labeled)
            ref_labels.append(f"  [{len(refs)}] {char_id} fullbody → '{label}' ({img.size[0]}x{img.size[1]})")

    scene_path = f"{PROJECT_DIR}/scene_refs/{location_id}_interior_anchor.png"
    if os.path.exists(scene_path):
        img = Image.open(scene_path)
        label = f"Scene: {location_id} Interior"
        labeled = _label_scene_image(img, label)
        refs.append(labeled)
        ref_labels.append(f"  [{len(refs)}] {location_id} interior → '{label}' ({img.size[0]}x{img.size[1]})")

    return refs, ref_labels


def build_full_prompt_for_shot(shot, storyboard, characters, screenplay, ref_count, char_refs_count):
    """完整复现 generate_shot_image_phase2 中的 prompt 构建逻辑"""
    style_preset = "illustration"

    # 1. PromptBuilder
    prompt_builder = Phase2PromptBuilder(
        storyboard=storyboard,
        characters=characters,
        style_preset=style_preset
    )

    scene_ref_count = max(0, ref_count - char_refs_count)

    prompt_package = prompt_builder.build_full_prompt(
        shot=shot,
        screenplay=screenplay,
        include_system_instruction=True,
        scene_ref_count=scene_ref_count
    )

    # 2. 组装 (与 image_generator.py L679-704 完全一致)
    system_instruction = prompt_package.get("system_instruction", "")
    critical_header = prompt_package.get("critical_header", "")
    character_mapping = prompt_package.get("character_mapping", "")
    main_prompt = prompt_package.get("image_prompt", "")
    continuity_context = prompt_package.get("continuity_context", "")
    narrative_context = prompt_package.get("narrative_context", "")

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
    full_prompt_parts.append(f"[SCENE DESCRIPTION]\n{main_prompt}")

    full_prompt = "\n\n".join(full_prompt_parts)

    # 3. StyleEnforcer
    full_prompt = StyleEnforcer.enforce_prompt(full_prompt, style_preset)

    # 4. color_mode
    color_mode = shot.get("color_mode", "full_color")
    if color_mode == "grayscale":
        full_prompt += "\n\n[COLOR OVERRIDE] This shot MUST be in GRAYSCALE, black and white."
    elif color_mode == "sepia":
        full_prompt += "\n\n[COLOR OVERRIDE] This shot MUST be in SEPIA TONE, warm brownish monochrome."

    # 5. Native text
    text_overlay = shot.get("text_overlay", {})
    native_text_block = build_native_text_prompt(text_overlay)
    if native_text_block:
        full_prompt += "\n\n" + native_text_block

    return full_prompt, prompt_package


def main():
    os.makedirs(DIAG_DIR, exist_ok=True)

    characters, screenplay, storyboard = load_data()
    shots = storyboard.get("shots", [])

    # 获取 scene→location 映射
    scene_locations = {}
    for scene in screenplay.get("scenes", []):
        sid = scene.get("scene_id") or scene.get("id")
        loc = scene.get("location_id", "unknown")
        scene_locations[sid] = loc

    print("=" * 80)
    print("SHOT_10 vs SHOT_11 全维度诊断")
    print("=" * 80)

    for shot_id in [10, 11]:
        shot = next((s for s in shots if s.get("shot_id") == shot_id), None)
        if not shot:
            print(f"\n❌ shot_{shot_id} not found")
            continue

        scene_id = shot.get("scene_id")
        location_id = scene_locations.get(scene_id, "unknown")
        chars_in_scene = shot.get("character_direction", {}).get("characters_visible", [])
        shot_type = shot.get("camera", {}).get("shot_size", "medium_shot")

        print(f"\n{'='*80}")
        print(f"SHOT {shot_id} 诊断")
        print(f"{'='*80}")

        # === 维度 1: Shot 元数据 ===
        print(f"\n--- 维度 1: Shot 元数据 ---")
        print(f"  scene_id: {scene_id}")
        print(f"  location_id: {location_id}")
        print(f"  shot_size: {shot_type}")
        print(f"  angle: {shot.get('camera', {}).get('angle')}")
        print(f"  characters: {chars_in_scene}")
        print(f"  text_type: {shot.get('text_overlay', {}).get('text_type')}")
        ct = shot.get("text_overlay", {}).get("chinese_text", "")
        if isinstance(ct, list) and len(ct) > 0:
            print(f"  chinese_text format: {'dict list' if isinstance(ct[0], dict) else 'string list'} ({len(ct)} items)")
        else:
            print(f"  chinese_text format: string")
        print(f"  color_mode: {shot.get('color_mode')}")

        # === 维度 2: 参考图 ===
        print(f"\n--- 维度 2: 参考图构建 ---")
        refs, ref_labels = build_refs_for_shot(shot, characters, location_id)
        for label in ref_labels:
            print(label)
        print(f"  Total: {len(refs)} refs")

        # 保存标注后的参考图供目视对比
        for i, ref in enumerate(refs):
            ref.save(f"{DIAG_DIR}/shot{shot_id:02d}_ref_{i+1}.png")

        # === 维度 3: 完整 Prompt ===
        print(f"\n--- 维度 3: Prompt 构建 ---")
        char_refs_count = len(chars_in_scene)
        full_prompt, pkg = build_full_prompt_for_shot(
            shot, storyboard, characters, screenplay, len(refs), char_refs_count
        )

        # 保存完整 prompt
        prompt_path = f"{DIAG_DIR}/shot{shot_id:02d}_full_prompt.txt"
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(full_prompt)
        print(f"  Prompt saved: {prompt_path}")
        print(f"  Prompt length: {len(full_prompt)} chars")

        # 打印 prompt 各部分长度
        print(f"  Parts:")
        print(f"    critical_header: {len(pkg.get('critical_header', ''))} chars")
        print(f"    character_mapping: {len(pkg.get('character_mapping', ''))} chars")
        print(f"    narrative_context: {len(pkg.get('narrative_context', ''))} chars")
        print(f"    system_instruction: {len(pkg.get('system_instruction', ''))} chars")
        print(f"    continuity_context: {len(pkg.get('continuity_context', ''))} chars")
        print(f"    image_prompt: {len(pkg.get('image_prompt', ''))} chars")

        # 打印 character_mapping 全文（关键！）
        print(f"\n  === CHARACTER MAPPING ===")
        print(pkg.get("character_mapping", "(empty)"))
        print(f"  === END CHARACTER MAPPING ===")

        # 打印 native text block
        text_overlay = shot.get("text_overlay", {})
        native_text = build_native_text_prompt(text_overlay)
        print(f"\n  === NATIVE TEXT BLOCK ===")
        print(native_text if native_text else "(empty)")
        print(f"  === END NATIVE TEXT BLOCK ===")

        # === 维度 4: API 调用参数 ===
        print(f"\n--- 维度 4: API 调用参数 ---")
        print(f"  model: gemini-3.1-flash-image-preview (NB2)")
        print(f"  style_preset: illustration")
        print(f"  aspect_ratio: 2:3")
        print(f"  use_native_text: True")
        print(f"  contents: [prompt_text, ref_1, ref_2, ..., ref_{len(refs)}]")
        print(f"  response_modalities: [IMAGE]")

    # === 维度 5: Prompt 差异对比 ===
    print(f"\n{'='*80}")
    print(f"维度 5: SHOT_10 vs SHOT_11 Prompt 结构对比")
    print(f"{'='*80}")

    p10_path = f"{DIAG_DIR}/shot10_full_prompt.txt"
    p11_path = f"{DIAG_DIR}/shot11_full_prompt.txt"

    with open(p10_path) as f:
        p10 = f.read()
    with open(p11_path) as f:
        p11 = f.read()

    # 对比结构性部分（非 shot-specific 内容应完全一致）
    # StyleEnforcer prefix 应相同
    p10_lines = p10.split("\n")
    p11_lines = p11.split("\n")

    # 找到 MANDATORY STYLE 块的结束
    def find_style_end(lines):
        for i, line in enumerate(lines):
            if "This style requirement applies to ALL elements" in line:
                return i
        return 0

    style_end_10 = find_style_end(p10_lines)
    style_end_11 = find_style_end(p11_lines)

    style_block_10 = "\n".join(p10_lines[:style_end_10+2])
    style_block_11 = "\n".join(p11_lines[:style_end_11+2])

    print(f"\n  Style block identical: {style_block_10 == style_block_11}")
    if style_block_10 != style_block_11:
        print(f"  ⚠️ Style blocks differ!")

    # CHARACTER & SCENE REFERENCES 块对比
    def extract_section(text, start_marker, end_markers):
        start = text.find(start_marker)
        if start == -1:
            return "(not found)"
        end = len(text)
        for marker in end_markers:
            pos = text.find(marker, start + len(start_marker))
            if pos != -1 and pos < end:
                end = pos
        return text[start:end].strip()

    ref_section_10 = extract_section(p10, "CHARACTER & SCENE REFERENCES:", ["[GLOBAL STYLE", "[SCENE DESCRIPTION"])
    ref_section_11 = extract_section(p11, "CHARACTER & SCENE REFERENCES:", ["[GLOBAL STYLE", "[SCENE DESCRIPTION"])

    print(f"  Ref section identical: {ref_section_10 == ref_section_11}")
    if ref_section_10 != ref_section_11:
        print(f"\n  Shot 10 ref section:\n{ref_section_10}")
        print(f"\n  Shot 11 ref section:\n{ref_section_11}")
    else:
        print(f"\n  Shared ref section:")
        print(f"  {ref_section_10[:500]}")

    # === 维度 6: pipeline vs 我的脚本 代码路径差异 ===
    print(f"\n{'='*80}")
    print(f"维度 6: 代码路径差异分析")
    print(f"{'='*80}")
    print("""
  Pipeline (Tester 回归测试生成 shot_11/15):
    1. ReferenceImageManager 生成参考图 → 存内存 PIL
    2. get_smart_references_for_scene(chars, shot_type) → 内存 PIL + _label_reference_image()
    3. SceneReferenceManager.get_references_for_location(loc_id) → 内存 PIL + _label_scene_image()
    4. generate_shot_image_phase2(shot, storyboard, characters, style_preset, all_refs, screenplay, "2:3")
       — use_native_text 默认 True

  我的脚本 (生成 shot_10):
    1. Image.open() 从磁盘加载 PNG
    2. _label_reference_image(img, label) → 与 pipeline 用完全相同的函数
    3. _label_scene_image(img, label) → 与 pipeline 用完全相同的函数
    4. generate_shot_image_phase2(shot, storyboard, characters, "illustration", refs, screenplay, "2:3", use_native_text=True)

  差异点分析:
    ✅ 标注函数: 完全相同 (_label_reference_image / _label_scene_image)
    ✅ 标签文本: "Character: {name_en}" / "Scene: {location_id} Interior" — 格式相同
    ✅ 参考图选择: wide_shot → fullbody — 逻辑相同
    ✅ Prompt 构建: Phase2PromptBuilder → StyleEnforcer → native_text — 路径相同
    ✅ API 参数: model/aspect_ratio/response_modalities — 相同
    ⚠️ 图像来源: pipeline=内存 PIL vs 脚本=磁盘 PNG (PNG 无损, 像素应完全一致)
    ⚠️ style_preset: pipeline 从 orchestrator 传入 vs 脚本硬编码 "illustration"
""")

    # 验证 style_preset
    print(f"  检查 storyboard 中的 style_preset:")
    gvd = storyboard.get("global_visual_direction", {})
    print(f"    global_visual_direction.style_enforcement: {gvd.get('style_enforcement', 'N/A')}")
    print(f"    global_visual_direction.style_preset: {gvd.get('style_preset', 'N/A')}")

    # === 最终结论 ===
    print(f"\n{'='*80}")
    print(f"诊断结论")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
