# Known Issues / TODO

> 发现但尚未解决的问题，按优先级排序

---

## 高优先级

### KI-001: StageD "重新生成"按钮未接通后端（纯 UI 壳）

**发现日期**: 2026-04-14 | **发现者**: PM + Founder 联调
**优先级**: P0（DEC-011 用户旅程 Stage D 核心功能）
**影响范围**: Frontend (StageD.tsx) + Backend (chapters.py) + Pipeline 集成

**问题描述**:
StageD 故事预览页的"重新生成"按钮当前是**纯前端 UI 壳**，无法实际重新生成 shot 图片。用户点击后图片消失（`imageUrl: null`），但不会调用后端 API 重新生图。

**断裂点清单**（共 5 个）:

| # | 断裂点 | 当前代码位置 | 问题详情 |
|---|--------|-------------|---------|
| 1 | **前端不调 API** | `StageD.tsx:33-35` `handleRegenerate()` | 只 dispatch `REGENERATE_SHOT` action，reducer 只做 `imageUrl: null`（清空图片），**没有任何 fetch 调用后端** |
| 2 | **后端 API 用旧 Pipeline** | `chapters.py:636-696` `regenerate_single_image_task()` | 调用 `StoryboardService` + `image_generator.generate_image()`，这是**Phase 1.0 旧版方法**，不是 Phase 2.0 的 `generate_shot_image_phase2()` |
| 3 | **后端无参考图** | `chapters.py:690-696` | 旧的 `generate_image()` 不接受 `reference_images` 参数。没有角色参考图 = 角色一致性完全丢失。也没有 StyleEnforcer、没有 Phase2PromptBuilder |
| 4 | **接口 ID 不匹配** | 前端 `shotId` vs 后端 `scene_id` | 前端按 `shotId` 操作（一个 shot 对应一张图），后端 API 按 `scene_id` 操作（一个 scene 有多个 shot）。路由是 `/{chapter_number}/images/{scene_id}/regenerate`，缺少 shot 级粒度 |
| 5 | **无 Schema 验证** | `chapters.py:678-687` | 旧版重新生成不经过 `pipeline_schemas.py` 的 Pydantic 验证，可能产出不合规数据 |

**修复方案（需 Backend + Frontend 配合）**:

**Backend**:
1. 新建 `POST /api/projects/{project_id}/chapters/{chapter_number}/shots/{shot_id}/regenerate` 端点
2. 从 DB 读取该 shot 的 `storyboard_json`（含 `image_prompt`、`camera`、`character_direction` 等完整数据）
3. 从 DB 读取角色参考图路径（`character_refs`）和场景参考图路径（`scene_refs`）
4. 调用 `image_generator.generate_shot_image_phase2()`（Phase 2.0 方法），传入完整参考图 + StyleEnforcer
5. 通过 `pipeline_schemas.py` 验证 shot 数据格式
6. 保存新图片，返回新 `imageUrl`

**Frontend**:
1. `handleRegenerate()` 改为调用新的 shot 级 API
2. 调用期间显示 loading 状态（spinner / skeleton）
3. API 返回后更新 `imageUrl`
4. 错误处理（API 失败时恢复原图 + toast 提示）

**验收标准**:
- [ ] 点"重新生成"后调用后端 API
- [ ] 后端用 Phase 2.0 Pipeline（`generate_shot_image_phase2`）
- [ ] 传入角色参考图 + 场景参考图 + StyleEnforcer
- [ ] 生成的新图角色一致性与原图一致
- [ ] 前端显示 loading → 新图片
- [ ] Shot 级粒度（不是 scene 级）

---

### KI-002: StageD 旁白编辑不回写 DB，重新生成不使用编辑后内容

**发现日期**: 2026-04-14 | **发现者**: PM + Founder 联调
**优先级**: P0（DEC-011 用户旅程 Stage D 核心功能）
**影响范围**: Frontend (StageD.tsx + CreateContext.tsx) + Backend

**问题描述**:
StageD 故事预览页的"编辑"按钮可以修改旁白文字（`narrationSegment`），但改动**只存在于前端内存**（React state），不会写回 DB。且"重新生成"按钮（KI-001）与编辑功能互不关联——即使修复了重新生成，也不会使用用户编辑后的旁白内容。

**断裂点清单**（共 3 个）:

