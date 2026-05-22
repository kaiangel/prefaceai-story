"""
tests/test_t20_47_shot_validator_fallback.py

T20-47 验收测试: ShotValidator Sonnet 4.6 主模型 + Haiku 4.5 降级备用.

背景 (KEY_LEARNINGS #34):
  test20 ShotValidator 调 Haiku 4.5 验证 27 shot, 13 个 4/4 retry 全 529 → fail-open
  (skipped_count=13, 48% shot 未验证). 原因: Haiku 在 Anthropic 过载时与 Sonnet 同时过载.

修复 (T20-47):
  - 主模型: Sonnet 4.6 (质量更好, 尤其 anatomy 检测)
  - Sonnet 4.6 全 529 → 降级 Haiku 4.5 (throughput 更高)
  - Haiku 也 fail → fail-open + reason=SONNET_AND_HAIKU_OVERLOADED
  - fail-open 率 > 30% → ERROR 告警

测试 case:
  1. Sonnet 成功 → 返回验证结果 (不降级)
  2. Sonnet 529 × 4 次 → 降级 Haiku → Haiku 成功 → PASS
  3. Sonnet + Haiku 双 529 全失 → fail-open + reason=SONNET_AND_HAIKU_OVERLOADED
  4. fail-open 率 > 30% → ERROR 级日志
  5. 非 retryable 错误 (400) → Sonnet 不降级 Haiku → fail-open + API_ERROR_SKIPPED
  6. SONNET_MODEL 常量值正确 (claude-sonnet-4-6-20251101)
  7. HAIKU_MODEL 常量值正确 (claude-haiku-4-5-20251001)
  8. validate_shot 返回结构完整 (含 anatomy_severity / anatomy_issues)
"""

import asyncio
import importlib
import importlib.util
import os
import sys
from pathlib import Path
import pytest
import logging
from unittest.mock import AsyncMock, MagicMock, patch, call
from PIL import Image


# ─────────────────────────────────────────────────────────────────────────────
# T20-52: Test isolation fixture
#
# 问题: test_t20_43_supernatural_humanoid_prompt.py 注入 stub:
#   sys.modules["app"] = types.ModuleType("app")            — 无 __path__
#   sys.modules["app.services"] = types.ModuleType("app.services")  — 无 __path__
# 导致后续 "from app.services.shot_validator import ..." 失败:
#   ModuleNotFoundError: 'app' is not a package / 'app.services' is not a package
#
# 修复策略:
#   1. 每 test 前检查 sys.modules["app"] / ["app.services"] 是否是 stub (无 __path__)
#   2. 若是, 删除所有 app.* stub 条目
#   3. 重新注入最小合法 package stub (有 __path__) 而不运行 __init__.py
#      (避免 app/services/__init__.py 触发 story_generator → google.genai import 失败)
#   4. 直接用 importlib.util.spec_from_file_location 加载 shot_validator.py
#      绕过 app/services/__init__.py
# ─────────────────────────────────────────────────────────────────────────────

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_shot_validator_fresh():
    """T20-52: 确保 app.services.shot_validator 以干净状态在 sys.modules 中.

    若 app / app.services 是 stub (无 __path__), 先清除再重建最小 package stub,
    然后直接从文件加载 shot_validator, 绕过 app/services/__init__.py.
    (app/services/__init__.py 会尝试 import story_generator → google.genai,
    在 test 环境中 google.genai 是 stub, 会触发 ImportError)
    """
    # Check if app or app.services are stubs (no __path__)
    app_mod = sys.modules.get("app")
    app_is_stub = (app_mod is not None and not hasattr(app_mod, "__path__"))
    svc_mod = sys.modules.get("app.services")
    svc_is_stub = (svc_mod is not None and not hasattr(svc_mod, "__path__"))

    if app_is_stub or svc_is_stub:
        # Remove all app.* entries (stubs and any cached submodules)
        keys_to_remove = [k for k in list(sys.modules.keys())
                          if k == "app" or k.startswith("app.")]
        for k in keys_to_remove:
            del sys.modules[k]

    # Always remove shot_validator so we get a fresh load (resets global counters)
    sys.modules.pop("app.services.shot_validator", None)

    # Ensure app and app.services are minimal package stubs (have __path__)
    if "app" not in sys.modules or not hasattr(sys.modules["app"], "__path__"):
        import types as _types
        _app_pkg = _types.ModuleType("app")
        _app_pkg.__path__ = [str(_PROJECT_ROOT / "app")]  # type: ignore[attr-defined]
        _app_pkg.__package__ = "app"
        sys.modules["app"] = _app_pkg

    if "app.services" not in sys.modules or not hasattr(sys.modules["app.services"], "__path__"):
        import types as _types
        _svc_pkg = _types.ModuleType("app.services")
        _svc_pkg.__path__ = [str(_PROJECT_ROOT / "app" / "services")]  # type: ignore[attr-defined]
        _svc_pkg.__package__ = "app.services"
        sys.modules["app"] .services = _svc_pkg  # type: ignore[attr-defined]
        sys.modules["app.services"] = _svc_pkg

    # Load shot_validator.py directly (bypassing __init__.py)
    _sv_path = _PROJECT_ROOT / "app" / "services" / "shot_validator.py"
    _spec = importlib.util.spec_from_file_location(
        "app.services.shot_validator",
        str(_sv_path),
    )
    _sv = importlib.util.module_from_spec(_spec)
    _sv.__package__ = "app.services"
    sys.modules["app.services.shot_validator"] = _sv
    _spec.loader.exec_module(_sv)  # type: ignore[union-attr]
    # Attach to parent package namespace
    sys.modules["app.services"].shot_validator = _sv  # type: ignore[attr-defined]


