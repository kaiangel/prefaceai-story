---
name: Ben 远程协作方案（完整版）
description: Ben 加入项目的协作架构、工具兼容性分析、领域划分、Git 工作流、Agent 团队设计、通讯协议和执行清单
type: project
---

## 背景（2026-03-18 Founder 与 Coordinator 讨论确定）

Founder 的人类合伙人 Ben（CTO 级别，安居客/车轮技术总监/CTO）加入序话Story 项目。Ben 使用 OpenAI Codex CLI（因地理因素无法使用 Claude Code），每周投入 6-12 小时。项目需要设计一套让 Ben + Codex 与 Founder + Claude Code 7 Agent 团队高效协作的方案。

**Why:** Ben 的后端/数据库/架构经验是项目下一阶段（用户系统、计费、API 正式化）的关键能力补充。但两个不同的 AI 工具生态（Claude Code vs Codex）+ 两个人同时开发，需要严谨的协作架构。

**How to apply:** 任何涉及 Ben 的任务派发、代码集成、工具选择、沟通协调都应参考此方案。

---

## 一、核心协作架构：双团队独立 + 直接 push main

```
┌─────────────────────────────┐     ┌─────────────────────────────┐
│   Founder 团队 (Claude Code) │     │   Ben 团队 (Codex)           │
│                              │     │                              │
│  Coordinator (Founder)       │     │  Ben (人类)                  │
│  ├── PM                     │     │  ├── Codex Session 1: 后端   │
│  ├── Backend                │     │  ├── Codex Session 2: 测试   │
│  ├── AI-ML                  │     │  ├── Codex Session 3: 运维   │
│  ├── Frontend               │     │  └── Codex Session 4: DB专家 │
│  ├── Tester                 │     │                              │
│  └── DevOps                 │     │                              │
└──────────┬──────────────────┘     └──────────┬───────────────────┘
           │                                    │
           │         ┌──────────┐               │
           └────────►│  GitHub   │◄──────────────┘
                     │  main    │
                     │ 直接push │
                     └──────────┘
                          ▲
                     ┌────┴────┐
                     │ 沟通桥梁 │
                     │ WeChat  │
                     │ TEAM_CHAT│
                     └─────────┘
```

### 独立运作的原因
1. **零冲突**: 两边各管各的文件/目录，不互踩
2. **工具隔离**: Claude Code 和 Codex 各做各的，不需要互相兼容
3. **决策清晰**: Pipeline/Prompt/前端 = Founder 拍板，后端架构/DB = Ben 拍板
4. **节奏独立**: Founder 全职推进，Ben 每周 6-12 小时，互不阻塞
5. **集成简单**: 两人直接 push main，分工不同冲突概率极低

---

## 二、工具兼容性分析（Codex vs Claude Code）

### Claude Code 原生的系统 vs Codex 兼容性

| 系统 | Claude Code | Codex 兼容性 |
|------|------------|-------------|
| `CLAUDE.md` 自动读取 | ✅ 启动自动加载 | ❌ 不读此文件，需用 `AGENTS.md` 或自定义 |
| `.claude/agents/*.md` 角色定义 | ✅ 原生 Agent 系统 | ❌ 不认，有自己的 Skills 系统 |
| Session 恢复 `--resume` | ✅ 原生 | ✅ Codex 有类似机制 |
| 持久记忆 `.claude/projects/*/memory/` | ✅ 原生 | ❌ 无等价物 |
| 多 Agent 并行 | ✅ 7 个独立 session | ⚠️ 可多终端，无原生 Agent 定义体系 |
| Progress 文件自动更新 | ✅ Agent 自动写 | ❌ 需要人工或脚本 |

### 结论：不需要做完整"兼容层"

**原因**: Ben 的工作领域是新模块开发（数据库/用户系统/计费）+ 运营技术支撑，不碰 Pipeline 和 Prompt。他不需要理解 33 条 Prompt 约束、NB2 vs Pro 模型选择等 Claude Code 深度上下文。

**实际需要做的**:
1. 创建 `.team-brain/team_ben/CODEX.md` — Ben 的 Codex 启动时读取的上下文文件（浓缩项目关键信息）
2. `.team-brain/team_ben/` 目录 — 存放 Ben 的 Agent instruction 文件
3. Codex 可以读取仓库中所有 .md 文件，Ben 需要时可以让 Codex 搜索/阅读

**工作量评估**: 对 Agent 来说约 30 分钟，不是大工程。

