"""Wave 13 #5e A: 非穿衣 type clothing 缺字段降 warning 不 raise (防冲垮 pipeline)。

验证:
  1. object / aquatic / plant / insect / elemental / vehicle_character / animal
     缺 clothing 子字段 → 不 raise (pipeline 继续)
  2. human (穿衣 type) 缺 clothing 子字段 → 仍 raise (surgical: 不破坏现有校验)
  3. 完整 clothing 的任何 type → 不 raise
"""

import pytest

from app.services.character_designer import CharacterDesigner


def _base_char(char_type: str, clothing: dict) -> dict:
    """构造一个除 clothing 外字段齐全的角色 (physical 给非 human 最小集, 避免别处误 raise)。"""
    char = {
        "id": "char_001",
        "name": "测试角色",
        "name_en": "Test Char",
        "role": "protagonist",
        "character_type": char_type,
        "gender": "male",
        "clothing": clothing,
    }
    if char_type == "human":
        char["physical"] = {
            "hair_color": "black",
            "hair_style": "short",
            "eye_color": "brown",
            "skin_tone": "fair",
            "face_shape": "oval",
        }
    elif char_type == "object":
        char["physical"] = {"object_type": "grandfather clock", "material": "mahogany"}
    elif char_type == "aquatic":
        char["physical"] = {"species": "clownfish", "scale_pattern": "orange-white bands"}
    elif char_type == "plant":
        char["physical"] = {"plant_type": "sunflower", "petal_color": "golden yellow"}
    elif char_type == "insect":
        char["physical"] = {"species": "ant", "exoskeleton": "glossy black"}
    elif char_type == "elemental":
        char["physical"] = {"element_type": "flame", "glow": "amber"}
    elif char_type == "vehicle_character":
        char["physical"] = {"vehicle_type": "vintage car", "paint": "cherry red"}
    elif char_type == "animal":
        char["physical"] = {"species": "wolf", "fur_color": "gray"}
    else:
        char["physical"] = {"being_type": "spirit"}
    return char


_INCOMPLETE_CLOTHING = {"style": "antique surface"}  # 缺 top/bottom/footwear


@pytest.mark.parametrize(
    "char_type",
    ["object", "aquatic", "plant", "insect", "elemental", "vehicle_character", "animal"],
)
def test_non_clothing_type_missing_clothing_does_not_raise(char_type):
    """非穿衣 type 缺 clothing 子字段 → 降 warning 不 raise → pipeline 不崩。"""
    designer = CharacterDesigner()
    chars = {"characters": [_base_char(char_type, dict(_INCOMPLETE_CLOTHING))]}
    # 不应抛异常 (旧代码会 raise ValueError)
    designer._validate_characters(chars)


def test_object_clothing_entirely_minimal_does_not_raise():
    """object 只给 style, 其余 clothing 全缺 → 不崩。"""
    designer = CharacterDesigner()
    chars = {"characters": [_base_char("object", {"style": "brass clock"})]}
    designer._validate_characters(chars)


def test_human_missing_clothing_still_raises():
    """surgical 守护: human 缺 clothing 子字段 → 仍 raise (现有穿衣校验不破坏)。"""
    designer = CharacterDesigner()
    chars = {"characters": [_base_char("human", dict(_INCOMPLETE_CLOTHING))]}
    with pytest.raises(ValueError, match="clothing缺少字段"):
        designer._validate_characters(chars)


def test_complete_clothing_object_does_not_raise():
    """非穿衣 type 给完整 clothing (n/a 占位) → 正常通过。"""
    designer = CharacterDesigner()
    full = {
        "top": "n/a",
        "bottom": "n/a",
        "footwear": "n/a",
        "style": "antique mahogany grandfather clock",
    }
    chars = {"characters": [_base_char("object", full)]}
    designer._validate_characters(chars)


def test_complete_clothing_human_does_not_raise():
    """human 给完整 clothing → 正常通过 (回归: 不误伤正常 human)。"""
    designer = CharacterDesigner()
    full = {
        "top": "white shirt",
        "bottom": "blue jeans",
        "footwear": "sneakers",
        "style": "casual",
    }
    chars = {"characters": [_base_char("human", full)]}
    designer._validate_characters(chars)


def test_non_clothing_types_set_membership():
    """NON_CLOTHING_TYPES 含 PM 决策 A 的 4 type + AI-ML 列出的其余非穿衣 type。"""
    s = CharacterDesigner.NON_CLOTHING_TYPES
    for t in ("object", "aquatic", "plant", "insect"):
        assert t in s
    # human / 超自然人形 / robot 不在内 (仍严格校验)
    for t in ("human", "supernatural", "robot", "anthropomorphic_animal"):
        assert t not in s
