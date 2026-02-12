# 绘话故事 - 测试验证与修复报告

## 项目概述

**项目名称**: 绘话故事 (Xuhua Story)
**测试周期**: 2025年12月15日 - 2025年12月16日
**测试版本**: teststory6 系列
**报告生成时间**: 2025-12-16 20:35

---

## 一、测试起源

### 1.1 初始测试Idea

```
深夜地铁末班车上，一个加班到崩溃的白领和一个刚结束演出的街头歌手，
因为同一首歌产生了短暂的共鸣。
```

### 1.2 测试目标

验证完整的故事生成流程：
- 故事生成 (StoryGenerator)
- 分镜拆分 (StoryboardService)
- TTS语音合成 (TTSService)
- Whisper时间戳 (WhisperService)
- 音画对齐 (AlignmentService)
- 角色参考图生成 (ReferenceImageManager)
- 场景参考图生成 (SceneReferenceManager)
- 场景图片生成 (ImageGenerator)

---

## 二、发现的问题与修复历程

### 2.1 问题1: characters_in_scene 未正确继承

**发现时间**: 2025-12-15
**问题描述**: Shot拆分后，`characters_in_scene` 字段丢失，导致无法获取正确的角色参考图

**根因分析**:
- `StoryboardService.generate_storyboard_with_splitting()` 方法在拆分场景时，没有将原始scene的 `characters_in_scene` 传递给子shot

**修复方案**:
```python
# storyboard_service.py - generate_storyboard_with_splitting()
# 在创建shot时，继承scene的characters_in_scene
shot['characters_in_scene'] = scene_characters_in_scene
```

**修复文件**: `app/services/storyboard_service.py`
**验证状态**: ✅ 已验证通过

---

### 2.2 问题2: 音画对齐不准确

**发现时间**: 2025-12-15
**问题描述**: Whisper返回的时间戳与原始旁白文本匹配不准确，导致音画不同步

**根因分析**:
1. Whisper经常输出繁体中文，而原始旁白是简体中文
2. 标点符号差异（句号vs逗号）
3. 文本匹配算法过于严格

**修复方案**:
```python
# alignment_service.py
def _convert_to_simplified(self, text: str) -> str:
    """将繁体中文转换为简体中文"""
    traditional_to_simplified = {
        '後': '后', '鐵': '铁', '燈': '灯', ...
    }
    # 转换繁体字

def _find_text_position(self, narration: str, full_text: str) -> tuple:
    """多策略文本匹配"""
    # 策略1: 直接匹配
    # 策略2: 去除标点符号匹配
    # 策略3: 前缀匹配
    # 策略4: 子序列匹配
```

**修复文件**: `app/services/alignment_service.py`
**验证状态**: ✅ 已验证通过

---

### 2.3 问题3: 场景参考图未生成

**发现时间**: 2025-12-15
**问题描述**: `SceneReferenceManager` 未正确生成和管理场景参考图

**修复方案**:
- 为每个唯一的location生成interior和exterior两种参考图
- 使用location的normalized ID作为key存储和检索

**修复文件**: `app/services/scene_reference_manager.py`
**验证状态**: ✅ 已验证通过

---

### 2.4 问题4: 角色参考图未传入场景生成

**发现时间**: 2025-12-15
**问题描述**: 生成场景图片时，角色参考图没有正确传入，导致角色外观不一致

**修复方案**:
```python
# 在生成场景图片时，合并角色参考图和场景参考图
char_refs = ref_manager.get_references_for_scene(chars_in_scene)
scene_refs = scene_ref_manager.get_references_for_location(location_id)
all_refs = char_refs + scene_refs

result = await image_gen.generate_shot_image(
    shot=shot,
    reference_images=all_refs,
    ...
)
```

**验证状态**: ✅ 已验证通过

---

### 2.5 问题5: image_prompt 未使用

