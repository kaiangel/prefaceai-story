# AI-ML Agent - 当前任务

> **最后更新**: 2026-03-04
> **状态**: ✅ Shot 15/18 Prompt 优化完成 + SQ-4/SQ-5/Bug#3 重新应用完成

---

## 刚完成

### Shot 15/18 Prompt 工程优化 + 代码恢复 ✅

**完成时间**: 2026-03-04
**修改文件**: `app/services/storyboard_director.py`

**⚠️ 重要事件**: PM 回滚代码时误删了 AI-ML 此前所有改动（SQ-4/SQ-5/Bug#3 Rule #6），本次一并重新应用。

**本次修改内容** (两处规则区):

#### 主规则区 `_build_scene_prompt()` — 完整版

| 编号 | 规则 | 行号 | 状态 |
|------|------|------|------|
| Rule #6 | STRICT CHARACTER COUNT — NO EXTRA PEOPLE | L414-423 | 🔄 重新应用（Bug #3 修复） |
| Rule #7 | OBJECT PHYSICAL PLAUSIBILITY ON SHARED SURFACES | L425-433 | 🆕 新增（Shot 15 手机叠菜） |
| Rule #8 | MULTI-CHARACTER LIMB INTERACTION LIMITS | L435-443 | 🆕 新增（Shot 18 筷子归属） |
| SQ-4 | NARRATIVE VISUAL PROPS | L445-454 | 🔄 重新应用 |
| SQ-4 | SPATIAL DEPTH RULES | L456-462 | 🔄 重新应用 |
| SQ-5 | SHOT TRANSITION RULES (5 subsections) | L464-489 | 🔄 重新应用 |
| SQ-5 | JSON template 增强 (focal_length + foreground/background/depth_layers) | L503-504 | 🔄 重新应用 |

#### 强化规则区 `_build_prompt()` — 精简版

| 编号 | 规则 | 行号 |
|------|------|------|
| Rule #6 | STRICT CHARACTER COUNT | L712-713 |
| Rule #7 | OBJECT PHYSICAL PLAUSIBILITY | L715-716 |
| Rule #8 | MULTI-CHARACTER LIMB INTERACTION LIMITS | L718-719 |

**验证**: ✅ Python 语法检查通过（0 error, 935 lines）

---

## 待处理队列

| 任务 | 优先级 | 状态 |
|------|--------|------|
| TASK-SHOT-QUALITY-UPGRADE SQ-3/4/5 | P0/P1 | ✅ 完成（SQ-4/5 已重新应用） |
| TASK-SHOT-QUALITY-BUGFIX Bug #3 | P2 | ✅ 完成（已重新应用） |
| Shot 15/18 Prompt 优化 (Rule #7/#8) | P3 | ✅ 完成 |
| 6人场景一致性 90%→95% | P2 | 暂缓 |

---

## 更新记录

| 时间 | 更新内容 |
|------|----------|
| 2026-03-04 | Shot 15/18 优化 (Rule #7/#8) + SQ-4/SQ-5/Bug#3 重新应用（PM 误回滚恢复） |
| 2026-03-04 | Bug #3 修复: 神秘路人负面约束 (Rule #6) |
| 2026-03-04 | Step 5b 完成: SQ-3/4/5 代码修改 |
| 2026-03-03 17:05 | slam_dunk 句序修复完成 |
| 2026-03-03 15:56 | TASK-STYLE-DESC-REWRITE 完成：15个风格全部改为场域式 |
