"""
项目风格配置 - 确保整个故事的视觉风格统一

支持 80+ 种视觉风格，分为以下类别：
- 艺术媒介/技法
- 艺术流派
- 文化/地域
- 时代/流行风格
- 现代数字/动画风格
- 漫画类型
- 氛围/情绪
- 特定应用
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum


class StyleCategory(str, Enum):
    """风格类别"""
    MEDIUM = "medium"                   # 艺术媒介/技法
    ART_MOVEMENT = "art_movement"       # 艺术流派
    CULTURAL = "cultural"               # 文化/地域
    ERA_TREND = "era_trend"             # 时代/流行风格
    DIGITAL_ANIMATION = "digital_animation"  # 现代数字/动画风格
    COMIC = "comic"                     # 漫画类型
    MOOD = "mood"                       # 氛围/情绪
    APPLICATION = "application"         # 特定应用


class ProjectStyleConfig(BaseModel):
    """
    项目级别的风格配置
    确保整个故事的视觉风格统一
    """
    # 基础风格
    style_preset: str = "cartoon"         # 风格预设名称

    # 色调配置
    color_palette: str = "warm"           # "warm", "cold", "neutral", "vibrant", "muted"
    dominant_colors: List[str] = []       # 主色调 ["golden", "cream"]

    # 光影风格
    lighting_style: str = "natural"       # "natural", "dramatic", "soft", "neon", "cinematic"
    time_of_day_default: str = "day"      # "day", "night", "dawn", "dusk"

    # 美术风格细节
    line_style: Optional[str] = None      # "clean", "sketchy", "no_outline"
    texture_style: Optional[str] = None   # "smooth", "textured", "painterly"
    detail_level: str = "detailed"        # "minimal", "moderate", "detailed"

    # 时代/世界观
    era: Optional[str] = None             # "modern", "ancient", "futuristic", "fantasy"
    world_setting: Optional[str] = None   # "urban", "rural", "space", "underwater"

    # 渲染风格
    rendering: Optional[str] = None       # "soft", "sharp", "painterly"

    # 固定的风格prompt片段（每张图都会加上）
    style_suffix: str = ""                # 自动生成的风格描述

    # 自定义风格覆盖（从用户上传风格参考图分析生成）
    custom_enforcement: Optional[Any] = None

    # 来自story.json的原始visual_style
    raw_visual_style: Optional[Dict[str, Any]] = None


class StyleConfigBuilder:
    """
    根据配置生成风格prompt
    支持 80+ 种视觉风格
    """

    # ================================================================
    # 完整的风格模板库 (80+ 种风格)
    # ================================================================

    STYLE_TEMPLATES = {
        # ============ 基础风格 (原有) ============
        "realistic": "photorealistic, cinematic lighting, film grain, detailed textures, lifelike",
        "cartoon": "cartoon style, vibrant colors, clean lines, animated movie quality, expressive",
        "anime": "anime style, cel shading, expressive eyes, Japanese animation, dynamic poses",
        "watercolor": "watercolor painting, soft edges, dreamy atmosphere, artistic, flowing colors",
        "cyberpunk": "cyberpunk aesthetic, neon lights, dark atmosphere, futuristic, high-tech low-life",
        "ink": "Chinese ink wash painting, minimalist, brush strokes, traditional sumi-e",
        "pixel": "pixel art, retro game aesthetic, 16-bit style, crisp pixels",
        "oil_painting": "oil painting style, visible brushstrokes, classical art, rich textures",
        "illustration": "digital illustration, vibrant colors, detailed artwork, artstation trending, concept art, clean lines, rich details",
        "3d_render": "3D rendered, Pixar style, smooth surfaces, volumetric lighting, subsurface scattering",

        # ============ 艺术媒介/技法 ============
        "pencil_sketch": "pencil sketch, graphite drawing, hatching and cross-hatching, paper texture",
        "colored_pencil": "colored pencil drawing, layered strokes, textured coloring, soft blending",
        "charcoal": "charcoal drawing, dramatic contrast, expressive strokes, smudged edges",
        "marker": "marker illustration, bold lines, vibrant colors, copic marker style",
        "crayon": "crayon drawing, childlike aesthetic, waxy texture, bright colors",
        "pastel": "pastel artwork, soft colors, chalky texture, dreamy atmosphere",
        "acrylic": "acrylic painting, bold brushstrokes, vibrant colors, textured surface",
        "gouache": "gouache painting, flat colors, matte finish, illustrative style",
        "woodcut": "woodcut print, bold lines, high contrast, relief printing style",
        "linocut": "linocut print, carved texture, block printing, bold shapes",
        "collage": "paper collage, cut-out elements, layered textures, mixed media",
        "paper_cut": "paper cutting art, intricate silhouettes, layered paper, kirigami style",
        "stained_glass": "stained glass style, bold outlines, jewel-toned colors, luminous",

        # ============ 艺术流派 ============
        "impressionist": "impressionist style, loose brushstrokes, light and color play, Monet-inspired",
        "expressionist": "expressionist art, emotional intensity, distorted forms, bold colors",
        "surrealist": "surrealist art, dreamlike imagery, unexpected juxtapositions, Dali-inspired",
        "pop_art": "pop art style, bold colors, halftone dots, Andy Warhol inspired",
        "minimalist": "minimalist art, simple forms, limited color palette, clean composition",
        "art_deco": "art deco style, geometric patterns, elegant lines, 1920s aesthetic",
        "art_nouveau": "art nouveau style, organic flowing lines, decorative flourishes, nature-inspired",
        "baroque": "baroque style, dramatic lighting, rich details, ornate composition",
        "rococo": "rococo style, pastel colors, ornamental details, playful elegance",
        "renaissance": "renaissance style, classical proportions, sfumato technique, religious themes",

        # ============ 文化/地域风格 ============
        "ukiyo_e": "ukiyo-e style, Japanese woodblock print, flat colors, bold outlines, Hokusai-inspired",
        "dunhuang": "Dunhuang mural style, Chinese Buddhist art, rich colors, flowing lines",
        "chinese_ink": "Chinese ink painting, sumi-e, minimalist, brush strokes, bamboo paper texture",
        "chinese_gongbi": "Chinese gongbi painting, meticulous brushwork, fine details, silk texture",
        "persian_miniature": "Persian miniature painting, intricate details, gold accents, illuminated",
        "byzantine": "Byzantine mosaic style, gold background, iconic figures, religious art",
        "african_tribal": "African tribal art, geometric patterns, bold shapes, earthy colors",
        "mexican_mural": "Mexican muralism, bold colors, social themes, Diego Rivera inspired",
        "indian_miniature": "Indian miniature painting, intricate details, vibrant colors, Mughal style",
        "korean_traditional": "Korean traditional painting, delicate brushwork, natural subjects, hanji paper",
        "russian_lacquer": "Russian lacquer art, Palekh style, dark background, intricate folk tales",
        "thai_traditional": "Thai traditional art, gold leaf, ornate details, temple painting style",

        # ============ 时代/流行风格 ============
        "steampunk": "steampunk aesthetic, Victorian machinery, brass and copper, gears and steam",
        "dieselpunk": "dieselpunk style, 1940s industrial, Art Deco machinery, diesel-powered",
        "atompunk": "atompunk style, retro-futuristic, 1950s atomic age, space age optimism",
        "solarpunk": "solarpunk aesthetic, green technology, sustainable future, organic architecture",
        "gothic": "gothic style, dark atmosphere, ornate architecture, dramatic shadows",
        "victorian": "Victorian era style, ornate details, muted colors, period costumes",
        "80s_neon": "1980s neon aesthetic, bright colors, grid patterns, synthwave vibes",
        "90s_cartoon": "1990s cartoon style, bold outlines, flat colors, Saturday morning cartoon",
        "y2k": "Y2K aesthetic, chrome effects, cyber aesthetic, early 2000s digital",
        "vaporwave": "vaporwave aesthetic, pastel colors, glitch effects, retro tech",
        "synthwave": "synthwave style, neon grid, sunset gradients, retro-futuristic",
        "medieval": "medieval style, illuminated manuscript, heraldic imagery, tapestry-like",

        # ============ 现代数字/动画风格 ============
        "pixar_3d": "Pixar 3D animation style, smooth surfaces, expressive characters, cinematic lighting",
        "disney_classic": "Disney classic animation, hand-drawn, expressive characters, magical atmosphere",
        "dreamworks": "DreamWorks animation style, stylized characters, dynamic action, humor",
        "ghibli": "Studio Ghibli style, Miyazaki inspired, hand-drawn animation, soft colors, detailed backgrounds, whimsical atmosphere",
        "shinkai": "Makoto Shinkai style, photorealistic backgrounds, dramatic lighting, emotional atmosphere",
        "makoto_style": "Kyoto Animation style, detailed character designs, fluid animation, slice-of-life",
        "cel_shaded": "cel-shaded style, flat colors, bold outlines, video game aesthetic",
        "flat_design": "flat design, minimal shadows, bold colors, geometric shapes",
        "isometric": "isometric perspective, pixel perfect, geometric, diorama-like",
        "low_poly": "low poly 3D style, geometric faces, minimal polygons, stylized",
        "vector": "vector illustration, clean lines, scalable graphics, flat colors",
        "line_art": "line art style, black and white, clean outlines, detailed linework",
        "semi_realistic": "semi-realistic style, stylized realism, detailed yet artistic",

        # ============ 漫画类型 ============
        "manga": "manga style, Japanese comic, screentone, dynamic panels, expressive",
        "manhwa": "manhwa style, Korean webtoon, vertical scroll, vibrant colors",
        "manhua": "manhua style, Chinese comic, dynamic action, traditional influences",
        "american_comic": "American comic book style, bold inking, dynamic poses, speech bubbles",
        "marvel_style": "Marvel comics style, heroic poses, dramatic lighting, action-packed",
        "dc_style": "DC comics style, detailed artwork, iconic poses, dramatic shadows",
        "european_comic": "European comic style, ligne claire, detailed backgrounds, Tintin-inspired",
        "indie_comic": "indie comic style, unique art style, experimental, graphic novel aesthetic",

        # ============ 氛围/情绪风格 ============
        "dark_fantasy": "dark fantasy style, gothic atmosphere, moody lighting, mystical creatures",
        "dreamy_soft": "dreamy soft style, pastel colors, soft focus, ethereal atmosphere",
        "bright_cheerful": "bright cheerful style, vivid colors, happy atmosphere, energetic",
        "mysterious": "mysterious atmosphere, dramatic shadows, enigmatic, suspenseful",
        "epic_cinematic": "epic cinematic style, grand scale, dramatic composition, film-like",
        "cozy_healing": "cozy healing style, warm colors, comfortable atmosphere, soothing",
        "horror": "horror style, dark atmosphere, unsettling imagery, tense mood",
        "romantic": "romantic style, soft lighting, warm tones, intimate atmosphere",
        "nostalgic": "nostalgic style, vintage colors, retro feel, memory-like quality",

        # ============ 特定应用风格 ============
        "children_book": "children's book illustration, friendly characters, soft colors, whimsical",
        "picture_book": "picture book style, storytelling visuals, expressive characters, page-layout aware",
        "concept_art": "concept art, detailed design, production-quality, world-building",
        "game_art": "video game art, character design, environment art, stylized for games",
        "movie_storyboard": "movie storyboard style, sequential frames, cinematic composition, action notes",
        "fashion_illustration": "fashion illustration, elongated figures, stylish poses, trendy",
        "botanical": "botanical illustration, scientific accuracy, detailed flora, naturalist style",
        "architectural": "architectural rendering, precise lines, perspective drawing, blueprint-like",
    }

    # 风格分类映射
    STYLE_CATEGORIES = {
        # 基础风格
        "realistic": StyleCategory.MEDIUM,
        "cartoon": StyleCategory.DIGITAL_ANIMATION,
        "anime": StyleCategory.DIGITAL_ANIMATION,
        "watercolor": StyleCategory.MEDIUM,
        "cyberpunk": StyleCategory.ERA_TREND,
        "ink": StyleCategory.CULTURAL,
        "pixel": StyleCategory.DIGITAL_ANIMATION,
        "oil_painting": StyleCategory.MEDIUM,
        "illustration": StyleCategory.APPLICATION,
        "3d_render": StyleCategory.DIGITAL_ANIMATION,

        # 艺术媒介
        "pencil_sketch": StyleCategory.MEDIUM,
        "colored_pencil": StyleCategory.MEDIUM,
        "charcoal": StyleCategory.MEDIUM,
        "marker": StyleCategory.MEDIUM,
        "crayon": StyleCategory.MEDIUM,
        "pastel": StyleCategory.MEDIUM,
        "acrylic": StyleCategory.MEDIUM,
        "gouache": StyleCategory.MEDIUM,
        "woodcut": StyleCategory.MEDIUM,
        "linocut": StyleCategory.MEDIUM,
        "collage": StyleCategory.MEDIUM,
        "paper_cut": StyleCategory.MEDIUM,
        "stained_glass": StyleCategory.MEDIUM,

        # 艺术流派
        "impressionist": StyleCategory.ART_MOVEMENT,
        "expressionist": StyleCategory.ART_MOVEMENT,
        "surrealist": StyleCategory.ART_MOVEMENT,
        "pop_art": StyleCategory.ART_MOVEMENT,
        "minimalist": StyleCategory.ART_MOVEMENT,
        "art_deco": StyleCategory.ART_MOVEMENT,
        "art_nouveau": StyleCategory.ART_MOVEMENT,
        "baroque": StyleCategory.ART_MOVEMENT,
        "rococo": StyleCategory.ART_MOVEMENT,
        "renaissance": StyleCategory.ART_MOVEMENT,

        # 文化/地域
        "ukiyo_e": StyleCategory.CULTURAL,
        "dunhuang": StyleCategory.CULTURAL,
        "chinese_ink": StyleCategory.CULTURAL,
        "chinese_gongbi": StyleCategory.CULTURAL,
        "persian_miniature": StyleCategory.CULTURAL,
        "byzantine": StyleCategory.CULTURAL,
        "african_tribal": StyleCategory.CULTURAL,
        "mexican_mural": StyleCategory.CULTURAL,
        "indian_miniature": StyleCategory.CULTURAL,
        "korean_traditional": StyleCategory.CULTURAL,
        "russian_lacquer": StyleCategory.CULTURAL,
        "thai_traditional": StyleCategory.CULTURAL,

        # 时代/流行
        "steampunk": StyleCategory.ERA_TREND,
        "dieselpunk": StyleCategory.ERA_TREND,
        "atompunk": StyleCategory.ERA_TREND,
        "solarpunk": StyleCategory.ERA_TREND,
        "gothic": StyleCategory.ERA_TREND,
        "victorian": StyleCategory.ERA_TREND,
        "80s_neon": StyleCategory.ERA_TREND,
        "90s_cartoon": StyleCategory.ERA_TREND,
        "y2k": StyleCategory.ERA_TREND,
        "vaporwave": StyleCategory.ERA_TREND,
        "synthwave": StyleCategory.ERA_TREND,
        "medieval": StyleCategory.ERA_TREND,

        # 数字/动画
        "pixar_3d": StyleCategory.DIGITAL_ANIMATION,
        "disney_classic": StyleCategory.DIGITAL_ANIMATION,
        "dreamworks": StyleCategory.DIGITAL_ANIMATION,
        "ghibli": StyleCategory.DIGITAL_ANIMATION,
        "shinkai": StyleCategory.DIGITAL_ANIMATION,
        "makoto_style": StyleCategory.DIGITAL_ANIMATION,
        "cel_shaded": StyleCategory.DIGITAL_ANIMATION,
        "flat_design": StyleCategory.DIGITAL_ANIMATION,
        "isometric": StyleCategory.DIGITAL_ANIMATION,
        "low_poly": StyleCategory.DIGITAL_ANIMATION,
        "vector": StyleCategory.DIGITAL_ANIMATION,
        "line_art": StyleCategory.DIGITAL_ANIMATION,
        "semi_realistic": StyleCategory.DIGITAL_ANIMATION,

        # 漫画
        "manga": StyleCategory.COMIC,
        "manhwa": StyleCategory.COMIC,
        "manhua": StyleCategory.COMIC,
        "american_comic": StyleCategory.COMIC,
        "marvel_style": StyleCategory.COMIC,
        "dc_style": StyleCategory.COMIC,
        "european_comic": StyleCategory.COMIC,
        "indie_comic": StyleCategory.COMIC,

        # 氛围
        "dark_fantasy": StyleCategory.MOOD,
        "dreamy_soft": StyleCategory.MOOD,
        "bright_cheerful": StyleCategory.MOOD,
        "mysterious": StyleCategory.MOOD,
        "epic_cinematic": StyleCategory.MOOD,
        "cozy_healing": StyleCategory.MOOD,
        "horror": StyleCategory.MOOD,
        "romantic": StyleCategory.MOOD,
        "nostalgic": StyleCategory.MOOD,

        # 应用
        "children_book": StyleCategory.APPLICATION,
        "picture_book": StyleCategory.APPLICATION,
        "concept_art": StyleCategory.APPLICATION,
        "game_art": StyleCategory.APPLICATION,
        "movie_storyboard": StyleCategory.APPLICATION,
        "fashion_illustration": StyleCategory.APPLICATION,
        "botanical": StyleCategory.APPLICATION,
        "architectural": StyleCategory.APPLICATION,
    }

    COLOR_MODIFIERS = {
        "warm": "warm color temperature, golden tones, amber highlights",
        "cold": "cool color temperature, blue tones, silver highlights",
        "neutral": "balanced color temperature, natural tones",
        "vibrant": "highly saturated colors, vivid and bold",
        "muted": "desaturated colors, soft and subdued palette",
        "rich": "rich saturated colors, deep tones",
        "pastel": "pastel colors, soft and light tones",
        "monochrome": "monochromatic, single color family, various shades",
        "earth": "earth tones, natural browns and greens",
        "jewel": "jewel tones, rich and saturated, gem-like colors",
        "neon": "neon colors, bright and glowing, fluorescent",
        "sepia": "sepia tones, warm brown vintage look",
    }

    LIGHTING_MODIFIERS = {
        "natural": "natural lighting, realistic shadows",
        "dramatic": "dramatic lighting, strong contrast, deep shadows",
        "soft": "soft diffused lighting, gentle shadows",
        "neon": "neon lighting, glowing effects, colorful light sources",
        "cinematic": "cinematic lighting, volumetric rays, film-like atmosphere",
        "ethereal": "ethereal soft glow, magical lighting",
        "golden_hour": "golden hour lighting, warm sunlight, long shadows",
        "moonlight": "moonlight illumination, cool blue tones, night atmosphere",
        "studio": "studio lighting, controlled shadows, professional setup",
        "backlit": "backlit, rim lighting, silhouette effect",
        "ambient": "ambient occlusion, soft shadows, diffused light",
        "harsh": "harsh lighting, strong shadows, high contrast",
    }

    RENDERING_MODIFIERS = {
        "soft": "soft rendering, smooth transitions",
        "sharp": "sharp details, crisp edges",
        "painterly": "painterly strokes, artistic rendering",
        "smooth": "smooth gradients, polished finish",
        "textured": "textured surface, visible brush/tool marks",
        "glossy": "glossy finish, reflective surfaces",
        "matte": "matte finish, non-reflective",
    }

    def build_style_suffix(self, config: ProjectStyleConfig) -> str:
        """构建风格后缀（每张图都会附加）"""
        parts = []

        # 基础风格
        base_style = self.STYLE_TEMPLATES.get(config.style_preset, config.style_preset)
        parts.append(base_style)

        # 渲染风格
        if config.rendering:
            rendering_mod = self.RENDERING_MODIFIERS.get(config.rendering, config.rendering)
            parts.append(rendering_mod)

        # 色调
        color_mod = self.COLOR_MODIFIERS.get(config.color_palette, "")
        if color_mod:
            parts.append(color_mod)

        # 主色调
        if config.dominant_colors:
            parts.append(f"featuring {', '.join(config.dominant_colors)} tones")

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
        parts.append("consistent style throughout, professional quality, high quality")

        return ", ".join(parts)

    def build_from_story(self, story_data: Dict[str, Any]) -> ProjectStyleConfig:
        """从story.json数据构建ProjectStyleConfig"""
        visual_style = story_data.get('visual_style', {})

        # 映射art_style到style_preset
        art_style = visual_style.get('art_style', 'illustration')
        style_preset = self._map_art_style(art_style)

        # 获取色调
        color_palette = visual_style.get('color_palette', 'warm')
        if color_palette not in self.COLOR_MODIFIERS:
            color_palette = self._infer_color_palette(color_palette)

        # 获取光影
        lighting = visual_style.get('lighting', 'natural')
        lighting_style = self._infer_lighting_style(lighting)

        # 获取渲染风格
        rendering = visual_style.get('rendering', 'soft')

        # 获取细节级别
        detail_level = visual_style.get('detail_level', 'detailed')
        if detail_level == 'high':
            detail_level = 'detailed'

        # 主色调
        primary_colors = visual_style.get('primary_colors', [])

        config = ProjectStyleConfig(
            style_preset=style_preset,
            color_palette=color_palette,
            dominant_colors=primary_colors,
            lighting_style=lighting_style,
            rendering=rendering,
            detail_level=detail_level,
            raw_visual_style=visual_style,
        )

        # 构建风格后缀
        config.style_suffix = self.build_style_suffix(config)

        return config

    def _map_art_style(self, art_style: str) -> str:
        """映射art_style到预设"""
        art_style_lower = art_style.lower().replace(' ', '_').replace('-', '_')

        # 直接匹配
        if art_style_lower in self.STYLE_TEMPLATES:
            return art_style_lower

        # 映射表
        mappings = {
            'digital_illustration': 'illustration',
            'photorealistic': 'realistic',
            '3d': '3d_render',
            'pixar': 'pixar_3d',
            'disney': 'disney_classic',
            'studio_ghibli': 'ghibli',
            'makoto_shinkai': 'shinkai',
            'kyoto_animation': 'makoto_style',
            'japanese_anime': 'anime',
            'korean_webtoon': 'manhwa',
            'chinese_comic': 'manhua',
            'western_comic': 'american_comic',
            'comic_book': 'american_comic',
            'watercolour': 'watercolor',
            'oil': 'oil_painting',
            'pencil': 'pencil_sketch',
            'sketch': 'pencil_sketch',
            'children': 'children_book',
            'kidlit': 'children_book',
            'childrens_illustration': 'children_book',
        }

        for key, value in mappings.items():
            if key in art_style_lower:
                return value

        return art_style_lower if art_style_lower in self.STYLE_TEMPLATES else 'illustration'

    def _infer_color_palette(self, color_desc: str) -> str:
        """从描述推断色调"""
        color_lower = color_desc.lower()
        keywords = {
            'warm': ['warm', 'golden', 'amber', 'orange', 'sunset'],
            'cold': ['cold', 'cool', 'blue', 'silver', 'ice'],
            'vibrant': ['vibrant', 'vivid', 'saturated', 'bright', 'bold'],
            'muted': ['muted', 'subdued', 'soft', 'gentle', 'pale'],
            'rich': ['rich', 'deep', 'dark'],
            'pastel': ['pastel', 'light', 'candy'],
            'neon': ['neon', 'fluorescent', 'glowing'],
            'earth': ['earth', 'natural', 'organic', 'brown', 'green'],
            'monochrome': ['monochrome', 'grayscale', 'black_and_white'],
        }

        for palette, words in keywords.items():
            if any(w in color_lower for w in words):
                return palette

        return 'neutral'

    def _infer_lighting_style(self, lighting_desc: str) -> str:
        """从描述推断光影风格"""
        lighting_lower = lighting_desc.lower()
        keywords = {
            'dramatic': ['dramatic', 'chiaroscuro', 'contrast'],
            'soft': ['soft', 'diffused', 'gentle'],
            'neon': ['neon', 'glowing', 'fluorescent'],
            'cinematic': ['cinematic', 'film', 'movie'],
            'ethereal': ['ethereal', 'magical', 'mystical'],
            'golden_hour': ['golden', 'sunset', 'sunrise', 'warm light'],
            'moonlight': ['moon', 'night', 'lunar'],
            'backlit': ['backlit', 'rim', 'silhouette'],
        }

        for style, words in keywords.items():
            if any(w in lighting_lower for w in words):
                return style

        return 'natural'

    def get_style_category(self, style_name: str) -> Optional[StyleCategory]:
        """获取风格的类别"""
        return self.STYLE_CATEGORIES.get(style_name)

    def get_styles_by_category(self, category: StyleCategory) -> List[str]:
        """获取某类别下的所有风格"""
        return [
            style for style, cat in self.STYLE_CATEGORIES.items()
            if cat == category
        ]

    def get_all_styles(self) -> List[str]:
        """获取所有可用风格名称"""
        return list(self.STYLE_TEMPLATES.keys())

    def get_style_count(self) -> int:
        """获取风格总数"""
        return len(self.STYLE_TEMPLATES)


# ================================================================
# 便捷函数
# ================================================================

def get_style_template(style_name: str) -> str:
    """获取风格模板"""
    builder = StyleConfigBuilder()
    return builder.STYLE_TEMPLATES.get(style_name, style_name)


def get_all_style_names() -> List[str]:
    """获取所有风格名称"""
    builder = StyleConfigBuilder()
    return builder.get_all_styles()


def get_styles_by_category(category: str) -> List[str]:
    """按类别获取风格"""
    builder = StyleConfigBuilder()
    try:
        cat = StyleCategory(category)
        return builder.get_styles_by_category(cat)
    except ValueError:
        return []
