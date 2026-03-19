# 序话Story - 系统架构规划文档

> 版本: 1.0  
> 日期: 2024年12月  
> 作者: Kai / Claude  

---

## 一、项目概述

### 1.1 产品定位

序话Story是一个AI驱动的短视频/短剧生成引擎。用户输入一句话创意，系统自动完成故事编剧、分镜设计、图像生成、语音合成、音画对齐、视频合成全流程，输出可直接发布到抖音、视频号、小红书等平台的成片。

### 1.2 核心技术挑战

1. **故事质量**: LLM生成的剧本需具备叙事张力和分镜可执行性
2. **人物一致性**: 跨场景的角色外貌必须保持稳定
3. **音画同步**: 旁白时间轴与图像停留时长的精确对齐（误差≤80ms）
4. **章节连续性**: 多章节剧情需保持上下文连贯

### 1.3 目标用户

- 短视频创作者（无技术背景）
- 自媒体运营者
- 内容营销团队
- 教育/培训内容制作者

---

## 二、系统架构总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 客户端层                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Web App   │  │ Mobile H5  │  │   微信小程序  │  │  企业微信Bot │         │
│  │  (Next.js)  │  │  (响应式)   │  │   (可选)     │  │   (可选)    │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                │                │
│         └────────────────┴────────────────┴────────────────┘                │
│                                    │                                        │
│                                    ▼                                        │
│                          ┌─────────────────┐                                │
│                          │   API Gateway   │                                │
│                          │  (Nginx/Traefik)│                                │
│                          └────────┬────────┘                                │
└───────────────────────────────────┼─────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼─────────────────────────────────────────┐
│                                 服务层                                       │
│                                    │                                        │
│    ┌───────────────────────────────┴───────────────────────────────┐        │
│    │                     FastAPI 主服务                              │        │
│    │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │        │
│    │  │ Auth API │ │Project API│ │Chapter API│ │ Job API  │          │        │
│    │  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │        │
│    └───────────────────────────────┬───────────────────────────────┘        │
│                                    │                                        │
│    ┌───────────────────────────────┴───────────────────────────────┐        │
│    │                     Celery Worker 集群                         │        │
│    │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐  │        │
│    │  │故事生成任务 │ │图像生成任务 │ │音频合成任务 │ │视频合成任务 │  │        │
│    │  └────────────┘ └────────────┘ └────────────┘ └────────────┘  │        │
│    └───────────────────────────────────────────────────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼─────────────────────────────────────────┐
│                               外部服务层                                     │
│                                    │                                        │
│    ┌──────────────┬────────────────┼────────────────┬──────────────┐        │
│    ▼              ▼                ▼                ▼              ▼        │
│ ┌──────┐    ┌──────────┐    ┌───────────┐    ┌──────────┐    ┌─────────┐   │
│ │Gemini│    │Nano Banana│   │火山引擎TTS │    │  Whisper │    │ FFmpeg  │   │
│ │3 Pro │    │   Pro     │   │  (豆包)    │    │  (OpenAI)│    │ (本地)  │   │
│ └──────┘    └──────────┘    └───────────┘    └──────────┘    └─────────┘   │
│  故事生成      图像生成         语音合成         时间戳提取       视频合成     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼─────────────────────────────────────────┐
│                                数据层                                        │
│                                    │                                        │
│    ┌──────────────┬────────────────┴────────────────┬──────────────┐        │
│    ▼              ▼                                 ▼              ▼        │
│ ┌──────┐    ┌──────────┐                      ┌──────────┐    ┌─────────┐   │
│ │ Redis│    │PostgreSQL│                      │ 对象存储  │    │ 文件系统│   │
│ │      │    │          │                      │(OSS/S3)  │    │ (本地)  │   │
│ └──────┘    └──────────┘                      └──────────┘    └─────────┘   │
│ 任务队列      业务数据                           媒体资产         临时文件     │
│ 缓存         用户/项目/章节                     图片/音频/视频                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 三、技术选型

### 3.1 后端

