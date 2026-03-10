"""
TASK-STYLE-THUMBNAILS: 为 create 页面 15 种视觉风格生成缩略图

统一场景: "一个年轻女生站在城市街头，微风拂过她的头发，背后是温暖的街景"
模型: NB2 (gemini-3.1-flash-image-preview)
宽高比: 1:1 (缩略图用途)
输出: test_output/manualtest/style_thumbnails/
"""

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.style_enforcer import StyleEnforcer
from app.services.image_generator import ImageGenerator


# 统一基础场景 (英文，符合图像 prompt 全英文规则)
BASE_SCENE = """A young woman standing on a city street, a gentle breeze flowing through her hair. Behind her, a warm and inviting streetscape with soft golden light. She wears a casual light jacket over a simple top, looking naturally relaxed with a faint smile. The scene captures a quiet everyday moment in the city — warm, approachable, and full of life."""

# 15 种风格 + 中文名映射
STYLES = [
    ("pixar_3d", "皮克斯3D"),
    ("ghibli", "吉卜力"),
    ("illustration", "数字插画"),
    ("ink", "中国水墨"),
    ("slam_dunk", "井上雄彦"),
    ("korean_webtoon", "韩漫"),
    ("oil_painting", "油画"),
    ("cyberpunk", "赛博朋克"),
    ("realistic", "写实摄影"),
    ("cartoon", "卡通动画"),
    ("anime", "日式动画"),
    ("watercolor", "水彩"),
    ("children_book", "儿童绘本"),
    ("manga", "日漫"),
    ("pixel", "像素艺术"),
]


async def generate_style_thumbnails():
    """生成 15 种风格缩略图"""

    output_dir = "test_output/manualtest/style_thumbnails"
    prompt_dir = os.path.join(output_dir, "prompts")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(prompt_dir, exist_ok=True)

    ig = ImageGenerator()

    success_count = 0
    fail_count = 0
    total_time = 0

    print(f"\n{'='*60}")
    print(f"TASK-STYLE-THUMBNAILS: 15 种风格缩略图生成")
    print(f"模型: NB2 ({ig.NB2_MODEL})")
    print(f"场景: 城市街头年轻女生")
    print(f"宽高比: 1:1")
    print(f"输出: {output_dir}")
    print(f"{'='*60}\n")

    for i, (style_key, chinese_name) in enumerate(STYLES):
        print(f"\n--- [{i+1}/15] {chinese_name} ({style_key}) ---")

        # 构建完整 prompt: StyleEnforcer mandatory 前缀 + 基础场景
        full_prompt = StyleEnforcer.enforce_prompt(
            BASE_SCENE,
            style_key,
            add_quality_suffix=True
        )

        # 保存 prompt 到文件
        prompt_file = os.path.join(prompt_dir, f"{chinese_name}.txt")
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(f"# {chinese_name} ({style_key})\n\n")
            f.write(full_prompt)
        print(f"  Prompt 已保存: {prompt_file}")

        # 调用 NB2 生成
        start = time.time()
        try:
            result = await ig.generate_image(
                prompt=full_prompt,
                aspect_ratio="1:1",
                use_pro_model=True,  # True = 使用 NB2_MODEL
            )
        except Exception as e:
            print(f"  ❌ 异常: {e}")
            fail_count += 1
            continue

        elapsed = time.time() - start
        total_time += elapsed

        if result.get("success"):
            # 保存图片
            pil_image = result["pil_image"]
            image_path = os.path.join(output_dir, f"{chinese_name}.png")
            pil_image.save(image_path, "PNG")
            print(f"  ✅ 成功 ({elapsed:.1f}s) — {pil_image.size[0]}x{pil_image.size[1]} — {image_path}")
            success_count += 1
        else:
            print(f"  ❌ 失败 ({elapsed:.1f}s): {result.get('error', 'unknown')}")
            fail_count += 1

        # 请求间隔避免限流
        if i < len(STYLES) - 1:
            await asyncio.sleep(3)

    # 汇总
    print(f"\n{'='*60}")
    print(f"生成完成: {success_count}/15 成功, {fail_count}/15 失败")
    print(f"总耗时: {total_time:.0f}s (平均 {total_time/max(success_count,1):.1f}s/张)")
    print(f"输出目录: {output_dir}")
    print(f"{'='*60}\n")

    return success_count


if __name__ == "__main__":
    count = asyncio.run(generate_style_thumbnails())
    sys.exit(0 if count == 15 else 1)
