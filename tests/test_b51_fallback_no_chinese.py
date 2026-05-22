"""
tests/test_b51_fallback_no_chinese.py

RISK-T19-8 Wave 14 — B51 fallback 中文化补漏: LLM input 真根因深挖单测

验证点:
1. _extract_english_from_field(): 双语 description 提取英文部分
2. _extract_english_from_field(): 纯中文 clothing 字段返回空
3. _extract_english_from_field(): 纯英文字段原样通过
4. _build_scene_prompt() characters_json: name 改用 name_en
5. _build_scene_prompt() characters_json: 含中文 clothing 字段提取英文
6. _build_scene_prompt() scene_json: atmosphere 过滤中文
7. _build_scene_prompt() scene_json: scene_heading 含中文时替换占位
8. _build_scene_prompt() prompt 开头: 含英文铁律规则
9. 中英双语 description — LLM input 只传英文部分
10. 角色名 — 含中文 name 时用 name_en
"""

import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.storyboard_director import (
    _contains_chinese,
    _extract_english_from_field,
    _atmosphere_to_str,
    StoryboardDirector,
)


# ══════════════════════════════════════════════════════════════════
# Section 1: _extract_english_from_field() 单元测试
# ══════════════════════════════════════════════════════════════════


class TestExtractEnglishFromField:
    """RISK-T19-8: _extract_english_from_field() 从双语字段提取英文部分"""

    def test_case1_pure_english_passthrough(self):
        """纯英文字段原样通过，不做任何处理（regression 保证）"""
        value = "light blue knit top with small buttons"
        result = _extract_english_from_field(value, "clothing.top")
        assert result == value
        assert not _contains_chinese(result)

    def test_case2_pure_chinese_returns_empty(self):
        """
        纯中文字段（如 char_001 clothing.top 全中文）→ 返回空字符串
        现实场景: "一件手工缝制的藕灰色棉麻小褂，领口和袖口有极细的白色滚边"
        """
        value = "一件手工缝制的藕灰色棉麻小褂，领口和袖口有极细的白色滚边"
        result = _extract_english_from_field(value, "clothing.top")
        assert result == ""
        assert not _contains_chinese(result)

    def test_case3_bilingual_description_extracts_english(self):
        """
        中英双语 description → 提取英文部分
        现实场景: char_002 description = "年轻的小白兔...。A young white rabbit..."
        """
        value = (
            "年轻的小白兔，耳朵特别短，圆眼睛总是闪着好奇的光，围着一条浅蓝色小围巾。"
            "A young white rabbit with particularly short ears, round eyes sparkling with curiosity, "
            "wearing a light blue scarf."
        )
        result = _extract_english_from_field(value, "description")
        # 应提取英文部分
        assert "young white rabbit" in result
        assert "particularly short ears" in result
        # 不应含中文
        assert not _contains_chinese(result)

    def test_case4_bilingual_char001_description_extracts_english(self):
        """
        char_001 (灰狐) 双语 description → 提取英文部分
        """
        value = (
            "年迈的灰色母狐，毛色如霜银，两鬓与吻部已白，背脊微弓，身着岁月洗旧的藕灰棉麻披风与长裙，"
            "左腕缠一截无挂件的银色皮绳。眼神深邃温柔，嘴角常含一缕淡淡微笑，每年立春独自踏雪入山，"
            "用双掌托着一颗野苹果，在白桦树下低声说着只有她自己听懂的话。"
            "An elderly grey vixen with frost-silver fur, white-tipped muzzle and temples, "
            "slightly bowed back, wearing a worn ash-grey handmade cape and ankle-length linen skirt "
            "dusted with snow at the hem."
        )
        result = _extract_english_from_field(value, "char_001.description")
        assert "grey vixen" in result or "frost-silver" in result
        assert not _contains_chinese(result)

    def test_case5_empty_string_returns_empty(self):
        """空字符串 → 返回空字符串"""
        assert _extract_english_from_field("", "test") == ""
        assert _extract_english_from_field("", "") == ""

    def test_case6_clothing_with_chinese_bottom_returns_empty(self):
        """
        char_003 啾啾 clothing.bottom = "米黄色宽松短裤，裤腰有松紧，裤口微微卷起"
        → 纯中文，返回空
        """
        value = "米黄色宽松短裤，裤腰有松紧，裤口微微卷起，裤腿上有一个被树枝划出的小破洞"
        result = _extract_english_from_field(value, "char_003.clothing.bottom")
        assert result == ""

    def test_case7_clothing_english_passthrough(self):
        """
        char_002 米莉 clothing.top = "light blue knit top"
        → 纯英文，原样通过
        """
        value = "light blue knit top"
        result = _extract_english_from_field(value, "char_002.clothing.top")
        assert result == value
        assert not _contains_chinese(result)

    def test_case8_no_extractable_english_returns_empty(self):
        """
        完全中文 + 无法分隔出英文片段 → 返回空（安全降级）
        """
        value = "藕灰色棉麻小褂，领口有白色滚边，布料柔软，胸前有暗纹绣花"
        result = _extract_english_from_field(value, "clothing.top")
        assert result == ""
        assert not _contains_chinese(result)


