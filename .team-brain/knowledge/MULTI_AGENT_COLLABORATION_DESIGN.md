# 多 Agent 协作系统设计记录

> **日期**: 2025-01-05（2026-03-19 更新：新增 Ben 团队 3 个 Codex Agent）
> **背景**: 讨论如何为序话Story项目建立多 Agent 协作机制
> **结论**: 建立了完整的"团队大脑"系统，实现 7 + 3 = 10 Agent 双团队协作

---

## 一、Claude Code Skills/Plugins

### 1.1 已导入的 Plugins 位置

```
~/.claude/plugins/marketplaces/claude-plugins-official/
├── plugins/                    # 官方插件
│   ├── agent-sdk-dev          # Agent SDK 开发
│   ├── code-review            # 代码审查
│   ├── commit-commands        # Git 提交命令
│   ├── feature-dev            # 功能开发工作流
│   ├── hookify                # Hook 配置
│   ├── plugin-dev             # 插件开发
│   ├── pr-review-toolkit      # PR 审查
│   ├── frontend-design        # 前端设计
│   ├── ralph-wiggum           # 迭代开发循环
│   ├── explanatory-output-style  # 教育性输出
│   ├── learning-output-style  # 交互式学习
│   └── *-lsp                  # 多个 LSP 插件
└── external_plugins/          # 外部插件
    ├── stripe, firebase, supabase  # 后端服务
    ├── asana, linear, slack   # 项目管理/通信
    ├── github, gitlab         # 代码托管
    ├── playwright             # E2E 测试
    └── ...                    # 更多
```

### 1.2 激活方法

```bash
# 交互式安装
/plugin

# 命令行安装
/plugin install code-review@claude-plugins-official
/plugin install commit-commands@claude-plugins-official
/plugin install feature-dev@claude-plugins-official
```

### 1.3 使用格式

```bash
/插件名:命令名

# 示例
/commit-commands:commit          # 自动提交代码
/code-review:code-review 123     # 审查 PR #123
/feature-dev:feature-dev 描述    # 引导式功能开发
```

### 1.4 可用插件完整清单

#### 官方插件 (Official Plugins)

| 插件名称 | 命令/触发 | 功能描述 | 推荐 Agent |
|---------|----------|---------|-----------|
| **code-review** | `/code-review` | 自动 PR 代码审查，4个专业 agent 并行审查（CLAUDE.md合规、Bug检测、历史分析），置信度评分过滤误报 | Tester, Backend, Frontend |
| **commit-commands** | `/commit`<br>`/commit-push-pr`<br>`/clean_gone` | Git 工作流自动化：自动生成 commit message、一键创建 PR、清理已删除的本地分支 | All Agents |
| **feature-dev** | `/feature-dev` | 7阶段功能开发工作流：Discovery → Exploration → Questions → Architecture → Implementation → Review → Summary | PM, Backend, Frontend |
| **pr-review-toolkit** | 6个专业 agent | PR审查工具包：comment-analyzer、pr-test-analyzer、silent-failure-hunter、type-design-analyzer、code-reviewer、code-simplifier | Tester |
| **hookify** | `/hookify`<br>`/hookify:list`<br>`/hookify:configure` | 创建自定义 hooks 防止危险操作，如阻止 `rm -rf`、警告敏感文件编辑等 | DevOps |
| **agent-sdk-dev** | `/new-sdk-app` | 创建 Claude Agent SDK 应用（Python/TypeScript），包含验证 agent | Backend |
| **plugin-dev** | `/plugin-dev:create-plugin` | 7个技能帮助开发 Claude Code 插件：Hook、MCP集成、插件结构、设置、命令、Agent、Skill开发 | Backend |
| **frontend-design** | 自动触发 | 生成高质量前端界面，避免通用 AI 美学，独特设计风格 | Frontend |
| **ralph-wiggum** | `/ralph-loop`<br>`/cancel-ralph` | 迭代式 AI 开发循环，让 Claude 自动迭代直到任务完成（适合 TDD、长任务） | All Agents |
| **explanatory-output-style** | 自动（SessionStart） | 教育性输出风格，提供实现选择的洞察解释 | 学习场景 |
| **learning-output-style** | 自动（SessionStart） | 交互式学习模式，在关键决策点请求用户编写代码 | 学习场景 |

#### LSP 插件（语言服务协议）

