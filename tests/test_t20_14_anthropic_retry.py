"""RISK-T20-14 (2026-05-19) — ShotValidator Anthropic 429/529/503 退避重试

测试 ShotValidator 对 Anthropic 过载错误的退避重试机制:
  - 退避阶梯: 2 / 8 / 30 秒 + ±30% jitter
  - 仅 429 / 529 / 503 retry; 其他错误直接 fail-open
  - 最多 3 次重试 (4 次总尝试)
  - 全部失败才走 fail-open (reason=OVERLOAD_RETRY_EXHAUSTED_*)

test17 v2 实证: 18 次 Anthropic 调用全部 529 → fail-open → B51 fallback 形同虚设
修复后: 3 次退避重试给 Anthropic 自愈窗口, 整体可用率应显著提升

测试覆盖 (universal):
  - _is_retryable_anthropic_error: 429/529/503/'overloaded' 文本 → True; 401/400 → False
  - _call_anthropic_with_retry: 第 N 次成功 / 全部失败 / 不可重试立即抛
  - 异常退避顺序: 2 / 8 / 30 阶梯
  - jitter 在 ±30% 范围
  - 集成: validate_shot 在 mock 529 时走重试路径 → 全失败 fail-open
"""

import asyncio
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# 1. Retryable 判定
# ---------------------------------------------------------------------------

class TestIsRetryableAnthropicError:
    """RISK-T20-14: _is_retryable_anthropic_error 正确识别 429/529/503"""

    def test_429_is_retryable(self):
        from app.services.shot_validator import _is_retryable_anthropic_error

        class FakeRateLimitError(Exception):
            status_code = 429

        retryable, code = _is_retryable_anthropic_error(FakeRateLimitError("rate limit"))
        assert retryable is True
        assert code == 429

    def test_529_is_retryable(self):
        from app.services.shot_validator import _is_retryable_anthropic_error

        class FakeOverloadedError(Exception):
            status_code = 529

        retryable, code = _is_retryable_anthropic_error(FakeOverloadedError("overloaded"))
        assert retryable is True
        assert code == 529

    def test_503_is_retryable(self):
        from app.services.shot_validator import _is_retryable_anthropic_error

        class FakeServiceUnavailable(Exception):
            status_code = 503

        retryable, code = _is_retryable_anthropic_error(FakeServiceUnavailable("unavail"))
        assert retryable is True
        assert code == 503

    def test_401_not_retryable(self):
        """认证失败不可重试"""
        from app.services.shot_validator import _is_retryable_anthropic_error

        class FakeAuthError(Exception):
            status_code = 401

        retryable, code = _is_retryable_anthropic_error(FakeAuthError("auth fail"))
        assert retryable is False

    def test_400_not_retryable(self):
        """请求错误不可重试"""
        from app.services.shot_validator import _is_retryable_anthropic_error

        class FakeBadRequest(Exception):
            status_code = 400

        retryable, code = _is_retryable_anthropic_error(FakeBadRequest("bad req"))
        assert retryable is False

    def test_overloaded_text_fallback(self):
        """无 status_code 但 message 含 'overloaded' → 仍可重试 (兜底)"""
        from app.services.shot_validator import _is_retryable_anthropic_error

        retryable, code = _is_retryable_anthropic_error(
            Exception("API Error: Overloaded - please retry later")
        )
        assert retryable is True

    def test_rate_limit_text_fallback(self):
        """无 status_code 但 message 含 'rate limit' → 仍可重试"""
        from app.services.shot_validator import _is_retryable_anthropic_error

        retryable, code = _is_retryable_anthropic_error(
            Exception("Rate Limit exceeded")
        )
        assert retryable is True

    def test_generic_error_not_retryable(self):
        """普通异常不可重试"""
        from app.services.shot_validator import _is_retryable_anthropic_error

        retryable, code = _is_retryable_anthropic_error(ValueError("bad data"))
        assert retryable is False


# ---------------------------------------------------------------------------
# 2. 退避常量验证
# ---------------------------------------------------------------------------