# ══════════════════════════════════════════════════════════════════
# Section 2: _build_scene_prompt() 输出验证（通过 StoryboardDirector）
# ══════════════════════════════════════════════════════════════════


@pytest.fixture
def director():
    """创建不初始化 API client 的 StoryboardDirector 实例（避免需要 API Key）"""
    d = StoryboardDirector.__new__(StoryboardDirector)
    d.claude_client = None
    d.gemini_client = None
    d.claude_model = "claude-sonnet-4-6"
    d.gemini_model = "gemini-3.1-flash-lite-preview"
    return d


@pytest.fixture
def test19_characters():
    """test19 真实 5 角色数据（2_characters.json 子集），全为 anthropomorphic_animal"""
    return {
        "characters": [
            {
                "id": "char_001",
                "name": "灰狐",
                "name_en": "Grey Fox",
                "character_type": "anthropomorphic_animal",
                "clothing": {
                    "top": "一件手工缝制的藕灰色棉麻小褂，领口和袖口有极细的白色滚边，布料因多年穿洗而柔软泛白",
                    "bottom": "同色系的宽松棉麻长裙，裙摆拖及脚踝，雪地行走后裙边沾有薄薄的碎雪和松针",
                },
                "description": (
                    "年迈的灰色母狐，毛色如霜银，两鬓与吻部已白，背脊微弓。"
                    "An elderly grey vixen with frost-silver fur, white-tipped muzzle and temples, "
                    "slightly bowed back, wearing a worn ash-grey handmade cape."
                ),
            },
            {
                "id": "char_002",
                "name": "米莉",
                "name_en": "Milly",
                "character_type": "anthropomorphic_animal",
                "clothing": {
                    "top": "light blue knit top",
                    "bottom": "white shorts",
                },
                "description": (
                    "年轻的小白兔，耳朵特别短，圆眼睛总是闪着好奇的光。"
                    "A young white rabbit with particularly short ears, round eyes sparkling with curiosity."
                ),
            },
            {
                "id": "char_003",
                "name": "啾啾",
                "name_en": "Jiu Jiu",
                "character_type": "anthropomorphic_animal",
                "clothing": {
                    "top": "一件暖棕色圆领短袖小背心，胸前印着一个手绘风格的小音符图案",
                    "bottom": "米黄色宽松短裤，裤腰有松紧，裤口微微卷起",
                },
                "description": (
                    "圆滚滚的棕色小麻雀，头顶一撮永远半炸的冠毛。"
                    "A plump chestnut-brown sparrow with a perpetually half-ruffled crown tuft."
                ),
            },
        ]
    }


