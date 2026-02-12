"""
测试 image_prompt 翻译功能
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google import genai
from app.config import settings
from app.prompts.storyboard_prompts import (
    translate_image_prompt_to_english,
    _simple_translate_prompt,
    prepare_shot_prompt_for_generation
)
from app.services.image_generator import ImageGenerator


async def test_simple_translation():
    """测试简单字典翻译"""
    print("=" * 60)
    print("测试1: 简单字典翻译")
    print("=" * 60)

    test_prompts = [
        "Medium shot of subway car. Shot type: 中景. Camera angle: 平视. Mood: 期待、好奇",
        "A girl enters the room. Shot type: 特写. Camera angle: 仰拍",
        "全景 of the city. 平视 angle. 温馨 atmosphere",
    ]

    for prompt in test_prompts:
        print(f"\n原文: {prompt}")
        translated = _simple_translate_prompt(prompt)
        print(f"翻译: {translated}")


async def test_llm_translation():
    """测试LLM翻译"""
    print("\n" + "=" * 60)
    print("测试2: LLM翻译")
    print("=" * 60)

    # 创建客户端
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    # 典型的中英混合prompt
    test_prompt = """Medium shot of subway car door opening. 小雨 enters, backlit by station lights.
Shot type: 中景. Camera angle: 平视. Mood: 期待、好奇.
Setting: 地铁站台, 清晨, 温暖的灯光.
Characters: 小雨: 年轻女孩，短发，穿着校服."""

    print(f"\n原文:\n{test_prompt}")
    print("-" * 40)

    translated = await translate_image_prompt_to_english(test_prompt, client=client)
    print(f"LLM翻译结果:\n{translated}")


async def test_shot_image_generation():
    """测试使用新方法生成shot图片"""
    print("\n" + "=" * 60)
    print("测试3: 使用 generate_shot_image 方法")
    print("=" * 60)

    # 模拟shot数据（类似shots.json中的格式）
    shot = {
        "shot_id": 1,
        "image_prompt": """Medium shot of subway car door opening. 小雨 enters, backlit by station lights.
She looks around with anticipation, adjusting her school bag strap.
Shot type: 中景. Camera angle: 平视. Mood: 期待、好奇.
Setting: 地铁车厢内, morning rush hour.
Scene style: warm color palette, soft lighting, cozy atmosphere.
Art style: digital illustration, vibrant colors, artstation trending.""",
        "negative_prompt": "blurry, low quality, distorted",
        "shot_type": "中景",
    }

    print(f"\n原始 image_prompt:\n{shot['image_prompt'][:200]}...")
    print("-" * 40)

    # 创建ImageGenerator
    generator = ImageGenerator()

    # 使用新方法生成（只翻译，不实际生成图片以节省API调用）
    print("\n测试翻译功能（使用简单翻译）...")

    # 测试prepare_shot_prompt_for_generation
    prepared = prepare_shot_prompt_for_generation(shot)
    print(f"准备好的prompt:\n{prepared[:300]}...")


async def test_full_generation():
    """完整测试：翻译 + 生成图片"""
    print("\n" + "=" * 60)
    print("测试4: 完整生成（翻译 + 生图）")
    print("=" * 60)

    shot = {
        "shot_id": 1,
        "image_prompt": """地铁车门打开的中景镜头。小雨走进车厢，背光站在站台灯光下。
她环顾四周，眼中充满期待，一边调整着书包带。
Shot type: 中景. Camera angle: 平视. Mood: 期待、好奇.
地铁车厢内部，清晨高峰时段。
数字插画风格，温暖的色调，柔和的光线。""",
        "negative_prompt": "blurry, low quality, distorted, bad anatomy",
        "shot_type": "中景",
    }

    print(f"\n原始中文 image_prompt:\n{shot['image_prompt']}")
    print("-" * 40)

    generator = ImageGenerator()

    print("\n开始生成（使用LLM翻译）...")
    result = await generator.generate_shot_image(
        shot=shot,
        aspect_ratio="16:9",
        use_llm_translation=True
    )

    if result.get("success"):
        print(f"\n✅ 生成成功!")
        print(f"翻译后的prompt:\n{result.get('translated_prompt', 'N/A')}")
        print(f"生成时间: {result.get('generation_time_seconds')}s")
        print(f"图片尺寸: {result.get('width')}x{result.get('height')}")

        # 保存图片
        if result.get('pil_image'):
            output_path = "test_output/test_translated_shot.png"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            result['pil_image'].save(output_path)
            print(f"图片已保存: {output_path}")
    else:
        print(f"\n❌ 生成失败: {result.get('error')}")


async def main():
    """运行所有测试"""
    # 测试1: 简单翻译
    await test_simple_translation()

    # 测试2: LLM翻译
    await test_llm_translation()

    # 测试3: 准备prompt
    await test_shot_image_generation()

    # 询问是否进行完整生成测试
    print("\n" + "=" * 60)
    user_input = input("是否进行完整生成测试（会调用API生成图片）? [y/N]: ")
    if user_input.lower() == 'y':
        await test_full_generation()
    else:
        print("跳过完整生成测试")

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
