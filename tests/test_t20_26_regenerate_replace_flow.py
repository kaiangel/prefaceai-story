"""
T20-26 P0 Wave 4 — regenerate flow replace 策略测试 (Backend)

测试范围 (Backend 层 — 不依赖真 LLM 调用):
1. build_replace_user_prompt 构造正确 (含 forbidden + safe_alternatives + REPLACE 指令)
2. find_known_dark_terms 检测所有暗黑题材敏感词
3. strip_known_dark_terms 兜底机械删除 (长短语优先)
4. check_replace_effective 判定 append 模式 / 真 replace 模式
5. gather_scene_context_for_replace + gather_character_context_for_replace 提取素材
6. Universal: 不绑定 test19, 不绑定特定故事/角色

注意: 不测真 Anthropic API 调用 (需 mock 才能跑, 留给 Tester e2e).

Reference:
  - DEC-045 Wave 4
  - KEY_LEARNINGS #37 (Seedream 敏感词) + #38 (replace vs append)
  - .team-brain/analysis/TEST19_FULL_AUDIT_2026-05-19.md Phase 12
"""

import pytest

from app.services.shot_prompt_rewriter import (
    KNOWN_DARK_TERMS,
    SAFE_REPLACEMENT_HINTS,
    build_replace_user_prompt,
    check_replace_effective,
    find_known_dark_terms,
    gather_character_context_for_replace,
    gather_scene_context_for_replace,
    strip_known_dark_terms,
)


# =============================================================================
# Section 1: build_replace_user_prompt 构造
# =============================================================================
class TestBuildReplaceUserPrompt:
    """验证 user prompt 含 REPLACE 策略所有必备元素."""

    def test_contains_original_prompt_block(self):
        original = "A ghost of his grandfather appears in the snow."
        out = build_replace_user_prompt(original, "陈砚跪在雪地")
        assert "<original_prompt>" in out
        assert "</original_prompt>" in out
        assert original in out

    def test_contains_user_request_block(self):
        out = build_replace_user_prompt("orig", "陈砚跪在雪地, 不要叠影")
        assert "<user_request>" in out
        assert "陈砚跪在雪地, 不要叠影" in out

    def test_empty_intent_uses_safe_default(self):
        out = build_replace_user_prompt("orig", "")
        assert "<user_request>" in out
        assert "no specific change requested" in out

    def test_contains_forbidden_terms_list(self):
        out = build_replace_user_prompt("orig", "test")
        assert "<forbidden_terms_must_delete>" in out
        # 关键 test19 暗黑词
        assert "ghost" in out
        assert "double-exposure" in out
        assert "two faces merging" in out
        assert "identical jaw" in out
        assert "deceased emerges" in out

    def test_contains_safe_alternatives(self):
        out = build_replace_user_prompt("orig", "test")
        assert "<safe_alternatives>" in out
        assert "in fond memory" in out or "warm light" in out

    def test_contains_replace_not_append_directive(self):
        """核心 — 必须显式告诉 Haiku 是 REPLACE 不是 APPEND."""
        out = build_replace_user_prompt("orig", "test")
        assert "REPLACE, NOT APPEND" in out
        assert "DO NOT preserve sentences containing those forbidden phrases" in out

    def test_scene_context_block(self):
        scene = {
            "scene_id": "sc4",
            "location_name": "snowy graveyard",
            "lighting": "cold blue moonlight",
            "mood": "somber",
        }
        out = build_replace_user_prompt("orig", "test", scene_context=scene)
        assert "<scene_context>" in out
        assert "snowy graveyard" in out
        assert "cold blue moonlight" in out
        assert "somber" in out

    def test_scene_context_missing_safe(self):
        out = build_replace_user_prompt("orig", "test", scene_context=None)
        assert "<scene_context>" in out
        assert "no scene metadata available" in out

    def test_character_context_block(self):
        chars = [
            {
                "id": "c1",
                "name": "陈砚",
                "character_type": "human",
                "appearance_summary": "hair_color=black, eye_color=dark brown",
                "clothing_summary": "top=dark wool coat",
            }
        ]
        out = build_replace_user_prompt("orig", "test", character_context=chars)
        assert "<character_context>" in out
        assert "陈砚" in out
        assert "human" in out
        assert "dark wool coat" in out

    def test_character_context_empty_safe(self):
        out = build_replace_user_prompt("orig", "test", character_context=[])
        assert "<character_context>" in out
        assert "no character context available" in out

    def test_style_and_aspect_block(self):
        out = build_replace_user_prompt(
            "orig", "test", style_preset="ghibli", aspect_ratio="2:3"
        )
        assert "style_preset: ghibli" in out
        assert "aspect_ratio: 2:3" in out

    def test_universal_no_test19_hardcode(self):
        """不绑定 test19 / 陈砚 等具体内容."""
        out = build_replace_user_prompt("any prompt", "any intent")
        # 模板本身不含 test19 特定字符串 (test19 / 陈砚 只能由调用者传入)
        assert "test19" not in out
        assert "陈砚" not in out  # 没传 intent 时模板里不应硬编码