@pytest.fixture
def scene_with_chinese_heading():
    """含中文 scene_heading 和 action_beats 的测试场景"""
    return {
        "scene_id": 7,
        "scene_heading": "EXT. 白桦树下 - 立春清晨 - 晴",
        "atmosphere": {
            "mood": "tranquil",
            "sound_design_hint": "远山鸟鸣稀疏，踩雪声轻脆，风过松枝沙沙作响",
            "temperature_feel": "凛冽中带一丝初春的微暖"
        },
        "characters_in_scene": ["char_001", "char_002"],
        "action_beats": [
            {
                "beat_id": "7a",
                "action": "灰狐在白桦树前停下，俯身将野苹果轻轻放在树根旁的雪地上。",
                "duration_hint": 7,
                "emotional_note": "solemn, tender",
            }
        ],
        "dialogue_beats": [],
        "narration": "白桦树高大而苍老，树皮皲裂成一道道细纹，像是岁月刻下的字迹。",
    }


class TestBuildScenePromptCharacterNames:
    """
    RISK-T19-8 Case 9-10: _build_scene_prompt characters_json 验证

    characters_json 里 name 字段应使用 name_en（英文名），
    不应包含中文角色名（"灰狐", "米莉", "啾啾" 等）。
    """

    def test_case9_name_uses_name_en(self, director, test19_characters, scene_with_chinese_heading):
        """
        Case 9: characters_json 中 name 字段必须是 name_en（英文名）
        不能出现 "灰狐", "米莉", "啾啾" 等中文名
        """
        visual_tone = {"mood": "gentle"}
        prompt = director._build_scene_prompt(
            scene=scene_with_chinese_heading,
            characters=test19_characters,
            visual_tone=visual_tone,
            style_preset="anime",
            shot_id_start=1,
        )

        # 解析 characters_json 部分（在 "Character data:\n" 之后）
        assert "Character data:" in prompt
        char_data_start = prompt.index("Character data:") + len("Character data:\n")
        # 找到下一个 ## 或 \n\n 结束
        char_data_section = prompt[char_data_start:char_data_start + 800]

        # characters_json 中不应出现中文角色名
        assert "灰狐" not in char_data_section, "characters_json 不应包含中文角色名 '灰狐'"
        assert "米莉" not in char_data_section, "characters_json 不应包含中文角色名 '米莉'"
        assert "啾啾" not in char_data_section, "characters_json 不应包含中文角色名 '啾啾'"

        # 应包含英文名
        assert "Grey Fox" in char_data_section, "characters_json 应包含 name_en 'Grey Fox'"
        assert "Milly" in char_data_section, "characters_json 应包含 name_en 'Milly'"
        assert "Jiu Jiu" in char_data_section, "characters_json 应包含 name_en 'Jiu Jiu'"

    def test_case10_clothing_chinese_excluded_from_characters_json(
        self, director, test19_characters, scene_with_chinese_heading
    ):
        """
        Case 10: 含中文的 clothing 字段不应出现在 characters_json 的 clothing_summary 中
        char_001 top="一件手工缝制的藕灰色棉麻小褂" → 纯中文应被排除
        char_002 top="light blue knit top" → 纯英文应保留
        """
        visual_tone = {"mood": "gentle"}
        prompt = director._build_scene_prompt(
            scene=scene_with_chinese_heading,
            characters=test19_characters,
            visual_tone=visual_tone,
            style_preset="anime",
            shot_id_start=1,
        )

        char_data_start = prompt.index("Character data:") + len("Character data:\n")
        char_data_section = prompt[char_data_start:char_data_start + 1000]

        # char_001 纯中文 clothing 不应出现
        assert "藕灰色" not in char_data_section
        assert "棉麻小褂" not in char_data_section
        assert "宽松棉麻长裙" not in char_data_section

        # char_002 英文 clothing 应保留
        assert "light blue knit top" in char_data_section
        assert "white shorts" in char_data_section


