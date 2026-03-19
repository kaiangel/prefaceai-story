# 序话Story - Ben 团队上下文

> 你是序话Story项目 Ben 团队的 AI 助手（OpenAI Codex）。Ben 是项目的人类合伙人兼技术联合创始人。
>
> Founder 团队使用 Claude Code，有独立的 7 个 Agent。两个团队通过 GitHub + TEAM_CHAT 文件协作。

---

## Ben 的角色

- **身份**: 序话Story 合伙人兼技术联合创始人
- **背景**: CTO 级别，安居客/车轮技术总监/CTO，后端+数据库+架构专长
- **决策权**: 后端架构/数据库/系统设计 = Ben 主导；产品方向 = Founder 主导

---

## Ben 的职责范围

### 负责的领域
- **数据库/用户系统**: 从零搭建（PostgreSQL + SQLAlchemy/SQLModel + Alembic）
- **API 架构/计费系统**: 新模块开发
- **运营/市场相关的技术支撑**: 数据分析后端、AB 测试框架等
- **基础设施/DevOps**: 与 Founder 共同负责

### 不碰的领域
- **Pipeline (Stage 1-5)**: Founder 团队的 Backend/AI-ML agent 负责
- **Prompt 工程**: Founder 团队的 AI-ML agent 负责
- **前端产品方向**: Founder 主导（Ben 的 frontend_Ben 做联动性前端工作）

---

## 项目概述

序话Story 是一个 AI 条漫/短视频生成系统。用户输入一句话创意，系统自动生成可发布的条漫或短视频。

### 技术架构（5 阶段 Pipeline）

```
idea → Stage 1 (故事大纲) → Stage 2 (角色设计) → Stage 3 (剧本) → Stage 4 (分镜) → Stage 5 (图像生成) → 成品
```

- Stage 1-4: Claude Sonnet 4.6 文本生成
- Stage 5: Nano Banana 2 (gemini-3.1-flash-image-preview) 图像生成
- 后处理: TextOverlayService 中文文字叠加

### 核心服务

| 服务 | 文件 | 说明 |
|------|------|------|
| Pipeline Orchestrator | `app/services/pipeline_orchestrator.py` | 主流程编排 |
| Image Generator | `app/services/image_generator.py` | 图像生成 |
| Story Generator | `app/services/story_generator.py` | 故事生成 |
| Text Overlay | `app/services/text_overlay_service.py` | 文字叠加 |
| Shot Validator | `app/services/shot_validator.py` | 质量校验 |

> Pipeline 相关代码由 Founder 团队维护，Ben 团队不修改。

### 前端

- Next.js 14 + TailwindCSS + TypeScript + Framer Motion
- 入口: `frontend/src/`
- 线上: https://prefaceai.mov

### 生产环境

- VPS: 107.148.1.199 (Docker 28.1.1 + Compose)
- 容器: api (FastAPI) + frontend (Next.js standalone) + redis
- SSL: Cloudflare Full Strict
- GitHub: https://github.com/kaiangel/prefaceai-story (private)

---

## 双团队协作模式

### 团队组成

| 团队 | 成员 | 工具 | 文件位置 |
|------|------|------|---------|
| Founder 团队 | Coordinator + PM + Backend + AI-ML + Frontend + Tester + DevOps (7个) | Claude Code (Opus 4.6) | `.claude/agents/` |
| Ben 团队 | frontend_Ben + backend_Ben + pm_Ben (3个) | Codex CLI (GPT-5.3-codex) | `.team-brain/team_ben/` |

### 沟通渠道

| 渠道 | 用途 | 文件 |
|------|------|------|
| Founder 团队群聊 | Founder 团队内部沟通 | `.team-brain/TEAM_CHAT.md`（Ben 只读） |
| Ben 团队群聊 | Ben 团队内部沟通 | `.team-brain/team_ben/TEAM_CHAT.md`（Founder 只读） |
| 微信 | Founder 和 Ben 实时讨论 | 线下 |
| shared-memory | 共享记忆文件 | `.team-brain/shared-memory/` |

### 互相只读规则（强约定）

- Ben 团队 **不修改** `.claude/agents/` 下的任何文件
- Ben 团队 **不修改** `.team-brain/TEAM_CHAT.md`
- Founder 团队 **不修改** `.team-brain/team_ben/` 下的任何文件
- Founder 团队 **不修改** `.team-brain/team_ben/TEAM_CHAT.md`

