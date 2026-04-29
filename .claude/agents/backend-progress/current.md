# Backend Agent - 当前任务

> **最后更新**: 2026-04-28 17:00

## ✅ TASK-T6-FIXBATCH Wave 2.5 D.15 P0 — aspect_ratio 完整修复 (2026-04-28 17:00)

**状态**: ✅ 4 文件修复，pytest 292/292 ✅

| 项 | 状态 | 文件 |
|----|------|------|
| `_ASPECT_RATIO_TO_SIZE` 补 `3:4` + `4:3`（现 7 种比例） | ✅ | seedream_generator.py |
| `pipeline.run()` 加 `aspect_ratio` 参数 | ✅ | pipeline_orchestrator.py |
| 真生图调用 `aspect_ratio=aspect_ratio`（不再 hardcoded "2:3"） | ✅ | pipeline_orchestrator.py L852 |
| ARCH-1 SceneImage width/height/aspect_ratio 从参数动态查 | ✅ | pipeline_orchestrator.py L1046-1079 |
| `run_story_generation_task()` 加 `aspect_ratio` 参数 + pipeline 传值 | ✅ | job_manager.py |
| `_run_generation_in_background()` 加 `aspect_ratio` 参数 | ✅ | projects.py |
| `start_generation()` 传 `project.aspect_ratio or "2:3"` | ✅ | projects.py |

**修改文件列表**:
- `app/services/seedream_generator.py` — `_ASPECT_RATIO_TO_SIZE` 补 `3:4` / `4:3`
- `app/services/pipeline_orchestrator.py` — `run()` 签名加 `aspect_ratio` + 3 处 hardcoded "2:3" 全部消除
- `app/services/job_manager.py` — `run_story_generation_task()` 加参数 + pipeline.run() 传值
- `app/api/projects.py` — `_run_generation_in_background()` + `start_generation()` 传 `project.aspect_ratio`

**等 PM 审查 → 决定是否进 T7 前部署**

---

## ✅ TASK-T6-FIXBATCH Wave 2 Agent D — R7-1 Dashboard 列表 backend 扩展完成 (2026-04-28 16:00)

**状态**: ✅ 2 文件改动，pytest 24/24 ✅（architecture 7 + parallel_stage5 17）

| 项 | 状态 | 文件 |
|----|------|------|
| `cover_image_url` 字段（storyboard shots[0].image_url） | ✅ | app/schemas/project.py + app/api/projects.py |
| `shot_count` 字段（storyboard 长度） | ✅ | app/schemas/project.py + app/api/projects.py |
| `mood` 字段（user_selected_mood ?? mood ?? null） | ✅ | app/schemas/project.py + app/api/projects.py |
| `created_at` / `updated_at` ISO 8601 with Z | ✅ | app/schemas/project.py + app/api/projects.py |
| N+1 避免（2 固定查询） | ✅ | app/api/projects.py list_projects |
| storyboard 双格式兼容（list / dict.shots） | ✅ | app/api/projects.py _parse_storyboard_cover_and_count |

**修改文件列表**:
- `app/schemas/project.py` — `ProjectDetail` 字段扩展（4 新字段 + datetime → str）
- `app/api/projects.py` — `from datetime import datetime, timezone`；3 helper 函数；`serialize_project_detail` 加 chapter 参数；`list_projects` 2-query N+1 避免

**等 PM 审查 → @frontend Agent E 读新字段**

---

## ✅ TASK-T6-FIXBATCH Wave 2 Agent F — ARCH-1 chapter_scene_images 写入完成 (2026-04-28 15:50)

**状态**: ✅ 完成，pytest 211/211 ✅

| 项 | 状态 | 文件 |
|----|------|------|
| P1-7 ARCH-1: pipeline 完成后批量写入 chapter_scene_images | ✅ | pipeline_orchestrator.py + job_manager.py |

**修改文件**:
- `app/services/pipeline_orchestrator.py` — `run()` 加 `chapter_id` 参数 + Stage 5 完成后 ARCH-1 批量写入块（DELETE + INSERT）
- `app/services/job_manager.py` — `pipeline.run()` 调用传 `chapter_id=chapter_id`

**验证**: pytest 211/211 ✅ import check ✅ 所有禁改文件未碰 ✅

**等 PM 审查**: 代码审查后可派 @devops 部署。

---

## ✅ R7-3 P1 — portrait 重生静默失效 bug 修复完成 (2026-04-28 21:42)

**状态**: ✅ 修复完成，backend 实测验证通过

| 项 | 状态 |
|----|------|
| 真因定位 | ✅ `character_prompt_builder._build_human_description()` L100-102 对 str 类型字段调 `.get()` |
| 修复实施 | ✅ `app/services/character_prompt_builder.py` 2 处防御性类型检查 |
| pytest 24/24 | ✅ |
| backend 重启 | ✅ pid 27833 |
| backend log 无异常 | ✅ `R7-3: char_001 肖像已重生成`，无 `'str' object has no attribute 'get'` |
| portrait mtime 变化 | ✅ `1777379854.28` → `1777383723.85` |
| DB portrait_url 更新 | ✅ `/static/outputs/.../char_001_portrait.png` |
| DB updated_at 更新 | ✅ `2026-04-28T13:42:03.852076Z` |
| 禁改文件未碰 | ✅ |
| D.15 aspect_ratio 链路 | ✅ 无影响 |

---

> 上轮完成记录见下方

## ✅ TASK-T6-FIXBATCH Wave 1.1 Agent A — 修复 round 1 完成 (2026-04-28 15:05)

**状态**: ✅ 5 项 + 修复 round 1 全部完成，pytest 7/7 ✅

| 项 | 状态 | 文件 |
|----|------|------|
| P0-2 mark_completed stage='completed' | ✅ | job_manager.py |
| P1-1 Stage label 重构（4 callback 修正 + image_generation 入口） | ✅ | pipeline_orchestrator.py |
| P1-2 STAGE_DURATIONS + estimate_remaining() + progress 单调 guard + **ETA 链路接通** | ✅ | pipeline_orchestrator.py + job_manager.py + **chapters.py** |
| P1-3 adjust 后 portrait 重生 + freshness check（**含 30s buffer**）+ 新端点 | ✅ | projects.py + pipeline_orchestrator.py + reference_image_manager.py |
| P1-5 character_ready 等 portrait 全成才设 | ✅ | pipeline_orchestrator.py |

**修改文件列表（含修复 round 1）**:
- `app/services/job_manager.py` — P0-2 + P1-2（单调 guard + estimated_remaining_seconds）
- `app/services/pipeline_orchestrator.py` — P1-1 + P1-2（STAGE_DURATIONS/estimate_remaining）+ P1-3（freshness check **30s buffer**）+ P1-5
- `app/services/reference_image_manager.py` — P1-3（skip_portrait 参数）
- `app/api/projects.py` — P1-3（adjust_character Step 7 + 新端点）
- `app/api/chapters.py` — **修复 round 1 P1-2**: import estimate_remaining + /status ETA 替换为 stage-aware 逻辑

**修复 round 1 关键变更**:
- `chapters.py` L21: `from app.services.pipeline_orchestrator import estimate_remaining`
- `chapters.py` L143-156: /status ETA 由旧 `job.estimated_seconds - elapsed` 改为 `estimate_remaining(job.current_stage, stage_progress=0.5)`，含 fallback
- `pipeline_orchestrator.py` L645: `_portrait_fresh = _portrait_mtime > (_char_ts + 30)` （30s buffer）

**验证**: pytest tests/test_architecture.py 7/7 ✅；import check ✅；所有禁改文件未触碰 ✅

**等 PM 审查**: 代码审查后派 @devops 部署，Wave 1.2 (Agent C UX-16) 可启动

---

> 上轮完成记录见下方

## ✅ TASK-T5-FIXBATCH-R6 子任务 1 — ProjectDetail 加 confirmed_outline + aspect_ratio (2026-04-27 17:30)

