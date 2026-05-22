"""
tests/test_b51_fallback_uses_screenplay.py

RISK-T20-7 + T20-1 + T20-4 (2026-05-18) — B51 fallback screenplay-aware 单测

验证点 (universal — 不依赖任何特定故事类型):
1. fallback prompt 含 action_beats[0] 的关键元素（emotional_note / english_action）
2. fallback prompt 提及 characters_in_scene 中的角色（英文 name_en）
3. fallback prompt 不含旧的 "No specific character interaction required" 指令
4. fallback prompt 全英文（无中文字符）
5. 同 location 两次 fallback 输出差异化（不同 angle / focus）
6. anti-empty-shots 硬约束在 _build_scene_prompt 输出中存在
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.storyboard_director import (
    _contains_chinese,
    _atmosphere_to_str,
    _extract_english_from_field,
    _extract_narration_keywords,
    _extract_action_beats_english,
    _build_character_descriptors,
    build_screenplay_aware_fallback_prompt,
    _FALLBACK_ANGLE_VARIANTS,
    _build_chinese_translation_request,
    _sanitize_llm_translation,
    StoryboardDirector,
)
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


# ═══════════════════════════════════════════════════════════════════
# Fixtures: test18 真实数据（雨夜冲突场景 + 多角色）
# 同时覆盖 anthropomorphic_animal + ancient/sci-fi 通用场景
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def test18_characters():
    """test18 真实 3 角色数据（陈默 / 林晓雨 / 方木）"""
    return {
        "characters": [
            {
                "id": "char_001",
                "name": "陈默",
                "name_en": "Chen Mo",
                "character_type": "human",
                "clothing": {
                    "top": "dark plaid shirt",
                    "bottom": "dark trousers",
                },
            },
            {
                "id": "char_002",
                "name": "林晓雨",
                "name_en": "Lin Xiaoyu",
                "character_type": "human",
                "clothing": {
                    "top": "soft oatmeal-ivory ribbed knit sweater, slightly oversized",
                    "bottom": "light stone-grey wide-leg casual trousers, cropped just above the ankle",
                },
            },
            {
                "id": "char_003",
                "name": "方木",
                "name_en": "Fang Mu",
                "character_type": "human",
                "clothing": {
                    "top": "forest green and navy blue large-check flannel overshirt",
                    "bottom": "dark charcoal jogger-style chinos, relaxed fit",
                },
            },
        ]
    }


@pytest.fixture
def anthropomorphic_characters():
    """通用 anthropomorphic_animal 角色（验证非 human 类型也 work）"""
    return {
        "characters": [
            {
                "id": "char_001",
                "name": "灰狐",
                "name_en": "Grey Fox",
                "character_type": "anthropomorphic_animal",
                "clothing": {
                    # 纯中文 → 应被过滤
                    "top": "一件手工缝制的藕灰色棉麻小褂",
                    "bottom": "宽松棉麻长裙",
                },
            },
            {
                "id": "char_002",
                "name": "米莉",
                "name_en": "Milly",
                "character_type": "anthropomorphic_animal",
                "clothing": {
                    "top": "light blue knit top",  # 英文，应保留
                    "bottom": "white shorts",
                },
            },
        ]
    }


@pytest.fixture
def scene_rainy_night_conflict():
    """test18 Scene 4 — 雨夜对峙（含 2 角色 + 中文 action_beats + 中文 narration）"""
    return {
        "scene_id": 4,
        "scene_heading": "EXT. Alley entrance of Chen Mo's rental building - Late night - rain",
        "location_id": "rainy_night_alley_entrance",
        "atmosphere": (
            "confrontational, heavy rain on pavement, door hinge creaking open, "
            "water dripping from eaves in uneven rhythm, cold and wet, "
            "rain-soaked air with a metallic edge"
        ),
        "characters_in_scene": ["char_001", "char_002"],
        "action_beats": [
            {
                "beat_id": "4a",
                "action": "林晓雨站在楼道口外的屋檐下，雨水顺着屋檐边缘滴成一道水帘",
                "emotional_note": "tense and watchful",
                "duration_hint": 7,
            },
            {
                "beat_id": "4b",
                "action": "陈默的脚步骤然停住，眼神里有一瞬间的慌乱",
                "emotional_note": "shocked, panicked",
                "duration_hint": 5,
            },
        ],
        "narration": (
            "雨水顺着屋檐滴落成帘，林晓雨站在那道水帘之外，衣肩已经濡湿了一片。"
            "She just raised her phone, fingers hovering. The iron gate of the corridor "
            "pushed open with a heavy metallic clang. Chen Mo appeared in the doorway."
        ),
    }


@pytest.fixture
def scene_same_location_2():
    """test18 Scene 6 — 同 location 第二个 scene（雨夜分手）"""
    return {
        "scene_id": 6,
        "scene_heading": "EXT. Alley entrance of Chen Mo's rental building - Late night - heavy rain",
        "location_id": "rainy_night_alley_entrance",  # 同上一个 fixture
        "atmosphere": (
            "devastated, rain suddenly heavier, water rushing along gutters, "
            "two people breathing in the downpour"
        ),
        "characters_in_scene": ["char_001", "char_002"],
        "action_beats": [
            {
                "beat_id": "6a",
                "action": "林晓雨深吸一口气，将手机缓缓收回",
                "emotional_note": "resolved, heartbroken",
                "duration_hint": 6,
            }
        ],
        "narration": "林晓雨深吸了一口气。",
    }


@pytest.fixture
def scene_same_location_3():
    """test18 Scene 9 — 同 location 第三个 scene"""
    return {
        "scene_id": 9,
        "scene_heading": "EXT. Alley entrance of Chen Mo's rental building - Late night - heavy rain",
        "location_id": "rainy_night_alley_entrance",
        "atmosphere": "overwhelming and tender, rain pouring steadily",
        "characters_in_scene": ["char_001", "char_002"],
        "action_beats": [
            {
                "beat_id": "9a",
                "action": "林晓雨接过那张对折的A4纸，手微微发抖",
                "emotional_note": "moved, breathless",
                "duration_hint": 7,
            }
        ],
        "narration": "那张纸在雨里微微洇湿。",
    }


@pytest.fixture
def scene_pure_environmental():
    """通用 — 纯环境场景（无角色）— 验证 fallback 适应 0 角色情况"""
    return {
        "scene_id": 1,
        "scene_heading": "EXT. Old town square - Dawn - mist",
        "location_id": "old_town_square",
        "atmosphere": "still, foggy, peaceful",
        "characters_in_scene": [],  # 无角色
        "action_beats": [
            {
                "beat_id": "1a",
                "action": "mist drifts across the empty cobblestones",
                "emotional_note": "serene",
            }
        ],
        "narration": "The town wakes slowly under the silver fog.",
    }


@pytest.fixture
def director():
    """无 API client 的 StoryboardDirector 实例（用于 prompt 构建测试）"""
    d = StoryboardDirector.__new__(StoryboardDirector)
    d.claude_client = None
    d.gemini_client = None
    d.claude_model = "claude-sonnet-4-6"
    d.gemini_model = "gemini-3.1-flash-lite-preview"
    return d


# ═══════════════════════════════════════════════════════════════════
# Section 1: 核心 helper 函数测试
# ═══════════════════════════════════════════════════════════════════


class TestHelperFunctions:
    """验证 RISK-T20-7 新增的 3 个 helper 函数"""

    def test_extract_narration_keywords_pure_chinese_returns_empty(self):
        """纯中文 narration → 返回 [] (复用现有英文提取逻辑)"""
        nar = "她本是随手划着屏幕，却在那一刻，手指像被什么钉住了。"
        result = _extract_narration_keywords(nar)
        assert result == []

    def test_extract_narration_keywords_bilingual_returns_english_only(self):
        """中英混合 narration → 提取英文片段"""
        nar = (
            "她站在屋檐下。She just raised her phone. "
            "陈默出现在门口。The iron gate opened with a clang."
        )
        result = _extract_narration_keywords(nar, max_keywords=3)
        # 至少包含 1 个英文片段
        assert len(result) >= 1
        # 都不含中文
        for kw in result:
            assert not _contains_chinese(kw), f"keyword 不应含中文: {kw}"

    def test_extract_narration_keywords_empty_input(self):
        """空 narration → 空列表"""
        assert _extract_narration_keywords("") == []
        assert _extract_narration_keywords(None) == []

    def test_extract_action_beats_english_extracts_emotional_note(self, scene_rainy_night_conflict):
        """action_beats 提取 emotional_note 英文字段"""
        beats = scene_rainy_night_conflict["action_beats"]
        result = _extract_action_beats_english(beats, max_beats=2)
        assert len(result) == 2
        # Beat 1 emotional_note
        assert result[0]["emotional_note"] == "tense and watchful"
        # Beat 2 emotional_note
        assert result[1]["emotional_note"] == "shocked, panicked"
        # action 是中文 → english_action 应为空
        assert result[0]["english_action"] == ""

    def test_extract_action_beats_chinese_emotional_note_filtered(self):
        """emotional_note 含中文 → 过滤"""
        beats = [
            {"beat_id": "1a", "action": "test", "emotional_note": "紧张的"},
            {"beat_id": "1b", "action": "test", "emotional_note": "tense"},
        ]
        result = _extract_action_beats_english(beats)
        assert result[0]["emotional_note"] == ""  # 中文已过滤
        assert result[1]["emotional_note"] == "tense"

    def test_build_character_descriptors_uses_name_en(self, test18_characters):
        """角色描述符使用 name_en，不用中文 name"""
        result = _build_character_descriptors(["char_001", "char_002"], test18_characters)
        assert len(result) == 2
        assert result[0]["name_en"] == "Chen Mo"
        assert result[1]["name_en"] == "Lin Xiaoyu"
        # 不应含中文 name
        for d in result:
            assert not _contains_chinese(d["name_en"]), \
                f"descriptor name_en 不应含中文: {d}"

    def test_build_character_descriptors_filters_chinese_clothing(
        self, anthropomorphic_characters
    ):
        """角色 clothing 含中文 → _extract_english_from_field 过滤"""
        result = _build_character_descriptors(
            ["char_001", "char_002"], anthropomorphic_characters
        )
        # char_001 clothing 是纯中文 → clothing 应为空字符串
        assert result[0]["clothing"] == ""
        # char_002 clothing 是英文 → 应保留
        assert "light blue knit top" in result[1]["clothing"]
        assert "white shorts" in result[1]["clothing"]
        # 无中文泄露
        for d in result:
            assert not _contains_chinese(d["clothing"]), \
                f"descriptor clothing 不应含中文: {d}"

    def test_build_character_descriptors_unknown_char_id_does_not_crash(self):
        """角色 id 不在 characters.json → 占位不崩"""
        chars = {"characters": []}
        result = _build_character_descriptors(["char_999"], chars)
        assert len(result) == 1
        assert result[0]["id"] == "char_999"
        assert result[0]["name_en"] == "char_999"

    def test_build_character_descriptors_empty_inputs(self):
        """空输入 → 空列表"""
        assert _build_character_descriptors([], {}) == []
        assert _build_character_descriptors(None, {}) == []
        assert _build_character_descriptors(["char_001"], {}) == []

    def test_fallback_angle_variants_count(self):
        """有至少 3 个差异化 variants（保证 T20-4 差异化有效）"""
        assert len(_FALLBACK_ANGLE_VARIANTS) >= 3
        # 每个 variant 必须有 3 个字段
        for v in _FALLBACK_ANGLE_VARIANTS:
            assert "angle_phrase" in v
            assert "focus_phrase" in v
            assert "framing_hint" in v


# ═══════════════════════════════════════════════════════════════════
# Section 2: build_screenplay_aware_fallback_prompt 核心测试
# ═══════════════════════════════════════════════════════════════════


class TestFallbackPromptBuilder:
    """RISK-T20-7 核心：fallback prompt 必须含 screenplay 数据"""

    def test_fallback_prompt_contains_action_beat_emotional_note(
        self, test18_characters, scene_rainy_night_conflict
    ):
        """RISK-T20-7 主验证: fallback prompt 含 action_beats[0] 的 emotional_note"""
        atm = _atmosphere_to_str(scene_rainy_night_conflict["atmosphere"])
        prompt = build_screenplay_aware_fallback_prompt(
            scene=scene_rainy_night_conflict,
            characters=test18_characters,
            scene_heading_safe=scene_rainy_night_conflict["scene_heading"],
            atmosphere_str=atm,
            fallback_seq=0,
        )
        # action_beats[0].emotional_note = "tense and watchful"
        assert "tense and watchful" in prompt or "shocked" in prompt, \
            f"fallback prompt 应含 action_beats emotional_note. 实际 prompt: {prompt[:500]}"

    def test_fallback_prompt_contains_characters_english_names(
        self, test18_characters, scene_rainy_night_conflict
    ):
        """RISK-T20-7 主验证: fallback prompt 提及 characters_in_scene 中的角色英文名"""
        atm = _atmosphere_to_str(scene_rainy_night_conflict["atmosphere"])
        prompt = build_screenplay_aware_fallback_prompt(
            scene=scene_rainy_night_conflict,
            characters=test18_characters,
            scene_heading_safe=scene_rainy_night_conflict["scene_heading"],
            atmosphere_str=atm,
            fallback_seq=0,
        )
        # characters_in_scene = ["char_001", "char_002"] → Chen Mo, Lin Xiaoyu
        assert "Chen Mo" in prompt, "fallback prompt 应含 Chen Mo (name_en)"
        assert "Lin Xiaoyu" in prompt, "fallback prompt 应含 Lin Xiaoyu (name_en)"
        # 不应含中文角色名
        assert "陈默" not in prompt, "fallback prompt 不应含中文 '陈默'"
        assert "林晓雨" not in prompt, "fallback prompt 不应含中文 '林晓雨'"

    def test_fallback_prompt_no_lazy_directive(
        self, test18_characters, scene_rainy_night_conflict
    ):
        """RISK-T20-7 主验证: fallback prompt 不含旧的 'No specific character interaction required'"""
        atm = _atmosphere_to_str(scene_rainy_night_conflict["atmosphere"])
        prompt = build_screenplay_aware_fallback_prompt(
            scene=scene_rainy_night_conflict,
            characters=test18_characters,
            scene_heading_safe=scene_rainy_night_conflict["scene_heading"],
            atmosphere_str=atm,
            fallback_seq=0,
        )
        # 旧 lazy 指令必须消失
        assert "No specific character interaction required" not in prompt, \
            "fallback prompt 不应再含 'No specific character interaction required' 的 lazy 指令"
        assert "no character interaction" not in prompt.lower(), \
            "fallback prompt 不应有任何 'no character interaction' 变体"

    def test_fallback_prompt_english_only(
        self, test18_characters, scene_rainy_night_conflict
    ):
        """RISK-T20-7 主验证: fallback prompt 全英文（无中文字符）"""
        atm = _atmosphere_to_str(scene_rainy_night_conflict["atmosphere"])
        prompt = build_screenplay_aware_fallback_prompt(
            scene=scene_rainy_night_conflict,
            characters=test18_characters,
            scene_heading_safe=scene_rainy_night_conflict["scene_heading"],
            atmosphere_str=atm,
            fallback_seq=0,
        )
        assert not _contains_chinese(prompt), \
            f"fallback prompt 必须全英文，但发现中文字符。前 200 chars: {prompt[:200]}"

    def test_fallback_prompt_handles_chinese_clothing_data(
        self, anthropomorphic_characters, scene_rainy_night_conflict
    ):
        """RISK-T20-7: 角色 clothing 中文时，fallback prompt 仍英文"""
        # 用 anthropomorphic_characters (char_001 clothing 全中文)
        atm = _atmosphere_to_str(scene_rainy_night_conflict["atmosphere"])
        prompt = build_screenplay_aware_fallback_prompt(
            scene=scene_rainy_night_conflict,
            characters=anthropomorphic_characters,
            scene_heading_safe=scene_rainy_night_conflict["scene_heading"],
            atmosphere_str=atm,
            fallback_seq=0,
        )
        assert not _contains_chinese(prompt), \
            "即使 clothing 全中文，fallback prompt 仍应全英文"
        # 应保留 Grey Fox 和 Milly 英文名
        assert "Grey Fox" in prompt
        assert "Milly" in prompt

    def test_fallback_prompt_explicit_character_count(
        self, test18_characters, scene_rainy_night_conflict
    ):
        """fallback prompt 应明确说出 character count (避免 Seedream 不画人)"""
        atm = _atmosphere_to_str(scene_rainy_night_conflict["atmosphere"])
        prompt = build_screenplay_aware_fallback_prompt(
            scene=scene_rainy_night_conflict,
            characters=test18_characters,
            scene_heading_safe=scene_rainy_night_conflict["scene_heading"],
            atmosphere_str=atm,
            fallback_seq=0,
        )
        # 2 角色场景 → EXACTLY 2
        assert "EXACTLY 2 character" in prompt, \
            f"应明确说出角色数 'EXACTLY 2 characters'. 实际: {prompt}"

    def test_fallback_prompt_pure_environmental_no_characters(
        self, test18_characters, scene_pure_environmental
    ):
        """0 角色场景 → fallback prompt 说明纯环境，不强加角色"""
        atm = _atmosphere_to_str(scene_pure_environmental["atmosphere"])
        prompt = build_screenplay_aware_fallback_prompt(
            scene=scene_pure_environmental,
            characters=test18_characters,
            scene_heading_safe=scene_pure_environmental["scene_heading"],
            atmosphere_str=atm,
            fallback_seq=0,
        )
        assert "No characters are present" in prompt or \
               "pure environmental" in prompt.lower() or \
               "Pure environmental" in prompt, \
            "0 角色场景应明确说明 pure environmental"
        # 不应出现 'EXACTLY 0 character' (语意奇怪)
        # 不应出现 character_in_scene 的角色（chars 列表为空）

    def test_fallback_prompt_missing_atmosphere_does_not_crash(
        self, test18_characters, scene_rainy_night_conflict
    ):
        """atmosphere 为空 → 不崩，prompt 仍可用"""
        prompt = build_screenplay_aware_fallback_prompt(
            scene=scene_rainy_night_conflict,
            characters=test18_characters,
            scene_heading_safe=scene_rainy_night_conflict["scene_heading"],
            atmosphere_str="",  # 空 atmosphere
            fallback_seq=0,
        )
        assert len(prompt) > 50
        assert not _contains_chinese(prompt)

    def test_fallback_prompt_missing_scene_heading_does_not_crash(
        self, test18_characters, scene_rainy_night_conflict
    ):
        """scene_heading 为空 → 不崩，prompt 仍可用"""
        prompt = build_screenplay_aware_fallback_prompt(
            scene=scene_rainy_night_conflict,
            characters=test18_characters,
            scene_heading_safe="",
            atmosphere_str="confrontational",
            fallback_seq=0,
        )
        assert len(prompt) > 50
        assert not _contains_chinese(prompt)


# ═══════════════════════════════════════════════════════════════════
# Section 3: RISK-T20-4 — 同 location 差异化测试
# ═══════════════════════════════════════════════════════════════════


class TestSameLocationDifferentiation:
    """RISK-T20-4: 同 location 多 fallback 输出必须不同 (避免 Shot 5/13 几乎一样)"""

    def test_same_location_different_scenes_get_different_variants(
        self, test18_characters, scene_rainy_night_conflict, scene_same_location_2,
        scene_same_location_3
    ):
        """3 个同 location_id 不同 scene_id 的 fallback prompt 应明显不同.

        注意: Python 3 的 hash(str) 是 process-randomized (PYTHONHASHSEED), 不能依赖
        固定 hash 值确定 angle variant. 因此该测试用显式 variant idx (0/1/2) 强制覆盖
        差异化逻辑, 而非依赖 hash 计算 (避免 flaky test).
        """
        atm1 = _atmosphere_to_str(scene_rainy_night_conflict["atmosphere"])
        atm2 = _atmosphere_to_str(scene_same_location_2["atmosphere"])
        atm3 = _atmosphere_to_str(scene_same_location_3["atmosphere"])

        # 显式用不同 fallback_seq 强制 3 种 angle variant (避免依赖 Python hash 随机化)
        # 真实 production 中 fallback_seq = hash(location_id|scene_id) % 4, 每次进程 hash 不同
        # 但 3 个 scene_id 不同时, hash 大概率分散到不同 variant (但不 100%)
        prompt1 = build_screenplay_aware_fallback_prompt(
            scene=scene_rainy_night_conflict,
            characters=test18_characters,
            scene_heading_safe=scene_rainy_night_conflict["scene_heading"],
            atmosphere_str=atm1,
            fallback_seq=0,  # 显式 idx 0
        )
        prompt2 = build_screenplay_aware_fallback_prompt(
            scene=scene_same_location_2,
            characters=test18_characters,
            scene_heading_safe=scene_same_location_2["scene_heading"],
            atmosphere_str=atm2,
            fallback_seq=1,  # 显式 idx 1
        )
        prompt3 = build_screenplay_aware_fallback_prompt(
            scene=scene_same_location_3,
            characters=test18_characters,
            scene_heading_safe=scene_same_location_3["scene_heading"],
            atmosphere_str=atm3,
            fallback_seq=2,  # 显式 idx 2
        )

        # 3 个 prompt 必须不同
        assert prompt1 != prompt2, \
            f"同 location 不同 scene 的 fallback prompt 应不同。\nprompt1: {prompt1[:200]}\nprompt2: {prompt2[:200]}"
        assert prompt2 != prompt3
        assert prompt1 != prompt3
        # 应使用 3 种不同 angle_phrase (因为显式传 0/1/2)
        used = set()
        for v in _FALLBACK_ANGLE_VARIANTS:
            for p in [prompt1, prompt2, prompt3]:
                if v["angle_phrase"] in p:
                    used.add(v["angle_phrase"])
                    break
        assert len(used) >= 2, \
            f"显式不同 fallback_seq 应触发至少 2 种不同 angle_phrase。used: {used}"

    def test_explicit_different_fallback_seq_produces_different_prompts(
        self, test18_characters, scene_rainy_night_conflict
    ):
        """显式不同 fallback_seq → 不同 prompt"""
        atm = _atmosphere_to_str(scene_rainy_night_conflict["atmosphere"])
        prompts = []
        for seq in range(len(_FALLBACK_ANGLE_VARIANTS)):
            p = build_screenplay_aware_fallback_prompt(
                scene=scene_rainy_night_conflict,
                characters=test18_characters,
                scene_heading_safe=scene_rainy_night_conflict["scene_heading"],
                atmosphere_str=atm,
                fallback_seq=seq,
            )
            prompts.append(p)
        # 所有 prompt 应两两不同
        for i in range(len(prompts)):
            for j in range(i + 1, len(prompts)):
                assert prompts[i] != prompts[j], \
                    f"fallback_seq={i} 和 {j} 的 prompt 不应相同"


# ═══════════════════════════════════════════════════════════════════
# Section 4: _build_scene_prompt anti-empty-shots 硬约束 (RISK-T20-1)
# ═══════════════════════════════════════════════════════════════════


class TestAntiEmptyShotsConstraint:
    """RISK-T20-1: _build_scene_prompt 必须包含 anti-empty-shots 硬约束"""

    def test_scene_prompt_contains_never_empty_directive(
        self, director, test18_characters, scene_rainy_night_conflict
    ):
        """LLM prompt 应明确禁止 shots: []"""
        visual_tone = {"mood": "tense"}
        prompt = director._build_scene_prompt(
            scene=scene_rainy_night_conflict,
            characters=test18_characters,
            visual_tone=visual_tone,
            style_preset="korean_webtoon",
            shot_id_start=1,
        )
        # 必含 RISK-T20-1 标记 + 关键约束词
        assert "RISK-T20-1" in prompt, "prompt 应含 RISK-T20-1 marker"
        assert "NEVER" in prompt and "EMPTY" in prompt.upper(), \
            "prompt 应含 NEVER + EMPTY 约束"

    def test_scene_prompt_lists_difficult_scene_types(
        self, director, test18_characters, scene_rainy_night_conflict
    ):
        """anti-empty 块应列出常见困难场景类型作 reminder"""
        prompt = director._build_scene_prompt(
            scene=scene_rainy_night_conflict,
            characters=test18_characters,
            visual_tone={"mood": "tense"},
            style_preset="korean_webtoon",
            shot_id_start=1,
        )
        # 应提及困难场景类型
        lower = prompt.lower()
        assert "conflict" in lower or "confrontation" in lower, \
            "prompt 应列出 conflict/confrontation 场景"
        assert "rainy" in lower or "rain" in lower, \
            "prompt 应列出 rainy 场景"

    def test_scene_prompt_contains_forbidden_output_example(
        self, director, test18_characters, scene_rainy_night_conflict
    ):
        """anti-empty 块应有 ❌ FORBIDDEN OUTPUT 示例"""
        prompt = director._build_scene_prompt(
            scene=scene_rainy_night_conflict,
            characters=test18_characters,
            visual_tone={"mood": "tense"},
            style_preset="korean_webtoon",
            shot_id_start=1,
        )
        # 应有 ❌ FORBIDDEN + 示例
        assert "FORBIDDEN" in prompt
        # 应有 shots: [] 或 "shots": [] 反例
        assert '"shots": []' in prompt or "shots: []" in prompt, \
            "prompt 应含 shots: [] anti-pattern 示例"


# ═══════════════════════════════════════════════════════════════════
# Section 5: 集成测试 — 完整 fallback 路径不退化 (regression)
# ═══════════════════════════════════════════════════════════════════


class TestRegression:
    """确保 RISK-T20-7 不破坏既有 _is_fallback 标记 + 100% 英文 invariant"""

    def test_fallback_uses_extract_english_from_field(
        self, test18_characters, scene_rainy_night_conflict
    ):
        """复用 _extract_english_from_field（不重新发明轮子）"""
        # 间接通过 _build_character_descriptors 调用，证明 clothing 英文提取生效
        result = _build_character_descriptors(["char_002"], test18_characters)
        assert "oatmeal-ivory ribbed knit sweater" in result[0]["clothing"], \
            "应保留英文 clothing 完整描述"

    def test_fallback_prompt_length_reasonable(
        self, test18_characters, scene_rainy_night_conflict
    ):
        """fallback prompt 长度合理（不会过长导致超 token，也不会过短）"""
        atm = _atmosphere_to_str(scene_rainy_night_conflict["atmosphere"])
        prompt = build_screenplay_aware_fallback_prompt(
            scene=scene_rainy_night_conflict,
            characters=test18_characters,
            scene_heading_safe=scene_rainy_night_conflict["scene_heading"],
            atmosphere_str=atm,
            fallback_seq=0,
        )
        # 长度 200-2000 chars 合理
        assert 200 <= len(prompt) <= 2000, \
            f"fallback prompt 长度应在 200-2000 chars。实际 {len(prompt)}"

    def test_fallback_prompt_preserves_atmosphere_when_english(
        self, test18_characters, scene_rainy_night_conflict
    ):
        """英文 atmosphere 应被保留到 prompt"""
        atm = _atmosphere_to_str(scene_rainy_night_conflict["atmosphere"])
        prompt = build_screenplay_aware_fallback_prompt(
            scene=scene_rainy_night_conflict,
            characters=test18_characters,
            scene_heading_safe=scene_rainy_night_conflict["scene_heading"],
            atmosphere_str=atm,
            fallback_seq=0,
        )
        # atmosphere 字段含 "confrontational"
        assert "confrontational" in prompt, \
            "英文 atmosphere 应被保留到 fallback prompt"

    def test_universal_works_for_anthropomorphic_characters(
        self, anthropomorphic_characters
    ):
        """通用工具视角: anthropomorphic_animal 类型也应 work"""
        scene = {
            "scene_id": 5,
            "scene_heading": "EXT. Old birch grove - Early spring - clear morning",
            "location_id": "birch_grove",
            "atmosphere": "tranquil, snow melting slowly, soft morning light",
            "characters_in_scene": ["char_001", "char_002"],
            "action_beats": [
                {
                    "beat_id": "5a",
                    "action": "Grey Fox stops by the largest birch tree",
                    "emotional_note": "solemn, reverent",
                }
            ],
            "narration": "The birch grove sat silent under fresh snow.",
        }
        atm = _atmosphere_to_str(scene["atmosphere"])
        prompt = build_screenplay_aware_fallback_prompt(
            scene=scene,
            characters=anthropomorphic_characters,
            scene_heading_safe=scene["scene_heading"],
            atmosphere_str=atm,
            fallback_seq=0,
        )
        # 应含拟人化角色英文名
        assert "Grey Fox" in prompt
        assert "Milly" in prompt
        # 应含 emotional_note
        assert "solemn" in prompt or "reverent" in prompt
        # 全英文
        assert not _contains_chinese(prompt)


# ═══════════════════════════════════════════════════════════════════
# Section 6: RISK-T20-7 v2 治本 — LLM 翻译路径测试 (2026-05-18)
# ═══════════════════════════════════════════════════════════════════
#
# 验证治本升级:
# 1. 中文 narration/action → LLM 翻译为英文片段 → 注入到 fallback prompt
# 2. LLM 失败 (超时/异常/返中文/过短) → 完全降级到静态 fallback (v1 行为)
# 3. 不传 llm_translator (向后兼容) → 走静态 (v1)
# 4. universal: 任何故事类型都 work, 不 hardcode test18
# ═══════════════════════════════════════════════════════════════════


class TestChineseTranslationRequest:
    """RISK-T20-7 v2: _build_chinese_translation_request 单元测试"""

    def test_returns_none_for_pure_english_input(self):
        """纯英文 scene → 返回 None (调用方走静态)"""
        scene = {
            "scene_id": 1,
            "atmosphere": "tense",
            "characters_in_scene": [],
            "action_beats": [
                {"beat_id": "1a", "action": "Bob enters the room", "emotional_note": "calm"}
            ],
            "narration": "Bob walked in slowly.",
        }
        req = _build_chinese_translation_request(scene, "INT. Office", "tense")
        assert req is None, "纯英文场景不应触发 LLM 翻译"

    def test_returns_prompt_for_chinese_action(self):
        """含中文 action → 返回翻译请求 prompt"""
        scene = {
            "scene_id": 2,
            "action_beats": [
                {"beat_id": "2a", "action": "林晓雨深吸一口气，将手机缓缓收回", "emotional_note": "resolved"}
            ],
            "narration": "",
        }
        req = _build_chinese_translation_request(scene, "EXT. Alley", "devastated")
        assert req is not None, "中文 action 应触发翻译"
        # 翻译请求 prompt 必须含核心指令
        assert "Translate" in req
        assert "ONLY" in req or "Output ONLY" in req
        assert "50 words" in req
        # 必须含输入素材
        assert "深吸一口气" in req or "林晓雨" in req

    def test_returns_prompt_for_chinese_narration(self):
        """中文 narration (action 英文) → 返回翻译请求"""
        scene = {
            "scene_id": 3,
            "action_beats": [
                {"beat_id": "3a", "action": "she walks slowly", "emotional_note": "tired"}
            ],
            "narration": "她的脚步在雨中渐渐变慢。",
        }
        req = _build_chinese_translation_request(scene, "EXT. Street", "melancholic")
        assert req is not None
        assert "她的脚步" in req or "渐渐变慢" in req

    def test_universal_works_for_any_chinese_story(self):
        """通用性: 古装/科幻/校园 任何中文故事都触发"""
        for action_chinese, atm in [
            ("月光下，剑客抽剑出鞘", "ancient_martial"),
            ("飞船舱门缓缓打开，少年走出", "sci-fi"),
            ("教室里，老师转身写下方程", "school_drama"),
        ]:
            scene = {
                "scene_id": 99,
                "action_beats": [{"beat_id": "99a", "action": action_chinese}],
                "narration": "",
            }
            req = _build_chinese_translation_request(scene, "SCENE", atm)
            assert req is not None, f"中文故事类型 '{atm}' 应触发翻译"


class TestSanitizeLLMTranslation:
    """RISK-T20-7 v2: _sanitize_llm_translation 清洗逻辑"""

    def test_strips_markdown_code_fence(self):
        """LLM 输出含 ``` 代码块包装 → 提取内容"""
        raw = "```\nA tense rainy alley with two figures facing each other under a streetlamp.\n```"
        cleaned = _sanitize_llm_translation(raw)
        assert "tense rainy alley" in cleaned
        assert "```" not in cleaned

    def test_strips_common_prefixes(self):
        """LLM 输出含 'Output:' 'Translation:' 前缀 → 剥离"""
        for prefix in ["Output: ", "Translation: ", "Here is the English prompt: ", "English prompt: "]:
            raw = f"{prefix}A wide shot of two characters in the rain at night."
            cleaned = _sanitize_llm_translation(raw)
            assert cleaned.startswith("A wide shot"), f"前缀 '{prefix}' 应被剥离"

    def test_rejects_chinese_output(self):
        """LLM 违规输出含中文 → 返回空 (调用方走静态)"""
        raw = "A wide shot of 两个角色 in the rain"
        cleaned = _sanitize_llm_translation(raw)
        assert cleaned == "", "含中文的 LLM 输出必须被拒"

    def test_rejects_too_short(self):
        """LLM 输出过短 (无意义) → 返回空"""
        for raw in ["", "ok", "yes", "Done.", "Image."]:
            cleaned = _sanitize_llm_translation(raw)
            assert cleaned == "", f"过短输出 '{raw}' 应被拒"

    def test_truncates_too_long(self):
        """LLM 输出过长 (失控) → 截断到 600 chars"""
        raw = "A wide shot. " * 200  # ~2600 chars
        cleaned = _sanitize_llm_translation(raw)
        assert len(cleaned) <= 600
        assert not _contains_chinese(cleaned)

    def test_strips_surrounding_quotes(self):
        """LLM 输出被引号包裹 → 剥离"""
        raw = '"A wide angle shot of two figures meeting eyes in heavy rain."'
        cleaned = _sanitize_llm_translation(raw)
        assert not cleaned.startswith('"')
        assert "A wide angle shot" in cleaned


