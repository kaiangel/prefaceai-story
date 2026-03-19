# Agent 进度追踪协议

> 本协议定义了 Founder 团队 6 个 Agent（+ Ben 团队 3 个 Codex Agent）之间通过进度文件同步信息的机制

---

## 核心理念

```
每个 Agent 有自己的进度目录
├── 记录自己在做什么
├── 记录完成了什么
└── 告诉其他 Agent 需要知道的信息

其他 Agent 通过读取这些文件了解团队状态
```

**关键**：这是 Agent 间信息同步的核心机制。不更新 = 其他 Agent 看不到你的进展。

---

## 目录结构

```
/.claude/agents/                  # Founder 团队（Claude Code）
├── backend.md                    # 角色配置
├── backend-progress/             # 进度追踪 ← 新增
│   ├── current.md                # 当前任务
│   ├── completed.md              # 已完成任务
│   └── context-for-others.md     # 给其他agent的信息
│
├── frontend.md
├── frontend-progress/
│   └── ...
│
├── tester.md
├── tester-progress/
│   └── ...
│
├── ai-ml.md
├── ai-ml-progress/
│   └── ...
│
├── devops.md
├── devops-progress/
│   └── ...
│
├── pm.md
└── pm-progress/
    └── ...

/.team-brain/team_ben/            # Ben 团队（OpenAI Codex CLI）
├── backend.md                    # 角色配置
├── backend-progress/             # 进度追踪（相同的三文件结构）
│   ├── current.md
│   ├── completed.md
│   └── context-for-others.md
│
├── frontend.md
├── frontend-progress/
│   └── ...
│
├── pm.md
└── pm-progress/
    └── ...
```

> **注意**: Ben 团队的 `.team-brain/team_ben/` 进度文件结构与 Founder 团队的 `.claude/agents/` 完全相同（current.md、completed.md、context-for-others.md 三文件规范）。两团队通过 `.team-brain/shared-memory/` 进行跨团队信息同步。

---

## 三个文件的用途

### 1. current.md - 当前任务

**用途**：让其他 Agent 知道你正在做什么

**何时更新**：
- 开始新任务时
- 任务状态变化时（进行中→被阻塞）
- 发现新的待办事项时

**模板**：
```markdown
# [Agent] Agent - 当前任务

> **最后更新**: YYYY-MM-DD HH:MM
> **状态**: 进行中 / 待命 / 被阻塞

## 正在进行
- [ ] 任务描述

## 待处理队列
- [ ] 待办1
- [ ] 待办2

## 阻塞项
| 阻塞项 | 等待 | 预计解除 |
|--------|------|----------|
| xxx | @agent | 日期 |

## 需要其他 Agent 协助
| 需要 | Agent | 原因 |
|------|-------|------|
| xxx | @agent | 原因 |
```

### 2. completed.md - 已完成任务

**用途**：记录完成的工作，供回顾和知识沉淀

**何时更新**：
- 完成一个任务时
- 从 current.md 移动任务过来

**模板**：
```markdown
### [任务标题] ✅

**完成时间**: YYYY-MM-DD
**验收状态**: 通过/部分通过

**完成内容**:
- [x] 内容1
- [x] 内容2

**关键产出**:
| 文件 | 说明 |
|------|------|
| path/to/file | 说明 |

**验收指标**:
- 指标1: 结果 ✅/❌

**经验教训**: (如有)
```

### 3. context-for-others.md - 给其他 Agent 的信息

**用途**：其他 Agent 了解你的工作状态和可用资源

**何时更新**：
- 完成任务后更新状态速览
- 产出新资源时（API、组件、测试等）
- 发现需要其他 Agent 知道的约束时

**核心部分**：
```markdown
## 当前状态速览
状态: 🟢 正常 / 🟡 部分阻塞 / 🔴 严重阻塞 / ⚪ 未启动
当前任务: xxx
阻塞: 有/无
可对接: xxx

## 给 @[agent] 的信息
[该 agent 需要知道的具体内容]
```

---

## 工作流程

### Agent 开工时

```
1. 阅读自己的 current.md，回顾上次进度
2. 阅读 PM 的 context-for-others.md，了解当前优先级
3. 阅读相关 Agent 的 context-for-others.md，了解依赖状态
4. 更新自己的 current.md，标记开始新任务
```

### Agent 工作中

```
1. 遇到阻塞 → 更新 current.md 的阻塞项
2. 需要其他 Agent → 更新 current.md 的协助需求
3. 产出中间成果 → 更新 context-for-others.md
```

### Agent 完成任务时

```
1. 将任务从 current.md 移到 completed.md
2. 更新 context-for-others.md 的状态速览
3. 更新 context-for-others.md 中相关 Agent 的信息
4. 继续处理下一个任务，更新 current.md
```

---

## 信息流动图

