# 序话Story - Phase 2 开发指令：分镜与图像生成

## 阶段目标

在Phase 1"idea → 故事JSON"的基础上，实现"故事 → 分镜图像"的完整链路。

**核心交付**：
1. 分镜决策服务：将故事scenes转化为精确的图像生成prompt
2. 图像生成服务：调用Nano Banana Pro生成分镜图
3. 角色一致性控制：确保同一角色在不同场景中外貌一致
4. 图像存储管理：本地存储 + 未来OSS扩展预留

---

## ⚠️ 重要提醒：API文档查阅

**在编写任何API调用代码之前，必须先搜索并阅读最新的官方文档：**

### Nano Banana Pro (Gemini 3 Pro Image)

```
搜索关键词：
- "Nano Banana Pro API documentation"
- "Gemini 3 Pro Image API"
- "Google AI Studio image generation API"
- site:ai.google.dev image generation
```

**必读文档**：
- https://ai.google.dev/gemini-api/docs/image-generation
- https://blog.google/technology/developers/gemini-3-pro-image-developers/

**关键确认点**：
1. 当前可用的模型ID（可能是 `gemini-3-pro-image` 或其他）
2. API请求格式和参数
3. 多图参考（reference images）的传入方式
4. 输出图像的格式和分辨率选项
5. 价格和速率限制
6. Python SDK的正确调用方式

### 备选方案文档

如果Nano Banana Pro API受限或不可用，准备以下备选：
- OpenAI DALL-E 3 API
- Stability AI API
- Replicate API (Flux等模型)

---

## API Key 配置

在 `.env` 文件中添加以下配置：

```env
# ===== 已有配置 (Phase 1) =====
GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
DATABASE_URL=sqlite+aiosqlite:///./xuhua_story.db

# ===== Phase 2 新增 =====
# Nano Banana Pro 使用的是 Gemini API Key（同一个key）
# 如果需要单独的图像生成key，在此添加
GEMINI_IMAGE_API_KEY=your_gemini_image_api_key

# 备选图像生成服务（按需配置）
OPENAI_API_KEY=your_openai_api_key
STABILITY_API_KEY=your_stability_api_key

# 图像存储配置
IMAGE_STORAGE_PATH=./storage/images
# 未来OSS配置预留
# OSS_ENDPOINT=oss-cn-shanghai.aliyuncs.com
# OSS_ACCESS_KEY=your_oss_ak
# OSS_SECRET_KEY=your_oss_sk
# OSS_BUCKET=xuhua-story-assets
```

**提醒**：
- 首次运行前确保已配置有效的API Key
- Nano Banana Pro目前可能需要付费API访问权限
- 建议先在Google AI Studio网页端测试API Key是否有图像生成权限

---

## 技术架构

### 新增模块

```
app/
├── services/
│   ├── story_generator.py      # 已有
│   ├── job_manager.py          # 已有
│   ├── storyboard_service.py   # 新增：分镜决策
│   ├── image_generator.py      # 新增：图像生成
│   └── image_storage.py        # 新增：图像存储
├── api/
│   ├── chapters.py             # 扩展：添加图像相关端点
│   └── images.py               # 新增：图像管理API
├── prompts/
│   ├── story_generation.py     # 已有
│   └── storyboard_prompts.py   # 新增：分镜prompt模板
└── models/
    └── scene_image.py          # 新增：场景图像模型
```

### 数据库扩展

在现有数据库基础上添加 `scene_images` 表：

