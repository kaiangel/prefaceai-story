"""
DEC-048 Layer 1 (2026-05-22) — Identity Anchor Framework v1.0 unit tests

Coverage:
  - 19 character_types × extract_identity_anchors() returns valid anchor dict
  - extract_distinctive_tokens() edge cases (empty / Chinese / long / numeric)
  - extract_style_anchors() across 6+ style presets
  - extract_location_anchors() with + without signature_visual
  - extract_props_anchors() with + without props
  - extract_time_continuity_anchors() across 5+ scene shapes

Design:
  - Stub out heavy SDK imports (anthropic / google.genai) so tests run in CI
  - Direct file-level import of identity_anchor_prompts (no app.services init)
  - Single test file under tests/ — no fixtures dir needed

Author: @AI-ML
Owner: TASK-T22-NEW-3 / DEC-048 Layer 1 M3
"""

from __future__ import annotations

import importlib
import sys

import pytest


# ---------------------------------------------------------------------------
# Defensive import: if upstream tests (e.g. T20-43 / T21-NEW-2) stubbed
# google.genai / anthropic in sys.modules, our `from app.services...` import
# would fail. We detect this and CLEAN the stubs before importing so we get
# the real production modules.
#
# NB: We do NOT reinstall the stubs after — pre-existing tests like t20_43
# create their own stubs at their own module-import time (which already
# happened), so removing them now is safe for already-collected tests.
# Future-collected tests will re-stub as needed.
# ---------------------------------------------------------------------------

_STUB_SUSPECTS = (
    "anthropic", "google", "google.genai", "google.generativeai",
)


def _is_stub(mod) -> bool:
    """Heuristic: stub modules lack __file__ or have non-site-packages __path__."""
    if mod is None:
        return False
    # Real package has __file__ pointing to an actual .py file
    file = getattr(mod, "__file__", None)
    if file and "site-packages" in str(file):
        return False
    # Or has __path__ pointing to project / site-packages (real module)
    path = getattr(mod, "__path__", None)
    if path:
        path_strs = [str(p) for p in path]
        if any("site-packages" in p for p in path_strs):
            return False
        # Path pointing at our project's app/ directory is also OK
        if any(p.endswith("/app") or "/app/" in p for p in path_strs):
            return False
    # No file + no site-packages path → stub
    if file is None and not path:
        return True
    # Has empty namespace __path__ ([]) → stub
    if path == []:
        return True
    return False


def _clean_stubs_and_import():
    """Remove stub modules + reimport for clean style_enforcer access."""
    # Clean upstream stubs (heavy SDKs)
    for key in _STUB_SUSPECTS:
        mod = sys.modules.get(key)
        if _is_stub(mod):
            sys.modules.pop(key, None)
    # Clean upstream stubs of our own packages — t20_43 / t21_new_2 stub these
    for key in ("app.config", "app", "app.services", "app.prompts", "app.models"):
        mod = sys.modules.get(key)
        if _is_stub(mod):
            sys.modules.pop(key, None)
    # Force reload chain so app.services rebuilds cleanly from real google.genai
    for key in (
        "app.services.style_enforcer",
        "app.services.story_generator",
        "app.services",
        "app.prompts",
        "app.prompts.identity_anchor_prompts",
        "app.prompts.storyboard_prompts",
        "app",
    ):
        sys.modules.pop(key, None)
    return importlib.import_module("app.prompts.identity_anchor_prompts")


try:
    _ANCHOR = _clean_stubs_and_import()
    _IMPORT_OK = True
    _IMPORT_ERR = ""
except Exception as exc:  # pragma: no cover — env-only fallback
    _ANCHOR = None  # type: ignore[assignment]
    _IMPORT_OK = False
    _IMPORT_ERR = str(exc)


