"""
Shot拆分优化测试 - teststory3-1

基于teststory3的故事，但使用新的shot拆分功能
- 音频时长缩短到3分钟（节省API成本）
- 测试shot拆分效果
- 对比shot数量和时间轴分布

目标：
- 3分钟视频 → 约18-30个shot
- 每个shot对应6-15秒音频
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
from app.services.storyboard_service import StoryboardService
from app.services.consistent_image_generator import ConsistentImageGenerator, create_generator_from_story
from app.services.tts_service import TTSService
from app.services.whisper_service import WhisperService
from app.services.alignment_service import AlignmentService
from app.config import settings


# 输出目录
OUTPUT_DIR = "./test_output/manualtest/teststory3-1"


async def step1_generate_story():
    """Step 1: 生成3分钟故事"""
    print("\n" + "=" * 60)
    print("Step 1: 生成3分钟迪士尼式故事")
    print("=" * 60)

    generator = StoryGenerator()

    # 简化版的小星冒险故事（3分钟）
    idea = """一只名叫小星的小麻雀梦想飞越云海山脉。
老雀们说那是不可能的，因为山脉终年被暴风雪包围。
小星出发了，遇到了一只受伤的老鹰和一只忠诚的田鼠朋友。
经历暴风雪和几乎放弃后，小星靠着友情和勇气飞越了云海山脉。
故事结构：开头渴望 → 冒险艰难 → 绝望黑暗 → 重生高潮 → 温暖结局。
场景风格随剧情变化。"""

    style = "illustration"

    print(f"主题: 小星的云海冒险（精简版）")
    print(f"风格: {style}")
    print(f"目标时长: 3分钟（约600字）")
    print("正在生成故事...")

    result = await generator.generate_story(
        idea=idea,
        style=style,
        chapter_number=1,
        total_chapters=1,
        duration_minutes=3,  # 3分钟
        character_count=3,   # 3个角色：小星、老鹰、田鼠
        language="zh-CN",
        min_scenes=6         # 最少6个场景
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

    characters = story.get("characters", [])
    scenes = story.get("scenes", [])
    print(f"  角色数量: {len(characters)}")
    print(f"  场景数量: {len(scenes)}")

    # 统计各场景的narration长度
    print("\n  场景narration长度分析:")
    total_chars = 0
    for scene in scenes:
        narration = scene.get("narration", "")
        length = len(narration)
        total_chars += length
        need_split = "需拆分" if length > settings.SHOT_MAX_NARRATION_LENGTH else "无需拆分"
        print(f"    场景 {scene.get('scene_id')}: {length}字 ({need_split})")

    print(f"  总字数: {total_chars}")
    print(f"  预计时长: {total_chars / settings.TTS_CHARS_PER_SECOND:.1f}秒")

    # 保存故事
    with open(f"{OUTPUT_DIR}/story.json", "w", encoding="utf-8") as f:
        json.dump(story, f, ensure_ascii=False, indent=2)

    return story


async def step2_split_to_shots(story: dict):
    """Step 2: 使用StoryboardService拆分场景为shots"""
    print("\n" + "=" * 60)
    print("Step 2: 场景拆分为Shots")
    print("=" * 60)

    if not story:
        print("没有故事数据，跳过")
        return None

    storyboard_service = StoryboardService()

    scenes = story.get("scenes", [])
    characters = story.get("characters", [])
    style_preset = story.get("visual_style", {}).get("art_style", "illustration")

    print(f"配置参数:")
    print(f"  MAX_NARRATION_LENGTH: {storyboard_service.MAX_NARRATION_LENGTH}")
    print(f"  TARGET_SHOT_LENGTH: {storyboard_service.TARGET_SHOT_LENGTH}")
    print(f"  TTS_CHARS_PER_SECOND: {storyboard_service.TTS_CHARS_PER_SECOND}")

    print(f"\n原始场景数: {len(scenes)}")
    print("正在进行shot拆分...")

    # 使用新的拆分方法
    shots = await storyboard_service.generate_storyboard_with_splitting(
        scenes=scenes,
        characters=characters,
        style_preset=style_preset,
        aspect_ratio="16:9"
    )

    print(f"\n✅ 拆分完成!")
    print(f"  原始场景数: {len(scenes)}")
    print(f"  拆分后shot数: {len(shots)}")
    print(f"  拆分比例: {len(shots)/len(scenes):.2f}x")

    # 详细信息
    print("\n  Shot详情:")
    for shot in shots:
        narration = shot.get("narration_segment", "")
        duration = shot.get("duration_hint", 0)
        print(f"    Shot {shot.get('shot_id')} (原场景{shot.get('original_scene_id')}): "
              f"{len(narration)}字, {duration:.1f}秒, {shot.get('shot_type', 'N/A')}")

    # 验证narration完整性
    original_text = "".join(scene.get("narration", "") for scene in scenes)
    shot_text = "".join(shot.get("narration_segment", "") for shot in shots)

    print(f"\n  文本完整性验证:")
    print(f"    原始总字数: {len(original_text)}")
    print(f"    拆分后总字数: {len(shot_text)}")
    print(f"    匹配: {'✅' if len(original_text) == len(shot_text) else '❌'}")

    # 保存shots
    with open(f"{OUTPUT_DIR}/shots.json", "w", encoding="utf-8") as f:
        json.dump(shots, f, ensure_ascii=False, indent=2)

    return shots


async def step3_generate_tts(story: dict):
    """Step 3: 生成TTS语音"""
    print("\n" + "=" * 60)
    print("Step 3: 生成TTS语音")
    print("=" * 60)

    if not story:
        print("没有故事数据，跳过TTS生成")
        return None

    tts = TTSService()
    scenes = story.get("scenes", [])

    narrations = [scene.get("narration", "") for scene in scenes]
    full_narration = "\n\n".join(narrations)

    print(f"总旁白长度: {len(full_narration)} 字符")
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


async def step4_align_shots(story: dict, shots: list, tts_result: dict):
    """Step 4: Shot与音频对齐"""
    print("\n" + "=" * 60)
    print("Step 4: Shot与音频对齐")
    print("=" * 60)

    if not tts_result or not shots:
        print("缺少必要数据，跳过")
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

    if not whisper_result.get("success"):
        print(f"❌ Whisper分析失败: {whisper_result.get('error')}")
        return None, None

    print(f"✅ 时间戳分析完成!")
    print(f"  音频时长: {whisper_result.get('duration'):.2f} 秒")
    print(f"  段落数: {len(whisper_result.get('segments', []))}")

    with open(f"{OUTPUT_DIR}/whisper_timestamps.json", "w", encoding="utf-8") as f:
        json.dump(whisper_result, f, ensure_ascii=False, indent=2)

    # 使用新的shot对齐方法
    alignment = AlignmentService()
    segments = whisper_result.get("segments", [])
    duration = whisper_result.get("duration", 0)
    full_text = tts_result["full_narration"]

    print("\n正在进行shot-音频对齐...")

    timeline = await alignment.align_shots_to_audio(
        shots=shots,
        segments=segments,
        full_text=full_text,
        audio_duration=duration
    )

    print("✅ 对齐完成!")

    # 输出时间轴信息
    print("\n  时间轴分布:")
    for item in timeline:
        print(f"    Shot {item['shot_id']} (场景{item['original_scene_id']}): "
              f"{item['start_time']:.2f}s - {item['end_time']:.2f}s "
              f"({item['duration']:.2f}s)")

    with open(f"{OUTPUT_DIR}/timeline.json", "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)

    # 生成对齐报告
    generate_report(story, shots, timeline, whisper_result)

    return whisper_result, timeline


def generate_report(story: dict, shots: list, timeline: list, whisper_result: dict):
    """生成详细报告"""
    scenes = story.get("scenes", [])
    duration = whisper_result.get("duration", 0)

    report = f"""# Shot拆分优化测试报告 - teststory3-1

