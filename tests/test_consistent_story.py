"""
角色一致性故事生成测试

测试新的角色一致性方案：
1. 故事生成时输出详细角色描述
2. 图片生成时注入角色描述
3. 验证角色在不同场景的一致性
"""

import asyncio
import json
import os
import sys
import shutil
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.story_generator import StoryGenerator
from app.services.consistent_image_generator import ConsistentImageGenerator, create_generator_from_story
from app.services.tts_service import TTSService
from app.services.whisper_service import WhisperService
from app.services.alignment_service import AlignmentService


# 输出目录
OUTPUT_DIR = "./test_output/manualtest/teststory2"


async def step1_generate_story_with_characters():
    """Step 1: 生成带详细角色描述的故事"""
    print("\n" + "=" * 60)
    print("Step 1: 生成故事（含详细角色描述）")
    print("=" * 60)

    generator = StoryGenerator()

    # 故事主题
    idea = "一只小猫咪在城市里迷路后，遇到了一只善良的流浪狗，它们结伴寻找小猫的家，途中经历了一些小冒险，最终小猫找到回家的路"
    style = "warm_illustration"

    print(f"主题: {idea}")
    print(f"风格: {style}")
    print("正在生成故事（包含详细角色描述）...")

    result = await generator.generate_story(
        idea=idea,
        style=style,
        chapter_number=1,
        total_chapters=1,
        duration_minutes=1,
        character_count=2,
        language="zh-CN"
    )

    if not result.get("success"):
        print(f"生成失败: {result.get('error')}")
        return None

    story = result.get("data")
    if not story:
        print("无法获取故事数据")
        return None

    print(f"\n✅ 故事生成成功!")
    print(f"  使用模型: {result.get('provider')}/{result.get('model_used')}")
    print(f"  故事标题: {story.get('title')}")

    # 检查角色描述
    characters = story.get("characters", [])
    print(f"  角色数量: {len(characters)}")

    for char in characters:
        print(f"\n  角色: {char.get('name')} ({char.get('name_en', 'N/A')})")
        print(f"    类型: {char.get('type', 'unknown')}")
        print(f"    ID: {char.get('id', 'N/A')}")

        # 检查是否有详细描述
        if char.get("animal"):
            animal = char["animal"]
            print(f"    毛色: {animal.get('fur_color', 'N/A')}")
            print(f"    图案: {animal.get('fur_pattern', 'N/A')}")
            print(f"    眼睛: {animal.get('eye_color', 'N/A')}")
        elif char.get("physical"):
            phys = char["physical"]
            print(f"    头发: {phys.get('hair_color', 'N/A')} {phys.get('hair_style', '')}")
            print(f"    眼睛: {phys.get('eye_color', 'N/A')}")

    # 检查视觉风格
    visual_style = story.get("visual_style", {})
    if visual_style:
        print(f"\n  视觉风格:")
        print(f"    艺术风格: {visual_style.get('art_style', 'N/A')}")
        print(f"    色调: {visual_style.get('color_palette', 'N/A')}")
        print(f"    光线: {visual_style.get('lighting', 'N/A')}")
        print(f"    氛围: {visual_style.get('atmosphere', 'N/A')}")

    # 检查场景
    scenes = story.get("scenes", [])
    print(f"\n  场景数量: {len(scenes)}")

    for scene in scenes:
        chars_in_scene = scene.get("characters_in_scene", [])
        print(f"    场景 {scene.get('scene_id')}: {len(chars_in_scene)} 个角色")

    # 保存故事
    with open(f"{OUTPUT_DIR}/story.json", "w", encoding="utf-8") as f:
        json.dump(story, f, ensure_ascii=False, indent=2)

    # 保存故事文档
    story_doc = f"""# {story.get('title')}

## 故事简介
{story.get('synopsis', story.get('summary', 'N/A'))}

## 视觉风格
- 艺术风格: {visual_style.get('art_style', 'N/A')}
- 渲染风格: {visual_style.get('rendering', 'N/A')}
- 色调: {visual_style.get('color_palette', 'N/A')}
- 主要颜色: {', '.join(visual_style.get('primary_colors', []))}
- 光线: {visual_style.get('lighting', 'N/A')}
- 氛围: {visual_style.get('atmosphere', 'N/A')}

## 角色设定

"""
    for char in characters:
        story_doc += f"""### {char.get('name')} ({char.get('name_en', '')})
- ID: {char.get('id')}
- 类型: {char.get('type')}
- 角色: {char.get('role')}
- 性别: {char.get('gender')}
- 年龄外观: {char.get('age_appearance')}
- 性格视觉: {char.get('personality_visual')}
- 默认表情: {char.get('default_expression')}

"""
        if char.get("animal"):
            a = char["animal"]
            story_doc += f"""**动物特征:**
- 物种: {a.get('species')} ({a.get('breed', 'N/A')})
- 毛色: {a.get('fur_color')}
- 图案: {a.get('fur_pattern')}
- 毛长: {a.get('fur_length')}
- 毛质: {a.get('fur_texture')}
- 体型: {a.get('body_size')} {a.get('body_shape', '')}
- 眼睛: {a.get('eye_color')} {a.get('eye_shape', '')}
- 鼻子: {a.get('nose_color')}
- 耳朵: {a.get('ear_shape')}
- 尾巴: {a.get('tail')}
- 特殊标记: {', '.join(a.get('distinctive_marks', []))}

"""

    story_doc += "## 场景详情\n\n"
    for scene in scenes:
        story_doc += f"""### 场景 {scene.get('scene_id')}
- 地点: {scene.get('location')}
- 时间: {scene.get('time')}
- 氛围: {scene.get('mood')}
- 出场角色: {', '.join(scene.get('characters_in_scene', []))}

**角色动作:**
"""
        for char_id, action in scene.get('character_actions', {}).items():
            story_doc += f"- {char_id}: {action}\n"

        story_doc += f"""
**画面描述:**
{scene.get('visual_description')}

**旁白:**
{scene.get('narration')}

---

"""

    with open(f"{OUTPUT_DIR}/story.md", "w", encoding="utf-8") as f:
        f.write(story_doc)

    print(f"\n故事文档已保存到: {OUTPUT_DIR}/story.md")

    return story


