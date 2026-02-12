"""
简化场景图生成测试 - 跳过分镜/TTS/Whisper步骤

直接使用已生成的story.json和character_refs来生成场景图
专注测试角色一致性
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
from app.services.style_enforcer import StyleEnforcer
from app.models.style_config import StyleConfigBuilder


# 使用之前生成的故事和角色参考图
INPUT_DIR = "test_output/manualtest/teststory5_flash"
OUTPUT_DIR = INPUT_DIR  # 在同一目录输出


async def load_story_data():
    """加载已生成的故事数据"""
    story_path = os.path.join(INPUT_DIR, "story.json")
    with open(story_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_character_refs(story_data, ref_manager):
    """加载已生成的角色参考图到ref_manager"""
    refs_dir = os.path.join(INPUT_DIR, "character_refs")
    characters = story_data.get('characters', [])

    from PIL import Image

    for char in characters:
        char_id = char.get('id')
        if not char_id:
            continue

        # 加载肖像
        portrait_path = os.path.join(refs_dir, f"{char_id}_portrait.png")
        if os.path.exists(portrait_path):
            portrait_img = Image.open(portrait_path)
            ref_manager.add_reference(char_id, portrait_img, 'portrait')
            print(f"  ✅ 加载 {char_id} 肖像参考图")

        # 加载全身
        fullbody_path = os.path.join(refs_dir, f"{char_id}_fullbody.png")
        if os.path.exists(fullbody_path):
            fullbody_img = Image.open(fullbody_path)
            ref_manager.add_reference(char_id, fullbody_img, 'fullbody')
            print(f"  ✅ 加载 {char_id} 全身参考图")


async def generate_scene_images(story_data, ref_manager, max_images=10):
    """生成场景图"""
    print("\n" + "=" * 70)
    print(f"生成场景图（前{max_images}张，全部使用Flash）")
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

    # 风格
    style_name = "realistic"

    scenes = story_data.get('scenes', [])
    generated_count = 0

    for i, scene in enumerate(scenes[:max_images]):
        scene_id = scene.get('scene_id', i + 1)
        print(f"\n[{i+1}/{min(len(scenes), max_images)}] 生成场景图 scene_{scene_id:02d}...")

        # 获取场景中的角色列表
        chars_in_scene = scene.get('characters_in_scene', [])

        # 如果没有角色列表，从visual_description中推断
        if not chars_in_scene:
            visual_desc = scene.get('visual_description', '')
            narration = scene.get('narration', '')
            combined_text = f"{visual_desc} {narration}"

            for char in characters:
                char_name = char.get('name', '')
                char_name_en = char.get('name_en', '')
                char_id = char.get('id')

                if char_id and (char_name in combined_text or char_name_en in combined_text):
                    if char_id not in chars_in_scene:
                        chars_in_scene.append(char_id)

        # 显示角色
        char_names = [char_map.get(cid, {}).get('name', cid) for cid in chars_in_scene]
        print(f"   场景角色: {char_names if char_names else '无'}")

        # 获取角色参考图
        char_refs = ref_manager.get_references_for_scene(chars_in_scene) if chars_in_scene else []
        print(f"   使用 {len(char_refs)} 张角色参考图")

        # 构建角色描述（简化版，索引引用）
        char_descriptions = []
        ref_index = 1
        for char_id in chars_in_scene:
            char = char_map.get(char_id)
            if char:
                char_name = char.get('name', '')
                char_name_en = char.get('name_en', '')

                # 获取关键识别特征
                physical = char.get('physical', {})
                clothing = char.get('clothing', {})

                key_features = []
                if char.get('gender'):
                    key_features.append(char['gender'])
                if physical.get('hair_color') and physical.get('hair_style'):
                    key_features.append(f"{physical['hair_color']} {physical['hair_style']} hair")
                if clothing.get('top'):
                    key_features.append(clothing['top'][:50])  # 截断过长的服装描述

                features_str = ", ".join(key_features) if key_features else ""

                char_desc = f"""CHARACTER "{char_name}" ({char_name_en}):