---

## 三、领域划分（正式版）

| 领域 | 负责人 | Agent 团队 | 说明 |
|------|--------|-----------|------|
| Pipeline (Stage 1-5) | Founder | Claude Code agents | 核心 AI 生成能力，3 个月深度上下文 |
| Prompt 工程 | Founder | AI-ML agent | 所有 prompt 相关 |
| 前端 | Founder | Frontend agent | UI/UX + 组件开发 |
| 产品方向/决策 | Founder | PM agent | DEC-xxx 系列决策 |
| **数据库/用户系统** | **Ben** | **Codex agents** | **从零搭建，新模块** |
| **API 架构/计费** | **Ben** | **Codex agents** | **新模块** |
| **运营/市场技术** | **Ben** | **Codex agents** | **数据分析、AB 测试等** |
| 基础设施/DevOps | 共同 | 各自的 DevOps agent | 重大变更需双方同意 |

---

## 四、Git 工作流

**分支策略**:
```
main (两人都直接 push)
```

- 两人（Founder + Ben）都直接 push 到 `main` 分支
- 分工不同，代码冲突概率极低；如有冲突，两人沟通解决后再 push
- **Push 节奏**: 每次工作 session（阶段性）结束后 push

---

## 五、Ben 的 Agent 团队设计

### 4 个 Agent（Codex 多终端 + 专用 instruction 文件）

| Agent | 角色 | Instruction 文件 | 说明 |
|-------|------|-----------------|------|
| Backend-B | 后端开发 | `.team-brain/team_ben/backend-b.md` | API 开发、服务实现 |
| DB-Expert | 数据库专家 | `.team-brain/team_ben/db-expert.md` | Schema 设计、迁移、查询优化 |
| Tester-B | 测试工程 | `.team-brain/team_ben/tester-b.md` | Ben 负责模块的测试 |
| DevOps-B | 运维 | `.team-brain/team_ben/devops-b.md` | Ben 负责模块的部署、CI/CD |

### 暂不需要 PM-B
- Ben 每周 6-12 小时，项目管理开销应最小化
- 和 Founder 直接微信沟通就足够协调
- 如果后续工作量增大，再加

### MacBook 配置不是瓶颈
- Codex 调用远程 API，本地资源消耗不大
- 4 个终端 session 同时跑没问题
- 瓶颈在 API 额度而非硬件

---

## 六、通讯协议

### 双通道

| 通道 | 用途 | 参与者 |
|------|------|--------|
| 微信 | 实时讨论、快速同步、决策碰撞 | Founder + Ben (人对人) |
| TEAM_CHAT.md | 正式项目记录、任务完成通知、PR 通知 | 所有 Agent + Founder + Ben |

### Ben 在 TEAM_CHAT 中的标签: `@ben`

Ben 只需要在以下情况写 TEAM_CHAT:
- 完成了一个功能/模块
- 提了 PR
- 遇到需要协调的问题
- **不需要**像 AI Agent 那样更新 progress 文件（对人类太繁琐）

---

## 七、Onboarding 包

### 7.1 核心文件: `.team-brain/team_ben/CODEX.md`

内容:
- 项目概述（序话Story 是什么、做什么）
- 技术架构全景图（5 阶段 Pipeline 简述 + 支撑服务）
- Ben 的职责范围（明确管什么、不碰什么）
- 代码规范（async/await、错误处理、日志格式、文件命名）
- Git 工作流（分支策略、PR 流程）
- 通讯协议（TEAM_CHAT.md 格式、@ben 标签）
- 关键决策摘要（DEC-001~014 一句话版本）
- 环境变量和部署信息
- **不包含**: Prompt 约束、StyleEnforcer 细节、NB2 vs Pro 选择逻辑等 Pipeline 专属信息

### 7.2 推荐阅读清单

**第一层: 必读（开工前）** ⏱️ ~1 小时
1. `.team-brain/team_ben/CODEX.md`（专为 Ben 创建的上下文文件）
2. `CLAUDE.md` 前半部分（项目状态 + 产品定位 + 技术架构，跳过 Prompt 细节）
3. `.team-brain/status/PROJECT_STATUS.md`（项目全貌）
4. `.team-brain/decisions/DECISIONS.md`（浏览关键决策）

**第二层: 了解团队（第一周内）** ⏱️ ~2 小时
5. `.team-brain/TEAM_PROTOCOL.md`（协作协议）
6. 各 Agent 的 `context-for-others.md`（6 个文件）
7. `.team-brain/status/TODAY_FOCUS.md`
8. DevOps 的 `current.md`（运维风险清单，和 Ben 工作直接相关）

