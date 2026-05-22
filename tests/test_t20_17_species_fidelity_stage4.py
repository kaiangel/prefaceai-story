"""
TASK-T20-FIXBATCH-4 Wave 2 RISK-T20-17 P0 — Stage 4 物种保真 (Species Fidelity) 测试

DEC-045 RISK-T20-17 (2026-05-19) 修复:
test17 v2 Shot 10 实证 — Stage 4 LLM 把 char_002 (兔子 米莉/Milly) 写成
"a small hedgehog-like creature with warm brown fur and a dried winter-grass collar"。
Seedream 收到"hedgehog"文本 + 兔子参考图，文本优先级高 → 渲染成刺猬。

真根因（5 维度调用链路追踪）:
1. characters_in_scene 正确 ✓
2. reference_images 正确 ✓
3. ❌ Stage 4 `_build_scene_prompt()` 给 LLM 的 character data 块只含 {id, name, clothing_summary}
   完全没有 character_type 和 species。LLM 对该角色物种零信息 → 自由发挥 → "hedgehog-like"
4. "CRITICAL: IMAGE_PROMPT MUST BE WRITTEN ENTIRELY IN ENGLISH" 规则禁止 LLM 从中文 narration
   抓物种线索 ("小兔米莉")
5. LLM 凭"暖色+冬草围领+小动物"自由发挥 → "hedgehog-like creature"

修复 (AI-ML 层 — Prompt + 数据契约):
1. 新加 `build_stage4_character_data_block()` — 给 LLM 加 character_type + species + appearance
2. 新加 `SPECIES_FIDELITY_RULES` 规则块 — 显式禁止 substituting/hedging/omitting 物种
3. Backend 需 wire 到 `storyboard_director.py` `_build_scene_prompt()` (L1537+) 和注入 SPECIES_FIDELITY_RULES

测试覆盖:
- Section A: _strip_chinese_bilingual_segments 工具函数 (5 cases)
- Section B: _short_distinctive_marks 工具函数 (4 cases)
- Section C: build_stage4_character_data_block 真实数据 (test17 v2) — 物种保真 (6 cases)
- Section D: build_stage4_character_data_block edge cases (8 cases)
- Section E: SPECIES_FIDELITY_RULES 规则块完整性 (6 cases)
- Section F: 真实 LLM prompt 集成模拟 (3 cases)

Usage:
    cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story
    python -m pytest tests/test_t20_17_species_fidelity_stage4.py -v
"""

import json
import re
import sys
from pathlib import Path

import pytest

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.prompts.storyboard_prompts import (
    SPECIES_FIDELITY_RULES,
    _short_distinctive_marks,
    _strip_chinese_bilingual_segments,
    build_stage4_character_data_block,
)


# ============================================================================
# Section A: _strip_chinese_bilingual_segments 工具函数测试
# ============================================================================

class TestStripChineseBilingualSegments:
    """覆盖中文清洗工具的 5 个核心 case"""

    def test_strips_dash_chinese_pattern(self):
        """'english — 中文' → 'english'"""
        s = "frost silver-grey fur — 通体霜灰，腹部褪为淡象牙白"
        result = _strip_chinese_bilingual_segments(s)
        assert "通体" not in result
        assert "霜灰" not in result
        assert "frost silver-grey fur" in result

    def test_handles_multiple_dash_chinese_segments(self):
        """多段 'eng1 — zh1 eng2 — zh2' → 'eng1, eng2'（保留词边界）"""
        s = "fluffy fur — 蓬松毛皮 with long ears — 长耳朵"
        result = _strip_chinese_bilingual_segments(s)
        assert "蓬松" not in result
        assert "长耳" not in result
        assert "fluffy fur" in result
        assert "with long ears" in result

    def test_returns_pure_english_unchanged(self):
        """纯英文不变"""
        s = "anthropomorphic rabbit with white fur"
        assert _strip_chinese_bilingual_segments(s) == s

    def test_handles_pure_chinese_returns_empty(self):
        """纯中文 → 空串（或只含标点）"""
        s = "通体霜灰，腹部褪为淡象牙白"
        result = _strip_chinese_bilingual_segments(s)
        # 应该没有任何中文字符残留
        assert not any("一" <= c <= "鿿" for c in result)

    def test_handles_empty_and_none(self):
        """空字符串、None → 空"""
        assert _strip_chinese_bilingual_segments("") == ""
        assert _strip_chinese_bilingual_segments(None) == ""

    def test_word_boundaries_preserved(self):
        """关键回归: 'white — 白色 fine' → 'white, fine' (不是 'whitefine')"""
        s = "white — 白色 fine"
        result = _strip_chinese_bilingual_segments(s)
        # 词边界保留: 应包含 'fine' 而不是 'whitefine'
        assert "whitefine" not in result
        assert "fine" in result
        assert "white" in result


