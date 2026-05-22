"""
test_emotional_arc_dict_str_defense.py — RISK-T19-9 emotional_arc dict/str 防御

测试 story_music_extractor.extract_story_for_music() 对
  - emotional_arc (outline 字段): dict / str / None / int 四种类型
的防御性处理，确保不再抛出 AttributeError (str.get() 不存在)。

仿照 test_bgm_dict_str_defense.py (RISK-T19-5 visual_tone/atmosphere) 的测试模式。

Wave 14 / RISK-T19-9 / 2026-05-18
"""

import pytest
from app.services.story_music_extractor import extract_story_for_music


# ── 辅助函数 ──────────────────────────────────────────────────────────────────


def _make_outline(**overrides) -> dict:
    """构造最小 outline，支持覆盖任意字段。"""
    base = {
        "title": "Test Story",
        "narrative_pace": "moderate",
        "visual_tone": {"overall_mood": "calm", "color_palette": ["blue", "white"]},
        "emotional_arc": {
            "opening": "peaceful",
            "midpoint": "tension",
            "climax": "dramatic",
            "resolution": "hopeful",
        },
        "plot_points": [],
        "characters_overview": [],
    }
    base.update(overrides)
    return base


def _make_screenplay_simple() -> dict:
    """构造最小 screenplay（无 atmosphere 复杂情况）"""
    return {
        "scenes": [
            {
                "scene_id": 1,
                "atmosphere": {"mood": "calm", "sound_design_hint": "quiet", "temperature_feel": "warm"},
                "narration_tone": "gentle",
                "narration_pace": "slow",
                "narration": "The story begins.",
            }
        ]
    }


# ── A. emotional_arc dict — 正常路径 ─────────────────────────────────────────


class TestEmotionalArcDictNormal:
    """emotional_arc 为 dict 类型时正常提取 4 个子字段"""

    def test_full_dict(self):
        """完整 dict — 4 子字段全部正确提取"""
        outline = _make_outline(
            emotional_arc={
                "opening": "calm_start",
                "midpoint": "rising_tension",
                "climax": "peak_drama",
                "resolution": "peaceful_end",
            }
        )
        result = extract_story_for_music(outline, _make_screenplay_simple())
        assert result["emotional_arc_opening"] == "calm_start"
        assert result["emotional_arc_midpoint"] == "rising_tension"
        assert result["emotional_arc_climax"] == "peak_drama"
        assert result["emotional_arc_resolution"] == "peaceful_end"

    def test_partial_dict(self):
        """不完整 dict（只有 opening + climax）— 缺失字段返回空字符串"""
        outline = _make_outline(
            emotional_arc={
                "opening": "bittersweet",
                "climax": "explosive",
            }
        )
        result = extract_story_for_music(outline, _make_screenplay_simple())
        assert result["emotional_arc_opening"] == "bittersweet"
        assert result["emotional_arc_midpoint"] == ""  # 缺失 → 空字符串
        assert result["emotional_arc_climax"] == "explosive"
        assert result["emotional_arc_resolution"] == ""  # 缺失 → 空字符串

    def test_empty_dict(self):
        """空 dict — 4 子字段全部返回空字符串"""
        outline = _make_outline(emotional_arc={})
        result = extract_story_for_music(outline, _make_screenplay_simple())
        assert result["emotional_arc_opening"] == ""
        assert result["emotional_arc_midpoint"] == ""
        assert result["emotional_arc_climax"] == ""
        assert result["emotional_arc_resolution"] == ""


# ── B. emotional_arc str — 防御路径 ──────────────────────────────────────────


class TestEmotionalArcStrDefense:
    """emotional_arc 为 str 类型时不抛 AttributeError，fallback 到 opening"""

    def test_str_simple(self):
        """
        str 类型: 整体作为 opening fallback，其他字段留空。
        修复前：'str' object has no attribute 'get' → AttributeError
        修复后：正常运行，opening=str值，其他字段=''
        """
        outline = _make_outline(emotional_arc="romantic_journey")
        # 这行修复前会 AttributeError
        result = extract_story_for_music(outline, _make_screenplay_simple())
        # opening 从 str 中提取
        assert result["emotional_arc_opening"] == "romantic_journey"
        # 其余字段为空（str 没有这些 key）
        assert result["emotional_arc_midpoint"] == ""
        assert result["emotional_arc_climax"] == ""
        assert result["emotional_arc_resolution"] == ""

    def test_str_complex_narrative(self):
        """str 类型含多段描述 — 整体作为 opening"""
        outline = _make_outline(emotional_arc="从平静到冲突，最终走向释然")
        result = extract_story_for_music(outline, _make_screenplay_simple())
        assert result["emotional_arc_opening"] == "从平静到冲突，最终走向释然"
        assert result["emotional_arc_midpoint"] == ""

    def test_str_english_arrow_notation(self):
        """str 类型 LLM 常见 arrow 格式 — 整体作为 opening"""
        outline = _make_outline(emotional_arc="hopeful→tense→heartbreaking→cathartic")
        result = extract_story_for_music(outline, _make_screenplay_simple())
        assert "hopeful" in result["emotional_arc_opening"]
        assert result["emotional_arc_resolution"] == ""

    def test_str_empty_string(self):
        """空 str — opening 为空，其他字段也为空"""
        outline = _make_outline(emotional_arc="")
        result = extract_story_for_music(outline, _make_screenplay_simple())
        assert result["emotional_arc_opening"] == ""
        assert result["emotional_arc_midpoint"] == ""


