"""
生成 Phase 1 新增 13 种风格缩略图

统一场景: 和原 15 张一致 (城市街头年轻女生)
模型: gemini-3.1-flash-image-preview
宽高比: 1:1 (缩略图用途)
输出: frontend/public/styles/ (直接放到前端静态目录)
"""

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from app.services.style_enforcer import StyleEnforcer
from app.services.image_generator import ImageGenerator


# 统一基础场景 (和原 15 张一致)
BASE_SCENE = """A young woman standing on a city street, a gentle breeze flowing through her hair. Behind her, a warm and inviting streetscape with soft golden light. She wears a casual light jacket over a simple top, looking naturally relaxed with a faint smile. The scene captures a quiet everyday moment in the city — warm, approachable, and full of life."""

# 新增 13 种风格
NEW_STYLES = [
    ("ukiyo_e", "浮世绘"),
    ("vintage_film", "复古胶片"),
    ("pencil_sketch", "铅笔素描"),
    ("chibi", "Q版卡通"),
    ("dark_fantasy", "暗黑奇幻"),
    ("pop_art", "波普艺术"),
    ("paper_cut", "中国剪纸"),
    ("steampunk", "蒸汽朋克"),
    ("art_nouveau", "新艺术"),
    ("noir", "黑色电影"),
    ("comic_western", "欧美漫画"),
    ("pastel_dream", "梦幻马卡龙"),
    ("gothic", "哥特风"),
]


async def generate_new_thumbnails():
    """生成 13 种新风格缩略图"""

    # 直接输出到前端静态目录
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "frontend", "public", "styles"
    )
    os.makedirs(output_dir, exist_ok=True)

    ig = ImageGenerator()

    success_count = 0
    fail_count = 0
    total_time = 0
    total = len(NEW_STYLES)

    print(f"\n{'='*60}")
    print(f"Phase 1 新增 13 种风格缩略图生成")
    print(f"模型: gemini-3.1-flash-image-preview")
    print(f"场景: 城市街头年轻女生 (同原 15 张)")
    print(f"宽高比: 1:1")
    print(f"输出: {output_dir}")
    print(f"{'='*60}\n")

    for i, (style_key, chinese_name) in enumerate(NEW_STYLES):
        print(f"\n--- [{i+1}/{total}] {chinese_name} ({style_key}) ---")

        # 构建完整 prompt
        full_prompt = StyleEnforcer.enforce_prompt(
            BASE_SCENE,
            style_key,
            add_quality_suffix=True
        )

        # 调用生成
        start = time.time()
        try:
            result = await ig.generate_image(
                prompt=full_prompt,
                aspect_ratio="1:1",
                use_pro_model=True,
            )
        except Exception as e:
            print(f"  ❌ 异常: {e}")
            fail_count += 1
            continue

        elapsed = time.time() - start
        total_time += elapsed

        if result.get("success"):
            pil_image = result["pil_image"]
            # 保存为 jpg (和原 15 张一致)
            image_path = os.path.join(output_dir, f"{style_key}.jpg")
            pil_image.save(image_path, "JPEG", quality=90)
            print(f"  ✅ 成功 ({elapsed:.1f}s) — {pil_image.size[0]}x{pil_image.size[1]} — {image_path}")
            success_count += 1
        else:
            print(f"  ❌ 失败 ({elapsed:.1f}s): {result.get('error', 'unknown')}")
            fail_count += 1

        # 请求间隔避免限流
        if i < total - 1:
            await asyncio.sleep(3)

    # 汇总
    print(f"\n{'='*60}")
    print(f"生成完成: {success_count}/{total} 成功, {fail_count}/{total} 失败")
    print(f"总耗时: {total_time:.0f}s (平均 {total_time/max(success_count,1):.1f}s/张)")
    print(f"输出目录: {output_dir}")
    print(f"{'='*60}\n")

    return success_count


if __name__ == "__main__":
    count = asyncio.run(generate_new_thumbnails())
    sys.exit(0 if count == 13 else 1)
