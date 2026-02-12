#!/usr/bin/env python3
"""
teststory6.3.9 - 端到端调试测试

目标：定位角色不一致问题的根源

调试点：
1. Shot生成时的参考图传递
2. Shot的完整Prompt
3. Gemini API的请求结构
4. visual_description与角色定义的对比
5. image_prompt中的角色描述

输出目录: test_output/manualtest/teststory6.3.9/
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.story_generator import StoryGenerator
from app.services.storyboard_service import StoryboardService
from app.services.image_generator import ImageGenerator
from app.services.reference_image_manager import ReferenceImageManager
from app.services.scene_reference_manager import SceneReferenceManager
from app.services.character_prompt_builder import CharacterPromptBuilder
from app.models.style_config import ProjectStyleConfig


# 输出目录
OUTPUT_DIR = Path("test_output/manualtest/teststory6.3.9")

# 新故事idea - 咖啡馆的邂逅
STORY_IDEA = """
深夜的咖啡馆，三个陌生人因为一场突如其来的暴雨被困在这里。
林小雨是一个刚失恋的设计师，正在喝着第三杯咖啡发呆；
张远是一个准备第二天面试的程序员，紧张地翻看着笔记本电脑；
老板娘陈婉是个50岁的温柔女人，默默地观察着这两个年轻人。
暴雨持续了整整一夜，三个人从陌生到熟悉，分享着各自的故事和困惑。
天亮时分，雨停了，三人在朝阳中告别，各自走向新的人生。
"""


class DebugLogger:
    """调试日志收集器"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.debug_dir = output_dir / "debug"
        self.debug_dir.mkdir(parents=True, exist_ok=True)

        # 日志文件
        self.reference_log = []
        self.gemini_request_log = []
        self.clothing_check_log = []

    def log_reference_images(self, shot_id: int, char_refs: list, scene_refs: list,
                             char_ref_sources: list, scene_ref_sources: list):
        """记录参考图传递"""
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
        """记录Gemini请求结构"""
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
        """保存shot的prompt到文件"""
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
        """保存所有日志到文件"""
        # 参考图日志
        with open(self.debug_dir / "reference_images_log.json", 'w', encoding='utf-8') as f:
            json.dump(self.reference_log, f, ensure_ascii=False, indent=2)

        # Gemini请求日志
        with open(self.debug_dir / "gemini_request_log.json", 'w', encoding='utf-8') as f:
            json.dump(self.gemini_request_log, f, ensure_ascii=False, indent=2)

        # 服装检查日志
        with open(self.debug_dir / "clothing_check.txt", 'w', encoding='utf-8') as f:
            f.write("\n".join(self.clothing_check_log))


def check_clothing_consistency(story: dict, debug_logger: DebugLogger):
    """调试点4：检查visual_description与角色定义的服装一致性"""

    lines = []
    lines.append("="*60)
    lines.append("角色服装定义 vs visual_description 一致性检查")
    lines.append("="*60)

    characters = story.get('characters', [])
    scenes = story.get('scenes', [])

    for char in characters:
        char_id = char.get('id', '')
        char_name = char.get('name', '')

        # 角色定义中的服装
        clothing = char.get('clothing', {})
        defined_top = clothing.get('top', '')
        defined_bottom = clothing.get('bottom', '')
        defined_accessories = clothing.get('accessories', [])

        lines.append(f"\n{'='*40}")
        lines.append(f"{char_name} ({char_id}) 定义的服装:")
        lines.append(f"  top: {defined_top}")
        lines.append(f"  bottom: {defined_bottom}")
        lines.append(f"  accessories: {defined_accessories}")

        # 检查每个出现该角色的scene的visual_description
        lines.append(f"\n  在各scene中的描述检查:")

        for scene in scenes:
            scene_id = scene.get('scene_id', '?')
            chars_in_scene = scene.get('characters_in_scene', [])

            if char_id in chars_in_scene:
                visual_desc = scene.get('visual_description', '')

                # 检查是否有服装相关词汇
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

    # 打印到控制台
    print("\n" + "\n".join(lines[:30]) + "\n... (完整日志见 debug/clothing_check.txt)")


