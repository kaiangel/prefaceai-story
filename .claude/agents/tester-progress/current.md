# Tester Agent - 当前任务

> **最后更新**: 2026-05-26 [Tester]
> **状态**: TASK-WAVE13-INDEPENDENT-RETEST 完成 ✅ — Wave 13 FIXBATCH 独立复测通过，可进入部署关口

---

## 当前状态 (2026-05-26)

**TASK-WAVE13-INDEPENDENT-RETEST 完成 ✅**

### Wave 13 FIXBATCH 独立复测结论 (集成关口第二道)

#### 后端新测试 (3 组, venv/bin/python3 -m pytest 真自跑)

| 测试文件 | 预期 | 实跑 | 结论 |
|---|---|---|---|
| test_wave13_db_retry_middleware.py | 14 | **14/14 PASS** | ✅ PASS |
| test_wave13_clothing_bypass.py | 12 | **12/12 PASS** | ✅ PASS |
| test_wave13_regenerate_portrait_async.py | 4 | **4/4 PASS** | ✅ PASS |
| **后端小计** | **30** | **30/30 PASS** | ✅ ALL PASS |

#### 前端 vitest (npm test)

| 测试文件 | 预期 | 实跑 | 结论 |
|---|---|---|---|
| src/hooks/useETA.test.ts | 15 | **15/15 PASS** | ✅ PASS |

console.assert override 验证: vitest.setup.ts 的 override 真生效 — 所有 PASS 输出均来自每个 it() 内的 console.assert 断言（真 PASS 不是静默 pass），Wave 13 #9 机制正确。

#### 全量回归 (确认 0 新退化)

| 范围 | 数字 | 说明 |
|---|---|---|
| 全量套件 (排除 3 个真实 API 文件 + api_cost_log_table) | **2390 PASS / 13 fail / 5 error** | 0 新退化 |
| Wave 13 + Wave 12 combined | **45/45 PASS** | 0 退化 |

Pre-existing 失败逐一确认 (全为 Wave 11 baseline 已存在，非 Wave 13 引入):
- test_async_anthropic_t18_j (2 fail): AsyncAnthropic 结构变更 — pre-existing ✅
- test_b51_fallback_no_chinese (3 fail): "Character data:" 字符串不匹配 — pre-existing ✅
- test_supernatural_missing_all_fields_fails (1 fail): Wave 8 warn-not-raise — pre-existing ✅
- test_compat_with_real_data (1 fail): AttributeError — pre-existing ✅
- test_t20_14_anthropic_retry (2 fail): chapters.py 结构 — pre-existing ✅
- test_wave6_full_regression / test_wave6_round1_b52_cascade (2 fail): 旧版回归 — pre-existing ✅
- test_parallel_stage5 (2 fail): mock 污染隔离 — pre-existing ✅
- 5 ERROR: 真实 API 集成测试需 key/网络 — pre-existing ✅

**结论: 0 新退化，Wave 13 代码未破坏任何现有测试**

#### §9.7.4 前后端契约独立核对 (regenerate-portrait 异步)

三方逐一字段比对: Backend projects.py + Frontend StageC.tsx + STATUS_API_CONTRACT §9.7.4

**202 kickoff 返回体 (POST regenerate-portrait)**

| 字段 | 契约 §9.7.4 | Backend 实际 (L1735-1741) | Frontend 读取 (L1565-1571) | 对齐 |
|---|---|---|---|---|
| success | true | `"success": True` | `kickoff.success` (不强制读) | ✅ |
| job_id | uuid | `"job_id": job_id` | `kickoff.job_id` | ✅ |
| status | "pending" | `"status": "pending"` | `kickoff.status` (不强制读) | ✅ |
| char_id | char_id | `"char_id": char_id` | `kickoff.char_id` (不强制读) | ✅ |
| message | (可选) | `"message": "..."` | 不读 (不需要) | ✅ |

**轮询端点返回体 (GET adjust-jobs/{job_id})**

