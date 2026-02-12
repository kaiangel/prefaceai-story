# Skill: Character Consistency

> 角色一致性是产品的生命线。这是xuhuastory最核心的技术约束。

## Activation Triggers

当涉及以下内容时，必须阅读此skill：
- 修改 `image_generator.py`
- 修改 `storyboard_prompts.py`
- 修改 `storyboard_service.py`
- 修改 `reference_image_manager.py`
- 讨论"角色一致性"、"参考图"、"Pro模型"

**大白话触发**: 人物变脸了、角色长得不一样、同一个人怎么不一样、外观不统一

**完整触发词映射**: [XUHUASTORY_SKILL_TRIGGERS.md](./XUHUASTORY_SKILL_TRIGGERS.md)

---

## Core Constraints (MUST FOLLOW)

### 1. Shot生成必须用Pro模型

```python
# 正确
result = await image_gen.generate_shot_image(
    shot=shot,
    reference_images=char_refs + scene_refs,
    use_pro_model=True  # 必须为True
)

# 错误 - 绝对禁止
use_pro_model=False  # 一致性会从100%降到70%
```

### 2. 参考图传递链必须完整

```
character_refs (fullbody) + scene_refs → generate_shot_image()
```

缺失任何一环都会导致一致性下降。

### 3. 角色描述必须完整

必须包含 `physical` + `clothing` 字段，不能简化：

```python
# 正确：完整描述
"black short slightly messy hair, dark brown eyes, fair skin,
 wearing gray wool sweater, dark blue jeans, black-framed glasses"

# 错误：简化描述
"young man with glasses"
```

---

## Model Selection Strategy

| 阶段 | 模型 | 原因 |
|------|------|------|
| Stage 1-4 (准备) | Gemini Flash | 速度快、成本低 |
| Stage 5 (Shot生成) | **Gemini Pro** | 角色一致性关键 |
| 参考图生成 | Gemini Flash | 无多角色混淆风险 |

---

## Verification Results (v6.6)

| 场景类型 | 一致性 | 测试用例 |
|---------|--------|---------|
| 3人场景 | **100%** | teststory6.4/6.5 |
| 6人场景 | **~90%** | teststory6.6 |

---

## Cost Impact

```
Pro方案: $9.35/故事 (100%一致性)
Flash方案: $3.11/故事 (70-80%一致性)

结论：+$6差价换来质的飞跃，值得
```

---

## Regression Test Requirement

修改相关代码后必须运行：

```bash
pytest tests/test_character_consistency_regression.py -v
```

验证标准：
- [ ] 3人场景一致性 ≥ 95%
- [ ] reference_images_log.json 中 total_refs > 0
- [ ] 无角色特征混淆

**如果不通过，必须回滚代码。**

---

## Key Files (Risk Level)

| 文件 | 风险 | 影响 |
|------|------|------|
| `image_generator.py` | 🔴 极高 | 直接影响图像质量 |
| `storyboard_prompts.py` | 🔴 极高 | 核心prompt构建 |
| `storyboard_service.py` | 🔴 极高 | 角色描述构建 |
| `reference_image_manager.py` | 🟡 高 | 参考图生成 |

---

## Common Pitfalls

| 问题 | 错误做法 | 正确做法 |
|------|----------|----------|
| 角色变脸 | 肖像和全身独立生成 | 串行：肖像→全身 |
| shot缺角色 | 拆分后忽略characters_in_scene | 手动继承 |
| 描述为空 | 从`human`字段读 | 从`physical`+`clothing`读 |
