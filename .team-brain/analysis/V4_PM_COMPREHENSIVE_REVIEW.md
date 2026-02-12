# PM独立复核报告 - V4综合分析

> **审核日期**: 2026-02-03
> **审核人**: PM Agent
> **审核范围**: comic_cc_kai_story (V1) 和 comic_cc_kai_story_v2 (V2) 全部42张图片
> **核心原则**: 我们是要做一个**通用的工具**，而不是为了完善单一的故事

---

## 一、执行摘要

| 问题类别 | V1状态 | V2状态 | 严重程度 | 负责方 |
|---------|--------|--------|----------|--------|
| Speaker前缀 | 未移除 | ✅ 已移除 | - | Backend |
| 「」符号 | 保留 | 保留 | P1 | Backend |
| 气泡重叠 | 严重 | 严重 | **P0** | Backend |
| 气泡透明度 | 不够透明 | 不够透明 | P2 | Backend |
| 碰撞检测 | 未使用 | 未使用 | P1 | Backend |
| 边缘填充 | 11+ shots | 6+ shots | **P0** | AI-ML |
| 亲密度问题 | shot_27/40 | shot_27/40 | **P0/P1** | AI-ML |
| 角色一致性 | 2+ shots | 2+ shots | P1 | AI-ML |

**整体评分**: 3.5/5 (V2相对V1有进步，但仍有P0级问题未解决)

---

## 二、图片审查详细发现

### 2.1 with_text_images 问题汇总

#### 气泡重叠问题 (P0)

| Shot | V1表现 | V2表现 | 根本原因 |
|------|--------|--------|----------|
| shot_02 | 气泡完全重叠 | 文字有乱码叠加 | process_shot()混合类型固定位置 |
| shot_03 | 气泡完全重叠 | 有乱码叠加 | 同上 |
| shot_18 | 气泡完全重叠 | 有乱码叠加 | 同上 |
| shot_19 | 3个气泡堆叠 | 3个气泡堆叠顶部 | 同上 |
| shot_31 | 2个气泡重叠 | 3个气泡严重重叠 | 同上 |
| shot_37 | 2个气泡重叠 | 改善但仍有问题 | 同上 |

**代码根因分析** (`app/services/text_overlay_service.py:497-499`):
```python
elif "：「" in txt or ":「" in txt or "：\"" in txt:
    # 对话气泡 - 所有dialogue都用固定位置!
    result = self.add_speech_bubble(result, txt, bubble_x_percent=50, bubble_y_percent=5)
```

**问题**: 混合类型(dialogue_with_narration等)中的多条对话全部使用固定位置(50, 5)，没有索引递增！

#### 「」符号问题 (P1)

| Shot | 气泡内容示例 | 期望内容 |
|------|-------------|----------|
| shot_02 | 「下次做给你吃？」 | 下次做给你吃？ |
| shot_12 | 「你好，Cici。终于见到真人了。」 | 你好，Cici。终于见到真人了。 |

**代码根因** (`app/services/text_overlay_service.py:82-83`):
```python
if not content.startswith('「') and not content.startswith('"'):
    return f"「{content}」"  # <-- 会添加「」!
```

**代码根因** (`app/services/text_overlay_service.py:82-83`):
```python
if not content.startswith('「') and not content.startswith('"'):
    return f"「{content}」"  # <-- 会添加「」!
```

### 2.2 no_text_images 问题汇总

#### 边缘填充问题 (P0)

| Shot | 问题描述 | V1 | V2 |
|------|----------|----|----|
| shot_06 | 上下有白边 | 有 | 有 |
| shot_21 | 上下有白边 | 有 | 有 |
| shot_22 | 上边有分隔线 | 有 | 改善 |
| shot_23 | 上边有暗边 | 有 | 有 |
| shot_24 | 有边缘问题 | 有 | 改善 |
| shot_28 | 下边有白边 | 有 | 改善 |
| shot_34 | **顶部大白边** | 严重 | 严重 |
| shot_36 | 上下有黑边 | 有 | 有 |