async def step2_generate_consistent_images(story: dict):
    """Step 2: 使用一致性图片生成器生成场景图片"""
    print("\n" + "=" * 60)
    print("Step 2: 生成一致性场景图片")
    print("=" * 60)

    if not story:
        print("没有故事数据，跳过图片生成")
        return None

    # 创建一致性图片生成器
    generator = create_generator_from_story(story)

    # 输出角色设定表
    character_sheet = generator.get_character_sheet()
    with open(f"{OUTPUT_DIR}/character_sheet.md", "w", encoding="utf-8") as f:
        f.write(character_sheet)
    print(f"角色设定表已保存: {OUTPUT_DIR}/character_sheet.md")

    # 创建图片目录
    images_dir = f"{OUTPUT_DIR}/images"
    os.makedirs(images_dir, exist_ok=True)

    scenes = story.get("scenes", [])
    image_results = []

    for scene in scenes:
        scene_id = scene.get("scene_id", 0)
        print(f"\n生成场景 {scene_id} 图片...")

        # 预览prompt
        preview = generator.get_prompt_preview(scene)
        print(f"  Prompt长度: {len(preview)} 字符")

        # 保存prompt预览
        with open(f"{images_dir}/scene_{scene_id}_prompt.txt", "w", encoding="utf-8") as f:
            f.write(preview)

        # 生成图片
        result = await generator.generate_scene_image(scene)

        if result.get("success") and result.get("image_data"):
            image_path = f"{images_dir}/scene_{scene_id}.png"
            image_data = result["image_data"]
            if isinstance(image_data, str):
                import base64
                image_data = base64.b64decode(image_data)
            with open(image_path, "wb") as f:
                f.write(image_data)

            print(f"  ✅ 已保存: {image_path}")
            print(f"  角色: {result.get('characters_included', [])}")

            image_results.append({
                "scene_id": scene_id,
                "image_path": image_path,
                "success": True,
                "characters": result.get("characters_included", [])
            })
        else:
            print(f"  ❌ 生成失败: {result.get('error')}")
            image_results.append({
                "scene_id": scene_id,
                "success": False,
                "error": result.get("error")
            })

        # 避免API速率限制
        await asyncio.sleep(3)

    # 保存图片生成日志
    with open(f"{OUTPUT_DIR}/images_log.json", "w", encoding="utf-8") as f:
        json.dump(image_results, f, ensure_ascii=False, indent=2)

    return image_results


