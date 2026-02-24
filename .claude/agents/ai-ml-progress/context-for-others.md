# AI-ML Agent - 给其他 Agent 的上下文

> 其他 Agent 查看此文件了解 AI-ML 的工作状态和 Prompt 约束
> **最后更新**: 2026-02-24 11:41

---

## 当前状态速览

```
状态: 🟢 空闲
刚完成: TASK-REF-PREPROCESS 全部闭环 (DEC-009 + DEC-010)
等待: Founder 下一阶段决策
```

---

## ✅ TASK-REF-PREPROCESS 已闭环 (DEC-009 + DEC-010)

**5步全部完成**:

| Step | 负责 | 状态 | 结果 |
|------|------|------|------|
| 1 | AI-ML | ✅ | 指定 shot_34/36/22 对比测试 |
| 2 | Backend | ✅ | 实现 `_preprocess_reference_to_aspect_ratio()` |
| 3 | Backend | ✅ | 6次API调用对比测试完成 |
| 4 | Tester | ✅ | shot_34略有改善，shot_36/22未复现 |
| 5 | PM | ✅ | 汇总报告+建议保留 |

**Founder 决策 (DEC-010)**:
- 保留预处理代码（低成本无副作用有潜在收益）
- 不启动后处理裁剪方案
- 新增 TASK-SCENE-REF-ASPECT: 从源头统一所有参考图为 2:3

---

## ✅ V5修复任务已完成 (2026-02-03 19:00)

**修复文件**:
- `docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md` (v2.2)
- `tests/test_comic_cc_kai.py`

| 任务 | 问题 | 修复方案 | 状态 |
|------|------|---------|------|
| FIX-A1 | 边缘填充约束 | FULL CANVAS COMPOSITION已强化 | ✅ |
| FIX-A2 | shot_27挽臂违和 | 改为过马路时男生保护性触碰 | ✅ |
| FIX-A3 | shot_40女亲男 | 改为男生偷亲女生 | ✅ |
| FIX-A4 | 角色一致性 | 新增约束块+shot_21/23/29强化 | ✅ |

---

## Prompt 核心约束 (必读)

### 1. 图像 Prompt 必须全英文

```python
# ❌ 错误
image_prompt = "一个穿着红色连衣裙的女孩"

# ✅ 正确
image_prompt = "A girl wearing a red dress"
```

**例外** (这些中文可以保留):
- 角色中文名: "Chen Mo (陈默)"
- 中国特色地点: 胡同、祠堂、牌坊
- 传统服饰: 汉服、旗袍、马褂
- 画面中的中文文字: 春联、牌匾

### 2. Shot 生成必须用 Pro 模型 (短剧场景)

```python
# ❌ 错误 - 会导致角色一致性下降
result = await gen.generate_shot_image(..., use_pro_model=False)

# ✅ 正确
result = await gen.generate_shot_image(..., use_pro_model=True)
```

### 3. 参考图必须完整传入 (短剧场景)

```python
char_refs = ref_manager.get_references_for_scene(chars_in_scene)
scene_refs = scene_ref_manager.get_references_for_location(location_id)
reference_images = char_refs + scene_refs
```

### 4. 所有图像统一 2:3 宽高比（TASK-ASPECT-2x3 + DEC-010）

```python
# ❌ 错误 - 旧的宽高比
aspect_ratio="9:16"  # 或 "16:9", "1:1", "3:4"

# ✅ 正确 - 统一 2:3（抖音适配）
aspect_ratio="2:3"
```

---

## 给 @tester 的信息

### Prompt 修改后的测试

```bash
python tests/test_character_consistency_regression.py

# 验收标准
- 3人场景一致性 ≥95%
- 参考图正确传入 (total_refs > 0)
- 无角色特征混淆
```

---

## 给 @pm 的信息

### 边缘问题优化路线图

| 方案 | 类型 | 负责方 | 状态 | 预期效果 |
|------|------|--------|------|---------|
| 强化prompt边缘约束 | 短期 | AI-ML | ✅ 已完成 | 有效但不彻底 |
| 预处理参考图 | 中期 | AI-ML+Backend | ✅ 已完成 (DEC-009) | 轻微改善，代码保留 |
| 统一2:3宽高比 | 中期 | Backend | ✅ 已完成 (DEC-010) | 消除源头比例不匹配 |
| 后处理边缘检测+裁剪 | 中期 | Backend | ❌ 不启动 (DEC-010) | Founder决定不走此路线 |
| 等待API修复 | 长期 | Google | 被动等待 | 根治 |

### 成本 vs 质量权衡

| 方案 | 成本 | 一致性 | 建议场景 |
|------|------|--------|----------|
| Pro | $9.35 | 100% | 短剧正式发布 |
| Flash | $3.11 | 70-80% | 快速预览、书籍解说 |

---

## 风格系统

### 可用风格列表

```
realistic      # 写实摄影
cartoon        # 3D卡通
anime          # 日式动画
ghibli         # 吉卜力
illustration   # 数字插画
watercolor     # 水彩画
children_book  # 儿童绘本
cyberpunk      # 赛博朋克
ink            # 中国水墨
pixel          # 像素艺术
... (80+种)
```
