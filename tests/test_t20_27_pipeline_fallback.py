"""TASK-T20-FIXBATCH-5 Wave 4 Backend Wire — T20-27 Pipeline fallback 单元测试.

测试目标:
1. pipeline_orchestrator.py validate_storyboard 调用后,
   shots 中 text_overlay.chinese_text 为空 且 有出场角色 的 shot
   → 自动填充 narration_segment[:25] 作为 fallback overlay
2. 已有 text_overlay (非空) 的 shot 不被覆盖
3. 无出场角色的 shot 不触发 fallback
4. narration_segment 为空的 shot 不触发 fallback (不注入空 overlay)
5. test19 Shot 13 场景复现 (关键转折 overlay=None → fallback 填充)

不依赖 LLM API. 直接模拟 storyboard dict 验证 fallback 逻辑.

Usage:
    cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story
    python -m pytest tests/test_t20_27_pipeline_fallback.py -v
"""

import sys
import logging
from pathlib import Path
from typing import Any

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest

logger = logging.getLogger("xuhua")


# ========================================================================
# Helpers: reproduce the fallback logic from pipeline_orchestrator.py
# (inline copy for unit testing — source of truth is orchestrator)
# ========================================================================

def apply_t20_27_fallback(storyboard: dict) -> list[str]:
    """Mirror of the T20-27 loop in pipeline_orchestrator.py.

    Returns list of triggered shot_ids (for assertion convenience).
    """
    triggered: list[str] = []
    for _shot in storyboard.get("shots", []):
        _overlay = _shot.get("text_overlay") or {}
        _chinese_text = _overlay.get("chinese_text")
        _is_empty = (
            not _chinese_text
            or (isinstance(_chinese_text, str) and not _chinese_text.strip())
            or (isinstance(_chinese_text, list) and not any(s.strip() for s in _chinese_text if isinstance(s, str)))
        )
        if _shot.get("characters_in_scene") and _is_empty:
            _narration = (_shot.get("narration_segment") or "")[:25]
            if _narration:
                _shot["text_overlay"] = {
                    "text_type": "narration",
                    "chinese_text": _narration,
                    "speaker_position": "bottom",
                }
                triggered.append(str(_shot.get("shot_id", "?")))
    return triggered


# ========================================================================
# Section 1: 基本触发 — overlay 为 None 且有角色
# ========================================================================

class TestFallbackTriggers:
    """overlay 为空 + 有出场角色 → 触发 fallback."""

    def test_overlay_none_triggers_fallback(self):
        """text_overlay=None, characters_in_scene 非空 → fallback 填充."""
        sb = {
            "shots": [
                {
                    "shot_id": 1,
                    "characters_in_scene": ["char_001"],
                    "narration_segment": "他终于明白了一切，泪水无声滑落。",
                    "text_overlay": None,
                }
            ]
        }
        triggered = apply_t20_27_fallback(sb)
        assert triggered == ["1"], f"Expected shot 1 triggered, got {triggered}"
        overlay = sb["shots"][0]["text_overlay"]
        assert overlay is not None
        assert overlay["text_type"] == "narration"
        assert overlay["speaker_position"] == "bottom"
        assert len(overlay["chinese_text"]) <= 25

    def test_overlay_empty_dict_triggers_fallback(self):
        """text_overlay={}, characters_in_scene 非空 → fallback 填充."""
        sb = {
            "shots": [
                {
                    "shot_id": 2,
                    "characters_in_scene": ["char_001", "char_002"],
                    "narration_segment": "两人在雨中沉默对视。",
                    "text_overlay": {},
                }
            ]
        }
        triggered = apply_t20_27_fallback(sb)
        assert triggered == ["2"]
        overlay = sb["shots"][0]["text_overlay"]
        assert overlay["chinese_text"] == "两人在雨中沉默对视。"

    def test_overlay_empty_string_triggers_fallback(self):
        """chinese_text 为空字符串 → fallback 触发."""
        sb = {
            "shots": [
                {
                    "shot_id": 3,
                    "characters_in_scene": ["char_001"],
                    "narration_segment": "命运的转折点就在此刻。",
                    "text_overlay": {"text_type": "narration", "chinese_text": ""},
                }
            ]
        }
        triggered = apply_t20_27_fallback(sb)
        assert triggered == ["3"]

    def test_overlay_whitespace_only_triggers_fallback(self):
        """chinese_text 只有空白字符 → fallback 触发."""
        sb = {
            "shots": [
                {
                    "shot_id": 4,
                    "characters_in_scene": ["char_001"],
                    "narration_segment": "她低下头，不知所措。",
                    "text_overlay": {"text_type": "narration", "chinese_text": "   "},
                }
            ]
        }
        triggered = apply_t20_27_fallback(sb)
        assert triggered == ["4"]

    def test_overlay_empty_list_triggers_fallback(self):
        """chinese_text 是空列表 → fallback 触发."""
        sb = {
            "shots": [
                {
                    "shot_id": 5,
                    "characters_in_scene": ["char_001"],
                    "narration_segment": "战斗一触即发。",
                    "text_overlay": {"text_type": "dialogue", "chinese_text": []},
                }
            ]
        }
        triggered = apply_t20_27_fallback(sb)
        assert triggered == ["5"]


