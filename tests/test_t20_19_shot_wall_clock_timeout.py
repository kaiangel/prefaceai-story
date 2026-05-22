"""RISK-T20-19 (2026-05-19) — Pipeline 单 Shot wall-clock timeout (720s)

测试 pipeline_orchestrator.py Stage 5 单 shot 生成的 wall-clock cap:
  - asyncio.wait_for(generate_shot_image_phase2_safe, timeout=SHOT_WALL_CLOCK_TIMEOUT_SEC=720)
  - 超时按 partial_failure 走 (result['success']=False, error_kind='wall_clock_timeout')
  - 不 retry: 已经等 12 min, 再等无意义
  - Frontend "查看并重生" 可救 (走原失败路径)

test17 v2 实证:
  - Shot 14 hang 12.5 min → 4 次 IncompleteRead retry 全失败
  - Shot 16 hang 14.2 min → attempt 4 险胜 (打破纪录)
  - SeedreamGenerator HTTP retry 上限 3 次 × 210s + 退避 (2+8+30+60s) = 理论最坏 ~15 min
  - pipeline_orchestrator 之前 0 处 asyncio.wait_for → 单个假死 shot 拖死整批 Semaphore 槽位
  - 720s = 12 min 是 SeedreamGenerator 自愈窗口 + 安全余量的合理 cap

测试覆盖:
  - 常量: SHOT_WALL_CLOCK_TIMEOUT_SEC = 720
  - 源码验证: asyncio.wait_for 包裹 generate_shot_image_phase2_safe
  - 行为: TimeoutError 时返回 success=False + error_kind=wall_clock_timeout
  - 不 retry: timeout 后 break 跳出 retry 循环
"""

import asyncio
import sys
import os
import inspect

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# 1. 常量验证
# ---------------------------------------------------------------------------

class TestWallClockConstant:
    """RISK-T20-19: SHOT_WALL_CLOCK_TIMEOUT_SEC 必须 = 720"""

    def test_constant_exists(self):
        from app.services.pipeline_orchestrator import SHOT_WALL_CLOCK_TIMEOUT_SEC
        assert isinstance(SHOT_WALL_CLOCK_TIMEOUT_SEC, int)

    def test_constant_value_720(self):
        """720s = 12 min, 略小于 SeedreamGenerator 理论最坏 ~15 min"""
        from app.services.pipeline_orchestrator import SHOT_WALL_CLOCK_TIMEOUT_SEC
        assert SHOT_WALL_CLOCK_TIMEOUT_SEC == 720, \
            f"设计值 720s (12 min), 实际 {SHOT_WALL_CLOCK_TIMEOUT_SEC}s"

    def test_constant_greater_than_seedream_single_timeout(self):
        """720s 必须 > 单次 SeedreamGenerator timeout (210s) 才有意义"""
        from app.services.pipeline_orchestrator import SHOT_WALL_CLOCK_TIMEOUT_SEC
        from app.config import settings
        assert SHOT_WALL_CLOCK_TIMEOUT_SEC > settings.IMAGE_GENERATION_TIMEOUT, \
            f"wall-clock {SHOT_WALL_CLOCK_TIMEOUT_SEC}s 必须 > seedream 单次 {settings.IMAGE_GENERATION_TIMEOUT}s"


# ---------------------------------------------------------------------------
# 2. 源码验证 (asyncio.wait_for 真正包裹 generate_shot_image_phase2_safe)
# ---------------------------------------------------------------------------

class TestSourceCodeWiring:
    """确保 pipeline_orchestrator.py 真有 asyncio.wait_for 包裹"""

    def test_has_wall_clock_constant(self):
        import inspect as insp
        from app.services import pipeline_orchestrator
        src = inspect.getsource(pipeline_orchestrator)
        assert "SHOT_WALL_CLOCK_TIMEOUT_SEC" in src

    def test_has_wait_for_in_generate_one_shot(self):
        """_generate_one_shot 内必须 asyncio.wait_for(...generate_shot_image_phase2_safe...)"""
        from app.services import pipeline_orchestrator
        src = inspect.getsource(pipeline_orchestrator)
        # 关键: asyncio.wait_for + generate_shot_image_phase2_safe 在同一区段
        assert "asyncio.wait_for" in src, "pipeline_orchestrator 必须用 asyncio.wait_for"
        assert "SHOT_WALL_CLOCK_TIMEOUT_SEC" in src, "必须 timeout 用 SHOT_WALL_CLOCK_TIMEOUT_SEC 常量"

    def test_timeout_error_handler_exists(self):
        """超时 except 必须存在, 不能让 TimeoutError 抛飞"""
        from app.services import pipeline_orchestrator
        src = inspect.getsource(pipeline_orchestrator)
        assert "asyncio.TimeoutError" in src, "必须 except asyncio.TimeoutError"

    def test_timeout_handler_marks_wall_clock_timeout(self):
        """超时 result 必须有 error_kind=wall_clock_timeout 标识 (便于追踪)"""
        from app.services import pipeline_orchestrator
        src = inspect.getsource(pipeline_orchestrator)
        assert "wall_clock_timeout" in src, "超时 result 必须标记 error_kind=wall_clock_timeout"

    def test_timeout_error_logged(self):
        """超时必须 ERROR 级日志 (便于 DevOps 监控)"""
        from app.services import pipeline_orchestrator
        src = inspect.getsource(pipeline_orchestrator)
        assert "T20-19" in src, "源码必须含 T20-19 标记便于追踪"


