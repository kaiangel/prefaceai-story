# 序话Story - Phase 1 开发指令

## 项目概述

你正在开发一个名为"序话Story"的AI短视频/短剧生成应用。用户输入一句话创意，系统自动生成可发布的短剧视频。

**本阶段目标**：实现最小闭环——"用户输入idea → 生成短剧故事文本"，验证Gemini 3 Pro的故事生成质量。

---

## 技术栈

- **后端**: Python 3.11+ / FastAPI
- **数据库**: SQLite（MVP阶段，后续可迁移PostgreSQL）
- **ORM**: SQLAlchemy 2.0
- **故事生成**: Google Gemini 3 Pro API (`gemini-3-pro-preview`)
- **异步任务**: 暂用简单的后台线程，后续可迁移Celery

---

## 数据库设计

创建以下表结构：

```sql
-- 用户表（MVP简化版）
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 项目表（一个短剧=一个项目）
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,                    -- 项目标题（可由LLM根据idea生成）
    original_idea TEXT NOT NULL,            -- 用户原始输入的idea
    style_preset TEXT NOT NULL,             -- 画面风格：realistic/illustration/cyberpunk/ink/cartoon/chinese/manga等
    total_chapters INTEGER DEFAULT 1,       -- 总章节数
    chapter_duration_minutes INTEGER DEFAULT 3,  -- 每章时长（分钟）
    character_count INTEGER DEFAULT 2,      -- 角色数量
    language TEXT DEFAULT 'zh-CN',          -- 语言
    voice_preset TEXT,                      -- TTS音色ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 章节表
CREATE TABLE chapters (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    chapter_number INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',          -- pending/generating_story/generating_images/generating_audio/compositing/completed/failed
    full_script TEXT,                       -- 完整剧本/旁白文本
    summary TEXT,                           -- 章节摘要（供后续章节参考）
    characters_json TEXT,                   -- 角色状态快照 JSON
    scenes_json TEXT,                       -- 场景分镜列表 JSON
    storyboard_json TEXT,                   -- 分镜决策结果 JSON
    video_url TEXT,                         -- 生成的视频URL
    error_message TEXT,                     -- 失败时的错误信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- 生成任务表（用于异步状态追踪）
CREATE TABLE generation_jobs (
    id TEXT PRIMARY KEY,
    chapter_id TEXT NOT NULL,
    status TEXT DEFAULT 'queued',           -- queued/processing/completed/failed
    current_stage TEXT,                     -- story_generation/storyboard/image_generation/tts/whisper/composition
    progress INTEGER DEFAULT 0,             -- 0-100
    estimated_seconds INTEGER,              -- 预估剩余时间
    stage_message TEXT,                     -- 当前阶段描述，如"正在生成第3/8张图片…"
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id)
);
```

---

## Phase 1 核心功能

### 1. 项目结构

