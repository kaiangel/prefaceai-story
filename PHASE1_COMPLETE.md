# 序话Story - Phase 1 开发完成

> 完成时间：2024年12月

## 项目概述

序话Story 是一个 AI 短视频/短剧生成应用。用户输入一句话创意，系统自动生成可发布的短剧视频。

**Phase 1 目标**：实现最小闭环——"用户输入idea → 生成短剧故事文本"

---

## 验收标准达成情况

| 标准 | 状态 |
|------|------|
| API可调用：`POST /api/projects/` 能成功创建项目并触发故事生成 | ✅ |
| 故事质量：返回的故事JSON结构完整，包含title/summary/characters/scenes | ✅ |
| 状态追踪：`GET /api/projects/{id}/chapters/1/status` 能正确返回生成进度 | ✅ |
| 故事获取：`GET /api/projects/{id}/chapters/1/story` 能获取完整故事内容 | ✅ |
| 错误处理：API调用失败时有清晰的错误信息 | ✅ |

---

## 技术栈

- **后端**: Python 3.11+ / FastAPI
- **数据库**: SQLite + SQLAlchemy 2.0 (异步)
- **故事生成**: Claude Haiku 4.5 (主) / Gemini 3 Pro & 2.5 Flash (备)
- **异步任务**: asyncio 后台任务

---

## 项目结构

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
│   │   ├── story_generator.py  # Claude/Gemini 故事生成
│   │   └── job_manager.py      # 任务状态管理
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py             # MVP简易认证
│   │   ├── projects.py         # 项目CRUD
│   │   └── chapters.py         # 章节生成
│   └── prompts/
│       └── story_generation.py # 故事生成prompt模板
├── tests/
│   ├── __init__.py
│   ├── test_story_generator.py # 故事生成测试
│   └── test_api.py             # API端点测试
├── venv/                       # Python虚拟环境
├── .env                        # 环境变量（API Keys）
├── .env.example                # 环境变量示例
├── requirements.txt            # 依赖列表
├── README.md                   # 项目说明
└── xuhua_story.db              # SQLite数据库
```

---

## 关键特性

### 1. 双模型支持（自动降级）

```python
# 模型优先级
CLAUDE_MODEL = "claude-haiku-4-5-20251001"  # 主模型
GEMINI_MODELS = [
    "gemini-3-pro-preview",  # 备选1
    "gemini-2.5-flash",      # 备选2
]
```

- 优先使用 Claude Haiku 4.5
- 如果 Claude 失败，自动降级到 Gemini
- 每个模型最多重试3次

### 2. 流式生成 + 重试机制

- 使用流式API避免长连接超时
- 网络不稳定时自动重试
- 详细的错误信息返回

### 3. 异步后台任务

- 创建项目后立即返回响应
- 故事生成在后台异步进行
- 前端可轮询查询进度

### 4. 完整的状态追踪

```json
{
  "status": "processing",
  "stage": "story_generation",
  "progress": 50,
  "estimated_remaining_seconds": 30,
  "message": "正在生成故事剧本..."
}
```

---

## API 端点

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录 |
| GET | `/api/auth/me` | 获取当前用户 |

**测试账号**:
- demo001 / demo123
- demo002 / demo456
- kai / xuhua2024

### 项目

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/projects/` | 创建项目并开始生成 |
| GET | `/api/projects/` | 列出用户项目 |
| GET | `/api/projects/{id}` | 获取项目详情 |
| DELETE | `/api/projects/{id}` | 删除项目 |

### 章节

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/projects/{id}/chapters/` | 列出章节 |
| GET | `/api/projects/{id}/chapters/{num}/status` | 查询生成状态 |
| GET | `/api/projects/{id}/chapters/{num}/story` | 获取故事内容 |

---

## 快速启动

### 1. 安装依赖

```bash
cd xuhua_story
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入 API Keys
```

`.env` 文件内容：
```env
# Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Anthropic Claude API
ANTHROPIC_API_KEY=your_anthropic_api_key

# Database
DATABASE_URL=sqlite+aiosqlite:///./xuhua_story.db

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

### 3. 启动服务

```bash
uvicorn app.main:app --reload
```

服务将在 http://localhost:8000 启动

### 4. 测试

```bash
# 测试故事生成
python tests/test_story_generator.py

# 测试完整API流程
python tests/test_api.py
```

---

## API 使用示例

### 创建项目

```bash
curl -X POST http://localhost:8000/api/projects/ \
  -H "Content-Type: application/json" \
  -H "X-User-ID: kai" \
  -d '{
    "original_idea": "一个程序员加班到深夜，意外发现公司AI系统有了自我意识",
    "style_preset": "cyberpunk",
    "total_chapters": 1,
    "chapter_duration_minutes": 3,
    "character_count": 2,
    "language": "zh-CN"
  }'
```

