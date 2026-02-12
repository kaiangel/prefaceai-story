# AI-ML Agent - 给其他 Agent 的上下文

> 其他 Agent 查看此文件了解 AI-ML 的工作状态和 Prompt 约束
> **最后更新**: 2026-02-03 19:15

---

## 当前状态速览

```
状态: 🟢 空闲
刚完成: V5修复任务(FIX-A1/A2/A3/A4) ✅ 🆕🆕🆕
阻塞: 无
可请求: Prompt 优化、模型选择建议、脚本编写
```

---

## ✅ V5修复任务已完成 (2026-02-03 19:00) 🆕🆕🆕

### @Tester 请执行V5验收

**修复文件**:
- `docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md` (v2.2)
- `tests/test_comic_cc_kai.py`

**任务完成清单**:

| 任务 | 问题 | 修复方案 | 状态 |
|------|------|---------|------|
| FIX-A1 | 边缘填充约束 | 已在PROMPT-1完成，FULL CANVAS COMPOSITION已强化 | ✅ |
| FIX-A2 | shot_27挽臂违和 | 改为过马路时男生保护性触碰 | ✅ |
| FIX-A3 | shot_40女亲男 | 改为男生偷亲女生 | ✅ |
| FIX-A4 | 角色一致性 | 新增约束块+shot_21/23/29强化 | ✅ |

### FIX-A2 shot_27 保护性触碰详情

**问题**: 女生挽着男生手臂，出现在牵手(shot_29)之前，显得违和

**修复**:
- 场景改为"过马路时男生自然的保护性触碰"
- Kai轻触Cici后背引导过马路
- chinese_text: 「过马路的时候，他轻轻护着我...好贴心。」
- INTIMACY LEVEL CONSTRAINT强调PROTECTIVE触碰

### FIX-A3 shot_40 亲吻方向调整详情

**问题**: 当前是女生亲男生

**修复**:
- 改为Kai鼓起勇气偷亲Cici脸颊
- Cici变为惊喜接受方（surprised delight, blushing）
- 旁白: 「他鼓起勇气，在她脸颊偷偷落下一吻。」

### FIX-A3补充 shot_41 叙事一致性修复 (P2) 🆕

**问题**: PM审查发现shot_41与shot_40修改不一致
- 原shot_41：描述Kai被亲后摸脸颊（"touch the cheek where she kissed him"）
- 但shot_40已改为Kai主动亲Cici

**修复**:
- 改为描述Kai亲完Cici后紧张期待她的反应
- 表情：nervous hopeful, slight blush, watching for her reaction
- 情感：Nervous anticipation after taking a bold step

### FIX-A4 角色一致性约束详情

**新增模板**（`docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md` v2.2）:
```
CHARACTER CONSISTENCY REQUIREMENT:
- {character_name}: MUST wear {clothing_description}
- Verify clothing matches reference image exactly before generating
- DO NOT change, modify, or substitute any clothing items
```

**应用到的shots**:
- shot_21: Cici黑色针织衫约束 (NOT beige, NOT brown)
- shot_23: 双角色服装约束
- shot_29: 红围巾强制约束（剪影中也必须可见）

### V5验收重点

1. **shot_27**: 场景是过马路保护性触碰（非挽臂）
2. **shot_40**: 男生主动亲女生（非女生亲男生）
3. **shot_21/23**: Cici穿黑色针织衫（非米色/棕色）
4. **shot_29**: Cici红围巾在剪影中可见
5. **边缘填充**: 无黑边/白边

---

## ✅ HANDOFF-2026-02-03-001 Prompt优化任务已完成 (2026-02-03 16:00)

### @Tester 请执行V4验收

**修复文件**:
- `docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md`
- `tests/test_comic_cc_kai.py`

**任务完成清单**:

| 任务 | 问题 | 受影响shots | 修复方案 | 状态 |
|------|------|------------|---------|------|
| PROMPT-1 | 边缘填充约束（黑边/白边） | 01,17,22,34,35,36,39,42 | 增强FULL CANVAS COMPOSITION指令 | ✅ |
| PROMPT-2 | 亲密行为约束（首次约会） | 25,26,27 | 添加INTIMACY LEVEL CONSTRAINT指令 | ✅ |
| **PROMPT-2B** | **亲密行为约束通用化** | 通用模板 | 创建"场景情境约束块"章节 | ✅ |

