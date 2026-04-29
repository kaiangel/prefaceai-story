"""
style_music_hints.py — 95 风格 × music_hint 字典

BGM-1 修复：T5 测试发现 outline 缺 music_hint 字段导致 BGM 不对味
（豫北悲伤民俗故事 + 铅笔素描 → Haiku 推成 acoustic guitar 而不是悲怆唢呐）。

设计原则（V4 极简哲学）：
  - raw_hint ≤400 字符；质量优先于长度；英文
  - 身体感觉 / 空间氛围描述，不列乐器清单（乐器作为色彩参考，非乐队编制说明）
  - 中乐用 guqin / dizi / xiao / erhu / pipa / zheng / gayageum 等作为色彩标记
  - 28 StyleEnforcer 上架风格：手工高质量填充
  - 67 style_config 独有风格：合理 default fallback + TODO 标记

用法：
  from app.services.style_music_hints import get_music_hint, get_raw_hint

  # Backend 在 Pipeline Stage 1 后查表，填写 outline.music_hint
  raw_hint = get_raw_hint(visual_style_preset)

  # Downstream story_music_extractor 透传给 Haiku 的 visual_style_hint 参数
  story_data = extract_story_for_music(
      outline=outline,
      screenplay=screenplay,
      visual_style_hint=raw_hint,
  )
"""

from typing import Dict

# ================================================================
# 核心字典结构说明
# ================================================================
#
#   primary_genre   : 音乐大类 / 风格流派（英文，逗号分隔可多项）
#   instruments     : 音色参考乐器列表（作为色彩标记，非编制规定）
#   tempo           : 速度感（"very slow" / "slow" / "moderate" / "upbeat" / "fast"）
#   mood_modifier   : 情绪质感描述（身体感觉 / 空间氛围，英文）
#   raw_hint        : ≤400 字符整句，直接注入 outline.music_hint + visual_style_hint
#
# ================================================================

