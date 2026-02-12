# PM独立审查报告 - V3验收复核

**审查人**: @PM
**审查日期**: 2026-02-03
**审查对象**: test_output/comic_cc_kai_story_v2/

---

## 🚨 审查结论：V3验收存在重大遗漏

Tester验收报告称"全部通过"，总体评分4.9/5。**PM独立审查发现多项严重问题被漏检**。

---

## 问题分类与根因分析

### 🔴 问题1: Speaker前缀未剥离（严重）

**Tester报告**: "对话气泡不含speaker前缀 ✅ 通过"

**实际情况**: 仅对话气泡(dialogue)正确剥离，**心理独白(thought)类型完全未处理**

**受影响shots** (共8个):
| Shot | 显示文字 | 应显示 |
|------|---------|--------|
| 04 | "Kai内心：「这件毛衣...应该还行吧？」" | "「这件毛衣...应该还行吧？」" |
| 06 | "Kai内心：「还有五分钟...她会喜欢这里吗？」" | "「还有五分钟...她会喜欢这里吗？」" |
| 09 | "Cici内心：「那个穿黑色大衣的...是他吗？」" | "「那个穿黑色大衣的...是他吗？」" |
| 11 | "Kai内心：「她笑起来，比照片还好看。」" | "「她笑起来，比照片还好看。」" |
| 21 | "Kai内心：「她讲话的样子真好看。」" | "「她讲话的样子真好看。」" |
| 27 | "Cici内心：「他的手好像碰到我了...是不小心的吗？」" | "「他的手好像碰到我了...是不小心的吗？」" |
| 28 | "Kai内心：「我可以...牵她的手吗？」" | "「我可以...牵她的手吗？」" |
| 41 | "Kai内心：「这一刻，我知道...她就是那个人。」" | "「这一刻，我知道...她就是那个人。」" |

**根因分析** (test_comic_cc_kai.py):

```python
# 第1624-1625行: add_speech_bubble 调用 strip_speaker_prefix
def add_speech_bubble(self, image, text, ...):
    clean_text = strip_speaker_prefix(text)  # ✅ 对话正确处理

# 第1564行: add_monologue 不调用 strip_speaker_prefix
def add_monologue(self, image, text, ...):
    # ❌ 直接使用 text，未剥离前缀

# 第1700-1704行: thought类型处理
elif text_type == "thought":
    result, bar_height = self.add_monologue(result, chinese_text, ...)
    # ❌ 未在传入前剥离前缀
```

**修复方案**: 在`add_monologue`开头添加`strip_speaker_prefix`调用，或在`process_shot`的thought分支中先剥离

---

### 🔴 问题2: 气泡透明度完全无效（严重）

**Tester报告**: "气泡半透明 ✅ 通过，气泡有轻微透明效果"

**实际情况**: **所有42张图的气泡都是纯白不透明**

**代码分析** (test_comic_cc_kai.py 第1656-1660行):

```python
# P1修复 TASK-5：使用半透明白色背景（75%不透明度）
bubble_fill_color = (255, 255, 255, 191)  # RGBA, alpha=191
draw.rounded_rectangle(bubble_rect, radius=18, fill=bubble_fill_color, ...)
```

**根因**: PIL的`ImageDraw.Draw().rounded_rectangle()`在RGBA图像上直接绘制时，**不会正确处理alpha通道混合**。shape直接覆盖底层像素，alpha值被忽略。

**正确做法对比** (add_monologue 第1588-1595行 正确实现):

```python
# 创建透明层
overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
overlay_draw = ImageDraw.Draw(overlay)
overlay_draw.rectangle([...], fill=(0, 0, 0, adaptive_alpha))
# 使用alpha_composite合成
img = Image.alpha_composite(img, overlay)
```

**修复方案**: `add_speech_bubble`需要使用与`add_monologue`相同的透明层合成方法

---

### 🟡 问题3: 气泡重叠（中等）

**Tester报告**: "未专门测试dialogue_with_*类型"

**受影响shots**: shot_02, shot_03, shot_18

**根因分析**:
- `get_bubble_position_for_index`函数只用于纯`dialogue`类型
- `dialogue_with_narration`/`dialogue_with_thought`类型走不同代码路径
- 混合类型的气泡位置硬编码为`(50, 5)`，多个气泡位置相同

**代码位置** (第1730-1751行):

```python
elif text_type in ["dialogue_with_thought", "dialogue_with_narration", ...]:
    for txt in texts:
        if "：「" in txt:
            result = self.add_speech_bubble(result, txt,
                bubble_x_percent=50, bubble_y_percent=5)  # ❌ 硬编码位置
```

---

### 🟡 问题4: 黑边/白边问题（中等）

这是**图像生成模型**的问题，不是文字叠加服务的问题。

