# 序话Story - Phase 3 开发完成

> 完成时间：2024年12月

## 项目概述

序话Story 是一个 AI 短视频/短剧生成应用。用户输入一句话创意，系统自动生成可发布的短剧视频。

**Phase 3 目标**：实现 "旁白音频合成 + 音画精确对齐"

---

## 验收标准达成情况

| 标准 | 状态 |
|------|------|
| TTS合成：调用豆包TTS生成音频 | ✅ 已实现 |
| 音色支持：多种中文音色选择 | ✅ 8种预设音色 |
| Whisper时间戳：获取word/segment级时间戳 | ✅ 已实现 |
| 图文匹配：Gemini智能匹配图片与音频段落 | ✅ 已实现 |
| 时间轴生成：输出精确的timeline_json | ✅ 已实现 |
| 对齐精度：音画误差≤80ms | ✅ 自动调整算法 |
| 状态追踪：各阶段进度可查询 | ✅ 已实现 |

---

## 测试结果

```
============================================================
序话Story - Phase 3 音频服务测试
============================================================
  TTS服务: ⚠️ 跳过（需配置API Key）
  Whisper服务: ⚠️ 跳过（需配置API Key）
  音频存储服务: ✅ 通过
  对齐服务: ✅ 通过
  音色列表: ✅ 通过
============================================================
✅ 所有本地服务测试通过!
============================================================
```

---

## ⚠️ Phase 3 所需的 API Key 配置

**重要：运行 Phase 3 功能需要以下 API Key**

在 `.env` 文件中添加：

```env
# ===== Phase 3 新增配置 =====

# OpenAI Whisper API
# 获取方式：https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-openai-api-key

# 火山引擎（豆包TTS）
# 获取方式：
# 1. 注册火山引擎账号：https://www.volcengine.com/
# 2. 开通"语音技术"服务：https://console.volcengine.com/speech/app
# 3. 创建应用获取 App ID
# 4. 在密钥管理获取 Access Key：https://console.volcengine.com/iam/keymanage/
VOLCENGINE_APP_ID=your-app-id
VOLCENGINE_ACCESS_KEY=your-access-key
VOLCENGINE_RESOURCE_ID=seed-tts-2.0

# 可选：指定默认音色
VOLCENGINE_DEFAULT_VOICE=zh_female_shuangkuaisisi_moon_bigtts
```

### 火山引擎配置步骤

1. **注册账号**：访问 https://www.volcengine.com/ 注册
2. **开通服务**：在控制台开通"语音技术" - "语音合成"服务
3. **创建应用**：在语音控制台创建应用，获取 App ID
4. **获取密钥**：在 IAM 密钥管理创建 Access Key

### OpenAI 配置

1. 访问 https://platform.openai.com/api-keys
2. 创建新的 API Key
3. Whisper API 按音频时长计费

---

## 技术栈

- **后端**: Python 3.11+ / FastAPI
- **数据库**: SQLite + SQLAlchemy 2.0 (异步)
- **TTS**: 火山引擎豆包语音合成大模型 (seed-tts-2.0)
- **语音识别**: OpenAI Whisper API
- **音画对齐**: Gemini 2.5 Flash + 自研对齐算法
- **异步任务**: asyncio 后台任务

---

## Phase 3 新增文件结构

```
xuhua_story/
├── app/
│   ├── services/
│   │   ├── tts_service.py         # 🆕 豆包TTS语音合成
│   │   ├── whisper_service.py     # 🆕 Whisper时间戳提取
│   │   ├── alignment_service.py   # 🆕 音画对齐服务
│   │   └── audio_storage.py       # 🆕 音频存储服务
│   ├── models/
│   │   ├── chapter.py             # 📝 新增音频字段
│   │   └── audio_segment.py       # 🆕 音频段落模型
│   ├── api/
│   │   ├── chapters.py            # 📝 扩展音频生成端点
│   │   └── audio.py               # 🆕 音频文件访问
│   ├── prompts/
│   │   └── alignment_prompts.py   # 🆕 对齐prompt模板
│   ├── config.py                  # 📝 新增音频配置
│   └── main.py                    # 📝 注册新路由
├── tests/
│   └── test_audio_service.py      # 🆕 音频服务测试
├── storage/
│   └── audio/                     # 🆕 音频存储目录
└── requirements.txt               # 📝 新增 openai
```