# =============================================================================
# Section 2: find_known_dark_terms 检测
# =============================================================================
class TestFindKnownDarkTerms:
    def test_empty_text(self):
        assert find_known_dark_terms("") == []
        assert find_known_dark_terms(None) == []

    def test_no_dark_terms(self):
        assert find_known_dark_terms("a peaceful snow scene") == []

    def test_single_ghost(self):
        hits = find_known_dark_terms("A ghost stands there")
        assert "ghost" in hits

    def test_case_insensitive(self):
        hits = find_known_dark_terms("A GHOST and a Phantom appeared")
        assert "ghost" in hits
        assert "phantom" in hits

    def test_word_boundary_single_word(self):
        """ghosts (plural) 应单独命中, 不影响 'ghost'."""
        hits = find_known_dark_terms("ghosts walked here")
        assert "ghosts" in hits

    def test_hyphenated_double_exposure(self):
        hits = find_known_dark_terms("a double-exposure photograph")
        assert "double-exposure" in hits

    def test_spaced_double_exposure(self):
        hits = find_known_dark_terms("a double exposure photograph")
        assert "double exposure" in hits

    def test_multi_word_phrases(self):
        text = "two faces merging into one with identical jaw"
        hits = find_known_dark_terms(text)
        assert "two faces merging" in hits
        assert "identical jaw" in hits

    def test_test19_shot15_real_prompt(self):
        """实测 test19 Shot 15 原 prompt 段落 (KEY_LEARNINGS #38 实证)."""
        text = (
            "Chen Yan kneels in the snow. The ghost of his grandfather emerges "
            "from a double-exposure overlay, two faces merging with identical jaw."
        )
        hits = find_known_dark_terms(text)
        assert "ghost" in hits
        assert "double-exposure" in hits
        assert "two faces merging" in hits
        assert "identical jaw" in hits

    def test_no_false_positive_substring(self):
        """'ghosted' 子串不应误命中 'ghost' (词边界规则)."""
        hits = find_known_dark_terms("the lighting was ghosted in post-production")
        # 'ghosted' 不是 'ghost' 边界匹配
        assert "ghost" not in hits

    def test_dedupe(self):
        """同一短语多次出现只算一次."""
        hits = find_known_dark_terms("ghost ghost ghost")
        assert hits.count("ghost") == 1


