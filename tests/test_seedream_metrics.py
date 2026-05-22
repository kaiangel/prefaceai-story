"""
单元测试：app/services/seedream_metrics.py

覆盖范围：
  - 基础计数（success / failure / total）
  - 失败率计算
  - IncompleteRead / TimeoutError 计数
  - attempt 分布
  - 耗时分位数（P25/P50/P75/P95）
  - 长尾检测（>120s）
  - 错误分类统计
  - log_summary 不抛异常
  - reset 清零
  - 线程安全基本验证
  - 轻量接口（record_incomplete_read / record_timeout_error）
"""

import threading

import pytest

from app.services.seedream_metrics import SeedreamMetrics, _percentiles, seedream_metrics


# ---------------------------------------------------------------------------
# _percentiles 辅助函数
# ---------------------------------------------------------------------------

class TestPercentiles:
    def test_empty_returns_none(self):
        p = _percentiles([])
        assert p["min"] is None
        assert p["p50"] is None
        assert p["max"] is None

    def test_single_value(self):
        p = _percentiles([100.0])
        assert p["min"] == 100.0
        assert p["p50"] == 100.0
        assert p["max"] == 100.0
        assert p["mean"] == 100.0

    def test_known_distribution(self):
        # 10 values: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100
        vals = [float(i * 10) for i in range(1, 11)]
        p = _percentiles(vals)
        assert p["min"] == 10.0
        assert p["max"] == 100.0
        assert p["mean"] == 55.0
        # P50: median of 10 values = (50+60)/2 = 55
        assert p["p50"] == 55.0

    def test_all_same(self):
        vals = [70.0] * 5
        p = _percentiles(vals)
        assert p["min"] == 70.0
        assert p["p50"] == 70.0
        assert p["max"] == 70.0


# ---------------------------------------------------------------------------
# SeedreamMetrics 基础功能
# ---------------------------------------------------------------------------

class TestBasicCounting:
    def setup_method(self):
        self.m = SeedreamMetrics()

    def test_initial_state(self):
        s = self.m.stats()
        assert s["total_shots"] == 0
        assert s["success_count"] == 0
        assert s["failure_count"] == 0
        assert s["failure_rate_pct"] == 0.0

    def test_record_one_success(self):
        self.m.record_shot(shot_id=1, success=True, duration_sec=70.0)
        s = self.m.stats()
        assert s["total_shots"] == 1
        assert s["success_count"] == 1
        assert s["failure_count"] == 0
        assert s["failure_rate_pct"] == 0.0

    def test_record_one_failure(self):
        self.m.record_shot(shot_id=8, success=False, duration_sec=760.0, error_kind="timeout")
        s = self.m.stats()
        assert s["total_shots"] == 1
        assert s["failure_count"] == 1
        assert s["failure_rate_pct"] == 100.0
        assert s["error_breakdown"]["timeout"] == 1

    def test_mixed_success_failure(self):
        for i in range(28):
            self.m.record_shot(shot_id=i + 1, success=True, duration_sec=70.0)
        self.m.record_shot(shot_id=29, success=False, duration_sec=760.0, error_kind="network")
        s = self.m.stats()
        assert s["total_shots"] == 29
        assert s["success_count"] == 28
        assert s["failure_count"] == 1
        assert abs(s["failure_rate_pct"] - 3.45) < 0.1  # ~3.4%


class TestErrorKindCounting:
    def setup_method(self):
        self.m = SeedreamMetrics()

    def test_multiple_error_kinds(self):
        self.m.record_shot(1, False, 180.0, error_kind="timeout")
        self.m.record_shot(2, False, 180.0, error_kind="timeout")
        self.m.record_shot(3, False, 90.0, error_kind="network")
        s = self.m.stats()
        assert s["error_breakdown"]["timeout"] == 2
        assert s["error_breakdown"]["network"] == 1

    def test_success_does_not_count_error_kind(self):
        self.m.record_shot(1, True, 70.0, error_kind="timeout")  # error_kind should be ignored on success
        s = self.m.stats()
        assert s["error_breakdown"] == {}

    def test_unknown_error_kind(self):
        self.m.record_shot(1, False, 90.0)  # no error_kind
        s = self.m.stats()
        assert "unknown" in s["error_breakdown"]


class TestAttemptDistribution:
    def setup_method(self):
        self.m = SeedreamMetrics()

    def test_attempt_1_success(self):
        self.m.record_shot(1, True, 60.0, attempt_count=1)
        s = self.m.stats()
        assert s["attempt_distribution"][1] == 1

    def test_attempt_4_failure(self):
        self.m.record_shot(8, False, 760.0, attempt_count=4, error_kind="timeout")
        s = self.m.stats()
        assert s["attempt_distribution"][4] == 1

    def test_mixed_attempts(self):
        self.m.record_shot(1, True, 60.0, attempt_count=1)
        self.m.record_shot(2, True, 90.0, attempt_count=2)
        self.m.record_shot(3, True, 95.0, attempt_count=2)
        self.m.record_shot(8, False, 760.0, attempt_count=4)
        s = self.m.stats()
        assert s["attempt_distribution"][1] == 1
        assert s["attempt_distribution"][2] == 2
        assert s["attempt_distribution"][4] == 1


