"""
Wave 9 / DEC-049 (2026-05-22) — Portrait Layer 1 注入跨风格回归测试

Coverage:
  - 4 彩色风格 (manga / children_book / cyberpunk / ink) portrait prompt
    必含 Layer 1 IDENTITY_ANCHOR_MARKER + character physical color tokens
  - 1 黑白风格 (_bw 后缀) portrait prompt 必 SKIP Layer 1 (无 marker)
  - StyleEnforcer.is_bw_style() helper 行为单测 (4 case)
  - 风险点: 跨题材 80+ style regression — 任何 style 的 portrait Layer 1 注入
    不能引入空 anchor block / 字符串拼接异常 / silent fail
  - 测试不调真生图 API (零成本, 仅验证 prompt 构造层)

Design:
  - Mirror tests/test_identity_anchor_injector.py pattern:
    spec_from_file_location + sys.modules canonical registration
    → 绕过 app/services/__init__.py story_generator → google.genai cascade
  - 不 mock inject_identity_anchors — 真调用真验证 anchor block 出现在 portrait prompt
  - StyleEnforcer.is_bw_style() 独立测试 — 验证扩展位语义

Author: @ai-ml (Opus 4.7 + max thinking)
Owner: TASK-T22-NEW-10 / DEC-049 Layer 1 portrait path wire
"""
from __future__ import annotations

import importlib
import importlib.util as _ilu
import os as _os
import sys

import pytest


# ---------------------------------------------------------------------------
# Defensive isolation import — mirror test_identity_anchor_injector pattern
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


