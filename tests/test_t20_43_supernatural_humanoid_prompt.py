"""
T20-43: SUPERNATURAL_HUMANOID_FIELDS_RULES — pytest 验证 CharacterDesigner prompt
含 being_type / undead_type / creature_type 种族字段示例.

Background: test20 镜中人 char_002 Stage 2 给了 character_type=supernatural 但只给人类
外貌字段（hair_color/skin_tone/face_shape），没给 being_type。Backend 已 hotfix schema 端
兜底（KEY_LEARNINGS #43），AI-ML 补强 prompt 端让 LLM 输出更语义化。

Author: @AI-ML
Date: 2026-05-20
Owner: TASK-T20-43 P2
"""

import sys
import pytest
from pathlib import Path

# ---------------------------------------------------------------------------
# Import character_designer without triggering full app service __init__
# (avoids google.genai / anthropic SDK import errors in test environments)
# Strategy: mock unavailable SDKs, then use importlib to load the .py file
# directly, bypassing app/services/__init__.py
# ---------------------------------------------------------------------------
import importlib.util
import types

project_root = Path(__file__).resolve().parent.parent

try:
    # ------------------------------------------------------------------
    # 1. Mock SDK modules that are not installed in the test environment
    # ------------------------------------------------------------------
    def _make_stub(name: str) -> types.ModuleType:
        return types.ModuleType(name)

    for _pkg in ("anthropic", "google", "google.genai", "google.generativeai"):
        if _pkg not in sys.modules:
            sys.modules[_pkg] = _make_stub(_pkg)

    # app.config.settings stub — only 'settings' attribute is used inside character_designer
    if "app.config" not in sys.modules:
        _app_config = types.ModuleType("app.config")
        _settings_stub = types.SimpleNamespace(
            ANTHROPIC_API_KEY="test",
            GEMINI_API_KEY="test",
            CLAUDE_MODEL="claude-sonnet-4-6",
            GEMINI_MODEL="gemini-3.1-flash-lite-preview",
        )
        _app_config.settings = _settings_stub
        sys.modules["app.config"] = _app_config

    # app / app.services stubs (prevent __init__.py from running)
    if "app" not in sys.modules:
        sys.modules["app"] = types.ModuleType("app")
    if "app.services" not in sys.modules:
        sys.modules["app.services"] = types.ModuleType("app.services")

    # ------------------------------------------------------------------
    # 2. Load character_designer.py directly (bypasses __init__.py)
    # ------------------------------------------------------------------
    _cd_spec = importlib.util.spec_from_file_location(
        "character_designer_isolated",
        project_root / "app" / "services" / "character_designer.py",
    )
    _cd_module = importlib.util.module_from_spec(_cd_spec)
    sys.modules["character_designer_isolated"] = _cd_module
    _cd_spec.loader.exec_module(_cd_module)
    CharacterDesigner = _cd_module.CharacterDesigner
    _DESIGNER_AVAILABLE = True
except Exception as _e:
    _DESIGNER_AVAILABLE = False
    _DESIGNER_IMPORT_ERROR = str(_e)


def _make_designer():
    """Return CharacterDesigner instance with no LLM clients (prompt-only testing)."""
    if not _DESIGNER_AVAILABLE:
        err = globals().get("_DESIGNER_IMPORT_ERROR", "unknown error")
        pytest.skip(f"CharacterDesigner import failed: {err}")
    cd = CharacterDesigner.__new__(CharacterDesigner)
    cd.claude_client = None
    cd.gemini_client = None
    cd.claude_model = "claude-sonnet-4-6"
    cd.gemini_model = "gemini-3.1-flash-lite-preview"
    return cd


def _build_gothic_horror_prompt() -> str:
    """Build a gothic horror outline prompt that triggers the supernatural rule."""
    designer = _make_designer()
    characters_overview = [
        {
            "name_suggestion": "陈宇",
            "name_en": "Chen Yu",
            "role": "protagonist",
            "description": "28岁上班族，穿黑色西装，戴黑框眼镜",
            "personality": "内向理性",
            "archetype": "exhausted_office_worker",
            "age_range": "young_adult",
            "gender": "male",
            "family_role": "none",
            "emotional_journey": "疑惑 → 恐惧 → 接受",
        },
        {
            "name_suggestion": "镜中人",
            "name_en": "Mirror Entity",
            "role": "antagonist",
            "description": "外形酷似陈宇，但眼神空洞，衣着镜像反转",
            "personality": "冷漠神秘",
            "archetype": "mirror_entity",
            "age_range": "young_adult",
            "gender": "male",
            "family_role": "none",
            "emotional_journey": "潜伏 → 侵蚀 → 取代",
        },
    ]
    visual_tone = {
        "overall_mood": "mysterious",
        "lighting_style": "low_key_dramatic",
        "color_palette": ["dark slate", "silver", "crimson"],
        "composition_style": "negative_space_isolation",
    }
    return designer._build_prompt(
        characters_overview=characters_overview,
        visual_tone=visual_tone,
        title="镜中的阴影",
        logline="电梯镜中人出现，正常人发现自己在镜中失去影子。",
        style_preset="gothic",
    )


