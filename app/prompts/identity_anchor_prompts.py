"""
Identity Anchor Framework v1.0 — Prompt templates + extraction helpers

DEC-048 Layer 1 (2026-05-22, AI-ML Opus 4.7 + max thinking)
================================================================

Background:
  test22 fairytale e2e exposed P0 universality disaster: Stage 4 LLM treated
  `HAIR_COLOR_REQUIREMENT_RULE` "Format example" hints as soft suggestions and
  freely overrode them with creative narrative impulse. 20/20 shots had 0
  correct hair_color injections (100% miss).

  Root cause: LLM RLHF training optimizes for narrative quality over schema
  fidelity. Any "soft suggestion" hint is systematically ignored under creative
  pressure. This is not a prompt bug — it is the fundamental tension between
  LLM creative ability and strict consistency.

Solution: separation of concerns
  - LLM (Stage 4) → narrative variables only (pose / expression / camera /
    emotion / interaction / scene_action)
  - Backend post-process → identity anchors (5 dimensions: character / style /
    location / props / time_continuity)

  Anchors are prepended to image_prompt at the START position (where model
  attention is highest), bypassing LLM decision-making entirely. This eliminates
  the entire class of "character physical drift" bugs.

Coverage:
  - 19 character_types (dispatch table in `extract_identity_anchors`)
  - 80+ styles (extracted from `StyleEnforcer`)
  - Any genre / theme (no hardcoding)

Public API (consumed by Backend `inject_identity_anchors` in image_generator.py):
  - IDENTITY_ANCHOR_INSTRUCTION_BLOCK_TEMPLATE — anchor block template
  - NARRATIVE_VARIABLES_GUIDANCE             — LLM creative-layer guidance
  - IDENTITY_ANCHOR_MARKER                   — idempotency marker
  - extract_identity_anchors(character)      — 5-field standardized character anchor
  - extract_style_anchors(style_preset)      — style mandatory/forbidden anchor
  - extract_location_anchors(location)       — location signature anchor
  - extract_props_anchors(props)             — props signature anchor
  - extract_time_continuity_anchors(scene)   — time/lighting/weather anchor
  - extract_distinctive_tokens(text, n=3)    — top-N tokens (PromptValidator use)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


# ═════════════════════════════════════════════════════════════
# Idempotency marker — checked by Backend `inject_identity_anchors` AND
# `PromptValidator.auto_correct` to detect "already injected" state.
#
# Uses Unicode box-drawing characters (═══) so LLM is unlikely to imitate this
# as a literal narrative element.
# ═════════════════════════════════════════════════════════════
IDENTITY_ANCHOR_MARKER = "[IDENTITY ANCHORS — MUST APPEAR EXACTLY AS DESCRIBED"


# ═════════════════════════════════════════════════════════════
# Anchor block template — Backend `inject_identity_anchors` fills the
# {character_anchors_block} / {style_anchor_block} / {location_anchor_block} /
# {props_anchor_block} / {time_continuity_anchor_block} placeholders and
# prepends the result to the LLM-generated image_prompt.
#
# Design principles:
#   1. Marker `[IDENTITY ANCHORS — MUST APPEAR EXACTLY AS DESCRIBED` first
#      (idempotency check + max model attention).
#   2. Each anchor block is independently optional — Backend may skip empty
#      ones via the `{...}` placeholder being filled with empty string.
#   3. The trailing `[NARRATIVE SCENE — LLM creative layer below]` marker
#      cleanly separates Backend-managed anchors from LLM creative output,
#      preventing model confusion.
# ═════════════════════════════════════════════════════════════
IDENTITY_ANCHOR_INSTRUCTION_BLOCK_TEMPLATE = """═══════════════════════════════════════════════════════════
{marker}, DO NOT VARY]
═══════════════════════════════════════════════════════════
{character_anchors_block}{style_anchor_block}{location_anchor_block}{props_anchor_block}{time_continuity_anchor_block}
═══════════════════════════════════════════════════════════
[NARRATIVE SCENE — LLM creative layer below]
═══════════════════════════════════════════════════════════

