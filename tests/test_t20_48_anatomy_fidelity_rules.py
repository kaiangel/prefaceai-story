"""
T20-48: ANATOMY_FIDELITY_RULES — pytest 验证 prompt 含 anatomy 关键词.

Background: test20 Shot 16 rendered 4 hands on 2 human characters because the
image_prompt had an ambiguous "typing" action without explicit hand attribution.
ANATOMY_FIDELITY_RULES in storyboard_prompts.py adds hard constraints that
Stage 4 LLM must specify "exactly 2 hands per person" and "exactly 2 arms per person".

Author: @AI-ML
Date: 2026-05-20
Owner: TASK-T20-48 P2
"""

import pytest
from app.prompts.storyboard_prompts import ANATOMY_FIDELITY_RULES


class TestAnatomyFidelityRulesExistence:
    """ANATOMY_FIDELITY_RULES 存在 + 关键词覆盖."""

    def test_anatomy_fidelity_rules_is_string(self):
        assert isinstance(ANATOMY_FIDELITY_RULES, str)
        assert len(ANATOMY_FIDELITY_RULES) > 100

    def test_contains_exactly_2_hands_constraint(self):
        lower = ANATOMY_FIDELITY_RULES.lower()
        assert "exactly 2 hands" in lower

    def test_contains_exactly_2_arms_constraint(self):
        lower = ANATOMY_FIDELITY_RULES.lower()
        assert "exactly 2 arms" in lower

    def test_contains_normal_human_anatomy(self):
        """Prompt must mention normal human anatomy proportions."""
        assert "normal human" in ANATOMY_FIDELITY_RULES or "Normal human" in ANATOMY_FIDELITY_RULES

    def test_contains_mandatory_label(self):
        assert "MANDATORY" in ANATOMY_FIDELITY_RULES

    def test_contains_anatomy_fidelity_title(self):
        assert "ANATOMY FIDELITY" in ANATOMY_FIDELITY_RULES

    def test_contains_self_check_instruction(self):
        assert "SELF-CHECK" in ANATOMY_FIDELITY_RULES or "self-check" in ANATOMY_FIDELITY_RULES.lower()

    def test_contains_bad_vs_good_examples(self):
        assert "BAD" in ANATOMY_FIDELITY_RULES
        assert "GOOD" in ANATOMY_FIDELITY_RULES


class TestAnatomyFidelityRulesContentDetail:
    """ANATOMY_FIDELITY_RULES content 细节 — action disambiguation + multi-character."""

    def test_contains_action_disambiguation_section(self):
        """Ambiguous action descriptions should be covered."""
        assert "ACTION DISAMBIGUATION" in ANATOMY_FIDELITY_RULES or "disambiguation" in ANATOMY_FIDELITY_RULES.lower()

    def test_contains_typing_example(self):
        """typing is the exact action that caused Shot 16 issue."""
        assert "typing" in ANATOMY_FIDELITY_RULES.lower()

    def test_contains_multi_character_section(self):
        """Multi-character scenarios need spatial body separation."""
        assert "MULTI-CHARACTER" in ANATOMY_FIDELITY_RULES or "multi-character" in ANATOMY_FIDELITY_RULES.lower()

    def test_contains_which_hand_instruction(self):
        """Must instruct which hand (left/right/both)."""
        lower = ANATOMY_FIDELITY_RULES.lower()
        assert "left hand" in lower or "right hand" in lower or "which hand" in lower

    def test_contains_per_character_count_rule(self):
        """Each character must have exactly the right limb count."""
        assert "per character" in ANATOMY_FIDELITY_RULES.lower() or "per visible" in ANATOMY_FIDELITY_RULES.lower()

    def test_contains_hallucinate_or_hallucination_reference(self):
        """Should reference the hallucination problem."""
        lower = ANATOMY_FIDELITY_RULES.lower()
        assert "hallucin" in lower  # covers hallucinate/hallucination

    def test_references_test20_shot16_evidence(self):
        """Should reference the real test20 Shot 16 evidence."""
        assert "Shot 16" in ANATOMY_FIDELITY_RULES or "test20" in ANATOMY_FIDELITY_RULES.lower()


class TestAnatomyFidelityRulesIntegration:
    """ANATOMY_FIDELITY_RULES 与其他 storyboard_prompts 导出的集成."""

    def test_importable_alongside_seedream_safety(self):
        """Must be importable together with SEEDREAM_SAFETY_AVOIDANCE_RULES."""
        from app.prompts.storyboard_prompts import (
            ANATOMY_FIDELITY_RULES,
            SEEDREAM_SAFETY_AVOIDANCE_RULES,
        )
        assert ANATOMY_FIDELITY_RULES != SEEDREAM_SAFETY_AVOIDANCE_RULES

    def test_importable_alongside_hand_prop_anatomy(self):
        """ANATOMY_FIDELITY_RULES and HAND_PROP_ANATOMY_RULES are both exported."""
        from app.prompts.storyboard_prompts import (
            ANATOMY_FIDELITY_RULES,
            HAND_PROP_ANATOMY_RULES,
        )
        # They are complementary but distinct (different purpose)
        assert ANATOMY_FIDELITY_RULES != HAND_PROP_ANATOMY_RULES

    def test_anatomy_fidelity_does_not_break_existing_exports(self):
        """Adding ANATOMY_FIDELITY_RULES must not break any existing exports."""
        from app.prompts.storyboard_prompts import (
            NARRATION_TO_VISUAL_EXTRACTION_RULES,
            OFF_SCREEN_SOUND_HANDLING_RULES,
            HAND_PROP_ANATOMY_RULES,
            HAIR_COLOR_REQUIREMENT_RULE,
            SPECIES_FIDELITY_RULES,
            SEEDREAM_SAFETY_AVOIDANCE_RULES,
            DEC046_V3_STAGE4_RULES,
        )
        for var in [
            NARRATION_TO_VISUAL_EXTRACTION_RULES,
            OFF_SCREEN_SOUND_HANDLING_RULES,
            HAND_PROP_ANATOMY_RULES,
            HAIR_COLOR_REQUIREMENT_RULE,
            SPECIES_FIDELITY_RULES,
            SEEDREAM_SAFETY_AVOIDANCE_RULES,
            DEC046_V3_STAGE4_RULES,
        ]:
            assert isinstance(var, str)
            assert len(var) > 50


class TestAnatomyFidelityRulesSelfCheckCoverage:
    """ANATOMY_FIDELITY_RULES SELF-CHECK section covers the right verbs."""

    def test_self_check_covers_key_action_verbs(self):
        """Self-check must list the action verbs that trigger hand-count verification."""
        lower = ANATOMY_FIDELITY_RULES.lower()
        # At least some of the key verbs must appear
        action_verbs = ["hold", "reach", "grab", "point", "gesture"]
        covered = [v for v in action_verbs if v in lower]
        assert len(covered) >= 3, f"Only covered verbs: {covered}"

    def test_rule_structure_uses_separator(self):
        """Rule blocks use the standard ═══ separator for readability."""
        assert "═══" in ANATOMY_FIDELITY_RULES

    def test_rule_length_is_substantial(self):
        """The rule should be substantial (>500 chars) to give LLM enough guidance."""
        assert len(ANATOMY_FIDELITY_RULES) > 500
