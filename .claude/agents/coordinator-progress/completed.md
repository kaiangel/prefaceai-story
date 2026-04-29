# Coordinator 已完成事项

---

### 2026-04-28 17:50 — 8 Agent frontmatter 升级（model 分级 + effort: xhigh，DEC-023）

**任务**：基于 17:25 symlink 修复后 frontmatter 自动加载机制可用，批量升级 8 个 agent frontmatter 默认值。

**前置验证**：
- claude-code-guide agent 查证官方文档（https://code.claude.com/docs/en/sub-agents.md L234-256）
- 官方 frontmatter schema 明确支持 `effort` 字段，5 档取值（low/medium/high/xhigh/max）
- spawn 时显式传 → 覆盖 frontmatter；不传 → 用 frontmatter 默认

**升级清单**：

| Agent | model（前→后）| effort（前→后）|
|-------|-------------|---------------|
| ai-ml | opus → opus（不变）| 无 → xhigh |
| pm | opus → opus（不变）| 无 → xhigh |
| xuhuastory-boss-coordinator | opus → opus（不变）| 无 → xhigh |
| backend | opus → **sonnet** | 无 → xhigh |
| devops | opus → **sonnet** | 无 → xhigh |
| frontend | opus → **sonnet** | 无 → xhigh |
| tester | opus → **sonnet** | 无 → xhigh |
| resonance | opus → **sonnet** | 无 → xhigh（Founder 决定 sonnet）|

**校验**：8/8 grep model+effort+color 全部通过

**已知风险**：
- ⚠️ xhigh 可能是 Opus 4.7 专属（slash command 提示 "(Opus 4.7 only)"）
- Sonnet 5 个 agent 写 xhigh 可能 silent 降级到 high / 报错 / 被 ignore
- 最差也就是 Sonnet 跑 high 而不是 xhigh，**不会比之前差**

**文档同步**：
- ✅ DECISIONS.md DEC-023 完整记录
- ✅ TEAM_CHAT @all 通知
- ✅ TODAY_FOCUS / KEY_LEARNINGS / daily-sync 追加
- ✅ Coordinator progress 三件套同步

**理由**：
- 改前 8 个 agent 全部 model: opus 默认，跟 `feedback_spawn_use_sonnet_for_simple_tasks.md` 原则冲突
- effort 字段从未启用，spawn 时全跑 medium 默认
- 升级后：质量更高（xhigh 推理深度增加）+ 执行类成本降 5x（Sonnet vs Opus）

---

### 2026-04-28 — subagent_type symlink 修复 + memory 地毯式搜查

**任务**：地毯式深挖所有可能受"PM 主对话只能用内置 type"错误结论污染的文档/记忆/规则，直接修明确错误，其他位置发现汇报。

**搜查范围**（按 `feedback_carpet_review_deep_dive.md` 精神不停在 grep 一遍）：
- memory 目录全 grep（subagent_type / general-purpose / symlink / 自定义 agent / 内置 type）
- `.team-brain/` 全（含 chat-archive / status / handoffs / decisions）
- `.claude/agents/*.md` + 各 progress 三件套
- `.claude/skills/`
- 项目 CLAUDE.md
- `docs/` + 项目根级 *.md（深度 4）

**真污染面（仅 2 处）**：
1. `feedback_use_custom_subagent_type.md` — 全文重写（旧错误结论删除，新真根因记录 + symlink 修复方案 + 验证证据 + How to apply）
2. `MEMORY.md` L134-136 — PM 协作做了索引同步

**新建文件（PM 协作）**：
- `reference_subagent_symlink.md` — symlink 路径 + 验证命令 + 重建命令 + git ignore 提醒

**误命中（不改，按 Founder "不删历史"偏好保留）**：
- TEAM_CHAT 4 处历史记录"那次任务用了 general-purpose"（事实，保留）
- pm-progress/completed.md L159 历史记录（保留）
- 多处"灰度/彩色"是图像质量任务（与 spawn 无关）
- docs/ 提到的 marketing skills 33 个 symlink（与 agents symlink 无关）

**验证**：
- symlink 状态：`Apr 28 16:53` 建立，target 正确（`xuhua_story/.claude/agents`），agents 完整可见
- spawn `subagent_type: "backend"` 实测：UI 绿色高亮 + 0 tool_uses + 2.8s 完成回复 + 包含"green"字样
- 三条验证标准全过

**与 PM 协作**：
- 我做：feedback_use_custom_subagent_type.md 全文重写 + 自己 progress 三件套 + TEAM_CHAT 协调总结
- PM 做：MEMORY.md 索引同步 + reference_subagent_symlink.md 新建（替我做了我没干完的两件事）
- **0 冲突**（互补做不同文件）

