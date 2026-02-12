# 序话Story - 通用角色与风格一致性系统

## 设计目标

序话Story是面向大众创作者的AI漫剧生成工具，需要支持：
- **多元角色类型**：人类、动物、奇幻生物、机器人、拟人化物品等
- **多元视觉风格**：写实、卡通、赛博朋克、水墨、像素等
- **多元故事类型**：都市情感、古装武侠、科幻冒险、童话寓言等

一致性系统必须**通用化**，而非针对特定故事类型硬编码。

---

## 问题诊断

当前系统的一致性问题根源：

| 层级 | 问题 | 影响 |
|------|------|------|
| 角色描述 | 只用简短描述，缺失关键特征 | 同一角色外观帧间漂移 |
| 角色类型 | 没有明确角色是人/动物/其他 | AI混淆角色物种 |
| 角色筛选 | 群体场景漏掉角色 | 该出现的角色没画 |
| 参考图机制 | 测试脚本绕过了整套系统 | 一致性系统形同虚设 |
| 风格锁定 | 每帧独立生成，无全局风格约束 | 色调、光影风格跳跃 |

---

## 通用解决方案

### 一、角色类型系统

#### 1.1 角色类型枚举

```python
# app/models/character_types.py

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel

class CharacterType(str, Enum):
    HUMAN = "human"
    ANIMAL = "animal"
    FANTASY_CREATURE = "fantasy_creature"  # 龙、精灵、妖怪等
    ROBOT = "robot"                        # 机器人、AI、机甲
    OBJECT_PERSONIFIED = "object"          # 拟人化物品
    HYBRID = "hybrid"                      # 混合类型（如半人半兽）


class HumanAppearance(BaseModel):
    """人类角色外观"""
    age_range: str                    # "child", "teen", "young_adult", "middle_aged", "elderly"
    gender: str                       # "male", "female", "androgynous"
    ethnicity: Optional[str]          # 可选，尊重多样性
    body_type: str                    # "slim", "average", "athletic", "heavy"
    height: str                       # "short", "average", "tall"
    
    # 面部特征
    face_shape: str
    skin_tone: str
    eye_color: str
    eye_shape: Optional[str]
    
    # 发型
    hair_color: str
    hair_length: str                  # "bald", "short", "medium", "long"
    hair_style: str                   # "straight", "wavy", "curly", "braided"
    
    # 服装（重要！）
    clothing_style: str               # "casual", "formal", "traditional", "futuristic"
    clothing_description: str         # 具体服装描述
    
    # 独特标记
    distinctive_features: List[str]   # 疤痕、纹身、眼镜、饰品等


class AnimalAppearance(BaseModel):
    """动物角色外观"""
    species: str                      # "bird", "mammal", "reptile"
    breed: str                        # 具体品种
    fur_color: str
    fur_pattern: Optional[str]        # 花纹
    body_size: str                    # "tiny", "small", "medium", "large"
    body_shape: str
    eye_color: str
    distinctive_marks: List[str]


class FantasyCreatureAppearance(BaseModel):
    """奇幻生物外观"""
    creature_type: str                # "dragon", "elf", "demon", "fairy"
    base_form: str                    # 基础形态描述
    skin_texture: str                 # "scales", "fur", "smooth", "ethereal"
    color_scheme: str
    special_features: List[str]       # 翅膀、角、尾巴、光环等
    size_category: str
    distinctive_marks: List[str]


class RobotAppearance(BaseModel):
    """机器人角色外观"""
    robot_type: str                   # "humanoid", "mecha", "drone", "android"
    material: str                     # "metal", "plastic", "organic_hybrid"
    color_scheme: str
    body_shape: str
    size_category: str
    special_features: List[str]       # 天线、发光部件、武器等
    era_style: str                    # "retro", "modern", "futuristic"


class Character(BaseModel):
    """通用角色模型"""
    id: str
    name: str
    name_en: Optional[str]
    character_type: CharacterType
    
    # 根据type使用对应的外观模型
    human: Optional[HumanAppearance]
    animal: Optional[AnimalAppearance]
    fantasy_creature: Optional[FantasyCreatureAppearance]
    robot: Optional[RobotAppearance]
    
    # 通用字段
    personality: Optional[str]
    role_in_story: Optional[str]      # "protagonist", "antagonist", "supporting"
```

