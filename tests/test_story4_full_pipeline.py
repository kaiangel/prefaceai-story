"""
teststory4 完整流程测试：胆小的小猫第一次离开家探险

使用新的角色一致性系统进行完整测试
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.story_generator import StoryGenerator
from app.services.storyboard_service import StoryboardService
from app.services.image_generator import ImageGenerator
from app.services.unified_prompt_builder import UnifiedPromptBuilder, build_project_style
from app.services.reference_image_manager import ReferenceImageManager
from app.services.character_prompt_builder import CharacterPromptBuilder

OUTPUT_DIR = "./test_output/manualtest/teststory4"

# 测试配置
TEST_CONFIG = {
    "idea": "一只胆小的小猫第一次离开家探险",
    "style": "cartoon",
    "duration_minutes": 3,
    "character_count": 2,
    "language": "zh-CN"
}


def save_json(data: Any, path: str):
    """保存JSON文件"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(path: str) -> Dict[str, Any]:
    """加载JSON文件"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def step1_generate_story() -> Dict[str, Any]:
    """Step 1: 生成故事"""
    print("\n" + "=" * 70)
    print("Step 1: 生成故事 (story.json)")
    print("=" * 70)

    generator = StoryGenerator()

    result = await generator.generate_story(
        idea=TEST_CONFIG["idea"],
        style=TEST_CONFIG["style"],
        duration_minutes=TEST_CONFIG["duration_minutes"],
        character_count=TEST_CONFIG["character_count"],
        language=TEST_CONFIG["language"]
    )

    if not result.get("success"):
        raise Exception(f"故事生成失败: {result.get('error')}")

    story_data = result["data"]

    # 保存
    save_json(story_data, f"{OUTPUT_DIR}/story.json")

    print(f"  故事标题: {story_data.get('title', 'N/A')}")
    print(f"  角色数量: {len(story_data.get('characters', []))}")
    print(f"  场景数量: {len(story_data.get('scenes', []))}")
    print(f"  使用模型: {result.get('model_used', 'N/A')}")
    print(f"  已保存: story.json")

    return story_data


async def step2_generate_shots(story_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Step 2: 生成分镜 (shots.json)"""
    print("\n" + "=" * 70)
    print("Step 2: 生成分镜 (shots.json)")
    print("=" * 70)

    service = StoryboardService()

    scenes = story_data.get('scenes', [])
    characters = story_data.get('characters', [])
    style = story_data.get('style_preset', TEST_CONFIG["style"])

    shots = await service.generate_storyboard_with_splitting(
        scenes=scenes,
        characters=characters,
        style_preset=style,
        aspect_ratio="16:9"
    )

    # 保存
    save_json(shots, f"{OUTPUT_DIR}/shots.json")

    print(f"  原始场景数: {len(scenes)}")
    print(f"  拆分后Shot数: {len(shots)}")
    print(f"  已保存: shots.json")

    return shots


async def step3_generate_character_refs(
    story_data: Dict[str, Any],
    image_generator: ImageGenerator
) -> Dict[str, Any]:
    """Step 3: 生成角色参考图"""
    print("\n" + "=" * 70)
    print("Step 3: 生成角色参考图")
    print("=" * 70)

    characters = story_data.get('characters', [])

    # 构建项目风格
    project_style = build_project_style(story_data)
    print(f"  风格预设: {project_style.style_preset}")
    print(f"  色调: {project_style.color_palette}")

    # 使用ReferenceImageManager
    ref_manager = ReferenceImageManager()

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

    # 收集参考图的prompt
    ref_prompts = {}
    char_builder = CharacterPromptBuilder()
    for char in characters:
        char_id = char.get('id')
        char_name = char.get('name')
        char_type = ref_manager._get_character_type(char)
        ref_prompt = ref_manager._build_reference_prompt(char, char_type, project_style)
        ref_prompts[char_name] = {
            "char_id": char_id,
            "char_type": char_type,
            "reference_prompt": ref_prompt,
            "negative_prompt": ref_manager._get_negative_prompt(char_type)
        }

    # 保存prompt记录
    save_json(ref_prompts, f"{OUTPUT_DIR}/character_ref_prompts.json")

    for char_id, path in saved_refs.items():
        print(f"  已保存: {os.path.basename(path)}")

    print(f"\n  参考图目录: {ref_dir}")

    return {
        "ref_manager": ref_manager,
        "ref_prompts": ref_prompts,
        "project_style": project_style
    }


