"""
TASK-WAVE-9-TESTER-INDEPENDENT-BASELINE (2026-05-22) — Tester 独立第二意见
跨题材 × 跨 character_type × 跨 location Layer 1 通用性验证

Coverage:
  T2: 5 风格 × 5 character_type 跨题材矩阵 (25 case)
      - portrait + fullbody 双路均含 IDENTITY_ANCHOR_MARKER
      - _bw 后缀 skip (不注入) — 每路各一组独立验证
      - BW_STYLES 显式注册 skip
  T3: log marker 实际触发 verify
      - portrait path: "Layer 1 injected for portrait" log
      - fullbody path: "Layer 1 injected for fullbody" log
      - bw path: "Layer 1 SKIPPED (bw style)" log
  T4: 边缘 case (Tester 独立设计)
      - character 没 id 但有 name_en (fallback 路径)
      - character 没 id 也没 name_en 只有 name (深 fallback)
      - inject_identity_anchors 失败 (mock raise Exception) → try/except 兜底
        → log warning 而不阻塞 portrait 生成
      - style_name 是 None / 整数 / 空字符串 (is_bw_style 防御 non-string)
      - character 含完整 physical schema 但 clothing 字段缺失
      - 跨 fullbody + portrait 同一 character 注入相同 anchor (跨路径一致性)

Design:
  - Mirror test_layer1_portrait_injection.py import isolation pattern
    (spec_from_file_location + sys.modules canonical registration)
  - 独立构造 character fixture，不复用 AI-ML 测试数据
  - 使用 caplog fixture 验证 log marker (T3)
  - 使用 monkeypatch mock inject_identity_anchors 异常路径 (T4)
  - 零成本：不调真生图 API，只验证 prompt 构造层

Author: @tester (Sonnet 4.6 effort high, 2026-05-22)
Owner: TASK-WAVE-9-TESTER-INDEPENDENT-BASELINE
"""
from __future__ import annotations

import importlib.util as _ilu
import logging
import os as _os
import sys
import types as _types
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Defensive isolation import — mirror test_layer1_portrait_injection.py pattern
# ---------------------------------------------------------------------------

_STUB_SUSPECTS = (
    "anthropic", "google", "google.genai", "google.generativeai",
)

_CANON_KEYS_TO_CLEAR = (
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
    "app.config",
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


def _clean_and_import_deps():
    """Load reference_image_manager + style_enforcer + identity_anchor_injector
    via spec_from_file_location, bypassing Google/Anthropic SDK cascade.

    Returns:
        (rim_module, style_enforcer_module, injector_module, anchor_module, cpb_module)
    """
    # Clear stub modules first
    for key in _STUB_SUSPECTS:
        mod = sys.modules.get(key)
        if _is_stub(mod):
            sys.modules.pop(key, None)
    for key in _CANON_KEYS_TO_CLEAR:
        mod = sys.modules.get(key)
        if _is_stub(mod):
            sys.modules.pop(key, None)
    for key in _CANON_KEYS_TO_CLEAR:
        sys.modules.pop(key, None)

    project_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))

    # Install minimal package stubs (path-only, no side effects)
    app_pkg = _types.ModuleType("app")
    app_pkg.__path__ = [_os.path.join(project_root, "app")]  # type: ignore[attr-defined]
    sys.modules["app"] = app_pkg

    models_pkg = _types.ModuleType("app.models")
    models_pkg.__path__ = [_os.path.join(project_root, "app", "models")]  # type: ignore[attr-defined]
    sys.modules["app.models"] = models_pkg

    services_pkg = _types.ModuleType("app.services")
    services_pkg.__path__ = [_os.path.join(project_root, "app", "services")]  # type: ignore[attr-defined]
    sys.modules["app.services"] = services_pkg

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

    # Load in dependency order
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
    _RIM, _SE, _INJ, _ANCHOR, _CPB = _clean_and_import_deps()
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
        pytest.skip(f"deps import failed: {_IMPORT_ERR}")