```sql
-- 场景图像表（一个场景可能多次重新生成）
CREATE TABLE scene_images (
    id TEXT PRIMARY KEY,
    chapter_id TEXT NOT NULL,
    scene_id INTEGER NOT NULL,
    image_prompt TEXT NOT NULL,          -- 生成时使用的完整prompt
    character_prompts TEXT,              -- 角色描述prompt（JSON）
    style_prompt TEXT,                   -- 风格prompt
    image_path TEXT NOT NULL,            -- 本地存储路径
    image_url TEXT,                      -- CDN/OSS URL（未来使用）
    thumbnail_path TEXT,                 -- 缩略图路径
    width INTEGER DEFAULT 1024,
    height INTEGER DEFAULT 1024,
    generation_model TEXT,               -- 使用的模型
    generation_params TEXT,              -- 生成参数（JSON）
    is_active BOOLEAN DEFAULT TRUE,      -- 是否为当前使用版本
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
);

CREATE INDEX idx_scene_images_chapter ON scene_images(chapter_id);
CREATE INDEX idx_scene_images_active ON scene_images(chapter_id, is_active);
```

---

## 模块实现详述

### 模块1：分镜决策服务 (storyboard_service.py)

**职责**：将故事的scenes[]和characters[]转化为可直接用于图像生成的精确prompt

**核心逻辑**：

```python
class StoryboardService:
    """
    分镜决策服务
    
    输入：故事的scenes[], characters[], style_preset
    输出：每个scene的完整图像生成prompt
    
    关键挑战：
    1. 角色描述一致性：同一角色在所有场景中的外貌描述必须一致
    2. 风格统一：所有场景的视觉风格必须统一
    3. Prompt工程：生成适合Nano Banana Pro的高质量prompt
    """
    
    async def generate_storyboard(
        self,
        scenes: list[dict],
        characters: list[dict],
        style_preset: str,
        project_config: dict
    ) -> list[dict]:
        """
        生成分镜决策
        
        Returns:
            [
                {
                    "scene_id": 1,
                    "image_prompt": "完整的图像生成prompt",
                    "character_prompts": {"角色名": "角色外貌描述"},
                    "style_prompt": "风格描述",
                    "negative_prompt": "负面提示词",
                    "aspect_ratio": "16:9",
                    "reference_images": []  # 参考图列表（用于角色一致性）
                }
            ]
        """
        pass
```

**分镜Prompt构建策略**：

```python
# prompts/storyboard_prompts.py

def build_image_prompt(
    scene: dict,
    characters: list[dict],
    style_preset: str,
    style_config: dict
) -> str:
    """
    构建完整的图像生成prompt
    
    Prompt结构：
    1. 主体描述（场景visual_description）
    2. 角色描述（从characters中提取，保持一致性）
    3. 环境描述（location, time, mood）
    4. 风格描述（从style_preset映射）
    5. 技术参数（分辨率、光影等）
    """
    
    # 风格映射
    style_prompts = {
        "realistic": "photorealistic, cinematic lighting, film grain, 8K UHD, detailed textures, professional photography",
        "cyberpunk": "cyberpunk style, neon lights, futuristic city, dark atmosphere, high contrast, blade runner aesthetic",
        "illustration": "digital illustration, vibrant colors, detailed artwork, artstation trending, concept art",
        "ink": "Chinese ink wash painting, minimalist, traditional aesthetics, brush strokes, rice paper texture",
        "cartoon": "cartoon style, cute characters, bright colors, simple shapes, animated movie quality",
        "chinese": "Chinese traditional style, classical elements, red and gold palette, ornate details",
        "manga": "manga style, Japanese anime, dramatic expressions, dynamic poses, cel shading",
        "oil_painting": "oil painting style, textured brushstrokes, classical art, rembrandt lighting",
        "watercolor": "watercolor style, soft edges, dreamy atmosphere, pastel colors, wet on wet technique",
        "pixel": "pixel art style, 16-bit retro game aesthetic, limited color palette"
    }
    
    # 提取场景中出现的角色
    scene_characters = extract_characters_from_scene(scene, characters)
    
    # 构建角色描述部分
    character_descriptions = []
    for char in scene_characters:
        char_desc = f"{char['name']}: {char['description']}"
        character_descriptions.append(char_desc)
    
    # 组装完整prompt
    prompt_parts = [
        scene['visual_description'],
        f"Setting: {scene['location']}, {scene['time']}, {scene['mood']} atmosphere",
    ]
    
    if character_descriptions:
        prompt_parts.append("Characters: " + "; ".join(character_descriptions))
    
    prompt_parts.append(f"Style: {style_prompts.get(style_preset, style_preset)}")
    prompt_parts.append("high quality, detailed, professional")
    
    return ", ".join(prompt_parts)


def build_negative_prompt(style_preset: str) -> str:
    """
    构建负面提示词，避免常见的AI生成问题
    """
    base_negative = [
        "blurry", "low quality", "distorted", "deformed",
        "bad anatomy", "extra limbs", "missing limbs",
        "mutated hands", "extra fingers", "fewer fingers",
        "text", "watermark", "signature", "logo",
        "cropped", "out of frame"
    ]
    
    # 针对不同风格的特定负面词
    style_specific = {
        "realistic": ["cartoon", "anime", "illustration", "painting"],
        "cartoon": ["realistic", "photorealistic", "photograph"],
        "manga": ["realistic", "3d render", "photograph"],
    }
    
    negatives = base_negative + style_specific.get(style_preset, [])
    return ", ".join(negatives)
```