# =============================================================================
# Section 3: strip_known_dark_terms 兜底
# =============================================================================
class TestStripKnownDarkTerms:
    def test_empty_text(self):
        result, removed = strip_known_dark_terms("")
        assert result == ""
        assert removed == []

    def test_clean_text_unchanged(self):
        text = "A peaceful snow scene at dawn."
        result, removed = strip_known_dark_terms(text)
        assert result == text
        assert removed == []

    def test_ghost_replaced(self):
        result, removed = strip_known_dark_terms("A ghost walks here")
        assert "ghost" not in result.lower()
        assert "warm light" in result.lower()
        assert "ghost" in removed

    def test_double_exposure_replaced(self):
        result, removed = strip_known_dark_terms("a double-exposure photo")
        assert "double-exposure" not in result.lower()
        assert "split composition" in result.lower()
        assert "double-exposure" in removed

    def test_longer_phrase_first(self):
        """'two faces merging' 应优先替换, 不残留 'faces merging' 二次拼接."""
        result, removed = strip_known_dark_terms("two faces merging into one")
        assert "two faces merging" not in result.lower()
        assert "faces merging" not in result.lower()
        # 应正常变成 "two figures separated"
        assert "two figures separated" in result.lower()
        # 不应有 "two two" 重复词
        assert "two two" not in result.lower()

    def test_test19_full_strip(self):
        """test19 Shot 15 原 prompt 完整 strip 后应不含任何敏感词."""
        text = (
            "A solitary figure stands in the snow. A ghost of his grandfather "
            "emerges in a double-exposure overlay, two faces merging with "
            "identical jaw."
        )
        result, removed = strip_known_dark_terms(text)
        post = find_known_dark_terms(result)
        assert post == [], f"strip 后仍含: {post}, result={result!r}"
        assert "ghost" in removed
        assert "double-exposure" in removed
        assert "two faces merging" in removed
        assert "identical jaw" in removed

    def test_universal_diverse_themes(self):
        """跨题材 (科幻 / 武侠 / 都市) 都能 strip."""
        for text in [
            "a cyberpunk ghost in the neon street",
            "wuxia master sees the apparition of his fallen disciple",
            "modern city at night with two faces merging on a billboard",
        ]:
            result, _ = strip_known_dark_terms(text)
            assert find_known_dark_terms(result) == []


# =============================================================================
# Section 4: check_replace_effective
# =============================================================================
class TestCheckReplaceEffective:
    def test_clean_rewrite_effective(self):
        orig = "A ghost stands here"
        new = "A warm light shines here"
        r = check_replace_effective(orig, new)
        assert r["effective"] is True
        assert r["still_contains_dark_terms"] is False
        assert r["length_suspicious_append"] is False

    def test_append_mode_detected_by_dark_terms(self):
        """模拟旧 append 模式: 原 prompt + intent 追加 → 仍含原敏感词."""
        orig = "A ghost stands here"
        new = orig + " Additionally Chen Yan kneels in snow."
        r = check_replace_effective(orig, new)
        assert r["effective"] is False
        assert r["still_contains_dark_terms"] is True
        assert "ghost" in r["rewritten_dark_terms"]
        assert "ghost" in r["reason"]

    def test_length_suspicious_append(self):
        """rewritten 远长于 original → 怀疑 append (即使无敏感词)."""
        orig = "A simple scene"  # 14 chars
        new = "A simple scene" + " extended description " * 20  # >> 28 chars
        r = check_replace_effective(orig, new)
        assert r["length_suspicious_append"] is True
        assert r["effective"] is False
        assert "ratio" in r["reason"].lower()

    def test_length_ratio_under_2x_ok(self):
        """ratio 1.5x 应允许 (合法重写)."""
        orig = "short prompt"
        new = "short prompt rewritten more elegantly"  # ~3x...
        r = check_replace_effective(orig, new)
        # 这里 ratio 会 > 2 因 orig 太短, 改用更长的对照
        orig = "A young man stands at the threshold of the old wooden house. " * 3
        new = "A young man stands gracefully before the weathered timber building. " * 3
        r = check_replace_effective(orig, new)
        assert r["length_suspicious_append"] is False
        assert r["effective"] is True

    def test_test19_shot15_real_failure_detected(self):
        """实证: append 模式 (orig + intent 追加) 应被检测为 effective=False."""
        orig = (
            "A solitary figure stands in the snow. A ghost of his grandfather "
            "emerges in a double-exposure overlay."
        )
        # 模拟实测 test19 Haiku 输出 (原 prompt + intent 追加 + 没删 ghost)
        new = orig + " The character kneels in the snow, hands on the gravestone, distant view."
        r = check_replace_effective(orig, new)
        assert r["effective"] is False
        assert "ghost" in r["rewritten_dark_terms"]
        assert "double-exposure" in r["rewritten_dark_terms"]

    def test_empty_inputs(self):
        r = check_replace_effective("", "")
        assert r["original_len"] == 0
        assert r["rewritten_len"] == 0


