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
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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
    """
    角色物理外观 — Stage 2 CharacterDesigner 输出的 physical 字段

    DEC-043 RISK-T20-10 (2026-05-19 方案 C):
    - 所有 sub-field 改 Optional 以支持 19 种 character_type
      (human 用 hair/skin/face_shape, anthropomorphic_animal 用 species/fur_color/ear_style 等)
    - `extra='allow'` 允许 LLM 输出各 character_type 特有字段
      (species, fur_color, snout_shape, robot_type, creature_type 等不在此 schema 列出但合法)
    - 核心字段最小集校验由 CharacterSchema.validate_physical_by_type model_validator 兜底
    """

    model_config = ConfigDict(extra='allow')  # 允许任意 character_type 特有字段透传

    # 通用维度 (任何 character_type 都可能用)
    height: Optional[str] = None
    build: Optional[str] = None
    distinctive_marks: Optional[List[str]] = None

    # human / anthropomorphic_animal / supernatural / undead / miniature / giant 等可能用
    skin_tone: Optional[str] = None
    face_shape: Optional[str] = None
    hair_color: Optional[str] = None
    hair_style: Optional[str] = None
    hair_texture: Optional[str] = None
    eye_color: Optional[str] = None
    eye_shape: Optional[str] = None
    eye_size: Optional[str] = None
    eye_description: Optional[str] = None
    eyebrows: Optional[str] = None
    nose: Optional[str] = None
    lips: Optional[str] = None


class CharacterClothing(BaseModel):
    """
    角色服装 — Stage 2 CharacterDesigner 输出的 clothing 字段

    DEC-043 RISK-T20-10: 部分非 human 类型 (animal/elemental/digital_virtual 等) 可能
    无服装。允许全部 Optional，校验由 CharacterSchema model_validator 兜底。
    """

    model_config = ConfigDict(extra='allow')

    top: Optional[str] = None
    bottom: Optional[str] = None
    footwear: Optional[str] = None
    style: Optional[str] = None
    outerwear: Optional[str] = None
    accessories: Optional[List[str]] = None
    condition: Optional[str] = None


# ============================================================
# 通用 Humanoid Fallback 架构 (Wave 8, 2026-05-22)
#
# 设计原则 (方案 B):
# ─────────────────────────────────────────────────────────────
# 旧方式 (Wave 4 + 4.5 hotfix): 17 个 character_type 各自手动写 humanoid 外貌字段
#   fallback 规则 → 重复、脆弱、新 type 需手动追加。
#
# 新方式: 通用 fallback 函数 has_humanoid_fallback() —
#   任何 character 含 humanoid 外貌字段 (hair_color / skin_tone / face_shape /
#   eye_color / eye_shape) 即视为有效拟人形态，不验 type-specific 字段。
#
# 严格 type (不接受 humanoid fallback):
#   animal          — 纯动物，不呈人形，必须有 species + 皮毛字段
#   vehicle_character — 变形金刚等机械载具，必须有 vehicle_type
#
# 特殊 type:
#   human           — 保留严格规则 (hair_color AND skin_tone 都必须非空)
#   anthropomorphic_animal — 2-group AND 结构
#                     group 1: species 必须有 (动物拟人化的核心要求)
#                     group 2: 毛色/羽色/scale_color 任一 OR humanoid fallback 任一
#
# 其余 15 type: 走通用 fallback — 含 humanoid 外貌字段即 PASS，否则 fallback 告警
# ─────────────────────────────────────────────────────────────

# humanoid fallback 判定字段集 — 含任一非空即视为拟人形态
_HUMANOID_FALLBACK_FIELDS: tuple = (
    'hair_color', 'skin_tone', 'face_shape', 'eye_color', 'eye_shape',
)

# 严格 type 集合 — 不接受 humanoid fallback
_STRICT_TYPES: frozenset = frozenset({'animal', 'vehicle_character'})

# anthropomorphic_animal 特殊: group 2 毛色/羽色字段集 (含 humanoid 外貌)
_ANTHRO_ANIMAL_APPEARANCE_FIELDS: tuple = (
    'fur_color', 'feather_color', 'plumage_color', 'coat_color', 'scale_color',
    # Wave 4.5 P0 — 狼人/猫娘半人形外貌: hair_color / skin_tone / face_shape
    'hair_color', 'skin_tone', 'face_shape',
)

# 严格 type 校验规则 (仅 animal + vehicle_character 使用)
_TYPE_REQUIRED_GROUPS: Dict[str, List[tuple]] = {
    # human: hair_color AND skin_tone 都必须非空 (两 group AND)
    'human': [('hair_color',), ('skin_tone',)],
    # anthropomorphic_animal: species AND (毛色/羽色/.../ 人外貌 任一) 两 group AND
    'anthropomorphic_animal': [
        ('species',),
        _ANTHRO_ANIMAL_APPEARANCE_FIELDS,
    ],
    # 纯动物 — 严格不接受 humanoid fallback
    'animal': [('species',), ('fur_color', 'feather_color', 'plumage_color', 'scale_color', 'skin_color', 'chitin_color')],
    # 载具角色 — 严格不接受 humanoid fallback
    'vehicle_character': [('vehicle_type',)],
}


