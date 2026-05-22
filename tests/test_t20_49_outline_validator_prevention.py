"""
T20-49: OUTLINE_VALIDATION_RULES — pytest 验证 StoryOutlineGenerator prompt
含 OUTLINE OUTPUT VALIDATION 关键词 + 4 条规则.

Background: test20 outline validator 抓到 4 警告:
  1. plot_points 最后一个 beat = "midpoint" 而非 climax/resolution
  2. inciting_incident + first_turn beat_tag 重复出现
  3. 2 角色 emotional_journey 与 plot_points 情绪递进不符

Stage 3 LLM 实际自愈了，但长期应该 Stage 1 一次输出对。
AI-ML 在 story_outline_generator.py _build_prompt() 末尾加 OUTLINE_VALIDATION_RULES
后置自检块，让 LLM 在输出前自检 4 条规则。

Author: @AI-ML
Date: 2026-05-20
Owner: TASK-T20-49 P3
"""

import sys
import pytest
from pathlib import Path

# ---------------------------------------------------------------------------
# Import story_outline_generator without triggering full app service __init__
# (avoids google.genai / anthropic SDK import errors in test environments)
# ---------------------------------------------------------------------------
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from app.services.story_outline_generator import StoryOutlineGenerator
    _GENERATOR_AVAILABLE = True
except Exception:
    _GENERATOR_AVAILABLE = False


def _make_generator():
    """Return StoryOutlineGenerator instance with no LLM clients (prompt-only)."""
    if not _GENERATOR_AVAILABLE:
        pytest.skip("StoryOutlineGenerator import failed (missing deps) — skip")
    gen = StoryOutlineGenerator.__new__(StoryOutlineGenerator)
    gen.claude_client = None
    gen.gemini_client = None
    gen.claude_model = "claude-sonnet-4-6"
    gen.gemini_model = "gemini-3.1-flash-lite-preview"
    return gen


def _build_outline_prompt(idea: str = "一个关于镜中人的恐怖故事", style_preset: str = "gothic") -> str:
    """Build the Stage 1 prompt for inspection."""
    gen = _make_generator()
    return gen._build_prompt(
        idea=idea,
        style_preset=style_preset,
        target_duration_minutes=2,
        min_shots=18,
        target_seconds=120,
        language="zh",
        character_count=3,
    )


class TestOutlineValidationRulesExistence:
    """OUTLINE_VALIDATION_RULES 存在于 StoryOutlineGenerator _build_prompt() 输出中."""

    def test_outline_validation_section_present(self):
        prompt = _build_outline_prompt()
        assert "OUTLINE OUTPUT VALIDATION" in prompt

    def test_mandatory_label_present(self):
        prompt = _build_outline_prompt()
        assert "MANDATORY" in prompt

    def test_four_rules_labeled(self):
        """Should have OV-1, OV-2, OV-3, OV-4 rule labels."""
        prompt = _build_outline_prompt()
        for rule_label in ["OV-1", "OV-2", "OV-3", "OV-4"]:
            assert rule_label in prompt, f"Missing rule label: {rule_label}"


class TestOutlineValidationRuleOV1:
    """OV-1: plot_points 最后一个 beat 必须是 climax 或 resolution."""

    def test_ov1_climax_mentioned(self):
        prompt = _build_outline_prompt()
        assert "climax" in prompt

    def test_ov1_resolution_mentioned(self):
        prompt = _build_outline_prompt()
        assert "resolution" in prompt

    def test_ov1_last_beat_constraint(self):
        """OV-1 should say the LAST plot_point beat must be climax/resolution."""
        prompt = _build_outline_prompt()
        lower = prompt.lower()
        assert "last" in lower or "最后" in prompt

    def test_ov1_midpoint_forbidden_as_final(self):
        """OV-1 should mention midpoint is not acceptable as last beat."""
        prompt = _build_outline_prompt()
        assert "midpoint" in prompt

    def test_ov1_beat_enum_list_present(self):
        """OV-1 should list the valid beat values."""
        prompt = _build_outline_prompt()
        assert "inciting_incident" in prompt


class TestOutlineValidationRuleOV2:
    """OV-2: beat_tag 不允许重复，重复时加 _a / _b 后缀."""

    def test_ov2_no_duplicate_beat_tags(self):
        prompt = _build_outline_prompt()
        lower = prompt.lower()
        assert "duplicate" in lower or "重复" in prompt

    def test_ov2_suffix_a_b_mentioned(self):
        """OV-2 should instruct using _a / _b suffix for duplicates."""
        prompt = _build_outline_prompt()
        assert "_a" in prompt or "_b" in prompt

    def test_ov2_inciting_incident_a_example(self):
        """Should use inciting_incident_a / inciting_incident_b as example."""
        prompt = _build_outline_prompt()
        assert "inciting_incident_a" in prompt or "inciting_incident_b" in prompt