class TestBuildScenePromptSceneJson:
    """
    RISK-T19-8: _build_scene_prompt scene_json 字段验证
    """

    def test_case11_scene_heading_chinese_replaced_in_scene_json(
        self, director, test19_characters, scene_with_chinese_heading
    ):
        """
        Case 11: scene_json 中 scene_heading 含中文时应被替换为 "Scene {id}"
        不应把 "EXT. 白桦树下 - 立春清晨 - 晴" 直接传入 scene_json
        """
        visual_tone = {"mood": "peaceful"}
        prompt = director._build_scene_prompt(
            scene=scene_with_chinese_heading,
            characters=test19_characters,
            visual_tone=visual_tone,
            style_preset="anime",
            shot_id_start=1,
        )

        # scene_json 在 "Scene data:\n" 之后
        assert "Scene data:" in prompt
        scene_data_start = prompt.index("Scene data:") + len("Scene data:\n")
        scene_data_section = prompt[scene_data_start:scene_data_start + 600]

        # 中文 scene_heading 不应直接出现在 scene_json 中
        assert "白桦树下" not in scene_data_section, \
            "scene_json 不应包含中文 scene_heading '白桦树下'"
        assert "立春清晨" not in scene_data_section, \
            "scene_json 不应包含中文 scene_heading '立春清晨'"

        # 应替换为安全占位
        assert "Scene 7" in scene_data_section

    def test_case12_atmosphere_chinese_filtered_in_scene_json(
        self, director, test19_characters, scene_with_chinese_heading
    ):
        """
        Case 12: scene_json 中 atmosphere 含中文时应经 _atmosphere_to_str 过滤
        "远山鸟鸣稀疏", "凛冽中带一丝初春" 不应出现在 scene_json atmosphere 字段
        """
        visual_tone = {"mood": "peaceful"}
        prompt = director._build_scene_prompt(
            scene=scene_with_chinese_heading,
            characters=test19_characters,
            visual_tone=visual_tone,
            style_preset="anime",
            shot_id_start=1,
        )

        # atmosphere 相关中文不应泄露到 scene_json 中
        assert "远山鸟鸣" not in prompt[:3000], \
            "scene_json atmosphere 不应包含中文 '远山鸟鸣'"
        assert "凛冽" not in prompt[:3000], \
            "scene_json atmosphere 不应包含中文 '凛冽'"
        # 英文 mood 应保留
        assert "tranquil" in prompt[:3000]


class TestBuildScenePromptEnglishRule:
    """
    RISK-T19-8: _build_scene_prompt 开头英文铁律规则验证
    """

    def test_case13_prompt_contains_english_mandate(
        self, director, test19_characters, scene_with_chinese_heading
    ):
        """
        Case 13: prompt 开头应包含 image_prompt MUST BE WRITTEN ENTIRELY IN ENGLISH 规则
        """
        visual_tone = {"mood": "peaceful"}
        prompt = director._build_scene_prompt(
            scene=scene_with_chinese_heading,
            characters=test19_characters,
            visual_tone=visual_tone,
            style_preset="anime",
            shot_id_start=1,
        )

        # 检查英文铁律规则存在
        assert "IMAGE_PROMPT MUST BE WRITTEN ENTIRELY IN ENGLISH" in prompt, \
            "prompt 应包含 image_prompt 全英文强制规则"
        assert "CRITICAL" in prompt[:2000], \
            "英文铁律应在 prompt 前部（CRITICAL 关键词）"

    def test_case14_prompt_warns_about_chinese_sources(
        self, director, test19_characters, scene_with_chinese_heading
    ):
        """
        Case 14: prompt 应明确告知 LLM action_beats/narration 的中文仅供理解使用
        """
        visual_tone = {"mood": "peaceful"}
        prompt = director._build_scene_prompt(
            scene=scene_with_chinese_heading,
            characters=test19_characters,
            visual_tone=visual_tone,
            style_preset="anime",
            shot_id_start=1,
        )

        # 应告知 LLM 中文来源仅供理解，不应复制进 image_prompt
        assert "UNDERSTANDING ONLY" in prompt or "understanding only" in prompt.lower(), \
            "prompt 应明确告知 LLM 中文字段仅供理解，不可复制进 image_prompt"


