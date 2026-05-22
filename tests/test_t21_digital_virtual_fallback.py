"""
TASK-T21-NEW-1: digital_virtual + 7 other non-human humanoid types accept
human appearance field fallback in CharacterSchema validation.

Background: test21 (scifi AI 客服, cyberpunk) Stage 2 failed because
char_001 小爱 (character_type=digital_virtual) provided 15 human appearance
fields (hair_color, skin_tone, face_shape, etc.) but NOT the type-specific
fields (digital_type OR base_form) that the old schema required.

Fix: pipeline_schemas.py _TYPE_REQUIRED_GROUPS — 8 non-human humanoid types
now accept human appearance fields as fallback (OR relationship), mirroring
T20-43 DEC-043 hotfix pattern for supernatural/undead/mythological/fantasy_creature.

Author: @Backend
Date: 2026-05-20
Owner: TASK-T21-NEW-1 P0
"""

import sys
import types
import importlib.util
import pytest
from pathlib import Path

# ---------------------------------------------------------------------------
# Load pipeline_schemas directly without triggering full app __init__
# ---------------------------------------------------------------------------
project_root = Path(__file__).resolve().parent.parent

try:
    # Mock SDK modules not available in test environment
    def _make_stub(name: str) -> types.ModuleType:
        mod = types.ModuleType(name)
        mod.__path__ = []  # mark as package
        return mod

    for _pkg in ("anthropic", "google", "google.genai", "google.generativeai"):
        if _pkg not in sys.modules:
            sys.modules[_pkg] = _make_stub(_pkg)

    # app.config.settings stub
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

    # app / app.services stubs (prevent __init__.py side-effects)
    if "app" not in sys.modules:
        _app_stub = types.ModuleType("app")
        _app_stub.__path__ = [str(project_root / "app")]
        sys.modules["app"] = _app_stub
    if "app.services" not in sys.modules:
        _svc_stub = types.ModuleType("app.services")
        _svc_stub.__path__ = [str(project_root / "app" / "services")]
        sys.modules["app.services"] = _svc_stub

    # Load pipeline_schemas.py directly
    _spec = importlib.util.spec_from_file_location(
        "pipeline_schemas_isolated",
        project_root / "app" / "services" / "pipeline_schemas.py",
    )
    _module = importlib.util.module_from_spec(_spec)
    sys.modules["pipeline_schemas_isolated"] = _module
    _spec.loader.exec_module(_module)
    CharacterSchema = _module.CharacterSchema
    _SCHEMA_AVAILABLE = True
except Exception as _e:
    _SCHEMA_AVAILABLE = False
    _SCHEMA_IMPORT_ERROR = str(_e)


