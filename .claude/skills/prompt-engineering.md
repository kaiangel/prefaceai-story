# Skill: Prompt Engineering

> 图像生成Prompt的工程规范。Gemini对英文理解更准确。

## Activation Triggers

当涉及以下内容时，必须阅读此skill：
- 修改 `storyboard_prompts.py`
- 修改 `storyboard_director.py`
- 讨论"image_prompt"、"中文泄露"、"风格描述"

**大白话触发**: 中文泄露到图里了、图片上有乱码、风格跑偏了、画风不统一

**完整触发词映射**: [XUHUASTORY_SKILL_TRIGGERS.md](./XUHUASTORY_SKILL_TRIGGERS.md)

---

## Core Rules

### 1. 图像生成Prompt必须全英文

```python
# 正确
image_prompt = "A young woman with black bob hair, wearing gray blazer..."

# 错误 - 中文会泄露到图像里!
image_prompt = "一位年轻女性，黑色短发..."
```

### 2. 允许的中文例外

以下中文词汇英文翻译会丢失视觉特征，可以保留：

| 类型 | 示例 | 原因 |
|------|------|------|
| 中国人名 | Chen Mo (陈默) | 名字需要中文辅助 |
| 中国地名 | 胡同、弄堂、祠堂 | "alley"无法传达视觉 |
| 传统服饰 | 汉服、旗袍、马褂 | 无准确英文对应 |
| 建筑元素 | 飞檐、斗拱、影壁 | 无准确英文对应 |
| 书法/文字 | 春联、牌匾、印章 | 画面中需要显示中文 |

### 3. narration保留中文

```json
{
  "image_prompt": "English only...",
  "narration_segment": "保留中文，用于TTS"
}
```

---

## Style Enforcement

### 风格描述必须在开头

StyleEnforcer在prompt开头注入强制风格：

```
═══════════════════════════════════════════════════════════
MANDATORY STYLE REQUIREMENT - DO NOT IGNORE THIS SECTION
═══════════════════════════════════════════════════════════

STYLE: Photorealistic

MUST INCLUDE: photorealistic, photograph, natural lighting...
DO NOT USE: cartoon, anime, illustration, 3D render...

═══════════════════════════════════════════════════════════

[actual image description follows...]
```

### 禁止在末尾加风格

```python
# 错误 - 风格漂移
prompt = f"{description}, realistic style"

# 正确 - 使用StyleEnforcer
prompt = style_enforcer.enforce_prompt(description, style_config)
```

---

## Shot Type & Camera Angle

必须使用英文，通过翻译函数：

```python
shot_type = _translate_shot_type(shot.shot_type)   # "中景" → "medium shot"
camera_angle = _translate_camera_angle(shot.camera_angle)  # "平视" → "eye level"
```

---

## IMAGE编号映射

Prompt中的Image N必须与contents数组对应：

```
has_previous_shot=True, scene_ref_count=2:

Image 1 = previous_shot_image
Image 2 = character_ref_1
Image 3 = character_ref_2
Image 4 = scene_ref_1
Image 5 = scene_ref_2
```

关键代码位置：
- `storyboard_prompts.py:1481-1530` - IMAGE编号映射

---

## VISUAL CONTINUITY REFERENCE

Shot 2+ 需要添加连续性指令：

```
═══════════════════════════════════════════════════════════
VISUAL CONTINUITY REFERENCE
═══════════════════════════════════════════════════════════

Image 1 shows the previous shot from this scene.

MUST MAINTAIN from Image 1:
- Same lighting conditions
- Same weather/time of day
- Same architectural details

MUST VARY from Image 1:
- Different camera angle
- Different character positions
- Fresh composition

═══════════════════════════════════════════════════════════
```

---

## Common Pitfalls

| 问题 | 错误做法 | 正确做法 |
|------|----------|----------|
| 中文泄露 | Stage 1/3输出中文mood | 修改LLM模板要求英文 |
| IMAGE编号错乱 | 固定编号 | 根据has_previous_shot计算 |
| 风格漂移 | 末尾加风格 | StyleEnforcer开头注入 |
| 构图复制 | 只传前序图无指令 | 添加CONTINUITY指令块 |
