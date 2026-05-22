"""TASK-T20-FIXBATCH-6 Wave 5 RISK-T20-28 P0 — DEC-046 v3 通用叙事原则重构.

测试目标:
1. screenplay_prompts.py 新增 DEC-046 v3 模块的结构 / 可 import / 完整性
2. detect_narrative_cluster() 真按 style + plot 自动选 cluster (8 cluster)
3. CLUSTER_DEFINITIONS 8 cluster 完整且符合 TOP 5 设计
4. validate_scene_self_evaluation() 真 enforce 85% KPI 门槛
5. validate_emphasis_usage() 真检测 climax shot 是否有 emphasis
6. storyboard_prompts.py 新增 6 个 Stage 4 v3 规则块完整
7. 6 cluster mock 故事跨题材 (Mock LLM, 不调真 API), 验证 cluster 分发逻辑

不依赖 LLM API / DB / backend 服务. 纯 prompt + validator 单测.

Usage:
    cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story
    python -m pytest tests/test_t20_28_cross_genre_principles.py -v
"""

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest


# ============================================================================
# Section 1: screenplay_prompts.py v3 module structure
# ============================================================================


class TestScreenplayPromptsV3ModuleStructure:
    """v3 模块结构完整性 — 9 个新规则块 + 全 helpers + composed block"""

    def test_module_importable(self):
        from app.prompts import screenplay_prompts  # noqa: F401

    def test_all_v3_blocks_present(self):
        from app.prompts import screenplay_prompts as sp
        required = [
            "CLUSTER_TOP5_DISPATCHER",
            "VIEWPOINT_SELECTION_RULES",
            "STYLE_LANGUAGE_MAPPING",
            "NARRATIVE_RHYTHM_RULES",
            "EMPHASIS_RULES",
            "CHARACTER_ANCHORING_RULES",
            "AUDIENCE_EXPECTATION_RULES",
            "NARRATIVE_STRUCTURE_RULES",
            "SELF_EVALUATION_85_KPI",
            "DEC046_V3_NARRATIVE_PRINCIPLES",
            "DEC046_V3_OUTPUT_EXAMPLE",
        ]
        for name in required:
            assert hasattr(sp, name), f"missing v3 export: {name}"
            value = getattr(sp, name)
            assert isinstance(value, str), f"{name} should be str"
            assert len(value) > 200, f"{name} too short ({len(value)} chars)"

    def test_v3_helpers_present(self):
        from app.prompts.screenplay_prompts import (
            CLUSTER_DEFINITIONS,
            detect_narrative_cluster,
            get_cluster_top5_principles,
            get_cluster_default_viewpoint,
            get_85_kpi_threshold,
            get_emphasis_marker_chars,
            get_v3_required_scene_fields,
            validate_scene_self_evaluation,
            validate_emphasis_usage,
        )
        # 全 callable
        assert callable(detect_narrative_cluster)
        assert callable(validate_scene_self_evaluation)

    def test_composed_block_includes_all_modules(self):
        from app.prompts.screenplay_prompts import DEC046_V3_NARRATIVE_PRINCIPLES as v3
        # 顶部模块名 / 关键标记应出现在 composed block 中
        markers = [
            "CLUSTER DISPATCHER",
            "VIEWPOINT SELECTION",
            "LANGUAGE STYLE MAPPING",
            "NARRATIVE RHYTHM",
            "EMPHASIS RULES",
            "CHARACTER ANCHORING",
            "AUDIENCE EXPECTATION",
            "NARRATIVE STRUCTURE",
            "SELF-EVALUATION 85%",
        ]
        for m in markers:
            assert m in v3, f"composed block missing marker: {m}"

    def test_v3_output_example_has_all_new_fields(self):
        from app.prompts.screenplay_prompts import DEC046_V3_OUTPUT_EXAMPLE as ex
        new_fields = [
            "narrative_cluster",
            "cluster_reasoning",
            "top5_principles_applied",
            "narrative_viewpoint",
            "narrative_phase",
            "structure_position_pct",
            "target_text_density",
            "narrative_structure",
            "scene_self_evaluation",
            "reader_comprehension_score",
            "key_info_conveyed_via_visible_text",
            "info_only_in_narration_prose",
            "emphasis_words",
        ]
        for f in new_fields:
            assert f in ex, f"v3 output example missing field: {f}"


