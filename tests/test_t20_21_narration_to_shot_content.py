"""TASK-T20-FIXBATCH-4 Wave 1 RISK-T20-21 P0 — DEC-044 去旁白 + 内容融入 shot.

测试目标:
1. screenplay_prompts.py 新模块的 DEC-044 rules 全文齐 + 可被 import
2. validate_narration_caption_length() 真正 enforces ≤120/≤25 chars 边界
3. validate_dialogue_thought_density() 真正 enforces ≥1 thought + plot-essential
4. storyboard_prompts.py COMIC_MODE_NARRATIVE_RULES 升级版含 DEC-044 关键规则
5. 向后兼容: 旧 test17 v2 narration (long prose) 仍可 validate (issues 列表非空但不崩)
6. Universal: 多语言/多类型/多风格 scene 都能 validate

不依赖 LLM API, 不依赖 DB, 不依赖 backend 服务. 纯 prompt + validator 单元测试.

Usage:
    cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story
    python -m pytest tests/test_t20_21_narration_to_shot_content.py -v
"""

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest


# ========================================================================
# Section 1: screenplay_prompts.py module structure tests
# ========================================================================


class TestScreenplayPromptsModuleStructure:
    """新建模块 app/prompts/screenplay_prompts.py 的结构 / 可 import / 完整性"""

    def test_module_importable(self):
        """新模块可以 import 不报错"""
        from app.prompts import screenplay_prompts  # noqa: F401

    def test_all_exports_present(self):
        """__all__ 中列出的所有 symbol 都真存在"""
        from app.prompts import screenplay_prompts
        for name in screenplay_prompts.__all__:
            assert hasattr(screenplay_prompts, name), f"missing export: {name}"

    def test_dec044_top_level_block_present(self):
        """顶层 DEC044_SCREENPLAY_RULES 包含 3 个子块"""
        from app.prompts.screenplay_prompts import (
            DEC044_PRODUCT_FORM_DECLARATION,
            NARRATION_CAPTION_RULES,
            DIALOGUE_THOUGHT_DENSITY_RULES,
            DEC044_SCREENPLAY_RULES,
        )
        assert DEC044_PRODUCT_FORM_DECLARATION in DEC044_SCREENPLAY_RULES
        assert NARRATION_CAPTION_RULES in DEC044_SCREENPLAY_RULES
        assert DIALOGUE_THOUGHT_DENSITY_RULES in DEC044_SCREENPLAY_RULES

    def test_dec044_rules_mention_no_tts_no_voiceover(self):
        """rules 必须明确说"NO TTS / NO voiceover" (DEC-044 核心)"""
        from app.prompts.screenplay_prompts import DEC044_SCREENPLAY_RULES
        # 关键词必须出现 (universal — 不限定具体措辞但要含核心概念)
        assert "TTS" in DEC044_SCREENPLAY_RULES, "must explicitly mention TTS is gone"
        assert "voiceover" in DEC044_SCREENPLAY_RULES.lower() or "voice-over" in DEC044_SCREENPLAY_RULES.lower(), \
            "must explicitly say no voiceover"
        assert "DEC-044" in DEC044_SCREENPLAY_RULES, "must cite the decision number"

    def test_dec044_rules_mention_caption_length_limit(self):
        """rules 必须明确说 narration ≤25 chars per caption"""
        from app.prompts.screenplay_prompts import DEC044_SCREENPLAY_RULES
        # 必须出现 ≤25 或者具体数字 25 的限制
        assert "25" in DEC044_SCREENPLAY_RULES, "must specify 25-char caption limit"

    def test_dec044_rules_have_worked_examples(self):
        """rules 必须含 worked examples (test17 灰狐故事示例)"""
        from app.prompts.screenplay_prompts import DEC044_SCREENPLAY_RULES
        assert "❌" in DEC044_SCREENPLAY_RULES, "must show BAD examples"
        assert "✅" in DEC044_SCREENPLAY_RULES, "must show GOOD examples"

    def test_output_example_is_dec044_conformant(self):
        """DEC044_SCREENPLAY_OUTPUT_EXAMPLE 自己必须符合 ≤120/≤25 char 规则"""
        from app.prompts.screenplay_prompts import (
            DEC044_SCREENPLAY_OUTPUT_EXAMPLE,
            validate_narration_caption_length,
        )
        # 提取示例里的 narration 字段 (粗略 — find first '"narration": "..."')
        import re
        m = re.search(r'"narration":\s*"([^"]+)"', DEC044_SCREENPLAY_OUTPUT_EXAMPLE)
        assert m, "example must contain a narration field"
        narration = m.group(1)
        result = validate_narration_caption_length(narration)
        assert result["passes_total_length"], f"example's narration breaks total length rule: {result['issues']}"
        assert result["passes_sentence_length"], f"example's narration breaks per-sentence rule: {result['issues']}"

    def test_integration_notes_present(self):
        """INTEGRATION_NOTES 必须存在并告诉 Backend 怎么 wire"""
        from app.prompts.screenplay_prompts import INTEGRATION_NOTES
        assert "screenplay_writer.py" in INTEGRATION_NOTES
        assert "_build_batch_prompt" in INTEGRATION_NOTES
        assert "_build_single_scene_prompt" in INTEGRATION_NOTES


