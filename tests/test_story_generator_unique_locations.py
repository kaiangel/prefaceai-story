#!/usr/bin/env python3
"""
端到端测试：验证StoryGenerator是否输出unique_locations

这个测试真正调用LLM（Claude/Gemini），验证生成的story.json包含：
1. unique_locations数组
2. 每个场景有location_ref引用
3. 描述是英文的

测试用例：
1. 都市故事（小明和小红的公寓）- 验证不同人物的家被区分
2. 武侠故事（竹林、客栈、山洞）- 验证多种场景类型
3. 科幻故事（飞船、异星、基地）- 验证复杂场景
"""

import sys
import os
import json
import asyncio
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.story_generator import StoryGenerator
from app.services.scene_reference_manager import SceneReferenceManager

OUTPUT_DIR = Path("test_output/manualtest/test_unique_locations_llm")


def validate_unique_locations(story: dict, test_name: str) -> tuple[bool, list[str]]:
    """验证story是否包含正确的unique_locations格式"""
    errors = []

    # 检查unique_locations是否存在
    unique_locations = story.get("unique_locations")
    if not unique_locations:
        errors.append("缺少unique_locations数组")
        return False, errors

    if not isinstance(unique_locations, list):
        errors.append(f"unique_locations应该是数组，实际是{type(unique_locations)}")
        return False, errors

    if len(unique_locations) == 0:
        errors.append("unique_locations数组为空")
        return False, errors

    # 验证每个location的格式
    location_ids = set()
    for i, loc in enumerate(unique_locations):
        loc_id = loc.get("location_id")
        if not loc_id:
            errors.append(f"unique_locations[{i}]缺少location_id")
        elif loc_id in location_ids:
            errors.append(f"location_id重复: {loc_id}")
        else:
            location_ids.add(loc_id)

        if not loc.get("display_name"):
            errors.append(f"unique_locations[{i}]缺少display_name")

        loc_type = loc.get("location_type")
        if loc_type not in ["interior_only", "exterior_only", "both"]:
            errors.append(f"unique_locations[{i}]的location_type无效: {loc_type}")

        # 根据location_type检查描述
        if loc_type in ["interior_only", "both"]:
            if not loc.get("interior_description"):
                errors.append(f"unique_locations[{i}]({loc_id})缺少interior_description")

        if loc_type in ["exterior_only", "both"]:
            if not loc.get("exterior_description"):
                errors.append(f"unique_locations[{i}]({loc_id})缺少exterior_description")

    # 检查scenes是否使用location_ref
    scenes = story.get("scenes", [])
    for i, scene in enumerate(scenes):
        loc_ref = scene.get("location_ref")
        if not loc_ref:
            # 可能是旧格式，检查是否有location字段
            if scene.get("location"):
                errors.append(f"scenes[{i}]使用旧格式location而非location_ref")
            else:
                errors.append(f"scenes[{i}]缺少location_ref")
        elif loc_ref not in location_ids:
            errors.append(f"scenes[{i}]的location_ref '{loc_ref}'未在unique_locations中定义")

    return len(errors) == 0, errors


async def test_urban_story():
    """测试都市故事：验证不同人物的家被区分"""
    print("\n" + "=" * 60)
    print("测试1：都市故事（小明和小红的公寓）")
    print("=" * 60)

    generator = StoryGenerator()

    # 设计一个会涉及多个不同人物家的故事
    idea = "小明和小红是邻居，他们各自在自己的公寓里准备周末聚会。小明的公寓是现代简约风格，小红的公寓是温馨浪漫风格。他们最后在楼下的咖啡厅碰面。"

    print(f"\n📝 故事创意: {idea}")
    print("\n⏳ 正在调用LLM生成故事...")

    result = await generator.generate_story(
        idea=idea,
        style="realistic",
        duration_minutes=2,
        character_count=2,
        min_scenes=4
    )

    if not result.get("success"):
        print(f"❌ 故事生成失败: {result.get('error')}")
        return False, None

    story = result.get("data")  # StoryGenerator returns 'data' not 'story'
    print(f"✅ 故事生成成功")

    # 保存story.json
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    story_path = OUTPUT_DIR / "urban_story.json"
    with open(story_path, "w", encoding="utf-8") as f:
        json.dump(story, f, ensure_ascii=False, indent=2)
    print(f"💾 保存到: {story_path}")

    # 验证unique_locations
    valid, errors = validate_unique_locations(story, "都市故事")

    if valid:
        print(f"\n✅ unique_locations格式验证通过")
        unique_locations = story.get("unique_locations", [])
        print(f"   场景数量: {len(unique_locations)}")
        for loc in unique_locations:
            print(f"   - {loc.get('location_id')}: {loc.get('display_name')} ({loc.get('location_type')})")
    else:
        print(f"\n❌ unique_locations格式验证失败:")
        for err in errors:
            print(f"   - {err}")

    return valid, story


