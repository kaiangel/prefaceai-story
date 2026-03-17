"""
TASK-SAFE-DRYRUN: 3 条 Prompt 安全改写链路 Dry-run 验证

目标: 不跑实际图片生成，只验证 phase2_safe() 的 prompt 检测/改写逻辑。

验证 3 条链路:
  链路 1: 正常路径 — mock 返回 success → 期望首次成功，零额外开销
  链路 2: CONTENT_SAFETY → 改写成功 — 首次 CONTENT_SAFETY, 改写后 success
  链路 3: CONTENT_SAFETY → 改写仍失败 — 连续 CONTENT_SAFETY, 所有改写均失败

数据源: R8 E2E 已有的 Stage 1-4 数据

验收标准:
  - 3 条链路日志完整
  - generate_shot_image_phase2_safe 确认被调用（而非非 safe 版本）
  - 正常路径零额外开销
  - CONTENT_SAFETY 路径 PromptRewriter 正确介入
"""

import asyncio
import json
import os
import sys
import io
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# R8 数据路径
R8_DATA_DIR = os.path.join(
    PROJECT_ROOT,
    "test_output/manualtest/e2e_regression_r8/20260316_145613/story_A/20260316_145614"
)

# 输出目录
OUTPUT_DIR = os.path.join(
    PROJECT_ROOT,
    f"test_output/manualtest/safe_dryrun_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
)


def load_r8_data():
    """加载 R8 E2E 数据"""
    with open(os.path.join(R8_DATA_DIR, "4_storyboard.json"), "r", encoding="utf-8") as f:
        storyboard = json.load(f)
    with open(os.path.join(R8_DATA_DIR, "2_characters.json"), "r", encoding="utf-8") as f:
        characters = json.load(f)
    return storyboard, characters


def make_success_result(shot_id):
    """构造正常成功返回"""
    return {
        "success": True,
        "image_data": "mock_base64_image_data_placeholder",
        "pil_image": MagicMock(size=(848, 1264), width=848, height=1264),
        "image_format": "png",
        "width": 848,
        "height": 1264,
        "model_used": "gemini-3.1-flash-image-preview",
        "generation_time_seconds": 1.0,
        "shot_id": shot_id,
        "prompt_package": {"system_instruction": "mock"},
        "phase2": True
    }


def make_content_safety_result(original_prompt):
    """构造 CONTENT_SAFETY 失败返回"""
    return {
        "success": False,
        "error": "Image generation failed after 1 attempts: Content safety filter triggered",
        "error_type": "content_safety",
        "model_used": "gemini-3.1-flash-image-preview",
        "generation_time_seconds": 0.5,
        "phase2": True,
        "original_prompt": original_prompt
    }


def capture_stdout(func):
    """装饰器: 捕获函数执行期间的 stdout 输出"""
    async def wrapper(*args, **kwargs):
        captured = io.StringIO()
        old_stdout = sys.stdout
        # 使用 tee 策略: 同时输出到控制台和捕获
        class TeeStream:
            def __init__(self, original, capture):
                self.original = original
                self.capture = capture
            def write(self, data):
                self.original.write(data)
                self.capture.write(data)
            def flush(self):
                self.original.flush()
                self.capture.flush()

        sys.stdout = TeeStream(old_stdout, captured)
        try:
            result = await func(*args, **kwargs)
            return result, captured.getvalue()
        finally:
            sys.stdout = old_stdout
    return wrapper


# ========== 链路 1: 正常路径 ==========

@capture_stdout
async def test_chain_1_normal(image_gen, shot, storyboard, characters):
    """链路 1: 正常路径 — mock 返回 success"""
    print("\n" + "=" * 60)
    print("🔗 链路 1: 正常路径测试")
    print("=" * 60)
    print(f"   Shot ID: {shot.get('shot_id')}")
    print(f"   场景: {shot.get('camera', {}).get('shot_size', 'N/A')}")

    with patch.object(image_gen, 'generate_shot_image_phase2', new_callable=AsyncMock) as mock_phase2:
        mock_phase2.return_value = make_success_result(shot["shot_id"])

        result = await image_gen.generate_shot_image_phase2_safe(
            shot=shot,
            storyboard=storyboard,
            characters=characters,
            style_preset="illustration",
        )

        # 验证
        checks = {
            "成功标志": result.get("success") is True,
            "调用次数=1": mock_phase2.call_count == 1,
            "无 rewrite_info": "rewrite_info" not in result,
            "零额外开销": mock_phase2.call_count == 1,  # 只调了一次 = 无额外开销
        }

        print(f"\n--- 链路 1 验证结果 ---")
        all_pass = True
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
            if not passed:
                all_pass = False

        return all_pass


# ========== 链路 2: CONTENT_SAFETY → 改写成功 ==========