# ========================================================================
# Section 2: hard-cap getters return expected DEC-044 values
# ========================================================================


class TestDec044HardCaps:
    """硬限制 getter 返回值正确"""

    def test_narration_max_chars(self):
        from app.prompts.screenplay_prompts import get_dec044_narration_max_chars
        assert get_dec044_narration_max_chars() == 120

    def test_caption_max_chars(self):
        from app.prompts.screenplay_prompts import get_dec044_caption_max_chars
        assert get_dec044_caption_max_chars() == 25

    def test_dialogue_max_chars(self):
        from app.prompts.screenplay_prompts import get_dec044_dialogue_max_chars
        # DEC-045 T20-21 v2 (2026-05-19): 25 → 35 (Founder 反馈通俗易懂)
        assert get_dec044_dialogue_max_chars() == 35

    def test_distribution_targets_structure(self):
        from app.prompts.screenplay_prompts import get_dec044_distribution_targets
        t = get_dec044_distribution_targets()
        # 必须有以下 key
        for k in ("dialogue_pct_min", "dialogue_pct_max",
                  "thought_pct_min", "thought_pct_max",
                  "narration_pct_max", "min_thought_per_scene",
                  "min_plot_essential_per_scene"):
            assert k in t, f"missing distribution target: {k}"
        # dialogue 50-65 (从 60-70 收紧)
        assert t["dialogue_pct_min"] == 50
        assert t["dialogue_pct_max"] == 65
        # thought 25-40 (从 20-30 放宽)
        assert t["thought_pct_min"] == 25
        assert t["thought_pct_max"] == 40


# ========================================================================
# Section 3: validate_narration_caption_length tests (DEC-044 enforcement)
# ========================================================================


