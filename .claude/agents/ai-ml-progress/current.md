# AI-ML Agent - 当前任务

> **最后更新**: 2026-03-17
> **状态**: ✅ TASK-OB1-CLEANUP 完成，等 PM 审查

---

## 刚完成

### TASK-OB1-CLEANUP — prompt_safety_rewrite.py "Haiku" 引用清理 ✅

**完成时间**: 2026-03-17
**修改文件**: `app/prompts/prompt_safety_rewrite.py`
**改动**: 11 处 "Haiku" → "Sonnet 4.6"（docstring + 注释 + 函数名 + model ID + 成本估算）
**验证**: Python syntax ✅ + "Haiku" grep 零匹配 ✅

---

### TASK-IMG-SAFETY-RETRY-AIML — 参考图安全改写 Prompt 工程 ✅

**完成时间**: 2026-03-16
**修改文件**: `app/prompts/prompt_safety_rewrite.py`

| # | 交付物 | 内容 |
|---|--------|------|
| 1 | 新增关键词类别 | CROWD(19) + ANIMAL(16) + FIRE_SMOKE(16) + CHILD_CONTEXT(10) + REVEALING_CLOTHING(13) = 74 个替换词条 |
| 2 | SCENE_REF_REWRITE_PROMPT | 场景参考图专用 LLM 改写模板（保留建筑/招牌, 去除人群/动物） |
| 3 | CHAR_REF_REWRITE_PROMPT | 角色参考图专用 LLM 改写模板（保留身份锚点, 修改武器/暴露） |
| 4 | _simplify_anchor_prompt() spec | Backend 实现指引（前置 No people + apply_simple_replacements + 正则清理） |
| 5 | _build_anchor_prompt() 结构优化 | 建议 "No people" 从 prompt 末尾前置到标题之后 |

### PM Code Review 后 2 项小补充 ✅

**完成时间**: 2026-03-16
**修改文件**: `app/services/scene_reference_manager.py`

1. `_simplify_anchor_prompt()` 补正则: `re.sub(r'\b(people|persons|humans|men|women|children)\s+(are\s+)?\w+ing\b', '', simplified)`
2. `_build_anchor_prompt()` "No people" 前置: exterior + interior 两个分支标题后紧接 STRICT 声明, 末尾删除原 STRICT 行

---

## 待处理队列

| 任务 | 优先级 | 状态 |
|------|--------|------|
| PM 审查 TASK-OB1-CLEANUP | — | 等 PM |
| TASK-STYLE-EXPANSION (80→25-35 风格精选) | P1 | 暂缓 |
| 6人场景一致性 90%->95% | P2 | 暂缓 |

---

## 更新记录

| 时间 | 更新内容 |
|------|----------|
| 2026-03-17 | TASK-OB1-CLEANUP: prompt_safety_rewrite.py 11 处 "Haiku"→"Sonnet 4.6" |
| 2026-03-16 | TASK-IMG-SAFETY-RETRY-AIML: 5 类新关键词 + 2 个改写模板 + 简化 spec + 结构优化建议 |
| 2026-03-13 | Phase 3: T-H-AIML 画面自然度 Haiku prompt 设计 |
| 2026-03-13 | Phase 1: T-E Rule#10 + T-F Rule#11 + T-G Rule#12 + T-C-AIML signage_text |
| 2026-03-12 | Phase 1b: T34 镜头信息完整性(Plan A+B) + T37 称谓歧义消除 |
| 2026-03-12 | Phase 1a: T33 关系校验 + T35 多人空间锚定 + T36 色板英文化 |
| 2026-03-12 | Phase 1: T25 标题校验 + T26 对话自然度 + T27 角色关系/背景多样/纵深 |
| 2026-03-11 | Phase 1: T18 道具连续性规则 + T19 跨年龄风格强化 |