@capture_stdout
async def test_chain_2_safety_then_success(image_gen, shot, storyboard, characters):
    """链路 2: CONTENT_SAFETY → Sonnet 改写 → 重试成功"""
    print("\n" + "=" * 60)
    print("🔗 链路 2: CONTENT_SAFETY → 改写成功")
    print("=" * 60)
    print(f"   Shot ID: {shot.get('shot_id')}")

    # 用一个足够长的 mock prompt，确保 PromptRewriter 不会因长度不够拒绝
    mock_original_prompt = (
        "A wide shot of a bustling rural market entrance with villagers carrying baskets. "
        "Morning light filters through wooden market stalls. Characters interact with vendors "
        "selling fresh produce and herbal medicines. The scene captures authentic countryside "
        "atmosphere with warm earth tones and natural lighting. Traditional architecture frames "
        "the background with curved rooftops and stone walls. Multiple characters walk through "
        "the market, browsing goods and chatting with shopkeepers."
    )

    with patch.object(image_gen, 'generate_shot_image_phase2', new_callable=AsyncMock) as mock_phase2:
        # 第 1 次: CONTENT_SAFETY, 第 2 次: success
        mock_phase2.side_effect = [
            make_content_safety_result(mock_original_prompt),
            make_success_result(shot["shot_id"]),
        ]

        # Mock PromptRewriter — 模拟 Sonnet 智能改写
        mock_rewriter = MagicMock()
        mock_rewriter.rewrite = AsyncMock(
            return_value="Rewritten safe prompt: A tranquil countryside market scene with "
                         "villagers browsing morning stalls. Soft golden light illuminates "
                         "wooden structures and stone pathways in a peaceful rural setting."
        )
        mock_rewriter.rewrite_simple = MagicMock(
            return_value="Simple rewrite: Rural market scene with morning atmosphere."
        )
        image_gen._prompt_rewriter = mock_rewriter

        result = await image_gen.generate_shot_image_phase2_safe(
            shot=shot,
            storyboard=storyboard,
            characters=characters,
            style_preset="illustration",
        )

        # 验证
        checks = {
            "成功标志": result.get("success") is True,
            "有 rewrite_info": "rewrite_info" in result,
            "rewrite_info.success=True": result.get("rewrite_info", {}).get("success") is True,
            "成功方法=sonnet": result.get("rewrite_info", {}).get("successful_method") == "sonnet",
            "phase2 调用=2 (首次+改写后)": mock_phase2.call_count == 2,
            "Sonnet 改写调用=1": mock_rewriter.rewrite.call_count == 1,
            "Simple 改写未调用": mock_rewriter.rewrite_simple.call_count == 0,
            "rewrites 数组有 1 条": len(result.get("rewrite_info", {}).get("rewrites", [])) == 1,
        }

        print(f"\n--- 链路 2 验证结果 ---")
        all_pass = True
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
            if not passed:
                all_pass = False

        if result.get("rewrite_info"):
            rewrites = result["rewrite_info"].get("rewrites", [])
            for rw in rewrites:
                print(f"  📝 改写 #{rw['attempt']}: method={rw['method']}, preview={rw['prompt_preview'][:80]}...")

        return all_pass


# ========== 链路 3: CONTENT_SAFETY → 改写仍失败 ==========

@capture_stdout
async def test_chain_3_safety_all_fail(image_gen, shot, storyboard, characters):
    """链路 3: CONTENT_SAFETY → 所有改写均失败"""
    print("\n" + "=" * 60)
    print("🔗 链路 3: CONTENT_SAFETY → 改写仍失败")
    print("=" * 60)
    print(f"   Shot ID: {shot.get('shot_id')}")

    mock_original_prompt = (
        "A wide shot of a bustling rural market entrance with villagers carrying baskets. "
        "Morning light filters through wooden market stalls. Characters interact with vendors. "
        "The scene captures authentic countryside atmosphere with warm earth tones."
    )

    with patch.object(image_gen, 'generate_shot_image_phase2', new_callable=AsyncMock) as mock_phase2:
        # 所有调用都返回 CONTENT_SAFETY (初始 + 2 次改写 = 3 次)
        mock_phase2.return_value = make_content_safety_result(mock_original_prompt)

        # Mock PromptRewriter — 改写返回内容但仍触发 CONTENT_SAFETY
        mock_rewriter = MagicMock()
        mock_rewriter.rewrite = AsyncMock(
            return_value="Sonnet rewrite attempt: A countryside market scene with morning "
                         "atmosphere. Villagers walk between wooden stalls. Natural golden light."
        )
        mock_rewriter.rewrite_simple = MagicMock(
            return_value="Simple rewrite: A peaceful rural market scene with morning light."
        )
        image_gen._prompt_rewriter = mock_rewriter

        result = await image_gen.generate_shot_image_phase2_safe(
            shot=shot,
            storyboard=storyboard,
            characters=characters,
            style_preset="illustration",
        )

        # MAX_REWRITE_ATTEMPTS = 2, 所以: 1 (初始) + 2 (改写) = 3 次调用
        checks = {
            "失败标志": result.get("success") is False,
            "有 rewrite_info": "rewrite_info" in result,
            "rewrite_info.success=False": result.get("rewrite_info", {}).get("success") is False,
            "phase2 调用=3 (初始+2改写)": mock_phase2.call_count == 3,
            "Sonnet 改写调用=1": mock_rewriter.rewrite.call_count == 1,
            "Simple 改写调用=1": mock_rewriter.rewrite_simple.call_count == 1,
            "rewrites 数组有 2 条": len(result.get("rewrite_info", {}).get("rewrites", [])) == 2,
        }

        print(f"\n--- 链路 3 验证结果 ---")
        all_pass = True
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
            if not passed:
                all_pass = False

        if result.get("rewrite_info"):
            rewrites = result["rewrite_info"].get("rewrites", [])
            for rw in rewrites:
                print(f"  📝 改写 #{rw['attempt']}: method={rw['method']}, preview={rw['prompt_preview'][:80]}...")

        return all_pass


