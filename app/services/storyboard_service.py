"""
Storyboard decision service - converts story scenes to image prompts with shot splitting

🚨🚨🚨 角色一致性核心模块 🚨🚨🚨

本文件的修改直接影响角色一致性，修改后必须运行回归测试：
    python tests/test_character_consistency_regression.py

关键方法（修改需谨慎）：
- _build_character_reference_mapping(): 构建角色-参考图映射，确保角色ID与图片顺序对应
- _extract_actual_characters_from_description(): 智能提取visual_description中实际出场的角色
- _build_identity_line(): 构建角色身份描述（含面部特征：face_shape, skin_tone, eye_description）
- _build_scene_direction(): 构建SCENE DIRECTION部分，包含CHARACTER MAPPING

这些方法的任何修改都可能导致角色混淆，务必谨慎。

验证通过的版本：teststory6.4-6.6（2025-12-23）
- 3人场景：100%角色一致性
- 6人场景：~90%角色一致性

🚨🚨🚨 警告结束 🚨🚨🚨
"""

import json
import re
from typing import List, Optional

from google import genai
from google.genai import types

from app.config import settings
from app.prompts.storyboard_prompts import (
    build_image_prompt,
    build_negative_prompt,
    get_aspect_ratio_for_scene,
    extract_characters_from_scene,
    extract_characters_from_narration,
    STYLE_PROMPTS
)


