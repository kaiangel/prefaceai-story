"""Test script for image generation - Phase 2"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.image_generator import ImageGenerator
from app.services.image_storage import ImageStorageService
from app.services.storyboard_service import StoryboardService
from app.prompts.storyboard_prompts import build_image_prompt, build_negative_prompt


async def test_single_image():
    """测试单图生成"""
    print("=" * 60)
    print("测试 1: 单图生成")
    print("=" * 60)

    generator = ImageGenerator()

    prompt = "A cyberpunk programmer working late at night in a futuristic office, neon lights glowing, multiple holographic screens floating, rain visible through the window, detailed, 8K quality"
    negative_prompt = "blurry, low quality, distorted, cartoon"

    print(f"\nPrompt: {prompt[:100]}...")
    print(f"Negative: {negative_prompt}")
    print("\n正在生成图像...")

    result = await generator.generate_image(
        prompt=prompt,
        negative_prompt=negative_prompt,
        aspect_ratio="16:9"
    )

    print(f"\n结果:")
    print(f"  成功: {result['success']}")

    if result['success']:
        print(f"  模型: {result.get('model_used')}")
        print(f"  尺寸: {result.get('width')}x{result.get('height')}")
        print(f"  耗时: {result.get('generation_time_seconds')}秒")

        # 保存测试图像
        import base64
        os.makedirs("./test_output", exist_ok=True)
        with open("./test_output/test_single_image.png", "wb") as f:
            f.write(base64.b64decode(result['image_data']))
        print(f"  图像已保存到: ./test_output/test_single_image.png")
    else:
        print(f"  错误: {result.get('error')}")

    return result['success']


async def test_storyboard_prompt():
    """测试分镜prompt生成"""
    print("\n" + "=" * 60)
    print("测试 2: 分镜Prompt生成")
    print("=" * 60)

    # 模拟场景数据
    scene = {
        "scene_id": 1,
        "location": "城市街道，十字路口",
        "time": "下午3点，烈日骄阳",
        "mood": "突兀、惊险、转折",
        "visual_description": "林城骑着电动车穿梭在城市街道上，肩上背着蓝色外卖箱。突然一辆黑色轿车从左侧冲出，林城紧急躲闪但还是被撞中。他和电动车飞起，在空中翻转，外卖撒落一地。镜头以慢镜头捕捉他摔落的瞬间，阳光透过灰尘洒下。",
        "narration": "我叫林城，是个外卖骑手。每天要跑两三百单，风雨无阻。那天下午，我以为我的人生就要结束了。"
    }

    characters = [
        {
            "name": "林城",
            "description": "28岁男性，外卖小哥装扮，穿着蓝色骑手服，黑色头盔，脸庞棱角分明，眼神原本木讷疲惫，但在获得超能力后眼神开始闪烁异彩。留着简单的短发，皮肤偏黑，有着长期在太阳下工作的痕迹。",
            "personality": "性格内敛，工作认真负责"
        }
    ]

    style_preset = "realistic"

    # 测试prompt生成
    image_prompt = build_image_prompt(scene, characters, style_preset)
    negative_prompt = build_negative_prompt(style_preset)

    print(f"\n生成的 Image Prompt:")
    print("-" * 40)
    print(image_prompt)
    print("-" * 40)
    print(f"\nNegative Prompt: {negative_prompt[:100]}...")

    # 测试完整分镜服务
    print("\n使用 StoryboardService 生成分镜:")
    storyboard_service = StoryboardService()
    storyboard = await storyboard_service.generate_storyboard(
        scenes=[scene],
        characters=characters,
        style_preset=style_preset
    )

    print(f"  场景数: {len(storyboard)}")
    for sb in storyboard:
        print(f"  场景 {sb['scene_id']}:")
        print(f"    宽高比: {sb['aspect_ratio']}")
        print(f"    角色: {sb['characters_in_scene']}")
        print(f"    Prompt长度: {len(sb['image_prompt'])} 字符")

    return True


async def test_storyboard_with_image():
    """测试分镜 + 图像生成"""
    print("\n" + "=" * 60)
    print("测试 3: 完整分镜图像生成")
    print("=" * 60)

    # 简化的测试场景
    scene = {
        "scene_id": 1,
        "location": "Modern office at night",
        "time": "Midnight",
        "mood": "Mysterious, technological",
        "visual_description": "A young programmer sits alone in a dark office, face illuminated by multiple glowing monitors. The city lights visible through the window behind him. Coffee cups scattered on the desk.",
    }

    characters = [
        {
            "name": "Alex",
            "description": "Young male programmer, early 30s, short dark hair, wearing a casual hoodie, tired eyes but focused expression",
        }
    ]

    style_preset = "cyberpunk"

    # 生成分镜
    storyboard_service = StoryboardService()
    storyboard = await storyboard_service.generate_storyboard(
        scenes=[scene],
        characters=characters,
        style_preset=style_preset
    )

    scene_board = storyboard[0]
    print(f"\n分镜 Prompt (前200字):")
    print(scene_board['image_prompt'][:200] + "...")

    # 生成图像
    print("\n正在生成图像...")
    generator = ImageGenerator()
    result = await generator.generate_image(
        prompt=scene_board['image_prompt'],
        negative_prompt=scene_board['negative_prompt'],
        aspect_ratio=scene_board['aspect_ratio']
    )

    if result['success']:
        print(f"✅ 图像生成成功!")
        print(f"   尺寸: {result['width']}x{result['height']}")
        print(f"   耗时: {result['generation_time_seconds']}秒")

        # 保存
        import base64
        os.makedirs("./test_output", exist_ok=True)
        with open("./test_output/test_storyboard_image.png", "wb") as f:
            f.write(base64.b64decode(result['image_data']))
        print(f"   保存到: ./test_output/test_storyboard_image.png")
        return True
    else:
        print(f"❌ 图像生成失败: {result.get('error')}")
        return False


async def test_image_storage():
    """测试图像存储服务"""
    print("\n" + "=" * 60)
    print("测试 4: 图像存储服务")
    print("=" * 60)

    storage = ImageStorageService("./test_output/storage")

    # 创建一个测试图像（1x1像素的PNG）
    import base64
    # 最小的有效PNG图像
    minimal_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    print("\n保存测试图像...")
    result = await storage.save_image(
        image_data=minimal_png,
        project_id="test_project",
        chapter_id="test_chapter",
        scene_id=1
    )

    print(f"  图像路径: {result['image_path']}")
    print(f"  缩略图路径: {result['thumbnail_path']}")
    print(f"  完整路径: {result['full_path']}")

    # 验证文件存在
    exists = storage.image_exists(result['image_path'])
    print(f"  文件存在: {exists}")

    # 获取URL
    url = storage.get_image_url(result['image_path'])
    print(f"  访问URL: {url}")

    return exists


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("序话Story - Phase 2 图像生成测试")
    print("=" * 60)

    results = {}

    # 测试1: 单图生成
    try:
        results['单图生成'] = await test_single_image()
    except Exception as e:
        print(f"❌ 单图生成测试失败: {e}")
        results['单图生成'] = False

    # 测试2: 分镜Prompt
    try:
        results['分镜Prompt'] = await test_storyboard_prompt()
    except Exception as e:
        print(f"❌ 分镜Prompt测试失败: {e}")
        results['分镜Prompt'] = False

    # 测试3: 完整分镜图像
    try:
        results['分镜图像生成'] = await test_storyboard_with_image()
    except Exception as e:
        print(f"❌ 分镜图像生成测试失败: {e}")
        results['分镜图像生成'] = False

    # 测试4: 存储服务
    try:
        results['存储服务'] = await test_image_storage()
    except Exception as e:
        print(f"❌ 存储服务测试失败: {e}")
        results['存储服务'] = False

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过!")
    else:
        print("❌ 部分测试失败，请检查上面的错误信息")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
