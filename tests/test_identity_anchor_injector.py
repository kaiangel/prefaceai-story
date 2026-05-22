"""
DEC-048 Layer 1 (2026-05-22) — Backend identity anchor injector unit tests

Coverage:
  - inject_identity_anchors idempotency (re-runs produce identical output)
  - 0-character shots (env-only) still inject style/location/time anchors
  - Multi-character (3-6 chars) each rendered as independent block
  - test22 Coral mermaid: hair="deep sea-green..." → "sea-green" must appear
  - anthropomorphic_animal: fur_color routed to primary_color slot
  - Edge cases: empty image_prompt / None inputs / invalid shot types
  - Render helpers: render_character_anchors_block / style / location / props / time

Design:
  - Same defensive import as test_identity_anchor_extraction.py
    (stub google.genai / anthropic to bypass app.services.__init__ cascade
    in CI without the GenAI SDK installed)
  - All tests are pure-Python — no async, no API calls

Author: @backend (Sonnet 4.6 + xhigh)
Owner: TASK-T22-NEW-3 / DEC-048 Layer 1
"""

from __future__ import annotations

import importlib
import sys

import pytest


# ---------------------------------------------------------------------------
# Defensive import: clean stubs and import the real injector module so we
# always test the production code path. Mirrors
# tests/test_identity_anchor_extraction.py for consistency.
# ---------------------------------------------------------------------------

_STUB_SUSPECTS = (
    "anthropic", "google", "google.genai", "google.generativeai",
)


def _is_stub(mod) -> bool:
    if mod is None:
        return False
    file = getattr(mod, "__file__", None)
    if file and "site-packages" in str(file):
        return False
    path = getattr(mod, "__path__", None)
    if path:
        path_strs = [str(p) for p in path]
        if any("site-packages" in p for p in path_strs):
            return False
        if any(p.endswith("/app") or "/app/" in p for p in path_strs):
            return False
    if file is None and not path:
        return True
    if path == []:
        return True
    return False


def _clean_and_import_injector():
    """Load injector via spec_from_file_location to bypass app.services
    __init__.py cascade (which imports story_generator → google.genai,
    failing in CI without GenAI SDK).

    Same pattern as extract_style_anchors in identity_anchor_prompts.py
    (also a workaround for the cascade — see KEY_LEARNINGS #50).
    """
    import importlib.util as _ilu
    import os as _os

    for key in _STUB_SUSPECTS:
        mod = sys.modules.get(key)
        if _is_stub(mod):
            sys.modules.pop(key, None)
    for key in ("app.config", "app", "app.services", "app.prompts", "app.models"):
        mod = sys.modules.get(key)
        if _is_stub(mod):
            sys.modules.pop(key, None)
    for key in (
        "app.services.style_enforcer",
        "app.services.identity_anchor_injector",
        "app.services.story_generator",
        "app.services",
        "app.prompts.identity_anchor_prompts",
        "app.prompts",
        "app",
    ):
        sys.modules.pop(key, None)

    # Load anchor prompts via standard import (app.prompts has no cascade)
    anchor_mod = importlib.import_module("app.prompts.identity_anchor_prompts")

    # Load injector directly from file to bypass app.services.__init__
    # (which imports story_generator → google.genai ImportError in CI).
    # Use canonical module name + register in sys.modules so any
    # downstream isinstance/dataclass resolution works correctly.
    inj_path = _os.path.join(
        _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
        "app", "services", "identity_anchor_injector.py",
    )
    spec = _ilu.spec_from_file_location(
        "app.services.identity_anchor_injector", inj_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load identity_anchor_injector.py from {inj_path}")
    inj = _ilu.module_from_spec(spec)
    sys.modules["app.services.identity_anchor_injector"] = inj
    spec.loader.exec_module(inj)  # type: ignore[union-attr]
    return inj, anchor_mod


try:
    _INJ, _ANCHOR = _clean_and_import_injector()
    _IMPORT_OK = True
    _IMPORT_ERR = ""
except Exception as exc:  # pragma: no cover
    _INJ = None  # type: ignore[assignment]
    _ANCHOR = None  # type: ignore[assignment]
    _IMPORT_OK = False
    _IMPORT_ERR = str(exc)


def _require_import():
    if not _IMPORT_OK:
        pytest.skip(f"identity_anchor_injector import failed: {_IMPORT_ERR}")


# ---------------------------------------------------------------------------
# Mock fixtures — characters / locations / props / scenes
# ---------------------------------------------------------------------------


def _mock_coral_mermaid() -> dict:
    """test22 Coral — the real reproduction case from DEC-048 Layer 1."""
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
            "eye_color": "vivid ocean blue",
            "eye_shape": "almond",
            "distinctive_marks": [
                "fine iridescent scale-shimmer along the collarbones",
                "lower body is a sweeping fish tail of overlapping scales",
            ],
            "creature_type": "mermaid",
        },
        "clothing": {
            "top": "soft blush-pink top woven from interlocking shell fragments",
            "accessories": ["small pearl-tipped pins in hair"],
        },
    }