```
┌─────────────────────────────────────────────────────────────┐
│                        PM Agent                              │
│  context-for-others.md: 优先级、产品方向、验收标准           │
└─────────────────────────────────────────────────────────────┘
                    ↓ 读取优先级
┌──────────────────────────────────────────────────────────────┐
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                │
│  │ Backend  │←──→│ Frontend │←──→│  Tester  │                │
│  │          │    │          │    │          │                │
│  │ API状态  │    │ 页面状态 │    │ 测试结果 │                │
│  └──────────┘    └──────────┘    └──────────┘                │
│       ↑               ↑               ↑                      │
│       └───────────────┼───────────────┘                      │
│                       │                                      │
│  ┌──────────┐    ┌──────────┐                                │
│  │  AI-ML   │←──→│  DevOps  │                                │
│  │          │    │          │                                │
│  │Prompt约束│    │ 部署状态 │                                │
│  └──────────┘    └──────────┘                                │
└──────────────────────────────────────────────────────────────┘

箭头 = 读取对方的 context-for-others.md
```

---

## 与现有 .team-brain 的关系

| 机制 | 粒度 | 用途 |
|------|------|------|
| `.team-brain/status/PROJECT_STATUS.md` | 项目级 | 整体进度看板 |
| `.team-brain/daily-sync/YYYY-MM-DD.md` | 日级 | 每日工作汇总 |
| `.team-brain/handoffs/PENDING.md` | 事件级 | 正式交接 |
| **`.claude/agents/*-progress/`** | **任务级** | **Agent 间实时同步** |

**两者互补**：
- progress 目录用于**实时、细粒度**的 Agent 间同步
- team-brain 用于**正式、粗粒度**的项目管理

---

## 快速参考

### 我要知道某个 Agent 在做什么

```
读取: /.claude/agents/{agent}-progress/current.md
```

### 我要知道某个 Agent 能提供什么

```
读取: /.claude/agents/{agent}-progress/context-for-others.md
```

### 我完成了一个任务

```
1. 移动任务到 completed.md
2. 更新 context-for-others.md 的状态速览
3. 更新 current.md 的下一个任务
```

### 我被阻塞了

```
1. 更新 current.md 的阻塞项
2. 更新 current.md 的"需要其他 Agent 协助"
3. （可选）在 .team-brain/handoffs/PENDING.md 创建正式交接
```

---

## 使用场景示例

### 示例1：日常状态同步（用 progress 文件）

**场景**：Backend 完成了一个 API 开发

```markdown
# 更新 backend-progress/context-for-others.md

## 当前状态速览
状态: 🟢 正常
当前任务: Phase 4 视频合成
阻塞: 无
可对接: GET /api/videos/{id} 已就绪

## 给 @frontend 的信息
新增 API 端点 GET /api/videos/{id}，可以开始对接
```

**不需要**创建正式交接，因为这是日常进度更新。

---

### 示例2：重大交接（用 handoffs + progress）

**场景**：Backend 完成了整个 Phase 4，需要 Frontend 接手

```markdown
# 1. 先更新 backend-progress/context-for-others.md（实时同步）
状态: 🟢 正常
当前任务: Phase 4 已完成
可对接: 视频合成 API 全部就绪

# 2. 再创建 .team-brain/handoffs/PENDING.md 条目（正式记录）
### HANDOFF-2025-01-06-001
**From**: @backend
**To**: @frontend
**Priority**: P0

#### 已完成
- [x] 视频合成服务
- [x] 所有 API 端点
- [x] API 文档

#### 需要接手
- [ ] 前端页面对接
- [ ] 视频预览组件
```

**两者都要**，因为这是里程碑级的重大交接。

---

### 示例3：被阻塞时（用 progress 文件）

**场景**：Frontend 等待 Backend 的 API

```markdown
# 更新 frontend-progress/current.md

## 正在进行
- [ ] 视频预览页面（被阻塞）

## 阻塞项
| 阻塞项 | 等待 | 预计解除 |
|--------|------|----------|
| GET /api/videos API | @backend | 1-2天 |

## 需要其他 Agent 协助
| 需要 | Agent | 原因 |
|------|-------|------|
| 视频 API | @backend | 前端无法继续开发 |
```

**不需要**创建交接，因为这是阻塞状态记录，@backend 会看到。

---

### 示例4：发现新约束（用 progress 文件）

**场景**：AI-ML 发现新的 Prompt 约束

```markdown
# 更新 ai-ml-progress/context-for-others.md

## 给 @backend 的信息
### ⚠️ 新发现的约束
图像 Prompt 中不要使用 "close-up" 关键词，
会导致 Pro 模型裁切参考图导致角色特征丢失。

改用 "portrait shot" 或 "medium close shot"。
```

**立即更新**，让 @backend 在下次工作前就能看到。

---

### 判断规则总结

| 场景 | 用 progress 文件 | 用 handoffs |
|------|-----------------|-------------|
| 日常状态更新 | ✅ | ❌ |
| 完成一个小任务 | ✅ | ❌ |
| 被阻塞/需要协助 | ✅ | ❌ |
| 发现新约束/经验 | ✅ | ❌ |
| 完成整个 Phase | ✅ | ✅ |
| 里程碑交接 | ✅ | ✅ |
| 需要正式记录的交接 | ✅ | ✅ |

**简单规则**：progress 文件**总是要更新**，handoffs 只在**重大交接**时创建。

---

## 注意事项

1. **保持简洁**：进度文件不需要长篇大论，关键信息即可
2. **及时更新**：完成任务后立即更新，不要攒着
3. **面向其他 Agent**：context-for-others.md 要想"对方需要知道什么"
4. **不替代交接**：重大交接仍走 `.team-brain/handoffs/PENDING.md`

---

*创建日期: 2025-01-06*
*版本: 1.0*
