"""
test_supernatural_humanoid_hotfix.py

DEC-043 RISK-T20-?? hotfix (2026-05-20):
验证 supernatural / undead / mythological / fantasy_creature 这 4 种 character_type
在 physical 字段只有人类外貌字段（而无 being_type/base_form 等专属字段）时，
CharacterSchema 能正常通过验证而不报错。

复现 test20 horror 电梯镜中人 (char_002, supernatural type) 的事故场景。
"""

import pytest
from app.services.pipeline_schemas import CharacterSchema


def _make_char(char_type: str, **extra_physical) -> dict:
    """构造一个最小化的角色 dict，physical 只含人类外貌字段。"""
    return {
        "id": "char_002",
        "name": "镜中人",
        "name_en": "Mirror Entity",
        "role": "antagonist",
        "character_type": char_type,
        "gender": "unknown",
        "age_appearance": "adult",
        "physical": {
            "height": "tall",
            "build": "slender",
            "hair_color": "silver white",
            "hair_style": "long straight",
            "hair_texture": "silky",
            "face_shape": "sharp angular",
            "skin_tone": "pale",
            "eye_color": "mirror-like silver",
            "eye_shape": "almond",
            "eye_size": "large",
            "eye_description": "reflective and unsettling",
            "eyebrows": "sharp thin",
            "nose": "straight",
            "lips": "pale thin",
            "distinctive_marks": ["mirror-like eyes that reflect surroundings"],
            **extra_physical,
        },
        "clothing": {
            "top": "tattered white dress shirt",
            "bottom": "black torn trousers",
            "style": "unsettling distorted",
        },
    }


class TestSupernatualHumanoidHotfix:
    """
    复现 test20 镜中人崩溃场景，确认 4 种人形超自然类型均通过。
    """

    def test_supernatural_with_human_physical_passes(self):
        """supernatural + 纯人类外貌字段 → 应通过（修复前报错）"""
        data = _make_char("supernatural")
        char = CharacterSchema(**data)
        assert char.character_type == "supernatural"

    def test_undead_with_human_physical_passes(self):
        """undead + 纯人类外貌字段 → 应通过（鬼魂 / 丧尸外表像人）"""
        data = _make_char("undead")
        char = CharacterSchema(**data)
        assert char.character_type == "undead"

    def test_mythological_with_human_physical_passes(self):
        """mythological + 纯人类外貌字段 → 应通过（山神 / 仙人外表像人）"""
        data = _make_char("mythological")
        char = CharacterSchema(**data)
        assert char.character_type == "mythological"

    def test_fantasy_creature_with_human_physical_passes(self):
        """fantasy_creature + 纯人类外貌字段 → 应通过（精灵 / 妖外表像人）"""
        data = _make_char("fantasy_creature")
        char = CharacterSchema(**data)
        assert char.character_type == "fantasy_creature"

    def test_supernatural_with_being_type_still_passes(self):
        """supernatural + being_type 字段（老路径）→ 依然通过，不退化"""
        data = _make_char("supernatural", being_type="mirror entity", base_form="humanoid")
        char = CharacterSchema(**data)
        assert char.character_type == "supernatural"

    def test_supernatural_missing_all_fields_fails(self):
        """supernatural + 既无 being_type/base_form 也无人类外貌字段 → 应报错"""
        data = {
            "id": "char_003",
            "name": "空洞实体",
            "name_en": "Void Entity",
            "role": "antagonist",
            "character_type": "supernatural",
            "gender": "none",
            "age_appearance": "unknown",
            "physical": {
                "height": "variable",
                "build": "formless",
                # 故意不提供 being_type / base_form / hair_color / skin_tone / face_shape
            },
            "clothing": {
                "style": "none",
            },
        }
        with pytest.raises(ValueError, match="physical 字段缺少最小集"):
            CharacterSchema(**data)

    def test_human_type_unaffected(self):
        """human type 的校验逻辑不受此次修改影响"""
        data = {
            "id": "char_001",
            "name": "主角",
            "name_en": "Protagonist",
            "role": "protagonist",
            "character_type": "human",
            "gender": "female",
            "age_appearance": "young_adult",
            "physical": {
                "hair_color": "black",
                "skin_tone": "fair",
                "face_shape": "oval",
            },
            "clothing": {
                "top": "white blouse",
                "style": "casual",
            },
        }
        char = CharacterSchema(**data)
        assert char.character_type == "human"
