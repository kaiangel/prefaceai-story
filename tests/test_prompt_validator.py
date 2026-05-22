"""
DEC-048 Layer 1 (2026-05-22) — PromptValidator unit tests

Coverage:
  - validate_prompt_vs_schema: detects missing critical anchors
    (hair_color / skin_tone) → severity=critical, passed=False
  - validate detects warning anchors (marks / clothing) → severity=warning,
    passed=True (does not fail the gate)
  - validate passes when all keywords present
  - auto_correct idempotent — won't double-inject when marker already there
  - auto_correct injects full anchor block when marker absent
  - Multi-character validation: each character's misses tracked separately
  - Edge cases: empty prompt, no characters, invalid inputs
  - Severity escalation: critical > warning > info
  - ValidationResult dataclass behaviour

Design:
  - Pure-Python tests, no async, no API calls
  - Same defensive stub-cleanup as test_identity_anchor_injector.py

Author: @backend (Sonnet 4.6 + xhigh)
Owner: TASK-T22-NEW-3 / DEC-048 Layer 1
"""

from __future__ import annotations

import importlib
import sys

import pytest


# ---------------------------------------------------------------------------
# Defensive import
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


def _clean_and_import_validator():
    """Load validator + injector via spec_from_file_location to bypass
    app.services.__init__.py cascade. Same pattern as injector test.
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
        "app.services.prompt_validator",
        "app.services.story_generator",
        "app.services",
        "app.prompts.identity_anchor_prompts",
        "app.prompts",
        "app",
    ):
        sys.modules.pop(key, None)

    # Load anchor prompts via standard import (app.prompts has no cascade)
    anchor_mod = importlib.import_module("app.prompts.identity_anchor_prompts")

    base_dir = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))

    # Load injector first (validator depends on it). Use canonical module
    # name so dataclasses in the validator can resolve cls.__module__.
    inj_path = _os.path.join(base_dir, "app", "services", "identity_anchor_injector.py")
    spec_inj = _ilu.spec_from_file_location(
        "app.services.identity_anchor_injector", inj_path
    )
    if spec_inj is None or spec_inj.loader is None:
        raise ImportError(f"Cannot load identity_anchor_injector.py from {inj_path}")
    inj = _ilu.module_from_spec(spec_inj)
    sys.modules["app.services.identity_anchor_injector"] = inj
    spec_inj.loader.exec_module(inj)  # type: ignore[union-attr]

    # Load validator (canonical name; register BEFORE exec so dataclass
    # decorator can look up sys.modules[cls.__module__] when defining
    # ValidationResult).
    pv_path = _os.path.join(base_dir, "app", "services", "prompt_validator.py")
    spec_pv = _ilu.spec_from_file_location(
        "app.services.prompt_validator", pv_path
    )
    if spec_pv is None or spec_pv.loader is None:
        raise ImportError(f"Cannot load prompt_validator.py from {pv_path}")
    pv = _ilu.module_from_spec(spec_pv)
    sys.modules["app.services.prompt_validator"] = pv  # register BEFORE exec
    spec_pv.loader.exec_module(pv)  # type: ignore[union-attr]
    return pv, inj, anchor_mod


try:
    _PV, _INJ, _ANCHOR = _clean_and_import_validator()
    _IMPORT_OK = True
    _IMPORT_ERR = ""
except Exception as exc:  # pragma: no cover
    _PV = None  # type: ignore[assignment]
    _INJ = None  # type: ignore[assignment]
    _ANCHOR = None  # type: ignore[assignment]
    _IMPORT_OK = False
    _IMPORT_ERR = str(exc)


def _require_import():
    if not _IMPORT_OK:
        pytest.skip(f"prompt_validator import failed: {_IMPORT_ERR}")


# ---------------------------------------------------------------------------
# Mock fixtures
# ---------------------------------------------------------------------------


def _mock_coral() -> dict:
    return {
        "id": "char_001",
        "name_en": "Coral",
        "character_type": "mythological",
        "physical": {
            "hair_color": "deep sea-green with teal highlights, like sunlit seaweed",
            "hair_style": "long flowing past the waist",
            "face_shape": "oval",
            "skin_tone": "fair with luminous aquamarine sheen",
            "eye_color": "vivid ocean blue",
            "eye_shape": "almond",
            "distinctive_marks": ["fine iridescent scale-shimmer along collarbones"],
            "creature_type": "mermaid",
        },
        "clothing": {
            "top": "soft blush-pink shell-fragment bodice",
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


def _mock_rabbit() -> dict:
    return {
        "id": "char_002",
        "name_en": "Milly",
        "character_type": "anthropomorphic_animal",
        "physical": {
            "species": "rabbit",
            "fur_color": "clean warm ivory white",
            "distinctive_marks": ["single pale freckle on left ear"],
        },
        "clothing": {
            "top": "cream knitted vest",
            "accessories": ["straw basket"],
        },
    }


# ---------------------------------------------------------------------------
# ValidationResult dataclass
# ---------------------------------------------------------------------------


def test_validation_result_default_construction():
    _require_import()
    r = _PV.ValidationResult(passed=True)
    assert r.passed is True
    assert r.missing_anchors == []
    assert r.severity == "info"


def test_validation_result_with_missing_entries():
    _require_import()
    r = _PV.ValidationResult(
        passed=False,
        missing_anchors=[{"char_id": "c1", "field": "hair_color", "tokens": ["red"], "severity": "critical"}],
        severity="critical",
    )
    assert r.passed is False
    assert len(r.missing_anchors) == 1
    assert r.severity == "critical"


def test_validation_result_repr_is_compact():
    _require_import()
    r = _PV.ValidationResult(passed=False, severity="critical",
                              missing_anchors=[{"x": 1}, {"y": 2}])
    s = repr(r)
    assert "passed=False" in s
    assert "missing=2" in s
    assert "critical" in s


# ---------------------------------------------------------------------------
# validate_prompt_vs_schema — happy path
# ---------------------------------------------------------------------------


def test_validate_passes_when_all_critical_keywords_present():
    _require_import()
    validator = _PV.PromptValidator()
    # Prompt mentions hair (sea-green), skin (aquamarine), marks (scale-shimmer),
    # and clothing (shell-fragment) — should be info / pass.
    prompt = (
        "Coral with deep sea-green hair, her aquamarine skin glowing softly, "
        "fine iridescent scale-shimmer along her collarbones, wearing a "
        "blush-pink shell-fragment bodice."
    )
    result = validator.validate_prompt_vs_schema(prompt, [_mock_coral()])
    assert result.passed is True
    assert result.severity == "info"
    assert result.missing_anchors == []


def test_validate_critical_fail_when_hair_color_missing():
    """test22 reproduction case — LLM wrote 'dark hair' instead of sea-green."""
    _require_import()
    validator = _PV.PromptValidator()
    # 'dark hair' contains none of [deep, sea-green, teal], and 'aquamarine'
    # is also missing → both critical fields fail
    prompt = "Coral with flowing dark hair drifts above the palace floor."
    result = validator.validate_prompt_vs_schema(prompt, [_mock_coral()])
    assert result.passed is False
    assert result.severity == "critical"
    # At least the hair_color miss should be reported
    fields_missed = {m["field"] for m in result.missing_anchors}
    assert "hair_color" in fields_missed or "primary_color" in fields_missed or any(
        f == "hair_color" for f in fields_missed
    )
    # severity=critical entries must be present
    critical_entries = [m for m in result.missing_anchors if m["severity"] == "critical"]
    assert len(critical_entries) >= 1


def test_validate_critical_fail_when_skin_tone_missing():
    _require_import()
    validator = _PV.PromptValidator()
    # Has hair, missing skin tone
    prompt = "Coral with sea-green hair drifts; nothing about skin colour."
    result = validator.validate_prompt_vs_schema(prompt, [_mock_coral()])
    assert result.passed is False
    assert any(m["field"] == "skin_tone" and m["severity"] == "critical"
               for m in result.missing_anchors)


def test_validate_warning_when_only_marks_or_clothing_missing():
    _require_import()
    validator = _PV.PromptValidator()
    # Has hair + skin, missing marks + clothing
    prompt = "Coral with sea-green hair and aquamarine skin floats in the void."
    result = validator.validate_prompt_vs_schema(prompt, [_mock_coral()])
    # Warning level — passed=True (does not fail gate), severity=warning
    assert result.passed is True
    assert result.severity == "warning"
    fields_missed = {m["field"] for m in result.missing_anchors}
    assert "distinctive_marks" in fields_missed or "clothing_top" in fields_missed


def test_validate_empty_prompt_passes_trivially():
    _require_import()
    validator = _PV.PromptValidator()
    result = validator.validate_prompt_vs_schema("", [_mock_coral()])
    assert result.passed is True
    assert result.severity == "info"
    assert result.missing_anchors == []


def test_validate_no_characters_passes_trivially():
    _require_import()
    validator = _PV.PromptValidator()
    result = validator.validate_prompt_vs_schema("anything", [])
    assert result.passed is True
    assert result.severity == "info"


def test_validate_none_characters_passes():
    _require_import()
    validator = _PV.PromptValidator()
    result = validator.validate_prompt_vs_schema("anything", None)  # type: ignore[arg-type]
    assert result.passed is True


def test_validate_anthropomorphic_uses_primary_color_field():
    _require_import()
    validator = _PV.PromptValidator()
    # Milly's primary color is fur_color (ivory white). Prompt must mention it.
    prompt = "Milly the rabbit hops by, his ivory-white fur catching the light."
    result = validator.validate_prompt_vs_schema(prompt, [_mock_rabbit()])
    # Should pass — ivory mentioned (warning may remain for marks/clothing)
    critical_misses = [m for m in result.missing_anchors if m["severity"] == "critical"]
    assert critical_misses == [], f"unexpected critical miss: {critical_misses}"


def test_validate_anthropomorphic_fail_when_fur_color_missing():
    _require_import()
    validator = _PV.PromptValidator()
    prompt = "A rabbit hops by in a dark blue coat."
    result = validator.validate_prompt_vs_schema(prompt, [_mock_rabbit()])
    assert result.passed is False
    # The miss should reference fur_color (or primary_color routed name)
    found_fur = any(
        m["field"] in ("fur_color", "primary_color", "hair_color") and
        m["severity"] == "critical"
        for m in result.missing_anchors
    )
    assert found_fur


# ---------------------------------------------------------------------------
# Multi-character validation
# ---------------------------------------------------------------------------


def test_validate_multi_character_each_checked_independently():
    _require_import()
    validator = _PV.PromptValidator()
    # Has Coral's hair but not Sea Witch's; has neither skin
    prompt = "Coral with sea-green hair stands beside the witch in the deep."
    result = validator.validate_prompt_vs_schema(prompt, [_mock_coral(), _mock_sea_witch()])
    assert result.passed is False
    char_ids_missed = {m["char_id"] for m in result.missing_anchors}
    # Sea Witch hair (silver-white) missed
    assert "char_003" in char_ids_missed


def test_validate_multi_character_all_pass_when_both_keywords_present():
    _require_import()
    validator = _PV.PromptValidator()
    # Each character's skin_tone must surface — Sea Witch's exact schema
    # value is "soft lavender-pale", so the prompt must contain a hyphenated
    # token match (validator tokenises hyphenated phrases as single tokens).
    prompt = (
        "Coral with deep sea-green hair and aquamarine skin floats. "
        "Beside her, the Sea Witch with silver-white spiraling tendrils, "
        "lavender-pale skin, watches in deep indigo silence."
    )
    result = validator.validate_prompt_vs_schema(prompt, [_mock_coral(), _mock_sea_witch()])
    # Should be info or warning (marks/clothing may miss)
    critical_misses = [m for m in result.missing_anchors if m["severity"] == "critical"]
    assert critical_misses == [], f"unexpected critical misses: {critical_misses}"


# ---------------------------------------------------------------------------
# auto_correct
# ---------------------------------------------------------------------------


def test_auto_correct_idempotent_when_marker_present():
    """LLM tail drifted but injector ran — don't double-inject."""
    _require_import()
    validator = _PV.PromptValidator()
    # Pre-inject with the marker, then add a drifting tail
    base = "Coral floats."
    pre_injected = _INJ.inject_identity_anchors(
        image_prompt=base,
        characters_in_scene=[_mock_coral()],
        style_preset="realistic",
    )
    # Marker is present
    assert _ANCHOR.IDENTITY_ANCHOR_MARKER in pre_injected

    # Synthesize a (false) validation failure — auto_correct should detect
    # marker and bail out without re-injecting
    fake_result = _PV.ValidationResult(
        passed=False,
        missing_anchors=[{
            "char_id": "char_001", "field": "hair_color",
            "tokens": ["bogus"], "severity": "critical", "expected": "bogus"
        }],
        severity="critical",
    )
    out = validator.auto_correct(
        image_prompt=pre_injected,
        validation_result=fake_result,
        characters_in_scene=[_mock_coral()],
    )
    # Output should equal input — no double injection
    assert out == pre_injected
    # Still exactly one marker
    assert out.count(_ANCHOR.IDENTITY_ANCHOR_MARKER) == 1


