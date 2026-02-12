"""
测试故事5：深夜便利店

完整流程测试：
1. 生成故事 (story.json, story.md)
2. 生成角色设定表 (character_sheet.md)
3. 生成shots分镜 (shots.json)
4. 生成TTS音频 (narration.mp3)
5. 提取Whisper时间戳 (whisper_timestamps.json)
6. 执行音画对齐 (timeline.json, alignment.md)
7. 生成所有shot图片 (images/)
8. 生成图片日志 (images_log.json)
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.story_generator import StoryGenerator
from app.services.storyboard_service import StoryboardService
from app.services.tts_service import TTSService
from app.services.whisper_service import WhisperService
from app.services.alignment_service import AlignmentService
from app.services.image_generator import ImageGenerator
from app.services.reference_image_manager import ReferenceImageManager
from app.services.character_prompt_builder import CharacterPromptBuilder
from app.models.style_config import ProjectStyleConfig, StyleConfigBuilder


# 测试配置
OUTPUT_DIR = "test_output/manualtest/teststory5_convenience_store"
STORY_IDEA = """深夜的便利店，一个失眠的程序员、一个刚下班的护士、一个神秘的老人，三个陌生人因为一场突如其来的停电被困在一起。在黑暗中，他们开始分享各自的秘密，却发现彼此的人生有着意想不到的交集。"""

STORY_REQUIREMENTS = """
## 角色要求
1. 程序员（男，28岁）- 主角视角，失眠，疲惫但眼神锐利，穿着休闲卫衣
2. 护士（女，32岁）- 疲惫但温暖，穿着护士服，有黑眼圈但笑容温和
3. 神秘老人（男，70岁）- 有故事的人，穿着朴素但气质不凡，银白头发，深邃眼神

## 情节要求
- 开头：便利店日常，三人各自购物
- 中段：突然停电，被困
- 小高潮：老人说出一句话，暗示他认识其中一个人（悬念，留到后续章节揭晓）
- 结尾：灯亮了，但三人的关系已经不同

## 章节信息
- 本次只生成第1章（共6章）
- 时长控制在3分钟以内