"""


# ═════════════════════════════════════════════════════════════
# Narrative variables guidance — injected into Stage 4 prompt by
# storyboard_director.py to remind the LLM that anchors are handled by Backend
# and the LLM should only produce narrative variables.
#
# Goal: complement HAIR_COLOR_REQUIREMENT_RULE rewrite by making the
# division-of-labor concrete at the prompt construction site.
# ═════════════════════════════════════════════════════════════
NARRATIVE_VARIABLES_GUIDANCE = """
═══════════════════════════════════════════════════════════
NARRATIVE VARIABLES — YOUR CREATIVE SCOPE (DEC-048 Layer 1)
═══════════════════════════════════════════════════════════

Your image_prompt output should focus ONLY on the narrative variables for
THIS shot. Backend will automatically prepend the authoritative
`[IDENTITY ANCHORS]` block (character physical / style / location / props /
time continuity) before the prompt reaches the image generator.

## YOUR CREATIVE SCOPE — narrative variables ONLY

| Variable          | What you write                                            |
|-------------------|-----------------------------------------------------------|
| pose              | Body posture for this shot (e.g. "chin lifted, hands at chest") |
| expression        | Face emotion (e.g. "eyes wide and direct, lips parted")   |
| camera_angle      | birds_eye/high/eye_level/low/dutch                        |
| camera_distance   | ECU/CU/MCU/MS/MWS/WS/EWS                                  |
| emotion           | Inner state (e.g. "determination, defiance")              |
| interaction       | With other characters / props / environment              |
| scene_action      | What HAPPENS in this shot (the beat)                      |

## OUT OF SCOPE — DO NOT WRITE THESE

❌ Character hair_color / hair_style / face_shape / skin_tone / eye_color /
   eye_shape / distinctive_marks / clothing_core — Backend ANCHOR
❌ Style keywords (watercolor / photorealistic / Pixar 3D / ink wash) — Backend STYLE ANCHOR
❌ Location signature visuals (bioluminescent coral / neon alley) — Backend LOCATION ANCHOR
❌ Props signature visuals (shell harmonica appearance) — Backend PROPS ANCHOR
❌ Time-of-day / lighting / weather signatures — Backend TIME CONTINUITY ANCHOR

## REFER TO CHARACTERS BY id OR name_en ONLY

✅ "char_001 (Coral) stands at the palace center, chin lifted with
    determination, gaze locked unflinchingly on the antagonist beyond"
❌ "Coral with her flowing sea-green hair lifts her chin"
    (anchor duplication — wastes prompt budget + risks conflict with
    backend anchor)