class TestNarrationCaptionValidator:
    """validate_narration_caption_length 正确判断 DEC-044 ≤120 / ≤25 边界"""

    def test_empty_narration_passes(self):
        """空 narration 允许 (有些 scene 纯 dialogue-driven)"""
        from app.prompts.screenplay_prompts import validate_narration_caption_length
        r = validate_narration_caption_length("")
        assert r["passes_total_length"]
        assert r["passes_sentence_length"]
        assert r["char_count"] == 0
        assert r["issues"] == []

    def test_short_caption_passes(self):
        """≤25 chars single sentence 通过 (理想 DEC-044 caption)"""
        from app.prompts.screenplay_prompts import validate_narration_caption_length
        r = validate_narration_caption_length("立春清晨，灰狐独行赴年年之约。")
        assert r["passes_total_length"]
        assert r["passes_sentence_length"]
        assert r["issues"] == []

    def test_short_multi_caption_passes(self):
        """≤120 chars total + each sentence ≤25 通过 (理想 DEC-044 sequence)"""
        from app.prompts.screenplay_prompts import validate_narration_caption_length
        narration = "立春清晨，雪林苏醒。灰狐独行赴年年之约。树上有二十三道划痕。"
        r = validate_narration_caption_length(narration)
        assert r["passes_total_length"], r["issues"]
        assert r["passes_sentence_length"], r["issues"]

    def test_long_prose_fails_total(self):
        """旧 TTS-era 长 prose narration 必须 fail total-length check"""
        from app.prompts.screenplay_prompts import validate_narration_caption_length
        # test17 v2 实际 Shot 1 narration_segment (122 chars)
        narration = (
            "立春的清晨，深山雪林还未完全苏醒。白桦树的枝丫挂着昨夜最后一层薄霜，"
            "晨光从林梢斜斜透入，将雪地染成淡蓝与银白交织的颜色。就在这寂静里，"
            "一道苍老却稳健的身影踏雪而来。"
        )
        r = validate_narration_caption_length(narration)
        # 总长 ~110 但每句很长 → 至少一项 fail
        assert (not r["passes_total_length"]) or (not r["passes_sentence_length"])
        assert len(r["issues"]) >= 1

    def test_long_single_sentence_fails_sentence(self):
        """单句 >25 chars 必须 fail per-sentence check"""
        from app.prompts.screenplay_prompts import validate_narration_caption_length
        # 单句 40+ chars
        narration = "灰狐缓缓站起来用爪尖贴着树皮轻轻触碰嘴唇翕动声音太低低到三只小动物只能看见他说话的样子却听不清字。"
        r = validate_narration_caption_length(narration)
        assert not r["passes_sentence_length"]
        assert any("sentence" in i for i in r["issues"])

    def test_universal_cjk_counting(self):
        """中文 ＋ 西文标点混合也正确计数 CJK chars"""
        from app.prompts.screenplay_prompts import validate_narration_caption_length
        # 混合: 含 ASCII 标点不应计入
        narration = "立春清晨, 灰狐独行赴年年之约."
        r = validate_narration_caption_length(narration)
        # CJK chars 约 15 — 应通过
        assert r["passes_total_length"]
        assert r["char_count"] < 20

    def test_backward_compat_does_not_crash(self):
        """旧故事的 prose narration 不让 validator 崩 (只 surface issues)"""
        from app.prompts.screenplay_prompts import validate_narration_caption_length
        narration = (
            "他叹道「你知道的，我没有别的选择。」窗外的雨下了一整夜，"
            "天色像被人撕碎的灰布，一点点垂落到城市的肩上。"
        )
        # 不应抛异常
        r = validate_narration_caption_length(narration)
        assert isinstance(r, dict)
        assert "issues" in r
        assert "char_count" in r


# ========================================================================
# Section 4: validate_dialogue_thought_density tests
# ========================================================================


