# 项目完整信息 - AI开发助手上下文文档

> 本文档为AI开发助手提供项目上下文，帮助快速理解项目架构和代码规范。

## 1. 项目结构 (3级目录树)

```
xuhua_story/
├── app/                          # 核心应用目录
│   ├── __init__.py
│   ├── main.py                   # FastAPI应用入口
│   ├── config.py                 # 配置管理（环境变量、API密钥）
│   ├── database.py               # 数据库连接
│   │
│   ├── api/                      # REST API端点
│   │   ├── auth.py               # 认证API
│   │   ├── projects.py           # 项目管理API
│   │   ├── chapters.py           # 章节管理API
│   │   ├── images.py             # 图片相关API
│   │   └── audio.py              # 音频相关API
│   │
│   ├── models/                   # 数据模型
│   │   ├── user.py               # 用户模型
│   │   ├── project.py            # 项目模型
│   │   ├── chapter.py            # 章节模型
│   │   ├── job.py                # 异步任务模型
│   │   ├── scene_image.py        # 场景图片模型
│   │   ├── audio_segment.py      # 音频片段模型
│   │   ├── style_config.py       # 风格配置模型（80+风格）
│   │   └── character_types.py    # 角色类型定义（19种类型）
│   │
│   ├── schemas/                  # Pydantic schemas
│   │   ├── project.py            # 项目请求/响应schema
│   │   └── chapter.py            # 章节schema
│   │
│   ├── prompts/                  # LLM提示词模板
│   │   ├── story_generation.py   # 故事生成prompt（核心）
│   │   ├── storyboard_prompts.py # 分镜prompt模板
│   │   └── alignment_prompts.py  # 音画对齐prompt
│   │
│   ├── services/                 # 核心业务服务
│   │   ├── story_generator.py    # 故事生成服务（Claude+Gemini）
│   │   ├── storyboard_service.py # 分镜决策服务（含shot拆分）
│   │   ├── image_generator.py    # 图像生成服务（Gemini API）
│   │   ├── tts_service.py        # TTS服务（火山引擎Doubao）
│   │   ├── whisper_service.py    # 语音识别服务（OpenAI Whisper）
│   │   ├── alignment_service.py  # 音画对齐服务
│   │   ├── reference_image_manager.py    # 角色参考图管理
│   │   ├── scene_reference_manager.py    # 场景参考图管理
│   │   ├── character_prompt_builder.py   # 角色描述构建（19类型）
│   │   ├── style_enforcer.py     # 风格强制器
│   │   └── scene_style_manager.py        # 场景风格管理
│   │
│   └── data/                     # 静态数据
│       ├── style_presets.json    # 风格预设定义
│       └── character_types.json  # 角色类型定义
│
├── tests/                        # 测试文件
│   ├── test_story_generator.py   # 故事生成测试
│   ├── test_story6_1.py          # teststory6.1完整测试
│   ├── test_verify_fixes.py      # 修复验证测试
│   └── ...                       # 其他测试
│
├── test_output/                  # 测试输出目录
│   └── manualtest/               # 手动测试输出
│       ├── teststory6.1/         # story.json, shots.json, 图片
│       └── teststory6_verify_fixes/
│
├── docs/                         # 文档
│   └── progress_report_teststory6.md  # 问题修复报告
│
├── venv/                         # Python虚拟环境
├── .env                          # 环境变量配置
└── README.md
```

## 2. 核心服务架构

| 服务类 | 文件位置 | 职责 | 依赖的外部API |
|--------|----------|------|---------------|
| **StoryGenerator** | `story_generator.py` | LLM故事生成 | Claude Haiku (主) + Gemini (备) |
| **StoryboardService** | `storyboard_service.py` | 分镜决策、shot拆分、image_prompt构建 | Gemini 2.5 Flash |
| **ImageGenerator** | `image_generator.py` | 图像生成 | Gemini 2.5 Flash Image / Gemini 3 Pro |
| **TTSService** | `tts_service.py` | 文字转语音 | 火山引擎 Doubao TTS |
| **WhisperService** | `whisper_service.py` | 语音转文字+时间戳 | OpenAI Whisper API |
| **AlignmentService** | `alignment_service.py` | 音画时间对齐 | Gemini 2.5 Flash |
| **ReferenceImageManager** | `reference_image_manager.py` | 角色参考图生成与管理 | ImageGenerator |
| **SceneReferenceManager** | `scene_reference_manager.py` | 场景参考图生成与管理 | ImageGenerator |
| **CharacterPromptBuilder** | `character_prompt_builder.py` | 19种角色类型的prompt构建 | - |
| **StyleEnforcer** | `style_enforcer.py` | 风格强制锁定（mandatory/forbidden词） | - |
| **StyleConfigBuilder** | `style_config.py` | 80+风格模板管理 | - |