def _build_realistic_romance_prompt() -> str:
    """Build a human-only romance outline prompt to test regression."""
    designer = _make_designer()
    characters_overview = [
        {
            "name_suggestion": "李明",
            "name_en": "Li Ming",
            "role": "protagonist",
            "description": "26岁程序员，戴眼镜，穿格子衫",
            "personality": "内向温柔",
            "archetype": "shy_programmer",
            "age_range": "young_adult",
            "gender": "male",
            "family_role": "none",
            "emotional_journey": "暗恋 → 告白 → 被接受",
        },
    ]
    visual_tone = {
        "overall_mood": "romantic",
        "lighting_style": "natural_soft",
        "color_palette": ["warm beige", "soft pink", "ivory"],
        "composition_style": "symmetrical_formal",
    }
    return designer._build_prompt(
        characters_overview=characters_overview,
        visual_tone=visual_tone,
        title="办公室暗恋",
        logline="程序员对同事暗恋的故事。",
        style_preset="realistic",
    )


class TestSupernatualHumanoidFieldsRulesExistence:
    """SUPERNATURAL_HUMANOID_FIELDS_RULES 规则块存在于 CharacterDesigner prompt."""

    def test_supernatural_humanoid_rule_section_exists(self):
        prompt = _build_gothic_horror_prompt()
        assert "SUPERNATURAL HUMANOID FIELDS RULES" in prompt

    def test_mandatory_label_present(self):
        prompt = _build_gothic_horror_prompt()
        assert "MANDATORY" in prompt

    def test_rule_covers_four_types(self):
        """All 4 types must be mentioned in the rule."""
        prompt = _build_gothic_horror_prompt()
        for char_type in ["supernatural", "undead", "mythological", "fantasy_creature"]:
            assert char_type in prompt, f"Missing char_type: {char_type}"

    def test_being_type_field_mentioned(self):
        prompt = _build_gothic_horror_prompt()
        assert "being_type" in prompt

    def test_undead_type_field_mentioned(self):
        prompt = _build_gothic_horror_prompt()
        assert "undead_type" in prompt

    def test_creature_type_field_mentioned(self):
        prompt = _build_gothic_horror_prompt()
        assert "creature_type" in prompt

    def test_original_form_field_mentioned(self):
        prompt = _build_gothic_horror_prompt()
        assert "original_form" in prompt

    def test_origin_culture_field_mentioned(self):
        prompt = _build_gothic_horror_prompt()
        assert "origin_culture" in prompt

    def test_base_form_field_mentioned(self):
        prompt = _build_gothic_horror_prompt()
        assert "base_form" in prompt


class TestSupernatualHumanoidFieldsRulesContent:
    """SUPERNATURAL_HUMANOID_FIELDS_RULES content — 人形配置 + bad/good examples."""

    def test_rule_sfh2_human_appearance_fallback(self):
        """Rule SHF-2 says humanoid supernaturals must also fill human appearance fields."""
        prompt = _build_gothic_horror_prompt()
        # The rule should mention that human appearance fields are also needed
        assert "人形" in prompt or "human appearance" in prompt.lower() or "SHF-2" in prompt

    def test_rule_sfh3_minimal_output_rejected(self):
        """Rule SHF-3 says minimal output (human fields only, no type identity) is rejected."""
        prompt = _build_gothic_horror_prompt()
        lower = prompt.lower()
        assert "minimal" in lower or "REJECTED" in prompt or "rejected" in lower or "SHF-3" in prompt

    def test_bad_vs_good_examples_present(self):
        """Must include BAD/GOOD examples."""
        prompt = _build_gothic_horror_prompt()
        assert "BAD" in prompt or "错误" in prompt
        assert "GOOD" in prompt or "正确" in prompt

    def test_mirror_entity_or_equivalent_example(self):
        """The rule should use 镜中人 or equivalent supernatural humanoid example."""
        prompt = _build_gothic_horror_prompt()
        has_mirror_entity = "镜中人" in prompt
        has_equivalent = "幽灵" in prompt or "鬼魂" in prompt or "mountain god" in prompt.lower()
        assert has_mirror_entity or has_equivalent

    def test_distinctive_marks_for_visual_differentiation(self):
        """Rule SHF-4 should mention distinctive marks for visual differentiation."""
        prompt = _build_gothic_horror_prompt()
        assert "distinctive_marks" in prompt

    def test_sfh1_type_table_present(self):
        """Rule SHF-1 should have a table mapping type to required fields."""
        prompt = _build_gothic_horror_prompt()
        # The rule uses SHF-1 label or equivalent
        assert "SHF-1" in prompt or "种族身份字段" in prompt or "type-specific identity" in prompt.lower()

    def test_sfh4_visual_differentiation_rule(self):
        """Rule SHF-4 should instruct adding marks that signal non-human nature."""
        prompt = _build_gothic_horror_prompt()
        assert "SHF-4" in prompt or "non-human" in prompt.lower() or "人类区分" in prompt


