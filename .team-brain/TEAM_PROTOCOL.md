# 序话Story 团队协作协议

## 团队成员

| Agent | 角色 | 职责范围 | CLAUDE.md 位置 |
|-------|------|---------|---------------|
| PM | 产品经理 | 需求分析、优先级、协调、验收 | Claude Web |
| Backend | 后端开发 | FastAPI、Services、Phase 4 | /app/CLAUDE.md |
| Frontend | 前端开发 | Next.js、React、UI/UX | /frontend/CLAUDE.md |
| Tester | 测试工程师 | 单元测试、E2E、回归 | /tests/CLAUDE.md |
| AI_ML | AI/ML专家 | Prompt、模型优化、一致性 | /app/prompts/CLAUDE.md |
| DevOps | 运维工程师 | 部署、CI/CD、监控 | /deploy/CLAUDE.md |

---

## 核心协议

### 1. 每次开始工作前必读

```
必读文件 (按顺序):
1. /.team-brain/status/TODAY_FOCUS.md       # 今日重点（最紧急）
2. /.team-brain/handoffs/PENDING.md         # 待处理的交接
3. /.team-brain/status/PROJECT_STATUS.md    # 项目当前状态
4. /claude.md                                # 项目核心约束
```

### 2. 每次完成工作后必更新

```
必更新文件（按并行任务协议执行）:

【所有Agent必须更新】
1. /.claude/agents/{你}-progress/current.md      # 更新当前状态
2. /.claude/agents/{你}-progress/completed.md    # 记录完成的任务
3. /.claude/agents/{你}-progress/context-for-others.md  # 写明需要PM汇总的内容

【追加模式】
4. /.team-brain/daily-sync/YYYY-MM-DD.md    # 追加今日工作（不覆盖他人）
5. /.team-brain/decisions/DECISIONS.md      # 追加重要决策（不覆盖他人）

【追加模式 - 各Agent自行追加】
• /.team-brain/TEAM_CHAT.md                 # ⭐ 追加模式，详见下方协议

【⚠️ 禁止直接编辑 - 由PM统一更新】
• /.team-brain/handoffs/PENDING.md          # 写入context-for-others.md，PM会汇总
• /.team-brain/status/PROJECT_STATUS.md     # 写入context-for-others.md，PM会汇总
• /.team-brain/status/TODAY_FOCUS.md        # 写入context-for-others.md，PM会汇总
```

### 3. 交接协议

当你的工作需要其他 Agent 接手时：

```markdown
## 交接模板
### From: [你的角色]
### To: [目标角色]
### Date: YYYY-MM-DD

#### 背景
[为什么需要交接]

#### 完成的工作
[你做了什么]

#### 需要接手的工作
[对方需要做什么]

#### 关键文件
- file1.py: [说明]
- file2.ts: [说明]

#### 注意事项
[踩过的坑、特别提醒]

#### 验收标准
[如何判断完成]
```

### 4. 决策记录协议

重要决策必须记录：

```markdown
## 决策模板
### 决策编号: DEC-YYYY-MM-DD-XXX
### 决策者: [角色]
### 影响范围: [哪些模块/Agent]

#### 问题
[要解决什么问题]

#### 方案选项
1. 方案A: [描述] - 优点/缺点
2. 方案B: [描述] - 优点/缺点

#### 最终决策
[选择了什么，为什么]

#### 后续行动
- [ ] Action 1 (负责人)
- [ ] Action 2 (负责人)
```

---

## 沟通规范

### Agent 间引用格式

```
@Backend: 需要你提供 /api/videos 的接口文档
@Frontend: 这个 API 已经 ready，可以对接了
@Tester: 新功能已完成，请编写测试
@AI_ML: 这个 Prompt 效果不好，需要优化
@DevOps: 准备部署，请检查配置
@PM: 需要确认这个需求的优先级
```

### 状态标记

```
[WIP] - Work In Progress 进行中
[BLOCKED] - 被阻塞，需要等待
[READY] - 准备就绪，可以交接
[REVIEW] - 需要 Review
[DONE] - 已完成
```

---

## 🚨 并行任务时的文档更新协议（重要）

### 问题背景

当多个Agent并行执行任务时，可能同时更新共享文档（如TEAM_CHAT.md、PENDING.md），导致：
- 内容覆盖/丢失
- 版本冲突
- 信息不一致

### 解决方案：文档所有权分类（完整版）

#### 一、私有文档（各Agent独立维护，无冲突风险）