**原因分析**: Prompt中的FULL CANVAS COMPOSITION约束未被AI严格遵守

#### 亲密度问题 - 首次约会场景

| Shot | 行为 | 状态 | Founder决策 |
|------|------|------|-------------|
| shot_27 | Cici挽着Kai的手臂 | **需修复** | 改为过马路时保护性触碰 |
| shot_28 | 两人手即将触碰 | ✅ OK | 可接受的自然互动 |
| shot_29 | 牵手特写 | ✅ OK | Founder确认：约会契合后不违和 |
| shot_40 | 亲吻脸颊 | **需微调** | 改为男生偷亲女生（而非女生亲男生）|

**Founder澄清 (2026-02-03 18:30)**:
1. shot_29牵手、shot_40亲吻都OK，两人约会后契合不违和
2. shot_27挽臂是主要问题（出现在牵手之前违和）
3. shot_40微调：改为男生偷亲女生更自然

#### 角色一致性问题 (P1)

| Shot | 问题 | 参考图设定 |
|------|------|-----------|
| shot_21 | Cici穿米色/棕色衣服 | 黑大衣+红围巾 |
| shot_23 | Cici没有红围巾 | 黑大衣+红围巾 |
| shot_29 | Cici穿白色高领 | 黑大衣+红围巾 |

**原因分析**: 角色参考图(character reference image)未被正确应用到所有场景

---

## 三、代码架构问题 (通用性视角)

### 3.1 已发现但未修复的代码缺陷

| 缺陷 | 文件:行号 | 影响 | 通用性影响 |
|------|-----------|------|-----------|
| 混合类型气泡位置固定 | text_overlay_service.py:499 | 所有混合类型dialogue重叠 | **高** - 所有故事受影响 |
| detect_overlay_collision未调用 | text_overlay_service.py:119 | 碰撞检测形同虚设 | **高** - 所有故事受影响 |
| 「」符号添加逻辑 | text_overlay_service.py:82-83 | 所有气泡有不需要的引号 | **高** - 所有故事受影响 |
| bubble_alpha固定191 | text_overlay_service.py:320 | 透明度不可配置 | 中 - 可接受但不灵活 |

### 3.2 建议的修复方案

#### FIX-1: 混合类型气泡位置 (P0)

```python
# 当前代码 (Line 480-499)
elif text_type in ["dialogue_with_thought", "dialogue_with_narration", ...]:
    texts = chinese_text if isinstance(chinese_text, list) else [chinese_text]
    dialogue_index = 0  # <-- 添加索引跟踪
    for txt in texts:
        if "：「" in txt or ":「" in txt:
            total_dialogues = sum(1 for t in texts if "：「" in t or ":「" in t)
            x_pct, y_pct = get_bubble_position_for_index(dialogue_index, total_dialogues)
            result = self.add_speech_bubble(result, txt, bubble_x_percent=x_pct, bubble_y_percent=y_pct)
            dialogue_index += 1  # <-- 递增索引
```

#### FIX-2: 「」符号移除 (P1)

```python
# 当前代码 (Line 77-85)
def strip_speaker_prefix(text: str) -> str:
    pattern = r'^[\w\u4e00-\u9fff]+(?:内心)?[：:]\s*[「"『]?(.+?)[」"』]?$'
    match = re.match(pattern, text.strip())
    if match:
        content = match.group(1)
        # 移除这段添加「」的逻辑
        # if not content.startswith('「'):
        #     return f"「{content}」"
        return content  # 直接返回内容，不加引号
    return text
```

#### FIX-3: 启用碰撞检测 (P1)

在`add_speech_bubble()`中调用`detect_overlay_collision()`，如果检测到碰撞则自动调整y位置。

---

## 四、Prompt/AI-ML问题 (通用性视角)

### 4.1 边缘填充约束强化

当前约束不够强，建议增强为:

```
CRITICAL COMPOSITION RULE - ZERO TOLERANCE:
- The image MUST fill 100% of the canvas with ZERO margins
- NO white, black, gray, or any colored borders at ANY edge
- If the scene cannot fill the frame naturally, EXTEND the background
- This is a HARD REQUIREMENT - images with borders will be rejected
```

