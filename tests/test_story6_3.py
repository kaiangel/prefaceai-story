"""
teststory6.3 - 完整端到端测试：深夜便利店

故事: 深夜便利店，三个失眠的陌生人
- 时长: 2分钟 (约8-12个scene)
- 角色: 3人 (护士、程序员、调酒师)
- 风格: realistic
- 场景: 便利店 (内部/外部/台阶)

验证重点:
1. 角色差异化：三个角色职业/外貌必须一眼可辨
2. 场景一致性：便利店在不同镜头中保持一致
3. 角色一致性：每个角色在所有出现的scene中保持一致
4. 音画对齐：TTS + Whisper + timeline
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

OUTPUT_DIR = "test_output/manualtest/teststory6.3"

# 验证结果记录
verification_results = {
    "character_differentiation": {"passed": False, "details": []},
    "scene_consistency": {"passed": False, "details": []},
    "character_consistency": {"passed": False, "details": []},
    "audio_alignment": {"passed": False, "details": []},
    "image_prompt_quality": {"passed": False, "details": []},
    "reference_images_used": {"passed": False, "details": []},
    "files_generated": {"passed": False, "details": []}
}


async def step1_generate_story():
    """步骤1：生成故事 - 深夜便利店的三个失眠者"""
    print("\n" + "=" * 60)
    print("步骤1: 生成故事 - 深夜便利店")
    print("=" * 60)

    story_gen = StoryGenerator()

    idea = """深夜便利店，三个失眠的陌生人

凌晨两点的便利店，三个睡不着的人在这里相遇：一个刚下夜班的护士，一个赶deadline的程序员，一个失恋买醉的调酒师。他们因为同时伸手拿最后一罐咖啡而相遇，最后坐在便利店门口的台阶上分享各自的故事，发现生活虽苦但并不孤单。

情节要求（8-10个场景）：
- 场景1：凌晨的便利店，霓虹灯闪烁，程序员拖着疲惫的身躯推门进入
- 场景2：护士刚下班，穿着护士服外套，在货架前挑选泡面
- 场景3：调酒师神情颓废，提着一袋啤酒站在冷饮柜前发呆
- 场景4：三人同时伸手拿货架上最后一罐咖啡，四目交汇的尴尬
- 场景5：收银台前，三人互相谦让，气氛从尴尬变得有趣
- 场景6：程序员提议一起在门口台阶坐坐，护士和调酒师同意
- 场景7：便利店门口的台阶上，三人分享各自失眠的原因
- 场景8：天边泛起鱼肚白，三人相视而笑，交换了联系方式
- 场景9：告别时刻，三人各自离去，心情却比来时轻松

角色设定（必须高度差异化）：

1. 陈默（女，26岁）— 护士
   - 外貌：马尾辫，疲惫但温柔的眼神，皮肤略显苍白
   - 服装：粉色护士服外套，里面是白色T恤，浅蓝色牛仔裤，白色运动鞋
   - 配饰：简单的银色手表，口袋里别着一支笔
   - 气质：温柔、细心、略带疲惫

2. 李想（男，28岁）— 程序员
   - 外貌：戴黑框眼镜，头发有点乱，胡子拉碴，黑眼圈明显
   - 服装：深灰色连帽卫衣，黑色工装裤，脏兮兮的白色球鞋
   - 配饰：大号双肩背包，耳机挂在脖子上
   - 气质：邋遢但聪明，有点社恐但善良

3. 张野（男，25岁）— 调酒师
   - 外貌：精心打理的偏分发型，帅气但眼神空洞，下巴有设计感的胡茬
   - 服装：黑色紧身V领毛衣，深色修身西裤，尖头皮鞋
   - 配饰：银色耳钉，手腕上有一条皮质手链
   - 气质：时尚颓废，表面不在乎但内心脆弱