| # | 断裂点 | 当前代码位置 | 问题详情 |
|---|--------|-------------|---------|
| 1 | **编辑只改前端 state** | `StageD.tsx:144-156` + `CreateContext.tsx:242-252` | `UPDATE_SHOT_TEXT` action 只更新 React state 中的 `narrationSegment`，**没有调 API 写回 DB** |
| 2 | **刷新页面丢失编辑** | — | 用户编辑旁白后刷新页面，改动全部丢失（state 重置从 DB 读取原始数据） |
| 3 | **重新生成不读编辑后内容** | `chapters.py:659-687` | 即使重新生成能工作（KI-001 修复后），后端从 `chapter.scenes_json` / `chapter.storyboard_json` 读取原始数据，不会读取前端编辑后的 `narrationSegment` |

**修复方案**:

**Backend**:
1. 新建 `PATCH /api/projects/{project_id}/chapters/{chapter_number}/shots/{shot_id}` 端点
2. 接受 `{ narrationSegment?: string, chineseText?: string }` 请求体
3. 更新 DB 中 `storyboard_json` 对应 shot 的字段
4. 返回更新后的 shot 数据

**Frontend**:
1. 编辑完成后（用户点"完成"按钮时）调用 PATCH API 回写 DB
2. 乐观更新：先更新本地 state，API 失败时回退
3. "重新生成"时将最新的 `narrationSegment` 传给后端（如果旁白影响 text_overlay，后端需要用编辑后的版本重新渲染文字）

**注意**:
- `narrationSegment` 是中文旁白（用于 TTS），不进入 `image_prompt`（英文图像生成）
- 但 `narrationSegment` 影响 `text_overlay`（条漫文字渲染）——如果用户编辑了旁白，重新生成时的文字叠加应该用编辑后的版本
- `image_prompt` 本身不需要根据旁白编辑而变化（图像构图由 Stage 4 storyboard 决定，与旁白文字无关）

**验收标准**:
- [ ] 编辑旁白后点"完成"→ 调 PATCH API 写回 DB
- [ ] 刷新页面后编辑内容不丢失
- [ ] 重新生成时的 text_overlay 使用编辑后的旁白
- [ ] 编辑不影响 image_prompt（图像构图不变）

---

### KI-003: StageD "删除" shot 未接通后端

**发现日期**: 2026-04-14 | **发现者**: PM 代码审查
**优先级**: P1
**影响范围**: Frontend (StageD.tsx) + Backend

**问题描述**:
`handleDelete(shotId)` 只 dispatch `DELETE_SHOT` action，reducer 做 `shots.filter(s => s.shotId !== action.payload)`（从前端 state 移除）。**没有调 API 通知后端**，刷新页面后 shot 重新出现。

**修复方案**: 新建 `DELETE /api/projects/{project_id}/chapters/{chapter_number}/shots/{shot_id}` 端点，标记 shot 为 deleted（软删除）。

---



### 2. ~~【系统性问题】图像生成prompt中的中文泄露~~ ✅ 已解决

**发现日期**: 2025-12-31 | **解决日期**: 2025-12-31

**解决方案**: 修改 Stage 1/3 的 LLM prompt 模板，要求输出英文
- `story_outline_generator.py:234-237` - key_visual_elements 示例改为英文
- `screenplay_writer.py:398` - atmosphere.mood 示例改为英文

**问题描述（存档）**:
多个Stage的数据字段包含中文，但被直接传入图像生成prompt，导致Gemini理解偏差或风格漂移。这是一个**系统性问题**，涉及多个文件和数据路径。

---

#### 2.1 完整泄露点审计表

| Stage | 文件:行号 | 字段 | 数据来源 | 示例值 |
|-------|----------|------|---------|--------|
| Stage 1 | `scene_reference_manager.py:656-657` | `key_visual_elements` | `unique_locations` | `["玻璃上的雨痕", "昏黄的候车灯"]` |
| Stage 1 | `scene_reference_manager.py:410,663` | `atmosphere` | `representative_scene.mood` | `"压抑、凄凉"` |
| Stage 3 | `storyboard_prompts.py:1343-1345` | `mood` | `scene.atmosphere.mood` | `"压抑、凄凉、无助"` |
| Stage 3 | `storyboard_service.py:1216` | `mood` | `scene.mood` | `"紧张"` |
| Stage 3 | `character_consistency.py:397-399` | `self.mood` | 场景mood | `"孤独"` |

---

#### 2.2 数据流追踪

