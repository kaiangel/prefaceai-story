"""RISK-T20-9.v3 (2026-05-19) — Backend ETA 全局重审 (基于真实 shots_total/completed)

Founder 5/19 16:08 反馈核心问题:
  1. test17 v2: progress=84% 但 Shot 14/20 才开始 — 真实 ~70%, ETA 严重失真
  2. 前后端 ETA 脱节, "前端在自说自话"
  3. progress >= 95% 显"即将完成"无具体 ETA — 终态 UX 灾难
  4. Stage 5 + Stage 6 BGM (~3min) + 后处理 (~30s) 必须算入剩余时间

v3 测试维度:
  1. image_generation stage 用真实 shots_completed 替代 progress 反推
  2. bgm stage 按 progress 内折扣 + postprocess baseline
  3. completed stage → 0
  4. 早期 stage (shots_total=None) → 走 legacy, v3 不接管
  5. 单调性 guard: v3 不能比 legacy 大很多
  6. 终态保底: progress >= 95% 仍返 >=5s 数值
  7. Universal: 5/19/29/50 shots × 1/3/6 concurrent → 算法准确
  8. 跨 stage 累积: image_generation 阶段 ETA 含 bgm + postprocess
"""

import sys
import os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.api.chapters import (
    _compute_v3_eta,
    _V3_PER_SHOT_SECONDS,
    _V3_BGM_BASELINE_SECONDS,
    _V3_POSTPROCESS_BASELINE_SECONDS,
    _V3_TERMINAL_PHASE_MIN_ETA,
)


def _mk_job(stage: str, progress: int = 0, estimated_seconds: int | None = None):
    """构造 mock GenerationJob"""
    job = MagicMock()
    job.current_stage = stage
    job.progress = progress
    job.estimated_seconds = estimated_seconds
    return job


# ---------------------------------------------------------------------------
# 1. completed stage → 0
# ---------------------------------------------------------------------------

class TestCompletedStage:
    """completed 终态必须返 0 — Founder 4 P0 要求"""

    def test_completed_returns_zero(self):
        job = _mk_job("completed", progress=100, estimated_seconds=120)
        eta = _compute_v3_eta(job, shots_total=18, shots_completed=18, max_concurrent=3, legacy_eta=120)
        assert eta == 0

    def test_completed_with_no_shots_still_zero(self):
        """completed 即使 shots_total=None 也返 0"""
        job = _mk_job("completed", progress=100)
        eta = _compute_v3_eta(job, shots_total=None, shots_completed=None, max_concurrent=3, legacy_eta=None)
        assert eta == 0


# ---------------------------------------------------------------------------
# 2. 早期 stage (storyboard 没生成) → 不接管, 返 None
# ---------------------------------------------------------------------------

class TestEarlyStageBackoff:
    """shots_total=None 时 v3 不接管, 返 None 让 legacy 继续生效"""

    def test_storyboard_stage_no_shots_total(self):
        """Stage 4 storyboard 跑中, shots_total 还没派生"""
        job = _mk_job("storyboard", progress=45)
        eta = _compute_v3_eta(job, shots_total=None, shots_completed=None, max_concurrent=3, legacy_eta=300)
        assert eta is None, "shots_total=None 应返 None 让 legacy_eta 继续生效"

    def test_screenplay_stage_no_shots_total(self):
        job = _mk_job("screenplay", progress=20)
        eta = _compute_v3_eta(job, shots_total=None, shots_completed=None, max_concurrent=3, legacy_eta=600)
        assert eta is None

    def test_character_design_no_shots_total(self):
        job = _mk_job("character_design", progress=8)
        eta = _compute_v3_eta(job, shots_total=None, shots_completed=None, max_concurrent=3, legacy_eta=800)
        assert eta is None

    def test_story_generation_no_shots_total(self):
        job = _mk_job("story_generation", progress=3)
        eta = _compute_v3_eta(job, shots_total=None, shots_completed=None, max_concurrent=3, legacy_eta=1200)
        assert eta is None


