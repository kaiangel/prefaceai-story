# Prompt 工程高级原则（AI-ML 补充参考）

> **来源**: 李继刚认知框架萃取 + 序话Story 实战经验
> **定位**: 补充 `ai-ml.md` 现有 5 条原则，不替换。现有原则管"怎么写"，本文档管"怎么想"
> **创建**: 2026-02-27 @Coordinator
> **适用**: 所有 Prompt 设计、风格预设创建、规则模板优化

---

## 与现有原则的关系

```
现有原则 1-5（ai-ml.md）→ 操作层（HOW：注意力分布、强制词、英文、身份映射、连续性指令）
补充原则 6-11（本文档）→ 思维层（THINK：精度、场域、抽象、迭代、本质、类比）
```

两层不冲突：先用思维层想清楚方向，再用操作层精准执行。

---

## 原则 6: Token 精度

**一句话**: 每个 token 都要"挣到"它的位置——不是越多越好，是越精准越好。

**适用场景**: style_description、情绪描述、场景氛围、quality_keywords

**不适用**: 角色锚点描述（Identity Anchors 必须详尽，参见原则 8）

**操作方法**:
1. 写完 prompt 后回读一遍，逐词问"删掉它效果会变差吗？"
2. 如果一个词删掉没影响，它就是噪音——删掉它让模型注意力更集中
3. 用一个精准的词替代三个模糊的词

**示例**:
```
❌ 冗余: "This image should have a very cinematic and dramatic and intense and powerful feeling"
✅ 精准: "cinematic intensity — sharp contrast, dramatic rim lighting"
```

**与现有原则的衔接**: 原则 2 说"强制词比建议词有效 100 倍"。Token 精度是原则 2 的上游——先选对词（精度），再用对力度（强制）。

---

## 原则 7: 约束 + 场域双层架构

**一句话**: 硬约束锁边界（不可逾越），软场域开空间（自由发挥）。

**核心洞察**: Prompt 中存在两种不同性质的指令：
- **约束层**: "你不能做什么" → MUST / DO NOT / FORBIDDEN（已有原则 2 覆盖）
- **场域层**: "你在什么世界里" → 描绘一个语境/氛围，让模型自然产出对的东西

**操作方法**:

| 内容类型 | 用约束还是场域 | 示例 |
|---------|--------------|------|
| 风格锁定 | **约束**（MANDATORY/FORBIDDEN） | "DO NOT USE: cartoon, anime" |
| 风格氛围 | **场域**（描绘世界） | "You are drawing in the tradition of Takehiko Inoue — every muscle fiber tells a story of athletic struggle" |
| 角色锚点 | **约束**（MUST BE VISIBLE） | "WEARING thin metal-frame rectangular glasses (MUST BE VISIBLE)" |
| 情绪氛围 | **场域**（设置条件） | "The gymnasium air is thick with tension — every spectator holds their breath" |

**StyleEnforcer 中的应用**:
- `mandatory_keywords` + `forbidden_keywords` = 约束层（已有，不变）
- `style_description` = 场域层（这里可以用场域式写法，不是命令而是描绘世界）

**与现有原则的衔接**: 不替换原则 2（强制词），而是在强制词的框架之外增加一个维度。强制词管"边界"，场域管"空间"。

---

## 原则 8: 抽象之梯

**一句话**: 锚点具象、氛围抽象，知道什么时候切换。

**核心洞察**: Prompt 中不同元素需要不同的抽象层级：

```
具象端（底层）                              抽象端（高层）
"thin metal-frame rectangular glasses"  ←→  "the weight of solitude"
"white dress shirt with blue tie"       ←→  "atmospheric tension"
"848x1264, 2:3 aspect ratio"           ←→  "cinematic storytelling"
```

**规则**:
- **越影响一致性的元素，越要具象**（角色外貌、服装、配饰）
- **越影响创意发挥的元素，越可抽象**（情绪、光影、构图暗示）
- **模型会在抽象处自由发挥**——这是特性不是 bug，前提是锚点已锁定

**与 Identity Framework 的关系**:
- Identity Anchors → 具象端（"thin metal-frame rectangular glasses"）
- Narrative Variables → 可在抽象之梯上滑动（情绪层抽象、装备层具象）