# ---------------------------------------------------------------------------
# Fixtures — 5 character types (Tester 独立设计，不复用 AI-ML fixture)
# ---------------------------------------------------------------------------

class _DummyStyle:
    def __init__(self, preset: str):
        self.style_preset = preset


# 跨 character_type 测试 fixtures
CHAR_FIXTURES = {
    "human": {
        "id": "tester_human_001",
        "name": "林晓霜",
        "name_en": "Lin Xiaoshuang",
        "character_type": "human",
        "gender": "female",
        "age_appearance": "young_adult",
        "physical": {
            "hair_color": "burgundy-crimson with copper highlights",
            "hair_style": "shoulder-length layered",
            "face_shape": "heart",
            "skin_tone": "warm ivory",
            "eye_color": "hazel brown",
            "eye_shape": "wide",
            "distinctive_marks": ["small crescent scar on left cheek"],
        },
        "clothing": {
            "top": "emerald green qipao with gold embroidery",
            "bottom": "fitted slit skirt",
            "accessories": ["jade bracelet", "golden hairpin"],
            "style": "modern cheongsam",
        },
    },
    "supernatural": {
        "id": "tester_supernatural_001",
        "name": "霜魂",
        "name_en": "Frost Soul",
        "character_type": "supernatural",
        "gender": "female",
        "age_appearance": "ageless",
        "physical": {
            "hair_color": "silver-white with icy blue tints",
            "hair_style": "long straight falling to waist",
            "face_shape": "oval",
            "skin_tone": "alabaster pale with faint blue glow",
            "eye_color": "pale silver with luminous glow",
            "eye_shape": "large almond",
            "distinctive_marks": ["translucent ghostly shimmer", "frost crystal patterns on temples"],
        },
        "clothing": {
            "top": "flowing white gossamer robe",
            "bottom": "layered translucent skirt",
            "accessories": ["ice crystal pendant"],
            "style": "ethereal spirit",
        },
    },
    "anthropomorphic_animal": {
        "id": "tester_anthro_001",
        "name": "毛豆",
        "name_en": "Maodou",
        "character_type": "anthropomorphic_animal",
        "gender": "male",
        "age_appearance": "teen",
        "physical": {
            "species": "red panda",
            "fur_color": "russet-orange with cream underbelly",
            "hair_style": "wild tufted ears",
            "face_shape": "round",
            "skin_tone": "orange fur",
            "eye_color": "bright amber",
            "eye_shape": "round",
            "distinctive_marks": ["raccoon-like facial mask pattern", "bushy striped tail"],
        },
        "clothing": {
            "top": "oversized hoodie in sage green",
            "bottom": "cargo shorts",
            "accessories": ["round-frame glasses"],
            "style": "casual streetwear",
        },
    },
    "ai_entity": {
        "id": "tester_ai_001",
        "name": "逻辑",
        "name_en": "Logic",
        "character_type": "ai_entity",
        "gender": "non_binary",
        "age_appearance": "ageless",
        "physical": {
            "hair_color": "electric blue neon with holographic sheen",
            "hair_style": "geometric structured",
            "face_shape": "angular",
            "skin_tone": "translucent with circuit patterns",
            "eye_color": "glowing cyan LEDs",
            "eye_shape": "sleek narrow",
            "distinctive_marks": ["data-stream tattoos across cheekbones", "holographic irises"],
        },
        "clothing": {
            "top": "sleek carbon fiber bodysuit",
            "bottom": "built-in leg interface panels",
            "accessories": ["neural interface headband"],
            "style": "cybernetic android",
        },
    },
    "mythological": {
        "id": "tester_myth_001",
        "name": "风神",
        "name_en": "Wind God",
        "character_type": "mythological",
        "gender": "male",
        "age_appearance": "mature",
        "physical": {
            "hair_color": "stormy grey-white with electric highlights",
            "hair_style": "wind-swept flowing mane",
            "face_shape": "strong square jaw",
            "skin_tone": "bronzed golden",
            "eye_color": "tempestuous storm grey",
            "eye_shape": "piercing narrow",
            "distinctive_marks": ["ancient rune tattoos on forearms", "wind-etched lines on brow"],
        },
        "clothing": {
            "top": "divine armored robe in cloud-white and gold",
            "bottom": "flowing battle skirt",
            "accessories": ["wind-jade scepter", "celestial crown"],
            "style": "divine warrior",
        },
    },
}

