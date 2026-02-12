# PM独立审查报告 V2 - 通用性视角

**审查人**: @PM
**审查日期**: 2026-02-03
**版本**: V2（从通用性视角重新分析）

---

## 🚨 核心问题：架构缺陷导致无法通用

### 当前架构问题

**TextOverlayService 在 8 个测试文件中各自重复定义：**

```
tests/test_comic_cc_kai.py          → 自己的 TextOverlayService + strip_speaker_prefix
tests/test_comic_story_b_wuxia_ink.py → 自己的 TextOverlayService（无strip_speaker_prefix）
tests/test_comic_story_c_cyberpunk.py → 自己的 TextOverlayService（无strip_speaker_prefix）
tests/test_comic_full_story_v2.py   → 自己的 TextOverlayService（无strip_speaker_prefix）
tests/test_comic_full_story.py      → 自己的 TextOverlayService（无strip_speaker_prefix）
tests/test_text_overlay_v2.py       → 自己的 TextOverlayServiceV2
tests/test_text_overlay.py          → 自己的 TextOverlayService
tests/test_new_story_overlay_v2.py  → 自己的实现
```

**主服务目录 `app/services/` 中没有 TextOverlayService！**

### 这导致的问题

| 问题 | 影响 |
|------|------|
| 代码重复 | 8份几乎相同的代码，维护噩梦 |
| 修复不传播 | 修复test_comic_cc_kai.py的bug，其他7个文件不受益 |
| 功能不一致 | cc_kai有strip_speaker_prefix，武侠/赛博朋克没有 |
| 新故事需复制 | 每个新故事都要copy-paste一份TextOverlayService |
| 违反DRY原则 | 严重违反Don't Repeat Yourself |

---

## 正确的架构应该是

```
app/services/
├── text_overlay_service.py   ← 唯一的、权威的TextOverlayService
│   ├── class TextOverlayService
│   ├── def strip_speaker_prefix()
│   ├── def add_monologue()      # 支持透明度、碰撞检测
│   ├── def add_speech_bubble()  # 支持透明度、动态位置
│   └── def process_shot()       # 通用shot处理
│
tests/
├── test_comic_cc_kai.py      → from app.services.text_overlay_service import TextOverlayService
├── test_comic_wuxia.py       → from app.services.text_overlay_service import TextOverlayService
├── test_comic_cyberpunk.py   → from app.services.text_overlay_service import TextOverlayService
└── ...所有测试共用同一个服务
```

---

## 从通用性视角重新分析V3问题

### 问题1: Speaker前缀剥离

**表象**: shot_04/06/09/11/21/27/28/41 显示 "Kai内心："/"Cici内心："

**通用性根因分析**:

| 文件 | strip_speaker_prefix | 调用位置 |
|------|---------------------|---------|
| test_comic_cc_kai.py | ✅ 有定义 | 只在add_speech_bubble调用 |
| test_comic_story_b_wuxia_ink.py | ❌ 没有 | - |
| test_comic_story_c_cyberpunk.py | ❌ 没有 | - |
| test_comic_full_story_v2.py | ❌ 没有 | - |
| 其他4个文件 | ❌ 没有 | - |

**通用性问题**:
1. 只有1个文件有`strip_speaker_prefix`，其他7个没有
2. 即使有，也只在对话气泡调用，心理独白不调用
3. **武侠、赛博朋克等故事如果有"角色内心："格式，同样会显示前缀**

**通用性解决方案**:
```python
# app/services/text_overlay_service.py

def strip_speaker_prefix(text: str) -> str:
    """
    通用Speaker前缀剥离

    支持格式:
    - "角色名：「内容」" → "「内容」"
    - "角色名内心：「内容」" → "「内容」"
    - "旁白：「内容」" → "「内容」"
    - 支持中英文冒号
    - 支持中日韩引号
    """
    import re
    # 支持各种角色名（中英文、数字）
    pattern = r'^[\w\u4e00-\u9fff]+(?:内心)?[：:]\s*(.+)$'
    match = re.match(pattern, text.strip())
    if match:
        return match.group(1)
    return text

class TextOverlayService:
    def add_monologue(self, image, text, ...):
        clean_text = strip_speaker_prefix(text)  # 所有文字都剥离前缀
        ...

    def add_speech_bubble(self, image, text, ...):
        clean_text = strip_speaker_prefix(text)  # 所有文字都剥离前缀
        ...
```