def test_auto_correct_injects_when_marker_absent():
    _require_import()
    validator = _PV.PromptValidator()
    drifted = "Coral with dark flowing hair stands at the altar."
    result = validator.validate_prompt_vs_schema(drifted, [_mock_coral()])
    assert result.passed is False  # should fail
    out = validator.auto_correct(
        image_prompt=drifted,
        validation_result=result,
        characters_in_scene=[_mock_coral()],
        style_preset="realistic",
    )
    # Marker now present
    assert _ANCHOR.IDENTITY_ANCHOR_MARKER in out
    # sea-green now visible in prompt
    assert "sea-green" in out.lower()


def test_auto_correct_no_op_when_validation_passed():
    _require_import()
    validator = _PV.PromptValidator()
    prompt = "All keywords here: sea-green, aquamarine, scale-shimmer, shell-fragment."
    result = _PV.ValidationResult(passed=True)
    out = validator.auto_correct(
        image_prompt=prompt,
        validation_result=result,
        characters_in_scene=[_mock_coral()],
    )
    assert out == prompt


def test_auto_correct_passes_through_optional_context():
    _require_import()
    validator = _PV.PromptValidator()
    drifted = "Generic content."
    result = validator.validate_prompt_vs_schema(drifted, [_mock_coral()])
    assert result.passed is False
    out = validator.auto_correct(
        image_prompt=drifted,
        validation_result=result,
        characters_in_scene=[_mock_coral()],
        style_preset="children_book",
        location={
            "id": "loc_xx",
            "signature_visual": "bioluminescent coral pillars",
            "atmosphere": "soft blue",
        },
        props=[{"id": "prop_1", "name_en": "harp", "signature_visual": "carved coral harp"}],
        time_continuity={"scene_id": 1, "time_of_day": "dusk", "lighting": "warm gold"},
    )
    # All 5 anchor blocks should now be present
    assert "CHARACTER ANCHORS" in out
    assert "STYLE ANCHOR" in out
    assert "LOCATION ANCHOR" in out
    assert "PROPS ANCHOR" in out
    assert "TIME CONTINUITY ANCHOR" in out