# ============================================================================
# Section 2: CLUSTER_DEFINITIONS 完整性 (8 cluster × TOP 5 全覆盖)
# ============================================================================


class TestClusterDefinitions:
    """8 cluster 完整且 TOP 5 不为空, viewpoint_default 在 3 类范围"""

    def test_all_8_clusters_present(self):
        from app.prompts.screenplay_prompts import CLUSTER_DEFINITIONS
        for i in range(1, 9):
            cid = f"C{i}"
            assert cid in CLUSTER_DEFINITIONS, f"cluster {cid} missing"

    def test_each_cluster_has_required_fields(self):
        from app.prompts.screenplay_prompts import CLUSTER_DEFINITIONS
        for cid, defn in CLUSTER_DEFINITIONS.items():
            assert "name" in defn, f"{cid} missing name"
            assert "genres" in defn and len(defn["genres"]) > 0
            assert "style_keywords" in defn and len(defn["style_keywords"]) > 0
            assert "top5" in defn and len(defn["top5"]) == 5, (
                f"{cid} top5 should be exactly 5 items, got {len(defn.get('top5', []))}"
            )
            assert "viewpoint_default" in defn

    def test_viewpoint_default_in_valid_set(self):
        from app.prompts.screenplay_prompts import CLUSTER_DEFINITIONS
        valid = {"first_person", "third_objective", "narrator_omniscient"}
        for cid, defn in CLUSTER_DEFINITIONS.items():
            vp = defn["viewpoint_default"]
            assert vp in valid, f"{cid} viewpoint '{vp}' not in {valid}"


# ============================================================================
# Section 3: detect_narrative_cluster() 6 cluster mock 故事跨题材
# ============================================================================


class TestClusterDetectionAcrossSixGenres:
    """6 cluster × 6 mock 故事 — 验证 LLM 真按 style + plot 选 cluster"""

    # 6 cluster 测试样本 (DEC-046 PM 推荐 Founder 测的样本)
    SAMPLES = [
        # (sample_name, style, plot_text, expected_cluster)
        (
            "romance_C1",
            "korean_webtoon",
            "程序员苏晨办公室暗恋部门经理林浩, 终于在加班一起的雨夜告白",
            "C1",
        ),
        (
            "horror_C2",
            "dark_fantasy",
            "深夜独自加班, 电梯门打开, 镜中多了一张陌生的脸. 凶手身份真相调查",
            "C2",
        ),
        (
            "wuxia_C5",
            "wuxia",
            "剑山派师妹凌雪复仇, 师父被害, 江湖论剑山下决战",
            "C5",
        ),
        (
            "fairytale_C4",
            "children_book",
            "小熊毛毛在森林里捡到一颗红苹果, 想跟苹果女孩做朋友, 学会分享",
            "C4",
        ),
        (
            "scifi_C6",
            "scifi",
            "AI 客服阿尔法在第 47 次时间循环中识别出来电者是它的儿子. 未来 2147 年",
            "C6",
        ),
        (
            "urban_C8",
            "urban_life",
            "都市白领老陈办公室 8 年没修的咖啡机突然坏掉, 引发同事间的奇遇",
            "C8",
        ),
    ]

    @pytest.mark.parametrize("name,style,plot,expected", SAMPLES)
    def test_detect_cluster_for_sample(self, name, style, plot, expected):
        from app.prompts.screenplay_prompts import detect_narrative_cluster
        result = detect_narrative_cluster(style=style, plot_text=plot)
        assert result == expected, (
            f"sample {name}: expected {expected}, got {result} "
            f"(style={style}, plot={plot[:30]}...)"
        )

    def test_default_to_c8_for_empty_input(self):
        from app.prompts.screenplay_prompts import detect_narrative_cluster
        assert detect_narrative_cluster() == "C8"
        assert detect_narrative_cluster(style="", plot_text="") == "C8"

    def test_style_keyword_priority_over_plot(self):
        """style 字段精确匹配优先于 plot 关键词"""
        from app.prompts.screenplay_prompts import detect_narrative_cluster
        # style=wuxia 强匹配 C5, 即使 plot 含恋爱词
        result = detect_narrative_cluster(
            style="wuxia",
            plot_text="师父和徒弟之间产生暗恋",
        )
        assert result == "C5"