---

### 问题2: 气泡透明度无效

**表象**: 所有气泡纯白不透明

**通用性根因分析**:

| 文件 | 透明度实现方式 | 是否有效 |
|------|--------------|---------|
| test_comic_cc_kai.py | draw.rounded_rectangle(fill=RGBA) | ❌ 无效 |
| test_text_overlay_v2.py | draw.rounded_rectangle(fill="white") | ❌ 纯白 |
| 其他6个文件 | draw.rounded_rectangle(fill="white") | ❌ 纯白 |

**通用性问题**:
1. 只有cc_kai尝试了透明度，但实现方式错误
2. 其他文件甚至没有尝试透明度
3. **所有条漫故事的气泡都是不透明的**

**通用性解决方案**:
```python
# app/services/text_overlay_service.py

class TextOverlayService:
    def add_speech_bubble(self, image, text, bubble_alpha=191, ...):
        """
        添加对话气泡（支持透明度）

        Args:
            bubble_alpha: 0-255，默认191（75%不透明）
        """
        img = image.copy().convert('RGBA')

        # 创建透明气泡层（关键：必须用单独的层）
        bubble_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
        bubble_draw = ImageDraw.Draw(bubble_layer)

        # 绘制气泡（在透明层上）
        bubble_color = (255, 255, 255, bubble_alpha)
        bubble_draw.rounded_rectangle(bubble_rect, radius=18,
            fill=bubble_color, outline=(0, 0, 0, 255), width=2)

        # 合成透明层
        img = Image.alpha_composite(img, bubble_layer)

        # 文字绘制在合成后的图像上（文字不透明）
        text_draw = ImageDraw.Draw(img)
        # ... 绘制文字

        return img
```

---

### 问题3: 气泡重叠

**表象**: shot_02/03/18 多个气泡位置重叠

**通用性根因分析**:

| 文件 | 多气泡位置计算 | 碰撞检测 |
|------|--------------|---------|
| test_comic_cc_kai.py | get_bubble_position_for_index（仅dialogue类型） | ❌ 部分 |
| 其他7个文件 | ❌ 无 | ❌ 无 |

**通用性问题**:
1. 多气泡布局逻辑只在1个文件实现
2. dialogue_with_narration等混合类型不使用该逻辑
3. **任何故事的多对话场景都可能重叠**

**通用性解决方案**:
```python
# app/services/text_overlay_service.py

class TextOverlayService:
    def __init__(self):
        self.occupied_regions = []  # 跟踪已占用区域

    def _find_non_overlapping_position(self, bubble_rect, preferred_x, preferred_y):
        """寻找不与现有元素重叠的位置"""
        ...

    def add_speech_bubble(self, image, text, ...):
        # 检测碰撞，自动调整位置
        final_rect = self._find_non_overlapping_position(...)
        self.occupied_regions.append(final_rect)
        ...

    def process_shot(self, image, shot):
        self.occupied_regions = []  # 每个shot重置
        # 统一处理所有文字类型
        ...
```

---

### 问题4: 黑边/白边

**表象**: 9张图有明显的上下边缘留白/留黑

**通用性根因分析**:

这是**图像生成Prompt**的问题，不是文字叠加的问题。

**当前Prompt模板**（test_comic_cc_kai.py）:
```python
TEXT_FREE_REQUIREMENT = """
ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text...
"""
# 没有关于画面边缘填充的要求
```

**通用性问题**:
1. 无文字Prompt模板没有明确要求填满画布
2. 模型可能在上下留白/留黑作为"文字区域"
3. **所有使用该模板的故事都可能有此问题**

**通用性解决方案**:

更新 `docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md`:
```
TEXT-FREE IMAGE REQUIREMENT:
...

COMPOSITION REQUIREMENT:
- Fill the ENTIRE canvas edge to edge
- NO black bars, NO white margins at top or bottom
- NO letterboxing or pillarboxing
- Image content must extend to all four edges
```

