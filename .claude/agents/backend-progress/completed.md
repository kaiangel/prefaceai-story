# Backend Agent - 已完成任务

> 按时间倒序记录已完成的工作

---

## 2026-04-01

### TASK-JSON-REPAIR-V3 完成 ✅

- `_fix_unescaped_quotes()` 正则 → 状态机（逐字符 + in_string + 前瞻）
- 10/10 测试全 PASS

### TASK-LOGGING-FIX 完成 ✅

- TeeStream → Python logging 模块 (4 文件)
- 26 处 print→logger.info + 零残留

### TASK-JSON-REPAIR-V2 完成 ✅

- 正则扩展: +全角标点 `\uff00-\uffef` + 长度 `{1,50}`
- 修复殡仪馆故事中"谢谢你...人"，后跟全角逗号的场景

### TASK-PERSISTENT-LOG 完成 ✅

- `main.py` TeeStream: stdout/stderr 同时写终端 + `storage/logs/backend.log`
- `storage/` 已在 `.gitignore`

### TASK-DOC-FORMAT 完成 ✅

- `projects.py`: idea 为空+有 doc → 直接用 doc（不加 `\n\n---\n附加文档内容:` 前缀）

### TASK-DOC-ONLY-FIX Backend 完成 ✅

- `project.py` schema: `original_idea` 允许空（纯文档上传场景）
- `projects.py`: 双重校验 idea+doc 都空 → 400

### TASK-JSON-REPAIR 完成 ✅

- `story_outline_generator.py`: `_fix_unescaped_quotes()` + `_extract_json()` 预处理
- 修复 Claude 中文 JSON 未转义双引号 (U+0022→U+201C/U+201D)
- 测试: 3/3 PASS (校霸、正常JSON不变、多处引号)

### TASK-DEBUG-LOGGING 完成 ✅

- `utils.py` 5 埋点 + `projects.py` 2 埋点 = 7 个日志点
- 只加 print，零逻辑改动

### TASK-PHASE2-PIPELINE 完成 ✅ (含 ProjectStyleConfig bug 修复)

- `style_enforcer.py`: +`create_custom_enforcement(analysis)` 类方法
- `reference_image_manager.py`: `generate_character_multi_refs` +`seed_image` + `set_reference` dict 格式修复
- `scene_reference_manager.py`: `generate_anchor_images` +`seed_images` 参数
- `pipeline_orchestrator.py`: `run()` +3 参数 + 自定义风格 enforcement + seed 传参

### TASK-PHASE2-INTEGRATE Backend 完成 ✅

- `app/schemas/project.py`: +3 字段 (custom_style_analysis, character_refs_analysis, scene_refs_analysis)
- `app/models/project.py`: +3 JSON 字段
- `app/api/projects.py`: create_project 存储 + generate_outline 传参
- `story_outline_generator.py`: 移除 _build_prompt 末尾重复 + else 分支补"现在开始生成故事大纲："（PM Review #7 修复）

### TASK-PHASE2-INFRA 完成 ✅

- 新建 `app/services/file_storage.py`: validate_image + compress_image + save/delete_upload
- `app/api/utils.py`: +3 分析端点 (analyze-style/character/scene) + `_vision_analyze` helper + AI-ML Prompt 1-3
- `story_outline_generator.py`: +`_build_user_reference_context()` (Prompt 4) + `generate()` 新增 3 参数
- 安全校验: 图片类型+大小+PIL验证 + 超 2048px 等比缩小

### TASK-UTILS-ASYNC-FIX 完成 ✅

- `app/api/utils.py` OCR 端点: Gemini 同步→异步 + Anthropic 同步→异步

### Phase 1 Step 2: StyleEnforcer 28 + Literal 28 完成 ✅

- `app/services/style_enforcer.py`: +13 个 `StyleEnforcement` 条目（AI-ML 设计）
- `app/schemas/project.py`: `StylePreset` Literal 15 → 28
- 验证: StyleEnforcement 28 ✅ + StylePreset 28 ✅

### TASK-STYLE-LITERAL-FIX 完成 ✅ (P0)

- `app/schemas/project.py`: `StylePreset` Literal 10 → 15，删 `"chinese"` 残留，加 5 个缺失风格
- 修复 422 bug（含默认 `korean_webtoon`）

### TASK-DOC-TEXT-WIRE Backend 完成 ✅

- `app/schemas/project.py`: +`document_text` 字段
- `app/api/projects.py`: `create_project` 拼接 `document_text` 到 `original_idea`

### TASK-OCR-ENDPOINT 完成 ✅

- 新建 `app/api/utils.py`: `POST /api/utils/ocr` (Gemini + Haiku) + `POST /api/utils/parse-document` (pdfplumber)
- `app/main.py` +2 行注册

### TASK-ASPECT-RATIO-WIRE Backend 完成 ✅

- `app/schemas/project.py` L32: +`aspect_ratio` 字段到 `ProjectCreate`
- `app/api/projects.py` L50: +`aspect_ratio=project_data.aspect_ratio` 到 `create_project`

### TASK-GEMINI-MODEL-FIX 完成 ✅

- 7 文件 9 处 Gemini 备用模型 ID → `gemini-3.1-flash-lite-preview`
- PM 派发 6 文件 + 额外 `story_generator.py` (共 7 文件)
- 旧 ID `gemini-3-flash-preview` + `gemini-3.1-flash-preview` 零残留

### TASK-OUTLINE-STORAGE 完成 ✅

- `app/models/project.py`: +3 字段 (`aspect_ratio`, `raw_outline_json`, `confirmed_outline_json`)
- `app/api/projects.py`: `generate_outline` 存 raw + 新增 `POST /{project_id}/confirm-outline`
- 遵循 Ben 架构模式 (verify_user + get_db + 归属验证)

---

## 2026-03-24

### TASK-OUTLINE-LLM-FIX 第 1-3 项完成 ✅

- `story_outline_generator.py` 3 项修复:
  1. System prompt 集成（AI-ML 设计，含角色定位 + JSON 约束 + 中英文字段分工 + 新增字段强化）
  2. Debug logging（JSON 提取失败时打印 provider/length/preview 前 500 字）
  3. `Anthropic` → `AsyncAnthropic` + `await` + `max_tokens` 8631→16384
- 验证: Python syntax ✅

### TASK-ENVVAR-FIX 完成 ✅

- 5 文件 `os.getenv("ANTHROPIC/GEMINI_API_KEY")` → `settings.ANTHROPIC/GEMINI_API_KEY`
- 每个文件: 删 `import os` + 加 `from app.config import settings`
- 根因: `pydantic-settings` 加载 `.env` 到 `settings` 对象不写入 `os.environ`，FastAPI 下 `os.getenv()` 返回 None
- 验证: 5/5 syntax ✅ + 零残留 ✅

### TASK-STAGE1-API 完成 ✅

- `app/api/projects.py` 新增 `POST /{project_id}/generate-outline`
- 遵循 Ben 架构模式（verify_user + get_db + Project 归属验证）
- 调用 `StoryOutlineGenerator.generate()`，snake_case → camelCase 映射
- 返回格式与前端 `StoryOutline` 接口对齐
- 生成后自动更新 Project.title
- 零改动 Ben 现有端点

---

## 2026-03-18

### TASK-CORS-RESTRICT 完成 ✅

- `app/main.py` L40: `allow_origins=["*"]` → `["https://prefaceai.mov", "http://localhost:3000"]`

### TASK-LOG-SANITIZE 完成 ✅

- 新建 `app/middleware/log_sanitizer.py`: patch `builtins.print`，正则脱敏
- 新建 `app/middleware/__init__.py`
- `app/main.py` +3 行注册
- 覆盖: ANTHROPIC/GEMINI/OPENAI/VOLCENGINE API Key + sk-ant/sk-/AIzaSy/AKLT 格式
- 验证: 4 项脱敏测试 PASS + CORS 白名单确认 + print patch 确认

---

## 2026-03-17

### TASK-OB2-MODEL-SYNC + OB-3 修正 完成 ✅

| # | 修复 | 文件 |
|---|------|------|
| OB-3 | CLAUDE_MODEL `claude-haiku-4-5-20251001` → `claude-sonnet-4-6` | `story_generator.py` L18 |
| OB2-1 | GEMINI_MODELS[0] → `gemini-3.1-flash-preview` | `story_generator.py` L21 |
| OB2-2 | 注释 "Gemini 3 Pro" → "Gemini 3.1 Flash" | `alignment_service.py` L44 |
| OB2-3 | gemini_model → `gemini-3.1-flash-preview` | `alignment_service.py` L46 |
| 额外 | docstring "Gemini 3 Pro" → "Gemini 3.1 Flash" | `alignment_service.py` L34 |

验证: Python import ✅ + `app/` 目录 `gemini-3-pro-preview` 零残留 ✅

### TASK-REWRITER-CLEANUP 完成 ✅ (11:30)

1. `pipeline_orchestrator.py` L375: `generate_shot_image_phase2` → `generate_shot_image_phase2_safe`
2. `prompt_rewriter.py` + `image_generator.py`: 7 处 "Haiku" → "Sonnet 4.6" 注释清理
3. `prompt_rewriter.py`: 6 处 `gemini-3-pro-preview` → `gemini-3.1-flash-preview`

---

## 2026-03-16

### N13-FIX + TASK-IMG-SAFETY-RETRY Backend 完成 ✅ (19:00)

**N13-FIX**: `pipeline_orchestrator.py` — Stage 1 后自动补全 spouse_of 反向关系

**L1**: `image_generator.py` 2 处日志 `MAX_RETRIES` → `attempt + 1`

**L2**: `scene_reference_manager.py` — `_simplify_anchor_prompt()` + CONTENT_SAFETY 简化重试

**L3a**: `scene_reference_manager.py` + `prompt_rewriter.py` — 场景参考 PromptRewriter 改写重试

**L3b**: `reference_image_manager.py` + `prompt_rewriter.py` — 角色参考 PromptRewriter 改写重试

**PromptRewriter**: 新增 `rewrite_scene_ref()` + `rewrite_char_ref()` 方法

**验证**: 5/5 import ✅ + 逻辑测试 ✅

---

## 2026-03-13

### OB-1 修复完成 ✅ (20:20)

- `shot_validator.py` 3 处 early-return 补齐 `has_visual_unnaturalness: False` + `unnaturalness_details: ""`
- 4 处返回点结构统一

---

### Phase 5 T-H-Backend 完成 ✅ (19:45)