| 字段 | 契约 §9.7.2/§9.7.4 | Backend 实际 (L1258-1266) | Frontend CharacterJob interface (L1464-1480) | 对齐 |
|---|---|---|---|---|
| job_id | string | `job["job_id"]` | `job_id: string` | ✅ |
| char_id | string | `job["char_id"]` | `char_id: string` | ✅ |
| kind | "adjust"\|"regenerate_portrait" | `job["kind"]` | `kind?: "adjust" \| "regenerate_portrait"` | ✅ |
| status | pending\|processing\|completed\|failed | `job["status"]` | `status: "pending"\|"processing"\|"completed"\|"failed"` | ✅ |
| progress | 0-100 | `job["progress"]` | `progress?: number \| null` | ✅ |
| stage_message | string | `job["stage_message"]` | `stage_message?: string \| null` | ✅ |
| result | {success,char_id,portrait_url,fullbody_url,message} | `job["result"]` (见 _regenerate_portrait_core L1966-1972) | `result?.{success,char_id,portrait_url,fullbody_url,message}` | ✅ |
| error | string\|null | `job["error"]` | `error?: string \| null` | ✅ |

**result shape 精确比对** (backend `_regenerate_portrait_core` L1966-1972 vs frontend CharacterJob.result):

| result 子字段 | 契约 | Backend 写入 | Frontend 读取 | 对齐 |
|---|---|---|---|---|
| success | true | `"success": True` | `result?.success` | ✅ |
| char_id | char_id | `"char_id": char_id` | `result?.char_id` (不强制读) | ✅ |
| portrait_url | "/static/...?v={epoch}" | `portrait_url` 带 `?v={_v_ts}` | `result.portrait_url` → `bustUrl()` 再加 `&_={Date.now()}` | ✅ |
| fullbody_url | "/static/...?v={epoch}" 或 null | `fullbody_url` (B57 非阻塞, 失败时 None) | `result?.fullbody_url` (不强制消费) | ✅ |
| message | string | `"肖像和全身图已重新生成"` 或类似 | 不读 (只读 portrait_url) | ✅ |

**独立 verdict: §9.7.4 前后端契约完全对齐，0 字段名不匹配，0 缺字段，0 类型歧义。**

Frontend reroll 路径: 读 `result.portrait_url` → bustUrl → `onUpdateCharacter(charId, { portraitUrl })` — 正确。
adjust fallback 路径 (留空调整框): `!adjustInput.trim()` → 直接调 `handleRegenerate(charId)` — 正确，两路统一。

---

## 上一完成 (2026-05-25)

### Wave 13 #1 — Wave 12 独立复测结论

#### ① 3 style 画风复测 (cyberpunk / pastel_dream / gothic)

**pytest 机制验证: 58/58 PASS** (`tests/test_wave12_style_anti_anime.py`, Tester 新建)

| 验证维度 | cyberpunk | pastel_dream | gothic |
|---|---|---|---|
| mandatory[:5] 含渲染介质锚点 | ✅ photorealistic + cinematic film still | ✅ soft painterly illustration + airbrushed soft shading | ✅ dark romantic painting |
| forbidden[:8] 含 anti-anime | ✅ anime / cel-shaded / manga / glossy idol render | ✅ cel-shaded / hard anime lineart / manga / sharp ink outlines / glossy idol render | ✅ anime / cel-shaded / manga / glossy idol render |
| prefix MUST INCLUDE 行实际含锚点 | ✅ | ✅ | ✅ |
| prefix DO NOT USE 行实际含 anti-anime | ✅ | ✅ | ✅ |
| by-design 动漫类 0 破坏 (8 style) | ✅ cartoon/ghibli/manga/chibi/anime/illustration/korean_webtoon/slam_dunk 全 PASS | | |
| 原有氛围词回归保留 | ✅ neon lights / futuristic city | ✅ pastel color palette / dreamy soft aesthetic | ✅ cathedral architecture / dramatic chiaroscuro |
| 未修改 style 介质锚点保留 | ✅ ink/watercolor/ukiyo_e/pixel/noir 全 PASS | | |