STYLE_MUSIC_HINTS: Dict[str, Dict] = {

    # ============================================================
    # 【A】28 StyleEnforcer 上架风格 — 手工高质量填充
    # ============================================================

    "realistic": {
        "primary_genre": "contemporary / naturalistic / acoustic",
        "instruments": ["piano", "acoustic guitar", "light strings"],
        "tempo": "moderate",
        "mood_modifier": "sparse and grounded, no synthetic sheen, documentary stillness",
        "raw_hint": "contemporary naturalistic, sparse and grounded, acoustic-piano palette, no synthetic sheen",
    },

    "cartoon": {
        "primary_genre": "orchestral / animated score",
        "instruments": ["woodwinds", "brass", "light percussion", "xylophone"],
        "tempo": "upbeat",
        "mood_modifier": "bright and bouncy, warm playful energy, melodic and expressive",
        "raw_hint": "bright orchestral, playful mid-tempo, warm and bouncy, light percussion with melodic energy",
    },

    "pixar_3d": {
        "primary_genre": "cinematic orchestral / animated feature score",
        "instruments": ["full strings", "French horn", "piano", "woodwinds"],
        "tempo": "moderate",
        "mood_modifier": "sweeping and emotional, adventure-lift warmth, never dark",
        "raw_hint": "cinematic orchestral warmth, full strings with adventure lift, emotional and sweeping but never dark",
    },

    "anime": {
        "primary_genre": "J-pop adjacent / cinematic anime score",
        "instruments": ["piano", "strings", "clean electric guitar"],
        "tempo": "moderate",
        "mood_modifier": "emotional directness, youthful energy, clean production",
        "raw_hint": "J-pop adjacent cinematic, piano and strings leading, clean production, emotional directness and youthful energy",
    },

    "ghibli": {
        "primary_genre": "pastoral romantic / acoustic chamber",
        "instruments": ["acoustic guitar", "strings", "flute", "accordion"],
        "tempo": "slow",
        "mood_modifier": "nostalgic warmth, childlike wonder, open-sky breathing room",
        "raw_hint": "pastoral romantic, acoustic strings and light winds, nostalgic warmth with childlike wonder and open-sky breathing room",
    },

    "illustration": {
        "primary_genre": "contemporary / piano-led / lush production",
        "instruments": ["piano", "strings", "warm synth pads"],
        "tempo": "moderate",
        "mood_modifier": "polished and emotionally articulate, no genre constraint",
        "raw_hint": "polished contemporary, piano-led with lush production, emotionally articulate without genre constraint",
    },

    "watercolor": {
        "primary_genre": "impressionist / acoustic / chamber",
        "instruments": ["piano", "light strings", "music box"],
        "tempo": "slow",
        "mood_modifier": "soft-edged textures, dreamy and quietly luminous, unhurried",
        "raw_hint": "impressionist gentle, soft-edged textures, dreamy piano and light strings, unhurried and quietly luminous",
    },

    "children_book": {
        "primary_genre": "folk / lullaby / chamber",
        "instruments": ["acoustic guitar", "ukulele", "gentle piano", "glockenspiel"],
        "tempo": "slow",
        "mood_modifier": "tender innocence, safe and loving sonic space, gentle and unhurried",
        "raw_hint": "tender folk-lullaby warmth, gentle and unhurried, innocence without sentimentality, safe and loving sonic space",
    },

    "manga": {
        "primary_genre": "cinematic / dramatic score / anime hybrid",
        "instruments": ["strings", "piano", "taiko", "electric guitar"],
        "tempo": "moderate",
        "mood_modifier": "dramatic peaks and quiet valleys, tension-release arc, emotionally charged",
        "raw_hint": "Japanese cinematic with dramatic peaks and quiet valleys, tension-release arc, emotionally charged pacing",
    },

    "slam_dunk": {
        "primary_genre": "cinematic / sports score / athletic drama",
        "instruments": ["electric guitar", "brass", "taiko", "synthesizer"],
        "tempo": "upbeat",
        "mood_modifier": "athletic energy, pulsing rhythm beneath restrained tension, sweat and rivalry",
        "raw_hint": "athletic cinematic energy, pulsing rhythm beneath restrained tension, the weight of sweat and rivalry and silent crowd breath",
    },

    "korean_webtoon": {
        "primary_genre": "K-drama romantic ambient / contemporary",
        "instruments": ["piano", "acoustic guitar", "light strings", "soft synth"],
        "tempo": "slow",
        "mood_modifier": "emotional restraint, the ache of almost-said feelings, clean production",
        "raw_hint": "K-drama romantic ambient, clean production with emotional restraint, the ache of almost-said feelings",
    },

    "oil_painting": {
        "primary_genre": "classical chamber / baroque / romantic era",
        "instruments": ["strings", "harpsichord", "piano", "cello"],
        "tempo": "slow",
        "mood_modifier": "classical gravity, Old World weight and emotional gravitas",
        "raw_hint": "classical chamber gravity, strings and harpsichord or piano, Old World weight and emotional gravitas",
    },

    "cyberpunk": {
        "primary_genre": "electronic / industrial / dark ambient",
        "instruments": ["analog synth", "bass synth", "electronic drums", "processed guitar"],
        "tempo": "moderate",
        "mood_modifier": "metropolitan cold, rain-soaked and machine-breathing, neon underlayer",
        "raw_hint": "electronic nocturne, analog synth pulse with neon underlayer, metropolitan cold, rain-soaked and machine-breathing",
    },

    "ink": {
        "primary_genre": "East Asian classical / ambient / minimal",
        "instruments": ["guqin", "dizi", "xiao", "erhu"],
        "tempo": "very slow",
        "mood_modifier": "negative space breathes between notes, ink-brush pacing, meditative",
        "raw_hint": "East Asian minimalist, guqin or dizi or xiao color, negative space breathes between notes, ink-brush pacing",
    },

    "pixel": {
        "primary_genre": "chiptune / retro game / pentatonic folk",
        "instruments": ["chiptune synthesizer", "simple percussion", "8-bit tones"],
        "tempo": "upbeat",
        "mood_modifier": "nostalgia without irony, constrained palette of sound, clean retro character",
        "raw_hint": "chiptune adjacent or simple pentatonic, clean retro character, nostalgia without irony, constrained palette of sound",
    },

    "ukiyo_e": {
        "primary_genre": "Japanese classical / traditional / Edo period",
        "instruments": ["shamisen", "koto", "shakuhachi", "taiko"],
        "tempo": "slow",
        "mood_modifier": "floating world elegance, decorative and unhurried grace, Edo period serenity",
        "raw_hint": "Japanese classical serenity, shamisen or koto color, Edo period floating world, decorative elegance and unhurried grace",
    },

    "vintage_film": {
        "primary_genre": "lo-fi / analog warmth / jazz-adjacent",
        "instruments": ["piano", "soft brass", "acoustic bass", "brushed drums"],
        "tempo": "slow",
        "mood_modifier": "analog warmth and grain, faded photographs, vinyl crackle, intimate",
        "raw_hint": "analog warmth and grain, lo-fi intimate, the ache of faded photographs, vinyl crackle and soft brass",
    },

    "pencil_sketch": {
        "primary_genre": "acoustic / contemporary classical / intimate",
        "instruments": ["acoustic guitar", "solo piano", "cello"],
        "tempo": "slow",
        "mood_modifier": "pencil-on-paper quietness, space between notes as loaded as the notes themselves",
        "raw_hint": "intimate acoustic, bare and unhurried, pencil-on-paper quietness, space between notes as loaded as the notes themselves",
    },

    "chibi": {
        "primary_genre": "kawaii pop / J-pop / bright orchestral",
        "instruments": ["glockenspiel", "xylophone", "pizzicato strings", "bright piano"],
        "tempo": "upbeat",
        "mood_modifier": "kawaii and bubbly, sugary sweet texture, maximum smile energy",
        "raw_hint": "kawaii pop bubbly, high-register bright and bouncy, sugary sweet texture, maximum smile energy",
    },

    "dark_fantasy": {
        "primary_genre": "epic orchestral / dark cinematic / fantasy score",
        "instruments": ["low brass", "choir", "deep strings", "war drums"],
        "tempo": "slow",
        "mood_modifier": "ancient stone and mythic power, deep resonance, shadows that breathe",
        "raw_hint": "epic dark orchestral, weight of ancient stone and mythic power, low brass and deep resonance, shadows that breathe",
    },

    "pop_art": {
        "primary_genre": "pop / commercial / hook-driven",
        "instruments": ["electric guitar", "bass", "drums", "synth"],
        "tempo": "upbeat",
        "mood_modifier": "bold and irreverent, commercial punch with artistic attitude, repetitive hook-driven",
        "raw_hint": "bold pop energy, repetitive hook-driven, bright and irreverent, commercial punch with artistic attitude",
    },

    "paper_cut": {
        "primary_genre": "Chinese folk / festive / traditional",
        "instruments": ["erhu", "pipa", "suona", "zheng", "dizi"],
        "tempo": "upbeat",
        "mood_modifier": "jianzhi red-paper brightness, celebration and community spirit, folk festivity",
        "raw_hint": "Chinese folk festivity, erhu and pipa warmth, jianzhi red-paper brightness, celebration and community spirit",
    },

    "steampunk": {
        "primary_genre": "Victorian / brass ensemble / industrial adventure",
        "instruments": ["brass section", "clockwork percussion", "strings", "pipe organ"],
        "tempo": "moderate",
        "mood_modifier": "clockwork rhythm, industrial elegance and adventurous invention",
        "raw_hint": "Victorian mechanical grandeur, brass ensemble with clockwork rhythm, industrial elegance and adventurous invention",
    },

    "art_nouveau": {
        "primary_genre": "fin-de-siècle / romantic orchestral / belle époque",
        "instruments": ["harp", "strings", "flute", "oboe"],
        "tempo": "slow",
        "mood_modifier": "organic sweep, belle époque grace, nature and beauty intertwined",
        "raw_hint": "fin-de-siècle lush and flowing, orchestral with organic sweep, belle époque grace, nature and beauty intertwined",
    },

    "noir": {
        "primary_genre": "jazz / dark ambient / 1940s cinematic",
        "instruments": ["muted trumpet", "alto saxophone", "upright bass", "brushed snare"],
        "tempo": "slow",
        "mood_modifier": "cigarette smoke, 1940s after-midnight urban dread, jazz cool and shadowed",
        "raw_hint": "jazz cool and shadowed, muted trumpet or saxophone through cigarette smoke, 1940s after-midnight urban dread",
    },

    "comic_western": {
        "primary_genre": "heroic orchestral / superhero score / cinematic",
        "instruments": ["brass", "full orchestra", "electric guitar", "drums"],
        "tempo": "fast",
        "mood_modifier": "bold punchy themes, larger-than-life energy, kinetic momentum and triumphant resolve",
        "raw_hint": "heroic action orchestral, bold punchy themes, larger-than-life energy, kinetic momentum and triumphant resolve",
    },

    "pastel_dream": {
        "primary_genre": "ethereal / ambient / dream pop",
        "instruments": ["music box", "soft piano", "ambient pads", "light chimes"],
        "tempo": "very slow",
        "mood_modifier": "luminous and weightless, cotton-candy warmth, between waking and sweetest dream",
        "raw_hint": "ethereal soft drift, luminous and weightless, cotton-candy warmth, between waking and the sweetest dream",
    },

    "gothic": {
        "primary_genre": "dark romantic / cathedral / choral",
        "instruments": ["pipe organ", "choir", "cello", "harpsichord"],
        "tempo": "slow",
        "mood_modifier": "beauty found in shadow, ornate melancholy and sacred dread, cathedral resonance",
        "raw_hint": "dark romantic cathedral resonance, organ or choir undertow, beauty found in shadow, ornate melancholy and sacred dread",
    },

    # ============================================================
    # 【B】style_config 独有 67 风格 — 合理 fallback + TODO
    # ============================================================
    # TODO: 上架前手工 polish（上架 = 加入 StyleEnforcer + 加入前端选择器）

    # ---- 艺术媒介/技法 ----

    "colored_pencil": {
        "primary_genre": "folk / acoustic / handcrafted",
        "instruments": ["acoustic guitar", "piano", "light strings"],
        "tempo": "slow",
        "mood_modifier": "warm and handcrafted, soft and personal, handmade emotional warmth",
        "raw_hint": "warm and handcrafted, gentle folk textures, soft and personal, handmade emotional warmth",
        # TODO: 上架前手工 polish
    },

    "charcoal": {
        "primary_genre": "dark ambient / expressive / chamber",
        "instruments": ["cello", "bass clarinet", "piano"],
        "tempo": "slow",
        "mood_modifier": "brooding and expressive, raw emotional weight, stark contrast, gestural",
        "raw_hint": "brooding and expressive, raw emotional weight, dark tones with stark contrast, gestural and unresolved",
        # TODO: 上架前手工 polish
    },

    "marker": {
        "primary_genre": "pop / graphic / commercial",
        "instruments": ["electric guitar", "bass", "synth", "drums"],
        "tempo": "upbeat",
        "mood_modifier": "bold and graphic, energetic and vivid, punchy without subtlety",
        "raw_hint": "bold and graphic, energetic pop-commercial, vivid and punchy, fun without subtlety",
        # TODO: 上架前手工 polish
    },

    "crayon": {
        "primary_genre": "children's / playful / folk",
        "instruments": ["glockenspiel", "acoustic guitar", "piano"],
        "tempo": "upbeat",
        "mood_modifier": "childlike wonder, simple bright melodies, innocent and colorful",
        "raw_hint": "childlike wonder and play, simple bright melodies, innocent and crayon-box colorful",
        # TODO: 上架前手工 polish
    },

    "pastel": {
        "primary_genre": "soft ambient / chamber / intimate",
        "instruments": ["piano", "light strings", "flute"],
        "tempo": "slow",
        "mood_modifier": "soft chalky calm, gentle and tender, quiet living-room intimacy",
        "raw_hint": "soft chalky calm, gentle and tender, pastel warmth without saccharine, quiet living-room intimacy",
        # TODO: 上架前手工 polish
    },

    "acrylic": {
        "primary_genre": "energetic / cinematic / textured",
        "instruments": ["piano", "strings", "percussion"],
        "tempo": "moderate",
        "mood_modifier": "bold and textured, energetic and confident, painterly strokes made audible",
        "raw_hint": "bold and textured, energetic and confident, painterly strokes made audible",
        # TODO: 上架前手工 polish
    },

    "gouache": {
        "primary_genre": "elegant / minimal / contemporary",
        "instruments": ["piano", "acoustic guitar", "light strings"],
        "tempo": "moderate",
        "mood_modifier": "flat and precise, elegant simplicity, matte warmth, illustrated and deliberate",
        "raw_hint": "flat and precise, elegant simplicity, matte warmth, illustrated and deliberate",
        # TODO: 上架前手工 polish
    },

    "woodcut": {
        "primary_genre": "folk / primal / ancient",
        "instruments": ["acoustic guitar", "hand drums", "fiddle"],
        "tempo": "moderate",
        "mood_modifier": "stark and primal, folk resonance, bold and carved, earth texture",
        "raw_hint": "stark and primal, folk or ancient resonance, wood-grain texture in sound, bold and carved",
        # TODO: 上架前手工 polish
    },

    "linocut": {
        "primary_genre": "folk / graphic / earthy",
        "instruments": ["acoustic guitar", "bass", "hand percussion"],
        "tempo": "moderate",
        "mood_modifier": "graphic and forceful, block-print directness, earthy and hand-pressed",
        "raw_hint": "graphic and forceful, block-print directness, earthy and hand-pressed",
        # TODO: 上架前手工 polish
    },

    "collage": {
        "primary_genre": "eclectic / mixed / experimental",
        "instruments": ["piano", "found sounds", "acoustic guitar", "electronic textures"],
        "tempo": "moderate",
        "mood_modifier": "layered and eclectic, mixed textures, unexpected juxtapositions",
        "raw_hint": "layered and eclectic, mixed textures, found-sound warmth, unexpected juxtapositions",
        # TODO: 上架前手工 polish
    },

    "stained_glass": {
        "primary_genre": "sacred / choral / devotional",
        "instruments": ["choir", "pipe organ", "strings"],
        "tempo": "slow",
        "mood_modifier": "cathedral light and resonance, warm devotional glow, jewel-toned and luminous",
        "raw_hint": "cathedral light and resonance, warm devotional glow, jewel-toned and luminous",
        # TODO: 上架前手工 polish
    },

    # ---- 艺术流派 ----

    "impressionist": {
        "primary_genre": "impressionist / classical / light chamber",
        "instruments": ["piano", "flute", "strings", "harp"],
        "tempo": "slow",
        "mood_modifier": "dappled light in sound, flowing and spontaneous, color-as-feeling",
        "raw_hint": "Impressionist shimmering, dappled light in sound, flowing and spontaneous, color-as-feeling",
        # TODO: 上架前手工 polish
    },

    "expressionist": {
        "primary_genre": "atonal / dark classical / expressionist",
        "instruments": ["dissonant strings", "piano", "brass", "percussion"],
        "tempo": "moderate",
        "mood_modifier": "raw and distorted, emotional urgency, dissonance as truth",
        "raw_hint": "raw and distorted, emotional urgency, dissonance as truth, the body before the mind",
        # TODO: 上架前手工 polish
    },

    "surrealist": {
        "primary_genre": "dream / experimental / ambient",
        "instruments": ["theremin", "piano", "processed sounds", "strings"],
        "tempo": "slow",
        "mood_modifier": "dreamlogic and uncanny, the subconscious given sonic shape",
        "raw_hint": "dreamlogic and uncanny, unexpected collisions of texture, the subconscious given sonic shape",
        # TODO: 上架前手工 polish
    },

    "minimalist": {
        "primary_genre": "minimalist / contemporary classical / ambient",
        "instruments": ["piano", "strings", "tuned percussion"],
        "tempo": "very slow",
        "mood_modifier": "spare and essential, slow unfolding, silence as presence",
        "raw_hint": "spare and essential, slow unfolding, each sound chosen with austere intention, silence as presence",
        # TODO: 上架前手工 polish
    },

    "art_deco": {
        "primary_genre": "jazz age / 1920s / glamour",
        "instruments": ["jazz ensemble", "piano", "brass", "strings"],
        "tempo": "upbeat",
        "mood_modifier": "geometric elegance, 1920s cocktail-hour sophistication, jazz age glamour",
        "raw_hint": "jazz age glamour, geometric elegance, 1920s cocktail-hour sophistication",
        # TODO: 上架前手工 polish
    },

    "baroque": {
        "primary_genre": "baroque / classical / counterpoint",
        "instruments": ["harpsichord", "strings", "choir", "organ"],
        "tempo": "moderate",
        "mood_modifier": "Baroque ornamentation and drama, counterpoint layering, grandeur and spiritual intensity",
        "raw_hint": "Baroque ornamentation and drama, counterpoint layering, grandeur and spiritual intensity",
        # TODO: 上架前手工 polish
    },

    "rococo": {
        "primary_genre": "French classical / pastoral / ornamental",
        "instruments": ["harpsichord", "flute", "strings", "oboe"],
        "tempo": "moderate",
        "mood_modifier": "light and playful ornament, French pastoral elegance, powder-and-lace delicacy",
        "raw_hint": "light and playful ornament, French pastoral elegance, powder-and-lace delicacy",
        # TODO: 上架前手工 polish
    },

    "renaissance": {
        "primary_genre": "Renaissance polyphony / sacred / classical",
        "instruments": ["lute", "recorder", "viols", "choir"],
        "tempo": "slow",
        "mood_modifier": "sacred and humanist, measured and luminous, the dignity of craft",
        "raw_hint": "classical polyphony, sacred and humanist, measured and luminous, the dignity of craft",
        # TODO: 上架前手工 polish
    },

    # ---- 文化/地域 ----

    "dunhuang": {
        "primary_genre": "Central Asian / Silk Road / devotional",
        "instruments": ["pipa", "dizi", "santur", "hand drums"],
        "tempo": "slow",
        "mood_modifier": "ancient Silk Road resonance, devotional reverence and cavernous depth",
        "raw_hint": "ancient Silk Road resonance, Central Asian modal color, devotional reverence and cavernous depth",
        # TODO: 上架前手工 polish
    },

    "chinese_ink": {
        "primary_genre": "East Asian classical / minimal / meditative",
        "instruments": ["guqin", "xiao", "dizi"],
        "tempo": "very slow",
        "mood_modifier": "ink-brush pacing, empty space as sound, meditative",
        "raw_hint": "East Asian minimalist, guqin or xiao color, ink-brush pacing, empty space as sound",
        # TODO: 上架前手工 polish
    },

    "chinese_gongbi": {
        "primary_genre": "Chinese court / silk texture / refined",
        "instruments": ["pipa", "zheng", "dizi", "erhu"],
        "tempo": "slow",
        "mood_modifier": "refined and ornate, silk-texture precision, meticulous",
        "raw_hint": "refined Chinese court music, delicate pipa or zheng, meticulous and ornate, silk-texture precision",
        # TODO: 上架前手工 polish
    },

    "persian_miniature": {
        "primary_genre": "Persian classical / modal / illuminated",
        "instruments": ["oud", "tar", "santur", "ney"],
        "tempo": "slow",
        "mood_modifier": "Persian classical modal warmth, illuminated manuscript intricacy",
        "raw_hint": "Persian classical modal warmth, oud and string resonance, illuminated manuscript intricacy",
        # TODO: 上架前手工 polish
    },

    "byzantine": {
        "primary_genre": "Orthodox chant / sacred / Byzantine",
        "instruments": ["choir", "organ", "byzantine chant"],
        "tempo": "very slow",
        "mood_modifier": "golden icon solemnity, sacred and gilded, eternal and austere",
        "raw_hint": "Orthodox chant resonance, golden icon solemnity, sacred and gilded, eternal and austere",
        # TODO: 上架前手工 polish
    },

    "african_tribal": {
        "primary_genre": "African / percussive / communal",
        "instruments": ["djembe", "balafon", "kora", "ngoni"],
        "tempo": "upbeat",
        "mood_modifier": "earth-rooted rhythm, call-and-response vitality, organic and ancestral",
        "raw_hint": "percussive communal energy, earth-rooted rhythm, call-and-response vitality, organic and ancestral",
        # TODO: 上架前手工 polish
    },

    "mexican_mural": {
        "primary_genre": "Mexican folk / revolutionary / communal",
        "instruments": ["mariachi ensemble", "guitarrón", "trumpets", "folk percussion"],
        "tempo": "upbeat",
        "mood_modifier": "folk and revolutionary spirit, bold and communal, social weight",
        "raw_hint": "Mexican folk and revolutionary spirit, mariachi color beneath social weight, bold and communal",
        # TODO: 上架前手工 polish
    },

    "indian_miniature": {
        "primary_genre": "Indian classical / raga / Mughal court",
        "instruments": ["sitar", "sarod", "tabla", "tanpura"],
        "tempo": "slow",
        "mood_modifier": "Mughal court ornament and devotion, Indian classical modal warmth",
        "raw_hint": "Indian classical modal warmth, sitar or sarod raga color, Mughal court ornament and devotion",
        # TODO: 上架前手工 polish
    },

    "korean_traditional": {
        "primary_genre": "Korean traditional / hanji / natural",
        "instruments": ["gayageum", "haegeum", "daegeum", "janggu"],
        "tempo": "slow",
        "mood_modifier": "hanji-paper quietness, natural subject reverence, gentle and precise",
        "raw_hint": "Korean hanji-paper quietness, gayageum or haegeum, natural subject reverence, gentle and precise",
        # TODO: 上架前手工 polish
    },

    "russian_lacquer": {
        "primary_genre": "Russian folk / Palekh / dark warmth",
        "instruments": ["balalaika", "bayan", "domra", "strings"],
        "tempo": "moderate",
        "mood_modifier": "folk tale warmth, Palekh dark-and-gold mystery",
        "raw_hint": "Russian folk tale warmth, balalaika or bayan color, Palekh dark-and-gold mystery",
        # TODO: 上架前手工 polish
    },

    "thai_traditional": {
        "primary_genre": "Thai classical / court / temple",
        "instruments": ["ranat", "khim", "saw duang", "ching"],
        "tempo": "slow",
        "mood_modifier": "Thai classical court splendor, temple painting devotion, golden warmth",
        "raw_hint": "Thai classical court splendor, ranat or khim color, temple painting devotion and golden warmth",
        # TODO: 上架前手工 polish
    },

    # ---- 时代/流行 ----

    "dieselpunk": {
        "primary_genre": "1940s industrial / big band / diesel-edge",
        "instruments": ["big band brass", "drums", "electric guitar", "strings"],
        "tempo": "upbeat",
        "mood_modifier": "1940s industrial drive, Art Deco momentum, big band grit",
        "raw_hint": "1940s industrial drive, big band edge with diesel-engine grit, Art Deco momentum",
        # TODO: 上架前手工 polish
    },

    "atompunk": {
        "primary_genre": "1950s / space-age lounge / retro futurism",
        "instruments": ["theremin", "muted brass", "vibraphone", "strings"],
        "tempo": "moderate",
        "mood_modifier": "atomic optimism, space-age lounge orchestral, Sputnik-era wonder",
        "raw_hint": "1950s atomic optimism, space-age lounge orchestral, Sputnik-era wonder and naive futurism",
        # TODO: 上架前手工 polish
    },

    "solarpunk": {
        "primary_genre": "acoustic / folk / organic hope",
        "instruments": ["acoustic guitar", "ukulele", "flute", "light percussion"],
        "tempo": "moderate",
        "mood_modifier": "green acoustic warmth, sustainable folk energy, living architecture breathing",
        "raw_hint": "green acoustic warmth, organic and hopeful, sustainable folk energy, living architecture breathing",
        # TODO: 上架前手工 polish
    },

    "victorian": {
        "primary_genre": "Victorian parlor / chamber / period romance",
        "instruments": ["piano", "strings", "clarinet", "bassoon"],
        "tempo": "moderate",
        "mood_modifier": "period formality with repressed longing, Victorian parlor elegance",
        "raw_hint": "Victorian parlor elegance, chamber strings and piano, period formality with repressed longing",
        # TODO: 上架前手工 polish
    },

    "80s_neon": {
        "primary_genre": "synth-pop / 1980s / retrowave",
        "instruments": ["analog synth", "drum machine", "electric bass", "electric guitar"],
        "tempo": "upbeat",
        "mood_modifier": "neon grid pulsing, analog warmth meets digital sheen, nostalgic electric",
        "raw_hint": "1980s synth-pop drive, neon grid pulsing, analog warmth meets digital sheen, nostalgic electric",
        # TODO: 上架前手工 polish
    },

    "90s_cartoon": {
        "primary_genre": "90s cartoon / Saturday morning / simple",
        "instruments": ["brass", "woodwinds", "drums", "synth"],
        "tempo": "upbeat",
        "mood_modifier": "Saturday morning energy, 90s cartoon bounce and bold hooks",
        "raw_hint": "Saturday morning energy, upbeat and simple, 90s cartoon bounce and bold hooks",
        # TODO: 上架前手工 polish
    },

    "y2k": {
        "primary_genre": "Y2K / early 2000s pop / digital gloss",
        "instruments": ["pop synth", "electric guitar", "drum machine", "bass"],
        "tempo": "upbeat",
        "mood_modifier": "Y2K pop shimmer, chrome-plated bubblegum electronic",
        "raw_hint": "early 2000s digital gloss, Y2K pop shimmer, chrome-plated bubblegum electronic",
        # TODO: 上架前手工 polish
    },

    "vaporwave": {
        "primary_genre": "vaporwave / slowed / nostalgic ambient",
        "instruments": ["slowed synth", "ambient pads", "saxophone", "electric piano"],
        "tempo": "very slow",
        "mood_modifier": "slowed and dreamlike, mall-music memory distorted, pastel digital haze",
        "raw_hint": "slowed and dreamlike, mall-music memory distorted, melancholy nostalgia bathed in pastel digital haze",
        # TODO: 上架前手工 polish
    },

    "synthwave": {
        "primary_genre": "synthwave / retrowave / neon highway",
        "instruments": ["analog synth", "drum machine", "electric bass", "lead synth"],
        "tempo": "moderate",
        "mood_modifier": "neon highway at night, analog synth warmth with retro-futurist drive",
        "raw_hint": "retrowave pulse, neon highway at night, analog synth warmth with retro-futurist drive",
        # TODO: 上架前手工 polish
    },

    "medieval": {
        "primary_genre": "medieval / lute / tapestry",
        "instruments": ["lute", "recorder", "hurdy-gurdy", "frame drum"],
        "tempo": "slow",
        "mood_modifier": "medieval modal resonance, ancient and sacred, tapestry-pattern repetition",
        "raw_hint": "medieval modal resonance, lute or recorder color, tapestry-pattern repetition, ancient and sacred",
        # TODO: 上架前手工 polish
    },

    # ---- 数字/动画 ----

    "disney_classic": {
        "primary_genre": "fairy-tale orchestral / Disney / classic animation",
        "instruments": ["full orchestra", "choir", "harp", "strings"],
        "tempo": "moderate",
        "mood_modifier": "magical fairy-tale orchestral, sweeping and singable, timeless warmth",
        "raw_hint": "magical fairy-tale orchestral, classic animation wonder, sweeping and singable, timeless warmth",
        # TODO: 上架前手工 polish
    },

    "dreamworks": {
        "primary_genre": "action-comedy / DreamWorks / kinetic",
        "instruments": ["full orchestra", "electric guitar", "drums", "brass"],
        "tempo": "upbeat",
        "mood_modifier": "wit and spectacle, DreamWorks swagger, kinetic energy",
        "raw_hint": "action-comedy orchestral, wit and spectacle, DreamWorks swagger and kinetic energy",
        # TODO: 上架前手工 polish
    },

    "shinkai": {
        "primary_genre": "bittersweet cinematic / piano and strings / emotional",
        "instruments": ["piano", "strings", "acoustic guitar", "ambient pads"],
        "tempo": "slow",
        "mood_modifier": "bittersweet longing, aching with distance, what cannot be held",
        "raw_hint": "bittersweet cinematic, piano and strings aching with distance, Shinkai longing for what cannot be held",
        # TODO: 上架前手工 polish
    },

    "makoto_style": {
        "primary_genre": "slice-of-life / contemporary / quiet emotional",
        "instruments": ["acoustic guitar", "piano", "light strings"],
        "tempo": "slow",
        "mood_modifier": "gentle and everyday, quiet emotional depth, Kyoto Animation warmth",
        "raw_hint": "slice-of-life warmth, gentle and everyday, Kyoto Animation quiet emotional depth",
        # TODO: 上架前手工 polish
    },

    "cel_shaded": {
        "primary_genre": "video game / stylized / adventure",
        "instruments": ["synth", "electric guitar", "drums", "orchestral"],
        "tempo": "upbeat",
        "mood_modifier": "cel-shaded cartoon bounce, stylized game-world energy, adventure palette",
        "raw_hint": "stylized game-world energy, cel-shaded cartoon bounce, video game adventure palette",
        # TODO: 上架前手工 polish
    },

    "flat_design": {
        "primary_genre": "minimal / design / geometric",
        "instruments": ["piano", "light synth", "minimal percussion"],
        "tempo": "moderate",
        "mood_modifier": "clean and geometric, design-thinking aesthetic without sentimentality",
        "raw_hint": "clean and geometric, minimal and precise, design-thinking aesthetic without sentimentality",
        # TODO: 上架前手工 polish
    },

    "isometric": {
        "primary_genre": "puzzle / contemplative / architectural",
        "instruments": ["piano", "light synth", "tuned percussion"],
        "tempo": "slow",
        "mood_modifier": "puzzle-like and contemplative, geometric and calm, architectural curiosity",
        "raw_hint": "puzzle-like and contemplative, architectural curiosity, geometric and calm with playful undertone",
        # TODO: 上架前手工 polish
    },

    "low_poly": {
        "primary_genre": "digital minimal / warm geometric / indie",
        "instruments": ["piano", "acoustic guitar", "soft synth"],
        "tempo": "slow",
        "mood_modifier": "geometric and spare, digital minimalism with warmth, angular but human",
        "raw_hint": "geometric and spare, digital minimalism with warmth, angular but human",
        # TODO: 上架前手工 polish
    },

    "vector": {
        "primary_genre": "graphic / bold / design-forward",
        "instruments": ["piano", "light bass", "minimal percussion"],
        "tempo": "moderate",
        "mood_modifier": "clean graphic precision, bold and scalable, design-forward and unambiguous",
        "raw_hint": "clean graphic precision, bold and scalable, design-forward and unambiguous",
        # TODO: 上架前手工 polish
    },

    "line_art": {
        "primary_genre": "minimal / monochrome / intimate",
        "instruments": ["solo piano", "cello", "acoustic guitar"],
        "tempo": "very slow",
        "mood_modifier": "bare linework quietness, monochrome intimacy, outline and silence",
        "raw_hint": "bare linework quietness, monochrome intimacy, clean and open, outline and silence",
        # TODO: 上架前手工 polish
    },

    "semi_realistic": {
        "primary_genre": "contemporary / grounded / stylized realism",
        "instruments": ["piano", "strings", "acoustic guitar"],
        "tempo": "moderate",
        "mood_modifier": "grounded yet stylized, contemporary with emotional color, real world through artist's eye",
        "raw_hint": "grounded yet stylized, contemporary with emotional color, the real world seen through an artist's eye",
        # TODO: 上架前手工 polish
    },

    "3d_render": {
        "primary_genre": "cinematic / orchestral / warm adventure",
        "instruments": ["full strings", "French horn", "piano", "choir"],
        "tempo": "moderate",
        "mood_modifier": "cinematic orchestral warmth, emotional and sweeping, adventure lift",
        "raw_hint": "cinematic orchestral warmth, full strings with adventure lift, emotional and sweeping but never dark",
        # TODO: 上架前手工 polish
    },

    # ---- 漫画类型 ----

    "manhwa": {
        "primary_genre": "K-drama / romantic ambient / contemporary",
        "instruments": ["piano", "acoustic guitar", "light strings", "soft synth"],
        "tempo": "slow",
        "mood_modifier": "K-drama romantic ambient, emotional restraint, almost-said feelings",
        "raw_hint": "K-drama romantic ambient, clean production with emotional restraint, the ache of almost-said feelings",
        # TODO: 上架前手工 polish
    },

    "manhua": {
        "primary_genre": "Chinese martial arts / cinematic / traditional + modern",
        "instruments": ["erhu", "pipa", "electric guitar", "strings"],
        "tempo": "moderate",
        "mood_modifier": "Chinese martial arts cinematic energy, traditional color beneath modern drama",
        "raw_hint": "Chinese martial arts cinematic energy, traditional instrument color beneath modern drama",
        # TODO: 上架前手工 polish
    },

    "american_comic": {
        "primary_genre": "heroic orchestral / superhero / dynamic",
        "instruments": ["full orchestra", "brass", "electric guitar", "drums"],
        "tempo": "upbeat",
        "mood_modifier": "heroic action, larger-than-life energy, kinetic momentum",
        "raw_hint": "heroic action orchestral, bold punchy themes, larger-than-life energy, kinetic momentum",
        # TODO: 上架前手工 polish
    },

    "marvel_style": {
        "primary_genre": "Marvel cinematic / superhero / wall-of-sound",
        "instruments": ["full orchestra", "choir", "brass", "electric guitar"],
        "tempo": "fast",
        "mood_modifier": "wall-of-sound orchestral, heroic and spectacular, world-saving weight",
        "raw_hint": "Marvel superhero cinematic, wall-of-sound orchestral, heroic and spectacular, world-saving weight",
        # TODO: 上架前手工 polish
    },

    "dc_style": {
        "primary_genre": "DC / dark operatic / mythic",
        "instruments": ["full orchestra", "choir", "low brass", "strings"],
        "tempo": "slow",
        "mood_modifier": "dramatic and weighty, iconic and mythic in scale, DC dark and operatic",
        "raw_hint": "DC dark and operatic, dramatic and weighty, iconic and mythic in scale",
        # TODO: 上架前手工 polish
    },

    "european_comic": {
        "primary_genre": "European / ligne-claire / refined adventure",
        "instruments": ["accordion", "piano", "strings", "light brass"],
        "tempo": "moderate",
        "mood_modifier": "refined adventure, Tintin-era discovery and wit, European elegance",
        "raw_hint": "European ligne-claire elegance, refined adventure, Tintin-era discovery and wit",
        # TODO: 上架前手工 polish
    },

    "indie_comic": {
        "primary_genre": "indie / experimental / voice-driven",
        "instruments": ["acoustic guitar", "piano", "found sounds", "minimal synth"],
        "tempo": "moderate",
        "mood_modifier": "intimate and experimental, voice-driven and personal, genre-bending",
        "raw_hint": "intimate and experimental, voice-driven and personal, genre-bending sonic identity",
        # TODO: 上架前手工 polish
    },

    # ---- 氛围/情绪 ----

    "dreamy_soft": {
        "primary_genre": "ethereal / ambient / dream pop",
        "instruments": ["ambient pads", "piano", "light strings", "chimes"],
        "tempo": "very slow",
        "mood_modifier": "luminous and weightless, pastel-warm and gently floating, ethereal",
        "raw_hint": "ethereal soft drift, luminous and weightless, pastel-warm and gently floating",
        # TODO: 上架前手工 polish
    },

    "bright_cheerful": {
        "primary_genre": "pop / orchestral / major key",
        "instruments": ["piano", "brass", "woodwinds", "drums"],
        "tempo": "upbeat",
        "mood_modifier": "sunny upbeat energy, joyful bounce, the world at its most generous",
        "raw_hint": "sunny upbeat energy, major key warmth, joyful bounce, the world at its most generous",
        # TODO: 上架前手工 polish
    },

    "mysterious": {
        "primary_genre": "dark ambient / tension / suspense",
        "instruments": ["strings", "piano", "bass clarinet", "subtle percussion"],
        "tempo": "slow",
        "mood_modifier": "shadowed and questioning, tension held in suspension, door not yet opened",
        "raw_hint": "shadowed and questioning, tension held in suspension, the sound of a door not yet opened",
        # TODO: 上架前手工 polish
    },

    "epic_cinematic": {
        "primary_genre": "epic orchestral / cinematic / grand scale",
        "instruments": ["full orchestra", "choir", "brass", "percussion"],
        "tempo": "moderate",
        "mood_modifier": "grand cinematic scale, the weight of consequence and size of sky",
        "raw_hint": "grand cinematic scale, sweeping orchestral, the weight of consequence and the size of sky",
        # TODO: 上架前手工 polish
    },

    "cozy_healing": {
        "primary_genre": "lo-fi / acoustic / healing",
        "instruments": ["piano", "acoustic guitar", "light strings", "rain sounds"],
        "tempo": "slow",
        "mood_modifier": "warm and unhurried, soft and restorative, no edges, heated room in winter",
        "raw_hint": "warm and unhurried, the sound of a heated room in winter, soft and restorative, no edges",
        # TODO: 上架前手工 polish
    },

    "horror": {
        "primary_genre": "horror score / dark ambient / tension",
        "instruments": ["strings", "bass", "processed noise", "piano"],
        "tempo": "very slow",
        "mood_modifier": "dread and unease, sounds that shouldn't exist in daylight, tension without resolution",
        "raw_hint": "dread and unease, tension without resolution, sounds that shouldn't exist in daylight",
        # TODO: 上架前手工 polish
    },

    "romantic": {
        "primary_genre": "romantic / intimate / warm",
        "instruments": ["piano", "strings", "acoustic guitar", "soft voice"],
        "tempo": "slow",
        "mood_modifier": "the space between two people, warm and soft with aching sweetness",
        "raw_hint": "intimate and longing, the space between two people, warm and soft with aching sweetness",
        # TODO: 上架前手工 polish
    },

    "nostalgic": {
        "primary_genre": "vintage / lo-fi / warm memory",
        "instruments": ["piano", "acoustic guitar", "vinyl crackle", "strings"],
        "tempo": "slow",
        "mood_modifier": "faded warmth, vintage grain, the ache of what was, memory given sonic texture",
        "raw_hint": "faded warmth, vintage grain, the ache of what was, memory given sonic texture",
        # TODO: 上架前手工 polish
    },

    # ---- 特定应用 ----

    "picture_book": {
        "primary_genre": "storybook / gentle / narrative warmth",
        "instruments": ["acoustic guitar", "piano", "glockenspiel"],
        "tempo": "slow",
        "mood_modifier": "storybook gentle, narrative warmth, each page-turn a breath, simple and inviting",
        "raw_hint": "storybook gentle, narrative warmth, each page-turn a breath, simple and inviting",
        # TODO: 上架前手工 polish
    },

    "concept_art": {
        "primary_genre": "world-building / atmospheric / production quality",
        "instruments": ["ambient pads", "strings", "percussion", "synth"],
        "tempo": "moderate",
        "mood_modifier": "world-building atmospheric, the hum of an imagined world",
        "raw_hint": "world-building atmospheric, production-quality soundscape, the hum of an imagined world",
        # TODO: 上架前手工 polish
    },

    "game_art": {
        "primary_genre": "game score / adventurous / stylized",
        "instruments": ["synth", "electric guitar", "orchestra", "drums"],
        "tempo": "upbeat",
        "mood_modifier": "game-world adventurous, stylized and interactive, genre-appropriate energy",
        "raw_hint": "game-world adventurous, stylized and interactive, genre-appropriate energy and pacing",
        # TODO: 上架前手工 polish
    },

    "movie_storyboard": {
        "primary_genre": "cinematic / pre-viz / dramatic",
        "instruments": ["orchestra", "piano", "strings", "brass"],
        "tempo": "moderate",
        "mood_modifier": "dramatic and scene-setting, the sound of a story about to happen",
        "raw_hint": "cinematic pre-viz, dramatic and scene-setting, the sound of a story about to happen",
        # TODO: 上架前手工 polish
    },

    "fashion_illustration": {
        "primary_genre": "editorial / chic / runway",
        "instruments": ["synth", "piano", "minimal percussion", "electronic"],
        "tempo": "moderate",
        "mood_modifier": "editorial chic, cool and stylized, runway tension and effortless attitude",
        "raw_hint": "editorial chic, cool and stylized, runway tension and effortless attitude",
        # TODO: 上架前手工 polish
    },

    "botanical": {
        "primary_genre": "naturalist / stillness / precise",
        "instruments": ["solo piano", "acoustic guitar", "light strings"],
        "tempo": "very slow",
        "mood_modifier": "the sound of careful observation, delicate and precise, nature's own patience",
        "raw_hint": "naturalist stillness, the sound of careful observation, delicate and precise, nature's own patience",
        # TODO: 上架前手工 polish
    },

    "architectural": {
        "primary_genre": "spatial / structural / resonant",
        "instruments": ["piano", "strings", "organ", "ambient"],
        "tempo": "slow",
        "mood_modifier": "spatial and structural, the resonance of designed space, form and proportion given sound",
        "raw_hint": "spatial and structural, the resonance of designed space, form and proportion given sound",
        # TODO: 上架前手工 polish
    },

    # ============================================================
    # 【C】特殊条目
    # ============================================================

    # 通用 fallback（未知 style_id 时使用）
    "__default__": {
        "primary_genre": "acoustic / ambient / versatile",
        "instruments": ["piano", "acoustic guitar", "strings"],
        "tempo": "moderate",
        "mood_modifier": "emotionally responsive and style-agnostic, match visual mood",
        "raw_hint": "acoustic versatile palette, match visual mood, emotionally responsive and style-agnostic",
    },

    # custom 风格（用户上传参考图生成）
    "custom": {
        "primary_genre": "acoustic / ambient / versatile",
        "instruments": ["piano", "acoustic guitar", "strings"],
        "tempo": "moderate",
        "mood_modifier": "emotionally responsive and style-agnostic, match visual mood",
        "raw_hint": "acoustic versatile palette, match visual mood, emotionally responsive and style-agnostic",
    },

    # oil_painting 别名（style_config 和 StyleEnforcer 均使用 oil_painting）
    "oil": {
        "primary_genre": "classical chamber / romantic / painterly",
        "instruments": ["strings", "piano", "cello"],
        "tempo": "slow",
        "mood_modifier": "Old World weight, classical gravity, rich painterly warmth",
        "raw_hint": "classical chamber gravity, strings and harpsichord or piano, Old World weight and emotional gravitas",
        # TODO: 统一到 oil_painting
    },
}


# ================================================================
# 公开接口
# ================================================================

def get_music_hint(style_id: str) -> dict:
    """
    返回完整 hint dict，未知 style_id 返回 __default__。

    示例:
        hint = get_music_hint("pencil_sketch")
        # {"primary_genre": ..., "instruments": [...], "tempo": ...,
        #  "mood_modifier": ..., "raw_hint": "intimate acoustic, bare and unhurried, ..."}
    """
    return STYLE_MUSIC_HINTS.get(style_id, STYLE_MUSIC_HINTS["__default__"])


def get_raw_hint(style_id: str) -> str:
    """
    快捷函数：返回 raw_hint 字符串，供 outline LLM 注入 music_hint 字段。

    Pipeline 用法（Backend Stage 1 后）:
        from app.services.style_music_hints import get_raw_hint
        outline["music_hint"] = get_raw_hint(visual_style_preset)

    story_music_extractor 用法:
        visual_style_hint = get_raw_hint(style_preset)
        story_data = extract_story_for_music(
            outline=outline,
            screenplay=screenplay,
            visual_style_hint=visual_style_hint,
        )
    """
    return get_music_hint(style_id).get("raw_hint", "ambient instrumental")