def _clean_and_import_portrait_deps():
    """Load reference_image_manager + style_enforcer + identity_anchor_injector
    via spec_from_file_location, bypassing both:
      - app/services/__init__.py story_generator cascade → google.genai ImportError
      - app/models/__init__.py SQLAlchemy + aiomysql cascade

    Strategy: install minimal *package stub* for `app.models` (so submodule
    imports `from app.models.character_types import X` don't trigger
    app.models.__init__ side effects), then load each needed module via
    spec_from_file_location with canonical name + sys.modules registration.

    Returns:
        (rim_module, style_enforcer_module, injector_module, anchor_module, cpb_module)
    """
    import types as _types

    # Clear stub modules first
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
        "app.services.reference_image_manager",
        "app.services.character_prompt_builder",
        "app.services.story_generator",
        "app.services",
        "app.prompts.identity_anchor_prompts",
        "app.prompts",
        "app.models.character_types",
        "app.models.style_config",
        "app.models",
        "app",
    ):
        sys.modules.pop(key, None)

    project_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))

    # Install minimal `app` package stub (path-only, no side effects)
    app_pkg = _types.ModuleType("app")
    app_pkg.__path__ = [_os.path.join(project_root, "app")]  # type: ignore[attr-defined]
    sys.modules["app"] = app_pkg

    # Install minimal `app.models` package stub (path-only, no side effects)
    # This is the key trick: empty __init__ avoids SQLAlchemy + aiomysql cascade
    # while submodules can still be located via the __path__ attribute
    models_pkg = _types.ModuleType("app.models")
    models_pkg.__path__ = [_os.path.join(project_root, "app", "models")]  # type: ignore[attr-defined]
    sys.modules["app.models"] = models_pkg

    # Install minimal `app.services` package stub
    services_pkg = _types.ModuleType("app.services")
    services_pkg.__path__ = [_os.path.join(project_root, "app", "services")]  # type: ignore[attr-defined]
    sys.modules["app.services"] = services_pkg

    # Install minimal `app.prompts` package stub (let real identity_anchor_prompts
    # load via standard mechanism since it has no problematic side effects)
    prompts_pkg = _types.ModuleType("app.prompts")
    prompts_pkg.__path__ = [_os.path.join(project_root, "app", "prompts")]  # type: ignore[attr-defined]
    sys.modules["app.prompts"] = prompts_pkg

    services_root = _os.path.join(project_root, "app", "services")
    models_root = _os.path.join(project_root, "app", "models")
    prompts_root = _os.path.join(project_root, "app", "prompts")

    def _load(canonical_name: str, abs_path: str):
        spec = _ilu.spec_from_file_location(canonical_name, abs_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load {canonical_name} from {abs_path}")
        module = _ilu.module_from_spec(spec)
        sys.modules[canonical_name] = module
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        return module

    # Load deps in dependency order
    _load("app.models.character_types",
          _os.path.join(models_root, "character_types.py"))
    _load("app.models.style_config",
          _os.path.join(models_root, "style_config.py"))
    anchor_mod = _load("app.prompts.identity_anchor_prompts",
                       _os.path.join(prompts_root, "identity_anchor_prompts.py"))
    se_mod = _load("app.services.style_enforcer",
                   _os.path.join(services_root, "style_enforcer.py"))
    inj_mod = _load("app.services.identity_anchor_injector",
                    _os.path.join(services_root, "identity_anchor_injector.py"))
    cpb_mod = _load("app.services.character_prompt_builder",
                    _os.path.join(services_root, "character_prompt_builder.py"))
    rim_mod = _load("app.services.reference_image_manager",
                    _os.path.join(services_root, "reference_image_manager.py"))
    return rim_mod, se_mod, inj_mod, anchor_mod, cpb_mod


try:
    _RIM, _SE, _INJ, _ANCHOR, _CPB = _clean_and_import_portrait_deps()
    _IMPORT_OK = True
    _IMPORT_ERR = ""
except Exception as exc:  # pragma: no cover
    _RIM = None  # type: ignore[assignment]
    _SE = None  # type: ignore[assignment]
    _INJ = None  # type: ignore[assignment]
    _ANCHOR = None  # type: ignore[assignment]
    _CPB = None  # type: ignore[assignment]
    _IMPORT_OK = False
    _IMPORT_ERR = f"{type(exc).__name__}: {exc}"


def _require_import():
    if not _IMPORT_OK:
        pytest.skip(f"portrait deps import failed: {_IMPORT_ERR}")


# ---------------------------------------------------------------------------
# Mock fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_character() -> dict:
    """A canonical color-rich human character — designed so the Layer 1
    anchor block emits distinctive tokens we can grep for.
    """
    return {
        "id": "char_001",
        "name": "测试角色",
        "name_en": "Test Character",
        "character_type": "human",
        "gender": "female",
        "age_appearance": "young_adult",
        "physical": {
            "hair_color": "deep teal-aqua gradient with seafoam highlights",
            "hair_style": "long flowing waves past the shoulders",
            "face_shape": "oval",
            "skin_tone": "fair with luminous aqua sheen",
            "eye_color": "translucent ocean blue",
            "eye_shape": "almond",
            "distinctive_marks": [
                "iridescent scale-shimmer along collarbones",
            ],
        },
        "clothing": {
            "top": "white off-shoulder silk blouse with flowing hem",
            "bottom": "long ivory skirt",
            "accessories": ["small pearl-tipped hairpin"],
            "style": "ethereal coastal",
        },
    }


@pytest.fixture
def make_project_style():
    """Factory for ProjectStyleConfig-compatible dummy with style_preset."""
    class _DummyStyle:
        def __init__(self, preset: str):
            self.style_preset = preset
    return _DummyStyle


# ---------------------------------------------------------------------------
# Section 1: 4 彩色风格 — portrait prompt 必含 Layer 1 anchor
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("style", ["manga", "children_book", "cyberpunk", "ink"])
def test_portrait_includes_layer1_for_color_styles(
    sample_character, make_project_style, style
):
    """4 个彩色风格的 portrait prompt 必含 IDENTITY_ANCHOR_MARKER + 主色 token"""
    _require_import()
    rim = _RIM.ReferenceImageManager()
    project_style = make_project_style(style)
    char_type = rim._get_character_type(sample_character)
    prompt = rim._build_portrait_prompt(
        sample_character, char_type, project_style
    )

    # Layer 1 marker must appear (positively asserts injection happened)
    assert _ANCHOR.IDENTITY_ANCHOR_MARKER in prompt, (
        f"Style {style!r} portrait MISSING Layer 1 marker — "
        f"_build_portrait_prompt did not inject. prompt[:300]={prompt[:300]!r}"
    )
    # Marker should appear near the start (high attention zone)
    marker_pos = prompt.find(_ANCHOR.IDENTITY_ANCHOR_MARKER)
    assert 0 <= marker_pos < 3000, (
        f"Style {style!r} marker at position {marker_pos} — "
        f"should be in the leading section, not buried mid-prompt"
    )

    # Critical color anchors must appear in the injected prompt — verifies
    # extract_identity_anchors → _render_character_anchors_block produced
    # meaningful content (not empty placeholder)
    assert "teal-aqua" in prompt.lower(), (
        f"Style {style!r}: hair_color token 'teal-aqua' missing from injected prompt"
    )
    # CHARACTER ANCHORS section header must be present
    assert "CHARACTER ANCHORS" in prompt, (
        f"Style {style!r}: CHARACTER ANCHORS section missing"
    )


# ---------------------------------------------------------------------------
# Section 2: 黑白风格 — portrait prompt 必 SKIP Layer 1
# ---------------------------------------------------------------------------


def test_portrait_skips_layer1_for_bw_style(sample_character, make_project_style):
    """_bw 后缀风格 → portrait prompt 不含 Layer 1 marker (Wave 9 扩展位语义)"""
    _require_import()
    rim = _RIM.ReferenceImageManager()
    project_style = make_project_style("manga_bw")
    char_type = rim._get_character_type(sample_character)
    prompt = rim._build_portrait_prompt(
        sample_character, char_type, project_style
    )

    assert _ANCHOR.IDENTITY_ANCHOR_MARKER not in prompt, (
        f"style 'manga_bw' (BW suffix) should SKIP Layer 1 injection. "
        f"prompt[:300]={prompt[:300]!r}"
    )
    # Should NOT have CHARACTER ANCHORS section
    assert "CHARACTER ANCHORS" not in prompt, (
        "BW style portrait must not emit CHARACTER ANCHORS section"
    )


def test_portrait_skips_layer1_for_explicit_bw_set_member(
    sample_character, make_project_style
):
    """通过 BW_STYLES set 显式注册的风格也 skip"""
    _require_import()
    # Inject temporarily (no _bw suffix → only set membership triggers skip)
    StyleEnforcer = _SE.StyleEnforcer
    StyleEnforcer.BW_STYLES.add("noir_film")
    try:
        rim = _RIM.ReferenceImageManager()
        project_style = make_project_style("noir_film")
        char_type = rim._get_character_type(sample_character)
        prompt = rim._build_portrait_prompt(
            sample_character, char_type, project_style
        )
        assert _ANCHOR.IDENTITY_ANCHOR_MARKER not in prompt, (
            "Explicit BW_STYLES member 'noir_film' must skip Layer 1"
        )
    finally:
        StyleEnforcer.BW_STYLES.discard("noir_film")


# ---------------------------------------------------------------------------
# Section 3: StyleEnforcer.is_bw_style() helper unit tests
# ---------------------------------------------------------------------------


def test_is_bw_style_helper_behavior():
    """StyleEnforcer.is_bw_style() returns True only for explicit BW_STYLES
    members OR `_bw` suffix; False for all current 80+ color styles."""
    _require_import()
    StyleEnforcer = _SE.StyleEnforcer

    # _bw suffix triggers skip
    assert StyleEnforcer.is_bw_style("manga_bw") is True
    assert StyleEnforcer.is_bw_style("ink_pure_bw") is True
    assert StyleEnforcer.is_bw_style("anything_bw") is True

    # Current set is empty → no other style triggers skip (manga / realistic / etc all colored)
    assert StyleEnforcer.is_bw_style("manga") is False
    assert StyleEnforcer.is_bw_style("realistic") is False
    assert StyleEnforcer.is_bw_style("ink") is False  # 水墨 mandatory 含彩色描述
    assert StyleEnforcer.is_bw_style("cyberpunk") is False
    assert StyleEnforcer.is_bw_style("children_book") is False
    assert StyleEnforcer.is_bw_style("korean_webtoon") is False
    assert StyleEnforcer.is_bw_style("anime") is False

    # Non-string defensive — should not raise
    assert StyleEnforcer.is_bw_style(None) is False  # type: ignore[arg-type]
    assert StyleEnforcer.is_bw_style(123) is False  # type: ignore[arg-type]
    assert StyleEnforcer.is_bw_style("") is False