| 插件名称 | 支持语言 | 功能 |
|---------|---------|------|
| **pyright-lsp** | Python | Python 类型检查和智能提示 |
| **typescript-lsp** | TypeScript/JS | TypeScript/JavaScript 开发支持 |
| **gopls-lsp** | Go | Go 语言开发支持 |
| **rust-analyzer-lsp** | Rust | Rust 开发支持 |
| **clangd-lsp** | C/C++ | C/C++ 开发支持 |
| **jdtls-lsp** | Java | Java 开发支持 |
| **swift-lsp** | Swift | Swift/iOS 开发支持 |
| **csharp-lsp** | C# | .NET 开发支持 |
| **php-lsp** | PHP | PHP 开发支持 |
| **lua-lsp** | Lua | Lua 脚本开发 |

#### 外部插件 (External Plugins)

| 插件名称 | 功能描述 | 推荐 Agent |
|---------|---------|-----------|
| **asana** | Asana 项目管理集成 | PM |
| **linear** | Linear 项目管理集成 | PM |
| **slack** | Slack 通信集成 | PM |
| **github** | GitHub 深度集成 | All |
| **gitlab** | GitLab 集成 | All |
| **playwright** | E2E 测试自动化 | Tester |
| **firebase** | Firebase 后端服务集成 | Backend |
| **supabase** | Supabase 后端服务集成 | Backend |
| **stripe** | Stripe 支付集成，错误解释和测试卡 | Backend |
| **context7** | 上下文管理增强 | All |
| **greptile** | 代码搜索增强 | All |
| **serena** | 语义搜索 | All |
| **laravel-boost** | Laravel PHP 框架支持 | Backend |

### 1.5 各 Agent 推荐插件配置

| Agent | 推荐激活的插件 |
|-------|---------------|
| **PM** | commit-commands, feature-dev, asana/linear, slack |
| **Backend** | code-review, commit-commands, pyright-lsp, firebase/supabase |
| **Frontend** | commit-commands, frontend-design, typescript-lsp |
| **Tester** | code-review, pr-review-toolkit, playwright |
| **AI_ML** | commit-commands, pyright-lsp |
| **DevOps** | hookify, commit-commands |

---

## 二、多 Agent 协作模式分析

### 2.1 多 Agent 协作的优势

| 优势 | 说明 |
|------|------|
| 专业分工 | 每个 agent 专注一个领域，prompt 更精准 |
| 并行处理 | 前端、后端、测试可以同时进行 |
| 上下文隔离 | 避免单个 agent 上下文过载 |
| 模拟真实团队 | 像真实开发团队一样协作 |

### 2.2 潜在挑战

| 挑战 | 说明 |
|------|------|
| 协调成本 | 需要"主控"来协调各 agent |
| 接口定义 | 前后端 agent 需要先约定 API 格式 |
| 上下文同步 | agent 之间信息传递可能丢失细节 |
| 适合大项目 | 小项目反而增加复杂度 |

### 2.3 适用场景判断

```
适合多 Agent：
├── 中大型项目（多模块、多技术栈）
├── 明确的前后端分离架构
├── 需要并行开发提高效率
└── 团队有清晰的职责划分

适合单 Agent：
├── 小型项目/快速原型
├── 全栈开发（一个人搞定）
├── 紧密耦合的功能
└── 需要快速迭代
```

---

## 三、序话Story 项目 Agent 团队配置

### 3.1 双团队 10 Agent 配置

#### Founder 团队（Claude Code，7 个 Agent）

```
┌─────────────────────────────────────────────────────────┐
│                    产品经理 (PM)                        │
│         需求分析、优先级、协调、验收                     │
└──────────────────────────┬──────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  Backend    │   │  Frontend   │   │   Tester    │
│  后端开发   │   │  前端开发   │   │  测试工程师 │
└─────────────┘   └─────────────┘   └─────────────┘
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────┐   ┌─────────────┐
│   AI_ML     │   │   DevOps    │
│  AI/ML专家  │   │  运维工程师 │
└─────────────┘   └─────────────┘
```

配置文件位置：`.claude/agents/`

#### Ben 团队（OpenAI Codex CLI，3 个 Agent）

```
┌─────────────────────────────────────────────────────────┐
│                   pm_Ben（协调者）                      │
│         与 Founder PM 对齐、文档、任务分配               │
└──────────────────────────┬──────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
┌─────────────────────┐   ┌─────────────────────┐
│    backend_Ben      │   │    frontend_Ben      │
│  数据库/API架构/    │   │  前端联动（Ben侧）   │
│  基础设施/计费      │   │                      │
└─────────────────────┘   └─────────────────────┘
```

