# 歌曲 Prompt 模板

> AI-ML Agent 音乐 Prompt 工程知识库 — 歌曲生成 Prompt 构建法 + 歌词标签系统 + 完整示例

---

## 歌曲 vs BGM 的核心区别

| 维度 | BGM | 歌曲 |
|------|-----|------|
| 人声 | 无 | 有（核心元素） |
| 歌词 | 无 | 有（需要结构标签） |
| 结构 | 自由/渐进式 | 明确的段落结构(verse/chorus) |
| 时长 | 30s-3min | 2-4min |
| Prompt 重点 | 氛围+意象 | 人声特质+歌词结构+情感叙事 |

---

## 歌曲 Prompt 模板

### A. 音乐描述部分（Music Description）

```
[风格] {genre}, {subgenre}, {era/influence}.
[人声] {vocal type}, {vocal quality description}, {language}.
[编曲] {primary instruments}, {production style}, {tempo/BPM}.
[氛围] {mood description}, {emotional arc}.
[灵魂] {narrative imagery from the story}.
```

### B. 歌词部分（Lyrics with Structure Tags）

```
[Intro]
{instrumental or vocal intro}

[Verse 1]
{歌词文本}

[Pre-Chorus]
{歌词文本}

[Chorus]
{歌词文本}

[Verse 2]
{歌词文本}

[Chorus]
{歌词文本}

[Bridge]
{歌词文本}

[Chorus]
{歌词文本}

[Outro]
{instrumental or vocal outro}
```

---

## 歌词结构标签完整列表

### 核心结构标签

| 标签 | 含义 | 使用说明 |
|------|------|---------|
| `[Intro]` | 前奏 | 可纯器乐或轻声哼唱, 10-20秒 |
| `[Verse]` / `[Verse 1]` / `[Verse 2]` | 主歌 | 叙事段落, 每段 4-8 行, 展开故事 |
| `[Pre-Chorus]` | 预副歌 | 过渡段, 2-4 行, 情绪升温, 为副歌铺路 |
| `[Chorus]` | 副歌 | 情感核心, 4-8 行, 旋律最记忆点, 可重复 |
| `[Post-Chorus]` | 副歌后段 | 副歌回味, 2-4 行, 延续高点或轻轻回落 |
| `[Bridge]` | 桥段 | 对比转折段, 4-6 行, 新视角/新情感/新和声 |
| `[Outro]` | 尾奏 | 收束, 可渐弱/重复/器乐, 10-30秒 |
| `[Interlude]` | 间奏 | 器乐段落, 无歌词, 用于场景转换 |

### 演唱指令标签

| 标签 | 含义 | 效果描述 |
|------|------|---------|
| `[Whisper]` | 耳语 | 极轻声、亲密的耳语式演唱 |
| `[Spoken]` | 念白 | 不唱而是说, 适合叙事/独白/旁白 |
| `[Rap]` | 说唱 | 有节奏的快速念白, 适合嘻哈段落 |
| `[Harmony]` | 和声 | 多声部和声段落 |
| `[Ad-lib]` | 即兴 | 自由发挥的感叹/装饰音/即兴段 |
| `[Humming]` | 哼唱 | 闭口哼唱, 无歌词, 适合温柔/梦幻段落 |
| `[Belting]` | 高声 | 全力高音演唱, 情感爆发点 |
| `[Falsetto]` | 假声 | 轻柔的假声演唱, 适合空灵段 |
| `[Vocal Break]` | 声音断裂 | 刻意的声音破音/哭腔, 情感极致 |

### 编曲动态标签

| 标签 | 含义 | 效果描述 |
|------|------|---------|
| `[Build]` | 递进 | 乐器逐层加入, 能量上升 |
| `[Drop]` | 投放 | 全部能量释放, 最大音量/最密编曲 |
| `[Breakdown]` | 分解 | 编曲精简到最少, 只留核心元素 |
| `[Instrumental]` | 器乐段 | 无人声, 纯器乐演奏 |
| `[Fade Out]` | 渐弱 | 音量逐渐降低到静默 |
| `[Silence]` | 静默 | 短暂的完全静音, 制造戏剧效果 |
| `[A Cappella]` | 无伴奏 | 只有人声, 无任何乐器 |
| `[Half-time]` | 半速 | 节奏减半, 产生飘浮/庄严感 |
| `[Double-time]` | 倍速 | 节奏加倍, 突然加速的紧迫感 |

