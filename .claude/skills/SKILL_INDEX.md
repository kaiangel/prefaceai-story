# Skill Index - xuhuastory

> 基于 Agent-Skills-for-Context-Engineering 的渐进式披露原则
> **按需加载，不要一次读完所有skill**

---

## 两类Skills

### 1. xuhuastory专属Skills（本地）

| Skill | 触发场景 | 优先级 |
|-------|---------|--------|
| [character-consistency](./character-consistency.md) | 修改图像生成相关代码 | 🔴 必读 |
| [prompt-engineering](./prompt-engineering.md) | 修改Prompt模板 | 🔴 必读 |
| [audio-alignment](./audio-alignment.md) | 修改音画对齐逻辑 | 🟡 高 |
| [context-management](./context-management.md) | 工作流程管理 | 🟡 推荐 |

**中英文触发词对照**: [XUHUASTORY_SKILL_TRIGGERS.md](./XUHUASTORY_SKILL_TRIGGERS.md)

### 2. Claude Official Plugins（已安装 8 个）

| Plugin | Scope | Skills/命令 |
|--------|-------|-------------|
| commit-commands | user | `/commit`, `/commit-push-pr`, `/clean_gone` |
| code-review | user | `/code-review` |
| feature-dev | user | `/feature-dev` |
| frontend-design | project | `/frontend-design` |
| pr-review-toolkit | project | 6个专业agent（自动触发） |
| hookify | project | `/hookify`, `/hookify:list`, `/hookify:configure` |
| pyright-lsp | project | 自动（Python类型检查） |
| security-guidance | project | 自动（安全指导） |

**中英文触发词对照**: [OFFICIAL_PLUGIN_TRIGGERS.md](./OFFICIAL_PLUGIN_TRIGGERS.md)

### 3. Context Engineering Skills（全局已安装）

| Plugin | 包含Skills | 触发场景 |
|--------|-----------|---------|
| context-engineering-fundamentals | context-fundamentals, context-degradation, context-compression, context-optimization | 上下文问题 |
| agent-architecture | multi-agent-patterns, memory-systems, tool-design | 多Agent/记忆/工具 |
| agent-evaluation | evaluation, advanced-evaluation | 评估Agent质量 |
| agent-development | project-development | AI项目开发 |
| cognitive-architecture | bdi-mental-states | 认知架构/决策 |

**中英文触发词对照**: [CONTEXT_ENGINEERING_TRIGGERS.md](./CONTEXT_ENGINEERING_TRIGGERS.md)

---

## Skill Activation Rules

### character-consistency.md

**触发词**: 角色一致性, 参考图, Pro模型, use_pro_model, 变脸

**触发文件**:
- `image_generator.py`
- `storyboard_prompts.py`
- `storyboard_service.py`
- `reference_image_manager.py`

**核心要点**: Shot生成必须 `use_pro_model=True`

---

### prompt-engineering.md

**触发词**: image_prompt, 中文泄露, 风格, StyleEnforcer, 全英文

**触发文件**:
- `storyboard_prompts.py`
- `storyboard_director.py`
- `style_enforcer.py`

**核心要点**: 图像Prompt必须全英文

---

### context-management.md

**触发场景**:
- 新会话开始
- 多agent协作
- 上下文混乱时

**核心要点**: 渐进式披露，按需加载

---

## Loading Strategy

```
任务复杂度 → 加载深度

Simple (bug fix):
  └── 只读 agent定义

Medium (new feature):
  └── agent定义 + 相关skill摘要

Complex (architectural change):
  └── agent定义 + 相关skill完整内容 + claude.md
```

---

## Integration with .team-brain

Skills提供**约束和方法论**，.team-brain提供**状态和协作**：

```
/.claude/skills/           # 怎么做（约束、规范）
  ├── character-consistency.md
  ├── prompt-engineering.md
  └── context-management.md

/.team-brain/              # 做什么（状态、任务）
  ├── status/              # 当前状态
  ├── handoffs/            # 交接任务
  └── knowledge/           # 积累的经验
```

---

## For Each Agent

| Agent | 必读Skills | 选读Skills |
|-------|-----------|-----------|
| pm | context-management | - |
| backend | character-consistency | prompt-engineering |
| frontend | - | context-management |
| tester | character-consistency | - |
| ai-ml | character-consistency, prompt-engineering | context-management |
| devops | - | context-management |
