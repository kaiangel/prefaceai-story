#!/usr/bin/env python3
"""
teststory6.3.9 续集 - 生成shot 5-10

继续使用已有的story.json和参考图，生成更多shots
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.image_generator import ImageGenerator
from app.services.reference_image_manager import ReferenceImageManager


# 输出目录
OUTPUT_DIR = Path("test_output/manualtest/teststory6.3.9")


class DebugLogger:
    """调试日志收集器"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.debug_dir = output_dir / "debug"
        self.debug_dir.mkdir(parents=True, exist_ok=True)

        # 加载已有日志
        self.reference_log = self._load_json("reference_images_log.json") or []
        self.gemini_request_log = self._load_json("gemini_request_log.json") or []
        self.clothing_check_log = []

    def _load_json(self, filename: str) -> list:
        filepath = self.debug_dir / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def log_reference_images(self, shot_id: int, char_refs: list, scene_refs: list,
                             char_ref_sources: list, scene_ref_sources: list):
        entry = {
            "shot_id": shot_id,
            "timestamp": datetime.now().isoformat(),
            "char_refs_count": len(char_refs),
            "scene_refs_count": len(scene_refs),
            "total_refs": len(char_refs) + len(scene_refs),
            "char_ref_sources": char_ref_sources,
            "scene_ref_sources": scene_ref_sources
        }
        self.reference_log.append(entry)

    def log_gemini_request(self, shot_id: int, model: str, contents_structure: list,
                           config: dict, has_system_instruction: bool = False,
                           system_instruction: str = None):
        entry = {
            "shot_id": shot_id,
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "contents_count": len(contents_structure),
            "contents_types": contents_structure,
            "config": config,
            "has_system_instruction": has_system_instruction,
            "system_instruction_preview": system_instruction[:500] if system_instruction else None
        }
        self.gemini_request_log.append(entry)

    def save_shot_prompt(self, shot_id: int, prompt: str, negative_prompt: str,
                         reference_count: int, original_prompt: str = None):
        prompt_file = self.debug_dir / f"shot_{shot_id:02d}_prompt.txt"

        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(f"{'='*60}\n")
            f.write(f"Shot {shot_id} Prompt 调试信息\n")
            f.write(f"时间: {datetime.now().isoformat()}\n")
            f.write(f"{'='*60}\n\n")

            if original_prompt and original_prompt != prompt:
                f.write(f"=== 原始Prompt (翻译前) ===\n\n")
                f.write(f"{original_prompt}\n\n")

            f.write(f"=== 发送给Gemini的Prompt ===\n\n")
            f.write(f"{prompt}\n\n")

            f.write(f"{'='*60}\n")
            f.write(f"Negative Prompt:\n{negative_prompt}\n\n")

            f.write(f"{'='*60}\n")
            f.write(f"参考图数量: {reference_count}\n")

    def save_all_logs(self):
        with open(self.debug_dir / "reference_images_log.json", 'w', encoding='utf-8') as f:
            json.dump(self.reference_log, f, ensure_ascii=False, indent=2)

        with open(self.debug_dir / "gemini_request_log.json", 'w', encoding='utf-8') as f:
            json.dump(self.gemini_request_log, f, ensure_ascii=False, indent=2)

        with open(self.debug_dir / "clothing_check.txt", 'w', encoding='utf-8') as f:
            f.write("\n".join(self.clothing_check_log))


def check_clothing_consistency(story: dict, debug_logger: DebugLogger):
    """检查服装一致性"""
    lines = []
    lines.append("="*60)
    lines.append("角色服装定义 vs visual_description 一致性检查")
    lines.append(f"更新时间: {datetime.now().isoformat()}")
    lines.append("="*60)

    characters = story.get('characters', [])
    scenes = story.get('scenes', [])

    for char in characters:
        char_id = char.get('id', '')
        char_name = char.get('name', '')

        clothing = char.get('clothing', {})
        defined_top = clothing.get('top', '')
        defined_bottom = clothing.get('bottom', '')
        defined_accessories = clothing.get('accessories', [])

        lines.append(f"\n{'='*40}")
        lines.append(f"{char_name} ({char_id}) 定义的服装:")
        lines.append(f"  top: {defined_top}")
        lines.append(f"  bottom: {defined_bottom}")
        lines.append(f"  accessories: {defined_accessories}")

        lines.append(f"\n  在各scene中的描述检查:")

        for scene in scenes:
            scene_id = scene.get('scene_id', '?')
            chars_in_scene = scene.get('characters_in_scene', [])

            if char_id in chars_in_scene:
                visual_desc = scene.get('visual_description', '')

                clothing_keywords = [
                    'shirt', 'jacket', 'pants', 'dress', 'wearing', 'clothes',
                    'sweater', 'coat', 'suit', 'blouse', 'skirt', 'jeans',
                    '衬衫', '外套', '裤子', '裙子', '穿着', '毛衣', '大衣'
                ]

                found_keywords = [kw for kw in clothing_keywords if kw.lower() in visual_desc.lower()]

                if found_keywords:
                    lines.append(f"  ⚠️ Scene {scene_id}: visual_description包含服装词汇: {found_keywords}")
                    lines.append(f"     描述片段: {visual_desc[:200]}...")
                else:
                    lines.append(f"  ✅ Scene {scene_id}: visual_description无明显服装描述")

    debug_logger.clothing_check_log = lines