**红线遵守**：
- ✅ 未删任何文件
- ✅ 未触碰 `.team-brain/team_ben/`
- ✅ 未改代码文件，仅动 memory + progress + TEAM_CHAT
- ✅ 地毯式深挖：grep + Read + 验证 symlink 现状 + 区分"规则陈述 vs 历史记录"

**系统级影响**：
- 所有 Founder agent 现在可直接 spawn 彩色 subagent_type（backend / frontend / tester / devops / ai-ml / pm / resonance）
- 派活 prompt 不再需要 paste 角色身份（frontmatter 自动加载）
- PM 17:15 已用真彩色 `subagent_type: "tester"` spawn Wave 3 验收

---

### 2026-04-25 — 4 层成本路线图 + TASK-PARALLEL-M1 派发 + 角色文件全面校准

**主要事项**：
1. 3 个 Sonnet 并发深查（代码现状 / Gemini Batch API / UX 影响）
2. 4 层成本路线图（M0 30% → M3 53% → M9 70% → M18 85%）
3. DEC-020/021/022 记录（M1 工程并行化 / BP 写完整路线图 / 不做画质降级）
4. TASK-PARALLEL-M1 详细规格（含 8 个失败分支兜底矩阵）写入 PENDING
5. BP_SUPPLEMENT 第 6 节《单位经济与成本工程》落盘
6. 角色文件 xuhuastory-boss-coordinator.md 全面校准（282 → 335 行）
7. TEAM_CHAT @PM 知会派活

**关键决策**：
- DEC-020：M1 工程并行化优先（13.5 min → 4.5 min UX 跃迁）
- DEC-021：BP 写完整 4 层杠杆 + 自建集群路线图
- DEC-022：不做 gemini-2.5 vs NB2 画质盲测（NB2 画质是产品力护城河）

**协作模式变化**：
- Founder 纠正"不要 spawn pm，只要知会他就好"——通过 TEAM_CHAT 知会，PM 自己 session 接手时读到再派活
- 这成为后续 Coordinator 协调 PM 的标准模式

---

### 2026-04-23 — BP 4 份调研 + xuhua-wx 移植指南刷新

**BP 4 份 Sonnet 并发调研**：
- Agent A：视频赛道 6 家（Sora 已关停 / Runway / 可灵 / Vidu / Pika / 即梦）
- Agent B：条漫赛道 10 家（含百度文心魔法漫画 / 即梦 / 海螺 / 巨日禄 / 灵境 / StoryDiffusion / NovelAI 等）+ 注先/秒东 推断
- Agent C：商业模型（4 路径定价 + 单位经济 3 scenarios + 12-24 月营收推演）
- Agent D：12 月里程碑（4 季度 OKR）+ 7 个使用场景（按 TAM × 付费意愿排序）

**产出**：`docs/BP_SUPPLEMENT_2026-04-23.md` 6 节（约 2500 字 markdown 富格式 + 900 字纯文本压缩版）

**xuhua-wx 移植指南刷新**：
- `MULTI_AGENT_PORTING_GUIDE.md` 增量回灌 13 处 2026-04-23 added
- `PORTING_PROMPT.md` 增量回灌 6 处 2026-04-23 added
- 内容：Harness V2、12 份 feedback memory、Mureka pipeline、CF SSL 修复经验、16 条 Agent 行为规范

---

### 2026-04-22 — prefaceai.net SSL 526 修复

**根因**：VPS Nginx 加载的是 `CN=Cloudflare` 占位证书（SAN 不含 prefaceai.net），CF Full (Strict) 模式回源校验 SAN 失败 → HTTP 526。

**修复**：CF Dashboard 创建 Origin Certificate（`*.prefaceai.net, prefaceai.net`，2041 到期）→ 本地 `~/secrets/prefaceai/` 备份（chmod 600）→ DevOps SSH 替换 + nginx -s reload → 526 → 200/301/404。

**沉淀经验**：
- CF Origin CA 私钥只在创建时显示一次（必须当场保存）
- 本地 `~/secrets/{project}/` 备份模式（chmod 600）
- HTTP 526 = Cloudflare Invalid SSL certificate 诊断路径

---

### 2026-04-13 — 全面审查 + 文档同步 + Resonance 时间线清理

**审查范围**: 8 Agent × progress + .team-brain 全部文档

**发现**: 
- Coordinator/Resonance 21 天休眠（3/23 后未更新）
- 6 处文档不一致（PROJECT_STATUS/DECISIONS/PENDING/AI-ML/DevOps/Frontend）
- TTS Key 由 Founder 提供，需 DevOps 填入 VPS

