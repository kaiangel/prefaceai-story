# 序话Story - Phase 3 开发指令：音频合成与音画对齐

## 阶段目标

在Phase 2"故事 → 分镜图像"的基础上，实现"旁白音频合成 + 音画精确对齐"。

**核心交付**：
1. TTS音频合成：调用豆包语音合成大模型，将旁白文本转为音频
2. 时间戳提取：调用OpenAI Whisper获取word/segment级时间戳
3. 图文匹配：调用Gemini 2.5 Flash智能匹配图片与音频段落
4. 时间轴生成：输出精确的 `timeline_mapping[{image, start, end}]`

**核心指标**：
- 音画对齐误差 ≤ 80ms（人眼无法察觉的同步阈值）

---

## ⚠️ 重要提醒：API文档查阅

**在编写任何API调用代码之前，必须先搜索并阅读最新的官方文档：**

### 1. 豆包语音合成（火山引擎TTS）

**官方文档**：https://www.volcengine.com/docs/6561/1257584?lang=zh

```
搜索关键词：
- "火山引擎 语音合成 API"
- "豆包 TTS API documentation"
- "volcengine speech synthesis"
- site:volcengine.com 语音合成
```

**必读文档**：
- https://www.volcengine.com/docs/6561/1257584 （大模型语音合成）
- https://www.volcengine.com/docs/6561/79823 （音色列表）
- https://www.volcengine.com/docs/6561/1221057 （API鉴权）

**关键确认点**：
1. API endpoint 和请求格式
2. 鉴权方式（Access Key / Secret Key）
3. 可用音色列表及其voice_type参数
4. 音频输出格式（mp3/wav/pcm）
5. 情感/语速/音量控制参数
6. 流式 vs 非流式 API的选择
7. Python SDK 或 HTTP 调用方式

### 2. OpenAI Whisper API

**官方文档**：https://platform.openai.com/docs/guides/speech-to-text

```
搜索关键词：
- "OpenAI Whisper API timestamp"
- "whisper-1 word level timestamps"
- site:platform.openai.com whisper
```

**关键确认点**：
1. `response_format="verbose_json"` 获取详细时间戳
2. `timestamp_granularities=["word", "segment"]` 参数
3. 返回的数据结构（注意是Pydantic对象，用点号访问）
4. 支持的音频格式和大小限制

**参考代码**（项目中已有）：
```python
# 参考 whisper_timestamp_test.py
transcript = client.audio.transcriptions.create(
    file=audio_file,
    model="whisper-1",
    response_format="verbose_json",
    timestamp_granularities=["word", "segment"]
)
# 注意：返回的是Pydantic对象，用 result.text, result.segments, result.words 访问
```

### 3. Gemini 2.5 Flash（图文匹配）

**官方文档**：https://ai.google.dev/gemini-api/docs

```
搜索关键词：
- "Gemini 2.5 Flash API"
- "Gemini multimodal image text"
- site:ai.google.dev gemini flash
```

**关键确认点**：
1. 当前可用的模型ID（`gemini-2.5-flash` 或类似）
2. 多模态输入格式（同时传入图片和文本）
3. 图片压缩/base64编码要求
4. `detail: "low"` 参数降低token消耗

---

## API Key 配置

在 `.env` 文件中添加以下配置：

```env
# ===== 已有配置 (Phase 1 & 2) =====
GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
DATABASE_URL=sqlite+aiosqlite:///./xuhua_story.db
IMAGE_STORAGE_PATH=./storage/images

# ===== Phase 3 新增 =====
# OpenAI Whisper API
OPENAI_API_KEY=your_openai_api_key

# 火山引擎（豆包TTS）
# 获取方式：https://console.volcengine.com/iam/keymanage/
VOLCENGINE_ACCESS_KEY=your_volcengine_access_key
VOLCENGINE_SECRET_KEY=your_volcengine_secret_key
# 可选：指定默认音色
VOLCENGINE_DEFAULT_VOICE=zh_female_tianmeixiaoyuan_moon_bigtts

# 音频存储配置
AUDIO_STORAGE_PATH=./storage/audio
```

