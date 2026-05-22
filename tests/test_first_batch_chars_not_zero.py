"""
TASK-T22-NEW-7 (2026-05-22) — first-batch chars=0 regression coverage

Backend root cause + fix verification for the e2e test22 Wave 7 P0:
  - Founder visual evidence (5/22 14:09): Shot 2 mermaid → blue-haired
    human-leg (Coral anchor never injected into prompt)
  - Backend log evidence: 3 of 21 shots logged `chars=0` then 18 logged
    `chars=2` (max_concurrent=3 — first batch all chars=0)
  - 4_storyboard.json inspection: LLM Stage 4 emitted `characters_in_scene=
    ['Coral']` (name_en format) for shots 1-3 but `['char_001']` (char_id
    format) for shots 4+. The OLD `_apply_identity_anchors` only matched
    `c["id"]`, so first-batch chars_in_shot was empty → no character
    anchor injected → Seedream weak-ref-following → wrong rendering.

Fix:
  - identity_anchor_injector.resolve_characters_in_shot(): smart-match by
    id OR name_en OR name (case-insensitive)
  - Defensive WARNING when shot_char_ids is non-empty but resolved chars
    list is empty (KEY_LEARNINGS #50/#52 silent-fail prevention)
  - image_generator._apply_identity_anchors now delegates to this helper

These tests exercise the helper directly (no heavy ImageGenerator import).
That keeps CI fast and the assertions tight to the fix.

Author: @backend (Sonnet 4.6 + xhigh) — Wave 7 P0
Ref: TEAM_CHAT 2026-05-22 14:09 Founder evidence, PENDING.md TASK-T22-NEW-7
"""

from __future__ import annotations

import importlib
import logging
import os
import sys
import importlib.util as _ilu

import pytest


# ---------------------------------------------------------------------------
# Defensive import: load identity_anchor_injector via spec_from_file_location
# to bypass the app.services.__init__ cascade (which imports story_generator
# → google.genai etc., failing in CI without those SDKs).
# Mirrors tests/test_identity_anchor_injector.py exactly.
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
except Exception as exc:  # pragma: no cover
    _INJ = None  # type: ignore[assignment]
    _ANCHOR = None  # type: ignore[assignment]
    _IMPORT_OK = False
    _IMPORT_ERR = str(exc)


def _require_import():
    if not _IMPORT_OK:
        pytest.skip(f"identity_anchor_injector import failed: {_IMPORT_ERR}")


# ---------------------------------------------------------------------------
# Test fixtures — reproduce the test22 / Coral scenario
# ---------------------------------------------------------------------------


def _coral_character() -> dict:
    """char_001 / Coral — the exact failing case from e2e test22."""
    return {
        "id": "char_001",
        "name": "珊瑚",
        "name_en": "Coral",
        "character_type": "mythological",
        "physical": {
            "hair_color": "soft pale coral pink",
            "hair_style": "long flowing waves past waist",
            "face_shape": "oval",
            "skin_tone": "fair with luminous aquamarine sheen",
            "eye_color": "vivid ocean blue",
            "distinctive_marks": [
                "sweeping fish tail of overlapping scales",
                "iridescent scale-shimmer along the collarbones",
            ],
            "creature_type": "mermaid",
        },
        "clothing": {
            "top": "blush-pink seashell bodice",
            "accessories": ["small pearl-tipped pins in hair"],
        },
    }


def _ah_hai_character() -> dict:
    return {
        "id": "char_002",
        "name": "阿海",
        "name_en": "Ah Hai",
        "character_type": "human",
        "physical": {
            "hair_color": "ash blonde with sea-salt highlights",
            "hair_style": "short messy waves",
            "skin_tone": "tanned bronze",
            "eye_color": "warm brown",
        },
        "clothing": {
            "top": "weathered green-and-white fishing tunic",
        },
    }


def _sea_witch_character() -> dict:
    return {
        "id": "char_003",
        "name": "深海女巫",
        "name_en": "Sea Witch",
        "character_type": "mythological",
        "physical": {
            "hair_color": "silver-white tendrils",
            "skin_tone": "lavender-pale",
            "eye_color": "deep abyssal indigo",
        },
        "clothing": {
            "top": "deep sea-moss green robe of woven kelp",
        },
    }


def _all_chars() -> list:
    return [_coral_character(), _ah_hai_character(), _sea_witch_character()]


# ---------------------------------------------------------------------------
# Core regression: name_en (e2e test22 first-batch format)
# ---------------------------------------------------------------------------