# 5 风格 × 5 character_type = 25 matrix
STYLE_PARAMS = ["manga", "children_book", "cyberpunk", "ink", "realistic"]
CHAR_TYPE_PARAMS = ["human", "supernatural", "anthropomorphic_animal", "ai_entity", "mythological"]


# ---------------------------------------------------------------------------
# T2: Portrait path 跨题材矩阵 (5 风格 × 5 character_type = 25 case)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("style", STYLE_PARAMS)
@pytest.mark.parametrize("char_type", CHAR_TYPE_PARAMS)
def test_portrait_cross_genre_matrix_layer1_injected(style, char_type):
    """T2: 跨题材矩阵 portrait — 任何 style × character_type 均含 IDENTITY_ANCHOR_MARKER

    验收标准:
    - portrait prompt 含 IDENTITY_ANCHOR_MARKER
    - 主色 token 出现在 prompt 中
    - CHARACTER ANCHORS section 存在
    """
    _require_import()
    rim = _RIM.ReferenceImageManager()
    project_style = _DummyStyle(style)
    char = CHAR_FIXTURES[char_type]
    inferred_type = rim._get_character_type(char)
    prompt = rim._build_portrait_prompt(char, inferred_type, project_style)

    assert _ANCHOR.IDENTITY_ANCHOR_MARKER in prompt, (
        f"[PORTRAIT MATRIX] style={style!r} char_type={char_type!r} "
        f"MISSING Layer 1 marker — portrait anchor injection FAILED. "
        f"First 400 chars of prompt: {prompt[:400]!r}"
    )

    marker_pos = prompt.find(_ANCHOR.IDENTITY_ANCHOR_MARKER)
    assert marker_pos < 3500, (
        f"[PORTRAIT MATRIX] style={style!r} char_type={char_type!r} "
        f"marker at {marker_pos} — should be in leading high-attention zone"
    )

    assert "CHARACTER ANCHORS" in prompt, (
        f"[PORTRAIT MATRIX] style={style!r} char_type={char_type!r} "
        f"CHARACTER ANCHORS section missing from portrait prompt"
    )

    # Verify primary color token actually surfaced (not empty anchor block)
    char_phys = char.get("physical", {})
    primary_color_raw = char_phys.get("hair_color") or char_phys.get("fur_color") or ""
    if primary_color_raw:
        # Check first distinct word of the color description appears
        first_token = primary_color_raw.split("-")[0].split()[0].lower()
        assert first_token in prompt.lower(), (
            f"[PORTRAIT MATRIX] style={style!r} char_type={char_type!r} "
            f"primary color token '{first_token}' missing from portrait prompt — "
            f"anchor block may be empty"
        )