**提醒**：
- 火山引擎需要先开通"语音技术"服务
- 首次使用需要在控制台创建应用并获取AppID
- Whisper API按音频时长计费，注意用量

---

## 技术架构

### 新增模块

```
app/
├── services/
│   ├── story_generator.py      # Phase 1
│   ├── image_generator.py      # Phase 2
│   ├── image_storage.py        # Phase 2
│   ├── storyboard_service.py   # Phase 2
│   ├── tts_service.py          # 🆕 TTS语音合成
│   ├── whisper_service.py      # 🆕 Whisper时间戳提取
│   ├── alignment_service.py    # 🆕 图文匹配+时间轴对齐
│   └── audio_storage.py        # 🆕 音频存储
├── api/
│   └── chapters.py             # 📝 扩展音频相关端点
├── prompts/
│   └── alignment_prompts.py    # 🆕 图文匹配prompt模板
└── models/
    └── chapter.py              # 📝 扩展音频字段
```

### 数据库扩展

更新 `chapters` 表，添加音频相关字段：

```sql
-- 在 chapters 表中添加以下字段（如果尚未存在）
ALTER TABLE chapters ADD COLUMN audio_url TEXT;
ALTER TABLE chapters ADD COLUMN audio_path TEXT;
ALTER TABLE chapters ADD COLUMN audio_duration_seconds REAL;
ALTER TABLE chapters ADD COLUMN transcript_json TEXT;      -- Whisper返回的完整转录
ALTER TABLE chapters ADD COLUMN timeline_json TEXT;        -- 音画对齐结果
ALTER TABLE chapters ADD COLUMN voice_preset TEXT;         -- 使用的音色
```

新增 `audio_segments` 表（可选，用于更精细的时间轴管理）：

```sql
CREATE TABLE audio_segments (
    id TEXT PRIMARY KEY,
    chapter_id TEXT NOT NULL,
    segment_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    duration REAL NOT NULL,
    matched_scene_id INTEGER,           -- 匹配的场景ID
    matched_image_path TEXT,            -- 匹配的图片路径
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
);

CREATE INDEX idx_audio_segments_chapter ON audio_segments(chapter_id);
```

---

## 模块实现详述

### 模块1：TTS语音合成服务 (tts_service.py)

**⚠️ 编码前必做**：阅读火山引擎TTS官方文档 https://www.volcengine.com/docs/6561/1257584

