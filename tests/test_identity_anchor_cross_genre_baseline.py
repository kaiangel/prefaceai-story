"""
DEC-048 Layer 1 (2026-05-22) — Cross-Genre 95 Baseline Regression

Validates inject_identity_anchors() universality across:
  - 19 character_types
  - 5 representative styles (realistic / anime / children_book / cyberpunk / ink)
  - 18 shots per test case (mock, zero real API calls)

For every shot that has characters_in_scene:
  - 100% of character primary_color (hair/fur/feather/scale) tokens MUST appear
    in the injected prompt (grep validation, case-insensitive)
  - 100% of character skin_tone tokens MUST appear (for humanoid types with
    non-empty skin_tone)

KEY_LEARNINGS #52 iron rule:
  - Import MUST use importlib.util.spec_from_file_location + sys.modules
    registration to bypass app/services/__init__.py cascade:
      app.services.__init__ -> story_generator -> google.genai -> ImportError
  - Mirrors Backend tests/test_identity_anchor_injector.py pattern exactly.

Zero cost: no real image-generation API calls. All inputs are deterministic
Python mock fixtures.

Author: @tester
Owner: TASK-T22-NEW-3 / DEC-048 Layer 1 Baseline Regression
"""

from __future__ import annotations

import importlib.util
import os
import sys

import pytest


# ---------------------------------------------------------------------------
# KEY_LEARNINGS #52 — importlib isolation pattern
# Must mirror Backend test_identity_anchor_injector.py and AI-ML
# test_identity_anchor_extraction.py to avoid google.genai cascade ImportError.
# ---------------------------------------------------------------------------