# ---------------------------------------------------------------------------
# 3. image_generation: 真实 shots_completed 取代 progress 反推
# ---------------------------------------------------------------------------

class TestImageGenerationRealData:
    """v3 image_generation 用真实 shots 计算 — Founder #1 核心修复"""

    def test_19_shots_0_completed_full_remaining(self):
        """test17 v2 场景: 刚进 image_generation, 19 shots 全剩"""
        job = _mk_job("image_generation", progress=75)
        eta = _compute_v3_eta(job, shots_total=19, shots_completed=0, max_concurrent=3, legacy_eta=600)
        # 19 * 80 / 3 = 506 + 120 (bgm) + 30 (postprocess) = 656
        expected = int(19 * 80 / 3) + 120 + 30
        assert eta == expected, f"19 shots all remaining: expected {expected}, got {eta}"

    def test_19_shots_13_completed_real_remaining(self):
        """test17 v2 实测 problem: progress 显示 84% 但实际只 13/19 完成
        legacy_eta 基于 progress 算出已经偏小, v3 信真实数据
        """
        job = _mk_job("image_generation", progress=84)
        # 真实剩余 6 shots
        eta = _compute_v3_eta(job, shots_total=19, shots_completed=13, max_concurrent=3, legacy_eta=100)
        expected = int(6 * 80 / 3) + 120 + 30  # = 160 + 150 = 310
        assert eta == expected, f"6 remaining: expected {expected}, got {eta}"

    def test_19_shots_18_completed_almost_done(self):
        """终态: 18/19 完成 — Founder 4 要求 progress>=95% 仍显具体 ETA"""
        job = _mk_job("image_generation", progress=94)
        eta = _compute_v3_eta(job, shots_total=19, shots_completed=18, max_concurrent=3, legacy_eta=50)
        # 1 * 80 / 3 = 26 + 120 + 30 = 176
        expected = int(1 * 80 / 3) + 120 + 30
        assert eta == expected
        # 不被 legacy_eta=50 压小 — v3 信真实剩余
        assert eta >= _V3_TERMINAL_PHASE_MIN_ETA

    def test_19_shots_19_completed_image_gen_done_bgm_starting(self):
        """所有 shots 完成但 stage 仍在 image_generation (尚未切到 bgm)"""
        job = _mk_job("image_generation", progress=95)
        eta = _compute_v3_eta(job, shots_total=19, shots_completed=19, max_concurrent=3, legacy_eta=150)
        # 0 shots remaining + 120 bgm + 30 postprocess = 150
        expected = 0 + 120 + 30
        assert eta == expected
        assert eta >= _V3_TERMINAL_PHASE_MIN_ETA


# ---------------------------------------------------------------------------
# 4. v3 接管: 真实数据完全替代 legacy (Founder 反馈核心修复)
# ---------------------------------------------------------------------------

class TestV3TakesOverLegacy:
    """Founder 5/19 16:08 反馈: legacy progress-based ETA "偏快".
    v3 真实 shots 数据必须接管, 不再受 legacy 上限约束 (这正是 Founder 痛点).
    """

    def test_v3_much_larger_than_legacy_use_v3_real_data(self):
        """Founder 痛点: legacy 显示 100s (progress-based 错算) 但真实剩 19 shots
        v3 算 19 * 80 / 1 + 150 = 1670 — 必须接管, 不被 legacy=100 压回
        """
        job = _mk_job("image_generation", progress=75)
        eta = _compute_v3_eta(job, shots_total=19, shots_completed=0, max_concurrent=1, legacy_eta=100)
        expected = int(19 * 80 / 1) + 120 + 30  # 1670
        assert eta == expected, f"v3 真实数据应接管, 不被 legacy 压回: expected {expected}, got {eta}"

    def test_v3_less_than_legacy_use_v3(self):
        """v3 比 legacy 小 (真实数据更准) — 信 v3"""
        job = _mk_job("image_generation", progress=90)
        eta = _compute_v3_eta(job, shots_total=19, shots_completed=17, max_concurrent=3, legacy_eta=400)
        expected = int(2 * 80 / 3) + 120 + 30
        assert eta == expected

    def test_v3_with_no_legacy_uses_v3_direct(self):
        """legacy_eta=None 时 v3 直接生效"""
        job = _mk_job("image_generation", progress=80)
        eta = _compute_v3_eta(job, shots_total=19, shots_completed=10, max_concurrent=3, legacy_eta=None)
        expected = int(9 * 80 / 3) + 120 + 30
        assert eta == expected


