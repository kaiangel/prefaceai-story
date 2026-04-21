# 音乐 Prompt 创作者专用——故事输入格式

> 从 `1_outline.json` 和 `3_screenplay.json` 中提取"写音乐 prompt 真正需要的信息"，
> 组织成人类可读的"故事音乐简报"。
>
> 这份格式定义来自实际写过 6 首音乐 prompt 的工作流复盘：
> **什么是看了但没用的？什么是没看到但其实很有用的？**

---

## 为什么需要这个格式

原始 JSON 的问题：
- `beat_id`、`location_id`、`characters_in_scene`、`duration_hint` — 对音乐创作**零价值**
- `character_type`、`physical`、`clothing` — 写图像 prompt 才用得上，音乐不需要
- 真正有用的 `sound_design_hint`、`narration_tone`、`narration_pace`、旁白全文 — 被埋在深层嵌套里

一份好的音乐 prompt 需要的信息维度：
1. **情感弧线**（全局走向，从 outline 的 emotional_arc）
2. **视觉/音色基调**（从 visual_tone 的 overall_mood + lighting + color）
3. **关键戏剧节点**（从 plot_points 的描述，提炼出音乐上要"做事"的时刻）
4. **声音设计提示**（从 scene.atmosphere.sound_design_hint，这是最直接的线索）
5. **旁白节奏**（narration_pace，决定音乐的呼吸感）
6. **叙事语调**（narration_tone，决定情绪密度）
7. **旁白金句**（从 narration 全文中摘取最有画面感的 1-2 句，用于灵魂层意象）
8. **场景氛围**（atmosphere.mood + temperature_feel，补充声音的物理感）

---

## 字段提取规范

### 来源：1_outline.json

| 字段路径 | 提取内容 | 必须/可选 | 用于哪一层 |
|---------|---------|---------|---------|
| `title` | 故事标题 | **必须** | 识别故事 |
| `emotional_arc` | opening/midpoint/climax/resolution 四段情感标签 | **必须** | [呼吸] 情绪弧线的骨架 |
| `narrative_pace` | 叙事节奏（steady/urgent/slow 等） | **必须** | [骨架] 节奏感的整体方向 |
| `visual_tone.overall_mood` | 整体视觉情绪 | **必须** | [场域] 基调定锚 |
| `visual_tone.lighting_style` | 灯光风格（chiaroscuro/high-key 等） | **必须** | [肌肉] 音色质感参考 |
| `visual_tone.color_palette` | 色彩基调描述 | **必须** | [灵魂] 跨感官映射 |
| `plot_points[].description` | 每个情节点的描述 | **必须** | [呼吸] 提炼关键转折时刻 |
| `plot_points[].beat` | 情节类型标签 | **可选** | 辅助判断音乐重心 |
| `unique_locations[].atmosphere` | 场景氛围描述 | **可选** | [肌肉] 环境音质感参考 |
| `logline` | 一句话故事摘要 | **可选** | 快速理解故事 |

**不提取（无用字段）**：
- `location_id`、`display_name`、`location_type`、`time_of_day`、`weather`
- `key_visual_elements`
- `characters_overview` 的 `archetype`、`emotional_journey`
- `target_metrics`（shot 数量、时长控制）

### 来源：3_screenplay.json

| 字段路径 | 提取内容 | 必须/可选 | 用于哪一层 |
|---------|---------|---------|---------|
| `scene.atmosphere.sound_design_hint` | 音效/声音设计提示 | **必须** | [肌肉] 可直接翻译为乐器/质感词 |
| `scene.narration_tone` | 旁白的情绪语调 | **必须** | [呼吸] 情绪密度校准 |
| `scene.narration_pace` | 旁白节奏描述 | **必须** | [骨架] 节拍感和速度变化 |
| `scene.narration` | 旁白全文 | **必须** | [灵魂] 摘取最有画面感的句子 |
| `scene.atmosphere.mood` | 场景情绪关键词 | **必须** | [呼吸] 每段情绪描述 |
| `scene.atmosphere.temperature_feel` | 温度感/物理氛围 | **可选** | [肌肉] 音色质感的物理锚点 |
| `scene.lighting_condition` | 灯光描述 | **可选** | [肌肉] 明暗→和声密度 |
| `scene.action_beats[].emotional_note` | 动作节拍的情绪注释 | **可选** | 辅助定位戏剧高点 |

**不提取（无用字段）**：
- `beat_id`、`duration_hint`
- `characters_in_scene`、`scene_heading`、`location_id`
- `dialogue_beats`（对话台词）
- `action_beats[].action`（动作描述）

---

## 完整示例：年夜饭上的战争 — 故事音乐简报

### 基本信息

- **故事标题**: 年夜饭上的战争
- **叙事节奏**: steady（稳定前进，张力在内部积压）
- **整体基调**: warm_nostalgic_yet_tense（温暖怀旧 + 暗藏紧张）

---

### 全局情感弧线（必须）

| 阶段 | 情感标签 | 音乐含义 |
|------|---------|---------|
| Opening | warm_surface_tension | 大调，有节庆感，但和弦有内在不稳定性 |
| Midpoint | growing_confrontation | 向小调偏移，节奏收紧，音色变硬 |
| Climax | emotional_eruption_and_revelation | 先爆发→戏剧性静默→突然出现单纯旋律 |
| Resolution | bittersweet_understanding | 温柔收尾，不强行圆满，留白 |

---

