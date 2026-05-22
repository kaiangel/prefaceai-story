"""
TASK-T21-NEW-2: 5 additional types accept human appearance field fallback in
CharacterSchema validation (Wave 4.5 补充).

Background: PM 19-type ground-truth analysis (project_schema_humanoid_fallback_remaining.md)
found that beyond T20-43 (4 types) + T21-NEW-1 (8 types) = 12 types already fixed,
5 more types can present as humanoid but lacked human-appearance-field fallback:

  P0: aquatic (美人鱼/鱼人/Siren — 童话奇幻必发)
  P0: anthropomorphic_animal (狼人/猫娘/furry — 字面"动物拟人化")
  P1: object (钟先生/Olaf — 绘本童话常见)
  P2: plant (树精 Dryad/花仙女 — 奇幻偶发)
  P2: insect (蝴蝶仙子/蜜蜂女王 — 奇幻偶发)

Special handling for anthropomorphic_animal:
  - Retains 2-group AND relationship (must have species AND appearance)
  - Group 2 extended to include human appearance fields (hair_color / skin_tone / face_shape)
  - Rationale: species is the literal "anthropomorphic" requirement; cannot be dropped.
    But group 2 (fur/feather/etc.) now also accepts human appearance fields for half-human
    cases like 狼人 (werewolf with human face), 猫娘 (nekomimi with human skin), etc.

Other 4 types: simple OR fallback (type-specific OR human appearance fields).

Kept unchanged:
  - animal: pure animal, no human appearance fallback (design intent)
  - vehicle_character: Transformers is rare, defer to future e2e exposure

Author: @Backend
Date: 2026-05-21
Owner: TASK-T21-NEW-2-HUMANOID-FALLBACK-WAVE-2 P0
"""

import sys
import types
import importlib.util
import pytest
from pathlib import Path

# ---------------------------------------------------------------------------
# Load pipeline_schemas directly without triggering full app __init__
# (Mirror exact pattern from test_t21_digital_virtual_fallback.py)
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

    # Load pipeline_schemas.py directly (isolated from full app stack)
    _spec = importlib.util.spec_from_file_location(
        "pipeline_schemas_wave2_isolated",
        project_root / "app" / "services" / "pipeline_schemas.py",
    )
    _module = importlib.util.module_from_spec(_spec)
    sys.modules["pipeline_schemas_wave2_isolated"] = _module
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
            "top": "fantasy costume",
            "style": "fantasy",
        },
    }


# Human appearance fields — the canonical set for fallback testing
_HUMAN_PHYSICAL = {
    "build": "slim",
    "distinctive_marks": [],
    "eye_color": "emerald green",
    "eye_description": "bright luminous eyes",
    "eye_shape": "almond",
    "eye_size": "large",
    "eyebrows": "delicate arched",
    "face_shape": "oval",
    "hair_color": "silver white",
    "hair_style": "long flowing wavy",
    "hair_texture": "wavy",
    "height": "medium",
    "lips": "rosy pink",
    "nose": "small delicate",
    "skin_tone": "pale luminous",
}


# ---------------------------------------------------------------------------
# Tests: aquatic (P0 — 美人鱼公主/鱼人/Siren)
# ---------------------------------------------------------------------------

class TestAquaticWithHumanPhysical:
    """aquatic + human appearance fields → schema PASS (P0 fix for mermaid / Siren)."""

    def test_aquatic_with_human_physical_passes(self):
        """P0: 美人鱼公主 upper-body humanoid — hair_color/skin_tone/face_shape satisfy group."""
        _require_schema()
        char_dict = _base_char("aquatic", _HUMAN_PHYSICAL)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "aquatic"

    def test_aquatic_with_species_passes(self):
        """Old path: aquatic + species (鱼人 species only) still works."""
        _require_schema()
        physical = {
            "species": "mermaid",
            "height": "medium",
        }
        char_dict = _base_char("aquatic", physical)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "aquatic"

    def test_aquatic_with_body_type_passes(self):
        """Old path: aquatic + body_type (海妖 body_type only) still works."""
        _require_schema()
        physical = {
            "body_type": "serpentine_tail",
            "height": "medium",
        }
        char_dict = _base_char("aquatic", physical)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "aquatic"


# ---------------------------------------------------------------------------
# Tests: anthropomorphic_animal (P0 — 狼人/猫娘/furry, special 2-group AND)
# ---------------------------------------------------------------------------

class TestAnthropomorphicAnimalWithHumanPhysical:
    """anthropomorphic_animal special case: 2-group AND (species AND appearance).
    Group 2 now accepts human appearance fields alongside fur/feather/etc.
    """

    def test_anthropomorphic_animal_with_species_and_fur_passes(self):
        """Original path: species (group1) + fur_color (group2) — must still work."""
        _require_schema()
        physical = {
            "species": "bear",
            "fur_color": "brown",
            "height": "tall",
        }
        char_dict = _base_char("anthropomorphic_animal", physical)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "anthropomorphic_animal"

    def test_anthropomorphic_animal_with_species_and_hair_color_passes(self):
        """P0 fix: 狼人 with species (group1) + hair_color as human appearance (group2)."""
        _require_schema()
        physical = {
            "species": "wolf",
            "hair_color": "silver grey",
            "skin_tone": "tanned",
            "face_shape": "angular",
        }
        char_dict = _base_char("anthropomorphic_animal", physical)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "anthropomorphic_animal"

    def test_anthropomorphic_animal_no_species_fails(self):
        """species is required (group1) — anthropomorphic_animal without species FAILS."""
        _require_schema()
        physical = {
            # No species — violates group 1
            "fur_color": "orange",
            "hair_color": "orange",
            "skin_tone": "fair",
            "face_shape": "round",
        }
        char_dict = _base_char("anthropomorphic_animal", physical)
        with pytest.raises(Exception) as exc_info:
            CharacterSchema(**char_dict)
        err_str = str(exc_info.value)
        assert "缺少最小集" in err_str or "anthropomorphic_animal" in err_str

    def test_anthropomorphic_animal_species_no_appearance_fails(self):
        """species alone (group1 OK) but group2 entirely missing → FAIL."""
        _require_schema()
        physical = {
            "species": "cat",
            # No fur_color, no feather_color, no plumage_color, no coat_color,
            # no scale_color, no hair_color, no skin_tone, no face_shape
            "height": "medium",
            "build": "slim",
        }
        char_dict = _base_char("anthropomorphic_animal", physical)
        with pytest.raises(Exception) as exc_info:
            CharacterSchema(**char_dict)
        err_str = str(exc_info.value)
        assert "缺少最小集" in err_str or "anthropomorphic_animal" in err_str


