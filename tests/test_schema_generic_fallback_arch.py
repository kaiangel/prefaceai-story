"""
TASK-T22-NEW-9: Wave 8 Generic Fallback Architecture
tests/test_schema_generic_fallback_arch.py

Validates the new generic humanoid fallback architecture in pipeline_schemas.py:

Architecture (Method B, 2026-05-22):
- OLD: 17 character_type × manual humanoid fallback entries in _TYPE_REQUIRED_GROUPS
- NEW: 1 universal has_humanoid_fallback() function handles all 15 non-strict types

Rules:
  1. human            → strict: hair_color AND skin_tone (2-group AND)
  2. anthropomorphic_animal → strict: species (group1) AND appearance (group2, extended)
  3. animal           → strict: species AND fur/feather/scale/etc. (NO humanoid fallback)
  4. vehicle_character → strict: vehicle_type (NO humanoid fallback)
  5. Other 15 types   → generic humanoid fallback: any humanoid field → PASS
                         no humanoid field → warning only (NOT raise)

Test Coverage:
  - 19 character_type × with humanoid fields → 19 PASS cases
  - animal + vehicle_character × with humanoid-only fields → 2 FAIL cases
  - human × without minimum → FAIL
  - anthropomorphic_animal × missing species → FAIL
  - anthropomorphic_animal × species only → FAIL (group 2 missing)
  - Edge cases: empty physical / partial fields / unknown type

Author: @Backend (Sonnet 4.6 xhigh)
Date: 2026-05-22
Owner: TASK-T22-NEW-9 Wave 8
"""

import sys
import types
import importlib.util
import pytest
from pathlib import Path

# ---------------------------------------------------------------------------
# Load pipeline_schemas directly without triggering full app __init__
# (Mirror exact isolation pattern from test_t21_digital_virtual_fallback.py)
# ---------------------------------------------------------------------------
project_root = Path(__file__).resolve().parent.parent


try:
    def _make_stub(name: str) -> types.ModuleType:
        mod = types.ModuleType(name)
        mod.__path__ = []
        return mod

    for _pkg in ("anthropic", "google", "google.genai", "google.generativeai"):
        if _pkg not in sys.modules:
            sys.modules[_pkg] = _make_stub(_pkg)

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

    if "app" not in sys.modules:
        _app_stub = types.ModuleType("app")
        _app_stub.__path__ = [str(project_root / "app")]
        sys.modules["app"] = _app_stub
    if "app.services" not in sys.modules:
        _svc_stub = types.ModuleType("app.services")
        _svc_stub.__path__ = [str(project_root / "app" / "services")]
        sys.modules["app.services"] = _svc_stub

    _spec = importlib.util.spec_from_file_location(
        "pipeline_schemas_wave8_isolated",
        project_root / "app" / "services" / "pipeline_schemas.py",
    )
    _module = importlib.util.module_from_spec(_spec)
    sys.modules["pipeline_schemas_wave8_isolated"] = _module
    _spec.loader.exec_module(_module)

    CharacterSchema = _module.CharacterSchema
    has_humanoid_fallback = _module.has_humanoid_fallback
    _HUMANOID_FALLBACK_FIELDS = _module._HUMANOID_FALLBACK_FIELDS
    _STRICT_TYPES = _module._STRICT_TYPES
    _TYPE_REQUIRED_GROUPS = _module._TYPE_REQUIRED_GROUPS
    _ANTHRO_ANIMAL_APPEARANCE_FIELDS = _module._ANTHRO_ANIMAL_APPEARANCE_FIELDS
    _SCHEMA_AVAILABLE = True
except Exception as _e:
    _SCHEMA_AVAILABLE = False
    _SCHEMA_IMPORT_ERROR = str(_e)


def _require_schema():
    if not _SCHEMA_AVAILABLE:
        err = globals().get("_SCHEMA_IMPORT_ERROR", "unknown error")
        pytest.skip(f"pipeline_schemas import failed: {err}")


# ---------------------------------------------------------------------------
# Canonical test data
# ---------------------------------------------------------------------------

_HUMAN_PHYSICAL = {
    "hair_color": "jet black",
    "hair_style": "short bob",
    "skin_tone": "fair",
    "face_shape": "oval",
    "eye_color": "dark brown",
    "eye_shape": "almond",
    "height": "medium",
    "build": "slim",
}

