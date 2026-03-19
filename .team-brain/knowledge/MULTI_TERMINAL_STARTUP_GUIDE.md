# 7 终端启动指南

> 序话Story 多 Agent 协作启动手册
> 适用于已有项目的日常开发

---

## 概述

本指南说明如何启动 7 个 Claude Code 终端进行多 Agent 协作开发：
- 1 个主会话（协调者）
- 6 个专业 Agent（PM、Backend、Frontend、Tester、AI-ML、DevOps）

---

## 启动顺序

```
1. 主会话 (协调者)     - 全局视角，任务分配
2. PM Agent           - 需求管理，优先级
3. Backend Agent      - 当前主力，Phase 4
4. AI-ML Agent        - 支援，一致性优化
5. Tester Agent       - 质量保障，测试基准
6. Frontend Agent     - 待命，Phase 5 准备
7. DevOps Agent       - 待命，部署准备
```

---

## 终端 1：主会话（协调者）

### 启动命令
```bash
cd /Users/kaisbabybook/aifun/xuhuastory/xuhua_story
claude
```

### 开场白（复制粘贴）
```
你是序话Story项目的主协调者。

当前项目状态：
- Phase 3 已完成（音频对齐）
- Phase 4 进行中（视频合成 MVP）
- Phase 5 待启动（前端）

你的职责：
1. 协调 6 个专业 Agent 的工作
2. 分配任务、解决阻塞
3. 汇总各 Agent 进度

请先阅读：
- /.team-brain/status/TODAY_FOCUS.md
- /.team-brain/status/PROJECT_STATUS.md

然后告诉我当前各 Agent 的任务分配建议。
```

---

## 终端 2：PM Agent

### 启动命令
```bash
cd /Users/kaisbabybook/aifun/xuhuastory/xuhua_story
claude
```

### 开场白（复制粘贴）
```
请先阅读 .claude/agents/pm.md 了解你的角色定义。

然后按"开工前必读"顺序阅读：
1. /.team-brain/status/TODAY_FOCUS.md
2. /.team-brain/handoffs/PENDING.md
3. /.team-brain/status/PROJECT_STATUS.md
4. /CLAUDE.md

完成后：
1. 确认当前项目优先级
2. 检查 PENDING.md 是否有待处理交接
3. 更新你的进度文件 .claude/agents/pm-progress/current.md

告诉我今日重点任务分配。
```

---

## 终端 3：Backend Agent

### 启动命令
```bash
cd /Users/kaisbabybook/aifun/xuhuastory/xuhua_story
claude
```

### 开场白（复制粘贴）
```
请先阅读 .claude/agents/backend.md 了解你的角色定义。

然后按"开工前必读"顺序阅读状态文件。

你当前的主线任务是 Phase 4 视频合成 MVP：
- FFmpeg vs MoviePy 技术选型
- Ken Burns 效果设计
- 视频合成 pipeline 实现

请先了解：
- /docs/ARCHITECTURE.md 整体架构
- /app/ 目录现有代码结构

然后更新 .claude/agents/backend-progress/current.md，告诉我你的开工计划。
```

---

## 终端 4：AI-ML Agent

### 启动命令
```bash
cd /Users/kaisbabybook/aifun/xuhuastory/xuhua_story
claude
```

### 开场白（复制粘贴）
```
请先阅读 .claude/agents/ai-ml.md 了解你的角色定义。

然后按"开工前必读"顺序阅读状态文件。

你的待处理任务：
- 6人场景一致性从 90% 提升到 95%
- Pro 模型成本优化研究
- Prompt 结构化标记改造

请先了解：
- /docs/character_consistency_breakthrough_6.4.md
- /app/services/storyboard_prompts.py

然后更新 .claude/agents/ai-ml-progress/current.md，告诉我你打算先做哪个任务。
```

---

## 终端 5：Tester Agent

### 启动命令
```bash
cd /Users/kaisbabybook/aifun/xuhuastory/xuhua_story
claude
```

### 开场白（复制粘贴）
```
请先阅读 .claude/agents/tester.md 了解你的角色定义。

然后按"开工前必读"顺序阅读状态文件。

你的任务：
- 为 @ai-ml 建立 6 人场景一致性测试基准
- 确保 Phase 3 回归测试通过
- 准备 Phase 4 测试框架

请先了解：
- /tests/ 目录现有测试结构
- /tests/test_character_consistency_regression.py

然后更新 .claude/agents/tester-progress/current.md。
```

---

## 终端 6：Frontend Agent

### 启动命令
```bash
cd /Users/kaisbabybook/aifun/xuhuastory/xuhua_story
claude
```

### 开场白（复制粘贴）
```
请先阅读 .claude/agents/frontend.md 了解你的角色定义。

然后按"开工前必读"顺序阅读状态文件。

你当前状态：待命（等待 Phase 4 完成后启动 Phase 5）

准备工作：
- 了解后端 API 结构
- 熟悉产品设计理念（见 CLAUDE.md 的产品设计理念部分）
- 准备 Next.js 14 项目架构设计

请更新 .claude/agents/frontend-progress/current.md，记录你的准备状态。

如果有问题需要 @backend 澄清，写入 context-for-others.md。
```

---

## 终端 7：DevOps Agent

### 启动命令
```bash
cd /Users/kaisbabybook/aifun/xuhuastory/xuhua_story
claude
```

