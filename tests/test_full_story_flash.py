"""
完整故事章节测试 - 全部使用 gemini-2.5-flash-image

测试目标：验证修复后的角色一致性在完整流程下的表现

故事设定：大学毕业十年后的同学聚会
- 3个人类角色
- 写实风格
- 3分钟以内
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.story_generator import StoryGenerator
from app.services.storyboard_service import StoryboardService
from app.services.image_generator import ImageGenerator
from app.services.reference_image_manager import ReferenceImageManager
from app.services.scene_reference_manager import SceneReferenceManager
from app.services.tts_service import TTSService
from app.services.whisper_service import WhisperService
from app.services.alignment_service import AlignmentService
from app.services.character_prompt_builder import CharacterPromptBuilder
from app.services.style_enforcer import StyleEnforcer
from app.models.style_config import StyleConfigBuilder, ProjectStyleConfig


OUTPUT_DIR = "test_output/manualtest/teststory6_enhanced"


async def step1_generate_story():
    """步骤1：生成故事"""
    print("\n" + "=" * 70)
    print("步骤1: 生成故事 (story.json, story.md)")
    print("=" * 70)

    story_gen = StoryGenerator()

    idea = """大学毕业十年后的同学聚会上，三个曾经最好的朋友重逢。
学生会主席如今在送外卖，当年的学渣成了上市公司CEO，而那个默默无闻的女生，竟然带来了一个让所有人震惊的秘密。

情节要求：
- 开头：酒吧包间，老同学们陆续到场
- 中段：三人各自近况，陈浩送外卖被调侃，王磊的身份被意外揭穿
- 小高潮：林小雨拿出一张照片，暗示和其中一个人有隐藏的过去（悬念留到后续章节）
- 结尾：气氛微妙，三人约定明天再聚