### 视觉/音色基调（必须）

- **灯光风格**: chiaroscuro（明暗对比强烈）
  - 音乐解读：和声需同时有明朗和阴郁两种质感
- **色彩基调**:
  - 深红朱砂 + 暖琥珀金 → 弦乐温暖、钢琴圆润
  - 冷青蓝（游戏屏幕）→ 高音区单纯旋律，钢琴清冽

---

### 关键戏剧节点（必须）

| # | 情节 | 音乐事件 |
|---|------|---------|
| 1 | 举杯共饮，暗流涌动 | 大调年节感，一丝不安底声 |
| 2 | 说出辞职，筷子顿桌 | 一声重击，紧张感骤起 |
| 3 | 双重施压，望向窗外 | 音乐退潮，单音线条，空白感 |
| 4 | "不务正业"，茶杯打翻，烟花炸开 | 爆发→硬切静默 |
| 5 | 手机屏幕，像素老人，游戏BGM | 全部退场，只留 pentatonic piano |
| 6 | 父亲夹菜，无言收回 | 温柔弦乐+钢琴，不解决，留白 |

---

### 场景音效线索（必须）

| 场景 | sound_design_hint | 音乐转化 |
|------|---------|---------|
| Scene 2 | 筷子顿桌的重击，呼吸声渐重 | 打击乐 hit（木块或 rim-shot） |
| Scene 3 | 安静得只剩筷子碰瓷，酒杯低频嗡声 | 低频 cello drone |
| Scene 4 | 椅脚刮地板，茶杯碎裂，烟花炸响后寂静 | 大幅音量起伏，硬切 silence |
| Scene 5 | 手机里细小的像素游戏BGM，呼吸声清晰 | 极轻 pentatonic motif |
| Scene 6 | 烟花由密转疏，最后归于寂静 | 逐渐稀疏消散 |

---

### 旁白节奏与语调（必须）

| 场景 | narration_tone | narration_pace |
|------|---------|---------|
| Scene 2 | 压抑、孤立、喘不过气 | 缓慢积压→筷子顿桌后骤然加速→沉入静默 |
| Scene 3 | 压抑、疏离、内敛悲凉 | 跟随争吵加速→望向窗外时骤然减速 |
| Scene 4 | 爆裂后的沉寂 | 急促→椅子声后骤然停顿→烟花处短暂加速 |
| Scene 5 | 哽咽而温柔 | 徐缓，每个细节蓄满重量 |
| Scene 6 | 克制的温情 | 极缓，余韵悠长 |

音乐含义：整体节奏模式是"积压→爆发→骤停→温柔展开"——断裂式，不是线性渐变。

---

### 旁白金句（用于灵魂层意象，必须）

- "父亲的筷子落在桌面那一声，比窗外任何一声爆竹都响。"
- "窗玻璃是黑的，只有他自己的脸悬在那片黑暗里——冷青色的，和身后红灯笼的暖光不属于同一个世界。"
- "手机屏幕是这张桌子上唯一不说谎的东西。"
- "那串念珠在指间转过一颗又一颗，像某种古老的计时器，滴答，滴答。"

---

### 场景物理氛围（可选）

| 场景 | temperature_feel | 音色含义 |
|------|---------|---------|
| Scene 2 | 餐桌上的热气令人窒息，暖意中藏着压迫 | 音色饱和，密度高 |
| Scene 3 | 暖气太足，像被人捂住了口鼻 | 温暖乐器但和声不稳定 |
| Scene 4 | 闷热，像一个密封的压力锅 | 能量积压，需要爆破点 |
| Scene 6 | 温度交界处，像一个未说完的句子 | 温暖但不圆满 |

---

## 字段选择依据（工作流复盘）

### 实际用到了什么

1. **`emotional_arc`** — 直接构成 [呼吸] 层的四段结构
2. **`visual_tone.color_palette`** — 暖红 vs 冷青 直接映射到乐器选择
3. **`sound_design_hint`** — "筷子顿桌""像素BGM""烟花炸响后静默" 几乎直接搬进 [肌肉] 层
4. **`narration` 全文** — 最有画面感的句子成了 [灵魂] 层的中文意象
5. **`narration_pace`** — "骤然加速"、"骤然减速" 直接告诉音乐节奏要断裂

### 看了但没用的

- `dialogue_beats` 台词 — 对话具体词汇不影响音乐
- `action_beats[].action` — 旁白已更精炼地描述同一动作
- `duration_hint` — Mureka 无法通过 prompt 控制时长
- `lighting_condition` 详细描述 — 只用 outline 层的简短标签就够

### 没看到但其实很有用的

- **`atmosphere.temperature_feel`** — 很好的音色质感锚点，"像密封的压力锅"比"tense"更能引导乐器选择
- **`narration_tone` + `narration_pace` 组合** — 要一起看才能理解"是渐变还是断裂"

---

## 快速提取流程

```
Step 1: 读 outline.json
  → 复制 emotional_arc 四段
  → 复制 visual_tone（mood + lighting + color）
  → 浏览 plot_points，标注 3-4 个关键转折节点

Step 2: 读 screenplay.json（按 scene_id 顺序）
  → 每个 scene 复制 atmosphere.sound_design_hint
  → 复制 narration_tone + narration_pace
  → 阅读 narration 全文，手工摘取 1-2 个金句

Step 3: 整理成"故事音乐简报"格式

Step 4: 基于简报写 BGM Prompt（5层结构）
```
