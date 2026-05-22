"""
tests/test_shot_validator_universal_skip.py

RISK-T20-6 v2 (2026-05-18) — ShotValidator universal skip 智能判断单测

测试场景 (universal, 不依赖任何特定故事类型):
1. 角色数量检查 skip 智能化:
   - _is_fallback=True → 跳过
   - shot_type wide/establishing/environmental → 跳过
   - characters_in_scene 为空 → 跳过
   - image_prompt 含 "No characters" 等指令 → 跳过
   - 普通 close_up + 有 character → 仍检查
2. has_duplicate_bubbles 关闭:
   - thought bubble 不再被误判为重复对话气泡
   - 即使 vision LLM 返 has_duplicate_bubbles=True, valid 不再 False
3. 向后兼容: validate_shot 不传 shot 参数, 行为不变

注意: 这些测试不调真 Haiku API (用 mock), 验证纯 Python 逻辑.
"""

import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.shot_validator import (
    ShotValidator,
    should_skip_character_count_check,
    _PROMPT_NO_CHARACTER_HINTS,
    _SHOT_TYPE_ENVIRONMENTAL_KEYWORDS,
)
from PIL import Image


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def small_pil_image():
    """1x1 PNG image fixture for validator tests."""
    return Image.new("RGB", (10, 10), color="white")


def _make_mock_haiku_response(
    character_count: int = 2,
    has_duplicate_bubbles: bool = False,
    anatomy_severity: str = "none",
    anatomy_issues=None,
):
    """构造 Haiku 4.5 mock response JSON."""
    import json
    body = {
        "character_count": character_count,
        "has_duplicate_bubbles": has_duplicate_bubbles,
        "has_visual_unnaturalness": False,
        "unnaturalness_details": "",
        "anatomy_severity": anatomy_severity,
        "anatomy_issues": anatomy_issues or [],
    }
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text=json.dumps(body))]
    return mock_resp


# ═══════════════════════════════════════════════════════════════════
# Section 1: should_skip_character_count_check pure function tests
# ═══════════════════════════════════════════════════════════════════