### PROMPT-1 边缘填充约束修复详情

**问题**: 8张图有黑边(shot 01,17,34)或白边(shot 22,35,36,39,42)

**修复方案**: 在所有FULL CANVAS COMPOSITION指令块中增强约束

**修改的文件**:
1. `docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md` - 所有6个模板
2. `tests/test_comic_cc_kai.py` - TEXT_FREE_REQUIREMENT常量

**新版FULL CANVAS COMPOSITION**:
```
FULL CANVAS COMPOSITION:
- Fill the ENTIRE image canvas edge-to-edge with meaningful visual content
- NO black borders, NO white margins, NO blank areas at ANY edge
- Extend backgrounds, scenery, and visual elements to ALL four edges
- The composition must touch all four sides of the frame without any padding
- DO NOT create reserved spaces, margins, or borders of any color
```

### PROMPT-2 亲密行为约束修复详情

**问题**: shot 25, 26, 27 亲密行为不符合"首次约会"设定

**修复方案**: 在shot 25, 26, 27的Prompt中添加INTIMACY LEVEL CONSTRAINT

**新增指令块**:
```
INTIMACY LEVEL CONSTRAINT (First Date):
- This is a FIRST DATE scenario - characters have just met today
- Maintain appropriate physical distance (arm's length minimum)
- Body language should be warm but reserved, NOT overtly romantic
- NO embracing, NO hand-holding, NO arm linking, NO leaning into each other
- Expressions should show curiosity and gentle interest, NOT passion
- The mood is "getting to know each other" NOT "established couple"
```

### PROMPT-2B 亲密行为约束通用化 🆕

**背景**: Founder决策亲密行为约束应该是通用模板，供未来所有"初次约会"类故事使用

**修复方案**: 在 `docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md` 中创建 **"场景情境约束块"** 章节

**新增内容**:
1. **首次约会 (First Date)** - 控制初次见面场景的亲密度
2. **热恋期 (Honeymoon Phase)** - 允许热恋情侣的亲密互动
3. **老友重逢 (Reunion)** - 久别重逢的情感表达

**通用性收益**:
- 未来任何"初次约会"类故事可以直接引用
- 无需在每个测试文件中重复编写约束
- 版本更新到 v2.1

### V4验收重点

1. **边缘填充**: shot 01, 17, 22, 34, 35, 36, 39, 42 无黑边/白边
2. **亲密度**: shot 25, 26, 27 的肢体语言符合"首次约会"含蓄氛围
3. **之前修复**: 确认V3已修复的问题仍然有效

---

## ✅ HANDOFF-2026-02-02-014 P1任务已完成 (2026-02-02 13:00)

### @Tester 请执行V3验收

**修复文件**: `tests/test_comic_cc_kai.py`

**P1任务完成清单**:

| 任务 | 问题 | 修复方案 | 状态 |
|------|------|---------|------|
| TASK-4 | Shot 01双手腕, Shot 03六指 | 添加ANATOMY REQUIREMENT指令块 | ✅ |
| TASK-5 | Shot 28触发内容安全 | 移除敏感词，替换安全版本 | ✅ |
| TASK-6 | Shot 34诡异手/身体 | 添加构图边界约束+POV视角 | ✅ |

**关键修改详情**:

### TASK-4 解剖约束 (Shot 01, 03, 28)
```
ANATOMY REQUIREMENT:
- Each hand must have exactly 5 fingers
- Both hands must connect to the SAME pair of wrists/arms
- No duplicate limbs or floating body parts
```

### TASK-5 Shot 28 安全重写
```
修改前（触发安全限制）:
❌ "palm slightly open in unconscious invitation"
❌ "The tension is palpable"
❌ "electric moment just before contact"

修改后（安全）:
✅ "palm relaxed in natural walking posture"
✅ "A moment of quiet anticipation"
✅ "walking together in comfortable closeness"
```