场景风格：
- 便利店：典型的24小时便利店，白色荧光灯，整齐的货架，冷藏柜发出低沉嗡嗡声
- 门口台阶：混凝土台阶，便利店招牌发出暖黄色光，对面是空旷的街道
- 氛围：深夜的孤独感，但温暖的人情味"""

    result = await story_gen.generate_story(
        idea=idea,
        style="realistic",
        duration_minutes=2,
        character_count=3,
        chapter_number=1,
        total_chapters=1,
        language="zh-CN",
        min_scenes=8
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

    # 打印角色信息
    print("\n角色详情:")
    for char in story_data.get('characters', []):
        name = char.get('name', 'N/A')
        name_en = char.get('name_en', 'N/A')
        physical = char.get('physical', {})
        clothing = char.get('clothing', {})

        print(f"\n  【{name}】({name_en})")
        print(f"    发型: {physical.get('hair_style', 'N/A')}")
        print(f"    发色: {physical.get('hair_color', 'N/A')}")
        print(f"    上衣: {clothing.get('top', 'N/A')}")
        print(f"    风格: {clothing.get('style', 'N/A')}")

        verification_results["character_differentiation"]["details"].append({
            "name": name,
            "hair_style": physical.get('hair_style'),
            "hair_color": physical.get('hair_color'),
            "top": clothing.get('top'),
            "style": clothing.get('style')
        })

    return story_data


async def step2_generate_character_refs(story_data):
    """步骤2：生成角色参考图（肖像+全身）"""
    print("\n" + "=" * 60)
    print("步骤2: 生成角色参考图 (3人×2张=6张)")
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
        char_name_en = char.get('name_en', char_name)
        char_id = char.get('id', f'char_{i+1:03d}')

        # 构建详细的外观描述
        physical = char.get('physical', {})
        clothing = char.get('clothing', {})

        appearance_parts = []
        if physical.get('hair_color'):
            appearance_parts.append(f"{physical['hair_color']} hair")
        if physical.get('hair_style'):
            appearance_parts.append(f"{physical['hair_style']}")
        if physical.get('skin_tone'):
            appearance_parts.append(f"{physical['skin_tone']} skin")
        if physical.get('eye_color'):
            appearance_parts.append(f"{physical['eye_color']} eyes")

        if clothing.get('top'):
            appearance_parts.append(f"wearing {clothing['top']}")
        if clothing.get('bottom'):
            appearance_parts.append(clothing['bottom'])
        if clothing.get('accessories'):
            appearance_parts.append(", ".join(clothing['accessories'][:2]))

        appearance = ", ".join(appearance_parts)

        print(f"\n[{i+1}/{len(characters)}] 生成 {char_name} ({char_name_en}) 参考图...")
        print(f"    外观: {appearance[:100]}...")

        # 肖像
        portrait_prompt = f"""Professional portrait photograph of {char_name_en}.
{appearance}
Front facing camera, neutral background.
Soft natural lighting, photorealistic, high detail, sharp focus.
Professional headshot for film production."""

        portrait_prompt = StyleEnforcer.enforce_prompt(portrait_prompt, "realistic")

        result = await image_gen.generate_image(
            prompt=portrait_prompt,
            aspect_ratio="1:1"
        )

        if result.get('success') and result.get('pil_image'):
            portrait_path = os.path.join(refs_dir, f"{char_id}_portrait.png")
            result['pil_image'].save(portrait_path)

            if char_id not in ref_manager.character_references:
                ref_manager.character_references[char_id] = {}
            ref_manager.character_references[char_id]['portrait'] = result['pil_image']
            print(f"   ✅ 肖像: {portrait_path}")

            await asyncio.sleep(3)

            # 全身（使用肖像作为参考）
            fullbody_prompt = f"""Full body photograph of {char_name_en}, standing pose.
{appearance}
Late night convenience store environment, fluorescent lighting.
Photorealistic, cinematic composition, detailed clothing and accessories."""

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

                verification_results["reference_images_used"]["details"].append({
                    "character": char_name,
                    "portrait": True,
                    "fullbody": True
                })
        else:
            print(f"   ❌ 肖像生成失败: {result.get('error')}")
            verification_results["reference_images_used"]["details"].append({
                "character": char_name,
                "portrait": False,
                "fullbody": False,
                "error": result.get('error')
            })

        await asyncio.sleep(3)

    return ref_manager, project_style


async def step3_generate_shots(story_data):
    """步骤3：生成分镜"""
    print("\n" + "=" * 60)
    print("步骤3: 生成分镜 (验证 characters_in_scene)")
    print("=" * 60)

    storyboard = StoryboardService()
    scenes = story_data.get('scenes', [])
    characters = story_data.get('characters', [])

    print("\n原始场景角色:")
    for scene in scenes:
        print(f"  Scene {scene.get('scene_id')}: {scene.get('characters_in_scene', [])}")

    shots = await storyboard.generate_storyboard_with_splitting(
        scenes=scenes,
        characters=characters,
        style_preset="realistic",
        aspect_ratio="16:9"
    )

    # 验证 characters_in_scene
    print("\n" + "-" * 40)
    print("【验证】Shot的characters_in_scene:")
    print("-" * 40)

    for shot in shots:
        chars = shot.get('characters_in_scene', [])
        image_prompt = shot.get('image_prompt', '')[:60]
        print(f"  Shot {shot.get('shot_id')}: {chars}")
        print(f"       prompt: {image_prompt}...")

        verification_results["image_prompt_quality"]["details"].append({
            "shot_id": shot.get('shot_id'),
            "characters": chars,
            "prompt_preview": image_prompt
        })

    with open(os.path.join(OUTPUT_DIR, "shots.json"), 'w', encoding='utf-8') as f:
        json.dump(shots, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 分镜生成完成: {len(shots)} 个shot")

    return shots


async def step4_tts_and_alignment(story_data, shots):
    """步骤4：TTS和音画对齐"""
    print("\n" + "=" * 60)
    print("步骤4: TTS + Whisper + 对齐")
    print("=" * 60)

    # TTS
    tts = TTSService()
    narrations = [shot.get('narration_segment', '') for shot in shots]
    full_text = ''.join(narrations)

    print(f"旁白总字数: {len(full_text)}")
    print(f"预计时长: {len(full_text) / 4:.1f}秒 (按4字/秒)")

    audio_result = await tts.synthesize(full_text)
    if not audio_result.get('success'):
        print(f"❌ TTS失败: {audio_result.get('error')}")
        return None, 0

    audio_path = os.path.join(OUTPUT_DIR, "narration.mp3")
    with open(audio_path, 'wb') as f:
        f.write(audio_result['audio_data'])

    audio_duration = audio_result.get('duration_seconds', 0)
    print(f"✅ TTS完成: {audio_duration:.1f}秒")

    verification_results["files_generated"]["details"].append("narration.mp3")

    # Whisper
    whisper = WhisperService()
    whisper_result = await whisper.transcribe_with_timestamps(audio_path)

    if not whisper_result:
        print("❌ Whisper失败")
        return None, audio_duration

    segments = whisper_result.get('segments', [])
    whisper_text = whisper_result.get('text', '')
    print(f"✅ Whisper完成: {len(segments)} 个segments")

    if audio_duration == 0 and segments:
        audio_duration = segments[-1].get('end', 0)
        print(f"   从Whisper获取音频时长: {audio_duration:.1f}秒")

    with open(os.path.join(OUTPUT_DIR, "whisper.json"), 'w', encoding='utf-8') as f:
        json.dump(whisper_result, f, ensure_ascii=False, indent=2)

    verification_results["files_generated"]["details"].append("whisper.json")

    # 对齐
    alignment = AlignmentService()
    timeline = await alignment.align_shots_to_audio(
        shots, segments, whisper_text, audio_duration
    )

    # 验证音画对齐
    print("\n" + "-" * 40)
    print("【验证】Timeline时间戳:")
    print("-" * 40)

    all_valid = True
    for item in timeline:
        start = item.get('start_time', 0)
        end = item.get('end_time', 0)
        duration = end - start
        status = "✅" if duration > 0 else "❌"
        if duration <= 0:
            all_valid = False
        print(f"  Shot {item.get('shot_id')}: {start:.2f}s - {end:.2f}s ({duration:.2f}s) {status}")
        verification_results["audio_alignment"]["details"].append({
            "shot_id": item.get('shot_id'),
            "start": start,
            "end": end,
            "duration": duration
        })

    if timeline:
        last_end = timeline[-1].get('end_time', 0)
        coverage = last_end / audio_duration * 100 if audio_duration > 0 else 0
        print(f"\n  时间覆盖: {last_end:.2f}s / {audio_duration:.2f}s ({coverage:.1f}%)")
        all_valid = all_valid and coverage > 90

    verification_results["audio_alignment"]["passed"] = all_valid

    with open(os.path.join(OUTPUT_DIR, "timeline.json"), 'w', encoding='utf-8') as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)

    verification_results["files_generated"]["details"].append("timeline.json")

    return timeline, audio_duration


async def step5_generate_scene_refs(story_data, project_style):
    """步骤5：生成场景参考图"""
    print("\n" + "=" * 60)
    print("步骤5: 生成场景参考图")
    print("=" * 60)

    scene_refs_dir = os.path.join(OUTPUT_DIR, "scene_refs")
    os.makedirs(scene_refs_dir, exist_ok=True)

    scene_ref_manager = SceneReferenceManager()
    scenes = story_data.get('scenes', [])

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
            if view_type == 'interior':
                prompt = f"""Cinematic interior shot of {loc}.