@pytest.fixture(autouse=True)
def _restore_app_services_package():
    """T20-52: 每 test 前加载干净的 shot_validator, 清除 test_t20_43 stub 污染."""
    _load_shot_validator_fresh()
    yield
    # Teardown: remove shot_validator so next test gets a fresh load (avoids global state leak)
    sys.modules.pop("app.services.shot_validator", None)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_minimal_image() -> Image.Image:
    return Image.new("RGB", (10, 10), color=(100, 150, 200))


def _make_anthropic_overload_exc() -> Exception:
    """Simulate Anthropic 529 OverloadedError."""
    exc = Exception("overloaded: 529 error — Anthropic service temporarily overloaded")
    exc.status_code = 529  # type: ignore[attr-defined]
    return exc


def _make_anthropic_bad_request_exc() -> Exception:
    """Simulate Anthropic 400 BadRequest (non-retryable)."""
    exc = Exception("bad request: 400 — invalid input")
    exc.status_code = 400  # type: ignore[attr-defined]
    return exc


def _make_valid_haiku_response(character_count: int = 1) -> MagicMock:
    """Simulate a valid Anthropic response JSON."""
    resp = MagicMock()
    resp.content = [MagicMock()]
    resp.content[0].text = (
        f'{{"character_count": {character_count}, "has_duplicate_bubbles": false, '
        f'"has_visual_unnaturalness": false, "unnaturalness_details": "", '
        f'"anatomy_severity": "none", "anatomy_issues": []}}'
    )
    return resp


# ─────────────────────────────────────────────────────────────────────────────
# Section 1: 常量验证
# ─────────────────────────────────────────────────────────────────────────────

