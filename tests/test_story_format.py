"""
测试StoryGenerator输出的字段格式是否符合新规范
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.story_generator import StoryGenerator


async def test_story_format():
    """测试故事生成的字段格式"""
    print("=" * 60)
    print("测试StoryGenerator输出格式")
    print("=" * 60)

    generator = StoryGenerator()

    # 生成一个简单的故事
    result = await generator.generate_story(
        idea="两个大学室友在咖啡馆重逢",
        style="realistic",
        duration_minutes=1,
        character_count=2,
        min_scenes=2
    )

    if not result.get("success"):
        print(f"❌ 故事生成失败: {result.get('error')}")
        return

    story = result.get("data", {})
    characters = story.get("characters", [])

    print(f"\n生成了 {len(characters)} 个角色")
    print("=" * 60)

    # 检查每个角色的字段格式
    errors = []
    warnings = []

    for char in characters:
        name = char.get("name", "Unknown")
        print(f"\n检查角色: {name}")
        print("-" * 40)

        # 检查是否使用旧字段
        if char.get("type"):
            errors.append(f"  ❌ 使用了旧字段 'type': {char.get('type')}")
        if char.get("character_type"):
            print(f"  ✅ 使用了新字段 'character_type': {char.get('character_type')}")
        else:
            warnings.append(f"  ⚠️ 缺少 'character_type' 字段")

        if char.get("role"):
            errors.append(f"  ❌ 使用了旧字段 'role': {char.get('role')}")
        if char.get("role_in_story"):
            print(f"  ✅ 使用了新字段 'role_in_story': {char.get('role_in_story')}")
        else:
            warnings.append(f"  ⚠️ 缺少 'role_in_story' 字段")

        # 检查根级gender和age_appearance（这些应该在human里）
        if char.get("gender"):
            errors.append(f"  ❌ 使用了根级 'gender': {char.get('gender')}")
        if char.get("age_appearance"):
            errors.append(f"  ❌ 使用了旧字段 'age_appearance': {char.get('age_appearance')}")

        # 检查human字段
        human = char.get("human", {})
        if human:
            if human.get("gender"):
                print(f"  ✅ 使用了新字段 'human.gender': {human.get('gender')}")
            if human.get("age_range"):
                print(f"  ✅ 使用了新字段 'human.age_range': {human.get('age_range')}")
        else:
            # 如果是人类角色但没有human字段
            char_type = char.get("character_type", char.get("type", ""))
            if char_type == "human":
                warnings.append(f"  ⚠️ 人类角色缺少 'human' 字段")

    # 汇总结果
    print("\n" + "=" * 60)
    print("检查结果汇总")
    print("=" * 60)

    if errors:
        print("\n❌ 错误（使用了旧格式字段）:")
        for e in errors:
            print(e)

    if warnings:
        print("\n⚠️ 警告（可能缺少字段）:")
        for w in warnings:
            print(w)

    if not errors and not warnings:
        print("\n✅ 所有字段格式正确！可以安全删除兼容性代码。")
    elif not errors:
        print("\n✅ 没有使用旧格式字段，可以考虑删除兼容性代码。")
    else:
        print("\n❌ LLM仍在使用旧格式字段！需要进一步调整prompt或保留兼容性代码。")

    # 保存完整的story.json用于分析
    import json
    output_path = "test_output/format_test_story.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(story, f, ensure_ascii=False, indent=2)
    print(f"\n完整故事已保存到: {output_path}")

    return len(errors) == 0


if __name__ == "__main__":
    success = asyncio.run(test_story_format())
    sys.exit(0 if success else 1)
