"""
增强版角色一致性测试

测试内容：
1. 生成3个角色各2张参考图（肖像+全身）= 6张
2. 生成2张场景参考图（便利店外观+内部）= 2张
3. 重新生成前10张场景图，使用增强的一致性指令
4. 输出对比报告
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
from app.services.scene_reference_manager import SceneReferenceManager
from app.services.character_prompt_builder import CharacterPromptBuilder
from app.models.style_config import StyleConfigBuilder


INPUT_DIR = "test_output/manualtest/teststory5_convenience_store"
OUTPUT_DIR = "test_output/manualtest/enhanced_consistency_test"


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
            # 增强的面部特征
            'face_shape': physical.get('face_shape', ''),
            'eye_shape': physical.get('eye_shape', ''),
            'eye_color': physical.get('eye_color', ''),
            'eye_size': physical.get('eye_size', 'medium'),
            'nose_type': physical.get('nose', ''),
            'lip_shape': physical.get('lips', ''),
            'jawline': physical.get('jawline', ''),
            'cheekbones': physical.get('cheekbones', ''),
            'eyebrows': physical.get('eyebrows', ''),
            # 头发
            'hair_color': physical.get('hair_color', ''),
            'hair_style': physical.get('hair_style', ''),
            'hair_length': 'medium',
            # 服装和特征
            'distinctive_features': distinctive_marks,
            'clothing_description': clothing_description,
            'accessories': clothing.get('accessories', []),
        }

    return converted


async def generate_character_refs():
    """生成角色参考图（肖像+全身）"""
    print("\n" + "=" * 60)
    print("步骤1: 生成角色参考图（肖像+全身）")
    print("=" * 60)

    # 读取故事数据
    with open(os.path.join(INPUT_DIR, "story.json"), 'r', encoding='utf-8') as f:
        story = json.load(f)

    # 创建输出目录
    char_refs_dir = os.path.join(OUTPUT_DIR, "character_refs")
    os.makedirs(char_refs_dir, exist_ok=True)

    # 初始化服务
    image_gen = ImageGenerator()
    ref_manager = ReferenceImageManager()
    style_builder = StyleConfigBuilder()
    project_style = style_builder.build_from_story(story)

    # 为每个角色生成2张参考图
    for i, char in enumerate(story.get('characters', [])):
        char_converted = convert_character_format(char)
        char_name = char['name']
        char_id = char['id']

        print(f"\n  [{i+1}/{len(story['characters'])}] 角色: {char_name}")

        # 使用新的 generate_character_multi_refs 方法
        results = await ref_manager.generate_character_multi_refs(
            character=char_converted,
            project_style=project_style,
            image_generator=image_gen,
            delay=3.0
        )

        # 保存参考图
        for ref_type, result in results.items():
            if result.get('success') and result.get('pil_image'):
                ref_path = os.path.join(char_refs_dir, f"{char_id}_{ref_type}.png")
                result['pil_image'].save(ref_path)
                print(f"    保存: {ref_path}")

        await asyncio.sleep(2)

    return ref_manager, story, project_style


async def generate_scene_refs(story, project_style):
    """生成场景参考图"""
    print("\n" + "=" * 60)
    print("步骤2: 生成场景参考图（外观+内部）")
    print("=" * 60)

    scene_refs_dir = os.path.join(OUTPUT_DIR, "scene_refs")
    os.makedirs(scene_refs_dir, exist_ok=True)

    image_gen = ImageGenerator()
    scene_manager = SceneReferenceManager()

    # 手动定义便利店场景（因为 story.json 可能没有详细的场景位置信息）
    convenience_store = {
        'id': 'convenience_store',
        'name': '24-hour convenience store',
        'description': 'A modern 24-hour convenience store with bright fluorescent lighting, typical Asian convenience store layout with refrigerated beverage shelves, snack aisles, and a checkout counter',
        'type': 'both',
        'time_of_day': 'late night',
        'atmosphere': 'quiet, slightly lonely',
        'lighting': 'bright fluorescent'
    }

    print(f"\n  生成便利店参考图...")

    # 生成外景
    print(f"    生成外景...")
    exterior_result = await scene_manager.generate_location_reference(
        location=convenience_store,
        project_style=project_style,
        image_generator=image_gen,
        view_types=['exterior']
    )

    if exterior_result.get('exterior', {}).get('success'):
        ext_path = os.path.join(scene_refs_dir, "convenience_store_exterior.png")
        exterior_result['exterior']['pil_image'].save(ext_path)
        print(f"    ✅ 外景已保存: {ext_path}")
    else:
        print(f"    ❌ 外景生成失败: {exterior_result.get('exterior', {}).get('error')}")

    await asyncio.sleep(3)

    # 生成内景
    print(f"    生成内景...")
    interior_result = await scene_manager.generate_location_reference(
        location=convenience_store,
        project_style=project_style,
        image_generator=image_gen,
        view_types=['interior']
    )

    if interior_result.get('interior', {}).get('success'):
        int_path = os.path.join(scene_refs_dir, "convenience_store_interior.png")
        interior_result['interior']['pil_image'].save(int_path)
        print(f"    ✅ 内景已保存: {int_path}")
    else:
        print(f"    ❌ 内景生成失败: {interior_result.get('interior', {}).get('error')}")

    return scene_manager


async def generate_scene_images(ref_manager, scene_manager, story, project_style):
    """生成场景图（使用增强的一致性指令）"""
    print("\n" + "=" * 60)
    print("步骤3: 生成场景图（增强一致性）")
    print("=" * 60)

    # 读取shots数据
    with open(os.path.join(INPUT_DIR, "shots.json"), 'r', encoding='utf-8') as f:
        shots = json.load(f)

    images_dir = os.path.join(OUTPUT_DIR, "images")
    os.makedirs(images_dir, exist_ok=True)

    image_gen = ImageGenerator()
    char_builder = CharacterPromptBuilder()
    characters = {char['id']: char for char in story.get('characters', [])}

    images_log = []
    max_shots = min(10, len(shots))

    # 获取场景参考图
    scene_refs = scene_manager.get_references_for_location('convenience_store')
    print(f"\n  场景参考图数量: {len(scene_refs)}")

    for i, shot in enumerate(shots[:max_shots]):
        shot_id = f"shot_{shot.get('shot_id', i+1):02d}"
        image_path = os.path.join(images_dir, f"{shot_id}.png")

        print(f"\n  [{i+1}/{max_shots}] 生成 {shot_id}...")

        # 从 image_prompt 解析角色
        shot_chars = []
        image_prompt = shot.get('image_prompt', '')
        for cid, cdata in characters.items():
            char_name = cdata.get('name', '')
            if char_name and char_name in image_prompt:
                shot_chars.append(char_name)

        # 获取角色ID
        char_ids = []
        for char_name in shot_chars:
            for cid, cdata in characters.items():
                if cdata.get('name') == char_name:
                    char_ids.append(cid)
                    break

        # 构建角色描述
        char_descriptions = []
        for char_id in char_ids:
            if char_id in characters:
                char = characters[char_id]
                char_converted = convert_character_format(char)
                char_desc = char_builder.build_character_prompt(char_converted)
                char_descriptions.append(f"{char['name']}: {char_desc}")

        # 获取角色参考图
        char_refs = ref_manager.get_references_for_scene(char_ids)

        # 组合所有参考图：场景 + 角色
        all_refs = scene_refs + char_refs

        print(f"    角色: {shot_chars}")
        print(f"    参考图总数: {len(all_refs)} (场景:{len(scene_refs)}, 角色:{len(char_refs)})")

        # 构建增强的prompt
        scene_desc = shot.get('visual_description', shot.get('image_prompt', ''))

        # 增强的一致性指令
        consistency_instruction = """
