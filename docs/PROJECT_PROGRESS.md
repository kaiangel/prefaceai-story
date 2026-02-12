# 序话Story - 项目完整进展文档

> 最后更新: 2025-12-19
> 版本: P2.0 (unique_locations架构)

---

## 一、项目概述

### 1.1 产品定位
**序话Story** 是一个面向大众创作者的AI多媒体内容生成工具，将用户的一句话创意转化为完整的短视频/漫剧/故事。

**核心价值**: 通用性
- 支持任何类型的故事（都市情感、古装武侠、童话寓言、科幻冒险）
- 支持任何类型的角色（人类、动物、奇幻生物、机器人）
- 支持任何视觉风格（写实、卡通、水墨、赛博朋克）

**用户画像**: 无技术背景的短视频创作者、自媒体运营者、内容营销团队

**核心体验**: 输入idea → 自动生成可发布的成片

### 1.2 技术栈
| 类别 | 技术选型 |
|------|----------|
| 后端框架 | FastAPI + Python 3.11 |
| LLM (故事生成) | Claude Haiku (主) / Gemini 2.5 Flash (备) |
| LLM (分镜) | Gemini 2.5 Flash |
| 图像生成 | Gemini 2.5 Flash Image / Gemini 3 Pro Image Preview |
| TTS | 火山引擎 Doubao |
| 语音识别 | OpenAI Whisper |
| 数据库 | SQLite (开发) / PostgreSQL (生产) |

---

## 二、系统架构

### 2.1 完整数据流