# ---------------------------------------------------------------------------
# 5. bgm stage: 按 progress 内折扣
# ---------------------------------------------------------------------------

class TestBgmStage:
    """bgm stage v3 按 progress (92-100) 内折扣"""

    def test_bgm_just_started_progress_92(self):
        """bgm 刚进, progress=92 → 全 baseline + postprocess"""
        job = _mk_job("bgm", progress=92)
        eta = _compute_v3_eta(job, shots_total=19, shots_completed=19, max_concurrent=3, legacy_eta=200)
        # bgm 全部 120 + postprocess 30 = 150
        expected = _V3_BGM_BASELINE_SECONDS + _V3_POSTPROCESS_BASELINE_SECONDS
        assert eta == expected

    def test_bgm_half_done_progress_96(self):
        """bgm 中间, progress=96 → 一半 baseline + postprocess"""
        job = _mk_job("bgm", progress=96)
        eta = _compute_v3_eta(job, shots_total=19, shots_completed=19, max_concurrent=3, legacy_eta=100)
        # frac = (96-92)/8 = 0.5, bgm remaining = 60, + 30 = 90
        expected = int(_V3_BGM_BASELINE_SECONDS * 0.5) + _V3_POSTPROCESS_BASELINE_SECONDS
        assert eta == expected

    def test_bgm_almost_done_progress_99(self):
        """bgm 快完成, progress=99"""
        job = _mk_job("bgm", progress=99)
        eta = _compute_v3_eta(job, shots_total=19, shots_completed=19, max_concurrent=3, legacy_eta=50)
        # frac = (99-92)/8 = 0.875, bgm remaining = 15, + 30 = 45
        frac = (99 - 92) / 8.0
        expected = int(_V3_BGM_BASELINE_SECONDS * (1 - frac)) + _V3_POSTPROCESS_BASELINE_SECONDS
        assert eta == expected
        assert eta >= _V3_TERMINAL_PHASE_MIN_ETA


# ---------------------------------------------------------------------------
# 6. image_preparation stage: 保底全 image_gen + bgm + postprocess
# ---------------------------------------------------------------------------

class TestImagePreparationStage:
    """image_preparation 保底不低于 v3_min (避免低估)"""

    def test_image_prep_v3_baseline(self):
        """image_preparation 阶段, legacy=None, 应给完整 image_gen + bgm + postprocess"""
        job = _mk_job("image_preparation", progress=67)
        eta = _compute_v3_eta(job, shots_total=19, shots_completed=0, max_concurrent=3, legacy_eta=None)
        v3_min = int(19 * 80 / 3) + 120 + 30
        assert eta == v3_min

    def test_image_prep_legacy_larger_keeps_legacy(self):
        """image_preparation legacy 已含 prep 剩余 + 后续 stage — 信 legacy"""
        job = _mk_job("image_preparation", progress=67)
        large_legacy = 1000
        eta = _compute_v3_eta(job, shots_total=19, shots_completed=0, max_concurrent=3, legacy_eta=large_legacy)
        # legacy > v3_min, 信 legacy
        assert eta == large_legacy