# ---------------------------------------------------------------------------
# T2: Fullbody path 跨题材矩阵 (5 风格 × 5 character_type = 25 case)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("style", STYLE_PARAMS)
@pytest.mark.parametrize("char_type", CHAR_TYPE_PARAMS)
def test_fullbody_cross_genre_matrix_layer1_injected(style, char_type):
    """T2: 跨题材矩阵 fullbody — 任何 style × character_type 均含 IDENTITY_ANCHOR_MARKER

    验收标准:
    - fullbody prompt 含 IDENTITY_ANCHOR_MARKER
    - 主色 token 出现在 prompt 中
    - CHARACTER ANCHORS section 存在
    """
    _require_import()
    rim = _RIM.ReferenceImageManager()
    project_style = _DummyStyle(style)
    char = CHAR_FIXTURES[char_type]
    inferred_type = rim._get_character_type(char)
    prompt = rim._build_reference_prompt(char, inferred_type, project_style)

    assert _ANCHOR.IDENTITY_ANCHOR_MARKER in prompt, (
        f"[FULLBODY MATRIX] style={style!r} char_type={char_type!r} "
        f"MISSING Layer 1 marker — fullbody anchor injection FAILED. "
        f"First 400 chars of prompt: {prompt[:400]!r}"
    )

    marker_pos = prompt.find(_ANCHOR.IDENTITY_ANCHOR_MARKER)
    assert marker_pos < 3500, (
        f"[FULLBODY MATRIX] style={style!r} char_type={char_type!r} "
        f"marker at {marker_pos} — should be in leading high-attention zone"
    )

    assert "CHARACTER ANCHORS" in prompt, (
        f"[FULLBODY MATRIX] style={style!r} char_type={char_type!r} "
        f"CHARACTER ANCHORS section missing from fullbody prompt"
    )

    # Verify primary color token actually surfaced (not empty anchor block)
    char_phys = char.get("physical", {})
    primary_color_raw = char_phys.get("hair_color") or char_phys.get("fur_color") or ""
    if primary_color_raw:
        first_token = primary_color_raw.split("-")[0].split()[0].lower()
        assert first_token in prompt.lower(), (
            f"[FULLBODY MATRIX] style={style!r} char_type={char_type!r} "
            f"primary color token '{first_token}' missing from fullbody prompt — "
            f"anchor block may be empty"
        )


# ---------------------------------------------------------------------------
# T2: BW style skip — portrait + fullbody 双路 (独立 case, Tester 视角)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("char_type", CHAR_TYPE_PARAMS)
def test_portrait_bw_suffix_skips_layer1_all_char_types(char_type):
    """T2: _bw 后缀对所有 character_type portrait 都 skip Layer 1"""
    _require_import()
    rim = _RIM.ReferenceImageManager()
    project_style = _DummyStyle("manga_bw")
    char = CHAR_FIXTURES[char_type]
    inferred_type = rim._get_character_type(char)
    prompt = rim._build_portrait_prompt(char, inferred_type, project_style)

    assert _ANCHOR.IDENTITY_ANCHOR_MARKER not in prompt, (
        f"[BW SKIP] portrait char_type={char_type!r} 'manga_bw' — "
        f"should SKIP Layer 1 but marker found. prompt[:300]={prompt[:300]!r}"
    )


@pytest.mark.parametrize("char_type", CHAR_TYPE_PARAMS)
def test_fullbody_bw_suffix_skips_layer1_all_char_types(char_type):
    """T2: _bw 后缀对所有 character_type fullbody 都 skip Layer 1"""
    _require_import()
    rim = _RIM.ReferenceImageManager()
    project_style = _DummyStyle("ink_bw")
    char = CHAR_FIXTURES[char_type]
    inferred_type = rim._get_character_type(char)
    prompt = rim._build_reference_prompt(char, inferred_type, project_style)

    assert _ANCHOR.IDENTITY_ANCHOR_MARKER not in prompt, (
        f"[BW SKIP] fullbody char_type={char_type!r} 'ink_bw' — "
        f"should SKIP Layer 1 but marker found. prompt[:300]={prompt[:300]!r}"
    )


# ---------------------------------------------------------------------------
# T3: Log marker 实际触发 verify (3 路 wire)
# ---------------------------------------------------------------------------

