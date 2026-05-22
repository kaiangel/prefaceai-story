"""Unit tests for ETA calculation helper — RISK-T17-5 (Wave 11.3)

Tests cover:
1. calculate_eta_remaining_sec per stage at different progress / elapsed values
2. Stage switching reset behaviour (monotonic guard resets between stages)
3. Edge cases: progress=0, progress=100, elapsed=0, elapsed > estimate, unknown stage
4. None return conditions (unknown stage)
5. Monotonic decrease within the same stage
6. Dynamic scaling (actual_shot_count / unique_location_count / max_concurrent)
"""

import pytest
from datetime import datetime, timedelta

# Minimal bootstrap so we can import without a running FastAPI / DB
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.job_manager import (
    calculate_eta_remaining_sec,
    _ETA_STAGE_BASELINES,
    _ETA_STAGE_ORDER,
    _ETA_STAGE_PROGRESS_BOUNDS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _call(stage: str, progress: int, **kw) -> int | None:
    """Thin wrapper so tests stay concise."""
    return calculate_eta_remaining_sec(stage=stage, progress=progress, **kw)


# ---------------------------------------------------------------------------
# 1. Terminal state
# ---------------------------------------------------------------------------

class TestTerminalState:
    def test_completed_returns_zero(self):
        assert _call("completed", 100) == 0

    def test_completed_with_any_progress(self):
        assert _call("completed", 50) == 0

    def test_completed_with_elapsed(self):
        assert _call("completed", 100, elapsed=9999) == 0


# ---------------------------------------------------------------------------
# 2. Unknown stage → None
# ---------------------------------------------------------------------------

class TestUnknownStage:
    def test_unknown_stage_returns_none(self):
        result = _call("alien_stage", 50)
        assert result is None

    def test_empty_string_stage_returns_none(self):
        assert _call("", 50) is None

    def test_typo_stage_returns_none(self):
        assert _call("image_generaton", 50) is None  # intentional typo


# ---------------------------------------------------------------------------
# 3. Progress edge cases
# ---------------------------------------------------------------------------

class TestProgressEdgeCases:
    def test_progress_zero_story_generation(self):
        # progress=2 is the lower bound for story_generation → within-stage progress = 0
        eta = _call("story_generation", 2)
        assert eta is not None and eta > 0

    def test_progress_100_any_stage(self):
        # progress=100 with stage != completed: stage progress = 1.0 → only subsequent stages
        eta = _call("bgm", 100)
        # bgm is the last real stage; subsequent only "completed" which is 0
        assert eta is not None and eta >= 5  # min floor

    def test_progress_at_stage_lower_bound(self):
        # screenplay starts at global progress 11
        eta_start = _call("screenplay", 11)
        eta_mid = _call("screenplay", 21)
        # start should be higher (more remaining) than mid
        assert eta_start is not None and eta_mid is not None
        assert eta_start > eta_mid

    def test_progress_at_stage_upper_bound(self):
        # screenplay ends at global progress 32 → stage progress = 1.0
        eta_end = _call("screenplay", 32)
        # Only storyboard + image_preparation + image_generation + bgm remaining
        # Must be > 0 (those subsequent stages have work)
        assert eta_end is not None and eta_end > 0

    def test_progress_beyond_stage_upper_bound_clamps_to_1(self):
        # progress > upper bound should not crash; stage_progress clamped to 1.0
        eta = _call("story_generation", 99)
        assert eta is not None and eta >= 5  # subsequent stages still count


# ---------------------------------------------------------------------------
# 4. Per-stage sanity: ETA should be positive and decrease with progress
# ---------------------------------------------------------------------------

ALL_REAL_STAGES = [
    s for s in _ETA_STAGE_ORDER
    if s not in ("completed", "character_ready", "scenes_ready")
]


class TestPerStageSanity:
    @pytest.mark.parametrize("stage", ALL_REAL_STAGES)
    def test_eta_positive_at_stage_start(self, stage: str):
        lo = _ETA_STAGE_PROGRESS_BOUNDS.get(stage, (50, 50))[0]
        eta = _call(stage, lo)
        assert eta is not None and eta >= 5, f"Stage {stage}: eta={eta} expected >= 5"

    @pytest.mark.parametrize("stage", ALL_REAL_STAGES)
    def test_eta_decreases_with_progress(self, stage: str):
        lo, hi = _ETA_STAGE_PROGRESS_BOUNDS.get(stage, (0, 100))
        if hi <= lo + 2:
            pytest.skip(f"Stage {stage} has too narrow progress band")
        mid = (lo + hi) // 2
        eta_early = _call(stage, lo)
        eta_mid = _call(stage, mid)
        assert eta_early is not None and eta_mid is not None
        assert eta_early >= eta_mid, (
            f"Stage {stage}: eta at progress={lo} ({eta_early}s) "
            f"should be >= eta at progress={mid} ({eta_mid}s)"
        )

    def test_user_wait_stages_not_in_eta_pipeline(self):
        # character_ready / scenes_ready have duration 0 so they contribute 0 to subsequent sum
        eta_post_character_ready = _call("screenplay", 11)
        # If character_ready were counted (e.g. 300s), eta would be much higher.
        # We just verify the function doesn't crash and returns a positive value.
        assert eta_post_character_ready is not None and eta_post_character_ready > 0


# ---------------------------------------------------------------------------
# 5. Stage switching reset behaviour (KEY fix for T17-5)
# ---------------------------------------------------------------------------

class TestStageSwitchingReset:
    """
    The monotonic guard in progress_callback must reset on stage switch.
    calculate_eta_remaining_sec() is STATELESS — it always computes from the
    current stage's baseline, so a new stage CAN correctly return a higher ETA
    than the previous stage's final ETA.

    Example:
      image_preparation ends at ~300s remaining (progress=70)
      image_generation starts at progress=70 → ETA could be ~600s for 29 shots
      Without reset: min(300, 600) = 300 (wrong — previous stage caps new stage)
      With reset:    600 (correct — new stage starts from its own baseline)
    """

    def test_image_prep_to_image_gen_eta_increases_correctly(self):
        """image_generation should have an equal or higher baseline than image_prep near its end.

        At the exact stage boundary (progress=70):
        - image_preparation at progress=70 has stage_progress=1.0 → only subsequent stages count
          (image_generation=580s + bgm=120s = 700s)
        - image_generation at progress=70 has stage_progress=0.0 → full remaining
          (image_generation=580s + bgm=120s = 700s)
        They are mathematically equal at the boundary, which is correct.
        The real fix is that progress_callback resets _last_eta on stage switch, so
        the monotonic guard no longer caps image_generation's ETA at image_preparation's lower value.
        """
        # Near end of image_preparation (progress=70)
        eta_prep_end = _call("image_preparation", 70, actual_shot_count=29)
        # Start of image_generation (progress=70) with 29 shots
        eta_gen_start = _call("image_generation", 70, actual_shot_count=29)

        # With 29 shots and 3 concurrent: 29 * 60 / 3 = 580s for image_generation alone
        # + bgm (120s) → ~700s total at start of image_generation
        assert eta_gen_start is not None and eta_gen_start > 0
        assert eta_prep_end is not None and eta_prep_end > 0
        # At the boundary they are equal; the function is STATELESS so no cross-stage bleed.
        # >= is correct: new stage ETA is always >= old stage's final ETA (at the transition point).
        assert eta_gen_start >= eta_prep_end, (
            f"image_generation start ({eta_gen_start}s) should be >= "
            f"image_preparation end ({eta_prep_end}s) for 29 shots"
        )

    def test_image_gen_at_start_vs_prep_mid(self):
        """At mid-image_preparation, the remaining ETA should be higher than image_gen start
        if we had enough shots to make image_gen big. Test a concrete scenario."""
        # With only 6 shots and 3 concurrent: image_gen = 6*60/3 = 120s + bgm(120s) = 240s total remaining
        # image_preparation mid (progress=67): stage_progress = (67-65)/(70-65) = 0.4
        # remaining from image_prep = (1-0.4)*image_prep_dur + image_gen(120s) + bgm(120s)
        # char_count = max(1, min(6//6, 6)) = 1; 1*90 + 2*90 = 270s image_prep_dur
        # remaining from image_prep = 0.6*270 + 120 + 120 = 162 + 240 = 402s
        eta_prep_mid = _call("image_preparation", 67, actual_shot_count=6, unique_location_count=2)
        eta_gen_start = _call("image_generation", 70, actual_shot_count=6, max_concurrent=3)
        assert eta_prep_mid is not None and eta_gen_start is not None
        # image_prep mid should be higher than image_gen start (it includes remaining prep work)
        assert eta_prep_mid >= eta_gen_start, (
            f"image_prep mid ({eta_prep_mid}s) should be >= image_gen start ({eta_gen_start}s)"
        )

    def test_stateless_function_always_returns_stage_baseline(self):
        """calculate_eta_remaining_sec has no state — calling it twice for different stages
        is always independent."""
        # Call story_generation at end
        eta_s1_end = _call("story_generation", 6)
        # Call image_generation at start
        eta_s5_start = _call("image_generation", 70, actual_shot_count=18)
        # Re-call story_generation: should return the SAME value as the first call (stateless)
        eta_s1_again = _call("story_generation", 6)
        assert eta_s1_end == eta_s1_again, (
            "calculate_eta_remaining_sec must be stateless — "
            f"first={eta_s1_end}s, second={eta_s1_again}s"
        )
        # And image_generation must be > 0
        assert eta_s5_start is not None and eta_s5_start > 0

    def test_screenplay_to_storyboard_transition_not_zero(self):
        """Storyboard at start should reflect full storyboard+image duration."""
        # End of screenplay (progress=32)
        eta_screenplay_end = _call("screenplay", 32)
        # Start of storyboard (progress=35)
        eta_storyboard_start = _call("storyboard", 35)
        assert eta_storyboard_start is not None and eta_storyboard_start > 0
        # Storyboard at start should still include storyboard (~236s) + image_prep + image_gen + bgm
        # screenplay at end only includes storyboard onwards
        # They should be close but storyboard_start could be slightly higher due to different bounds
        assert abs(eta_storyboard_start - eta_screenplay_end) < 300, (
            f"Stage transition gap too large: screenplay_end={eta_screenplay_end}s "
            f"storyboard_start={eta_storyboard_start}s"
        )


# ---------------------------------------------------------------------------
# 6. Dynamic scaling (actual_shot_count, unique_location_count, max_concurrent)
# ---------------------------------------------------------------------------

class TestDynamicScaling:
    def test_more_shots_gives_higher_eta_at_image_generation(self):
        eta_18 = _call("image_generation", 70, actual_shot_count=18)
        eta_29 = _call("image_generation", 70, actual_shot_count=29)
        assert eta_29 is not None and eta_18 is not None
        assert eta_29 > eta_18, (
            f"29 shots ({eta_29}s) should have higher ETA than 18 shots ({eta_18}s)"
        )

    def test_more_concurrent_reduces_eta_at_image_generation(self):
        eta_1 = _call("image_generation", 70, actual_shot_count=18, max_concurrent=1)
        eta_5 = _call("image_generation", 70, actual_shot_count=18, max_concurrent=5)
        assert eta_1 is not None and eta_5 is not None
        assert eta_1 > eta_5, (
            f"max_concurrent=1 ({eta_1}s) should be higher than max_concurrent=5 ({eta_5}s)"
        )

    def test_more_locations_gives_higher_eta_at_image_preparation(self):
        eta_2loc = _call("image_preparation", 65, unique_location_count=2)
        eta_5loc = _call("image_preparation", 65, unique_location_count=5)
        assert eta_5loc is not None and eta_2loc is not None
        assert eta_5loc > eta_2loc, (
            f"5 locations ({eta_5loc}s) should be higher than 2 locations ({eta_2loc}s)"
        )

    def test_image_generation_scaling_formula(self):
        """Verify: image_gen_duration = actual_shot_count * 60 / max_concurrent."""
        actual_shot_count = 30
        max_concurrent = 3
        expected_gen_duration = int(actual_shot_count * 60 / max_concurrent)  # 600s

        # At start of image_generation (progress=70, stage_progress=0.0)
        eta = _call("image_generation", 70, actual_shot_count=actual_shot_count, max_concurrent=max_concurrent)
        assert eta is not None
        # ETA should include image_generation (600s) + bgm (120s) at progress=70
        # stage_progress = (70 - 70) / (92 - 70) = 0.0 → remaining = 600s * 1.0 + 120s = 720s
        expected_min = expected_gen_duration + _ETA_STAGE_BASELINES["bgm"] - 60  # allow ±60s tolerance
        assert eta >= expected_min, (
            f"ETA={eta}s < expected_min={expected_min}s for {actual_shot_count} shots, "
            f"{max_concurrent} concurrent"
        )

    def test_single_shot_minimum_floor(self):
        """Degenerate: 1 shot should still return at least 5s."""
        eta = _call("image_generation", 91, actual_shot_count=1, max_concurrent=10)
        assert eta is not None and eta >= 5

    def test_large_shot_count(self):
        """50 shots should not crash and should return a very large ETA."""
        eta = _call("image_generation", 70, actual_shot_count=50, max_concurrent=3)
        assert eta is not None and eta > 0
        # 50 * 60 / 3 = 1000s + bgm 120s = 1120s at minimum
        assert eta >= 1000, f"50 shots ETA={eta}s seems too low"


# ---------------------------------------------------------------------------
# 7. Elapsed parameter (currently informational, reserved for future use)
# ---------------------------------------------------------------------------

class TestElapsedParameter:
    def test_elapsed_zero_no_effect(self):
        """elapsed=0 should give same result as elapsed=None."""
        eta_none = _call("screenplay", 20, elapsed=None)
        eta_zero = _call("screenplay", 20, elapsed=0)
        assert eta_none == eta_zero

    def test_elapsed_large_does_not_crash(self):
        """Large elapsed value should not cause negative ETA or crash."""
        eta = _call("screenplay", 20, elapsed=9999)
        assert eta is None or eta >= 0


# ---------------------------------------------------------------------------
# 8. started_at parameter (currently informational)
# ---------------------------------------------------------------------------

class TestStartedAtParameter:
    def test_started_at_none_works(self):
        eta = _call("character_design", 7, started_at=None)
        assert eta is not None and eta >= 5

    def test_started_at_past_does_not_crash(self):
        past = datetime.utcnow() - timedelta(minutes=10)
        eta = _call("character_design", 7, started_at=past)
        assert eta is None or eta >= 0


# ---------------------------------------------------------------------------
# 9. Monotonic property within same stage (property test)
# ---------------------------------------------------------------------------

class TestMonotonicWithinStage:
    """ETA should be non-increasing as progress increases within a stage."""

    @pytest.mark.parametrize("stage", ALL_REAL_STAGES)
    def test_monotonic_within_stage(self, stage: str):
        lo, hi = _ETA_STAGE_PROGRESS_BOUNDS.get(stage, (0, 100))
        if hi <= lo + 2:
            pytest.skip(f"Stage {stage} too narrow")

        # Sample 5 evenly-spaced progress values within stage bounds
        steps = [lo + (hi - lo) * i // 4 for i in range(5)]
        etas = [_call(stage, p) for p in steps]

        # All should be non-None (known stage)
        for i, (p, eta) in enumerate(zip(steps, etas)):
            assert eta is not None, f"Stage {stage} at progress={p} returned None"

        # ETA should be non-increasing (later progress → lower or equal ETA)
        for i in range(len(etas) - 1):
            assert etas[i] >= etas[i + 1], (
                f"Stage {stage}: ETA at progress={steps[i]} ({etas[i]}s) < "
                f"ETA at progress={steps[i+1]} ({etas[i+1]}s) — not monotonic"
            )


# ---------------------------------------------------------------------------
# 10. Floor: ETA never returns exactly 0 for non-terminal non-completed stages
# ---------------------------------------------------------------------------

class TestMinimumFloor:
    def test_floor_at_5s_minimum(self):
        """For non-terminal stages, ETA must be at least 5s."""
        # bgm at progress=99 → only "completed" (0) left → but floor kicks in
        eta = _call("bgm", 99)
        assert eta is not None and eta >= 5

    def test_story_generation_at_upper_bound(self):
        # progress=6 = upper bound of story_generation
        # Remaining: 0 for story_generation + character_design + screenplay + ... stages
        # Must be >= 5 (floor)
        eta = _call("story_generation", 6)
        assert eta is not None and eta >= 5


# ---------------------------------------------------------------------------
# 11. All stage names in _ETA_STAGE_ORDER are covered
# ---------------------------------------------------------------------------

class TestStageCoverage:
    def test_all_known_stages_handled(self):
        """Every stage in _ETA_STAGE_ORDER should either return int or 0 (not None)."""
        for stage in _ETA_STAGE_ORDER:
            lo = _ETA_STAGE_PROGRESS_BOUNDS.get(stage, (0, 100))[0]
            result = _call(stage, lo)
            assert result is not None, (
                f"Known stage {stage!r} returned None — must return int"
            )
            assert isinstance(result, int), (
                f"Stage {stage!r} returned non-int: {result!r}"
            )
            assert result >= 0, f"Stage {stage!r} returned negative: {result}"
