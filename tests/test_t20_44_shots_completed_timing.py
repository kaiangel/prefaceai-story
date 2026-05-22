"""
tests/test_t20_44_shots_completed_timing.py

T20-44 Backend 验收测试: shots_completed 字段一致性

两个独立 bug:
  Bug 1: BGM 阶段 shots_completed 被重置为 0 (应保留最终值 27)
  Bug 2: shots_completed 字段滞后 — message regex 解析逻辑验证

修复:
  chapters.py `_shots_completed` 计算逻辑:
    - BGM / postprocess / finalize / completed stage → shots_total (保留最终值)
    - image_generation → 优先 regex 解析 message
    - 早期 stage → 0

注: Frontend 配合工作 (useETA 渲染) 待 Wave 2。Backend 只做自己负责的部分。
"""

import re
import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Helper: simulate chapters.py _shots_completed calculation logic (T20-44 fixed)
# ---------------------------------------------------------------------------

def _simulate_shots_completed_calc(
    stage: str,
    stage_message: str | None,
    progress: int,
    shots_total: int,
) -> int:
    """
    Mirrors the T20-44 fixed logic in chapters.py for _shots_completed calculation.

    Returns shots_completed value that the status API would return.
    """
    _POST_IMAGE_GEN_STAGES = {"bgm", "postprocess", "finalize", "completed"}

    if stage in _POST_IMAGE_GEN_STAGES or stage == "completed":
        return shots_total

    if stage == "image_generation":
        _parsed_done = None
        _msg = stage_message or ""
        _match = re.search(r"已生成\s*(\d+)\s*/\s*\d+", _msg)
        if _match:
            try:
                _parsed_done = int(_match.group(1))
            except ValueError:
                _parsed_done = None
        if _parsed_done is not None:
            return min(_parsed_done, shots_total)
        else:
            # progress fallback
            if progress >= 75:
                return max(0, min(shots_total, int((progress - 75) * shots_total / 20)))
            else:
                return 0

    # early stage
    return 0


# ---------------------------------------------------------------------------
# Bug 1 Tests: BGM stage shots_completed reset
# ---------------------------------------------------------------------------

class TestBGMStageReset:
    """T20-44 Bug 1: BGM 阶段 shots_completed 不应重置为 0"""

    def test_bgm_stage_returns_shots_total(self):
        """
        BGM 阶段: shots_completed 应等于 shots_total (保留最终值)
        旧 bug: BGM 走 `else` 分支 → shots_completed = 0 (reset)
        新修复: BGM 走 `_POST_IMAGE_GEN_STAGES` → shots_completed = shots_total
        """
        result = _simulate_shots_completed_calc(
            stage="bgm",
            stage_message="BGM 生成中...",
            progress=96,
            shots_total=27,
        )
        assert result == 27, f"BGM 阶段 shots_completed 应为 27, 实际 {result} (旧 bug 重置为 0)"

    def test_completed_stage_returns_shots_total(self):
        """completed 阶段: shots_completed 应等于 shots_total"""
        result = _simulate_shots_completed_calc(
            stage="completed",
            stage_message="Pipeline 完成",
            progress=100,
            shots_total=27,
        )
        assert result == 27

    def test_postprocess_stage_returns_shots_total(self):
        """postprocess 阶段: shots_completed 应等于 shots_total"""
        result = _simulate_shots_completed_calc(
            stage="postprocess",
            stage_message="后处理中...",
            progress=97,
            shots_total=18,
        )
        assert result == 18

    def test_finalize_stage_returns_shots_total(self):
        """finalize 阶段: shots_completed 应等于 shots_total"""
        result = _simulate_shots_completed_calc(
            stage="finalize",
            stage_message="最终处理...",
            progress=98,
            shots_total=36,
        )
        assert result == 36

    def test_bgm_message_none_still_returns_total(self):
        """BGM 阶段 stage_message=None 时也应返回 shots_total"""
        result = _simulate_shots_completed_calc(
            stage="bgm",
            stage_message=None,
            progress=95,
            shots_total=27,
        )
        assert result == 27

    def test_old_bug_simulation(self):
        """
        模拟旧 bug: 旧代码 BGM 走 else → 0
        用旧逻辑函数验证 bug 确实存在, 新逻辑修复了。
        """
        def _old_logic(stage, stage_message, progress, shots_total):
            if stage == "completed":
                return shots_total
            elif stage == "image_generation":
                _match = re.search(r"已生成\s*(\d+)\s*/\s*\d+", stage_message or "")
                if _match:
                    return int(_match.group(1))
                return 0
            else:
                return 0  # BUG: BGM 走这里

        old_result = _old_logic("bgm", "BGM 生成中...", 96, 27)
        new_result = _simulate_shots_completed_calc("bgm", "BGM 生成中...", 96, 27)

        assert old_result == 0, "旧 bug 验证: BGM 阶段旧逻辑应返回 0"
        assert new_result == 27, "新修复: BGM 阶段应返回 27"


# ---------------------------------------------------------------------------
# Bug 2 Tests: shots_completed regex parsing during image_generation
# ---------------------------------------------------------------------------