# ---------------------------------------------------------------------------
# 7. Universal: 不同 shot count × concurrent
# ---------------------------------------------------------------------------

class TestUniversalShotCountConcurrent:
    """v3 算法 universal — 任何 shot count / concurrent 都准确"""

    def test_5_shots_3_concurrent(self):
        """快闪 5 shots, 0 completed"""
        job = _mk_job("image_generation", progress=75)
        eta = _compute_v3_eta(job, shots_total=5, shots_completed=0, max_concurrent=3, legacy_eta=200)
        expected = int(5 * 80 / 3) + 120 + 30
        # 5 shots * 80 / 3 = 133, +150 = 283 — 但 legacy=200, 200*1.5=300, 283<300, 信 v3
        assert eta == expected

    def test_29_shots_3_concurrent(self):
        """长篇 29 shots, 10 completed"""
        job = _mk_job("image_generation", progress=80)
        eta = _compute_v3_eta(job, shots_total=29, shots_completed=10, max_concurrent=3, legacy_eta=None)
        expected = int(19 * 80 / 3) + 120 + 30
        assert eta == expected

    def test_50_shots_6_concurrent(self):
        """中长篇 50 shots, 20 completed, 高并发"""
        job = _mk_job("image_generation", progress=82)
        eta = _compute_v3_eta(job, shots_total=50, shots_completed=20, max_concurrent=6, legacy_eta=None)
        expected = int(30 * 80 / 6) + 120 + 30
        assert eta == expected

    def test_19_shots_1_concurrent_low_priority(self):
        """单并发场景"""
        job = _mk_job("image_generation", progress=75)
        eta = _compute_v3_eta(job, shots_total=19, shots_completed=0, max_concurrent=1, legacy_eta=None)
        expected = int(19 * 80 / 1) + 120 + 30
        assert eta == expected


# ---------------------------------------------------------------------------
# 8. 跨 stage 累积验证
# ---------------------------------------------------------------------------

class TestCrossStageAccumulation:
    """v3 image_generation ETA 必须含 bgm + postprocess (Founder #4 要求)"""

    def test_image_gen_eta_includes_bgm_and_postprocess(self):
        """正进 image_gen 阶段, ETA 必须 ≥ 0 image_gen + bgm + postprocess"""
        job = _mk_job("image_generation", progress=75)
        eta = _compute_v3_eta(job, shots_total=19, shots_completed=19, max_concurrent=3, legacy_eta=None)
        # 0 image_gen + bgm + postprocess = 150
        assert eta >= _V3_BGM_BASELINE_SECONDS + _V3_POSTPROCESS_BASELINE_SECONDS
        assert eta == _V3_BGM_BASELINE_SECONDS + _V3_POSTPROCESS_BASELINE_SECONDS

    def test_image_gen_partial_completed_includes_remaining_plus_tail(self):
        """部分完成 image_gen, ETA = 剩余 shot + bgm + postprocess"""
        job = _mk_job("image_generation", progress=78)
        eta = _compute_v3_eta(job, shots_total=20, shots_completed=5, max_concurrent=3, legacy_eta=None)
        remaining_image = int(15 * 80 / 3)
        expected = remaining_image + _V3_BGM_BASELINE_SECONDS + _V3_POSTPROCESS_BASELINE_SECONDS
        assert eta == expected


# ---------------------------------------------------------------------------
# 9. 终态保底: progress >= 95% 仍显具体 ETA
# ---------------------------------------------------------------------------