def test_name_en_match_resolves_to_full_character():
    """T22-NEW-7 P0 regression: characters_in_scene=['Coral'] (name_en)
    MUST resolve to the Coral character dict."""
    _require_import()
    matched = _INJ.resolve_characters_in_shot(
        shot_char_ids=["Coral"],
        characters_list=_all_chars(),
        shot_id=1,
    )
    assert len(matched) == 1
    assert matched[0]["id"] == "char_001"
    assert matched[0]["name_en"] == "Coral"


def test_name_en_match_multiple_characters_first_batch():
    """Reproduce test22 shot 2 exactly: ['Coral', 'Ah Hai'] → 2 chars."""
    _require_import()
    matched = _INJ.resolve_characters_in_shot(
        shot_char_ids=["Coral", "Ah Hai"],
        characters_list=_all_chars(),
        shot_id=2,
    )
    assert len(matched) == 2
    matched_ids = {c["id"] for c in matched}
    assert matched_ids == {"char_001", "char_002"}


def test_char_id_match_still_works_canonical_format():
    """Confirm canonical char_xxx format still resolves (shots 4+ behavior)."""
    _require_import()
    matched = _INJ.resolve_characters_in_shot(
        shot_char_ids=["char_001", "char_003"],
        characters_list=_all_chars(),
        shot_id=4,
    )
    assert len(matched) == 2
    matched_ids = {c["id"] for c in matched}
    assert matched_ids == {"char_001", "char_003"}


def test_chinese_name_match_via_name_field():
    """LLM may emit Chinese display names — must still resolve."""
    _require_import()
    matched = _INJ.resolve_characters_in_shot(
        shot_char_ids=["珊瑚"],
        characters_list=_all_chars(),
        shot_id=1,
    )
    assert len(matched) == 1
    assert matched[0]["id"] == "char_001"


def test_case_insensitive_match_all_variants():
    """LLM may emit 'CORAL' or 'coral' or '  Coral  ' — all match."""
    _require_import()
    for variant in ("CORAL", "coral", "Coral", "  Coral  ", "cOrAl"):
        matched = _INJ.resolve_characters_in_shot(
            shot_char_ids=[variant],
            characters_list=_all_chars(),
            shot_id=99,
        )
        assert len(matched) == 1, (
            f"Variant {variant!r} should match Coral but got {len(matched)}"
        )
        assert matched[0]["id"] == "char_001"


def test_mixed_name_en_and_char_id_same_shot():
    """Even more chaotic: ['Coral', 'char_002'] → both should resolve."""
    _require_import()
    matched = _INJ.resolve_characters_in_shot(
        shot_char_ids=["Coral", "char_002"],
        characters_list=_all_chars(),
        shot_id=3,
    )
    assert len(matched) == 2
    matched_ids = {c["id"] for c in matched}
    assert matched_ids == {"char_001", "char_002"}


def test_dedup_when_multiple_keys_hit_same_character():
    """['Coral', 'char_001', '珊瑚'] all match char_001 — must be deduped."""
    _require_import()
    matched = _INJ.resolve_characters_in_shot(
        shot_char_ids=["Coral", "char_001", "珊瑚"],
        characters_list=_all_chars(),
        shot_id=5,
    )
    assert len(matched) == 1, (
        f"Expected 1 deduped match, got {len(matched)} — dedup failed"
    )
    assert matched[0]["id"] == "char_001"


# ---------------------------------------------------------------------------
# Defensive WARNING — KEY_LEARNINGS #50/#52 silent-fail prevention
# ---------------------------------------------------------------------------


def test_unknown_ids_logs_defensive_warning(caplog):
    """When shot_char_ids non-empty but no character matches, WARNING
    must be emitted."""
    _require_import()
    with caplog.at_level(logging.WARNING, logger="xuhua"):
        matched = _INJ.resolve_characters_in_shot(
            shot_char_ids=["NonExistent", "AnotherGhost"],
            characters_list=_all_chars(),
            shot_id=7,
        )
    assert matched == []
    assert any(
        "character match miss" in r.getMessage() or "T22-NEW-7" in r.getMessage()
        for r in caplog.records
    ), "Defensive WARNING missing — silent-fail risk"


def test_empty_characters_in_scene_does_not_warn(caplog):
    """Shots with intentionally-empty characters_in_scene (env-only) must
    NOT trigger the defensive WARNING — would be noisy false-positive."""
    _require_import()
    with caplog.at_level(logging.WARNING, logger="xuhua"):
        matched = _INJ.resolve_characters_in_shot(
            shot_char_ids=[],  # intentionally empty (env-only shot)
            characters_list=_all_chars(),
            shot_id=10,
        )
    assert matched == []
    assert not any(
        "character match miss" in r.getMessage() for r in caplog.records
    ), "Empty characters_in_scene must not emit match-miss warning"


