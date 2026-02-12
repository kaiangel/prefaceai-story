"""
测试角色一致性修复

只生成2-3张有角色的场景图，验证：
1. distinctive_features 不再被逐字符拆分
2. 服装描述被正确包含
3. 参考图被正确传入 API
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
TEST_OUTPUT_DIR = "test_output/manualtest/consistency_test"


def convert_character_format(char):
    """转换角色数据格式以兼容 CharacterPromptBuilder"""
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

        # 保持 distinctive_marks 为列表格式
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
            'distinctive_features': distinctive_marks,  # 保持列表格式！
            'clothing_description': clothing_description,
            'accessories': clothing.get('accessories', []),
        }

    return converted


async def test_character_prompt():
    """测试角色prompt生成"""
    print("=" * 60)
    print("测试1: 角色 Prompt 生成")
    print("=" * 60)

    with open(os.path.join(OUTPUT_DIR, "story.json"), 'r', encoding='utf-8') as f:
        story = json.load(f)

    char_builder = CharacterPromptBuilder()

    for char in story.get('characters', []):
        char_converted = convert_character_format(char)
        prompt = char_builder.build_character_prompt(char_converted)

        print(f"\n【{char['name']}】")
        print(f"原始 distinctive_marks: {char.get('physical', {}).get('distinctive_marks', [])}")
        print(f"转换后 distinctive_features: {char_converted.get('human', {}).get('distinctive_features', [])}")
        print(f"原始 clothing: {char.get('clothing', {})}")
        print(f"转换后 clothing_description: {char_converted.get('human', {}).get('clothing_description', '')}")
        print(f"\n生成的 Prompt:\n{prompt}")
        print("-" * 40)

        # 验证 distinctive_features 没有被拆分
        if 'd, a, r, k' in prompt:
            print("❌ BUG: distinctive_features 被逐字符拆分了!")
        else:
            print("✅ distinctive_features 正确格式化")

        # 验证服装描述存在
        clothing = char.get('clothing', {})
        if clothing.get('top') and clothing['top'] not in prompt:
            print(f"❌ BUG: 服装描述 '{clothing['top']}' 没有出现在 prompt 中!")
        else:
            print("✅ 服装描述已包含")


async def test_reference_image_generation():
    """测试参考图生成"""
    print("\n" + "=" * 60)
    print("测试2: 参考图生成 (只生成1个角色)")
    print("=" * 60)

    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

    with open(os.path.join(OUTPUT_DIR, "story.json"), 'r', encoding='utf-8') as f:
        story = json.load(f)

    image_gen = ImageGenerator()
    ref_manager = ReferenceImageManager()
    style_builder = StyleConfigBuilder()
    project_style = style_builder.build_from_story(story)

    # 只测试第一个角色
    char = story['characters'][0]
    char_converted = convert_character_format(char)

    print(f"\n生成 {char['name']} 的参考图...")

    result = await ref_manager.generate_character_reference(
        character=char_converted,
        project_style=project_style,
        image_generator=image_gen
    )

    if result.get('success') and result.get('pil_image'):
        ref_path = os.path.join(TEST_OUTPUT_DIR, f"{char['id']}_reference_v2.png")
        result['pil_image'].save(ref_path)
        print(f"✅ 参考图已保存: {ref_path}")

        # 获取并保存生成时用的 prompt
        char_builder = CharacterPromptBuilder()
        char_desc = char_builder.build_character_prompt(char_converted)
        print(f"\n参考图使用的角色描述:\n{char_desc[:500]}...")

        return char['id'], result['pil_image'], char_converted
    else:
        print(f"❌ 参考图生成失败: {result.get('error')}")
        return None, None, None


async def test_scene_with_reference(char_id, ref_image, char_converted):
    """测试使用参考图生成场景"""
    print("\n" + "=" * 60)
    print("测试3: 使用参考图生成场景")
    print("=" * 60)

    if not ref_image:
        print("跳过：没有参考图")
        return

    with open(os.path.join(OUTPUT_DIR, "story.json"), 'r', encoding='utf-8') as f:
        story = json.load(f)

    style_builder = StyleConfigBuilder()
    project_style = style_builder.build_from_story(story)

    char_builder = CharacterPromptBuilder()
    char_desc = char_builder.build_character_prompt(char_converted)

    image_gen = ImageGenerator()

    # 简单场景测试
    scene_desc = "A young man in a gray hoodie standing in front of refrigerated beverage shelves in a convenience store, looking at the energy drinks. Bright fluorescent lighting, late night atmosphere."

    full_prompt = f"""
IMPORTANT: Use the provided reference image to maintain character consistency.
The character in this scene MUST match the appearance in the reference image exactly:
{char_desc}

Generate this scene with the SAME character from the reference image:
{scene_desc}
Setting: late night convenience store, fluorescent lighting
{project_style.style_suffix}
realistic photography style, cinematic composition, dramatic lighting
"""

    print(f"\n场景 Prompt (前800字符):\n{full_prompt[:800]}...")
    print(f"\n传入参考图数量: 1")

    result = await image_gen.generate_image(
        prompt=full_prompt.strip(),
        negative_prompt="blurry, low quality, cartoon, anime, text, watermark, signature, animal features, furry",
        aspect_ratio="16:9",
        reference_images=[ref_image]
    )

    if result.get('success') and result.get('pil_image'):
        scene_path = os.path.join(TEST_OUTPUT_DIR, "scene_with_ref_v2.png")
        result['pil_image'].save(scene_path)
        print(f"✅ 场景图已保存: {scene_path}")
        print(f"   模型使用: {result.get('model_used')}")
        print(f"   生成时间: {result.get('generation_time_seconds')}秒")
    else:
        print(f"❌ 场景图生成失败: {result.get('error')}")


async def main():
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 测试1: 角色 Prompt 生成
        await test_character_prompt()

        # 测试2: 参考图生成
        char_id, ref_image, char_converted = await test_reference_image_generation()

        # 测试3: 使用参考图生成场景
        await test_scene_with_reference(char_id, ref_image, char_converted)

        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
        print(f"\n请检查 {TEST_OUTPUT_DIR}/ 目录下的图片")
        print("对比 v2 版本和之前的版本，看角色一致性是否有改善")

    except Exception as e:
        print(f"❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
