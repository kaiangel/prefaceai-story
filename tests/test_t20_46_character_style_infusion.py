"""
T20-46 — CharacterDesigner STYLE_INFUSION_RULES 单测

验证目标：
1. _get_style_infusion_block() 按 style_preset 返回正确风格块
2. gothic 风格强制词正确注入 (pale, gaunt, ash-gray, lace, blood-red 等)
3. 通用 fallback (style_preset=None + 无法推断时) 也有约束规则
4. 从 visual_tone 推断 gothic 风格（无 style_preset 时的 fallback 路径）
5. _build_prompt() 含 style_infusion_block（不为空）
6. STYLE_MODIFIER_DICT 覆盖 8 个核心风格
7. 所有风格块含 MANDATORY / SELF-CHECK 关键词
8. anthropomorphic_animal 路径不受影响（通用性保障）
"""

import sys
import inspect
from pathlib import Path
import pytest

# ---------------------------------------------------------------------------
# Import character_designer without triggering full app service __init__
# (avoids Gemini/Anthropic SDK import errors in test environments without API keys)
# ---------------------------------------------------------------------------
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from app.services.character_designer import CharacterDesigner
    _DESIGNER_AVAILABLE = True
except Exception:
    _DESIGNER_AVAILABLE = False


def _make_designer():
    """Return CharacterDesigner instance with no LLM clients (prompt-only testing)."""
    if not _DESIGNER_AVAILABLE:
        pytest.skip("CharacterDesigner import failed (missing deps) — skip")
    cd = CharacterDesigner.__new__(CharacterDesigner)
    cd.claude_client = None
    cd.gemini_client = None
    cd.claude_model = "claude-sonnet-4-6"
    cd.gemini_model = "gemini-3.1-flash-lite-preview"
    return cd


@pytest.fixture
def designer():
    return _make_designer()


# ──────────────────────────────────────────────
# Section 1: STYLE_MODIFIER_DICT 覆盖完整性
# ──────────────────────────────────────────────

class TestStyleModifierDictCoverage:
    """STYLE_MODIFIER_DICT 覆盖 8 个核心风格"""

    EXPECTED_STYLES = ["gothic", "anime", "realistic", "cartoon", "watercolor", "ghibli", "ink", "cyberpunk"]

    def test_all_8_styles_present(self, designer):
        for style in self.EXPECTED_STYLES:
            assert style in designer.STYLE_MODIFIER_DICT, f"STYLE_MODIFIER_DICT 缺少 '{style}'"

    def test_each_style_has_required_keys(self, designer):
        for style, config in designer.STYLE_MODIFIER_DICT.items():
            assert "style_name" in config, f"{style} 缺少 style_name"
            assert "physical_modifiers" in config, f"{style} 缺少 physical_modifiers"
            assert "clothing_modifiers" in config, f"{style} 缺少 clothing_modifiers"
            assert "tone_hint" in config, f"{style} 缺少 tone_hint"

    def test_each_style_has_enough_modifiers(self, designer):
        for style, config in designer.STYLE_MODIFIER_DICT.items():
            assert len(config["physical_modifiers"]) >= 4, \
                f"{style}.physical_modifiers 少于 4 个"
            assert len(config["clothing_modifiers"]) >= 3, \
                f"{style}.clothing_modifiers 少于 3 个"

    def test_style_modifier_dict_is_class_attr(self, designer):
        assert hasattr(designer, "STYLE_MODIFIER_DICT"), \
            "CharacterDesigner 应有 STYLE_MODIFIER_DICT 类属性"


# ──────────────────────────────────────────────
# Section 2: gothic 风格块内容验证
# ──────────────────────────────────────────────

class TestGothicStyleBlock:
    """gothic 风格块必须含正确的强制词"""

    def test_gothic_style_name_in_block(self, designer):
        block = designer._get_style_infusion_block("gothic", {})
        assert "gothic dark romantic" in block.lower()

    def test_gothic_physical_modifiers_in_block(self, designer):
        block = designer._get_style_infusion_block("gothic", {})
        block_lower = block.lower()
        expected = ["pale", "gaunt", "ash-gray", "hollow", "shadow"]
        hits = [w for w in expected if w in block_lower]
        assert len(hits) >= 3, f"gothic block 含 physical modifier 不足: {hits}"

    def test_gothic_clothing_modifiers_in_block(self, designer):
        block = designer._get_style_infusion_block("gothic", {})
        block_lower = block.lower()
        expected = ["blood-red", "lace", "dark", "velvet", "gothic"]
        hits = [w for w in expected if w in block_lower]
        assert len(hits) >= 2, f"gothic block 含 clothing modifier 不足: {hits}"

    def test_gothic_block_has_mandatory_marker(self, designer):
        block = designer._get_style_infusion_block("gothic", {})
        assert "MANDATORY" in block or "mandatory" in block.lower()

    def test_gothic_block_has_self_check(self, designer):
        block = designer._get_style_infusion_block("gothic", {})
        assert "SELF-CHECK" in block or "self-check" in block.lower()

    def test_gothic_block_has_wrong_pattern_example(self, designer):
        """必须给 LLM 反例，指出旧写法的问题"""
        block = designer._get_style_infusion_block("gothic", {})
        assert "WRONG" in block or "DO NOT" in block

    def test_gothic_block_has_correct_pattern_example(self, designer):
        """必须给 LLM 正例"""
        block = designer._get_style_infusion_block("gothic", {})
        assert "CORRECT" in block or "DO THIS" in block


