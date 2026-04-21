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

    # ================================================================
    # 音乐方向提示 (music_hint) — Pipeline 集成 Wave 1 Step B
    # 给 Haiku 在生成 BGM prompt 时提供视觉风格 → 音乐方向的锚点
    # 原则: 从身体感觉/空间氛围描述，不列乐器清单，英文
    # ================================================================
    MUSIC_HINTS: Dict[str, str] = {
        # ============ 基础风格 ============
        "realistic": "contemporary naturalistic, sparse and grounded, acoustic-piano palette, no synthetic sheen",
        "cartoon": "bright orchestral, playful mid-tempo, warm and bouncy, light percussion with melodic energy",
        "anime": "J-pop adjacent cinematic, piano and strings leading, clean production, emotional directness and youthful energy",
        "watercolor": "impressionist gentle, soft-edged textures, dreamy piano and light strings, unhurried and quietly luminous",
        "cyberpunk": "electronic nocturne, analog synth pulse with neon underlayer, metropolitan cold, rain-soaked and machine-breathing",
        "ink": "East Asian minimalist, guqin or dizi or xiao color, negative space breathes between notes, ink-brush pacing",
        "pixel": "chiptune adjacent or simple pentatonic, clean retro character, nostalgia without irony, constrained palette of sound",
        "oil_painting": "classical chamber gravity, strings and harpsichord or piano, Old World weight and emotional gravitas",
        "illustration": "polished contemporary, piano-led with lush production, emotionally articulate without genre constraint",
        "3d_render": "cinematic orchestral warmth, full strings with adventure lift, emotional and sweeping but never dark",

        # ============ 艺术媒介/技法 ============
        "pencil_sketch": "intimate acoustic, bare and unhurried, pencil-on-paper quietness, space between notes as loaded as the notes themselves",
        "colored_pencil": "warm and handcrafted, gentle folk textures, soft and personal, handmade emotional warmth",
        "charcoal": "brooding and expressive, raw emotional weight, dark tones with stark contrast, gestural and unresolved",
        "marker": "bold and graphic, energetic pop-commercial, vivid and punchy, fun without subtlety",
        "crayon": "childlike wonder and play, simple bright melodies, innocent and crayon-box colorful",
        "pastel": "soft chalky calm, gentle and tender, pastel warmth without saccharine, quiet living-room intimacy",
        "acrylic": "bold and textured, energetic and confident, painterly strokes made audible",
        "gouache": "flat and precise, elegant simplicity, matte warmth, illustrated and deliberate",
        "woodcut": "stark and primal, folk or ancient resonance, wood-grain texture in sound, bold and carved",
        "linocut": "graphic and forceful, block-print directness, earthy and hand-pressed",
        "collage": "layered and eclectic, mixed textures, found-sound warmth, unexpected juxtapositions",
        "paper_cut": "Chinese folk festivity, erhu and pipa warmth, jianzhi red-paper brightness, celebration and community spirit",
        "stained_glass": "cathedral light and resonance, warm devotional glow, jewel-toned and luminous",

        # ============ 艺术流派 ============
        "impressionist": "Impressionist shimmering, dappled light in sound, flowing and spontaneous, color-as-feeling",
        "expressionist": "raw and distorted, emotional urgency, dissonance as truth, the body before the mind",
        "surrealist": "dreamlogic and uncanny, unexpected collisions of texture, the subconscious given sonic shape",
        "pop_art": "bold pop energy, repetitive hook-driven, bright and irreverent, commercial punch with artistic attitude",
        "minimalist": "spare and essential, slow unfolding, each sound chosen with austere intention, silence as presence",
        "art_deco": "jazz age glamour, geometric elegance, 1920s cocktail-hour sophistication",
        "art_nouveau": "fin-de-siècle lush and flowing, orchestral with organic sweep, belle époque grace, nature and beauty intertwined",
        "baroque": "Baroque ornamentation and drama, counterpoint layering, grandeur and spiritual intensity",
        "rococo": "light and playful ornament, French pastoral elegance, powder-and-lace delicacy",
        "renaissance": "classical polyphony, sacred and humanist, measured and luminous, the dignity of craft",

        # ============ 文化/地域风格 ============
        "ukiyo_e": "Japanese classical serenity, shamisen or koto color, Edo period floating world, decorative elegance and unhurried grace",
        "dunhuang": "ancient Silk Road resonance, Central Asian modal color, devotional reverence and cavernous depth",
        "chinese_ink": "East Asian minimalist, guqin or xiao color, ink-brush pacing, empty space as sound",
        "chinese_gongbi": "refined Chinese court music, delicate pipa or zheng, meticulous and ornate, silk-texture precision",
        "persian_miniature": "Persian classical modal warmth, oud and string resonance, illuminated manuscript intricacy",
        "byzantine": "Orthodox chant resonance, golden icon solemnity, sacred and gilded, eternal and austere",
        "african_tribal": "percussive communal energy, earth-rooted rhythm, call-and-response vitality, organic and ancestral",
        "mexican_mural": "Mexican folk and revolutionary spirit, mariachi color beneath social weight, bold and communal",
        "indian_miniature": "Indian classical modal warmth, sitar or sarod raga color, Mughal court ornament and devotion",
        "korean_traditional": "Korean hanji-paper quietness, gayageum or haegeum, natural subject reverence, gentle and precise",
        "russian_lacquer": "Russian folk tale warmth, balalaika or bayan color, Palekh dark-and-gold mystery",
        "thai_traditional": "Thai classical court splendor, ranat or khim color, temple painting devotion and golden warmth",

        # ============ 时代/流行风格 ============
        "steampunk": "Victorian mechanical grandeur, brass ensemble with clockwork rhythm, industrial elegance and adventurous invention",
        "dieselpunk": "1940s industrial drive, big band edge with diesel-engine grit, Art Deco momentum",
        "atompunk": "1950s atomic optimism, space-age lounge orchestral, Sputnik-era wonder and naive futurism",
        "solarpunk": "green acoustic warmth, organic and hopeful, sustainable folk energy, living architecture breathing",
        "gothic": "dark romantic cathedral resonance, organ or choir undertow, beauty found in shadow, ornate melancholy and sacred dread",
        "victorian": "Victorian parlor elegance, chamber strings and piano, period formality with repressed longing",
        "80s_neon": "1980s synth-pop drive, neon grid pulsing, analog warmth meets digital sheen, nostalgic electric",
        "90s_cartoon": "Saturday morning energy, upbeat and simple, 90s cartoon bounce and bold hooks",
        "y2k": "early 2000s digital gloss, Y2K pop shimmer, chrome-plated bubblegum electronic",
        "vaporwave": "slowed and dreamlike, mall-music memory distorted, melancholy nostalgia bathed in pastel digital haze",
        "synthwave": "retrowave pulse, neon highway at night, analog synth warmth with retro-futurist drive",
        "medieval": "medieval modal resonance, lute or recorder color, tapestry-pattern repetition, ancient and sacred",

        # ============ 现代数字/动画风格 ============
        "pixar_3d": "cinematic orchestral warmth, full strings with adventure lift, emotional and sweeping but never dark",
        "disney_classic": "magical fairy-tale orchestral, classic animation wonder, sweeping and singable, timeless warmth",
        "dreamworks": "action-comedy orchestral, wit and spectacle, DreamWorks swagger and kinetic energy",
        "ghibli": "pastoral romantic, acoustic strings and light winds, nostalgic warmth with childlike wonder and open-sky breathing room",
        "shinkai": "bittersweet cinematic, piano and strings aching with distance, Shinkai longing for what cannot be held",
        "makoto_style": "slice-of-life warmth, gentle and everyday, Kyoto Animation quiet emotional depth",
        "cel_shaded": "stylized game-world energy, cel-shaded cartoon bounce, video game adventure palette",
        "flat_design": "clean and geometric, minimal and precise, design-thinking aesthetic without sentimentality",
        "isometric": "puzzle-like and contemplative, architectural curiosity, geometric and calm with playful undertone",
        "low_poly": "geometric and spare, digital minimalism with warmth, angular but human",
        "vector": "clean graphic precision, bold and scalable, design-forward and unambiguous",
        "line_art": "bare linework quietness, monochrome intimacy, clean and open, outline and silence",
        "semi_realistic": "grounded yet stylized, contemporary with emotional color, the real world seen through an artist's eye",

        # ============ 漫画类型 ============
        "manga": "Japanese cinematic with dramatic peaks and quiet valleys, tension-release arc, emotionally charged pacing",
        "manhwa": "K-drama romantic ambient, clean production with emotional restraint, the ache of almost-said feelings",
        "manhua": "Chinese martial arts cinematic energy, traditional instrument color beneath modern drama",
        "american_comic": "heroic action orchestral, bold punchy themes, larger-than-life energy, kinetic momentum",
        "marvel_style": "Marvel superhero cinematic, wall-of-sound orchestral, heroic and spectacular, world-saving weight",
        "dc_style": "DC dark and operatic, dramatic and weighty, iconic and mythic in scale",
        "european_comic": "European ligne-claire elegance, refined adventure, Tintin-era discovery and wit",
        "indie_comic": "intimate and experimental, voice-driven and personal, genre-bending sonic identity",

        # ============ 氛围/情绪风格 ============
        "dark_fantasy": "epic dark orchestral, weight of ancient stone and mythic power, low brass and deep resonance, shadows that breathe",
        "dreamy_soft": "ethereal soft drift, luminous and weightless, pastel-warm and gently floating",
        "bright_cheerful": "sunny upbeat energy, major key warmth, joyful bounce, the world at its most generous",
        "mysterious": "shadowed and questioning, tension held in suspension, the sound of a door not yet opened",
        "epic_cinematic": "grand cinematic scale, sweeping orchestral, the weight of consequence and the size of sky",
        "cozy_healing": "warm and unhurried, the sound of a heated room in winter, soft and restorative, no edges",
        "horror": "dread and unease, tension without resolution, sounds that shouldn't exist in daylight",
        "romantic": "intimate and longing, the space between two people, warm and soft with aching sweetness",
        "nostalgic": "faded warmth, vintage grain, the ache of what was, memory given sonic texture",

        # ============ 特定应用风格 ============
        "children_book": "tender folk-lullaby warmth, gentle and unhurried, innocence without sentimentality, safe and loving sonic space",
        "picture_book": "storybook gentle, narrative warmth, each page-turn a breath, simple and inviting",
        "concept_art": "world-building atmospheric, production-quality soundscape, the hum of an imagined world",
        "game_art": "game-world adventurous, stylized and interactive, genre-appropriate energy and pacing",
        "movie_storyboard": "cinematic pre-viz, dramatic and scene-setting, the sound of a story about to happen",
        "fashion_illustration": "editorial chic, cool and stylized, runway tension and effortless attitude",
        "botanical": "naturalist stillness, the sound of careful observation, delicate and precise, nature's own patience",
        "architectural": "spatial and structural, the resonance of designed space, form and proportion given sound",

        # ============ fallback ============
        "custom": "acoustic versatile palette, match visual mood, emotionally responsive and style-agnostic",
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

    def get_music_hint(self, style_name: str) -> str:
        """
        获取风格对应的音乐方向提示（music_hint）
        给 Haiku 在生成 BGM prompt 时提供视觉风格 → 音乐方向的锚点。
        优先从 StyleEnforcer 读取（有完整 StyleEnforcement 的 28 个风格），
        再查 MUSIC_HINTS dict，最后 fallback 到通用提示。
        """
        # 先尝试从 StyleEnforcer 获取（有完整定义的风格）
        try:
            from app.services.style_enforcer import StyleEnforcer
            enforcement = StyleEnforcer.get_enforcement(style_name)
            if enforcement and enforcement.music_hint:
                return enforcement.music_hint
        except ImportError:
            pass
        # 从本地 MUSIC_HINTS dict 获取
        hint = self.MUSIC_HINTS.get(style_name, "")
        if hint:
            return hint
        # fallback
        return self.MUSIC_HINTS.get("custom", "acoustic versatile palette, match visual mood")


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


def get_music_hint(style_name: str) -> str:
    """
    获取风格对应的音乐方向提示（music_hint）
    Pipeline 集成 Wave 1 Step B — 给 Haiku 生成 BGM prompt 时的视觉→音乐锚点
    """
    builder = StyleConfigBuilder()
    return builder.get_music_hint(style_name)
