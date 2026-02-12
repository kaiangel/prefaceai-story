#!/usr/bin/env python3
"""
teststory6.3.5 - 验证P1修复效果（scene_refs链式生成）

新增修复内容（相比6.3.4）：
- P1: SceneReferenceManager链式生成
  - 按场景类型分组（interior/exterior）
  - 每组第一张独立生成作为"锚点"
  - 同组后续图片使用第一张作为reference_image生成
  - 新增 _build_location_prompt_with_reference() 强调参考图一致性

验证重点：
1. scene_refs一致性：
   - 所有interior场景参考图应该看起来是同一家便利店内部
   - 所有exterior场景参考图应该看起来是同一家便利店外部
2. 角色外观一致性（继承自6.3.4）
3. 日志验证：应该看到"使用参考图生成"和"设为锚点图"的日志

输出目录: test_output/manualtest/teststory6.3.5/
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
from app.models.style_config import ProjectStyleConfig


# 输出目录
OUTPUT_DIR = Path("test_output/manualtest/teststory6.3.5")

# 故事配置（与teststory6.3.4完全相同）
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
    print("teststory6.3.5 - 验证P1修复效果（scene_refs链式生成）")
    print("="*80)
    print("\n新增修复内容（P1）：")
    print("  - SceneReferenceManager.generate_all_scene_references_chained()")
    print("  - 按场景类型分组（interior/exterior）")
    print("  - 每组第一张独立生成作为'锚点'")
    print("  - 同组后续图片使用锚点图作为reference_image生成")
    print("\n验证重点：")
    print("  1. scene_refs一致性: 所有interior看起来是同一家店内部")
    print("  2. scene_refs一致性: 所有exterior看起来是同一家店外部")
    print("  3. 日志验证: 应看到'使用参考图生成'和'设为锚点图'")
    print("="*80)

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "character_refs").mkdir(exist_ok=True)
    (OUTPUT_DIR / "scene_refs").mkdir(exist_ok=True)
    (OUTPUT_DIR / "images").mkdir(exist_ok=True)

    results = {
        "test_name": "teststory6.3.5",
        "description": "验证P1修复效果（scene_refs链式生成）",
        "fixes_tested": [
            "P1: SceneReferenceManager链式生成",
            "按类型分组: interior/exterior",
            "锚点图机制: 第一张独立生成，后续使用参考图"
        ],
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

    # ========== Step 5: 生成场景参考图（链式生成 - P1修复核心） ==========
    print("\n" + "="*60)
    print("Step 5: 生成场景参考图（链式生成 - P1修复核心）")
    print("="*60)
    print("📎 关键改动: 使用generate_all_scene_references_chained()")
    print("   - 按类型分组（interior/exterior）")
    print("   - 第一张作为锚点，后续使用参考图生成")

    scene_ref_manager = SceneReferenceManager()
    style_config = ProjectStyleConfig(style_preset="realistic")

    # ===== P1修复核心：使用链式生成 =====
    scene_results = await scene_ref_manager.generate_all_scene_references_chained(
        scenes=story['scenes'],
        project_style=style_config,
        image_generator=image_gen,
        delay=3.0
    )

    # 保存所有场景参考图
    saved_paths = scene_ref_manager.save_all_references(str(OUTPUT_DIR / "scene_refs"))

    # 构建scene到location的映射，供Step 6使用
    scene_to_location = {}
    for scene in story['scenes']:
        location_name = (
            scene.get('location', '') or
            scene.get('setting', '') or
            scene.get('location_name', '')
        )
        if location_name:
            location_id = scene_ref_manager._normalize_location_id(location_name)
            scene_id = scene.get('scene_id')
            if scene_id:
                scene_to_location[scene_id] = location_id

    scene_ref_count = len(list((OUTPUT_DIR / "scene_refs").glob("*.png")))
    print(f"\n✅ 场景参考图生成完成: {scene_ref_count} 张")
    print(f"  场景到location映射: {scene_to_location}")
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

        print(f"  角色参考图: {len(char_refs)} 张")

        # 获取场景参考图
        scene_refs = []
        original_scene_id = shot.get('original_scene_id')
        if original_scene_id:
            location_id = scene_to_location.get(original_scene_id)
            if location_id and location_id in scene_ref_manager.scene_references:
                scene_refs = scene_ref_manager.get_references_for_location(location_id)
                print(f"  场景参考图: {len(scene_refs)} 张 (location: {location_id})")
            else:
                print(f"  场景参考图: 0 张 (未找到location: {location_id})")
        else:
            print(f"  场景参考图: 0 张 (无original_scene_id)")

        # 合并参考图 - 角色参考图优先级更高（放前面）
        all_refs = char_refs + scene_refs
        print(f"  总参考图: {len(all_refs)} 张")

        # 生成图片
        try:
            result = await image_gen.generate_shot_image(
                shot=shot,
                reference_images=all_refs if all_refs else None,
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

    print("\n" + "="*80)
    print("🔍 请手动验证以下关键点（P1修复核心验证）：")
    print("="*80)
    print("  1. scene_refs/目录: 所有interior图是否像同一家店内部？")
    print("     - 墙面颜色是否一致？")
    print("     - 货架布局是否一致？")
    print("     - 灯具样式是否一致？")
    print("  2. scene_refs/目录: 所有exterior图是否像同一家店外部？")
    print("     - 招牌样式是否一致？")
    print("     - 建筑风格是否一致？")
    print("     - 台阶设计是否一致？")
    print("  3. 日志检查: 是否看到了以下日志？")
    print('     - "🎨 首次生成 XXX，作为参考基准"')
    print('     - "🔗 设为interior/exterior锚点图"')
    print('     - "📸 使用参考图生成 XXX，确保场景一致性"')
    print("="*80)

    return results


if __name__ == "__main__":
    result = asyncio.run(run_full_e2e_test())
    print("\n测试结束")
