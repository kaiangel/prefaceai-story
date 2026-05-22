"""
T20-45 — BGM Duration Control: 短片信号词 linter 单测

验证目标：
1. _check_bgm_duration_signals() 检测到短片信号词时返回 has_duration_issue=True
2. _check_bgm_duration_signals() 缺少时长框架词时返回 has_duration_issue=True
3. _check_bgm_duration_signals() 含框架词且无短片信号时返回 PASS
4. _check_bgm_duration_signals() 大小写不敏感匹配
5. test20 实际 BGM prompt (镜中怒者) 能被检测到短片信号
6. _build_duration_repair_hint() 输出含必要修复指令
7. 健康 BGM prompt 含框架词时 PASS（不误杀正常 prompt）
8. 空/None 输入的安全处理
9. 各短片信号词单独触发测试
10. 各框架词单独通过测试
"""

import sys
from pathlib import Path
import pytest

# ---------------------------------------------------------------------------
# Import music_generation_service without triggering full app init
# ---------------------------------------------------------------------------
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from app.services.music_generation_service import (
        _check_bgm_duration_signals,
        _build_duration_repair_hint,
        _DURATION_SHORT_SIGNALS,
        _DURATION_FRAMEWORK_WORDS,
    )
    _MODULE_AVAILABLE = True
except ImportError as e:
    _MODULE_AVAILABLE = False
    _IMPORT_ERROR = str(e)


def _require():
    if not _MODULE_AVAILABLE:
        pytest.skip(f"music_generation_service not importable: {_IMPORT_ERROR}")


# ─────────────────────────────────────────────────────────────────────────────
# Section 1: Module-level constants coverage
# ─────────────────────────────────────────────────────────────────────────────

class TestDurationConstants:
    def test_short_signals_list_not_empty(self):
        _require()
        assert len(_DURATION_SHORT_SIGNALS) >= 5, (
            "SHORT_SIGNALS should cover at least 5 known bad patterns"
        )

    def test_framework_words_list_not_empty(self):
        _require()
        assert len(_DURATION_FRAMEWORK_WORDS) >= 8, (
            "FRAMEWORK_WORDS should cover at least 8 positive signals"
        )

    def test_short_signals_includes_key_patterns(self):
        _require()
        signals_lower = [s.lower() for s in _DURATION_SHORT_SIGNALS]
        for expected in ["suddenly stops", "no resolution", "no answer", "question hanging"]:
            assert expected in signals_lower, (
                f"Key short signal '{expected}' missing from _DURATION_SHORT_SIGNALS"
            )

    def test_framework_includes_sustained(self):
        _require()
        fw_lower = [w.lower() for w in _DURATION_FRAMEWORK_WORDS]
        assert "sustained" in fw_lower

    def test_framework_includes_building(self):
        _require()
        fw_lower = [w.lower() for w in _DURATION_FRAMEWORK_WORDS]
        assert "building" in fw_lower

    def test_framework_includes_continuous(self):
        _require()
        fw_lower = [w.lower() for w in _DURATION_FRAMEWORK_WORDS]
        assert "continuous" in fw_lower or "continuously" in fw_lower


# ─────────────────────────────────────────────────────────────────────────────
# Section 2: _check_bgm_duration_signals() — short signal detection
# ─────────────────────────────────────────────────────────────────────────────