```
Stage 1 (story.json)
├── unique_locations.key_visual_elements  ←── 中文
├── unique_locations.display_name         ←── 中文（用于识别，不直接进prompt）
└── scenes[].mood                         ←── 中文

     ↓

Stage 3 (screenplay.json)
└── scenes[].atmosphere.mood              ←── 中文（继承自Stage 1）

     ↓

图像生成 Prompt
├── scene_reference_manager._build_anchor_prompt()
│   ├── key_visual_elements → "KEY VISUAL ELEMENTS:\n- 玻璃上的雨痕"  ❌
│   └── atmosphere → "desolate atmosphere"  ← 如果是中文则 ❌
│
├── storyboard_prompts.build_narrative_context_phase2()
│   └── mood → "SCENE ATMOSPHERE: 压抑、凄凉、无助"  ❌
│
├── storyboard_service._build_atmosphere()
│   └── mood → "ATMOSPHERE: 紧张 mood"  ❌
│
└── character_consistency.SceneDescription.to_prompt()
    └── self.mood → "Atmosphere: 孤独"  ❌
```

---

#### 2.3 修复方案（简化版）

**直接源头改英文**（不需要双语字段）：

这些字段目前**只用于图像生成**，不用于TTS/UI，所以直接输出英文即可：

```
Stage 1 - story_outline_generator.py:237 修改：
"unique_locations": [
  {
    "location_id": "bus_stop_night",
    "display_name": "深夜公交站",           // 保留中文（仅用于开发者识别）
    "key_visual_elements": [                // 直接输出英文（当前是中文示例）
      "raindrops streaking down glass",
      "dim yellow waiting area lights",
      "distant blurred neon reflections"
    ]
  }
]

Stage 3 - screenplay_writer.py:398 修改：
"atmosphere": {
  "mood": "oppressive, desolate, helpless"  // 直接输出英文（当前是"氛围情绪"）
}
```

**理由**：
1. 这些字段目前只用于图像生成，不用于TTS/UI
2. 避免所有使用点改为 `xxx_en`
3. 减少数据冗余
4. 符合"无后缀=英文"的命名规范

---

#### 2.4 排除的字段（无需修复）

| 字段 | 原因 |
|------|------|
| `action_beat.action` | 作为Stage 4 LLM输入，LLM输出英文`image_prompt`，不直接进入图像生成 |
| `display_name` | 有description时用英文；无description时有`_clean_location_name()`翻译层 |
| `character.personality` | Stage 2输出已是英文 |
| `narration` | 用于TTS，不进入图像生成 |

---

## 中优先级

### 1. 【功能缺失】Stage 3 不生成角色对话

**发现日期**: 2025-01-06

**问题描述**:
当前 Stage 3 (ScreenplayWriter) 生成的剧本只包含旁白和动作描述，**没有角色对话**。整个故事是"默片+旁白"模式，角色之间没有任何语言交流。

---

#### 1.1 当前 Stage 3 完整输出结构

以测试故事 `20251231_181728` 的 Scene 2 为例：

