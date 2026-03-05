# SQ-7 草稿：CLAUDE.md + Guide Pro→NB2 + DEC-014 更新

> **状态**: ✅ 已执行完毕 (2026-03-04 11:15)
> **创建**: 2026-03-03 15:40 | **更新**: 2026-03-03 16:22 (DEC-014 新增项)
> **Founder 决策**: NB2 为默认主力，Pro 仅 Premium 储备 + Plan A 移除 previous_shot

---

## 更新位置汇总

| # | 文件 | 行号 | 当前内容 | 更新后内容 |
|---|------|------|----------|-----------|
| 1 | CLAUDE.md | 190 | Shot生成必须使用 `use_pro_model=True` | NB2 默认，Pro 仅 Premium 储备 |
| 2 | CLAUDE.md | 227-245 | Shot间连续性（VISUAL CONTINUITY REFERENCE）整节 | **DEC-014: 移除 previous_shot，改用场景参考图** |
| 3 | CLAUDE.md | 355 | Nano Banana 2 评估中 | NB2 已确认为主力 |
| 4 | CLAUDE.md | 466 | Shot生成必须使用Pro模型 | NB2 默认 + Pro 储备说明 |
| 5 | CLAUDE.md | 671-678 | use_pro_model=True 代码示例 + 警告 | 更新为 NB2 默认示例 |
| 6 | guide | 656 | Shot生成必须继续使用Pro模型 | NB2 默认 |

---

## 逐项更新内容

### 1. CLAUDE.md 第 190 行

**当前**:
```
- **Shot生成必须使用 `use_pro_model=True`**，这是角色一致性的基石
```

**更新为**:
```
- **Shot生成默认使用 Nano Banana 2（`use_pro_model=False`）**，角色一致性 ~95% 与 Pro 持平，速度快 3-5x，成本降 50%。Pro 模型仅作为未来 Premium 用户储备
```

### 2. CLAUDE.md 第 227-245 行 (DEC-014 新增)

**当前** (Section 2.2 整节):
```
### 2.2 Shot间连续性（VISUAL CONTINUITY REFERENCE）

相邻shot之间需要保持场景连贯性（同一地点的光线、天气、环境细节），同时避免构图复制。

**实现方案（2025-01-05）**：
- Shot 2+ 传入 `previous_shot_image` 作为环境参考
- 添加 VISUAL CONTINUITY REFERENCE 指令块，明确告诉模型：
  - **MUST MAINTAIN**：环境一致性（光线、天气、建筑细节）
  - **MUST VARY**：相机角度、构图、角色位置

**技术实现要点**：
- `build_continuity_context_phase2()` 添加 `has_previous_shot_image` 参数
- `build_character_reference_mapping_phase2()` 添加 `has_previous_shot` 和 `scene_ref_count` 参数
- IMAGE 编号正确对应 contents 数组：Image 1 = previous_shot，Images 2-N = character refs，Images M+ = scene refs

**关键代码位置**：
- `storyboard_prompts.py:1420-1443` - VISUAL CONTINUITY REFERENCE 指令块
- `storyboard_prompts.py:1481-1530` - IMAGE 编号映射
- `image_generator.py:365-380` - 参数计算和传递
```

**更新为**:
```
### 2.2 Shot间连续性

相邻shot之间需要保持场景连贯性（同一地点的光线、天气、环境细节），同时保证构图多样性。

**实现方案（DEC-014, 2026-03-03 更新）**：
- ~~previous_shot_image 已移除~~ — 不再传入前序 shot 图像（DEC-014 Plan A）
- 环境连续性由 **场景参考图** (interior/exterior anchor) + **文字 prompt** 保障
- 构图多样性由 Stage 4 StoryboardDirector 的运镜差异化指令保障（SQ-5）

**移除原因**：
- previous_shot 导致构图感染（模型复制前序 shot 的角度/构图/色调）
- 29 shots 串行传递 = 链式误差放大
- 代码无 location_id 检测，跨场景转场时传入错误图像

**当前参考图传递**：
- 每 shot 传入：角色参考图（每角色 1 张，SQ-2 智能选择）+ 场景参考图（interior/exterior）
- IMAGE 编号：Image 1 = 第一个角色参考图，依次排列，最后为场景参考图
- 不再有 "Image 1 = previous_shot" 的占位

**关键代码位置**：
- `storyboard_prompts.py:1481-1530` - IMAGE 编号映射
- `image_generator.py:756-771` - Contents 数组组装
- `pipeline_orchestrator.py:279-341` - Shot 生成循环（previous_shot 传 None）
```

