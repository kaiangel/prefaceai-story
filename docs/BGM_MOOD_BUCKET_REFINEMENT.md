# BGM Mood-Bucket Refinement — 8 Mood × 6 Bucket 全维度深挖

> **任务**: B40 全维度 mood/桶映射重新设计
> **触发**: test9 (用户选"热血") Haiku 写出"坚韧悲壮"而非"激昂热血"，Founder 反馈"BGM 不是完全热血的感觉，开头有点平静悲凉，后面有点悲壮，有壮的成分，可能贴近一点热血的感觉"
> **Founder 强调**: "不光是热血风格，其他风格也都要细且尽可能贴切的 BGM"
> **作者**: AI-ML Engineer
> **日期**: 2026-05-09

---

## 一、问题诊断

### 1.1 实测产物（test9, project=a7a7763b）

用户选 "热血" → outline.user_selected_mood='热血'，visual_tone.overall_mood='heroic'，narrative_pace='fast_paced'，故事是"55 岁陈志远再战高考，30 年磨砺"。

Haiku 输出（B32 持久化产物 `bgm_prompt_chapter0.txt`，794 chars）：

```
<quotes>
那一步，他走了三十年。
他是这里最年长的考生，鬓角有几根白发，眼角有几道细纹，但此刻他的背脊是直的，眼神是定的，是整条走廊里最从容的一个人——不是因为他不怕，而是因为他早已学会，带着恐惧，继续走。
</quotes>

Driving. Cinematic. The way a body learns to move forward despite thirty years of weight pressing down on it. A steady percussive pulse underneath — not relentless, but inevitable, like footsteps that have already decided. Brass swells rising on the exhale, a climbing motif that doesn't triumph but endures. Piano notes that build, then hold their ground rather than soar.

那一步，他走了三十年。他早已学会，带着恐惧，继续走。

The sound of someone choosing themselves after decades of choosing duty. Golden light cutting through doubt. Resolution earned, not given — every step a small rebellion. No dramatic crescendo. Just the certainty of a man who has already survived the hardest part: waiting.
```

### 1.2 数据 vs 听感的悖论

| 维度 | 数据评分 | 听感评分 |
|------|---------|---------|
| Heroic 桶必备词命中（driving/cinematic/brass swells/climbing motif/percussive build/rising scale）| 6/7（缺 triumphant resolution）| - |
| 禁用词污染（heavy/sink/hollow/passive/no resolution）| 0/5 | - |
| 整体调性方向 | 4.5/5（数据上完全 Heroic 桶）| 3/5（用户感觉"坚韧悲壮"不是"激昂"）|

**核心悖论**：调性词命中率高，但 Haiku 用反向修饰把所有热血词的能量都"压"住了——

- "not relentless, but **inevitable**" — 把"驱动力"从主动转为宿命
- "doesn't triumph but **endures**" — 直接否定胜利感
- "build, then **hold their ground rather than soar**" — 把 climbing 截断在地面
- "**No dramatic crescendo**" — 显式禁用激昂高潮
- "every step a **small** rebellion" — 把英雄叙事缩成微小抵抗
- "Resolution earned, not given" — 强调代价而非凯旋

**根因**：Haiku 看到 idea 含 "55 岁 / 30 年 / 重返 / 高考"（年龄+时间跨度+第二次机会语义），自动激活了"中年坚守"叙事原型，**虽然走在 Heroic 桶里，但选了 Heroic 桶下的"坚韧型"子 vibe，而不是"激昂型"子 vibe**。

### 1.3 关键洞察

Heroic 桶其实包含至少 3 个截然不同的 sub-vibe：