角色设定：
1. 陈浩（男，32岁）— 曾经的学生会主席，现在的外卖骑手，有点落魄但眼神依然有光，穿着外卖骑手的蓝色工作服
2. 王磊（男，32岁）— 曾经的学渣，现在的CEO，故意穿着低调的休闲装（深灰色polo衫），戴着低调的手表
3. 林小雨（女，32岁）— 当年默默无闻的女生，现在气质优雅，穿着简约的白色衬衫和黑色西裤，有个惊人的秘密"""

    result = await story_gen.generate_story(
        idea=idea,
        style="realistic",
        duration_minutes=3,
        character_count=3,
        chapter_number=1,
        total_chapters=6,
        language="zh-CN"
    )

    # generate_story 返回格式可能是 {'success': True, 'data': {...}} 或直接是故事数据
    if isinstance(result, dict):
        if result.get('success') and result.get('data'):
            story_data = result['data']
        elif result.get('scenes'):
            story_data = result
        else:
            print(f"❌ 故事生成失败: {result}")
            return None
    else:
        print(f"❌ 故事生成返回格式错误: {type(result)}")
        return None

    if story_data and story_data.get('scenes'):
        # 保存 story.json
        story_path = os.path.join(OUTPUT_DIR, "story.json")
        with open(story_path, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)
        print(f"✅ story.json 已保存: {story_path}")

        # 生成 story.md
        md_content = f"# {story_data.get('title', '未命名')}\n\n"
        md_content += f"**简介**: {story_data.get('synopsis', '')}\n\n"
        md_content += "## 角色\n\n"
        for char in story_data.get('characters', []):
            md_content += f"- **{char.get('name')}** ({char.get('name_en', '')}): {char.get('role', '')}\n"
        md_content += "\n## 场景\n\n"
        for scene in story_data.get('scenes', []):
            md_content += f"### 场景 {scene.get('scene_id')}\n"
            md_content += f"**地点**: {scene.get('location', '')}\n"
            md_content += f"**旁白**: {scene.get('narration', '')}\n\n"

        md_path = os.path.join(OUTPUT_DIR, "story.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"✅ story.md 已保存: {md_path}")

        # 输出统计
        scenes = story_data.get('scenes', [])
        characters = story_data.get('characters', [])
        print(f"\n📊 故事统计:")
        print(f"   - 场景数: {len(scenes)}")
        print(f"   - 角色数: {len(characters)}")

        return story_data
    else:
        print(f"❌ 故事生成失败: {story_data}")
        return None


async def step2_generate_character_refs(story_data):
    """步骤2：生成角色参考图"""
    print("\n" + "=" * 70)
    print("步骤2: 生成角色参考图（肖像+全身，全部使用Flash）")
    print("=" * 70)

    refs_dir = os.path.join(OUTPUT_DIR, "character_refs")
    os.makedirs(refs_dir, exist_ok=True)

    # 构建风格配置
    style_builder = StyleConfigBuilder()
    project_style = style_builder.build_from_story(story_data)
    # 强制使用 realistic
    project_style.style_preset = "realistic"
    project_style.style_suffix = style_builder.build_style_suffix(project_style)

    print(f"风格: {project_style.style_preset}")

    # 初始化服务
    image_gen = ImageGenerator()
    ref_manager = ReferenceImageManager()

    characters = story_data.get('characters', [])
    all_results = {}

    for i, char in enumerate(characters):
        char_name = char.get('name', f'角色{i+1}')
        char_id = char.get('id', f'char_{i+1:03d}')
        print(f"\n[{i+1}/{len(characters)}] 生成 {char_name} 的参考图...")

        # 输出角色完整描述
        print(f"   角色描述:")
        if char.get('human'):
            h = char['human']
            print(f"     - 年龄: {h.get('age_range', 'N/A')}")
            print(f"     - 性别: {h.get('gender', 'N/A')}")
            print(f"     - 发型: {h.get('hair_color', '')} {h.get('hair_style', '')}")
            print(f"     - 服装: {h.get('clothing_description', 'N/A')}")
            print(f"     - 特征: {h.get('distinctive_features', [])}")

        # 生成多参考图（肖像+全身）
        results = await ref_manager.generate_character_multi_refs(
            character=char,
            project_style=project_style,
            image_generator=image_gen,
            delay=3.0
        )

        # 保存结果
        for ref_type, result in results.items():
            if result.get('success') and result.get('pil_image'):
                ref_path = os.path.join(refs_dir, f"{char_id}_{ref_type}.png")
                result['pil_image'].save(ref_path)
                print(f"   ✅ {ref_type} 已保存: {ref_path}")
            else:
                print(f"   ❌ {ref_type} 生成失败: {result.get('error')}")

        all_results[char_id] = results

        # 等待避免速率限制
        if i < len(characters) - 1:
            await asyncio.sleep(3)

    return ref_manager, project_style


async def step2b_generate_scene_refs(story_data, project_style):
    """步骤2.5：生成场景参考图（确保环境一致性）"""
    print("\n" + "=" * 70)
    print("步骤2.5: 生成场景参考图（确保环境一致性）")
    print("=" * 70)

    scene_refs_dir = os.path.join(OUTPUT_DIR, "scene_refs")
    os.makedirs(scene_refs_dir, exist_ok=True)

    image_gen = ImageGenerator()
    scene_ref_manager = SceneReferenceManager()

    scenes = story_data.get('scenes', [])

    # 生成所有场景参考图（使用链式生成，确保场景一致性）
    results = await scene_ref_manager.generate_all_scene_references_chained(
        scenes=scenes,
        project_style=project_style,
        image_generator=image_gen,
        delay=3.0
    )

    # 保存场景参考图
    saved_paths = scene_ref_manager.save_all_references(scene_refs_dir)

    print(f"\n📊 场景参考图统计:")
    print(f"   - 独特场景数: {len(saved_paths)}")
    for loc_id, views in saved_paths.items():
        for view_type, path in views.items():
            print(f"   - {loc_id} ({view_type}): {path}")

    return scene_ref_manager


async def step3_generate_shots(story_data):
    """步骤3：生成分镜"""
    print("\n" + "=" * 70)
    print("步骤3: 生成分镜 (shots.json)")
    print("=" * 70)

    storyboard = StoryboardService()

    # 获取故事数据
    scenes = story_data.get('scenes', [])
    characters = story_data.get('characters', [])
    style_preset = story_data.get('style', {}).get('style_preset', 'realistic')

    # 使用正确的方法名
    shots = await storyboard.generate_storyboard_with_splitting(
        scenes=scenes,
        characters=characters,
        style_preset=style_preset,
        aspect_ratio="16:9"
    )

    # 保存 shots.json
    shots_path = os.path.join(OUTPUT_DIR, "shots.json")
    with open(shots_path, 'w', encoding='utf-8') as f:
        json.dump(shots, f, ensure_ascii=False, indent=2)
    print(f"✅ shots.json 已保存: {shots_path}")

    print(f"\n📊 分镜统计:")
    print(f"   - 总镜头数: {len(shots)}")

    # 统计每个场景的镜头数
    scene_shots = {}
    for shot in shots:
        scene_id = shot.get('original_scene_id', shot.get('scene_id', 0))
        scene_shots[scene_id] = scene_shots.get(scene_id, 0) + 1

    for scene_id, count in sorted(scene_shots.items()):
        print(f"   - 场景{scene_id}: {count}个镜头")

    return shots


async def step4_generate_tts(story_data, shots):
    """步骤4：生成TTS音频"""
    print("\n" + "=" * 70)
    print("步骤4: 生成TTS音频 (narration.mp3)")
    print("=" * 70)

    tts = TTSService()

    # 合并所有旁白
    narrations = []
    for shot in shots:
        narration = shot.get('narration_segment', '') or shot.get('narration', '')
        if narration:
            narrations.append(narration)

    print(f"旁白段落数: {len(narrations)}")
    total_chars = sum(len(n) for n in narrations)
    print(f"旁白总字数: {total_chars}")

    # 使用 synthesize_chapter 方法生成音频
    result = await tts.synthesize_chapter(
        narrations=narrations,
        voice_preset="zh_female_shuangkuai",
        speed_ratio=0.95
    )

    if result.get('success'):
        # 保存音频文件
        audio_path = os.path.join(OUTPUT_DIR, "narration.mp3")
        with open(audio_path, 'wb') as f:
            f.write(result['audio_data'])

        duration = result.get('duration_seconds', 0)
        print(f"✅ narration.mp3 已保存: {audio_path}")
        print(f"   音频时长: {duration:.1f}秒")
        print(f"   文件大小: {len(result['audio_data']):,} bytes")
        return audio_path, duration
    else:
        print(f"❌ TTS生成失败: {result.get('error')}")
        return None, 0


async def step5_whisper_timestamps(audio_path):
    """步骤5：提取Whisper时间戳"""
    print("\n" + "=" * 70)
    print("步骤5: 提取Whisper时间戳 (whisper_timestamps.json)")
    print("=" * 70)

    whisper = WhisperService()
    result = await whisper.transcribe_with_timestamps(
        audio_path=audio_path,
        granularity="both"
    )

    if result.get('success'):
        timestamps_path = os.path.join(OUTPUT_DIR, "whisper_timestamps.json")
        with open(timestamps_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"✅ whisper_timestamps.json 已保存: {timestamps_path}")
        print(f"   音频时长: {result.get('duration', 0):.2f}秒")
        print(f"   识别段落数: {len(result.get('segments', []))}")
        return result
    else:
        print(f"❌ Whisper识别失败: {result.get('error')}")
        return None


async def step6_timeline_alignment(shots, whisper_result):
    """步骤6：音画对齐"""
    print("\n" + "=" * 70)
    print("步骤6: 音画对齐 (timeline.json)")
    print("=" * 70)

    if not whisper_result:
        print("❌ 没有Whisper结果，跳过对齐")
        return None

    alignment_service = AlignmentService()

    segments = whisper_result.get('segments', [])
    full_text = whisper_result.get('text', '')
    audio_duration = whisper_result.get('duration', 0)

    print(f"正在进行音画对齐...")
    print(f"   Shots数量: {len(shots)}")
    print(f"   音频段落数: {len(segments)}")
    print(f"   音频总时长: {audio_duration:.2f}秒")

    timeline = await alignment_service.align_shots_to_audio(
        shots=shots,
        segments=segments,
        full_text=full_text,
        audio_duration=audio_duration
    )

    if timeline:
        timeline_path = os.path.join(OUTPUT_DIR, "timeline.json")
        with open(timeline_path, 'w', encoding='utf-8') as f:
            json.dump(timeline, f, ensure_ascii=False, indent=2)
        print(f"✅ timeline.json 已保存: {timeline_path}")
        print(f"   对齐项数: {len(timeline)}")

        # 打印时间线摘要
        for item in timeline[:5]:
            print(f"   Shot {item.get('shot_id')}: {item.get('start_time', 0):.2f}s - {item.get('end_time', 0):.2f}s")
        if len(timeline) > 5:
            print(f"   ... 以及 {len(timeline) - 5} 个其他shots")
    else:
        print("⚠️ 对齐失败，尝试使用快速对齐...")
        timeline = await alignment_service.quick_align(
            scene_count=len(shots),
            segments=segments,
            audio_duration=audio_duration
        )
        if timeline:
            timeline_path = os.path.join(OUTPUT_DIR, "timeline.json")
            with open(timeline_path, 'w', encoding='utf-8') as f:
                json.dump(timeline, f, ensure_ascii=False, indent=2)
            print(f"✅ timeline.json (快速对齐) 已保存: {timeline_path}")

    return timeline


async def step7_generate_scene_images(story_data, timeline, ref_manager, scene_ref_manager, project_style, max_images=10):
    """步骤7：生成场景图（使用timeline精确对齐）"""
    print("\n" + "=" * 70)
    print(f"步骤7: 生成场景图（前{max_images}张，使用timeline精确对齐）")
    print("=" * 70)

    images_dir = os.path.join(OUTPUT_DIR, "images")
    os.makedirs(images_dir, exist_ok=True)

    image_gen = ImageGenerator()

    # 构建角色ID到角色数据的映射
    characters = story_data.get('characters', [])
    char_map = {}
    for char in characters:
        char_id = char.get('id')
        if char_id:
            char_map[char_id] = char

    # 构建场景ID到场景数据的映射
    scenes = story_data.get('scenes', [])
    scene_map = {}
    for scene in scenes:
        scene_id = scene.get('scene_id')
        if scene_id:
            scene_map[scene_id] = scene

    style_name = project_style.style_preset
    generated_count = 0

    for i, shot in enumerate(timeline[:max_images]):
        shot_id = shot.get('shot_id', i + 1)
        scene_id = shot.get('original_scene_id', 1)
        start_time = shot.get('start_time', 0)
        end_time = shot.get('end_time', 0)
        duration = shot.get('duration', 0)

        print(f"\n[{i+1}/{min(len(timeline), max_images)}] 生成场景图 shot_{shot_id:02d}...")
        print(f"   ⏱️  时间轴: {start_time:.2f}s - {end_time:.2f}s (时长: {duration:.2f}s)")

        # 从原始scene获取characters_in_scene
        original_scene = scene_map.get(scene_id, {})
        chars_in_scene = original_scene.get('characters_in_scene', [])

        # 如果场景没有角色列表，从visual_description中推断
        if not chars_in_scene:
            visual_desc = shot.get('visual_description', '') or shot.get('image_prompt', '')
            narration = shot.get('narration_segment', '')
            combined_text = f"{visual_desc} {narration}"

            for char in characters:
                char_name = char.get('name', '')
                char_name_en = char.get('name_en', '')
                char_id = char.get('id')
                if char_id and (char_name in combined_text or char_name_en in combined_text):
                    if char_id not in chars_in_scene:
                        chars_in_scene.append(char_id)

        char_names = [char_map.get(cid, {}).get('name', cid) for cid in chars_in_scene]
        print(f"   👥 场景角色: {char_names if char_names else '无'}")

        # 获取角色参考图
        char_refs = ref_manager.get_references_for_scene(chars_in_scene) if chars_in_scene else []
        print(f"   📸 使用 {len(char_refs)} 张角色参考图")

        # 获取场景参考图
        scene_refs = []
        if scene_ref_manager:
            location = original_scene.get('location', '')
            location_id = scene_ref_manager._normalize_location_id(location) if location else None
            if location_id and scene_ref_manager.has_reference(location_id):
                scene_refs = scene_ref_manager.get_references_for_location(location_id)
                print(f"   🏠 使用 {len(scene_refs)} 张场景参考图 (location: {location_id})")

        # 合并参考图：角色参考图在前，场景参考图在后
        all_refs = char_refs + scene_refs

        # 构建角色描述（简化版，索引引用）
        char_descriptions = []
        ref_index = 1
        for char_id in chars_in_scene:
            char = char_map.get(char_id)
            if char:
                char_name = char.get('name', '')
                char_name_en = char.get('name_en', '')
                # 获取关键识别特征 - 使用physical字段
                physical = char.get('physical', {})
                clothing = char.get('clothing', {})
                key_features = []
                if char.get('gender'):
                    key_features.append(char['gender'])
                if physical.get('hair_color') and physical.get('hair_style'):
                    key_features.append(f"{physical['hair_color']} {physical['hair_style']} hair")
                if clothing.get('top'):
                    key_features.append(clothing['top'][:50])
                features_str = ", ".join(key_features) if key_features else ""

                char_desc = f"""CHARACTER "{char_name}" ({char_name_en}):