#### 1.2 通用角色描述生成器

```python
# app/services/character_prompt_builder.py

class CharacterPromptBuilder:
    """
    根据角色类型生成对应的图像prompt描述
    
    核心原则：
    1. 根据角色类型选择对应的描述模板
    2. 包含所有关键视觉特征
    3. 强调角色类型以防AI混淆
    4. 输出格式统一：[CHARACTER: 名字] 详细描述
    """
    
    def build_character_prompt(self, character: dict) -> str:
        """
        构建单个角色的完整描述
        
        自动检测角色类型并调用对应的构建方法
        """
        char_type = character.get('character_type', self._infer_type(character))
        name = character.get('name', 'Unknown')
        name_en = character.get('name_en', '')
        
        # 根据类型调用不同的构建方法
        if char_type == 'human':
            desc = self._build_human_description(character)
        elif char_type == 'animal':
            desc = self._build_animal_description(character)
        elif char_type == 'fantasy_creature':
            desc = self._build_fantasy_description(character)
        elif char_type == 'robot':
            desc = self._build_robot_description(character)
        else:
            desc = self._build_generic_description(character)
        
        # 统一格式
        name_str = f"{name} ({name_en})" if name_en else name
        return f"[CHARACTER: {name_str}] {desc}"
    
    def _infer_type(self, character: dict) -> str:
        """根据字段推断角色类型"""
        if character.get('human'):
            return 'human'
        elif character.get('animal'):
            return 'animal'
        elif character.get('fantasy_creature'):
            return 'fantasy_creature'
        elif character.get('robot'):
            return 'robot'
        else:
            return 'unknown'
    
    def _build_human_description(self, character: dict) -> str:
        """构建人类角色描述"""
        h = character.get('human', {})
        
        parts = []
        
        # 基础信息
        age = h.get('age_range', '')
        gender = h.get('gender', '')
        body_type = h.get('body_type', '')
        height = h.get('height', '')
        
        if age and gender:
            parts.append(f"A {age} {gender}")
        if body_type and height:
            parts.append(f"{height} height, {body_type} build")
        
        # 面部特征
        skin = h.get('skin_tone', '')
        face = h.get('face_shape', '')
        eyes = h.get('eye_color', '')
        if skin:
            parts.append(f"{skin} skin")
        if eyes:
            parts.append(f"{eyes} eyes")
        
        # 发型（非常重要的识别特征）
        hair_color = h.get('hair_color', '')
        hair_length = h.get('hair_length', '')
        hair_style = h.get('hair_style', '')
        if hair_color and hair_length:
            parts.append(f"{hair_color} {hair_length} {hair_style} hair")
        
        # 服装
        clothing = h.get('clothing_description', '')
        if clothing:
            parts.append(f"wearing {clothing}")
        
        # 独特标记
        features = h.get('distinctive_features', [])
        if features:
            parts.append(f"Distinctive features: {', '.join(features)}")
        
        desc = ", ".join(parts)
        return f"{desc}. This is a HUMAN character."
    
    def _build_animal_description(self, character: dict) -> str:
        """构建动物角色描述"""
        a = character.get('animal', {})
        
        parts = []
        
        species = a.get('species', '')
        breed = a.get('breed', species)
        fur_color = a.get('fur_color', '')
        fur_pattern = a.get('fur_pattern', '')
        body_size = a.get('body_size', '')
        body_shape = a.get('body_shape', '')
        eye_color = a.get('eye_color', '')
        
        # 基础描述
        if body_size and body_shape:
            parts.append(f"A {body_size}, {body_shape} {breed}")
        else:
            parts.append(f"A {breed}")
        
        # 外观
        if fur_color:
            parts.append(f"with {fur_color} fur/feathers")
        if fur_pattern:
            parts.append(f"featuring {fur_pattern} pattern")
        if eye_color:
            parts.append(f"{eye_color} eyes")
        
        # 独特标记
        marks = a.get('distinctive_marks', [])
        if marks:
            parts.append(f"Distinctive marks: {', '.join(marks)}")
        
        desc = ", ".join(parts)
        return f"{desc}. This is an ANIMAL character, NOT a human."
    
    def _build_fantasy_description(self, character: dict) -> str:
        """构建奇幻生物描述"""
        f = character.get('fantasy_creature', {})
        
        parts = []
        
        creature_type = f.get('creature_type', '')
        base_form = f.get('base_form', '')
        color_scheme = f.get('color_scheme', '')
        skin_texture = f.get('skin_texture', '')
        size = f.get('size_category', '')
        
        if creature_type and base_form:
            parts.append(f"A {size} {creature_type}, {base_form}")
        
        if color_scheme:
            parts.append(f"{color_scheme} coloring")
        if skin_texture:
            parts.append(f"{skin_texture} texture")
        
        features = f.get('special_features', [])
        if features:
            parts.append(f"with {', '.join(features)}")
        
        marks = f.get('distinctive_marks', [])
        if marks:
            parts.append(f"Distinctive marks: {', '.join(marks)}")
        
        desc = ", ".join(parts)
        return f"{desc}. This is a FANTASY CREATURE."
    
    def _build_robot_description(self, character: dict) -> str:
        """构建机器人角色描述"""
        r = character.get('robot', {})
        
        parts = []
        
        robot_type = r.get('robot_type', '')
        material = r.get('material', '')
        color_scheme = r.get('color_scheme', '')
        size = r.get('size_category', '')
        era = r.get('era_style', '')
        
        if robot_type:
            parts.append(f"A {size} {era} {robot_type} robot")
        
        if material:
            parts.append(f"made of {material}")
        if color_scheme:
            parts.append(f"{color_scheme} color scheme")
        
        features = r.get('special_features', [])
        if features:
            parts.append(f"featuring {', '.join(features)}")
        
        desc = ", ".join(parts)
        return f"{desc}. This is a ROBOT/MECHANICAL character."
    
    def _build_generic_description(self, character: dict) -> str:
        """通用描述（兜底）"""
        desc = character.get('description', '')
        if desc:
            return desc
        return "A character with unspecified appearance."
```