```python
class TTSService:
    """
    豆包语音合成服务
    
    使用火山引擎大模型语音合成API
    文档：https://www.volcengine.com/docs/6561/1257584
    
    关键特性：
    1. 多音色支持（男声/女声/童声等）
    2. 情感控制（开心/悲伤/激动等）
    3. 语速/音量调节
    4. 流式/非流式合成
    """
    
    # 预设音色列表（从火山引擎文档获取最新列表）
    VOICE_PRESETS = {
        # 中文女声
        "zh_female_tianmei": {
            "voice_type": "zh_female_tianmeixiaoyuan_moon_bigtts",
            "name": "甜美小源",
            "language": "zh-CN",
            "gender": "female",
            "style": "温柔甜美"
        },
        "zh_female_shuangkuai": {
            "voice_type": "zh_female_shuangkuaisisi_moon_bigtts",
            "name": "爽快思思",
            "language": "zh-CN",
            "gender": "female",
            "style": "活泼开朗"
        },
        # 中文男声
        "zh_male_wennuanahu": {
            "voice_type": "zh_male_wennuanahu_moon_bigtts",
            "name": "温暖阿虎",
            "language": "zh-CN",
            "gender": "male",
            "style": "温暖磁性"
        },
        # TODO: 从文档补充更多音色
    }
    
    def __init__(self):
        self.access_key = settings.VOLCENGINE_ACCESS_KEY
        self.secret_key = settings.VOLCENGINE_SECRET_KEY
        # TODO: 根据文档初始化客户端
    
    async def synthesize(
        self,
        text: str,
        voice_preset: str = "zh_female_tianmei",
        speed_ratio: float = 1.0,      # 语速 0.5-2.0
        volume_ratio: float = 1.0,     # 音量 0.5-2.0
        pitch_ratio: float = 1.0,      # 音调 0.5-2.0
        emotion: str = None,           # 情感：happy/sad/angry等
        output_format: str = "mp3"
    ) -> dict:
        """
        合成语音
        
        Args:
            text: 要合成的文本
            voice_preset: 音色预设代码
            speed_ratio: 语速比例
            volume_ratio: 音量比例
            pitch_ratio: 音调比例
            emotion: 情感类型（可选）
            output_format: 输出格式 mp3/wav/pcm
        
        Returns:
            {
                "success": True,
                "audio_data": bytes,        # 音频二进制数据
                "audio_format": "mp3",
                "duration_seconds": 45.5,   # 音频时长
                "sample_rate": 24000,
                "voice_used": "zh_female_tianmei"
            }
        
        ⚠️ 实现时注意：
        1. 确认API endpoint（查阅最新文档）
        2. 实现正确的鉴权签名（火山引擎使用AK/SK签名）
        3. 处理长文本分段合成（如果有长度限制）
        4. 错误处理和重试机制
        """
        # TODO: 根据火山引擎文档实现
        pass
    
    async def synthesize_chapter(
        self,
        narrations: list[str],
        voice_preset: str,
        **kwargs
    ) -> dict:
        """
        合成整个章节的旁白
        
        将所有场景的narration拼接后合成
        
        Args:
            narrations: 各场景的旁白文本列表
            voice_preset: 音色预设
        
        Returns:
            {
                "success": True,
                "audio_data": bytes,
                "duration_seconds": 180.5,
                "full_text": "拼接后的完整文本"
            }
        """
        # 拼接所有旁白，添加适当的停顿标记
        full_text = self._join_narrations(narrations)
        return await self.synthesize(full_text, voice_preset, **kwargs)
    
    def _join_narrations(self, narrations: list[str]) -> str:
        """
        拼接旁白文本
        
        在段落之间添加适当的停顿标记
        火山引擎支持SSML标记，可以用 <break time="500ms"/> 控制停顿
        """
        # TODO: 根据文档确认SSML支持情况
        return "\n\n".join(narrations)
    
    def get_available_voices(self, language: str = "zh-CN") -> list[dict]:
        """获取可用音色列表"""
        return [
            v for v in self.VOICE_PRESETS.values() 
            if v["language"] == language
        ]
```

### 模块2：Whisper时间戳服务 (whisper_service.py)

**参考项目中已有的 `whisper_timestamp_test.py`**

```python
from openai import OpenAI

class WhisperService:
    """
    OpenAI Whisper 时间戳提取服务
    
    文档：https://platform.openai.com/docs/guides/speech-to-text
    
    关键功能：
    1. 音频转文字
    2. Word级时间戳（精确到每个词）
    3. Segment级时间戳（句子/段落级别）
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def transcribe_with_timestamps(
        self,
        audio_path: str,
        granularity: str = "both"  # "word", "segment", or "both"
    ) -> dict:
        """
        转录音频并获取时间戳
        
        Args:
            audio_path: 音频文件路径
            granularity: 时间戳粒度
        
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
                ]
            }
        
        ⚠️ 注意：
        1. Whisper返回的是Pydantic对象，用点号访问属性
        2. 需要 response_format="verbose_json" 才能获取时间戳
        3. timestamp_granularities 参数控制返回的时间戳级别
        """
        if granularity == "both":
            granularities = ["word", "segment"]
        else:
            granularities = [granularity]
        
        with open(audio_path, "rb") as audio_file:
            # ⚠️ 这是同步API，如果需要异步，使用线程池
            transcript = self.client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                response_format="verbose_json",
                timestamp_granularities=granularities
            )
        
        # 注意：transcript 是 Pydantic 对象，用点号访问
        return {
            "success": True,
            "text": transcript.text,
            "duration": transcript.duration,
            "language": getattr(transcript, 'language', None),
            "segments": transcript.segments if hasattr(transcript, 'segments') else [],
            "words": transcript.words if hasattr(transcript, 'words') else []
        }
    
    def get_segment_boundaries(self, segments: list) -> list[dict]:
        """
        提取segment边界信息
        
        用于后续与图片匹配
        """
        boundaries = []
        for seg in segments:
            boundaries.append({
                "index": seg.get('id', len(boundaries)),
                "start": seg['start'],
                "end": seg['end'],
                "text": seg['text'].strip(),
                "duration": seg['end'] - seg['start']
            })
        return boundaries
```