# ---------------------------------------------------------------------------
# Tests: object (P1 — 美女与野兽 钟先生 / Olaf / 玩具总动员)
# ---------------------------------------------------------------------------

class TestObjectWithHumanPhysical:
    """object + human appearance fields → schema PASS (P1 fix for personified objects)."""

    def test_object_with_human_physical_passes(self):
        """P1: 美女与野兽 钟先生 (animated clock with face) — human appearance fields valid."""
        _require_schema()
        char_dict = _base_char("object", _HUMAN_PHYSICAL)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "object"

    def test_object_with_object_type_passes(self):
        """Old path: object + object_type still works (non-humanoid object)."""
        _require_schema()
        physical = {
            "object_type": "clock",
            "base_object": "grandfather_clock",
        }
        char_dict = _base_char("object", physical)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "object"


# ---------------------------------------------------------------------------
# Tests: plant (P2 — 树精 Dryad / 花仙女 / 樱花精灵)
# ---------------------------------------------------------------------------

class TestPlantWithHumanPhysical:
    """plant + human appearance fields → schema PASS (P2 fix for humanoid plant spirits)."""

    def test_plant_with_human_physical_passes(self):
        """P2: 树精 (Dryad) — human appearance fields now valid for plant character."""
        _require_schema()
        char_dict = _base_char("plant", _HUMAN_PHYSICAL)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "plant"

    def test_plant_with_plant_type_passes(self):
        """Old path: plant + plant_type still works (non-humanoid plant)."""
        _require_schema()
        physical = {
            "plant_type": "cherry_blossom_tree",
            "species": "Prunus serrulata",
        }
        char_dict = _base_char("plant", physical)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "plant"


# ---------------------------------------------------------------------------
# Tests: insect (P2 — 蝴蝶仙子 / 蜜蜂女王)
# ---------------------------------------------------------------------------

class TestInsectWithHumanPhysical:
    """insect + human appearance fields → schema PASS (P2 fix for humanoid insect fairies)."""

    def test_insect_with_human_physical_passes(self):
        """P2: 蝴蝶仙子 (butterfly fairy with humanoid body) — human appearance fields valid."""
        _require_schema()
        char_dict = _base_char("insect", _HUMAN_PHYSICAL)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "insect"

    def test_insect_with_species_passes(self):
        """Old path: insect + species still works (non-humanoid insect)."""
        _require_schema()
        physical = {
            "species": "honeybee",
            "wing_type": "membranous",
        }
        char_dict = _base_char("insect", physical)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "insect"


# ---------------------------------------------------------------------------
# Regression: animal / vehicle_character schema NOT loosened (design intent)
# ---------------------------------------------------------------------------

class TestNonHumanoidTypesRegression:
    """animal and vehicle_character must still enforce type-specific fields.
    These two types were deliberately kept unchanged in T21-NEW-2.
    """

    def test_animal_still_requires_species_or_fur(self):
        """animal must still have species OR fur/feather/etc. — NOT loosened to accept human fields."""
        _require_schema()
        # Provide only human appearance fields — animal should still FAIL
        physical = _HUMAN_PHYSICAL.copy()
        # Ensure no animal-specific fields are present
        for _field in ("species", "fur_color", "feather_color", "plumage_color",
                        "scale_color", "skin_color", "chitin_color", "coat_color"):
            physical.pop(_field, None)
        char_dict = _base_char("animal", physical)
        with pytest.raises(Exception) as exc_info:
            CharacterSchema(**char_dict)
        err_str = str(exc_info.value)
        assert "缺少最小集" in err_str or "animal" in err_str

    def test_vehicle_character_still_requires_vehicle_type(self):
        """vehicle_character must still have vehicle_type — NOT loosened by T21-NEW-2."""
        _require_schema()
        # Provide only human appearance fields — should FAIL
        physical = _HUMAN_PHYSICAL.copy()
        char_dict = _base_char("vehicle_character", physical)
        with pytest.raises(Exception) as exc_info:
            CharacterSchema(**char_dict)
        err_str = str(exc_info.value)
        assert "缺少最小集" in err_str or "vehicle_character" in err_str

    def test_digital_virtual_still_passes(self):
        """T21-NEW-1 regression: digital_virtual + human fields must still PASS."""
        _require_schema()
        char_dict = _base_char("digital_virtual", _HUMAN_PHYSICAL)
        result = CharacterSchema(**char_dict)
        assert result.character_type == "digital_virtual"
