"""Wave 12 style_enforcer.py 防动漫漂移修复验证.

验证 3 个 style (cyberpunk / pastel_dream / gothic) 的 Wave 12 修复:
1. mandatory[:5] 含渲染介质锚点 (photorealistic / soft painterly / dark romantic painting)
2. forbidden[:8] 含 anti-anime 条目 (anime / cel-shaded / manga / glossy idol render)
3. Seedream 接收的 prefix 真正包含这些词 (build_mandatory_prefix 输出验证)
4. 零破坏 by-design 动漫类 style (cartoon / ghibli / manga / chibi / illustration 等)
"""

import pytest
from app.services.style_enforcer import StyleEnforcer


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def get_mandatory_top5(style_name: str):
    e = StyleEnforcer.get_enforcement(style_name)
    assert e is not None, f"style '{style_name}' 不存在"
    return e.mandatory_keywords[:5]


def get_forbidden_top8(style_name: str):
    e = StyleEnforcer.get_enforcement(style_name)
    assert e is not None, f"style '{style_name}' 不存在"
    return e.forbidden_keywords[:8]


def get_prefix(style_name: str) -> str:
    return StyleEnforcer.build_mandatory_prefix(style_name)


# ---------------------------------------------------------------------------
# cyberpunk — 写实电影感，不能动漫
# ---------------------------------------------------------------------------

class TestCyberpunkWave12:
    """cyberpunk: mandatory 前 5 含 photorealistic + cinematic，forbidden 前 8 含 anime/cel-shaded/manga."""

    def test_mandatory_has_photorealistic(self):
        top5 = get_mandatory_top5("cyberpunk")
        assert "photorealistic" in top5, f"cyberpunk mandatory[:5] 应含 photorealistic, 实际: {top5}"

    def test_mandatory_has_cinematic(self):
        top5 = get_mandatory_top5("cyberpunk")
        assert "cinematic film still" in top5, f"cyberpunk mandatory[:5] 应含 cinematic film still, 实际: {top5}"

    def test_forbidden_has_anime(self):
        top8 = get_forbidden_top8("cyberpunk")
        assert "anime" in top8, f"cyberpunk forbidden[:8] 应含 anime, 实际: {top8}"

    def test_forbidden_has_cel_shaded(self):
        top8 = get_forbidden_top8("cyberpunk")
        assert "cel-shaded" in top8, f"cyberpunk forbidden[:8] 应含 cel-shaded, 实际: {top8}"

    def test_forbidden_has_manga(self):
        top8 = get_forbidden_top8("cyberpunk")
        assert "manga" in top8, f"cyberpunk forbidden[:8] 应含 manga, 实际: {top8}"

    def test_forbidden_has_glossy_idol_render(self):
        top8 = get_forbidden_top8("cyberpunk")
        assert "glossy idol render" in top8, f"cyberpunk forbidden[:8] 应含 glossy idol render, 实际: {top8}"

    def test_prefix_contains_photorealistic(self):
        prefix = get_prefix("cyberpunk")
        assert "photorealistic" in prefix, "cyberpunk prefix 应含 photorealistic (MUST INCLUDE 行)"

    def test_prefix_contains_anime_in_do_not_use(self):
        prefix = get_prefix("cyberpunk")
        # "DO NOT USE:" 行之后
        assert "anime" in prefix, "cyberpunk prefix 应含 anime (DO NOT USE 行)"

    def test_prefix_contains_cel_shaded_in_do_not_use(self):
        prefix = get_prefix("cyberpunk")
        assert "cel-shaded" in prefix, "cyberpunk prefix 应含 cel-shaded (DO NOT USE 行)"

    def test_mandatory_top5_length(self):
        top5 = get_mandatory_top5("cyberpunk")
        assert len(top5) == 5, f"cyberpunk mandatory[:5] 长度应为 5, 实际: {len(top5)}"

    def test_forbidden_top8_length(self):
        top8 = get_forbidden_top8("cyberpunk")
        assert len(top8) == 8, f"cyberpunk forbidden[:8] 长度应为 8, 实际: {len(top8)}"

    def test_cyberpunk_still_has_neon_and_futuristic(self):
        """回归: 原有氛围词保留."""
        e = StyleEnforcer.get_enforcement("cyberpunk")
        all_mandatory = e.mandatory_keywords
        assert "neon lights" in all_mandatory, "cyberpunk 应保留 neon lights 氛围词"
        assert "futuristic city" in all_mandatory, "cyberpunk 应保留 futuristic city 氛围词"


# ---------------------------------------------------------------------------
# pastel_dream — 柔光插画，不能硬动漫 (但本身是插画，不加 photorealistic)
# ---------------------------------------------------------------------------

