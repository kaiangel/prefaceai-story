#!/usr/bin/env python3
"""
测试多场景锚点生成逻辑

验证 _analyze_anchor_needs() 能正确识别多个独特场景并生成相应数量的锚点

测试用例：
1. 单场景故事（便利店）-> 2张锚点
2. 多场景故事（咖啡厅+公寓+街道）-> 3张锚点
3. 复杂场景故事（多个独特地点）-> 4+张锚点
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scene_reference_manager import SceneReferenceManager


def test_single_location_story():
    """测试单场景故事：便利店（interior + exterior）"""
    print("\n" + "=" * 60)
    print("测试1：单场景故事（便利店）")
    print("=" * 60)

    scenes = [
        {"scene_id": 1, "location": "24小时便利店，收银台附近"},
        {"scene_id": 2, "location": "便利店饮料区，咖啡货架前"},
        {"scene_id": 3, "location": "便利店饮料区"},  # 同一场景
        {"scene_id": 4, "location": "便利店收银台"},
        {"scene_id": 5, "location": "便利店门口"},  # exterior
    ]

    manager = SceneReferenceManager()
    needs = manager._analyze_anchor_needs(scenes)

    print(f"场景数量: {len(scenes)}")
    print(f"锚点数量: {len(needs)}")
    print(f"锚点列表: {list(needs.keys())}")

    # 验证
    expected = 2  # 便利店 interior + exterior
    assert len(needs) == expected, f"Expected {expected} anchors, got {len(needs)}"
    print(f"✅ 通过：预期 {expected} 张锚点，实际 {len(needs)} 张")

    return True


def test_multi_location_story():
    """测试多场景故事：咖啡厅(int) + 公寓(int) + 街道(ext)"""
    print("\n" + "=" * 60)
    print("测试2：多场景故事（咖啡厅+公寓+街道）")
    print("=" * 60)

    scenes = [
        {"scene_id": 1, "location": "咖啡厅室内，靠窗位置"},
        {"scene_id": 2, "location": "咖啡厅室内，吧台"},  # 同一场景
        {"scene_id": 3, "location": "公寓房间，卧室"},
        {"scene_id": 4, "location": "城市街道，行人匆匆"},
        {"scene_id": 5, "location": "咖啡厅室内"},  # 同一场景
    ]

    manager = SceneReferenceManager()
    needs = manager._analyze_anchor_needs(scenes)

    print(f"场景数量: {len(scenes)}")
    print(f"锚点数量: {len(needs)}")
    print(f"锚点列表: {list(needs.keys())}")

    # 验证
    # 咖啡厅室内 interior -> 1
    # 公寓房间 interior -> 1
    # 城市街道 exterior -> 1
    expected = 3
    assert len(needs) == expected, f"Expected {expected} anchors, got {len(needs)}"
    print(f"✅ 通过：预期 {expected} 张锚点，实际 {len(needs)} 张")

    return True


def test_complex_story():
    """测试复杂场景故事：竹林(ext) + 客栈(int+ext) + 山洞(int)"""
    print("\n" + "=" * 60)
    print("测试3：复杂场景故事（武侠多地点）")
    print("=" * 60)

    scenes = [
        {"scene_id": 1, "location": "翠竹林深处"},  # exterior (竹林)
        {"scene_id": 2, "location": "翠竹林边缘"},  # 同一场景
        {"scene_id": 3, "location": "客栈大堂"},  # interior (客栈)
        {"scene_id": 4, "location": "客栈门口"},  # exterior (客栈)
        {"scene_id": 5, "location": "山洞内部，火光摇曳"},  # interior (山洞)
    ]

    manager = SceneReferenceManager()
    needs = manager._analyze_anchor_needs(scenes)

    print(f"场景数量: {len(scenes)}")
    print(f"锚点数量: {len(needs)}")
    print(f"锚点列表: {list(needs.keys())}")

    # 验证
    # 竹林 exterior -> 1
    # 客栈 interior -> 1
    # 客栈 exterior -> 1
    # 山洞 interior -> 1
    expected = 4
    assert len(needs) == expected, f"Expected {expected} anchors, got {len(needs)}"
    print(f"✅ 通过：预期 {expected} 张锚点，实际 {len(needs)} 张")

    return True


def test_same_location_different_times():
    """测试同一场景不同时间：不应生成额外锚点"""
    print("\n" + "=" * 60)
    print("测试4：同一场景不同时间（不生成额外锚点）")
    print("=" * 60)

    scenes = [
        {"scene_id": 1, "location": "便利店室内", "scene_style": {"time_of_day": "midnight"}},
        {"scene_id": 2, "location": "便利店室内", "scene_style": {"time_of_day": "dawn"}},
        {"scene_id": 3, "location": "便利店室内", "scene_style": {"time_of_day": "morning"}},
        {"scene_id": 4, "location": "便利店门口", "scene_style": {"time_of_day": "midnight"}},
        {"scene_id": 5, "location": "便利店门口", "scene_style": {"time_of_day": "dawn"}},
    ]

    manager = SceneReferenceManager()
    needs = manager._analyze_anchor_needs(scenes)

    print(f"场景数量: {len(scenes)}")
    print(f"锚点数量: {len(needs)}")
    print(f"锚点列表: {list(needs.keys())}")

    # 验证：不同时间不应生成额外锚点
    # 便利店 interior -> 1
    # 便利店 exterior -> 1
    expected = 2
    assert len(needs) == expected, f"Expected {expected} anchors, got {len(needs)}"
    print(f"✅ 通过：预期 {expected} 张锚点，实际 {len(needs)} 张（时间差异不影响）")

    return True


def test_scifi_story():
    """测试科幻故事：飞船舱内(int) + 异星地表(ext) + 基地(int+ext)"""
    print("\n" + "=" * 60)
    print("测试5：科幻故事（飞船+异星+基地）")
    print("=" * 60)

    scenes = [
        {"scene_id": 1, "location": "飞船驾驶舱室内"},
        {"scene_id": 2, "location": "异星地表，红色荒漠"},
        {"scene_id": 3, "location": "殖民地基地室内"},
        {"scene_id": 4, "location": "殖民地基地门口"},
    ]

    manager = SceneReferenceManager()
    needs = manager._analyze_anchor_needs(scenes)

    print(f"场景数量: {len(scenes)}")
    print(f"锚点数量: {len(needs)}")
    print(f"锚点列表: {list(needs.keys())}")

    # 验证
    # 飞船 interior -> 1
    # 异星 exterior -> 1
    # 基地 interior -> 1
    # 基地 exterior -> 1
    expected = 4
    assert len(needs) == expected, f"Expected {expected} anchors, got {len(needs)}"
    print(f"✅ 通过：预期 {expected} 张锚点，实际 {len(needs)} 张")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("多场景锚点生成逻辑测试")
    print("=" * 60)

    results = []

    try:
        results.append(("单场景故事", test_single_location_story()))
        results.append(("多场景故事", test_multi_location_story()))
        results.append(("复杂场景故事", test_complex_story()))
        results.append(("同场景不同时间", test_same_location_different_times()))
        results.append(("科幻故事", test_scifi_story()))
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")

    print("\n所有测试通过！")