---

### 模块2：图像生成服务 (image_generator.py)

**⚠️ 编码前必做**：搜索并阅读Nano Banana Pro最新API文档

**职责**：调用Nano Banana Pro API生成图像

**核心结构**：

```python
class ImageGenerator:
    """
    图像生成服务
    
    支持的后端：
    1. Nano Banana Pro (Gemini 3 Pro Image) - 主选
    2. DALL-E 3 - 备选
    3. Stability AI - 备选
    
    关键功能：
    1. 单图生成
    2. 批量生成（并行）
    3. 角色参考图支持（用于一致性）
    4. 自动重试和降级
    """
    
    def __init__(self):
        self.primary_backend = "nano_banana_pro"
        self.fallback_backends = ["dalle3", "stability"]
        # 初始化各后端客户端
        self._init_backends()
    
    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        aspect_ratio: str = "16:9",
        reference_images: list[str] = None,  # base64或URL
        style_preset: str = None,
        **kwargs
    ) -> dict:
        """
        生成单张图像
        
        Returns:
            {
                "success": True,
                "image_data": "base64编码的图像",
                "image_format": "png",
                "width": 1920,
                "height": 1080,
                "model_used": "nano_banana_pro",
                "generation_time_seconds": 12.5
            }
        """
        pass
    
    async def generate_batch(
        self,
        prompts: list[dict],
        max_concurrent: int = 3
    ) -> list[dict]:
        """
        批量生成图像（并行执行）
        
        Args:
            prompts: [{"scene_id": 1, "prompt": "...", ...}, ...]
            max_concurrent: 最大并发数（注意API速率限制）
        
        Returns:
            [{"scene_id": 1, "result": {...}}, ...]
        """
        pass


class NanoBananaProBackend:
    """
    Nano Banana Pro (Gemini 3 Pro Image) 后端
    
    ⚠️ 实现前请务必查阅最新API文档：
    - https://ai.google.dev/gemini-api/docs/image-generation
    - 确认模型ID、请求格式、参数选项
    
    关键特性（根据文档确认）：
    1. 支持多图参考输入（用于角色一致性）
    2. 支持迭代式对话生成
    3. 高保真文字渲染
    4. 最高4K分辨率
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        # TODO: 根据最新文档初始化客户端
        # 可能使用 google.generativeai 或 google-genai SDK
    
    async def generate(
        self,
        prompt: str,
        reference_images: list = None,
        **kwargs
    ) -> dict:
        """
        调用Nano Banana Pro生成图像
        
        ⚠️ 实现时注意：
        1. 确认正确的模型ID（搜索最新文档）
        2. 确认请求格式（可能与文本生成不同）
        3. 处理base64图像输出
        4. 实现速率限制和重试逻辑
        """
        # TODO: 根据最新API文档实现
        pass
```