def test_portrait_log_marker_injected_fires(caplog):
    """T3: portrait Layer 1 inject → 'Layer 1 injected for portrait' log 实际触发

    技术说明: reference_image_manager 用 logger = logging.getLogger(__name__)
    在 spec_from_file_location 加载时 __name__ = 'app.services.reference_image_manager'。
    caplog 需要使用 root logger 级别 (无 logger 参数) 才能捕获所有 logger。
    """
    _require_import()
    char = CHAR_FIXTURES["human"]
    rim = _RIM.ReferenceImageManager()
    project_style = _DummyStyle("manga")
    inferred_type = rim._get_character_type(char)

    # 使用 root logger 级别捕获所有 logger (包括 app.services.reference_image_manager)
    with caplog.at_level(logging.INFO):
        rim._build_portrait_prompt(char, inferred_type, project_style)

    log_text = caplog.text
    assert "Layer 1 injected for portrait" in log_text, (
        f"Expected 'Layer 1 injected for portrait' in logs but got: {log_text!r}\n"
        f"Note: logger name is 'app.services.reference_image_manager' (not 'xuhua')"
    )
    # char id should be in the log
    assert char["id"] in log_text or char.get("name_en", "") in log_text, (
        f"char id/name_en not found in Layer 1 portrait log: {log_text!r}"
    )


def test_fullbody_log_marker_injected_fires(caplog):
    """T3: fullbody Layer 1 inject → 'Layer 1 injected for fullbody' log 实际触发"""
    _require_import()
    char = CHAR_FIXTURES["supernatural"]
    rim = _RIM.ReferenceImageManager()
    project_style = _DummyStyle("children_book")
    inferred_type = rim._get_character_type(char)

    with caplog.at_level(logging.INFO):
        rim._build_reference_prompt(char, inferred_type, project_style)

    log_text = caplog.text
    assert "Layer 1 injected for fullbody" in log_text, (
        f"Expected 'Layer 1 injected for fullbody' in logs but got: {log_text!r}"
    )


def test_bw_style_skip_log_marker_fires_portrait(caplog):
    """T3: BW portrait → 'Layer 1 SKIPPED (bw style)' log 实际触发"""
    _require_import()
    char = CHAR_FIXTURES["ai_entity"]
    rim = _RIM.ReferenceImageManager()
    project_style = _DummyStyle("realistic_bw")
    inferred_type = rim._get_character_type(char)

    with caplog.at_level(logging.INFO):
        rim._build_portrait_prompt(char, inferred_type, project_style)

    log_text = caplog.text
    assert "Layer 1 SKIPPED (bw style)" in log_text, (
        f"Expected 'Layer 1 SKIPPED (bw style)' in logs but got: {log_text!r}"
    )


def test_bw_style_skip_log_marker_fires_fullbody(caplog):
    """T3: BW fullbody → 'Layer 1 SKIPPED (bw style)' log 实际触发"""
    _require_import()
    char = CHAR_FIXTURES["mythological"]
    rim = _RIM.ReferenceImageManager()
    project_style = _DummyStyle("anime_bw")
    inferred_type = rim._get_character_type(char)

    with caplog.at_level(logging.INFO):
        rim._build_reference_prompt(char, inferred_type, project_style)

    log_text = caplog.text
    assert "Layer 1 SKIPPED (bw style)" in log_text, (
        f"Expected 'Layer 1 SKIPPED (bw style)' in logs but got: {log_text!r}"
    )


# ---------------------------------------------------------------------------
# T4: 边缘 case (Tester 独立设计)
# ---------------------------------------------------------------------------

def test_edge_character_no_id_but_has_name_en():
    """T4: character 没 id 但有 name_en → inject_identity_anchors 用 name_en fallback
    Layer 1 仍注入 (name_en 不为空则 anchor block 有内容)
    """
    _require_import()
    char_no_id = {
        # 无 id 字段
        "name": "无名刺客",
        "name_en": "Nameless Assassin",
        "character_type": "human",
        "physical": {
            "hair_color": "jet black with silver streak",
            "hair_style": "pulled back severely",
            "skin_tone": "olive bronze",
            "face_shape": "angular",
            "eye_color": "cold steel grey",
        },
        "clothing": {
            "top": "black tactical vest",
            "bottom": "dark cargo pants",
            "style": "stealth operative",
        },
    }
    rim = _RIM.ReferenceImageManager()
    project_style = _DummyStyle("realistic")
    char_type = rim._get_character_type(char_no_id)
    prompt = rim._build_portrait_prompt(char_no_id, char_type, project_style)

    # Layer 1 should still inject (name_en is present for anchor block)
    assert _ANCHOR.IDENTITY_ANCHOR_MARKER in prompt, (
        "character without id but with name_en should still get Layer 1 injection"
    )
    # jet (first token of hair_color) should appear
    assert "jet" in prompt.lower() or "black" in prompt.lower(), (
        "primary color token should appear even without id field"
    )


