"""RISK-T20-21 (2026-05-19) — Backend wire: Stage 3 ScreenplayWriter 接通 DEC-044 prompts

AI-ML Wave 1 (5/19 17:25) 已实现 app/prompts/screenplay_prompts.py
(DEC044_SCREENPLAY_RULES / DEC044_SCREENPLAY_OUTPUT_EXAMPLE / hard-cap getters / validators).
Backend Wave 2 wire 测试验证:

1. _build_batch_prompt() 注入 DEC044_SCREENPLAY_RULES + OUTPUT_EXAMPLE
2. _build_single_scene_prompt() 同上
3. target_narration_words 公式改为 min(120, int(duration * 1.5))
4. 旧"【字数硬性要求】" prose-mode 文本已删除
5. _expand_narration_if_needed 已 disable (return scene unchanged)
6. Wire 是 UNIVERSAL (任何 plot_point duration / shot count 都适用)

测试不调用 LLM, 仅检查 prompt string 内容和 helper return value.
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.screenplay_writer import ScreenplayWriter
from app.prompts.screenplay_prompts import (
    DEC044_SCREENPLAY_RULES,
    DEC044_SCREENPLAY_OUTPUT_EXAMPLE,
    DEC044_PRODUCT_FORM_DECLARATION,
    NARRATION_CAPTION_RULES,
    DIALOGUE_THOUGHT_DENSITY_RULES,
    get_dec044_narration_max_chars,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _mock_outline(unique_locations_count: int = 2):
    return {
        "plot_points": [
            {
                "beat": "opening",
                "description": "灰狐独行雪林赴约",
                "estimated_duration_seconds": 30,
            },
            {
                "beat": "discovery",
                "description": "小动物发现树皮上划痕",
                "estimated_duration_seconds": 40,
            },
        ],
        "unique_locations": [
            {"location_id": "L001", "display_name": "深山雪林路", "location_type": "EXT"},
            {"location_id": "L002", "display_name": "白桦树下", "location_type": "EXT"},
        ][:unique_locations_count],
        "target_metrics": {"target_duration_seconds": 180},
        "visual_tone": {"overall_mood": "warm"},
    }


def _mock_characters():
    return {
        "characters": [
            {
                "id": "char_001",
                "name": "灰狐",
                "role": "protagonist",
                "clothing": {"accessories": ["sun-pale fur", "weathered paws"]},
            },
            {
                "id": "char_002",
                "name": "米莉",
                "role": "supporting",
                "clothing": {"accessories": ["white rabbit fur"]},
            },
        ]
    }


def _make_writer() -> ScreenplayWriter:
    """构造 ScreenplayWriter, family_relationships 初始化"""
    writer = ScreenplayWriter()
    writer._family_relationships = []
    return writer


# ---------------------------------------------------------------------------
# 1. DEC044_SCREENPLAY_RULES 注入验证
# ---------------------------------------------------------------------------

class TestDec044RulesInjection:
    """T20-21 wire: DEC-044 prompt rules 必须出现在 batch + single prompt"""

    def test_batch_prompt_contains_dec044_rules(self):
        writer = _make_writer()
        outline = _mock_outline()
        chars = _mock_characters()
        prompt = writer._build_batch_prompt(
            plot_points=outline["plot_points"],
            outline=outline,
            characters=chars,
            previous_scenes=[],
            scene_id_offset=0,
        )
        # DEC044_SCREENPLAY_RULES 是 PRODUCT_FORM + NARRATION + DIALOGUE 三块组合
        assert "DEC-044" in prompt, "batch prompt 缺少 DEC-044 标记"
        assert "PRODUCT FINAL FORM" in prompt, "batch prompt 缺少 PRODUCT FORM 声明"
        assert "NARRATION FIELD RULES" in prompt, "batch prompt 缺少 narration 规则"
        assert "DIALOGUE & THOUGHT DENSITY" in prompt, "batch prompt 缺少 dialogue density 规则"

    def test_single_prompt_contains_dec044_rules(self):
        writer = _make_writer()
        outline = _mock_outline()
        chars = _mock_characters()
        prompt = writer._build_single_scene_prompt(
            plot_point=outline["plot_points"][0],
            plot_point_index=0,
            total_plot_points=2,
            outline=outline,
            characters=chars,
            previous_scenes=[],
        )
        assert "DEC-044" in prompt
        assert "PRODUCT FINAL FORM" in prompt
        assert "NARRATION FIELD RULES" in prompt
        assert "DIALOGUE & THOUGHT DENSITY" in prompt


class TestDec044OutputExampleInjection:
    """T20-21 wire: OUTPUT_EXAMPLE 必须出现 (替代旧 prose JSON template)"""

    def test_batch_prompt_contains_output_example(self):
        writer = _make_writer()
        outline = _mock_outline()
        chars = _mock_characters()
        prompt = writer._build_batch_prompt(
            plot_points=outline["plot_points"],
            outline=outline,
            characters=chars,
            previous_scenes=[],
            scene_id_offset=0,
        )
        # OUTPUT_EXAMPLE 包含 "立春清晨，灰狐独行赴年年之约。" caption 示例
        assert "立春清晨" in prompt or "caption-style" in prompt, \
            "batch prompt 缺少 DEC-044 OUTPUT_EXAMPLE caption 示例"

    def test_single_prompt_contains_output_example(self):
        writer = _make_writer()
        outline = _mock_outline()
        chars = _mock_characters()
        prompt = writer._build_single_scene_prompt(
            plot_point=outline["plot_points"][0],
            plot_point_index=0,
            total_plot_points=2,
            outline=outline,
            characters=chars,
            previous_scenes=[],
        )
        assert "立春清晨" in prompt or "caption-style" in prompt


# ---------------------------------------------------------------------------
# 2. 旧 prose-mode 文本已删除
# ---------------------------------------------------------------------------

class TestOldProseTextRemoved:
    """T20-21 wire: 旧 TTS-era prose 硬要求文本应已被替换"""

    def test_batch_prompt_no_old_zishu_hard_requirement(self):
        writer = _make_writer()
        outline = _mock_outline()
        chars = _mock_characters()
        prompt = writer._build_batch_prompt(
            plot_points=outline["plot_points"],
            outline=outline,
            characters=chars,
            previous_scenes=[],
            scene_id_offset=0,
        )
        # 旧 "【字数硬性要求：必须≥X字】" 应已删除
        assert "【字数硬性要求" not in prompt, \
            "batch prompt 仍含旧 TTS-era 字数硬性要求"
        # 旧 "TTS朗读" 旁白 prose 描述应已删除
        # (NOTE: DEC044_SCREENPLAY_RULES 里有提到 "NOT spoken" 字样, 不要误判)
        # 只判断旧 JSON template 内 "TTS朗读旁白，有文学性" 完整字符串
        assert "TTS朗读旁白，有文学性，详细描写" not in prompt

    def test_single_prompt_no_old_zishu_hard_requirement(self):
        writer = _make_writer()
        outline = _mock_outline()
        chars = _mock_characters()
        prompt = writer._build_single_scene_prompt(
            plot_point=outline["plot_points"][0],
            plot_point_index=0,
            total_plot_points=2,
            outline=outline,
            characters=chars,
            previous_scenes=[],
        )
        assert "【字数硬性要求" not in prompt
        # 旧 "这是TTS朗读的旁白" 完整字符串应已删除
        assert "这是TTS朗读的旁白" not in prompt


# ---------------------------------------------------------------------------
# 3. target_narration_words 改用 DEC-044 公式
# ---------------------------------------------------------------------------

class TestTargetNarrationWordsFormula:
    """T20-21: target_narration_words 改为 min(120, int(duration * 1.5))"""

    def test_single_prompt_target_words_short_duration(self):
        """duration=30s → 30*1.5=45, 不超 120, 用 45"""
        writer = _make_writer()
        outline = _mock_outline()
        chars = _mock_characters()
        prompt = writer._build_single_scene_prompt(
            plot_point={"beat": "test", "description": "x", "estimated_duration_seconds": 30},
            plot_point_index=0,
            total_plot_points=1,
            outline=outline,
            characters=chars,
            previous_scenes=[],
        )
        # 30*1.5 = 45, DEC-044 上限 120 → 取 45
        assert "≤45 CJK 字" in prompt, f"应含 '≤45 CJK 字', prompt={prompt[-1000:]}"

    def test_single_prompt_target_words_long_duration_capped(self):
        """duration=120s → 120*1.5=180, 但 DEC-044 上限 120 → 取 120"""
        writer = _make_writer()
        outline = _mock_outline()
        chars = _mock_characters()
        prompt = writer._build_single_scene_prompt(
            plot_point={"beat": "test", "description": "x", "estimated_duration_seconds": 120},
            plot_point_index=0,
            total_plot_points=1,
            outline=outline,
            characters=chars,
            previous_scenes=[],
        )
        assert "≤120 CJK 字" in prompt

    def test_dec044_narration_max_chars_constant(self):
        """get_dec044_narration_max_chars() 必须返 120"""
        assert get_dec044_narration_max_chars() == 120

    def test_batch_prompt_pp_block_caption_upper_limit(self):
        """batch prompt 内 pp_block 必须显示 caption 上限"""
        writer = _make_writer()
        outline = _mock_outline()
        chars = _mock_characters()
        prompt = writer._build_batch_prompt(
            plot_points=outline["plot_points"],
            outline=outline,
            characters=chars,
            previous_scenes=[],
            scene_id_offset=0,
        )
        # pp_block 应有 "narration caption 上限: ≤120字" 描述
        assert "caption" in prompt.lower() or "≤120" in prompt


# ---------------------------------------------------------------------------
# 4. _expand_narration_if_needed 已 disable
# ---------------------------------------------------------------------------

class TestExpandNarrationDisabled:
    """T20-21: _expand_narration_if_needed v1 直接 disable (return unchanged)"""

    def test_expand_returns_scene_unchanged_short_narration(self):
        """narration 远短于 target_words 也不扩写"""
        writer = _make_writer()
        scene = {
            "scene_heading": "EXT. Test - Day",
            "narration": "短",  # 1 char, 远短于 target 200
            "characters_in_scene": ["char_001"],
            "atmosphere": {"mood": "test"},
        }
        result = asyncio.run(writer._expand_narration_if_needed(scene, target_words=200))
        assert result is scene, "应返回同一对象 (not modified)"
        assert result["narration"] == "短", "narration 不应被扩写"

    def test_expand_returns_scene_unchanged_empty_narration(self):
        """空 narration 也不扩写"""
        writer = _make_writer()
        scene = {"narration": "", "characters_in_scene": []}
        result = asyncio.run(writer._expand_narration_if_needed(scene, target_words=100))
        assert result["narration"] == ""

    def test_expand_no_llm_call(self):
        """_expand_narration_if_needed 不应触发 LLM 调用 (无 monkeypatch 也不应崩)"""
        writer = _make_writer()
        # 故意不设 claude_client / gemini_client
        writer.claude_client = None
        writer.gemini_client = None
        scene = {"narration": "短", "characters_in_scene": []}
        # 应该不报错也不阻塞
        result = asyncio.run(writer._expand_narration_if_needed(scene, target_words=200))
        assert result["narration"] == "短"


# ---------------------------------------------------------------------------
# 5. Universal: 任何故事题材都接通 (不 hardcode 灰狐故事)
# ---------------------------------------------------------------------------

class TestUniversalWireGenericStory:
    """T20-21 wire universal: 都市 / 武侠 / 科幻 / 童话 都受益"""

    def test_wire_works_for_urban_story(self):
        """都市情感故事 — 不含动物角色"""
        writer = _make_writer()
        outline = {
            "plot_points": [
                {"beat": "intro", "description": "陈默在咖啡馆遇见苏晨", "estimated_duration_seconds": 30}
            ],
            "unique_locations": [
                {"location_id": "L001", "display_name": "咖啡馆", "location_type": "INT"}
            ],
            "target_metrics": {"target_duration_seconds": 180},
        }
        chars = {
            "characters": [
                {"id": "char_001", "name": "陈默", "role": "protagonist",
                 "clothing": {"accessories": ["black-framed glasses"]}}
            ]
        }
        prompt = writer._build_single_scene_prompt(
            plot_point=outline["plot_points"][0],
            plot_point_index=0,
            total_plot_points=1,
            outline=outline,
            characters=chars,
            previous_scenes=[],
        )
        # DEC-044 规则仍然注入
        assert "DEC-044" in prompt
        # 都市故事的角色信息正常出现
        assert "陈默" in prompt

    def test_wire_works_for_scifi_story(self):
        """科幻故事 — 机器人 + 未来场景"""
        writer = _make_writer()
        outline = {
            "plot_points": [
                {"beat": "discovery", "description": "机器人发现古老遗迹", "estimated_duration_seconds": 60}
            ],
            "unique_locations": [
                {"location_id": "L001", "display_name": "废墟", "location_type": "EXT"}
            ],
            "target_metrics": {"target_duration_seconds": 240},
        }
        chars = {
            "characters": [
                {"id": "char_001", "name": "R-7", "role": "robot",
                 "clothing": {"accessories": ["metallic alloy plates"]}}
            ]
        }
        prompt = writer._build_batch_prompt(
            plot_points=outline["plot_points"],
            outline=outline,
            characters=chars,
            previous_scenes=[],
            scene_id_offset=0,
        )
        assert "DEC-044" in prompt
        assert "R-7" in prompt


# ---------------------------------------------------------------------------
# 6. 模块导入完整性
# ---------------------------------------------------------------------------

class TestModuleStructure:
    """T20-21 wire: import 路径正确, 模块结构正确"""

    def test_import_dec044_constants(self):
        from app.services.screenplay_writer import ScreenplayWriter
        # 确认 ScreenplayWriter module 能正常 import DEC044 常量
        from app.prompts.screenplay_prompts import (
            DEC044_SCREENPLAY_RULES,
            DEC044_SCREENPLAY_OUTPUT_EXAMPLE,
            get_dec044_narration_max_chars,
        )
        assert DEC044_SCREENPLAY_RULES is not None
        assert DEC044_SCREENPLAY_OUTPUT_EXAMPLE is not None
        assert get_dec044_narration_max_chars() == 120

    def test_dec044_rules_contains_three_blocks(self):
        """DEC044_SCREENPLAY_RULES = PRODUCT_FORM + NARRATION + DIALOGUE 组合"""
        assert "PRODUCT FINAL FORM" in DEC044_SCREENPLAY_RULES
        assert "NARRATION FIELD RULES" in DEC044_SCREENPLAY_RULES
        assert "DIALOGUE & THOUGHT DENSITY" in DEC044_SCREENPLAY_RULES

    def test_writer_imports_dec044_helpers(self):
        """screenplay_writer.py 顶部应 import DEC044 helpers"""
        import inspect
        from app.services import screenplay_writer
        src = inspect.getsource(screenplay_writer)
        assert "DEC044_SCREENPLAY_RULES" in src
        assert "DEC044_SCREENPLAY_OUTPUT_EXAMPLE" in src
        assert "get_dec044_narration_max_chars" in src