| 文档路径 | 说明 |
|---------|------|
| `.claude/agents/{agent}-progress/current.md` | 当前任务状态 |
| `.claude/agents/{agent}-progress/completed.md` | 已完成任务记录 |
| `.claude/agents/{agent}-progress/context-for-others.md` | 给其他Agent的上下文 |

#### 二、共享文档 - 高频更新

| 文档路径 | 更新方式 | 说明 |
|---------|---------|------|
| `.team-brain/TEAM_CHAT.md` | ⭐ **追加模式** | 各Agent自行追加，详见下方协议 |
| `.team-brain/handoffs/PENDING.md` | PM统一更新 | 写入context-for-others.md，PM会汇总 |
| `.team-brain/status/TODAY_FOCUS.md` | PM统一更新 | 写入context-for-others.md，PM会汇总 |
| `.team-brain/status/PROJECT_STATUS.md` | PM统一更新 | 写入context-for-others.md，PM会汇总 |

#### 三、共享文档 - 谁创建谁维护（文件名需包含创建者标识）

| 文档路径 | 命名规则 | 示例 |
|---------|---------|------|
| `.team-brain/analysis/*.md` | `{主题}_{AGENT}.md` | `V2_COMPREHENSIVE_ANALYSIS_PM.md` |
| `.team-brain/handoffs/HANDOFF-*.md` | `HANDOFF-{日期}-{编号}-{主题}.md` | `HANDOFF-2026-01-30-011-CC-KAI-STORY.md` |
| `.team-brain/handoffs/{专题}*.md` | `{专题}_{目标AGENT}.md` | `BOOK_PROMPT_TASK_FOR_AIML.md` |
| `test_output/**/acceptance_report*.md` | 测试验收报告 | Tester创建和维护 |

#### 四、共享文档 - 低频更新（需Coordinator批准或团队协商）

| 文档路径 | 说明 | 修改条件 |
|---------|------|---------|
| `.claude/agents/{agent}.md` | Agent角色定义 | 需Coordinator批准 |
| `.team-brain/TEAM_PROTOCOL.md` | 团队协作协议（本文档） | 需Coordinator批准 |
| `.team-brain/QUICKSTART.md` | 快速入门指南 | 需团队协商 |
| `.team-brain/context/TECH_STACK.md` | 技术栈说明 | 需团队协商 |
| `.team-brain/knowledge/*.md` | 知识库文档 | 谁负责该领域谁更新 |
| `.team-brain/decisions/DECISIONS.md` | 决策记录 | 任何Agent可追加，不可删改他人记录 |
| `CLAUDE.md` | 项目主文档 | 需Coordinator批准 |
| `docs/*.md` | 项目技术文档 | 需相关Agent Review |
| `ARCHITECTURE.md` | 架构文档 | 需Backend/Coordinator批准 |
| `PHASE*_COMPLETE.md` | 里程碑文档 | 需Coordinator批准 |

#### 五、特殊处理

| 文档路径 | 处理方式 |
|---------|---------|
| `.team-brain/daily-sync/YYYY-MM-DD.md` | **追加模式**：每个Agent追加自己的部分，不覆盖他人内容 |
| `test_output/**/*.md`（非验收报告） | **自动生成**：测试脚本自动生成，不需要手动协调 |
| `frontend/README.md` | Frontend独立维护 |