def test_edge_character_no_id_no_name_en_only_name():
    """T4: character 没 id 也没 name_en 只有 name (深 fallback)
    Layer 1 仍注入 (physical anchor block 仍有颜色信息)
    """
    _require_import()
    char_deep_fallback = {
        # 只有中文 name，无 id, 无 name_en
        "name": "幽灵",
        "character_type": "supernatural",
        "physical": {
            "hair_color": "misty white with translucent wisps",
            "hair_style": "flowing ethereal",
            "skin_tone": "ghostly translucent",
            "face_shape": "oval",
            "eye_color": "hollow void grey",
        },
        # 无 clothing
    }
    rim = _RIM.ReferenceImageManager()
    project_style = _DummyStyle("ink")
    char_type = rim._get_character_type(char_deep_fallback)
    prompt = rim._build_portrait_prompt(char_deep_fallback, char_type, project_style)

    # Layer 1 should attempt injection (character has physical data)
    assert _ANCHOR.IDENTITY_ANCHOR_MARKER in prompt, (
        "character with only name (no id, no name_en) should still attempt Layer 1 injection"
    )
    # primary color 'misty' or 'white' should appear
    assert "misty" in prompt.lower() or "white" in prompt.lower(), (
        "primary color token 'misty'/'white' should appear in deep-fallback character portrait"
    )


def test_edge_inject_exception_fallback_no_blocking_portrait(monkeypatch, caplog):
    """T4: inject_identity_anchors 内部 raise Exception → try/except 兜底
    → log warning 出现 but portrait 生成不阻塞 (返回 non-empty prompt)
    """
    _require_import()

    # Patch inject_identity_anchors inside reference_image_manager module to raise
    def _raise_inject(*args, **kwargs):
        raise RuntimeError("Simulated inject failure for T4 test")

    rim_module = _RIM
    monkeypatch.setattr(
        rim_module.ReferenceImageManager,
        "_build_portrait_prompt",
        # We can't easily patch the inner import, so instead patch the injector
        # directly in the sys.modules reference used by rim at runtime
        rim_module.ReferenceImageManager._build_portrait_prompt,  # don't change
    )

    # Directly patch the lazy import that reference_image_manager uses:
    # The module stores a reference to `inject_identity_anchors` via lazy import.
    # We patch it in the injector module's namespace that rim imports from.
    inj_mod = sys.modules.get("app.services.identity_anchor_injector")
    if inj_mod is None:
        pytest.skip("identity_anchor_injector not in sys.modules, skip exception patch test")

    original_fn = inj_mod.inject_identity_anchors
    inj_mod.inject_identity_anchors = _raise_inject  # type: ignore[attr-defined]

    try:
        char = CHAR_FIXTURES["human"]
        rim = rim_module.ReferenceImageManager()
        project_style = _DummyStyle("manga")
        char_type = rim._get_character_type(char)

        with caplog.at_level(logging.WARNING, logger="xuhua"):
            prompt = rim._build_portrait_prompt(char, char_type, project_style)

        # 1. Portrait generation did NOT raise (兜底成功)
        assert isinstance(prompt, str), "Portrait prompt should still be returned (try/except兜底)"
        assert len(prompt) > 50, "Portrait prompt should be non-trivial even after inject failure"

        # 2. Warning log should appear
        log_text = caplog.text
        assert "Layer 1 inject FAILED for portrait" in log_text or "FAILED" in log_text, (
            f"Expected warning about inject failure in logs but got: {log_text!r}"
        )

        # 3. IDENTITY_ANCHOR_MARKER should NOT be in prompt (fallback degraded)
        assert _ANCHOR.IDENTITY_ANCHOR_MARKER not in prompt, (
            "After inject failure, prompt should NOT contain IDENTITY_ANCHOR_MARKER "
            "(degraded to no-anchor)"
        )
    finally:
        # Restore original
        inj_mod.inject_identity_anchors = original_fn  # type: ignore[attr-defined]


