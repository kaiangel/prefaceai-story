"""
角色一致性服务 - 确保故事中角色在不同场景的视觉一致性

核心策略：
1. 方案A（主要）：通过极度详细的文字描述保持一致性
2. 方案B（备用）：使用角色参考图 + Pro模型

支持最多10个角色的一致性管理
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("xuhua")


class CharacterType(Enum):
    """角色类型"""
    HUMAN = "human"
    ANIMAL = "animal"
    CREATURE = "creature"  # 幻想生物
    ROBOT = "robot"
    OTHER = "other"


class Gender(Enum):
    """性别"""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


@dataclass
class PhysicalFeatures:
    """物理特征 - 人类/类人角色"""
    height: str = ""  # tall/medium/short/petite
    build: str = ""  # slim/athletic/average/stocky/heavy
    skin_tone: str = ""  # pale/fair/medium/olive/tan/brown/dark
    face_shape: str = ""  # oval/round/square/heart/long

    # 头发
    hair_color: str = ""  # black/brown/blonde/red/gray/white/colored(specify)
    hair_style: str = ""  # short/medium/long + straight/wavy/curly + specific style
    hair_texture: str = ""  # smooth/fluffy/sleek/messy

    # 眼睛
    eye_color: str = ""  # brown/blue/green/gray/hazel/amber/heterochromia
    eye_shape: str = ""  # round/almond/hooded/monolid/upturned/downturned
    eye_size: str = ""  # large/medium/small

    # 其他面部特征
    nose: str = ""  # small/medium/large + shape
    lips: str = ""  # thin/medium/full
    eyebrows: str = ""  # thick/thin/arched/straight

    # 特殊标记
    distinctive_marks: List[str] = field(default_factory=list)  # scars/moles/freckles/birthmarks


@dataclass
class AnimalFeatures:
    """动物特征"""
    species: str = ""  # cat/dog/rabbit/bird/etc
    breed: str = ""  # specific breed if applicable

    # 毛发/皮肤
    fur_color: str = ""  # primary color
    fur_pattern: str = ""  # solid/tabby/spotted/striped/calico/etc
    fur_length: str = ""  # short/medium/long/fluffy
    fur_texture: str = ""  # smooth/fluffy/curly/wiry

    # 体型
    body_size: str = ""  # tiny/small/medium/large/huge
    body_shape: str = ""  # slim/stocky/round/muscular

    # 面部
    eye_color: str = ""
    eye_shape: str = ""  # round/almond/slanted
    nose_color: str = ""  # pink/black/brown
    ear_shape: str = ""  # pointed/floppy/round/tall

    # 特殊特征
    tail: str = ""  # long/short/fluffy/curled/bushy
    distinctive_marks: List[str] = field(default_factory=list)


@dataclass
class Clothing:
    """服装描述"""
    top: str = ""  # shirt/dress/jacket type and color
    bottom: str = ""  # pants/skirt type and color
    footwear: str = ""  # shoes/boots type and color
    accessories: List[str] = field(default_factory=list)  # hat/glasses/jewelry/bag
    style: str = ""  # casual/formal/sporty/vintage/fantasy


@dataclass
class Character:
    """完整角色定义"""
    # 基本信息
    id: str  # 唯一标识符 char_001
    name: str  # 角色名字
    name_en: str  # 英文名（用于图像生成）
    role: str  # protagonist/supporting/background
    character_type: CharacterType
    gender: Gender
    age_appearance: str  # child/teen/young_adult/adult/middle_aged/elderly

    # 物理特征（根据类型选择）
    physical: Optional[PhysicalFeatures] = None
    animal: Optional[AnimalFeatures] = None

    # 服装（如果适用）
    clothing: Optional[Clothing] = None

    # 性格/表情倾向（影响默认表情）
    personality_visual: str = ""  # cheerful/serious/shy/energetic/calm
    default_expression: str = ""  # smiling/neutral/determined/gentle

    # 额外描述
    extra_details: str = ""

    def to_image_prompt(self, include_clothing: bool = True) -> str:
        """
        生成用于图像生成的角色描述文本

        Returns:
            极度详细的英文角色描述，确保一致性
        """
        parts = []

        # 角色名称和基本信息
        parts.append(f"[CHARACTER: {self.name_en}]")

        if self.character_type == CharacterType.HUMAN:
            parts.append(self._human_description())
        elif self.character_type == CharacterType.ANIMAL:
            parts.append(self._animal_description())
        else:
            parts.append(self._generic_description())

        # 服装
        if include_clothing and self.clothing:
            parts.append(self._clothing_description())

        # 额外细节
        if self.extra_details:
            parts.append(f"Additional details: {self.extra_details}")

        return " ".join(parts)

    def _human_description(self) -> str:
        """生成人类角色描述"""
        if not self.physical:
            return f"A {self.age_appearance} {self.gender.value}"

        p = self.physical
        parts = []

        # 基本描述
        parts.append(f"A {self.age_appearance} {self.gender.value}")

        # 体型
        if p.height or p.build:
            body = " ".join(filter(None, [p.height, p.build]))
            parts.append(f"with {body} build")

        # 皮肤
        if p.skin_tone:
            parts.append(f"{p.skin_tone} skin")

        # 面部
        if p.face_shape:
            parts.append(f"{p.face_shape} face")

        # 头发 - 详细描述
        hair_parts = []
        if p.hair_length or p.hair_style:
            hair_parts.append(p.hair_length or "")
            hair_parts.append(p.hair_style or "")
        if p.hair_color:
            hair_parts.append(f"{p.hair_color} hair")
        if p.hair_texture:
            hair_parts.append(f"({p.hair_texture})")
        if hair_parts:
            parts.append(" ".join(filter(None, hair_parts)))

        # 眼睛 - 详细描述
        eye_parts = []
        if p.eye_size:
            eye_parts.append(p.eye_size)
        if p.eye_shape:
            eye_parts.append(p.eye_shape)
        if p.eye_color:
            eye_parts.append(f"{p.eye_color} eyes")
        if eye_parts:
            parts.append(" ".join(filter(None, eye_parts)))

        # 其他面部特征
        if p.eyebrows:
            parts.append(f"{p.eyebrows} eyebrows")
        if p.nose:
            parts.append(f"{p.nose} nose")
        if p.lips:
            parts.append(f"{p.lips} lips")

        # 特殊标记
        if p.distinctive_marks:
            parts.append(f"with {', '.join(p.distinctive_marks)}")

        # 表情
        if self.default_expression:
            parts.append(f"({self.default_expression} expression)")

        return ", ".join(parts)

    def _animal_description(self) -> str:
        """生成动物角色描述"""
        if not self.animal:
            return f"A {self.name_en}"

        a = self.animal
        parts = []

        # 基本描述
        species_desc = f"{a.breed} {a.species}" if a.breed else a.species
        parts.append(f"A {a.body_size} {species_desc}")

        # 毛发 - 极度详细
        fur_parts = []
        if a.fur_length:
            fur_parts.append(a.fur_length)
        if a.fur_texture:
            fur_parts.append(a.fur_texture)
        if a.fur_color:
            fur_parts.append(f"{a.fur_color}")
        if a.fur_pattern and a.fur_pattern != "solid":
            fur_parts.append(f"{a.fur_pattern} pattern")
        fur_parts.append("fur")
        parts.append(" ".join(fur_parts))

        # 体型
        if a.body_shape:
            parts.append(f"{a.body_shape} body")

        # 眼睛
        eye_parts = []
        if a.eye_shape:
            eye_parts.append(a.eye_shape)
        if a.eye_color:
            eye_parts.append(f"{a.eye_color} eyes")
        if eye_parts:
            parts.append(" ".join(eye_parts))

        # 鼻子
        if a.nose_color:
            parts.append(f"{a.nose_color} nose")

        # 耳朵
        if a.ear_shape:
            parts.append(f"{a.ear_shape} ears")

        # 尾巴
        if a.tail:
            parts.append(f"{a.tail} tail")

        # 特殊标记
        if a.distinctive_marks:
            parts.append(f"with {', '.join(a.distinctive_marks)}")

        # 表情
        if self.default_expression:
            parts.append(f"({self.default_expression} expression)")

        return ", ".join(parts)

    def _generic_description(self) -> str:
        """通用角色描述"""
        return self.extra_details or f"A {self.name_en}"

    def _clothing_description(self) -> str:
        """服装描述"""
        if not self.clothing:
            return ""

        c = self.clothing
        parts = ["Wearing:"]

        if c.top:
            parts.append(c.top)
        if c.bottom:
            parts.append(c.bottom)
        if c.footwear:
            parts.append(c.footwear)
        if c.accessories:
            parts.append(f"accessories: {', '.join(c.accessories)}")
        if c.style:
            parts.append(f"({c.style} style)")

        return " ".join(parts)


@dataclass
class SceneStyle:
    """场景独立风格 - 随剧情变化"""
    color_palette: str = ""  # warm/cool/dark/golden/muted/vibrant
    lighting: str = ""  # soft/dramatic/dim/harsh/ethereal/natural
    atmosphere: str = ""  # cozy/tense/melancholic/hopeful/triumphant/mysterious
    weather: str = ""  # clear/cloudy/rainy/stormy/foggy/snowy
    time_of_day: str = ""  # dawn/morning/noon/afternoon/golden_hour/dusk/night/midnight

    def to_style_prompt(self) -> str:
        """生成场景风格描述"""
        parts = []

        if self.color_palette:
            parts.append(f"{self.color_palette} color palette")
        if self.lighting:
            parts.append(f"{self.lighting} lighting")
        if self.atmosphere:
            parts.append(f"{self.atmosphere} atmosphere")
        if self.weather and self.weather != "clear":
            parts.append(f"{self.weather} weather")
        if self.time_of_day:
            parts.append(f"{self.time_of_day}")

        return ", ".join(parts) if parts else ""


@dataclass
class VisualStyle:
    """全局视觉风格定义 - 整个故事保持一致的艺术风格"""
    # 整体风格（全局一致）
    art_style: str = ""  # illustration/anime/realistic/watercolor/oil_painting/3d_render
    rendering: str = ""  # soft/sharp/painterly/cel_shaded
    detail_level: str = ""  # high/medium/stylized

    # 以下为默认值，可被场景风格覆盖
    color_palette: str = ""  # warm/cool/neutral/vibrant/muted/pastel
    primary_colors: List[str] = field(default_factory=list)  # main colors used
    mood_colors: str = ""  # golden hour/blue hour/neutral daylight

    # 光线
    lighting: str = ""  # soft/dramatic/natural/studio/backlit
    light_source: str = ""  # sunlight/moonlight/artificial/ambient
    time_of_day: str = ""  # dawn/morning/noon/afternoon/dusk/night

    # 氛围
    atmosphere: str = ""  # warm/cozy/mysterious/energetic/melancholic/peaceful
    mood: str = ""  # happy/sad/tense/relaxing/exciting

    # 技术参数
    texture: str = ""  # smooth/textured/grainy

    def to_style_prompt(self, scene_style: Optional[SceneStyle] = None) -> str:
        """
        生成风格描述文本

        Args:
            scene_style: 场景独立风格，会覆盖全局默认值
        """
        parts = []

        parts.append("[VISUAL STYLE]")

        # 全局艺术风格（始终一致）
        if self.art_style:
            parts.append(f"Art style: {self.art_style}")
        if self.rendering:
            parts.append(f"{self.rendering} rendering")

        # 颜色 - 场景风格优先
        color_palette = scene_style.color_palette if scene_style and scene_style.color_palette else self.color_palette
        color_parts = []
        if color_palette:
            color_parts.append(f"{color_palette} color palette")
        if self.primary_colors:
            color_parts.append(f"featuring {', '.join(self.primary_colors)}")
        if color_parts:
            parts.append("Colors: " + ", ".join(color_parts))

        # 光线 - 场景风格优先
        lighting = scene_style.lighting if scene_style and scene_style.lighting else self.lighting
        time_of_day = scene_style.time_of_day if scene_style and scene_style.time_of_day else self.time_of_day
        light_parts = []
        if lighting:
            light_parts.append(f"{lighting} lighting")
        if self.light_source:
            light_parts.append(f"from {self.light_source}")
        if time_of_day:
            light_parts.append(f"({time_of_day})")
        if light_parts:
            parts.append("Lighting: " + " ".join(light_parts))

        # 氛围 - 场景风格优先
        atmosphere = scene_style.atmosphere if scene_style and scene_style.atmosphere else self.atmosphere
        if atmosphere or self.mood:
            atm = " ".join(filter(None, [atmosphere, self.mood]))
            parts.append(f"Atmosphere: {atm}")

        # 天气（仅场景风格）
        if scene_style and scene_style.weather and scene_style.weather not in ["clear", ""]:
            parts.append(f"Weather: {scene_style.weather}")

        # 技术
        if self.detail_level or self.texture:
            tech = " ".join(filter(None, [self.detail_level, self.texture]))
            parts.append(f"Quality: {tech} detail")

        return ", ".join(parts)


class CharacterConsistencyManager:
    """
    角色一致性管理器

    负责：
    1. 存储和管理故事中的所有角色
    2. 为每个场景生成包含角色描述的完整prompt
    3. 管理角色参考图（方案B）
    """

    MAX_CHARACTERS = 10

    def __init__(self):
        self.characters: Dict[str, Character] = {}
        self.visual_style: Optional[VisualStyle] = None
        self.reference_images: Dict[str, any] = {}  # char_id -> PIL Image

    def add_character(self, character: Character) -> bool:
        """添加角色"""
        if len(self.characters) >= self.MAX_CHARACTERS:
            logger.warning(
                f"[CharacterConsistency] add_character rejected: MAX_CHARACTERS={self.MAX_CHARACTERS} reached, "
                f"cannot add {character.id} ({character.name_en})"
            )
            return False
        self.characters[character.id] = character
        logger.info(
            f"[CharacterConsistency] add_character: {character.id} ({character.name_en}), "
            f"type={character.char_type.value}, total={len(self.characters)}"
        )
        return True

    def get_character(self, char_id: str) -> Optional[Character]:
        """获取角色"""
        return self.characters.get(char_id)

    def set_visual_style(self, style: VisualStyle):
        """设置视觉风格"""
        self.visual_style = style
        logger.info(
            f"[CharacterConsistency] set_visual_style: art_style={style.art_style}, "
            f"rendering={style.rendering}, atmosphere={style.atmosphere}"
        )

    def set_reference_image(self, char_id: str, image) -> bool:
        """设置角色参考图（方案B）"""
        if char_id not in self.characters:
            logger.warning(f"[CharacterConsistency] set_reference_image: char_id={char_id} not found in characters")
            return False
        self.reference_images[char_id] = image
        logger.info(f"[CharacterConsistency] set_reference_image: {char_id} reference image registered")
        return True

    def build_scene_prompt(
        self,
        scene_description: str,
        character_ids: List[str],
        character_actions: Dict[str, str] = None,
        include_style: bool = True,
        scene_style: Optional[SceneStyle] = None
    ) -> str:
        """
        构建完整的场景prompt

        Args:
            scene_description: 场景描述（环境、动作等）
            character_ids: 出现在场景中的角色ID列表
            character_actions: 角色特定动作 {char_id: "running", ...}
            include_style: 是否包含风格描述
            scene_style: 场景独立风格（可覆盖全局风格的部分属性）

        Returns:
            完整的图像生成prompt
        """
        resolved_chars = [cid for cid in character_ids if cid in self.characters]
        missing_chars = [cid for cid in character_ids if cid not in self.characters]
        if missing_chars:
            logger.warning(
                f"[CharacterConsistency] build_scene_prompt: char_ids not found in registry: {missing_chars}"
            )
        logger.info(
            f"[CharacterConsistency] build_scene_prompt: {len(resolved_chars)} chars resolved "
            f"({resolved_chars}), include_style={include_style}"
        )

        parts = []

        # 1. 视觉风格（放在最前面，设定整体基调）
        # 场景风格会覆盖全局风格的色调、光线、氛围
        if include_style and self.visual_style:
            parts.append(self.visual_style.to_style_prompt(scene_style))

        # 2. 角色描述（按出场顺序）
        parts.append("\n[CHARACTERS IN SCENE]")
        for i, char_id in enumerate(character_ids[:self.MAX_CHARACTERS]):
            char = self.characters.get(char_id)
            if char:
                char_prompt = char.to_image_prompt()
                # 添加特定动作/表情
                if character_actions and char_id in character_actions:
                    char_prompt += f" - Action: {character_actions[char_id]}"
                parts.append(f"{i+1}. {char_prompt}")

        # 3. 场景描述
        parts.append(f"\n[SCENE]\n{scene_description}")

        # 4. 一致性强调
        parts.append("\n[CONSISTENCY REQUIREMENTS]")
        parts.append("- Maintain exact character appearances as described above")
        parts.append("- Keep consistent art style throughout")
        parts.append("- Ensure proper character proportions and features")

        return "\n".join(parts)

    def get_reference_images_for_scene(self, character_ids: List[str]) -> List:
        """获取场景中角色的参考图（方案B）"""
        images = []
        for char_id in character_ids:
            if char_id in self.reference_images:
                images.append(self.reference_images[char_id])
        logger.info(
            f"[CharacterConsistency] get_reference_images_for_scene: "
            f"requested={len(character_ids)} chars, found={len(images)} ref images"
        )
        return images

    def export_character_sheet(self) -> str:
        """导出角色设定表（用于文档）"""
        lines = ["# Character Sheet\n"]

        for char_id, char in self.characters.items():
            lines.append(f"## {char.name} ({char.name_en})")
            lines.append(f"- ID: {char_id}")
            lines.append(f"- Role: {char.role}")
            lines.append(f"- Type: {char.character_type.value}")
            lines.append(f"\n**Visual Description:**")
            lines.append(f"```\n{char.to_image_prompt()}\n```\n")

        if self.visual_style:
            lines.append("## Visual Style")
            lines.append(f"```\n{self.visual_style.to_style_prompt()}\n```")

        return "\n".join(lines)


def create_character_from_dict(data: dict) -> Character:
    """
    从字典创建Character对象

    用于从故事生成API的JSON输出创建角色
    """
    char_type = CharacterType(data.get("type", "other"))

    # 创建物理特征
    physical = None
    animal = None

    if char_type == CharacterType.HUMAN:
        phys_data = data.get("physical", {})
        physical = PhysicalFeatures(
            height=phys_data.get("height", ""),
            build=phys_data.get("build", ""),
            skin_tone=phys_data.get("skin_tone", ""),
            face_shape=phys_data.get("face_shape", ""),
            hair_color=phys_data.get("hair_color", ""),
            hair_style=phys_data.get("hair_style", ""),
            hair_texture=phys_data.get("hair_texture", ""),
            eye_color=phys_data.get("eye_color", ""),
            eye_shape=phys_data.get("eye_shape", ""),
            eye_size=phys_data.get("eye_size", ""),
            nose=phys_data.get("nose", ""),
            lips=phys_data.get("lips", ""),
            eyebrows=phys_data.get("eyebrows", ""),
            distinctive_marks=phys_data.get("distinctive_marks", [])
        )
    elif char_type == CharacterType.ANIMAL:
        anim_data = data.get("animal", {})
        animal = AnimalFeatures(
            species=anim_data.get("species", ""),
            breed=anim_data.get("breed", ""),
            fur_color=anim_data.get("fur_color", ""),
            fur_pattern=anim_data.get("fur_pattern", ""),
            fur_length=anim_data.get("fur_length", ""),
            fur_texture=anim_data.get("fur_texture", ""),
            body_size=anim_data.get("body_size", ""),
            body_shape=anim_data.get("body_shape", ""),
            eye_color=anim_data.get("eye_color", ""),
            eye_shape=anim_data.get("eye_shape", ""),
            nose_color=anim_data.get("nose_color", ""),
            ear_shape=anim_data.get("ear_shape", ""),
            tail=anim_data.get("tail", ""),
            distinctive_marks=anim_data.get("distinctive_marks", [])
        )

    # 服装
    clothing = None
    cloth_data = data.get("clothing")
    if cloth_data:
        clothing = Clothing(
            top=cloth_data.get("top", ""),
            bottom=cloth_data.get("bottom", ""),
            footwear=cloth_data.get("footwear", ""),
            accessories=cloth_data.get("accessories", []),
            style=cloth_data.get("style", "")
        )

    return Character(
        id=data.get("id", f"char_{data.get('name', 'unknown')}"),
        name=data.get("name", ""),
        name_en=data.get("name_en", data.get("name", "")),
        role=data.get("role", "supporting"),
        character_type=char_type,
        gender=Gender(data.get("gender", "unknown")),
        age_appearance=data.get("age_appearance", ""),
        physical=physical,
        animal=animal,
        clothing=clothing,
        personality_visual=data.get("personality_visual", ""),
        default_expression=data.get("default_expression", ""),
        extra_details=data.get("extra_details", "")
    )


def create_style_from_dict(data: dict) -> VisualStyle:
    """从字典创建VisualStyle对象"""
    return VisualStyle(
        art_style=data.get("art_style", ""),
        rendering=data.get("rendering", ""),
        color_palette=data.get("color_palette", ""),
        primary_colors=data.get("primary_colors", []),
        mood_colors=data.get("mood_colors", ""),
        lighting=data.get("lighting", ""),
        light_source=data.get("light_source", ""),
        time_of_day=data.get("time_of_day", ""),
        atmosphere=data.get("atmosphere", ""),
        mood=data.get("mood", ""),
        detail_level=data.get("detail_level", ""),
        texture=data.get("texture", "")
    )


def create_scene_style_from_dict(data: dict) -> Optional[SceneStyle]:
    """从场景数据中的scene_style字段创建SceneStyle对象"""
    if not data:
        return None
    return SceneStyle(
        color_palette=data.get("color_palette", ""),
        lighting=data.get("lighting", ""),
        atmosphere=data.get("atmosphere", ""),
        weather=data.get("weather", ""),
        time_of_day=data.get("time_of_day", "")
    )
