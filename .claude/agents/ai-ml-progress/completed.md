# AI-ML Agent - 已完成任务

> 按时间倒序记录已完成的工作

---

## 2026-04-24

### TASK-SEEDREAM-INTEGRATION Prompt 层 — Seedream 2D 风格硬约束 ✅

**方案 A**: 在 `style_enforcer.py` 加 Seedream 专用分支（`enforce_prompt_for_provider()`），NB2 路径零影响

**改动**: `app/services/style_enforcer.py` L677-L768，新增 3 项：
- `_SEEDREAM_2D_LOCK_BLOCK` 类属性（Seedream 2D 锁定块全文，纯英文 1169 字符）
- `build_seedream_2d_boost_prefix()` classmethod（返回锁定块）
- `enforce_prompt_for_provider(prompt, style_name, provider="nb2")` classmethod（核心接入点）

**验证**:
- NB2 路径: `enforce_prompt_for_provider(p, s, "nb2") == enforce_prompt(p, s)` 字符串完全相同
- pytest test_architecture 7/7 PASS（含 test_prompt_templates_are_english，全英文约束通过）
- 8 项手动测试全 PASS（含多风格验证、中文字符检测）

---

## 2026-04-21（PM 代更新）

### Wave 1 Step B — 95 风格 music_hint 字段 ✅
- style_enforcer.py + style_config.py 两个文件
- 95 个用户可选风格 100% 覆盖 + custom fallback
- V4 哲学：身体感觉驱动，不列乐器清单
- Backend: `from app.models.style_config import get_music_hint`