| Sub-vibe | 典型场景 | 调性词 | 用户期待 vs 实际差异 |
|---------|---------|-------|------------------|
| **激昂式** | Rocky 训练蒙太奇、体育片高潮、少年冲锋 | explosive / triumphant / soaring / fanfare / breakthrough | 用户选"热血"99% 指这个 |
| **坚守式** | 中年磨剑、30 年磨砺、扛住坠落 | enduring / inevitable / hold ground / not triumph | LLM 看"年龄+时间"自动选这个 |
| **悲壮式** | 明知不可为而为之、背水一战、孤勇者 | fierce dignity / accepting cost / charging into loss | 第三种独立 vibe |

**所以 B11 的"6 桶映射" 在桶选择层面是对的**（Haiku 选了 Heroic 桶），**问题在桶内的 sub-vibe 选择**——这是 6 桶系统本身的盲区。

### 1.4 这个问题不只 Heroic 桶有

| Mood | 用户期望（默认）| LLM 可能选错的 sub-vibe | 实例 |
|------|--------------|-------------------|------|
| 温馨 | 家庭温情 / 朋友闲聊 | 怀旧伤逝（年纪大了想起妈妈）| 故事含老人/已故亲人时 |
| 紧张 | 危机四伏 / 心跳加速 | 沉重压抑（窒息式）| 故事含家暴/职场霸凌时 |
| 幽默 | 段子反转 / 轻快搞笑 | 黑色幽默（苦中作乐）| 故事含失败/挫折时 |
| 感人 | 真情流露 / 泪点动人 | 哀伤悲怆（亲人离世）| 故事含死亡/告别时 |
| 治愈 | 温暖抚慰 / 释放压力 | 寂寞独处（一个人的修行）| 故事含独居/隐居时 |
| 热血 | 激昂高燃 / 血脉偾张 | 坚守坚韧 / 悲壮孤勇 | 故事含中年/长跨度/挫败时 |
| 悬疑 | 紧张未知 / 解谜推理 | 阴森恐怖 / 心理诡异 | 故事含死亡/超自然时 |
| 浪漫 | 心动悸动 / 长情陪伴 | 哀伤别离 / 错过遗憾 | 故事含分手/异地时 |

**结论**：每个 mood 都有 2-3 个 sub-vibe，**用户选的 mood 通常默认指"激昂/明亮/正面"那个 sub-vibe**，但 Haiku 看故事内容会被诱导选错。

---

## 二、8 Mood × Sub-Vibe 全维度分析

### 2.1 完整 sub-vibe 映射表

| 用户选 (前端) | 桶 (英文映射) | 默认期望 sub-vibe | 次要 sub-vibe | LLM 误选风险 sub-vibe | 风险触发条件 |
|--------------|--------------|----------------|-------------|----------------|-----------|
| **温馨** | warm | 家庭温情 / 朋友闲聊 / 情侣甜蜜 | 怀旧温暖（不带伤逝） | 怀旧伤逝（"再也回不去了"）| 故事含已故亲人/旧物/老照片 |
| **治愈** | heartwarming | 温暖抚慰 / 释放疲惫 / 重获力量 | 自然平和（独处疗愈）| 寂寞独处（孤独感）| 故事含独居/分手后/失业后 |
| **紧张** | tense | 危机感 / 心跳加速 / 倒计时 | 心理博弈 / 暗流涌动 | 沉重压抑（窒息式）| 故事含家暴/职场霸凌/无力反抗 |
| **幽默** | comedic | 段子反转 / 轻快搞笑 / 荒诞落位 | 温情喜剧（带温度的笑）| 黑色幽默（自嘲式苦中作乐）| 故事含失败/挫折/职业危机 |
| **感人** | melancholic | 真情流露 / 泪点动人 / 释怀 | 默默坚守（无声付出）| 哀伤悲怆（葬礼式）| 故事含死亡/重大告别 |
| **热血** | heroic | **激昂高燃 / 突破爆发 / 巅峰对决** | 励志奋进（坚定向前）| **坚守坚韧 / 悲壮孤勇** | **故事含中年 / 30 年磨砺 / 长跨度** |
| **悬疑** | mysterious | 紧张未知 / 解谜推理 / 暗中观察 | 神秘探秘（好奇驱动）| 阴森恐怖（jumpscare 式）| 故事含死亡/超自然/精神病 |
| **浪漫** | romantic | 心动悸动 / 暧昧怦然 / 长情陪伴 | 缱绻不舍（含蓄长情）| 哀伤别离（错过遗憾）| 故事含分手/异地/告别 |