class TestBuildScenePromptEnglishNameFallback:
    """
    RISK-T19-8: 当 name_en 缺失时的兜底逻辑
    """

    def test_case15_missing_name_en_uses_name(self, director, scene_with_chinese_heading):
        """
        Case 15: 角色无 name_en 字段时，兜底用 name
        （这是边界情况，正常生成的角色都应有 name_en）
        """
        characters_no_name_en = {
            "characters": [
                {
                    "id": "char_001",
                    "name": "TestChar",  # 英文 name，无 name_en
                    "character_type": "human",
                    "clothing": {"top": "blue shirt", "bottom": "jeans"},
                }
            ]
        }
        visual_tone = {"mood": "peaceful"}
        prompt = director._build_scene_prompt(
            scene=scene_with_chinese_heading,
            characters=characters_no_name_en,
            visual_tone=visual_tone,
            style_preset="anime",
            shot_id_start=1,
        )

        # 应使用 name 作为兜底
        assert "TestChar" in prompt

    def test_case16_name_en_takes_priority_over_name(self, director, scene_with_chinese_heading):
        """
        Case 16: name_en 存在时优先使用 name_en（不用中文 name）
        """
        characters_with_name_en = {
            "characters": [
                {
                    "id": "char_001",
                    "name": "灰狐",
                    "name_en": "Grey Fox",
                    "character_type": "anthropomorphic_animal",
                    "clothing": {"top": "grey cape", "bottom": "linen skirt"},
                }
            ]
        }
        visual_tone = {"mood": "peaceful"}
        prompt = director._build_scene_prompt(
            scene=scene_with_chinese_heading,
            characters=characters_with_name_en,
            visual_tone=visual_tone,
            style_preset="anime",
            shot_id_start=1,
        )

        char_data_start = prompt.index("Character data:") + len("Character data:\n")
        char_data_section = prompt[char_data_start:char_data_start + 500]

        assert "Grey Fox" in char_data_section, "应优先使用 name_en 'Grey Fox'"
        assert "灰狐" not in char_data_section, "不应使用中文 name '灰狐'"


# ══════════════════════════════════════════════════════════════════
# Section 3: Wave 12+13 Regression — 不破坏已有防御
# ══════════════════════════════════════════════════════════════════


class TestWave12And13Regression:
    """确保 Wave 14 修复不破坏 Wave 12+13 已有的防御逻辑"""

    def test_regression_atmosphere_to_str_still_works(self):
        """Wave 12 regression: _atmosphere_to_str 中文过滤正常工作"""
        atm = {
            "mood": "tranquil",
            "sound_design_hint": "远山鸟鸣稀疏",
            "temperature_feel": "凛冽中带一丝初春的微暖"
        }
        result = _atmosphere_to_str(atm)
        assert "tranquil" in result
        assert "远山" not in result
        assert not _contains_chinese(result)

    def test_regression_contains_chinese_still_accurate(self):
        """Wave 12+13 regression: _contains_chinese 基本功能不变"""
        assert _contains_chinese("白桦树下") is True
        assert _contains_chinese("Birch tree") is False
        assert _contains_chinese("") is False
        assert _contains_chinese("EXT. Forest - Dawn") is False

    def test_regression_fallback_scene_heading_defense_intact(self):
        """Wave 13 regression: fallback 路径 scene_heading 中文防御仍然工作"""
        # 模拟 _generate_scene_shots fallback 路径
        scene_heading = "EXT. 白桦树下 - 立春清晨 - 晴"
        scene_id = 7

        if _contains_chinese(scene_heading):
            scene_heading_safe = f"Scene {scene_id}"
        else:
            scene_heading_safe = scene_heading

        assert scene_heading_safe == "Scene 7"
        assert not _contains_chinese(scene_heading_safe)

    def test_regression_english_scene_heading_not_replaced(self):
        """Wave 13 regression: 英文 scene_heading 不应被替换"""
        scene_heading = "EXT. Birch grove - Early spring morning - clear"
        scene_id = 7

        if _contains_chinese(scene_heading):
            scene_heading_safe = f"Scene {scene_id}"
        else:
            scene_heading_safe = scene_heading

        assert "Birch grove" in scene_heading_safe
        assert "Scene 7" not in scene_heading_safe