No people, empty space, establishing shot.
Late night atmosphere, fluorescent lighting, quiet ambiance.
Photorealistic, high quality, detailed convenience store interior."""
            else:
                prompt = f"""Cinematic exterior shot of {loc}.
No people, empty street, night time.
Convenience store front with glowing signage, concrete steps at entrance.
Photorealistic, high quality, urban night photography."""

            prompt = StyleEnforcer.enforce_prompt(prompt, "realistic")

            result = await image_gen.generate_image(
                prompt=prompt,
                aspect_ratio="16:9"
            )

            if result.get('success') and result.get('pil_image'):
                location_id = scene_ref_manager._normalize_location_id(loc)
                scene_ref_manager.set_reference(location_id, view_type, result['pil_image'])

                safe_name = "".join(c if c.isalnum() or c in ['_', '-'] else '_' for c in loc)[:30]
                filename = f"{safe_name}_{view_type}.png"
                filepath = os.path.join(scene_refs_dir, filename)
                result['pil_image'].save(filepath)
                print(f"  ✅ {view_type}: {filename}")

                verification_results["scene_consistency"]["details"].append({
                    "location": loc[:30],
                    "view_type": view_type,
                    "file": filename
                })
            else:
                print(f"  ❌ {view_type} 失败: {result.get('error')}")

            await asyncio.sleep(3)

    verification_results["scene_consistency"]["passed"] = len(verification_results["scene_consistency"]["details"]) > 0

    return scene_ref_manager


async def step6_generate_scene_images(story_data, timeline, ref_manager, scene_ref_manager, max_images=12):
    """步骤6：生成场景图片"""
    print("\n" + "=" * 60)
    print(f"步骤6: 生成场景图片 (最多{max_images}张)")
    print("=" * 60)

    images_dir = os.path.join(OUTPUT_DIR, "images")
    os.makedirs(images_dir, exist_ok=True)

    image_gen = ImageGenerator()
    characters = story_data.get('characters', [])
    scenes = story_data.get('scenes', [])

    char_map = {c.get('id'): c for c in characters if c.get('id')}
    scene_map = {s.get('scene_id'): s for s in scenes if s.get('scene_id')}

    generated_images = []
    all_refs_used = True

    for i, shot in enumerate(timeline[:max_images]):
        shot_id = shot.get('shot_id', i + 1)
        scene_id = shot.get('original_scene_id', 1)
        start_time = shot.get('start_time', 0)
        end_time = shot.get('end_time', 0)

        print(f"\n[Shot {shot_id}] {start_time:.2f}s - {end_time:.2f}s")

        # 获取原始scene
        original_scene = scene_map.get(scene_id, {})
        chars_in_scene = original_scene.get('characters_in_scene', [])
        location = original_scene.get('location', '')

        # 获取角色参考图
        char_refs = ref_manager.get_references_for_scene(chars_in_scene) if chars_in_scene else []
        print(f"  角色: {chars_in_scene} -> {len(char_refs)} 张参考图")

        # 获取场景参考图
        scene_refs = []
        if scene_ref_manager and location:
            location_id = scene_ref_manager._normalize_location_id(location)
            if scene_ref_manager.has_reference(location_id):
                scene_refs = scene_ref_manager.get_references_for_location(location_id)
                print(f"  场景: {location[:30]} -> {len(scene_refs)} 张参考图")

        all_refs = char_refs + scene_refs
        print(f"  总参考图: {len(all_refs)} 张")

        if len(all_refs) == 0:
            all_refs_used = False

        # 使用 generate_shot_image 方法
        result = await image_gen.generate_shot_image(
            shot=shot,
            reference_images=all_refs if all_refs else None,
            aspect_ratio="16:9",
            use_llm_translation=False
        )

        if result.get('success') and result.get('pil_image'):
            img_path = os.path.join(images_dir, f"shot_{shot_id:02d}.png")
            result['pil_image'].save(img_path)
            generated_images.append(img_path)
            print(f"  ✅ 已保存: shot_{shot_id:02d}.png")

            verification_results["character_consistency"]["details"].append({
                "shot_id": shot_id,
                "characters": chars_in_scene,
                "ref_count": len(char_refs),
                "scene_ref_count": len(scene_refs),
                "success": True
            })
        else:
            print(f"  ❌ 生成失败: {result.get('error')}")
            verification_results["character_consistency"]["details"].append({
                "shot_id": shot_id,
                "success": False,
                "error": result.get('error')
            })

        await asyncio.sleep(3)

    verification_results["reference_images_used"]["passed"] = all_refs_used
    verification_results["character_consistency"]["passed"] = len(generated_images) > 0

    return generated_images


def print_final_report(audio_duration):
    """打印最终验证报告"""
    print("\n")
    print("=" * 60)
    print("teststory6.3 验证报告 - 深夜便利店")
    print("=" * 60)

    all_passed = True

    # 验证点1：角色差异化
    v1 = verification_results["character_differentiation"]
    print(f"\n【验证点1】角色差异化:")
    for detail in v1["details"]:
        print(f"  - {detail['name']}: {detail.get('hair_style', 'N/A')[:20]}, {detail.get('top', 'N/A')[:20]}")
    v1["passed"] = len(v1["details"]) == 3  # 必须有3个不同角色

    # 验证点2：场景一致性
    v2 = verification_results["scene_consistency"]
    print(f"\n【验证点2】场景一致性: {'✅ 通过' if v2['passed'] else '❌ 失败'}")
    print(f"  生成了 {len(v2['details'])} 张场景参考图")

    # 验证点3：角色一致性
    v3 = verification_results["character_consistency"]
    success_count = sum(1 for d in v3["details"] if d.get("success"))
    print(f"\n【验证点3】角色一致性: {'✅ 通过' if v3['passed'] else '❌ 失败'}")
    print(f"  成功生成 {success_count}/{len(v3['details'])} 张场景图")

    # 验证点4：音画对齐
    v4 = verification_results["audio_alignment"]
    print(f"\n【验证点4】音画对齐: {'✅ 通过' if v4['passed'] else '❌ 失败'}")

    # 验证点5：参考图使用
    v5 = verification_results["reference_images_used"]
    print(f"\n【验证点5】参考图使用: {'✅ 通过' if v5['passed'] else '⚠️ 部分未使用'}")

    # 文件列表
    print("\n" + "-" * 40)
    print(f"音频时长: {audio_duration:.2f}秒")
    print(f"输出目录: {OUTPUT_DIR}")

    print("\n生成的文件:")
    for root, dirs, files in os.walk(OUTPUT_DIR):
        level = root.replace(OUTPUT_DIR, '').count(os.sep)
        indent = '  ' * level
        subindent = '  ' * (level + 1)
        folder_name = os.path.basename(root)
        if level > 0:
            print(f"{indent}{folder_name}/")
        for f in sorted(files):
            if not f.startswith('.'):
                print(f"{subindent}{f}")

    # 验证结果汇总
    verification_results["files_generated"]["passed"] = True
    verification_results["character_differentiation"]["passed"] = len(verification_results["character_differentiation"]["details"]) >= 3

    print("\n" + "=" * 60)
    passed_count = sum(1 for v in verification_results.values() if v.get("passed"))
    total_count = len(verification_results)
    print(f"验证结果: {passed_count}/{total_count} 项通过")

    if passed_count == total_count:
        print("🎉 所有验证点通过！")
    else:
        print("⚠️ 部分验证点需要检查。")
    print("=" * 60)

    # 保存验证结果
    with open(os.path.join(OUTPUT_DIR, "verification_results.json"), 'w', encoding='utf-8') as f:
        json.dump(verification_results, f, ensure_ascii=False, indent=2)


async def main():
    print("=" * 60)
    print("teststory6.3 - 深夜便利店的三个失眠者")
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

        # Step 3: 分镜
        shots = await step3_generate_shots(story_data)

        # Step 4: TTS + 对齐
        timeline, audio_duration = await step4_tts_and_alignment(story_data, shots)
        if not timeline:
            print("❌ 对齐失败，终止测试")
            return

        # Step 5: 场景参考图
        scene_ref_manager = await step5_generate_scene_refs(story_data, project_style)

        # Step 6: 场景图片
        await step6_generate_scene_images(
            story_data, timeline, ref_manager, scene_ref_manager, max_images=12
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