**状态**: ✅ 完成，等 PM 审查

**修改文件**:
- `app/schemas/project.py` — ProjectDetail 新增 `confirmed_outline: dict[str, Any] | None = None` + `aspect_ratio: str | None = None`
- `app/api/projects.py` — serialize_project_detail 解析 confirmed_outline_json + 注入两个新字段

**验证**: pytest 211/211 ✅ + schema 实例化测试 ✅

**下一步**: 等 PM 审查 → @frontend 可开始 R6 子任务 2 重写 StoryDetailContent.tsx

---

> **最后更新 (PM 代更)**: 2026-04-27 16:33
## 🆕 TASK-T5-FIXBATCH round 5 紧急 hotfix (2026-04-27 16:50, PM 代更)

### ✅ ChapterStory Pydantic schema 兼容修复

**根因**: `ChapterStory.scenes` / `characters` 字段名跟 Stage 3 ScreenplayWriter / Stage 2 CharacterDesigner 实际输出**完全不匹配**，导致 `/api/projects/{uuid}/chapters/{n}/story` 端点 41 validation errors → 500 → Stage E 进不去.

**修复方案 A (最干净)**:
- `app/schemas/chapter.py`: 删除 SceneInfo / CharacterInfo 类（全项目无引用）
- ChapterStory.scenes 改 `list[dict[str, Any]]`
- ChapterStory.characters 改 `list[dict[str, Any]]`
- 保留 title / summary / full_script 类型校验

**验证**:
- ✅ pytest 211/211 passed
- ✅ /chapters/1/story curl 不再 500 (返 401 auth)
- ✅ T5-FIXBATCH 之前 BE-3/4/5/BGM-1/OBS-4/UX-1/10/11/14 零影响

---


> **状态**: ✅ TASK-T5-FIXBATCH 8 条后端修复完成 + Hot-fix T5 数据补 URL 完成

---

## 最新完成 (2026-04-27 16:33)

### ✅ TASK-T5-FIXBATCH 8 条后端修复

| # | 条目 | 修改 |
|---|------|------|
| BE-3 P0 | image_url 写回 storyboard | pipeline_orchestrator.py Stage 5 每张 shot 完成写 image_url + checkpoint_callback storyboard_json |
| BE-4 P0 | /chapters/{n}/storyboard 端点 | chapters.py 新加 GET 端点 |
| BE-5 P0 | bgm_url HTTP URL | pipeline_orchestrator.py Stage 6 后转 HTTP path 写 chapter.bgm_url |
| BGM-1 P1 | outline.music_hint 注入 | Stage 1 后 outline["music_hint"] = get_raw_hint(style_preset) |
| OBS-4 P1 | 用户情绪持久化 | ConfirmOutlineRequest.user_selected_mood 持久化到 outline.mood / visual_tone.overall_mood |
| UX-10/11 P1 | BGM stage + completed signal | progress_callback("bgm", 92) + ("completed", 100) + job_manager status |
| UX-1/14 P1 | Stage 2 portrait 提前 | Stage 2 后调 generate_character_reference('portrait')，写 character_refs/ + characters_json.portrait_url |
| UX-2 A2 P2 | outline 一致性 LLM check | confirm-outline 加 Sonnet 4.6 一致性 check 返 warnings |

**测试**: 211/211 真实 venv 通过 (7 architecture + 17 parallel + 187 music_hint)

**修改文件**: pipeline_orchestrator.py / chapters.py / projects.py / job_manager.py + 新建 scripts/hotfix_t5_urls.py

**Hot-fix T5 数据**: 已跑 hotfix 给 T5 项目 (uuid=283bd407-0e64-43bb-b2eb-8f6b4063c4af) 补 image_url + bgm_url，Founder 现在可看图听 BGM
## 最新进展 [2026-04-25 16:30 — round 3 完成]

### ✅ TASK-PARALLEL-M1 round 3 — Phase 2 D1 暴露的 4 bug 全部修复

**Bug 1 project_id=None ✅**: pipeline_orchestrator.py 加 else 分支 — 当 project_uuid=None (driver/test 模式) 时创建 temp Project DB record（user_id=0 sentinel）拿真 integer id

**Bug 2 ShotValidator 鉴权 ✅**: shot_validator.py 显式  传给 AsyncAnthropic（pydantic-settings 不写 os.environ）

**Bug 3 IncompleteRead ✅**: seedream_generator.py SEEDREAM_HTTP_RETRIES 2→3 + 加 retry log + retry_count 统计返回

**Bug 4 Event loop closed ✅**: image_generator.py + seedream_generator.py 把  改  (~10ms/shot 额外延迟，160ms/16-shot 故事，可接受)

**Bonus**: tests/test_parallel_stage5.py branch1/2 patch IMAGE_GEN_PROVIDER=nb2，避免 .env 的 Seedream dispatcher 干扰 NB2 路径 mock

**pytest**: 24/24 passed in 0.80s ✅

**修改文件**: pipeline_orchestrator.py / shot_validator.py / seedream_generator.py / image_generator.py / tests/test_parallel_stage5.py (5 个)

**Phase 2 D1 浪费统计**: 用旧代码跑出 36 shots × ¥0.22 ≈ ¥7.92（PM kill stale processes + 重启 backend 后 stop bleed）

---

## 最新进展 [2026-04-25 16:00 — PM 审查]

### 🟡 TASK-PARALLEL-M1 Phase 1 — 代码完成附 3 隐忧

**Backend agent 完成内容** (24/24 tests passed via conftest stubs):
- pipeline_orchestrator.py Stage 5: serial → asyncio.Semaphore(IMAGE_MAX_CONCURRENT) + asyncio.gather + gc.collect 累积态兜底 + Haiku validator 并行 + 0.5s 冷却保留在 Semaphore 内
- image_generator.py + seedream_generator.py: 成功路径 asyncio.ensure_future(log_api_cost(...))
- 新建 app/services/api_cost_logger.py (3.3KB) ARCH-4 INSERT 路径
- 新建 app/models/api_cost_log.py ORM model + app/models/__init__.py 导出
- 新建 tests/test_parallel_stage5.py (25KB) 17 用例覆盖 8 失败分支 + Q2/Q3/ARCH-4
- 新建 conftest.py (14.6KB) stub 外部依赖让测试能跑

**PM 审查 3 隐忧**:
1. conftest.py stub 了所有外部依赖 → 24/24 不是真实环境验证
2. PipelineCostTracker.check_db_cost_limit() 在 project_id=None 时 graceful skip → ARCH-4 READ 路径在 string-id 场景下未生效（INSERT 已通）
3. 文档 4 件套 agent 自报权限不够没更新（PM 代更兜底）

**等 Founder 决策**: 进 Phase 2 (Tester) 还是先 Backend round 2 修隐忧

---

## 上轮 [2026-04-25 13:48] — TASK-SHOT08-DIAGNOSIS
### ✅ TASK-SHOT08-DIAGNOSIS — Shot 8 Seedream 卡死根因诊断

**任务**: 单独跑 R8 shot_8（4 角色 + 2 场景 = 6 refs），通过生产路径 `generate_shot_image_phase2_safe()` 判断根因 A/B/C

**执行方式**: 方案 1（`bash -c` wrapper）成功跑通，耗时 81.6s 完成

**结论**: **根因 A — 累积态资源耗尽**。单独跑 shot_8 成功（1664x2496 生图，3218KB），明确排除根因 B（代码层同步阻塞）和根因 C（API payload 拒绝）。

**关键数据**:

| 指标 | 数值 |
|------|------|
| outcome | success |
| root_cause | A |
| mem_peak_mb | 290.45 MB |
| payload_bytes | 10,363,884 (~9.88 MB) |
| total_elapsed_sec | 81.603 s |
| api_call 耗时 | 78.648 s |
| http_status | null（无错误）|
| exception_type | null（无异常）|