### v3.2 精修 ✅ (取代 v3.1)
- 回退 v3.1 过度约束（ASCII 分层图 + 输出纯净规则）- PM 实测发现质量退步 8.4→6.7
- 保留 few-shot 示例无 ``` 围栏（根因消除不回退）
- 新加 2 行轻量长度建议（"建议 ≤400 字符，质量优先"）
- 方案 B: 污染清理迁到 @backend clean_haiku_output() 代码层

### v3.1 mixed 微调 ⚠️ (已被 v3.2 取代)
- 初次尝试在 meta-prompt 层修字符约束 + 输出污染
- 实测发现 Haiku 挑金句质量退步（秋梨膏/拿铁/终点站严重退步）
- 教训：meta-prompt 加越多，Haiku 越分心

### TASK-HAIKU-QUOTE-EXTRACTION Step 1 — v3 quote picking meta-prompt ✅
- Opus 设计 Quote Selection Protocol（5 正/5 反标准 + 位置倾向 + 数量硬约束 + 忠实规则）
- 产出 `meta_{en,mixed}_v3_quote_picking.md` (~15KB 每个)
- few-shot 示例用年夜饭手选 2 句金句 + 为什么有效解释
- v2 所有优点完整保留（V4 哲学 + cross_sensory + 示例 + ≤400 字符）

---

## 2026-04-20（PM 代更新）

### TASK-MUSIC-LANG-AB-V2 Step 1 — meta-prompt v2 升级 ✅
- 产出 `meta_{en,cn,mixed}_v2.md` 3 个文件
- 新增: cross_sensory 4 条元原则 + 3 精选示例（2 好例 + 1 反例保守格式）+ ≤400 字符硬约束
- 保持 14 个占位符与 v1 一致

---

## 2026-04-18（PM 代更新）

### TASK-MUSIC-LANG-AB Step 1 — 3 个语言变体 meta-prompt ✅
- meta_en / meta_cn / meta_mixed 三个 system+user prompt 模板
- 14 个数据占位符完全一致，覆盖 V4 5 条创作原则
- 路径: `test_output/manualtest/sq_upgrade_ab_test/20260304_113630/meta_prompts/`
- 为 @backend 的 Haiku API 调用提供模板

---

## 2026-04-17（PM 代更新）

### TASK-MUSIC-EXTRACT — 音乐 Prompt 输入格式定义 ✅
- 定义从 outline + screenplay JSON 提取音乐 prompt 所需信息的格式规范
- 产出: `.claude/skills/music-prompt/templates/story_input_format.md`
- 含完整年夜饭示例 + 必须/可选字段标注 + 工作流复盘

### TASK-MUSIC-TRANSITION — 年夜饭转折测试 Prompt ✅
- 4 个显式 Section + 3 个硬转折点，856 字符
- 产出: `transition_test_prompt.md`
- PM 调 API 生成 bgm_transition_test.mp3

### TASK-MUSIC-REWRITE — 3 首 BGM Prompt 重写 ✅
- Founder 试听后否决 #3/#4/#6 风格选择（不贴故事）
- 根因：上一轮过度追求差异化，风格选择服务于"和其他几首不同"而非"最适合这个故事"
- 重写：#3 Dark jazz→Chinese NY acoustic+erhu, #4 Bossa nova→Indie acoustic, #6 Lo-fi electronic→Acoustic warmth+harmonica
- PM 审查 PASS (5/5)

---

## 2026-04-16（PM 代更新）

### TASK-MUSIC-PROMPT — 6 个故事 BGM Prompt 设计 ✅

为 6 个测试故事编写音乐生成 prompt，使用 Music Prompt Skill 5 层结构，6 种完全不同风格：
1. 最后一投 — Post-rock → Orchestral (felt piano + brass)
2. 外公的秋梨膏 — Chinese folk-acoustic (dizi + nylon guitar + guzheng)
3. 年夜饭上的战争 — Dark chamber jazz (upright piano + muted trumpet)
4. 拿铁上的告白 — Bossa nova + dream pop (nylon guitar + Rhodes)
5. 墨痕 — East Asian minimalist / ambient guqin (guqin + shakuhachi)
6. 终点站前的余温 — Lo-fi ambient electronic (synth pad + rain texture + toy piano)

6 个 `music_prompt.md` 文件创建，@backend 已全部调 Mureka API 生成 BGM（7 个 mp3）。

---

## 2026-04-14（PM 代更新）

### TASK-HE-TESTER-1 — 架构测试参与 ✅
### TASK-HE-AIML-1 — Prompt Format A/B 分析 (36KB) ✅
### 10-Shot 三方 Prompt 对比分析 (68KB) ✅
### TASK-STAGED-V2-AIML — Shot 画面调整 Haiku Prompt ✅
- `app/prompts/shot_adjustment_prompt.py` 新建
- 9 条规则 system prompt + build_adjustment_user_prompt 函数

---

## 2026-04-09

### TASK-PIPELINE-OPT-R3 A-1 — description_zh prompt 加强 ✅

**文件**: `app/services/story_outline_generator.py` — 3 处 prompt 文本改动
**根因**: 原 AM-1 的 prompt 对 description_zh 强调不够，LLM 可能跳过
**修复**: System prompt MANDATORY 规则 + JSON schema 【必填】+ 创作要点 (REQUIRED/必填)

---

## 2026-03-25

### TASK-PHASE2-PROMPTS — Phase 2 分析/上下文 prompt 设计 ✅

**完成时间**: 2026-03-25
**交付方式**: TEAM_CHAT 发布，@backend 集成

4 个 prompt:
1. 自定义风格分析 (STYLE_ANALYSIS_PROMPT) — 6 维分析 → StyleEnforcement JSON + display_tags
2. 角色特征提取 (CHARACTER_ANALYSIS_PROMPT) — 6 维分析 → description_zh/en + gender + age_range + display_name
3. 场景特征提取 (SCENE_ANALYSIS_PROMPT) — 6 维分析 → description_zh/en + location_type + atmosphere + display_name
4. 用户参考上下文段 (_build_user_reference_context) — 动态函数，角色/场景/风格三段按需拼接，无参考时返回空字符串

设计要点:
- Prompt 1 的 mandatory/forbidden 直接对齐 StyleEnforcement，Backend 零转换
- Prompt 2/3 核心用文本描述（PM 决策避免前后端耦合），保留少量结构化字段（gender/age_range/location_type）
- Prompt 4 是函数而非纯文本，处理部分参考缺失

---

### TASK-STYLE-EXPAND-28 — 13 个新风格完整配置 ✅

**完成时间**: 2026-03-25
**交付方式**: TEAM_CHAT 发布，@backend + @frontend 集成

13 个新风格: ukiyo_e, vintage_film, pencil_sketch, chibi, dark_fantasy, pop_art, paper_cut, steampunk, art_nouveau, noir, comic_western, pastel_dream, gothic

每个风格交付:
- StyleEnforcement 6 维度 (name, display_name, mandatory 8-10, forbidden 10-15, description 100-300 字, quality 5-8)
- 前端展示 (label 中文名 + description 定位 + CSS gradient)
- StylePreset Literal 扩展 15→28

---

## 2026-03-24

### TASK-OUTLINE-LLM-FIX 第 1 项 — system prompt 设计 ✅

**完成时间**: 2026-03-24
**交付方式**: TEAM_CHAT 发布，@backend 集成

StoryOutlineGenerator 专用 system prompt:
- 角色定位: story planner + visual director
- JSON 严格约束: no markdown, no explanation, pure JSON { ... }
- 中英文分工: 逐字段明确（title 中文, title_en 英文, color_palette 英文, description 中文等）
- 新增字段强化: ending_options 3 选项 + description/personality 字数 + mood 枚举

---

### TASK-OUTLINE-PROMPT-UPGRADE — Stage 1 Prompt 新增 4 个字段 ✅

**完成时间**: 2026-03-24
**修改文件**: `app/services/story_outline_generator.py` (`_build_prompt` 方法)

新增 3 个顶层字段 + 2 个 characters_overview 子字段:
- `summary`: 故事简介（100-200 字）
- `ending_options`: 3 个结局选项数组（ending_1/2/3，各有 id+description）
- `mood`: 情绪基调（感人/治愈/热血/悬疑/浪漫/温馨 六选一）
- `description`: 角色外貌简述（20-30 字中文，给前端用户看）
- `personality`: 角色性格简述（10-20 字中文，给前端用户看）

创作要点新增 #8-#11（summary 定位、ending 差异化、mood 预设值、角色简述定位）

验证: Python syntax ✅

---

## 2026-03-17

### TASK-OB1-CLEANUP — prompt_safety_rewrite.py "Haiku" 引用清理 ✅

**完成时间**: 2026-03-17
**修改文件**: `app/prompts/prompt_safety_rewrite.py`

11 处 "Haiku" → "Sonnet 4.6":
- L3 docstring, L312 section 注释, L598 docstring
- L646-648 示例函数名+注释: `rewrite_prompt_with_haiku` → `rewrite_prompt_with_sonnet`
- L656 model ID: `claude-haiku-4-5-20251001` → `claude-sonnet-4-6`
- L689 调用处同步
- L714/L728 设计说明
- L752 成本估算: `~$0.001/次` → `~$0.005/次`

验证: "Haiku" grep 零匹配 ✅

---

## 2026-03-16

### TASK-IMG-SAFETY-RETRY-AIML — 参考图安全改写 Prompt 工程 ✅

**完成时间**: 2026-03-16
**修改文件**: `app/prompts/prompt_safety_rewrite.py`

| # | 交付物 | 内容 |
|---|--------|------|
| 1 | 新增关键词类别 | 5 类 74 词条: CROWD(19)+ANIMAL(16)+FIRE_SMOKE(16)+CHILD_CONTEXT(10)+REVEALING_CLOTHING(13) |
| 2 | SCENE_REF_REWRITE_PROMPT | 场景参考图专用 LLM 改写模板 |
| 3 | CHAR_REF_REWRITE_PROMPT | 角色参考图专用 LLM 改写模板 |
| 4 | _simplify_anchor_prompt() spec | Backend 实现指引（前置 No people + apply_simple_replacements + 正则清理） |
| 5 | _build_anchor_prompt() 结构优化 | 建议 "No people" 从 prompt 末尾前置到标题之后 |

**设计要点**:
- **CROWD 策略**: 人群活动→静态环境元素（crowds→visitors, bustling→serene, townspeople→architectural details）
- **ANIMAL 策略**: 活体动物→容器道具（chickens→woven baskets with eggs, livestock→wooden crates）
- **FIRE_SMOKE 策略**: 明火浓烟→温暖光晕雾气（fire→warm glow, smoke→atmospheric haze）
- **场景改写模板**: PRESERVE 建筑/招牌 + REMOVE 人群/动物 + REPHRASE 氛围词 + ADD "No people" 开头
- **角色改写模板**: PRESERVE 身份锚点(面部/发色/服装颜色) + MODIFY 武器(→ornate implement) + MODIFY 暴露(增加覆盖但不改颜色) + SIMPLIFY 儿童(聚焦面部服装)
- **结构优化**: "No people" 从 prompt 末尾前置到标题后，降低 Gemini 安全过滤误触发

**R8 触发案例**: `rural_market_entrance` 被 "crowds of rural townspeople" + "clucking chickens" + "smoke rising" 触发，现有 6 类关键词一个都匹配不到 → 新增 CROWD/ANIMAL/FIRE_SMOKE 三类完整覆盖

### PM Code Review 后 2 项小补充 ✅

**完成时间**: 2026-03-16
**修改文件**: `app/services/scene_reference_manager.py`

1. **`_simplify_anchor_prompt()` 正则补充**: `re.sub(r'\b(people|persons|humans|men|women|children)\s+(are\s+)?\w+ing\b', '', simplified)` — 清理 `apply_simple_replacements()` 可能漏掉的自由文本人物描述
2. **`_build_anchor_prompt()` "No people" 前置**: exterior + interior 两个分支，将 "STRICT: No people..." 从 prompt 末尾移到标题之后，新增 "This is a PURE ARCHITECTURAL/ENVIRONMENTAL scene."，末尾原 STRICT 行删除

---

## 2026-03-13

### Phase 3 — T-H-AIML (画面自然度 Haiku Prompt 设计) ✅

**完成时间**: 2026-03-13
**交付物**: TEAM_CHAT 中的 prompt 设计文档（非代码改动）

| # | 任务 | P | 交付 |
|---|------|---|------|
| T-H-AIML | 画面自然度维度 prompt 设计 | P2 | 3 子维度 + 风格无关原则 + prompt 文本 + 5 正例 + 5 反例 + 集成确认 |

**设计要点**:
- **3 个子维度**: D1 ANATOMICAL (断肢/多余肢体/手指数量/关节反折) + D2 PHYSICS (无支撑悬浮/不可能姿态) + D3 SPATIAL (比例矛盾/朝向不一致)
- **风格无关原则**: 区分"生成失败"(应 flag) vs "艺术风格选择"(不应 flag)
  - NATURAL: anime 大眼、ink 极简肢体、pixel 方块比例、manga 夸张动态、梦境悬浮
  - UNNATURAL: 断臂浮空、3 只手、平地双脚悬空、成人与幼儿等身高、7 根手指
- **集成方案**: 合并到 VALIDATION_PROMPT_BASE Q3 位置，零额外 API 调用
  - JSON 新增 `has_visual_unnaturalness` (bool) + `unnaturalness_details` (string)
  - max_tokens 建议 256→384
  - VALIDATION_PROMPT_PROPS 编号从 Q3→Q4
- **Phase 1/2 分界**: Phase 1 仅日志不触发 FAIL; Phase 2 需累计数据证明 Haiku 准确率 > 90%

---

### Phase 1 — T-E+T-F+T-G+T-C-AIML (T-A~T-K 派发) ✅

**完成时间**: 2026-03-13
**修改文件**: `app/services/storyboard_director.py`, `app/services/story_outline_generator.py`

| # | 任务 | P | 修改 |
|---|------|---|------|
| T-E | Stage 4 背面/高角度角色一致性 | P1 | Rule #10 BACK-VIEW/HIGH-ANGLE CHARACTER CONSISTENCY (两处规则区同步) |
| T-F | Stage 4 off-screen 肢体接触 | P1 | Rule #11 OFF-SCREEN CHARACTER PHYSICAL CONTACT (CRITICAL) (两处同步) |
| T-G | Stage 4 空间方向矛盾 | P1 | Rule #12 SPATIAL DIRECTION SELF-CONSISTENCY CHECK (两处同步) |
| T-C-AIML | Stage 1 signage_text 字段 | P1 | unique_locations schema 新增 signage_text + 创作要点 #7 |

**T-E 设计要点**:
- back-view/over-shoulder/bird's-eye/high-angle 时: REINFORCE 服装精确色名+garment type + 发色+发型
- 显式注明 "Even viewed from behind/above, [character]'s [color] [garment] must remain clearly identifiable"
- R7 实例: Shot_08 鼠尾草绿 T 恤从背面偏白 → 此规则要求显式重复 "sage-green T-shirt"
- 含 ❌ BAD (vague "her top") / ✅ GOOD (exact color+garment) 正反例

**T-F 设计要点**:
- FORBIDDEN: 可见角色与画外角色直接物理接触 (grip, pull, hold, embrace)
- REQUIRED: 可见角色独立肢体语言暗示互动 (reaching toward frame edge, beckoning gesture)
- 原因: 图像模型渲染不可见角色肢体为悬空断肢
- 不影响环境交互（开门、拿物品等）
- R7 实例: Shot_03 "pulled by Xiaohe's grip off-screen left" → 悬空手

**T-G 设计要点**:
- camera_angle + character actions + spatial descriptions 自洽验证
- 前向镜头 → 角色不应"走向远方"; "领队前行" → 应拍背/侧; "落在最后" → 不应前景居中
- R7 实例: Shot_04 "trailing at the rear" + 正面镜头 → 空间矛盾
- 含 ❌ CONTRADICTORY / ✅ CONSISTENT 正反例

**T-C-AIML 设计要点**:
- unique_locations schema 新增 `signage_text` 字段: "店铺/建筑招牌上实际显示的文字（中文），无招牌则为空字符串"
- 创作要点 #7: 有招牌场所填真实名称（"李记桂花糕"），无招牌场所填 ""
- 分离 display_name（开发标签 "李记桂花糕铺·外景"）与 signage_text（图像用文字 "李记桂花糕"）
- Backend T-C-Backend 将改用 signage_text 作为 `_detect_signage_name()` 数据源

---

## 2026-03-12

### Phase 1b — T34+T37 ✅

**完成时间**: 2026-03-12
**修改文件**: `app/services/storyboard_director.py`, `app/services/screenplay_writer.py`

| # | 任务 | P | 修改 |
|---|------|---|------|
| T34 | shot_size/angle 完整性 (P-R6) | P1 | Plan A: CAMERA_INFORMATION_COMPLETENESS_RULE 常量 + Plan B: _validate_storyboard() 检测+注入 |
| T37 | 称谓歧义消除规则 (P-R9) | P2 | KINSHIP ADDRESS CLARITY (Rule 5) 加入 DIALOGUE NATURALNESS RULES |

**T34 设计要点**:
- Plan A: 3 条规则 — shot size in prompt + camera angle in prompt + natural integration
- Plan B: 后验证 — 关键词映射表检测 image_prompt 缺失 → 从 shot.camera 元数据构建 "low angle medium shot" 注入开头
- eye_level 不强制（最常见角度，省略合理）
- 注入位置: Plan A 在 SHOT TRANSITION RULES 后；Plan B 在 _validate T29 off_screen 逻辑之后
- Founder 要求的"创意注入": 自然英文短语融入 prompt，非技术标签

**T37 设计要点**:
- Rule 5 KINSHIP ADDRESS CLARITY: 多代际家庭称谓从说话者视角消歧
- "妈"→需确定指谁："你妈" vs "奶奶" vs "婶婶"
- 旁白同样消歧: "林秀梅走了过来" 而非 "妈妈走了过来"
- 引用 T32 CHARACTER RELATIONSHIPS 数据
- SHOULD 措辞，含 3 代家庭 ❌/✅ 正反例

---

### Phase 1a — T33+T35+T36 (T29-T37 派发) ✅

**完成时间**: 2026-03-12
**修改文件**: `app/services/story_outline_generator.py`, `app/services/storyboard_director.py`

| # | 任务 | P | 修改 |
|---|------|---|------|
| T33 | family_relationships 三角关系校验 (P-R4) | P2 | RELATIONSHIP CONSISTENCY RULES (三角一致+配偶传递+代际自检+正反例) |
| T35 | 多人空间锚定+比例 (P-R7+P-R10) | P2 | MULTI_CHARACTER_SPATIAL_ANCHORING_RULES 5条规则注入 _build_scene_prompt() |
| T36 | color_palette 英文化 (P-R8) | P3 | Schema 占位符英文化 + 注意事项英文色名要求 |

**T33 设计要点**:
- Triangle Consistency: A→C grandfather_of + B→C father_of → A→B SHOULD father_of (非 grandfather_of)
- Spouse Transitivity: A spouse_of B + A parent_of C → B parent_of C
- Self-Check: 标注每人代际距离，1 代=parent_of，2 代=grandparent_of
- 含陈守正/陈建国/陈晓桐三代正反例

**T35 设计要点**:
- 5 条规则: HEADCOUNT GUARANTEE + FURNITURE-TO-BODY SCALE + ENVIRONMENT INTERACTION + SPATIAL DISTRIBUTION (≥2 depth planes) + OVERLAP AVOIDANCE
- 每条含 ❌/✅ 正反例，"SHOULD" 非 "MUST"
- 位置: INTERIOR_SPATIAL_DEPTH_RULES 之后，CINEMATOGRAPHY_GUIDE 之前
- 注入: BACKGROUND_VARIETY_RULES 之后
- 与 T27 互补: T27=背景+纵深，T35=多人空间+比例
- ⚠️ 未改 `_validate_storyboard()` — Phase 1b T34 范围

**T36 设计要点**:
- Schema: `["主色调1","主色调2","点缀色"]` → `["primary color in English","secondary color in English","accent color in English"]`
- 注意事项: 要求英文色名 (warm amber, deep navy, muted sage green)
- 仅改 schema+prompt，不改代码逻辑

---

### Phase 1 — T25+T26+T27 平台级改进 ✅

**完成时间**: 2026-03-12
**修改文件**: `app/services/story_outline_generator.py`, `app/services/screenplay_writer.py`, `app/services/storyboard_director.py`

| # | 任务 | P | 修改 |
|---|------|---|------|
| T25 | Stage 1 标题-内容校验 + family_relationships (P-S5) | P2 | characters_overview 新增 family_role + family_relationships 数组 + TITLE CONSISTENCY 规则 |
| T26 | Stage 3 对话自然度规则 (P-S2) | P1 | DIALOGUE NATURALNESS RULES (4 条) 注入对话明确化规则之后 |
| T27 | Stage 4 角色关系映射+背景多样性+纵深感 (P-S1/S3/S4) | P1+P2 | 3 个新常量 (CHARACTER_RELATIONSHIP_MAPPING_RULES + BACKGROUND_VARIETY_RULES + INTERIOR_SPATIAL_DEPTH_RULES) 注入 _build_scene_prompt() |

**T25 设计要点**:
- `family_role` 字段: grandfather/mother/father/daughter 等
- `family_relationships` 数组: from→to relationship mapping
- TITLE CONSISTENCY: 标题中的家庭角色称谓/性别必须与 characters_overview 匹配
- 包含正反例指导

**T26 设计要点**:
- 4 条规则: 逻辑常识(西瓜不热吃) + 主语明确 + 年龄身份匹配 + 口语自然度
- 措辞 "SHOULD" 不 "MUST"
- 注入位置: 对话明确化规则之后、输出要求之前

**T27 设计要点**:
- CHARACTER_RELATIONSHIP_MAPPING_RULES (P-S1): 配合 T24 传入的 characters_overview 关系数据，强制 text_overlay 使用正确称谓 + 视角感知 + 跨 shot 一致
- BACKGROUND_VARIETY_RULES (P-S3): 同 location 3+ shots 变换背景焦点/镜头朝向
- INTERIOR_SPATIAL_DEPTH_RULES (P-S4): medium_shot + interior 需前中后景三层纵深
- 与 T24 (@Backend) 配合: T24 已完成参数传递，T27 规则引用其生成的关系数据表

---

## 2026-03-11

### Phase 1 — T18+T19 平台级改进 ✅

**完成时间**: 2026-03-11
**修改文件**: `app/services/storyboard_director.py`, `app/services/reference_image_manager.py`

| # | 任务 | P | 修改 |
|---|------|---|------|
| T18 | Stage 4 场景道具连续性规则 (S2) | P1 | 新增 SCENE_PROP_CONTINUITY_RULES 常量（4 条规则 + 4 组正反例），注入 _build_scene_prompt + _build_prompt |
| T19 | 参考图跨年龄风格统一强化 (S4) | P2 | 两处 T14 CROSS-AGE 替换为强化版：显式引用 style_name + 正面/反面约束 + 条件 AGE-SPECIFIC STYLE ANCHOR |

**T18 设计要点**:
- 措辞松紧: "SHOULD maintain" (指导原则) 而非 "MUST exactly match" (硬约束)
- 保留构图创意空间: "不同镜头角度自然展示不同部分"
- 4 条规则: 持续道具 + 叙事驱动变化 + 数量一致 + 灵活性

**T19 设计要点**:
- 从 `project_style.style_preset` 提取 style_name 显式注入
- 从 `character.get('age_appearance')` 判断是否 young 角色
- young 角色条件追加 AGE-SPECIFIC STYLE ANCHOR（仅 child/teen/teenager/young_adult/baby/toddler/kid）

---

## 2026-03-10

### TASK-STYLE-THUMBNAILS — 15 种风格缩略图生成 ✅

**完成时间**: 2026-03-10
**Founder 审图**: ✅ 通过（"图片质量非常好"）
**新增文件**: `tests/test_style_thumbnails.py`
**输出**: `test_output/manualtest/style_thumbnails/` (15 张 PNG + 15 个 prompt)

**任务类型**: 图像生成（NB2 缩略图）

**完成内容**:
- [x] 统一场景 prompt（英文）: 城市街头年轻女生 + 温暖街景
- [x] 15 种风格各生成 1 张缩略图（StyleEnforcer.enforce_prompt() + add_quality_suffix=True）
- [x] 模型: NB2 (`gemini-3.1-flash-image-preview`)，宽高比 1:1
- [x] 15/15 全部成功，1024×1024 PNG
- [x] Prompt 保存到 `prompts/` 子文件夹
- [x] 总耗时 ~383s（平均 25.5s/张）
- [x] Founder 审图通过

**15 种风格**:
pixar_3d/皮克斯3D, ghibli/吉卜力, illustration/数字插画, ink/中国水墨, slam_dunk/井上雄彦, korean_webtoon/韩漫, oil_painting/油画, cyberpunk/赛博朋克, realistic/写实摄影, cartoon/卡通动画, anime/日式动画, watercolor/水彩, children_book/儿童绘本, manga/日漫, pixel/像素艺术

**关键产出**:
| 文件 | 说明 |
|------|------|
| `tests/test_style_thumbnails.py` | 生成脚本 |
| `test_output/manualtest/style_thumbnails/*.png` | 15 张缩略图 |
| `test_output/manualtest/style_thumbnails/prompts/*.txt` | 15 个 prompt |

**下一步**: @Frontend 集成到 create 页面替换渐变色块

---

### Step 7 — T13+T14+T15 R3 修复 ✅

**完成时间**: 2026-03-10
**修改文件**: `app/prompts/storyboard_prompts.py`, `app/services/image_generator.py`, `app/services/reference_image_manager.py`

| # | 任务 | P | 修改 |
|---|------|---|------|
| T13 | 条漫模式叙事自足 prompt | P1 | 新增 COMIC_MODE_NARRATIVE_RULES 常量（3 条规则） |
| T14 | 角色参考图跨年龄风格统一 | P1 | portrait + reference prompt 各加 CROSS-AGE STYLE CONSISTENCY |
| T15 | NB2 气泡重复抑制 | P2 | build_dialogue_scene_embed() 加 EXACTLY ONCE 指令 |

---

## 2026-03-09

### Step 3 — T10 Stage 3 thought 比例强化 ✅

**完成时间**: 2026-03-09
**修改文件**: `app/services/screenplay_writer.py` (2 处)

| # | 修改项 | 内容 |
|---|-------|------|
| 1 | 分布目标 L404 | "每 scene 至少 1 个 thought" → "thought 占比 ≥20%（5 beats ≥1，6+ beats ≥2）" |
| 2 | 输出要求 L430 | 同上双重约束 |

---

### Step 1 — T1+T2+T3 F1-F5 深层修复 ✅

**完成时间**: 2026-03-09
**修改文件**: `app/services/screenplay_writer.py`, `app/services/storyboard_director.py`

| # | 任务 | P | 修改 |
|---|------|---|------|
| T1 | Stage 3 dialogue_beats type 字段 | P0 | schema + thought 示例 + 强制覆盖 + 分布目标 |
| T2 | Stage 4 MAPPING RULES 增强 | P0 | THOUGHT GENERATION + SPEAKER VISIBILITY + SELF-CHECK (×2) |
| T3 | Stage 3 plot_points 1:1 | P0 | PLOT POINT COVERAGE 约束块 |

---

### E2E 回归修复 — 4 项 AI-ML 任务 (Issue #1/#3/#4/#5) ✅

**完成时间**: 2026-03-09
**修改文件**: `app/services/storyboard_director.py`, `app/prompts/storyboard_prompts.py`

| # | Issue | P | 修改 |
|---|-------|---|------|
| 1 | text_overlay 缺失 (Pipeline 架构缺陷) | P0 | Stage 4 两套 schema + TEXT OVERLAY MAPPING RULES + dialogue_beats 传入 |
| 3 | SQ-1 标签泄露 | P1 | 标签防复制指令 |
| 4 | 单角色多手动作 | P2 | Rule #9 SINGLE-CHARACTER HAND ACTION LIMIT (两处) |
| 5 | NB2 乱码文字 | P2 | TEXT-FREE 全局约束 |

---

## 2026-03-06

### TASK-PROMPT-BUBBLE-FOLLOWUP-R2 -- R2 补测 + text_language 约束 ✅

**完成时间**: 2026-03-06 14:10
**关联任务**: TASK-PROMPT-BUBBLE-FOLLOWUP-R2 (PM 派发, 2 项后续)
**修改文件**: `app/services/image_generator.py`
**新增文件**: `tests/test_speaker_format_abc_r2.py`

**Task A: R2 补测 (P0)** -- 修复 R1 ref_manager bug:
- R1 Bug: 每组 `new ReferenceImageManager()`，B/C 组 ref_count=0 (不公平对比)
- R2 Fix: 循环外生成参考图一次，三组共用同一个实例
- A 组 (中文名): 10/10 成功, 10/10 对话嵌入, avg 4.4 refs/shot, 305s
- B 组 (英文名): 10/10 成功, 10/10 对话嵌入, avg 4.4 refs/shot, 416s
- C 组 (char_ID): 10/10 成功, 10/10 对话嵌入, avg 4.4 refs/shot, 332s
- 总耗时: 1054s (~17.5 分钟)

**Task B: text_language 约束 (P1)** -- 繁简约束 + 多语言预留:
- 新增 `_TEXT_LANGUAGE_CONFIG` 字典 (zh-CN/zh-TW/en)
- `build_dialogue_scene_embed()` 新增 `text_language: str = "zh-CN"` 参数
- 气泡描述 "Chinese text" -> "Simplified Chinese text" + 末尾语言约束
- 向后兼容: 生产代码第 829 行默认 zh-CN

**测试脚本**: `tests/test_speaker_format_abc_r2.py`
**报告**: `test_output/manualtest/prompt_bubble/speaker_format_test_r2/comparison_report.md`

---

### TASK-PROMPT-BUBBLE-FOLLOWUP -- 精确测量 + 命名格式 A/B/C 对比 ✅

**完成时间**: 2026-03-06
**关联任务**: TASK-PROMPT-BUBBLE-FOLLOWUP (PM 22:46 派发, 2 项后续)
**修改文件**: `app/services/image_generator.py`
**新增文件**: `tests/test_prompt_size_measurement.py` + `tests/test_speaker_format_abc.py`

**任务 1: 精确 prompt 尺寸测量**:
- 逐模块对比: System Instruction -296, Quality Suffix -59, TEXT OVERLAY -210, Dialogue Embed +113
- Shot 1 (dialogue): 5707 → 5252 chars (-455, -8.0%)
- Shot 5 (dialogue_with_thought): 5258 → 4803 chars (-455, -8.7%)
- Before/After prompt 全文保存到 `test_output/manualtest/prompt_bubble/prompts/`

**任务 2: Near {speaker} 命名格式 A/B/C 对比**:
- 新增 `_resolve_speaker_label()` 函数 (chinese/english/char_id 格式转换)
- 修改 `build_dialogue_scene_embed()` 新增 `characters` + `speaker_format` 参数 (向后兼容)
- 3 组 × 10 shots = 30 张: A 10/10, B 10/10, C 10/10 (全部成功)
- **注意**: B/C 组无参考图 (测试脚本问题), 需 Founder 人工对比时考虑

**测试脚本**: `tests/test_prompt_size_measurement.py` + `tests/test_speaker_format_abc.py`
**报告**: `test_output/manualtest/prompt_bubble/speaker_format_test/comparison_report.md`

---

## 2026-03-05

### TASK-PROMPT-BUBBLE — Prompt 架构优化（NB2 原生对话气泡）✅

**完成时间**: 2026-03-05
**关联任务**: TASK-PROMPT-BUBBLE (Founder 确定方向, PM 19:00 派发)
**修改文件**: `app/services/image_generator.py` + `app/prompts/storyboard_prompts.py`

**代码改动**:
- 新增 `build_dialogue_scene_embed()`: 对话气泡嵌入 [SCENE DESCRIPTION] ("Near {speaker}, a white speech bubble...")
- `build_native_text_prompt()`: dialogue 分支返回 "" + 复合类型跳过 dialogue 子项
- `generate_shot_image_phase2()`: 对话嵌入场景描述 + Quality Suffix 禁用 (add_quality_suffix=False)
- `build_system_instruction_phase2()`: 精简 ~400→~150 chars (移除 Style Enforcement/Aspect Ratio 冗余行)
- thought/narration TEXT OVERLAY REQUIREMENT 保持不变

**验证**: 2 × 10-shot (不同风格, 使用已有 dialogue-rich storyboard 数据)
- dialogue_dense_illustration: 10/10 成功, 10/10 对话嵌入
- slamdunk_dialogue: 10/10 成功, 4/4 对话嵌入
- Prompt 净减少 ~400-600 chars

**测试脚本**: `tests/test_prompt_bubble.py`
**报告**: `test_output/manualtest/prompt_bubble/comparison_report.md`

---

## 2026-03-04

### Shot 15/18 Prompt 工程优化 + SQ-4/SQ-5/Bug#3 恢复 ✅

**完成时间**: 2026-03-04
**关联任务**: TASK-SHOT-QUALITY-BUGFIX (Founder 指派, PM 19:30 派发)
**修改文件**: `app/services/storyboard_director.py`

**事件**: PM 回滚代码时误删 AI-ML 所有改动，本次一并重新应用 + 新增 2 条规则
**新增规则**:
- Rule #7 OBJECT PHYSICAL PLAUSIBILITY: 共享表面物体需独立空间锚点，禁止重叠
- Rule #8 MULTI-CHARACTER LIMB INTERACTION LIMITS: 同一物体最多2角色手部交互
**重新应用**: Rule #6 (Bug #3) + SQ-4 (NARRATIVE VISUAL PROPS + SPATIAL DEPTH) + SQ-5 (SHOT TRANSITION + 数据增强)
**两处规则区**: 主规则区 (详细版) + 强化规则区 (精简版)
**验证**: ✅ Python 语法检查通过 (935 lines)

---

### TASK-SHOT-QUALITY-BUGFIX Bug #3 — 神秘路人修复 ✅

**完成时间**: 2026-03-04
**关联任务**: TASK-SHOT-QUALITY-BUGFIX (P2, Bug #3)
**修改文件**: `app/services/storyboard_director.py`

**问题**: Step 7 B 组 6/24 (25%) shots 出现不在角色列表中的路人（餐厅服务员、模糊背景人影等）
**根因**: NB2 模型默认填充大空间 + prompt 暗示性措辞 + 缺少人数负面约束
**修复**: IMAGE PROMPT QUALITY REQUIREMENTS Rule #6 — STRICT CHARACTER COUNT — NO EXTRA PEOPLE
- 要求 "EXACTLY N characters in this scene"
- 禁止 bystanders/extras/crowd/background figures
- 禁止暗示性措辞 "blurred forms of other people"
- 空座位保持空状态
**验证**: ✅ Python 语法检查通过

---

### TASK-SHOT-QUALITY-UPGRADE Step 5b — SQ-3 + SQ-4 + SQ-5 ✅

**完成时间**: 2026-03-04
**关联任务**: TASK-SHOT-QUALITY-UPGRADE (P0, Step 5b)
**修改文件**:
- `app/services/screenplay_writer.py` — SQ-3
- `app/services/storyboard_director.py` — SQ-4 + SQ-5

**任务类型**: Prompt 工程（Stage 3+4 prompt 改进 × 3 项）

**SQ-3: Stage 3 对话明确化规则**
- 在 `_build_single_scene_prompt()` 对话要求区块添加：
  - 关键剧情词显式表达（禁止"那个行业"→必须"公务员考试"）
  - 前30%对话完成核心冲突定义
- 插入方法: 在现有"对话写作原则"4条规则后、输出要求前

**SQ-4: Stage 4 叙事性视觉道具 + 空间纵深**
- 在 `_build_scene_prompt()` 添加：
  - NARRATIVE VISUAL PROPS: 每 image_prompt 至少1个剧情道具
  - SPATIAL DEPTH RULES: medium/close-up 保留≥30%背景，≥2层景深
- 插入方法: IMAGE PROMPT QUALITY 后、TEXT OVERLAY RULES 前

**SQ-5: Stage 4 运镜差异化 + 构图数据增强**
- Prompt 新增 SHOT TRANSITION RULES:
  - 30度法则 + 景别变化 + 角度变化 + 构图变化 + 焦距规则
- 数据结构增强:
  - composition 新增: foreground, background, depth_layers
  - camera 新增: focal_length
- 仅 Stage 4（DEC-014 后 Stage 5 由 Backend SQ-8 处理）

**验证**: ✅ Python 语法检查通过（两文件 0 error）

**经验记录**:
- SQ-4 的 NARRATIVE VISUAL PROPS 是视觉叙事的关键 — 让观众不看文字也能理解冲突
- SQ-5 的30度法则是影视专业最基础的剪辑规则，之前 Stage 4 prompt 完全没有
- composition 增加 foreground/background/depth_layers 后，LLM 被迫思考每个 shot 的空间层次
- focal_length 与 shot_size 绑定（wide=24-35mm, close=85mm）确保了光学真实性

---

## 2026-03-03

### TASK-STYLE-DESC-REWRITE — slam_dunk 句序修复 ✅

**完成时间**: 2026-03-03 17:05
**关联任务**: TASK-STYLE-DESC-REWRITE (P1, Step 3 PM review 反馈)
**修改文件**: `app/services/style_enforcer.py`

**任务类型**: Prompt 工程（句序修复）

**问题**: PM review 发现 slam_dunk 场域式描述的 6 句顺序错乱
- 错误: 传统→体态→笔触→光影→色彩→构图
- 正确: 传统→光影→色彩→质感→角色→构图

**修复**: 保持 6 句内容不变，重新排列顺序为标准 6 句结构

**验证**: ✅ 句序正确 + enforce_prompt() 通过 + 词数不变 (107)

**经验记录**:
- 已验证的 A/B 测试版本虽然内容经过验证，但句序标准化仍然需要确认
- 6句结构的顺序本身也是"场域式"规范的一部分，不仅是内容

---

### TASK-STYLE-DESC-REWRITE — 15个风格 style_description 场域式改写 ✅

**完成时间**: 2026-03-03 15:56
**关联任务**: TASK-STYLE-DESC-REWRITE (P1, Step 2)
**修改文件**: `app/services/style_enforcer.py`

**任务类型**: Prompt 工程（场域式改写 × 15 风格）

**完成内容**:
- [x] 2个已验证描述（slam_dunk, illustration）直接应用 A/B 测试胜出版本
- [x] 13个新写场域式描述，全部遵循6句结构
- [x] 每个描述 150-250 词范围（已验证版本除外）
- [x] 全英文，与 mandatory/forbidden 零重复
- [x] Python 加载验证 15/15 通过
- [x] enforce_prompt() 验证 15/15 通过
- [x] 更新 ai-ml-progress 三个文件

**6句结构**: ①传统锚定 ②光影哲学 ③色彩心理 ④质感密度 ⑤角色表演 ⑥构图原则

**经验记录**:
- 场域式描述的核心是让模型"进入角色"而不是"执行命令"
- 每个风格的传统锚定必须独特且具体（不能泛泛说"fine art"）
- 光影/色彩/质感三者构成视觉底座，角色表演和构图构成叙事顶层
- 已验证的 slam_dunk/illustration 虽然词数偏少（107/116），但因通过 A/B 测试不应修改

---

## 2026-02-28

### TASK-CROSS-STYLE-TEST 前置 — illustration 场域式 style_description 提供 ✅

**完成时间**: 2026-02-28 11:30
**关联任务**: TASK-CROSS-STYLE-TEST (P2) 前置准备
**产出**: TEAM_CHAT 中发布 B 组场域式改写版本

**任务类型**: Prompt 工程（场域式改写）

**依据**: 原则 7（约束+场域双层架构），复用 slam_dunk 场域式 6 句结构

**完成内容**:
- [x] 分析当前命令式 style_description（1 句，与 mandatory 高度重叠）
- [x] 编写场域式改写版本（6 句各司其职）
- [x] 确认与 mandatory/forbidden 约束层不重复
- [x] 确认适合都市情感题材但不锁死题材
- [x] 发布到 TEAM_CHAT 通知 PM + Tester

**场域式改写要点**:
| 句 | 功能 |
|----|------|
| 1 | 传统锚定（digital illustration as storytelling art） |
| 2 | 光影哲学（光引导视线、情绪暗示） |
| 3 | 色彩心理（色温=情感：暖琥珀=亲密、冷蓝=孤独） |
| 4 | 质感密度（真实但不写实：织物纹理、雨湿路面、手机微光） |
| 5 | 角色表演（姿态、微表情、人物间距） |
| 6 | 构图原则（清晰+深度、情感定位） |

---

## 2026-02-27

### TASK-AB-STYLE-DESC 前置 — slam_dunk 场域式 style_description 提供 ✅

**完成时间**: 2026-02-27 17:44
**关联任务**: TASK-AB-STYLE-DESC (P2) 前置准备
**产出**: TEAM_CHAT 中发布 B 组场域式改写版本

**任务类型**: Prompt 工程（场域式改写）

**依据**: 原则 7（约束+场域双层架构）

**完成内容**:
- [x] 分析当前命令式 style_description 的结构和冗余
- [x] 根据原则 7 编写场域式改写版本（6 句各司其职）
- [x] 确认与 mandatory/forbidden 约束层不重复
- [x] 发布到 TEAM_CHAT 通知 PM

**场域式改写要点**:
| 句 | 功能 |
|----|------|
| 1 | 传统锚定（Inoue + cinema-manga） |
| 2 | 人体质感（真实比例、运动员体魄、表情深度） |
| 3 | 墨法特征（粗线力量、细线阴影、网点渐变） |
| 4 | 光影叙事（体育馆荧光灯、黄金时段暖色调） |
| 5 | 色彩定调（饱和全彩，接地真实感） |
| 6 | 构图哲学（电影感角度，情感冲击力） |

---

### TASK-SLAMDUNK-COLOR — slam_dunk 彩色修复+color_mode增强 ✅ (P0)

**完成时间**: 2026-02-27 16:05
**关联任务**: E2E-TEST-2 发现灰度/彩色不统一
**文件**: `app/services/style_enforcer.py` + `app/services/storyboard_director.py` + `app/services/image_generator.py`

**任务类型**: 风格修复 + 增强功能

**Part A — slam_dunk preset 修复**:
- [x] `mandatory_keywords` 新增 `"full color manga"`, `"colored manga illustration"`（10→12个）
- [x] `forbidden_keywords` 新增 `"black and white"`, `"grayscale"`, `"monochrome"`（12→15个）
- [x] `style_description` 删除 `"dramatic black-and-white contrast"` → `"dramatic contrast with rich color palette"` + `"MUST be in FULL COLOR."`

**Part B — per-shot color_mode 增强**:
- [x] `storyboard_director.py` Stage 4 prompt 新增 COLOR MODE 规则说明
- [x] shot JSON 模板新增 `"color_mode"` 可选字段（full_color/grayscale/sepia）
- [x] `image_generator.py` 新增 color_mode 处理：在 StyleEnforcer.enforce_prompt() 之后追加 COLOR OVERRIDE 指令
- [x] Python 语法验证 3/3 通过

**关键产出**:
| 文件 | 说明 |
|------|------|
| `app/services/style_enforcer.py` | slam_dunk preset 全彩修复 |
| `app/services/storyboard_director.py` | Stage 4 color_mode 规则 + JSON 模板 |
| `app/services/image_generator.py` | color_mode → prompt COLOR OVERRIDE |

---

### TASK-DIALOGUE-SYSTEM Layer 2+3 — 对话系统 Stage 4 规则重构 ✅ (P0)

**完成时间**: 2026-02-27 16:05
**关联任务**: E2E-TEST-2 发现 dialogue 10%/thought 45% 失衡
**文件**: `app/services/storyboard_director.py` TEXT OVERLAY RULES 区域

**任务类型**: Prompt 优化（规则重构）

**Layer 2 — CRITICAL DISTRIBUTION RULES 完全重写**:
- [x] dialogue（含混合类型）≥60% 硬下限（原 40-50%）
- [x] thought 15-25%（原 20-25%）
- [x] narration ≤10%（原 ≤30%）
- [x] none 禁止（原 5-10%）
- [x] 新增 "Why dialogue dominance matters" 原理说明
- [x] 新增 SELF-CHECK 自检规则

**Layer 3 — Guidelines 重写**:
- [x] 删除 "not every shot needs text"、"Action/establishing shots → none"
- [x] 新增 "Every shot MUST have text. NO exceptions."
- [x] 新增 "When 2+ characters are together → MUST be dialogue"
- [x] Python 语法验证通过

**效果对比**:
| 指标 | Phase 2 规则 | Phase 3 规则 | E2E-TEST-2 实测 |
|------|-------------|-------------|----------------|
| dialogue(含混合) | 40-50% | **≥60%** | 25% |
| thought | 20-25% | 15-25% | 45% |
| narration | ≤30% | **≤10%** | 5% |
| none | 5-10% | **0%** | 20% |

**关键产出**:
| 文件 | 说明 |
|------|------|
| `app/services/storyboard_director.py` | TEXT OVERLAY RULES 完全重构 |

---

## 2026-02-26

### TASK-STYLE-SLAMDUNK — 灌篮高手风格预设 ✅ (P0)

**完成时间**: 2026-02-26 15:56
**关联决策**: DEC-012 决策 3
**文件**: `app/services/style_enforcer.py`

**任务类型**: 风格预设新增

**完成内容**:
- [x] 新增 `slam_dunk` 风格预设（StyleEnforcement 配置完整）
- [x] 10 个 mandatory_keywords：slam dunk manga style, Takehiko Inoue inspired, realistic manga proportions, dynamic linework, detailed anatomy, dramatic lighting and shadow, Japanese manga aesthetic, expressive character art, screentone effects, bold ink strokes
- [x] 12 个 forbidden_keywords：chibi, cute, super deformed, pastel colors, photorealistic photograph, 3D render, CGI, Western comic style, simple cartoon, flat colors, pixel art, watercolor, oil painting
- [x] 详细 style_description 强调"成熟写实漫画，非可爱向"
- [x] 额外新增 `korean_webtoon` 预设（为后续测试备用）
- [x] Python 语法验证通过，`get_supported_styles()` 确认 15 种风格

**关键产出**:
| 文件 | 说明 |
|------|------|
| `app/services/style_enforcer.py` | 新增 slam_dunk + korean_webtoon 预设 |

---

### TASK-TEXT-TYPE-OPT — text_type 分布优化 ✅ (P1)

**完成时间**: 2026-02-26 15:56
**关联决策**: DEC-012 决策 2
**文件**: `app/services/storyboard_director.py` TEXT OVERLAY RULES 区域

**任务类型**: Prompt 优化

**任务背景**:
Phase 1 E2E 测试发现 narration 占 86%（25/29 shots），dialogue 仅 1 shot。需要优化 Stage 4 prompt 引导 LLM 生成更合理的 text_type 分布。

**完成内容**:
- [x] 新增 CRITICAL DISTRIBUTION RULES 硬约束：narration ≤30%, dialogue 40-50%, thought 20-25%, none 5-10%
- [x] 新增 "Why this matters" 原理说明：narration 是最不吸引人的 text_type
- [x] 增强 Guidelines 场景引导：明确何时用 dialogue/thought/none，何时才用 narration
- [x] 参考 Tester 18:30 的 7 个 shot 改写建议
- [x] Python 语法验证通过

**效果对比**:
| 指标 | 优化前 | 优化后（预期） |
|------|--------|---------------|
| narration 占比 | 86% | ≤30% |
| dialogue 占比 | 3.4% | 40-50% |
| thought 占比 | 10.3% | 20-25% |
| none 占比 | 0% | 5-10% |

**关键产出**:
| 文件 | 说明 |
|------|------|
| `app/services/storyboard_director.py` | TEXT OVERLAY RULES 区域优化 |

---

### TASK-IDENTITY-DESIGN — 角色一致性框架文档 ✅ (P2)

**完成时间**: 2026-02-26 15:56
**关联决策**: DEC-012 决策 1
**文件**: `docs/CHARACTER_IDENTITY_FRAMEWORK.md`

**任务类型**: 设计文档

**任务背景**:
Founder 提出 Identity Anchors + Narrative Variables 概念框架，用于系统化角色视觉一致性管理。

**完成内容**:
- [x] Identity Anchors 定义（6 类锚点：面部骨骼、身体比例、肤色、发型发色、标志性配饰、基础服装）
- [x] 标志性配饰的特殊地位和应对策略（image_prompt 强调、参考图确认、Stage 2 标注）
- [x] Narrative Variables 6 层体系（情绪/物理/装备/环境/可见度/时间）
- [x] 各层优先级排序
- [x] Stage 2 角色设计数据结构建议（identity_anchors + narrative_defaults）
- [x] image_prompt 完整应用示例（陈默在雨中）
- [x] 已知限制 + 后续迭代方向

**关键产出**:
| 文件 | 说明 |
|------|------|
| `docs/CHARACTER_IDENTITY_FRAMEWORK.md` | v1.0 角色一致性框架文档 |

**后续方向**:
| 方向 | 优先级 | 说明 |
|------|--------|------|
| prompt 中强调标志性配饰 | P1 | `_build_character_description()` 中加 MUST BE VISIBLE |
| Stage 2 输出增加 identity_anchors 字段 | P2 | 显式标记锁定特征 |
| 单张 shot 重新生成功能 | P1 | 配饰丢失时可单独重跑 |

---

## 2026-02-24

### TASK-REF-PREPROCESS — 全部闭环 (DEC-009 + DEC-010) ✅

**闭环时间**: 2026-02-24 (DEC-010 确认)
**关联决策**: DEC-009（方案批准）→ DEC-010（正式闭环 + 源头方案）

**任务类型**: 跨团队协作 — 参考图预处理对比验证

**AI-ML 参与**: Step 1 指定对比测试 shot

**全流程回顾**:

| Step | 负责 | 完成时间 | 结果 |
|------|------|----------|------|
| 1 | AI-ML | 2026-02-13 16:00 | 指定 shot_34/36/22，覆盖留白+留黑、单双角色 |
| 2 | Backend | 2026-02-14 16:07 | 实现 `_preprocess_reference_to_aspect_ratio()` |
| 3 | Backend | 2026-02-14 16:24 | 6次API调用对比测试，全部成功 |
| 4 | Tester | 2026-02-14 17:05 | shot_34略有改善(白边~4%→~2-3%)，shot_36/22未复现 |
| 5 | PM | 2026-02-14 17:34 | 汇总报告：建议保留预处理代码 |

**Founder 决策 (DEC-010)**:
- 保留预处理代码（低成本无副作用有潜在收益）
- 不启动"后处理边缘检测+裁剪"
- 新增 TASK-SCENE-REF-ASPECT：从源头统一场景参考图为 2:3

**边缘问题最终状态**:
- 短期方案（prompt约束强化）✅ 有效但不彻底
- 中期方案（参考图预处理）✅ 轻微改善，代码保留
- 中期方案（2:3宽高比统一）✅ 从源头消除比例不匹配
- 长期方案（等待 Gemini API 修复）被动等待

---

### TASK-ASPECT-2x3 — AI-ML 确认无需修改 ✅

**确认时间**: 2026-02-24
**关联任务**: TASK-ASPECT-2x3 宽高比统一改为 2:3

PM 排查确认 AI-ML 负责的 prompt 模板文本（`docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md` 等）中无宽高比硬编码内容，AI-ML 无需修改任何文件。

---

## 2026-02-12

### TASK-REF-PREPROCESS Step 1: 指定对比测试 shot ✅

**完成时间**: 2026-02-13 16:00
**关联任务**: TASK-REF-PREPROCESS (DEC-009)

**任务类型**: 分析选择 - 对比测试shot指定

**任务背景**:
Founder批准DEC-009参考图预处理方案后，PM制定5步执行方案。Step 1由AI-ML负责：从边缘问题8个shot中选择2-3个用于对比测试。

**完成内容**:
- [x] 分析8个边缘问题shot的角色配置和参考图数量
- [x] 排除shot_01（无角色无参考图，预处理无效）
- [x] 选择3个shot，覆盖留白/留黑、单角色/双角色

**选择结果**:

| # | Shot | 边缘问题 | 类型 | 角色 | 参考图数 |
|---|------|---------|------|------|---------|
| 1 | shot_34 | 顶部大白边 | 留白 | Jerry | 1张 |
| 2 | shot_36 | 上下有黑边 | 留黑 | Jerry+Cici | 2张 |
| 3 | shot_22 | 上边有分隔线 | 留白 | Jerry+Cici | 2张 |

**下一步**: @Backend Step 2(代码) + Step 3(对比测试) → @Tester Step 4(验证) → @PM Step 5(汇总)

---

### 参考图预处理方案探索（边缘问题中期方案）✅

**完成时间**: 2026-02-12 17:48
**状态**: ✅ 已获批准 (DEC-009)
**关联任务**: 边缘问题根因分析 → 中期方案

**任务类型**: 技术探索 - 参考图宽高比预处理

**任务背景**:
边缘问题根因分析显示，参考图宽高比不匹配(0.73~0.78 vs 目标0.5625)是加剧Gemini API边缘留黑/留白问题的因素之一。Founder提出是否可通过预处理参考图来缓解此问题。

**探索内容**:
- [x] 查看所有参考图实际尺寸和宽高比
- [x] 计算裁剪到9:16需要裁掉的比例和像素
- [x] 分析参考图内容（角色位置、背景分布）
- [x] 实际模拟中心裁剪并目视验证
- [x] 分析代码中可注入预处理的位置
- [x] 评估边界情况和风险

**核心发现**:

| 参考图 | 原尺寸 | 裁剪后 | 裁掉比例 | 内容损失 |
|--------|--------|--------|---------|---------|
| Jerry fullbody | 864x1184 | 666x1184 | 宽度23% | 零 |
| CC fullbody | 896x1152 | 648x1152 | 宽度28% | 零 |
| Jerry portrait | 864x1184 | 666x1184 | 宽度23% | 零 |
| CC portrait | 896x1152 | 648x1152 | 宽度28% | 零 |

**结论**: 中心裁剪完全可行。参考图中角色天然居中，裁掉的只是两侧背景。

**实现建议**:
- 推荐在 `ImageGenerator.generate_image()` 中实现（可根据目标aspect_ratio动态匹配）
- 约10行代码，无额外API开销

**关键产出**:
| 文件 | 说明 |
|------|------|
| `.claude/agents/ai-ml-progress/context-for-others.md` | 详细方案和建议代码 |

**等待决策**: PM/Founder是否批准执行

---

## 2026-02-03

### V5修复任务 (FIX-A1/A2/A3/A4) ✅ 🆕🆕🆕

**完成时间**: 2026-02-03 19:00
**验收状态**: 待 @Tester V5验收 → @PM 最终核验
**关联任务**: PM V4综合复核 + Founder更正

**任务背景**:
PM完成V4综合复核后，Founder更正了部分任务要求：
- shot_29牵手、shot_40亲吻OK（约会契合后不违和）
- shot_27挽臂是主要问题（出现在牵手之前违和）
- shot_40微调：改为男生偷亲女生

**完成内容**:

**FIX-A1: 边缘填充约束 (P0)**
- [x] 已在PROMPT-1完成，FULL CANVAS COMPOSITION已强化

**FIX-A2: shot_27 挽臂→保护性触碰 (P0)**
- [x] 修改场景为"过马路时男生自然的保护性触碰"
- [x] 更新image_prompt：Kai轻触Cici后背引导过马路
- [x] 更新chinese_text：「过马路的时候，他轻轻护着我...好贴心。」
- [x] INTIMACY LEVEL CONSTRAINT强调PROTECTIVE触碰而非浪漫

**FIX-A3: shot_40 女亲男→男偷亲女 (P1)**
- [x] 修改image_prompt：Kai鼓起勇气偷亲Cici脸颊
- [x] 更新chinese_text旁白：「他鼓起勇气，在她脸颊偷偷落下一吻。」
- [x] Cici从主动方变为惊喜接受方（surprised delight, blushing）

**FIX-A3补充: shot_41 叙事一致性修复 (P2)** 🆕
- [x] PM审查发现shot_41与shot_40修改不一致
- [x] 原：描述Kai被亲后摸脸颊
- [x] 改：描述Kai亲完Cici后紧张期待她的反应

**FIX-A4: 角色一致性约束 (P1)**
- [x] 新增模板文档"角色一致性约束块"章节
- [x] shot_21: 添加Cici黑色针织衫约束 (NOT beige, NOT brown)
- [x] shot_23: 添加双角色服装约束
- [x] shot_29: 添加红围巾强制约束，在剪影中也必须可见

**关键产出**:
| 文件 | 说明 |
|------|------|
| `docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md` | 新增角色一致性约束块(v2.2) |
| `tests/test_comic_cc_kai.py` | shot_27/40修改 + shot_21/23/29角色约束 |

**下一步**: @Tester 执行V5验收测试

---

### HANDOFF-2026-02-03-001: Prompt优化 (PROMPT-1/PROMPT-2/PROMPT-2B) ✅

**完成时间**: 2026-02-03 16:00
**验收状态**: 待 @Tester V4验收 → @PM 最终核验
**关联任务**: PM V3独立复核后的Prompt优化任务

**任务类型**: Prompt 修复 - 解决边缘填充和亲密度问题 + 通用化

**任务背景**:
Backend完成架构重构(ARCH-1/2/3)和核心功能修复(CORE-1/2)后，PM分配Prompt优化任务给AI-ML：
- 8张图有边缘黑边/白边问题（01,17,22,34,35,36,39,42）
- 3张图亲密行为不符合首次约会设定（25,26,27）
- Founder决策：亲密行为约束应做成通用模板

**完成内容**:

**PROMPT-1: 边缘填充约束**
- [x] 更新 `docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md`
  - 所有6个模板的 `FULL CANVAS COMPOSITION` 指令块增强
  - 添加 "NO black borders, NO white margins, NO blank areas at ANY edge"
  - 添加 "The composition must touch all four sides of the frame without any padding"
- [x] 更新 `tests/test_comic_cc_kai.py`
  - `TEXT_FREE_REQUIREMENT` 常量添加 `FULL CANVAS COMPOSITION` 指令块

**PROMPT-2: 亲密行为约束**
- [x] Shot 25 添加 `INTIMACY LEVEL CONSTRAINT (First Date)` 指令块
- [x] Shot 26 添加 `INTIMACY LEVEL CONSTRAINT (First Date)` 指令块
- [x] Shot 27 添加 `INTIMACY LEVEL CONSTRAINT (First Date)` 指令块
  - 约束内容：保持适当距离、NO arm linking、NO hand-holding initiated
  - 明确这是首次约会场景，角色刚刚认识

**PROMPT-2B: 亲密行为约束通用化** 🆕
- [x] 在 `docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md` 创建 **"场景情境约束块"** 章节
- [x] 添加3种通用约束模板：
  - **首次约会 (First Date)** - 控制初次见面场景的亲密度
  - **热恋期 (Honeymoon Phase)** - 允许热恋情侣的亲密互动
  - **老友重逢 (Reunion)** - 久别重逢的情感表达
- [x] 模板版本更新到 v2.1

**关键产出**:
| 文件 | 说明 |
|------|------|
| `docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md` | FULL CANVAS增强 + 场景情境约束块(v2.1) |
| `tests/test_comic_cc_kai.py` | TEXT_FREE_REQUIREMENT + Shots 25-27亲密约束 |

**通用性收益**:
- 未来任何"初次约会"类故事可以直接引用模板
- 无需在每个测试文件中重复编写约束
- 支持多种情境：首次约会、热恋期、老友重逢

**下一步**: @Tester 执行V4验收测试

---

## 2026-02-02

### HANDOFF-2026-02-02-014: V2+ Prompt优化 P1任务 ✅ 🆕

**完成时间**: 2026-02-02 13:00
**验收状态**: 待 @Tester V3验收 → @PM 核验
**关联任务**: V2综合分析后的Prompt修复

**任务类型**: Prompt 修复 - 解决解剖、内容安全、构图问题

**任务背景**:
Backend完成P1任务（TEXT_FREE强化、Leave指令清理）后，PM分配剩余P1任务给AI-ML：
- Shot 01/03 解剖问题（双手腕、六指）
- Shot 28 内容安全触发
- Shot 34 构图问题（部分肢体）

**完成内容**:

**TASK-4: 解剖约束Prompt**
- [x] Shot 01 添加 `ANATOMY REQUIREMENT` 指令块
  - 要求只有一对手、每只手5个手指、连接到同一对手腕
- [x] Shot 03 添加 `ANATOMY REQUIREMENT` 指令块
  - 要求每只手5个手指、解剖学正确
- [x] Shot 28 添加 `ANATOMY REQUIREMENT` 指令块
  - 要求每只手5个手指、手腕自然连接

**TASK-5: Shot 28 内容安全重写**
- [x] 移除敏感触发词:
  - "unconscious invitation" → 删除
  - "tension is palpable" → 删除
  - "electric moment" → 删除
- [x] 替换为安全版本:
  - "natural walking posture"
  - "quiet anticipation"
  - "comfortable closeness"

**TASK-6: Shot 34 构图优化**
- [x] 添加 `COMPOSITION REQUIREMENT` 指令块:
  - 画面边界在中控台处结束
  - Cici不在镜头中（POV视角）
  - 禁止画面边缘出现部分肢体
  - 所有可见身体部位必须完整自然

**验证**:
- [x] Python语法验证通过
- [x] Grep确认所有修改已生效

**关键产出**:
| 文件 | 说明 |
|------|------|
| `tests/test_comic_cc_kai.py` | 修复后的测试脚本（Shot 01, 03, 28, 34） |

**修改对比**:
| Shot | 问题 | 修复 |
|------|------|------|
| 01 | 双手腕 | ANATOMY REQUIREMENT - 单人双手 |
| 03 | 六指 | ANATOMY REQUIREMENT - 5指约束 |
| 28 | 安全触发 | 敏感词替换 + ANATOMY |
| 34 | 边缘肢体 | COMPOSITION REQUIREMENT + POV |

**下一步**: @Tester 执行V3验收测试

---

## 2026-01-31

### TASK-CC-KAI-FIX-001: Prompt模板修复 ✅ 🆕

**完成时间**: 2026-01-31 17:00
**验收状态**: 待 @Backend 重新测试后验收
**关联任务**: HANDOFF-2026-01-31-012

**任务类型**: Prompt 修复 - 解决32+个图片问题

**任务背景**:
Founder审查42张图片发现32+问题（AI气泡20+、留白10+、乱码5+、服装错误3+）。PM独立审查确认Prompt模板约束不足是根本原因。

**修复内容**:
- [x] 替换 TEXT_FREE_REQUIREMENT 为 "ABSOLUTELY NO TEXT ALLOWED" 强约束版本
- [x] 删除 57行 "Leave clean space..." 矛盾指令
- [x] 强化 Shot 38 (拥抱) 服装描述：BLACK long wool coat (NOT red!)
- [x] 强化 Shot 40 (脸颊之吻) 服装描述：BLACK long wool coat (NOT red, NOT teal!)
- [x] 强化 Shot 22, 39 服装描述
- [x] Python 语法验证通过

**关键产出**:
| 文件 | 说明 |
|------|------|
| `tests/test_comic_cc_kai.py` | 修复后的测试脚本 |

**修改对比**:
| 修改前 | 修改后 |
|--------|--------|
| TEXT-FREE IMAGE REQUIREMENT | ABSOLUTELY NO TEXT ALLOWED |
| 57行 Leave 指令 | 全部删除 |
| 服装描述较弱 | 明确强调 BLACK + NOT red/teal |

---

## 2026-01-30

### HANDOFF-2026-01-30-011: Kai与Cici初次约会故事脚本 ✅

**完成时间**: 2026-01-30 12:30
**验收状态**: 待 @Backend 生成图片后验收
**关联任务**: Kai与Cici初次约会条漫测试

**任务类型**: 脚本编写 - Korean Webtoon Style

**任务背景**:
创始人发起都市情感题材测试，PM完成42张详细分镜大纲，需要AI-ML完善Prompt和文字脚本。

**完成内容**:
- [x] 2个角色的完整 physical + clothing 描述（英文）
  - Kai (男主, 33岁): 黑短发、黑框眼镜、黑紫色毛衣+牛仔裤+黑大衣
  - Cici (女主, 33岁): 深棕色长波浪发、黑色针织衫+浅灰裙+黑大衣+红丝巾
- [x] Korean Webtoon Style 风格指令块
- [x] 42张图的全英文 image_prompt
- [x] 42张图的中文旁白/对话/内心独白
- [x] 4个情感重点镜头特别标注（⭐ EMOTIONAL HIGHLIGHT SHOT）

**关键产出**:
| 文件 | 说明 |
|------|------|
| `docs/CC_KAI_STORY_SCRIPT.md` | 42图完整脚本 |

**角色设计**:
| 角色ID | 名字 | 关键标记 |
|--------|------|----------|
| kai | Kai | 黑框眼镜、黑短发、温和气质 |
| cici | Cici | 深棕波浪长发、红丝巾、优雅气质 |

**关键设计点**:
| 设计点 | 说明 |
|--------|------|
| 韩漫风格前缀 | 每个Prompt强制注入风格指令 |
| 参考图使用 | 明确指定"FACE REFERENCE ONLY"，服装用故事描述 |
| 无文字Prompt | 配合 TextOverlayServiceV2 后处理叠加 |
| 情感重点 | Shot 10-11, 29, 38, 40 特别强调 |

**验证重点**: 韩漫风格稳定性、双人互动情感表达、服装一致性（42张）

---

## 2026-01-28

### TASK-VERIFY-001-B: 故事C《最后的记忆商人》详细脚本 ✅ 🆕

**完成时间**: 2026-01-28 19:00
**验收状态**: 待 @Backend 生成图片后验收
**关联任务**: TASK-VERIFY-001 多风格通用性验证

**任务类型**: 脚本编写 - 赛博朋克风格

**任务背景**:
PM 完成故事C《最后的记忆商人》大纲和分镜设计后，需要完善详细脚本用于赛博朋克风格验证测试。

**完成内容**:
- [x] 3个角色的完整 physical + clothing 描述
- [x] 赛博朋克风格指令块（霓虹、湿地反光、全息、暗黑氛围）
- [x] 15张图的全英文 image_prompt
- [x] 15张图的中文旁白/对话/心理
- [x] 特殊效果标注（记忆场景明亮对比、追逐动态）
- [x] 角色视觉识别标记表

**关键产出**:
| 文件 | 说明 |
|------|------|
| `docs/COMIC_STORY_C_CYBERPUNK_SCRIPT.md` | 故事C完整脚本 |

**角色设计**:
| 角色ID | 名字 | 关键标记 |
|--------|------|----------|
| char_001 | 林夜 | 银色左眼义眼(蓝光)、右脸疤 |
| char_002 | 老陈 | 白发、褪色蓝工装、金属拐杖 |
| char_003 | 凯拉 | 红色双义眼、全金属右臂 |

**验证重点**: 赛博朋克风格稳定性、赛博义眼一致性、记忆场景对比效果、追逐动感

---

### TASK-RESILIENCE-001-B: Prompt安全改写规则设计 ✅

**完成时间**: 2026-01-28 01:00
**验收状态**: 待 @Backend 集成后验收
**关联任务**: TASK-RESILIENCE-001 图像生成韧性机制

**任务类型**: Prompt 工程 - 安全改写规则设计

**任务背景**:
故事B《断剑》测试中，Shot 06 因 Gemini 内容安全过滤失败。敏感词包括："motionless youth", "dark spreading pool", "killer/victim", "death of innocence"。PM 分析后认为需要建立智能改写机制。

**完成内容**:
- [x] 6大类敏感词分类（死亡、暴力、血腥、武器、尸体、极端情绪）
- [x] 80+ 敏感词 → 安全替代词映射
- [x] 4种题材特定规则（武侠、悬疑、赛博朋克、战争）
- [x] Haiku 智能改写 Prompt 模板（保留艺术意图）
- [x] 辅助函数：检测、替换、构建改写请求

**关键产出**:
| 文件 | 说明 |
|------|------|
| `app/prompts/prompt_safety_rewrite.py` | 完整改写规则 + Prompt 模板 |

**核心组件**:
| 组件 | 说明 |
|------|------|
| `SensitiveCategory` | 6种敏感类型枚举 |
| `SENSITIVE_WORD_REPLACEMENTS` | 敏感词 → 安全替代映射 |
| `GENRE_SPECIFIC_REPLACEMENTS` | 题材特定规则 |
| `SAFETY_REWRITE_PROMPT` | Haiku 改写 Prompt 模板 |
| `detect_sensitive_content()` | 检测函数 |
| `apply_simple_replacements()` | 简单替换函数（零成本兜底） |
| `build_rewrite_prompt()` | 构建改写请求函数 |

**成本估算**: Haiku 改写 ~$0.001/次（仅在 CONTENT_SAFETY 错误时触发）

---

## 2026-01-27

### TASK-VERIFY-001-B: 故事B《断剑》详细脚本 ✅

**完成时间**: 2026-01-27 23:30
**验收状态**: 待 @Backend 生成图片后验收
**关联任务**: TASK-VERIFY-001 多风格通用性验证

**任务类型**: 脚本编写 - 古装武侠 + 水墨风格

**任务背景**:
创始人指出只测试一个故事不足以验证通用性，需要测试2-3个完全不同风格的故事。

**完成内容**:
- [x] 4个角色的完整 physical + clothing 描述
- [x] 水墨风格指令块（含回忆场景、动作场景处理）
- [x] 15张图的全英文 image_prompt
- [x] 15张图的中文旁白/对话/心理
- [x] 特殊效果标注（回忆柔光、动作场景、红色强调）

**关键产出**:
| 文件 | 说明 |
|------|------|
| `docs/COMIC_STORY_B_WUXIA_INK_SCRIPT.md` | 故事B完整脚本 |

**角色设计**:
| 角色ID | 名字 | 说明 |
|--------|------|------|
| master_old | 白川 | 60岁老剑客，白发束髻，麻布长袍 |
| master_young | 白川(年轻) | 30岁，回忆场景用 |
| disciple | 林风 | 25岁徒弟，蓝色劲装 |
| enemy | 周沧 | 50岁蒙面仇人 |

**验证重点**: 水墨风格稳定性、古装服饰一致性、年龄版本一致性、动作场景动态感

---

### TASK-OPT-005-A: AI智能推荐泡泡位置 ✅

**完成时间**: 2026-01-27 20:30
**验收状态**: 待 @Backend 集成 TASK-OPT-005-B 后验收
**关联任务**: HANDOFF-2026-01-27-002

**优化类型**: 方案升级 - AI直接推荐泡泡位置

**任务背景**:
TASK-OPT-004验收后，创始人发现泡泡仍遮挡角色脸部：
- shot_04: 爸爸泡泡遮住整张脸
- shot_14: 爸爸泡泡遮住额头

**PM评估通用性后升级方案**:

| 边缘情况 | 旧方案 | 新方案 |
|----------|--------|--------|
| 特写镜头 | ❌ 头顶在画面外 | ✅ AI推荐侧边 |
| 俯视/仰视 | ❌ head_top_y不准 | ✅ AI理解透视 |
| 角色在顶部 | ❌ 需边界检查 | ✅ AI自动考虑 |
| 多人说话 | ❌ 需避让算法 | ✅ AI一次规划 |
| 非人类角色 | ❌ "头顶"不适用 | ✅ AI理解形态 |

**完成内容**:
- [x] Step 3 改为 "Bubble Placement Recommendation"
- [x] 新增 "BUBBLE PLACEMENT RULES" 指令块（6条规则）
- [x] 输出格式: `{"x_percent": 25}` → `{"bubble_x_percent": 25, "bubble_y_percent": 8}`
- [x] Debug模式包含 `placement_reasoning`
- [x] 更新设计说明和示例代码

**关键产出**:
| 文件 | 说明 |
|------|------|
| `app/prompts/character_position_detection.py` | v3 - AI直接推荐泡泡位置 |

**成本估算**: 不变 (~$0.04/故事)

---

### TASK-OPT-004-A: Prompt改为百分比坐标输出 ✅ (已升级)

**完成时间**: 2026-01-27 18:00
**验收状态**: ⚠️ 验收通过后发现遮挡问题，已升级为 TASK-OPT-005-A
**关联任务**: HANDOFF-2026-01-27-001

**优化类型**: Prompt精度提升

**任务背景**:
创始人审查第一轮优化结果，发现泡泡位置仍不够精确：
- shot_04: 女儿泡泡离角色较远
- shot_07: 小女孩泡泡太远，父亲泡泡碰头
- shot_14: 两个泡泡位置都不理想

**完成内容**:
- [x] Step 3: Position Classification → Position Estimation (百分比)
- [x] 输出格式: `{"position": "left"}` → `{"x_percent": 15}`
- [x] 添加百分比估算方法和示例

**后续**: 验收通过后创始人发现泡泡遮挡脸部，升级为 TASK-OPT-005-A

**成本估算**: 不变 (~$0.04/故事)

---

## 2026-01-26

### TASK-OPT-002-A: Haiku角色识别Prompt设计 ✅ (已升级)

**完成时间**: 2026-01-26 20:00
**验收状态**: ⚠️ 已被 TASK-OPT-004-A 升级
**关联任务**: HANDOFF-2026-01-26-002

**优化类型**: 多模态Prompt工程

**任务背景**:
对话泡泡位置依赖硬编码的 `speaker_position`，但AI生成的图片中角色位置不可预测。
需要设计Prompt让Claude 4.5 Haiku通过参考图比对来识别角色位置。

**挑战与解决**:

| 挑战 | 解决方案 |
|------|----------|
| 相似角色区分 | 关注细微差异：服装颜色、配饰、发饰、身高 |
| 部分遮挡处理 | 面部不可见时使用服装/配饰识别，降低置信度 |
| 多风格适配 | 优先主要特征（发型发色），风格差异用置信度反映 |

**设计要点**:
- [x] 三段式图像映射（Image 1=场景，Image 2+=参考图）
- [x] 三步识别方法论（扫描→匹配→分类）
- [x] ~~左/中/右三分法位置分类~~ → 已改为百分比 (TASK-OPT-004-A)
- [x] high/medium/low三级置信度标准
- [x] Debug模式返回识别依据
- [x] 辅助函数：build_prompt(), extract_character_description_for_haiku()

**关键产出**:
| 文件 | 说明 |
|------|------|
| `app/prompts/character_position_detection.py` | 完整Prompt模板 + 辅助函数 + 使用示例 |

**成本估算**: ~$0.04/故事（15 shots）

---

### TASK-FIX-005: 测试脚本Prompts直接修复 ✅

**完成时间**: 2026-01-26 12:00
**验收状态**: 待 @Tester 重新测试验收
**关联任务**: HANDOFF-2026-01-26-001

**优化类型**: Prompt修复（解决V2测试图片问题）

**任务背景**:
PM二次审核V2测试图片发现上轮修复不彻底：
1. 留白仍存在 (10/15张) - 测试脚本prompts未同步更新
2. 乱码文字泄露 (4/15张) - TEXT_FREE指令不够强
3. LLM生成对话泡泡占位 - prompts提到"dialogue bubble"

**完成内容**:
- [x] 加强 TEXT_FREE_REQUIREMENT 为 "ABSOLUTELY NO TEXT ALLOWED"
- [x] 删除所有15个shot的 "COMPOSITION GUIDANCE FOR TEXT OVERLAY" 部分
- [x] 删除所有 "Leave clean space for dialogue bubble" 指令

**关键产出**:
| 文件 | 说明 |
|------|------|
| `tests/test_comic_full_story_v2.py` | 15个shot的prompts全部修复 |

**新版TEXT_FREE指令**:
```
ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

---

## 2026-01-23

### TASK-FIX-001: Prompt模板修复 (v2.0) ✅

**完成时间**: 2026-01-23 02:00
**验收状态**: 部分有效（需要TASK-FIX-005补充）
**关联任务**: HANDOFF-2026-01-23-001

**优化类型**: Prompt模板修复

**任务背景**:
创始人审核测试图片发现：图片留白、百分比泄露

**完成内容**:
- [x] 修改 `docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md`
- [x] 移除所有 `(XX-XX% height)` 百分比数字
- [x] 将"预留空间"改为"禁止留白"表述
- [x] 添加 `FULL CANVAS COMPOSITION` 指令块

**关键产出**:
| 文件 | 说明 |
|------|------|
| `docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md` | v2.0核心指令块 |

**后续发现**: 测试脚本 `test_comic_full_story_v2.py` 中的prompts未同步更新，由TASK-FIX-005补充修复

---

## 2026-01-22

### 条漫完整故事脚本 (TASK-A) ✅

**完成时间**: 2026-01-22 23:15
**验收状态**: 通过（93.3%）

**完成内容**:
- [x] 角色设计（4角色x多时期，完整physical+clothing）
- [x] 15张图的英文image_prompt（Ghibli-inspired风格）
- [x] 15张图的中文旁白/对话/心理
- [x] text_type / speaker_position 标注
- [x] Shot 07-10 回忆场景 MEMORY SCENE TREATMENT
- [x] Shot 09 情感强调

**关键产出**:
| 文件 | 说明 |
|------|------|
| `docs/COMIC_FULL_STORY_SCRIPT.md` | 15图完整脚本 |

---

### 无文字Prompt模板 (TASK-001) ✅

**完成时间**: 2026-01-22 19:30
**验收状态**: 通过

**完成内容**:
- [x] 6种模板类型的无文字版本
- [x] TEXT-FREE IMAGE REQUIREMENT 核心指令

**关键产出**:
| 文件 | 说明 |
|------|------|
| `docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md` | 无文字Prompt模板 |

---

## 2026-01-15

### 书籍解说 Prompt 模板 (Side Test) ✅

**完成时间**: 2026-01-15
**验收状态**: 待 @backend 测试验证

**优化类型**: 新场景Prompt设计

**任务背景**:
为"书籍解说视频"场景设计Prompt模板，验证序话Story能否用于生成书籍解说视频（抖音/B站常见的"3分钟讲完一本书"形态）。

**完成内容**:
- [x] `book_narration_prompt.py` - 解说脚本生成 (Stage 2)
- [x] `book_storyboard_prompt.py` - 配图分镜 (Stage 3)
- [x] 概念可视化指令块设计
- [x] 多风格支持 (illustration, realistic, watercolor, ink, oil_painting, digital_art)

**核心设计**:

| 维度 | 短剧 Prompt | 书籍解说 Prompt |
|------|-------------|-----------------|
| 核心关注 | 角色一致性 | 概念可视化 |
| 角色处理 | 完整physical+clothing | 通用人物描述 |
| 连续性 | 场景环境连续 | 视觉风格统一 |
| 动作 | 具体动作、表情 | 偏静态、意象化 |

**关键产出**:
| 文件 | 说明 |
|------|------|
| `app/prompts/book/book_narration_prompt.py` | 解说脚本生成 |
| `app/prompts/book/book_storyboard_prompt.py` | 配图分镜生成 |

**交接文档**:
- `.team-brain/handoffs/BOOK_PROMPT_COMPLETED_FOR_BACKEND.md`

---

## 2025-12-23

### 角色一致性突破 (teststory6.4-6.6) ✅

**完成时间**: 2025-12-23
**验收状态**: 通过

**完成内容**:
- [x] 混合模型架构设计 (Flash参考图 + Pro Shot)
- [x] 分层面部特征描述
- [x] CRITICAL FACIAL FEATURES 指令块
- [x] 19种角色类型 Prompt Builder

**关键发现**:
```
Pro模型不只是"看到"参考图，而是**理解**每个角色的身份边界
3人场景: 70-80% → 100%
6人场景: ~50% → ~90%
```

**关键产出**:
| 文件 | 说明 |
|------|------|
| `app/services/character_prompt_builder.py` | 角色描述构建 |
| `app/services/storyboard_prompts.py` | Prompt 模板 |
| `app/services/style_enforcer.py` | 风格强制 |

**成本影响**:
- Flash 方案: $3.11/故事 (70-80% 一致性)
- Pro 方案: $9.35/故事 (100% 一致性)
- 选择: Pro 方案 (用户体验优先)

---

## 2025-01-05

### Shot 间连续性优化 ✅

**完成时间**: 2025-01-05
**验收状态**: 通过

**完成内容**:
- [x] VISUAL CONTINUITY REFERENCE 指令块
- [x] previous_shot_image 参数传递
- [x] IMAGE 编号正确映射

**关键产出**:
| 文件 | 位置 |
|------|------|
| `storyboard_prompts.py` | L1420-1443 |

---

## 任务归档模板

```markdown
### [任务标题] ✅

**完成时间**: YYYY-MM-DD
**验收状态**: 通过/部分通过

**优化类型**: Prompt结构/模型选择/成本优化

**完成内容**:
- [x] 内容1
- [x] 内容2

**效果对比**:
| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| xxx | x% | y% |

**关键产出**:
| 文件 | 说明 |
|------|------|
| path/to/file | 说明 |
```


---

### TASK-T5-FIXBATCH BGM-1 95 风格 music_hint 字典 ✅ (2026-04-27 PM 代更归档)

**完成时间**: 2026-04-27 16:25 (~9 min agent 时间)
**验收状态**: ✅ 187/187 unit + 7/7 architecture pass

**关键产出**:
| 文件 | 内容 |
|------|------|
| `app/services/style_music_hints.py` | 105 entries × 5 字段 |
| `tests/test_style_music_hints.py` | 187 测试 |

**接口**:
- `get_raw_hint(style_id) -> str`
- `get_music_hint(style_id) -> dict`

**T5 BGM 不对味的根因解决**: pencil_sketch + 悲伤故事 → "intimate acoustic, pencil-on-paper quietness" (不再是亮 acoustic guitar)


---

## 2026-04-29 17:33 Wave 5.1 O-1 outline 一致性 prompt + JSON OBS（PM 代更归档）

详见 current.md。改动文件 1 个，pytest 7/7 PASS。
