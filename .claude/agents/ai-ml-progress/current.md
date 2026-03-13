# AI-ML Agent - 当前任务

> **最后更新**: 2026-03-13
> **状态**: ✅ Phase 1 + Phase 3 T-H-AIML 全部完成，等 PM Phase 4 Code Review

---

## 刚完成

### Phase 3 — T-H-AIML (画面自然度 Haiku Prompt 设计) ✅

**完成时间**: 2026-03-13
**交付物**: TEAM_CHAT 中的 prompt 设计文档（供 Backend T-H-Backend 实现）

| # | 任务 | P | 交付 |
|---|------|---|------|
| T-H-AIML | 画面自然度维度 prompt 设计 | P2 | 3 子维度定义 + 风格无关原则 + prompt 文本 + 5 正例 + 5 反例 + 集成确认 |

**设计要点**:
- 3 个子维度: D1 ANATOMICAL (断肢/多余肢体) + D2 PHYSICS (重力违反) + D3 SPATIAL (比例矛盾)
- 风格无关: anime 大眼/ink 极简/pixel 方块 = NATURAL; 断臂/3只手/无支撑悬浮 = UNNATURAL
- 可直接合并到 VALIDATION_PROMPT_BASE（零额外 API 调用，Q3 位置）
- JSON 新增 2 字段: `has_visual_unnaturalness` + `unnaturalness_details`
- max_tokens 建议 256→384
- Phase 1 仅日志，Phase 2 需 Haiku 准确率 > 90% 后启用硬判定

### Phase 1 — T-E+T-F+T-G+T-C-AIML ✅ (PM Code Review 8/8 PASS)

**完成时间**: 2026-03-13
**修改文件**: `storyboard_director.py`, `story_outline_generator.py`

| # | 任务 | P | 修改 |
|---|------|---|------|
| T-E | Stage 4 背面/高角度角色一致性 | P1 | Rule #10 BACK-VIEW/HIGH-ANGLE CHARACTER CONSISTENCY |
| T-F | Stage 4 off-screen 肢体接触 | P1 | Rule #11 OFF-SCREEN CHARACTER PHYSICAL CONTACT |
| T-G | Stage 4 空间方向矛盾 | P1 | Rule #12 SPATIAL DIRECTION SELF-CONSISTENCY CHECK |
| T-C-AIML | Stage 1 signage_text 字段 | P1 | unique_locations schema 新增 signage_text + 创作要点 #7 |

---

## 待处理队列

| 任务 | 优先级 | 状态 |
|------|--------|------|
| Phase 4 PM Code Review | — | 等 PM |
| TASK-STYLE-EXPANSION (80→25-35 风格精选) | P1 | 暂缓 |
| 6人场景一致性 90%->95% | P2 | 暂缓 |

---

## 更新记录

| 时间 | 更新内容 |
|------|----------|
| 2026-03-13 | Phase 3: T-H-AIML 画面自然度 Haiku prompt 设计 |
| 2026-03-13 | Phase 1: T-E Rule#10 + T-F Rule#11 + T-G Rule#12 + T-C-AIML signage_text |
| 2026-03-12 | Phase 1b: T34 镜头信息完整性(Plan A+B) + T37 称谓歧义消除 |
| 2026-03-12 | Phase 1a: T33 关系校验 + T35 多人空间锚定 + T36 色板英文化 |
| 2026-03-12 | Phase 1: T25 标题校验 + T26 对话自然度 + T27 角色关系/背景多样/纵深 |
| 2026-03-11 | Phase 1: T18 道具连续性规则 + T19 跨年龄风格强化 |
| 2026-03-10 | TASK-STYLE-THUMBNAILS: 15/15 风格缩略图生成成功 |
| 2026-03-10 | Step 7: T13 条漫叙事自足 + T14 跨年龄风格统一 + T15 气泡去重 |
| 2026-03-09 | Step 3: T10 thought 比例强化 |
| 2026-03-09 | Step 1: T1+T2+T3 |