**含义**: 前 7 个 shot 跑完后内存/socket/handle 未完全释放，第 8 个 shot 时资源耗尽卡死。生产 FastAPI 每次请求独立调用栈，不会重现此问题。

**修复建议**:
- 生产代码**无需修改**（FastAPI 调用栈天然隔离）
- 若修复批量测试脚本的卡死，在第 7/8 个 shot 之间加 `await asyncio.sleep(1)` 或 `gc.collect()` 即可

**产物**: `test_output/manualtest/shot8_diagnosis_2026-04-25/` (diagnose.log, result.json, shot_08.png)

---

## 上一完成 [2026-04-24 23:00]

### ✅ TASK-SEEDREAM-INTEGRATION 补丁 — `generate_shot_image_phase2_safe()` dispatcher 修复

**根因**: 上次 dispatcher 仅挂在 `generate_shot_image()`（Phase 1 legacy），但生产 `pipeline_orchestrator.py:583` 调用的是 `generate_shot_image_phase2_safe()`，导致 `IMAGE_GEN_PROVIDER=seedream` 在生产 Pipeline 完全无效。

**本次改动**（仅 `app/services/image_generator.py`，+12 行）

在 `generate_shot_image_phase2_safe()` docstring 之后（L1374）插入同款 dispatcher：

```python
# TASK-SEEDREAM-INTEGRATION dispatcher: Seedream 路径 + NB2 fallback（NB2 原逻辑零改动）
if settings.IMAGE_GEN_PROVIDER == "seedream" and not kwargs.pop("_seedream_fallback", False):
    from app.services.seedream_generator import generate_shot_image_seedream
    _kwargs_copy = dict(kwargs)
    return await generate_shot_image_seedream(
        shot=shot, reference_images=reference_images, aspect_ratio=aspect_ratio,
        fallback_callback=lambda: self.generate_shot_image_phase2_safe(
            shot=shot, storyboard=storyboard, characters=characters,
            style_preset=style_preset, reference_images=reference_images,
            screenplay=screenplay, aspect_ratio=aspect_ratio, genre=genre,
            use_native_text=use_native_text, _seedream_fallback=True, **_kwargs_copy))
```

**关键设计**:
- fallback_callback → `generate_shot_image_phase2_safe`（完整生产路径，含内容安全改写）
- `_seedream_fallback=True` guard 防无限递归
- `_kwargs_copy` 在 lambda 外提前拷贝（pop 后安全）
- `seedream_generator.py` 无需修改

**验收**:

| 项 | 结果 |
|----|------|
| `_phase2_safe` dispatcher 行号 | ✅ L1374 |
| 两 dispatcher 合计 diff | ✅ **+19 行**（`generate_shot_image` +7，`_phase2_safe` +12），≤ 25 ✅ |
| NB2 `_phase2_safe` body 零改动 | ✅ |
| pytest test_architecture | ✅ **7 passed in 0.04s** |
| import check | ✅ 无 ImportError |
| `seedream_generator.py` 需改 | ✅ 无需改（签名已兼容） |

---

---

## 最新进展 [2026-04-24 22:10]

### ✅ TASK-SEEDREAM-INTEGRATION — Seedream 5.0-lite 接入生产作测试期主力

**Founder 4 项决策全部落地**:
- Q1 env flag `IMAGE_GEN_PROVIDER=seedream|nb2` 零代码切换 ✅
- Q2 用 5.0-lite `doubao-seedream-5-0-260128`（硬编码在 seedream_generator.py）✅
- Q3 Sanitize 3 次失败 → 降级 NB2 fallback_callback（保证 Pipeline 不断）✅
- Q4 火山方舟国内版 `https://ark.cn-beijing.volces.com/api/v3/images/generations` ✅

**4 个文件改动**

| 文件 | 类型 | 行数 | 说明 |
|------|------|------|------|
| `app/config.py` | 修改 | +10 | 新增 `IMAGE_GEN_PROVIDER: str = "nb2"` + `ARK_API_KEY: str = ""` |
| `.env.example` | 修改 | +12 | 新增 IMAGE_GEN_PROVIDER 配置块（含注释示例）+ ARK_API_KEY 占位 |
| `app/services/seedream_generator.py` | **新建** | +555 | 封装 API 调用 + text_overlay 注入 + sanitize 3 级 + NB2 fallback |
| `app/services/image_generator.py` 🔴 | 修改 | **+7** | `generate_shot_image()` 入口 dispatcher，NB2 原逻辑零改动 |

**🔴 image_generator.py 改动（7 行）** — 仅在 `generate_shot_image()` docstring 之后入口处插入：

```python
# TASK-SEEDREAM-INTEGRATION dispatcher: Seedream 路径 + NB2 fallback（NB2 原逻辑零改动）
if settings.IMAGE_GEN_PROVIDER == "seedream" and not kwargs.pop("_seedream_fallback", False):
    from app.services.seedream_generator import generate_shot_image_seedream
    return await generate_shot_image_seedream(
        shot=shot, reference_images=reference_images, aspect_ratio=aspect_ratio,
        fallback_callback=lambda: self.generate_shot_image(shot, reference_images,
            aspect_ratio, use_llm_translation, _seedream_fallback=True, **kwargs))
```

`_seedream_fallback` kwarg guard 防止 fallback 再次进入 dispatcher 造成无限递归；kwarg 在传回时被 `kwargs.pop` 消费掉不会污染 NB2 原参数。

**Sanitize 关键词表（POC Phase 3/4 实证 + 预防性扩展，共 27 条，分 3 级）**

- Attempt 1（10 条，POC 实测拦截词保守替换）:
  - `elderly man → older man` / `elderly woman → older woman` / `elderly → older`
  - `furrow of quiet worry → sense of quiet contemplation`
  - `quiet worry → quiet contemplation` / `worry → concern` / `worried → concerned`
  - `suppressed → quiet`
  - `mist → fog` / `misty → foggy`
- Attempt 2（8 条，情绪强词替换）:
  - `furrow → expression` / `furrowed → thoughtful`
  - `grief → reflection` / `sorrow → quietness` / `anguish → stillness`
  - `suffering → quiet moment` / `pain → stillness` / `tears → gentle eyes`
- Attempt 3（9 条，兜底最激进）:
  - `dying → resting` / `death → stillness` / `dead → still`
  - `blood → mark` / `bloody → marked`
  - `violent → intense` / `violence → intensity`
  - `cry → gentle expression` / `crying → gentle`

POC shot_04 原 prompt（`elderly man ... furrow of quiet worry ... suppressed ... mist`）在 Attempt 1 即命中 4 处替换，与 POC Phase 3a 的 `comparison.html` 标注一致。

**NB2 fallback 实现（Founder Q3 决策）**

- fallback_callback 通过 closure 传回 `self.generate_shot_image(..., _seedream_fallback=True, ...)` 重入同一方法
- `_seedream_fallback=True` 触发 dispatcher 跳过 Seedream 分支，走 NB2 原生 pipeline
- sanitize 循环结束条件：命中 `InputTextSensitiveContentDetected` 3 次仍失败 → fallback / 非敏感错误（网络/5xx/格式）→ 直接 fallback 不消耗 sanitize 轮次
- fallback 结果 dict 注入 `seedream_info.used_fallback=True + fallback_reason + sanitize_attempts`，pipeline 日志可追踪

**验收清单**

