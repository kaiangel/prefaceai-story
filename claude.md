# 序话Story - 主会话协调者上下文

> 你是序话Story的创始人兼技术负责人。这不是一份工作，这是你的事业。
>
> 完整的角色定义见：`.claude/agents/xuhuastory-boss-coordinator.md`

---

## 当前项目状态（2026-02-24）

| Phase | 状态 | 说明 |
|-------|------|------|
| Phase 1 | ✅ 完成 | idea → story.json，多章节支持 |
| Phase 2 | ✅ 完成 | 5阶段流水线 + 角色一致性突破（3人100%，6人90%） |
| Phase 3 | ✅ 完成 | TTS + Whisper + 音画对齐（误差≤80ms） |
| Phase 4 | ✅ **完成** | 条漫MVP技术验证（V5验收4.9/5）+ TextOverlayService架构重构完成 |
| Phase 4.5 | 🔄 WIP (5%) | 视频合成（FFmpeg集成方案选型中） |
| Phase 5 | ✅ **Landing Page完成** | LP主页5.0/5 + 10个子页面4.8/5（TASK-LP-PAGES + TASK-LP-PAGES-FIX） |
| Phase 6 | 🟡 **已启动** (5%) | Git仓库已初始化（DEC-007），等待后续部署工作 |

### 你的团队（6个专业Agent）

| Agent | 状态 | 当前任务 |
|-------|------|----------|
| Frontend | 🟢 | 空闲（TASK-LP-PAGES-FIX 4.8/5 完成） |
| Backend | 🟢 | 空闲（TASK-SCENE-REF-ASPECT 完成，DEC-010） |
| Tester | 🟢 | 空闲（TASK-REF-PREPROCESS Step4 对比验证完成） |
| AI-ML | 🟢 | 空闲（TASK-REF-PREPROCESS Step1 指定测试shot完成） |
| DevOps | 🟢 | 空闲（TASK-GIT-COMMIT-2 三批提交完成） |
| PM | 🟢 | Coordinator 6项任务完成，等待Founder下一阶段决策 |

### 关键决策
| 决策 | 内容 | 日期 |
|------|------|------|
| DEC-011 | 条漫产品形态定义：交付模式+篇幅选项+短视频模式+用户旅程 | 2026-02-24 |
| DEC-010 | 边缘问题根治：参考图源头统一2:3（scene_reference_manager.py） | 2026-02-24 |
| DEC-009 | 参考图预处理（方案A，已闭环） | 2026-02-13 |
| DEC-008 | Pipeline.tsx → Option A 品牌叙事路线（不暴露技术流程） | 2026-02-12 |
| DEC-007 | Git仓库初始化（仅本地，main分支） | 2026-02-12 |

### 协调相关文件

| 文件 | 用途 |
|------|------|
| `.team-brain/status/TODAY_FOCUS.md` | 今日重点任务 |
| `.team-brain/status/PROJECT_STATUS.md` | 项目状态看板 |
| `.team-brain/handoffs/PENDING.md` | 待处理交接 |
| `.team-brain/decisions/DECISIONS.md` | 决策记录 |
| `.claude/agents/{agent}-progress/` | 各Agent进度 |

---

## 产品定位

序话Story将用户的一句话创意转化为完整的短视频/漫剧/故事。核心价值是**通用性**：支持任何类型的故事（都市情感、古装武侠、童话寓言、科幻冒险）、任何类型的角色（人类、动物、奇幻生物、机器人）、任何视觉风格（写实、卡通、水墨、赛博朋克）。

**用户画像**：无技术背景的短视频创作者、自媒体运营者、内容营销团队。

**核心体验**：输入idea → 自动生成可发布的成片。

---

## 产品设计理念

### 核心设计原则

序话Story的目标是**把专业影视制作能力封装成系统能力**，让普通用户只需要当"制片人"——决定故事方向，剩下的交给系统执行。

**用户关心的是"讲什么故事"，不是"怎么拍"。**

### 专业影视制作流程 vs 序话Story简化流程

专业流程有5个核心环节：
1. **故事大纲（Story Outline）** - 情节骨架、人物设定
2. **分场剧本（Screenplay）** - 每场戏的动作、对白、情绪
3. **分镜脚本（Storyboard）** - 镜头语言：景别、机位、构图、光影
4. **旁白文案（Narration）** - 适合TTS朗读的文学文本
5. **视觉/音频/视频生成**

**序话Story的简化策略**：
- **Phase 1（用户确认）**：故事大纲 - 用户唯一需要深度参与的环节
- **Phase 2-4（系统自动）**：分场剧本、分镜脚本、旁白文案 - 系统自动完成，不打断用户
- **Phase 5+（系统自动）**：生成环节

### 用户旅程设计（DEC-011 落地）

用户全程只当"制片人"——决定方向，系统执行专业制作。五个阶段：

#### Stage A: 输入（Input）

用户提供3项信息，仅第1项必填：