**角色一致性策略**：

```python
class CharacterConsistencyManager:
    """
    角色一致性管理器
    
    策略：
    1. 首次生成：为每个角色生成"参考图"（角色立绘）
    2. 后续生成：将参考图作为reference_images传入
    3. Prompt强化：在每个场景的prompt中重复角色的固定描述
    
    Nano Banana Pro支持最多14张参考图，可以包含：
    - 角色参考图
    - 风格参考图
    - 场景参考图
    """
    
    async def get_character_references(
        self,
        project_id: str,
        characters: list[dict]
    ) -> dict:
        """
        获取或生成角色参考图
        
        Returns:
            {
                "角色名": {
                    "reference_image": "base64或URL",
                    "description": "角色描述"
                }
            }
        """
        pass
    
    async def generate_character_portrait(
        self,
        character: dict,
        style_preset: str
    ) -> str:
        """
        生成角色立绘（用作后续场景的参考）
        
        Prompt策略：
        - 半身像或全身像
        - 纯色背景
        - 正面或3/4侧面
        - 详细的服装和特征
        """
        portrait_prompt = f"""
        Character portrait of {character['name']}: {character['description']}.
        Half-body shot, neutral background, facing slightly left,
        detailed features, professional character design,
        {style_preset} style, high quality, detailed
        """
        # 调用图像生成
        pass
```

---

### 模块3：图像存储服务 (image_storage.py)

**职责**：管理生成图像的存储、缩略图生成、未来OSS扩展

```python
import os
import uuid
from PIL import Image
import base64
from io import BytesIO

class ImageStorageService:
    """
    图像存储服务
    
    存储结构：
    storage/
    └── images/
        └── {project_id}/
            └── {chapter_id}/
                ├── scene_001.png
                ├── scene_001_thumb.png
                ├── scene_002.png
                └── ...
    """
    
    def __init__(self, base_path: str = "./storage/images"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
    
    async def save_image(
        self,
        image_data: str,  # base64
        project_id: str,
        chapter_id: str,
        scene_id: int,
        format: str = "png"
    ) -> dict:
        """
        保存图像到本地
        
        Returns:
            {
                "image_path": "相对路径",
                "thumbnail_path": "缩略图路径",
                "full_path": "绝对路径",
                "width": 1920,
                "height": 1080
            }
        """
        # 创建目录
        dir_path = os.path.join(self.base_path, project_id, chapter_id)
        os.makedirs(dir_path, exist_ok=True)
        
        # 解码base64
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        
        # 保存原图
        filename = f"scene_{scene_id:03d}.{format}"
        image_path = os.path.join(dir_path, filename)
        image.save(image_path, format.upper())
        
        # 生成缩略图
        thumb_filename = f"scene_{scene_id:03d}_thumb.{format}"
        thumb_path = os.path.join(dir_path, thumb_filename)
        thumb = image.copy()
        thumb.thumbnail((400, 400))
        thumb.save(thumb_path, format.upper())
        
        return {
            "image_path": os.path.relpath(image_path, self.base_path),
            "thumbnail_path": os.path.relpath(thumb_path, self.base_path),
            "full_path": os.path.abspath(image_path),
            "width": image.width,
            "height": image.height
        }
    
    def get_image_url(self, image_path: str) -> str:
        """
        获取图像访问URL
        
        当前：返回本地静态文件路径
        未来：返回OSS/CDN URL
        """
        # MVP阶段返回本地路径
        return f"/static/images/{image_path}"
```

---

### 模块4：API端点扩展

**扩展 chapters.py**：

