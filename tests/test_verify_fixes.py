"""
精简端到端验证测试 - 验证4个修复是否生效

验证点:
1. characters_in_scene 修复
2. 音画对齐修复
3. 场景参考图
4. 角色参考图传入
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
from app.services.style_enforcer import StyleEnforcer
from app.models.style_config import StyleConfigBuilder

OUTPUT_DIR = "test_output/manualtest/teststory6_verify_fixes"

# 验证结果记录
verification_results = {
    "characters_in_scene": {"passed": False, "details": []},
    "audio_alignment": {"passed": False, "details": []},
    "scene_refs": {"passed": False, "details": []},
    "char_refs_in_scene": {"passed": False, "details": []}
}


async def step1_generate_story():
    """步骤1：生成故事"""
    print("\n" + "=" * 60)
    print("步骤1: 生成故事")
    print("=" * 60)

    story_gen = StoryGenerator()

    idea = """深夜地铁末班车上，一个加班到崩溃的白领和一个刚结束演出的街头歌手，因为同一首歌产生了短暂的共鸣。

情节要求（简短）：
- 开头：空荡的地铁车厢，李明疲惫地靠着座位
- 中段：小雨上车，轻轻哼起一首歌，李明被吸引
- 结尾：两人相视一笑，各自下车

角色设定：
1. 李明（男，28岁）— 加班白领，西装领带松垮，眼圈发黑，神情疲惫
2. 小雨（女，24岁）— 街头歌手，吉他背在身后，穿着随性的卫衣牛仔裤"""

    result = await story_gen.generate_story(
        idea=idea,
        style="realistic",
        duration_minutes=1,  # 1分钟
        character_count=2,
        chapter_number=1,
        total_chapters=1,
        language="zh-CN"
    )

    if isinstance(result, dict):
        if result.get('success') and result.get('data'):
            story_data = result['data']
        elif result.get('scenes'):
            story_data = result
        else:
            print(f"❌ 故事生成失败: {result}")
            return None
    else:
        print(f"❌ 格式错误: {type(result)}")
        return None

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "story.json"), 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 故事生成完成: {len(story_data.get('scenes', []))} 个场景, {len(story_data.get('characters', []))} 个角色")
    return story_data


async def step2_generate_character_refs(story_data):
    """步骤2：生成角色参考图"""
    print("\n" + "=" * 60)
    print("步骤2: 生成角色参考图")
    print("=" * 60)

    refs_dir = os.path.join(OUTPUT_DIR, "character_refs")
    os.makedirs(refs_dir, exist_ok=True)

    style_builder = StyleConfigBuilder()
    project_style = style_builder.build_from_story(story_data)
    project_style.style_preset = "realistic"

    image_gen = ImageGenerator()
    ref_manager = ReferenceImageManager()

    characters = story_data.get('characters', [])

    for i, char in enumerate(characters):
        char_name = char.get('name', f'角色{i+1}')
        char_id = char.get('id', f'char_{i+1:03d}')
        print(f"\n[{i+1}/{len(characters)}] 生成 {char_name} 参考图...")

        # 肖像
        portrait_prompt = f"Professional portrait photo of {char.get('name_en', char_name)}, {char.get('appearance', '')}, front facing, neutral background, photorealistic"
        portrait_prompt = StyleEnforcer.enforce_prompt(portrait_prompt, "realistic")

        result = await image_gen.generate_image(
            prompt=portrait_prompt,
            aspect_ratio="1:1"
        )

        if result.get('success') and result.get('pil_image'):
            portrait_path = os.path.join(refs_dir, f"{char_id}_portrait.png")
            result['pil_image'].save(portrait_path)
            # 初始化char_id的字典并存储portrait
            if char_id not in ref_manager.character_references:
                ref_manager.character_references[char_id] = {}
            ref_manager.character_references[char_id]['portrait'] = result['pil_image']
            print(f"   ✅ 肖像: {portrait_path}")

            # 全身（使用肖像作为参考）
            fullbody_prompt = f"Full body shot of {char.get('name_en', char_name)}, {char.get('appearance', '')}, standing pose, photorealistic"
            fullbody_prompt = StyleEnforcer.enforce_prompt(fullbody_prompt, "realistic")

            fb_result = await image_gen.generate_image(
                prompt=fullbody_prompt,
                aspect_ratio="3:4",
                reference_images=[result['pil_image']]
            )

            if fb_result.get('success') and fb_result.get('pil_image'):
                fullbody_path = os.path.join(refs_dir, f"{char_id}_fullbody.png")
                fb_result['pil_image'].save(fullbody_path)
                ref_manager.character_references[char_id]['fullbody'] = fb_result['pil_image']
                print(f"   ✅ 全身: {fullbody_path}")

        await asyncio.sleep(2)

    return ref_manager, project_style


async def step3_generate_shots(story_data):
    """步骤3：生成分镜（验证characters_in_scene修复）"""
    print("\n" + "=" * 60)
    print("步骤3: 生成分镜 (验证 characters_in_scene)")
    print("=" * 60)

    storyboard = StoryboardService()
    scenes = story_data.get('scenes', [])
    characters = story_data.get('characters', [])

    # 打印原始scene的characters_in_scene
    print("\n原始场景角色:")
    for scene in scenes:
        print(f"  Scene {scene.get('scene_id')}: {scene.get('characters_in_scene', [])}")

    shots = await storyboard.generate_storyboard_with_splitting(
        scenes=scenes,
        characters=characters,
        style_preset="realistic",
        aspect_ratio="16:9"
    )

    # 验证点1: characters_in_scene
    print("\n" + "-" * 40)
    print("【验证点1】Shot的characters_in_scene:")
    print("-" * 40)

    all_have_chars = True
    for shot in shots:
        chars = shot.get('characters_in_scene', [])
        status = "✅" if chars else "❌"
        if not chars:
            all_have_chars = False
        print(f"  Shot {shot.get('shot_id')}: {chars} {status}")
        verification_results["characters_in_scene"]["details"].append({
            "shot_id": shot.get('shot_id'),
            "characters": chars
        })

    verification_results["characters_in_scene"]["passed"] = all_have_chars
    print(f"\n验证结果: {'✅ 通过' if all_have_chars else '❌ 失败'}")

    with open(os.path.join(OUTPUT_DIR, "shots.json"), 'w', encoding='utf-8') as f:
        json.dump(shots, f, ensure_ascii=False, indent=2)

    return shots


async def step4_tts_and_alignment(story_data, shots):
    """步骤4：TTS和音画对齐（验证对齐修复）"""
    print("\n" + "=" * 60)
    print("步骤4: TTS + Whisper + 对齐 (验证音画对齐)")
    print("=" * 60)

    # TTS
    tts = TTSService()
    narrations = [shot.get('narration_segment', '') for shot in shots]
    full_text = ''.join(narrations)

    print(f"旁白总字数: {len(full_text)}")

    audio_result = await tts.synthesize(full_text)
    if not audio_result.get('success'):
        print(f"❌ TTS失败: {audio_result.get('error')}")
        return None, 0

    audio_path = os.path.join(OUTPUT_DIR, "narration.mp3")
    with open(audio_path, 'wb') as f:
        f.write(audio_result['audio_data'])

    # TTS返回的是duration_seconds，不是duration
    audio_duration = audio_result.get('duration_seconds', 0)
    print(f"✅ TTS完成: {audio_duration:.1f}秒")

    # Whisper
    whisper = WhisperService()
    whisper_result = await whisper.transcribe_with_timestamps(audio_path)

    if not whisper_result:
        print("❌ Whisper失败")
        return None, audio_duration

    segments = whisper_result.get('segments', [])
    whisper_text = whisper_result.get('text', '')
    print(f"✅ Whisper完成: {len(segments)} 个segments")

    # 从Whisper获取准确的audio duration（如果TTS没返回）
    if audio_duration == 0 and segments:
        audio_duration = segments[-1].get('end', 0)
        print(f"   从Whisper获取音频时长: {audio_duration:.1f}秒")

    with open(os.path.join(OUTPUT_DIR, "whisper.json"), 'w', encoding='utf-8') as f:
        json.dump(whisper_result, f, ensure_ascii=False, indent=2)

    # 对齐
    alignment = AlignmentService()
    timeline = await alignment.align_shots_to_audio(
        shots, segments, whisper_text, audio_duration
    )

    # 验证点2: 音画对齐
    print("\n" + "-" * 40)
    print("【验证点2】Timeline时间戳:")
    print("-" * 40)

    all_have_time = True
    for item in timeline:
        start = item.get('start_time', 0)
        end = item.get('end_time', 0)
        has_time = (start > 0 or end > 0) or (item == timeline[0])  # 第一个可以从0开始
        status = "✅" if end > start else "❌"
        if end <= start and item != timeline[0]:
            all_have_time = False
        print(f"  Shot {item.get('shot_id')}: {start:.2f}s - {end:.2f}s {status}")
        verification_results["audio_alignment"]["details"].append({
            "shot_id": item.get('shot_id'),
            "start": start,
            "end": end
        })

    # 检查时间戳是否覆盖完整
    if timeline:
        last_end = timeline[-1].get('end_time', 0)
        coverage = last_end / audio_duration * 100 if audio_duration > 0 else 0
        print(f"\n  时间覆盖: {last_end:.2f}s / {audio_duration:.2f}s ({coverage:.1f}%)")
        all_have_time = all_have_time and coverage > 90

    verification_results["audio_alignment"]["passed"] = all_have_time
    print(f"\n验证结果: {'✅ 通过' if all_have_time else '❌ 失败'}")

    with open(os.path.join(OUTPUT_DIR, "timeline.json"), 'w', encoding='utf-8') as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)

    return timeline, audio_duration


async def step5_generate_scene_refs(story_data, project_style):
    """步骤5：生成场景参考图"""
    print("\n" + "=" * 60)
    print("步骤5: 生成场景参考图")
    print("=" * 60)

    scene_refs_dir = os.path.join(OUTPUT_DIR, "scene_refs")
    os.makedirs(scene_refs_dir, exist_ok=True)

    scene_ref_manager = SceneReferenceManager()  # 不接受参数
    scenes = story_data.get('scenes', [])

    # 收集唯一location
    locations = set()
    for scene in scenes:
        loc = scene.get('location', '')
        if loc:
            locations.add(loc)

    print(f"唯一场景数: {len(locations)}")

    image_gen = ImageGenerator()

    for loc in locations:
        print(f"\n生成场景: {loc}")

        for view_type in ['interior', 'exterior']:
            prompt = f"Cinematic {view_type} shot of {loc}, photorealistic, no people, establishing shot"
            prompt = StyleEnforcer.enforce_prompt(prompt, "realistic")

            result = await image_gen.generate_image(
                prompt=prompt,
                aspect_ratio="16:9"
            )

            if result.get('success') and result.get('pil_image'):
                location_id = scene_ref_manager._normalize_location_id(loc)
                # 使用 set_reference 而不是 add_reference
                scene_ref_manager.set_reference(location_id, view_type, result['pil_image'])

                filename = f"{loc}_{view_type}.png"
                filepath = os.path.join(scene_refs_dir, filename)
                result['pil_image'].save(filepath)
                print(f"  ✅ {view_type}: {filename}")

                verification_results["scene_refs"]["details"].append(filename)

            await asyncio.sleep(2)

    verification_results["scene_refs"]["passed"] = len(verification_results["scene_refs"]["details"]) > 0

    return scene_ref_manager


async def step6_generate_scene_images(story_data, timeline, ref_manager, scene_ref_manager, max_images=6):
    """步骤6：生成场景图（验证参考图传入）"""
    print("\n" + "=" * 60)
    print(f"步骤6: 生成场景图 (前{max_images}张，验证参考图传入)")
    print("=" * 60)

    images_dir = os.path.join(OUTPUT_DIR, "images")
    os.makedirs(images_dir, exist_ok=True)

    image_gen = ImageGenerator()
    characters = story_data.get('characters', [])
    scenes = story_data.get('scenes', [])

    char_map = {c.get('id'): c for c in characters if c.get('id')}
    scene_map = {s.get('scene_id'): s for s in scenes if s.get('scene_id')}

    print("\n" + "-" * 40)
    print("【验证点3&4】参考图传入情况:")
    print("-" * 40)

    all_refs_correct = True
    generated_images = []

    for i, shot in enumerate(timeline[:max_images]):
        shot_id = shot.get('shot_id', i + 1)
        scene_id = shot.get('original_scene_id', 1)
        start_time = shot.get('start_time', 0)
        end_time = shot.get('end_time', 0)

        print(f"\n[Shot {shot_id}] {start_time:.2f}s - {end_time:.2f}s")

        # 获取角色
        original_scene = scene_map.get(scene_id, {})
        chars_in_scene = original_scene.get('characters_in_scene', [])

        char_names = [char_map.get(cid, {}).get('name', cid) for cid in chars_in_scene]
        print(f"  角色: {char_names}")

        # 获取角色参考图
        char_refs = ref_manager.get_references_for_scene(chars_in_scene) if chars_in_scene else []
        print(f"  角色参考图: {len(char_refs)} 张")

        # 获取场景参考图
        scene_refs = []
        location = original_scene.get('location', '')
        if scene_ref_manager and location:
            location_id = scene_ref_manager._normalize_location_id(location)
            if scene_ref_manager.has_reference(location_id):
                scene_refs = scene_ref_manager.get_references_for_location(location_id)
                print(f"  场景参考图: {len(scene_refs)} 张 ({location})")

        all_refs = char_refs + scene_refs
        print(f"  总参考图: {len(all_refs)} 张")

        # 记录验证信息
        ref_info = {
            "shot_id": shot_id,
            "characters": char_names,
            "char_refs": len(char_refs),
            "scene_refs": len(scene_refs),
            "total_refs": len(all_refs)
        }
        verification_results["char_refs_in_scene"]["details"].append(ref_info)

        # 验证：多角色场景应该有对应数量的参考图
        expected_char_refs = len(chars_in_scene) * 2  # portrait + fullbody
        if len(char_refs) < expected_char_refs and chars_in_scene:
            all_refs_correct = False
            print(f"  ⚠️ 期望 {expected_char_refs} 张角色参考图，实际 {len(char_refs)} 张")

        # 构建prompt
        visual_desc = shot.get('visual_description', '')
        narration = shot.get('narration_segment', '')

        char_descriptions = []
        ref_idx = 1
        for char_id in chars_in_scene:
            char = char_map.get(char_id)
            if char:
                char_descriptions.append(
                    f"CHARACTER \"{char.get('name')}\": See reference images #{ref_idx} and #{ref_idx+1}"
                )
                ref_idx += 2

        scene_prompt = f"""SCENE IMAGE - Shot {shot_id}