**T-H-Backend [P2] ShotValidator 画面自然度维度（Phase 1 仅日志）**:
- `shot_validator.py` 6 处改动:
  1. VALIDATION_PROMPT_BASE 新增 Q3（3 子维度 D1+D2+D3 + 风格排除块）
  2. VALIDATION_PROMPT_PROPS 编号 3→4
  3. VALIDATION_RESPONSE_BASE 新增 has_visual_unnaturalness + unnaturalness_details
  4. VALIDATION_RESPONSE_WITH_PROPS 同上
  5. max_tokens 256→384
  6. 结果提取+日志，不纳入 valid 判定，result_dict 含新字段

**验证**: Python import ✅ + 逻辑测试 5/5 ✅

---

### Phase 3 T-C-Backend + T-I 完成 ✅ (19:00)

**T-C-Backend [P1] signage_text 消费（场景参考图 label 泄漏修复）**:
- `scene_reference_manager.py` 4 处改动:
  1. `_analyze_anchor_needs_from_structured()`: interior + exterior needs dict 新增 `signage_text`
  2. `_generate_single_anchor()`: location_info 新增 `signage_text` 传递
  3. `_detect_signage_name()`: 新增 `signage_text` 参数，优先使用 → fallback 清洗 display_name（去 `·`）
  4. `_build_anchor_prompt()`: 两处调用传入 `signage_text`

**T-I [P2] Prompt Pre-Check 机制 (v1 log-only)**:
- `pipeline_orchestrator.py` 新增 `_pre_check_prompt()` 方法 + `import re` + 调用点
- P1 角色数量一致性 / P2 画外物理接触 / P3 预留 / P4 speaker 数据一致性
- v1 仅日志，不阻断不修改 prompt

**验证**: Python import 2/2 ✅ + T-C-Backend 5/5 ✅ + T-I 5/5 ✅

---

### Phase 1 T-B+T-A+T-K+T-D 完成 ✅ (17:00)

**T-B [P0] MAX_SHOT_RETRIES 2→1**:
- `pipeline_orchestrator.py:343`: 常量 `2` → `1`

**T-A [P0] off_screen 文字双重渲染修复**:
- `image_generator.py` `build_native_text_prompt()`: 新增 `characters` + `characters_in_scene` 参数
- 新增 `_is_speaker_off_screen()` 内部函数
- dialogue + off_screen: 仅为不可见 speaker 生成 voiceover，可见 speaker 跳过（由 embed 处理气泡）
- compound types 同步修复
- 调用处传入新参数
- `characters_in_scene=None` → 安全降级全部渲染

**T-K [P1] ShotValidator 人群角色计数容差（方案 α）**:
- `shot_validator.py` `VALIDATION_PROMPT_BASE`: 优化 Haiku 计数指令
- 区分 named/featured subjects vs unnamed bystanders/crowd
- 零 Python 逻辑改动

**T-D [P2] Prompt Quality Report 关键词扩展**:
- `pipeline_orchestrator.py:584-589`: 8 关键词 → ~90 关键词（复用 storyboard_director.py 列表）

**验证**: Python import 3/3 ✅ + T-A 逻辑测试 5/5 ✅

---

## 2026-03-12

### Phase 1b T29+T32 完成 ✅ (21:15)

**T29 [P1] T5 降级逻辑修复 (P-R1)**:
- `storyboard_director.py` L1358-1365: 移除 dialogue→thought 降级，改为保留 dialogue + 标记 `off_screen_speaker: true`
- `image_generator.py` `build_native_text_prompt()`: off_screen dialogue → voiceover 半透明底条；compound types dialogue 子项同理
- `text_overlay_service.py` `process_shot()`: 备用通道 off_screen → 旁白条（非气泡）
- 正常 speaker 可见时的 dialogue 气泡渲染完全不受影响

**T32 [P2] family_relationships → Stage 3 (P-R9)**:
- `pipeline_orchestrator.py` L155: Stage 3 调用传入 `outline["family_relationships"]`
- `screenplay_writer.py` `write()`: 新增 `family_relationships: list = None` 参数
- `_build_single_scene_prompt()`: 注入 `## CHARACTER RELATIONSHIPS` prompt 块（格式参考 T24 Stage 4）
- 缺失时不注入、不报错

**验证**: Python import 5/5 ✅ + T29 逻辑测试 4/4 ✅ + T32 逻辑测试 2/2 ✅

### OB-T29 备用通道复合类型修复 ✅ (21:40)

- `text_overlay_service.py` L669: 复合类型 `sub_type == "dialogue"` 分支新增 `off_screen_speaker` 检查
- off_screen → `add_monologue()` 渲染旁白条（与纵向堆叠偏移同步）；否则保持原有气泡逻辑
- Python import ✅

---

### Phase 1a T30+T31 完成 ✅ (20:00)

**T30 [P1] ShotValidator 日志+依赖修复**:
- `shot_validator.py`: init ✅/❌ 日志 + validate 每次调用入口+出口日志 + 异常标注 fail-open
- `pipeline_orchestrator.py`: 调用前后各加 `[ShotValidator]` 日志行

**T31 [P2] 场景参考图注入故事特定名称**:
- `scene_reference_manager.py`: 新增 `_detect_signage_name()` (中文10+英文24关键词)
- exterior: 匹配时注入 `REQUIRED TEXT ON SIGNAGE: "{name}"`
- interior: 匹配时注入墙面匾额指令
- 无招牌场景不注入

**验证**: Python import 3/3 ✅

---

### T23+T24+T28 Phase 1 全部完成 ✅

**T23 [P1] 参考图模型统一使用 NB2**:
- `image_generator.py` L560: 模型选择从条件判断改为始终 NB2
- `FAST_MODEL` 常量保留但不再被引用

**T24 [P1] Pipeline 传递 outline.characters_overview 到 Stage 4**:
- `pipeline_orchestrator.py`: Stage 4 调用新增 characters_overview 参数
- `storyboard_director.py`: `direct()` → `_generate_scene_shots()` → `_build_scene_prompt()` 三层传递
- `_build_scene_prompt()` 格式化为 CHARACTER RELATIONSHIPS 数据块，注入 prompt

**T28 [P2] ShotValidator 新增道具存在性检测**:
- `shot_validator.py`: VALIDATION_PROMPT 拆分动态组装 + validate_shot 新增 key_props 参数
- 判定: >50% 关键道具缺失 → invalid，返回 missing_props 列表
- `pipeline_orchestrator.py`: 从 shot.get("key_props") 提取传入 validate_shot

**验证**: Python import 3/3 ✅

---

## 2026-03-11

### T17+T20+T21+T22 Phase 1 全部完成 ✅

**T17 [P1] Shot 后置 Haiku 验证 + Auto-Retry**:
- 新建 `app/services/shot_validator.py`: Haiku 4.5 视觉验证（角色数量 ±1 容差 + 气泡重复检测）
- `pipeline_orchestrator.py`: import + 初始化 + shot 循环内验证+retry（最多 2 次，不阻塞）

**T20 [P2] Close-up 参考图选择优化**:
- `reference_image_manager.py:get_smart_references_for_scene()`: medium_shot + ≤2 角色使用 portrait

**T21 [P3] 场景参考图角色数量传入**:
- `scene_reference_manager.py`: `_build_anchor_prompt()` / `_generate_single_anchor()` / `generate_anchor_images()` 新增 num_characters 参数链
- `pipeline_orchestrator.py`: 从 screenplay 计算 location_character_counts 传入
- Interior prompt 注入 "space arranged for N people"

**T22 [P3] with_text_images 冗余跳过 + refs/ 清理**:
- `pipeline_orchestrator.py`: 删除 refs_dir + with_text_dir 条件创建 + use_native_text=True 时 with_text_path 指向 raw

**验证**: Python import 4/4 ✅

---

## 2026-03-10

### PRO_MODEL → NB2_MODEL 命名清理 ✅ (14:15)

**来源**: PM 全局 Double-Check [P3] 派发

**修改**:
- `image_generator.py`: 类常量 `PRO_MODEL` → `NB2_MODEL` + 7 处引用 + 误导性注释/docstring 清理
- `tests/test_nb2_switch.py`: 4 处 `ig.PRO_MODEL` → `ig.NB2_MODEL`
- 不改功能逻辑，`use_pro_model` 参数名保留

**验证**: Python import ✅ + PRO_MODEL 零残留 ✅

### Step 8.5: T13-INT + T12-UNIFY 完成 ✅ (13:48)

**来源**: PM Step 8 Code Review → 2 项微型修复
**优先级**: P0 (阻塞) + P3 (代码质量)

| # | 任务 | 文件 | 修改内容 |
|---|------|------|---------|
| T13-INT | COMIC_MODE_NARRATIVE_RULES 集成 | `storyboard_director.py` | import + 两处 prompt 注入 |
| T12-UNIFY | skip 分支合并 | `pipeline_orchestrator.py` | `if use_native_text:` 单一分支 |

**验证**: Python import 2/2 ✅

---

### Step 7 Phase 1: T11+T12+T16 全部完成 ✅ (13:21)

**来源**: TASK-F1-F5-FIX Step 7 → PM 派发 (R3 修复)
**优先级**: P0-P3

**修改文件**: 4 个文件，3 项任务

| # | 任务 | P | 文件 | 修改内容 |
|---|------|---|------|---------|
| T11 | 移除参考图 PIL 标签 | P0 | `scene_reference_manager.py` + `reference_image_manager.py` | `get_references_for_location()` 移除 `_label_scene_image()` 调用；`get_smart_references_for_scene()` 移除 `_label_reference_image()` 调用 |
| T12 | TextOverlay native_text 模式修复 | P0 | `pipeline_orchestrator.py` | `use_native_text=True` 时全部跳过 TextOverlay（DEC-012），替换原 T8 compound split 逻辑 |
| T16 | OB-6 降级分支补充 | P3 | `storyboard_director.py` | elif 加 `"narration_with_dialogue"` |

**验证**: Python import 4/4 ✅

---

## 2026-03-09

### Step 3: T5+T6+T7+T8+T9 全部完成 ✅ (16:36)

**来源**: TASK-F1-F5-FIX Step 3 → PM 派发
**优先级**: P1-P3

**修改文件**: 3 个文件，5 项任务

