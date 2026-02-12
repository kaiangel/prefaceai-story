"""
场景内外景关联测试

验证SceneReferenceManager的内外景关联功能：
- 同一location先生成内景，再生成外景
- 生成外景时，把内景作为参考图传入
- 测试3种不同场景类型的内外景一致性

测试场景：
1. 现代建筑 - 咖啡厅（玻璃门/窗户透视）
2. 古代建筑 - 客栈（门廊/天井过渡）
3. 自然场景 - 山洞（洞口衔接）
"""

import asyncio
import os
import sys
import json
from datetime import datetime

# 添加项目根目录到path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scene_reference_manager import SceneReferenceManager
from app.services.image_generator import ImageGenerator
from app.models.style_config import ProjectStyleConfig


# 测试场景配置
TEST_SCENES = {
    "modern_building": {
        "name": "现代建筑 - 咖啡厅",
        "style": "realistic",
        "unique_locations": [
            {
                "location_id": "coffee_shop",
                "display_name": "Sunset Coffee Shop",
                "location_type": "both",
                "interior_description": "A cozy modern coffee shop interior with warm wooden furniture, exposed brick walls, large windows letting in natural light, espresso machines on the counter, plants hanging from the ceiling, comfortable armchairs and small tables",
                "exterior_description": "A charming street-side coffee shop with large glass windows and door, wooden signage reading 'Sunset Coffee', outdoor seating area with small bistro tables, flower boxes on the windowsills, warm light glowing from inside",
                "key_visual_elements": ["glass windows", "wooden elements", "warm lighting", "coffee equipment"]
            }
        ],
        "scenes": [
            {"scene_id": 1, "location_ref": "coffee_shop", "location_type_used": "interior", "location": "咖啡厅内部"}
        ]
    },
    "ancient_building": {
        "name": "古代建筑 - 客栈",
        "style": "ink",
        "unique_locations": [
            {
                "location_id": "ancient_inn",
                "display_name": "Dragon Gate Inn",
                "location_type": "both",
                "interior_description": "A traditional Chinese inn interior with wooden beams and pillars, paper lanterns hanging from the ceiling, round wooden tables with stools, a reception counter with an abacus, silk curtains, calligraphy scrolls on the walls, a staircase leading to upper floors",
                "exterior_description": "A two-story traditional Chinese inn building with curved eaves and upturned roof corners, red paper lanterns at the entrance, a wooden signboard with gold calligraphy, stone steps leading to the main door, courtyard visible through the gate",
                "key_visual_elements": ["curved eaves", "paper lanterns", "wooden architecture", "traditional Chinese elements"]
            }
        ],
        "scenes": [
            {"scene_id": 1, "location_ref": "ancient_inn", "location_type_used": "interior", "location": "客栈大堂"}
        ]
    },
    "natural_scene": {
        "name": "自然场景 - 山洞",
        "style": "illustration",
        "unique_locations": [
            {
                "location_id": "mountain_cave",
                "display_name": "Crystal Cave",
                "location_type": "both",
                "interior_description": "A mystical cave interior with glowing crystals embedded in the rocky walls, a small underground stream flowing through, stalactites hanging from the ceiling, bioluminescent moss providing soft blue-green light, ancient stone formations",
                "exterior_description": "A dramatic cave entrance on a mountainside, surrounded by pine trees and rocky outcrops, morning mist swirling at the entrance, crystal formations visible just inside the opening, moss and ferns growing around the cave mouth",
                "key_visual_elements": ["crystal formations", "rocky surfaces", "natural lighting", "vegetation at entrance"]
            }
        ],
        "scenes": [
            {"scene_id": 1, "location_ref": "mountain_cave", "location_type_used": "interior", "location": "山洞内部"}
        ]
    }
}


