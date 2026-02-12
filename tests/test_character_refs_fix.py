"""
测试角色参考图修复：
1. 重新生成 story.json（验证 LLM 输出正确格式）
2. 生成角色参考图（验证两个角色外观明显不同）

预期结果：
- 苏晨：短发、职业装、精致妆容
- 林薇：长发、随性穿着、彩色手链
"""

import asyncio
import json
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.story_generator import StoryGenerator
from app.services.reference_image_manager import ReferenceImageManager
from app.services.image_generator import ImageGenerator
from app.models.style_config import StyleConfigBuilder


async def main():
    output_dir = "test_output/manualtest/test_character_refs_fix"
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(f"{output_dir}/character_refs", exist_ok=True)

    # 1. 生成 story
    print("=" * 60)
    print("Step 1: 生成 story.json")
    print("=" * 60)

    # 使用原始故事idea - 两个女性室友，测试同性别角色差异化
    idea = "五年未见的大学女室友在咖啡馆意外重逢，从尴尬到敞开心扉。一个是28岁互联网公司产品经理，职业装扮，一个是28岁自由插画师，穿着随性"

    generator = StoryGenerator()
    story_result = await generator.generate_story(idea, style="realistic")

    # 处理嵌套返回格式
    if story_result.get('success') and story_result.get('data'):
        story = story_result['data']
    else:
        story = story_result

    # 保存 story.json
    story_path = f"{output_dir}/story.json"
    with open(story_path, 'w', encoding='utf-8') as f:
        json.dump(story, f, ensure_ascii=False, indent=2)
    print(f"✅ story.json 已保存到 {story_path}")

    # 2. 验证角色数据格式
    print("\n" + "=" * 60)
    print("Step 2: 验证角色数据格式")
    print("=" * 60)

    characters = story.get('characters', [])
    has_error = False

    for char in characters:
        char_id = char.get('id')
        name = char.get('name')
        print(f"\n【{name}】({char_id}):")

        # 检查必需字段
        checks = [
            ('character_type', char.get('character_type')),
            ('human.gender', char.get('human', {}).get('gender')),
            ('human.age_range', char.get('human', {}).get('age_range')),
            ('physical', bool(char.get('physical'))),
            ('clothing', bool(char.get('clothing'))),
        ]

        for field, value in checks:
            if value:
                print(f"  ✅ {field}: {value}")
            else:
                print(f"  ❌ {field}: MISSING!")
                has_error = True

        # 检查不应该存在的旧字段
        old_fields = ['type', 'gender', 'age_appearance', 'role']
        for field in old_fields:
            if char.get(field):
                print(f"  ⚠️ 发现旧字段 '{field}': {char.get(field)}")
                has_error = True

    if has_error:
        print("\n❌ 角色数据格式有问题，请检查 LLM prompt")
        # 继续执行，看看实际效果
    else:
        print("\n✅ 所有角色数据格式正确")

    # 3. 生成角色参考图
    print("\n" + "=" * 60)
    print("Step 3: 生成角色参考图")
    print("=" * 60)

    # 构建项目风格
    style_builder = StyleConfigBuilder()
    project_style = style_builder.build_from_story(story)

    # 初始化图像生成器
    image_gen = ImageGenerator()
    ref_manager = ReferenceImageManager()

    for i, char in enumerate(characters):
        char_name = char.get('name', 'Unknown')
        char_id = char.get('id', f'char_{i+1:03d}')

        print(f"\n生成 {char_name} 的参考图...")

        # 生成肖像 + 全身（串行）
        results = await ref_manager.generate_character_multi_refs(
            character=char,
            project_style=project_style,
            image_generator=image_gen,
            delay=3.0
        )

        # 保存图片
        for ref_type, result in results.items():
            if result.get('success') and result.get('pil_image'):
                img_path = f"{output_dir}/character_refs/{char_id}_{ref_type}.png"
                result['pil_image'].save(img_path)
                print(f"  ✅ {ref_type} 已保存: {img_path}")
            else:
                print(f"  ❌ {ref_type} 生成失败: {result.get('error')}")

        # 等待一下避免 API 限流
        if i < len(characters) - 1:
            await asyncio.sleep(5)

    print("\n" + "=" * 60)
    print("完成！请查看以下文件：")
    print(f"  - {output_dir}/story.json")
    print(f"  - {output_dir}/character_refs/*.png")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
