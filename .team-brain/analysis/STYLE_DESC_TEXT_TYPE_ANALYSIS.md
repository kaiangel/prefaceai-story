# 场域式 style_description 对 text_type 分布的影响分析

> **分析者**: @coordinator
> **日期**: 2026-03-02
> **背景**: Founder 要求在采纳场域式之前，排查场域式写法是否是导致对话占比低的原因

---

## 核心结论

**场域式 style_description 对 text_type 分布零影响。** 这是架构决定的事实，非经验推断。

---

## 分析依据

### 1. 架构隔离：Stage 4 和 Stage 5 不共享 style_description

```
Stage 4 (StoryboardDirector)
├── 输入：screenplay, characters, visual_tone, style_preset(字符串)
├── 输出：4_storyboard.json（含 text_type）
├── 不接收：style_config 对象、style_description 文本
└── 不引用：StyleEnforcer

Stage 5 (ImageGenerator)
├── 输入：4_storyboard.json + style_config（含 style_description）
├── 调用：StyleEnforcer.enforce_prompt()
└── 此时 text_type 早已固定
```

**关键代码证据**：

- `storyboard_director.py` 的 `direct()` 方法签名只有 `style_preset: str = "anime"`
- `storyboard_director.py` 全文无 `StyleEnforcer` 的 import 或调用
- `_build_scene_prompt()` 中 style 仅以 `"{style_preset}_cinematic"` 字符串出现

### 2. A/B 测试设计验证

两次测试均为：Stage 1-4 只执行一次 → 两组共享同一份 `4_storyboard.json` → Stage 5 才切换 style_description。

| 测试 | A/B 两组 text_type 分布 | 结论 |
|------|----------------------|------|
| TASK-AB-STYLE-DESC (slam_dunk, 5 shots) | 完全相同 | style_description 无影响 |
| TASK-CROSS-STYLE-TEST (illustration, 32 shots) | 完全相同 | style_description 无影响 |

### 3. 场域式写法特征分析

场域式 illustration 描述原文：
> "You are creating in the tradition of the finest digital illustrators — artists who treat every frame as a painting that tells a story. Light pours through windows and catches in hair, pooling in warm gradients that guide the eye to what matters most. Colors breathe with intention: warm ambers for intimacy, cool blues for solitude, saturated accents that anchor emotion. Every surface carries just enough texture to feel alive — the weave of fabric, the sheen of rain-wet pavement, the soft glow of a phone screen in twilight. Characters inhabit their world through posture, micro-expression, and the charged space between them. Each composition balances clarity with depth, placing the viewer exactly where the feeling lives."

虽然场域式描述偏向氛围/情绪/光影（可能引发"是否抑制对话"的直觉怀疑），但这些文字**只在 Stage 5 生图时注入 prompt**，不参与 Stage 4 的 text_type 决策。

**结论：直觉怀疑合理，但架构上不可能产生因果关系。**

---

## text_type 分布问题的真正原因

### 问题现象

TASK-CROSS-STYLE-TEST（暗恋题材《拿铁上的告白》）：
- dialogue 家族：28.1%（目标 ≥60%，**FAIL**）
- thought：71.9%（目标 15-25%，**严重超标**）

### 根因分析

**原因在 Stage 4 的 TEXT OVERLAY RULES 执行力**，而非 style_description。

Stage 4 prompt 中有硬约束：
```
dialogue (including dialogue_with_thought, dialogue_with_narration) MUST account for AT LEAST 60%
After generating all shots, SELF-CHECK: Count your dialogue shots. If less than 60%, go back and convert.
```

但 Claude Sonnet 4.6 在暗恋题材中**选择了忽略 SELF-CHECK**，优先服从故事的内在逻辑。

### 待验证假设

| 假设 | 验证方式 |
|------|---------|
| A: 暗恋题材天然不适合 60% 对话（题材结构性） | 用对话密集型题材测试，看能否达 60% |
| B: SELF-CHECK 机制对 Sonnet 4.6 约束力不足 | 同上——如果对话密集型也达不到 60%，说明是 B |
| C: A+B 复合 | 需更多数据点 |

**下一步：TASK-DIALOGUE-DENSE-TEST（家庭晚餐争吵题材），专门验证假设 A vs B。**

---

## 场域式采纳的独立评估

### 已验证的收益

| 维度 | slam_dunk | illustration |
|------|-----------|-------------|
| 画面质量 | B 4.5 vs A 4.17 | B 4.38 vs A 3.88 |
| 速度 | B 慢 51% | B 快 26% |
| 角色一致性 | 平 | 平 |

**画面质量一致性胜出，速度因风格而异。**

### 待验证的风险

| 风险 | 说明 | 建议验证方式 |
|------|------|------------|
| 跨风格泛化性 | 只测了 2/16 个风格 | AI-ML 全量改写 + 挑 1-2 个差异最大的风格小规模验证 |
| 速度不一致 | slam_dunk 慢 51%、illustration 快 26% | 更多数据点 |

### Founder 决策状态

- 场域式采纳方向已确认
- 全量铺开前需先验证跨风格泛化性（Founder 要求）