| 组件 | 选型 | 论证 |
|------|------|------|
| **Web框架** | FastAPI | 异步原生、自动OpenAPI文档、Pydantic集成、Python生态AI库支持最佳 |
| **任务队列** | Celery + Redis | Python生态成熟方案，支持任务重试/优先级/结果存储 |
| **ORM** | SQLAlchemy 2.0 | 异步支持、类型提示友好、迁移工具成熟(Alembic) |
| **数据库** | SQLite(开发) / PostgreSQL(生产) | SQLite零配置便于开发，PostgreSQL支持并发和JSON操作 |
| **缓存** | Redis | 任务队列复用、Session存储、热数据缓存 |

### 3.2 前端

| 组件 | 选型 | 论证 |
|------|------|------|
| **框架** | Next.js 14 (App Router) | React生态、SSR/SSG灵活、API Routes可做轻量BFF |
| **状态管理** | Zustand | 轻量、无样板代码、TypeScript友好 |
| **UI组件** | shadcn/ui + Tailwind | 可定制、不臃肿、设计感好 |
| **视频播放** | Video.js | 成熟稳定、插件丰富 |
| **请求** | TanStack Query | 自动缓存、轮询支持、乐观更新 |

### 3.3 AI服务

| 能力 | 服务商 | 模型/产品 | 用途 |
|------|--------|----------|------|
| **故事生成** | Google | Gemini 3 Pro | idea→剧本、分镜决策 |
| **图像生成** | Google | Nano Banana Pro | 分镜图像、角色一致性 |
| **图文匹配** | Google | Gemini 2.5 Flash | 图片与音频段落的智能匹配 |
| **语音合成** | 火山引擎 | 豆包TTS | 中英文多音色旁白 |
| **时间戳提取** | OpenAI | Whisper API | 音频转文字+word级时间戳 |

### 3.4 基础设施

> **负责人**: Ben（合伙人，CTO 级别）— 数据库/API 架构/基础设施由 Ben 团队维护

| 组件 | 选型 | 论证 |
|------|------|------|
| **视频处理** | FFmpeg + MoviePy | 行业标准、Python绑定成熟 |
| **对象存储** | 阿里云OSS / AWS S3 | 媒体文件存储、CDN加速 |
| **部署** | Docker + Docker Compose | 环境一致性、快速部署 |
| **反向代理** | Nginx / Traefik | 负载均衡、SSL终止 |

---

## 四、模块划分

### 4.1 模块依赖图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户请求入口                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  M1: 项目管理模块                                                │
│  - 创建/查询/删除项目                                            │
│  - 管理项目配置（风格/角色数/章节数/时长/音色）                    │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  M2: 故事生成模块                                                │
│  - 调用Gemini 3 Pro生成剧本                                      │
│  - 输出: title, summary, characters[], scenes[]                 │
│  - 支持章节续写（传入前章summary和characters）                    │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  M3: 分镜决策模块                                                │
│  - 根据scenes[]生成图像prompt                                    │
│  - 确保角色外貌描述一致性                                        │
│  - 输出: image_prompts[]                                        │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  M4: 图像生成模块                                                │
│  - 调用Nano Banana Pro生成分镜图                                 │
│  - 支持多图参考（角色参考图）保持一致性                           │
│  - 图像压缩和存储                                                │
│  - 输出: image_urls[]                                           │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  M5: 音频合成模块                                                │
│  - 调用火山引擎TTS生成旁白音频                                   │
│  - 支持多音色、情感控制                                          │
│  - 输出: audio_url, audio_duration                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  M6: 音画对齐模块                                                │
│  - 调用Whisper获取音频时间戳                                     │
│  - 调用Gemini 2.5 Flash匹配图片与音频段落                        │
│  - 输出: timeline_mapping[{image, start, end}]                  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  M7: 视频合成模块                                                │
│  - FFmpeg合成图片+音频                                           │
│  - Ken Burns效果（平移/缩放）                                    │
│  - 字幕轨道渲染                                                  │
│  - BGM混音（可选）                                               │
│  - 输出: video_url                                              │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 模块职责详述