| 项 | 期望 | 结果 |
|----|------|------|
| `app/config.py` 新增 `IMAGE_GEN_PROVIDER` | ✅ | ✅ 默认 `"nb2"` |
| `.env.example` 新增示例行 | ✅ | ✅ 实装 + 注释双份 |
| `app/services/seedream_generator.py` 新文件 | ✅ | ✅ 555 行 |
| `image_generator.py` dispatcher ≤ 15 行 | ≤ 15 | ✅ **7 行** |
| NB2 原逻辑零变化 | ✅ | ✅ 仅在 docstring 后加 7 行 if 分支 |
| pytest test_architecture 7/7 | ✅ | ✅ `7 passed in 0.04s` |
| import check 无 ImportError | ✅ | ✅ `from app.services import image_generator, seedream_generator` OK |
| `git diff --stat app/services/image_generator.py` | ≤ 15 行 | ✅ `7 +++++++` |

**🟡 重要架构澄清（需 PM 知悉，可能需后续派发）**

**dispatcher 目前只挂在 `generate_shot_image()` 入口（任务文案明确指定）**，但实际生产 Pipeline 不走这条路径：

- `pipeline_orchestrator.py:583` 调用的是 **`generate_shot_image_phase2_safe()`**，后者内部调用 `generate_shot_image_phase2()`（Phase 2.0 / B' prompt 格式）
- `generate_shot_image()`（Phase 1 legacy）目前全项目只有被测试和 R8 回归用，**生产 chapters.py / pipeline_orchestrator.py 均不调用它**
- 结果：本次改动**语义正确但在生产 Pipeline 不会触发 Seedream 分支**，`IMAGE_GEN_PROVIDER=seedream` 在生产环境下会被 ignore

**处理建议**（我不越权自行决定，等 PM 审查后派）:
- 选项 A：PM 派新任务把 dispatcher 同样加到 `generate_shot_image_phase2_safe()` 入口（估 +8 行，NB2 原逻辑同样零变化）— 推荐
- 选项 B：PM 评估后改派 pipeline_orchestrator.py 切换到 `generate_shot_image()` 路径（工作量大，需重新构建 B' prompt 和回归测试）— 不推荐
- 选项 C：保持现状，Seedream 路径只用于将来重构后的统一入口 — 不推荐，直接阻塞了 Founder 测试期省钱意图

我等 PM 审查后再决定是否补 dispatcher（如果是选项 A，再加 8 行就能让生产生效）。

**其他约束遵守**

- ✅ 没碰 storyboard_prompts.py / storyboard_service.py / reference_image_manager.py / scene_reference_manager.py
- ✅ 没碰 style_enforcer.py（@ai-ml 在改）
- ✅ 不改前端 / 不改 DB schema / 不改共享 MySQL
- ✅ 本次不跑真实角色一致性回归（按任务说明 @tester 负责）
- ✅ 代码只 import app/ + stdlib + certifi + PIL（requirements 已有）

**文档更新**
- ✅ TEAM_CHAT.md（本次报告）
- ✅ `backend-progress/current.md`（本条）
- ✅ `backend-progress/context-for-others.md`（Seedream 接入 context）

---

## 最新进展 [2026-04-24 18:20]

### ✅ TASK-SEEDREAM-POC Phase 3a — comparison.html shot_04 警告标注

**任务**: 在 `comparison.html` shot_04 区块加视觉警告，展示原 prompt 与 sanitized prompt 差异

**改动文件**: `test_output/manualtest/seedream_vs_nb2_2026-04-24/comparison.html` **1 个文件**

**Step 1 — ⚠️ 警告 badge** (行 160):
- 红色实心 badge（`background: #d32f2f`，白字）
- 文字: "⚠️ Prompt Sanitized — 火山方舟内容审查拦截，Seedream 实际用的 prompt 与 NB2 baseline 不同"

**Step 2 — 双 prompt 并排对照** (行 163-173):
- 左框（黄底橙边）: "原 prompt（NB2 baseline 用的 / R8 storyboard 原文）"，两处差异高亮（黄底）：
  - <span class="highlight-diff">elderly man</span>
  - <span class="highlight-diff">faint but legible furrow of quiet worry</span>
- 右框（浅红底橙边）: "Sanitized prompt（Seedream 实际送入 API 的）"，替换后的词高亮：
  - <span class="highlight-diff">older man</span>
  - <span class="highlight-diff">sense of quiet contemplation</span>
  - 底部附注拦截原因说明

**Step 3 — 其他 9 shots 展示不变**（未碰 shot_01~03、05~10 的任何行）

**Step 4 — 页面底部评分说明** (行 315-319):
- 橙色框（`#fff3e0`）注明 shot_04 不计入公平对比均分，理由说明 + 文档引用

**图片加载验证**: 10 张 Seedream 图 (`seedream/shot_01~10.png`) + 10 张 NB2 图 (`nb2_baseline/shot_01~10.png`) 路径未改，均可正常加载。

**Style 新增** (行 24-76): 6 个新 CSS 类（sanitized-badge / prompt-comparison / prompt-box / prompt-box-original / prompt-box-sanitized / prompt-box-label / highlight-diff / shot04-note），内联在 `<style>` 块中，无新依赖。

---

## 刚完成 [2026-04-24 17:05]

### 🔴 TASK-SEEDREAM-POC Step A-D 执行 — 新 blocker: ModelNotOpen（已解决）

**Step A** ✅ 改 env 变量名 `VOLCENGINE_API_KEY` → `ARK_API_KEY`（script 3 处 + doc 字符串）
**Step B** ✅ 执行脚本（10/10 shots，0 syntax error，0 中断）
**Step C** ✅ 内置 edge case 处理（downsample/retry/continue-on-error）
  - 降采样阈值 10 MB → 1024px，413/400 too large → 512px
  - 429/5xx → 指数退避 3s/5s/9s
  - 网络异常 → 2s/4s 退避
  - 每 shot 间隔 1s 软节流
  - 本次实际 payload 最大 4.3 MB，未触发降采样；404 不在重试列表（不可恢复错误）
**Step D** ✅ 产物齐全
  - `test_output/manualtest/seedream_vs_nb2_2026-04-24/seedream/` — **空（0 张）**
  - `.../nb2_baseline/shot_01~10.png` — 10 张（上轮已复制）
  - `.../logs/seedream_api_logs.json` — 10 条 404 记录（含 request_id）
  - `.../comparison.html` — 左列 10 个 FAILED 红块，右列 NB2 基线
  - `.../README.md` — 含 BLOCKER 说明 + 下一步操作指南

**新 Blocker（Ark API Key 鉴权通过，但模型未开通）**:

```json
{
  "error": {
    "code": "ModelNotOpen",
    "message": "Your account 2105093537 has not activated the model doubao-seedream-4-0-250828. Please activate the model service in the Ark Console.",
    "type": "Not Found"
  }
}
```

10/10 shots 全部触发，单次返回 ~0.3s，**无真实图片生成**，**无 API 计费**。

**下一步**（需 Founder 操作）:
1. 登录 https://console.volcengine.com/ark/
2. 「模型广场」→ 搜 `doubao-seedream-4-0` → 点「开通」（免费/按量付费均可）
3. 等 ~1 分钟服务生效后重跑 `python3 scripts/test_seedream_vs_nb2.py`

脚本已具备 production-grade edge case 处理，模型开通后无需改任何代码即可端到端跑通。

**验收状态**:
- ✅ 脚本 0 syntax error
- ❌ ≥ 8/10 success（实际 0/10，blocker 外部）
- ✅ 10 张 NB2 基线到位（新生图空）
- ✅ comparison.html 可本地打开
- ✅ README.md 含 4 项核心数据 + blocker 详情
- ✅ `pytest tests/test_architecture.py` 7/7 通过
- ✅ `git diff --stat app/` 空（0 生产代码修改）

---

## 刚完成

### 🟡 TASK-SEEDREAM-POC — Step 1-2 完成，Step 3 阻塞 [2026-04-24 15:40]

**任务**: Founder 决策 Seedream 4.0 vs NB2 10-shot 隔离对比（火山方舟/只传 fullbody/严格隔离）

**已完成**:

| Step | 内容 | 结果 |
|------|------|------|
| 1 | 火山方舟 Seedream 4.0 API 调研 | ✅ 锁定 endpoint/model ID/请求格式/多参考图机制 |
| 2 | 写独立测试脚本 `scripts/test_seedream_vs_nb2.py` | ✅ 360 行，零 app/ import，纯 urllib + base64 data URI |

**Step 3 阻塞根因**:

本地 `.env` 的 `VOLCENGINE_API_KEY` **不是**火山方舟 Ark API Key，而是 IAM Access Key ID（.env 注释明确：`VolcEngine 控制台 Access Key ID，供签名鉴权备用`）。实测 3 个候选 key 都返回 HTTP 401:

| 尝试 key | 错误 | 说明 |
|----------|------|------|
| `VOLCENGINE_API_KEY` (36字符 UUID 格式) | `AuthenticationError: The API key doesn't exist` | 不是 Ark key |
| `VOLCENGINE_ACCESS_KEY` (TTS 用) | `AuthenticationError: The API key format is incorrect` | 格式不符 |
| `VOLCENGINE_SECRET_KEY` | 同上 | 格式不符 |

**结论**: Ark 是独立产品线（`console.volcengine.com/ark/apiKey`），API Key 需要在 Ark 控制台单独创建，和 IAM/TTS 的 AK/SK 体系不同。

**已完成关键发现（Step 1 技术报告）**:
- **Endpoint**: `POST https://ark.cn-beijing.volces.com/api/v3/images/generations`
- **Model ID**: `doubao-seedream-4-0-250828`（Seedream 4.0，2025-08-28 build）
- **Auth**: `Authorization: Bearer $ARK_API_KEY`
- **Size**: `1664x2496`（2K 2:3 portrait，DEC-010 抖音标准）
- **多参考图机制**: `"image"` 字段，`string | string[]`，接受 **URL 或 base64 data URI**（最多 14 张）
- **响应**: `response_format: "b64_json" | "url"`，`data: [{b64_json|url, size}]`
- **价格**: 2K ~$0.03/张（第三方代理报价，官方需 Ark 控制台确认）

**产物（Step 2）**:
- `scripts/test_seedream_vs_nb2.py` - 360 行，零 app/ import，SSL certifi fix，读 R8 storyboard + screenplay，按 shot.character_direction.characters_visible + scene_id→location_id 匹配 fullbody 参考图，base64 inline 传给 Seedream，b64_json 响应回写 PNG，含 comparison.html + README + api_logs 生成

**产物目录**（空壳，待 Ark key 到位后补生图）:
```
test_output/manualtest/seedream_vs_nb2_2026-04-24/
├── seedream/          (空)
├── nb2_baseline/      (空)
├── logs/seedream_api_logs.json (10 shots 全 URLError SSL EOF / 401)
├── comparison.html    (占位：10 行，全 FAILED 状态)
└── README.md          (配置说明)
```

**0 生产代码修改**:
- ✅ `git diff app/` 空
- ✅ `git diff --stat` 无 app/ 行
- ✅ pytest test_architecture 7/7 PASS
- ✅ 未碰 🔴 警示文件

**等 PM**: 请 Founder 在 `console.volcengine.com/ark/apiKey` 创建 Ark API Key 并把值加到 `.env`（建议用 `ARK_API_KEY=` 前缀，避免和现有 VOLCENGINE_* 冲突）。脚本读环境变量 `VOLCENGINE_API_KEY`，后续可改为读 `ARK_API_KEY`（1 行改动，或直接复用 VOLCENGINE_API_KEY 变量名覆盖）。

---

### ✅ TASK-BUG-FIX-BATCH-1 Route B — Pipeline SKIP/BGM/credits 修复 + DB 清理 [2026-04-23 16:15]

**背景**: Founder 2026-04-23 本地跑 Pipeline 16 分钟发现 4 个 bug + chapter id=2 脏数据。PM 派 Route B（4 处代码 + DB 清理）。

**5 Step 改动**

| Step | 文件 | 行号 | 改动 |
|------|------|------|------|
| 1 | `app/services/job_manager.py` | L201-205 | checkpoint_callback 加类型判断：`isinstance(data, (dict, list))` 才 json.dumps，String/int/float 直接赋值 |
| 2 | `app/services/pipeline_orchestrator.py` | L721-728 | Stage 6 BGM 后新增 `await checkpoint_callback("credits_used", bgm_result.get("credits_used", 0))` |
| 3a | `app/services/pipeline_orchestrator.py` | L381-401 | SKIP 分支：`_run_stage5_skip_mode(..., project_id=project_id)` + 完成后重存 4_storyboard.json + 回调 `checkpoint_callback("storyboard_json", storyboard)` |
| 3b | `app/services/pipeline_orchestrator.py` | L872-944 | `_run_stage5_skip_mode` 接 `project_id` 参数，shot 循环内写 `shot["image_url"] = "/static/outputs/{uuid}/images/shot_NN.png"` 回 storyboard dict |
| 4 | `app/main.py` | L82-85 | 新增 `app.mount("/static/outputs", StaticFiles(directory=os.path.abspath("output")))` |
| 5 | DB chapter id=2 | — | 一次性 UPDATE：bgm_url 去引号 + 改 `/static/outputs/...` URL，bgm_meta_version 去引号，credits_used 0→10 |

**验收**

| 验收项 | 结果 |
|--------|------|
| pytest test_architecture | ✅ 7 passed in 0.04s |
| backend 启动无 `--reload` | ✅ 16:10:16 startup complete |
| /health | ✅ `{"status":"healthy"}` |
| /static/outputs/.../bgm_chapter0.mp3 | ✅ 200 audio/mpeg |
| /static/outputs/.../shot_01.png | ✅ 200 image/png |
| DB chapter id=2 | ✅ bgm_url 无引号 + credits_used=10 + bgm_meta_version='mixed' |

**额外风险**:
- 其他 chapter 可能也有 `"` 引号脏数据（根因修复前累积），建议 @tester 全表扫 `WHERE bgm_url LIKE '"%'`
- 新产出 chapter 的 `bgm_url` 仍是本地路径（music_generation_service 未改），前端仍需要处理协议不统一问题 — 待 PM 决策是否派发后续任务
- Pipeline 真实 e2e 未跑（任务标为可选，16 分钟 + LLM 成本）

**未碰**: 🔴 image_generator.py / storyboard_prompts.py / storyboard_service.py / reference_image_manager.py / scene_reference_manager.py；前端/VPS/.env/DB schema；Ben 侧 MySQL 数据。

---

### ✅ TASK-P0P1-LOGGING-FIX — 异常日志治理 [2026-04-23 11:30]

**背景**: Ben 在 VPS 踩 500 错误 (/api/projects/.../chapters/1/status)，但 docker logs 只剩 139 行，11:50 traceback 被 rotate 冲掉。PM 审查发现 3 处 P0 日志缺口 + image_generator.py 0 logger。Founder 批准全部处理。

**4 处改动实际行号**:

| # | 文件 | 位置 | 改动 |
|---|------|------|------|
| 1 (P0) | `app/services/pipeline_orchestrator.py` | L1074-1081 | 裸 `except:` → `except Exception as e: logger.exception(...)` + `pass` 保留原吞异常行为（forclaudeweb/prompt_quality_report.md 写入失败不阻塞主流程）|
| 2a (P0) | `app/api/chapters.py` | L498-501（import + try 包裹 async with）/ L630-657（asyncio.CancelledError + logger.exception + write DB + error_message=traceback[:10000]）| `generate_images_task` 强化异常处理 |
| 2b (P0) | `app/api/chapters.py` | L762-790（`regenerate_single_image_task` 的 CancelledError 透传 + logger.exception + 写失败 SceneImage 记录）|
| 2c (P0) | `app/api/chapters.py` | L1237-1262（`generate_audio_and_align_task` 的 CancelledError 透传 + logger.exception + error_message=traceback[:10000] + chapter.status=failed）|
| 3 (P0) | `app/api/chapters.py` | 9 个 GET 端点全部加 try/except: `/` (L58) / `/status` (L89) / `/story` (L163) / `/{chapter_number}` (L237) / `/images` (L352) / `/timeline` (L883) / `/audio` (L966) / `/voices` (L1007) / `/bgm` (L1571) | HTTPException 透传 + `logger.exception(...)` + 返 500 JSON `{"detail":"服务异常: {type}: {msg}"}` |
| 4 (P1) | `app/services/image_generator.py` | L3 加 `import logging`，L16 加 `logger = logging.getLogger("xuhua")`，65 处 print 机械转换：`❌/失败` → `logger.error`，`⚠️/跳过/Warning` → `logger.warning`，其余 → `logger.info` |