class TestTerminalPhaseMinETA:
    """Founder #3: progress >= 95% 不能显 0 / 即将完成 — 仍要具体数字"""

    def test_image_gen_near_done_min_eta(self):
        """所有 shot 完成但还在 image_generation, ETA >= MIN"""
        job = _mk_job("image_generation", progress=95)
        eta = _compute_v3_eta(job, shots_total=19, shots_completed=19, max_concurrent=3, legacy_eta=None)
        assert eta is not None and eta >= _V3_TERMINAL_PHASE_MIN_ETA

    def test_bgm_almost_done_min_eta(self):
        """bgm 99%, ETA >= MIN"""
        job = _mk_job("bgm", progress=99)
        eta = _compute_v3_eta(job, shots_total=19, shots_completed=19, max_concurrent=3, legacy_eta=None)
        assert eta is not None and eta >= _V3_TERMINAL_PHASE_MIN_ETA


# ---------------------------------------------------------------------------
# 10. Edge cases & robustness
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """边缘情况: shots_completed > shots_total, shots_total=0, concurrent=0"""

    def test_shots_completed_exceeds_total_clamped(self):
        """shots_completed > shots_total 时应 clamp 到 total (T20-13 派生兜底已做, 这里防御)"""
        job = _mk_job("image_generation", progress=95)
        eta = _compute_v3_eta(job, shots_total=19, shots_completed=25, max_concurrent=3, legacy_eta=None)
        # clamp 到 19, remaining=0, ETA = 0 + 120 + 30 = 150
        expected = 0 + 120 + 30
        assert eta == expected

    def test_shots_total_zero_treats_as_none(self):
        """shots_total=0 边缘情况 — 当成 None (v3 不接管)"""
        job = _mk_job("image_generation", progress=75)
        eta = _compute_v3_eta(job, shots_total=0, shots_completed=0, max_concurrent=3, legacy_eta=200)
        assert eta is None, "shots_total=0 应返 None"

    def test_job_none_returns_none(self):
        """job=None 时返 None (chapters.py 入口已防 None job 但 defense)"""
        eta = _compute_v3_eta(job=None, shots_total=19, shots_completed=5, max_concurrent=3, legacy_eta=100)
        assert eta is None

    def test_unknown_stage_returns_none(self):
        """未知 stage (e.g. legacy 老数据) → 不接管, 返 None"""
        job = _mk_job("legacy_unknown_stage", progress=50)
        eta = _compute_v3_eta(job, shots_total=19, shots_completed=5, max_concurrent=3, legacy_eta=300)
        assert eta is None


# ---------------------------------------------------------------------------
# 11. 实测场景: test17 v2 "84% 但 Shot 14/20 才开始" Founder 反馈
# ---------------------------------------------------------------------------

class TestRealWorldTest17V2Scenario:
    """Founder 5/19 16:08 反馈 test17 v2 真实数据"""

    def test_progress_84_shots_14_of_20_real_eta(self):
        """实测: progress=84%, shots_completed=14, shots_total=20
        legacy 算的是 progress 反推 (75 + 20 * X / 20 → X = 9), 错算成 9 shots done
        v3 信真实 14 shots done → 剩 6 shots — v3 必须接管
        """
        job = _mk_job("image_generation", progress=84, estimated_seconds=200)
        eta = _compute_v3_eta(job, shots_total=20, shots_completed=14, max_concurrent=3, legacy_eta=200)
        # v3 用真实数据: 6 shots * 80 / 3 = 160 + 120 + 30 = 310
        # legacy 偏小 (200), v3 真实数据 (310) 必须接管 — 这正是 Founder 反馈核心修复
        expected = int(6 * 80 / 3) + 120 + 30
        assert eta == expected, f"v3 真实 6 shots remaining 应接管 (Founder #1 痛点): expected {expected}, got {eta}"

    def test_progress_84_shots_14_of_20_with_large_legacy(self):
        """同上但 legacy 更大 (progress 过估), v3 接管"""
        job = _mk_job("image_generation", progress=84, estimated_seconds=500)
        eta = _compute_v3_eta(job, shots_total=20, shots_completed=14, max_concurrent=3, legacy_eta=500)
        expected = int(6 * 80 / 3) + 120 + 30
        assert eta == expected, "legacy 过大时, v3 真实数据接管"