---

### 二、全局风格一致性系统

#### 2.1 项目风格配置

```python
# app/models/style_config.py

from pydantic import BaseModel
from typing import List, Optional

class ProjectStyleConfig(BaseModel):
    """
    项目级别的风格配置
    
    确保整个故事的视觉风格统一
    """
    
    # 基础风格
    style_preset: str                 # "realistic", "cartoon", "anime", "watercolor"等
    
    # 色调配置
    color_palette: str                # "warm", "cold", "neutral", "vibrant", "muted"
    dominant_colors: List[str]        # 主色调 ["#FFD700", "#8B4513"]
    
    # 光影风格
    lighting_style: str               # "natural", "dramatic", "soft", "neon", "cinematic"
    time_of_day_default: str          # "day", "night", "dawn", "dusk"
    
    # 美术风格细节
    line_style: Optional[str]         # "clean", "sketchy", "no_outline"
    texture_style: Optional[str]      # "smooth", "textured", "painterly"
    detail_level: str                 # "minimal", "moderate", "detailed"
    
    # 时代/世界观
    era: Optional[str]                # "modern", "ancient", "futuristic", "fantasy"
    world_setting: Optional[str]      # "urban", "rural", "space", "underwater"
    
    # 固定的风格prompt片段（每张图都会加上）
    style_suffix: str                 # 自动生成的风格描述


class StyleConfigBuilder:
    """
    根据配置生成风格prompt
    """
    
    STYLE_TEMPLATES = {
        "realistic": "photorealistic, cinematic lighting, film grain, detailed textures",
        "cartoon": "cartoon style, vibrant colors, clean lines, animated movie quality",
        "anime": "anime style, cel shading, expressive eyes, Japanese animation",
        "watercolor": "watercolor painting, soft edges, dreamy atmosphere, artistic",
        "cyberpunk": "cyberpunk aesthetic, neon lights, dark atmosphere, futuristic",
        "ink": "Chinese ink wash painting, minimalist, brush strokes, traditional",
        "pixel": "pixel art, retro game aesthetic, 16-bit style",
        "oil_painting": "oil painting style, visible brushstrokes, classical art",
    }
    
    COLOR_MODIFIERS = {
        "warm": "warm color temperature, golden tones, amber highlights",
        "cold": "cool color temperature, blue tones, silver highlights",
        "neutral": "balanced color temperature, natural tones",
        "vibrant": "highly saturated colors, vivid and bold",
        "muted": "desaturated colors, soft and subdued palette",
    }
    
    LIGHTING_MODIFIERS = {
        "natural": "natural lighting, realistic shadows",
        "dramatic": "dramatic lighting, strong contrast, deep shadows",
        "soft": "soft diffused lighting, gentle shadows",
        "neon": "neon lighting, glowing effects, colorful light sources",
        "cinematic": "cinematic lighting, volumetric rays, film-like atmosphere",
    }
    
    def build_style_suffix(self, config: ProjectStyleConfig) -> str:
        """
        构建风格后缀（每张图都会附加）
        """
        parts = []
        
        # 基础风格
        base_style = self.STYLE_TEMPLATES.get(config.style_preset, config.style_preset)
        parts.append(base_style)
        
        # 色调
        color_mod = self.COLOR_MODIFIERS.get(config.color_palette, "")
        if color_mod:
            parts.append(color_mod)
        
        # 光影
        lighting_mod = self.LIGHTING_MODIFIERS.get(config.lighting_style, "")
        if lighting_mod:
            parts.append(lighting_mod)
        
        # 细节级别
        if config.detail_level == "detailed":
            parts.append("highly detailed, intricate")
        elif config.detail_level == "minimal":
            parts.append("minimalist, simple")
        
        # 时代感
        if config.era:
            parts.append(f"{config.era} era aesthetic")
        
        # 质量保证
        parts.append("consistent style throughout, professional quality")
        
        return ", ".join(parts)
```

