# BGM Prompt 模板

> AI-ML Agent 音乐 Prompt 工程知识库 — 5 层 BGM Prompt 构建法 + 完整示例

---

## 五层结构概述

BGM prompt 的核心思想：**从抽象到具体，从场域到灵魂**。

每一层回答一个问题：

| 层 | 名称 | 回答的问题 | 占比 |
|----|------|-----------|------|
| 1 | 场域 (Field) | 这是什么类型的音乐？ | 10% |
| 2 | 骨架 (Skeleton) | 速度和节奏骨架是什么？ | 10% |
| 3 | 肌肉 (Muscle) | 用什么乐器、什么质感？ | 25% |
| 4 | 呼吸 (Breath) | 情绪怎么发展？ | 25% |
| 5 | 灵魂 (Soul) | 这段音乐要讲什么故事？ | 30% |

> **为什么"灵魂"层最重要？** 因为 AI 音乐模型对叙事性描述的响应比纯技术参数更丰富。一句好的意象描述能引导模型产生比十个参数更精准的结果。

---

## 模板

```
[场域] {genre}, {subgenre}. 
[骨架] {tempo description or BPM}, {time signature if non-standard}. 
[肌肉] {primary instrument} with {secondary instrument}, {texture description}. 
[呼吸] {emotion start} → {emotion development} → {emotion resolution}. 
[灵魂] {1-2 sentences of narrative imagery from the story}.
```

### 各层详解

#### [场域] Field — 流派定锚

**作用**: 给 AI 模型一个基础音乐框架，避免方向偏差。

**写法规则**:
- 先写大类，再写子类: `cinematic, neoclassical` 而非仅 `neoclassical`
- 可以用 "with {元素}" 做融合: `Chinese traditional with ambient electronic`
- 最多 2-3 个流派标签，过多会导致模型困惑

**示例**:
```
Cinematic, neoclassical.
Lo-fi hip-hop, jazz-influenced.
Chinese traditional with modern ambient elements.
Indie pop, acoustic-driven.
Dark ambient, cinematic tension.
```

#### [骨架] Skeleton — 速度与节奏

**作用**: 建立时间框架，决定音乐的"心跳"。

**写法规则**:
- BPM 数值精确但允许浮动: `around 75 BPM` 或 `slow walking pace, 70-80 BPM`
- 非标准拍号要明确: `in 3/4 waltz time` 或 `6/8 flowing rhythm`
- 可以描述节奏变化: `starts at 60 BPM, gradually accelerating to 100`
- 用比喻增强表达: `heartbeat pace` `breathing rhythm` `ticking clock pace`

**示例**:
```
Slow and deliberate, around 65 BPM, like a grandfather's measured footsteps.
Moderate groove, 95 BPM, with a gentle swing feel.
Starts sparse and rubato, settles into a steady 80 BPM.
Urgent and driving, 140 BPM, relentless forward motion.
Waltz time, 3/4, around 100 BPM, graceful but slightly melancholic.
```

#### [肌肉] Muscle — 乐器与质感

**作用**: 定义音乐的色彩和触感。

**写法规则**:
- 明确主次: `{primary} with {secondary}` — 主乐器承载旋律，次乐器铺底
- 描述质感: 不只说乐器名，还说它听起来像什么
- 加 texture 描述: vinyl crackle, tape warmth, room reverb 等
- 负面描述也有效: `no drums` `without heavy bass` `avoid bright synths`

**示例**:
```
Warm felt piano with gentle cello, wrapped in soft room reverb. Occasional harp arpeggios like raindrops.
Lo-fi Rhodes with brushed drums and vinyl crackle. Muted trumpet enters halfway, distant and warm.
Guzheng and xiao as primary voices, supported by subtle ambient pad. No percussion — let silence breathe.
Acoustic guitar (nylon) with upright bass pizzicato and light cajon. Intimate, close-mic'd, like recording in a small room.
Full string orchestra with solo violin above. French horn adds warmth in the mid-range. Timpani only at the climax.
```

#### [呼吸] Breath — 情绪弧线

**作用**: 音乐不是静态的，它要"呼吸"。这一层定义情感的起承转合。

**写法规则**:
- 用箭头表示变化: `A → B → C`
- 3-4 个阶段为佳，太多会模糊
- 描述变化方式: "gradually"(渐变), "suddenly"(突变), "subtly"(微妙)
- 结尾比开头更重要 — 音乐的最后几秒决定情感记忆