```
用户输入 (idea: "深夜便利店，三个失眠的陌生人")
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  StoryGenerator.generate_story()                                 │
│  - 调用 Claude Haiku (主) / Gemini (备)                          │
│  - 输出: story.json                                              │
│    ├── characters[] (角色详细描述)                               │
│    ├── unique_locations[] (结构化场景位置) ← P2.0新增           │
│    ├── scenes[] (场景列表)                                       │
│    └── visual_style (全局视觉风格)                               │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  StoryboardService.generate_storyboard_with_splitting()          │
│  - 检测 narration 长度 (阈值: 60字)                              │
│  - >60字: LLM拆分为多个shots                                     │
│  - ≤60字: 直接转换为单个shot                                     │
│  - 输出: shots.json                                              │
│    ├── shot_id                                                   │
│    ├── image_prompt (全英文)                                     │
│    ├── narration_segment (中文)                                  │
│    ├── characters_in_scene[]                                     │
│    └── shot_type, camera_angle                                   │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  ReferenceImageManager.generate_character_multi_refs()           │
│  - 串行生成: 肖像 → 用肖像作参考生成全身图                       │
│  - 确保同一角色面部一致                                          │
│  - 输出: character_refs/                                         │
│    ├── {char_id}_portrait.png                                    │
│    └── {char_id}_fullbody.png                                    │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  SceneReferenceManager.generate_anchor_images()                  │
│  - P2.0: 使用 unique_locations 结构化数据                        │
│  - 每个location生成 interior/exterior 锚点图                     │
│  - 输出: scene_refs/                                             │
│    ├── {location_id}_interior.png                                │
│    └── {location_id}_exterior.png                                │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  TTSService.synthesize() → 火山引擎 Doubao                       │
│  - 输出: narration.mp3                                           │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  WhisperService.transcribe_with_timestamps()                     │
│  - OpenAI Whisper API                                            │
│  - 提取 word-level 时间戳                                        │
│  - 输出: whisper.json                                            │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  AlignmentService.align_shots_to_audio()                         │
│  - 多策略匹配: 精确 → 去标点 → 前缀 → 子序列                     │
│  - 繁简转换处理                                                  │
│  - 输出: timeline.json                                           │
│    ├── shot_id                                                   │
│    ├── start_time, end_time, duration                            │
│    └── image_path                                                │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  ImageGenerator.generate_shot_image()                            │
│  - 传入参考图: char_refs + scene_refs                            │
│  - StyleEnforcer 强制风格前缀                                    │
│  - 输出: images/shot_{id}.png                                    │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  视频合成 (外部处理)                                             │
│  - 按 timeline.json 组装图片+音频                                │
│  - 输出: final.mp4                                               │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心服务清单

| 服务 | 文件 | 职责 | 外部API |
|------|------|------|---------|
| **StoryGenerator** | `story_generator.py` | 故事生成 | Claude/Gemini |
| **StoryboardService** | `storyboard_service.py` | 分镜决策、shot拆分、image_prompt构建 | Gemini |
| **ImageGenerator** | `image_generator.py` | 图像生成 | Gemini Image |
| **ReferenceImageManager** | `reference_image_manager.py` | 角色参考图管理 | ImageGenerator |
| **SceneReferenceManager** | `scene_reference_manager.py` | 场景参考图管理 | ImageGenerator |
| **TTSService** | `tts_service.py` | 文字转语音 | 火山引擎 |
| **WhisperService** | `whisper_service.py` | 语音识别+时间戳 | OpenAI |
| **AlignmentService** | `alignment_service.py` | 音画对齐 | - |
| **StyleEnforcer** | `style_enforcer.py` | 风格强制锁定 | - |
| **CharacterPromptBuilder** | `character_prompt_builder.py` | 角色描述构建 | - |
| **ShotPromptGenerator** | `shot_prompt_generator.py` | Shot定制化prompt生成 | Gemini |

---

## 三、核心数据结构

### 3.1 story.json

```json
{
  "title": "凌晨便利店",
  "synopsis": "三个失眠的陌生人在便利店相遇...",
  "summary": "本章摘要，用于续集参考",

  "visual_style": {
    "art_style": "illustration",
    "rendering": "soft",
    "color_palette": "warm",
    "primary_colors": ["golden", "cream"],
    "lighting": "soft natural",
    "atmosphere": "warm and cozy"
  },

  "unique_locations": [
    {
      "location_id": "convenience_store_24h",
      "display_name": "24小时便利店",
      "location_type": "both",
      "interior_description": "Typical Asian 24-hour convenience store interior, bright fluorescent lighting...",
      "exterior_description": "Modern convenience store exterior at night, illuminated storefront...",
      "key_visual_elements": ["fluorescent lights", "glass refrigerators", "tile floor"]
    }
  ],

  "characters": [
    {
      "id": "char_001",
      "name": "陈默",
      "name_en": "Chen Mo",
      "character_type": "human",
      "gender": "female",
      "physical": {
        "hair_color": "jet black",
        "hair_style": "high ponytail with wispy bangs",
        "eye_color": "deep brown",
        "skin_tone": "fair with slight pallor",
        "face_shape": "oval"
      },
      "clothing": {
        "top": "pink nursing jacket over white t-shirt",
        "bottom": "light blue skinny jeans",
        "accessories": ["silver minimalist watch", "black ballpoint pen in pocket"],
        "style": "practical medical casual"
      }
    }
  ],

  "scenes": [
    {
      "scene_id": 1,
      "story_phase": "opening",
      "location_ref": "convenience_store_24h",
      "location_type_used": "interior",
      "time": "2:00 AM",
      "mood": "lonely and isolating",
      "scene_style": {
        "color_palette": "cool",
        "lighting": "harsh fluorescent",
        "atmosphere": "desolate"
      },
      "characters_in_scene": ["char_001"],
      "visual_description": "An empty convenience store at 2 AM...",
      "narration": "凌晨两点的便利店，只有冰箱嗡嗡的运转声..."
    }
  ]
}
```

### 3.2 shots.json

```json
[
  {
    "shot_id": 1,
    "original_scene_id": 1,
    "image_prompt": "CHARACTERS IN THIS SHOT (MUST MATCH EXACTLY): Chen Mo: jet black high ponytail with wispy bangs, deep brown eyes, fair skin, wearing pink nursing jacket... Scene: An empty convenience store at 2 AM... Shot type: wide shot. Camera angle: eye level.",
    "narration_segment": "凌晨两点的便利店，只有冰箱嗡嗡的运转声...",
    "shot_type": "wide shot",
    "camera_angle": "eye level",
    "characters_in_scene": ["char_001"],
    "duration_hint": 8.5
  }
]
```

### 3.3 timeline.json

```json
[
  {
    "shot_id": 1,
    "original_scene_id": 1,
    "image_path": "images/shot_01.png",
    "start_time": 0.0,
    "end_time": 8.5,
    "duration": 8.5,
    "narration_segment": "凌晨两点的便利店..."
  }
]
```

---

## 四、关键Prompt模板

### 4.1 故事生成Prompt (story_generation.py)

```python
LOCATION_FORMAT_TEMPLATE = """
### 场景位置格式说明（unique_locations）

在生成故事前，先分析故事中出现的所有独特场景位置，输出到 `unique_locations` 数组。

**每个独特场景包含：**
- `location_id`: 唯一标识符（英文+下划线，如 "xiaoming_apartment"）
- `display_name`: 场景的显示名称（中文）
- `location_type`: "interior_only" | "exterior_only" | "both"
- `interior_description`: 室内视觉描述（英文）
- `exterior_description`: 室外视觉描述（英文）
- `key_visual_elements`: 关键视觉元素列表

**重要规则：**
1. 同一栋建筑的不同区域属于同一个location
2. 不同人物的家是不同的location（"小明家"和"小红家"需分开）
3. 描述必须是英文，便于图像生成
"""

