"""
TASK-T20-FIXBATCH-3 RISK-T20-10 P0 灾难修复 — Universal CharacterSchema 校验测试

DEC-043 方案 C (Optional + per-type model_validator):
- pipeline_schemas.py CharacterPhysical 所有字段改 Optional + ConfigDict(extra='allow')
- CharacterSchema 加 model_validator(mode='after') 按 character_type 校验最小字段集
- 19 种 character_type 全支持 (human / anthropomorphic_animal / robot / fantasy_creature /
  supernatural / mythological / undead / vehicle_character / insect / miniature / etc.)

10 universal cases (覆盖 5+ character_type) + 5 处下游 consumers 收敛到
CharacterPromptBuilder 的真实输出校验。

测试目标:
1. test17 5 anthropomorphic_animal 角色 schema 真过 (test 1)
2. test18 3 human 角色 regression 不退化 (test 2)
3. 8+ 种 character_type schema 真过 + builder 输出合理 (test 3-9)
4. Edge cases: 缺核心字段清晰失败, 空字符串不允许 silent pass (test 8-9)
5. Smoke: 19 类型各 1 角色 schema 全过 (test 10)

Usage:
    cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story
    python -m pytest tests/test_t20_10_universal_character_schema.py -v
"""

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
from pydantic import ValidationError

from app.services.pipeline_schemas import (
    CharacterPhysical,
    CharacterClothing,
    CharacterSchema,
    CharactersOutput,
    PipelineSchemaError,
    validate_characters,
)
from app.services.character_prompt_builder import CharacterPromptBuilder


# ========================================================================
# Fixtures: 真实 LLM 输出样本 (test17/test18 提取 + 19 类型 mock)
# ========================================================================

def make_anthropomorphic_animal_char(
    id_: str,
    name: str,
    name_en: str,
    species: str,
    fur_color: str,
    extra_physical: dict = None,
) -> dict:
    """构建 anthropomorphic_animal 角色 (test17 风格)"""
    physical = {
        "species": species,
        "fur_color": fur_color,
        "fur_texture": "soft and dense",
        "fur_pattern": "solid with subtle markings",
        "ear_style": f"large {species} ears",
        "tail_style": f"{species} tail",
        "snout_shape": f"{species} muzzle",
        "eye_color": "deep amber",
        "eye_shape": "almond",
        "height": "short",
        "build": "slim",
        "distinctive_marks": ["chest mark"],
    }
    if extra_physical:
        physical.update(extra_physical)

    return {
        "id": id_,
        "name": name,
        "name_en": name_en,
        "role": "protagonist",
        "character_type": "anthropomorphic_animal",
        "gender": "female",
        "age_appearance": "elderly",
        "physical": physical,
        "clothing": {
            "top": "indigo-grey linen wrap-jacket",
            "bottom": "slate blue layered skirt",
            "footwear": "bare pawed",
            "outerwear": "dark charcoal travelling cloak",
            "accessories": ["dried white wildflower stem"],
            "style": "austere_woodland_elder",
            "condition": "worn and faded",
        },
    }


def make_human_char(
    id_: str = "char_001",
    name: str = "苏晨",
    name_en: str = "Su Chen",
    gender: str = "female",
) -> dict:
    """构建 human 角色 (test18 风格)"""
    return {
        "id": id_,
        "name": name,
        "name_en": name_en,
        "role": "protagonist",
        "character_type": "human",
        "gender": gender,
        "age_appearance": "young_adult",
        "physical": {
            "height": "medium",
            "build": "slim",
            "skin_tone": "fair",
            "face_shape": "oval",
            "hair_color": "jet black",
            "hair_style": "short bob cut",
            "hair_texture": "silky",
            "eye_color": "dark brown",
            "eye_shape": "almond",
        },
        "clothing": {
            "top": "light gray fitted blazer",
            "bottom": "black slim-fit trousers",
            "footwear": "black flats",
            "style": "professional elegant",
        },
    }


def make_robot_char() -> dict:
    return {
        "id": "char_robot_001",
        "name": "守护者",
        "name_en": "Guardian",
        "role": "supporting",
        "character_type": "robot",
        "gender": "androgynous",
        "age_appearance": "adult",
        "physical": {
            "robot_type": "humanoid",
            "material": "polished titanium alloy",
            "color_scheme": "midnight blue with silver accents",
            "height": "tall",
            "build": "athletic",
        },
        "clothing": {
            "style": "integrated armor plating",
        },
    }