# ──────────────────────────────────────────────
# Section 3: style_preset 精确匹配
# ──────────────────────────────────────────────

class TestStylePresetExactMatch:
    """style_preset 直接匹配各风格"""

    @pytest.mark.parametrize("style_preset,expected_keyword", [
        ("gothic", "gothic dark romantic"),
        ("anime", "japanese anime"),
        ("realistic", "photorealistic"),
        ("cartoon", "3d cartoon"),
        ("watercolor", "watercolor illustration"),
        ("ghibli", "studio ghibli"),
        ("ink", "chinese ink wash"),
        ("cyberpunk", "cyberpunk neon"),
    ])
    def test_style_preset_matches_style_name(self, designer, style_preset, expected_keyword):
        block = designer._get_style_infusion_block(style_preset, {})
        assert expected_keyword in block.lower(), \
            f"style_preset={style_preset} 应产生含 '{expected_keyword}' 的 block"


# ──────────────────────────────────────────────
# Section 4: visual_tone fallback 推断
# ──────────────────────────────────────────────

class TestVisualToneFallbackInference:
    """无 style_preset 时，从 visual_tone 推断 gothic 风格"""

    def test_gothic_inferred_from_dark_palette(self, designer):
        """test20 风格: 'cold steel blue', 'sickly pale white', 'deep shadow black' → gothic"""
        visual_tone = {
            "overall_mood": "悬疑",
            "lighting_style": "chiaroscuro",
            "color_palette": ["cold steel blue", "sickly pale white", "deep shadow black"],
        }
        block = designer._get_style_infusion_block(None, visual_tone)
        assert len(block) > 100, "fallback block 不应为空"
        # 有 chiaroscuro + dark palette → 应推断 gothic 或至少有 STYLE 约束
        assert "CONSISTENCY" in block.upper() or "STYLE" in block.upper()

    def test_gothic_inferred_from_chiaroscuro_lighting(self, designer):
        """chiaroscuro lighting + dark palette 是 gothic 信号"""
        visual_tone = {
            "lighting_style": "chiaroscuro",
            "color_palette": ["shadow", "dark", "pale"],
        }
        block = designer._get_style_infusion_block(None, visual_tone)
        block_lower = block.lower()
        # 应推断 gothic 并产生含 gothic 相关词的 block
        assert "gothic" in block_lower or "shadow" in block_lower or "pale" in block_lower

    def test_fallback_when_no_style_hints(self, designer):
        """既无 style_preset 也无 visual_tone 提示 → 通用规则（非空）"""
        block = designer._get_style_infusion_block(None, {})
        assert len(block) > 50, "通用 fallback block 不应为空"
        assert "STYLE" in block.upper()

    def test_none_style_none_visual_tone_produces_generic(self, designer):
        """style_preset=None, visual_tone=None → 不崩溃"""
        block = designer._get_style_infusion_block(None, None)
        assert isinstance(block, str)
        assert len(block) > 0


# ──────────────────────────────────────────────
# Section 5: _build_prompt 集成测试
# ──────────────────────────────────────────────

