# 跨感官联想映射

> AI-ML Agent 音乐 Prompt 工程知识库 — 画面到声音的系统性转换方法论

---

## 核心理念

**序话Story 的音乐不是"配"上去的，而是从画面中"长"出来的。**

每一帧画面都包含色彩、光影、构图、动态、情感信息 — 这些视觉参数可以系统性地映射为音乐参数（音色、力度、节奏、和声、编曲密度）。本文档提供完整的映射表，供 AI-ML Agent 在生成音乐 prompt 时参考。

---

## 一、色调 → 音色映射

### 暖色系
| 色调 | 视觉感受 | 音色映射 | 推荐乐器 |
|------|---------|---------|---------|
| 橙色 (Orange) | 温暖、亲切、活力 | 温暖中频、木质共鸣 | Acoustic guitar, warm piano, cello, soft brass |
| 金色 (Gold) | 高贵、辉煌、丰收 | 明亮温暖的泛音 | French horn, harp, grand piano, brass ensemble |
| 琥珀 (Amber) | 怀旧、柔和、蜂蜜般 | 模拟的温暖失真 | Rhodes, felt piano, nylon guitar, warm synth pad |
| 红色 (Red) | 热情、危险、激烈 | 高能量、饱和的音色 | Distorted guitar, powerful brass, full orchestra, taiko |
| 粉色 (Pink) | 柔软、浪漫、梦幻 | 柔和高频、圆润 | Celesta, music box, soft synth pad, gentle flute |
| 棕色 (Brown) | 大地、稳重、朴实 | 低频温暖、有机质感 | Acoustic bass, cajon, upright piano, warm cello |

### 冷色系
| 色调 | 视觉感受 | 音色映射 | 推荐乐器 |
|------|---------|---------|---------|
| 蓝色 (Blue) | 沉静、忧郁、深邃 | 清冷、带有泛音的通透 | Synth pad, glass piano, string harmonics, distant bell |
| 灰色 (Gray) | 中性、压抑、工业 | 去色彩感、金属质地 | Muted piano, brushed snare, distant strings, lo-fi texture |
| 银色 (Silver) | 清冷、科技、锋利 | 高频金属泛音 | Celesta, vibraphone, crystal synth, metallic percussion |
| 深蓝 (Navy) | 夜晚、神秘、深沉 | 低频 pad + 远距离泛音 | Deep synth bass, distant piano, sub bass drone |
| 紫色 (Purple) | 神秘、灵性、魔幻 | 合成+原声的混合质感 | Synth + strings blend, choir pad, processed harp |
| 青色 (Cyan/Teal) | 清新、科技、未来 | 清脆数字音色 | Digital synth, processed piano, clean electric guitar |

### 特殊色调
| 色调 | 视觉感受 | 音色映射 | 推荐乐器 |
|------|---------|---------|---------|
| 高饱和 (Saturated) | 强烈、鲜明、抢眼 | 饱满有力的音色 | Full orchestra, distorted guitar, powerful brass |
| 低饱和 (Desaturated) | 褪色、安静、复古 | lo-fi/muted 质感 | Lo-fi piano, brushed drums, tape-processed everything |
| 黑白 (B&W) | 经典、纯粹、戏剧 | 极简+极端对比 | Solo piano or solo cello, silence as instrument |
| 水墨 (Ink Wash) | 东方留白、写意 | 负空间为主、点到即止 | Solo erhu/guzheng/xiao, 大量留白，一两个音符 |
| 霓虹 (Neon) | 赛博朋克、夜店 | 电子脉冲、明亮合成器 | Synthwave leads, arpeggiator, drum machine 808 |
| 柔光 (Soft Focus) | 梦幻、朦胧、回忆 | 大量混响与延迟 | Mellotron, dream pop guitars, distant vocals |
| 高对比 (High Contrast) | 戏剧、冲突、张力 | 极端力度对比 pp↔ff | Orchestral dynamics, crescendo/subito piano |

---

## 二、光影 → 力度映射