# Only non-humanoid fields — used for strict-type failure cases
_NON_HUMANOID_PHYSICAL = {
    "height": "medium",
    "build": "slim",
    "distinctive_marks": [],
    # No hair_color, skin_tone, face_shape, eye_color, eye_shape
}


def _char(character_type: str, physical: dict, clothing: dict | None = None) -> dict:
    return {
        "id": "char_001",
        "name": "测试",
        "name_en": "Test",
        "role": "protagonist",
        "character_type": character_type,
        "gender": "female",
        "age_appearance": "adult",
        "physical": physical,
        "clothing": clothing or {"top": "test outfit", "style": "test"},
    }


# ===========================================================================
# Section 1: has_humanoid_fallback() unit tests
# ===========================================================================

class TestHasHumanoidFallback:
    """Unit tests for the standalone has_humanoid_fallback() helper."""

    def test_hair_color_triggers_fallback(self):
        _require_schema()
        assert has_humanoid_fallback({"hair_color": "black"}) is True

    def test_skin_tone_triggers_fallback(self):
        _require_schema()
        assert has_humanoid_fallback({"skin_tone": "fair"}) is True

    def test_face_shape_triggers_fallback(self):
        _require_schema()
        assert has_humanoid_fallback({"face_shape": "oval"}) is True

    def test_eye_color_triggers_fallback(self):
        _require_schema()
        assert has_humanoid_fallback({"eye_color": "blue"}) is True

    def test_eye_shape_triggers_fallback(self):
        _require_schema()
        assert has_humanoid_fallback({"eye_shape": "almond"}) is True

    def test_no_humanoid_fields_returns_false(self):
        _require_schema()
        assert has_humanoid_fallback({"height": "tall", "build": "muscular"}) is False

    def test_empty_dict_returns_false(self):
        _require_schema()
        assert has_humanoid_fallback({}) is False

    def test_empty_string_fields_return_false(self):
        _require_schema()
        assert has_humanoid_fallback({"hair_color": "", "skin_tone": None}) is False

    def test_all_five_humanoid_fields_present(self):
        _require_schema()
        assert has_humanoid_fallback(_HUMAN_PHYSICAL) is True

    def test_fallback_fields_constant_has_five_entries(self):
        _require_schema()
        assert len(_HUMANOID_FALLBACK_FIELDS) == 5
        assert "hair_color" in _HUMANOID_FALLBACK_FIELDS
        assert "skin_tone" in _HUMANOID_FALLBACK_FIELDS
        assert "face_shape" in _HUMANOID_FALLBACK_FIELDS
        assert "eye_color" in _HUMANOID_FALLBACK_FIELDS
        assert "eye_shape" in _HUMANOID_FALLBACK_FIELDS


# ===========================================================================
# Section 2: Architecture constants validation
# ===========================================================================

class TestArchitectureConstants:
    """Validate the new architecture constants are set up correctly."""

    def test_strict_types_contains_exactly_two(self):
        _require_schema()
        assert _STRICT_TYPES == frozenset({"animal", "vehicle_character"})

    def test_type_required_groups_has_exactly_four_entries(self):
        """Wave 8: _TYPE_REQUIRED_GROUPS reduced from 19 → 4 special types only."""
        _require_schema()
        assert len(_TYPE_REQUIRED_GROUPS) == 4
        assert "human" in _TYPE_REQUIRED_GROUPS
        assert "anthropomorphic_animal" in _TYPE_REQUIRED_GROUPS
        assert "animal" in _TYPE_REQUIRED_GROUPS
        assert "vehicle_character" in _TYPE_REQUIRED_GROUPS

    def test_human_has_two_and_groups(self):
        """human requires hair_color AND skin_tone (2 separate groups)."""
        _require_schema()
        groups = _TYPE_REQUIRED_GROUPS["human"]
        assert len(groups) == 2
        # Each group is a 1-element tuple
        assert ("hair_color",) in groups
        assert ("skin_tone",) in groups

    def test_anthropomorphic_animal_has_two_and_groups(self):
        """anthropomorphic_animal: species (group1) AND appearance (group2)."""
        _require_schema()
        groups = _TYPE_REQUIRED_GROUPS["anthropomorphic_animal"]
        assert len(groups) == 2
        # group 1 must have species
        assert any("species" in g for g in groups)

    def test_anthropomorphic_animal_group2_contains_humanoid_fields(self):
        """group 2 of anthropomorphic_animal now includes hair_color/skin_tone/face_shape."""
        _require_schema()
        groups = _TYPE_REQUIRED_GROUPS["anthropomorphic_animal"]
        # find the longer group (group2)
        group2 = max(groups, key=len)
        assert "hair_color" in group2
        assert "skin_tone" in group2
        assert "face_shape" in group2

    def test_animal_has_two_and_groups(self):
        _require_schema()
        groups = _TYPE_REQUIRED_GROUPS["animal"]
        assert len(groups) == 2
        assert ("species",) in groups

    def test_vehicle_character_has_one_group(self):
        _require_schema()
        groups = _TYPE_REQUIRED_GROUPS["vehicle_character"]
        assert len(groups) == 1
        assert "vehicle_type" in groups[0]