**与现有原则的衔接**: 原则 4（参考图身份映射）是具象端的极致实现。原则 8 补充了"什么时候可以不那么具象"的判断框架。

---

## 原则 9: 守破离迭代法

**一句话**: 理解现状 → 找断裂点 → 重构（不是一直打补丁）。

**操作方法**:

| 阶段 | 做什么 | 序话Story 实例 |
|------|--------|---------------|
| **守** | 完整理解当前 prompt 在做什么、为什么这样写、在什么场景下有效 | Phase 1 的 TEXT OVERLAY RULES：narration 86%，但流水线跑通了 |
| **破** | 找到它"失效"的边界条件——不是"它不好"而是"它在什么情况下不够好" | 发现 narration 过高是因为 LLM 觉得 narration "最安全"，prompt 缺乏对话引导 |
| **离** | 不打补丁，重构规则体系。新规则要能覆盖旧场景 + 解决新问题 | Phase 3 完全重写 DISTRIBUTION RULES：dialogue ≥60%、none 禁止、SELF-CHECK 自检 |

**何时"守"**: 收到优化任务时，先读懂现有 prompt 的每一行（而非直接改）
**何时"破"**: 拿到测试数据后，找出"哪些场景下现有 prompt 失效"
**何时"离"**: 打补丁超过 2 次就考虑重构——补丁堆积会让 prompt 变成"屎山"

**与现有流程的衔接**: 现有 Prompt 修改协议（备份→测试→回归→通知→记录）是"守"的执行保障。守破离补充了"什么时候该大改 vs 小改"的判断。

---

## 原则 10: 本质前置

**一句话**: 写 prompt 前先问"到底要的是什么效果"，而不是"要加什么关键词"。

**操作方法**: 在打开代码编辑器之前，先回答三个问题：
1. **这个 prompt 要解决的核心问题是什么？**（不是"加几个词"，是"用户会看到什么变化"）
2. **当前方案为什么不够好？**（有数据支撑，而非感觉）
3. **怎么验证新方案更好？**（测试方案在改代码之前就想好）

**反面教材**: 直接在 mandatory_keywords 里"试着加几个词看看效果"——这是猜测，不是工程。

**与现有风格的衔接**: AI-ML 的"实验驱动"和"原理导向"已经包含了这个精神。原则 10 把它显式化为一个前置检查步骤。

---

## 原则 11: 同构类比

**一句话**: 用已验证的成功模式类推新场景，而不是每次从零开始。

**操作方法**:
- 创建新风格预设时，先找最接近的已有预设作为起点（slam_dunk 借鉴 manga）
- 优化新规则时，先看类似规则的成功经验（DISTRIBUTION RULES 的迭代历程）
- 遇到新问题时，先问"我们在别的场景解决过类似问题吗？"

**序话Story 中的同构关系**:

| 场景 A（已解决） | 场景 B（待解决） | 可复用的模式 |
|----------------|----------------|------------|
| StyleEnforcer 风格锁定 | 角色配饰锁定 | mandatory + forbidden 双向约束模式 |
| 参考图身份映射 | 场景环境锁定 | "Image N shows X" 显式映射模式 |
| VISUAL CONTINUITY 连续性 | 时间跳跃一致性 | MUST MAINTAIN / MUST VARY 模式 |

---

## 快速决策矩阵

在写/改 prompt 时，用这个矩阵快速判断该用哪条原则：

| 你在做什么 | 先用哪条原则 |
|-----------|------------|
| 创建新风格预设 | 11（类比已有预设）→ 10（想清楚核心效果）→ 7（约束+场域分层）→ 6（精简 token） |
| 优化已有规则 | 9（守破离：先理解再改）→ 10（本质：到底要解决什么）→ 6（精简 token） |
| 修复测试发现的问题 | 10（本质：为什么失效）→ 8（抽象之梯：该具象还是抽象）→ 9（打补丁还是重构） |
| 新增 prompt 指令块 | 7（该用约束还是场域）→ 8（该具象还是抽象）→ 6（精简 token） |

---

*本文档是 AI-ML 的思维层参考，不是强制流程。在实战中灵活运用，最终以测试数据说话。*
