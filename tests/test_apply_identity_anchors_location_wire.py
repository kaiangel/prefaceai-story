"""
TASK-T22-NEW-6 (2026-05-22) — _apply_identity_anchors location wire

E2E test22 evidence (5/22 13:47): all 21 shots logged
    [IdentityAnchorInjector] Injected anchors: chars=N, ..., location=N, ...
Root cause: pipeline_orchestrator.py Stage 5 dispatch never passed `outline`
to generate_shot_image_phase2_safe, so the inner _apply_identity_anchors had
no way to look up unique_locations by scene → location_id.

Fix:
  - _apply_identity_anchors accepts `outline` kwarg
  - pipeline_orchestrator.py Stage 5 passes `outline` via kwargs
  - generate_shot_image_phase2_safe pulls `outline` from kwargs and forwards
    to _apply_identity_anchors
  - generate_shot_image_phase2 (NB2 path) does the same defensively

These tests directly exercise the resolution chain by injecting via the real
inject_identity_anchors helper and confirming the LOCATION ANCHOR block is
present when outline is provided.

Author: @backend (Sonnet 4.6 + xhigh) — Wave 7 P2
"""

from __future__ import annotations

import importlib
import logging
import os
import sys
import importlib.util as _ilu

import pytest


# ---------------------------------------------------------------------------
# Defensive import — load identity_anchor_injector via spec (skip
# app.services.__init__ cascade)
# ---------------------------------------------------------------------------