| 光线条件 | 视觉感受 | 力度映射 | 音乐处理 |
|---------|---------|---------|---------|
| 明亮阳光 | 开朗、温暖、清晰 | forte (f), 开放和弦 | 高音区为主, 大调, 明亮 EQ, 开放的编曲 |
| 柔和自然光 | 舒适、日常、平和 | mezzo-forte (mf) | 中音区, 自然混响, 不刻意修饰 |
| 昏暗灯光 | 私密、忧郁、深夜 | piano (p), 弱音器 | 低音区为主, 暗色调, muted 音色 |
| 烛光/火光 | 温暖、摇曳、不稳定 | mp, 微妙的力度波动 | 温暖频率, 轻微的 tremolo/vibrato |
| 强对比 (明暗交错) | 戏剧性、冲突、张力 | pp ↔ ff 极端动态 | Chiaroscuro 式编曲: 突然的力度变化 |
| 背光/剪影 | 神秘、轮廓、未知 | p, 简洁轮廓 | Ambient drone, 简单旋律线, 大量负空间 |
| 霓虹/人工光 | 都市、科技、夜生活 | mf-f, 电子脉冲 | 合成器主导, sidechain pumping, 节奏明确 |
| 月光 | 宁静、浪漫、幽远 | pp-p, 银色质感 | Debussy 式印象派, 模糊调性, 泛音 |
| 雾中光 | 朦胧、迷失、不确定 | p, 模糊的边缘 | 大量 reverb + lo-pass filter, 模糊的音色 |
| 闪电/频闪 | 突发、惊恐、断裂 | sfz (突强), 间歇性 | 突然的打击乐 hit, 寂静中的爆发 |
| 日出/日落 | 渐变、希望/告别 | 渐强或渐弱 (crescendo/diminuendo) | 从稀疏到丰满, 或从丰满到稀疏 |
| 完全黑暗 | 恐惧、未知、空无 | ppp, 或完全静默 | 低频 drone only, 或刻意的沉默 |

---

## 三、构图 → 节奏/编曲映射

| 构图方式 | 视觉效果 | 节奏映射 | 编曲建议 |
|---------|---------|---------|---------|
| 特写 (Close-up) | 细节、亲密、情感 | 慢速 60-80 BPM | 少量乐器, 细腻表情, 近距离拾音, 能听到呼吸 |
| 中景 (Medium Shot) | 平衡、叙事、日常 | 中速 80-110 BPM | 标准编曲密度, 旋律+和声+节奏均衡 |
| 全景 (Wide Shot) | 宏观、环境、壮阔 | 中慢速 70-100 BPM | 大编制, 宽立体声场, 管弦乐/合唱, 空间感 |
| 广角/超广角 | 壮观、史诗、渺小感 | 宏大但不急促 80-100 BPM | Full orchestra + choir, 极宽 stereo, hall reverb |
| 俯拍 (Top Down) | 上帝视角、命运、格局 | 稳定节奏, 重力感 | 下行旋律, 深沉低音 pedal point, 庄严 |
| 仰拍 (Low Angle) | 崇高、威压、敬畏 | 上升感 | 上行旋律, 渐强, soaring strings/brass |
| 斜角/荷兰角 | 不安、疯狂、失衡 | 不规则节奏 | 不协和和声, odd meter (5/4, 7/8), 失谐 |
| 快切/蒙太奇 | 快节奏、紧迫、碎片 | 快速 130-180 BPM | Staccato hits, drum fills, 快速剪辑式编曲 |
| 长镜头 | 连续、沉浸、真实 | 缓慢演化, 不中断 | Legato, 无突然变化, 渐进式, 有机过渡 |
| 移动镜头 (Tracking) | 跟随、流动、旅程 | 中速, 持续推进 | Ostinato bass, 持续节奏, 前进感 |
| 摇镜头 (Pan) | 展示空间、扫描 | 稳定中速 | Panning effects, 立体声运动, 逐渐展开 |
| 推镜头 (Push In) | 聚焦、紧迫、发现 | 渐快或渐密 | Build-up, 乐器逐层加入, crescendo |
| 拉镜头 (Pull Out) | 远离、释然、全貌 | 渐慢或渐疏 | Diminuendo, 乐器逐层退出, 空间变大 |

---

## 四、情感 → 音乐参数完整映射（18 种情绪）