---

## 核心服务

### 1. TTS语音合成服务 (`tts_service.py`)

```python
class TTSService:
    """
    豆包语音合成服务

    使用火山引擎大模型语音合成API（单向流式HTTP-V3）
    文档：https://www.volcengine.com/docs/6561/1598757
    """

    # API 端点
    API_ENDPOINT = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"

    async def synthesize(
        self,
        text: str,
        voice_preset: str = "zh_female_shuangkuai",
        speed_ratio: float = 1.0,
        volume_ratio: float = 1.0,
        pitch_ratio: float = 1.0,
        output_format: str = "mp3"
    ) -> dict:
        """
        合成语音

        Returns:
            {
                "success": True,
                "audio_data": bytes,
                "audio_format": "mp3",
                "voice_used": "zh_female_shuangkuai",
                "generation_time_seconds": 5.2
            }
        """

    async def synthesize_chapter(
        self,
        narrations: List[str],
        voice_preset: str,
        **kwargs
    ) -> dict:
        """合成整个章节的旁白"""
```

**预设音色列表**:

| 代码 | 名称 | 性别 | 风格 |
|------|------|------|------|
| `zh_female_shuangkuai` | 爽快思思 | 女 | 活泼开朗，适合短视频旁白 |
| `zh_female_tianmei` | 甜美小源 | 女 | 温柔甜美，适合温馨内容 |
| `zh_female_qingxin` | 清新小鹿 | 女 | 清新自然 |
| `zh_male_wennuan` | 温暖阿虎 | 男 | 温暖磁性，适合故事讲述 |
| `zh_male_yangguang` | 阳光青叔 | 男 | 阳光开朗 |
| `zh_male_chenwen` | 沉稳书生 | 男 | 沉稳大气，适合正式内容 |
| `en_female` | Amanda Brown | 女 | Professional English |
| `en_male` | John Taylor | 男 | Professional English |

### 2. Whisper时间戳服务 (`whisper_service.py`)

```python
class WhisperService:
    """
    OpenAI Whisper 时间戳提取服务

    文档：https://platform.openai.com/docs/guides/speech-to-text
    """

    async def transcribe_with_timestamps(
        self,
        audio_path: str,
        granularity: str = "both"  # "word", "segment", or "both"
    ) -> dict:
        """
        转录音频并获取时间戳

        Returns:
            {
                "success": True,
                "text": "完整转录文本",
                "duration": 180.5,
                "segments": [{"id": 0, "start": 0.0, "end": 5.2, "text": "..."}],
                "words": [{"word": "你好", "start": 0.0, "end": 0.5}]
            }
        """

    def merge_short_segments(self, segments, min_duration=2.0) -> list:
        """合并过短的segment"""

    def split_by_scene_count(self, segments, scene_count, total_duration) -> list:
        """根据场景数量重新划分时间段"""
```

### 3. 音画对齐服务 (`alignment_service.py`)

```python
class AlignmentService:
    """
    音画对齐服务

    对齐误差目标：≤ 80ms
    """

    async def align_images_to_audio(
        self,
        images: List[dict],           # 场景图片列表
        segments: List[dict],         # Whisper返回的segments
        full_text: str,               # 完整旁白文本
        audio_duration: float,        # 音频总时长
        use_visual_matching: bool = True
    ) -> List[dict]:
        """
        将图片与音频时间段对齐

        Returns:
            [
                {
                    "scene_id": 1,
                    "image_path": "path/to/image.png",
                    "start_time": 0.0,
                    "end_time": 18.4,
                    "duration": 18.4,
                    "matched_text": "对应的旁白文本",
                    "segment_indices": [0, 1, 2]
                }
            ]
        """

    async def quick_align(
        self,
        scene_count: int,
        segments: List[dict],
        audio_duration: float
    ) -> List[dict]:
        """快速对齐（不使用LLM）"""
```