## 3. 数据流完整链

```
用户输入(idea)
    ↓
StoryGenerator.generate_story()
    ├── Claude Haiku (primary)
    └── Gemini 3 Pro / 2.5 Flash (fallback)
    ↓
story.json 输出
{characters[], scenes[], visual_style}
    ↓
StoryboardService.generate_storyboard_with_splitting()
    ├── 检测 narration 长度
    ├── >60字：调用 _split_scene_to_shots() [LLM拆分]
    └── ≤60字：_create_shot_from_scene() [直接转换]
    ↓
shots.json 输出 (每个shot ≤40字narration)
{shot_id, image_prompt, narration_segment, characters_in_scene, ...}
    ↓
ReferenceImageManager.generate_character_multi_refs()
    ├── 生成角色肖像参考图 (portrait)
    └── 生成角色全身参考图 (fullbody, 使用portrait作参考)
    ↓
角色参考图 → scene_refs/{char_id}_portrait.png, {char_id}_fullbody.png
    ↓
SceneReferenceManager.generate_all_scene_references()
    ↓
场景参考图 → scene_refs/{location_id}_{view_type}.png
    ↓
ImageGenerator.generate_shot_image(shot, reference_images)
    ├── 翻译 image_prompt → 英文
    ├── 传入角色+场景参考图
    └── Gemini 图像生成
    ↓
场景图片 → images/shot_{id}.png
    ↓
TTSService.generate_speech()
    └── 火山引擎 Doubao TTS
    ↓
音频文件 → audio/narration.mp3
    ↓
WhisperService.transcribe_with_timestamps()
    └── OpenAI Whisper API
    ↓
{segments: [{start, end, text}], words: [{start, end, word}]}
    ↓
AlignmentService.align_shots_to_audio()
    ├── 构建segment文本索引
    ├── 匹配shot.narration_segment → segment时间范围
    └── 繁简转换处理
    ↓
timeline.json 输出
{shot_id, start_time, end_time, duration, image_path, ...}
    ↓
视频合成（外部处理）
```

## 4. 关键Prompt模板

### 4.1 故事生成Prompt (story_generation.py)

```python
# 核心结构
{
  "characters": [
    {
      "id": "char_001",
      "name": "中文名",
      "name_en": "English Name",
      "physical": {  # 人类角色
        "hair_color", "hair_style", "eye_color", "eye_shape",
        "skin_tone", "face_shape", "height", "build", ...
      },
      "animal": {  # 动物角色
        "species", "breed", "fur_color", "fur_pattern",
        "eye_color", "tail", ...
      },
      "clothing": {
        "top", "bottom", "accessories", "style"
      }
    }
  ],
  "scenes": [
    {
      "scene_id": 1,
      "story_phase": "opening/adventure/crisis/climax/resolution",
      "scene_style": {
        "color_palette", "lighting", "atmosphere", "weather", "time_of_day"
      },
      "characters_in_scene": ["char_001"],
      "visual_description": "英文场景描述",
      "narration": "中文旁白（40-80字）"
    }
  ]
}
```

### 4.2 分镜拆分Prompt (storyboard_service.py)

```python
# _split_scene_to_shots() 使用的prompt
"""
You are a professional storyboard artist. Split the following scene into {n} shots.

## Splitting Requirements
1. Each shot corresponds to 25-50 characters of narration
2. Each shot describes a single frame with clear visual focus
3. Maintain continuity between shots

## Output Format (JSON)
{
  "shots": [
    {
      "shot_index": 1,
      "shot_type": "wide shot/medium shot/close-up/...",  # MUST be English
      "visual_description": "MUST BE IN ENGLISH",
      "narration_segment": "保留原始中文",
      "camera_angle": "eye level/low angle/high angle",
      "focus": "Visual focus in ENGLISH"
    }
  ]
}
"""
```

### 4.3 音画对齐Prompt (alignment_prompts.py)