class TestShortSignalDetection:
    def test_suddenly_stops_detected(self):
        _require()
        prompt = "Minor key. A muffled pulse. Then suddenly stops."
        has_issue, leaked, _ = _check_bgm_duration_signals(prompt)
        assert has_issue
        assert any("suddenly stops" in s.lower() for s in leaked)

    def test_no_resolution_detected(self):
        _require()
        prompt = "Dark ambient tone. No resolution. The drone fades."
        has_issue, leaked, _ = _check_bgm_duration_signals(prompt)
        assert has_issue
        assert any("no resolution" in s.lower() for s in leaked)

    def test_question_hanging_detected(self):
        _require()
        prompt = "Sparse piano. A question hanging. No answer."
        has_issue, leaked, _ = _check_bgm_duration_signals(prompt)
        assert has_issue
        assert any("question hanging" in s.lower() for s in leaked)

    def test_no_answer_detected(self):
        _require()
        prompt = "The mirror reflects nothing. No answer. Silence."
        has_issue, leaked, _ = _check_bgm_duration_signals(prompt)
        assert has_issue

    def test_long_silences_detected(self):
        _require()
        prompt = "Long silences that last one beat too long."
        has_issue, leaked, _ = _check_bgm_duration_signals(prompt)
        assert has_issue
        assert any("long silence" in s.lower() for s in leaked)

    def test_abruptly_ends_detected(self):
        _require()
        prompt = "Tension builds, then abruptly ends."
        has_issue, leaked, _ = _check_bgm_duration_signals(prompt)
        assert has_issue

    def test_case_insensitive_detection(self):
        _require()
        prompt = "A pulse that builds. Then SUDDENLY STOPS."
        has_issue, leaked, _ = _check_bgm_duration_signals(prompt)
        assert has_issue

    def test_multiple_short_signals_all_reported(self):
        _require()
        prompt = "Suddenly stops. No resolution. Question hanging. No answer."
        has_issue, leaked, _ = _check_bgm_duration_signals(prompt)
        assert has_issue
        assert len(leaked) >= 2

    def test_test20_actual_bgm_prompt_fails(self):
        """test20 镜中怒者实际生成的 BGM prompt 应被检测出短片信号"""
        _require()
        actual_prompt = (
            "Minor key. Sparse percussion that won't quite become a rhythm — "
            "single thuds at irregular intervals, like a heartbeat heard through apartment walls. "
            "Ambient drone underneath, low and persistent, settling into the chest before the ear notices. "
            "Long silences that last one beat too long. A muffled pulse that builds, builds — "
            "then suddenly stops. No resolution. The drone continues into darkness, "
            "as if the mirror knows something the listener doesn't.\n\n"
            "镜中，只剩林深一人。灯灭。\n\n"
            "A question hanging. No answer. Just the cold certainty of something watching from the glass."
        )
        has_issue, leaked, has_framework = _check_bgm_duration_signals(actual_prompt)
        assert has_issue, (
            f"test20 BGM prompt should fail duration check. "
            f"leaked={leaked}, has_framework={has_framework}"
        )
        assert len(leaked) >= 2, (
            f"Expected ≥2 short signals in test20 prompt, got {leaked}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Section 3: _check_bgm_duration_signals() — framework word requirement
# ─────────────────────────────────────────────────────────────────────────────

class TestFrameworkWordRequirement:
    def test_no_framework_word_triggers_issue(self):
        _require()
        # No short signals AND no framework words → still has issue
        prompt = "Minor key. Sparse piano. Dark ambient drone. Melancholic tone."
        has_issue, leaked, has_framework = _check_bgm_duration_signals(prompt)
        assert not leaked, "No short signals should be leaked"
        assert not has_framework, "No framework word should be found"
        assert has_issue, "Missing framework word should trigger duration issue"

    def test_sustained_passes(self):
        _require()
        prompt = "Sustained low drone beneath unresolved tension, continuously deepening."
        has_issue, leaked, has_framework = _check_bgm_duration_signals(prompt)
        assert has_framework
        assert not leaked
        assert not has_issue

    def test_building_passes(self):
        _require()
        prompt = "Building momentum with layered percussion and ambient drone."
        has_issue, leaked, has_framework = _check_bgm_duration_signals(prompt)
        assert has_framework
        assert not has_issue

    def test_developing_passes(self):
        _require()
        prompt = "A slowly developing melody, melancholic and extended."
        has_issue, leaked, has_framework = _check_bgm_duration_signals(prompt)
        assert has_framework
        assert not has_issue

    def test_unfolding_passes(self):
        _require()
        prompt = "Dark tension unfolding gradually through the scene."
        has_issue, leaked, has_framework = _check_bgm_duration_signals(prompt)
        assert has_framework
        assert not has_issue

    def test_continuously_passes(self):
        _require()
        prompt = "Tension continuously deepening beneath sparse percussion."
        has_issue, leaked, has_framework = _check_bgm_duration_signals(prompt)
        assert has_framework
        assert not has_issue

    def test_extended_passes(self):
        _require()
        prompt = "An extended ambient passage, sparse and haunting."
        has_issue, leaked, has_framework = _check_bgm_duration_signals(prompt)
        assert has_framework
        assert not has_issue

    def test_throughout_passes(self):
        _require()
        prompt = "Low drone persisting throughout, heartbeat rhythm."
        has_issue, leaked, has_framework = _check_bgm_duration_signals(prompt)
        assert has_framework
        assert not has_issue


# ─────────────────────────────────────────────────────────────────────────────
# Section 4: Healthy BGM prompts — should PASS (no false positives)
# ─────────────────────────────────────────────────────────────────────────────

class TestHealthyPromptNotFlagged:
    def test_mystery_healthy_prompt_passes(self):
        _require()
        prompt = (
            "Sustained low drone building beneath unresolved tension, "
            "continuously deepening through the scene. Sparse percussion "
            "at irregular intervals. Dark ambient atmosphere developing "
            "throughout the story, carrying the cold certainty forward."
        )
        has_issue, leaked, has_framework = _check_bgm_duration_signals(prompt)
        assert not has_issue, f"Healthy mystery prompt should pass. leaked={leaked}"

    def test_melancholic_healthy_prompt_passes(self):
        _require()
        prompt = (
            "A slowly evolving melody, melancholic and extended, developing "
            "through long unhurried phrases. Sustained strings layering "
            "softly, gradually expanding to fill the emotional space."
        )
        has_issue, _, _ = _check_bgm_duration_signals(prompt)
        assert not has_issue

    def test_heroic_healthy_prompt_passes(self):
        _require()
        prompt = (
            "Continuously building momentum, layering percussion and melody, "
            "carrying through to a sustained peak of determination. "
            "Gradually expanding orchestral texture throughout."
        )
        has_issue, _, _ = _check_bgm_duration_signals(prompt)
        assert not has_issue

    def test_warm_healthy_prompt_passes(self):
        _require()
        prompt = (
            "Gentle warmth unfolding gradually, sustained throughout, "
            "softly expanding to fill the scene with comfort and hope. "
            "Developing piano melody building into full texture."
        )
        has_issue, _, _ = _check_bgm_duration_signals(prompt)
        assert not has_issue


# ─────────────────────────────────────────────────────────────────────────────
# Section 5: Edge cases — empty/None input safety
# ─────────────────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_string_safe(self):
        _require()
        has_issue, leaked, has_framework = _check_bgm_duration_signals("")
        assert not has_issue
        assert leaked == []
        assert not has_framework

    def test_none_input_safe(self):
        _require()
        has_issue, leaked, has_framework = _check_bgm_duration_signals(None)
        assert not has_issue
        assert leaked == []
        assert not has_framework

    def test_whitespace_only_safe(self):
        _require()
        has_issue, leaked, has_framework = _check_bgm_duration_signals("   \n\t  ")
        # whitespace has no short signals and no framework — but that's "missing framework"
        # However since we also return False for empty-ish prompts, check it doesn't crash
        assert isinstance(has_issue, bool)
        assert isinstance(leaked, list)
        assert isinstance(has_framework, bool)


# ─────────────────────────────────────────────────────────────────────────────
# Section 6: _build_duration_repair_hint() output validation
# ─────────────────────────────────────────────────────────────────────────────

class TestDurationRepairHint:
    def test_hint_mentions_target_duration(self):
        _require()
        hint = _build_duration_repair_hint(["suddenly stops"], False)
        assert "150" in hint or "2.5" in hint, (
            "Repair hint must mention target duration (150s or 2.5 minutes)"
        )

    def test_hint_lists_leaked_signals(self):
        _require()
        hint = _build_duration_repair_hint(["suddenly stops", "no resolution"], False)
        assert "suddenly stops" in hint
        assert "no resolution" in hint

    def test_hint_lists_framework_words_when_missing(self):
        _require()
        hint = _build_duration_repair_hint([], False)
        # Should mention framework words
        assert "sustained" in hint.lower() or "building" in hint.lower() or "continuous" in hint.lower()

    def test_hint_contains_replacement_example(self):
        _require()
        hint = _build_duration_repair_hint(["suddenly stops"], False)
        # Should give a concrete replacement example
        assert "sustained" in hint.lower() or "→" in hint

    def test_hint_not_empty(self):
        _require()
        hint = _build_duration_repair_hint(["no resolution"], True)
        assert len(hint) > 100

    def test_hint_no_leaked_no_framework(self):
        _require()
        # Only missing framework word (no short signals)
        hint = _build_duration_repair_hint([], False)
        assert len(hint) > 50
        # Should NOT mention leaked signals section
        assert "❌ 检测到短片信号词" not in hint

    def test_hint_with_leaked_and_framework_missing(self):
        _require()
        hint = _build_duration_repair_hint(["suddenly stops", "question hanging"], False)
        # Should mention both issues
        assert "suddenly stops" in hint
        assert len(hint) > 100
