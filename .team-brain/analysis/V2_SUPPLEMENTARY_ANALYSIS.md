# V2 补充深入分析 - PM遗漏点

**分析人**: @PM
**日期**: 2026-02-02
**状态**: 补充分析

---

## 遗漏点1: Shot 28 内容安全限制深入分析 ⭐

### Prompt内容分析

```
CLOSE-UP SHOT focusing on two hands walking side by side, about to touch.
The scene captures the electric moment just before contact.

LEFT - A man's hand, defined fingers, slightly reaching toward her...
RIGHT - A woman's hand, delicate fingers, palm slightly open in unconscious invitation...

Their fingertips are millimeters apart, about to brush. The tension is palpable.
```

### 触发安全过滤的可能因素

| 因素 | 敏感词/描述 | 风险等级 |
|-----|-----------|---------|
| 身体接触暗示 | "about to touch", "just before contact" | 中 |
| 情绪张力 | "electric moment", "tension is palpable" | 中 |
| 暗示性语言 | "unconscious invitation", "reaching toward her" | **高** |
| 物理接近 | "fingertips millimeters apart" | 中 |

### 根因分析

Gemini的安全过滤器可能将以下组合识别为潜在亲密内容：
1. **"invitation"** - 这个词在身体接触语境中可能被标记
2. **强调期待和张力** - "electric", "tension", "palpable"
3. **身体部位特写** + **即将接触** 的组合

### 通用化解决方案

**方案A - 语言重写（推荐）**:
```
修改前（触发安全限制）:
"palm slightly open in unconscious invitation"
"The tension is palpable"
"electric moment just before contact"

修改后（安全）:
"palm relaxed in natural walking posture"
"A moment of quiet anticipation"
"walking together in comfortable closeness"
```

**方案B - 场景重构**:
```
避免手部特写，改用中景展示两人并肩走路：
"MEDIUM SHOT of the couple walking side by side on the street,
their arms naturally close but not touching, both looking ahead
with gentle smiles."
```

**敏感场景Prompt模板库** (建议AI-ML建立):

| 场景类型 | 安全描述模板 |
|---------|------------|
| 牵手前奏 | "walking close together, arms naturally swinging near each other" |
| 牵手瞬间 | "hands gently clasped in a natural, comfortable grip" |
| 拥抱 | "a warm, friendly embrace" (避免 "tight", "intimate") |
| 亲吻脸颊 | "a light, friendly kiss on the cheek" |

---

## 遗漏点2: Shot 19 三个气泡重叠 + 对话归属错误 ⭐

### 原始数据

```python
"chinese_text": [
    "Cici：「你是做什么工作的？」",      # Cici问
    "Kai：「互联网，产品经理。你呢？」",  # Kai答
    "Cici：「设计师，做品牌视觉的。」"    # Cici答
]
```

### 实际渲染结果

| 预期 | 实际 | 问题 |
|-----|-----|-----|
| 3个气泡 | 2个气泡 | Kai的回答消失了 |
| Cici, Kai, Cici | Cici, Cici | 归属显示错误 |

### 问题分析

1. **气泡数量限制**: 当前TextOverlay可能只支持2个气泡
2. **第三个气泡被丢弃**: Kai的回答被完全忽略
3. **显示归属错误**: 即使修复了前缀问题，对话归属逻辑本身有问题

### 通用化解决方案

**方案A - 支持多气泡（3+）**:
```python
def add_multiple_speech_bubbles(self, image, bubbles: List[SpeechBubbleConfig]):
    """支持3个以上气泡，自动调整位置避免重叠"""
    # 计算每个气泡的安全位置
    # 垂直堆叠或交错排列
```

**方案B - 合并同一人连续对话**:
```python
# 如果连续两条是同一人，合并为一个气泡
# Cici: "你是做什么工作的？" + "设计师..." → 一个气泡
```

**方案C - 分镜拆分**:
- 3条对话拆成2个shot
- 每个shot最多2个气泡

---

## 遗漏点3: Shot 34 右下角诡异的手/身体

### 图片观察

```
场景: Kai开车，Cici在副驾驶
问题区域: 右下角
```

**诡异之处**:
1. Cici的手出现在画面右下角，位置不自然
2. 手似乎放在Kai的大腿/座位区域
3. 红色围巾/衣物在右边缘出现突兀

### 原因分析

1. **构图问题**: Prompt要求展示驾驶场景，但没有明确限定Cici的可见范围
2. **AI补全**: 模型试图在画面边缘补全Cici的存在，导致不自然的手部出现

### 通用化解决方案

**Prompt优化**:
```
修改前:
"Kai driving... Cici visible in passenger seat"

修改后:
"MEDIUM SHOT of Kai driving, shot from passenger side angle.
Focus on Kai's profile and hands on steering wheel.
Cici NOT VISIBLE in this shot - camera is from her POV."
```

**或明确限定构图边界**:
```
"Frame ends at center console. Do NOT include partial body parts
at frame edges. All visible body parts must be complete and natural."
```

---

## 遗漏点4: Shot 18 确认（只有1个气泡，不是3个）

### 重新审查

查看shot_18的数据：
```python
"chinese_text": ["Cici：「好呀，你做主。」"]  # 只有1条
```

**结论**: Shot 18 只有1条对话，不存在3个气泡重叠的问题。
用户可能记错了shot编号，实际是**Shot 19**有3条对话的重叠问题。

---

## 更新后的问题总结

| # | 问题 | 深入分析状态 | 解决方案状态 |
|---|-----|------------|------------|
| 1 | shot_01 双手腕 | ✅ AI解剖限制 | P1 prompt约束 |
| 2 | shot_03 六指 + 气泡重叠 | ✅ | P1 prompt + P0 已修复 |
| 3 | Speaker前缀 | ✅ | ✅ Backend已修复 |
| 4 | shot_05 底部留白 | ✅ | P2 prompt约束 |
| 5 | 气泡遮脸 | ✅ | ✅ Backend已修复 |
| 6 | 挽手亲密度 | ✅ | P2 故事内容 |
| **7** | **shot_28 内容安全** | ✅ **已深入分析** | **AI-ML重写prompt** |
| 8 | 心理/旁白底部重叠 | ✅ | P1 碰撞检测 |
| **9** | **shot_34 诡异手/身体** | ✅ **已深入分析** | **AI-ML优化构图prompt** |
| 10 | shot_40 气泡遮脸 | ✅ | ✅ Backend已修复 |
| **新增** | **shot_19 3气泡问题** | ✅ **已深入分析** | **Backend支持多气泡** |

---

## AI-ML 新增任务

基于深入分析，@AI-ML 需要额外处理：

### TASK-7: Shot 28 安全Prompt重写 [P1]

```python
# 修改前（触发安全限制）
"palm slightly open in unconscious invitation"
"The tension is palpable"

# 修改后（安全）
"palm relaxed in natural walking posture"
"A moment of quiet anticipation"
```

### TASK-8: Shot 34 构图优化 [P2]

```
明确限定：
"Frame ends at center console. Do NOT include partial body parts
at frame edges."
```

---

**@PM**
2026-02-02 10:30