| 输入项 | 方式 | 默认值 | 说明 |
|--------|------|--------|------|
| **故事创意** | 自由文本 | 无（必填） | 一句话或一段描述 |
| **故事篇幅** | 三选一卡片 | 短篇（~18张） | 快闪(~10张) / 短篇(~18张) / 中篇(~36张) |
| **视觉风格** | 风格卡片选择 | 韩漫 | 从已有风格预设中选择，带缩略图预览 |

短视频模式另有时长选择：15秒(~4张) / 1分钟(~15张) / 3分钟(~46张)，每4秒=1 shot。

#### Stage B: 确认（Confirm）

系统生成故事大纲后，用户可选择性调整（全部可跳过）：

| 可调整项 | 交互方式 | 说明 |
|---------|---------|------|
| 角色设定 | 卡片展示，可编辑名字/外貌/性格 | 系统根据 idea 自动生成 |
| 情节走向 | 列表展示，可拖拽调整/删除/新增 | 3-5 个关键情节点 |
| 结局选择 | 2-3 个结局选项 | 系统推荐，用户可自定义 |
| 情绪基调 | 选择题（温馨/紧张/幽默/感人等） | 可跳过，系统自动判断 |

**设计原则**：默认全部"系统推荐"，用户不点就自动往下走。有追求的用户可以深度调整。

#### Stage C: 生成（Generate）

**全自动**，用户只看进度条。系统内部执行 Stage 1-5 流水线。

进度反馈示例：
```
正在构思故事大纲... → 正在设计角色... → 正在编写剧本... → 正在绘制分镜... → 正在生成画面...
```

#### Stage D: 预览（Preview）

生成完成后，用户浏览成果。提供局部调整的"逃生口"：

| 功能 | 优先级 | 说明 |
|------|--------|------|
| 单张 shot 重新生成 | P0 | 不满意某张图 → 点击重新生成 |
| 文字内容编辑 | P0 | 修改旁白/对话文字 |
| BGM 更换 | P1 | 从曲库中选择替换 |
| 删除 shot | P2 | 去掉不需要的画面 |

**设计原则**：不打断主流程，但给用户"微调权"。重新生成单张 shot 的成本很低（1次 Pro API 调用）。

#### Stage E: 交付（Deliver）

两种并行的交付模式（DEC-011）：

| 模式 | 内容 | 用途 |
|------|------|------|
| **打包下载** | 参考图 + 带文字 shot 图 + BGM | 用户二次创作 |
| **视频下载** | shot 图序列 + BGM → 合成视频 | 直接发布到抖音等平台 |

### 产品愿景

**AI时代每个人都会讲故事** —— 专业能力平民化，而不是专业流程简化。

让普通人做出专业成品（短剧、微电影、长剧、漫剧、电影、卡通等），必要的专业流程不省略，但由AI代替人完成。

---

## 技术挑战（按优先级排序）

### 1. 角色一致性（最高优先级）✅ 已解决

同一角色在所有场景图中必须看起来是"同一个人/动物/生物"。这是产品可用性的根基。

**🎉 突破性解决方案（teststory6.4-6.6验证通过）**：

采用**混合模型架构**彻底解决角色一致性问题：
- **参考图生成**：Gemini 2.5 Flash（速度快、成本低）
- **Shot生成**：Gemini 3 Pro Image / Nano Banana Pro（参考图理解能力强）

**验证结果（2025-12-23）**：
| 场景类型 | 一致性 | 测试用例 |
|---------|--------|---------|
| 3人场景 | **100%** | teststory6.4 咖啡馆、teststory6.5 武侠 |
| 6人场景 | **~90%** | teststory6.6 家庭聚会 |
| 跨题材 | **稳定** | 现代都市、武侠古装、写实、水墨 |

**核心原理**：
Pro模型不只是"看到"参考图，而是**理解**每个角色的身份边界，不会混淆角色特征。
Flash模型仅用于参考图生成（无多角色混淆风险），成本仅为Pro的1/3。

**成本对比（60 shots完整故事）**：
- Pro方案：$9.35（100%一致性）
- Flash方案：$3.11（70-80%一致性）
- 差价：+$6.24 (+201%)，但用户体验质的飞跃

**技术实现要点**：
- 串行生成参考图：先肖像 → 用肖像作为参考生成全身图
- 场景图生成时传入角色参考图（仅fullbody）+ 场景参考图
- 详细的角色描述：physical字段（含face_shape, skin_tone, eye_description）+ clothing字段
- `_extract_actual_characters_from_description()` 智能提取实际出场角色
- `_build_identity_line()` 构建含面部特征的身份描述
- StyleEnforcer强制风格锁定，防止写实风格漂移成卡通

**开发时必须遵守**：
- **Shot生成默认使用 Nano Banana 2（`use_pro_model=False`）**，角色一致性 ~95% 与 Pro 持平，速度快 3-5x，成本降 50%。Pro 模型仅作为未来 Premium 用户储备
- 每个shot的prompt必须包含完整的角色外观描述
- 场景图生成必须传入所有出场角色的参考图
- 新增角色类型时，必须在CharacterPromptBuilder中实现对应的描述构建方法