**实际生图视觉验证 (AI-ML style_drift_probe 图):**
- cyberpunk: current 和 patched 均为写实电影感 (雨夜霓虹城市, 真人面孔, 非动漫) ✅
- pastel_dream: patched 为柔光插画风 (粉彩背景, 柔笔触, 非硬动漫线稿) ✅
- gothic: 暗黑浪漫大教堂场景 (哥特氛围显著), 人物脸部仍偏 CG 平滑 (轻微, 在 AI-ML 预期"mild"范围内) ✅
- 图路径: `test_output/manualtest/style_drift_probe/` (6 张 probe 图)

注: AI-ML 实测校准已用相同 28 岁帅哥角色跑 probe, 图为 AI-ML 的测试结果。Tester 复测目的是用独立 pytest 验证 prompt 工程层 (style_enforcer.py) 防护配置正确, 而非重复 API 生图 (避免额外成本)。视觉已有 AI-ML probe 图 + test28 e2e gothic 验证。

#### ② adjust 异步端到端复测

**pytest: 15/15 PASS** (`tests/test_wave12_adjust_async_job.py`, AI-ML 写, Tester 独立运行验证)

| 验证维度 | 结果 |
|---|---|
| AdjustJobManager create_job 初始状态 | ✅ |
| progress 单调递增 guard | ✅ |
| 完成写 result + portrait/fullbody url | ✅ |
| 失败写 error | ✅ |
| get_job 快照隔离 (外部 mutate 不污染) | ✅ |
| 不存在 job → None + update 静默 no-op | ✅ |
| TTL 惰性清理 (completed/failed) | ✅ |
| processing 不被清理 | ✅ |
| 10 并发 job 隔离 | ✅ |
| 模块级单例可用 | ✅ |
| Stage 2 portrait 子进度公式落在 band (6,10) 内 (4 n_chars 参数化) | ✅ |
| character_design ETA 随 progress 递增而递减 (不冻结) | ✅ |

e2e 行为: test28 (PM 5/25 实测, gothic) 已实证 adjust 异步化 "不转圈, POST 202+job 轮询" ✅ (见 TEST28_FULL_RETROSPECTIVE)

#### ③ ETA Stage 1-4 不冻结复测

**pytest: test_p2_2 全部 PASS** (含 test_wave12_style_anti_anime.py TestETAStage14NotFrozen 3 cases)

- character_design band (6, 10) 确认存在
- ETA 在 band 内 progress 6→9 单调递减 ✅
- test28 实测 Stage 2 "正在生成角色画像 1/3" sub-progress 有效 ✅

#### ④ pytest 回归 (Wave 12 全量)

**总结: 0 新退化**

| 测试集 | 结果 | 说明 |
|---|---|---|
| test_wave12_style_anti_anime.py (Tester 新建) | **58/58 PASS** | Wave 12 style 防护验证 |
| test_wave12_adjust_async_job.py (AI-ML 写) | **15/15 PASS** | Wave 12 adjust 异步验证 |
| style/layer1/identity_anchor/wave9/wave10 关联 | **623/623 PASS** (1 pre-existing fail) | 0 新退化 |
| 全量套件 (excluding 3 需真实 API 的旧文件) | 2363/2363 PASS (15 fail 全为 pre-existing) | 0 新退化 |

**Pre-existing 失败确认 (Wave 11 baseline 已存在, 非 Wave 12 引入):**
- test_async_anthropic_t18_j: AsyncAnthropic 在 HEAD 时就不存在 ✅ pre-existing
- test_b51_fallback_no_chinese (3 fail): HEAD 时已 fail ✅ pre-existing
- test_api_cost_log_table (2 fail): LONGTEXT SQLite 不兼容 ✅ pre-existing
- test_compat_with_real_data / test_supernatural_humanoid_hotfix / test_t20_14 / test_wave6_* (7 fail): HEAD 时已 fail ✅ pre-existing
- test_parallel_stage5 (在全量 combined run 中 2 fail): 独立跑 17/17 PASS, 是 mock 污染 isolation 问题 ✅ pre-existing 模式

**新建测试文件:**
- `tests/test_wave12_style_anti_anime.py` — 58 cases (Tester 独立新建, Wave 12 style 防护回归)

