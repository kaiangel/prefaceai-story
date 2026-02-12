"""
Phase 2.0 完整流程测试

测试5阶段生成流程：
1. StoryOutlineGenerator - 故事大纲
2. CharacterDesigner - 角色设计
3. ScreenplayWriter - 分场剧本
4. StoryboardDirector - 分镜脚本
5. ShotImageGenerator - 镜头图像生成

使用方法：
    # 完整测试（包含图像生成）
    python tests/test_phase2_full_pipeline.py

    # 仅测试文本生成（不生成图像）
    python tests/test_phase2_full_pipeline.py --no-images

    # 自定义idea
    python tests/test_phase2_full_pipeline.py --idea "凌晨便利店三个失眠的人"
"""

import os
import sys
import json
import asyncio
import argparse
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_individual_stages():
    """测试各个阶段独立运行"""
    print("\n" + "="*60)
    print("测试各阶段独立运行")
    print("="*60)

    # Stage 1
    print("\n--- Stage 1: StoryOutlineGenerator ---")
    from app.services.story_outline_generator import StoryOutlineGenerator

    generator = StoryOutlineGenerator()
    outline = await generator.generate(
        idea="雨夜公交站，错过末班车的三个人",
        style_preset="realistic",
        target_duration_minutes=3
    )

    print(f"标题: {outline.get('title')}")
    print(f"Logline: {outline.get('logline')}")
    print(f"角色数: {len(outline.get('characters_overview', []))}")
    print(f"场景数: {len(outline.get('unique_locations', []))}")

    # Stage 2
    print("\n--- Stage 2: CharacterDesigner ---")
    from app.services.character_designer import CharacterDesigner

    designer = CharacterDesigner()
    characters = await designer.design(outline)

    for char in characters.get("characters", []):
        print(f"  - {char.get('name')} ({char.get('role')})")
        print(f"    发型: {char.get('physical', {}).get('hair_style', 'N/A')}")
        print(f"    上衣: {char.get('clothing', {}).get('top', 'N/A')}")

    # Stage 3
    print("\n--- Stage 3: ScreenplayWriter ---")
    from app.services.screenplay_writer import ScreenplayWriter

    writer = ScreenplayWriter()
    screenplay = await writer.write(outline, characters)

    scenes = screenplay.get("scenes", [])
    print(f"总场景数: {len(scenes)}")
    print(f"总动作节拍: {screenplay.get('total_action_beats', 0)}")
    print(f"总旁白字数: {screenplay.get('total_narration_words', 0)}")

    for scene in scenes[:2]:  # 只显示前2个场景
        print(f"\n  Scene {scene.get('scene_id')}: {scene.get('scene_heading', 'N/A')}")
        print(f"    动作节拍: {len(scene.get('action_beats', []))}个")
        narration = scene.get('narration', '')[:100]
        print(f"    旁白: {narration}...")

    # Stage 4
    print("\n--- Stage 4: StoryboardDirector ---")
    from app.services.storyboard_director import StoryboardDirector

    director = StoryboardDirector()
    storyboard = await director.direct(
        screenplay=screenplay,
        characters=characters,
        visual_tone=outline.get("visual_tone", {}),
        style_preset="realistic"
    )

    shots = storyboard.get("shots", [])
    print(f"总镜头数: {len(shots)}")
    print(f"全局视觉指导: {storyboard.get('global_visual_direction', {}).get('style_preset', 'N/A')}")

    for shot in shots[:3]:  # 只显示前3个镜头
        camera = shot.get("camera", {})
        print(f"\n  Shot {shot.get('shot_id')}:")
        print(f"    景别: {camera.get('shot_size', 'N/A')}")
        print(f"    角度: {camera.get('angle', 'N/A')}")
        print(f"    动作: {shot.get('action_description', 'N/A')[:50]}...")

    return {
        "outline": outline,
        "characters": characters,
        "screenplay": screenplay,
        "storyboard": storyboard
    }