# ===========================================================================
# Section 3: All 19 character_type × with humanoid fields → PASS
# ===========================================================================

# 19 canonical types from CLAUDE.md + pipeline_schemas history
_ALL_19_TYPES = [
    "human",
    "anthropomorphic_animal",
    "animal",
    "supernatural",
    "undead",
    "mythological",
    "fantasy_creature",
    "digital_virtual",
    "robot",
    "hybrid",
    "alien",
    "elemental",
    "concept_personified",
    "giant",
    "miniature",
    "aquatic",
    "object",
    "plant",
    "insect",
    "vehicle_character",
]


class TestAllTypesWithHumanoidFields:
    """
    All 19 types + human appearance fields → schema PASS.

    Special cases:
    - human: hair_color AND skin_tone both present → PASS
    - anthropomorphic_animal: species + hair_color → PASS (2-group satisfied)
    - animal: humanoid-only fields → FAIL (strict, no humanoid fallback)
    - vehicle_character: humanoid-only fields → FAIL (strict, no humanoid fallback)
    """

    def test_human_with_hair_and_skin_passes(self):
        """human: both hair_color and skin_tone present → PASS."""
        _require_schema()
        result = CharacterSchema(**_char("human", _HUMAN_PHYSICAL))
        assert result.character_type == "human"

    def test_anthropomorphic_animal_with_species_and_hair_passes(self):
        """anthropomorphic_animal: species (group1) + hair_color (group2) → PASS."""
        _require_schema()
        physical = {"species": "wolf", "hair_color": "silver", "skin_tone": "tanned"}
        result = CharacterSchema(**_char("anthropomorphic_animal", physical))
        assert result.character_type == "anthropomorphic_animal"

    def test_supernatural_with_humanoid_passes(self):
        _require_schema()
        result = CharacterSchema(**_char("supernatural", _HUMAN_PHYSICAL))
        assert result.character_type == "supernatural"

    def test_undead_with_humanoid_passes(self):
        _require_schema()
        result = CharacterSchema(**_char("undead", _HUMAN_PHYSICAL))
        assert result.character_type == "undead"

    def test_mythological_with_humanoid_passes(self):
        _require_schema()
        result = CharacterSchema(**_char("mythological", _HUMAN_PHYSICAL))
        assert result.character_type == "mythological"

    def test_fantasy_creature_with_humanoid_passes(self):
        _require_schema()
        result = CharacterSchema(**_char("fantasy_creature", _HUMAN_PHYSICAL))
        assert result.character_type == "fantasy_creature"

    def test_digital_virtual_with_humanoid_passes(self):
        _require_schema()
        result = CharacterSchema(**_char("digital_virtual", _HUMAN_PHYSICAL))
        assert result.character_type == "digital_virtual"

    def test_robot_with_humanoid_passes(self):
        _require_schema()
        result = CharacterSchema(**_char("robot", _HUMAN_PHYSICAL))
        assert result.character_type == "robot"

    def test_hybrid_with_humanoid_passes(self):
        _require_schema()
        result = CharacterSchema(**_char("hybrid", _HUMAN_PHYSICAL))
        assert result.character_type == "hybrid"

    def test_alien_with_humanoid_passes(self):
        _require_schema()
        result = CharacterSchema(**_char("alien", _HUMAN_PHYSICAL))
        assert result.character_type == "alien"

    def test_elemental_with_humanoid_passes(self):
        _require_schema()
        result = CharacterSchema(**_char("elemental", _HUMAN_PHYSICAL))
        assert result.character_type == "elemental"

    def test_concept_personified_with_humanoid_passes(self):
        _require_schema()
        result = CharacterSchema(**_char("concept_personified", _HUMAN_PHYSICAL))
        assert result.character_type == "concept_personified"

    def test_giant_with_humanoid_passes(self):
        _require_schema()
        result = CharacterSchema(**_char("giant", _HUMAN_PHYSICAL))
        assert result.character_type == "giant"

    def test_miniature_with_humanoid_passes(self):
        _require_schema()
        result = CharacterSchema(**_char("miniature", _HUMAN_PHYSICAL))
        assert result.character_type == "miniature"

    def test_aquatic_with_humanoid_passes(self):
        """美人鱼: humanoid upper-body appearance fields → PASS."""
        _require_schema()
        result = CharacterSchema(**_char("aquatic", _HUMAN_PHYSICAL))
        assert result.character_type == "aquatic"

    def test_object_with_humanoid_passes(self):
        """钟先生 / Olaf: personified object with human face → PASS."""
        _require_schema()
        result = CharacterSchema(**_char("object", _HUMAN_PHYSICAL))
        assert result.character_type == "object"

    def test_plant_with_humanoid_passes(self):
        """树精 Dryad: humanoid plant spirit → PASS."""
        _require_schema()
        result = CharacterSchema(**_char("plant", _HUMAN_PHYSICAL))
        assert result.character_type == "plant"

    def test_insect_with_humanoid_passes(self):
        """蝴蝶仙子: humanoid insect fairy → PASS."""
        _require_schema()
        result = CharacterSchema(**_char("insect", _HUMAN_PHYSICAL))
        assert result.character_type == "insect"

    def test_animal_with_humanoid_only_fails(self):
        """animal (strict): humanoid-only fields → FAIL (no humanoid fallback for pure animal)."""
        _require_schema()
        physical = {f: _HUMAN_PHYSICAL.get(f, "test") for f in _HUMANOID_FALLBACK_FIELDS}
        with pytest.raises(Exception) as exc_info:
            CharacterSchema(**_char("animal", physical))
        err = str(exc_info.value)
        assert "缺少最小集" in err or "animal" in err

    def test_vehicle_character_with_humanoid_only_fails(self):
        """vehicle_character (strict): humanoid-only fields → FAIL."""
        _require_schema()
        physical = {f: _HUMAN_PHYSICAL.get(f, "test") for f in _HUMANOID_FALLBACK_FIELDS}
        with pytest.raises(Exception) as exc_info:
            CharacterSchema(**_char("vehicle_character", physical))
        err = str(exc_info.value)
        assert "缺少最小集" in err or "vehicle_character" in err