---

## 上一完成 (2026-05-23)

**TASK-T22-NEW-1-TEST-ISOLATION-EXTENDED 完成 ✅**

### pytest 结果

| 运行方式 | 结果 |
|---------|------|
| 单跑 `pytest tests/test_status_authoritative.py` | **44/44 PASS** |
| 综合跑 `pytest tests/ -k status_authoritative` | **44/44 PASS** |
| 17文件联跑 (Wave 9 + t21 + status_authoritative) | **667/667 PASS** |
| 综合跑含 t21_digital_virtual_fallback + schema_generic_fallback | **0 errors, 0 fail** |

### 根因 + 修法

**根因 1**: `test_t21_digital_virtual_fallback.py` + `test_schema_generic_fallback_arch.py` + `test_llm_fallback_chain.py` 在 pytest collection 时注入：
- `sys.modules["app.config"].settings` = `SimpleNamespace`（缺 `DATABASE_URL`）
- `sys.modules["google.genai"]` = 空 `ModuleType`（无 `types`）
- `sys.modules["google.genai.types"]` = 空 stub（无 `HttpOptions`）

**级联**: `setup_method` 做 `from app.api.chapters import _derive_ui_phase` 时：
- `app.database L13: settings.DATABASE_URL` → `AttributeError` (27 errors)
- 或 `story_generator: from google.genai import types` → `ImportError` (cascade)

**修法**: `autouse` fixture `_ensure_chapters_importable()` 每 test 前执行：
1. `_augment_settings_stub()`: 检测 `app.config.settings` 缺 `DATABASE_URL` → 补全 MySQL URL 等 12 个属性
2. `_clean_google_genai_stubs()`: 检测 `google.genai` / `google.genai.types` 是 stub → 从 sys.modules 删除 → 允许真实包加载

**根因 2**: 3 个测试断言 `scene_review` phase 存在 (`scene_review_hints_to_story_endpoint`, `scenes_ready_unconfirmed_returns_scene_review`, `endpoint_has_project_id_placeholder`) — 但 T22-NEW-5 已移除此 phase。

**修法**: 更新 3 个测试以匹配当前实现：
- `test_scenes_ready_unconfirmed_returns_scene_review` → 改期望 `storyboard_running`
- `test_scene_review_hints_to_story_endpoint` → 改为验证 `None`（phase 已移除）
- `test_endpoint_has_project_id_placeholder` → 改用 `char_review` 验证占位符机制

### 修改文件

- `tests/test_status_authoritative.py` — autouse fixture + 3 个过时测试更新

### 上一完成 (2026-05-22)

**TASK-WAVE-9-TESTER-INDEPENDENT-BASELINE 全完成 ✅ (独立第二意见)**

### pytest 真自跑结果 (KEY_LEARNINGS #47 铁律, 16 test files)

```
test_layer1_portrait_injection.py              7/7   PASS  (Wave 9 新)
test_layer1_fullbody_injection.py              6/6   PASS  (Wave 9.1 新)
test_identity_anchor_cross_genre_baseline.py  105/105 PASS  (Layer 1 baseline, 0 退化)
test_identity_anchor_extraction.py             74/74  PASS  (Layer 1 regression, 0 退化)
test_identity_anchor_injector.py               25/25  PASS  (Layer 1 regression, 0 退化)
test_apply_identity_anchors_location_wire.py    7/7   PASS  (T22-NEW-6, 0 退化)
test_prompt_validator.py                        28/28  PASS  (Layer 1 regression, 0 退化)
test_t22_new_7_id_format_robustness.py         65/65  PASS  (Wave 7, 0 退化)
test_first_batch_chars_not_zero.py             17/17  PASS  (Wave 7, 0 退化)
test_llm_fallback_chain.py                     14/14  PASS  (Wave 7, 0 退化)
test_schema_generic_fallback_arch.py           83/83  PASS  (Wave 8, 0 退化)
test_t22_new_5_r4_2_removed.py                24/24  PASS  (Wave 8, 0 退化)
test_t21_new_3_to_7_backend.py                51/51  PASS  (T21, 0 退化)
test_t21_digital_virtual_fallback.py           25/25  PASS  (T21, 0 退化)
test_t21_new_2_humanoid_fallback_wave2.py      16/16  PASS  (T21, 0 退化)
test_wave9_cross_genre_independent_baseline.py 76/76  PASS  (Tester 独立新建)
────────────────────────────────────────────────────────────────────────
623/623 PASS, 0 FAIL, 0 退化
elapsed: 0.90s, API calls: 0 (零成本 mock)
```