async def test_full_pipeline(idea: str, style: str, duration: int, generate_images: bool, shots_limit: int = 0):
    """测试完整Pipeline"""
    print("\n" + "="*60)
    print("测试完整Pipeline (Phase2PipelineOrchestrator)")
    print("="*60)

    from app.services.pipeline_orchestrator import Phase2PipelineOrchestrator

    output_dir = "./test_output/manualtest/phase2"
    orchestrator = Phase2PipelineOrchestrator(output_dir=output_dir)

    result = await orchestrator.run(
        idea=idea,
        style_preset=style,
        target_duration_minutes=duration,
        generate_images=generate_images,
        max_concurrent_images=2,
        shots_limit=shots_limit
    )

    if result.get("success"):
        summary = result.get("summary", {})
        print("\n✅ Pipeline 成功完成!")
        print(f"  项目目录: {summary.get('project_dir')}")
        print(f"  故事标题: {summary.get('title')}")
        print(f"  角色数: {summary.get('total_characters')}")
        print(f"  场景数: {summary.get('total_scenes')}")
        print(f"  镜头数: {summary.get('total_shots')}")
        print(f"  总耗时: {summary.get('pipeline_duration_seconds')}秒")
    else:
        print(f"\n❌ Pipeline 失败: {result.get('error')}")
        print(f"  失败阶段: {result.get('failed_stage')}")

    return result


async def test_phase2_prompt_builder():
    """测试Phase2PromptBuilder"""
    print("\n" + "="*60)
    print("测试 Phase2PromptBuilder")
    print("="*60)

    from app.prompts.storyboard_prompts import Phase2PromptBuilder

    # 模拟shot数据
    shot = {
        "shot_id": 1,
        "action_description": "李铭从远处跑来，公文包挡在头顶挡雨",
        "camera": {
            "shot_size": "medium_shot",
            "angle": "eye_level",
            "movement": "static"
        },
        "composition": {
            "framing": "rule_of_thirds",
            "depth": "shallow",
            "focus_point": "character_face"
        },
        "lighting": {
            "key_light": "streetlight_overhead",
            "mood": "melancholic",
            "time_of_day": "night"
        },
        "character_direction": {
            "characters_visible": ["char_001"]
        },
        "location_id": "bus_station"
    }

    characters = {
        "characters": [
            {
                "id": "char_001",
                "name": "李铭",
                "name_en": "Li Ming",
                "physical": {
                    "hair_color": "jet black",
                    "hair_style": "short messy",
                    "eye_color": "dark brown",
                    "skin_tone": "fair"
                },
                "clothing": {
                    "top": "wrinkled white dress shirt",
                    "bottom": "navy dress pants"
                }
            }
        ]
    }

    # 模拟storyboard数据
    storyboard = {
        "global_visual_direction": {
            "overall_mood": "melancholic_intimate",
            "lighting_style": "low_key_dramatic",
            "color_palette": ["deep blue", "cold gray", "warm amber"],
            "style_preset": "realistic"
        },
        "shot_continuity_notes": [],
        "shots": [shot]
    }

    previous_shot = {
        "shot_id": 0,
        "action_description": "空镜头",
        "camera": {"shot_size": "wide_shot"}
    }

    builder = Phase2PromptBuilder(
        storyboard=storyboard,
        characters=characters,
        style_preset="realistic"
    )
    prompt_package = builder.build_full_prompt(
        shot=shot,
        previous_shot=previous_shot,
        include_system_instruction=True
    )

    print("\n--- System Instruction ---")
    print(prompt_package.get("system_instruction", "N/A")[:500])

    print("\n--- Image Prompt ---")
    print(prompt_package.get("image_prompt", "N/A")[:800])

    print("\n--- Character Mapping ---")
    print(prompt_package.get("character_mapping", "N/A"))

    print("\n--- Continuity Context ---")
    print(prompt_package.get("continuity_context", "N/A"))

    return prompt_package


def main():
    parser = argparse.ArgumentParser(description="Phase 2.0 Pipeline 测试")
    parser.add_argument("--idea", type=str, default="雨夜公交站，错过末班车的三个人",
                        help="故事创意")
    parser.add_argument("--style", type=str, default="realistic",
                        help="视觉风格 (realistic, cartoon, anime, etc.)")
    parser.add_argument("--duration", type=int, default=3,
                        help="目标时长（分钟）")
    parser.add_argument("--no-images", action="store_true",
                        help="不生成图像，仅测试文本流程")
    parser.add_argument("--stages-only", action="store_true",
                        help="仅测试各阶段独立运行")
    parser.add_argument("--prompt-only", action="store_true",
                        help="仅测试PromptBuilder")
    parser.add_argument("--shots-limit", type=int, default=0,
                        help="限制生成的shot数量（0=不限制）")

    args = parser.parse_args()

    async def run_tests():
        if args.prompt_only:
            await test_phase2_prompt_builder()
        elif args.stages_only:
            await test_individual_stages()
        else:
            await test_full_pipeline(
                idea=args.idea,
                style=args.style,
                duration=args.duration,
                generate_images=not args.no_images,
                shots_limit=args.shots_limit
            )

    asyncio.run(run_tests())


if __name__ == "__main__":
    main()