class TestBackoffConstants:
    """RISK-T20-14: 退避阶梯常量必须 = (2, 8, 30) 类似 Seedream"""

    def test_retry_delays_match_design(self):
        from app.services.shot_validator import SHOT_VALIDATOR_RETRY_DELAYS_SEC
        assert SHOT_VALIDATOR_RETRY_DELAYS_SEC == (2, 8, 30), \
            f"退避阶梯设计为 2/8/30s, 实际 {SHOT_VALIDATOR_RETRY_DELAYS_SEC}"

    def test_jitter_ratio_30_percent(self):
        from app.services.shot_validator import SHOT_VALIDATOR_RETRY_JITTER_RATIO
        assert SHOT_VALIDATOR_RETRY_JITTER_RATIO == 0.30, \
            f"jitter 设计为 ±30%, 实际 {SHOT_VALIDATOR_RETRY_JITTER_RATIO * 100}%"

    def test_retryable_codes_include_429_529_503(self):
        from app.services.shot_validator import SHOT_VALIDATOR_RETRYABLE_STATUS_CODES
        for code in (429, 529, 503):
            assert code in SHOT_VALIDATOR_RETRYABLE_STATUS_CODES

    def test_max_total_attempts_4(self):
        """4 总尝试 = 1 原始 + 3 退避重试"""
        from app.services.shot_validator import SHOT_VALIDATOR_RETRY_DELAYS_SEC
        total = len(SHOT_VALIDATOR_RETRY_DELAYS_SEC) + 1
        assert total == 4, f"总尝试次数应为 4, 实际 {total}"


# ---------------------------------------------------------------------------
# 3. _call_anthropic_with_retry 行为
# ---------------------------------------------------------------------------

