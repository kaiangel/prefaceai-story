"""
一致性图片生成服务

整合角色一致性管理，确保故事中角色在不同场景的视觉一致性

方案A（主要）：通过详细文字描述保持一致性
方案B（备用）：使用角色参考图 + Pro模型
"""

import asyncio
from typing import List, Dict, Optional
from PIL import Image

from app.services.image_generator import ImageGenerator
from app.services.character_consistency import (
    CharacterConsistencyManager,
    Character,
    VisualStyle,
    SceneStyle,
    create_character_from_dict,
    create_style_from_dict,
    create_scene_style_from_dict
)


class ConsistentImageGenerator:
    """
    一致性图片生成器

    核心功能：
    1. 管理故事中所有角色的详细描述
    2. 为每个场景自动注入角色描述和视觉风格
    3. 支持备用方案：角色参考图
    """

    def __init__(self):
        self.image_generator = ImageGenerator()
        self.consistency_manager = CharacterConsistencyManager()
        self.use_reference_images = False  # 是否使用参考图模式

    def initialize_from_story(self, story_data: dict) -> bool:
        """
        从故事数据初始化角色和风格

        Args:
            story_data: 故事生成API返回的完整数据，包含characters和visual_style

        Returns:
            是否初始化成功
        """
        try:
            # 初始化视觉风格
            if "visual_style" in story_data:
                style = create_style_from_dict(story_data["visual_style"])
                self.consistency_manager.set_visual_style(style)

            # 初始化角色
            characters = story_data.get("characters", [])
            for char_data in characters:
                character = create_character_from_dict(char_data)
                self.consistency_manager.add_character(character)

            return True
        except Exception as e:
            print(f"初始化角色数据失败: {e}")
            return False

    def add_character(self, character: Character) -> bool:
        """添加单个角色"""
        return self.consistency_manager.add_character(character)

    def set_visual_style(self, style: VisualStyle):
        """设置视觉风格"""
        self.consistency_manager.set_visual_style(style)

    async def generate_character_reference(
        self,
        character_id: str,
        additional_prompt: str = ""
    ) -> dict:
        """
        方案B：生成角色参考图

        为指定角色生成一张参考图，用于后续场景生成

        Args:
            character_id: 角色ID
            additional_prompt: 额外的提示（如特定姿势）

        Returns:
            生成结果，包含图片数据
        """
        character = self.consistency_manager.get_character(character_id)
        if not character:
            return {"success": False, "error": f"角色 {character_id} 不存在"}

        # 构建角色参考图prompt
        char_prompt = character.to_image_prompt(include_clothing=True)

        # 添加参考图特定要求
        reference_prompt = f"""Character reference sheet for: {character.name_en}

{char_prompt}

Requirements:
- Clean, simple background (white or light gray)
- Clear full-body view
- Consistent lighting
- High detail on character features
- Suitable as reference for future illustrations
{additional_prompt}
"""

        # 使用1:1比例生成参考图
        result = await self.image_generator.generate_image(
            prompt=reference_prompt,
            aspect_ratio="2:3",  # 竖版角色参考图（抖音适配）
            use_pro_model=True  # 使用Pro模型获得更好质量
        )

        if result.get("success") and result.get("pil_image"):
            # 保存为角色参考图
            self.consistency_manager.set_reference_image(
                character_id,
                result["pil_image"]
            )

        return result

    async def generate_all_character_references(self) -> Dict[str, dict]:
        """
        方案B：为所有角色生成参考图

        Returns:
            {character_id: generation_result}
        """
        results = {}
        for char_id in self.consistency_manager.characters.keys():
            print(f"生成角色参考图: {char_id}")
            results[char_id] = await self.generate_character_reference(char_id)
            # 避免API速率限制
            await asyncio.sleep(2)
        return results

    async def generate_scene_image(
        self,
        scene_data: dict,
        use_reference_images: bool = None
    ) -> dict:
        """
        生成场景图片

        自动注入角色描述和视觉风格

        Args:
            scene_data: 场景数据，包含：
                - visual_description: 场景描述
                - characters_in_scene: 场景中的角色ID列表
                - character_actions: 角色动作 {char_id: action}
                - scene_style: 场景独立风格（可选）
            use_reference_images: 是否使用参考图模式（None则使用默认设置）

        Returns:
            生成结果
        """
        use_refs = use_reference_images if use_reference_images is not None else self.use_reference_images

        # 获取场景中的角色
        char_ids = scene_data.get("characters_in_scene", [])
        char_actions = scene_data.get("character_actions", {})
        scene_desc = scene_data.get("visual_description", "")

        # 获取场景独立风格
        scene_style_data = scene_data.get("scene_style", {})
        scene_style = create_scene_style_from_dict(scene_style_data) if scene_style_data else None

        # 构建完整prompt（传入场景风格）
        full_prompt = self.consistency_manager.build_scene_prompt(
            scene_description=scene_desc,
            character_ids=char_ids,
            character_actions=char_actions,
            include_style=True,
            scene_style=scene_style
        )

        # 决定是否使用参考图
        reference_images = None
        use_pro = False

        if use_refs:
            reference_images_list = self.consistency_manager.get_reference_images_for_scene(char_ids)
            if reference_images_list:
                reference_images = reference_images_list
                use_pro = True

        # 生成图片
        result = await self.image_generator.generate_image(
            prompt=full_prompt,
            aspect_ratio="2:3",
            reference_images=reference_images,
            use_pro_model=use_pro
        )

        # 添加调试信息
        if result.get("success"):
            result["prompt_used"] = full_prompt
            result["characters_included"] = char_ids
            result["used_reference_images"] = use_refs and reference_images is not None

        return result

    async def generate_all_scene_images(
        self,
        scenes: List[dict],
        use_reference_images: bool = None
    ) -> List[dict]:
        """
        批量生成所有场景图片

        Args:
            scenes: 场景数据列表
            use_reference_images: 是否使用参考图模式

        Returns:
            生成结果列表
        """
        results = []

        for i, scene in enumerate(scenes):
            print(f"生成场景 {i+1}/{len(scenes)} 图片...")
            result = await self.generate_scene_image(scene, use_reference_images)
            result["scene_id"] = scene.get("scene_id", i + 1)
            results.append(result)

            # 避免API速率限制
            if i < len(scenes) - 1:
                await asyncio.sleep(2)

        return results

    def get_character_sheet(self) -> str:
        """导出角色设定表"""
        return self.consistency_manager.export_character_sheet()

    def get_prompt_preview(self, scene_data: dict) -> str:
        """
        预览场景的完整prompt（用于调试）

        Args:
            scene_data: 场景数据

        Returns:
            完整的prompt文本
        """
        char_ids = scene_data.get("characters_in_scene", [])
        char_actions = scene_data.get("character_actions", {})
        scene_desc = scene_data.get("visual_description", "")

        # 获取场景独立风格
        scene_style_data = scene_data.get("scene_style", {})
        scene_style = create_scene_style_from_dict(scene_style_data) if scene_style_data else None

        return self.consistency_manager.build_scene_prompt(
            scene_description=scene_desc,
            character_ids=char_ids,
            character_actions=char_actions,
            include_style=True,
            scene_style=scene_style
        )


# 便捷函数：从故事数据创建一致性图片生成器
def create_generator_from_story(story_data: dict) -> ConsistentImageGenerator:
    """
    从故事数据创建配置好的一致性图片生成器

    Args:
        story_data: 故事生成API返回的完整数据

    Returns:
        配置好的ConsistentImageGenerator实例
    """
    generator = ConsistentImageGenerator()
    generator.initialize_from_story(story_data)
    return generator