# ========================================================================
# Section 2: 不触发情形 — overlay 已有内容 / 无角色 / narration 为空
# ========================================================================

class TestFallbackNotTriggered:
    """各种不应触发 fallback 的情形."""

    def test_existing_overlay_not_overwritten(self):
        """已有非空 text_overlay → 不覆盖."""
        original_text = "我不会让你一个人面对的！"
        sb = {
            "shots": [
                {
                    "shot_id": 10,
                    "characters_in_scene": ["char_001"],
                    "narration_segment": "这是旁白内容不应被用来覆盖。",
                    "text_overlay": {
                        "text_type": "dialogue",
                        "chinese_text": original_text,
                        "speaker_position": "left",
                    },
                }
            ]
        }
        triggered = apply_t20_27_fallback(sb)
        assert triggered == [], f"Should not trigger, got {triggered}"
        assert sb["shots"][0]["text_overlay"]["chinese_text"] == original_text

    def test_no_characters_no_fallback(self):
        """characters_in_scene 为空 → 不触发 fallback."""
        sb = {
            "shots": [
                {
                    "shot_id": 11,
                    "characters_in_scene": [],
                    "narration_segment": "天空中乌云密布。",
                    "text_overlay": None,
                }
            ]
        }
        triggered = apply_t20_27_fallback(sb)
        assert triggered == []
        assert sb["shots"][0]["text_overlay"] is None

    def test_no_characters_field_no_fallback(self):
        """characters_in_scene 字段缺失 → 不触发 fallback."""
        sb = {
            "shots": [
                {
                    "shot_id": 12,
                    "narration_segment": "远处的山峦连绵起伏。",
                    "text_overlay": None,
                }
            ]
        }
        triggered = apply_t20_27_fallback(sb)
        assert triggered == []

    def test_empty_narration_no_fallback(self):
        """narration_segment 为空 → 即使 overlay 空且有角色, 也不注入空 overlay."""
        sb = {
            "shots": [
                {
                    "shot_id": 13,
                    "characters_in_scene": ["char_001"],
                    "narration_segment": "",
                    "text_overlay": None,
                }
            ]
        }
        triggered = apply_t20_27_fallback(sb)
        assert triggered == [], "Should not inject empty narration"
        assert sb["shots"][0]["text_overlay"] is None

    def test_none_narration_no_fallback(self):
        """narration_segment=None → 不注入."""
        sb = {
            "shots": [
                {
                    "shot_id": 14,
                    "characters_in_scene": ["char_001"],
                    "narration_segment": None,
                    "text_overlay": None,
                }
            ]
        }
        triggered = apply_t20_27_fallback(sb)
        assert triggered == []


# ========================================================================
# Section 3: narration 截断 ≤25 字
# ========================================================================

class TestNarrationTruncation:
    """fallback 文本必须截断到 ≤25 字."""

    def test_long_narration_truncated_to_25(self):
        """narration > 25 字 → fallback chinese_text ≤ 25 字."""
        long_narration = "这是一段非常长的旁白文字，超过了二十五个字的上限，需要被截断处理。"
        assert len(long_narration) > 25, "Test data setup: narration must be > 25 chars"
        sb = {
            "shots": [
                {
                    "shot_id": 20,
                    "characters_in_scene": ["char_001"],
                    "narration_segment": long_narration,
                    "text_overlay": None,
                }
            ]
        }
        triggered = apply_t20_27_fallback(sb)
        assert triggered == ["20"]
        filled = sb["shots"][0]["text_overlay"]["chinese_text"]
        assert len(filled) <= 25, f"Expected ≤25 chars, got {len(filled)}: {filled!r}"
        assert filled == long_narration[:25]

    def test_short_narration_not_truncated(self):
        """narration ≤ 25 字 → fallback chinese_text 完整保留."""
        short = "命运转折。"
        sb = {
            "shots": [
                {
                    "shot_id": 21,
                    "characters_in_scene": ["char_001"],
                    "narration_segment": short,
                    "text_overlay": None,
                }
            ]
        }
        triggered = apply_t20_27_fallback(sb)
        assert triggered == ["21"]
        filled = sb["shots"][0]["text_overlay"]["chinese_text"]
        assert filled == short


# ========================================================================
# Section 4: 多 shot 混合场景
# ========================================================================