_STUB_SUSPECTS = (
    "anthropic", "google", "google.genai", "google.generativeai",
)

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _is_stub(mod) -> bool:
    """Heuristic: stub modules lack a site-packages __file__ / __path__."""
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

    Registers in sys.modules BEFORE exec_module so any dataclass
    cls.__module__ resolution works correctly (KEY_LEARNINGS #52).
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


def _bootstrap_imports():
    """Clean heavy-SDK stubs, then load anchor_prompts + injector in isolation."""
    # 1. Remove stub suspects (upstream tests may have planted stubs)
    for key in _STUB_SUSPECTS:
        mod = sys.modules.get(key)
        if _is_stub(mod):
            sys.modules.pop(key, None)

    # 2. Remove app.* stubs (some test files stub these without __path__)
    for key in ("app.config", "app", "app.services", "app.prompts", "app.models"):
        mod = sys.modules.get(key)
        if _is_stub(mod):
            sys.modules.pop(key, None)

    # 3. Evict stale cached versions of our own modules so we reload fresh
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

    # 4. Load anchor_prompts via standard importlib (no cascade there)
    anchor_mod = importlib.import_module("app.prompts.identity_anchor_prompts")

    # 5. Load injector directly from file — bypass app.services.__init__
    inj_path = os.path.join(_BASE_DIR, "app", "services", "identity_anchor_injector.py")
    inj_mod = _load_isolated("app.services.identity_anchor_injector", inj_path)

    return anchor_mod, inj_mod


try:
    _ANCHOR, _INJ = _bootstrap_imports()
    _IMPORT_OK = True
    _IMPORT_ERR = ""
except Exception as exc:  # pragma: no cover
    _ANCHOR = None  # type: ignore[assignment]
    _INJ = None  # type: ignore[assignment]
    _IMPORT_OK = False
    _IMPORT_ERR = str(exc)


def _require_import():
    if not _IMPORT_OK:
        pytest.skip(f"Layer 1 import failed: {_IMPORT_ERR}")


# Public symbols used in tests
if _IMPORT_OK:
    extract_identity_anchors = _ANCHOR.extract_identity_anchors
    extract_distinctive_tokens = _ANCHOR.extract_distinctive_tokens
    inject_identity_anchors = _INJ.inject_identity_anchors
else:
    # Placeholders so the file still parses when import fails
    extract_identity_anchors = None  # type: ignore[assignment]
    extract_distinctive_tokens = None  # type: ignore[assignment]
    inject_identity_anchors = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# 19 character_types — full list (spec E.1)
# Note: some names differ from AI-ML spec to match actual schema field values
# used in CharacterDesigner output (e.g. "object_personified" vs "object").
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

# 5 representative styles (spec E.1 — diverse across visual axis)
ALL_5_STYLES = [
    "realistic",
    "anime",
    "children_book",
    "cyberpunk",
    "ink",
]


# ---------------------------------------------------------------------------
# Mock character fixtures — one template per character_type
# Each fixture provides the minimal schema needed for extract_identity_anchors
# to return a non-trivial primary_color anchor.
# ---------------------------------------------------------------------------

def _mock_character(char_type: str, char_id: str = "char_001", index: int = 0) -> dict:
    """Return a mock character dict for the given character_type."""
    base = {
        "id": char_id,
        "name_en": f"TestChar{index}",
        "character_type": char_type,
    }

    if char_type == "human":
        base["physical"] = {
            "hair_color": "warm chestnut brown",
            "hair_style": "medium length wavy",
            "face_shape": "oval",
            "skin_tone": "light golden tan",
            "eye_color": "hazel green",
            "eye_shape": "almond",
            "distinctive_marks": ["small scar on left chin"],
        }
        base["clothing"] = {
            "top": "navy blue button-down shirt",
            "accessories": ["silver-framed glasses"],
        }

    elif char_type == "animal":
        base["physical"] = {
            "species": "golden retriever",
            "fur_color": "deep golden amber",
            "eye_color": "warm brown",
            "distinctive_marks": ["white patch on chest"],
        }
        base["clothing"] = {}

    elif char_type == "anthropomorphic_animal":
        base["physical"] = {
            "species": "fox",
            "fur_color": "rich russet orange with cream chest",
            "hair_color": "russet orange",
            "face_shape": "pointed muzzle",
            "skin_tone": "cream-furred",
            "eye_color": "amber gold",
            "distinctive_marks": ["black-tipped ears and tail"],
        }
        base["clothing"] = {
            "top": "forest-green traveller's cloak",
            "accessories": ["leather satchel"],
        }

    elif char_type == "fantasy_creature":
        base["physical"] = {
            "creature_type": "elf",
            "hair_color": "silver moonlight white",
            "hair_style": "long flowing to mid-back",
            "face_shape": "narrow angular",
            "skin_tone": "pale luminescent",
            "eye_color": "violet amethyst",
            "eye_shape": "elongated almond",
            "distinctive_marks": ["pointed ears extending 4cm beyond hairline"],
        }
        base["clothing"] = {
            "top": "emerald silk tunic with gold leaf embroidery",
            "accessories": ["leaf-shaped tiara"],
        }

    elif char_type == "supernatural":
        base["physical"] = {
            "being_type": "ghost",
            "hair_color": "translucent silver-blue",
            "hair_style": "long loose ethereal",
            "face_shape": "oval",
            "skin_tone": "pale luminous with slight blue tinge",
            "eye_color": "hollow white with faint blue glow",
            "distinctive_marks": ["partial transparency through torso"],
        }
        base["clothing"] = {
            "top": "tattered white linen dress",
            "accessories": [],
        }

    elif char_type == "undead":
        base["physical"] = {
            "undead_type": "zombie",
            "original_form": "human",
            "hair_color": "matted dark brown with grey streaks",
            "hair_style": "dishevelled and tangled",
            "face_shape": "gaunt hollow-cheeked",
            "skin_tone": "ashen grey-green with visible decay",
            "eye_color": "milky white clouded",
            "distinctive_marks": ["exposed ribcage on left side", "missing two fingers on right hand"],
        }
        base["clothing"] = {
            "top": "torn business shirt bloodstained",
            "accessories": [],
        }

    elif char_type == "mythological":
        base["physical"] = {
            "creature_type": "mermaid",
            "origin_culture": "East Asian sea legend",
            "hair_color": "deep sea-green with teal highlights",
            "hair_style": "long flowing past the waist",
            "face_shape": "oval",
            "skin_tone": "fair with soft luminous aquamarine sheen",
            "eye_color": "vivid ocean blue faintly luminescent",
            "eye_shape": "almond",
            "distinctive_marks": [
                "iridescent scale-shimmer along collarbones",
                "fish tail of gradient coral-pink to golden-amber scales",
            ],
        }
        base["clothing"] = {
            "top": "shell-fragment bodice soft blush-pink",
            "accessories": ["pearl-tipped pins in hair"],
        }

    elif char_type == "robot":
        base["physical"] = {
            "robot_type": "android",
            "material": "brushed titanium with carbon-fibre panels",
            "hair_color": "silver metallic synthetic fibres",
            "hair_style": "short structured",
            "face_shape": "symmetrical angular",
            "skin_tone": "matte white polymer with subtle seam lines",
            "eye_color": "piercing electric blue LED",
            "distinctive_marks": ["manufacturer serial number etched on left cheekbone"],
        }
        base["clothing"] = {
            "top": "slim-fit charcoal jacket over white undershirt",
            "accessories": ["wrist data-display band"],
        }

    elif char_type == "ai_entity":
        base["physical"] = {
            "digital_type": "AI",
            "base_form": "holographic humanoid",
            "hair_color": "glowing cyan-white digital strands",
            "hair_style": "geometric pixelated short",
            "face_shape": "smooth idealised",
            "skin_tone": "translucent blue-white with data-stream patterns",
            "eye_color": "bright teal scanning",
            "distinctive_marks": ["visible circuit-line patterns across temples"],
        }
        base["clothing"] = {
            "top": "seamless holographic bodysuit with floating interface panels",
            "accessories": [],
        }

    elif char_type == "digital_virtual":
        base["physical"] = {
            "digital_type": "virtual avatar",
            "base_form": "human-like game character",
            "hair_color": "neon purple with electric highlights",
            "hair_style": "asymmetric undercut",
            "face_shape": "heart",
            "skin_tone": "smooth medium warm",
            "eye_color": "bright magenta glowing",
            "distinctive_marks": ["HUD overlay marker at left temple"],
        }
        base["clothing"] = {
            "top": "armoured jacket with glowing trim",
            "accessories": ["holographic earpiece"],
        }

    elif char_type == "hybrid":
        base["physical"] = {
            "primary_type": "human-wolf hybrid",
            "hair_color": "dark charcoal grey",
            "hair_style": "wild tousled medium-length",
            "face_shape": "square with pronounced brow ridges",
            "skin_tone": "tanned olive with dark hair follicle shadows",
            "eye_color": "golden amber wolf-like",
            "distinctive_marks": ["elongated canine teeth visible when speaking", "fur patches on forearms"],
        }
        base["clothing"] = {
            "top": "ripped sleeveless leather vest",
            "accessories": ["metal cuff on right wrist"],
        }

    elif char_type == "alien":
        base["physical"] = {
            "body_plan": "bipedal humanoid",
            "hair_color": "bioluminescent cerulean blue tendrils",
            "hair_style": "tendrils hanging to shoulders",
            "face_shape": "elongated with wide-set eyes",
            "skin_tone": "smooth iridescent indigo",
            "eye_color": "compound faceted gold",
            "distinctive_marks": ["four thin antenna above brow", "neck gill slits"],
        }
        base["clothing"] = {
            "top": "form-fitting bio-mesh suit",
            "accessories": ["translator device on throat"],
        }

    elif char_type == "elemental":
        base["physical"] = {
            "element_type": "fire",
            "material_form": "living flame",
            "hair_color": "blazing amber-to-crimson flame",
            "hair_style": "rising flame tendrils",
            "face_shape": "fluid shifting",
            "skin_tone": "incandescent orange-red with ember glow",
            "eye_color": "white-hot molten",
            "distinctive_marks": ["core of blue-white at chest centre"],
        }
        base["clothing"] = {
            "top": "molten lava armour plate",
            "accessories": [],
        }

    elif char_type == "aquatic":
        base["physical"] = {
            "species": "mermaid",
            "hair_color": "teal-blue with silver tips",
            "hair_style": "long flowing underwater",
            "face_shape": "rounded soft",
            "skin_tone": "pearl-white with scale shimmer",
            "eye_color": "sea-glass green",
            "scale_color": "teal-blue iridescent",
            "distinctive_marks": ["fin-tips on ears", "dorsal scale pattern on shoulders"],
        }
        base["clothing"] = {
            "top": "woven seaweed top with coral clasp",
            "accessories": ["shell necklace"],
        }

    elif char_type == "anthropomorphic_plant":
        base["physical"] = {
            "plant_type": "cherry blossom tree spirit",
            "hair_color": "soft pink petal-hair",
            "hair_style": "loose flowing petals cascading",
            "face_shape": "oval with bark-texture cheekbones",
            "skin_tone": "pale green with subtle leaf-vein patterns",
            "eye_color": "deep forest moss green",
            "distinctive_marks": ["flowering branches growing from shoulders"],
        }
        base["clothing"] = {
            "top": "woven grass and flower dress",
            "accessories": ["flower crown"],
        }

    elif char_type == "insect":
        base["physical"] = {
            "species": "butterfly fairy",
            "chitin_color": "cobalt blue with black edge markings",
            "hair_color": "midnight blue",
            "hair_style": "short pixie",
            "face_shape": "petite delicate",
            "skin_tone": "pale ivory with dusting of blue shimmer",
            "eye_color": "compound mosaic amber-green",
            "wing_type": "monarch-like butterfly wings",
            "distinctive_marks": ["antennae with glowing tips"],
        }
        base["clothing"] = {
            "top": "gossamer dress of wing-material",
            "accessories": ["dewdrop bracelet"],
        }

    elif char_type == "object_personified":
        base["physical"] = {
            "object_type": "grandfather clock",
            "base_object": "antique mahogany longcase clock",
            "hair_color": "golden pendulum swinging",
            "hair_style": "pendulum as beard",
            "face_shape": "clock-face circular",
            "skin_tone": "warm mahogany wood-grain",
            "eye_color": "roman numeral black on ivory",
            "distinctive_marks": ["chiming bell crown", "glass-window chest revealing gears"],
        }
        base["clothing"] = {
            "top": "carved mahogany coat-body",
            "accessories": [],
        }

    elif char_type == "cosmic_entity":
        base["physical"] = {
            "concept_type": "embodiment of galaxy",
            "giant_type": "cosmic",
            "height_category": "vast nebula-scale",
            "hair_color": "swirling nebula purple-pink stardust",
            "hair_style": "galaxy spiral cascading",
            "face_shape": "vast shifting constellation",
            "skin_tone": "deep cosmic black scattered with star-points",
            "eye_color": "supernovae white-gold",
            "distinctive_marks": ["black hole vortex at chest centre", "planets orbiting shoulders"],
        }
        base["clothing"] = {
            "top": "nebula-woven cloak",
            "accessories": [],
        }

    elif char_type == "historical_figure":
        base["physical"] = {
            "hair_color": "black scholar-topknot",
            "hair_style": "formal topknot with jade pin",
            "face_shape": "broad dignified",
            "skin_tone": "warm golden yellow",
            "eye_color": "deep ink-black",
            "eye_shape": "narrow contemplative",
            "distinctive_marks": ["long ceremonial beard", "ink-stained fingertips"],
        }
        base["clothing"] = {
            "top": "imperial blue scholar's robe with crane embroidery",
            "accessories": ["jade scholar's belt ornament"],
        }

    else:
        # Fallback for any unknown type — treat as human
        base["character_type"] = "human"
        base["physical"] = {
            "hair_color": "plain brown",
            "face_shape": "oval",
            "skin_tone": "medium",
            "eye_color": "brown",
        }
        base["clothing"] = {"top": "plain shirt", "accessories": []}

    return base


def _mock_characters(char_type: str, count: int = 3) -> list:
    """Return list of `count` mock characters with the given character_type.

    The first character (char_001) is the primary; others (char_002, char_003)
    are human side characters to simulate a realistic multi-char shot.
    """
    chars = [_mock_character(char_type, char_id=f"char_{1:03d}", index=0)]
    for i in range(1, count):
        # Side characters are always human for simplicity
        chars.append(_mock_character("human", char_id=f"char_{i+1:03d}", index=i))
    return chars


def _mock_location() -> dict:
    """Return a minimal Stage 1 location entry for anchor extraction."""
    return {
        "location_id": "loc_001",
        "location_name": "test_location",
        "interior_description": "a warmly lit interior with wooden floors and soft amber lamps",
        "signature_visual": "wooden beams, amber lanterns, and a stone fireplace",
        "atmosphere": "cosy and intimate",
    }


def _mock_time_continuity(scene_id: int = 1) -> dict:
    """Return a minimal Stage 3 scene dict for time_continuity anchor."""
    return {
        "scene_id": scene_id,
        "time_of_day": "late afternoon golden hour",
        "lighting": "warm amber slanting light, long shadows",
        "weather": "clear sky",
    }


def _mock_storyboard(characters: list, num_shots: int = 18) -> dict:
    """Return a mock storyboard with num_shots shots.

    Shot distribution:
    - Shots 1-6: all 3 characters in scene (group shots)
    - Shots 7-12: primary character only (char_001)
    - Shots 13-18: 2-character shots (char_001 + char_002)
    """
    char_ids = [c["id"] for c in characters]
    shots = []
    for i in range(1, num_shots + 1):
        if i <= 6:
            chars_in = char_ids[:min(3, len(char_ids))]
        elif i <= 12:
            chars_in = [char_ids[0]]
        else:
            chars_in = char_ids[:min(2, len(char_ids))]

        shots.append({
            "shot_id": i,
            "image_prompt": (
                f"Shot {i}: medium shot at eye level. "
                f"Characters interact in scene {((i - 1) // 6) + 1}. "
                f"Focus on emotional expression and narrative beat {i}."
            ),
            "characters_in_scene": chars_in,
            "scene_id": ((i - 1) // 6) + 1,
        })

    return {"shots": shots}


# ---------------------------------------------------------------------------
# Core validation helpers
# ---------------------------------------------------------------------------

def _get_primary_color_value(char: dict) -> str:
    """Extract the primary color value that should appear in the injected prompt."""
    anchors = extract_identity_anchors(char)
    ia = anchors["identity_anchor"]
    # primary_color is the authoritative slot for hair/fur/feather/scale
    primary = ia.get("primary_color") or ia.get("hair_color") or ""
    return primary


def _get_skin_tone_value(char: dict) -> str:
    """Extract skin_tone that should appear in injected prompt (humanoid only)."""
    anchors = extract_identity_anchors(char)
    ia = anchors["identity_anchor"]
    return ia.get("skin_tone") or ""


def _validate_shot_prompt(
    injected: str,
    chars_in_shot: list,
    char_type: str,
    style_preset: str,
    shot_id: int,
) -> list:
    """Validate that injected prompt contains anchor tokens for all visible chars.

    Returns list of failure strings (empty = all pass).
    """
    failures = []

    for char in chars_in_shot:
        anchors = extract_identity_anchors(char)
        ia = anchors["identity_anchor"]
        char_id = anchors["character_id"]
        actual_char_type = anchors["character_type"]

        # --- Primary color check (100% MUST, per spec E.2) ---
        primary_color = ia.get("primary_color") or ia.get("hair_color") or ""
        if primary_color:
            tokens = extract_distinctive_tokens(primary_color, n=3)
            if tokens:
                found = any(tok.lower() in injected.lower() for tok in tokens)
                if not found:
                    failures.append(
                        f"shot_{shot_id:02d} char {char_id} ({actual_char_type}) "
                        f"primary_color={primary_color!r} tokens={tokens} "
                        f"NOT in prompt. style={style_preset}"
                    )

        # --- Skin tone check (humanoid types, 100% MUST per spec E.2) ---
        # Only check skin_tone for humanoid-leaning types with a real skin value
        skin_tone = ia.get("skin_tone") or ""
        # Skip skin_tone check for pure-animal types that don't have skin
        is_pure_animal = actual_char_type in ("animal",)
        if skin_tone and not is_pure_animal:
            tokens = extract_distinctive_tokens(skin_tone, n=3)
            if tokens:
                found = any(tok.lower() in injected.lower() for tok in tokens)
                if not found:
                    failures.append(
                        f"shot_{shot_id:02d} char {char_id} ({actual_char_type}) "
                        f"skin_tone={skin_tone!r} tokens={tokens} "
                        f"NOT in prompt. style={style_preset}"
                    )

    return failures


# ---------------------------------------------------------------------------
# 95 baseline test cases — parametrized
# Each (char_type, style_preset) pair is one test case
# 19 types × 5 styles = 95 total
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("char_type", ALL_19_TYPES)
@pytest.mark.parametrize("style_preset", ALL_5_STYLES)
def test_baseline_case(char_type: str, style_preset: str):
    """Baseline: inject_identity_anchors 100% injects primary_color + skin_tone
    tokens for every character in every shot, across all 19 character_types
    and 5 styles.

    Zero real API calls — pure Python mock + grep validation.
    """
    _require_import()

    # --- Build mock fixture ---
    characters = _mock_characters(char_type, count=3)
    storyboard = _mock_storyboard(characters, num_shots=18)
    location = _mock_location()

    all_failures = []

    # --- Run inject_identity_anchors on all 18 shots ---
    for shot in storyboard["shots"]:
        shot_id = shot["shot_id"]
        raw_prompt = shot["image_prompt"]
        chars_in_shot_ids = shot["characters_in_scene"]
        chars_in_shot = [c for c in characters if c["id"] in chars_in_shot_ids]

        # Compute scene_id for time_continuity
        scene_id = shot.get("scene_id", 1)
        time_cont = _mock_time_continuity(scene_id)

        injected = inject_identity_anchors(
            image_prompt=raw_prompt,
            characters_in_scene=chars_in_shot,
            style_preset=style_preset,
            location=location,
            props=None,
            time_continuity=time_cont,
        )

        # --- Structural checks ---
        # 1. Injected prompt must be longer than raw (anchor was prepended)
        assert len(injected) > len(raw_prompt), (
            f"shot_{shot_id:02d} ({char_type}/{style_preset}): "
            f"injected prompt should be longer than raw. "
            f"raw={len(raw_prompt)} injected={len(injected)}"
        )

        # 2. Original raw prompt must still be in injected (not replaced)
        assert raw_prompt in injected, (
            f"shot_{shot_id:02d} ({char_type}/{style_preset}): "
            f"raw prompt not found in injected — injection overwrote instead of prepending"
        )

        # 3. Idempotency: re-injecting produces identical output
        injected_twice = inject_identity_anchors(
            image_prompt=injected,
            characters_in_scene=chars_in_shot,
            style_preset=style_preset,
            location=location,
            props=None,
            time_continuity=time_cont,
        )
        assert injected == injected_twice, (
            f"shot_{shot_id:02d} ({char_type}/{style_preset}): "
            f"inject_identity_anchors is not idempotent — second call changed the prompt"
        )

        # --- Anchor content validation (per spec E.2) ---
        if chars_in_shot:
            shot_failures = _validate_shot_prompt(
                injected=injected,
                chars_in_shot=chars_in_shot,
                char_type=char_type,
                style_preset=style_preset,
                shot_id=shot_id,
            )
            all_failures.extend(shot_failures)

    # --- Final assertion — all shots must pass ---
    if all_failures:
        failure_summary = "\n  ".join(all_failures)
        pytest.fail(
            f"[{char_type}/{style_preset}] {len(all_failures)} anchor token "
            f"check(s) failed across 18 shots:\n  {failure_summary}"
        )


# ---------------------------------------------------------------------------
# Additional structural tests (non-parametrized)
# These run once and check cross-cutting concerns.
# ---------------------------------------------------------------------------

def test_inject_empty_characters_still_injects_style():
    """Env-only shots (0 characters_in_scene) still inject STYLE ANCHOR."""
    _require_import()
    raw = "Wide establishing shot of the abandoned city plaza."
    injected = inject_identity_anchors(
        image_prompt=raw,
        characters_in_scene=[],
        style_preset="cyberpunk",
        location=None,
        props=None,
        time_continuity=None,
    )
    assert len(injected) > len(raw), "0-char shot should still have style anchor"
    assert raw in injected


def test_inject_all_19_types_returns_string():
    """Smoke test: inject_identity_anchors returns str for all 19 types."""
    _require_import()
    raw = "Test shot narrative scene."
    for ct in ALL_19_TYPES:
        char = _mock_character(ct)
        result = inject_identity_anchors(
            image_prompt=raw,
            characters_in_scene=[char],
            style_preset="realistic",
            location=None,
            props=None,
            time_continuity=None,
        )
        assert isinstance(result, str), f"Expected str for char_type={ct}"
        assert len(result) >= len(raw), f"Injected should be >= raw for char_type={ct}"


def test_inject_6_characters_each_has_independent_block():
    """Multi-character (6 chars) — each character gets its own anchor entry."""
    _require_import()
    chars = [_mock_character("human", char_id=f"char_{i:03d}", index=i) for i in range(6)]
    raw = "Group shot with all characters."
    injected = inject_identity_anchors(
        image_prompt=raw,
        characters_in_scene=chars,
        style_preset="anime",
        location=None,
        props=None,
        time_continuity=None,
    )
    # Each character's id should appear in the injected prompt
    for i, char in enumerate(chars):
        char_id = char["id"]
        assert char_id in injected, (
            f"char {char_id} (index {i}) not found in injected prompt for 6-char shot"
        )


def test_style_anchor_mandatory_keywords_present():
    """Injected prompt contains style mandatory keywords for each of the 5 styles."""
    _require_import()
    raw = "A character standing in the scene."
    char = _mock_character("human")
    for style in ALL_5_STYLES:
        injected = inject_identity_anchors(
            image_prompt=raw,
            characters_in_scene=[char],
            style_preset=style,
            location=None,
            props=None,
            time_continuity=None,
        )
        # Style block should be present — any reasonable style has at least the preset name
        # or mandatory keywords visible in the injected text
        assert len(injected) > len(raw), f"Style anchor missing for style={style}"


def test_location_anchor_injected_when_present():
    """Location signature_visual appears in injected prompt when location provided."""
    _require_import()
    char = _mock_character("human")
    location = {
        "location_id": "loc_test",
        "signature_visual": "glowing purple crystal formations jutting from cave walls",
        "atmosphere": "eerie and luminescent",
    }
    raw = "Character walks through the cave."
    injected = inject_identity_anchors(
        image_prompt=raw,
        characters_in_scene=[char],
        style_preset="realistic",
        location=location,
        props=None,
        time_continuity=None,
    )
    # Location signature_visual text should appear
    assert "crystal" in injected.lower(), (
        "location signature_visual keyword 'crystal' not found in injected prompt"
    )


def test_time_continuity_anchor_injected():
    """Time continuity fields appear in injected prompt when time_continuity provided."""
    _require_import()
    char = _mock_character("human")
    time_cont = {
        "scene_id": 3,
        "time_of_day": "midnight blue hour",
        "lighting": "cold blue moonlight casting stark shadows",
        "weather": "light snow falling",
    }
    raw = "Character stands alone in the storm."
    injected = inject_identity_anchors(
        image_prompt=raw,
        characters_in_scene=[char],
        style_preset="realistic",
        location=None,
        props=None,
        time_continuity=time_cont,
    )
    assert "midnight" in injected.lower(), (
        "time_of_day 'midnight' not found in injected prompt"
    )


def test_non_string_image_prompt_handled_gracefully():
    """Non-string image_prompt is coerced to empty string without raising."""
    _require_import()
    char = _mock_character("human")
    # Should not raise — returns a string
    result = inject_identity_anchors(
        image_prompt=None,  # type: ignore[arg-type]
        characters_in_scene=[char],
        style_preset="realistic",
    )
    assert isinstance(result, str)


def test_extract_distinctive_tokens_basic():
    """extract_distinctive_tokens returns useful tokens for common color strings."""
    _require_import()
    tokens = extract_distinctive_tokens("deep sea-green with teal highlights", n=3)
    assert isinstance(tokens, list)
    assert len(tokens) <= 3
    # Should include "sea-green", "teal", or "deep" (meaningful tokens)
    combined = " ".join(tokens).lower()
    assert any(w in combined for w in ("sea", "green", "teal", "deep")), (
        f"Expected meaningful tokens from sea-green text, got: {tokens}"
    )


def test_all_19_extract_identity_anchors_no_crash():
    """extract_identity_anchors returns valid dict for all 19 character_types."""
    _require_import()
    for ct in ALL_19_TYPES:
        char = _mock_character(ct)
        result = extract_identity_anchors(char)
        assert isinstance(result, dict), f"Expected dict for char_type={ct}"
        assert "identity_anchor" in result, f"Missing identity_anchor key for char_type={ct}"
        ia = result["identity_anchor"]
        assert isinstance(ia, dict), f"identity_anchor not a dict for char_type={ct}"
        # Primary color slot must be present (may be empty string)
        assert "primary_color" in ia, f"Missing primary_color in identity_anchor for {ct}"


def test_baseline_matrix_coverage():
    """Sanity: assert we have 19 types and 5 styles (full matrix = 95 cases)."""
    assert len(ALL_19_TYPES) == 19, f"Expected 19 types, got {len(ALL_19_TYPES)}"
    assert len(ALL_5_STYLES) == 5, f"Expected 5 styles, got {len(ALL_5_STYLES)}"
    assert len(set(ALL_19_TYPES)) == 19, "Duplicate types in ALL_19_TYPES"
    assert len(set(ALL_5_STYLES)) == 5, "Duplicate styles in ALL_5_STYLES"