### Git 工作流

- 两人（Founder + Ben）都直接 push 到 `main` 分支
- 分工不同，代码冲突概率极低；如有冲突，两人沟通解决后再 push
- **Push 节奏**: 每次工作 session（阶段性）结束后 push，不是每个小改动都 push

### team_chat.md 格式

```markdown
### YYYY-MM-DD HH:MM

**@agent_name**:
消息内容。@mention 通知其他 agent。

---
```

---

## 代码规范

### Python (后端)
- 异步: 所有外部 API 调用使用 `async/await`
- 错误处理: LLM 失败 → fallback 到简单规则；服务都有降级策略
- 日志格式: `print(f"[ServiceName] ✅ 操作成功: {detail}")` / `print(f"[ServiceName] ❌ 操作失败: {error}")`
- 文件命名: 服务类 `*_service.py` 或 `*_manager.py`，测试 `test_*.py`

### 通用
- 不要硬编码：故事类型、角色类型、风格
- 宽高比统一 2:3（抖音适配）
- 图像生成 prompt 必须全英文（Pipeline 约定，Ben 不直接涉及但需知晓）

---

## 关键决策摘要

| 决策 | 内容 | 日期 |
|------|------|------|
| DEC-014 | 移除 previous_shot_image 传递 | 2026-03-03 |
| DEC-013 | Create 页面升级 7 项功能决策 | 2026-02-28 |
| DEC-012 | 模型全面升级 Sonnet 4.6 + 灌篮高手风格 | 2026-02-25 |
| DEC-011 | 条漫产品形态定义（篇幅/交付/用户旅程） | 2026-02-24 |
| DEC-010 | 参考图源头统一 2:3 | 2026-02-24 |

> 完整决策链: `.team-brain/decisions/DECISIONS.md`

---

## 环境变量

```bash
# 必需 (Founder 管理，Ben 需知晓)
ANTHROPIC_API_KEY=sk-ant-xxx       # Claude
GEMINI_API_KEY=AIzaSyxxx           # Gemini
OPENAI_API_KEY=sk-xxx              # Whisper
VOLCENGINE_ACCESS_KEY=AKLTxxx      # 火山引擎 TTS
VOLCENGINE_SECRET_KEY=xxx
VOLCENGINE_TTS_APPID=xxx

# 数据库 (Ben 负责)
DATABASE_URL=postgresql://...      # 待 Ben 搭建
REDIS_URL=redis://localhost:6379   # 已有
```

---

## 推荐阅读清单

### 必读（开工前）
1. 本文件 (`codex.md`)
2. `CLAUDE.md` 前半部分（项目状态 + 产品定位 + 技术架构）
3. `.team-brain/status/PROJECT_STATUS.md`
4. `.team-brain/decisions/DECISIONS.md`

### 了解团队（第一周内）
5. `.team-brain/TEAM_PROTOCOL.md`
6. 各 Agent 的 `context-for-others.md`（`.claude/agents/*-progress/`）
7. `docs/ARCHITECTURE.md`
8. DevOps 的 `current.md`（运维风险清单）

### 深入了解（需要时查阅）
9. `.team-brain/TEAM_CHAT.md`（让 Codex 搜索关键词）
10. `docs/` 目录下的技术文档
11. `.team-brain/shared-memory/`（项目记忆）

---

## Ben 的 Agent 团队

| Agent | 文件 | 职责 |
|-------|------|------|
| backend_Ben | `.team-brain/team_ben/backend.md` | 后端 + 数据库 + API 架构 |
| frontend_Ben | `.team-brain/team_ben/frontend.md` | 前端联动（Ben 侧需要时） |
| pm_Ben | `.team-brain/team_ben/pm.md` | 协调 + 文档 + 与 Founder PM 对齐 |

### Progress 文件

每个 Agent 维护三个文件（与 Founder 团队一致）：
- `current.md` — 当前在做什么
- `context-for-others.md` — 其他人需要知道的
- `completed.md` — 已完成的工作

---

*记住：Ben 团队专注于数据库、API 架构和运营技术。Pipeline 和 Prompt 由 Founder 团队维护。*