def check_image_prompt_characters(shots: list):
    """调试点5：检查image_prompt中的角色描述"""

    print("\n" + "="*60)
    print("image_prompt 角色描述检查")
    print("="*60)

    for shot in shots:
        shot_id = shot.get('shot_id', '?')
        image_prompt = shot.get('image_prompt', '')

        # 检查是否包含 "CHARACTERS IN THIS SHOT" 段落
        if 'CHARACTERS IN THIS SHOT' in image_prompt.upper():
            # 提取角色描述段落
            upper_prompt = image_prompt.upper()
            start = upper_prompt.find('CHARACTERS IN THIS SHOT')

            # 找到下一个主要段落的开始
            next_sections = ['SCENE:', 'SHOT TYPE:', '[SCENE', '[SHOT']
            end = len(image_prompt)
            for section in next_sections:
                pos = upper_prompt.find(section, start + 30)
                if pos > 0 and pos < end:
                    end = pos

            char_section = image_prompt[start:end].strip()
            print(f"\n✅ Shot {shot_id} 包含角色描述段落:")
            print(f"   {char_section[:300]}...")
        else:
            print(f"\n⚠️ Shot {shot_id}: 缺少 'CHARACTERS IN THIS SHOT' 段落!")
            # 检查是否有其他角色描述方式
            if 'character' in image_prompt.lower():
                print(f"   但包含'character'关键词，可能有其他格式的角色描述")


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

    # 调试点1：记录参考图传递
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

    # 记录到日志
    debug_logger.log_reference_images(
        shot_id=shot_id,
        char_refs=char_refs,
        scene_refs=scene_refs,
        char_ref_sources=char_ref_sources,
        scene_ref_sources=scene_ref_sources
    )

    # 获取prompt
    image_prompt = shot.get('image_prompt', '')
    negative_prompt = shot.get('negative_prompt', '')

    # 调试点2：保存完整prompt
    debug_logger.save_shot_prompt(
        shot_id=shot_id,
        prompt=image_prompt,
        negative_prompt=negative_prompt,
        reference_count=len(all_refs),
        original_prompt=shot.get('original_image_prompt', image_prompt)
    )

    # 调试点3：记录Gemini请求结构（在调用前）
    contents_types = ["prompt (text)"] + [f"reference_image_{i+1} (PIL.Image)" for i in range(len(all_refs))]

    debug_logger.log_gemini_request(
        shot_id=shot_id,
        model="gemini-2.5-flash-image",
        contents_structure=contents_types,
        config={
            "response_modalities": ["IMAGE"],
            "aspect_ratio": aspect_ratio
        },
        has_system_instruction=False,  # Gemini image generation不使用system instruction
        system_instruction=None
    )

    # 调用图像生成
    result = await image_gen.generate_shot_image(
        shot=shot,
        reference_images=all_refs[:14],  # 最多14张
        aspect_ratio=aspect_ratio,
        use_llm_translation=False  # 避免额外翻译干扰调试
    )

    return result


