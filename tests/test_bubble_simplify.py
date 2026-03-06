"""
TASK-BUBBLE-SIMPLIFY: 对话气泡简化方案验证测试

背景: Bug #6 的 `near {中文名}` 方案对 NB2 不够可靠。
Founder 简化思路: 把对话直接嵌入 image_prompt，让 NB2 自行理解气泡定位。

测试 3 种对话嵌入方式（仅 dialogue 类型，thought/narration 不动）:
  A: char_ID + 中文台词  → char_003's dialogue: '都给我住口——！'
  B: 英文名 + 中文台词   → Lin Defu shouts: '都给我住口——！'
  C: 角色描述 + 中文台词  → The old man in navy Mao-jacket shouts: '都给我住口——！'

评判标准:
  1. 3 个气泡是否各自靠近正确的说话角色（最重要）
  2. 是否出现重复渲染
  3. 气泡样式是否可接受
"""

import asyncio
import json
import os
import sys
import time

from PIL import Image
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.image_generator import ImageGenerator, _strip_speaker_for_native, _extract_speaker_name
from app.services.reference_image_manager import _label_reference_image
from app.services.scene_reference_manager import _label_scene_image
from app.prompts.storyboard_prompts import Phase2PromptBuilder
from app.services.style_enforcer import StyleEnforcer

PROJECT_DIR = "test_output/manualtest/bugfix_regression/20260304_162910"
OUTPUT_DIR = "test_output/manualtest/bubble_simplify"


def load_data():
    with open(f"{PROJECT_DIR}/2_characters.json", "r", encoding="utf-8") as f:
        characters = json.load(f)
    with open(f"{PROJECT_DIR}/3_screenplay.json", "r", encoding="utf-8") as f:
        screenplay = json.load(f)
    with open(f"{PROJECT_DIR}/4_storyboard.json", "r", encoding="utf-8") as f:
        storyboard = json.load(f)
    return characters, screenplay, storyboard


def build_reference_images(shot, characters):
    """构建标注参考图（与 pipeline 完全一致）"""
    chars_in_scene = shot.get("character_direction", {}).get("characters_visible", [])
    char_names = {}
    for c in characters.get("characters", []):
        char_names[c["id"]] = c.get("name_en", c["id"])

    refs = []
    for char_id in chars_in_scene:
        fullbody_path = f"{PROJECT_DIR}/character_refs/{char_id}_fullbody.png"
        if os.path.exists(fullbody_path):
            img = Image.open(fullbody_path)
            name_en = char_names.get(char_id, char_id)
            labeled = _label_reference_image(img, f"Character: {name_en}")
            refs.append(labeled)

    scene_path = f"{PROJECT_DIR}/scene_refs/old_family_dining_room_interior_anchor.png"
    if os.path.exists(scene_path):
        img = Image.open(scene_path)
        labeled = _label_scene_image(img, "Scene: old_family_dining_room Interior")
        refs.append(labeled)

    return refs


def build_base_prompt(shot, storyboard, characters, screenplay, ref_count, char_refs_count):
    """构建不含 TEXT OVERLAY 的基础 prompt（与 generate_shot_image_phase2 一致）"""
    style_preset = "illustration"

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
    full_prompt = StyleEnforcer.enforce_prompt(full_prompt, style_preset)

    return full_prompt


def build_dialogue_block_group_a(text_overlay):
    """组 A: char_ID + 中文台词 — char_003's dialogue: '都给我住口——！'"""
    # 说话者中文名 → char_ID 映射
    name_to_id = {"林晨宇": "char_001", "林建国": "char_002", "林德福": "char_003"}

    texts = text_overlay.get("chinese_text", [])
    lines = []
    for item in texts:
        txt = item.get("text", "") if isinstance(item, dict) else item
        speaker = _extract_speaker_name(txt)
        clean = _strip_speaker_for_native(txt)
        char_id = name_to_id.get(speaker, speaker)
        lines.append(f"{char_id}'s dialogue: '{clean}'")

    return "\n".join(lines)


def build_dialogue_block_group_b(text_overlay):
    """组 B: 英文名 + 中文台词 — Lin Defu shouts: '都给我住口——！'"""
    name_to_en = {"林晨宇": "Lin Chenyu", "林建国": "Lin Jianguo", "林德福": "Lin Defu"}

    texts = text_overlay.get("chinese_text", [])
    lines = []
    for item in texts:
        txt = item.get("text", "") if isinstance(item, dict) else item
        speaker = _extract_speaker_name(txt)
        clean = _strip_speaker_for_native(txt)
        en_name = name_to_en.get(speaker, speaker)
        lines.append(f"{en_name} shouts: '{clean}'")

    return "\n".join(lines)