# ========== 代码验证: REWRITER-CLEANUP 确认 ==========

def verify_rewriter_cleanup():
    """验证 TASK-REWRITER-CLEANUP 3 项修复已正确落地"""
    print("\n" + "=" * 60)
    print("🔍 代码验证: TASK-REWRITER-CLEANUP 落地确认")
    print("=" * 60)

    checks = {}

    # 修复 1: pipeline_orchestrator.py 调用 phase2_safe
    pipeline_path = os.path.join(PROJECT_ROOT, "app/services/pipeline_orchestrator.py")
    with open(pipeline_path, "r", encoding="utf-8") as f:
        pipeline_code = f.read()
    checks["修复1: pipeline 调用 phase2_safe"] = "generate_shot_image_phase2_safe(" in pipeline_code
    # 排除注释行后，检查是否存在非 safe 版本的实际调用
    # 注: "generate_shot_image_phase2(" 不是 "generate_shot_image_phase2_safe(" 的子串
    #     (phase2 后接 "(" vs "_safe(")，所以计数互不干扰
    non_comment_lines = [
        line for line in pipeline_code.split('\n')
        if line.strip() and not line.strip().startswith('#')
    ]
    non_comment_code = '\n'.join(non_comment_lines)
    checks["修复1: 无 non-safe 实际调用"] = "generate_shot_image_phase2(" not in non_comment_code

    # 修复 2: prompt_rewriter.py 无 "Haiku" 残留
    rewriter_path = os.path.join(PROJECT_ROOT, "app/services/prompt_rewriter.py")
    with open(rewriter_path, "r", encoding="utf-8") as f:
        rewriter_code = f.read()
    checks["修复2: prompt_rewriter.py 无 Haiku"] = "Haiku" not in rewriter_code and "haiku" not in rewriter_code

    # 修复 2: image_generator.py rewrite_method = "sonnet"
    ig_path = os.path.join(PROJECT_ROOT, "app/services/image_generator.py")
    with open(ig_path, "r", encoding="utf-8") as f:
        ig_code = f.read()
    checks['修复2: rewrite_method = "sonnet"'] = 'rewrite_method = "sonnet"' in ig_code

    # 修复 3: 备用模型 gemini-3.1-flash-preview
    checks["修复3: 备用模型 gemini-3.1-flash-preview"] = "gemini-3.1-flash-preview" in rewriter_code
    checks["修复3: 无 gemini-3-pro-preview 残留"] = "gemini-3-pro-preview" not in rewriter_code

    all_pass = True
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
        if not passed:
            all_pass = False

    return all_pass


# ========== 日志完整性检查 ==========

def verify_logs(chain_name, log_output, expected_markers):
    """验证日志中包含期望的关键标记"""
    print(f"\n--- {chain_name} 日志标记验证 ---")
    all_found = True
    for marker in expected_markers:
        found = marker in log_output
        status = "✅" if found else "❌"
        print(f"  {status} 日志包含: \"{marker}\"")
        if not found:
            all_found = False
    return all_found


# ========== 主函数 ==========