- Reference: See provided reference images #{ref_index} (portrait) and #{ref_index+1} (fullbody)
- Key identifiers: {features_str}
- This character's face MUST match the provided reference images EXACTLY"""
                char_descriptions.append(char_desc)
                ref_index += 2

        # 从timeline获取精确的场景描述
        visual_desc = shot.get('visual_description', '')
        narration = shot.get('narration_segment', '')
        location = original_scene.get('location', '')
        scene_style = shot.get('scene_style', {})

        # 构建完整prompt（强调时间点和具体内容）
        scene_prompt = f"""SCENE IMAGE - Shot {shot_id}
TIMELINE: {start_time:.2f}s - {end_time:.2f}s

{"CHARACTERS IN THIS SCENE:" if char_descriptions else ""}
{chr(10).join(char_descriptions) if char_descriptions else "No characters in this shot."}

SCENE DESCRIPTION:
{visual_desc}

LOCATION: {location}
NARRATIVE CONTEXT (对应音频内容): {narration}

COMPOSITION:
- Cinematic shot composition matching the narrative moment
- Characters must match their reference images exactly
- Environment must match the scene reference images
- Maintain consistent lighting: {scene_style.get('lighting', 'natural')}
- Atmosphere: {scene_style.get('atmosphere', 'cinematic')}

{"Each character's face MUST match their provided portrait reference image exactly." if char_descriptions else ""}
{"The environment/setting MUST match the provided scene reference images." if scene_refs else ""}
"""

        # 应用风格强制
        full_prompt = StyleEnforcer.enforce_prompt(scene_prompt.strip(), style_name)
        negative_prompt = StyleEnforcer.build_style_negative_prompt(style_name)
        negative_prompt += ", different face, inconsistent appearance, wrong hairstyle, different person, wrong clothing, wrong environment, inconsistent background"

        # 生成图像
        result = await image_gen.generate_image(
            prompt=full_prompt,
            negative_prompt=negative_prompt,
            aspect_ratio="16:9",
            reference_images=all_refs if all_refs else None
        )

        if result.get('success') and result.get('pil_image'):
            img_path = os.path.join(images_dir, f"shot_{shot_id:02d}.png")
            result['pil_image'].save(img_path)
            print(f"   ✅ 已保存: {img_path}")
            generated_count += 1
        else:
            print(f"   ❌ 生成失败: {result.get('error')}")

        # 等待避免速率限制
        if i < min(len(timeline), max_images) - 1:
            await asyncio.sleep(3)

    print(f"\n📊 场景图生成完成: {generated_count}/{min(len(timeline), max_images)}")
    return generated_count


