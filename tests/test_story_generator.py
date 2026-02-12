"""Test script for story generation"""

import asyncio
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.story_generator import StoryGenerator


def test_story_generation():
    """Test the story generation with a sample idea (sync version)"""
    print("=" * 60)
    print("序话Story - Story Generation Test")
    print("=" * 60)

    generator = StoryGenerator()

    # Test case
    idea = "一个程序员加班到深夜，意外发现公司AI系统有了自我意识，两人展开了一段关于人生意义的对话"

    print(f"\n测试创意: {idea}")
    print(f"主要模型: {generator.CLAUDE_MODEL}")
    print(f"备用模型: {generator.GEMINI_MODELS}")
    print("\n正在生成故事（这可能需要30-60秒）...")

    # Use sync version for more stable connection
    result = generator.generate_story_sync(
        idea=idea,
        style="cyberpunk",
        chapter_number=1,
        total_chapters=1,
        duration_minutes=3,
        character_count=2,
        language="zh-CN",
    )

    if result["success"]:
        print(f"\n✅ 故事生成成功！")
        print(f"   使用模型: {result.get('model_used', 'unknown')}")
        print(f"   提供商: {result.get('provider', 'unknown')}")
        print(f"   尝试次数: {result.get('attempts', 'unknown')}")
        print("-" * 60)

        story = result["data"]

        print(f"\n📖 标题: {story.get('title', 'N/A')}")
        print(f"\n📝 摘要: {story.get('summary', 'N/A')}")

        print("\n👥 角色:")
        for char in story.get("characters", []):
            print(f"  - {char.get('name')}: {char.get('description')}")
            print(f"    性格: {char.get('personality')}")

        print(f"\n🎬 场景数: {story.get('total_scenes', len(story.get('scenes', [])))}")
        print(f"📊 字数: {story.get('word_count', 'N/A')}")

        print("\n🎥 分镜详情:")
        for scene in story.get("scenes", []):
            print(f"\n  场景 {scene.get('scene_id')}:")
            print(f"    地点: {scene.get('location')}")
            print(f"    时间: {scene.get('time')}")
            print(f"    氛围: {scene.get('mood')}")
            print(f"    画面: {scene.get('visual_description')[:100]}...")
            print(f"    旁白: {scene.get('narration')[:100]}...")

        print("\n" + "-" * 60)
        print(f"Token使用: {result.get('usage', {})}")

        # Save full result to file
        with open("test_story_output.json", "w", encoding="utf-8") as f:
            json.dump(result["data"], f, ensure_ascii=False, indent=2)
        print("\n完整结果已保存到 test_story_output.json")

    else:
        print(f"\n❌ 故事生成失败!")
        print(f"错误: {result.get('error')}")


def main():
    """Run the test"""
    test_story_generation()


if __name__ == "__main__":
    main()