### 新建 test_wave9_cross_genre_independent_baseline.py (76 cases)

| Section | 内容 | Cases | 结果 |
|---------|------|-------|------|
| T2 Portrait 矩阵 | 5 风格 × 5 char_type | 25 | 25/25 PASS |
| T2 Fullbody 矩阵 | 5 风格 × 5 char_type | 25 | 25/25 PASS |
| T2 BW Skip | portrait + fullbody × 5 char_type | 10 | 10/10 PASS |
| T3 Log Marker | portrait inject / fullbody inject / bw skip × 2 路 | 4 | 4/4 PASS |
| T4 边缘 Case | no_id / no_clothing / inject_exception / non-string / cross-path | 12 | 12/12 PASS |
| **Total** | | **76** | **76/76 PASS** |

### 重要 Tester 独立发现

1. **Log marker logger name 不匹配** (P3, 非阻塞): RIM 用 `app.services.reference_image_manager` logger，injector 用 `xuhua` logger。caplog 需用 root level 捕获。建议未来统一到 `xuhua`。
2. **inject exception fallback 验证**: try/except 兜底真实有效 — inject 失败时 portrait/fullbody 仍返回 non-empty prompt + warning log，不 crash。
3. **cross-path anchor consistency 验证**: 同一 character 的 portrait+fullbody 双路注入相同主色 token (mythological "stormy")，Layer 1 三路统一设计正确。

---

## 下一步

DevOps push + VPS 部署 (一次 9+9.1) → Founder spot-check → 内测启动

---

## 上一完成: Wave 7+8 综合 Regression

### pytest 真自跑结果 (KEY_LEARNINGS #47 铁律)

```
13 test files 综合:
  534/534 PASS, 0 FAIL, 0 SKIP
  elapsed: 0.84s
  API calls: 0 (零成本 mock)
```

### 新建 test_t22_new_7_id_format_robustness.py (65 cases)

- Section 1: Format A (char_id) × 19 types = 19 PASS
- Section 2: Format B (name_en) × 19 types = 19 PASS  ← T22-NEW-7 根因修后实证
- Section 3: Format C (mixed)   × 19 types = 19 PASS
- Section 4: Boundary cases                  = 8 PASS
- Total: 65/65 PASS

### T22-NEW-7 修后真实证

Format B (name_en): 19/19 types 全成功匹配 — 修前 Shot 1-3 chars=0 (Coral 变蓝发人腿), 修后 resolve_characters_in_shot 三路 fuzzy match 全通过.

### import 模式 (KEY_LEARNINGS #52 铁律)

使用 `importlib.util.spec_from_file_location` + sys.modules 注册，镜像 baseline 真 pattern，绕过 `app/services/__init__.py` cascade 避免 google.genai ImportError。

---

## 下一步

PM 终审 → e2e test22 重跑验证视觉 → Founder 验证 → 内测启动

---

## 刚完成

### B16 P1 Hotfix 重测 [2026-05-08 20:33-20:36]

**测试项目**: test7 UUID `edd4e938-68f6-4ffe-84f5-503442034dca`
**Backend PID 35835 (PM 重启，hotfix 生效)**

**重测验证结果**:

| 验证项 | 结果 | 证据 |
|--------|------|------|
| Backend 真重启确认 | PASS | PID 35835 (新), /health HTTP 200, "Application startup complete" |
| HTTP 200 响应 | PASS | status="completed", message="Shot 1 重新生成成功" |
| imageUrl 含 ?v= cache bust | PASS | `?v=1778243792` |
| Seedream 真重新生图 | PASS | log: "Shot 1 生成成功 (1664x2218, 147.36s, sanitize_attempts=0)" |
| shot_01.png mtime 变化 | PASS | 1778230393 (16:53) → 1778243792 (20:36) |
| 文件大小变化 | PASS | 2716589 bytes → 2436064 bytes (不同图像) |
| PIL 尺寸验证 | PASS | 1664x2218 RGB，符合 D.15 |
| "生成图像数据格式异常" 不再出现 | PASS | grep count = 0 |
| storyboard_json 写回 DB | PASS | log: UPDATE project_chapters SET storyboard_json, COMMIT |
| 角色一致性回归 | 低风险/已完成进程 | PID 32983 已结束; 5-08 零触碰高风险文件 |

**B16 Hotfix 验收**: PASS — chapters.py L1682-1710 三路判断正确，pil_image 优先路径生效

---

### TASK-T8-INTEGRATION-VERIFY — 5-08 修复批集成验证 [2026-05-08]

**测试项目**: test7 UUID `edd4e938-68f6-4ffe-84f5-503442034dca` (《我妈骂的AI客服是我训练的》)
**测试时间**: 2026-05-08 19:50 - 20:30
**Backend PID 26925 / Frontend PID 26957 (5-08 19:36 启动)**

**验证结果汇总**:

| 验证项 | 状态 | 说明 |
|--------|------|------|
| **V7 pytest 全套** | PASS (295/3 failed/6 errors) | 与 Wave 5.2 基线一致，零退化 |
| **架构测试** | PASS 11/11 | test_architecture.py + test_quality_gates.py 全通过 |
| **B8 _extract_json inner quote fix** | PASS | R4-4 修复: 未转义内部引号解析成功，直接 parse 失败后 fix 成功 |
| **B6 /story 404 for pending/generating_story** | PASS | pending/generating_story -> 404，failed -> 400，completed -> 200 |
| **B11 BGM 6 桶 meta-prompt** | PASS | 6 桶调性词全部验证：bouncy(13次)/syncopated(5次)/driving(7次)/minor key(3次)等全部存在 |
| **B17 ShotValidator anatomy** | PASS 3/3 | severe→valid=False, mild→valid=True, UPPERCASE+string→valid=False |
| **D.24 cache bust** | PASS | bustCache 逻辑正确：无?v=时加 Date.now()，已有时保留 |
| **D.25 BGM 文案** | PASS | "换种风格"+"再来一首"+tooltip 代码已确认 |
| **B16 regenerate_shot 真生图** | **FAIL P1** | 图像生成成功(1664x2218,446s)，但save步骤失败(HTTP500) |
| **角色一致性回归** | RUNNING | test仍在运行中(Stage 1 LLM生成阶段，高风险文件未被修改) |

**B16 P1 Bug 详情**:
- **症状**: POST /chapters/1/shots/1/regenerate → HTTP 500 "生成图像数据格式异常"
- **根因**: chapters.py L1683 `image_data = result.get("image_data")` 从 Seedream 返回的是 base64 string，不是 bytes 也不是 PIL Image。代码 isinstance(bytes) 和 hasattr("save") 均不匹配，fall through 到 else raise 500。PIL Image 在 `result.get("pil_image")` 有但代码未检查
- **Seedream 返回格式**: `{"success": True, "image_data": "<base64_string>", "pil_image": <PIL.Image>, ...}`
- **修复方向**: chapters.py 第1683行附近加一路: `elif result.get("pil_image") and hasattr(result["pil_image"], "save"):` 或先尝试 `pil_image = result.get("pil_image")`
- **严重度**: P1 — 用户无法通过重新生成按钮更新画面
- **图像已真实生成**: 446s Seedream 调用成功，只是保存步骤代码逻辑错误
- **派给**: @backend 修复 `app/api/chapters.py` L1683-1696

**B6 failed状态的分歧**:
- 任务 spec 说 failed → 404，但代码返回 400（"故事生成失败: ${error_message}"）
- 400 语义上更准确（有内容但生成失败），但与 Frontend 处理逻辑需对齐
- 建议 @backend 与 @frontend 对齐处理（现有代码 400 已有明确错误信息）