#### 2.2 场景风格继承

```python
# app/services/scene_style_manager.py

class SceneStyleManager:
    """
    场景风格管理器
    
    确保：
    1. 同一场景类型的背景风格一致
    2. 室内/室外场景有对应的光影处理
    3. 情绪氛围反映在色调上
    """
    
    SCENE_TYPE_MODIFIERS = {
        "indoor": "interior scene, indoor lighting",
        "outdoor": "exterior scene, natural environment",
        "urban": "city environment, buildings, streets",
        "nature": "natural landscape, organic elements",
        "fantasy": "magical environment, otherworldly elements",
    }
    
    MOOD_COLOR_MAPPING = {
        "happy": "bright, warm colors, high key lighting",
        "sad": "muted colors, low saturation, soft shadows",
        "tense": "high contrast, dramatic shadows, desaturated",
        "romantic": "warm pink/golden tones, soft focus, dreamy",
        "scary": "dark shadows, cold tones, low key lighting",
        "epic": "grand scale, dramatic lighting, saturated colors",
    }
    
    TIME_LIGHTING_MAPPING = {
        "morning": "soft morning light, warm golden hour",
        "noon": "bright midday sun, short shadows",
        "afternoon": "warm afternoon light, long shadows",
        "evening": "golden hour, orange/pink sky",
        "night": "night scene, moonlight, artificial lights",
        "dawn": "early dawn, purple/pink sky, soft light",
        "dusk": "twilight, blue hour, fading light",
    }
    
    def build_scene_style_prompt(
        self,
        scene: dict,
        project_style: ProjectStyleConfig
    ) -> str:
        """
        为单个场景构建环境风格描述
        """
        parts = []
        
        location = scene.get('location', '')
        time = scene.get('time', '')
        mood = scene.get('mood', '')
        
        # 场景类型
        scene_type = self._infer_scene_type(location)
        if scene_type in self.SCENE_TYPE_MODIFIERS:
            parts.append(self.SCENE_TYPE_MODIFIERS[scene_type])
        
        # 时间光影
        time_key = self._normalize_time(time)
        if time_key in self.TIME_LIGHTING_MAPPING:
            parts.append(self.TIME_LIGHTING_MAPPING[time_key])
        
        # 情绪色调
        mood_key = self._normalize_mood(mood)
        if mood_key in self.MOOD_COLOR_MAPPING:
            parts.append(self.MOOD_COLOR_MAPPING[mood_key])
        
        return ", ".join(parts)
    
    def _infer_scene_type(self, location: str) -> str:
        """从location推断场景类型"""
        location_lower = location.lower()
        
        indoor_keywords = ['room', 'house', 'office', 'indoor', '室内', '房间', '屋']
        outdoor_keywords = ['forest', 'mountain', 'sea', 'outdoor', '户外', '森林', '山']
        urban_keywords = ['city', 'street', 'building', '城市', '街道']
        
        if any(kw in location_lower for kw in indoor_keywords):
            return 'indoor'
        elif any(kw in location_lower for kw in urban_keywords):
            return 'urban'
        elif any(kw in location_lower for kw in outdoor_keywords):
            return 'nature'
        else:
            return 'outdoor'
    
    def _normalize_time(self, time: str) -> str:
        """标准化时间词"""
        time_lower = time.lower()
        mappings = {
            '清晨': 'dawn', '早晨': 'morning', '上午': 'morning',
            '中午': 'noon', '下午': 'afternoon', '傍晚': 'evening',
            '黄昏': 'dusk', '夜晚': 'night', '深夜': 'night',
        }
        for cn, en in mappings.items():
            if cn in time_lower:
                return en
        return time_lower
    
    def _normalize_mood(self, mood: str) -> str:
        """标准化情绪词"""
        mood_lower = mood.lower()
        mappings = {
            '温馨': 'happy', '欢乐': 'happy', '紧张': 'tense',
            '悲伤': 'sad', '恐怖': 'scary', '浪漫': 'romantic',
            '史诗': 'epic', '绝望': 'sad', '希望': 'happy',
        }
        for cn, en in mappings.items():
            if cn in mood_lower:
                return en
        return mood_lower
```