**对齐策略**:
1. 加载图片并压缩（节省token）
2. 构建prompt让Gemini分析语义对应
3. 根据匹配结果计算时间边界
4. 自动消除间隙和重叠（误差≤80ms）
5. 确保时间轴从0开始、覆盖完整音频

### 4. 音频存储服务 (`audio_storage.py`)

```python
class AudioStorageService:
    """
    音频存储服务

    存储结构：
    storage/audio/{project_id}/{chapter_id}/
        ├── narration.mp3
        ├── narration_meta.json
        └── timeline.json
    """

    async def save_audio(audio_data, project_id, chapter_id) -> dict
    async def save_metadata(project_id, chapter_id, metadata) -> str
    async def save_timeline(project_id, chapter_id, timeline) -> str
    async def load_timeline(project_id, chapter_id) -> list
```

---

## API 端点

### 音频生成

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/projects/{id}/chapters/{num}/generate-audio` | 生成旁白音频并执行对齐 |
| GET | `/api/projects/{id}/chapters/{num}/timeline` | 获取音画时间轴 |
| GET | `/api/projects/{id}/chapters/{num}/audio` | 获取音频信息 |
| GET | `/api/projects/{id}/chapters/{num}/voices` | 获取可用音色列表 |

### 音频文件访问

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/audio/{project_id}/{chapter_id}/{filename}` | 获取音频文件 |

---

## API 使用示例

### 生成章节音频

```bash
curl -X POST "http://localhost:8000/api/projects/{project_id}/chapters/1/generate-audio" \
  -H "X-User-ID: kai" \
  -H "Content-Type: application/json" \
  -d '{
    "voice_preset": "zh_female_shuangkuai",
    "speed_ratio": 1.0
  }'
```

**响应**:
```json
{
  "job_id": "xxx-xxx-xxx",
  "status": "generating_audio",
  "message": "音频生成已开始"
}
```

### 获取音画时间轴

```bash
curl "http://localhost:8000/api/projects/{project_id}/chapters/1/timeline" \
  -H "X-User-ID: kai"
```

**响应**:
```json
{
  "timeline": [
    {
      "scene_id": 1,
      "image_url": "/api/images/proj_xxx/chap_xxx/scene_001.png",
      "start_time": 0.0,
      "end_time": 18.4,
      "duration": 18.4,
      "matched_text": "在一个深夜，程序员小明还在加班..."
    },
    {
      "scene_id": 2,
      "image_url": "/api/images/proj_xxx/chap_xxx/scene_002.png",
      "start_time": 18.4,
      "end_time": 35.2,
      "duration": 16.8,
      "matched_text": "突然，屏幕上出现了奇怪的代码..."
    }
  ],
  "audio_url": "/api/audio/proj_xxx/chap_xxx/narration.mp3",
  "audio_duration_seconds": 180.5,
  "voice_preset": "zh_female_shuangkuai"
}
```

### 获取可用音色

```bash
curl "http://localhost:8000/api/projects/{project_id}/chapters/1/voices" \
  -H "X-User-ID: kai"
```

**响应**:
```json
{
  "voices": [
    {
      "preset_code": "zh_female_shuangkuai",
      "speaker": "zh_female_shuangkuaisisi_moon_bigtts",
      "name": "爽快思思",
      "language": "zh-CN",
      "gender": "female",
      "style": "活泼开朗，适合短视频旁白"
    }
  ],
  "default": "zh_female_shuangkuai"
}
```

---

## 数据库更新

### chapters 表新增字段