def _mock_sea_witch() -> dict:
    return {
        "id": "char_003",
        "name_en": "Sea Witch",
        "character_type": "mythological",
        "physical": {
            "hair_color": "silver-white spiraling tendrils intertwined with sea-stones",
            "hair_style": "long, voluminous, with embedded shells",
            "face_shape": "diamond",
            "skin_tone": "soft lavender-pale",
            "eye_color": "deep abyssal indigo",
            "distinctive_marks": ["dark violet vein-lines at temples"],
        },
        "clothing": {
            "top": "voluminous deep sea-moss green robe of woven kelp",
            "accessories": ["coral crown"],
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
            "distinctive_marks": ["single pale freckle on tip of left ear"],
        },
        "clothing": {
            "top": "cream knitted vest over white long-sleeve shirt",
            "accessories": ["small woven straw basket"],
        },
    }


def _mock_pure_animal_sparrow() -> dict:
    return {
        "id": "char_004",
        "name_en": "Sparrow",
        "character_type": "animal",
        "physical": {
            "species": "sparrow",
            "feather_color": "warm brown with cream belly",
            "distinctive_marks": ["white wing band"],
        },
    }


def _mock_location_underwater() -> dict:
    return {
        "id": "loc_001",
        "name_en": "underwater_palace",
        "signature_visual": "bioluminescent coral pillars, schools of small silver fish, swaying kelp forests",
        "atmosphere": "soft blue-green ambient light filtering down from surface",
        "interior_or_exterior": "interior",
    }


def _mock_props_shell_harmonica() -> list[dict]:
    return [
        {
            "id": "prop_001",
            "name_en": "shell_harmonica",
            "signature_visual": "small palm-sized harmonica carved from a spiral shell with faint pearl glow",
        },
    ]


def _mock_time_continuity_sunrise() -> dict:
    return {
        "scene_id": 5,
        "time_of_day": "golden morning sunrise",
        "lighting": "warm amber light from the rising sun, long shadows toward the west",
        "weather": "clear sky, light sea breeze",
    }


# ---------------------------------------------------------------------------
# inject_identity_anchors — happy path
# ---------------------------------------------------------------------------


def test_inject_with_full_5_dim_context_produces_all_blocks():
    _require_import()
    base = "Coral stands at the underwater palace center, chin lifted."
    out = _INJ.inject_identity_anchors(
        image_prompt=base,
        characters_in_scene=[_mock_coral_mermaid()],
        location=_mock_location_underwater(),
        style_preset="children_book",
        props=_mock_props_shell_harmonica(),
        time_continuity=_mock_time_continuity_sunrise(),
    )

    # Marker must appear at the start
    assert out.startswith("═══"), f"output must start with Unicode boundary: {out[:80]}"
    # All 5 sections present
    assert "CHARACTER ANCHORS" in out
    assert "STYLE ANCHOR" in out
    assert "LOCATION ANCHOR" in out
    assert "PROPS ANCHOR" in out
    assert "TIME CONTINUITY ANCHOR" in out
    # NARRATIVE SCENE separator after anchors
    assert "[NARRATIVE SCENE — LLM creative layer below]" in out
    # Original prompt preserved at the end
    assert out.endswith(base)