# ============================================================================
# Section 4: validate_scene_self_evaluation() 85% KPI 门槛
# ============================================================================


class TestSelfEvaluation85KPI:
    """validate_scene_self_evaluation 真 enforce score ≥ 0.85"""

    def test_passes_when_score_above_threshold(self):
        from app.prompts.screenplay_prompts import validate_scene_self_evaluation
        scene = {
            "scene_id": 1,
            "scene_self_evaluation": {
                "reader_comprehension_score": 0.92,
                "reader_comprehension_reasoning": "OK",
                "info_only_in_narration_prose": [],
            }
        }
        result = validate_scene_self_evaluation(scene)
        assert result["has_self_evaluation"] is True
        assert result["passes_85_kpi"] is True
        assert result["score"] == 0.92

    def test_fails_when_score_below_threshold(self):
        from app.prompts.screenplay_prompts import validate_scene_self_evaluation
        scene = {
            "scene_id": 1,
            "scene_self_evaluation": {
                "reader_comprehension_score": 0.70,
                "info_only_in_narration_prose": [],
            }
        }
        result = validate_scene_self_evaluation(scene)
        assert result["passes_85_kpi"] is False
        assert "门槛" in " ".join(result["issues"])

    def test_at_threshold_passes(self):
        from app.prompts.screenplay_prompts import validate_scene_self_evaluation
        scene = {"scene_self_evaluation": {"reader_comprehension_score": 0.85}}
        result = validate_scene_self_evaluation(scene)
        assert result["passes_85_kpi"] is True

    def test_missing_self_evaluation_fails(self):
        from app.prompts.screenplay_prompts import validate_scene_self_evaluation
        scene = {"scene_id": 1}
        result = validate_scene_self_evaluation(scene)
        assert result["has_self_evaluation"] is False
        assert result["passes_85_kpi"] is False

    def test_info_only_in_narration_flagged(self):
        """info_only_in_narration_prose 非空 = 警告 (关键 plot 未补到 visible text)"""
        from app.prompts.screenplay_prompts import validate_scene_self_evaluation
        scene = {
            "scene_self_evaluation": {
                "reader_comprehension_score": 0.95,
                "info_only_in_narration_prose": ["主角发现真相", "时间是 1949"],
            }
        }
        result = validate_scene_self_evaluation(scene)
        # 整体 pass (score 高) 但 issues 含警告
        assert any("info_only_in_narration_prose" in i for i in result["issues"])

    def test_non_numeric_score_fails_gracefully(self):
        from app.prompts.screenplay_prompts import validate_scene_self_evaluation
        scene = {
            "scene_self_evaluation": {"reader_comprehension_score": "abc"}
        }
        result = validate_scene_self_evaluation(scene)
        assert result["passes_85_kpi"] is False
        assert result["score"] is None


# ============================================================================
# Section 5: validate_emphasis_usage() climax 必有 emphasis
# ============================================================================