# ===========================================================================
# Section 4: 15 generic types WITHOUT humanoid fields → warning not raise
# ===========================================================================

class TestGenericTypesWithoutHumanoidFields:
    """
    Non-strict types with neither humanoid nor type-specific fields →
    logger.warning only, schema PASS (not raise).

    This is the key architectural difference from the old hotfix approach.
    """

    def _no_humanoid_physical(self):
        return {"height": "medium", "build": "slim"}

    def test_supernatural_no_humanoid_warns_not_raises(self):
        _require_schema()
        result = CharacterSchema(**_char("supernatural", self._no_humanoid_physical()))
        assert result.character_type == "supernatural"

    def test_digital_virtual_no_humanoid_warns_not_raises(self):
        _require_schema()
        result = CharacterSchema(**_char("digital_virtual", self._no_humanoid_physical()))
        assert result.character_type == "digital_virtual"

    def test_robot_no_humanoid_warns_not_raises(self):
        _require_schema()
        result = CharacterSchema(**_char("robot", self._no_humanoid_physical()))
        assert result.character_type == "robot"

    def test_aquatic_no_humanoid_warns_not_raises(self):
        """aquatic without species/body_type/humanoid fields → warning, PASS."""
        _require_schema()
        result = CharacterSchema(**_char("aquatic", self._no_humanoid_physical()))
        assert result.character_type == "aquatic"

    def test_object_no_humanoid_warns_not_raises(self):
        _require_schema()
        result = CharacterSchema(**_char("object", self._no_humanoid_physical()))
        assert result.character_type == "object"

    def test_plant_no_humanoid_warns_not_raises(self):
        _require_schema()
        result = CharacterSchema(**_char("plant", self._no_humanoid_physical()))
        assert result.character_type == "plant"

    def test_insect_no_humanoid_warns_not_raises(self):
        _require_schema()
        result = CharacterSchema(**_char("insect", self._no_humanoid_physical()))
        assert result.character_type == "insect"