---

### 三、统一Prompt构建器

```python
# app/services/unified_prompt_builder.py

class UnifiedPromptBuilder:
    """
    统一的Prompt构建器
    
    整合：
    1. 场景视觉描述
    2. 角色完整描述（根据类型自动适配）
    3. 场景风格（光影、色调、氛围）
    4. 项目全局风格（贯穿全片）
    """
    
    def __init__(self):
        self.character_builder = CharacterPromptBuilder()
        self.scene_style_manager = SceneStyleManager()
        self.style_config_builder = StyleConfigBuilder()
    
    def build_shot_prompt(
        self,
        shot: dict,
        characters: List[dict],
        project_style: ProjectStyleConfig
    ) -> str:
        """
        构建完整的shot prompt
        """
        prompt_sections = []
        
        # === Section 1: 场景视觉描述 ===
        visual_desc = shot.get('visual_description', '')
        if visual_desc:
            prompt_sections.append(f"SCENE: {visual_desc}")
        
        # === Section 2: 镜头信息 ===
        shot_type = shot.get('shot_type', '')
        camera_angle = shot.get('camera_angle', '')
        if shot_type or camera_angle:
            camera_info = f"CAMERA: {shot_type}"
            if camera_angle:
                camera_info += f", {camera_angle}"
            prompt_sections.append(camera_info)
        
        # === Section 3: 角色描述（核心！）===
        scene_characters = self._get_characters_in_shot(shot, characters)
        if scene_characters:
            char_prompts = []
            for char in scene_characters:
                char_prompt = self.character_builder.build_character_prompt(char)
                char_prompts.append(char_prompt)
            prompt_sections.append("CHARACTERS:\n" + "\n".join(char_prompts))
        
        # === Section 4: 场景风格 ===
        scene_style = self.scene_style_manager.build_scene_style_prompt(
            scene=shot,
            project_style=project_style
        )
        if scene_style:
            prompt_sections.append(f"SCENE STYLE: {scene_style}")
        
        # === Section 5: 全局风格后缀 ===
        style_suffix = project_style.style_suffix
        if style_suffix:
            prompt_sections.append(f"ART STYLE: {style_suffix}")
        
        # === Section 6: 质量保证 ===
        prompt_sections.append("QUALITY: high quality, consistent with previous frames, professional artwork")
        
        return "\n\n".join(prompt_sections)
    
    def _get_characters_in_shot(self, shot: dict, all_characters: list) -> list:
        """
        智能识别shot中出现的角色
        
        策略：
        1. 显式标记的角色ID
        2. 文本中提到的角色名
        3. 群体关键词触发所有主角
        """
        result = []
        
        char_ids = shot.get('characters_in_scene', [])
        narration = shot.get('narration_segment', '').lower()
        visual_desc = shot.get('visual_description', '').lower()
        combined_text = f"{narration} {visual_desc}"
        
        # 群体关键词（中英文）
        group_keywords = [
            '三个', '两个', '所有人', '大家', '伙伴们', '朋友们', '他们', '一起',
            'three', 'two', 'all', 'together', 'they', 'companions', 'friends', 'group'
        ]
        is_group_scene = any(kw in combined_text for kw in group_keywords)
        
        for char in all_characters:
            char_id = char.get('id', '')
            char_name = char.get('name', '').lower()
            char_name_en = (char.get('name_en', '') or '').lower()
            
            is_explicit = char_id in char_ids
            is_mentioned = char_name in combined_text or char_name_en in combined_text
            
            # 如果是群体场景且角色是主角，自动包含
            is_main = char.get('role_in_story') in ['protagonist', 'main', None]  # 默认主角
            
            if is_explicit or is_mentioned or (is_group_scene and is_main):
                result.append(char)
        
        return result
```