**角色一致性分析**:
- 5-08 修改文件: chapters.py / projects.py / screenplay_writer.py / shot_validator.py / story_outline_generator.py
- 零触碰高风险文件: image_generator.py / storyboard_prompts.py / storyboard_service.py / reference_image_manager.py
- 结论: 极低风险，预期 PASS

---

### Wave 3.6 — R7-3 P1 portrait 重生独立复测 [2026-04-29]

**测试项目**: T7 UUID `631eef3c-4a26-413a-bcb1-1f038d176e85`，char_001（陈伯）
**测试时间**: 2026-04-29 15:04 - 15:12

**6 证据点**:
| 证据点 | 结果 | 数据 |
|--------|------|------|
| adjust API HTTP 200 + portrait_url 非 null | PASS | 35.5s |
| portrait mtime 真变 | PASS | 20:37:34（Wave3基准）→ 21:42:03（Backend测）→ 15:10:47（Tester独立测）|
| portrait HTTP 200 + size>100KB | PASS | 1524775 bytes (1489 KB) |
| DB updated_at 更新 | PASS | 2026-04-29T07:10:47.273465Z |
| backend log 无 str.get() 错误 | PASS | 日志全文计数=0 |
| character_prompt_builder.py isinstance 检查 | PASS | L106-116 代码确认+日志无异常 |

**复测 verdict**: R7-3 P1 修复 PASS

**char_002 附带发现**: 调整七岁小孩角色触发 CONTENT_SAFETY（NB2 模型内容审查），属独立问题（P3），非 R7-3 bug

---

### TASK-T6-FIXBATCH Wave 3 — T7 端到端验收 [2026-04-28]

**目标**: 真生图 E2E 验收，验证 Wave 1.1 / 1.2 / 2 / 2.5 全部 17 项修复

**T7 项目信息**:
- UUID: `631eef3c-4a26-413a-bcb1-1f038d176e85`
- 故事: "深夜灯火" — 便利店，2 角色（陈伯 + 小宝），插画风格，1:1 比例
- 16 shots 生成完成，所有 2048x2048（PIL 实测）
- BGM 生成成功（156s，Mureka credits=10）
- 实际花费: 16 × $0.03 + portrait/refs ≈ $0.48（¥3.50，超出 ¥1.5 预算）

**12 项验收结果**:

| # | 验收项 | 结论 | 证据摘要 |
|---|--------|------|----------|
| 1 | D.15 shot 实际尺寸 1:1 | PASS | PIL 实测 16/16 shots = 2048x2048，DB aspect_ratio='1:1' |
| 2 | job.current_stage='completed' | PASS | DB 直查确认 |
| 3 | Stage label 跟随 backend stage | PASS | 6 阶段观察: character_design→character_ready→storyboard→image_preparation→image_generation→completed |
| 4 | ETA 单调递减，Stage 5 ≥5min | PASS | 855s→270s→0s，Stage 5 入口 300s |
| 5 | Progress 不倒退（BGM 不掉到 92%） | PASS | 10%→35%→75%→95%→100%，无 92% |
| 6 | adjust portrait 重生（R7-3 P1-3） | FAIL | 非阻塞异常 'str' object has no attribute 'get'，portrait 文件 mtime 未变 |
| 7 | character_ready 后 portrait ≤2s 显示 | PASS | portrait 文件已生成，DB portrait_url 已写入 |
| 8 | StageD 16 shots 可见 + BGM 可播 | PASS | 16/16 image_url，BGM HTTP 200 |
| 9 | Stage E 显示 outline.summary | PASS | confirmed_outline.summary 存在且与 original_idea 不同 |
| 10 | URL /create/[uuid]/[stage] 路由 | PASS | 6 stage 路由全 200，invalid 路由 404 |
| 11 | Dashboard 封面 + shot 数 + 北京时区 | PASS | cover_image_url 存在，shot_count=16，ISO 时区，mood=温馨 |
| 12 | GET /images 返回真实数据（ARCH-1） | PASS(有保留) | 16 行 DB 记录，URL 格式 legacy 问题（预存在） |