async def main():
    print(f"\n{'=' * 70}")
    print("完整故事章节测试 - 全部使用 gemini-2.5-flash-image")
    print("增强版：音画精确对齐 + 角色/场景参考图")
    print(f"{'=' * 70}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"输出目录: {OUTPUT_DIR}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        # 步骤1：生成故事
        story_data = await step1_generate_story()
        if not story_data:
            return

        # 步骤2：生成角色参考图
        ref_manager, project_style = await step2_generate_character_refs(story_data)

        # 步骤2.5：生成场景参考图（确保环境一致性）
        scene_ref_manager = await step2b_generate_scene_refs(story_data, project_style)

        # 步骤3：生成分镜
        shots = await step3_generate_shots(story_data)

        # 步骤4：生成TTS音频
        audio_path, audio_duration = await step4_generate_tts(story_data, shots)

        # 步骤5：提取Whisper时间戳
        whisper_result = None
        if audio_path:
            whisper_result = await step5_whisper_timestamps(audio_path)

        # 步骤6：音画对齐（关键步骤）
        timeline = None
        if whisper_result:
            timeline = await step6_timeline_alignment(shots, whisper_result)

        # 如果timeline生成失败，使用shots作为fallback
        if not timeline or all(t.get('start_time', 0) == 0 and t.get('end_time', 0) == 0 for t in timeline[:-1]):
            print("\n⚠️ 时间线对齐可能存在问题，检查timeline数据...")
            # 打印timeline诊断信息
            if timeline:
                for t in timeline[:3]:
                    print(f"   Shot {t.get('shot_id')}: {t.get('start_time', 0):.2f}s - {t.get('end_time', 0):.2f}s")

        # 步骤7：生成场景图（使用timeline精确对齐）
        # 使用timeline而不是shots，以获取精确的时间戳信息
        await step7_generate_scene_images(
            story_data=story_data,
            timeline=timeline if timeline else shots,  # fallback to shots if timeline is empty
            ref_manager=ref_manager,
            scene_ref_manager=scene_ref_manager,
            project_style=project_style,
            max_images=12
        )

        # 输出最终总结
        print("\n" + "=" * 70)
        print("测试完成 - 最终总结")
        print("=" * 70)

        print(f"\n📁 输出目录: {OUTPUT_DIR}")
        print(f"\n📊 统计信息:")
        print(f"   - 场景数: {len(story_data.get('scenes', []))}")
        print(f"   - 镜头数: {len(shots)}")
        print(f"   - 音频时长: {audio_duration:.1f}秒")
        if timeline:
            print(f"   - 时间线条目: {len(timeline)}")

        print(f"\n👥 角色列表:")
        for char in story_data.get('characters', []):
            char_id = char.get('id', 'N/A')
            char_name = char.get('name', 'N/A')
            clothing = char.get('clothing', {})
            top = clothing.get('top', 'N/A')[:40] if clothing else 'N/A'
            print(f"   - {char_name} ({char_id}): {top}...")

        print(f"\n📸 生成的文件:")
        # 列出所有生成的图片
        for root, dirs, files in os.walk(OUTPUT_DIR):
            for f in sorted(files):
                if f.endswith('.png') or f.endswith('.mp3') or f.endswith('.json'):
                    rel_path = os.path.relpath(os.path.join(root, f), OUTPUT_DIR)
                    print(f"   - {rel_path}")

        print(f"\n🔑 关键验证点:")
        print(f"   - 所有图片使用: gemini-2.5-flash-image")
        print(f"   - 风格: realistic (写实摄影)")
        print(f"   - 角色一致性: 使用角色参考图")
        print(f"   - 场景一致性: 使用场景参考图")
        print(f"   - 音画对齐: 基于Whisper时间戳")

    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