---

### 问题5: 亲密行为不当

**表象**: shot_25/26/27 女生挽着男生，第一次约会不应如此亲密

**通用性分析**:

这是**故事内容和Prompt**的问题，不是通用工具的问题。

但工具可以提供**通用的约束机制**:
```python
# app/prompts/comic_constraints.py

FIRST_DATE_CONSTRAINTS = """
INTERACTION CONSTRAINTS (First Meeting/Date):
- Characters should maintain appropriate social distance
- NO linking arms, holding hands, or other intimate contact
- Body language should be friendly but not romantic
"""

# 在生成Prompt时根据故事阶段自动添加
```

---

## 修复优先级（通用性视角）

### P0 - 架构重构（最高优先级）

**TASK-ARCH-1: 创建统一的TextOverlayService**

```
1. 创建 app/services/text_overlay_service.py
2. 整合8个测试文件中最好的实现
3. 包含所有通用功能:
   - strip_speaker_prefix()
   - add_monologue() （透明度、碰撞检测）
   - add_speech_bubble() （透明度、动态位置）
   - process_shot() （统一shot处理）
4. 所有测试文件改为 import 主服务
```

**负责人**: @Backend
**影响范围**: 所有条漫故事

### P0 - 核心功能修复

**TASK-CORE-1: Speaker前缀剥离（在主服务中实现）**
- 所有文字类型（对话、心理、旁白）统一剥离前缀
- 支持各种格式（中英文冒号、各种引号）

**TASK-CORE-2: 气泡透明度（在主服务中实现）**
- 使用alpha_composite正确实现透明度
- 提供bubble_alpha参数供调用方配置

### P1 - 增强功能

**TASK-ENH-1: 碰撞检测（在主服务中实现）**
- 跟踪已占用区域
- 自动调整重叠元素位置

**TASK-ENH-2: Prompt边缘填充约束**
- 更新无文字Prompt模板
- 明确要求填满画布

### P2 - 故事特定修复

**TASK-STORY-1: Kai与Cici亲密行为Prompt**
- 这是故事特定的，不是通用工具问题
- 但可以在工具中提供"关系阶段约束"模板

---

## 实施计划

### Phase 1: 架构重构（必须先做）

```
Day 1:
├── @Backend: 创建 app/services/text_overlay_service.py
├── @Backend: 整合最佳实现（从8个文件中提取）
└── @Backend: 单元测试

Day 2:
├── @Backend: 迁移 test_comic_cc_kai.py 使用主服务
├── @Tester: 验证 Kai与Cici 故事功能不变
└── @Backend: 迁移其他7个测试文件
```

### Phase 2: 功能修复（架构重构后）

```
Day 3:
├── @Backend: 在主服务中实现 strip_speaker_prefix 全覆盖
├── @Backend: 在主服务中实现透明度正确合成
└── @Tester: V4验收

Day 4:
├── @Backend: 在主服务中实现碰撞检测
├── @AI-ML: 更新Prompt模板添加边缘填充约束
└── @Tester: 全量回归测试（所有故事）
```

---

## 通用性检查清单

**架构重构后，以下问题应该对所有故事都解决**:

| 问题 | 预期效果 |
|------|---------|
| Speaker前缀 | Kai与Cici、武侠、赛博朋克...所有故事自动修复 |
| 气泡透明度 | 所有故事的气泡都有正确透明度 |
| 气泡重叠 | 所有故事的多气泡场景自动布局 |
| 边缘留白 | 所有使用新Prompt模板的故事修复 |

**新故事开发时**:
- 不再需要copy-paste TextOverlayService
- 直接 `from app.services.text_overlay_service import TextOverlayService`
- 自动获得所有功能和修复

---

## 结论

**V3问题的根本原因是架构缺陷，不是单个bug**。

在测试文件中修复bug是**短期行为**，会导致：
1. 下一个故事又要重新修
2. 维护成本越来越高
3. 功能不一致

正确做法是**先架构重构，再功能修复**。这样：
1. 一次修复，所有故事受益
2. 新故事自动继承所有功能
3. 这才是"通用AI视频生成工具"应有的架构