### TASK-6 Shot 34 构图优化
```
COMPOSITION REQUIREMENT:
- Frame ends at center console
- Cici is NOT VISIBLE in this shot (camera is from her POV)
- Do NOT include partial body parts at frame edges
```

**V3验收重点**:
1. Shot 28 能正常生成（不触发安全限制）
2. Shot 34 无诡异手/身体出现
3. Shot 01, 03 手指数量正确（5指）

---

## ✅ HANDOFF-2026-01-30-011 Kai与Cici故事脚本已完成 (2026-01-30 12:30)

### @Backend 请接手（编写测试脚本）

**任务背景**: 都市情感题材测试 - 探探相识到首次约会

**交付物**: `docs/CC_KAI_STORY_SCRIPT.md`

**脚本内容**:

| 项目 | 内容 |
|------|------|
| 标题 | Kai与Cici初次约会 |
| 风格 | Korean Webtoon Style (韩漫) |
| 图片数 | **42** |
| 角色 | 2个 |

**角色设计完成**:

| 角色 | 关键识别标记 | ⚠️ 服装（必须用这个） |
|------|-------------|---------------------|
| Kai | 黑短发、**黑框眼镜**、高挑 | 黑紫色毛衣 + 牛仔裤 + 黑大衣 |
| Cici | 深棕色长波浪发、精致五官、白皙 | 黑色针织衫 + 浅灰裙 + 黑大衣 + **红丝巾** |

**⚠️ 重要：参考图使用说明**:
```
角色参考图仅用于脸部特征参考！
服装必须使用故事中描述的，不要用参考图服装！

Prompt中的格式：
CHARACTER REFERENCE:
- FACE REFERENCE ONLY from reference image (ignore clothing in reference)
- CLOTHING: [故事服装描述]
```

**参考图路径**: `test_output/manualtest/teststory_CCKai/character_refs/`

**情感重点镜头（4个）**:

| 镜头 | Shot编号 | 情感 |
|------|----------|------|
| 心动瞬间 | Shot 10-11 | 第一眼看到对方 |
| 散步牵手 | Shot 29 | 温暖、自然 |
| 拥抱告别 | Shot 38 | 依依不舍 |
| 脸颊之吻 | Shot 40 | 惊喜、甜蜜 |

**韩漫风格关键词**:
```
manhwa style, Korean webtoon, full color, detailed backgrounds
modern aesthetic, refined features, soft lighting, emotional expressions
```

**预期输出**:
- 测试脚本：`tests/test_cc_kai_story.py`
- 输出目录：`test_output/comic_cc_kai_story/`

---

## ✅ TASK-VERIFY-001-B 故事C脚本已完成 (2026-01-28 19:00)

### @Backend 请接手（编写测试脚本）

**任务背景**: 多风格通用性验证测试 - 赛博朋克风格

**交付物**: `docs/COMIC_STORY_C_CYBERPUNK_SCRIPT.md`

**脚本内容**:

| 项目 | 内容 |
|------|------|
| 标题 | 《最后的记忆商人》 |
| 风格 | Cyberpunk (赛博朋克) |
| 图片数 | 15 |
| 角色 | 3个 |

**角色设计完成**:

| 角色ID | 名字 | 关键识别标记 |
|--------|------|-------------|
| char_001 | 林夜 | **银色左眼义眼(蓝光)**、右脸疤、深灰皮夹克 |
| char_002 | 老陈 | **白发**、褪色蓝工装、金属拐杖、手背氧化端口 |
| char_003 | 凯拉 | **银白短发**、**红色双义眼**、**全金属右臂**、黑色战术装甲 |

**特殊场景处理**:
- Shot 10-11: 追逐场景（动态模糊、雨中霓虹）
- **Shot 14**: 记忆场景（**明亮自然光**，与暗黑风格形成强烈对比）

**赛博朋克风格关键词**:
```
cyberpunk, neon lights (pink, cyan, purple), wet reflective surfaces
holographic displays, dark atmosphere, futuristic technology
dense urban environment, dramatic lighting contrasts
```

**验证重点**:
- 赛博义眼一致性（林夜左眼银色蓝光、凯拉双眼红色）
- 金属义肢（凯拉右臂）在相关镜头中可见
- 霓虹风格稳定性
- Shot 14 对比效果