def make_fantasy_creature_char() -> dict:
    return {
        "id": "char_fc_001",
        "name": "森精灵",
        "name_en": "Forest Sprite",
        "role": "supporting",
        "character_type": "fantasy_creature",
        "gender": "androgynous",
        "age_appearance": "ageless",
        "physical": {
            "creature_type": "elf",
            "base_form": "slender humanoid with leaf-shaped ears",
            "skin_texture": "smooth with faint moss patterns",
        },
        "clothing": {
            "top": "vine-woven tunic",
            "bottom": "moss-green leggings",
            "footwear": "barefoot",
            "style": "natural woodland",
        },
    }


def make_supernatural_char() -> dict:
    return {
        "id": "char_sn_001",
        "name": "雷神",
        "name_en": "Thunder Deity",
        "role": "antagonist",
        "character_type": "supernatural",
        "gender": "male",
        "age_appearance": "elderly",
        "physical": {
            "being_type": "deity",
            "base_form": "humanoid",
        },
        "clothing": {
            "style": "celestial robes",
        },
    }


def make_mythological_char() -> dict:
    return {
        "id": "char_my_001",
        "name": "凤凰",
        "name_en": "Phoenix",
        "role": "supporting",
        "character_type": "mythological",
        "gender": "female",
        "age_appearance": "ageless",
        "physical": {
            "creature_type": "phoenix",
            "origin_culture": "chinese",
            "color_scheme": "crimson and gold",
        },
        "clothing": {
            "style": "natural plumage",
        },
    }


def make_undead_char() -> dict:
    return {
        "id": "char_un_001",
        "name": "幽魂",
        "name_en": "Wraith",
        "role": "antagonist",
        "character_type": "undead",
        "gender": "androgynous",
        "age_appearance": "ancient",
        "physical": {
            "undead_type": "ghost",
            "original_form": "noble warrior",
            "ghostly_transparency": "semi_transparent",
        },
        "clothing": {
            "style": "tattered armor",
        },
    }


def make_vehicle_character_char() -> dict:
    return {
        "id": "char_vc_001",
        "name": "小红",
        "name_en": "Little Red",
        "role": "protagonist",
        "character_type": "vehicle_character",
        "gender": "female",
        "age_appearance": "young",
        "physical": {
            "vehicle_type": "car",
            "body_color": "red",
            "paint_finish": "glossy",
        },
        "clothing": {
            "style": "racing decals",
        },
    }


def make_insect_char() -> dict:
    return {
        "id": "char_in_001",
        "name": "萤萤",
        "name_en": "Firefly",
        "role": "protagonist",
        "character_type": "insect",
        "gender": "female",
        "age_appearance": "young_adult",
        "physical": {
            "species": "firefly",
            "wing_type": "transparent",
            "exoskeleton_color": "soft yellow",
        },
        "clothing": {
            "style": "natural exoskeleton",
        },
    }


def make_miniature_char() -> dict:
    return {
        "id": "char_mi_001",
        "name": "拇指姑娘",
        "name_en": "Thumbelina",
        "role": "protagonist",
        "character_type": "miniature",
        "gender": "female",
        "age_appearance": "young",
        "physical": {
            "base_type": "human",
            "scale_ratio": "thumb_sized",
            "skin_color": "fair",
        },
        "clothing": {
            "top": "petal-woven dress",
            "style": "delicate floral",
        },
    }


# ========================================================================
# Tests 1-10: Universal CharacterSchema 校验
# ========================================================================


