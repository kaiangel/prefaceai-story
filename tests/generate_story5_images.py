"""
继续teststory5的图片生成

读取已有的 story.json 和 shots.json，生成图片并输出最终统计
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.image_generator import ImageGenerator
from app.services.reference_image_manager import ReferenceImageManager
from app.services.character_prompt_builder import CharacterPromptBuilder
from app.models.style_config import StyleConfigBuilder


OUTPUT_DIR = "test_output/manualtest/teststory5_convenience_store"


async def generate_images():
    """生成图片"""
    print("\n" + "="*60)
    print("继续 teststory5 - 生成图片")
    print("="*60)

    # 读取已有数据
    with open(os.path.join(OUTPUT_DIR, "story.json"), 'r', encoding='utf-8') as f:
        story = json.load(f)

    with open(os.path.join(OUTPUT_DIR, "shots.json"), 'r', encoding='utf-8') as f:
        shots = json.load(f)

    # 创建图片目录
    images_dir = os.path.join(OUTPUT_DIR, "images")
    os.makedirs(images_dir, exist_ok=True)

    # 初始化服务
    image_gen = ImageGenerator()
    ref_manager = ReferenceImageManager()
    char_builder = CharacterPromptBuilder()

    # 构建项目风格
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

        # 检查是否已有参考图
        ref_path = os.path.join(char_refs_dir, f"{char_id}_reference.png")
        if os.path.exists(ref_path):
            print(f"  {char_name} 参考图已存在，跳过")
            continue

        print(f"  生成 {char_name} 参考图...")

        # 转换角色数据格式以兼容 CharacterPromptBuilder
        char_converted = convert_character_format(char)

        result = await ref_manager.generate_character_reference(
            character=char_converted,
            project_style=project_style,
            image_generator=image_gen
        )

        if result.get('success') and result.get('pil_image'):
            result['pil_image'].save(ref_path)
            print(f"    ✅ {char_name} 参考图已保存")

            char_ref_prompts[char_name] = {
                'char_id': char_id,
                'char_type': 'human',
                'reference_prompt': ref_manager._build_reference_prompt(
                    char_converted,
                    'human',
                    project_style
                ),
            }
        else:
            print(f"    ❌ {char_name} 参考图生成失败: {result.get('error')}")

        await asyncio.sleep(2)

    # 保存角色参考图prompt
    char_ref_prompts_path = os.path.join(OUTPUT_DIR, "character_ref_prompts.json")
    with open(char_ref_prompts_path, 'w', encoding='utf-8') as f:
        json.dump(char_ref_prompts, f, ensure_ascii=False, indent=2)

    # 生成shot图片（只生成前10张作为测试）
    print("\n生成Shot图片（前10张）...")
    images_log = []
    generated_count = 0

    max_shots = min(10, len(shots))  # 只生成10张

    for i, shot in enumerate(shots[:max_shots]):
        shot_id = f"shot_{shot.get('shot_id', i+1):02d}"

        # 检查是否已有图片
        image_path = os.path.join(images_dir, f"{shot_id}.png")
        if os.path.exists(image_path):
            print(f"  [{i+1}/{max_shots}] {shot_id} 已存在，跳过")
            generated_count += 1
            continue

        print(f"\n  [{i+1}/{max_shots}] 生成 {shot_id}...")

        # 获取shot中的角色 - 从 image_prompt 中解析角色名
        shot_chars = shot.get('characters_in_scene', [])

        # 如果 characters_in_scene 为空，尝试从 image_prompt 解析
        if not shot_chars:
            image_prompt = shot.get('image_prompt', '')
            for cid, cdata in characters.items():
                char_name = cdata.get('name', '')
                char_name_en = cdata.get('name_en', '')
                # 检查角色名或英文名是否出现在 prompt 中
                if char_name and char_name in image_prompt:
                    shot_chars.append(char_name)
                elif char_name_en and char_name_en in image_prompt:
                    shot_chars.append(char_name)

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
                char_converted = convert_character_format(char)
                char_desc = char_builder.build_character_prompt(char_converted)
                char_descriptions.append(f"{char['name']}: {char_desc}")

        # 组合prompt
        scene_desc = shot.get('visual_description', shot.get('image_prompt', ''))

        # 获取角色参考图
        ref_images = ref_manager.get_references_for_scene(char_ids)

        # 如果有参考图，添加明确指令让模型使用参考图中的角色外观
        if ref_images and char_descriptions:
            ref_instruction = f"""
IMPORTANT: Use the provided reference images to maintain character consistency.
The characters in this scene MUST match the appearance in the reference images exactly:
{chr(10).join(char_descriptions)}

