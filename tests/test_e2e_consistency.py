"""
端到端测试：场景一致性 + 角色一致性验证

测试故事：三个高中好友毕业十年后在母校重逢
- 3个角色（投行经理、健身教练、小学老师）
- 3个场景（学校大门、教学楼走廊、校园咖啡馆）
- 验证：角色在不同场景中的视觉一致性
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.story_generator import StoryGenerator
from app.services.storyboard_service import StoryboardService
from app.services.reference_image_manager import ReferenceImageManager
from app.services.scene_reference_manager import SceneReferenceManager
from app.services.image_generator import ImageGenerator
from app.models.style_config import StyleConfigBuilder


OUTPUT_DIR = "test_output/manualtest/teststory6.2"


async def main():
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(f"{OUTPUT_DIR}/character_refs", exist_ok=True)
    os.makedirs(f"{OUTPUT_DIR}/scene_refs", exist_ok=True)
    os.makedirs(f"{OUTPUT_DIR}/images", exist_ok=True)

    # ================================================================
    # Step 1: 生成 story.json
    # ================================================================
    print("=" * 60)
    print("Step 1: 生成 story.json")
    print("=" * 60)

    idea = """三个高中好友毕业十年后在母校门口偶遇。
一个成了投行经理（男，西装革履），一个成了健身教练（男，运动装），一个成了小学老师（女，温柔知性）。
三人一起走进校园，在教学楼走廊追忆往事，最后在校园咖啡馆约定每年此日重聚。"""

    generator = StoryGenerator()
    story_result = await generator.generate_story(
        idea=idea,
        style="realistic",
        duration_minutes=2,
        character_count=3,
        min_scenes=8
    )

    # 处理嵌套返回格式
    if story_result.get('success') and story_result.get('data'):
        story = story_result['data']
    else:
        story = story_result

    # 保存
    with open(f"{OUTPUT_DIR}/story.json", 'w', encoding='utf-8') as f:
        json.dump(story, f, ensure_ascii=False, indent=2)
    print(f"✅ story.json 已保存")

    # 验证角色数据
    characters = story.get('characters', [])
    print(f"\n找到 {len(characters)} 个角色:")
    for char in characters:
        name = char.get('name')
        gender = char.get('human', {}).get('gender', 'N/A')
        ethnicity = char.get('physical', {}).get('ethnicity', 'N/A')
        hair = char.get('physical', {}).get('hair_style', 'N/A')
        clothing_style = char.get('clothing', {}).get('style', 'N/A')
        print(f"  - {name}: {gender}, {ethnicity}, 发型: {hair[:30]}..., 服装风格: {clothing_style}")

    # 验证场景数据
    scenes = story.get('scenes', [])
    print(f"\n找到 {len(scenes)} 个场景:")
    locations = {}
    for scene in scenes:
        loc = scene.get('location', 'Unknown')
        if loc not in locations:
            locations[loc] = []
        locations[loc].append(scene.get('scene_id'))

    for loc, scene_ids in locations.items():
        print(f"  - {loc}: scenes {scene_ids}")

    # ================================================================
    # Step 2: 生成 shots.json
    # ================================================================
    print("\n" + "=" * 60)
    print("Step 2: 生成 shots.json")
    print("=" * 60)

    storyboard_service = StoryboardService()
    shots = await storyboard_service.generate_storyboard(
        scenes=scenes,
        characters=characters,
        style_preset="realistic"
    )

    with open(f"{OUTPUT_DIR}/shots.json", 'w', encoding='utf-8') as f:
        json.dump(shots, f, ensure_ascii=False, indent=2)
    print(f"✅ shots.json 已保存，共 {len(shots)} 个镜头")

    # ================================================================
    # Step 3: 生成角色参考图
    # ================================================================
    print("\n" + "=" * 60)
    print("Step 3: 生成角色参考图 (3人×2张=6张)")
    print("=" * 60)

    style_builder = StyleConfigBuilder()
    project_style = style_builder.build_from_story(story)
    image_gen = ImageGenerator()
    ref_manager = ReferenceImageManager()

    for i, char in enumerate(characters):
        char_name = char.get('name')
        char_id = char.get('id', f'char_{i+1:03d}')
        print(f"\n生成 {char_name} 的参考图...")

        results = await ref_manager.generate_character_multi_refs(
            character=char,
            project_style=project_style,
            image_generator=image_gen,
            delay=3.0
        )

        for ref_type, result in results.items():
            if result.get('success') and result.get('pil_image'):
                img_path = f"{OUTPUT_DIR}/character_refs/{char_id}_{ref_type}.png"
                result['pil_image'].save(img_path)
                print(f"  ✅ {ref_type}: {img_path}")
            else:
                print(f"  ❌ {ref_type}: {result.get('error')}")

        if i < len(characters) - 1:
            await asyncio.sleep(5)

    # ================================================================
    # Step 4: 生成场景参考图
    # ================================================================
    print("\n" + "=" * 60)
    print("Step 4: 生成场景参考图")
    print("=" * 60)

    scene_ref_manager = SceneReferenceManager()

    # 使用链式生成，确保同类型场景的视觉一致性
    scene_results = await scene_ref_manager.generate_all_scene_references_chained(
        scenes=scenes,
        project_style=project_style,
        image_generator=image_gen,
        delay=3.0
    )

    # 保存场景参考图 (返回格式: {location_id: {view_type: result}})
    scene_ref_images = []  # 收集所有场景参考图用于后续
    scene_idx = 0
    for loc_id, view_results in scene_results.items():
        for view_type, result in view_results.items():
            if result.get('success') and result.get('pil_image'):
                scene_idx += 1
                safe_name = f"scene_{scene_idx:02d}_{view_type}"
                img_path = f"{OUTPUT_DIR}/scene_refs/{safe_name}.png"
                result['pil_image'].save(img_path)
                scene_ref_images.append(result['pil_image'])
                print(f"  ✅ {loc_id[:30]}_{view_type}: {img_path}")
            else:
                print(f"  ❌ {loc_id[:30]}_{view_type}: {result.get('error')}")

    # ================================================================
    # Step 5: 生成所有场景图片
    # ================================================================
    print("\n" + "=" * 60)
    print("Step 5: 生成场景图片")
    print("=" * 60)

    # 构建角色ID到数据的映射
    char_map = {char.get('id'): char for char in characters}

    for i, shot in enumerate(shots[:12]):  # 限制最多12张
        shot_id = shot.get('scene_id', i + 1)
        # 从original_scene获取角色ID（不是名称）
        original_scene = shot.get('original_scene', {})
        char_ids = original_scene.get('characters_in_scene', [])

        print(f"\n生成 Shot {shot_id}...")
        print(f"  场景: {original_scene.get('location', 'N/A')[:40]}...")
        print(f"  角色IDs: {char_ids}")

        # 获取角色参考图（使用角色ID）
        char_refs = ref_manager.get_references_for_scene(char_ids)

        # 获取场景参考图（使用前面收集的scene_ref_images，最多用2张）
        scene_ref_list = scene_ref_images[:2] if scene_ref_images else []

        all_refs = char_refs + scene_ref_list
        print(f"  使用 {len(char_refs)} 张角色参考图 + {len(scene_ref_list)} 张场景参考图")

        # 构建完整prompt
        image_prompt = shot.get('image_prompt', '')

        # 注入角色描述
        char_descs = []
        for cid in char_ids:
            if cid in char_map:
                char = char_map[cid]
                char_descs.append(f"{char.get('name_en', char.get('name'))}")

        if char_descs:
            image_prompt = f"Characters present: {', '.join(char_descs)}. " + image_prompt

        result = await image_gen.generate_image(
            prompt=image_prompt,
            reference_images=all_refs if all_refs else None,
            aspect_ratio="16:9"
        )

        if result.get('success') and result.get('pil_image'):
            img_path = f"{OUTPUT_DIR}/images/shot_{shot_id:02d}.png"
            result['pil_image'].save(img_path)
            print(f"  ✅ {img_path}")
        else:
            print(f"  ❌ {result.get('error')}")

        await asyncio.sleep(3)

    # ================================================================
    # Step 6: 输出验证报告
    # ================================================================
    print("\n" + "=" * 60)
    print("Step 6: 验证报告")
    print("=" * 60)

    report = f"""
