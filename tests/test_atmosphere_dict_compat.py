"""
tests/test_atmosphere_dict_compat.py

Wave 10.1 / RISK-T17-6: atmosphere 字段容错单测

测试 _atmosphere_to_str() helper 的 5 个核心 case：
1. atmosphere = str        → 直接返回 str
2. atmosphere = dict {mood} → 返回 mood 字段
3. atmosphere = dict 含全部 3 字段 → 拼接
4. atmosphere = None       → 返回 ""
5. atmosphere = dict 空    → 返回 ""

额外 case:
6. atmosphere = int/other  → 兜底 str()
7. 全流程：_generate_scene_shots fallback prompt 不 TypeError
"""

import pytest
from app.services.storyboard_director import _atmosphere_to_str


class TestAtmosphereToStr:
    """_atmosphere_to_str 容错逻辑单测"""

    def test_case1_str_passthrough(self):
        """Case 1: atmosphere = str → 原样返回"""
        result = _atmosphere_to_str("tense and atmospheric")
        assert result == "tense and atmospheric"

    def test_case2_dict_mood_only(self):
        """Case 2: atmosphere = dict 含 mood → 返回 mood 字段"""
        atm = {"mood": "melancholic and heavy"}
        result = _atmosphere_to_str(atm)
        assert result == "melancholic and heavy"

    def test_case3_dict_all_fields(self):
        """Case 3: atmosphere = dict 含 mood + sound_design_hint + temperature_feel → 拼接"""
        atm = {
            "mood": "tense",
            "sound_design_hint": "distant thunder",
            "temperature_feel": "cold and damp"
        }
        result = _atmosphere_to_str(atm)
        # 三个字段都应出现，用 ", " 分隔
        assert "tense" in result
        assert "distant thunder" in result
        assert "cold and damp" in result
        # 分隔符
        assert ", " in result

    def test_case4_none_returns_empty(self):
        """Case 4: atmosphere = None → 返回 ""，保证 if atmosphere_str 分支不进入"""
        result = _atmosphere_to_str(None)
        assert result == ""

    def test_case5_empty_dict_returns_empty(self):
        """Case 5: atmosphere = {} (空 dict) -> 返回 empty str，不应拼出 Atmosphere: {}"""
        result = _atmosphere_to_str({})
        assert result == ""

    def test_case6_empty_string_returns_empty(self):
        """Case 6: atmosphere = "" → 返回 ""（falsy str）"""
        result = _atmosphere_to_str("")
        assert result == ""

    def test_case7_int_fallback(self):
        """Case 7: 非预期类型 int → 兜底 str() 转换，不 TypeError"""
        result = _atmosphere_to_str(42)
        assert result == "42"

    def test_case8_dict_partial_fields(self):
        """Case 8: dict 只有 sound_design_hint，没有 mood → 拼接非空字段"""
        atm = {"sound_design_hint": "rain on windows", "temperature_feel": "chilly"}
        result = _atmosphere_to_str(atm)
        assert "rain on windows" in result
        assert "chilly" in result

    def test_case9_fallback_prompt_no_type_error(self):
        """Case 9: 模拟 _generate_scene_shots fallback 拼接，dict atmosphere 不报 TypeError"""
        atmosphere = {
            "mood": "oppressive silence",
            "sound_design_hint": "cicadas in distance",
            "temperature_feel": "humid and suffocating"
        }
        atmosphere_str = _atmosphere_to_str(atmosphere)
        # 这是 storyboard_director.py L658 的实际拼接逻辑
        scene_heading = "INT. ABANDONED FACTORY - DAY"
        fallback_image_prompt = (
            f"Establishing shot of {scene_heading}. "
            f"{'Atmosphere: ' + atmosphere_str + '. ' if atmosphere_str else ''}"
            f"Wide angle, showing the environment and setting clearly. "
            f"No specific character interaction required."
        )
        # 不报 TypeError，且 atmosphere 信息有出现在 prompt 中
        assert "oppressive silence" in fallback_image_prompt
        assert "Atmosphere:" in fallback_image_prompt

    def test_case10_dict_mood_none_value(self):
        """Case 10: dict mood 字段值为 None → 跳过 None，用其他字段"""
        atm = {"mood": None, "sound_design_hint": "soft piano music"}
        result = _atmosphere_to_str(atm)
        assert "soft piano music" in result
        assert "None" not in result
