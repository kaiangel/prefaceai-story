# 书籍解说 Prompt 编写任务

> **From**: @Backend
> **To**: @AI-ML
> **Priority**: P1
> **Type**: Side Test (实验性，不影响主线)

---

## 任务概述

为"书籍解说视频"场景设计3个新的Prompt模板。

**一句话需求**：用《人类简史》做测试，验证序话Story能不能用来生成书籍解说视频（抖音/B站常见的"3分钟讲完一本书"形态）。

**核心原则**：不动现有短剧代码/Prompt/流程，只新建文件。

---

## 你需要产出的文件

在 `app/prompts/book/` 目录下（已创建）：

| 文件 | 用途 | 对应短剧的Stage |
|------|------|----------------|
| `book_outline_prompt.py` | 书籍要点提炼 | Stage 1 (StoryOutlineGenerator) |
| `book_narration_prompt.py` | 解说脚本生成 | Stage 3 (ScreenplayWriter) |
| `book_storyboard_prompt.py` | 配图分镜 | Stage 4 (StoryboardDirector) |

---

## 各Prompt的设计要点

### 1. book_outline_prompt.py - 书籍要点提炼

**输入**：
```python
{
    "book_title": "人类简史",
    "author": "尤瓦尔·赫拉利",
    "book_summary": "用户提供的书籍内容摘要...",
    "target_duration": 180,  # 目标视频时长（秒）
    "num_insights": 5,       # 提炼几个核心洞见
    "style": "illustration"  # 视觉风格
}
```

**输出JSON结构**：
```json
{
  "book_title": "人类简史",
  "book_title_en": "Sapiens: A Brief History of Humankind",
  "author": "尤瓦尔·赫拉利",
  "core_theme": "人类如何从无名小卒成为地球主宰",
  "key_insights": [
    {
      "insight_id": 1,
      "title": "认知革命",
      "title_en": "Cognitive Revolution",
      "summary": "7万年前，智人突然开始创造虚构故事...",
      "visual_concept": "ENGLISH: A group of primitive humans sitting around a campfire at night, smoke rising into the starry sky, forming shapes of mythical creatures and spirits",
      "emotional_arc": "surprising",
      "duration_hint": 35
    }
  ],
  "opening_hook_idea": "如果有人告诉你，小麦才是地球上最成功的物种，你会相信吗？",
  "closing_message_idea": "我们统治世界，不是因为我们最强壮，而是因为我们最会讲故事。"
}
```

**关键设计点**：
- `visual_concept` **必须是英文**（用于图像生成）
- `visual_concept` **必须是具体场景**，不能是文字/图表/抽象概念
- `duration_hint` 加起来约等于 `target_duration`
- 保持原书核心观点，不过度简化

**visual_concept 示例（好 vs 坏）**：

| 好的（具体场景） | 坏的（太抽象） |
|-----------------|---------------|
| "A farmer bent over in exhaustion tending wheat fields, while a carefree hunter-gatherer walks freely through a forest in the background" | "Text showing 'Agricultural Revolution'" |
| "A medieval merchant at a crowded bazaar, gold coins floating magically between diverse traders" | "A chart comparing GDP" |
| "A scientist looking through a microscope with a giant question mark floating above" | "Abstract representation of knowledge" |

---

### 2. book_narration_prompt.py - 解说脚本生成

**输入**：Stage 1的输出（book_outline）

**输出JSON结构**：
```json
{
  "narration_segments": [
    {
      "segment_id": 1,
      "insight_ref": 1,
      "narration_text": "七万年前的某一天，一个智人对他的同伴说了一句话，改变了整个人类的命运。他说的不是"小心老虎"，而是"我们部落的守护神会保佑我们"。这是人类第一次讲述虚构的故事...",
      "duration_hint": 35,
      "visual_direction": "ENGLISH: Opening scene with primitive humans around campfire, camera slowly pushes in toward the flames, mythical shapes emerging from smoke"
    }
  ],
  "total_duration": 180,
  "opening_hook": "如果有人告诉你，小麦才是地球上最成功的物种，你会相信吗？",
  "closing_statement": "这就是人类简史告诉我们的：我们统治世界，不是因为我们最强壮，而是因为我们最会讲故事。"
}
```

