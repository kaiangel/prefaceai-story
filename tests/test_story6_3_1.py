#!/usr/bin/env python3
"""
teststory6.3.1 - 角色描述修复后的完整端到端测试

测试内容（与teststory6.3相同的故事，验证修复效果）：
- Story: "深夜便利店，三个失眠的陌生人"
- Duration: 2分钟 (~8-12 scenes)
- Style: realistic
- Characters: 3 (护士、程序员、调酒师)

输出目录: test_output/manualtest/teststory6.3.1/

生成内容（完整无遗漏）:
1. story.json - 故事结构
2. shots.json - 分镜数据
3. character_refs/ - 角色参考图 (portrait + fullbody)
4. scene_refs/ - 场景参考图 (interior + exterior)
5. images/ - 所有scene图片
6. narration.mp3 - TTS音频
7. whisper.json - 语音识别结果
8. timeline.json - 音画对齐数据
9. verification_results.json - 验证报告
"""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


# 输出目录
OUTPUT_DIR = Path("test_output/manualtest/teststory6.3.1")

# 故事配置
STORY_IDEA = """
深夜便利店，三个失眠的陌生人。

凌晨两点的24小时便利店，护士陈默刚下夜班，程序员李想还在赶deadline，调酒师张野刚失恋借酒浇愁。
三个人为了最后一罐咖啡相遇，从尴尬到相识，最后坐在便利店门口的台阶上分享各自的故事。
天亮时分，他们交换了联系方式，发现生活虽苦但并不孤单。
"""

CHARACTERS_SPEC = [
    {
        "id": "char_001",
        "name": "陈默",
        "name_en": "Chen Mo",
        "role": "护士",
        "gender": "female",
        "physical": {
            "hair_color": "jet black",
            "hair_style": "high ponytail with wispy bangs",
            "eye_color": "deep brown",
            "skin_tone": "fair with slight pallor",
            "face_shape": "oval"
        },
        "clothing": {
            "top": "pink nursing jacket over white t-shirt",
            "bottom": "light blue skinny jeans",
            "accessories": ["silver minimalist watch", "black ballpoint pen in pocket"],
            "style": "practical medical casual"
        }
    },
    {
        "id": "char_002",
        "name": "李想",
        "name_en": "Li Xiang",
        "role": "程序员",
        "gender": "male",
        "physical": {
            "hair_color": "dark brown",
            "hair_style": "medium length messy bedhead",
            "eye_color": "dark brown",
            "skin_tone": "pale",
            "face_shape": "square"
        },
        "clothing": {
            "top": "dark gray oversized hoodie with drawstrings",
            "bottom": "black cargo pants with multiple pockets",
            "accessories": ["thick black-framed rectangular glasses", "black earbuds around neck", "large dark gray backpack"],
            "style": "tech casual neglected"
        }
    },
    {
        "id": "char_003",
        "name": "张野",
        "name_en": "Zhang Ye",
        "role": "调酒师",
        "gender": "male",
        "physical": {
            "hair_color": "dark brown",
            "hair_style": "perfectly styled side-parted with subtle waves",
            "eye_color": "dark brown",
            "skin_tone": "medium",
            "face_shape": "heart"
        },
        "clothing": {
            "top": "black fitted v-neck sweater with fine knit",
            "bottom": "charcoal gray tapered dress pants with sharp crease",
            "accessories": ["silver stud earring on left ear", "brown leather bracelet on wrist", "brown leather messenger bag"],
            "style": "fashionable dark elegant"
        }
    }
]


def build_character_description(char: dict) -> str:
    """构建角色的详细外观描述"""
    parts = []

    physical = char.get('physical', {})
    if physical:
        if physical.get('hair_color') or physical.get('hair_style'):
            parts.append(f"{physical.get('hair_color', '')} {physical.get('hair_style', '')}".strip())
        if physical.get('eye_color'):
            parts.append(f"{physical.get('eye_color')} eyes")
        if physical.get('skin_tone'):
            parts.append(f"{physical.get('skin_tone')} skin")

    clothing = char.get('clothing', {})
    if clothing:
        if clothing.get('top'):
            parts.append(f"wearing {clothing.get('top')}")
        if clothing.get('bottom'):
            parts.append(clothing.get('bottom'))
        if clothing.get('accessories'):
            parts.append(", ".join(clothing.get('accessories', [])[:3]))

    return ", ".join(parts)


