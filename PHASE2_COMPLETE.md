# 序话Story - Phase 2 开发完成

> 完成时间：2024年12月

## 项目概述

序话Story 是一个 AI 短视频/短剧生成应用。用户输入一句话创意，系统自动生成可发布的短剧视频。

**Phase 2 目标**：实现 "故事 → 分镜图像" 的完整流程

---

## 验收标准达成情况

| 标准 | 状态 |
|------|------|
| 图像生成：使用 Gemini API 成功生成图像 | ✅ |
| 分镜服务：将故事场景转换为图像生成 prompt | ✅ |
| 存储服务：图像本地存储 + 缩略图生成 | ✅ |
| API 端点：支持批量生成、单图重新生成、图像获取 | ✅ |
| 风格支持：10种风格预设 | ✅ |

---

## 测试结果

```
============================================================
序话Story - Phase 2 图像生成测试
============================================================
  单图生成: ✅ 通过 (1344x768, 13.37秒)
  分镜Prompt: ✅ 通过 (471字符)
  分镜图像生成: ✅ 通过 (768x1344, 8.98秒)
  存储服务: ✅ 通过
============================================================
✅ 所有测试通过!
============================================================
```

---

## 技术栈

- **后端**: Python 3.11+ / FastAPI
- **数据库**: SQLite + SQLAlchemy 2.0 (异步)
- **故事生成**: Claude Haiku 4.5 (主) / Gemini (备)
- **图像生成**: Gemini 2.5 Flash Image (主) / Gemini 3 Pro Image Preview (备)
- **图像处理**: Pillow
- **异步任务**: asyncio 后台任务

---

## Phase 2 新增文件结构

```
xuhua_story/
├── app/
│   ├── services/
│   │   ├── image_generator.py     # 🆕 Gemini 图像生成服务
│   │   ├── image_storage.py       # 🆕 图像存储服务
│   │   └── storyboard_service.py  # 🆕 分镜决策服务
│   ├── models/
│   │   └── scene_image.py         # 🆕 场景图像数据模型
│   ├── api/
│   │   ├── images.py              # 🆕 图像访问端点
│   │   └── chapters.py            # 📝 扩展图像生成端点
│   ├── prompts/
│   │   └── storyboard_prompts.py  # 🆕 分镜 prompt 模板
│   ├── config.py                  # 📝 新增图像配置
│   └── main.py                    # 📝 注册新路由
├── tests/
│   └── test_image_generator.py    # 🆕 图像生成测试
├── storage/
│   └── images/                    # 🆕 图像存储目录
└── requirements.txt               # 📝 新增 Pillow, aiohttp
```

---

## 核心服务

### 1. 图像生成服务 (`image_generator.py`)

```python
class ImageGenerator:
    # 模型配置
    FAST_MODEL = "gemini-2.5-flash-image"      # 主模型：快速生成
    PRO_MODEL = "gemini-3-pro-image-preview"   # 备用：支持参考图

    # 重试配置
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        aspect_ratio: str = "16:9",
        reference_images: Optional[List[Image.Image]] = None,
        style_preset: str = None,
        use_pro_model: bool = False,
    ) -> dict:
        """
        生成单张图像

        Returns:
            {
                "success": True,
                "image_data": "base64编码的图像",
                "pil_image": PIL.Image对象,
                "width": 1920,
                "height": 1080,
                "model_used": "gemini-2.5-flash-image",
                "generation_time_seconds": 12.5
            }
        """

    async def generate_batch(
        self,
        prompts: List[dict],
        max_concurrent: int = 3
    ) -> List[dict]:
        """批量并行生成图像"""
```

**关键特性**：
- 自动重试机制（3次）
- 批量并行生成（可配置并发数）
- 支持参考图（角色一致性）
- 多种宽高比支持

### 2. 分镜服务 (`storyboard_service.py`)

```python
class StoryboardService:
    async def generate_storyboard(
        self,
        scenes: List[dict],
        characters: List[dict],
        style_preset: str,
        aspect_ratio: str = "16:9"
    ) -> List[dict]:
        """
        将故事场景转换为图像生成 storyboard

        Returns:
            [{
                "scene_id": 1,
                "image_prompt": "完整的图像生成prompt",
                "negative_prompt": "负面提示词",
                "aspect_ratio": "16:9",
                "characters_in_scene": ["林城", "小美"],
                "mood": "紧张"
            }, ...]
        """
```

