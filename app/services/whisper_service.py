"""Whisper时间戳提取服务 - 使用OpenAI Whisper API"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List
import time

from openai import OpenAI

from app.config import settings


class WhisperService:
    """
    OpenAI Whisper 时间戳提取服务

    文档：https://platform.openai.com/docs/guides/speech-to-text

    关键功能：
    1. 音频转文字
    2. Word级时间戳（精确到每个词）
    3. Segment级时间戳（句子/段落级别）

    注意：
    - Whisper API 是同步的，需要用线程池包装实现异步
    - 需要 response_format="verbose_json" 才能获取时间戳
    - timestamp_granularities 参数控制返回的时间戳级别
    """

    def __init__(self):
        api_key = settings.OPENAI_API_KEY
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
            print("Warning: OPENAI_API_KEY not set, Whisper service will fail")

        self._executor = ThreadPoolExecutor(max_workers=2)

    def _transcribe_sync(
        self,
        audio_path: str,
        granularities: List[str]
    ) -> dict:
        """
        同步转录音频（在线程池中运行）

        Args:
            audio_path: 音频文件路径
            granularities: 时间戳粒度列表 ["word", "segment"]

        Returns:
            转录结果字典
        """
        if not self.client:
            return {
                "success": False,
                "error": "OpenAI client not initialized. Check OPENAI_API_KEY."
            }

        try:
            start_time = time.time()

            with open(audio_path, "rb") as audio_file:
                # 调用 Whisper API
                transcript = self.client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-1",
                    response_format="verbose_json",
                    timestamp_granularities=granularities
                )

            processing_time = time.time() - start_time

            # 注意：transcript 是 Pydantic 对象，用点号访问属性
            result = {
                "success": True,
                "text": transcript.text,
                "duration": getattr(transcript, 'duration', None),
                "language": getattr(transcript, 'language', None),
                "processing_time_seconds": round(processing_time, 2)
            }

            # 提取 segments
            if hasattr(transcript, 'segments') and transcript.segments:
                result["segments"] = [
                    {
                        "id": seg.id if hasattr(seg, 'id') else i,
                        "start": seg.start,
                        "end": seg.end,
                        "text": seg.text.strip() if hasattr(seg, 'text') else ""
                    }
                    for i, seg in enumerate(transcript.segments)
                ]
            else:
                result["segments"] = []

            # 提取 words
            if hasattr(transcript, 'words') and transcript.words:
                result["words"] = [
                    {
                        "word": word.word,
                        "start": word.start,
                        "end": word.end
                    }
                    for word in transcript.words
                ]
            else:
                result["words"] = []

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Whisper transcription failed: {str(e)}"
            }

    async def transcribe_with_timestamps(
        self,
        audio_path: str,
        granularity: str = "both"
    ) -> dict:
        """
        异步转录音频并获取时间戳

        Args:
            audio_path: 音频文件路径
            granularity: 时间戳粒度 "word", "segment", 或 "both"

        Returns:
            {
                "success": True,
                "text": "完整转录文本",
                "duration": 180.5,
                "language": "zh",
                "segments": [
                    {
                        "id": 0,
                        "start": 0.0,
                        "end": 5.2,
                        "text": "第一段文字..."
                    }
                ],
                "words": [
                    {
                        "word": "你好",
                        "start": 0.0,
                        "end": 0.5
                    }
                ],
                "processing_time_seconds": 5.2
            }
        """
        # 确定要请求的粒度
        if granularity == "both":
            granularities = ["word", "segment"]
        elif granularity in ["word", "segment"]:
            granularities = [granularity]
        else:
            granularities = ["segment"]  # 默认只获取 segment

        # 在线程池中运行同步方法
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self._executor,
            self._transcribe_sync,
            audio_path,
            granularities
        )

        return result

    def get_segment_boundaries(self, segments: List[dict]) -> List[dict]:
        """
        提取segment边界信息

        用于后续与图片匹配

        Args:
            segments: Whisper返回的segments列表

        Returns:
            [
                {
                    "index": 0,
                    "start": 0.0,
                    "end": 5.2,
                    "text": "第一段文字",
                    "duration": 5.2
                }
            ]
        """
        boundaries = []
        for i, seg in enumerate(segments):
            boundaries.append({
                "index": seg.get('id', i),
                "start": seg['start'],
                "end": seg['end'],
                "text": seg.get('text', '').strip(),
                "duration": round(seg['end'] - seg['start'], 3)
            })
        return boundaries

    def merge_short_segments(
        self,
        segments: List[dict],
        min_duration: float = 2.0
    ) -> List[dict]:
        """
        合并过短的segment

        有时Whisper会生成很短的segment，这可能导致图片切换过于频繁
        此方法将过短的segment与相邻的合并

        Args:
            segments: segment列表
            min_duration: 最小时长（秒）

        Returns:
            合并后的segment列表
        """
        if not segments:
            return []

        merged = []
        current = None

        for seg in segments:
            if current is None:
                current = seg.copy()
            else:
                # 如果当前累积的时长仍然很短，继续合并
                current_duration = current['end'] - current['start']
                if current_duration < min_duration:
                    # 合并
                    current['end'] = seg['end']
                    current['text'] = current['text'] + ' ' + seg['text']
                else:
                    # 保存当前，开始新的
                    merged.append(current)
                    current = seg.copy()

        # 添加最后一个
        if current:
            merged.append(current)

        # 更新 duration
        for seg in merged:
            seg['duration'] = round(seg['end'] - seg['start'], 3)

        return merged

    def split_by_scene_count(
        self,
        segments: List[dict],
        scene_count: int,
        total_duration: float
    ) -> List[dict]:
        """
        根据场景数量重新划分时间段

        当segments数量与场景数量不匹配时，尝试均匀划分

        Args:
            segments: 原始segment列表
            scene_count: 场景数量
            total_duration: 音频总时长

        Returns:
            重新划分的时间段列表
        """
        if not segments or scene_count <= 0:
            return segments

        # 如果segment数量等于或接近场景数量，直接返回
        if len(segments) == scene_count:
            return segments

        # 均匀划分时间
        time_per_scene = total_duration / scene_count
        result = []

        for i in range(scene_count):
            start = i * time_per_scene
            end = (i + 1) * time_per_scene if i < scene_count - 1 else total_duration

            # 收集该时间段内的文本
            texts = []
            for seg in segments:
                seg_mid = (seg['start'] + seg['end']) / 2
                if start <= seg_mid < end:
                    texts.append(seg['text'])

            result.append({
                "index": i,
                "start": round(start, 3),
                "end": round(end, 3),
                "text": ' '.join(texts),
                "duration": round(end - start, 3)
            })

        return result

    async def close(self):
        """关闭资源"""
        self._executor.shutdown(wait=False)
