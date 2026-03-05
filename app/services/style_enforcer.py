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
            style_description="You are photographing in the tradition of master cinematographers and documentary photographers — every frame a real moment captured with an unblinking lens. Light falls as it does in life: warm afternoon sun streaming through curtains, cool fluorescent wash in office corridors, the golden edge of dawn tracing a jawline into shadow. Colors remain true and grounded — warm skin tones set against cool urban concrete, the muted organic palette of real weather and real rooms, never oversaturated or artificially vivid. Every surface holds photographic truth: pores and fine lines on living skin, the crease of worn leather, condensation on cold glass, dust motes drifting through a shaft of afternoon light. Characters exist as real people caught in unposed moments — the weight of a tired hand on a table, the unconscious angle of a turned shoulder, eyes that carry genuine thought. Each composition uses the photographer's disciplined eye: depth of field isolating subjects from background, leading lines drawing attention to the emotional center, the decisive moment where gesture and setting align.",
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
            style_description="You are animating in the tradition of classic cartoon storytelling — where every frame pops with personality and every expression lands without subtlety. Light serves clarity above all: bold flat shadows define form, bright fills keep the mood buoyant, and dramatic backlighting appears only when the comedy or drama demands a spotlight moment. Colors sing at full volume — primaries punch with energy, pastels soften tender scenes, and every palette choice reads instantly from across the room. Surfaces stay clean and graphic: smooth skin, crisp fabric shapes, environments built from confident color blocks rather than fussy texture. Characters perform with their whole bodies — rubbery limbs stretching into gesture, eyebrows arching into orbit, mouths pulling wide enough to swallow the joke. Each composition stages action for instant readability: clear silhouettes against contrasting backgrounds, generous negative space around key expressions, and dynamic angles that make still frames feel like they are mid-motion.",
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
            style_description="You are sculpting in the tradition of Pixar's master animators — artists who proved that digital characters can carry the full weight of human emotion. Light behaves cinematically: volumetric rays filter through dusty attics, subsurface scattering warms cheeks with life, rim lights separate characters from lush environments in moments of revelation. Colors are emotionally engineered — warm ambers wrap moments of connection, cool desaturated tones signal loss, and every palette shift follows the heart of the story. Surfaces achieve that signature tangibility: smooth plastic-like skin with just enough imperfection, fabric that drapes with real physics, environments rich with small props that whisper backstory. Characters perform through the subtlest channels — the slight widening of eyes, the barely suppressed quiver of a lip, the weight shift that betrays hesitation before a brave step. Each composition borrows from live-action cinematography: rack focus to shift emotional attention, low angles that make small characters feel brave, wide establishing shots that make vast worlds feel intimate.",
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
            style_description="You are animating in the tradition of Japan's finest studios — where hand-drawn precision meets cinematic ambition and every frame could be a poster. Light is theatrical and unapologetic: harsh cel-shaded shadows cut across faces in moments of resolve, golden sunset backlighting halos a character's silhouette, lens flares burst through tree canopies as emotions peak. Colors shift with narrative temperature — saturated and vivid in moments of passion and confrontation, washed pale in bittersweet memories, deep midnight blues for quiet introspection. Linework is the skeleton of everything: clean and confident outer strokes define form, while detail concentrates where emotion lives — in the luminous depth of large expressive eyes, in the liquid flow of hair catching wind. Characters perform through anime's unique visual grammar — eyes that carry entire soliloquies, hair that responds to emotional energy, the held pause before an explosive reaction. Each composition embraces dynamic camera language: dramatic low angles for determination, tight close-ups where eyes fill the frame, sweeping wide shots where characters stand small against vast skies and city lights.",
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
            style_description="You are painting in the tradition of Studio Ghibli and Hayao Miyazaki — where hand-drawn warmth transforms every scene into a place you wish you could visit. Light arrives softly and naturally: dappled sunlight filtering through forest canopies, the gentle amber of lantern-lit evenings, clouds that glow with the quiet gold of late afternoon. Colors are drawn from the living earth — sage greens of wild meadows, warm ochres of wooden interiors, the infinite graduating blues of Miyazaki's signature skies. Every background is painted with loving attention to organic detail: wind-rippled grass, weathered stone walls with moss creeping through cracks, laundry swaying on a clothesline in a breeze you can almost feel. Characters express themselves with disarming simplicity — round gentle faces where a single tear or a small determined frown carries more weight than any dramatic gesture. Each composition breathes with space and patience: wide shots where characters exist as small figures within vast living landscapes, intimate framings that find magic in the mundane — a meal being prepared, rain drumming on a window, the moment of stillness before adventure begins.",
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
            style_description="You are creating in the tradition of the finest digital illustrators — artists who treat every frame as a painting that tells a story. Light pours through windows and catches in hair, pooling in warm gradients that guide the eye to what matters most. Colors breathe with intention: warm ambers for intimacy, cool blues for solitude, saturated accents that anchor emotion. Every surface carries just enough texture to feel alive — the weave of fabric, the sheen of rain-wet pavement, the soft glow of a phone screen in twilight. Characters inhabit their world through posture, micro-expression, and the charged space between them. Each composition balances clarity with depth, placing the viewer exactly where the feeling lives.",
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
            style_description="You are painting in the tradition of watercolor masters — artists who know that the most beautiful mark is the one shared between pigment and water's own will. Light exists not by adding brightness but by protecting the white of the paper — untouched space glows with a luminosity no pigment can match, creating halos around figures and windows that seem to radiate warmth. Colors bloom and mingle on wet surfaces: warm siennas bleed into cool ceruleans at the horizon, rose washes drift into violet shadows, each edge soft and alive with the memory of water's movement. Texture is the medium itself — the tooth of cold-pressed paper catching pigment in its valleys, pools of color drying darker at their edges, granulation where heavy pigments settle into gentle constellations. Characters emerge from washes rather than sharp lines — a turned head suggested by a shadow's edge, emotion carried in the warmth or coolness of flesh tones, figures that breathe because their boundaries are never fully closed. Each composition embraces the watercolorist's wisdom: leave more unsaid than said, let white space carry as much story as painted areas, and trust the viewer to complete what the water began.",
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
            style_description="You are illustrating in the tradition of beloved picture book artists — creators who know that a child's first encounter with art should feel like a warm hug made visible. Light wraps everything in safety: soft and even, with no frightening shadows, just gentle warmth that makes indoor scenes feel cozy and outdoor scenes feel like endless summer afternoons. Colors speak the language of comfort — honeyed yellows, powder blues, rosy pinks, leaf greens — all slightly softened as if seen through the haze of a happy memory. Textures feel handmade and touchable: the chalky grain of crayon, the soft press of colored pencil, backgrounds that feel like painted paper you could reach into and crinkle. Characters are drawn to be instantly loved — round faces with oversized curious eyes, small hands that gesture with wonder, proportions that make even grown-ups look approachable and kind. Each composition keeps the story crystal clear: one main action per frame, uncluttered backgrounds that never compete with characters, and generous space that lets young eyes find the story without getting lost.",
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
            style_description="You are drawing in the tradition of manga masters — storytellers who compress entire emotional arcs into single frames and make still images feel like they are in motion. Light is rendered through the language of ink: crisp shadows define drama, screentone gradients build atmospheric depth from delicate to oppressive, and strategic white space creates moments of blinding revelation or serene calm. Contrast is the primary emotional instrument — deep blacks anchor moments of intensity, while open linework lightens scenes of tenderness or comedy. Every line earns its place: bold confident strokes for action and silhouette, fine detailed hatching for texture and mood, speed lines that make the eye race across the frame. Characters express through manga's full emotional spectrum — from subtle downcast eyes in a quiet panel to explosive reaction faces that shatter the frame's boundaries, each expression calibrated to the story's current heartbeat. Each composition thinks in sequential rhythm: establishing shots that set the stage wide, rapid close-ups that punch emotional beats, dramatic dutch angles for crisis moments, and the deliberate held silence of a full-frame face that lets a single expression speak volumes.",
            quality_keywords=["professional manga", "detailed linework", "high quality manga art"]
        ),

        # ============ 灌篮高手/井上雄彦风格 ============
        "slam_dunk": StyleEnforcement(
            style_name="slam_dunk",
            style_display_name="Slam Dunk Manga (Takehiko Inoue)",
            mandatory_keywords=[
                "slam dunk manga style", "Takehiko Inoue inspired",
                "realistic manga proportions", "dynamic linework",
                "detailed anatomy", "dramatic lighting and shadow",
                "Japanese manga aesthetic", "expressive character art",
                "screentone effects", "bold ink strokes",
                "full color manga", "colored manga illustration"
            ],
            forbidden_keywords=[
                "chibi", "cute", "super deformed", "pastel colors",
                "photorealistic photograph", "3D render", "CGI",
                "Western comic style", "simple cartoon", "flat colors",
                "pixel art", "watercolor", "oil painting",
                "black and white", "grayscale", "monochrome"
            ],
            style_description="You are drawing in the tradition of Takehiko Inoue, where basketball manga becomes cinema. Light is the silent storyteller: gymnasium fluorescents carving sharp shadows, golden hour warming courts in amber. Rich, saturated color grounds every panel in vivid reality. Bold ink strokes for power, fine hatching for shadow, screentone gradients building atmosphere like a film score. Every body carries real athletic weight — muscles defined under fabric, postures shaped by exhaustion and resolve, faces holding the full depth of human emotion. Each composition finds the cinematic angle that makes the viewer feel the impact — a dunk's slam, a free throw's silence, the weight of unspoken rivalry.",
            quality_keywords=["professional manga art", "detailed linework", "cinematic manga composition", "masterful ink work", "dynamic action poses"]
        ),

        # ============ 韩漫风格 ============
        "korean_webtoon": StyleEnforcement(
            style_name="korean_webtoon",
            style_display_name="Korean Webtoon Style",
            mandatory_keywords=[
                "Korean webtoon style", "manhwa aesthetic", "clean digital linework",
                "soft color palette", "romantic manga", "detailed facial expressions",
                "modern urban setting", "webtoon format"
            ],
            forbidden_keywords=[
                "photorealistic photograph", "3D render", "pixel art",
                "chibi", "Western comic", "rough sketch",
                "dark gritty", "horror"
            ],
            style_description="You are drawing in the tradition of Korean webtoon artists — digital storytellers who elevated the manhwa form into an art of beautiful faces and electric emotional tension. Light glows with a soft digital warmth: gentle gradients wrap around cheekbones, backlit hair shimmers with an almost ethereal halo, and indoor scenes carry the intimate warmth of carefully placed ambient light. Colors are refined and intentional — soft blush tones for romantic scenes, cool lavenders for melancholy, with selective vivid accents on eyes and lips that draw focus like a spotlight on a stage. Every surface is polished and precise: clean digital linework that never wavers, smooth color fills with subtle gradient shading, character designs so carefully rendered that each eyelash and strand of hair feels individually placed. Characters live through their faces — large expressive eyes that shimmer with unshed tears or narrow with determination, the charged centimeters of space between two people who have not yet touched, micro-expressions that carry entire unspoken conversations. Each composition gravitates toward emotional intimacy: close framings that make the viewer feel like a confidant, dramatic angles that heighten confrontation, and the strategic use of negative space that makes characters feel beautifully alone in their feelings.",
            quality_keywords=["professional webtoon", "polished digital art", "beautiful character design", "clean coloring"]
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
            style_description="You are painting in the tradition of the Old Masters — artists who understood that oil on canvas holds light like no other medium, layering luminosity into every shadow and warmth into every face. Light is sculpted with a painter's patience: golden glow emerging from darkness to caress a cheek, cool daylight pouring through a single window, chiaroscuro carving three-dimensional presence from flat canvas. Colors are mixed with the richness that only oil allows — warm umbers layered beneath cool surface tones, flesh that glows because translucent glazes build up its life, shadows that are never black but alive with deep violets and burnt siennas. Every surface declares its material truth through the brush: thick impasto catching real light on a sunlit sleeve, soft blended passages where skin turns from light into shadow, the visible weave of canvas asserting itself beneath thin washes. Characters carry the psychological weight of portraiture — eyes that follow the viewer with thought behind them, hands positioned with meaning, postures that reveal inner state as clearly as any expression. Each composition follows classical architecture: the golden section guiding the eye, atmospheric perspective building depth, and the careful orchestration of light and dark masses that makes a painting feel like a world with its own gravity.",
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
            style_description="You are building worlds in the tradition of cyberpunk visionaries — Syd Mead's chrome futures, Ridley Scott's rain-soaked neon nightscapes, and Ghost in the Shell's meditative urban decay. Light is artificial and omnipresent: neon signs bleed pink and cyan through perpetual rain, holographic advertisements cast shifting color onto wet faces, and the only natural light is the sickly glow of a sky choked by smog and industry. Colors exist in electric opposition — hot neon magentas and teals burn against deep shadow, chrome surfaces scatter fractured reflections, and the rare warm light of an analog lamp becomes a beacon of humanity in a digital wasteland. Every surface tells a story of layered time: rain-slicked asphalt reflecting a thousand neon signs, corroded metal alongside sleek corporate glass, cables and pipes snaking through architecture like exposed veins. Characters carry the weight of living between worlds — augmented eyes reflecting data streams, leather and synthetic fabric layered for function over fashion, postures that balance street-level weariness with coiled readiness. Each composition builds depth through urban density: towering vertical cityscapes that dwarf their inhabitants, Dutch angles that keep the viewer off-balance, and rain — always rain — turning every surface into a mirror of fractured light.",
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
            style_description="You are painting in the tradition of Chinese ink wash masters — scholars who believed that a single brush stroke, guided by decades of discipline, could capture the essence of a mountain or the spirit of a person. Light does not fall from any source — it exists in the paper itself, the untouched white silk or rice paper radiating a luminosity that ink approaches but never conquers, creating depth through the dialogue between presence and absence. Color is the ink's own vocabulary: dense black for bold certainty, diluted gray washes drifting like morning mist across valleys, and the rare touch of mineral pigment — a vermillion seal, an ochre autumn leaf — that burns with intensity precisely because the rest is restrained. Texture lives in the brush's memory: a single stroke can begin thick and wet with confident authority, thin to a trembling hair-fine line, and end in a dry brush scratch that makes paper grain visible like wind across water. Figures are suggested rather than defined — a scholar's posture captured in three confident strokes, emotion conveyed through the angle of a bowed head or the energy of a turned sleeve, humanity distilled to its essential gestures. Each composition embraces emptiness as its most powerful element: vast unpainted space that becomes sky, water, silence, and meaning — asymmetric balance where a single figure at the edge of nothing carries more weight than a crowded scene ever could.",
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
            style_description="You are crafting in the tradition of pixel art masters — artists who turned severe technical constraints into an aesthetic that feels more deliberate and honest than any high-resolution render. Light is constructed pixel by pixel: dithering patterns simulate gradients with mathematical precision, limited palettes force every shadow to be a conscious color choice, and highlights land on exactly the right pixel to make forms read clearly at any scale. Colors are curated with the discipline of a limited palette — each hue earned its place, warm tones cluster for life and energy, cool tones for calm and mystery, and the careful juxtaposition of two or three colors creates the illusion of dozens. Every surface honors the grid: crisp aliased edges define clean silhouettes, clusters of pixels suggest texture — brick, wood, fabric, metal — through pattern rather than detail, and each tile of environment is placed with the intentionality of mosaic. Characters are designed for instant recognition — distinctive silhouettes readable at thumbnail size, emotions conveyed through the tilt of a few-pixel head and the position of dot eyes, each pose a carefully chosen frame that implies motion. Each composition respects the pixel grid's geometry: clean horizontal staging, thoughtful use of the limited canvas, and the retro warmth of an era when every single pixel was placed by a human hand with purpose.",
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