**执行**:
1. 更新 Coordinator progress 三件套（补录 3 周进展）
2. 清理 Resonance 旧时间线（Phase 0/1/2 日期作废，待 Founder 重新定义）
3. 修复 6 处文档不一致
4. TTS Key 安全处理（通知 DevOps 直接在 VPS 填入，不经过文档）
5. 记录待定事项到 Coordinator current.md（Resonance 新时间线 + 续写模式 Phase 3 #11 + api_cost_logs 建表）

---

### 2026-03-23 — Resonance Agent 创建

- 新建 `.claude/agents/resonance.md`（市场共鸣官 System Prompt）
- 融合特质: GaryVee 60% + Rory Sutherland 16% + 杜蕾斯 13% + Sean Ellis 11%
- 新建 `resonance-progress/` 三件套（current + context-for-others + completed）
- 全部关联文件更新（CLAUDE.md、TEAM_PROTOCOL、QUICKSTART、PROGRESS_PROTOCOL、coordinator.md、pm.md、backend.md、frontend.md、TEAM_CHAT、TODAY_FOCUS、PROJECT_STATUS、知识文档×2）

---

### 2026-03-19 14:00 — 双团队协作系统全面搭建

**背景**: 合伙人 Ben（人类，CTO 级别）正式加入项目，带来 3 个 Codex Agent。

**新建文件 (23 个)**:
- `.team-brain/team_ben/CODEX.md` — Ben 的 Codex 上下文文件（项目概述+职责+代码规范+协作规则）
- `.team-brain/team_ben/TEAM_CHAT.md` — Ben 团队群聊初始化
- `.team-brain/team_ben/backend.md` — 后端+数据库 Agent 定义
- `.team-brain/team_ben/frontend.md` — 前端联动 Agent 定义
- `.team-brain/team_ben/pm.md` — 协调 Agent 定义
- `.team-brain/team_ben/*-progress/` — 9 个 progress 文件（3 Agent × current/context/completed）
- `.team-brain/shared-memory/` — 7 个记忆文件副本（从 ~/.claude 复制）

**更新文件 (23 个)**:
- `CLAUDE.md` — 新增双团队协作节、Ben 团队表、协调文件表、文件边界规则
- 7 个 Agent 角色文件 — 全部加入双团队感知（pm/backend/frontend 有对应关系说明，tester/ai-ml/devops 有简要说明）
- `TEAM_CHAT.md` — 公告双团队启动 + 群成员更新
- `coordinator-progress/` × 3 — 更新状态
- `.team-brain/daily-sync/2026-03-19.md` — 今日同步
- 其他文件由 PM 后续更新（TEAM_PROTOCOL, PROJECT_STATUS, TODAY_FOCUS, PENDING, QUICKSTART, PROGRESS_PROTOCOL, ARCHITECTURE, Knowledge docs）

---

### 2026-03-18 10:00 — 全面项目审查 + 安全加固启动

**审查范围**:
- 6 Agent × 3 progress 文件 (current + context-for-others + completed) = 18 文件
- .team-brain: TEAM_CHAT (26975 行), PENDING, TODAY_FOCUS, PROJECT_STATUS, DECISIONS, TEAM_PROTOCOL, daily-sync

**发现的问题**:
1. PENDING.md 3 条过期条目 (LOGO-REPLACE / DEPLOY-PREP 实际已完成, STYLE-THUMBNAILS 状态存疑)
2. TODAY_FOCUS.md 日期过期 (03-17, 今天 03-18)
3. Backend/Tester context-for-others 有过期语言 ("awaiting DevOps deployment")
4. 生产安全前置未完成: CORS `["*"]` + 日志无脱敏

**执行的动作**:
- 通知 @PM: 文档清理 (3 项) + 安全加固规划 (CORS + 日志脱敏, 2 项)
- 创建 coordinator-progress 目录 + 3 个 progress 文件
- 更新 TEAM_CHAT 群聊通知
- 创建 daily-sync/2026-03-18.md

**Session 恢复码记录**:
- 将 7 个 Agent session 恢复码写入各自的角色 .md 文件 (pm/ai-ml/backend/tester/frontend/devops/coordinator)

---

### 2026-03-17 — Session 恢复码记录

为所有 7 个 Agent 角色文件添加 Claude Code session 恢复码, 方便 terminal 崩溃后恢复:
- PM: `claude --resume 4bd90c48-...`
- AI-ML: `claude --resume ca6fe52a-...`
- Backend: `claude --resume cd545259-...`
- Tester: `claude --resume 73ed73de-...`
- Frontend: `claude --resume 49434edf-...`
- DevOps: `claude --resume 07dcd631-...`
- Coordinator: `claude --resume ad1bc0c3-...`