# ---------------------------------------------------------------------------
# Severity classification
# ---------------------------------------------------------------------------


def test_severity_critical_when_hair_missing():
    _require_import()
    validator = _PV.PromptValidator()
    prompt = "Generic bland scene without identity markers."
    result = validator.validate_prompt_vs_schema(prompt, [_mock_coral()])
    assert result.severity == "critical"


def test_severity_warning_when_only_marks_or_clothing_missing():
    _require_import()
    validator = _PV.PromptValidator()
    # critical present, only marks/clothing absent
    prompt = "Coral with sea-green hair and aquamarine skin."
    result = validator.validate_prompt_vs_schema(prompt, [_mock_coral()])
    assert result.severity == "warning"


def test_severity_info_when_all_present():
    _require_import()
    validator = _PV.PromptValidator()
    prompt = (
        "Coral with sea-green hair, aquamarine skin, scale-shimmer along "
        "collarbones, in a shell-fragment bodice."
    )
    result = validator.validate_prompt_vs_schema(prompt, [_mock_coral()])
    assert result.severity == "info"


def test_severity_critical_dominates_over_warning():
    """When both critical and warning misses, severity must be critical."""
    _require_import()
    validator = _PV.PromptValidator()
    # hair missing (critical), also clothing missing (warning)
    prompt = "Generic content."
    result = validator.validate_prompt_vs_schema(prompt, [_mock_coral()])
    # severity must be critical even though warnings also exist
    assert result.severity == "critical"


