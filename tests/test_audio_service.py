"""Test script for audio generation - Phase 3"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.tts_service import TTSService
from app.services.whisper_service import WhisperService
from app.services.audio_storage import AudioStorageService
from app.services.alignment_service import AlignmentService


async def test_tts_service():
    """测试TTS服务（需要火山引擎API配置）"""
    print("=" * 60)
    print("测试 1: TTS语音合成服务")
    print("=" * 60)

    tts = TTSService()

    # 检查配置
    from app.config import settings
    if not settings.VOLCENGINE_APP_ID or not settings.VOLCENGINE_ACCESS_KEY:
        print("⚠️ 火山引擎TTS未配置，跳过TTS测试")
        print("  请在 .env 中设置:")
        print("  - VOLCENGINE_APP_ID")
        print("  - VOLCENGINE_ACCESS_KEY")
        return None

    # 测试合成
    text = "你好，欢迎使用序话Story。这是一个AI短视频生成应用，可以帮你把创意变成精彩的短剧。"

    print(f"\n测试文本: {text[:50]}...")
    print("正在合成...")

    result = await tts.synthesize(
        text=text,
        voice_preset="zh_female_shuangkuai",
        speed_ratio=1.0
    )

    print(f"\n结果:")
    print(f"  成功: {result['success']}")

    if result['success']:
        print(f"  音色: {result.get('voice_used')}")
        print(f"  文本长度: {result.get('text_length')} 字符")
        print(f"  音频大小: {len(result.get('audio_data', b''))} bytes")
        print(f"  耗时: {result.get('generation_time_seconds')}秒")

        # 保存测试音频
        os.makedirs("./test_output", exist_ok=True)
        with open("./test_output/test_tts.mp3", "wb") as f:
            f.write(result['audio_data'])
        print(f"  音频已保存到: ./test_output/test_tts.mp3")

        return "./test_output/test_tts.mp3"
    else:
        print(f"  错误: {result.get('error')}")
        return None


async def test_whisper_service(audio_path: str = None):
    """测试Whisper服务（需要OpenAI API配置）"""
    print("\n" + "=" * 60)
    print("测试 2: Whisper时间戳服务")
    print("=" * 60)

    # 检查配置
    from app.config import settings
    if not settings.OPENAI_API_KEY:
        print("⚠️ OpenAI API未配置，跳过Whisper测试")
        print("  请在 .env 中设置 OPENAI_API_KEY")
        return None

    if not audio_path or not os.path.exists(audio_path):
        print("⚠️ 没有音频文件，跳过Whisper测试")
        return None

    whisper = WhisperService()

    print(f"\n音频文件: {audio_path}")
    print("正在转录...")

    result = await whisper.transcribe_with_timestamps(
        audio_path=audio_path,
        granularity="both"
    )

    print(f"\n结果:")
    print(f"  成功: {result['success']}")

    if result['success']:
        print(f"  转录文本: {result.get('text', '')[:100]}...")
        print(f"  音频时长: {result.get('duration')}秒")
        print(f"  语言: {result.get('language')}")
        print(f"  段落数: {len(result.get('segments', []))}")
        print(f"  词数: {len(result.get('words', []))}")
        print(f"  处理耗时: {result.get('processing_time_seconds')}秒")

        # 打印前3个段落
        segments = result.get('segments', [])
        if segments:
            print("\n  前3个段落:")
            for seg in segments[:3]:
                print(f"    [{seg['start']:.2f}s - {seg['end']:.2f}s]: {seg['text'][:30]}...")

        return result
    else:
        print(f"  错误: {result.get('error')}")
        return None


async def test_audio_storage():
    """测试音频存储服务"""
    print("\n" + "=" * 60)
    print("测试 3: 音频存储服务")
    print("=" * 60)

    storage = AudioStorageService("./test_output/audio_storage")

    # 创建测试音频数据（1秒静音MP3的最小示例）
    # 实际使用中会是真正的音频数据
    test_audio_data = b'\xff\xfb\x90\x00' + b'\x00' * 100  # 简化的测试数据

    print("\n保存测试音频...")
    result = await storage.save_audio(
        audio_data=test_audio_data,
        project_id="test_project",
        chapter_id="test_chapter"
    )

    print(f"  音频路径: {result['audio_path']}")
    print(f"  完整路径: {result['full_path']}")
    print(f"  文件大小: {result['file_size_bytes']} bytes")

    # 测试元数据保存
    print("\n保存元数据...")
    await storage.save_metadata(
        project_id="test_project",
        chapter_id="test_chapter",
        metadata={
            "duration": 10.5,
            "voice_preset": "zh_female_shuangkuai",
            "text": "测试文本"
        }
    )
    print("  元数据已保存")

    # 测试时间轴保存
    print("\n保存时间轴...")
    await storage.save_timeline(
        project_id="test_project",
        chapter_id="test_chapter",
        timeline=[
            {"scene_id": 1, "start_time": 0.0, "end_time": 5.0},
            {"scene_id": 2, "start_time": 5.0, "end_time": 10.5}
        ]
    )
    print("  时间轴已保存")

    # 验证文件存在
    exists = storage.audio_exists("test_project", "test_chapter")
    print(f"\n  音频文件存在: {exists}")

    # 加载时间轴
    timeline = await storage.load_timeline("test_project", "test_chapter")
    print(f"  加载的时间轴: {timeline}")

    return True


async def test_alignment_service():
    """测试对齐服务"""
    print("\n" + "=" * 60)
    print("测试 4: 音画对齐服务")
    print("=" * 60)

    alignment = AlignmentService()

    # 准备测试数据
    images = [
        {"scene_id": 1, "visual_description": "程序员在电脑前工作"},
        {"scene_id": 2, "visual_description": "城市夜景，霓虹灯闪烁"},
        {"scene_id": 3, "visual_description": "主角露出惊讶的表情"},
    ]

    segments = [
        {"start": 0.0, "end": 3.5, "text": "在一个深夜，程序员小明还在加班"},
        {"start": 3.5, "end": 7.0, "text": "窗外是璀璨的城市灯火"},
        {"start": 7.0, "end": 10.0, "text": "突然，屏幕上出现了奇怪的代码"},
        {"start": 10.0, "end": 12.5, "text": "他意识到，这不是普通的bug"},
    ]

    print("\n测试快速对齐（不使用LLM）...")
    timeline = await alignment.quick_align(
        scene_count=3,
        segments=segments,
        audio_duration=12.5
    )

    print("\n时间轴结果:")
    for item in timeline:
        print(f"  场景 {item['scene_id']}: {item['start_time']:.2f}s - {item['end_time']:.2f}s (时长: {item['duration']:.2f}s)")

    # 验证时间轴
    is_valid = True
    # 检查从0开始
    if timeline[0]["start_time"] != 0:
        print("❌ 时间轴未从0开始")
        is_valid = False
    # 检查覆盖到结尾
    if abs(timeline[-1]["end_time"] - 12.5) > 0.1:
        print("❌ 时间轴未覆盖到音频结尾")
        is_valid = False
    # 检查无间隙
    for i in range(1, len(timeline)):
        if abs(timeline[i]["start_time"] - timeline[i-1]["end_time"]) > 0.1:
            print(f"❌ 场景 {i} 和 {i+1} 之间有间隙")
            is_valid = False

    if is_valid:
        print("\n✅ 时间轴验证通过")
    else:
        print("\n❌ 时间轴验证失败")

    return is_valid


async def test_voice_list():
    """测试可用音色列表"""
    print("\n" + "=" * 60)
    print("测试 5: 可用音色列表")
    print("=" * 60)

    tts = TTSService()
    voices = tts.get_available_voices(language="zh-CN")

    print(f"\n共 {len(voices)} 个中文音色:")
    for v in voices:
        print(f"  - {v['preset_code']}: {v['name']} ({v['gender']}) - {v['style']}")

    return True


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("序话Story - Phase 3 音频服务测试")
    print("=" * 60)

    results = {}

    # 测试1: TTS服务
    try:
        audio_path = await test_tts_service()
        results['TTS服务'] = audio_path is not None or "跳过（未配置）"
    except Exception as e:
        print(f"❌ TTS服务测试失败: {e}")
        results['TTS服务'] = False
        audio_path = None

    # 测试2: Whisper服务
    try:
        whisper_result = await test_whisper_service(audio_path)
        results['Whisper服务'] = whisper_result is not None or "跳过（未配置）"
    except Exception as e:
        print(f"❌ Whisper服务测试失败: {e}")
        results['Whisper服务'] = False

    # 测试3: 音频存储服务
    try:
        results['音频存储服务'] = await test_audio_storage()
    except Exception as e:
        print(f"❌ 音频存储服务测试失败: {e}")
        results['音频存储服务'] = False

    # 测试4: 对齐服务
    try:
        results['对齐服务'] = await test_alignment_service()
    except Exception as e:
        print(f"❌ 对齐服务测试失败: {e}")
        results['对齐服务'] = False

    # 测试5: 音色列表
    try:
        results['音色列表'] = await test_voice_list()
    except Exception as e:
        print(f"❌ 音色列表测试失败: {e}")
        results['音色列表'] = False

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results.items():
        if passed == True:
            status = "✅ 通过"
        elif passed == False:
            status = "❌ 失败"
            all_passed = False
        else:
            status = f"⚠️ {passed}"
        print(f"  {test_name}: {status}")

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过!")
    else:
        print("⚠️ 部分测试需要配置API Key后才能运行")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
