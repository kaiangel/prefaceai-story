# AI-ML Agent - 当前任务

> **最后更新**: 2026-03-24
> **状态**: ✅ TASK-OUTLINE-LLM-FIX 第 1 项完成 (system prompt 设计)，等 Backend 集成

---

## 刚完成

### TASK-OUTLINE-LLM-FIX 第 1 项 — system prompt 设计 ✅

**完成时间**: 2026-03-24
**交付方式**: TEAM_CHAT 发布，@backend 集成
**内容**: StoryOutlineGenerator 专用 system prompt — 角色定位 + JSON 严格约束 + 中英文分工 + 新增字段强化

---

### TASK-OUTLINE-PROMPT-UPGRADE — Stage 1 Prompt 新增 4 个字段 ✅

**完成时间**: 2026-03-24
**修改文件**: `app/services/story_outline_generator.py` (`_build_prompt` 方法)

**新增 3 个顶层字段**:
| 字段 | 说明 |
|------|------|
| `summary` | 故事简介（100-200字，比 logline 详细但比 plot_points 精炼） |
| `ending_options` | 3 个结局选项（数组，每项 id + description，选项间有明显差异） |
| `mood` | 情绪基调（从 感人/治愈/热血/悬疑/浪漫/温馨 六选一） |

**新增 2 个 `characters_overview` 子字段**:
| 字段 | 说明 |
|------|------|
| `description` | 外貌简述（20-30 字中文，给前端用户看） |
| `personality` | 性格简述（10-20 字中文，给前端用户看） |

**创作要点新增**: #8-#11（summary 定位、ending 差异化、mood 预设值、角色简述为中文非图像用途）

**验证**: Python syntax ✅

**不动的部分**: 现有所有字段（title/title_en/logline/emotional_arc/narrative_pace/visual_tone/target_metrics/characters_overview 现有字段/plot_points/unique_locations/family_relationships）全部保持不变。

---

## 待处理队列

| 任务 | 优先级 | 状态 |
|------|--------|------|
| TASK-OUTLINE-LLM-FIX 第 1 项 (system prompt) | — | ✅ 已交付，等 Backend 集成 |
| TASK-STYLE-THUMBNAILS (15 风格缩略图) | P0 | 暂缓 |
| TASK-STYLE-EXPANSION (80→25-35 风格精选) | P1 | 暂缓 |
| 6人场景一致性 90%->95% | P2 | 暂缓 |

---

## 更新记录

| 时间 | 更新内容 |
|------|----------|
| 2026-03-24 | TASK-OUTLINE-LLM-FIX 第 1 项: system prompt 设计 (JSON 约束 + 中英文分工 + 新增字段强化) |
| 2026-03-24 | TASK-OUTLINE-PROMPT-UPGRADE: Stage 1 prompt 新增 summary + ending_options + mood + description + personality |
| 2026-03-17 | TASK-OB1-CLEANUP: prompt_safety_rewrite.py 11 处 "Haiku"→"Sonnet 4.6" |
| 2026-03-16 | TASK-IMG-SAFETY-RETRY-AIML: 5 类新关键词 + 2 个改写模板 + 简化 spec + 结构优化建议 |
| 2026-03-13 | Phase 3: T-H-AIML 画面自然度 Haiku prompt 设计 |
| 2026-03-13 | Phase 1: T-E Rule#10 + T-F Rule#11 + T-G Rule#12 + T-C-AIML signage_text |
| 2026-03-12 | Phase 1b: T34 镜头信息完整性(Plan A+B) + T37 称谓歧义消除 |
| 2026-03-12 | Phase 1a: T33 关系校验 + T35 多人空间锚定 + T36 色板英文化 |
| 2026-03-12 | Phase 1: T25 标题校验 + T26 对话自然度 + T27 角色关系/背景多样/纵深 |
| 2026-03-11 | Phase 1: T18 道具连续性规则 + T19 跨年龄风格强化 |