### 2.2 每个 mood 的 sub-vibe 调性词谱（用于 Haiku 约束）

#### 温馨 (warm)

**默认期望（家庭温情）**:
- ✅ 必备: warm / unhurried / fingerpicked / gentle / soft pad / morning mist / cozy / familial
- ❌ 禁用: heavy / suffocating / mournful / grief / longing for the lost / nostalgic_aching

**次要（怀旧温暖，不带伤逝）**:
- ✅ 允许: nostalgic / sepia / memory-tinted / amber light
- ❌ 仍禁用: bittersweet for the gone / mournful

**LLM 误选风险（怀旧伤逝）**:
- ⚠️ 警示: 即使故事含老人/旧物，**音乐不能让"逝去感"压过"温暖现存"**

#### 治愈 (heartwarming)

**默认期望（温暖抚慰，主动给力量）**:
- ✅ 必备: gentle / restorative / breath returning / unclenching / soft uplift / warm sunlight / supportive cushion
- ❌ 禁用: sparse / desolate / lonely / breath held / wounded

**次要（自然平和，独处疗愈）**:
- ✅ 允许: spacious / unhurried walking / breeze / morning bird
- ❌ 仍禁用: lonely / isolated / yearning for connection

**LLM 误选风险（寂寞独处）**:
- ⚠️ 故事含独居/分手后时，**音乐必须给"被陪伴感"，不能给"一个人的孤单"**

#### 紧张 (tense)

**默认期望（外部危机，心跳加速）**:
- ✅ 必备: heartbeat-like pulse / mounting tension / approaching deadline / cliffhanger / kinetic dread
- ❌ 禁用: suffocating / breath held / no resolution / hopeless / inevitable doom

**次要（心理博弈）**:
- ✅ 允许: cat-and-mouse / silent calculation / hidden tension
- ❌ 仍禁用: passive collapse / despair

**LLM 误选风险（沉重压抑/窒息）**:
- ⚠️ 故事含无力反抗时，**音乐要"危机感+反击姿态"，不能写成"被压垮的窒息"**
- ⚠️ 这是当前最危险的 sub-vibe slip：紧张→窒息（年夜饭好例 1 形状渗透）

#### 幽默 (comedic)

**默认期望（明快段子）**:
- ✅ 必备: bouncy / syncopated / snare clap on punchline / brass stab / lift / drop / no melodrama
- ❌ 禁用: heavy / sink / mournful / breath held / suffocating

**次要（温情喜剧）**:
- ✅ 允许: warm chuckle / fond mockery / lighthearted teasing
- ❌ 仍禁用: bitter laughter / self-mocking despair

**LLM 误选风险（黑色幽默/苦中作乐）**:
- ⚠️ 故事含失败/挫折时，**音乐不能写成"含泪的笑"，必须保住"段子节奏"**
- ⚠️ 这是 test7 修过的问题（"喜剧外壳+窒息底色" → 已修正）

#### 感人 (melancholic / 真情)

**⚠️ 桶名注意**: melancholic 在 6 桶系统里映射 "感人"，但语义上 melancholic 偏"哀伤"，"感人"偏"真情"。这是命名层面的 mismatch。

**默认期望（真情流露，泪点动人）**:
- ✅ 必备: heartfelt / tears welling / restrained sob / a body finally allowed to feel / warm release
- ❌ 禁用: detached / cold / mocking / triumphant

**次要（默默坚守）**:
- ✅ 允许: quiet dedication / wordless devotion / pen-on-paper steadiness
- ❌ 仍禁用: triumphant / fanfare