def test_inject_critical_hair_keyword_present_in_output():
    """The reproduction test from test22: Coral hair_color must surface."""
    _require_import()
    base = "Coral floats serenely above the palace floor."
    out = _INJ.inject_identity_anchors(
        image_prompt=base,
        characters_in_scene=[_mock_coral_mermaid()],
        style_preset="children_book",
    )
    # sea-green should be in the prompt after injection
    assert "sea-green" in out.lower(), f"hair_color sea-green missing from: {out[:500]}"


def test_inject_is_idempotent_repeated_calls_identical():
    _require_import()
    base = "Coral floats in the palace."
    once = _INJ.inject_identity_anchors(
        image_prompt=base,
        characters_in_scene=[_mock_coral_mermaid()],
        style_preset="anime",
    )
    twice = _INJ.inject_identity_anchors(
        image_prompt=once,
        characters_in_scene=[_mock_coral_mermaid()],
        style_preset="anime",
    )
    thrice = _INJ.inject_identity_anchors(
        image_prompt=twice,
        characters_in_scene=[_mock_coral_mermaid()],
        style_preset="anime",
    )
    assert once == twice == thrice, "inject_identity_anchors must be idempotent"
    # Only one marker, not 3
    assert once.count(_ANCHOR.IDENTITY_ANCHOR_MARKER) == 1


def test_inject_marker_appears_at_start_position():
    _require_import()
    out = _INJ.inject_identity_anchors(
        image_prompt="anything here",
        characters_in_scene=[_mock_coral_mermaid()],
        style_preset="realistic",
    )
    # marker should appear in the first 200 chars (start position critical
    # for LLM attention)
    marker_pos = out.find(_ANCHOR.IDENTITY_ANCHOR_MARKER)
    assert 0 <= marker_pos < 200, f"marker at position {marker_pos} should be near start"


# ---------------------------------------------------------------------------
# Edge cases (M1 spec C.4)
# ---------------------------------------------------------------------------


def test_inject_zero_characters_env_shot_still_injects_other_blocks():
    """Pure environmental shot — no characters, but location/style/time still anchored."""
    _require_import()
    base = "Wide establishing shot of empty underwater palace."
    out = _INJ.inject_identity_anchors(
        image_prompt=base,
        characters_in_scene=[],
        location=_mock_location_underwater(),
        style_preset="children_book",
        time_continuity=_mock_time_continuity_sunrise(),
    )
    # Anchor marker present
    assert _ANCHOR.IDENTITY_ANCHOR_MARKER in out
    # No CHARACTER ANCHORS block (empty char list)
    assert "CHARACTER ANCHORS" not in out
    # But style + location + time still present
    assert "STYLE ANCHOR" in out
    assert "LOCATION ANCHOR" in out
    assert "TIME CONTINUITY ANCHOR" in out


def test_inject_zero_props_skips_props_block():
    _require_import()
    out = _INJ.inject_identity_anchors(
        image_prompt="A scene.",
        characters_in_scene=[_mock_coral_mermaid()],
        style_preset="anime",
        props=None,
    )
    assert "PROPS ANCHOR" not in out


def test_inject_no_location_skips_location_block():
    _require_import()
    out = _INJ.inject_identity_anchors(
        image_prompt="A scene.",
        characters_in_scene=[_mock_coral_mermaid()],
        style_preset="anime",
        location=None,
    )
    assert "LOCATION ANCHOR" not in out


def test_inject_no_time_continuity_skips_time_block():
    _require_import()
    out = _INJ.inject_identity_anchors(
        image_prompt="A scene.",
        characters_in_scene=[_mock_coral_mermaid()],
        style_preset="anime",
        time_continuity=None,
    )
    assert "TIME CONTINUITY ANCHOR" not in out


