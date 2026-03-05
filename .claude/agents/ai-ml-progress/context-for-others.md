# AI-ML Agent - 给其他 Agent 的上下文

> 其他 Agent 查看此文件了解 AI-ML 的工作状态和 Prompt 约束
> **最后更新**: 2026-03-04

---

## 当前状态速览

```
状态: ✅ Shot 15/18 Prompt 优化完成 + SQ-4/SQ-5/Bug#3 重新应用完成
下一步: 等待 PM review
```

---

## 🆕 Shot 15/18 Prompt 工程优化 + 代码恢复 @PM @Tester

### ⚠️ 重要通知

PM 回滚代码时误删了 AI-ML 此前所有 `storyboard_director.py` 改动。本次已全部重新应用并追加新规则。

### 修改文件: `storyboard_director.py`

**主规则区 `_build_scene_prompt()` — 完整版:**

| 编号 | 规则 | 说明 |
|------|------|------|
| Rule #6 | STRICT CHARACTER COUNT | 🔄 重新应用 — 禁止路人/群演/背景人物 |
| Rule #7 | OBJECT PHYSICAL PLAUSIBILITY | 🆕 共享平面物体需独立空间锚点，禁止重叠 |
| Rule #8 | MULTI-CHARACTER LIMB INTERACTION LIMITS | 🆕 同一物体最多2角色手部交互，超过则拆 shot |
| SQ-4 | NARRATIVE VISUAL PROPS + SPATIAL DEPTH | 🔄 重新应用 |
| SQ-5 | SHOT TRANSITION RULES + 数据结构增强 | 🔄 重新应用 |

**强化规则区 `_build_prompt()` — 精简版:** Rules 6-8 同步添加

### Rule #7 详情: 物体物理合理性 (Shot 15 手机叠菜)

- 根因: prompt 写 "smartphone glows at centre, around it braised pork" → 空间关系模糊 → NB2 渲染出手机叠在菜上
- 修复: 要求共享表面上每个物体有 distinct spatial anchor，禁止 "among"/"around it"/"surrounded by"

### Rule #8 详情: 肢体交互上限 (Shot 18 筷子归属)

- 根因: prompt 写 "three pairs of chopsticks converging on same dumplings" → 6 手+6 筷 → NB2 无法分辨归属
- 修复: 同一 shot 最多 2 角色手部与同一物体交互，超过则拆 shot 或用柔焦

---

## Prompt 核心约束 (必读)

### 1. 图像 Prompt 必须全英文
### 2. Shot 生成用 NB2 模型（DEC-012 后已切换）
### 3. 参考图必须完整传入
### 4. 所有图像统一 2:3 宽高比（TASK-ASPECT-2x3 + DEC-010）
### 5. DIALOGUE-SYSTEM 规则 (dialogue≥60%, thought 15-25%, narration≤10%, none禁止)
### 6. DEC-014: previous_shot_image 已移除

---

## 风格系统

15 种风格全部已升级场域式 ✅:
realistic, cartoon, pixar_3d, anime, ghibli, illustration, watercolor, children_book, manga, slam_dunk, korean_webtoon, oil_painting, cyberpunk, ink, pixel
