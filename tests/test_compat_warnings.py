"""
测试兼容性代码警告

这个脚本模拟旧格式的数据来验证兼容性代码分支是否会被触发
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.character_prompt_builder import CharacterPromptBuilder
from app.services.storyboard_service import StoryboardService


def test_compat_warnings():
    """测试兼容性警告"""
    print("=" * 60)
    print("测试兼容性代码警告")
    print("=" * 60)

    builder = CharacterPromptBuilder()
    storyboard = StoryboardService()

    # 测试1: 旧格式 'type' 字段
    print("\n[TEST 1] 测试旧格式 'type' 字段 (应触发警告)")
    old_format_char_1 = {
        "name": "测试角色1",
        "type": "human",  # 旧格式，应该用 character_type
    }
    char_type = builder._get_character_type(old_format_char_1)
    print(f"  → 结果: {char_type}")

    # 测试2: 新格式 'character_type' 字段
    print("\n[TEST 2] 测试新格式 'character_type' 字段 (不应触发警告)")
    new_format_char = {
        "name": "测试角色2",
        "character_type": "human",
    }
    char_type = builder._get_character_type(new_format_char)
    print(f"  → 结果: {char_type}")

    # 测试3: 旧格式 'age_appearance' 字段
    print("\n[TEST 3] 测试旧格式 'age_appearance' 字段 (应触发警告)")
    old_format_char_3 = {
        "name": "测试角色3",
        "character_type": "human",
        "age_appearance": "young adult",  # 旧格式，应该用 human.age_range
        "human": {}
    }
    desc = builder._build_human_description(old_format_char_3)
    print(f"  → 结果: {desc[:100]}...")

    # 测试4: 旧格式根级 'gender' 字段
    print("\n[TEST 4] 测试旧格式根级 'gender' 字段 (应触发警告)")
    old_format_char_4 = {
        "name": "测试角色4",
        "character_type": "human",
        "gender": "female",  # 旧格式，应该用 human.gender
        "human": {}
    }
    desc = builder._build_human_description(old_format_char_4)
    print(f"  → 结果: {desc[:100]}...")

    # 测试5: 新格式 human 字段
    print("\n[TEST 5] 测试新格式 human 字段 (不应触发警告)")
    new_format_char_5 = {
        "name": "测试角色5",
        "character_type": "human",
        "human": {
            "age_range": "young adult",
            "gender": "female"
        }
    }
    desc = builder._build_human_description(new_format_char_5)
    print(f"  → 结果: {desc[:100]}...")

    # 测试6: storyboard 的 description/appearance fallback
    print("\n[TEST 6] 测试 description/appearance fallback (应触发警告)")
    old_format_char_6 = {
        "name": "测试角色6",
        "description": "A tall man with dark hair",  # 旧格式 fallback
    }
    desc = storyboard._build_character_description(old_format_char_6)
    print(f"  → 结果: {desc}")

    # 测试7: storyboard 新格式 physical/clothing
    print("\n[TEST 7] 测试新格式 physical/clothing (不应触发警告)")
    new_format_char_7 = {
        "name": "测试角色7",
        "physical": {
            "hair_color": "black",
            "eye_color": "brown"
        },
        "clothing": {
            "top": "blue shirt"
        }
    }
    desc = storyboard._build_character_description(new_format_char_7)
    print(f"  → 结果: {desc}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("如果上面显示了 '⚠️ [COMPAT WARNING]' 消息，")
    print("说明这些兼容代码分支被触发了。")
    print("=" * 60)


if __name__ == "__main__":
    test_compat_warnings()
