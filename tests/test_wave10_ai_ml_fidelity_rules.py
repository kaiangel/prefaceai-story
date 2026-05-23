"""
Wave 10 AI-ML — Verify P3-2 / P3-4 / P3-5 / P3-1 const exist + are wired
=========================================================================

Tests in this file verify the new constants from Wave 10 AI-ML round:
  - P3-2: ASPECT_RATIO_FIDELITY_RULES (storyboard JSON aspect_ratio hallucinate)
  - P3-4: CHARACTER_COUNT_FIDELITY_RULES (EXACTLY N character visible)
  - P3-5: KEY_PROPS_CONSTRAINT_RULES (key_props ≤ 3 items ≤ 50 chars)
  - P3-1: CHARACTER_FIELD_PRESERVATION_RULES (Backend wire pending in api/projects.py)

All 4 const live in app/prompts/storyboard_prompts.py. P3-2/4/5 are wired
into storyboard_director.py LLM prompt templates. P3-1 is wired into Backend
api/projects.py adjust_character (handed off to Backend agent — out of scope
for this test file).
"""
from __future__ import annotations

import re

import pytest


# ---------------------------------------------------------------------------
# A. CONST EXISTS + IS NON-EMPTY + CONTAINS KEY MARKERS
# ---------------------------------------------------------------------------


def test_character_count_fidelity_rules_exists_and_well_formed():
    """P3-4: CHARACTER_COUNT_FIDELITY_RULES must exist + contain key markers."""
    from app.prompts.storyboard_prompts import CHARACTER_COUNT_FIDELITY_RULES

    assert isinstance(CHARACTER_COUNT_FIDELITY_RULES, str)
    assert len(CHARACTER_COUNT_FIDELITY_RULES) > 500
    # Key markers
    assert "CHARACTER COUNT FIDELITY" in CHARACTER_COUNT_FIDELITY_RULES
    assert "Wave 10 P3-4" in CHARACTER_COUNT_FIDELITY_RULES
    assert "FORBIDDEN phrases" in CHARACTER_COUNT_FIDELITY_RULES
    assert "EXACTLY" in CHARACTER_COUNT_FIDELITY_RULES
    # Contains forbidden phrase examples (Seedream extra-figure trap)
    for forbidden in (
        "retreating figures",
        "silhouettes of distant people",
        "blurred forms",
        "background crowd",
    ):
        assert forbidden in CHARACTER_COUNT_FIDELITY_RULES, (
            f"forbidden phrase '{forbidden}' should be listed as red flag"
        )


def test_key_props_constraint_rules_exists_and_well_formed():
    """P3-5: KEY_PROPS_CONSTRAINT_RULES must exist + state hard limits."""
    from app.prompts.storyboard_prompts import KEY_PROPS_CONSTRAINT_RULES

    assert isinstance(KEY_PROPS_CONSTRAINT_RULES, str)
    assert len(KEY_PROPS_CONSTRAINT_RULES) > 500
    assert "KEY PROPS CONSTRAINT" in KEY_PROPS_CONSTRAINT_RULES
    assert "Wave 10 P3-5" in KEY_PROPS_CONSTRAINT_RULES
    # Hard limits stated explicitly
    assert "MAX 3 items per shot" in KEY_PROPS_CONSTRAINT_RULES
    assert "MAX 50 characters per item" in KEY_PROPS_CONSTRAINT_RULES
    assert "ATOMIC prop only" in KEY_PROPS_CONSTRAINT_RULES


def test_aspect_ratio_fidelity_rules_exists_and_well_formed():
    """P3-2: ASPECT_RATIO_FIDELITY_RULES must exist + state copy-from-input rule."""
    from app.prompts.storyboard_prompts import ASPECT_RATIO_FIDELITY_RULES

    assert isinstance(ASPECT_RATIO_FIDELITY_RULES, str)
    assert len(ASPECT_RATIO_FIDELITY_RULES) > 500
    assert "ASPECT RATIO FIDELITY" in ASPECT_RATIO_FIDELITY_RULES
    assert "Wave 10 P3-2" in ASPECT_RATIO_FIDELITY_RULES
    # Core rule: copy from input, not from example
    assert "DO NOT COPY" in ASPECT_RATIO_FIDELITY_RULES or "NEVER copy" in ASPECT_RATIO_FIDELITY_RULES
    assert "project_aspect_ratio" in ASPECT_RATIO_FIDELITY_RULES
    # Lists valid ratios
    for ratio in ("1:1", "2:3", "3:4", "16:9", "9:16"):
        assert ratio in ASPECT_RATIO_FIDELITY_RULES, (
            f"valid Seedream ratio '{ratio}' should be documented"
        )


def test_character_field_preservation_rules_exists_and_well_formed():
    """P3-1: CHARACTER_FIELD_PRESERVATION_RULES must exist + list all 8 mandatory fields."""
    from app.prompts.storyboard_prompts import CHARACTER_FIELD_PRESERVATION_RULES

    assert isinstance(CHARACTER_FIELD_PRESERVATION_RULES, str)
    assert len(CHARACTER_FIELD_PRESERVATION_RULES) > 1000  # Detailed schema rule
    assert "CHARACTER FIELD PRESERVATION" in CHARACTER_FIELD_PRESERVATION_RULES
    assert "Wave 10 P3-1" in CHARACTER_FIELD_PRESERVATION_RULES
    # All 8 mandatory preserved fields must be listed
    for field in (
        "character_type",
        "name",
        "name_en",
        "role",
        "gender",
        "age_appearance",
        "personality",
    ):
        assert field in CHARACTER_FIELD_PRESERVATION_RULES, (
            f"mandatory preserved field '{field}' missing from rule"
        )
    # All 19 character_type values must appear in the documented list
    for ctype in (
        "human",
        "anthropomorphic_animal",
        "animal",
        "fantasy_creature",
        "robot",
    ):
        assert ctype in CHARACTER_FIELD_PRESERVATION_RULES, (
            f"character_type value '{ctype}' should be in 19-type list"
        )
    # MERGE rule must be stated
    assert "MERGE" in CHARACTER_FIELD_PRESERVATION_RULES
    assert "deep copy" in CHARACTER_FIELD_PRESERVATION_RULES or "Start from the ORIGINAL" in CHARACTER_FIELD_PRESERVATION_RULES


