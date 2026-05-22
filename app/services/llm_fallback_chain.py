"""
TASK-T22-NEW-4 (2026-05-22) — LLM Fallback Chain

Cross-provider three-layer fallback for user-facing LLM endpoints that
currently use Haiku 4.5 (AdjustCharacter / Shot regenerate adjustment / Music
BGM). When Anthropic Haiku is overloaded (529) or fails, transparently
attempts Gemini 3.1 Flash (cross-provider primary backup) then Sonnet 4.6
(strongest same-provider fallback) before giving up.

Founder decision (5/22 13:35, KEY_LEARNINGS #55):
    Cross-provider > Cross-size.
    When Anthropic has region-wide overload, Sonnet (same provider) also
    fails. Gemini (different provider) is more likely to be available.

    Chain order:
        Layer 1: Haiku 4.5 (claude-haiku-4-5-20251001)
                 — fast + cheap, default for routine ops
        Layer 2: Gemini 3.1 Flash (gemini-3.1-flash-lite-preview)
                 — cross-provider primary backup
        Layer 3: Sonnet 4.6 (claude-sonnet-4-6)
                 — strongest fallback for quality-critical ops

E2E test22 evidence (5/22):
- 13:30 AdjustCharacter to Ah Hai → 500 (Haiku 529 overload)
- 13:56 Music BGM → no BGM (Haiku 3x retry all 529)
- Founder explicit: "这点要记下来 之后还是需要 fallback 的"

Pipeline Stage 1-5 already have T20-14 fallback. This module covers the
remaining user-facing endpoints.

Ben 5/13 协议: 0 API contract / schema / Alembic / frontend impact.

Author: @backend (Sonnet 4.6 + xhigh, Wave 7 P0)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger("xuhua")


# ═════════════════════════════════════════════════════════════
# Model identifiers (KEY_LEARNINGS #54 — always use exact IDs)
# ═════════════════════════════════════════════════════════════

HAIKU_MODEL = "claude-haiku-4-5-20251001"      # Anthropic (Layer 1)
GEMINI_FALLBACK_MODEL = "gemini-3.1-flash-lite-preview"  # Google (Layer 2)
SONNET_MODEL = "claude-sonnet-4-6"             # Anthropic (Layer 3, no date suffix per CLAUDE.md)


# Default retry config per layer (KEY_LEARNINGS #55 — fast fail to next layer
# rather than hammer one provider during region-wide outage)
DEFAULT_LAYER_RETRIES = 1   # one extra attempt per layer (2 total per provider)
DEFAULT_LAYER_BACKOFF_S = 2.0  # short backoff between intra-layer retries


# ═════════════════════════════════════════════════════════════
# Result dataclass — structured outcome
# ═════════════════════════════════════════════════════════════


@dataclass
class FallbackResult:
    """Outcome of call_llm_with_fallback.

    Attributes:
        text: Response text (empty when all layers fail).
        model_used: Model ID that produced the response (or last attempted).
        provider_used: "anthropic" | "gemini" | "" (empty on full failure).
        chain_depth: 1 (Haiku) / 2 (Gemini) / 3 (Sonnet) / 0 (no layer succeeded).
        success: True if any layer returned non-empty text.
        error: Exception message from the final failure (empty on success).
        attempts: list of dicts {layer, model, provider, ok, error} for telemetry.
    """
    text: str = ""
    model_used: str = ""
    provider_used: str = ""
    chain_depth: int = 0
    success: bool = False
    error: str = ""
    attempts: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.attempts is None:
            self.attempts = []

    def __repr__(self) -> str:
        return (
            f"FallbackResult(success={self.success}, "
            f"chain={self.chain_depth}, model={self.model_used!r}, "
            f"provider={self.provider_used!r}, attempts={len(self.attempts)})"
        )


class LLMFallbackAllFailedError(RuntimeError):
    """Raised when all three layers fail. Carries FallbackResult for telemetry."""

    def __init__(self, result: FallbackResult):
        self.result = result
        attempt_log = "; ".join(
            f"L{a.get('layer')}={a.get('provider')}:{a.get('model')} → "
            f"{'ok' if a.get('ok') else (a.get('error') or 'fail')}"
            for a in result.attempts
        )
        super().__init__(
            f"LLM fallback chain exhausted (all 3 layers failed). "
            f"Attempts: [{attempt_log}]"
        )


# ═════════════════════════════════════════════════════════════
# Layer implementations
# ═════════════════════════════════════════════════════════════


async def _call_haiku(
    system: Optional[str],
    user: str,
    max_tokens: int,
    extra_messages: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Layer 1 — Haiku 4.5 via AsyncAnthropic (async, non-blocking)."""
    import anthropic
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    create_kwargs: Dict[str, Any] = {
        "model": HAIKU_MODEL,
        "max_tokens": max_tokens,
    }
    if system is not None:
        create_kwargs["system"] = system
    if extra_messages:
        create_kwargs["messages"] = extra_messages
    else:
        create_kwargs["messages"] = [{"role": "user", "content": user}]

    resp = await client.messages.create(**create_kwargs)
    if not resp or not resp.content:
        return ""
    # Concat all text blocks (defensive — typically just one)
    parts = [b.text for b in resp.content if getattr(b, "type", "text") == "text"]
    return "".join(parts).strip()


