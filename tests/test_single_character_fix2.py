"""
单角色风格一致性测试2 - 全部使用 gemini-2.5-flash-image

验证 Flash 模型是否也能支持参考图并保持一致性
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
from app.services.style_enforcer import StyleEnforcer
from app.models.style_config import ProjectStyleConfig


OUTPUT_DIR = "test_output/manualtest/single_char_fix_test2"


def create_test_character():
    """创建测试角色数据（林宇）"""
    return {
        "id": "char_001",
        "name": "林宇",
        "name_en": "Lin Yu",
        "role": "protagonist",
        "type": "human",
        "gender": "male",
        "age_appearance": "young_adult",
        "personality_visual": "tired but warm",
        "default_expression": "gentle tired smile",
        "character_type": "human",
        "human": {
            "age_range": "young_adult",
            "gender": "male",
            "skin_tone": "fair",
            "height": "medium",
            "body_type": "average",
            "face_shape": "oval",
            "eye_shape": "almond",
            "eye_color": "dark brown",
            "eye_size": "medium",
            "nose_type": "straight",
            "lip_shape": "medium",
            "jawline": "soft",
            "cheekbones": "subtle",
            "eyebrows": "natural",
            "hair_color": "jet black",
            "hair_style": "short messy",
            "hair_length": "short",
            "distinctive_features": ["dark circles under eyes", "gentle tired expression"],
            "clothing_description": "gray hoodie, dark pants, white sneakers",
            "accessories": []
        }
    }


def create_test_style():
    """创建测试风格配置（写实风格）"""
    return ProjectStyleConfig(
        style_preset="realistic",
        color_palette="neutral",
        dominant_colors=["gray", "white", "fluorescent"],
        lighting_style="cinematic",
        detail_level="detailed",
        rendering="sharp",
        style_suffix="photorealistic, cinematic lighting, detailed textures, lifelike, 8K quality"
    )


async def test_single_character():
    """测试单角色生成（全部使用Flash模型）"""
    print("\n" + "=" * 60)
    print("测试: 单角色参考图生成（全部使用 gemini-2.5-flash-image）")
    print("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    char_refs_dir = os.path.join(OUTPUT_DIR, "character_refs")
    os.makedirs(char_refs_dir, exist_ok=True)

    # 创建测试数据
    character = create_test_character()
    project_style = create_test_style()

    # 初始化服务
    image_gen = ImageGenerator()
    ref_manager = ReferenceImageManager()

    print(f"\n角色: {character['name']} ({character['name_en']})")
    print(f"风格: {project_style.style_preset}")
    print(f"模型: gemini-2.5-flash-image (全部)")

    # 生成多参考图（肖像+全身，串行）
    print("\n开始生成参考图...")
    results = await ref_manager.generate_character_multi_refs(
        character=character,
        project_style=project_style,
        image_generator=image_gen,
        delay=3.0
    )

    # 保存结果
    success_count = 0
    for ref_type, result in results.items():
        if result.get('success') and result.get('pil_image'):
            ref_path = os.path.join(char_refs_dir, f"{character['id']}_{ref_type}.png")
            result['pil_image'].save(ref_path)
            print(f"  ✅ {ref_type} 已保存: {ref_path}")
            success_count += 1
        else:
            print(f"  ❌ {ref_type} 生成失败: {result.get('error')}")

    print(f"\n参考图生成结果: {success_count}/2 成功")
    return ref_manager, character, project_style, success_count == 2


async def test_scene_image(ref_manager, character, project_style):
    """测试场景图生成（使用参考图）"""
    print("\n" + "=" * 60)
    print("测试: 场景图生成（使用角色参考图，Flash模型）")
    print("=" * 60)

    images_dir = os.path.join(OUTPUT_DIR, "images")
    os.makedirs(images_dir, exist_ok=True)

    image_gen = ImageGenerator()

    # 获取参考图
    char_refs = ref_manager.get_references_for_scene([character['id']])
    print(f"使用 {len(char_refs)} 张角色参考图")

    # 构建简化的角色描述
    char_desc = f"""CHARACTER "{character['name']}" ({character['name_en']}):
- Reference: See provided reference images #1 (portrait) and #2 (fullbody)
- Key identifiers: young Asian male, messy black hair, gray hoodie, dark circles under eyes
- This character's face MUST match the provided reference images EXACTLY"""

    # 构建场景描述
    scene_desc = f"""
SCENE: Late night convenience store interior

CHARACTERS IN THIS SCENE:
{char_desc}

SCENE DESCRIPTION:
A young man ({character['name']}) standing alone in the snack aisle of a brightly lit
convenience store at night. He is looking at the shelves with a tired but contemplative
expression. Fluorescent lights illuminate the scene from above.

COMPOSITION:
- Medium shot, showing the character from waist up
- Character positioned in the left third of frame
- Convenience store shelves visible in background
- Late night atmosphere, fluorescent lighting

The character's face MUST match the provided portrait reference image exactly.
Same person, same facial features, same hairstyle.
"""

    # 应用风格强制
    style_name = project_style.style_preset
    full_prompt = StyleEnforcer.enforce_prompt(scene_desc.strip(), style_name)
    negative_prompt = StyleEnforcer.build_style_negative_prompt(style_name)
    negative_prompt += ", different face, inconsistent appearance, wrong hairstyle, different person"

    print("\n生成场景图...")

    result = await image_gen.generate_image(
        prompt=full_prompt,
        negative_prompt=negative_prompt,
        aspect_ratio="16:9",
        reference_images=char_refs if char_refs else None
    )

    if result.get('success') and result.get('pil_image'):
        scene_path = os.path.join(images_dir, "scene_01.png")
        result['pil_image'].save(scene_path)
        print(f"✅ 场景图已保存: {scene_path}")
        return True
    else:
        print(f"❌ 场景图生成失败: {result.get('error')}")
        return False


async def main():
    print(f"\n{'=' * 60}")
    print("单角色风格一致性测试2 - Flash模型")
    print(f"{'=' * 60}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"模型: gemini-2.5-flash-image (全部)")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        # 测试1: 单角色参考图生成
        ref_manager, character, project_style, refs_ok = await test_single_character()

        if refs_ok:
            # 测试2: 场景图生成
            await asyncio.sleep(3)
            scene_ok = await test_scene_image(ref_manager, character, project_style)
        else:
            scene_ok = False
            print("\n⚠️ 跳过场景图测试（参考图生成失败）")

        # 输出总结
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)

        print(f"\n📁 输出目录: {OUTPUT_DIR}")
        print(f"\n📊 结果:")
        print(f"  - 角色参考图: {'✅' if refs_ok else '❌'}")
        print(f"  - 场景图: {'✅' if scene_ok else '❌'}")

        if refs_ok and scene_ok:
            print(f"\n🎉 所有测试通过！")
            print(f"\n请检查以下文件：")
            print(f"  1. {OUTPUT_DIR}/character_refs/char_001_portrait.png - 肖像参考图")
            print(f"  2. {OUTPUT_DIR}/character_refs/char_001_fullbody.png - 全身参考图")
            print(f"  3. {OUTPUT_DIR}/images/scene_01.png - 场景图")

    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