**发现时间**: 2025-12-16
**问题描述**: shots.json中有LLM生成的`image_prompt`字段，但图片生成时没有使用

**背景**:
- `build_image_prompt()` 函数的system prompt指示LLM生成详细的image_prompt
- 但实际图片生成时使用的是简化的`visual_description`

**修复方案**:
新增 `generate_shot_image()` 方法，优先使用shot的`image_prompt`字段：

```python
# image_generator.py
async def generate_shot_image(
    self,
    shot: dict,
    reference_images: Optional[List[Image.Image]] = None,
    aspect_ratio: str = "16:9",
    use_llm_translation: bool = True,
    **kwargs
) -> dict:
    """
    生成单个shot的场景图片
    优先使用shot的image_prompt字段，并自动翻译为英文
    """
    image_prompt = shot.get('image_prompt', '')
    # 翻译 + 生成
```

**修复文件**: `app/services/image_generator.py`
**验证状态**: ✅ 已验证通过

---

### 2.6 问题6: image_prompt 未完全翻译成英文

**发现时间**: 2025-12-16
**问题描述**: shots.json中的image_prompt包含大量中文，影响Gemini图片生成效果

**问题示例**:
```
之前的image_prompt:
"Shot type: 中景. Camera angle: 平视.
Setting: 现代简约咖啡馆靠窗位置，米色墙面，木质桌椅...
Characters: 苏晨: jet black hair, dark brown eyes."
```

**根因分析**:
1. LLM拆分场景时使用中文prompt，导致输出的shot_type、camera_angle是中文
2. `_build_shot_prompt()` 方法直接使用中文的location、time、mood
3. 角色名使用中文而非英文名

**修复方案**:

#### 修复点1: 修改LLM拆分prompt为英文
```python
# storyboard_service.py - _split_scene_to_shots()
prompt = f"""You are a professional storyboard artist.
Split the following scene into {estimated_shots} independent shots.

## Output Format
{{
  "shots": [
    {{
      "shot_type": "wide shot/medium shot/close-up/...",
      "visual_description": "MUST BE IN ENGLISH...",
      "camera_angle": "eye level/low angle/high angle/side view"
    }}
  ]
}}

IMPORTANT:
- visual_description MUST be written entirely in English
- shot_type MUST be in English
- camera_angle MUST be in English
"""
```

#### 修复点2: 添加镜头术语翻译函数
```python
def _translate_shot_type(self, shot_type: str) -> str:
    translations = {
        "全景": "wide shot",
        "中景": "medium shot",
        "特写": "close-up",
        "中近景": "medium close-up",
        ...
    }
    return translations.get(shot_type, shot_type)

def _translate_camera_angle(self, camera_angle: str) -> str:
    translations = {
        "平视": "eye level",
        "仰拍": "low angle",
        "俯拍": "high angle",
        ...
    }
    return translations.get(camera_angle, camera_angle)
```

#### 修复点3: 修改 _build_shot_prompt() 使用英文
```python
def _build_shot_prompt(self, shot, characters, ...):
    shot_type_en = self._translate_shot_type(shot_type)
    camera_angle_en = self._translate_camera_angle(camera_angle)

    prompt_parts = [
        visual_desc,
        f"Shot type: {shot_type_en}",
        f"Camera angle: {camera_angle_en}",
    ]
```

**修复文件**: `app/services/storyboard_service.py`
**验证状态**: ✅ 已验证通过

---

### 2.7 问题7: 角色外观相似度过高

**发现时间**: 2025-12-16
**问题描述**:
- 两个女性角色外观太相似，都穿职业装
- 林薇应该是"自由插画师，随性穿着"，但生成的图片显示为职业装

**根因分析**:
- `_build_shot_prompt()` 中的角色描述过于简化
- 只使用了 `description` 字段，没有使用详细的 `clothing` 和 `physical` 字段

**修复方案**:
新增 `_build_character_description()` 方法，构建详细的角色外观描述：

