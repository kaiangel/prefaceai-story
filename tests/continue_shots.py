"""
继续生成指定范围的 shots
"""
import os
import sys
import json
import asyncio
from PIL import Image
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.image_generator import ImageGenerator
from app.prompts.storyboard_prompts import Phase2PromptBuilder


async def continue_shots(project_dir: str, start_shot: int, end_shot: int):
    """继续生成指定范围的 shots"""

    # 加载数据
    with open(f"{project_dir}/2_characters.json", "r", encoding="utf-8") as f:
        characters = json.load(f)

    with open(f"{project_dir}/3_screenplay.json", "r", encoding="utf-8") as f:
        screenplay = json.load(f)

    with open(f"{project_dir}/4_storyboard.json", "r", encoding="utf-8") as f:
        storyboard = json.load(f)

    shots = storyboard.get("shots", [])
    style_preset = "realistic"

    # 初始化
    image_generator = ImageGenerator()
    prompt_builder = Phase2PromptBuilder(
        storyboard=storyboard,
        characters=characters,
        style_preset=style_preset
    )

    # 加载角色参考图
    char_refs_dir = f"{project_dir}/character_refs"
    char_ref_images = {}
    for char in characters.get("characters", []):
        char_id = char.get("id")
        portrait_path = f"{char_refs_dir}/{char_id}_portrait.png"
        fullbody_path = f"{char_refs_dir}/{char_id}_fullbody.png"

        refs = []
        if os.path.exists(portrait_path):
            refs.append(Image.open(portrait_path))
        if os.path.exists(fullbody_path):
            refs.append(Image.open(fullbody_path))

        if refs:
            char_ref_images[char_id] = refs
            print(f"  加载角色参考图: {char_id} ({len(refs)}张)")

    # 加载场景参考图
    scene_refs_dir = f"{project_dir}/scene_refs"
    scene_ref_images = {}
    if os.path.exists(scene_refs_dir):
        for filename in os.listdir(scene_refs_dir):
            if filename.endswith(".png"):
                location_id = filename.replace(".png", "").replace("_interior", "").replace("_exterior", "")
                if location_id not in scene_ref_images:
                    scene_ref_images[location_id] = []
                scene_ref_images[location_id].append(Image.open(f"{scene_refs_dir}/{filename}"))
                print(f"  加载场景参考图: {filename}")

    images_dir = f"{project_dir}/images"
    os.makedirs(images_dir, exist_ok=True)

    print(f"\n开始生成 Shot {start_shot} - {end_shot}...")

    for i in range(start_shot - 1, min(end_shot, len(shots))):
        shot = shots[i]
        shot_id = shot.get("shot_id", i + 1)

        print(f"\n生成 Shot {shot_id}/{end_shot}...")

        # 获取前一个shot
        previous_shot = shots[i - 1] if i > 0 else None

        # 加载前一个shot的图像
        previous_shot_image = None
        if previous_shot:
            prev_path = f"{images_dir}/shot_{previous_shot.get('shot_id', i):02d}.png"
            if os.path.exists(prev_path):
                previous_shot_image = Image.open(prev_path)
                print(f"  加载前序shot图像: {prev_path}")

        # 构建参考图列表
        reference_images = []

        # 角色参考图
        char_direction = shot.get("character_direction", {})
        characters_in_shot = char_direction.get("characters_visible", [])
        for char_id in characters_in_shot:
            if char_id in char_ref_images:
                reference_images.extend(char_ref_images[char_id])

        # 场景参考图
        location_id = shot.get("location_id", "")
        if not location_id:
            # 从 screenplay 查找 location
            scene_id = shot.get("scene_id", 1)
            for scene in screenplay.get("scenes", []):
                if scene.get("scene_id") == scene_id:
                    location_id = scene.get("location_id", "")
                    break

        if location_id and location_id in scene_ref_images:
            reference_images.extend(scene_ref_images[location_id])

        # 如果没有找到对应的场景参考图，使用第一个可用的
        if not any(location_id in scene_ref_images for location_id in [location_id]):
            for loc_id, refs in scene_ref_images.items():
                reference_images.extend(refs)
                break

        print(f"  角色: {characters_in_shot} ({len(characters_in_shot) * 2}张)")
        print(f"  场景参考图: {len(reference_images) - len(characters_in_shot) * 2}张")

        # 生成图像
        try:
            result = await image_generator.generate_shot_image_phase2(
                shot=shot,
                storyboard=storyboard,
                characters=characters,
                style_preset=style_preset,
                reference_images=reference_images,
                previous_shot_image=previous_shot_image,
                previous_shot=previous_shot,
                screenplay=screenplay
            )

            if result.get("success"):
                image = result.get("pil_image")
                output_path = f"{images_dir}/shot_{shot_id:02d}.png"
                if image:
                    image.save(output_path)
                    print(f"  ✅ Shot {shot_id} 保存: {output_path}")
                else:
                    print(f"  ❌ Shot {shot_id} 失败: 返回的图像为空")
            else:
                print(f"  ❌ Shot {shot_id} 失败: {result.get('error')}")

        except Exception as e:
            print(f"  ❌ Shot {shot_id} 异常: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n完成! 已生成 Shot {start_shot} - {end_shot}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str, required=True, help="项目目录")
    parser.add_argument("--start", type=int, default=4, help="起始shot")
    parser.add_argument("--end", type=int, default=10, help="结束shot")
    args = parser.parse_args()

    asyncio.run(continue_shots(args.dir, args.start, args.end))
