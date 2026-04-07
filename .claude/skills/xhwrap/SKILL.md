---
name: xhwrap
description: 收尾检查 — 提醒当前 Agent double check 是否已更新群聊、progress、team-brain 所有必要文档
disable-model-invocation: true
allowed-tools: Bash Read Write Edit Grep Glob
---

# 收尾检查

任务完成后的 double check，确保所有文档更新到位。

## 检查清单

逐项确认以下内容是否已更新，**未更新的立即补上**：

### 1. 群聊
- [ ] `.team-brain/TEAM_CHAT.md` — 是否已将本次工作的进展、结论、关键信息同步到群聊？

### 2. 自己的 progress
- [ ] **current** — 是否反映了当前最新状态（任务已完成则清空或标注下一步）？
- [ ] **context-for-others** — 是否把其他同事需要知道的信息更新进去了？
- [ ] **completed** — 是否记录了本次完成的工作？

### 3. team-brain 文档
逐个检查 `.team-brain/` 中每个文件夹里所有需要更新的文档：
- [ ] `status/TODAY_FOCUS.md` — 今日重点是否需要更新？
- [ ] `status/PROJECT_STATUS.md` — 项目状态是否需要更新？
- [ ] `handoffs/PENDING.md` — 是否有新的交接事项？是否有已完成的交接需要标记？
- [ ] `decisions/DECISIONS.md` — 是否有新的决策需要记录？
- [ ] `shared-memory/` — 是否有需要同步给 Ben 团队的信息？
- [ ] 其他任何受本次工作影响的文档

**发现遗漏的，现在就补上。**

## 更新格式要求

每次更新文档时，遵循以下标准化格式：
- **带时间戳**：每条更新以 `[YYYY-MM-DD HH:MM]` 开头
- **带变更摘要**：简明说明改了什么、为什么改
- **带状态标记**：明确标注完成/进行中/阻塞
