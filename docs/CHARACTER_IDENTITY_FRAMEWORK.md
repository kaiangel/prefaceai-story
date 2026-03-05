# Character Identity Framework

> 角色一致性系统框架 — Identity Anchors + Narrative Variables
>
> 来源: DEC-012 决策 1 (Founder 提出)
> 版本: v1.0
> 创建: 2026-02-26 @AI-ML

---

## 一、核心概念

角色视觉一致性的本质是：**哪些特征必须锁定不变，哪些特征可以随叙事动态变化。**

当前系统通过 Pro 模型 + 参考图（portrait + fullbody）实现了 3 人场景 100% 一致性，但在远景、侧面、动态镜头中仍可能丢失小配饰（如眼镜）。

本框架将角色视觉特征分为两类：

| 类别 | 定义 | 规则 |
|------|------|------|
| **Identity Anchors** | 角色的"身份证"特征 | 每个 shot 必须锁定，不可缺失 |
| **Narrative Variables** | 随叙事变化的特征 | 6 层动态变化，服务于故事表达 |

---

## 二、Identity Anchors（身份锚点）

**定义**: 观众凭此"认出"角色的核心特征。即使在远景、剪影、背影中，这些特征仍应尽量可辨。

### 2.1 锚点类型

| 锚点类型 | 说明 | 示例 |
|---------|------|------|
| **面部骨骼结构** | 脸型、五官比例 | 方脸 vs 瓜子脸、高颧骨 |
| **身体比例** | 身高、体型、肩宽 | 高瘦 vs 矮壮、宽肩 |
| **肤色** | 皮肤色调 | fair / tan / dark |
| **发型+发色** | 最强视觉识别特征 | 黑色短发、深棕色长波浪 |
| **标志性配饰** | 角色专属的关键物件 | 眼镜、疤痕、红围巾、银项链 |
| **基础服装设计** | 角色的标准穿搭 | 白衬衫+蓝领带、奶油色毛衣+牛仔裤 |

### 2.2 标志性配饰的特殊地位

**标志性配饰是最容易丢失、但对角色辨识度最关键的锚点。**

E2E 测试发现：陈默的薄框金属方框眼镜在 19 个面部可见 shot 中丢失了 6 个（68% 一致性）。远景和动态镜头中 Pro 模型倾向于"简化"小物件。

**应对策略**:

1. **image_prompt 强调**: 每个 shot 的 prompt 中必须明确提及标志性配饰
   ```
   ❌ BAD: "Chen Mo walks in the rain"
   ✅ GOOD: "Chen Mo (WEARING thin metal-frame rectangular glasses) walks in the rain"
   ```

2. **参考图传递确认**: 确保 fullbody 参考图中配饰清晰可见，且每个 shot 传入完整参考图

3. **Stage 2 角色设计标注**: 在 `physical` 字段中为标志性配饰添加 `IDENTITY_ANCHOR` 标记
   ```json
   {
     "physical": {
       "distinctive_marks": ["thin metal-frame rectangular glasses (IDENTITY_ANCHOR)"]
     }
   }
   ```

### 2.3 在 image_prompt 中的体现

```
# 每个 shot prompt 的角色描述模板:

{character_name} — IDENTITY ANCHORS:
- [hair]: {hair_color} {hair_style}
- [face]: {face_shape}, {skin_tone} skin
- [signature]: {distinctive_marks} (MUST BE VISIBLE)
- [outfit]: {clothing_description}
```

---

## 三、Narrative Variables（叙事变量）

**定义**: 角色随故事进展而合理变化的视觉特征。这些变化是有意为之的，服务于叙事。

### 3.1 六层叙事变量

#### Layer 1: 情绪层 (Emotional State)

| 变化维度 | 示例 |
|---------|------|
| 表情 | 微笑 → 皱眉 → 惊讶 → 哭泣 |
| 眼神 | 空洞 → 锐利 → 温柔 → 泪光 |
| 肢体语言 | 挺胸 → 蜷缩 → 颤抖 → 放松 |

**prompt 示例**:
```
Shot 1: "Chen Mo walks with slumped shoulders, exhaustion visible in his half-closed eyes"
Shot 15: "Chen Mo stands tall with soft warmth in his eyes, a gentle smile forming"
```

#### Layer 2: 物理状态层 (Physical State)

| 变化维度 | 示例 |
|---------|------|
| 疲劳程度 | 精神焕发 → 黑眼圈 → 步履蹒跚 |
| 伤痕/汗水 | 干净 → 额头冒汗 → 浑身湿透 |
| 温度反应 | 正常 → 手缩袖中 → 哈气取暖 |

#### Layer 3: 装备层 (Equipment/Accessory State)

| 变化维度 | 示例 |
|---------|------|
| 服装变化 | 穿着外套 → 脱下搭在手臂上 |
| 道具持有 | 撑伞 → 收伞 → 拿在手里 |
| 配饰位置 | 围巾系紧 → 围巾松垂 |

**关键规则**: 即使装备状态变化，Identity Anchors 不变（脱了外套但眼镜仍在）。

#### Layer 4: 环境交互层 (Environmental Interaction)