### 2. 风格一致性
整个故事的视觉风格必须统一，不能某张图写实、某张图卡通。

**已实现的解决方案**：
- StyleEnforcer在每个图像prompt开头注入强制风格指令
- 80+风格预设，每个预设有mandatory词和forbidden词
- 场景参考图（interior + exterior）保持环境一致

### 2.1 场景内外景关联（SceneReferenceManager优化）

同一地点的内景和外景在视觉上应保持一致（如：透过玻璃门能看到店内的场景）。

**实现方案（2025-12-23）**：
- 同一location先生成内景，再生成外景
- 生成外景时，把内景作为参考图传入Flash模型
- Prompt中添加通用的内外景一致性指令（不硬编码具体场景类型）

**技术实现要点**：
- `_group_anchors_by_location()` 按location_id分组锚点需求
- `_generate_single_anchor()` 支持传入参考图
- `_build_anchor_prompt()` 添加 `has_interior_reference` 参数
- 外景prompt包含 "INTERIOR-EXTERIOR CONSISTENCY" 指令块

**适用场景类型**：
| 场景类型 | 内景 | 外景 | 关联方式 |
|---------|------|------|---------|
| 现代建筑（咖啡厅、便利店）| 店内布局 | 街边外观 | 玻璃门/窗户透视 |
| 古代建筑（客栈、祠堂）| 大堂内部 | 门楼外观 | 门廊/天井过渡 |
| 自然场景（山洞、树屋）| 洞内/屋内 | 洞口/树下 | 入口区域衔接 |

**注意**：场景参考图使用Flash模型即可，不需要Pro模型（无角色混淆风险）

### 2.2 Shot间连续性

相邻shot之间需要保持场景连贯性（同一地点的光线、天气、环境细节），同时保证构图多样性。

**实现方案（DEC-014, 2026-03-03 更新）**：
- ~~previous_shot_image 已移除~~ — 不再传入前序 shot 图像（DEC-014 Plan A）
- 环境连续性由 **场景参考图** (interior/exterior anchor) + **文字 prompt** 保障
- 构图多样性由 Stage 4 StoryboardDirector 的运镜差异化指令保障（SQ-5）

**移除原因**：
- previous_shot 导致构图感染（模型复制前序 shot 的角度/构图/色调）
- 29 shots 串行传递 = 链式误差放大
- 代码无 location_id 检测，跨场景转场时传入错误图像

**当前参考图传递**：
- 每 shot 传入：角色参考图（每角色 1 张，SQ-2 智能选择）+ 场景参考图（interior/exterior）
- IMAGE 编号：Image 1 = 第一个角色参考图，依次排列，最后为场景参考图
- 不再有 "Image 1 = previous_shot" 的占位

**关键代码位置**：
- `storyboard_prompts.py:1481-1530` - IMAGE 编号映射
- `image_generator.py:756-771` - Contents 数组组装
- `pipeline_orchestrator.py:279-341` - Shot 生成循环（previous_shot 传 None）

### 3. 音画对齐
旁白时间轴与图像停留时长必须精确匹配（误差≤80ms）。

**已实现的解决方案**：
- Whisper提取word-level时间戳
- 多策略文本匹配：精确匹配 → 去标点匹配 → 前缀匹配 → 子序列匹配
- 繁简转换处理（Whisper常输出繁体）

### 4. 条漫文字渲染 ✅ 架构重构完成

条漫/漫画需要在图片中显示对话气泡、心理旁白、叙事旁白等中文文字。

**问题发现（2026-01-22）**：
Gemini Flash 模型无法正确渲染中文文字，所有对话气泡和旁白都是乱码。但基础画面质量优秀（角色一致性4/5、合成效果4/5、表情细腻度4/5）。

**架构重构完成（2026-02-03）**：
TextOverlayService原先分散在8个测试文件中，现已统一到`app/services/text_overlay_service.py`。
- ARCH-1/2/3 架构重构 ✅，CORE-1/2 核心修复 ✅
- V5验收评分 4.9/5（42/42 shots全部通过）
- 所有故事类型自动受益，删除~2075行重复代码

**🎉 技术方案：无文字Prompt + 后处理叠加（V2）**

| 步骤 | 说明 |
|------|------|
| 1. 图像生成 | 使用无文字Prompt模板，生成不含任何文字的干净图片 |
| 2. 后处理叠加 | 使用 TextOverlayServiceV2 程序化叠加中文文字 |

**技术实现要点**：

1. **无文字Prompt模板**（`docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md`）
   ```
   TEXT-FREE IMAGE REQUIREMENT:
   DO NOT include any text, speech bubbles, captions, or written characters.
   Leave clean space at TOP (0-15%) and BOTTOM (80-100%) for text overlay.
   ```

2. **TextOverlayServiceV2** 功能：
   - 顶部/底部/中央黑底旁白（半透明背景 + 白字）
   - 顶部白底叙事旁白（白色背景 + 黑字）
   - 对话气泡（圆角框 + 尾巴指向说话者）
   - **动态气泡位置**：根据 `speaker_position` 参数靠近说话角色
   - **情感强调**：检测 `!!!` 触发红色高亮（如"没一张能看的！！！"）
   - 字体大小：旁白42px、气泡36px

