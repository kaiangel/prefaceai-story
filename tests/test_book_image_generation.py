"""
书籍解说视频图片生成测试

Side Test: 验证 image_prompt 能否生成符合预期的图片

用法：
    python tests/test_book_image_generation.py

输出：
    test_output/book_narration_test/images/
    ├── shot_01.png
    ├── shot_02.png
    └── ...
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.image_generator import ImageGenerator
from app.services.style_enforcer import StyleEnforcer


# ===== 配置 =====
INPUT_DIR = Path(__file__).parent.parent / "test_output" / "book_narration_test"
OUTPUT_DIR = INPUT_DIR / "images"
STORYBOARD_FILE = INPUT_DIR / "3_storyboard.json"

# 生成配置
MAX_SHOTS = 3  # 只生成前3张图片用于测试（节省成本）
USE_PRO_MODEL = False  # 书籍解说不需要角色一致性，用Flash即可


async def generate_test_images():
    """生成测试图片"""

    print("=" * 70)
    print("  书籍解说视频 - 图片生成测试 (Side Test)")
    print("=" * 70)
    print()

    # 检查输入文件
    if not STORYBOARD_FILE.exists():
        print(f"错误: 找不到 storyboard 文件: {STORYBOARD_FILE}")
        print("请先运行 test_book_narration_experiment.py 生成 storyboard")
        return False

    # 读取 storyboard
    with open(STORYBOARD_FILE, "r", encoding="utf-8") as f:
        storyboard = json.load(f)

    shots = storyboard.get("shots", [])
    visual_style = storyboard.get("visual_style", "illustration")

    print(f"Storyboard: {len(shots)} shots")
    print(f"Visual Style: {visual_style}")
    print(f"测试生成: 前 {MAX_SHOTS} 张图片")
    print(f"模型: {'Pro' if USE_PRO_MODEL else 'Flash'}")
    print()

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 初始化服务
    image_generator = ImageGenerator()

    # 生成图片
    results = []
    test_shots = shots[:MAX_SHOTS]

    for i, shot in enumerate(test_shots):
        shot_id = shot.get("shot_id", i + 1)
        image_prompt = shot.get("image_prompt", "")

        print("=" * 60)
        print(f"[Shot {shot_id}] 生成中...")
        print("=" * 60)
        print(f"Prompt ({len(image_prompt)} chars):")
        print(f"  {image_prompt[:200]}...")
        print()

        # 应用风格强制 (类方法)
        final_prompt = StyleEnforcer.enforce_prompt(image_prompt, visual_style)

        # 生成图片
        result = await image_generator.generate_image(
            prompt=final_prompt,
            aspect_ratio="16:9",
            use_pro_model=USE_PRO_MODEL,
            style_preset=visual_style
        )

        if result.get("success"):
            # 保存图片
            output_path = OUTPUT_DIR / f"shot_{shot_id:02d}.png"
            pil_image = result.get("pil_image")
            if pil_image:
                pil_image.save(output_path)
                print(f"保存: {output_path}")
                print(f"尺寸: {result.get('width')}x{result.get('height')}")
                print(f"耗时: {result.get('generation_time_seconds', 0):.1f}s")
                results.append({
                    "shot_id": shot_id,
                    "success": True,
                    "path": str(output_path),
                    "time": result.get("generation_time_seconds", 0)
                })
        else:
            print(f"失败: {result.get('error', '未知错误')}")
            results.append({
                "shot_id": shot_id,
                "success": False,
                "error": result.get("error", "未知错误")
            })

        print()

    # 总结
    print("=" * 70)
    print("  测试总结")
    print("=" * 70)
    print()

    success_count = sum(1 for r in results if r.get("success"))
    total_time = sum(r.get("time", 0) for r in results)

    print(f"成功: {success_count}/{len(results)}")
    print(f"总耗时: {total_time:.1f}s")
    print()

    if success_count > 0:
        print(f"图片输出目录: {OUTPUT_DIR}")
        print()
        print("生成的图片:")
        for r in results:
            if r.get("success"):
                print(f"  - {r.get('path')}")

    # 保存结果
    results_file = INPUT_DIR / "image_generation_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump({
            "total_shots": len(test_shots),
            "success_count": success_count,
            "total_time_seconds": total_time,
            "model": "Pro" if USE_PRO_MODEL else "Flash",
            "visual_style": visual_style,
            "results": results
        }, f, ensure_ascii=False, indent=2)
    print(f"\n结果保存: {results_file}")

    return success_count == len(results)


if __name__ == "__main__":
    # 检查环境变量
    if not os.environ.get("GEMINI_API_KEY"):
        # 尝试从 .env 加载
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        key = line.strip().split("=", 1)[1]
                        os.environ["GEMINI_API_KEY"] = key
                        break

    if not os.environ.get("GEMINI_API_KEY"):
        print("错误: 未设置 GEMINI_API_KEY 环境变量")
        sys.exit(1)

    success = asyncio.run(generate_test_images())
    sys.exit(0 if success else 1)
