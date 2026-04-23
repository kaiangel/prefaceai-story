# Backend Agent - 给其他 Agent 的上下文

> **最后更新**: [2026-04-23 16:15]

---

## ✅ TASK-BUG-FIX-BATCH-1 Route B — Pipeline SKIP/BGM/credits 修复 + DB 清理 [2026-04-23 16:15]

**改动范围**: 3 个 Python 文件 + DB 一条 UPDATE
- `app/services/job_manager.py` L201-205（checkpoint_callback 类型判断）
- `app/services/pipeline_orchestrator.py` L381-401 / L721-728 / L872-944（SKIP + credits_used + image_url 写回）
- `app/main.py` L82-85（新增 `/static/outputs` StaticFiles mount → `./output/`）
- DB: chapter id=2 一条 UPDATE

**对其他 Agent 的影响**:

- **@frontend**: 现在 SKIP 模式（`SKIP_IMAGE_GENERATION=true`）生成的 chapter，`storyboard_json.shots[*].image_url` 字段会有值，格式 `/static/outputs/{project_uuid}/images/shot_NN.png`。前端预览页直接 `<img src={shot.image_url}>` 即可显示。本地 localhost:8000 和生产 Nginx 反代都适用。  
  同理，chapter id=2 的 `bgm_url` 已改成 `/static/outputs/.../bgm_chapter0.mp3`，可直接 `<audio src={chapter.bgm_url}>`。