### 3. 存储服务 (`image_storage.py`)

```python
class ImageStorageService:
    async def save_image(
        self,
        image_data: str,          # base64
        project_id: str,
        chapter_id: str,
        scene_id: int
    ) -> dict:
        """
        保存图像（含缩略图）

        Returns:
            {
                "image_path": "project_id/chapter_id/scene_001.png",
                "thumbnail_path": "project_id/chapter_id/scene_001_thumb.png",
                "full_path": "/abs/path/to/image.png"
            }
        """

    async def save_character_reference(
        self,
        image_data: str,
        project_id: str,
        character_name: str
    ) -> dict:
        """保存角色参考图"""

    async def load_image_as_pil(self, relative_path: str) -> Image.Image:
        """加载图像为 PIL Image 对象"""
```

### 4. 角色一致性管理器 (`image_generator.py`)

```python
class CharacterConsistencyManager:
    """
    角色一致性策略：
    1. 首次生成：为每个角色生成"参考图"（角色立绘）
    2. 后续生成：将参考图作为 reference_images 传入
    3. Prompt强化：在每个场景的 prompt 中重复角色的固定描述
    """

    async def get_character_references(
        self,
        project_id: str,
        characters: List[dict],
        style_preset: str
    ) -> dict:
        """获取或生成角色参考图"""

    async def generate_character_portrait(
        self,
        character: dict,
        style_preset: str
    ) -> dict:
        """生成角色立绘"""
```

---

## API 端点

### 图像生成

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/projects/{id}/chapters/{num}/generate-images` | 为章节生成所有场景图像 |
| GET | `/api/projects/{id}/chapters/{num}/images` | 获取章节图像列表 |
| POST | `/api/projects/{id}/chapters/{num}/images/{scene_id}/regenerate` | 重新生成单个场景图像 |

### 图像访问

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/images/{project_id}/{chapter_id}/{filename}` | 获取图像文件 |

---

## API 使用示例

### 生成章节图像

```bash
# 启动图像生成任务
curl -X POST "http://localhost:8000/api/projects/{project_id}/chapters/1/generate-images" \
  -H "X-User-ID: kai" \
  -H "Content-Type: application/json" \
  -d '{
    "style_preset": "cyberpunk"
  }'
```

**响应**:
```json
{
  "job_id": "img_xxx-xxx-xxx",
  "status": "generating_images",
  "message": "图像生成已开始",
  "total_scenes": 5
}
```

### 查询图像生成状态

```bash
curl "http://localhost:8000/api/projects/{project_id}/chapters/1/status" \
  -H "X-User-ID: kai"
```

**响应**:
```json
{
  "status": "processing",
  "stage": "image_generation",
  "progress": 60,
  "message": "正在生成场景图像 (3/5)..."
}
```

### 获取章节图像列表

```bash
curl "http://localhost:8000/api/projects/{project_id}/chapters/1/images" \
  -H "X-User-ID: kai"
```

**响应**:
```json
{
  "images": [
    {
      "scene_id": 1,
      "image_url": "/api/images/proj_xxx/chap_xxx/scene_001.png",
      "thumbnail_url": "/api/images/proj_xxx/chap_xxx/scene_001_thumb.png",
      "width": 1344,
      "height": 768,
      "prompt": "A cyberpunk programmer...",
      "generation_time_seconds": 12.5
    }
  ],
  "total": 5,
  "completed": 5
}
```

### 重新生成单个场景图像

```bash
curl -X POST "http://localhost:8000/api/projects/{project_id}/chapters/1/images/3/regenerate" \
  -H "X-User-ID: kai" \
  -H "Content-Type: application/json" \
  -d '{
    "custom_prompt": "更多霓虹灯效果",
    "style_preset": "cyberpunk"
  }'
```

---

## 支持的画面风格

| 风格代码 | 说明 | 典型Prompt关键词 |
|----------|------|------------------|
| `realistic` | 写实摄影风格 | photorealistic, cinematic lighting, film grain |
| `illustration` | 精美插画风格 | digital illustration, vibrant colors, artstation |
| `cyberpunk` | 赛博朋克风格 | neon lights, futuristic city, holographic |
| `ink` | 中国水墨风格 | Chinese ink wash, brush strokes, minimalist |
| `cartoon` | 卡通动画风格 | cartoon style, vibrant colors, cute design |
| `chinese` | 中国风 | Chinese traditional, classical elements |
| `manga` | 日本漫画风格 | manga style, anime, cel shading |
| `oil_painting` | 油画风格 | oil painting, thick brush strokes, classical |
| `watercolor` | 水彩风格 | watercolor, soft edges, dreamy |
| `pixel` | 像素艺术风格 | pixel art, retro game aesthetic |

