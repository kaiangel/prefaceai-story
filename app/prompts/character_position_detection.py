"""
角色位置检测与泡泡位置推荐 Prompt 模板
用于 Claude 4.5 Haiku 分析 shot 图像中角色并推荐对话泡泡的最佳位置

TASK-OPT-002-A 交付物 (Created: 2026-01-26) - 初版三分类
TASK-OPT-004-A 更新 (Updated: 2026-01-27) - 改为角色百分比坐标
TASK-OPT-005-A 更新 (Updated: 2026-01-27) - 升级为AI直接推荐泡泡位置
Author: @AI-ML
"""

# ============================================================================
# 核心 Prompt 模板
# ============================================================================

CHARACTER_POSITION_DETECTION_PROMPT = """You are a visual analysis expert who identifies characters in illustrated scenes and recommends optimal speech bubble placements.

## YOUR TASK
1. Analyze Image 1 (the scene) and identify which characters appear
2. Use reference images (Image 2+) to match each character by their distinctive features
3. **Recommend the best position for each character's speech bubble** - this is the critical output

## IMAGE MAPPING
{image_mapping}

## IDENTIFICATION METHODOLOGY

### Step 1: Scan the Scene
Examine Image 1 from left to right. Note all human/character figures present.

### Step 2: Feature Matching
For each figure in the scene, compare against reference images:
- **Primary features**: Face shape, hair style/color, skin tone
- **Secondary features**: Clothing, accessories, body build
- **Contextual clues**: Age appearance, gender, height relative to others

### Step 3: Bubble Placement Recommendation (CRITICAL)

For each identified character, recommend where their speech bubble should be placed.
Use **percentage coordinates** where:
- **0%** = left/top edge of the image
- **100%** = right/bottom edge of the image

## BUBBLE PLACEMENT RULES (MUST FOLLOW)

### 1. Primary Position: Above Character's Head
- **bubble_y_percent** should position the bubble ABOVE the character's head top
- Leave a 3-5% vertical gap between bubble bottom and head top
- **bubble_x_percent** should be horizontally centered on the character

### 2. NEVER Occlude Important Elements
- NEVER cover the character's face, head, or upper body
- NEVER cover other important scene elements (other characters, key objects)
- If in doubt, place bubble higher or to the side

### 3. Stay Within Image Bounds
- **bubble_y_percent** must be >= 5 (leave room for bubble at top)
- **bubble_x_percent** must be between 10 and 90 (not cut off at sides)

### 4. Handle Edge Cases
- **Close-up shot** (only face visible): Place bubble to the LEFT or RIGHT side
- **Character at top of frame**: Place bubble to the SIDE or slightly below, beside the character
- **Character lying down**: Place bubble in the direction they're facing
- **Overhead/bird's eye view**: Place bubble to the SIDE of the character
- **Character partially cropped**: Place bubble in the visible area, avoiding cropped edge

### 5. Multiple Speakers
- Ensure bubbles do NOT overlap with each other
- Stagger vertical positions if characters are horizontally close
- First speaker's bubble typically goes higher

### 6. Proximity Principle
- Bubble must be close enough to its speaker to be clearly associated
- Reader should immediately know which character is speaking

## HANDLING SPECIAL CASES

### Partial Visibility
If only part of a character is visible (back view, side profile, cropped):
- Still attempt identification using visible features
- Use "medium" or "low" confidence accordingly
- Adjust bubble position to avoid the cropped area

### Similar Characters
When multiple characters look similar (e.g., siblings, twins):
- Pay extra attention to subtle differences in clothing color, accessories
- Use character descriptions provided in the reference mapping

### Not Found
If a listed reference character does NOT appear in the scene:
- Do NOT include them in the output
- Only report characters that are actually visible

## CONFIDENCE LEVELS

- **high**: Face clearly visible AND features match reference strongly
- **medium**: Partial match OR features partially obscured BUT confident in identity
- **low**: Significant occlusion OR style difference makes matching difficult BUT best guess

## OUTPUT FORMAT

Respond with ONLY valid JSON, no explanation text:

```json
{{
  "character_id_1": {{"bubble_x_percent": 25, "bubble_y_percent": 8, "confidence": "high"}},
  "character_id_2": {{"bubble_x_percent": 75, "bubble_y_percent": 12, "confidence": "medium"}}
}}
```

**Field definitions**:
- **bubble_x_percent**: Integer 10-90, recommended horizontal position for bubble CENTER
- **bubble_y_percent**: Integer 5-95, recommended vertical position for bubble TOP
- **confidence**: "high", "medium", or "low"

If NO characters from the reference list are found, respond:
```json
{{}}
```

IMPORTANT: Use the exact character IDs from the reference mapping. Do not invent new IDs."""