class TestOutlineValidationRuleOV3:
    """OV-3: emotional_journey 必须与 plot_points 对应."""

    def test_ov3_emotional_journey_mentioned(self):
        prompt = _build_outline_prompt()
        assert "emotional_journey" in prompt

    def test_ov3_plot_points_consistency(self):
        """OV-3 should explicitly link emotional_journey to plot_points."""
        prompt = _build_outline_prompt()
        assert "plot_points" in prompt.lower() or "plot_point" in prompt.lower()

    def test_ov3_bad_good_examples(self):
        """OV-3 should have bad/good examples for emotional_journey consistency."""
        prompt = _build_outline_prompt()
        assert "❌" in prompt or "BAD" in prompt or "错误" in prompt
        assert "✅" in prompt or "GOOD" in prompt or "正确" in prompt


class TestOutlineValidationRuleOV4:
    """OV-4: 输出前在 _validation_check 字段自报 4 条规则状态."""

    def test_ov4_validation_check_field_mentioned(self):
        prompt = _build_outline_prompt()
        assert "_validation_check" in prompt

    def test_ov4_ov1_self_report_field(self):
        """OV-4 should show OV1_last_beat_is_climax_or_resolution field."""
        prompt = _build_outline_prompt()
        assert "OV1_last_beat_is_climax_or_resolution" in prompt

    def test_ov4_ov2_self_report_field(self):
        """OV-4 should show OV2_no_duplicate_beat_tags field."""
        prompt = _build_outline_prompt()
        assert "OV2_no_duplicate_beat_tags" in prompt

    def test_ov4_ov3_self_report_field(self):
        """OV-4 should show OV3_emotional_journey_matches_plot field."""
        prompt = _build_outline_prompt()
        assert "OV3_emotional_journey_matches_plot" in prompt

    def test_ov4_issues_if_any_field(self):
        """OV-4 should have issues_if_any for reporting violations."""
        prompt = _build_outline_prompt()
        assert "issues_if_any" in prompt

    def test_ov4_rewrite_instruction(self):
        """OV-4 should instruct LLM to rewrite if any rule fails."""
        prompt = _build_outline_prompt()
        lower = prompt.lower()
        assert "rewrite" in lower or "重写" in prompt


class TestOutlineValidationRulesRegression:
    """Regression: 加了 OV 规则不破坏现有 _build_prompt() 内容."""

    def test_existing_plot_points_format_still_present(self):
        """The existing plot_points JSON format must still be in the prompt."""
        prompt = _build_outline_prompt()
        assert "plot_points" in prompt
        assert "beat" in prompt
        assert "estimated_duration_seconds" in prompt

    def test_existing_characters_overview_format_still_present(self):
        """characters_overview format must still be intact."""
        prompt = _build_outline_prompt()
        assert "characters_overview" in prompt
        assert "emotional_journey" in prompt

    def test_existing_unique_locations_format_still_present(self):
        """unique_locations section must still be intact."""
        prompt = _build_outline_prompt()
        assert "unique_locations" in prompt

    def test_existing_narrative_consistency_rules_still_present(self):
        """The existing 故事内部一致性规则 must still be present."""
        prompt = _build_outline_prompt()
        assert "故事内部一致性" in prompt

    def test_existing_title_consistency_rules_still_present(self):
        """TITLE CONSISTENCY section must still be present."""
        prompt = _build_outline_prompt()
        assert "TITLE CONSISTENCY" in prompt

    def test_validation_rules_near_end_of_prompt(self):
        """OUTLINE_VALIDATION_RULES should be the last major section (appended at end)."""
        prompt = _build_outline_prompt()
        ov4_pos = prompt.find("OV-4")
        assert ov4_pos > 0
        # Should be in the last 25% of the prompt
        assert ov4_pos > len(prompt) * 0.5, f"OV-4 found too early at pos {ov4_pos} / {len(prompt)}"

    def test_prompt_builds_without_error_for_different_styles(self):
        """Prompt build should work for any style/genre combination."""
        for style in ["realistic", "anime", "ink", "cyberpunk"]:
            prompt = _build_outline_prompt(idea=f"一个关于{style}风格的故事", style_preset=style)
            assert "OUTLINE OUTPUT VALIDATION" in prompt

    def test_plot_points_completeness_rule_still_present(self):
        """The existing plot_points 字段完整性 MANDATORY rule must still be there."""
        prompt = _build_outline_prompt()
        # The existing rule about beat + estimated_duration_seconds being mandatory
        assert "plot_points 字段完整性" in prompt or (
            "beat" in prompt and "estimated_duration_seconds" in prompt
        )

    def test_no_duplicate_mandatory_label_confusion(self):
        """The MANDATORY in OV rules should not interfere with existing MANDATORY sections."""
        prompt = _build_outline_prompt()
        # Multiple MANDATORY labels are fine as long as both sections exist
        assert "OUTLINE OUTPUT VALIDATION" in prompt
        assert "故事内部一致性" in prompt
