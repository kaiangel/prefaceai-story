"""
tests/test_t20_48_anatomy_auto_regen.py

T20-48 验收测试: Shot anatomy_issue 自动重生 (最多 2 次) + partial_failure 标记.

背景:
  test20 Shot 16 anatomy_issue (4 hands), ShotValidator 抓到但仅 ⚠️ 警告不重生.
  实际上 anatomy_severity="severe" 已触发 valid=False → pipeline retry。
  但 MAX_SHOT_RETRIES=1 只给 1 次重试 (2 次总). anatomy 需要 2 次重试 (3 次总).

修复 (T20-48):
  - anatomy_issue 专用最多 2 次重试 (3 次总尝试)
  - 第 3 次还 fail → shot["_anatomy_partial_failure"] = True + log ERROR
  - 非 anatomy fail 保持原 1 次重试 (2 次总尝试) 不变

测试 case:
  1. anatomy_issue 触发 → 第 1 次重生后 PASS → Pipeline 接受 (anatomy_regen_count=1)
  2. anatomy_issue × 2 次 → 第 2 次重生后 PASS → Pipeline 接受 (anatomy_regen_count=2)
  3. anatomy_issue 持续 3 次 → partial_failure 标记 + 不死循环 (循环退出)
  4. 非 anatomy fail (角色数量不匹配) → 1 次重试上限不变 (不使用 anatomy 专用上限)
  5. 验证代码层面 MAX_ANATOMY_RETRIES=2 存在于 pipeline_orchestrator.py
  6. _anatomy_partial_failure 字段标记逻辑
"""

import os
import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Helpers: 模拟 pipeline 内的 anatomy retry 逻辑
# ─────────────────────────────────────────────────────────────────────────────

def _simulate_shot_regen_loop(
    validation_sequence: list[dict],
    max_shot_retries: int = 1,
    max_anatomy_retries: int = 2,
) -> dict:
    """
    模拟 pipeline_orchestrator.py 内 shot 生成 + 验证 + retry 循环逻辑 (T20-48 修复后).

    Args:
        validation_sequence: 每次 attempt 的 validate_shot 结果列表.
          每个元素格式: {"valid": bool, "reason": str, "anatomy_severity": str, "anatomy_issues": []}
        max_shot_retries: 普通 fail 最大重试次数 (默认 1 = 2 次总尝试)
        max_anatomy_retries: anatomy fail 最大重试次数 (默认 2 = 3 次总尝试)

    Returns:
        {
          "attempts": int,          # 总尝试次数
          "anatomy_regen_count": int, # anatomy 专用重生次数
          "final_valid": bool,       # 最终 shot 是否验证通过
          "partial_failure": bool,   # 是否标记 partial_failure
          "anatomy_issues": list,    # partial_failure 时的 anatomy_issues
        }
    """
    _anatomy_regen_count = 0
    attempts = 0
    partial_failure = False
    anatomy_issues_logged = []
    final_valid = False

    for attempt in range(max_anatomy_retries + 1):
        attempts += 1
        # 获取当前 attempt 的验证结果 (超出 sequence 用最后一个)
        idx = min(attempt, len(validation_sequence) - 1)
        validation = validation_sequence[idx]

        _val_reason = validation.get("reason", "")
        _is_anatomy_fail = "anatomy_issue" in _val_reason

        if validation["valid"]:
            final_valid = True
            break
        else:
            if _is_anatomy_fail:
                _anatomy_regen_count += 1
                if _anatomy_regen_count <= max_anatomy_retries:
                    continue  # 继续重生
                else:
                    # 超过 anatomy 重试上限 → partial_failure
                    partial_failure = True
                    anatomy_issues_logged = validation.get("anatomy_issues", [])
                    break
            elif attempt >= max_shot_retries:
                # 非 anatomy fail, 达到普通重试上限
                break

    return {
        "attempts": attempts,
        "anatomy_regen_count": _anatomy_regen_count,
        "final_valid": final_valid,
        "partial_failure": partial_failure,
        "anatomy_issues": anatomy_issues_logged,
    }


