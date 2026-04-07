---
name: xhdispatch
description: PM 记录讨论结果并派活 — 记录到文档、更新群聊和 progress、更新 team-brain、派活给指定同事
disable-model-invocation: true
allowed-tools: Bash Read Write Edit Grep Glob
argument-hint: [核心内容摘要]
---

# PM 记录 + 更新 + 派活

在与 Founder 讨论完成后，执行以下完整流程。

**用法**：`/dispatch 核心内容摘要`

`$ARGUMENTS` 中的内容是本次讨论中**核心重要的、绝对不能遗漏**的关键信息。

## 执行步骤

### 1. 记录讨论结果

把我们讨论的所有内容记录到合适的文档中。

**特别注意**：`$ARGUMENTS` 中提到的核心内容**尤其不要遗漏**，必须完整、准确地记录。

### 2. 更新群聊

更新 `.team-brain/TEAM_CHAT.md`，将本次讨论的结论和决策同步给团队。

### 3. 更新 PM 的 progress

更新你（PM）的 progress 文件，确保三个维度都是最新的：
- **current** — 当前正在做什么
- **context-for-others** — 其他同事需要知道的上下文
- **completed** — 已完成的工作

### 4. 更新 team-brain

更新 `.team-brain/` 中每个文件夹里所有需要更新的文档，包括但不限于：
- `status/TODAY_FOCUS.md`
- `status/PROJECT_STATUS.md`
- `handoffs/PENDING.md`
- `decisions/DECISIONS.md`
- 其他任何受本次讨论影响的文档

### 5. 派活

根据讨论结果，向所有必要的同事派发任务。明确每个同事需要做什么、验收标准是什么、依赖关系和优先级。
