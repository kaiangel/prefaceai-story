"""
迪士尼风格复杂故事生成测试

测试一个完整的迪士尼式故事结构：
1. Opening (开头铺垫) - 建立世界观，展示主角的平凡生活和内心渴望
2. Adventure (冒险试炼) - 主角踏上旅程，遇到挑战和盟友
3. Crisis (绝望时刻) - 最大的危机，一切似乎失去希望
4. Climax (高潮) - 主角找到力量，面对最终挑战
5. Resolution (重生结局) - 胜利、成长、回归

场景数量：13+个
场景风格随剧情变化
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
OUTPUT_DIR = "./test_output/manualtest/teststory3"


async def step1_generate_disney_story():
    """Step 1: 生成迪士尼式复杂故事"""
    print("\n" + "=" * 60)
    print("Step 1: 生成迪士尼式故事（含详细角色描述）")
    print("=" * 60)

    generator = StoryGenerator()

    # 迪士尼式故事主题 - 一只小鸟的冒险
    idea = """一只名叫小星的小麻雀，从小就梦想着飞越传说中的云海山脉，看看山那边的神秘世界。
村子里的老雀们都说那是不可能的，因为云海山脉终年被暴风雪包围。
有一天，小星决定出发了。
在旅途中，她遇到了一只受伤的老鹰（曾经飞越过云海山脉的传奇飞行家），
一只胆小但忠诚的田鼠朋友，还有一只狡猾的乌鸦反派。
经历了暴风雪、迷路、背叛、几乎放弃之后，
小星最终靠着友情的力量和自己的勇气，成功飞越了云海山脉，
看到了山那边壮丽的日出，也发现真正的宝藏是一路上收获的友谊。
故事要有：开头的渴望、冒险的艰难、绝望的黑暗时刻、重生的高潮、温暖的结局。
场景风格要随剧情变化：开头温暖、冒险紧张、绝望阴暗、重生金色光芒。"""

    style = "illustration"

    print(f"主题: 小星的云海冒险")
    print(f"风格: {style}")
    print("正在生成故事（包含详细角色描述，13+场景）...")
    print("预计需要较长时间，请耐心等待...")

    result = await generator.generate_story(
        idea=idea,
        style=style,
        chapter_number=1,
        total_chapters=1,
        duration_minutes=5,  # 5分钟，约1000字，13+场景
        character_count=5,   # 5个角色：小星、老鹰、田鼠、乌鸦、老雀
        language="zh-CN",
        min_scenes=13        # 强制要求最少13个场景
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
        print(f"    角色: {char.get('role', 'N/A')}")

    # 检查视觉风格
    visual_style = story.get("visual_style", {})
    if visual_style:
        print(f"\n  全局视觉风格:")
        print(f"    艺术风格: {visual_style.get('art_style', 'N/A')}")
        print(f"    渲染: {visual_style.get('rendering', 'N/A')}")

    # 检查场景
    scenes = story.get("scenes", [])
    print(f"\n  场景数量: {len(scenes)}")

    # 统计各阶段场景
    phases = {}
    for scene in scenes:
        phase = scene.get("story_phase", "unknown")
        phases[phase] = phases.get(phase, 0) + 1
        scene_style = scene.get("scene_style", {})
        print(f"    场景 {scene.get('scene_id')}: [{phase}] "
              f"色调={scene_style.get('color_palette', 'N/A')}, "
              f"氛围={scene_style.get('atmosphere', 'N/A')}")

    print(f"\n  故事阶段分布: {phases}")

    # 保存故事
    with open(f"{OUTPUT_DIR}/story.json", "w", encoding="utf-8") as f:
        json.dump(story, f, ensure_ascii=False, indent=2)

    # 保存详细故事文档
    story_doc = generate_story_document(story)
    with open(f"{OUTPUT_DIR}/story.md", "w", encoding="utf-8") as f:
        f.write(story_doc)

    print(f"\n故事文档已保存到: {OUTPUT_DIR}/story.md")

    return story


def generate_story_document(story: dict) -> str:
    """生成详细的故事文档"""
    visual_style = story.get("visual_style", {})
    characters = story.get("characters", [])
    scenes = story.get("scenes", [])

    doc = f"""# {story.get('title')}