class TestFallbackPromptWithLLMTranslation:
    """RISK-T20-7 v2: build_screenplay_aware_fallback_prompt 接受 llm_translation 参数"""

    def test_llm_translation_replaces_static_action_segment(
        self, test18_characters, scene_rainy_night_conflict
    ):
        """有 LLM 翻译 → prompt 含 'Scene details:' 段 + 翻译内容"""
        atm = _atmosphere_to_str(scene_rainy_night_conflict["atmosphere"])
        translation = (
            "Two people facing each other under heavy rain at a corridor doorway. "
            "She holds up a phone, fingers hovering above the screen. "
            "He stops at the threshold, water dripping from the eaves around him."
        )
        prompt = build_screenplay_aware_fallback_prompt(
            scene=scene_rainy_night_conflict,
            characters=test18_characters,
            scene_heading_safe=scene_rainy_night_conflict["scene_heading"],
            atmosphere_str=atm,
            fallback_seq=0,
            llm_translation=translation,
        )
        # 翻译内容必须被注入
        assert "Scene details:" in prompt
        assert "facing each other under heavy rain" in prompt
        assert "phone" in prompt
        # 仍含角色信息和情感锚点 (T20-7 v1 部分)
        assert "Chen Mo" in prompt
        assert "Lin Xiaoyu" in prompt
        assert "EXACTLY 2 character" in prompt
        # 全英文
        assert not _contains_chinese(prompt)

    def test_empty_llm_translation_falls_back_to_static(
        self, test18_characters, scene_rainy_night_conflict
    ):
        """LLM 翻译为空 → 走静态 (v1 行为, 向后兼容)"""
        atm = _atmosphere_to_str(scene_rainy_night_conflict["atmosphere"])
        prompt_with_empty = build_screenplay_aware_fallback_prompt(
            scene=scene_rainy_night_conflict,
            characters=test18_characters,
            scene_heading_safe=scene_rainy_night_conflict["scene_heading"],
            atmosphere_str=atm,
            fallback_seq=0,
            llm_translation="",  # 显式空字符串
        )
        # 不传 llm_translation (使用默认 "")
        prompt_default = build_screenplay_aware_fallback_prompt(
            scene=scene_rainy_night_conflict,
            characters=test18_characters,
            scene_heading_safe=scene_rainy_night_conflict["scene_heading"],
            atmosphere_str=atm,
            fallback_seq=0,
        )
        # 两个 prompt 应完全一致 (向后兼容)
        assert prompt_with_empty == prompt_default
        # 不应含 "Scene details:" 段 (是 LLM 路径独有)
        assert "Scene details:" not in prompt_with_empty
        # 仍是合法 fallback prompt
        assert "EXACTLY 2 character" in prompt_with_empty
        assert not _contains_chinese(prompt_with_empty)

    def test_chinese_llm_translation_rejected_falls_back_static(
        self, test18_characters, scene_rainy_night_conflict
    ):
        """LLM 翻译含中文 (违规) → builder 自动忽略, 走静态"""
        atm = _atmosphere_to_str(scene_rainy_night_conflict["atmosphere"])
        bad_translation = "A wide shot of 林晓雨 and 陈默 in heavy rain"  # 含中文
        prompt = build_screenplay_aware_fallback_prompt(
            scene=scene_rainy_night_conflict,
            characters=test18_characters,
            scene_heading_safe=scene_rainy_night_conflict["scene_heading"],
            atmosphere_str=atm,
            fallback_seq=0,
            llm_translation=bad_translation,
        )
        # 不应注入含中文的 translation
        assert "林晓雨" not in prompt
        assert "陈默" not in prompt
        # 全英文
        assert not _contains_chinese(prompt)
        # 不应出现 "Scene details:" 段 (因为 translation 被拒)
        assert "Scene details:" not in prompt

    def test_too_short_llm_translation_rejected(
        self, test18_characters, scene_rainy_night_conflict
    ):
        """LLM 翻译过短 (< 20 chars) → builder 忽略"""
        atm = _atmosphere_to_str(scene_rainy_night_conflict["atmosphere"])
        prompt = build_screenplay_aware_fallback_prompt(
            scene=scene_rainy_night_conflict,
            characters=test18_characters,
            scene_heading_safe=scene_rainy_night_conflict["scene_heading"],
            atmosphere_str=atm,
            fallback_seq=0,
            llm_translation="OK done.",  # 太短
        )
        # 不应出现 "Scene details:" 段
        assert "Scene details:" not in prompt

    def test_universal_llm_translation_works_for_anthropomorphic(
        self, anthropomorphic_characters
    ):
        """通用性: anthropomorphic_animal 故事 + LLM 翻译也能正确工作"""
        scene = {
            "scene_id": 7,
            "scene_heading": "EXT. Forest grove - Twilight",
            "location_id": "forest_grove",
            "atmosphere": "mystical, fog rolling in",
            "characters_in_scene": ["char_001", "char_002"],
            "action_beats": [
                {"beat_id": "7a", "action": "灰狐站在大树下深思", "emotional_note": "contemplative"}
            ],
            "narration": "暮色四合，森林归于沉寂。",
        }
        atm = _atmosphere_to_str(scene["atmosphere"])
        translation = "A grey fox stands beneath a tall ancient tree, head tilted thoughtfully, with a small companion nearby in the twilight fog."
        prompt = build_screenplay_aware_fallback_prompt(
            scene=scene,
            characters=anthropomorphic_characters,
            scene_heading_safe=scene["scene_heading"],
            atmosphere_str=atm,
            fallback_seq=0,
            llm_translation=translation,
        )
        assert "Scene details:" in prompt
        assert "ancient tree" in prompt
        assert "Grey Fox" in prompt
        assert "Milly" in prompt
        assert not _contains_chinese(prompt)