**示例**:
```
Gentle nostalgia → slowly building warmth → quiet contentment that lingers.
Uneasy tension → mounting dread → sudden silence → single note of clarity.
Playful curiosity → excited discovery → warm satisfaction.
Deep sadness → painful acceptance → bittersweet peace, like tears drying in sunlight.
Nervous anticipation → burst of joy → settling into calm happiness.
```

#### [灵魂] Soul — 故事意象

**作用**: 这是最关键的一层。把故事画面化为声音意象，给 AI 模型最直接的情感锚点。

**写法规则**:
- 用具体意象而非抽象概念: "像外公熬秋梨膏时厨房里升起的蒸汽" 而非 "温暖的回忆"
- 中英文混写也行，但意象要清晰
- 1-2 句话，不超过 40 词
- 可以引用故事原文中最有画面感的句子
- 这不是歌词，是"音乐应该让人联想到什么"

**示例**:
```
Like the steam rising from a grandmother's kitchen on a winter morning — you didn't know it was precious until years later.
The last train of the night pulling away, platform lights reflecting on wet ground, someone standing still among the crowd.
A child's paper airplane caught in an updraft, spinning higher than expected, both thrilling and terrifying.
Two cups of tea growing cold on the table between them, all the important words already spoken in the silence.
Autumn leaves pressing against a rain-streaked window, the sound of an old song playing in the next room.
```

---

## 完整示例

### 示例 1: 温馨家庭 — 外公的秋梨膏

**故事背景**: 外公每年秋天都会给孙女熬秋梨膏。厨房里蒸汽升腾，琥珀色的梨膏在铜锅里冒着小泡。多年后孙女独自在异乡，闻到类似的甜香时，突然泪流满面。

```
[场域] Cinematic, neoclassical with subtle Chinese traditional elements.
[骨架] Slow and unhurried, around 72 BPM, like the patient stirring of a copper pot.
[肌肉] Warm felt piano as the core voice, accompanied by soft cello. Guzheng enters gently in the second half like a memory surfacing. Subtle vinyl crackle and room reverb throughout — like listening through the haze of years.
[呼吸] Quiet domestic warmth → deepening tenderness → a swell of bittersweet recognition → gentle fade like steam disappearing.
[灵魂] The amber glow of autumn pear syrup bubbling in a copper pot, steam curling upward like years dissolving — you didn't know this ordinary kitchen moment was the most precious thing you'd ever lose.
```

**完整 prompt (合并后可直接使用)**:
```
Cinematic, neoclassical with subtle Chinese traditional elements. Slow and unhurried, around 72 BPM, like the patient stirring of a copper pot. Warm felt piano as the core voice, accompanied by soft cello. Guzheng enters gently in the second half like a memory surfacing. Subtle vinyl crackle and room reverb throughout — like listening through the haze of years. The music moves from quiet domestic warmth through deepening tenderness into a swell of bittersweet recognition, then gently fades like steam disappearing. The amber glow of autumn pear syrup bubbling in a copper pot — you didn't know this ordinary kitchen moment was the most precious thing you'd ever lose.
```

---

### 示例 2: 紧张冲突 — 年夜饭上的战争

**故事背景**: 除夕夜的家庭聚餐，表面是和乐融融的年夜饭，暗流涌动。爸爸和二叔因为老房拆迁的分配问题，从互相敬酒到冷嘲热讽，最终摔了筷子。奶奶在角落里默默流泪。

```
[场域] Cinematic, dark acoustic with jazz-influenced tension.
[骨架] Moderate tempo, 88 BPM, with an underlying pulse like a ticking time bomb disguised as chopsticks tapping on porcelain.
[肌肉] Upright piano playing stiff, polite phrases — gradually becoming more dissonant. Pizzicato cello mimics the nervous energy under the table. Muted trumpet adds sardonic commentary. Low strings enter as the argument surfaces. No percussion until the climax — then a single sharp snare hit like a slap.
[呼吸] Forced cheerfulness (slightly off-key major) → simmering tension (chromatic creep) → ugly eruption (dissonant clash) → devastating silence → solo piano, broken and simple, like a grandmother's quiet weeping.
[灵魂] A dining table groaning with abundance, red lanterns overhead, but the real feast is old grievances served cold. The sound of porcelain breaking is quieter than the silence that follows — and in that silence, an old woman's chopsticks tremble, holding nothing.
```

