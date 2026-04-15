"""
Pipeline 阶段间数据 Schema - Harness Engineering 的 Sensor
确保阶段间数据传递的格式正确性

覆盖范围:
- Stage 1 → Stage 2: 大纲数据 (OutlineSchema) + 角色数据 (CharacterSchema)
- Stage 3 → Stage 4: 剧本数据 (ScreenplaySchema)
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
# Stage 1 输出 Schema: StoryOutlineGenerator → Stage 2
# ============================================================


class OutlineCharacterOverview(BaseModel):
    """角色概览 — Stage 1 大纲中的 characters_overview 子项"""

    name_suggestion: Optional[str] = None
    name_en: Optional[str] = None
    role: Optional[str] = None
    description: str
    personality: Optional[str] = None
    archetype: Optional[str] = None
    age_range: Optional[str] = None
    gender: Optional[str] = None
    family_role: Optional[str] = None
    emotional_journey: Optional[str] = None

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("角色 description 不能为空")
        return v


class OutlinePlotPoint(BaseModel):
    """情节节点 — Stage 1 大纲中的 plot_points 子项"""

    beat: Optional[str] = None
    description: str
    estimated_duration_seconds: Optional[float] = None

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("plot_point description 不能为空")
        return v


class OutlineLocation(BaseModel):
    """场景位置 — Stage 1 大纲中的 unique_locations 子项"""

    location_id: str
    display_name: Optional[str] = None
    description_zh: Optional[str] = None
    location_type: Optional[str] = None
    time_of_day: Optional[str] = None
    weather: Optional[str] = None
    atmosphere: Optional[str] = None
    interior_description: Optional[str] = None
    exterior_description: Optional[str] = None
    key_visual_elements: Optional[List[str]] = None
    signage_text: Optional[str] = None


class OutlineSchema(BaseModel):
    """
    Stage 1 大纲完整 Schema — StoryOutlineGenerator 输出

    必需字段: title, title_en, logline, summary,
    characters_overview (min 1), plot_points (min 3), unique_locations (min 1)
    """

    title: str
    title_en: str
    logline: str
    summary: str
    ending_options: Optional[List[Dict[str, Any]]] = None
    mood: Optional[str] = None
    emotional_arc: Optional[Dict[str, Any]] = None
    narrative_pace: Optional[str] = None
    visual_tone: Optional[Dict[str, Any]] = None
    target_metrics: Optional[Dict[str, Any]] = None
    characters_overview: List[OutlineCharacterOverview] = Field(min_length=1)
    family_relationships: Optional[List[Dict[str, Any]]] = None
    plot_points: List[OutlinePlotPoint] = Field(min_length=3)
    unique_locations: List[OutlineLocation] = Field(min_length=1)

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("title 不能为空")
        return v

    @field_validator("title_en")
    @classmethod
    def title_en_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("title_en 不能为空")
        return v

    @field_validator("logline")
    @classmethod
    def logline_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("logline 不能为空")
        return v

    @field_validator("summary")
    @classmethod
    def summary_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("summary 不能为空")
        return v

    @field_validator("characters_overview")
    @classmethod
    def characters_not_empty_list(cls, v: List[OutlineCharacterOverview]) -> List[OutlineCharacterOverview]:
        if not v:
            raise ValueError("characters_overview 不能为空列表")
        return v


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
# Stage 3 输出 Schema: ScreenplayWriter → Stage 4
# ============================================================


class ActionBeat(BaseModel):
    """动作节拍 — Stage 3 剧本中 scene.action_beats 子项"""

    beat_id: str
    action: Optional[str] = None
    duration_hint: Optional[float] = None
    emotional_note: Optional[str] = None

    @field_validator("beat_id")
    @classmethod
    def beat_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("beat_id 不能为空")
        return v


class DialogueBeat(BaseModel):
    """对话节拍 — Stage 3 剧本中 scene.dialogue_beats 子项"""

    beat_id: str
    type: Optional[str] = None
    speaker: Optional[str] = None
    line: Optional[str] = None
    emotion: Optional[str] = None


class SceneAtmosphere(BaseModel):
    """场景氛围"""

    mood: Optional[str] = None
    sound_design_hint: Optional[str] = None
    temperature_feel: Optional[str] = None


class SceneSchema(BaseModel):
    """
    单个场景的完整 Schema — Stage 3 ScreenplayWriter 输出的 scene

    必需: scene_id, location_id, characters_in_scene (list), action_beats (min 1)
    每个 action_beat 必须有 beat_id
    """

    scene_id: int
    scene_heading: Optional[str] = None
    plot_point: Optional[str] = None
    location_id: str
    time_of_day: Optional[str] = None
    weather: Optional[str] = None
    lighting_condition: Optional[str] = None
    atmosphere: Optional[Union[SceneAtmosphere, Dict[str, Any]]] = None
    characters_in_scene: List[str] = Field(default_factory=list)
    action_beats: List[ActionBeat] = Field(min_length=1)
    dialogue_beats: Optional[List[DialogueBeat]] = None
    narration: str = ""
    narration_tone: Optional[str] = None
    narration_pace: Optional[str] = None


class ScreenplaySchema(BaseModel):
    """
    Stage 3 完整输出 — ScreenplayWriter 的 scenes 列表

    必需: scenes (min 1)
    每个 scene 必须有 scene_id, location_id, characters_in_scene, action_beats (min 1)
    每个 action_beat 必须有 beat_id
    """

    scenes: List[SceneSchema] = Field(min_length=1)

    @field_validator("scenes")
    @classmethod
    def scenes_not_empty_list(cls, v: List[SceneSchema]) -> List[SceneSchema]:
        if not v:
            raise ValueError("scenes 不能为空列表")
        return v


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

        检测策略: 如果中文字符超过 prompt 总长度的 5%，判定为中文泄露。
        5% 允许角色中文名 (如 "Chen Mo (陈默)") 但拒绝大段中文。
        """
        if not v or not v.strip():
            raise ValueError("image_prompt 不能为空")

        chinese_chars = re.findall(r"[\u4e00-\u9fff]", v)
        total_chars = len(v)

        if total_chars > 0 and len(chinese_chars) / total_chars > 0.05:
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