**LLM 误选风险（哀伤悲怆/葬礼式）**:
- ⚠️ 故事含死亡时，**音乐要"温暖的真情释怀"，不是"无尽悲怆"**
- ⚠️ 当前 melancholic 桶必备词 "slow / heavy / suffocating / notes that sink" **过于偏向哀伤一侧**，需要拆"感人型 melancholic" vs "压抑型 melancholic"

#### 热血 (heroic) — 本次问题核心

**默认期望（激昂高燃）**:
- ✅ 必备: **explosive / triumphant / soaring / breakthrough fanfare / climactic crescendo / surge / burst** (NEW)
- ❌ 禁用: enduring / inevitable / hold ground / not triumph / small rebellion / no crescendo (NEW)

**次要（励志奋进）**:
- ✅ 允许: driving / climbing motif / percussive build / cinematic（**当前 Heroic 桶必备词** — 现在重新定位为"次要"）
- ❌ 仍禁用: hollow / passive / no resolution

**LLM 误选风险（坚守坚韧/悲壮孤勇）**:
- ⚠️ 故事含中年/长跨度时，**音乐必须保留"激昂爆发"的形状，不能写成"沉默的坚持"**
- ⚠️ **核心修复点**: 在 Haiku prompt 加显式"反 endurance 偏置"约束（当前 prompt 没说"不要写成坚守式"）

#### 悬疑 (mysterious)

**默认期望（紧张未知/解谜）**:
- ✅ 必备: minor key / sparse percussion / ambient drone / cryptic phrase / question hanging
- ❌ 禁用: warm / unhurried / cheerful / triumphant

**次要（神秘探秘）**:
- ✅ 允许: curious / shadowy fascination / almost-glimpse / receding clue
- ❌ 仍禁用: full resolution / clear answer

**LLM 误选风险（阴森恐怖）**:
- ⚠️ 故事含超自然时，**音乐不能写成 jumpscare 恐怖片，必须保住"探秘感"**
- ⚠️ 必须避免: shrieking strings / horror stab / dissonant scream

#### 浪漫 (romantic)

**默认期望（心动悸动）**:
- ✅ 必备: butterflies / fingertip electricity / first-glance pause / breath catching / soaring tender melody
- ❌ 禁用: bouncy / heavy / sparse / mocking / mournful

**次要（缱绻长情）**:
- ✅ 允许: yearning / strings that breathe / tide-like / piano motif almost resolving
- ❌ 仍禁用: detached / cynical

**LLM 误选风险（哀伤别离/错过）**:
- ⚠️ 故事含分手/异地时，**音乐要"暧昧悸动"或"长情陪伴"，不能写成"分手式哀伤"**
- ⚠️ Note: 好例 5 暗夜浪漫现在偏"长情告别"sub-vibe，没覆盖到"心动暧昧"sub-vibe — 未来可补好例 7

---

## 三、修复方案 A/B/C/D 评估

### 方案 A: 桶细分（每 mood 拆 2-3 sub-bucket）

**操作**: Heroic 桶拆成 `heroic_uplifting` / `heroic_resolute` / `heroic_tragic`，每个 mood 同样拆。

**优点**:
- 语义粒度最细
- meta-prompt 可以为每 sub-bucket 给一个好例

**缺点**:
- 6 桶 × 3 sub = 18 桶，meta-prompt 体量爆炸（487 行 → 估计 1200+ 行）
- Mureka 不感知"sub-bucket"，最终都通过 prompt 调性词控制，sub-bucket 只是 Haiku 内部分类
- 用户 Stage A 选项不变（仍然 8 个），所以 sub-bucket 必须 LLM 自己判断 — 反而增加 LLM 负担
- 上下文窗口压力（Haiku 4.5 max 200k 但 prompt cache 失效会贵 5x）

