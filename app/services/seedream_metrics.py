"""
Seedream 生成指标监控模块 (T18-D Wave 11.4)

职责：
  - 追踪每张 shot 的 attempt 次数 / 成功失败 / 耗时
  - 统计 IncompleteRead / TimeoutError 频率
  - 提供 stats() 方法供 admin endpoint 或 log 使用
  - 可选：集成到 ApiCostLogger 一起持久化（无 schema 改动）

设计原则：
  - 纯内存（不依赖 DB），重启清零
  - 线程安全（asyncio + threading.Lock 双保险）
  - 不阻塞 Pipeline（所有操作 O(1)）
  - 与 seedream_generator.py 解耦（通过 import 引用，不反向依赖）

使用方式：
    from app.services.seedream_metrics import seedream_metrics

    # 记录一次 shot 生成完成
    seedream_metrics.record_shot(
        shot_id=3,
        success=True,
        duration_sec=173.4,
        attempt_count=2,         # 含重试次数（IncompleteRead 等）
        error_kind=None,         # 或 "network" / "timeout"
    )

    # 获取当前统计
    stats = seedream_metrics.stats()
    print(stats)
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class _ShotRecord:
    """单次 shot 生成的记录。"""
    shot_id: int | str
    success: bool
    duration_sec: float
    attempt_count: int          # 总 attempt 数（含首次，IncompleteRead 每次算 1 attempt）
    error_kind: Optional[str]   # None 表示成功；"network" / "timeout" / "sensitive_content" 等
    recorded_at: float = field(default_factory=time.time)


class SeedreamMetrics:
    """Seedream 生图监控。

    单例使用（见模块底部 seedream_metrics 全局对象）。

    线程安全说明：
      _lock 保护内部列表和计数器；
      asyncio 环境下 record_shot 是同步调用（O(1) 锁持有时间极短，不影响 event loop）。
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._shots: List[_ShotRecord] = []

        # 快速计数器（O(1)）
        self._total: int = 0
        self._success_count: int = 0
        self._failure_count: int = 0

        # 错误分类计数
        self._error_kind_counts: Dict[str, int] = {}

        # attempt 分布计数（1=首次成功，2=1次重试后成功，…）
        self._attempt_dist: Dict[int, int] = {}

        # IncompleteRead / TimeoutError 发生次数（每次 attempt 级别计数）
        self._incomplete_read_count: int = 0
        self._timeout_error_count: int = 0

        # 耗时聚合（用于计算 P25/P50/P75/P95）
        self._durations: List[float] = []

        # session 开始时间（用于 session 级统计）
        self._session_start: float = time.time()

    # ------------------------------------------------------------------
    # 记录接口
    # ------------------------------------------------------------------

    def record_shot(
        self,
        shot_id: int | str,
        success: bool,
        duration_sec: float,
        attempt_count: int = 1,
        error_kind: Optional[str] = None,
        incomplete_read_attempts: int = 0,
        timeout_attempts: int = 0,
    ) -> None:
        """记录一次 shot 生成结果。

        Args:
            shot_id: shot 编号（来自 storyboard）
            success: 是否最终成功
            duration_sec: 总耗时（秒），含重试等待时间
            attempt_count: 总 attempt 次数（含首次）。
                1 = 首次成功，2 = 1 次重试后成功，4 = 4 次全失败。
            error_kind: 最终失败原因（成功时传 None）。
                可选值：network / timeout / sensitive_content / api_error /
                        empty_response / missing_api_key / seedream_error:xxx
            incomplete_read_attempts: 本 shot 触发 IncompleteRead 的 attempt 次数
            timeout_attempts: 本 shot 触发 TimeoutError 的 attempt 次数
        """
        record = _ShotRecord(
            shot_id=shot_id,
            success=success,
            duration_sec=round(duration_sec, 2),
            attempt_count=attempt_count,
            error_kind=error_kind if not success else None,
        )
        with self._lock:
            self._shots.append(record)
            self._total += 1
            self._durations.append(duration_sec)

            if success:
                self._success_count += 1
            else:
                self._failure_count += 1
                kind = error_kind or "unknown"
                self._error_kind_counts[kind] = self._error_kind_counts.get(kind, 0) + 1

            self._attempt_dist[attempt_count] = self._attempt_dist.get(attempt_count, 0) + 1
            self._incomplete_read_count += incomplete_read_attempts
            self._timeout_error_count += timeout_attempts

    def record_incomplete_read(self, shot_id: int | str, attempt: int) -> None:
        """轻量接口：仅记录一次 IncompleteRead 事件（不需要完整 shot 结果时使用）。

        适合在 seedream_generator.py _call_seedream_sync 的 except 块内调用。
        """
        with self._lock:
            self._incomplete_read_count += 1

    def record_timeout_error(self, shot_id: int | str, attempt: int) -> None:
        """轻量接口：仅记录一次 TimeoutError 事件。"""
        with self._lock:
            self._timeout_error_count += 1

    # ------------------------------------------------------------------
    # 查询接口
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        """返回当前统计快照（供 admin endpoint 或 log 使用）。

        Returns 结构示例:
        {
          "session_duration_sec": 1234.5,
          "total_shots": 29,
          "success_count": 28,
          "failure_count": 1,
          "failure_rate_pct": 3.45,
          "incomplete_read_count": 24,
          "timeout_error_count": 1,
          "latency": {
            "min": 47.0, "p25": 55.0, "p50": 70.0,
            "p75": 110.0, "p95": 160.0, "max": 177.0, "mean": 98.0
          },
          "attempt_distribution": {1: 17, 2: 8, 3: 3, 4: 1},
          "error_breakdown": {"network": 1},
          "longtail_count": 6,         # duration > 120s
          "longtail_pct": 20.69,
        }
        """
        with self._lock:
            total = self._total
            success_count = self._success_count
            failure_count = self._failure_count
            incomplete_read = self._incomplete_read_count
            timeout_err = self._timeout_error_count
            durations = list(self._durations)
            attempt_dist = dict(self._attempt_dist)
            error_kinds = dict(self._error_kind_counts)
            session_elapsed = round(time.time() - self._session_start, 1)

        failure_rate = round(failure_count / total * 100, 2) if total > 0 else 0.0
        latency_stats = _percentiles(durations)

        longtail = [d for d in durations if d > 120.0]
        longtail_pct = round(len(longtail) / len(durations) * 100, 2) if durations else 0.0

        return {
            "session_duration_sec": session_elapsed,
            "total_shots": total,
            "success_count": success_count,
            "failure_count": failure_count,
            "failure_rate_pct": failure_rate,
            "incomplete_read_count": incomplete_read,
            "timeout_error_count": timeout_err,
            "latency": latency_stats,
            "attempt_distribution": attempt_dist,
            "error_breakdown": error_kinds,
            "longtail_count": len(longtail),
            "longtail_pct": longtail_pct,
        }

    def log_summary(self, logger_instance=None) -> None:
        """将当前统计以 INFO 日志形式输出。

        Args:
            logger_instance: Python logging.Logger 实例；
                若为 None，则使用模块默认 logger。
        """
        import logging
        _logger = logger_instance or logging.getLogger("xuhua")

        s = self.stats()
        lat = s.get("latency", {})
        _logger.info(
            f"[SeedreamMetrics] shots={s['total_shots']} "
            f"success={s['success_count']} fail={s['failure_count']} "
            f"fail_rate={s['failure_rate_pct']}% | "
            f"latency p50={lat.get('p50','?')}s p95={lat.get('p95','?')}s max={lat.get('max','?')}s | "
            f"longtail(>120s)={s['longtail_count']} ({s['longtail_pct']}%) | "
            f"IncompleteRead={s['incomplete_read_count']} TimeoutError={s['timeout_error_count']} | "
            f"attempts={s['attempt_distribution']}"
        )

    def reset(self) -> None:
        """重置所有计数（主要用于测试）。"""
        with self._lock:
            self._shots.clear()
            self._total = 0
            self._success_count = 0
            self._failure_count = 0
            self._error_kind_counts.clear()
            self._attempt_dist.clear()
            self._incomplete_read_count = 0
            self._timeout_error_count = 0
            self._durations.clear()
            self._session_start = time.time()


# ------------------------------------------------------------------
# 辅助函数
# ------------------------------------------------------------------

def _percentiles(values: List[float]) -> dict:
    """计算 min / P25 / P50 / P75 / P95 / max / mean。

    空列表返回全 None。
    """
    if not values:
        return {
            "min": None, "p25": None, "p50": None,
            "p75": None, "p95": None, "max": None, "mean": None,
        }
    sorted_vals = sorted(values)
    n = len(sorted_vals)

    def _pct(p: float) -> float:
        idx = (n - 1) * p
        lo = int(idx)
        hi = lo + 1
        if hi >= n:
            return round(sorted_vals[lo], 1)
        frac = idx - lo
        return round(sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac, 1)

    return {
        "min": round(sorted_vals[0], 1),
        "p25": _pct(0.25),
        "p50": _pct(0.50),
        "p75": _pct(0.75),
        "p95": _pct(0.95),
        "max": round(sorted_vals[-1], 1),
        "mean": round(sum(values) / n, 1),
    }


# ------------------------------------------------------------------
# 全局单例
# ------------------------------------------------------------------

#: 全局 Seedream 指标对象。在 Pipeline 内直接 import 使用。
#: 服务重启后自动清零（纯内存）。
seedream_metrics = SeedreamMetrics()