async def run_debug_test():
    """运行端到端调试测试"""

    print("="*80)
    print("teststory6.3.9 - 端到端调试测试")
    print("="*80)
    print(f"\n目标：定位角色不一致问题的根源")
    print(f"时间：{datetime.now().isoformat()}")
    print("="*80)

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "character_refs").mkdir(exist_ok=True)
    (OUTPUT_DIR / "scene_refs").mkdir(exist_ok=True)
    (OUTPUT_DIR / "images").mkdir(exist_ok=True)
    (OUTPUT_DIR / "debug").mkdir(exist_ok=True)

    # 初始化调试日志
    debug_logger = DebugLogger(OUTPUT_DIR)

    # 初始化服务
    story_gen = StoryGenerator()
    storyboard_service = StoryboardService()
    image_gen = ImageGenerator()
    char_prompt_builder = CharacterPromptBuilder()
    style_config = ProjectStyleConfig(style_preset="realistic")

    # ===== 阶段1：故事生成 =====
    print("\n" + "="*60)
    print("阶段1：故事生成")
    print("="*60)
    print(f"Idea: {STORY_IDEA[:100]}...")

    story_result = await story_gen.generate_story(
        idea=STORY_IDEA,
        style="realistic",
        duration_minutes=3,
        character_count=3,
        min_scenes=8
    )

    if not story_result.get('success'):
        print(f"❌ 故事生成失败: {story_result.get('error')}")
        return None

    story = story_result['data']
    print(f"✅ 故事生成成功: {len(story.get('scenes', []))} scenes, {len(story.get('characters', []))} characters")
    print(f"   使用模型: {story_result.get('model_used', 'unknown')}")

    # 检查是否有unique_locations
    unique_locations = story.get('unique_locations', None)
    if unique_locations:
        print(f"   ✅ 发现 unique_locations: {len(unique_locations)} 个")
    else:
        print(f"   ⚠️ 未发现 unique_locations (将使用fallback)")

    # 检查角色是否有 character_type
    print("\n检查角色 character_type 字段:")
    for char in story.get('characters', []):
        char_name = char.get('name', 'Unknown')
        char_type = char.get('character_type', None)
        if char_type:
            print(f"   ✅ {char_name}: character_type = {char_type}")
        else:
            print(f"   ⚠️ {char_name}: 缺少 character_type 字段!")

    # 保存story.json
    with open(OUTPUT_DIR / "story.json", 'w', encoding='utf-8') as f:
        json.dump(story, f, ensure_ascii=False, indent=2)
    print(f"\n💾 保存 story.json")

    # ===== 阶段2：分镜生成 =====
    print("\n" + "="*60)
    print("阶段2：分镜生成")
    print("="*60)

    scenes = story.get('scenes', [])
    characters = story.get('characters', [])

    shots = await storyboard_service.generate_storyboard_with_splitting(
        scenes=scenes,
        characters=characters,
        style_preset="realistic",
        aspect_ratio="16:9"
    )

    print(f"✅ 分镜生成完成: {len(shots)} shots")

    # 保存shots.json
    with open(OUTPUT_DIR / "shots.json", 'w', encoding='utf-8') as f:
        json.dump(shots, f, ensure_ascii=False, indent=2)
    print(f"💾 保存 shots.json")

    # 调试点4：检查服装一致性
    check_clothing_consistency(story, debug_logger)

    # 调试点5：检查image_prompt中的角色描述
    check_image_prompt_characters(shots)

    # ===== 阶段3：角色参考图生成 =====
    print("\n" + "="*60)
    print("阶段3：角色参考图生成")
    print("="*60)

    ref_manager = ReferenceImageManager()

    # 为每个角色生成参考图
    for char in characters:
        char_name = char.get('name', 'Unknown')
        print(f"   生成 {char_name} 的参考图...")

        await ref_manager.generate_character_multi_refs(
            character=char,
            project_style=style_config,
            image_generator=image_gen,
            delay=3.0
        )

    # 保存参考图并记录来源
    char_refs_dir = OUTPUT_DIR / "character_refs"
    saved_refs = ref_manager.save_all_references(str(char_refs_dir))

    print(f"✅ 角色参考图保存完成")
    for char_id, refs in saved_refs.items():
        if isinstance(refs, dict):
            for ref_type, path in refs.items():
                print(f"   {char_id}_{ref_type}: {Path(path).name}")

    # ===== 阶段4：场景参考图生成 =====
    print("\n" + "="*60)
    print("阶段4：场景参考图生成")
    print("="*60)

    scene_ref_manager = SceneReferenceManager()

    anchor_results = await scene_ref_manager.generate_anchor_images(
        scenes=scenes,
        project_style=style_config,
        image_generator=image_gen,
        unique_locations=unique_locations,
        delay=3.0
    )

    # 保存场景参考图
    scene_refs_dir = OUTPUT_DIR / "scene_refs"
    scene_ref_paths = {}

    for anchor_key, result in anchor_results.items():
        if 'image' in result:
            filename = f"{anchor_key}.png"
            filepath = scene_refs_dir / filename
            result['image'].save(str(filepath))
            scene_ref_paths[anchor_key] = str(filepath)
            print(f"   💾 {filename}")

    print(f"✅ 场景参考图生成完成: {len(scene_ref_paths)} 张")

    # ===== 阶段5：Shot图像生成（带调试） =====
    print("\n" + "="*60)
    print("阶段5：Shot图像生成（带调试）")
    print("="*60)
    print("生成前4个shot，收集详细调试信息...")

    images_dir = OUTPUT_DIR / "images"
    generated_count = 0

    for i, shot in enumerate(shots[:4]):  # 只生成前4个
        shot_id = shot.get('shot_id', i + 1)
        chars_in_scene = shot.get('characters_in_scene', [])

        # 获取角色参考图
        char_refs = []
        char_ref_sources = []
        for char_id in chars_in_scene:
            refs = ref_manager.get_references_for_scene([char_id])
            for j, ref in enumerate(refs):
                char_refs.append(ref)
                ref_type = "portrait" if j == 0 else "fullbody"
                char_ref_sources.append(f"{char_id}_{ref_type}")

        # 获取场景参考图
        scene_refs = []
        scene_ref_sources = []
        # 简单逻辑：使用第一个可用的锚点图
        for anchor_key, result in anchor_results.items():
            if 'image' in result:
                scene_refs.append(result['image'])
                scene_ref_sources.append(anchor_key)
                break  # 只取一张场景参考图

        # 生成图像（带调试）
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
            # 保存图像
            image_path = images_dir / f"shot_{shot_id:02d}.png"
            result['pil_image'].save(str(image_path))
            print(f"   ✅ Shot {shot_id} 生成成功: {image_path.name}")
            generated_count += 1
        else:
            print(f"   ❌ Shot {shot_id} 生成失败: {result.get('error', 'unknown')}")

        # 避免API限制
        await asyncio.sleep(5.0)

    print(f"\n✅ Shot图像生成完成: {generated_count}/{min(4, len(shots))} 张")

    # ===== 阶段6：保存调试日志 =====
    print("\n" + "="*60)
    print("阶段6：保存调试日志")
    print("="*60)

    debug_logger.save_all_logs()
    print(f"💾 保存 debug/reference_images_log.json")
    print(f"💾 保存 debug/gemini_request_log.json")
    print(f"💾 保存 debug/clothing_check.txt")

    # 生成调试摘要
    summary = generate_debug_summary(story, shots, debug_logger, generated_count)
    with open(OUTPUT_DIR / "debug_summary.txt", 'w', encoding='utf-8') as f:
        f.write(summary)
    print(f"💾 保存 debug_summary.txt")

    # ===== 最终输出 =====
    print("\n" + "="*80)
    print("测试完成")
    print("="*80)

    print(f"\n📁 输出目录: {OUTPUT_DIR}")
    print(f"\n📊 生成结果:")
    print(f"  - story.json: ✅")
    print(f"  - shots.json: ✅ ({len(shots)} shots)")
    print(f"  - character_refs/: ✅ ({len(saved_refs)} 个角色)")
    print(f"  - scene_refs/: ✅ ({len(scene_ref_paths)} 张)")
    print(f"  - images/: ✅ ({generated_count} 张)")
    print(f"  - debug/: ✅ (调试文件)")

    print("\n" + "="*80)
    print("🔍 调试检查清单")
    print("="*80)

    print("""
1. 检查 debug/shot_XX_prompt.txt - 每个shot的完整prompt
   - 是否包含正确的角色描述？
   - 角色服装描述是否与character定义一致？

2. 检查 debug/reference_images_log.json - 参考图传递
   - 每个shot收到了几张参考图？
   - 是否包含所有出场角色的portrait+fullbody？

3. 检查 debug/clothing_check.txt - 服装一致性
   - visual_description是否包含与character.clothing冲突的描述？

4. 检查 debug/gemini_request_log.json - Gemini请求结构
   - contents包含了什么？
   - 有没有system instruction？

5. 人工检查 images/*.png - 角色一致性
   - 同一角色在不同shot中是否一致？
   - 如果不一致，是服装不一致还是面部不一致？

6. 检查控制台输出 - 警告信息
   - 是否出现 "⚠️ 角色 'xxx' 缺少 character_type 字段"？
   - 是否出现 "⚠️ 警告: 未找到unique_locations"？
""")

    return {
        "story": story,
        "shots": shots,
        "generated_images": generated_count,
        "output_dir": str(OUTPUT_DIR)
    }