CHARACTER_DETAIL_TEMPLATE = """
### 角色描述格式说明

**人类角色需要包含：**
- physical: hair_color, hair_style, eye_color, eye_shape, skin_tone, face_shape
- clothing: top, bottom, footwear, accessories, style

**动物角色需要包含：**
- animal: species, breed, fur_color, fur_pattern, eye_color, tail
"""
```

### 4.2 角色参考图Prompt (reference_image_manager.py)

```python
# 肖像参考图prompt
CLOSE-UP PORTRAIT - CHARACTER REFERENCE

═══════════════════════════════════════════════════════════
CRITICAL FACIAL FEATURES - MUST MATCH EXACTLY
═══════════════════════════════════════════════════════════
{face_desc}

These facial features are UNIQUE to this character and MUST be rendered precisely.
DO NOT use generic/default Asian beauty face template.
═══════════════════════════════════════════════════════════

{char_desc}

COMPOSITION:
- Front-facing portrait view, eye-level camera angle
- Head and shoulders framing
- Simple solid neutral background
- Soft studio lighting, no harsh shadows

FACE RENDERING REQUIREMENTS:
- Face shape: Render the EXACT face shape specified above
- Eyes: Match the EXACT eye shape, size, and color described
- Nose: Follow the SPECIFIC nose description
- Lips: Match the lip fullness and shape exactly
- Eyebrows: Render according to description

IMPORTANT: This is the MASTER REFERENCE for this character's face.
All subsequent images of this character must match this exact face.
```

### 4.3 风格强制前缀 (style_enforcer.py)

```
═══════════════════════════════════════════════════════════
MANDATORY STYLE REQUIREMENT - DO NOT IGNORE THIS SECTION
═══════════════════════════════════════════════════════════

STYLE: {style_display_name}

{style_description}

MUST INCLUDE: {mandatory_keywords}

DO NOT USE: {forbidden_keywords}

This style requirement applies to ALL elements in this image.
═══════════════════════════════════════════════════════════
```

### 4.4 Shot图像Prompt结构 (storyboard_service.py)

```
CHARACTERS IN THIS SHOT (MUST MATCH EXACTLY):
{char_name}: {physical_desc}, {clothing_desc};
...

Scene: {cleaned_visual_description}

Shot type: {shot_type}.
Camera angle: {camera_angle}.
Focus on: {focus}.

Scene style: {color_palette}, {lighting}, {atmosphere}.

Art style: {style_keywords}, {quality_keywords}.
```

---

## 五、核心算法

### 5.1 角色一致性策略

```python
# 串行生成：确保肖像和全身图是同一个人
async def generate_character_multi_refs(character, project_style, image_generator):
    # 1. 先生成肖像（无参考）
    portrait_result = await generate_character_reference(
        character, ref_type='portrait', portrait_ref=None
    )
    portrait_image = portrait_result.get('pil_image')

    # 2. 用肖像作为参考生成全身图
    fullbody_result = await generate_character_reference(
        character, ref_type='fullbody', portrait_ref=portrait_image  # 传入肖像！
    )

    return {'portrait': portrait_result, 'fullbody': fullbody_result}