class TestEmphasisValidator:
    """climax scene 必须含 !!! 或 emphasis_words 否则 fail"""

    def test_climax_with_inline_marker_passes(self):
        from app.prompts.screenplay_prompts import validate_emphasis_usage
        scene = {
            "narrative_phase": "climax",
            "dialogue_beats": [
                {"type": "dialogue", "speaker": "char_001",
                 "line": "我恨你！！！"}
            ],
            "narration": "",
        }
        result = validate_emphasis_usage(scene)
        assert result["passes"] is True
        assert result["emphasis_marker_count"] == 1
        assert result["is_climax"] is True

    def test_climax_without_emphasis_fails(self):
        from app.prompts.screenplay_prompts import validate_emphasis_usage
        scene = {
            "narrative_phase": "climax",
            "dialogue_beats": [
                {"type": "dialogue", "speaker": "char_001",
                 "line": "我恨你。"}
            ],
            "narration": "她说了她恨他。",
        }
        result = validate_emphasis_usage(scene)
        assert result["passes"] is False
        assert "climax" in " ".join(result["issues"]).lower()

    def test_non_climax_no_emphasis_ok(self):
        from app.prompts.screenplay_prompts import validate_emphasis_usage
        scene = {
            "narrative_phase": "setup",
            "dialogue_beats": [
                {"type": "dialogue", "speaker": "char_001", "line": "你好。"}
            ],
            "narration": "深秋傍晚。",
        }
        result = validate_emphasis_usage(scene)
        assert result["passes"] is True
        assert result["emphasis_marker_count"] == 0

    def test_climax_with_emphasis_words_passes(self):
        from app.prompts.screenplay_prompts import validate_emphasis_usage
        scene = {
            "narrative_phase": "climax",
            "dialogue_beats": [
                {"type": "dialogue", "speaker": "char_001",
                 "line": "你居然知道。",
                 "emphasis_words": ["居然"]}
            ],
            "narration": "",
        }
        result = validate_emphasis_usage(scene)
        assert result["passes"] is True
        assert result["emphasis_words_count"] == 1

    def test_too_many_inline_markers_warning(self):
        from app.prompts.screenplay_prompts import validate_emphasis_usage
        scene = {
            "narrative_phase": "climax",
            "dialogue_beats": [
                {"type": "dialogue", "speaker": "c1", "line": "啊！！！"},
                {"type": "dialogue", "speaker": "c2", "line": "啊！！！"},
                {"type": "dialogue", "speaker": "c3", "line": "啊！！！"},
            ],
            "narration": "",
        }
        result = validate_emphasis_usage(scene)
        assert any("失去强调意义" in i for i in result["issues"])

    def test_full_width_marker_recognized(self):
        from app.prompts.screenplay_prompts import validate_emphasis_usage
        scene = {
            "narrative_phase": "climax",
            "dialogue_beats": [
                {"type": "dialogue", "speaker": "c1", "line": "好！！！"},
            ],
            "narration": "",
        }
        result = validate_emphasis_usage(scene)
        assert result["emphasis_marker_count"] == 1


# ============================================================================
# Section 6: storyboard_prompts.py v3 Stage 4 6 个规则块
# ============================================================================


class TestStoryboardPromptsV3Modules:
    """Stage 4 v3 6 个新规则块 + helpers"""

    def test_module_importable(self):
        from app.prompts import storyboard_prompts  # noqa: F401

    def test_six_new_stage4_blocks_present(self):
        from app.prompts import storyboard_prompts as sb
        required = [
            "IMAGE_TEXT_COMPLEMENT_RULES",
            "MINIMAL_DIALOGUE_RULES",
            "TIMELINE_JUMP_MARKER_RULES",
            "MULTI_CHARACTER_DIALOGUE_RULES",
            "METAPHOR_SYMBOL_RULES",
            "CULTURAL_CONTEXT_RULES",
            "DEC046_V3_STAGE4_RULES",
        ]
        for name in required:
            assert hasattr(sb, name), f"missing v3 Stage 4 export: {name}"
            value = getattr(sb, name)
            assert isinstance(value, str)
            assert len(value) > 200, f"{name} too short ({len(value)} chars)"

    def test_composed_stage4_block_includes_all_modules(self):
        from app.prompts.storyboard_prompts import DEC046_V3_STAGE4_RULES as v3
        markers = [
            "IMAGE-TEXT COMPLEMENT",
            "MINIMAL DIALOGUE",
            "TIMELINE JUMP MARKER",
            "MULTI-CHARACTER DIALOGUE",
            "METAPHOR & SYMBOL",
            "CULTURAL CONTEXT",
        ]
        for m in markers:
            assert m in v3, f"composed Stage 4 block missing: {m}"

    def test_v3_stage4_helpers_present(self):
        from app.prompts.storyboard_prompts import (
            get_dec046_v3_stage4_module_names,
            get_minimal_dialogue_acceptable_examples,
            get_timeline_jump_marker_templates,
            get_symbol_common_clusters,
            get_cluster_cultural_palette,
            validate_text_overlay_complements_image,
        )
        assert callable(get_dec046_v3_stage4_module_names)
        names = get_dec046_v3_stage4_module_names()
        assert len(names) == 6

    def test_minimal_dialogue_acceptable_examples_overrides_old_rejects(self):
        """v3 撤销旧 D2 反例: '怎么了?' '你来了' '走吧' 应该 OK (在 C1/C7)"""
        from app.prompts.storyboard_prompts import get_minimal_dialogue_acceptable_examples
        examples = get_minimal_dialogue_acceptable_examples()
        # 应该含 1-3 字 dialogue 例
        assert any(len(e) <= 4 for e in examples), "v3 应认可 1-3 字 dialogue"
        # 应该跨多个 cluster
        assert "好。" in examples or "嗯。" in examples
        assert "嘿嘿。" in examples or "好甜!" in examples

    def test_timeline_jump_marker_templates_12_categories(self):
        from app.prompts.storyboard_prompts import get_timeline_jump_marker_templates
        templates = get_timeline_jump_marker_templates()
        # 12 类
        assert len(templates) >= 10, f"expected ≥10 categories, got {len(templates)}"
        # 每类至少 1 个模板
        for category, items in templates.items():
            assert len(items) >= 1, f"category {category} empty"

    def test_symbol_clusters_mapping(self):
        from app.prompts.storyboard_prompts import get_symbol_common_clusters
        symbols = get_symbol_common_clusters()
        # 应含常见象征物
        assert "银扣" in symbols
        assert "镜子" in symbols
        assert "苹果" in symbols
        # 每个有 meaning + clusters
        for sym, info in symbols.items():
            assert "meaning" in info
            assert "clusters" in info

    def test_cluster_cultural_palette_8_clusters(self):
        from app.prompts.storyboard_prompts import get_cluster_cultural_palette
        for i in range(1, 9):
            cid = f"C{i}"
            palette = get_cluster_cultural_palette(cid)
            assert len(palette) > 0, f"{cid} cultural palette empty"


