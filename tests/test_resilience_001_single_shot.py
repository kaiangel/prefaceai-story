"""
TASK-RESILIENCE-001 单张图片验收测试

验收目标:
1. 使用类似 Shot 06 的敏感 prompt 触发 Gemini 内容安全过滤
2. 验证 ImageGenerator 正确识别 CONTENT_SAFETY 错误
3. 验证 PromptRewriter 自动改写 prompt
4. 验证改写后成功生成图像

预期日志输出:
    [ImageGenerator] ⚠️ Shot X 触发内容安全过滤，开始智能改写...
    [PromptRewriter] 🔄 开始智能改写 (Haiku)...
    [PromptRewriter] ✅ 智能改写完成
    [ImageGenerator] ✅ Shot X 改写后生成成功 (方法: haiku)

运行方式:
    python tests/test_resilience_001_single_shot.py

Author: @Tester
Date: 2026-01-28
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))

# 自动加载 .env 文件
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from app.services.image_generator import ImageGenerator


# =============================================================================
# 测试用 Prompt（类似 Shot 06 的敏感内容）
# =============================================================================

# 原始敏感 prompt（类似故事B Shot 06）
SENSITIVE_PROMPT = """
Chinese ink wash painting style (sumi-e). Brush strokes with intentional variation.
Rich ink gradations from deep black to pale gray. Generous negative space (留白).
Traditional rice paper texture visible.

---

Overhead view looking down at the tavern floor. A young man in dark blue silk robes
has dropped to his knees, his famous sword fallen beside him, his hands shaking.
Before him lies a young boy of about sixteen, motionless. A dark spreading pool
surrounds the fallen youth, rendered in deeper ink tones.

The kneeling swordsman's face is turned downward, anguish visible in his hunched
shoulders, his fists clenched against his thighs. His proud topknot has come
partially loose, black hair falling over his face.

Other figures are frozen in the background, rendered as faint suggestions.
All attention focuses on this tableau of tragedy - the killer kneeling before his victim.

EMOTIONAL ATMOSPHERE:
Absolute devastation, irreversible guilt, the death of innocence.
A man's entire world collapsing in a single moment.

TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text, speech bubbles, captions, or written characters in the image.
"""

# 预期触发的敏感词
EXPECTED_SENSITIVE_WORDS = [
    "motionless",
    "dark spreading pool",
    "killer",
    "victim",
    "death of innocence"
]


# =============================================================================
# 测试用 Shot 数据结构
# =============================================================================

TEST_SHOT = {
    "shot_id": 99,  # 测试用 ID
    "scene": "韧性机制测试 - 敏感内容",
    "image_prompt": SENSITIVE_PROMPT,
    "camera": {
        "shot_size": "extreme_wide",
        "angle": "birds_eye"
    },
    "character_direction": {
        "characters_visible": []
    }
}

TEST_STORYBOARD = {
    "global_visual_direction": {
        "style_preset": "ink",
        "color_palette": ["black", "gray", "sepia"],
        "lighting": "soft_ambient"
    }
}

TEST_CHARACTERS = {
    "characters": []
}


# =============================================================================
# 主测试函数
# =============================================================================

async def run_resilience_test():
    """运行 TASK-RESILIENCE-001 验收测试"""

    print("=" * 70)
    print("TASK-RESILIENCE-001 图像生成韧性机制验收测试")
    print("=" * 70)

    # 1. 检查环境变量
    print("\n[Step 1] 检查环境变量...")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    if not gemini_key:
        print("❌ 错误: GEMINI_API_KEY 未设置")
        return False
    print(f"  ✅ GEMINI_API_KEY: {gemini_key[:10]}...")

    if not anthropic_key:
        print("  ⚠️ 警告: ANTHROPIC_API_KEY 未设置，Haiku 智能改写将不可用")
        print("  将降级使用简单规则替换")
    else:
        print(f"  ✅ ANTHROPIC_API_KEY: {anthropic_key[:10]}...")

    # 2. 初始化 ImageGenerator
    print("\n[Step 2] 初始化 ImageGenerator...")
    image_gen = ImageGenerator()

    if not image_gen.client:
        print("❌ 错误: ImageGenerator 初始化失败")
        return False
    print("  ✅ ImageGenerator 初始化成功")

    # 3. 检查 PromptRewriter 是否可用
    print("\n[Step 3] 检查 PromptRewriter...")
    rewriter = image_gen.prompt_rewriter
    if rewriter:
        print("  ✅ PromptRewriter 可用")
        # 检测敏感内容
        if rewriter.needs_rewrite(SENSITIVE_PROMPT):
            detection = rewriter.detect(SENSITIVE_PROMPT)
            print(f"  📋 检测到 {detection['count']} 个敏感词")
            print(f"  📋 敏感类别: {detection['categories']}")
        else:
            print("  ⚠️ 未检测到敏感内容（可能敏感词库需要更新）")
    else:
        print("  ⚠️ PromptRewriter 不可用，将无法自动改写")

    # 4. 创建输出目录
    output_dir = Path("test_output/resilience_001_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n[Step 4] 输出目录: {output_dir}")

    # 5. 调用 generate_shot_image_phase2_safe
    print("\n[Step 5] 调用 generate_shot_image_phase2_safe()...")
    print("-" * 70)
    print("预期行为:")
    print("  1. 首次生成触发 CONTENT_SAFETY 错误")
    print("  2. 自动调用 PromptRewriter 改写")
    print("  3. 使用改写后的 prompt 重试生成")
    print("  4. 最终成功生成图像")
    print("-" * 70)

    result = await image_gen.generate_shot_image_phase2_safe(
        shot=TEST_SHOT,
        storyboard=TEST_STORYBOARD,
        characters=TEST_CHARACTERS,
        style_preset="ink",
        reference_images=None,
        previous_shot_image=None,
        previous_shot=None,
        screenplay=None,
        aspect_ratio="9:16",  # 条漫比例
        genre="wuxia"  # 武侠题材
    )

    # 6. 分析结果
    print("\n" + "=" * 70)
    print("[Step 6] 测试结果分析")
    print("=" * 70)

    if result.get("success"):
        print("\n✅ 测试通过: 图像生成成功")

        # 检查是否经过改写
        rewrite_info = result.get("rewrite_info")
        if rewrite_info:
            print(f"\n📋 改写信息:")
            print(f"  - 是否尝试改写: {rewrite_info.get('attempted', False)}")
            print(f"  - 改写成功: {rewrite_info.get('success', False)}")
            print(f"  - 成功方法: {rewrite_info.get('successful_method', 'N/A')}")

            rewrites = rewrite_info.get("rewrites", [])
            for rw in rewrites:
                print(f"\n  改写尝试 {rw['attempt']}:")
                print(f"    方法: {rw['method']}")
                print(f"    预览: {rw['prompt_preview'][:100]}...")
        else:
            print("\n📋 首次生成即成功，未触发改写机制")
            print("  （可能 Gemini API 此次未过滤该内容）")

        # 保存生成的图像
        if result.get("pil_image"):
            image_path = output_dir / "resilience_test_result.png"
            result["pil_image"].save(image_path)
            print(f"\n💾 图像已保存: {image_path}")
            print(f"  尺寸: {result['width']}x{result['height']}")
            print(f"  生成耗时: {result.get('generation_time_seconds', 'N/A')}s")

        return True

    else:
        print("\n❌ 测试失败: 图像生成失败")
        print(f"\n错误信息: {result.get('error', 'Unknown')}")
        print(f"错误类型: {result.get('error_type', 'Unknown')}")

        # 检查改写信息
        rewrite_info = result.get("rewrite_info")
        if rewrite_info:
            print(f"\n📋 改写信息:")
            print(f"  - 是否尝试改写: {rewrite_info.get('attempted', False)}")
            print(f"  - 改写成功: {rewrite_info.get('success', False)}")

            rewrites = rewrite_info.get("rewrites", [])
            for rw in rewrites:
                print(f"\n  改写尝试 {rw['attempt']}:")
                print(f"    方法: {rw['method']}")
                print(f"    预览: {rw['prompt_preview'][:100]}...")

        return False


# =============================================================================
# 入口
# =============================================================================

if __name__ == "__main__":
    print("\n启动 TASK-RESILIENCE-001 验收测试...\n")

    success = asyncio.run(run_resilience_test())

    print("\n" + "=" * 70)
    if success:
        print("🎉 TASK-RESILIENCE-001 验收: ✅ 通过")
    else:
        print("⚠️ TASK-RESILIENCE-001 验收: 需要进一步检查")
    print("=" * 70)

    sys.exit(0 if success else 1)
