"""
ShotPromptGenerator - 为每个shot动态生成图像生成prompt

核心职责：
1. 整合故事上下文、场景信息、角色信息
2. 调用LLM生成贴切、具体、精准的prompt
3. 确保prompt包含所有必要的摄影规格

新架构核心：scene_refs只生成锚点图，差异化由shots的prompt决定
"""

from typing import Dict, List, Any, Optional
from google import genai
from google.genai import types
from app.config import settings
from app.prompts.shot_prompt_generator import SHOT_PROMPT_GENERATOR_SYSTEM


class ShotPromptGenerator:
    """
    为每个shot动态生成图像生成prompt

    使用场景：
    - 在shots图像生成前，为每个shot生成定制化的prompt
    - 结合scene_ref锚点图，实现同场景不同角度/景别的差异化
    """

    def __init__(self, model_name: str = "gemini-2.0-flash"):
        """
        初始化ShotPromptGenerator

        Args:
            model_name: 用于生成prompt的LLM模型名称
        """
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = model_name
        print(f"[ShotPromptGenerator] 初始化完成，使用模型: {model_name}")

    async def generate_shot_prompt(
        self,
        story_context: Dict[str, Any],
        scene_ref_description: str,
        shot_info: Dict[str, Any],
        characters: List[Dict[str, Any]],
        style_config: Dict[str, Any]
    ) -> str:
        """
        为单个shot生成图像prompt

        Args:
            story_context: 故事元信息（类型、风格、整体氛围）
            scene_ref_description: 场景锚点图的描述
            shot_info: 当前shot的完整信息
            characters: 出场角色列表及其视觉定义
            style_config: 视觉风格配置

        Returns:
            可直接用于Gemini图像生成的prompt文本（全英文）
        """

        # 构建发给LLM的请求
        user_prompt = self._build_shot_context(
            story_context, scene_ref_description, shot_info, characters, style_config
        )

        try:
            # 构建对话历史（使用字典格式，与其他服务一致）
            contents = [
                {
                    "role": "user",
                    "parts": [{"text": SHOT_PROMPT_GENERATOR_SYSTEM}]
                },
                {
                    "role": "model",
                    "parts": [{"text": "I understand. Please provide the shot information and I will generate a precise image prompt in English."}]
                },
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}]
                }
            ]

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=2048
                )
            )

            generated_prompt = response.text.strip()

            # 清理可能的markdown代码块标记
            if generated_prompt.startswith("```"):
                lines = generated_prompt.split("\n")
                # 移除开头的```和可能的语言标识
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # 移除结尾的```
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                generated_prompt = "\n".join(lines)

            print(f"[ShotPromptGenerator] Shot {shot_info.get('shot_id', '?')} prompt生成成功 ({len(generated_prompt)} 字符)")
            return generated_prompt

        except Exception as e:
            print(f"[ShotPromptGenerator] ❌ 生成prompt失败: {e}")
            # 返回一个基本的fallback prompt
            return self._generate_fallback_prompt(shot_info, scene_ref_description)

    def _build_shot_context(
        self,
        story_context: Dict,
        scene_ref_description: str,
        shot_info: Dict,
        characters: List[Dict],
        style_config: Dict
    ) -> str:
        """构建shot上下文，发送给LLM"""

        # 提取出场角色
        appearing_characters = []
        chars_in_shot = shot_info.get('characters_in_shot', []) or shot_info.get('characters_in_scene', [])

        for char_id in chars_in_shot:
            char = next((c for c in characters if c.get('id') == char_id), None)
            if char:
                appearing_characters.append(char)

        # 构建角色外观描述
        def build_character_appearance(char: Dict) -> str:
            """从角色数据构建外观描述"""
            parts = []

            # 基本信息
            name = char.get('name', 'Unknown')
            name_en = char.get('name_en', name)
            gender = char.get('gender', '')
            age = char.get('age_appearance', char.get('age', ''))

            parts.append(f"**{name} ({name_en})**")
            if gender:
                parts.append(f"Gender: {gender}")
            if age:
                parts.append(f"Age: {age}")

            # 物理外观
            physical = char.get('physical', {})
            if physical:
                physical_desc = []
                if physical.get('hair_color'):
                    physical_desc.append(f"{physical['hair_color']} {physical.get('hair_style', 'hair')}")
                if physical.get('eye_color'):
                    physical_desc.append(f"{physical['eye_color']} eyes")
                if physical.get('skin_tone'):
                    physical_desc.append(f"{physical['skin_tone']} skin")
                if physical.get('build'):
                    physical_desc.append(f"{physical['build']} build")
                if physical.get('height'):
                    physical_desc.append(f"{physical['height']} height")
                if physical_desc:
                    parts.append(f"Appearance: {', '.join(physical_desc)}")

            # 服装
            clothing = char.get('clothing', {})
            if clothing:
                clothing_desc = []
                if clothing.get('top'):
                    clothing_desc.append(clothing['top'])
                if clothing.get('bottom'):
                    clothing_desc.append(clothing['bottom'])
                if clothing.get('footwear'):
                    clothing_desc.append(clothing['footwear'])
                accessories = clothing.get('accessories', [])
                if accessories:
                    clothing_desc.append(f"accessories: {', '.join(accessories[:3])}")
                if clothing_desc:
                    parts.append(f"Clothing: {', '.join(clothing_desc)}")

            # 简短描述兜底
            if len(parts) <= 2:  # 只有名字和性别
                desc = char.get('description', '') or char.get('appearance', '')
                if desc:
                    parts.append(f"Description: {desc}")

            return "\n".join(parts)

        # 获取风格关键词
        style_preset = style_config.get('style_preset', 'realistic')
        style_keywords = self._get_style_keywords(style_preset)

        # 场景style信息
        scene_style = shot_info.get('scene_style', {})

        context = f"""## 故事元信息
- 故事类型: {story_context.get('genre', '未知')}
- 视觉风格: {style_preset}
- 整体氛围: {story_context.get('overall_mood', '')}
- 故事标题: {story_context.get('title', '')}

## 场景参考图描述
{scene_ref_description if scene_ref_description else '（无场景参考图描述，请根据location信息推断）'}

## 当前Shot信息
- Scene ID: {shot_info.get('scene_id', shot_info.get('original_scene_id', '?'))}
- Shot ID: {shot_info.get('shot_id', '?')}
- 场景位置: {shot_info.get('location', '')}
- 剧情描述: {shot_info.get('action_description', shot_info.get('visual_description', ''))}
- 旁白/对白: {shot_info.get('narration', shot_info.get('narration_segment', ''))}
- 时间: {shot_info.get('time', scene_style.get('time_of_day', ''))}
- 氛围: {shot_info.get('mood', '')}
- 光线: {scene_style.get('lighting', shot_info.get('lighting', ''))}
- 天气: {scene_style.get('weather', '')}

## 当前镜头建议（仅供参考，你可以根据剧情调整）
- 景别建议: {shot_info.get('shot_type', '由你决定')}
- 角度建议: {shot_info.get('camera_angle', '由你决定')}

## 出场角色
"""

        if appearing_characters:
            for i, char in enumerate(appearing_characters, 1):
                context += f"\n### 角色 {i}\n"
                context += build_character_appearance(char)

                # 当前动作和表情（如果有）
                char_id = char.get('id', '')
                actions = shot_info.get('character_actions', {})
                expressions = shot_info.get('character_expressions', {})
                positions = shot_info.get('character_positions', {})

                if char_id in actions:
                    context += f"\nCurrent Action: {actions[char_id]}"
                if char_id in expressions:
                    context += f"\nCurrent Expression: {expressions[char_id]}"
                if char_id in positions:
                    context += f"\nPosition in Frame: {positions[char_id]}"
                context += "\n"
        else:
            context += "（无人场景/空镜头）\n"

        context += f"""
## 视觉风格关键词
{style_keywords}

## 特殊要求
{shot_info.get('special_requirements', '无')}

请根据以上信息，生成一个精确的图像生成prompt（全英文）。
"""

        return context

    def _get_style_keywords(self, style_preset: str) -> str:
        """根据风格预设返回对应的关键词"""
        style_map = {
            'realistic': "photorealistic, cinematic, film grain, natural lighting, professional photography",
            'cartoon': "3D cartoon style, Pixar-like, vibrant colors, stylized, friendly characters",
            'anime': "anime style, Japanese animation, cel shading, expressive eyes, dynamic poses",
            'ghibli': "Studio Ghibli style, Miyazaki inspired, hand-drawn, soft colors, whimsical",
            'illustration': "digital illustration, vibrant colors, detailed artwork, concept art",
            'watercolor': "watercolor painting, soft edges, dreamy atmosphere, flowing colors",
            'children_book': "children's book illustration, friendly, soft colors, whimsical, storybook",
            'cyberpunk': "cyberpunk, neon lights, futuristic, dark atmosphere, blade runner",
            'ink': "Chinese ink wash, sumi-e, brush strokes, minimalist, traditional art",
            'pixel': "pixel art, retro game, 16-bit, crisp pixels, nostalgic"
        }
        return style_map.get(style_preset, style_map['realistic'])

    def _generate_fallback_prompt(self, shot_info: Dict, scene_ref_description: str) -> str:
        """生成降级的基础prompt"""
        location = shot_info.get('location', 'scene')
        narration = shot_info.get('narration', shot_info.get('narration_segment', ''))
        shot_type = shot_info.get('shot_type', 'medium shot')

        return f"""[SCENE CONSISTENCY]
Same location as reference image: {location}

[SHOT SPECIFICATIONS]
{shot_type}, eye level angle

[CONTENT]
Scene depicting: {narration[:200] if narration else 'story moment'}

[STYLE]
Photorealistic, cinematic composition

[EXCLUDE]
No text overlay, no watermark, no UI elements
"""

    async def generate_all_shot_prompts(
        self,
        story_data: Dict[str, Any],
        scene_ref_descriptions: Dict[str, str],
        style_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        为故事中所有shots生成prompts

        Args:
            story_data: 完整的story数据（包含scenes和characters）
            scene_ref_descriptions: 场景参考图描述 {location_key: description}
            style_config: 视觉风格配置

        Returns:
            [{"shot_id": ..., "scene_id": ..., "prompt": ..., "scene_ref_key": ...}, ...]
        """
        results = []

        story_context = {
            "genre": story_data.get('genre', ''),
            "overall_mood": story_data.get('overall_mood', ''),
            "title": story_data.get('title', '')
        }

        characters = story_data.get('characters', [])

        for scene in story_data.get('scenes', []):
            scene_id = scene.get('scene_id')
            location = scene.get('location', '')
            scene_style = scene.get('scene_style', {})

            # 确定使用哪个scene_ref
            location_type = self._infer_location_type(location)
            scene_ref_key = f"{location_type}_anchor"
            scene_ref_description = scene_ref_descriptions.get(scene_ref_key, '')

            # 获取该scene的shots
            shots = scene.get('shots', [])

            for shot in shots:
                # 合并scene信息到shot
                enriched_shot = {
                    **shot,
                    'scene_id': scene_id,
                    'location': location,
                    'scene_style': scene_style,
                    'time': scene.get('time', ''),
                    'mood': scene.get('mood', ''),
                    'characters_in_scene': scene.get('characters_in_scene', [])
                }

                # 如果shot没有characters_in_shot，继承scene的
                if not enriched_shot.get('characters_in_shot'):
                    enriched_shot['characters_in_shot'] = scene.get('characters_in_scene', [])

                shot_prompt = await self.generate_shot_prompt(
                    story_context=story_context,
                    scene_ref_description=scene_ref_description,
                    shot_info=enriched_shot,
                    characters=characters,
                    style_config=style_config
                )

                results.append({
                    'shot_id': shot.get('shot_id'),
                    'scene_id': scene_id,
                    'prompt': shot_prompt,
                    'scene_ref_key': scene_ref_key,
                    'location_type': location_type
                })

        print(f"[ShotPromptGenerator] 已为 {len(results)} 个shots生成prompts")
        return results

    def _infer_location_type(self, location: str) -> str:
        """推断场景类型（interior/exterior）"""
        location_lower = location.lower()

        exterior_keywords = ['门口', '外面', '街', '路', '广场', '公园', '天台', '屋顶',
                           'outside', 'outdoor', 'street', 'road', 'plaza', 'park',
                           'rooftop', 'entrance', 'exit']

        for keyword in exterior_keywords:
            if keyword in location_lower:
                return 'exterior'

        return 'interior'

    async def generate_single_shot_prompt_for_test(
        self,
        shot_info: Dict[str, Any],
        scene_ref_description: str,
        characters: List[Dict[str, Any]],
        style_preset: str = "anime"
    ) -> str:
        """
        测试用：为单个shot生成prompt

        简化版本，直接传入必要信息
        """
        story_context = {
            "genre": "",
            "overall_mood": "",
            "title": "测试故事"
        }

        style_config = {
            "style_preset": style_preset
        }

        return await self.generate_shot_prompt(
            story_context=story_context,
            scene_ref_description=scene_ref_description,
            shot_info=shot_info,
            characters=characters,
            style_config=style_config
        )
