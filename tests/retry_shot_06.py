#!/usr/bin/env python3
"""
单独重试 Shot 06 生成
"""
import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from PIL import Image
from app.services.image_generator import ImageGenerator

# 输出目录
OUTPUT_DIR = Path("test_output/comic_full_story_v2_wuxia_ink")
REF_DIR = OUTPUT_DIR / "reference_images"
NO_TEXT_DIR = OUTPUT_DIR / "no_text_images"
WITH_TEXT_DIR = OUTPUT_DIR / "with_text_images"

# 水墨风格前缀
INK_WASH_STYLE_PREFIX = """═══════════════════════════════════════════════════════════
MANDATORY STYLE REQUIREMENT - DO NOT IGNORE THIS SECTION
═══════════════════════════════════════════════════════════

STYLE: Chinese Ink Wash (水墨画)

This MUST be rendered in traditional Chinese ink wash painting style:
- Brush stroke textures visible throughout
- Ink wash gradients from deep black to pale gray
- Rice paper texture feel
- Intentional white space (留白) as compositional element
- Atmospheric depth through ink density variation
- Traditional Chinese aesthetic sensibility

MUST INCLUDE: brush strokes, ink wash, sumi-e technique, rice paper texture, traditional Chinese art

DO NOT USE: photorealistic, colorful, neon, 3D render, Western art style, digital art look

This style requirement applies to ALL elements in this image.
═══════════════════════════════════════════════════════════
"""

MEMORY_SCENE_TREATMENT = """
MEMORY/FLASHBACK TREATMENT:
- Warmer sepia-tinted ink tones (not pure black)
- Softer brush strokes, slightly dreamlike quality
- Lighter overall ink density
- Gentle vignette effect at edges
- Nostalgic, melancholic atmosphere
"""

TEXT_FREE_REQUIREMENT = """
═══════════════════════════════════════════════════════════
ABSOLUTELY NO TEXT ALLOWED - CRITICAL REQUIREMENT
═══════════════════════════════════════════════════════════

This image must contain ZERO visible text, characters, letters, or words in any language.

DO NOT draw any:
- Speech bubbles or dialogue balloons
- Caption boxes or text areas
- Written characters (Chinese, English, or any language)
- Signs, labels, or watermarks
- Any rectangular areas that look like text placeholders

Fill the ENTIRE image with visual content only.
Any visible text will cause this image to FAIL.

═══════════════════════════════════════════════════════════
"""

# Shot 06 配置 - 极简版本，完全避免敏感内容
SHOT_06 = {
    "shot_id": 6,
    "scene": "好友之弟倒下 - 俯视绝望",
    "text_type": "thought",
    "speaker_position": "bottom",
    "chinese_text": "他才十六岁...是周沧的亲弟弟...！！！",
    "is_memory": True,
    "emphasis": "red_highlight",
    "characters": ["master_young"],
    "image_prompt": f"""{INK_WASH_STYLE_PREFIX}
{MEMORY_SCENE_TREATMENT}

---

A young swordsman in dark blue silk robes kneeling alone in an empty traditional Chinese tavern. High-angle view looking down at him. His sword lies on the wooden floor beside him.

He is kneeling with his head bowed, hands on his knees, expressing deep contemplation and sadness. His black hair is in a high topknot, partially loosened.

The tavern interior shows wooden beams overhead, paper lanterns, and wine jars in the background. Soft warm light filters through. The scene is rendered in warm sepia-tinted ink wash style with soft brush strokes.

A moment of quiet reflection and regret. Melancholic atmosphere.

{TEXT_FREE_REQUIREMENT}
"""
}


async def retry_shot_06():
    """重试生成 Shot 06"""
    print("=" * 70)
    print("重试 Shot 06: 好友之弟倒下 - 俯视绝望")
    print("=" * 70)

    # 初始化
    image_gen = ImageGenerator()

    # 加载 master_young 参考图
    ref_path = REF_DIR / "master_young_fullbody.png"
    if not ref_path.exists():
        print(f"❌ 参考图不存在: {ref_path}")
        return False

    print(f"  📷 使用参考图: {ref_path}")
    ref_image = Image.open(ref_path)

    # 构建 prompt
    prompt = f"""
CHARACTER REFERENCE IMAGES:
The following reference images show the characters that should appear in this scene.
CRITICAL: Match each character's appearance EXACTLY as shown in their reference images.

Image 1: Reference for master_young (白川年轻时) - Young swordsman with black hair in high topknot, wearing dark blue silk robes

---

{SHOT_06['image_prompt']}
"""

    print(f"  🎯 开始生成...")

    # 生成图片 - 先尝试不带参考图
    try:
        print("  🔄 尝试不带参考图生成...")
        result = await image_gen.generate_image(
            prompt=SHOT_06['image_prompt'],  # 直接用原始 prompt，不加参考图说明
            reference_images=None,  # 不带参考图
            aspect_ratio="9:16"
        )

        if result and result.get("image"):
            # 保存图片
            image = result["image"]
            no_text_path = NO_TEXT_DIR / "shot_06.png"
            image.save(no_text_path)
            print(f"  ✅ 图片生成成功: {no_text_path}")

            # 复制到 with_text 目录（稍后需要叠加文字）
            with_text_path = WITH_TEXT_DIR / "shot_06.png"
            image.save(with_text_path)
            print(f"  ✅ 已复制到: {with_text_path}")

            return True
        else:
            print(f"  ❌ 生成失败: 返回结果为空")
            return False

    except Exception as e:
        print(f"  ❌ 生成异常: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    success = await retry_shot_06()

    if success:
        print("\n" + "=" * 70)
        print("✅ Shot 06 重试成功!")
        print("=" * 70)
        print("\n请检查生成的图片:")
        print(f"  - 无文字: test_output/comic_full_story_v2_wuxia_ink/no_text_images/shot_06.png")
        print(f"  - 叠加后: test_output/comic_full_story_v2_wuxia_ink/with_text_images/shot_06.png")
        print("\n注意: 叠加的图片还需要添加文字，目前只是原图副本")
    else:
        print("\n" + "=" * 70)
        print("❌ Shot 06 重试失败")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