class TestLLMTranslatorAsyncMethod:
    """RISK-T20-7 v2: StoryboardDirector._translate_chinese_to_image_prompt async 集成"""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_chinese_input(self, director, test18_characters):
        """纯英文 scene → 直接返回 "" (不调 LLM)"""
        scene = {
            "scene_id": 1,
            "action_beats": [{"beat_id": "1a", "action": "Bob enters", "emotional_note": "calm"}],
            "narration": "Bob walked in.",
            "characters_in_scene": ["char_001"],
        }
        # director.claude_client = None, gemini_client = None
        result = await director._translate_chinese_to_image_prompt(
            scene=scene,
            scene_heading_safe="INT. Office",
            atmosphere_str="calm",
        )
        assert result == ""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_llm_clients(self, director, scene_rainy_night_conflict):
        """无 LLM 客户端 (claude_client + gemini_client 都 None) → 返回 "" """
        # director fixture 已设置 claude_client=None, gemini_client=None
        result = await director._translate_chinese_to_image_prompt(
            scene=scene_rainy_night_conflict,
            scene_heading_safe=scene_rainy_night_conflict["scene_heading"],
            atmosphere_str="confrontational",
        )
        assert result == ""

    @pytest.mark.asyncio
    async def test_llm_timeout_returns_empty(self, scene_rainy_night_conflict):
        """LLM 超时 → 返回 "" (降级静态)"""
        d = StoryboardDirector.__new__(StoryboardDirector)
        d.claude_model = "claude-sonnet-4-6"
        d.gemini_model = "gemini-3.1-flash-lite-preview"
        d.gemini_client = None

        # Mock claude_client.messages.create 永远不返回
        async def _slow_call(*args, **kwargs):
            await asyncio.sleep(10)  # > timeout
            return MagicMock()

        d.claude_client = MagicMock()
        d.claude_client.messages = MagicMock()
        d.claude_client.messages.create = AsyncMock(side_effect=_slow_call)

        result = await d._translate_chinese_to_image_prompt(
            scene=scene_rainy_night_conflict,
            scene_heading_safe=scene_rainy_night_conflict["scene_heading"],
            atmosphere_str="confrontational",
            timeout_seconds=0.5,  # 短超时方便测试
        )
        assert result == ""

    @pytest.mark.asyncio
    async def test_llm_returns_chinese_rejected(self, scene_rainy_night_conflict):
        """LLM 违规返中文 → 被拒, 返回 "" """
        d = StoryboardDirector.__new__(StoryboardDirector)
        d.claude_model = "claude-sonnet-4-6"
        d.gemini_model = "gemini-3.1-flash-lite-preview"
        d.gemini_client = None

        # Mock Claude 返回含中文的翻译
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="A wide shot of 林晓雨 facing 陈默")]

        d.claude_client = MagicMock()
        d.claude_client.messages = MagicMock()
        d.claude_client.messages.create = AsyncMock(return_value=mock_response)

        result = await d._translate_chinese_to_image_prompt(
            scene=scene_rainy_night_conflict,
            scene_heading_safe=scene_rainy_night_conflict["scene_heading"],
            atmosphere_str="confrontational",
            timeout_seconds=5.0,
        )
        assert result == "", "含中文的 LLM 输出必须被拒"

    @pytest.mark.asyncio
    async def test_llm_success_returns_cleaned_translation(self, scene_rainy_night_conflict):
        """LLM 成功翻译 → 返回清洗后的英文片段"""
        d = StoryboardDirector.__new__(StoryboardDirector)
        d.claude_model = "claude-sonnet-4-6"
        d.gemini_model = "gemini-3.1-flash-lite-preview"
        d.gemini_client = None

        # Mock Claude 返回合法翻译 (含 markdown 包装测试清洗)
        clean_translation = "Two figures meet under heavy rain at a corridor doorway, one holding a phone with fingers hovering above the screen."
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=f"```\n{clean_translation}\n```")]

        d.claude_client = MagicMock()
        d.claude_client.messages = MagicMock()
        d.claude_client.messages.create = AsyncMock(return_value=mock_response)

        result = await d._translate_chinese_to_image_prompt(
            scene=scene_rainy_night_conflict,
            scene_heading_safe=scene_rainy_night_conflict["scene_heading"],
            atmosphere_str="confrontational",
            timeout_seconds=5.0,
        )
        assert result != ""
        assert "Two figures meet under heavy rain" in result
        assert "```" not in result
        assert not _contains_chinese(result)

    @pytest.mark.asyncio
    async def test_llm_claude_exception_falls_back_to_gemini(self, scene_rainy_night_conflict):
        """Claude 异常 → Gemini 兜底 → 返回 Gemini 翻译"""
        d = StoryboardDirector.__new__(StoryboardDirector)
        d.claude_model = "claude-sonnet-4-6"
        d.gemini_model = "gemini-3.1-flash-lite-preview"

        # Claude 抛异常
        d.claude_client = MagicMock()
        d.claude_client.messages = MagicMock()
        d.claude_client.messages.create = AsyncMock(side_effect=Exception("Claude API error"))

        # Gemini 成功返回
        gemini_translation = "A wide shot showing two characters in heavy rain at the corridor entrance."
        gemini_response = MagicMock()
        gemini_response.text = gemini_translation

        d.gemini_client = MagicMock()
        d.gemini_client.aio = MagicMock()
        d.gemini_client.aio.models = MagicMock()
        d.gemini_client.aio.models.generate_content = AsyncMock(return_value=gemini_response)

        result = await d._translate_chinese_to_image_prompt(
            scene=scene_rainy_night_conflict,
            scene_heading_safe=scene_rainy_night_conflict["scene_heading"],
            atmosphere_str="confrontational",
            timeout_seconds=5.0,
        )
        # Gemini 翻译应被使用
        assert "two characters in heavy rain" in result

    @pytest.mark.asyncio
    async def test_llm_both_fail_returns_empty(self, scene_rainy_night_conflict):
        """Claude + Gemini 都失败 → 返回 "" (降级静态, 不崩)"""
        d = StoryboardDirector.__new__(StoryboardDirector)
        d.claude_model = "claude-sonnet-4-6"
        d.gemini_model = "gemini-3.1-flash-lite-preview"

        d.claude_client = MagicMock()
        d.claude_client.messages = MagicMock()
        d.claude_client.messages.create = AsyncMock(side_effect=Exception("Claude fail"))

        d.gemini_client = MagicMock()
        d.gemini_client.aio = MagicMock()
        d.gemini_client.aio.models = MagicMock()
        d.gemini_client.aio.models.generate_content = AsyncMock(side_effect=Exception("Gemini fail"))

        result = await d._translate_chinese_to_image_prompt(
            scene=scene_rainy_night_conflict,
            scene_heading_safe=scene_rainy_night_conflict["scene_heading"],
            atmosphere_str="confrontational",
            timeout_seconds=5.0,
        )
        # 不崩, 返回 ""
        assert result == ""


if __name__ == "__main__":
    import subprocess
    # 允许直接 python tests/test_b51_fallback_uses_screenplay.py 跑
    sys.exit(subprocess.call([sys.executable, "-m", "pytest", __file__, "-v"]))
