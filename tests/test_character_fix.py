#!/usr/bin/env python3
"""
测试角色描述修复效果

只测试shots.json生成，验证：
1. shot_02的prompt中应该是Li Xiang（李想）而非Chen Mo
2. 多人场景的prompt中应该包含所有角色的描述
"""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.storyboard_service import StoryboardService


async def test_character_fix():
    """测试角色描述修复"""

    # 使用teststory6.3的story.json
    story_path = "test_output/manualtest/teststory6.3/story.json"

    if not os.path.exists(story_path):
        print(f"❌ 找不到 {story_path}")
        print("请先运行 teststory6.3 测试生成 story.json")
        return False

    with open(story_path, 'r', encoding='utf-8') as f:
        story = json.load(f)

    scenes = story.get('scenes', [])
    characters = story.get('characters', [])
    style = story.get('visual_style', {}).get('art_style', 'realistic')

    print(f"📖 加载story: {len(scenes)} scenes, {len(characters)} characters")

    # 打印角色信息
    print("\n👥 角色列表:")
    for c in characters:
        print(f"  - {c.get('id')}: {c.get('name')} ({c.get('name_en')})")

    # 生成shots
    service = StoryboardService()
    shots = await service.generate_storyboard_with_splitting(
        scenes=scenes,
        characters=characters,
        style_preset=style
    )

    print(f"\n📷 生成了 {len(shots)} 个shots")

    # 验证关键shots
    print("\n" + "="*80)
    print("验证角色描述修复效果")
    print("="*80)

    test_results = []

    # 测试shot_02 (应该是李想，char_002)
    if len(shots) >= 2:
        shot = shots[1]  # shot_02
        prompt = shot.get('image_prompt', '')
        chars_in_scene = shot.get('characters_in_scene', [])

        print(f"\n【Shot 02】")
        print(f"  characters_in_scene: {chars_in_scene}")

        # 检查prompt中的角色
        has_li_xiang = 'Li Xiang' in prompt or 'li xiang' in prompt.lower()
        has_chen_mo = 'Chen Mo' in prompt or 'chen mo' in prompt.lower()

        print(f"  prompt包含 Li Xiang: {has_li_xiang}")
        print(f"  prompt包含 Chen Mo: {has_chen_mo}")

        # 期望：chars_in_scene是char_002时，prompt应该有Li Xiang
        if 'char_002' in chars_in_scene:
            if has_li_xiang and not has_chen_mo:
                print(f"  ✅ 正确：只包含李想的描述")
                test_results.append(True)
            elif has_chen_mo:
                print(f"  ❌ 错误：包含了陈默的描述（应该只有李想）")
                test_results.append(False)
            else:
                print(f"  ⚠️ 警告：没有找到角色描述")
                test_results.append(False)

        # 打印prompt片段
        if 'Characters:' in prompt:
            start = prompt.find('Characters:')
            end = prompt.find('.', start + 50)
            if end == -1:
                end = start + 200
            print(f"  prompt角色部分: ...{prompt[start:end]}...")

    # 测试多人场景 (scene 4, 5, 6 等都是三人同框)
    multi_char_shots = [s for s in shots if len(s.get('characters_in_scene', [])) >= 3]

    if multi_char_shots:
        shot = multi_char_shots[0]
        shot_id = shots.index(shot) + 1
        prompt = shot.get('image_prompt', '')
        chars_in_scene = shot.get('characters_in_scene', [])

        print(f"\n【Shot {shot_id:02d}（三人同框）】")
        print(f"  characters_in_scene: {chars_in_scene}")

        # 检查是否包含所有三个角色
        has_chen_mo = 'Chen Mo' in prompt
        has_li_xiang = 'Li Xiang' in prompt
        has_zhang_ye = 'Zhang Ye' in prompt

        print(f"  prompt包含 Chen Mo: {has_chen_mo}")
        print(f"  prompt包含 Li Xiang: {has_li_xiang}")
        print(f"  prompt包含 Zhang Ye: {has_zhang_ye}")

        if has_chen_mo and has_li_xiang and has_zhang_ye:
            print(f"  ✅ 正确：包含所有三个角色的描述")
            test_results.append(True)
        else:
            missing = []
            if not has_chen_mo: missing.append("Chen Mo")
            if not has_li_xiang: missing.append("Li Xiang")
            if not has_zhang_ye: missing.append("Zhang Ye")
            print(f"  ❌ 错误：缺少角色 {missing}")
            test_results.append(False)

        # 打印prompt角色部分
        if 'Characters:' in prompt:
            start = prompt.find('Characters:')
            end = prompt.find('. Scene style:', start)
            if end == -1:
                end = start + 500
            print(f"  prompt角色部分:\n    {prompt[start:end]}")

    # 总结
    print("\n" + "="*80)
    passed = sum(test_results)
    total = len(test_results)
    print(f"验证结果: {passed}/{total} 通过")

    if passed == total:
        print("✅ 角色描述修复成功！")
        return True
    else:
        print("❌ 仍有问题需要修复")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_character_fix())
    sys.exit(0 if result else 1)