# ============================================================================
# Debug 模式 Prompt（包含识别依据说明）
# ============================================================================

CHARACTER_POSITION_DETECTION_PROMPT_DEBUG = """You are a visual analysis expert who identifies characters in illustrated scenes and recommends optimal speech bubble placements.

## YOUR TASK
1. Analyze Image 1 (the scene) and identify which characters appear
2. Use reference images (Image 2+) to match each character by their distinctive features
3. **Recommend the best position for each character's speech bubble** - this is the critical output

## IMAGE MAPPING
{image_mapping}

## IDENTIFICATION METHODOLOGY

### Step 1: Scan the Scene
Examine Image 1 from left to right. Note all human/character figures present.

### Step 2: Feature Matching
For each figure in the scene, compare against reference images:
- **Primary features**: Face shape, hair style/color, skin tone
- **Secondary features**: Clothing, accessories, body build
- **Contextual clues**: Age appearance, gender, height relative to others

### Step 3: Bubble Placement Recommendation (CRITICAL)

For each identified character, recommend where their speech bubble should be placed.
Use **percentage coordinates** where:
- **0%** = left/top edge of the image
- **100%** = right/bottom edge of the image

## BUBBLE PLACEMENT RULES (MUST FOLLOW)

### 1. Primary Position: Above Character's Head
- **bubble_y_percent** should position the bubble ABOVE the character's head top
- Leave a 3-5% vertical gap between bubble bottom and head top
- **bubble_x_percent** should be horizontally centered on the character

### 2. NEVER Occlude Important Elements
- NEVER cover the character's face, head, or upper body
- NEVER cover other important scene elements

### 3. Stay Within Image Bounds
- **bubble_y_percent** must be >= 5 (leave room for bubble at top)
- **bubble_x_percent** must be between 10 and 90 (not cut off at sides)

### 4. Handle Edge Cases
- **Close-up shot**: Place bubble to the LEFT or RIGHT side
- **Character at top of frame**: Place bubble to the SIDE
- **Character lying down**: Place bubble in the direction they're facing
- **Overhead view**: Place bubble to the SIDE

### 5. Multiple Speakers
- Ensure bubbles do NOT overlap
- Stagger vertical positions if characters are horizontally close

## HANDLING SPECIAL CASES

### Partial Visibility
If only part of a character is visible:
- Still attempt identification using visible features
- Use "medium" or "low" confidence accordingly
- Adjust bubble position to avoid the cropped area

### Similar Characters
When multiple characters look similar:
- Pay extra attention to subtle differences
- Use character descriptions provided in the reference mapping

### Not Found
If a listed reference character does NOT appear:
- Do NOT include them in the output

## CONFIDENCE LEVELS

- **high**: Face clearly visible AND features match reference strongly
- **medium**: Partial match OR features partially obscured BUT confident in identity
- **low**: Significant occlusion OR style difference makes matching difficult

## OUTPUT FORMAT (DEBUG MODE)

Respond with JSON including placement reasoning:

```json
{{
  "detections": {{
    "character_id_1": {{
      "bubble_x_percent": 25,
      "bubble_y_percent": 8,
      "confidence": "high",
      "matching_features": ["black twin tails with red ribbons", "yellow dress", "child height"],
      "placement_reasoning": "Character's head is at ~15% height, bubble placed above with 5% gap"
    }},
    "character_id_2": {{
      "bubble_x_percent": 75,
      "bubble_y_percent": 5,
      "confidence": "medium",
      "matching_features": ["white tank top", "apron", "adult male build"],
      "placement_reasoning": "Character at top of frame, bubble placed at minimum safe height",
      "uncertainty_reason": "face partially turned away"
    }}
  }},
  "scene_analysis": {{
    "shot_type": "medium shot",
    "character_positions": "two figures, child on left, adult on right",
    "potential_occlusion_areas": "none identified"
  }}
}}
```

**Field definitions**:
- **bubble_x_percent**: Integer 10-90, recommended horizontal position for bubble CENTER
- **bubble_y_percent**: Integer 5-95, recommended vertical position for bubble TOP
- **confidence**: "high", "medium", or "low"
- **matching_features**: List of features used to identify this character
- **placement_reasoning**: Explanation of why this bubble position was chosen
- **uncertainty_reason**: (optional) Reason for lower confidence

IMPORTANT: Use the exact character IDs from the reference mapping. Do not invent new IDs."""