```python
# 视觉匹配prompt - 传入图片给Gemini分析
"""
分析每张图片的内容，将其匹配到语义上最相关的音频段落。

## 匹配原则
1. 语义匹配：图片内容与文本语义相关
2. 顺序性：保持故事顺序
3. 完整覆盖：所有图片和时间段都要分配
4. 无重叠：相邻图片时间段不能重叠

## 输出格式
{
  "matches": [
    {"scene_id": 1, "start_segment_index": 0, "end_segment_index": 2}
  ]
}
"""
```

## 5. 数据模型 (JSON结构)

### 5.1 story.json

```json
{
  "title": "故事标题",
  "synopsis": "简介",
  "visual_style": {
    "art_style": "illustration",
    "rendering": "soft",
    "color_palette": "warm",
    "primary_colors": ["golden", "cream"],
    "lighting": "soft natural",
    "atmosphere": "warm and cozy"
  },
  "characters": [
    {
      "id": "char_su_chen",
      "name": "苏晨",
      "name_en": "Su Chen",
      "role": "protagonist",
      "character_type": "human",
      "physical": {
        "hair_color": "black",
        "hair_style": "short slightly messy",
        "eye_color": "dark brown",
        "skin_tone": "fair",
        "face_shape": "oval"
      },
      "clothing": {
        "top": "gray wool sweater",
        "bottom": "dark blue jeans",
        "accessories": ["black-framed glasses"],
        "style": "casual intellectual"
      }
    }
  ],
  "scenes": [...]
}
```

### 5.2 shots.json

```json
[
  {
    "shot_id": 1,
    "original_scene_id": 1,
    "image_prompt": "A young woman with short neat black hair... Shot type: medium shot. Camera angle: eye level...",
    "narration_segment": "清晨的阳光透过咖啡馆的落地窗...",
    "shot_type": "medium shot",
    "visual_description": "English description...",
    "camera_angle": "eye level",
    "characters_in_scene": ["char_su_chen", "char_lin_wei"],
    "duration_hint": 8.5,
    "aspect_ratio": "16:9"
  }
]
```

### 5.3 timeline.json

```json
[
  {
    "shot_id": 1,
    "original_scene_id": 1,
    "image_path": "images/shot_1.png",
    "start_time": 0.0,
    "end_time": 8.5,
    "duration": 8.5,
    "narration_segment": "清晨的阳光透过咖啡馆的落地窗..."
  }
]
```

## 6. 技术决策记录

| 决策 | 选择 | 原因 |
|------|------|------|
| LLM主模型 | Claude Haiku | 快速、成本低、中文理解好 |
| LLM备用模型 | Gemini 3 Pro / 2.5 Flash | Claude失败时的fallback |
| 图像生成 | Gemini 2.5 Flash Image | 支持参考图、速度快 |
| 图像备用 | Gemini 3 Pro Image Preview | 高质量生成 |
| TTS服务 | 火山引擎 Doubao | 中文语音质量高、多种音色 |
| 语音识别 | OpenAI Whisper | 精确的word-level时间戳 |
| Shot拆分阈值 | MAX=60字, TARGET=40字 | 短视频节奏优化 |
| 参考图策略 | 肖像+全身串行生成 | 确保同一角色面部一致 |
| 风格强制 | StyleEnforcer | 每个prompt强制添加风格前缀 |
| 繁简转换 | _convert_to_simplified() | Whisper常输出繁体 |
| Prompt语言 | image_prompt全英文 | Gemini图像生成效果更好 |

## 7. 已知限制与注意事项

### 7.1 角色一致性
- Gemini图像生成无法100%保证角色一致
- 依赖参考图+详细描述来提高一致性
- 同一角色在不同场景可能有细微差异

### 7.2 Shot拆分
- LLM拆分可能输出中文字段（已修复：强制要求英文）
- 简单拆分是fallback方案，质量较低

### 7.3 音画对齐
- Whisper可能输出繁体中文（已修复：繁简转换）
- 对于生僻词或专有名词，匹配可能失败
- 使用多种策略（精确匹配→去标点→子串）

### 7.4 API限制
- Gemini图像生成有速率限制
- 火山引擎TTS有字数限制
- 建议生成间隔3秒以上

### 7.5 characters_in_scene继承
- shot必须继承scene的characters_in_scene
- 在_split_scene_to_shots()后手动设置