# =============================================================================
# Section 5: gather_scene_context_for_replace
# =============================================================================
class TestGatherSceneContext:
    def test_empty_shot(self):
        assert gather_scene_context_for_replace({}) == {}

    def test_non_dict_shot(self):
        assert gather_scene_context_for_replace(None) == {}

    def test_pull_from_shot_directly(self):
        shot = {
            "scene_id": "sc4",
            "location_id": "loc1",
            "setting": "snowy graveyard",
            "lighting": "cold moonlight",
            "mood": "somber",
        }
        ctx = gather_scene_context_for_replace(shot)
        assert ctx["scene_id"] == "sc4"
        assert ctx["lighting"] == "cold moonlight"
        assert ctx["mood"] == "somber"

    def test_pull_from_camera_block(self):
        shot = {"scene_id": "sc4", "camera": {"lighting": "low key", "mood": "tense"}}
        ctx = gather_scene_context_for_replace(shot)
        assert ctx["lighting"] == "low key"
        assert ctx["mood"] == "tense"

    def test_merge_from_storyboard_scenes(self):
        shot = {"scene_id": "sc4"}
        storyboard = {
            "scenes": [
                {"scene_id": "sc1", "location_name": "wrong"},
                {
                    "scene_id": "sc4",
                    "location_name": "snowy graveyard",
                    "time_of_day": "dawn",
                },
            ]
        }
        ctx = gather_scene_context_for_replace(shot, storyboard)
        assert ctx["location_name"] == "snowy graveyard"
        assert ctx["time_of_day"] == "dawn"

    def test_universal_no_hardcode(self):
        """不绑定特定 scene_id 命名 (支持 sc4 / scene_4 / loc_001 等)."""
        for sid in ["sc4", "scene_4", "loc_001", "anything"]:
            shot = {"scene_id": sid}
            ctx = gather_scene_context_for_replace(shot)
            assert ctx["scene_id"] == sid


# =============================================================================
# Section 6: gather_character_context_for_replace
# =============================================================================
class TestGatherCharacterContext:
    def test_empty(self):
        assert gather_character_context_for_replace([], []) == []
        assert gather_character_context_for_replace(["c1"], []) == []

    def test_basic_human(self):
        chars = [
            {
                "id": "c1",
                "name": "Chen Yan",
                "character_type": "human",
                "physical": {"hair_color": "black", "eye_color": "brown"},
                "clothing": {"top": "wool coat", "style": "mourning"},
            }
        ]
        out = gather_character_context_for_replace(["c1"], chars)
        assert len(out) == 1
        assert out[0]["name"] == "Chen Yan"
        assert "hair_color=black" in out[0]["appearance_summary"]
        assert "wool coat" in out[0]["clothing_summary"]

    def test_filter_to_chars_in_scene(self):
        """chars_in_scene 只列 c1, c3 → 只返这两个."""
        chars = [
            {"id": "c1", "name": "A"},
            {"id": "c2", "name": "B"},
            {"id": "c3", "name": "C"},
        ]
        out = gather_character_context_for_replace(["c1", "c3"], chars)
        assert len(out) == 2
        names = {c["name"] for c in out}
        assert names == {"A", "C"}

    def test_missing_char_id_skipped(self):
        chars = [{"id": "c1", "name": "A"}]
        out = gather_character_context_for_replace(["c1", "nonexistent"], chars)
        assert len(out) == 1

    def test_universal_animal_type(self):
        """支持 animal / anthropomorphic_animal 等非 human 类型."""
        chars = [
            {
                "id": "c3",
                "name": "独眼鸦",
                "character_type": "animal",
                "physical": {"plumage_color": "iridescent black"},
            }
        ]
        out = gather_character_context_for_replace(["c3"], chars)
        assert out[0]["character_type"] == "animal"

    def test_fallback_appearance_description(self):
        """无 physical 字段时用 appearance / description 兜底."""
        chars = [
            {"id": "c1", "name": "Wraith", "appearance": "tall robed figure"}
        ]
        out = gather_character_context_for_replace(["c1"], chars)
        assert "tall robed figure" in out[0]["appearance_summary"]