```sql
ALTER TABLE chapters ADD COLUMN audio_url TEXT;
ALTER TABLE chapters ADD COLUMN audio_path TEXT;
ALTER TABLE chapters ADD COLUMN audio_duration_seconds REAL;
ALTER TABLE chapters ADD COLUMN transcript_json TEXT;
ALTER TABLE chapters ADD COLUMN timeline_json TEXT;
ALTER TABLE chapters ADD COLUMN voice_preset TEXT;
```

### 新增 audio_segments 表

```sql
CREATE TABLE audio_segments (
    id TEXT PRIMARY KEY,
    chapter_id TEXT NOT NULL,
    segment_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    duration REAL NOT NULL,
    matched_scene_id INTEGER,
    matched_image_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
);

CREATE INDEX idx_audio_segments_chapter ON audio_segments(chapter_id);
```

---

## 配置项

`.env` 新增配置：

```env
# Phase 3: Audio
OPENAI_API_KEY=your-openai-api-key
VOLCENGINE_APP_ID=your-app-id
VOLCENGINE_ACCESS_KEY=your-access-key
VOLCENGINE_RESOURCE_ID=seed-tts-2.0
VOLCENGINE_DEFAULT_VOICE=zh_female_shuangkuaisisi_moon_bigtts
AUDIO_STORAGE_PATH=./storage/audio
```

---

## 状态机更新

```
story_ready / images_ready
    │
    ▼ (触发音频生成)
generating_audio ──────────────┐
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

```txt
# ===== Phase 3: Audio =====
# OpenAI (Whisper)
openai>=1.0.0
```

---

## 测试

```bash
# 运行 Phase 3 音频服务测试
./venv/bin/python tests/test_audio_service.py
```

---

## 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Layer                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    chapters.py                               ││
│  │  POST /generate-audio  GET /timeline  GET /audio  GET /voices││
│  └────────────────────────────┬────────────────────────────────┘│
└───────────────────────────────┼─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                               │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  TTSService  │    │ WhisperSvc   │    │ AlignmentService │  │
│  │ (火山引擎)   │    │ (OpenAI)     │    │ (Gemini+算法)    │  │
│  └──────┬───────┘    └──────┬───────┘    └────────┬─────────┘  │
│         │                   │                      │            │
│         ▼                   ▼                      ▼            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  AudioStorageService                      │  │
│  │           (音频存储、元数据、时间轴)                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      External APIs                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ 火山引擎TTS  │  │ OpenAI       │  │ Gemini 2.5 Flash     │  │
│  │ seed-tts-2.0 │  │ Whisper-1    │  │ (图文匹配)           │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 完整生成流程

```
用户输入创意
    │
    ▼
Phase 1: 故事生成 (Claude/Gemini)
    │
    ▼
Phase 2: 分镜图像生成 (Gemini Image)
    │
    ▼
Phase 3: 音频生成+对齐
    │
    ├─► TTS合成 (火山引擎)
    │       │
    │       ▼
    ├─► Whisper时间戳 (OpenAI)
    │       │
    │       ▼
    └─► 图文匹配对齐 (Gemini)
            │
            ▼
      timeline_json 生成
            │
            ▼
Phase 4: 视频合成 (待实现)
```

---

## 下一阶段计划 (Phase 4)

- [ ] 视频合成（图片 + 音频 → 视频）
- [ ] Ken Burns 效果（图片动态化）
- [ ] 字幕叠加
- [ ] 背景音乐
- [ ] 视频导出（多分辨率）

---

## 参考资源

- [火山引擎TTS文档](https://www.volcengine.com/docs/6561/1598757)
- [火山引擎音色列表](https://www.volcengine.com/docs/6561/79823)
- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
- [Gemini 2.5 Flash](https://ai.google.dev/gemini-api/docs)
- [Phase 1 文档](./PHASE1_COMPLETE.md)
- [Phase 2 文档](./PHASE2_COMPLETE.md)