class TestUniversalCharacterSchema:
    """T20-10: 10 universal cases 覆盖 5+ character_type"""

    def test_1_anthropomorphic_animal_5chars_validates(self):
        """test17 5 anthropomorphic_animal 角色 schema 真过 (Pipeline 不再 100% 崩)"""
        # 模拟 test17 5 角色 (灰狐/老雪狼/米莉/啾啾/果果)
        chars = [
            make_anthropomorphic_animal_char(
                "char_001", "灰狐", "Grey Fox", "fox", "frost silver grey"
            ),
            make_anthropomorphic_animal_char(
                "char_002", "老雪狼", "Old Snow Wolf", "wolf", "aged off-white",
                extra_physical={"eye_color": "pale winter sky blue"},
            ),
            make_anthropomorphic_animal_char(
                "char_003", "米莉", "Milly", "rabbit", "clean snow white",
            ),
            make_anthropomorphic_animal_char(
                "char_004", "啾啾", "Jojo", "sparrow", "warm chestnut brown",
                extra_physical={"feather_color": "tawny amber"},
            ),
            make_anthropomorphic_animal_char(
                "char_005", "果果", "Guoguo", "squirrel", "russet brown",
            ),
        ]
        # 全部都能过 CharacterSchema 校验
        for char in chars:
            CharacterSchema(**char)  # 不抛异常

        # CharactersOutput 整体也过
        CharactersOutput(characters=chars)

        # validate_characters 函数级别校验也通过
        validate_characters({"characters": chars})

    def test_2_human_3chars_regression(self):
        """test18 3 human 角色 schema 仍过, 不退化"""
        chars = [
            make_human_char("char_001", "陈默", "Chen Mo", "male"),
            make_human_char("char_002", "林晴", "Lin Qing", "female"),
            make_human_char("char_003", "周杰", "Zhou Jie", "male"),
        ]
        for char in chars:
            CharacterSchema(**char)
        CharactersOutput(characters=chars)
        validate_characters({"characters": chars})

    def test_3_robot_passes(self):
        """机器人角色 robot_type/material 满足"""
        char = make_robot_char()
        CharacterSchema(**char)
        # Builder 输出能产生合理 robot 描述 (不是 hardcoded human)
        desc = CharacterPromptBuilder().build_character_prompt(char)
        assert "ROBOT" in desc.upper() or "robot" in desc.lower()
        # 不包含 hardcoded human 误描述
        assert "Asian man" not in desc
        assert "Asian woman" not in desc

    def test_4_fantasy_creature_passes(self):
        """奇幻生物 creature_type/base_form 满足"""
        char = make_fantasy_creature_char()
        CharacterSchema(**char)
        desc = CharacterPromptBuilder().build_character_prompt(char)
        assert "FANTASY" in desc.upper() or "elf" in desc.lower()
        assert "Asian man" not in desc
        assert "Asian woman" not in desc

    def test_5_supernatural_mythological_undead_passes(self):
        """3 supernatural-side type 混合 schema 都过"""
        for char in [
            make_supernatural_char(),
            make_mythological_char(),
            make_undead_char(),
        ]:
            CharacterSchema(**char)
            desc = CharacterPromptBuilder().build_character_prompt(char)
            assert desc  # 非空
            assert "Asian man" not in desc
            assert "Asian woman" not in desc

    def test_6_vehicle_character_passes(self):
        """汽车角色 vehicle_type 满足"""
        char = make_vehicle_character_char()
        CharacterSchema(**char)
        desc = CharacterPromptBuilder().build_character_prompt(char)
        assert "VEHICLE" in desc.upper() or "car" in desc.lower()
        assert "Asian man" not in desc

    def test_7_miniature_insect_mixed(self):
        """拇指姑娘场景: miniature + insect 混合"""
        for char in [
            make_miniature_char(),
            make_insect_char(),
        ]:
            CharacterSchema(**char)
            desc = CharacterPromptBuilder().build_character_prompt(char)
            assert desc

    def test_8_edge_case_anthro_animal_missing_species_fails_clearly(self):
        """边界: anthropomorphic_animal 缺 species → 清晰错误而非 4 missing"""
        char = make_anthropomorphic_animal_char(
            "char_bad", "无名", "Nameless", species="", fur_color=""
        )
        # 删除核心字段
        char["physical"]["species"] = ""
        char["physical"]["fur_color"] = ""
        char["physical"].pop("feather_color", None)
        char["physical"].pop("coat_color", None)

        with pytest.raises(ValidationError) as exc_info:
            CharacterSchema(**char)

        msg = str(exc_info.value)
        # 错误信息明确指出 character_type 和缺失字段组
        assert "anthropomorphic_animal" in msg
        assert "species" in msg
        # 提到 fur_color OR feather_color OR coat_color
        assert "fur_color" in msg or "feather_color" in msg or "coat_color" in msg

    def test_9_edge_case_human_empty_hair_and_skin_fails(self):
        """边界: human 全空 hair + skin → 不允许 silent pass"""
        char = make_human_char()
        char["physical"]["hair_color"] = ""
        char["physical"]["skin_tone"] = ""

        with pytest.raises(ValidationError) as exc_info:
            CharacterSchema(**char)

        msg = str(exc_info.value)
        assert "human" in msg
        assert "hair_color" in msg or "skin_tone" in msg

    def test_10_smoke_19_types_all_pass(self):
        """Smoke test: 19 类型 各 1 角色 schema 全过"""
        type_samples = [
            ("human", {"hair_color": "black", "skin_tone": "fair"}),
            ("anthropomorphic_animal", {"species": "fox", "fur_color": "red"}),
            ("animal", {"species": "wolf", "fur_color": "grey"}),
            ("robot", {"robot_type": "humanoid", "material": "steel"}),
            ("fantasy_creature", {"creature_type": "elf", "base_form": "humanoid"}),
            ("object", {"object_type": "lamp", "base_object": "table lamp"}),
            ("hybrid", {"primary_type": "human", "secondary_type": "wolf"}),
            ("insect", {"species": "bee", "wing_type": "transparent"}),
            ("aquatic", {"species": "dolphin", "body_type": "streamlined"}),
            ("plant", {"plant_type": "tree", "species": "oak"}),
            ("mythological", {"creature_type": "dragon", "origin_culture": "chinese"}),
            ("supernatural", {"being_type": "deity", "base_form": "humanoid"}),
            ("undead", {"undead_type": "ghost", "original_form": "knight"}),
            ("elemental", {"element_type": "fire", "material_form": "energy"}),
            ("alien", {"body_plan": "insectoid"}),
            ("vehicle_character", {"vehicle_type": "car"}),
            ("digital_virtual", {"digital_type": "ai", "base_form": "humanoid"}),
            ("concept_personified", {"concept_type": "time"}),
            ("miniature", {"base_type": "human"}),
            ("giant", {"giant_type": "titan", "height_category": "colossal"}),
        ]
        assert len(type_samples) >= 19  # 至少 19 (实际 20 含 object)

        for ct, physical in type_samples:
            char = {
                "id": f"char_smoke_{ct}",
                "name": f"smoke_{ct}",
                "name_en": f"Smoke_{ct}",
                "role": "test",
                "character_type": ct,
                "gender": "androgynous",
                "age_appearance": "adult",
                "physical": physical,
                "clothing": {"style": "test"},
            }
            try:
                CharacterSchema(**char)
            except ValidationError as e:
                pytest.fail(f"Smoke fail for character_type={ct}: {e}")


