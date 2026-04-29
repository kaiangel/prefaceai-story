"""
test_style_music_hints.py — BGM-1 style_music_hints 模块单元测试

覆盖：
  - 所有 28 上架风格的 dict 结构完整性
  - 所有 95 风格条目存在
  - get_music_hint() / get_raw_hint() 接口正确性
  - fallback 行为（未知 style_id 返回 __default__）
  - raw_hint ≤500 字符（V4 极简哲学宽松约束）

Note: 直接用 importlib 加载模块文件，绕过 app/services/__init__.py 的
      重量级依赖（google-genai / dotenv 等在测试环境可能未安装）。
"""

import importlib.util
import os
import sys
import pytest

# 直接加载 style_music_hints.py，不触发 app.services.__init__ 的级联导入
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
_MODULE_PATH = os.path.join(_PROJECT_ROOT, "app", "services", "style_music_hints.py")

_spec = importlib.util.spec_from_file_location("style_music_hints", _MODULE_PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

STYLE_MUSIC_HINTS = _mod.STYLE_MUSIC_HINTS
get_music_hint = _mod.get_music_hint
get_raw_hint = _mod.get_raw_hint

# ================================================================
# 28 个 StyleEnforcer 上架风格（高质量手工填充）
# ================================================================
ENFORCER_STYLES = [
    "realistic", "cartoon", "pixar_3d", "anime", "ghibli", "illustration",
    "watercolor", "children_book", "manga", "slam_dunk", "korean_webtoon",
    "oil_painting", "cyberpunk", "ink", "pixel", "ukiyo_e", "vintage_film",
    "pencil_sketch", "chibi", "dark_fantasy", "pop_art", "paper_cut",
    "steampunk", "art_nouveau", "noir", "comic_western", "pastel_dream", "gothic",
]

# 必需字段
REQUIRED_KEYS = {"primary_genre", "instruments", "tempo", "mood_modifier", "raw_hint"}

VALID_TEMPOS = {"very slow", "slow", "moderate", "upbeat", "fast"}


class TestDictStructure:
    """验证字典结构完整性"""

    def test_default_entry_exists(self):
        """__default__ fallback 条目必须存在"""
        assert "__default__" in STYLE_MUSIC_HINTS

    def test_custom_entry_exists(self):
        """custom 条目必须存在"""
        assert "custom" in STYLE_MUSIC_HINTS

    @pytest.mark.parametrize("style_id", ENFORCER_STYLES)
    def test_enforcer_styles_exist(self, style_id):
        """28 个上架风格必须全部在字典中"""
        assert style_id in STYLE_MUSIC_HINTS, f"缺少上架风格: {style_id}"

    @pytest.mark.parametrize("style_id", ENFORCER_STYLES)
    def test_enforcer_styles_have_required_keys(self, style_id):
        """上架风格的 dict 必须包含所有必需字段"""
        hint = STYLE_MUSIC_HINTS[style_id]
        for key in REQUIRED_KEYS:
            assert key in hint, f"{style_id} 缺少字段: {key}"

    @pytest.mark.parametrize("style_id", ENFORCER_STYLES)
    def test_enforcer_styles_instruments_is_list(self, style_id):
        """instruments 必须是列表"""
        hint = STYLE_MUSIC_HINTS[style_id]
        assert isinstance(hint["instruments"], list), f"{style_id}.instruments 不是列表"
        assert len(hint["instruments"]) >= 1, f"{style_id}.instruments 不能为空列表"

    @pytest.mark.parametrize("style_id", ENFORCER_STYLES)
    def test_enforcer_styles_tempo_valid(self, style_id):
        """tempo 必须是有效值之一"""
        hint = STYLE_MUSIC_HINTS[style_id]
        assert hint["tempo"] in VALID_TEMPOS, (
            f"{style_id}.tempo='{hint['tempo']}' 不在有效值集合 {VALID_TEMPOS} 中"
        )

    @pytest.mark.parametrize("style_id", ENFORCER_STYLES)
    def test_enforcer_styles_raw_hint_length(self, style_id):
        """raw_hint ≤500 字符（V4 极简哲学宽松约束）"""
        raw_hint = STYLE_MUSIC_HINTS[style_id]["raw_hint"]
        assert len(raw_hint) <= 500, (
            f"{style_id}.raw_hint 超出 500 字符限制: {len(raw_hint)} 字符"
        )

    @pytest.mark.parametrize("style_id", ENFORCER_STYLES)
    def test_enforcer_styles_raw_hint_is_english(self, style_id):
        """raw_hint 不应包含中文字符"""
        raw_hint = STYLE_MUSIC_HINTS[style_id]["raw_hint"]
        chinese_chars = [c for c in raw_hint if "一" <= c <= "鿿"]
        assert len(chinese_chars) == 0, (
            f"{style_id}.raw_hint 包含中文字符: {''.join(chinese_chars)}"
        )


class TestGetMusicHint:
    """验证 get_music_hint() 接口"""

    def test_known_style_returns_correct_dict(self):
        """已知风格返回对应 dict"""
        result = get_music_hint("pencil_sketch")
        assert result["tempo"] == "slow"
        assert "acoustic" in result["primary_genre"].lower()
        assert len(result["instruments"]) > 0

    def test_unknown_style_returns_default(self):
        """未知 style_id 返回 __default__"""
        result = get_music_hint("nonexistent_style_xyz")
        default = STYLE_MUSIC_HINTS["__default__"]
        assert result == default

    def test_cyberpunk_hint_has_electronic(self):
        """cyberpunk 的 raw_hint 应包含电子/合成音色关键词"""
        hint = get_music_hint("cyberpunk")
        raw = hint["raw_hint"].lower()
        assert any(kw in raw for kw in ["electronic", "synth", "neon"]), (
            f"cyberpunk raw_hint 缺少电子音色关键词: {hint['raw_hint']}"
        )

    def test_ink_hint_has_chinese_instrument_color(self):
        """ink 的 raw_hint 应包含中式乐器名（guqin/dizi/xiao/erhu）"""
        hint = get_music_hint("ink")
        raw = hint["raw_hint"].lower()
        chinese_instruments = ["guqin", "dizi", "xiao", "erhu", "pipa", "zheng"]
        assert any(inst in raw for inst in chinese_instruments), (
            f"ink raw_hint 缺少中式乐器色彩: {hint['raw_hint']}"
        )

    def test_paper_cut_hint_has_folk_energy(self):
        """paper_cut 应有民俗节庆感"""
        hint = get_music_hint("paper_cut")
        raw = hint["raw_hint"].lower()
        assert any(kw in raw for kw in ["folk", "festiv", "celebrat", "community"]), (
            f"paper_cut raw_hint 缺少民俗节庆关键词: {hint['raw_hint']}"
        )

    def test_ghibli_hint_slow_tempo(self):
        """ghibli 应该是 slow tempo"""
        hint = get_music_hint("ghibli")
        assert hint["tempo"] == "slow"

    def test_cartoon_hint_upbeat_tempo(self):
        """cartoon 应该是 upbeat tempo"""
        hint = get_music_hint("cartoon")
        assert hint["tempo"] == "upbeat"

    def test_pencil_sketch_for_bgm1_scenario(self):
        """BGM-1 具体场景：铅笔素描风格 — 应有 acoustic quietness 而非 acoustic guitar cheerful"""
        hint = get_music_hint("pencil_sketch")
        raw = hint["raw_hint"].lower()
        # 应有安静/内敛特质
        assert any(kw in raw for kw in ["quiet", "bare", "intimate", "unhurried", "space"]), (
            f"pencil_sketch raw_hint 缺少安静/内敛关键词: {hint['raw_hint']}"
        )

    def test_korean_webtoon_has_kdrama_feel(self):
        """korean_webtoon 应有 K-drama 情绪氛围"""
        hint = get_music_hint("korean_webtoon")
        raw = hint["raw_hint"].lower()
        assert "k-drama" in raw or "restraint" in raw or "ache" in raw, (
            f"korean_webtoon raw_hint 缺少 K-drama 氛围: {hint['raw_hint']}"
        )

    def test_noir_has_jazz_color(self):
        """noir 应有爵士色彩"""
        hint = get_music_hint("noir")
        raw = hint["raw_hint"].lower()
        assert "jazz" in raw or "saxophone" in raw or "trumpet" in raw, (
            f"noir raw_hint 缺少爵士色彩: {hint['raw_hint']}"
        )

    def test_vintage_film_has_analog_warmth(self):
        """vintage_film 应有模拟温暖感"""
        hint = get_music_hint("vintage_film")
        raw = hint["raw_hint"].lower()
        assert "analog" in raw or "lo-fi" in raw or "vinyl" in raw or "grain" in raw, (
            f"vintage_film raw_hint 缺少模拟温暖感: {hint['raw_hint']}"
        )


class TestGetRawHint:
    """验证 get_raw_hint() 快捷接口"""

    def test_known_style_returns_string(self):
        """已知风格返回字符串"""
        result = get_raw_hint("realistic")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_unknown_style_returns_fallback_string(self):
        """未知风格返回 fallback 字符串（不抛异常）"""
        result = get_raw_hint("totally_unknown_style_abc")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_raw_hint_matches_dict_entry(self):
        """get_raw_hint 返回值与 dict 中的 raw_hint 字段一致"""
        for style_id in ["watercolor", "slam_dunk", "cyberpunk"]:
            expected = STYLE_MUSIC_HINTS[style_id]["raw_hint"]
            assert get_raw_hint(style_id) == expected, (
                f"{style_id}: get_raw_hint() 返回值与 dict 不一致"
            )

    def test_pipeline_usage_pattern(self):
        """模拟 Pipeline 用法：Backend Stage 1 后查表填 outline.music_hint"""
        visual_style_preset = "pencil_sketch"
        music_hint = get_raw_hint(visual_style_preset)
        # 模拟写入 outline
        outline = {"title": "豫北悲伤民俗故事", "music_hint": music_hint}
        assert outline["music_hint"] == music_hint
        assert "acoustic" in music_hint.lower() or "intimate" in music_hint.lower()


class TestCoverage:
    """验证覆盖范围"""

    def test_total_style_count_at_least_95(self):
        """字典至少覆盖 95 个用户可选风格（不含 __default__ 和 custom）"""
        user_facing = {
            k for k in STYLE_MUSIC_HINTS
            if not k.startswith("__") and k != "custom"
        }
        assert len(user_facing) >= 95, (
            f"字典只有 {len(user_facing)} 个用户可选风格，需要 ≥ 95"
        )

    def test_all_style_config_styles_covered(self):
        """style_config.py 中的所有风格都应在字典中"""
        # 直接加载 style_config.py 文件，绕过 app.models.__init__ 级联导入
        _style_config_path = os.path.join(_PROJECT_ROOT, "app", "models", "style_config.py")
        _sc_spec = importlib.util.spec_from_file_location("style_config", _style_config_path)
        _sc_mod = importlib.util.module_from_spec(_sc_spec)
        _sc_spec.loader.exec_module(_sc_mod)
        builder = _sc_mod.StyleConfigBuilder()
        all_styles = builder.get_all_styles()
        missing = [s for s in all_styles if s not in STYLE_MUSIC_HINTS]
        assert len(missing) == 0, f"以下风格在字典中缺失: {missing}"