配置文件位置：`.team-brain/team_ben/`

> **注意**: `.team-brain/team_ben/` 目录由 Ben 团队维护，Founder 团队只读，不可修改。Ben 团队的进度文件结构与 Founder 团队相同（current.md、completed.md、context-for-others.md）。

### 3.2 各 Agent 职责

#### Founder 团队

| Agent | 职责 | 负责目录/模块 |
|-------|------|--------------|
| PM | 需求分析、优先级、协调、验收 | 全局 |
| Backend | FastAPI、Services、Phase 4 视频合成 | `/app/` |
| Frontend | Next.js、React、UI/UX | `/frontend/` |
| Tester | 单元测试、E2E、回归测试 | `/tests/` |
| AI_ML | Prompt 工程、模型优化、一致性 | `/app/prompts/` |
| DevOps | 部署、CI/CD、监控 | `/deploy/` |
| Resonance | 增长策略、内容营销、平台运营、品牌传播、用户获取 | resonance.md |

#### Ben 团队

| Agent | 职责 | 负责目录/模块 |
|-------|------|--------------|
| backend_Ben | 数据库设计、API 架构、计费系统、基础设施 | DB schema、`/api/`、infra |
| frontend_Ben | 前端联动（Ben 侧）、与 Founder Frontend 对齐 | `/frontend/`（Ben 侧功能） |
| pm_Ben | 协调 Ben 团队、文档、与 Founder PM 对齐 | `.team-brain/team_ben/`、共享记忆 |

---

## 四、团队大脑系统设计

### 4.1 核心理念：Single Source of Truth

```
所有 Agent 读写同一套文件
就像团队共用一个 Notion/飞书知识库
```

### 4.2 目录结构

```
/.team-brain/
├── TEAM_PROTOCOL.md              # 协作协议（必读）
├── QUICKSTART.md                 # 快速启动指南
├── context/                      # Agent 上下文
│   ├── AGENT_PM.md               # 产品经理
│   ├── AGENT_BACKEND.md          # 后端开发
│   ├── AGENT_FRONTEND.md         # 前端开发
│   ├── AGENT_TESTER.md           # 测试工程师
│   ├── AGENT_AI_ML.md            # AI/ML 专家
│   ├── AGENT_DEVOPS.md           # 运维工程师
│   └── TECH_STACK.md             # 技术栈速查
├── status/                       # 状态同步
│   ├── PROJECT_STATUS.md         # 项目看板
│   └── TODAY_FOCUS.md            # 今日重点
├── handoffs/                     # 交接区
│   └── PENDING.md                # 待办交接
├── decisions/                    # 决策记录
│   └── DECISIONS.md              # 重要决策
├── daily-sync/                   # 每日同步
│   └── YYYY-MM-DD.md             # 日报
└── knowledge/                    # 知识库
    ├── WEB_CONVERSATIONS_DIGEST.md  # Web 对话精华
    └── ...
```

### 4.3 协作协议核心要点

**开工前必读**：
```
1. /.team-brain/status/TODAY_FOCUS.md      # 今日重点（最紧急）
2. /.team-brain/handoffs/PENDING.md        # 待处理交接
3. /.team-brain/status/PROJECT_STATUS.md   # 项目状态
4. /claude.md                               # 核心约束
```

**完成后必更新**：
```
1. /.team-brain/status/PROJECT_STATUS.md  # 更新进度
2. /.team-brain/daily-sync/YYYY-MM-DD.md  # 记录工作
3. /.team-brain/handoffs/PENDING.md       # 如有交接
```

### 4.4 Agent 间协作方式

```markdown
# 交接模板
### From: @Backend
### To: @Frontend

#### 已完成
- [x] API 开发完成

#### 需要接手
- [ ] 前端对接 API

#### 关键文件
- /app/api/videos.py

#### 验收标准
- [ ] 前端能调用 API
```

---

## 五、PM 放置位置决策

### 5.1 问题分析

| 对比维度 | Web PM | Terminal PM |
|---------|--------|------------|
| 与 Agent 协作 | 需要复制粘贴 | 直接文件交互 |
| 更新状态文件 | 需要手动 | 直接更新 |
| 历史上下文 | Project 功能好 | 需要文件化 |
| 工作效率 | 低（切换成本） | 高（一体化） |

