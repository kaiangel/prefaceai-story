#!/usr/bin/env python3
"""
teststory6.6 - 5人以上场景边界测试

验证目标：
1. Pro模型对5-6人同框的处理能力
2. 找出角色数量的上限（在哪个人数开始出现混淆）
3. 写实风格下的最严格测试

核心设置：
- 风格：realistic (写实，最严格测试)
- 角色：6人 (家庭聚会场景)
- 必须包含：2张5人同框 + 1张6人同框
"""

import asyncio
import json
import os
import sys
import shutil
import re
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
OUTPUT_DIR = Path("test_output/manualtest/teststory6.6_multichar")

# 家庭聚会故事idea - 6人角色
STORY_IDEA = """
春节除夕夜，陈家三代人终于齐聚一堂。

爷爷陈建国，75岁，白发苍苍，德高望重的退休教授。
奶奶王秀兰，72岁，和蔼可亲，围着围裙准备年夜饭。
大儿子陈明远，48岁，西装革履的企业高管，常年在外工作。
大儿媳林晓雯，45岁，温婉优雅的大学教授，戴着眼镜。
孙子陈浩宇，22岁，阳光帅气的大学生，刚放寒假回来。
孙女陈诗雨，18岁，甜美可爱的高中生，是爷爷奶奶最疼爱的小孙女。

这是一个温馨的家庭故事，讲述一家六口在除夕夜的团圆时光。
从准备年夜饭，到吃团圆饭，再到一起看春晚、发红包，充满了欢声笑语。
最后，全家人在客厅合影留念，记录下这幸福的一刻。
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


class DebugLogger:
    """调试日志收集器"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.debug_dir = output_dir / "debug"
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        self.reference_log = []
        self.prompt_log = []

    def log_reference_images(self, shot_id: int, char_refs: list, scene_refs: list,
                             char_ref_sources: list, scene_ref_sources: list,
                             actual_char_ids: list):
        entry = {
            "shot_id": shot_id,
            "timestamp": datetime.now().isoformat(),
            "char_refs_count": len(char_refs),
            "scene_refs_count": len(scene_refs),
            "total_refs": len(char_refs) + len(scene_refs),
            "char_ref_sources": char_ref_sources,
            "scene_ref_sources": scene_ref_sources,
            "actual_char_ids": actual_char_ids
        }
        self.reference_log.append(entry)

    def save_shot_prompt(self, shot_id: int, prompt: str, char_count: int, actual_char_ids: list):
        prompt_file = self.debug_dir / f"shot_{shot_id:02d}_prompt.txt"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(f"Shot {shot_id} Prompt (多人边界测试)\n")
            f.write(f"模型: Gemini 3 Pro Image (Nano Banana Pro)\n")
            f.write(f"时间: {datetime.now().isoformat()}\n")
            f.write(f"实际出场角色数: {char_count}\n")
            f.write(f"实际出场角色: {actual_char_ids}\n")
            f.write(f"Prompt长度: {len(prompt)} chars\n")
            f.write("=" * 60 + "\n\n")
            f.write(prompt)

        self.prompt_log.append({
            "shot_id": shot_id,
            "prompt_length": len(prompt),
            "char_count": char_count,
            "actual_char_ids": actual_char_ids
        })

    def save_all_logs(self):
        with open(self.debug_dir / "reference_images_log.json", 'w', encoding='utf-8') as f:
            json.dump(self.reference_log, f, ensure_ascii=False, indent=2)

        with open(self.debug_dir / "prompt_log.json", 'w', encoding='utf-8') as f:
            json.dump(self.prompt_log, f, ensure_ascii=False, indent=2)


