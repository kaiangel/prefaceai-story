"""
test_bgm_dict_str_defense.py — RISK-T19-5 BGM dict/str 双修单测

测试 story_music_extractor.extract_story_for_music() 对
  - visual_tone (outline 字段): dict / str / None / int 四种类型
  - atmosphere (scene 字段): dict / str / None / int 四种类型
的防御性处理，确保不再抛出 AttributeError (str.get() 不存在)。

Wave 14 / 2026-05-15
"""

import pytest
from app.services.story_music_extractor import extract_story_for_music


# ── 辅助函数 ──────────────────────────────────────────────────────────────


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


def _make_screenplay(atmosphere_value) -> dict:
    """构造含单 scene 的 screenplay，atmosphere 使用指定值。"""
    return {
        "scenes": [
            {
                "scene_id": 1,
                "atmosphere": atmosphere_value,
                "narration_tone": "gentle",
                "narration_pace": "slow",
                "narration": "The story begins.",
            }
        ]
    }


# ── A. visual_tone 4 case ─────────────────────────────────────────────────


class TestVisualToneDefense:
    """visual_tone 字段 isinstance 防御 — 4 case"""

    def test_visual_tone_dict_normal(self):
        """正常 dict 类型 — overall_mood + color_palette 正确提取。"""
        outline = _make_outline(
            visual_tone={
                "overall_mood": "bittersweet",
                "color_palette": ["warm amber", "pale birch"],
            }
        )
        result = extract_story_for_music(outline, {"scenes": []})
        assert result["overall_mood"] == "bittersweet"
        assert "warm amber" in result["color_palette"]
        assert "pale birch" in result["color_palette"]

    def test_visual_tone_str_fallback(self):
        """str 类型 — 不抛 AttributeError，整体作为 overall_mood。"""
        outline = _make_outline(visual_tone="melancholic")
        # 这行之前会 AttributeError: 'str' object has no attribute 'get'
        result = extract_story_for_music(outline, {"scenes": []})
        assert result["overall_mood"] == "melancholic"
        # color_palette 应为空字符串（str 类型的 visual_tone 没有 color_palette 字段）
        assert result["color_palette"] == ""

    def test_visual_tone_none_fallback(self):
        """None 类型 — 不抛错，overall_mood 和 color_palette 为空。"""
        outline = _make_outline(visual_tone=None)
        result = extract_story_for_music(outline, {"scenes": []})
        # None 走 else 分支 → visual_tone = {}
        assert result["overall_mood"] == ""
        assert result["color_palette"] == ""

    def test_visual_tone_int_fallback(self):
        """int 类型 (异常值) — 不抛错，字段为空。"""
        outline = _make_outline(visual_tone=42)
        result = extract_story_for_music(outline, {"scenes": []})
        assert result["overall_mood"] == ""
        assert result["color_palette"] == ""

    def test_visual_tone_dict_empty(self):
        """空 dict — 正常处理，overall_mood 为空。"""
        outline = _make_outline(visual_tone={})
        result = extract_story_for_music(outline, {"scenes": []})
        assert result["overall_mood"] == ""
        assert result["color_palette"] == ""

    def test_visual_tone_str_with_user_selected_mood_priority(self):
        """str visual_tone 时，user_selected_mood 仍优先于 visual_tone 内容。"""
        outline = _make_outline(visual_tone="hopeful")
        result = extract_story_for_music(
            outline, {"scenes": []}, user_selected_mood="joyful"
        )
        # user_selected_mood 优先级最高
        assert result["overall_mood"] == "joyful"


# ── B. atmosphere 4 case ──────────────────────────────────────────────────