| 情绪 | 调式 | 速度 | 乐器倾向 | 编曲密度 | 特征技法 |
|------|------|------|---------|---------|---------|
| 温馨 | 大调 / Lydian | Andante (75-85) | Acoustic guitar, warm piano, soft strings, ukulele | 中等偏少 | Legato, 温暖 reverb, 柔和动态 |
| 紧张 | 小调 / Diminished | Allegro (120-140) | Staccato strings, timpani, synth pulse, muted brass | 中等偏密 | Ostinato, tremolo, crescendo, 不安定低频 |
| 悬疑 | Locrian / Chromatic | Adagio-Andante (60-80) | Low strings, piano (sparse), ambient drone, reversed sounds | 稀疏 | Pedal point, 长音 sustain, 大量负空间 |
| 浪漫 | 大调 / Dorian | Andante-Moderato (70-95) | Piano, cello, nylon guitar, flute, harp | 中等 | Rubato, vibrato, 渐进式旋律发展 |
| 热血 | 大调 / Mixolydian | Allegro-Vivace (130-160) | Full brass, electric guitar, taiko, full orchestra | 极密 | Unison power, tutti 全奏, 持续高能量 |
| 悲伤 | 小调 / Aeolian | Largo-Adagio (50-70) | Solo piano, solo cello, erhu, oboe | 极少 | 下行旋律, 大量留白, diminuendo |
| 幽默 | 大调 / 五声 | Allegretto-Allegro (100-130) | Bassoon, clarinet, pizzicato strings, glockenspiel | 中等 | Staccato, 意外的音程跳跃, 节奏错位 |
| 孤独 | 小调 / Dorian | Adagio (55-70) | Solo piano, solo guitar, solo flute, distant strings | 极少 | 单旋律线, 大 reverb, 回声般的空间 |
| 恐惧 | Atonal / Chromatic | 不定/极慢 | Low drone, scraped strings, reversed piano, sub bass | 稀疏但压迫 | Dissonance, 突然 sfz, col legno, 不规则节奏 |
| 愤怒 | 小调 / Phrygian | Presto (160-200) | Distorted guitar, aggressive drums, brass stabs, synth | 极密 | Fortissimo, accents, 快速连击, 持续高能 |
| 释然 | 大调 / Lydian | Moderato (85-100) | Piano (opening up), strings (warm), gentle brass, harp | 从密到疏 | 从小调解决到大调, decrescendo, 空间打开 |
| 怀旧 | 大调 + lo-fi 处理 | Andante (70-85) | Lo-fi piano, Rhodes, warm acoustic, vinyl crackle | 中等偏少 | Tape saturation, 温暖滤波, 柔焦质感 |
| 治愈 | 大调 / Pentatonic | Andante (70-85) | Acoustic guitar, gentle piano, nature sounds, soft pads | 少 | 简单和声, 重复的舒适 pattern, 自然音效 |
| 激昂 | 大调 / Minor→Major | Allegro (120-140) | Orchestra + choir, brass fanfare, timpani, snare roll | 极密→高潮 | 渐进式 build-up, 大调解决, tutti fff |
| 迷幻 | Modal / Whole Tone | 中速偏慢 (80-100) | Sitar, synth pad, processed guitar, reversed sounds | 中等（层叠） | Phaser, flanger, delay, 声音变形, 非线性结构 |
| 思念 | 小调 / sus4 解决 | Adagio-Andante (60-80) | Solo vocal melody, piano, distant strings, music box | 少 | 旋律上行但不解决, 挂留和弦, 叹息般乐句 |
| 决绝 | 小调→大调 | Moderato-Allegro (90-120) | Powerful piano, cello section, brass, snare | 中→密 | 坚定的节奏, 下行→上行旋律, 力度坚定不波动 |
| 天真 | 大调 / Pentatonic | Allegretto (100-115) | Glockenspiel, ukulele, recorder, music box, clapping | 少 | 简单旋律, 重复, 高音区, pizzicato |

---

## 五、场景 → 音乐意象完整映射（25 个场景）

### 自然场景