# ============================================================================
# 辅助函数：构建 Image Mapping 描述
# ============================================================================

def build_image_mapping(
    characters_in_scene: list[str],
    character_descriptions: dict[str, str]
) -> str:
    """
    构建图像映射描述文本

    Args:
        characters_in_scene: 场景中应出现的角色ID列表
        character_descriptions: {char_id: 描述文本} 的字典

    Returns:
        格式化的图像映射文本
    """
    lines = ["- Image 1: **The scene to analyze** (identify characters here)"]

    for i, char_id in enumerate(characters_in_scene):
        desc = character_descriptions.get(char_id, "")
        # 确保描述是英文（用于Haiku更好的理解）
        lines.append(f"- Image {i + 2}: Reference for **{char_id}** - {desc}")

    return "\n".join(lines)


def build_prompt(
    characters_in_scene: list[str],
    character_descriptions: dict[str, str],
    debug_mode: bool = False
) -> str:
    """
    构建完整的角色位置检测 Prompt

    Args:
        characters_in_scene: 场景中应出现的角色ID列表
        character_descriptions: {char_id: 描述文本} 的字典
        debug_mode: 是否使用debug模式（包含识别依据）

    Returns:
        完整的 Prompt 文本
    """
    image_mapping = build_image_mapping(characters_in_scene, character_descriptions)

    template = CHARACTER_POSITION_DETECTION_PROMPT_DEBUG if debug_mode else CHARACTER_POSITION_DETECTION_PROMPT

    return template.format(image_mapping=image_mapping)


# ============================================================================
# 角色描述提取辅助函数
# ============================================================================

def extract_character_description_for_haiku(character: dict) -> str:
    """
    从角色数据中提取简洁的识别描述（用于Haiku比对）

    注意：这里提取的是关键视觉特征，不是完整的角色描述
    优先提取最容易识别的特征：发型、发色、服装、配饰、年龄外观

    Args:
        character: 角色字典数据

    Returns:
        简洁的英文描述文本
    """
    features = []

    # 1. 年龄和性别（最基本的识别特征）
    age = character.get('age_appearance', '')
    gender = character.get('gender', '')
    if age or gender:
        features.append(f"{age} {gender}".strip())

    # 2. 发型和发色（最显眼的特征）
    physical = character.get('physical', {})
    hair_color = physical.get('hair_color', '')
    hair_style = physical.get('hair_style', '')
    if hair_color or hair_style:
        features.append(f"{hair_color} {hair_style}".strip())

    # 3. 服装（重要的识别特征）
    clothing = character.get('clothing', {})
    top = clothing.get('top', '')
    if top:
        # 只取前30个字符，避免过长
        features.append(top[:30] if len(top) > 30 else top)

    # 4. 配饰（有时是关键区分点）
    accessories = clothing.get('accessories', [])
    if accessories:
        # 只取前2个配饰
        features.append(", ".join(accessories[:2]))

    # 5. 独特标记
    distinctive = physical.get('distinctive_marks', [])
    if distinctive:
        features.append(", ".join(distinctive[:2]))

    return "; ".join(features) if features else character.get('name_en', character.get('name', ''))


