# 序话Story - AI短视频/短剧生成应用

> Phase 1: 故事生成 MVP

## 项目概述

序话Story 是一个 AI 短视频/短剧生成应用。用户输入一句话创意，系统自动生成可发布的短剧视频。

**当前阶段目标**：实现最小闭环——"用户输入idea → 生成短剧故事文本"

## 技术栈

- **后端**: Python 3.11+ / FastAPI
- **数据库**: SQLite + SQLAlchemy 2.0
- **故事生成**: Google Gemini API
- **异步任务**: asyncio 后台任务

## 快速开始

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
# 编辑 .env 文件，填入你的 Gemini API Key
```

### 3. 启动服务

```bash
python -m app.main
# 或
uvicorn app.main:app --reload
```

服务将在 http://localhost:8000 启动

### 4. 测试 API

```bash
# 测试故事生成（需要配置 API Key）
python tests/test_story_generator.py

# 测试完整 API 流程（需要先启动服务）
python tests/test_api.py
```

## API 端点

### 认证

- `POST /api/auth/login` - 登录（MVP 测试账号）
  - demo001 / demo123
  - demo002 / demo456
  - kai / xuhua2024

### 项目

- `POST /api/projects/` - 创建项目并开始生成
- `GET /api/projects/` - 列出用户项目
- `GET /api/projects/{id}` - 获取项目详情
- `DELETE /api/projects/{id}` - 删除项目

### 章节

- `GET /api/projects/{id}/chapters/` - 列出章节
- `GET /api/projects/{id}/chapters/{num}/status` - 查询生成状态
- `GET /api/projects/{id}/chapters/{num}/story` - 获取故事内容

## 创建项目示例

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

## 支持的画面风格

- `realistic` - 写实摄影风格
- `illustration` - 精美插画风格
- `cyberpunk` - 赛博朋克风格
- `ink` - 中国水墨风格
- `cartoon` - 卡通动画风格
- `chinese` - 中国风
- `manga` - 日本漫画风格
- `oil_painting` - 油画风格
- `watercolor` - 水彩风格
- `pixel` - 像素艺术风格

## 项目结构

```
xuhua_story/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # 配置
│   ├── database.py             # 数据库连接
│   ├── models/                 # SQLAlchemy 模型
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # 业务逻辑
│   ├── api/                    # API 路由
│   └── prompts/                # Prompt 模板
├── tests/
├── requirements.txt
└── README.md
```

## 下一阶段计划 (Phase 2)

- [ ] 分镜决策（LLM 根据故事确定每个 scene 的图像 prompt）
- [ ] 图像生成集成
- [ ] TTS 音频合成
- [ ] 视频合成
