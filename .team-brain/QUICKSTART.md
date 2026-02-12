# 团队协作系统 - 快速启动指南

> 最后更新: 2026-02-03

---

## 首次配置（只需一次）

### 激活插件

在任意 Claude Code 终端执行：

```bash
cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story
claude

# 激活核心插件
/plugin install commit-commands@claude-plugins-official
/plugin install code-review@claude-plugins-official
/plugin install feature-dev@claude-plugins-official
/plugin install frontend-design@claude-plugins-official
/plugin install pr-review-toolkit@claude-plugins-official
/plugin install hookify@claude-plugins-official
```

---

## 系统概览

```
/.claude/agents/                 # Agent 定义和进度
├── maincoordinator.md           # 主会话协调者 (创始人兼技术负责人)
├── pm.md                        # 产品经理
├── backend.md                   # 后端开发
├── frontend.md                  # 前端开发
├── tester.md                    # 测试工程师
├── ai-ml.md                     # AI/ML 专家
├── devops.md                    # 运维工程师
└── {agent}-progress/            # 各 Agent 进度目录
    ├── current.md               # 当前任务
    ├── completed.md             # 已完成
    └── context-for-others.md    # 给其他agent的信息

/.team-brain/                    # 团队共享大脑
├── TEAM_PROTOCOL.md             # 协作协议 (必读)
├── QUICKSTART.md                # 本文件
├── context/                     # 技术栈等共享上下文
│   └── TECH_STACK.md            # 技术栈速查
├── status/                      # 状态文件
│   ├── PROJECT_STATUS.md        # 项目状态看板
│   └── TODAY_FOCUS.md           # 今日重点
├── handoffs/                    # 交接区
│   └── PENDING.md               # 待处理交接
├── decisions/                   # 决策记录
│   └── DECISIONS.md             # 重要决策
└── daily-sync/                  # 每日同步
    └── YYYY-MM-DD.md            # 日报
```

---

## 各 Agent 启动方式

> **原则**: 每个 Agent = 一个独立的终端窗口 + Claude Code 会话

### 主会话协调者 (创始人) - Claude Code 主终端

```bash
cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story
claude

# 启动方式:
@agent-xuhuastory-boss-coordinator

# 或者直接说:
请阅读 /.claude/agents/maincoordinator.md 了解你的角色，
然后按照启动指令开始工作。
```

### PM (产品经理)

```bash
cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story
claude

# 启动 prompt:
请阅读 /.claude/agents/pm.md 了解你的角色和职责，
然后阅读 /.team-brain/status/TODAY_FOCUS.md 了解今日任务。

# PM 专属插件命令:
# /feature-dev [功能描述]  - 引导功能开发
# /commit                   - 提交变更
```

### Backend Agent

```bash
cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story
claude

# 启动 prompt:
请阅读 /.claude/agents/backend.md 了解你的角色和职责，
然后阅读 /.team-brain/status/TODAY_FOCUS.md 了解今日任务。

# Backend 专属插件命令:
# /feature-dev [功能描述]  - 结构化功能开发
# /code-review             - 审查 PR
# /commit                  - 提交代码
# /commit-push-pr          - 创建 PR
```

### Frontend Agent

```bash
cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story
claude

# 启动 prompt:
请阅读 /.claude/agents/frontend.md 了解你的角色和职责，
然后阅读 /.team-brain/status/TODAY_FOCUS.md 了解今日任务。

# Frontend 专属插件:
# frontend-design          - 自动触发，生成高质量 UI
# /commit                  - 提交代码
# /commit-push-pr          - 创建 PR
```

### Tester Agent

```bash
cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story
claude

# 启动 prompt:
请阅读 /.claude/agents/tester.md 了解你的角色和职责，
然后阅读 /.team-brain/status/TODAY_FOCUS.md 了解今日任务。

# Tester 专属插件命令:
# /code-review             - 自动审查 PR
# pr-review-toolkit        - 6个专业审查 agent（自动触发）
```