async def step3_generate_tts(story: dict):
    """Step 3: 生成TTS语音"""
    print("\n" + "=" * 60)
    print("Step 3: 生成TTS语音合成")
    print("=" * 60)

    if not story:
        print("没有故事数据，跳过TTS生成")
        return None

    tts = TTSService()
    scenes = story.get("scenes", [])

    narrations = [scene.get("narration", "") for scene in scenes]
    full_narration = "\n\n".join(narrations)

    print(f"总旁白长度: {len(full_narration)} 字符")
    print(f"场景数量: {len(narrations)}")
    print("正在合成语音...")

    result = await tts.synthesize_chapter(
        narrations=narrations,
        voice_preset="zh_female_shuangkuai",
        speed_ratio=0.95
    )

    if result.get("success"):
        audio_path = f"{OUTPUT_DIR}/narration.mp3"
        with open(audio_path, "wb") as f:
            f.write(result["audio_data"])

        print(f"\n✅ 语音合成成功!")
        print(f"  音频文件: {audio_path}")
        print(f"  文件大小: {len(result['audio_data'])} bytes")

        return {
            "audio_path": audio_path,
            "audio_data": result["audio_data"],
            "narrations": narrations,
            "full_narration": full_narration
        }
    else:
        print(f"❌ 语音合成失败: {result.get('error')}")
        return None


async def step4_whisper_and_align(story: dict, tts_result: dict):
    """Step 4: Whisper时间戳和音画对齐"""
    print("\n" + "=" * 60)
    print("Step 4: Whisper时间戳 + 音画对齐")
    print("=" * 60)

    if not tts_result:
        print("没有音频数据，跳过")
        return None, None

    # Whisper
    whisper = WhisperService()
    audio_path = tts_result["audio_path"]

    print(f"音频文件: {audio_path}")
    print("正在分析时间戳...")

    whisper_result = await whisper.transcribe_with_timestamps(
        audio_path=audio_path,
        granularity="both"
    )

    if whisper_result.get("success"):
        print(f"✅ 时间戳分析完成!")
        print(f"  音频时长: {whisper_result.get('duration'):.2f} 秒")
        print(f"  段落数: {len(whisper_result.get('segments', []))}")

        with open(f"{OUTPUT_DIR}/whisper_timestamps.json", "w", encoding="utf-8") as f:
            json.dump(whisper_result, f, ensure_ascii=False, indent=2)
    else:
        print(f"❌ Whisper分析失败")
        return None, None

    # 对齐
    alignment = AlignmentService()
    scenes = story.get("scenes", [])
    segments = whisper_result.get("segments", [])
    duration = whisper_result.get("duration", 0)
    full_text = whisper_result.get("text", "")

    images = [
        {
            "scene_id": scene.get("scene_id"),
            "visual_description": scene.get("visual_description", "")
        }
        for scene in scenes
    ]

    print("\n正在进行音画对齐...")

    timeline = await alignment.align_images_to_audio(
        images=images,
        segments=segments,
        full_text=full_text,
        audio_duration=duration
    )

    if not timeline:
        timeline = await alignment.quick_align(
            scene_count=len(scenes),
            segments=segments,
            audio_duration=duration
        )

    print("✅ 对齐完成!")
    for item in timeline:
        print(f"  场景 {item['scene_id']}: {item['start_time']:.2f}s - {item['end_time']:.2f}s")

    with open(f"{OUTPUT_DIR}/timeline.json", "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)

    return whisper_result, timeline


async def main():
    """运行完整测试"""
    print("\n" + "=" * 60)
    print("序话Story - 角色一致性测试")
    print("=" * 60)
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 清理并创建输出目录
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Step 1: 生成故事
    story = await step1_generate_story_with_characters()

    # Step 2: 生成一致性图片
    image_results = await step2_generate_consistent_images(story)

    # Step 3: 生成TTS
    tts_result = await step3_generate_tts(story)

    # Step 4: Whisper + 对齐
    whisper_result, timeline = await step4_whisper_and_align(story, tts_result)

    # 汇总
    print("\n" + "=" * 60)
    print("测试完成汇总")
    print("=" * 60)

    results = {
        "故事生成（含角色描述）": "✅" if story and story.get("characters") else "❌",
        "一致性图片生成": "✅" if image_results else "❌",
        "TTS合成": "✅" if tts_result else "❌",
        "Whisper + 对齐": "✅" if timeline else "❌"
    }

    for step, status in results.items():
        print(f"  {step}: {status}")

    print(f"\n输出目录: {OUTPUT_DIR}")
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 列出生成的文件
    print("\n生成的文件:")
    for root, dirs, files in os.walk(OUTPUT_DIR):
        level = root.replace(OUTPUT_DIR, '').count(os.sep)
        indent = '  ' * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = '  ' * (level + 1)
        for file in files:
            filepath = os.path.join(root, file)
            size = os.path.getsize(filepath)
            print(f"{subindent}{file} ({size:,} bytes)")


if __name__ == "__main__":
    asyncio.run(main())
