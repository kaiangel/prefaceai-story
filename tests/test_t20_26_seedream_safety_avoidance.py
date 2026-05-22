"""TASK-T20-FIXBATCH-5 Wave 4 RISK-T20-26 + KEY_LEARNINGS #37 —
Stage 4 prompt 加 Seedream 暗黑题材避开规则.

测试目标:
1. SEEDREAM_SAFETY_AVOIDANCE_RULES 块存在并可 import
2. 含 4 类 Seedream-rejected 触发词列表 (FORBIDDEN PHRASES)
3. 给出 4 种 SAFE STRATEGIES (Symbolic Object / Warm Light / Solo+Emotion / Defocused BG)
4. 提供 narrative beat → safe rewrite 表
5. 含 SELF-CHECK 步骤
6. 是 universal (不限定故事类型/角色物种)

不依赖 LLM API. 纯 prompt 内容单元测试.

Usage:
    cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story
    python -m pytest tests/test_t20_26_seedream_safety_avoidance.py -v
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest


# ========================================================================
# Section 1: SEEDREAM_SAFETY_AVOIDANCE_RULES 模块结构
# ========================================================================


class TestSeedreamSafetyAvoidanceRulesStructure:
    """新增 SEEDREAM_SAFETY_AVOIDANCE_RULES 块的存在性 + 必备元素"""

    def test_rules_importable(self):
        from app.prompts.storyboard_prompts import SEEDREAM_SAFETY_AVOIDANCE_RULES  # noqa: F401

    def test_rules_non_empty(self):
        from app.prompts.storyboard_prompts import SEEDREAM_SAFETY_AVOIDANCE_RULES
        assert len(SEEDREAM_SAFETY_AVOIDANCE_RULES) > 1000, "rules block too short to be meaningful"

    def test_dec_id_present(self):
        """规则块必须标注 DEC-045 T20-26 + KEY_LEARNINGS #37"""
        from app.prompts.storyboard_prompts import SEEDREAM_SAFETY_AVOIDANCE_RULES
        assert "DEC-045" in SEEDREAM_SAFETY_AVOIDANCE_RULES or "T20-26" in SEEDREAM_SAFETY_AVOIDANCE_RULES
        assert "KEY_LEARNINGS #37" in SEEDREAM_SAFETY_AVOIDANCE_RULES or "#37" in SEEDREAM_SAFETY_AVOIDANCE_RULES

    def test_critical_mark_present(self):
        """规则块顶部必须有 CRITICAL 强调"""
        from app.prompts.storyboard_prompts import SEEDREAM_SAFETY_AVOIDANCE_RULES
        assert "CRITICAL" in SEEDREAM_SAFETY_AVOIDANCE_RULES
        assert "Seedream" in SEEDREAM_SAFETY_AVOIDANCE_RULES


# ========================================================================
# Section 2: 4 类 FORBIDDEN 触发词列表
# ========================================================================


class TestForbiddenPhrasesListed:
    """FORBIDDEN PHRASES 必须覆盖 4 类 (灵异/双重曝光/已故角色/身体特征重叠)"""

    def test_category1_ghost_phrases_listed(self):
        from app.prompts.storyboard_prompts import SEEDREAM_SAFETY_AVOIDANCE_RULES
        lower = SEEDREAM_SAFETY_AVOIDANCE_RULES.lower()
        # Category 1
        assert "ghost" in lower
        assert "spectral" in lower
        assert "apparition" in lower
        assert "phantom" in lower

    def test_category2_double_exposure_phrases_listed(self):
        from app.prompts.storyboard_prompts import SEEDREAM_SAFETY_AVOIDANCE_RULES
        lower = SEEDREAM_SAFETY_AVOIDANCE_RULES.lower()
        assert "double-exposure" in lower or "double exposure" in lower
        assert "face overlapping" in lower or "faces overlapping" in lower
        assert "faces merging" in lower or "two faces" in lower

    def test_category3_deceased_emerges_listed(self):
        from app.prompts.storyboard_prompts import SEEDREAM_SAFETY_AVOIDANCE_RULES
        lower = SEEDREAM_SAFETY_AVOIDANCE_RULES.lower()
        assert "deceased emerges" in lower or "deceased appears" in lower
        assert "younger face emerges" in lower or "older face surfaces" in lower

    def test_category4_identical_features_listed(self):
        from app.prompts.storyboard_prompts import SEEDREAM_SAFETY_AVOIDANCE_RULES
        lower = SEEDREAM_SAFETY_AVOIDANCE_RULES.lower()
        assert "identical jaw" in lower or "identical scar" in lower or "identical face" in lower
        assert "exact contour" in lower


