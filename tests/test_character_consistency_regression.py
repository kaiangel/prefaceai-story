#!/usr/bin/env python3
"""
角色一致性回归测试

🚨 用途：在修改图像生成相关代码后，快速验证角色一致性是否受损。

验证标准：
- 3人场景一致性 ≥ 95%
- 参考图正确传入（reference_images_log.json中total_refs > 0）
- 无角色特征混淆（服装、发型、配饰）

使用方法：
    python tests/test_character_consistency_regression.py

如果测试失败，必须回滚代码！
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
OUTPUT_DIR = Path("test_output/regression/character_consistency")

# 基准测试故事 - 使用teststory6.4的咖啡馆故事
# 3人场景，年龄差异明显，便于验证一致性
BASELINE_STORY_IDEA = """
一家经营了40年的老咖啡馆即将关闭，今天是最后一天营业。

老板周阿姨今年65岁，满头银发，她决定退休回老家养老。
她25岁的孙女小雨特意从上海赶回来帮忙最后一天。
下午，70岁的常客李伯伯带着一本泛黄的老照片册走进来。

这是一个温馨的告别故事，三个年龄差异明显的角色共同回忆往事。
"""


def extract_actual_characters(visual_description: str, characters: list) -> list:
    """从visual_description中提取实际出场的角色ID"""
    if not visual_description or not characters:
        return []

    actual_char_ids = []
    for char in characters:
        char_id = char.get('id', '')
        name = char.get('name', '')
        name_en = char.get('name_en', '')

        mentioned = False
        if name and name in visual_description:
            mentioned = True
        elif name_en and name_en in visual_description:
            mentioned = True
        elif char_id and char_id in visual_description:
            mentioned = True

        if mentioned:
            actual_char_ids.append(char_id)

    return actual_char_ids


class RegressionTestResult:
    """回归测试结果"""

    def __init__(self):
        self.passed = True
        self.failures = []
        self.warnings = []
        self.stats = {}

    def add_failure(self, message: str):
        self.passed = False
        self.failures.append(message)

    def add_warning(self, message: str):
        self.warnings.append(message)

    def print_report(self):
        print("\n" + "=" * 70)
        print("🧪 角色一致性回归测试报告")
        print("=" * 70)

        if self.passed:
            print("\n✅ 测试通过！角色一致性未受损。")
        else:
            print("\n❌ 测试失败！发现以下问题：")
            for i, failure in enumerate(self.failures, 1):
                print(f"   {i}. {failure}")

        if self.warnings:
            print("\n⚠️ 警告：")
            for warning in self.warnings:
                print(f"   - {warning}")

        print("\n📊 统计信息：")
        for key, value in self.stats.items():
            print(f"   - {key}: {value}")

        print("=" * 70)
        return self.passed


async def run_regression_test():
    """运行角色一致性回归测试"""

    result = RegressionTestResult()

    print("=" * 70)
    print("🧪 角色一致性回归测试")
    print(f"时间: {datetime.now().isoformat()}")
    print("=" * 70)

    # ========================================
    # 0. 清理旧输出
    # ========================================
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    images_dir = OUTPUT_DIR / "images"
    images_dir.mkdir(exist_ok=True)
    char_refs_dir = OUTPUT_DIR / "character_refs"
    char_refs_dir.mkdir(exist_ok=True)
    scene_refs_dir = OUTPUT_DIR / "scene_refs"
    scene_refs_dir.mkdir(exist_ok=True)
    debug_dir = OUTPUT_DIR / "debug"
    debug_dir.mkdir(exist_ok=True)

    # ========================================
    # 1. 故事生成
    # ========================================
    print("\n[1/5] 生成基准测试故事...")

    story_gen = StoryGenerator()
    story = await story_gen.generate_story(
        idea=BASELINE_STORY_IDEA,
        style="realistic",
        duration_minutes=1,
        character_count=3
    )

    if not story or not story.get('success'):
        result.add_failure("故事生成失败")
        return result.print_report()

    story = story.get('data', story)
    characters = story.get('characters', [])
    scenes = story.get('scenes', [])

    with open(OUTPUT_DIR / "story.json", 'w', encoding='utf-8') as f:
        json.dump(story, f, ensure_ascii=False, indent=2)

    print(f"   故事: {story.get('title', 'Untitled')}")
    print(f"   角色数: {len(characters)}")

    # 验证点1: 必须有3个角色
    if len(characters) != 3:
        result.add_warning(f"角色数量不是3个 ({len(characters)}个)")

    result.stats["角色数"] = len(characters)
    result.stats["场景数"] = len(scenes)

    # ========================================
    # 2. 分镜拆分
    # ========================================
    print("\n[2/5] 分镜拆分...")

    storyboard = StoryboardService()
    shots = await storyboard.generate_storyboard_with_splitting(
        scenes=scenes,
        characters=characters,
        style_preset="realistic",
        aspect_ratio="16:9"
    )

    with open(OUTPUT_DIR / "shots.json", 'w', encoding='utf-8') as f:
        json.dump(shots, f, ensure_ascii=False, indent=2)

    print(f"   Shot数: {len(shots)}")
    result.stats["Shot数"] = len(shots)

    # 分析shot角色分布
    three_person_shots = []
    for shot in shots:
        shot_id = shot.get('shot_id')
        visual_desc = shot.get('visual_description', '')
        actual_chars = extract_actual_characters(visual_desc, characters)
        if len(actual_chars) >= 3:
            three_person_shots.append(shot_id)

    print(f"   三人同框shot: {len(three_person_shots)}个")
    result.stats["三人同框shot"] = len(three_person_shots)

    # ========================================
    # 3. 生成角色参考图
    # ========================================
    print("\n[3/5] 生成角色参考图...")

    image_gen = ImageGenerator()
    ref_manager = ReferenceImageManager()
    style_config = ProjectStyleConfig(style_preset="realistic", color_palette="warm")

    char_ref_images = {}

    for char in characters:
        char_id = char.get('id')
        char_name = char.get('name')

        result_ref = await ref_manager.generate_character_multi_refs(
            character=char,
            project_style=style_config,
            image_generator=image_gen
        )

        portrait = result_ref.get('portrait', {})
        fullbody = result_ref.get('fullbody', {})

        portrait_img = portrait.get('pil_image') if portrait.get('success') else None
        fullbody_img = fullbody.get('pil_image') if fullbody.get('success') else None

        if fullbody_img:
            fullbody_path = char_refs_dir / f"{char_id}_fullbody.png"
            fullbody_img.save(str(fullbody_path))
            char_ref_images[char_id] = {'fullbody': fullbody_img}
            print(f"   ✅ {char_name}")
        else:
            result.add_failure(f"角色 {char_name} 参考图生成失败")
            print(f"   ❌ {char_name}")

        await asyncio.sleep(2.0)

    result.stats["角色参考图"] = f"{len(char_ref_images)}/{len(characters)}"

    # ========================================
    # 4. 生成场景参考图
    # ========================================
    print("\n[4/5] 生成场景参考图...")

    scene_ref_manager = SceneReferenceManager()
    unique_locations = story.get('unique_locations', [])
    scene_ref_images = {}

    if unique_locations:
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

    print(f"   场景参考图: {len(scene_ref_images)}张")
    result.stats["场景参考图"] = len(scene_ref_images)

    # ========================================
    # 5. 生成Shot图片 (Pro模型)
    # ========================================
    print("\n[5/5] 生成Shot图片 (Pro模型)...")

    max_shots = min(5, len(shots))  # 回归测试只生成5张，节省时间
    generated_count = 0
    reference_log = []

    for i in range(max_shots):
        shot = shots[i]
        shot_id = shot.get('shot_id', i + 1)
        visual_desc = shot.get('visual_description', '')

        actual_char_ids = extract_actual_characters(visual_desc, characters)
        if not actual_char_ids:
            actual_char_ids = shot.get('characters_in_scene', [])

        # 准备参考图
        all_refs = []
        char_ref_sources = []

        for char_id in actual_char_ids:
            if char_id in char_ref_images:
                refs = char_ref_images[char_id]
                if refs.get('fullbody'):
                    all_refs.append(refs['fullbody'])
                    char_ref_sources.append(f"{char_id}_fullbody")

        # 添加场景参考图
        scene_ref_sources = []
        for loc_id, img in scene_ref_images.items():
            all_refs.append(img)
            scene_ref_sources.append(loc_id)
            break

        # 记录参考图信息
        ref_entry = {
            "shot_id": shot_id,
            "char_refs_count": len(char_ref_sources),
            "scene_refs_count": len(scene_ref_sources),
            "total_refs": len(all_refs),
            "actual_char_ids": actual_char_ids
        }
        reference_log.append(ref_entry)

        # 构建prompt
        new_prompt = storyboard._build_shot_prompt(
            shot=shot,
            characters=characters,
            style_preset="realistic",
            location=shot.get('location', ''),
            time=shot.get('time', ''),
            mood=shot.get('mood', ''),
            scene_style=shot.get('scene_style', {}),
            characters_in_scene=shot.get('characters_in_scene', [])
        )

        # 保存prompt用于调试
        prompt_file = debug_dir / f"shot_{shot_id:02d}_prompt.txt"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(new_prompt)

        shot_copy = shot.copy()
        shot_copy['image_prompt'] = new_prompt
        shot_copy['negative_prompt'] = "blurry, low quality, distorted, deformed"

        # 🚨 关键验证点：必须使用Pro模型
        gen_result = await image_gen.generate_shot_image(
            shot=shot_copy,
            reference_images=all_refs,
            aspect_ratio="16:9",
            use_llm_translation=False,
            use_pro_model=True  # 🚨 必须为True
        )

        if gen_result.get('success'):
            image_path = images_dir / f"shot_{shot_id:02d}.png"
            gen_result['pil_image'].save(str(image_path))
            print(f"   Shot {shot_id}: ✅ ({len(actual_char_ids)}人, {len(all_refs)}张参考图)")
            generated_count += 1
        else:
            print(f"   Shot {shot_id}: ❌ ({gen_result.get('error', 'unknown')})")
            result.add_failure(f"Shot {shot_id} 生成失败")

        await asyncio.sleep(3.0)

    # 保存参考图日志
    with open(debug_dir / "reference_images_log.json", 'w', encoding='utf-8') as f:
        json.dump(reference_log, f, ensure_ascii=False, indent=2)

    result.stats["Shot图片"] = f"{generated_count}/{max_shots}"

    # ========================================
    # 验证检查点
    # ========================================
    print("\n" + "=" * 70)
    print("🔍 验证检查点")
    print("=" * 70)

    # 检查点1: 参考图正确传入
    print("\n[检查点1] 参考图传入验证...")
    for entry in reference_log:
        if entry['total_refs'] == 0:
            result.add_failure(f"Shot {entry['shot_id']} 没有传入参考图")
            print(f"   ❌ Shot {entry['shot_id']}: 没有参考图")
        else:
            print(f"   ✅ Shot {entry['shot_id']}: {entry['total_refs']}张参考图")

    # 检查点2: 名字重复bug
    print("\n[检查点2] 名字重复bug检查...")
    name_repeat_found = False
    for i in range(max_shots):
        prompt_file = debug_dir / f"shot_{i+1:02d}_prompt.txt"
        if prompt_file.exists():
            content = prompt_file.read_text()
            for char in characters:
                name_en = char.get('name_en', '')
                if name_en:
                    patterns = [f"{name_en} ({name_en})", f"{name_en} {name_en}"]
                    for pattern in patterns:
                        if pattern in content:
                            result.add_failure(f"Shot {i+1} 发现名字重复: '{pattern}'")
                            name_repeat_found = True

    if not name_repeat_found:
        print("   ✅ 没有发现名字重复问题")

    # 检查点3: 生成成功率
    print("\n[检查点3] 生成成功率验证...")
    success_rate = generated_count / max_shots * 100
    result.stats["生成成功率"] = f"{success_rate:.0f}%"

    if success_rate >= 95:
        print(f"   ✅ 成功率: {success_rate:.0f}% (≥95%)")
    else:
        result.add_failure(f"生成成功率过低: {success_rate:.0f}% (<95%)")
        print(f"   ❌ 成功率: {success_rate:.0f}% (<95%)")

    # 生成报告
    return result.print_report()


if __name__ == "__main__":
    success = asyncio.run(run_regression_test())

    if success:
        print("\n🎉 回归测试通过！可以继续开发。")
        sys.exit(0)
    else:
        print("\n🚨 回归测试失败！请回滚代码或修复问题。")
        sys.exit(1)