### 模块3：图文匹配+时间轴对齐服务 (alignment_service.py)

**核心模块**：使用Gemini 2.5 Flash智能匹配图片与音频段落

```python
import google.generativeai as genai
from PIL import Image
import base64
import json

class AlignmentService:
    """
    音画对齐服务
    
    核心逻辑：
    1. 接收Whisper的时间戳数据和所有场景图片
    2. 调用Gemini 2.5 Flash分析图片内容与文本语义
    3. 智能匹配每张图片应该对应哪个时间段
    4. 输出精确的时间轴映射
    
    对齐误差目标：≤ 80ms
    """
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # 使用2.5 Flash，成本低速度快
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    async def align_images_to_audio(
        self,
        images: list[dict],           # [{"scene_id": 1, "path": "...", "visual_description": "..."}]
        segments: list[dict],         # Whisper返回的segments
        full_text: str,               # 完整旁白文本
        audio_duration: float         # 音频总时长
    ) -> list[dict]:
        """
        将图片与音频时间段对齐
        
        Args:
            images: 场景图片列表，包含路径和描述
            segments: Whisper返回的时间戳段落
            full_text: 完整的旁白文本
            audio_duration: 音频总时长（秒）
        
        Returns:
            [
                {
                    "scene_id": 1,
                    "image_path": "path/to/image.png",
                    "start_time": 0.0,
                    "end_time": 18.4,
                    "duration": 18.4,
                    "matched_text": "对应的旁白文本段落",
                    "confidence": 0.95
                },
                ...
            ]
        
        对齐策略：
        1. 加载所有图片（压缩以节省token）
        2. 构建prompt，让LLM分析每张图与文本的语义对应关系
        3. 根据LLM返回的匹配结果，结合Whisper时间戳计算精确时间
        4. 验证和调整，确保无重叠无间隙
        """
        # 1. 压缩并编码图片
        encoded_images = await self._prepare_images(images)
        
        # 2. 构建匹配prompt
        prompt = self._build_alignment_prompt(
            images=images,
            segments=segments,
            full_text=full_text
        )
        
        # 3. 调用Gemini 2.5 Flash进行匹配
        # 传入所有图片 + prompt
        contents = []
        for img_data in encoded_images:
            contents.append({
                "mime_type": "image/jpeg",
                "data": img_data["base64"]
            })
        contents.append(prompt)
        
        response = await self.model.generate_content_async(
            contents,
            generation_config={
                "temperature": 0.2,  # 低温度确保一致性
                "response_mime_type": "application/json"
            }
        )
        
        # 4. 解析LLM返回的匹配结果
        matching = json.loads(response.text)
        
        # 5. 计算精确时间轴
        timeline = self._calculate_timeline(
            matching=matching,
            segments=segments,
            audio_duration=audio_duration
        )
        
        # 6. 验证和调整
        timeline = self._validate_and_adjust(timeline, audio_duration)
        
        return timeline
    
    async def _prepare_images(
        self,
        images: list[dict],
        max_size: int = 512
    ) -> list[dict]:
        """
        压缩图片并转为base64
        
        使用较小尺寸以节省token，同时添加 detail: "low" 参数
        """
        encoded = []
        for img_info in images:
            # 加载并压缩
            img = Image.open(img_info["path"])
            img.thumbnail((max_size, max_size))
            
            # 转为JPEG base64（JPEG比PNG小）
            from io import BytesIO
            buffer = BytesIO()
            img.convert("RGB").save(buffer, format="JPEG", quality=85)
            b64 = base64.b64encode(buffer.getvalue()).decode()
            
            encoded.append({
                "scene_id": img_info["scene_id"],
                "base64": b64
            })
        
        return encoded
    
    def _build_alignment_prompt(
        self,
        images: list[dict],
        segments: list[dict],
        full_text: str
    ) -> str:
        """
        构建图文匹配的prompt
        """
        # 格式化segments信息
        segments_info = []
        for seg in segments:
            segments_info.append(
                f"[{seg['start']:.2f}s - {seg['end']:.2f}s]: {seg['text']}"
            )
        
        # 格式化图片信息
        images_info = []
        for i, img in enumerate(images):
            images_info.append(
                f"图片{i+1} (scene_id={img['scene_id']}): {img.get('visual_description', '无描述')}"
            )
        
        prompt = f"""你是一个专业的视频编辑助手。请分析以下图片和音频文本，将每张图片匹配到最合适的音频时间段。

## 音频转录（带时间戳）

{chr(10).join(segments_info)}

## 图片列表

{chr(10).join(images_info)}

## 任务

分析每张图片的内容，将其匹配到语义上最相关的音频段落。

## 匹配原则

1. **语义匹配**：图片内容应与对应文本在语义上相关
2. **顺序性**：图片通常按故事顺序排列，匹配结果应大致保持顺序
3. **完整覆盖**：所有图片必须分配时间段，所有时间段必须被覆盖
4. **无重叠**：相邻图片的时间段不能重叠
5. **时长合理**：每张图片的停留时长应合理（通常10-40秒）

## 输出格式

请以JSON格式输出匹配结果：

```json
{{
  "matches": [
    {{
      "scene_id": 1,
      "start_segment_index": 0,
      "end_segment_index": 2,
      "reasoning": "简短说明匹配理由"
    }}
  ]
}}
```

请严格按照JSON格式输出，不要添加其他内容。
"""
        return prompt
    
    def _calculate_timeline(
        self,
        matching: dict,
        segments: list[dict],
        audio_duration: float
    ) -> list[dict]:
        """
        根据匹配结果计算精确时间轴
        """
        timeline = []
        
        for match in matching.get("matches", []):
            scene_id = match["scene_id"]
            start_idx = match["start_segment_index"]
            end_idx = match["end_segment_index"]
            
            # 获取对应的时间范围
            start_time = segments[start_idx]["start"]
            end_time = segments[end_idx]["end"]
            
            # 收集匹配的文本
            matched_texts = [
                segments[i]["text"] 
                for i in range(start_idx, end_idx + 1)
            ]
            
            timeline.append({
                "scene_id": scene_id,
                "start_time": start_time,
                "end_time": end_time,
                "duration": end_time - start_time,
                "matched_text": " ".join(matched_texts),
                "segment_indices": list(range(start_idx, end_idx + 1))
            })
        
        # 按start_time排序
        timeline.sort(key=lambda x: x["start_time"])
        
        return timeline
    
    def _validate_and_adjust(
        self,
        timeline: list[dict],
        audio_duration: float
    ) -> list[dict]:
        """
        验证并调整时间轴
        
        确保：
        1. 时间轴从0开始
        2. 时间轴覆盖整个音频
        3. 无重叠无间隙
        """
        if not timeline:
            return timeline
        
        # 调整第一个场景从0开始
        timeline[0]["start_time"] = 0.0
        
        # 调整相邻场景边界，消除间隙和重叠
        for i in range(1, len(timeline)):
            prev_end = timeline[i-1]["end_time"]
            curr_start = timeline[i]["start_time"]
            
            # 如果有间隙或重叠，调整边界
            if abs(curr_start - prev_end) > 0.1:
                # 取中间值
                mid_point = (prev_end + curr_start) / 2
                timeline[i-1]["end_time"] = mid_point
                timeline[i]["start_time"] = mid_point
        
        # 确保最后一个场景覆盖到音频结尾
        timeline[-1]["end_time"] = audio_duration
        
        # 重新计算duration
        for item in timeline:
            item["duration"] = item["end_time"] - item["start_time"]
        
        return timeline
```