# ============================================================================
# Section 7: validate_text_overlay_complements_image() ITC-1 检测
# ============================================================================


class TestTextOverlayComplementsImage:
    """v3 ITC-1: text_overlay 不能纯描述 image (浪费)"""

    def test_pure_image_description_flagged(self):
        from app.prompts.storyboard_prompts import validate_text_overlay_complements_image
        result = validate_text_overlay_complements_image(
            image_prompt="A woman crying in the rain, side view, soft light",
            overlay_text="她在哭。",
        )
        assert result["passes"] is False
        assert result["duplicate_score"] > 0

    def test_complementary_thought_passes(self):
        from app.prompts.storyboard_prompts import validate_text_overlay_complements_image
        result = validate_text_overlay_complements_image(
            image_prompt="A woman crying in the rain, side view, soft light",
            overlay_text="（其实我只是想他回头看我一眼。）",
        )
        assert result["passes"] is True

    def test_reveal_caption_passes(self):
        from app.prompts.storyboard_prompts import validate_text_overlay_complements_image
        result = validate_text_overlay_complements_image(
            image_prompt="Close-up of a gravestone in soft sunset light",
            overlay_text="碑上刻着：陈砚。",
        )
        assert result["passes"] is True

    def test_empty_overlay_passes_trivially(self):
        from app.prompts.storyboard_prompts import validate_text_overlay_complements_image
        result = validate_text_overlay_complements_image(
            image_prompt="A landscape shot",
            overlay_text="",
        )
        assert result["passes"] is True


# ============================================================================
# Section 8: 6 cluster mock scene 跨题材验证 (端到端)
# ============================================================================


