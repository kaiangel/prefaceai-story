"""
统一的Prompt构建器

整合：
1. 场景视觉描述
2. 角色完整描述（根据类型自动适配）
3. 场景风格（光影、色调、氛围）
4. 项目全局风格（贯穿全片）
5. 智能角色识别（群体场景自动包含所有主角）
"""

from typing import List, Dict, Any, Optional
from app.services.character_prompt_builder import CharacterPromptBuilder
from app.services.scene_style_manager import SceneStyleManager
from app.models.style_config import ProjectStyleConfig, StyleConfigBuilder


class UnifiedPromptBuilder:
    """
    统一的Prompt构建器

    整合：
    1. 场景视觉描述
    2. 角色完整描述（根据类型自动适配）
    3. 场景风格（光影、色调、氛围）
    4. 项目全局风格（贯穿全片）
    """

    # 群体关键词（中英文）
    GROUP_KEYWORDS = [
        '三个', '两个', '所有人', '大家', '伙伴们', '朋友们', '他们', '一起',
        '三个朋友', '三个伙伴', '同伴', '三人',
        'three', 'two', 'all', 'together', 'they', 'companions', 'friends', 'group',
        'three friends', 'three companions', 'the trio'
    ]

    def __init__(self):
        self.character_builder = CharacterPromptBuilder()
        self.scene_style_manager = SceneStyleManager()
        self.style_config_builder = StyleConfigBuilder()

    def build_shot_prompt(
        self,
        shot: Dict[str, Any],
        characters: List[Dict[str, Any]],
        project_style: ProjectStyleConfig,
        original_scene: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        构建完整的shot prompt

        Args:
            shot: shot数据
            characters: 所有角色列表
            project_style: 项目风格配置
            original_scene: 原始场景数据（可选，用于获取更多信息）
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
        scene_characters = self._get_characters_in_shot(shot, characters, original_scene)
        if scene_characters:
            char_prompts = []
            for char in scene_characters:
                char_prompt = self.character_builder.build_character_prompt(char)
                char_prompts.append(char_prompt)
            prompt_sections.append("CHARACTERS:\n" + "\n".join(char_prompts))

        # === Section 4: 场景风格 ===
        # 合并shot和original_scene的信息
        scene_data = self._merge_scene_data(shot, original_scene)
        scene_style = self.scene_style_manager.build_scene_style_prompt(
            scene=scene_data,
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

    def build_negative_prompt(self, character_type: str = None) -> str:
        """
        构建negative prompt

        Args:
            character_type: 角色类型，用于生成类型特定的negative prompt
        """
        base = "blurry, low quality, distorted, deformed, bad anatomy, extra limbs, missing limbs"
        base += ", text, watermark, signature, logo, cropped, out of frame, duplicate"
        base += ", ugly, disfigured, malformed"

        # 根据角色类型添加特定的negative prompt
        type_specific = {
            'animal': ", human features, human face, human body, humanoid",
            'human': ", animal features, fur, scales, feathers",
            'robot': ", organic features, flesh, skin",
        }

        if character_type and character_type in type_specific:
            base += type_specific[character_type]

        return base

    def _get_characters_in_shot(
        self,
        shot: Dict[str, Any],
        all_characters: List[Dict[str, Any]],
        original_scene: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        智能识别shot中出现的角色

        策略：
        1. 显式标记的角色ID（来自original_scene）
        2. 文本中提到的角色名
        3. 群体关键词触发所有主角
        """
        result = []

        # 获取显式标记的角色ID
        char_ids = []
        if original_scene:
            char_ids = original_scene.get('characters_in_scene', [])

        # 获取文本内容
        narration = (shot.get('narration_segment', '') or '').lower()
        visual_desc = (shot.get('visual_description', '') or '').lower()
        image_prompt = (shot.get('image_prompt', '') or '').lower()
        combined_text = f"{narration} {visual_desc} {image_prompt}"

        # 检查是否是群体场景
        is_group_scene = any(kw.lower() in combined_text for kw in self.GROUP_KEYWORDS)

        for char in all_characters:
            char_id = char.get('id', '')
            char_name = (char.get('name', '') or '').lower()
            char_name_en = (char.get('name_en', '') or '').lower()

            # 检查是否显式包含
            is_explicit = char_id in char_ids

            # 检查是否在文本中提及
            is_mentioned = (
                (char_name and char_name in combined_text) or
                (char_name_en and any(part.lower() in combined_text for part in char_name_en.split()))
            )

            # 如果是群体场景，检查角色是否是主角
            role = char.get('role_in_story', '')
            is_main = role in ['protagonist', 'main', 'supporting', '']

            # 决定是否包含此角色
            should_include = is_explicit or is_mentioned or (is_group_scene and is_main)

            if should_include:
                result.append(char)

        return result

    def _merge_scene_data(
        self,
        shot: Dict[str, Any],
        original_scene: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        合并shot和original_scene的数据

        优先使用shot的数据，缺失时从original_scene获取
        """
        merged = dict(shot)

        if original_scene:
            # 合并location
            if not merged.get('location'):
                merged['location'] = original_scene.get('location', '')

            # 合并time
            if not merged.get('time'):
                merged['time'] = original_scene.get('time', '')

            # 合并mood
            if not merged.get('mood'):
                merged['mood'] = original_scene.get('mood', '')

            # 合并scene_style
            if not merged.get('scene_style'):
                merged['scene_style'] = original_scene.get('scene_style', {})

        return merged

    def get_prompt_preview(
        self,
        shot: Dict[str, Any],
        characters: List[Dict[str, Any]],
        project_style: ProjectStyleConfig,
        original_scene: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        预览将要生成的完整prompt（用于调试）
        """
        return self.build_shot_prompt(shot, characters, project_style, original_scene)

    def get_characters_preview(
        self,
        shot: Dict[str, Any],
        characters: List[Dict[str, Any]],
        original_scene: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        预览将要包含的角色列表（用于调试）
        """
        scene_chars = self._get_characters_in_shot(shot, characters, original_scene)
        return [c.get('name', 'Unknown') for c in scene_chars]


def create_prompt_builder() -> UnifiedPromptBuilder:
    """创建UnifiedPromptBuilder实例"""
    return UnifiedPromptBuilder()


def build_project_style(story_data: Dict[str, Any]) -> ProjectStyleConfig:
    """
    从story数据构建项目风格配置

    Args:
        story_data: story.json的内容

    Returns:
        ProjectStyleConfig实例
    """
    builder = StyleConfigBuilder()
    return builder.build_from_story(story_data)