| 场景 | 核心音乐意象 | 推荐流派 | 关键乐器 | 节奏型 |
|------|------------|---------|---------|--------|
| 晨曦 | 光线渐明，鸟鸣初现 | Ambient → Neoclassical | Gentle piano, bird sounds, soft strings, harp | 从无节奏到轻柔脉搏, 渐强 |
| 黄昏 | 金色渐暗，温暖收束 | Lo-fi, Acoustic, Bossa Nova | Nylon guitar, warm piano, soft brass, gentle bass | 中速渐慢, 渐弱 |
| 雨夜 | 滴答节奏，孤寂温暖 | Lo-fi Hip-Hop, Ambient, Jazz | Piano + rain texture, muted trumpet, vinyl crackle | 慢速, rain pattern 作为 hi-hat |
| 山间 | 壮阔空旷，回声环绕 | Post-Rock, Celtic, Film Score | French horn, strings, pan flute, deep reverb | 缓慢展开, 大间距音符 |
| 海边 | 波浪律动，开阔自由 | Ambient, Dream Pop, Bossa Nova | Acoustic guitar, wave texture, vibraphone, airy pads | 海浪节奏 (6/8 摇摆), 周期感 |
| 森林 | 层叠绿意，神秘自然 | Celtic, Ambient, Film Score | Flute, harp, wind sounds, soft percussion, bird calls | 不规则有机节奏, 层叠 |
| 深夜 | 万籁俱寂，独处时光 | Lo-fi, Cool Jazz, Ambient | Felt piano, muted trumpet, brush drums, vinyl crackle | 极慢, 稀疏, 大量留白 |

### 人文场景

| 场景 | 核心音乐意象 | 推荐流派 | 关键乐器 | 节奏型 |
|------|------------|---------|---------|--------|
| 集市 | 嘈杂热闹，人声鼎沸 | World Music, Latin, Funk | Percussion ensemble, accordion, brass, crowd texture | 快速多层打击乐, 呼应 |
| 古建筑 | 历史厚重，时间沉淀 | Chinese Traditional, Neoclassical | Guzheng, xiao, deep bell, soft gong, sparse piano | 极慢, 单音, 大量空间 |
| 都市街头 | 快节奏，多元碰撞 | Lo-fi Hip-Hop, Indie Pop, City Pop | Synth bass, drum machine, electric piano, subtle horns | 中快速, groovy, 层叠 |
| 教室 | 青春，紧张或无聊 | Indie Pop, Lo-fi, Acoustic | Acoustic guitar, glockenspiel, piano, gentle drums | 中速, 轻快或慢悠悠 |
| 厨房 | 烟火气，温暖忙碌 | Jazz, Bossa Nova, Acoustic | Upright piano, acoustic guitar, light percussion, bass | 中速, groovy, 温暖 |
| 舞台 | 聚光灯，紧张与绽放 | Cinematic, Pop, Jazz | Spotlight solo instrument + building orchestra | 从静到爆发, spotlight moment |

### 叙事场景

| 场景 | 核心音乐意象 | 推荐流派 | 关键乐器 | 节奏型 | 情绪弧线 |
|------|------------|---------|---------|--------|---------|
| 对峙 | 紧绷弦线，一触即发 | Cinematic, Post-Rock | Staccato strings, low brass, timpani roll, synth drone | Ostinato 固定重复, 渐密 | 紧张 → 高潮前的静止 |
| 追逐 | 急促心跳，生死时速 | Drum & Bass, Trailer Music | Fast drums, pulsing synth, staccato brass, bass pulse | 160+ BPM, 持续高速 | 持续高紧张 |
| 告白 | 心跳加速，不确定 | Indie Pop, Acoustic, Dream Pop | Acoustic guitar, gentle piano, soft strings, heartbeat | 中速, 轻微加速, 心跳 | 紧张 → 期待 → 释放 |
| 离别 | 不舍牵扯，渐行渐远 | Post-Rock, Neoclassical | Piano, cello, strings (gradually thinning), distant pad | 渐慢, 渐疏, 渐弱 | 悲伤 → 接受 → 寂静 |
| 重逢 | 惊喜到释然，温暖涌上 | Film Score, Indie, Acoustic | Piano (recognition motif), swelling strings, warm brass | 从愣住(停顿)到温暖脉搏 | 惊讶 → 感动 → 温暖 |
| 战场 | 混乱暴力，恢弘悲壮 | Epic Orchestral, Trailer Music | Full orchestra, choir, taiko, brass fanfare | 快速但厚重, 多层打击 | 恐惧 → 决心 → 悲壮 |
| 实验室 | 科技感，精密冰冷 | IDM, Ambient, Techno | Arpeggiator, clean synth, glitch, precise percussion | 精确机械节奏, quantized | 冷静 → 发现 → 兴奋 |
| 回忆 | 模糊褪色，温暖遥远 | Lo-fi, Dream Pop, Ambient | Lo-fi piano, tape-warped guitar, distant melody | 比正常慢 10-15%, 模糊 | 怀旧 → 温暖 → 惆怅 |