## 8. 代码规范

### 8.1 异步模式
- 所有外部API调用使用async/await
- 使用asyncio.Semaphore控制并发

### 8.2 错误处理
- 所有服务都有fallback策略
- LLM失败 → 简单规则处理
- 图像生成失败 → 最多重试3次

### 8.3 日志输出
- 使用print输出进度信息
- 格式: `[ServiceName] 操作描述`
- 使用✅/❌表示成功/失败

### 8.4 文件命名
- 测试脚本: `test_*.py`
- 服务类: `*_service.py` 或 `*_manager.py`
- 输出目录: `test_output/manualtest/{test_name}/`

## 9. 环境配置

### 9.1 必需的环境变量 (.env)

```bash
# LLM API
ANTHROPIC_API_KEY=sk-ant-xxx       # Claude API
GEMINI_API_KEY=AIzaSyxxx           # Google Gemini API

# 音频服务
OPENAI_API_KEY=sk-xxx              # OpenAI Whisper API
VOLCENGINE_ACCESS_KEY=AKLTxxx      # 火山引擎
VOLCENGINE_SECRET_KEY=xxx
VOLCENGINE_TTS_APPID=xxx

# 可选配置
SHOT_MAX_NARRATION_LENGTH=60       # 触发拆分的阈值
SHOT_TARGET_LENGTH=40              # 目标shot长度
SHOT_MIN_LENGTH=20                 # 最小shot长度
TTS_CHARS_PER_SECOND=4             # TTS语速
```

### 9.2 Python依赖
```
fastapi
uvicorn
anthropic
google-genai
openai
pillow
pydantic
python-dotenv
```

## 10. 测试验证清单

### 10.1 story.json验证
- [ ] characters[]每个角色有id、name、name_en
- [ ] 人类角色有physical字段（hair_color, eye_color等）
- [ ] 动物角色有animal字段（species, fur_color等）
- [ ] 服装有clothing字段（top, bottom, accessories）
- [ ] scenes[]每个场景有characters_in_scene
- [ ] scene_style有color_palette, lighting, atmosphere

### 10.2 shots.json验证
- [ ] image_prompt全英文（除了需要渲染的文字）
- [ ] shot_type是英文（wide shot, medium shot等）
- [ ] camera_angle是英文（eye level, low angle等）
- [ ] narration_segment保留原始中文
- [ ] characters_in_scene从scene继承

### 10.3 图像生成验证
- [ ] 角色参考图生成（portrait + fullbody）
- [ ] 场景参考图生成（exterior/interior）
- [ ] shot图像使用参考图作为reference_images
- [ ] 风格前缀被正确添加（StyleEnforcer）

### 10.4 音画对齐验证
- [ ] timeline覆盖完整音频时长
- [ ] 无时间重叠
- [ ] 无时间间隙（或间隙<80ms）
- [ ] 每个shot都有对应时间段

---

## 附录A：StyleEnforcer 完整风格配置

### A.1 支持的风格列表

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

### A.2 各风格 mandatory/forbidden 关键词完整列表

#### realistic (写实摄影)
```python
mandatory_keywords = [
    "photorealistic", "photograph", "real photo", "professional photography",
    "natural skin texture", "realistic lighting", "photographic quality",
    "lifelike", "real human"
]
forbidden_keywords = [
    "cartoon", "anime", "illustration", "drawing", "painting",
    "3D render", "CGI", "Pixar", "Disney", "stylized",
    "cel-shaded", "vector", "flat colors", "manga", "comic",
    "artistic interpretation", "digital art"
]
quality_keywords = ["8K", "high resolution", "sharp focus", "professional lighting", "DSLR quality"]
```

#### cartoon (卡通动画)
```python
mandatory_keywords = [
    "cartoon style", "animated", "vibrant colors", "clean lines",
    "expressive characters", "animated movie quality"
]
forbidden_keywords = [
    "photorealistic", "photograph", "real photo", "lifelike",
    "realistic skin", "natural lighting"
]
quality_keywords = ["high quality animation", "professional cartoon", "polished artwork"]
```