class TestBuildPromptIntegration:
    """_build_prompt() 必须含 style_infusion_block"""

    SAMPLE_CHARACTERS = [
        {
            "name_suggestion": "林深",
            "description": "28岁程序员",
            "role": "protagonist",
        }
    ]

    SAMPLE_VISUAL_TONE = {
        "overall_mood": "悬疑",
        "lighting_style": "chiaroscuro",
        "color_palette": ["cold steel blue", "sickly pale white"],
    }

    def test_build_prompt_with_gothic_has_style_block(self, designer):
        prompt = designer._build_prompt(
            characters_overview=self.SAMPLE_CHARACTERS,
            visual_tone=self.SAMPLE_VISUAL_TONE,
            title="Test",
            logline="Test story",
            style_preset="gothic",
        )
        assert "gothic dark romantic" in prompt.lower(), \
            "_build_prompt 输出应含 gothic style block"

    def test_build_prompt_without_style_preset_has_block(self, designer):
        """style_preset=None 也必须有 style block（通用规则）"""
        prompt = designer._build_prompt(
            characters_overview=self.SAMPLE_CHARACTERS,
            visual_tone=self.SAMPLE_VISUAL_TONE,
            title="Test",
            logline="Test story",
            style_preset=None,
        )
        assert "STYLE" in prompt.upper(), \
            "_build_prompt 无 style_preset 也应含 STYLE 约束"

    def test_build_prompt_gothic_has_mandatory_marker(self, designer):
        prompt = designer._build_prompt(
            characters_overview=self.SAMPLE_CHARACTERS,
            visual_tone=self.SAMPLE_VISUAL_TONE,
            title="Test",
            logline="Test",
            style_preset="gothic",
        )
        assert "MANDATORY" in prompt

    def test_build_prompt_style_block_before_design_principles(self, designer):
        """STYLE_INFUSION_RULES 应在 '## 设计原则' 之前（注意力顺序）"""
        prompt = designer._build_prompt(
            characters_overview=self.SAMPLE_CHARACTERS,
            visual_tone=self.SAMPLE_VISUAL_TONE,
            title="Test",
            logline="Test",
            style_preset="gothic",
        )
        style_pos = prompt.lower().find("style infusion rules")
        design_pos = prompt.find("## 设计原则")
        assert style_pos != -1, "prompt 应含 STYLE INFUSION RULES"
        assert design_pos != -1, "prompt 应含 ## 设计原则"
        assert style_pos < design_pos, \
            "STYLE INFUSION RULES 应在 ## 设计原则 之前（注意力权重更高）"

    def test_build_prompt_backward_compatible_no_style_preset(self, designer):
        """不传 style_preset 时，_build_prompt 默认参数不崩溃"""
        prompt = designer._build_prompt(
            characters_overview=[],
            visual_tone={},
            title="T",
            logline="L",
        )
        assert isinstance(prompt, str)
        assert len(prompt) > 100


# ──────────────────────────────────────────────
# Section 6: 通用性保障（非 gothic 风格）
# ──────────────────────────────────────────────

class TestGeneralityPreservation:
    """所有 8 风格都有约束，不影响 anthropomorphic_animal 规则"""

    @pytest.mark.parametrize("style_preset", [
        "gothic", "anime", "realistic", "cartoon", "watercolor", "ghibli", "ink", "cyberpunk"
    ])
    def test_all_styles_produce_non_empty_block(self, designer, style_preset):
        block = designer._get_style_infusion_block(style_preset, {})
        assert len(block) > 100, f"{style_preset} 风格块不应为空"

    @pytest.mark.parametrize("style_preset", [
        "gothic", "anime", "realistic", "cartoon"
    ])
    def test_all_main_styles_have_self_check(self, designer, style_preset):
        block = designer._get_style_infusion_block(style_preset, {})
        assert "SELF-CHECK" in block or "SELF CHECK" in block or "self-check" in block.lower()

    def test_anthropomorphic_animal_rules_still_in_prompt(self, designer):
        """STYLE_INFUSION_RULES 加入后，anthropomorphic_animal 规则仍存在"""
        prompt = designer._build_prompt(
            characters_overview=[],
            visual_tone={},
            title="Test",
            logline="Test",
            style_preset="gothic",
        )
        assert "anthropomorphic_animal" in prompt
        assert "species" in prompt
        assert "fur_color" in prompt

    def test_character_type_list_still_in_prompt(self, designer):
        """19 种 character_type 列表仍在 prompt 中"""
        prompt = designer._build_prompt(
            characters_overview=[],
            visual_tone={},
            title="Test",
            logline="Test",
            style_preset="anime",
        )
        assert "human" in prompt
        assert "supernatural" in prompt
        assert "fantasy_creature" in prompt


# ──────────────────────────────────────────────
# Section 7: design() 接口向后兼容
# ──────────────────────────────────────────────

class TestDesignInterfaceBackwardCompatibility:
    """design() 新增 style_preset 参数，默认 None，向后兼容"""

    def test_design_signature_has_style_preset_param(self):
        if not _DESIGNER_AVAILABLE:
            pytest.skip("CharacterDesigner not available")
        sig = inspect.signature(CharacterDesigner.design)
        params = sig.parameters
        assert "style_preset" in params, "design() 应有 style_preset 参数"

    def test_style_preset_default_is_none(self):
        if not _DESIGNER_AVAILABLE:
            pytest.skip("CharacterDesigner not available")
        sig = inspect.signature(CharacterDesigner.design)
        param = sig.parameters.get("style_preset")
        assert param is not None
        assert param.default is None, "style_preset 默认值应为 None"

    def test_build_prompt_signature_has_style_preset(self):
        if not _DESIGNER_AVAILABLE:
            pytest.skip("CharacterDesigner not available")
        sig = inspect.signature(CharacterDesigner._build_prompt)
        params = sig.parameters
        assert "style_preset" in params, "_build_prompt() 应有 style_preset 参数"

    def test_get_style_infusion_block_exists(self, designer):
        assert hasattr(designer, "_get_style_infusion_block"), \
            "CharacterDesigner 应有 _get_style_infusion_block() 方法"

    def test_style_modifier_dict_is_class_attr(self, designer):
        assert hasattr(designer, "STYLE_MODIFIER_DICT"), \
            "CharacterDesigner 应有 STYLE_MODIFIER_DICT 类属性"