def validate_outline(outline_data: dict, stage_transition: str = "Stage 1 -> 2") -> None:
    """
    验证 Stage 1 大纲输出的数据格式。

    在 Pipeline 的 Stage 1 LLM 返回后立即调用。
    验证失败时抛出 PipelineSchemaError。

    Args:
        outline_data: StoryOutlineGenerator.generate() 的返回值
        stage_transition: 阶段转换标识（用于错误信息）
    """
    try:
        OutlineSchema(**outline_data)

        logger.info(
            f"[Pipeline] Schema 验证通过 ({stage_transition}): "
            f"大纲包含 {len(outline_data.get('characters_overview', []))} 角色, "
            f"{len(outline_data.get('plot_points', []))} 情节点, "
            f"{len(outline_data.get('unique_locations', []))} 场景"
        )
        print(
            f"[Pipeline] Schema 验证通过 ({stage_transition}): "
            f"大纲 {len(outline_data.get('characters_overview', []))} 角色 / "
            f"{len(outline_data.get('plot_points', []))} 情节点 / "
            f"{len(outline_data.get('unique_locations', []))} 场景"
        )

    except PipelineSchemaError:
        raise
    except Exception as e:
        raise PipelineSchemaError(stage_transition, str(e))


def validate_screenplay(screenplay_data: dict, stage_transition: str = "Stage 3 -> 4") -> None:
    """
    验证 Stage 3 剧本输出的数据格式。

    在 Pipeline 的 Stage 3 LLM 返回后立即调用。
    验证失败时抛出 PipelineSchemaError。

    Args:
        screenplay_data: ScreenplayWriter.write() 的返回值
        stage_transition: 阶段转换标识（用于错误信息）
    """
    try:
        scenes = screenplay_data.get("scenes", [])
        if not scenes:
            raise PipelineSchemaError(
                stage_transition, "scenes 数组为空"
            )

        errors = []
        for i, scene in enumerate(scenes):
            scene_id = scene.get("scene_id", i + 1)
            try:
                SceneSchema(**scene)
            except Exception as e:
                errors.append(f"Scene {scene_id}: {e}")

        if errors:
            error_msg = "\n".join(errors)
            raise PipelineSchemaError(stage_transition, error_msg)

        total_beats = sum(len(s.get("action_beats", [])) for s in scenes)
        logger.info(
            f"[Pipeline] Schema 验证通过 ({stage_transition}): "
            f"{len(scenes)} 个场景, {total_beats} 个 action_beats"
        )
        print(
            f"[Pipeline] Schema 验证通过 ({stage_transition}): "
            f"{len(scenes)} 场景 / {total_beats} action_beats"
        )

    except PipelineSchemaError:
        raise
    except Exception as e:
        raise PipelineSchemaError(stage_transition, str(e))


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