class StoryboardService:
    """
    分镜决策服务

    输入：故事的scenes[], characters[], style_preset
    输出：每个scene的完整图像生成prompt

    关键功能：
    1. 角色描述一致性：同一角色在所有场景中的外貌描述必须一致
    2. 风格统一：所有场景的视觉风格必须统一
    3. Prompt工程：生成适合Gemini图像生成的高质量prompt
    4. 长场景拆分：将narration过长的场景拆分成多个shot
    """

    def __init__(self):
        # 从配置文件读取拆分阈值
        self.MAX_NARRATION_LENGTH = settings.SHOT_MAX_NARRATION_LENGTH
        self.TARGET_SHOT_LENGTH = settings.SHOT_TARGET_LENGTH
        self.MIN_SHOT_LENGTH = settings.SHOT_MIN_LENGTH
        self.TTS_CHARS_PER_SECOND = settings.TTS_CHARS_PER_SECOND
        self.client = None
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def generate_storyboard(
        self,
        scenes: List[dict],
        characters: List[dict],
        style_preset: str,
        project_config: Optional[dict] = None
    ) -> List[dict]:
        """
        生成分镜决策（原始方法，不拆分）

        Args:
            scenes: 场景列表
            characters: 角色列表
            style_preset: 风格预设
            project_config: 项目配置

        Returns:
            分镜列表（1:1映射）
        """
        storyboard = []

        # 获取风格描述
        style_prompt = STYLE_PROMPTS.get(style_preset, "high quality, detailed, professional")

        # 构建角色描述字典（从physical和clothing字段构建完整描述）
        character_prompts = {}
        for char in characters:
            char_name = char.get("name", "")
            # 使用_build_character_description从physical和clothing字段构建完整描述
            char_desc = self._build_character_description(char)
            if char_name:
                character_prompts[char_name] = char_desc

        # 处理每个场景
        for scene in scenes:
            scene_id = scene.get("scene_id", 0)

            # 构建图像prompt
            image_prompt = build_image_prompt(
                scene=scene,
                characters=characters,
                style_preset=style_preset
            )

            # 构建负面prompt
            negative_prompt = build_negative_prompt(style_preset)

            # 推断宽高比
            aspect_ratio = get_aspect_ratio_for_scene(scene)

            # 提取场景中的角色
            scene_chars = extract_characters_from_scene(scene, characters)
            characters_in_scene = [c.get("name", "") for c in scene_chars]

            storyboard.append({
                "scene_id": scene_id,
                "image_prompt": image_prompt,
                "character_prompts": character_prompts,
                "style_prompt": style_prompt,
                "negative_prompt": negative_prompt,
                "aspect_ratio": aspect_ratio,
                "characters_in_scene": characters_in_scene,
                "original_scene": scene  # 保留原始场景数据
            })

        return storyboard

    async def generate_storyboard_with_splitting(
        self,
        scenes: List[dict],
        characters: List[dict],
        style_preset: str,
        aspect_ratio: str = "16:9"
    ) -> List[dict]:
        """
        生成分镜板（带拆分功能）

        流程：
        1. 遍历所有scene
        2. 检测是否需要拆分（narration > MAX_NARRATION_LENGTH）
        3. 需要拆分的调用LLM细化
        4. 不需要拆分的直接生成image_prompt
        5. 返回完整的shot列表
        """
        storyboard = []
        shot_index = 1

        # 构建角色ID映射（用于从scene继承characters_in_scene）
        char_id_map = {}
        for c in characters:
            char_id = c.get('id')
            char_name = c.get('name', '')
            char_name_en = c.get('name_en', '')
            if char_id:
                char_id_map[char_name] = char_id
                char_id_map[char_name_en] = char_id

        for scene in scenes:
            scene_id = scene.get('scene_id', len(storyboard) + 1)
            narration = scene.get('narration', '')
            narration_length = len(narration)

            # 获取场景中的角色列表（从原始scene继承）
            scene_characters_in_scene = scene.get('characters_in_scene', [])

            if narration_length > self.MAX_NARRATION_LENGTH:
                # 需要拆分
                sub_shots = await self._split_scene_to_shots(
                    scene=scene,
                    characters=characters,
                    style_preset=style_preset
                )

                for i, shot in enumerate(sub_shots):
                    shot['shot_id'] = shot_index
                    shot['original_scene_id'] = scene_id
                    shot['aspect_ratio'] = aspect_ratio
                    # 继承scene的characters_in_scene
                    shot['characters_in_scene'] = scene_characters_in_scene
                    storyboard.append(shot)
                    shot_index += 1
            else:
                # 不需要拆分，直接生成
                shot = self._create_shot_from_scene(
                    scene=scene,
                    characters=characters,
                    style_preset=style_preset
                )
                shot['shot_id'] = shot_index
                shot['original_scene_id'] = scene_id
                shot['aspect_ratio'] = aspect_ratio
                # 继承scene的characters_in_scene
                shot['characters_in_scene'] = scene_characters_in_scene
                storyboard.append(shot)
                shot_index += 1

        return storyboard

    async def _split_scene_to_shots(
        self,
        scene: dict,
        characters: List[dict],
        style_preset: str
    ) -> List[dict]:
        """
        将长场景拆分成多个shot

        调用LLM分析narration中的视觉切换点，拆分成独立的画面单元
        """
        narration = scene.get('narration', '')
        visual_description = scene.get('visual_description', '')
        location = scene.get('location', '')
        time = scene.get('time', '')
        mood = scene.get('mood', '')
        scene_style = scene.get('scene_style', {})

        # 计算需要拆成几个shot
        estimated_shots = max(2, len(narration) // self.TARGET_SHOT_LENGTH)

        # 构建角色信息
        char_info = []
        for c in characters:
            char_info.append({
                "name": c.get("name", ""),
                "name_en": c.get("name_en", ""),
                "description": c.get("description", ""),
            })

        # 构建拆分prompt - 要求LLM输出纯英文的visual_description
        prompt = f"""You are a professional storyboard artist. Split the following scene into {estimated_shots} independent shots.

## Original Scene

**Location**: {location}
**Time**: {time}
**Mood**: {mood}
**Visual Description**: {visual_description}
**Narration Text**: {narration}

## Characters in Scene

{json.dumps(char_info, ensure_ascii=False, indent=2)}

## Splitting Requirements

1. **Each shot corresponds to 25-50 characters of narration** (approximately 6-12 seconds of audio)
2. **Each shot describes a single frame** with a clear visual focus
3. **Splitting criteria**:
   - Shot type changes (wide shot/medium shot/close-up/low angle/high angle)
   - Character action changes
   - Visual focus shifts
   - Emotional rhythm changes
4. **Maintain continuity**: Split shots should flow smoothly together
5. **Narration allocation**: Allocate the original text to each shot by semantic boundaries, DO NOT rewrite

## Output Format

Output in JSON format:

```json
{{
  "shots": [
    {{
      "shot_index": 1,
      "shot_type": "wide shot/medium shot/close-up/...",
      "visual_description": "MUST BE IN ENGLISH. Detailed visual description for image generation. Include character appearances, clothing, actions, expressions, and environment details.",
      "narration_segment": "Original narration text segment (keep original Chinese text, DO NOT translate or rewrite)",
      "focus": "Visual focus point in ENGLISH (e.g., 'character expressions', 'hands holding coffee', 'window view')",
      "camera_angle": "eye level/low angle/high angle/side view"
    }}
  ]
}}
```

IMPORTANT:
- visual_description MUST be written entirely in English for better image generation
- shot_type MUST be in English (wide shot, medium shot, close-up, etc.)
- camera_angle MUST be in English (eye level, low angle, high angle, side view)
- focus MUST be in English
- narration_segment MUST keep the original Chinese text unchanged
- Ensure narration_segments concatenate to the complete original narration
"""

        if not self.client:
            # 没有LLM，使用简单拆分
            return self._simple_split(scene, characters, style_preset)

        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    response_mime_type="application/json"
                )
            )

            result = json.loads(response.text)
            shots = result.get('shots', [])

            if not shots:
                return self._simple_split(scene, characters, style_preset)

            # 获取scene的characters_in_scene用于传递给_build_shot_prompt
            scene_characters_in_scene = scene.get('characters_in_scene', [])

            # 转换为标准shot格式
            formatted_shots = []
            for shot in shots:
                formatted_shots.append({
                    "image_prompt": self._build_shot_prompt(
                        shot=shot,
                        characters=characters,
                        style_preset=style_preset,
                        location=location,
                        time=time,
                        mood=mood,
                        scene_style=scene_style,
                        characters_in_scene=scene_characters_in_scene
                    ),
                    "negative_prompt": build_negative_prompt(style_preset),
                    "narration_segment": shot.get('narration_segment', ''),
                    "shot_type": shot.get('shot_type', '中景'),
                    "visual_description": shot.get('visual_description', ''),
                    "duration_hint": len(shot.get('narration_segment', '')) / self.TTS_CHARS_PER_SECOND,
                    "scene_style": scene_style,
                    "story_phase": scene.get('story_phase', '')
                })

            return formatted_shots

        except Exception as e:
            # 拆分失败，回退到简单的按字数切分
            print(f"LLM拆分失败，使用简单切分: {e}")
            return self._simple_split(scene, characters, style_preset)

    def _simple_split(
        self,
        scene: dict,
        characters: List[dict],
        style_preset: str
    ) -> List[dict]:
        """
        简单的按字数切分（LLM拆分失败时的兜底方案）
        """
        narration = scene.get('narration', '')
        visual_description = scene.get('visual_description', '')
        scene_style = scene.get('scene_style', {})

        # 按句号/感叹号/问号分割
        sentences = re.split(r'([。！？])', narration)

        # 重新组合句子（保留标点）
        segments = []
        current_segment = ''
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i]
            punct = sentences[i + 1] if i + 1 < len(sentences) else ''

            if len(current_segment) + len(sentence) < self.TARGET_SHOT_LENGTH * 1.5:
                current_segment += sentence + punct
            else:
                if current_segment:
                    segments.append(current_segment)
                current_segment = sentence + punct

        if current_segment:
            segments.append(current_segment)

        # 如果没有有效分割，至少返回原始内容
        if not segments:
            segments = [narration]

        # 生成shots
        shots = []
        for i, segment in enumerate(segments):
            shots.append({
                "image_prompt": build_image_prompt(
                    {**scene, 'visual_description': f"{visual_description}"},
                    characters,
                    style_preset
                ),
                "negative_prompt": build_negative_prompt(style_preset),
                "narration_segment": segment,
                "shot_type": "中景",
                "visual_description": visual_description,
                "duration_hint": len(segment) / self.TTS_CHARS_PER_SECOND,
                "scene_style": scene_style,
                "story_phase": scene.get('story_phase', '')
            })

        return shots

    def _clean_visual_description(self, visual_desc: str) -> str:
        """
        清洗visual_description中可能与角色定义冲突的描述

        问题根因：
        1. LLM生成visual_description时会添加错误的职业标签如"Li Xiang (bartender)"
        2. LLM会自创服装描述如"burgundy silk shirt"，与角色定义的"black v-neck sweater"冲突
        3. 冲突的服装描述会让Gemini困惑，导致角色一致性失败

        解决方案：移除所有服装颜色/款式描述，因为正确的服装信息已在CHARACTERS部分
        """
        import re

        if not visual_desc:
            return visual_desc

        cleaned = visual_desc

        # 1. 移除 "Name (occupation)" 格式的职业标签
        occupation_patterns = [
            r'\s*\((?:nurse|programmer|bartender|doctor|engineer|teacher|student|worker|cashier|waiter|waitress|chef|manager|clerk|attendant)\)',
            r'\s*\((?:护士|程序员|调酒师|医生|工程师|教师|学生|工人|店员|服务员|厨师|经理|职员)\)',
        ]
        for pattern in occupation_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        # 2. 移除服装颜色+款式描述（关键修复！）
        # 这些描述可能与角色定义冲突，应该让CHARACTERS部分的描述主导
        clothing_patterns = [
            # "in a burgundy silk shirt" / "in white scrubs" / "in a black hoodie"
            r'\s+in\s+(?:a\s+)?(?:[\w-]+\s+){0,2}(?:silk\s+)?(?:shirt|scrubs|hoodie|sweater|jacket|coat|dress|suit|pants|jeans|skirt|blouse|top|t-shirt|tee)',
            # "wearing a burgundy shirt" / "wearing white scrubs"
            r'\s+wearing\s+(?:a\s+)?(?:[\w-]+\s+){0,3}(?:shirt|scrubs|hoodie|sweater|jacket|coat|dress|suit|pants|jeans|skirt|blouse|top|t-shirt|tee)',
            # "with shoulder-length chestnut brown hair" - 保留发型，但移除颜色形容词如"chestnut brown"
            # 不处理发型，因为发型描述通常是对的
        ]
        for pattern in clothing_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        # 3. 移除独立的服装颜色短语
        # "a man in burgundy," / "woman in white." (颜色后面跟逗号、句号或空格)
        standalone_color_patterns = [
            r'\s+in\s+(?:a\s+)?(?:burgundy|white|black|gray|grey|blue|red|green|pink|navy|beige|brown|purple|orange|yellow)(?=[,\.\s])',
        ]
        for pattern in standalone_color_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        # 4. 移除可能引入额外人物的描述
        extra_person_patterns = [
            r'(?:The\s+)?(?:night-shift\s+)?cashier[^,\.]*(?:is\s+visible\s+in\s+the\s+background)?[,\.]?\s*',
            r'(?:A\s+)?(?:store\s+)?clerk[^,\.]*[,\.]?\s*',
            r'(?:The\s+)?(?:convenience\s+store\s+)?attendant[^,\.]*[,\.]?\s*',
            r'店员[^，。]*[，。]?\s*',
            r'收银员[^，。]*[，。]?\s*',
        ]
        for pattern in extra_person_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        # 5. 清理多余空格和标点
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'\.\s*\.', '.', cleaned)
        cleaned = re.sub(r',\s*,', ',', cleaned)
        cleaned = re.sub(r'\s+([,\.])', r'\1', cleaned)  # 移除标点前的空格

        return cleaned.strip()

    def _build_shot_prompt(
        self,
        shot: dict,
        characters: List[dict],
        style_preset: str,
        location: str,
        time: str,
        mood: str,
        scene_style: dict = None,
        characters_in_scene: List[str] = None
    ) -> str:
        """
        为单个shot构建图像生成prompt（全英文输出）

        ========================================
        终极方案：FIXED vs FLEXIBLE属性分离
        ========================================

        核心理念：
        1. 关键指令头：明确告诉Gemini哪些属性必须匹配参考图
        2. 角色映射：每个角色对应哪几张参考图 + 完整身份描述
        3. 场景指导：只描述动态属性（表情、动作、位置）
        4. 环境氛围：背景、光线、构图

        Args:
            characters_in_scene: 角色ID列表，从scene继承（可能不准确）
        """
        visual_desc = shot.get('visual_description', '')
        shot_type = shot.get('shot_type', '中景')
        camera_angle = shot.get('camera_angle', '平视')
        focus = shot.get('focus', '')

        # ========================================
        # 0. 智能提取实际出场角色（不信任characters_in_scene）
        # ========================================
        actual_char_ids = self._extract_actual_characters_from_description(visual_desc, characters)

        # 如果提取结果为空，fallback到characters_in_scene
        if not actual_char_ids:
            actual_char_ids = characters_in_scene or []

        # 翻译镜头类型
        shot_type_en = self._translate_shot_type(shot_type)
        camera_angle_en = self._translate_camera_angle(camera_angle)

        prompt_parts = []

        # ========================================
        # 1. CRITICAL HEADER - 关键指令头
        # ========================================
        if actual_char_ids:
            prompt_parts.append(self._build_critical_header())

        # ========================================
        # 2. CHARACTER REFERENCE MAPPING - 角色参考图映射
        # ========================================
        if actual_char_ids:
            char_mapping = self._build_character_reference_mapping(characters, actual_char_ids)
            if char_mapping:
                prompt_parts.append(char_mapping)

        # ========================================
        # 3. SCENE DIRECTION - 场景指导（动态属性）
        # ========================================
        scene_direction = self._build_scene_direction(shot, characters, actual_char_ids)
        if scene_direction:
            prompt_parts.append(scene_direction)

        # ========================================
        # 4. ENVIRONMENT - 环境描述
        # ========================================
        env_parts = []
        if location:
            env_parts.append(location)
        if time:
            env_parts.append(time)
        if env_parts:
            prompt_parts.append(f"ENVIRONMENT: {', '.join(env_parts)}")

        # ========================================
        # 5. ATMOSPHERE - 光线和氛围
        # ========================================
        atmosphere = self._build_atmosphere(shot, scene_style, mood)
        if atmosphere:
            prompt_parts.append(f"ATMOSPHERE: {atmosphere}")

        # ========================================
        # 6. COMPOSITION - 构图信息
        # ========================================
        composition_parts = [f"{shot_type_en}", f"{camera_angle_en}"]
        if focus:
            focus_en = self._translate_text_simple(focus)
            composition_parts.append(f"focus on {focus_en}")
        prompt_parts.append(f"COMPOSITION: {', '.join(composition_parts)}")

        # ========================================
        # 7. ART STYLE - 风格标签
        # ========================================
        prompt_parts.append(f"ART STYLE: {STYLE_PROMPTS.get(style_preset, style_preset)}")

        return "\n\n".join(prompt_parts)

    def _translate_shot_type(self, shot_type: str) -> str:
        """翻译镜头类型为英文"""
        translations = {
            "全景": "wide shot",
            "远景": "extreme wide shot",
            "中景": "medium shot",
            "中近景": "medium close-up",
            "近景": "medium close-up",
            "特写": "close-up",
            "大特写": "extreme close-up",
            "过肩镜头": "over-the-shoulder shot",
            "主观镜头": "POV shot",
        }
        return translations.get(shot_type, shot_type)

    def _translate_camera_angle(self, camera_angle: str) -> str:
        """翻译镜头角度为英文"""
        translations = {
            "平视": "eye level",
            "仰拍": "low angle",
            "俯拍": "high angle",
            "鸟瞰": "bird's eye view",
            "侧面": "side view",
            "正面": "front view",
            "斜侧": "three-quarter view",
        }
        return translations.get(camera_angle, camera_angle)

    def _translate_text_simple(self, text: str) -> str:
        """简单的文本翻译（用于焦点描述等）"""
        # 常用词汇翻译
        translations = {
            "人物": "characters",
            "场景": "scene",
            "背景": "background",
            "表情": "expression",
            "动作": "action",
            "手部": "hands",
            "眼神": "eyes",
            "笑容": "smile",
            "拥抱": "embrace",
            "对话": "dialogue",
            "互动": "interaction",
        }
        result = text
        for zh, en in translations.items():
            result = result.replace(zh, en)
        return result

    def _build_critical_header(self) -> str:
        """
        构建关键指令头 - 明确区分FIXED vs FLEXIBLE属性

        目的：让Gemini明确知道哪些属性必须与参考图完全匹配，哪些可以根据场景变化
        """
        return """═══════════════════════════════════════════════════════════
CRITICAL INSTRUCTIONS FOR CHARACTER CONSISTENCY
═══════════════════════════════════════════════════════════

FIXED ATTRIBUTES (MUST match reference images EXACTLY - DO NOT ALTER):
- Facial features (face shape, eyes, nose, mouth, skin tone)
- Hair (color, style, length)
- Clothing (exact garments and colors as shown in reference)
- Accessories (glasses, watches, earrings exactly as shown)

FLEXIBLE ATTRIBUTES (may vary based on scene context):
- Expression (based on scene emotion)
- Pose (based on action description)
- Camera angle (based on shot direction)

═══════════════════════════════════════════════════════════"""

    def _extract_actual_characters_from_description(
        self,
        visual_description: str,
        characters: List[dict]
    ) -> List[str]:
        """
        根据visual_description中实际提到的角色，返回出场角色ID列表

        检测逻辑：
        1. 检查是否包含角色的中文名
        2. 检查是否包含角色的英文名
        3. 检查是否包含角色ID (char_001等)

        Returns:
            实际出场角色的ID列表，按characters原始顺序排列
        """
        if not visual_description or not characters:
            return []

        actual_char_ids = []

        for char in characters:
            char_id = char.get('id', '')
            name = char.get('name', '')
            name_en = char.get('name_en', '')

            # 检查visual_description中是否提到这个角色
            mentioned = False
            if name and name in visual_description:
                mentioned = True
            elif name_en and name_en in visual_description:
                mentioned = True
            elif char_id and char_id in visual_description:
                mentioned = True

            if mentioned:
                actual_char_ids.append(char_id)

        return actual_char_ids

    def _build_identity_line(self, character: dict) -> str:
        """
        构建增强的角色身份行

        输出示例：
        "young Asian man, short black hair with side part, rectangular silver-framed glasses,
         gray casual button-up shirt, black slim jeans, black smartwatch"

        特点：
        - 包含种族/民族
        - 完整发型描述（不只是颜色）
        - 关键服装（上衣+下装）
        - 关键配饰
        """
        parts = []

        # 1. 年龄 + 种族 + 性别
        human_info = character.get('human', {})
        gender = human_info.get('gender') or character.get('gender', '')
        age = human_info.get('age_range') or character.get('age_appearance', '')

        # 年龄映射
        age_map = {
            'child': 'young',
            'teenager': 'teenage',
            'young_adult': 'young',
            'adult': '',
            'middle_aged': 'middle-aged',
            'elderly': 'elderly'
        }
        age_term = age_map.get(age, '')

        # 获取种族/民族 - 从physical.ethnicity或skin_tone推断
        physical = character.get('physical', {})
        ethnicity = physical.get('ethnicity', '')

        # 如果没有明确ethnicity，从skin_tone推断
        if not ethnicity:
            skin_tone = physical.get('skin_tone', '')
            if skin_tone in ['fair', 'light', 'pale']:
                ethnicity = 'Asian'  # 默认亚洲人（因为这是中文故事）
            elif skin_tone in ['tan', 'olive']:
                ethnicity = ''
            elif skin_tone in ['brown', 'dark']:
                ethnicity = ''

        # 构建基础标识
        if gender == 'female':
            base = f"{age_term} {ethnicity} woman".strip()
        elif gender == 'male':
            base = f"{age_term} {ethnicity} man".strip()
        else:
            base = f"{age_term} {ethnicity} person".strip()

        # 清理多余空格
        base = ' '.join(base.split())
        parts.append(base)

        # 1.5 面部特征（关键！）
        face_shape = physical.get('face_shape', '')
        if face_shape:
            parts.append(f"{face_shape} face")

        skin_tone = physical.get('skin_tone', '')
        if skin_tone:
            parts.append(f"{skin_tone} skin")

        eye_shape = physical.get('eye_shape', '')
        eye_color = physical.get('eye_color', '')
        if eye_shape and eye_color:
            parts.append(f"{eye_color} {eye_shape} eyes")
        elif eye_color:
            parts.append(f"{eye_color} eyes")

        # 2. 完整发型描述
        hair_color = physical.get('hair_color', '')
        hair_style = physical.get('hair_style', '')
        hair_length = physical.get('hair_length', '')

        hair_desc = []
        if hair_length:
            hair_desc.append(hair_length)
        if hair_color:
            hair_desc.append(hair_color)
        hair_desc.append('hair')
        if hair_style:
            hair_desc.append(f"with {hair_style}")

        if hair_color or hair_style:
            parts.append(' '.join(hair_desc))

        # 3. 关键配饰（眼镜等）- 放在服装前面因为更显眼
        clothing = character.get('clothing', {})
        accessories = clothing.get('accessories', [])

        # 优先提取眼镜
        glasses = [a for a in accessories if 'glass' in a.lower() or 'spectacle' in a.lower()]
        if glasses:
            parts.append(glasses[0])

        # 4. 上衣
        top = clothing.get('top', '')
        if top:
            # 简化上衣描述，保留颜色和类型
            parts.append(top)

        # 5. 下装
        bottom = clothing.get('bottom', '')
        if bottom:
            parts.append(bottom)

        # 6. 其他关键配饰（手表、耳环等）
        other_accessories = [a for a in accessories if 'glass' not in a.lower() and 'spectacle' not in a.lower()]
        if other_accessories:
            # 只取前2个
            parts.extend(other_accessories[:2])

        return ', '.join(parts)

    def _build_character_reference_mapping(
        self,
        characters: List[dict],
        characters_in_scene: List[str]
    ) -> str:
        """
        构建角色参考图映射

        输出示例（每角色1张fullbody参考图）：
        CHARACTER REFERENCE MAPPING:
        - Image 1: Li Ming (李明) - young Asian man, short black hair, gray button shirt
        - Image 2: Wang Xin (王欣) - young Asian woman, long black hair, white dress

        重要：按characters_in_scene的顺序构建，确保与图片传递顺序一致
        """
        if not characters_in_scene:
            return ""

        # 按characters_in_scene的顺序构建，确保与图片传递顺序一致
        scene_characters = []
        for char_id in characters_in_scene:
            for c in characters:
                if c.get('id') == char_id:
                    scene_characters.append(c)
                    break

        if not scene_characters:
            return ""

        lines = ["CHARACTER REFERENCE MAPPING:"]

        for i, char in enumerate(scene_characters):
            char_name_en = char.get('name_en') or char.get('name', 'Character')
            char_name_zh = char.get('name', '')
            identity = self._build_identity_line(char)

            # 格式：Image X: Name (中文名) - identity description [只有fullbody]
            image_idx = i + 1  # 从1开始
            if char_name_zh and char_name_zh != char_name_en:
                line = f"- Image {image_idx}: {char_name_en} ({char_name_zh}) - {identity}"
            else:
                line = f"- Image {image_idx}: {char_name_en} - {identity}"

            lines.append(line)

        return '\n'.join(lines)

    def _build_scene_direction(
        self,
        shot: dict,
        characters: List[dict],
        characters_in_scene: List[str]
    ) -> str:
        """
        构建场景指导 - 只描述动态属性（动作、位置、表情）

        重要：不包含任何外观描述（发型、服装、年龄等），
        因为外观已经在CHARACTER REFERENCE MAPPING中定义。

        输出示例：
        SCENE DIRECTION:
        Lin Xiaoyu is seated by the window, looking out with a pensive expression.
        Wang Rou stands at the checkout counter, holding instant noodles, gaze distant.
        """
        visual_desc = shot.get('visual_description', '')
        if not visual_desc:
            return ""

        cleaned_desc = visual_desc

        # 1. 替换char_id为角色英文名（在清洗外观之前）
        for char in characters:
            char_id = char.get('id', '')
            name_en = char.get('name_en') or char.get('name', '')
            if char_id and name_en:
                # 先处理 "Name (char_id)" 格式 -> "Name"
                pattern_with_name = rf'{re.escape(name_en)}\s*\({re.escape(char_id)}\)'
                cleaned_desc = re.sub(pattern_with_name, name_en, cleaned_desc)

                # 再处理单独的 "(char_id)" -> "Name"
                cleaned_desc = cleaned_desc.replace(f'({char_id})', name_en)

                # 最后处理裸 "char_id" -> "Name"（使用单词边界避免误替换）
                cleaned_desc = re.sub(rf'\b{re.escape(char_id)}\b', name_en, cleaned_desc)

        # 2. 移除所有外观描述（发型、服装、年龄等）
        cleaned_desc = self._remove_appearance_from_description(cleaned_desc)

        # 3. 清理各种名字重复格式
        for char in characters:
            name_en = char.get('name_en') or char.get('name', '')
            if name_en:
                # 处理 "Name (Name)" 格式 -> "Name"
                cleaned_desc = re.sub(
                    rf'{re.escape(name_en)}\s*\({re.escape(name_en)}\)',
                    name_en,
                    cleaned_desc
                )
                # 处理 "Name Name" 格式 -> "Name"
                cleaned_desc = re.sub(
                    rf'\b{re.escape(name_en)}\s+{re.escape(name_en)}\b',
                    name_en,
                    cleaned_desc
                )
                # 处理 "Name's Name" 格式（如 "Zhang Yi's Zhang Yi"）-> "Name's"
                cleaned_desc = re.sub(
                    rf"\b{re.escape(name_en)}'s\s+{re.escape(name_en)}\b",
                    f"{name_en}'s",
                    cleaned_desc
                )

        # 4. 清理多余空格和标点
        cleaned_desc = re.sub(r'\s+', ' ', cleaned_desc)
        cleaned_desc = re.sub(r',\s*,', ',', cleaned_desc)
        cleaned_desc = re.sub(r'\.\s*\.', '.', cleaned_desc)

        if not cleaned_desc.strip():
            return ""

        # 5. 构建角色-图片映射行（放在SCENE DIRECTION开头）
        char_mapping_parts = []
        for i, char_id in enumerate(characters_in_scene):
            char = next((c for c in characters if c.get('id') == char_id), None)
            if char:
                name_en = char.get('name_en') or char.get('name', '')
                char_mapping_parts.append(f"{name_en}=Image {i+1}")

        scene_content = cleaned_desc.strip()
        if char_mapping_parts:
            mapping_line = f"[Characters: {', '.join(char_mapping_parts)}]"
            scene_content = f"{mapping_line}\n\n{scene_content}"

        return f"SCENE DIRECTION:\n{scene_content}"

    def _remove_appearance_from_description(self, text: str) -> str:
        """
        移除外观描述词汇，只保留动作/位置/表情

        移除：
        - "a young woman with short dark hair"
        - "wearing a cream shirt"
        - "a man in his early 30s"
        - "with long black hair"
        - "a young woman" (独立的年龄性别描述)
        - "another young woman"

        保留：
        - "is seated by the window"
        - "looking out with a pensive expression"
        - "holding a bowl of instant noodles"
        - "with a thoughtful expression" (表情描述)
        """
        if not text:
            return text

        result = text

        # 1. 移除 "a young/old woman/man with [hair description]" 模式
        # 例如: "a young woman with short dark hair" -> ""
        result = re.sub(
            r',?\s*a\s+(?:young|old|middle-aged|teenage|elderly)?\s*(?:Asian|East Asian|Chinese|woman|man|person|lady|guy|girl|boy)(?:\s+(?:in\s+(?:her|his)\s+(?:early|mid|late)\s+\d+s|\w+))?\s+with\s+[^,\.]+(?:hair|locks)[^,\.]*[,\.]?',
            '',
            result,
            flags=re.IGNORECASE
        )

        # 2. 移除 "a young woman in [clothing]" 模式
        # 例如: "a young woman in a white dress" -> ""
        result = re.sub(
            r',?\s*a\s+(?:young|old|middle-aged|teenage|elderly)?\s*(?:Asian|East Asian|Chinese|woman|man|person|lady|guy|girl|boy)(?:\s+(?:in\s+(?:her|his)\s+(?:early|mid|late)\s+\d+s|\w+))?\s+in\s+(?:a\s+)?[^,\.]+[,\.]?',
            '',
            result,
            flags=re.IGNORECASE
        )

        # 3. 移除独立的 "with [hair description]" 模式
        # 例如: ", with short dark hair," -> ","
        result = re.sub(
            r',?\s*with\s+(?:short|long|medium|dark|light|blonde|black|brown|red|gray|grey|wavy|curly|straight|messy|neat|shoulder-length|waist-length)[\s\w-]*(?:hair|locks)[^,\.]*[,\.]?',
            '',
            result,
            flags=re.IGNORECASE
        )

        # 4. 移除 "wearing [clothing]" 模式
        # 例如: ", wearing a cream shirt," -> ","
        result = re.sub(
            r',?\s*wearing\s+(?:a\s+)?[^,\.]+[,\.]?',
            ',',
            result,
            flags=re.IGNORECASE
        )

        # 5. 移除 "dressed in [clothing]" 模式
        result = re.sub(
            r',?\s*dressed\s+in\s+(?:a\s+)?[^,\.]+[,\.]?',
            ',',
            result,
            flags=re.IGNORECASE
        )

        # 6. 移除 "in her/his early/mid/late 20s/30s" 年龄描述
        result = re.sub(
            r',?\s*in\s+(?:her|his)\s+(?:early|mid|late)\s+\d+s[,\.]?',
            '',
            result,
            flags=re.IGNORECASE
        )

        # 7. 移除独立的年龄+性别描述（逗号之间）
        # 例如: ", a young woman," -> ","
        result = re.sub(
            r',\s*a\s+(?:young|old|middle-aged|teenage|elderly)\s+(?:Asian|East Asian|Chinese)?\s*(?:woman|man|person|lady|guy|girl|boy)\s*,',
            ',',
            result,
            flags=re.IGNORECASE
        )

        # 8. 移除 "a young woman with a [adjective] expression" 但保留表情
        # 例如: "a young woman with a thoughtful expression" -> "with a thoughtful expression"
        result = re.sub(
            r',?\s*(?:another\s+)?a?\s*(?:young|old|middle-aged|teenage|elderly)?\s*(?:Asian|East Asian|Chinese)?\s*(?:woman|man|person|lady|guy|girl|boy)\s+with\s+(a\s+(?:thoughtful|pensive|tired|happy|sad|worried|anxious|calm|friendly|warm|gentle|serious|stern|curious|surprised|excited|nervous|relaxed)\s+expression)',
            r', \1',
            result,
            flags=re.IGNORECASE
        )

        # 9. 移除 "another young woman" / "a young woman" 后面跟逗号
        # 例如: ", another young woman," -> ","
        result = re.sub(
            r',?\s*(?:another\s+)?(?:a\s+)?(?:young|old|middle-aged|teenage|elderly)?\s*(?:Asian|East Asian|Chinese)?\s*(?:woman|man|person|lady|guy|girl|boy)\s*,',
            ',',
            result,
            flags=re.IGNORECASE
        )

        # 10. 移除名字后面紧跟的年龄性别描述
        # 例如: "Lin Shiyun, a young woman with a thoughtful expression"
        #    -> "Lin Shiyun, with a thoughtful expression"
        result = re.sub(
            r'(\w+),\s*(?:another\s+)?(?:a\s+)?(?:young|old|middle-aged|teenage|elderly)?\s*(?:Asian|East Asian|Chinese)?\s*(?:woman|man|person|lady|guy|girl|boy)(?:\s+with\s+(a\s+\w+\s+expression))?',
            lambda m: f"{m.group(1)}, {m.group(2)}" if m.group(2) else f"{m.group(1)}",
            result,
            flags=re.IGNORECASE
        )

        # 11. 清理结果
        result = re.sub(r'\s+', ' ', result)
        result = re.sub(r',\s*,', ',', result)
        result = re.sub(r'\.\s*\.', '.', result)
        result = re.sub(r'^\s*,\s*', '', result)
        result = re.sub(r',\s*$', '.', result)
        result = re.sub(r',\s+\.', '.', result)

        return result.strip()

    def _build_brief_identifier(self, character: dict) -> str:
        """
        构建角色的简短标识符

        目的：生成一个准确的识别标签，包含关键视觉特征。

        输出示例：
        - "young woman in cream sweater"
        - "young man with glasses in striped shirt"
        - "woman in medical scrubs"
        """
        parts = []

        # 1. 性别和年龄
        human_info = character.get('human', {})
        gender = human_info.get('gender') or character.get('gender', '')
        age = human_info.get('age_range') or character.get('age_appearance', '')

        age_map = {
            'child': 'young',
            'teenager': 'teenage',
            'young_adult': 'young',
            'adult': '',
            'middle_aged': 'middle-aged',
            'elderly': 'elderly'
        }
        age_term = age_map.get(age, '')

        if gender == 'female':
            parts.append(f"{age_term} woman".strip())
        elif gender == 'male':
            parts.append(f"{age_term} man".strip())
        else:
            parts.append("person")

        # 2. 检查是否有眼镜（非常显眼的特征）
        clothing = character.get('clothing', {})
        accessories = clothing.get('accessories', [])

        has_glasses = False
        for acc in accessories:
            if 'glass' in acc.lower() or 'spectacle' in acc.lower():
                has_glasses = True
                break

        if has_glasses:
            parts.append("with glasses")

        # 3. 服装特征
        top = clothing.get('top', '')

        if top:
            top_lower = top.lower()

            # 检查特殊服装类型
            if 'scrub' in top_lower or 'medical' in top_lower:
                parts.append("in medical scrubs")
            elif 'hoodie' in top_lower:
                # 提取颜色
                color = self._extract_color(top_lower)
                if color:
                    parts.append(f"in {color} hoodie")
                else:
                    parts.append("in hoodie")
            else:
                # 检查是否有条纹等图案
                has_pattern = ''
                if 'stripe' in top_lower:
                    has_pattern = 'striped'
                elif 'check' in top_lower or 'plaid' in top_lower:
                    has_pattern = 'checkered'

                # 提取颜色
                color = self._extract_color(top_lower)

                # 提取服装类型
                garment = self._extract_garment(top_lower)

                if garment:
                    desc_parts = []
                    if color:
                        desc_parts.append(color)
                    if has_pattern:
                        desc_parts.append(has_pattern)
                    desc_parts.append(garment)
                    parts.append(f"in {' '.join(desc_parts)}")

        return " ".join(parts)

    def _extract_color(self, text: str) -> str:
        """从文本中提取主要颜色"""
        colors = [
            ('cream', 'cream'), ('navy', 'navy'), ('burgundy', 'burgundy'),
            ('white', 'white'), ('black', 'black'), ('gray', 'gray'),
            ('grey', 'gray'), ('blue', 'blue'), ('red', 'red'),
            ('green', 'green'), ('pink', 'pink'), ('brown', 'brown'),
            ('beige', 'beige'), ('purple', 'purple'), ('light blue', 'light blue'),
            ('dark gray', 'dark gray'), ('light gray', 'light gray')
        ]

        for pattern, color_name in colors:
            if pattern in text:
                return color_name
        return ''

    def _extract_garment(self, text: str) -> str:
        """从文本中提取服装类型"""
        garments = [
            'sweater', 'shirt', 'blouse', 'jacket', 'coat', 'hoodie',
            'dress', 'apron', 'vest', 'cardigan', 't-shirt', 'top',
            'scrubs', 'uniform'
        ]

        for garment in garments:
            if garment in text:
                return garment
        return ''

    def _build_character_actions(
        self,
        shot: dict,
        characters: List[dict],
        characters_in_scene: List[str]
    ) -> str:
        """
        构建角色动作和位置描述

        从shot的visual_description中提取动作，不包含外貌描述
        """
        visual_desc = shot.get('visual_description', '')

        # 清洗掉外貌相关的描述
        cleaned = self._clean_visual_description(visual_desc)

        # 如果cleaned还有内容，直接使用
        if cleaned:
            return cleaned

        return ""

    def _build_atmosphere(
        self,
        shot: dict,
        scene_style: dict,
        mood: str
    ) -> str:
        """
        构建氛围和光线描述

        不涉及角色，只描述环境氛围
        """
        parts = []

        if scene_style:
            if scene_style.get('color_palette'):
                parts.append(f"{scene_style['color_palette']} color palette")
            if scene_style.get('lighting'):
                parts.append(f"{scene_style['lighting']} lighting")
            if scene_style.get('atmosphere'):
                parts.append(scene_style['atmosphere'])

        if mood and mood not in str(parts):
            parts.append(f"{mood} mood")

        return ", ".join(parts) if parts else ""

    def _build_character_description(self, character: dict) -> str:
        """
        从角色数据构建详细的外观描述（用于image prompt）

        优先从clothing和physical字段获取详细信息，确保角色一致性
        """
        desc_parts = []

        # 1. 物理外观 (physical)
        physical = character.get('physical', {})
        if physical:
            # 发型和发色（最重要的识别特征）
            hair_color = physical.get('hair_color', '')
            hair_style = physical.get('hair_style', '')
            if hair_color or hair_style:
                desc_parts.append(f"{hair_color} {hair_style}".strip())

            # 眼睛
            eye_color = physical.get('eye_color', '')
            eye_shape = physical.get('eye_shape', '')
            if eye_color:
                desc_parts.append(f"{eye_color} eyes")

            # 肤色
            skin_tone = physical.get('skin_tone', '')
            if skin_tone:
                desc_parts.append(f"{skin_tone} skin")

        # 2. 服装（clothing）- 非常重要，用于区分角色
        clothing = character.get('clothing', {})
        if clothing:
            # 上衣
            top = clothing.get('top', '')
            if top:
                desc_parts.append(f"wearing {top}")

            # 下装
            bottom = clothing.get('bottom', '')
            if bottom:
                desc_parts.append(bottom)

            # 配饰（非常重要，用于区分角色）
            accessories = clothing.get('accessories', [])
            if accessories:
                # 只取前2-3个最重要的配饰
                key_accessories = accessories[:3]
                desc_parts.append(", ".join(key_accessories))

            # 风格
            style = clothing.get('style', '')
            if style:
                desc_parts.append(f"{style} style")

        # 3. 如果没有详细字段，尝试使用description
        if not desc_parts:
            desc = character.get('description', '')
            if desc:
                return desc

        # 4. 兜底：尝试从animal字段构建（非人类角色）
        if not desc_parts and character.get('animal'):
            a = character['animal']
            return f"{a.get('fur_color', '')} {a.get('species', '')} with {a.get('eye_color', '')} eyes"

        return ", ".join(desc_parts) if desc_parts else ""

    def _create_shot_from_scene(
        self,
        scene: dict,
        characters: List[dict],
        style_preset: str
    ) -> dict:
        """
        将不需要拆分的scene直接转为shot
        """
        return {
            "image_prompt": build_image_prompt(scene, characters, style_preset),
            "negative_prompt": build_negative_prompt(style_preset),
            "narration_segment": scene.get('narration', ''),
            "shot_type": "中景",
            "visual_description": scene.get('visual_description', ''),
            "duration_hint": len(scene.get('narration', '')) / self.TTS_CHARS_PER_SECOND,
            "scene_style": scene.get('scene_style', {}),
            "story_phase": scene.get('story_phase', '')
        }

    async def generate_storyboard_with_llm(
        self,
        scenes: List[dict],
        characters: List[dict],
        style_preset: str,
        llm_client=None
    ) -> List[dict]:
        """
        使用LLM优化分镜决策（兼容旧接口）
        """
        # 使用新的拆分方法
        return await self.generate_storyboard_with_splitting(
            scenes=scenes,
            characters=characters,
            style_preset=style_preset
        )

    def validate_storyboard(self, storyboard: List[dict]) -> dict:
        """
        验证分镜数据完整性
        """
        errors = []
        warnings = []

        if not storyboard:
            errors.append("分镜列表为空")
            return {"valid": False, "errors": errors, "warnings": warnings}

        for i, scene_board in enumerate(storyboard):
            scene_id = scene_board.get("shot_id", scene_board.get("scene_id", i + 1))

            # 检查必要字段
            if not scene_board.get("image_prompt"):
                errors.append(f"场景 {scene_id} 缺少 image_prompt")

            # 检查prompt长度
            prompt = scene_board.get("image_prompt", "")
            if len(prompt) < 20:
                warnings.append(f"场景 {scene_id} 的prompt可能太短 ({len(prompt)} 字符)")
            elif len(prompt) > 2000:
                warnings.append(f"场景 {scene_id} 的prompt可能太长 ({len(prompt)} 字符)")

            # 检查宽高比
            aspect_ratio = scene_board.get("aspect_ratio", "")
            valid_ratios = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]
            if aspect_ratio and aspect_ratio not in valid_ratios:
                warnings.append(f"场景 {scene_id} 使用非标准宽高比: {aspect_ratio}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def estimate_generation_time(self, storyboard: List[dict]) -> dict:
        """
        估算图像生成所需时间
        """
        total_scenes = len(storyboard)
        seconds_per_scene = 15

        total_seconds = total_scenes * seconds_per_scene

        return {
            "total_scenes": total_scenes,
            "estimated_seconds_per_scene": seconds_per_scene,
            "estimated_total_seconds": total_seconds,
            "estimated_total_minutes": round(total_seconds / 60, 1)
        }

    def get_scene_summary(self, scene_board: dict) -> str:
        """
        获取场景的简短摘要（用于UI显示）
        """
        original_scene = scene_board.get("original_scene", {})
        location = original_scene.get("location", "Unknown location")
        time = original_scene.get("time", "")
        mood = original_scene.get("mood", "")

        parts = [location]
        if time:
            parts.append(time)
        if mood:
            parts.append(mood)

        return " - ".join(parts)