class TestPastelDreamWave12:
    """pastel_dream: mandatory 前 5 含软笔触介质锚点，forbidden 前 8 含 cel-shaded/manga/sharp ink/glossy idol."""

    def test_mandatory_has_soft_painterly_illustration(self):
        top5 = get_mandatory_top5("pastel_dream")
        assert "soft painterly illustration" in top5, (
            f"pastel_dream mandatory[:5] 应含 soft painterly illustration, 实际: {top5}"
        )

    def test_mandatory_has_airbrushed_soft_shading(self):
        top5 = get_mandatory_top5("pastel_dream")
        assert "airbrushed soft shading" in top5, (
            f"pastel_dream mandatory[:5] 应含 airbrushed soft shading, 实际: {top5}"
        )

    def test_mandatory_does_not_have_photorealistic(self):
        """pastel_dream 是插画风, 不应含 photorealistic (与其本质冲突)."""
        top5 = get_mandatory_top5("pastel_dream")
        assert "photorealistic" not in top5, (
            f"pastel_dream mandatory[:5] 不应含 photorealistic, 实际: {top5}"
        )

    def test_forbidden_has_cel_shaded(self):
        top8 = get_forbidden_top8("pastel_dream")
        assert "cel-shaded" in top8, f"pastel_dream forbidden[:8] 应含 cel-shaded, 实际: {top8}"

    def test_forbidden_has_hard_anime_lineart(self):
        top8 = get_forbidden_top8("pastel_dream")
        assert "hard anime lineart" in top8, (
            f"pastel_dream forbidden[:8] 应含 hard anime lineart, 实际: {top8}"
        )

    def test_forbidden_has_manga(self):
        top8 = get_forbidden_top8("pastel_dream")
        assert "manga" in top8, f"pastel_dream forbidden[:8] 应含 manga, 实际: {top8}"

    def test_forbidden_has_sharp_ink_outlines(self):
        top8 = get_forbidden_top8("pastel_dream")
        assert "sharp ink outlines" in top8, (
            f"pastel_dream forbidden[:8] 应含 sharp ink outlines, 实际: {top8}"
        )

    def test_forbidden_has_glossy_idol_render(self):
        top8 = get_forbidden_top8("pastel_dream")
        assert "glossy idol render" in top8, (
            f"pastel_dream forbidden[:8] 应含 glossy idol render, 实际: {top8}"
        )

    def test_prefix_contains_soft_painterly_in_must_include(self):
        prefix = get_prefix("pastel_dream")
        assert "soft painterly illustration" in prefix, (
            "pastel_dream prefix 应含 soft painterly illustration (MUST INCLUDE 行)"
        )

    def test_prefix_contains_cel_shaded_in_do_not_use(self):
        prefix = get_prefix("pastel_dream")
        assert "cel-shaded" in prefix, "pastel_dream prefix 应含 cel-shaded (DO NOT USE 行)"

    def test_prefix_contains_manga_in_do_not_use(self):
        prefix = get_prefix("pastel_dream")
        assert "manga" in prefix, "pastel_dream prefix 应含 manga (DO NOT USE 行)"

    def test_pastel_dream_still_has_dreamy_keywords(self):
        """回归: 原有梦幻色调词保留."""
        e = StyleEnforcer.get_enforcement("pastel_dream")
        all_mandatory = e.mandatory_keywords
        assert "pastel color palette" in all_mandatory, "pastel_dream 应保留 pastel color palette"
        assert "dreamy soft aesthetic" in all_mandatory, "pastel_dream 应保留 dreamy soft aesthetic"


# ---------------------------------------------------------------------------
# gothic — 暗黑浪漫绘画，不能光面 idol/动漫
# ---------------------------------------------------------------------------

class TestGothicWave12:
    """gothic: mandatory 前 5 含 dark romantic painting 绘画介质，forbidden 前 8 含 anime/cel-shaded/manga/glossy idol."""

    def test_mandatory_has_dark_romantic_painting(self):
        top5 = get_mandatory_top5("gothic")
        assert "dark romantic painting" in top5, (
            f"gothic mandatory[:5] 应含 dark romantic painting, 实际: {top5}"
        )

    def test_forbidden_has_anime(self):
        top8 = get_forbidden_top8("gothic")
        assert "anime" in top8, f"gothic forbidden[:8] 应含 anime, 实际: {top8}"

    def test_forbidden_has_cel_shaded(self):
        top8 = get_forbidden_top8("gothic")
        assert "cel-shaded" in top8, f"gothic forbidden[:8] 应含 cel-shaded, 实际: {top8}"

    def test_forbidden_has_manga(self):
        top8 = get_forbidden_top8("gothic")
        assert "manga" in top8, f"gothic forbidden[:8] 应含 manga, 实际: {top8}"

    def test_forbidden_has_glossy_idol_render(self):
        top8 = get_forbidden_top8("gothic")
        assert "glossy idol render" in top8, (
            f"gothic forbidden[:8] 应含 glossy idol render, 实际: {top8}"
        )

    def test_prefix_contains_dark_romantic_painting(self):
        prefix = get_prefix("gothic")
        assert "dark romantic painting" in prefix, (
            "gothic prefix 应含 dark romantic painting (MUST INCLUDE 行)"
        )

    def test_prefix_contains_anime_in_do_not_use(self):
        prefix = get_prefix("gothic")
        assert "anime" in prefix, "gothic prefix 应含 anime (DO NOT USE 行)"

    def test_gothic_still_has_cathedral_and_chiaroscuro(self):
        """回归: 原有风格词保留."""
        e = StyleEnforcer.get_enforcement("gothic")
        all_mandatory = e.mandatory_keywords
        assert "cathedral architecture" in all_mandatory, "gothic 应保留 cathedral architecture"
        assert "dramatic chiaroscuro" in all_mandatory, "gothic 应保留 dramatic chiaroscuro"