## 角色数据格式要求
每个角色必须包含完整的 human 字段，格式如下：
{
  "id": "char_xxx",
  "name": "角色名",
  "character_type": "human",
  "role": "角色定位",
  "personality": "性格描述",
  "human": {
    "age_stage": "young_adult/middle_aged/elderly",
    "gender": "male/female",
    "skin_tone": "肤色描述",
    "height": "身高描述",
    "build": "体型描述",
    "hair_color": "发色",
    "hair_style": "发型",
    "hair_length": "发长",
    "eye_color": "眼睛颜色",
    "eye_shape": "眼型",
    "face_shape": "脸型",
    "nose": "鼻子描述",
    "mouth": "嘴巴描述",
    "distinctive_features": "独特特征",
    "clothing_style": "服装风格",
    "clothing_colors": "服装颜色",
    "accessories": "配饰",
    "default_expression": "默认表情",
    "special_notes": "特殊说明"
  }
}
"""


async def step1_generate_story():
    """步骤1: 生成故事"""
    print("\n" + "="*60)
    print("步骤 1: 生成故事")
    print("="*60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    generator = StoryGenerator()

    # 生成故事 - 将角色要求合并到idea中
    full_idea = f"{STORY_IDEA}\n\n{STORY_REQUIREMENTS}"
    result = await generator.generate_story(
        idea=full_idea,
        style="realistic",
        duration_minutes=3,
        character_count=3,
        language="zh-CN",
        chapter_number=1,
        total_chapters=6
    )

    if not result.get('success'):
        print(f"❌ 故事生成失败: {result.get('error')}")
        return None

    story = result.get('data', result.get('story', result))

    # 保存 story.json
    story_path = os.path.join(OUTPUT_DIR, "story.json")
    with open(story_path, 'w', encoding='utf-8') as f:
        json.dump(story, f, ensure_ascii=False, indent=2)
    print(f"✅ story.json 已保存")

    # 保存 story.md
    story_md_path = os.path.join(OUTPUT_DIR, "story.md")
    with open(story_md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {story.get('title', '深夜便利店')}\n\n")
        f.write(f"**风格**: {story.get('style', 'realistic')}\n\n")
        f.write(f"## 故事简介\n{story.get('summary', '')}\n\n")
        f.write(f"## 角色\n")
        for char in story.get('characters', []):
            f.write(f"- **{char.get('name')}**: {char.get('role', '')}\n")
        f.write(f"\n## 场景\n")
        for i, scene in enumerate(story.get('scenes', []), 1):
            f.write(f"\n### 场景 {i}: {scene.get('title', '')}\n")
            f.write(f"{scene.get('narration', '')}\n")
    print(f"✅ story.md 已保存")

    # 生成角色设定表
    character_sheet_path = os.path.join(OUTPUT_DIR, "character_sheet.md")
    with open(character_sheet_path, 'w', encoding='utf-8') as f:
        f.write("# 角色设定表\n\n")
        for char in story.get('characters', []):
            f.write(f"## {char.get('name')}\n\n")
            f.write(f"- **ID**: {char.get('id')}\n")
            f.write(f"- **角色类型**: {char.get('character_type', 'unknown')}\n")
            f.write(f"- **角色定位**: {char.get('role', '')}\n")
            f.write(f"- **性格**: {char.get('personality', '')}\n")

            # 人类角色详细外观
            human = char.get('human', {})
            if human:
                f.write(f"\n### 外观详情\n")
                f.write(f"- **年龄阶段**: {human.get('age_stage', '')}\n")
                f.write(f"- **性别**: {human.get('gender', '')}\n")
                f.write(f"- **肤色**: {human.get('skin_tone', '')}\n")
                f.write(f"- **身高**: {human.get('height', '')}\n")
                f.write(f"- **体型**: {human.get('build', '')}\n")
                f.write(f"- **发色**: {human.get('hair_color', '')}\n")
                f.write(f"- **发型**: {human.get('hair_style', '')}\n")
                f.write(f"- **眼色**: {human.get('eye_color', '')}\n")
                f.write(f"- **眼型**: {human.get('eye_shape', '')}\n")
                f.write(f"- **脸型**: {human.get('face_shape', '')}\n")
                f.write(f"- **服装风格**: {human.get('clothing_style', '')}\n")
                f.write(f"- **服装颜色**: {human.get('clothing_colors', '')}\n")
                f.write(f"- **配饰**: {human.get('accessories', '')}\n")
                f.write(f"- **独特特征**: {human.get('distinctive_features', '')}\n")
                f.write(f"- **默认表情**: {human.get('default_expression', '')}\n")
            f.write("\n---\n\n")
    print(f"✅ character_sheet.md 已保存")

    print(f"\n📊 故事统计:")
    print(f"   - 标题: {story.get('title')}")
    print(f"   - 场景数: {len(story.get('scenes', []))}")
    print(f"   - 角色数: {len(story.get('characters', []))}")

    return story


async def step2_generate_shots(story):
    """步骤2: 生成分镜"""
    print("\n" + "="*60)
    print("步骤 2: 生成分镜")
    print("="*60)

    service = StoryboardService()

    # 使用带拆分的分镜生成
    shots = await service.generate_storyboard_with_splitting(
        scenes=story.get('scenes', []),
        characters=story.get('characters', []),
        style_preset="realistic",
        aspect_ratio="16:9"
    )

    # 保存 shots.json
    shots_path = os.path.join(OUTPUT_DIR, "shots.json")
    with open(shots_path, 'w', encoding='utf-8') as f:
        json.dump(shots, f, ensure_ascii=False, indent=2)
    print(f"✅ shots.json 已保存")

    print(f"\n📊 分镜统计:")
    print(f"   - 总Shot数: {len(shots)}")

    return shots


async def step3_generate_tts(story):
    """步骤3: 生成TTS音频"""
    print("\n" + "="*60)
    print("步骤 3: 生成TTS音频")
    print("="*60)

    tts = TTSService()

    # 拼接所有场景的旁白
    narration_parts = []
    for scene in story.get('scenes', []):
        narration = scene.get('narration', '')
        if narration:
            narration_parts.append(narration)

    full_narration = '\n\n'.join(narration_parts)

    # 保存旁白文本
    narration_text_path = os.path.join(OUTPUT_DIR, "narration.txt")
    with open(narration_text_path, 'w', encoding='utf-8') as f:
        f.write(full_narration)
    print(f"✅ narration.txt 已保存 ({len(full_narration)} 字符)")

    # 生成音频 - 使用 synthesize_chapter 方法
    audio_path = os.path.join(OUTPUT_DIR, "narration.mp3")
    result = await tts.synthesize_chapter(
        narrations=narration_parts,
        voice_preset="zh_male_wennuan",  # 温暖阿虎，适合故事讲述
        pause_duration_ms=800
    )

    if not result.get('success'):
        print(f"❌ TTS生成失败: {result.get('error')}")
        await tts.close()
        return None

    # 保存音频文件
    audio_data = result.get('audio_data')
    if audio_data:
        with open(audio_path, 'wb') as f:
            f.write(audio_data)
        print(f"✅ narration.mp3 已保存")
    else:
        print(f"❌ TTS返回空音频数据")
        await tts.close()
        return None

    await tts.close()
    return audio_path, full_narration


async def step4_whisper_timestamps(audio_path):
    """步骤4: 提取Whisper时间戳"""
    print("\n" + "="*60)
    print("步骤 4: 提取Whisper时间戳")
    print("="*60)

    whisper = WhisperService()

    result = await whisper.transcribe_with_timestamps(audio_path)

    if not result.get('success'):
        print(f"❌ Whisper转录失败: {result.get('error')}")
        return None

    timestamps = result.get('timestamps', result)  # 兼容不同返回格式

    # 保存时间戳
    timestamps_path = os.path.join(OUTPUT_DIR, "whisper_timestamps.json")
    with open(timestamps_path, 'w', encoding='utf-8') as f:
        json.dump(timestamps, f, ensure_ascii=False, indent=2)
    print(f"✅ whisper_timestamps.json 已保存")

    # 获取音频时长
    audio_duration = result.get('duration', timestamps.get('duration', 0))
    segments = timestamps.get('segments', [])

    print(f"\n📊 音频统计:")
    print(f"   - 音频时长: {audio_duration:.2f}秒 ({audio_duration/60:.2f}分钟)")
    print(f"   - 词段数: {len(segments)}")

    return timestamps, audio_duration


async def step5_align_audio_visual(story, shots, timestamps, audio_duration, full_narration):
    """步骤5: 音画对齐"""
    print("\n" + "="*60)
    print("步骤 5: 音画对齐")
    print("="*60)

    aligner = AlignmentService()

    # 准备图片数据（此时还没生成图片，使用shot的visual_description）
    images = []
    for shot in shots:
        images.append({
            'scene_id': shot.get('shot_id', shot.get('original_scene_id')),
            'visual_description': shot.get('visual_description', shot.get('image_prompt', '')),
            'narration_segment': shot.get('narration_segment', '')
        })

    segments = timestamps.get('segments', [])

    # 执行对齐
    timeline = await aligner.align_images_to_audio(
        images=images,
        segments=segments,
        full_text=full_narration,
        audio_duration=audio_duration,
        use_visual_matching=False  # 还没有图片，使用文本匹配
    )

    # 保存 timeline.json
    timeline_path = os.path.join(OUTPUT_DIR, "timeline.json")
    with open(timeline_path, 'w', encoding='utf-8') as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    print(f"✅ timeline.json 已保存")

    # 生成 alignment.md 可视化报告
    alignment_md_path = os.path.join(OUTPUT_DIR, "alignment.md")
    with open(alignment_md_path, 'w', encoding='utf-8') as f:
        f.write("# 音画对齐报告\n\n")
        f.write(f"**音频总时长**: {audio_duration:.2f}秒\n\n")
        f.write("| Shot | 开始时间 | 结束时间 | 时长 | 场景 |\n")
        f.write("|------|----------|----------|------|------|\n")
        for item in timeline:
            start = item.get('start_time', 0)
            end = item.get('end_time', 0)
            duration = end - start
            f.write(f"| {item.get('scene_id', '')} | {start:.2f}s | {end:.2f}s | {duration:.2f}s | - |\n")
    print(f"✅ alignment.md 已保存")

    # 统计
    total_shots = len(timeline)
    avg_duration = audio_duration / total_shots if total_shots > 0 else 0
    print(f"\n📊 对齐统计:")
    print(f"   - 总Shot数: {total_shots}")
    print(f"   - 平均Shot时长: {avg_duration:.2f}秒")

    return timeline, avg_duration


async def step6_generate_images(story, shots, timeline):
    """步骤6: 生成所有shot图片"""
    print("\n" + "="*60)
    print("步骤 6: 生成Shot图片")
    print("="*60)

    # 创建图片目录
    images_dir = os.path.join(OUTPUT_DIR, "images")
    os.makedirs(images_dir, exist_ok=True)

    # 初始化服务
    image_gen = ImageGenerator()
    ref_manager = ReferenceImageManager()
    char_builder = CharacterPromptBuilder()

    # 构建项目风格 - 使用 build_from_story 方法
    style_builder = StyleConfigBuilder()
    project_style = style_builder.build_from_story(story)

    # 构建角色映射
    characters = {char['id']: char for char in story.get('characters', [])}

    # 先生成角色参考图
    print("\n生成角色参考图...")
    char_refs_dir = os.path.join(OUTPUT_DIR, "character_refs")
    os.makedirs(char_refs_dir, exist_ok=True)

    char_ref_prompts = {}
    for char in story.get('characters', []):
        char_id = char['id']
        char_name = char['name']
        print(f"  生成 {char_name} 参考图...")

        result = await ref_manager.generate_character_reference(
            character=char,
            project_style=project_style,
            image_generator=image_gen
        )

        if result.get('success') and result.get('pil_image'):
            ref_path = os.path.join(char_refs_dir, f"{char_id}_reference.png")
            result['pil_image'].save(ref_path)
            print(f"    ✅ {char_name} 参考图已保存")

            # 记录prompt
            char_ref_prompts[char_name] = {
                'char_id': char_id,
                'char_type': char.get('character_type', 'human'),
                'reference_prompt': ref_manager._build_reference_prompt(
                    char,
                    ref_manager._get_character_type(char),
                    project_style
                ),
                'negative_prompt': ref_manager._get_negative_prompt(
                    ref_manager._get_character_type(char)
                )
            }
        else:
            print(f"    ❌ {char_name} 参考图生成失败: {result.get('error')}")

        await asyncio.sleep(2)  # API限速

    # 保存角色参考图prompt
    char_ref_prompts_path = os.path.join(OUTPUT_DIR, "character_ref_prompts.json")
    with open(char_ref_prompts_path, 'w', encoding='utf-8') as f:
        json.dump(char_ref_prompts, f, ensure_ascii=False, indent=2)

    # 生成shot图片
    print("\n生成Shot图片...")
    images_log = []
    generated_count = 0

    for i, shot in enumerate(shots):
        shot_id = f"shot_{shot.get('shot_id', i+1):02d}"
        print(f"\n  [{i+1}/{len(shots)}] 生成 {shot_id}...")

        # 获取shot中的角色
        shot_chars = shot.get('characters_in_scene', [])
        # 从角色名称查找角色ID
        char_ids = []
        for char_name in shot_chars:
            for cid, cdata in characters.items():
                if cdata.get('name') == char_name:
                    char_ids.append(cid)
                    break

        char_descriptions = []
        for char_id in char_ids:
            if char_id in characters:
                char = characters[char_id]
                char_desc = char_builder.build_character_prompt(char)
                char_descriptions.append(f"{char['name']}: {char_desc}")

        # 组合prompt
        scene_desc = shot.get('visual_description', shot.get('image_prompt', ''))

        full_prompt = f"""
{scene_desc}
Characters in scene: {', '.join(char_descriptions) if char_descriptions else 'no specific characters'}
Setting: late night convenience store, fluorescent lighting
{project_style.style_suffix}
realistic photography style, cinematic composition, dramatic lighting
"""

        negative_prompt = "blurry, low quality, cartoon, anime, text, watermark, signature, animal features, furry"

        # 获取角色参考图
        ref_images = ref_manager.get_references_for_scene(char_ids)

        # 生成图片
        result = await image_gen.generate_image(
            prompt=full_prompt.strip(),
            negative_prompt=negative_prompt,
            aspect_ratio="16:9",
            reference_images=ref_images if ref_images else None
        )

        # 记录日志
        log_entry = {
            'shot_id': shot_id,
            'original_scene_id': shot.get('original_scene_id', ''),
            'prompt': full_prompt.strip(),
            'negative_prompt': negative_prompt,
            'characters': shot_chars,
            'success': result.get('success', False),
            'timestamp': datetime.now().isoformat()
        }

        if result.get('success') and result.get('pil_image'):
            image_path = os.path.join(images_dir, f"{shot_id}.png")
            result['pil_image'].save(image_path)
            log_entry['image_path'] = image_path
            generated_count += 1
            print(f"    ✅ 已保存")
        else:
            log_entry['error'] = result.get('error', 'Unknown error')
            print(f"    ❌ 失败: {result.get('error')}")

        images_log.append(log_entry)

        # API限速
        await asyncio.sleep(3)

    # 保存图片日志
    images_log_path = os.path.join(OUTPUT_DIR, "images_log.json")
    with open(images_log_path, 'w', encoding='utf-8') as f:
        json.dump(images_log, f, ensure_ascii=False, indent=2)
    print(f"\n✅ images_log.json 已保存")

    # 保存prompts日志
    prompts_log_path = os.path.join(OUTPUT_DIR, "prompts_log.json")
    with open(prompts_log_path, 'w', encoding='utf-8') as f:
        prompts_data = [{
            'shot_id': log['shot_id'],
            'prompt': log['prompt'],
            'negative_prompt': log['negative_prompt']
        } for log in images_log]
        json.dump(prompts_data, f, ensure_ascii=False, indent=2)
    print(f"✅ prompts_log.json 已保存")

    return generated_count, images_log


async def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("深夜便利店 - 完整流程测试")
    print("="*60)
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 步骤1: 生成故事
        story = await step1_generate_story()
        if not story:
            return

        # 步骤2: 生成分镜
        shots = await step2_generate_shots(story)
        if not shots:
            return

        # 步骤3: 生成TTS音频
        result = await step3_generate_tts(story)
        if not result:
            return
        audio_path, full_narration = result

        # 步骤4: 提取Whisper时间戳
        result = await step4_whisper_timestamps(audio_path)
        if not result:
            return
        timestamps, audio_duration = result

        # 步骤5: 音画对齐
        result = await step5_align_audio_visual(story, shots, timestamps, audio_duration, full_narration)
        if not result:
            return
        timeline, avg_shot_duration = result

        # 步骤6: 生成图片
        generated_count, images_log = await step6_generate_images(story, shots, timeline)

        # 最终报告
        print("\n" + "="*60)
        print("测试完成 - 最终报告")
        print("="*60)

        print(f"\n📊 故事统计:")
        print(f"   - 场景数: {len(story.get('scenes', []))}")
        print(f"   - Shot数: {len(shots)}")

        print(f"\n🎵 音频统计:")
        print(f"   - 音频时长: {audio_duration:.2f}秒 ({audio_duration/60:.2f}分钟)")
        print(f"   - 平均Shot时长: {avg_shot_duration:.2f}秒")

        print(f"\n👥 角色描述:")
        for char in story.get('characters', []):
            char_type = char.get('character_type', 'unknown')
            print(f"\n   【{char.get('name')}】")
            print(f"   - 类型: {char_type}")
            print(f"   - 角色: {char.get('role', '')}")
            human = char.get('human', {})
            if human:
                print(f"   - 年龄: {human.get('age_stage', '')}")
                print(f"   - 性别: {human.get('gender', '')}")
                print(f"   - 外观: {human.get('hair_color', '')}头发, {human.get('eye_color', '')}眼睛")
                print(f"   - 服装: {human.get('clothing_style', '')}")
                print(f"   - 特征: {human.get('distinctive_features', '')}")

        print(f"\n🖼️  图片统计:")
        print(f"   - 生成成功: {generated_count}/{len(shots)}")

        print(f"\n📁 文件路径:")
        print(f"   - 故事: {OUTPUT_DIR}/story.json")
        print(f"   - 分镜: {OUTPUT_DIR}/shots.json")
        print(f"   - 音频: {OUTPUT_DIR}/narration.mp3")
        print(f"   - 时间戳: {OUTPUT_DIR}/whisper_timestamps.json")
        print(f"   - 时间线: {OUTPUT_DIR}/timeline.json")
        print(f"   - 图片目录: {OUTPUT_DIR}/images/")
        print(f"   - 角色参考图: {OUTPUT_DIR}/character_refs/")
        print(f"   - 图片日志: {OUTPUT_DIR}/images_log.json")

        print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