# ========================================================================
# Bonus: 5 处下游 consumers 真实输出校验
# ========================================================================


class TestDownstreamConsumersConvergence:
    """T20-10: 5 处下游 consumers 全部 dispatch CharacterPromptBuilder"""

    def test_storyboard_service_identity_line_anthro_no_hardcode(self):
        """storyboard_service._build_identity_line 非 human → CharacterPromptBuilder"""
        from app.services.storyboard_service import StoryboardService
        svc = StoryboardService.__new__(StoryboardService)  # 跳过 __init__ (无需依赖)
        char = make_anthropomorphic_animal_char(
            "char_001", "灰狐", "Grey Fox", "fox", "silver grey"
        )
        line = svc._build_identity_line(char)
        # 不包含 hardcoded "Asian woman/man"
        assert "Asian woman" not in line
        assert "Asian man" not in line
        # 包含动物特征
        assert "fox" in line.lower() or "anthropomorphic" in line.lower()

    def test_storyboard_service_character_description_anthro_no_hardcode(self):
        """storyboard_service._build_character_description 非 human → CharacterPromptBuilder"""
        from app.services.storyboard_service import StoryboardService
        svc = StoryboardService.__new__(StoryboardService)
        char = make_anthropomorphic_animal_char(
            "char_002", "老雪狼", "Old Snow Wolf", "wolf", "aged ivory"
        )
        desc = svc._build_character_description(char)
        assert "Asian woman" not in desc
        assert "Asian man" not in desc
        # 不写 hair_color="aged ivory" — anthropomorphic_animal 用 fur_color
        # 此前 hardcoded 路径会输出 "aged ivory ..." (作为 hair)
        # 现路径输出 "fur" 关键词
        assert "fur" in desc.lower() or "wolf" in desc.lower()

    def test_storyboard_prompts_module_build_character_description_anthro(self):
        """storyboard_prompts 模块级 _build_character_description 非 human → builder"""
        from app.prompts.storyboard_prompts import _build_character_description
        char = make_anthropomorphic_animal_char(
            "char_003", "米莉", "Milly", "rabbit", "snow white"
        )
        desc = _build_character_description(char)
        assert "Asian woman" not in desc
        assert "Asian man" not in desc
        assert "rabbit" in desc.lower() or "anthropomorphic" in desc.lower()

    def test_storyboard_prompts_build_identity_line_phase2_anthro(self):
        """build_identity_line_phase2 非 human → builder"""
        from app.prompts.storyboard_prompts import build_identity_line_phase2
        char = make_anthropomorphic_animal_char(
            "char_004", "啾啾", "Jojo", "sparrow", "chestnut brown"
        )
        line = build_identity_line_phase2(char)
        assert "Asian woman" not in line
        assert "Asian man" not in line
        assert "sparrow" in line.lower() or "anthropomorphic" in line.lower()

    def test_pipeline_orchestrator_convert_anthro_no_hardcode(self):
        """pipeline_orchestrator._convert_characters_for_ref_manager 非 human → builder"""
        from app.services.pipeline_orchestrator import Phase2PipelineOrchestrator
        orch = Phase2PipelineOrchestrator.__new__(Phase2PipelineOrchestrator)
        char = make_anthropomorphic_animal_char(
            "char_005", "果果", "Guoguo", "squirrel", "russet brown"
        )
        chars_dict = {"characters": [char]}
        result = orch._convert_characters_for_ref_manager(chars_dict)
        assert len(result) == 1
        first = result[0]
        # character_type 字段已透传 (ReferenceImageManager 必读)
        assert first.get("character_type") == "anthropomorphic_animal"
        # description 不含 hardcoded human 误描述
        desc = first.get("description", "")
        assert "Asian woman" not in desc
        assert "Asian man" not in desc
        # 包含动物特征
        assert "squirrel" in desc.lower() or "anthropomorphic" in desc.lower()

    def test_pipeline_orchestrator_convert_human_regression(self):
        """human 角色经 _convert_characters_for_ref_manager 不退化 (原路径仍生效)"""
        from app.services.pipeline_orchestrator import Phase2PipelineOrchestrator
        orch = Phase2PipelineOrchestrator.__new__(Phase2PipelineOrchestrator)
        char = make_human_char()
        result = orch._convert_characters_for_ref_manager({"characters": [char]})
        first = result[0]
        assert first.get("character_type") == "human"
        desc = first.get("description", "")
        # human 描述仍含 hair / skin / clothing 字段
        assert "black" in desc.lower()  # hair_color
        assert "fair" in desc.lower()   # skin_tone
        assert "blazer" in desc.lower() # top


