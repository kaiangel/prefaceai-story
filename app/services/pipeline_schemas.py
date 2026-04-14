"""
Pipeline 阶段间数据 Schema - Harness Engineering 的 Sensor
确保阶段间数据传递的格式正确性

覆盖范围:
- Stage 1 → Stage 2: 角色数据 (CharacterSchema)
- Stage 4 → Stage 5: 分镜数据 (ShotSchema)

校验失败时抛出 PipelineSchemaError，Pipeline 中止，
不让错误数据流到下游产生难以追溯的 bug。
"""

import re
import logging
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger("xuhua")


class PipelineSchemaError(Exception):
    """Pipeline Schema 验证失败时抛出的异常"""

    def __init__(self, stage_transition: str, errors: str):
        self.stage_transition = stage_transition
        self.errors = errors
        super().__init__(
            f"[Pipeline] Schema 验证失败 ({stage_transition}): {errors}"
        )


# ============================================================
# Stage 2 输出 Schema: CharacterDesigner → 后续阶段
# ============================================================


class CharacterPhysical(BaseModel):
    """角色物理外观 — Stage 2 CharacterDesigner 输出的 physical 字段"""

    height: str
    build: str
    skin_tone: str
    face_shape: str
    hair_color: str
    hair_style: str
    eye_color: str
    # 以下字段在 CharacterDesigner prompt 中要求，但 LLM 有时会省略，
    # 设为 Optional 允许缺失，核心 5 字段 (上方) 必须存在
    hair_texture: Optional[str] = None
    eye_shape: Optional[str] = None
    eye_size: Optional[str] = None
    eye_description: Optional[str] = None
    eyebrows: Optional[str] = None
    nose: Optional[str] = None
    lips: Optional[str] = None
    distinctive_marks: Optional[List[str]] = None


class CharacterClothing(BaseModel):
    """角色服装 — Stage 2 CharacterDesigner 输出的 clothing 字段"""

    top: str
    bottom: str
    footwear: str
    style: str
    # outerwear 和 condition 在 prompt 中要求但 LLM 可能省略
    outerwear: Optional[str] = None
    accessories: Optional[List[str]] = None
    condition: Optional[str] = None


class CharacterSchema(BaseModel):
    """
    单个角色的完整 Schema — Stage 2 CharacterDesigner 输出

    对应 character_designer.py 的 _validate_characters() 要求的字段:
    必需: name, name_en, role, character_type, gender, physical, clothing
    physical 必需: hair_color, hair_style, eye_color, skin_tone, face_shape
    clothing 必需: top, bottom, footwear, style
    """

    id: str
    name: str
    name_en: str
    role: str
    character_type: str
    gender: str
    age_appearance: str = "adult"
    physical: CharacterPhysical
    clothing: CharacterClothing
    # 可选字段
    personality: Optional[Dict[str, Any]] = None
    character_specific_directions: Optional[Dict[str, Any]] = None


class CharactersOutput(BaseModel):
    """Stage 2 完整输出"""

    characters: List[CharacterSchema] = Field(min_length=1)


# ============================================================
# Stage 4 输出 Schema: StoryboardDirector → Stage 5
# ============================================================


class ShotCamera(BaseModel):
    """镜头摄影参数"""

    shot_size: str
    angle: str
    movement: str = "static"
    focal_length: Optional[str] = None


class ShotComposition(BaseModel):
    """镜头构图参数"""

    subject_position: Optional[str] = None
    foreground: Optional[str] = None
    background: Optional[str] = None
    depth_layers: Optional[str] = None


class ShotLighting(BaseModel):
    """镜头光影参数"""

    key_light: Optional[str] = None
    mood: Optional[str] = None


class ShotCharacterDirection(BaseModel):
    """镜头角色指导"""

    characters_visible: List[str] = Field(default_factory=list)


class ShotTextOverlay(BaseModel):
    """镜头文字覆盖参数"""

    text_type: str = "none"
    chinese_text: Optional[Union[str, List[Any]]] = None
    speaker_position: Optional[str] = None
    off_screen_speaker: Optional[bool] = None