═══════════════════════════════════════════════════════════
"""


# ═════════════════════════════════════════════════════════════
# extract_identity_anchors — dispatch table for 19 character_types
#
# Returns a dict with stable keys:
#   {
#     "character_id": str,
#     "name_en": str,
#     "character_type": str,
#     "identity_anchor": {
#       "hair_color": str,           # may be "" for non-humanoid (animal)
#       "hair_style": str,
#       "face_shape": str,
#       "skin_tone": str,
#       "eye_color": str,
#       "eye_shape": str,
#       "distinctive_marks_short": list[str],
#       "clothing_core": {
#         "top": str,
#         "signature_accessory": str,
#       },
#       # Optional type-specific extras (populated by dispatch):
#       "species": str,                  # animal / anthropomorphic / aquatic / insect
#       "fur_color": str,                # animal / anthropomorphic (mapped to hair_color analog)
#       "feather_color": str,            # animal / anthropomorphic (bird)
#       "scale_color": str,              # animal / aquatic / fantasy
#       "creature_type": str,            # mythological / fantasy_creature
#       "being_type": str,               # supernatural
#       "undead_type": str,              # undead
#       "robot_type": str,               # robot
#       "digital_type": str,             # digital_virtual
#       "object_type": str,              # object
#       "plant_type": str,               # plant
#     }
#   }
# ═════════════════════════════════════════════════════════════

# Centralized dispatch — maps character_type to the "primary identity color"
# field (analog of hair_color for non-humanoid types). This is what the anchor
# block presents as the "hair" line for that character.
#
# test29 fix (#5, 2026-05-26): Stage 2 CharacterDesigner writes ALL type-specific
# attributes into `physical` (not a `character[type]` sub-dict). For a REAL non-human
# creature (golden koi fish, sunflower, ant, talking clock) the identity color lives
# in scale_color / flower_color / exoskeleton_color / color_scheme — NOT hair_color.
# The old map assumed every non-human was a SEMI-humanoid variant (mermaid / dryad /
# butterfly fairy) and only listed hair_color → real creatures lost their primary
# color → "golden koi" rendered red (only `description` free-text survived, which
# conflicted with the species prior). Fix: each type lists its REAL structured color
# field(s) FIRST, with hair_color kept as a TAIL fallback so semi-humanoid variants
# (mermaid with hair, dryad with leaf-hair) still resolve. Field names match the
# Stage 2 schema consumed by character_prompt_builder.py.
_CHARACTER_TYPE_PRIMARY_COLOR_FIELDS: Dict[str, List[str]] = {
    # Humanoid types — hair_color is primary
    "human":                ["hair_color"],
    # Semi/non-humanoid — real color field first, hair_color as semi-humanoid fallback
    "supernatural":         ["skin_color", "aura_color", "ghostly_color", "hair_color"],
    "undead":               ["ghostly_color", "glow_color", "skin_color", "hair_color"],
    "mythological":         ["color_scheme", "scale_color", "skin_type", "hair_color"],
    "fantasy_creature":     ["color_scheme", "scale_color", "skin_texture", "hair_color"],
    "digital_virtual":      ["primary_color", "hologram_color", "accent_color", "hair_color"],
    "robot":                ["color_scheme", "primary_color", "hair_color"],
    "hybrid":               ["color_scheme", "primary_color", "hair_color"],
    "alien":                ["skin_color", "color_scheme", "hair_color"],
    "elemental":            ["energy_color", "secondary_color", "color_scheme", "hair_color"],
    "concept_personified":  ["color_symbolism", "color_scheme", "hair_color"],
    "giant":                ["skin_color", "color_scheme", "hair_color"],
    "miniature":            ["hair_color", "skin_color"],   # usually a tiny humanoid
    "aquatic":              ["scale_color", "fin_color", "skin_color", "hair_color"],  # real fish vs mermaid
    "object":               ["color_scheme", "primary_color", "hair_color"],  # talking clock vs Olaf
    "plant":                ["leaf_color", "flower_color", "bark_color", "hair_color"],  # foliage-dominant; flower as fallback
    "insect":               ["exoskeleton_color", "wing_color", "hair_color"],  # ant vs butterfly fairy
    # Non-humanoid types — primary color is fur/feather/scale/skin
    "anthropomorphic_animal": ["fur_color", "feather_color", "plumage_color", "coat_color", "scale_color", "hair_color"],
    "animal":               ["fur_color", "feather_color", "plumage_color", "scale_color", "skin_color", "chitin_color"],
    "vehicle_character":    ["body_color", "color_scheme", "secondary_color"],  # paint, not biological
}


def extract_identity_anchors(character: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract standardized identity anchor dict from a single character schema.

    Dispatches by character_type to handle all 19 types uniformly. For
    non-humanoid types (animal / anthropomorphic_animal), the primary
    identity color field is fur_color/feather_color/scale_color etc., which
    is mapped to the "primary_color" slot for anchor block rendering. The
    humanoid fallback fields (hair_color/skin_tone/face_shape — added by
    T20-43 / T21-NEW-1 / T21-NEW-2) are read when present.

    Args:
        character: Stage 2 CharacterDesigner output dict — must contain at
            minimum `id` and `character_type`. Tolerates missing/empty
            sub-fields (returns empty string per slot).

    Returns:
        Standardized anchor dict (see module docstring for full schema).
        Always returns a complete dict — never raises. Empty string for
        unavailable fields.
    """
    if not isinstance(character, dict):
        return _empty_identity_anchor("", "", "")

    char_id = str(character.get("id") or "").strip()
    name_en = (character.get("name_en") or character.get("name") or "").strip()
    # Defensive: strip Chinese name fallback
    if name_en and any("一" <= c <= "鿿" for c in name_en):
        name_en = char_id or "character"
    char_type = (character.get("character_type") or "human").strip().lower() or "human"

    physical = character.get("physical") if isinstance(character.get("physical"), dict) else {}
    animal_data = character.get("animal") if isinstance(character.get("animal"), dict) else {}
    clothing = character.get("clothing") if isinstance(character.get("clothing"), dict) else {}

    physical = physical or {}
    animal_data = animal_data or {}
    clothing = clothing or {}

    # --- Primary identity color (hair_color analog) ---
    # Dispatch by type; fall through humanoid fallback if non-humanoid type
    # has T20-43/T21-NEW-1/T21-NEW-2 humanoid fields populated (e.g. mermaid).
    primary_color = ""
    primary_color_field = ""
    primary_field_list = _CHARACTER_TYPE_PRIMARY_COLOR_FIELDS.get(char_type, ["hair_color"])
    for fld in primary_field_list:
        value = _read_field(physical, animal_data, fld)
        if value:
            primary_color = value
            primary_color_field = fld
            break

    # --- Humanoid identity fields (may exist for non-humanoid via fallback) ---
    hair_color = _read_field(physical, animal_data, "hair_color")
    hair_style = _read_field(physical, animal_data, "hair_style")
    face_shape = _read_field(physical, animal_data, "face_shape")
    skin_tone = _read_field(physical, animal_data, "skin_tone")
    eye_color = _read_field(physical, animal_data, "eye_color")
    eye_shape = _read_field(physical, animal_data, "eye_shape")

    # --- Distinctive marks (short — limit 2 marks, 80 chars each) ---
    raw_marks = (
        physical.get("distinctive_marks")
        or animal_data.get("distinctive_marks")
        or []
    )
    distinctive_marks_short = _trim_marks(raw_marks, max_marks=2, max_chars_per=80)

    # --- Clothing core (top + first signature accessory) ---
    top = _safe_str(clothing.get("top"))
    accessories_raw = clothing.get("accessories") or []
    signature_accessory = ""
    if isinstance(accessories_raw, list) and accessories_raw:
        first_acc = accessories_raw[0]
        if isinstance(first_acc, str):
            signature_accessory = _safe_str(first_acc)
    clothing_core = {
        "top": top,
        "signature_accessory": signature_accessory,
    }

    anchor: Dict[str, Any] = {
        "hair_color": hair_color,
        "hair_style": hair_style,
        "face_shape": face_shape,
        "skin_tone": skin_tone,
        "eye_color": eye_color,
        "eye_shape": eye_shape,
        "distinctive_marks_short": distinctive_marks_short,
        "clothing_core": clothing_core,
        # Primary color slot (analog of hair_color for non-humanoid types)
        "primary_color": primary_color,
        "primary_color_field": primary_color_field,
    }

    # --- Type-specific extras (species / creature_type / robot_type / etc.) ---
    # Populated only when present in schema (tolerant of missing fields).
    type_specific_fields = (
        "species", "breed",
        "fur_color", "feather_color", "plumage_color", "coat_color",
        "scale_color", "skin_color", "chitin_color",
        "creature_type", "origin_culture", "base_form",
        "being_type", "undead_type", "original_form",
        "robot_type", "material",
        "digital_type",
        "object_type", "base_object",
        "plant_type",
        "wing_type", "body_type",
        "primary_type",
        "body_plan",
        "element_type", "material_form",
        "concept_type",
        "giant_type", "height_category",
        "base_type",
        "vehicle_type",
    )
    for fld in type_specific_fields:
        value = _read_field(physical, animal_data, fld)
        if value:
            anchor[fld] = value

    return {
        "character_id": char_id,
        "name_en": name_en,
        "character_type": char_type,
        "identity_anchor": anchor,
    }