#### pixar_3d (皮克斯3D)
```python
mandatory_keywords = [
    "Pixar style", "3D animation", "smooth surfaces", "subsurface scattering",
    "cinematic lighting", "expressive 3D characters", "volumetric lighting"
]
forbidden_keywords = [
    "photorealistic", "photograph", "real photo", "2D", "flat",
    "anime", "manga", "hand-drawn", "sketch"
]
quality_keywords = ["high quality 3D render", "professional animation", "studio quality"]
```

#### anime (日式动画)
```python
mandatory_keywords = [
    "anime style", "Japanese animation", "cel shading", "expressive eyes",
    "dynamic poses", "anime aesthetic"
]
forbidden_keywords = [
    "photorealistic", "photograph", "3D render", "Pixar",
    "Western cartoon", "realistic skin"
]
quality_keywords = ["high quality anime", "professional anime art", "detailed anime"]
```

#### ghibli (吉卜力)
```python
mandatory_keywords = [
    "Studio Ghibli style", "Miyazaki inspired", "hand-drawn animation",
    "soft colors", "detailed backgrounds", "whimsical atmosphere"
]
forbidden_keywords = [
    "photorealistic", "3D render", "digital 3D", "harsh lighting",
    "dark gritty", "modern CGI"
]
quality_keywords = ["Ghibli quality", "masterful animation", "hand-painted look"]
```

#### illustration (数字插画)
```python
mandatory_keywords = [
    "digital illustration", "vibrant colors", "detailed artwork",
    "concept art", "clean lines", "rich details"
]
forbidden_keywords = [
    "photorealistic", "photograph", "3D render",
    "low quality", "sketch", "unfinished"
]
quality_keywords = ["artstation trending", "professional illustration", "high detail"]
```

#### watercolor (水彩画)
```python
mandatory_keywords = [
    "watercolor painting", "soft edges", "dreamy atmosphere",
    "flowing colors", "wet on wet technique", "artistic"
]
forbidden_keywords = [
    "photorealistic", "sharp edges", "3D render", "digital",
    "hard lines", "neon colors"
]
quality_keywords = ["beautiful watercolor", "artistic quality", "delicate washes"]
```

#### children_book (儿童绘本)
```python
mandatory_keywords = [
    "children's book illustration", "friendly characters", "soft colors",
    "whimsical", "storybook style", "child-friendly"
]
forbidden_keywords = [
    "photorealistic", "scary", "dark", "violent",
    "mature content", "horror", "realistic violence"
]
quality_keywords = ["professional children's illustration", "picture book quality", "appealing to children"]
```

#### manga (日式漫画)
```python
mandatory_keywords = [
    "manga style", "Japanese comic", "screentone", "expressive",
    "dynamic composition", "manga aesthetic"
]
forbidden_keywords = [
    "photorealistic", "3D render", "Western comic style",
    "full color realistic"
]
quality_keywords = ["professional manga", "detailed linework", "high quality manga art"]
```

#### oil_painting (油画)
```python
mandatory_keywords = [
    "oil painting", "visible brushstrokes", "classical art",
    "rich textures", "painterly", "artistic"
]
forbidden_keywords = [
    "photorealistic", "digital", "flat colors", "vector",
    "anime", "cartoon"
]
quality_keywords = ["museum quality", "masterful painting", "fine art"]
```

#### cyberpunk (赛博朋克)
```python
mandatory_keywords = [
    "cyberpunk", "neon lights", "futuristic city", "dark atmosphere",
    "high tech low life", "blade runner aesthetic"
]
forbidden_keywords = [
    "pastoral", "rural", "ancient", "medieval",
    "bright daylight", "nature scene"
]
quality_keywords = ["atmospheric", "cinematic cyberpunk", "detailed futuristic"]
```

#### ink (中国水墨)
```python
mandatory_keywords = [
    "Chinese ink wash", "sumi-e", "brush strokes", "minimalist",
    "traditional Chinese art", "rice paper texture"
]
forbidden_keywords = [
    "colorful", "neon", "photorealistic", "3D render",
    "Western art", "digital effects"
]
quality_keywords = ["elegant", "masterful brushwork", "traditional aesthetics"]
```

#### pixel (像素艺术)
```python
mandatory_keywords = [
    "pixel art", "retro game", "16-bit", "crisp pixels",
    "limited color palette", "nostalgic gaming"
]
forbidden_keywords = [
    "photorealistic", "smooth gradients", "high resolution photo",
    "3D render", "anti-aliased"
]
quality_keywords = ["clean pixels", "well-designed pixel art", "professional retro"]
```