```json
{
  "scene_id": 2,
  "scene_heading": "EXT. URBAN BUS STOP - NIGHT - HEAVY RAIN",
  "plot_point": "first_turn",
  "location_id": "urban_bus_stop",
  "time_of_day": "深夜",
  "weather": "暴雨",
  "lighting_condition": "昏暗的街灯穿过雨幕，站台顶棚散发着惨白的荧光，手机屏幕的冷光映在脸上",
  "atmosphere": {
    "mood": "melancholic",
    "sound_design_hint": "密集的雨滴撞击金属顶棚的声音，低沉的抽泣声，手机按键的轻微嘀嗒声，保温杯旋开的摩擦声",
    "temperature_feel": "阴冷潮湿"
  },
  "characters_in_scene": ["char_001", "char_002", "char_003"],
  "action_beats": [
    {
      "beat_id": "2a",
      "action": "陈默低头盯着那只老式银色腕表，秒针迟缓地走动，他眉头紧锁，手指在手机屏幕上急促地回复着消息。",
      "duration_hint": 7,
      "emotional_note": "焦躁不安"
    },
    {
      "beat_id": "2b",
      "action": "陈默另一只手攥着那把已经收拢、正不断向地面滴水的黑色折叠伞，伞面在大理石地面上聚起一滩水渍。",
      "duration_hint": 6,
      "emotional_note": "冷漠"
    },
    {
      "beat_id": "2c",
      "action": "林悦蜷缩在长椅最边缘，死死抱着黑色双肩包，包上的猫咪挂件发出微弱且断续的荧光，她低着头，双肩因为抽泣而剧烈颤抖。",
      "duration_hint": 8,
      "emotional_note": "极度悲伤"
    },
    {
      "beat_id": "2d",
      "action": "林悦颈间缠绕的有线耳机随着她的动作晃动，她抬手抹掉脸上的雨水和泪水，却不小心让耳机线缠得更乱了。",
      "duration_hint": 7,
      "emotional_note": "无助"
    },
    {
      "beat_id": "2e",
      "action": "老周沉默地摘下那顶湿透的灰色报童帽，将它压在膝盖上，双手紧紧握着复古保温杯的杯身，像是在汲取最后的温度。",
      "duration_hint": 7,
      "emotional_note": "颓丧"
    }
  ],
  "narration": "在这个被暴雨围困的深夜，窄小的公交站台成了这三个陌生人唯一的避难所，却也更像是一座冰冷的孤岛。陈默不断拨弄着那只银色腕表，机械的滴答声与他手机里疯狂闪烁的消息交织，他手中那把折叠好的黑色雨伞正顺着伞骨淌下冰冷的积水，如同他此刻无法言说的焦灼。不远处的林悦把自己缩成了一个小小的黑影，她紧紧搂住双肩包，那个发光的猫咪挂件在昏暗中忽明忽暗，映照出她颈间杂乱缠绕的耳机线，以及那些被密集雨声掩盖的、支离破碎的抽泣。老周则像是一尊静默的石雕，他缓缓摘下那顶磨损的灰色报童帽，露出写满疲惫的额头，枯槁的手指死死扣住那只褪色的复古保温杯，任由杯中微弱的热气在大雨带来的寒意中迅速消散。他们之间保持着近乎僵硬的社交距离，在这一刻，挫败感在沉默中无声发酵，比外面的暴雨更加让人窒息。",
  "narration_tone": "忧郁而压抑",
  "narration_pace": "缓慢而沉重"
}
```

---

#### 1.2 当前已有的内容维度

| 维度 | 字段 | 用途 | 示例 |
|------|------|------|------|
| 场景设定 | `scene_heading` | 场景标题 | "EXT. URBAN BUS STOP - NIGHT - HEAVY RAIN" |
| 情节点 | `plot_point` | 故事节拍类型 | "first_turn" (第一转折点) |
| 地点 | `location_id` | 场景位置标识 | "urban_bus_stop" |
| 时间 | `time_of_day` | 时间段 | "深夜" |
| 天气 | `weather` | 天气状况 | "暴雨" |
| 光线 | `lighting_condition` | 光照描述 | "昏暗的街灯穿过雨幕..." |
| 氛围情绪 | `atmosphere.mood` | 情绪基调 | "melancholic" |
| 音效提示 | `atmosphere.sound_design_hint` | 环境音描述 | "密集的雨滴撞击金属顶棚的声音..." |
| 温度感 | `atmosphere.temperature_feel` | 体感温度 | "阴冷潮湿" |
| 出场角色 | `characters_in_scene` | 角色ID列表 | ["char_001", "char_002", "char_003"] |
| 动作节拍 | `action_beats` | 动作序列 | 见上方JSON |
| 旁白文本 | `narration` | TTS朗读内容 | 第三人称叙述文本 |
| 旁白语气 | `narration_tone` | 朗读情绪 | "忧郁而压抑" |
| 旁白节奏 | `narration_pace` | 朗读速度 | "缓慢而沉重" |

---

#### 1.3 缺失的内容维度

| 缺失维度 | 说明 | 当前状态 | 影响 |
|----------|------|---------|------|
| **角色对话** | 角色之间的直接语言交流 | ❌ 完全没有 | 故事只能用旁白叙述，无法表现角色互动 |
| **内心独白** | 角色心理活动的第一人称描写 | ❌ 完全没有 | 情感表达只能通过旁白和动作，无法深入角色内心 |
| **对话语气标注** | 对话的情绪/语调指示 | ❌ 完全没有 | 无法指导多角色TTS配音 |
| **对话时机** | 对话在动作中的时间点 | ❌ 完全没有 | 无法确定对话与动作的时序关系 |

---

#### 1.4 具体示例对比

**Shot 09 当前生成内容** (beat_id: 2d):

| 内容类型 | 实际内容 |
|----------|---------|
| action_beat.action | "林悦颈间缠绕的有线耳机随着她的动作晃动，她抬手抹掉脸上的雨水和泪水，却不小心让耳机线缠得更乱了。" |
| action_beat.emotional_note | "无助" |
| narration_segment | "林悦颈间缠绕的有线耳机随着她的动作晃动，她抬手抹掉脸上的雨水和泪水，却不小心让耳机线缠得更乱了。" |
| image_prompt | "A tight close-up of Lin Yue's (char_002) face. Her skin is pale and wet with a mixture of rain and tears. White wired earphones are messily tangled around her neck..." |
| **dialogue** | ❌ **不存在** |

