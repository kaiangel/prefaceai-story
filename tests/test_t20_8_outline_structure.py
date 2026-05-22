"""RISK-T20-8 (2026-05-18) — Outline structure tests

测试:
1. ending_options 的 id + ending_id 双字段 normalization (兜底防御 LLM 漏写)
2. confirm_outline UX-2 prompt 含 R6-2 设计说明 (避免 false positive)
3. universal — 任何故事 (3 ending / 5 ending / 任何 mood) 都不再 false positive
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


# ---------------------------------------------------------------------------
# 1. ending_options normalization (universal 兜底)
# ---------------------------------------------------------------------------

class TestEndingOptionsNormalization:
    """RISK-T20-8.2: LLM 漏写 id / ending_id 时 backend 兜底补全"""

    def _get_validator(self):
        from app.services.story_outline_generator import StoryOutlineGenerator
        gen = StoryOutlineGenerator()
        return gen._validate_outline

    def _minimum_valid_outline(self) -> dict:
        """构造最小合法 outline (用于跑 _validate_outline)"""
        return {
            "title": "测试",
            "logline": "test",
            "emotional_arc": {"opening": "a", "midpoint": "b", "climax": "c", "resolution": "d"},
            "narrative_pace": "steady",
            "visual_tone": {
                "overall_mood": "warm",
                "lighting_style": "natural",
                "color_palette": ["white", "blue", "grey"],
            },
            "characters_overview": [{"name": "test"}],
            "plot_points": [
                {"beat": "inciting_incident", "description": "x", "estimated_duration_seconds": 30}
            ],
            "unique_locations": [{"location_id": "loc_1", "display_name": "test"}],
        }

    def test_ending_with_only_id_gets_ending_id_added(self):
        """LLM 只输出 id, 兜底自动加 ending_id"""
        outline = self._minimum_valid_outline()
        outline["ending_options"] = [
            {"id": "ending_1", "description": "happy"},
            {"id": "ending_2", "description": "sad"},
        ]
        self._get_validator()(outline, min_shots=10)
        for ending in outline["ending_options"]:
            assert "id" in ending and "ending_id" in ending
            assert ending["id"] == ending["ending_id"]

    def test_ending_with_only_ending_id_gets_id_added(self):
        """LLM 只输出 ending_id, 兜底自动加 id"""
        outline = self._minimum_valid_outline()
        outline["ending_options"] = [
            {"ending_id": "ending_1", "description": "happy"},
            {"ending_id": "ending_2", "description": "sad"},
        ]
        self._get_validator()(outline, min_shots=10)
        for ending in outline["ending_options"]:
            assert "id" in ending and "ending_id" in ending
            assert ending["id"] == ending["ending_id"]

    def test_ending_with_neither_id_gets_default(self):
        """LLM 漏写两个字段, 兜底 ending_{i+1}"""
        outline = self._minimum_valid_outline()
        outline["ending_options"] = [
            {"description": "happy"},
            {"description": "sad"},
            {"description": "twist"},
        ]
        self._get_validator()(outline, min_shots=10)
        assert outline["ending_options"][0]["id"] == "ending_1"
        assert outline["ending_options"][0]["ending_id"] == "ending_1"
        assert outline["ending_options"][1]["id"] == "ending_2"
        assert outline["ending_options"][2]["id"] == "ending_3"

    def test_ending_with_both_fields_preserved(self):
        """LLM 输出完整, 不修改"""
        outline = self._minimum_valid_outline()
        outline["ending_options"] = [
            {"id": "custom_a", "ending_id": "custom_a", "description": "x"},
        ]
        self._get_validator()(outline, min_shots=10)
        assert outline["ending_options"][0]["id"] == "custom_a"
        assert outline["ending_options"][0]["ending_id"] == "custom_a"

    def test_ending_options_missing_no_crash(self):
        """outline 完全没 ending_options 字段也不应崩"""
        outline = self._minimum_valid_outline()
        # 不加 ending_options
        # 不应抛任何异常
        self._get_validator()(outline, min_shots=10)

    def test_universal_5_endings_long_form(self):
        """中长篇可能 5 endings — universal"""
        outline = self._minimum_valid_outline()
        outline["ending_options"] = [
            {"description": f"ending {i}"} for i in range(1, 6)
        ]
        self._get_validator()(outline, min_shots=30)
        for i, e in enumerate(outline["ending_options"], start=1):
            assert e["id"] == f"ending_{i}"
            assert e["ending_id"] == f"ending_{i}"


# ---------------------------------------------------------------------------
# 2. UX-2 prompt 含 R6-2 说明 (避免 false positive)
# ---------------------------------------------------------------------------

class TestUX2PromptIncludesR62Design:
    """RISK-T20-8.1: confirm_outline UX-2 一致性检查 prompt 必须告诉 LLM R6-2"""

    def test_ux2_prompt_mentions_r62_design(self):
        """grep projects.py 源代码确认 prompt 包含 R6-2 关键词"""
        with open(
            os.path.join(os.path.dirname(__file__), "..", "app", "api", "projects.py"),
            "r",
            encoding="utf-8",
        ) as f:
            src = f.read()
        # 关键字必须出现在 confirm_outline UX-2 prompt 中
        assert "R6-2" in src, "UX-2 prompt 必须含 R6-2 设计标识"
        assert "plot_points 末尾" in src, "UX-2 prompt 必须解释 selected_ending 追加到 plot_points 末尾"
        assert "plot_points[-1]" in src, "UX-2 prompt 必须告诉 LLM 检查 plot_points[-1] 而非 selected_ending"

    def test_ux2_prompt_explicit_negative_rule(self):
        """prompt 必须明确说"不要因为 selected_ending 空就 warning" """
        with open(
            os.path.join(os.path.dirname(__file__), "..", "app", "api", "projects.py"),
            "r",
            encoding="utf-8",
        ) as f:
            src = f.read()
        # 明确的负面规则
        assert "selected_ending 为空" in src or "selected_ending 为空字符串" in src
        assert "不要" in src  # 至少一处 "不要" 限制规则


# ---------------------------------------------------------------------------
# 3. Universal — 不依赖具体故事 (test18 / 任何 idea)
# ---------------------------------------------------------------------------

class TestUniversalNoTest18Hardcode:
    """RISK-T20-8 修复不应 hardcode test18 — 应 universal"""

    def test_outline_validator_works_any_story_type(self):
        """3 不同 mood + ending count → 都通过 normalization"""
        from app.services.story_outline_generator import StoryOutlineGenerator
        gen = StoryOutlineGenerator()

        stories = [
            ("浪漫", 3),
            ("悬疑", 5),
            ("幽默", 3),
        ]
        for mood, n_endings in stories:
            outline = {
                "title": f"{mood}故事",
                "logline": "test",
                "emotional_arc": {
                    "opening": "a", "midpoint": "b", "climax": "c", "resolution": "d"
                },
                "narrative_pace": "steady",
                "visual_tone": {
                    "overall_mood": "warm" if mood == "浪漫" else (
                        "mysterious" if mood == "悬疑" else "comedic"
                    ),
                    "lighting_style": "natural",
                    "color_palette": ["white", "blue", "grey"],
                },
                "characters_overview": [{"name": "test"}],
                "plot_points": [
                    {"beat": "inciting_incident", "description": "x", "estimated_duration_seconds": 30}
                ],
                "unique_locations": [{"location_id": "loc_1", "display_name": "test"}],
                "ending_options": [{"description": f"ending {i}"} for i in range(1, n_endings + 1)],
            }
            gen._validate_outline(outline, min_shots=10)
            # 验证 normalization 兜底
            for i, e in enumerate(outline["ending_options"], start=1):
                assert e.get("id") == f"ending_{i}", \
                    f"{mood} story ending {i}: id 不正确 = {e}"
                assert e.get("ending_id") == f"ending_{i}", \
                    f"{mood} story ending {i}: ending_id 不正确 = {e}"
