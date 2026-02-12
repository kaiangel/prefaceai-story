"""
书籍解说视频生成实验测试脚本

Side Test: 验证序话Story能否用于生成书籍解说视频

用法：
    python tests/test_book_narration_experiment.py

输出：
    test_output/book_narration_test/
    ├── 1_book_outline.json
    ├── 2_narration_script.json
    └── 3_storyboard.json
"""

import asyncio
import json
import os
import re
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from google import genai

# 导入书籍解说Prompt
from app.prompts.book.book_outline_prompt import (
    build_book_outline_prompt,
    BOOK_OUTLINE_EXAMPLE_INPUT
)
from app.prompts.book.book_narration_prompt import (
    build_book_narration_prompt,
    BOOK_NARRATION_EXAMPLE_INPUT
)
from app.prompts.book.book_storyboard_prompt import (
    build_book_storyboard_prompt,
    BOOK_STORYBOARD_EXAMPLE_INPUT
)


# ===== 配置 =====
OUTPUT_DIR = Path(__file__).parent.parent / "test_output" / "book_narration_test"
GEMINI_MODEL = "gemini-3-flash-preview"  # 使用Flash模型，与项目其他地方一致


# ===== 测试输入 =====
BOOK_INPUT = {
    "title": "人类简史",
    "author": "尤瓦尔·赫拉利",
    "summary": """
《人类简史》讲述了人类从7万年前的认知革命到21世纪的科技革命的历程。

核心观点：
1. 认知革命：智人能够创造和相信虚构故事（神话、宗教、国家、货币），这是人类统治地球的关键
2. 农业革命是"史上最大骗局"：人类以为驯化了小麦，实际上是小麦驯化了人类
3. 帝国、货币、宗教是统一人类的三大力量
4. 科学革命：承认无知是进步的开始
5. 快乐悖论：物质进步不等于幸福增加
""",
    "target_duration": 180,  # 3分钟
    "num_insights": 5,
    "style": "illustration"
}


def extract_json(text: str) -> dict:
    """从LLM响应中提取JSON"""
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试从markdown代码块提取
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # 尝试找到JSON对象
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"无法从响应中提取JSON:\n{text[:500]}...")


async def call_gemini(client: genai.Client, prompt: str, stage_name: str) -> dict:
    """调用Gemini API并返回解析后的JSON"""
    print(f"\n{'='*60}")
    print(f"[Stage] {stage_name}")
    print(f"{'='*60}")
    print(f"Prompt长度: {len(prompt)} 字符")

    try:
        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={"max_output_tokens": 8192}
        )
        raw_text = response.text
        print(f"响应长度: {len(raw_text)} 字符")

        result = extract_json(raw_text)
        print(f"✅ JSON解析成功")
        return result

    except Exception as e:
        print(f"❌ 调用失败: {e}")
        raise


def validate_stage1(outline: dict) -> list:
    """验证Stage 1输出"""
    issues = []

    # 检查key_insights
    insights = outline.get("key_insights", [])
    if len(insights) < 3:
        issues.append(f"key_insights数量不足: {len(insights)} < 3")

    for i, insight in enumerate(insights):
        # 检查visual_concept是英文
        vc = insight.get("visual_concept", "")
        if not vc:
            issues.append(f"insight {i+1} 缺少 visual_concept")
        elif any('\u4e00' <= c <= '\u9fff' for c in vc):
            issues.append(f"insight {i+1} visual_concept 包含中文字符")

        # 检查禁止的文字/图表描述
        forbidden = ["text showing", "chart", "diagram", "infographic", "timeline"]
        for word in forbidden:
            if word.lower() in vc.lower():
                issues.append(f"insight {i+1} visual_concept 包含禁止词: {word}")

    return issues


def validate_stage2(narration: dict) -> list:
    """验证Stage 2输出"""
    issues = []

    segments = narration.get("narration_segments", [])
    if len(segments) < 2:
        issues.append(f"narration_segments数量不足: {len(segments)} < 2")

    for i, seg in enumerate(segments):
        # 检查narration_text是中文
        nt = seg.get("narration_text", "")
        if not nt:
            issues.append(f"segment {i+1} 缺少 narration_text")
        elif not any('\u4e00' <= c <= '\u9fff' for c in nt):
            issues.append(f"segment {i+1} narration_text 不是中文")

        # 检查visual_direction是英文
        vd = seg.get("visual_direction", "")
        if not vd:
            issues.append(f"segment {i+1} 缺少 visual_direction")
        elif any('\u4e00' <= c <= '\u9fff' for c in vd):
            issues.append(f"segment {i+1} visual_direction 包含中文字符")

    return issues