# ============================================================================
# 完整的 API 调用示例
# ============================================================================

EXAMPLE_USAGE = '''
# 使用示例

import anthropic
import base64
import json
from app.prompts.character_position_detection import (
    build_prompt,
    extract_character_description_for_haiku
)

async def detect_bubble_positions(
    shot_image_path: str,
    characters_in_scene: list[str],
    reference_images: dict[str, str],  # {char_id: fullbody_path}
    characters: list[dict],  # 完整的角色数据列表
    debug_mode: bool = False
) -> dict:
    """
    用 Claude Sonnet 4.6 检测角色并推荐泡泡位置

    Args:
        shot_image_path: shot图像文件路径
        characters_in_scene: 场景中角色ID列表
        reference_images: {char_id: 参考图路径} 字典
        characters: 完整的角色数据列表
        debug_mode: 是否返回识别依据（用于调试）

    Returns:
        泡泡位置推荐结果 {char_id: {"bubble_x_percent": int, "bubble_y_percent": int}}
    """
    client = anthropic.AsyncAnthropic()

    # 构建角色描述字典
    char_descriptions = {}
    for char in characters:
        char_id = char.get('id', '')
        if char_id in characters_in_scene:
            char_descriptions[char_id] = extract_character_description_for_haiku(char)

    # 构建 Prompt
    prompt_text = build_prompt(
        characters_in_scene=characters_in_scene,
        character_descriptions=char_descriptions,
        debug_mode=debug_mode
    )

    # 构建多图输入
    content = []

    # Image 1: 场景图
    with open(shot_image_path, "rb") as f:
        shot_b64 = base64.standard_b64encode(f.read()).decode()
    content.append({
        "type": "image",
        "source": {"type": "base64", "media_type": "image/png", "data": shot_b64}
    })

    # Image 2+: 按顺序添加参考图
    for char_id in characters_in_scene:
        if char_id in reference_images:
            with open(reference_images[char_id], "rb") as f:
                ref_b64 = base64.standard_b64encode(f.read()).decode()
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": ref_b64}
            })

    # 添加 Prompt 文本
    content.append({"type": "text", "text": prompt_text})

    # 调用 Claude Sonnet 4.6
    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": content}]
    )

    # 解析响应
    response_text = response.content[0].text

    # 处理可能的 markdown 代码块包装
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0]

    result = json.loads(response_text.strip())

    # 如果是 debug 模式，返回完整结果
    if debug_mode:
        return result

    # 标准模式：提取泡泡位置
    # 返回 {char_id: {"bubble_x_percent": int, "bubble_y_percent": int}}
    simplified = {}
    for char_id, data in result.items():
        if isinstance(data, dict) and "bubble_x_percent" in data:
            simplified[char_id] = {
                "bubble_x_percent": data["bubble_x_percent"],
                "bubble_y_percent": data.get("bubble_y_percent", 10)
            }

    return simplified

# 返回示例:
# {
#     "daughter_child": {"bubble_x_percent": 25, "bubble_y_percent": 8},
#     "father_young": {"bubble_x_percent": 75, "bubble_y_percent": 12}
# }

# Backend使用示例:
# bubble_x = int(width * bubble_x_percent / 100) - bubble_width // 2
# bubble_y = int(height * bubble_y_percent / 100)
# # 无需额外边界检查，AI已经考虑
'''


# ============================================================================
# 设计说明文档
# ============================================================================