## 基本信息
- 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 音频时长: {duration:.2f} 秒 ({duration/60:.1f} 分钟)
- 原始场景数: {len(scenes)}
- 拆分后shot数: {len(shots)}
- 拆分比例: {len(shots)/len(scenes):.2f}x

## 配置参数
- MAX_NARRATION_LENGTH: {settings.SHOT_MAX_NARRATION_LENGTH}
- TARGET_SHOT_LENGTH: {settings.SHOT_TARGET_LENGTH}
- TTS_CHARS_PER_SECOND: {settings.TTS_CHARS_PER_SECOND}

## 目标验证
- 目标shot数: 18-30个 (3分钟视频)
- 实际shot数: {len(shots)} {'✅ 达标' if 18 <= len(shots) <= 30 else '❌ 未达标'}
- 平均shot时长: {duration/len(shots):.2f}秒
- 目标时长: 6-15秒/shot {'✅' if 6 <= duration/len(shots) <= 15 else '❌'}

## Shot时长分布

| Shot ID | 原场景 | 时长(秒) | narration字数 | 类型 | 状态 |
|---------|--------|----------|---------------|------|------|
"""

    for item in timeline:
        shot_id = item.get("shot_id")
        shot = shots[shot_id - 1] if shot_id <= len(shots) else {}
        narration_len = len(item.get("narration_segment", ""))
        shot_type = shot.get("shot_type", "N/A")
        dur = item.get("duration", 0)
        status = "✅" if 6 <= dur <= 15 else "⚠️"

        report += f"| {shot_id} | {item.get('original_scene_id')} | {dur:.2f} | {narration_len} | {shot_type} | {status} |\n"

    # 时长统计
    durations = [item.get("duration", 0) for item in timeline]
    min_dur = min(durations) if durations else 0
    max_dur = max(durations) if durations else 0
    avg_dur = sum(durations) / len(durations) if durations else 0

    report += f"""