**执行方式**:
- P0-1: 手动 Edit（单点位置）
- P0-2/3: 手动 Edit 每个 endpoint 一次（避免破坏缩进）
- P1-4: Python 脚本批量扫描分类替换（`print(` → `logger.{level}(`，按行内 emoji/关键词分流），run 后做 1 次 syntax + 1 次 import 确认

**关键设计决策**:
- 3 个后台任务的 `asyncio.CancelledError` 独立 raise（用户主动取消不算 failed，保留 FastAPI 生命周期语义）
- 错误 traceback 切片 10000 字符写入 `chapter.error_message` + stage_message 400 字符，让 Ben 能直接在 DB 读到真实报错
- GET 端点的 try/except 是**最外层**包装，HTTPException 原样透传（404/400 等业务异常不被吞），其他异常统一 logger.exception 打 traceback 并返 500 含 type+msg

**验收结果**:

| 验收项 | 期望 | 结果 |
|--------|------|------|
| `grep -n "except:" app/services/pipeline_orchestrator.py` | 0 命中 | ✅ 0 |
| `grep -c "print(" app/services/image_generator.py` | ≤ 5 | ✅ **0** |
| `grep -c "logger\." app/services/image_generator.py` | ≥ 60 | ✅ **65** |
| `pytest tests/test_architecture.py -x -q` | 7 passed | ✅ **7 passed in 0.06s** |
| `python3 -c "from app.api import chapters; from app.services import image_generator, pipeline_orchestrator"` | 无 ImportError | ✅ OK |
| `curl http://localhost:8000/health` | healthy | ✅ `{"status":"healthy"}`（本地后端 shell `bxgmyw2yw` 自动热重载）|
| chapters.py GET 端点 try/except 包装 | ≥ `/status` `/story` `/storyboard` | ✅ 9 个 GET 端点全部包（含 /bgm /audio /timeline /voices /images）|
| start-generation asyncio.create_task wrapper | 有 | ⚠️ **N/A**（chapters.py 没有 `start-generation` 端点，实际用的是 FastAPI `BackgroundTasks.add_task`，3 个后台任务函数内部都已强化异常处理）|

**跳过真实图像生成回归测试**（Founder 批准）:
- image_generator.py 本次是 **纯机械 print → logger 转换**（0 行为变化）
- 未碰 `generate_image` / `generate_shot_image_phase2` / API 参数 / contents 数组 / prompt / 参考图传递
- pytest test_architecture 7 passed + import 检查通过 + backend /health healthy 已足够验证机械转换正确性

---

### ✅ TASK-8631-UNIFY — max_tokens 统一 16384 [2026-04-22 16:10]

**13 处 `max_tokens=8631 → 16384`**（5 个 Python 文件）：

| # | 文件 | 行 | 类型 |
|---|------|----|----|
| 1 | `character_designer.py` | 84 | Claude |
| 2 | `character_designer.py` | 105 | Gemini |
| 3 | `alignment_service.py` | 177 | Claude 视觉 |
| 4 | `alignment_service.py` | 193 | Gemini 视觉 |
| 5 | `alignment_service.py` | 234 | Claude 文本 |
| 6 | `alignment_service.py` | 250 | Gemini 文本 |
| 7 | `story_outline_generator.py` | 196 | Gemini fallback（补齐半改遗漏）|
| 8 | `storyboard_director.py` | 543 | 调用 |
| 9 | `storyboard_director.py` | 580 | 函数默认参 |
| 10 | `screenplay_writer.py` | 236 | 调用 |
| 11 | `screenplay_writer.py` | 663 | 函数默认参 |
| 12 | `screenplay_writer.py` | 790 | Gemini config |
| 13 | `screenplay_writer.py` | 800 | Claude |

**执行方式**: `sed -i '' 's/8631/16384/g'` 5 个文件批量替换（sed 不改变文件行号结构）。

**自我纠错 (诚实记录，不是自责)**:
- 上次 TASK-LLM-TEMP-AUDIT-FIX Step 7 汇报 **"14 处"** → PM 独立地毯式 grep 核对发现 **实际 13 处**（我数错了一处）
- 上次汇报 "story_outline_generator 已改 8631→16384" → **实际半改状态**（L178 Claude 已 16384 ✅，L196 Gemini fallback 仍 8631 ❌，遗漏）
- 本次 TASK-8631-UNIFY 已补齐 L196 并校对全量 13 处

**验收**:
- ✅ `grep -rn "8631" app/` 返回 0 结果（全 app/ 干净）
- ✅ `pytest tests/test_architecture.py -x -q` → 7 passed in 0.04s
- ✅ `curl http://localhost:8000/health` → `{"status":"healthy"}`（uvicorn --reload 自动热重载）

---

### ✅ TASK-LLM-TEMP-AUDIT-FIX — 全量 LLM 温度/上限审计修复 [2026-04-22 15:36]

**7 步改动全部落地**（6 个 Python 文件 + 1 项调查）：

| Step | 文件 | 关键改动 |
|------|------|----------|
| 1 | `alignment_service.py` L175, L231 | Claude `messages.create` × 2 → `temperature=0.2`（确定性对齐任务，与 Gemini 备用 0.2 对齐）|
| 2 | `shot_validator.py` L125 | Haiku `messages.create` → `temperature=0.2`（是/否判断任务低温稳定）|
| 3 | `app/api/utils.py` L8/L35/L55/L144/L163 | 加 types import + 4 处调用 → `temperature=0.2`（OCR + vision_analyze 识别型任务）|
| 4 | `story_generator.py` L303 | sync Claude `max_tokens` 8192→16384（与 async 对齐防截断）|
| 5 | `screenplay_writer.py` L697/L725/L787/L798 | Stage 3 主 Claude + 备 Gemini + _expand_narration 2 处 → `temperature=0.8`（创意任务显式化）|
| 6 | `storyboard_director.py` L614/L642 | Stage 4 主 Claude + 备 Gemini → `temperature=0.8`（运镜差异化需创意）|
| 7 | 多文件调查 | `max_tokens=8631` **结论: 历史遗留**（初始 commit 就存在，无注释说明，pre-git 状态不可追溯，2026-03-24 story_outline_generator 已改 16384，其他未同步）|

**8631 调查建议**: 统一为 16384（与 Stage 1/2 story_outline_generator、story_generator 对齐），但**本次 PR 不改**（token 上限独立决策需 Founder 批，建议写入 PENDING.md）

**验收**:
- ✅ `pytest tests/test_architecture.py` → 7 passed in 0.05s
- ✅ 6 个 Python 模块 import 检查通过（alignment_service / shot_validator / story_generator / screenplay_writer / storyboard_director / api/utils）
- ✅ `curl http://localhost:8000/health` → `{"status":"healthy"}` HTTP 200

**行号逐行对应（详见 TEAM_CHAT 完成报告）**

---

### ✅ Wave 3 Step 5 — Stage D BGM REST API (2026-04-21)

**文件**: `app/api/chapters.py` L1530-1913

