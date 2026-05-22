"""
RISK-T20-23: character_designer._validate_characters() hardcoded human fields
修复 2026-05-19

根因: _validate_characters() 的 else 分支对所有非 anthropomorphic_animal 类型
硬要求 ['hair_color', 'hair_style', 'eye_color', 'skin_tone', 'face_shape'],
导致 test19 独眼鸦 (character_type='animal') 抛 ValueError,
Pipeline 在 Stage 2 LLM 返回后、写 2_characters.json 之前崩溃。

修复: else → elif char_type_val == 'human' (硬检查) + else: 其他类型跳过此处,
由 pipeline_orchestrator.py validate_characters() 负责 (T20-10 已覆盖 19 types).

Coverage:
- animal (test19 独眼鸦) 通过 _validate_characters() — 不再抛 ValueError
- anthropomorphic_animal 通过 (T20-22 不退化)
- human 仍强制检查 hair_color/hair_style/eye_color/skin_tone/face_shape (不退化)
- human 缺少 hair_color → ValueError (保持严格校验)
- robot/fantasy_creature 跳过此处 physical 检查 (19 种支持)
"""

import sys
import importlib.util
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import character_designer without triggering full app service init
# (avoids Gemini/Anthropic SDK import errors in CI without API keys)
# ---------------------------------------------------------------------------
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _load_module(name: str, rel_path: str):
    """Load a single .py file as a module, bypassing package __init__ imports."""
    spec = importlib.util.spec_from_file_location(
        name, project_root / rel_path
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# We only need the _validate_characters method; load a thin stub instead of
# importing the full CharacterDesigner which requires LLM clients.
# Strategy: parse character_designer.py to extract _validate_characters logic
# by instantiating CharacterDesigner with mock clients.

# Try direct import — may succeed if deps are available
try:
    from app.services.character_designer import CharacterDesigner  # type: ignore
    _DESIGNER_AVAILABLE = True
except Exception:
    _DESIGNER_AVAILABLE = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_designer() -> object:
    """Return a CharacterDesigner instance with no LLM clients (validation only)."""
    if not _DESIGNER_AVAILABLE:
        pytest.skip("CharacterDesigner import failed (no API keys) — skip")
    cd = CharacterDesigner.__new__(CharacterDesigner)
    cd.anthropic_client = None
    cd.gemini_client = None
    return cd


def _human_char(overrides: dict = None) -> dict:
    """Minimal valid human character."""
    char = {
        "id": "char_001",
        "name": "苏晨",
        "name_en": "Su Chen",
        "role": "protagonist",
        "character_type": "human",
        "gender": "female",
        "age_appearance": "young_adult",
        "physical": {
            "hair_color": "jet black",
            "hair_style": "short bob cut",
            "eye_color": "dark brown",
            "skin_tone": "fair",
            "face_shape": "oval",
        },
        "clothing": {
            "top": "gray wool sweater",
            "bottom": "dark blue jeans",
            "footwear": "white sneakers",
            "style": "casual",
        },
        "description": "A young woman with black hair.",
    }
    if overrides:
        char.update(overrides)
    return char


def _animal_char(overrides: dict = None) -> dict:
    """Minimal valid animal character (test19 独眼鸦 style)."""
    char = {
        "id": "char_003",
        "name": "独眼鸦",
        "name_en": "One-Eyed Crow",
        "role": "supporting",
        "character_type": "animal",
        "gender": "male",
        "age_appearance": "adult",
        "physical": {
            "species": "crow",
            "plumage_color": "jet black with iridescent blue sheen",
            "eye_description": "single golden eye, left eye covered by scar tissue",
            "distinctive_features": "missing left eye, ruffled chest feathers",
            "size": "large crow",
        },
        "clothing": {
            "top": "none",
            "bottom": "none",
            "footwear": "none",
            "style": "natural animal",
        },
        "description": "A one-eyed crow spirit.",
    }
    if overrides:
        char.update(overrides)
    return char


def _anthropomorphic_char(overrides: dict = None) -> dict:
    """Minimal valid anthropomorphic_animal character."""
    char = {
        "id": "char_002",
        "name": "Milly",
        "name_en": "Milly",
        "role": "supporting",
        "character_type": "anthropomorphic_animal",
        "gender": "female",
        "age_appearance": "young_adult",
        "physical": {
            "species": "rabbit",
            "fur_color": "white with gray patches",
            "ear_style": "long floppy",
            "eye_description": "large pink eyes",
        },
        "clothing": {
            "top": "floral dress",
            "bottom": "none",
            "footwear": "leather sandals",
            "style": "cute casual",
        },
        "description": "A white rabbit in a floral dress.",
    }
    if overrides:
        char.update(overrides)
    return char


def _wrap(chars: list) -> dict:
    """Wrap character list into validate_characters() expected format."""
    return {"characters": chars}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAnimalPassesValidation:
    """T20-23 core: animal character_type must NOT raise ValueError."""

    def test_animal_with_plumage_color_passes(self):
        """test19 独眼鸦: animal + plumage_color → no ValueError."""
        cd = _make_designer()
        chars = _wrap([_animal_char()])
        # Must not raise
        cd._validate_characters(chars)

    def test_animal_with_fur_color_passes(self):
        """animal + fur_color only → PASS."""
        cd = _make_designer()
        chars = _wrap([_animal_char({
            "physical": {
                "species": "fox",
                "fur_color": "orange with white underbelly",
            }
        })])
        cd._validate_characters(chars)

    def test_animal_no_hair_fields_required(self):
        """Confirm animal does NOT need hair_color / skin_tone / face_shape."""
        cd = _make_designer()
        # physical has no human fields at all
        chars = _wrap([_animal_char({
            "physical": {
                "species": "sparrow",
                "feather_color": "brown with white streaks",
            }
        })])
        cd._validate_characters(chars)


class TestAnthropomorphicAnimalPasses:
    """T20-22 不退化: anthropomorphic_animal still passes."""

    def test_anthropomorphic_with_fur_color_passes(self):
        cd = _make_designer()
        chars = _wrap([_anthropomorphic_char()])
        cd._validate_characters(chars)

    def test_anthropomorphic_missing_fur_warns_not_raises(self):
        """anthropomorphic_animal missing fur_color → warning, NOT ValueError."""
        cd = _make_designer()
        char = _anthropomorphic_char({
            "physical": {
                "species": "rabbit",
                # fur_color missing
                "eye_description": "pink eyes",
            }
        })
        chars = _wrap([char])
        # Must not raise — only logs a warning
        cd._validate_characters(chars)


class TestHumanStillValidated:
    """Human character_type must still be strictly validated."""

    def test_human_valid_passes(self):
        cd = _make_designer()
        chars = _wrap([_human_char()])
        cd._validate_characters(chars)

    def test_human_missing_hair_color_raises(self):
        cd = _make_designer()
        physical = {
            # hair_color missing
            "hair_style": "short bob",
            "eye_color": "brown",
            "skin_tone": "fair",
            "face_shape": "oval",
        }
        chars = _wrap([_human_char({"physical": physical})])
        with pytest.raises(ValueError, match="physical缺少字段"):
            cd._validate_characters(chars)

    def test_human_missing_skin_tone_raises(self):
        cd = _make_designer()
        physical = {
            "hair_color": "black",
            "hair_style": "bob",
            "eye_color": "brown",
            # skin_tone missing
            "face_shape": "oval",
        }
        chars = _wrap([_human_char({"physical": physical})])
        with pytest.raises(ValueError, match="physical缺少字段"):
            cd._validate_characters(chars)

    def test_human_all_five_fields_required(self):
        """All 5 human physical fields must be present."""
        cd = _make_designer()
        required = ["hair_color", "hair_style", "eye_color", "skin_tone", "face_shape"]
        base_physical = {f: "x" for f in required}
        for field in required:
            physical = {k: v for k, v in base_physical.items() if k != field}
            chars = _wrap([_human_char({"physical": physical})])
            with pytest.raises(ValueError, match="physical缺少字段"):
                cd._validate_characters(chars)


class TestOtherTypesSkipPhysicalCheck:
    """robot / fantasy_creature 等非 human/anthropomorphic_animal 类型跳过此处 physical 检查."""

    def test_robot_passes_without_human_fields(self):
        """robot type: no hair_color/skin_tone needed."""
        cd = _make_designer()
        char = {
            "id": "char_001",
            "name": "R2D2",
            "name_en": "R2D2",
            "role": "supporting",
            "character_type": "robot",
            "gender": "none",
            "age_appearance": "N/A",
            "physical": {
                "robot_type": "utility droid",
                "material": "chrome and blue plastic",
            },
            "clothing": {
                "top": "none",
                "bottom": "none",
                "footwear": "none",
                "style": "mechanical",
            },
            "description": "A small utility robot.",
        }
        cd._validate_characters({"characters": [char]})

    def test_mixed_human_and_animal(self):
        """Mixed cast: human + animal together → both pass."""
        cd = _make_designer()
        chars = _wrap([_human_char(), _animal_char()])
        cd._validate_characters(chars)

    def test_empty_characters_raises(self):
        """Empty characters array still raises ValueError."""
        cd = _make_designer()
        with pytest.raises(ValueError, match="不能为空"):
            cd._validate_characters({"characters": []})


class TestTest19IdeaScenario:
    """Simulate test19 idea scenario: 2 human + 1 animal (crow)."""

    def test_test19_cast_passes(self):
        """Reproduce the exact failure: char_003 (animal) caused ValueError."""
        cd = _make_designer()

        char_001 = _human_char({
            "id": "char_001",
            "name": "陈砚",
            "name_en": "Chen Yan",
            "physical": {
                "hair_color": "jet black",
                "hair_style": "messy short",
                "eye_color": "dark brown",
                "skin_tone": "fair",
                "face_shape": "oval",
            },
        })
        char_002 = _human_char({
            "id": "char_002",
            "name": "陈怀山",
            "name_en": "Chen Huaishan",
            "gender": "male",
            "physical": {
                "hair_color": "salt and pepper",
                "hair_style": "short neat",
                "eye_color": "dark",
                "skin_tone": "medium",
                "face_shape": "square",
            },
        })
        char_003 = _animal_char()  # 独眼鸦, plumage_color only

        chars = _wrap([char_001, char_002, char_003])
        # This used to raise ValueError("角色 char_003 physical缺少字段: ['hair_color', ...]")
        cd._validate_characters(chars)