### 5.2 最终决策

**PM 在 Terminal + 知识迁移**

原因：
1. 消除复制粘贴的摩擦
2. 与其他 Agent 无缝协作
3. 通过知识迁移保留 Web 端的历史智慧

### 5.3 角色定位

```
你（人类）= 真正的 PM/决策者
├── 在 Terminal：直接指挥各 Agent
└── 在 Web（偶尔）：回顾历史、深度思考

Terminal PM Agent = 你的执行助理
├── 接收你的决策
├── 更新 .team-brain/ 文件
├── 通知其他 Agent
└── 汇总进度给你
```

---

## 六、知识迁移方案

### 6.1 迁移目标

把 Web 端 6 个对话的精华提取到文件系统，让 Terminal Agent 也能获得这些"记忆"。

### 6.2 提取 Prompt 设计

要求覆盖的维度：
- 产品层面：愿景、用户、功能、路线图
- 技术层面：架构、选型、难题、踩坑
- 业务逻辑：流程、数据流、规则
- 质量约束：红线、标准、指标、成本
- 进度层面：已完成、进行中、待办、风险
- 决策记录：选择、放弃、待评估
- 经验教训：成功、失败、建议

### 6.3 最终产出

```
WEB_CONVERSATIONS_DIGEST.md (917行)
├── 一、产品认知
├── 二、技术架构
├── 三、已解决的技术难题
├── 四、踩过的坑
├── 五、不可妥协的原则
├── 六、重要决策记录
├── 七、当前状态和进度
├── 八、给各 Agent 的具体指引
├── 九、未来思考
├── 十、技术债务清单
└── 附录
```

---

## 七、启动各 Agent 的方法（/agents 原生方案）

### 7.1 核心概念 - 单终端多 Agent

Claude Code 提供原生的 `/agents` 命令，支持在**单个终端**内调用不同的专业 Agent，无需开启 6 个终端窗口。

```
旧方案：6 个终端窗口，每个窗口手动注入角色 prompt
新方案：1 个终端窗口，通过 @agent 或自动委派调用子 Agent
```

**优势对比**：

| 方面 | 旧方案（6终端） | 新方案（/agents） |
|------|----------------|------------------|
| 窗口数量 | 6 个独立终端 | 1 个终端 |
| 角色切换 | 手动切换窗口 | @agent 或自动委派 |
| 上下文 | 每个终端独立 | 子 Agent 有独立上下文 |
| 工具权限 | 相同 | 可为每个 Agent 定制 |
| 技能配置 | 全局共享 | 每个 Agent 可配置专属技能 |

### 7.2 Agent 配置文件

所有 Agent 配置存放在 `.claude/agents/` 目录：

```
/.claude/agents/
├── pm.md          # 产品经理
├── backend.md     # 后端开发
├── frontend.md    # 前端开发
├── tester.md      # 测试工程师
├── ai-ml.md       # AI/ML 专家
└── devops.md      # 运维工程师
```

### 7.3 Agent 配置格式

每个 Agent 配置文件由 **YAML 前置配置** + **System Prompt** 组成：

```markdown
---
name: backend
description: 后端开发专家，负责 FastAPI、业务逻辑、视频合成。
tools: Read, Edit, Write, Bash, Grep, Glob
model: sonnet
skills: code-review, feature-dev
---

你是序话Story项目的后端开发专家 (Backend)。

## 职责范围
...
```

**YAML 字段说明**：

| 字段 | 说明 | 示例 |
|------|------|------|
| `name` | Agent 名称（用于 @召唤） | `backend` |
| `description` | 功能描述（用于自动委派判断） | `后端开发专家...` |
| `tools` | 可用工具（权限控制） | `Read, Edit, Write, Bash` |
| `model` | 使用的模型 | `sonnet`, `opus`, `haiku` |
| `skills` | 关联的技能/插件 | `code-review, feature-dev` |

### 7.4 7 个 Agent 配置详情

