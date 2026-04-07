---
name: xhsync
description: Coordinator 全局同步 — 扫描所有同事 progress、群聊、team-brain 全维度文档，思考可协调的事项
disable-model-invocation: true
allowed-tools: Bash Read Grep Glob
---

# Coordinator 全局同步

作为主会话协调者，执行一次全面的全局同步。

## 执行步骤

### 1. 扫描所有同事的 progress

仔细毫无遗漏地读取 `.claude/agents/` 中**所有**同事的 progress 文件夹，包括每个 Agent 的：
- `current` — 当前正在做什么
- `context-for-others` — 给其他同事的上下文信息
- `completed` — 已完成的工作

覆盖所有 Agent：PM、Backend、Frontend、Tester、AI-ML、DevOps、Resonance（以及未来可能新增的任何 Agent）。

### 2. 读取群聊

读取 `.team-brain/TEAM_CHAT.md`，内容可能很长，尽可能读取最新的、足够多的行数（500-1000 行起），确保不遗漏近期重要信息。

### 3. 读取 team-brain 全维度文档

读取 `.team-brain/` 中所有必要的文档，包括但不限于：
- `status/TODAY_FOCUS.md` — 今日重点
- `status/PROJECT_STATUS.md` — 项目状态
- `handoffs/PENDING.md` — 待处理交接
- `decisions/DECISIONS.md` — 决策记录
- `shared-memory/` — 共享记忆
- `team_ben/TEAM_CHAT.md` — Ben 团队群聊（只读）
- 其他任何存在的子目录和文件

### 4. 综合思考

基于以上所有信息，思考目前有什么你可以协调的：
- 哪些同事之间需要信息对齐？
- 有没有阻塞或等待中的交接？
- 有没有可以并行推进的任务？
- 有没有遗漏或落下的工作？
- 今日重点任务的进展如何？

输出你的协调建议，按优先级排列。