class TestIncompleteReadTimeout:
    def setup_method(self):
        self.m = SeedreamMetrics()

    def test_incomplete_read_via_record_shot(self):
        self.m.record_shot(1, True, 70.0, attempt_count=2, incomplete_read_attempts=1)
        s = self.m.stats()
        assert s["incomplete_read_count"] == 1
        assert s["timeout_error_count"] == 0

    def test_timeout_via_record_shot(self):
        self.m.record_shot(8, False, 760.0, attempt_count=4, timeout_attempts=4)
        s = self.m.stats()
        assert s["timeout_error_count"] == 4

    def test_lightweight_incomplete_read(self):
        self.m.record_incomplete_read(shot_id=1, attempt=1)
        self.m.record_incomplete_read(shot_id=1, attempt=2)
        s = self.m.stats()
        assert s["incomplete_read_count"] == 2

    def test_lightweight_timeout_error(self):
        self.m.record_timeout_error(shot_id=8, attempt=4)
        s = self.m.stats()
        assert s["timeout_error_count"] == 1

    def test_combined_counts(self):
        # 模拟 test18: 24 IncompleteRead + 1 TimeoutError (4 attempts)
        for i in range(24):
            self.m.record_incomplete_read(shot_id=i // 3 + 1, attempt=(i % 3) + 1)
        self.m.record_timeout_error(shot_id=8, attempt=4)
        self.m.record_timeout_error(shot_id=8, attempt=4)
        self.m.record_timeout_error(shot_id=8, attempt=4)
        self.m.record_timeout_error(shot_id=8, attempt=4)
        s = self.m.stats()
        assert s["incomplete_read_count"] == 24
        assert s["timeout_error_count"] == 4


class TestLatencyStats:
    def setup_method(self):
        self.m = SeedreamMetrics()

    def test_longtail_detection(self):
        # 6 long-tail shots > 120s, rest < 80s
        for i in range(23):
            self.m.record_shot(i + 1, True, 70.0)
        for duration in [107.0, 148.0, 159.0, 161.0, 173.0, 177.0]:
            self.m.record_shot(99, True, duration)
        s = self.m.stats()
        # >120s: 148, 159, 161, 173, 177 = 5 shots (107 < 120)
        assert s["longtail_count"] == 5
        assert s["total_shots"] == 29

    def test_latency_percentiles_empty(self):
        s = self.m.stats()
        assert s["latency"]["p50"] is None

    def test_latency_mean_simple(self):
        self.m.record_shot(1, True, 100.0)
        self.m.record_shot(2, True, 200.0)
        s = self.m.stats()
        assert s["latency"]["mean"] == 150.0

    def test_latency_min_max(self):
        self.m.record_shot(1, True, 47.0)
        self.m.record_shot(2, True, 177.0)
        s = self.m.stats()
        assert s["latency"]["min"] == 47.0
        assert s["latency"]["max"] == 177.0


class TestReset:
    def setup_method(self):
        self.m = SeedreamMetrics()

    def test_reset_clears_all(self):
        self.m.record_shot(1, True, 70.0, attempt_count=2, incomplete_read_attempts=1)
        self.m.record_shot(2, False, 180.0, error_kind="timeout", timeout_attempts=1)
        self.m.reset()
        s = self.m.stats()
        assert s["total_shots"] == 0
        assert s["success_count"] == 0
        assert s["failure_count"] == 0
        assert s["incomplete_read_count"] == 0
        assert s["timeout_error_count"] == 0
        assert s["attempt_distribution"] == {}
        assert s["error_breakdown"] == {}


class TestLogSummary:
    def setup_method(self):
        self.m = SeedreamMetrics()

    def test_log_summary_no_exception_empty(self):
        # 空数据不抛异常
        self.m.log_summary()

    def test_log_summary_no_exception_with_data(self):
        self.m.record_shot(1, True, 70.0, attempt_count=1)
        self.m.record_shot(2, False, 180.0, error_kind="timeout")
        self.m.log_summary()

    def test_log_summary_custom_logger(self):
        import logging
        custom_logger = logging.getLogger("test_custom")
        self.m.record_shot(1, True, 55.0)
        self.m.log_summary(logger_instance=custom_logger)


class TestGlobalSingleton:
    def test_global_singleton_exists(self):
        assert seedream_metrics is not None
        assert isinstance(seedream_metrics, SeedreamMetrics)

    def test_global_singleton_is_same_object(self):
        from app.services.seedream_metrics import seedream_metrics as sm2
        assert seedream_metrics is sm2


class TestThreadSafety:
    def test_concurrent_record_shots(self):
        m = SeedreamMetrics()
        errors = []

        def _worker(shot_id: int):
            try:
                m.record_shot(shot_id=shot_id, success=(shot_id % 5 != 0), duration_sec=70.0 + shot_id)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=_worker, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread safety violation: {errors}"
        s = m.stats()
        assert s["total_shots"] == 50