| 端点 | 方法 | 路径 | 功能 | Credits |
|------|------|------|------|:----:|
| `get_bgm` | GET | `/{chapter_number}/bgm` | 读 bgm 信息（url/volume/meta/credits/exists）| — |
| `regenerate_bgm` | POST | `/{chapter_number}/bgm/regenerate` | 同 meta 重生 | 10 |
| `change_bgm_meta` | POST | `/{chapter_number}/bgm/change-meta` | mixed↔en 切换 | 5 |
| `update_bgm_volume` | PATCH | `/{chapter_number}/bgm/volume` | 仅改 DB 不重渲染 | — |

**关键设计**:
- regenerate/change-meta 用 `asyncio.to_thread(generate_bgm_for_chapter, ...)` 避免阻塞 event loop（service 同步调用 90-300s）
- `get_bgm` 包含 `bgm_exists`（os.path.isfile 本地路径检查）
- `PATCH volume` 校验 0.0-1.0（超范围 HTTP 400）
- 所有端点 Bearer token 认证（verify_user 与现有 shots 端点一致）
- 数据来源：outline 从 `project.confirmed_outline_json`，screenplay 从 `chapter.scenes_json`

**已知限制**:
- regenerate/change-meta 90-300s，前端需大 timeout 或后续改 async job 轮询
- `chapter` 无 `bgm_regen_count` 字段（regenerate 固定 regen_count=0）

---

### ✅ Wave 1 Step 1 — `story_music_extractor.py` (2026-04-21)

**路径**: `app/services/story_music_extractor.py`
**函数**: `extract_story_for_music(outline, screenplay, visual_style_hint, max_scenes=6) -> dict`
**返回 15 字段**: 14 meta-prompt 占位符 + visual_style_hint
**关键实现**:
- max_scenes 超限按 plot_point 优先级选取（inciting_incident → first_turn → midpoint → crisis → climax → resolution）
- 5 个 parity 风险全覆盖
- 空数据容错，类型注解 + docstring 完整

**PM 验证**: 3 个测试（正常 / max_scenes=3 / 空数据）全部 PASS

---

### ✅ Wave 1 Step 3 — `ffmpeg_post_processor.py` (2026-04-21)

**路径**: `app/services/ffmpeg_post_processor.py`
**函数**: `process_bgm(input, output, target_duration_sec, volume=1.0) -> dict` + `get_audio_duration(path) -> float`
**FFmpeg 一次性 filter 链**: atrim 切水印 + atrim 裁目标时长 + volume + afade 淡入淡出
**QA**: silencedetect (-30dB / 5s) + loudnorm LUFS

**PM 验证**: 处理年夜饭 V4 BGM → 180s 输出正确 + 静音检测 PASS
**🟡 已知 bug**: LUFS 检测返回 0.0 永远超范围（loudnorm 单 pass 只测 RMS 不输出 LUFS）。**归 Wave 2 启动时顺手修**（改用 `ebur128` filter 或两阶段 loudnorm）

---

### ✅ 方案 B Backend 部分 — 脚本加 clean_haiku_output() (2026-04-21)

**改动**: `scripts/test_haiku_music_prompt_languages.py`
- L346-364: 新增 `clean_haiku_output(text: str) -> str` 正则清理函数
- L341-343: `call_haiku()` 内部调用点
- L666-674: BGM prompt 超 974 字符打警告（不截断）

**清理覆盖**:
- markdown fence（```开头/结尾/行内）
- 非 `<quotes>` 的 XML/HTML 残留标签
- `<quotes>...</quotes>` 保留不动
- hardcoded 模式无副作用

**配合 @ai-ml v3.2**: meta-prompt 去掉"输出纯净规则"大段+ASCII 图，污染清理移到代码层

---

### ✅ TASK-MUSIC-LANG-AB-V2 Step 2 — 脚本加 --version 参数 (2026-04-20)

**文件**: `scripts/test_haiku_music_prompt_languages.py`
- 新增 `argparse --version v1|v2`（默认 v2）
- `load_meta_prompt(lang, version)` 按版本选文件
- v2 产出 `bgm_haiku_{lang}_v2.mp3` + `_v2_prompt.txt`，v1 向后兼容不覆盖
- SSL fix/Haiku/Mureka/narration_quotes 均未改

**PM 实测运行**: 3/3 v2 BGM 成功，长度硬约束（≤400 字符）起作用：
- en: 833→421 字符 (↓50%)
- cn: 265→196 字符 (↓26%)
- mixed: 855→506 字符 (↓41%, 仍超 400 但改善明显)

---

### ✅ TASK-MUSIC-LANG-AB Step 2 — Haiku+Mureka A/B/C 脚本 (2026-04-18)

**脚本**: `scripts/test_haiku_music_prompt_languages.py` (512 行)
**功能**: 从年夜饭 JSON 提取 14 占位符 → 填入 3 个 meta-prompt → 调 Haiku 4.5 API → 调 Mureka API → 产 3 套 BGM
**关键设计**:
- 占位符用 str.replace 链（避免 .format 吞 meta-prompt 里的 JSON 花括号）
- Mureka 用 urllib + ensure_ascii=False（EP-015）
- narration_quotes 硬编码 AI-ML 选定的 2 句金句
- meta-prompt Markdown 按 `## SYSTEM/USER PROMPT` 解析

**修复**: 首轮 Mureka 调用遭遇 Python 3.11 framework SSL 证书链错误，@backend 加 5 行 SSL fix（certifi.where() 做全局 default context）

**运行结果**: 3/3 成功
- en: Haiku 833 chars, Mureka 175s, 5.4M
- cn: Haiku 265 chars, Mureka 192s, 5.9M
- mixed: Haiku 855 chars, Mureka 172s, 5.3M

**产出文件**: `test_output/.../sq_upgrade_ab_test/20260304_113630/bgm_haiku_{en,cn,mixed}.mp3` + prompt.txt

---

### ✅ TASK-ENV-SETTINGS-SYNC-TEST — .env / Settings 漂移 CI 检查 (2026-04-18)

**背景**: TASK-SETTINGS-FIX 后续，防止未来再次漂移
**改动**: `tests/test_architecture.py` 新增 `test_env_example_matches_settings` (AST 解析避免 DB 副作用)
**白名单策略**: Settings-only 白名单（含 MUREKA_API_KEY 临时项 + TODO）；反向零豁免
**PM 验证**: 正常 PASS + 故意制造漂移时精准捕获 ✅
**副作用**: EP-016 防护状态 ❌→✅，防护率 53%→56%

---

### ✅ TASK-SETTINGS-FIX — Settings 类补齐 + .env 审计 (2026-04-18)

**根因**: `.env` 有 3 个字段未在 Settings 声明，PM 临时加 `extra = "ignore"` 绷带
**改动**: `app/config.py`:
- 补 `VOLCENGINE_API_KEY`, `VOLCENGINE_SECRET_KEY`（签名鉴权备用）
- 新增 `MUREKA_API_KEY`（Mureka AI 音乐生成）
- 删除 `extra = "ignore"`，恢复严格模式

**验证**: PM 实际重启 backend，严格模式下 `/health` 正常
**副作用**: EP-016 新增到 ERROR_PATTERNS.md
**已知缺口**: `.env.example` 缺 `MUREKA_API_KEY`，需 DevOps 补（非阻塞）

---

### ✅ TASK-PROMPT-B-PRIME — B' 为默认 Prompt 格式 (2026-04-14)

**改动文件**:
- `app/config.py` — 新增 `PROMPT_FORMAT: str = "b_prime"`
- `app/services/image_generator.py` — 新增 `_build_b_prime_prompt()` + `prompt_format` 参数

**实现**:
- 默认 B' 格式（盲测验证质量等价，省 46% token）
- A 格式保留：`PROMPT_FORMAT=legacy` 或 `prompt_format="legacy"` 切回
- B' 模式跳过 `StyleEnforcer.enforce_prompt()`（B' 自带风格块，避免重复）

