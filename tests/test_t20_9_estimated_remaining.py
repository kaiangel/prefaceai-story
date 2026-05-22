"""RISK-T20-9 (2026-05-18) — Backend ETA universal accuracy tests

测试 backend `estimated_remaining_seconds` 字段在不同 shot_count / concurrent /
stage / progress 组合下都返回 universal 准确值, 不再 hardcode 18 shots/29 shots。

5 维度 universal 验证:
1. per_shot_seconds 80 (替代旧 60) — 匹配实测 long-tail Seedream
2. 不同 shot count: 5 / 19 / 29 / 50 → image_generation 总秒数动态计算
3. 不同 concurrent: 1 / 3 / 6 → image_generation 串/并行差异
4. 不同 stage + global progress → stage-internal progress 自动转换
5. estimate_remaining + calculate_eta_remaining_sec 两 helper 同步 (双源 baseline 一致)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.pipeline_orchestrator import (
    build_stage_durations,
    estimate_remaining,
)
from app.services.job_manager import (
    calculate_eta_remaining_sec,
    _ETA_STAGE_BASELINES,
)


# ---------------------------------------------------------------------------
# 1. Per-shot seconds calibration (T20-9 核心修复)
# ---------------------------------------------------------------------------

class TestPerShotSecondsCalibration:
    """RISK-T20-9: per_shot_seconds 必须 = 80 (匹配实测 long-tail)"""

    def test_19_shots_3_concurrent_uses_80s_per_shot(self):
        """test18 second run 真实场景: 19 shots × 80 / 3 = 506s ≈ 实测 540s"""
        durations = build_stage_durations(actual_shot_count=19, max_concurrent=3)
        # 19 × 80 / 3 = 506 (int 截断)
        assert durations["image_generation"] == int(19 * 80 / 3), \
            f"19 shots × 80 / 3 = 506, 实际 {durations['image_generation']}"

    def test_29_shots_3_concurrent(self):
        """worst-case 长篇 29 shots"""
        durations = build_stage_durations(actual_shot_count=29, max_concurrent=3)
        assert durations["image_generation"] == int(29 * 80 / 3)

    def test_5_shots_3_concurrent(self):
        """快闪 5 shots — 应有 1 min 最小兜底"""
        durations = build_stage_durations(actual_shot_count=5, max_concurrent=3)
        raw = int(5 * 80 / 3)  # = 133
        assert durations["image_generation"] == max(raw, 60), \
            f"5 shots × 80 / 3 = {raw}s (取 max 60), 实际 {durations['image_generation']}"

    def test_50_shots_3_concurrent_long_form(self):
        """中长篇 50 shots"""
        durations = build_stage_durations(actual_shot_count=50, max_concurrent=3)
        assert durations["image_generation"] == int(50 * 80 / 3)


# ---------------------------------------------------------------------------
# 2. Concurrent scaling
# ---------------------------------------------------------------------------

class TestConcurrentScaling:
    """ETA 必须随 concurrent 数线性减少 — universal"""

    def test_concurrent_1_doubles_time(self):
        d1 = build_stage_durations(actual_shot_count=18, max_concurrent=1)
        d3 = build_stage_durations(actual_shot_count=18, max_concurrent=3)
        # 1 并发 时间 ≈ 3 并发 × 3
        assert d1["image_generation"] == int(18 * 80 / 1), "1 并发应是 18×80=1440s"
        assert d3["image_generation"] == int(18 * 80 / 3), "3 并发应是 18×80/3=480s"

    def test_concurrent_6_halves_3concurrent(self):
        d3 = build_stage_durations(actual_shot_count=18, max_concurrent=3)
        d6 = build_stage_durations(actual_shot_count=18, max_concurrent=6)
        # 6 并发 = 3 并发的一半
        assert d6["image_generation"] == int(18 * 80 / 6)
        assert d3["image_generation"] >= 2 * d6["image_generation"] - 5  # 容许整数截断 5s 误差

    def test_concurrent_zero_safe(self):
        """edge case: max_concurrent=0 不应该 ZeroDivisionError"""
        d = build_stage_durations(actual_shot_count=18, max_concurrent=0)
        # max(max_concurrent, 1) 兜底 → 退化为 1 并发
        assert d["image_generation"] == int(18 * 80 / 1)


# ---------------------------------------------------------------------------
# 3. Stage + global progress 映射
# ---------------------------------------------------------------------------

class TestStageInternalProgressMapping:
    """RISK-T20-9: 真实 progress 映射 stage-internal — 替代 hardcoded 0.5"""

    def test_image_generation_progress_75_is_early_stage(self):
        """global progress=75 在 image_generation [70-92] 范围内 stage_progress=22.7%
        → ETA 应保留大部分 image_generation 时间
        """
        eta = calculate_eta_remaining_sec(
            stage="image_generation",
            progress=75,
            actual_shot_count=19,
            max_concurrent=3,
        )
        # image_generation 总 = int(19*80/3) = 506
        # stage_progress = (75-70)/(92-70) = 0.227
        # remaining_in_stage = 506 × (1-0.227) = 391
        # + bgm 120 = 511
        assert eta is not None
        assert 480 <= eta <= 540, f"expected 480-540s, got {eta}"

    def test_image_generation_progress_90_is_near_end(self):
        """global progress=90 → stage_progress=(90-70)/(92-70)=0.909
        → ETA 应几乎只剩 bgm
        """
        eta = calculate_eta_remaining_sec(
            stage="image_generation",
            progress=90,
            actual_shot_count=19,
            max_concurrent=3,
        )
        # remaining = 506 × (1-0.909) = 46 + 120 = 166
        assert eta is not None
        assert 150 <= eta <= 200, f"expected 150-200s, got {eta}"

    def test_image_generation_progress_70_is_stage_start(self):
        """global progress=70 = image_generation 起点 → stage_progress=0 → 全部时间"""
        eta = calculate_eta_remaining_sec(
            stage="image_generation",
            progress=70,
            actual_shot_count=19,
            max_concurrent=3,
        )
        # 506 + 120 = 626
        assert eta is not None
        assert 600 <= eta <= 650, f"expected 600-650s, got {eta}"

    def test_image_generation_progress_92_stage_end(self):
        """global progress=92 = stage 完成 → 几乎只剩 bgm 120s"""
        eta = calculate_eta_remaining_sec(
            stage="image_generation",
            progress=92,
            actual_shot_count=19,
            max_concurrent=3,
        )
        # remaining_in_stage = 506 × 0 = 0 + bgm 120
        # 但 + 5s 最小兜底; 实测应 ≈ 120-125
        assert eta is not None
        assert 115 <= eta <= 130, f"expected 115-130s, got {eta}"


# ---------------------------------------------------------------------------
# 4. estimate_remaining vs calculate_eta_remaining_sec 同步
# ---------------------------------------------------------------------------

class TestHelperConsistency:
    """两个 ETA helper 在 baseline 上必须同步 (RISK-T20-9 双源修复)"""

    def test_both_helpers_use_same_per_shot_seconds(self):
        """两 helper 必须用 80 s/shot, 不能一个 60 一个 80"""
        # 验证 estimate_remaining 间接走 build_stage_durations
        d_orch = build_stage_durations(actual_shot_count=20, max_concurrent=4)
        expected_image_gen = int(20 * 80 / 4)  # 400
        assert d_orch["image_generation"] == expected_image_gen

        # 验证 calculate_eta_remaining_sec 同公式
        # image_generation 起点 progress=70, stage_progress=0
        # ETA = image_generation 全长 + bgm 全长 = 400 + 120 = 520
        eta_jm = calculate_eta_remaining_sec(
            stage="image_generation",
            progress=70,
            actual_shot_count=20,
            max_concurrent=4,
        )
        assert eta_jm is not None
        # 容许 5s 兜底 + 截断误差
        assert abs(eta_jm - (expected_image_gen + 120)) <= 10, \
            f"helpers desync: orch={expected_image_gen + 120}, jm={eta_jm}"


# ---------------------------------------------------------------------------
# 5. Edge cases / universal robustness
# ---------------------------------------------------------------------------

class TestUniversalRobustness:
    def test_completed_returns_zero(self):
        assert calculate_eta_remaining_sec(stage="completed", progress=100) == 0

    def test_unknown_stage_returns_none(self):
        assert calculate_eta_remaining_sec(stage="bogus_stage", progress=50) is None

    def test_zero_shots_min_60(self):
        """edge case: 0 shots — 不应崩, 走 60s 最小兜底"""
        d = build_stage_durations(actual_shot_count=0, max_concurrent=3)
        assert d["image_generation"] >= 60

    def test_estimate_remaining_image_gen_19_shots(self):
        """estimate_remaining(stage_progress=0.0, 19 shots) 应返 image_gen 全长 + bgm"""
        eta = estimate_remaining(
            current_stage="image_generation",
            stage_progress=0.0,
            actual_shot_count=19,
            max_concurrent=3,
        )
        # int(19*80/3) = 506 + bgm 120 = 626
        assert 620 <= eta <= 635

    def test_estimate_remaining_bgm_stage(self):
        """estimate_remaining bgm stage 不依赖 shot_count"""
        eta = estimate_remaining(
            current_stage="bgm",
            stage_progress=0.0,
            actual_shot_count=999,  # 不影响
            max_concurrent=3,
        )
        # bgm baseline 120
        assert 115 <= eta <= 125
