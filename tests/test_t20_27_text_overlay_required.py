"""TASK-T20-FIXBATCH-5 Wave 4 RISK-T20-27 P2→P1 升级 —
Stage 3/4 强制 text_overlay 必填 + 关键转折强调.

测试目标 (test19 实证 Shot 13 关键转折 text_overlay=None bug):
1. screenplay_prompts.py 新增 RULE D8 (Stage 3 强制 critical turn 配 dialogue/thought)
2. storyboard_prompts.py 升级 RULE 0 + 新增 RULE 0.B (Stage 4 强制 critical turn 写 text_overlay)
3. is_critical_turn_beat() universal 检测器 (4 维度)
4. validate_critical_turns_have_dialogue() 验证 scene 完整性
5. test19 Shot 13 实际数据复现 (验证 validator 真能抓到这个 bug)
6. 关键转词清单覆盖通用故事 (universal — 不限定一种)

不依赖 LLM API. 纯 prompt + validator 单元测试.

Usage:
    cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story
    python -m pytest tests/test_t20_27_text_overlay_required.py -v
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest


# ========================================================================
# Section 1: Stage 4 storyboard_prompts.py RULE 0 + 0.B 升级
# ========================================================================


class TestStage4Rule0Upgrade:
    """COMIC_MODE_NARRATIVE_RULES RULE 0 + 0.B 必须含 T20-27 强制规则"""

    def test_rules_importable(self):
        from app.prompts.storyboard_prompts import COMIC_MODE_NARRATIVE_RULES  # noqa: F401

    def test_rule_0_b_critical_turn_present(self):
        from app.prompts.storyboard_prompts import COMIC_MODE_NARRATIVE_RULES
        assert "RULE 0.B" in COMIC_MODE_NARRATIVE_RULES or "CRITICAL TURN" in COMIC_MODE_NARRATIVE_RULES

    def test_rule_0_b_marks_t20_27(self):
        from app.prompts.storyboard_prompts import COMIC_MODE_NARRATIVE_RULES
        assert "T20-27" in COMIC_MODE_NARRATIVE_RULES

    def test_rule_0_lists_critical_keywords(self):
        from app.prompts.storyboard_prompts import COMIC_MODE_NARRATIVE_RULES
        keywords = ["climax", "twist", "reveal", "recognition", "discovery"]
        present = sum(1 for kw in keywords if kw in COMIC_MODE_NARRATIVE_RULES.lower())
        assert present >= 4, f"expected ≥4 critical turn keywords, got {present}"

    def test_rule_0_lists_chinese_emotional_keywords(self):
        from app.prompts.storyboard_prompts import COMIC_MODE_NARRATIVE_RULES
        zh_kw = ["震惊", "崩溃", "顿悟", "认出", "意识到"]
        present = sum(1 for kw in zh_kw if kw in COMIC_MODE_NARRATIVE_RULES)
        assert present >= 3, f"expected ≥3 Chinese emotional keywords, got {present}"

    def test_rule_0_forbids_empty_chinese_text(self):
        """RULE 0 必须明确禁止 chinese_text 为空"""
        from app.prompts.storyboard_prompts import COMIC_MODE_NARRATIVE_RULES
        # 必须说 NON-EMPTY + FORBIDDEN empty
        assert "NON-EMPTY" in COMIC_MODE_NARRATIVE_RULES or "non-empty" in COMIC_MODE_NARRATIVE_RULES
        assert "FORBIDDEN" in COMIC_MODE_NARRATIVE_RULES

    def test_rule_0_shows_shot_13_example(self):
        """RULE 0.B 必须用 Shot 13 (碑上陈砚名字) 真实案例"""
        from app.prompts.storyboard_prompts import COMIC_MODE_NARRATIVE_RULES
        # 至少 1 个 test19 真实案例 (墓碑 / 陈砚)
        assert "陈砚" in COMIC_MODE_NARRATIVE_RULES or "墓碑" in COMIC_MODE_NARRATIVE_RULES or "碑上" in COMIC_MODE_NARRATIVE_RULES

    def test_rule_0_has_self_check(self):
        from app.prompts.storyboard_prompts import COMIC_MODE_NARRATIVE_RULES
        assert "SELF-CHECK" in COMIC_MODE_NARRATIVE_RULES


# ========================================================================
# Section 2: Stage 3 screenplay_prompts.py RULE D8 新增
# ========================================================================


class TestStage3RuleD8:
    """DIALOGUE_THOUGHT_DENSITY_RULES 新增 RULE D8 — critical turn 必配 dialogue"""

    def test_rules_importable(self):
        from app.prompts.screenplay_prompts import DIALOGUE_THOUGHT_DENSITY_RULES  # noqa: F401

    def test_rule_d8_present(self):
        from app.prompts.screenplay_prompts import DIALOGUE_THOUGHT_DENSITY_RULES
        assert "RULE D8" in DIALOGUE_THOUGHT_DENSITY_RULES

    def test_rule_d8_marks_t20_27(self):
        from app.prompts.screenplay_prompts import DIALOGUE_THOUGHT_DENSITY_RULES
        assert "T20-27" in DIALOGUE_THOUGHT_DENSITY_RULES

    def test_rule_d8_provides_bad_good_examples(self):
        from app.prompts.screenplay_prompts import DIALOGUE_THOUGHT_DENSITY_RULES
        # D8 必须有 ❌ BAD + ✅ GOOD JSON example
        d8_start = DIALOGUE_THOUGHT_DENSITY_RULES.find("RULE D8")
        d8_section = DIALOGUE_THOUGHT_DENSITY_RULES[d8_start:]
        assert "❌" in d8_section
        assert "✅" in d8_section
        # 必须含 JSON 示例
        assert "action_beats" in d8_section
        assert "dialogue_beats" in d8_section

    def test_rule_d8_recommends_is_critical_turn_marker(self):
        from app.prompts.screenplay_prompts import DIALOGUE_THOUGHT_DENSITY_RULES
        assert "is_critical_turn" in DIALOGUE_THOUGHT_DENSITY_RULES


# ========================================================================
# Section 3: is_critical_turn_beat() universal 检测器
# ========================================================================


class TestIsCriticalTurnBeat:
    """4 维度检测 critical turn beat"""

    def test_function_importable(self):
        from app.prompts.screenplay_prompts import is_critical_turn_beat  # noqa: F401

    def test_dimension_1_beat_id_climax(self):
        from app.prompts.screenplay_prompts import is_critical_turn_beat
        assert is_critical_turn_beat({"beat_id": "scene_5_climax"})
        assert is_critical_turn_beat({"beat_id": "6a_revelation_reveal"})
        assert is_critical_turn_beat({"beat_id": "twist_turning_point"})
        assert is_critical_turn_beat({"beat_id": "death_scene"})
        assert is_critical_turn_beat({"beat_id": "recognition_moment"})

    def test_dimension_2_emotional_note_chinese(self):
        from app.prompts.screenplay_prompts import is_critical_turn_beat
        assert is_critical_turn_beat({"beat_id": "5a", "emotional_note": "震惊崩溃"})
        assert is_critical_turn_beat({"beat_id": "5a", "emotional_note": "突然顿悟"})
        assert is_critical_turn_beat({"beat_id": "5a", "emotional_note": "认出对方"})
        assert is_critical_turn_beat({"beat_id": "5a", "emotional_note": "发现真相"})

    def test_dimension_3_scene_plot_point(self):
        from app.prompts.screenplay_prompts import is_critical_turn_beat
        scene = {"plot_point": "climax_reveal", "scene_id": 6}
        # beat 自身无 marker, 但 scene plot_point 标记 → 仍 critical
        assert is_critical_turn_beat({"beat_id": "6a"}, scene=scene)

    def test_non_critical_returns_false(self):
        from app.prompts.screenplay_prompts import is_critical_turn_beat
        assert not is_critical_turn_beat({"beat_id": "1a_intro", "emotional_note": "平静"})
        assert not is_critical_turn_beat({"beat_id": "2b_walking", "emotional_note": "好奇"})
        assert not is_critical_turn_beat({"beat_id": "3a_dialog", "emotional_note": ""})

    def test_empty_input_no_crash(self):
        from app.prompts.screenplay_prompts import is_critical_turn_beat
        assert not is_critical_turn_beat({})
        assert not is_critical_turn_beat(None)  # type: ignore
        assert not is_critical_turn_beat({"beat_id": ""})


# ========================================================================
# Section 4: validate_critical_turns_have_dialogue() 验证器
# ========================================================================


class TestValidateCriticalTurnsHaveDialogue:
    """验证一个 scene 中 critical turn beats 都有 dialogue/thought 覆盖"""

    def test_function_importable(self):
        from app.prompts.screenplay_prompts import validate_critical_turns_have_dialogue  # noqa: F401

    def test_no_critical_turns_passes(self):
        """无 critical turn → 自动通过"""
        from app.prompts.screenplay_prompts import validate_critical_turns_have_dialogue
        scene = {
            "action_beats": [
                {"beat_id": "1a_intro", "action": "灰狐独行", "emotional_note": "平静"},
                {"beat_id": "1b_walk", "action": "小动物跟随", "emotional_note": "好奇"},
            ],
            "dialogue_beats": [],
        }
        r = validate_critical_turns_have_dialogue(scene)
        assert r["passes"]
        assert r["critical_turn_beats"] == []
        assert r["uncovered_beat_ids"] == []

    def test_critical_turn_with_matching_dialogue_passes(self):
        """critical turn beat 有对应 dialogue_beat (beat_id 前缀匹配)"""
        from app.prompts.screenplay_prompts import validate_critical_turns_have_dialogue
        scene = {
            "action_beats": [
                {"beat_id": "5a_climax", "action": "陈砚看墓碑", "emotional_note": "震惊"},
            ],
            "dialogue_beats": [
                {"beat_id": "5a_climax_thought", "type": "thought",
                 "line": "（这是我的名字……）"},
            ],
        }
        r = validate_critical_turns_have_dialogue(scene)
        assert r["passes"], r["issues"]
        assert "5a_climax" in r["covered_beat_ids"]

    def test_critical_turn_without_dialogue_fails(self):
        """test19 Shot 13 真根因: critical turn beat 无 dialogue_beat → P0 bug"""
        from app.prompts.screenplay_prompts import validate_critical_turns_have_dialogue
        # 模拟 test19 Stage 3 输出的 scene 6 (Shot 13 关键转折所在)
        scene = {
            "scene_id": 6,
            "narration": "碑上刻着：陈砚。生卒年空白。",
            "action_beats": [
                {"beat_id": "6a_revelation", "action": "陈砚跪在墓碑前看见自己的名字",
                 "emotional_note": "震惊崩溃"}
            ],
            "dialogue_beats": [],  # ← 空! Stage 4 无 text_overlay 来源
        }
        r = validate_critical_turns_have_dialogue(scene)
        assert not r["passes"]
        assert "6a_revelation" in r["uncovered_beat_ids"]
        assert len(r["issues"]) >= 1
        assert "T20-27" in r["issues"][0] or "P0" in r["issues"][0]

    def test_multiple_critical_turns_partial_coverage(self):
        from app.prompts.screenplay_prompts import validate_critical_turns_have_dialogue
        scene = {
            "action_beats": [
                {"beat_id": "5a_climax", "emotional_note": "震惊"},
                {"beat_id": "5b_reveal", "emotional_note": "认出"},
                {"beat_id": "5c_quiet", "emotional_note": "平静"},
            ],
            "dialogue_beats": [
                {"beat_id": "5a_climax_thought", "type": "thought", "line": "（看到了）"},
                # 5b_reveal 没有覆盖 → uncovered
            ],
        }
        r = validate_critical_turns_have_dialogue(scene)
        assert not r["passes"]
        assert "5a_climax" in r["covered_beat_ids"]
        assert "5b_reveal" in r["uncovered_beat_ids"]
        # 5c 不是 critical turn → 不计入
        assert "5c_quiet" not in r["critical_turn_beats"]


# ========================================================================
# Section 5: test19 Shot 13 真实数据复现
# ========================================================================


class TestTest19Shot13Real:
    """模拟 test19 实际 Stage 3 输出 → 验证 validator 真抓到 P0 bug"""

    def test_test19_shot13_critical_turn_detected(self):
        """Shot 13 对应的 scene 6 应被识别为含 critical turn"""
        from app.prompts.screenplay_prompts import (
            is_critical_turn_beat,
            validate_critical_turns_have_dialogue,
        )
        # 真实 narration: "碑上刻着：陈砚。生卒年空白。弓落雪中。"
        # action_beat 含 revelation + 震惊
        scene = {
            "scene_id": 6,
            "narration": "碑上刻着：陈砚。生卒年空白。",
            "action_beats": [
                {"beat_id": "6a_revelation", "action": "陈砚跪在墓碑前看见自己的名字",
                 "emotional_note": "震惊崩溃"}
            ],
            "dialogue_beats": [],
        }
        # critical turn 应被 detect (双维度命中: beat_id "revelation" + emotional "震惊崩溃")
        # 注意: "revelation" 不在 BEAT_ID_KEYWORDS 显式列表中, 但 "震惊崩溃" 双中文词都在
        beat = scene["action_beats"][0]
        assert is_critical_turn_beat(beat, scene=scene), \
            "test19 Shot 13 scene must be detected as critical turn (震惊崩溃 matches)"

        # validator 应抓到 uncovered
        r = validate_critical_turns_have_dialogue(scene)
        assert not r["passes"], "must catch the empty dialogue_beats P0 bug"


# ========================================================================
# Section 6: Universal — 多种故事/角色类型通用
# ========================================================================


class TestUniversal:
    """检测器不限定具体故事/角色物种"""

    def test_critical_keywords_constants_exported(self):
        from app.prompts.screenplay_prompts import (
            CRITICAL_TURN_BEAT_ID_KEYWORDS,
            CRITICAL_TURN_EMOTIONAL_KEYWORDS_ZH,
        )
        assert isinstance(CRITICAL_TURN_BEAT_ID_KEYWORDS, tuple)
        assert isinstance(CRITICAL_TURN_EMOTIONAL_KEYWORDS_ZH, tuple)
        # 必须含通用关键词
        assert "climax" in CRITICAL_TURN_BEAT_ID_KEYWORDS
        assert "reveal" in CRITICAL_TURN_BEAT_ID_KEYWORDS
        assert "震惊" in CRITICAL_TURN_EMOTIONAL_KEYWORDS_ZH
        assert "认出" in CRITICAL_TURN_EMOTIONAL_KEYWORDS_ZH

    def test_works_for_modern_drama_story(self):
        from app.prompts.screenplay_prompts import is_critical_turn_beat
        # 现代都市剧
        scene = {
            "scene_id": 8,
            "action_beats": [
                {"beat_id": "8a_betrayal", "action": "她发现丈夫出轨", "emotional_note": "崩溃"}
            ]
        }
        for b in scene["action_beats"]:
            assert is_critical_turn_beat(b, scene)

    def test_works_for_fantasy_animal_story(self):
        from app.prompts.screenplay_prompts import is_critical_turn_beat
        # 奇幻动物寓言
        scene = {
            "scene_id": 4,
            "action_beats": [
                {"beat_id": "4c_recognition", "action": "小狐狸认出失散母亲", "emotional_note": "认出"}
            ]
        }
        for b in scene["action_beats"]:
            assert is_critical_turn_beat(b, scene)

    def test_works_for_scifi_story(self):
        from app.prompts.screenplay_prompts import is_critical_turn_beat
        # 科幻
        scene = {
            "scene_id": 10,
            "plot_point": "twist_reveal",
            "action_beats": [
                {"beat_id": "10a_awakening", "action": "AI 发现自己是人类", "emotional_note": "顿悟"}
            ]
        }
        for b in scene["action_beats"]:
            assert is_critical_turn_beat(b, scene)


# ========================================================================
# Section 7: 向后兼容 (不破坏现有用例)
# ========================================================================


class TestBackwardCompat:
    """T20-27 升级不破坏现有 Stage 3 / Stage 4 工作流"""

    def test_dec044_rules_still_intact(self):
        from app.prompts.screenplay_prompts import DEC044_SCREENPLAY_RULES
        assert "DEC-044" in DEC044_SCREENPLAY_RULES
        assert "narration" in DEC044_SCREENPLAY_RULES.lower()

    def test_existing_validators_still_work(self):
        from app.prompts.screenplay_prompts import (
            validate_narration_caption_length,
            validate_dialogue_thought_density,
        )
        r = validate_narration_caption_length("立春清晨")
        assert r["passes_total_length"]
        scene = {"dialogue_beats": [{"type": "thought", "line": "（嗯）"}]}
        r2 = validate_dialogue_thought_density(scene)
        assert isinstance(r2, dict)

    def test_existing_comic_mode_rules_intact(self):
        from app.prompts.storyboard_prompts import COMIC_MODE_NARRATIVE_RULES
        # 旧 RULE 1-6 全在
        for rule_num in (1, 2, 3, 4, 5, 6):
            assert f"RULE {rule_num}" in COMIC_MODE_NARRATIVE_RULES

    def test_all_new_symbols_in_all(self):
        from app.prompts.screenplay_prompts import __all__
        new_symbols = [
            "CRITICAL_TURN_BEAT_ID_KEYWORDS",
            "CRITICAL_TURN_EMOTIONAL_KEYWORDS_ZH",
            "is_critical_turn_beat",
            "validate_critical_turns_have_dialogue",
        ]
        for sym in new_symbols:
            assert sym in __all__, f"missing from __all__: {sym}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