# ── C. emotional_arc None/缺失 — 兜底路径 ────────────────────────────────────


class TestEmotionalArcNoneOrMissing:
    """emotional_arc 为 None 或完全缺失时返回空字符串"""

    def test_none_value(self):
        """None 值 — 4 字段全部返回空字符串"""
        outline = _make_outline(emotional_arc=None)
        result = extract_story_for_music(outline, _make_screenplay_simple())
        assert result["emotional_arc_opening"] == ""
        assert result["emotional_arc_midpoint"] == ""
        assert result["emotional_arc_climax"] == ""
        assert result["emotional_arc_resolution"] == ""

    def test_missing_field(self):
        """字段完全不存在 — outline 没有 emotional_arc key"""
        outline = {
            "title": "Test Story",
            "narrative_pace": "moderate",
            "visual_tone": {"overall_mood": "calm", "color_palette": []},
            "plot_points": [],
            "characters_overview": [],
            # 没有 emotional_arc 字段
        }
        result = extract_story_for_music(outline, _make_screenplay_simple())
        assert result["emotional_arc_opening"] == ""
        assert result["emotional_arc_midpoint"] == ""
        assert result["emotional_arc_climax"] == ""
        assert result["emotional_arc_resolution"] == ""

    def test_int_value(self):
        """int 类型 — 类型未知，兜底为空 dict，4 字段返回空字符串"""
        outline = _make_outline(emotional_arc=42)
        result = extract_story_for_music(outline, _make_screenplay_simple())
        assert result["emotional_arc_opening"] == ""
        assert result["emotional_arc_midpoint"] == ""
        assert result["emotional_arc_climax"] == ""
        assert result["emotional_arc_resolution"] == ""

    def test_list_value(self):
        """list 类型 — 类型未知，兜底为空 dict"""
        outline = _make_outline(emotional_arc=["opening", "midpoint"])
        result = extract_story_for_music(outline, _make_screenplay_simple())
        assert result["emotional_arc_opening"] == ""


# ── D. 源码验证: isinstance 防御代码存在 ──────────────────────────────────────


class TestSourceCodeDefensePattern:
    """验证 story_music_extractor.py 源码中确实有 emotional_arc isinstance 防御"""

    def test_isinstance_defense_in_source(self):
        """源码中有 isinstance(arc_raw, dict) 和 isinstance(arc_raw, str)"""
        import os
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "app", "services", "story_music_extractor.py"
        )
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        assert "isinstance(arc_raw, dict)" in source or "isinstance(arc_raw, dict" in source, (
            "story_music_extractor.py 应有 isinstance(arc_raw, dict) 防御 (RISK-T19-9)"
        )
        assert "isinstance(arc_raw, str)" in source or "isinstance(arc_raw, str" in source, (
            "story_music_extractor.py 应有 isinstance(arc_raw, str) 防御 (RISK-T19-9)"
        )

    def test_warning_log_for_str_type(self):
        """str 类型触发时有 logger.warning 日志"""
        import os
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "app", "services", "story_music_extractor.py"
        )
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        assert "emotional_arc 为 str 类型" in source, (
            "story_music_extractor.py 应有 emotional_arc str 类型的 warning 日志"
        )

    def test_t19_5_visual_tone_defense_still_present(self):
        """Wave 14 T19-5 修复 (visual_tone/atmosphere) 不被本次改动覆盖"""
        import os
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "app", "services", "story_music_extractor.py"
        )
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        # T19-5 的 visual_tone 防御
        assert "RISK-T19-5" in source, "T19-5 visual_tone 防御注释应保留"
        assert "isinstance(visual_tone_raw, dict)" in source, "visual_tone dict 防御应保留"
        # T19-9 的 emotional_arc 防御
        assert "RISK-T19-9" in source, "T19-9 emotional_arc 防御注释应存在"


# ─────────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    # 正常 dict
    t1 = TestEmotionalArcDictNormal()
    t1.test_full_dict()
    t1.test_partial_dict()
    t1.test_empty_dict()

    # str fallback
    t2 = TestEmotionalArcStrDefense()
    t2.test_str_simple()
    t2.test_str_complex_narrative()
    t2.test_str_english_arrow_notation()
    t2.test_str_empty_string()

    # None/缺失/未知
    t3 = TestEmotionalArcNoneOrMissing()
    t3.test_none_value()
    t3.test_missing_field()
    t3.test_int_value()
    t3.test_list_value()

    # 源码验证
    t4 = TestSourceCodeDefensePattern()
    t4.test_isinstance_defense_in_source()
    t4.test_warning_log_for_str_type()
    t4.test_t19_5_visual_tone_defense_still_present()

    print("All 15 test cases PASS!")
    import sys
    sys.exit(0)