---

### 四、参考图系统（通用版）

```python
# app/services/reference_image_manager.py

class ReferenceImageManager:
    """
    参考图管理器
    
    管理两类参考图：
    1. 角色参考图：每个角色一张立绘
    2. 环境参考图：每种场景类型一张（可选）
    """
    
    def __init__(self):
        self.character_references = {}  # {char_id: PIL.Image}
        self.environment_references = {}  # {scene_type: PIL.Image}
    
    async def generate_character_reference(
        self,
        character: dict,
        project_style: ProjectStyleConfig,
        image_generator
    ) -> dict:
        """
        生成角色参考图
        
        根据角色类型生成对应的立绘
        """
        char_id = character.get('id')
        char_type = character.get('character_type', self._infer_type(character))
        
        # 构建角色立绘prompt
        prompt = self._build_reference_prompt(character, char_type, project_style)
        
        result = await image_generator.generate_image(
            prompt=prompt,
            negative_prompt=self._get_negative_prompt(char_type),
            aspect_ratio="1:1"
        )
        
        if result.get('success'):
            self.character_references[char_id] = result.get('pil_image')
        
        return result
    
    def _build_reference_prompt(
        self,
        character: dict,
        char_type: str,
        project_style: ProjectStyleConfig
    ) -> str:
        """构建角色参考图prompt"""
        builder = CharacterPromptBuilder()
        char_desc = builder.build_character_prompt(character)
        
        reference_template = f"""
Character reference sheet, turnaround view
{char_desc}
Full body view, 3/4 angle, simple solid background
Clear details showing all distinctive features
{project_style.style_suffix}
Single character only, no other elements
Professional character design sheet
"""
        return reference_template.strip()
    
    def _get_negative_prompt(self, char_type: str) -> str:
        """根据角色类型生成negative prompt"""
        base = "blurry, low quality, multiple characters, complex background"
        
        type_specific = {
            'human': "animal features, cartoon proportions",
            'animal': "human features, human face, human body",
            'robot': "organic features, flesh",
            'fantasy_creature': "",
        }
        
        return f"{base}, {type_specific.get(char_type, '')}"
    
    def get_references_for_scene(self, character_ids: List[str]) -> List:
        """获取场景中角色的参考图列表"""
        refs = []
        for char_id in character_ids:
            if char_id in self.character_references:
                refs.append(self.character_references[char_id])
        return refs
```