### 模块4：音频存储服务 (audio_storage.py)

```python
import os
import uuid

class AudioStorageService:
    """
    音频存储服务
    
    存储结构：
    storage/
    └── audio/
        └── {project_id}/
            └── {chapter_id}/
                ├── narration.mp3       # 旁白音频
                └── narration_meta.json # 元数据
    """
    
    def __init__(self, base_path: str = "./storage/audio"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
    
    async def save_audio(
        self,
        audio_data: bytes,
        project_id: str,
        chapter_id: str,
        audio_format: str = "mp3"
    ) -> dict:
        """
        保存音频文件
        
        Returns:
            {
                "audio_path": "相对路径",
                "full_path": "绝对路径",
                "format": "mp3"
            }
        """
        # 创建目录
        dir_path = os.path.join(self.base_path, project_id, chapter_id)
        os.makedirs(dir_path, exist_ok=True)
        
        # 保存音频
        filename = f"narration.{audio_format}"
        audio_path = os.path.join(dir_path, filename)
        
        with open(audio_path, 'wb') as f:
            f.write(audio_data)
        
        return {
            "audio_path": os.path.relpath(audio_path, self.base_path),
            "full_path": os.path.abspath(audio_path),
            "format": audio_format
        }
    
    def get_audio_path(
        self,
        project_id: str,
        chapter_id: str,
        filename: str = "narration.mp3"
    ) -> str:
        """获取音频文件完整路径"""
        return os.path.join(self.base_path, project_id, chapter_id, filename)
```