| 模块 | 输入 | 输出 | 依赖服务 |
|------|------|------|----------|
| M1 项目管理 | 用户配置 | project_id, chapter_id | PostgreSQL |
| M2 故事生成 | idea, 配置, 前章摘要 | 剧本JSON | Gemini 3 Pro |
| M3 分镜决策 | scenes[], characters[] | image_prompts[] | Gemini 3 Pro |
| M4 图像生成 | image_prompts[] | image_urls[] | Nano Banana Pro, OSS |
| M5 音频合成 | narration_text, voice_id | audio_url | 火山引擎TTS |
| M6 音画对齐 | audio_url, images[] | timeline[] | Whisper, Gemini 2.5 Flash |
| M7 视频合成 | timeline[], audio, images | video_url | FFmpeg, MoviePy |

---

## 五、数据流设计

### 5.1 主流程数据流

```
用户输入
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. 创建项目                                                      │
│    Input:  { idea, style, chapters, duration, voice }           │
│    Output: { project_id }                                       │
│    Store:  projects 表                                          │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. 故事生成 (Celery Task)                                        │
│    Input:  { project_id, chapter_number, prev_summary? }        │
│    LLM:    Gemini 3 Pro                                         │
│    Output: { title, summary, characters[], scenes[] }           │
│    Store:  chapters 表 (full_script, summary, characters_json,  │
│            scenes_json)                                         │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. 用户确认/编辑故事                                             │
│    前端展示故事内容，用户可编辑后确认                             │
│    Update: chapters 表                                          │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. 分镜决策 (Celery Task)                                        │
│    Input:  { scenes[], characters[] }                           │
│    LLM:    Gemini 3 Pro                                         │
│    Output: { storyboard[{ scene_id, image_prompt }] }           │
│    Store:  chapters 表 (storyboard_json)                        │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. 图像生成 (Celery Task, 可并行)                                │
│    Input:  { image_prompts[], character_refs[]? }               │
│    API:    Nano Banana Pro                                      │
│    Output: { images[{ scene_id, url, thumbnail }] }             │
│    Store:  scene_images 表, OSS                                 │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. 音频合成 (Celery Task)                                        │
│    Input:  { narration_text, voice_id, language }               │
│    API:    火山引擎 TTS                                          │
│    Output: { audio_url, duration_seconds }                      │
│    Store:  chapters 表 (audio_url), OSS                         │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. 音画对齐 (Celery Task)                                        │
│    Input:  { audio_url, images[], scenes[] }                    │
│    API:    Whisper (时间戳) + Gemini 2.5 Flash (匹配)            │
│    Output: { timeline[{ image_url, start_sec, end_sec }] }      │
│    Store:  chapters 表 (timeline_json)                          │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. 视频合成 (Celery Task)                                        │
│    Input:  { timeline[], audio_url, subtitle_text?, bgm? }      │
│    Tool:   FFmpeg + MoviePy                                     │
│    Output: { video_url, thumbnail_url }                         │
│    Store:  chapters 表 (video_url), OSS                         │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
用户下载/分享视频
```

### 5.2 状态机设计

章节生成状态流转：

```
pending
    │
    ▼ (触发生成)
generating_story ──────────────┐
    │                          │ (失败)
    ▼ (成功)                   ▼
story_ready ◄─────────── failed
    │
    ▼ (用户确认)
confirmed
    │
    ▼ (触发分镜)
generating_storyboard
    │
    ▼
generating_images
    │
    ▼
generating_audio
    │
    ▼
aligning
    │
    ▼
compositing
    │
    ▼
completed
```

---

## 六、API设计全景

> **负责人**: Ben（合伙人，CTO 级别）— 数据库/API 架构/基础设施由 Ben 团队维护

### 6.1 API端点清单

```
认证模块
├── POST   /api/auth/login              # 登录
├── POST   /api/auth/logout             # 登出
└── GET    /api/auth/me                 # 当前用户信息

项目模块
├── POST   /api/projects                # 创建项目
├── GET    /api/projects                # 项目列表
├── GET    /api/projects/:id            # 项目详情
├── PATCH  /api/projects/:id            # 更新项目配置
└── DELETE /api/projects/:id            # 删除项目

章节模块
├── POST   /api/projects/:id/chapters               # 创建新章节
├── GET    /api/projects/:id/chapters               # 章节列表
├── GET    /api/projects/:id/chapters/:num          # 章节详情
├── PATCH  /api/projects/:id/chapters/:num          # 编辑章节内容
├── POST   /api/projects/:id/chapters/:num/confirm  # 确认故事，开始生成
└── GET    /api/projects/:id/chapters/:num/status   # 生成状态查询

任务模块
├── GET    /api/jobs/:id                # 任务详情
└── POST   /api/jobs/:id/cancel         # 取消任务

资源模块
├── GET    /api/voices                  # 可用音色列表
└── GET    /api/styles                  # 可用画面风格列表
```