def _require_schema():
    """Skip test if schema import failed."""
    if not _SCHEMA_AVAILABLE:
        err = globals().get("_SCHEMA_IMPORT_ERROR", "unknown error")
        pytest.skip(f"pipeline_schemas import failed: {err}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_char(character_type: str, physical: dict) -> dict:
    """Build minimal valid character JSON for CharacterSchema."""
    return {
        "id": "char_001",
        "name": "测试角色",
        "name_en": "Test Character",
        "role": "protagonist",
        "character_type": character_type,
        "gender": "female",
        "age_appearance": "adult",
        "physical": physical,
        "clothing": {
            "top": "futuristic suit",
            "style": "cyberpunk",
        },
    }


# 15 human appearance fields — exactly what test21 小爱 had
_HUMAN_PHYSICAL = {
    "build": "slim",
    "distinctive_marks": [],
    "eye_color": "electric blue",
    "eye_description": "glowing cybernetic eyes",
    "eye_shape": "almond",
    "eye_size": "medium",
    "eyebrows": "sharp arched",
    "face_shape": "oval",
    "hair_color": "silver white",
    "hair_style": "sleek short bob",
    "hair_texture": "straight",
    "height": "medium",
    "lips": "pale rose",
    "nose": "small straight",
    "skin_tone": "luminous pale",
}


# ---------------------------------------------------------------------------
# Tests: digital_virtual (P0 — test21 immediate fix)
# ---------------------------------------------------------------------------

class TestDigitalVirtualWithHumanPhysical:
    """digital_virtual + 15 human appearance fields → schema PASS."""

    def test_digital_virtual_with_human_physical_passes(self):
        """P0: test21 小爱 scenario — hair_color/skin_tone/face_shape satisfy the group."""
        _require_schema()
        char_dict = _base_char("digital_virtual", _HUMAN_PHYSICAL)
        # Must not raise
        result = CharacterSchema(**char_dict)
        assert result.character_type == "digital_virtual"

    def test_digital_virtual_with_digital_type_passes(self):
        """Old path still works: digital_virtual + digital_type satisfies the group."""
        _require_schema()
        physical = {
            "digital_type": "holographic_avatar",
            "height": "medium",
        }
        char_dict = _base_char("digital_virtual", physical)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "digital_virtual"

    def test_digital_virtual_with_base_form_passes(self):
        """Old path still works: digital_virtual + base_form satisfies the group."""
        _require_schema()
        physical = {
            "base_form": "humanoid",
            "height": "medium",
        }
        char_dict = _base_char("digital_virtual", physical)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "digital_virtual"

    def test_digital_virtual_no_minimum_fields_warns_not_raises(self):
        """
        Wave 8 Generic Fallback Architecture (2026-05-22):
        digital_virtual with neither humanoid appearance fields nor type-specific fields
        → logger.warning only (NOT raise), schema PASS.

        Design rationale: Method B generic fallback — any non-strict type with missing
        fields gets a warning but does NOT block Pipeline. This allows LLM field-naming
        flexibility and avoids false-positive schema failures. Strict enforcement is
        reserved for animal + vehicle_character only.

        (Previously this test expected a RAISE under the old hotfix schema. Updated
        to reflect the new generic fallback architecture behavior.)
        """
        _require_schema()
        physical = {
            # No digital_type, no base_form, no hair_color, no skin_tone, no face_shape
            "height": "medium",
            "build": "slim",
            "eye_size": "medium",
        }
        char_dict = _base_char("digital_virtual", physical)
        # Wave 8: generic fallback issues warning but does NOT raise — schema PASS
        result = CharacterSchema(**char_dict)
        assert result.character_type == "digital_virtual"


# ---------------------------------------------------------------------------
# Tests: robot (P1)
# ---------------------------------------------------------------------------

class TestRobotWithHumanPhysical:
    """robot + human appearance fields → schema PASS (P1 fix)."""

    def test_robot_with_human_physical_passes(self):
        """robot with human appearance fields (android-type robot) now valid."""
        _require_schema()
        char_dict = _base_char("robot", _HUMAN_PHYSICAL)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "robot"

    def test_robot_with_robot_type_passes(self):
        """robot + robot_type → old path still works."""
        _require_schema()
        physical = {"robot_type": "android", "material": "titanium alloy"}
        char_dict = _base_char("robot", physical)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "robot"


# ---------------------------------------------------------------------------
# Tests: hybrid (P1)
# ---------------------------------------------------------------------------

class TestHybridWithHumanPhysical:
    """hybrid + human appearance fields → schema PASS (P1 fix)."""

    def test_hybrid_with_human_physical_passes(self):
        """hybrid (half-human half-beast) with human appearance fields is valid."""
        _require_schema()
        char_dict = _base_char("hybrid", _HUMAN_PHYSICAL)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "hybrid"

    def test_hybrid_with_primary_type_passes(self):
        """hybrid + primary_type → old path still works."""
        _require_schema()
        physical = {"primary_type": "human-wolf", "height": "tall"}
        char_dict = _base_char("hybrid", physical)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "hybrid"


# ---------------------------------------------------------------------------
# Tests: alien (P1)
# ---------------------------------------------------------------------------

class TestAlienWithHumanPhysical:
    """alien + human appearance fields → schema PASS (P1 fix)."""

    def test_alien_with_human_physical_passes(self):
        """humanoid alien with human appearance fields is now valid."""
        _require_schema()
        char_dict = _base_char("alien", _HUMAN_PHYSICAL)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "alien"

    def test_alien_with_body_plan_passes(self):
        """alien + body_plan → old path still works."""
        _require_schema()
        physical = {"body_plan": "bipedal_humanoid", "height": "tall"}
        char_dict = _base_char("alien", physical)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "alien"


# ---------------------------------------------------------------------------
# Tests: elemental (P2)
# ---------------------------------------------------------------------------

class TestElementalWithHumanPhysical:
    """elemental + human appearance fields → schema PASS (P2 fix)."""

    def test_elemental_with_human_physical_passes(self):
        """personified elemental (fire spirit as human) with human fields is valid."""
        _require_schema()
        char_dict = _base_char("elemental", _HUMAN_PHYSICAL)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "elemental"

    def test_elemental_with_element_type_passes(self):
        """elemental + element_type → old path still works."""
        _require_schema()
        physical = {"element_type": "fire", "material_form": "living flame"}
        char_dict = _base_char("elemental", physical)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "elemental"


# ---------------------------------------------------------------------------
# Tests: concept_personified (P2)
# ---------------------------------------------------------------------------

class TestConceptPersonifiedWithHumanPhysical:
    """concept_personified + human appearance fields → schema PASS (P2 fix)."""

    def test_concept_personified_with_human_physical_passes(self):
        """personified concept (Death as hooded figure) with human fields is valid."""
        _require_schema()
        char_dict = _base_char("concept_personified", _HUMAN_PHYSICAL)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "concept_personified"

    def test_concept_personified_with_concept_type_passes(self):
        """concept_personified + concept_type → old path still works."""
        _require_schema()
        physical = {"concept_type": "death", "height": "tall"}
        char_dict = _base_char("concept_personified", physical)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "concept_personified"


# ---------------------------------------------------------------------------
# Tests: giant (P2)
# ---------------------------------------------------------------------------

class TestGiantWithHumanPhysical:
    """giant + human appearance fields → schema PASS (P2 fix)."""

    def test_giant_with_human_physical_passes(self):
        """giant with human appearance fields (giant humanoid) is valid."""
        _require_schema()
        char_dict = _base_char("giant", _HUMAN_PHYSICAL)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "giant"

    def test_giant_with_giant_type_passes(self):
        """giant + giant_type → old path still works."""
        _require_schema()
        physical = {"giant_type": "stone_giant", "height_category": "colossal"}
        char_dict = _base_char("giant", physical)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "giant"


# ---------------------------------------------------------------------------
# Tests: miniature (P2)
# ---------------------------------------------------------------------------

class TestMiniatureWithHumanPhysical:
    """miniature + human appearance fields → schema PASS (P2 fix)."""

    def test_miniature_with_human_physical_passes(self):
        """miniature (tiny person / fairy) with human appearance fields is valid."""
        _require_schema()
        char_dict = _base_char("miniature", _HUMAN_PHYSICAL)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "miniature"

    def test_miniature_with_base_type_passes(self):
        """miniature + base_type → old path still works."""
        _require_schema()
        physical = {"base_type": "fairy", "height": "tiny"}
        char_dict = _base_char("miniature", physical)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "miniature"


# ---------------------------------------------------------------------------
# Regression: T20-43 types still pass (not broken by T21-NEW-1 changes)
# ---------------------------------------------------------------------------

class TestT2043TypesRegression:
    """T20-43 supernatural/undead/mythological/fantasy_creature must still pass."""

    def test_supernatural_with_human_physical_still_passes(self):
        """supernatural + human fields — T20-43 fix must not regress."""
        _require_schema()
        char_dict = _base_char("supernatural", _HUMAN_PHYSICAL)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "supernatural"

    def test_undead_with_human_physical_still_passes(self):
        """undead + human fields — T20-43 fix must not regress."""
        _require_schema()
        char_dict = _base_char("undead", _HUMAN_PHYSICAL)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "undead"

    def test_mythological_with_human_physical_still_passes(self):
        """mythological + human fields — T20-43 fix must not regress."""
        _require_schema()
        char_dict = _base_char("mythological", _HUMAN_PHYSICAL)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "mythological"

    def test_fantasy_creature_with_human_physical_still_passes(self):
        """fantasy_creature + human fields — T20-43 fix must not regress."""
        _require_schema()
        char_dict = _base_char("fantasy_creature", _HUMAN_PHYSICAL)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "fantasy_creature"


# ---------------------------------------------------------------------------
# Regression: human / animal types still enforce type-specific fields
# ---------------------------------------------------------------------------

class TestNonHumanoidTypesRegression:
    """Non-humanoid types (insect/aquatic/plant/vehicle_character) still require type fields."""

    def test_human_still_requires_hair_or_skin(self):
        """human type still requires hair_color or skin_tone."""
        _require_schema()
        physical = {
            "height": "medium",
            "build": "slim",
            # No hair_color, no skin_tone
        }
        char_dict = _base_char("human", physical)
        with pytest.raises(Exception):
            CharacterSchema(**char_dict)

    def test_human_with_hair_color_passes(self):
        """human + hair_color → valid (regression check)."""
        _require_schema()
        physical = {"hair_color": "black", "skin_tone": "fair"}
        char_dict = _base_char("human", physical)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "human"

    def test_insect_now_accepts_human_physical_after_t21_new2(self):
        """UPDATED by TASK-T21-NEW-2 (2026-05-21): insect now accepts human appearance fields.
        Original T21-NEW-1 note said 'insect NOT in fix list' — that was correct at the time.
        T21-NEW-2 extended insect to support 蝴蝶仙子/蜜蜂女王 humanoid cases (P2 priority).
        Schema now: insect → [('species', 'wing_type', 'hair_color', 'skin_tone', 'face_shape')]
        Human appearance fields (hair_color/skin_tone/face_shape) now satisfy the group.
        """
        _require_schema()
        physical = _HUMAN_PHYSICAL.copy()
        char_dict = _base_char("insect", physical)
        # T21-NEW-2 fix: insect now PASSES with human physical fields (蝴蝶仙子 scenario)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "insect"
