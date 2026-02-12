# PM决策：TextOverlay方案V2 - 优化升级

**日期**: 2026-01-22
**决策者**: @PM
**状态**: 🆕 新任务分配
**优先级**: P0

---

## 背景

TextOverlayService V1 验收结果：**功能通过，但需优化**

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 文字重叠 | 原图已有乱码文字 | AI-ML写新的"无文字"Prompt模板 |
| 字体偏小 | 28px对于768x1344图偏小 | 增大50%到42px |
| 气泡位置固定 | 只有upper_right选项 | 根据角色位置动态定位 |
| 无情感强调 | 参考图有红色高亮效果 | LLM驱动的强调词检测 |

---

## 参考图文字样式分析

### IMG_0804 - 情感强调效果 ⭐

```
普通文字（白色）: "那天和男朋友逛街，让他帮我拍照，拍了好多张"
强调文字（红色+放大）: "没一张能看的！！！"
```

**强调触发条件**：
- 多个感叹号（!!!）
- 强烈情绪词（生气、崩溃、震惊）
- 转折/重点词

### IMG_0805 - 情感符号

- 男主头顶有"?"问号符号
- 底部旁白无强调

### IMG_0812 - 多角色气泡定位

```
女主气泡: "对不起。" - 位于女主附近，尖角指向她
男主气泡: "什么?" - 位于男主附近，尖角指向他
旁白: "他懂了。" - 左侧黑色垂直条
```

**气泡位置规则**：气泡应靠近说话角色，尖角指向角色嘴部方向

---

## 任务分配

### ⚠️ 重要原则

1. **现有Prompt模板不要修改** - 保留用于后续Pro模型测试
2. **代码保持独立** - 不耦合主流程
3. **这仍是验证测试** - 效果不佳时启动Plan B

---

## TASK-001: @AI-ML - 新建无文字Prompt模板

### 任务说明

**单独创建**一套用于TextOverlay测试的Prompt模板，**不修改现有模板**。

### 输出文件

```
docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md  # 新文件，不改现有的
```

### 模板要求

在现有模板基础上，添加以下指令（替换所有TEXT OVERLAY相关内容）：

```
TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any of the following in the image:
- Text, letters, words, or characters (Chinese, English, or any language)
- Speech bubbles or dialogue balloons
- Caption boxes or narrative text areas
- Written signs, labels, or watermarks
- Any form of typography or calligraphy

COMPOSITION GUIDANCE:
- Leave clean space at the TOP (0-15% of height) for text overlay
- Leave clean space at the BOTTOM (80-100% of height) for text overlay
- Keep the center area clear for potential center text overlay
- Ensure character faces and expressions are not obstructed by these reserved areas
```

### 需要覆盖的模板类型

| 类型 | 原模板 | 新模板改动 |
|------|--------|-----------|
| 对话场景 | `speech_bubble_*` | 移除气泡描述，保留角色表情 |
| 黑底旁白 | `black_monologue_*` | 移除旁白条描述 |
| 白底旁白 | `white_narrative_*` | 移除旁白条描述 |
| 分屏效果 | `split_screen` | 移除中央文字描述 |
| 回忆碎片 | `memory_fragments` | 移除底部旁白描述 |
| 画中画 | `picture_in_picture_*` | 移除气泡/旁白描述 |

### 验收标准

- [ ] 新建独立文件，不修改现有模板
- [ ] 所有6种模板类型都有无文字版本
- [ ] 明确的空间预留指令（顶部/底部/中央）

---

## TASK-002: @Backend - TextOverlayService V2 增强

### 任务说明

基于V1验收反馈，增强TextOverlayService功能。

### 增强项1：字体大小增大50%

```python
# V1 配置
DEFAULT_FONT_SIZE = 28
SPEECH_BUBBLE_FONT_SIZE = 24

# V2 配置 (+50%)
DEFAULT_FONT_SIZE = 42
SPEECH_BUBBLE_FONT_SIZE = 36
```

### 增强项2：动态气泡位置

根据说话角色在画面中的位置，动态调整气泡位置：

```python
def add_speech_bubble(
    self,
    image: Image.Image,
    text: str,
    speaker_position: str = "right",  # "left", "right", "center"
    speaker_vertical: str = "upper"   # "upper", "middle", "lower"
) -> Image.Image:
    """
    根据说话者位置动态定位气泡

    speaker_position: 说话者在画面中的水平位置
    speaker_vertical: 说话者在画面中的垂直位置

    气泡逻辑：
    - 说话者在右侧 → 气泡在右上，尖角指向右下
    - 说话者在左侧 → 气泡在左上，尖角指向左下
    - 说话者在中间 → 气泡在上方中央，尖角指向下方
    """
```