3. **验证结果**（2026-01-22）：
   - 原测试（都市情感 + Korean Webtoon）：✅ 5/5 通过
   - 交叉验证（古风武侠 + 中国水墨）：✅ 5/5 通过
   - 跨题材、跨风格通用性已确认

**关键文件**：
| 文件 | 说明 |
|------|------|
| `docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md` | 无文字Prompt模板（6种场景类型） |
| `docs/COMIC_MVP_PROMPT_TEMPLATES.md` | 带文字Prompt模板（保留用于Pro模型测试） |
| `tests/test_text_overlay_v2.py` | TextOverlayServiceV2 实现和测试 |
| `docs/COMIC_TEXT_OVERLAY_V2_DECISION.md` | V2 决策文档 |
| `.team-brain/analysis/V3_PM_INDEPENDENT_REVIEW_GENERALITY.md` | 🆕 14维度通用性分析（架构重构依据） |

**开发时必须遵守**：
- **条漫模式下，image_prompt 不能包含任何文字生成指令**
- 文字内容由后处理服务添加，不进入图像生成流程
- 保留切换到原生文字渲染的能力（Prompt模板已保留）

---

## 数据流 (Phase 2.0 五阶段架构)

```
idea (用户输入)
    ↓
┌─────────────────────────────────────────────────────────┐
│ Stage 1: StoryOutlineGenerator                          │
│ → 1_outline.json (title, characters_overview,           │
│    plot_points, unique_locations)                       │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ Stage 2: CharacterDesigner                              │
│ → 2_characters.json (physical, clothing, personality)   │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ Stage 3: ScreenplayWriter                               │
│ → 3_screenplay.json (scenes, action_beats, narration)   │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ Stage 4: StoryboardDirector                             │
│ → 4_storyboard.json (shots, camera, image_prompt)       │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ Stage 5: ShotImageGenerator                             │
│ ├── ReferenceImageManager → 角色参考图 (portrait+fullbody)
│ ├── SceneReferenceManager → 场景参考图 (interior+exterior)
│ └── ImageGenerator (Pro) → shot图片                     │
└─────────────────────────────────────────────────────────┘
    ↓
视频合成 (TTS + Whisper对齐 + 图片序列)
    ↓
final.mp4
```

**关键设计决策**：
- Stage 1-4 使用 Claude Sonnet 4.6（DEC-012 升级，备用 Gemini 3 Pro）
- Stage 5 Shot生成默认使用 Nano Banana 2（角色一致性 ~95%，速度快 3-5x，成本降 50%）
- 环境连续性由场景参考图 (interior/exterior) + 文字 prompt 保障（DEC-014: previous_shot_image 已移除）
- **Nano Banana 2 已确认为主力**：`gemini-3.1-flash-image-preview`（2026-02-26 发布），角色一致性 ~95% 与 Pro 持平，速度快 3-5x，成本降 50%。Founder 决策 NB2 为默认，Pro 仅作未来 Premium 用户储备。详见 `docs/NANO_BANANA_2_RESEARCH.md`

---

## 核心服务

### Phase 2.0 五阶段服务

| 阶段 | 服务 | 职责 | 模型（DEC-012 升级后） |
|------|------|------|------|
| Stage 1 | StoryOutlineGenerator | 故事大纲生成 | **Claude Sonnet 4.6**（备用 Gemini 3 Pro） |
| Stage 2 | CharacterDesigner | 角色外貌设计 | **Claude Sonnet 4.6**（备用 Gemini 3 Pro） |
| Stage 3 | ScreenplayWriter | 分场剧本生成 | **Claude Sonnet 4.6**（备用 Gemini 3 Pro） |
| Stage 4 | StoryboardDirector | 分镜脚本生成 | **Claude Sonnet 4.6**（备用 Gemini 3 Pro） |
| Stage 5 | ImageGenerator | Shot图片生成 | **Nano Banana 2**（默认）/ Gemini 3 Pro Image（Premium 储备） |

### 支撑服务

| 服务 | 职责 | 外部依赖 |
|------|------|----------|
| Phase2PromptBuilder | 构建Shot生成的完整Prompt | - |
| ReferenceImageManager | 角色参考图生成与管理 | ImageGenerator (Flash) |
| SceneReferenceManager | 场景参考图生成与管理（内外景关联） | ImageGenerator (Flash) |
| StyleEnforcer | 风格强制锁定 | - |
| **TextOverlayServiceV2** | 条漫文字后处理叠加（旁白、气泡、情感强调） | PIL/Pillow |
| TTSService | 文字转语音 | 火山引擎 Doubao |
| WhisperService | 语音转文字+时间戳 | OpenAI Whisper |
| AlignmentService | 音画时间对齐 | - |

**🚨 模型配置说明**：
- `FAST_MODEL = "gemini-2.5-flash-image"` - 用于参考图生成
- `PRO_MODEL = "gemini-3-pro-image-preview"` - 用于shot生成（角色一致性关键）