### A.3 风格强制前缀模板

StyleEnforcer会在每个image_prompt最前面加入强制风格前缀：

```
═══════════════════════════════════════════════════════════
MANDATORY STYLE REQUIREMENT - DO NOT IGNORE THIS SECTION
═══════════════════════════════════════════════════════════

STYLE: {style_display_name}

{style_description}

MUST INCLUDE: {mandatory_keywords前5个}

DO NOT USE: {forbidden_keywords前8个}

This style requirement applies to ALL elements in this image.
═══════════════════════════════════════════════════════════
```

---

## 附录B：_build_character_description 完整实现

位置：`app/services/storyboard_service.py:489-553`

```python
def _build_character_description(self, character: dict) -> str:
    """
    从角色数据构建详细的外观描述（用于image prompt）

    优先从clothing和physical字段获取详细信息，确保角色一致性
    """
    desc_parts = []

    # 1. 物理外观 (physical)
    physical = character.get('physical', {})
    if physical:
        # 发型和发色（最重要的识别特征）
        hair_color = physical.get('hair_color', '')
        hair_style = physical.get('hair_style', '')
        if hair_color or hair_style:
            desc_parts.append(f"{hair_color} {hair_style}".strip())

        # 眼睛
        eye_color = physical.get('eye_color', '')
        eye_shape = physical.get('eye_shape', '')
        if eye_color:
            desc_parts.append(f"{eye_color} eyes")

        # 肤色
        skin_tone = physical.get('skin_tone', '')
        if skin_tone:
            desc_parts.append(f"{skin_tone} skin")

    # 2. 服装（clothing）- 非常重要，用于区分角色
    clothing = character.get('clothing', {})
    if clothing:
        # 上衣
        top = clothing.get('top', '')
        if top:
            desc_parts.append(f"wearing {top}")

        # 下装
        bottom = clothing.get('bottom', '')
        if bottom:
            desc_parts.append(bottom)

        # 配饰（非常重要，用于区分角色）
        accessories = clothing.get('accessories', [])
        if accessories:
            # 只取前2-3个最重要的配饰
            key_accessories = accessories[:3]
            desc_parts.append(", ".join(key_accessories))

        # 风格
        style = clothing.get('style', '')
        if style:
            desc_parts.append(f"{style} style")

    # 3. 如果没有详细字段，尝试使用description或appearance
    if not desc_parts:
        desc = character.get('description', '') or character.get('appearance', '')
        if desc:
            return desc

    # 4. 兜底：尝试从animal字段构建（非人类角色）
    if not desc_parts and character.get('animal'):
        a = character['animal']
        return f"{a.get('fur_color', '')} {a.get('species', '')} with {a.get('eye_color', '')} eyes"

    return ", ".join(desc_parts) if desc_parts else ""
```

### B.1 方法调用位置

该方法在 `_build_shot_prompt()` 中被调用，用于构建每个shot的image_prompt：

```python
def _build_shot_prompt(self, shot: dict, scene: dict, characters: List[dict], style_preset: str) -> str:
    # ...
    # 构建角色描述部分
    char_ids = shot.get('characters_in_scene', scene.get('characters_in_scene', []))
    char_descriptions = []
    for char_id in char_ids:
        char = char_map.get(char_id)
        if char:
            name = char.get('name_en', char.get('name', 'Unknown'))
            desc = self._build_character_description(char)  # <-- 调用位置
            if desc:
                char_descriptions.append(f"{name}: {desc}")
    # ...
```

### B.2 输出示例

输入角色数据：
```json
{
  "name": "苏晨",
  "name_en": "Su Chen",
  "physical": {
    "hair_color": "black",
    "hair_style": "short slightly messy",
    "eye_color": "dark brown",
    "skin_tone": "fair"
  },
  "clothing": {
    "top": "gray wool sweater",
    "bottom": "dark blue jeans",
    "accessories": ["black-framed glasses"],
    "style": "casual intellectual"
  }
}
```

输出描述：
```
black short slightly messy, dark brown eyes, fair skin, wearing gray wool sweater, dark blue jeans, black-framed glasses, casual intellectual style
```

---

## 附录C：常见问题修复记录

详见 `/docs/progress_report_teststory6.md`，包含9个已修复问题的完整诊断和解决方案。

---

*文档更新日期: 2025-12-16*