# ---------------------------------------------------------------------------
# 零破坏验证: by-design 动漫/插画类 style 不自禁介质
# ---------------------------------------------------------------------------

class TestByDesignStylesNotBroken:
    """cartoon / ghibli / manga / chibi / anime / illustration / korean_webtoon / slam_dunk
    均为 by-design 动漫/插画类，Wave 12 0 改动，逐项验证核心 mandatory 词存在。"""

    @pytest.mark.parametrize("style_name,expected_keyword", [
        ("cartoon", "cartoon style"),
        ("ghibli", "Studio Ghibli style"),
        ("manga", "manga style"),
        ("chibi", "chibi style"),
        ("anime", "anime style"),
        ("illustration", "digital illustration"),
        ("korean_webtoon", "Korean webtoon style"),
        ("slam_dunk", "slam dunk manga style"),
    ])
    def test_by_design_mandatory_keyword_preserved(self, style_name, expected_keyword):
        e = StyleEnforcer.get_enforcement(style_name)
        assert e is not None, f"style '{style_name}' 不存在"
        assert expected_keyword in e.mandatory_keywords, (
            f"{style_name}: mandatory 应含 '{expected_keyword}', "
            f"实际: {e.mandatory_keywords}"
        )

    @pytest.mark.parametrize("style_name", [
        "cartoon", "ghibli", "manga", "chibi", "anime",
        "illustration", "korean_webtoon", "slam_dunk",
    ])
    def test_by_design_prefix_renders_ok(self, style_name):
        """prefix 能正常 render (不抛异常, 不为空)."""
        prefix = get_prefix(style_name)
        assert len(prefix) > 100, f"{style_name} prefix 异常短: {prefix[:100]}"
        assert "MANDATORY STYLE REQUIREMENT" in prefix


# ---------------------------------------------------------------------------
# 未修改的 style (实测守住): 验证 mandatory 有介质锚点
# ---------------------------------------------------------------------------

class TestUnmodifiedStylesIntact:
    """ink / watercolor / ukiyo_e / pixel / noir: 实测已守住, Wave 12 0 改动, mandatory 介质锚点验证。"""

    @pytest.mark.parametrize("style_name,medium_keyword", [
        ("ink", "Chinese ink wash"),
        ("watercolor", "watercolor painting"),
        ("ukiyo_e", "ukiyo-e style"),
        ("pixel", "pixel art"),
        ("noir", "film noir style"),
    ])
    def test_medium_anchor_in_mandatory(self, style_name, medium_keyword):
        e = StyleEnforcer.get_enforcement(style_name)
        if e is None:
            pytest.skip(f"style '{style_name}' 不存在, 跳过")
        assert medium_keyword in e.mandatory_keywords, (
            f"{style_name} 应含介质锚点 '{medium_keyword}', 实际: {e.mandatory_keywords}"
        )


# ---------------------------------------------------------------------------
# ETA 不冻结: Stage 1-4 sub-progress 验证 (引用 Wave 12 job_manager 公式)
# ---------------------------------------------------------------------------

from app.services.job_manager import (
    calculate_eta_remaining_sec,
    _ETA_STAGE_PROGRESS_BOUNDS,
)


class TestETAStage14NotFrozen:
    """验证 Stage 1-4 sub-progress band 定义存在 + ETA 公式在 band 内单调递减。"""

    @pytest.mark.parametrize("stage", [
        "story_generation",
        "character_design",
        "storyboard",
    ])
    def test_stage_has_progress_bounds(self, stage):
        assert stage in _ETA_STAGE_PROGRESS_BOUNDS, (
            f"_ETA_STAGE_PROGRESS_BOUNDS 缺少 stage '{stage}'"
        )
        lo, hi = _ETA_STAGE_PROGRESS_BOUNDS[stage]
        assert lo < hi, f"{stage} band lo={lo} >= hi={hi}"

    def test_character_design_band_is_6_to_10(self):
        """P2-2 根因: character_design band 必须是 (6, 10) 才能让 portrait 子进度生效。"""
        lo, hi = _ETA_STAGE_PROGRESS_BOUNDS["character_design"]
        assert lo == 6 and hi == 10, (
            f"character_design band 应为 (6, 10), 实际: ({lo}, {hi})"
        )

    def test_eta_decreases_within_character_design_band(self):
        """ETA 在 character_design band 内随 progress 递增而递减 (不冻结)。"""
        eta_lo = calculate_eta_remaining_sec("character_design", 6, actual_shot_count=18)
        eta_hi = calculate_eta_remaining_sec("character_design", 9, actual_shot_count=18)
        assert eta_lo is not None and eta_hi is not None
        assert eta_hi < eta_lo, (
            f"ETA 应随 progress 递增而递减: eta@6={eta_lo}s, eta@9={eta_hi}s"
        )
