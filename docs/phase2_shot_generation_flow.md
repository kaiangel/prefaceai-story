# Phase 2.0 Shot 图片生成完整流程

> 本文档详细说明了 Phase 2.0 中每个 shot 图片生成的具体流程逻辑，包括每一步做了什么以及怎么做的。

## 流程概览图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Pipeline Orchestrator (调度层)                           │
│                     pipeline_orchestrator.py:273-352                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 1: 准备参考图                                                          │
│  ┌──────────────────────────┐   ┌──────────────────────────────────────┐   │
│  │ 角色参考图 (2张/角色)     │   │ 场景参考图 (1张/location)             │   │
│  │ ReferenceImageManager    │   │ SceneReferenceManager                │   │
│  │ - portrait + fullbody    │   │ - interior/exterior                  │   │
│  └──────────────────────────┘   └──────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 2: 构建 Prompt                                                        │
│  Phase2PromptBuilder (storyboard_prompts.py:991-1084)                       │
│                                                                             │
│  ┌────────────────────┐ ┌────────────────────┐ ┌─────────────────────────┐ │
│  │ critical_header    │ │ character_mapping  │ │ system_instruction      │ │
│  │ (角色一致性指令)    │ │ (角色-图像映射)     │ │ (全局风格锁定)           │ │
│  └────────────────────┘ └────────────────────┘ └─────────────────────────┘ │
│  ┌────────────────────┐ ┌────────────────────────────────────────────────┐ │
│  │ continuity_context │ │ image_prompt (场景描述)                        │ │
│  │ (连续性上下文)      │ │                                               │ │
│  └────────────────────┘ └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 3: 组装 Gemini 请求                                                    │
│  image_generator.py:398-412                                                 │
│                                                                             │
│  contents = [                                                               │
│      full_prompt,           # 文本 prompt                                   │
│      previous_shot_image,   # 上一张 shot (连续性)                          │
│      char_ref_1_portrait,   # 角色1肖像                                     │
│      char_ref_1_fullbody,   # 角色1全身                                     │
│      char_ref_2_portrait,   # 角色2肖像 (如有)                              │
│      char_ref_2_fullbody,   # 角色2全身 (如有)                              │
│      scene_ref,             # 场景参考图                                    │
│  ]                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 4: 调用 Gemini API                                                    │
│  image_generator.py:437-443                                                 │
│                                                                             │
│  model: gemini-3-pro-image-preview (始终使用 Pro 保证角色一致性)            │
│  config: response_modalities=["IMAGE"], aspect_ratio="16:9"                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 5: 保存结果                                                           │
│  pipeline_orchestrator.py:327-341                                           │
│                                                                             │
│  - 保存 PNG 到 images/shot_XX.png                                           │
│  - 更新 previous_shot_image (用于下一 shot 的连续性)                         │
│  - 记录到 reference_images_log.json                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 详细步骤说明

### Step 1: 准备参考图

**位置**: `pipeline_orchestrator.py:277-294`

```python
# 1.1 获取角色参考图
char_direction = shot.get("character_direction", {})
chars_in_scene = char_direction.get("characters_visible", [])  # 例如 ["char_001", "char_002"]
char_refs = ref_manager.get_references_for_scene(chars_in_scene)

# 1.2 获取场景参考图
location_id = self._get_location_id_for_scene(scene_id, screenplay, unique_locations)
scene_refs = scene_ref_manager.get_references_for_location(location_id)

# 1.3 合并
all_refs = char_refs + scene_refs
```

**角色参考图获取逻辑** (`reference_image_manager.py:470-489`):
- 遍历 `characters_visible` 中的角色 ID
- 每个角色返回 2 张图：`portrait` + `fullbody`
- 例如：3 人同框 → 6 张角色参考图

**场景参考图获取逻辑** (`scene_reference_manager.py`):
- 根据 `location_id` 查找已生成的场景锚点图
- 通常返回 1 张（interior 或 exterior）

---

### Step 2: 构建 Prompt

**位置**: `image_generator.py:338-380`, `storyboard_prompts.py:991-1084`

#### 2.1 初始化 Phase2PromptBuilder

```python
prompt_builder = Phase2PromptBuilder(
    storyboard=storyboard,       # 包含 global_visual_direction
    characters=characters,        # 完整角色数据
    style_preset=style_preset     # "realistic"
)
```

#### 2.2 构建 Prompt 包

```python
prompt_package = prompt_builder.build_full_prompt(
    shot=shot,
    previous_shot=previous_shot,
    include_system_instruction=True
)
```

返回 6 个组件：