# ---------------------------------------------------------------------------
# Defensive input handling
# ---------------------------------------------------------------------------


def test_validate_handles_invalid_character_entries():
    _require_import()
    validator = _PV.PromptValidator()
    prompt = "Anything."
    # Mix of valid + invalid entries
    chars = [None, "not-a-dict", _mock_coral(), 42]  # type: ignore[list-item]
    result = validator.validate_prompt_vs_schema(prompt, chars)
    # Should not raise; missing should be from Coral only
    assert all(m.get("char_id") == "char_001" for m in result.missing_anchors)


def test_validate_handles_non_string_prompt():
    _require_import()
    validator = _PV.PromptValidator()
    # None / int — pass trivially (treat as empty)
    for bad in (None, 42, {"x": 1}, []):
        result = validator.validate_prompt_vs_schema(bad, [_mock_coral()])  # type: ignore[arg-type]
        assert result.passed is True


def test_summarize_missing_handles_empty():
    _require_import()
    assert _PV.PromptValidator._summarize_missing([]) == "<none>"


def test_summarize_missing_caps_at_5():
    _require_import()
    misses = [{"char_id": f"c{i}", "field": "hair_color",
               "tokens": ["x"], "severity": "critical"} for i in range(10)]
    s = _PV.PromptValidator._summarize_missing(misses)
    assert "+5 more" in s