**评估**: ❌ 不推荐 — 复杂度对收益不成比例

---

### 方案 B: Haiku prompt 加 8 mood 显式 sub-vibe 约束 ✅ 推荐

**操作**: 不改桶结构，在 meta-prompt 的 Step 0（"先按 overall_mood 判断 6 桶哪一桶"）下加一段 **"sub-vibe 倾向锁定"** 约束块，对 8 个 mood 各给 1 段：

```
当 overall_mood = "热血" 时：
  ⚠️ DEFAULT TO 激昂式 sub-vibe (uplifting/explosive/triumphant)
  即使故事内容含中年/长跨度/挫败元素，仍必须给"激昂高燃"的形状
  PREFER: explosive / soaring / breakthrough fanfare / climactic crescendo
  AVOID: enduring / inevitable / "doesn't triumph but endures" / "no crescendo"
  原因: 用户选"热血"几乎从不指"坚守式坚韧"，那是 LLM 看到年龄+时间跨度的自动联想偏置

当 overall_mood = "紧张" 时：
  ⚠️ DEFAULT TO 危机感 sub-vibe (heartbeat / mounting / kinetic dread)
  即使故事内容含无力反抗，仍必须给"紧张+反击姿态"
  PREFER: heartbeat-like pulse / mounting tension / approaching deadline
  AVOID: suffocating / breath held / hopeless（这些是"沉重"侧不是"紧张"侧）

(以此类推 8 个 mood)
```

**优点**:
- ✅ **直接命中根因**：用户期望和 LLM 自动倾向之间的差距
- ✅ 不破坏现有 6 桶框架（B11/B19 投入保留）
- ✅ 实现成本低（meta-prompt 加 ~80 行）
- ✅ Haiku prompt cache 命中率不变（system prompt 仍稳定）
- ✅ 可单独审视每个 mood 的"用户期望 vs 故事内容"冲突
- ✅ 对 Haiku 的认知负担小（8 个清晰指令 vs 18 个 sub-bucket 判断）

**缺点**:
- 需要为 8 个 mood 各写清晰的 sub-vibe 约束
- 有过度约束风险（例如温馨故事确实是"怀旧伤逝"主调，强制给"温情"会失真）— 通过留 escape hatch 缓解（"如果故事 90%+ 内容明确指向次要 sub-vibe，可使用次要"）

**评估**: ✅ **强烈推荐** — 投入产出比最高

---

### 方案 C: Stage A 加副选项（用户细分激昂/内敛）

**操作**: 用户选"热血"后，再问"你想要：A. 激昂高燃 B. 励志奋进 C. 悲壮坚守"。

**优点**:
- 让用户主动表达
- 完全消除 LLM 误猜

**缺点**:
- ❌ Stage A UI 复杂度爆炸（每个 mood 都要副选项 = 8 × 3 = 24 个新选项）
- ❌ 违反 Stage A 设计原则（默认全部"系统推荐"用户不点就走）
- ❌ 用户不一定理解 sub-vibe 区别
- 需要 Frontend + Backend + DB 改动

**评估**: ⏸️ **不推荐当前阶段** — 未来可作为 advanced 设置

---

### 方案 D: 故事画像驱动（关键词检测）

**操作**: pipeline 里加一个 `story_keyword_classifier`，检测年龄/职业/时间跨度/主题词等，传给 Haiku 暗示倾向。

**优点**:
- 数据驱动，可量化

**缺点**:
- ❌ 又一层规则系统，维护成本高
- ❌ 关键词检测必然有 false positive（"30 年"不一定意味"坚守"）
- ❌ 比方案 B 更间接，效果未必更好
- ❌ 跟 LLM 在做的判断重复了（Haiku 已经看 idea 了）

**评估**: ❌ 不推荐 — 反而把简单问题复杂化

---

## 四、推荐方案 + 实施

### 4.1 推荐: **方案 B**（Haiku prompt 加 8 mood sub-vibe 约束）

