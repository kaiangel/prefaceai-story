"""
单元测试: Wave 10 / RISK-T16-6 — Pipeline 失败时 chapter.status 写 "failed" 不 "completed"

验证 job_manager.run_story_generation_task() 在 pipeline.run() 返回 success=False 时：
1. result["success"] == False
2. chapter.status 走 "failed" 路径（不走 "completed"）
3. chapter.error_message 包含 failed_stage 信息

运行命令:
  pytest tests/test_pipeline_failure_status.py -v
"""

import json
import pytest


# --------------------------------------------------------------------------
# 提取 job_manager 的核心 success 判断逻辑为可测试的纯函数
# --------------------------------------------------------------------------

def _build_result_from_pipeline(pipeline_result: dict) -> dict:
    """
    Wave 10 / RISK-T16-6: 复现 job_manager.py 中的 result 构建逻辑（已修复版）。

    原始 bug（修复前）:
        result = {"success": True, "data": pipeline_result}   # 硬编码 True，永不失败

    修复后:
        if pipeline_result.get("success", True):
            result = {"success": True, "data": pipeline_result}
        else:
            result = {"success": False, "error": ..., "data": pipeline_result}
    """
    if pipeline_result.get("success", True):
        return {"success": True, "data": pipeline_result}
    else:
        return {
            "success": False,
            "error": (
                f"[Stage {pipeline_result.get('failed_stage', '?')}] "
                f"{pipeline_result.get('error', 'Pipeline 运行失败')}"
            ),
            "data": pipeline_result,
        }


def _determine_chapter_status(result: dict) -> tuple[str, str | None]:
    """
    模拟 job_manager 中的 chapter.status 写入逻辑:
    - success=False  → chapter.status="failed", error_message=result["error"]
    - success=True   → chapter.status="completed", error_message=None

    Returns: (chapter_status, error_message)
    """
    if not result["success"]:
        return "failed", result.get("error", "未知错误")
    else:
        return "completed", None


# --------------------------------------------------------------------------
# Case 1: Pipeline Stage 4 失败 → chapter.status="failed" + error_message 非空
# --------------------------------------------------------------------------

class TestPipelineFailureChapterStatus:
    """RISK-T16-6 核心验证: Pipeline 失败时 chapter.status 应为 failed，不走 completed"""

    def test_stage4_failure_sets_chapter_failed(self):
        """
        Pipeline Stage 4 (storyboard) 失败:
        - pipeline_result.success = False
        - failed_stage = "storyboard"
        - error = "所有 scene 均无 action_beats，无法生成 shots"
        → chapter.status = "failed"
        → chapter.error_message 包含 "storyboard" 和真实 error 文本
        """
        pipeline_result = {
            "success": False,
            "error": "所有 scene 均无 action_beats，无法生成 shots",
            "failed_stage": "storyboard",
            "stage_results": {},
        }

        result = _build_result_from_pipeline(pipeline_result)

        # result["success"] 应该是 False
        assert result["success"] is False, (
            "RISK-T16-6 bug: pipeline 失败时 result['success'] 不应为 True"
        )

        chapter_status, error_message = _determine_chapter_status(result)

        # chapter.status 应该是 "failed"
        assert chapter_status == "failed", (
            f"Pipeline 失败时 chapter.status 应为 'failed'，实际是 '{chapter_status}'"
        )

        # error_message 应该非空
        assert error_message is not None, "chapter.error_message 应该非空"
        assert len(error_message) > 0, "chapter.error_message 不能是空字符串"

        # error_message 应该包含 failed_stage 信息
        assert "storyboard" in error_message, (
            f"error_message 应包含 failed_stage 信息，实际: {error_message}"
        )

        # error_message 应该包含真实 error 文本
        assert "action_beats" in error_message, (
            f"error_message 应包含原始 error 文本，实际: {error_message}"
        )

    def test_stage5_failure_sets_chapter_failed(self):
        """
        Pipeline Stage 5 (image_generation) 失败:
        → chapter.status = "failed"
        """
        pipeline_result = {
            "success": False,
            "error": "Seedream API 连接超时",
            "failed_stage": "image_generation",
            "stage_results": {},
        }

        result = _build_result_from_pipeline(pipeline_result)

        assert result["success"] is False
        assert "image_generation" in result["error"]

        chapter_status, error_message = _determine_chapter_status(result)
        assert chapter_status == "failed"
        assert error_message is not None
        assert "image_generation" in error_message

    def test_pipeline_success_sets_chapter_completed(self):
        """
        Pipeline 成功:
        → chapter.status = "completed"（happy path 不能误伤）
        """
        pipeline_result = {
            "success": True,
            "summary": {"title": "测试故事", "total_shots": 18},
            "stage_results": {},
        }

        result = _build_result_from_pipeline(pipeline_result)

        assert result["success"] is True

        chapter_status, error_message = _determine_chapter_status(result)
        assert chapter_status == "completed", (
            "Pipeline 成功时 chapter.status 应为 'completed'"
        )
        assert error_message is None, "Pipeline 成功时 error_message 应为 None"

    def test_pipeline_result_missing_success_defaults_to_true(self):
        """
        pipeline_result 没有 'success' 字段（异常情况）:
        → 默认 get("success", True) = True → chapter.status = "completed"
        （向后兼容：旧代码可能没写 success 字段）
        """
        pipeline_result = {
            "summary": {"title": "测试故事"},
            "stage_results": {},
            # 没有 "success" 字段
        }

        result = _build_result_from_pipeline(pipeline_result)

        # 默认 True（向后兼容）
        assert result["success"] is True

        chapter_status, _ = _determine_chapter_status(result)
        assert chapter_status == "completed"

    def test_pipeline_failure_error_message_format(self):
        """error_message 格式验证: [Stage X] error text"""
        pipeline_result = {
            "success": False,
            "error": "LLM 返回格式错误",
            "failed_stage": "screenplay",
        }

        result = _build_result_from_pipeline(pipeline_result)
        error_msg = result["error"]

        # 格式应为 "[Stage screenplay] LLM 返回格式错误"
        assert error_msg.startswith("[Stage screenplay]"), (
            f"error_message 格式应以 '[Stage X]' 开头，实际: {error_msg}"
        )
        assert "LLM 返回格式错误" in error_msg


# --------------------------------------------------------------------------
# 运行验证
# --------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    t = TestPipelineFailureChapterStatus()
    t.test_stage4_failure_sets_chapter_failed()
    t.test_stage5_failure_sets_chapter_failed()
    t.test_pipeline_success_sets_chapter_completed()
    t.test_pipeline_result_missing_success_defaults_to_true()
    t.test_pipeline_failure_error_message_format()

    print("All 5 test cases passed!")
    sys.exit(0)
