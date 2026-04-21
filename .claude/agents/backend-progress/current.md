# Backend Agent - 当前任务

> **最后更新**: 2026-04-21（PM 代更新）
> **状态**: ✅ Wave 2+3 完成 — music_gen_service + orchestrator + BGM REST API 全部就绪（PM E2E 年夜饭 PASS）

---

## 刚完成

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