class TestSixClusterCrossGenreMockScenes:
    """6 个 mock scene (覆盖 6 cluster) 端到端通过 v3 validators."""

    def _make_scene_for_cluster(self, cluster_id: str) -> dict:
        """构造一个符合 cluster TOP 5 原则的 mock scene."""
        from app.prompts.screenplay_prompts import get_cluster_default_viewpoint
        base = {
            "scene_id": 1,
            "narrative_cluster": cluster_id,
            "narrative_viewpoint": get_cluster_default_viewpoint(cluster_id),
            "narrative_phase": "climax",
            "structure_position_pct": 75,
            "target_text_density": 2.0,
            "narrative_structure": "qichengzhuanhe",
            "scene_self_evaluation": {
                "reader_comprehension_score": 0.90,
                "reader_comprehension_reasoning": f"{cluster_id} cluster: top5 全部应用",
                "key_info_conveyed_via_visible_text": ["主线", "情感", "关键 plot"],
                "info_only_in_narration_prose": [],
            },
        }
        # cluster 特定 dialogue
        cluster_dialogues = {
            "C1": [("char_001", "（其实心里很难过。）", "thought"),
                   ("char_002", "对不起宝宝。", "dialogue"),
                   ("char_001", "没一张能看的！！！", "dialogue")],
            "C2": [("char_001", "三点二十七分。", "narration"),
                   ("char_001", "（镜中, 多了一张脸。）", "thought"),
                   ("char_002", "她已经死了三年了！！！", "dialogue")],
            "C3": [("char_001", "勇者拔出圣剑。", "narration"),
                   ("char_001", "（这就是命运的考验。）", "thought"),
                   ("char_002", "魔王: 你来了！！！", "dialogue")],
            "C4": [("char_001", "好甜！", "dialogue"),
                   ("char_001", "嘿嘿。", "dialogue"),
                   ("char_002", "（小熊很开心。）", "thought")],
            "C5": [("char_001", "师父: 三日后, 论剑山！！！", "dialogue"),
                   ("char_001", "（多年的等待。）", "thought"),
                   ("char_002", "去。", "dialogue")],
            "C6": [("char_001", "AI: 第 47 次循环。", "dialogue"),
                   ("char_001", "（数据异常。）", "thought"),
                   ("char_002", "目标确认！！！", "dialogue")],
            "C7": [("char_001", "卧槽。", "thought"),
                   ("char_001", "结果他真离婚了！！！", "dialogue"),
                   ("char_002", "啊?", "dialogue")],
            "C8": [("char_001", "他被裁员了 (优化)。", "dialogue"),
                   ("char_001", "（什么时候到我?）", "thought"),
                   ("char_002", "三期。", "dialogue")],
        }
        beats = []
        for i, (sp, line, typ) in enumerate(cluster_dialogues[cluster_id]):
            beats.append({
                "beat_id": f"1{chr(ord('a')+i)}",
                "type": typ,
                "speaker": sp,
                "line": line,
                "emotion": "intense",
                "speaker_position": "left" if i % 2 == 0 else "right",
            })
        base["dialogue_beats"] = beats
        base["narration"] = "短 caption。"
        return base

    @pytest.mark.parametrize("cluster", ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"])
    def test_cluster_scene_passes_self_evaluation(self, cluster):
        from app.prompts.screenplay_prompts import validate_scene_self_evaluation
        scene = self._make_scene_for_cluster(cluster)
        result = validate_scene_self_evaluation(scene)
        assert result["passes_85_kpi"] is True

    @pytest.mark.parametrize("cluster", ["C1", "C2", "C3", "C5", "C6", "C7"])
    def test_cluster_climax_has_emphasis(self, cluster):
        """这些 cluster 的 climax 都设了 !!! emphasis"""
        from app.prompts.screenplay_prompts import validate_emphasis_usage
        scene = self._make_scene_for_cluster(cluster)
        result = validate_emphasis_usage(scene)
        assert result["passes"] is True, (
            f"cluster {cluster} climax should have emphasis, issues: {result['issues']}"
        )


# ============================================================================
# Section 9: 向后兼容 — v1 + v2 (DEC-044) 规则仍可 import 不退化
# ============================================================================


class TestBackwardCompatibilityV1V2:
    """v3 不破坏 v1 (DEC-044) + v2 (T20-21 v2 35 字) 规则"""

    def test_dec044_v1_rules_still_present(self):
        from app.prompts.screenplay_prompts import (
            DEC044_SCREENPLAY_RULES,
            DEC044_SCREENPLAY_OUTPUT_EXAMPLE,
            NARRATION_CAPTION_RULES,
            DIALOGUE_THOUGHT_DENSITY_RULES,
        )
        assert "DEC-044" in DEC044_SCREENPLAY_RULES
        assert "PRODUCT FINAL FORM" in DEC044_SCREENPLAY_RULES

    def test_v2_dialogue_max_chars_unchanged(self):
        from app.prompts.screenplay_prompts import get_dec044_dialogue_max_chars
        # v2 (T20-21 v2) 改成 35, v3 不动
        assert get_dec044_dialogue_max_chars() == 35

    def test_v2_narration_max_chars_unchanged(self):
        from app.prompts.screenplay_prompts import get_dec044_narration_max_chars
        assert get_dec044_narration_max_chars() == 120

    def test_v2_caption_max_chars_unchanged(self):
        from app.prompts.screenplay_prompts import get_dec044_caption_max_chars
        assert get_dec044_caption_max_chars() == 25

    def test_t20_27_critical_turn_detection_still_present(self):
        from app.prompts.screenplay_prompts import (
            is_critical_turn_beat,
            validate_critical_turns_have_dialogue,
        )
        assert callable(is_critical_turn_beat)
        assert callable(validate_critical_turns_have_dialogue)

    def test_stage4_wave4_rules_still_present(self):
        from app.prompts.storyboard_prompts import (
            COMIC_MODE_NARRATIVE_RULES,
            SPECIES_FIDELITY_RULES,
            SEEDREAM_SAFETY_AVOIDANCE_RULES,
        )
        # Wave 4 已有规则不退化
        assert "DEC-044" in COMIC_MODE_NARRATIVE_RULES
        assert "SPECIES" in SPECIES_FIDELITY_RULES
        assert "SEEDREAM CONTENT-SAFETY" in SEEDREAM_SAFETY_AVOIDANCE_RULES


# ============================================================================
# Section 10: helper getters 数值合理性
# ============================================================================


class TestHelperGetterValues:
    """helper 返回合理数值"""

    def test_85_kpi_threshold_value(self):
        from app.prompts.screenplay_prompts import get_85_kpi_threshold
        assert get_85_kpi_threshold() == 0.85

    def test_emphasis_marker_chars(self):
        from app.prompts.screenplay_prompts import get_emphasis_marker_chars
        markers = get_emphasis_marker_chars()
        assert "!!!" in markers
        assert "！！！" in markers

    def test_v3_required_scene_fields(self):
        from app.prompts.screenplay_prompts import get_v3_required_scene_fields
        fields = get_v3_required_scene_fields()
        assert "narrative_cluster" in fields
        assert "scene_self_evaluation" in fields

    def test_cluster_top5_principles(self):
        from app.prompts.screenplay_prompts import get_cluster_top5_principles
        for cid in ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]:
            principles = get_cluster_top5_principles(cid)
            assert len(principles) == 5

    def test_cluster_default_viewpoint(self):
        from app.prompts.screenplay_prompts import get_cluster_default_viewpoint
        # C1 应是 first_person, C2 第三客观, C4 全知
        assert get_cluster_default_viewpoint("C1") == "first_person"
        assert get_cluster_default_viewpoint("C2") == "third_objective"
        assert get_cluster_default_viewpoint("C4") == "narrator_omniscient"
        # 未知 cluster 默认 C8 (first_person)
        assert get_cluster_default_viewpoint("UNKNOWN") == "first_person"