---

## 宽高比支持

| 比例 | 用途 | 实际尺寸示例 |
|------|------|--------------|
| `16:9` | 横屏视频 | 1344x768 |
| `9:16` | 竖屏短视频 | 768x1344 |
| `1:1` | 正方形 | 1024x1024 |
| `4:3` | 传统屏幕 | 1024x768 |
| `3:4` | 竖版 | 768x1024 |
| `21:9` | 电影宽屏 | 1680x720 |

---

## 数据库新增表

### scene_images（场景图像表）

```sql
CREATE TABLE scene_images (
    id TEXT PRIMARY KEY,
    chapter_id TEXT NOT NULL,
    scene_id INTEGER NOT NULL,
    image_prompt TEXT,
    negative_prompt TEXT,
    image_path TEXT,
    thumbnail_path TEXT,
    width INTEGER,
    height INTEGER,
    aspect_ratio TEXT,
    style_preset TEXT,
    model_used TEXT,
    generation_time_seconds REAL,
    status TEXT DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
);
```

### character_references（角色参考图表）

```sql
CREATE TABLE character_references (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    character_name TEXT NOT NULL,
    description TEXT,
    image_path TEXT,
    style_preset TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE (project_id, character_name)
);
```

---

## 配置项

`.env` 新增配置：

```env
# Phase 2: Image Generation
IMAGE_STORAGE_PATH=./storage/images
IMAGE_MAX_CONCURRENT=3
IMAGE_GENERATION_TIMEOUT=120
```

`app/config.py` 对应字段：

```python
# Phase 2: Image Storage
IMAGE_STORAGE_PATH: str = "./storage/images"

# Image Generation Settings
IMAGE_MAX_CONCURRENT: int = 3      # 最大并发生成数
IMAGE_GENERATION_TIMEOUT: int = 120  # 单张图片生成超时（秒）
```

---

## 依赖更新

```txt
# ===== Phase 2: Image Generation =====
# Image processing
Pillow>=10.0.0

# Async HTTP (for backup APIs if needed)
aiohttp>=3.9.0
```

---

## 测试

```bash
# 运行 Phase 2 图像生成测试
./venv/bin/python tests/test_image_generator.py
```

测试覆盖：
1. 单图生成 - 基础图像生成功能
2. 分镜Prompt生成 - 场景到prompt转换
3. 完整分镜图像生成 - 端到端流程
4. 存储服务 - 图像保存和读取

---

## 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Layer                                 │
│  ┌─────────────┐  ┌──────────────────┐  ┌───────────────────┐  │
│  │ chapters.py │  │ images.py        │  │ projects.py       │  │
│  │ (扩展)      │  │ (新增)           │  │ (Phase 1)         │  │
│  └──────┬──────┘  └────────┬─────────┘  └───────────────────┘  │
└─────────┼──────────────────┼────────────────────────────────────┘
          │                  │
          ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │ StoryboardService│  │ ImageGenerator   │  │ ImageStorage  │ │
│  │ (分镜决策)       │─▶│ (Gemini API)     │─▶│ (文件存储)    │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
│           │                     │                               │
│           ▼                     ▼                               │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ storyboard_      │  │ Character        │                    │
│  │ prompts.py       │  │ ConsistencyMgr   │                    │
│  │ (Prompt模板)     │  │ (角色一致性)     │                    │
│  └──────────────────┘  └──────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      External APIs                               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Gemini API                              │ │
│  │  gemini-2.5-flash-image (主) / gemini-3-pro-image (备)    │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 下一阶段计划 (Phase 3)

- [ ] TTS 音频合成（旁白朗读）
- [ ] Whisper 时间戳对齐
- [ ] 背景音乐选择
- [ ] 视频合成（图片 + 音频 → 视频）
- [ ] Ken Burns 效果（图片动态化）

---

## 参考资源

- [Google Gemini Image Generation](https://ai.google.dev/gemini-api/docs/image-generation)
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [Phase 1 文档](./PHASE1_COMPLETE.md)
