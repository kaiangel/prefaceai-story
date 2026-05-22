"""
DEC-048 Layer 1 (2026-05-22) — Identity Anchor Injector

Backend post-process to bypass Stage 4 LLM creative drift on character/style/
location/props/time anchors. Prepends a 5-block authoritative anchor section
to the START of `image_prompt` (where model attention is highest), so the
image generator (Seedream / NB2) sees identity-critical descriptors before
any LLM-generated narrative content.

Design principles (from AI-ML M1 spec, context-for-others.md C.1-C.4):
  1. Bypass LLM decision — anchors injected AFTER Stage 4 completes
  2. Inject at PROMPT START — LLM attention is highest at the beginning
  3. Idempotent — re-running N times produces identical output (marker check)
  4. Edge-case safe — 0 chars / 0 props / 0 location all gracefully skipped
  5. Universal across 19 character_types + 80+ styles (extract helpers
     dispatch by type)

Public API:
  - inject_identity_anchors(image_prompt, characters_in_scene, location,
    style_preset, props, time_continuity) -> str

Companion module:
  - app/services/prompt_validator.py uses this for auto-correct re-injection

Author: @backend (Sonnet 4.6 + xhigh)
Owner: TASK-T22-NEW-3 / DEC-048 Layer 1 Backend implementation
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.prompts.identity_anchor_prompts import (
    IDENTITY_ANCHOR_INSTRUCTION_BLOCK_TEMPLATE,
    IDENTITY_ANCHOR_MARKER,
    extract_identity_anchors,
    extract_location_anchors,
    extract_props_anchors,
    extract_style_anchors,
    extract_time_continuity_anchors,
)

logger = logging.getLogger("xuhua")


# ═════════════════════════════════════════════════════════════
# T22-NEW-7 (2026-05-22) — smart character ID resolution
# ═════════════════════════════════════════════════════════════
# Stage 4 LLM emits inconsistent character identifiers in
# shot.characters_in_scene — sometimes name_en ("Coral"), sometimes char_id
# ("char_001"), occasionally Chinese name. The old `c.get("id") in ids`
# check failed when the LLM emitted name_en, causing first-batch chars=0
# (Founder e2e test22 5/22 — 21 shots, first 3 missed all char anchors).
#
# resolve_characters_in_shot does three-key fuzzy match (id / name_en /
# name) with case-insensitive comparison and dedup, then logs a
# defensive WARNING when the caller passed identifiers we couldn't resolve
# (silent-fail prevention per KEY_LEARNINGS #50/#52).
# ═════════════════════════════════════════════════════════════


def resolve_characters_in_shot(
    shot_char_ids: Optional[List[Any]],
    characters_list: Optional[List[Dict[str, Any]]],
    shot_id: Any = None,
    log_mismatch: bool = True,
) -> List[Dict[str, Any]]:
    """Smart-resolve `shot.characters_in_scene` ids against full character
    list, matching by `id` OR `name_en` OR `name` (case-insensitive).

    Returns matched character dicts (deduped). Emits a WARNING log when
    shot_char_ids is non-empty but no match found, so silent failures
    surface in production logs.

    Args:
        shot_char_ids: List from shot["characters_in_scene"] — may contain
            char_id strings, name_en strings, Chinese names, or even ints.
        characters_list: List of character dicts from Stage 2
            characters["characters"]. Each must have at least `id`.
        shot_id: For logging — included in WARNING message.
        log_mismatch: When False, suppress the mismatch WARNING (useful for
            unit tests that intentionally probe edge cases).

    Returns:
        List of matched character dicts (each from characters_list verbatim),
        deduped by canonical `id`. Empty list when no match.
    """
    if not isinstance(shot_char_ids, list):
        shot_char_ids = []
    if not isinstance(characters_list, list):
        characters_list = []

    # Normalize candidate keys (case-insensitive lookup)
    shot_ids_norm: Dict[str, str] = {
        str(cid).strip().lower(): str(cid).strip()
        for cid in shot_char_ids
        if isinstance(cid, (str, int)) and str(cid).strip()
    }

    matched: List[Dict[str, Any]] = []
    seen_canonical_ids: set = set()
    for c in characters_list:
        if not isinstance(c, dict):
            continue
        c_id_raw = c.get("id") or ""
        c_id_canonical = str(c_id_raw).strip()
        if not c_id_canonical or c_id_canonical in seen_canonical_ids:
            continue
        # Build candidate match-keys for this character
        match_keys: List[str] = []
        for fld in ("id", "name_en", "name"):
            val = c.get(fld)
            if isinstance(val, str) and val.strip():
                match_keys.append(val.strip().lower())
        if any(k in shot_ids_norm for k in match_keys):
            matched.append(c)
            seen_canonical_ids.add(c_id_canonical)

    # Defensive WARNING — caller passed non-empty ids but we resolved 0
    if log_mismatch and shot_char_ids and not matched:
        avail = [
            (c.get("id"), c.get("name_en"), c.get("name"))
            for c in characters_list if isinstance(c, dict)
        ]
        logger.warning(
            "[IdentityAnchorInjector] T22-NEW-7 character match miss for "
            "shot %s — characters_in_scene=%r did not match any "
            "id/name_en/name in characters list (%d available: %r). "
            "Identity anchor will inject WITHOUT character anchors. Stage 4 "
            "LLM likely emitted inconsistent character identifiers.",
            shot_id,
            shot_char_ids,
            len(characters_list),
            avail[:5],
        )

    return matched


# ═════════════════════════════════════════════════════════════
# Render helpers — produce a single anchor block string from extracted dict.
# Each helper returns "" for empty input so the template can compose blocks
# unconditionally.
# ═════════════════════════════════════════════════════════════


def _render_character_anchors_block(char_anchors: List[Dict[str, Any]]) -> str:
    """Render CHARACTER ANCHORS block — one entry per character.

    Args:
        char_anchors: list of dicts returned by extract_identity_anchors()
    Returns:
        Formatted block string, or "" if no anchors with usable content.
    """
    if not char_anchors:
        return ""

    entries: List[str] = []
    for anchor in char_anchors:
        if not isinstance(anchor, dict):
            continue
        ia = anchor.get("identity_anchor") or {}
        if not isinstance(ia, dict):
            continue

        char_id = anchor.get("character_id") or "char_?"
        name_en = anchor.get("name_en") or ""
        char_type = anchor.get("character_type") or "human"

        # Header line: char_id (name, type [+ species/creature_type for non-human])
        type_suffix = char_type
        type_extras: List[str] = []
        for fld in ("species", "creature_type", "being_type", "undead_type",
                    "robot_type", "digital_type", "object_type", "plant_type"):
            val = ia.get(fld) or ""
            if val:
                type_extras.append(val)
        if type_extras:
            type_suffix = f"{char_type} {type_extras[0]}"
        header_name = name_en if name_en else char_id
        header = f"{char_id} ({header_name}, {type_suffix}):"

        lines: List[str] = [header]

        # Primary color (hair/fur/feather/scale) — prefer primary_color slot
        primary_color = ia.get("primary_color") or ia.get("hair_color") or ""
        primary_field = ia.get("primary_color_field") or "hair"
        hair_style = ia.get("hair_style") or ""
        if primary_color:
            # Normalize field name → display label
            label = "hair" if primary_field in ("hair_color", "") else primary_field.replace("_color", "")
            if hair_style:
                lines.append(f"- {label}: {primary_color} — {hair_style}")
            else:
                lines.append(f"- {label}: {primary_color}")

        # Face / skin
        face_shape = ia.get("face_shape") or ""
        skin_tone = ia.get("skin_tone") or ""
        if face_shape and skin_tone:
            lines.append(f"- face: {face_shape}, {skin_tone}")
        elif face_shape:
            lines.append(f"- face: {face_shape}")
        elif skin_tone:
            lines.append(f"- skin: {skin_tone}")

        # Eyes
        eye_color = ia.get("eye_color") or ""
        eye_shape = ia.get("eye_shape") or ""
        if eye_color and eye_shape:
            lines.append(f"- eyes: {eye_color} {eye_shape}")
        elif eye_color:
            lines.append(f"- eyes: {eye_color}")

        # Distinctive marks (joined by '; ')
        marks = ia.get("distinctive_marks_short") or []
        if marks and isinstance(marks, list):
            mark_text = "; ".join(m for m in marks if m)
            if mark_text:
                lines.append(f"- signature: {mark_text}")

        # Clothing core (top + signature accessory)
        clothing = ia.get("clothing_core") or {}
        if isinstance(clothing, dict):
            top = clothing.get("top") or ""
            acc = clothing.get("signature_accessory") or ""
            if top and acc:
                lines.append(f"- core outfit: {top}, {acc}")
            elif top:
                lines.append(f"- core outfit: {top}")
            elif acc:
                lines.append(f"- signature accessory: {acc}")

        # Only emit entry if it has at least one body line beyond header
        if len(lines) > 1:
            entries.append("\n".join(lines))

    if not entries:
        return ""

    return "\n## CHARACTER ANCHORS (each visible character)\n\n" + "\n\n".join(entries) + "\n"


def _render_style_anchor_block(style_anchor: Optional[Dict[str, Any]]) -> str:
    """Render STYLE ANCHOR block."""
    if not style_anchor or not isinstance(style_anchor, dict):
        return ""
    sa = style_anchor.get("style_anchor") or {}
    if not isinstance(sa, dict):
        return ""

    display_name = sa.get("style_display_name") or style_anchor.get("style_preset") or ""
    mandatory = sa.get("mandatory_keywords_top5") or []
    forbidden = sa.get("forbidden_keywords_top8") or []

    # If we have neither display_name nor any keywords, skip
    if not display_name and not mandatory and not forbidden:
        return ""

    lines: List[str] = ["\n## STYLE ANCHOR\n"]
    if mandatory:
        lines.append(f"{display_name} — MUST INCLUDE: {', '.join(mandatory)}.")
    elif display_name:
        lines.append(f"{display_name} style.")
    if forbidden:
        lines.append(f"DO NOT USE: {', '.join(forbidden)}.")
    return "\n".join(lines) + "\n"


def _render_location_anchor_block(location_anchor: Optional[Dict[str, Any]]) -> str:
    """Render LOCATION ANCHOR block."""
    if not location_anchor or not isinstance(location_anchor, dict):
        return ""
    la = location_anchor.get("location_anchor") or {}
    if not isinstance(la, dict):
        return ""

    loc_id = location_anchor.get("location_id") or ""
    name_en = la.get("name_en") or ""
    signature_visual = la.get("signature_visual") or ""
    atmosphere = la.get("atmosphere") or ""
    interior_or_exterior = la.get("interior_or_exterior") or ""

    # Require at least loc_id AND (signature_visual OR atmosphere) to emit
    if not loc_id:
        return ""
    if not signature_visual and not atmosphere:
        return ""

    header_parts: List[str] = []
    if loc_id:
        header_parts.append(loc_id)
    if name_en:
        header_parts.append(name_en)
    header = " ".join(header_parts)
    if interior_or_exterior:
        header = f"{header} ({interior_or_exterior})"
    header = f"{header}:"

    lines = ["\n## LOCATION ANCHOR\n", header]
    if signature_visual:
        lines.append(f"- signature visual: {signature_visual}")
    if atmosphere:
        lines.append(f"- atmosphere: {atmosphere}")
    return "\n".join(lines) + "\n"


def _render_props_anchor_block(props_anchors: List[Dict[str, Any]]) -> str:
    """Render PROPS ANCHOR block — one entry per prop."""
    if not props_anchors:
        return ""

    entries: List[str] = []
    for pa in props_anchors:
        if not isinstance(pa, dict):
            continue
        prop_id = pa.get("prop_id") or ""
        anchor = pa.get("prop_anchor") or {}
        if not isinstance(anchor, dict):
            continue
        name_en = anchor.get("name_en") or ""
        signature_visual = anchor.get("signature_visual") or ""
        if not prop_id or not signature_visual:
            continue
        if name_en:
            entries.append(f"{prop_id} ({name_en}): {signature_visual}")
        else:
            entries.append(f"{prop_id}: {signature_visual}")

    if not entries:
        return ""

    return "\n## PROPS ANCHOR\n\n" + "\n".join(entries) + "\n"


def _render_time_anchor_block(time_anchor: Optional[Dict[str, Any]]) -> str:
    """Render TIME CONTINUITY ANCHOR block."""
    if not time_anchor or not isinstance(time_anchor, dict):
        return ""
    ta = time_anchor.get("time_continuity_anchor") or {}
    if not isinstance(ta, dict):
        return ""

    scene_id = time_anchor.get("scene_id")
    time_of_day = ta.get("time_of_day") or ""
    lighting = ta.get("lighting") or ""
    weather = ta.get("weather") or ""
    continuity = ta.get("continuity_from_previous_scene") or ""

    # Require at least one substantive field
    if not (time_of_day or lighting or weather or continuity):
        return ""

    # scene_id may be int / str / 0 — accept anything truthy or 0
    if scene_id in (None, ""):
        return ""

    parts: List[str] = []
    if time_of_day:
        parts.append(time_of_day)
    if lighting:
        parts.append(lighting)
    if weather:
        parts.append(weather)
    descriptor = ", ".join(parts) if parts else ""

    lines: List[str] = ["\n## TIME CONTINUITY ANCHOR\n"]
    if descriptor:
        lines.append(f"scene {scene_id}: {descriptor}.")
    else:
        lines.append(f"scene {scene_id}.")
    if continuity:
        lines.append(continuity)
    return "\n".join(lines) + "\n"


# ═════════════════════════════════════════════════════════════
# Public API — inject_identity_anchors
# ═════════════════════════════════════════════════════════════


def inject_identity_anchors(
    image_prompt: str,
    characters_in_scene: List[Dict[str, Any]],
    location: Optional[Dict[str, Any]] = None,
    style_preset: str = "realistic",
    props: Optional[List[Dict[str, Any]]] = None,
    time_continuity: Optional[Dict[str, Any]] = None,
) -> str:
    """Prepend 5-block identity anchor section to image_prompt.

    Bypasses Stage 4 LLM creative drift by injecting authoritative anchors
    AFTER the LLM finishes — anchors are NOT visible to the LLM during prompt
    construction. The image generator (Seedream / NB2) sees this expanded
    prompt with anchors at the START, where model attention is highest.

    Idempotent: if image_prompt already contains IDENTITY_ANCHOR_MARKER, this
    is a no-op (returns the prompt unchanged) and logs a debug message. This
    means defense-in-depth injection at multiple call sites is safe.

    Edge-case handling (spec C.4):
      1. characters_in_scene=[]: skip CHARACTER ANCHORS block (env-only shots)
      2. props=[] or None: skip PROPS ANCHOR block
      3. location=None or empty: skip LOCATION ANCHOR block
      4. time_continuity=None or empty: skip TIME CONTINUITY ANCHOR block
      5. Multi-character (3-6): one anchor entry per character (no merging)
      6. anthropomorphic_animal: dispatch via extract_identity_anchors —
         fur_color/feather_color/scale_color → primary_color slot

    Args:
        image_prompt: Raw image_prompt as produced by Stage 4 LLM.
        characters_in_scene: List of full character schema dicts. Each must
            contain at minimum `id` and `character_type`; missing fields are
            tolerated (empty strings in anchor block).
        location: Stage 1 outline location entry (dict) OR None. Supports
            multiple field name variants via extract_location_anchors().
        style_preset: Style preset key (e.g., "realistic", "anime",
            "children_book"). Looked up in StyleEnforcer.STYLE_ENFORCEMENTS.
        props: List of prop dicts OR None. Props without signature_visual are
            skipped (cannot anchor visually).
        time_continuity: Stage 3 scene dict OR None. Reads time_of_day /
            lighting / weather / continuity_from_previous_scene.

    Returns:
        image_prompt with anchor block prepended. Unchanged if already
        injected (idempotent).
    """
    # Step 1: Idempotency — early return if already injected
    if not isinstance(image_prompt, str):
        # Defensive: coerce to empty string rather than raise
        logger.warning(
            "[IdentityAnchorInjector] image_prompt is not a string (%s), "
            "treating as empty",
            type(image_prompt).__name__,
        )
        image_prompt = ""

    if IDENTITY_ANCHOR_MARKER in image_prompt:
        logger.debug(
            "[IdentityAnchorInjector] image_prompt already contains "
            "IDENTITY_ANCHOR_MARKER, skipping (idempotent)"
        )
        return image_prompt

    # Step 2: Extract 5-dimensional anchors via helpers (tolerant of empties)
    char_anchors: List[Dict[str, Any]] = []
    if characters_in_scene and isinstance(characters_in_scene, list):
        for c in characters_in_scene:
            if isinstance(c, dict):
                char_anchors.append(extract_identity_anchors(c))

    style_anchor = extract_style_anchors(style_preset or "realistic")

    loc_anchor: Optional[Dict[str, Any]] = None
    if location:
        loc_anchor = extract_location_anchors(location)
        # If extract returned an empty placeholder, treat as missing
        if not (loc_anchor.get("location_id") or
                (loc_anchor.get("location_anchor") or {}).get("signature_visual")):
            loc_anchor = None

    props_anchor_list: List[Dict[str, Any]] = []
    if props:
        props_anchor_list = extract_props_anchors(props)

    time_anchor: Optional[Dict[str, Any]] = None
    if time_continuity:
        time_anchor = extract_time_continuity_anchors(time_continuity)
        # Treat empty extraction (no scene_id + no fields) as missing
        ta_inner = (time_anchor.get("time_continuity_anchor") or {})
        if not (time_anchor.get("scene_id") or
                ta_inner.get("time_of_day") or
                ta_inner.get("lighting") or
                ta_inner.get("weather")):
            time_anchor = None

    # Step 3: Render each anchor block (empty string if no content)
    character_block = _render_character_anchors_block(char_anchors)
    style_block = _render_style_anchor_block(style_anchor)
    location_block = _render_location_anchor_block(loc_anchor)
    props_block = _render_props_anchor_block(props_anchor_list)
    time_block = _render_time_anchor_block(time_anchor)

    # Step 4: Defensive — if ALL blocks empty (no characters + unknown style +
    # no location/props/time), skip injection entirely so we don't add a
    # noise header with no content. Style anchor with at least a display_name
    # is always present for known presets, so this is rare.
    if not (character_block or style_block or location_block or props_block or time_block):
        logger.debug(
            "[IdentityAnchorInjector] All 5 anchor blocks empty, skipping "
            "injection for image_prompt of length %d", len(image_prompt)
        )
        return image_prompt

    # Step 5: Format template + prepend to image_prompt
    anchor_section = IDENTITY_ANCHOR_INSTRUCTION_BLOCK_TEMPLATE.format(
        marker=IDENTITY_ANCHOR_MARKER,
        character_anchors_block=character_block,
        style_anchor_block=style_block,
        location_anchor_block=location_block,
        props_anchor_block=props_block,
        time_continuity_anchor_block=time_block,
    )

    logger.info(
        "[IdentityAnchorInjector] Injected anchors: chars=%d, style=%s, "
        "location=%s, props=%d, time=%s (prompt %d → %d chars)",
        len(char_anchors),
        "Y" if style_block else "N",
        "Y" if location_block else "N",
        len(props_anchor_list),
        "Y" if time_block else "N",
        len(image_prompt),
        len(anchor_section) + len(image_prompt),
    )

    return anchor_section + image_prompt