```python
# 添加到现有的chapters路由

@router.post("/{project_id}/chapters/{chapter_number}/generate-images")
async def generate_chapter_images(
    project_id: str,
    chapter_number: int,
    user_id: str = Header(..., alias="X-User-ID"),
    background_tasks: BackgroundTasks
):
    """
    为章节生成所有分镜图像
    
    前置条件：章节故事已生成完成（status >= story_ready）
    """
    # 1. 验证章节状态
    # 2. 创建图像生成任务
    # 3. 启动后台生成
    pass

@router.get("/{project_id}/chapters/{chapter_number}/images")
async def get_chapter_images(
    project_id: str,
    chapter_number: int,
    user_id: str = Header(..., alias="X-User-ID")
):
    """
    获取章节的所有分镜图像
    
    Returns:
        {
            "images": [
                {
                    "scene_id": 1,
                    "image_url": "/static/images/...",
                    "thumbnail_url": "/static/images/..._thumb",
                    "prompt": "生成时使用的prompt",
                    "status": "completed"
                }
            ],
            "total": 8,
            "completed": 8
        }
    """
    pass

@router.post("/{project_id}/chapters/{chapter_number}/images/{scene_id}/regenerate")
async def regenerate_scene_image(
    project_id: str,
    chapter_number: int,
    scene_id: int,
    user_id: str = Header(..., alias="X-User-ID"),
    prompt_override: str = None  # 可选：用户自定义prompt
):
    """
    重新生成单个场景的图像
    
    用于用户对某张图不满意时重新生成
    """
    pass
```

**新增 images.py**：

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/images", tags=["images"])

@router.get("/{project_id}/{chapter_id}/{filename}")
async def serve_image(project_id: str, chapter_id: str, filename: str):
    """
    提供图像文件访问
    
    实际路径：storage/images/{project_id}/{chapter_id}/{filename}
    """
    pass
```

---

## 状态机扩展

更新章节状态流转，添加图像生成阶段：

```
pending
    │
    ▼
generating_story
    │
    ▼
story_ready  ◄──────────────┐
    │                       │
    ▼ (用户确认)            │ (重新生成故事)
confirmed                   │
    │                       │
    ▼                       │
generating_storyboard ──────┘
    │
    ▼
storyboard_ready
    │
    ▼
generating_images ──────────┐
    │                       │ (部分失败可重试)
    ▼                       │
images_ready ◄──────────────┘
    │
    ▼ (Phase 3: 音频)
generating_audio
    ...
```

---

## 生成任务流程

```python
async def generate_images_task(job_id: str, chapter_id: str):
    """
    图像生成后台任务
    
    步骤：
    1. 加载章节数据（scenes, characters, style）
    2. 生成分镜决策（storyboard）
    3. 生成角色参考图（如果不存在）
    4. 并行生成各场景图像
    5. 保存图像和更新数据库
    6. 更新任务状态
    """
    try:
        # 更新状态
        await update_job_status(job_id, "processing", "generating_storyboard", 10)
        
        # 1. 加载数据
        chapter = await get_chapter(chapter_id)
        scenes = json.loads(chapter.scenes_json)
        characters = json.loads(chapter.characters_json)
        project = await get_project(chapter.project_id)
        
        # 2. 生成分镜
        storyboard_service = StoryboardService()
        storyboard = await storyboard_service.generate_storyboard(
            scenes=scenes,
            characters=characters,
            style_preset=project.style_preset,
            project_config={...}
        )
        
        await update_job_status(job_id, "processing", "generating_images", 20)
        
        # 3. 获取角色参考图
        consistency_manager = CharacterConsistencyManager()
        char_references = await consistency_manager.get_character_references(
            project_id=project.id,
            characters=characters
        )
        
        # 4. 并行生成图像
        image_generator = ImageGenerator()
        total_scenes = len(storyboard)
        
        for i, scene_board in enumerate(storyboard):
            progress = 20 + int((i / total_scenes) * 70)
            await update_job_status(
                job_id, "processing", "generating_images", progress,
                f"正在生成第 {i+1}/{total_scenes} 张图片..."
            )
            
            result = await image_generator.generate_image(
                prompt=scene_board["image_prompt"],
                negative_prompt=scene_board.get("negative_prompt", ""),
                reference_images=list(char_references.values()),
                style_preset=project.style_preset
            )
            
            if result["success"]:
                # 保存图像
                storage = ImageStorageService()
                saved = await storage.save_image(
                    image_data=result["image_data"],
                    project_id=project.id,
                    chapter_id=chapter.id,
                    scene_id=scene_board["scene_id"]
                )
                
                # 保存到数据库
                await save_scene_image(
                    chapter_id=chapter.id,
                    scene_id=scene_board["scene_id"],
                    image_prompt=scene_board["image_prompt"],
                    image_path=saved["image_path"],
                    ...
                )
        
        # 5. 完成
        await update_job_status(job_id, "completed", "images_ready", 100, "图像生成完成！")
        await update_chapter_status(chapter_id, "images_ready")
        
    except Exception as e:
        await update_job_status(job_id, "failed", error_message=str(e))
        raise
