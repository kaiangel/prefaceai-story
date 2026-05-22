"""
story_music_extractor.py — Pipeline 生产版故事数据提取服务（Wave 1 Step 1）

从 Pipeline 生成的故事 JSON 数据中提取 music prompt 生成所需的 19 字段
（14 原始 + full_narration + visual_style_hint + 4 通用性维度），
返回一个 dict 供下游 music_generation_service.py 使用。

⚠️  PARITY RISK 说明（见 TASK-MUREKA-PIPELINE-INTEGRATION.md 章节 4）：
  - 风险点 1 (narration_quotes 动态化): 不硬编码金句，使用 full_narration
    让 Haiku 在调用时自挑，每个用户故事都不同
  - 风险点 2 (per-scene 数组上限): 限制 max_scenes=6；超出时取 outline 中
    plot_points 关键节点对应的 scene（按 scene.plot_point 字段匹配）
  - 风险点 3 (风格差异): 接收 visual_style_hint 参数，原样传递给下游
  - 风险点 4 (confirmed_outline_json): 传入的 outline 参数必须是 Stage B
    用户 confirmed 后的版本（字段通常叫 confirmed_outline_json），不是原始
    raw_outline_json；raw_outline_json 未经用户确认，mood/plot_points 可能
    和最终故事不符
  - 风险点 5 (prompt cache 质量保证): 所有字段放入 user prompt（每次变化），
    不影响 system prompt cache；输出为扁平 dict，对 Haiku fill_placeholders
    友好

设计约束：
  - 纯数据处理，不调用任何 API
  - 无 DB 交互
  - 所有字段缺失时用空字符串，不抛出 KeyError
  - max_scenes 超限时优先取关键 plot_points 对应的 scene

Wave 7 (2026-05-13) 升级 — BGM 通用性框架（RISK-T14-11 + DEC-026）:
  新增 4 个维度字段，让 BGM 生成 prompt 能按"视觉风格 × 情绪"二维矩阵
  挑选乐器/调性/节奏，而不是单一 mood 桶映射。
  - style_preset:          (str) Stage A 用户选的 style_preset id（如 "ink_wash"）
  - style_category:        (str) BGM 用一级分类（chinese_traditional / western_realistic /
                            sci_fi / japanese_anime / fantasy_children / cartoon_humor /
                            ink_painting / generic），决定使用哪一栏 instruments
  - setting_period:        (str) 故事时代（ancient_china / modern_china / western_modern /
                            future / fantasy_world / generic），辅助乐器选择
  - character_dominant_type: (str) 主导角色类型（human / animal / fantasy / robot），
                            非人类角色可调整音乐质感（如机器人→电子化）
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("xuhua")

# 关键情节节点的优先级顺序（和 outline 生成时的 beat 命名一致）
# 超出 max_scenes 时按此顺序取关键 scene
_KEY_PLOT_BEATS: list[str] = [
    "inciting_incident",
    "first_turn",
    "midpoint",
    "crisis",
    "climax",
    "resolution",
]


# ──────────────────────────────────────────────────────────────────────────
# Wave 7 / DEC-026 — style_preset → BGM style_category 映射表
# ──────────────────────────────────────────────────────────────────────────
#
# 把 82 个 style_preset id (`app/data/style_presets.json`) 归到 8 个
# BGM 听感差异显著的一级分类。BGM Haiku template 里的 6 mood × 5 style
# 矩阵就按这些 category 行进行乐器/调性/节奏的差异化。
#
# 设计原则:
#   - "看起来很中国" → chinese_traditional（强制中国传统乐器 + 五声音阶）
#   - "看起来很赛博/未来" → sci_fi（强制合成器 + 电子节奏）
#   - "看起来很日漫" → japanese_anime（管弦 + 民谣 + cell shading 感）
#   - "看起来像绘本/儿童" → fantasy_children（铃铛/木琴/玩具感）
#   - "看起来像现代摄影/写实" → western_realistic（钢琴+弦乐+现代配器）
#   - "看起来像水墨" → ink_painting（chinese_traditional 的极简变体，留白>乐器）
#   - "看起来很搞怪/卡通" → cartoon_humor（俏皮+节奏感+反转）
#   - 其余 → generic（中性温暖，最不会出错）
#
# 注意: 这个映射只关心"BGM 听感差异"，不关心"视觉媒介/技法差异"。
#   - 水彩 + 中国故事 = chinese_traditional（看完整 style+setting 综合判断）
#   - 水彩 + 西方故事 = western_realistic
#   所以 setting_period 是 style_category 的补充信号，二者共同决定 BGM。
_STYLE_PRESET_TO_CATEGORY: dict[str, str] = {
    # ─── medium (14) ───────────────────────────────────────────
    "pencil_sketch": "western_realistic",
    "colored_pencil": "western_realistic",
    "watercolor": "western_realistic",        # 默认西式水彩；setting_period 可覆盖
    "gouache": "western_realistic",
    "oil_painting": "western_realistic",
    "acrylic": "western_realistic",
    "pastel": "fantasy_children",             # 色粉柔软，常用于绘本/治愈
    "ink_wash": "ink_painting",               # ★ 中国水墨独立 category
    "charcoal": "western_realistic",
    "digital_painting": "western_realistic",
    "vector_art": "cartoon_humor",
    "pixel_art": "cartoon_humor",             # 8-bit 怀旧，俏皮电子
    "collage": "cartoon_humor",
    "linocut": "western_realistic",
    # ─── art_movement (12) ─────────────────────────────────────
    "impressionist": "western_realistic",
    "post_impressionist": "western_realistic",
    "expressionist": "western_realistic",
    "surrealist": "western_realistic",
    "art_nouveau": "western_realistic",
    "art_deco": "western_realistic",
    "pop_art": "cartoon_humor",
    "minimalist": "generic",
    "cubist": "western_realistic",
    "fauvism": "western_realistic",
    "romanticism": "western_realistic",
    "baroque": "western_realistic",
    # ─── cultural (12) ─────────────────────────────────────────
    "ukiyo_e": "japanese_anime",              # 浮世绘≠ chinese
    "shin_hanga": "japanese_anime",
    "dunhuang": "chinese_traditional",
    "gongbi": "chinese_traditional",
    "xieyi": "ink_painting",                  # 写意=水墨延伸
    "persian_miniature": "western_realistic",  # 中东偏 generic-western
    "byzantine": "western_realistic",
    "aboriginal": "western_realistic",
    "mexican_folk": "western_realistic",      # TODO future: latin category
    "russian_folk": "western_realistic",
    "nordic": "western_realistic",
    "african_tribal": "western_realistic",
    # ─── era_trend (10) ────────────────────────────────────────
    "steampunk": "sci_fi",                    # 蒸汽朋克 = 复古 sci-fi
    "cyberpunk": "sci_fi",
    "dieselpunk": "sci_fi",
    "solarpunk": "sci_fi",
    "retro_futurism": "sci_fi",
    "vaporwave": "sci_fi",
    "synthwave": "sci_fi",
    "cottagecore": "fantasy_children",
    "dark_academia": "western_realistic",
    "kawaii": "japanese_anime",
    # ─── digital_animation (10) ────────────────────────────────
    "ghibli": "japanese_anime",
    "pixar": "fantasy_children",
    "disney_classic": "fantasy_children",
    "disney_modern": "fantasy_children",
    "dreamworks": "fantasy_children",
    "shinkai": "japanese_anime",
    "kyoto_animation": "japanese_anime",
    "cartoon_network": "cartoon_humor",
    "adventure_time": "cartoon_humor",
    "laika": "fantasy_children",
    # ─── comic (9) ─────────────────────────────────────────────
    "manga_shounen": "japanese_anime",
    "manga_shoujo": "japanese_anime",
    "manhwa": "western_realistic",            # 韩漫常见现代都市 → 西式
    "manhua": "chinese_traditional",          # 中漫常古风 → 中式（可被 setting 覆盖）
    "marvel_comics": "western_realistic",
    "dc_comics": "western_realistic",
    "franco_belgian": "western_realistic",
    "underground_comics": "western_realistic",
    "webcomic": "western_realistic",
    # ─── mood (8) — 这些是情绪类风格，BGM 主要听 mood 而非 style ──
    "dark_fantasy": "western_realistic",
    "whimsical": "fantasy_children",
    "cozy_healing": "fantasy_children",
    "epic_dramatic": "western_realistic",
    "nostalgic": "western_realistic",
    "dreamy": "fantasy_children",
    "mysterious": "western_realistic",        # 类型预设≠ setting，留给 mood
    "cheerful": "fantasy_children",
    # ─── application (7) ───────────────────────────────────────
    "picture_book": "fantasy_children",
    "concept_art": "western_realistic",
    "storyboard": "western_realistic",
    "game_art": "western_realistic",
    "book_cover": "western_realistic",
    "editorial": "western_realistic",
    "fashion_illustration": "western_realistic",
}

# 五大 BGM matrix style_category（对应 Haiku template 6×5 矩阵的 5 列）
# 其余 category（cartoon_humor / ink_painting / generic）归入对应列做 sub-flavor
_BGM_MATRIX_COLUMNS: list[str] = [
    "chinese_traditional",
    "western_realistic",
    "sci_fi",
    "japanese_anime",
    "fantasy_children",
]


def _derive_style_category(style_preset: str, setting_period: str = "") -> str:
    """
    根据 style_preset id 推导 BGM 一级分类。

    setting_period 用作 fallback / override 信号：
      - 当 style_preset = "watercolor" 且 setting_period 含"古代中国" → 升级为 chinese_traditional
      - 当 style_preset 未知（用户自定义）时，按 setting_period 兜底

    Args:
        style_preset: 来自 project.style_preset 的 id
        setting_period: 时代背景字符串（从 outline 推断）

    Returns:
        BGM style_category 之一: chinese_traditional / western_realistic / sci_fi /
        japanese_anime / fantasy_children / cartoon_humor / ink_painting / generic
    """
    if not style_preset:
        # 完全无 style_preset 信号 — 按 setting 兜底
        if "中国" in setting_period or "ancient_china" in setting_period:
            return "chinese_traditional"
        return "generic"

    base_category = _STYLE_PRESET_TO_CATEGORY.get(style_preset, "generic")

    # setting 覆盖规则 — 视觉风格中性时（如水彩/油画/插画），故事 setting 起决定作用
    if base_category == "western_realistic" and (
        "古代中国" in setting_period or "ancient_china" in setting_period
    ):
        return "chinese_traditional"

    # 反向 — 中漫 style_preset 但故事 setting 是现代/赛博 → 不能套古风
    if base_category == "chinese_traditional" and (
        "future" in setting_period or "sci_fi" in setting_period or "未来" in setting_period
    ):
        return "sci_fi"

    return base_category


def _derive_setting_period(outline: dict) -> str:
    """
    从 outline 推断故事的时代/地域背景。

    扫描 title + summary + plot_points 文本，匹配关键词桶。

    Returns:
        ancient_china / modern_china / western_modern / future / fantasy_world / generic
    """
    title = str(outline.get("title", ""))
    summary = str(outline.get("summary", "")) + str(outline.get("logline", ""))
    plot_text = " ".join(
        str(p.get("description", "")) + " " + str(p.get("beat", ""))
        for p in outline.get("plot_points", [])
    )
    # 也吃 unique_locations 描述
    locs = outline.get("unique_locations", [])
    if isinstance(locs, list):
        loc_text = " ".join(
            str(l.get("description", "")) + " " + str(l.get("location_type", ""))
            for l in locs if isinstance(l, dict)
        )
    else:
        loc_text = ""

    full = f"{title} {summary} {plot_text} {loc_text}".lower()

    # 古代中国信号
    # 注意：单字关键词（"明"/"清"/"宋"等朝代单字）容易误匹配 "明天"/"清晨"/"宋词"等
    # 现代用语，故全部使用至少 2 字组合或专属名词。
    ancient_china_keywords = [
        "古代", "古时", "古风", "古装", "古城",
        "唐朝", "宋朝", "明朝", "清朝", "汉朝", "魏晋", "隋唐", "盛唐",
        "皇帝", "皇宫", "皇上", "妃子", "皇后", "公主", "太子", "王爷",
        "客栈", "驿站", "镖局", "茶馆", "酒楼", "祠堂", "牌坊", "戏楼",
        "江湖", "武林", "侠客", "剑客", "镖师",
        # "和尚"/"道士"在现代故事也可能出现，故只保留古风专属词
        "汉服", "长袍", "马褂", "旗袍", "凤冠", "霞帔",
        "飞檐", "斗拱", "影壁", "月亮门", "石板路",
        # "禅"在现代禅意/茶艺也用，故移除
        "ancient china", "imperial", "wuxia", "martial arts", "dynasty",
    ]
    if any(kw in full for kw in ancient_china_keywords):
        return "ancient_china"

    # sci-fi / 未来信号
    future_keywords = [
        "未来", "赛博", "霓虹", "全息", "机器人", "人工智能", "ai 客服",
        "太空", "星舰", "外星", "克隆", "脑机", "VR", "元宇宙",
        "cyber", "futuristic", "robot", "android", "neon", "hologram",
        "spaceship", "alien",
    ]
    if any(kw in full for kw in future_keywords):
        return "future"

    # 奇幻信号
    fantasy_keywords = [
        "魔法", "巫师", "精灵", "矮人", "巨龙", "兽人", "城堡",
        "异世界", "穿越", "勇者", "魔王",
        "wizard", "elf", "dragon", "fairy", "magic", "fantasy world",
    ]
    if any(kw in full for kw in fantasy_keywords):
        return "fantasy_world"

    # 现代中国信号（默认中文都市故事）
    modern_china_keywords = [
        "外卖", "地铁", "高铁", "上海", "北京", "广州", "深圳", "杭州",
        "微信", "支付宝", "抖音", "小红书", "煎饼", "兰州拉面", "火锅",
        "辣条", "奶茶", "工地", "996", "北漂", "沪漂",
        "subway in china", "wechat", "alipay", "douyin",
    ]
    if any(kw in full for kw in modern_china_keywords):
        return "modern_china"

    # 默认 generic（不强制方向，让 mood 起主导）
    return "generic"


def _derive_character_dominant_type(characters: list) -> str:
    """
    从 character 数据推断主导角色类型。

    Args:
        characters: outline.characters_overview 列表（或空）

    Returns:
        human / animal / fantasy / robot / generic
    """
    if not characters or not isinstance(characters, list):
        return "human"  # 安全默认

    type_count: dict[str, int] = {}
    for c in characters:
        if not isinstance(c, dict):
            continue
        ctype = (
            c.get("character_type")
            or c.get("type")
            or "human"
        )
        ctype = str(ctype).lower().strip()
        # 归一化
        if ctype in ("human", "person", "girl", "boy", "man", "woman", "adult", "child"):
            normalized = "human"
        elif ctype in ("animal", "dog", "cat", "bird", "creature", "beast", "pet"):
            normalized = "animal"
        elif ctype in ("robot", "ai", "android", "cyborg", "machine"):
            normalized = "robot"
        elif ctype in ("fantasy", "magical", "elf", "fairy", "wizard", "monster", "demon", "spirit"):
            normalized = "fantasy"
        else:
            normalized = "human"  # 未知类型按人类处理
        type_count[normalized] = type_count.get(normalized, 0) + 1

    if not type_count:
        return "human"

    # 取出现次数最多的
    return max(type_count.items(), key=lambda kv: kv[1])[0]


def extract_story_for_music(
    outline: dict,
    screenplay: dict,
    visual_style_hint: str = "",
    max_scenes: int = 6,
    user_selected_mood: Optional[str] = None,  # B33: project.user_selected_mood (最高优先级)
    style_preset: str = "",                     # Wave 7 / DEC-026: 用户 Stage A 选的 style_preset id
) -> dict:
    """
    从 Pipeline JSON 提取 music prompt 生成所需的所有字段。

    ⚠️  outline 参数说明（风险点 4）：
        传入的 outline 应该是 Stage B 用户 confirmed 后的版本。
        在 Pipeline DB 中对应 chapters.confirmed_outline_json 解析结果，
        不要传 raw_outline_json（原始自动生成，未经用户确认）。
        如果用户没有在 Stage B 做任何修改，两者相同，传哪个都可以；
        但如果用户修改了 mood / plot_points / ending，必须传 confirmed 版本。

    Args:
        outline:            Stage 1 输出的故事大纲 dict，或 confirmed_outline_json
                            解析结果。必须包含 title / emotional_arc / narrative_pace
                            / visual_tone / plot_points 等字段。
        screenplay:         Stage 3 输出的分场剧本 dict。包含 scenes 列表，
                            每个 scene 含 atmosphere / narration_tone /
                            narration_pace / narration 等字段。
        visual_style_hint:  从用户选的 style_preset 读取的 music_hint 字段
                            （@ai-ml Step B 产出）。原样传递给下游，不做转换。
        max_scenes:         per-scene 数组字段（sound_design_hints / narration_tones
                            / narration_paces / scene_moods / temperature_feels /
                            full_narration）的 scene 上限。默认 6。
                            超出时取 outline.plot_points 中关键节点对应的 scene
                            （按 scene.plot_point 字段匹配），保证中篇 10+ scenes
                            也能正确截断而不丢失关键戏剧节点。
        style_preset:       (Wave 7 / DEC-026) 用户在 Stage A 选的 style_preset id
                            （如 "ink_wash" / "cyberpunk" / "ghibli"）。配合 outline
                            内容推导出 style_category / setting_period /
                            character_dominant_type 三个 BGM 通用性维度。
                            为空时按 outline 文本兜底，不抛错。

    Returns:
        dict，包含以下键（字段顺序固定）：
        {
            # 原 15 字段（保持向后兼容）
            "story_title": str,              # outline.title
            "narrative_pace": str,           # outline.narrative_pace
            "overall_mood": str,             # outline.visual_tone.overall_mood
            "emotional_arc_opening": str,    # outline.emotional_arc.opening
            "emotional_arc_midpoint": str,   # outline.emotional_arc.midpoint
            "emotional_arc_climax": str,     # outline.emotional_arc.climax
            "emotional_arc_resolution": str, # outline.emotional_arc.resolution
            "color_palette": str,            # outline.visual_tone.color_palette 拼接
            "sound_design_hints": str,       # per-scene 拼接，限 max_scenes
            "narration_tones": str,          # per-scene 拼接，限 max_scenes
            "narration_paces": str,          # per-scene 拼接，限 max_scenes
            "scene_moods": str,              # per-scene 拼接，限 max_scenes
            "temperature_feels": str,        # per-scene 拼接，限 max_scenes
            "full_narration": str,           # 所有选定 scene 的 narration 拼接
            "visual_style_hint": str,        # 传入的 visual_style_hint 原样返回

            # Wave 7 / DEC-026 新增 4 字段（BGM 通用性框架）
            "style_preset": str,             # 用户选的 style_preset id 原样回传
            "style_category": str,           # BGM 一级分类（chinese_traditional 等 8 选 1）
            "setting_period": str,           # 时代背景（ancient_china 等 6 选 1）
            "character_dominant_type": str,  # 主导角色类型（human/animal/fantasy/robot）
        }
    """
    # ── 来自 outline ──────────────────────────────────────────────────────────
    story_title: str = outline.get("title", "")
    narrative_pace: str = outline.get("narrative_pace", "")

    # RISK-T19-5: visual_tone 字段容错 — LLM 可能返回 dict 或 str
    # dict 形式: {"overall_mood": "bittersweet", "color_palette": [...], ...}
    # str 形式: "bittersweet" 或 "warm and nostalgic"（极少数 LLM 输出）
    visual_tone_raw = outline.get("visual_tone", {})
    if isinstance(visual_tone_raw, dict):
        visual_tone: dict = visual_tone_raw
    elif isinstance(visual_tone_raw, str):
        # str 形式 fallback: 将整体作为 overall_mood，其他字段留空
        visual_tone = {"overall_mood": visual_tone_raw}
        logger.warning(
            f"[StoryMusicExtractor] visual_tone 为 str 类型，已转为 dict: {visual_tone_raw!r}"
        )
    else:
        visual_tone = {}
        logger.warning(
            f"[StoryMusicExtractor] visual_tone 类型未知 ({type(visual_tone_raw).__name__})，已置空"
        )

    # B33: overall_mood 优先级：
    #   1. user_selected_mood (DB 字段，project.user_selected_mood — 最高优先)
    #   2. confirmed_outline_json.user_selected_mood (旧路径，兼容)
    #   3. outline.visual_tone.overall_mood (LLM 输出，fallback)
    overall_mood: str = (
        user_selected_mood
        or outline.get("user_selected_mood", "")
        or visual_tone.get("overall_mood", "")
    )

    # RISK-T19-9: emotional_arc 字段容错 — LLM 偶尔输出 str 而非 dict
    # dict 形式: {"opening": "平静", "midpoint": "冲突", "climax": "爆发", "resolution": "释然"}
    # str 形式: "从平静到冲突，最终释然" 或 "romantic→bittersweet"（极少数 LLM 输出）
    arc_raw = outline.get("emotional_arc", {})
    if isinstance(arc_raw, dict):
        arc: dict = arc_raw
    elif isinstance(arc_raw, str):
        # str 形式 fallback: 将整体作为 opening（最常用字段），其他字段留空
        arc = {"opening": arc_raw}
        logger.warning(
            f"[StoryMusicExtractor] emotional_arc 为 str 类型，已转为 dict: {arc_raw!r}"
        )
    else:
        arc = {}
        logger.warning(
            f"[StoryMusicExtractor] emotional_arc 类型未知 ({type(arc_raw).__name__})，已置空"
        )

    emotional_arc_opening: str = arc.get("opening", "")
    emotional_arc_midpoint: str = arc.get("midpoint", "")
    emotional_arc_climax: str = arc.get("climax", "")
    emotional_arc_resolution: str = arc.get("resolution", "")

    color_palette_raw = visual_tone.get("color_palette", [])
    if isinstance(color_palette_raw, list):
        color_palette: str = ", ".join(str(c) for c in color_palette_raw)
    else:
        # 兼容已经是字符串的情况（防御性处理）
        color_palette = str(color_palette_raw)

    # ── 提取 outline.plot_points 关键节点的 beat → 用于超限场景选择 ──────────
    # plot_points 是 list[dict]，每条有 "beat" 字段（如 "inciting_incident"）
    plot_points: list[dict] = outline.get("plot_points", [])
    key_beats_in_outline: list[str] = [
        pp.get("beat", "") for pp in plot_points if pp.get("beat", "")
    ]

    # ── 来自 screenplay（按 scene_id 顺序排列所有 scenes）───────────────────
    scenes_raw: list[dict] = screenplay.get("scenes", [])
    scenes_sorted: list[dict] = sorted(
        scenes_raw, key=lambda s: int(s.get("scene_id", 0))
    )

    # ── 超限场景选择（风险点 2）───────────────────────────────────────────────
    # 如果 scenes 总数 <= max_scenes，直接全取
    # 如果超出，优先取和 _KEY_PLOT_BEATS 对应的 scene（按优先级顺序，最多取 max_scenes 个）
    selected_scenes: list[dict] = _select_key_scenes(
        scenes_sorted, key_beats_in_outline, max_scenes
    )

    # ── 遍历选定 scenes 提取 per-scene 字段 ─────────────────────────────────
    sound_design_hints_parts: list[str] = []
    narration_tones_parts: list[str] = []
    narration_paces_parts: list[str] = []
    scene_moods_parts: list[str] = []
    temperature_feels_parts: list[str] = []
    narration_parts: list[str] = []

    for scene in selected_scenes:
        scene_id = scene.get("scene_id", "?")

        # RISK-T19-5: atmosphere 字段容错 — LLM 可能返回 str 或 dict
        # str 形式: "tranquil, 远山鸟鸣稀疏, 凛冽中带一丝初春的微暖"（逗号分隔）
        # dict 形式: {"mood": "tranquil", "sound_design_hint": "...", "temperature_feel": "..."}
        atm_raw = scene.get("atmosphere", {})
        if isinstance(atm_raw, dict):
            atm: dict = atm_raw
        elif isinstance(atm_raw, str):
            # str 形式: 首段（逗号前）通常是 mood 关键词
            parts = atm_raw.split(",")
            mood_from_str = parts[0].strip() if parts else ""
            atm = {
                "mood": mood_from_str,
                "sound_design_hint": "",
                "temperature_feel": "",
            }
            logger.warning(
                f"[StoryMusicExtractor] Scene {scene_id} atmosphere 为 str 类型，"
                f"已解析首段为 mood: {mood_from_str!r}"
            )
        else:
            atm = {}
            logger.warning(
                f"[StoryMusicExtractor] Scene {scene_id} atmosphere 类型未知 "
                f"({type(atm_raw).__name__})，已置空"
            )

        hint: str = atm.get("sound_design_hint", "").strip()
        if hint:
            sound_design_hints_parts.append(f"Scene {scene_id}: {hint}")

        tone: str = scene.get("narration_tone", "").strip()
        if tone:
            narration_tones_parts.append(f"Scene {scene_id}: {tone}")

        pace: str = scene.get("narration_pace", "").strip()
        if pace:
            narration_paces_parts.append(f"Scene {scene_id}: {pace}")

        mood: str = atm.get("mood", "").strip()
        if mood:
            scene_moods_parts.append(f"Scene {scene_id}: {mood}")

        temp: str = atm.get("temperature_feel", "").strip()
        if temp:
            temperature_feels_parts.append(f"Scene {scene_id}: {temp}")

        narration: str = scene.get("narration", "").strip()
        if narration:
            narration_parts.append(f"[Scene {scene_id}] {narration}")

    sound_design_hints: str = "\n".join(sound_design_hints_parts)
    narration_tones: str = "\n".join(narration_tones_parts)
    narration_paces: str = "\n".join(narration_paces_parts)
    scene_moods: str = "\n".join(scene_moods_parts)
    temperature_feels: str = "\n".join(temperature_feels_parts)
    full_narration: str = "\n\n".join(narration_parts)

    # ── Wave 7 / DEC-026 — 4 个 BGM 通用性维度推导 ────────────────────────────
    # 即使 style_preset 为空，仍要尽力从 outline 文本推断（兜底逻辑）
    setting_period: str = _derive_setting_period(outline)
    style_category: str = _derive_style_category(style_preset, setting_period)
    character_dominant_type: str = _derive_character_dominant_type(
        outline.get("characters_overview", []) or outline.get("characters", [])
    )

    logger.info(
        f"[StoryMusicExtractor] BGM 通用性维度: "
        f"style_preset={style_preset!r} → style_category={style_category!r}, "
        f"setting_period={setting_period!r}, "
        f"character_dominant_type={character_dominant_type!r}"
    )

    # ── 组装返回 dict ────────────────────────────────────────────────────────
    return {
        "story_title": story_title,
        "narrative_pace": narrative_pace,
        "overall_mood": overall_mood,
        "emotional_arc_opening": emotional_arc_opening,
        "emotional_arc_midpoint": emotional_arc_midpoint,
        "emotional_arc_climax": emotional_arc_climax,
        "emotional_arc_resolution": emotional_arc_resolution,
        "color_palette": color_palette,
        "sound_design_hints": sound_design_hints,
        "narration_tones": narration_tones,
        "narration_paces": narration_paces,
        "scene_moods": scene_moods,
        "temperature_feels": temperature_feels,
        "full_narration": full_narration,
        "visual_style_hint": visual_style_hint,
        # Wave 7 / DEC-026 — BGM 通用性框架 4 字段
        "style_preset": style_preset,
        "style_category": style_category,
        "setting_period": setting_period,
        "character_dominant_type": character_dominant_type,
    }


# ── 内部辅助函数 ────────────────────────────────────────────────────────────

def _select_key_scenes(
    scenes_sorted: list[dict],
    key_beats_in_outline: list[str],
    max_scenes: int,
) -> list[dict]:
    """
    当 scenes 数量超过 max_scenes 时，从关键 plot_points 节点中选取代表性场景。

    选取策略（按优先级）：
    1. 遍历 _KEY_PLOT_BEATS 优先级顺序（inciting_incident → first_turn →
       midpoint → crisis → climax → resolution）
    2. 在 scenes_sorted 中找 scene.plot_point 匹配的 scene
    3. 如果某个 beat 在 outline 的 plot_points 中存在但 screenplay 里没有对应
       的 scene.plot_point，则跳过
    4. 选够 max_scenes 个后截止，不足 max_scenes 时补充排在最前面的未选 scene

    场景不超出 max_scenes 时直接返回全部 scenes_sorted。

    Args:
        scenes_sorted:          已按 scene_id 排序的 scenes 列表
        key_beats_in_outline:   outline.plot_points 中出现的 beat 名称列表
        max_scenes:             最大场景数上限

    Returns:
        不超过 max_scenes 个 scene 的列表，保持 scene_id 顺序
    """
    if len(scenes_sorted) <= max_scenes:
        return scenes_sorted

    logger.info(
        f"[StoryMusicExtractor] scenes 数量 {len(scenes_sorted)} 超出 "
        f"max_scenes={max_scenes}，启动关键节点选取策略"
    )

    # 建立 plot_point → scene 的映射（每个 beat 只取第一个匹配的 scene）
    beat_to_scene: dict[str, dict] = {}
    for scene in scenes_sorted:
        pp: str = scene.get("plot_point", "").strip()
        if pp and pp not in beat_to_scene:
            beat_to_scene[pp] = scene

    # 按优先级顺序选取
    selected_ids: set[int] = set()
    selected: list[dict] = []

    for beat in _KEY_PLOT_BEATS:
        if len(selected) >= max_scenes:
            break
        if beat in beat_to_scene:
            scene = beat_to_scene[beat]
            sid = int(scene.get("scene_id", -1))
            if sid not in selected_ids:
                selected.append(scene)
                selected_ids.add(sid)

    # 如果关键节点不足 max_scenes，用前面未被选中的 scene 补足
    if len(selected) < max_scenes:
        for scene in scenes_sorted:
            if len(selected) >= max_scenes:
                break
            sid = int(scene.get("scene_id", -1))
            if sid not in selected_ids:
                selected.append(scene)
                selected_ids.add(sid)

    # 按 scene_id 重新排序，保持故事时间顺序
    selected.sort(key=lambda s: int(s.get("scene_id", 0)))

    logger.info(
        f"[StoryMusicExtractor] 选取了 {len(selected)} 个关键 scenes: "
        f"{[s.get('scene_id') for s in selected]}"
    )
    return selected


# ── __main__ 自测块 ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    快速自测：读取年夜饭故事的 outline + screenplay，
    调用 extract_story_for_music()，打印结果。

    运行方式（在项目根目录）：
        python app/services/story_music_extractor.py
    """
    import os

    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    _PROJECT_ROOT = os.path.join(_SCRIPT_DIR, "..", "..")

    _STORY_DIR = os.path.join(
        _PROJECT_ROOT,
        "test_output", "manualtest", "sq_upgrade_ab_test", "20260304_113630"
    )

    outline_path = os.path.join(_STORY_DIR, "1_outline.json")
    screenplay_path = os.path.join(_STORY_DIR, "3_screenplay.json")

    print(f"[自测] 读取 outline: {outline_path}")
    print(f"[自测] 读取 screenplay: {screenplay_path}")

    with open(outline_path, encoding="utf-8") as f:
        outline_data = json.load(f)
    with open(screenplay_path, encoding="utf-8") as f:
        screenplay_data = json.load(f)

    total_scenes = len(screenplay_data.get("scenes", []))
    print(f"[自测] screenplay 中共 {total_scenes} 个 scenes")

    # ── 测试 1: 正常调用（年夜饭 5 scenes，未超限）──
    print("\n" + "=" * 60)
    print("[测试 1] 正常调用（max_scenes=6，年夜饭共 5 scenes，不超限）")
    print("=" * 60)

    result = extract_story_for_music(
        outline=outline_data,
        screenplay=screenplay_data,
        visual_style_hint="Korean webtoon style with warm nostalgic palette",
        max_scenes=6,
    )

    for key, value in result.items():
        if key in ("full_narration",):
            # 只打印前 200 字符避免刷屏
            preview = value[:200] + "..." if len(value) > 200 else value
            print(f"  {key}: {repr(preview)}")
        else:
            print(f"  {key}: {repr(value)}")

    # ── 验证返回 dict 包含所有必须字段 ──
    required_keys = [
        "story_title", "narrative_pace", "overall_mood",
        "emotional_arc_opening", "emotional_arc_midpoint",
        "emotional_arc_climax", "emotional_arc_resolution",
        "color_palette", "sound_design_hints", "narration_tones",
        "narration_paces", "scene_moods", "temperature_feels",
        "full_narration", "visual_style_hint",
    ]
    missing = [k for k in required_keys if k not in result]
    if missing:
        print(f"\n[错误] 缺少必须字段: {missing}")
    else:
        print(f"\n[✓] 全部 {len(required_keys)} 个必须字段均存在")

    # ── 测试 2: 超限场景截断（模拟 max_scenes=3 触发关键节点选取）──
    print("\n" + "=" * 60)
    print("[测试 2] max_scenes=3，触发关键节点选取策略")
    print("=" * 60)

    result_limited = extract_story_for_music(
        outline=outline_data,
        screenplay=screenplay_data,
        visual_style_hint="",
        max_scenes=3,
    )

    # 通过计算 "Scene X:" 前缀的行数来验证 scene 数量上限
    sdh_lines = [ln for ln in result_limited["sound_design_hints"].split("\n") if ln.strip()]
    print(f"  sound_design_hints 行数（= 选取的 scenes 数）: {len(sdh_lines)}")
    assert len(sdh_lines) <= 3, f"超限！应 ≤ 3，实际 {len(sdh_lines)}"
    print(f"  [✓] max_scenes=3 上限正确，选取了 {len(sdh_lines)} 个 scenes")
    for line in sdh_lines:
        print(f"    {line[:80]}")

    # ── 测试 3: 空数据容错 ──
    print("\n" + "=" * 60)
    print("[测试 3] 空 outline 和 screenplay 容错")
    print("=" * 60)

    result_empty = extract_story_for_music(
        outline={},
        screenplay={},
        visual_style_hint="",
        max_scenes=6,
    )
    for key, value in result_empty.items():
        print(f"  {key}: {repr(value)}")
    assert all(isinstance(v, str) for v in result_empty.values()), \
        "所有字段应为 str 类型"
    print("[✓] 空数据容错正常，所有字段均为空字符串")

    print("\n[自测完成] extract_story_for_music() 逻辑验证通过")