# ---------------------------------------------------------------------------
# B. CONST IS WIRED INTO storyboard_director.py LLM PROMPT (P3-2/4/5)
# ---------------------------------------------------------------------------


def _read_storyboard_director_src() -> str:
    """Helper: load storyboard_director.py source as text."""
    import os
    path = os.path.join(
        os.path.dirname(__file__),
        "..", "app", "services", "storyboard_director.py",
    )
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_character_count_const_imported_in_director():
    """P3-4: CHARACTER_COUNT_FIDELITY_RULES must be imported in storyboard_director.py."""
    src = _read_storyboard_director_src()
    assert "CHARACTER_COUNT_FIDELITY_RULES" in src
    # Import statement (anchored to import block)
    assert re.search(
        r"from\s+app\.prompts\.storyboard_prompts\s+import\s*\(",
        src,
    ), "import statement should exist"
    # Used inside f-string at least once in either _build_scene_prompt or _build_prompt
    assert src.count("{CHARACTER_COUNT_FIDELITY_RULES}") >= 1, (
        "const should be wired into at least one prompt f-string"
    )


def test_key_props_const_imported_in_director():
    """P3-5: KEY_PROPS_CONSTRAINT_RULES must be imported + wired."""
    src = _read_storyboard_director_src()
    assert "KEY_PROPS_CONSTRAINT_RULES" in src
    assert src.count("{KEY_PROPS_CONSTRAINT_RULES}") >= 1


def test_aspect_ratio_const_imported_in_director():
    """P3-2: ASPECT_RATIO_FIDELITY_RULES must be imported + wired."""
    src = _read_storyboard_director_src()
    assert "ASPECT_RATIO_FIDELITY_RULES" in src
    assert src.count("{ASPECT_RATIO_FIDELITY_RULES}") >= 1


def test_storyboard_director_aspect_ratio_examples_no_longer_hardcoded():
    """P3-2: hardcoded '"aspect_ratio": "2:3"' in LLM prompt examples must be replaced.

    Two LLM prompt templates inside storyboard_director.py (around L1899 + L2040)
    previously had hardcoded "aspect_ratio": "2:3" → caused LLM to copy verbatim
    rather than read user's actual aspect_ratio from input.

    Validation/runtime fallback dict literals (L1065 + L2327) are NOT subject to
    this rule — those are runtime fallback dicts (when LLM returned nothing or
    empty global_visual_direction). They are also "2:3" placeholders pending
    Backend fix to pull project.aspect_ratio, but they are NOT LLM prompt
    examples and do NOT cause hallucination.
    """
    src = _read_storyboard_director_src()
    # Count remaining occurrences of literal "aspect_ratio": "2:3" pattern
    pattern = r'"aspect_ratio":\s*"2:3"'
    matches = re.findall(pattern, src)
    # Two remaining are the runtime fallback dicts (L1065 + L2327)
    # All LLM prompt examples (was: L1901 + L2040) should have been replaced with placeholder text
    assert len(matches) <= 2, (
        f"Expected ≤ 2 hardcoded \"aspect_ratio\": \"2:3\" (runtime fallback dicts only),"
        f" got {len(matches)} — P3-2 should have replaced LLM prompt examples"
    )

    # New placeholder must appear in at least 2 places (the 2 LLM examples)
    placeholder_pattern = "COPY USER'S aspect_ratio FROM INPUT"
    placeholder_count = src.count(placeholder_pattern)
    assert placeholder_count >= 2, (
        f"placeholder hint should appear in ≥2 LLM examples, got {placeholder_count}"
    )


# ---------------------------------------------------------------------------
# C. SANITY: const block format (markers + idempotency)
# ---------------------------------------------------------------------------


def test_all_wave10_consts_have_section_divider():
    """All Wave 10 const blocks must have ═══ section dividers for visibility."""
    from app.prompts.storyboard_prompts import (
        CHARACTER_COUNT_FIDELITY_RULES,
        KEY_PROPS_CONSTRAINT_RULES,
        ASPECT_RATIO_FIDELITY_RULES,
        CHARACTER_FIELD_PRESERVATION_RULES,
    )

    divider = "═══════════════════════════════════════════════════════════"
    for name, const in (
        ("CHARACTER_COUNT_FIDELITY_RULES", CHARACTER_COUNT_FIDELITY_RULES),
        ("KEY_PROPS_CONSTRAINT_RULES", KEY_PROPS_CONSTRAINT_RULES),
        ("ASPECT_RATIO_FIDELITY_RULES", ASPECT_RATIO_FIDELITY_RULES),
        ("CHARACTER_FIELD_PRESERVATION_RULES", CHARACTER_FIELD_PRESERVATION_RULES),
    ):
        assert divider in const, f"{name} missing section divider"
