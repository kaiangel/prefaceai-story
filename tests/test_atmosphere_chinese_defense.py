"""
tests/test_atmosphere_chinese_defense.py

Wave 12 / RISK-T19-1: _atmosphere_to_str 中文防御单测

验证当 Stage 3 LLM 违规输出中文 atmosphere 时，
_atmosphere_to_str() 能正确跳过中文字段，只保留英文部分，
防止中文流入 image_prompt 导致 pipeline_schemas 验证失败。
"""

import pytest
from app.services.storyboard_director import _atmosphere_to_str, _contains_chinese


# ============================================================
# _contains_chinese 辅助函数测试
# ============================================================

class TestContainsChinese:
    """_contains_chinese 检测函数"""

    def test_pure_english_returns_false(self):
        assert _contains_chinese("distant bird calls, crisp footsteps") is False

    def test_chinese_string_returns_true(self):
        assert _contains_chinese("远山鸟鸣稀疏，踩雪声轻脆") is True

    def test_mixed_returns_true(self):
        assert _contains_chinese("tranquil, 远山鸟鸣") is True

    def test_empty_returns_false(self):
        assert _contains_chinese("") is False

    def test_numbers_and_punctuation_returns_false(self):
        assert _contains_chinese("123, 456. hello!") is False


# ============================================================
# _atmosphere_to_str 中文防御测试（Wave 12 新增 Case 11-14）
# ============================================================

class TestAtmosphereChineseDefense:
    """Wave 12 / RISK-T19-1 中文防御: dict 字段含中文时跳过，只输出英文"""

    def test_case11_dict_chinese_sound_skipped_english_mood_kept(self):
        """
        Case 11: dict 中 sound_design_hint 含中文 → 跳过，只保留英文 mood
        模拟 test19 真实失败: {mood: "tranquil", sound_design_hint: "远山鸟鸣稀疏..."}
        """
        atm = {
            "mood": "tranquil",
            "sound_design_hint": "远山鸟鸣稀疏，踩雪声轻脆，风过松枝沙沙作响",
            "temperature_feel": "凛冽中带一丝初春的微暖"
        }
        result = _atmosphere_to_str(atm)
        # mood (英文) 应保留
        assert "tranquil" in result
        # 中文字段应被跳过
        assert "远山" not in result
        assert "鸟鸣" not in result
        assert "凛冽" not in result
        # 结果不含中文字符
        assert not _contains_chinese(result)

    def test_case12_dict_all_chinese_except_mood_only_mood_returned(self):
        """
        Case 12: sound_design_hint 和 temperature_feel 均含中文 → 只保留英文 mood
        """
        atm = {
            "mood": "solemn",
            "sound_design_hint": "四周极静，偶有雪粒从枝头滑落的细碎声",
            "temperature_feel": "寒意深沉，静止的冷"
        }
        result = _atmosphere_to_str(atm)
        assert "solemn" in result
        assert "四周" not in result
        assert "寒意" not in result
        assert not _contains_chinese(result)

    def test_case13_str_with_chinese_only_english_prefix_kept(self):
        """
        Case 13: atmosphere 是混合字符串（实际 test19 格式）→ 提取英文 mood 前缀
        "tranquil, 远山鸟鸣稀疏..." → "tranquil"
        """
        atm = "tranquil, 远山鸟鸣稀疏，踩雪声轻脆，风过松枝沙沙作响, 凛冽中带一丝初春的微暖"
        result = _atmosphere_to_str(atm)
        # 应保留首段英文 "tranquil"
        assert "tranquil" in result
        # 不应包含中文
        assert "远山" not in result
        assert "凛冽" not in result
        assert not _contains_chinese(result)

    def test_case14_str_fully_chinese_returns_empty(self):
        """
        Case 14: atmosphere 完全是中文字符串 → 返回 "" (安全降级)
        """
        atm = "远山鸟鸣，踩雪声轻脆"
        result = _atmosphere_to_str(atm)
        assert result == ""
        assert not _contains_chinese(result)

    def test_case15_dict_mixed_english_temperature_kept(self):
        """
        Case 15: sound_design_hint 含中文但 temperature_feel 是英文 → 跳过前者，保留后者
        """
        atm = {
            "mood": "peaceful",
            "sound_design_hint": "树叶沙沙作响",
            "temperature_feel": "warm and humid"
        }
        result = _atmosphere_to_str(atm)
        assert "peaceful" in result
        assert "warm and humid" in result
        assert "树叶" not in result
        assert not _contains_chinese(result)

    def test_case16_fully_english_dict_unchanged(self):
        """
        Case 16: 全英文 dict (理想情况) → 正常拼接，行为与 Wave 10.1 一致
        这确保新防御逻辑没有破坏正常路径 (regression)
        """
        atm = {
            "mood": "mysterious",
            "sound_design_hint": "wind through bare branches, distant owl calls",
            "temperature_feel": "cold and clear"
        }
        result = _atmosphere_to_str(atm)
        assert "mysterious" in result
        assert "wind through bare branches" in result
        assert "cold and clear" in result
        assert not _contains_chinese(result)

    def test_case17_str_all_english_unchanged(self):
        """
        Case 17: 全英文 str → 原样返回，regression 保证
        """
        atm = "tense and atmospheric, heavy air"
        result = _atmosphere_to_str(atm)
        assert result == atm

    def test_case18_fallback_prompt_no_chinese_leakage(self):
        """
        Case 18: 端到端验证 — 含中文 atmosphere 不泄露到 fallback_image_prompt
        模拟 storyboard_director.py L656-659 的真实拼接逻辑
        (这是 test19 Pipeline failed 的实际代码路径)
        """
        atmosphere = {
            "mood": "tranquil",
            "sound_design_hint": "远山鸟鸣稀疏，踩雪声轻脆",
            "temperature_feel": "凛冽中带一丝初春的微暖"
        }
        atmosphere_str = _atmosphere_to_str(atmosphere)

        scene_heading = "EXT. MOUNTAIN PATH - DAWN"
        fallback_image_prompt = (
            f"Establishing shot of {scene_heading}. "
            f"{'Atmosphere: ' + atmosphere_str + '. ' if atmosphere_str else ''}"
            f"Wide angle, showing the environment and setting clearly. "
            f"No specific character interaction required."
        )

        # image_prompt 不应含中文
        assert not _contains_chinese(fallback_image_prompt), (
            f"image_prompt 含中文字符，会触发 pipeline_schemas 验证失败: {fallback_image_prompt[:100]}"
        )
        # mood (英文) 应出现
        assert "tranquil" in fallback_image_prompt