def generate_debug_summary(story: dict, shots: list, debug_logger: DebugLogger,
                           generated_count: int) -> str:
    lines = []
    lines.append("="*60)
    lines.append("teststory6.3.9 调试摘要 (更新版)")
    lines.append(f"更新时间: {datetime.now().isoformat()}")
    lines.append("="*60)

    lines.append("\n## 故事信息")
    lines.append(f"- 标题: {story.get('title', 'N/A')}")
    lines.append(f"- 场景数: {len(story.get('scenes', []))}")
    lines.append(f"- 角色数: {len(story.get('characters', []))}")
    lines.append(f"- 是否有unique_locations: {bool(story.get('unique_locations'))}")

    lines.append("\n## 角色信息")
    for char in story.get('characters', []):
        char_name = char.get('name', 'Unknown')
        char_type = char.get('character_type', '❌ MISSING')
        clothing = char.get('clothing', {})
        top = clothing.get('top', 'N/A')
        lines.append(f"- {char_name}")
        lines.append(f"  - character_type: {char_type}")
        lines.append(f"  - clothing.top: {top[:50]}...")

    lines.append("\n## Shot信息")
    lines.append(f"- 总shot数: {len(shots)}")
    lines.append(f"- 已生成图片数: {generated_count}")

    lines.append("\n## 参考图传递统计")
    for entry in debug_logger.reference_log:
        shot_id = entry['shot_id']
        total = entry['total_refs']
        char_count = entry['char_refs_count']
        scene_count = entry['scene_refs_count']
        lines.append(f"- Shot {shot_id}: {total} 张 (角色:{char_count}, 场景:{scene_count})")
        lines.append(f"  角色参考图: {entry['char_ref_sources']}")

    lines.append("\n## 关键问题检查")

    missing_type = [c['name'] for c in story.get('characters', []) if not c.get('character_type')]
    if missing_type:
        lines.append(f"⚠️ 缺少character_type的角色: {missing_type}")
    else:
        lines.append("✅ 所有角色都有character_type")

    if story.get('unique_locations'):
        lines.append("✅ 使用结构化unique_locations")
    else:
        lines.append("⚠️ 使用fallback规则匹配场景")

    low_refs = [e for e in debug_logger.reference_log if e['char_refs_count'] == 0]
    if low_refs:
        lines.append(f"⚠️ {len(low_refs)} 个shot没有角色参考图")
    else:
        lines.append("✅ 所有shot都有角色参考图")

    return "\n".join(lines)


async def generate_shot_with_debug(
    image_gen: ImageGenerator,
    shot: dict,
    char_refs: list,
    scene_refs: list,
    char_ref_sources: list,
    scene_ref_sources: list,
    debug_logger: DebugLogger,
    aspect_ratio: str = "16:9"
) -> dict:
    """带调试日志的shot图像生成"""

    shot_id = shot.get('shot_id', 0)

    print(f"\n{'='*60}")
    print(f"Shot {shot_id} 调试信息")
    print(f"{'='*60}")

    print(f"characters_in_scene: {shot.get('characters_in_scene', [])}")
    print(f"角色参考图数量: {len(char_refs)}")
    for i, source in enumerate(char_ref_sources):
        print(f"  [{i}] {source}")

    print(f"场景参考图数量: {len(scene_refs)}")
    for i, source in enumerate(scene_ref_sources):
        print(f"  [{i}] {source}")

    all_refs = char_refs + scene_refs
    print(f"总参考图数量: {len(all_refs)} (最大14张)")

    debug_logger.log_reference_images(
        shot_id=shot_id,
        char_refs=char_refs,
        scene_refs=scene_refs,
        char_ref_sources=char_ref_sources,
        scene_ref_sources=scene_ref_sources
    )

    image_prompt = shot.get('image_prompt', '')
    negative_prompt = shot.get('negative_prompt', '')

    debug_logger.save_shot_prompt(
        shot_id=shot_id,
        prompt=image_prompt,
        negative_prompt=negative_prompt,
        reference_count=len(all_refs),
        original_prompt=shot.get('original_image_prompt', image_prompt)
    )

    contents_types = ["prompt (text)"] + [f"reference_image_{i+1} (PIL.Image)" for i in range(len(all_refs))]

    debug_logger.log_gemini_request(
        shot_id=shot_id,
        model="gemini-2.5-flash-image",
        contents_structure=contents_types,
        config={
            "response_modalities": ["IMAGE"],
            "aspect_ratio": aspect_ratio
        },
        has_system_instruction=False,
        system_instruction=None
    )

    result = await image_gen.generate_shot_image(
        shot=shot,
        reference_images=all_refs[:14],
        aspect_ratio=aspect_ratio,
        use_llm_translation=False
    )

    return result


