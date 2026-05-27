"""
bgm_signal_probe.py — #8 BGM 路径B dry-run 验证 harness (2026-05-27)

目的: 不真生 audio, 只打印多组 {type × style × mood} 的 BGM universal 信号
      (setting_period / chinese_cultural / style_category / character_dominant_type)
      + 调 _fill_placeholders 看最终喂给 Haiku 的关键占位符是否合理。

运行: venv/bin/python3 scripts/bgm_signal_probe.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.story_music_extractor import (
    extract_story_for_music,
    _derive_setting_period,
    _detect_chinese_cultural,
    _derive_style_category,
    _derive_character_dominant_type,
)


def _outline(title, summary, chars, locs=None, mood="", plot=None):
    return {
        "title": title,
        "summary": summary,
        "logline": summary,
        "user_selected_mood": mood,
        "emotional_arc": {"opening": "calm", "midpoint": "tension", "climax": "peak", "resolution": "release"},
        "narrative_pace": "moderate",
        "visual_tone": {"overall_mood": mood or "warm", "color_palette": ["soft", "muted"]},
        "plot_points": plot or [{"beat": "inciting_incident", "description": summary}],
        "characters_overview": chars,
        "unique_locations": locs or [],
    }


def _screenplay():
    return {"scenes": [{
        "scene_id": 1, "plot_point": "inciting_incident",
        "atmosphere": {"mood": "tranquil", "sound_design_hint": "water ripple", "temperature_feel": "cool"},
        "narration_tone": "gentle", "narration_pace": "slow",
        "narration": "荷塘静默，锦鲤吐出最后一串气泡。",
    }]}


CASES = [
    # name, outline, style_preset
    (
        "① 中式非人类(荷塘渡): 锦鲤+菖蒲, watercolor, 无朝代词",
        _outline(
            "荷塘渡",
            "暴雨夜冲垮荷塘一角，年迈的红锦鲤金爷被困泥洼，一株菖蒲把根须探来，把水汽一点点渡给它。雨季重临荷塘蓄满那天，金爷衔来一粒莲子埋在菖蒲根旁。",
            [
                {"name_suggestion": "金爷", "character_type": "aquatic", "description": "年迈的红锦鲤，鳞片渐失光泽"},
                {"name_suggestion": "小蒲", "character_type": "plant", "description": "最不起眼的菖蒲，叶尖青绿"},
            ],
            locs=[{
                "display_name": "残破荷塘", "location_type": "exterior",
                "description_zh": "暴雨后的荷塘，残荷低垂，泥洼里映着灰白天光",
                "key_visual_elements": ["wilting lotus leaves", "muddy puddle", "koi fish", "reed"],
            }],
            mood="感人",
        ),
        "watercolor",
    ),
    (
        "② 西式人类: 现代都市爱情, realistic, 浪漫",
        _outline(
            "雨夜咖啡馆",
            "A young architect meets a violinist in a Manhattan coffee shop during a rainstorm; they fall in love over one evening.",
            [
                {"name_suggestion": "Emma", "character_type": "human", "description": "28岁建筑师，金发"},
                {"name_suggestion": "Liam", "character_type": "human", "description": "30岁小提琴手"},
            ],
            locs=[{"display_name": "Manhattan cafe", "location_type": "interior",
                   "description_zh": "曼哈顿街角咖啡馆，落地窗外霓虹与雨",
                   "key_visual_elements": ["espresso machine", "rain on window", "neon street"]}],
            mood="浪漫",
        ),
        "oil_painting",
    ),
    (
        "③ 现代中国都市: 外卖小哥, manhwa, 热血",
        _outline(
            "深夜骑手",
            "上海暴雨夜，外卖骑手为赶最后一单冲过积水的街道，地铁口、便利店的灯一盏盏亮着。",
            [{"name_suggestion": "阿强", "character_type": "human", "description": "外卖骑手，黝黑结实"}],
            locs=[{"display_name": "上海街头", "location_type": "exterior",
                   "description_zh": "上海暴雨夜的街道，霓虹倒映在积水里",
                   "key_visual_elements": ["delivery scooter", "wet asphalt", "subway entrance", "convenience store"]}],
            mood="热血",
        ),
        "manhwa",
    ),
    (
        "④ 古风武侠人类: 客栈刺客, ink_wash, 紧张",
        _outline(
            "夜雨客栈",
            "唐朝末年，一名独行剑客夜宿江湖客栈，发现镖局暗藏的杀机，刀光剑影一触即发。",
            [{"name_suggestion": "无名", "character_type": "human", "description": "独行剑客，长袍束发"}],
            locs=[{"display_name": "江湖客栈", "location_type": "interior",
                   "description_zh": "唐末江湖客栈，飞檐斗拱，烛火摇曳",
                   "key_visual_elements": ["wooden inn", "sword", "lantern", "rain"]}],
            mood="紧张",
        ),
        "ink_wash",
    ),
    (
        "⑤ 机器人: 末日机械, cyberpunk, 悬疑",
        _outline(
            "锈蚀纪元",
            "In a post-apocalyptic neon city, a lone android searches the ruins for its lost memory core.",
            [{"name_suggestion": "Unit-7", "character_type": "robot", "description": "孤独的仿生机器人"}],
            locs=[{"display_name": "霓虹废墟", "location_type": "exterior",
                   "description_zh": "赛博废墟，全息广告残影闪烁",
                   "key_visual_elements": ["neon ruins", "hologram", "rusted android"]}],
            mood="悬疑",
        ),
        "cyberpunk",
    ),
    (
        "⑥ 奇幻儿童动物: 森林小狐狸, ghibli, 治愈",
        _outline(
            "森林的礼物",
            "A little fox in an enchanted forest helps lost woodland creatures find their way home.",
            [
                {"name_suggestion": "小狐", "character_type": "animal", "description": "橘红色小狐狸"},
                {"name_suggestion": "灰兔", "character_type": "animal", "description": "灰色长耳兔"},
            ],
            locs=[{"display_name": "魔法森林", "location_type": "exterior",
                   "description_zh": "魔法森林，蘑菇与萤火",
                   "key_visual_elements": ["enchanted forest", "mushrooms", "fireflies"]}],
            mood="治愈",
        ),
        "ghibli",
    ),
    (
        "⑦ 边界: 中式概念+物件(会说话的灯笼), watercolor, 温馨 — 验非人类不默认human + 文化触发",
        _outline(
            "灯笼引路",
            "中秋夜，一盏老灯笼记得每一个曾经提着它走夜路的人，今晚它要为迷路的孩子照亮回家的青石板路。",
            [{"name_suggestion": "老灯笼", "character_type": "object", "description": "百年红灯笼，灯面绘着莲花"}],
            locs=[{"display_name": "青石板巷", "location_type": "exterior",
                   "description_zh": "中秋夜的古巷，青瓦白墙，石桥流水",
                   "key_visual_elements": ["paper lantern", "stone path", "moon"]}],
            mood="温馨",
        ),
        "watercolor",
    ),
]


def run():
    sp = _screenplay()
    for name, outline, style_preset in CASES:
        print("\n" + "=" * 78)
        print(name)
        print("=" * 78)
        setting = _derive_setting_period(outline)
        cultural = _detect_chinese_cultural(outline)
        cat = _derive_style_category(style_preset, setting, cultural)
        cdt = _derive_character_dominant_type(
            outline.get("characters_overview", [])
        )
        print(f"  style_preset           = {style_preset!r}")
        print(f"  setting_period         = {setting!r}")
        print(f"  chinese_cultural       = {cultural!r}")
        print(f"  → style_category       = {cat!r}   ← BGM 选乐器/调式的主轴")
        print(f"  character_dominant_type= {cdt!r}   (弱信号; meta-prompt 仅 robot 轻度电子化)")

        data = extract_story_for_music(
            outline=outline, screenplay=sp,
            visual_style_hint="", style_preset=style_preset,
            user_selected_mood=outline.get("user_selected_mood") or None,
        )
        print(f"  overall_mood(用户选)   = {data['overall_mood']!r}   ← BGM mood 桶主轴")
        # 关键断言摘要
        assert data["style_category"] == cat
        assert data["character_dominant_type"] == cdt


if __name__ == "__main__":
    run()
    print("\n[probe 完成]")