def build_dialogue_block_group_c(text_overlay):
    """组 C: 角色描述 + 中文台词 — The old man in navy Mao-jacket shouts: '都给我住口——！'"""
    name_to_desc = {
        "林晨宇": "The young man in light grey shirt",
        "林建国": "The middle-aged man in burgundy tunic",
        "林德福": "The old man in dark navy Mao-jacket",
    }

    texts = text_overlay.get("chinese_text", [])
    lines = []
    for item in texts:
        txt = item.get("text", "") if isinstance(item, dict) else item
        speaker = _extract_speaker_name(txt)
        clean = _strip_speaker_for_native(txt)
        desc = name_to_desc.get(speaker, speaker)
        lines.append(f"{desc} shouts: '{clean}'")

    return "\n".join(lines)


async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    characters, screenplay, storyboard = load_data()
    shots = storyboard.get("shots", [])
    shot = next((s for s in shots if s.get("shot_id") == 10), None)
    if not shot:
        print("shot_id=10 not found")
        return

    print("=" * 60)
    print("TASK-BUBBLE-SIMPLIFY: 对话气泡简化方案 A/B/C 对比")
    print("=" * 60)

    # 构建参考图
    refs = build_reference_images(shot, characters)
    print(f"\nReference images: {len(refs)}")

    # 构建基础 prompt（不含 TEXT OVERLAY）
    chars_in_scene = shot.get("character_direction", {}).get("characters_visible", [])
    base_prompt = build_base_prompt(
        shot, storyboard, characters, screenplay, len(refs), len(chars_in_scene)
    )

    text_overlay = shot.get("text_overlay", {})

    # 3 组对话嵌入方式
    groups = {
        "A": ("char_ID + 中文台词", build_dialogue_block_group_a(text_overlay)),
        "B": ("英文名 + 中文台词", build_dialogue_block_group_b(text_overlay)),
        "C": ("角色描述 + 中文台词", build_dialogue_block_group_c(text_overlay)),
    }

    image_generator = ImageGenerator()

    for group_id, (desc, dialogue_block) in groups.items():
        print(f"\n{'='*60}")
        print(f"组 {group_id}: {desc}")
        print(f"{'='*60}")
        print(f"\n  对话嵌入内容:")
        for line in dialogue_block.split("\n"):
            print(f"    {line}")

        # 在 base_prompt 末尾附加对话嵌入
        full_prompt = base_prompt + "\n\n" + dialogue_block
        full_prompt += "\n\nartstation trending, professional illustration, high detail"

        # 保存完整 prompt
        prompt_path = f"{OUTPUT_DIR}/group_{group_id}_prompt.txt"
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(full_prompt)
        print(f"  Prompt saved: {prompt_path} ({len(full_prompt)} chars)")

        # 调用 NB2 生成
        print(f"\n  Generating...")
        start_time = time.time()

        try:
            contents = [full_prompt]
            for ref_img in refs:
                contents.append(ref_img)

            from google import genai
            from google.genai import types

            client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

            result = client.models.generate_content(
                model="gemini-3.1-flash-image-preview",
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                ),
            )

            elapsed = time.time() - start_time

            # 提取图片
            pil_image = None
            if result.candidates and result.candidates[0].content and result.candidates[0].content.parts:
                for part in result.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                        import io
                        img_bytes = part.inline_data.data
                        pil_image = Image.open(io.BytesIO(img_bytes))
                        break

            if pil_image:
                output_path = f"{OUTPUT_DIR}/group_{group_id}.png"
                pil_image.save(output_path)
                w, h = pil_image.size
                print(f"  ✅ 组 {group_id} 生成成功!")
                print(f"    输出: {output_path}")
                print(f"    尺寸: {w}x{h}")
                print(f"    耗时: {elapsed:.1f}s")
            else:
                print(f"  ❌ 组 {group_id} 生成失败: 未返回图片")
                print(f"    耗时: {elapsed:.1f}s")
                if result.candidates:
                    print(f"    finish_reason: {result.candidates[0].finish_reason}")

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ❌ 组 {group_id} 异常: {e}")
            print(f"    耗时: {elapsed:.1f}s")

    print(f"\n{'='*60}")
    print(f"3 组对比完成，图片保存在 {OUTPUT_DIR}/")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