# ============================================================================
# Section B: _short_distinctive_marks 工具函数测试
# ============================================================================

class TestShortDistinctiveMarks:
    """4 个 distinctive_marks 截取测试"""

    def test_takes_first_n_marks(self):
        marks = ["mark1 description", "mark2 description", "mark3 description"]
        result = _short_distinctive_marks(marks, max_marks=2)
        assert "mark1" in result
        assert "mark2" in result
        assert "mark3" not in result

    def test_strips_chinese_from_marks(self):
        marks = [
            "faint white scar on left paw — 左前爪上有浅白旧疤",
            "always cradles an apple — 静立时双爪轻托一颗小野苹果",
        ]
        result = _short_distinctive_marks(marks, max_marks=2)
        assert "通体" not in result
        assert "前爪" not in result
        assert "faint white scar on left paw" in result
        assert "always cradles an apple" in result

    def test_truncates_long_marks(self):
        long_mark = "a" * 200
        result = _short_distinctive_marks([long_mark], max_marks=1, max_chars_per=50)
        assert len(result) <= 55  # 50 + "..."

    def test_handles_empty_list(self):
        assert _short_distinctive_marks([]) == ""
        assert _short_distinctive_marks(None) == ""
        assert _short_distinctive_marks([""]) == ""


# ============================================================================
# Section C: build_stage4_character_data_block — 真实数据 (test17 v2)
# ============================================================================