---

## API端点扩展

**扩展 chapters.py**：

```python
@router.post("/{project_id}/chapters/{chapter_number}/generate-audio")
async def generate_chapter_audio(
    project_id: str,
    chapter_number: int,
    voice_preset: str = "zh_female_tianmei",
    speed_ratio: float = 1.0,
    user_id: str = Header(..., alias="X-User-ID"),
    background_tasks: BackgroundTasks
):
    """
    为章节生成旁白音频
    
    前置条件：章节故事已生成完成
    
    流程：
    1. 提取所有场景的narration文本
    2. 调用TTS合成音频
    3. 调用Whisper获取时间戳
    4. 保存音频和元数据
    """
    pass

@router.post("/{project_id}/chapters/{chapter_number}/align")
async def align_chapter_audio_images(
    project_id: str,
    chapter_number: int,
    user_id: str = Header(..., alias="X-User-ID"),
    background_tasks: BackgroundTasks
):
    """
    执行音画对齐
    
    前置条件：
    - 章节图像已生成完成
    - 章节音频已生成完成
    
    流程：
    1. 加载音频时间戳
    2. 加载所有场景图片
    3. 调用Gemini进行图文匹配
    4. 生成时间轴映射
    5. 保存timeline_json
    """
    pass

@router.get("/{project_id}/chapters/{chapter_number}/timeline")
async def get_chapter_timeline(
    project_id: str,
    chapter_number: int,
    user_id: str = Header(..., alias="X-User-ID")
):
    """
    获取章节的音画时间轴
    
    Returns:
        {
            "timeline": [
                {
                    "scene_id": 1,
                    "image_url": "/api/images/...",
                    "start_time": 0.0,
                    "end_time": 18.4,
                    "duration": 18.4,
                    "narration": "对应的旁白文本"
                }
            ],
            "audio_url": "/api/audio/...",
            "total_duration": 180.5
        }
    """
    pass

@router.get("/{project_id}/chapters/{chapter_number}/audio")
async def get_chapter_audio(
    project_id: str,
    chapter_number: int,
    user_id: str = Header(..., alias="X-User-ID")
):
    """
    获取章节音频文件
    """
    pass
```