```python
def _build_character_description(self, character: dict) -> str:
    """从角色数据构建详细的外观描述"""
    desc_parts = []

    # 1. 物理外观 (physical)
    physical = character.get('physical', {})
    if physical:
        hair_color = physical.get('hair_color', '')
        hair_style = physical.get('hair_style', '')
        if hair_color or hair_style:
            desc_parts.append(f"{hair_color} {hair_style}".strip())

        eye_color = physical.get('eye_color', '')
        if eye_color:
            desc_parts.append(f"{eye_color} eyes")

    # 2. 服装 (clothing)
    clothing = character.get('clothing', {})
    if clothing:
        top = clothing.get('top', '')
        if top:
            desc_parts.append(f"wearing {top}")

        bottom = clothing.get('bottom', '')
        if bottom:
            desc_parts.append(bottom)

        accessories = clothing.get('accessories', [])
        if accessories:
            desc_parts.append(", ".join(accessories[:3]))

        style = clothing.get('style', '')
        if style:
            desc_parts.append(f"{style} style")

    return ", ".join(desc_parts)
```

**修复后的角色描述示例**:
```
苏晨 (Su Chen):
jet black short straight bob with soft layers, deep dark brown eyes,
fair skin, wearing light gray fitted blazer over cream silk camisole,
charcoal gray tailored trousers, simple silver stud earrings,
minimalist silver wristwatch, small black crossbody bag,
professional elegant style

林薇 (Lin Wei):
chestnut brown long wavy hair with natural highlights,
warm honey brown eyes, fair skin, wearing soft beige knit sweater
with texture, long cream linen skirt, colorful beaded hand bracelet
in rainbow colors, canvas tote bag with art prints,
small silver pendant necklace, casual artistic style
```

**修复文件**: `app/services/storyboard_service.py`
**验证状态**: ✅ 已验证通过

---

### 2.8 问题8: 角色穿着在不同shot间不一致

**发现时间**: 2025-12-16
**问题描述**: 同一角色在不同shot中的穿着/配饰发生变化，不符合逻辑

**根因分析**: 与问题7相同 - 角色描述不够详细和一致

**修复方案**: 通过问题7的修复，每个shot中都包含完整且一致的角色外观描述

**验证状态**: ✅ 已验证通过

---

### 2.9 问题9: 苏晨发型在各shot间不一致

**发现时间**: 2025-12-16
**问题描述**: 苏晨的短发样式在每个shot中都有所不同

**根因分析**: 与问题7相同 - 发型描述不够详细

**修复方案**:
- 在 `_build_character_description()` 中优先提取 `physical.hair_style` 和 `physical.hair_color`
- 确保每个shot的prompt中包含一致的发型描述

**验证状态**: ✅ 已验证通过

---

## 三、测试故事汇总

### 3.1 teststory6_verify_fixes

**故事主题**: 深夜地铁末班车
**测试目的**: 验证4个核心修复点
1. characters_in_scene 正确继承
2. 音画对齐准确
3. 场景参考图生成
4. 角色参考图传入场景生成

**测试结果**: ✅ 全部通过

---

### 3.2 teststory6.1 (最新)

**故事主题**: 咖啡馆的重逢
**角色设定**:
- 苏晨（女，28岁）— 互联网公司产品经理，职业装扮
- 林薇（女，28岁）— 自由插画师，穿着随性

**测试目的**: 验证6个验证点
1. characters_in_scene 正确继承
2. 音画对齐准确
3. 场景参考图生成
4. 角色参考图传入场景生成
5. [新增] 使用shot的image_prompt生成图片
6. [新增] prompt自动翻译为英文

**生成参数**:
- 时长: 2分钟以内
- 角色数: 2个人类角色
- 场景数: 8个scene → 16个shot
- 风格: realistic

**测试结果**: ✅ 全部6个验证点通过

**输出目录**: `test_output/manualtest/teststory6.1/`