---

## 六、五感 + 第六感 + 第七感 → 音乐映射

### 触觉 Touch
| 触觉感受 | 音乐转译 | 具体手法 |
|---------|---------|---------|
| 温暖 | 中低频丰富的音色 | Warm piano, cello, soft brass, analog synth |
| 冰冷 | 高频尖锐、数字化 | Crystal synth, high string harmonics, metallic percussion |
| 粗糙 | 失真、颗粒感 | Distorted guitar, bitcrush, rough texture |
| 光滑 | Legato, 无棱角 | Smooth strings, silky pad, portamento |
| 刺痛 | Staccato 高频打击 | Pizzicato, sharp stabs, needle-like synth |
| 柔软 | 缓慢起音 + 大 reverb | Felt piano, soft pad, distant flute |
| 沉重压迫 | 低频积压、压缩 | Sub bass, compressed drums, low drone |
| 风吹拂 | 气息感音色 | Breathy flute, airy pad, wind texture, soft white noise |

### 嗅觉 Smell
| 嗅觉感受 | 联想意象 | 音乐转译 |
|---------|---------|---------|
| 花香 | 轻盈飘散 | Harp arpeggios, celesta, flute trills, high strings |
| 烟火/厨房 | 温暖浓郁 | Acoustic guitar, warm bass, cajon, upright piano |
| 雨后泥土 | 新鲜湿润 | Piano + rain sounds, earthy bass, gentle percussion |
| 老旧/发霉 | 腐朽怀旧 | Detuned piano, tape warble, dusty vinyl crackle |
| 海风/咸味 | 开阔清新 | Open guitar chords, gentle breeze sounds, wide stereo |
| 焚香/寺庙 | 灵性庄严 | Temple bell, singing bowl, low chant drone, xiao |

### 味觉 Taste
| 味觉感受 | 联想意象 | 音乐转译 |
|---------|---------|---------|
| 甜 | 愉悦满足 | Major key, warm tone, gentle melody, celesta |
| 苦 | 厚重深沉 | Minor key, low register, sparse, dark timbre |
| 酸 | 刺激不安 | Dissonant intervals, sharp attacks, unexpected notes |
| 辣 | 刺激兴奋 | Brass stabs, fast percussion, distorted, energetic |
| 鲜 | 满足丰富 | Full arrangement, satisfying chord resolution, umami-like warmth |
| 淡 | 清新质朴 | Solo instrument, pentatonic, unprocessed, minimal |

### 听觉 (环境音 → 音乐化)
| 环境声 | 音乐化处理 |
|--------|-----------|
| 雨声 | 用 hi-hat/shaker 模拟雨点节奏, 或直接叠加雨声 texture |
| 风声 | Breathy pad, white noise sweep, wind texture sample |
| 鸟鸣 | Flute trills/ornaments, high woodwind phrases |
| 火焰噼啪 | Vinyl crackle, light percussive hits, warm tone |
| 钟声 | Bell samples, tubular bells, celesta hits on downbeat |
| 人群嘈杂 | Layered murmur texture, multi-layered rhythms |
| 心跳 | Low kick drum/sub bass 60-80 BPM pulse |
| 脚步声 | Rhythmic percussion pattern, walking bass line |
| 水流/溪流 | Harp arpeggios, flowing piano runs, water texture |
| 雷声 | Timpani roll, sub bass boom, orchestral crash |

### 第六感 — 直觉/预感 (Sixth Sense: Intuition)
| 直觉感受 | 音乐手法 | 具体描述 |
|---------|---------|---------|
| "有什么不对" | Low drone + subtle dissonance | 低频持续音上叠加微弱的不协和泛音 |
| "即将发生" | Building tension, rising pitch | 缓慢上行的音高, tremolo strings, crescendo |
| "似曾相识" | Reversed melody fragments | 将主题旋律倒放/变形，似曾相识但无法辨认 |
| "被注视" | Sparse, exposed, vulnerable | 几乎无配乐，只有环境音+单一高频泛音 |
| "命运降临" | Inevitable ostinato | 不可阻挡的重复音型，越来越强，越来越近 |
| "时间扭曲" | Tape speed variation | 音乐忽快忽慢, 如磁带被拉扯, 不稳定的 tempo |