### 4.2 亲密度约束通用化

建议在`docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md`中添加"场景情境约束块"，不同故事类型使用不同约束:

| 情境类型 | 约束示例 |
|---------|---------|
| 首次约会 | 保持一臂距离，无身体接触 |
| 热恋期 | 允许牵手、挽臂，无亲吻 |
| 已婚夫妻 | 允许亲密行为 |

### 4.3 角色一致性强化

建议在每个shot的prompt中显式引用角色参考图，并添加:

```
CHARACTER CONSISTENCY REQUIREMENT:
- Kai: ALWAYS wears black overcoat, dark sweater, glasses
- Cici: ALWAYS wears black coat with RED scarf
- Verify clothing matches reference before generating
```

---

## 五、任务分配

### @Backend (P0优先)

| 任务ID | 描述 | 优先级 | 预估工作量 |
|--------|------|--------|-----------|
| FIX-B1 | 混合类型气泡位置索引修复 | P0 | 小 |
| FIX-B2 | 移除「」符号添加逻辑 | P1 | 小 |
| FIX-B3 | 启用detect_overlay_collision | P1 | 中 |
| FIX-B4 | bubble_alpha配置化 | P2 | 小 |

### @AI-ML (P0优先)

| 任务ID | 描述 | 优先级 | 预估工作量 |
|--------|------|--------|-----------|
| FIX-A1 | 强化边缘填充prompt约束 | P0 | 小 |
| FIX-A2 | shot_27挽臂→保护性触碰 | P0 | 中 |
| FIX-A3 | shot_40女亲男→男偷亲女 | P1 | 小 |
| FIX-A4 | 强化角色一致性约束 | P1 | 中 |
| FIX-A5 | shot_41叙事一致性（PM预审查发现）| P2 | 小 |

---

## 六、通用性收益分析

如果上述修复实施:

| 修复 | 单故事收益 | 通用工具收益 |
|------|-----------|-------------|
| FIX-B1 | shot_02/03/18/19/31/37修复 | **所有**使用mixed type的故事受益 |
| FIX-B2 | 42张图气泡文字更干净 | **所有**故事的气泡文字更干净 |
| FIX-B3 | 减少重叠 | **所有**故事自动避免重叠 |
| FIX-A1 | 6+ shots边缘修复 | **所有**故事画面更完整 |
| FIX-A2 | shot_27修复 | 表达保护性触碰更自然 |
| FIX-A3 | shot_40修复 | 亲吻方向更自然 |
| FIX-A4 | 3+ shots角色一致 | **所有**故事角色一致性提升 |
| FIX-A5 | shot_41叙事修复 | 叙事逻辑一致 |

---

## 七、执行建议

### 立即执行 (Today)
1. @Backend: FIX-B1 (混合类型气泡位置) - **阻塞性问题**
2. @Backend: FIX-B2 (移除「」符号)

### 短期执行 (This Week)
1. @AI-ML: FIX-A1 (边缘填充) - P0
2. @AI-ML: FIX-A2 (shot_27保护性触碰) - P0
3. @Backend: FIX-B3 (碰撞检测)

### 中期执行
1. @AI-ML: FIX-A3 (shot_40亲吻方向)
2. @AI-ML: FIX-A4 (角色一致性)
3. @Backend: FIX-B4 (透明度配置化)

---

## 八、结论

V2相对V1有进步（Speaker前缀已移除），但仍有**2个P0级问题**未解决:
1. 气泡重叠 (代码bug)
2. 边缘填充 (Prompt约束不够)

另有**2个P1级问题**需要处理:
- shot_27: 挽臂改为保护性触碰
- shot_40: 亲吻方向调整（男偷亲女）

从**通用工具**角度，代码级问题会影响**所有使用该系统的故事**，必须优先修复。

---

**下一步**: 等待Founder审核后分配具体任务给Backend和AI-ML。