## 故事简介
{story.get('synopsis', story.get('summary', 'N/A'))}

## 全局视觉风格
- 艺术风格: {visual_style.get('art_style', 'N/A')}
- 渲染风格: {visual_style.get('rendering', 'N/A')}
- 默认色调: {visual_style.get('color_palette', 'N/A')}
- 主要颜色: {', '.join(visual_style.get('primary_colors', []))}
- 默认光线: {visual_style.get('lighting', 'N/A')}
- 默认氛围: {visual_style.get('atmosphere', 'N/A')}
- 细节程度: {visual_style.get('detail_level', 'N/A')}

## 角色设定

"""
    for char in characters:
        doc += f"""### {char.get('name')} ({char.get('name_en', '')})
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
            doc += f"""**动物特征:**
- 物种: {a.get('species')} ({a.get('breed', 'N/A')})
- 毛色: {a.get('fur_color')}
- 图案: {a.get('fur_pattern')}
- 毛长: {a.get('fur_length')}
- 毛质: {a.get('fur_texture')}
- 体型: {a.get('body_size')} {a.get('body_shape', '')}
- 眼睛: {a.get('eye_color')} {a.get('eye_shape', '')}
- 特殊标记: {', '.join(a.get('distinctive_marks', []))}

"""
        elif char.get("physical"):
            p = char["physical"]
            doc += f"""**物理特征:**
- 身高: {p.get('height')}
- 体型: {p.get('build')}
- 肤色: {p.get('skin_tone')}
- 头发: {p.get('hair_color')} {p.get('hair_style', '')}
- 眼睛: {p.get('eye_color')} {p.get('eye_shape', '')}
- 特殊标记: {', '.join(p.get('distinctive_marks', []))}

"""

    doc += "## 场景详情\n\n"

    # 按故事阶段分组
    current_phase = None
    phase_names = {
        "opening": "第一幕：开头铺垫",
        "adventure": "第二幕：冒险试炼",
        "crisis": "第三幕：绝望时刻",
        "climax": "第四幕：高潮",
        "resolution": "第五幕：重生结局"
    }

    for scene in scenes:
        phase = scene.get("story_phase", "unknown")
        if phase != current_phase:
            current_phase = phase
            doc += f"\n### {phase_names.get(phase, phase)}\n\n"

        scene_style = scene.get("scene_style", {})
        doc += f"""#### 场景 {scene.get('scene_id')}
- **地点**: {scene.get('location')}
- **时间**: {scene.get('time')}
- **氛围**: {scene.get('mood')}
- **场景风格**:
  - 色调: {scene_style.get('color_palette', 'N/A')}
  - 光线: {scene_style.get('lighting', 'N/A')}
  - 氛围: {scene_style.get('atmosphere', 'N/A')}
  - 天气: {scene_style.get('weather', 'N/A')}
  - 时段: {scene_style.get('time_of_day', 'N/A')}
- **出场角色**: {', '.join(scene.get('characters_in_scene', []))}

**角色动作:**
"""
        for char_id, action in scene.get('character_actions', {}).items():
            doc += f"- {char_id}: {action}\n"

        doc += f"""
**画面描述:**
{scene.get('visual_description')}

**旁白:**
{scene.get('narration')}

---

"""

    return doc