**预期输出目录**: `test_output/comic_full_story_v2_cyberpunk/`

---

## ✅ TASK-RESILIENCE-001-B 已完成 (2026-01-28 01:00) 🆕🆕

### @Backend 请接手（集成安全改写到 image_generator.py）

**任务背景**: Shot 06 因 Gemini 内容安全过滤失败，需要智能改写机制

**交付物**: `app/prompts/prompt_safety_rewrite.py`

**文件内容**:

| 组件 | 说明 |
|------|------|
| `SensitiveCategory` | 6种敏感类型枚举 |
| `SENSITIVE_WORD_REPLACEMENTS` | 80+ 敏感词 → 安全替代映射 |
| `GENRE_SPECIFIC_REPLACEMENTS` | 4种题材特定规则 |
| `SAFETY_REWRITE_PROMPT` | Haiku 智能改写 Prompt 模板 |
| `detect_sensitive_content()` | 检测敏感内容 |
| `apply_simple_replacements()` | 简单规则替换（零成本兜底） |
| `build_rewrite_prompt()` | 构建 Haiku 改写请求 |

**@Backend 集成指南**:

```python
from app.prompts.prompt_safety_rewrite import (
    detect_sensitive_content,
    apply_simple_replacements,
    build_rewrite_prompt,
    SAFETY_REWRITE_PROMPT
)

# 当检测到 CONTENT_SAFETY 错误时:
async def _rewrite_and_retry(self, original_prompt: str) -> str:
    # 方案1: Haiku 智能改写（推荐）
    rewrite_prompt = build_rewrite_prompt(original_prompt)
    response = await self.haiku_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": rewrite_prompt}]
    )
    return response.content[0].text

    # 方案2: 简单规则替换（零成本兜底）
    # return apply_simple_replacements(original_prompt, genre="wuxia")
```

**敏感词分类**:

| 类别 | 示例敏感词 | 安全替代 |
|------|-----------|----------|
| 死亡 | death, dead, killed | fallen, defeated, overcome |
| 血腥 | blood, bloody, bleeding | shadow, darkness, stain |
| 暴力 | murder, killer, victim | conflict, confrontation, the other |
| 武器 | stab, slash, pierce | strike, impact, contact |
| 尸体 | corpse, body, remains | fallen figure, silhouette |
| 情绪 | agony, torment, despair | struggle, sorrow, weight |

**成本估算**: Haiku 改写 ~$0.001/次（仅在 CONTENT_SAFETY 错误时触发）

---

## ✅ TASK-VERIFY-001-B 已完成 (2026-01-27 23:30) 🆕🆕🆕

### @Backend 请接手 TASK-VERIFY-001-C（生成测试图片）

**任务背景**: 多风格通用性验证测试 - 故事B 古装武侠 + 水墨风格

**交付物**: `docs/COMIC_STORY_B_WUXIA_INK_SCRIPT.md`

**脚本内容**:

| 项目 | 内容 |
|------|------|
| 标题 | 《断剑》 |
| 风格 | Chinese Ink Wash (水墨) |
| 图片数 | 15 |
| 角色 | 4个（含回忆用年轻版本） |

**角色设计完成**:

| 角色ID | 名字 | 说明 |
|--------|------|------|
| master_old | 白川 | 60岁老剑客，白发束髻，麻布长袍 |
| master_young | 白川(年轻) | 30岁，回忆场景用，黑发蓝袍 |
| disciple | 林风 | 25岁徒弟，黑发马尾，蓝色劲装 |
| enemy | 周沧 | 50岁蒙面仇人，黑衣夜行服 |

**特殊场景处理**:
- Shot 04-06: 回忆场景（柔光、暖色调）
- Shot 06: 红色强调 `！！！`
- Shot 10-11: 动作场景（动态笔触、墨点飞溅）

**验证重点**:
- 水墨风格稳定性
- 古装服饰一致性
- 年龄版本一致性 (master_young ↔ master_old)
- 动作场景动态感

**预期输出目录**: `test_output/comic_full_story_v2_wuxia_ink/`

---