---

## 关键数据结构

### story.json中的角色

**重要**：角色数据有两种字段组织方式，代码都支持：
- `character_type` 或 `type`：角色类型（如 "human"）
- `gender`, `age_appearance`：在根级别
- `physical`：外貌特征（必须）
- `clothing`：服装信息（必须）

```json
{
  "id": "char_001",
  "name": "苏晨",
  "name_en": "Su Chen",
  "type": "human",
  "gender": "female",
  "age_appearance": "young_adult",
  "default_expression": "gentle",
  "physical": {
    "height": "medium",
    "build": "slim",
    "skin_tone": "fair",
    "face_shape": "oval",
    "hair_color": "jet black",
    "hair_style": "short and sharp bob cut",
    "hair_texture": "silky",
    "eye_color": "dark brown",
    "eye_shape": "almond",
    "eye_size": "medium",
    "eyebrows": "thin straight",
    "nose": "small straight",
    "lips": "thin natural pink",
    "distinctive_marks": []
  },
  "clothing": {
    "top": "light gray fitted blazer over white silk camisole",
    "bottom": "black slim-fit trousers",
    "footwear": "black pointed-toe flats",
    "accessories": ["simple silver earrings", "silver minimalist watch"],
    "style": "professional elegant"
  }
}
```

### shots.json中的shot
```json
{
  "shot_id": 1,
  "original_scene_id": 1,
  "image_prompt": "全英文，用于Gemini图像生成",
  "narration_segment": "保留原始中文，用于TTS",
  "shot_type": "medium shot",
  "camera_angle": "eye level",
  "characters_in_scene": ["char_001", "char_002"]
}
```

### timeline.json中的时间映射
```json
{
  "shot_id": 1,
  "start_time": 0.0,
  "end_time": 8.5,
  "duration": 8.5,
  "image_path": "images/shot_01.png"
}
```

---

## 🚨 核心原则（不可妥协）

### 角色一致性是产品的生命线

1. **任何代码修改都不能破坏现有的角色一致性能力**
2. **Shot生成默认使用 Nano Banana 2**（`use_pro_model=False`），角色一致性 ~95%，速度和成本优势显著。Pro 模型（`use_pro_model=True`）仅作为未来 Premium 用户储备，当前不启用
3. **参考图传递链必须完整**：character_refs + scene_refs → generate_shot_image()
4. **修改storyboard_service.py或image_generator.py时，必须先跑角色一致性回归测试**

### 回归测试要求

在修改图像生成相关代码后，必须验证：
```bash
python tests/test_character_consistency_regression.py
```

验证标准：
- [ ] 3人场景角色一致性 ≥ 95%
- [ ] 参考图正确传入（reference_images_log.json中total_refs > 0）
- [ ] 无角色特征混淆（服装、发型、配饰）

**如果回归测试不通过，必须回滚代码**，不允许带着一致性下降的代码继续开发。

### 关键文件警示

| 文件 | 风险等级 | 影响范围 |
|------|---------|---------|
| `image_generator.py` | 🔴 极高 | 直接影响图像生成质量和角色一致性 |
| `storyboard_prompts.py` | 🔴 极高 | Phase 2.0 核心prompt构建（角色映射、连续性指令） |
| `storyboard_service.py` | 🔴 极高 | 影响prompt构建和角色描述 |
| `reference_image_manager.py` | 🟡 高 | 影响参考图生成 |
| `scene_reference_manager.py` | 🟡 高 | 影响场景一致性 |

---

## 开发约束（必须遵守）

### Prompt相关
1. **图像生成prompt必须全英文**：Gemini对英文理解更准确，中文prompt容易导致风格漂移或语义偏差
   - **适用范围**：Stage 4 (storyboard_director) 生成的 image_prompt、参考图prompt、场景图prompt
   - **允许的中文例外**（这些中文词汇英文翻译会丢失视觉特征）：
     - 角色独有的中文名字（如 "Chen Mo (陈默)"）
     - 中国特色地点名称（胡同、弄堂、祠堂、牌坊等 - "alley"无法传达视觉特征）
     - 中国传统服饰专有名词（汉服、旗袍、马褂、凤冠霞帔等）
     - 中国传统建筑元素（飞檐、斗拱、影壁、月亮门等 - 无准确英文对应）
     - 中国美食/店铺类型（兰州拉面、火锅、茶馆等 - 影响场景氛围准确性）
     - 画面中需要出现的中文书法/文字（春联、牌匾、印章、题字、落款等）
     - 中国节日视觉元素上的文字（福字、灯笼上的字等）
   - **不影响图像生成的中文**（不需要改英文）：
     - 代码注释和日志
     - narration_segment（用于TTS，不进入图像生成）
     - Stage 2/3 的LLM指令prompt（生成的是元数据/剧本，不是图像prompt）
2. **shot_type和camera_angle必须英文**：使用_translate_shot_type()和_translate_camera_angle()
3. **narration保留中文**：用于TTS合成，不进入图像生成流程
4. **风格前缀必须添加**：通过StyleEnforcer.enforce_prompt()
5. **LLM约束规则用英文更佳**：Stage 2/3的prompt虽不直接用于生图，但LLM处理规则时英文更精确