# =============================================================================
# Section 7: End-to-end (acceptance — Backend 任务核心验收)
# =============================================================================
class TestE2EReplaceAcceptance:
    """
    PM 任务验收核心:
    输入: 原 prompt 含 "ghost of grandfather" + Founder intent "陈砚跪在雪地"
    期望: 调 build_replace_user_prompt + (模拟 LLM 真重写) 后 final prompt 不含 ghost
    """

    def test_user_prompt_explicitly_lists_forbidden(self):
        """build_replace_user_prompt 必须显式列出 ghost 作为 MUST DELETE."""
        original = (
            "A solitary figure stands in the snow. A ghost of his grandfather "
            "emerges in a double-exposure overlay, two faces merging with "
            "identical jaw."
        )
        intent = "陈砚跪在雪地, 不要叠影"
        out = build_replace_user_prompt(
            original_image_prompt=original,
            user_intent_zh=intent,
            scene_context={"location_name": "snowy graveyard", "lighting": "cold dawn"},
            character_context=[
                {
                    "id": "c1",
                    "name": "陈砚",
                    "character_type": "human",
                    "appearance_summary": "hair_color=black, eye_color=dark brown",
                    "clothing_summary": "top=dark wool coat",
                }
            ],
            style_preset="ghibli",
            aspect_ratio="2:3",
        )
        # 验证 user prompt 含所有需要 Haiku 删除的敏感词
        assert "ghost" in out
        assert "double-exposure" in out
        assert "two faces merging" in out
        assert "identical jaw" in out
        # 验证 Founder intent 透传
        assert "陈砚跪在雪地" in out
        # 验证素材完整
        assert "snowy graveyard" in out
        assert "dark wool coat" in out
        assert "ghibli" in out
        # 验证 REPLACE 指令
        assert "REPLACE, NOT APPEND" in out

    def test_mech_strip_fallback_works_when_llm_fails(self):
        """如 Haiku 仍返含 ghost 的 prompt, strip 兜底必须能去掉."""
        # 模拟 Haiku 仍 append (旧 bug 行为)
        original_with_ghost = "A ghost of grandfather appears, double-exposure overlay."
        haiku_returned = original_with_ghost + " Chen Yan kneels in snow."
        # 验证 check 标 False
        chk = check_replace_effective(original_with_ghost, haiku_returned)
        assert chk["effective"] is False
        # 兜底 strip
        cleaned, removed = strip_known_dark_terms(haiku_returned)
        # 兜底后必须无敏感词
        assert find_known_dark_terms(cleaned) == []
        assert "ghost" in removed
        assert "double-exposure" in removed

    def test_universal_does_not_break_clean_prompts(self):
        """干净 prompt 不应被任何 strip / replace 影响."""
        clean = (
            "Chen Yan kneels in fresh snow, holding a framed photograph. "
            "Warm dawn light. Distant trees blurred. ghibli style."
        )
        # find = 0
        assert find_known_dark_terms(clean) == []
        # strip 不变
        result, removed = strip_known_dark_terms(clean)
        assert result == clean
        assert removed == []
        # check effective vs self
        r = check_replace_effective(clean, clean)
        assert r["effective"] is True


# =============================================================================
# Section 8: Smoke — KNOWN_DARK_TERMS 完整性
# =============================================================================
class TestKnownDarkTermsCompleteness:
    """KEY_LEARNINGS #37 实证 — 列表必须含 test19 暴露的所有关键词."""

    @pytest.mark.parametrize("must_have_term", [
        "ghost",
        "double-exposure",
        "two faces merging",
        "identical jaw",
        "deceased emerges",
        "phantom",
        "apparition",
        "spectre",
    ])
    def test_required_term_present(self, must_have_term):
        assert must_have_term in KNOWN_DARK_TERMS, (
            f"KEY_LEARNINGS #37 要求 KNOWN_DARK_TERMS 含 '{must_have_term}'"
        )

    def test_safe_replacement_hints_nonempty(self):
        assert len(SAFE_REPLACEMENT_HINTS) > 200
        assert "in fond memory" in SAFE_REPLACEMENT_HINTS or "warm light" in SAFE_REPLACEMENT_HINTS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