```
xuhua_story/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # 配置（API keys等）
│   ├── database.py             # 数据库连接
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── chapter.py
│   │   └── job.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── project.py          # Pydantic schemas
│   │   └── chapter.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── story_generator.py  # Gemini 3 Pro 故事生成
│   │   └── job_manager.py      # 任务状态管理
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py             # MVP简易认证
│   │   ├── projects.py         # 项目CRUD
│   │   └── chapters.py         # 章节生成
│   └── prompts/
│       └── story_generation.py # 故事生成prompt模板
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

### 2. 故事生成Prompt设计（核心）

在 `app/prompts/story_generation.py` 中实现：

```python
def build_story_generation_prompt(
    idea: str,
    style: str,
    chapter_number: int,
    total_chapters: int,
    duration_minutes: int,
    character_count: int,
    language: str,
    previous_summary: str | None = None,
    characters_json: str | None = None
) -> str:
    """
    构建故事生成的prompt
    
    关键要求：
    1. 生成的故事文本要适合TTS朗读（旁白/对白形式）
    2. 根据时长估算字数（中文约200字/分钟朗读速度）
    3. 故事要有明确的分镜提示（用于后续图像生成）
    4. 如果是续集章节，要衔接前文摘要
    """
    
    estimated_word_count = duration_minutes * 200  # 中文朗读速度
    
    # 风格映射为详细描述
    style_descriptions = {
        "realistic": "写实摄影风格，真实光影，电影质感",
        "illustration": "精美插画风格，色彩丰富，艺术感强",
        "cyberpunk": "赛博朋克风格，霓虹灯光，未来都市",
        "ink": "中国水墨风格，留白意境，传统美学",
        "cartoon": "卡通动画风格，Q版可爱，色彩明快",
        "chinese": "中国风，古典元素，传统配色",
        "manga": "日本漫画风格，分镜感强，情绪张力",
        "oil_painting": "油画风格，厚重笔触，古典美感",
        "watercolor": "水彩风格，透明轻盈，梦幻氛围",
        "pixel": "像素艺术风格，复古游戏感"
    }
    
    style_desc = style_descriptions.get(style, style)
    
    prompt = f"""你是一位专业的短视频编剧，擅长创作适合社交媒体传播的短剧内容。

## 创作任务

根据以下创意，创作一个短剧的第{chapter_number}章（共{total_chapters}章）。

**用户创意**: {idea}
**视觉风格**: {style_desc}
**角色数量**: {character_count}个主要角色
**目标时长**: {duration_minutes}分钟
**目标字数**: 约{estimated_word_count}字（旁白+对白总计）
**语言**: {language}

"""

    if previous_summary and chapter_number > 1:
        prompt += f"""
## 前情提要

{previous_summary}

## 已有角色

{characters_json if characters_json else "（根据前情提要中的角色继续）"}

请确保本章与前文剧情连贯，角色性格一致。

"""

    prompt += """
## 输出格式要求

请严格按照以下JSON格式输出：

```json
{
  "title": "本章标题",
  "summary": "本章内容摘要（100-150字，用于下一章参考）",
  "characters": [
    {
      "name": "角色名",
      "description": "外貌特征描述（用于图像生成保持一致性）",
      "personality": "性格特点"
    }
  ],
  "scenes": [
    {
      "scene_id": 1,
      "location": "场景地点",
      "time": "时间（如：夜晚、清晨）",
      "mood": "氛围（如：紧张、温馨）",
      "visual_description": "画面描述（用于图像生成prompt，要详细具体）",
      "narration": "这个场景的旁白或对白文本（这是会被TTS朗读的内容）",
      "duration_hint": "建议停留秒数"
    }
  ],
  "total_scenes": "场景总数",
  "word_count": "实际字数统计"
}
```

## 创作要点

1. **故事节奏**: 短视频观众注意力有限，开头3秒必须抓人，每个场景都要有信息增量
2. **视觉思维**: 每个scene的visual_description要具体到可以直接用于AI图像生成
3. **角色一致性**: characters中的外貌描述要详细且固定，便于后续所有场景保持一致
4. **旁白风格**: narration要适合朗读，语言流畅自然，避免书面语
5. **情感曲线**: 注意铺垫、高潮、转折的节奏设计
6. **分镜数量**: 根据时长合理分配，约每15-30秒一个场景

现在开始创作：
"""
    
    return prompt
```

### 3. Gemini 3 Pro API 调用

在 `app/services/story_generator.py` 中实现：

```python
import google.generativeai as genai
import json
from app.config import settings
from app.prompts.story_generation import build_story_generation_prompt

class StoryGenerator:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-3-pro-preview')
    
    async def generate_story(
        self,
        idea: str,
        style: str,
        chapter_number: int = 1,
        total_chapters: int = 1,
        duration_minutes: int = 3,
        character_count: int = 2,
        language: str = "zh-CN",
        previous_summary: str | None = None,
        characters_json: str | None = None
    ) -> dict:
        """
        调用Gemini 3 Pro生成故事
        
        Returns:
            解析后的故事JSON对象
        """
        prompt = build_story_generation_prompt(
            idea=idea,
            style=style,
            chapter_number=chapter_number,
            total_chapters=total_chapters,
            duration_minutes=duration_minutes,
            character_count=character_count,
            language=language,
            previous_summary=previous_summary,
            characters_json=characters_json
        )
        
        # Gemini 3 Pro 配置
        generation_config = {
            "temperature": 0.8,  # 创意任务适当提高
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json"  # 强制JSON输出
        }
        
        response = await self.model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        
        # 解析响应
        try:
            result = json.loads(response.text)
            return {
                "success": True,
                "data": result,
                "usage": {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count
                }
            }
        except json.JSONDecodeError as e:
            # 如果JSON解析失败，尝试提取```json```块
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response.text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
                return {"success": True, "data": result}
            
            return {
                "success": False,
                "error": f"JSON解析失败: {str(e)}",
                "raw_response": response.text
            }