class ShotSchema(BaseModel):
    """
    单个镜头的完整 Schema — Stage 4 StoryboardDirector 输出

    核心约束:
    - image_prompt 必须为纯英文 (允许中文例外: 角色名/地点名/传统元素)
    - shot_id 和 scene_id 为整数
    - camera 字段必须存在
    """

    shot_id: int
    scene_id: int
    action_beat_id: Optional[str] = None
    camera: ShotCamera
    composition: Optional[ShotComposition] = None
    lighting: Optional[ShotLighting] = None
    character_direction: Optional[ShotCharacterDirection] = None
    image_prompt: str
    narration_segment: str = ""
    text_overlay: Optional[ShotTextOverlay] = None
    estimated_duration: float = 5.0

    @field_validator("image_prompt")
    @classmethod
    def image_prompt_must_be_english(cls, v: str) -> str:
        """
        Image prompt 不能包含中文 — 核心约束。

        允许的中文例外 (claude.md 明确列出):
        - 角色中文名 (如 "Chen Mo (陈默)")
        - 中国特色地点名称 (胡同、弄堂、祠堂等)
        - 中国传统服饰 (汉服、旗袍、马褂等)
        - 中国传统建筑元素 (飞檐、斗拱等)
        - 中国美食/店铺类型 (兰州拉面、火锅等)
        - 画面中需要出现的中文书法/文字 (春联、牌匾等)

        检测策略: 如果中文字符超过 prompt 总长度的 15%，判定为中文泄露。
        少量中文字符 (人名、地名等) 属于允许例外。
        """
        if not v or not v.strip():
            raise ValueError("image_prompt 不能为空")

        chinese_chars = re.findall(r"[\u4e00-\u9fff]", v)
        total_chars = len(v)

        if total_chars > 0 and len(chinese_chars) / total_chars > 0.15:
            raise ValueError(
                f"image_prompt 中文比例过高 ({len(chinese_chars)}/{total_chars} = "
                f"{len(chinese_chars)/total_chars:.0%}): {v[:80]}..."
            )
        return v


class StoryboardOutput(BaseModel):
    """Stage 4 完整输出"""

    shots: List[ShotSchema] = Field(min_length=1)
    global_visual_direction: Optional[Dict[str, Any]] = None


# ============================================================
# 验证入口函数
# ============================================================


def validate_characters(characters_data: dict, stage_transition: str = "Stage 1 -> 2") -> None:
    """
    验证 Stage 2 角色设计输出的数据格式。

    在 Pipeline 的 Stage 1→2 转换点调用。
    验证失败时抛出 PipelineSchemaError。

    Args:
        characters_data: CharacterDesigner.design() 的返回值
        stage_transition: 阶段转换标识（用于错误信息）
    """
    try:
        char_list = characters_data.get("characters", [])
        if not char_list:
            raise PipelineSchemaError(
                stage_transition, "characters 数组为空"
            )

        errors = []
        for i, char in enumerate(char_list):
            char_id = char.get("id", f"char_{i+1:03d}")
            try:
                CharacterSchema(**char)
            except Exception as e:
                errors.append(f"角色 {char_id} ({char.get('name', '?')}): {e}")

        if errors:
            error_msg = "\n".join(errors)
            raise PipelineSchemaError(stage_transition, error_msg)

        logger.info(
            f"[Pipeline] Schema 验证通过 ({stage_transition}): "
            f"{len(char_list)} 个角色全部符合规范"
        )
        print(
            f"[Pipeline] Schema 验证通过 ({stage_transition}): "
            f"{len(char_list)} 个角色"
        )

    except PipelineSchemaError:
        raise
    except Exception as e:
        raise PipelineSchemaError(stage_transition, str(e))


def validate_storyboard(storyboard_data: dict, stage_transition: str = "Stage 4 -> 5") -> None:
    """
    验证 Stage 4 分镜脚本输出的数据格式。

    在 Pipeline 的 Stage 4→5 转换点调用。
    验证失败时抛出 PipelineSchemaError。

    Args:
        storyboard_data: StoryboardDirector.direct() 的返回值
        stage_transition: 阶段转换标识（用于错误信息）
    """
    try:
        shots = storyboard_data.get("shots", [])
        if not shots:
            raise PipelineSchemaError(
                stage_transition, "shots 数组为空"
            )

        errors = []
        for i, shot in enumerate(shots):
            shot_id = shot.get("shot_id", i + 1)
            try:
                ShotSchema(**shot)
            except Exception as e:
                errors.append(f"Shot {shot_id}: {e}")

        if errors:
            error_msg = "\n".join(errors)
            raise PipelineSchemaError(stage_transition, error_msg)

        logger.info(
            f"[Pipeline] Schema 验证通过 ({stage_transition}): "
            f"{len(shots)} 个镜头全部符合规范"
        )
        print(
            f"[Pipeline] Schema 验证通过 ({stage_transition}): "
            f"{len(shots)} 个镜头"
        )

    except PipelineSchemaError:
        raise
    except Exception as e:
        raise PipelineSchemaError(stage_transition, str(e))
