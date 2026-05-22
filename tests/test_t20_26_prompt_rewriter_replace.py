"""TASK-T20-FIXBATCH-5 Wave 4 RISK-T20-26 P0 — PromptRewriter REPLACE 策略测试.

测试目标 (test19 实证 5 次重生 Shot 15 全失败的真根因):
1. detect_seedream_tripwire() 准确识别暗黑题材敏感词
2. build_adjustment_user_prompt() auto 模式根据触发词正确切到 Mode B
3. SHOT_ADJUSTMENT_SYSTEM_PROMPT 包含 Mode B 完整规则 + 触发词清单 + verify 步骤
4. SAFETY_REWRITE_PROMPT (Sonnet 4.6 Pipeline 自动改写路径) 含暗黑题材替换字典
5. 触发词列表覆盖 KEY_LEARNINGS #37 全部 4 类
6. Mode A 行为不退化 (无触发词时仍走 surgical edit)

不依赖 LLM API. 纯 prompt 构建 + 触发词检测单元测试.

Usage:
    cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story
    python -m pytest tests/test_t20_26_prompt_rewriter_replace.py -v
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest


# ========================================================================
# Section 1: detect_seedream_tripwire() 准确性
# ========================================================================


class TestSeedreamTripwireDetection:
    """触发词检测器 — 4 类暗黑题材关键词全覆盖"""

    def test_module_importable(self):
        from app.prompts.shot_adjustment_prompt import (  # noqa: F401
            SHOT_ADJUSTMENT_SYSTEM_PROMPT,
            SEEDREAM_TRIPWIRE_KEYWORDS,
            detect_seedream_tripwire,
            build_adjustment_user_prompt,
        )

    def test_safe_prompt_no_trigger(self):
        """普通安全 prompt 不触发 (Mode A 默认)"""
        from app.prompts.shot_adjustment_prompt import detect_seedream_tripwire
        prompt = "Wide shot, eye level. A young woman wearing a red sweater walks in a city street at dusk. EXACTLY 1 character visible."
        result = detect_seedream_tripwire(prompt)
        assert not result["has_tripwire"]
        assert result["match_count"] == 0
        assert result["matched_keywords"] == []

    def test_empty_prompt_no_trigger(self):
        """空 prompt 不崩 + 不触发"""
        from app.prompts.shot_adjustment_prompt import detect_seedream_tripwire
        assert detect_seedream_tripwire("")["has_tripwire"] is False
        assert detect_seedream_tripwire(None)["has_tripwire"] is False  # type: ignore

    def test_category1_ghost_triggers(self):
        """Category 1 — 灵异类: ghost / spectral / phantom / apparition / haunted / vision of"""
        from app.prompts.shot_adjustment_prompt import detect_seedream_tripwire
        cases = [
            "ghost of grandfather emerges",
            "ghostly figure standing behind",
            "a spectral presence in the room",
            "phantom shape in the mist",
            "apparition of the deceased",
            "haunted corridor with cold light",
            "vision of his late mother",
            "a wraith stalks the hallway",
        ]
        for p in cases:
            result = detect_seedream_tripwire(p)
            assert result["has_tripwire"], f"failed to detect category-1 in: {p}"

    def test_category2_double_exposure_triggers(self):
        """Category 2 — 双重曝光类: double-exposure / face overlapping / faces merging / two faces"""
        from app.prompts.shot_adjustment_prompt import detect_seedream_tripwire
        cases = [
            "rendered as a double-exposure vision",
            "double exposure of two characters",
            "his face overlapping with his grandfather",
            "two faces merging into one",
            "faces blending in soft light",
            "the two faces overlap with exact contour alignment",
        ]
        for p in cases:
            result = detect_seedream_tripwire(p)
            assert result["has_tripwire"], f"failed to detect category-2 in: {p}"

    def test_category3_deceased_emerges_triggers(self):
        """Category 3 — 已故角色出现类"""
        from app.prompts.shot_adjustment_prompt import detect_seedream_tripwire
        cases = [
            "the deceased emerges from the shadow",
            "younger face emerges through his features",
            "older face surfaces in the mirror",
            "memory emerges in the warm light",
        ]
        for p in cases:
            result = detect_seedream_tripwire(p)
            assert result["has_tripwire"], f"failed to detect category-3 in: {p}"

    def test_category4_identical_features_triggers(self):
        """Category 4 — 身体特征重叠类"""
        from app.prompts.shot_adjustment_prompt import detect_seedream_tripwire
        cases = [
            "identical jaw to his grandfather",
            "identical scar bisecting the left brow",
            "identical face to the deceased",
            "exact contour alignment of the two figures",
        ]
        for p in cases:
            result = detect_seedream_tripwire(p)
            assert result["has_tripwire"], f"failed to detect category-4 in: {p}"

    def test_test19_shot15_real_prompt_triggers(self):
        """test19 Shot 15 原始 image_prompt (Founder 5 次重生失败的真案例)"""
        from app.prompts.shot_adjustment_prompt import detect_seedream_tripwire
        # 取自 output/36b303b2-2877-4ab4-9d61-6090e7d7282c/4_storyboard.json shot 15
        real_prompt = (
            "Eye-level close-up of Chen Yan's face — a human man with medium skin, "
            "rectangular face, thick arched brows with a pale scar bisecting the left brow, "
            "nearly black hooded eyes — rendered as a double-exposure vision: his living "
            "face occupies the foreground, eyes glistening and wide, lips trembling open "
            "in disbelief. Layered over his features like a ghost of light, the younger "
            "face of his grandfather Chen Huaishan emerges — identical rectangular jaw, "
            "same scar on the left brow, deep dark eyes, silver-white straight hair framing "
            "the face, earth-brown linen collar at the neck — the two faces overlapping "
            "with exact contour alignment."
        )
        result = detect_seedream_tripwire(real_prompt)
        assert result["has_tripwire"]
        # 至少命中 4 类中的多个 (粗略验证多触发词)
        assert result["match_count"] >= 4, f"expected ≥4 matches in real Shot 15, got {result['match_count']}: {result['matched_keywords']}"

    def test_case_insensitive(self):
        """大小写不敏感匹配"""
        from app.prompts.shot_adjustment_prompt import detect_seedream_tripwire
        assert detect_seedream_tripwire("GHOST of the deceased")["has_tripwire"]
        assert detect_seedream_tripwire("Double-Exposure Of Two Faces")["has_tripwire"]
        assert detect_seedream_tripwire("Identical JAW")["has_tripwire"]


# ========================================================================
# Section 2: SHOT_ADJUSTMENT_SYSTEM_PROMPT 含 Mode B 完整规则
# ========================================================================


class TestSystemPromptModeBStructure:
    """系统 prompt 必须含 Mode B 完整 7 步规则 + 触发词清单 + verify 步骤"""

    def test_two_mode_rule_present(self):
        from app.prompts.shot_adjustment_prompt import SHOT_ADJUSTMENT_SYSTEM_PROMPT
        assert "MODE A" in SHOT_ADJUSTMENT_SYSTEM_PROMPT
        assert "MODE B" in SHOT_ADJUSTMENT_SYSTEM_PROMPT
        assert "REPLACE-AND-CLEAN" in SHOT_ADJUSTMENT_SYSTEM_PROMPT
        assert "SURGICAL EDIT" in SHOT_ADJUSTMENT_SYSTEM_PROMPT

    def test_mode_b_strip_keywords_listed(self):
        """Mode B 必须列出所有 4 类触发词的 strip 指令"""
        from app.prompts.shot_adjustment_prompt import SHOT_ADJUSTMENT_SYSTEM_PROMPT
        # Category 1: 灵异类
        assert "ghost" in SHOT_ADJUSTMENT_SYSTEM_PROMPT.lower()
        assert "spectral" in SHOT_ADJUSTMENT_SYSTEM_PROMPT.lower()
        assert "apparition" in SHOT_ADJUSTMENT_SYSTEM_PROMPT.lower()
        # Category 2: 双重曝光类
        assert "double-exposure" in SHOT_ADJUSTMENT_SYSTEM_PROMPT.lower()
        assert "two faces" in SHOT_ADJUSTMENT_SYSTEM_PROMPT.lower() or "face overlap" in SHOT_ADJUSTMENT_SYSTEM_PROMPT.lower()
        # Category 3: 已故角色出现类
        assert "emerges" in SHOT_ADJUSTMENT_SYSTEM_PROMPT.lower()
        assert "deceased" in SHOT_ADJUSTMENT_SYSTEM_PROMPT.lower()
        # Category 4: 身体特征重叠类
        assert "identical jaw" in SHOT_ADJUSTMENT_SYSTEM_PROMPT.lower()

    def test_mode_b_rewrite_strategy_present(self):
        """Mode B 必须明确说"完全重写从头"+"不 patch 原文本"+"不 append" """
        from app.prompts.shot_adjustment_prompt import SHOT_ADJUSTMENT_SYSTEM_PROMPT
        # "COMPLETELY REWRITE" / "from scratch" / "DO NOT patch" / "DO NOT append"
        lower = SHOT_ADJUSTMENT_SYSTEM_PROMPT.lower()
        assert "completely rewrite" in lower or "rewrite the image_prompt from scratch" in lower
        assert "do not append" in lower or "do not patch" in lower

    def test_mode_b_safe_alternatives_provided(self):
        """Mode B 必须给具体安全替换示例 (ghost → warm symbolic memory 等)"""
        from app.prompts.shot_adjustment_prompt import SHOT_ADJUSTMENT_SYSTEM_PROMPT
        lower = SHOT_ADJUSTMENT_SYSTEM_PROMPT.lower()
        # 至少 1 个 ghost → 安全替换示例
        assert "warm symbolic memory" in lower or "lingering presence" in lower or "golden halo" in lower

    def test_mode_b_verify_step_present(self):
        """Mode B 必须含输出前 verify scan 步骤"""
        from app.prompts.shot_adjustment_prompt import SHOT_ADJUSTMENT_SYSTEM_PROMPT
        lower = SHOT_ADJUSTMENT_SYSTEM_PROMPT.lower()
        assert "verify" in lower or "scan" in lower
        # 必须明确指令: 如果残留就 rewrite
        assert "rewrite" in lower


# ========================================================================
# Section 3: build_adjustment_user_prompt() auto 模式决策
# ========================================================================


class TestBuildAdjustmentUserPromptAutoMode:
    """build_adjustment_user_prompt() auto 模式根据触发词自动切 Mode A/B"""

    def test_auto_mode_safe_prompt_picks_mode_a(self):
        """安全 prompt + auto → Mode A"""
        from app.prompts.shot_adjustment_prompt import build_adjustment_user_prompt
        safe_prompt = "Wide shot. A young woman in a red sweater walks down a city street. EXACTLY 1 character visible."
        user_msg = build_adjustment_user_prompt(safe_prompt, "让她转过身来", mode="auto")
        assert "MODE A" in user_msg
        assert "MODE B" not in user_msg.split("active_mode")[1].split("</active_mode>")[0] if "active_mode" in user_msg else True
        assert "minimal modification" in user_msg.lower() or "surgical" in user_msg.lower()

    def test_auto_mode_dark_prompt_picks_mode_b(self):
        """含 ghost / double-exposure 的 prompt + auto → Mode B"""
        from app.prompts.shot_adjustment_prompt import build_adjustment_user_prompt
        dark_prompt = (
            "Eye-level close-up of Chen Yan rendered as a double-exposure vision: "
            "his living face in foreground, the ghost of his grandfather emerges "
            "with identical jaw and same scar, two faces overlapping with exact contour alignment."
        )
        user_msg = build_adjustment_user_prompt(dark_prompt, "陈砚跪在雪地", mode="auto")
        assert "MODE B" in user_msg
        assert "REPLACE-AND-CLEAN" in user_msg
        assert "strip ALL" in user_msg or "completely rewrite" in user_msg.lower()
        # 必须把触发词列在提示里 (debugging 友好)
        assert "ghost" in user_msg.lower() or "double-exposure" in user_msg.lower()

    def test_forced_mode_b_overrides_auto(self):
        """mode='B' 强制走 Mode B, 即使 prompt 安全"""
        from app.prompts.shot_adjustment_prompt import build_adjustment_user_prompt
        safe_prompt = "A young woman walks in a city street."
        user_msg = build_adjustment_user_prompt(safe_prompt, "改变光线", mode="B")
        assert "MODE B" in user_msg

    def test_forced_mode_a_overrides_auto(self):
        """mode='A' 强制走 Mode A, 即使 prompt 含触发词"""
        from app.prompts.shot_adjustment_prompt import build_adjustment_user_prompt
        dark_prompt = "ghost emerges in the room"
        user_msg = build_adjustment_user_prompt(dark_prompt, "改光线", mode="A")
        assert "MODE A" in user_msg

    def test_user_intent_preserved_in_message(self):
        """用户中文意图必须在 user_msg 中"""
        from app.prompts.shot_adjustment_prompt import build_adjustment_user_prompt
        intent = "陈砚跪在雪地, 双手按在墓碑上, 远景, 不要叠影"
        user_msg = build_adjustment_user_prompt("ghost prompt", intent, mode="auto")
        assert intent in user_msg

    def test_original_prompt_preserved_in_message(self):
        """原 prompt 必须在 user_msg 的 <original_prompt> tag 内"""
        from app.prompts.shot_adjustment_prompt import build_adjustment_user_prompt
        orig = "a unique sentinel string 12345"
        user_msg = build_adjustment_user_prompt(orig, "test", mode="auto")
        assert orig in user_msg
        assert "<original_prompt>" in user_msg


# ========================================================================
# Section 4: SAFETY_REWRITE_PROMPT (Sonnet 4.6 Pipeline 自动改写路径) 升级
# ========================================================================


class TestSafetyRewritePromptDarkFantasy:
    """prompt_safety_rewrite.py 必须新增暗黑题材替换字典 (DEC-045 T20-26)"""

    def test_safety_rewrite_prompt_importable(self):
        from app.prompts.prompt_safety_rewrite import SAFETY_REWRITE_PROMPT  # noqa: F401

    def test_seedream_tripwire_section_present(self):
        """SAFETY_REWRITE_PROMPT 必须含 §2.B SEEDREAM DARK-FANTASY TRIPWIRES 块"""
        from app.prompts.prompt_safety_rewrite import SAFETY_REWRITE_PROMPT
        assert "SEEDREAM DARK-FANTASY TRIPWIRES" in SAFETY_REWRITE_PROMPT
        assert "DEC-045 T20-26" in SAFETY_REWRITE_PROMPT

    def test_4_categories_in_safety_rewrite(self):
        """4 类敏感词全部出现在替换表中"""
        from app.prompts.prompt_safety_rewrite import SAFETY_REWRITE_PROMPT
        lower = SAFETY_REWRITE_PROMPT.lower()
        # Category 1
        assert "ghost" in lower
        assert "spectral" in lower
        # Category 2
        assert "double-exposure" in lower
        assert "face overlap" in lower or "faces overlapping" in lower
        # Category 3
        assert "deceased emerges" in lower or "younger face emerges" in lower
        # Category 4
        assert "identical jaw" in lower or "identical face" in lower

    def test_safe_alternatives_provided(self):
        """每个敏感词都有具体安全替换 (不能只列禁忌不给方案)"""
        from app.prompts.prompt_safety_rewrite import SAFETY_REWRITE_PROMPT
        lower = SAFETY_REWRITE_PROMPT.lower()
        assert "warm symbolic memory" in lower or "lingering presence" in lower
        assert "golden halo" in lower or "soft golden" in lower

    def test_verify_step_present(self):
        """§3.C 必须含输出后 verify scan 指令"""
        from app.prompts.prompt_safety_rewrite import SAFETY_REWRITE_PROMPT
        assert "CRITICAL VERIFY" in SAFETY_REWRITE_PROMPT or "scan your output" in SAFETY_REWRITE_PROMPT.lower()


# ========================================================================
# Section 5: Mode A 行为不退化 (核心向后兼容)
# ========================================================================


class TestModeABackwardCompat:
    """Mode A 仍按原 minimal modification 规则工作 — 不退化"""

    def test_mode_a_rules_1_through_9_present(self):
        """Rule 1-9 (Mode A 旧规则) 全部保留"""
        from app.prompts.shot_adjustment_prompt import SHOT_ADJUSTMENT_SYSTEM_PROMPT
        for i in range(1, 10):
            assert f"Rule {i}" in SHOT_ADJUSTMENT_SYSTEM_PROMPT, f"missing Rule {i}"

    def test_mode_a_minimal_modification_intact(self):
        """Rule 1 仍说 MINIMAL MODIFICATION (Mode A only)"""
        from app.prompts.shot_adjustment_prompt import SHOT_ADJUSTMENT_SYSTEM_PROMPT
        assert "MINIMAL MODIFICATION" in SHOT_ADJUSTMENT_SYSTEM_PROMPT

    def test_default_mode_is_auto(self):
        """build_adjustment_user_prompt() 默认 mode='auto' 不破坏旧调用契约"""
        from app.prompts.shot_adjustment_prompt import build_adjustment_user_prompt
        import inspect
        sig = inspect.signature(build_adjustment_user_prompt)
        assert sig.parameters["mode"].default == "auto"

    def test_existing_old_signature_compat(self):
        """旧调用方 (chapters.py L2070-2074 只传 2 个 args) 仍能工作"""
        from app.prompts.shot_adjustment_prompt import build_adjustment_user_prompt
        result = build_adjustment_user_prompt(
            "Wide shot of city street.",
            "改成夜景"
        )
        assert isinstance(result, str)
        assert "city street" in result
        assert "改成夜景" in result


# ========================================================================
# Section 6: 端到端集成 — Founder Shot 15 4 次重生场景
# ========================================================================


class TestEndToEndShot15Scenario:
    """模拟 Founder 5/19 21:51-22:00 4 次重生 Shot 15 的真实场景"""

    @pytest.fixture
    def shot15_prompt(self):
        """test19 Shot 15 原始 image_prompt (含 ghost / double-exposure)"""
        return (
            "Eye-level close-up of Chen Yan's face — a human man with medium skin, "
            "rectangular face, thick arched brows with a pale scar bisecting the left brow, "
            "nearly black hooded eyes — rendered as a double-exposure vision: his living "
            "face occupies the foreground, eyes glistening and wide, lips trembling open "
            "in disbelief. Layered over his features like a ghost of light, the younger "
            "face of his grandfather Chen Huaishan emerges — identical rectangular jaw, "
            "same scar on the left brow, deep dark eyes, silver-white straight hair framing "
            "the face, earth-brown linen collar at the neck — the two faces overlapping "
            "with exact contour alignment."
        )

    def test_founder_intent_1_auto_picks_mode_b(self, shot15_prompt):
        """Founder 第 1 次: "let it look more dramatic" → auto 应选 Mode B"""
        from app.prompts.shot_adjustment_prompt import build_adjustment_user_prompt
        msg = build_adjustment_user_prompt(shot15_prompt, "让画面更戏剧化", mode="auto")
        assert "MODE B" in msg

    def test_founder_intent_4_complete_scene_change(self, shot15_prompt):
        """Founder 第 4 次完全换场景: "陈砚跪在雪地, 双手按在墓碑上, 远景" → Mode B 仍强制 strip"""
        from app.prompts.shot_adjustment_prompt import build_adjustment_user_prompt
        msg = build_adjustment_user_prompt(
            shot15_prompt,
            "陈砚跪在雪地, 双手按在墓碑上, 远景, 不要叠影",
            mode="auto"
        )
        assert "MODE B" in msg
        # Founder intent 必须保留 (Mode B 用它做新 prompt 主轴)
        assert "雪地" in msg
        assert "墓碑" in msg

    def test_tripwire_keywords_passed_to_haiku(self, shot15_prompt):
        """检测到的触发词必须在 user_msg 里告诉 Haiku (debugging 友好)"""
        from app.prompts.shot_adjustment_prompt import build_adjustment_user_prompt, detect_seedream_tripwire
        msg = build_adjustment_user_prompt(shot15_prompt, "test", mode="auto")
        detection = detect_seedream_tripwire(shot15_prompt)
        assert detection["has_tripwire"]
        # user_msg 必须含 seedream_tripwires_detected tag
        assert "seedream_tripwires_detected" in msg
        # 至少有 1 个触发词出现 (而非空)
        assert "ghost" in msg.lower() or "double-exposure" in msg.lower() or "identical" in msg.lower()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