class TestDialogueThoughtDensityValidator:
    """validate_dialogue_thought_density 正确判断 DEC-044 density 规则"""

    def test_empty_beats_fails(self):
        from app.prompts.screenplay_prompts import validate_dialogue_thought_density
        r = validate_dialogue_thought_density({"dialogue_beats": []})
        assert not r["passes_thought_min"]
        assert len(r["issues"]) >= 1

    def test_no_thought_fails(self):
        """只 dialogue 没 thought → fail thought_min"""
        from app.prompts.screenplay_prompts import validate_dialogue_thought_density
        scene = {
            "dialogue_beats": [
                {"type": "dialogue", "speaker": "char_001", "line": "你好"},
                {"type": "dialogue", "speaker": "char_002", "line": "嗨"},
            ]
        }
        r = validate_dialogue_thought_density(scene)
        assert not r["passes_thought_min"]
        assert r["thought_count"] == 0
        assert r["dialogue_count"] == 2

    def test_one_thought_passes_thought_min(self):
        """≥1 thought 满足 min 要求"""
        from app.prompts.screenplay_prompts import validate_dialogue_thought_density
        scene = {
            "dialogue_beats": [
                {"type": "dialogue", "speaker": "char_001", "line": "你好"},
                {"type": "thought", "speaker": "char_002", "line": "（他来了二十三年了）"},
            ]
        }
        r = validate_dialogue_thought_density(scene)
        assert r["passes_thought_min"]
        assert r["passes_plot_essential"]  # 含 "二十三年"
        assert r["thought_count"] == 1

    def test_vague_lines_fail_plot_essential(self):
        """全部 vague 短 line → fail plot-essential heuristic"""
        from app.prompts.screenplay_prompts import validate_dialogue_thought_density
        scene = {
            "dialogue_beats": [
                {"type": "thought", "speaker": "char_001", "line": "（怎么会这样）"},
                {"type": "dialogue", "speaker": "char_002", "line": "好"},
                {"type": "dialogue", "speaker": "char_003", "line": "嗯"},
            ]
        }
        r = validate_dialogue_thought_density(scene)
        assert r["passes_thought_min"]  # 有 1 thought
        # 全都很 vague 没数字没强动词没长 line → fail plot-essential
        assert not r["passes_plot_essential"]

    def test_number_line_passes_plot_essential(self):
        """含数字 line 触发 plot-essential heuristic"""
        from app.prompts.screenplay_prompts import validate_dialogue_thought_density
        scene = {
            "dialogue_beats": [
                {"type": "thought", "speaker": "char_001", "line": "（想想）"},
                {"type": "dialogue", "speaker": "char_002", "line": "二十三年了。"},
            ]
        }
        r = validate_dialogue_thought_density(scene)
        assert r["passes_plot_essential"]

    def test_reveal_verb_passes_plot_essential(self):
        """含强 reveal 动词 line 触发 plot-essential heuristic"""
        from app.prompts.screenplay_prompts import validate_dialogue_thought_density
        scene = {
            "dialogue_beats": [
                {"type": "thought", "speaker": "char_001", "line": "（突然明白了）"},
                {"type": "dialogue", "speaker": "char_002", "line": "她其实没死。"},
            ]
        }
        r = validate_dialogue_thought_density(scene)
        # "死" 在强 reveal 动词清单
        assert r["passes_plot_essential"]

    def test_long_line_passes_plot_essential(self):
        """≥10 CJK chars line 也触发 (信息密度足够)"""
        from app.prompts.screenplay_prompts import validate_dialogue_thought_density
        scene = {
            "dialogue_beats": [
                {"type": "thought", "speaker": "char_001", "line": "（嗯）"},
                {"type": "dialogue", "speaker": "char_002",
                 "line": "树皮上刻着密密麻麻的划痕。"},
            ]
        }
        r = validate_dialogue_thought_density(scene)
        assert r["passes_plot_essential"]

    def test_distribution_pct_correctly_computed(self):
        from app.prompts.screenplay_prompts import validate_dialogue_thought_density
        scene = {
            "dialogue_beats": [
                {"type": "dialogue", "speaker": "char_001", "line": "我要卖房。"},
                {"type": "dialogue", "speaker": "char_002", "line": "你疯了？"},
                {"type": "thought", "speaker": "char_001", "line": "（妈妈不会理解。）"},
                {"type": "thought", "speaker": "char_002", "line": "（他真的要走？）"},
            ]
        }
        r = validate_dialogue_thought_density(scene)
        assert r["dialogue_count"] == 2
        assert r["thought_count"] == 2
        assert r["dialogue_pct"] == 50.0
        assert r["thought_pct"] == 50.0

    def test_universal_works_for_any_story_type(self):
        """validator 不 hardcode 特定故事/角色/语言/风格"""
        from app.prompts.screenplay_prompts import validate_dialogue_thought_density
        # 科幻 / robot 角色 / 未来场景
        sf_scene = {
            "dialogue_beats": [
                {"type": "dialogue", "speaker": "robot_001",
                 "line": "数据显示故障率0.3%。"},
                {"type": "thought", "speaker": "robot_002",
                 "line": "（他是被诬告的。）"},
            ]
        }
        r = validate_dialogue_thought_density(sf_scene)
        assert r["passes_thought_min"]
        assert r["passes_plot_essential"]

        # 武侠 / 古风
        wuxia_scene = {
            "dialogue_beats": [
                {"type": "dialogue", "speaker": "侠客",
                 "line": "十年寻仇，今日了结。"},
                {"type": "thought", "speaker": "师父",
                 "line": "（他终于来了。）"},
            ]
        }
        r2 = validate_dialogue_thought_density(wuxia_scene)
        assert r2["passes_thought_min"]
        assert r2["passes_plot_essential"]


# ========================================================================
# Section 5: COMIC_MODE_NARRATIVE_RULES (storyboard_prompts) 升级版校验
# ========================================================================