**实施位置**: `test_output/manualtest/sq_upgrade_ab_test/20260304_113630/meta_prompts/meta_mixed_v3_quote_picking.md`

**实施位置 2**: 同时把约束精简版注入到 USER PROMPT 顶部（Step 0 之后），让 Haiku 在每次请求时都看到（不只在 system prompt cache 里）。

### 4.2 具体改动 (3 处)

**改动 #1**: 在 SYSTEM PROMPT 的 "调性 → 6 桶强制映射" 表后插入 **"sub-vibe 倾向锁定（Sub-Vibe Default Lock）"** 段落

**改动 #2**: 在每个好例后追加 **"sub-vibe 警示框"**，明确该桶下的"用户默认期望"vs"LLM 自动倾向偏置"

**改动 #3**: USER PROMPT 的 Step 0 之后插入精简版 sub-vibe 约束（每 mood 1 行 prefer/avoid 调性词）

### 4.3 不破坏现有逻辑

| 现有逻辑 | 是否保留 |
|--------|--------|
| B11 6 桶框架 | ✅ 完全保留 |
| B33 user_selected_mood priority chain | ✅ 完全保留（meta-prompt 不动业务代码） |
| B32 Haiku prompt 持久化 | ✅ 完全保留（写文件路径不变） |
| B19 8 mood enum + 中英 mood_map | ✅ 完全保留 |
| 好例 1-6 | ✅ 完全保留（只在好例后追加 sub-vibe 警示，不改示例本体） |

---

## 五、实施后 mock 验证（8 mood）

> **执行模式**: mock 验证 — 构造每个 mood 的典型 idea，跑 Haiku 4.5 (新 meta-prompt) 看输出调性词是否符合"默认期望 sub-vibe"，禁用词是否进入。
>
> **不真调 Mureka**（节省成本，调性词命中即可证明 prompt 工程层修复有效，是否听感100%贴切由 Founder 试听 1-2 个核心 mood 决定）

### 5.1 验证矩阵设计

| Mood | Mock idea | LLM 易误选风险 | 期望调性词命中 | 期望禁用词 0/N |
|------|-----------|--------------|------------|--------------|
| 温馨 | "30 年后回到老家，妈妈做的红烧肉还是那个味道" | 怀旧伤逝（妈妈年纪大）| warm/unhurried/cozy/familial | mournful/longing for the lost |
| 治愈 | "失业半年的程序员搬到大理民宿，慢慢找回写代码的快乐" | 寂寞独处 | restorative/breath returning/supportive | lonely/isolated |
| 紧张 | "实习生发现财务造假，3 天后股东大会，不能退" | 沉重压抑 | heartbeat/mounting/kinetic dread | suffocating/hopeless |
| 幽默 | "我妈把家庭群天气预报当真，一个人扛伞出门 6 次" | 黑色幽默 | bouncy/snare clap/lift drop | bitter/self-mocking despair |
| 感人 | "外公教会我修自行车那年我 12 岁，今年我 40，第一次给我儿子修" | 哀伤悲怆 | heartfelt/restrained sob/warm release | grief funeral / hopeless |
| **热血** | **"55 岁陈志远再战高考，30 年磨砺重返考场"**（test9 真案例）| **坚守坚韧（test9 实测的错）** | **explosive/triumphant/soaring/breakthrough** | **enduring/inevitable/no crescendo** |
| 悬疑 | "新搬的公寓晚上听到天花板有规律的滴答声" | 阴森恐怖 | minor key/drone/cryptic | shrieking/horror stab |
| 浪漫 | "异地恋第三年，第一次在他们家跨年，倒数 3 秒他给我戴上围巾" | 哀伤别离 | butterflies/tender soaring/breath catching | mocking/cynical |

### 5.2 验证结果（待真跑 Haiku 后填入）