### 3. CLAUDE.md 第 355 行

**当前**:
```
- **Nano Banana 2 评估中**：`gemini-3.1-flash-image-preview`（2026-02-26 发布），角色一致性 ~95% 与 Pro 持平，速度快 3-5x，成本降 50%，有望替代 Pro 成为 Shot 生图主力。详见 `docs/NANO_BANANA_2_RESEARCH.md`
```

**更新为**:
```
- **Nano Banana 2 已确认为主力**：`gemini-3.1-flash-image-preview`（2026-02-26 发布），角色一致性 ~95% 与 Pro 持平，速度快 3-5x，成本降 50%。Founder 决策 NB2 为默认，Pro 仅作未来 Premium 用户储备。详见 `docs/NANO_BANANA_2_RESEARCH.md`
```

### 3. CLAUDE.md 第 369 行

**当前**:
```
| Stage 5 | ImageGenerator | Shot图片生成 | **Gemini 3 Pro Image** 🚨（评估切换 Nano Banana 2） |
```

**更新为**:
```
| Stage 5 | ImageGenerator | Shot图片生成 | **Nano Banana 2**（默认）/ Gemini 3 Pro Image（Premium 储备） |
```

### 4. CLAUDE.md 第 466 行

**当前**:
```
2. **Shot生成必须使用Pro模型**（`use_pro_model=True`），这是角色一致性的基石
```

**更新为**:
```
2. **Shot生成默认使用 Nano Banana 2**（`use_pro_model=False`），角色一致性 ~95%，速度和成本优势显著。Pro 模型（`use_pro_model=True`）仅作为未来 Premium 用户储备，当前不启用
```

### 5. CLAUDE.md 第 671-678 行

**当前**:
```python
result = await image_gen.generate_shot_image(
    shot=shot,
    reference_images=char_refs + scene_refs,
    style_enforcer=style_enforcer,
    use_pro_model=True  # 🚨 关键：必须为True，否则角色一致性会从100%下降到70-80%
)
```
```
**警告**：如果 `use_pro_model=False`：
- 3人场景一致性：100% → ~75%
- 6人场景一致性：~90% → ~50%
- 成本节省 $6/故事，但用户体验严重受损
```

**更新为**:
```python
result = await image_gen.generate_shot_image(
    shot=shot,
    reference_images=char_refs + scene_refs,
    style_enforcer=style_enforcer,
    use_pro_model=False  # 默认 NB2（Nano Banana 2），角色一致性 ~95%
    # use_pro_model=True 仅用于未来 Premium 用户
)
```
```
**NB2 vs Pro 对比**：
- NB2（默认）：角色一致性 ~95%，37.2s/shot，成本降 50%
- Pro（Premium 储备）：角色一致性 ~98%，70-90s/shot，成本高 2x
- Founder 决策：NB2 为默认主力，Pro 不做 3+ 角色场景自动切换
```

### 6. shot_transition_improvement_guide.md 第 656 行

**当前**:
```
- Shot生成**必须**继续使用Pro模型（`use_pro_model=True`）
```

**更新为**:
```
- Shot生成默认使用 Nano Banana 2（`use_pro_model=False`），Pro 仅作 Premium 储备
```

---

## 执行检查清单（Step 5 启动时逐项执行）

- [x] CLAUDE.md 第 190 行更新 (Pro→NB2) ✅
- [x] CLAUDE.md 第 227-245 行更新 (DEC-014: 移除 previous_shot 整节重写) ✅
- [x] CLAUDE.md 第 355 行更新 (评估中→已确认) ✅
- [x] CLAUDE.md 第 369 行更新 (Stage 5 表格) ✅
- [x] CLAUDE.md 第 466 行更新 (核心原则) ✅
- [x] CLAUDE.md 第 671-678 行更新 (代码示例 + 警告) ✅
- [x] shot_transition_improvement_guide.md 第 656 行更新 ✅
- [x] 全文搜索 `use_pro_model=True` 确认无遗漏 ✅
- [x] 全文搜索 `评估切换` 确认无遗漏 ✅
- [x] 全文搜索 `previous_shot_image` 在 CLAUDE.md 中确认无遗漏 ✅
- [x] 更新 pm-progress 文档标记 SQ-7 完成 ✅
- [x] **额外**: CLAUDE.md L353-354 数据流 + L562-563 已踩坑表 + L663 标题 (草稿未覆盖的 5 处) ✅
- [x] **额外**: Guide Section 3.2/3.3/4 DEC-014 标注 (草稿未覆盖的 7 处) ✅