def generate_debug_summary(story: dict, shots: list, debug_logger: DebugLogger,
                           generated_count: int) -> str:
    """生成调试摘要"""

    lines = []
    lines.append("="*60)
    lines.append("teststory6.3.9 调试摘要")
    lines.append(f"时间: {datetime.now().isoformat()}")
    lines.append("="*60)

    # 故事信息
    lines.append("\n## 故事信息")
    lines.append(f"- 标题: {story.get('title', 'N/A')}")
    lines.append(f"- 场景数: {len(story.get('scenes', []))}")
    lines.append(f"- 角色数: {len(story.get('characters', []))}")
    lines.append(f"- 是否有unique_locations: {bool(story.get('unique_locations'))}")

    # 角色信息
    lines.append("\n## 角色信息")
    for char in story.get('characters', []):
        char_name = char.get('name', 'Unknown')
        char_type = char.get('character_type', '❌ MISSING')
        clothing = char.get('clothing', {})
        top = clothing.get('top', 'N/A')
        lines.append(f"- {char_name}")
        lines.append(f"  - character_type: {char_type}")
        lines.append(f"  - clothing.top: {top[:50]}...")

    # Shot信息
    lines.append("\n## Shot信息")
    lines.append(f"- 总shot数: {len(shots)}")
    lines.append(f"- 生成图片数: {generated_count}")

    # 参考图统计
    lines.append("\n## 参考图传递统计")
    for entry in debug_logger.reference_log:
        shot_id = entry['shot_id']
        total = entry['total_refs']
        char_count = entry['char_refs_count']
        scene_count = entry['scene_refs_count']
        lines.append(f"- Shot {shot_id}: {total} 张 (角色:{char_count}, 场景:{scene_count})")
        lines.append(f"  角色参考图: {entry['char_ref_sources']}")

    # 关键问题检查
    lines.append("\n## 关键问题检查")

    # 检查character_type
    missing_type = [c['name'] for c in story.get('characters', []) if not c.get('character_type')]
    if missing_type:
        lines.append(f"⚠️ 缺少character_type的角色: {missing_type}")
    else:
        lines.append("✅ 所有角色都有character_type")

    # 检查unique_locations
    if story.get('unique_locations'):
        lines.append("✅ 使用结构化unique_locations")
    else:
        lines.append("⚠️ 使用fallback规则匹配场景")

    # 检查参考图数量
    low_refs = [e for e in debug_logger.reference_log if e['char_refs_count'] == 0]
    if low_refs:
        lines.append(f"⚠️ {len(low_refs)} 个shot没有角色参考图")
    else:
        lines.append("✅ 所有shot都有角色参考图")

    return "\n".join(lines)


if __name__ == "__main__":
    result = asyncio.run(run_debug_test())
    print("\n测试结束")