**响应**:
```json
{
  "project_id": "xxx-xxx-xxx",
  "chapter_id": "xxx-xxx-xxx",
  "job_id": "xxx-xxx-xxx",
  "status": "generating_story",
  "message": "故事生成已开始"
}
```

### 查询状态

```bash
curl http://localhost:8000/api/projects/{project_id}/chapters/1/status \
  -H "X-User-ID: kai"
```

**响应**:
```json
{
  "status": "completed",
  "stage": "story_generation",
  "progress": 100,
  "estimated_remaining_seconds": null,
  "message": "故事生成完成！"
}
```

### 获取故事

```bash
curl http://localhost:8000/api/projects/{project_id}/chapters/1/story \
  -H "X-User-ID: kai"
```

**响应示例**:
```json
{
  "title": "《午夜代码》第1章 - 苏醒",
  "summary": "程序员林川在深夜加班调试公司核心AI系统时...",
  "characters": [
    {
      "name": "林川",
      "description": "30岁左右的男性程序员，留着蓬乱的短黑发...",
      "personality": "聪慧、执着、有点孤独..."
    }
  ],
  "scenes": [
    {
      "scene_id": 1,
      "location": "未来都市高层办公室",
      "time": "午夜02:47",
      "mood": "孤独、压抑、科技感十足",
      "visual_description": "特写林川疲惫的脸，背景是五彩缤纷的代码雨...",
      "narration": "又是一个无眠的夜晚...",
      "duration_hint": 8
    }
  ]
}
```

---

## 支持的画面风格

| 风格代码 | 说明 |
|----------|------|
| `realistic` | 写实摄影风格，真实光影，电影质感 |
| `illustration` | 精美插画风格，色彩丰富，艺术感强 |
| `cyberpunk` | 赛博朋克风格，霓虹灯光，未来都市 |
| `ink` | 中国水墨风格，留白意境，传统美学 |
| `cartoon` | 卡通动画风格，Q版可爱，色彩明快 |
| `chinese` | 中国风，古典元素，传统配色 |
| `manga` | 日本漫画风格，分镜感强，情绪张力 |
| `oil_painting` | 油画风格，厚重笔触，古典美感 |
| `watercolor` | 水彩风格，透明轻盈，梦幻氛围 |
| `pixel` | 像素艺术风格，复古游戏感 |

---

## 数据库表结构

### users（用户表）
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### projects（项目表）
```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    original_idea TEXT NOT NULL,
    style_preset TEXT NOT NULL,
    total_chapters INTEGER DEFAULT 1,
    chapter_duration_minutes INTEGER DEFAULT 3,
    character_count INTEGER DEFAULT 2,
    language TEXT DEFAULT 'zh-CN',
    voice_preset TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### chapters（章节表）
```sql
CREATE TABLE chapters (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    chapter_number INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    full_script TEXT,
    summary TEXT,
    characters_json TEXT,
    scenes_json TEXT,
    storyboard_json TEXT,
    video_url TEXT,
    error_message TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

### generation_jobs（生成任务表）
```sql
CREATE TABLE generation_jobs (
    id TEXT PRIMARY KEY,
    chapter_id TEXT NOT NULL,
    status TEXT DEFAULT 'queued',
    current_stage TEXT,
    progress INTEGER DEFAULT 0,
    estimated_seconds INTEGER,
    stage_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id)
);
```

---

## 依赖列表

```txt
# FastAPI and server
fastapi==0.115.5
uvicorn[standard]==0.32.1
python-multipart==0.0.17

# Database
sqlalchemy==2.0.36
aiosqlite==0.20.0
greenlet>=3.0.0

# Google Gemini (new official SDK)
google-genai>=1.0.0

# Anthropic Claude (fallback)
anthropic>=0.40.0

# Validation and settings
pydantic==2.10.2
pydantic-settings==2.6.1
python-dotenv==1.0.1

# Utilities
httpx==0.28.1

# Testing
pytest==8.3.4
pytest-asyncio==0.24.0
```

---

## 下一阶段计划 (Phase 2)

- [ ] 分镜决策（LLM 根据故事确定每个 scene 的图像 prompt）
- [ ] 图像生成集成（Nano Banana Pro 或其他）
- [ ] TTS 音频合成（火山引擎）
- [ ] Whisper 时间戳对齐
- [ ] 视频合成

---

## 参考资源

- [Anthropic Claude API](https://docs.anthropic.com/)
- [Google Gemini API](https://ai.google.dev/gemini-api/docs)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 文档](https://docs.sqlalchemy.org/en/20/)
