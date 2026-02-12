#!/usr/bin/env python3
"""
测试结构化场景位置（unique_locations）格式

验证 SceneReferenceManager 能正确处理：
1. 新格式（带 unique_locations）- 直接使用结构化数据
2. 旧格式（无 unique_locations）- 回退到规则匹配

测试用例：
1. 新格式：不同人物的家（小明家 vs 小红家）应该是不同场景
2. 新格式：混合场景类型（interior_only, exterior_only, both）
3. 旧格式回退：确保向后兼容
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scene_reference_manager import SceneReferenceManager


def test_new_format_different_homes():
    """测试新格式：不同人物的家应该是不同场景"""
    print("\n" + "=" * 60)
    print("测试1：新格式 - 不同人物的家（小明家 vs 小红家）")
    print("=" * 60)

    unique_locations = [
        {
            "location_id": "xiaoming_apartment",
            "display_name": "小明的公寓",
            "location_type": "both",
            "interior_description": "Modern apartment with warm lighting, minimalist furniture",
            "exterior_description": "High-rise apartment building entrance with glass doors",
            "key_visual_elements": ["warm wooden floor", "large windows", "potted plants"]
        },
        {
            "location_id": "xiaohong_apartment",
            "display_name": "小红的公寓",
            "location_type": "interior_only",
            "interior_description": "Cozy apartment with pink accents, bookshelf wall",
            "exterior_description": "",
            "key_visual_elements": ["pink curtains", "bookshelf", "soft carpet"]
        },
        {
            "location_id": "city_park",
            "display_name": "城市公园",
            "location_type": "exterior_only",
            "interior_description": "",
            "exterior_description": "Urban park with cherry blossom trees, winding paths",
            "key_visual_elements": ["cherry blossoms", "wooden benches", "stone pathway"]
        }
    ]

    scenes = [
        {"scene_id": 1, "location_ref": "xiaoming_apartment", "location_area": "客厅", "location_type_used": "interior"},
        {"scene_id": 2, "location_ref": "xiaoming_apartment", "location_area": "门口", "location_type_used": "exterior"},
        {"scene_id": 3, "location_ref": "xiaohong_apartment", "location_area": "卧室", "location_type_used": "interior"},
        {"scene_id": 4, "location_ref": "city_park", "location_area": "樱花树下", "location_type_used": "exterior"},
    ]

    manager = SceneReferenceManager()
    needs = manager._analyze_anchor_needs(scenes, unique_locations)

    print(f"场景数量: {len(scenes)}")
    print(f"锚点数量: {len(needs)}")
    print(f"锚点列表:")
    for key, value in needs.items():
        print(f"  - {key}: {value.get('location_name', 'N/A')} ({value.get('view_type', 'N/A')})")

    # 验证
    # 小明公寓 interior -> 1
    # 小明公寓 exterior -> 1
    # 小红公寓 interior -> 1 (interior_only)
    # 城市公园 exterior -> 1 (exterior_only)
    expected = 4
    assert len(needs) == expected, f"Expected {expected} anchors, got {len(needs)}"

    # 验证具体的锚点存在
    assert "xiaoming_apartment_interior_anchor" in needs, "Missing xiaoming interior anchor"
    assert "xiaoming_apartment_exterior_anchor" in needs, "Missing xiaoming exterior anchor"
    assert "xiaohong_apartment_interior_anchor" in needs, "Missing xiaohong interior anchor"
    assert "city_park_exterior_anchor" in needs, "Missing city_park exterior anchor"

    # 验证 interior_only 没有生成 exterior
    assert "xiaohong_apartment_exterior_anchor" not in needs, "Should not have xiaohong exterior anchor"
    # 验证 exterior_only 没有生成 interior
    assert "city_park_interior_anchor" not in needs, "Should not have city_park interior anchor"

    print(f"✅ 通过：预期 {expected} 张锚点，实际 {len(needs)} 张")
    print("✅ 小明家和小红家正确识别为不同场景")
    return True


def test_new_format_with_descriptions():
    """测试新格式：验证描述和视觉元素正确传递"""
    print("\n" + "=" * 60)
    print("测试2：新格式 - 描述和视觉元素传递")
    print("=" * 60)

    unique_locations = [
        {
            "location_id": "wuxia_inn",
            "display_name": "龙门客栈",
            "location_type": "both",
            "interior_description": "Traditional Chinese inn interior with wooden beams, paper lanterns, and carved furniture",
            "exterior_description": "Weathered wooden inn facade with hanging signboard, dusty courtyard",
            "key_visual_elements": ["paper lanterns", "wooden beams", "carved patterns", "traditional furniture"]
        }
    ]

    scenes = [
        {"scene_id": 1, "location_ref": "wuxia_inn", "location_area": "大堂", "location_type_used": "interior"},
        {"scene_id": 2, "location_ref": "wuxia_inn", "location_area": "门口", "location_type_used": "exterior"},
    ]

    manager = SceneReferenceManager()
    needs = manager._analyze_anchor_needs(scenes, unique_locations)

    print(f"锚点数量: {len(needs)}")

    # 验证描述正确传递
    interior_anchor = needs.get("wuxia_inn_interior_anchor", {})
    exterior_anchor = needs.get("wuxia_inn_exterior_anchor", {})

    assert interior_anchor.get("description") == "Traditional Chinese inn interior with wooden beams, paper lanterns, and carved furniture"
    assert exterior_anchor.get("description") == "Weathered wooden inn facade with hanging signboard, dusty courtyard"
    assert "paper lanterns" in interior_anchor.get("key_visual_elements", [])

    print(f"  Interior description: {interior_anchor.get('description', 'N/A')[:50]}...")
    print(f"  Exterior description: {exterior_anchor.get('description', 'N/A')[:50]}...")
    print(f"  Key elements: {interior_anchor.get('key_visual_elements', [])}")

    print("✅ 通过：描述和视觉元素正确传递")
    return True


def test_old_format_fallback():
    """测试旧格式：没有 unique_locations 时回退到规则匹配"""
    print("\n" + "=" * 60)
    print("测试3：旧格式回退 - 无 unique_locations")
    print("=" * 60)

    # 旧格式：只有 location 字符串，没有 unique_locations
    scenes = [
        {"scene_id": 1, "location": "24小时便利店，收银台附近"},
        {"scene_id": 2, "location": "便利店饮料区，咖啡货架前"},
        {"scene_id": 3, "location": "便利店门口"},
    ]

    manager = SceneReferenceManager()
    # 不传 unique_locations，应该回退到规则匹配
    needs = manager._analyze_anchor_needs(scenes, unique_locations=None)

    print(f"场景数量: {len(scenes)}")
    print(f"锚点数量: {len(needs)}")
    print(f"锚点列表: {list(needs.keys())}")

    # 验证使用了规则匹配（便利店 interior + exterior = 2）
    expected = 2
    assert len(needs) == expected, f"Expected {expected} anchors (fallback), got {len(needs)}"

    print(f"✅ 通过：旧格式回退正常，生成 {len(needs)} 张锚点")
    return True


def test_mixed_location_types():
    """测试混合场景类型"""
    print("\n" + "=" * 60)
    print("测试4：混合场景类型（interior_only, exterior_only, both）")
    print("=" * 60)

    unique_locations = [
        {
            "location_id": "mountain_cave",
            "display_name": "神秘山洞",
            "location_type": "interior_only",
            "interior_description": "Dark cave with glowing crystals, stalactites",
            "exterior_description": "",
            "key_visual_elements": ["crystals", "stalactites", "mysterious glow"]
        },
        {
            "location_id": "bamboo_forest",
            "display_name": "翠竹林",
            "location_type": "exterior_only",
            "interior_description": "",
            "exterior_description": "Dense bamboo forest with misty atmosphere, sunlight filtering through",
            "key_visual_elements": ["bamboo stalks", "mist", "filtered sunlight"]
        },
        {
            "location_id": "tea_house",
            "display_name": "清风茶楼",
            "location_type": "both",
            "interior_description": "Elegant tea house with traditional decor, steam rising from teacups",
            "exterior_description": "Two-story traditional building with upturned eaves, garden entrance",
            "key_visual_elements": ["teacups", "traditional furniture", "calligraphy scrolls"]
        }
    ]

    scenes = [
        {"scene_id": 1, "location_ref": "mountain_cave", "location_type_used": "interior"},
        {"scene_id": 2, "location_ref": "bamboo_forest", "location_type_used": "exterior"},
        {"scene_id": 3, "location_ref": "tea_house", "location_type_used": "interior"},
        {"scene_id": 4, "location_ref": "tea_house", "location_type_used": "exterior"},
    ]

    manager = SceneReferenceManager()
    needs = manager._analyze_anchor_needs(scenes, unique_locations)

    print(f"锚点数量: {len(needs)}")
    print(f"锚点列表:")
    for key in sorted(needs.keys()):
        print(f"  - {key}")

    # 验证
    # 山洞 interior -> 1 (interior_only)
    # 竹林 exterior -> 1 (exterior_only)
    # 茶楼 interior -> 1
    # 茶楼 exterior -> 1
    expected = 4
    assert len(needs) == expected, f"Expected {expected} anchors, got {len(needs)}"

    # 验证正确的锚点
    assert "mountain_cave_interior_anchor" in needs
    assert "mountain_cave_exterior_anchor" not in needs  # interior_only
    assert "bamboo_forest_exterior_anchor" in needs
    assert "bamboo_forest_interior_anchor" not in needs  # exterior_only
    assert "tea_house_interior_anchor" in needs
    assert "tea_house_exterior_anchor" in needs  # both

    print(f"✅ 通过：混合类型正确处理，生成 {len(needs)} 张锚点")
    return True


def test_scifi_structured():
    """测试科幻故事结构化场景"""
    print("\n" + "=" * 60)
    print("测试5：科幻故事结构化场景")
    print("=" * 60)

    unique_locations = [
        {
            "location_id": "spaceship_bridge",
            "display_name": "星际飞船驾驶舱",
            "location_type": "interior_only",
            "interior_description": "Futuristic spaceship bridge with holographic displays, command chairs",
            "exterior_description": "",
            "key_visual_elements": ["holographic screens", "starfield view", "sleek consoles"]
        },
        {
            "location_id": "alien_planet_surface",
            "display_name": "异星地表",
            "location_type": "exterior_only",
            "interior_description": "",
            "exterior_description": "Red desert alien planet with two suns, strange rock formations",
            "key_visual_elements": ["red sand", "twin suns", "alien rocks", "purple sky"]
        },
        {
            "location_id": "colony_base",
            "display_name": "殖民地基地",
            "location_type": "both",
            "interior_description": "Colony base interior with life support systems, hydroponic gardens",
            "exterior_description": "Dome structure on alien terrain, landing pads, antenna arrays",
            "key_visual_elements": ["dome structure", "hydroponics", "airlocks"]
        }
    ]

    scenes = [
        {"scene_id": 1, "location_ref": "spaceship_bridge", "location_type_used": "interior"},
        {"scene_id": 2, "location_ref": "alien_planet_surface", "location_type_used": "exterior"},
        {"scene_id": 3, "location_ref": "colony_base", "location_type_used": "interior"},
        {"scene_id": 4, "location_ref": "colony_base", "location_type_used": "exterior"},
    ]

    manager = SceneReferenceManager()
    needs = manager._analyze_anchor_needs(scenes, unique_locations)

    print(f"锚点数量: {len(needs)}")

    expected = 4
    assert len(needs) == expected, f"Expected {expected} anchors, got {len(needs)}"

    print(f"✅ 通过：科幻结构化场景正确处理，生成 {len(needs)} 张锚点")
    return True


def test_empty_unique_locations():
    """测试空的 unique_locations 数组"""
    print("\n" + "=" * 60)
    print("测试6：空的 unique_locations 数组")
    print("=" * 60)

    unique_locations = []  # 空数组

    scenes = [
        {"scene_id": 1, "location": "咖啡厅室内"},
        {"scene_id": 2, "location": "咖啡厅门口"},
    ]

    manager = SceneReferenceManager()
    # 空数组应该回退到规则匹配
    needs = manager._analyze_anchor_needs(scenes, unique_locations)

    print(f"锚点数量: {len(needs)}")

    # 空数组应该回退到规则匹配
    expected = 2  # 咖啡厅 interior + exterior
    assert len(needs) == expected, f"Expected {expected} anchors (fallback), got {len(needs)}"

    print(f"✅ 通过：空数组正确回退到规则匹配")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("结构化场景位置（unique_locations）测试")
    print("=" * 60)

    results = []

    try:
        results.append(("新格式-不同人物的家", test_new_format_different_homes()))
        results.append(("新格式-描述传递", test_new_format_with_descriptions()))
        results.append(("旧格式回退", test_old_format_fallback()))
        results.append(("混合场景类型", test_mixed_location_types()))
        results.append(("科幻结构化", test_scifi_structured()))
        results.append(("空数组回退", test_empty_unique_locations()))
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

    print("\n所有测试通过！")