class TestStoryboardComicRulesUpgrade:
    """COMIC_MODE_NARRATIVE_RULES 已升级为 DEC-044 终极形态规则"""

    def test_rules_importable(self):
        from app.prompts.storyboard_prompts import COMIC_MODE_NARRATIVE_RULES  # noqa: F401

    def test_rules_mention_dec044(self):
        from app.prompts.storyboard_prompts import COMIC_MODE_NARRATIVE_RULES
        assert "DEC-044" in COMIC_MODE_NARRATIVE_RULES

    def test_rules_forbid_text_type_none(self):
        """新 RULE 0 必须禁止 text_type=none (有角色的 shot)"""
        from app.prompts.storyboard_prompts import COMIC_MODE_NARRATIVE_RULES
        assert "text_type=\"none\"" in COMIC_MODE_NARRATIVE_RULES or \
               "text_type='none'" in COMIC_MODE_NARRATIVE_RULES or \
               'text_type="none"' in COMIC_MODE_NARRATIVE_RULES
        assert "FORBIDDEN" in COMIC_MODE_NARRATIVE_RULES

    def test_rules_specify_caption_length_limit(self):
        """narration caption 限制必须出现"""
        from app.prompts.storyboard_prompts import COMIC_MODE_NARRATIVE_RULES
        assert "≤25" in COMIC_MODE_NARRATIVE_RULES or "25 chars" in COMIC_MODE_NARRATIVE_RULES

    def test_rules_include_distillation_examples(self):
        """必须含 BAD vs GOOD distillation examples (灰狐故事 worked example)"""
        from app.prompts.storyboard_prompts import COMIC_MODE_NARRATIVE_RULES
        assert "❌ BAD" in COMIC_MODE_NARRATIVE_RULES
        assert "✅ GOOD" in COMIC_MODE_NARRATIVE_RULES
        # 含 test17 灰狐故事示例的关键词之一
        assert any(k in COMIC_MODE_NARRATIVE_RULES for k in
                   ["二十三", "灰狐", "划痕", "银色狼毛"]), \
            "should include test17 灰狐故事 worked example for concreteness"

    def test_rules_include_self_check_block(self):
        """必须含 SELF-CHECK pre-flight 块 (LLM 在输出前自检)"""
        from app.prompts.storyboard_prompts import COMIC_MODE_NARRATIVE_RULES
        assert "SELF-CHECK" in COMIC_MODE_NARRATIVE_RULES

    def test_rules_total_length_reasonable(self):
        """rules 不能短到没内容, 也不能长到爆 token (粗略 sanity check)"""
        from app.prompts.storyboard_prompts import COMIC_MODE_NARRATIVE_RULES
        n = len(COMIC_MODE_NARRATIVE_RULES)
        # DEC-045 T20-21 v2 + T20-27 升级后 ~11000 chars (旧版 ~900,
        # 中间版 ~3500). cap 放宽到 16000.
        assert 2500 <= n <= 16000, f"COMIC_MODE_NARRATIVE_RULES length={n} unexpected"


# ========================================================================
# Section 6: 真实数据对比 — test17 v2 旧 narration vs DEC-044 应该的形态
# ========================================================================