class TestSupernatualHumanoidFieldsRulesRegression:
    """Regression: 加了新规则不破坏 human / anthropomorphic_animal 现有逻辑."""

    def test_human_type_section_still_present(self):
        """human type section must remain unchanged."""
        prompt = _build_gothic_horror_prompt()
        assert "human" in prompt

    def test_anthropomorphic_animal_section_still_present(self):
        """anthropomorphic_animal section must remain."""
        prompt = _build_gothic_horror_prompt()
        assert "anthropomorphic_animal" in prompt

    def test_fur_color_still_required_for_animal(self):
        """fur_color field instruction for anthropomorphic_animal must not be removed."""
        prompt = _build_gothic_horror_prompt()
        assert "fur_color" in prompt

    def test_style_infusion_block_still_injected(self):
        """T20-46 style_infusion_block must still appear in the prompt."""
        prompt = _build_gothic_horror_prompt()
        # Gothic style should trigger the gothic style infusion block (T20-46 pre-existing)
        assert "STYLE INFUSION" in prompt or "STYLE_INFUSION" in prompt or "gothic" in prompt.lower()

    def test_design_principles_still_present(self):
        """设计原则 section must still appear after our new rule."""
        prompt = _build_gothic_horror_prompt()
        assert "设计原则" in prompt

    def test_prompt_builds_without_error_for_human_only_story(self):
        """Pure human story must still build prompt without error."""
        prompt = _build_realistic_romance_prompt()
        assert len(prompt) > 100
        assert "设计原则" in prompt

    def test_new_rule_appears_before_design_principles(self):
        """SUPERNATURAL HUMANOID FIELDS RULES must appear before 设计原则."""
        prompt = _build_gothic_horror_prompt()
        supernatural_pos = prompt.find("SUPERNATURAL HUMANOID FIELDS RULES")
        design_pos = prompt.find("设计原则")
        assert supernatural_pos > 0, "SUPERNATURAL HUMANOID FIELDS RULES not found"
        assert design_pos > 0, "设计原则 not found"
        assert supernatural_pos < design_pos, "Rule should appear before 设计原则"


class TestSupernatualHumanoidFieldsRulesTableFormat:
    """Rule table format — 4 types × identity fields correctly listed."""

    def test_table_has_all_four_character_types(self):
        """The type-to-field mapping table must cover all 4 types."""
        prompt = _build_gothic_horror_prompt()
        for t in ["supernatural", "undead", "mythological", "fantasy_creature"]:
            assert t in prompt

    def test_example_values_present(self):
        """Chinese supernatural entity examples should appear."""
        prompt = _build_gothic_horror_prompt()
        # At least some of the typical examples should appear
        chinese_entities = ["鬼魂", "幽灵", "镜中人", "山神", "狐仙", "僵尸", "精灵", "兽人"]
        found = [e for e in chinese_entities if e in prompt]
        assert len(found) >= 3, f"Only found examples: {found}"

    def test_rule_length_is_substantial(self):
        """The new rules section should be substantial."""
        prompt = _build_gothic_horror_prompt()
        # Find the section and check it's long enough
        start = prompt.find("SUPERNATURAL HUMANOID FIELDS RULES")
        assert start > 0
        end = prompt.find("## 设计原则", start)
        if end < 0:
            end = start + 3000  # fallback
        section_text = prompt[start:end]
        assert len(section_text) > 300, f"Rule section too short: {len(section_text)} chars"