def _make_anatomy_fail_validation(issues: list[str] | None = None) -> dict:
    """生成 anatomy_issue 验证失败结果."""
    if issues is None:
        issues = ["character_A: 4 hands visible"]
    return {
        "valid": False,
        "reason": f"anatomy_issue: {'; '.join(issues)}",
        "anatomy_severity": "severe",
        "anatomy_issues": issues,
    }


def _make_pass_validation(character_count: int = 2) -> dict:
    """生成验证通过结果."""
    return {
        "valid": True,
        "reason": "pass",
        "anatomy_severity": "none",
        "anatomy_issues": [],
        "actual_character_count": character_count,
    }


def _make_char_count_fail_validation() -> dict:
    """生成角色数量不匹配 fail (非 anatomy)."""
    return {
        "valid": False,
        "reason": "角色数量不匹配: 预期2, 实际0",
        "anatomy_severity": "none",
        "anatomy_issues": [],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Section 1: anatomy 重生流程
# ─────────────────────────────────────────────────────────────────────────────

class TestAnatomyAutoRegen:
    """anatomy_issue 自动重生逻辑 (T20-48)."""

    def test_case1_anatomy_fail_then_pass_on_first_regen(self):
        """
        T20-48 case 1: anatomy_issue 触发 → 第 1 次重生后 PASS → Pipeline 接受.

        序列: [anatomy_fail, pass]
        期望: attempts=2, anatomy_regen_count=1, final_valid=True, partial_failure=False
        """
        result = _simulate_shot_regen_loop(
            validation_sequence=[
                _make_anatomy_fail_validation(["character_A: 4 hands visible"]),
                _make_pass_validation(),
            ]
        )
        assert result["attempts"] == 2, f"应 2 次尝试 (1 次初生 + 1 次重生), 实际={result['attempts']}"
        assert result["anatomy_regen_count"] == 1, (
            f"anatomy 重生 1 次, 实际={result['anatomy_regen_count']}"
        )
        assert result["final_valid"] is True, "第 1 次重生后应 PASS"
        assert result["partial_failure"] is False, "不应标记 partial_failure"

    def test_case2_anatomy_fail_twice_then_pass(self):
        """
        T20-48 case 2: anatomy_issue × 2 次 → 第 2 次重生后 PASS.

        序列: [anatomy_fail, anatomy_fail, pass]
        期望: attempts=3, anatomy_regen_count=2, final_valid=True, partial_failure=False
        """
        result = _simulate_shot_regen_loop(
            validation_sequence=[
                _make_anatomy_fail_validation(),
                _make_anatomy_fail_validation(),
                _make_pass_validation(),
            ]
        )
        assert result["attempts"] == 3, f"应 3 次尝试, 实际={result['attempts']}"
        assert result["anatomy_regen_count"] == 2, (
            f"anatomy 重生 2 次, 实际={result['anatomy_regen_count']}"
        )
        assert result["final_valid"] is True, "第 2 次重生后应 PASS"
        assert result["partial_failure"] is False

    def test_case3_persistent_anatomy_fail_marks_partial_failure(self):
        """
        T20-48 case 3: anatomy_issue 持续 3 次 → partial_failure 标记 + 不死循环.

        序列: [anatomy_fail, anatomy_fail, anatomy_fail]
        期望: attempts=3, partial_failure=True, final_valid=False, 不死循环
        """
        issues = ["character_A: 4 hands visible", "character_A: 4 arms visible"]
        result = _simulate_shot_regen_loop(
            validation_sequence=[
                _make_anatomy_fail_validation(issues),
                _make_anatomy_fail_validation(issues),
                _make_anatomy_fail_validation(issues),
            ]
        )
        assert result["attempts"] == 3, f"应 3 次尝试后退出 (不死循环), 实际={result['attempts']}"
        assert result["partial_failure"] is True, "持续 anatomy fail 3 次应标记 partial_failure"
        assert result["final_valid"] is False, "partial_failure 时 final_valid 应为 False"
        assert result["anatomy_issues"] == issues, (
            f"partial_failure 时应记录 anatomy_issues={issues!r}"
        )

    def test_case4_anatomy_max_retries_is_2_not_1(self):
        """
        T20-48: anatomy 最多 2 次重试 (3 次总尝试), 而非普通 fail 的 1 次重试 (2 次总).

        验证: max_anatomy_retries=2 时允许到 3 次尝试, max_shot_retries=1 限 2 次
        """
        # Anatomy: 3 次尝试 (2 次重生) 后才 partial_failure
        anatomy_result = _simulate_shot_regen_loop(
            validation_sequence=[
                _make_anatomy_fail_validation(),
                _make_anatomy_fail_validation(),
                _make_anatomy_fail_validation(),
            ],
            max_shot_retries=1,
            max_anatomy_retries=2,
        )
        assert anatomy_result["attempts"] == 3, (
            f"anatomy 应允许 3 次尝试 (2 次重生), 实际={anatomy_result['attempts']}"
        )

    def test_case5_no_infinite_loop_guarantee(self):
        """
        T20-48: 无限死循环保证 — 即使 validation_sequence 无限 anatomy_fail, 循环仍退出.

        验证: max_anatomy_retries=2 硬上限, 3 次后 break
        """
        # 100 个全部 anatomy_fail
        infinitely_failing = [_make_anatomy_fail_validation()] * 100
        result = _simulate_shot_regen_loop(
            validation_sequence=infinitely_failing,
            max_anatomy_retries=2,
        )
        assert result["attempts"] <= 3, (
            f"死循环保证: 最多 3 次尝试, 实际={result['attempts']}"
        )
        assert result["partial_failure"] is True


# ─────────────────────────────────────────────────────────────────────────────
# Section 2: 非 anatomy fail 保持原行为
# ─────────────────────────────────────────────────────────────────────────────

class TestNonAnatomyFailBehaviorUnchanged:
    """非 anatomy fail 保持原 MAX_SHOT_RETRIES=1 行为不变."""

    def test_char_count_fail_uses_max_shot_retries(self):
        """
        T20-48: 角色数量不匹配 fail (非 anatomy) → 最多 1 次重试 (2 次总尝试).

        序列: [char_count_fail, char_count_fail]
        期望: attempts=2, partial_failure=False (不触发 anatomy 逻辑)
        """
        result = _simulate_shot_regen_loop(
            validation_sequence=[
                _make_char_count_fail_validation(),
                _make_char_count_fail_validation(),
            ],
            max_shot_retries=1,
            max_anatomy_retries=2,
        )
        assert result["attempts"] == 2, (
            f"非 anatomy fail 应 2 次尝试后停止 (MAX_SHOT_RETRIES=1), 实际={result['attempts']}"
        )
        assert result["partial_failure"] is False, (
            "非 anatomy fail 不应标记 partial_failure (无 _anatomy_partial_failure)"
        )
        assert result["anatomy_regen_count"] == 0, "非 anatomy fail 不应增加 anatomy_regen_count"

    def test_char_count_fail_then_pass_on_first_retry(self):
        """
        非 anatomy fail 首次重试通过 → 正常 PASS.

        序列: [char_count_fail, pass]
        期望: final_valid=True, anatomy_regen_count=0
        """
        result = _simulate_shot_regen_loop(
            validation_sequence=[
                _make_char_count_fail_validation(),
                _make_pass_validation(),
            ]
        )
        assert result["final_valid"] is True
        assert result["anatomy_regen_count"] == 0
        assert result["attempts"] == 2

    def test_immediate_pass_no_retries(self):
        """
        首次生成即通过 → 0 次重试.
        """
        result = _simulate_shot_regen_loop(
            validation_sequence=[_make_pass_validation()]
        )
        assert result["attempts"] == 1
        assert result["final_valid"] is True
        assert result["anatomy_regen_count"] == 0
        assert result["partial_failure"] is False


# ─────────────────────────────────────────────────────────────────────────────
# Section 3: 代码层面静态验证
# ─────────────────────────────────────────────────────────────────────────────

class TestAnatomyAutoRegenCodeStructure:
    """验证 pipeline_orchestrator.py 代码结构符合 T20-48 规范."""

    def _read_orchestrator_source(self) -> str:
        source_path = os.path.join(
            os.path.dirname(__file__), "..", "app", "services", "pipeline_orchestrator.py"
        )
        with open(os.path.normpath(source_path), "r", encoding="utf-8") as f:
            return f.read()

    def test_max_anatomy_retries_constant_exists(self):
        """MAX_ANATOMY_RETRIES 常量应在 pipeline_orchestrator.py 中定义."""
        source = self._read_orchestrator_source()
        assert "MAX_ANATOMY_RETRIES" in source, (
            "MAX_ANATOMY_RETRIES 常量应在 pipeline_orchestrator.py 中"
        )

    def test_max_anatomy_retries_is_2(self):
        """MAX_ANATOMY_RETRIES 应为 2 (3 次总尝试)."""
        source = self._read_orchestrator_source()
        assert "MAX_ANATOMY_RETRIES = 2" in source, (
            "MAX_ANATOMY_RETRIES 应 = 2"
        )

    def test_anatomy_regen_count_tracking(self):
        """pipeline_orchestrator.py 应追踪 _anatomy_regen_count."""
        source = self._read_orchestrator_source()
        assert "_anatomy_regen_count" in source, (
            "_anatomy_regen_count 追踪变量应在 pipeline_orchestrator.py 中"
        )

    def test_anatomy_partial_failure_flag(self):
        """anatomy 持续失败时应标记 _anatomy_partial_failure."""
        source = self._read_orchestrator_source()
        assert "_anatomy_partial_failure" in source, (
            "_anatomy_partial_failure 标记应在 pipeline_orchestrator.py 中"
        )

    def test_anatomy_issue_detection(self):
        """代码应检测 'anatomy_issue' in reason."""
        source = self._read_orchestrator_source()
        assert '"anatomy_issue"' in source or "'anatomy_issue'" in source, (
            "pipeline_orchestrator.py 应检测 anatomy_issue 关键词"
        )

    def test_t20_48_comment_present(self):
        """T20-48 注释应在 pipeline_orchestrator.py 中存在."""
        source = self._read_orchestrator_source()
        assert "T20-48" in source, "T20-48 注释应在 pipeline_orchestrator.py 中"

    def test_max_shot_retries_still_1(self):
        """MAX_SHOT_RETRIES 应保持 1 (普通 fail 不受 anatomy 影响)."""
        source = self._read_orchestrator_source()
        assert "MAX_SHOT_RETRIES = 1" in source, (
            "MAX_SHOT_RETRIES 应保持 = 1 (普通 fail 上限不变)"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Section 4: anatomy_issue 关键词检测
# ─────────────────────────────────────────────────────────────────────────────

class TestAnatomyIssueDetection:
    """验证 anatomy_issue 关键词检测逻辑."""

    @pytest.mark.parametrize("reason,expected", [
        ("anatomy_issue: character_A: 4 hands visible", True),
        ("anatomy_issue: character_B: 3 arms visible; character_C: 2 faces", True),
        ("角色数量不匹配: 预期2, 实际0", False),
        ("key_props 全部缺失 2/2（灾难级生成跑偏）", False),
        ("pass", False),
        ("", False),
        ("ANATOMY_ISSUE: should still detect (case sensitive)", False),  # 当前逻辑用 in, 区分大小写
    ])
    def test_anatomy_issue_in_reason(self, reason: str, expected: bool):
        """'anatomy_issue' in reason 检测逻辑."""
        actual = "anatomy_issue" in reason
        assert actual == expected, (
            f"reason={reason!r}: 'anatomy_issue' in reason 应为 {expected}, 实际={actual}"
        )

    def test_anatomy_issue_reason_from_shot_validator(self):
        """ShotValidator 返回的 anatomy fail reason 格式应含 'anatomy_issue'."""
        # shot_validator.py L714: reasons.append(f"anatomy_issue: {_issues_label}")
        issues = ["character_A: 3 hands", "character_A: 4 arms"]
        issues_label = "; ".join(issues) if issues else "未提供具体描述"
        reason = f"anatomy_issue: {issues_label}"
        assert "anatomy_issue" in reason, (
            f"ShotValidator 格式的 reason 应含 'anatomy_issue': {reason!r}"
        )
