"""
角色类型系统 - 支持多元角色类型

支持 18 种角色类型：
- human: 人类
- animal: 动物（真实动物，无服装，四足）
- anthropomorphic_animal: 拟人化动物（有意识、穿服装、两足站立，但保留物种特征）
- fantasy_creature: 奇幻生物
- robot: 机器人/AI
- object_personified: 拟人化物品
- hybrid: 混合类型
- insect: 昆虫
- aquatic: 水生生物
- plant: 植物
- mythological: 神话生物
- supernatural: 超自然存在
- undead: 亡灵
- elemental: 元素生物
- alien: 外星生物
- vehicle_character: 载具角色
- digital_virtual: 数字/虚拟
- concept_personified: 概念拟人
- miniature: 微型角色
- giant: 巨型角色
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel


class CharacterType(str, Enum):
    """角色类型枚举 - 18种类型"""
    # 基础类型
    HUMAN = "human"
    ANIMAL = "animal"
    ANTHROPOMORPHIC_ANIMAL = "anthropomorphic_animal"
    FANTASY_CREATURE = "fantasy_creature"
    ROBOT = "robot"
    OBJECT_PERSONIFIED = "object"
    HYBRID = "hybrid"

    # 扩展类型
    INSECT = "insect"
    AQUATIC = "aquatic"
    PLANT = "plant"
    MYTHOLOGICAL = "mythological"
    SUPERNATURAL = "supernatural"
    UNDEAD = "undead"
    ELEMENTAL = "elemental"
    ALIEN = "alien"
    VEHICLE_CHARACTER = "vehicle_character"
    DIGITAL_VIRTUAL = "digital_virtual"
    CONCEPT_PERSONIFIED = "concept_personified"
    MINIATURE = "miniature"
    GIANT = "giant"


# ============================================================
# 基础类型 Appearance 模型
# ============================================================

class HumanAppearance(BaseModel):
    """人类角色外观"""
    age_range: str = ""                   # "child", "teen", "young_adult", "middle_aged", "elderly"
    gender: str = ""                      # "male", "female", "androgynous"
    ethnicity: Optional[str] = None       # 可选，尊重多样性
    body_type: str = ""                   # "slim", "average", "athletic", "heavy"
    height: str = ""                      # "short", "average", "tall"

    # 面部特征
    face_shape: str = ""
    skin_tone: str = ""
    eye_color: str = ""
    eye_shape: Optional[str] = None

    # 发型
    hair_color: str = ""
    hair_length: str = ""                 # "bald", "short", "medium", "long"
    hair_style: str = ""                  # "straight", "wavy", "curly", "braided"

    # 服装（重要！）
    clothing_style: str = ""              # "casual", "formal", "traditional", "futuristic"
    clothing_description: str = ""        # 具体服装描述

    # 独特标记
    distinctive_features: List[str] = []  # 疤痕、纹身、眼镜、饰品等


class AnimalAppearance(BaseModel):
    """动物角色外观"""
    species: str = ""                     # "bird", "mammal", "reptile"
    breed: str = ""                       # 具体品种
    fur_color: str = ""
    fur_pattern: Optional[str] = None     # 花纹
    fur_length: Optional[str] = None
    fur_texture: Optional[str] = None
    body_size: str = ""                   # "tiny", "small", "medium", "large"
    body_shape: str = ""
    eye_color: str = ""
    eye_shape: Optional[str] = None
    nose_color: Optional[str] = None
    ear_shape: Optional[str] = None
    tail: Optional[str] = None
    distinctive_marks: List[str] = []


class FantasyCreatureAppearance(BaseModel):
    """奇幻生物外观（精灵、妖精、矮人等）"""
    creature_type: str = ""               # "elf", "dwarf", "fairy", "ogre", "troll"
    base_form: str = ""                   # 基础形态描述
    skin_texture: str = ""                # "smooth", "rough", "glowing"
    color_scheme: str = ""
    special_features: List[str] = []      # 尖耳朵、翅膀、光环等
    size_category: str = ""
    distinctive_marks: List[str] = []


class RobotAppearance(BaseModel):
    """机器人角色外观"""
    robot_type: str = ""                  # "humanoid", "mecha", "drone", "android"
    material: str = ""                    # "metal", "plastic", "organic_hybrid"
    color_scheme: str = ""
    body_shape: str = ""
    size_category: str = ""
    special_features: List[str] = []      # 天线、发光部件、武器等
    era_style: str = ""                   # "retro", "modern", "futuristic"


class ObjectAppearance(BaseModel):
    """拟人化物品外观"""
    object_type: str = ""                 # "furniture", "appliance", "toy", "food"
    base_object: str = ""                 # 具体物品名称
    material: str = ""
    color_scheme: str = ""
    face_location: str = ""               # 脸部在物品上的位置
    limb_style: str = ""                  # 四肢的表现方式
    size_category: str = ""
    distinctive_features: List[str] = []


class HybridAppearance(BaseModel):
    """混合类型外观（如半人半兽）"""
    primary_type: str = ""                # 主要类型
    secondary_type: str = ""              # 次要类型
    human_parts: List[str] = []           # 人类部分
    non_human_parts: List[str] = []       # 非人类部分
    blend_style: str = ""                 # "merged", "split", "transformed"
    color_scheme: str = ""
    distinctive_features: List[str] = []


# ============================================================
# 扩展类型 Appearance 模型
# ============================================================

class InsectAppearance(BaseModel):
    """昆虫角色外观"""
    species: str = ""                     # "bee", "butterfly", "ant", "firefly", "beetle"
    wing_type: str = ""                   # "transparent", "colorful", "shell_covered", "none"
    wing_pattern: Optional[str] = None
    antennae: str = ""                    # "long", "short", "feathered", "clubbed"
    body_segments: str = ""               # "distinct", "fused", "elongated"
    exoskeleton_color: str = ""
    exoskeleton_pattern: Optional[str] = None
    compound_eyes: str = ""               # "large", "small", "glowing"
    eye_color: str = ""
    leg_count: int = 6
    body_size: str = ""                   # "tiny", "small", "medium"
    special_features: List[str] = []      # stinger, pincers, glowing abdomen
    distinctive_marks: List[str] = []


class AquaticAppearance(BaseModel):
    """水生生物角色外观"""
    species: str = ""                     # "fish", "octopus", "dolphin", "mermaid", "seahorse"
    body_type: str = ""                   # "streamlined", "round", "elongated", "humanoid"
    fin_type: str = ""                    # "dorsal", "pectoral", "caudal", "flowing"
    fin_color: Optional[str] = None
    scale_pattern: str = ""               # "shimmering", "spotted", "striped", "smooth"
    scale_color: str = ""
    tentacles: Optional[str] = None       # for octopus, jellyfish
    tail_shape: str = ""                  # "forked", "rounded", "fan", "mermaid"
    gills: str = ""                       # "visible", "hidden", "decorative"
    eye_type: str = ""                    # "large", "small", "bioluminescent"
    eye_color: str = ""
    bioluminescence: Optional[str] = None # 发光部位
    body_size: str = ""
    distinctive_marks: List[str] = []


class PlantAppearance(BaseModel):
    """植物角色外观"""
    plant_type: str = ""                  # "tree", "flower", "mushroom", "vine", "grass"
    species: str = ""                     # 具体物种
    leaf_shape: str = ""                  # "broad", "needle", "heart", "fan"
    leaf_color: str = ""
    flower_color: Optional[str] = None
    flower_type: Optional[str] = None
    bark_texture: Optional[str] = None    # for trees
    bark_color: Optional[str] = None
    root_visible: bool = False            # 根部是否可见
    root_style: Optional[str] = None      # 根部风格
    face_location: str = ""               # 面部位置
    limb_style: str = ""                  # 枝干作为四肢的方式
    height_category: str = ""             # "tiny", "small", "medium", "tall", "giant"
    seasonal_state: str = ""              # "spring", "summer", "autumn", "winter", "evergreen"
    special_features: List[str] = []      # 果实、花朵、藤蔓等
    distinctive_marks: List[str] = []


class MythologicalAppearance(BaseModel):
    """神话生物外观（龙、凤凰、麒麟、独角兽等）"""
    creature_type: str = ""               # "dragon", "phoenix", "unicorn", "qilin", "nine_tailed_fox"
    origin_culture: str = ""              # "chinese", "western", "japanese", "norse", "greek"
    base_form: str = ""                   # 基础形态
    body_size: str = ""                   # "small", "medium", "large", "colossal"
    color_scheme: str = ""
    skin_type: str = ""                   # "scales", "feathers", "fur", "ethereal"
    mythical_powers: List[str] = []       # 神话能力的视觉表现
    sacred_symbols: List[str] = []        # 神圣符号
    aura: Optional[str] = None            # 光环/气场
    wing_type: Optional[str] = None
    horn_type: Optional[str] = None
    tail_type: Optional[str] = None
    eye_style: str = ""                   # "wise", "fierce", "ancient", "glowing"
    distinctive_marks: List[str] = []


class SupernaturalAppearance(BaseModel):
    """超自然存在外观（神仙、天使、恶魔、精灵）"""
    being_type: str = ""                  # "deity", "angel", "demon", "spirit", "yokai"
    origin_culture: Optional[str] = None
    base_form: str = ""                   # "humanoid", "ethereal", "shapeless"
    aura_color: str = ""                  # 气场颜色
    aura_intensity: str = ""              # "subtle", "moderate", "intense", "blinding"
    supernatural_features: List[str] = [] # 翅膀、光环、角、多臂等
    skin_appearance: str = ""             # "normal", "glowing", "translucent", "marked"
    skin_color: str = ""
    eye_type: str = ""                    # "normal", "glowing", "no_pupils", "multiple"
    eye_color: str = ""
    ethereal_quality: str = ""            # "solid", "semi_transparent", "wispy"
    clothing_style: str = ""              # "robes", "armor", "flowing", "none"
    accessories: List[str] = []           # 法器、武器、饰品
    distinctive_marks: List[str] = []


class UndeadAppearance(BaseModel):
    """亡灵角色外观"""
    undead_type: str = ""                 # "ghost", "zombie", "skeleton", "vampire", "lich"
    original_form: str = ""               # 生前形态
    decay_level: str = ""                 # "none", "minor", "moderate", "severe", "skeletal"
    ghostly_transparency: str = ""        # "opaque", "semi_transparent", "very_transparent"
    ghostly_color: str = ""               # 幽灵色调
    undead_features: List[str] = []       # 腐烂、骨骼外露、空洞眼眶等
    glow_color: Optional[str] = None      # 发光颜色（如眼睛）
    clothing_state: str = ""              # "intact", "tattered", "ancient", "none"
    accessories: List[str] = []           # 锁链、墓碑碎片等
    atmosphere: str = ""                  # "eerie", "menacing", "tragic", "peaceful"
    distinctive_marks: List[str] = []


class ElementalAppearance(BaseModel):
    """元素生物外观"""
    element_type: str = ""                # "fire", "water", "ice", "earth", "air", "lightning", "nature"
    material_form: str = ""               # "solid", "liquid", "gas", "energy", "mixed"
    energy_color: str = ""                # 能量颜色
    secondary_color: Optional[str] = None
    body_shape: str = ""                  # "humanoid", "amorphous", "creature", "geometric"
    size_category: str = ""
    surface_texture: str = ""             # "flames", "waves", "crystals", "swirling"
    core_visible: bool = False            # 是否有可见核心
    core_appearance: Optional[str] = None
    particle_effects: List[str] = []      # 火花、水滴、闪电等粒子效果
    intensity_level: str = ""             # "calm", "active", "raging"
    distinctive_marks: List[str] = []


class AlienAppearance(BaseModel):
    """外星生物外观"""
    home_planet_type: str = ""            # "desert", "ocean", "gas_giant", "ice", "jungle"
    body_plan: str = ""                   # "humanoid", "insectoid", "cephalopod", "amorphous"
    limb_count: int = 4
    limb_type: str = ""                   # "arms", "tentacles", "wings", "appendages"
    sensory_organs: List[str] = []        # 眼睛类型、触角、其他感官器官
    eye_count: int = 2
    eye_appearance: str = ""
    skin_texture: str = ""                # "smooth", "scaly", "chitinous", "gelatinous"
    skin_color: str = ""
    skin_pattern: Optional[str] = None
    special_adaptations: List[str] = []   # 特殊适应性特征
    technology_integrated: bool = False   # 是否有整合科技
    size_category: str = ""
    distinctive_marks: List[str] = []


class VehicleCharacterAppearance(BaseModel):
    """载具角色外观（如《汽车总动员》风格）"""
    vehicle_type: str = ""                # "car", "truck", "airplane", "boat", "train", "spaceship"
    vehicle_subtype: str = ""             # 具体型号/类型
    body_color: str = ""
    secondary_color: Optional[str] = None
    paint_finish: str = ""                # "glossy", "matte", "metallic", "rusty"
    decals_markings: List[str] = []       # 贴纸、涂装
    headlight_eyes: str = ""              # 车灯作为眼睛的风格
    eye_color: str = ""
    mouth_location: str = ""              # 嘴巴位置（格栅、保险杠等）
    wheel_count: int = 4
    wheel_style: str = ""
    size_category: str = ""
    era_style: str = ""                   # "vintage", "modern", "futuristic"
    personality_accessories: List[str] = [] # 帽子、眼镜等个性化配件
    distinctive_marks: List[str] = []


class DigitalVirtualAppearance(BaseModel):
    """数字/虚拟角色外观"""
    digital_type: str = ""                # "ai", "virtual_idol", "hologram", "game_npc", "avatar"
    base_form: str = ""                   # "humanoid", "abstract", "geometric", "data_stream"
    digital_aesthetic: str = ""           # "clean", "glitchy", "retro_pixel", "neon", "minimal"
    primary_color: str = ""
    accent_color: str = ""
    glitch_effects: List[str] = []        # 故障效果
    hologram_color: str = ""              # 全息投影颜色
    transparency_level: str = ""          # "solid", "semi_transparent", "wireframe"
    interface_elements: List[str] = []    # UI元素、代码、数据流
    pixel_resolution: Optional[str] = None # for pixel style
    scan_lines: bool = False
    glow_effects: List[str] = []
    distinctive_marks: List[str] = []


class ConceptPersonifiedAppearance(BaseModel):
    """概念拟人外观（时间、死神、爱神等）"""
    concept_type: str = ""                # "time", "death", "love", "justice", "season", "emotion"
    personification_style: str = ""       # "classical", "modern", "abstract", "symbolic"
    base_form: str = ""                   # 基础形态
    symbolic_objects: List[str] = []      # 象征物品（镰刀、沙漏、天平等）
    abstract_features: List[str] = []     # 抽象特征
    color_symbolism: str = ""             # 象征性颜色
    aura_effect: Optional[str] = None
    clothing_style: str = ""
    facial_features: str = ""             # "visible", "obscured", "mask", "none"
    body_type: str = ""
    movement_style: str = ""              # "floating", "walking", "teleporting"
    distinctive_marks: List[str] = []


class MiniatureAppearance(BaseModel):
    """微型角色外观"""
    base_type: str = ""                   # "human", "fairy", "borrower", "thumbelina"
    scale_ratio: str = ""                 # "ant_sized", "thumb_sized", "hand_sized"
    size_reference_object: str = ""       # 参照物（如"站在茶杯旁"）
    body_proportions: str = ""            # "normal", "chibi", "exaggerated"
    clothing_style: str = ""
    clothing_material: str = ""           # 微型服装材料
    tools_items: List[str] = []           # 微型工具/物品
    skin_color: str = ""
    hair_style: str = ""
    hair_color: str = ""
    eye_style: str = ""                   # "large", "normal", "button"
    distinctive_marks: List[str] = []


class GiantAppearance(BaseModel):
    """巨型角色外观"""
    giant_type: str = ""                  # "humanoid_giant", "titan", "kaiju", "colossus"
    height_category: str = ""             # "large", "huge", "colossal", "mountainous"
    scale_reference: str = ""             # 参照物（如"比大楼还高"）
    body_build: str = ""                  # "muscular", "fat", "lanky", "massive"
    skin_type: str = ""                   # "human_like", "rocky", "mossy", "armored"
    skin_color: str = ""
    facial_features: str = ""
    eye_style: str = ""
    clothing_style: str = ""              # "primitive", "armored", "none", "tattered"
    weapons_tools: List[str] = []
    environmental_effects: List[str] = [] # 走路引起地震等
    distinctive_marks: List[str] = []


# ============================================================
# 通用角色模型
# ============================================================

class Character(BaseModel):
    """通用角色模型 - 支持所有角色类型"""
    id: str
    name: str
    name_en: Optional[str] = None
    character_type: Optional[CharacterType] = None

    # 基础类型外观
    human: Optional[HumanAppearance] = None
    animal: Optional[AnimalAppearance] = None
    fantasy_creature: Optional[FantasyCreatureAppearance] = None
    robot: Optional[RobotAppearance] = None
    object_personified: Optional[ObjectAppearance] = None
    hybrid: Optional[HybridAppearance] = None

    # 扩展类型外观
    insect: Optional[InsectAppearance] = None
    aquatic: Optional[AquaticAppearance] = None
    plant: Optional[PlantAppearance] = None
    mythological: Optional[MythologicalAppearance] = None
    supernatural: Optional[SupernaturalAppearance] = None
    undead: Optional[UndeadAppearance] = None
    elemental: Optional[ElementalAppearance] = None
    alien: Optional[AlienAppearance] = None
    vehicle_character: Optional[VehicleCharacterAppearance] = None
    digital_virtual: Optional[DigitalVirtualAppearance] = None
    concept_personified: Optional[ConceptPersonifiedAppearance] = None
    miniature: Optional[MiniatureAppearance] = None
    giant: Optional[GiantAppearance] = None

    # 通用字段
    personality: Optional[str] = None
    personality_visual: Optional[str] = None
    default_expression: Optional[str] = None
    role_in_story: Optional[str] = None   # "protagonist", "antagonist", "supporting"
    extra_details: Optional[str] = None
    gender: Optional[str] = None
    age_appearance: Optional[str] = None


# 类型强制声明映射
CHARACTER_TYPE_DECLARATIONS = {
    CharacterType.HUMAN: "This is a HUMAN character.",
    CharacterType.ANIMAL: "This is an ANIMAL character, NOT a human.",
    CharacterType.ANTHROPOMORPHIC_ANIMAL: "This is an ANTHROPOMORPHIC ANIMAL — a sentient animal character with human-like consciousness, upright posture, and clothing, but retaining the species' natural features (fur, ears, tail, snout/beak). NOT a human. NOT a regular animal. Draw the species body with animal fur/feathers, animal face/snout/beak, animal ears and tail — but standing upright and wearing clothes.",
    CharacterType.FANTASY_CREATURE: "This is a FANTASY CREATURE.",
    CharacterType.ROBOT: "This is a ROBOT/MECHANICAL character.",
    CharacterType.OBJECT_PERSONIFIED: "This is a PERSONIFIED OBJECT with face and personality.",
    CharacterType.HYBRID: "This is a HYBRID character combining multiple forms.",
    CharacterType.INSECT: "This is an INSECT character, NOT a human or mammal.",
    CharacterType.AQUATIC: "This is an AQUATIC creature that lives in water.",
    CharacterType.PLANT: "This is a PLANT character, NOT an animal or human.",
    CharacterType.MYTHOLOGICAL: "This is a MYTHOLOGICAL creature from legend.",
    CharacterType.SUPERNATURAL: "This is a SUPERNATURAL being with otherworldly qualities.",
    CharacterType.UNDEAD: "This is an UNDEAD character.",
    CharacterType.ELEMENTAL: "This is an ELEMENTAL being made of pure element.",
    CharacterType.ALIEN: "This is an ALIEN creature from another world.",
    CharacterType.VEHICLE_CHARACTER: "This is a VEHICLE character with personality and face.",
    CharacterType.DIGITAL_VIRTUAL: "This is a DIGITAL/VIRTUAL character.",
    CharacterType.CONCEPT_PERSONIFIED: "This is a PERSONIFIED CONCEPT.",
    CharacterType.MINIATURE: "This is a MINIATURE character, very tiny compared to normal objects.",
    CharacterType.GIANT: "This is a GIANT character, enormous in scale.",
}


def get_type_declaration(char_type: str) -> str:
    """获取角色类型的强制声明"""
    try:
        enum_type = CharacterType(char_type)
        return CHARACTER_TYPE_DECLARATIONS.get(enum_type, "")
    except ValueError:
        return ""