### AI_ML Agent

```bash
cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story
claude

# 启动 prompt:
请阅读 /.claude/agents/ai-ml.md 了解你的角色和职责，
然后阅读 /.team-brain/status/TODAY_FOCUS.md 了解今日任务。

# AI_ML 专属插件命令:
# /commit-push-pr          - Prompt 变更后创建 PR
# /code-review             - 审查 Prompt 相关代码
```

### DevOps Agent

```bash
cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story
claude

# 启动 prompt:
请阅读 /.claude/agents/devops.md 了解你的角色和职责，
然后阅读 /.team-brain/status/TODAY_FOCUS.md 了解今日任务。

# DevOps 专属插件命令:
# /hookify [规则描述]      - 创建安全防护规则
# /hookify:list            - 查看已有规则
# /hookify:configure       - 配置规则
```

---

## 每日工作流程

### 1. 晨会 (主会话协调者/PM 执行)

```
08:00 更新 TODAY_FOCUS.md
08:15 各 Agent 阅读 TODAY_FOCUS.md
08:30 开始工作
```

### 2. 工作中

```
各 Agent:
- 执行分配的任务
- 完成任务时更新各自的 progress/current.md
- 完成任务后追加消息到 TEAM_CHAT.md（追加模式）
- 需要交接时通知 PM 更新 PENDING.md
```

### 3. 收工

```
17:00 各 Agent 更新 daily-sync/YYYY-MM-DD.md（追加模式）
17:30 PM 汇总进度到 PROJECT_STATUS.md
18:00 PM 准备明日计划到 TODAY_FOCUS.md
```

---

## Agent 间协作示例

### 示例 1: Backend 完成 API，通知 Frontend

```markdown
# 在 /.team-brain/handoffs/PENDING.md 添加:

### HANDOFF-2026-01-06-001

**From**: @Backend
**To**: @Frontend
**Priority**: P1
**Status**: 🔴 待接收

#### 背景
视频合成 API 已完成

#### 已完成的工作
- [x] POST /api/videos/generate
- [x] GET /api/videos/{id}
- [x] GET /api/videos/{id}/status

#### 需要接手的工作
- [ ] 前端对接这些 API
- [ ] 添加进度显示

#### 关键文件
| 文件 | 说明 |
|------|------|
| /app/api/videos.py | API 端点 |
| /docs/api/videos.md | API 文档 |

#### 验收标准
- [ ] 前端能调用 API
- [ ] 进度正确显示
```

---

## 常见问题

### Q: Agent 不记得之前的上下文怎么办？

每次新对话开始时，让 Agent 重新阅读其定义文件:
```
请阅读 /.claude/agents/{agent}.md 恢复你的角色上下文
```

### Q: 如何确保信息同步？

1. 完成任务后追加消息到 TEAM_CHAT.md（追加模式，不会覆盖）
2. 各 Agent 开工前必读 TODAY_FOCUS.md 和 PENDING.md
3. 交接通过 PENDING.md 传递（由PM统一更新）
4. 详见 TEAM_PROTOCOL.md 的"TEAM_CHAT.md 追加模式协议"

### Q: 一个 Agent 被阻塞了怎么办？

1. 在 PENDING.md 记录阻塞原因
2. @PM 或主会话协调者解决
3. 阻塞方主动推进

---

## 成功标准

```
✅ 各 Agent 清楚自己的职责
✅ 信息在共享文件中流动
✅ 阻塞问题及时暴露和解决
✅ 每日进度可追踪
✅ 决策有记录可查
```

---

## 迭代优化

这个系统会随着使用不断完善：

1. 发现流程问题 → 更新 TEAM_PROTOCOL.md
2. Agent 定义不足 → 补充 /.claude/agents/{agent}.md
3. 新的协作模式 → 记录到 DECISIONS.md

**持续改进是关键！**