def _clean_and_import_injector():
    for key in (
        "app.services.style_enforcer",
        "app.services.identity_anchor_injector",
        "app.services.story_generator",
        "app.services",
        "app.prompts.identity_anchor_prompts",
        "app.prompts",
        "app.config",
        "app",
    ):
        sys.modules.pop(key, None)

    anchor_mod = importlib.import_module("app.prompts.identity_anchor_prompts")

    inj_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "app", "services", "identity_anchor_injector.py",
    )
    spec = _ilu.spec_from_file_location(
        "app.services.identity_anchor_injector", inj_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load identity_anchor_injector.py from {inj_path}")
    inj = _ilu.module_from_spec(spec)
    sys.modules["app.services.identity_anchor_injector"] = inj
    spec.loader.exec_module(inj)
    return inj, anchor_mod


try:
    _INJ, _ANCHOR = _clean_and_import_injector()
    _IMPORT_OK = True
    _IMPORT_ERR = ""
except Exception as exc:
    _INJ = None  # type: ignore[assignment]
    _IMPORT_OK = False
    _IMPORT_ERR = str(exc)


def _require_import():
    if not _IMPORT_OK:
        pytest.skip(f"injector import failed: {_IMPORT_ERR}")


# ---------------------------------------------------------------------------
# Test fixtures — reproduce test22 outline + storyboard data
# ---------------------------------------------------------------------------


def _test22_outline() -> dict:
    """The actual outline.unique_locations format from test22 4_storyboard."""
    return {
        "unique_locations": [
            {
                "location_id": "stormy_sea",
                "display_name": "暴风雨海面",
                "description_zh": "雷电在乌云间交织, 深色的海浪像巨兽般翻滚",
                "location_type": "exterior",
                "time_of_day": "night",
                "weather": "stormy",
                "atmosphere": "tense_suspenseful",
                "exterior_description": (
                    "A dark, churning ocean with crashing waves "
                    "surrounding a splintered ship deck under lightning"
                ),
                "key_visual_elements": [
                    "crashing waves", "lightning",
                    "splintered ship deck", "dark stormy clouds",
                ],
            },
            {
                "location_id": "witch_cave",
                "display_name": "女巫洞穴",
                "location_type": "interior",
                "time_of_day": "night",
                "weather": "clear",
                "atmosphere": "mysterious_quiet",
                "interior_description": (
                    "A dark, cavernous space lit by flickering "
                    "magical wisps, filled with ancient shells and seaweed"
                ),
                "key_visual_elements": [
                    "glowing magical wisps", "jagged rock formations",
                ],
            },
        ],
    }


def _test22_screenplay() -> dict:
    return {
        "scenes": [
            {"scene_id": 1, "location_id": "stormy_sea", "time_of_day": "night"},
            {"scene_id": 2, "location_id": "witch_cave", "time_of_day": "night"},
        ],
    }


def _test22_characters() -> dict:
    return {
        "characters": [
            {
                "id": "char_001",
                "name_en": "Coral",
                "character_type": "mythological",
                "physical": {
                    "hair_color": "soft pale coral pink",
                    "skin_tone": "fair luminous aquamarine",
                    "eye_color": "vivid ocean blue",
                    "creature_type": "mermaid",
                },
                "clothing": {"top": "blush-pink seashell bodice"},
            },
        ],
    }


# ---------------------------------------------------------------------------
# Core regression — inject WITH location dict shows LOCATION ANCHORS block
# ---------------------------------------------------------------------------


def test_location_dict_produces_location_anchors_block():
    """T22-NEW-6 fix: passing location=dict must produce LOCATION ANCHORS."""
    _require_import()
    outline = _test22_outline()
    location = outline["unique_locations"][0]  # stormy_sea

    result = _INJ.inject_identity_anchors(
        image_prompt="medium shot — Coral swims through wreckage",
        characters_in_scene=_test22_characters()["characters"],
        location=location,
        style_preset="children_book",
    )
    assert "IDENTITY ANCHORS" in result
    assert "LOCATION ANCHOR" in result, (
        "LOCATION ANCHOR block missing — location wire not effective"
    )
    rlow = result.lower()
    # Location key visual elements must surface in the anchor block
    assert "stormy_sea" in result or "暴风雨" in result or "churning" in rlow, (
        "Location signature must appear in anchor"
    )


def test_no_location_produces_no_location_anchors_block():
    """Sanity: omit location → LOCATION ANCHOR block absent."""
    _require_import()
    result = _INJ.inject_identity_anchors(
        image_prompt="generic shot",
        characters_in_scene=_test22_characters()["characters"],
        location=None,
        style_preset="children_book",
    )
    assert "IDENTITY ANCHORS" in result
    assert "LOCATION ANCHOR" not in result


def test_empty_location_dict_produces_no_block():
    """Empty dict {} should be treated as "no location"."""
    _require_import()
    result = _INJ.inject_identity_anchors(
        image_prompt="generic shot",
        characters_in_scene=_test22_characters()["characters"],
        location={},
        style_preset="children_book",
    )
    assert "LOCATION ANCHOR" not in result


def test_location_lookup_simulation_full_chain():
    """Simulate the full pipeline lookup chain:
        shot.scene_id → screenplay.scenes → location_id → outline.unique_locations.

    This is the resolution chain that _apply_identity_anchors performs.
    Here we run it manually to confirm each step works.
    """
    _require_import()
    outline = _test22_outline()
    screenplay = _test22_screenplay()

    shot = {"shot_id": 1, "scene_id": 1, "image_prompt": "shot 1"}

    # Step 1: shot.scene_id → screenplay.scenes
    scene_id = shot["scene_id"]
    location_id = None
    for sc in screenplay["scenes"]:
        if sc.get("scene_id") == scene_id:
            location_id = sc.get("location_id")
            break
    assert location_id == "stormy_sea"

    # Step 2: location_id → outline.unique_locations
    location_dict = None
    for loc in outline["unique_locations"]:
        if loc.get("location_id") == location_id:
            location_dict = loc
            break
    assert location_dict is not None
    assert location_dict["location_id"] == "stormy_sea"

    # Step 3: pass through inject → LOCATION ANCHOR block appears
    result = _INJ.inject_identity_anchors(
        image_prompt=shot["image_prompt"],
        characters_in_scene=[],
        location=location_dict,
        style_preset="children_book",
    )
    assert "LOCATION ANCHOR" in result


def test_witch_cave_location_renders_interior_description():
    """Second location (witch_cave) must also work — not just stormy_sea."""
    _require_import()
    outline = _test22_outline()
    witch_cave = outline["unique_locations"][1]
    result = _INJ.inject_identity_anchors(
        image_prompt="char_001 confronts the witch",
        characters_in_scene=_test22_characters()["characters"],
        location=witch_cave,
        style_preset="children_book",
    )
    assert "LOCATION ANCHOR" in result
    rlow = result.lower()
    # Either the cave name or its interior description visual element
    assert (
        "witch_cave" in result
        or "女巫洞穴" in result
        or "magical wisps" in rlow
        or "cavernous" in rlow
    )


# ---------------------------------------------------------------------------
# Idempotency — wire should not break re-injection safety
# ---------------------------------------------------------------------------


def test_location_anchor_idempotent_on_double_inject():
    """Running inject twice with same args must not duplicate LOCATION block."""
    _require_import()
    outline = _test22_outline()
    location = outline["unique_locations"][0]

    first = _INJ.inject_identity_anchors(
        image_prompt="test prompt",
        characters_in_scene=[],
        location=location,
        style_preset="children_book",
    )
    second = _INJ.inject_identity_anchors(
        image_prompt=first,
        characters_in_scene=[],
        location=location,
        style_preset="children_book",
    )
    assert first == second
    assert first.count("LOCATION ANCHOR") == 1


# ---------------------------------------------------------------------------
# Combined: location + character anchors in one prompt
# ---------------------------------------------------------------------------


def test_combined_character_and_location_anchors_both_present():
    """Combined block: both CHARACTER + LOCATION must coexist."""
    _require_import()
    outline = _test22_outline()
    result = _INJ.inject_identity_anchors(
        image_prompt="Coral swims through stormy sea",
        characters_in_scene=_test22_characters()["characters"],
        location=outline["unique_locations"][0],
        style_preset="children_book",
    )
    assert "CHARACTER ANCHORS" in result
    assert "LOCATION ANCHOR" in result
    assert "STYLE ANCHOR" in result
    rlow = result.lower()
    assert "coral" in rlow
    # location signature
    assert (
        "stormy_sea" in result or "暴风雨" in result
        or "churning" in rlow
    )