### 开场白（复制粘贴）
```
请先阅读 .claude/agents/devops.md 了解你的角色定义。

然后按"开工前必读"顺序阅读状态文件。

你当前状态：待命（等待 Phase 4/5 完成后启动部署）

准备工作：
- 了解项目技术栈（见 .team-brain/context/TECH_STACK.md）
- 收集 @backend 的环境变量清单需求
- 初步设计 Docker 配置

请更新 .claude/agents/devops-progress/current.md，记录阻塞项和准备状态。
```

---

## 日常协作流程

### Agent 间通信架构

```
┌─────────────────────────────────────────────────────────┐
│                    主会话 (协调)                          │
│  - 读取各 Agent 的 current.md 汇总进度                    │
│  - 发现阻塞时协调解决                                     │
│  - 重大决策记录到 DECISIONS.md                           │
└─────────────────────────────────────────────────────────┘
                          ↕
    ┌──────────┬──────────┬──────────┬──────────┬──────────┐
    │    PM    │ Backend  │  AI-ML   │  Tester  │ Frontend │
    │          │          │          │          │          │
    │ 需求澄清  │ Phase 4  │ 一致性   │ 测试基准  │ 待命     │
    └──────────┴──────────┴──────────┴──────────┴──────────┘
```

### 每个 Agent 完成任务后

```
1. 更新自己的 current.md（标记任务完成）
2. 如需其他 Agent 协助 → 写入 context-for-others.md
3. 重大交接 → 写入 PENDING.md 并 @目标Agent
```

### 主会话定期检查（复制粘贴）

```
请读取所有 Agent 的 progress 文件，汇总当前状态：
- .claude/agents/backend-progress/current.md
- .claude/agents/ai-ml-progress/current.md
- .claude/agents/tester-progress/current.md
- .claude/agents/frontend-progress/current.md
- .claude/agents/devops-progress/current.md
- .claude/agents/pm-progress/current.md

告诉我：
1. 谁在做什么
2. 谁被阻塞了
3. 有什么需要我协调的
```

---

## 快速参考卡片

| 终端 | Agent | 当前任务 | 状态 |
|------|-------|---------|------|
| 1 | 主会话 | 协调全局 | 🟢 活跃 |
| 2 | PM | 需求管理 | 🟢 活跃 |
| 3 | Backend | Phase 4 视频合成 | 🟢 主力 |
| 4 | AI-ML | 6人一致性优化 | 🟡 支援 |
| 5 | Tester | 测试基准建立 | 🟡 支援 |
| 6 | Frontend | Phase 5 准备 | ⚪ 待命 |
| 7 | DevOps | 部署准备 | ⚪ 待命 |

---

## 关键文件速查

### Agent 定义文件
```
.claude/agents/pm.md
.claude/agents/backend.md
.claude/agents/frontend.md
.claude/agents/tester.md
.claude/agents/ai-ml.md
.claude/agents/devops.md
```

### Agent 进度文件
```
.claude/agents/*/current.md          # 当前任务
.claude/agents/*/completed.md        # 已完成任务
.claude/agents/*/context-for-others.md  # 给其他 Agent 的信息
```

### 项目状态文件
```
/.team-brain/status/TODAY_FOCUS.md      # 今日重点（最紧急）
/.team-brain/handoffs/PENDING.md        # 待处理交接
/.team-brain/status/PROJECT_STATUS.md   # 项目状态
/CLAUDE.md                               # 核心约束
```

---

## 常见问题

### Q: Agent 之间如何传递信息？

通过文件系统：
1. 更新自己的 `current.md` 状态
2. 需要协助时写入 `context-for-others.md`
3. 正式交接写入 `PENDING.md`

### Q: 主会话多久检查一次？

建议：
- 每 30 分钟检查一次各 Agent 进度
- 收到 @主会话 的交接时立即响应

### Q: 待命的 Agent 需要做什么？

1. 阅读状态文件保持信息同步
2. 做准备工作（了解相关代码、设计方案）
3. 记录阻塞项和依赖
4. 等待主会话分配任务

---

## Ben 团队（Codex Agent）说明

> **重要**: Ben 的 Codex Agent 不由本启动脚本管理，运行在独立的终端环境中。

### 运行环境差异

| 维度 | Founder 团队 | Ben 团队 |
|------|------------|---------|
| 工具 | Claude Code (`claude` CLI) | OpenAI Codex CLI |
| 启动方式 | 本指南的 7 终端方案 | Ben 自行管理 |
| Agent 配置 | `.claude/agents/` | `codex-agents/` |
| 进度文件 | `.claude/agents/*-progress/` | `codex-agents/*-progress/` |
| 管理者 | Founder（本文档） | Ben（独立） |

### 跨团队协作方式

Ben 团队不通过 Founder 的终端启动流程接入，但两团队共享以下机制：

- **共享记忆**: `.team-brain/shared-memory/` — 双方可读可写
- **Ben 群聊**: `.team-brain/TEAM_CHAT_Ben.md` — Founder 只读
- **Git PR**: 跨团队代码变更通过 Pull Request 合并（Founder 分支: `founder/xxx`，Ben 分支: `ben/xxx`）
- **微信**: Founder 和 Ben 实时讨论（线下）

### 如何了解 Ben 团队状态

```bash
# 读取 Ben 团队进度文件
cat codex-agents/backend_Ben-progress/current.md
cat codex-agents/pm_Ben-progress/context-for-others.md

# 读取共享记忆
ls .team-brain/shared-memory/
```

---

## 更新记录

| 日期 | 更新内容 |
|------|----------|
| 2025-01-06 | 初始版本 |
| 2026-03-19 | 新增 Ben 团队（Codex Agent）说明 |