**第三层: 深入了解（需要时查阅）**
9. 各 Agent 的 `completed.md`
10. `TEAM_CHAT.md`（让 Codex 搜索关键词，不需全文阅读）
11. `docs/` 目录下的技术文档

### 7.3 通知 Ben 的方式

Founder 在微信上发消息，告知:
1. git pull 最新代码
2. 先读 `.team-brain/team_ben/CODEX.md`
3. 按阅读清单花 1-2 小时了解项目
4. 第一个任务建议从用户数据库层开始
5. 直接 push 到 `main` 分支
6. 有问题微信聊或在 TEAM_CHAT.md 留言

---

## 八、Ben 的 Vibe Coding 学习路径

### 推荐第一个任务: 用户数据库层

**选择原因**:
1. Ben 最擅长的领域（数据库/后端架构）— 用熟悉领域学新工具
2. 完全自包含 — 新建 `app/database/` 目录，不碰任何现有文件
3. 零冲突风险 — 不影响 Pipeline、不影响 Prompt
4. 有明确交付物 — Schema + Migration + 基础 CRUD API
5. 后续扩展性 — 用户系统、计费、故事持久化都基于这个

### 具体起步内容

```
Ben 的第一个 PR:
├── app/database/
│   ├── models.py          # SQLAlchemy/SQLModel 数据模型
│   ├── connection.py       # DB 连接管理
│   ├── migrations/         # Alembic 迁移
│   └── crud.py            # 基础 CRUD 操作
├── tests/test_database/
│   └── test_models.py     # 模型测试
└── docs/DATABASE_DESIGN.md # 设计文档
```

**技术选型建议（Ben 来定）**:
- PostgreSQL（生产级关系型数据库）
- SQLModel 或 SQLAlchemy（FastAPI 生态）
- Alembic（数据库迁移）
- Redis 已有（可复用做缓存）

### 不推荐的起步方式
- 一上来就改现有 Pipeline 代码（上下文太深，风险太高）
- 直接用不熟悉的工具改别人的 Prompt（有很多隐性约定）

---

## 九、执行清单

### 立即执行（在 Ben 开始前）

| # | 事项 | 负责 | 工作量 | 状态 |
|---|------|------|--------|------|
| 1 | 创建 `.team-brain/team_ben/CODEX.md` | Coordinator/PM agent | ~30 分钟 | ✅ 已完成 |
| 2 | 创建 `.team-brain/team_ben/` 目录 + 4 个 instruction 文件 | Coordinator/PM agent | ~30 分钟 | ⏳ |
| 3 | ~~GitHub branch protection~~ 已取消 — 两人直接 push main | - | - | ✅ 不需要 |
| 4 | 更新 TEAM_PROTOCOL.md 加入 @ben 和双团队协议 | PM agent | ~15 分钟 | ⏳ |
| 5 | Founder 微信通知 Ben + 发送阅读清单 | Founder (人工) | 5 分钟 | ⏳ |

### Ben 开始后

| # | 事项 | 负责 | 时机 |
|---|------|------|------|
| 6 | Ben 读完 .team-brain/team_ben/CODEX.md + 阅读清单 | Ben | 第一天 |
| 7 | Ben 搭建数据库层 (第一个 PR) | Ben + Codex | 第一周 |
| 8 | Founder/PM review Ben 的 PR | Founder 团队 | Ben 提 PR 后 |
| 9 | 根据体验调整协作流程 | Founder + Ben | 持续 |

---

## 十、Founder 在讨论中表达的关键观点

1. **工具选择**: 理解 Codex 也能读取项目文档，认为不一定需要完整兼容层
2. **领域划分**: 同意独立团队，强调各自用独立于对方的属于自己的 Agent
3. **Ben 不碰 Prompt 和 Pipeline**: 明确说明"他一般不改 prompt，目前暂时也不会动 pipeline"
4. **文档共享**: 希望把所有 agent 相关文档共享给 Ben，让 Codex 逐字阅读来最大程度对齐
5. **Git 工作流**: 两人都直接 push 到 main，无分支保护
6. **决策权**: Founder 自认产品经理能力 + 优秀审美/UI/UX/前端审核能力；后端/DB/架构更多听 Ben
7. **通讯**: 微信 + TEAM_CHAT.md 双通道