class TestAtmosphereDefense:
    """atmosphere 字段 isinstance 防御 — 4 case"""

    def test_atmosphere_dict_normal(self):
        """正常 dict 类型 — mood / sound_design_hint / temperature_feel 正确提取。"""
        screenplay = _make_screenplay(
            {
                "mood": "tranquil",
                "sound_design_hint": "distant bird calls",
                "temperature_feel": "crisp and cold",
            }
        )
        result = extract_story_for_music(_make_outline(), screenplay, max_scenes=1)
        assert "Scene 1: tranquil" in result["scene_moods"]
        assert "distant bird calls" in result["sound_design_hints"]
        assert "crisp and cold" in result["temperature_feels"]

    def test_atmosphere_str_no_attribute_error(self):
        """str 类型 — 之前这里 AttributeError，现在不抛错。"""
        # 实际 test19 数据格式: "tranquil, 远山鸟鸣稀疏, 凛冽中带一丝初春的微暖"
        screenplay = _make_screenplay("tranquil, 远山鸟鸣稀疏, 凛冽中带一丝初春的微暖")
        result = extract_story_for_music(_make_outline(), screenplay, max_scenes=1)
        # 首段 "tranquil" 作为 mood
        assert "Scene 1: tranquil" in result["scene_moods"]
        # sound_design_hint / temperature_feel 来自 str → 空字符串，不进 parts
        assert result["sound_design_hints"] == ""
        assert result["temperature_feels"] == ""

    def test_atmosphere_str_english_only(self):
        """str 类型纯英文 — 首段正确解析为 mood。"""
        screenplay = _make_screenplay("solemn, very quiet, bone-chilling cold")
        result = extract_story_for_music(_make_outline(), screenplay, max_scenes=1)
        assert "Scene 1: solemn" in result["scene_moods"]

    def test_atmosphere_none_fallback(self):
        """None 类型 — 不抛错，该 scene 的 mood/hint/temp 全跳过。"""
        screenplay = _make_screenplay(None)
        result = extract_story_for_music(_make_outline(), screenplay, max_scenes=1)
        assert result["scene_moods"] == ""
        assert result["sound_design_hints"] == ""
        assert result["temperature_feels"] == ""

    def test_atmosphere_int_fallback(self):
        """int 类型 (异常值) — 不抛错，该 scene per-scene 字段全空。"""
        screenplay = _make_screenplay(999)
        result = extract_story_for_music(_make_outline(), screenplay, max_scenes=1)
        assert result["scene_moods"] == ""
        assert result["sound_design_hints"] == ""
        assert result["temperature_feels"] == ""

    def test_atmosphere_dict_empty(self):
        """空 dict — 正常处理，per-scene 字段全空 (没有值可提取)。"""
        screenplay = _make_screenplay({})
        result = extract_story_for_music(_make_outline(), screenplay, max_scenes=1)
        assert result["scene_moods"] == ""
        assert result["sound_design_hints"] == ""
        assert result["temperature_feels"] == ""


# ── C. 混合场景 (visual_tone=str + atmosphere=str 同时触发) ──────────────


class TestBothStrSimultaneously:
    """两个字段同时为 str — 验证双修协同工作。"""

    def test_both_str_no_error(self):
        """两处同时为 str 类型，不抛任何 AttributeError。"""
        outline = _make_outline(visual_tone="ethereal")
        screenplay = _make_screenplay("mysterious, distant wind, cold and damp")
        result = extract_story_for_music(outline, screenplay, max_scenes=1)
        # visual_tone str → overall_mood = "ethereal"
        assert result["overall_mood"] == "ethereal"
        # atmosphere str → mood = "mysterious"
        assert "Scene 1: mysterious" in result["scene_moods"]

    def test_return_dict_structure_intact(self):
        """即使两处都 str，返回 dict 的 19 个字段全部存在。"""
        outline = _make_outline(visual_tone="warm")
        screenplay = _make_screenplay("peaceful")
        result = extract_story_for_music(
            outline, screenplay, style_preset="ghibli", max_scenes=1
        )
        expected_keys = [
            "story_title", "narrative_pace", "overall_mood",
            "emotional_arc_opening", "emotional_arc_midpoint",
            "emotional_arc_climax", "emotional_arc_resolution",
            "color_palette", "sound_design_hints", "narration_tones",
            "narration_paces", "scene_moods", "temperature_feels",
            "full_narration", "visual_style_hint",
            "style_preset", "style_category", "setting_period",
            "character_dominant_type",
        ]
        for key in expected_keys:
            assert key in result, f"缺少字段: {key}"


# ── D. 回归：真实 test19 数据格式验证 ────────────────────────────────────


class TestRealDataRegression:
    """用实际 test19 数据格式验证防御逻辑。"""

    def test_real_test19_atmosphere_format(self):
        """
        test19 实际 atmosphere 格式 (Scene 1 真实值):
        "tranquil, 远山鸟鸣稀疏，踩雪声轻脆，风过松枝沙沙作响, 凛冽中带一丝初春的微暖"
        此格式之前导致 'str' object has no attribute 'get' → BGM 失败。
        """
        screenplay = {
            "scenes": [
                {
                    "scene_id": 1,
                    "atmosphere": "tranquil, 远山鸟鸣稀疏，踩雪声轻脆，风过松枝沙沙作响, 凛冽中带一丝初春的微暖",
                    "narration_tone": "reflective",
                    "narration_pace": "slow",
                    "narration": "立春这天，连山都安静下来。",
                },
                {
                    "scene_id": 2,
                    "atmosphere": "solemn, 四周极静，偶有雪粒从枝头滑落的细碎声，无风, 寒意深沉，静止的冷",
                    "narration_tone": "somber",
                    "narration_pace": "slow",
                    "narration": "她一个人站在白桦树下。",
                },
            ]
        }
        outline = _make_outline(
            visual_tone={
                "overall_mood": "感人",
                "color_palette": ["pale birch white", "warm amber gold"],
            }
        )
        # 必须不抛 AttributeError
        result = extract_story_for_music(outline, screenplay, max_scenes=6)
        # 两个 scene 的 mood 都被提取
        assert "Scene 1: tranquil" in result["scene_moods"]
        assert "Scene 2: solemn" in result["scene_moods"]
        # sound_design_hints 和 temperature_feels 对 str atmosphere 为空
        assert result["sound_design_hints"] == ""
        assert result["temperature_feels"] == ""