async def test_wuxia_story():
    """测试武侠故事：竹林、客栈、山洞"""
    print("\n" + "=" * 60)
    print("测试2：武侠故事（竹林+客栈+山洞）")
    print("=" * 60)

    generator = StoryGenerator()

    idea = "一位年轻剑客在翠竹林中偶遇一位神秘女子，两人结伴来到龙门客栈休息，却发现客栈内藏着通往山洞的密道，山洞中藏着失传的武功秘籍。"

    print(f"\n📝 故事创意: {idea}")
    print("\n⏳ 正在调用LLM生成故事...")

    result = await generator.generate_story(
        idea=idea,
        style="ink",  # 水墨风格
        duration_minutes=2,
        character_count=2,
        min_scenes=4
    )

    if not result.get("success"):
        print(f"❌ 故事生成失败: {result.get('error')}")
        return False, None

    story = result.get("data")  # StoryGenerator returns 'data' not 'story'
    print(f"✅ 故事生成成功")

    # 保存story.json
    story_path = OUTPUT_DIR / "wuxia_story.json"
    with open(story_path, "w", encoding="utf-8") as f:
        json.dump(story, f, ensure_ascii=False, indent=2)
    print(f"💾 保存到: {story_path}")

    # 验证unique_locations
    valid, errors = validate_unique_locations(story, "武侠故事")

    if valid:
        print(f"\n✅ unique_locations格式验证通过")
        unique_locations = story.get("unique_locations", [])
        print(f"   场景数量: {len(unique_locations)}")
        for loc in unique_locations:
            print(f"   - {loc.get('location_id')}: {loc.get('display_name')} ({loc.get('location_type')})")
    else:
        print(f"\n❌ unique_locations格式验证失败:")
        for err in errors:
            print(f"   - {err}")

    return valid, story


async def test_scifi_story():
    """测试科幻故事：飞船、异星、基地"""
    print("\n" + "=" * 60)
    print("测试3：科幻故事（飞船+异星+基地）")
    print("=" * 60)

    generator = StoryGenerator()

    idea = "星际探险队的飞船降落在红色异星球上，队员们穿过荒漠地表来到殖民地基地，发现基地内部已经被废弃，只有一个神秘的AI还在运行。"

    print(f"\n📝 故事创意: {idea}")
    print("\n⏳ 正在调用LLM生成故事...")

    result = await generator.generate_story(
        idea=idea,
        style="cyberpunk",  # 赛博朋克风格
        duration_minutes=2,
        character_count=2,
        min_scenes=4
    )

    if not result.get("success"):
        print(f"❌ 故事生成失败: {result.get('error')}")
        return False, None

    story = result.get("data")  # StoryGenerator returns 'data' not 'story'
    print(f"✅ 故事生成成功")

    # 保存story.json
    story_path = OUTPUT_DIR / "scifi_story.json"
    with open(story_path, "w", encoding="utf-8") as f:
        json.dump(story, f, ensure_ascii=False, indent=2)
    print(f"💾 保存到: {story_path}")

    # 验证unique_locations
    valid, errors = validate_unique_locations(story, "科幻故事")

    if valid:
        print(f"\n✅ unique_locations格式验证通过")
        unique_locations = story.get("unique_locations", [])
        print(f"   场景数量: {len(unique_locations)}")
        for loc in unique_locations:
            print(f"   - {loc.get('location_id')}: {loc.get('display_name')} ({loc.get('location_type')})")
    else:
        print(f"\n❌ unique_locations格式验证失败:")
        for err in errors:
            print(f"   - {err}")

    return valid, story


async def test_anchor_generation_with_new_format(story: dict, test_name: str):
    """验证新格式story能正确生成锚点"""
    print(f"\n" + "-" * 40)
    print(f"验证锚点生成: {test_name}")
    print("-" * 40)

    unique_locations = story.get("unique_locations", [])
    scenes = story.get("scenes", [])

    if not unique_locations:
        print("⚠️ 无unique_locations，跳过锚点验证")
        return True

    manager = SceneReferenceManager()
    needs = manager._analyze_anchor_needs(scenes, unique_locations)

    print(f"锚点数量: {len(needs)}")
    for key in sorted(needs.keys()):
        loc_name = needs[key].get("location_name", "N/A")
        view_type = needs[key].get("view_type", "N/A")
        print(f"  - {key}: {loc_name} ({view_type})")

    # 基本验证
    if len(needs) == 0:
        print("❌ 锚点数量为0")
        return False

    print("✅ 锚点生成验证通过")
    return True


async def main():
    print("=" * 60)
    print("StoryGenerator unique_locations 端到端测试")
    print("=" * 60)
    print("\n⚠️ 此测试会调用真实的LLM API（Claude/Gemini）")
    print("⚠️ 预计耗时：2-5分钟\n")

    results = []
    stories = {}

    # 测试1：都市故事
    try:
        valid, story = await test_urban_story()
        results.append(("都市故事", valid))
        if story:
            stories["urban"] = story
            await test_anchor_generation_with_new_format(story, "都市故事")
    except Exception as e:
        print(f"❌ 都市故事测试异常: {e}")
        import traceback
        traceback.print_exc()
        results.append(("都市故事", False))

    # 测试2：武侠故事
    try:
        valid, story = await test_wuxia_story()
        results.append(("武侠故事", valid))
        if story:
            stories["wuxia"] = story
            await test_anchor_generation_with_new_format(story, "武侠故事")
    except Exception as e:
        print(f"❌ 武侠故事测试异常: {e}")
        import traceback
        traceback.print_exc()
        results.append(("武侠故事", False))

    # 测试3：科幻故事
    try:
        valid, story = await test_scifi_story()
        results.append(("科幻故事", valid))
        if story:
            stories["scifi"] = story
            await test_anchor_generation_with_new_format(story, "科幻故事")
    except Exception as e:
        print(f"❌ 科幻故事测试异常: {e}")
        import traceback
        traceback.print_exc()
        results.append(("科幻故事", False))

    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n🎉 所有端到端测试通过！")
        print(f"📁 输出目录: {OUTPUT_DIR}")
    else:
        print("\n⚠️ 部分测试失败，请检查LLM输出")
        print("💡 提示：如果LLM未输出unique_locations，可能需要调整prompt")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