| # | 任务 | 优先级 | 文件 | 修改内容 |
|---|------|--------|------|---------|
| T5 | speaker-visibility 验证 | P1 | `storyboard_director.py` | `_validate_storyboard()` 新增 characters 参数 + speaker-visibility 校验（中文名→char_id 映射，不匹配降级） |
| T6 | dialogue speaker 降级 | P1 | `image_generator.py` | `build_dialogue_scene_embed()` 新增 characters_in_scene 参数 + 不可见 speaker 跳过 + 调用方传参 |
| T7 | text_type 分布检查 | P2 | `storyboard_director.py` | 新增 `_rebalance_text_types()` 方法，narration>15%/thought<10% 警告 |
| T8 | compound type 拆分渲染 | P2 | `pipeline_orchestrator.py` | compound type dialogue 子项 NB2 渲染、非 dialogue 子项 TextOverlay 渲染 |
| T9 | use_native_text 参数同步 | P3 | `pipeline_orchestrator.py` | `self.use_native_text = True` 统一配置源 |

**验证**: Python import 3/3 ✅

---

### T4 [P0] pipeline TextOverlay 条件判断 ✅ (15:55)

**来源**: TASK-F1-F5-FIX Step 1 → PM 派发 (F2 修复)
**优先级**: P0

**修改文件**: `app/services/pipeline_orchestrator.py` (L335-357, 1 处修改)

**根因**: `use_native_text=True` 时 NB2 通过 `build_dialogue_scene_embed()` 原生渲染 dialogue 气泡，但 pipeline 无条件对所有 `text_type != "none"` 执行 `text_overlay_service.process_shot()`，导致 dialogue 被双重/三重渲染。

**修改内容**:

| # | 修改点 | 修改前 | 修改后 |
|---|--------|--------|--------|
| 1 | TextOverlay 条件判断 | 无条件对 text_type != "none" 执行 | `use_native_text=True` 且 `text_type == "dialogue"` 时跳过，复制 raw image |

```python
# 新增逻辑
text_type = text_overlay_data.get("text_type", "none")
use_native_text = True
if text_type != "none":
    if use_native_text and text_type == "dialogue":
        # 直接复制 raw image 作为 with_text 版本
        result["pil_image"].copy().save(with_text_path)
    else:
        text_overlay_service.process_shot(...)
```

**验证**: Python import ✅

---

### TASK-BACKUP-MODEL-FLASH — Stage 1-3 备用模型统一 Flash ✅ (11:07)

**来源**: Founder 决策（成本和性价比）→ PM 派发
**优先级**: P1

**修改文件**: 3 个文件，每文件 4 处修改

| # | 文件 | 修改内容 |
|---|------|---------|
| 1 | `story_outline_generator.py` | `gemini-3-pro-preview` → `gemini-3-flash-preview` + docstring + 注释×2 |
| 2 | `character_designer.py` | `gemini-3-pro-preview` → `gemini-3-flash-preview` + docstring + 注释×2 |
| 3 | `screenplay_writer.py` | `gemini-3-pro-preview` → `gemini-3-flash-preview` + docstring + 注释×2 |

**验证**: Python import + 模型配置确认 (3/3 = gemini-3-flash-preview) ✅

---

### Issue #2 — DEC-012 Stage 4 模型配置修复 ✅ (10:21)

**来源**: E2E 回归测试 PM 深度分析 Issue #2 (Extra #1) → Founder 批准修复
**优先级**: P1

**修改文件**: `app/services/storyboard_director.py` (4 处修改)

| # | 修改点 | 修改前 | 修改后 |
|---|--------|--------|--------|
| 1 | 主模型 | `gemini-3-flash-preview` | `claude-sonnet-4-6` |
| 2 | 备用模型 | `claude-haiku-4-5-20251001` | `gemini-3-flash-preview` |
| 3 | 调用顺序 | Gemini 优先 → Claude fallback | Claude 优先 → Gemini fallback |
| 4 | style_preset 默认值 (×2) | `"realistic"` | `"anime"` |

**根因**: AI-ML 后续修改此文件（TASK-PROMPT-BUBBLE 系列）时覆盖了 TASK-MODEL-UPGRADE + TASK-STYLE-DEFAULT-FIX 的变更。

**验证**: Python import + 模型配置确认 (claude-sonnet-4-6 / gemini-3-flash-preview) ✅

---

## 2026-03-06

### TASK-BUBBLE-SPEAKER-FORMAT-DEPLOY ✅ (14:56)

**来源**: PM 派发 (Founder 决策 speaker_format='english', R2 A/B/C 对比后确认)
**优先级**: P0

**任务**: 修改 `image_generator.py` 生产代码，为 `build_dialogue_scene_embed()` 传入 `characters`, `speaker_format`, `text_language` 三个参数

**修改文件**: `app/services/image_generator.py` (第 845-853 行)

```python
# BEFORE:
dialogue_embed = build_dialogue_scene_embed(text_overlay)

# AFTER:
dialogue_embed = build_dialogue_scene_embed(
    text_overlay,
    characters=characters.get("characters", []),
    speaker_format='english',
    text_language='zh-CN'
)
```

**关键决策**:
- 类型处理: `characters.get("characters", [])` 从 dict wrapper 提取 list，匹配函数签名 `characters: list`
- `speaker_format='english'`: Founder 决策，B 组 (english) 语言一致性 + 多语言扩展性最优
- `text_language='zh-CN'`: 强制简体中文，完全修复 R1 繁体渲染问题
- 死代码: 检查后未发现需清理的死代码路径

**验证**: Python 语法/import 检查通过 ✅

---

## 2026-03-05

### TASK-BUBBLE-SIMPLIFY 测试完成 ✅ (16:14)

**来源**: PM 派发 TASK-BUBBLE-SIMPLIFY (对话气泡简化方案验证)
**优先级**: P1

- **脚本**: `tests/test_bubble_simplify.py`
- **输出**: `test_output/manualtest/bubble_simplify/` (group_A/B/C.png + prompt.txt)
- **耗时**: A=33.1s, B=41.3s, C=99.3s

**关键结论**: 3 组均未渲染对话气泡。移除 TEXT OVERLAY REQUIREMENT 后 NB2 将对话行理解为场景情绪上下文，不触发气泡渲染。对话嵌入有助于场景情绪表现，角色一致性 3 组均良好。

等待 PM/Founder 评审决定下一步方案。

---

### TASK-SHOT10-REGEN + Bug #6 修复 ✅ (15:17)