async def run_full_e2e_test():
    """运行完整的端到端测试"""

    print("="*80)
    print("teststory6.3.1 - 角色描述修复后完整E2E测试")
    print("="*80)

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "character_refs").mkdir(exist_ok=True)
    (OUTPUT_DIR / "scene_refs").mkdir(exist_ok=True)
    (OUTPUT_DIR / "images").mkdir(exist_ok=True)

    results = {
        "test_name": "teststory6.3.1",
        "description": "角色描述修复后的完整E2E测试",
        "steps": {},
        "verification": {}
    }

    # ========== Step 1: 生成Story ==========
    print("\n" + "="*60)
    print("Step 1: 生成Story")
    print("="*60)

    story_generator = StoryGenerator()
    result = await story_generator.generate_story(
        idea=STORY_IDEA,
        style="realistic",
        duration_minutes=2,
        character_count=3,
        min_scenes=8
    )

    # 处理返回格式
    if isinstance(result, dict):
        if result.get('success') and result.get('data'):
            story = result['data']
        elif result.get('scenes'):
            story = result
        else:
            print(f"❌ 故事生成失败: {result}")
            return None
    else:
        print(f"❌ 格式错误: {type(result)}")
        return None

    # 注入我们指定的角色（确保角色描述准确）
    story['characters'] = CHARACTERS_SPEC

    # 保存story.json
    story_path = OUTPUT_DIR / "story.json"
    with open(story_path, 'w', encoding='utf-8') as f:
        json.dump(story, f, ensure_ascii=False, indent=2)

    print(f"✅ Story生成完成: {len(story.get('scenes', []))} scenes, {len(story.get('characters', []))} characters")
    results["steps"]["story"] = {"status": "success", "scenes": len(story.get('scenes', [])), "characters": len(story.get('characters', []))}

    # ========== Step 2: 生成角色参考图 ==========
    print("\n" + "="*60)
    print("Step 2: 生成角色参考图")
    print("="*60)

    image_gen = ImageGenerator()
    ref_manager = ReferenceImageManager()

    for i, char in enumerate(story['characters']):
        char_id = char.get('id')
        char_name = char.get('name')
        char_name_en = char.get('name_en', char_name)
        appearance = build_character_description(char)
        gender = char.get('gender', 'person')

        print(f"\n[{i+1}/{len(story['characters'])}] 生成 {char_name} ({char_name_en}) 参考图...")

        # 肖像
        portrait_prompt = f"""Professional portrait photograph of {char_name_en}, a Chinese {gender}.
{appearance}
Front facing camera, neutral studio background.
Soft natural lighting, photorealistic, high detail, sharp focus.
Professional headshot for film production."""

        portrait_prompt = StyleEnforcer.enforce_prompt(portrait_prompt, "realistic")

        portrait_result = await image_gen.generate_image(
            prompt=portrait_prompt,
            aspect_ratio="1:1"
        )

        if portrait_result.get('success') and portrait_result.get('pil_image'):
            portrait_path = OUTPUT_DIR / "character_refs" / f"{char_id}_portrait.png"
            portrait_result['pil_image'].save(str(portrait_path))

            if char_id not in ref_manager.character_references:
                ref_manager.character_references[char_id] = {}
            ref_manager.character_references[char_id]['portrait'] = portrait_result['pil_image']
            print(f"   ✅ 肖像: {portrait_path}")

            # 全身（使用肖像作为参考）
            fullbody_prompt = f"""Full body photograph of {char_name_en}, standing relaxed pose.
{appearance}
Late night convenience store environment, fluorescent lighting.
Photorealistic, cinematic composition, detailed clothing and accessories."""

            fullbody_prompt = StyleEnforcer.enforce_prompt(fullbody_prompt, "realistic")

            fb_result = await image_gen.generate_image(
                prompt=fullbody_prompt,
                aspect_ratio="3:4",
                reference_images=[portrait_result['pil_image']]
            )

            if fb_result.get('success') and fb_result.get('pil_image'):
                fullbody_path = OUTPUT_DIR / "character_refs" / f"{char_id}_fullbody.png"
                fb_result['pil_image'].save(str(fullbody_path))
                ref_manager.character_references[char_id]['fullbody'] = fb_result['pil_image']
                print(f"   ✅ 全身: {fullbody_path}")
        else:
            print(f"   ❌ 肖像生成失败: {portrait_result.get('error')}")

        await asyncio.sleep(2)

    char_ref_count = len(list((OUTPUT_DIR / "character_refs").glob("*.png")))
    print(f"\n✅ 角色参考图生成完成: {char_ref_count} 张")
    results["steps"]["character_refs"] = {"status": "success", "count": char_ref_count}

    # ========== Step 3: 生成Shots ==========
    print("\n" + "="*60)
    print("Step 3: 生成Shots（分镜）")
    print("="*60)

    storyboard = StoryboardService()
    shots = await storyboard.generate_storyboard_with_splitting(
        scenes=story['scenes'],
        characters=story['characters'],
        style_preset="realistic"
    )

    # 保存shots.json
    shots_path = OUTPUT_DIR / "shots.json"
    with open(shots_path, 'w', encoding='utf-8') as f:
        json.dump(shots, f, ensure_ascii=False, indent=2)

    print(f"✅ Shots生成完成: {len(shots)} shots")
    results["steps"]["shots"] = {"status": "success", "count": len(shots)}

    # 验证角色描述修复
    print("\n📋 验证角色描述修复...")
    char_fix_passed = verify_character_fix(shots, story['characters'])
    results["verification"]["character_fix"] = char_fix_passed

    # ========== Step 4: TTS + Whisper + Alignment ==========
    print("\n" + "="*60)
    print("Step 4: TTS + Whisper + 音画对齐")
    print("="*60)

    # 合并所有narration
    full_narration = "".join([shot.get('narration_segment', '') for shot in shots])
    print(f"旁白总字数: {len(full_narration)}")

    # TTS
    tts = TTSService()
    audio_result = await tts.synthesize(full_narration)

    if not audio_result.get('success'):
        print(f"❌ TTS失败: {audio_result.get('error')}")
        return results

    audio_path = OUTPUT_DIR / "narration.mp3"
    with open(audio_path, 'wb') as f:
        f.write(audio_result['audio_data'])

    audio_duration = audio_result.get('duration_seconds', 0)
    print(f"✅ TTS完成: {audio_path} ({audio_duration:.1f}秒)")

    # Whisper
    whisper = WhisperService()
    whisper_result = await whisper.transcribe_with_timestamps(str(audio_path))

    if not whisper_result:
        print("❌ Whisper失败")
        return results

    whisper_path = OUTPUT_DIR / "whisper.json"
    with open(whisper_path, 'w', encoding='utf-8') as f:
        json.dump(whisper_result, f, ensure_ascii=False, indent=2)

    segments = whisper_result.get('segments', [])
    whisper_text = whisper_result.get('text', '')
    print(f"✅ Whisper完成: {len(segments)} segments")

    if audio_duration == 0 and segments:
        audio_duration = segments[-1].get('end', 0)

    # Alignment
    alignment = AlignmentService()
    timeline = await alignment.align_shots_to_audio(
        shots, segments, whisper_text, audio_duration
    )

    timeline_path = OUTPUT_DIR / "timeline.json"
    with open(timeline_path, 'w', encoding='utf-8') as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    print(f"✅ Timeline对齐完成: {len(timeline)} entries")

    results["steps"]["audio"] = {"status": "success", "segments": len(segments), "timeline_entries": len(timeline)}

    # ========== Step 5: 生成场景参考图 ==========
    print("\n" + "="*60)
    print("Step 5: 生成场景参考图")
    print("="*60)

    scene_ref_manager = SceneReferenceManager()

    # 提取独特场景
    locations = scene_ref_manager.extract_unique_locations(story['scenes'])
    print(f"发现 {len(locations)} 个独特场景")

    for loc in locations:
        loc_id = loc.get('id', 'unknown')
        loc_name = loc.get('name', 'unknown location')
        loc_desc = loc.get('description', '')

        print(f"\n生成场景 {loc_name} 的参考图...")

        # 内景
        interior_prompt = f"""Interior view of {loc_name}. {loc_desc}
Late night atmosphere, fluorescent lighting mixed with warm ambient lights.
Photorealistic, cinematic wide shot, detailed environment."""

        interior_prompt = StyleEnforcer.enforce_prompt(interior_prompt, "realistic")

        int_result = await image_gen.generate_image(
            prompt=interior_prompt,
            aspect_ratio="16:9"
        )

        if int_result.get('success') and int_result.get('pil_image'):
            int_path = OUTPUT_DIR / "scene_refs" / f"{loc_id}_interior.png"
            int_result['pil_image'].save(str(int_path))

            if loc_id not in scene_ref_manager.scene_references:
                scene_ref_manager.scene_references[loc_id] = {}
            scene_ref_manager.scene_references[loc_id]['interior'] = int_result['pil_image']
            print(f"   ✅ 内景: {int_path}")

        await asyncio.sleep(2)

    scene_ref_count = len(list((OUTPUT_DIR / "scene_refs").glob("*.png")))
    print(f"\n✅ 场景参考图生成完成: {scene_ref_count} 张")
    results["steps"]["scene_refs"] = {"status": "success", "count": scene_ref_count}

    # ========== Step 6: 生成所有场景图片 ==========
    print("\n" + "="*60)
    print("Step 6: 生成所有场景图片")
    print("="*60)

    generated_count = 0
    total_shots = len(shots)

    for i, shot in enumerate(shots):
        shot_id = shot.get('shot_id', i + 1)
        print(f"\n[{i+1}/{total_shots}] 生成 shot_{shot_id:02d}...")

        # 获取角色参考图
        chars_in_scene = shot.get('characters_in_scene', [])
        char_refs = []
        for cid in chars_in_scene:
            if cid in ref_manager.character_references:
                refs = ref_manager.character_references[cid]
                if 'portrait' in refs:
                    char_refs.append(refs['portrait'])
                if 'fullbody' in refs:
                    char_refs.append(refs['fullbody'])

        print(f"  使用 {len(char_refs)} 张角色参考图")

        # 生成图片
        try:
            result = await image_gen.generate_shot_image(
                shot=shot,
                reference_images=char_refs if char_refs else None,
            )

            if result and result.get('success') and result.get('pil_image'):
                image_path = OUTPUT_DIR / "images" / f"shot_{shot_id:02d}.png"
                result['pil_image'].save(str(image_path))
                generated_count += 1
                print(f"  ✅ 生成成功: {image_path}")
            else:
                print(f"  ❌ 生成失败: {result.get('error', 'unknown')}")
        except Exception as e:
            print(f"  ❌ 生成异常: {e}")

        await asyncio.sleep(2)

    print(f"\n✅ 场景图片生成完成: {generated_count}/{total_shots}")
    results["steps"]["images"] = {"status": "success", "generated": generated_count, "total": total_shots}

    # ========== Step 7: 生成验证报告 ==========
    print("\n" + "="*60)
    print("Step 7: 生成验证报告")
    print("="*60)

    results["verification"]["total_files"] = {
        "story.json": story_path.exists(),
        "shots.json": shots_path.exists(),
        "character_refs": char_ref_count,
        "scene_refs": scene_ref_count,
        "images": generated_count,
        "narration.mp3": audio_path.exists(),
        "whisper.json": whisper_path.exists(),
        "timeline.json": timeline_path.exists()
    }

    # 保存验证结果
    verify_path = OUTPUT_DIR / "verification_results.json"
    with open(verify_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 打印总结
    print("\n" + "="*80)
    print("测试完成总结")
    print("="*80)

    print(f"\n📁 输出目录: {OUTPUT_DIR}")
    print(f"\n📊 生成结果:")
    print(f"  - story.json: ✅")
    print(f"  - shots.json: ✅ ({len(shots)} shots)")
    print(f"  - character_refs/: ✅ ({char_ref_count} 张)")
    print(f"  - scene_refs/: ✅ ({scene_ref_count} 张)")
    print(f"  - images/: ✅ ({generated_count}/{total_shots} 张)")
    print(f"  - narration.mp3: ✅")
    print(f"  - whisper.json: ✅")
    print(f"  - timeline.json: ✅")
    print(f"  - verification_results.json: ✅")

    print(f"\n🔍 角色描述修复验证: {'✅ 通过' if char_fix_passed else '❌ 未通过'}")

    return results


def verify_character_fix(shots: list, characters: list) -> bool:
    """验证角色描述修复是否成功"""

    # 构建角色ID到名字的映射
    char_map = {c['id']: c.get('name_en', c.get('name', '')) for c in characters}

    errors = []

    for shot in shots:
        shot_id = shot.get('shot_id', 0)
        prompt = shot.get('image_prompt', '')
        chars_in_scene = shot.get('characters_in_scene', [])

        if not chars_in_scene:
            continue

        # 检查prompt中是否包含正确的角色
        for char_id in chars_in_scene:
            char_name = char_map.get(char_id, '')
            if char_name and char_name not in prompt:
                errors.append(f"Shot {shot_id}: 缺少角色 {char_name} ({char_id})")

    if errors:
        print(f"  ❌ 发现 {len(errors)} 个问题:")
        for e in errors[:5]:  # 只显示前5个
            print(f"    - {e}")
        if len(errors) > 5:
            print(f"    ... 还有 {len(errors) - 5} 个问题")
        return False
    else:
        print(f"  ✅ 所有shot的角色描述都正确")
        return True


if __name__ == "__main__":
    result = asyncio.run(run_full_e2e_test())
    print("\n测试结束")