## 时长统计
- 最短: {min_dur:.2f}秒
- 最长: {max_dur:.2f}秒
- 平均: {avg_dur:.2f}秒
- 标准差: {(sum((d - avg_dur)**2 for d in durations) / len(durations))**0.5:.2f}秒

## 与teststory3对比

| 指标 | teststory3 | teststory3-1 | 改进 |
|------|------------|--------------|------|
| 音频时长 | ~480秒 | {duration:.0f}秒 | 缩短 |
| 场景/shot数 | 13 | {len(shots)} | +{len(shots)-13} |
| 平均时长 | 37秒 | {avg_dur:.1f}秒 | -{37-avg_dur:.1f}秒 |
| 目标达成 | ❌ | {'✅' if 6 <= avg_dur <= 15 else '❌'} | {'改进' if avg_dur < 37 else '未改进'} |

## 完整时间轴

"""

    current_phase = None
    for item in timeline:
        phase = item.get("story_phase", "unknown")
        if phase != current_phase:
            current_phase = phase
            report += f"\n### {phase}\n\n"

        report += f"""#### Shot {item['shot_id']} (原场景 {item['original_scene_id']})
- 时间: {item['start_time']:.2f}s - {item['end_time']:.2f}s ({item['duration']:.2f}s)
- 类型: {shots[item['shot_id']-1].get('shot_type', 'N/A') if item['shot_id'] <= len(shots) else 'N/A'}
- 旁白: {item.get('narration_segment', '')[:50]}...