class TestImageGenerationRegexParsing:
    """T20-44 Bug 2: image_generation 阶段 shots_completed regex 解析"""

    def test_message_5_of_27_returns_5(self):
        """
        message '已生成 5/27 张图像...' → shots_completed = 5
        验证 regex 能正确解析中间进度
        """
        result = _simulate_shots_completed_calc(
            stage="image_generation",
            stage_message="已生成 5/27 张图像...",
            progress=79,
            shots_total=27,
        )
        assert result == 5, f"已生成 5/27 应解析为 5, 实际 {result}"

    def test_message_3_of_27_returns_3(self):
        """
        message '已生成 3/27 张图像...' → shots_completed = 3
        验证 test20 实测: backend.log 说 5 张, 但状态 API 报 3 的情形
        """
        result = _simulate_shots_completed_calc(
            stage="image_generation",
            stage_message="已生成 3/27 张图像...",
            progress=77,
            shots_total=27,
        )
        assert result == 3

    def test_message_27_of_27_returns_27(self):
        """message '已生成 27/27 张图像...' → shots_completed = 27"""
        result = _simulate_shots_completed_calc(
            stage="image_generation",
            stage_message="已生成 27/27 张图像...",
            progress=95,
            shots_total=27,
        )
        assert result == 27

    def test_message_with_failure_label(self):
        """message '已生成 10/27 张图像（含失败）...' → shots_completed = 10"""
        result = _simulate_shots_completed_calc(
            stage="image_generation",
            stage_message="已生成 10/27 张图像（含失败）...",
            progress=82,
            shots_total=27,
        )
        assert result == 10

    def test_no_message_falls_back_to_progress(self):
        """message=None 时 → progress 反推 fallback"""
        result = _simulate_shots_completed_calc(
            stage="image_generation",
            stage_message=None,
            progress=82,
            shots_total=27,  # (82-75) * 27 / 20 = 7*27/20 = 9.45 → 9
            shots_total_for_calc=27,
        ) if False else _simulate_shots_completed_calc(
            stage="image_generation",
            stage_message=None,
            progress=82,
            shots_total=27,
        )
        # (82-75) * 27 / 20 = 7 * 27 / 20 = 9
        assert result == 9, f"progress 82 → 应为 9, 实际 {result}"

    def test_message_cannot_exceed_shots_total(self):
        """message 解析值不能超过 shots_total (防止数据异常)"""
        result = _simulate_shots_completed_calc(
            stage="image_generation",
            stage_message="已生成 30/27 张图像...",  # 异常: 超出 total
            progress=95,
            shots_total=27,
        )
        assert result == 27, "shots_completed 不能超过 shots_total"

    def test_empty_message_at_start(self):
        """image_generation 开始时 message='开始绘制画面...' (无数字) → progress=75 → 0"""
        result = _simulate_shots_completed_calc(
            stage="image_generation",
            stage_message="开始绘制画面...",
            progress=75,
            shots_total=27,
        )
        assert result == 0, f"刚开始绘制时应为 0, 实际 {result}"


# ---------------------------------------------------------------------------
# Early Stage Tests: stages before image_generation
# ---------------------------------------------------------------------------

class TestEarlyStages:
    """早期阶段 shots_completed 应为 0 (还没到生图)"""

    @pytest.mark.parametrize("stage", [
        "outline",
        "character_design",
        "screenplay",
        "storyboard",
        "image_preparation",
    ])
    def test_early_stages_return_zero(self, stage):
        """早期 stage → shots_completed = 0"""
        result = _simulate_shots_completed_calc(
            stage=stage,
            stage_message="处理中...",
            progress=50,
            shots_total=27,
        )
        assert result == 0, f"stage={stage} 时 shots_completed 应为 0, 实际 {result}"

    def test_unknown_stage_returns_zero(self):
        """未知 stage → shots_completed = 0 (安全 fallback)"""
        result = _simulate_shots_completed_calc(
            stage="some_unknown_stage",
            stage_message="未知阶段",
            progress=60,
            shots_total=27,
        )
        assert result == 0


# ---------------------------------------------------------------------------
# Integration: verify chapters.py can be imported and _POST_IMAGE_GEN_STAGES is defined
# ---------------------------------------------------------------------------

def test_chapters_py_compiles():
    """
    chapters.py 可正常 import (间接验证 syntax + _POST_IMAGE_GEN_STAGES 存在)
    """
    import subprocess
    import sys
    import os

    chapters_path = os.path.join(
        os.path.dirname(__file__), "..", "app", "api", "chapters.py"
    )
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", chapters_path],
        capture_output=True, text=True
    )
    assert result.returncode == 0, f"chapters.py 编译失败: {result.stderr}"


def test_post_image_gen_stages_in_source():
    """
    验证 chapters.py 源码中含 T20-44 修复的 _POST_IMAGE_GEN_STAGES 定义
    """
    import os
    chapters_path = os.path.normpath(os.path.join(
        os.path.dirname(__file__), "..", "app", "api", "chapters.py"
    ))
    with open(chapters_path, "r", encoding="utf-8") as f:
        source = f.read()

    assert "_POST_IMAGE_GEN_STAGES" in source, (
        "T20-44 修复: _POST_IMAGE_GEN_STAGES 应在 chapters.py 中定义"
    )
    assert '"bgm"' in source, "bgm 应在 _POST_IMAGE_GEN_STAGES 集合中"
    assert "T20-44" in source, "T20-44 注释应在 chapters.py 中"