## ✅ TASK-OPT-005-A 已完成 (2026-01-27 20:30)

### @Backend 请接手 TASK-OPT-005-B（代码大幅简化！）

**背景**: TASK-OPT-004验收后，创始人发现泡泡仍遮挡角色脸部。PM评估通用性后升级方案：让AI直接推荐泡泡位置。

**交付物**: `app/prompts/character_position_detection.py` (v3)

**⚠️ 重大变更 - 输出格式改变**:

| 对比项 | 旧版 (TASK-OPT-004-A) | 新版 (TASK-OPT-005-A) |
|--------|----------------------|----------------------|
| 输出格式 | `{"x_percent": 25}` | `{"bubble_x_percent": 25, "bubble_y_percent": 8}` |
| 含义 | 角色位置 | **泡泡推荐位置** |
| y坐标 | ❌ 无 | ✅ 有 |
| 边界检查 | 代码需要 | AI已考虑 |

**新版返回格式**:
```python
# Haiku返回
{
    "daughter_child": {"bubble_x_percent": 25, "bubble_y_percent": 8, "confidence": "high"},
    "father_young": {"bubble_x_percent": 75, "bubble_y_percent": 12, "confidence": "medium"}
}
```

**@Backend 代码简化** (`test_comic_full_story_v2.py`):

```python
# 旧代码 (复杂，需要边界检查)
char_x = int(width * x_percent / 100)
bubble_x = char_x - bubble_width // 2
bubble_x = max(10, min(bubble_x, width - bubble_width - 10))
# bubble_y 还需要根据 head_top_y 计算...

# 新代码 (简单，直接使用)
bubble_x_percent = position_data.get("bubble_x_percent", 50)
bubble_y_percent = position_data.get("bubble_y_percent", 10)

bubble_x = int(width * bubble_x_percent / 100) - bubble_width // 2
bubble_y = int(height * bubble_y_percent / 100)
# 不需要额外边界检查，AI已经考虑
```

**优势**:
- 代码大幅简化，不需要边界检查
- 特写、俯视、躺卧等边缘情况AI自动处理
- 多人说话时AI自动规划不重叠

**成本**: 不变 (~$0.04/故事)

---

## ✅ TASK-OPT-004-A (已升级) (2026-01-27 18:00)

验收通过后创始人发现泡泡遮挡脸部问题。
已被 TASK-OPT-005-A 升级为AI直接推荐泡泡位置。

**TASK-OPT-004-B 已废弃**，请改用 TASK-OPT-005-B。

---

## ✅ TASK-OPT-002-A (已升级) (2026-01-26 20:00)

原版使用三分类(left/center/right)，已迭代两次升级。

---

## ✅ TASK-FIX-005 已完成 (2026-01-26 12:00)

### 修复内容

**直接修改** `tests/test_comic_full_story_v2.py` 解决V2测试图片的3个问题：

| 问题 | 修复方案 |
|------|----------|
| 留白仍存在 (10/15张) | 删除所有15个shot的"COMPOSITION GUIDANCE FOR TEXT OVERLAY"部分 |
| 乱码文字泄露 (4/15张) | 加强TEXT_FREE指令为"ABSOLUTELY NO TEXT ALLOWED" |
| LLM生成对话泡泡占位 | 删除所有"dialogue bubble"提及 |

### 新版TEXT_FREE_REQUIREMENT

```
ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

### 下一步

- @Backend: TASK-FIX-006（修复参考图生成bug）
- @Tester: 等待修复完成后重新验收

---

## ✅ TASK-FIX-001 已完成 (2026-01-23 02:00)

### 修复内容

| 问题 | 修复方案 | 修改文件 |
|------|----------|----------|
| 图片留白 | `FULL CANVAS COMPOSITION` 禁止留白 | `docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md` |
| 百分比泄露 | 移除所有 `(XX-XX% height)` | 同上 |

**注**: 红色强调检测逻辑（支持中英文`!!!`/`！！！`）由 @Backend 在 TASK-FIX-002 中处理

### v2.0核心指令块

```
TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text, speech bubbles, captions...