# ============================================================================
# Section 11: Universal — v3 应支持任意 style / 任意角色 / 任意语言
# ============================================================================


class TestUniversalDesign:
    """DEC-046 v3 必须 universal (40+ genre 都能用), 不 hardcode test19 / 灰狐"""

    def test_no_hardcode_test19_chars(self):
        from app.prompts.screenplay_prompts import DEC046_V3_NARRATIVE_PRINCIPLES as v3
        # v3 应不写死 test19 特定角色名为唯一原则示例
        # (允许 reference test19 作为例子, 但不能 hardcode)
        # 验证: cluster definitions 不含特定故事名
        from app.prompts.screenplay_prompts import CLUSTER_DEFINITIONS
        for cid, defn in CLUSTER_DEFINITIONS.items():
            text = str(defn)
            assert "陈砚" not in text, f"{cid} hardcodes 陈砚"
            assert "灰狐" not in text, f"{cid} hardcodes 灰狐"

    def test_supports_all_8_clusters_detection(self):
        from app.prompts.screenplay_prompts import detect_narrative_cluster
        # 各 cluster 至少一个 style 关键词能 detect 出
        cluster_styles = {
            "C1": "korean_webtoon",
            "C2": "horror",
            "C3": "fantasy",
            "C4": "children_book",
            "C5": "wuxia",
            "C6": "scifi",
            "C7": "comedy",
            "C8": "realistic",
        }
        for cid, style in cluster_styles.items():
            result = detect_narrative_cluster(style=style)
            assert result == cid, f"style {style} should detect {cid}, got {result}"

    def test_v3_works_with_empty_scene(self):
        """空 scene 不应崩 (universal)"""
        from app.prompts.screenplay_prompts import (
            validate_scene_self_evaluation,
            validate_emphasis_usage,
        )
        empty_scene = {}
        # 不崩
        r1 = validate_scene_self_evaluation(empty_scene)
        r2 = validate_emphasis_usage(empty_scene)
        assert r1["passes_85_kpi"] is False
        assert r2["emphasis_marker_count"] == 0