def validate_stage3(storyboard: dict) -> list:
    """验证Stage 3输出"""
    issues = []

    shots = storyboard.get("shots", [])
    if len(shots) < 2:
        issues.append(f"shots数量不足: {len(shots)} < 2")

    for i, shot in enumerate(shots):
        # 检查image_prompt是英文
        ip = shot.get("image_prompt", "")
        if not ip:
            issues.append(f"shot {i+1} 缺少 image_prompt")
        elif any('\u4e00' <= c <= '\u9fff' for c in ip):
            issues.append(f"shot {i+1} image_prompt 包含中文字符")

        # 检查禁止的文字/图表描述
        forbidden = ["text showing", "text appears", "chart", "diagram", "infographic"]
        for word in forbidden:
            if word.lower() in ip.lower():
                issues.append(f"shot {i+1} image_prompt 包含禁止词: {word}")

    return issues


async def run_test():
    """运行完整测试流程"""
    print("="*70)
    print("  书籍解说视频生成实验 - Side Test")
    print("  测试用例: 《人类简史》")
    print("="*70)

    # 检查API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置 GEMINI_API_KEY 环境变量")
        return False

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n输出目录: {OUTPUT_DIR}")

    # 初始化Gemini客户端
    client = genai.Client(api_key=api_key)
    print(f"模型: {GEMINI_MODEL}")

    all_issues = []

    # ===== Stage 1: 书籍要点提炼 =====
    stage1_prompt = build_book_outline_prompt(
        book_title=BOOK_INPUT["title"],
        author=BOOK_INPUT["author"],
        book_summary=BOOK_INPUT["summary"],
        target_duration=BOOK_INPUT["target_duration"],
        num_insights=BOOK_INPUT["num_insights"],
        style=BOOK_INPUT["style"]
    )

    outline = await call_gemini(client, stage1_prompt, "Stage 1: 书籍要点提炼")

    # 保存输出
    with open(OUTPUT_DIR / "1_book_outline.json", "w", encoding="utf-8") as f:
        json.dump(outline, f, ensure_ascii=False, indent=2)
    print(f"📁 保存: 1_book_outline.json")

    # 验证
    stage1_issues = validate_stage1(outline)
    if stage1_issues:
        print("⚠️ Stage 1 验证问题:")
        for issue in stage1_issues:
            print(f"   - {issue}")
        all_issues.extend(stage1_issues)
    else:
        print("✅ Stage 1 验证通过")

    # ===== Stage 2: 解说脚本生成 =====
    stage2_prompt = build_book_narration_prompt(outline)

    narration = await call_gemini(client, stage2_prompt, "Stage 2: 解说脚本生成")

    # 保存输出
    with open(OUTPUT_DIR / "2_narration_script.json", "w", encoding="utf-8") as f:
        json.dump(narration, f, ensure_ascii=False, indent=2)
    print(f"📁 保存: 2_narration_script.json")

    # 验证
    stage2_issues = validate_stage2(narration)
    if stage2_issues:
        print("⚠️ Stage 2 验证问题:")
        for issue in stage2_issues:
            print(f"   - {issue}")
        all_issues.extend(stage2_issues)
    else:
        print("✅ Stage 2 验证通过")

    # ===== Stage 3: 配图分镜 =====
    stage3_prompt = build_book_storyboard_prompt(
        narration_script=narration,
        visual_style=BOOK_INPUT["style"]
    )

    storyboard = await call_gemini(client, stage3_prompt, "Stage 3: 配图分镜")

    # 保存输出
    with open(OUTPUT_DIR / "3_storyboard.json", "w", encoding="utf-8") as f:
        json.dump(storyboard, f, ensure_ascii=False, indent=2)
    print(f"📁 保存: 3_storyboard.json")

    # 验证
    stage3_issues = validate_stage3(storyboard)
    if stage3_issues:
        print("⚠️ Stage 3 验证问题:")
        for issue in stage3_issues:
            print(f"   - {issue}")
        all_issues.extend(stage3_issues)
    else:
        print("✅ Stage 3 验证通过")

    # ===== 总结 =====
    print("\n" + "="*70)
    print("  测试总结")
    print("="*70)

    if all_issues:
        print(f"\n❌ 发现 {len(all_issues)} 个问题:")
        for issue in all_issues:
            print(f"   - {issue}")
        print("\n建议: 检查Prompt模板，调整约束强度")
        return False
    else:
        print("\n✅ 所有验证通过!")
        print("\n输出文件:")
        print(f"   - {OUTPUT_DIR / '1_book_outline.json'}")
        print(f"   - {OUTPUT_DIR / '2_narration_script.json'}")
        print(f"   - {OUTPUT_DIR / '3_storyboard.json'}")
        print("\n下一步: 可以使用ImageGenerator生成测试图片")
        return True


if __name__ == "__main__":
    success = asyncio.run(run_test())
    sys.exit(0 if success else 1)
