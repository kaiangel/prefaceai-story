# Backend Agent - 给其他 Agent 的上下文

> **最后更新**: 2026-04-18（PM 代更新）

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