### 增强项3：LLM驱动的情感强调 ⭐

**核心功能**：调用LLM分析文字内容，自动识别需要强调的词句。

```python
@dataclass
class TextEmphasis:
    """文字强调配置"""
    text: str                    # 原始文字
    emphasized_parts: List[str]  # 需要强调的部分
    emphasis_type: str           # "red_large" | "bold" | "none"

async def analyze_text_emphasis(text: str) -> TextEmphasis:
    """
    调用LLM分析文字，识别需要强调的部分

    规则：
    1. 多个感叹号(!!!) → 该句强调
    2. 强烈情绪词(生气、崩溃、震惊、不敢相信) → 强调
    3. 转折词后的重点(但是、可是、然而) → 强调
    4. 直接引语中的关键词 → 可能强调

    返回：
    - emphasized_parts: 需要高亮的词/句
    - emphasis_type: "red_large" (红色+放大) 或 "bold" (仅加粗)
    """
```

**渲染效果**：
```python
def render_with_emphasis(
    self,
    draw: ImageDraw.ImageDraw,
    text: str,
    emphasis: TextEmphasis,
    base_color: str = "white",
    emphasis_color: str = "#FF4444",  # 红色
    base_size: int = 42,
    emphasis_size: int = 52  # 放大约25%
):
    """渲染带强调效果的文字"""
```

### 增强项4：支持多气泡

```python
def add_multiple_speech_bubbles(
    self,
    image: Image.Image,
    bubbles: List[dict]  # [{"text": "...", "speaker": "left"}, ...]
) -> Image.Image:
    """支持一张图多个对话气泡（多角色对话）"""
```

### 输出文件

```
tests/test_text_overlay_v2.py  # 新测试脚本
# 或直接增强现有 tests/test_text_overlay.py
```

### 验收标准

- [ ] 字体大小增大50%
- [ ] 气泡位置可根据说话者动态调整
- [ ] LLM强调功能可用（至少识别感叹号场景）
- [ ] 支持多气泡场景

---

## TASK-003: @Backend - 重新生成无文字测试图

### 前置条件

等待 @AI-ML 完成 TASK-001（无文字Prompt模板）

### 任务说明

使用新的无文字Prompt模板，重新生成5张测试图。

```bash
# 使用新模板生成
python tests/test_comic_mvp_story_no_text.py
```

### 输出

```
test_output/comic_mvp_test/no_text_images/
├── shot_01.png  # 无文字版本
├── shot_06.png
├── shot_08.png
├── shot_12.png
└── shot_14.png
```

---

## TASK-004: @Tester - V2 验收

### 前置条件

- TASK-001 完成（无文字Prompt模板）
- TASK-002 完成（TextOverlayService V2）
- TASK-003 完成（无文字测试图）

### 验收内容

| 维度 | 标准 |
|------|------|
| 文字重叠 | 无重叠（原图无文字） |
| 字体大小 | 与参考图接近 |
| 气泡位置 | 靠近对应说话角色 |
| 情感强调 | 感叹句有红色高亮效果 |

---

## 任务依赖关系

```
TASK-001 (@AI-ML: 无文字Prompt模板)
    ↓
TASK-003 (@Backend: 重新生成无文字测试图)
    ↓                              ↘
TASK-002 (@Backend: TextOverlayService V2)
    ↓                              ↙
TASK-004 (@Tester: V2 验收)
```

**可并行**：TASK-001 和 TASK-002 可同时进行

---

## LLM强调功能的Prompt示例

```
你是一个漫画文字分析助手。分析以下文字，识别需要视觉强调的部分。

文字：那天和男朋友逛街，让他帮我拍照，拍了好多张没一张能看的！！！

请返回JSON格式：
{
  "original_text": "那天和男朋友逛街，让他帮我拍照，拍了好多张没一张能看的！！！",
  "segments": [
    {"text": "那天和男朋友逛街，让他帮我拍照，拍了好多张", "emphasis": "none"},
    {"text": "没一张能看的！！！", "emphasis": "red_large", "reason": "多感叹号，表达强烈不满"}
  ]
}

强调规则：
1. "red_large": 红色+放大 - 用于强烈情绪（愤怒、震惊、崩溃）
2. "bold": 加粗 - 用于重点词但非强烈情绪
3. "none": 无强调 - 普通叙述
```

---

## 文档更新记录

| 时间 | 更新内容 |
|------|----------|
| 2026-01-22 19:00 | 创建V2决策文档，定义4个任务 |

---

**PM签名**: @PM