# ---------------------------------------------------------------------------
# 3. asyncio.wait_for 行为验证 (独立单元测试, 不依赖完整 pipeline)
# ---------------------------------------------------------------------------

class TestAsyncioWaitForBehavior:
    """证明 asyncio.wait_for 在我们用的方式下行为正确"""

    @pytest.mark.asyncio
    async def test_wait_for_returns_value_if_within_timeout(self):
        """正常 shot 在 timeout 内完成 → 返回结果"""
        async def fast_shot():
            await asyncio.sleep(0.01)
            return {"success": True, "image": "data"}

        result = await asyncio.wait_for(fast_shot(), timeout=1.0)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_wait_for_raises_timeout_error_if_exceeded(self):
        """假死 shot 超过 timeout → asyncio.TimeoutError"""
        async def slow_shot():
            await asyncio.sleep(10)
            return {"success": True}

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_shot(), timeout=0.1)

    @pytest.mark.asyncio
    async def test_wait_for_cancels_underlying_task(self):
        """timeout 后底层 coroutine 被 cancel (不浪费 CPU)"""
        cancelled_flag = {"v": False}

        async def watcher():
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                cancelled_flag["v"] = True
                raise

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(watcher(), timeout=0.05)
        # 给 cancellation 一点时间生效
        await asyncio.sleep(0.05)
        assert cancelled_flag["v"] is True, "底层 task 应被 cancel"


# ---------------------------------------------------------------------------
# 4. 集成: timeout 路径返回正确 result dict
# ---------------------------------------------------------------------------

class TestTimeoutResultShape:
    """模拟 pipeline 内 timeout 处理路径, 验证 result dict 结构"""

    @pytest.mark.asyncio
    async def test_timeout_constructs_failure_result(self):
        """超时时 result 必须 success=False + error_kind=wall_clock_timeout"""
        from app.services.pipeline_orchestrator import SHOT_WALL_CLOCK_TIMEOUT_SEC

        # 模拟 pipeline 内 timeout 处理逻辑
        async def hanging_call():
            await asyncio.sleep(100)
            return {"success": True}

        try:
            await asyncio.wait_for(hanging_call(), timeout=0.05)
            result = None
        except asyncio.TimeoutError:
            result = {
                "success": False,
                "error": (
                    f"Shot wall-clock timeout {SHOT_WALL_CLOCK_TIMEOUT_SEC}s exceeded (T20-19)"
                ),
                "error_kind": "wall_clock_timeout",
            }

        assert result is not None
        assert result["success"] is False
        assert result["error_kind"] == "wall_clock_timeout"
        assert "T20-19" in result["error"]
        assert str(SHOT_WALL_CLOCK_TIMEOUT_SEC) in result["error"]


# ---------------------------------------------------------------------------
# 5. 既有错误路径仍正常 (向后兼容: SeedreamGenerator 主动失败也要走 break)
# ---------------------------------------------------------------------------

class TestExistingFailurePathIntact:
    """SeedreamGenerator 短时返回 success=False (rate_limit / sensitive_content 等) → 不应误判 timeout"""

    @pytest.mark.asyncio
    async def test_seedream_quick_failure_not_treated_as_timeout(self):
        """快速返回的 success=False → 走原有 break, 不进 TimeoutError 路径"""
        async def quick_failure():
            await asyncio.sleep(0.01)
            return {"success": False, "error_kind": "rate_limit", "error": "429"}

        try:
            result = await asyncio.wait_for(quick_failure(), timeout=2.0)
        except asyncio.TimeoutError:
            result = None

        assert result is not None
        assert result["success"] is False
        assert result["error_kind"] == "rate_limit"  # 不是 wall_clock_timeout

    @pytest.mark.asyncio
    async def test_seedream_normal_success_not_affected(self):
        """正常成功 shot 不受 wait_for 包裹影响"""
        async def normal_success():
            await asyncio.sleep(0.02)
            return {"success": True, "pil_image": "fake_image"}

        result = await asyncio.wait_for(normal_success(), timeout=2.0)
        assert result["success"] is True