def test_warn_suppressed_when_flag_false(caplog):
    """log_mismatch=False (used in unit-test probing) suppresses warning."""
    _require_import()
    with caplog.at_level(logging.WARNING, logger="xuhua"):
        _INJ.resolve_characters_in_shot(
            shot_char_ids=["GhostId"],
            characters_list=_all_chars(),
            shot_id=99,
            log_mismatch=False,
        )
    assert not any(
        "character match miss" in r.getMessage() for r in caplog.records
    )


# ---------------------------------------------------------------------------
# Edge cases — None / empty / malformed inputs
# ---------------------------------------------------------------------------


def test_none_inputs_safe():
    """None / None must return [] without crashing."""
    _require_import()
    assert _INJ.resolve_characters_in_shot(None, None) == []
    assert _INJ.resolve_characters_in_shot(["Coral"], None) == []
    assert _INJ.resolve_characters_in_shot(None, _all_chars()) == []


def test_non_list_inputs_coerced_to_empty():
    """Non-list inputs (str / dict / int) should produce []."""
    _require_import()
    assert _INJ.resolve_characters_in_shot("not a list", _all_chars()) == []
    assert _INJ.resolve_characters_in_shot({}, _all_chars()) == []
    assert _INJ.resolve_characters_in_shot(["Coral"], "broken") == []


def test_characters_list_with_invalid_entries_skipped():
    """Characters list containing non-dict entries should be filtered."""
    _require_import()
    bad_list = [_coral_character(), "not a char dict", None, 42, _ah_hai_character()]
    matched = _INJ.resolve_characters_in_shot(
        shot_char_ids=["Coral", "Ah Hai"],
        characters_list=bad_list,
    )
    assert len(matched) == 2
    assert {c["id"] for c in matched} == {"char_001", "char_002"}


def test_character_missing_id_skipped():
    """Character dict without `id` field is unanchorable — skip."""
    _require_import()
    chars = [
        {"name_en": "NoID", "physical": {}},  # no id
        _coral_character(),
    ]
    matched = _INJ.resolve_characters_in_shot(
        shot_char_ids=["NoID", "Coral"],
        characters_list=chars,
    )
    assert len(matched) == 1
    assert matched[0]["id"] == "char_001"


def test_integer_ids_normalized_to_string():
    """LLM occasionally emits numeric ids (e.g. shot 5 → 5). Should coerce."""
    _require_import()
    chars = [{"id": "5", "name_en": "Five"}]
    matched = _INJ.resolve_characters_in_shot(
        shot_char_ids=[5],  # int
        characters_list=chars,
    )
    assert len(matched) == 1


# ---------------------------------------------------------------------------
# End-to-end integration — full inject_identity_anchors through helper
# ---------------------------------------------------------------------------


def test_full_inject_first_batch_test22_repro():
    """Repro: feed name_en-style shot characters into inject_identity_anchors
    after resolving with helper. Verify anchor block contains Coral identity.
    This proves the integration path is sound."""
    _require_import()
    matched = _INJ.resolve_characters_in_shot(
        shot_char_ids=["Coral", "Ah Hai"],
        characters_list=_all_chars(),
        shot_id=2,
    )
    assert len(matched) == 2

    image_prompt = (
        "Medium shot — Coral swims toward Ah Hai amidst deep ocean wreckage."
    )
    result = _INJ.inject_identity_anchors(
        image_prompt=image_prompt,
        characters_in_scene=matched,
        style_preset="children_book",
    )
    # Anchor block must be prepended
    assert "IDENTITY ANCHORS" in result
    assert "CHARACTER ANCHORS" in result
    assert len(result) > len(image_prompt)
    # Coral identity tokens must appear (the core fix)
    rlow = result.lower()
    assert "coral" in rlow
    assert "mermaid" in rlow or "fish tail" in rlow
    assert "ah hai" in rlow


def test_full_inject_zero_chars_no_character_block():
    """Sanity check: if matched chars is [], no CHARACTER ANCHORS block."""
    _require_import()
    result = _INJ.inject_identity_anchors(
        image_prompt="environment-only shot",
        characters_in_scene=[],
        style_preset="children_book",
    )
    # Style anchor still injects (children_book has display_name)
    assert "IDENTITY ANCHORS" in result
    # But no character anchors block
    assert "CHARACTER ANCHORS" not in result
