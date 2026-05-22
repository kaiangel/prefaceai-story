"""
DEC-048 Layer 1 (2026-05-22) — PromptValidator

Pre-generation guard that greps the image_prompt for character schema
keywords (hair_color / skin_tone / distinctive_marks / clothing_core). If any
critical keyword is missing, auto_correct re-injects the full anchor block
via identity_anchor_injector. Forms a cross-stage validation pair with
ShotValidator (post-generation image-vs-prompt check):

    Stage 4 LLM → image_prompt
                       ↓
              PromptValidator (pre-gen, grep schema keywords)
                       ↓ (auto_correct re-injects if missing)
              Image generator (Seedream / NB2)
                       ↓
              ShotValidator (post-gen, vision LLM check)

Design principles (from AI-ML M1 spec, context-for-others.md D.1-D.4):
  1. Cross-stage validation — catches Stage 4 LLM drift BEFORE wasting an
     image generation API call (Seedream $0.030/img × N retries adds up)
  2. Idempotent auto-correct — checks IDENTITY_ANCHOR_MARKER, never double-
     injects (prevents block duplication)
  3. Severity-aware — hair_color / skin_tone are CRITICAL (100% MUST), marks
     and clothing are WARNING (90% SHOULD, may be hidden in wide shots)
  4. Multi-character — validates each character independently, returns
     list of missing entries with char_id / field / expected / tokens

Companion module:
  - app/services/identity_anchor_injector.py provides the actual injection

Author: @backend (Sonnet 4.6 + xhigh)
Owner: TASK-T22-NEW-3 / DEC-048 Layer 1 Backend implementation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.prompts.identity_anchor_prompts import (
    IDENTITY_ANCHOR_MARKER,
    extract_distinctive_tokens,
    extract_identity_anchors,
)
from app.services.identity_anchor_injector import inject_identity_anchors

logger = logging.getLogger("xuhua")


# ═════════════════════════════════════════════════════════════
# ValidationResult — structured output of validate_prompt_vs_schema
# ═════════════════════════════════════════════════════════════


@dataclass
class ValidationResult:
    """Outcome of validate_prompt_vs_schema.

    Attributes:
        passed: True when all critical anchors found in prompt.
        missing_anchors: list of dicts describing each missed field. Each entry:
            {
              "char_id": str,
              "field": str (e.g. "hair_color" / "skin_tone"),
              "expected": str (raw schema value),
              "tokens": list[str] (distinctive tokens we grepped for),
              "severity": str ("critical" | "warning"),
            }
        severity: overall severity:
            - "critical" if any critical (hair/skin) missed
            - "warning" if only marks/clothing missed
            - "info" if all passed
    """
    passed: bool
    missing_anchors: List[Dict[str, Any]] = field(default_factory=list)
    severity: str = "info"

    def __repr__(self) -> str:
        return (
            f"ValidationResult(passed={self.passed}, "
            f"missing={len(self.missing_anchors)}, severity={self.severity!r})"
        )


# ═════════════════════════════════════════════════════════════
# PromptValidator
# ═════════════════════════════════════════════════════════════


class PromptValidator:
    """Pre-generation validator for identity anchor presence in image_prompt.

    Greps prompt for distinctive tokens extracted from each character's
    schema (hair_color, skin_tone, distinctive_marks, clothing_core.top).
    auto_correct re-injects the full anchor block when critical keywords are
    missing — idempotent (won't double-inject if marker already present).

    Usage:
        validator = PromptValidator()
        result = validator.validate_prompt_vs_schema(image_prompt, chars)
        if not result.passed:
            image_prompt = validator.auto_correct(
                image_prompt, result, chars,
                location=loc, style_preset="anime",
                props=props_list, time_continuity=scene_data,
            )
    """

    # Severity classification per AI-ML M1 spec D.2:
    # - hair_color / primary_color: 100% MUST (critical)
    # - skin_tone: 100% MUST (critical, humanoid only)
    # - distinctive_marks: 90% SHOULD (warning, wide shots may hide)
    # - clothing_core.top: 90% SHOULD (warning)
    _CRITICAL_FIELDS = ("primary_color", "skin_tone")
    _WARNING_FIELDS = ("distinctive_marks", "clothing_top")

    def validate_prompt_vs_schema(
        self,
        image_prompt: str,
        characters_in_scene: List[Dict[str, Any]],
    ) -> ValidationResult:
        """Validate that image_prompt contains schema keywords for each char.

        For each character:
          1. Extract anchors via extract_identity_anchors()
          2. For each anchorable field, extract distinctive tokens via
             extract_distinctive_tokens()
          3. Grep prompt (lowercase, substring) — pass if ANY token matches
          4. Record misses in result with severity tag

        Args:
            image_prompt: Final prompt string about to go to image generator.
            characters_in_scene: List of full character schema dicts.

        Returns:
            ValidationResult with passed/missing_anchors/severity.
        """
        if not isinstance(image_prompt, str) or not image_prompt:
            # Empty / invalid prompt → "passed" trivially (nothing to check
            # against; upstream should have caught empty prompts)
            return ValidationResult(passed=True, missing_anchors=[], severity="info")

        if not characters_in_scene or not isinstance(characters_in_scene, list):
            # No characters to validate → pure environmental shot, pass
            return ValidationResult(passed=True, missing_anchors=[], severity="info")

        prompt_lower = image_prompt.lower()
        missing: List[Dict[str, Any]] = []

        for char in characters_in_scene:
            if not isinstance(char, dict):
                continue

            anchors = extract_identity_anchors(char)
            char_id = anchors.get("character_id") or ""
            ia = anchors.get("identity_anchor") or {}
            if not isinstance(ia, dict):
                continue

            # ---- CRITICAL: primary identity color (hair / fur / feather...)
            # Prefer primary_color (dispatch-aware) over hair_color, but fall
            # through to hair_color for humanoid types.
            hair_text = ia.get("primary_color") or ia.get("hair_color") or ""
            hair_field = ia.get("primary_color_field") or "hair_color"
            if hair_text:
                tokens = extract_distinctive_tokens(hair_text, n=3)
                if tokens and not any(t.lower() in prompt_lower for t in tokens):
                    missing.append({
                        "char_id": char_id,
                        "field": hair_field,
                        "expected": hair_text,
                        "tokens": tokens,
                        "severity": "critical",
                    })

            # ---- CRITICAL: skin_tone (humanoid only; empty for pure animal)
            skin_text = ia.get("skin_tone") or ""
            if skin_text:
                tokens = extract_distinctive_tokens(skin_text, n=3)
                if tokens and not any(t.lower() in prompt_lower for t in tokens):
                    missing.append({
                        "char_id": char_id,
                        "field": "skin_tone",
                        "expected": skin_text,
                        "tokens": tokens,
                        "severity": "critical",
                    })

            # ---- WARNING: distinctive_marks (any mark, any token)
            # marks are long descriptive phrases — extract up to 4 tokens
            # per mark to widen the keyword net (the signature word may not
            # be in the top-2). M1 spec D.2: "any marks, any token" → pass.
            marks = ia.get("distinctive_marks_short") or []
            if marks and isinstance(marks, list):
                # Collect all tokens across all marks, dedup
                all_tokens: List[str] = []
                seen: set = set()
                for mark in marks:
                    if not mark:
                        continue
                    for t in extract_distinctive_tokens(mark, n=4):
                        if t not in seen:
                            seen.add(t)
                            all_tokens.append(t)
                if all_tokens and not any(t.lower() in prompt_lower for t in all_tokens):
                    missing.append({
                        "char_id": char_id,
                        "field": "distinctive_marks",
                        "expected": "; ".join(marks),
                        "tokens": all_tokens,
                        "severity": "warning",
                    })

            # ---- WARNING: clothing_core.top
            clothing = ia.get("clothing_core") or {}
            if isinstance(clothing, dict):
                top_text = clothing.get("top") or ""
                if top_text:
                    tokens = extract_distinctive_tokens(top_text, n=3)
                    if tokens and not any(t.lower() in prompt_lower for t in tokens):
                        missing.append({
                            "char_id": char_id,
                            "field": "clothing_top",
                            "expected": top_text,
                            "tokens": tokens,
                            "severity": "warning",
                        })

        # Compute overall severity
        has_critical = any(m.get("severity") == "critical" for m in missing)
        has_warning = any(m.get("severity") == "warning" for m in missing)
        if has_critical:
            severity = "critical"
            passed = False
        elif has_warning:
            severity = "warning"
            # Warnings DO NOT fail the gate (auto_correct still runs on
            # critical only). M1 spec D.2 — wide shots may legitimately hide
            # marks; pass with severity=warning.
            passed = True
        else:
            severity = "info"
            passed = True

        return ValidationResult(
            passed=passed,
            missing_anchors=missing,
            severity=severity,
        )

    def auto_correct(
        self,
        image_prompt: str,
        validation_result: ValidationResult,
        characters_in_scene: List[Dict[str, Any]],
        location: Optional[Dict[str, Any]] = None,
        style_preset: str = "realistic",
        props: Optional[List[Dict[str, Any]]] = None,
        time_continuity: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Auto-correct missing anchors via re-injection (idempotent).

        Algorithm (M1 spec D.3):
          1. If image_prompt already contains IDENTITY_ANCHOR_MARKER, the
             injector ran but the LLM-generated tail still drifted. Log the
             miss for manual review but DO NOT double-inject. Return as-is.
          2. Otherwise, call inject_identity_anchors() with full context so
             the prompt gets a complete 5-block anchor section prepended.

        Args:
            image_prompt: The prompt that failed validation.
            validation_result: Result from validate_prompt_vs_schema().
            characters_in_scene: Same characters list used in validation.
            location: Optional, passed through to inject_identity_anchors.
            style_preset: Optional, passed through.
            props: Optional, passed through.
            time_continuity: Optional, passed through.

        Returns:
            Corrected image_prompt (with anchor block prepended) OR the
            original prompt unchanged if marker already present (logged).
        """
        if validation_result.passed:
            # Nothing to correct — return as-is
            return image_prompt

        # Idempotency: marker already present → injector ran, but LLM tail
        # drifted. Re-injecting would just duplicate the anchor block above
        # the same drifting tail. Log for PM review (KEY_LEARNINGS #47/#48
        # defense — surface anomalies, don't silently re-inject).
        if isinstance(image_prompt, str) and IDENTITY_ANCHOR_MARKER in image_prompt:
            logger.warning(
                "[PromptValidator] image_prompt already contains "
                "IDENTITY_ANCHOR_MARKER but %d anchor(s) still missing — "
                "possible LLM tail drift or injector dropped a block. "
                "Missing: %s. Manual review recommended.",
                len(validation_result.missing_anchors),
                self._summarize_missing(validation_result.missing_anchors),
            )
            return image_prompt

        # Marker absent → injector hasn't run yet. Run it now with full
        # context. The injector itself is idempotent so double-protection is
        # safe at all call sites.
        logger.warning(
            "[PromptValidator] image_prompt missing %d anchor(s), "
            "auto-correcting via inject_identity_anchors. Missing: %s",
            len(validation_result.missing_anchors),
            self._summarize_missing(validation_result.missing_anchors),
        )

        return inject_identity_anchors(
            image_prompt=image_prompt,
            characters_in_scene=characters_in_scene,
            location=location,
            style_preset=style_preset,
            props=props,
            time_continuity=time_continuity,
        )

    @staticmethod
    def _summarize_missing(missing: List[Dict[str, Any]]) -> str:
        """Build a compact log summary of missing anchors."""
        if not missing:
            return "<none>"
        parts: List[str] = []
        for m in missing[:5]:  # cap at 5 to keep log lines readable
            char_id = m.get("char_id") or "?"
            field = m.get("field") or "?"
            tokens = m.get("tokens") or []
            sev = m.get("severity") or "?"
            tok_str = "/".join(tokens[:3]) if tokens else "?"
            parts.append(f"{char_id}.{field}[{sev}]={tok_str}")
        if len(missing) > 5:
            parts.append(f"+{len(missing) - 5} more")
        return ", ".join(parts)
