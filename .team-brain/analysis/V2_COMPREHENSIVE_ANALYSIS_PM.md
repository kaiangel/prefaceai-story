# Kai与Cici V2 综合分析报告 - PM独立审查

**审查人**: @PM
**日期**: 2026-02-02
**审查范围**: `comic_cc_kai_story_v2` 全部41张图片（shot 28失败）
**补充分析**: `V2_SUPPLEMENTARY_ANALYSIS.md` (深入分析遗漏点)

---

## 执行摘要

V2测试相比V1有显著改进（AI空白气泡、留白、乱码文字问题基本解决），但仍存在**10+类新问题**。这些问题**不是个案**，而是**系统性问题**，需要从通用性角度解决。

| 问题类别 | 影响图片数 | 根因归属 | 优先级 | 状态 |
|---------|-----------|---------|--------|------|
| Speaker前缀未移除 | 15+ | Backend-TextOverlay | P0 | ✅ 已修复 |
| 气泡遮挡人脸 | 5+ | Backend-TextOverlay | P0 | ✅ 已修复 |
| 文字叠加重叠 | 4+ | Backend-TextOverlay | P1 | 待修复 |
| 人体解剖问题(手指/手腕) | 3+ | AI-ML-Prompt | P1 | 待修复 |
| 不必要边距 | 8+ | AI-ML-Prompt | P2 | 待修复 |
| 亲密度不合理 | 3 | PM-Story | P2 | 待修复 |
| **内容安全限制(Shot28)** | 1 | AI-ML-Prompt | **P1** | **已深入分析** |
| 服装不一致 | 1 | AI-ML-Prompt | P3 | 待修复 |
| 对话归属错误 | 1+ | PM-Data | P1 | 待修复 |
| **Shot34诡异手/身体** | 1 | AI-ML-Prompt | **P1** | **已深入分析** |
| **Shot19三气泡消失** | 1 | Backend-TextOverlay | **P1** | **已深入分析** |

---

## 一、图像生成问题（AI-ML负责）

### 1.1 人体解剖问题 [P1]

**现象**:
- Shot 01: 双手腕握手机，解剖结构异常
- Shot 03: 手指数量可能异常（疑似6指）
- Shot 34: 右下角出现奇怪的手/身体部分

**通用化分析**:
这是AI图像生成的已知局限性。当前prompt没有明确的解剖约束。

**通用化解决方案**:
```
在prompt中添加显式解剖约束:
"ANATOMY REQUIREMENT:
- All human figures must have anatomically correct body proportions
- Hands must have exactly 5 fingers per hand
- Arms must connect naturally to shoulders
- No duplicate limbs or body parts"
```

**验证方式**: 后处理检测（可用AI视觉模型检测手指数量异常）

---

### 1.2 不必要边距 [P2]

**现象**:
- Shot 05: 底部边距
- Shot 19: 顶部白色边距
- Shot 26, 32: 上下边距
- Shot 29, 34, 35, 38, 42: 可见边距

**通用化分析**:
当前`TEXT_FREE_REQUIREMENT`说"Fill the ENTIRE image"，但模型仍然生成边距。约束不够强。

**通用化解决方案**:
```
增强prompt约束:
"COMPOSITION REQUIREMENT:
- Edge-to-edge visual content - NO margins at any edge
- NO borders, NO blank areas at top/bottom/left/right
- Visual content must extend to the exact pixel boundaries
- Any visible margin area will FAIL validation"
```

---

### 1.3 内容安全限制 [P1] - Shot 28

**现象**:
- Scene: "牵手前奏"
- Error: "Content safety blocked: response.parts is None"
- 连续3次重试全部失败

**通用化分析**:
Gemini的内容安全过滤器对某些亲密场景敏感。需要:
1. 分析触发安全过滤的prompt元素
2. 准备替代措辞
3. 建立敏感场景的prompt模板库

**通用化解决方案**:
```python
# 敏感场景prompt改写策略
SENSITIVE_SCENE_ALTERNATIVES = {
    "hand_holding_prelude": [
        "两人并肩走路，手臂轻微靠近" -> "walking side by side, arms naturally close",
        "focus on upper body and facial expressions, hands not visible",
        "medium shot focusing on eye contact and subtle smiles"
    ]
}
```

---

### 1.4 服装不一致 [P3]

**现象**:
- Shot 21: Cici穿白色/米色上衣（应为黑色针织衫）