async def run_multichar_test():
    """5人以上边界测试"""

    print("=" * 80)
    print("teststory6.6 - 5人以上场景边界测试")
    print("风格: realistic (写实，最严格测试)")
    print(f"时间: {datetime.now().isoformat()}")
    print("=" * 80)

    # ========================================
    # 0. 清理旧输出目录
    # ========================================
    if OUTPUT_DIR.exists():
        print(f"\n清理旧输出目录: {OUTPUT_DIR}")
        shutil.rmtree(OUTPUT_DIR)

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
    print("1. 生成家庭聚会故事 (6人)")
    print("=" * 60)
    print(f"Idea: {STORY_IDEA.strip()[:100]}...")

    story_gen = StoryGenerator()
    story = await story_gen.generate_story(
        idea=STORY_IDEA,
        style="realistic",
        duration_minutes=2,
        character_count=6  # 要求6个角色
    )

    if not story or not story.get('success'):
        print("故事生成失败")
        return

    with open(OUTPUT_DIR / "story_raw.json", 'w', encoding='utf-8') as f:
        json.dump(story, f, ensure_ascii=False, indent=2)

    story = story.get('data', story)

    with open(OUTPUT_DIR / "story.json", 'w', encoding='utf-8') as f:
        json.dump(story, f, ensure_ascii=False, indent=2)
    print(f"故事生成成功: {story.get('title', 'Untitled')}")

    characters = story.get('characters', [])
    scenes = story.get('scenes', [])
    print(f"   角色数: {len(characters)}")
    print(f"   场景数: {len(scenes)}")

    for char in characters:
        age = char.get('age_appearance', char.get('human', {}).get('age_range', ''))
        print(f"   - {char.get('name')} ({char.get('id')}): {char.get('name_en', '')} - {age}")

    if len(characters) < 5:
        print(f"\n警告: 角色数量不足5人 ({len(characters)}人)")

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

    with open(OUTPUT_DIR / "shots.json", 'w', encoding='utf-8') as f:
        json.dump(shots, f, ensure_ascii=False, indent=2)
    print(f"分镜拆分完成: {len(shots)} shots")

    # Shot角色分布分析
    print("\n   Shot角色分布:")
    char_count_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
    five_plus_shots = []
    six_person_shots = []

    for shot in shots:
        shot_id = shot.get('shot_id')
        visual_desc = shot.get('visual_description', '')
        actual_chars = extract_actual_characters(visual_desc, characters)
        char_count = len(actual_chars)
        print(f"   Shot {shot_id}: {char_count}人 - {actual_chars}")

        if char_count in char_count_distribution:
            char_count_distribution[char_count] += 1
        if char_count >= 5:
            five_plus_shots.append(shot_id)
        if char_count >= 6:
            six_person_shots.append(shot_id)

    print(f"\n   人数分布统计:")
    for count, num in char_count_distribution.items():
        if num > 0:
            print(f"      {count}人shot: {num}个")

    print(f"\n   5人以上shot: {len(five_plus_shots)}个 - {five_plus_shots}")
    print(f"   6人shot: {len(six_person_shots)}个 - {six_person_shots}")

    # ========================================
    # 3. 生成角色参考图 (Flash)
    # ========================================
    print("\n" + "=" * 60)
    print("3. 生成角色参考图 (Gemini Flash)")
    print("=" * 60)

    image_gen = ImageGenerator()
    ref_manager = ReferenceImageManager()

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

        await asyncio.sleep(3.0)

    print(f"\n角色参考图生成完成: {len(char_ref_images)}/{len(characters)}")

    # ========================================
    # 4. 生成场景参考图 (Flash)
    # ========================================
    print("\n" + "=" * 60)
    print("4. 生成场景参考图 (Gemini Flash)")
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
    # 5. 生成Shot图片 (Pro模型)
    # ========================================
    print("\n" + "=" * 60)
    print("5. 生成Shot图片 (Gemini 3 Pro Image)")
    print("=" * 60)

    max_shots = min(12, len(shots))
    generated_count = 0
    boundary_test_results = []

    for i in range(max_shots):
        shot = shots[i]
        shot_id = shot.get('shot_id', i + 1)
        visual_desc = shot.get('visual_description', '')

        # 智能提取实际出场角色
        actual_char_ids = extract_actual_characters(visual_desc, characters)
        if not actual_char_ids:
            actual_char_ids = shot.get('characters_in_scene', [])

        char_count = len(actual_char_ids)
        is_boundary_test = char_count >= 5

        print(f"\n{'='*40}")
        print(f"Shot {shot_id} (Pro模型) {'[边界测试: ' + str(char_count) + '人]' if is_boundary_test else ''}")
        print(f"实际出场角色: {actual_char_ids}")
        print(f"{'='*40}")

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

        debug_logger.save_shot_prompt(shot_id, new_prompt, char_count, actual_char_ids)

        # 准备参考图 - 只传实际出场角色的fullbody
        all_refs = []
        char_ref_sources = []
        scene_ref_sources = []

        for char_id in actual_char_ids:
            if char_id in char_ref_images:
                refs = char_ref_images[char_id]
                if refs.get('fullbody'):
                    all_refs.append(refs['fullbody'])
                    char_ref_sources.append(f"{char_id}_fullbody")

        # 添加场景参考图
        for loc_id, img in scene_ref_images.items():
            all_refs.append(img)
            scene_ref_sources.append(f"{loc_id}")
            break

        char_ref_count = len(char_ref_sources)
        scene_ref_count = len(scene_ref_sources)

        debug_logger.log_reference_images(
            shot_id=shot_id,
            char_refs=all_refs[:char_ref_count],
            scene_refs=all_refs[char_ref_count:],
            char_ref_sources=char_ref_sources,
            scene_ref_sources=scene_ref_sources,
            actual_char_ids=actual_char_ids
        )

        print(f"参考图: {len(all_refs)}张 (角色:{char_ref_count}, 场景:{scene_ref_count})")

        # 警告：Pro模型最多支持14张参考图
        if len(all_refs) > 14:
            print(f"   警告: 参考图数量 ({len(all_refs)}) 超过Pro模型限制 (14张)")
            all_refs = all_refs[:14]

        shot_copy = shot.copy()
        shot_copy['image_prompt'] = new_prompt
        shot_copy['negative_prompt'] = "blurry, low quality, distorted, deformed, bad anatomy, extra limbs, missing limbs, mutated hands, extra fingers, fewer fingers, text, watermark, signature, logo, cropped, out of frame, duplicate, ugly, disfigured, malformed, cartoon, anime, illustration, painting, drawn, 3d render"

        # 使用Pro模型生成
        result = await image_gen.generate_shot_image(
            shot=shot_copy,
            reference_images=all_refs,
            aspect_ratio="16:9",
            use_llm_translation=False,
            use_pro_model=True
        )

        success = result.get('success')
        if success:
            image_path = images_dir / f"shot_{shot_id:02d}.png"
            result['pil_image'].save(str(image_path))
            print(f"生成成功: {image_path.name}")
            generated_count += 1
        else:
            print(f"生成失败: {result.get('error', 'unknown')}")

        # 记录边界测试结果
        if is_boundary_test:
            boundary_test_results.append({
                "shot_id": shot_id,
                "char_count": char_count,
                "actual_char_ids": actual_char_ids,
                "success": success,
                "ref_count": len(all_refs)
            })

        await asyncio.sleep(5.0)

    debug_logger.save_all_logs()

    # ========================================
    # 6. 边界测试结果分析
    # ========================================
    print("\n" + "=" * 60)
    print("边界测试结果分析")
    print("=" * 60)

    if boundary_test_results:
        print(f"\n5人以上shot测试结果:")
        for result in boundary_test_results:
            status = "成功" if result['success'] else "失败"
            print(f"   Shot {result['shot_id']}: {result['char_count']}人 - {status}")
            print(f"      角色: {result['actual_char_ids']}")
            print(f"      参考图: {result['ref_count']}张")

        # 分析边界
        success_by_count = {}
        for result in boundary_test_results:
            count = result['char_count']
            if count not in success_by_count:
                success_by_count[count] = {'success': 0, 'fail': 0}
            if result['success']:
                success_by_count[count]['success'] += 1
            else:
                success_by_count[count]['fail'] += 1

        print(f"\n按人数统计成功率:")
        for count in sorted(success_by_count.keys()):
            stats = success_by_count[count]
            total = stats['success'] + stats['fail']
            rate = stats['success'] / total * 100
            print(f"   {count}人: {stats['success']}/{total} ({rate:.0f}%)")
    else:
        print("   没有5人以上的shot进行测试")

    # ========================================
    # 7. 生成摘要
    # ========================================
    summary_file = OUTPUT_DIR / "summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("teststory6.6 - 5人以上场景边界测试\n")
        f.write(f"风格: realistic (写实，最严格测试)\n")
        f.write(f"测试时间: {datetime.now().isoformat()}\n")
        f.write("=" * 60 + "\n\n")

        f.write("## 验证目标\n")
        f.write("1. Pro模型对5-6人同框的处理能力\n")
        f.write("2. 找出角色数量的上限\n")
        f.write("3. 写实风格下的最严格测试\n\n")

        f.write("## 故事信息\n")
        f.write(f"标题: {story.get('title', 'Untitled')}\n")
        f.write(f"角色数: {len(characters)}\n")
        f.write(f"场景数: {len(scenes)}\n")
        f.write(f"Shot数: {len(shots)}\n\n")

        f.write("## 角色列表 (6人家庭)\n")
        for char in characters:
            char_id = char.get('id')
            char_name = char.get('name')
            name_en = char.get('name_en', '')
            age = char.get('age_appearance', char.get('human', {}).get('age_range', ''))
            f.write(f"- {char_name} ({char_id}): {name_en} - {age}\n")

        f.write("\n## 生成结果\n")
        f.write(f"角色参考图: {len(char_ref_images)}/{len(characters)}\n")
        f.write(f"场景参考图: {len(scene_ref_images)}\n")
        f.write(f"Shot图片: {generated_count}/{max_shots}\n\n")

        f.write("## 人数分布统计\n")
        for count, num in char_count_distribution.items():
            if num > 0:
                f.write(f"- {count}人shot: {num}个\n")

        f.write(f"\n## 边界测试结果\n")
        f.write(f"5人以上shot: {len(five_plus_shots)}个\n")
        f.write(f"6人shot: {len(six_person_shots)}个\n\n")

        if boundary_test_results:
            f.write("详细结果:\n")
            for result in boundary_test_results:
                status = "成功" if result['success'] else "失败"
                f.write(f"- Shot {result['shot_id']}: {result['char_count']}人 - {status}\n")
                f.write(f"  角色: {result['actual_char_ids']}\n")

        f.write("\n## 参考图传递统计\n")
        for entry in debug_logger.reference_log:
            shot_id = entry['shot_id']
            char_count = entry['char_refs_count']
            actual_chars = entry['actual_char_ids']
            f.write(f"Shot {shot_id}: {char_count}张角色图 - {actual_chars}\n")

    print(f"\n保存摘要: {summary_file}")

    print("\n" + "=" * 80)
    print(f"多人边界测试完成！(写实风格 + Pro模型)")
    print(f"  故事: {story.get('title', 'Untitled')}")
    print(f"  角色参考图: {len(char_ref_images)}/{len(characters)}")
    print(f"  场景参考图: {len(scene_ref_images)}")
    print(f"  Shot图片: {generated_count}/{max_shots}")
    print(f"  5人以上shot: {len(five_plus_shots)}个")
    print(f"  6人shot: {len(six_person_shots)}个")
    print("=" * 80)

    # ========================================
    # 8. 验证
    # ========================================
    print("\n" + "=" * 60)
    print("验证结果")
    print("=" * 60)

    # 检查名字重复
    print("\n1. 检查名字重复bug:")
    name_repeat_found = False
    for i in range(max_shots):
        prompt_file = OUTPUT_DIR / "debug" / f"shot_{i+1:02d}_prompt.txt"
        if prompt_file.exists():
            content = prompt_file.read_text()
            for char in characters:
                name_en = char.get('name_en', '')
                if name_en:
                    patterns = [f"{name_en} ({name_en})", f"{name_en} {name_en}"]
                    for pattern in patterns:
                        if pattern in content:
                            print(f"   Shot {i+1}: 发现重复 '{pattern}'")
                            name_repeat_found = True
    if not name_repeat_found:
        print("   没有发现名字重复问题")

    # 检查shot类型分布
    print("\n2. Shot类型分布:")
    for count in [1, 2, 3, 4, 5, 6]:
        num = sum(1 for e in debug_logger.reference_log if e['char_refs_count'] == count)
        if num > 0:
            print(f"   {count}人shot: {num}个")

    # 验收标准
    print("\n3. 验收标准:")
    five_count = len([e for e in debug_logger.reference_log if e['char_refs_count'] >= 5])
    six_count = len([e for e in debug_logger.reference_log if e['char_refs_count'] >= 6])

    if five_count >= 2:
        print(f"   [PASS] 5人以上shot >= 2个 ({five_count}个)")
    else:
        print(f"   [FAIL] 5人以上shot不足2个 ({five_count}个)")

    if six_count >= 1:
        print(f"   [PASS] 6人shot >= 1个 ({six_count}个)")
    else:
        print(f"   [WARN] 6人shot不足1个 ({six_count}个)")

    print(f"\n输出目录: {OUTPUT_DIR}")
    print("\n请人工检查:")
    print("  1. 5人以上场景中每个角色是否可识别")
    print("  2. 角色是否有混淆（服装/面部特征）")
    print("  3. 记录从哪个人数开始出现混淆")


if __name__ == "__main__":
    asyncio.run(run_multichar_test())