| Agent | 描述 | 工具 | 技能 |
|-------|------|------|------|
| **pm** | 产品经理：需求分析、优先级、协调、验收 | Read, Glob, Grep, Bash | feature-dev |
| **backend** | 后端开发：FastAPI、业务逻辑、视频合成 | Read, Edit, Write, Bash, Grep, Glob | code-review, feature-dev |
| **frontend** | 前端开发：Next.js、React、UI/UX | Read, Edit, Write, Bash, Grep, Glob | frontend-design, code-review |
| **tester** | 测试工程师：单元测试、E2E、回归测试 | Read, Edit, Write, Bash, Grep, Glob | code-review, pr-review-toolkit |
| **ai-ml** | AI/ML专家：Prompt工程、模型优化、一致性 | Read, Edit, Write, Bash, Grep, Glob | code-review |
| **devops** | 运维工程师：部署、CI/CD、监控 | Read, Edit, Write, Bash, Grep, Glob | hookify |
| **resonance** | 市场共鸣官：增长策略、内容营销、平台运营、品牌传播、用户获取 | Read, Edit, Write, Bash, Grep, Glob | — |

### 7.5 使用方法

#### 查看可用 Agent

```bash
/agents
```

#### 显式调用 Agent

```bash
# 方式1：在消息中使用 @agent
@backend 请实现用户认证 API

# 方式2：使用 /agent 命令
/agent backend 请实现用户认证 API
```

#### 自动委派

当主 Agent 遇到与某个子 Agent 职责相关的任务时，会自动委派：

```
用户: 帮我优化图像生成的 Prompt
主 Agent: (识别到这是 AI/ML 相关任务，自动委派给 @ai-ml)
```

### 7.6 首次配置插件（只需一次）

在任意 Claude Code 终端执行插件激活：

```bash
cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story
claude

# 激活核心插件（全局生效，所有 Agent 共享）
/plugin install commit-commands@claude-plugins-official
/plugin install code-review@claude-plugins-official
/plugin install feature-dev@claude-plugins-official
/plugin install frontend-design@claude-plugins-official
/plugin install pr-review-toolkit@claude-plugins-official
/plugin install hookify@claude-plugins-official
```

### 7.7 每日工作流程

```
启动会话:
├── cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story
├── claude
└── 在单个终端内与所有 Agent 协作

工作中:
├── @pm 确认需求和优先级
├── @backend 实现后端功能
├── @frontend 实现前端界面
├── @tester 运行测试
├── @ai-ml 优化 Prompt
└── @devops 配置部署

交接:
├── Agent 间通过 /.team-brain/handoffs/PENDING.md 交接
└── 更新 /.team-brain/status/PROJECT_STATUS.md
```

### 7.8 与上下文文件的关系

```
/.claude/agents/*.md      → Agent 的角色配置和系统 Prompt（精简版）
/.team-brain/context/*.md → 详细的上下文信息和参考文档（详细版）

两者互补：
- /agents 配置定义 Agent 的核心身份和职责
- team-brain 上下文提供更详细的项目知识
- Agent 可以在工作时主动读取 team-brain 文件获取更多信息
```

---

## 八、关键文件清单

### 已创建的文件

| 文件 | 用途 |
|------|------|
| `/.team-brain/TEAM_PROTOCOL.md` | 协作协议 |
| `/.team-brain/QUICKSTART.md` | 快速启动指南 |
| `/.team-brain/context/AGENT_*.md` | 6 个 Agent 上下文 |
| `/.team-brain/status/PROJECT_STATUS.md` | 项目状态看板 |
| `/.team-brain/status/TODAY_FOCUS.md` | 今日重点 |
| `/.team-brain/handoffs/PENDING.md` | 交接区 |
| `/.team-brain/decisions/DECISIONS.md` | 决策记录 |
| `/.team-brain/daily-sync/2025-01-05.md` | 今日日报 |
| `/.team-brain/knowledge/WEB_CONVERSATIONS_DIGEST.md` | Web 对话精华 |

---

## 九、核心洞察总结

### 9.1 多 Agent 协作的关键

1. **共享知识库**：所有 Agent 读写同一套文件
2. **角色身份认同**：每个 Agent 有专属上下文
3. **信息流动机制**：状态文件 + 交接区 + 日报
4. **标准化协议**：开工必读、完成必更新

### 9.2 解决的核心问题

| 问题 | 解决方案 |
|------|---------|
| Agent 不记得项目背景 | 每次启动读取上下文文件 |
| Agent 间信息不同步 | 共享状态文件 |
| 不知道谁负责什么 | 角色定义文件 |
| 决策没有记录 | DECISIONS.md |
| 交接混乱 | PENDING.md 标准化 |
| 进度不透明 | PROJECT_STATUS.md + 日报 |