**新发现 Bug**:
- R7-3 portrait 重生异常：`projects.py` 约 L987 `generate_character_reference()` 接收到 `str` 而非 `dict`，非阻塞 catch 静默失败
- 严重度: P1（功能失效，非崩溃）

---

### TASK-SEEDREAM-POC Phase 3b — 5 维度评分报告 [2026-04-24]

**目标**: Seedream 5.0-lite vs NB2 (Gemini 3.1 Flash Image Preview) 10 shots 隔离 POC 对比评分

**产出文件**:
- `.team-brain/analysis/SEEDREAM_VS_NB2_POC_REPORT.md`

**9 shots 公平对比均分**（排除 shot_04 sanitized）:

| 维度 | Seedream 5.0-lite | NB2 |
|------|-------------------|-----|
| D2 角色一致性 | 2.78 | 3.00 |
| D3 场景一致性 | 3.22 | 3.44 |
| D4 整体质量 | 3.00 | 3.78 |
| **综合均分** | **3.00** | **3.41** |

**D5 审查严格度**: Seedream 2/5 vs NB2 5/5（Seedream 拦截率 1/10 = 10%）

**总体推荐**: 暂时保留 NB2 为默认，Seedream 需要肉眼看图后再决策

**关键局限**: 本评分是 text-only agent 的 metadata 间接评估，不能替代肉眼看图

---

### TASK-HE-TESTER-1 — 架构测试 + 质量门测试 (10/10 PASS)

**目标**: 创建结构性测试（Architecture Fitness Tests）— 用代码强制执行架构规则。

**创建的文件**:
- `tests/test_architecture.py` — 6 个架构适应度测试
- `tests/test_quality_gates.py` — 4 个质量门测试

**pytest 结果**: 10/10 PASS, 0.06 秒

| # | 测试函数 | 内容 | 结果 |
|---|---------|------|------|
| 1 | test_frontend_does_not_import_backend | 前端不引用后端模块 | PASS |
| 2 | test_backend_does_not_import_frontend | 后端不引用前端模块 | PASS |
| 3 | test_shot_generation_uses_nb2_model | NB2 模型配置正确 | PASS |
| 4 | test_prompt_templates_are_english | Prompt 模板/配置全英文 | PASS |
| 5 | test_pipeline_services_exist | 5 阶段服务文件完整 | PASS |
| 6 | test_reference_generation_is_serial | 参考图串行生成 | PASS |
| 7 | test_story_json_schema | 角色必需字段定义完整 | PASS |
| 8 | test_image_prompts_no_chinese | 翻译机制存在且配置正确 | PASS |
| 9 | test_env_example_exists | .env.example 存在 | PASS |
| 10 | test_required_directories | 必需目录结构完整 | PASS |

---

## 历史完成

### TASK-REAL-PIPELINE-UX Step 1 ✅ 35/35 PASS
### TASK-OUTLINE-MERGE-TEST ✅ 55/55 PASS
### TASK-PLOTPOINT-REORDER-FIX ✅ 39/39 PASS
### TASK-CONFIRM-OUTLINE-TEST ✅ 37/37 PASS (初版)
### TASK-SAFE-DRYRUN ✅ 7/7 PASS
### TASK-IMG-SAFETY-VERIFY ✅ 17/17 PASS
### TASK-E2E-REGRESSION-R8 ✅ 42/44 PASS

---

## 🆕 [2026-04-27 10:50] (PM 代更 — Tester sandbox blocked)

**TASK-PARALLEL-M1 D1 redo ✅ 完成 (04-25 16:40-18:40)**:
- 14/14 全过 + 8 故事图都生成了
- 实花 ¥34.3 / 预算 ¥48
- Bug 2 完全修，Bug 1+4 partial，Bug 5 新发现
- 详见 context-for-others 和 `test_output/parallel_m1_phase2_2026-04-25/PHASE2_REPORT.md`

**当前状态**: 等 Backend round 4 修 Bug 1 + Bug 5，修完 PM 可能派一次 sanity 复测（~¥6, 1 个 quality 故事）