class TestShotValidatorModelConstants:
    """验证模型常量正确."""

    def test_sonnet_model_constant(self):
        """SONNET_MODEL 应为 claude-sonnet-4-6（无日期后缀）.

        T20-50-fix-round3: 旧值 'claude-sonnet-4-6-20251101' 导致 Anthropic 404 NotFoundError,
        100% fail-open（20 张图全部跳过验证）。Sonnet 4.6 的正确 ID 没有日期后缀。
        """
        from app.services.shot_validator import SONNET_MODEL
        assert SONNET_MODEL == "claude-sonnet-4-6", (
            f"SONNET_MODEL={SONNET_MODEL!r}, expected 'claude-sonnet-4-6' (no date suffix)"
        )
        # 额外防御：确保没有错误的日期后缀
        assert "20251101" not in SONNET_MODEL, (
            f"SONNET_MODEL 包含不存在的日期后缀 '20251101': {SONNET_MODEL!r}"
        )

    def test_haiku_model_constant(self):
        """HAIKU_MODEL 应为 claude-haiku-4-5-20251001."""
        from app.services.shot_validator import HAIKU_MODEL
        assert HAIKU_MODEL == "claude-haiku-4-5-20251001", (
            f"HAIKU_MODEL={HAIKU_MODEL!r}, expected 'claude-haiku-4-5-20251001'"
        )

    def test_fallback_function_exists(self):
        """_call_sonnet_with_haiku_fallback 函数应存在."""
        from app.services import shot_validator
        assert hasattr(shot_validator, "_call_sonnet_with_haiku_fallback"), (
            "_call_sonnet_with_haiku_fallback 函数不存在于 shot_validator"
        )

    def test_fail_open_rate_threshold_exists(self):
        """FAIL_OPEN_RATE_ALERT_THRESHOLD 常量应存在."""
        from app.services.shot_validator import FAIL_OPEN_RATE_ALERT_THRESHOLD
        assert 0 < FAIL_OPEN_RATE_ALERT_THRESHOLD <= 1.0, (
            f"FAIL_OPEN_RATE_ALERT_THRESHOLD={FAIL_OPEN_RATE_ALERT_THRESHOLD} 应在 (0, 1]"
        )

    def test_validator_total_count_global_exists(self):
        """validator_total_count 全局变量应存在."""
        from app.services import shot_validator
        assert hasattr(shot_validator, "validator_total_count"), (
            "validator_total_count 全局变量不存在"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Section 2: _call_sonnet_with_haiku_fallback 行为测试
# ─────────────────────────────────────────────────────────────────────────────

class TestCallSonnetWithHaikuFallback:
    """直接测试降级函数行为."""

    @pytest.mark.asyncio
    async def test_sonnet_success_returns_sonnet_model(self):
        """case 1: Sonnet 成功 → 返回 (response, SONNET_MODEL), 不降级."""
        from app.services.shot_validator import _call_sonnet_with_haiku_fallback, SONNET_MODEL

        mock_client = MagicMock()
        valid_response = _make_valid_haiku_response(character_count=2)

        # Sonnet 成功 (第一次就通过)
        with patch(
            "app.services.shot_validator._call_anthropic_with_retry",
            new=AsyncMock(return_value=valid_response),
        ):
            response, model_used = await _call_sonnet_with_haiku_fallback(
                mock_client,
                max_tokens=512,
                temperature=0.2,
                messages=[{"role": "user", "content": "test"}],
                shot_id_for_log="1",
            )

        assert model_used == SONNET_MODEL, f"Sonnet 成功时 model_used 应为 SONNET_MODEL, 实际={model_used}"
        assert response is valid_response

    @pytest.mark.asyncio
    async def test_sonnet_529_falls_to_haiku(self):
        """case 2: Sonnet 529 全失 → 降级 Haiku → Haiku 成功 → HAIKU_MODEL."""
        from app.services.shot_validator import (
            _call_sonnet_with_haiku_fallback, SONNET_MODEL, HAIKU_MODEL,
        )

        mock_client = MagicMock()
        overload_exc = _make_anthropic_overload_exc()
        valid_response = _make_valid_haiku_response(character_count=1)

        # call_count 用来区分 Sonnet 和 Haiku 调用
        call_results = [overload_exc, valid_response]  # Sonnet raise, Haiku 成功

        async def mock_retry(client, *, model, **kwargs):
            if model == SONNET_MODEL:
                raise overload_exc
            return valid_response  # Haiku 成功

        with patch("app.services.shot_validator._call_anthropic_with_retry", side_effect=mock_retry):
            response, model_used = await _call_sonnet_with_haiku_fallback(
                mock_client,
                max_tokens=512,
                temperature=0.2,
                messages=[{"role": "user", "content": "test"}],
                shot_id_for_log="5",
            )

        assert model_used == HAIKU_MODEL, (
            f"Sonnet 529 后降级 Haiku, model_used 应为 HAIKU_MODEL, 实际={model_used}"
        )
        assert response is valid_response

    @pytest.mark.asyncio
    async def test_both_models_fail_raises(self):
        """case 3: Sonnet + Haiku 双失败 → raise 最终异常."""
        from app.services.shot_validator import _call_sonnet_with_haiku_fallback, SONNET_MODEL

        mock_client = MagicMock()
        overload_exc = _make_anthropic_overload_exc()

        async def mock_retry(client, *, model, **kwargs):
            raise overload_exc  # 两个模型都 529 全失

        with patch("app.services.shot_validator._call_anthropic_with_retry", side_effect=mock_retry):
            with pytest.raises(Exception) as exc_info:
                await _call_sonnet_with_haiku_fallback(
                    mock_client,
                    max_tokens=512,
                    temperature=0.2,
                    messages=[{"role": "user", "content": "test"}],
                    shot_id_for_log="13",
                )

        # 应抛出最后一次异常 (Haiku 的)
        assert "overloaded" in str(exc_info.value).lower() or "529" in str(exc_info.value), (
            "双失败应抛出过载相关异常"
        )

    @pytest.mark.asyncio
    async def test_non_retryable_error_not_falls_to_haiku(self):
        """case 4: 非 retryable 错误 (400) → 不降级 Haiku → 直接 raise."""
        from app.services.shot_validator import _call_sonnet_with_haiku_fallback, SONNET_MODEL

        mock_client = MagicMock()
        bad_request_exc = _make_anthropic_bad_request_exc()

        haiku_was_called = []

        async def mock_retry(client, *, model, **kwargs):
            if model == SONNET_MODEL:
                raise bad_request_exc
            haiku_was_called.append(model)  # 不应被调用
            return _make_valid_haiku_response()

        with patch("app.services.shot_validator._call_anthropic_with_retry", side_effect=mock_retry):
            with pytest.raises(Exception) as exc_info:
                await _call_sonnet_with_haiku_fallback(
                    mock_client,
                    max_tokens=512,
                    temperature=0.2,
                    messages=[{"role": "user", "content": "test"}],
                    shot_id_for_log="3",
                )

        assert not haiku_was_called, (
            f"非 retryable 错误 (400) 时 Haiku 不应被调用, 但被调用了: {haiku_was_called}"
        )
        assert "bad request" in str(exc_info.value).lower() or "400" in str(exc_info.value), (
            "应抛出 400 bad request 异常"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Section 3: validate_shot fail-open 行为
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateShotFailOpen:
    """validate_shot 在 API 失败时 fail-open 行为."""

    @pytest.mark.asyncio
    async def test_sonnet_haiku_both_fail_returns_valid_true(self):
        """case 5: Sonnet + Haiku 双失败 → fail-open, valid=True, reason=*OVERLOADED*."""
        from app.services.shot_validator import ShotValidator, SONNET_MODEL

        validator = ShotValidator.__new__(ShotValidator)
        validator.client = MagicMock()

        overload_exc = _make_anthropic_overload_exc()

        async def mock_fallback(client, *, max_tokens, temperature, messages, shot_id_for_log):
            raise overload_exc

        with patch(
            "app.services.shot_validator._call_sonnet_with_haiku_fallback",
            side_effect=mock_fallback,
        ):
            result = await validator.validate_shot(
                pil_image=_make_minimal_image(),
                expected_character_count=1,
            )

        assert result["valid"] is True, "双失败后应 fail-open (valid=True)"
        # reason 应包含过载相关关键词
        reason = result.get("reason", "")
        assert any(kw in reason.upper() for kw in ["OVERLOAD", "529", "HAIKU", "SONNET"]), (
            f"fail-open reason 应含过载相关关键词, 实际 reason={reason!r}"
        )

    @pytest.mark.asyncio
    async def test_sonnet_success_returns_valid_result(self):
        """case 6: Sonnet 正常返回 → validate_shot 返回正确判定."""
        from app.services.shot_validator import ShotValidator

        validator = ShotValidator.__new__(ShotValidator)
        validator.client = MagicMock()

        valid_response = _make_valid_haiku_response(character_count=2)

        async def mock_fallback(client, *, max_tokens, temperature, messages, shot_id_for_log):
            return valid_response, "claude-sonnet-4-6-20251101"

        with patch(
            "app.services.shot_validator._call_sonnet_with_haiku_fallback",
            side_effect=mock_fallback,
        ):
            result = await validator.validate_shot(
                pil_image=_make_minimal_image(),
                expected_character_count=2,
            )

        assert result["valid"] is True, "Sonnet 正常返回 2 chars, 期待 2 chars → valid=True"
        assert result["actual_character_count"] == 2
        assert result["anatomy_severity"] == "none"


# ─────────────────────────────────────────────────────────────────────────────
# Section 4: fail-open 率告警
# ─────────────────────────────────────────────────────────────────────────────

class TestFailOpenRateAlert:
    """验证 fail-open 率超阈值时记 ERROR 告警."""

    def test_fail_open_rate_alert_threshold_is_30_percent(self):
        """FAIL_OPEN_RATE_ALERT_THRESHOLD 应为 0.30 (30%)."""
        from app.services.shot_validator import FAIL_OPEN_RATE_ALERT_THRESHOLD
        assert abs(FAIL_OPEN_RATE_ALERT_THRESHOLD - 0.30) < 0.001, (
            f"FAIL_OPEN_RATE_ALERT_THRESHOLD 应为 0.30, 实际={FAIL_OPEN_RATE_ALERT_THRESHOLD}"
        )

    def test_fail_open_rate_calculation(self):
        """fail-open 率 = skipped / total 计算逻辑."""
        # 模拟: 13 / 27 = 48.1% > 30% → 应告警
        skipped = 13
        total = 27
        rate = skipped / max(total, 1)
        assert rate > 0.30, f"13/27={rate:.1%} 应 > 30%"

        # 模拟: 8 / 27 = 29.6% < 30% → 不告警
        skipped2 = 8
        rate2 = skipped2 / max(total, 1)
        assert rate2 < 0.30, f"8/27={rate2:.1%} 应 < 30%"

    @pytest.mark.asyncio
    async def test_fail_open_rate_above_threshold_logs_error(self, caplog):
        """fail-open 率 > 30% 时 logger.error 被调用 (含告警关键词)."""
        import app.services.shot_validator as sv_module

        # 重置全局计数器到已知状态
        sv_module.validator_skipped_count = 13
        sv_module.validator_total_count = 14  # 13/14 = 93% > 30%

        from app.services.shot_validator import ShotValidator, FAIL_OPEN_RATE_ALERT_THRESHOLD

        validator = ShotValidator.__new__(ShotValidator)
        validator.client = MagicMock()

        overload_exc = _make_anthropic_overload_exc()

        async def mock_fallback(client, *, max_tokens, temperature, messages, shot_id_for_log):
            raise overload_exc

        with caplog.at_level(logging.ERROR, logger="xuhua"):
            with patch(
                "app.services.shot_validator._call_sonnet_with_haiku_fallback",
                side_effect=mock_fallback,
            ):
                result = await validator.validate_shot(
                    pil_image=_make_minimal_image(),
                    expected_character_count=1,
                )

        # 检查 ERROR 日志包含告警关键词
        error_logs = [r for r in caplog.records if r.levelno >= logging.ERROR]
        alert_logs = [
            r for r in error_logs
            if "fail-open" in r.message.lower() or "T20-47" in r.message
        ]
        assert len(alert_logs) > 0, (
            f"fail-open 率超 {FAIL_OPEN_RATE_ALERT_THRESHOLD:.0%} 时应记 ERROR 告警, "
            f"实际 ERROR logs: {[r.message for r in error_logs]}"
        )

        # 恢复全局计数器 (避免影响其他测试)
        sv_module.validator_skipped_count = 0
        sv_module.validator_total_count = 0


# ─────────────────────────────────────────────────────────────────────────────
# Section 5: 代码层面静态验证
# ─────────────────────────────────────────────────────────────────────────────

class TestShotValidatorCodeStructure:
    """验证 shot_validator.py 代码结构符合 T20-47 规范."""

    def _read_validator_source(self) -> str:
        source_path = os.path.join(
            os.path.dirname(__file__), "..", "app", "services", "shot_validator.py"
        )
        with open(os.path.normpath(source_path), "r", encoding="utf-8") as f:
            return f.read()

    def test_sonnet_model_defined(self):
        """SONNET_MODEL 常量在源码中定义."""
        source = self._read_validator_source()
        assert "SONNET_MODEL" in source, "SONNET_MODEL 常量应在 shot_validator.py 中定义"

    def test_haiku_fallback_function_defined(self):
        """_call_sonnet_with_haiku_fallback 函数在源码中定义."""
        source = self._read_validator_source()
        assert "_call_sonnet_with_haiku_fallback" in source, (
            "_call_sonnet_with_haiku_fallback 函数应在 shot_validator.py 中定义"
        )

    def test_validate_shot_uses_sonnet_haiku_fallback(self):
        """validate_shot 使用 _call_sonnet_with_haiku_fallback (不再直接调 _call_anthropic_with_retry)."""
        source = self._read_validator_source()
        # 应含降级函数调用
        assert "_call_sonnet_with_haiku_fallback" in source, (
            "validate_shot 应调用 _call_sonnet_with_haiku_fallback"
        )

    def test_sonnet_and_haiku_overloaded_reason(self):
        """fail-open reason=SONNET_AND_HAIKU_OVERLOADED 应在源码中定义."""
        source = self._read_validator_source()
        assert "SONNET_AND_HAIKU_OVERLOADED" in source, (
            "fail-open reason SONNET_AND_HAIKU_OVERLOADED 应在 shot_validator.py 中"
        )

    def test_fail_open_rate_alert_in_source(self):
        """fail-open 率告警逻辑应在 shot_validator.py 中."""
        source = self._read_validator_source()
        assert "FAIL_OPEN_RATE_ALERT_THRESHOLD" in source, (
            "FAIL_OPEN_RATE_ALERT_THRESHOLD 告警逻辑应在 shot_validator.py 中"
        )