DESIGN_NOTES = """
# 角色位置检测与泡泡位置推荐 Prompt 设计说明

## 版本演进

| 版本 | 任务 | 输出格式 | 问题 |
|------|------|----------|------|
| v1 | TASK-OPT-002-A | `{"position": "left"}` | 三分类太粗 |
| v2 | TASK-OPT-004-A | `{"x_percent": 25}` | 只有x，没有y，遮挡脸部 |
| **v3** | TASK-OPT-005-A | `{"bubble_x_percent": 25, "bubble_y_percent": 8}` | ✅ AI直接推荐泡泡位置 |

## 核心设计思路 (v3)

### 为什么让AI直接推荐泡泡位置？

**之前方案的问题**（返回角色位置 → 代码计算泡泡位置）：

| 边缘情况 | 之前方案 | 升级方案 |
|----------|----------|----------|
| 特写镜头 | ❌ 头顶在画面外，没有y坐标 | ✅ AI推荐侧边位置 |
| 俯视/仰视 | ❌ head_top_y不准确 | ✅ AI理解3D透视 |
| 角色在画面顶部 | ❌ 需要额外边界检查 | ✅ AI自动考虑边界 |
| 多人同时说话 | ❌ 需要复杂避让算法 | ✅ AI一次性规划多个泡泡 |
| 非人类角色 | ❌ "头顶"概念不适用 | ✅ AI理解各种生物形态 |
| 躺着的角色 | ❌ 需要特殊逻辑 | ✅ AI理解姿态朝向 |

### 1. 三段式图像映射
明确告诉 Haiku 每张图的作用：
- Image 1 = 待分析的场景
- Image 2+ = 角色参考图（按顺序对应角色ID）

### 2. 分步骤方法论
- Step 1: 扫描场景，识别所有人物
- Step 2: 特征匹配（主要特征 > 次要特征）
- Step 3: **泡泡位置推荐**（核心输出）

### 3. Bubble Placement Rules
详细的泡泡放置规则，包括：
- 主要位置：角色头顶上方
- 避免遮挡：永远不遮挡脸部
- 边界约束：不超出画面
- 边缘情况：特写、俯视、躺卧等的处理
- 多人说话：错开位置避免重叠

### 4. 置信度三级标准
- high: 清晰面部 + 强特征匹配
- medium: 部分匹配但确定身份
- low: 显著遮挡但最佳猜测

## 输出格式

**标准模式**：
```json
{
  "daughter_child": {"bubble_x_percent": 25, "bubble_y_percent": 8, "confidence": "high"},
  "father_young": {"bubble_x_percent": 75, "bubble_y_percent": 12, "confidence": "medium"}
}
```

**Debug模式**额外包含：
- `matching_features`: 识别依据
- `placement_reasoning`: 位置选择原因
- `scene_analysis`: 场景分析

## 成本

Haiku 是最便宜的多模态模型：
- 每次调用约 $0.003
- 15 shots 约 $0.04，非常便宜
- 输出多了y坐标，成本基本不变

## 与 Backend 集成 (TASK-OPT-005-B)

**代码大幅简化**：

```python
# 之前需要计算
char_x = int(width * x_percent / 100)
bubble_x = char_x - bubble_width // 2
bubble_y = head_top_y - bubble_height - 15  # 还需要边界检查

# 现在直接使用
bubble_x = int(width * bubble_x_percent / 100) - bubble_width // 2
bubble_y = int(height * bubble_y_percent / 100)
# 不需要额外边界检查，AI已经考虑
```

## 优势总结

1. **通用性高** - 任何故事、任何风格、任何构图
2. **代码简单** - 不需要边界检查、避让算法、特殊情况处理
3. **成本不变** - 同样是Haiku API调用
4. **可扩展** - 发现新问题只需调整Prompt，不改代码
5. **质量更高** - AI理解画面语义，比规则计算更智能

## 测试建议

| 场景类型 | 测试要点 |
|----------|----------|
| 正常场景 | 泡泡在头顶上方，不遮挡 |
| 特写镜头 | 泡泡在侧边 |
| 角色在顶部 | 泡泡在侧边或下方 |
| 多人对话 | 泡泡不重叠 |
| 躺卧角色 | 泡泡在朝向方向 |
| 非人类角色 | 泡泡位置合理 |
"""