```

### 5.2 场景参考图生成 (P2.0)

```python
def _analyze_anchor_needs(scenes, unique_locations=None):
    """分析需要生成的锚点图"""

    # P2.0: 优先使用结构化 unique_locations
    if unique_locations:
        return _analyze_anchor_needs_from_structured(scenes, unique_locations)

    # Fallback: 规则匹配（兼容旧格式）
    return _analyze_anchor_needs_by_rules(scenes)

def _analyze_anchor_needs_from_structured(scenes, unique_locations):
    """从结构化 unique_locations 分析锚点需求"""
    anchors = {}

    for loc in unique_locations:
        loc_id = loc.get('location_id')
        loc_type = loc.get('location_type', 'both')

        if loc_type in ('interior_only', 'both'):
            anchors[f"{loc_id}_interior"] = {
                'location_name': loc.get('display_name'),
                'description': loc.get('interior_description'),
                'key_visual_elements': loc.get('key_visual_elements', []),
                'view_type': 'interior'
            }

        if loc_type in ('exterior_only', 'both'):
            anchors[f"{loc_id}_exterior"] = {
                'location_name': loc.get('display_name'),
                'description': loc.get('exterior_description'),
                'key_visual_elements': loc.get('key_visual_elements', []),
                'view_type': 'exterior'
            }

    return anchors
```

### 5.3 Shot图像生成流程

```python
for shot in shots:
    # 1. 获取出场角色的参考图
    chars_in_scene = shot.get('characters_in_scene', [])
    char_refs = []
    for cid in chars_in_scene:
        if cid in ref_manager.character_references:
            refs = ref_manager.character_references[cid]
            if 'portrait' in refs:
                char_refs.append(refs['portrait'])
            if 'fullbody' in refs:
                char_refs.append(refs['fullbody'])

    # 2. 获取场景参考图
    scene_refs = scene_ref_manager.get_references_for_location(location_id)

    # 3. 合并参考图（角色优先）
    all_refs = char_refs + scene_refs  # 最多14张

    # 4. 生成图像
    result = await image_gen.generate_shot_image(
        shot=shot,
        reference_images=all_refs
    )
```

### 5.4 音画对齐算法

```python
def align_shots_to_audio(shots, whisper_segments, whisper_text, audio_duration):
    """多策略文本匹配"""

    for shot in shots:
        narration = shot['narration_segment']

        # 策略1: 精确匹配
        match = find_exact_match(narration, whisper_segments)

        # 策略2: 去标点匹配
        if not match:
            match = find_match_without_punctuation(narration, whisper_segments)

        # 策略3: 前缀匹配
        if not match:
            match = find_prefix_match(narration, whisper_segments)

        # 策略4: 子序列匹配
        if not match:
            match = find_subsequence_match(narration, whisper_segments)

        # 繁简转换处理
        if not match:
            simplified = convert_to_simplified(narration)
            match = find_match(simplified, whisper_segments)
```

---

## 六、风格系统

### 6.1 支持的风格列表

| 风格名 | 显示名 | 说明 |
|--------|--------|------|
| `realistic` | Photorealistic Photography | 写实摄影风格 |
| `cartoon` | Cartoon Animation | 卡通动画风格 |
| `pixar_3d` | Pixar 3D Animation | 皮克斯3D动画风格 |
| `anime` | Japanese Anime | 日式动画风格 |
| `ghibli` | Studio Ghibli Style | 吉卜力风格 |
| `illustration` | Digital Illustration | 数字插画风格 |
| `watercolor` | Watercolor Painting | 水彩画风格 |
| `children_book` | Children's Book Illustration | 儿童绘本风格 |
| `manga` | Japanese Manga | 日式漫画风格 |
| `oil_painting` | Oil Painting | 油画风格 |
| `cyberpunk` | Cyberpunk Aesthetic | 赛博朋克风格 |
| `ink` | Chinese Ink Wash Painting | 中国水墨风格 |
| `pixel` | Pixel Art | 像素艺术风格 |

### 6.2 风格强制关键词示例

**realistic (写实摄影)**
```python
mandatory = ["photorealistic", "photograph", "real photo", "professional photography",
             "natural skin texture", "realistic lighting"]