# ============================================================
# Wave 10.1 regression — 确保新防御不破坏原有容错逻辑
# ============================================================

class TestAtmosphereWave10Regression:
    """Wave 10.1 回归测试 — 新防御逻辑不破坏原有 10 个 case"""

    def test_regression_str_passthrough_english(self):
        result = _atmosphere_to_str("tense and atmospheric")
        assert result == "tense and atmospheric"

    def test_regression_dict_mood_only(self):
        atm = {"mood": "melancholic and heavy"}
        result = _atmosphere_to_str(atm)
        assert result == "melancholic and heavy"

    def test_regression_dict_all_english_fields(self):
        atm = {
            "mood": "tense",
            "sound_design_hint": "distant thunder",
            "temperature_feel": "cold and damp"
        }
        result = _atmosphere_to_str(atm)
        assert "tense" in result
        assert "distant thunder" in result
        assert "cold and damp" in result

    def test_regression_none_returns_empty(self):
        assert _atmosphere_to_str(None) == ""

    def test_regression_empty_dict_returns_empty(self):
        assert _atmosphere_to_str({}) == ""

    def test_regression_empty_string_returns_empty(self):
        assert _atmosphere_to_str("") == ""

    def test_regression_int_fallback(self):
        result = _atmosphere_to_str(42)
        assert result == "42"

    def test_regression_dict_partial_english_fields(self):
        atm = {"sound_design_hint": "rain on windows", "temperature_feel": "chilly"}
        result = _atmosphere_to_str(atm)
        assert "rain on windows" in result
        assert "chilly" in result

    def test_regression_dict_mood_none_value(self):
        atm = {"mood": None, "sound_design_hint": "soft piano music"}
        result = _atmosphere_to_str(atm)
        assert "soft piano music" in result
        assert "None" not in result