CRITICAL CONSISTENCY REQUIREMENTS:
1. The character faces MUST exactly match the reference portrait images provided
2. The environment MUST exactly match the location reference images provided
3. Maintain the SAME facial features, hairstyle, and clothing as references
4. Keep the SAME architectural details, lighting, and color scheme as location reference

"""
        if char_descriptions:
            char_section = f"""
CHARACTERS IN THIS SCENE (must match reference images EXACTLY):
{chr(10).join(char_descriptions)}

Each character has the EXACT SAME face as shown in their portrait reference image.
"""
        else:
            char_section = ""

        full_prompt = f"""{consistency_instruction}
{char_section}
SCENE DESCRIPTION:
{scene_desc}

SETTING: late night convenience store, bright fluorescent lighting
This scene takes place in the SAME convenience store shown in the location reference images.

{project_style.style_suffix}
photorealistic photography, cinematic composition, dramatic lighting
"""

        negative_prompt = "blurry, low quality, cartoon, anime, text, watermark, signature, animal features, furry, different face, inconsistent appearance, different location"

        # 生成图片
        result = await image_gen.generate_image(
            prompt=full_prompt.strip(),
            negative_prompt=negative_prompt,
            aspect_ratio="16:9",
            reference_images=all_refs if all_refs else None
        )

        log_entry = {
            'shot_id': shot_id,
            'characters': shot_chars,
            'character_ids': char_ids,
            'scene_refs_used': len(scene_refs),
            'char_refs_used': len(char_refs),
            'total_refs_used': len(all_refs),
            'success': result.get('success', False),
            'timestamp': datetime.now().isoformat()
        }

        if result.get('success') and result.get('pil_image'):
            result['pil_image'].save(image_path)
            log_entry['image_path'] = image_path
            print(f"    ✅ 已保存")
        else:
            log_entry['error'] = result.get('error', 'Unknown error')
            print(f"    ❌ 失败: {result.get('error')}")

        images_log.append(log_entry)
        await asyncio.sleep(3)

    # 保存日志
    log_path = os.path.join(OUTPUT_DIR, "images_log.json")
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(images_log, f, ensure_ascii=False, indent=2)

    return images_log


async def main():
    print(f"\n{'='*60}")
    print("增强版角色一致性测试")
    print(f"{'='*60}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        # 步骤1: 生成角色参考图
        ref_manager, story, project_style = await generate_character_refs()

        # 步骤2: 生成场景参考图
        scene_manager = await generate_scene_refs(story, project_style)

        # 步骤3: 生成场景图
        images_log = await generate_scene_images(ref_manager, scene_manager, story, project_style)

        # 输出报告
        print("\n" + "=" * 60)
        print("测试完成 - 报告")
        print("=" * 60)

        success_count = sum(1 for log in images_log if log['success'])
        print(f"\n📊 统计:")
        print(f"   - 角色参考图: 3角色 x 2张 = 6张")
        print(f"   - 场景参考图: 2张 (外观+内部)")
        print(f"   - 场景图: {success_count}/{len(images_log)} 成功")

        print(f"\n📁 输出文件:")
        print(f"   - 角色参考图: {OUTPUT_DIR}/character_refs/")
        print(f"   - 场景参考图: {OUTPUT_DIR}/scene_refs/")
        print(f"   - 场景图: {OUTPUT_DIR}/images/")
        print(f"   - 日志: {OUTPUT_DIR}/images_log.json")

        print(f"\n⚡ 改进措施:")
        print(f"   1. 每个角色生成肖像+全身两张参考图")
        print(f"   2. 生成场景参考图（外观+内部）")
        print(f"   3. 场景图生成时传入所有参考图")
        print(f"   4. 增强的一致性指令prompt")

        print(f"\n请对比以下目录的图片:")
        print(f"   修复前: test_output/manualtest/teststory5_convenience_store/")
        print(f"   修复后: {OUTPUT_DIR}/")

    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
