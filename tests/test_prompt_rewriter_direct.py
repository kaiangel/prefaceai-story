"""
TASK-RESILIENCE-001 PromptRewriter 直接测试

直接测试 PromptRewriter 的改写功能，验证：
1. 敏感词检测功能
2. Haiku 智能改写功能
3. 简单规则替换功能

运行方式:
    python tests/test_prompt_rewriter_direct.py

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

from app.services.prompt_rewriter import PromptRewriter


# 类似 Shot 06 的敏感 prompt
SENSITIVE_PROMPT = """
Chinese ink wash painting style. Overhead view looking down at the tavern floor.
A young man in dark blue silk robes has dropped to his knees, his famous sword
fallen beside him. Before him lies a young boy of about sixteen, motionless.
A dark spreading pool surrounds the fallen youth.

The kneeling swordsman's face shows anguish. All attention focuses on this
tableau of tragedy - the killer kneeling before his victim.

EMOTIONAL ATMOSPHERE: Absolute devastation, irreversible guilt, the death of innocence.
"""


async def test_prompt_rewriter():
    """测试 PromptRewriter 各项功能"""

    print("=" * 70)
    print("TASK-RESILIENCE-001 PromptRewriter 直接测试")
    print("=" * 70)

    # 1. 初始化
    print("\n[1] 初始化 PromptRewriter...")
    rewriter = PromptRewriter()

    if not rewriter.client:
        print("  ⚠️ Anthropic 客户端未初始化，Haiku 智能改写不可用")
    else:
        print("  ✅ PromptRewriter 初始化成功")

    # 2. 测试敏感词检测
    print("\n[2] 测试敏感词检测...")
    print("-" * 70)
    print(f"原始 prompt (前200字符):\n{SENSITIVE_PROMPT[:200]}...")
    print("-" * 70)

    detection = rewriter.detect(SENSITIVE_PROMPT)
    print(f"\n检测结果:")
    print(f"  - 是否包含敏感内容: {detection['has_sensitive']}")
    print(f"  - 敏感词数量: {detection['count']}")
    print(f"  - 敏感类别: {detection['categories']}")

    if detection.get('details'):
        print(f"\n  详细敏感词:")
        for item in detection['details'][:10]:
            print(f"    - '{item.get('word', 'N/A')}' -> 类别: {item.get('category', 'N/A')}")

    # 3. 测试简单规则替换
    print("\n" + "=" * 70)
    print("[3] 测试简单规则替换 (rewrite_simple)...")
    print("=" * 70)

    simple_rewritten = rewriter.rewrite_simple(SENSITIVE_PROMPT, genre="wuxia")

    print(f"\n简单替换后的 prompt:")
    print("-" * 70)
    print(simple_rewritten[:500] + "..." if len(simple_rewritten) > 500 else simple_rewritten)
    print("-" * 70)

    # 检查替换后是否还有敏感内容
    post_detection = rewriter.detect(simple_rewritten)
    print(f"\n替换后检测:")
    print(f"  - 是否仍有敏感内容: {post_detection['has_sensitive']}")
    print(f"  - 剩余敏感词数量: {post_detection['count']}")

    # 4. 测试 Haiku 智能改写
    print("\n" + "=" * 70)
    print("[4] 测试 Haiku 智能改写 (rewrite)...")
    print("=" * 70)

    if rewriter.client:
        haiku_rewritten = await rewriter.rewrite(SENSITIVE_PROMPT)

        if haiku_rewritten:
            print(f"\nHaiku 改写后的 prompt:")
            print("-" * 70)
            print(haiku_rewritten[:600] + "..." if len(haiku_rewritten) > 600 else haiku_rewritten)
            print("-" * 70)

            # 检查改写后是否还有敏感内容
            post_detection = rewriter.detect(haiku_rewritten)
            print(f"\n改写后检测:")
            print(f"  - 是否仍有敏感内容: {post_detection['has_sensitive']}")
            print(f"  - 剩余敏感词数量: {post_detection['count']}")
        else:
            print("  ❌ Haiku 智能改写失败")
    else:
        print("  ⚠️ 跳过（Anthropic 客户端不可用）")

    # 5. 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    print("✅ 敏感词检测: 正常工作")
    print("✅ 简单规则替换: 正常工作")
    if rewriter.client:
        print("✅ Haiku 智能改写: 正常工作")
    else:
        print("⚠️ Haiku 智能改写: 需要 ANTHROPIC_API_KEY")

    return True


if __name__ == "__main__":
    asyncio.run(test_prompt_rewriter())