def test_edge_inject_exception_fallback_no_blocking_fullbody(monkeypatch, caplog):
    """T4: inject_identity_anchors 异常 → fullbody 也不阻塞，log warning"""
    _require_import()

    inj_mod = sys.modules.get("app.services.identity_anchor_injector")
    if inj_mod is None:
        pytest.skip("identity_anchor_injector not in sys.modules, skip exception patch test")

    original_fn = inj_mod.inject_identity_anchors

    def _raise_inject(*args, **kwargs):
        raise ValueError("Simulated fullbody inject failure for T4 test")

    inj_mod.inject_identity_anchors = _raise_inject  # type: ignore[attr-defined]

    try:
        char = CHAR_FIXTURES["ai_entity"]
        rim = _RIM.ReferenceImageManager()
        project_style = _DummyStyle("cyberpunk")
        char_type = rim._get_character_type(char)

        with caplog.at_level(logging.WARNING, logger="xuhua"):
            prompt = rim._build_reference_prompt(char, char_type, project_style)

        assert isinstance(prompt, str), "Fullbody prompt should still return on inject failure"
        assert len(prompt) > 50, "Fullbody prompt should be non-trivial even after inject failure"

        log_text = caplog.text
        assert "Layer 1 inject FAILED for fullbody" in log_text or "FAILED" in log_text, (
            f"Expected fullbody inject FAILED warning but got: {log_text!r}"
        )
    finally:
        inj_mod.inject_identity_anchors = original_fn  # type: ignore[attr-defined]


def test_edge_is_bw_style_none_input():
    """T4: is_bw_style(None) → False (防御 non-string)"""
    _require_import()
    assert _SE.StyleEnforcer.is_bw_style(None) is False


def test_edge_is_bw_style_integer_input():
    """T4: is_bw_style(123) → False (防御 non-string integer)"""
    _require_import()
    assert _SE.StyleEnforcer.is_bw_style(123) is False


def test_edge_is_bw_style_empty_string():
    """T4: is_bw_style('') → False (空字符串不触发 _bw suffix)"""
    _require_import()
    assert _SE.StyleEnforcer.is_bw_style("") is False


def test_edge_is_bw_style_list_input():
    """T4: is_bw_style([]) → False (防御列表类型)"""
    _require_import()
    assert _SE.StyleEnforcer.is_bw_style([]) is False  # type: ignore[arg-type]


def test_edge_character_missing_clothing_field():
    """T4: character 含完整 physical schema 但 clothing 字段缺失
    Layer 1 仍注入 (physical 已足够构建 anchor block)
    """
    _require_import()
    char_no_clothing = {
        "id": "tester_no_clothing_001",
        "name": "无衣角色",
        "name_en": "No Clothing Char",
        "character_type": "human",
        "physical": {
            "hair_color": "fiery auburn red",
            "hair_style": "wild curly",
            "face_shape": "square",
            "skin_tone": "warm tan",
            "eye_color": "bright emerald green",
            "eye_shape": "round wide",
            "distinctive_marks": ["freckles across nose bridge"],
        },
        # 无 clothing 字段
    }
    rim = _RIM.ReferenceImageManager()
    project_style = _DummyStyle("anime")
    char_type = rim._get_character_type(char_no_clothing)
    prompt = rim._build_portrait_prompt(char_no_clothing, char_type, project_style)

    assert _ANCHOR.IDENTITY_ANCHOR_MARKER in prompt, (
        "Character without clothing field should still get Layer 1 injection from physical alone"
    )
    # 'fiery' or 'auburn' should appear from hair_color
    assert "fiery" in prompt.lower() or "auburn" in prompt.lower(), (
        "Primary color token 'fiery'/'auburn' should appear even without clothing"
    )