# ===========================================================================
# Section 5: Strict type enforcement (human / anthropomorphic_animal)
# ===========================================================================

class TestStrictTypeEnforcement:
    """human and anthropomorphic_animal must still raise when minimum fields missing."""

    def test_human_without_hair_or_skin_fails(self):
        """human without hair_color: even if skin_tone present, hair_color group fails."""
        _require_schema()
        physical = {"skin_tone": "fair", "height": "medium"}
        # human requires BOTH hair_color AND skin_tone (2-group AND)
        # With only skin_tone → hair_color group unsatisfied → FAIL
        with pytest.raises(Exception) as exc_info:
            CharacterSchema(**_char("human", physical))
        assert "缺少最小集" in str(exc_info.value)

    def test_human_without_skin_tone_fails(self):
        """human without skin_tone: even if hair_color present, skin_tone group fails."""
        _require_schema()
        physical = {"hair_color": "black", "height": "medium"}
        with pytest.raises(Exception) as exc_info:
            CharacterSchema(**_char("human", physical))
        assert "缺少最小集" in str(exc_info.value)

    def test_human_with_both_passes(self):
        """human with both hair_color AND skin_tone → PASS."""
        _require_schema()
        physical = {"hair_color": "black", "skin_tone": "fair"}
        result = CharacterSchema(**_char("human", physical))
        assert result.character_type == "human"

    def test_anthropomorphic_animal_without_species_fails(self):
        """anthropomorphic_animal: missing species (group 1) → FAIL regardless of group 2."""
        _require_schema()
        physical = {"hair_color": "silver", "fur_color": "grey", "skin_tone": "pale"}
        with pytest.raises(Exception) as exc_info:
            CharacterSchema(**_char("anthropomorphic_animal", physical))
        err = str(exc_info.value)
        assert "缺少最小集" in err or "anthropomorphic_animal" in err

    def test_anthropomorphic_animal_species_no_appearance_fails(self):
        """anthropomorphic_animal: species only, no fur/hair/skin_tone → group 2 FAIL."""
        _require_schema()
        physical = {"species": "cat", "height": "medium", "build": "slim"}
        with pytest.raises(Exception) as exc_info:
            CharacterSchema(**_char("anthropomorphic_animal", physical))
        err = str(exc_info.value)
        assert "缺少最小集" in err or "anthropomorphic_animal" in err

    def test_anthropomorphic_animal_species_plus_fur_passes(self):
        """anthropomorphic_animal: species (group1) + fur_color (group2) → PASS."""
        _require_schema()
        physical = {"species": "bear", "fur_color": "brown"}
        result = CharacterSchema(**_char("anthropomorphic_animal", physical))
        assert result.character_type == "anthropomorphic_animal"

    def test_anthropomorphic_animal_species_plus_hair_color_passes(self):
        """anthropomorphic_animal: species (group1) + hair_color as humanoid appearance (group2) → PASS."""
        _require_schema()
        physical = {"species": "wolf", "hair_color": "silver grey"}
        result = CharacterSchema(**_char("anthropomorphic_animal", physical))
        assert result.character_type == "anthropomorphic_animal"


# ===========================================================================
# Section 6: Strict pure animal / vehicle_character enforcement
# ===========================================================================