### 组合用法示例
```
[Verse 1] [Whisper]
（耳语式演唱第一段主歌）

[Chorus] [Build]
（副歌从轻到强逐渐递进）

[Bridge] [Spoken]
（桥段用念白方式）

[Chorus] [Belting] [Drop]
（最后一遍副歌全力高声+全编曲释放）

[Outro] [Humming] [Fade Out]
（尾奏哼唱渐弱）
```

---

## 人声描述指南

### 声音类型
| 类型 | 英文 | 描述 |
|------|------|------|
| 女高音 | Soprano | 明亮、穿透、高音区, 适合抒情/灵性 |
| 女中音 | Mezzo-Soprano / Alto | 温暖、丰满、中音区, 适合叙事/情感 |
| 男高音 | Tenor | 明亮、温暖、高音区, 适合浪漫/热血 |
| 男中音 | Baritone | 沉稳、有力、中音区, 适合叙事/成熟 |
| 男低音 | Bass | 深沉、厚重、低音区, 适合庄严/力量 |
| 童声 | Children's Voice | 纯真、清澈、未经修饰, 适合天真/回忆 |

### 声音质感描述词
| 词汇 | 描述 | 适合风格 |
|------|------|---------|
| Breathy | 气声感, 带有呼吸声 | 亲密/梦幻/lo-fi |
| Raspy | 沙哑, 带有颗粒感 | 摇滚/布鲁斯/情感强烈 |
| Smooth | 丝滑, 无棱角 | R&B/爵士/流行 |
| Warm | 温暖, 中低频丰富 | 民谣/治愈/温馨 |
| Bright | 明亮, 高频突出 | 流行/indie/欢快 |
| Ethereal | 空灵, 大量混响 | 梦幻流行/ambient/灵性 |
| Raw | 未加工的真实感 | 民谣/朋克/独立 |
| Sultry | 性感低沉 | 爵士/R&B/夜晚 |
| Nasal | 鼻音感 | 特定民族风格/独特个性 |
| Powerful | 有力量的全声 | 灵魂/摇滚/高潮段 |
| Delicate | 精致纤细 | 独立流行/文艺/治愈 |

### 演唱风格提示
```
# 亲密叙事
"Soft, breathy female vocal, close-mic'd, like whispering a secret to a friend"

# 情感爆发
"Powerful tenor voice, raw and unpolished, emotion breaking through the technique"

# 怀旧复古
"Warm baritone with slight tape processing, like a voice from an old radio"

# 空灵梦幻
"Ethereal soprano with heavy reverb, floating above the instruments like morning mist"

# 都市夜晚
"Smooth, slightly raspy alto, intimate and sultry, jazz-influenced phrasing"

# 中国风
"Gentle female voice with Chinese folk singing characteristics, clear and emotive, mandarin lyrics"
```

---

## 完整示例

### 示例 1: 治愈系独立民谣 — 《煮一碗面》

**故事背景**: 在外打拼的年轻人，深夜回到出租屋，冰箱里只有半根葱和一包挂面。煮面的过程中，突然想起小时候妈妈煮面的样子——也是这样在灶台前等水开，也是这样随手加一个荷包蛋。原来自己不知不觉，已经学会了妈妈的手艺。

**Music Description**:
```
Indie folk, acoustic-driven, warm lo-fi production. Gentle female vocal, breathy and intimate, like talking to yourself in a quiet kitchen. Acoustic guitar fingerpicking with soft upright piano, minimal brush percussion. Around 78 BPM, unhurried like waiting for water to boil. The warmth of a small kitchen at midnight, steam on a cold window, the realization that you carry home inside your hands.
```

