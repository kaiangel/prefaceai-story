#!/usr/bin/env python3
"""
端到端测试：unique_locations 结构化场景格式

测试从 story.json（包含 unique_locations）到锚点图生成的完整流程

验证点：
1. story.json 包含 unique_locations 时，SceneReferenceManager 正确使用结构化数据
2. 不同人物的家（小明家 vs 小红家）生成独立的锚点图
3. 锚点图 prompt 正确使用 description 和 key_visual_elements
"""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scene_reference_manager import SceneReferenceManager
from app.models.style_config import ProjectStyleConfig


def create_test_story_with_unique_locations():
    """创建包含 unique_locations 的测试 story 数据"""
    return {
        "title": "测试故事：小明和小红的周末",
        "unique_locations": [
            {
                "location_id": "xiaoming_apartment",
                "display_name": "小明的公寓",
                "location_type": "both",
                "interior_description": "Modern minimalist apartment with warm wooden floors, large floor-to-ceiling windows overlooking the city skyline, neutral gray sofa, potted monstera plants",
                "exterior_description": "High-rise apartment building entrance with glass automatic doors, concrete canopy, bicycle parking area",
                "key_visual_elements": ["warm wooden floor", "large windows", "city view", "monstera plants", "gray sofa"]
            },
            {
                "location_id": "xiaohong_apartment",
                "display_name": "小红的公寓",
                "location_type": "interior_only",
                "interior_description": "Cozy feminine apartment with pink accent wall, floor-to-ceiling bookshelf filled with books, soft white carpet, vintage desk lamp, many house plants",
                "exterior_description": "",
                "key_visual_elements": ["pink accent wall", "bookshelf", "white carpet", "vintage lamp", "house plants"]
            },
            {
                "location_id": "riverside_park",
                "display_name": "滨江公园",
                "location_type": "exterior_only",
                "interior_description": "",
                "exterior_description": "Urban riverside park with winding stone paths, weeping willow trees, wooden benches, joggers in the distance, city skyline reflection in the river",
                "key_visual_elements": ["weeping willows", "stone path", "wooden bench", "river reflection", "city skyline"]
            },
            {
                "location_id": "coffee_shop_sakura",
                "display_name": "樱花咖啡馆",
                "location_type": "both",
                "interior_description": "Trendy Japanese-style coffee shop with light wood furniture, cherry blossom decorations, glass pendant lights, latte art on display, soft jazz atmosphere",
                "exterior_description": "Charming corner cafe with large window front, potted sakura tree at entrance, handwritten chalkboard menu, outdoor seating with pink umbrellas",
                "key_visual_elements": ["cherry blossom decor", "light wood", "glass pendant lights", "latte art", "pink umbrellas"]
            }
        ],
        "scenes": [
            {
                "scene_id": 1,
                "location_ref": "xiaoming_apartment",
                "location_area": "客厅",
                "location_type_used": "interior",
                "narration": "周六早晨，小明在自己的公寓里醒来..."
            },
            {
                "scene_id": 2,
                "location_ref": "xiaoming_apartment",
                "location_area": "门口",
                "location_type_used": "exterior",
                "narration": "他走出公寓大楼..."
            },
            {
                "scene_id": 3,
                "location_ref": "riverside_park",
                "location_area": "柳树下的长椅",
                "location_type_used": "exterior",
                "narration": "在公园的长椅上，他看到了小红..."
            },
            {
                "scene_id": 4,
                "location_ref": "coffee_shop_sakura",
                "location_area": "靠窗位置",
                "location_type_used": "interior",
                "narration": "他们一起走进了樱花咖啡馆..."
            },
            {
                "scene_id": 5,
                "location_ref": "xiaohong_apartment",
                "location_area": "书房",
                "location_type_used": "interior",
                "narration": "下午，小红邀请小明去她家看书..."
            },
            {
                "scene_id": 6,
                "location_ref": "coffee_shop_sakura",
                "location_area": "门口",
                "location_type_used": "exterior",
                "narration": "傍晚，他们又回到咖啡馆门口告别..."
            }
        ],
        "characters": [
            {"id": "xiaoming", "name": "小明", "type": "human"},
            {"id": "xiaohong", "name": "小红", "type": "human"}
        ]
    }