### 6.2 核心数据结构

```typescript
// 项目创建请求
interface CreateProjectRequest {
  idea: string;                    // 用户创意
  style: StylePreset;              // 画面风格
  total_chapters: number;          // 总章节数 1-30
  chapter_duration_minutes: number; // 每章时长 2-10
  character_count: number;         // 角色数量 1-30
  language: 'zh-CN' | 'en-US';     // 语言
  voice_id: string;                // 音色ID
}

// 章节内容
interface ChapterContent {
  title: string;
  summary: string;
  characters: Character[];
  scenes: Scene[];
  word_count: number;
}

interface Character {
  name: string;
  description: string;   // 外貌描述（用于图像一致性）
  personality: string;
}

interface Scene {
  scene_id: number;
  location: string;
  time: string;
  mood: string;
  visual_description: string;  // 图像生成prompt
  narration: string;           // TTS朗读内容
  duration_hint: number;       // 建议秒数
}

// 生成状态响应
interface GenerationStatus {
  status: 'queued' | 'processing' | 'completed' | 'failed';
  stage: string;
  progress: number;           // 0-100
  estimated_remaining_seconds: number;
  message: string;
}

// 时间轴映射
interface TimelineItem {
  scene_id: number;
  image_url: string;
  start_sec: number;
  end_sec: number;
  duration_sec: number;
}
```

---

## 七、数据库设计（完整版）

> **负责人**: Ben（合伙人，CTO 级别）— 数据库/API 架构/基础设施由 Ben 团队维护