class TestSkipCharacterCountCheck:
    """T20-6 v2: pure helper function 5+ universal cases"""

    def test_skip_check_for_fallback_shot(self):
        """_is_fallback=True 的 shot → 跳过"""
        shot = {
            "_is_fallback": True,
            "shot_type": "wide_shot",
            "characters_in_scene": ["char_001", "char_002"],
            "image_prompt": "EXACTLY 2 characters visible",
        }
        skip, reason = should_skip_character_count_check(shot)
        assert skip is True
        assert "fallback" in reason

    def test_skip_check_for_wide_shot_type(self):
        """shot_type='wide_shot' → 跳过"""
        shot = {
            "_is_fallback": False,
            "shot_type": "wide_shot",
            "characters_in_scene": ["char_001"],
            "image_prompt": "A scene with one character",
        }
        skip, reason = should_skip_character_count_check(shot)
        assert skip is True
        assert "wide" in reason

    def test_skip_check_for_establishing_shot(self):
        """shot_type='establishing_shot' → 跳过"""
        shot = {
            "shot_type": "establishing_shot",
            "characters_in_scene": ["char_001"],
        }
        skip, reason = should_skip_character_count_check(shot)
        assert skip is True
        assert "establishing" in reason

    def test_skip_check_for_environmental_shot(self):
        """shot_type='environmental' → 跳过"""
        shot = {
            "shot_type": "environmental_detail",
            "characters_in_scene": [],
        }
        skip, reason = should_skip_character_count_check(shot)
        assert skip is True

    def test_skip_check_for_no_character_prompt(self):
        """image_prompt 含 'No characters' → 跳过"""
        shot = {
            "shot_type": "close_up",  # 即使是 close_up
            "characters_in_scene": ["char_001"],  # 即使列了 char
            "image_prompt": "A wide angle scene. No characters are present in this shot. Pure environmental composition.",
        }
        skip, reason = should_skip_character_count_check(shot)
        assert skip is True
        assert "prompt_hint" in reason

    def test_skip_check_for_no_character_interaction_prompt(self):
        """image_prompt 含 'No specific character interaction' (legacy fallback prompt) → 跳过"""
        shot = {
            "shot_type": "medium_shot",
            "characters_in_scene": ["char_001"],
            "image_prompt": "Wide angle of the alley. No specific character interaction required. Atmosphere: tense.",
        }
        skip, reason = should_skip_character_count_check(shot)
        assert skip is True

    def test_skip_check_for_empty_characters_in_scene(self):
        """characters_in_scene 为 [] → 跳过 (作者意图无角色)"""
        shot = {
            "shot_type": "close_up",  # 即使是 close_up
            "characters_in_scene": [],
            "image_prompt": "A detail shot of a coffee cup on the table.",
        }
        skip, reason = should_skip_character_count_check(shot)
        assert skip is True
        assert "empty_characters" in reason

    def test_enforce_check_for_normal_close_up(self):
        """普通 close_up 含 character + 普通 prompt → 仍检查 (不跳过)"""
        shot = {
            "_is_fallback": False,
            "shot_type": "close_up",
            "characters_in_scene": ["char_001"],
            "image_prompt": "A close-up of Chen Mo's face, looking serious",
        }
        skip, reason = should_skip_character_count_check(shot)
        assert skip is False
        assert reason == ""

    def test_enforce_check_for_medium_shot_with_characters(self):
        """medium_shot + 角色存在 + 普通 prompt → 仍检查"""
        shot = {
            "shot_type": "medium_shot",
            "characters_in_scene": ["char_001", "char_002"],
            "image_prompt": "Two characters facing each other at a cafe table",
        }
        skip, reason = should_skip_character_count_check(shot)
        assert skip is False

    def test_skip_check_none_shot_returns_false(self):
        """shot=None (旧调用) → 不跳过 (向后兼容)"""
        skip, reason = should_skip_character_count_check(None)
        assert skip is False

    def test_skip_check_empty_dict_returns_false(self):
        """shot={} → 不跳过 (无 fallback/wide 信号)"""
        skip, reason = should_skip_character_count_check({})
        assert skip is False

    def test_skip_check_via_camera_shot_size(self):
        """通过 shot.camera.shot_size 也能识别 wide (Stage 4 输出位置)"""
        shot = {
            "shot_type": "",
            "camera": {"shot_size": "wide_shot", "angle": "eye_level"},
            "characters_in_scene": ["char_001"],
        }
        skip, reason = should_skip_character_count_check(shot)
        assert skip is True

    def test_universal_works_for_extreme_wide_shot(self):
        """extreme_wide_shot 也命中 'wide' keyword"""
        shot = {
            "shot_type": "extreme_wide_shot",
            "characters_in_scene": ["char_001"],
        }
        skip, reason = should_skip_character_count_check(shot)
        assert skip is True

    def test_universal_works_for_insert_shot(self):
        """insert_shot → 跳过 (一般是道具特写, 不强检角色数)"""
        shot = {
            "shot_type": "insert_shot",
            "characters_in_scene": [],
        }
        skip, reason = should_skip_character_count_check(shot)
        assert skip is True

    def test_universal_works_for_cutaway_shot(self):
        """cutaway_shot → 跳过"""
        shot = {
            "shot_type": "cutaway",
            "characters_in_scene": [],
        }
        skip, reason = should_skip_character_count_check(shot)
        assert skip is True