### 9.3 实施建议

```
第一步：知识迁移（已完成）
├── 把 Web 端对话精华提取到文件

第二步：启动 Terminal PM
├── PM 在 Terminal 直接协调各 Agent

第三步：逐步增加 Agent
├── 从 PM + Backend + Frontend 开始
├── 后续加入 Tester、AI_ML、DevOps

第四步：持续优化
├── 根据实际情况调整协议和模板
├── 不断完善上下文文件
```

---

## 十、后续行动项

### 已完成

- [x] 建立多 Agent 协作系统设计
- [x] 创建团队大脑文件结构
- [x] 编写 6 个 Agent 上下文文件
- [x] 从 Web 端迁移知识到 WEB_CONVERSATIONS_DIGEST.md
- [x] 整理可用插件完整清单（11个官方 + 10个LSP + 13个外部）
- [x] 为每个 Agent 配置推荐插件
- [x] 更新各 Agent 上下文文件（添加可用插件部分）
- [x] 更新 QUICKSTART.md（添加插件激活步骤）
- [x] 发现并研究 Claude Code 原生 `/agents` 功能
- [x] 创建 6 个 Agent 配置文件（`.claude/agents/`）
- [x] 更新设计文档为单终端方案

### 待完成

- [ ] 激活推荐插件（执行 `/plugin install` 命令）
- [ ] 测试 `/agents` 功能（@agent 调用）
- [ ] 启动 Frontend Agent，开始 Phase 5
- [ ] 建立定期 Review 机制
- [ ] 根据实际使用迭代协作协议

---

## 十一、关键问答

### Q: 一个 Agent 可以配多个 Skills 吗？

**A: 是的。**

```
插件激活 = 全局/项目级别
所有已激活的插件对当前会话都可用
每个 Agent 根据自己的角色选择使用哪些插件命令
```

### Q: 插件激活后如何使用？

**A: 分两种类型：**

| 类型 | 使用方式 | 示例 |
|-----|---------|-----|
| 命令型 | 手动输入斜杠命令 | `/commit`, `/code-review` |
| 技能型 | 自动触发（根据上下文） | `frontend-design`, `pr-review-toolkit` |

### Q: 如何知道一个 Agent 可用哪些插件？

**A: 查看对应的上下文文件。**

每个 `AGENT_*.md` 文件中都有"可用插件"部分，列出了推荐使用的插件和命令。

### Q: /agents 功能是什么？

**A: Claude Code 原生的子 Agent 系统。**

```
通过 .claude/agents/ 目录配置专业子 Agent
├── 每个 Agent 有独立的角色配置（YAML + System Prompt）
├── 可以通过 @agent 或 /agent 命令调用
├── 自动委派：主 Agent 识别任务类型后自动调用对应子 Agent
└── 优势：单终端管理所有 Agent，无需开多个窗口
```

### Q: Agent 可以有自己的 Skills 吗？

**A: 是的，通过配置文件的 `skills` 字段。**

```yaml
---
name: backend
skills: code-review, feature-dev  # 该 Agent 专属的技能
---
```

注意：
- 子 Agent 不会继承父 Agent 的技能
- 必须在配置中显式声明需要的技能
- 技能需要先通过 `/plugin install` 全局激活

### Q: .claude/agents/ 和 .team-brain/context/ 有什么区别？

**A: 两者互补，用途不同。**

| 目录 | 用途 | 内容 |
|------|------|------|
| `.claude/agents/` | Agent 配置 | YAML配置 + 精简System Prompt |
| `.team-brain/context/` | 详细上下文 | 完整的项目知识、技术栈、约束 |

工作方式：
1. Agent 启动时读取 `.claude/agents/` 配置获得角色身份
2. 工作时可以主动读取 `.team-brain/` 获取更多项目知识

### Q: 如何在单终端调用不同 Agent？

**A: 三种方式。**

```bash
# 1. @召唤（推荐）
@backend 请实现用户认证 API
@tester 请运行回归测试

# 2. /agent 命令
/agent frontend 请创建登录页面

# 3. 自动委派
# 直接描述任务，主 Agent 会根据任务类型自动委派
"优化图像生成的 Prompt" → 自动委派给 @ai-ml
```

---

*本文档记录了多 Agent 协作系统的设计过程和决策，是团队协作机制的元文档。*
*最后更新: 2025-01-05*