def _empty_identity_anchor(char_id: str, name_en: str, char_type: str) -> Dict[str, Any]:
    """Return a safe empty anchor structure (for invalid input)."""
    return {
        "character_id": char_id,
        "name_en": name_en,
        "character_type": char_type or "human",
        "identity_anchor": {
            "hair_color": "",
            "hair_style": "",
            "face_shape": "",
            "skin_tone": "",
            "eye_color": "",
            "eye_shape": "",
            "distinctive_marks_short": [],
            "clothing_core": {"top": "", "signature_accessory": ""},
            "primary_color": "",
            "primary_color_field": "",
        },
    }


def _read_field(physical: Dict[str, Any], animal_data: Dict[str, Any], field: str) -> str:
    """Read a field from physical first, then animal sub-dict. Returns ''."""
    value = physical.get(field) if isinstance(physical, dict) else None
    if not value and isinstance(animal_data, dict):
        value = animal_data.get(field)
    return _safe_str(value)


def _safe_str(value: Any) -> str:
    """Coerce to stripped string; empty for None / non-str."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _trim_marks(marks: Any, max_marks: int = 2, max_chars_per: int = 80) -> List[str]:
    """
    Trim distinctive_marks list — keep first N marks, truncate each to M chars.

    Handles list[str], list[dict (with 'text' or 'description')], or scalar str.
    Filters empty entries. Returns [] for invalid input.
    """
    if not marks:
        return []
    if isinstance(marks, str):
        # Single mark as string
        marks = [marks]
    if not isinstance(marks, list):
        return []
    out: List[str] = []
    for m in marks[:max_marks]:
        if isinstance(m, str):
            text = m.strip()
        elif isinstance(m, dict):
            text = _safe_str(m.get("text") or m.get("description") or m.get("desc") or "")
        else:
            continue
        if not text:
            continue
        if len(text) > max_chars_per:
            text = text[:max_chars_per].rstrip() + "..."
        out.append(text)
    return out


# ═════════════════════════════════════════════════════════════
# extract_style_anchors — extract mandatory + forbidden keywords from
# StyleEnforcer.STYLE_ENFORCEMENTS[style_preset].
# ═════════════════════════════════════════════════════════════

def extract_style_anchors(style_preset: str) -> Dict[str, Any]:
    """
    Extract style anchor dict from StyleEnforcer for a given style preset.

    Returns a dict with:
      {
        "style_preset": str,
        "style_anchor": {
          "style_display_name": str,
          "mandatory_keywords_top5": list[str],
          "forbidden_keywords_top8": list[str],
          "style_signature_line": str,  # 1-line concise summary for anchor block
        }
      }

    Falls back to a generic neutral anchor if style_preset unknown.
    """
    preset = (style_preset or "").strip().lower() or "realistic"

    # Load StyleEnforcer via importlib.util.spec_from_file_location to bypass
    # app/services/__init__.py cascade (story_generator → google.genai ImportError).
    # This is the same pattern as T20-52 _load_shot_validator_fresh fixture.
    # See KEY_LEARNINGS #50 / DEC-048: silent fail here = Layer 1 anchor injection
    # completely disabled with no error raised — P0 risk.
    enforcement = None
    try:
        import importlib.util as _ilu
        import os as _os
        _se_path = _os.path.join(
            _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
            "services", "style_enforcer.py",
        )
        _spec = _ilu.spec_from_file_location("_style_enforcer_isolated", _se_path)
        if _spec is None or _spec.loader is None:
            raise ImportError(f"Cannot load style_enforcer.py from {_se_path}")
        _module = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_module)  # type: ignore[union-attr]
        _StyleEnforcer = _module.StyleEnforcer
        enforcement = _StyleEnforcer.STYLE_ENFORCEMENTS.get(preset)
    except (ImportError, FileNotFoundError, AttributeError) as _e:
        import logging as _logging
        _logging.getLogger(__name__).warning(
            "[Layer 1] extract_style_anchors failed to load StyleEnforcer "
            "for preset=%r: %s: %s. "
            "Returning empty anchor — IDENTITY ANCHOR INJECTION WILL BE INCOMPLETE. "
            "This is a P0 risk per DEC-048 / KEY_LEARNINGS #50.",
            preset, type(_e).__name__, _e,
        )

    if enforcement is None:
        return {
            "style_preset": preset,
            "style_anchor": {
                "style_display_name": preset,
                "mandatory_keywords_top5": [],
                "forbidden_keywords_top8": [],
                "style_signature_line": f"{preset} style",
            },
        }

    mandatory = list(getattr(enforcement, "mandatory_keywords", []) or [])[:5]
    forbidden = list(getattr(enforcement, "forbidden_keywords", []) or [])[:8]
    display_name = getattr(enforcement, "style_display_name", preset) or preset
    signature_line = f"{display_name} — {', '.join(mandatory[:3])}" if mandatory else display_name

    return {
        "style_preset": preset,
        "style_anchor": {
            "style_display_name": display_name,
            "mandatory_keywords_top5": mandatory,
            "forbidden_keywords_top8": forbidden,
            "style_signature_line": signature_line,
        },
    }


# ═════════════════════════════════════════════════════════════
# extract_location_anchors — read signature_visual / atmosphere / time_of_day
# from a Stage 1 outline.unique_locations[] entry.
# ═════════════════════════════════════════════════════════════

def extract_location_anchors(location: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract location anchor dict from a location schema (Stage 1 outline entry).

    Returns:
      {
        "location_id": str,
        "location_anchor": {
          "name_en": str,
          "signature_visual": str,
          "atmosphere": str,
          "time_of_day": str,
          "interior_or_exterior": str,
        }
      }

    Returns empty-anchor structure when location is None or empty (Backend
    should skip the LOCATION ANCHOR block in that case).
    """
    if not isinstance(location, dict) or not location:
        return {
            "location_id": "",
            "location_anchor": {
                "name_en": "",
                "signature_visual": "",
                "atmosphere": "",
                "time_of_day": "",
                "interior_or_exterior": "",
            },
        }

    loc_id = str(location.get("id") or location.get("location_id") or "").strip()
    name_en = _safe_str(location.get("name_en") or location.get("name"))
    if name_en and any("一" <= c <= "鿿" for c in name_en):
        name_en = loc_id or "location"

    # Multiple Stage 1 field name variants supported
    signature_visual = _safe_str(
        location.get("signature_visual")
        or location.get("signature_visual_summary")
        or location.get("visual_summary")
        or location.get("description")
    )
    atmosphere = _safe_str(location.get("atmosphere") or location.get("mood"))
    time_of_day = _safe_str(location.get("time_of_day") or location.get("time"))
    interior_or_exterior = _safe_str(
        location.get("interior_or_exterior")
        or location.get("type")
        or location.get("location_type")
    )

    return {
        "location_id": loc_id,
        "location_anchor": {
            "name_en": name_en,
            "signature_visual": signature_visual,
            "atmosphere": atmosphere,
            "time_of_day": time_of_day,
            "interior_or_exterior": interior_or_exterior,
        },
    }


