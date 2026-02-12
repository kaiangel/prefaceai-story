"""
完整微故事生成测试 - Phase 1-3 端到端测试

生成一个完整的微故事，包含：
1. 故事内容、旁白文档
2. 场景图片（使用Gemini）
3. TTS语音合成音频
4. Whisper时间戳
5. 音画对齐时间轴
6. 完整元数据
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.story_generator import StoryGenerator
from app.services.image_generator import ImageGenerator
from app.services.tts_service import TTSService
from app.services.whisper_service import WhisperService
from app.services.alignment_service import AlignmentService
from app.services.audio_storage import AudioStorageService


# 输出目录
OUTPUT_DIR = "./test_output/manualtest/teststory1"


async def step1_generate_story():
    """Step 1: 生成故事内容"""
    print("\n" + "=" * 60)
    print("Step 1: 生成故事内容")
    print("=" * 60)

    generator = StoryGenerator()

    # 故事主题
    idea = "一只小猫咪在城市里迷路后，遇到了一只善良的流浪狗，最终找到回家的路"
    style = "温馨治愈"

    print(f"主题: {idea}")
    print(f"风格: {style}")
    print("正在生成故事...")

    # 使用StoryGenerator生成故事
    result = await generator.generate_story(
        idea=idea,
        style=style,
        chapter_number=1,
        total_chapters=1,
        duration_minutes=1,  # 1分钟短视频
        character_count=2,
        language="zh-CN"
    )

    if not result.get("success"):
        print(f"生成失败: {result.get('error')}")
        return None

    # 获取解析后的故事数据 - 返回的是 "data" 字段
    story = result.get("data")
    if not story:
        print("无法获取故事数据")
        print(f"返回结果: {result}")
        return None

    print(f"\n✅ 故事生成成功!")
    print(f"  使用模型: {result.get('provider')}/{result.get('model_used')}")
    print(f"  故事标题: {story.get('title')}")
    print(f"  故事简介: {story.get('synopsis')}")
    print(f"  场景数量: {len(story.get('scenes', []))}")

    # 保存故事文档
    story_doc = f"""# {story.get('title')}

## 故事简介
{story.get('synopsis')}

## 场景详情

"""
    for scene in story.get('scenes', []):
        story_doc += f"""### 场景 {scene['scene_id']}

**旁白：**
{scene['narration']}

**画面描述：**
{scene['visual_description']}

---

"""

    with open(f"{OUTPUT_DIR}/story.md", "w", encoding="utf-8") as f:
        f.write(story_doc)

    # 保存原始JSON
    with open(f"{OUTPUT_DIR}/story.json", "w", encoding="utf-8") as f:
        json.dump(story, f, ensure_ascii=False, indent=2)

    print(f"故事文档已保存到: {OUTPUT_DIR}/story.md")

    return story


async def step2_generate_images(story: dict):
    """Step 2: 生成场景图片"""
    print("\n" + "=" * 60)
    print("Step 2: 生成场景图片")
    print("=" * 60)

    if not story:
        print("没有故事数据，跳过图片生成")
        return None

    image_generator = ImageGenerator()
    scenes = story.get('scenes', [])

    # 创建图片目录
    images_dir = f"{OUTPUT_DIR}/images"
    os.makedirs(images_dir, exist_ok=True)

    image_results = []

    for scene in scenes:
        scene_id = scene['scene_id']
        visual_desc = scene['visual_description']

        print(f"\n生成场景 {scene_id} 图片...")
        print(f"  描述: {visual_desc[:80]}...")

        # 增强提示词
        enhanced_prompt = f"""A heartwarming illustration for a short story video.

Scene description: {visual_desc}

