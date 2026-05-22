# Coordinator — 其他 Agent 需要知道的

> 最后更新: 2026-04-28（**冻结**）
>
> ⚠️ **2026-05-12 16:30 Founder 纠正身份归属**：本文件中关于 subagent_type symlink / 8 agent frontmatter 升级等工作流变化的描述实际为 PM 工作误归档。**最新状态请看 `pm-progress/context-for-others.md`**。
>
> 本文件保留供历史翻账。

## 项目总体状态

**v0.9.0 内测中（683+ 用户）+ TASK-PARALLEL-M1 实施中 + BP 天使轮筹备中**

### 团队组成（11 角色）
- **Founder 团队**：Coordinator + PM + Backend + AI-ML + Frontend + Tester + DevOps + Resonance（8）
- **Ben 团队**：backend_Ben + frontend_Ben + pm_Ben（3，互相只读）

### 当前主线
1. **TASK-PARALLEL-M1**（PM → Backend → Tester → DevOps，DEC-020）：图像生成并行化 13.5 min → ~4.5 min + ARCH-4 顺手解决
2. **BP 天使轮募资**（500-800 万 RMB）：4 份调研已成 + BP_SUPPLEMENT 6 节落地 + 4 层成本路线图
3. **4 层成本路线图**（DEC-021）：M0 30% → M3 53% → M9 70% → M18 85%

---

## ⚡ 重要的工作流变化（2026-04-28）

**自定义 subagent_type 现已可用**（symlink 修复完成）。

### 新姿势：直接 spawn 彩色 agent

```python
# 旧（基于 2026-04-25 错误结论）
Agent({ subagent_type: "general-purpose", prompt: "你是 backend，做..." })

# 新（2026-04-28 起）
Agent({ subagent_type: "backend", prompt: "做..." })
```

### 可直接 spawn 的 7 个角色
`backend / frontend / tester / devops / ai-ml / pm / resonance`

### 关键好处
- **frontmatter 自动加载**（白名单 / 红线 / 必读 / 启动指令进系统 prompt）
- **派活 prompt 不再需要 paste 角色身份**
- **UI 显示彩色标签**（不是灰色 `Agent(...)`）
- **0 tool_uses 即可启动**（角色文件不用现读）

### 8 Agent frontmatter 默认升级（2026-04-28 17:50，DEC-023）

| Agent | model | effort |
|-------|-------|--------|
| ai-ml / pm / coordinator | opus | xhigh |
| backend / devops / frontend / tester / resonance | **sonnet** | xhigh |

**spawn 时不显式传 → 用上表默认**。显式传 model/effort 可覆盖：
- 复杂架构改造 → 显式 `model: opus, effort: max`（max 仅 Opus 4.7 可用）
- 临时降本 → 显式 `model: sonnet`

⚠️ **xhigh 可能是 Opus 4.7 专属**（slash command 提示 "(Opus 4.7 only)"）。Sonnet 5 个 agent 写 xhigh 可能 silent 降级到 high。监控 1-2 周确认。

### ⚠️ 维护提醒
**symlink 不要误删**：`/Users/kaisbabybook/AIFun/xuhuastory/.claude/agents → xuhua_story/.claude/agents`

误删后重建：
```bash
ln -sf /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story/.claude/agents \
       /Users/kaisbabybook/AIFun/xuhuastory/.claude/agents
```

详见：`~/.claude/projects/.../memory/reference_subagent_symlink.md`

---

## 基础设施

- 网站：https://prefaceai.mov 在线（Docker 28.1.1 + Nginx + Redis healthy）
- API Keys：4/6 已填（TTS 2 个仍待填）
- CI/CD：GitHub Actions 上线（pyright + tsc + pytest）
- 单条成本：$1.85（核心运行）/ $3.40（短篇 21 shots 总成本）
- 当前耗时：13.5 min/20 shots（M1 改造后 → ~4.5 min）

## 关键文件

| 文件 | 说明 |
|------|------|
| `docs/BP_SUPPLEMENT_2026-04-23.md` | BP 补充信息（含第 6 节《单位经济与成本工程》）|
| `.team-brain/analysis/COST_UX_ROADMAP_2026Q2.md` | 4 层杠杆完整路线图 |
| `.team-brain/handoffs/PENDING.md` `TASK-PARALLEL-M1` | M1 派活规格 + 8 分支兜底矩阵 |
| `.team-brain/decisions/DECISIONS.md` DEC-020/021/022 | 成本路线 + Q3 不做画质降级决策 |
| `~/.claude/projects/.../memory/reference_subagent_symlink.md` | symlink 维护参考 |
| `~/.claude/projects/.../memory/feedback_use_custom_subagent_type.md` | subagent_type 真规则（已纠正旧错误结论）|

## 互相只读规则（不变）
- **不修改** `.team-brain/team_ben/` 下的任何文件
- 各 Agent 只动自己角色 .md 白名单内的文件

## 待 Founder 决策
- Resonance 新时间线（旧的 Phase 0/1/2 日期已清理）
- 续写模式 Phase 3 #11 是否开始设计
- BP 主体 15 页是否现在写

## 各 Agent 工作方式变化

**主要变化**：自定义 subagent_type 可用 — 派活方式更简洁。
**其他规则**（白名单 / 红线 / 文档更新 / 审查三步顺序 / Sonnet vs Opus 判断）**全部不变**。