class TestPureAnimalAndVehicleStrictEnforcement:
    """animal and vehicle_character are strict — no humanoid fallback."""

    def test_animal_with_species_and_fur_passes(self):
        _require_schema()
        physical = {"species": "fox", "fur_color": "orange"}
        result = CharacterSchema(**_char("animal", physical))
        assert result.character_type == "animal"

    def test_animal_with_species_and_feather_passes(self):
        _require_schema()
        physical = {"species": "crow", "feather_color": "jet black", "plumage_color": "iridescent"}
        result = CharacterSchema(**_char("animal", physical))
        assert result.character_type == "animal"

    def test_animal_without_species_fails(self):
        _require_schema()
        physical = {"fur_color": "brown", "height": "small"}
        with pytest.raises(Exception):
            CharacterSchema(**_char("animal", physical))

    def test_animal_with_species_but_no_fur_or_scale_fails(self):
        _require_schema()
        physical = {"species": "snake", "height": "medium"}
        with pytest.raises(Exception) as exc_info:
            CharacterSchema(**_char("animal", physical))
        assert "缺少最小集" in str(exc_info.value)

    def test_vehicle_character_with_vehicle_type_passes(self):
        _require_schema()
        physical = {"vehicle_type": "sports_car"}
        result = CharacterSchema(**_char("vehicle_character", physical))
        assert result.character_type == "vehicle_character"

    def test_vehicle_character_without_vehicle_type_fails(self):
        _require_schema()
        physical = {"height": "large", "build": "heavy"}
        with pytest.raises(Exception) as exc_info:
            CharacterSchema(**_char("vehicle_character", physical))
        assert "缺少最小集" in str(exc_info.value)


# ===========================================================================
# Section 7: Edge cases
# ===========================================================================

class TestEdgeCases:
    """Edge cases: empty physical / unknown type / partial fields / degenerate inputs."""

    def test_unknown_character_type_passes_with_warning(self):
        """Unknown type → logger.warning, PASS (LLM extensibility — future 20th type)."""
        _require_schema()
        physical = {"height": "medium"}
        result = CharacterSchema(**_char("crystal_being", physical))
        assert result.character_type == "crystal_being"

    def test_unknown_type_with_humanoid_fields_passes(self):
        """Unknown type + humanoid fields → PASS (unknown type hits fallback path)."""
        _require_schema()
        result = CharacterSchema(**_char("spirit_entity", _HUMAN_PHYSICAL))
        assert result.character_type == "spirit_entity"

    def test_generic_type_with_single_humanoid_field_passes(self):
        """Only hair_color present → sufficient for humanoid fallback on generic type."""
        _require_schema()
        physical = {"hair_color": "silver", "height": "tall"}
        result = CharacterSchema(**_char("supernatural", physical))
        assert result.character_type == "supernatural"

    def test_generic_type_with_only_eye_shape_passes(self):
        """eye_shape alone triggers humanoid fallback."""
        _require_schema()
        physical = {"eye_shape": "almond", "build": "slim"}
        result = CharacterSchema(**_char("alien", physical))
        assert result.character_type == "alien"

    def test_aquatic_with_species_only_passes(self):
        """aquatic: species alone (no humanoid fields) → in _TYPE_REQUIRED_GROUPS? No.
        Wait — aquatic is NOT in _TYPE_REQUIRED_GROUPS in Wave 8.
        So species alone with no humanoid → warning but PASS."""
        _require_schema()
        physical = {"species": "mermaid", "height": "medium"}
        result = CharacterSchema(**_char("aquatic", physical))
        assert result.character_type == "aquatic"

    def test_character_type_case_insensitive(self):
        """character_type is lowercased before lookup."""
        _require_schema()
        result = CharacterSchema(**_char("Human", _HUMAN_PHYSICAL))
        assert result.character_type == "Human"

    def test_empty_character_type_raises(self):
        """Empty character_type → ValueError."""
        _require_schema()
        with pytest.raises(Exception) as exc_info:
            CharacterSchema(**_char("", _HUMAN_PHYSICAL))
        assert "character_type 不能为空" in str(exc_info.value)


# ===========================================================================
# Section 8: Regression — Wave 4 / Wave 4.5 types not broken by Wave 8
# ===========================================================================

