# AI-ML Agent - 当前任务

> **最后更新**: 2026-04-15（PM 代更新）
> **状态**: ✅ Harness V2: OutlineSchema + ScreenplaySchema + 中文阈值 5% + 已部署

---

## 刚完成

### TASK-PIPELINE-OPT-R3 A-1 — description_zh prompt 加强 ✅

**完成时间**: 2026-04-09
**文件**: `app/services/story_outline_generator.py`

排查发现原 AM-1 的 prompt 对 description_zh 强调不够，LLM 可能跳过。3 处加强:
1. System prompt: 新增 MANDATORY 规则（英文强制词）
2. JSON schema: 加 `【必填】` + 内联示例
3. 创作要点 #12: 加 `(REQUIRED/必填)` + 三者共存说明

---

### TASK-PHASE2-PROMPTS — Phase 2 分析/上下文 prompt 设计 ✅

**完成时间**: 2026-03-25
**交付方式**: TEAM_CHAT 发布，@backend 集成

| # | Prompt | 用途 | 输出 |
|---|--------|------|------|
| 1 | 自定义风格分析 | analyze-style 端点 | StyleEnforcement JSON + display_tags 中文标签 |
| 2 | 角色特征提取 | analyze-character 端点 | description_zh/en + gender + age_range + display_name |
| 3 | 场景特征提取 | analyze-scene 端点 | description_zh/en + location_type + atmosphere + display_name |
| 4 | 用户参考上下文段 | _build_prompt 追加 | 动态函数，角色/场景/风格三段按需拼接 |

---

### TASK-STYLE-EXPAND-28 — 13 个新风格完整配置 ✅

**完成时间**: 2026-03-25（早些时候）

---

## 待处理队列

| 任务 | 优先级 | 状态 |
|------|--------|------|
| Backend 集成 4 prompts | P0 | 等 Backend |
| PM Review prompts | P0 | 等集成后 |
| Phase 2 Step 2-3（可能涉及 AI-ML） | — | 等 Step 1 完成 |
| 6人场景一致性 90%->95% | P2 | 暂缓 |

---

## 更新记录

| 时间 | 更新内容 |
|------|----------|
| 2026-03-25 | TASK-PHASE2-PROMPTS: 4 个分析/上下文 prompt (风格/角色/场景/大纲上下文) |
| 2026-03-25 | TASK-STYLE-EXPAND-28: 13 个新风格 × 6 维度 + 前端展示信息 |
| 2026-03-24 | TASK-OUTLINE-LLM-FIX 第 1 项: system prompt 设计 |
| 2026-03-24 | TASK-OUTLINE-PROMPT-UPGRADE: Stage 1 prompt 新增 5 个字段 |
| 2026-03-17 | TASK-OB1-CLEANUP: prompt_safety_rewrite.py 11 处 "Haiku"→"Sonnet 4.6" |