**期望的完整内容**:

```json
{
  "beat_id": "2d",
  "action": "林悦颈间缠绕的有线耳机随着她的动作晃动，她抬手抹掉脸上的雨水和泪水，却不小心让耳机线缠得更乱了。",
  "duration_hint": 7,
  "emotional_note": "无助",
  "dialogue": [
    {
      "character_id": "char_002",
      "character_name": "林悦",
      "line": "怎么又缠住了...",
      "line_type": "self_talk",
      "tone": "低声自语，带着哭腔",
      "volume": "whisper",
      "timing": "mid_action",
      "language": "zh"
    }
  ],
  "inner_monologue": {
    "character_id": "char_002",
    "thought": "为什么今天所有事情都这么糟糕...",
    "emotional_state": "despair"
  }
}
```

---

#### 1.5 功能影响范围

**需要修改的文件**:

| 文件 | 修改内容 |
|------|---------|
| `app/services/screenplay_writer.py` | 修改 prompt 模板，要求 LLM 输出 `dialogue` 字段 |
| `app/services/storyboard_director.py` | 处理对话信息，可能影响 shot 拆分逻辑 |
| `app/prompts/storyboard_prompts.py` | 在 image_prompt 中决定是否体现对话（如嘴部动作） |

**需要新增的功能**:

| 功能 | 说明 |
|------|------|
| 多角色TTS | 不同角色使用不同音色配音 |
| 对话字幕轨道 | 视频中显示角色台词 |
| 对话时序对齐 | 对话音频与画面的精确同步 |
| 嘴部动作提示 | image_prompt 中指示角色是否在说话 |

---

#### 1.6 建议的数据结构扩展

**dialogue 字段完整定义**:

```json
{
  "dialogue": [
    {
      "character_id": "char_002",
      "character_name": "林悦",
      "line": "怎么又缠住了...",
      "line_type": "self_talk | conversation | exclamation | question",
      "tone": "低声自语，带着哭腔",
      "volume": "whisper | normal | loud | shout",
      "timing": "before_action | mid_action | after_action",
      "duration_hint": 2.0,
      "language": "zh",
      "subtitles": {
        "zh": "怎么又缠住了...",
        "en": "Why is it tangled again..."
      }
    }
  ]
}
```

**inner_monologue 字段定义**:

```json
{
  "inner_monologue": {
    "character_id": "char_002",
    "thought": "为什么今天所有事情都这么糟糕...",
    "emotional_state": "despair",
    "show_in_narration": true,
    "show_as_voiceover": false
  }
}
```

---

#### 1.7 优先级说明

**中优先级**，原因：
1. 当前"默片+旁白"模式可以产出可用的短视频
2. 很多短视频类型（风景、美食、氛围向）本身就不需要对话
3. 但缺乏对话会限制：
   - 剧情向短视频的表现力
   - 角色驱动型故事的叙事能力
   - 多人互动场景的真实感

**建议实现顺序**:
1. 先实现 Stage 3 生成 dialogue 字段（纯数据层）
2. 再实现对话字幕显示（视觉层）
3. 最后实现多角色TTS配音（音频层）

---

## 低优先级

（暂无）

---

## 已解决

| 问题 | 解决日期 | 解决方案 |
|------|---------|---------|
| Shot生成风格漂移 | 2025-12-30 | 在 `generate_shot_image_phase2` 中添加 StyleEnforcer |
| Stage 3 LLM自作主张添加道具 | 2025-12-30 | 添加 CHARACTER CONSISTENCY RULES 到 screenplay_writer |
| Stage 4 prompt 中文导致理解偏差 | 2025-12-30 | 将 storyboard_director prompt 改为英文 |
| 图像生成prompt中的中文泄露（系统性） | 2025-12-31 | 修改 Stage 1/3 prompt 模板，要求输出英文的 `key_visual_elements` 和 `atmosphere.mood` |
| 前序Shot图像参考缺少使用指令 | 2025-01-05 | 添加 VISUAL CONTINUITY REFERENCE 指令块到 `build_continuity_context_phase2()` |
| IMAGE编号与contents数组不对应 | 2025-01-05 | 修复 `build_character_reference_mapping_phase2()` 添加 `has_previous_shot` 和 `scene_ref_count` 参数 |