- Reference: See provided reference images #{ref_index} (portrait) and #{ref_index+1} (fullbody)
- Key identifiers: {features_str}
- This character's face MUST match the provided reference images EXACTLY"""
                char_descriptions.append(char_desc)
                ref_index += 2

        # 获取场景描述
        visual_desc = scene.get('visual_description', '')
        location = scene.get('location', '')
        narration = scene.get('narration', '')

        # 构建完整prompt
        scene_prompt = f"""SCENE IMAGE - Scene {scene_id}

{"CHARACTERS IN THIS SCENE:" if char_descriptions else ""}
{chr(10).join(char_descriptions) if char_descriptions else "No characters in this shot."}

SCENE DESCRIPTION:
{visual_desc}

LOCATION: {location}
NARRATIVE CONTEXT: {narration[:100]}...

COMPOSITION:
- Cinematic shot composition
- Characters must match their reference images exactly
- Maintain consistent lighting and atmosphere

{"Each character's face MUST match their provided portrait reference image exactly." if char_descriptions else ""}
"""

        # 应用风格强制
        full_prompt = StyleEnforcer.enforce_prompt(scene_prompt.strip(), style_name)
        negative_prompt = StyleEnforcer.build_style_negative_prompt(style_name)
        negative_prompt += ", different face, inconsistent appearance, wrong hairstyle, different person, wrong clothing"

        # 生成图像
        result = await image_gen.generate_image(
            prompt=full_prompt,
            negative_prompt=negative_prompt,
            aspect_ratio="16:9",
            reference_images=char_refs if char_refs else None
        )

        if result.get('success') and result.get('pil_image'):
            img_path = os.path.join(images_dir, f"scene_{scene_id:02d}.png")
            result['pil_image'].save(img_path)
            print(f"   ✅ 已保存: {img_path}")
            generated_count += 1
        else:
            print(f"   ❌ 生成失败: {result.get('error')}")

        # 等待避免速率限制
        if i < min(len(scenes), max_images) - 1:
            await asyncio.sleep(3)

    print(f"\n📊 场景图生成完成: {generated_count}/{min(len(scenes), max_images)}")
    return generated_count


async def main():
    print(f"\n{'=' * 70}")
    print("简化场景图生成测试 - 使用已有的故事和角色参考图")
    print(f"{'=' * 70}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"输入目录: {INPUT_DIR}")

    try:
        # 加载故事数据
        print("\n加载故事数据...")
        story_data = await load_story_data()
        print(f"✅ 故事: {story_data.get('title', '未命名')}")
        print(f"   场景数: {len(story_data.get('scenes', []))}")
        print(f"   角色数: {len(story_data.get('characters', []))}")

        # 加载角色参考图
        print("\n加载角色参考图...")
        ref_manager = ReferenceImageManager()
        load_character_refs(story_data, ref_manager)

        # 生成场景图（前10张）
        await generate_scene_images(story_data, ref_manager, max_images=10)

        # 输出总结
        print("\n" + "=" * 70)
        print("测试完成 - 最终总结")
        print("=" * 70)

        print(f"\n📁 输出目录: {OUTPUT_DIR}")

        print(f"\n👥 角色列表:")
        for char in story_data.get('characters', []):
            char_id = char.get('id', 'N/A')
            char_name = char.get('name', 'N/A')
            clothing = char.get('clothing', {})
            top = clothing.get('top', 'N/A')[:30]
            print(f"   - {char_name} ({char_id}): {top}...")

        print(f"\n📸 生成的图片:")
        images_dir = os.path.join(OUTPUT_DIR, "images")
        if os.path.exists(images_dir):
            for f in sorted(os.listdir(images_dir)):
                if f.endswith('.png'):
                    print(f"   - images/{f}")

        print(f"\n🔑 关键验证点:")
        print(f"   - 所有图片使用: gemini-2.5-flash-image")
        print(f"   - 风格: realistic (写实摄影)")
        print(f"   - 检查角色一致性: 请比对参考图和场景图中的角色")

    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