**通用化分析**:
即使有参考图，服装仍可能漂移。每个shot的prompt都需要包含完整服装描述。

**通用化解决方案**:
```
每个shot的prompt必须包含:
"CHARACTER CLOTHING (MANDATORY - DO NOT DEVIATE):
- [Character]: [exact clothing description from story]"
```

---

## 二、文字叠加问题（Backend负责）

### 2.1 Speaker前缀未移除 [P0] ⭐ 最高优先级

**现象**（几乎所有带对话的图）:
- Shot 03: "Kai：「好，周三傍晚6点」" - 显示了"Kai："
- Shot 04: "Kai内心：「这件毛衣...应该还行吧？」" - 显示了"Kai内心："
- Shot 06: "Kai内心：「还有五分钟...她会喜欢这里吗？」"
- Shot 12: "Kai：「你好，Cici。终于见到真人了。」", "Cici：「你好呀，Kai。」"
- Shot 16, 18, 19, 21, 23, 27, 31, 34, 40, 42... 全部有前缀

**通用化分析**:
TextOverlayServiceV2接收到的文本格式是`"Speaker：「内容」"`或`"Speaker内心：「内容」"`，但服务没有剥离speaker前缀。

**通用化解决方案**:
```python
def strip_speaker_prefix(text: str) -> str:
    """移除说话者前缀，保留引号内容"""
    import re
    # 匹配: "Kai：「内容」" 或 "Kai内心：「内容」"
    pattern = r'^[\w]+(?:内心)?[：:]\s*[「"]?(.+?)[」"]?$'
    match = re.match(pattern, text)
    if match:
        return f"「{match.group(1)}」"
    return text
```

**影响范围**: 所有故事的对话气泡渲染

---

### 2.2 气泡遮挡人脸 [P0] ⭐ 最高优先级

**现象**:
- Shot 12: 两个气泡都遮挡了角色脸部
- Shot 16: 气泡遮挡Kai的脸
- Shot 23: 气泡靠近脸部
- Shot 31: 两个气泡严重遮挡Kai的脸
- Shot 40: 气泡靠近脸部

**通用化分析**:
当前`speaker_position`逻辑使用固定位置:
- left: 5% from left edge
- right: 5% from right edge
- vertical: 12%/25%/40% from top

这没有考虑实际角色脸部位置。

**通用化解决方案**:

方案A - AI驱动的位置检测（推荐）:
```python
async def detect_safe_bubble_zone(image, characters_in_shot):
    """使用Haiku检测人脸位置，返回安全的气泡放置区域"""
    # 1. 检测角色位置
    positions = await detect_character_positions(image)

    # 2. 计算脸部区域（假设占角色边界框上1/4）
    face_zones = [get_face_zone(pos) for pos in positions]

    # 3. 返回不与脸部重叠的区域
    return find_non_overlapping_zones(image.size, face_zones)
```

方案B - 安全区域约束:
```python
SAFE_BUBBLE_ZONES = {
    "two_people_shot": {
        "left_speaker": {"x_range": (0.02, 0.35), "y_range": (0.05, 0.25)},
        "right_speaker": {"x_range": (0.65, 0.98), "y_range": (0.05, 0.25)}
    },
    "single_person_shot": {
        "center_speaker": {"x_range": (0.1, 0.9), "y_range": (0.02, 0.15)}
    }
}
```

---

### 2.3 文字叠加重叠 [P1]

**现象**:
- Shot 29: 文字与视觉效果重叠
- Shot 35, 38: 文字中出现方块伪影
- Shot 42: **两条底部旁白完全重叠**
  - "「那个冬夜，思南路的风很轻，两颗」"
  - "「这是他们的开始。」"

**通用化分析**:
1. 没有多文字元素的碰撞检测
2. 同区域多个叠加没有垂直堆叠

**通用化解决方案**:
```python
def detect_overlay_collision(existing_overlays, new_overlay):
    """检测新叠加是否与现有叠加冲突"""
    for existing in existing_overlays:
        if rectangles_overlap(existing.bounds, new_overlay.bounds):
            return True, existing
    return False, None

def stack_overlays_vertically(overlays_at_same_region):
    """将同区域的多个叠加垂直堆叠"""
    total_height = sum(o.height for o in overlays_at_same_region)
    # 计算起始Y位置，然后依次放置
```

---

### 2.4 对话归属错误 [P1]