- **@devops**: `/static/outputs` mount 对应 `./output/` 目录，VPS 部署时要确保 Docker volume 或 rsync 把 `output/` 目录带过去。否则 /static/outputs/*.png 会 404。**这是新增的静态路径，比原 /api/images/ 范围更广**。
- **@tester**: 
  - 建议跑一次全表扫：`SELECT id, bgm_url, bgm_meta_version FROM project_chapters WHERE bgm_url LIKE '"%' OR bgm_meta_version LIKE '"%'`，找出其他带引号的脏数据（根因修复前累积）
  - 建议 e2e 验证 SKIP 模式：创建新 project + 触发 Pipeline（SKIP_IMAGE_GENERATION=true）→ 查 chapter.storyboard_json 的 shots[].image_url 都有值 + curl 200
- **@ai-ml**: 不影响 prompt 工程，SKIP 模式仅影响图像生成环节
- **@pm**: Stage 5 SKIP 分支会重新 checkpoint storyboard_json（覆盖 Stage 4 旧版），这是期望的；但非 SKIP 模式（真实生图）目前**没有**把 image_url 写回 storyboard，后续是否也要统一行为待 PM 决策

**关键设计**:
- `_run_stage5_skip_mode` 签名新增 `project_id: Optional[str] = None` 参数，用来构造 URL 前缀（fallback 从 `project_dir` basename 反推）
- image_url 格式 `/static/outputs/{project_id}/images/shot_NN.png`（shot_id 2-digit padded）
- SKIP 完成后 `self._save_json(project_dir, "4_storyboard.json", storyboard)` 重写本地 JSON（非阻塞主流程）
- `checkpoint_callback("storyboard_json", storyboard)` 调用包 try/except，失败不中断 Pipeline

---

## ✅ TASK-P0P1-LOGGING-FIX — 异常日志治理 [2026-04-23 11:30]

**改动范围**: 3 个文件 / 4 处改动
- `app/services/pipeline_orchestrator.py` L1074-1081（消除裸 except）
- `app/services/image_generator.py`（65 处 print → logger，新增 `logger = logging.getLogger("xuhua")`）
- `app/api/chapters.py`（9 个 GET 端点加 try/except + 3 个后台任务强化异常处理）

**对其他 Agent 的影响**:

- **@tester / @pm**: 现在所有 chapters API 的 500 错误都会在 uvicorn 日志输出完整 traceback（`logger.exception`），不会再被 FastAPI 默认的 "Internal Server Error" 页面吞掉。response body 也会有 `{"detail":"服务异常: {ExceptionType}: {msg[:200]}"}`，前端/curl 能看到具体异常类型。Ben 以后踩 500 可以直接看返回 body 判断是 DB/KeyError/NPE 还是真正的业务错误。

- **@devops**: 
  - VPS 上的 uvicorn 输出现在会有大量 `logger.exception` 打出的 traceback，docker log rotate 不够激进的话会撑爆磁盘。本次 @devops 的 P1-2 任务（`docker/docker-compose.yml` 加 `logging.driver=json-file` + `max-size=50m` + `max-file=5`）必须跟上
  - `logger = logging.getLogger("xuhua")` 统一 namespace，方便 filter

- **@ai-ml**: image_generator.py 的 65 处 print 全部变 logger，`[ImageGenerator]` 前缀保留在 message 里。如果 AI-ML 之前有过"看 print 输出调试 prompt 工程"的习惯，现在应该看 uvicorn 日志的 logger.info 输出（依然有）。**纯机械转换无行为变化**。

- **@frontend**: 3 个后台任务现在失败时会写 `chapter.error_message = traceback[:10000]`（以前只存 `str(e)` 可能只有一行）。前端展示 chapter 错误时 UI 要能显示长 traceback 或做截断，避免直接全量渲染破坏布局。

**关键设计**:
- 3 个后台任务独立处理 `asyncio.CancelledError`（用户主动取消不算 failed，保留 FastAPI 生命周期语义）
- GET 端点 HTTPException 透传（404/400 等业务异常不被 500 吞）
- 其他异常统一 logger.exception + 返 500 JSON 含 type+msg

**发现的额外风险**:
- 任务描述里提到 `chapters.py` 有 `start-generation` 端点 + `asyncio.create_task(...)` — **实际没有**。chapters.py 用的是 FastAPI `BackgroundTasks.add_task(...)`（3 个后台任务：generate_images / regenerate_single_image / generate_audio_and_align）。本次按 FastAPI BackgroundTasks 语义处理，把 3 个函数内部的 `except Exception: print(...)` 全部强化为 `asyncio.CancelledError` 独立 + `logger.exception` 全打 traceback + 写 DB error_message。语义等价于 wrapper 方案。
- `regenerate_single_image_task` 原代码的 `except Exception: print(...)` 不写 DB（失败不可见），本次新增失败时写一条 `SceneImage(error_message=..., is_active=True)`，让 GET /images 能看到 failed 记录。这是行为改动但符合任务意图（让真实错误可见）。

---

## ✅ TASK-8631-UNIFY — max_tokens 统一 16384 [2026-04-22 16:10]

**改动范围**: 5 个 Python 文件（character_designer / alignment_service / story_outline_generator / storyboard_director / screenplay_writer），共 13 处 `max_tokens=8631` 全部改为 `max_tokens=16384`。

**对其他 Agent 的影响**:
- **@ai-ml**: Stage 1-4 全部 LLM 调用（主 Claude + 备 Gemini）max_tokens 统一 16384，长故事/多角色/复杂剧本的输出不再有截断风险（原 8631 容易截断）。prompt 设计时可假设输出上限稳定 16K
- **@tester**: 基线统一后，E2E 测试更稳定（原混用 8631/16384 两个上限容易在边界用例出非确定性截断）。如触发黄金断言测试，可能需 re-baseline
- **@pm**: 上次审计（TASK-LLM-TEMP-AUDIT-FIX Step 7）记入 PENDING 的 "统一 16384" 建议，本次已全部执行完毕，可从 PENDING 标记为完成

**自我纠错 (诚实记录)**:
- 上次汇报 `8631` **14 处** → 实际 **13 处**（PM 独立地毯式核对发现偏差）
- 上次汇报 `story_outline_generator.py` **已改** → 实际 **半改状态**（L178 已 16384，L196 Gemini fallback 仍 8631），本次 TASK-8631-UNIFY 补齐
- 教训：调查类任务（grep 计数 / 多行改动覆盖度）汇报前应二次核对，不仅靠心算数行。future Agent 复盘时可参考此纠错链

**当前 max_tokens 基线** (全 Stage 1-4 + alignment + character_designer):
| 位置 | max_tokens |
|------|-----------:|
| Claude Sonnet 4.6 主模型 | 16384 |
| Gemini 备用 fallback | 16384 |
| sync Claude (story_generator L303) | 16384（TASK-LLM-TEMP-AUDIT-FIX Step 4 已改）|

---

## ✅ TASK-LLM-TEMP-AUDIT-FIX — LLM 调用参数统一 [2026-04-22 15:36]

**影响范围**：Stage 1-4 LLM 调用 + vision_analyze + OCR + shot_validator + alignment_service

**对其他 Agent 的影响**：
- **@ai-ml**: Stage 3/4 主+备模型 temperature 现在显式=0.8（创意任务不再依赖模型默认值，主备一致）。若再做 prompt 质量审查，基线已变（从"默认值参差"变成"显式 0.8"）
- **@tester**: 旧 E2E 测试结果可能轻微变化（Stage 3/4 创意温度可能从 1.0 降到 0.8，或从无显式提升到 0.8；Haiku/alignment 从默认 1.0 降到 0.2 会更稳定）。若触发相对黄金断言测试，可能需要重新 baseline
- **@pm**: 8631 max_tokens 历史遗留已确认，建议写入 PENDING（统一为 16384，与 story_generator/story_outline_generator 对齐）

**当前显式温度基线**：
| 场景 | 温度 | 理由 |
|------|------|------|
| OCR / vision_analyze / shot_validator / alignment_service | 0.2 | 识别/判断/对齐确定性任务 |
| Stage 3 screenplay_writer | 0.8 | 剧本创意任务 |
| Stage 4 storyboard_director | 0.8 | 运镜差异化创意任务 |
| story_generator / story_outline_generator / character_designer | 未改（保持原状）| 不在本次审计范围 |

---

## ✅ Wave 3 Step 5 — Stage D BGM REST API (2026-04-21)

**路径**: `/api/projects/{project_id}/chapters/{chapter_number}/bgm`

| 端点 | 方法 | 用途 |
|-----|------|------|
| GET `/bgm` | 读 | 返回 bgm_url/volume/meta_version/credits/bgm_exists |
| POST `/bgm/regenerate` | 重生 | credits += 10，同 meta 重跑（async to_thread）|
| POST `/bgm/change-meta` | 换版本 | credits += 5，mixed↔en 切换（async to_thread）|
| PATCH `/bgm/volume` | 音量 | 仅 DB 写入，Stage E 交付时 FFmpeg 应用 |

Bearer token 认证一致。@Frontend 按此 API 契约开发（Step 6 已完成）

## ✅ Wave 2 完成 — music_generation_service + orchestrator + DB schema (2026-04-21)

- **LUFS 修复**: `ffmpeg_post_processor.py` 改用 `ebur128` filter（PM 实测 -15.5 dBLUFS 在范围内）
- **新服务**: `app/services/music_generation_service.py`
  - `generate_bgm_for_chapter(chapter_id, project_id, outline, screenplay, output_dir, story_type, visual_style_hint, regen_count, bgm_volume, is_change_bgm) -> dict`
  - regen_count 映射: 0→mixed（首选），1→en（备选），2+→mixed（回到最优）
  - 完整 8 步 flow，prompt cache + SSL fix
  - **已知限制**: 同步阻塞 ~90-300s，Wave 3 REST API 层需用 asyncio.to_thread 包装
- **Chapter model 加 4 列**: `bgm_url` / `bgm_volume` / `bgm_meta_version` / `credits_used`
- **Alembic migration**: `alembic/versions/001_add_bgm_fields_to_chapters.py`（项目 alembic 未初始化，需 Ben/DevOps 处理 MySQL schema 变更）
- **orchestrator 接入**: Stage 5 完成后加 Stage 6 BGM 生成（try/except 包裹，失败不卡 Pipeline）
- **PM E2E 验证**: 年夜饭故事跑通，Mureka task 134387356336130，BGM 成功生成
- **PM 修 1 行 URL typo**: `MUREKA_QUERY_URL_TPL` 少 `/query/` 已修

## ✅ Wave 1 Step 1 — story_music_extractor.py (2026-04-21)

- `app/services/story_music_extractor.py`
- `extract_story_for_music(outline, screenplay, visual_style_hint, max_scenes=6) -> dict`
- 15 字段返回（14 meta-prompt 占位符 + visual_style_hint）
- **Wave 2 Step 2 的 music_generation_service.py 要用这个函数**

## ✅ Wave 1 Step 3 — ffmpeg_post_processor.py (2026-04-21)

- `app/services/ffmpeg_post_processor.py`
- `process_bgm(input, output, target_duration_sec, volume=1.0) -> dict`
- 切水印 + 裁剪 + 音量 + 淡入淡出 + QA 静音检测
- 🟡 **LUFS 检测有 bug**，Wave 2 启动时顺手修（5 行代码用 ebur128 filter）
- **Wave 2 Step 2 的 music_generation_service.py 要用这个函数**

## ✅ clean_haiku_output() 输出清理 (2026-04-21)

- `scripts/test_haiku_music_prompt_languages.py` 新增 `clean_haiku_output()` 函数
- 清理 Haiku 输出里的 markdown fence + 非 `<quotes>` 的 XML 标签
- `call_haiku()` 每次返回前自动调用
- BGM prompt 超 974 字符打警告（近 Mureka 1024 上限）
- **生产集成时复用**：clean 函数可提取到 utility module

## ✅ TASK-MUSIC-LANG-AB-V2 Step 2 — 脚本加 --version 参数 (2026-04-20)

- `scripts/test_haiku_music_prompt_languages.py --version v1|v2`（默认 v2）
- v2 读 `meta_{lang}_v2.md`，产出 `bgm_haiku_{lang}_v2.mp3`
- v1 原命名保留向后兼容
- PM 已运行 v2，3/3 BGM 成功

## ✅ TASK-MUSIC-LANG-AB Step 2 — Haiku+Mureka 集成脚本 (2026-04-18)

- `scripts/test_haiku_music_prompt_languages.py`
- 流程：extract_story_data → load_meta_prompt → fill_placeholders → call_haiku → call_mureka
- 用 settings.ANTHROPIC_API_KEY + settings.MUREKA_API_KEY（TASK-SETTINGS-FIX 补齐的）
- SSL fix 用 `ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())`
- **未来 Pipeline 集成可直接复用**：`call_haiku` + `call_mureka` 两个函数可独立调用

## ✅ TASK-ENV-SETTINGS-SYNC-TEST — CI 漂移检查 (2026-04-18)

- `tests/test_architecture.py::test_env_example_matches_settings`
- 双向对比 `.env.example` 和 `Settings` 类字段，AST 解析避免 DB 连接
- 任何一侧有对方没有的字段 → 测试失败（PreCommit/PrePush 自动触发）
- MUREKA_API_KEY 在临时白名单，Mureka 集成 Pipeline 时必须移除

## ✅ TASK-SETTINGS-FIX — Settings 类补齐 + 严格模式恢复 (2026-04-18)

- `app/config.py` 补充 `VOLCENGINE_API_KEY`、`VOLCENGINE_SECRET_KEY`、`MUREKA_API_KEY`
- 删除 `extra = "ignore"`，恢复 Pydantic 严格模式
- `settings.MUREKA_API_KEY` 现在可安全引用（Pipeline 集成 Mureka 时直接用）
- EP-016 已记录到 `.team-brain/knowledge/ERROR_PATTERNS.md`
- 以后往 `.env` 加新字段必须同步在 Settings 类声明，否则启动报错

---

## ✅ TASK-MUREKA-BGM 系列 — 6 个故事 BGM 生成 (2026-04-16)

3 轮 Mureka API 调用，共生成 7 个 mp3 文件（story 1 用了 n=2，后续全部 n=1）。

| # | 故事 | Task ID | 时长 | 文件 |
|---|------|---------|------|------|
| 1a | 最后一投 | 133491079708673 | 2:55 | `slamdunk_dialogue/bgm_01.mp3` (5.4M) |
| 1b | 最后一投(备选) | 同上 | 3:23 | `slamdunk_dialogue/bgm_02.mp3` (6.2M) |
| 2 | 外公的秋梨膏 | 133495221583873 | 3:54 | `e2e_regression_r8/.../bgm_01.mp3` (7.2M) |
| 3 | 年夜饭上的战争 | 133510809518082 | 2:58 | `sq_upgrade_ab_test/.../bgm_01.mp3` (5.5M) |
| 4 | 拿铁上的告白 | 133511086538756 | 2:52 | `cross_style_test/.../bgm_01.mp3` (5.2M) |
| 5 | 墨痕 | 133511373848578 | 3:25 | `e2e_regression_r4/.../bgm_01.mp3` (6.3M) |
| 6 | 终点站前的余温 | 133511616921601 | 3:39 | `phase2/.../bgm_01.mp3` (6.7M) |

**技术要点**:
- 模型: mureka-9 (auto)
- curl 传含中文 JSON 报错 → 用 Python urllib + `ensure_ascii=False` 解决 (EP-015)
- n 必须设为 1（n=2 按次计费，浪费成本）
- 生成脚本: `generate_bgm.py`（4 首批量生成用）

---

## ✅ TASK-STAGED-V2 — Haiku 集成到 regenerate 端点 (2026-04-14)

- regenerate 端点 API 契约更新：
  - Body (可选): `{ "adjustment_intent": "让她笑" }`
  - 返回新增: `prompt_modified: bool`, `modified_prompt_preview: str | null`
- 有 intent: Haiku 4.5 改 image_prompt → 写回 DB → 生图（或 SKIP 返回现有图片）
- 无 intent: 原 prompt re-roll
- Haiku 修改持久化：写回 storyboard_json
- 错误处理：Haiku 失败 fallback 到原始 prompt，不阻塞

---

## ✅ TASK-PROMPT-B-PRIME — B' 默认格式 (2026-04-14)

- `image_generator.py` 的 `generate_shot_image_phase2()` 新增 `prompt_format` 参数
- 默认 `"b_prime"`（省 46% token，盲测验证质量等价）
- `"legacy"` 切回 A 格式（全部旧代码保留）
- 环境变量 `PROMPT_FORMAT=b_prime|legacy` 可全局切换
- B' 模式跳过 `StyleEnforcer.enforce_prompt()`（B' 自带风格块）

## ✅ TASK-KI-FIX — 3 个 Shot 级 API 端点 (2026-04-14)

**@Frontend 需要的 API 契约**:

### POST `/{chapter_number}/shots/{shot_id}/regenerate`

请求: 无 body（或 `{ "adjustment_intent": "让她笑" }`）
响应:
```json
{
  "status": "completed",
  "shot_id": 1,
  "imageUrl": "/images/shot_01.png",
  "skipped": true,
  "message": "..."
}
```

### PATCH `/{chapter_number}/shots/{shot_id}`

请求:
```json
{
  "narration_segment": "新的旁白文字",
  "chinese_text": "新的对话文字"
}
```
响应:
```json
{
  "status": "updated",
  "shot_id": 1,
  "updated_fields": ["narration_segment"],
  "shot": { ... }
}
```

### DELETE `/{chapter_number}/shots/{shot_id}`

请求: 无 body
响应:
```json
{
  "status": "deleted",
  "shot_id": 1,
  "message": "Shot 1 已标记为删除"
}
```

**通用**: 所有端点需 Authorization header（Bearer token），路由前缀 `/api/projects/{project_id}/chapters/`

---

## 之前的工作

### ✅ R6 Backend (2026-04-13)

- R6-5: max_wait 300→1800（30 分钟）
- R6-6: 有自定义风格时日志显示 `Style: custom (display_name)`
- R6-1b: mood 更新顶层字段
- R6-2b: 删除 selected_ending 替换 plot_point 逻辑

### ✅ TASK-HE-BACKEND-1 — Pipeline Schema 验证 (2026-04-14)

- `app/services/pipeline_schemas.py` — Pydantic 验证 characters + shots
- Stage 2→3 + Stage 4→5 验证调用已嵌入 pipeline_orchestrator.py
- image_prompt 中文比例检测 validator（>15% 拒绝）