async def test_single_scene_type(scene_key: str, scene_config: dict, output_base: str) -> dict:
    """测试单个场景类型的内外景关联"""

    print(f"\n{'='*60}")
    print(f"测试场景: {scene_config['name']}")
    print(f"风格: {scene_config['style']}")
    print(f"{'='*60}")

    # 创建输出目录
    output_dir = os.path.join(output_base, scene_key)
    os.makedirs(output_dir, exist_ok=True)

    # 初始化服务
    image_generator = ImageGenerator()
    scene_ref_manager = SceneReferenceManager()
    project_style = ProjectStyleConfig(style_preset=scene_config['style'])

    # 生成场景参考图（内外景关联）
    print(f"\n[测试] 开始生成场景参考图...")

    results = await scene_ref_manager.generate_anchor_images(
        scenes=scene_config['scenes'],
        project_style=project_style,
        image_generator=image_generator,
        unique_locations=scene_config['unique_locations'],
        delay=3.0
    )

    # 保存结果
    saved_images = {}
    test_result = {
        "scene_type": scene_key,
        "scene_name": scene_config['name'],
        "style": scene_config['style'],
        "success": True,
        "anchors": {}
    }

    for anchor_key, result in results.items():
        if result.get('image'):
            # 保存图片
            image_path = os.path.join(output_dir, f"{anchor_key}.png")
            result['image'].save(image_path)
            saved_images[anchor_key] = image_path

            test_result["anchors"][anchor_key] = {
                "success": True,
                "view_type": result.get('view_type'),
                "used_interior_reference": result.get('used_interior_reference', False),
                "image_path": image_path
            }

            ref_note = " (使用内景参考)" if result.get('used_interior_reference') else ""
            print(f"  ✅ {anchor_key} 保存成功{ref_note}")
        else:
            test_result["anchors"][anchor_key] = {
                "success": False,
                "error": result.get('error', 'Unknown error')
            }
            test_result["success"] = False
            print(f"  ❌ {anchor_key} 生成失败: {result.get('error')}")

    # 验证内外景关联
    location_id = scene_config['unique_locations'][0]['location_id']
    interior_key = f"{location_id}_interior_anchor"
    exterior_key = f"{location_id}_exterior_anchor"

    if interior_key in test_result["anchors"] and exterior_key in test_result["anchors"]:
        interior_success = test_result["anchors"][interior_key].get("success", False)
        exterior_success = test_result["anchors"][exterior_key].get("success", False)
        used_reference = test_result["anchors"][exterior_key].get("used_interior_reference", False)

        if interior_success and exterior_success and used_reference:
            print(f"\n  ✅ 内外景关联验证通过: 外景生成时使用了内景作为参考图")
            test_result["interior_exterior_linked"] = True
        else:
            print(f"\n  ⚠️ 内外景关联验证:")
            print(f"    - 内景生成: {'成功' if interior_success else '失败'}")
            print(f"    - 外景生成: {'成功' if exterior_success else '失败'}")
            print(f"    - 使用内景参考: {'是' if used_reference else '否'}")
            test_result["interior_exterior_linked"] = False

    return test_result


async def run_all_tests():
    """运行所有场景测试"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_base = f"test_output/manualtest/interior_exterior_linking_{timestamp}"
    os.makedirs(output_base, exist_ok=True)

    print("\n" + "="*70)
    print("场景内外景关联测试")
    print("="*70)
    print(f"输出目录: {output_base}")
    print(f"测试场景数: {len(TEST_SCENES)}")

    all_results = {}

    for scene_key, scene_config in TEST_SCENES.items():
        try:
            result = await test_single_scene_type(scene_key, scene_config, output_base)
            all_results[scene_key] = result
        except Exception as e:
            print(f"\n❌ 测试 {scene_key} 失败: {e}")
            all_results[scene_key] = {
                "scene_type": scene_key,
                "success": False,
                "error": str(e)
            }

    # 保存测试报告
    report_path = os.path.join(output_base, "test_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    # 打印总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)

    success_count = 0
    linked_count = 0

    for scene_key, result in all_results.items():
        scene_name = result.get('scene_name', scene_key)
        success = result.get('success', False)
        linked = result.get('interior_exterior_linked', False)

        status = "✅" if success else "❌"
        link_status = "🔗" if linked else "⚠️"

        print(f"  {status} {scene_name}: {'成功' if success else '失败'} {link_status} {'已关联' if linked else '未关联'}")

        if success:
            success_count += 1
        if linked:
            linked_count += 1

    print(f"\n总计: {success_count}/{len(TEST_SCENES)} 场景生成成功")
    print(f"内外景关联: {linked_count}/{len(TEST_SCENES)} 场景已关联")
    print(f"\n测试报告: {report_path}")

    return all_results


if __name__ == "__main__":
    asyncio.run(run_all_tests())