def test_e2e_anchor_generation():
    """端到端测试：从 story.json 到锚点分析"""
    print("\n" + "=" * 60)
    print("端到端测试：unique_locations 结构化场景格式")
    print("=" * 60)

    story = create_test_story_with_unique_locations()
    unique_locations = story.get("unique_locations", [])
    scenes = story.get("scenes", [])

    print(f"\n📋 故事概览:")
    print(f"  - 标题: {story['title']}")
    print(f"  - 独特场景数: {len(unique_locations)}")
    print(f"  - 场景段落数: {len(scenes)}")

    print(f"\n📍 独特场景列表:")
    for loc in unique_locations:
        print(f"  - {loc['location_id']}: {loc['display_name']} ({loc['location_type']})")

    # 使用 SceneReferenceManager 分析锚点需求
    manager = SceneReferenceManager()
    needs = manager._analyze_anchor_needs(scenes, unique_locations)

    print(f"\n🎯 锚点需求分析:")
    print(f"  预期锚点数: 6 (小明公寓int+ext, 小红公寓int, 公园ext, 咖啡馆int+ext)")
    print(f"  实际锚点数: {len(needs)}")
    print(f"\n  锚点列表:")
    for key, value in sorted(needs.items()):
        desc_preview = value.get('description', '')[:50] + "..." if value.get('description') else "N/A"
        print(f"    - {key}:")
        print(f"        场景: {value.get('location_name')}")
        print(f"        类型: {value.get('view_type')}")
        print(f"        描述: {desc_preview}")
        print(f"        视觉元素: {value.get('key_visual_elements', [])[:3]}")

    # 验证
    expected_anchors = {
        "xiaoming_apartment_interior_anchor",
        "xiaoming_apartment_exterior_anchor",
        "xiaohong_apartment_interior_anchor",  # interior_only
        "riverside_park_exterior_anchor",       # exterior_only
        "coffee_shop_sakura_interior_anchor",
        "coffee_shop_sakura_exterior_anchor",
    }

    actual_anchors = set(needs.keys())

    assert actual_anchors == expected_anchors, f"Anchor mismatch!\nExpected: {expected_anchors}\nActual: {actual_anchors}"

    # 验证描述正确传递
    xiaoming_int = needs.get("xiaoming_apartment_interior_anchor", {})
    assert "wooden floors" in xiaoming_int.get("description", "").lower(), "小明公寓描述未正确传递"
    assert "warm wooden floor" in xiaoming_int.get("key_visual_elements", []), "小明公寓视觉元素未正确传递"

    xiaohong_int = needs.get("xiaohong_apartment_interior_anchor", {})
    assert "pink" in xiaohong_int.get("description", "").lower(), "小红公寓描述未正确传递"

    print(f"\n✅ 端到端测试通过！")
    print(f"  - 锚点数量正确: {len(needs)} 张")
    print(f"  - 小明家和小红家正确识别为不同场景")
    print(f"  - 描述和视觉元素正确传递")
    return True


def test_backward_compatibility():
    """测试向后兼容：旧格式 story.json（无 unique_locations）"""
    print("\n" + "=" * 60)
    print("向后兼容测试：旧格式 story.json")
    print("=" * 60)

    # 旧格式 story：没有 unique_locations
    old_story = {
        "title": "旧格式故事",
        "scenes": [
            {"scene_id": 1, "location": "小明的公寓客厅"},
            {"scene_id": 2, "location": "公寓楼门口"},
            {"scene_id": 3, "location": "咖啡厅室内"},
        ]
    }

    scenes = old_story.get("scenes", [])
    unique_locations = old_story.get("unique_locations")  # None

    manager = SceneReferenceManager()
    needs = manager._analyze_anchor_needs(scenes, unique_locations)

    print(f"\n📋 旧格式故事:")
    print(f"  - 场景数: {len(scenes)}")
    print(f"  - unique_locations: {unique_locations}")

    print(f"\n🎯 锚点需求分析（规则匹配回退）:")
    print(f"  锚点数: {len(needs)}")
    for key in sorted(needs.keys()):
        print(f"    - {key}")

    # 旧格式应该回退到规则匹配
    assert len(needs) > 0, "旧格式应该使用规则匹配生成锚点"

    print(f"\n✅ 向后兼容测试通过！旧格式正确回退到规则匹配")
    return True


def test_prompt_building():
    """测试锚点 prompt 构建是否正确使用新格式数据"""
    print("\n" + "=" * 60)
    print("Prompt 构建测试")
    print("=" * 60)

    story = create_test_story_with_unique_locations()
    unique_locations = story.get("unique_locations", [])
    scenes = story.get("scenes", [])

    manager = SceneReferenceManager()
    needs = manager._analyze_anchor_needs(scenes, unique_locations)

    style_config = ProjectStyleConfig(style_preset="realistic")

    print("\n📝 测试 prompt 构建:")
    for anchor_key, location_data in list(needs.items())[:2]:  # 只测试前2个
        view_type = location_data.get('view_type', 'interior')
        prompt = manager._build_anchor_prompt(location_data, view_type, style_config)

        print(f"\n  {anchor_key}:")
        print(f"    Prompt 长度: {len(prompt)} 字符")
        print(f"    Prompt 预览: {prompt[:200]}...")

        # 验证 prompt 包含关键元素
        description = location_data.get('description', '')
        if description:
            # 描述应该出现在 prompt 中（可能被修改，但核心词汇应该在）
            core_words = description.split()[:3]
            for word in core_words:
                if len(word) > 3:  # 跳过短词
                    assert word.lower() in prompt.lower(), f"描述关键词 '{word}' 未出现在 prompt 中"

        key_elements = location_data.get('key_visual_elements', [])
        if key_elements:
            # 至少部分视觉元素应该出现在 prompt 中
            found_count = sum(1 for elem in key_elements if elem.lower() in prompt.lower())
            assert found_count > 0, f"视觉元素未出现在 prompt 中: {key_elements}"

    print(f"\n✅ Prompt 构建测试通过！描述和视觉元素正确包含在 prompt 中")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("unique_locations 端到端测试")
    print("=" * 60)

    results = []

    try:
        results.append(("端到端锚点生成", test_e2e_anchor_generation()))
        results.append(("向后兼容", test_backward_compatibility()))
        results.append(("Prompt构建", test_prompt_building()))
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")

    print("\n所有端到端测试通过！")