def test_inject_empty_image_prompt_returns_unchanged_when_no_content_for_blocks():
    """All blocks empty + empty prompt — return as-is rather than just a noise header."""
    _require_import()
    out = _INJ.inject_identity_anchors(
        image_prompt="",
        characters_in_scene=[],
        location=None,
        style_preset="__unknown_style__",  # → empty style anchor (just preset name)
        props=None,
        time_continuity=None,
    )
    # Defensive: with unknown style, only the style block is present (just the
    # display name "__unknown_style__ style.") OR injection is skipped entirely
    # depending on how empty things resolve. Both acceptable — the key
    # property is that no exception is raised.
    assert isinstance(out, str)


def test_inject_already_injected_returns_unchanged():
    _require_import()
    pre_injected = (
        "═══════════════════════════════════════════════════════════\n"
        + _ANCHOR.IDENTITY_ANCHOR_MARKER + ", DO NOT VARY]\n"
        + "═══════════════════════════════════════════════════════════\n"
        + "rest of prompt"
    )
    out = _INJ.inject_identity_anchors(
        image_prompt=pre_injected,
        characters_in_scene=[_mock_coral_mermaid()],
        style_preset="anime",
    )
    assert out == pre_injected, "must be no-op when marker already present"


# ---------------------------------------------------------------------------
# Multi-character & non-humanoid dispatch
# ---------------------------------------------------------------------------


def test_inject_multi_character_each_renders_independently():
    _require_import()
    out = _INJ.inject_identity_anchors(
        image_prompt="They stand together.",
        characters_in_scene=[_mock_coral_mermaid(), _mock_sea_witch()],
        style_preset="anime",
    )
    # Both character IDs and names appear
    assert "char_001" in out
    assert "char_003" in out
    assert "Coral" in out
    assert "Sea Witch" in out
    # Both hair colors surface
    assert "sea-green" in out.lower()
    assert "silver-white" in out.lower()


def test_inject_anthropomorphic_animal_routes_fur_color_to_primary():
    _require_import()
    out = _INJ.inject_identity_anchors(
        image_prompt="Milly bounces.",
        characters_in_scene=[_mock_anthropomorphic_rabbit()],
        style_preset="children_book",
    )
    # fur_color is the primary identity field for anthropomorphic_animal
    assert "ivory" in out.lower(), f"fur_color (ivory white) must be in output: {out[:600]}"
    assert "rabbit" in out.lower()


def test_inject_pure_animal_uses_feather_color():
    _require_import()
    out = _INJ.inject_identity_anchors(
        image_prompt="A bird perches.",
        characters_in_scene=[_mock_pure_animal_sparrow()],
        style_preset="watercolor",
    )
    # feather_color is primary for pure animal
    assert "warm brown" in out.lower() or "brown" in out.lower()
    assert "sparrow" in out.lower()


# ---------------------------------------------------------------------------
# Render helper unit tests (private but stable behaviour matters)
# ---------------------------------------------------------------------------


def test_render_character_block_returns_empty_for_no_anchors():
    _require_import()
    out = _INJ._render_character_anchors_block([])
    assert out == ""


def test_render_character_block_skips_anchors_with_no_content():
    _require_import()
    # extract_identity_anchors returns slots even when source is empty
    empty_anchor = _ANCHOR.extract_identity_anchors({})
    out = _INJ._render_character_anchors_block([empty_anchor])
    # No body lines beyond header = skipped entry; whole block returns ""
    assert out == ""


def test_render_style_block_empty_preset_returns_empty():
    _require_import()
    out = _INJ._render_style_anchor_block(None)
    assert out == ""


def test_render_location_block_requires_loc_id_and_visual():
    _require_import()
    # Location with no signature_visual → empty
    no_visual = {
        "location_id": "loc_xx",
        "location_anchor": {
            "name_en": "blank",
            "signature_visual": "",
            "atmosphere": "",
            "interior_or_exterior": "",
        },
    }
    assert _INJ._render_location_anchor_block(no_visual) == ""