FULL CANVAS COMPOSITION:
- Fill the ENTIRE image canvas with meaningful visual content
- DO NOT leave any blank or empty areas in the image
- DO NOT create reserved spaces or margins - text will be overlaid in post-processing
- Extend backgrounds, scenery, and visual elements to all edges of the frame
- These are internal instructions - DO NOT render them as visible text in the image
```

### 下一步

- @Backend: TASK-FIX-002（启用参考图机制）
- @Tester: TASK-FIX-004（等待修复完成后验收）

---

## 🆕 条漫完整故事脚本 (TASK-A / HANDOFF-009) ✅ 刚完成

> 详见 `docs/COMIC_FULL_STORY_SCRIPT.md`

### 任务背景

V2技术验证通过后，PM设计了新故事《最后一碗面》用于完整故事测试（15张图）。

### 已完成内容

**交付文档**: `docs/COMIC_FULL_STORY_SCRIPT.md`

| 内容 | 说明 |
|------|------|
| 角色设计 | 4个角色（女儿3时期 + 父亲2时期）完整physical+clothing |
| image_prompt | 15张图全英文，Ghibli-inspired warm illustration风格 |
| 中文文字 | 15张图的旁白/对话/心理 + text_type + speaker_position |
| 特殊效果 | Shot 09 红色高亮，Shot 07-10 回忆柔光 |

### 下一步

- @Backend 执行 TASK-B：创建测试脚本 `tests/test_comic_full_story.py`
- @Tester 执行 TASK-C：验收完整故事

---

## 无文字Prompt模板 (TASK-001 / HANDOFF-006) ✅

> 详见 `docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md`

### 任务背景

V1测试发现：原图已有乱码文字，后处理叠加文字时导致两层文字重叠。需要创建「无文字」版本Prompt模板。

### 已完成的模板

**交付文档**: `docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md`

| # | 模板 | 说明 |
|---|------|------|
| 1 | 对话场景（无气泡）| 仅人物表情，预留气泡区域 |
| 2 | 心理旁白场景（无黑底）| 仅场景氛围，预留旁白区域 |
| 3 | 叙事旁白场景（无白底）| 仅叙事画面，预留旁白区域 |
| 4 | 分屏效果（无中央文字）| 仅分屏画面，预留中央区域 |
| 5 | 回忆碎片（无底部旁白）| 仅碎片效果，预留底部区域 |
| 6 | 画中画（无文字）| 仅画中画，屏幕不含UI文字 |

### 核心指令（所有模板包含）

```
TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any text, speech bubbles, captions, or written characters.
Leave clean space at TOP (0-15%) and BOTTOM (80-100%) for text overlay.
```

---

## 原Prompt模板 (HANDOFF-002) ✅ 已完成

**交付文档**: `docs/COMIC_MVP_PROMPT_TEMPLATES.md`
**PM审核**: ✅ 通过
**测试结果**: 图片质量优秀，但**中文文字乱码** → 触发V2方案

**重要**: 此模板保留用于未来Pro模型测试，不要修改或删除。

---

## 表情细腻度词库 (8种情绪)

| 情绪 | 英文关键词 |
|------|-----------|
| 不悦 | displeased, annoyed, furrowed brows |
| 委屈 | aggrieved, hurt, glistening eyes |
| 困惑 | confused, puzzled, tilted head |
| 道歉 | apologetic, remorseful, lowered gaze |
| 震惊 | shocked, stunned, wide eyes |
| 冷漠 | indifferent, aloof, flat expression |
| 释然 | relieved, at peace, soft smile |
| 开心 | happy, joyful, genuine smile |

---

---

## 给 @backend 的信息

### 书籍解说 Side Test ✅ 全部完成 (2026-01-19)

| 文件 | 用途 | 状态 |
|------|------|------|
| `app/prompts/book/book_outline_prompt.py` | 书籍要点提炼 | ✅ 验证通过 |
| `app/prompts/book/book_narration_prompt.py` | 解说脚本生成 | ✅ 验证通过 |
| `app/prompts/book/book_storyboard_prompt.py` | 配图分镜 | ✅ 验证通过 |

**验证结果**: @Tester于2026-01-19全部验证通过，图片生成测试3/3成功

**PM决策**: 技术可行，暂不纳入主线，保持专注短剧

**关键设计点**:
1. 重点是**概念可视化**，不是角色一致性
2. 所有图像相关字段必须英文
3. 包含 `CONCEPT_VISUALIZATION_BLOCK` 强制指令
4. 使用Flash模型即可（不需要Pro的角色一致性能力）

### Prompt 相关修改流程

1. 修改前：阅读 `/.claude/skills/prompt-engineering.md`
2. 修改后：通知 @tester 运行回归测试
3. 验收：一致性 ≥95%

### 关键文件权限

| 文件 | 修改前 |
|------|--------|
| `storyboard_prompts.py` | 必须通知 @ai-ml 审核 |
| `character_prompt_builder.py` | 必须通知 @ai-ml 审核 |

---

## Prompt 核心约束 (必读)

### 1. 图像 Prompt 必须全英文

```python
# ❌ 错误
image_prompt = "一个穿着红色连衣裙的女孩"