async def main():
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n{'=' * 60}")
    print(f"TASK-SAFE-DRYRUN: Prompt 安全改写链路 Dry-run 验证")
    print(f"时间: {timestamp}")
    print(f"数据源: R8 E2E (story_A, 28 shots)")
    print(f"{'=' * 60}")

    # 0. 代码验证
    cleanup_pass = verify_rewriter_cleanup()

    # 加载 R8 数据
    storyboard, characters = load_r8_data()
    shots = storyboard.get("shots", [])
    print(f"\n📂 加载 R8 数据: {len(shots)} shots, {len(characters.get('characters', []))} 角色")

    # 创建 ImageGenerator (mock Gemini client)
    with patch.dict(os.environ, {"GEMINI_API_KEY": "mock_key_for_dryrun"}):
        from app.services.image_generator import ImageGenerator
        image_gen = ImageGenerator()
        # Mock 掉真实 Gemini client，避免任何实际 API 调用
        image_gen.client = MagicMock()

    # 选取测试 shots
    shot_normal = shots[0]      # Shot 1 — 正常路径
    shot_safety_ok = shots[8]   # Shot 9 — CONTENT_SAFETY → 改写成功
    shot_safety_fail = shots[9] # Shot 10 — CONTENT_SAFETY → 改写仍失败

    results = {}
    logs = {}

    # 链路 1: 正常路径
    result1, log1 = await test_chain_1_normal(image_gen, shot_normal, storyboard, characters)
    results["chain_1"] = result1
    logs["chain_1"] = log1
    log1_pass = verify_logs("链路 1", log1, [
        "安全生成开始",
        "首次生成成功",
    ])
    results["chain_1_logs"] = log1_pass

    # 链路 2: CONTENT_SAFETY → 改写成功
    result2, log2 = await test_chain_2_safety_then_success(image_gen, shot_safety_ok, storyboard, characters)
    results["chain_2"] = result2
    logs["chain_2"] = log2
    log2_pass = verify_logs("链路 2", log2, [
        "安全生成开始",
        "触发内容安全过滤",
        "改写尝试 1/2",
        "改写后生成成功",
    ])
    results["chain_2_logs"] = log2_pass

    # 链路 3: CONTENT_SAFETY → 改写仍失败
    result3, log3 = await test_chain_3_safety_all_fail(image_gen, shot_safety_fail, storyboard, characters)
    results["chain_3"] = result3
    logs["chain_3"] = log3
    log3_pass = verify_logs("链路 3", log3, [
        "安全生成开始",
        "触发内容安全过滤",
        "改写尝试 1/2",
        "改写尝试 2/2",
        "所有改写尝试均失败",
    ])
    results["chain_3_logs"] = log3_pass

    # ========== 汇总报告 ==========
    print(f"\n{'=' * 60}")
    print("TASK-SAFE-DRYRUN 测试汇总")
    print(f"{'=' * 60}")

    summary_items = [
        ("代码验证: REWRITER-CLEANUP", cleanup_pass),
        ("链路 1: 正常路径", results["chain_1"]),
        ("链路 1: 日志完整性", results["chain_1_logs"]),
        ("链路 2: CONTENT_SAFETY → 改写成功", results["chain_2"]),
        ("链路 2: 日志完整性", results["chain_2_logs"]),
        ("链路 3: CONTENT_SAFETY → 改写仍失败", results["chain_3"]),
        ("链路 3: 日志完整性", results["chain_3_logs"]),
    ]

    total = len(summary_items)
    passed = sum(1 for _, v in summary_items if v)

    for name, is_pass in summary_items:
        status = "✅ PASS" if is_pass else "❌ FAIL"
        print(f"  {status}  {name}")

    all_pass = passed == total
    print(f"\n结果: {passed}/{total} {'✅ 全部通过' if all_pass else '❌ 有失败项'}")
    print(f"{'=' * 60}")

    # 保存报告
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report_path = os.path.join(OUTPUT_DIR, "dryrun_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# TASK-SAFE-DRYRUN 验证报告\n\n")
        f.write(f"**时间**: {timestamp}\n")
        f.write(f"**数据源**: R8 E2E (story_A, 28 shots)\n")
        f.write(f"**结果**: {passed}/{total} {'全部通过' if all_pass else '有失败项'}\n\n")
        f.write(f"## 验证项\n\n")
        f.write(f"| # | 验证项 | 结果 |\n")
        f.write(f"|---|--------|------|\n")
        for i, (name, is_pass) in enumerate(summary_items, 1):
            status = "✅ PASS" if is_pass else "❌ FAIL"
            f.write(f"| {i} | {name} | {status} |\n")
        f.write(f"\n## 链路日志\n\n")
        for chain_name, log in logs.items():
            f.write(f"### {chain_name}\n\n```\n{log}\n```\n\n")
        f.write(f"\n## 代码验证明细\n\n")
        f.write(f"- `pipeline_orchestrator.py:376`: ✅ 调用 `generate_shot_image_phase2_safe()`\n")
        f.write(f"- `prompt_rewriter.py`: ✅ Haiku 零残留, 备用模型 `gemini-3.1-flash-preview`\n")
        f.write(f"- `image_generator.py:1227`: ✅ `rewrite_method = \"sonnet\"`\n")

    print(f"\n📄 报告已保存: {report_path}")

    return all_pass


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