**Lyrics**:
```
[Intro] [Instrumental]

[Verse 1]
冰箱里翻出半根葱
水龙头哗啦响几声
出租屋灯泡有点黄
照着我一个人的影

[Verse 2]
锅里的水开始冒泡
挂面散开像小时候
随手磕个荷包蛋
才发觉手势那么熟

[Pre-Chorus]
什么时候开始的呢
不记得了 也不用记

[Chorus]
原来我已经学会了
妈妈煮面的样子
在没人看到的深夜
变成了最温柔的自己
一碗面而已
够了 今晚就够了

[Interlude] [Instrumental]

[Verse 3]
窗户上一层薄薄的雾
用手指画了个笑脸
明天又是新的一天
先把这碗面吃完

[Chorus]
原来我已经学会了
妈妈煮面的样子
在没人看到的深夜
变成了最温柔的自己
一碗面而已
够了 今晚就够了

[Bridge] [Spoken]
其实也没什么大不了的
就是突然发现
那些最普通的动作里
藏着最深的爱

[Chorus] [Build]
原来我已经学会了
妈妈煮面的样子
在没人看到的深夜
变成了最温柔的自己

[Outro] [Humming] [Fade Out]
嗯~嗯~嗯~
```

---

### 示例 2: 中国风流行 — 《廊桥》

**故事背景**: 江南水乡，一对青梅竹马在古廊桥上重逢。他从北京回来，她还在镇上开茶馆。十年过去，桥还是那座桥，河还是那条河，只是桥上的人已经不是当年的少年少女了。他们并肩站在桥上，说了一些可有可无的话，然后各自转身走回各自的生活。

**Music Description**:
```
Chinese pop with traditional elements, modern neoclassical production. Male vocal, warm baritone with gentle vibrato, singing in Mandarin with clear diction. Guzheng and piano as dual core instruments, supported by soft string quartet. Subtle electronic ambient pad creates modern space. 82 BPM, flowing like the river under the bridge. The sound of ten years compressed into one glance — familiar faces wearing unfamiliar expressions.
```

**Lyrics**:
```
[Intro] [Instrumental]

[Verse 1]
廊桥还在 河水还在
你站的位置 换了栏杆
我从很远的地方回来
发现近处的路最难走完

[Verse 2]
你说茶馆生意还行
我说北京冬天很冷
两句客气话之间
十年就轻轻带过了

[Pre-Chorus]
我们都变了 又好像
什么都没变

[Chorus]
站在同一座廊桥上
影子不再重叠
你往东走 我往西走
桥还是弯的
河还是弯的
只是我们 学会了直着走

[Interlude] [Instrumental]

[Verse 3]
你低头整理围巾的样子
还是十六岁那个动作
有些东西认不出了
有些东西 一辈子都认得

[Chorus]
站在同一座廊桥上
影子不再重叠
你往东走 我往西走
桥还是弯的
河还是弯的
只是我们 学会了直着走

[Bridge]
如果再晚一步回来
如果再早一步离开
所有的如果
都不如此刻
好好看你一眼

[Chorus] [Belting]
站在同一座廊桥上
影子不再重叠
你往东走 我往西走
桥还是弯的
河还是弯的
只是我们 学会了直着走

[Outro] [Whisper]
廊桥还在
河水还在
```

---

## 歌词写作指南

### 序话Story 歌词的原则

1. **画面先行**: 每一句歌词都应该能在脑海中形成一幅画面
2. **留白胜过填满**: 中文歌词的力量在于"不说出来的那部分"
3. **具体打败抽象**: "半根葱" > "简陋的食材", "栏杆换了" > "物是人非"
4. **口语化**: 序话Story 的故事是普通人的故事，歌词不要文绉绉
5. **重复的力量**: 副歌中的核心句要值得重复，每次重复都能产生新的理解层次

### 中文歌词的节奏技巧

- **字数对称**: 上下句字数尽量一致，产生节奏感
- **押韵但不刻板**: 自然的韵脚，不要为了押韵牺牲意思
- **虚词留气口**: "了、的、呢、吧" 等虚词是自然的呼吸点
- **长短交替**: 长句叙事 + 短句点睛，如 "一碗面而已 / 够了"

### Prompt 与歌词的配合

- Music description 中的氛围要与歌词情感一致
- 如果歌词有戏剧性转折，在 music description 中预告编曲变化
- 歌词中的具体意象可以反映到乐器选择中
  - 水/河 → 流水般的 guzheng arpeggios
  - 厨房 → 温暖的 acoustic guitar
  - 雨 → brush drums + rain texture