# ✅ 正确
image_prompt = "A girl wearing a red dress"
```

**例外** (这些中文可以保留):
- 角色中文名: "Chen Mo (陈默)"
- 中国特色地点: 胡同、祠堂、牌坊
- 传统服饰: 汉服、旗袍、马褂
- 画面中的中文文字: 春联、牌匾

### 2. Shot 生成必须用 Pro 模型 (短剧场景)

```python
# ❌ 错误 - 会导致角色一致性下降
result = await gen.generate_shot_image(..., use_pro_model=False)

# ✅ 正确
result = await gen.generate_shot_image(..., use_pro_model=True)
```

**注意**: 书籍解说场景可以使用Flash模型，因为不需要角色一致性。

### 3. 参考图必须完整传入 (短剧场景)

```python
char_refs = ref_manager.get_references_for_scene(chars_in_scene)
scene_refs = scene_ref_manager.get_references_for_location(location_id)
# 必须传入两者
reference_images = char_refs + scene_refs
```

---

## 给 @tester 的信息

### Prompt 修改后的测试

```bash
# 必须运行
python tests/test_character_consistency_regression.py

# 验收标准
- 3人场景一致性 ≥95%
- 参考图正确传入 (total_refs > 0)
- 无角色特征混淆
```

### 书籍解说场景测试 (新增)

等 @backend 完成测试脚本后，验收标准：
- [ ] image_prompt 中无中文字符
- [ ] image_prompt 中无文字/图表描述
- [ ] 生成的图片无明显文字元素

---

## 给 @pm 的信息

### 成本 vs 质量权衡

| 方案 | 成本 | 一致性 | 建议场景 |
|------|------|--------|----------|
| Pro | $9.35 | 100% | 短剧正式发布 |
| Flash | $3.11 | 70-80% | 快速预览、书籍解说 |

**当前决策**: 短剧默认使用 Pro，优先用户体验；书籍解说使用 Flash。

### 新场景支持: 书籍解说视频

**状态**: Prompt已完成，等待测试验证

**产品形态**: 抖音/B站常见的"3分钟讲完一本书"

**技术特点**:
- 不需要角色一致性（使用通用人物）
- 重点是概念可视化（抽象→具体）
- 成本更低（可用Flash模型）

---

## 风格系统

### 可用风格列表

```
realistic      # 写实摄影
cartoon        # 3D卡通
anime          # 日式动画
ghibli         # 吉卜力
illustration   # 数字插画
watercolor     # 水彩画
children_book  # 儿童绘本
cyberpunk      # 赛博朋克
ink            # 中国水墨
pixel          # 像素艺术
... (80+种)
```

### StyleEnforcer 工作原理

```python
# 在 prompt 开头注入强制风格指令
enforced_prompt = style_enforcer.enforce_prompt(original_prompt)

# 结果:
# ═══════════════════════════════════════════════════
# MANDATORY STYLE REQUIREMENT - DO NOT IGNORE
# ═══════════════════════════════════════════════════
# STYLE: Photorealistic Photography
# MUST INCLUDE: photorealistic, photograph, real photo...
# DO NOT USE: cartoon, anime, illustration...
# ═══════════════════════════════════════════════════
# [原始 prompt]
```
