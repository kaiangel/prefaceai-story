# Skill: Context Management

> 基于 Agent-Skills-for-Context-Engineering 的上下文工程最佳实践

## Activation Triggers

当遇到以下情况时，应用此skill：
- 开始新的工作会话
- 感觉上下文变得混乱
- 任务复杂度增加
- 需要多个agent协作

**大白话触发**: Claude忘了之前说的、对话太长了、信息混乱了、开始重复了

**完整触发词映射**: [XUHUASTORY_SKILL_TRIGGERS.md](./XUHUASTORY_SKILL_TRIGGERS.md)

---

## Core Principle: Progressive Disclosure

**不要一次加载所有信息。**

### 分层加载策略

| 层级 | 内容 | 何时加载 |
|------|------|---------|
| L0 必读 | agent定义 + 核心约束 | 每次会话开始 |
| L1 常用 | 相关skill摘要 | 任务开始时 |
| L2 详情 | skill完整内容 | 需要时按需加载 |
| L3 参考 | 历史决策、踩坑记录 | 遇到问题时 |

### 示例

```
简单任务（修复typo）：
  只需 L0

中等任务（新增API）：
  L0 + L1（backend相关skill）

复杂任务（修改图像生成）：
  L0 + L1 + L2（character-consistency完整内容）
```

---

## Attention Budget Constraint

LLM的注意力是有限资源。研究表明：
- Tool outputs可能消耗83.9%的上下文
- 关键信息应放在开头/结尾（"Lost in the Middle"问题）

### 自检问题

开始工作前问自己：
1. 这个任务真的需要读完整个claude.md吗？
2. 我需要哪些具体的约束？
3. 有没有可以跳过的部分？

---

## Memory Layers

### Working Memory（工作记忆）
- 当前对话上下文
- 会话结束即消失
- 容量有限

### Short-Term Memory（短期记忆）
- `/.team-brain/status/TODAY_FOCUS.md`
- `/.team-brain/handoffs/PENDING.md`
- 当日有效

### Long-Term Memory（长期记忆）
- `/.team-brain/knowledge/KEY_LEARNINGS.md`
- `/.team-brain/decisions/DECISIONS.md`
- `/claude.md` 核心约束
- 跨会话持久

---

## Context Quality Indicators

### 退化信号

当出现以下情况时，上下文可能已退化：
- 开始重复之前讨论过的内容
- 忘记了已经做出的决策
- 混淆了不同文件的内容
- 回答变得泛泛而谈

### 恢复策略

1. **压缩当前上下文**：总结关键点
2. **重新加载核心约束**：读取相关skill
3. **检查长期记忆**：查看KEY_LEARNINGS.md

---

## Multi-Agent Coordination

### "电话游戏"问题

监督者转述子代理响应时会丢失/歪曲信息。

### 解决方案

交接时必须包含：
- 原始输出（不只是摘要）
- 关键代码变更的diff
- 精确的数值结果

### 交接模板

```markdown
## Handoff: @backend → @tester

### 完成的工作
[具体描述，附带文件路径和代码片段]

### 原始输出
[不要转述，直接附带]

### 需要验证的点
1. [ ] 具体验证点1
2. [ ] 具体验证点2
```

---

## File System as State Machine

利用目录和文件作为状态标记：

```
/.team-brain/
├── active-context/
│   ├── CURRENT_TASK.md      # 当前任务
│   └── LOADED_SKILLS.md     # 已加载的skills
├── handoffs/
│   └── PENDING.md           # 待处理交接
└── daily-sync/
    └── 2025-01-05.md        # 今日进度
```

---

## Best Practices

1. **开始工作时**
   - 先读TODAY_FOCUS.md
   - 确定需要哪些skills
   - 按需加载，不要全部加载

2. **工作过程中**
   - 完成一个任务就更新状态
   - 发现重要经验就记录到KEY_LEARNINGS
   - 需要交接时写清楚PENDING

3. **结束工作时**
   - 更新PROJECT_STATUS.md
   - 记录今日daily-sync
   - 清理已完成的handoffs