### ✅ TASK-KI-FIX — 3 个 Shot 级 API 端点 (2026-04-14)

**改动文件**: `app/api/chapters.py`

| 端点 | 方法 | 路径 | 功能 |
|------|------|------|------|
| regenerate_shot | POST | `/{chapter_number}/shots/{shot_id}/regenerate` | 重新生成（SKIP 模式返回现有图片） |
| update_shot | PATCH | `/{chapter_number}/shots/{shot_id}` | 更新旁白/对话，写回 DB |
| delete_shot | DELETE | `/{chapter_number}/shots/{shot_id}` | 软删除（deleted: true） |

---

### ✅ TASK-MUREKA-BGM — Mureka API 纯音乐生成 (2026-04-16)

**任务**: 为"最后一投"故事生成 BGM，使用 AI-ML 写的 Post-Rock → Orchestral 合并版 Prompt

**调用详情**:
- Endpoint: `POST https://api.mureka.cn/v1/instrumental/generate`
- model: auto（自动选 mureka-9）
- n: 2（生成 2 首）
- 耗时: ~58s（succeeded）

**技术问题 & 解决**:
- curl 直接传中文引号 JSON 报 `Invalid JSON` → 改用 Python urllib + ensure_ascii=False 解决

**产出文件**:
- `test_output/manualtest/prompt_bubble/slamdunk_dialogue/bgm_01.mp3` (2:55, 5.36 MB)
- `test_output/manualtest/prompt_bubble/slamdunk_dialogue/bgm_02.mp3` (3:23, 6.20 MB)

---

### ✅ TASK-MUREKA-BGM-2 — "外公的秋梨膏" BGM 生成 (2026-04-16)

**任务**: 为"外公的秋梨膏"故事生成 BGM (n=1)，使用 AI-ML 写的 Chinese folk-acoustic 合并版 Prompt

**调用详情**:
- Endpoint: `POST https://api.mureka.cn/v1/instrumental/generate`
- model: `auto`（自动选 mureka-9）
- n: 1
- prompt: music_prompt.md 合并版（732 字符，含中英文）
- 耗时: ~83 秒（running → reviewing → succeeded）

**产出文件**:
- `test_output/manualtest/e2e_regression_r8/20260316_145613/story_A/20260316_145614/bgm_01.mp3`（7.17 MB，3分54秒）

**文档更新**:
- `music_prompt.md` 末尾追加"生成结果"表格

---

### ✅ TASK-MUREKA-BGM-3 — 4 个故事 BGM 批量生成 (2026-04-16)

**任务**: 为剩余 4 个故事生成 BGM (n=1)，使用 Python 脚本 `generate_bgm.py` 顺序调用

| # | 故事 | Task ID | 时长 | 文件大小 | API 耗时 |
|---|------|---------|------|---------|---------|
| 3 | 年夜饭上的战争 | 133510809518082 | ~2:58 | 5.5 MB | 133s |
| 4 | 拿铁上的告白 | 133511086538756 | ~2:52 | 5.2 MB | 133s |
| 5 | 墨痕 | 133511373848578 | ~3:25 | 6.3 MB | 118s |
| 6 | 终点站前的余温 | 133511616921601 | ~3:39 | 6.7 MB | 120s |

**产出文件**:
- `test_output/manualtest/sq_upgrade_ab_test/20260304_113630/bgm_01.mp3`
- `test_output/manualtest/cross_style_test/20260228_152134/bgm_01.mp3`
- `test_output/manualtest/e2e_regression_r4/20260310_155024/story_B/20260310_161426/bgm_01.mp3`
- `test_output/manualtest/phase2/20251231_181728/bgm_01.mp3`

---

## 待处理队列

- 无。等 Founder 试听 6 首 BGM 质量评估。

---

## ✅ TASK-MUREKA-PIPELINE-INTEGRATION Wave 2 — 三件事全部完成 (2026-04-18)

**状态**: ✅ Wave 2 全部完成

### Wave 2 Task 1 — LUFS bug 修复 (2026-04-18)

**文件**: `app/services/ffmpeg_post_processor.py`（修改 LUFS 检测段）
**修复**: `loudnorm=print_format=json` → `ebur128=peak=true`
- 原 bug: loudnorm 单 pass 只测 RMS，`input_i` 字段永远返回 0.0
- 修复: ebur128 正确实现 EBU R128，解析 `Integrated loudness: I: -XX.X LUFS`
- 保留 silencedetect 不动
- 支持 `-inf` 静音特殊值（记为 -99.0 dBLUFS）

### Wave 2 Task 2 — music_generation_service.py (2026-04-18)

**文件**: `app/services/music_generation_service.py`（新建）
**主函数**: `generate_bgm_for_chapter(chapter_id, project_id, outline, screenplay, output_dir, story_type, visual_style_hint, regen_count, bgm_volume, is_change_bgm) -> dict`

**Flow (8步)**:
1. `extract_story_for_music()` → 15 字段 story_data
2. `_select_meta_version(regen_count)` → meta_version
3. `_load_meta_prompt(meta_version)` → (system_prompt, user_prompt_template)
4. `_fill_placeholders(user_prompt_template, story_data)` → user_prompt
5. `_call_haiku_with_retry(system_prompt, user_prompt)` → bgm_prompt（Haiku 最多 3 次重试）
6. `_call_mureka(bgm_prompt, raw_mp3_path)` → {"task_id", "duration_ms"}（Mureka 最多 3 次重试）
7. `process_bgm(raw_mp3_path, output_mp3_path, target_duration_sec, bgm_volume)` → qa_result
8. 删除临时 raw mp3，返回结果 dict

**关键实现**:
- SSL certifi fix 在模块顶部全局应用
- Haiku system prompt 使用 `cache_control: {"type": "ephemeral"}`
- str.replace 链式填充（避免 .format() 花括号冲突）
- meta_version: regen=0 → "mixed"，regen=1 → "en"，regen≥2 → "mixed"（v3.2 finding: mixed > en）
- 目标时长: 快闪→60s，短篇→90s，中篇→180s，fallback→180s
- 积分 mock: 首次=10，换 BGM=5，regen=10

**已知限制**: 同步阻塞（Haiku+Mureka 约 90-300s），Wave 3 需 asyncio.to_thread 包裹

### Wave 2 Task 3 — Pipeline 接入 + DB schema (2026-04-18)

**文件 1**: `app/models/chapter.py`
- 新增 4 列: bgm_url (VARCHAR 500), bgm_volume (FLOAT DEFAULT 1.0), bgm_meta_version (VARCHAR 50), credits_used (INT DEFAULT 0)

**文件 2**: `alembic/versions/001_add_bgm_fields_to_chapters.py`（新建）
- Alembic migration，revision ID: 001_add_bgm_fields
- **@pm 请运行**: 需先 `alembic init alembic` + 配置 alembic.ini，然后 `alembic upgrade head`

**文件 3**: `app/services/pipeline_orchestrator.py`
- Stage 5 之后新增 Stage 6 BGM 生成块
- 完整 try/except 包裹：失败仅 logger.warning，不 raise，不阻塞 Pipeline
- story_type 从 target_duration_minutes 映射（≤1→快闪，≤2→短篇，>2→中篇）
- BGM 成功后通过 checkpoint_callback 写 bgm_url + bgm_meta_version 到 DB
- summary dict 新增 bgm_url + bgm_meta_version 字段

---

## 待处理队列

- @pm 需运行 alembic migration（先 alembic init + 配置 alembic.ini）
- Wave 3 Step 5: REST API 端点（/chapters/{id}/bgm，GET/POST/DELETE）
- Wave 3 Step 6: generate_bgm_for_chapter 异步化（asyncio.to_thread 包裹）
- Wave 3: meta-prompt 文件迁移到 app/prompts/music/（当前路径在 test_output 下）