```

---

## 依赖更新

在 `requirements.txt` 中添加：

```txt
# ===== Phase 2 新增 =====
# 图像处理
Pillow>=10.0.0

# 异步HTTP（如果需要直接调用REST API）
aiohttp>=3.9.0

# OpenAI（备选图像生成）
openai>=1.0.0
```

---

## Phase 2 验收标准

| 标准 | 说明 |
|------|------|
| 分镜生成 | 给定故事JSON，能生成每个scene的图像prompt |
| 图像生成 | 调用Nano Banana Pro成功生成图像 |
| 角色一致性 | 同一角色在不同场景中外貌基本一致 |
| 图像存储 | 图像保存到本地，可通过API访问 |
| 状态追踪 | 图像生成进度可查询 |
| 重新生成 | 单个场景图像可重新生成 |
| 错误处理 | 生成失败有清晰错误信息，支持重试 |

---

## 开发顺序

1. **先搜索API文档**：查阅Nano Banana Pro最新文档，确认可用性
2. **实现图像存储服务**：最简单，无外部依赖
3. **实现图像生成服务**：核心功能，先跑通单图生成
4. **实现分镜决策服务**：prompt工程
5. **实现角色一致性**：参考图管理
6. **扩展API端点**：对外暴露功能
7. **集成测试**：完整流程测试

---

## 测试脚本示例

```python
# tests/test_image_generator.py

import asyncio
from app.services.image_generator import ImageGenerator

async def test_single_image():
    """测试单图生成"""
    generator = ImageGenerator()
    
    result = await generator.generate_image(
        prompt="A cyberpunk programmer working late at night, neon lights, futuristic office, detailed, 8K",
        negative_prompt="blurry, low quality, distorted",
        aspect_ratio="16:9"
    )
    
    print(f"Success: {result['success']}")
    print(f"Model: {result.get('model_used')}")
    print(f"Time: {result.get('generation_time_seconds')}s")
    
    if result['success']:
        # 保存测试图像
        import base64
        with open("test_output.png", "wb") as f:
            f.write(base64.b64decode(result['image_data']))
        print("Image saved to test_output.png")

if __name__ == "__main__":
    asyncio.run(test_single_image())
```

---

## 注意事项

1. **API文档优先**：编码前必须查阅Nano Banana Pro最新文档
2. **速率限制**：注意API调用频率，实现适当的延迟和重试
3. **成本控制**：图像生成有成本，测试时注意用量
4. **并发控制**：批量生成时控制并发数，避免触发限制
5. **错误处理**：API可能不稳定，实现完善的重试和降级机制
6. **存储清理**：实现过期图像清理机制（可选）

---

## 参考资源

- [Nano Banana Pro官方文档](https://ai.google.dev/gemini-api/docs/image-generation)
- [Gemini 3 Pro Image开发博客](https://blog.google/technology/developers/gemini-3-pro-image-developers/)
- [Google AI Studio](https://aistudio.google.com/) - 在线测试
- [Pillow文档](https://pillow.readthedocs.io/)