**关键设计点**：
- `narration_text` 是中文（用于TTS朗读）
- `visual_direction` 是英文（给Stage 4用于生成image_prompt）
- 口语化风格，适合TTS朗读
- 有节奏感：开头有hook，结尾有总结
- 每段控制在20-40秒

---

### 3. book_storyboard_prompt.py - 配图分镜

**输入**：Stage 2的输出（narration_script）

**输出JSON结构**：
```json
{
  "shots": [
    {
      "shot_id": 1,
      "segment_ref": 1,
      "image_prompt": "ENGLISH ONLY: A group of primitive humans sitting in a circle around a glowing campfire in a dark cave. Smoke rises and forms translucent shapes of mythical creatures - a dragon, a spirit, a moon goddess. The humans look up in wonder, their faces illuminated by firelight. Photorealistic style, dramatic lighting, cinematic composition.",
      "shot_type": "wide shot",
      "camera_angle": "slightly low angle",
      "mood": "mystical, awe-inspiring"
    }
  ]
}
```

**关键设计点**：
- `image_prompt` **必须全英文**
- 重点是**概念可视化**，不是角色一致性
- 镜头偏静态（知识传递不需要动作戏）
- 抽象概念必须转化为具体、可画的场景

**与短剧Prompt的核心差异**：

| 维度 | 短剧 Prompt | 书籍解说 Prompt |
|------|-------------|-----------------|
| 核心关注 | 角色一致性（身份映射、参考图） | 概念可视化（抽象→具体） |
| 角色处理 | 完整physical+clothing描述 | 通用人物描述即可 |
| 连续性 | 场景环境连续（VISUAL CONTINUITY） | 视觉风格统一即可 |
| 动作 | 需要具体动作、表情 | 偏静态、意象化 |

---

## 书籍解说的特殊Prompt技巧

### 概念可视化指令块（建议加入）

```
CONCEPT VISUALIZATION RULES:
- Abstract concepts MUST be converted to concrete, visualizable scenes
- NO text overlays, infographics, charts, or diagrams in the image
- Use metaphorical scenes to represent ideas
- Examples:
  - "Cognitive revolution" → primitive humans around campfire with mythical smoke shapes
  - "Agricultural trap" → split image: exhausted farmer vs. carefree hunter-gatherer
  - "Power of fiction" → diverse people united under the same banner/symbol
```

### 风格一致性指令（建议加入）

```
VISUAL STYLE CONSISTENCY:
- All images must follow the same artistic style: {style}
- Maintain consistent color palette throughout
- Similar lighting mood across all shots
- Do NOT mix realistic and cartoon elements
```

---

## 测试用例

用这个输入测试：

```python
BOOK_INPUT = {
    "title": "人类简史",
    "author": "尤瓦尔·赫拉利",
    "summary": """
《人类简史》讲述了人类从7万年前的认知革命到21世纪的科技革命的历程。

核心观点：
1. 认知革命：智人能够创造和相信虚构故事（神话、宗教、国家、货币），这是人类统治地球的关键
2. 农业革命是"史上最大骗局"：人类以为驯化了小麦，实际上是小麦驯化了人类
3. 帝国、货币、宗教是统一人类的三大力量
4. 科学革命：承认无知是进步的开始
5. 快乐悖论：物质进步不等于幸福增加
""",
    "target_duration": 180,  # 3分钟
    "style": "illustration"
}
```

---

## 关键约束（红线）

1. **不修改现有文件** - 尤其是 `storyboard_prompts.py`
2. **所有图像相关字段必须英文** - visual_concept, visual_direction, image_prompt
3. **不追求完美** - 先跑通，后续迭代
4. **遵循现有Prompt结构** - 参考 `app/prompts/story_generation.py` 的风格

---

## 完成后通知

完成Prompt编写后：
1. 更新你的 `ai-ml-progress/context-for-others.md`
2. 通知 @Backend，我来写测试脚本跑通流程

---

## 参考资料

- 整体实验方案：`.team-brain/handoffs/BOOK_NARRATION_EXPERIMENT.md`
- 现有Prompt示例：`app/prompts/story_generation.py`
- 我已创建的目录：`app/prompts/book/`（含`__init__.py`）

---

**有问题随时问。这是探索性任务，遇到卡点及时沟通。**