# 真实 test17 v2 角色数据（截取自 output/adfdfa58.../2_characters.json）
TEST17_V2_CHARACTERS = {
    "characters": [
        {
            "id": "char_001",
            "name": "灰狐",
            "name_en": "Grey Fox",
            "character_type": "anthropomorphic_animal",
            "gender": "female",
            "age_appearance": "elderly",
            "description": (
                "年迈的灰色母狐，通体霜银灰色毛皮，腹部与吻部褪为象牙白。"
                "An elderly female fox with frost silver-grey fur, fading to ivory white at belly"
            ),
            "physical": {
                "species": "fox",
                "fur_color": "frost silver-grey with ivory white underbelly — 通体霜灰",
                "fur_texture": "fine — 细密",
                "ear_style": "medium upright pointed fox ears",
                "tail_style": "full bushy fox tail",
                "snout_shape": "slender elongated fox snout",
                "eye_color": "deep amber-gold",
                "eye_shape": "almond",
                "build": "slightly_hunched_but_dignified",
                "distinctive_marks": [
                    "faint white scar on left forepaw pad — 左前爪掌垫上有一道浅白旧疤",
                    "always cradles a small wild apple between both forepaws — 静立时双爪轻托一颗小野苹果",
                ],
            },
            "clothing": {
                "top": "loosely draped pale birch-bark beige linen wrap coat — 桦树皮米白亚麻披裹长衣",
                "bottom": "layered dusty sage green linen underskirt — 雾绿亚麻长裙",
                "accessories": ["single dried white birch-leaf stem behind left ear"],
            },
        },
        {
            "id": "char_002",
            "name": "米莉",
            "name_en": "Milly",
            "character_type": "anthropomorphic_animal",
            "gender": "female",
            "age_appearance": "young_adult",
            "description": (
                "年轻的象牙白小兔。A young female rabbit with warm ivory white fur"
            ),
            "physical": {
                "species": "rabbit",
                "fur_color": "clean warm ivory white overall — 通体温暖象牙白",
                "fur_texture": "extremely soft and fluffy — 极度柔软蓬松",
                "ear_style": "very long upright rabbit ears",
                "tail_style": "small round fluffy cotton-ball tail",
                "snout_shape": "small soft rounded rabbit nose",
                "eye_color": "large bright warm ruby-rose",
                "eye_shape": "very large round",
                "distinctive_marks": [
                    "single small pale freckle on tip of left ear — 左耳外侧耳尖有一枚浅色小斑点",
                    "fluffy ruff of dried winter grass around neck — 脖颈围着一圈蓬松干冬草",
                ],
            },
            "clothing": {
                "top": "snug pale warm cream knitted vest — 温暖米乳色针织小背心",
                "bottom": "soft dusty warm brown short skirt — 柔软暖褐色短裙",
            },
        },
        {
            "id": "char_003",
            "name": "啾啾",
            "name_en": "Jojo",
            "character_type": "anthropomorphic_animal",
            "gender": "female",
            "age_appearance": "young_adult",
            "description": (
                "活泼的年轻麻雀。A vivacious young female sparrow with warm tawny brown feathers"
            ),
            "physical": {
                "species": "sparrow",
                "fur_color": "warm tawny brown with streaked darker umber-brown — 通体暖栗褐色",
                "fur_texture": "feathers — overall fluffy and puffed — 羽毛蓬松鼓胀",
                "ear_style": "small rounded feathered ear patches",
                "tail_style": "short fan-shaped tail",
                "snout_shape": "short sharp pointed sparrow beak",
                "eye_color": "small bright warm dark amber-brown",
                "distinctive_marks": [
                    "signature single white streak across each wing — 翅膀两侧各一道白色细纹",
                    "beak almost always slightly open as if mid-sentence — 嘴喙几乎永远微微张开",
                ],
            },
            "clothing": {
                "top": "bright warm ochre-yellow short puffed-sleeve blouse — 明亮暖赭黄色短袖泡泡袖衬衫",
                "bottom": "warm rust-orange wide-leg shorts — 暖锈橙色宽腿短裤",
            },
        },
    ]
}


class TestBuildStage4CharacterDataBlockReal:
    """test17 v2 灰狐故事真实数据 — 物种保真核心测试"""

    def test_block_contains_all_three_species(self):
        """关键: char_001 species=fox / char_002 species=rabbit / char_003 species=sparrow"""
        block = build_stage4_character_data_block(TEST17_V2_CHARACTERS)
        assert '"species": "fox"' in block
        assert '"species": "rabbit"' in block
        assert '"species": "sparrow"' in block

    def test_block_contains_character_type_for_all_chars(self):
        """每个角色都必须有 character_type 字段"""
        block = build_stage4_character_data_block(TEST17_V2_CHARACTERS)
        parsed = json.loads(block.split("[", 1)[1].rsplit("]", 1)[0].join(["[", "]"]))
        assert len(parsed) == 3
        for c in parsed:
            assert "character_type" in c
            assert c["character_type"] == "anthropomorphic_animal"

    def test_block_has_zero_chinese_characters(self):
        """全英文输出 (无中文字符泄漏)"""
        block = build_stage4_character_data_block(TEST17_V2_CHARACTERS)
        chinese_chars = re.findall(r"[一-鿿]", block)
        assert len(chinese_chars) == 0, f"Found Chinese chars: {chinese_chars[:5]}"

    def test_milly_has_rabbit_species_not_hedgehog(self):
        """关键回归: Milly (char_002) 物种是 rabbit, 不能是 hedgehog"""
        block = build_stage4_character_data_block(TEST17_V2_CHARACTERS)
        # 找 char_002 段
        milly_start = block.find('"id": "char_002"')
        assert milly_start > 0
        milly_end = block.find('"id": "char_003"')
        milly_section = block[milly_start:milly_end] if milly_end > 0 else block[milly_start:]
        assert '"species": "rabbit"' in milly_section
        assert "hedgehog" not in milly_section.lower()

    def test_block_uses_english_names(self):
        """name 字段用 name_en（Grey Fox / Milly / Jojo），不用中文"""
        block = build_stage4_character_data_block(TEST17_V2_CHARACTERS)
        assert '"name": "Grey Fox"' in block
        assert '"name": "Milly"' in block
        assert '"name": "Jojo"' in block
        assert "灰狐" not in block
        assert "米莉" not in block
        assert "啾啾" not in block

    def test_block_size_reasonable(self):
        """块大小 < 5000 chars 保证不挤占 LLM context window"""
        block = build_stage4_character_data_block(TEST17_V2_CHARACTERS)
        assert len(block) < 5000, f"Block too large: {len(block)} chars"
        assert len(block) > 800, f"Block too small (likely empty): {len(block)} chars"