```sql
-- ============================================
-- 用户表
-- ============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20) UNIQUE,
    name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255),
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 项目表
-- ============================================
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200),                          -- LLM生成或用户编辑
    original_idea TEXT NOT NULL,                 -- 用户原始输入
    style_preset VARCHAR(50) NOT NULL,           -- 画面风格代码
    total_chapters INTEGER NOT NULL DEFAULT 1,
    chapter_duration_minutes INTEGER NOT NULL DEFAULT 3,
    character_count INTEGER NOT NULL DEFAULT 2,
    language VARCHAR(10) NOT NULL DEFAULT 'zh-CN',
    voice_id VARCHAR(100),
    thumbnail_url TEXT,                          -- 项目封面
    status VARCHAR(20) DEFAULT 'draft',          -- draft/in_progress/completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_projects_user ON projects(user_id);

-- ============================================
-- 章节表
-- ============================================
CREATE TABLE chapters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    chapter_number INTEGER NOT NULL,
    status VARCHAR(30) DEFAULT 'pending',
    
    -- 故事内容
    title VARCHAR(200),
    full_script TEXT,                            -- 完整剧本
    summary TEXT,                                -- 摘要（供续写参考）
    characters_json JSONB,                       -- 角色列表
    scenes_json JSONB,                           -- 场景列表
    word_count INTEGER,
    
    -- 分镜数据
    storyboard_json JSONB,                       -- 分镜决策结果
    
    -- 媒体资源
    audio_url TEXT,
    audio_duration_seconds FLOAT,
    timeline_json JSONB,                         -- 音画对齐结果
    video_url TEXT,
    thumbnail_url TEXT,
    
    -- 错误处理
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(project_id, chapter_number)
);

CREATE INDEX idx_chapters_project ON chapters(project_id);

-- ============================================
-- 场景图像表（一个场景可能多次重新生成）
-- ============================================
CREATE TABLE scene_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id UUID NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    scene_id INTEGER NOT NULL,
    image_prompt TEXT NOT NULL,                  -- 生成时使用的prompt
    image_url TEXT NOT NULL,
    thumbnail_url TEXT,
    width INTEGER,
    height INTEGER,
    is_active BOOLEAN DEFAULT TRUE,              -- 当前使用的版本
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scene_images_chapter ON scene_images(chapter_id);

-- ============================================
-- 生成任务表
-- ============================================
CREATE TABLE generation_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id UUID NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    job_type VARCHAR(30) NOT NULL,               -- story/storyboard/images/audio/align/composite/full
    status VARCHAR(20) DEFAULT 'queued',
    current_stage VARCHAR(50),
    progress INTEGER DEFAULT 0,
    estimated_seconds INTEGER,
    stage_message TEXT,
    
    -- Celery任务关联
    celery_task_id VARCHAR(100),
    
    -- 耗时统计
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- 错误信息
    error_message TEXT,
    error_traceback TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_jobs_chapter ON generation_jobs(chapter_id);
CREATE INDEX idx_jobs_status ON generation_jobs(status);

-- ============================================
-- 音色配置表
-- ============================================
CREATE TABLE voice_presets (
    id VARCHAR(100) PRIMARY KEY,                 -- 火山引擎音色ID
    name VARCHAR(100) NOT NULL,
    language VARCHAR(10) NOT NULL,
    gender VARCHAR(10),
    style VARCHAR(50),                           -- 风格标签
    sample_url TEXT,                             -- 试听链接
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 画面风格配置表
-- ============================================
CREATE TABLE style_presets (
    code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    example_image_url TEXT,
    prompt_template TEXT,                        -- 用于图像生成的风格描述
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0
);

-- 初始化风格数据
INSERT INTO style_presets (code, name, description, prompt_template, sort_order) VALUES
('realistic', '写实摄影', '真实光影，电影质感', 'photorealistic, cinematic lighting, film grain, 8K UHD', 1),
('illustration', '精美插画', '色彩丰富，艺术感强', 'digital illustration, vibrant colors, detailed artwork', 2),
('cyberpunk', '赛博朋克', '霓虹灯光，未来都市', 'cyberpunk style, neon lights, futuristic city, dark atmosphere', 3),
('ink', '中国水墨', '留白意境，传统美学', 'Chinese ink wash painting, minimalist, traditional aesthetics', 4),
('cartoon', '卡通动画', 'Q版可爱，色彩明快', 'cartoon style, cute characters, bright colors, simple shapes', 5),
('chinese', '中国风', '古典元素，传统配色', 'Chinese traditional style, classical elements, red and gold palette', 6),
('manga', '日本漫画', '分镜感强，情绪张力', 'manga style, Japanese anime, dramatic expressions, dynamic poses', 7),
('oil_painting', '油画风格', '厚重笔触，古典美感', 'oil painting style, textured brushstrokes, classical art', 8),
('watercolor', '水彩风格', '透明轻盈，梦幻氛围', 'watercolor style, soft edges, dreamy atmosphere, pastel colors', 9),
('pixel', '像素艺术', '复古游戏感', 'pixel art style, 16-bit retro game aesthetic', 10);
```

---

## 八、分阶段开发计划

### Phase 1: 故事生成核心 ✅（进行中）

**目标**: 跑通 idea → 故事JSON

**交付物**:
- FastAPI项目骨架
- 数据库模型 (users, projects, chapters, jobs)
- Gemini 3 Pro 故事生成服务
- 基础API端点 (创建项目、生成故事、查询状态)
- MVP认证

**验收标准**:
- API返回结构完整的故事JSON
- 故事内容具备叙事性，分镜描述可执行

---

### Phase 2: 分镜与图像生成

**目标**: 故事 → 分镜图像

**交付物**:
- 分镜决策服务 (Gemini 3 Pro)
- Nano Banana Pro 图像生成服务
- 图像存储服务 (OSS集成)
- 场景图像管理API

**验收标准**:
- 每个scene生成对应图像
- 同一角色跨场景外貌基本一致

**技术要点**:
- Nano Banana Pro支持传入参考图保持角色一致性
- 图像生成可并行（Celery group）

---

### Phase 3: 音频合成与音画对齐

**目标**: 旁白生成 + 时间轴映射

**交付物**:
- 火山引擎TTS集成
- OpenAI Whisper时间戳服务
- Gemini 2.5 Flash 图文匹配服务
- 时间轴生成逻辑

**验收标准**:
- TTS音频自然流畅
- 图片停留时长与旁白内容匹配
- 音画误差≤80ms

**技术要点**:
- 参考 story_video_generator.py 的对齐逻辑
- Whisper返回word级时间戳用于精确切分