**新增 audio.py**：

```python
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/audio", tags=["audio"])

@router.get("/{project_id}/{chapter_id}/{filename}")
async def serve_audio(project_id: str, chapter_id: str, filename: str):
    """提供音频文件访问"""
    pass
```

---

## 生成任务流程

```python
async def generate_audio_and_align_task(job_id: str, chapter_id: str, voice_preset: str):
    """
    音频生成+对齐后台任务
    
    步骤：
    1. 加载章节数据
    2. 提取所有narration文本
    3. TTS合成音频
    4. Whisper获取时间戳
    5. 加载场景图片
    6. Gemini图文匹配
    7. 生成时间轴
    8. 保存结果
    """
    try:
        # 1. 加载数据
        await update_job_status(job_id, "processing", "loading_data", 5)
        chapter = await get_chapter(chapter_id)
        scenes = json.loads(chapter.scenes_json)
        
        # 2. 提取旁白
        await update_job_status(job_id, "processing", "extracting_narration", 10)
        narrations = [scene['narration'] for scene in scenes]
        
        # 3. TTS合成
        await update_job_status(job_id, "processing", "synthesizing_audio", 20, "正在合成语音...")
        tts = TTSService()
        audio_result = await tts.synthesize_chapter(narrations, voice_preset)
        
        if not audio_result['success']:
            raise Exception(f"TTS合成失败: {audio_result.get('error')}")
        
        # 4. 保存音频
        await update_job_status(job_id, "processing", "saving_audio", 35)
        audio_storage = AudioStorageService()
        saved = await audio_storage.save_audio(
            audio_data=audio_result['audio_data'],
            project_id=chapter.project_id,
            chapter_id=chapter.id
        )
        
        # 5. Whisper时间戳
        await update_job_status(job_id, "processing", "extracting_timestamps", 50, "正在分析音频时间戳...")
        whisper = WhisperService()
        transcript = await whisper.transcribe_with_timestamps(saved['full_path'])
        
        # 6. 加载图片信息
        await update_job_status(job_id, "processing", "loading_images", 60)
        images = await get_chapter_images(chapter_id)
        
        # 7. 图文匹配
        await update_job_status(job_id, "processing", "aligning", 70, "正在进行音画对齐...")
        alignment = AlignmentService()
        timeline = await alignment.align_images_to_audio(
            images=[{
                "scene_id": img.scene_id,
                "path": img.full_path,
                "visual_description": img.image_prompt
            } for img in images],
            segments=transcript['segments'],
            full_text=transcript['text'],
            audio_duration=transcript['duration']
        )
        
        # 8. 保存结果
        await update_job_status(job_id, "processing", "saving_results", 90)
        await update_chapter(
            chapter_id,
            audio_path=saved['audio_path'],
            audio_duration_seconds=transcript['duration'],
            transcript_json=json.dumps(transcript),
            timeline_json=json.dumps(timeline),
            status="audio_ready"
        )
        
        # 完成
        await update_job_status(job_id, "completed", "audio_ready", 100, "音频合成和对齐完成！")
        
    except Exception as e:
        await update_job_status(job_id, "failed", error_message=str(e))
        raise
```

---

## 状态机扩展

```
... (前序状态)
    │
    ▼
images_ready
    │
    ▼ (触发音频生成)
generating_audio ──────────────┐
    │                          │ (失败可重试)
    ▼                          │
audio_synthesized ◄────────────┘
    │
    ▼ (触发对齐)
aligning ──────────────────────┐
    │                          │ (失败可重试)
    ▼                          │
audio_ready ◄──────────────────┘
    │
    ▼ (Phase 4: 视频合成)
compositing
    ...
```

---

## 依赖更新

在 `requirements.txt` 中添加：

```txt
# ===== Phase 3: Audio =====
# OpenAI (Whisper)
openai>=1.0.0

# 火山引擎SDK（如果有官方SDK）
# volcengine-python-sdk>=x.x.x

# 或者使用HTTP请求
requests>=2.31.0

# 音频处理（可选，用于获取音频时长等）
pydub>=0.25.0
```