# ============================================================================
# Section D: build_stage4_character_data_block edge cases
# ============================================================================

class TestBuildStage4CharacterDataBlockEdgeCases:
    """8 个 edge case 测试"""

    def test_empty_characters_dict(self):
        result = build_stage4_character_data_block({})
        assert result == "Character data:\n[]"

    def test_empty_characters_list(self):
        result = build_stage4_character_data_block({"characters": []})
        assert result == "Character data:\n[]"

    def test_none_input(self):
        result = build_stage4_character_data_block(None)
        # 应该不崩，返回空块
        assert "[]" in result or "Character data" in result

    def test_human_character_no_species_field(self):
        """human 类型不输出 species（因为 physical 没 species 字段）"""
        human_chars = {
            "characters": [{
                "id": "char_001",
                "name_en": "Su Chen",
                "character_type": "human",
                "physical": {
                    "face_shape": "oval",
                    "skin_tone": "fair",
                    "hair_color": "black",
                    "hair_style": "short bob",
                    "eye_color": "dark brown",
                },
                "clothing": {
                    "top": "gray blazer",
                    "bottom": "black trousers",
                },
            }]
        }
        block = build_stage4_character_data_block(human_chars)
        assert '"character_type": "human"' in block
        # human 不应有 species
        assert '"species":' not in block
        # 但要有 appearance（来自 CharacterPromptBuilder）
        assert "appearance" in block

    def test_clothing_summary_falls_back_when_chinese_only(self):
        """中文-only clothing → fallback 'see character reference image'"""
        chars = {
            "characters": [{
                "id": "char_001",
                "name_en": "Test",
                "character_type": "anthropomorphic_animal",
                "physical": {"species": "rabbit"},
                "clothing": {
                    "top": "纯中文上衣",
                    "bottom": "纯中文下衣",
                },
            }]
        }
        block = build_stage4_character_data_block(chars)
        assert "see character reference image" in block

    def test_chinese_name_falls_back_to_id(self):
        """如果 name_en 缺失 且 name 含中文 → 用 id 作 name (防中文泄露)"""
        chars = {
            "characters": [{
                "id": "char_001",
                "name": "灰狐",  # 含中文
                # 无 name_en
                "character_type": "anthropomorphic_animal",
                "physical": {"species": "fox"},
            }]
        }
        block = build_stage4_character_data_block(chars)
        chinese_chars = re.findall(r"[一-鿿]", block)
        assert len(chinese_chars) == 0

    def test_missing_physical_field(self):
        """physical 缺失 → 不崩，无 species 字段"""
        chars = {
            "characters": [{
                "id": "char_001",
                "name_en": "Test",
                "character_type": "anthropomorphic_animal",
                # 无 physical
                "description": "A small animal",
            }]
        }
        block = build_stage4_character_data_block(chars)
        # 不崩
        assert "char_001" in block

    def test_missing_character_type_defaults_to_human(self):
        """character_type 缺失 → 默认 'human'"""
        chars = {
            "characters": [{
                "id": "char_001",
                "name_en": "Test",
                # 无 character_type
                "physical": {"hair_color": "black"},
            }]
        }
        block = build_stage4_character_data_block(chars)
        assert '"character_type": "human"' in block


# ============================================================================
# Section E: SPECIES_FIDELITY_RULES 规则块完整性
# ============================================================================