**现象**:
- Shot 19: 两个气泡都标记为"Cici"，但一个应该是Kai的回答
  - "Cici：「你是做什么工作的？」" ✓ Cici提问
  - "Cici：「设计师，做品牌视觉的。」" ✗ 应该是Kai回答!

**通用化分析**:
这是上游数据错误。shot定义中的speaker归属有误。

**通用化解决方案**:
- PM层面: 对话归属的交叉校验
- 自动化: 对话逻辑校验（问答对中，回答者不应该是提问者）

---

## 三、故事内容问题（PM负责）

### 3.1 亲密度进展不合理 [P2]

**现象**:
- Shot 26, 27, 32: Cici挽着Kai的手臂
- 这是**初次约会**场景，挽手臂过于亲密

**通用化分析**:
关系阶段与肢体接触程度不匹配。需要建立关系阶段指南。

**通用化解决方案 - 关系阶段指南**:

| 关系阶段 | 允许的肢体接触 | 不允许的肢体接触 |
|---------|--------------|----------------|
| 初次见面 | 握手、轻微触碰 | 挽手、拥抱、亲吻 |
| 第1-2次约会 | 牵手（约会末尾） | 挽手、拥抱 |
| 第3-5次约会 | 牵手、挽手 | 亲密拥抱、亲吻 |
| 确认关系后 | 所有正常亲密接触 | - |

**Prompt层面修正**:
```
Shot 26/27/32 的prompt应改为:
"walking side by side with comfortable personal space between them"
而不是:
"woman linking arms with man"
```

---

## 四、系统性改进建议

### 4.1 测试流程改进

建议增加**自动化质量检查**:

```python
class ComicQualityChecker:
    """条漫质量自动检查器"""

    async def check_anatomy(self, image) -> List[Issue]:
        """检查人体解剖问题（手指数、肢体比例）"""

    async def check_margins(self, image) -> List[Issue]:
        """检查是否有不必要的边距"""

    def check_text_overlay_collision(self, overlays) -> List[Issue]:
        """检查文字叠加是否重叠"""

    def check_speaker_prefix(self, text) -> List[Issue]:
        """检查是否有未移除的speaker前缀"""

    def check_dialogue_attribution(self, dialogue_sequence) -> List[Issue]:
        """检查对话归属是否合理"""
```

### 4.2 TextOverlayServiceV3 设计

基于V2的问题，V3需要:

1. **Speaker前缀自动剥离**
2. **AI驱动的气泡位置** (避免遮挡人脸)
3. **多叠加碰撞检测** (防止重叠)
4. **叠加预览API** (生成前预览位置)

### 4.3 Prompt模板库

建立分类的prompt约束库:

```
prompt_constraints/
├── anatomy/           # 人体解剖约束
├── composition/       # 构图约束（无边距等）
├── safety_alternatives/  # 敏感场景替代措辞
└── clothing/          # 服装一致性约束
```

---

## 五、下一步行动

### 优先级排序

| 优先级 | 任务 | 负责人 | 预计影响 |
|-------|------|-------|---------|
| P0 | Speaker前缀剥离 | Backend | 修复15+张图 |
| P0 | 气泡位置优化（避免遮脸） | Backend | 修复5+张图 |
| P1 | 文字叠加碰撞检测 | Backend | 修复4+张图 |
| P1 | 解剖约束prompt | AI-ML | 预防3+类问题 |
| P1 | 内容安全替代prompt | AI-ML | 修复shot 28 |
| P2 | 边距约束prompt | AI-ML | 预防8+类问题 |
| P2 | 亲密度指南 | PM | 指导所有故事 |

### 建议的验收标准更新

在`COMIC_MVP_TEST_ACCEPTANCE_CRITERIA.md`中添加:

```markdown
## 新增验收项（V2+）

### 文字叠加质量
- [ ] 对话气泡不遮挡角色脸部
- [ ] 对话气泡不包含speaker前缀（如"Kai："）
- [ ] 多个文字叠加不互相重叠
- [ ] 文字渲染无伪影/方块

### 图像生成质量
- [ ] 人物手指数量正确（5指）
- [ ] 无不必要的边距/空白
- [ ] 服装与角色设定一致

### 故事内容合理性
- [ ] 亲密度与关系阶段匹配
- [ ] 对话归属正确
```

---

**@PM**
2026-02-02

*此报告从通用性角度分析问题，所有解决方案适用于任何故事，而非仅此测试用例。*