---

## 全维度深度分析

### 维度1: 代码架构

| 分析项 | 现状 | 问题 | 通用性影响 |
|-------|------|------|-----------|
| 服务位置 | 8个测试文件各自定义 | 无主服务 | 🔴 致命 |
| 代码复用 | 完全重复 | 维护噩梦 | 🔴 致命 |
| 依赖关系 | 测试文件自包含 | 无法共享改进 | 🔴 致命 |
| 扩展性 | 每个文件独立修改 | 无法统一扩展 | 🔴 致命 |

### 维度2: 文字类型支持

**当前支持的text_type**:

| text_type | add_monologue | add_speech_bubble | strip_speaker调用 | 碰撞检测 |
|-----------|---------------|-------------------|------------------|---------|
| none | - | - | - | - |
| narration | ✅ | ❌ | ❌ 不调用 | ❌ |
| thought | ✅ | ❌ | ❌ 不调用 | ❌ |
| dialogue | ❌ | ✅ | ✅ 调用 | ⚠️ 部分 |
| dialogue_with_thought | ✅+✅ | ✅ | ⚠️ 部分（硬编码split） | ⚠️ 部分 |
| dialogue_with_narration | ✅+✅ | ✅ | ⚠️ 部分（硬编码replace） | ⚠️ 部分 |
| narration_with_thought | ✅+✅ | ❌ | ⚠️ 部分 | ⚠️ 部分 |
| narration_with_dialogue | ✅+✅ | ✅ | ⚠️ 部分 | ⚠️ 部分 |

**问题**:
1. strip_speaker_prefix只在dialogue调用，其他类型用硬编码字符串处理
2. 混合类型的文字解析靠字符串匹配（"旁白："、"内心："、"：「"），脆弱
3. 不支持新的text_type（如"monologue"、"caption"等）

### 维度3: Speaker前缀处理

**当前实现（test_comic_cc_kai.py）**:

```python
# 函数定义（独立函数）
def strip_speaker_prefix(text: str) -> str:
    pattern = r'^[\w\u4e00-\u9fff]+(?:内心)?[：:]\s*[「"『]?(.+?)[」"』]?$'
    ...

# 调用位置1: add_speech_bubble
def add_speech_bubble(self, image, text, ...):
    clean_text = strip_speaker_prefix(text)  # ✅ 调用

# 调用位置2: add_monologue
def add_monologue(self, image, text, ...):
    # ❌ 不调用strip_speaker_prefix

# 调用位置3: process_shot的dialogue_with_*分支
elif "内心：" in txt:
    clean_text = txt.split("内心：")[1]  # ❌ 硬编码split，不用strip_speaker_prefix
```

**问题**:
1. 函数存在但调用不完整
2. 混合类型用硬编码字符串处理而不是调用通用函数
3. 其他7个测试文件完全没有这个函数

**通用性需求**:
- 支持各种角色名格式（中文、英文、日文、韩文）
- 支持各种冒号（：:）
- 支持各种引号（「」""『』）
- 支持各种前缀类型（旁白、内心、OS、VO等）

### 维度4: 透明度实现

**当前实现对比**:

| 函数 | 实现方式 | 是否有效 |
|------|---------|---------|
| add_monologue | overlay层 + alpha_composite | ✅ 有效 |
| add_speech_bubble | 直接draw.rounded_rectangle(fill=RGBA) | ❌ 无效 |

**add_monologue正确实现**:
```python
overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
overlay_draw = ImageDraw.Draw(overlay)
overlay_draw.rectangle([...], fill=(0, 0, 0, adaptive_alpha))
img = Image.alpha_composite(img, overlay)  # ← 关键
```

**add_speech_bubble错误实现**:
```python
draw = ImageDraw.Draw(img)
bubble_fill_color = (255, 255, 255, 191)
draw.rounded_rectangle(bubble_rect, fill=bubble_fill_color, ...)  # ← PIL不处理alpha
```

**根因**: PIL的ImageDraw在绘制shape时不进行alpha混合，RGBA的A值被忽略

### 维度5: 碰撞检测

**当前实现**:

| 场景 | 实现 | 有效性 |
|------|------|-------|
| 多个旁白（同位置） | y_offset堆叠 | ✅ 有效 |
| 多个对话气泡 | get_bubble_position_for_index | ⚠️ 部分（只用于dialogue类型） |
| 对话+旁白混合 | 各自独立计算 | ❌ 可能重叠 |
| 气泡遮挡脸部 | bubble_y_percent=5% | ⚠️ 硬编码，不检测实际脸部位置 |

**问题**:
1. 旁白和气泡各自跟踪，不互相检测
2. 脸部遮挡只是硬编码降低y位置，不是真正的脸部检测
3. AI角色位置检测（Haiku）存在但不是所有路径都使用

### 维度6: 位置检测（AI辅助）

**当前实现**:

```python
# test_comic_cc_kai.py 有Haiku角色位置检测
from app.prompts.character_position_detection import (
    build_prompt as build_position_detection_prompt,
    extract_character_description_for_haiku,
)
```

**但**:
1. 只在test_comic_cc_kai.py实现
2. 其他7个测试文件没有
3. 不是所有text_type都使用检测结果
4. 检测失败时无降级策略

### 维度7: 字体配置

**当前实现**:
```python
FONT_PATHS = [
    "/System/Library/Fonts/STHeiti Medium.ttc",  # macOS
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    ...
]
DEFAULT_FONT_SIZE = 42
SPEECH_BUBBLE_FONT_SIZE = 36
```

**问题**:
1. 字体路径硬编码macOS路径，Linux/Windows不工作
2. 字体大小固定，不适应不同图片尺寸
3. 没有字体fallback链
4. 不支持不同语言（日文、韩文、阿拉伯文等）

### 维度8: 图片尺寸适配

**当前实现**:
```python
height_ratio = 0.18  # 旁白高度
bubble_x_percent = 50  # 气泡x位置百分比
bubble_y_percent = 5   # 气泡y位置百分比
max_bubble_width = int(width * 0.5)  # 气泡最大宽度
```

**问题**:
1. 所有尺寸用固定百分比
2. 9:16和16:9的条漫需要不同布局
3. 横屏和竖屏的文字位置应该不同
4. 没有根据图片实际内容动态调整

### 维度9: 视觉风格适配

**当前实现**: 所有故事使用相同的气泡样式

**问题**:
1. 韩漫、水墨、赛博朋克应该有不同的气泡风格
2. 气泡边框、圆角、颜色都是硬编码
3. 旁白条样式固定
4. 没有"风格配置"概念

**应该支持**:
```python
class BubbleStyle:
    border_radius: int = 18
    border_color: str = "black"
    border_width: int = 2
    fill_color: Tuple[int, int, int, int] = (255, 255, 255, 191)
    tail_style: str = "triangle"  # triangle, cloud, none

STYLES = {
    "korean_webtoon": BubbleStyle(border_radius=18, ...),
    "chinese_ink": BubbleStyle(border_radius=0, border_color="gray", ...),
    "cyberpunk": BubbleStyle(fill_color=(0, 255, 255, 150), ...),
}
```

### 维度10: 错误处理

**当前实现**: 几乎没有

**问题**:
1. 字体找不到 → 抛异常，整个处理中断
2. 文字太长 → 可能超出画面
3. chinese_text为None → 可能崩溃
4. 无效的speaker_position → 使用默认，无警告

### 维度11: 测试覆盖

**当前状态**: 无单元测试

**问题**:
1. TextOverlayService没有独立的单元测试
2. 只有端到端测试（生成整个故事）
3. 无法快速验证单个功能修复
4. 回归测试成本高

**应该有**:
```python
# tests/unit/test_text_overlay_service.py
def test_strip_speaker_prefix_chinese():
def test_strip_speaker_prefix_english():
def test_add_monologue_transparency():
def test_add_speech_bubble_transparency():
def test_collision_detection():
def test_multiple_bubbles_layout():
```

### 维度12: 文档

**当前状态**: 分散在多个地方