# ═══════════════════════════════════════════════════════════════════
# Section 2: validate_shot 集成测试 (mock Haiku response)
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestValidateShotUniversalSkip:
    """T20-6 v2: validate_shot 与 shot 参数集成 + has_duplicate_bubbles 禁用"""

    async def test_skip_when_shot_is_fallback_actual_zero(self, small_pil_image):
        """fallback shot 实际 0 角色 → valid=True (skip 生效, 不再 FAIL)"""
        # mock Haiku 返回 character_count=0 (Seedream 真的没画人)
        validator = ShotValidator()
        validator.client = MagicMock()
        validator.client.messages = MagicMock()
        validator.client.messages.create = AsyncMock(
            return_value=_make_mock_haiku_response(character_count=0)
        )

        fallback_shot = {
            "_is_fallback": True,
            "shot_type": "wide_shot",
            "characters_in_scene": ["char_001", "char_002"],
            "image_prompt": "Fallback wide shot",
        }

        result = await validator.validate_shot(
            pil_image=small_pil_image,
            expected_character_count=2,
            shot=fallback_shot,
        )
        # 应通过 (skip 生效)
        assert result["valid"] is True
        assert "角色数量" not in result["reason"]

    async def test_skip_when_wide_shot_actual_zero(self, small_pil_image):
        """wide_shot 实际 0 角色 → valid=True (skip 生效)"""
        validator = ShotValidator()
        validator.client = MagicMock()
        validator.client.messages = MagicMock()
        validator.client.messages.create = AsyncMock(
            return_value=_make_mock_haiku_response(character_count=0)
        )

        shot = {
            "_is_fallback": False,
            "shot_type": "wide_shot",
            "characters_in_scene": ["char_001"],
        }
        result = await validator.validate_shot(
            pil_image=small_pil_image,
            expected_character_count=1,
            shot=shot,
        )
        assert result["valid"] is True

    async def test_skip_when_no_character_prompt_actual_zero(self, small_pil_image):
        """prompt 含 'No characters' → valid=True (skip 生效)"""
        validator = ShotValidator()
        validator.client = MagicMock()
        validator.client.messages = MagicMock()
        validator.client.messages.create = AsyncMock(
            return_value=_make_mock_haiku_response(character_count=0)
        )

        shot = {
            "shot_type": "medium_shot",
            "characters_in_scene": ["char_001"],
            "image_prompt": "A close-up scene. No characters are present in this shot.",
        }
        result = await validator.validate_shot(
            pil_image=small_pil_image,
            expected_character_count=1,
            shot=shot,
        )
        assert result["valid"] is True

    async def test_enforce_when_normal_close_up_count_mismatch(self, small_pil_image):
        """普通 close_up + 角色数不匹配 → valid=False (skip 不触发)"""
        validator = ShotValidator()
        validator.client = MagicMock()
        validator.client.messages = MagicMock()
        validator.client.messages.create = AsyncMock(
            return_value=_make_mock_haiku_response(character_count=0)
        )

        shot = {
            "_is_fallback": False,
            "shot_type": "close_up",
            "characters_in_scene": ["char_001", "char_002"],
            "image_prompt": "A close-up of two characters facing each other.",
        }
        result = await validator.validate_shot(
            pil_image=small_pil_image,
            expected_character_count=2,
            shot=shot,
        )
        # 应失败 (普通 shot 严格检查)
        assert result["valid"] is False
        assert "角色数量" in result["reason"]

    async def test_duplicate_bubble_no_longer_triggers_fail(self, small_pil_image):
        """vision LLM 返 has_duplicate_bubbles=True → valid=True (检测已禁用)"""
        validator = ShotValidator()
        validator.client = MagicMock()
        validator.client.messages = MagicMock()
        validator.client.messages.create = AsyncMock(
            return_value=_make_mock_haiku_response(
                character_count=2,
                has_duplicate_bubbles=True,  # ⚠️ vision LLM 误判
            )
        )

        shot = {
            "_is_fallback": False,
            "shot_type": "medium_shot",
            "characters_in_scene": ["char_001", "char_002"],
            "image_prompt": "A normal scene",
        }
        result = await validator.validate_shot(
            pil_image=small_pil_image,
            expected_character_count=2,
            shot=shot,
        )
        # 应通过 (duplicate bubble 检测已禁用)
        assert result["valid"] is True
        # 字段仍返回 (backward compat)
        assert result["has_duplicate_bubbles"] is True
        # reason 不应含"重复对话气泡"
        assert "重复对话气泡" not in result["reason"]

    async def test_backward_compat_no_shot_param(self, small_pil_image):
        """旧调用 (不传 shot 参数) → 走原严格检查 (向后兼容)"""
        validator = ShotValidator()
        validator.client = MagicMock()
        validator.client.messages = MagicMock()
        validator.client.messages.create = AsyncMock(
            return_value=_make_mock_haiku_response(character_count=0)
        )

        # 不传 shot 参数 — 旧调用 (pipeline_orchestrator 当前还是这样)
        result = await validator.validate_shot(
            pil_image=small_pil_image,
            expected_character_count=2,
            text_overlay_data=None,
            key_props=None,
            # shot=None (默认)
        )
        # 应失败 (旧严格行为)
        assert result["valid"] is False
        assert "角色数量" in result["reason"]

    async def test_anatomy_severity_still_triggers_fail(self, small_pil_image):
        """anatomy_severity=severe 仍触发 retry (T20-6 不影响 B17 anatomy 检测)"""
        validator = ShotValidator()
        validator.client = MagicMock()
        validator.client.messages = MagicMock()
        validator.client.messages.create = AsyncMock(
            return_value=_make_mock_haiku_response(
                character_count=2,
                anatomy_severity="severe",
                anatomy_issues=["char_001: 3 hands visible"],
            )
        )

        shot = {
            "shot_type": "medium_shot",
            "characters_in_scene": ["char_001", "char_002"],
            "image_prompt": "Normal scene",
        }
        result = await validator.validate_shot(
            pil_image=small_pil_image,
            expected_character_count=2,
            shot=shot,
        )
        # anatomy severe 仍触发 fail
        assert result["valid"] is False
        assert "anatomy" in result["reason"].lower()