"""

    with open(f"{OUTPUT_DIR}/report.md", "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n报告已保存: {OUTPUT_DIR}/report.md")


async def step5_generate_images(story: dict, shots: list, timeline: list):
    """Step 5: 可选 - 生成图片（默认跳过以节省成本）"""
    print("\n" + "=" * 60)
    print("Step 5: 图片生成（可选）")
    print("=" * 60)

    # 询问是否要生成图片
    print(f"共有 {len(shots)} 个shot需要生成图片")
    print("为节省API成本，默认跳过图片生成")
    print("如需生成，请修改代码中的 GENERATE_IMAGES = True")

    GENERATE_IMAGES = True  # 改为True以生成图片

    if not GENERATE_IMAGES:
        print("跳过图片生成")
        return None

    generator = create_generator_from_story(story)
    images_dir = f"{OUTPUT_DIR}/images"
    os.makedirs(images_dir, exist_ok=True)

    image_results = []
    for shot in shots:
        shot_id = shot.get("shot_id")
        print(f"\n生成Shot {shot_id}/{len(shots)}...")

        # 构建一个scene-like对象用于图片生成
        scene_like = {
            "scene_id": shot_id,
            "visual_description": shot.get("visual_description", ""),
            "location": "",
            "time": "",
            "mood": "",
            "scene_style": shot.get("scene_style", {}),
            "story_phase": shot.get("story_phase", "")
        }

        result = await generator.generate_scene_image(scene_like)

        if result.get("success") and result.get("image_data"):
            image_path = f"{images_dir}/shot_{shot_id:02d}.png"
            image_data = result["image_data"]
            if isinstance(image_data, str):
                import base64
                image_data = base64.b64decode(image_data)
            with open(image_path, "wb") as f:
                f.write(image_data)
            print(f"  ✅ 已保存: shot_{shot_id:02d}.png")
            image_results.append({"shot_id": shot_id, "success": True, "path": image_path})
        else:
            print(f"  ❌ 失败: {result.get('error')}")
            image_results.append({"shot_id": shot_id, "success": False})

        await asyncio.sleep(3)

    return image_results


async def main():
    """运行Shot拆分测试"""
    print("\n" + "=" * 60)
    print("序话Story - Shot拆分优化测试 (teststory3-1)")
    print("=" * 60)
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 清理并创建输出目录
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Step 1: 生成故事
    story = await step1_generate_story()
    if not story:
        print("\n故事生成失败，测试终止")
        return

    # Step 2: 拆分为shots
    shots = await step2_split_to_shots(story)
    if not shots:
        print("\nShot拆分失败，测试终止")
        return

    # Step 3: 生成TTS
    tts_result = await step3_generate_tts(story)

    # Step 4: Shot对齐
    whisper_result, timeline = await step4_align_shots(story, shots, tts_result)

    # Step 5: 图片生成
    image_results = await step5_generate_images(story, shots, timeline)

    # 汇总
    print("\n" + "=" * 60)
    print("测试完成汇总")
    print("=" * 60)

    scenes_count = len(story.get("scenes", []))
    shots_count = len(shots) if shots else 0
    audio_duration = whisper_result.get("duration", 0) if whisper_result else 0

    print(f"  原始场景数: {scenes_count}")
    print(f"  拆分后shot数: {shots_count}")
    print(f"  拆分比例: {shots_count/scenes_count:.2f}x")
    print(f"  音频时长: {audio_duration:.2f}秒")
    print(f"  平均shot时长: {audio_duration/shots_count:.2f}秒" if shots_count > 0 else "")

    target_met = 6 <= (audio_duration/shots_count if shots_count > 0 else 0) <= 15
    print(f"\n  目标达成: {'✅' if target_met else '❌'} (6-15秒/shot)")

    print(f"\n输出目录: {OUTPUT_DIR}")
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 列出生成的文件
    print("\n生成的文件:")
    for file in sorted(os.listdir(OUTPUT_DIR)):
        filepath = os.path.join(OUTPUT_DIR, file)
        size = os.path.getsize(filepath)
        print(f"  {file} ({size:,} bytes)")


if __name__ == "__main__":
    asyncio.run(main())