# ========================================================================
# Test that physical extra='allow' works (raw test17 dict 直接过)
# ========================================================================


class TestPhysicalExtraAllow:
    """T20-10: CharacterPhysical extra='allow' 允许 type 特有字段透传"""

    def test_anthropomorphic_animal_full_physical_passes(self):
        """test17 真实 LLM 输出 (含 11 个 physical extra fields) schema 真过"""
        # 模拟灰狐的真实 physical 字段
        physical_raw = {
            "species": "fox",
            "fur_color": "frost silver grey",
            "fur_texture": "fluffy but slightly matted",
            "fur_pattern": "darker ash grey saddle",
            "ear_style": "large triangular ears",
            "tail_style": "long and voluminous",
            "snout_shape": "slender elegant fox muzzle",
            "eye_color": "deep amber gold",
            "eye_shape": "almond, slightly hooded",
            "height": "short",
            "build": "slim_slightly_hunched",
            "distinctive_marks": ["silver scar on left forepaw"],
        }
        # CharacterPhysical 直接接受
        cp = CharacterPhysical(**physical_raw)
        # extra fields 真透传 (model_dump 包含所有字段)
        dumped = cp.model_dump()
        assert dumped.get("species") == "fox"
        assert dumped.get("fur_color") == "frost silver grey"
        assert dumped.get("ear_style") == "large triangular ears"
        assert dumped.get("snout_shape") == "slender elegant fox muzzle"

    def test_robot_physical_extra_allow(self):
        """robot physical (robot_type/material) 真透传"""
        cp = CharacterPhysical(
            robot_type="humanoid",
            material="titanium",
            color_scheme="silver",
        )
        dumped = cp.model_dump()
        assert dumped.get("robot_type") == "humanoid"
        assert dumped.get("material") == "titanium"

    def test_validate_characters_function_smoke(self):
        """validate_characters 函数 (Pipeline 调用入口) 真过"""
        chars = [
            make_anthropomorphic_animal_char(
                "char_001", "灰狐", "Grey Fox", "fox", "silver grey"
            ),
            make_human_char("char_002"),
            make_robot_char(),
        ]
        # 不抛 PipelineSchemaError
        validate_characters({"characters": chars})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