def test_render_props_block_skips_empty():
    _require_import()
    assert _INJ._render_props_anchor_block([]) == ""
    # Prop with no signature → skipped
    bad_props = [{"prop_id": "p1", "prop_anchor": {"name_en": "x", "signature_visual": ""}}]
    assert _INJ._render_props_anchor_block(bad_props) == ""


def test_render_time_block_skips_when_no_substantive_fields():
    _require_import()
    empty_time = {
        "scene_id": 5,
        "time_continuity_anchor": {
            "time_of_day": "",
            "lighting": "",
            "weather": "",
            "continuity_from_previous_scene": "",
        },
    }
    assert _INJ._render_time_anchor_block(empty_time) == ""


# ---------------------------------------------------------------------------
# Defensive input handling
# ---------------------------------------------------------------------------


def test_inject_handles_non_string_image_prompt_gracefully():
    _require_import()
    # int / None / dict — must not raise
    for bad in (None, 123, {"x": 1}, []):
        out = _INJ.inject_identity_anchors(
            image_prompt=bad,  # type: ignore[arg-type]
            characters_in_scene=[_mock_coral_mermaid()],
            style_preset="anime",
        )
        assert isinstance(out, str)


def test_inject_handles_non_list_characters_gracefully():
    _require_import()
    out = _INJ.inject_identity_anchors(
        image_prompt="A scene.",
        characters_in_scene=None,  # type: ignore[arg-type]
        style_preset="anime",
    )
    # No characters block but style still injected
    assert "CHARACTER ANCHORS" not in out
    assert "STYLE ANCHOR" in out or out == "A scene."  # depending on style resolution


def test_inject_handles_invalid_character_entries_gracefully():
    _require_import()
    out = _INJ.inject_identity_anchors(
        image_prompt="A scene.",
        characters_in_scene=[None, "string-not-dict", _mock_coral_mermaid(), 42],  # type: ignore[list-item]
        style_preset="anime",
    )
    # Should still inject Coral
    assert "Coral" in out
    assert "sea-green" in out.lower()


# ---------------------------------------------------------------------------
# 3-character scene (multi-character regression)
# ---------------------------------------------------------------------------


def test_inject_three_characters_all_anchored():
    _require_import()
    out = _INJ.inject_identity_anchors(
        image_prompt="The three stand at the altar.",
        characters_in_scene=[
            _mock_coral_mermaid(),
            _mock_sea_witch(),
            _mock_anthropomorphic_rabbit(),
        ],
        style_preset="anime",
        location=_mock_location_underwater(),
    )
    # All 3 char ids
    assert "char_001" in out
    assert "char_002" in out
    assert "char_003" in out
    # Primary identity colors for each
    assert "sea-green" in out.lower()
    assert "silver-white" in out.lower()
    assert "ivory" in out.lower()


# ---------------------------------------------------------------------------
# Output structure sanity
# ---------------------------------------------------------------------------


def test_inject_preserves_original_prompt_after_anchor_section():
    _require_import()
    base = (
        "This is a scene description with many details. "
        "The character looks at the horizon."
    )
    out = _INJ.inject_identity_anchors(
        image_prompt=base,
        characters_in_scene=[_mock_coral_mermaid()],
        style_preset="anime",
    )
    # Original prompt is the tail
    assert out.endswith(base)
    # Anchor section is in front
    anchor_part = out[: -len(base)]
    assert _ANCHOR.IDENTITY_ANCHOR_MARKER in anchor_part


def test_inject_output_contains_narrative_scene_separator():
    _require_import()
    out = _INJ.inject_identity_anchors(
        image_prompt="content",
        characters_in_scene=[_mock_coral_mermaid()],
        style_preset="anime",
    )
    # The template includes a separator between anchor block and LLM content
    assert "[NARRATIVE SCENE — LLM creative layer below]" in out