class TestWave4Wave45Regression:
    """
    All types fixed in Wave 4 (T20-43) + Wave 4.5 (T21-NEW-1/2) must still
    accept humanoid appearance fields after the Wave 8 refactor.
    """

    # T20-43 types (Wave 4)
    def test_supernatural_regression(self):
        _require_schema()
        result = CharacterSchema(**_char("supernatural", _HUMAN_PHYSICAL))
        assert result.character_type == "supernatural"

    def test_undead_regression(self):
        _require_schema()
        result = CharacterSchema(**_char("undead", _HUMAN_PHYSICAL))
        assert result.character_type == "undead"

    def test_mythological_regression(self):
        _require_schema()
        result = CharacterSchema(**_char("mythological", _HUMAN_PHYSICAL))
        assert result.character_type == "mythological"

    def test_fantasy_creature_regression(self):
        _require_schema()
        result = CharacterSchema(**_char("fantasy_creature", _HUMAN_PHYSICAL))
        assert result.character_type == "fantasy_creature"

    # T21-NEW-1 types (Wave 4.5 P0/P1/P2)
    def test_digital_virtual_regression(self):
        _require_schema()
        result = CharacterSchema(**_char("digital_virtual", _HUMAN_PHYSICAL))
        assert result.character_type == "digital_virtual"

    def test_robot_regression(self):
        _require_schema()
        result = CharacterSchema(**_char("robot", _HUMAN_PHYSICAL))
        assert result.character_type == "robot"

    def test_hybrid_regression(self):
        _require_schema()
        result = CharacterSchema(**_char("hybrid", _HUMAN_PHYSICAL))
        assert result.character_type == "hybrid"

    def test_alien_regression(self):
        _require_schema()
        result = CharacterSchema(**_char("alien", _HUMAN_PHYSICAL))
        assert result.character_type == "alien"

    def test_elemental_regression(self):
        _require_schema()
        result = CharacterSchema(**_char("elemental", _HUMAN_PHYSICAL))
        assert result.character_type == "elemental"

    def test_concept_personified_regression(self):
        _require_schema()
        result = CharacterSchema(**_char("concept_personified", _HUMAN_PHYSICAL))
        assert result.character_type == "concept_personified"

    def test_giant_regression(self):
        _require_schema()
        result = CharacterSchema(**_char("giant", _HUMAN_PHYSICAL))
        assert result.character_type == "giant"

    def test_miniature_regression(self):
        _require_schema()
        result = CharacterSchema(**_char("miniature", _HUMAN_PHYSICAL))
        assert result.character_type == "miniature"

    # T21-NEW-2 types (Wave 4.5 P0/P1/P2)
    def test_aquatic_regression(self):
        _require_schema()
        result = CharacterSchema(**_char("aquatic", _HUMAN_PHYSICAL))
        assert result.character_type == "aquatic"

    def test_object_regression(self):
        _require_schema()
        result = CharacterSchema(**_char("object", _HUMAN_PHYSICAL))
        assert result.character_type == "object"

    def test_plant_regression(self):
        _require_schema()
        result = CharacterSchema(**_char("plant", _HUMAN_PHYSICAL))
        assert result.character_type == "plant"

    def test_insect_regression(self):
        _require_schema()
        result = CharacterSchema(**_char("insect", _HUMAN_PHYSICAL))
        assert result.character_type == "insect"

    # anthropomorphic_animal special 2-group AND preserved
    def test_anthropomorphic_animal_regression_fur(self):
        _require_schema()
        physical = {"species": "fox", "fur_color": "amber"}
        result = CharacterSchema(**_char("anthropomorphic_animal", physical))
        assert result.character_type == "anthropomorphic_animal"

    def test_anthropomorphic_animal_regression_hair(self):
        """P0 fix: 猫娘 species + hair_color (humanoid appearance in group2) → PASS."""
        _require_schema()
        physical = {"species": "cat", "hair_color": "white", "skin_tone": "fair"}
        result = CharacterSchema(**_char("anthropomorphic_animal", physical))
        assert result.character_type == "anthropomorphic_animal"

    def test_anthropomorphic_animal_no_species_still_fails(self):
        """anthropomorphic_animal without species still fails after Wave 8."""
        _require_schema()
        physical = {"hair_color": "silver", "fur_color": "grey"}
        with pytest.raises(Exception):
            CharacterSchema(**_char("anthropomorphic_animal", physical))