def has_humanoid_fallback(phys_dict: dict) -> bool:
    """
    通用判断: character physical 字段中含人类外貌关键字段即视为拟人形态。

    判定字段: hair_color / skin_tone / face_shape / eye_color / eye_shape
    任一非空 (str 非空 / list 非空 / truthy) → True

    用于 validate_physical_by_type 在以下情况下提前 PASS:
    - character_type 不在严格集合 (_STRICT_TYPES) 中
    - character_type 不是 'human' / 'anthropomorphic_animal' (各有独立规则)
    - LLM 给了 humanoid 外貌字段 (合理且正确的行为)

    Args:
        phys_dict: CharacterPhysical.model_dump() 的结果 (含 extra='allow' 字段)

    Returns:
        True 如果含任一 humanoid 外貌字段非空，False 否则
    """
    return any(bool(phys_dict.get(f)) for f in _HUMANOID_FALLBACK_FIELDS)


class CharacterSchema(BaseModel):
    """
    单个角色的完整 Schema — Stage 2 CharacterDesigner 输出

    必需: id, name, name_en, role, character_type, gender, physical, clothing
    physical 核心字段最小集: 按 character_type 动态校验
    (DEC-043 RISK-T20-10 方案 C, 2026-05-19)
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

    @model_validator(mode='after')
    def validate_physical_by_type(self) -> 'CharacterSchema':
        """
        DEC-043 RISK-T20-10 + Wave 8 通用 fallback 架构: 按 character_type 动态校验 physical 字段最小集。

        校验流程 (Wave 8, 2026-05-22):
        ─────────────────────────────────────────────────────────────
        1. human / anthropomorphic_animal → 走 _TYPE_REQUIRED_GROUPS 精确规则
        2. animal / vehicle_character (_STRICT_TYPES) → 走 _TYPE_REQUIRED_GROUPS 严格规则
        3. 其余 15 type →
             先检查 has_humanoid_fallback():
               - 含 humanoid 外貌字段 (hair_color / skin_tone / face_shape 等) → 直接 PASS
               - 不含 → logger.warning 告警 (不 raise, 允许 type-specific 字段灵活性)
        4. 未知 character_type → logger.warning 跳过 (给 LLM 扩展新 type 的灵活性)
        ─────────────────────────────────────────────────────────────

        extra='allow' 允许 LLM 输出 type 特有字段 (species/fur_color/robot_type/etc.)
        字段精确规则定义见 _TYPE_REQUIRED_GROUPS (仅 4 个 type)
        通用 humanoid fallback 字段见 _HUMANOID_FALLBACK_FIELDS
        """
        ct = (self.character_type or '').strip().lower()
        if not ct:
            raise ValueError("character_type 不能为空")

        # physical 字段 (含 extra='allow' 注入的字段)
        phys_dict = self.physical.model_dump()

        # ─── 路径 1: 有精确规则的 type (human / anthropomorphic_animal / animal / vehicle_character)
        groups = _TYPE_REQUIRED_GROUPS.get(ct)
        if groups is not None:
            missing_groups = []
            for grp in groups:
                # 每个 group 要求至少一个字段非空 (允许 str / list / 任意 truthy)
                satisfied = any(
                    bool(phys_dict.get(field_name))
                    for field_name in grp
                )
                if not satisfied:
                    missing_groups.append(' OR '.join(grp))

            if missing_groups:
                raise ValueError(
                    f"character_type={ct} physical 字段缺少最小集: "
                    f"需要至少满足 [{' AND '.join(missing_groups)}]，"
                    f"实际 physical keys={sorted(phys_dict.keys())}"
                )
            return self

        # ─── 路径 2: 严格 type (animal / vehicle_character 已在 _TYPE_REQUIRED_GROUPS 处理)
        # 以下为保险兜底 — 理论上不会到这里 (animal + vehicle_character 已在 groups 分支处理)
        if ct in _STRICT_TYPES:
            logger.warning(
                f"[CharacterSchema] 严格 type='{ct}' 未找到精确规则，跳过校验"
            )
            return self

        # ─── 路径 3: 通用 fallback — 其余 15 种 type
        # 含 humanoid 外貌字段 → 直接 PASS (LLM 给了人形描述，合理且正确)
        if has_humanoid_fallback(phys_dict):
            return self

        # 不含 humanoid 外貌字段也不含 type-specific 字段 → 告警但不 raise
        # 这给了 LLM 输出纯 type-specific 字段的灵活性 (e.g. robot_type / creature_type)
        logger.warning(
            f"[CharacterSchema] character_type='{ct}' 既无 humanoid 外貌字段也无 type 特有字段，"
            f"建议补全 physical 描述。实际 physical keys={sorted(phys_dict.keys())}"
        )
        return self


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

    # DEC-046 T20-28 v3: 允许 LLM 输出 narrative_cluster + scene_self_evaluation 等新字段透传
    model_config = ConfigDict(extra='allow')

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

    # DEC-046 T20-28 v3: 允许 LLM 输出 narrative_cluster + scene_self_evaluation 等新字段透传
    model_config = ConfigDict(extra='allow')

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
