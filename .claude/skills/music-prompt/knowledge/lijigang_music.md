# 李继刚 Prompt 哲学在音乐生成中的应用

> 将李继刚对 Prompt 的核心认知——压缩、场域、共振、种子——迁移到音乐生成领域
> 来源: `/Users/kaisbabybook/AIFun/Lijigang/李继刚分析笔记.md` + `李继刚_system_prompt_含示例对话.md`

---

## 一、四大原则迁移

### 1. 压缩 — "金句怎么来？压缩而来"

**在文本 prompt 中**: 把复杂思想压成最少词表达，每个字都有意义。

**在音乐 prompt 中**: 每个词都要携带**音乐信息**。

| 坏例子 | 信息密度 | 好例子 | 信息密度 |
|--------|:-------:|--------|:-------:|
| "sad slow piano music" | 低 | "felt piano, heartbeat rubato" | 高 |
| "happy upbeat song" | 低 | "ukulele shuffle, sun-dappled 110 BPM" | 高 |
| "dramatic orchestral" | 低 | "brass fanfare over timpani roll, Wagner-esque grandeur" | 高 |

**压缩的关键**: 不是字数少，是**每个词都不可替代**。
- "sad" 可以被删掉而不影响（因为太泛了）
- "felt piano" 不能被删掉（它指定了一种特殊的钢琴音色——毛毡消音的温暖声音）

### 2. 场域 — "与其直接下达指令，不如创造一个能够自然唤起该模式的情境"

**在文本 prompt 中**: 不说"请写一篇悲伤的文章"，而是创造一个让悲伤自然涌现的场景。

**在音乐 prompt 中**: 不说"请生成悲伤的音乐"，而是**描绘一个让悲伤音乐自然生长的场景**。

```
❌ 命令式: "Generate a sad and melancholic piano piece"
✅ 场域式: "Solo piano in an empty concert hall, 3 AM. 
    The sustain pedal held too long, notes bleeding into each other 
    like memories that refuse to separate."
```

音乐模型读到"empty concert hall, 3 AM"，会自然选择：
- 大量混响（空旷大厅）
- 缓慢的速度（深夜的寂静）
- 小调和弦（孤独的氛围）
- 踏板延音（notes bleeding into each other）

你不需要命令它做这些选择——**场域自然唤起了这些选择**。

### 3. 种子 — "拿到种子，需要压缩。种子生长，需要自由"

**在文本 prompt 中**: Prompt 是种子，不是图纸。给核心信息，让 LLM 自由生长。

**在音乐 prompt 中**: 给足**关键约束**（风格+乐器+情绪方向），然后**放手**让模型自由编曲。

```
❌ 过度规定（图纸式）:
"Piano plays C minor chord, then G minor, then Ab major. 
 Tempo 72 BPM. Verse 16 bars. Chorus 8 bars. Bridge 4 bars.
 Dynamics: verse pp, chorus mf, bridge f."

✅ 种子式:
"Minimalist piano, C minor tonality. Starts sparse, single notes 
 like drops of water. Gradually layers, building to a restrained 
 emotional peak before dissolving back to silence."
```

种子给了：调性（C minor）、质感（minimalist）、情绪曲线（sparse→build→dissolve）。
模型在这个框架内自由选择具体的和弦进行、节奏型、力度变化。

### 4. 共振 — "Prompt = Field(LLM, Human)"

**在文本 prompt 中**: 最好的 prompt 在 LLM 的计算空间和人的认知空间之间产生共振。

**在音乐 prompt 中**: **Prompt = Field(Music Model, Human Emotion)**

最好的音乐 prompt 让模型"理解"你的情感意图，生成的音乐让听众"感受到"同样的情感。

**共振发生的条件**:
- prompt 里有**具体的感官细节**（不是抽象的情绪标签）
- prompt 里有**动态变化**（不是静态的一个 mood）
- prompt 里有**留白**（不过度规定，给模型诠释空间）

```
高共振 prompt:
"Acoustic guitar fingerpicking in a sunlit kitchen. 
 Coffee steam rising. Someone humming a half-remembered tune. 
 Warm but with a thread of something unresolved — 
 like a conversation you keep meaning to have."
```

这段 prompt 不说"温馨但带点遗憾"，而是用画面让你**自己感受到**温馨和遗憾。模型也会"感受到"，因为它的训练数据里有无数关于厨房、晨光、低哼的关联。

---

## 二、5 层 Prompt 结构（场域→骨架→肌肉→呼吸→灵魂）

这个结构本身就是李继刚"抽象之梯"的应用——从最抽象（流派场域）到最具象（叙事画面）：

```
[第 1 层：场域 Genre]     ← 抽象的顶端，定义"哪个世界"
     ↓
[第 2 层：骨架 Tempo]     ← 节奏框架
     ↓
[第 3 层：肌肉 Instruments] ← 具体的音色
     ↓
[第 4 层：呼吸 Mood Curve]  ← 情绪动态
     ↓
[第 5 层：灵魂 Imagery]    ← 具象的底端，从故事提炼的画面
```

**李继刚的"得意忘言"**: 写完 prompt 后回读一遍——如果删掉某个词不影响理解，删掉它。最终留下的每个词都是不可替代的。

---

## 三、序话Story 特有的优势

我们有一个大多数音乐 prompt 写作者没有的东西：**完整的故事上下文**。

普通用户写音乐 prompt 只能靠想象："帮我生成一段悲伤的钢琴曲"。
我们有：
- 故事大纲（title, logline, mood, plot_points）
- 角色设定（性格、情感旅程）
- 分场剧本（每场戏的氛围、情绪节拍）
- 分镜脚本（视觉色调、光影、构图）

**这些都是"灵魂层"的原料**。

用 Haiku 读完故事内容后，提取 3-5 个**情感锚点**（故事中情绪转折最强的时刻），然后用这些锚点的画面意象构建音乐 prompt 的"灵魂层"——这样每个故事的 BGM 都是**只属于它的**。

---

## 四、避免同质化的核心策略

**同质化的根源**: prompt 只用抽象标签（mood="温馨"），没有具象细节。

**解药**: 从故事内容中提取**只属于这个故事的**感官细节。

| 故事 | mood | 烂 prompt | 好 prompt（有灵魂） |
|------|------|----------|-------------------|
| 外公的秋梨膏 | 温馨 | "warm family music" | "bamboo flute over soft erhu, mountain morning mist, grandfather's weathered hands stirring a copper pot" |
| 年夜饭上的战争 | 紧张 | "tense dinner music" | "muted piano chords under chopstick percussion, steam rising like suppressed anger, silence between bites heavier than shouting" |
| 最后一投 | 热血 | "energetic sports music" | "sneaker squeak on hardwood, heartbeat bass drum accelerating, crowd noise swelling then muting to a single breath" |

三个 prompt 的"灵魂层"完全不同——因为它们来自完全不同的故事画面。