Style requirements:
- Warm, soft lighting with gentle colors
- Cute, appealing character design
- Cinematic composition suitable for video
- High quality, detailed illustration
- Emotional and touching atmosphere
- 16:9 aspect ratio for video format
"""

        result = await image_generator.generate_image(
            prompt=enhanced_prompt,
            aspect_ratio="16:9"
        )

        if result.get("success") and result.get("image_data"):
            # 保存图片 - image_data 是 bytes
            image_path = f"{images_dir}/scene_{scene_id}.png"
            image_data = result["image_data"]
            # 如果是 base64 字符串，需要解码
            if isinstance(image_data, str):
                import base64
                image_data = base64.b64decode(image_data)
            with open(image_path, "wb") as f:
                f.write(image_data)

            print(f"  ✅ 已保存: {image_path}")

            image_results.append({
                "scene_id": scene_id,
                "image_path": image_path,
                "prompt": enhanced_prompt[:200] + "...",
                "success": True
            })
        else:
            print(f"  ❌ 生成失败: {result.get('error')}")
            image_results.append({
                "scene_id": scene_id,
                "success": False,
                "error": result.get('error')
            })

        # 避免API速率限制
        await asyncio.sleep(2)

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
    scenes = story.get('scenes', [])

    # 提取所有旁白
    narrations = [scene['narration'] for scene in scenes]
    full_narration = "\n\n".join(narrations)

    print(f"总旁白长度: {len(full_narration)} 字符")
    print(f"场景数量: {len(narrations)}")
    print("正在合成语音...")

    # 合成完整音频
    result = await tts.synthesize_chapter(
        narrations=narrations,
        voice_preset="zh_female_shuangkuai",  # 爽快思思
        speed_ratio=0.95  # 稍微慢一点，更清晰
    )

    if result.get("success"):
        # 保存音频
        audio_path = f"{OUTPUT_DIR}/narration.mp3"
        with open(audio_path, "wb") as f:
            f.write(result["audio_data"])

        print(f"\n✅ 语音合成成功!")
        print(f"  音频文件: {audio_path}")
        print(f"  文件大小: {len(result['audio_data'])} bytes")
        print(f"  预估时长: {result.get('duration_seconds', 'N/A')} 秒")
        print(f"  合成耗时: {result.get('generation_time_seconds')} 秒")

        # 保存旁白文档
        narration_doc = f"""# 旁白文稿

## 基本信息
- 音色: 爽快思思 (zh_female_shuangkuai)
- 语速: 0.95x
- 总字数: {len(full_narration)} 字符
- 场景数: {len(narrations)}

## 完整旁白

"""
        for i, narration in enumerate(narrations, 1):
            narration_doc += f"""### 场景 {i}
{narration}

"""

        with open(f"{OUTPUT_DIR}/narration.md", "w", encoding="utf-8") as f:
            f.write(narration_doc)

        return {
            "audio_path": audio_path,
            "audio_data": result["audio_data"],
            "narrations": narrations,
            "full_narration": full_narration
        }
    else:
        print(f"❌ 语音合成失败: {result.get('error')}")
        return None


async def step4_whisper_timestamps(tts_result: dict):
    """Step 4: 获取Whisper时间戳"""
    print("\n" + "=" * 60)
    print("Step 4: Whisper时间戳分析")
    print("=" * 60)

    if not tts_result:
        print("没有音频数据，跳过Whisper分析")
        return None

    whisper = WhisperService()
    audio_path = tts_result["audio_path"]

    print(f"音频文件: {audio_path}")
    print("正在分析时间戳（这可能需要1-2分钟）...")

    result = await whisper.transcribe_with_timestamps(
        audio_path=audio_path,
        granularity="both"
    )

    if result.get("success"):
        print(f"\n✅ 时间戳分析完成!")
        print(f"  音频时长: {result.get('duration'):.2f} 秒")
        print(f"  识别语言: {result.get('language')}")
        print(f"  段落数: {len(result.get('segments', []))}")
        print(f"  词数: {len(result.get('words', []))}")
        print(f"  处理耗时: {result.get('processing_time_seconds'):.2f} 秒")

        # 保存时间戳文档
        timestamp_doc = f"""# Whisper时间戳分析报告

## 基本信息
- 音频时长: {result.get('duration'):.2f} 秒
- 识别语言: {result.get('language')}
- 段落数: {len(result.get('segments', []))}
- 词数: {len(result.get('words', []))}
- 处理耗时: {result.get('processing_time_seconds'):.2f} 秒

## 转录文本
{result.get('text', '')}

## 段落级时间戳