| 组件 | 函数 | 作用 |
|------|------|------|
| `critical_header` | `build_critical_header_phase2()` | 角色一致性关键指令（FIXED vs FLEXIBLE 属性） |
| `character_mapping` | `build_character_reference_mapping_phase2()` | 角色-参考图映射（Image 1: 老陈 - 身份描述） |
| `system_instruction` | `build_system_instruction_phase2()` | 全局风格锁定（色调、光影、镜头风格） |
| `continuity_context` | `build_continuity_context_phase2()` | 与上一 shot 的连续性（人物位置、180度法则） |
| `image_prompt` | 从 `shot["image_prompt"]` 读取 | 场景具体描述 |
| `negative_prompt` | `build_negative_prompt()` | 负面提示词 |

#### 2.3 各组件详细内容

**critical_header** (角色一致性关键指令):
```
═══════════════════════════════════════════════════════════
CRITICAL INSTRUCTIONS FOR CHARACTER CONSISTENCY
═══════════════════════════════════════════════════════════

FIXED ATTRIBUTES (MUST match reference images EXACTLY - DO NOT ALTER):
- Facial features (face shape, eyes, nose, mouth, skin tone)
- Hair (color, style, length)
- Clothing (exact garments and colors as shown in reference)
- Accessories (glasses, watches, earrings exactly as shown)

FLEXIBLE ATTRIBUTES (may vary based on scene context):
- Expression (based on scene emotion)
- Pose (based on action description)
- Camera angle (based on shot direction)
═══════════════════════════════════════════════════════════
```

**character_mapping** (角色-参考图映射):
```
CHARACTER REFERENCE MAPPING:
- Image 1: Old Chen (老陈) - middle-aged East Asian man, rectangular face, pale skin,
  dark brown hooded eyes, jet black with silvering temples hair with short messy unbrushed,
  A classic silver-rimmed glasses, wrinkled white dress shirt...
- Image 2: Susu (苏苏) - young East Asian woman, heart face, fair skin,
  dark brown round eyes, chestnut brown hair with shoulder-length straight bangs...
```

**build_identity_line_phase2()** 构建每个角色的完整身份描述：
```python
parts = []
# 1. 年龄+种族+性别: "middle-aged East Asian man"
# 2. 面部特征: "rectangular face", "pale skin", "dark brown hooded eyes"
# 3. 完整发型: "jet black with silvering temples hair with short messy unbrushed"
# 4. 眼镜配饰: "A classic silver-rimmed glasses"
# 5. 服装: "wrinkled white dress shirt", "navy dress pants"
# 6. 其他配饰: "A worn leather briefcase", "A dripping black umbrella"
return ', '.join(parts)
```

**system_instruction** (全局风格锁定):
```
GLOBAL VISUAL DIRECTION FOR THIS STORY:

Style Enforcement: realistic_cinematic
Aspect Ratio: 16:9
Color Grade: Cold teal and blue tones contrasted with harsh neon red and orange highlights
Overall Lighting Approach: Low-key lighting, moody and atmospheric
Lens Style: 35mm

CRITICAL REQUIREMENTS:
1. MAINTAIN these visual parameters CONSISTENTLY across ALL shots
2. Every image must feel like it's from the SAME film/story
3. Color palette, lighting mood, and visual style must be cohesive
4. Character appearances must remain IDENTICAL across shots
```

---

### Step 3: 组装 Gemini 请求

**位置**: `image_generator.py:357-412`

#### 3.1 组装完整 Prompt 文本

```python
full_prompt_parts = []

# 顺序很重要！按teststory6.4验证的最佳结构
if critical_header:
    full_prompt_parts.append(critical_header)           # 1. 角色一致性指令（最前）
if character_mapping:
    full_prompt_parts.append(character_mapping)         # 2. 角色映射
if system_instruction:
    full_prompt_parts.append(f"[GLOBAL STYLE DIRECTIVE]\n{system_instruction}")  # 3. 风格锁定
if continuity_context:
    full_prompt_parts.append(f"[CONTINUITY]\n{continuity_context}")              # 4. 连续性
full_prompt_parts.append(f"[SCENE DESCRIPTION]\n{main_prompt}")                  # 5. 场景描述

full_prompt = "\n\n".join(full_prompt_parts)
```

#### 3.2 构建 Contents 列表

```python
contents = [full_prompt]  # 文本 prompt

# 添加上一 shot 图像（连续性参考）
if previous_shot_image:
    contents.append(previous_shot_image)

# 添加参考图（角色 + 场景）
if reference_images:
    for ref_img in reference_images[:13]:  # 最多 13 张
        contents.append(ref_img)
```

**最终 Contents 结构示例（3人同框 Shot 4）**:
```
contents = [
    "<完整 prompt 文本>",           # 约 2000-3000 字符
    <previous_shot_03.png>,        # 1344x768
    <char_001_portrait.png>,       # 1024x1024
    <char_001_fullbody.png>,       # 1024x1024
    <char_002_portrait.png>,       # 1024x1024
    <char_002_fullbody.png>,       # 1024x1024
    <char_003_portrait.png>,       # 1024x1024
    <char_003_fullbody.png>,       # 1024x1024
    <scene_bus_stop.png>,          # 1344x768
]
# total_refs = 7 (6 角色参考图 + 1 场景参考图)
```