class TestCallAnthropicWithRetry:
    """RISK-T20-14: 测试重试 helper 行为"""

    @pytest.mark.asyncio
    async def test_success_first_try(self, monkeypatch):
        """第一次就成功 → 不重试, 直接返回"""
        from app.services import shot_validator as sv

        call_count = {"n": 0}
        sleep_calls = {"n": 0}

        class FakeMsg:
            content = "ok"

        class FakeClient:
            class messages:
                @staticmethod
                async def create(**kwargs):
                    call_count["n"] += 1
                    return FakeMsg()

        async def fake_sleep(t):
            sleep_calls["n"] += 1

        monkeypatch.setattr(sv.asyncio, "sleep", fake_sleep)

        resp = await sv._call_anthropic_with_retry(
            FakeClient(), model="x", max_tokens=10, temperature=0, messages=[],
        )
        assert call_count["n"] == 1
        assert sleep_calls["n"] == 0  # 没退避
        assert resp.content == "ok"

    @pytest.mark.asyncio
    async def test_retry_succeeds_on_third_attempt(self, monkeypatch):
        """前 2 次 529, 第 3 次成功 → retry 2 次 ✅"""
        from app.services import shot_validator as sv

        attempt_track = {"n": 0}
        sleep_calls = []

        class FakeOverloaded(Exception):
            status_code = 529

        class FakeMsg:
            content = "ok after retry"

        class FakeClient:
            class messages:
                @staticmethod
                async def create(**kwargs):
                    attempt_track["n"] += 1
                    if attempt_track["n"] < 3:
                        raise FakeOverloaded("Overloaded")
                    return FakeMsg()

        async def fake_sleep(t):
            sleep_calls.append(t)

        monkeypatch.setattr(sv.asyncio, "sleep", fake_sleep)

        resp = await sv._call_anthropic_with_retry(
            FakeClient(), model="x", max_tokens=10, temperature=0, messages=[],
        )
        assert attempt_track["n"] == 3
        assert len(sleep_calls) == 2  # 重试 2 次, 各 1 次 sleep
        assert resp.content == "ok after retry"

    @pytest.mark.asyncio
    async def test_all_retries_exhausted(self, monkeypatch):
        """全部 4 次都 529 → raise 最后一次异常 (走 fail-open)"""
        from app.services import shot_validator as sv

        attempt_track = {"n": 0}
        sleep_calls = []

        class FakeOverloaded(Exception):
            status_code = 529

        class FakeClient:
            class messages:
                @staticmethod
                async def create(**kwargs):
                    attempt_track["n"] += 1
                    raise FakeOverloaded("Overloaded")

        async def fake_sleep(t):
            sleep_calls.append(t)

        monkeypatch.setattr(sv.asyncio, "sleep", fake_sleep)

        with pytest.raises(FakeOverloaded):
            await sv._call_anthropic_with_retry(
                FakeClient(), model="x", max_tokens=10, temperature=0, messages=[],
            )
        assert attempt_track["n"] == 4  # 1 + 3 retry
        assert len(sleep_calls) == 3  # 3 次 sleep

    @pytest.mark.asyncio
    async def test_non_retryable_raises_immediately(self, monkeypatch):
        """401 认证错误 → 立即 raise, 不重试"""
        from app.services import shot_validator as sv

        attempt_track = {"n": 0}
        sleep_calls = []

        class FakeAuth(Exception):
            status_code = 401

        class FakeClient:
            class messages:
                @staticmethod
                async def create(**kwargs):
                    attempt_track["n"] += 1
                    raise FakeAuth("auth fail")

        async def fake_sleep(t):
            sleep_calls.append(t)

        monkeypatch.setattr(sv.asyncio, "sleep", fake_sleep)

        with pytest.raises(FakeAuth):
            await sv._call_anthropic_with_retry(
                FakeClient(), model="x", max_tokens=10, temperature=0, messages=[],
            )
        assert attempt_track["n"] == 1  # 没重试
        assert len(sleep_calls) == 0

    @pytest.mark.asyncio
    async def test_backoff_delays_match_schedule(self, monkeypatch):
        """退避阶梯实测: 第 1 次失败 sleep~2s, 第 2 次 sleep~8s, 第 3 次 sleep~30s"""
        from app.services import shot_validator as sv

        sleep_calls = []

        class FakeOverloaded(Exception):
            status_code = 529

        class FakeClient:
            class messages:
                @staticmethod
                async def create(**kwargs):
                    raise FakeOverloaded("Overloaded")

        async def fake_sleep(t):
            sleep_calls.append(t)

        monkeypatch.setattr(sv.asyncio, "sleep", fake_sleep)

        with pytest.raises(FakeOverloaded):
            await sv._call_anthropic_with_retry(
                FakeClient(), model="x", max_tokens=10, temperature=0, messages=[],
            )
        # 3 次 sleep 应分别在 2/8/30 附近（±30% jitter）
        assert len(sleep_calls) == 3
        # 第 1 次 sleep ∈ [1.4, 2.6]（jitter 范围）
        assert 1.4 <= sleep_calls[0] <= 2.6, f"第 1 次 sleep={sleep_calls[0]} 偏离 2±30%"
        # 第 2 次 sleep ∈ [5.6, 10.4]
        assert 5.6 <= sleep_calls[1] <= 10.4, f"第 2 次 sleep={sleep_calls[1]} 偏离 8±30%"
        # 第 3 次 sleep ∈ [21, 39]
        assert 21.0 <= sleep_calls[2] <= 39.0, f"第 3 次 sleep={sleep_calls[2]} 偏离 30±30%"

    @pytest.mark.asyncio
    async def test_overloaded_text_in_message_retries(self, monkeypatch):
        """异常无 status_code 但 message 含 'overloaded' → 仍重试"""
        from app.services import shot_validator as sv

        attempt_track = {"n": 0}
        sleep_calls = []

        class FakeMsg:
            content = "recovered"

        class FakeClient:
            class messages:
                @staticmethod
                async def create(**kwargs):
                    attempt_track["n"] += 1
                    if attempt_track["n"] < 2:
                        raise Exception("API Error: Overloaded — try later")
                    return FakeMsg()

        async def fake_sleep(t):
            sleep_calls.append(t)

        monkeypatch.setattr(sv.asyncio, "sleep", fake_sleep)

        resp = await sv._call_anthropic_with_retry(
            FakeClient(), model="x", max_tokens=10, temperature=0, messages=[],
        )
        assert attempt_track["n"] == 2
        assert len(sleep_calls) == 1


# ---------------------------------------------------------------------------
# 4. validate_shot 集成路径（fail-open after exhaustion）
# ---------------------------------------------------------------------------