Generate this scene with the SAME characters from the reference images:
"""
            full_prompt = f"""{ref_instruction}
{scene_desc}
Setting: late night convenience store, fluorescent lighting
{project_style.style_suffix}
realistic photography style, cinematic composition, dramatic lighting
"""
        else:
            full_prompt = f"""
{scene_desc}
Characters: {', '.join(char_descriptions) if char_descriptions else 'no specific characters'}
Setting: late night convenience store, fluorescent lighting
{project_style.style_suffix}
realistic photography style, cinematic composition, dramatic lighting
"""

        negative_prompt = "blurry, low quality, cartoon, anime, text, watermark, signature, animal features, furry"

        # 生成图片
        result = await image_gen.generate_image(
            prompt=full_prompt.strip(),
            negative_prompt=negative_prompt,
            aspect_ratio="16:9",
            reference_images=ref_images if ref_images else None
        )

        log_entry = {
            'shot_id': shot_id,
            'original_scene_id': shot.get('original_scene_id', ''),
            'prompt': full_prompt.strip()[:500],
            'characters': shot_chars,
            'character_ids': char_ids,
            'ref_images_used': len(ref_images) if ref_images else 0,
            'success': result.get('success', False),
            'timestamp': datetime.now().isoformat()
        }

        if result.get('success') and result.get('pil_image'):
            result['pil_image'].save(image_path)
            log_entry['image_path'] = image_path
            generated_count += 1
            print(f"    ✅ 已保存")
        else:
            log_entry['error'] = result.get('error', 'Unknown error')
            print(f"    ❌ 失败: {result.get('error')}")

        images_log.append(log_entry)
        await asyncio.sleep(3)

    # 保存图片日志
    images_log_path = os.path.join(OUTPUT_DIR, "images_log.json")
    with open(images_log_path, 'w', encoding='utf-8') as f:
        json.dump(images_log, f, ensure_ascii=False, indent=2)

    return story, shots, generated_count, max_shots


def convert_character_format(char):
    """转换角色数据格式以兼容 CharacterPromptBuilder"""
    # story_generator 生成的格式使用 physical 字段
    # CharacterPromptBuilder 期望使用 human 字段

    converted = dict(char)
    converted['character_type'] = 'human'

    physical = char.get('physical', {})
    clothing = char.get('clothing', {})

    if physical:
        # 构建完整的服装描述
        clothing_parts = []
        if clothing.get('top'):
            clothing_parts.append(clothing['top'])
        if clothing.get('bottom'):
            clothing_parts.append(clothing['bottom'])
        if clothing.get('footwear'):
            clothing_parts.append(clothing['footwear'])
        clothing_description = ', '.join(clothing_parts) if clothing_parts else ''

        # 保持 distinctive_marks 为列表格式，不要预先 join
        # 这样 CharacterPromptBuilder 中的 ', '.join(features) 才能正确工作
        distinctive_marks = physical.get('distinctive_marks', [])
        if isinstance(distinctive_marks, str):
            distinctive_marks = [distinctive_marks]

        converted['human'] = {
            'age_range': char.get('age_appearance', 'adult'),
            'gender': char.get('gender', 'unknown'),
            'skin_tone': physical.get('skin_tone', ''),
            'height': physical.get('height', ''),
            'body_type': physical.get('build', ''),
            'hair_color': physical.get('hair_color', ''),
            'hair_style': physical.get('hair_style', ''),
            'hair_length': 'medium',
            'eye_color': physical.get('eye_color', ''),
            'eye_shape': physical.get('eye_shape', ''),
            'face_shape': physical.get('face_shape', ''),
            'nose': physical.get('nose', ''),
            'mouth': physical.get('lips', ''),
            # 保持列表格式！
            'distinctive_features': distinctive_marks,
            'clothing_description': clothing_description,
            'accessories': clothing.get('accessories', []),
        }

    return converted


async def main():
    """主函数"""
    print(f"\n开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        story, shots, generated_count, max_shots = await generate_images()

        # 读取音频信息
        whisper_path = os.path.join(OUTPUT_DIR, "whisper_timestamps.json")
        audio_duration = 0
        if os.path.exists(whisper_path):
            with open(whisper_path, 'r') as f:
                whisper_data = json.load(f)
                audio_duration = whisper_data.get('duration', 0)

        # 最终报告
        print("\n" + "="*60)
        print("测试完成 - 最终报告")
        print("="*60)

        print(f"\n📊 故事统计:")
        print(f"   - 场景数 (scenes): {len(story.get('scenes', []))}")
        print(f"   - Shot数: {len(shots)}")

        print(f"\n🎵 音频统计:")
        print(f"   - 音频时长: {audio_duration:.2f}秒 ({audio_duration/60:.2f}分钟)")
        avg_shot_duration = audio_duration / len(shots) if shots else 0
        print(f"   - 平均Shot时长: {avg_shot_duration:.2f}秒")

        print(f"\n👥 角色描述 (3个人类角色):")
        for char in story.get('characters', []):
            char_type = char.get('type', 'human')
            print(f"\n   【{char.get('name')}】")
            print(f"   - 类型: {char_type}")
            print(f"   - 角色: {char.get('role', '')}")
            physical = char.get('physical', {})
            clothing = char.get('clothing', {})
            if physical:
                print(f"   - 年龄外观: {char.get('age_appearance', '')}")
                print(f"   - 性别: {char.get('gender', '')}")
                print(f"   - 发色: {physical.get('hair_color', '')}")
                print(f"   - 眼睛: {physical.get('eye_color', '')} {physical.get('eye_shape', '')}")
                print(f"   - 服装: {clothing.get('top', '')} + {clothing.get('bottom', '')}")
                marks = physical.get('distinctive_marks', [])
                if marks:
                    print(f"   - 特征: {', '.join(marks)}")

        print(f"\n🖼️  图片统计:")
        print(f"   - 生成成功: {generated_count}/{max_shots} (测试)")
        print(f"   - 总Shot数: {len(shots)}")

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
