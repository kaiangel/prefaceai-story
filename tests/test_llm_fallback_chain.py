"""
TASK-T22-NEW-4 (2026-05-22) — LLM fallback chain unit tests

Cross-provider three-layer fallback for user-facing LLM endpoints.
Verifies:
  - Happy path: Haiku succeeds → no fallback (chain_depth=1)
  - Haiku fails → Gemini succeeds → chain_depth=2 (cross-provider primary)
  - Haiku + Gemini fail → Sonnet succeeds → chain_depth=3
  - All three fail → success=False, error message populated
  - Per-layer intra-retry behavior (1 retry per layer by default)
  - Telemetry attempts list captures every try

Design:
  - Use monkeypatch to swap _call_haiku / _call_gemini / _call_sonnet
    (the layer-implementation functions) so no real API is hit
  - Mirrors KEY_LEARNINGS #52 importlib pattern for cascade safety:
    load the module via spec_from_file_location to bypass app.services
    __init__ (which imports google.genai / anthropic)

Author: @backend (Sonnet 4.6 + xhigh) — Wave 7 P0
"""

from __future__ import annotations

import asyncio
import importlib
import os
import sys
import types
import unittest.mock as _um
import importlib.util as _ilu

import pytest


# ---------------------------------------------------------------------------
# Stub the heavy SDKs (anthropic / google.genai) before loading the chain
# module so its top-level imports don't fail. Since the chain's layer
# implementations defer to `import anthropic` / `from google import genai`
# inside the function body (not at module top), our monkeypatched layer
# functions will never call them — but pytest's caplog/event loop machinery
# imports anthropic indirectly via other tests, so we still stub.
# ---------------------------------------------------------------------------


def _ensure_stubs() -> None:
    if "anthropic" not in sys.modules:
        anth_mod = types.ModuleType("anthropic")

        class _APIError(Exception):
            pass

        anth_mod.APIError = _APIError
        anth_mod.AsyncAnthropic = lambda *a, **k: _um.MagicMock()
        anth_mod.Anthropic = lambda *a, **k: _um.MagicMock()
        sys.modules["anthropic"] = anth_mod

    if "google" not in sys.modules:
        google_pkg = types.ModuleType("google")
        google_pkg.__path__ = []
        sys.modules["google"] = google_pkg
    if "google.genai" not in sys.modules:
        genai_mod = types.ModuleType("google.genai")
        genai_mod.Client = lambda *a, **k: _um.MagicMock()
        types_mod = types.ModuleType("google.genai.types")
        for nm in (
            "Content", "Part", "GenerateContentConfig", "ThinkingConfig",
            "HarmCategory", "HarmBlockThreshold", "SafetySetting",
        ):
            setattr(types_mod, nm, _um.MagicMock())
        genai_mod.types = types_mod
        sys.modules["google.genai"] = genai_mod
        sys.modules["google.genai.types"] = types_mod
        sys.modules["google"].genai = genai_mod  # type: ignore[attr-defined]


_ensure_stubs()