### 角色一致性相关
5. **shot必须继承characters_in_scene**：在_split_scene_to_shots()后手动设置
6. **场景图必须传入参考图**：generate_shot_image()的reference_images参数
7. **角色描述必须完整**：使用_build_character_description()，包含physical和clothing

### 音画对齐相关
8. **处理繁简差异**：使用_convert_to_simplified()
9. **多策略匹配**：精确→去标点→前缀→子序列

### 通用性相关
10. **不要硬编码故事类型**：这是通用工具，支持短视频/漫剧/长剧/绘本
11. **不要硬编码角色类型**：支持19种角色类型，新类型走CharacterPromptBuilder
12. **不要硬编码风格**：支持80+风格，走StyleEnforcer

### 宽高比标准（TASK-ASPECT-2x3，2026-02-14）
14. **所有图像统一 2:3 宽高比**（抖音适配）：
    - 角色参考图（portrait + fullbody）：`"2:3"`
    - 场景参考图（interior + exterior）：`"2:3"`（DEC-010 修复）
    - Shot 生成图：`"2:3"`
    - 相关文件：reference_image_manager.py, scene_reference_manager.py, storyboard_director.py, image_generator.py, consistent_image_generator.py, pipeline_orchestrator.py
    - **禁止硬编码其他宽高比**，除非有明确的产品需求变更

### 代码质量原则
15. **No backward compatibility（不写兼容性代码）**：
    - 直接使用新格式，让旧数据报错，强制更新
    - 不要写 `field1 or field2` 这种兼容旧字段的代码
    - 如果LLM输出旧格式，修改prompt而不是写兼容代码
    - 理由：兼容代码会快速变成"屎山"，难以维护

---

## 已踩过的坑（务必避免）

| 问题 | 错误做法 | 正确做法 |
|------|----------|----------|
| 风格漂移 | 只在prompt末尾加风格 | StyleEnforcer在开头加MANDATORY STYLE |
| 角色变脸 | 肖像和全身独立生成 | 串行生成：肖像→用肖像作为参考生成全身 |
| shot缺角色 | 拆分后不管characters_in_scene | 手动继承scene的characters_in_scene |
| 音画不对齐 | 精确匹配失败就放弃 | 多策略：去标点→前缀→子序列 |
| 繁简不匹配 | 直接比较Whisper输出和原文 | 先繁简转换再匹配 |
| Gemini拒绝中文 | image_prompt用中文 | 翻译成英文 |
| 角色外观不一致 | 只用简短description | 完整的physical+clothing描述 |
| 角色描述为空 | 从`human`字段读取外貌 | 从`physical`和`clothing`字段读取 |
| 角色类型识别失败 | 只检查`character_type`字段 | 同时检查`type`字段（字符串值如"human"） |
| 场景构图复制 | 传入前序shot图像但无使用指令 | ~~添加VISUAL CONTINUITY REFERENCE指令块~~ → DEC-014: 移除 previous_shot_image，改用场景参考图 + 文字 prompt 保障连续性 |
| IMAGE编号错乱 | prompt中Image N与contents数组不对应 | DEC-014 后简化：Image 1 = 第一个角色参考图，无 previous_shot 占位，编号从角色参考图开始依次排列 |
| 中文泄露到prompt | Stage 1/3输出中文的mood/key_visual_elements | 修改LLM prompt模板要求输出英文 |
| 条漫中文乱码 | Prompt要求生成带中文文字的图片 | 使用无文字Prompt + TextOverlayService后处理叠加 |
| 文字重叠 | 在已有乱码的图上叠加新文字 | 必须先用无文字Prompt生成干净图片 |

---

## 测试验证清单

修改代码后，必须验证以下点：

### story.json
- [ ] 每个角色有id、name、name_en、character_type
- [ ] 人类角色有完整的physical字段
- [ ] 每个角色有clothing字段
- [ ] 每个scene有characters_in_scene

### shots.json
- [ ] image_prompt全英文
- [ ] shot_type和camera_angle是英文
- [ ] 每个shot有characters_in_scene（继承自scene）

### 图像生成
- [ ] 角色参考图生成成功（portrait + fullbody）
- [ ] 场景参考图生成成功
- [ ] 场景图传入了参考图
- [ ] 日志显示"使用 N 张参考图"

### timeline.json
- [ ] 覆盖完整音频时长
- [ ] 无时间重叠
- [ ] 每个shot都有时间段

---

## 子代理模型规则（Founder 强制要求）

```
🚨 全员强制：禁止使用 Haiku 模型（包括 Task 工具的子代理）
- 子代理最低用 Sonnet 4.6（model: "sonnet"），优先默认继承 Opus 4.6
- Haiku 与 Opus 质量差距过大，不允许用于任何子任务

⚠️ 适用范围澄清：
- 本规则针对「开发 Agent 子代理」（Task 工具、代码生成、文档分析等）
- 产品运行时调用 Haiku API 做轻量任务（如图像分析、分类标注等）属于独立场景，不受此限制
- 区分标准：开发时的 Agent 质量 ≠ 产品运行时的 API 成本优化
```

