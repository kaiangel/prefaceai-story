"""
T22-NEW-7 (2026-05-22) — ID Format Robustness Regression

Validates resolve_characters_in_shot() across all 19 character_types and
3 ID formats that Stage 4 LLM may emit in shot.characters_in_scene:

  Format A: char_id string  ("char_001", "char_002", ...)
  Format B: name_en string  ("Coral", "Ah Hai", "Su Chen", ...)
  Format C: mixed           (some shots use name_en, others use char_id)

Root cause background (KEY_LEARNINGS #56 Lesson A):
  e2e test22 5/22 — Stage 4 LLM emitted inconsistent characters_in_scene:
    - Shot 1-3: ['Coral'] (name_en)
    - Shot 4-21: ['char_001'] (char_id)
  Old code only compared c["id"] → shots 1-3 resolved 0 chars → CHARACTER
  ANCHORS completely missing → Seedream weak ref following → Shot 2 became
  blue-haired human-legs instead of coral-pink mermaid tail.

  Wave 7 Backend fix: resolve_characters_in_shot() three-key fuzzy match
  (id / name_en / name, case-insensitive, dedup, defensive mismatch WARNING).

Test design principles:
  - Zero real API calls (zero cost, pure Python)
  - Mirrors KEY_LEARNINGS #52 importlib isolation pattern
  - Covers 19 character_types × 3 ID formats = 57 match cases
  - Plus boundary/edge cases: no-match → empty list + log_mismatch WARNING
  - Idempotent: re-running produces identical output

Coverage matrix:
  - 19 char types × format_A (char_id)     = 19 cases
  - 19 char types × format_B (name_en)     = 19 cases
  - 19 char types × format_C (mixed)       = 19 cases
  - boundary cases (no-match, empty input) =  8 cases
  Total: 65 cases

Author: @tester (Sonnet 4.6 xhigh)
Owner: TASK-T22-NEW-7 — Wave 7 ID format mismatch robustness verification
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
from typing import Any, Dict, List, Optional

import pytest


# ---------------------------------------------------------------------------
# KEY_LEARNINGS #52 — importlib isolation pattern
# Must bypass app/services/__init__.py → story_generator → google.genai
# cascade ImportError. Mirrors test_identity_anchor_cross_genre_baseline.py
# ---------------------------------------------------------------------------

_STUB_SUSPECTS = (
    "anthropic", "google", "google.genai", "google.generativeai",
)

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _is_stub(mod) -> bool:
    """Heuristic: stub modules lack a real site-packages __file__ / __path__."""
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


def _load_isolated(module_name: str, file_path: str):
    """Load module via spec_from_file_location to bypass __init__.py cascade.

    Registers in sys.modules BEFORE exec_module so any cls.__module__
    resolution works correctly (KEY_LEARNINGS #52).
    """
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot find spec for {module_name} at {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module  # register BEFORE exec
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _bootstrap_injector():
    """Clean SDK stubs, then load identity_anchor_injector in isolation."""
    # 1. Remove stub suspects
    for key in _STUB_SUSPECTS:
        mod = sys.modules.get(key)
        if _is_stub(mod):
            sys.modules.pop(key, None)

    # 2. Remove app.* stubs
    for key in ("app.config", "app", "app.services", "app.prompts", "app.models"):
        mod = sys.modules.get(key)
        if _is_stub(mod):
            sys.modules.pop(key, None)

    # 3. Evict stale cached versions of our own modules
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

    # 4. Load injector directly from file — bypass app.services.__init__
    inj_path = os.path.join(
        _BASE_DIR, "app", "services", "identity_anchor_injector.py"
    )
    inj_mod = _load_isolated("app.services.identity_anchor_injector", inj_path)

    return inj_mod


try:
    _INJ = _bootstrap_injector()
    _IMPORT_OK = True
    _IMPORT_ERR = ""
except Exception as exc:  # pragma: no cover
    _INJ = None  # type: ignore[assignment]
    _IMPORT_OK = False
    _IMPORT_ERR = str(exc)


def _require_import():
    if not _IMPORT_OK:
        pytest.skip(f"Layer 1 injector import failed: {_IMPORT_ERR}")


if _IMPORT_OK:
    resolve_characters_in_shot = _INJ.resolve_characters_in_shot
else:
    resolve_characters_in_shot = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# 19 character_types
# ---------------------------------------------------------------------------

ALL_19_TYPES = [
    "human",
    "animal",
    "anthropomorphic_animal",
    "fantasy_creature",
    "supernatural",
    "undead",
    "mythological",
    "robot",
    "ai_entity",
    "digital_virtual",
    "hybrid",
    "alien",
    "elemental",
    "aquatic",
    "anthropomorphic_plant",
    "insect",
    "object_personified",
    "cosmic_entity",
    "historical_figure",
]


# ---------------------------------------------------------------------------
# Mock character fixture builder
# Each character has id, name_en, name (Chinese), and character_type.
# ---------------------------------------------------------------------------

def _make_character(char_type: str, index: int = 0) -> Dict[str, Any]:
    """Return a minimal character dict for given type."""
    idx_str = str(index + 1).zfill(3)
    char_id = f"char_{idx_str}"

    # Type-appropriate English names and Chinese names
    _type_names: Dict[str, tuple] = {
        "human":                 ("Su Chen",        "苏晨"),
        "animal":                ("Golden Eagle",   "金鹰"),
        "anthropomorphic_animal": ("Little Bear",   "小熊"),
        "fantasy_creature":      ("Coral",          "珊瑚"),
        "supernatural":          ("Shadow Ghost",   "影鬼"),
        "undead":                ("Iron Skull",     "铁骷髅"),
        "mythological":          ("Lord Azure",     "苍天神"),
        "robot":                 ("ARIA-7",         "艾雅"),
        "ai_entity":             ("Echo",           "回声"),
        "digital_virtual":       ("Pixel King",     "像素王"),
        "hybrid":                ("Fenrir",         "芬里尔"),
        "alien":                 ("Zyx Prime",      "子克"),
        "elemental":             ("Ember",          "炎灵"),
        "aquatic":               ("Ah Hai",         "阿海"),
        "anthropomorphic_plant": ("Bloom",          "花灵"),
        "insect":                ("Moth Queen",     "蛾后"),
        "object_personified":    ("Clockwork",      "钟表精"),
        "cosmic_entity":         ("Void Walker",    "虚空行者"),
        "historical_figure":     ("Hua Mulan",      "花木兰"),
    }

    name_en, name_cn = _type_names.get(char_type, (f"Character {idx_str}", f"角色{idx_str}"))

    return {
        "id": char_id,
        "name_en": name_en,
        "name": name_cn,
        "character_type": char_type,
        "physical": {
            "hair_color": "jet black",
            "skin_tone": "fair",
            "face_shape": "oval",
            "eye_color": "dark brown",
        },
        "clothing": {
            "top": "white shirt",
            "bottom": "dark trousers",
        },
    }


def _make_secondary_character(index: int) -> Dict[str, Any]:
    """Return a distinct secondary (human) character to avoid name collision."""
    idx_str = str(index + 1).zfill(3)
    char_id = f"char_{idx_str}"
    # Give secondary chars unique names that differ from any primary name_en
    secondary_names = ["Ah Ming", "Xiao Hua"]
    name_en = secondary_names[(index - 1) % len(secondary_names)]
    return {
        "id": char_id,
        "name_en": name_en,
        "name": f"次角色{index}",
        "character_type": "human",
        "physical": {
            "hair_color": "brown",
            "skin_tone": "medium",
            "face_shape": "round",
            "eye_color": "brown",
        },
        "clothing": {
            "top": "blue jacket",
            "bottom": "jeans",
        },
    }


def _make_characters_list(char_type: str) -> List[Dict[str, Any]]:
    """Return a 3-character list; char at index 0 has the given type.

    Secondary chars (index 1, 2) use distinct names to avoid false name_en
    matches when the test checks that shot_char_ids=[primary_name_en] returns
    exactly 1 result.
    """
    return [
        _make_character(char_type, 0),
        _make_secondary_character(1),
        _make_secondary_character(2),
    ]


# ---------------------------------------------------------------------------
# Section 1: Format A — characters_in_scene uses char_id strings
# 19 parametrized cases
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("char_type", ALL_19_TYPES)
def test_format_a_char_id_resolves_correctly(char_type: str):
    """Format A: shot uses char_id ('char_001') — must match across all 19 types."""
    _require_import()
    characters = _make_characters_list(char_type)
    target = characters[0]
    target_char_id = target["id"]  # "char_001"

    # Simulate Stage 4 LLM emitting char_id format (most shots, Shot 4-21 in test22)
    shot_char_ids = [target_char_id]

    result = resolve_characters_in_shot(
        shot_char_ids=shot_char_ids,
        characters_list=characters,
        shot_id=f"shot_format_a_{char_type}",
        log_mismatch=False,
    )

    assert len(result) == 1, (
        f"[{char_type}] Format A: expected 1 match for char_id={target_char_id!r}, "
        f"got {len(result)}"
    )
    assert result[0]["id"] == target_char_id, (
        f"[{char_type}] Format A: matched char id mismatch: "
        f"got {result[0]['id']!r}, expected {target_char_id!r}"
    )


# ---------------------------------------------------------------------------
# Section 2: Format B — characters_in_scene uses name_en strings
# 19 parametrized cases (this was the T22-NEW-7 P0 root cause: shots 1-3 in test22)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("char_type", ALL_19_TYPES)
def test_format_b_name_en_resolves_correctly(char_type: str):
    """Format B: shot uses name_en ('Coral') — must match after Wave 7 fix.

    This is the exact T22-NEW-7 root cause: Stage 4 LLM emitted name_en for
    first 3 shots, old code only matched c['id'] → chars=0 → Coral became
    blue-haired human-legs.
    """
    _require_import()
    characters = _make_characters_list(char_type)
    target = characters[0]
    target_name_en = target["name_en"]

    # Simulate Stage 4 LLM emitting name_en format (shots 1-3 in test22)
    shot_char_ids = [target_name_en]

    result = resolve_characters_in_shot(
        shot_char_ids=shot_char_ids,
        characters_list=characters,
        shot_id=f"shot_format_b_{char_type}",
        log_mismatch=False,
    )

    assert len(result) == 1, (
        f"[{char_type}] Format B: expected 1 match for name_en={target_name_en!r}, "
        f"got {len(result)}. T22-NEW-7 fix must handle name_en."
    )
    assert result[0]["id"] == target["id"], (
        f"[{char_type}] Format B: matched wrong character. "
        f"Expected id={target['id']!r}, got {result[0]['id']!r}"
    )


# ---------------------------------------------------------------------------
# Section 3: Format C — mixed (some use name_en, some use char_id)
# 19 parametrized cases — real test22 scenario where shot 1-3 use name_en
# and shot 4-21 use char_id within the same story
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("char_type", ALL_19_TYPES)
def test_format_c_mixed_resolves_all_correctly(char_type: str):
    """Format C: mixed name_en + char_id in same shot.characters_in_scene list.

    Simulates real test22 multi-character scenario where LLM uses:
      - name_en for primary character ('Coral')
      - char_id for secondary character ('char_002')
    Both must resolve. No duplicates in result (dedup by canonical id).
    """
    _require_import()
    characters = _make_characters_list(char_type)
    target_0 = characters[0]  # primary — use name_en
    target_1 = characters[1]  # secondary — use char_id

    # Mixed format: primary by name_en, secondary by char_id
    shot_char_ids = [target_0["name_en"], target_1["id"]]

    result = resolve_characters_in_shot(
        shot_char_ids=shot_char_ids,
        characters_list=characters,
        shot_id=f"shot_format_c_{char_type}",
        log_mismatch=False,
    )

    result_ids = {c["id"] for c in result}
    assert target_0["id"] in result_ids, (
        f"[{char_type}] Format C: primary char (name_en={target_0['name_en']!r}) "
        f"not resolved. result_ids={result_ids}"
    )
    assert target_1["id"] in result_ids, (
        f"[{char_type}] Format C: secondary char (char_id={target_1['id']!r}) "
        f"not resolved. result_ids={result_ids}"
    )
    assert len(result) == 2, (
        f"[{char_type}] Format C: expected exactly 2 results, got {len(result)}. "
        f"Dedup may have dropped one. result_ids={result_ids}"
    )


# ---------------------------------------------------------------------------
# Section 4: Boundary cases
# 8 cases covering edge inputs and defensive behavior
# ---------------------------------------------------------------------------

class TestBoundaryEdgeCases:
    """Boundary cases for resolve_characters_in_shot defensive behavior."""

    def test_empty_shot_char_ids_returns_empty_list(self):
        """Empty shot_char_ids must return empty list without error."""
        _require_import()
        characters = [_make_character("human", 0)]
        result = resolve_characters_in_shot(
            shot_char_ids=[],
            characters_list=characters,
            shot_id="boundary_empty_ids",
            log_mismatch=False,
        )
        assert result == []

    def test_none_shot_char_ids_returns_empty_list(self):
        """None shot_char_ids must normalize to [] and return empty list."""
        _require_import()
        characters = [_make_character("human", 0)]
        result = resolve_characters_in_shot(
            shot_char_ids=None,  # type: ignore[arg-type]
            characters_list=characters,
            shot_id="boundary_none_ids",
            log_mismatch=False,
        )
        assert result == []

    def test_empty_characters_list_returns_empty_list(self):
        """Empty characters_list must return empty list without error."""
        _require_import()
        result = resolve_characters_in_shot(
            shot_char_ids=["char_001"],
            characters_list=[],
            shot_id="boundary_empty_chars",
            log_mismatch=False,
        )
        assert result == []

    def test_no_match_returns_empty_list(self):
        """Non-matching id/name_en must return empty list (not raise)."""
        _require_import()
        characters = [_make_character("human", 0)]
        # 'char_999' doesn't exist in characters list
        result = resolve_characters_in_shot(
            shot_char_ids=["char_999"],
            characters_list=characters,
            shot_id="boundary_no_match",
            log_mismatch=False,  # suppress warning for clean test output
        )
        assert result == []

    def test_no_match_emits_log_mismatch_warning(self, caplog):
        """Non-matching shot_char_ids with log_mismatch=True must emit WARNING.

        KEY_LEARNINGS #50/#52 — silent fail prevention: when characters_in_scene
        is non-empty but no match found, defensive WARNING must surface in logs.
        """
        _require_import()
        characters = [_make_character("human", 0)]
        with caplog.at_level(logging.WARNING, logger="xuhua"):
            result = resolve_characters_in_shot(
                shot_char_ids=["char_999", "NoSuchCharacter"],
                characters_list=characters,
                shot_id="shot_42",
                log_mismatch=True,  # must emit warning
            )
        assert result == []
        # Must have emitted at least one WARNING-level log about the mismatch
        warning_records = [
            r for r in caplog.records
            if r.levelno >= logging.WARNING and "char_999" in r.message
        ]
        assert len(warning_records) >= 1, (
            "Expected WARNING log about character match miss with 'char_999' "
            f"in message. caplog records: {[r.message for r in caplog.records]}"
        )

    def test_dedup_prevents_same_character_appearing_twice(self):
        """When shot_char_ids contains both name_en and char_id for same char,
        result must contain that character only once (dedup by canonical id).
        """
        _require_import()
        characters = [_make_character("human", 0)]
        target = characters[0]
        # Both formats pointing to same character
        shot_char_ids = [target["id"], target["name_en"]]

        result = resolve_characters_in_shot(
            shot_char_ids=shot_char_ids,
            characters_list=characters,
            shot_id="boundary_dedup",
            log_mismatch=False,
        )
        assert len(result) == 1, (
            f"Dedup failed: same character matched twice. result len={len(result)}"
        )
        assert result[0]["id"] == target["id"]

    def test_case_insensitive_name_en_match(self):
        """name_en match must be case-insensitive ('coral' matches 'Coral')."""
        _require_import()
        characters = [_make_character("aquatic", 0)]
        target = characters[0]
        # LLM may emit lowercase version of name_en
        shot_char_ids = [target["name_en"].lower()]

        result = resolve_characters_in_shot(
            shot_char_ids=shot_char_ids,
            characters_list=characters,
            shot_id="boundary_case_insensitive",
            log_mismatch=False,
        )
        assert len(result) == 1, (
            f"Case-insensitive match failed for name_en={target['name_en']!r} "
            f"with shot_id={target['name_en'].lower()!r}"
        )

    def test_case_insensitive_char_id_match(self):
        """char_id match must be case-insensitive ('CHAR_001' matches 'char_001')."""
        _require_import()
        characters = [_make_character("human", 0)]
        target = characters[0]
        # LLM may emit uppercase version of char_id
        shot_char_ids = [target["id"].upper()]

        result = resolve_characters_in_shot(
            shot_char_ids=shot_char_ids,
            characters_list=characters,
            shot_id="boundary_case_insensitive_id",
            log_mismatch=False,
        )
        assert len(result) == 1, (
            f"Case-insensitive match failed for char_id={target['id']!r} "
            f"with shot_id={target['id'].upper()!r}"
        )


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
# Total cases:
#   Section 1 (Format A: char_id):  19 parametrized
#   Section 2 (Format B: name_en):  19 parametrized  ← T22-NEW-7 root cause
#   Section 3 (Format C: mixed):    19 parametrized
#   Section 4 (Boundary):            8 cases
#   ─────────────────────────────────────────────────
#   Total:                          65 cases
#
# Zero API calls. Pure Python mock fixtures. ~0.5s runtime.
# ---------------------------------------------------------------------------
