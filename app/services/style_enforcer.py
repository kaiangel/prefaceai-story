"""
风格强制锁定器 (Style Enforcer)

解决核心问题：风格参数没有强制传递到每个环节
- 确保所有图像生成使用完全相同的视觉风格
- 在prompt开头加入不可忽略的风格强制指令
- 提供风格对应的负面提示词

设计原则：
1. 风格指令放在prompt最开头，不可被后续内容覆盖
2. 明确列出禁止的风格，防止AI混淆
3. 每种风格有对应的强制关键词和禁止关键词
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class StyleEnforcement:
    """风格强制配置"""
    style_name: str                    # 风格名称
    style_display_name: str            # 显示名称
    mandatory_keywords: List[str]      # 必须包含的关键词
    forbidden_keywords: List[str]      # 必须排除的关键词
    style_description: str             # 风格描述
    quality_keywords: List[str]        # 质量关键词


class StyleEnforcer:
    """
    风格强制锁定器

    确保所有生成的图像使用完全一致的视觉风格
    """

    # 风格强制配置表
    STYLE_ENFORCEMENTS: Dict[str, StyleEnforcement] = {
        # ============ 写实风格 ============
        "realistic": StyleEnforcement(
            style_name="realistic",
            style_display_name="Photorealistic Photography",
            mandatory_keywords=[
                "photorealistic", "photograph", "real photo", "professional photography",
                "natural skin texture", "realistic lighting", "photographic quality",
                "lifelike", "real human"
            ],
            forbidden_keywords=[
                "cartoon", "anime", "illustration", "drawing", "painting",
                "3D render", "CGI", "Pixar", "Disney", "stylized",
                "cel-shaded", "vector", "flat colors", "manga", "comic",
                "artistic interpretation", "digital art"
            ],
            style_description="This image MUST look like a real photograph taken with a professional camera. Natural lighting, realistic textures, no stylization.",
            quality_keywords=["8K", "high resolution", "sharp focus", "professional lighting", "DSLR quality"]
        ),

        # ============ 卡通/动画风格 ============
        "cartoon": StyleEnforcement(
            style_name="cartoon",
            style_display_name="Cartoon Animation",
            mandatory_keywords=[
                "cartoon style", "animated", "vibrant colors", "clean lines",
                "expressive characters", "animated movie quality"
            ],
            forbidden_keywords=[
                "photorealistic", "photograph", "real photo", "lifelike",
                "realistic skin", "natural lighting"
            ],
            style_description="This image MUST be in cartoon animation style with vibrant colors, clean outlines, and expressive character designs.",
            quality_keywords=["high quality animation", "professional cartoon", "polished artwork"]
        ),

        "pixar_3d": StyleEnforcement(
            style_name="pixar_3d",
            style_display_name="Pixar 3D Animation",
            mandatory_keywords=[
                "Pixar style", "3D animation", "smooth surfaces", "subsurface scattering",
                "cinematic lighting", "expressive 3D characters", "volumetric lighting"
            ],
            forbidden_keywords=[
                "photorealistic", "photograph", "real photo", "2D", "flat",
                "anime", "manga", "hand-drawn", "sketch"
            ],
            style_description="This image MUST be in Pixar 3D animation style with smooth 3D surfaces, expressive characters, and cinematic lighting.",
            quality_keywords=["high quality 3D render", "professional animation", "studio quality"]
        ),

        # ============ 日式动画风格 ============
        "anime": StyleEnforcement(
            style_name="anime",
            style_display_name="Japanese Anime",
            mandatory_keywords=[
                "anime style", "Japanese animation", "cel shading", "expressive eyes",
                "dynamic poses", "anime aesthetic"
            ],
            forbidden_keywords=[
                "photorealistic", "photograph", "3D render", "Pixar",
                "Western cartoon", "realistic skin"
            ],
            style_description="This image MUST be in Japanese anime style with characteristic cel shading, expressive eyes, and anime aesthetics.",
            quality_keywords=["high quality anime", "professional anime art", "detailed anime"]
        ),

        "ghibli": StyleEnforcement(
            style_name="ghibli",
            style_display_name="Studio Ghibli Style",
            mandatory_keywords=[
                "Studio Ghibli style", "Miyazaki inspired", "hand-drawn animation",
                "soft colors", "detailed backgrounds", "whimsical atmosphere"
            ],
            forbidden_keywords=[
                "photorealistic", "3D render", "digital 3D", "harsh lighting",
                "dark gritty", "modern CGI"
            ],
            style_description="This image MUST be in Studio Ghibli style with hand-drawn aesthetics, soft watercolor-like colors, and detailed natural backgrounds.",
            quality_keywords=["Ghibli quality", "masterful animation", "hand-painted look"]
        ),

        # ============ 插画风格 ============
        "illustration": StyleEnforcement(
            style_name="illustration",
            style_display_name="Digital Illustration",
            mandatory_keywords=[
                "digital illustration", "vibrant colors", "detailed artwork",
                "concept art", "clean lines", "rich details"
            ],
            forbidden_keywords=[
                "photorealistic", "photograph", "3D render",
                "low quality", "sketch", "unfinished"
            ],
            style_description="This image MUST be in polished digital illustration style with vibrant colors, clean lines, and rich details.",
            quality_keywords=["artstation trending", "professional illustration", "high detail"]
        ),

        # ============ 水彩风格 ============
        "watercolor": StyleEnforcement(
            style_name="watercolor",
            style_display_name="Watercolor Painting",
            mandatory_keywords=[
                "watercolor painting", "soft edges", "dreamy atmosphere",
                "flowing colors", "wet on wet technique", "artistic"
            ],
            forbidden_keywords=[
                "photorealistic", "sharp edges", "3D render", "digital",
                "hard lines", "neon colors"
            ],
            style_description="This image MUST be in watercolor painting style with soft edges, dreamy atmosphere, and flowing colors.",
            quality_keywords=["beautiful watercolor", "artistic quality", "delicate washes"]
        ),

        # ============ 儿童绘本风格 ============
        "children_book": StyleEnforcement(
            style_name="children_book",
            style_display_name="Children's Book Illustration",
            mandatory_keywords=[
                "children's book illustration", "friendly characters", "soft colors",
                "whimsical", "storybook style", "child-friendly"
            ],
            forbidden_keywords=[
                "photorealistic", "scary", "dark", "violent",
                "mature content", "horror", "realistic violence"
            ],
            style_description="This image MUST be in children's book illustration style with friendly characters, soft colors, and whimsical charm.",
            quality_keywords=["professional children's illustration", "picture book quality", "appealing to children"]
        ),

        # ============ 漫画风格 ============
        "manga": StyleEnforcement(
            style_name="manga",
            style_display_name="Japanese Manga",
            mandatory_keywords=[
                "manga style", "Japanese comic", "screentone", "expressive",
                "dynamic composition", "manga aesthetic"
            ],
            forbidden_keywords=[
                "photorealistic", "3D render", "Western comic style",
                "full color realistic"
            ],
            style_description="This image MUST be in Japanese manga style with characteristic screentone effects, expressive linework, and dynamic composition.",
            quality_keywords=["professional manga", "detailed linework", "high quality manga art"]
        ),

        # ============ 油画风格 ============
        "oil_painting": StyleEnforcement(
            style_name="oil_painting",
            style_display_name="Oil Painting",
            mandatory_keywords=[
                "oil painting", "visible brushstrokes", "classical art",
                "rich textures", "painterly", "artistic"
            ],
            forbidden_keywords=[
                "photorealistic", "digital", "flat colors", "vector",
                "anime", "cartoon"
            ],
            style_description="This image MUST be in oil painting style with visible brushstrokes, rich textures, and classical art aesthetics.",
            quality_keywords=["museum quality", "masterful painting", "fine art"]
        ),

        # ============ 赛博朋克风格 ============
        "cyberpunk": StyleEnforcement(
            style_name="cyberpunk",
            style_display_name="Cyberpunk Aesthetic",
            mandatory_keywords=[
                "cyberpunk", "neon lights", "futuristic city", "dark atmosphere",
                "high tech low life", "blade runner aesthetic"
            ],
            forbidden_keywords=[
                "pastoral", "rural", "ancient", "medieval",
                "bright daylight", "nature scene"
            ],
            style_description="This image MUST be in cyberpunk aesthetic with neon lights, dark futuristic atmosphere, and high-tech urban environment.",
            quality_keywords=["atmospheric", "cinematic cyberpunk", "detailed futuristic"]
        ),

        # ============ 中国水墨风格 ============
        "ink": StyleEnforcement(
            style_name="ink",
            style_display_name="Chinese Ink Wash Painting",
            mandatory_keywords=[
                "Chinese ink wash", "sumi-e", "brush strokes", "minimalist",
                "traditional Chinese art", "rice paper texture"
            ],
            forbidden_keywords=[
                "colorful", "neon", "photorealistic", "3D render",
                "Western art", "digital effects"
            ],
            style_description="This image MUST be in traditional Chinese ink wash painting style with elegant brush strokes, minimalist composition, and ink gradients.",
            quality_keywords=["elegant", "masterful brushwork", "traditional aesthetics"]
        ),

        # ============ 像素艺术风格 ============
        "pixel": StyleEnforcement(
            style_name="pixel",
            style_display_name="Pixel Art",
            mandatory_keywords=[
                "pixel art", "retro game", "16-bit", "crisp pixels",
                "limited color palette", "nostalgic gaming"
            ],
            forbidden_keywords=[
                "photorealistic", "smooth gradients", "high resolution photo",
                "3D render", "anti-aliased"
            ],
            style_description="This image MUST be in pixel art style with visible pixels, limited color palette, and retro game aesthetics.",
            quality_keywords=["clean pixels", "well-designed pixel art", "professional retro"]
        ),
    }

    @classmethod
    def get_enforcement(cls, style_name: str) -> Optional[StyleEnforcement]:
        """获取风格强制配置"""
        return cls.STYLE_ENFORCEMENTS.get(style_name)

    @classmethod
    def build_mandatory_prefix(cls, style_name: str) -> str:
        """
        构建强制风格前缀
        这个前缀必须放在所有prompt的最开头
        """
        enforcement = cls.get_enforcement(style_name)

        if not enforcement:
            # 如果没有预定义的强制配置，使用通用模板
            return cls._build_generic_prefix(style_name)

        mandatory_str = ", ".join(enforcement.mandatory_keywords[:5])
        forbidden_str = ", ".join(enforcement.forbidden_keywords[:8])

        prefix = f"""═══════════════════════════════════════════════════════════
