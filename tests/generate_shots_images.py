"""
为teststory3-1生成shot图片
使用新的角色一致性系统确保角色外观和风格统一

核心改进：
1. 使用CharacterPromptBuilder生成完整的[CHARACTER: ...]格式描述
2. 使用UnifiedPromptBuilder整合场景、角色、风格
3. 智能识别群体场景中的所有角色
4. 可选：生成角色参考图（方案B）
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.image_generator import ImageGenerator
from app.services.unified_prompt_builder import UnifiedPromptBuilder, build_project_style
from app.services.reference_image_manager import ReferenceImageManager
from app.services.character_prompt_builder import CharacterPromptBuilder

OUTPUT_DIR = "./test_output/manualtest/teststory3-1"

# 配置选项
GENERATE_REFERENCE_IMAGES = True   # 是否先生成角色参考图
USE_REFERENCE_IMAGES = False        # 是否在生成场景图时使用参考图（需要支持multi-modal的模型）
SAVE_PROMPTS = True                 # 是否保存生成的prompt到文件


def load_json(path: str) -> Dict[str, Any]:
    """加载JSON文件"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, path: str):
    """保存JSON文件"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_scene_by_id(scenes: List[Dict], scene_id: int) -> Optional[Dict]:
    """根据scene_id获取原始场景数据"""
    for scene in scenes:
        if scene.get('scene_id') == scene_id:
            return scene
    return None


async def main():
    print("\n" + "=" * 70)
    print("生成teststory3-1的Shot图片（使用角色一致性系统）")
    print("=" * 70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 加载数据
    story_data = load_json(f"{OUTPUT_DIR}/story.json")
    shots = load_json(f"{OUTPUT_DIR}/shots.json")

    characters = story_data.get('characters', [])
    scenes = story_data.get('scenes', [])

    print(f"\n故事: {story_data.get('title', 'N/A')}")
    print(f"角色数量: {len(characters)}")
    print(f"Shot数量: {len(shots)}")

    # 初始化服务
    image_generator = ImageGenerator()
    prompt_builder = UnifiedPromptBuilder()
    ref_manager = ReferenceImageManager()

    # 构建项目风格配置
    print("\n构建项目风格配置...")
    project_style = build_project_style(story_data)
    print(f"  风格预设: {project_style.style_preset}")
    print(f"  色调: {project_style.color_palette}")
    print(f"  光影: {project_style.lighting_style}")

    # 显示角色信息
    print("\n角色列表:")
    char_builder = CharacterPromptBuilder()
    for char in characters:
        char_type = char.get('type', char.get('character_type', 'unknown'))
        print(f"  - {char.get('name')} ({char.get('name_en', 'N/A')}): {char_type}")
        # 预览生成的角色描述
        char_prompt = char_builder.build_character_prompt(char)
        print(f"    Prompt预览: {char_prompt[:100]}...")

    # Step 1: 生成角色参考图（可选）
    if GENERATE_REFERENCE_IMAGES:
        print("\n" + "-" * 50)
        print("Step 1: 生成角色参考图")
        print("-" * 50)

        ref_results = await ref_manager.generate_all_character_references(
            characters=characters,
            project_style=project_style,
            image_generator=image_generator,
            delay=4.0
        )

        # 保存参考图
        ref_dir = f"{OUTPUT_DIR}/character_refs"
        os.makedirs(ref_dir, exist_ok=True)

        saved_refs = ref_manager.save_all_references(ref_dir)
        for char_id, path in saved_refs.items():
            print(f"  已保存: {os.path.basename(path)}")

        print(f"\n角色参考图保存目录: {ref_dir}")
    else:
        print("\n跳过角色参考图生成（GENERATE_REFERENCE_IMAGES=False）")

    # Step 2: 生成Shot图片
    print("\n" + "-" * 50)
    print("Step 2: 生成Shot图片")
    print("-" * 50)

    images_dir = f"{OUTPUT_DIR}/images"
    os.makedirs(images_dir, exist_ok=True)

    image_results = []
    prompts_log = []
    success_count = 0

    for shot in shots:
        shot_id = shot.get('shot_id')
        original_scene_id = shot.get('original_scene_id', shot.get('scene_id'))

        print(f"\n生成Shot {shot_id}/{len(shots)}...")
        print(f"  阶段: {shot.get('story_phase', 'N/A')}")
        print(f"  原场景: {original_scene_id}")
        print(f"  镜头类型: {shot.get('shot_type', 'N/A')}")

        # 获取原始场景数据
        original_scene = get_scene_by_id(scenes, original_scene_id)

        # 预览将要包含的角色
        char_names = prompt_builder.get_characters_preview(shot, characters, original_scene)
        print(f"  包含角色: {', '.join(char_names) if char_names else '无'}")

        # 构建完整的prompt
        full_prompt = prompt_builder.build_shot_prompt(
            shot=shot,
            characters=characters,
            project_style=project_style,
            original_scene=original_scene
        )

        # 构建negative prompt
        # 获取场景中主要角色的类型
        main_char_type = None
        if char_names and characters:
            for char in characters:
                if char.get('name') in char_names:
                    main_char_type = char.get('type', char.get('character_type'))
                    break

        negative_prompt = prompt_builder.build_negative_prompt(main_char_type)

        # 保存prompt日志
        if SAVE_PROMPTS:
            prompts_log.append({
                "shot_id": shot_id,
                "characters_included": char_names,
                "full_prompt": full_prompt,
                "negative_prompt": negative_prompt
            })

        # 获取参考图（如果启用）
        reference_images = None
        if USE_REFERENCE_IMAGES and original_scene:
            char_ids = original_scene.get('characters_in_scene', [])
            reference_images = ref_manager.get_references_for_scene(char_ids)
            if reference_images:
                print(f"  使用 {len(reference_images)} 张参考图")

        # 生成图片
        result = await image_generator.generate_image(
            prompt=full_prompt,
            negative_prompt=negative_prompt,
            aspect_ratio=shot.get('aspect_ratio', '16:9'),
            reference_images=reference_images if reference_images else None
        )

        if result.get('success') and result.get('pil_image'):
            image_path = f"{images_dir}/shot_{shot_id:02d}.png"
            result['pil_image'].save(image_path)
            print(f"  ✅ 已保存: shot_{shot_id:02d}.png")

            image_results.append({
                "shot_id": shot_id,
                "success": True,
                "path": image_path,
                "story_phase": shot.get("story_phase"),
                "shot_type": shot.get("shot_type"),
                "characters_included": char_names,
                "used_reference_images": bool(reference_images)
            })
            success_count += 1
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"  ❌ 失败: {error_msg}")
            image_results.append({
                "shot_id": shot_id,
                "success": False,
                "error": error_msg,
                "characters_included": char_names
            })

        # 避免API速率限制
        await asyncio.sleep(4)

    # 保存结果
    save_json(image_results, f"{OUTPUT_DIR}/images_log.json")

    if SAVE_PROMPTS:
        save_json(prompts_log, f"{OUTPUT_DIR}/prompts_log.json")
        print(f"\n已保存prompt日志: prompts_log.json")

    # 生成角色设定表
    print("\n生成角色设定表...")
    character_sheet_content = generate_character_sheet(characters, project_style, char_builder)
    with open(f"{OUTPUT_DIR}/character_sheet.md", "w", encoding="utf-8") as f:
        f.write(character_sheet_content)
    print(f"已保存: character_sheet.md")

    # 打印总结
    print("\n" + "=" * 70)
    print("图片生成完成")
    print("=" * 70)
    print(f"成功: {success_count}/{len(shots)}")
    print(f"生成参考图: {GENERATE_REFERENCE_IMAGES}")
    print(f"使用参考图: {USE_REFERENCE_IMAGES}")
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 列出生成的图片
    if os.path.exists(images_dir):
        print(f"\n图片目录: {images_dir}")
        total_size = 0
        for f in sorted(os.listdir(images_dir)):
            if f.endswith('.png'):
                size = os.path.getsize(os.path.join(images_dir, f))
                total_size += size
                print(f"  {f} ({size:,} bytes)")
        print(f"\n总大小: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")


def generate_character_sheet(
    characters: List[Dict],
    project_style,
    char_builder: CharacterPromptBuilder
) -> str:
    """生成角色设定表（Markdown格式）"""
    lines = ["# 角色设定表\n"]
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 项目风格
    lines.append("## 项目风格\n")
    lines.append(f"- 风格预设: {project_style.style_preset}")
    lines.append(f"- 色调: {project_style.color_palette}")
    lines.append(f"- 光影: {project_style.lighting_style}")
    lines.append(f"\n**风格后缀:**\n```\n{project_style.style_suffix}\n```\n")

    # 角色列表
    lines.append("## 角色详情\n")

    for char in characters:
        name = char.get('name', 'Unknown')
        name_en = char.get('name_en', '')
        char_type = char.get('type', char.get('character_type', 'unknown'))
        role = char.get('role', char.get('role_in_story', 'unknown'))

        lines.append(f"### {name} ({name_en})\n")
        lines.append(f"- **ID**: {char.get('id', 'N/A')}")
        lines.append(f"- **类型**: {char_type}")
        lines.append(f"- **角色**: {role}")
        lines.append(f"- **性别**: {char.get('gender', 'N/A')}")

        # 生成完整的prompt描述
        full_prompt = char_builder.build_character_prompt(char)
        lines.append(f"\n**图像Prompt:**\n```\n{full_prompt}\n```\n")

        # 额外细节
        extra = char.get('extra_details', '')
        if extra:
            lines.append(f"**额外细节:** {extra}\n")

        lines.append("---\n")

    return "\n".join(lines)


if __name__ == "__main__":
    asyncio.run(main())