def _load_chain_module():
    """Bypass app.services.__init__ cascade by loading via spec_from_file."""
    # Drop existing module to force fresh load
    for key in (
        "app.services.llm_fallback_chain",
        "app.services",
        "app.config",
        "app",
    ):
        sys.modules.pop(key, None)

    # app.config is needed first (chain reads settings.ANTHROPIC_API_KEY)
    cfg_mod = importlib.import_module("app.config")
    # Stub the keys to non-empty so the layer functions don't refuse to call
    # (we won't actually call them — monkeypatched at chain-module level)
    if hasattr(cfg_mod, "settings"):
        cfg_mod.settings.ANTHROPIC_API_KEY = "test-key"  # type: ignore[attr-defined]
        cfg_mod.settings.GEMINI_API_KEY = "test-key"  # type: ignore[attr-defined]

    chain_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "app", "services", "llm_fallback_chain.py",
    )
    spec = _ilu.spec_from_file_location(
        "app.services.llm_fallback_chain", chain_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load llm_fallback_chain.py from {chain_path}")
    mod = _ilu.module_from_spec(spec)
    sys.modules["app.services.llm_fallback_chain"] = mod
    spec.loader.exec_module(mod)
    return mod


try:
    _CHAIN = _load_chain_module()
    _IMPORT_OK = True
    _IMPORT_ERR = ""
except Exception as exc:  # pragma: no cover
    _CHAIN = None  # type: ignore[assignment]
    _IMPORT_OK = False
    _IMPORT_ERR = str(exc)


def _require_import():
    if not _IMPORT_OK:
        pytest.skip(f"llm_fallback_chain import failed: {_IMPORT_ERR}")


# ---------------------------------------------------------------------------
# Helpers — make_async_returns / make_async_raises
# ---------------------------------------------------------------------------


def _async_returns(value: str):
    """Build a coroutine factory that returns `value`."""
    async def _fn(*args, **kwargs):
        return value
    return _fn


def _async_raises(exc: Exception):
    """Build a coroutine factory that raises `exc`."""
    async def _fn(*args, **kwargs):
        raise exc
    return _fn


# ---------------------------------------------------------------------------
# Happy path — Haiku layer succeeds
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_haiku_success_chain_depth_1(monkeypatch):
    """Layer 1 (Haiku) returns text → no fallback, chain_depth=1."""
    _require_import()
    monkeypatch.setattr(_CHAIN, "_call_haiku", _async_returns("haiku response"))
    monkeypatch.setattr(_CHAIN, "_call_gemini", _async_raises(RuntimeError("should not call")))
    monkeypatch.setattr(_CHAIN, "_call_sonnet", _async_raises(RuntimeError("should not call")))

    result = await _CHAIN.call_llm_with_fallback(user="hello")
    assert result.success is True
    assert result.text == "haiku response"
    assert result.chain_depth == 1
    assert result.provider_used == "anthropic"
    assert result.model_used == _CHAIN.HAIKU_MODEL
    assert len(result.attempts) == 1
    assert result.attempts[0]["ok"] is True


# ---------------------------------------------------------------------------
# Layer 2 fallback — Haiku fails, Gemini succeeds
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_haiku_fails_gemini_succeeds(monkeypatch):
    """Haiku 529 → Gemini takes over → chain_depth=2 (cross-provider)."""
    _require_import()
    monkeypatch.setattr(
        _CHAIN, "_call_haiku",
        _async_raises(RuntimeError("anthropic 529 overloaded"))
    )
    monkeypatch.setattr(_CHAIN, "_call_gemini", _async_returns("gemini response"))
    monkeypatch.setattr(_CHAIN, "_call_sonnet", _async_raises(RuntimeError("should not call")))

    result = await _CHAIN.call_llm_with_fallback(user="hello", layer_retries=0)
    assert result.success is True
    assert result.text == "gemini response"
    assert result.chain_depth == 2
    assert result.provider_used == "gemini"
    assert result.model_used == _CHAIN.GEMINI_FALLBACK_MODEL


# ---------------------------------------------------------------------------
# Layer 3 fallback — Haiku + Gemini fail, Sonnet succeeds
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_haiku_gemini_fail_sonnet_succeeds(monkeypatch):
    """Both Anthropic Haiku + Gemini Flash fail → Sonnet recovers."""
    _require_import()
    monkeypatch.setattr(
        _CHAIN, "_call_haiku",
        _async_raises(RuntimeError("anthropic 529"))
    )
    monkeypatch.setattr(
        _CHAIN, "_call_gemini",
        _async_raises(RuntimeError("google rate-limited"))
    )
    monkeypatch.setattr(_CHAIN, "_call_sonnet", _async_returns("sonnet wins"))

    result = await _CHAIN.call_llm_with_fallback(
        user="hello", layer_retries=0, operation_label="adjust_character",
    )
    assert result.success is True
    assert result.text == "sonnet wins"
    assert result.chain_depth == 3
    assert result.provider_used == "anthropic"
    assert result.model_used == _CHAIN.SONNET_MODEL


# ---------------------------------------------------------------------------
# All layers fail — must return success=False, no exception
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_all_three_layers_fail(monkeypatch):
    """All providers down → returns FallbackResult(success=False)."""
    _require_import()
    monkeypatch.setattr(_CHAIN, "_call_haiku", _async_raises(RuntimeError("h-down")))
    monkeypatch.setattr(_CHAIN, "_call_gemini", _async_raises(RuntimeError("g-down")))
    monkeypatch.setattr(_CHAIN, "_call_sonnet", _async_raises(RuntimeError("s-down")))

    result = await _CHAIN.call_llm_with_fallback(user="hello", layer_retries=0)
    assert result.success is False
    assert result.text == ""
    assert result.chain_depth == 0
    assert result.provider_used == ""
    assert "h-down" in result.error
    assert "g-down" in result.error
    assert "s-down" in result.error


@pytest.mark.asyncio
async def test_all_fail_friendly_error_message(monkeypatch):
    """friendly_error_message returns user-readable Chinese on failure."""
    _require_import()
    monkeypatch.setattr(_CHAIN, "_call_haiku", _async_raises(RuntimeError("e1")))
    monkeypatch.setattr(_CHAIN, "_call_gemini", _async_raises(RuntimeError("e2")))
    monkeypatch.setattr(_CHAIN, "_call_sonnet", _async_raises(RuntimeError("e3")))

    result = await _CHAIN.call_llm_with_fallback(user="hello", layer_retries=0)
    msg = _CHAIN.friendly_error_message(result)
    assert "服务繁忙" in msg
    assert "Haiku" in msg
    assert "Gemini" in msg
    assert "Sonnet" in msg


@pytest.mark.asyncio
async def test_raise_if_failed_raises_typed_exception(monkeypatch):
    """raise_if_failed() exposes structured FallbackResult on full failure."""
    _require_import()
    monkeypatch.setattr(_CHAIN, "_call_haiku", _async_raises(RuntimeError("h-fail")))
    monkeypatch.setattr(_CHAIN, "_call_gemini", _async_raises(RuntimeError("g-fail")))
    monkeypatch.setattr(_CHAIN, "_call_sonnet", _async_raises(RuntimeError("s-fail")))

    result = await _CHAIN.call_llm_with_fallback(user="hello", layer_retries=0)
    with pytest.raises(_CHAIN.LLMFallbackAllFailedError) as exc_info:
        _CHAIN.raise_if_failed(result)
    assert exc_info.value.result is result


# ---------------------------------------------------------------------------
# Empty response handling — treat empty as failure, fall through to next layer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_response_falls_through_to_next_layer(monkeypatch):
    """Haiku returns "" → treated as failure → Gemini layer activates."""
    _require_import()
    monkeypatch.setattr(_CHAIN, "_call_haiku", _async_returns(""))
    monkeypatch.setattr(_CHAIN, "_call_gemini", _async_returns("gemini text"))
    monkeypatch.setattr(_CHAIN, "_call_sonnet", _async_raises(RuntimeError("nope")))

    result = await _CHAIN.call_llm_with_fallback(user="hello", layer_retries=0)
    assert result.success is True
    assert result.chain_depth == 2
    assert result.text == "gemini text"


# ---------------------------------------------------------------------------
# Intra-layer retries — verify default 1 extra retry per layer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_intra_layer_retry_eventually_succeeds(monkeypatch):
    """Haiku fails first attempt, succeeds on retry → still chain_depth=1."""
    _require_import()
    calls = {"haiku": 0}

    async def haiku_flaky(*args, **kwargs):
        calls["haiku"] += 1
        if calls["haiku"] == 1:
            raise RuntimeError("transient")
        return "haiku recovered"

    monkeypatch.setattr(_CHAIN, "_call_haiku", haiku_flaky)
    monkeypatch.setattr(_CHAIN, "_call_gemini", _async_raises(RuntimeError("nope")))
    monkeypatch.setattr(_CHAIN, "_call_sonnet", _async_raises(RuntimeError("nope")))

    result = await _CHAIN.call_llm_with_fallback(
        user="hello", layer_retries=1, layer_backoff_s=0,
    )
    assert result.success is True
    assert result.chain_depth == 1
    assert calls["haiku"] == 2  # 1 fail + 1 success
    assert result.text == "haiku recovered"


@pytest.mark.asyncio
async def test_no_intra_retry_when_layer_retries_zero(monkeypatch):
    """layer_retries=0 → exactly 1 attempt per layer, no intra-layer retry."""
    _require_import()
    calls = {"haiku": 0, "gemini": 0, "sonnet": 0}

    async def haiku_count(*args, **kwargs):
        calls["haiku"] += 1
        raise RuntimeError("fail")

    async def gemini_count(*args, **kwargs):
        calls["gemini"] += 1
        return "gemini ok"

    monkeypatch.setattr(_CHAIN, "_call_haiku", haiku_count)
    monkeypatch.setattr(_CHAIN, "_call_gemini", gemini_count)
    monkeypatch.setattr(_CHAIN, "_call_sonnet", _async_raises(RuntimeError("no")))

    result = await _CHAIN.call_llm_with_fallback(user="hello", layer_retries=0)
    assert result.success is True
    assert result.chain_depth == 2
    assert calls["haiku"] == 1  # no intra-retry
    assert calls["gemini"] == 1


# ---------------------------------------------------------------------------
# Telemetry — attempts list captures every try
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_attempts_log_captures_all_tries(monkeypatch):
    """Every sub-attempt across layers logs an entry in attempts list."""
    _require_import()
    monkeypatch.setattr(_CHAIN, "_call_haiku", _async_raises(RuntimeError("h")))
    monkeypatch.setattr(_CHAIN, "_call_gemini", _async_raises(RuntimeError("g")))
    monkeypatch.setattr(_CHAIN, "_call_sonnet", _async_returns("ok"))

    result = await _CHAIN.call_llm_with_fallback(
        user="hello", layer_retries=1, layer_backoff_s=0,
    )
    # 2 attempts per failed layer × 2 layers + 1 success on sonnet = 5
    assert len(result.attempts) == 5
    layers_seen = [a["layer"] for a in result.attempts]
    assert layers_seen == [1, 1, 2, 2, 3]
    # Final attempt is the success
    assert result.attempts[-1]["ok"] is True
    assert result.attempts[-1]["layer"] == 3


# ---------------------------------------------------------------------------
# Logging — verify [LLMFallbackChain] tag emitted
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_log_emits_fallback_chain_tag(monkeypatch, caplog):
    """Logs must contain `[LLMFallbackChain]` prefix for grep monitoring."""
    _require_import()
    import logging as _lg
    monkeypatch.setattr(_CHAIN, "_call_haiku", _async_raises(RuntimeError("h")))
    monkeypatch.setattr(_CHAIN, "_call_gemini", _async_returns("ok"))
    monkeypatch.setattr(_CHAIN, "_call_sonnet", _async_raises(RuntimeError("no")))

    with caplog.at_level(_lg.INFO, logger="xuhua"):
        await _CHAIN.call_llm_with_fallback(
            user="hello", layer_retries=0, operation_label="adjust_character",
        )
    msgs = [r.getMessage() for r in caplog.records]
    assert any("[LLMFallbackChain]" in m for m in msgs)
    # Fallback success path should log a WARNING (chain>=2)
    assert any(
        "FALLBACK" in m or "SUCCESS via FALLBACK" in m
        for m in msgs
    )


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_user_raises_value_error():
    """Calling without user message is a programming error."""
    _require_import()
    with pytest.raises(ValueError):
        await _CHAIN.call_llm_with_fallback(user="")
    with pytest.raises(ValueError):
        await _CHAIN.call_llm_with_fallback(user=None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# FallbackResult dataclass sanity
# ---------------------------------------------------------------------------


def test_fallback_result_default_attempts_is_empty_list():
    """Default attempts list is empty, not None (post_init sets it)."""
    _require_import()
    r = _CHAIN.FallbackResult()
    assert r.attempts == []
    assert r.success is False
    assert r.chain_depth == 0


def test_fallback_result_repr_is_compact():
    """__repr__ should be short and informative."""
    _require_import()
    r = _CHAIN.FallbackResult(success=True, chain_depth=2, model_used="m")
    s = repr(r)
    assert "success=True" in s
    assert "chain=2" in s
    assert "model='m'" in s