**生成文件清单**:
```
teststory6.1/
├── story.json          # 故事数据
├── shots.json          # 分镜数据 (image_prompt已为英文)
├── narration.mp3       # TTS语音
├── whisper.json        # Whisper时间戳
├── timeline.json       # 音画对齐结果
├── verification_results.json
├── character_refs/     # 角色参考图
│   ├── char_001_portrait.png
│   ├── char_001_fullbody.png
│   ├── char_002_portrait.png
│   └── char_002_fullbody.png
├── scene_refs/         # 场景参考图 (16张)
│   ├── *_interior.png
│   └── *_exterior.png
└── images/             # 场景图片
    ├── shot_01.png
    ├── shot_02.png
    ├── ...
    └── shot_08.png
```

---

## 四、代码修改汇总

### 4.1 修改的文件

| 文件 | 修改内容 |
|------|----------|
| `app/services/storyboard_service.py` | LLM拆分prompt改为英文、添加翻译函数、增强角色描述 |
| `app/services/image_generator.py` | 新增 `generate_shot_image()` 方法 |
| `app/services/alignment_service.py` | 繁简转换、多策略文本匹配 |
| `app/prompts/storyboard_prompts.py` | 添加翻译函数和字典 |

### 4.2 新增的函数

```python
# storyboard_service.py
def _translate_shot_type(shot_type: str) -> str
def _translate_camera_angle(camera_angle: str) -> str
def _translate_text_simple(text: str) -> str
def _build_character_description(character: dict) -> str

# image_generator.py
async def generate_shot_image(shot, reference_images, aspect_ratio, use_llm_translation) -> dict

# alignment_service.py
def _convert_to_simplified(text: str) -> str

# storyboard_prompts.py
SHOT_TYPE_TRANSLATIONS = {...}
CAMERA_ANGLE_TRANSLATIONS = {...}
MOOD_TRANSLATIONS = {...}
async def translate_image_prompt_to_english(prompt, client, preserve_text_in_image) -> str
def _simple_translate_prompt(prompt: str) -> str
def prepare_shot_prompt_for_generation(shot, client) -> str
async def prepare_shot_prompt_for_generation_async(shot, client, style_enforcer) -> str
```

---

## 五、测试脚本

### 5.1 tests/test_verify_fixes.py
验证4个基础修复点的测试脚本

### 5.2 tests/test_story6_1.py
验证6个完整验证点的测试脚本，包含新增的image_prompt使用和翻译功能

### 5.3 tests/test_prompt_translation.py
专门测试prompt翻译功能的测试脚本

---

## 六、已知限制与后续优化建议

### 6.1 当前限制

1. **角色一致性仍依赖参考图质量**: 即使prompt描述一致，Gemini生成的图片仍可能有差异
2. **繁简转换不完整**: `_convert_to_simplified()` 中的字典可能遗漏某些繁体字
3. **LLM翻译可能失败**: 当Gemini API返回空响应时，会回退到简单字典翻译

### 6.2 后续优化建议

1. **引入面部一致性技术**: 考虑使用IP-Adapter或其他面部保持技术
2. **增加翻译质量检查**: 验证翻译后的prompt是否仍包含中文
3. **缓存角色描述**: 避免每次都重新构建角色描述
4. **优化参考图使用策略**: 根据shot类型智能选择传入的参考图数量

---

## 七、总结

本次测试周期从"深夜地铁末班车"idea出发，经过多轮迭代，完成了以下工作：

1. **发现并修复9个问题**
2. **新增4个核心功能函数**
3. **优化了角色一致性描述机制**
4. **实现了image_prompt的纯英文输出**
5. **完成了完整的端到端测试验证**

所有6个验证点均已通过测试，系统已准备好进行更多故事的生成测试。

---

**报告编写**: Claude (Anthropic)
**最后更新**: 2025-12-16 20:35 CST