async def step2_generate_consistent_images(story: dict):
    """Step 2: 使用一致性图片生成器生成场景图片"""
    print("\n" + "=" * 60)
    print("Step 2: 生成一致性场景图片（含场景风格变化）")
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

    print(f"\n开始生成 {len(scenes)} 个场景图片...")
    print("每个场景会根据story_phase使用不同的场景风格")

    for scene in scenes:
        scene_id = scene.get("scene_id", 0)
        phase = scene.get("story_phase", "unknown")
        scene_style = scene.get("scene_style", {})

        print(f"\n生成场景 {scene_id}/{len(scenes)} [{phase}]...")
        print(f"  色调: {scene_style.get('color_palette', 'default')}")
        print(f"  氛围: {scene_style.get('atmosphere', 'default')}")

        # 预览prompt
        preview = generator.get_prompt_preview(scene)

        # 保存prompt预览
        with open(f"{images_dir}/scene_{scene_id:02d}_prompt.txt", "w", encoding="utf-8") as f:
            f.write(f"Story Phase: {phase}\n")
            f.write(f"Scene Style: {json.dumps(scene_style, ensure_ascii=False)}\n\n")
            f.write(preview)

        # 生成图片
        result = await generator.generate_scene_image(scene)

        if result.get("success") and result.get("image_data"):
            image_path = f"{images_dir}/scene_{scene_id:02d}.png"
            image_data = result["image_data"]
            if isinstance(image_data, str):
                import base64
                image_data = base64.b64decode(image_data)
            with open(image_path, "wb") as f:
                f.write(image_data)

            print(f"  ✅ 已保存: scene_{scene_id:02d}.png")
            print(f"     角色: {result.get('characters_included', [])}")

            image_results.append({
                "scene_id": scene_id,
                "story_phase": phase,
                "image_path": image_path,
                "success": True,
                "characters": result.get("characters_included", []),
                "scene_style": scene_style
            })
        else:
            print(f"  ❌ 生成失败: {result.get('error')}")
            image_results.append({
                "scene_id": scene_id,
                "story_phase": phase,
                "success": False,
                "error": result.get("error")
            })

        # 避免API速率限制
        await asyncio.sleep(3)

    # 保存图片生成日志
    with open(f"{OUTPUT_DIR}/images_log.json", "w", encoding="utf-8") as f:
        json.dump(image_results, f, ensure_ascii=False, indent=2)

    # 统计成功率
    success_count = sum(1 for r in image_results if r.get("success"))
    print(f"\n图片生成完成: {success_count}/{len(scenes)} 成功")

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
        print(f"  文件大小: {len(result['audio_data']):,} bytes")

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
        print(f"❌ Whisper分析失败: {whisper_result.get('error')}")
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
            "visual_description": scene.get("visual_description", ""),
            "story_phase": scene.get("story_phase", "")
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

    # 生成带阶段信息的时间线
    phase_names = {
        "opening": "开头铺垫",
        "adventure": "冒险试炼",
        "crisis": "绝望时刻",
        "climax": "高潮",
        "resolution": "重生结局"
    }

    for i, item in enumerate(timeline):
        scene = scenes[i] if i < len(scenes) else {}
        phase = scene.get("story_phase", "unknown")
        item["story_phase"] = phase
        item["phase_name"] = phase_names.get(phase, phase)
        print(f"  场景 {item['scene_id']} [{item['phase_name']}]: "
              f"{item['start_time']:.2f}s - {item['end_time']:.2f}s")

    with open(f"{OUTPUT_DIR}/timeline.json", "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)

    # 生成对齐报告
    generate_alignment_report(story, timeline, whisper_result)

    return whisper_result, timeline


def generate_alignment_report(story: dict, timeline: list, whisper_result: dict):
    """生成音画对齐报告"""
    scenes = story.get("scenes", [])

    report = f"""# 音画对齐报告

## 基本信息
- 场景数: {len(scenes)}
- 音频时长: {whisper_result.get('duration', 0):.2f} 秒
- 对齐方法: LLM智能对齐

## 故事阶段时间分布

| 阶段 | 场景数 | 开始时间 | 结束时间 | 总时长 |
|------|--------|----------|----------|--------|
"""

    # 统计各阶段
    phases = {}
    for item in timeline:
        phase = item.get("story_phase", "unknown")
        if phase not in phases:
            phases[phase] = {
                "count": 0,
                "start": item["start_time"],
                "end": item["end_time"]
            }
        phases[phase]["count"] += 1
        phases[phase]["end"] = item["end_time"]

    phase_order = ["opening", "adventure", "crisis", "climax", "resolution"]
    phase_names = {
        "opening": "开头铺垫",
        "adventure": "冒险试炼",
        "crisis": "绝望时刻",
        "climax": "高潮",
        "resolution": "重生结局"
    }

    for phase in phase_order:
        if phase in phases:
            p = phases[phase]
            duration = p["end"] - p["start"]
            report += f"| {phase_names.get(phase, phase)} | {p['count']} | {p['start']:.2f}s | {p['end']:.2f}s | {duration:.2f}s |\n"

    report += "\n## 详细时间轴\n\n"
    report += "| 场景 | 阶段 | 开始时间 | 结束时间 | 时长 | 旁白摘要 |\n"
    report += "|------|------|----------|----------|------|----------|\n"

    for i, item in enumerate(timeline):
        scene = scenes[i] if i < len(scenes) else {}
        narration = scene.get("narration", "")[:30] + "..."
        duration = item["end_time"] - item["start_time"]
        report += f"| {item['scene_id']} | {item.get('phase_name', 'N/A')} | {item['start_time']:.2f}s | {item['end_time']:.2f}s | {duration:.2f}s | {narration} |\n"

    report += "\n## 详细场景信息\n\n"

    current_phase = None
    for i, item in enumerate(timeline):
        scene = scenes[i] if i < len(scenes) else {}
        phase = item.get("story_phase", "unknown")

        if phase != current_phase:
            current_phase = phase
            report += f"\n### {item.get('phase_name', phase)}\n\n"

        scene_style = scene.get("scene_style", {})
        report += f"""#### 场景 {item['scene_id']}
- **时间范围**: {item['start_time']:.2f}s - {item['end_time']:.2f}s
- **时长**: {item['end_time'] - item['start_time']:.2f}s
- **场景风格**: {scene_style.get('color_palette', 'N/A')} / {scene_style.get('atmosphere', 'N/A')}
- **旁白**: {scene.get('narration', 'N/A')}
- **画面**: {scene.get('visual_description', 'N/A')[:100]}...

"""

    with open(f"{OUTPUT_DIR}/alignment.md", "w", encoding="utf-8") as f:
        f.write(report)


async def main():
    """运行完整迪士尼故事测试"""
    print("\n" + "=" * 60)
    print("序话Story - 迪士尼风格复杂故事测试")
    print("=" * 60)
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 清理并创建输出目录
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Step 1: 生成故事
    story = await step1_generate_disney_story()

    if not story:
        print("\n故事生成失败，测试终止")
        return

    scenes_count = len(story.get("scenes", []))
    if scenes_count < 13:
        print(f"\n⚠️ 警告：生成的场景数量({scenes_count})少于预期(13+)")
        print("继续执行后续步骤...")

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

    characters_count = len(story.get("characters", []))
    scenes_count = len(story.get("scenes", []))
    successful_images = sum(1 for r in (image_results or []) if r.get("success"))

    results = {
        "故事生成（迪士尼结构）": f"✅ {characters_count}角色, {scenes_count}场景",
        "一致性图片生成": f"✅ {successful_images}/{scenes_count}" if image_results else "❌",
        "TTS合成": "✅" if tts_result else "❌",
        "Whisper + 对齐": "✅" if timeline else "❌"
    }

    for step, status in results.items():
        print(f"  {step}: {status}")

    print(f"\n输出目录: {OUTPUT_DIR}")
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 列出生成的文件
    print("\n生成的文件:")
    total_size = 0
    for root, dirs, files in os.walk(OUTPUT_DIR):
        level = root.replace(OUTPUT_DIR, '').count(os.sep)
        indent = '  ' * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = '  ' * (level + 1)
        for file in sorted(files):
            filepath = os.path.join(root, file)
            size = os.path.getsize(filepath)
            total_size += size
            print(f"{subindent}{file} ({size:,} bytes)")

    print(f"\n总文件大小: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")


if __name__ == "__main__":
    asyncio.run(main())