class TestMixedShots:
    """多个 shot 的混合场景 — 只有符合条件的触发."""

    def test_mixed_storyboard_only_empty_overlay_triggered(self):
        """3 shots: 1 有 overlay, 1 无角色, 1 空 overlay + 有角色 → 只触发第 3 个."""
        sb = {
            "shots": [
                {
                    "shot_id": 30,
                    "characters_in_scene": ["char_001"],
                    "narration_segment": "已有覆层。",
                    "text_overlay": {"text_type": "dialogue", "chinese_text": "我来了！"},
                },
                {
                    "shot_id": 31,
                    "characters_in_scene": [],
                    "narration_segment": "风景空镜。",
                    "text_overlay": None,
                },
                {
                    "shot_id": 32,
                    "characters_in_scene": ["char_001", "char_002"],
                    "narration_segment": "两人终于重逢，泪眼相望。",
                    "text_overlay": None,
                },
            ]
        }
        triggered = apply_t20_27_fallback(sb)
        assert triggered == ["32"], f"Only shot 32 should trigger, got {triggered}"
        # shot 30: overlay unchanged
        assert sb["shots"][0]["text_overlay"]["chinese_text"] == "我来了！"
        # shot 31: still None (no chars)
        assert sb["shots"][1]["text_overlay"] is None
        # shot 32: filled from narration
        assert sb["shots"][2]["text_overlay"]["chinese_text"] == "两人终于重逢，泪眼相望。"

    def test_multiple_empty_shots_all_triggered(self):
        """3 shots 全部符合条件 → 全部填充."""
        sb = {
            "shots": [
                {
                    "shot_id": i,
                    "characters_in_scene": ["char_001"],
                    "narration_segment": f"第{i}场旁白文字。",
                    "text_overlay": None,
                }
                for i in [40, 41, 42]
            ]
        }
        triggered = apply_t20_27_fallback(sb)
        assert set(triggered) == {"40", "41", "42"}
        for shot in sb["shots"]:
            assert shot["text_overlay"] is not None
            assert shot["text_overlay"]["text_type"] == "narration"
            assert shot["text_overlay"]["speaker_position"] == "bottom"


# ========================================================================
# Section 5: test19 Shot 13 复现 (关键转折 overlay=None)
# ========================================================================

class TestTest19Shot13Reproduction:
    """test19 实证: Shot 13 (认出关键物证) text_overlay=None → fallback 填充."""

    def test_test19_shot13_critical_turn_fallback(self):
        """模拟 test19 Shot 13 的实际数据结构."""
        # Shot 13: 陈砚认出独眼鸦胸前的玉佩正是失踪弟弟之物 — 关键转折
        sb = {
            "shots": [
                {
                    "shot_id": 13,
                    "characters_in_scene": ["char_001", "char_003"],  # 陈砚 + 独眼鸦
                    "narration_segment": "玉佩在烛光下闪烁，那正是他弟弟的信物。",
                    "image_prompt": "Close-up of jade pendant glowing under candlelight...",
                    "text_overlay": None,  # Bug: LLM 遗漏了关键转折 overlay
                }
            ]
        }
        triggered = apply_t20_27_fallback(sb)
        assert triggered == ["13"], "Shot 13 (关键转折) should trigger fallback"
        overlay = sb["shots"][0]["text_overlay"]
        assert overlay is not None, "Fallback should inject overlay"
        assert overlay["text_type"] == "narration"
        assert overlay["speaker_position"] == "bottom"
        # chinese_text should be first ≤25 chars of narration_segment
        expected = "玉佩在烛光下闪烁，那正是他弟弟的信物。"
        assert len(expected) <= 25, "Test narration is within 25 chars"
        assert overlay["chinese_text"] == expected


# ========================================================================
# Section 6: fallback overlay schema 完整性
# ========================================================================

class TestFallbackSchema:
    """fallback 注入的 overlay 字段结构必须完整."""

    def test_fallback_overlay_has_required_fields(self):
        """fallback overlay 必须有 text_type, chinese_text, speaker_position."""
        sb = {
            "shots": [
                {
                    "shot_id": 50,
                    "characters_in_scene": ["char_001"],
                    "narration_segment": "最后的决战开始了。",
                    "text_overlay": None,
                }
            ]
        }
        apply_t20_27_fallback(sb)
        overlay = sb["shots"][0]["text_overlay"]
        assert "text_type" in overlay, "Missing text_type"
        assert "chinese_text" in overlay, "Missing chinese_text"
        assert "speaker_position" in overlay, "Missing speaker_position"

    def test_fallback_text_type_is_narration(self):
        """fallback text_type 固定为 narration."""
        sb = {
            "shots": [
                {
                    "shot_id": 51,
                    "characters_in_scene": ["char_001"],
                    "narration_segment": "他握紧了拳头。",
                    "text_overlay": None,
                }
            ]
        }
        apply_t20_27_fallback(sb)
        assert sb["shots"][0]["text_overlay"]["text_type"] == "narration"

    def test_fallback_speaker_position_is_bottom(self):
        """fallback speaker_position 固定为 bottom."""
        sb = {
            "shots": [
                {
                    "shot_id": 52,
                    "characters_in_scene": ["char_001"],
                    "narration_segment": "这一天终于来了。",
                    "text_overlay": None,
                }
            ]
        }
        apply_t20_27_fallback(sb)
        assert sb["shots"][0]["text_overlay"]["speaker_position"] == "bottom"