# 端到端测试验证报告

## 测试参数
- 故事idea: 三个高中好友毕业十年后在母校重逢
- 时长: 2分钟
- 风格: realistic
- 角色数: 3

## 角色信息
"""
    for char in characters:
        physical = char.get('physical', {})
        clothing = char.get('clothing', {})
        report += f"""
### {char.get('name')} ({char.get('id')})
- 性别: {char.get('human', {}).get('gender')}
- 种族: {physical.get('ethnicity')}
- 脸型: {physical.get('face_shape')}
- 发型: {physical.get('hair_style')}
- 发色: {physical.get('hair_color')}
- 上衣: {clothing.get('top')}
- 服装风格: {clothing.get('style')}
"""

    report += f"""
## 场景分布
"""
    for loc, scene_ids in locations.items():
        report += f"- {loc}: {len(scene_ids)} 个镜头 (scenes {scene_ids})\n"

    report += f"""
## 生成文件
- story.json: {OUTPUT_DIR}/story.json
- shots.json: {OUTPUT_DIR}/shots.json
- 角色参考图: {OUTPUT_DIR}/character_refs/*.png
- 场景参考图: {OUTPUT_DIR}/scene_refs/*.png
- 场景图片: {OUTPUT_DIR}/images/*.png

## 验证清单

### 角色一致性
- [ ] 角色1 发型在所有场景中一致
- [ ] 角色1 面部特征在所有场景中一致
- [ ] 角色2 发型在所有场景中一致
- [ ] 角色2 面部特征在所有场景中一致
- [ ] 角色3 发型在所有场景中一致
- [ ] 角色3 面部特征在所有场景中一致

### 场景一致性
- [ ] 学校大门 不同镜头建筑风格一致
- [ ] 教学楼走廊 不同镜头装饰元素一致
- [ ] 校园咖啡馆 不同镜头环境风格一致

### 逻辑自洽
- [ ] 服装变化合理（室外→室内）
- [ ] 配饰全程一致（眼镜/手表等）
"""

    with open(f"{OUTPUT_DIR}/report.md", 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✅ 报告已保存: {OUTPUT_DIR}/report.md")

    print("\n" + "=" * 60)
    print("完成！请查看以下目录:")
    print(f"  {OUTPUT_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