> **执行说明**: 由于本任务边界限制（不重启 backend / 不动 Mureka 调用），mock 验证将通过**构造直接调用 Haiku API 的脚本**完成。验证产物存于 `test_output/manualtest/b40_mood_subvibe_verification/`。
>
> 真跑环境需求：ANTHROPIC_API_KEY，约 8 次 Haiku 调用，单价 ~$0.001 = 总计 $0.01 测试成本。

| Mood | 调性词命中 | 禁用词污染 | sub-vibe 命中 | 评分 |
|------|----------|----------|------------|------|
| 温馨 | TBD | TBD | TBD | TBD |
| 治愈 | TBD | TBD | TBD | TBD |
| 紧张 | TBD | TBD | TBD | TBD |
| 幽默 | TBD | TBD | TBD | TBD |
| 感人 | TBD | TBD | TBD | TBD |
| 热血 | TBD | TBD | TBD | TBD |
| 悬疑 | TBD | TBD | TBD | TBD |
| 浪漫 | TBD | TBD | TBD | TBD |

> **注**: TBD 待 PM/Tester 真跑验证脚本后填入。AI-ML 本次任务交付 prompt 工程层修复 + mock 测试脚本（runnable）。

---

## 六、风险与回滚

### 6.1 风险

| 风险 | 概率 | 影响 | 缓解 |
|-----|-----|-----|-----|
| 过度约束让 Haiku 输出僵化 | 中 | 中 | 留 escape hatch（"如果故事 90%+ 内容明确指向次要 sub-vibe，可使用次要"） |
| 喜剧/温馨故事误吃热血约束 | 低 | 低 | 约束按 user_selected_mood 分发，每 mood 只看自己那段 |
| meta-prompt 体量增加影响 Haiku cache | 低 | 低 | system prompt 仍稳定（cache_control 不变），增加 ~80 行 ~3KB 不破坏 cache |
| Founder 听感仍不满意 | 中 | 中 | 真跑 Haiku → Mureka 1-2 个核心 mood 让 Founder 试听 v4，若仍不行回到方案 A 桶细分 |

### 6.2 回滚方案

```bash
cp test_output/manualtest/sq_upgrade_ab_test/20260304_113630/meta_prompts/meta_mixed_v3_quote_picking.md.bak-20260509-b40-pre \
   test_output/manualtest/sq_upgrade_ab_test/20260304_113630/meta_prompts/meta_mixed_v3_quote_picking.md
```

---

## 七、Future Work（不在 B40 范围内）

1. **方案 A 升级**（如方案 B 仍不够）: 桶系统重构成 8 桶（每 mood 一桶），sub-vibe 通过桶内 default + escape hatch 处理
2. **方案 C 探索**（如用户主动反馈想细分）: Stage A 加 advanced toggle "细化情绪"
3. **好例 7-8** 补充: 给 Heroic 桶加"激昂式好例"（Rocky 训练蒙太奇形状）和 Romantic 桶加"心动悸动好例"（覆盖当前缺失 sub-vibe）
4. **故事关键词分析层**（如 sub-vibe 仍误选频繁）: 在 Stage A 后加一个 LLM 关键词分析，提示 Haiku "故事含 X 元素，注意 Y sub-vibe slip 风险"
5. **听感盲测**（在产品 GA 前）: 真跑 8 mood × Mureka 让 5+ 用户盲听打分，用真实数据验证 prompt 工程层有效

---

## 附录: 关键引用

- B11 6 桶通用化: `meta_mixed_v3_quote_picking.md` (487 行)
- B33 user_selected_mood priority chain: `app/services/story_music_extractor.py` L106-114
- B32 Haiku prompt 持久化: `app/services/music_generation_service.py` L513-541
- test9 实测产物: `output/a7a7763b-1737-4ced-bff6-515a485a2ada/bgm_prompt_chapter0.txt`
- B19 8 mood enum: `app/services/story_outline_generator.py` L153-163