---

### Step 4: 调用 Gemini API

**位置**: `image_generator.py:425-478`

```python
# 配置
config = types.GenerateContentConfig(
    response_modalities=["IMAGE"],
    image_config=types.ImageConfig(
        aspect_ratio="16:9",
    ),
)

# 调用 (始终使用 Pro 模型)
response = await self.client.aio.models.generate_content(
    model="gemini-3-pro-image-preview",  # Phase 2.0 强制使用 Pro
    contents=contents,
    config=config,
)

# 提取图像
for part in response.parts:
    if part.inline_data is not None:
        pil_image = Image.open(BytesIO(part.inline_data.data))
```

**为什么必须用 Pro 模型？**
- Flash 模型（gemini-2.5-flash-image）：生成速度快，成本低，但参考图理解能力弱
- Pro 模型（gemini-3-pro-image-preview）：**能真正"理解"参考图中的角色边界**，不会混淆特征
- 实测对比：3 人同框场景，Pro 100% 一致性 vs Flash 70-80%

---

### Step 5: 保存结果

**位置**: `pipeline_orchestrator.py:327-352`

```python
if result.get("success"):
    # 5.1 保存图像文件
    image_path = os.path.join(images_dir, f"shot_{shot_id:02d}.png")
    result["pil_image"].save(image_path)

    # 5.2 更新连续性参考（用于下一 shot）
    previous_shot_image = result["pil_image"]
    previous_shot = shot

    # 5.3 记录结果
    image_results.append({
        "shot_id": shot_id,
        "success": True,
        "image_path": image_path,
        "generation_time": result.get("generation_time_seconds", 0)
    })
```

---

## 完整数据流示例

以 **Shot 4（3人同框）** 为例：

```
输入数据:
├── shot (from storyboard)
│   ├── shot_id: 4
│   ├── scene_id: 2
│   ├── character_direction.characters_visible: ["char_001", "char_002", "char_003"]
│   ├── camera: {shot_size: "wide_shot", angle: "eye_level"}
│   └── image_prompt: "Three strangers at a rainy bus stop..."
│
├── characters (from Stage 2)
│   ├── char_001: {name: "老陈", physical: {...}, clothing: {...}}
│   ├── char_002: {name: "苏苏", physical: {...}, clothing: {...}}
│   └── char_003: {name: "阿强", physical: {...}, clothing: {...}}
│
└── reference_images (from Stage 5a)
    ├── char_001_portrait.png
    ├── char_001_fullbody.png
    ├── char_002_portrait.png
    ├── char_002_fullbody.png
    ├── char_003_portrait.png
    ├── char_003_fullbody.png
    └── scene_bus_stop.png

                    ↓ Pipeline Orchestrator 调度

处理步骤:
1. 准备参考图: char_refs(6张) + scene_refs(1张) = 7张
2. 构建 Prompt:
   - critical_header: FIXED vs FLEXIBLE 指令
   - character_mapping: Image 1=老陈, Image 2=苏苏, Image 3=阿强
   - system_instruction: 冷色调、低调照明、35mm镜头
   - image_prompt: 场景描述
3. 组装 contents: [prompt, prev_shot, 7张参考图]
4. 调用 Gemini Pro: gemini-3-pro-image-preview
5. 保存: shot_04.png

                    ↓

输出:
├── images/shot_04.png (1344x768, 3人同框，角色特征无混淆)
├── reference_images_log.json: {shot_id:4, total_refs:7}
└── 更新 previous_shot_image 供 Shot 5 使用
```

---

## 关键代码文件索引

| 文件 | 职责 | 关键函数/行号 |
|------|------|--------------|
| `pipeline_orchestrator.py` | 调度整个流程 | `run()`:273-352 |
| `image_generator.py` | 图像生成核心 | `generate_shot_image_phase2()`:299-478 |
| `storyboard_prompts.py` | Prompt 构建 | `Phase2PromptBuilder`:991-1084, `build_critical_header_phase2()`:732, `build_identity_line_phase2()`:756 |
| `reference_image_manager.py` | 角色参考图管理 | `get_references_for_scene()`:470-489 |
| `scene_reference_manager.py` | 场景参考图管理 | `get_references_for_location()` |

---

## 调试输出

每次运行会自动生成以下调试文件：

1. **`forclaudeweb/phase2_shot01_prompt.txt`** - Shot 1 的完整 prompt（用于验证结构）
2. **`reference_images_log.json`** - 每个 shot 使用的参考图统计
3. **控制台日志** - 实时显示每个 shot 的参考图数量和 Gemini 请求结构

---

*文档更新时间: 2025-12-30*
