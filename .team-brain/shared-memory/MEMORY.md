# 序话Story 项目记忆

## 关键教训

### 任务派发必须具体化（2026-02-26 Founder 指出）

**事件**: TASK-MODEL-UPGRADE Step 3 要求 Backend "跑一个简短故事验证"，未指定风格参数。Backend 使用代码默认值 `realistic`，但 DEC-012 决策 3 选择了 Slam Dunk 风格。

**教训**:
- 任务派发**必须**包含所有关键测试参数（风格、模型、数据集等），不留歧义
- 不要假设执行者会推断上下文意图 — 他们会遵循代码默认值
- 验证测试任务尤其重要：明确 what to test、with what parameters、expected outcome
- 派发前自查：参数是否完整？有没有隐含假设？执行者能否无歧义执行？
- 如果新决策改变了默认行为，派发任务时必须明确指出

### PM 不可直接操作代码文件（2026-03-04 回滚事故）

**事件**: PM 尝试回滚自己对 `storyboard_director.py` 的代码修改，执行 `git checkout -- storyboard_director.py`，结果将整个文件恢复到 HEAD 状态，误删了 AI-ML 此前所有改动（SQ-4/SQ-5/Bug#3 Rule#6）。AI-ML 不得不重新应用全部改动。

**教训**:
- PM 角色**不应直接修改或操作代码文件**，代码修改应派发给对应的专业 Agent
- `git checkout -- <file>` 会将整个文件恢复到 HEAD，不区分"谁的改动"——同一文件上所有未提交的改动都会丢失
- 即使 Founder 要求"回滚"，正确做法是派发给原作者或让 DevOps 处理，而非 PM 自己执行
- 如果 PM 确实需要撤销自己的代码尝试，应先确认该文件上是否有其他人的未提交改动

### 不要过早将问题归为"模型限制"（2026-03-04 Founder 指出）

**事件**: PM 将 Shot 15（手机叠菜）和 Shot 18（筷子归属）归为"NB2 模型限制"。Founder 挑战此结论，PM 重新分析后发现根因在 Stage 4 prompt 规则缺失——LLM 生成了有歧义的构图描述，图像模型只是忠实执行。

**教训**:
- 遇到图像生成质量问题，先排查我们可控的 prompt 工程层面，再考虑模型限制
- 特别是 Stage 4 StoryboardDirector 的 IMAGE PROMPT QUALITY REQUIREMENTS — 这是我们能控制的"指令层"

## 文档更新权限协议

**重要**：共享文档由 PM 统一更新，Frontend 不可直接修改：
- `PENDING.md` — PM 维护
- `PROJECT_STATUS.md` — PM 维护
- `DECISIONS.md` — PM 维护

Frontend 可更新的文档：
- `frontend-progress/current.md`、`context-for-others.md`、`completed.md`
- `TEAM_CHAT.md`（仅追加消息通知）

### 任务派发必须尊重专业分工（2026-03-05 Founder 指出）

**事件**: PM 将 TASK-PROMPT-BUBBLE 整体派发给 AI-ML，包括 2×10-shot 生图测试。但生图测试应由 Backend 或 Tester 执行，AI-ML 专长是 prompt 工程。

**教训**:
- **术业有专攻** — 每个 Agent 做好自己专业的事情
- AI-ML: prompt 设计/优化（storyboard_prompts.py, style_enforcer.py）
- Backend: 服务代码集成 + 生图测试（image_generator.py, pipeline）
- Tester: 独立验证（不同数据集/风格复测）
- PM: 审查/协调/文档，不越界做代码或测试
- 派发任务时先想清楚：这个任务的核心能力要求是什么？谁最专业？
- 不要图省事把跨专业的工作打包给一个 Agent

### Commit message 必须覆盖完整代码范围（2026-03-14 PM 复核指出）
- [详见](feedback_commit_message_scope.md)：commit 包含多批变更时，message 必须全部标注，不能遗漏

## Founder 偏好

- **子代理模型选择**：不用 Haiku，最低用 Sonnet 4.6，优先默认继承 Opus 4.6（Haiku 与 Opus 差距太大）
- **不要主动删除任何文件** — [详见](feedback_no_delete_without_confirm.md)：清理/删除必须先报告，经 Founder/PM/Coordinator 确认后才执行
- **Founder 的能力画像**：偏向优秀产品经理，兼有优秀审美的 UI/UX 及前端开发审核能力；后端/DB/架构方面更多听合伙人 Ben 的意见

## 合伙人 Ben（人类，2026-03-18 加入讨论）

- [Ben 画像](user_ben_cofounder.md)：CTO 级别，安居客/车轮技术总监/CTO，后端+数据库+架构，用 Codex（地理因素无法用 Claude）
- [远程协作方案](project_ben_collaboration_plan.md)：双团队独立 + Git PR 桥接，领域划分，Agent 团队设计，Onboarding，执行清单（完整方案）
- [Codex 兼容性分析](project_codex_compatibility.md)：OpenAI Codex CLI vs Claude Code 技术差异和解决方案

**关键决策**：
- Ben 用 Codex（地理因素无法用 Claude），不需要做完整兼容层，只需创建 `CODEX.md`
- 双团队独立运作：Founder 管 Pipeline/Prompt/前端/产品，Ben 管 数据库/API架构/运营技术
- Git 必须升级分支保护（P0，Ben 动代码前完成）
- Ben 的第一个任务建议：从零搭建用户数据库层（`app/database/`，自包含零冲突）
- Ben 不碰 Prompt 和 Pipeline（明确说明暂时不会动）

## 待办技术决策

- [生产环境 MySQL 迁移](project_mysql_migration.md)：合伙人要求生产用 MySQL，当前 SQLite + SQLAlchemy ORM，切换成本低（3 步），P2 优先级

## 项目结构快速参考

- Frontend: `frontend/src/` (Next.js 14)
- Backend: `app/services/`
- Team docs: `.team-brain/` (TEAM_CHAT, PENDING, TODAY_FOCUS, PROJECT_STATUS)
- Agent progress: `.claude/agents/{agent}-progress/` (current, context-for-others, completed)
- Daily sync: `.team-brain/daily-sync/`
- Decisions: `.team-brain/decisions/DECISIONS.md`