MANDATORY STYLE REQUIREMENT - DO NOT IGNORE THIS SECTION
═══════════════════════════════════════════════════════════

STYLE: {enforcement.style_display_name}

{enforcement.style_description}

MUST INCLUDE: {mandatory_str}

DO NOT USE: {forbidden_str}

This style requirement applies to ALL elements in this image.
═══════════════════════════════════════════════════════════

"""
        return prefix

    @classmethod
    def _build_generic_prefix(cls, style_name: str) -> str:
        """构建通用风格前缀（用于未预定义的风格）"""
        return f"""═══════════════════════════════════════════════════════════
MANDATORY STYLE REQUIREMENT - DO NOT IGNORE
═══════════════════════════════════════════════════════════

STYLE: {style_name}

This image MUST be rendered in {style_name} style consistently.
Maintain visual consistency with all other images in this project.

═══════════════════════════════════════════════════════════

"""

    @classmethod
    def build_style_negative_prompt(cls, style_name: str) -> str:
        """构建风格对应的负面提示词"""
        enforcement = cls.get_enforcement(style_name)

        base_negatives = [
            "blurry", "low quality", "distorted", "deformed",
            "bad anatomy", "extra limbs", "text", "watermark",
            "signature", "cropped", "out of frame"
        ]

        if enforcement:
            # 添加该风格禁止的关键词
            style_negatives = enforcement.forbidden_keywords
            all_negatives = base_negatives + style_negatives
        else:
            all_negatives = base_negatives

        return ", ".join(all_negatives)

    @classmethod
    def build_quality_suffix(cls, style_name: str) -> str:
        """构建质量后缀"""
        enforcement = cls.get_enforcement(style_name)

        if enforcement:
            return ", ".join(enforcement.quality_keywords)
        else:
            return "high quality, detailed, professional"

    @classmethod
    def enforce_prompt(
        cls,
        original_prompt: str,
        style_name: str,
        add_quality_suffix: bool = True
    ) -> str:
        """
        对原始prompt应用风格强制

        Args:
            original_prompt: 原始prompt
            style_name: 风格名称
            add_quality_suffix: 是否添加质量后缀

        Returns:
            强制风格后的prompt
        """
        prefix = cls.build_mandatory_prefix(style_name)

        if add_quality_suffix:
            suffix = f"\n\n{cls.build_quality_suffix(style_name)}"
        else:
            suffix = ""

        return f"{prefix}{original_prompt}{suffix}"

    @classmethod
    def get_supported_styles(cls) -> List[str]:
        """获取所有支持强制锁定的风格列表"""
        return list(cls.STYLE_ENFORCEMENTS.keys())


# ================================================================
# 便捷函数
# ================================================================

def enforce_style(prompt: str, style_name: str) -> str:
    """快捷函数：对prompt应用风格强制"""
    return StyleEnforcer.enforce_prompt(prompt, style_name)


def get_style_negative(style_name: str) -> str:
    """快捷函数：获取风格负面提示词"""
    return StyleEnforcer.build_style_negative_prompt(style_name)