forbidden = ["cartoon", "anime", "illustration", "drawing", "painting",
             "3D render", "CGI", "Pixar", "Disney", "stylized"]
```

**anime (日式动画)**
```python
mandatory = ["anime style", "Japanese animation", "cel shading", "expressive eyes",
             "dynamic poses", "anime aesthetic"]
forbidden = ["photorealistic", "photograph", "3D render", "Pixar",
             "Western cartoon", "realistic skin"]
```

---

## 七、角色类型系统

### 7.1 支持的19种角色类型

| 类型 | 描述 | 关键字段 |
|------|------|----------|
| `human` | 人类 | physical, clothing |
| `animal` | 动物 | animal (species, fur_color, etc.) |
| `robot` | 机器人 | robot (chassis, sensors, etc.) |
| `fantasy_creature` | 奇幻生物 | fantasy (wings, horns, etc.) |
| `insect` | 昆虫 | insect (wings, antennae, etc.) |
| `aquatic` | 水生生物 | aquatic (fins, scales, etc.) |
| `plant` | 植物角色 | plant (leaves, flowers, etc.) |
| `mythological` | 神话生物 | mythological |
| `supernatural` | 超自然存在 | supernatural |
| `undead` | 亡灵 | undead |
| `elemental` | 元素生物 | elemental |
| `alien` | 外星生物 | alien |
| `vehicle_character` | 载具角色 | vehicle_character |
| `digital_virtual` | 数字/虚拟角色 | digital_virtual |
| `concept_personified` | 概念拟人 | concept_personified |
| `miniature` | 微型角色 | miniature |
| `giant` | 巨型角色 | giant |
| `object` | 物品拟人 | object |
| `hybrid` | 混合类型 | hybrid |

---

## 八、开发迭代历史

### 8.1 版本演进

| 版本 | 日期 | 核心改动 |
|------|------|----------|
| P1.0 | 12月初 | 基础流程搭建 |
| P1.1 | 12月中 | 角色一致性优化（串行生成） |
| P1.2 | 12月16日 | 修复9个核心问题 |
| P2.0 | 12月19日 | unique_locations结构化场景 |

### 8.2 P1.2修复的问题清单

| 问题ID | 问题描述 | 解决方案 |
|--------|----------|----------|
| P1 | visual_description中文未翻译 | _simple_translate_prompt() |
| P2 | shot_type/camera_angle中文 | _translate_shot_type() |
| P3 | characters_in_scene未继承 | 手动继承scene的角色列表 |
| P4 | 角色描述为空 | 从physical+clothing字段构建 |
| P5 | 角色类型识别失败 | 同时检查type和character_type |
| P6 | 风格漂移 | StyleEnforcer强制前缀 |
| P7 | 繁简不匹配 | _convert_to_simplified() |
| P8 | 音画不对齐 | 多策略匹配 |
| P9 | 场景参考图缺失 | SceneReferenceManager |

### 8.3 P2.0核心改动

1. **unique_locations结构化**
   - LLM输出结构化场景位置数据
   - 每个location包含英文description和key_visual_elements
   - 支持location_type区分interior/exterior

2. **场景锚点图简化**
   - 每个location_type只生成1张锚点图
   - 差异化由ShotPromptGenerator在shots阶段完成

3. **多场景故事支持**
   - 正确区分"小明家"和"小红家"
   - 规则解析作为fallback

---

## 九、测试记录

### 9.1 测试文件清单

| 测试文件 | 测试内容 |
|----------|----------|
| `test_story6_3_4.py` | 完整端到端测试（服装描述清洗） |
| `test_story6_3_5.py` | story.json生成测试 |
| `test_story6_3_8.py` | P2.0锚点图+ShotPromptGenerator |
| `test_structured_locations.py` | unique_locations结构测试 |
| `test_e2e_unique_locations.py` | 端到端mock测试 |
| `test_story_generator_unique_locations.py` | 真实LLM测试 |

### 9.2 测试输出目录

```
test_output/manualtest/
├── teststory6.3.4/
│   ├── story.json
│   ├── shots.json
│   ├── character_refs/
│   │   ├── char_001_portrait.png
│   │   ├── char_001_fullbody.png
│   │   └── ...
│   ├── scene_refs/
│   │   ├── convenience_store_interior.png
│   │   └── ...
│   ├── images/
│   │   ├── shot_01.png
│   │   └── ...
│   ├── narration.mp3
│   ├── whisper.json
│   └── timeline.json
```

---

## 十、开发约束

### 10.1 必须遵守的规则

1. **image_prompt必须全英文** - Gemini图像生成对英文效果更好
2. **shot_type和camera_angle必须英文** - 使用翻译函数
3. **narration保留中文** - 用于TTS合成
4. **风格前缀必须添加** - StyleEnforcer.enforce_prompt()
5. **shot必须继承characters_in_scene**
6. **场景图必须传入参考图** - generate_shot_image()
7. **No backward compatibility** - 不写兼容性代码

### 10.2 已踩过的坑

| 问题 | 错误做法 | 正确做法 |
|------|----------|----------|
| 风格漂移 | 只在prompt末尾加风格 | 在开头加MANDATORY STYLE |
| 角色变脸 | 肖像和全身独立生成 | 串行生成：肖像→用肖像作参考 |
| shot缺角色 | 拆分后不管characters_in_scene | 手动继承 |
| 音画不对齐 | 精确匹配失败就放弃 | 多策略匹配 |
| 繁简不匹配 | 直接比较 | 先繁简转换 |

---

## 十一、环境配置

### 11.1 环境变量

```bash
# 必需
ANTHROPIC_API_KEY=sk-ant-xxx       # Claude API
GEMINI_API_KEY=AIzaSyxxx           # Google Gemini API
OPENAI_API_KEY=sk-xxx              # OpenAI Whisper API
VOLCENGINE_ACCESS_KEY=AKLTxxx      # 火山引擎TTS
VOLCENGINE_SECRET_KEY=xxx
VOLCENGINE_TTS_APPID=xxx

