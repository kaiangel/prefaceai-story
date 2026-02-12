"""TTS语音合成服务 - 使用火山引擎豆包语音合成大模型"""

import asyncio
import base64
import json
import time
from typing import Optional, List
from io import BytesIO

import aiohttp

from app.config import settings


class TTSService:
    """
    豆包语音合成服务

    使用火山引擎语音合成API（HTTP一次性合成）
    文档：https://www.volcengine.com/docs/6561/1257584

    关键特性：
    1. 多音色支持（男声/女声等）
    2. 语速/音量/音调调节
    3. 一次性合成，返回完整音频
    4. 自动重试机制
    """

    # API 端点
    API_ENDPOINT = "https://openspeech.bytedance.com/api/v1/tts"

    # 重试配置
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    # 预设音色列表
    VOICE_PRESETS = {
        # 中文女声
        "zh_female_shuangkuai": {
            "speaker": "zh_female_shuangkuaisisi_moon_bigtts",
            "name": "爽快思思",
            "language": "zh-CN",
            "gender": "female",
            "style": "活泼开朗，适合短视频旁白"
        },
        "zh_female_tianmei": {
            "speaker": "zh_female_tianmeixiaoyuan_moon_bigtts",
            "name": "甜美小源",
            "language": "zh-CN",
            "gender": "female",
            "style": "温柔甜美，适合温馨内容"
        },
        "zh_female_qingxin": {
            "speaker": "zh_female_qingxinxiaolu_moon_bigtts",
            "name": "清新小鹿",
            "language": "zh-CN",
            "gender": "female",
            "style": "清新自然"
        },
        # 中文男声
        "zh_male_wennuan": {
            "speaker": "zh_male_wennuanahu_moon_bigtts",
            "name": "温暖阿虎",
            "language": "zh-CN",
            "gender": "male",
            "style": "温暖磁性，适合故事讲述"
        },
        "zh_male_yangguang": {
            "speaker": "zh_male_yangguangqingshu_moon_bigtts",
            "name": "阳光青叔",
            "language": "zh-CN",
            "gender": "male",
            "style": "阳光开朗"
        },
        "zh_male_chenwen": {
            "speaker": "zh_male_chenwenshu_moon_bigtts",
            "name": "沉稳书生",
            "language": "zh-CN",
            "gender": "male",
            "style": "沉稳大气，适合正式内容"
        },
        # 英文
        "en_female": {
            "speaker": "en_female_amandabrown_moon_bigtts",
            "name": "Amanda Brown",
            "language": "en-US",
            "gender": "female",
            "style": "Professional English voice"
        },
        "en_male": {
            "speaker": "en_male_johntaylor_moon_bigtts",
            "name": "John Taylor",
            "language": "en-US",
            "gender": "male",
            "style": "Professional English voice"
        },
    }

    def __init__(self):
        self.app_id = settings.VOLCENGINE_APP_ID
        self.access_key = settings.VOLCENGINE_ACCESS_KEY
        self.resource_id = settings.VOLCENGINE_RESOURCE_ID
        self.default_voice = settings.VOLCENGINE_DEFAULT_VOICE
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """关闭 session"""
        if self._session and not self._session.closed:
            await self._session.close()

    def _get_speaker(self, voice_preset: str) -> str:
        """获取音色的 speaker 参数"""
        if voice_preset in self.VOICE_PRESETS:
            return self.VOICE_PRESETS[voice_preset]["speaker"]
        # 如果不在预设中，假设直接传入的是 speaker 值
        return voice_preset

    async def synthesize(
        self,
        text: str,
        voice_preset: str = None,
        speed_ratio: float = 1.0,
        volume_ratio: float = 1.0,
        pitch_ratio: float = 1.0,
        output_format: str = "mp3",
        sample_rate: int = 24000
    ) -> dict:
        """
        合成语音

        Args:
            text: 要合成的文本
            voice_preset: 音色预设代码或直接的speaker值
            speed_ratio: 语速比例 (0.5-2.0)
            volume_ratio: 音量比例 (0.5-2.0)
            pitch_ratio: 音调比例 (0.5-2.0)
            output_format: 输出格式 mp3/ogg_opus/pcm
            sample_rate: 采样率

        Returns:
            {
                "success": True,
                "audio_data": bytes,
                "audio_format": "mp3",
                "duration_seconds": 45.5,
                "sample_rate": 24000,
                "voice_used": "zh_female_shuangkuai",
                "text_length": 100
            }
        """
        if not self.app_id or not self.access_key:
            return {
                "success": False,
                "error": "火山引擎 TTS 未配置。请设置 VOLCENGINE_APP_ID 和 VOLCENGINE_ACCESS_KEY"
            }

        # 确定音色
        speaker = self._get_speaker(voice_preset or self.default_voice)

        # 构建请求（火山引擎 TTS HTTP API v1 格式）
        # 参考文档: https://www.volcengine.com/docs/6561/1257584
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer;{self.access_key}"
        }

        # 生成唯一请求ID
        import uuid
        reqid = str(uuid.uuid4())

        # 音频格式映射
        encoding_map = {
            "mp3": "mp3",
            "wav": "wav",
            "pcm": "pcm",
            "ogg_opus": "ogg_opus"
        }
        encoding = encoding_map.get(output_format, "mp3")

        payload = {
            "app": {
                "appid": self.app_id,
                "token": "access_token",  # 固定值
                "cluster": self.resource_id  # 使用resource_id作为cluster
            },
            "user": {
                "uid": "xuhua_story_user"
            },
            "audio": {
                "voice_type": speaker,
                "encoding": encoding,
                "speed_ratio": speed_ratio,
                "volume_ratio": volume_ratio,
                "pitch_ratio": pitch_ratio
            },
            "request": {
                "reqid": reqid,
                "text": text,
                "text_type": "plain",
                "operation": "query"
            }
        }

        start_time = time.time()
        last_error = None

        for attempt in range(self.MAX_RETRIES):
            try:
                session = await self._get_session()

                async with session.post(
                    self.API_ENDPOINT,
                    headers=headers,
                    json=payload,
                    ssl=False  # 禁用SSL验证以避免证书问题
                ) as response:
                    response_text = await response.text()

                    if response.status != 200:
                        last_error = f"API返回错误 {response.status}: {response_text}"
                        if attempt < self.MAX_RETRIES - 1:
                            await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                            continue
                        break

                    # 解析JSON响应
                    try:
                        data = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        last_error = f"JSON解析错误: {str(e)}"
                        if attempt < self.MAX_RETRIES - 1:
                            await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                            continue
                        break

                    # 检查响应状态码
                    code = data.get("code", -1)
                    if code != 3000:  # 3000 表示成功
                        last_error = f"TTS错误 (code={code}): {data.get('message', 'Unknown error')}"
                        if attempt < self.MAX_RETRIES - 1:
                            await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                            continue
                        break

                    # 提取音频数据（Base64编码）
                    audio_base64 = data.get("data")
                    if not audio_base64:
                        last_error = "响应中没有音频数据"
                        if attempt < self.MAX_RETRIES - 1:
                            await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                            continue
                        break

                    # 解码Base64音频
                    audio_data = base64.b64decode(audio_base64)
                    generation_time = time.time() - start_time

                    # 估算音频时长（基于文件大小和格式）
                    # MP3 大约 16kbps = 2KB/s
                    estimated_duration = len(audio_data) / 2000 if output_format == "mp3" else None

                    return {
                        "success": True,
                        "audio_data": audio_data,
                        "audio_format": output_format,
                        "duration_seconds": estimated_duration,
                        "sample_rate": sample_rate,
                        "voice_used": voice_preset or self.default_voice,
                        "text_length": len(text),
                        "generation_time_seconds": round(generation_time, 2)
                    }

            except aiohttp.ClientError as e:
                last_error = f"网络错误: {str(e)}"
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue

            except Exception as e:
                last_error = f"未知错误: {str(e)}"
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue

        return {
            "success": False,
            "error": f"TTS合成失败（重试{self.MAX_RETRIES}次后）: {last_error}",
            "voice_used": voice_preset or self.default_voice,
            "text_length": len(text),
            "generation_time_seconds": round(time.time() - start_time, 2)
        }

    async def synthesize_chapter(
        self,
        narrations: List[str],
        voice_preset: str = None,
        pause_duration_ms: int = 800,
        **kwargs
    ) -> dict:
        """
        合成整个章节的旁白

        将所有场景的narration拼接后合成

        Args:
            narrations: 各场景的旁白文本列表
            voice_preset: 音色预设
            pause_duration_ms: 段落之间的停顿时长（毫秒）

        Returns:
            {
                "success": True,
                "audio_data": bytes,
                "duration_seconds": 180.5,
                "full_text": "拼接后的完整文本",
                "segment_count": 5
            }
        """
        # 拼接所有旁白，添加适当的停顿
        full_text = self._join_narrations(narrations, pause_duration_ms)

        result = await self.synthesize(
            text=full_text,
            voice_preset=voice_preset,
            **kwargs
        )

        if result["success"]:
            result["full_text"] = full_text
            result["segment_count"] = len(narrations)

        return result

    def _join_narrations(
        self,
        narrations: List[str],
        pause_duration_ms: int = 800
    ) -> str:
        """
        拼接旁白文本

        在段落之间添加适当的停顿
        注意：火山引擎TTS支持一些标记，但具体支持情况需要测试
        这里使用多个换行来模拟停顿
        """
        # 清理每段旁白
        cleaned = []
        for narration in narrations:
            text = narration.strip()
            if text:
                # 确保以句号结尾
                if not text.endswith(('。', '！', '？', '.', '!', '?')):
                    text += '。'
                cleaned.append(text)

        # 用换行符分隔，TTS通常会在换行处有自然停顿
        return '\n\n'.join(cleaned)

    def get_available_voices(self, language: str = None) -> List[dict]:
        """
        获取可用音色列表

        Args:
            language: 过滤语言，如 "zh-CN", "en-US"

        Returns:
            音色信息列表
        """
        voices = []
        for key, info in self.VOICE_PRESETS.items():
            if language is None or info["language"] == language:
                voices.append({
                    "preset_code": key,
                    **info
                })
        return voices

    def get_voice_info(self, voice_preset: str) -> Optional[dict]:
        """获取指定音色的详细信息"""
        if voice_preset in self.VOICE_PRESETS:
            return {
                "preset_code": voice_preset,
                **self.VOICE_PRESETS[voice_preset]
            }
        return None