---

### Phase 4: 视频合成

**目标**: 生成可发布的MP4

**交付物**:
- FFmpeg/MoviePy 视频合成服务
- Ken Burns效果实现
- 字幕渲染（中文字体支持）
- BGM混音（可选）

**验收标准**:
- 输出1080p MP4
- 字幕清晰可读
- 视频无卡顿/花屏

**技术要点**:
- ImageMagick字幕渲染需指定中文字体
- Ken Burns参数随机化增加动态感

---

### Phase 5: 前端MVP

**目标**: 可用的Web界面

**交付物**:
- Next.js项目
- 登录页
- 项目列表/资料库页
- 创建项目表单
- 故事编辑页
- 生成状态页
- 视频预览/下载页

**验收标准**:
- 全流程可在浏览器完成
- 响应式适配移动端

---

### Phase 6: 优化与扩展

**目标**: 生产可用

**交付物**:
- 真实用户认证 (手机验证码/微信OAuth)
- 付费/配额系统
- 章节续写功能
- 视频二次编辑
- 性能优化 (缓存/并行/预热)
- 监控告警

---

## 九、部署架构

### 9.1 开发环境

```
本地机器
├── Docker Compose
│   ├── app (FastAPI)
│   ├── worker (Celery)
│   ├── redis
│   └── postgres
└── .env.local
```

### 9.2 生产环境

```
                    ┌─────────────┐
                    │   CDN       │
                    │ (CloudFlare)│
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Nginx     │
                    │ (SSL/LB)    │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
  ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
  │  FastAPI    │   │  FastAPI    │   │  Next.js    │
  │  Pod 1      │   │  Pod 2      │   │  (Vercel)   │
  └──────┬──────┘   └──────┬──────┘   └─────────────┘
         │                 │
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │     Redis       │
         │   (队列/缓存)    │
         └────────┬────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐    ┌────▼────┐   ┌────▼────┐
│Celery │    │ Celery  │   │ Celery  │
│Worker1│    │ Worker2 │   │ Worker3 │
└───────┘    └─────────┘   └─────────┘
                  │
         ┌────────▼────────┐
         │   PostgreSQL    │
         │   (RDS)         │
         └─────────────────┘
                  │
         ┌────────▼────────┐
         │    OSS/S3       │
         │  (媒体存储)      │
         └─────────────────┘
```

---

## 十、扩展性预留

### 10.1 多语言支持

- 数据库language字段已预留
- TTS音色按语言分类
- 字幕渲染支持多语言字体

### 10.2 多平台输出

- 视频分辨率/比例参数化
- 平台预设 (抖音9:16, 视频号4:3, YouTube16:9)

### 10.3 模型可替换

- AI服务抽象为接口
- 配置化模型选择
- 备用模型fallback

### 10.4 插件化

- BGM库扩展
- 特效模板扩展
- 转场动画扩展

---

## 附录A: 环境变量清单

```env
# ===== 数据库 =====
DATABASE_URL=postgresql://user:pass@localhost:5432/xuhua_story

# ===== Redis =====
REDIS_URL=redis://localhost:6379/0

# ===== AI服务 =====
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
VOLCENGINE_ACCESS_KEY=your_volcengine_ak
VOLCENGINE_SECRET_KEY=your_volcengine_sk

# ===== 对象存储 =====
OSS_ENDPOINT=oss-cn-shanghai.aliyuncs.com
OSS_ACCESS_KEY=your_oss_ak
OSS_SECRET_KEY=your_oss_sk
OSS_BUCKET=xuhua-story-assets

# ===== 应用配置 =====
APP_ENV=development
APP_SECRET_KEY=your_secret_key
CORS_ORIGINS=http://localhost:3000

# ===== Celery =====
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

---

## 附录B: 参考资料

- [Gemini 3 Pro API文档](https://ai.google.dev/gemini-api/docs/gemini-3)
- [Nano Banana Pro开发指南](https://ai.google.dev/gemini-api/docs/image-generation)
- [火山引擎TTS文档](https://www.volcengine.com/docs/6561)
- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
- [FFmpeg官方文档](https://ffmpeg.org/documentation.html)
- [MoviePy文档](https://zulko.github.io/moviepy/)

---

*文档结束*