# ========================================================================
# Section 3: 4 种 SAFE STRATEGIES
# ========================================================================


class TestSafeStrategiesProvided:
    """规则块必须给 4 种安全替代策略, 不能只列禁忌"""

    def test_strategy_1_symbolic_object_present(self):
        """Strategy 1: 用旧照片/遗物代替灵异身体出现"""
        from app.prompts.storyboard_prompts import SEEDREAM_SAFETY_AVOIDANCE_RULES
        lower = SEEDREAM_SAFETY_AVOIDANCE_RULES.lower()
        assert "symbolic object" in lower or "photograph" in lower or "keepsake" in lower

    def test_strategy_2_warm_light_present(self):
        """Strategy 2: 用温暖光晕代替二人重叠"""
        from app.prompts.storyboard_prompts import SEEDREAM_SAFETY_AVOIDANCE_RULES
        lower = SEEDREAM_SAFETY_AVOIDANCE_RULES.lower()
        assert "golden halo" in lower or "warm light" in lower or "warm golden" in lower

    def test_strategy_3_solo_emotion_present(self):
        """Strategy 3: 单角色 + 强情绪表现"""
        from app.prompts.storyboard_prompts import SEEDREAM_SAFETY_AVOIDANCE_RULES
        lower = SEEDREAM_SAFETY_AVOIDANCE_RULES.lower()
        assert "alone" in lower
        assert "remembrance" in lower or "grief" in lower or "recognition" in lower

    def test_strategy_4_defocused_bg_present(self):
        """Strategy 4: 远景虚化身影 (仅必须时使用)"""
        from app.prompts.storyboard_prompts import SEEDREAM_SAFETY_AVOIDANCE_RULES
        lower = SEEDREAM_SAFETY_AVOIDANCE_RULES.lower()
        assert "deeply-blurred" in lower or "out of focus" in lower or "defocused" in lower

    def test_safe_alternative_for_ghost_grandfather(self):
        """实例: ghost of grandfather → 安全替换 (test19 真案例)"""
        from app.prompts.storyboard_prompts import SEEDREAM_SAFETY_AVOIDANCE_RULES
        # 必须显式给出 grandfather 的安全替代 (例子)
        assert "grandfather" in SEEDREAM_SAFETY_AVOIDANCE_RULES or "deceased" in SEEDREAM_SAFETY_AVOIDANCE_RULES.lower()


# ========================================================================
# Section 4: NARRATIVE BEAT → SAFE REWRITE 表
# ========================================================================


class TestNarrativeBeatRewriteTable:
    """规则块必须提供 narrative intent → safe image_prompt 的映射表"""

    def test_rewrite_table_present(self):
        from app.prompts.storyboard_prompts import SEEDREAM_SAFETY_AVOIDANCE_RULES
        # 表格必须列出 narrative beat → forbidden vs safe
        assert "NARRATIVE BEAT" in SEEDREAM_SAFETY_AVOIDANCE_RULES or "SAFE REWRITE TABLE" in SEEDREAM_SAFETY_AVOIDANCE_RULES

    def test_table_has_bad_and_good_examples(self):
        from app.prompts.storyboard_prompts import SEEDREAM_SAFETY_AVOIDANCE_RULES
        # ❌/✅ 对比 (至少 3 行)
        bad_count = SEEDREAM_SAFETY_AVOIDANCE_RULES.count("❌")
        good_count = SEEDREAM_SAFETY_AVOIDANCE_RULES.count("✅")
        assert bad_count >= 5, f"expected ≥5 ❌ markers, got {bad_count}"
        assert good_count >= 5, f"expected ≥5 ✅ markers, got {good_count}"


# ========================================================================
# Section 5: SELF-CHECK 步骤
# ========================================================================


