"""
RISK-T20-22: animal character_type + plumage_color (鸟类专用) 校验

修复 2026-05-19: _TYPE_REQUIRED_GROUPS['animal'] 漏了 plumage_color，
导致 test19 独眼鸦 (character_type='animal', plumage_color=...) 在 Stage 2 崩溃。

Coverage:
- animal + plumage_color only → PASS
- animal + fur_color only → PASS
- animal + scale_color only → PASS
- animal + all fields empty → FAIL (species ok, color group missing)
- animal + species missing → FAIL
- anthropomorphic_animal + plumage_color → PASS (Wave 14 不退化)
- anthropomorphic_animal + fur_color → PASS (test17 不退化)
"""

import sys
from pathlib import Path

# Add project root to sys.path and import pipeline_schemas directly
# (bypassing app/services/__init__.py which imports Gemini and fails without API keys)
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import importlib.util
_spec = importlib.util.spec_from_file_location(
    "pipeline_schemas",
    project_root / "app" / "services" / "pipeline_schemas.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
CharacterSchema = _mod.CharacterSchema
CharactersOutput = _mod.CharactersOutput

import pytest


# ─── Helper builders ─────────────────────────────────────────────────────────

def _base_char(overrides: dict) -> dict:
    """Minimal valid character skeleton."""
    base = {
        "id": "char_001",
        "name": "独眼鸦",
        "name_en": "One-Eyed Crow",
        "role": "supporting",
        "character_type": "animal",
        "gender": "male",
        "age_appearance": "adult",
        "physical": {
            "species": "crow (Corvus corone)",
            "height": "average",
            "build": "stocky",
        },
        "clothing": {
            "style": "no_clothing_supernatural_animal",
        },
    }
    base.update(overrides)
    return base


def _merge_physical(base_char: dict, physical_extras: dict) -> dict:
    """Merge extra keys into the physical sub-dict."""
    result = dict(base_char)
    result["physical"] = {**base_char["physical"], **physical_extras}
    return result


# ─── PASS cases ──────────────────────────────────────────────────────────────

def test_animal_plumage_color_only_passes():
    """
    RISK-T20-22 核心用例: animal + plumage_color (无 fur_color / feather_color)
    对应 test19 独眼鸦实际 LLM 输出。
    """
    char = _merge_physical(_base_char({}), {
        "plumage_color": "deep matte jet black with cold silver-grey metallic sheen",
        "plumage_texture": "slightly stiff outer feathers, dense underlayer",
        "beak": "long angular iron-blue-black beak",
        "talons": "heavy curved jet black",
    })
    result = CharacterSchema.model_validate(char)
    assert result.character_type == "animal"
    assert result.physical.model_dump()["plumage_color"].startswith("deep matte")


def test_animal_fur_color_only_passes():
    """animal + fur_color (哺乳类 e.g. 狐狸) → 应该 PASS (原有行为不退化)"""
    char = _merge_physical(_base_char({"name": "Wolf", "name_en": "Wolf"}), {
        "fur_color": "grey with darker markings",
    })
    CharacterSchema.model_validate(char)


def test_animal_scale_color_only_passes():
    """animal + scale_color (爬虫 e.g. 蜥蜴) → 应该 PASS"""
    char = _merge_physical(_base_char({"name": "Lizard", "name_en": "Lizard"}), {
        "scale_color": "forest green with mottled brown patches",
    })
    CharacterSchema.model_validate(char)


def test_animal_feather_color_only_passes():
    """animal + feather_color (旧 schema 字段名) → 应该 PASS (旧 schema 不退化)"""
    char = _merge_physical(_base_char({"name": "Eagle", "name_en": "Eagle"}), {
        "feather_color": "golden brown with white head",
    })
    CharacterSchema.model_validate(char)


def test_animal_skin_color_only_passes():
    """animal + skin_color (两栖类 e.g. 青蛙) → 应该 PASS"""
    char = _merge_physical(_base_char({"name": "Frog", "name_en": "Frog"}), {
        "skin_color": "bright green with yellow belly",
    })
    CharacterSchema.model_validate(char)


def test_animal_chitin_color_only_passes():
    """animal + chitin_color (昆虫 e.g. 甲虫) → 应该 PASS"""
    char = _merge_physical(_base_char({"name": "Beetle", "name_en": "Beetle"}), {
        "chitin_color": "iridescent dark green",
    })
    CharacterSchema.model_validate(char)


def test_animal_test19_full_char003_passes():
    """
    test19 char_003 独眼鸦完整字段 → 应该 PASS (真实崩溃复现后验证修复)
    """
    char = {
        "id": "char_003",
        "name": "独眼鸦",
        "name_en": "One-Eyed Crow",
        "role": "supporting",
        "character_type": "animal",
        "gender": "male",
        "age_appearance": "adult",
        "physical": {
            "height": "average",
            "build": "stocky",
            "face_shape": None,
            "skin_tone": None,
            "hair_color": None,
            "hair_style": None,
            "hair_texture": None,
            "eye_color": "left eye: living pale cold silver-white iris with a pinpoint black pupil",
            "eye_shape": "almond",
            "eye_size": "medium",
            "eye_description": "left eye alive with cold silver-white light",
            "eyebrows": None,
            "nose": None,
            "lips": None,
            "distinctive_marks": [
                "plumage carries an unnatural cold metallic sheen",
                "right eye socket contains a silver button",
            ],
            "species": "crow (Corvus corone / large mountain variant)",
            "fur_color": None,
            "plumage_color": "deep matte jet black across entire body, overlaid with unnatural cold silver-grey metallic sheen",
            "plumage_texture": "outer feathers slightly stiff and over-smooth",
            "body_size": "noticeably large for a crow",
            "beak": "long angular iron-blue-black beak, upper mandible distinctly hooked at tip",
            "talons": "heavy and curved, jet black fading to dark steel-grey at tips",
            "tail": "long graduated tail feathers, tips frost-edged in permanent white crystalline rime",
        },
        "clothing": {
            "top": None,
            "bottom": None,
            "outerwear": None,
            "footwear": None,
            "accessories": ["a single hand-wrought silver button resting in the hollow of the right eye socket"],
            "style": "no_clothing_supernatural_animal",
            "condition": "perpetually frost-edged",
        },
        "personality": {
            "core_trait": "ancient_sorrowful_witness",
            "surface_behavior": "unnervingly_still_and_silent",
            "internal_conflict": "the_burden_of_knowing_vs_the_mercy_of_withholding",
        },
    }
    result = CharacterSchema.model_validate(char)
    assert result.id == "char_003"
    # plumage_color should be accessible via extra fields
    phys_dict = result.physical.model_dump()
    assert phys_dict.get("plumage_color") is not None


# ─── FAIL cases ──────────────────────────────────────────────────────────────

def test_animal_no_color_field_fails():
    """
    animal + species present but NO color field at all → 应该 FAIL
    (第二个 required group 未满足)
    """
    char = _base_char({})
    # physical has only species, height, build — no color field
    with pytest.raises(Exception) as exc_info:
        CharacterSchema.model_validate(char)
    error_msg = str(exc_info.value)
    assert "physical 字段缺少最小集" in error_msg or "Value error" in error_msg


def test_animal_no_species_fails():
    """
    animal + plumage_color but no species → 应该 FAIL
    (第一个 required group 未满足)
    """
    char = {
        "id": "char_001",
        "name": "神秘鸟",
        "name_en": "Mystery Bird",
        "role": "supporting",
        "character_type": "animal",
        "gender": "unknown",
        "age_appearance": "adult",
        "physical": {
            # no species field
            "plumage_color": "deep black with silver sheen",
        },
        "clothing": {"style": "none"},
    }
    with pytest.raises(Exception) as exc_info:
        CharacterSchema.model_validate(char)
    error_msg = str(exc_info.value)
    assert "physical 字段缺少最小集" in error_msg or "Value error" in error_msg


# ─── anthropomorphic_animal 不退化 (Wave 14) ────────────────────────────────

def test_anthropomorphic_animal_plumage_color_passes():
    """
    anthropomorphic_animal + plumage_color (如: 拟人化鸟类角色) → PASS
    RISK-T20-22 同步扩展 anthropomorphic_animal group
    """
    char = {
        "id": "char_001",
        "name": "啾啾",
        "name_en": "Jojo",
        "role": "supporting",
        "character_type": "anthropomorphic_animal",
        "gender": "female",
        "age_appearance": "young_adult",
        "physical": {
            "species": "sparrow",
            "plumage_color": "warm tawny brown with darker umber streaks",
        },
        "clothing": {
            "top": "ochre-yellow puffed-sleeve blouse",
            "style": "cheerful_chaotic_forest_sparrow",
        },
    }
    result = CharacterSchema.model_validate(char)
    assert result.character_type == "anthropomorphic_animal"


def test_anthropomorphic_animal_fur_color_still_passes():
    """
    test17 灰狐 (anthropomorphic_animal + fur_color) → PASS (Wave 14 不退化)
    """
    char = {
        "id": "char_001",
        "name": "灰狐",
        "name_en": "Grey Fox",
        "role": "protagonist",
        "character_type": "anthropomorphic_animal",
        "gender": "female",
        "age_appearance": "elderly",
        "physical": {
            "species": "fox",
            "fur_color": "frost silver-grey with ivory white underbelly",
            "fur_texture": "fine but slightly coarse with age",
            "eye_color": "deep amber-gold with grey ring at iris edge",
        },
        "clothing": {
            "top": "pale birch-bark beige linen wrap coat",
            "style": "weathered_forest_elder",
        },
    }
    result = CharacterSchema.model_validate(char)
    assert result.character_type == "anthropomorphic_animal"


def test_characters_output_test19_all_chars_pass():
    """
    test19 全部 3 个角色 (2 human + 1 animal crow) 作为 CharactersOutput 验证 → PASS
    """
    data = {
        "characters": [
            {
                "id": "char_001",
                "name": "陈砚",
                "name_en": "Chen Yan",
                "role": "protagonist",
                "character_type": "human",
                "gender": "male",
                "age_appearance": "adult",
                "physical": {
                    "hair_color": "coarse jet black",
                    "hair_style": "short cropped",
                    "skin_tone": "tan",
                    "face_shape": "square",
                    "eye_color": "dark charcoal brown",
                },
                "clothing": {"top": "indigo cotton shirt", "style": "mountain_hunter"},
            },
            {
                "id": "char_002",
                "name": "陈怀山",
                "name_en": "Chen Huaishan",
                "role": "supporting",
                "character_type": "human",
                "gender": "male",
                "age_appearance": "elderly",
                "physical": {
                    "hair_color": "pure white",
                    "skin_tone": "pale",
                    "face_shape": "oval",
                },
                "clothing": {"top": "pale grey linen inner garment", "style": "austere_traditional"},
            },
            {
                "id": "char_003",
                "name": "独眼鸦",
                "name_en": "One-Eyed Crow",
                "role": "supporting",
                "character_type": "animal",
                "gender": "male",
                "age_appearance": "adult",
                "physical": {
                    "species": "crow (Corvus corone)",
                    "plumage_color": "deep matte jet black with cold silver-grey metallic sheen",
                    "beak": "long angular iron-blue-black beak",
                    "talons": "heavy and curved, jet black",
                },
                "clothing": {"style": "no_clothing_supernatural_animal"},
            },
        ]
    }
    result = CharactersOutput.model_validate(data)
    assert len(result.characters) == 3
    assert result.characters[2].character_type == "animal"
    assert result.characters[2].physical.model_dump()["plumage_color"] is not None
