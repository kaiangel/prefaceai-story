# Phase 2.0 进度记录：从 6.4 到最新测试

> 记录从 teststory6.4 角色一致性突破到 Phase 2.0 架构完善的全部改进
> 日期范围：2025-12-23 ~ 2025-01-05
> 状态：持续更新

---

## 一、里程碑概览

| 版本/日期 | 里程碑 | 核心改进 |
|----------|--------|---------|
| 6.4 (12-23) | 角色一致性突破 | 混合模型架构 (Flash参考图 + Pro shots) |
| 6.5-6.6 (12-23) | 跨题材验证 | 武侠水墨、6人家庭场景验证通过 |
| Phase 2.0 (12-29) | 5阶段流水线 | 完整的 Outline→Character→Screenplay→Storyboard→Image 流程 |
| 12-30 | 风格锁定 | StyleEnforcer 在 Shot 生成中强制风格 |
| 12-31 | 中文泄露修复 | Stage 1/3 输出英文的 key_visual_elements 和 mood |
| 01-05 | 场景连续性增强 | VISUAL CONTINUITY REFERENCE 指令 + IMAGE 编号修复 |

---

## 二、角色一致性突破 (6.4-6.6)

### 2.1 问题背景

使用 Gemini 2.5 Flash Image 生成所有图片时：
- 3人场景一致性：~70%
- 6人场景一致性：<60%
- 核心问题：Flash 模型只能"看到"参考图，无法理解角色身份边界

### 2.2 解决方案：混合模型架构

```
参考图生成 (Flash) ──┬── 速度快、成本低
                     └── 单角色任务，无混淆风险

Shot生成 (Pro) ──────┬── 理解每个角色的身份边界
                     └── 不会混淆角色特征
```

### 2.3 验证结果

| 测试 | 风格 | 角色数 | 一致性 |
|------|------|--------|--------|
| teststory6.4 咖啡馆告别 | realistic | 3人 | **100%** |
| teststory6.5 武侠水墨 | ink | 3人 | **100%** |
| teststory6.6 家庭聚会 | realistic | 6人 | **~90%** |

### 2.4 成本影响

| 方案 | 60 shots 成本 | 一致性 |
|------|--------------|--------|
| 全 Flash | $3.11 | ~70% |
| 混合架构 | $9.35 | 100% |
| 差价 | +$6.24 | 用户体验质的飞跃 |

---

## 三、Phase 2.0 五阶段流水线

### 3.1 架构设计

```
Stage 1: StoryOutlineGenerator
├── 输入: idea + style_preset + target_duration
├── 输出: title, logline, characters_overview, plot_points, unique_locations
└── 模型: Gemini 3 Flash

Stage 2: CharacterDesigner
├── 输入: outline
├── 输出: characters (physical, clothing, personality)
└── 模型: Gemini 3 Flash

Stage 3: ScreenplayWriter
├── 输入: outline + characters
├── 输出: scenes (action_beats, narration, atmosphere)
└── 模型: Gemini 3 Flash

Stage 4: StoryboardDirector
├── 输入: screenplay + characters + visual_tone
├── 输出: shots (camera, composition, lighting, image_prompt)
└── 模型: Gemini 3 Flash

Stage 5: ShotImageGenerator
├── 输入: shots + character_refs + scene_refs + previous_shot_image
├── 输出: PNG images
└── 模型: Gemini 3 Pro Image (关键！)
```

### 3.2 关键设计决策

1. **Pro 模型仅用于 Shot 生成**：成本敏感，但一致性是产品生命线
2. **参考图分离管理**：ReferenceImageManager + SceneReferenceManager
3. **风格强制锁定**：StyleEnforcer 在每个 prompt 开头注入 MANDATORY STYLE
4. **连续性参考**：传入 previous_shot_image 保持场景连贯

---

## 四、风格锁定与中文泄露修复 (12-30 ~ 12-31)

### 4.1 问题：Shot 生成风格漂移

**症状**：realistic 风格的故事中出现卡通化的 shot

**根因**：`generate_shot_image_phase2()` 未调用 StyleEnforcer

**修复**：
```python
# image_generator.py:408
full_prompt = StyleEnforcer.enforce_prompt(full_prompt, style_preset)
```

### 4.2 问题：中文泄露到图像 Prompt

**症状**：Gemini 生成图像时对中文理解偏差

**泄露点**：
- Stage 1: `key_visual_elements` 中文示例
- Stage 3: `atmosphere.mood` 中文示例

**修复**：修改 LLM prompt 模板，要求输出英文
```python
# story_outline_generator.py:237
"key_visual_elements": ["visual element 1 in English", "visual element 2 in English"]

# screenplay_writer.py:398
"mood": "tense / melancholic / hopeful / peaceful (English only, for image generation)"
```

---

## 五、场景连续性增强 (01-05)

### 5.1 问题发现

当 Shot 2+ 接收 previous_shot_image 作为参考时：
1. **无使用指令**：模型不知道如何使用这张图
2. **可能过度复制**：模型可能直接复制前序 shot 的构图
3. **IMAGE 编号错误**：prompt 中的 "Image N" 与 contents 数组位置不对应

### 5.2 解决方案

#### 5.2.1 添加 VISUAL CONTINUITY REFERENCE 指令

```python
# storyboard_prompts.py:1420-1443
if has_previous_shot_image:
    context_parts.append("""
═══════════════════════════════════════════════════════════
VISUAL CONTINUITY REFERENCE (CRITICAL)
═══════════════════════════════════════════════════════════

A previous shot image is provided (Image 1) showing the same location.

MUST MAINTAIN (environment continuity):
- Location identity and architectural details
- Lighting direction and color temperature
- Weather conditions (rain intensity, wet surfaces, fog density)
- Time-of-day atmosphere and ambient lighting

MUST VARY (cinematic storytelling - follow THIS shot's instructions):
- Camera angle and shot size (as specified in THIS shot's camera settings)
- Character positioning and poses (based on THIS shot's action description)
- Composition and framing (create visual variety, don't copy previous layout)
- Focal point (based on THIS shot's narrative emphasis)

⚠️ IMPORTANT: The previous shot is for ENVIRONMENT reference only.
Do NOT replicate its framing, composition, or character positions.
═══════════════════════════════════════════════════════════
""")
```