```

### 4. API 端点设计

在 `app/api/projects.py` 中实现：

```python
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.story_generator import StoryGenerator
from app.services.job_manager import JobManager

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.post("/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    background_tasks: BackgroundTasks,
    user_id: str = Header(...)  # MVP: 从header获取user_id
):
    """
    创建新项目并开始生成第一章故事
    """
    # 1. 创建项目记录
    project_id = create_project_in_db(project, user_id)
    
    # 2. 创建第一章记录
    chapter_id = create_chapter_in_db(project_id, chapter_number=1)
    
    # 3. 创建生成任务
    job_id = create_job_in_db(chapter_id)
    
    # 4. 启动后台生成任务
    background_tasks.add_task(
        generate_story_task,
        job_id=job_id,
        chapter_id=chapter_id,
        project=project
    )
    
    return {
        "project_id": project_id,
        "chapter_id": chapter_id,
        "job_id": job_id,
        "status": "generating_story",
        "message": "故事生成已开始"
    }

@router.get("/{project_id}/chapters/{chapter_number}/status")
async def get_generation_status(project_id: str, chapter_number: int):
    """
    查询生成状态（供前端轮询）
    """
    job = get_latest_job_for_chapter(project_id, chapter_number)
    
    return {
        "status": job.status,
        "stage": job.current_stage,
        "progress": job.progress,
        "estimated_remaining_seconds": job.estimated_seconds,
        "message": job.stage_message
    }

@router.get("/{project_id}/chapters/{chapter_number}/story")
async def get_chapter_story(project_id: str, chapter_number: int):
    """
    获取已生成的故事内容
    """
    chapter = get_chapter(project_id, chapter_number)
    
    if chapter.status != "completed" and chapter.status != "generating_images":
        raise HTTPException(400, "故事尚未生成完成")
    
    return {
        "full_script": chapter.full_script,
        "scenes": json.loads(chapter.scenes_json),
        "characters": json.loads(chapter.characters_json),
        "summary": chapter.summary
    }
```

### 5. MVP认证（硬编码测试账号）

在 `app/api/auth.py` 中实现：

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])

# MVP测试账号
DEMO_USERS = {
    "demo001": {"name": "测试用户A", "password": "demo123"},
    "demo002": {"name": "测试用户B", "password": "demo456"},
    "kai": {"name": "Kai", "password": "xuhua2024"},
}

class LoginRequest(BaseModel):
    user_id: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    user_id: str
    name: str
    token: str  # MVP阶段就是user_id本身

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    user = DEMO_USERS.get(request.user_id)
    if not user or user["password"] != request.password:
        raise HTTPException(401, "用户名或密码错误")
    
    return {
        "success": True,
        "user_id": request.user_id,
        "name": user["name"],
        "token": request.user_id  # MVP简化
    }
```

---

## 配置文件

`.env.example`:

```env
# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Database
DATABASE_URL=sqlite:///./xuhua_story.db

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

---

## Phase 1 验收标准

1. **API可调用**: `POST /api/projects/` 能成功创建项目并触发故事生成
2. **故事质量**: Gemini 3 Pro 返回的故事JSON结构完整，包含title/summary/characters/scenes
3. **状态追踪**: `GET /api/projects/{id}/chapters/1/status` 能正确返回生成进度
4. **故事获取**: `GET /api/projects/{id}/chapters/1/story` 能获取完整故事内容
5. **错误处理**: API调用失败时有清晰的错误信息

---

## 开发顺序

1. 先创建项目结构和依赖文件
2. 实现数据库模型和初始化脚本
3. 实现 `story_generator.py`，先用简单脚本测试Gemini 3 Pro调用
4. 实现API端点
5. 编写简单的测试脚本验证全流程

---

## 注意事项

1. **Gemini 3 Pro API Key**: 需要在Google AI Studio申请，模型ID是 `gemini-3-pro-preview`
2. **JSON输出**: 使用 `response_mime_type: "application/json"` 强制JSON格式
3. **异步调用**: 使用 `generate_content_async` 避免阻塞
4. **Token计费**: Gemini 3 Pro 价格是 $2/M input, $12/M output（200k以内），注意监控用量
5. **故事长度**: 3分钟视频约600字旁白，prompt里要明确字数要求

---

## 下一阶段预告（Phase 2）

完成Phase 1后，下一步将实现：
- 分镜决策（LLM根据故事确定每个scene的图像prompt）
- Nano Banana Pro图像生成
- 火山引擎TTS音频合成

先把"idea → 故事"跑通，验证故事质量再继续。