def test_edge_portrait_and_fullbody_same_character_anchor_consistency():
    """T4: 跨 fullbody + portrait 同一 character — 两路注入相同 anchor token

    验证 Layer 1 三路统一性 (DEC-049 关键设计):
    portrait 和 fullbody 使用同一个 extract_identity_anchors → 相同主色 token 出现在双路中
    """
    _require_import()
    char = CHAR_FIXTURES["mythological"]  # 独特颜色: stormy grey-white
    rim = _RIM.ReferenceImageManager()
    project_style = _DummyStyle("ink")
    char_type = rim._get_character_type(char)

    portrait_prompt = rim._build_portrait_prompt(char, char_type, project_style)
    fullbody_prompt = rim._build_reference_prompt(char, char_type, project_style)

    # Both must have the marker
    assert _ANCHOR.IDENTITY_ANCHOR_MARKER in portrait_prompt, (
        "Portrait should have Layer 1 marker for cross-path consistency check"
    )
    assert _ANCHOR.IDENTITY_ANCHOR_MARKER in fullbody_prompt, (
        "Fullbody should have Layer 1 marker for cross-path consistency check"
    )

    # Primary color token 'stormy' should appear in BOTH prompts
    assert "stormy" in portrait_prompt.lower(), (
        "Primary color 'stormy' should appear in portrait anchor block"
    )
    assert "stormy" in fullbody_prompt.lower(), (
        "Primary color 'stormy' should appear in fullbody anchor block — "
        "cross-path consistency requires same anchor content"
    )


# ---------------------------------------------------------------------------
# T2 additional: BW_STYLES explicit set skip (cross-genre view)
# ---------------------------------------------------------------------------

def test_bw_styles_explicit_set_portrait_skip():
    """T2/T4: BW_STYLES 显式注册 → portrait skip Layer 1 (任意 char_type)"""
    _require_import()
    StyleEnforcer = _SE.StyleEnforcer
    StyleEnforcer.BW_STYLES.add("tester_grayscale")
    try:
        char = CHAR_FIXTURES["anthropomorphic_animal"]
        rim = _RIM.ReferenceImageManager()
        project_style = _DummyStyle("tester_grayscale")
        char_type = rim._get_character_type(char)
        prompt = rim._build_portrait_prompt(char, char_type, project_style)
        assert _ANCHOR.IDENTITY_ANCHOR_MARKER not in prompt, (
            "Explicit BW_STYLES member 'tester_grayscale' must skip Layer 1 in portrait"
        )
    finally:
        StyleEnforcer.BW_STYLES.discard("tester_grayscale")


def test_bw_styles_explicit_set_fullbody_skip():
    """T2/T4: BW_STYLES 显式注册 → fullbody skip Layer 1 (任意 char_type)"""
    _require_import()
    StyleEnforcer = _SE.StyleEnforcer
    StyleEnforcer.BW_STYLES.add("tester_monochrome")
    try:
        char = CHAR_FIXTURES["supernatural"]
        rim = _RIM.ReferenceImageManager()
        project_style = _DummyStyle("tester_monochrome")
        char_type = rim._get_character_type(char)
        prompt = rim._build_reference_prompt(char, char_type, project_style)
        assert _ANCHOR.IDENTITY_ANCHOR_MARKER not in prompt, (
            "Explicit BW_STYLES member 'tester_monochrome' must skip Layer 1 in fullbody"
        )
    finally:
        StyleEnforcer.BW_STYLES.discard("tester_monochrome")