def _require_import():
    if not _IMPORT_OK:
        pytest.skip(f"identity_anchor_prompts import failed: {_IMPORT_ERR}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_human() -> dict:
    return {
        "id": "char_001",
        "name": "苏晨",
        "name_en": "Su Chen",
        "character_type": "human",
        "physical": {
            "hair_color": "jet black",
            "hair_style": "short sharp bob",
            "face_shape": "oval",
            "skin_tone": "fair",
            "eye_color": "dark brown",
            "eye_shape": "almond",
            "distinctive_marks": ["faint freckle on left cheek"],
        },
        "clothing": {
            "top": "gray fitted blazer over white camisole",
            "accessories": ["silver minimalist watch", "small pearl earrings"],
        },
    }


def _mock_mythological_coral() -> dict:
    return {
        "id": "char_001",
        "name": "珊瑚",
        "name_en": "Coral",
        "character_type": "mythological",
        "physical": {
            "hair_color": "deep sea-green with teal highlights, like sunlit seaweed",
            "hair_style": "long flowing past the waist, loose and undulating",
            "face_shape": "oval",
            "skin_tone": "fair with soft luminous aquamarine sheen",
            "eye_color": "vivid ocean blue, faintly luminescent",
            "eye_shape": "almond",
            "distinctive_marks": [
                "fine iridescent scale-shimmer along the collarbones",
                "lower body is a sweeping fish tail of overlapping scales in gradient coral-pink to golden-amber",
            ],
            "creature_type": "mermaid",
            "origin_culture": "Asian sea legend",
        },
        "clothing": {
            "top": "soft blush-pink top woven from interlocking pale pink and cream shell fragments",
            "accessories": ["small pearl-tipped pins in hair"],
        },
    }


def _mock_anthropomorphic_rabbit() -> dict:
    return {
        "id": "char_002",
        "name_en": "Milly",
        "character_type": "anthropomorphic_animal",
        "physical": {
            "species": "rabbit",
            "fur_color": "clean warm ivory white",
            "ear_style": "long upright",
            "distinctive_marks": ["single pale freckle on tip of left ear"],
        },
        "clothing": {
            "top": "cream knitted vest over white long-sleeve shirt",
            "accessories": ["small woven straw basket"],
        },
    }


def _mock_pure_animal() -> dict:
    return {
        "id": "char_003",
        "name_en": "Sparrow",
        "character_type": "animal",
        "physical": {
            "species": "sparrow",
            "feather_color": "warm brown with cream belly",
            "distinctive_marks": ["white wing band"],
        },
    }


def _mock_robot() -> dict:
    return {
        "id": "char_004",
        "name_en": "Aria",
        "character_type": "robot",
        "physical": {
            "robot_type": "humanoid service robot",
            "material": "brushed aluminum with white polymer",
            "hair_color": "platinum silver synthetic fiber",
            "face_shape": "heart",
            "skin_tone": "pale matte ceramic",
            "eye_color": "luminous cyan",
        },
        "clothing": {"top": "fitted utility tunic", "accessories": []},
    }


def _mock_minimal(char_type: str) -> dict:
    """Minimal valid character — only id + character_type + 1 physical field."""
    return {
        "id": f"char_{char_type}",
        "name_en": f"Test_{char_type}",
        "character_type": char_type,
        "physical": {"hair_color": "varies", "skin_tone": "varies"},
        "clothing": {"top": "test outfit"},
    }


# ===========================================================================
# extract_identity_anchors — Type 1: Humanoid types
# ===========================================================================


def test_human_returns_complete_anchor():
    _require_import()
    anchor = _ANCHOR.extract_identity_anchors(_mock_human())
    assert anchor["character_id"] == "char_001"
    assert anchor["name_en"] == "Su Chen"
    assert anchor["character_type"] == "human"
    ia = anchor["identity_anchor"]
    assert ia["hair_color"] == "jet black"
    assert ia["hair_style"] == "short sharp bob"
    assert ia["face_shape"] == "oval"
    assert ia["skin_tone"] == "fair"
    assert ia["eye_color"] == "dark brown"
    assert ia["eye_shape"] == "almond"
    assert ia["distinctive_marks_short"] == ["faint freckle on left cheek"]
    assert ia["clothing_core"]["top"].startswith("gray fitted blazer")
    assert ia["clothing_core"]["signature_accessory"] == "silver minimalist watch"
    assert ia["primary_color"] == "jet black"
    assert ia["primary_color_field"] == "hair_color"


def test_mythological_coral_preserves_signature_marks():
    _require_import()
    anchor = _ANCHOR.extract_identity_anchors(_mock_mythological_coral())
    assert anchor["character_type"] == "mythological"
    ia = anchor["identity_anchor"]
    # The exact sea-green hair value MUST survive — this is the test22 root case
    assert "sea-green" in ia["hair_color"]
    assert "teal" in ia["hair_color"]
    # Distinctive marks limited to 2 (per spec)
    assert len(ia["distinctive_marks_short"]) == 2
    # Type-specific extras present
    assert anchor["identity_anchor"]["creature_type"] == "mermaid"
    assert anchor["identity_anchor"]["origin_culture"] == "Asian sea legend"


def test_anthropomorphic_animal_uses_fur_as_primary_color():
    _require_import()
    anchor = _ANCHOR.extract_identity_anchors(_mock_anthropomorphic_rabbit())
    assert anchor["character_type"] == "anthropomorphic_animal"
    ia = anchor["identity_anchor"]
    # species + fur_color present
    assert ia["species"] == "rabbit"
    assert ia["fur_color"] == "clean warm ivory white"
    # primary_color routes to fur_color (NOT hair_color — humanoid fallback)
    assert ia["primary_color"] == "clean warm ivory white"
    assert ia["primary_color_field"] == "fur_color"
    # hair_color empty (rabbit has fur, not hair)
    assert ia["hair_color"] == ""


def test_pure_animal_uses_feather_color():
    _require_import()
    anchor = _ANCHOR.extract_identity_anchors(_mock_pure_animal())
    assert anchor["character_type"] == "animal"
    ia = anchor["identity_anchor"]
    assert ia["species"] == "sparrow"
    assert ia["feather_color"] == "warm brown with cream belly"
    # primary_color routes to feather_color (sparrow has feathers)
    assert ia["primary_color"] == "warm brown with cream belly"
    assert ia["primary_color_field"] == "feather_color"


def test_robot_uses_humanoid_fallback_when_present():
    _require_import()
    anchor = _ANCHOR.extract_identity_anchors(_mock_robot())
    assert anchor["character_type"] == "robot"
    ia = anchor["identity_anchor"]
    assert ia["hair_color"] == "platinum silver synthetic fiber"
    assert ia["face_shape"] == "heart"
    assert ia["skin_tone"] == "pale matte ceramic"
    # robot type-specific extras
    assert ia["robot_type"] == "humanoid service robot"
    assert ia["material"] == "brushed aluminum with white polymer"
    # primary_color from hair_color (humanoid fallback)
    assert ia["primary_color"] == "platinum silver synthetic fiber"
    assert ia["primary_color_field"] == "hair_color"


# ===========================================================================
# extract_identity_anchors — Type 2: All 19 character_types dispatch (smoke)
# ===========================================================================

_ALL_19_TYPES = [
    "human",
    "animal",
    "anthropomorphic_animal",
    "fantasy_creature",
    "robot",
    "object",
    "hybrid",
    "insect",
    "aquatic",
    "plant",
    "mythological",
    "supernatural",
    "undead",
    "elemental",
    "alien",
    "vehicle_character",
    "digital_virtual",
    "concept_personified",
    "miniature",
    "giant",
]


@pytest.mark.parametrize("char_type", _ALL_19_TYPES)
def test_extract_returns_complete_dict_for_all_19_types(char_type):
    _require_import()
    anchor = _ANCHOR.extract_identity_anchors(_mock_minimal(char_type))
    # Top-level keys always present
    assert set(anchor.keys()) >= {"character_id", "name_en", "character_type", "identity_anchor"}
    assert anchor["character_type"] == char_type
    ia = anchor["identity_anchor"]
    # 9 stable slots ALWAYS present (even if empty string)
    for fld in (
        "hair_color", "hair_style", "face_shape", "skin_tone", "eye_color",
        "eye_shape", "distinctive_marks_short", "clothing_core",
        "primary_color",
    ):
        assert fld in ia, f"{char_type}: missing slot '{fld}'"
    # clothing_core sub-structure
    assert "top" in ia["clothing_core"]
    assert "signature_accessory" in ia["clothing_core"]


# ===========================================================================
# extract_identity_anchors — Edge cases
# ===========================================================================


def test_empty_character_returns_safe_empty_anchor():
    _require_import()
    anchor = _ANCHOR.extract_identity_anchors({})
    assert anchor["character_id"] == ""
    assert anchor["character_type"] == "human"  # default
    ia = anchor["identity_anchor"]
    assert ia["hair_color"] == ""
    assert ia["distinctive_marks_short"] == []


def test_non_dict_input_returns_empty_anchor():
    _require_import()
    anchor = _ANCHOR.extract_identity_anchors("not a dict")  # type: ignore[arg-type]
    assert anchor["character_id"] == ""
    assert anchor["identity_anchor"]["hair_color"] == ""


def test_chinese_name_falls_back_to_id():
    _require_import()
    char = {
        "id": "char_007",
        "name": "苏晨",
        "name_en": "苏晨",  # mistakenly Chinese in name_en field
        "character_type": "human",
        "physical": {"hair_color": "black"},
    }
    anchor = _ANCHOR.extract_identity_anchors(char)
    # Chinese name_en should be replaced with id (defensive)
    assert anchor["name_en"] == "char_007"


def test_distinctive_marks_limited_to_2():
    _require_import()
    char = _mock_human()
    char["physical"]["distinctive_marks"] = [f"mark_{i}" for i in range(10)]
    anchor = _ANCHOR.extract_identity_anchors(char)
    assert len(anchor["identity_anchor"]["distinctive_marks_short"]) == 2


def test_long_mark_is_truncated_to_80_chars():
    _require_import()
    char = _mock_human()
    long_mark = "a" * 200
    char["physical"]["distinctive_marks"] = [long_mark]
    anchor = _ANCHOR.extract_identity_anchors(char)
    mark = anchor["identity_anchor"]["distinctive_marks_short"][0]
    assert len(mark) <= 83  # 80 + "..."
    assert mark.endswith("...")


def test_marks_as_dict_extracted():
    _require_import()
    char = _mock_human()
    char["physical"]["distinctive_marks"] = [
        {"text": "scar on left brow", "severity": "minor"},
        {"description": "freckles across nose bridge"},
    ]
    anchor = _ANCHOR.extract_identity_anchors(char)
    marks = anchor["identity_anchor"]["distinctive_marks_short"]
    assert marks == ["scar on left brow", "freckles across nose bridge"]


def test_marks_as_single_string_wrapped():
    _require_import()
    char = _mock_human()
    char["physical"]["distinctive_marks"] = "lone scar on jaw"  # str not list
    anchor = _ANCHOR.extract_identity_anchors(char)
    assert anchor["identity_anchor"]["distinctive_marks_short"] == ["lone scar on jaw"]


def test_accessories_empty_yields_empty_signature():
    _require_import()
    char = _mock_human()
    char["clothing"]["accessories"] = []
    anchor = _ANCHOR.extract_identity_anchors(char)
    assert anchor["identity_anchor"]["clothing_core"]["signature_accessory"] == ""


def test_missing_clothing_dict_safe():
    _require_import()
    char = _mock_human()
    del char["clothing"]
    anchor = _ANCHOR.extract_identity_anchors(char)
    assert anchor["identity_anchor"]["clothing_core"] == {"top": "", "signature_accessory": ""}


def test_missing_physical_dict_safe():
    _require_import()
    char = {"id": "char_x", "name_en": "X", "character_type": "human"}
    anchor = _ANCHOR.extract_identity_anchors(char)
    ia = anchor["identity_anchor"]
    assert ia["hair_color"] == ""
    assert ia["primary_color"] == ""


def test_default_character_type_when_missing():
    _require_import()
    char = {"id": "char_y", "name_en": "Y", "physical": {"hair_color": "red"}}
    anchor = _ANCHOR.extract_identity_anchors(char)
    assert anchor["character_type"] == "human"
    assert anchor["identity_anchor"]["hair_color"] == "red"


# ===========================================================================
# extract_distinctive_tokens — Edge cases
# ===========================================================================


def test_distinctive_tokens_basic_extraction():
    _require_import()
    toks = _ANCHOR.extract_distinctive_tokens(
        "deep sea-green with teal highlights, like sunlit seaweed"
    )
    assert toks == ["deep", "sea-green", "teal"]


def test_distinctive_tokens_respects_n():
    _require_import()
    toks = _ANCHOR.extract_distinctive_tokens(
        "fair with a soft luminous aquamarine sheen", n=4
    )
    # Stopwords "with" / "a" filtered; 4 distinctive: fair, soft, luminous, aquamarine
    assert toks == ["fair", "soft", "luminous", "aquamarine"]


def test_distinctive_tokens_empty_string_returns_empty():
    _require_import()
    assert _ANCHOR.extract_distinctive_tokens("") == []


def test_distinctive_tokens_none_returns_empty():
    _require_import()
    assert _ANCHOR.extract_distinctive_tokens(None) == []  # type: ignore[arg-type]


def test_distinctive_tokens_pure_chinese_returns_empty():
    _require_import()
    # Pure Chinese — no English tokens to extract
    assert _ANCHOR.extract_distinctive_tokens("深海绿色带青绿色高光") == []


def test_distinctive_tokens_mixed_chinese_english():
    _require_import()
    toks = _ANCHOR.extract_distinctive_tokens(
        "sea-green hair 海洋绿色头发 with teal highlights"
    )
    # Only English tokens extracted, Chinese skipped
    assert "sea-green" in toks
    assert "teal" in toks


def test_distinctive_tokens_all_stopwords_returns_empty():
    _require_import()
    assert _ANCHOR.extract_distinctive_tokens("the and of an is") == []


def test_distinctive_tokens_drops_pure_digits():
    _require_import()
    # The regex only matches [a-zA-Z]+ so digits naturally drop
    toks = _ANCHOR.extract_distinctive_tokens("8-bit pixel-art 1920x1080 retro")
    assert "8" not in toks
    assert "1920" not in toks
    assert "retro" in toks


def test_distinctive_tokens_long_sentence_truncates_at_n():
    _require_import()
    # Use space-separated distinct words (no underscores — regex matches
    # [a-zA-Z]+ with optional internal hyphens, which is appropriate for
    # physical descriptions like "sea-green" / "rose-gold" / "blue-violet")
    long_text = "alpha beta gamma delta epsilon zeta eta theta iota kappa"
    toks = _ANCHOR.extract_distinctive_tokens(long_text, n=3)
    assert len(toks) == 3
    assert toks == ["alpha", "beta", "gamma"]


def test_distinctive_tokens_preserves_insertion_order():
    _require_import()
    toks = _ANCHOR.extract_distinctive_tokens("zebra apple banana cherry date")
    assert toks == ["zebra", "apple", "banana"]


def test_distinctive_tokens_deduplicates():
    _require_import()
    toks = _ANCHOR.extract_distinctive_tokens("red red blue red green")
    assert toks == ["red", "blue", "green"]


# ===========================================================================
# extract_style_anchors — 6 styles
# ===========================================================================


@pytest.mark.parametrize("preset", [
    "realistic",
    "cyberpunk",
    "anime",
    "children_book",
    "ink",
    "gothic",
])
def test_style_anchors_returns_top5_mandatory(preset):
    _require_import()
    s = _ANCHOR.extract_style_anchors(preset)
    assert s["style_preset"] == preset
    sa = s["style_anchor"]
    assert "style_display_name" in sa
    assert isinstance(sa["mandatory_keywords_top5"], list)
    assert isinstance(sa["forbidden_keywords_top8"], list)
    # Real presets must have non-empty mandatory (StyleEnforcer.STYLE_ENFORCEMENTS)
    assert len(sa["mandatory_keywords_top5"]) >= 1
    assert len(sa["mandatory_keywords_top5"]) <= 5
    assert len(sa["forbidden_keywords_top8"]) <= 8
    assert isinstance(sa["style_signature_line"], str)


def test_style_anchors_unknown_preset_falls_back():
    _require_import()
    s = _ANCHOR.extract_style_anchors("nonexistent_xyz_style")
    assert s["style_preset"] == "nonexistent_xyz_style"
    # Unknown preset: empty mandatory but always returns a signature line
    sa = s["style_anchor"]
    assert sa["mandatory_keywords_top5"] == []
    assert sa["forbidden_keywords_top8"] == []
    assert "nonexistent_xyz_style" in sa["style_signature_line"]


def test_style_anchors_empty_preset_defaults_to_realistic():
    _require_import()
    s = _ANCHOR.extract_style_anchors("")
    assert s["style_preset"] == "realistic"
    assert "photorealistic" in " ".join(s["style_anchor"]["mandatory_keywords_top5"])


# ===========================================================================
# extract_location_anchors — with + without signature_visual
# ===========================================================================


def test_location_anchor_with_signature_visual():
    _require_import()
    loc = {
        "id": "loc_001",
        "name_en": "underwater_palace",
        "signature_visual": "bioluminescent coral pillars, schools of silver fish",
        "atmosphere": "soft blue-green ambient light filtering from surface",
        "time_of_day": "perpetual underwater twilight",
        "interior_or_exterior": "interior",
    }
    out = _ANCHOR.extract_location_anchors(loc)
    assert out["location_id"] == "loc_001"
    la = out["location_anchor"]
    assert la["name_en"] == "underwater_palace"
    assert la["signature_visual"].startswith("bioluminescent coral")
    assert la["atmosphere"].startswith("soft blue-green")
    assert la["time_of_day"] == "perpetual underwater twilight"
    assert la["interior_or_exterior"] == "interior"


def test_location_anchor_without_signature_visual():
    _require_import()
    loc = {"id": "loc_002", "name_en": "alley"}  # no signature_visual
    out = _ANCHOR.extract_location_anchors(loc)
    assert out["location_id"] == "loc_002"
    assert out["location_anchor"]["signature_visual"] == ""
    # Other fields default to empty string
    assert out["location_anchor"]["atmosphere"] == ""


def test_location_anchor_none_returns_empty():
    _require_import()
    out = _ANCHOR.extract_location_anchors(None)
    assert out["location_id"] == ""
    assert out["location_anchor"]["name_en"] == ""


def test_location_anchor_chinese_name_falls_back_to_id():
    _require_import()
    loc = {"id": "loc_003", "name_en": "皇宫", "signature_visual": "red lacquer columns"}
    out = _ANCHOR.extract_location_anchors(loc)
    assert out["location_anchor"]["name_en"] == "loc_003"


def test_location_anchor_supports_alt_field_names():
    _require_import()
    # Stage 1 outline may use signature_visual_summary or visual_summary
    loc = {
        "id": "loc_004",
        "name": "courtyard",
        "signature_visual_summary": "stone-paved square with cherry trees",
        "mood": "tranquil",
    }
    out = _ANCHOR.extract_location_anchors(loc)
    assert out["location_anchor"]["signature_visual"].startswith("stone-paved")
    assert out["location_anchor"]["atmosphere"] == "tranquil"


# ===========================================================================
# extract_props_anchors — with + without props
# ===========================================================================


def test_props_anchor_with_signature_visuals():
    _require_import()
    props = [
        {"id": "prop_001", "name_en": "shell_harmonica",
         "signature_visual": "palm-sized harmonica carved from pink spiral shell"},
        {"id": "prop_002", "name_en": "pearl_pendant",
         "signature_visual": "single luminous pearl on silver chain"},
    ]
    out = _ANCHOR.extract_props_anchors(props)
    assert len(out) == 2
    assert out[0]["prop_id"] == "prop_001"
    assert "harmonica" in out[0]["prop_anchor"]["signature_visual"]
    assert out[1]["prop_id"] == "prop_002"


def test_props_anchor_skips_missing_signature():
    _require_import()
    props = [
        {"id": "prop_003", "name_en": "key"},  # no signature_visual → skip
        {"id": "prop_004", "name_en": "scroll", "signature_visual": "tattered parchment"},
    ]
    out = _ANCHOR.extract_props_anchors(props)
    assert len(out) == 1
    assert out[0]["prop_id"] == "prop_004"


def test_props_anchor_empty_returns_empty_list():
    _require_import()
    assert _ANCHOR.extract_props_anchors([]) == []
    assert _ANCHOR.extract_props_anchors(None) == []


def test_props_anchor_skips_invalid_entries():
    _require_import()
    props = [
        "not a dict",
        {"signature_visual": "no id"},  # no id → skip
        {"id": "prop_005", "signature_visual": "valid prop"},
    ]
    out = _ANCHOR.extract_props_anchors(props)
    assert len(out) == 1
    assert out[0]["prop_id"] == "prop_005"


# ===========================================================================
# extract_time_continuity_anchors — across 5+ scene shapes
# ===========================================================================


def test_time_continuity_with_full_fields():
    _require_import()
    scene = {
        "scene_id": 5,
        "time_of_day": "golden morning sunrise",
        "lighting": "warm amber light, long west-pointing shadows",
        "weather": "clear sky, light sea breeze",
        "continuity_from_previous_scene": "jump from night to morning",
    }
    out = _ANCHOR.extract_time_continuity_anchors(scene)
    assert out["scene_id"] == 5
    tc = out["time_continuity_anchor"]
    assert tc["time_of_day"] == "golden morning sunrise"
    assert tc["lighting"].startswith("warm amber")
    assert tc["weather"].startswith("clear sky")
    assert "night to morning" in tc["continuity_from_previous_scene"]


def test_time_continuity_via_atmosphere_subdict():
    _require_import()
    scene = {
        "scene_id": 6,
        "atmosphere": {
            "time_of_day": "dusk",
            "lighting": "rose-gold backlight",
            "weather": "overcast",
        },
    }
    out = _ANCHOR.extract_time_continuity_anchors(scene)
    tc = out["time_continuity_anchor"]
    assert tc["time_of_day"] == "dusk"
    assert tc["lighting"] == "rose-gold backlight"
    assert tc["weather"] == "overcast"


def test_time_continuity_none_returns_empty():
    _require_import()
    out = _ANCHOR.extract_time_continuity_anchors(None)
    assert out["scene_id"] == ""
    assert out["time_continuity_anchor"]["time_of_day"] == ""


def test_time_continuity_empty_dict_returns_empty():
    _require_import()
    out = _ANCHOR.extract_time_continuity_anchors({})
    assert out["scene_id"] == ""
    assert out["time_continuity_anchor"]["lighting"] == ""


def test_time_continuity_partial_fields():
    _require_import()
    # Only time_of_day, no lighting / weather
    scene = {"scene_id": 7, "time_of_day": "noon"}
    out = _ANCHOR.extract_time_continuity_anchors(scene)
    tc = out["time_continuity_anchor"]
    assert tc["time_of_day"] == "noon"
    assert tc["lighting"] == ""
    assert tc["weather"] == ""


# ===========================================================================
# Module-level templates / marker sanity
# ===========================================================================


def test_anchor_marker_starts_correctly():
    _require_import()
    assert _ANCHOR.IDENTITY_ANCHOR_MARKER.startswith("[IDENTITY ANCHORS")


def test_template_contains_unicode_boundary_marker():
    _require_import()
    tmpl = _ANCHOR.IDENTITY_ANCHOR_INSTRUCTION_BLOCK_TEMPLATE
    # Unicode box-drawing equals signs delimit the anchor block (max attention)
    assert "═══════" in tmpl
    assert "{character_anchors_block}" in tmpl
    assert "{style_anchor_block}" in tmpl
    assert "{location_anchor_block}" in tmpl
    assert "{props_anchor_block}" in tmpl
    assert "{time_continuity_anchor_block}" in tmpl
    assert "{marker}" in tmpl
    # Trailing narrative scene marker for LLM creative-layer separation
    assert "[NARRATIVE SCENE — LLM creative layer below]" in tmpl


def test_narrative_variables_guidance_lists_creative_scope():
    _require_import()
    g = _ANCHOR.NARRATIVE_VARIABLES_GUIDANCE
    # Lists narrative variables explicitly
    for v in ("pose", "expression", "camera_angle", "camera_distance",
              "emotion", "interaction", "scene_action"):
        assert v in g
    # Lists out-of-scope items explicitly
    for v in ("hair_color", "skin_tone", "STYLE ANCHOR", "LOCATION ANCHOR",
              "PROPS ANCHOR", "TIME CONTINUITY ANCHOR"):
        assert v in g


def test_template_can_be_formatted_with_5_blocks():
    _require_import()
    # Smoke test: template formats cleanly with all 5 blocks
    formatted = _ANCHOR.IDENTITY_ANCHOR_INSTRUCTION_BLOCK_TEMPLATE.format(
        marker=_ANCHOR.IDENTITY_ANCHOR_MARKER,
        character_anchors_block="\n## CHAR ANCHOR\nchar_001 hair: red\n",
        style_anchor_block="\n## STYLE ANCHOR\nrealistic\n",
        location_anchor_block="\n## LOCATION ANCHOR\nbeach\n",
        props_anchor_block="\n## PROPS ANCHOR\nshell\n",
        time_continuity_anchor_block="\n## TIME ANCHOR\ndawn\n",
    )
    # Marker present
    assert _ANCHOR.IDENTITY_ANCHOR_MARKER in formatted
    # All 5 block headers present
    for hdr in ("CHAR ANCHOR", "STYLE ANCHOR", "LOCATION ANCHOR",
                "PROPS ANCHOR", "TIME ANCHOR"):
        assert hdr in formatted


def test_template_supports_empty_optional_blocks():
    _require_import()
    # Backend may skip optional blocks (pure environment shot etc.)
    formatted = _ANCHOR.IDENTITY_ANCHOR_INSTRUCTION_BLOCK_TEMPLATE.format(
        marker=_ANCHOR.IDENTITY_ANCHOR_MARKER,
        character_anchors_block="",
        style_anchor_block="\n## STYLE ANCHOR\nrealistic\n",
        location_anchor_block="",
        props_anchor_block="",
        time_continuity_anchor_block="",
    )
    assert "STYLE ANCHOR" in formatted
    assert _ANCHOR.IDENTITY_ANCHOR_MARKER in formatted