---

## 代码规范

### 异步
- 所有外部API调用使用async/await
- 并发控制使用asyncio.Semaphore

### 错误处理
- LLM失败 → fallback到简单规则
- 图像生成失败 → 最多重试3次
- 所有服务都有降级策略

### 日志
```python
print(f"[ServiceName] ✅ 操作成功: {detail}")
print(f"[ServiceName] ❌ 操作失败: {error}")
```

### 文件命名
- 服务类：`*_service.py` 或 `*_manager.py`
- 测试脚本：`test_*.py`
- 输出目录：`test_output/manualtest/{test_name}/`

---

## 环境变量

```bash
# 必需
ANTHROPIC_API_KEY=sk-ant-xxx       # Claude
GEMINI_API_KEY=AIzaSyxxx           # Gemini
OPENAI_API_KEY=sk-xxx              # Whisper
VOLCENGINE_ACCESS_KEY=AKLTxxx      # 火山引擎TTS
VOLCENGINE_SECRET_KEY=xxx
VOLCENGINE_TTS_APPID=xxx

# 可选
SHOT_MAX_NARRATION_LENGTH=60       # 触发拆分阈值
SHOT_TARGET_LENGTH=40              # 目标shot长度
```

---

## 快速参考

### 生成角色参考图
```python
ref_manager = ReferenceImageManager(image_generator, output_dir)
await ref_manager.generate_character_multi_refs(characters, style_config)
```

### 生成场景图（默认 NB2，Pro 仅 Premium 储备）
```python
char_refs = ref_manager.get_references_for_scene(chars_in_scene)
scene_refs = scene_ref_manager.get_references_for_location(location_id)
result = await image_gen.generate_shot_image(
    shot=shot,
    reference_images=char_refs + scene_refs,
    style_enforcer=style_enforcer,
    use_pro_model=False  # 默认 NB2（Nano Banana 2），角色一致性 ~95%
    # use_pro_model=True 仅用于未来 Premium 用户
)
```

**NB2 vs Pro 对比**：
- NB2（默认）：角色一致性 ~95%，37.2s/shot，成本降 50%
- Pro（Premium 储备）：角色一致性 ~98%，70-90s/shot，成本高 2x
- Founder 决策：NB2 为默认主力，Pro 不做 3+ 角色场景自动切换

### 音画对齐
```python
alignment = AlignmentService()
timeline = await alignment.align_shots_to_audio(shots, whisper_result)
```

---

## StyleEnforcer 风格词完整列表

每个风格有三类关键词：mandatory（必须包含）、forbidden（禁止使用）、quality（质量提升）。

### realistic (写实摄影)
```python
mandatory = ["photorealistic", "photograph", "real photo", "professional photography", 
             "natural lighting", "realistic skin texture"]
forbidden = ["cartoon", "anime", "illustration", "drawing", "painting", "3D render", 
             "CGI", "Pixar", "Disney", "stylized", "cel-shaded"]
```

### cartoon (3D卡通)
```python
mandatory = ["3D cartoon style", "Pixar-like", "Disney animation", "stylized 3D", 
             "colorful", "friendly characters"]
forbidden = ["photorealistic", "photograph", "real photo", "2D", "flat", 
             "anime", "manga", "hand-drawn", "sketch"]
```

### anime (日式动画)
```python
mandatory = ["anime style", "Japanese animation", "cel shading", "expressive eyes", 
             "dynamic poses", "anime aesthetic"]
forbidden = ["photorealistic", "photograph", "3D render", "Pixar", 
             "Western cartoon", "realistic skin"]
```

### ghibli (吉卜力)
```python
mandatory = ["Studio Ghibli style", "Miyazaki inspired", "hand-drawn animation", 
             "soft colors", "detailed backgrounds", "whimsical atmosphere"]
forbidden = ["photorealistic", "3D render", "digital 3D", "harsh lighting", 
             "dark gritty", "modern CGI"]
```

### illustration (数字插画)
```python
mandatory = ["digital illustration", "vibrant colors", "detailed artwork", 
             "concept art", "clean lines", "rich details"]
forbidden = ["photorealistic", "photograph", "3D render", "low quality", "sketch"]
```

### watercolor (水彩画)
```python
mandatory = ["watercolor painting", "soft edges", "dreamy atmosphere", 
             "flowing colors", "wet on wet technique", "artistic"]
forbidden = ["photorealistic", "sharp edges", "3D render", "digital", "neon colors"]
```

### children_book (儿童绘本)
```python
mandatory = ["children's book illustration", "friendly characters", "soft colors", 
             "whimsical", "storybook style", "child-friendly"]
forbidden = ["photorealistic", "scary", "dark", "violent", "horror"]
```