# 可选
SHOT_MAX_NARRATION_LENGTH=60       # 触发拆分的阈值
SHOT_TARGET_LENGTH=40              # 目标shot长度
```

### 11.2 项目结构

```
xuhua_story/
├── app/
│   ├── api/                  # REST API端点
│   ├── models/               # 数据模型
│   ├── prompts/              # Prompt模板
│   │   ├── story_generation.py
│   │   ├── storyboard_prompts.py
│   │   └── shot_prompt_generator.py
│   ├── services/             # 核心服务
│   │   ├── story_generator.py
│   │   ├── storyboard_service.py
│   │   ├── image_generator.py
│   │   ├── reference_image_manager.py
│   │   ├── scene_reference_manager.py
│   │   ├── style_enforcer.py
│   │   └── ...
│   └── data/                 # 静态数据
├── tests/                    # 测试文件
├── test_output/              # 测试输出
├── docs/                     # 文档
├── forclaudeweb/             # Claude Web分享文件
└── CLAUDE.md                 # AI开发上下文
```

---

## 十二、待解决问题

### 12.1 角色一致性仍有提升空间

- Gemini对参考图的遵循是"参考"而非"强制"
- 多人场景复杂度高时，难以同时精确匹配所有角色
- prompt中角色描述与参考图可能存在冲突

### 12.2 场景变化一致性

- 当前只有锚点图（1张interior/exterior）
- 不同时间/天气/氛围的变化完全依赖prompt描述
- 缺少"条件变体"参考图

### 12.3 可能的改进方向

1. 增加条件变体场景参考图（night/dawn/rain等）
2. 更强的prompt结构强制角色一致性
3. 后处理：检测角色不一致并重新生成

---

*文档版本: 2025-12-19 | 维护者: AI开发助手*