# ═════════════════════════════════════════════════════════════
# extract_props_anchors — extract signature_visual per prop from a props list.
# ═════════════════════════════════════════════════════════════

def extract_props_anchors(props: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Extract prop anchor list from a Stage 2/3 props schema list.

    Returns a list of:
      [
        {
          "prop_id": str,
          "prop_anchor": {
            "name_en": str,
            "signature_visual": str,
          }
        },
        ...
      ]

    Returns [] for empty/None input (Backend skips PROPS ANCHOR block).
    Skips props without signature_visual (they cannot anchor visually).
    """
    if not props or not isinstance(props, list):
        return []

    out: List[Dict[str, Any]] = []
    for p in props:
        if not isinstance(p, dict):
            continue
        prop_id = str(p.get("id") or p.get("prop_id") or "").strip()
        name_en = _safe_str(p.get("name_en") or p.get("name"))
        if name_en and any("一" <= c <= "鿿" for c in name_en):
            name_en = prop_id or "prop"
        signature_visual = _safe_str(
            p.get("signature_visual")
            or p.get("visual_summary")
            or p.get("description")
        )
        # Skip props without ID or signature_visual — cannot anchor
        if not prop_id or not signature_visual:
            continue
        out.append({
            "prop_id": prop_id,
            "prop_anchor": {
                "name_en": name_en,
                "signature_visual": signature_visual,
            },
        })
    return out


# ═════════════════════════════════════════════════════════════
# extract_time_continuity_anchors — extract time_of_day / lighting / weather
# from a Stage 3 scene schema.
# ═════════════════════════════════════════════════════════════

def extract_time_continuity_anchors(scene: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract time continuity anchor dict from a Stage 3 scene schema.

    Returns:
      {
        "scene_id": int | str,
        "time_continuity_anchor": {
          "time_of_day": str,
          "lighting": str,
          "weather": str,
          "continuity_from_previous_scene": str,  # optional, may be empty
        }
      }

    Returns empty-anchor structure when scene is None/empty (Backend skips
    TIME CONTINUITY ANCHOR block).
    """
    if not isinstance(scene, dict) or not scene:
        return {
            "scene_id": "",
            "time_continuity_anchor": {
                "time_of_day": "",
                "lighting": "",
                "weather": "",
                "continuity_from_previous_scene": "",
            },
        }

    scene_id = scene.get("scene_id") or scene.get("id") or ""
    # Scene may have atmosphere as a dict
    atmosphere = scene.get("atmosphere") if isinstance(scene.get("atmosphere"), dict) else {}
    atmosphere = atmosphere or {}

    time_of_day = _safe_str(
        scene.get("time_of_day")
        or atmosphere.get("time_of_day")
        or scene.get("time")
    )
    lighting = _safe_str(
        scene.get("lighting")
        or atmosphere.get("lighting")
    )
    weather = _safe_str(
        scene.get("weather")
        or atmosphere.get("weather")
    )
    continuity = _safe_str(
        scene.get("continuity_from_previous_scene")
        or scene.get("continuity_note")
    )

    return {
        "scene_id": scene_id,
        "time_continuity_anchor": {
            "time_of_day": time_of_day,
            "lighting": lighting,
            "weather": weather,
            "continuity_from_previous_scene": continuity,
        },
    }


# ═════════════════════════════════════════════════════════════
# extract_distinctive_tokens — extract top-N most distinctive tokens from a
# text string. Used by PromptValidator to grep prompt for schema keywords.
#
# Algorithm:
#   1. Lowercase + tokenize on word boundaries (alphanumeric + hyphen).
#   2. Filter out English stopwords + 1-char tokens + pure-digit tokens.
#   3. Preserve insertion order, return first N unique.
# ═════════════════════════════════════════════════════════════

_DISTINCTIVE_STOPWORDS = frozenset({
    # Articles / determiners / pronouns
    "a", "an", "the", "this", "that", "these", "those", "his", "her", "its",
    "their", "my", "your", "our", "one", "two", "three",
    # Common verbs
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "should", "could", "may", "might",
    "can", "shall", "must",
    # Common prepositions / conjunctions
    "of", "in", "on", "at", "to", "for", "with", "by", "from", "as", "into",
    "and", "or", "but", "if", "then", "than", "so", "yet", "nor",
    # Vague descriptors that shouldn't be primary identity tokens
    "very", "much", "more", "less", "some", "any", "all", "each", "every",
    "like", "just", "only", "also", "even",
    # Often-redundant filler in physical descriptions
    "color", "colored", "looking", "such", "kind", "type",
})


def extract_distinctive_tokens(text: str, n: int = 3) -> List[str]:
    """
    Extract top-N distinctive tokens from a descriptive text string.

    Used by `PromptValidator.validate_prompt_vs_schema` to grep image_prompt
    for character schema keywords (e.g. "sea-green" / "teal" / "seaweed" from
    `hair_color="deep sea-green with teal highlights, like sunlit seaweed"`).

    Args:
        text: Source text (typically a schema field value).
        n: Max tokens to return.

    Returns:
        List of lowercase distinctive tokens (≤ n entries), insertion order
        preserved. Returns [] for empty/None input.

    Examples:
        >>> extract_distinctive_tokens("deep sea-green with teal highlights, like sunlit seaweed")
        ['deep', 'sea-green', 'teal']
        >>> extract_distinctive_tokens("fair with a soft luminous aquamarine sheen", n=4)
        ['fair', 'soft', 'luminous', 'aquamarine']
        >>> extract_distinctive_tokens("")
        []
        >>> extract_distinctive_tokens("the and of an")  # all stopwords
        []
    """
    if not text or not isinstance(text, str):
        return []

    # Tokenize: alphanumeric + hyphens, lowercase, drop empty
    # Pattern: word chars + optional internal hyphens (e.g. "sea-green", "blue-violet")
    tokens = re.findall(r"[a-zA-Z][a-zA-Z\-]*[a-zA-Z]|[a-zA-Z]", text.lower())

    seen: set = set()
    out: List[str] = []
    for tok in tokens:
        if len(tok) < 2:
            continue
        if tok in _DISTINCTIVE_STOPWORDS:
            continue
        if tok in seen:
            continue
        seen.add(tok)
        out.append(tok)
        if len(out) >= n:
            break
    return out
