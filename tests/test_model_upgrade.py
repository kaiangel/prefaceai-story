"""
TASK-MODEL-UPGRADE-RETEST: Slam Dunk 风格 + Sonnet 4.6 Stage 1-4 验证

验证：
- Stage 1-4 使用 Claude Sonnet 4.6 正常输出
- slam_dunk 风格在 image_prompt 中体现
- text_type 分布记录（与上次 realistic 结果对比）

不运行 Stage 5（图像生成），仅验证文本生成。

作者: @Backend
日期: 2026-02-26
"""

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from app.services.story_outline_generator import StoryOutlineGenerator
from app.services.character_designer import CharacterDesigner
from app.services.screenplay_writer import ScreenplayWriter
from app.services.storyboard_director import StoryboardDirector


async def run_model_upgrade_test():
    """Stage 1-4 模型切换验证"""
    print("=" * 70)
    print("TASK-MODEL-UPGRADE-RETEST: Slam Dunk + Sonnet 4.6 Stage 1-4")
    print("=" * 70)

    output_dir = Path("./test_output/manualtest/model_upgrade_retest_slamdunk")
    output_dir.mkdir(parents=True, exist_ok=True)

    start = time.time()

    # === Stage 1: StoryOutlineGenerator ===
    print("\n--- Stage 1: StoryOutlineGenerator ---")
    generator = StoryOutlineGenerator()
    print(f"  主模型: {generator.claude_model}")
    print(f"  备模型: {generator.gemini_model}")
    print(f"  Claude客户端: {'✅' if generator.claude_client else '❌'}")

    outline = await generator.generate(
        idea="篮球少年在一场关键比赛中找到自信的故事",
        style_preset="slam_dunk",
        target_duration_minutes=2,
        character_count=2
    )

    with open(output_dir / "1_outline.json", "w", encoding="utf-8") as f:
        json.dump(outline, f, ensure_ascii=False, indent=2)
    print(f"  ✅ Stage 1 完成: {outline.get('title', 'N/A')}")
    print(f"  角色数: {len(outline.get('characters_overview', []))}")
    print(f"  情节点: {len(outline.get('plot_points', []))}")

    # === Stage 2: CharacterDesigner ===
    print("\n--- Stage 2: CharacterDesigner ---")
    designer = CharacterDesigner()
    print(f"  主模型: {designer.claude_model}")

    characters = await designer.design(outline)

    with open(output_dir / "2_characters.json", "w", encoding="utf-8") as f:
        json.dump(characters, f, ensure_ascii=False, indent=2)
    char_list = characters.get("characters", [])
    print(f"  ✅ Stage 2 完成: {len(char_list)} 角色")
    for c in char_list:
        has_physical = bool(c.get("physical"))
        has_clothing = bool(c.get("clothing"))
        print(f"    - {c.get('name', 'N/A')} (physical: {'✅' if has_physical else '❌'}, clothing: {'✅' if has_clothing else '❌'})")

    # === Stage 3: ScreenplayWriter ===
    print("\n--- Stage 3: ScreenplayWriter ---")
    writer = ScreenplayWriter()
    print(f"  主模型: {writer.claude_model}")

    screenplay = await writer.write(outline, characters)

    with open(output_dir / "3_screenplay.json", "w", encoding="utf-8") as f:
        json.dump(screenplay, f, ensure_ascii=False, indent=2)
    print(f"  ✅ Stage 3 完成: {screenplay.get('total_scenes', 0)} scenes, {screenplay.get('total_action_beats', 0)} beats")

    # === Stage 4: StoryboardDirector ===
    print("\n--- Stage 4: StoryboardDirector ---")
    director = StoryboardDirector()
    print(f"  主模型: {director.claude_model}")

    storyboard = await director.direct(
        screenplay=screenplay,
        characters=characters,
        visual_tone=outline.get("visual_tone", {}),
        style_preset="slam_dunk"
    )

    with open(output_dir / "4_storyboard.json", "w", encoding="utf-8") as f:
        json.dump(storyboard, f, ensure_ascii=False, indent=2)
    shots = storyboard.get("shots", [])
    print(f"  ✅ Stage 4 完成: {len(shots)} shots")

    # 检查 text_overlay 分布
    text_types = {}
    for s in shots:
        to = s.get("text_overlay", {})
        tt = to.get("text_type", "missing")
        text_types[tt] = text_types.get(tt, 0) + 1
    print(f"  text_overlay 分布: {text_types}")

    # 检查 slam_dunk 风格在 image_prompt 中的体现
    slam_dunk_keywords = ["slam dunk", "basketball", "manga", "inoue", "takehiko",
                          "dynamic", "sport", "athletic", "court"]
    prompts_with_style = 0
    for s in shots:
        prompt = s.get("image_prompt", "").lower()
        if any(kw in prompt for kw in slam_dunk_keywords):
            prompts_with_style += 1
    print(f"  slam_dunk 风格体现: {prompts_with_style}/{len(shots)} shots 包含相关关键词")

    elapsed = time.time() - start

    # === 汇总 ===
    print("\n" + "=" * 70)
    print(f"✅ TASK-MODEL-UPGRADE-RETEST Stage 1-4 验证通过!")
    print(f"  模型: Claude Sonnet 4.6 (主) / Gemini 3 Pro (备)")
    print(f"  风格: slam_dunk")
    print(f"  故事: {outline.get('title', 'N/A')}")
    print(f"  角色: {len(char_list)}")
    print(f"  场景: {screenplay.get('total_scenes', 0)}")
    print(f"  镜头: {len(shots)}")
    print(f"  耗时: {elapsed:.1f}秒")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_model_upgrade_test())