### 第七感 — 超越/灵性 (Seventh Sense: Transcendence)
| 超越体验 | 音乐手法 | 具体描述 |
|---------|---------|---------|
| 灵魂出窍 | Overtone singing, extreme reverb | 泛音歌唱的多重音高 + 无限混响空间 |
| 时间静止 | Single sustained tone → silence | 一个音符延续至消失，然后是有意义的沉默 |
| 万物合一 | All instruments converge to unison | 所有乐器从混乱渐渐汇聚到同一个音 |
| 宇宙视角 | Cosmic pad, vast emptiness | 极宽声场的合成垫音，如漂浮在太空 |
| 生死边界 | Bell tones fading in/out of silence | 钟声在寂静中若隐若现，呼吸般的节奏 |
| 顿悟 | Sudden clarity after noise | 从复杂/混乱突然切到一个清澈的音 |
| 轮回感 | Circular melody, no beginning/end | 循环结构，旋律首尾相接，无法分辨起止 |

---

## 七、联想映射使用原则

### 1. 不是 1:1 对应，而是 N:1 综合
- 一个画面同时包含色调+光影+构图+情感，音乐 prompt 应综合所有维度
- 例: "黄昏海边特写" = 暖色(acoustic guitar) + 渐暗(diminuendo) + 特写(intimate, slow) + 海边(wave rhythm)

### 2. 冲突感来自映射矛盾
- 当画面参数彼此矛盾时，音乐也应反映这种张力
- 例: "明亮色调+悲伤情绪" = 大调旋律但带有下行走向，或明亮音色但慢速

### 3. 留白是最强的工具
- 不是每个画面都需要音乐填满
- 特写+安静的画面 → 音乐也应极度稀疏，或直接沉默
- 沉默后的第一个音符 = 画面中最亮的光

### 4. 过渡比单帧更重要
- 序话Story 是分镜叙事，关注镜头间的过渡
- 音乐的情绪弧线应跨越多帧，而非逐帧匹配
- 用 "emotion start → development → resolution" 描述音乐的时间维度

### 5. 文化映射优先于通用映射
- 序话Story 的故事多为中国文化背景
- 中国场景优先使用中国乐器映射，而非默认西方乐器
- 但可以用中西融合创造现代中国风（如 guzheng + electronic beats）

---

## 七、叙事节奏 → 音乐结构映射

**序话Story 的故事有完整的叙事弧线（Pipeline Stage 1 大纲 → Stage 3 剧本），BGM 的结构应与叙事节奏对应。**

| 叙事阶段 | 故事内容 | 音乐结构 | 音乐特征 |
|---------|---------|---------|---------|
| 铺垫/日常 | 角色介绍、场景建立 | Intro | 稀疏编曲、低能量、建立音色基调 |
| 引发/转折 | 矛盾出现、情绪转变 | Build | 加入新乐器层、和声变化、力度渐增 |
| 发展/冲突 | 矛盾加剧、情感碰撞 | Development | 编曲密度增加、节奏推进、情绪升温 |
| 高潮 | 情感最强点、决定性时刻 | Climax | 全编制 tutti、最强力度、调性解决或突变 |
| 收尾/余韵 | 情感沉淀、故事结尾 | Outro | 回到稀疏、呼应 intro、渐弱消散 |

**从序话Story JSON 数据到音乐结构**：

| 故事数据字段 | 音乐映射 |
|------------|---------|
| `1_outline.json → mood` | 整首 BGM 的基调（大调/小调、快/慢） |
| `1_outline.json → logline` | 灵魂层的核心意象来源 |
| `1_outline.json → plot_points` | 情绪曲线的转折点（铺垫→冲突→高潮→余韵） |
| `3_screenplay.json → scenes[].atmosphere` | 各段的情绪色彩 |
| `4_storyboard.json → global_visual_direction → color_grade` | 色调→音色映射的输入 |
| `4_storyboard.json → global_visual_direction → overall_lighting` | 光影→力度映射的输入 |
| `4_storyboard.json → shots[0].lighting.mood` | 开场情绪锚点 |
