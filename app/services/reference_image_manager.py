"""
参考图管理器

管理两类参考图：
1. 角色参考图：每个角色一张立绘
2. 环境参考图：每种场景类型一张（可选）

确保角色在不同场景中的视觉一致性

核心改进 (v2):
- 风格强制锁定：在所有prompt开头加入强制风格指令
- 串行生成：先生成肖像，再用肖像作为参考生成全身图
- 确保同一角色的肖像和全身图是同一个人
"""

import asyncio
from typing import Dict, Any, List, Optional
from PIL import Image, ImageDraw, ImageFont

from app.services.character_prompt_builder import CharacterPromptBuilder
from app.services.style_enforcer import StyleEnforcer
from app.models.style_config import ProjectStyleConfig


def _label_reference_image(image: Image.Image, label: str) -> Image.Image:
    """
    SQ-1: 在参考图左上角叠加身份标签（半透明黑底+白字）
    返回标注后的副本，不修改原图
    """
    labeled = image.copy().convert("RGBA")
    overlay = Image.new("RGBA", labeled.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_size = max(20, image.width // 20)
    font = None
    for font_path in [
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]:
        try:
            font = ImageFont.truetype(font_path, font_size)
            break
        except (OSError, IOError):
            continue
    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), label, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    padding = 8

    draw.rectangle(
        [4, 4, text_w + padding * 2 + 4, text_h + padding * 2 + 4],
        fill=(0, 0, 0, 180)
    )
    draw.text((padding + 4, padding + 4), label, fill=(255, 255, 255), font=font)

    labeled = Image.alpha_composite(labeled, overlay)
    return labeled.convert("RGB")


class ReferenceImageManager:
    """
    参考图管理器

    管理两类参考图：
    1. 角色参考图：每个角色多张参考图（肖像+全身）
    2. 环境参考图：每种场景类型一张（可选）
    """

    def __init__(self):
        # 新格式：{char_id: {'portrait': Image, 'fullbody': Image}}
        self.character_references: Dict[str, Dict[str, Image.Image]] = {}
        self.environment_references: Dict[str, Image.Image] = {}  # {scene_type: PIL.Image}
        self.character_names: Dict[str, str] = {}  # SQ-1: {char_id: name_en}
        self.character_builder = CharacterPromptBuilder()

    async def generate_character_reference(
        self,
        character: Dict[str, Any],
        project_style: ProjectStyleConfig,
        image_generator,
        ref_type: str = 'fullbody',
        portrait_ref: Optional[Image.Image] = None
    ) -> Dict[str, Any]:
        """
        生成角色参考图（单张）

        Args:
            character: 角色数据
            project_style: 项目风格配置
            image_generator: 图片生成器实例
            ref_type: 参考图类型 'portrait' 或 'fullbody'
            portrait_ref: 肖像参考图（用于全身图生成时确保人脸一致）

        Returns:
            生成结果
        """
        char_id = character.get('id')
        char_type = self._get_character_type(character)
        style_name = project_style.style_preset

        # 根据类型构建不同的prompt
        if ref_type == 'portrait':
            prompt = self._build_portrait_prompt(character, char_type, project_style)
            aspect_ratio = "2:3"  # 肖像用竖版（抖音适配）
            reference_images = None  # 肖像不需要参考图
        else:
            # 全身图：如果有肖像参考，传入以确保人脸一致
            prompt = self._build_reference_prompt(
                character, char_type, project_style,
                portrait_ref=portrait_ref
            )
            aspect_ratio = "2:3"  # 全身用竖版（抖音适配）
            # 如果有肖像参考图，传给图像生成器
            reference_images = [portrait_ref] if portrait_ref else None

        # 使用风格强制的负面提示词
        negative_prompt = StyleEnforcer.build_style_negative_prompt(style_name)
        # 添加角色类型特定的负面提示词
        type_negative = self._get_negative_prompt(char_type)
        negative_prompt = f"{negative_prompt}, {type_negative}"

        # 生成图像
        result = await image_generator.generate_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            aspect_ratio=aspect_ratio,
            reference_images=reference_images
        )

        # L3b: CONTENT_SAFETY → PromptRewriter 角色参考图改写重试（1 次）
        if not result.get('success') and result.get('error_type') == 'content_safety':
            char_name = character.get('name', 'Unknown')
            print(f"    ⚠️ {char_name} {ref_type} CONTENT_SAFETY → PromptRewriter 改写重试")
            try:
                from app.services.prompt_rewriter import get_rewriter
                rewriter = get_rewriter()
                rewritten = await rewriter.rewrite_char_ref(prompt)
                if rewritten:
                    result = await image_generator.generate_image(
                        prompt=rewritten,
                        negative_prompt=negative_prompt,
                        aspect_ratio=aspect_ratio,
                        reference_images=reference_images
                    )
            except Exception as rw_err:
                print(f"    ⚠️ PromptRewriter 角色改写异常: {rw_err}")

        if result.get('success') and result.get('pil_image'):
            if char_id not in self.character_references:
                self.character_references[char_id] = {}
            self.character_references[char_id][ref_type] = result['pil_image']
            # SQ-1: 存储角色英文名用于标注
            name_en = character.get('name_en', '') or character.get('name', 'Unknown')
            self.character_names[char_id] = name_en
            result['char_id'] = char_id
            result['char_name'] = character.get('name', 'Unknown')
            result['ref_type'] = ref_type

        return result

    async def generate_character_multi_refs(
        self,
        character: Dict[str, Any],
        project_style: ProjectStyleConfig,
        image_generator,
        delay: float = 3.0
    ) -> Dict[str, Any]:
        """
        生成角色的多张参考图（肖像+全身）- 串行生成确保一致性

        核心改进：
        1. 先生成肖像
        2. 用肖像作为参考图生成全身图
        3. 确保同一角色的肖像和全身图是同一个人

        Args:
            character: 角色数据
            project_style: 项目风格配置
            image_generator: 图片生成器实例
            delay: 请求间隔（秒）

        Returns:
            {ref_type: generation_result}
        """
        char_id = character.get('id')
        char_name = character.get('name', 'Unknown')
        results = {}

        # 1. 先生成正面肖像特写（作为基准参考）
        print(f"      [1/2] 生成 {char_name} 正面肖像（基准参考）...")
        portrait_result = await self.generate_character_reference(
            character=character,
            project_style=project_style,
            image_generator=image_generator,
            ref_type='portrait',
            portrait_ref=None  # 肖像不需要参考
        )
        results['portrait'] = portrait_result

        portrait_image = None
        if portrait_result.get('success'):
            portrait_image = portrait_result.get('pil_image')
            print(f"      ✅ {char_name} 肖像生成成功（将用于全身图参考）")
        else:
            print(f"      ❌ {char_name} 肖像生成失败: {portrait_result.get('error')}")
            print(f"      ⚠️ 全身图将在没有肖像参考的情况下生成")

        await asyncio.sleep(delay)

        # 2. 用肖像作为参考生成全身图（串行关键步骤）
        print(f"      [2/2] 生成 {char_name} 全身视图（使用肖像作为参考）...")
        fullbody_result = await self.generate_character_reference(
            character=character,
            project_style=project_style,
            image_generator=image_generator,
            ref_type='fullbody',
            portrait_ref=portrait_image  # 传入肖像作为参考！
        )
        results['fullbody'] = fullbody_result

        if fullbody_result.get('success'):
            if portrait_image:
                print(f"      ✅ {char_name} 全身图生成成功（已使用肖像参考）")
            else:
                print(f"      ✅ {char_name} 全身图生成成功（无肖像参考）")
        else:
            print(f"      ❌ {char_name} 全身图生成失败: {fullbody_result.get('error')}")

        return results

    def _build_portrait_prompt(
        self,
        character: Dict[str, Any],
        char_type: str,
        project_style: ProjectStyleConfig
    ) -> str:
        """构建正面肖像参考图prompt - 强调面部细节 + 风格强制"""
        char_desc = self.character_builder.build_character_prompt(character)

        # 尝试获取精细面部描述
        face_desc = ""
        if hasattr(self.character_builder, 'build_face_description'):
            face_desc = self.character_builder.build_face_description(character)

        # 获取风格名称
        style_name = project_style.style_preset

        if char_type == 'human':
            # 构建核心prompt内容（不含风格前缀）
            # 关键改进：将面部特征放在最前面并使用强调语法
            core_prompt = f"""CLOSE-UP PORTRAIT - CHARACTER REFERENCE

═══════════════════════════════════════════════════════════
CRITICAL FACIAL FEATURES - MUST MATCH EXACTLY
═══════════════════════════════════════════════════════════
{f"{face_desc}" if face_desc else ""}

These facial features are UNIQUE to this character and MUST be rendered precisely.
DO NOT use generic/default Asian beauty face template.
═══════════════════════════════════════════════════════════

{char_desc}

COMPOSITION:
- Front-facing portrait view, eye-level camera angle
- Head and shoulders framing
- Simple solid neutral background
- Soft studio lighting, no harsh shadows

FACE RENDERING REQUIREMENTS:
- Face shape: Render the EXACT face shape specified above (oval/round/square/heart/etc)
- Eyes: Match the EXACT eye shape, size, and color described
- Nose: Follow the SPECIFIC nose description (small/prominent/button/straight/etc)
- Lips: Match the lip fullness and shape exactly
- Eyebrows: Render according to description (thin/thick/arched/straight)
- Skin: Use the specified skin tone accurately

IMPORTANT: This is the MASTER REFERENCE for this character's face.
All subsequent images of this character must match this exact face.
Each character has UNIQUE facial features - do not homogenize.

Single person only, no other people, no text, no logos."""

        else:
            # 非人类角色使用简化的肖像prompt
            core_prompt = f"""CLOSE-UP REFERENCE - CHARACTER HEAD/FACE
{char_desc}

Front-facing close-up view focusing on head and face area.
Clear details of all distinctive features.
Single character only, simple solid background, no text."""

        # T14+T19: 跨年龄风格统一指令（强化版）
        age_appearance = character.get('age_appearance', '')
        young_ages = {'child', 'teen', 'teenager', 'young_adult', 'baby', 'toddler', 'kid'}
        is_young = age_appearance.lower() in young_ages if age_appearance else False

        core_prompt += f"""

CROSS-AGE STYLE CONSISTENCY (MANDATORY):
This character MUST be rendered in {style_name} style — the SAME style used for every
other character in this story, regardless of age, gender, or body type.

Requirements:
- IDENTICAL line weight, shading technique, and level of stylization as all other characters
- Express age differences through FACIAL FEATURES (wrinkles, skin smoothness, face proportions,
  eye size) and BODY PROPORTIONS (height, build) — NOT through art style changes
- DO NOT shift toward anime, chibi, or cartoon for younger characters
- DO NOT shift toward photorealistic or painterly for older characters
- A child and an elderly person in the same story must look like they belong in the same artwork"""

        if is_young:
            core_prompt += f"""

AGE-SPECIFIC STYLE ANCHOR (this character appears young — {age_appearance}):
Even though this character is young, render with the EXACT SAME {style_name} technique
as adult characters. Show youth through softer facial features, rounder face shape,
and smaller build — NOT by switching to a cuter or more cartoon-like art style."""

        # 应用风格强制
        enforced_prompt = StyleEnforcer.enforce_prompt(
            core_prompt,
            style_name,
            add_quality_suffix=True
        )

        return enforced_prompt

    async def generate_all_character_references(
        self,
        characters: List[Dict[str, Any]],
        project_style: ProjectStyleConfig,
        image_generator,
        delay: float = 3.0
    ) -> Dict[str, Dict[str, Any]]:
        """
        为所有角色生成参考图

        Args:
            characters: 角色列表
            project_style: 项目风格配置
            image_generator: 图片生成器实例
            delay: 请求间隔（秒）

        Returns:
            {char_id: generation_result}
        """
        results = {}

        for i, char in enumerate(characters):
            char_id = char.get('id')
            char_name = char.get('name', 'Unknown')

            print(f"  生成角色参考图 [{i+1}/{len(characters)}]: {char_name}...")

            result = await self.generate_character_reference(
                character=char,
                project_style=project_style,
                image_generator=image_generator
            )

            results[char_id] = result

            if result.get('success'):
                print(f"    ✅ {char_name} 参考图生成成功")
            else:
                print(f"    ❌ {char_name} 参考图生成失败: {result.get('error')}")

            # 避免API速率限制
            if i < len(characters) - 1:
                await asyncio.sleep(delay)

        return results

    def _build_reference_prompt(
        self,
        character: Dict[str, Any],
        char_type: str,
        project_style: ProjectStyleConfig,
        portrait_ref: Optional[Image.Image] = None
    ) -> str:
        """
        构建角色全身参考图prompt + 风格强制

        Args:
            character: 角色数据
            char_type: 角色类型
            project_style: 项目风格配置
            portrait_ref: 肖像参考图（用于确保全身图与肖像一致）
        """
        # 使用CharacterPromptBuilder生成详细角色描述
        char_desc = self.character_builder.build_character_prompt(character)
        style_name = project_style.style_preset

        # 如果有肖像参考，添加一致性指令
        consistency_instruction = ""
        if portrait_ref is not None:
            consistency_instruction = """
CRITICAL FACE CONSISTENCY:
The face in this full-body image MUST be IDENTICAL to the provided portrait reference.
Same person, same facial features, same expression style.
DO NOT generate a different-looking person.
"""

        # 根据角色类型选择合适的参考图模板
        if char_type == 'animal':
            core_prompt = f"""FULL BODY CHARACTER REFERENCE
{char_desc}

COMPOSITION:
- Full body view, 3/4 angle showing the complete animal
- Simple solid light gray background
- Clear view of all body parts and features

DETAILS TO CAPTURE:
- Fur/feathers color, pattern, and texture
- Body shape and proportions
- Eyes, ears, nose, tail details
- All distinctive markings

Single animal character only, no humans, no other animals, no text."""

        elif char_type == 'human':
            core_prompt = f"""FULL BODY CHARACTER REFERENCE
{char_desc}
{consistency_instruction}
COMPOSITION:
- Full body standing pose, 3/4 angle
- Simple solid neutral background
- Head to toe visible, natural pose

DETAILS TO CAPTURE:
- Face (MUST match portrait reference if provided)
- Hair color, style, and length
- Complete outfit from head to toe
- Body proportions and posture
- All clothing details and accessories

Single person only, no other people, no text, no logos."""
        else:
            # 其他所有非人类角色类型使用通用模板
            type_labels = {
                'robot': 'robot/mecha',
                'insect': 'insect',
                'aquatic': 'aquatic creature',
                'plant': 'plant character',
                'mythological': 'mythological creature',
                'supernatural': 'supernatural being',
                'undead': 'undead character',
                'elemental': 'elemental being',
                'alien': 'alien creature',
                'vehicle_character': 'vehicle character',
                'digital_virtual': 'digital/virtual character',
                'concept_personified': 'personified concept',
                'miniature': 'miniature character',
                'giant': 'giant character',
                'fantasy_creature': 'fantasy creature',
                'object': 'personified object',
                'hybrid': 'hybrid character',
            }
            type_label = type_labels.get(char_type, 'character')

            core_prompt = f"""FULL BODY CHARACTER REFERENCE - {type_label.upper()}
{char_desc}

COMPOSITION:
- Full body view, 3/4 angle
- Simple solid neutral background
- Clear view of all distinctive features

Single {type_label} only, no other elements, no text."""

        # T14+T19: 跨年龄风格统一指令（强化版）
        age_appearance = character.get('age_appearance', '')
        young_ages = {'child', 'teen', 'teenager', 'young_adult', 'baby', 'toddler', 'kid'}
        is_young = age_appearance.lower() in young_ages if age_appearance else False

        core_prompt += f"""

CROSS-AGE STYLE CONSISTENCY (MANDATORY):
This character MUST be rendered in {style_name} style — the SAME style used for every
other character in this story, regardless of age, gender, or body type.

Requirements:
- IDENTICAL line weight, shading technique, and level of stylization as all other characters
- Express age differences through FACIAL FEATURES (wrinkles, skin smoothness, face proportions,
  eye size) and BODY PROPORTIONS (height, build) — NOT through art style changes
- DO NOT shift toward anime, chibi, or cartoon for younger characters
- DO NOT shift toward photorealistic or painterly for older characters
- A child and an elderly person in the same story must look like they belong in the same artwork"""

        if is_young:
            core_prompt += f"""

AGE-SPECIFIC STYLE ANCHOR (this character appears young — {age_appearance}):
Even though this character is young, render with the EXACT SAME {style_name} technique
as adult characters. Show youth through softer facial features, rounder face shape,
and smaller build — NOT by switching to a cuter or more cartoon-like art style."""

        # 应用风格强制（适用于所有角色类型）
        enforced_prompt = StyleEnforcer.enforce_prompt(
            core_prompt,
            style_name,
            add_quality_suffix=True
        )

        return enforced_prompt

    def _get_negative_prompt(self, char_type: str) -> str:
        """根据角色类型生成negative prompt"""
        base = "blurry, low quality, multiple characters, complex background, busy background"
        base += ", text, watermark, signature, cropped, out of frame"

        type_specific = {
            # 基础类型
            'human': ", animal features, cartoon proportions, furry, animal ears, tail",
            'animal': ", human features, human face, human body, humanoid, person, hands, fingers",
            'robot': ", organic features, flesh, skin, human face, fur, feathers",
            'fantasy_creature': ", modern elements, realistic photo, real world objects",
            'object': ", human features, animal features, realistic proportions",
            'hybrid': ", pure human, pure animal, inconsistent features",

            # 昆虫类型
            'insect': ", human features, mammal features, fur, hair, humanoid face, person",

            # 水生生物类型
            'aquatic': ", human features, land animal features, fur, legs (for fish), humanoid face, person",

            # 植物类型
            'plant': ", human features, animal features, fur, feathers, humanoid proportions, person",

            # 神话生物类型
            'mythological': ", modern technology, realistic photo, contemporary clothing, mundane objects",

            # 超自然类型
            'supernatural': ", mundane, ordinary, non-magical appearance, plain clothing",

            # 亡灵类型
            'undead': ", healthy skin, living appearance, warm colors, vibrant, lively expression",

            # 元素生物类型
            'elemental': ", human features, animal features, solid body (unless appropriate), normal skin",

            # 外星生物类型
            'alien': ", human features, earth animal features, familiar earth objects",

            # 载具角色类型
            'vehicle_character': ", human body, animal body, organic limbs, biological features",

            # 数字/虚拟角色类型
            'digital_virtual': ", organic texture, natural materials, non-digital appearance",

            # 概念拟人类型
            'concept_personified': ", ordinary person, mundane appearance, without symbolic elements",

            # 微型角色类型
            'miniature': ", normal scale, giant proportions, incorrect size reference",

            # 巨型角色类型
            'giant': ", normal human scale, tiny proportions, incorrect size reference",
        }

        return f"{base}{type_specific.get(char_type, '')}"

    def _get_character_type(self, character: Dict[str, Any]) -> str:
        """
        获取角色类型 - 只从 character_type 字段读取

        如果没有 character_type 字段，返回 'unknown' 并打印警告
        这会让错误的数据格式快速暴露，而不是静默fallback到可能错误的类型
        """
        char_type = character.get('character_type')
        if char_type:
            return char_type

        # 没有 character_type 字段，打印警告并返回 unknown
        char_name = character.get('name', 'Unknown')
        print(f"  ⚠️ [ReferenceImageManager] 角色 '{char_name}' 缺少 character_type 字段，请检查 story.json")
        return 'unknown'

    def get_references_for_scene(self, character_ids: List[str]) -> List[Image.Image]:
        """
        获取场景中角色的参考图列表（肖像+全身）

        Args:
            character_ids: 角色ID列表

        Returns:
            参考图列表（每个角色最多2张：肖像+全身）
        """
        refs = []
        for char_id in character_ids:
            if char_id in self.character_references:
                char_refs = self.character_references[char_id]
                # 标准格式：{'portrait': Image, 'fullbody': Image}
                if 'portrait' in char_refs:
                    refs.append(char_refs['portrait'])
                if 'fullbody' in char_refs:
                    refs.append(char_refs['fullbody'])
        return refs

    def get_smart_references_for_scene(
        self, character_ids: List[str], shot_type: str = "medium_shot"
    ) -> List[Image.Image]:
        """
        SQ-2: 智能参考图选择 — 每角色 1 张，根据 shot_type 决定用 portrait 或 fullbody

        规则：
        - close_up / extreme_close_up / medium_close_up → portrait
        - 其余 (wide, medium, etc.) → fullbody

        Args:
            character_ids: 角色ID列表
            shot_type: 当前 shot 的景别

        Returns:
            参考图列表（每个角色 1 张）
        """
        portrait_types = {"close_up", "extreme_close_up", "medium_close_up"}
        # T20: medium_shot + ≤2 角色也使用 portrait（面部细节更丰富，提升一致性）
        if shot_type == "medium_shot" and len(character_ids) <= 2:
            use_portrait = True
        else:
            use_portrait = shot_type in portrait_types

        refs = []
        for char_id in character_ids:
            if char_id in self.character_references:
                char_refs = self.character_references[char_id]
                name_en = self.character_names.get(char_id, char_id)

                if use_portrait and 'portrait' in char_refs:
                    ref_type = 'portrait'
                    img = char_refs['portrait']
                elif 'fullbody' in char_refs:
                    ref_type = 'fullbody'
                    img = char_refs['fullbody']
                elif 'portrait' in char_refs:
                    ref_type = 'portrait'
                    img = char_refs['portrait']
                else:
                    continue

                # T11: 移除 _label_reference_image() 调用，直接返回原图
                # 原因: PIL 标签被 Gemini 在生成图中复现（标签泄露）
                refs.append(img)
        return refs

    def get_portrait_refs(self, character_ids: List[str]) -> List[Image.Image]:
        """只获取肖像参考图"""
        refs = []
        for char_id in character_ids:
            if char_id in self.character_references:
                char_refs = self.character_references[char_id]
                if isinstance(char_refs, dict) and 'portrait' in char_refs:
                    refs.append(char_refs['portrait'])
        return refs

    def get_fullbody_refs(self, character_ids: List[str]) -> List[Image.Image]:
        """只获取全身参考图"""
        refs = []
        for char_id in character_ids:
            if char_id in self.character_references:
                char_refs = self.character_references[char_id]
                if isinstance(char_refs, dict) and 'fullbody' in char_refs:
                    refs.append(char_refs['fullbody'])
        return refs

    def get_all_references(self) -> Dict[str, Image.Image]:
        """获取所有角色参考图"""
        return self.character_references.copy()

    def has_reference(self, char_id: str) -> bool:
        """检查是否有某角色的参考图"""
        return char_id in self.character_references

    def set_reference(self, char_id: str, image: Image.Image):
        """手动设置角色参考图"""
        self.character_references[char_id] = image

    def clear_references(self):
        """清空所有参考图"""
        self.character_references.clear()
        self.environment_references.clear()

    def save_all_references(self, output_dir: str) -> Dict[str, Dict[str, str]]:
        """
        保存所有参考图到目录

        Args:
            output_dir: 输出目录

        Returns:
            {char_id: {ref_type: file_path}}
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        saved = {}
        for char_id, char_refs in self.character_references.items():
            # 标准格式：{'portrait': Image, 'fullbody': Image}
            saved[char_id] = {}
            for ref_type, image in char_refs.items():
                file_path = os.path.join(output_dir, f"{char_id}_{ref_type}.png")
                image.save(file_path)
                saved[char_id][ref_type] = file_path

        return saved


def create_reference_manager() -> ReferenceImageManager:
    """创建ReferenceImageManager实例"""
    return ReferenceImageManager()