async def _call_gemini(
    system: Optional[str],
    user: str,
    max_tokens: int,
) -> str:
    """Layer 2 — Gemini 3.1 Flash via google.genai (cross-provider backup).

    Translates system+user into Gemini's input format. Gemini doesn't have
    a "system" role in the same way; we prepend system as preamble.
    """
    from google import genai
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not configured")

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    full_prompt = user
    if system:
        full_prompt = f"{system}\n\n---\n\n{user}"

    # google.genai client uses asyncio via .aio sub-client (per SDK convention)
    # Fall back to sync wrapped in to_thread if .aio not available.
    try:
        # Preferred: native async path
        resp = await client.aio.models.generate_content(
            model=GEMINI_FALLBACK_MODEL,
            contents=full_prompt,
        )
    except AttributeError:
        # Older SDK fallback — run sync call in thread to avoid event-loop block
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model=GEMINI_FALLBACK_MODEL,
                contents=full_prompt,
            ),
        )

    if not resp:
        return ""
    text = getattr(resp, "text", "") or ""
    return text.strip()


async def _call_sonnet(
    system: Optional[str],
    user: str,
    max_tokens: int,
    extra_messages: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Layer 3 — Sonnet 4.6 via AsyncAnthropic (highest quality fallback)."""
    import anthropic
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    create_kwargs: Dict[str, Any] = {
        "model": SONNET_MODEL,
        "max_tokens": max_tokens,
    }
    if system is not None:
        create_kwargs["system"] = system
    if extra_messages:
        create_kwargs["messages"] = extra_messages
    else:
        create_kwargs["messages"] = [{"role": "user", "content": user}]

    resp = await client.messages.create(**create_kwargs)
    if not resp or not resp.content:
        return ""
    parts = [b.text for b in resp.content if getattr(b, "type", "text") == "text"]
    return "".join(parts).strip()


# ═════════════════════════════════════════════════════════════
# Public API — call_llm_with_fallback
# ═════════════════════════════════════════════════════════════


async def call_llm_with_fallback(
    user: str,
    system: Optional[str] = None,
    max_tokens: int = 2000,
    extra_messages: Optional[List[Dict[str, Any]]] = None,
    operation_label: str = "user_op",
    layer_retries: int = DEFAULT_LAYER_RETRIES,
    layer_backoff_s: float = DEFAULT_LAYER_BACKOFF_S,
) -> FallbackResult:
    """Call LLM with Haiku → Gemini Flash → Sonnet three-layer fallback.

    Cross-provider order (KEY_LEARNINGS #55 Founder decision):
        Anthropic region-wide overload → Sonnet (same provider) also fails →
        Gemini (different provider) more likely available → try Gemini before
        escalating to Sonnet.

    Args:
        user: User message text (required).
        system: Optional system prompt. Anthropic uses `system` arg; for Gemini
            it is prepended as preamble (no native system role).
        max_tokens: Max response tokens (passed to Anthropic; ignored by
            Gemini SDK which uses its own config — informational only).
        extra_messages: Optional pre-built messages list for Anthropic (used
            when caller has multi-turn history). When provided, replaces the
            single-turn user message. Gemini layer ignores this (uses `user`).
        operation_label: Short tag for telemetry logs ("adjust_character",
            "shot_adjustment", "music_bgm" etc.).
        layer_retries: Extra retries per layer before moving to next layer
            (default 1 = total 2 attempts per provider).
        layer_backoff_s: Backoff (seconds) between intra-layer retries.

    Returns:
        FallbackResult dataclass. Caller should check `.success`. If False,
        `.error` holds the final exception message.

    Raises:
        Never raises directly — always returns FallbackResult with
        success=False on full chain failure. Callers wanting exception
        semantics can use `raise_if_failed(result)` helper or check
        `.success` explicitly.

    Telemetry:
        Emits one INFO log per attempt with `[LLMFallbackChain]` prefix so
        ops can grep for fallback rate metrics (KEY_LEARNINGS #55 #6).
    """
    if not user or not isinstance(user, str):
        raise ValueError("call_llm_with_fallback: `user` must be non-empty string")

    layers = [
        ("haiku", "anthropic", HAIKU_MODEL,
            lambda: _call_haiku(system, user, max_tokens, extra_messages)),
        ("gemini", "gemini", GEMINI_FALLBACK_MODEL,
            lambda: _call_gemini(system, user, max_tokens)),
        ("sonnet", "anthropic", SONNET_MODEL,
            lambda: _call_sonnet(system, user, max_tokens, extra_messages)),
    ]

    result = FallbackResult()
    last_error_per_layer: List[str] = []

    for layer_idx, (layer_name, provider, model, fn) in enumerate(layers, start=1):
        layer_attempts = layer_retries + 1
        attempt_error = ""
        for sub_attempt in range(1, layer_attempts + 1):
            try:
                logger.info(
                    "[LLMFallbackChain] op=%s layer=%d/%d (%s:%s) sub=%d/%d attempt",
                    operation_label, layer_idx, len(layers),
                    provider, layer_name, sub_attempt, layer_attempts,
                )
                text = await fn()
                if text:
                    result.text = text
                    result.model_used = model
                    result.provider_used = provider
                    result.chain_depth = layer_idx
                    result.success = True
                    result.attempts.append({
                        "layer": layer_idx,
                        "model": model,
                        "provider": provider,
                        "sub_attempt": sub_attempt,
                        "ok": True,
                        "error": "",
                    })
                    if layer_idx == 1:
                        logger.info(
                            "[LLMFallbackChain] op=%s → %s:%s SUCCESS (chain=1)",
                            operation_label, provider, layer_name,
                        )
                    else:
                        # Notable: secondary layer succeeded — log loudly for monitoring
                        prior_summary = " ".join(
                            f"L{a['layer']}={a['provider']}={'ok' if a['ok'] else 'fail'}"
                            for a in result.attempts
                        )
                        logger.warning(
                            "[LLMFallbackChain] op=%s → %s:%s SUCCESS via FALLBACK "
                            "(chain=%d). Prior attempts: %s",
                            operation_label, provider, layer_name,
                            layer_idx, prior_summary,
                        )
                    return result
                else:
                    attempt_error = "empty_response"
                    result.attempts.append({
                        "layer": layer_idx,
                        "model": model,
                        "provider": provider,
                        "sub_attempt": sub_attempt,
                        "ok": False,
                        "error": attempt_error,
                    })
                    logger.warning(
                        "[LLMFallbackChain] op=%s layer=%d (%s:%s) sub=%d → empty response",
                        operation_label, layer_idx, provider, layer_name, sub_attempt,
                    )
            except Exception as exc:
                attempt_error = f"{type(exc).__name__}: {exc}"
                result.attempts.append({
                    "layer": layer_idx,
                    "model": model,
                    "provider": provider,
                    "sub_attempt": sub_attempt,
                    "ok": False,
                    "error": attempt_error,
                })
                logger.warning(
                    "[LLMFallbackChain] op=%s layer=%d (%s:%s) sub=%d failed: %s",
                    operation_label, layer_idx, provider, layer_name,
                    sub_attempt, attempt_error,
                )
                # Intra-layer backoff before retry (only if more attempts remain)
                if sub_attempt < layer_attempts:
                    await asyncio.sleep(layer_backoff_s)
        # Layer exhausted; record final error then escalate
        last_error_per_layer.append(f"L{layer_idx}({provider}:{layer_name})={attempt_error}")
        logger.warning(
            "[LLMFallbackChain] op=%s layer=%d (%s:%s) EXHAUSTED, escalating to next layer",
            operation_label, layer_idx, provider, layer_name,
        )

    # All three layers failed
    result.error = "; ".join(last_error_per_layer)
    logger.error(
        "[LLMFallbackChain] op=%s ALL 3 LAYERS FAILED. Details: %s",
        operation_label, result.error,
    )
    return result


def raise_if_failed(result: FallbackResult) -> None:
    """Raise LLMFallbackAllFailedError when result.success is False.

    Use when caller wants exception-based control flow instead of checking
    `result.success`.
    """
    if not result.success:
        raise LLMFallbackAllFailedError(result)


def friendly_error_message(result: FallbackResult) -> str:
    """User-friendly error message for frontend toast.

    Returns Chinese message suitable for frontend display when all 3
    layers fail (Anthropic+Gemini both unreachable — rare).
    """
    if result.success:
        return ""
    return (
        "服务繁忙，自动切换备用模型仍失败，请稍后再试。"
        f"(尝试模型: Haiku → Gemini → Sonnet, 共 {len(result.attempts)} 次)"
    )