async def run_continue_test():
    """继续生成shot 5-10"""

    print("="*80)
    print("teststory6.3.9 续集 - 生成 Shot 5-10")
    print("="*80)
    print(f"时间：{datetime.now().isoformat()}")
    print("="*80)

    # 加载已有数据
    with open(OUTPUT_DIR / "story.json", 'r', encoding='utf-8') as f:
        story = json.load(f)

    with open(OUTPUT_DIR / "shots.json", 'r', encoding='utf-8') as f:
        shots = json.load(f)

    characters = story.get('characters', [])
    print(f"✅ 加载数据: {len(shots)} shots, {len(characters)} characters")

    # 初始化
    debug_logger = DebugLogger(OUTPUT_DIR)
    image_gen = ImageGenerator()

    # 加载已有的角色参考图
    char_refs_dir = OUTPUT_DIR / "character_refs"
    char_ref_images = {}

    for char in characters:
        char_id = char.get('id')
        portrait_path = char_refs_dir / f"{char_id}_portrait.png"
        fullbody_path = char_refs_dir / f"{char_id}_fullbody.png"

        if portrait_path.exists() and fullbody_path.exists():
            char_ref_images[char_id] = {
                'portrait': Image.open(portrait_path),
                'fullbody': Image.open(fullbody_path)
            }
            print(f"   ✅ 加载 {char_id} 参考图")

    # 加载场景参考图
    scene_refs_dir = OUTPUT_DIR / "scene_refs"
    scene_ref_images = {}

    for ref_file in scene_refs_dir.glob("*.png"):
        anchor_key = ref_file.stem
        scene_ref_images[anchor_key] = Image.open(ref_file)
        print(f"   ✅ 加载场景参考图: {anchor_key}")

    # 生成shot 5-10
    print("\n" + "="*60)
    print("生成 Shot 5-10")
    print("="*60)

    images_dir = OUTPUT_DIR / "images"
    generated_count = 4  # 已有4张

    for i, shot in enumerate(shots[4:10]):  # shot 5-10 (index 4-9)
        shot_id = shot.get('shot_id', i + 5)
        chars_in_scene = shot.get('characters_in_scene', [])

        # 获取角色参考图
        char_refs = []
        char_ref_sources = []
        for char_id in chars_in_scene:
            if char_id in char_ref_images:
                refs = char_ref_images[char_id]
                char_refs.append(refs['portrait'])
                char_ref_sources.append(f"{char_id}_portrait")
                char_refs.append(refs['fullbody'])
                char_ref_sources.append(f"{char_id}_fullbody")

        # 获取场景参考图
        scene_refs = []
        scene_ref_sources = []
        if scene_ref_images:
            # 使用第一个可用的锚点图
            for anchor_key, img in scene_ref_images.items():
                scene_refs.append(img)
                scene_ref_sources.append(anchor_key)
                break

        # 生成图像
        result = await generate_shot_with_debug(
            image_gen=image_gen,
            shot=shot,
            char_refs=char_refs,
            scene_refs=scene_refs,
            char_ref_sources=char_ref_sources,
            scene_ref_sources=scene_ref_sources,
            debug_logger=debug_logger,
            aspect_ratio="16:9"
        )

        if result.get('success'):
            image_path = images_dir / f"shot_{shot_id:02d}.png"
            result['pil_image'].save(str(image_path))
            print(f"   ✅ Shot {shot_id} 生成成功: {image_path.name}")
            generated_count += 1
        else:
            print(f"   ❌ Shot {shot_id} 生成失败: {result.get('error', 'unknown')}")

        await asyncio.sleep(5.0)

    print(f"\n✅ Shot 5-10 生成完成: {generated_count - 4}/6 张")

    # 更新服装检查
    check_clothing_consistency(story, debug_logger)

    # 保存更新的日志
    debug_logger.save_all_logs()
    print(f"\n💾 更新 debug/reference_images_log.json")
    print(f"💾 更新 debug/gemini_request_log.json")
    print(f"💾 更新 debug/clothing_check.txt")

    # 更新摘要
    summary = generate_debug_summary(story, shots, debug_logger, generated_count)
    with open(OUTPUT_DIR / "debug_summary.txt", 'w', encoding='utf-8') as f:
        f.write(summary)
    print(f"💾 更新 debug_summary.txt")

    print("\n" + "="*80)
    print(f"完成！共生成 {generated_count} 张图像")
    print("="*80)

    return generated_count


if __name__ == "__main__":
    result = asyncio.run(run_continue_test())
    print("\n测试结束")