| 段落 | 开始时间 | 结束时间 | 文本 |
|------|----------|----------|------|
"""
        for i, seg in enumerate(result.get('segments', []), 1):
            text = seg.get('text', '').replace('|', '\\|')[:50]
            timestamp_doc += f"| {i} | {seg['start']:.2f}s | {seg['end']:.2f}s | {text}... |\n"

        timestamp_doc += """

## 词级时间戳（前20个词）

| 词 | 开始时间 | 结束时间 |
|----|----------|----------|
"""
        for word in result.get('words', [])[:20]:
            w = word.get('word', '').replace('|', '\\|')
            timestamp_doc += f"| {w} | {word['start']:.2f}s | {word['end']:.2f}s |\n"

        if len(result.get('words', [])) > 20:
            timestamp_doc += f"\n... 共 {len(result.get('words', []))} 个词\n"

        with open(f"{OUTPUT_DIR}/whisper_timestamps.md", "w", encoding="utf-8") as f:
            f.write(timestamp_doc)

        # 保存原始JSON
        with open(f"{OUTPUT_DIR}/whisper_timestamps.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"  时间戳文档: {OUTPUT_DIR}/whisper_timestamps.md")

        return result
    else:
        print(f"❌ Whisper分析失败: {result.get('error')}")
        return None


async def step5_alignment(story: dict, whisper_result: dict, tts_result: dict = None):
    """Step 5: 音画对齐"""
    print("\n" + "=" * 60)
    print("Step 5: 音画对齐")
    print("=" * 60)

    if not story or not whisper_result:
        print("缺少必要数据，跳过对齐")
        return None

    alignment = AlignmentService()
    scenes = story.get('scenes', [])
    segments = whisper_result.get('segments', [])
    duration = whisper_result.get('duration', 0)
    full_text = whisper_result.get('text', '') or (tts_result.get('full_narration', '') if tts_result else '')

    print(f"场景数: {len(scenes)}")
    print(f"音频段落数: {len(segments)}")
    print(f"音频时长: {duration:.2f} 秒")

    # 准备图片数据
    images = [
        {
            "scene_id": scene['scene_id'],
            "visual_description": scene['visual_description']
        }
        for scene in scenes
    ]

    print("\n正在进行智能对齐...")

    # 尝试使用LLM对齐
    timeline = await alignment.align_images_to_audio(
        images=images,
        segments=segments,
        full_text=full_text,
        audio_duration=duration
    )

    if not timeline:
        print("LLM对齐失败，使用快速对齐...")
        timeline = await alignment.quick_align(
            scene_count=len(scenes),
            segments=segments,
            audio_duration=duration
        )

    print("\n✅ 对齐完成!")
    print("\n时间轴:")
    for item in timeline:
        print(f"  场景 {item['scene_id']}: {item['start_time']:.2f}s - {item['end_time']:.2f}s (时长: {item['duration']:.2f}s)")

    # 保存对齐文档
    alignment_doc = f"""# 音画对齐报告

## 基本信息
- 场景数: {len(scenes)}
- 音频时长: {duration:.2f} 秒
- 对齐方法: {"LLM智能对齐" if len(timeline) == len(scenes) else "快速对齐"}

## 时间轴

| 场景 | 开始时间 | 结束时间 | 时长 | 旁白摘要 |
|------|----------|----------|------|----------|
"""
    for item in timeline:
        scene_id = item['scene_id']
        narration = scenes[scene_id - 1]['narration'][:30] + "..." if scene_id <= len(scenes) else ""
        alignment_doc += f"| {scene_id} | {item['start_time']:.2f}s | {item['end_time']:.2f}s | {item['duration']:.2f}s | {narration} |\n"

    alignment_doc += """

## 详细场景信息

"""
    for item in timeline:
        scene_id = item['scene_id']
        if scene_id <= len(scenes):
            scene = scenes[scene_id - 1]
            alignment_doc += f"""### 场景 {scene_id}
- **时间范围**: {item['start_time']:.2f}s - {item['end_time']:.2f}s
- **时长**: {item['duration']:.2f}s
- **旁白**: {scene['narration']}
- **画面**: {scene['visual_description'][:100]}...