TIMELINE: {start_time:.2f}s - {end_time:.2f}s

{chr(10).join(char_descriptions) if char_descriptions else "No characters."}

SCENE: {visual_desc}
LOCATION: {location}
NARRATIVE: {narration}

Characters MUST match their reference images exactly.
"""
        full_prompt = StyleEnforcer.enforce_prompt(scene_prompt, "realistic")
        negative_prompt = StyleEnforcer.build_style_negative_prompt("realistic")

        # 生成
        result = await image_gen.generate_image(
            prompt=full_prompt,
            negative_prompt=negative_prompt,
            aspect_ratio="16:9",
            reference_images=all_refs if all_refs else None
        )

        if result.get('success') and result.get('pil_image'):
            img_path = os.path.join(images_dir, f"shot_{shot_id:02d}.png")
            result['pil_image'].save(img_path)
            generated_images.append(img_path)
            print(f"  ✅ 已保存: shot_{shot_id:02d}.png")
        else:
            print(f"  ❌ 生成失败: {result.get('error')}")

        await asyncio.sleep(3)

    verification_results["char_refs_in_scene"]["passed"] = all_refs_correct

    return generated_images


def print_final_report(audio_duration):
    """打印最终验证报告"""
    print("\n")
    print("=" * 60)
    print("验证报告")
    print("=" * 60)

    all_passed = True

    # 验证点1
    v1 = verification_results["characters_in_scene"]
    status1 = "✅ 通过" if v1["passed"] else "❌ 失败"
    print(f"\n【验证点1】characters_in_scene修复: {status1}")
    for d in v1["details"]:
        print(f"  Shot {d['shot_id']}: {d['characters']}")
    if not v1["passed"]:
        all_passed = False

    # 验证点2
    v2 = verification_results["audio_alignment"]
    status2 = "✅ 通过" if v2["passed"] else "❌ 失败"
    print(f"\n【验证点2】音画对齐修复: {status2}")
    for d in v2["details"]:
        print(f"  Shot {d['shot_id']}: {d['start']:.2f}s - {d['end']:.2f}s")
    if not v2["passed"]:
        all_passed = False

    # 验证点3
    v3 = verification_results["scene_refs"]
    status3 = "✅ 通过" if v3["passed"] else "❌ 失败"
    print(f"\n【验证点3】场景参考图: {status3}")
    for f in v3["details"]:
        print(f"  - {f}")
    if not v3["passed"]:
        all_passed = False

    # 验证点4
    v4 = verification_results["char_refs_in_scene"]
    status4 = "✅ 通过" if v4["passed"] else "❌ 失败"
    print(f"\n【验证点4】角色参考图传入: {status4}")
    for d in v4["details"]:
        print(f"  Shot {d['shot_id']}: 角色{d['characters']} -> {d['char_refs']}张角色参考 + {d['scene_refs']}张场景参考")
    if not v4["passed"]:
        all_passed = False

    # 总结
    print("\n" + "=" * 60)
    print(f"音频时长: {audio_duration:.2f}秒")
    print(f"输出目录: {OUTPUT_DIR}")

    # 列出所有文件
    print("\n生成的文件:")
    for root, dirs, files in os.walk(OUTPUT_DIR):
        for f in sorted(files):
            if f.endswith('.png') or f.endswith('.mp3') or f.endswith('.json'):
                rel_path = os.path.relpath(os.path.join(root, f), OUTPUT_DIR)
                print(f"  - {rel_path}")

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有验证点通过！4个修复均已生效。")
    else:
        print("⚠️ 部分验证点失败，请检查上述详情。")
    print("=" * 60)

    # 保存验证结果
    with open(os.path.join(OUTPUT_DIR, "verification_results.json"), 'w', encoding='utf-8') as f:
        json.dump(verification_results, f, ensure_ascii=False, indent=2)


async def main():
    print("=" * 60)
    print("精简端到端验证测试 - 验证4个修复")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"输出目录: {OUTPUT_DIR}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        # Step 1: 生成故事
        story_data = await step1_generate_story()
        if not story_data:
            return

        # Step 2: 角色参考图
        ref_manager, project_style = await step2_generate_character_refs(story_data)

        # Step 3: 分镜（验证characters_in_scene）
        shots = await step3_generate_shots(story_data)

        # Step 4: TTS + 对齐（验证音画对齐）
        timeline, audio_duration = await step4_tts_and_alignment(story_data, shots)
        if not timeline:
            print("❌ 对齐失败，终止测试")
            return

        # Step 5: 场景参考图
        scene_ref_manager = await step5_generate_scene_refs(story_data, project_style)

        # Step 6: 场景图（验证参考图传入）
        await step6_generate_scene_images(
            story_data, timeline, ref_manager, scene_ref_manager, max_images=6
        )

        # 打印报告
        print_final_report(audio_duration)

    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