async def step4_generate_shot_images(
    story_data: Dict[str, Any],
    shots: List[Dict[str, Any]],
    project_style,
    image_generator: ImageGenerator,
    max_shots: int = 10
) -> List[Dict[str, Any]]:
    """Step 4: 生成前N张shot图片"""
    print("\n" + "=" * 70)
    print(f"Step 4: 生成前 {max_shots} 张 Shot 图片")
    print("=" * 70)

    characters = story_data.get('characters', [])
    scenes = story_data.get('scenes', [])

    # 使用UnifiedPromptBuilder
    prompt_builder = UnifiedPromptBuilder()

    images_dir = f"{OUTPUT_DIR}/images"
    os.makedirs(images_dir, exist_ok=True)

    image_results = []
    prompts_log = []

    shots_to_generate = shots[:max_shots]

    for i, shot in enumerate(shots_to_generate):
        shot_id = shot.get('shot_id', i + 1)
        original_scene_id = shot.get('original_scene_id', shot.get('scene_id'))

        print(f"\n  生成 Shot {shot_id}/{len(shots_to_generate)}...")

        # 获取原始场景
        original_scene = None
        for scene in scenes:
            if scene.get('scene_id') == original_scene_id:
                original_scene = scene
                break

        # 预览角色
        char_names = prompt_builder.get_characters_preview(shot, characters, original_scene)
        print(f"    包含角色: {', '.join(char_names) if char_names else '无'}")

        # 构建完整prompt（使用新的一致性系统）
        full_prompt = prompt_builder.build_shot_prompt(
            shot=shot,
            characters=characters,
            project_style=project_style,
            original_scene=original_scene
        )

        # 获取主角色类型
        main_char_type = None
        if char_names and characters:
            for char in characters:
                if char.get('name') in char_names:
                    main_char_type = char.get('type', char.get('character_type'))
                    break

        negative_prompt = prompt_builder.build_negative_prompt(main_char_type)

        # 记录prompt
        prompts_log.append({
            "shot_id": shot_id,
            "characters_included": char_names,
            "full_prompt": full_prompt,
            "negative_prompt": negative_prompt
        })

        # 生成图片
        result = await image_generator.generate_image(
            prompt=full_prompt,
            negative_prompt=negative_prompt,
            aspect_ratio=shot.get('aspect_ratio', '16:9')
        )

        if result.get('success') and result.get('pil_image'):
            image_path = f"{images_dir}/shot_{shot_id:02d}.png"
            result['pil_image'].save(image_path)
            print(f"    ✅ 已保存: shot_{shot_id:02d}.png")

            image_results.append({
                "shot_id": shot_id,
                "success": True,
                "path": image_path,
                "characters_included": char_names
            })
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"    ❌ 失败: {error_msg}")
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
    save_json(prompts_log, f"{OUTPUT_DIR}/prompts_log.json")

    success_count = sum(1 for r in image_results if r.get('success'))
    print(f"\n  成功: {success_count}/{len(shots_to_generate)}")
    print(f"  图片目录: {images_dir}")

    return prompts_log


def step5_output_verification(
    story_data: Dict[str, Any],
    shots: List[Dict[str, Any]],
    ref_prompts: Dict[str, Any],
    prompts_log: List[Dict[str, Any]]
):
    """Step 5: 输出验收数据"""
    print("\n" + "=" * 70)
    print("验收数据总结")
    print("=" * 70)

    scenes = story_data.get('scenes', [])
    characters = story_data.get('characters', [])

    print(f"\n【故事统计】")
    print(f"  场景数量: {len(scenes)}")
    print(f"  Shot数量: {len(shots)}")
    print(f"  角色数量: {len(characters)}")

    print(f"\n【角色信息】")
    for char in characters:
        char_name = char.get('name')
        char_type = char.get('type', char.get('character_type', 'unknown'))
        print(f"  - {char_name}: {char_type}")

    print(f"\n【角色参考图 Prompt】")
    for char_name, info in ref_prompts.items():
        print(f"\n  === {char_name} ({info['char_type']}) ===")
        print(f"  {info['reference_prompt'][:200]}...")

    print(f"\n【Shot Prompt 示例】")
    for shot_id in [1, 5, 10]:
        for log in prompts_log:
            if log.get('shot_id') == shot_id:
                print(f"\n  === Shot {shot_id} ===")
                print(f"  包含角色: {log.get('characters_included')}")
                print(f"  Prompt: {log.get('full_prompt')[:300]}...")
                break

    print(f"\n【生成的图片路径】")
    images_dir = f"{OUTPUT_DIR}/images"
    if os.path.exists(images_dir):
        for f in sorted(os.listdir(images_dir)):
            if f.endswith('.png'):
                full_path = os.path.join(images_dir, f)
                size = os.path.getsize(full_path)
                print(f"  {full_path} ({size:,} bytes)")


async def main():
    print("\n" + "=" * 70)
    print("teststory4 完整流程测试")
    print("=" * 70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"故事创意: {TEST_CONFIG['idea']}")
    print(f"风格: {TEST_CONFIG['style']}")
    print(f"时长: {TEST_CONFIG['duration_minutes']} 分钟")
    print(f"角色数: {TEST_CONFIG['character_count']}")

    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 初始化图片生成器（共用）
    image_generator = ImageGenerator()

    # Step 1: 生成故事
    story_data = await step1_generate_story()

    # Step 2: 生成分镜
    shots = await step2_generate_shots(story_data)

    # Step 3: 生成角色参考图
    ref_result = await step3_generate_character_refs(story_data, image_generator)

    # Step 4: 生成前10张shot图片
    prompts_log = await step4_generate_shot_images(
        story_data=story_data,
        shots=shots,
        project_style=ref_result["project_style"],
        image_generator=image_generator,
        max_shots=10
    )

    # Step 5: 输出验收数据
    step5_output_verification(
        story_data=story_data,
        shots=shots,
        ref_prompts=ref_result["ref_prompts"],
        prompts_log=prompts_log
    )

    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"输出目录: {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