"""

    with open(f"{OUTPUT_DIR}/alignment.md", "w", encoding="utf-8") as f:
        f.write(alignment_doc)

    # 保存JSON
    with open(f"{OUTPUT_DIR}/timeline.json", "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)

    print(f"  对齐文档: {OUTPUT_DIR}/alignment.md")

    return timeline


async def step6_save_metadata(story: dict, tts_result: dict, whisper_result: dict, timeline: list):
    """Step 6: 保存完整元数据"""
    print("\n" + "=" * 60)
    print("Step 6: 保存元数据")
    print("=" * 60)

    metadata = {
        "project_info": {
            "name": "teststory1",
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0",
            "phases_completed": ["phase1_story", "phase2_images", "phase3_audio"]
        },
        "story": {
            "title": story.get('title') if story else None,
            "synopsis": story.get('synopsis') if story else None,
            "scene_count": len(story.get('scenes', [])) if story else 0
        },
        "audio": {
            "file": "narration.mp3",
            "duration_seconds": whisper_result.get('duration') if whisper_result else None,
            "voice_preset": "zh_female_shuangkuai",
            "language": whisper_result.get('language') if whisper_result else None
        },
        "timeline": timeline,
        "files": {
            "story_doc": "story.md",
            "story_json": "story.json",
            "narration_doc": "narration.md",
            "narration_audio": "narration.mp3",
            "whisper_timestamps": "whisper_timestamps.json",
            "alignment_doc": "alignment.md",
            "timeline_json": "timeline.json",
            "images_dir": "images/"
        }
    }

    with open(f"{OUTPUT_DIR}/metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"✅ 元数据已保存: {OUTPUT_DIR}/metadata.json")

    # 创建README
    readme = f"""# 微故事测试项目: {story.get('title', 'teststory1') if story else 'teststory1'}

## 项目概述
这是一个完整的微故事生成测试，包含Phase 1-3的所有产出物。

## 文件说明

### 故事内容 (Phase 1)
- `story.md` - 故事文档（Markdown格式）
- `story.json` - 故事原始数据（JSON格式）
- `narration.md` - 旁白文稿

### 场景图片 (Phase 2)
- `images/` - 场景图片目录
  - `scene_1.png` - 场景1图片
  - `scene_2.png` - 场景2图片
  - ...
- `images_log.json` - 图片生成日志

### 音频与对齐 (Phase 3)
- `narration.mp3` - 语音合成音频
- `whisper_timestamps.md` - Whisper时间戳分析报告
- `whisper_timestamps.json` - Whisper原始数据
- `alignment.md` - 音画对齐报告
- `timeline.json` - 时间轴数据

### 元数据
- `metadata.json` - 项目完整元数据

## 生成时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 使用的服务
- **故事生成**: Google Gemini 2.5 Flash
- **图片生成**: Google Gemini 2.5 Flash Image
- **语音合成**: 火山引擎豆包TTS (爽快思思)
- **时间戳**: OpenAI Whisper
- **对齐算法**: Gemini 2.5 Flash + 快速对齐
"""

    with open(f"{OUTPUT_DIR}/README.md", "w", encoding="utf-8") as f:
        f.write(readme)

    print(f"✅ README已保存: {OUTPUT_DIR}/README.md")

    return metadata


async def main():
    """运行完整测试"""
    print("\n" + "=" * 60)
    print("序话Story - 完整微故事生成测试")
    print("=" * 60)
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Step 1: 生成故事
    story = await step1_generate_story()

    # Step 2: 生成图片
    image_results = await step2_generate_images(story)

    # Step 3: 生成TTS音频
    tts_result = await step3_generate_tts(story)

    # Step 4: Whisper时间戳
    whisper_result = await step4_whisper_timestamps(tts_result)

    # Step 5: 音画对齐
    timeline = await step5_alignment(story, whisper_result, tts_result)

    # Step 6: 保存元数据
    metadata = await step6_save_metadata(story, tts_result, whisper_result, timeline)

    # 汇总
    print("\n" + "=" * 60)
    print("测试完成汇总")
    print("=" * 60)

    results = {
        "故事生成": "✅" if story else "❌",
        "图片生成": "✅" if image_results else "❌",
        "TTS合成": "✅" if tts_result else "❌",
        "Whisper时间戳": "✅" if whisper_result else "❌",
        "音画对齐": "✅" if timeline else "❌",
        "元数据保存": "✅" if metadata else "❌"
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
