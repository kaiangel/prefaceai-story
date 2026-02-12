"""
使用真实 story.json 数据测试兼容性代码
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.character_prompt_builder import CharacterPromptBuilder
from app.services.storyboard_service import StoryboardService
from app.services.unified_prompt_builder import UnifiedPromptBuilder


def test_with_real_data():
    """使用真实数据测试兼容性代码"""
    print("=" * 60)
    print("使用真实 story.json 数据测试兼容性代码")
    print("=" * 60)

    # 读取真实的story.json
    story_path = "test_output/manualtest/teststory6.1/story.json"
    if not os.path.exists(story_path):
        print(f"❌ 找不到测试文件: {story_path}")
        return

    with open(story_path, 'r', encoding='utf-8') as f:
        story = json.load(f)

    characters = story.get('characters', [])
    print(f"\n找到 {len(characters)} 个角色")

    builder = CharacterPromptBuilder()
    storyboard = StoryboardService()

    print("\n" + "=" * 60)
    print("开始测试...")
    print("=" * 60)

    for char in characters:
        print(f"\n处理角色: {char.get('name')} ({char.get('name_en')})")
        print("-" * 40)

        # 测试 character_type 兼容性
        char_type = builder._get_character_type(char)
        print(f"  角色类型: {char_type}")

        # 测试人类角色描述（会触发 age_appearance, gender 等兼容性代码）
        if char_type == 'human':
            desc = builder._build_human_description(char)
            print(f"  人类描述: {desc[:80]}...")

        # 测试 storyboard 的描述构建
        sb_desc = storyboard._build_character_description(char)
        print(f"  Storyboard描述: {sb_desc[:80]}...")

    # 测试 unified_prompt_builder 的 role 兼容性
    print("\n" + "=" * 60)
    print("测试 UnifiedPromptBuilder role 字段兼容性")
    print("=" * 60)

    upb = UnifiedPromptBuilder()

    # 模拟一个shot数据
    mock_shot = {
        "narration": "苏晨和林薇在咖啡馆相遇",
        "image_prompt": "Su Chen and Lin Wei meet in a cafe"
    }

    # 调用会触发 role_in_story/role 兼容性代码的方法
    filtered_chars = upb._filter_characters_for_shot(mock_shot, characters)
    print(f"  筛选后的角色数: {len(filtered_chars)}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("如果上面有 '⚠️ [COMPAT WARNING]' 消息，")
    print("说明LLM输出的数据格式确实触发了兼容性代码。")
    print("=" * 60)


if __name__ == "__main__":
    test_with_real_data()