# ---------------------------------------------------------------------------
# End-to-end: validate → auto_correct → re-validate flow
# ---------------------------------------------------------------------------


def test_full_flow_validate_correct_revalidate_passes():
    """The whole flow PromptValidator is meant to enable."""
    _require_import()
    validator = _PV.PromptValidator()
    drifted = "Coral with dark flowing hair stands at the altar."

    # 1. Initial validate — fails critical
    r1 = validator.validate_prompt_vs_schema(drifted, [_mock_coral()])
    assert not r1.passed
    assert r1.severity == "critical"

    # 2. Auto-correct
    corrected = validator.auto_correct(
        image_prompt=drifted,
        validation_result=r1,
        characters_in_scene=[_mock_coral()],
        style_preset="realistic",
    )

    # 3. Re-validate — should pass critical (anchor block injected with hair_color)
    r2 = validator.validate_prompt_vs_schema(corrected, [_mock_coral()])
    critical_misses = [m for m in r2.missing_anchors if m["severity"] == "critical"]
    assert critical_misses == [], f"after auto-correct, critical misses remain: {critical_misses}"


def test_full_flow_idempotent_recorrection_is_noop():
    _require_import()
    validator = _PV.PromptValidator()
    drifted = "Generic prompt missing keywords."

    r1 = validator.validate_prompt_vs_schema(drifted, [_mock_coral()])
    corrected_once = validator.auto_correct(drifted, r1, [_mock_coral()])

    # If somehow validation re-runs on the corrected prompt and still flags
    # something (e.g. due to tail content), re-correcting should NOT re-inject
    fake_r = _PV.ValidationResult(
        passed=False,
        missing_anchors=[{"char_id": "char_001", "field": "x", "tokens": ["y"],
                          "severity": "critical"}],
        severity="critical",
    )
    corrected_twice = validator.auto_correct(corrected_once, fake_r, [_mock_coral()])
    # Same output — marker idempotency kicks in
    assert corrected_once == corrected_twice
    assert corrected_twice.count(_ANCHOR.IDENTITY_ANCHOR_MARKER) == 1
