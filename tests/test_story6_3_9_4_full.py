#!/usr/bin/env python3
"""
teststory6.3.9.4 - 面部特征增强 + 只传fullbody参考图

修复内容：
1. _build_identity_line() 添加面部特征（face_shape, skin_tone, eye描述）
2. _build_character_reference_mapping() 按characters_in_scene顺序遍历 + 单图索引
3. 只传fullbody参考图（不传portrait）
4. SCENE DIRECTION添加角色-图片映射行
"""

import asyncio
import json
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.story_generator import StoryGenerator
from app.services.storyboard_service import StoryboardService
from app.services.image_generator import ImageGenerator
from app.services.reference_image_manager import ReferenceImageManager
from app.services.scene_reference_manager import SceneReferenceManager
from app.models.style_config import ProjectStyleConfig

# 输出目录
OUTPUT_DIR = Path("test_output/manualtest/teststory6.3.9.4")

# 全新故事idea
STORY_IDEA = """
深夜的便利店，三个陌生人因为暴雨被困在一起。
一个失眠的作家、一个刚下班的护士、一个准备面试的程序员。
他们在等雨停的几个小时里，分享了各自的故事和烦恼，最终成为了朋友。
"""


class DebugLogger:
    """调试日志收集器"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.debug_dir = output_dir / "debug"
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        self.reference_log = []
        self.prompt_log = []

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

    def save_shot_prompt(self, shot_id: int, prompt: str, char_count: int):
        prompt_file = self.debug_dir / f"shot_{shot_id:02d}_prompt.txt"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(f"Shot {shot_id} Prompt\n")
            f.write(f"时间: {datetime.now().isoformat()}\n")
            f.write(f"角色数: {char_count}\n")
            f.write(f"Prompt长度: {len(prompt)} chars\n")
            f.write("=" * 60 + "\n\n")
            f.write(prompt)

        self.prompt_log.append({
            "shot_id": shot_id,
            "prompt_length": len(prompt),
            "char_count": char_count
        })

    def save_all_logs(self):
        with open(self.debug_dir / "reference_images_log.json", 'w', encoding='utf-8') as f:
            json.dump(self.reference_log, f, ensure_ascii=False, indent=2)

        with open(self.debug_dir / "prompt_log.json", 'w', encoding='utf-8') as f:
            json.dump(self.prompt_log, f, ensure_ascii=False, indent=2)


async def run_full_test():
    """完整端到端测试"""

    print("=" * 80)
    print("teststory6.3.9.4 - 面部特征增强 + 只传fullbody参考图")
    print(f"时间: {datetime.now().isoformat()}")
    print("=" * 80)

    # ========================================
    # 0. 清理旧输出目录
    # ========================================
    if OUTPUT_DIR.exists():
        print(f"\n清理旧输出目录: {OUTPUT_DIR}")
        shutil.rmtree(OUTPUT_DIR)

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    images_dir = OUTPUT_DIR / "images"
    images_dir.mkdir(exist_ok=True)
    char_refs_dir = OUTPUT_DIR / "character_refs"
    char_refs_dir.mkdir(exist_ok=True)
    scene_refs_dir = OUTPUT_DIR / "scene_refs"
    scene_refs_dir.mkdir(exist_ok=True)

    debug_logger = DebugLogger(OUTPUT_DIR)

    # ========================================
    # 1. 故事生成
    # ========================================
    print("\n" + "=" * 60)
    print("1. 生成故事")
    print("=" * 60)
    print(f"Idea: {STORY_IDEA.strip()}")

    story_gen = StoryGenerator()
    story = await story_gen.generate_story(
        idea=STORY_IDEA,
        style="realistic",
        duration_minutes=2,
        character_count=3
    )

    if not story or not story.get('success'):
        print("故事生成失败")
        return

    # 保存原始响应
    with open(OUTPUT_DIR / "story_raw.json", 'w', encoding='utf-8') as f:
        json.dump(story, f, ensure_ascii=False, indent=2)

    # 提取实际故事数据
    story = story.get('data', story)

    # 保存story.json
    with open(OUTPUT_DIR / "story.json", 'w', encoding='utf-8') as f:
        json.dump(story, f, ensure_ascii=False, indent=2)
    print(f"故事生成成功: {story.get('title', 'Untitled')}")

    characters = story.get('characters', [])
    scenes = story.get('scenes', [])
    print(f"   角色数: {len(characters)}")
    print(f"   场景数: {len(scenes)}")

    for char in characters:
        print(f"   - {char.get('name')} ({char.get('id')})")

    # 打印每个scene的characters_in_scene
    print("\n   场景角色分布:")
    for scene in scenes:
        scene_id = scene.get('scene_id')
        chars = scene.get('characters_in_scene', [])
        print(f"   Scene {scene_id}: {chars}")

    # ========================================
    # 2. 分镜拆分
    # ========================================
    print("\n" + "=" * 60)
    print("2. 分镜拆分")
    print("=" * 60)

    storyboard = StoryboardService()
    shots = await storyboard.generate_storyboard_with_splitting(
        scenes=scenes,
        characters=characters,
        style_preset="realistic",
        aspect_ratio="16:9"
    )

    # 保存shots.json
    with open(OUTPUT_DIR / "shots.json", 'w', encoding='utf-8') as f:
        json.dump(shots, f, ensure_ascii=False, indent=2)
    print(f"分镜拆分完成: {len(shots)} shots")

    # 统计多人场景
    multi_char_shots = [s for s in shots if len(s.get('characters_in_scene', [])) >= 2]
    print(f"   多人场景: {len(multi_char_shots)} shots")

    # 打印每个shot的角色数
    print("\n   Shot角色分布:")
    for shot in shots:
        shot_id = shot.get('shot_id')
        chars = shot.get('characters_in_scene', [])
        print(f"   Shot {shot_id}: {len(chars)}人 - {chars}")

    # ========================================
    # 3. 生成角色参考图
    # ========================================
    print("\n" + "=" * 60)
    print("3. 生成角色参考图")
    print("=" * 60)

    image_gen = ImageGenerator()
    ref_manager = ReferenceImageManager()

    # 创建风格配置
    style_config = ProjectStyleConfig(
        style_preset="realistic",
        color_palette="warm"
    )

    char_ref_images = {}

    for char in characters:
        char_id = char.get('id')
        char_name = char.get('name')
        print(f"\n   生成 {char_name} 参考图...")

        result = await ref_manager.generate_character_multi_refs(
            character=char,
            project_style=style_config,
            image_generator=image_gen
        )

        portrait_result = result.get('portrait', {})
        fullbody_result = result.get('fullbody', {})

        portrait_img = portrait_result.get('pil_image') if portrait_result.get('success') else None
        fullbody_img = fullbody_result.get('pil_image') if fullbody_result.get('success') else None

        if portrait_img:
            portrait_path = char_refs_dir / f"{char_id}_portrait.png"
            portrait_img.save(str(portrait_path))
            print(f"      portrait: {portrait_path.name}")

        if fullbody_img:
            fullbody_path = char_refs_dir / f"{char_id}_fullbody.png"
            fullbody_img.save(str(fullbody_path))
            print(f"      fullbody: {fullbody_path.name}")

        if portrait_img or fullbody_img:
            char_ref_images[char_id] = {
                'portrait': portrait_img,
                'fullbody': fullbody_img
            }
        else:
            print(f"      生成失败")

        await asyncio.sleep(2.0)

    print(f"\n角色参考图生成完成: {len(char_ref_images)}/{len(characters)}")

    # ========================================
    # 4. 生成场景参考图
    # ========================================
    print("\n" + "=" * 60)
    print("4. 生成场景参考图")
    print("=" * 60)

    scene_ref_manager = SceneReferenceManager()
    unique_locations = story.get('unique_locations', [])

    scene_ref_images = {}

    if unique_locations:
        print(f"   共 {len(unique_locations)} 个场景")

        anchors = await scene_ref_manager.generate_anchor_images(
            scenes=scenes,
            project_style=style_config,
            image_generator=image_gen,
            unique_locations=unique_locations
        )

        for anchor_key, anchor_data in anchors.items():
            img = anchor_data.get('image')
            if img:
                ref_path = scene_refs_dir / f"{anchor_key}.png"
                img.save(str(ref_path))
                scene_ref_images[anchor_key] = img
                print(f"   {ref_path.name}")

    print(f"\n场景参考图生成完成: {len(scene_ref_images)}")

    # ========================================
    # 5. 生成Shot图片
    # ========================================
    print("\n" + "=" * 60)
    print("5. 生成Shot图片")
    print("=" * 60)

    max_shots = min(10, len(shots))
    generated_count = 0

    for i in range(max_shots):
        shot = shots[i]
        shot_id = shot.get('shot_id', i + 1)
        chars_in_scene = shot.get('characters_in_scene', [])

        print(f"\n{'='*40}")
        print(f"Shot {shot_id} ({len(chars_in_scene)}人)")
        print(f"角色: {chars_in_scene}")
        print(f"{'='*40}")

        # 构建新prompt
        new_prompt = storyboard._build_shot_prompt(
            shot=shot,
            characters=characters,
            style_preset="realistic",
            location=shot.get('location', ''),
            time=shot.get('time', ''),
            mood=shot.get('mood', ''),
            scene_style=shot.get('scene_style', {}),
            characters_in_scene=chars_in_scene
        )

        # 保存prompt - 使用实际的chars_in_scene长度
        debug_logger.save_shot_prompt(shot_id, new_prompt, len(chars_in_scene))

        # 准备参考图 - 只传fullbody，不传portrait
        all_refs = []
        char_ref_sources = []
        scene_ref_sources = []

        for char_id in chars_in_scene:
            if char_id in char_ref_images:
                refs = char_ref_images[char_id]
                # 只传fullbody，不传portrait
                if refs.get('fullbody'):
                    all_refs.append(refs['fullbody'])
                    char_ref_sources.append(f"{char_id}_fullbody")

        # 添加场景参考图
        for loc_id, img in scene_ref_images.items():
            all_refs.append(img)
            scene_ref_sources.append(f"{loc_id}")
            break  # 只取第一个

        char_ref_count = len(char_ref_sources)
        scene_ref_count = len(scene_ref_sources)

        debug_logger.log_reference_images(
            shot_id=shot_id,
            char_refs=all_refs[:char_ref_count],
            scene_refs=all_refs[char_ref_count:],
            char_ref_sources=char_ref_sources,
            scene_ref_sources=scene_ref_sources
        )

        print(f"参考图: {len(all_refs)}张 (角色:{char_ref_count}, 场景:{scene_ref_count})")
        print(f"Prompt长度: {len(new_prompt)} chars")

        # 更新shot
        shot_copy = shot.copy()
        shot_copy['image_prompt'] = new_prompt
        shot_copy['negative_prompt'] = "blurry, low quality, distorted, deformed, bad anatomy, extra limbs, missing limbs, mutated hands, extra fingers, fewer fingers, text, watermark, signature, logo, cropped, out of frame, duplicate, ugly, disfigured, malformed, cartoon, anime, illustration, painting, drawn, 3d render"

        # 生成图像
        result = await image_gen.generate_shot_image(
            shot=shot_copy,
            reference_images=all_refs[:14],
            aspect_ratio="16:9",
            use_llm_translation=False
        )

        if result.get('success'):
            image_path = images_dir / f"shot_{shot_id:02d}.png"
            result['pil_image'].save(str(image_path))
            print(f"生成成功: {image_path.name}")
            generated_count += 1
        else:
            print(f"生成失败: {result.get('error', 'unknown')}")

        await asyncio.sleep(5.0)

    # 保存日志
    debug_logger.save_all_logs()

    # ========================================
    # 6. 生成摘要
    # ========================================
    summary_file = OUTPUT_DIR / "summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("teststory6.3.9.4 - 面部特征增强 + 只传fullbody参考图\n")
        f.write(f"测试时间: {datetime.now().isoformat()}\n")
        f.write("=" * 60 + "\n\n")

        f.write("## 故事信息\n")
        f.write(f"标题: {story.get('title', 'Untitled')}\n")
        f.write(f"角色数: {len(characters)}\n")
        f.write(f"场景数: {len(scenes)}\n")
        f.write(f"Shot数: {len(shots)}\n\n")

        f.write("## 角色列表（验证identity_line包含面部特征）\n")
        for char in characters:
            char_id = char.get('id')
            char_name = char.get('name')
            identity = storyboard._build_identity_line(char)
            f.write(f"- {char_name} ({char_id}): {identity}\n")

        f.write("\n## 生成结果\n")
        f.write(f"角色参考图: {len(char_ref_images)}/{len(characters)}\n")
        f.write(f"场景参考图: {len(scene_ref_images)}\n")
        f.write(f"Shot图片: {generated_count}/{max_shots}\n\n")

        f.write("## 参考图传递统计（只传fullbody）\n")
        for entry in debug_logger.reference_log:
            shot_id = entry['shot_id']
            total = entry['total_refs']
            char_count = entry['char_refs_count']
            scene_count = entry['scene_refs_count']
            sources = entry['char_ref_sources']
            f.write(f"Shot {shot_id}: {total}张 (角色:{char_count}, 场景:{scene_count}) - {sources}\n")

    print(f"\n保存摘要: {summary_file}")

    print("\n" + "=" * 80)
    print(f"测试完成！")
    print(f"  故事: {story.get('title', 'Untitled')}")
    print(f"  角色参考图: {len(char_ref_images)}/{len(characters)}")
    print(f"  场景参考图: {len(scene_ref_images)}")
    print(f"  Shot图片: {generated_count}/{max_shots}")
    print("=" * 80)

    # ========================================
    # 7. 验证修复效果
    # ========================================
    print("\n" + "=" * 60)
    print("验证修复效果")
    print("=" * 60)

    # 验证1：检查identity_line是否包含面部特征
    print("\n1. 检查identity_line面部特征:")
    for char in characters:
        char_name = char.get('name')
        identity = storyboard._build_identity_line(char)
        physical = char.get('physical', {})

        issues = []
        # 检查face_shape
        if physical.get('face_shape') and 'face' not in identity.lower():
            issues.append("缺少face_shape")
        # 检查skin_tone
        if physical.get('skin_tone') and 'skin' not in identity.lower():
            issues.append("缺少skin_tone")
        # 检查eye描述
        if physical.get('eye_color') and 'eye' not in identity.lower():
            issues.append("缺少eye描述")

        if issues:
            print(f"   {char_name}: {identity[:80]}...")
            print(f"      问题: {', '.join(issues)}")
        else:
            print(f"   {char_name}: 面部特征完整")
            print(f"      {identity[:80]}...")

    # 验证2：检查CHARACTER REFERENCE MAPPING格式
    print("\n2. 检查CHARACTER REFERENCE MAPPING格式:")
    for i in range(min(3, max_shots)):
        prompt_file = OUTPUT_DIR / "debug" / f"shot_{i+1:02d}_prompt.txt"
        if prompt_file.exists():
            content = prompt_file.read_text()
            if "- Image " in content and "- Images " not in content:
                print(f"   Shot {i+1}: 使用单图索引格式 (Image X)")
            else:
                print(f"   Shot {i+1}: 仍使用双图索引格式 (Images X-Y) - 需检查")

    # 验证3：检查SCENE DIRECTION是否包含角色映射行
    print("\n3. 检查SCENE DIRECTION角色映射行:")
    for i in range(min(3, max_shots)):
        prompt_file = OUTPUT_DIR / "debug" / f"shot_{i+1:02d}_prompt.txt"
        if prompt_file.exists():
            content = prompt_file.read_text()
            if "[Characters:" in content:
                # 提取映射行
                import re
                match = re.search(r'\[Characters: ([^\]]+)\]', content)
                if match:
                    print(f"   Shot {i+1}: {match.group(0)}")
            else:
                print(f"   Shot {i+1}: 缺少角色映射行")

    # 验证4：参考图只传fullbody
    print("\n4. 参考图传递验证（只传fullbody）:")
    for entry in debug_logger.reference_log:
        shot_id = entry['shot_id']
        sources = entry['char_ref_sources']

        has_portrait = any('portrait' in s for s in sources)
        all_fullbody = all('fullbody' in s for s in sources)

        if has_portrait:
            print(f"   Shot {shot_id}: 错误 - 仍传递了portrait")
        elif all_fullbody:
            print(f"   Shot {shot_id}: 正确 - 只传fullbody ({len(sources)}张)")
        else:
            print(f"   Shot {shot_id}: 异常 - {sources}")

    print(f"\n输出目录: {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(run_full_test())