**完整 prompt (合并后可直接使用)**:
```
Cinematic, dark acoustic with jazz-influenced tension. Moderate tempo, 88 BPM, with an underlying pulse like chopsticks tapping nervously on porcelain. Upright piano playing stiff, polite phrases that gradually become more dissonant. Pizzicato cello mimics nervous energy, muted trumpet adds sardonic commentary. Low strings enter as the argument surfaces. No percussion until the climax — then a single sharp snare hit. The music moves from forced cheerfulness through simmering chromatic tension into an ugly dissonant eruption, then devastating silence, ending with a solo piano, broken and simple. A dining table groaning with abundance, red lanterns overhead, but the real feast is old grievances — the sound of porcelain breaking is quieter than the silence that follows.
```

---

### 示例 3: 都市治愈 — 终点站前的余温

**故事背景**: 深夜末班地铁，只剩几个乘客。一个加班到很晚的年轻人靠在扶手上快要睡着，旁边坐着一个拎着保温桶的阿姨，从保温桶里递过来一个热包子。"小伙子，吃个包子吧，我孩子也在外面上班。" 地铁到站的铃声响了，他们各自下车，再也没有见过。

```
[场域] Lo-fi, indie acoustic with cinematic warmth.
[骨架] Gentle rolling rhythm, 76 BPM, like the sway of a late-night subway car. Slight rubato — not metronomically precise, human and imperfect.
[肌肉] Rhodes electric piano with tape warmth as the foundation. Soft acoustic guitar (fingerpicking) enters like a kind gesture. Gentle brush drums provide the subway-car sway. A single, distant trumpet plays a brief phrase — like a stranger's unexpected warmth. Lo-fi vinyl texture and subway ambient sounds woven throughout. 
[呼吸] Exhausted numbness → surprised by small kindness → warmth spreading through the chest → gentle parting — not sad, just the quiet beauty of strangers caring for strangers.
[灵魂] The fluorescent hum of the last subway car at midnight, a steamed bun still warm in your hands from someone else's mother — the most tender moments have no names, no second meetings, just the lingering heat against your palms as the doors close.
```

**完整 prompt (合并后可直接使用)**:
```
Lo-fi, indie acoustic with cinematic warmth. Gentle rolling rhythm, 76 BPM, like the sway of a late-night subway car. Rhodes electric piano with tape warmth as the foundation, soft fingerpicked acoustic guitar enters like a kind gesture. Gentle brush drums provide subway-car sway. A single distant trumpet plays a brief phrase like unexpected warmth from a stranger. Lo-fi vinyl texture throughout. The music moves from exhausted numbness through surprised kindness into warmth spreading through the chest, ending in gentle parting — not sad, just the quiet beauty of strangers caring. The fluorescent hum of the last subway car at midnight, a steamed bun still warm in your hands from someone else's mother — the most tender moments have no names, just lingering heat as the doors close.
```

---

## 实用技巧

### 1. Prompt 长度指南
| 用途 | 推荐长度 | 说明 |
|------|---------|------|
| Mureka API BGM | 80-150 词 | 合并五层，去掉标签，保留核心 |
| 内部文档参考 | 150-250 词 | 带五层标签的完整版本 |
| 快速草稿 | 40-60 词 | 场域+灵魂两层即可 |

### 2. 避免的写法
| 避免 | 为什么 | 改为 |
|------|--------|------|
| "sad music" | 太泛，AI 不知道哪种 sad | "bittersweet longing, like watching old photos fade" |
| "120 BPM, C major, 4/4" | 纯技术参数缺乏灵魂 | "moderate pace like a heartbeat calming down, bright but not naive" |
| "像周杰伦的歌" | 版权风险+AI 可能不理解 | 描述具体的音乐特征而非引用艺术家 |
| "happy and sad at the same time" | 矛盾但无具体方向 | "major key melody over minor key harmony — smiling through tears" |
| 堆砌 10 个乐器 | AI 无法同时处理太多 | 聚焦 2-3 个核心乐器，其余用 "subtle" "occasional" 修饰 |

### 3. 故事特定的灵魂层写法
- 从故事文本中提取**最有画面感的一句话**
- 用英文重写这个画面，加入**感官细节**（温度、光线、气味、触感）
- 避免直接翻译，而是**重新创造一个意象**
- 结尾留一个**情感钩子** — 让人想知道接下来会怎样

### 4. 五层可以不完整
- 如果故事场景非常明确，可以只写 [场域]+[灵魂]
- 如果需要精确控制，五层全写
- [呼吸] 层对于短 BGM（<30秒）可以省略
- [骨架] 层在不确定时可以用 "moderate pace" 让 AI 自行判断