# ═══════════════════════════════════════════════════════════════════
# Section 3: 通用性验证 — 不 hardcode 任何故事类型
# ═══════════════════════════════════════════════════════════════════


class TestUniversal:
    """T20-6 v2: skip 规则对任何故事类型都生效"""

    def test_universal_works_for_ancient_story(self):
        """古装故事 — wide_shot 同样 skip"""
        shot = {
            "shot_type": "wide_shot",
            "characters_in_scene": ["jianke_01"],
            "image_prompt": "Ancient mountain temple at dawn, mist rising",
        }
        skip, _ = should_skip_character_count_check(shot)
        assert skip is True

    def test_universal_works_for_scifi_story(self):
        """科幻故事 — establishing 同样 skip"""
        shot = {
            "shot_type": "establishing_shot",
            "characters_in_scene": ["captain_01", "ai_droid"],
            "image_prompt": "Vast space station orbiting a blue planet",
        }
        skip, _ = should_skip_character_count_check(shot)
        assert skip is True

    def test_universal_works_for_school_drama(self):
        """校园故事 — close_up + character 不 skip (严格检查)"""
        shot = {
            "shot_type": "close_up",
            "characters_in_scene": ["xiaoyu"],
            "image_prompt": "Close-up of Xiaoyu's smiling face at the school gate",
        }
        skip, _ = should_skip_character_count_check(shot)
        assert skip is False

    def test_universal_works_for_anthropomorphic_animal(self):
        """拟人化动物故事 — fallback 同样 skip"""
        shot = {
            "_is_fallback": True,
            "shot_type": "medium_shot",  # 即使是 medium
            "characters_in_scene": ["grey_fox", "milly"],
            "image_prompt": "Two anthropomorphic animals in forest",
        }
        skip, reason = should_skip_character_count_check(shot)
        assert skip is True
        assert "fallback" in reason


# ═══════════════════════════════════════════════════════════════════
# Section 4: 配置常量自检
# ═══════════════════════════════════════════════════════════════════


class TestConstants:
    """T20-6 v2: 配置常量完整性自检"""

    def test_prompt_hints_lower_case(self):
        """所有 prompt hint 必须小写 (与 .lower() 匹配)"""
        for hint in _PROMPT_NO_CHARACTER_HINTS:
            assert hint == hint.lower(), f"hint 必须小写: {hint}"

    def test_shot_type_keywords_lower_case(self):
        """所有 shot_type keyword 必须小写"""
        for kw in _SHOT_TYPE_ENVIRONMENTAL_KEYWORDS:
            assert kw == kw.lower(), f"keyword 必须小写: {kw}"

    def test_prompt_hints_not_empty(self):
        """至少 5 个 prompt hint (覆盖常见 universal pattern)"""
        assert len(_PROMPT_NO_CHARACTER_HINTS) >= 5

    def test_shot_type_keywords_not_empty(self):
        """至少 3 个 shot_type keyword"""
        assert len(_SHOT_TYPE_ENVIRONMENTAL_KEYWORDS) >= 3


if __name__ == "__main__":
    import subprocess
    sys.exit(subprocess.call([sys.executable, "-m", "pytest", __file__, "-v"]))