**来源**: PM 派发 TASK-SHOT10-REGEN (补生成因 Bug #5 crash 缺失的 shot_10)
**优先级**: P1

#### TASK-SHOT10-REGEN: 补生成 shot_10

- **脚本**: `tests/test_shot10_regen.py`
- **输出**: `test_output/manualtest/bugfix_regression/20260304_162910/shots/shot_10.png` (848x1264, NB2)
- **验证**: Bug #5 dict 格式 chinese_text 正确处理 ✅, 角色一致性 ✅, 18/18 shots 全部到位 ✅

**验证过程**:
1. 首次生成角色一致性差 → 创建诊断脚本 `tests/test_shot10_diagnosis.py` 对 shot_10 vs shot_11 做 6 维度全量对比
2. 诊断结论: prompt/参考图/API 参数完全一致，确认为 NB2 模型随机性 + wide_shot+high_angle 增加难度
3. 重跑后角色一致性 OK，但发现 Bug #6

#### Bug #6 (P2): 多人对话气泡缺少说话者指向

**文件**: `image_generator.py`

| 修改点 | 修改前 | 修改后 |
|--------|--------|--------|
| 新增 `_extract_speaker_name()` | (不存在) | 从 "林晨宇：「...」" 提取说话者名 |
| dialogue handler 气泡位置 | `"upper left" if i == 0 else "upper right"` (硬编码) | `f"near {speaker}"` (跟随说话者) |
| dialogue handler 尾部指向 | `"triangular tail pointing to speaker"` (无名) | `f"triangular tail pointing toward {speaker}"` |
| compound handler 气泡位置 | 同上硬编码 | 同上跟随说话者 |
| compound handler 尾部指向 | 同上无名 | 同上具名 |

**根因**: `_strip_speaker_for_native()` 剥离说话者前缀后丢弃，prompt 中气泡位置硬编码且无说话者身份信息。多人对话时模型无法确定哪个气泡属于谁。

**影响范围**: 18 shots 中 5 个含多人对话 (Shot 2/4/5/10/11)，其中 2/4/5 碰巧正确（单人+内心独白），10/11 错误（3 人同时对话）。

**验证**: shot_10 重跑后林晨宇台词气泡正确出现在林晨宇旁 ✅

---

## 2026-03-04

### TASK-SHOT-QUALITY-BUGFIX Backend 部分 ✅ (16:09 + 18:07)

**来源**: PM Step 7 独立复核发现 4 个 Bug + 回归验证发现 Bug #5，Backend 负责 #1/#2/#4/#5
**优先级**: P1-P3

**4 项修复，3 个文件：**

| # | Bug | 级别 | 文件 | 修复方式 |
|---|-----|------|------|----------|
| 1 | 场景标签中文→□ 泄漏 | **P1** | `scene_reference_manager.py` | 标签改用英文 `location_id`；CJK 字体 (PingFang/STHeiti/NotoSansCJK) 加入字体 fallback 列表 |
| 2 | Prompt "70-80% opacity" 文字泄漏 | **P2** | `image_generator.py` | `build_native_text_prompt()` 移除 4 处 opacity 行 + 1 处 px 描述 |
| 4 | Validator `camera_angle` 字段名错误 | **P3** | `storyboard_service.py` | `_get_camera_angle()` 从 `camera.camera_angle` 改为 `camera.angle` |
| 5 | dialogue handler dict crash | **P2** | `image_generator.py` | L81-82 添加 `isinstance(txt, dict)` 类型检查，与 compound handlers 一致 |

全部语法/import 检查通过 ✅

---

### Step 5c: TASK-SHOT-QUALITY-UPGRADE Backend 部分 ✅ (10:50)

**来源**: PM 正式启动 Step 5c → SQ-8 + SQ-2 + SQ-1 + SQ-6
**优先级**: P0

**4 项改进，6 个文件修改：**

| SQ | 改进项 | 涉及文件 |
|----|--------|----------|
| SQ-8 | 移除 previous_shot_image (DEC-014) | pipeline_orchestrator.py, image_generator.py, storyboard_prompts.py |
| SQ-2 | 智能参考图选择（每角色1张） | reference_image_manager.py, pipeline_orchestrator.py, image_generator.py, storyboard_prompts.py |
| SQ-1 | PIL文字标注参考图 | reference_image_manager.py, scene_reference_manager.py, storyboard_prompts.py |
| SQ-6 | Shot Transition Validator | storyboard_service.py |

**关键变更**:
- SQ-8: previous_shot_image + previous_shot 从全链路移除 (pipeline → image_gen → prompts)
- SQ-2: 新增 `get_smart_references_for_scene(char_ids, shot_type)`，close_up→portrait/其余→fullbody
- SQ-1: `_label_reference_image()` + `_label_scene_image()` PIL叠加，标签声明式prompt
- SQ-6: `validate_shot_transitions()` 5项规则检查

全部语法检查通过 ✅

---

## 2026-02-28

### TASK-ROBUSTNESS-FIX (P1) ✅ — 关键字回退逻辑修复 (11:31)

**来源**: PM 核验 TASK-NATIVE-TEXT-ROBUSTNESS 发现不一致 → PM 派发 (2026-02-28 11:15)
**优先级**: P1

**修复文件**: `app/services/image_generator.py` `build_native_text_prompt()` 混合类型回退分支

对齐 `text_overlay_service.py` `_classify_sub_type()`:

| # | 修复点 | 修复前 | 修复后 |
|---|--------|--------|--------|
| 1 | thought 关键字 | `"内心" in txt`（过于宽泛，可能误触） | `"内心：" in txt or "内心:" in txt`（含冒号，精准匹配） |
| 2 | narration 检测 | `"旁白" in txt`（过于宽泛） | `txt.startswith("旁白：")`（仅匹配前缀） |
| 3 | dialogue 检测 | 缺少 `"：\""` 中文冒号+双引号 | 补充 `or "：\"" in txt` |

语法 ✅

---

### TASK-NATIVE-TEXT-ROBUSTNESS (P2) ✅ — 混合类型文本分类逻辑优化 (10:37)

**来源**: PM 派发 (2026-02-28 10:25)
**优先级**: P2

**问题**: `build_native_text_prompt()` 和 `process_shot()` 中混合类型（dialogue_with_thought 等）判断每条文本的子类型依赖中文关键字（"内心"/"旁白"/"：「"），Stage 4 输出格式变化会导致分类失败。

**优化**: 让 Stage 4 输出结构化子类型元数据，Stage 5 和 TextOverlay 优先使用元数据分类。

**修改文件**（3 个）：

1. **`storyboard_director.py`** — Stage 4 prompt 更新:
   - TEXT OVERLAY RULES 中混合类型 `chinese_text` 格式从字符串数组改为对象数组
   - 新格式: `[{"type": "dialogue", "text": "苏晨：「你好」"}, {"type": "thought", "text": "苏晨内心：「...」"}]`
   - JSON 输出模板 `chinese_text` 说明同步更新

2. **`image_generator.py`** — `build_native_text_prompt()` 混合类型处理:
   - 优先检查 `isinstance(item, dict) and "type" in item` → 使用 `item["type"]`
   - 回退: LLM 输出纯字符串时，从文本内容推断子类型（保持鲁棒性）

3. **`text_overlay_service.py`** — `process_shot()` 混合类型处理:
   - 新增 `_classify_sub_type()` 内部函数，统一分类逻辑
   - 支持结构化元数据 + 旧格式回退
   - `total_dialogues` 计算改用分类结果（`sub_type == "dialogue"`）

语法 3/3 通过 ✅

---

## 2026-02-27

### TASK-NB2-NATIVE-TEXT (P0) ✅ — NB2 原生文字渲染切换 (17:50)

**来源**: Phase 4 PM 派发 (Founder 决策方案 B)
**优先级**: P0

**任务**: 修改 Shot 生成流程，让 NB2 原生渲染中文文字，不再依赖 TextOverlay 后处理

`app/services/image_generator.py`:

1. **新增模块级函数**:
   - `build_native_text_prompt(text_overlay)` — 根据 text_overlay 数据构建 TEXT OVERLAY REQUIREMENT 指令块
   - `_strip_speaker_for_native(text)` — 剥离说话者前缀（用于 prompt 构建）
   - 支持 7 种 text_type: thought, narration, dialogue, dialogue_with_thought, narration_with_thought, narration_with_dialogue, dialogue_with_narration

2. **`generate_shot_image_phase2()` 新增参数 `use_native_text: bool = True`**:
   - `True`（默认）: StyleEnforcer + color_mode 之后，将 TEXT OVERLAY REQUIREMENT 附加到 prompt 末尾
   - `False`: 不附加，由 TextOverlay 后处理叠加

3. **`generate_shot_image_phase2_safe()` 同步新增 `use_native_text` 参数**:
   - 透传给首次生成 + 改写重试的两处 `generate_shot_image_phase2()` 调用

**参考实现**: `tests/test_nb2_text_test.py` B组 `build_text_overlay_prompt()` (:87-170)

**验证结果** (5 shots, slam_dunk, `use_native_text=True`):

| Shot | text_type | 时间 | 尺寸 |
|------|-----------|------|------|
| 01 | thought | 51.1s | 848x1264 |
| 06 | narration | 39.4s | 848x1264 |
| 09 | dialogue | 41.9s | 848x1264 |
| 13 | narration_with_thought | 48.0s | 848x1264 |
| 17 | dialogue_with_thought | 44.3s | 848x1264 |

- 成功率: **5/5 (100%)** ✅
- 平均: **45.0s/张**
- TextOverlay 代码完整保留（未删除任何功能）✅

语法 ✅ | 输出: `test_output/manualtest/nb2_native_text_verify/`
测试脚本: `tests/test_nb2_native_text.py`

---

### Phase 3 Backend 四项任务 ✅ (16:09)

**TASK-NB2-SWITCH (P0)**: Shot 生图主力模型 Gemini 3 Pro → Nano Banana 2 (gemini-3.1-flash-image-preview)
- `image_generator.py:58` PRO_MODEL 改 1 行 + 注释更新
- 验证: 5/5 shots 成功, 848x1264, 平均 25.9s/张（Pro ~72s, 提速 ~2.8x）
- 输出: `test_output/manualtest/nb2_switch_verify/`

**TASK-DIALOGUE-SYSTEM Layer 1 (P0)**: Stage 3 ScreenplayWriter 对话系统
- `screenplay_writer.py` `_build_single_scene_prompt()` 新增对话强制约束块
- JSON 输出模板新增 `dialogue_beats` 字段（speaker + line + emotion）
- 每 scene 至少 2 组对话交互

**TASK-TEAM-UNIFORM (P1)**: Stage 2 CharacterDesigner 团队着装一致性
- `character_designer.py` 新增规则 5（球队/学校/军队/公司统一着装）
- 原规则 5 "服装状态" 改编号为 6

**TASK-SPEAKER-PREFIX (P2)**: TextOverlay 智能 Speaker 前缀处理
- `text_overlay_service.py` 新增 3 个函数: `extract_speaker_name`, `smart_strip_speaker_prefix`, `_find_char_id_by_name`
- `process_shot()` 新增 `characters_in_scene` + `characters_data` 可选参数
- 画面可见角色→剥离前缀，画外音→保留前缀，完全向后兼容

语法 4/4 通过 ✅

---

## 2026-02-26

### TASK-STYLE-DEFAULT-FIX + TASK-MODEL-UPGRADE-RETEST ✅

**完成时间**: 2026-02-26 17:33
**来源**: Founder 反馈 → PM 派发 (2026-02-26 16:43)
**优先级**: P0

#### TASK-STYLE-DEFAULT-FIX: 默认风格修复

4 个文件 8 处 `style_preset` 默认值 `"realistic"` → `"anime"`:

| 文件 | 处数 | 行号 |
|------|------|------|
| pipeline_orchestrator.py | 3 | :42, :65, :615 |
| storyboard_director.py | 2 | :98, :892 |
| image_generator.py | 2 | :494, :760 |
| shot_prompt_generator.py | 1 | :389 |

语法 4/4 通过 ✅

#### TASK-MODEL-UPGRADE-RETEST: slam_dunk 风格重跑验证

**测试脚本**: `tests/test_model_upgrade.py` (style_preset="slam_dunk")

| Stage | provider | 结果 |
|-------|----------|------|
| 1 | claude ✅ | "最后一投", 2角色, 6情节, 4场景 |
| 2 | claude ✅ | 陈晨+林峰, physical+clothing 完整 |
| 3 | claude ✅ | 6 scenes, 20 beats, 1302字 |
| 4 | claude ✅ | 20 shots, text_overlay 完整 |

**slam_dunk 风格验证**: 20/20 (100%) image_prompt 包含 slam dunk 相关关键词 ✅

**text_type 分布对比**:
| text_type | realistic | slam_dunk | DEC-012 目标 |
|-----------|-----------|-----------|-------------|
| narration | 2 (10.5%) | 1 (5%) | ≤30% ✅ |
| thought | 9 (47.4%) | 9 (45%) | 20-25% |
| dialogue | 1 (5.3%) | 2 (10%) | 40-50% |
| dialogue_with_thought | 1 (5.3%) | 3 (15%) | - |
| none | 5 (26.3%) | 4 (20%) | 5-10% |
| narration_with_thought | 1 (5.3%) | 1 (5%) | - |

总耗时 553.9秒 | 输出: `test_output/manualtest/model_upgrade_retest_slamdunk/`

---

### TASK-MODEL-UPGRADE: 模型全面升级 ✅

**完成时间**: 2026-02-26 16:18
**来源**: DEC-012 决策 4 → PM 派发 (2026-02-25 18:09)
**优先级**: P0

**任务**: 7 个文本生成服务文件从 Gemini Flash/Haiku → Claude Sonnet 4.6 (主) + Gemini 3 Pro (备)

#### Step 1: 模型配置切换 (7文件) ✅

| # | 文件 | 原主力 | 新主力 | 新备用 |
|---|------|--------|--------|--------|
| 1 | story_outline_generator.py | Gemini Flash | Sonnet 4.6 | Gemini 3 Pro |
| 2 | character_designer.py | Gemini Flash | Sonnet 4.6 | Gemini 3 Pro |
| 3 | screenplay_writer.py | Gemini Flash | Sonnet 4.6 | Gemini 3 Pro |
| 4 | storyboard_director.py | Gemini Flash | Sonnet 4.6 | Gemini 3 Pro |
| 5 | alignment_service.py | Gemini Flash | Sonnet 4.6 | Gemini 3 Pro |
| 6 | prompt_rewriter.py | Haiku 4.5 | Sonnet 4.6 | Gemini 3 Pro (新增) |
| 7 | character_position_detection.py | Haiku 4.5 | Sonnet 4.6 | *(示例代码)* |

**具体修改内容**:
- Files 1-5: 交换 __init__ 中 Claude/Gemini 客户端初始化顺序 + 方法内优先级
- File 5 (alignment_service): 额外修改 `_visual_alignment()` 支持 Claude 多模态图片输入（之前 Claude fallback 不传图）
- File 6 (prompt_rewriter): 重命名 `HAIKU_MODEL` → `SONNET_MODEL`，新增 Gemini 3 Pro 客户端和 fallback
- File 7 (character_position_detection): `EXAMPLE_USAGE` 字符串内模型 ID 更新

**模型 ID 对照**:
| 用途 | 旧 ID | 新 ID |
|------|-------|-------|
| 文本主力 | `gemini-3-flash-preview` / `claude-haiku-4-5-20251001` | `claude-sonnet-4-6` |
| 文本备用 | `claude-haiku-4-5-20251001` / 无 | `gemini-3-pro-preview` |

#### Step 2: 验证 Gemini 3 Pro 文本模型 ID ✅

`client.models.list()` 确认 `gemini-3-pro-preview` 存在于 API 模型列表。

#### Step 3: Stage 1-4 基础测试 ✅

**测试脚本**: `tests/test_model_upgrade.py`

| Stage | 服务 | provider | 结果 |
|-------|------|----------|------|
| 1 | StoryOutlineGenerator | claude ✅ | "最后三秒", 2角色, 6情节点, 3场景 |
| 2 | CharacterDesigner | claude ✅ | 2角色 (林晟+教练老陈), physical+clothing 完整 |
| 3 | ScreenplayWriter | claude ✅ | 6 scenes, 19 beats, 1247字旁白 |
| 4 | StoryboardDirector | claude ✅ | 19 shots, text_overlay 全覆盖 |

**text_overlay 分布对比**:
| text_type | Sonnet 4.6 (本次) | Gemini Flash (上次 E2E) | 变化 |
|-----------|-------------------|------------------------|------|
| narration | 2 (10.5%) | 25 (86%) | 大幅下降 |
| thought | 9 (47.4%) | 1 (3.4%) | 大幅增加 |
| none | 5 (26.3%) | 1 (3.4%) | 增加 |
| dialogue | 1 (5.3%) | 1 (3.4%) | 持平 |
| dialogue_with_thought | 1 (5.3%) | 0 | 新增 |
| narration_with_thought | 1 (5.3%) | 1 (3.4%) | 持平 |

**总耗时**: 597秒 (~10分钟，仅 Stage 1-4，不含图像生成)
**语法检查**: 7/7 通过 ✅
**输出目录**: `test_output/manualtest/model_upgrade/`

#### 未改动的文件
- `image_generator.py` — 生图模型不变（Gemini Pro Image + Flash Image）
- `story_generator.py` — Phase 1 遗留文件，不在 DEC-012 任务范围

---

## 2026-02-24

### TASK-E2E-VALIDATE Step 1a+1b: 端到端流水线验证 ✅

**完成时间**: 2026-02-24 17:38
**验收状态**: ✅ 代码完成 + 实际运行通过（29/29 shots, 28/29 TextOverlay）

**任务背景**:
- TASK-E2E-VALIDATE（Phase 1 端到端流水线验证 + TextOverlay 集成）
- PM 指定混合方案：先跑通基础流水线(1a)，再集成 TextOverlay(1b)

**完成内容**:

#### Step 1b-1: Stage 4 Prompt 修改 ✅
- [x] `storyboard_director.py:_build_scene_prompt()` 新增 TEXT OVERLAY RULES 指令段
- [x] 教 LLM 输出 `text_overlay` 字段（text_type + chinese_text + speaker_position）
- [x] 支持 8 种 text_type，chinese_text 可为字符串或数组

#### Step 1b-2: Pipeline TextOverlay 集成 ✅
- [x] `pipeline_orchestrator.py` 导入 `TextOverlayService`
- [x] 创建 `with_text_images/` 输出目录
- [x] 图片保存后调用 `text_overlay_service.process_shot()` 生成带文字版
- [x] 错误隔离：TextOverlay 失败不影响基础流水线

#### Step 1a: E2E 测试脚本 ✅
- [x] 新建 `tests/test_e2e_validate.py`
- [x] 调用 `Phase2PipelineOrchestrator` 全参数运行

#### 实际运行结果 ✅ (2026-02-24 17:08→17:38)
- [x] 29/29 shots 全部生成成功
- [x] 28/29 TextOverlay 成功（1张 text_type=none 正确跳过）
- [x] 4种 text_overlay 类型（narration/thought/dialogue/narration_with_thought）均正确渲染
- [x] Speaker 前缀剥离正确
- [x] 宽高比 832x1248 = 2:3 ✅
- [x] 总耗时 1775秒 (~29.6分钟)

**运行统计**:
| 指标 | 结果 |
|------|------|
| 故事 | 雨夜的庇护 / 2角色 / 6场 / 29 shots |
| 原图 | 29/29 ✅ |
| 带文字版 | 28/29 ✅ (shot_13 text_type=none) |
| 角色参考图 | 4/4 (portrait+fullbody x 2) |
| 场景参考图 | 2/2 |
| Shot模型 | gemini-3-pro-image-preview (Pro) |
| 参考图模型 | gemini-2.5-flash-image (Flash) |

**text_overlay 类型分布**:
| text_type | 数量 | 渲染验证 |
|-----------|------|----------|
| narration | 25 | ✅ 底部半透明黑底白字 |
| thought | 1 | ✅ "林晓内心：「...」" → 正确剥离前缀 |
| dialogue | 1 | ✅ "林晓：「谢谢。」" → 对话气泡 |
| narration_with_thought | 1 | ✅ 混合分层：旁白(下)+内心独白(中) |
| none | 1 | ✅ 正确跳过 |

**关键产出**:
| 文件 | 说明 |
|------|------|
| `app/services/storyboard_director.py` | 新增 text_overlay prompt 规则 + 输出字段 |
| `app/services/pipeline_orchestrator.py` | TextOverlay 集成（import + dir + process） |
| `tests/test_e2e_validate.py` | E2E 验证测试脚本 |
| `test_output/manualtest/e2e_validate/20260224_170840/` | 完整运行输出 |

**技术设计决策**:
- `text_overlay` 字段格式直接兼容 `process_shot()` 期望的 dict 结构，无需额外转换
- chinese_text 使用前缀标记法（"旁白：「...」" / "角色名：「...」" / "角色名内心：「...」"），与现有测试数据格式一致
- TextOverlay 处理在 try/except 中，失败不阻塞主流水线

---

### TASK-SCENE-REF-ASPECT: 场景参考图宽高比统一为 2:3 ✅

**完成时间**: 2026-02-24 11:37
**验收状态**: 1处修改，语法通过，grep 确认无遗漏

**任务背景**:
- DEC-010 决策：从源头统一参考图宽高比，消除比例不匹配
- TASK-ASPECT-2x3 遗漏了 `scene_reference_manager.py`

**完成内容**:
- [x] `scene_reference_manager.py:431` — `aspect_ratio="16:9"` → `aspect_ratio="2:3"`
- [x] Python 语法验证通过
- [x] grep 排查 `app/services/` 无遗漏

---

## 2026-02-14

### TASK-ASPECT-2x3: 宽高比统一改为 2:3 ✅

**完成时间**: 2026-02-14 10:56
**验收状态**: 9个文件26处修改，语法验证9/9通过

**任务背景**:
- Founder 指令: 条漫为主，抖音首发，图片统一 2:3
- PM 排查后发布完整清单（9个文件）

**完成内容**:
- [x] 9个生产代码文件的默认宽高比统一为 `"2:3"`
- [x] `get_aspect_ratio_for_scene()` 智能推断也统一为 `"2:3"`（Backend 决策）
- [x] Python 语法验证 9/9 通过
- [x] grep 排查确认无遗漏

**修改文件**:
| 文件 | 修改数 | 原值 |
|------|--------|------|
| `reference_image_manager.py` | 2 | `"1:1"` |
| `image_generator.py` | 6 | `"16:9"` / `"3:4"` |
| `storyboard_director.py` | 4 | `"16:9"` |
| `storyboard_prompts.py` | 5 | `"16:9"` / `"9:16"` / `"21:9"` / `"1:1"` |
| `storyboard_service.py` | 1 | `"16:9"` |
| `consistent_image_generator.py` | 2 | `"1:1"` / `"16:9"` |
| `pipeline_orchestrator.py` | 1 | `"16:9"` |
| `chapters.py` | 4 | `"16:9"` |
| `scene_image.py` | 1 | `"16:9"` |

---

## 2026-02-13

### TASK-REF-PREPROCESS Step 3: 对比测试 ✅

**完成时间**: 2026-02-13 16:24
**验收状态**: 6/6 API调用成功，图片已保存，等待 Tester Step 4

**任务背景**:
- PM 核验 Step 1+2 通过后批准执行 Step 3
- AI-ML 指定 shot_34/36/22 作为对比测试（覆盖留白+留黑、单角色+双角色）

**完成内容**:
- [x] 创建对比测试脚本 `tests/test_ref_preprocess_comparison.py`
- [x] Phase 1: 禁用预处理，生成3个shot（monkey-patch noop）
- [x] Phase 2: 启用预处理，生成相同3个shot
- [x] 6次API调用全部成功

**关键产出**:
| 文件 | 说明 |
|------|------|
| `tests/test_ref_preprocess_comparison.py` | 对比测试脚本 |
| `test_output/ref_preprocess_test/without/shot_{22,34,36}.png` | 无预处理结果 |
| `test_output/ref_preprocess_test/with/shot_{22,34,36}.png` | 有预处理结果 |
| `test_output/ref_preprocess_test/comparison_report.json` | 测试报告 |

**预处理日志确认**:
```
Phase 2 中每张参考图都正确裁剪:
Jerry fullbody: 864x1184 → 666x1184 (裁剪宽度22.9%)
CC fullbody: 896x1152 → 648x1152 (裁剪宽度27.7%)
Phase 1 中无裁剪日志（noop正确生效）
```

---

### TASK-REF-PREPROCESS Step 2: 参考图预处理代码 ✅

**完成时间**: 2026-02-13 16:07
**验收状态**: 代码验证通过，等待 Step 3 对比测试

**任务背景**:
- DEC-009 批准方案A：在 ImageGenerator.generate_image() 中实现参考图中心裁剪
- 参考图比例(0.73~0.78)与目标9:16(0.5625)差距17-22%，可能加剧边缘留黑/留白问题
- AI-ML 提供了建议代码，Backend 负责实现

**完成内容**:
- [x] 新增 `_preprocess_reference_to_aspect_ratio()` 方法（中心裁剪）
- [x] 在 `generate_image()` 中添加预处理调用
- [x] 在 `generate_shot_image_phase2()` 中添加预处理调用
- [x] 单元验证：裁剪数据与 AI-ML 探索结果一致

**关键产出**:
| 文件 | 说明 |
|------|------|
| `app/services/image_generator.py` | 新增方法 L183-214，修改两处调用 L275、L631 |

**验收标准**:
- 中心裁剪逻辑: ✅
- 只裁不拉伸: ✅
- 原图不受影响: ✅ (crop()返回新Image)
- 日志输出裁剪信息: ✅
- 容差0.01: ✅
- 覆盖所有生成路径: ✅ (generate_image + generate_shot_image_phase2)

**裁剪验证数据**:
```
Jerry fullbody (864x1184) → 666x1184 (裁剪宽度22.9%)
CC fullbody (896x1152) → 648x1152 (裁剪宽度27.7%)
已匹配的图 → 不裁剪
```

---

## 2026-02-03

### TASK-RENAME-KAI-TO-JERRY ✅

**完成时间**: 2026-02-03 21:30
**验收状态**: shot_12验证通过

**任务**: 将"Kai与Cici"故事中的"Kai"全部替换为"Jerry"

| 修改项 | 原 | 新 |
|--------|-----|-----|
| 测试文件 | `test_comic_cc_kai.py` | `test_comic_cc_jerry.py` |
| 参考图目录 | `teststory_CCKai` | `teststory_CCJerry` |
| 参考图文件 | `Kai_*.png` | `Jerry_*.png` |
| 输出目录 | `comic_cc_kai_story_v3` | `comic_cc_jerry_story_v3` |
| 代码内容 | 172处"Kai" | "Jerry" |
| shot_12台词 | "你好呀，Kai" | "你好，Jerry" |

**验证结果**:
- shot_12图片生成成功 ✅
- 输出: `test_output/comic_cc_jerry_story_v3/with_text_images/shot_12.png`

---

### V5修复任务(FIX-B1/B2/B3/B4) ✅

**完成时间**: 2026-02-03 19:00
**验收状态**: ✅ Tester V5验收通过 (4.9/5)

**任务来源**: PM独立综合复核 (V4_PM_COMPREHENSIVE_REVIEW.md)

| 任务ID | 描述 | 优先级 | 修改位置 |
|--------|------|--------|----------|
| **FIX-B1** | 混合类型气泡位置索引修复 | **P0** | Line 497-507 |
| FIX-B2 | 移除「」符号添加逻辑 | P1 | Line 79-83 |
| FIX-B3 | 启用detect_overlay_collision | P1 | Line 175, 367-378, 466 |
| FIX-B4 | bubble_alpha配置化/降低 | P2 | Line 162, 173, 322 |

**关键修复详情**:

#### FIX-B1: 混合类型气泡位置索引修复
```python
# 先统计总对话数量
total_dialogues = sum(1 for t in texts if "：「" in t or ":「" in t or "：\"" in t)
dialogue_index = 0

for txt in texts:
    if "：「" in txt or ":「" in txt or "：\"" in txt:
        x_pct, y_pct = get_bubble_position_for_index(dialogue_index, total_dialogues)
        result = self.add_speech_bubble(result, txt, bubble_x_percent=x_pct, bubble_y_percent=y_pct)
        dialogue_index += 1
```

#### FIX-B3: 碰撞检测
```python
# 在__init__中
self._bubble_bounds: List[Tuple[int, int, int, int]] = []

# 在add_speech_bubble中
new_bounds = (bubble_x, bubble_y, bubble_width, bubble_height)
for attempt in range(max_attempts):
    if not detect_overlay_collision(self._bubble_bounds, new_bounds):
        break
    bubble_y += y_step  # 检测到碰撞，向下移动
self._bubble_bounds.append(new_bounds)

# 在process_shot开始时重置
self._bubble_bounds = []
```

**验证**: Python语法验证通过 ✅

---

### 架构重构(ARCH-1/2/3) + 核心功能修复(CORE-1/2) ✅

**完成时间**: 2026-02-03
**验收状态**: ✅ 已完成（V5修复基于此）

**任务背景**:
- PM发现TextOverlayService在8个测试文件中各自重复定义
- 主服务目录`app/services/`中没有统一实现
- 修复一个故事的bug，其他故事不受益（架构缺陷）
- Speaker前缀剥离不完整，气泡透明度实现错误

**完成内容**:

#### 阶段0: 架构重构 ✅

| 步骤 | 说明 | 状态 |
|------|------|------|
| ARCH-1 | 创建 `app/services/text_overlay_service.py` (537行) | ✅ |
| ARCH-2 | 更新 `__init__.py` 导出 | ✅ |
| ARCH-3 | 迁移7个测试文件 | ✅ |

#### 阶段1: 核心功能修复 ✅

| 任务 | 问题 | 修复方案 | 状态 |
|------|------|---------|------|
| CORE-1 | Speaker前缀未全覆盖 | `strip_speaker_prefix()`在add_monologue和add_speech_bubble中都调用 | ✅ |
| CORE-2 | 气泡透明度实现错误 | 使用`alpha_composite`正确实现半透明 | ✅ |

#### 迁移的7个测试文件

| 文件 | 删除代码行数 | 迁移方式 |
|------|-------------|---------|
| `test_comic_story_c_cyberpunk.py` | ~350行 | 直接导入 |
| `test_comic_full_story_v2.py` | ~430行 | 直接导入 |
| `test_comic_full_story.py` | ~345行 | 直接导入 |
| `test_text_overlay.py` | ~200行 | 适配器模式 |
| `test_text_overlay_v2.py` | ~250行 | 适配器模式 |
| `test_new_story_overlay_v2.py` | ~150行 | 适配器模式 |
| `test_comic_story_b_wuxia_ink.py` | ~350行 | 直接导入 |

**总计**: 删除 ~2075 行重复代码

#### 迁移策略

1. **直接导入**: 测试文件API与主服务API一致，直接替换
   ```python
   from app.services.text_overlay_service import (
       TextOverlayService,
       strip_speaker_prefix,
       get_bubble_position_for_index,
       detect_overlay_collision,
   )
   ```

2. **适配器模式**: 测试文件有独特API，创建适配器函数桥接
   - `apply_overlay()` → 调用 `service.add_monologue()` / `service.add_speech_bubble()`
   - `add_speech_bubble_v2()` → 转换参数后调用 `service.add_speech_bubble()`

#### 关键产出

| 文件 | 说明 |
|------|------|
| `app/services/text_overlay_service.py` | 统一的主服务（ARCH-1创建） |
| `app/services/__init__.py` | 导出新服务（ARCH-2更新） |
| 7个测试文件 | 全部迁移至使用主服务 |

**验证**:
- 所有测试文件保留原有功能
- 现在修复主服务的bug，所有故事类型都受益

---

## 2026-02-02

### HANDOFF-2026-02-02-015: V2+ TextOverlay P1修复 ✅

**完成时间**: 2026-02-02
**验收状态**: 等待 @Tester 执行V3测试验收

**任务背景**:
- PM对V2进行综合分析，发现P1级别问题需要修复
- TASK-3: Shot 42两条旁白完全重叠
- TASK-4: Shot 19有3条对话但只渲染2条

**完成内容**:

#### TASK-3: 文字叠加碰撞检测 ✅
- [x] 修改`add_monologue()`返回`(image, bar_height)`元组
- [x] 添加`y_offset`参数支持垂直偏移
- [x] 在`process_shot()`中跟踪各位置偏移量`position_offsets`
- [x] 混合类型叠加时自动堆叠，避免重叠

**碰撞避免逻辑**:
```python
# 跟踪各位置已占用高度
position_offsets = {"top": 0, "bottom": 0, "center": 0}

# 添加旁白时使用偏移
result, bar_height = self.add_monologue(
    result, text, position="bottom",
    y_offset=position_offsets["bottom"]
)
# 更新偏移量
position_offsets["bottom"] += bar_height + 5  # 5px间距
```

#### TASK-4: 3+气泡支持 ✅
- [x] 添加`get_bubble_position_for_index()`函数
- [x] 支持任意数量气泡的交替左右布局
- [x] y位置按行递增: [3%, 10%, 18%, 26%, 34%, 42%]

**布局算法**:
```python
def get_bubble_position_for_index(index: int, total: int) -> tuple:
    y_positions = [3, 10, 18, 26, 34, 42]
    row = index // 2
    is_left = (index % 2 == 0)
    x_pct = 30 if is_left else 70
    y_pct = y_positions[min(row, len(y_positions) - 1)]
    return (x_pct, y_pct)
```

#### TASK-5: 对话气泡半透明底 ✅
- [x] 将`fill="white"`改为`fill=(255, 255, 255, 191)`
- [x] alpha=191 ≈ 75%不透明度
- [x] 应用于气泡主体、尾巴、连接线

**半透明实现**:
```python
# P1修复 TASK-5：使用半透明白色背景（75%不透明度）
bubble_fill_color = (255, 255, 255, 191)  # RGBA, alpha=191 ≈ 75%不透明
draw.rounded_rectangle(bubble_rect, radius=18, fill=bubble_fill_color, ...)
draw.polygon(tail_points, fill=bubble_fill_color, ...)
```

**关键产出**:
| 文件 | 说明 |
|------|------|
| `tests/test_comic_cc_kai.py` | P1修复完成（TASK-3/4/5） |

**验证**:
- Python语法验证 ✅

---

### HANDOFF-2026-02-02-013: V2+ TextOverlay P0修复 ✅

**完成时间**: 2026-02-02
**验收状态**: 等待 @Tester 执行V3测试验收

**任务背景**:
- PM对V2进行综合分析，发现10+类新问题
- 其中2个P0级别问题需要Backend立即修复

**完成内容**:

#### TASK-1: Speaker前缀剥离 ✅
- [x] 添加`strip_speaker_prefix()`函数
- [x] 支持"Kai：「内容」"和"Kai内心：「内容」"格式
- [x] 在`add_speech_bubble()`内部自动调用
- [x] 单元测试 6/6 通过

**修复效果**:
```
修复前: "Kai：「你好」"
修复后: "「你好」"
```

#### TASK-2: 气泡位置优化 ✅
- [x] 降低默认y位置避免遮挡脸部
- [x] 单气泡: 10% → 5%
- [x] 双气泡第一个: 8% → 3%
- [x] 双气泡第二个: 20% → 12%
- [x] 混合类型对话: 10% → 5%

**关键产出**:
| 文件 | 说明 |
|------|------|
| `tests/test_comic_cc_kai.py` | P0修复完成 |

**验证**:
- Python语法验证 ✅
- strip_speaker_prefix 单元测试 ✅

---

## 2026-01-31

### HANDOFF-2026-01-31-012: Kai与Cici故事配置调整 ✅

**完成时间**: 2026-01-31
**验收状态**: 等待 @Tester 执行测试

**任务背景**:
- Founder对v1版本42张图发现32+问题（空白气泡、留白、乱码、服装错误）
- PM独立审查确认Prompt模板是根因
- AI-ML完成Prompt修复

**完成内容**:
- [x] 确认AI-ML修复到位（TEXT_FREE_REQUIREMENT替换）
- [x] 确认矛盾指令已删除（grep无匹配）
- [x] 确认服装描述强化（Shot 38, 40）
- [x] 修改OUTPUT_DIR为`comic_cc_kai_story_v2`便于对比
- [x] 更新TEAM_CHAT通知@Tester

**配置修改**:
| 项目 | 修改前 | 修改后 |
|------|--------|--------|
| OUTPUT_DIR | comic_cc_kai_story | comic_cc_kai_story_v2 |

**关键产出**:
| 文件 | 说明 |
|------|------|
| `tests/test_comic_cc_kai.py` | 配置调整完成 |

**预期输出目录**: `test_output/comic_cc_kai_story_v2/`

---

## 2026-01-30

### HANDOFF-2026-01-30-011: Kai与Cici初次约会测试脚本 ✅

**完成时间**: 2026-01-30
**验收状态**: 等待 @Tester 运行脚本并验收生成结果

**任务背景**:
- PM设计了12幕42张分镜大纲
- AI-ML完成了42张图的Prompt和文字脚本
- Backend负责创建可执行的测试脚本

**完成内容**:
- [x] 创建测试脚本 `tests/test_comic_cc_kai.py`
- [x] 定义2个角色 (Kai, Cici) 及其 physical/clothing 字段
- [x] 配置42个完整shot的image_prompt和文字脚本
- [x] 配置SHOT_CHARACTER_MAPPING指定每个shot的出场角色
- [x] 实现 `load_existing_reference_images()` 直接加载现有参考图
- [x] 实现 `build_character_reference_instruction()` 构建参考图指令（仅脸部特征）
- [x] 集成 TextOverlayServiceV2 处理文字叠加
- [x] 标注4个情感重点镜头

**关键设计决策**:

| 决策 | 说明 |
|------|------|
| 参考图使用 | 仅用于脸部特征，忽略参考图中的服装 |
| 参考图加载 | 直接加载现有文件，不重新生成 |
| 服装描述 | 使用故事中定义的服装（非参考图服装） |

**角色服装**（故事中）:
| 角色 | 服装 |
|------|------|
| Kai | 黑紫色毛衣 + 深色牛仔裤 + 黑色大衣 |
| Cici | 黑色针织衫 + 浅灰色半身裙 + 黑色长大衣 + 红色丝巾 |

**情感重点镜头**:
| Shot | 情感 |
|------|------|
| 10-11 | 心动瞬间 |
| 29 | 牵手 |
| 38 | 拥抱 |
| 40 | 脸颊之吻 |

**关键产出**:
| 文件 | 说明 |
|------|------|
| `tests/test_comic_cc_kai.py` | 42张完整测试脚本 |

**预期输出目录**: `test_output/comic_cc_kai_story/`

**验证重点**:
- 角色一致性: Kai/Cici 五官在所有图中保持一致
- 服装正确: 穿故事中描述的服装，非参考图服装
- 韩漫风格: 精致五官、柔和光线、情感表达细腻
- 文字叠加: 对话气泡、旁白、内心独白正确渲染

---

## 2026-01-29

### BUG-BUBBLE-001: 对话泡泡位置跟随说话者修复 ✅

**完成时间**: 2026-01-29
**验收状态**: 等待 @PM 验收

**问题背景**:
- `speaker_position` 参数对 `dialogue` 类型无效，泡泡总是居中
- 故事C Shot 06 老陈说话（`speaker_position="right"`），泡泡却在左上角默认位置
- 读者会误认为是林夜（左侧）在说话

**根因分析**:
`process_shot()` 方法中 `dialogue` 类型只检查 `bubble_positions`（AI检测结果），当没有AI检测结果时直接使用默认值 `(50, 10)`，完全忽略了 `speaker_position` 参数。

**完成内容**:
- [x] 添加 `get_default_x_by_speaker_pos()` 辅助函数
- [x] 修改 `dialogue` 类型处理逻辑，当没有AI检测结果时使用 `speaker_position` 作为 fallback
- [x] 修复 `tests/test_comic_story_c_cyberpunk.py`
- [x] 修复 `tests/test_comic_story_b_wuxia_ink.py`（同样的Bug）

**关键修复**:
```python
def get_default_x_by_speaker_pos(pos: str) -> int:
    if pos == "right":
        return 70  # 靠右
    elif pos == "left":
        return 30  # 靠左
    else:
        return 50  # 居中

# dialogue 类型处理
else:
    # 使用 speaker_position 作为 fallback (BUG-BUBBLE-001 修复)
    x_pct = get_default_x_by_speaker_pos(speaker_pos)
    y_pct = 10
```

**关键产出**:
| 文件 | 说明 |
|------|------|
| `tests/test_comic_story_c_cyberpunk.py` | 修复 dialogue 类型的 speaker_position 支持 |
| `tests/test_comic_story_b_wuxia_ink.py` | 同样的修复 |

**受影响镜头**:
- 故事C Shot 06 (老陈说话, speaker_position="right" → 泡泡靠右)
- 故事C Shot 13 (老陈说话, speaker_position="left" → 泡泡靠左)

---

### TASK-VERIFY-001-C: 故事C《最后的记忆商人》测试脚本 ✅

**完成时间**: 2026-01-29
**验收状态**: 等待 @Tester 运行脚本并验收生成结果

**问题背景**:
- 多风格通用性验证测试 (TASK-VERIFY-001)
- 验证系统对不同故事类型、视觉风格的通用性
- 故事C: 赛博朋克 + Neo-Noir 风格

**完成内容**:
- [x] 创建测试脚本 `tests/test_comic_story_c_cyberpunk.py`
- [x] 定义3个赛博朋克角色 (lin_ye, old_chen, kayla)
- [x] 配置 Cyberpunk / Neo-Noir 风格前缀
- [x] 添加记忆场景处理 (Shot 14, MEMORY_SCENE_TREATMENT - 明亮自然光对比)
- [x] 添加追逐场景处理 (Shots 10-11, CHASE_SCENE_TREATMENT)
- [x] 配置15个完整shots及image_prompt
- [x] 角色关键标识定义（义眼颜色、赛博义肢等）

**关键产出**:
| 文件 | 说明 |
|------|------|
| `tests/test_comic_story_c_cyberpunk.py` | 故事C完整测试脚本 |

**预期输出目录**: `test_output/comic_full_story_v2_cyberpunk/`

**角色定义**:
| 角色 | 关键标识 |
|------|----------|
| 林夜 (lin_ye) | 银色左眼义眼+蓝光、右颊淡疤、深灰皮夹克 |
| 老陈 (old_chen) | 白发、蓝色工装、金属拐杖、手背氧化神经端口 |
| 凯拉 (kayla) | 双红眼义眼、银白短发、金属右臂、黑色战术装甲 |

**验证重点**:
- 角色一致性: 林夜(银色左眼义眼+蓝光)
- 角色一致性: 老陈(白发/蓝色工装)
- 角色一致性: 凯拉(双红眼义眼/金属右臂)
- 赛博朋克风格: 霓虹灯/湿地反光/全息广告/暗黑氛围
- 记忆对比: Shot 14 明亮自然光 vs 其他暗黑镜头
- 追逐场景: Shot 10-11 动态感

---

## 2026-01-28

### TASK-RESILIENCE-001: 图像生成韧性机制 ✅

**完成时间**: 2026-01-28
**验收状态**: 等待 @Tester 验收

**问题背景**:
- Story B 故事《断剑》Shot 06 触发 Gemini 内容安全过滤
- 原因: prompt 含 "motionless youth", "dark spreading pool", "killer/victim" 等敏感词
- 表现: `response.parts` 为 None，迭代时抛出 `'NoneType' object is not iterable`

**完成内容**:

#### TASK-RESILIENCE-001-A: 错误分类
- [x] 添加 `ErrorType` 枚举 (API_ERROR, RATE_LIMIT, CONTENT_SAFETY, FORMAT_ERROR, UNKNOWN)
- [x] 添加 `_classify_error()` 方法
- [x] 修改 `generate_image()` 在迭代 `response.parts` 前检查 None
- [x] 修改 `generate_shot_image_phase2()` 同样检查并分类错误
- [x] 返回 `error_type` 字段供上层处理

#### TASK-RESILIENCE-001-B: Prompt 改写服务
- [x] 创建 `PromptRewriter` 服务类 (`app/services/prompt_rewriter.py`)
- [x] 实现 `rewrite()` 方法 - Claude Haiku 智能改写
- [x] 实现 `rewrite_simple()` 方法 - 简单规则替换
- [x] 添加 `generate_shot_image_phase2_safe()` 方法到 ImageGenerator
- [x] 集成自动改写重试流程

**关键产出**:
| 文件 | 说明 |
|------|------|
| `app/services/image_generator.py` | ErrorType枚举, _classify_error(), generate_shot_image_phase2_safe() |
| `app/services/prompt_rewriter.py` | PromptRewriter 服务类 |

**技术细节**:
```python
# 自动改写重试流程
result = await image_gen.generate_shot_image_phase2_safe(
    shot=shot,
    ...,
    genre="wuxia"  # 用于题材特定替换规则
)

# 流程:
# 1. 首次尝试生成
# 2. 如果 CONTENT_SAFETY 错误，使用 Haiku 智能改写
# 3. 重试生成
# 4. 如果仍失败，降级到简单规则替换再试
```

**依赖**:
- AI-ML 交付的 `app/prompts/prompt_safety_rewrite.py`
- Claude 4.5 Haiku API

---

## 2026-01-27

### TASK-VERIFY-001-C: 故事B《断剑》测试脚本 ✅

**完成时间**: 2026-01-27
**验收状态**: 等待 @Tester 运行脚本并验收生成结果

**问题背景**:
- 多风格通用性验证测试 (TASK-VERIFY-001)
- 验证系统对不同故事类型、视觉风格的通用性
- 故事B: 古装武侠 + Chinese Ink Wash (水墨) 风格

**完成内容**:
- [x] 创建测试脚本 `tests/test_comic_story_b_wuxia_ink.py`
- [x] 定义4个武侠角色 (master_old, master_young, disciple, enemy)
- [x] 配置 Chinese Ink Wash 水墨风格前缀
- [x] 添加回忆场景处理 (Shots 04-06, MEMORY_SCENE_TREATMENT)
- [x] 添加动作场景处理 (Shots 10-11, ACTION_SCENE_TREATMENT)
- [x] 添加红色强调处理 (Shot 06, ！！！)
- [x] 处理无文字场景 (Shots 07, 11, text_type="none")
- [x] 配置15个完整shots及image_prompt

**关键产出**:
| 文件 | 说明 |
|------|------|
| `tests/test_comic_story_b_wuxia_ink.py` | 故事B完整测试脚本 |

**预期输出目录**: `test_output/comic_full_story_v2_wuxia_ink/`

**验证重点**:
- 角色一致性: 老剑客(白发/麻布袍/左颊疤痕)
- 年龄一致性: master_young vs master_old
- 水墨风格: 笔触感/留白/墨色层次/宣纸质感
- 动作场景: 剑术对决动态感
- 回忆场景: 暖色调柔光

---

### TASK-OPT-005-B: AI智能推荐泡泡位置 ✅

**完成时间**: 2026-01-27
**验收状态**: 等待 @Tester 验收 (TASK-OPT-005-C)

**问题背景**:
- 创始人反馈泡泡遮挡角色脸部（shot_04, shot_14）
- y坐标固定(12%/25%/40%)不够精确

**完成内容**:
- [x] 修改 `detect_character_positions()` 返回 `{char_id: {"bubble_x_percent": int, "bubble_y_percent": int}}`
- [x] 修改 `add_speech_bubble()` 接受 `bubble_x_percent, bubble_y_percent` 参数
- [x] 修改 `process_shot()` 使用 `bubble_positions` 字段
- [x] 修改集成代码存储完整泡泡位置

**关键产出**:
| 文件 | 说明 |
|------|------|
| `tests/test_comic_full_story_v2.py` | AI推荐泡泡位置实现 |

**技术细节**:
```python
# 之前 (y坐标固定)
bubble_y = int(height * 0.12)  # 固定值

# 现在 (AI推荐)
bubble_x = int(width * bubble_x_percent / 100) - bubble_width // 2
bubble_y = int(height * bubble_y_percent / 100)
# 不需要额外边界检查，AI已经考虑
```

**优势**:
- 通用性高：任何故事、任何风格、任何构图
- 代码简单：不需要边界检查、避让算法
- 成本不变：~$0.04/故事
- 可扩展：发现新问题只需调整Prompt

---

### TASK-OPT-004-B: 泡泡百分比定位 ✅

**完成时间**: 2026-01-27
**验收状态**: ✅ 通过 (TASK-OPT-004-C)

**问题背景**:
- 创始人反馈对话泡泡位置不够精确
- 原来三分类(left/center/right)粒度太粗，映射到固定位置(5%/50%/95%)

**完成内容**:
- [x] 修改 `detect_character_positions()` 返回 `x_percent` (0-100)
- [x] 修改 `add_speech_bubble()` 使用百分比动态定位
- [x] 修改尖角绘制指向角色实际位置
- [x] 修改 `process_shot()` 支持新字段 `speaker_x_percent`
- [x] 修改集成代码存储百分比结果

**关键产出**:
| 文件 | 说明 |
|------|------|
| `tests/test_comic_full_story_v2.py` | 百分比定位实现 |

**技术细节**:
```python
# 气泡位置计算
char_x = int(width * speaker_x_percent / 100)
bubble_x = char_x - bubble_width // 2
bubble_x = max(10, min(bubble_x, width - bubble_width - 10))
```

---

### dotenv加载修复 ✅

**完成时间**: 2026-01-27

**问题**: Tester验收时ANTHROPIC_API_KEY未加载，Haiku检测跳过

**修复**: 添加 `load_dotenv()` 自动加载 `.env` 文件

---

### TASK-OPT-001: 透明度自适应 ✅

**完成时间**: 2026-01-27
**验收状态**: 等待 @Tester 验收 (TASK-OPT-003)

**问题背景**:
- Ghibli等明亮风格图片黑底过暗，影响可读性
- 需要根据图片亮度动态调整overlay透明度

**完成内容**:
- [x] 添加 `get_overlay_alpha_by_brightness()` 方法
- [x] 使用PIL计算overlay区域平均亮度
- [x] 根据亮度阈值返回不同alpha值
- [x] 修改 `add_monologue()` 调用新方法

**关键产出**:
| 文件 | 说明 |
|------|------|
| `tests/test_comic_full_story_v2.py` | 添加亮度自适应方法 |

**亮度阈值**:
- `> 180` → alpha=100（非常透明）
- `> 140` → alpha=130
- `> 100` → alpha=160
- `≤ 100` → alpha=190（较不透明）

---

### TASK-OPT-002-B: 集成Haiku角色位置检测 ✅

**完成时间**: 2026-01-27
**验收状态**: 等待 @Tester 验收 (TASK-OPT-003)

**问题背景**:
- 对话气泡位置硬编码，可能遮挡角色
- 需要根据角色实际位置动态定位气泡

**完成内容**:
- [x] 添加 `anthropic` 和 `base64` imports
- [x] 导入 AI-ML 的 Prompt 模块
- [x] 添加 `detect_character_positions()` 异步函数
- [x] 集成到主流程，对 dialogue 类型 shot 检测位置
- [x] 动态更新 `speaker_position` 字段

**关键产出**:
| 文件 | 说明 |
|------|------|
| `tests/test_comic_full_story_v2.py` | 添加位置检测函数和集成 |

**技术细节**:
- 使用 Claude 4.5 Haiku 多模态API
- 输入：shot图 + 角色fullbody参考图
- 输出：`{char_id: "left"|"center"|"right"}`
- 成本：~$0.04/故事（15 shots）

---

## 2026-01-26

### TASK-FIX-006: 修复参考图生成bug ✅

**完成时间**: 2026-01-26 12:30
**验收状态**: 等待 @Tester 验收

**问题背景**:
- 创始人二次审核发现 `reference_images/` 目录为空
- 5个角色参考图全部生成失败

**根因分析**:
| 错误假设 | 实际格式 |
|----------|----------|
| `{'success': True, ...}` | `{'portrait': {...}, 'fullbody': {...}}` |

`generate_reference_images()` 函数对 `ReferenceImageManager.generate_character_multi_refs()` 返回格式处理错误

**完成内容**:
- [x] 对比 teststory6.4 正确实现
- [x] 修复 `generate_reference_images()` 函数
- [x] 正确解析嵌套结构获取 `pil_image`
- [x] 保存参考图到 `reference_images/` 目录

**关键产出**:
| 文件 | 说明 |
|------|------|
| `tests/test_comic_full_story_v2.py` | 修复参考图生成函数 |

**经验教训**:
- `generate_character_multi_refs()` 返回嵌套格式，需正确解析
- 参考 teststory6.4 的正确实现模式

---

## 2026-01-23

### TASK-FIX-002: 启用参考图机制 ✅

**完成时间**: 2026-01-23
**验收状态**: 通过

**完成内容**:
- [x] 创建 `test_comic_full_story_v2.py`
- [x] 集成 ReferenceImageManager
- [x] 为5个角色变体定义完整格式
- [x] 优化红色强调检测

**关键产出**:
| 文件 | 说明 |
|------|------|
| `tests/test_comic_full_story_v2.py` | 带参考图的完整故事测试脚本 |

---

## 2026-01-22

### TASK-B: 条漫完整故事测试脚本 ✅

**完成时间**: 2026-01-22 23:45
**验收状态**: 通过 (28/30 = 93.3%)

**完成内容**:
- [x] 角色定义：5个角色变体完整配置
- [x] 风格前缀：Ghibli-inspired + MEMORY_SCENE_TREATMENT
- [x] 15图配置：完整集成AI-ML的所有配置
- [x] 文字叠加：TextOverlayService (narration/thought/dialogue)
- [x] 特殊效果：Shot 09 红色强调, Shot 07-10 回忆场景

**关键产出**:
| 文件 | 说明 |
|------|------|
| `tests/test_comic_full_story.py` | 15图完整故事测试脚本 |

---

## 2025-12-31 之前 (Phase 1-3)

### Phase 3: 音频对齐 ✅

**完成时间**: 2025-01-05
**验收状态**: 通过

**完成内容**:
- [x] TTS 服务集成 (火山引擎 Doubao)
- [x] Whisper 时间戳提取
- [x] 多策略文本匹配算法
- [x] 繁简转换处理
- [x] 时间轴生成

**关键产出**:
| 文件 | 说明 |
|------|------|
| `app/services/tts_service.py` | TTS 服务 |
| `app/services/whisper_service.py` | Whisper 服务 |
| `app/services/alignment_service.py` | 对齐算法 |

**验收指标**:
- 时间精度: ≤80ms ✅
- 繁简转换: 100% 准确 ✅

---

### Phase 2: 图像生成 ✅

**完成时间**: 2025-12-23
**验收状态**: 通过

**完成内容**:
- [x] 五阶段 Pipeline 架构
- [x] 角色一致性突破 (Pro模型方案)
- [x] 场景参考图系统
- [x] Shot 间连续性

**关键产出**:
| 文件 | 说明 |
|------|------|
| `app/services/image_generator.py` | 图像生成核心 |
| `app/services/reference_image_manager.py` | 参考图管理 |
| `app/services/scene_reference_manager.py` | 场景参考图 |
| `app/services/storyboard_service.py` | 分镜服务 |

**验收指标**:
- 3人场景一致性: 100% ✅
- 6人场景一致性: ~90% ✅

---

### Phase 1: 故事生成 ✅

**完成时间**: 2025-12-11
**验收状态**: 通过

**完成内容**:
- [x] 故事大纲生成
- [x] 角色设计
- [x] 分场剧本
- [x] 分镜脚本

---

## 任务归档模板

```markdown
### [任务标题] ✅

**完成时间**: YYYY-MM-DD
**验收状态**: 通过/部分通过

**完成内容**:
- [x] 内容1
- [x] 内容2

**关键产出**:
| 文件 | 说明 |
|------|------|
| path/to/file | 说明 |

**验收指标**:
- 指标1: 结果 ✅/❌

**经验教训**:
- 学到了什么
```