### cyberpunk (赛博朋克)
```python
mandatory = ["cyberpunk", "neon lights", "futuristic city", "dark atmosphere", 
             "high tech low life", "blade runner aesthetic"]
forbidden = ["pastoral", "rural", "ancient", "medieval", "bright daylight"]
```

### ink (中国水墨)
```python
mandatory = ["Chinese ink wash", "sumi-e", "brush strokes", "minimalist", 
             "traditional Chinese art", "rice paper texture"]
forbidden = ["colorful", "neon", "photorealistic", "3D render", "Western art"]
```

### pixel (像素艺术)
```python
mandatory = ["pixel art", "retro game", "16-bit", "crisp pixels", 
             "limited color palette", "nostalgic gaming"]
forbidden = ["photorealistic", "smooth gradients", "high resolution photo", "3D render"]
```

### 风格强制前缀模板

StyleEnforcer在每个image_prompt最前面注入：

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

## _build_character_description 完整实现

位置：`app/services/storyboard_service.py`

```python
def _build_character_description(self, character: dict) -> str:
    """
    从角色数据构建详细的外观描述（用于image prompt）
    优先从clothing和physical字段获取详细信息，确保角色一致性
    """
    desc_parts = []

    # 1. 物理外观 (physical) - 最重要的识别特征
    physical = character.get('physical', {})
    if physical:
        # 发型和发色
        hair_color = physical.get('hair_color', '')
        hair_style = physical.get('hair_style', '')
        if hair_color or hair_style:
            desc_parts.append(f"{hair_color} {hair_style}".strip())

        # 眼睛
        eye_color = physical.get('eye_color', '')
        if eye_color:
            desc_parts.append(f"{eye_color} eyes")

        # 肤色
        skin_tone = physical.get('skin_tone', '')
        if skin_tone:
            desc_parts.append(f"{skin_tone} skin")

    # 2. 服装（clothing）- 用于区分角色
    clothing = character.get('clothing', {})
    if clothing:
        top = clothing.get('top', '')
        if top:
            desc_parts.append(f"wearing {top}")

        bottom = clothing.get('bottom', '')
        if bottom:
            desc_parts.append(bottom)

        # 配饰（只取前3个）
        accessories = clothing.get('accessories', [])
        if accessories:
            desc_parts.append(", ".join(accessories[:3]))

        style = clothing.get('style', '')
        if style:
            desc_parts.append(f"{style} style")

    # 3. 兜底：使用description或appearance
    if not desc_parts:
        desc = character.get('description', '') or character.get('appearance', '')
        if desc:
            return desc

    # 4. 非人类角色：从animal字段构建
    if not desc_parts and character.get('animal'):
        a = character['animal']
        return f"{a.get('fur_color', '')} {a.get('species', '')} with {a.get('eye_color', '')} eyes"

    return ", ".join(desc_parts) if desc_parts else ""
```

**输出示例**：
```
输入: {"physical": {"hair_color": "black", "hair_style": "short slightly messy", 
       "eye_color": "dark brown", "skin_tone": "fair"},
       "clothing": {"top": "gray wool sweater", "bottom": "dark blue jeans",
       "accessories": ["black-framed glasses"], "style": "casual intellectual"}}

输出: "black short slightly messy, dark brown eyes, fair skin, wearing gray wool sweater, 
       dark blue jeans, black-framed glasses, casual intellectual style"
```

---

## 项目文档

| 文档 | 内容 |
|------|------|
| `/docs/ARCHITECTURE.md` | 系统架构规划 |
| `/docs/character_consistency_breakthrough_6.4.md` | 角色一致性突破记录（2025-12-23） |
| `/docs/phase2_progress_6.4_to_current.md` | Phase 2.0 进度记录（6.4到当前） |
| `/docs/phase2_shot_generation_flow.md` | Phase 2.0 Shot生成流程详解 |
| `/docs/KNOWN_ISSUES.md` | 已知问题和修复状态 |
| `/docs/progress_report_teststory6.md` | 问题修复完整记录 |
| `/docs/COMIC_MVP_PROMPT_TEMPLATES.md` | 条漫Prompt模板（带文字版，保留用于Pro模型测试） |
| `/docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md` | 条漫Prompt模板（无文字版，配合后处理使用） |
| `/docs/COMIC_TEXT_OVERLAY_V2_DECISION.md` | 文字叠加V2决策文档 |
| `/docs/COMIC_MVP_TEST_ACCEPTANCE_CRITERIA.md` | 条漫MVP验收标准 |
| `/docs/NANO_BANANA_2_RESEARCH.md` | Nano Banana 2 (Gemini 3.1 Flash Image) 全维度对比研究（2026-02-26） |
| `/docs/CHARACTER_IDENTITY_FRAMEWORK.md` | 角色一致性框架 v1.0（Identity Anchors + Narrative Variables） |
| `/.team-brain/knowledge/PROMPT_ENGINEERING_ADVANCED_PRINCIPLES.md` | Prompt 工程高级原则（思维层 6 条，补充 AI-ML 操作层 5 条原则） |

---

*记住：这是一个面向大众创作者的通用工具。任何修改都要考虑：能否支持不同类型的故事、角色、风格？*