---

## Phase 3 验收标准

| 标准 | 说明 |
|------|------|
| TTS合成 | 调用豆包TTS成功生成音频 |
| 音色支持 | 支持多种中文音色选择 |
| Whisper时间戳 | 成功获取word/segment级时间戳 |
| 图文匹配 | Gemini正确匹配图片与音频段落 |
| 时间轴生成 | 输出完整的timeline_json |
| 对齐精度 | 音画误差≤80ms |
| 状态追踪 | 各阶段进度可查询 |
| 错误处理 | 失败有清晰错误信息，支持重试 |

---

## 开发顺序

1. **配置环境**：获取火山引擎AK/SK，配置.env
2. **阅读文档**：仔细阅读豆包TTS API文档
3. **实现TTS服务**：先跑通单段文本合成
4. **实现Whisper服务**：参考项目中的whisper_timestamp_test.py
5. **实现音频存储**：简单的文件存储
6. **实现对齐服务**：Gemini图文匹配
7. **集成API端点**：串联完整流程
8. **集成测试**：验证全流程

---

## 测试脚本示例

```python
# tests/test_tts_service.py

import asyncio
from app.services.tts_service import TTSService

async def test_tts():
    """测试TTS合成"""
    tts = TTSService()
    
    result = await tts.synthesize(
        text="你好，欢迎使用序话Story。这是一个AI短视频生成应用。",
        voice_preset="zh_female_tianmei",
        speed_ratio=1.0
    )
    
    print(f"Success: {result['success']}")
    print(f"Duration: {result.get('duration_seconds')}s")
    
    if result['success']:
        with open("test_audio.mp3", "wb") as f:
            f.write(result['audio_data'])
        print("Audio saved to test_audio.mp3")

if __name__ == "__main__":
    asyncio.run(test_tts())
```

```python
# tests/test_alignment.py

import asyncio
from app.services.alignment_service import AlignmentService

async def test_alignment():
    """测试音画对齐"""
    # 准备测试数据
    images = [
        {"scene_id": 1, "path": "test_image_1.png", "visual_description": "程序员在电脑前"},
        {"scene_id": 2, "path": "test_image_2.png", "visual_description": "城市夜景"},
    ]
    
    segments = [
        {"start": 0.0, "end": 5.0, "text": "在一个深夜，程序员小明还在加班"},
        {"start": 5.0, "end": 10.0, "text": "窗外是璀璨的城市灯火"},
    ]
    
    alignment = AlignmentService()
    timeline = await alignment.align_images_to_audio(
        images=images,
        segments=segments,
        full_text="在一个深夜，程序员小明还在加班。窗外是璀璨的城市灯火。",
        audio_duration=10.0
    )
    
    print("Timeline:")
    for item in timeline:
        print(f"  Scene {item['scene_id']}: {item['start_time']:.2f}s - {item['end_time']:.2f}s")

if __name__ == "__main__":
    asyncio.run(test_alignment())
```

---

## 注意事项

1. **火山引擎鉴权**：需要正确实现AK/SK签名，参考官方文档
2. **Whisper同步API**：OpenAI SDK的Whisper是同步的，需要用线程池包装
3. **图片压缩**：传给Gemini前压缩图片，使用`detail: "low"`节省token
4. **长文本处理**：TTS可能有字数限制，需要分段合成再拼接
5. **时间轴验证**：确保时间轴无重叠、无间隙、覆盖完整
6. **错误重试**：网络不稳定时的重试机制
7. **成本控制**：监控API调用量

---

## 参考资源

- [火山引擎TTS文档](https://www.volcengine.com/docs/6561/1257584)
- [火山引擎音色列表](https://www.volcengine.com/docs/6561/79823)
- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
- [Gemini 2.5 Flash](https://ai.google.dev/gemini-api/docs)
- [项目中的 whisper_timestamp_test.py](./whisper_timestamp_test.py)