#### 5.2.2 修复 IMAGE 编号映射

```python
# storyboard_prompts.py:1481-1530
def build_character_reference_mapping_phase2(
    characters_in_shot: List[str],
    characters_data: List[dict],
    has_previous_shot: bool = False,  # 新增
    scene_ref_count: int = 0          # 新增
) -> str:
    """
    正确对应 contents 数组的图像顺序：
    - Image 1: Previous shot (如有)
    - Images N-N+1: Character portrait + fullbody (每角色2张)
    - Images M-M+X: Scene references
    """
```

#### 5.2.3 调用方传参更新

```python
# image_generator.py:365-380
has_previous_shot_image = previous_shot_image is not None
char_refs_count = len(characters_in_shot) * 2
scene_ref_count = max(0, total_refs - char_refs_count)

prompt_package = prompt_builder.build_full_prompt(
    shot=shot,
    previous_shot=previous_shot,
    screenplay=screenplay,
    include_system_instruction=True,
    has_previous_shot_image=has_previous_shot_image,
    scene_ref_count=scene_ref_count
)
```

### 5.3 验证结果

**Shot 1 prompt** (无前序图像)：
```
has_previous_shot_image: False
REFERENCE IMAGES IN ORDER:
- Image 1: Scene reference (interior or exterior)
```

**Shot 2 prompt** (有前序图像)：
```
has_previous_shot_image: True
REFERENCE IMAGES IN ORDER:
- Image 1: Previous shot (ENVIRONMENT reference only, do NOT copy composition)

CHARACTER REFERENCES:
- Images 2-3: Chen Mo - portrait + fullbody

SCENE REFERENCES:
- Image 4: Scene reference

[CONTINUITY]
═══════════════════════════════════════════════════════════
VISUAL CONTINUITY REFERENCE (CRITICAL)
═══════════════════════════════════════════════════════════
...
```

---

## 六、测试验证记录

### 6.1 20251231_181728 (3-shot 验证测试)

| 项目 | 值 |
|------|-----|
| 故事 | 终点站前的余温 |
| 风格 | realistic |
| Shot 数 | 3 (验证用) |
| 角色数 | 3 |
| 结果 | ✅ 全部生成成功 |

**验证点**：
- [x] Shot 1 无 VISUAL CONTINUITY 块（正确，无前序图像）
- [x] Shot 2 有 VISUAL CONTINUITY 块（正确，有前序图像）
- [x] IMAGE 编号正确映射 contents 数组

### 6.2 01-05 继续生成 Shot 4-10

| Shot | 角色 | 状态 |
|------|------|------|
| 4 | char_003 | ✅ |
| 5 | char_001, char_002, char_003 (3人同框) | ✅ |
| 6-7 | char_001 | ✅ |
| 8-9 | char_002 | ✅ |
| 10 | char_003 | ✅ |

所有 shot 均使用 `has_continuity: True`，前序图像参考生效。

---

## 七、关键文件变更清单

| 文件 | 变更 | 日期 |
|------|------|------|
| `image_generator.py` | 添加 StyleEnforcer 调用 | 12-30 |
| `image_generator.py` | 计算 has_previous_shot_image 和 scene_ref_count | 01-05 |
| `storyboard_prompts.py` | 添加 VISUAL CONTINUITY REFERENCE 块 | 01-05 |
| `storyboard_prompts.py` | 修复 build_character_reference_mapping_phase2 参数 | 01-05 |
| `story_outline_generator.py` | key_visual_elements 示例改英文 | 12-31 |
| `screenplay_writer.py` | atmosphere.mood 示例改英文 | 12-31 |

---

## 八、已知遗留问题

### 8.1 已解决

| 问题 | 解决日期 |
|------|---------|
| Shot 生成风格漂移 | 12-30 |
| 中文泄露到图像 prompt | 12-31 |
| 前序 Shot 图像缺少使用指令 | 01-05 |
| IMAGE 编号与 contents 不对应 | 01-05 |

### 8.2 待观察

| 问题 | 状态 |
|------|------|
| 7-8 人场景一致性上限 | 未测试 |
| 角色对话生成 | 未实现 |

---

## 九、性能指标

### 9.1 生成速度

| 阶段 | 耗时 |
|------|------|
| Stage 1 (Outline) | ~5秒 |
| Stage 2 (Characters) | ~8秒 |
| Stage 3 (Screenplay) | ~20秒 |
| Stage 4 (Storyboard) | ~30秒 |
| Stage 5 (Images, 10 shots) | ~200秒 |
| **总计 (10 shots)** | **~4分钟** |

### 9.2 成本估算 (10 shots)

| 项目 | 成本 |
|------|------|
| 参考图 (Flash) | ~$0.10 |
| Shot 图 (Pro) | ~$1.45 |
| 文本生成 | ~$0.05 |
| **总计** | **~$1.60** |

---

## 十、下一步计划

1. **完整故事测试**：生成完整 27 shots，验证端到端质量
2. **角色对话生成**：Stage 3 增加 dialogue 字段
3. **Batch API 集成**：降低 50% Pro 模型成本
4. **视频合成**：集成 TTS + 音画对齐 + 视频输出

---

*文档作者：Claude Code*
*创建日期：2025-01-05*
*最后更新：2025-01-05*