#### 六、文档分类速查表

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         文档分类速查                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  🟢 可以直接编辑（无需协调）:                                              │
│     • 你自己的 {agent}-progress/*.md                                     │
│     • 你创建的 analysis/*.md 和 handoffs/*.md                            │
│     • daily-sync/*.md（追加模式）                                        │
│     • TEAM_CHAT.md（⭐追加模式，只能在末尾添加）                           │
│                                                                         │
│  🟡 需要PM汇总（不要直接编辑）:                                            │
│     • PENDING.md                                                        │
│     • TODAY_FOCUS.md                                                    │
│     • PROJECT_STATUS.md                                                 │
│                                                                         │
│  🔴 需要审批（提前沟通）:                                                  │
│     • CLAUDE.md                                                         │
│     • TEAM_PROTOCOL.md                                                  │
│     • {agent}.md（角色定义）                                              │
│     • docs/*.md                                                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 并行任务执行流程

```
┌─────────────────────────────────────────────────────────────┐
│ Agent完成任务后的更新流程                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Backend / AI-ML / Tester / Frontend / DevOps:              │
│  ├── ✅ 更新 .claude/agents/{自己}/current.md               │
│  ├── ✅ 更新 .claude/agents/{自己}/completed.md             │
│  ├── ✅ 更新 .claude/agents/{自己}/context-for-others.md    │
│  ├── ✅ 追加 TEAM_CHAT.md（追加模式，只在末尾添加）          │
│  └── ❌ 不直接编辑 PENDING.md、PROJECT_STATUS.md 等          │
│                                                             │
│  PM:                                                        │
│  ├── 读取各Agent的 context-for-others.md                    │
│  ├── ✅ 追加 TEAM_CHAT.md（追加模式，与其他Agent相同）       │
│  └── 统一更新 PENDING.md、PROJECT_STATUS.md、TODAY_FOCUS.md │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### context-for-others.md 的格式要求

各Agent完成任务后，在 `context-for-others.md` 中写明：

```markdown
## 当前状态速览

状态: 🟢 完成 / 🟡 进行中 / 🔴 阻塞
刚完成: [一句话描述完成了什么]
下一步: [一句话描述下一步]
需要PM汇总: [需要写入TEAM_CHAT的内容摘要]

---

## 需要PM汇总到群聊的内容

[详细的完成报告，PM会将此内容汇总到TEAM_CHAT.md]
```

### 注意事项

1. **TEAM_CHAT.md 采用追加模式**：各Agent完成任务后自行追加消息，详见下方协议
2. **其他高频文档由PM统一更新**：PENDING/PROJECT_STATUS/TODAY_FOCUS 仍由PM汇总更新
3. **文件名包含所有者**：分析文档命名为 `{主题}_PM.md`、`{主题}_BACKEND.md` 等，避免冲突
4. **定期汇总**：PM在每个阶段结束后汇总各Agent状态，更新共享文档
5. **追加模式文档**：daily-sync、decisions、TEAM_CHAT 采用追加模式，每个Agent在文件末尾追加自己的内容，不修改他人内容
6. **低频文档修改**：修改 CLAUDE.md、TEAM_PROTOCOL.md、Agent角色定义等低频文档前，必须先与Coordinator沟通获得批准
7. **docs/*.md 修改**：修改项目技术文档时，需要通知相关Agent进行Review

---

## ⭐ TEAM_CHAT.md 追加模式协议（重要）

### 为什么改为追加模式

之前由PM统一更新TEAM_CHAT.md存在问题：
- 信息不够及时（需等PM汇总）
- PM负担过重
- 各Agent对自己的工作描述更准确

改为追加模式后：
- 各Agent完成任务后立即记录
- 信息更及时、更准确
- 并行任务时也不会冲突（只追加，不覆盖）

### 核心规则

```
1. 只能在文件末尾追加新消息
2. 不能修改、删除已有消息
3. 每条消息必须有精确时间戳（到分钟）
4. 用明确的分隔线标记消息边界
```

### 消息格式

```markdown
---

### YYYY-MM-DD HH:MM

**@agent名**:

[消息内容]

---
```

### 追加方法

使用 Edit 工具时：
- `old_string`: 文件最后的 `---` 分隔线
- `new_string`: 原分隔线 + 新消息 + 新分隔线

**示例**：
```python
Edit(
    file_path=".team-brain/TEAM_CHAT.md",
    old_string="---\n",  # 匹配文件末尾的分隔线
    new_string="""---

### 2026-02-03 14:35

**@backend**:

架构重构 ARCH-1 完成，已创建 `app/services/text_overlay_service.py`。

**完成内容**:
- 从8个测试文件整合最佳实现
- 添加strip_speaker_prefix全覆盖
- 添加alpha_composite正确透明度

下一步：ARCH-2 测试文件迁移

---
"""
)
```

### 禁止操作

- ❌ 修改他人消息
- ❌ 删除任何内容
- ❌ 在中间插入
- ❌ 修改时间戳

### 并行安全性

| 场景 | 传统编辑 | 追加模式 |
|------|---------|---------|
| A读→A写→B读→B写 | ✅ 正常 | ✅ 正常 |
| A读→B读→A写→B写 | ❌ A的内容被覆盖 | ✅ 两条消息都保留 |
| 最坏情况 | 信息丢失 | 顺序轻微错乱（可接受） |

---

## 文件命名规范

```
日期格式: YYYY-MM-DD
时间格式: HH:MM
文件命名: kebab-case (小写+连字符)

示例:
- 2025-01-05.md
- video-synthesis-api-design.md
- DEC-2025-01-05-001.md
```