| 文档 | 位置 | 问题 |
|------|------|------|
| Prompt模板 | docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md | 只有Prompt，无代码文档 |
| 服务说明 | CLAUDE.md 简要提及 | 不详细 |
| API文档 | 无 | 无 |
| 使用示例 | 各测试文件 | 分散、不一致 |

### 维度13: 主流程集成

**当前状态**: TextOverlayService不在主Pipeline中

**问题**:
1. 只能通过测试脚本使用
2. 没有集成到`pipeline_orchestrator.py`
3. 用户无法通过正常流程生成带文字的条漫
4. "条漫模式"不是产品的一等公民

**应该**:
```python
# app/services/pipeline_orchestrator.py
class PipelineOrchestrator:
    def generate_comic(self, story_input, output_format="comic"):
        # ... 生成无文字图片
        if output_format == "comic":
            from app.services.text_overlay_service import TextOverlayService
            overlay_service = TextOverlayService(style=story.visual_style)
            for shot in shots:
                image = overlay_service.process_shot(image, shot)
```

### 维度14: 国际化

**当前状态**: 仅支持中文

**问题**:
1. strip_speaker_prefix的正则只考虑中文
2. 字体路径只有中文字体
3. 文字方向假设从左到右
4. 引号格式硬编码中文引号

**通用工具应该支持**:
- 多语言文字渲染
- RTL语言（阿拉伯文、希伯来文）
- 日文竖排文字
- 多语言角色名前缀

---

## 完整修复任务清单（按通用性优先级）

### 阶段0: 架构重构（必须先做）

| 任务ID | 任务 | 负责人 | 优先级 |
|--------|------|--------|--------|
| ARCH-1 | 创建 app/services/text_overlay_service.py | Backend | P0 |
| ARCH-2 | 整合8个测试文件的最佳实现 | Backend | P0 |
| ARCH-3 | 所有测试文件改为import主服务 | Backend | P0 |
| ARCH-4 | 创建单元测试 tests/unit/test_text_overlay.py | Tester | P0 |

### 阶段1: 核心功能修复

| 任务ID | 任务 | 问题 | 负责人 | 优先级 |
|--------|------|------|--------|--------|
| CORE-1 | strip_speaker_prefix全覆盖 | 8处遗漏 | Backend | P0 |
| CORE-2 | 气泡透明度正确实现 | 完全无效 | Backend | P0 |
| CORE-3 | 混合text_type统一处理 | 硬编码字符串处理 | Backend | P1 |
| CORE-4 | 碰撞检测跨类型 | 旁白/气泡互不检测 | Backend | P1 |

### 阶段2: 增强功能

| 任务ID | 任务 | 负责人 | 优先级 |
|--------|------|--------|--------|
| ENH-1 | 字体配置支持多平台 | Backend | P1 |
| ENH-2 | 动态字体大小（适应图片尺寸） | Backend | P1 |
| ENH-3 | 气泡风格配置（按visual_style） | Backend | P2 |
| ENH-4 | 图片尺寸自适应布局 | Backend | P2 |

### 阶段3: Prompt优化

| 任务ID | 任务 | 问题 | 负责人 | 优先级 |
|--------|------|------|--------|--------|
| PROMPT-1 | 边缘填充约束 | 9处黑边/白边 | AI-ML | P1 |
| PROMPT-2 | 关系阶段约束模板 | 亲密行为不当 | AI-ML | P2 |
| PROMPT-3 | 脸部遮挡区域指导 | 气泡遮挡脸部 | AI-ML | P2 |

### 阶段4: 集成与文档

| 任务ID | 任务 | 负责人 | 优先级 |
|--------|------|--------|--------|
| INT-1 | 集成到pipeline_orchestrator | Backend | P1 |
| INT-2 | 编写服务API文档 | Backend | P2 |
| INT-3 | 编写使用示例 | Backend | P2 |

---

## 影响范围汇总

**架构重构后，以下改进将自动应用于**:
- ✅ Kai与Cici（都市情感）
- ✅ 武侠水墨故事
- ✅ 赛博朋克故事
- ✅ 所有未来新故事
- ✅ 主Pipeline生成的条漫

**不需要任何额外工作，一次修复，永久受益**。

---

**@PM**
2026-02-03 12:30