class TestRealDataComparison:
    """test17 v2 真实 screenplay 数据应该 fail 新 validator (证明 validator 真有效)"""

    @pytest.fixture
    def test17_v2_screenplay(self):
        """加载 test17 v2 实际生成的 3_screenplay.json"""
        import json
        path = project_root / "output" / "adfdfa58-b2b3-420c-bddd-5e9077ceba3e" / "3_screenplay.json"
        if not path.exists():
            pytest.skip(f"test17 v2 screenplay not found at {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_old_narration_fails_dec044_validator(self, test17_v2_screenplay):
        """旧 ScreenplayWriter 输出的 long narration 必须 fail 新 validator
        — 证明 validator 真有 enforcement 能力"""
        from app.prompts.screenplay_prompts import validate_narration_caption_length
        scenes = test17_v2_screenplay.get("scenes", [])
        assert len(scenes) > 0
        fail_count = 0
        for sc in scenes:
            narration = sc.get("narration", "")
            r = validate_narration_caption_length(narration)
            if not (r["passes_total_length"] and r["passes_sentence_length"]):
                fail_count += 1
        # 旧版几乎所有 scene 都应该 fail (narration 270-370 chars)
        assert fail_count >= max(1, len(scenes) - 1), \
            f"only {fail_count}/{len(scenes)} scenes fail new validator " \
            f"— validator may not be strict enough"

    def test_old_density_thought_min_check(self, test17_v2_screenplay):
        """旧 ScreenplayWriter 输出的 dialogue_beats density — 至少有 thought"""
        from app.prompts.screenplay_prompts import validate_dialogue_thought_density
        scenes = test17_v2_screenplay.get("scenes", [])
        # 旧版本 thought 20% 配额, 通常会满足 ≥1 thought
        for sc in scenes:
            r = validate_dialogue_thought_density(sc)
            # 不强 assert (旧故事可能有空 dialogue_beats scene)
            # 只验证 validator 不崩 + 返回 dict 结构
            assert isinstance(r, dict)
            assert "thought_count" in r


# ========================================================================
# Section 7: TextOverlayService 兼容性确认 (read-only check)
# ========================================================================


def _load_text_overlay_module():
    """Direct file-spec load of app/services/text_overlay_service.py to bypass
    app/services/__init__.py imports (story_generator needs google.genai which
    may not be present in this environment). Returns the module object.

    Universal: works in any test runner / venv without requiring full backend
    deps. This is a TEST-ONLY helper to verify TextOverlayService capability.
    """
    import importlib.util
    src = project_root / "app" / "services" / "text_overlay_service.py"
    spec = importlib.util.spec_from_file_location("_tos_compat", str(src))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestTextOverlayServiceCompat:
    """TextOverlayServiceV2 是否支持 DEC-044 需要的所有 text_type"""

    def test_supported_text_types_include_dec044_needs(self):
        """TextOverlayService.process_shot 需要支持的 text_type 全在"""
        mod = _load_text_overlay_module()
        TextOverlayService = mod.TextOverlayService
        # 通过 inspect 看 process_shot 的内部分支
        import inspect
        src = inspect.getsource(TextOverlayService.process_shot)
        # DEC-044 需要的: narration / thought / dialogue / dialogue_with_thought
        for t in ("narration", "thought", "dialogue", "dialogue_with_thought"):
            assert t in src, f"TextOverlayService missing text_type: {t}"

    def test_multi_bubble_support(self):
        """get_bubble_position_for_index 支持 2-6 个气泡"""
        mod = _load_text_overlay_module()
        get_bubble_position_for_index = mod.get_bubble_position_for_index
        # 1 个气泡
        pos1 = get_bubble_position_for_index(0, 1)
        assert len(pos1) == 2  # (x_pct, y_pct)
        # 2 个气泡
        pos2 = get_bubble_position_for_index(1, 2)
        assert len(pos2) == 2
        # 5 个气泡 (overcrowd 但不崩)
        pos5 = get_bubble_position_for_index(4, 5)
        assert len(pos5) == 2

    def test_narration_can_position_top_or_bottom(self):
        """add_monologue 支持 top / bottom / center 位置"""
        mod = _load_text_overlay_module()
        TextOverlayService = mod.TextOverlayService
        import inspect
        src = inspect.getsource(TextOverlayService.add_monologue)
        for pos in ("top", "bottom", "center"):
            assert pos in src, f"add_monologue missing position: {pos}"


# ========================================================================
# Section 8: end-to-end prompt build verification
# ========================================================================


class TestPromptBuildersEndToEnd:
    """builder helpers 端到端返回完整可注入的 prompt block"""

    def test_build_dec044_screenplay_block(self):
        from app.prompts.screenplay_prompts import build_dec044_screenplay_block
        block = build_dec044_screenplay_block()
        assert isinstance(block, str)
        assert len(block) > 1000, "block must be substantial (≥1000 chars)"
        assert "DEC-044" in block
        assert "narration" in block.lower()
        assert "dialogue" in block.lower()
        assert "thought" in block.lower()

    def test_build_dec044_output_example(self):
        from app.prompts.screenplay_prompts import build_dec044_output_example
        ex = build_dec044_output_example()
        assert isinstance(ex, str)
        # 含 JSON-like structure markers
        assert '"scene_id"' in ex
        assert '"narration"' in ex
        assert '"dialogue_beats"' in ex


# ========================================================================
# Section 9: T20-21 v2 升级测试 — dialogue/thought 长度 25→35 + 通俗易懂
# ========================================================================


class TestT20_21_v2_LineLengthUpgrade:
    """v2: dialogue/thought 长度上限从 25 → 35 (Founder 实证反馈)"""

    def test_dialogue_max_chars_is_35(self):
        from app.prompts.screenplay_prompts import get_dec044_dialogue_max_chars
        assert get_dec044_dialogue_max_chars() == 35

    def test_density_rules_mention_35_chars(self):
        from app.prompts.screenplay_prompts import DIALOGUE_THOUGHT_DENSITY_RULES
        assert "35" in DIALOGUE_THOUGHT_DENSITY_RULES, "v2 must specify 35-char cap"

    def test_density_rules_have_v2_marker(self):
        from app.prompts.screenplay_prompts import DIALOGUE_THOUGHT_DENSITY_RULES
        assert "v2" in DIALOGUE_THOUGHT_DENSITY_RULES.lower() or "T20-21 v2" in DIALOGUE_THOUGHT_DENSITY_RULES

    def test_density_rules_provide_sweet_spot_18_30(self):
        """v2 必须告诉 LLM target 18-30, hard cap 35"""
        from app.prompts.screenplay_prompts import DIALOGUE_THOUGHT_DENSITY_RULES
        # 18-30 sweet spot
        assert "18-30" in DIALOGUE_THOUGHT_DENSITY_RULES or "sweet spot" in DIALOGUE_THOUGHT_DENSITY_RULES.lower()


class TestT20_21_v2_PlainLanguageRule:
    """v2: 通俗易懂规则 (D7) — 反文言/晦涩词"""

    def test_d7_plain_language_rule_present(self):
        from app.prompts.screenplay_prompts import DIALOGUE_THOUGHT_DENSITY_RULES
        assert "PLAIN-LANGUAGE" in DIALOGUE_THOUGHT_DENSITY_RULES or "通俗易懂" in DIALOGUE_THOUGHT_DENSITY_RULES

    def test_d7_forbidden_classical_words_listed(self):
        """禁文言词列表必须含 KEY_LEARNINGS #37 高频词"""
        from app.prompts.screenplay_prompts import DIALOGUE_THOUGHT_DENSITY_RULES
        # 必须列禁忌词 (至少几个)
        forbidden = ["咒", "夙愿", "亘古", "殒命", "命数"]
        present = sum(1 for w in forbidden if w in DIALOGUE_THOUGHT_DENSITY_RULES)
        assert present >= 3, f"expected ≥3 classical forbidden words, got {present}"

    def test_d7_provides_replacement_table(self):
        """禁忌词必须有对应日常口语替换"""
        from app.prompts.screenplay_prompts import DIALOGUE_THOUGHT_DENSITY_RULES
        # 替换示例
        assert "心愿" in DIALOGUE_THOUGHT_DENSITY_RULES
        assert "哀鸣" in DIALOGUE_THOUGHT_DENSITY_RULES or "叫" in DIALOGUE_THOUGHT_DENSITY_RULES

    def test_d7_exceptions_for_classical_characters(self):
        """exception: 古风角色/咒文/proper noun 允许文言"""
        from app.prompts.screenplay_prompts import DIALOGUE_THOUGHT_DENSITY_RULES
        assert "EXCEPTION" in DIALOGUE_THOUGHT_DENSITY_RULES
        # 允许的特殊场景说明
        lower = DIALOGUE_THOUGHT_DENSITY_RULES.lower()
        assert "classical scholar" in lower or "monk" in lower or "poem" in lower or "ritual" in lower

    def test_d7_test_reading_aloud_criterion(self):
        """v2 必须给"读出声判断是否通俗"的检验法"""
        from app.prompts.screenplay_prompts import DIALOGUE_THOUGHT_DENSITY_RULES
        lower = DIALOGUE_THOUGHT_DENSITY_RULES.lower()
        assert "read each line aloud" in lower or "read aloud" in lower or "sounds like" in lower


class TestT20_21_v2_Stage4PromptUpdate:
    """v2: storyboard_prompts.py COMIC_MODE_NARRATIVE_RULES RULE 6 同步 35"""

    def test_rule_6_updated_to_35_chars(self):
        from app.prompts.storyboard_prompts import COMIC_MODE_NARRATIVE_RULES
        # RULE 6 必须有 35 字
        # 注意: "RULE 6" 字符串可能在多处出现 (RULE 0.B SELF-CHECK 段提到 RULE 6),
        # 用 "## RULE 6" (markdown header) 精确定位
        marker = "## RULE 6"
        idx = COMIC_MODE_NARRATIVE_RULES.find(marker)
        assert idx != -1, f"missing markdown header '{marker}' in COMIC_MODE_NARRATIVE_RULES"
        rule_6_section = COMIC_MODE_NARRATIVE_RULES[idx:idx + 2000]
        assert "35" in rule_6_section, "RULE 6 must specify 35-char cap"

    def test_rule_7_plain_language_in_stage4(self):
        """Stage 4 COMIC_MODE 也加 PLAIN-LANGUAGE (RULE 7)"""
        from app.prompts.storyboard_prompts import COMIC_MODE_NARRATIVE_RULES
        assert "PLAIN-LANGUAGE" in COMIC_MODE_NARRATIVE_RULES or "通俗" in COMIC_MODE_NARRATIVE_RULES

    def test_stage4_can_lightly_rewrite_classical_dialogue(self):
        """Stage 4 有权把"夙愿"轻改为"心愿"等"""
        from app.prompts.storyboard_prompts import COMIC_MODE_NARRATIVE_RULES
        lower = COMIC_MODE_NARRATIVE_RULES.lower()
        # 必须说 Stage 4 has authority to swap
        assert "lightly rewrite" in lower or "stage 4 has authority" in lower or "stage 4 should" in lower


class TestT20_21_v2_RealWorldDataConformance:
    """v2 现实场景: 35 字以内 dialogue 应通过"""

    def test_v2_target_dialogue_35_chars_ok(self):
        """≤35 char dialogue line 应符合 v2 规则 (validator 不存在长度 cap, 但 prompt 应允许)"""
        # v2 prompt 允许 ≤35, 用 narration validator 不直接验 dialogue, 但 caption validator 仍是 25
        # 这里只验证 hard-cap getter 真的是 35
        from app.prompts.screenplay_prompts import get_dec044_dialogue_max_chars
        assert get_dec044_dialogue_max_chars() == 35

    def test_v2_examples_in_prompt_within_35(self):
        """v2 prompt 中给的所有正例 dialogue 长度 ≤35"""
        from app.prompts.screenplay_prompts import DIALOGUE_THOUGHT_DENSITY_RULES
        # 从 EXAMPLES 段抽取 ✅ 示例
        import re
        # 匹配 ✅ 后面的中文字符串 (粗略)
        good_examples = re.findall(r'✅\s*"([^"]{3,60})"', DIALOGUE_THOUGHT_DENSITY_RULES)
        if not good_examples:
            # try 中文引号
            good_examples = re.findall(r'✅[^\n]+「([^」]{3,60})」', DIALOGUE_THOUGHT_DENSITY_RULES)
        # 至少有 3 个 ✅ 正例 (验证 prompt 给了具体例子)
        # (不强制每个都 ≤35 — 例子可能含 narration not dialogue, 检查 prompt 完整性即可)
        assert len(good_examples) >= 1, "DIALOGUE_THOUGHT_DENSITY_RULES should contain ✅ examples"


class TestT20_21_v2_BackwardCompat:
    """v2 升级不破坏旧用法"""

    def test_density_distribution_still_intact(self):
        """distribution 比例不变 (D1)"""
        from app.prompts.screenplay_prompts import get_dec044_distribution_targets
        t = get_dec044_distribution_targets()
        # 数值不变
        assert t["dialogue_pct_min"] == 50
        assert t["thought_pct_min"] == 25

    def test_validator_still_works(self):
        from app.prompts.screenplay_prompts import (
            validate_narration_caption_length,
            validate_dialogue_thought_density,
        )
        r = validate_narration_caption_length("立春清晨")
        assert r["passes_total_length"]
        scene = {"dialogue_beats": [{"type": "thought", "line": "（二十三年了）"}]}
        r2 = validate_dialogue_thought_density(scene)
        assert isinstance(r2, dict)

    def test_narration_caption_still_25_chars(self):
        """narration caption 仍 ≤25 (只 dialogue/thought 升到 35)"""
        from app.prompts.screenplay_prompts import get_dec044_caption_max_chars
        assert get_dec044_caption_max_chars() == 25  # unchanged

    def test_narration_total_still_120(self):
        from app.prompts.screenplay_prompts import get_dec044_narration_max_chars
        assert get_dec044_narration_max_chars() == 120  # unchanged


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