| 变化维度 | 示例 |
|---------|------|
| 光影投射 | 路灯下的暖光 → 霓虹灯的彩色反射 |
| 天气痕迹 | 干燥 → 雨水淋湿头发和衣服 |
| 环境附着 | 干净 → 树叶粘在肩上 → 泥点溅在裤脚 |

#### Layer 5: 可见度层 (Visibility/Framing)

| 变化维度 | 说明 |
|---------|------|
| 身体可见范围 | 全身 → 半身 → 特写 → 只露出手 |
| 角度 | 正面 → 侧面 → 背影 → 俯视 |
| 遮挡 | 无遮挡 → 伞遮挡半脸 → 玻璃反射 → 剪影 |

**关键规则**: 即使只能看到剪影/背影，可辨识的锚点（发型轮廓、体型、标志色服装）应仍可暗示角色身份。

#### Layer 6: 时间层 (Temporal Changes)

| 变化维度 | 适用场景 |
|---------|---------|
| 年龄变化 | 回忆 vs 现实（年轻白川 vs 老年白川） |
| 服装磨损 | 长篇故事中衣物逐渐变旧 |
| 季节变化 | 夏装 → 冬装（同一角色） |
| 发型变化 | 时间跳跃后发型微调 |

**关键规则**: 时间层变化最大，但面部骨骼结构和标志性特征（疤痕、眼镜）应保持不变。

### 3.2 各层优先级

在 prompt 空间有限时，按以下优先级分配描述词:

```
1. Identity Anchors (必须)     — 每个 shot
2. Layer 1 情绪层 (高优)       — 每个 shot
3. Layer 3 装备层 (中优)       — 有变化时
4. Layer 4 环境交互 (中优)     — 有变化时
5. Layer 2 物理状态 (低优)     — 关键时刻
6. Layer 5 可见度 (由镜头决定)  — 隐式通过 camera angle 表达
7. Layer 6 时间层 (极少)       — 仅在回忆/时间跳跃时
```

---

## 四、在 Stage 2 (CharacterDesigner) 中的应用

角色设计阶段应明确区分 anchors 和 variables:

```json
{
  "id": "char_001",
  "name": "陈默",
  "name_en": "Chen Mo",
  "identity_anchors": {
    "face_shape": "rectangular with defined jawline",
    "skin_tone": "light",
    "hair": "short neat black hair, side-parted",
    "signature_features": ["thin metal-frame rectangular glasses"],
    "base_outfit": "white dress shirt, blue tie, navy slacks, black leather shoes"
  },
  "narrative_defaults": {
    "expression": "calm, reserved",
    "posture": "upright, slightly stiff",
    "accessories_state": "holding black umbrella, brown leather briefcase",
    "physical_state": "tired but composed"
  }
}
```

**注意**: 这是未来的理想数据结构。当前系统的 `physical` + `clothing` 字段已覆盖大部分锚点信息，但未显式区分 anchors 和 variables。后续迭代可逐步引入。

---

## 五、在 image_prompt 中的完整应用示例

### 示例：陈默在雨中（Shot 5, 双人撑伞）

```
IDENTITY ANCHORS — Chen Mo (char_001):
- WEARING thin metal-frame rectangular glasses (MUST BE VISIBLE even in rain)
- Short neat black hair, side-parted
- Light skin, rectangular face with defined jawline
- White dress shirt with blue tie (may be loosened), navy slacks

NARRATIVE STATE (Shot 5):
- Emotion: tentative concern, eyebrows slightly raised
- Physical: shirt dampened by rain on exposed shoulder
- Equipment: holding large black umbrella, tilted toward Lin Xiao
- Environment: warm amber streetlight casting glow on wet surfaces
- Framing: medium shot, three-quarter view

Chen Mo stands at the bus stop holding his large black umbrella tilted toward
Lin Xiao, his exposed right shoulder darkened by rain. His thin metal-frame
rectangular glasses reflect the amber streetlight. His white shirt is slightly
damp, blue tie loosened. His expression shows tentative concern — eyebrows
slightly raised, lips pressed together, maintaining respectful distance.
```

---

## 六、已知限制与后续方向

### 当前限制

1. **Pro 模型在远景中丢失小配饰**: 即使 prompt 强调，Gemini Pro Image 在 wide shot 中仍可能省略眼镜等细节
2. **Stage 2 未显式区分 anchors/variables**: 当前 physical + clothing 字段是扁平结构
3. **image_prompt 空间有限**: 80-100 词难以同时覆盖场景、情绪、所有锚点

### 后续迭代方向

| 方向 | 优先级 | 说明 |
|------|--------|------|
| prompt 中强调标志性配饰 | P1 | 在 `_build_character_description()` 中为 `distinctive_marks` 加 MUST BE VISIBLE |
| Stage 2 输出增加 identity_anchors 字段 | P2 | 显式标记哪些是锁定特征 |
| 单张 shot 重新生成功能 | P1 | 配饰丢失时可单独重跑 |
| 参考图质量优化 | P2 | 确保参考图中标志性配饰清晰突出 |

---

*本文档为 AI-ML 负责的角色一致性设计规范，后续随系统迭代更新。*