class TestSelfCheckStep:
    """规则块必须含 LLM 输出前的 SELF-CHECK 扫描清单"""

    def test_self_check_section_present(self):
        from app.prompts.storyboard_prompts import SEEDREAM_SAFETY_AVOIDANCE_RULES
        assert "SELF-CHECK" in SEEDREAM_SAFETY_AVOIDANCE_RULES

    def test_self_check_lists_forbidden_tokens(self):
        from app.prompts.storyboard_prompts import SEEDREAM_SAFETY_AVOIDANCE_RULES
        # SELF-CHECK 必须列出所有 forbidden tokens 让 LLM 自检
        section_start = SEEDREAM_SAFETY_AVOIDANCE_RULES.find("SELF-CHECK")
        if section_start == -1:
            pytest.skip("no SELF-CHECK section")
        section = SEEDREAM_SAFETY_AVOIDANCE_RULES[section_start:].lower()
        assert "ghost" in section
        assert "double-exposure" in section
        assert "identical" in section
        assert "rewrite" in section  # 必须明确指令: 发现就 rewrite


# ========================================================================
# Section 6: Universal (不限定故事类型/角色物种)
# ========================================================================


class TestUniversal:
    """规则块必须 universal — 适用所有故事类型"""

    def test_not_hardcoded_to_dark_fantasy(self):
        """规则不应只针对 dark_fantasy 风格"""
        from app.prompts.storyboard_prompts import SEEDREAM_SAFETY_AVOIDANCE_RULES
        lower = SEEDREAM_SAFETY_AVOIDANCE_RULES.lower()
        # 必须说"ANY scene"或类似 universal 措辞
        assert "any scene" in lower or "any story" in lower or "all" in lower or "适用" in SEEDREAM_SAFETY_AVOIDANCE_RULES

    def test_covers_multiple_narrative_types(self):
        """覆盖多种叙事场景 — 不只一个"""
        from app.prompts.storyboard_prompts import SEEDREAM_SAFETY_AVOIDANCE_RULES
        # 必须提及多类场景: 记忆 / 灵异 / 双重曝光 / 时空交错
        lower = SEEDREAM_SAFETY_AVOIDANCE_RULES.lower()
        scenarios = ["memory", "vision", "flashback", "past-self", "deceased",
                     "spirit", "ghost", "haunted", "supernatural"]
        present = sum(1 for s in scenarios if s in lower)
        assert present >= 4, f"expected ≥4 narrative scenario keywords, got {present}"


# ========================================================================
# Section 7: 与 SPECIES_FIDELITY_RULES 共存 (向后兼容)
# ========================================================================


class TestCoexistWithSpeciesFidelity:
    """新规则不破坏 T20-17 SPECIES_FIDELITY_RULES"""

    def test_species_fidelity_still_importable(self):
        from app.prompts.storyboard_prompts import SPECIES_FIDELITY_RULES  # noqa: F401

    def test_both_rules_coexist(self):
        from app.prompts.storyboard_prompts import (
            SPECIES_FIDELITY_RULES,
            SEEDREAM_SAFETY_AVOIDANCE_RULES,
        )
        # 两个规则块都 non-empty 且不互相覆盖
        assert SPECIES_FIDELITY_RULES != SEEDREAM_SAFETY_AVOIDANCE_RULES
        assert len(SPECIES_FIDELITY_RULES) > 500
        assert len(SEEDREAM_SAFETY_AVOIDANCE_RULES) > 1000

    def test_build_stage4_character_data_block_still_importable(self):
        from app.prompts.storyboard_prompts import build_stage4_character_data_block  # noqa: F401


# ========================================================================
# Section 8: 模拟 Stage 4 prompt 拼装 (验证可 inject 不冲突)
# ========================================================================


class TestStage4PromptInjectionSimulation:
    """模拟 storyboard_director.py 怎么拼装新规则块"""

    def test_can_inject_into_prompt_template(self):
        """模拟 _build_scene_prompt() L1666 注入"""
        from app.prompts.storyboard_prompts import (
            COMIC_MODE_NARRATIVE_RULES,
            SPECIES_FIDELITY_RULES,
            SEEDREAM_SAFETY_AVOIDANCE_RULES,
        )
        template = f"""
{COMIC_MODE_NARRATIVE_RULES}

{SPECIES_FIDELITY_RULES}

{SEEDREAM_SAFETY_AVOIDANCE_RULES}
"""
        assert len(template) > 5000  # all 3 blocks combined
        assert "ghost" in template.lower()  # T20-26 rule present
        assert "species" in template.lower()  # T20-17 rule present
        assert "no voiceover" in template.lower() or "voiceover" in template.lower()  # COMIC_MODE


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