class TestSpeciesFidelityRules:
    """6 个 SPECIES_FIDELITY_RULES 必含规则项测试"""

    def test_rules_block_exists_and_nonempty(self):
        assert SPECIES_FIDELITY_RULES
        assert len(SPECIES_FIDELITY_RULES) > 1000

    def test_rules_mention_hedgehog_anti_pattern(self):
        """test17 v2 真实失败案例必须在规则中显式禁止"""
        assert "hedgehog" in SPECIES_FIDELITY_RULES.lower()
        # 同时禁止其他常见 substitution 错误
        assert "rabbit" in SPECIES_FIDELITY_RULES.lower()

    def test_rules_mention_species_fidelity_concept(self):
        """关键概念必须出现"""
        assert "species" in SPECIES_FIDELITY_RULES.lower()
        assert "fidelity" in SPECIES_FIDELITY_RULES.lower()
        assert "character_type" in SPECIES_FIDELITY_RULES.lower()

    def test_rules_have_anatomy_cross_reference_table(self):
        """anatomy 对照表必须存在 (rabbit→paws, bird→wings)"""
        rules_lower = SPECIES_FIDELITY_RULES.lower()
        assert "paws" in rules_lower
        assert "wings" in rules_lower
        assert "beak" in rules_lower
        assert "fur" in rules_lower
        # 至少 3 个物种的 anatomy 描述
        anatomy_species = sum(
            1 for sp in ["rabbit", "bird", "fox", "cat", "bear"] if sp in rules_lower
        )
        assert anatomy_species >= 3

    def test_rules_have_self_check_block(self):
        """每个规则必须有 SELF-CHECK 检查项"""
        assert "SELF-CHECK" in SPECIES_FIDELITY_RULES

    def test_rules_have_forbidden_patterns_section(self):
        """规则必须显式列出 FORBIDDEN patterns"""
        assert "FORBIDDEN" in SPECIES_FIDELITY_RULES
        # T20-10 cross-reference: 也禁止 human descriptors
        assert "Asian woman" in SPECIES_FIDELITY_RULES or "human" in SPECIES_FIDELITY_RULES.lower()


# ============================================================================
# Section F: 真实 LLM prompt 集成模拟
# ============================================================================

class TestPromptIntegrationSimulation:
    """3 个集成测试 — 模拟新 character data 块对解决 hedgehog bug 的效果"""

    def test_old_vs_new_milly_data(self):
        """模拟旧/新 Stage 4 给 LLM 的 char_002 (Milly) 数据对比"""
        # 旧方式 (storyboard_director.py L1537-1558 现有代码)
        old_block = json.dumps([{
            "id": "char_002",
            "name": "Milly",
            "clothing_summary": "see character reference image",  # 中文 clothing 被 strip 后 fallback
        }], indent=2)

        # 新方式
        new_block = build_stage4_character_data_block(TEST17_V2_CHARACTERS)
        new_milly_section = new_block[new_block.find('"id": "char_002"'):]
        new_milly_section = new_milly_section[:new_milly_section.find('"id": "char_003"')]

        # 旧方式: LLM 完全不知道 Milly 是什么物种
        assert "species" not in old_block
        assert "character_type" not in old_block
        assert "rabbit" not in old_block.lower()

        # 新方式: LLM 明确知道 Milly 是 rabbit
        assert '"species": "rabbit"' in new_milly_section
        assert '"character_type": "anthropomorphic_animal"' in new_milly_section
        assert "appearance" in new_milly_section

    def test_rules_block_explicitly_forbids_actual_bug_phrasing(self):
        """test17 v2 真实失败短语 (LLM 输出过的) 必须在 FORBIDDEN 列表中"""
        # 真实 LLM 输出 (test17 v2 Shot 10): "hedgehog-like creature"
        assert "hedgehog-like" in SPECIES_FIDELITY_RULES

    def test_rules_provide_correct_alternative(self):
        """规则不只说 FORBIDDEN, 还给 LLM REQUIRED PATTERN 示范"""
        assert "REQUIRED" in SPECIES_FIDELITY_RULES
        # 修复示范必须包含正确写法 (rabbit + paws)
        rules_lower = SPECIES_FIDELITY_RULES.lower()
        assert "anthropomorphic rabbit" in rules_lower or "anthropomorphic [species]" in rules_lower


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