| 类型 | 受影响shots | 可能原因 |
|------|-------------|---------|
| 黑边 | shot_01, shot_17, shot_34(轻微) | Prompt未明确要求画面填充 |
| 白边 | shot_22, shot_35, shot_36, shot_39, shot_42 | 构图留白过多 |

**建议**: 在Prompt中添加 `Fill the entire canvas. No letterboxing or empty margins.`

---

### 🟡 问题5: 亲密行为不当（中等）

**受影响shots**: shot_25, shot_26, shot_27

**问题**: 女生挽着男生手臂，对于"刚认识第一次约会"的情节过于亲密

**根因**: 图像生成模型对"walking together"的理解偏向浪漫亲密

**建议**: Prompt中明确 `Walking side by side with appropriate distance. NOT linking arms.`

---

### 🟢 问题6: 气泡遮挡脸部（轻微）

**受影响shots**: shot_13, shot_31

shot_31有多个气泡在顶部，但从实际图片看遮挡程度可接受。shot_13的气泡位置接近角色但未严重遮挡。

---

## 验收对比

| 验收项 | Tester结论 | PM复核 | 差异 |
|--------|-----------|--------|------|
| Speaker前缀剥离 | ✅ 通过 | ❌ **8处遗漏** | 严重差异 |
| 气泡半透明 | ✅ 通过 | ❌ **完全无效** | 严重差异 |
| 碰撞检测(shot_42) | ✅ 通过 | ✅ 通过 | 一致 |
| 3+气泡(shot_19) | ✅ 通过 | ✅ 通过 | 一致 |
| Shot 28生成 | ✅ 通过 | ✅ 通过 | 一致 |
| Shot 34构图 | ✅ 通过 | ✅ 通过 | 一致 |
| 黑边/白边 | ⬜ 未检测 | 🟡 9处问题 | 漏检 |
| 气泡重叠 | ⬜ 未检测 | 🟡 3处问题 | 漏检 |
| 亲密行为 | ⬜ 未检测 | 🟡 3处问题 | 漏检 |

---

## 修复优先级

### P0 必须修复（阻塞发布）

1. **Speaker前缀剥离** - 用户看到"Kai内心："会感觉产品质量低
2. **气泡透明度** - 代码已写但完全无效，是明显bug

### P1 建议修复

3. **混合类型气泡位置** - 多气泡重叠影响阅读体验
4. **亲密行为Prompt** - 内容不符合故事情节

### P2 低优先级

5. **黑边/白边** - 影响美观但不影响功能
6. **气泡遮挡脸部** - 个别镜头，影响轻微

---

## 给Backend的修复任务

### TASK-B1: Speaker前缀剥离（P0）

**文件**: tests/test_comic_cc_kai.py

**方案A**（推荐）: 在`add_monologue`开头添加剥离

```python
def add_monologue(self, image, text, position="bottom", ...):
    # P0修复：剥离speaker前缀
    clean_text = strip_speaker_prefix(text)
    # ... 后续使用 clean_text
```

**方案B**: 在`process_shot`的thought分支剥离

### TASK-B2: 气泡透明度修复（P0）

**文件**: tests/test_comic_cc_kai.py

**修复**: 使用透明层合成替代直接绘制

```python
def add_speech_bubble(self, image, text, ...):
    img = image.copy()
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # 创建透明气泡层
    bubble_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    bubble_draw = ImageDraw.Draw(bubble_layer)

    bubble_fill_color = (255, 255, 255, 191)  # 75%不透明
    bubble_draw.rounded_rectangle(bubble_rect, radius=18,
        fill=bubble_fill_color, outline=(0, 0, 0, 255), width=2)
    # 绘制尾巴...

    # 合成
    img = Image.alpha_composite(img, bubble_layer)

    # 在合成后的图像上绘制文字（文字需要不透明）
    draw = ImageDraw.Draw(img)
    # ... 绘制文字
```

### TASK-B3: 混合类型气泡位置（P1）

在`dialogue_with_*`分支使用`get_bubble_position_for_index`计算位置

---

## 给AI-ML的修复任务

### TASK-A1: 边缘留白约束（P2）

在所有Prompt末尾添加:
```
COMPOSITION: Fill the entire canvas edge to edge. No letterboxing, no black/white margins at top or bottom.
```

### TASK-A2: 亲密行为约束（P1）

对shot_25-27的Prompt修改:
```
INTERACTION: Walking side by side with appropriate social distance.
DO NOT show linking arms, holding hands, or other intimate physical contact.
This is their FIRST DATE - keep body language friendly but not romantic.
```

---

## 结论

V3验收报告存在**重大遗漏**。两个P0问题（Speaker前缀、透明度）必须修复后重新验收。

**建议流程**:
1. Backend修复 TASK-B1, TASK-B2
2. 重新运行测试生成 V4
3. PM再次独立验收
4. 确认无遗漏后发布

---

**@PM**
2026-02-03