class TestValidateShotFailOpenAfterRetry:
    """RISK-T20-14: validate_shot 在 retry 耗尽后走 fail-open"""

    @pytest.mark.asyncio
    async def test_validate_shot_fail_open_after_retry_exhausted(self, monkeypatch, caplog):
        """模拟 18 次 Anthropic 529 → ShotValidator 3 次退避后 fail-open"""
        from app.services import shot_validator as sv
        from PIL import Image

        class FakeOverloaded(Exception):
            status_code = 529

        attempt_track = {"n": 0}
        sleep_calls = []

        class FakeClient:
            class messages:
                @staticmethod
                async def create(**kwargs):
                    attempt_track["n"] += 1
                    raise FakeOverloaded("Overloaded — service degraded")

        async def fake_sleep(t):
            sleep_calls.append(t)

        validator = sv.ShotValidator()
        validator.client = FakeClient()
        monkeypatch.setattr(sv.asyncio, "sleep", fake_sleep)

        img = Image.new("RGB", (100, 100), (255, 255, 255))
        result = await validator.validate_shot(
            pil_image=img,
            expected_character_count=2,
            shot={"shot_id": 7},
        )
        # 关键: fail-open valid=True (不阻塞 pipeline)
        assert result["valid"] is True
        # 关键: 真做了 4 次尝试 (1 原 + 3 retry)
        assert attempt_track["n"] == 4
        assert len(sleep_calls) == 3
        # 关键: reason 标识为 OVERLOAD_RETRY_EXHAUSTED (不是普通 API_ERROR_SKIPPED)
        assert "OVERLOAD_RETRY_EXHAUSTED" in result["reason"], \
            f"reason 应含 OVERLOAD_RETRY_EXHAUSTED, 实际 {result['reason']}"

    @pytest.mark.asyncio
    async def test_validate_shot_fail_open_immediately_on_non_retryable(self, monkeypatch):
        """非可重试错误 (401) → 立即 fail-open, 不重试"""
        from app.services import shot_validator as sv
        from PIL import Image

        class FakeAuth(Exception):
            status_code = 401

        attempt_track = {"n": 0}
        sleep_calls = []

        class FakeClient:
            class messages:
                @staticmethod
                async def create(**kwargs):
                    attempt_track["n"] += 1
                    raise FakeAuth("auth fail")

        async def fake_sleep(t):
            sleep_calls.append(t)

        validator = sv.ShotValidator()
        validator.client = FakeClient()
        monkeypatch.setattr(sv.asyncio, "sleep", fake_sleep)

        img = Image.new("RGB", (100, 100), (255, 255, 255))
        result = await validator.validate_shot(
            pil_image=img,
            expected_character_count=2,
            shot={"shot_id": 8},
        )
        assert result["valid"] is True  # fail-open
        assert attempt_track["n"] == 1  # 没重试
        assert len(sleep_calls) == 0
        assert "API_ERROR_SKIPPED" in result["reason"]


# ---------------------------------------------------------------------------
# 5. 源码验证
# ---------------------------------------------------------------------------

class TestSourceCodeVerification:
    """确保 shot_validator.py 真有 retry 机制"""

    def test_has_call_anthropic_with_retry_helper(self):
        from app.services.shot_validator import _call_anthropic_with_retry
        assert callable(_call_anthropic_with_retry)

    def test_has_is_retryable_helper(self):
        from app.services.shot_validator import _is_retryable_anthropic_error
        assert callable(_is_retryable_anthropic_error)

    def test_validate_shot_uses_retry_helper(self):
        """validate_shot 必须调用 _call_anthropic_with_retry, 不直接 await client.messages.create"""
        import inspect
        from app.services import shot_validator
        src = inspect.getsource(shot_validator.ShotValidator.validate_shot)
        assert "_call_anthropic_with_retry" in src, \
            "validate_shot 必须调用 _call_anthropic_with_retry"

    def test_no_direct_messages_create_in_validate_shot(self):
        """validate_shot 不应直接 await self.client.messages.create (绕过 retry)"""
        import inspect
        from app.services import shot_validator
        src = inspect.getsource(shot_validator.ShotValidator.validate_shot)
        assert "await self.client.messages.create" not in src, \
            "validate_shot 不能直接 await self.client.messages.create, 必须经 retry helper"