---

### 五、更新后的测试脚本

```python
# scripts/generate_story_images.py

async def generate_story_with_consistency(
    story_json_path: str,
    shots_json_path: str,
    output_dir: str
):
    """
    通用的故事图片生成脚本
    
    适用于任何类型的故事
    """
    # 加载数据
    story = load_json(story_json_path)
    shots = load_json(shots_json_path)
    
    characters = story.get('characters', [])
    style_config = build_project_style(story.get('style_preset', 'cartoon'))
    
    # 初始化服务
    image_generator = ImageGenerator()
    ref_manager = ReferenceImageManager()
    prompt_builder = UnifiedPromptBuilder()
    
    # Step 1: 生成所有角色的参考图
    print("=== 生成角色参考图 ===")
    for char in characters:
        print(f"  生成 {char.get('name')} ...")
        await ref_manager.generate_character_reference(
            character=char,
            project_style=style_config,
            image_generator=image_generator
        )
    
    # Step 2: 生成场景图片
    print("\n=== 生成场景图片 ===")
    for shot in shots.get('shots', []):
        shot_id = shot.get('shot_id')
        
        # 构建prompt
        prompt = prompt_builder.build_shot_prompt(
            shot=shot,
            characters=characters,
            project_style=style_config
        )
        
        # 获取参考图
        char_ids = shot.get('characters_in_scene', [])
        reference_images = ref_manager.get_references_for_scene(char_ids)
        
        # 生成图片
        result = await image_generator.generate_image(
            prompt=prompt,
            negative_prompt=shot.get('negative_prompt', ''),
            aspect_ratio=shot.get('aspect_ratio', '16:9'),
            reference_images=reference_images if reference_images else None
        )
        
        if result.get('success'):
            save_image(result, output_dir, f"shot_{shot_id:02d}.png")
            print(f"  ✅ shot_{shot_id:02d}.png")
        else:
            print(f"  ❌ shot_{shot_id:02d} 失败: {result.get('error')}")
```

---

## 验收标准

| 标准 | 说明 |
|------|------|
| 角色类型适配 | 人类、动物、奇幻生物等都能正确描述 |
| 角色物种一致 | 整片内同一角色物种不变 |
| 外观特征一致 | 服装/毛色/独特标记等帧间保持 |
| 群体场景完整 | "三个朋友"等场景包含所有应出现的角色 |
| 风格一致 | 色调、光影风格全片统一 |
| 通用性 | 换一个完全不同的故事也能正常工作 |

---
