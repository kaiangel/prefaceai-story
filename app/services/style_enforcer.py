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
    music_hint: str = ""               # 音乐方向提示（给 Haiku 生成 BGM prompt 时的视觉→音乐锚点）


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
            quality_keywords=["8K", "high resolution", "sharp focus", "professional lighting", "DSLR quality"],
            music_hint="contemporary naturalistic, sparse and grounded, acoustic-piano palette, no synthetic sheen"
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
            quality_keywords=["high quality animation", "professional cartoon", "polished artwork"],
            music_hint="bright orchestral, playful mid-tempo, warm and bouncy, light percussion with melodic energy"
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
            quality_keywords=["high quality 3D render", "professional animation", "studio quality"],
            music_hint="cinematic orchestral warmth, full strings with adventure lift, emotional and sweeping but never dark"
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
            quality_keywords=["high quality anime", "professional anime art", "detailed anime"],
            music_hint="J-pop adjacent cinematic, piano and strings leading, clean production, emotional directness and youthful energy"
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
            quality_keywords=["Ghibli quality", "masterful animation", "hand-painted look"],
            music_hint="pastoral romantic, acoustic strings and light winds, nostalgic warmth with childlike wonder and open-sky breathing room"
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
            quality_keywords=["artstation trending", "professional illustration", "high detail"],
            music_hint="polished contemporary, piano-led with lush production, emotionally articulate without genre constraint"
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
            quality_keywords=["beautiful watercolor", "artistic quality", "delicate washes"],
            music_hint="impressionist gentle, soft-edged textures, dreamy piano and light strings, unhurried and quietly luminous"
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
            quality_keywords=["professional children's illustration", "picture book quality", "appealing to children"],
            music_hint="tender folk-lullaby warmth, gentle and unhurried, innocence without sentimentality, safe and loving sonic space"
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
            quality_keywords=["professional manga", "detailed linework", "high quality manga art"],
            music_hint="Japanese cinematic with dramatic peaks and quiet valleys, tension-release arc, emotionally charged pacing"
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
            quality_keywords=["professional manga art", "detailed linework", "cinematic manga composition", "masterful ink work", "dynamic action poses"],
            music_hint="athletic cinematic energy, pulsing rhythm beneath restrained tension, the weight of sweat and rivalry and silent crowd breath"
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
            quality_keywords=["professional webtoon", "polished digital art", "beautiful character design", "clean coloring"],
            music_hint="K-drama romantic ambient, clean production with emotional restraint, the ache of almost-said feelings"
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
            quality_keywords=["museum quality", "masterful painting", "fine art"],
            music_hint="classical chamber gravity, strings and harpsichord or piano, Old World weight and emotional gravitas"
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
            quality_keywords=["atmospheric", "cinematic cyberpunk", "detailed futuristic"],
            music_hint="electronic nocturne, analog synth pulse with neon underlayer, metropolitan cold, rain-soaked and machine-breathing"
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
            quality_keywords=["elegant", "masterful brushwork", "traditional aesthetics"],
            music_hint="East Asian minimalist, guqin or dizi or xiao color, negative space breathes between notes, ink-brush pacing"
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
            quality_keywords=["clean pixels", "well-designed pixel art", "professional retro"],
            music_hint="chiptune adjacent or simple pentatonic, clean retro character, nostalgia without irony, constrained palette of sound"
        ),

        # ============ 浮世绘风格 ============
        "ukiyo_e": StyleEnforcement(
            style_name="ukiyo_e",
            style_display_name="Ukiyo-e Japanese Woodblock Print",
            mandatory_keywords=[
                "ukiyo-e style", "Japanese woodblock print", "flat color areas",
                "bold outlines", "traditional Japanese art", "decorative patterns",
                "Edo period aesthetic", "woodcut texture", "Japanese composition"
            ],
            forbidden_keywords=[
                "photorealistic", "photograph", "3D render", "CGI", "digital effects",
                "neon lights", "modern setting", "Western art style", "gradient shading",
                "photographic", "realistic skin texture", "smooth blending", "pixel art"
            ],
            style_description="You are carving in the tradition of ukiyo-e masters — Hokusai, Hiroshige, Utamaro — artists who compressed the floating world into flat planes of pure color and fearless line. Light does not model form through gradient — it exists as decisive areas of color separated by bold outlines, each block printed with the pressure of carved cherry wood against mulberry paper. Colors are the pigments of the woodblock palette: indigo blues that deepen like evening water, vermillion reds that burn with festival intensity, soft ochres and greens drawn from mineral and vegetable sources, and the warm cream of washi paper glowing through unprinted areas. Every surface declares its flat, printed nature: fabric patterns rendered as precise repeating motifs, water as stylized curling waves, clouds as decorative bands floating across the composition. Characters are defined by costume and posture rather than anatomical modeling — flowing kimono lines, elaborate hair arrangements, faces rendered with minimal but expressive economy: a tilted head, a sidelong glance, fingers delicately positioned. Each composition follows ukiyo-e's sophisticated spatial logic: layered flat planes creating depth without perspective, diagonal elements generating dynamic tension, and asymmetric balance where a single branch or figure anchors vast areas of atmospheric space.",
            quality_keywords=["masterful woodblock print", "museum quality ukiyo-e", "detailed traditional art", "authentic Japanese aesthetic", "elegant composition"],
            music_hint="Japanese classical serenity, shamisen or koto color, Edo period floating world, decorative elegance and unhurried grace"
        ),

        # ============ 复古胶片风格 ============
        "vintage_film": StyleEnforcement(
            style_name="vintage_film",
            style_display_name="Vintage Film Photography",
            mandatory_keywords=[
                "vintage film photography", "film grain", "analog camera aesthetic",
                "Kodak Portra tones", "retro color grading", "soft focus",
                "70s 80s film look", "nostalgic photography", "warm film tones"
            ],
            forbidden_keywords=[
                "digital clarity", "HDR", "neon", "cyberpunk", "anime", "cartoon",
                "3D render", "sharp digital", "modern clean", "vector", "pixel art",
                "illustration", "painting", "watercolor"
            ],
            style_description="You are shooting in the tradition of analog film photographers — artists who understood that imperfection is intimacy, that grain is warmth, and that faded color carries the weight of time. Light arrives through the gentle imprecision of vintage glass: soft halation blooming around highlights, lens flares that streak like golden memories, and a natural falloff at frame edges that pulls focus to the center like a whispered secret. Colors wear the patina of aged emulsion — Kodak warmth where skin glows amber, Fuji greens that drift toward teal in shadows, highlights that roll off into creamy whites rather than clinical brightness, and an overall palette that feels like looking at life through honey-colored glass. Every surface carries the honest texture of photochemical process: film grain dancing across the image like visual static, slight color shifts between frames, the occasional light leak painting an edge in unexpected warmth. Characters exist in the unselfconscious beauty of candid moments — the unstaged gesture, the genuine laugh caught between poses, the intimacy of someone unaware they are being observed through a viewfinder. Each composition breathes with the relaxed confidence of photographers who had 36 exposures and made each one count: centered subjects with generous negative space, natural framing through doorways and windows, and the patient stillness of waiting for the right moment rather than manufacturing it.",
            quality_keywords=["authentic film look", "beautiful analog tones", "professional vintage photography", "nostalgic quality", "cinematic film grain"],
            music_hint="analog warmth and grain, lo-fi intimate, the ache of faded photographs, vinyl crackle and soft brass"
        ),

        # ============ 铅笔素描风格 ============
        "pencil_sketch": StyleEnforcement(
            style_name="pencil_sketch",
            style_display_name="Pencil Sketch Drawing",
            mandatory_keywords=[
                "pencil sketch", "graphite drawing", "hand-drawn lines",
                "crosshatching", "sketched artwork", "pencil on paper",
                "detailed pencil work", "monochrome drawing", "fine linework"
            ],
            forbidden_keywords=[
                "photorealistic", "full color", "vibrant colors", "neon",
                "3D render", "digital painting", "watercolor", "oil painting",
                "cartoon", "anime", "pixel art", "glossy", "saturated"
            ],
            style_description="You are drawing in the tradition of master draftsmen — artists who proved that a single graphite pencil against white paper holds infinite range, from the palest whisper of tone to the deepest velvet black. Light is built through the absence and accumulation of marks: bright areas where the paper breathes untouched, mid-tones constructed through patient parallel hatching, and deep shadows layered through crosshatching that builds density like woven darkness. The tonal palette spans the full graphite spectrum — hard pencil lines that leave silvery traces for distant details, soft graphite laid on its side for broad atmospheric washes, and the rich near-black of 6B pressed firmly for moments of dramatic emphasis. Every surface reveals the hand that made it: the slight wobble of a freehand line that proves human presence, the varied pressure that gives each stroke its own character, eraser marks that leave ghost traces of revised decisions, and the tooth of paper grain catching graphite in its texture. Characters emerge through the accumulation of observed detail — the weight of fabric rendered through directional strokes, the luminosity of eyes built from carefully preserved highlights, the suggestion of life in the looseness of hair and the precision of a gaze. Each composition thinks in terms of tonal architecture: large shapes of light and dark establishing the structure, focal areas rendered in crisp detail while periphery dissolves into suggestion, and generous white space that gives the drawing room to breathe.",
            quality_keywords=["masterful pencil work", "detailed graphite drawing", "professional sketch quality", "artistic linework", "museum quality drawing"],
            music_hint="intimate acoustic, bare and unhurried, pencil-on-paper quietness, space between notes as loaded as the notes themselves"
        ),

        # ============ Q版卡通风格 ============
        "chibi": StyleEnforcement(
            style_name="chibi",
            style_display_name="Chibi Cute Cartoon",
            mandatory_keywords=[
                "chibi style", "super deformed", "cute cartoon", "big head small body",
                "kawaii aesthetic", "adorable characters", "rounded proportions",
                "pastel colors", "chibi anime"
            ],
            forbidden_keywords=[
                "photorealistic", "photograph", "realistic anatomy", "realistic proportions",
                "dark gritty", "horror", "violent", "mature content", "oil painting",
                "ink wash", "noir", "gothic", "harsh shadows", "realistic skin"
            ],
            style_description="You are drawing in the tradition of chibi and super-deformed character design — artists who discovered that shrinking a character to their most essential, adorable proportions amplifies emotion by a thousand percent. Light is universally kind: soft even illumination that eliminates harsh shadows, gentle highlights on round cheeks, and an overall brightness that keeps every scene feeling safe and joyful. Colors burst with sugary energy — cotton candy pinks, sky blues, mint greens, sunny yellows — all pushed toward their most cheerful saturation, with pastel backgrounds that never compete with the characters' candy-colored world. Proportions follow the sacred chibi ratio: heads occupy one-half to one-third of total body height, eyes are enormous sparkling orbs that carry every emotion from giddy joy to comedic despair, and tiny stubby limbs gesture with maximum expressiveness despite minimal anatomy. Characters express through exaggeration and simplicity — a blush rendered as two rosy circles, anger as a comically oversized vein mark, joy as closed crescent eyes and a mouth wider than physically possible, each emotion dialed to its most readable extreme. Each composition keeps things delightfully simple: clean uncluttered backgrounds often reduced to color fields or simple patterns, characters centered and prominent, and generous use of cute decorative elements — sparkles, hearts, stars, musical notes — floating around characters like emotional subtitles.",
            quality_keywords=["adorable chibi art", "professional kawaii style", "cute character design", "polished chibi illustration", "clean coloring"],
            music_hint="kawaii pop bubbly, high-register bright and bouncy, sugary sweet texture, maximum smile energy"
        ),

        # ============ 暗黑奇幻风格 ============
        "dark_fantasy": StyleEnforcement(
            style_name="dark_fantasy",
            style_display_name="Dark Fantasy Art",
            mandatory_keywords=[
                "dark fantasy art", "epic fantasy illustration", "dramatic dark lighting",
                "mythical atmosphere", "fantasy concept art", "otherworldly",
                "dark magical ambiance", "epic scale", "fantasy character design"
            ],
            forbidden_keywords=[
                "photorealistic photograph", "cute", "kawaii", "chibi", "bright cheerful",
                "pastel colors", "children's style", "pixel art", "minimalist",
                "flat design", "cartoon comedy", "pop art", "light-hearted"
            ],
            style_description="You are painting in the tradition of dark fantasy masters — Beksinski's organic nightmares, Frazetta's primal power, and the brooding majesty of artists who find beauty in shadow and terror in grandeur. Light is rare and precious: a single torch flame carving warmth from engulfing darkness, bioluminescent flora casting an alien glow through primordial caverns, moonlight filtering through storm clouds to silver-edge a figure standing against the void. Colors are drawn from a palette of ancient darkness — deep crimsons like dried blood, midnight blues that swallow distance, tarnished golds that suggest fallen glory, and the sickly greens of things that grow where light cannot reach. Every surface tells of age and power: stone carved with forgotten runes now cracked by centuries, armor scarred by battles whose names are lost, forests where trees twist with an intelligence that predates humanity, and skies where clouds form shapes that might be gods or might be warnings. Characters carry the weight of mythic archetypes — warriors whose scars map their survival, sorcerers whose eyes hold forbidden knowledge, creatures that blur the boundary between beautiful and terrifying. Each composition builds toward the sublime: vast scale that dwarfs human figures against impossible architecture, dramatic contrasts between illuminated subjects and consuming darkness, and the careful placement of light sources that make every shadow feel like it might contain something watching.",
            quality_keywords=["epic fantasy illustration", "cinematic dark art", "concept art quality", "detailed fantasy rendering", "atmospheric dark painting"],
            music_hint="epic dark orchestral, weight of ancient stone and mythic power, low brass and deep resonance, shadows that breathe"
        ),

        # ============ 波普艺术风格 ============
        "pop_art": StyleEnforcement(
            style_name="pop_art",
            style_display_name="Pop Art",
            mandatory_keywords=[
                "pop art style", "Andy Warhol inspired", "Roy Lichtenstein",
                "bold primary colors", "Ben-Day dots", "comic book aesthetic",
                "graphic bold outlines", "flat vibrant colors", "pop culture art"
            ],
            forbidden_keywords=[
                "photorealistic", "subtle tones", "muted colors", "watercolor",
                "oil painting texture", "3D render", "anime", "pixel art",
                "dark gritty", "minimalist", "ink wash", "traditional painting",
                "soft gradients", "pastel"
            ],
            style_description="You are creating in the tradition of Pop Art provocateurs — Warhol, Lichtenstein, Haring — artists who grabbed mass culture by the throat and held it up as fine art, proving that bold is beautiful and repetition is revelation. Light is graphic rather than natural: flat and even, eliminating subtle shadow in favor of bold color blocks that read like billboard advertisements, with occasional dramatic spotlights rendered as simple geometric shapes. Colors scream with commercial intensity — fire engine red, electric blue, taxi cab yellow, shocking pink — each applied in flat unmodulated areas that vibrate against each other with optical aggression, creating images that demand attention from across any room. Every surface is reduced to its graphic essence: Ben-Day dots simulating tone and texture with mechanical precision, thick black outlines containing color like stained glass, and the deliberate absence of nuanced shading replaced by hard-edged shadow shapes. Characters become icons — faces simplified to their most recognizable features then amplified, expressions frozen at their most dramatic or banal, ordinary people elevated to celebrity status through the sheer force of graphic treatment. Each composition embraces the language of commercial design: centered subjects with maximum impact, text elements integrated as graphic components, serial repetition that transforms single images into patterns, and the aggressive cropping that turns a face or an object into a cultural statement.",
            quality_keywords=["bold pop art", "graphic art quality", "professional pop illustration", "iconic pop style", "vibrant graphic design"],
            music_hint="bold pop energy, repetitive hook-driven, bright and irreverent, commercial punch with artistic attitude"
        ),

        # ============ 中国剪纸风格 ============
        "paper_cut": StyleEnforcement(
            style_name="paper_cut",
            style_display_name="Chinese Paper Cut Art",
            mandatory_keywords=[
                "Chinese paper cut art", "jianzhi style", "paper cutting silhouette",
                "intricate paper craft", "red paper cut", "folk art aesthetic",
                "traditional Chinese craft", "layered paper", "decorative cutout"
            ],
            forbidden_keywords=[
                "photorealistic", "3D render", "digital effects", "neon",
                "Western art", "anime", "manga", "oil painting", "watercolor wash",
                "pixel art", "gradient shading", "photographic", "smooth blending"
            ],
            style_description="You are cutting in the tradition of Chinese jianzhi masters — folk artists whose scissors and knives transform flat paper into worlds of astonishing intricacy, where negative space tells the story as eloquently as the remaining form. Light does not fall from any source — it passes through: the bright background shining through cut-away areas creates luminous negative shapes that define figures, patterns, and scenes, while the uncut paper creates bold silhouettes rich with internal detail. Color follows the jianzhi tradition — predominantly festive red against white or gold backgrounds, with occasional polychrome versions layering colored papers to create depth, each color a distinct flat plane with no gradation. Every surface celebrates the paper's own nature: crisp clean edges where the blade has passed, intricate internal patterns of flowers, clouds, and geometric motifs cut within larger forms, and the slight dimensional quality of layered paper casting tiny real shadows. Characters are defined through silhouette and costume detail — elaborate headdresses, flowing robes with patterned borders, theatrical poses that read clearly as flat shapes, faces in profile or three-quarter view rendered with minimal but expressive cutout features. Each composition follows folk art's decorative logic: bilateral symmetry for auspicious subjects, border frames of intertwining vines and auspicious symbols, layered foreground and background planes that create theatrical depth, and the joyful density of pattern filling every available space with meaning and beauty.",
            quality_keywords=["exquisite paper cut art", "masterful jianzhi craft", "traditional folk art quality", "intricate cutting detail", "authentic Chinese craft"],
            music_hint="Chinese folk festivity, erhu and pipa warmth, jianzhi red-paper brightness, celebration and community spirit"
        ),

        # ============ 蒸汽朋克风格 ============
        "steampunk": StyleEnforcement(
            style_name="steampunk",
            style_display_name="Steampunk Aesthetic",
            mandatory_keywords=[
                "steampunk style", "Victorian aesthetic", "brass and copper machinery",
                "clockwork mechanisms", "steam-powered technology", "industrial gears",
                "retro-futuristic", "Victorian fashion", "mechanical details"
            ],
            forbidden_keywords=[
                "modern technology", "digital screens", "neon lights", "minimalist",
                "clean futuristic", "anime", "chibi", "kawaii", "pixel art",
                "flat colors", "watercolor", "paper cut", "ink wash", "pastel"
            ],
            style_description="You are engineering in the tradition of steampunk visionaries — artists who imagined a future that the Victorians might have built, where steam power never yielded to electricity and every machine is a work of brass-and-glass art. Light comes from flame and filament: gas lamps casting warm amber pools through fog-thick streets, furnace glow painting engineers in hellish orange, and the pale daylight of industrial cities filtering through soot-stained skylights. Colors are drawn from the steampunk material palette — warm brass and burnished copper, deep mahogany and rich leather brown, verdigris patina on aged bronze, and the steel-gray of iron machinery, all set against the sepia warmth of aged parchment and the cream of Victorian wallpaper. Every surface is a celebration of mechanical craft: exposed gears meshing with mathematical precision, riveted metal plates joined with visible bolts, polished wood inlaid with brass instruments, glass dials and pressure gauges clustered on every available surface. Characters dress at the intersection of elegance and engineering — top hats fitted with brass goggles, corsets reinforced with leather straps, waistcoats hung with pocket watches and miniature tools, and the soot under fingernails that marks an inventor who works with their hands. Each composition builds layered mechanical worlds: foreground machinery framing characters like industrial portraiture, background skylines bristling with smokestacks and airship masts, and the satisfying visual density of a world where every device proudly displays its working parts.",
            quality_keywords=["detailed steampunk illustration", "professional mechanical design", "atmospheric steampunk art", "Victorian-era quality", "intricate machinery detail"],
            music_hint="Victorian mechanical grandeur, brass ensemble with clockwork rhythm, industrial elegance and adventurous invention"
        ),

        # ============ 新艺术风格 ============
        "art_nouveau": StyleEnforcement(
            style_name="art_nouveau",
            style_display_name="Art Nouveau Style",
            mandatory_keywords=[
                "Art Nouveau style", "Alphonse Mucha inspired", "organic flowing lines",
                "decorative borders", "floral ornamental patterns", "elegant curves",
                "sinuous organic forms", "ornate illustration", "belle epoque aesthetic"
            ],
            forbidden_keywords=[
                "photorealistic", "3D render", "pixel art", "minimalist",
                "harsh geometric", "brutalist", "cyberpunk", "dark gritty",
                "cartoon comedy", "chibi", "sharp angles only", "industrial"
            ],
            style_description="You are designing in the tradition of Art Nouveau masters — Mucha, Klimt, Beardsley — artists who believed that art should flow like nature and that decoration is not excess but essence. Light glows from within: figures and flowers seem to generate their own radiance, with soft golden halos and warm backlighting that makes every subject appear blessed by an inner luminosity, shadows remaining gentle and warm rather than harsh. Colors follow nature's most elegant palette — dusty rose, sage green, warm gold, deep teal, and muted lavender — applied in flat or gently gradated areas bounded by the defining outlines, occasionally punctuated by rich jewel tones that glow like stained glass panels. Every surface is alive with organic ornament: sinuous vine tendrils framing the composition, flowers that are botanically recognizable yet stylized into flowing decorative motifs, hair cascading in impossible arabesque curves that become part of the overall pattern. Characters — predominantly elegant figures — are defined by the flowing line that traces their forms: long necks, cascading hair that merges with surrounding flora, draped fabrics that follow the body in idealized curves, and poses that embody grace and contemplation rather than action. Each composition follows Mucha's theatrical logic: figures centered within elaborate decorative frames, symmetrical or near-symmetrical arrangements that lend poster-like impact, halo-shaped backgrounds that sanctify the subject, and the integration of typography and ornament into a unified visual experience where every element serves both decoration and narrative.",
            quality_keywords=["masterful Art Nouveau illustration", "Mucha-quality decorative art", "elegant ornamental design", "professional belle epoque style", "exquisite flowing linework"],
            music_hint="fin-de-siècle lush and flowing, orchestral with organic sweep, belle époque grace, nature and beauty intertwined"
        ),

        # ============ 黑色电影风格 ============
        "noir": StyleEnforcement(
            style_name="noir",
            style_display_name="Film Noir Cinematic",
            mandatory_keywords=[
                "film noir style", "high contrast black and white", "dramatic shadows",
                "venetian blind lighting", "hard-boiled detective aesthetic",
                "chiaroscuro", "moody atmosphere", "1940s cinematic", "noir lighting"
            ],
            forbidden_keywords=[
                "bright colors", "vibrant", "cheerful", "kawaii", "cartoon comedy",
                "pastel", "children's style", "pixel art", "pop art",
                "watercolor", "flat lighting", "even illumination", "neon"
            ],
            style_description="You are filming in the tradition of noir cinematographers — artists who proved that darkness is not the absence of light but its most powerful expression, where shadows carry more story than anything illumination reveals. Light is the protagonist's adversary and confessor: a single desk lamp carving a face into halves of knowledge and secret, venetian blind shadows striping a wall like prison bars, the cold fluorescent of an interrogation room leaving no place to hide, and the rain-blurred glow of a distant streetlight promising safety that never arrives. The palette is the grayscale's full dramatic range — crushed blacks that swallow entire backgrounds, silvery mid-tones on rain-wet surfaces, and the shocking bright white of a femme fatale's cigarette smoke or a detective's shirt cuff emerging from darkness. Every surface glistens with noir's signature moisture: rain-slicked streets reflecting fractured light, polished desk surfaces mirroring the overhead interrogation lamp, chrome bumpers of parked sedans catching stray illumination, and the wet sheen of a trench coat that has been through one too many stakeouts. Characters are defined by what the light chooses to reveal — a jaw clenched in determination, eyes hidden under a fedora brim, the curl of cigarette smoke rising from a silhouette, hands that grip or gesture from pools of shadow. Each composition uses noir's geometric vocabulary: extreme high angles that make characters feel trapped, low angles that turn ordinary people into threatening figures, Dutch tilts for a world off its moral axis, and the deep-focus compositions where foreground and background both hold clues.",
            quality_keywords=["cinematic noir photography", "dramatic black and white", "professional film noir", "atmospheric monochrome", "masterful shadow work"],
            music_hint="jazz cool and shadowed, muted trumpet or saxophone through cigarette smoke, 1940s after-midnight urban dread"
        ),

        # ============ 欧美漫画风格 ============
        "comic_western": StyleEnforcement(
            style_name="comic_western",
            style_display_name="Western Comic Book Art",
            mandatory_keywords=[
                "Western comic book style", "Marvel DC aesthetic", "bold comic colors",
                "superhero art", "dynamic action poses", "comic book inking",
                "heroic proportions", "dramatic comic composition", "comic panel art"
            ],
            forbidden_keywords=[
                "anime", "manga", "chibi", "kawaii", "photorealistic photograph",
                "watercolor", "ink wash", "pixel art", "minimalist",
                "soft pastel", "oil painting", "children's book", "cute"
            ],
            style_description="You are drawing in the tradition of Western comic book legends — Kirby, Ross, Lee, McFarlane — artists who turned ink and color into a mythology where every human body becomes heroic architecture and every panel crackles with kinetic force. Light is theatrical and purposeful: dramatic rim lighting that separates figures from backgrounds like spotlights on a stage, bold shadow shapes that define musculature and create instant drama, and the signature comic technique of colored lighting — blue key light from one side, warm fill from another — that gives flat illustrations three-dimensional punch. Colors are the saturated primaries and secondaries of four-color printing pushed to maximum impact — Superman blue, Hulk green, Spider-Man red — applied in bold flat areas with decisive shadow shapes, skin tones that glow with idealized vitality, and backgrounds that shift color temperature to match the emotional register of the scene. Every surface declares its material through confident linework: muscles defined by precise anatomical inking, fabric stretching and folding under physical force, metal reflecting environment in simplified highlight shapes, and the dynamic hatching and crosshatching that builds texture and shadow. Characters embody heroic idealism — powerful proportions with broad shoulders and dynamic stances, clenched fists and billowing capes that suggest action even in still moments, faces that project determination and emotion with comic clarity. Each composition explodes with energy: dramatic foreshortening that makes fists and feet burst toward the viewer, diagonal compositions that keep the eye racing, the iconic low angle that makes every figure monumental, and dynamic camera angles borrowed from action cinematography.",
            quality_keywords=["professional comic book art", "heroic illustration quality", "dynamic comic composition", "bold inking", "cinematic comic style"],
            music_hint="heroic action orchestral, bold punchy themes, larger-than-life energy, kinetic momentum and triumphant resolve"
        ),

        # ============ 梦幻马卡龙风格 ============
        "pastel_dream": StyleEnforcement(
            style_name="pastel_dream",
            style_display_name="Pastel Dreamscape",
            mandatory_keywords=[
                "pastel color palette", "dreamy soft aesthetic", "ethereal atmosphere",
                "soft pink and lavender tones", "gentle gradient lighting",
                "whimsical fairy tale", "cotton candy colors", "soft focus dreamy"
            ],
            forbidden_keywords=[
                "dark", "gritty", "noir", "horror", "harsh shadows",
                "cyberpunk", "industrial", "photorealistic", "desaturated",
                "monochrome", "black and white", "gothic", "violent", "bold contrast"
            ],
            style_description="You are painting in the tradition of pastel dreamscape artists — creators who build worlds from spun sugar and morning mist, where every color arrives pre-softened and every edge dissolves into reverie. Light suffuses everything with gentle warmth: no harsh source, no hard shadow, just an omnipresent luminous glow as if the entire world is lit from within by rose-gold dawn that never quite becomes full day. Colors exist exclusively in their most tender register — powder pink, baby blue, lavender, mint cream, peach, and soft coral — each further softened by the addition of white until they feel like tinted air rather than pigment, gradients transitioning so gently between hues that boundaries disappear into chromatic whispers. Every surface feels impossibly soft: clouds that look like they would yield to a finger's touch, petals with translucent edges, fabrics that drift and float as if gravity itself has been gentled, and backgrounds that fade into luminous fog at their edges. Characters are delicate and idealized — smooth skin with the faintest blush, large gentle eyes that shimmer with reflected pastel light, hair that flows in soft waves catching pink and lavender highlights, and expressions that lean toward wonder, tenderness, and quiet joy. Each composition creates floating sanctuary: subjects surrounded by generous breathing space of soft gradient, decorative elements — butterflies, petals, sparkles, bubbles — drifting through the air like visual poetry, and an overall sense that the frame captures a moment existing somewhere between waking and the sweetest possible dream.",
            quality_keywords=["beautiful pastel art", "ethereal illustration quality", "professional dreamy aesthetic", "soft luminous coloring", "delicate atmospheric art"],
            music_hint="ethereal soft drift, luminous and weightless, cotton-candy warmth, between waking and the sweetest dream"
        ),

        # ============ 哥特风格 ============
        "gothic": StyleEnforcement(
            style_name="gothic",
            style_display_name="Gothic Dark Romantic",
            mandatory_keywords=[
                "gothic art style", "dark romantic aesthetic", "cathedral architecture",
                "ornate dark details", "dramatic chiaroscuro", "Victorian gothic",
                "ravens and roses", "stained glass", "dark elegance"
            ],
            forbidden_keywords=[
                "bright cheerful", "kawaii", "chibi", "pastel", "pop art",
                "cartoon comedy", "pixel art", "minimalist", "flat design",
                "children's style", "sunny", "beach", "tropical"
            ],
            style_description="You are creating in the tradition of Gothic romantics — artists who find transcendent beauty in darkness, who see cathedrals as stone prayers and graveyards as gardens of memory. Light enters through colored glass: stained windows casting jewel-toned patterns across stone floors, candelabra flames making shadows dance on vaulted ceilings, moonlight filtering through gargoyle-guarded apertures to silver-edge figures in prayer or contemplation. Colors are drawn from the Gothic palette — deep burgundy, midnight purple, forest black-green, tarnished silver, and bone white — occasionally pierced by the gemstone brilliance of stained glass ruby and sapphire that burn with spiritual intensity against surrounding shadow. Every surface carries the weight of centuries: stone walls where moisture traces dark veins, wrought iron twisted into thorned arabesques, velvet that absorbs light into its deep folds, aged wood carved with saints and sinners, and the patina of silver tarnishing under generations of candlesmoke. Characters embody dark elegance — pale skin that glows against dark clothing, features caught between beauty and melancholy, elaborate Victorian or medieval dress rich with lace and embroidery, and the stillness of figures who have made peace with the darkness around them. Each composition builds architectural drama: towering vertical elements that draw the eye upward like nave columns, pointed arches framing figures like altarpieces, the interplay of massive stone structure and intimate human vulnerability, and the presence of Gothic's symbolic vocabulary — ravens, roses, thorns, keys, and the ever-present dance of candlelight against encroaching shadow.",
            quality_keywords=["atmospheric gothic art", "dark romantic illustration", "detailed gothic architecture", "professional dark fantasy", "elegant Victorian aesthetic"],
            music_hint="dark romantic cathedral resonance, organ or choir undertow, beauty found in shadow, ornate melancholy and sacred dread"
        ),
    }

    @classmethod
    def create_custom_enforcement(cls, analysis: dict) -> "StyleEnforcement":
        """从自定义风格分析结果创建动态 StyleEnforcement"""
        return StyleEnforcement(
            style_name="custom",
            style_display_name=analysis.get("style_display_name", "Custom Style"),
            mandatory_keywords=analysis.get("mandatory_keywords", []),
            forbidden_keywords=analysis.get("forbidden_keywords", []),
            style_description=analysis.get("style_description", ""),
            quality_keywords=analysis.get("quality_keywords", []),
        )

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
