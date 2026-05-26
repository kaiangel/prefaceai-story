# Backend Agent - 已完成任务

> 按时间倒序记录已完成的工作

---

## 2026-05-26

### test29 #4 — Packet sequence 握手腐败漏接修复 ✅ [2026-05-26 — Opus 4.7 default]

**任务背景**: 浏览器 tab 恢复后突发并发轮询，MySQL 认证握手被截断 → `pymysql.err.InternalError: Packet sequence number wrong - got N expected M` → 3 次 500。旧 `_is_transient_connection_error` 走分支 1 (DBAPIError 子类) 但既无 `connection_invalidated` 也不含 2013/2006/2003 码 → 判 False → 不重试 → 500 漏接。

**改动文件 (1 改 + 1 测扩展)**:

| 文件 | 改动 |
|------|------|
| `app/middleware/db_retry.py` | 新增 `_TRANSIENT_MESSAGE_FRAGMENTS = ("packet sequence number wrong",)` 常量 + `_matches_transient_message_fragment()` (小写匹配) + `_matches_transient_signature()` (统一码匹配 OR 消息片段)。分支 1 的 2 处 `_matches_transient_code` 改调 `_matches_transient_signature`。docstring 同步 |
| `tests/test_wave13_db_retry_middleware.py` | +7 case: packet seq 判 transient / 大小写不敏感 / 经 __cause__ 链 / InternalError 不含短语不误伤 / 业务错含 'packet' 单词不误伤 / GET 重试 1 次自愈 / POST 不重试 |

**#5d 4 重安全约束全保持 (0 破坏)**:
1. 仅幂等 GET/HEAD 重试 — `_IDEMPOTENT_METHODS` 未动，POST/PUT/PATCH/DELETE 不重试
2. 限 1 次 — `_MAX_RETRIES=1` 未动
3. 业务错绝不重试 — 短语 "packet sequence number wrong" 是握手层专有字符串，业务消息含单词 'packet' 不命中（test 实证）
4. 不掩盖真错误 — 非 transient 立即原样抛；重试后仍失败原样抛

**误伤边界已验**: 含 'packet' 业务单词 (`"invalid network packet count"`) + 不含短语的 InternalError (1364 字段错) 均判 False。

**pytest**: `test_wave13_db_retry_middleware.py` **21 PASS** (14 旧 + 7 新)；相关域回归 (db_retry + t20_53_db_pool_config + status_authoritative) **78 PASS，0 退化**。

**PM 审查**: 通过。[frontend-impact: no] 透明重试用户无感，0 Ben 协议越界。

---

## 2026-05-24

### Wave 12 P2-1 (adjust 异步化) + P2-2 (Stage 2 sub-progress) ✅ [2026-05-24 — Opus 4.7 xhigh]

**任务**: test26 暴露 P2-1 adjust 同步阻塞 90s (前端转圈/重试) + P2-2 progress stage 边界粒度 (ETA 冻结)。

**P2-1**: adjust 端点改异步 — 快速校验后返 202+job_id, asyncio.create_task 后台跑 LLM 重写+portrait+fullbody 重生, 前端轮询新 GET adjust-jobs/{job_id} 端点。
- in-memory job 注册表 (`adjust_job_manager.py`), 不新建 DB 表 (避开 Alembic/Ben 域, adjust 是短命 UI 操作)
- 单 uvicorn worker 假设 (Dockerfile.api 无 --workers)
- 全部 fallback 保留 (DEC-051): LLMFallbackChain + B57 fullbody + portrait_ref + 非阻塞 except, 逻辑从旧端点逐行迁移到 `_adjust_character_core`

**P2-2**: Stage 2 portrait loop 每角色推 sub-progress (character_design band 6→9), 让 progress 在 stage 内递增 → ETA 不冻结。Stage 4 已有 per-scene; Stage 1/3 单次 opaque LLM 不造假, 由前端时间插值兜底。

**改动**: 🆕 adjust_job_manager.py + projects.py (异步+轮询+worker) + pipeline_orchestrator.py (Stage 2 sub-progress) + 🆕 test_wave12_adjust_async_job.py (15 case)

**契约**: `[frontend-impact: yes]` — adjust 同步→异步, 完整契约见 context-for-others.md + TEAM_CHAT 2026-05-24 23:55。

**pytest**: 252 PASS / 2 skip / 0 退化。Ben 协议: 0 schema / 0 Alembic / 0 STATUS_API 升级。

---

### Wave 11 TASK-WAVE-11-MYSQL-POOL-PRE-PING-RELIABILITY 诊断完成 ✅ [2026-05-24 — Sonnet 4.6 xhigh, ~20min]

**任务**: 调查 idle 1h 后 pymysql 2013 Lost connection 500

**结论**: `app/database.py` pool 参数在 Wave 4 BUG-T13 + T20-53 时已全部配置到位（pool_pre_ping=True, pool_recycle=1800, pool_size=10, max_overflow=20, pool_timeout=30），无需修改代码。

**middleware retry 决策**: 不加。pool_pre_ping 已覆盖实测场景，遵守 CLAUDE.md 15-A 不过度防御。

**pytest**: 66 PASS (database + status_authoritative), 0 退化。0 越权，0 改动。

---

## 2026-05-23

### Wave 10 Backend 接力 — P3-1 + P3-2 wire ✅ [2026-05-23 — Sonnet 4.6 xhigh, ~30min]

**任务**: 接力 AI-ML commit 3faf585, 完成 2 项 wire

**P3-1 改动** (`app/api/projects.py`):
- import CHARACTER_FIELD_PRESERVATION_RULES (4461 chars)
- 拼接到 adjust_character LLM prompt 末尾 (保护 8 mandatory fields + character_type)
- L1286 直接覆盖 → deep-merge: `merged_char = dict(target_char); merged_char.update(updated_char)` (updated 优先, mandatory 兜底)
- portrait/fullbody 重生成、chapter sync、return 全部改用 `merged_char`

**P3-2 改动** (`app/services/storyboard_director.py` + `pipeline_orchestrator.py`):
- `direct()` 加 `project_aspect_ratio: str = "3:4"` 参数
- `_generate_scene_shots()` 加同参 + 透传
- `_build_scene_prompt()` 加同参 + 注入 `scene_json["project_aspect_ratio"]` 到 LLM input
- `_validate_storyboard()` 加同参 + fallback dict 用 `project_aspect_ratio`
- L1068 + L2334 hardcoded `"2:3"` → `project_aspect_ratio`
- `pipeline_orchestrator.py`: `storyboard_director.direct()` 加 `project_aspect_ratio=aspect_ratio`

**pytest**: 81/81 (Wave 10 suite) + 227/227 (回归) = 308 PASS, 0 退化
**Ben 协议**: 0 schema / 0 Alembic / 0 STATUS_API / 0 frontend 影响 / [frontend-impact: no]
**0 越权**: 不动 AI-ML 已 commit 的 4 个 const

---

## 2026-05-22

### Wave 8 第 3 批 — T22-NEW-5 R4-2 砍掉 (scene_review 移除) ✅ [2026-05-22 ~19:00 — Sonnet 4.6 xhigh, ~2h]

**任务**: TASK-T22-NEW-5 — R4-2 文字层场景确认移除, Stage 3→4 直连

**核心改动**:
- `app/services/pipeline_orchestrator.py`: R4-2 wait loop 完整移除 (~90 行 → 7 行 T22-NEW-5 标记)
- `app/api/chapters.py`: `_derive_ui_phase` 移除 scene_review, `_build_hydrate_hints` 移除 scene_review 分支, 新增 `confirm_scenes_noop` endpoint
- `.team-brain/contracts/STATUS_API_CONTRACT.md`: 升级 v1.4 → v1.5 (8 状态机, scene_review 移除)
- `tests/test_t22_new_5_r4_2_removed.py`: 新建 24 case

**pytest**: 24/24 新 + 172/172 回归 = 196/196 PASS, 0 退化
**Ben 5/13 协议**: 0 schema / 0 Alembic / 0 frontend / 0 越权
**部署**: Frontend Wave 8 #2 + Backend T22-NEW-5 必须同时部署

---

### Wave 8 — Generic Fallback Architecture (pipeline_schemas.py 重构) ✅ [2026-05-22 ~17:00 — Sonnet 4.6 xhigh, ~1.5h]

**任务**: TASK-T22-NEW-9 — 将 Wave 4+4.5 hotfix (17 type 手动 humanoid fallback) 重构为通用方案 B

**核心改动**:
- `app/services/pipeline_schemas.py`: `_TYPE_REQUIRED_GROUPS` 19 entry → 4 + `has_humanoid_fallback()` 通用函数
- `tests/test_schema_generic_fallback_arch.py`: 新建 83 case (8 section)
- `tests/test_t21_digital_virtual_fallback.py`: 1 test 更新 (warning not raise)

**pytest**: 229/229 PASS (25+16+83+105), 0 退化, 0 越权

---

### Wave 7 P0 — Layer 1 first-batch chars=0 + LLM Fallback Chain + Location Wire ✅ [2026-05-22 ~15:30 — Sonnet 4.6 xhigh, ~3h]

**任务范围**: 3 P0/P1/P2 任务一波修齐 (Founder e2e test22 14:09 视觉验证 + 13:30/13:56 fallback 实证)

**真根因诊断 (T22-NEW-7)**: test22 4_storyboard.json 实证 — Stage 4 LLM 输出 `characters_in_scene` 真**格式不一致** (前 3 shot 用 name_en "Coral", 后 18 shot 用 char_id "char_001"). 旧 `_apply_identity_anchors` 只比对 `c["id"]` → 前 3 完全 mismatch → chars=0 → Coral CHARACTER ANCHORS 完全没注入 → Seedream weak ref → Shot 2 美人鱼变蓝头发人腿. **真不是** race/batch/scope — **纯 ID format mismatch**.

**改动文件 (6 改 + 3 新单测, 0 Ben 协议越界)**:

| 文件 | 改动 |
|------|------|
| `app/services/identity_anchor_injector.py` | + 新增 `resolve_characters_in_shot()` standalone helper (三路 id/name_en/name smart match, case-insensitive, dedup, 防御 WARNING) |
| `app/services/image_generator.py` | `_apply_identity_anchors` + outline kwarg (T22-NEW-6), char resolution 改 delegate 到 helper |
| `app/services/pipeline_orchestrator.py` | Stage 5 dispatch 传 `outline=outline` kwarg (T22-NEW-6 wire) |
| `app/services/llm_fallback_chain.py` (**新建 404 行**) | Haiku → Gemini 3.1 Flash → Sonnet 4.6 三层 (跨 provider 优先, KEY_LEARNINGS #55) + FallbackResult dataclass + LLMFallbackAllFailedError + friendly_error_message |
| `app/api/projects.py` | AdjustCharacter 接入 fallback chain |
| `app/api/chapters.py` | Shot regenerate adjustment 接入 fallback |
| `app/services/music_generation_service.py` | `_call_haiku_with_retry()` 重写用 fallback chain (3 caller 自动 benefit) |
| `tests/test_first_batch_chars_not_zero.py` | **新建** 17 case |
| `tests/test_llm_fallback_chain.py` | **新建** 14 case |
| `tests/test_apply_identity_anchors_location_wire.py` | **新建** 7 case |

**pytest 真自跑**: 321/321 PASS (38 新 + 283 旧 regression, 0 退化, 8 文件分别跑)

**Ben 5/13 协议**: 0 改 schemas / alembic / STATUS_API_CONTRACT / frontend / AI-ML 文件 / prompt_validator.py

**RegeneratePortrait 未接入 fallback (note)**: PENDING.md 列入但实测**不调任何 LLM**, 真无 LLM fallback 必要. 已标注给 PM/Founder.

---

### DEC-048 Layer 1 — Identity Anchor Backend 实施 ✅ [2026-05-22 ~12:00 — Sonnet 4.6 xhigh, ~3h]

**任务范围**: AI-ML M1 spec C/D 节真精确实施, 解决 LLM 创意层与一致性的根本张力 (test22 fairytale 20/20 shot Coral hair 全失重演 7 次的真根因)

**核心改动** (5 文件, 0 Ben 协议越界):

| 文件 | 改动 |
|------|------|
| `app/services/identity_anchor_injector.py` | **新建** 400 行 — `inject_identity_anchors()` + 5 个 `_render_*_block` helper. 6 edge case 真兜底 (0 char / 0 props / 0 location / 已注入 / 多角色 / anthropomorphic 调度). Idempotent (marker check). |
| `app/services/prompt_validator.py` | **新建** 260 行 — `PromptValidator` 类 + `ValidationResult` dataclass. `validate_prompt_vs_schema()` (severity 三级: critical/warning/info) + `auto_correct()` (idempotent re-inject). |
| `app/services/image_generator.py` | **改** ~190 行 — + Layer 1 import (L25-32) + `_apply_identity_anchors()` 私有 helper (L820-970, 从 storyboard/screenplay 真提取 location/scene_id/props 的 5 维度 context) + 3 dispatch wire (L1009 generate_shot_image / L1278 generate_shot_image_phase2 / L1639 generate_shot_image_phase2_safe **生产 primary**) |
| `tests/test_identity_anchor_injector.py` | **新建** 25 case |
| `tests/test_prompt_validator.py` | **新建** 28 case |

**pytest 真自跑结果** (KEY_LEARNINGS #47 第 7 次防御, PM 必跑铁律):

- 新单测 injector: **25/25 PASS** (0.05s)
- 新单测 validator: **28/28 PASS** (0.03s)
- AI-ML extraction 真**0 退化**: **74/74 PASS** (0.03s, 与 round 2 完全一致)
- Layer 1 全套合跑: **127/127 PASS** (0.06s)
- Wider 回归 (10 file 含 T20-21/T20-26/T20-27/T20-28/T20-43/T20-22 + t21_new_2): **365/365 PASS** (0.23s)
- 我之前 backend (t21_new_3_to_7): **51/51 PASS** (0.06s)

**真**调用链路接通** (KEY_LEARNINGS #48 防死代码):

```
import L31-32 → 真 in
_apply_identity_anchors L834 → 定义
  ├── inject_identity_anchors L935 → 内部真调
  ├── PromptValidator() L945 → 真实例化
  ├── validate_prompt_vs_schema L946 → 真校验
  └── auto_correct L947 → 真自纠
3 dispatch 调用:
  ├── L1009 generate_shot_image → 真调
  ├── L1278 generate_shot_image_phase2 → 真调
  └── L1639 generate_shot_image_phase2_safe → 真调 (生产 PRIMARY, pipeline_orchestrator L1589 唯一入口)
```

**Ben 5/13 协议 0 变更** (全面 grep self-check):
- ✅ chapters.py / projects.py / schemas / STATUS_API_CONTRACT / alembic 本 session 0 diff
- ✅ storyboard_prompts.py / storyboard_director.py / identity_anchor_prompts.py (AI-ML 职责) 0 越权
- ✅ frontend 0 影响 (Layer 1 真对前端透明)

**关键设计决策**:
- 注入位置: image_prompt 真起始 (LLM 注意力衰减原理)
- 注入器层 idempotent (marker) + 验证器层 idempotent (marker check 不重注 防 LLM tail 漂移导致 anchor block 重复)
- 异常防护: `_apply_identity_anchors()` try/except 兜底 — 任何异常都 fallback 原 shot, 不抛出 (production safety > validation strictness, 与 KEY_LEARNINGS #47/#48/#50 一致)
- mutate shot **COPY** 不动 caller dict
- 跨 19 character_types 通用 (dispatch 已在 AI-ML extract_identity_anchors 真做)
- 跨 80+ styles 通用 (extract_style_anchors 真从 StyleEnforcer 真读)

**风险提示给 Tester / Founder**:
1. Tester baseline 矩阵 (95 case) 真用 `inject_identity_anchors()` mock fixture 跑 grep 验证, 不调真 API (零成本)
2. Founder e2e 重跑 test22 真验证 prompt 含 sea-green (现在通过 inject path 真保证 100%)
3. anchor block 真**~600-1500 chars** for 1-3 角色 — Seedream context budget 真**充裕** (Seedream 真允许 ~4000 chars)

---

## 2026-05-21

### Wave 5 — TASK-T21-NEW-3/4/5/6/7 ✅ [2026-05-21 22:30 — Opus 4.7 thinking xhigh, ~3h]

**任务范围** (5 task 串行, 真大架构改造):

| Task | 优先级 | 改动核心 | 单测 |
|------|--------|---------|------|
| T21-NEW-3 | P1 | restart-from-failed-stage 真重算 progress/ETA (传 actual_shot_count/unique_location_count/max_concurrent 真值 + 友好 stage_message) | 5/5 |
| T21-NEW-4 | P1 | AdjustCharacter + RegeneratePortrait portrait_url + fullbody_url 加 `?v={epoch}` cache-buster | 4/4 |
| T21-NEW-5 | P2 | Stage 5 stage_message "角色参考图" → "全身参考图" 明确语义 (KEY_LEARNINGS #46 同源思想) | 2/2 |
| T21-NEW-7 | P0 | **大架构**: Stage 4.5 scene_image_preparation + R4-3 闸门 + 3 endpoint + STATUS_API_CONTRACT v1.4 + DEC-047 + Alembic 006 + 2 DB 列 + 9 ui_phase 状态机 | 24/24 |
| T21-NEW-6 | P1 | image_preparation 多 sub-step stage_message 细化 (≥5 sub-step) + SceneReferenceManager sub_progress_callback 参数 | 6/6 |

**改动文件** (9 个 + 2 文档):
- `app/models/project.py` (+ scene_references_confirmed)
- `app/models/chapter.py` (+ scene_references_json LONGTEXT)
- `app/schemas/chapter.py` (+ 2 字段, 9 状态机注释)
- `app/services/pipeline_orchestrator.py` (+ Stage 4.5 大块 ~180 行 + R4-3 wait loop + Stage 5 5a.5 复用+兜底 + STAGE_DURATIONS 9 stage + sub-stage messages + T21-NEW-5 文案)
- `app/services/scene_reference_manager.py` (+ sub_progress_callback 4 参数 + _emit_sub_progress helper)
- `app/services/job_manager.py` (+ _ETA_STAGE_BASELINES/_ETA_STAGE_PROGRESS_BOUNDS 9 stage)
- `app/api/chapters.py` (+ T21-NEW-3 真重算 + _derive_ui_phase 新 stage + _build_hydrate_hints + status return 新字段 + 3 endpoint)
- `app/api/projects.py` (+ T21-NEW-4 cache-buster + start_generation 重置)
- `alembic/versions/006_add_scene_references_t21_new7.py` (新 migration + backfill)
- `.team-brain/contracts/STATUS_API_CONTRACT.md` (v1.3 → v1.4)
- `.team-brain/decisions/DECISIONS.md` (+ DEC-047)

**pytest 真结果** (PM 自跑 KEY_LEARNINGS #47):
- 新 51/51 PASS (test_t21_new_3_to_7_backend.py)
- 综合回归 234/234 PASS (T21-NEW-1/2/T20-43/T20-50/T20-44/T20-47/T20-48/T20-46/T20-27/T20-13/T20-53/shot_regenerate/T20-50b)
- 综合 (新 + status_authoritative) 95/95 PASS

**架构关键设计**:
- 9 状态机 (新 scene_references_review): input → outline → char_review_pending → char_review → scene_review_pending → scene_review → storyboard_running (Stage 4 + Stage 4.5 复用) → **scene_references_review (R4-3)** → shot_generating → completed
- Pipeline Stage 4 完成 → Stage 4.5 真生成 scene anchors + 写 chapter.scene_references_json → R4-3 wait loop → 用户在 frontend /scenes 页面真预览+编辑+重生+60s 倒计时 → POST /confirm-scene-references → Stage 5 fullbody+shots
- "情节确认" (R4-2 文字) ≠ "场景视觉确认" (R4-3 视觉), 都给用户停留点
- 镜像 characters 页面对偶设计 (R4-1 角色视觉 ↔ R4-3 场景视觉)
- DEC-014/DEC-009 一致性保留 (regenerate exterior 用 interior 作参考)

**约束遵守**:
- 0 越权改 TEAM_CHAT/PENDING (paste 给 PM 代写)
- Edit STATUS_API_CONTRACT v1.4 + DECISIONS DEC-047 (PM 派工明确授权)
- 不重启 Backend (等 PM 审查后重启)
- 镜像 AdjustCharacter / 60s 倒计时模式
- 0 退化 (除 pre-existing T20-52 isolation bug, 不阻塞)

---

### TASK-T21-NEW-2 — Wave 4.5 5 type humanoid fallback 补充 ✅ [2026-05-21 ~21:45 — Sonnet 4.6 xhigh]

**背景**: PM 19 type 地毯式分析发现 5 type (aquatic/anthropomorphic_animal/object/plant/insect) 可能呈人形但无人外貌字段 fallback

**修复** (`app/services/pipeline_schemas.py` 注释 + _TYPE_REQUIRED_GROUPS):
- P0: `aquatic` → 加 hair_color/skin_tone/face_shape (美人鱼公主)
- P0: `anthropomorphic_animal` → 保留 2 group AND, group 2 加人外貌 (狼人/猫娘, species 仍必须)
- P1: `object` → 加 hair_color/skin_tone/face_shape (钟先生/Olaf)
- P2: `plant` → 加 hair_color/skin_tone/face_shape (树精/花仙女)
- P2: `insect` → 加 hair_color/skin_tone/face_shape (蝴蝶仙子)
- 保留不改: `animal` (纯动物) + `vehicle_character` (Transformers 罕见)

**新建测试** (`tests/test_t21_new_2_humanoid_fallback_wave2.py`):
- 16 单测: 5 type × 人外貌 PASS + type-specific PASS + anthropomorphic_animal 2 FAIL + 3 regression
- **16/16 PASS**

**更新** (`tests/test_t21_digital_virtual_fallback.py`):
- 1 过时测试 (T21-NEW-1 时 insect 未在修复列表, 预期 FAIL) 更新为 T21-NEW-2 后正确 PASS
- T21-NEW-1 仍 **25/25 PASS**

**pytest 汇总**:
- 新测试 16/16 PASS
- T21-NEW-1 25/25 PASS (0 退化)
- T20-43 26/26 PASS (0 退化)

**约束**: 不重启 backend, 等 PM 审查后重启

---

## 2026-05-20

### TASK-T21-NEW-1 — digital_virtual + 7 non-human humanoid schema fallback ✅ [2026-05-20 ~21:30 — Sonnet 4.6 xhigh]

**背景**: test21 Stage 2 失败 (char_001 小爱 digital_virtual, 15 人类外貌字段被 schema 拒绝)

**修复** (`app/services/pipeline_schemas.py` L220-245):
- 更新注释 + _TYPE_REQUIRED_GROUPS 8 个 type 加人类外貌字段 OR fallback
- P0: digital_virtual → `[('digital_type', 'base_form', 'hair_color', 'skin_tone', 'face_shape')]`
- P1: robot, hybrid, alien (各加 hair_color/skin_tone/face_shape)
- P2: elemental, concept_personified, giant, miniature (各加 hair_color/skin_tone/face_shape)

**新建测试** (`tests/test_t21_digital_virtual_fallback.py`):
- 25 单测: 8 type × 2 PASS (human fallback + type-specific) + 1 FAIL (无字段) + regression
- 25/25 PASS

**pytest 汇总**:
- 新测试 25/25 PASS
- T20-43 26/26 PASS (0 退化)
- Wave 3 核心 6 文件综合 101/101 PASS
- 全量 tests/ 1685 PASS (pre-existing 9 fail 与本次改动无关)

**约束**: 不重启 backend, 等 PM 审查后重启

---

### Wave 3 — T20-51 + T20-52 + T20-53 (3 P3 long-tail fixes) ✅ [2026-05-20 ~21:00 — Sonnet 4.6 xhigh]

**T20-51 BGM meta-prompt 迁出 test_output**:
- `app/services/music_generation_service.py` META_PROMPT_DIR: `test_output/...` → `app/prompts/bgm`
- `app/prompts/bgm/meta_mixed_v3_quote_picking.md` (新建, 100% 与旧文件一致)
- `app/prompts/bgm/meta_en_v2.md` (新建, 100% 与旧文件一致)
- `tests/test_t20_51_bgm_meta_prompt_path.py` (新建, 9 PASS)

**T20-52 T20-47 测试 isolation 修复**:
- `tests/test_t20_47_shot_validator_fallback.py` — 新增 `_load_shot_validator_fresh()` autouse fixture
- `tests/test_t20_50_fix_round3.py` — 同样的 isolation fixture
- 根因: test_t20_43 注入 app/app.services stub (无 __path__) 污染 sys.modules
- 修复: 每 test 前清除 stub, 用 importlib.util.spec_from_file_location 直接加载 shot_validator.py
- 综合跑验收: 140→162 PASS, 0 fail (修复前 22 fail)

**T20-53 SQLAlchemy pool 优化**:
- `app/database.py` 新增 `pool_timeout=30`
- `tests/test_t20_53_db_pool_config.py` (新建, 13 PASS)
- 其余 pool 参数 (pool_pre_ping/pool_recycle/pool_size/max_overflow) 在 Wave 4 BUG-T13 已配置

**pytest 汇总**: 综合 T20-43~T20-53 162 PASS, 0 fail (3 新 test 文件共 31 新单测)

---

### Wave 2 round 3 — T20-47-fix (SONNET_MODEL) + T20-50-fix-2 (save_all_references) ✅ [2026-05-20 ~20:00 — Sonnet 4.6 xhigh]

**改动**:
- `app/services/shot_validator.py` L184: `SONNET_MODEL` 改为 `"claude-sonnet-4-6"`（去掉不存在的 -20251101 后缀）
- `app/services/reference_image_manager.py` L791-811: `save_all_references` 加 `os.path.exists` 判断，文件已存在 skip save
- `tests/test_t20_47_shot_validator_fallback.py` L77-89: 更新 `test_sonnet_model_constant` 期望值

**新建测试**: `tests/test_t20_50_fix_round3.py` — 9 case 全 PASS:
- 3 case: SONNET_MODEL 常量验证
- 2 case: mock Anthropic API 调用 (model ID 真发到 API)
- 4 case: save_all_references 不覆盖已存在文件（含 T20-50 重生场景）

**注意**: 代码改完未重启 backend (PID=79233 正跑 Founder test20 Pipeline)，等 Pipeline 完成后 PM 重启生效

---

### Wave 2 — T20-50b + T20-47 + T20-48 ✅ [2026-05-20 18:15 — Sonnet 4.6 xhigh]

**改动**: `app/services/shot_validator.py` + `app/services/pipeline_orchestrator.py` (代码改动) + `app/api/projects.py` (审查确认)

**新建测试**: 3 文件 58 新单测全 PASS:
- `tests/test_t20_50b_adjust_character_regen.py` — 16 case (adjust_character 总是重生 portrait+fullbody)
- `tests/test_t20_47_shot_validator_fallback.py` — 20 case (Sonnet 4.6 主 + Haiku 降级 + 30%告警)
- `tests/test_t20_48_anatomy_auto_regen.py` — 22 case (anatomy 2次重试 + partial_failure)

**Backend**: PID=75990, `/health` 200

---

### Wave 1 补遗 — T20-46 wire + STATUS_API_CONTRACT v1.3 + character_consistency 说明 ✅ [2026-05-20 17:45 — Sonnet 4.6 xhigh]

**任务 1 - T20-46 Backend Wire**:
- `app/services/pipeline_orchestrator.py` L561-564: `character_designer.design(outline)` → 传 `style_preset=style_preset`
- 新建 `tests/test_t20_46_backend_wire.py` 11 单测 PASS
- 回归: `tests/test_t20_46_character_style_infusion.py` 47/47 PASS

**任务 2 - STATUS_API_CONTRACT v1.3**:
- `.team-brain/contracts/STATUS_API_CONTRACT.md` 升级 v1.2→v1.3
- shots_completed §1.2 注释升级 (8 stage 行为说明)
- 新增 §1.4 跨阶段值表
- 新增 §8 v1.3 历史条目
- 补救 KEY_LEARNINGS #36 (Backend agent 漏改 STATUS_API_CONTRACT.md 铁律)

**任务 3 - character_consistency e2e 说明**:
- 更新 context-for-others.md: T20-50 修改逻辑正确性已 unit test 验证，e2e 一致性需 Founder 手动跑 test20/test21

---

### T20-50 P0 freshness check 算法完全移除 ✅ [2026-05-20 17:15 — Sonnet 4.6 xhigh]

**触发**: test20 陈婶重生事故 — 用户在 /characters 页重生 portrait (gothic) → Pipeline 覆盖重生为 realistic (freshness check 算法 bug)

**真根因**: `pipeline_orchestrator.py:L1071` `_portrait_fresh = _portrait_mtime > (_char_ts + 30)` — RegeneratePortrait 端点 T₀ 同时写文件(mtime=T₀) + 更新 DB(updated_at=T₀)，所以 T₀ > T₀+30 = False → 算"陈旧" → Pipeline 重新生成覆盖

**修复 (Founder 方案 A — 信任用户操作 KEY_LEARNINGS #46)**:
- 完全删除 freshness check 算法 (~20 行: `_portrait_mtime / _char_updated_at_str / _portrait_fresh / _char_ts + 30`)
- 改为: `if file exists → skip=True` (信任 character_refs/ 目录里现有文件)
- 加 `logger.info(f"[Pipeline] {char_name} portrait 已存在, 信任用户操作 (no regen, T20-50 KEY_LEARNINGS #46)")`

**改动 1 文件**: `app/services/pipeline_orchestrator.py` L1054-1080

**新增测试**: `tests/test_t20_50_freshness_removed.py` 5 个 case (含 case 4 旧 bug 重现对比)

**验收**: 5/5 pytest PASS，回归 137/137 PASS，Backend 重启 PID=68942 /health 200

---

### T20-44 P1 shots_completed BGM 阶段重置 bug 修复 ✅ [2026-05-20 17:15 — Sonnet 4.6 xhigh]

**触发**: test20 BGM 阶段 status API 返回 shots_completed=0 (应保留 27)

**真根因**: `chapters.py` shots_completed 计算逻辑: stage="bgm" 走 `else` 分支 → `_shots_completed = 0` (重置)

**修复**: 加 `_POST_IMAGE_GEN_STAGES = {"bgm", "postprocess", "finalize", "completed"}` 集合，这些 stage 下返回 `shots_total` (不重置)

**改动 1 文件**: `app/api/chapters.py` — shots_completed 计算逻辑区分 post-image-gen stages

**新增测试**: `tests/test_t20_44_shots_completed_timing.py` 21 个 case

**验收**: 21/21 pytest PASS，Backend PID=68942 /health 200

**Frontend 配合**: 待 Wave 2 (Frontend 读 shots_completed 渲染 ETA)

---

### DEC-043 RISK-T20-?? supernatural humanoid hotfix ✅ [2026-05-20 15:35 — Sonnet 4.6]

**触发**: test20 horror 镜中人 char_002 (supernatural + 人类外貌字段) Stage 2 Schema 验证崩溃

**改动**: `app/services/pipeline_schemas.py` `_TYPE_REQUIRED_GROUPS` — supernatural/undead/mythological/fantasy_creature 4 个 type 各自 group 内加入 `hair_color/skin_tone/face_shape`（OR 关系 fallback）

**新增**: `tests/test_supernatural_humanoid_hotfix.py` 7 个 case，全 PASS

**验收**: 51/51 pytest PASS（7 新 + 44 回归），Backend 重启 PID=55021 health OK

---

### T20-29 v3 输出端 wire — Schema extra='allow' + KPI 真接通 + narrative_cluster fallback ✅ [2026-05-20 11:30 — Sonnet 4.6]

**任务**: PM v3 wire 审查发现 KEY_LEARNINGS #29 教训重演 — AI-ML v3 prompt 写好了、Backend 注入 prompt 也对了，但 LLM 输出端没接住：schema 默认丢 v3 字段 + validate_scene_self_evaluation 死代码。

**改动 2 文件**:

| 文件 | 改动 | 行数 |
|------|------|------|
| `app/services/pipeline_schemas.py` | SceneSchema + ScreenplaySchema 各加 `model_config = ConfigDict(extra='allow')` | +6 行净增 |
| `app/services/screenplay_writer.py` | import 3 个 v3 函数 + 3 处 KPI 软警告调用 + P2 narrative_cluster fallback | +22 行净增 |

**验收全 PASS**:
- ✅ py_compile 两文件 PASS
- ✅ SceneSchema(**v3_dict) 实测: narrative_cluster + scene_self_evaluation 字段全保留 ✅
- ✅ grep validate_scene_self_evaluation app/services/ → 3 处调用 (修前 0) ✅
- ✅ 538/538 pytest (test_t20_* 519 + test_pipeline_* 19) 全 PASS

---

### TASK-T20-FIXBATCH-6 Wave 5 v3 wire — DEC-046 Stage 3 + Stage 4 注入 ✅ [2026-05-20 10:45 — Sonnet 4.6]

**任务**: AI-ML Wave 5 完成 T20-28 v3 prompt 重构 (15 原则 + 8 cluster + 85% KPI), Backend wire 到 services 层让 v3 生效.

**改动 2 文件**:

| 文件 | 改动 | 行数 |
|------|------|------|
| `app/services/screenplay_writer.py` | import 2 个 v3 常量 + 4 处 f-string 注入 (batch + single 各 2) | +8 行净增 |
| `app/services/storyboard_director.py` | import 1 个 v3 常量 + 2 处 f-string 注入 (scene + prompt) | +4 行净增 |

**验收全 PASS**:
- ✅ py_compile 两文件 PASS
- ✅ Stage 3 dry-run: CLUSTER DISPATCHER / SELF-EVALUATION 85% / narrative_cluster / scene_self_evaluation 全在 prompt ✅
- ✅ Stage 4 dry-run: IMAGE-TEXT COMPLEMENT / MINIMAL DIALOGUE / TIMELINE JUMP MARKER / METAPHOR & SYMBOL 全在 prompt ✅
- ✅ 217/217 pytest PASS (test_t20_21 60 + test_t20_17 33 + test_t20_26 23 + test_t20_27 33 + test_t20_28 68)

---

## 2026-05-19

### TASK-T20-FIXBATCH-5 Wave 4 T20-26 P0 — regenerate flow replace 策略 ✅ [2026-05-19 22:55 — Opus 4.7 default]

**任务**: 改 `regenerate_shot` endpoint 为 replace 策略 (不再 append) + Backend 双层兜底 (KEY_LEARNINGS #37/#38, DEC-045)

**根因 (test19 Founder 5 次 Shot 15 重生失败)**:
- 旧 `build_adjustment_user_prompt()` Rule 1+4+8 强制 Haiku 保留原 prompt 全部元素 → ghost / double-exposure / overlap 段落原封不动 → Seedream content_safety 100% 拒
- 实测: 原 prompt 814 chars → Haiku 改写后 2203 chars (追加 1389 chars 不删原敏感词)

**修复路径** (双团队协调):
- **AI-ML** (并行 Wave 4): 升级 `SHOT_ADJUSTMENT_SYSTEM_PROMPT` 为 Two-Mode (Mode A surgical / Mode B replace) + 新 `build_adjustment_user_prompt(mode="auto")` + `SEEDREAM_TRIPWIRE_KEYWORDS` + `detect_seedream_tripwire()`
- **Backend** (本任务): 接通 AI-ML 升级的 `mode="auto"` builder + Haiku 返回后**强制 check_replace_effective** + **兜底 strip_known_dark_terms**

**改动 3 文件**:

| 文件 | 改动 | 行数 |
|------|------|------|
| `app/services/shot_prompt_rewriter.py` | 新建 — Backend 兜底层模块 | 568 |
| `app/api/chapters.py` `regenerate_shot` | 改 user prompt 构造 + Haiku 后 check + 兜底 strip + 完整 [T20-26] 日志 | L2056-2168 (改 ~100 行) |
| `tests/test_t20_26_regenerate_replace_flow.py` | 新建 60 单测 8 sections | 568 |

**真实链路**:
```
Founder 点 "调整画面" (中文 intent)
  ↓ POST /chapters/1/shots/{id}/regenerate
  ↓ detect_seedream_tripwire(orig) → mode A/B
  ↓ build_adjustment_user_prompt(orig, intent, mode="auto")  ← AI-ML
  ↓ Haiku 4.5 (max_tokens=3000) + SHOT_ADJUSTMENT_SYSTEM_PROMPT
  ↓ check_replace_effective(orig, rewritten)  ← Backend 强制校验
  ↓ effective=False? → strip_known_dark_terms()  ← 机械兜底
  ↓ 写回 storyboard_json (image_prompt)
  ↓ SeedreamGenerator 真生图
```

**Backend 兜底层 (`shot_prompt_rewriter.py`)**:
- `KNOWN_DARK_TERMS` 5 类 ~40 词 (灵异/双重曝光/已故角色/身体重叠/vision overlay)
- `find_known_dark_terms(text)` — 词边界匹配 (单词) + 子串匹配 (短语), 大小写不敏感, 去重
- `strip_known_dark_terms(text)` — **长短语优先**替换 (防 "two faces merging" 替换后留 "faces merging" 二次拼接) + safe alternatives map ("warm light" / "split composition" / "in fond memory")
- `check_replace_effective(orig, rewritten)` — 2 维度: 仍含敏感词 + length ratio > 2.0x = suspicious append
- `build_replace_user_prompt()` + `gather_scene_context_for_replace()` + `gather_character_context_for_replace()` — 保留为 helper (当前 endpoint 不用, 未来如需 Backend 完全自主构造 prompt 可启用)

**Mode A/B 自动判定** (AI-ML 设计, Backend 接通):
- 无触发词 → Mode A (SURGICAL EDIT, 旧行为)
- 含 ghost/double-exposure/etc → Mode B (REPLACE-AND-CLEAN, 完全重写 + 自检 verify)

**验证**:
- ✅ 60/60 test_t20_26_regenerate_replace_flow PASS (Backend 新单测)
- ✅ 55/55 test_t20_26_prompt_rewriter_replace + test_t20_26_seedream_safety_avoidance PASS (AI-ML 写)
- ✅ 9/9 test_shot_regenerate_persistence PASS (主流程不退化)
- ✅ 15/15 test_async_anthropic_t18_j PASS (T18-J 不退化)
- ✅ 139/139 status_authoritative + t20_13 + t20_9_v3 + t20_19 + t20_21 + t20_10 综合 PASS
- ✅ 400/400 Wave 1-4 + T20 系列综合 PASS
- ✅ 1218 全 suite PASS, 4 fail + 6 error 全 pre-existing (audit 确认与本次无关)
- ✅ py_compile chapters.py + shot_prompt_rewriter.py PASS

**Ben 契约**:
- regenerate-shot endpoint **不在** STATUS_API_CONTRACT 监控的 13 字段范围内 (Wave 9 字段)
- 响应 schema **无新字段**
- **`[frontend-impact: no]`** — STATUS_API_CONTRACT.md 不需要改, 无需升 v1.3

**0 越权**: 仅改 app/services + app/api + tests/ (Backend 白名单), 未改 AI-ML 任何文件, 未改 frontend, 未重启 backend (PM 决定时机)

**给 Tester 验收 metrics** (Founder 手动 test20 时 grep backend log):
- `[T20-26][Shot Regenerate] strategy=mode_X_...` (期望 mode_B_ok 为主, 偶尔 mode_B_with_mech_strip_fallback)
- `tripwire_hits=[...]` (Mode B 应 ≥1)
- `ratio=...x` (应 0.4-1.5x, > 2.0x 标 warning)

---

### T20-17 Backend Wire — Stage 4 Species Fidelity ✅ [2026-05-19 20:00 — Sonnet 4.6]

**任务**: Wire AI-ML 的 `build_stage4_character_data_block` + `SPECIES_FIDELITY_RULES` 到 `storyboard_director.py`

**根因**: `_build_scene_prompt()` 旧逻辑只传 `{id, name, clothing_summary}` → LLM 对非 human 角色物种零信息 → hallucinate "hedgehog-like" (Milly 是 rabbit)

**改动** (仅 `app/services/storyboard_director.py`):
- import 加 `SPECIES_FIDELITY_RULES` + `build_stage4_character_data_block`
- `_build_scene_prompt()` L1534-1558: 旧 chars_simplified loop → `characters_block = build_stage4_character_data_block(characters)`
- prompt 模板: `{characters_json}` → `{characters_block}` (含 "Character data:" prefix, 去掉重复 header)
- prompt 模板 HAIR_COLOR 后注入 `{SPECIES_FIDELITY_RULES}`
- `_build_prompt()` dead code: Option A 同步改动

**验证**: 33/33 test_t20_17 + 13/13 storyboard_schema + 79/79 t20_10+t20_21 PASS, dry-run fox/rabbit/sparrow 全传 LLM

---

### TASK-T20-FIXBATCH-4 Wave 2 — T20-21 wire + T20-9.v3 ETA 全局重审 ✅ [2026-05-19 19:00 — Opus 4.7 default]

**任务**: Wave 1 完成后串行 2 项 (PM 派活 5/19 17:45):
- T20-21 P0 Backend wire — Stage 3 ScreenplayWriter 接通 AI-ML Wave 1 已实现的 DEC-044 prompts
- T20-9.v3 P1 ETA 全局重审 — Founder 5/19 16:08 反馈 4 项核心问题 (基于 Wave 1 T20-13 新加的 shots_total/completed/failed 真字段)

#### T20-21 Backend wire (~30 min)

**改动** (`app/services/screenplay_writer.py`):
- 顶部 import: `DEC044_SCREENPLAY_RULES` + `DEC044_SCREENPLAY_OUTPUT_EXAMPLE` + `get_dec044_narration_max_chars`
- `_build_batch_prompt()` 2 处注入: DEC-044 rules block (在 CHARACTER CONSISTENCY 后) + OUTPUT_EXAMPLE (替换旧 prose JSON template)
- `_build_single_scene_prompt()` 2 处注入: 同上
- `target_narration_words` 公式改: `max(80, int(duration * 4))` (80-400) → `min(120, int(duration * 1.5))` (≤120 hard cap, DEC-044)
- 删旧"【字数硬性要求：必须≥X字】" prose-mode 硬要求文本
- 删旧"这是TTS朗读的旁白" 描述
- `_expand_narration_if_needed()` v1 disable (return scene unchanged) — 详注释为何 DEC-044 narration 不再需要扩写

**Stage 4 自动受益**: storyboard_director.py 已 import COMIC_MODE_NARRATIVE_RULES (AI-ML Wave 1 已升级, Backend 无需改动)

**验证**:
- py_compile screenplay_writer.py PASS
- 新单测 tests/test_t20_21_wire.py 18 PASS (6 测试类: rules injection / output example injection / 旧文本删除 / target words 公式 / expand disabled / universal generic story / module structure)
- 回归 111 PASS (b51_fallback 50 + t20_21_narration_to_shot_content 42 + t20_10_universal_character_schema 19)

#### T20-9.v3 ETA 全局重审 (~60 min)

**改动** (`app/api/chapters.py`):
- 新加 4 常量: `_V3_PER_SHOT_SECONDS=80` / `_V3_BGM_BASELINE_SECONDS=120` / `_V3_POSTPROCESS_BASELINE_SECONDS=30` / `_V3_TERMINAL_PHASE_MIN_ETA=5`
- 新 helper `_compute_v3_eta(job, shots_total, shots_completed, max_concurrent, legacy_eta) -> int | None`:
  - completed → 0
  - image_generation: `(shots_total - shots_completed) * 80 / max_concurrent + 120 (bgm) + 30 (postprocess)`
  - bgm: bgm baseline 按 progress (92-100) 内折扣 + postprocess
  - image_preparation: 保底 full image_gen + bgm + postprocess (避免低估), legacy 更大时信 legacy
  - 早期 stage (shots_total=None) → 返 None 走 legacy chain
  - **v3 真实数据完全接管, 不被 legacy_eta 上限约束** (Founder 反馈核心修复)
- status endpoint 在 `_shots_total/_shots_completed` 计算后调 v3, 接管 estimated_remaining (try/except 兜底)

**改动** (`.team-brain/contracts/STATUS_API_CONTRACT.md`):
- 升 v1.1 → v1.2 — schema 字段不变, 仅 estimated_remaining_seconds 算法升级
- §8 添加完整 v1.2 changelog (Founder 4 核心问题 + v3 算法 + 测试结果 + 向后兼容声明)

**Founder 4 P0 问题修复对照**:

| Founder 反馈 | v3 修复 |
|------|---------|
| #1 progress=84% 但 Shot 14/20 才开始 | 用真实 shots_completed (=14) 替代 progress 反推, 算剩 6 shot |
| #2 前端"自说自话" | backend 优先返 v3 真实 ETA, frontend 直接显示 (不再需自己 fallback) |
| #3 progress >= 95% 显"即将完成"无数字 | v3 保底 ≥5s 具体数值 (`_V3_TERMINAL_PHASE_MIN_ETA`) |
| #4 跨 stage 累积 | image_generation ETA 含 bgm(120) + postprocess(30) |

**验证**:
- py_compile chapters.py PASS
- 新单测 tests/test_t20_9_v3_eta.py 32 PASS (11 测试类: completed / 早期 stage 不接管 / image_gen 真实数据 / v3 接管 legacy / bgm / image_prep / universal / 跨 stage / 终态保底 / edge cases / Founder 实测场景)
- 回归 102 PASS (status_authoritative 44 + t20_13_shots_count 34 + t20_9_estimated_remaining 17 + d2_eta_parallel 7)
- 全 suite (~30 min 跑中, 后台)

**API 契约变化** (STATUS_API_CONTRACT.md v1.2):
- `estimated_remaining_seconds`: schema 不变, 算法升级
- Frontend useETA.ts Wave 2 行动建议: **优先用 backend 这个字段** (现更准, 不需前端 fallback 算 ETA)
- shots_total/completed/failed (Wave 1 T20-13 已加) — v3 算法直接消费, frontend 也可直接读

**Frontend Wave 2 useETA.ts 建议**:
- 删除任何 hardcoded `STAGE_BUDGET_SECONDS` fallback (backend v3 算法已准, 无需前端补)
- 直接显示 `status.estimated_remaining_seconds` (image_generation/bgm/completed/image_preparation 阶段都准了)
- progress >= 95% 也显示具体数字 (不再"即将完成")
- 如要本地校验, 可用 `shots_total - shots_completed` 显示 "已生成 X/Y 张" (T20-13 字段)

**改动文件列表** (3 修改 + 2 新建):

修改:
1. `app/services/screenplay_writer.py` — DEC-044 wire (import + 2 inject + 2 narration target + expand disable)
2. `app/api/chapters.py` — v3 ETA helper + status endpoint 接管
3. `.team-brain/contracts/STATUS_API_CONTRACT.md` — v1.1 → v1.2

新建:
4. `tests/test_t20_21_wire.py` — 18 case
5. `tests/test_t20_9_v3_eta.py` — 32 case

**Commit label** (Ben 规则 3 pre-commit hook):
- 修改了 6 监控文件之一 (`app/api/chapters.py`)
- commit message 必须含 `[frontend-impact: yes]`
  - 理由: estimated_remaining_seconds 算法升级, Frontend Wave 2 useETA.ts 应改用 backend 值不再 fallback

**0 越权**: 严格在 PM 派活白名单内 (app/services/screenplay_writer.py / app/api/chapters.py / .team-brain/contracts/ / tests/)

**Backend PID 82102 未重启** (PM 任务约束明确说不重启 — 待 PM 决定时机)

### TASK-T20-FIXBATCH-4 Wave 1 — T20-13 P0 + T20-14 P0 + T20-19 P1 ✅ [2026-05-19 17:20 — Opus 4.7 default]

**任务**: test17 v2 端到端实测后 Founder 拍板 12 项内测前必修, Wave 1 Backend 3 项串行做 (PM 派活 5/19 16:30):
- T20-13 P0 status API 加 shot 级真实计数字段 (frontend 不再 regex 解析 message)
- T20-14 P0 ShotValidator Anthropic 429/529 退避重试 (test17 v2 18/18 fail-open → B51 fallback 形同虚设)
- T20-19 P1 pipeline 单 shot wall-clock timeout 720s (Shot 14 hang 12.5 min / Shot 16 hang 14.2 min)

#### 改动文件 (4 修改 + 3 新建)

修改:
1. `app/schemas/chapter.py` — ChapterStatus +3 字段 (shots_total/completed/failed, 默认 None)
2. `app/api/chapters.py` — import re + ~50 行 status endpoint shots_total/completed/failed 派生 (regex/progress 反推/stage 派生)
3. `app/services/shot_validator.py` — 2 helper (_is_retryable + _call_anthropic_with_retry) + validate_shot 用 helper + except 路径区分 reason
4. `app/services/pipeline_orchestrator.py` — SHOT_WALL_CLOCK_TIMEOUT_SEC=720 常量 + asyncio.wait_for 包裹 _generate_one_shot

新建:
5. `tests/test_t20_13_shots_count_fields.py` — 34 case (6 schema + 6 regex + 6 progress + 6 stage + 5 真实场景 + 5 源码验证)
6. `tests/test_t20_14_anthropic_retry.py` — 24 case (8 retryable 判定 + 4 常量 + 6 helper 行为 + 2 集成 + 4 源码)
7. `tests/test_t20_19_shot_wall_clock_timeout.py` — 14 case (3 常量 + 5 源码 + 3 wait_for 行为 + 1 result shape + 2 既有路径)

#### 验证

- ✅ **新单测 72/72 PASS** (34 + 24 + 14)
- ✅ **293 regression PASS** (T20-8/9/10 + status_authoritative + shot_validator_compression + shot_validator_universal_skip + parallel_stage5 + pipeline_failure_status + pipeline_restart + b51_fallback)
- ✅ **全 suite 1002 PASS / 32 skipped** (跑全 tests/, 14:32 总耗时)
- ✅ 4 fail + 6 error 是 **pre-existing 与本次改动无关** (SQLite LONGTEXT dialect 兼容 / e2e 需 backend / 需登录 fixture, 跟 audit 报告"4 已有 fail 与本次无关"完全吻合)
- ✅ py_compile 所有改动文件 PASS
- ✅ Backend PID 82102 **未重启** (等 PM 决定何时重启)
- ✅ 0 越权 (严格在 PM 派活白名单内)

#### T20-13: status API 真实 shot 计数字段

**3 字段派生规则** (universal, 不破坏向后兼容):
- `shots_total`: chapter.storyboard_json 解析 shots count
- `shots_failed`: job.failed_shot_count (DB 直读)
- `shots_completed`: stage="completed" → shots_total; stage="image_generation" → 优先 regex "已生成 X/Y", 兜底 progress 反推 (75+20*X/Y); 其他 stage → 0; 早期 stage 全 null

**Frontend 收益** (Wave 2):
- 删除 message regex 解析 "已生成 X/Y" — 直接读 shots_completed
- ETA 算法可用 `(shots_total - shots_completed) * 80 / max_concurrent` 更准
- shots_in_flight 可派生

#### T20-14: ShotValidator Anthropic 退避重试

**核心常量**:
- `SHOT_VALIDATOR_RETRY_DELAYS_SEC = (2, 8, 30)` (类似 Seedream)
- `SHOT_VALIDATOR_RETRY_JITTER_RATIO = 0.30` (防 retry storm)
- `SHOT_VALIDATOR_RETRYABLE_STATUS_CODES = (429, 529, 503)`

**逻辑**:
- 仅对 429/529/503 + 文本兜底 "overloaded"/"rate limit" 退避
- 其他错误 (401/400/超大图) 立即 fail-open
- 总尝试 4 次 (1 原 + 3 重试), 仍失败才走 fail-open
- ERROR 级日志 `OVERLOAD_RETRY_EXHAUSTED_{code}` (退避耗尽), WARNING 级 `API_ERROR_SKIPPED` (其他)
- shot_id 从 shot dict 拿 (兜底 "?"), 便于日志追踪

**影响**: test17 v2 实测 18/18 Anthropic 调用 529 全 fail-open. 修后 529 应被重试覆盖大部分, ShotValidator 真验证率显著提升, B51 fallback 不再"形同虚设".

#### T20-19: Pipeline 单 Shot wall-clock timeout

**为什么 720s**:
- SeedreamGenerator 理论最坏: 4 attempts × 210s + 退避 (2+8+30+60s) = ~940s ≈ 15.7 min
- 720s = 12 min: SeedreamGenerator 自愈窗口 + 安全余量
- 略小于理论最坏, 但合理 cap, 不让单个假死 shot 拖死整批 Semaphore 槽位

**逻辑**:
- `asyncio.wait_for(generate_shot_image_phase2_safe, timeout=SHOT_WALL_CLOCK_TIMEOUT_SEC)` 包裹
- TimeoutError → 构造失败 result (success=False, error_kind="wall_clock_timeout") + ERROR 级日志
- 不 retry (已等 12 min, 再来无意义) → break 跳出 retry 循环
- partial_failure (T15-9) + Frontend "查看并重生" 可救

#### Ben 5 维度链路验证 (T20-13)

1. **函数定义** — ChapterStatus schema 加 3 字段 (Optional[int] 默认 None) ✅
2. **调用点** — chapters.py get_chapter_status (L298+) 唯一构造 ChapterStatus 处 ✅
3. **参数传递** — _shots_total/_shots_completed/_shots_failed 在 endpoint 内构造, 来自 chapter.storyboard_json + job.stage_message + job.failed_shot_count ✅
4. **数据流向** — regex 解析 message → progress 反推 → stage 派生 (3 层兜底) ✅
5. **消费点** — Frontend Wave 2 useETA.ts 可消费 (PM 已知, 等 W2 派活) ✅

---

## 2026-05-18

### TASK-T20-FIXBATCH-2 Backend #1 — T20-9 P0 + T20-8 P3 ✅ [2026-05-18 20:50 — Opus 4.7 max]

**任务**: T20-9 P0 ETA 数字偏快 (test18 second run Founder 反复反馈"4 分钟太快了, 实际剩 6 min") + T20-8 P3 UX-2 false positive + ending_id 字段

#### T20-9 P0 真根因 (5 维度调研)
1. backend `estimated_remaining_seconds` 字段已存在 (chapters.py:366), schema 已定义 — 不是 audit 说的"加新字段"
2. frontend useETA.ts L187 已 prefer backend value — STAGE_BUDGET_SECONDS fallback 仅 backend null 时触发
3. **真问题**: backend ETA 本身**算偏快**
   - chapters.py:344 fallback hardcoded `stage_progress=0.5` → 永远以"stage 半成"算
   - `per_shot_seconds = 60s` 过乐观 (实测 image_generation 含 retry + 长尾 ~80s/shot)
4. test18 second run 验证: 19 shots × 60 / 3 = 380s, 实测 540s, **低估 42%**
5. 修复后: 19 × 80 / 3 = 506s, 实测 540s, **低估 6%** (符合用户预期)

#### T20-8 P3
- UX-2 false positive: LLM 不知道 R6-2 设计 (用户选的 ending 已追加到 plot_points 末尾, 不在 selected_ending 字段)
- ending_id: PM 任务要求加，避免 LLM 偶尔漏写时 frontend `e.id` 拿不到值

#### 修改文件
1. `app/services/pipeline_orchestrator.py` — `build_stage_durations` per_shot 60 → 80 (含完整设计取舍注释)
2. `app/services/job_manager.py` — `calculate_eta_remaining_sec` per_shot 60 → 80 (双源 baseline 同步)
3. `app/api/chapters.py` — 1) import `_calculate_eta_with_progress` 2) fallback 用真实 global progress 3) status response 加 `actual_shot_count` + `max_concurrent` 透传字段
4. `app/api/projects.py` — confirm_outline UX-2 prompt 加 R6-2 设计说明 (plot_points[-1] 检查替代 selected_ending 字段检查)
5. `app/services/story_outline_generator.py` — 1) system_prompt 强制 ending_options 双字段 2) JSON 示例增加 ending_id 3) `_validate_outline` 兜底 normalization (LLM 漏写时补 ending_{i+1})
6. `app/schemas/chapter.py` — `ChapterStatus` 加 `actual_shot_count` + `max_concurrent` (Optional int)
7. `tests/test_t20_9_estimated_remaining.py` — **新建 17 case** (5 per_shot calibration + 3 concurrent scaling + 4 stage+progress + 1 helper sync + 4 robustness)
8. `tests/test_t20_8_outline_structure.py` — **新建 9 case** (6 ending normalization + 2 UX-2 prompt + 1 universal 跨故事)
9. `tests/test_d2_eta_parallel.py` — 旧 3 个 RISK-T14-4 测试更新 baseline 60→80 (硬编码假设必须同步)

#### Universal 视角
- T20-9: 5/19/29/50 shots × 1/3/6 concurrent × 任何 stage progress → universal 准确, 0 hardcode test18
- T20-8: 3/5 endings × 浪漫/悬疑/幽默 mood → universal 适配 R6-2 设计, 0 hardcode 特定故事

#### 验证
- ✅ py_compile 全部 6 文件 PASS
- ✅ 新单测 **26/26 PASS** (1.8s)
- ✅ Regression **132/132 PASS** (eta_calculation + d2_eta_parallel + status_authoritative + confirm_outline_wire)
- ✅ Backend HTTP 200, OpenAPI schema 含 `actual_shot_count` + `max_concurrent` + `estimated_remaining_seconds`
- ✅ 0 越权 (改动全在白名单 app/services/ + app/api/ + app/schemas/ + tests/)

#### API 契约通知 Frontend
**新字段**: ChapterStatus.actual_shot_count + max_concurrent (Optional int)
**Frontend 行动**: useETA.ts fallback 用 `actual_shot_count * 80 / max_concurrent` 替代 hardcoded 1440 (universal)

---

### TASK-T20-FIXBATCH-2 Backend #2 — T17-1 + T18-J + T19-9 + POST_BETA-5 ✅ [2026-05-18 21:00 — Sonnet 4.6]

**任务**: 4 个 RISK 串行修（2个P2 + 1个P3 + 1个POST_BETA）

**修改文件**:
1. `app/services/prompt_safety_advisor.py` — T17-1: extract_json_from_llm_response 替换旧 markdown 剥离
2. `app/services/alignment_service.py` — T18-J: Anthropic() → AsyncAnthropic() + 2 处 await
3. `app/api/chapters.py` — T18-J: Anthropic() → AsyncAnthropic() + await (Shot 调整端点)
4. `app/services/story_music_extractor.py` — T19-9: emotional_arc isinstance 防御
5. `app/services/image_generator.py` — POST_BETA-5: 3 dispatch 块加 refs=N (M portrait + K scene_ref)
6. `app/services/seedream_generator.py` — POST_BETA-5: 开始生成 log 加 ref 类型详情

**新测试文件**: 4 个，共 64 case，全 PASS

**验证**: py_compile PASS + 服务 PID 61003 HTTP 200

---

### TASK-T20-FIXBATCH T20-6 wiring — pipeline_orchestrator 1 行修复 ✅ [2026-05-18 17:15 — Sonnet 4.6]

**任务**: AI-ML 在 shot_validator.py 加了 `validate_shot(..., shot: Optional[dict] = None)` 参数实现 universal skip，但 pipeline_orchestrator.py 调用处没传 `shot=shot` → skip 完全无效。

**修复 (1 行)**:

`app/services/pipeline_orchestrator.py` L1285-1290，在 `validate_shot(...)` 调用末尾加：
```python
shot=shot,  # T20-6 v2: 传入完整 shot dict，让 universal skip 真正生效
```

**Ben 教训 5 维度链路验证**:
- 函数定义: `shot_validator.py:399` `validate_shot(..., shot: Optional[dict] = None)` ✅
- 调用点: `pipeline_orchestrator.py:L1285` — 唯一调用处（grep 确认）✅
- 参数传递: `shot` 变量在作用域内（L1233/L1275 已用到），加 `shot=shot` 后正确传入 ✅
- 数据流向: `should_skip_character_count_check(shot)` 现在真正被调用 ✅
- 消费点: `_is_fallback=True` / wide shot / no-char prompt → early return `valid=True` → 不再误报"角色数量不匹配" ✅

**验证**:
- py_compile PASS
- 30/30 ShotValidator universal skip 测试 PASS（`tests/test_shot_validator_universal_skip.py`）
- 4 维度内联验证 PASS (helper truthy/falsy + no-client path valid=True + grep wiring 存在)
- 服务重启: kill PID 53186 → 新 PID 53809 + curl /health → HTTP 200 `{"status":"healthy"}`
- 0 越权 (只改 `app/services/pipeline_orchestrator.py` 1 行)

**修改文件**: `app/services/pipeline_orchestrator.py` L1289 (加 `shot=shot,`)

---

### TASK-T20-FIXBATCH T20-3 — P0 招牌污染修复 (方案 A) ✅ [2026-05-18 16:15 — Sonnet 4.6]

**RISK-T20-3 (P0) test18 实证: 3 张 shot (5/8/13) 因招牌污染渲染出完整 location 描述**

**真根因**: `scene_reference_manager.py` `_detect_signage_name` L746-757 keyword fallback 不信任 Stage 1 LLM 决策:
- "陈默租住楼的雨夜楼道口" 含 "楼" → 命中 `_SIGNAGE_KEYWORDS_ZH` → 整段当招牌 → scene_ref.png 污染 → Shot 5/8/13 继承

**修复 (方案 A — Founder 决策)**: 删除 L746-757 整段 keyword fallback，只保留:
```python
if signage_text:
    return signage_text
return None
```

**验证**:
- py_compile PASS
- 5/5 universal 测试用例 PASS (signage_text 有值返回 / 办公楼无招牌 / 教学楼无招牌 / 陈默租住楼无招牌 / 出租屋无招牌)
- 693 pytest PASS (--ignore test_api_cost_log_table 已知 SQLite LONGTEXT 问题) + 0 新增 fail
- 服务重启 (新 PID 48774) + curl /health → HTTP 200 {"status":"healthy"}
- 0 越权 (只改 app/services/scene_reference_manager.py 1 个文件)

**修改文件**: `app/services/scene_reference_manager.py` L739-758 (_detect_signage_name 函数)

---

## 2026-05-15

### TASK-WAVE14-RISK-T19-7 — IMAGE_TOO_LARGE 真压缩 ✅ [2026-05-15 19:30 — Sonnet 4.6]

**RISK-T19-7 (P1) Wave 14 Backend #3**

**真根因**: Wave 11.4 target 4.5 MB binary × base64 膨胀 1.33 = ~6 MB base64，仍超 Anthropic 5 MB 限制。

**修复**:
- `app/services/shot_validator.py`: `_compress_for_claude` target 4.5 MB → 3.5 MB，resize 优先策略（8 级压缩 + 2 级极端 fallback），增强 logging（binary ratio + b64 estimate）
- `tests/test_image_compression_safety.py`: 新建 9 case（5.7/7/10/20 MB 真实场景 + base64 < 5 MB 验证 + resize 策略验证 + 安全余量理论）
- 9/9 新单测 PASS + 9/9 Wave 11.4 regression PASS（test_shot_validator_compression.py）

### TASK-WAVE14-RISK-T19-8 — B51 fallback 中文化补漏真根因 ✅ [2026-05-15 ~19:00 — Sonnet 4.6]

**RISK-T19-8 (P0) Wave 14 Backend #1**

**真根因**: LLM 主路径 3 次失败（B51 fallback 触发）的根因是 `_build_scene_prompt()` 传给 LLM 的 input 含多处中文来源，导致 LLM 在 image_prompt 中输出中文，触发 pipeline_schemas.py 中文比例 >5% 校验失败。

**LLM input 中文来源完整清单**:
1. `characters_json.name` — 中文角色名（"灰狐", "米莉" 等）→ Wave 14: 改用 name_en
2. `characters_json.clothing_summary` — top/bottom 全中文 → Wave 14: `_extract_english_from_field()` 提取英文
3. `scene_json.scene_heading` — 含中文（"白桦树下"）→ Wave 14: `_contains_chinese` 检测替换占位
4. `scene_json.atmosphere` — 含中文子字段 → Wave 14: `_atmosphere_to_str()` 过滤后传字符串
5. `scene_json.action_beats[].action` — 全中文（保留，LLM 需理解）→ prompt 开头加铁律规则
6. `scene_json.narration`/`dialogue_beats` — 全中文（保留，TTS用）→ 同上

**修复**:
- 文件: `app/services/storyboard_director.py`
  - 新增 `_extract_english_from_field()` helper
  - `_build_scene_prompt()` characters_json 英文化（name → name_en, clothing → 英文提取）
  - `_build_scene_prompt()` scene_json 中文防御（scene_heading 替换, atmosphere 过滤）
  - `_build_scene_prompt()` prompt 开头加 "CRITICAL: IMAGE_PROMPT MUST BE WRITTEN ENTIRELY IN ENGLISH" 铁律
- 新建: `tests/test_b51_fallback_no_chinese.py` — 20/20 PASS
- Wave 12+13 regression: 50/50 PASS（atmosphere + scene_heading + dict_compat 全过）
- py_compile: PASS | 0 越权

---

### TASK-WAVE14-RISK-T19-5 — BGM dict/str 双修 ✅ [2026-05-15 17:55 — Sonnet 4.6]

**RISK-T19-5 (P1) Wave 14 Backend #2**

- 文件 1: `app/services/story_music_extractor.py` — L416-432 visual_tone isinstance 防御 (dict/str/else 三分支) + L488-511 atmosphere isinstance 防御 (dict/str/else 三分支，跟 Wave 12 _atmosphere_to_str 同模式)
- 新建: `tests/test_bgm_dict_str_defense.py` — 15 case (6 visual_tone + 6 atmosphere + 2 混合 + 1 真实 test19 数据回归)
- 验证: py_compile PASS + 15/15 新单测 PASS + 152/152 regression PASS (Wave 10-13 全覆盖) + 0 越权
- Bonus 发现: `emotional_arc` L444 同样模式但风险较低，已记录给 PM

---

### TASK-WAVE13-RISK-T19-4 — scene_heading 中文防御双修 ✅ [2026-05-15 17:15 — Sonnet 4.6]

**RISK-T19-4 (P0) Wave 13 Backend**

- 文件 1: `app/services/screenplay_writer.py` — Batch + 逐 scene 两处 CRITICAL 约束块扩展为 "ENGLISH ONLY RULES"，新增 Rule 1 scene_heading 英文约束 + 对比示例；JSON 示例中 scene_heading 占位改为 "ENGLISH ONLY — e.g. 'EXT. Birch grove...'"
- 文件 2: `app/services/storyboard_director.py` — L682-692 新增 scene_heading 中文检测防御 (复用 Wave 12 `_contains_chinese()`)，含中文时替换为 `f"Scene {scene_id}"` + WARN 日志
- 新建: `tests/test_scene_heading_chinese_defense.py` — 18 case (5 含中文防御 + 3 英文通过 + 5 _contains_chinese 边界 + 5 Wave 12 atmosphere regression)
- 验证: py_compile 2 文件 PASS + 18/18 新单测 PASS + Wave 12 regression 39/39 PASS + Wave 10/11 regression 155/155 PASS + 0 越权
- 其他中文来源排查: B51 fallback 路径 scene_heading/atmosphere_str 全封堵，narration_segment (TTS用，允许中文)，chars_in_scene (英文 ID)

---

### TASK-WAVE12-RISK-T17-8 — Pipeline 失败原地重启从 Stage 4 ✅ [2026-05-15 16:30 — Sonnet 4.6]

**RISK-T17-8 (P0) Wave 12 Backend #2**

- 文件 1: `app/services/pipeline_orchestrator.py` — `run()` 新增 `start_from_stage: int = 1` 参数 + disk 加载块 + Stage 1-3 skip guards + R4-1/R4-2 skip guards
- 文件 2: `app/api/chapters.py` — 新增 `_parse_failed_stage_number()` + `POST /{chapter_number}/restart-from-failed-stage` endpoint + `_run_restart_pipeline_task()` 后台任务
- 新建: `tests/test_pipeline_restart.py` — 14 case (5 parse + 4 disk loading + 2 utility + 3 R4 skip flags)
- 验证: py_compile 2 文件 PASS + 14/14 新单测 PASS (1.02s, 0 hang) + Wave 11.x 保护行验证 PASS + 0 越权

---

### TASK-WAVE12-RISK-T19-1 — atmosphere 中文防御双修 ✅ [2026-05-15 15:55 — Sonnet 4.6 xhigh]

**RISK-T19-1 (P0) Wave 12 Backend #1**

- 文件 1: `app/services/screenplay_writer.py` — Batch + 逐 scene 两处 prompt 模板强制 atmosphere 全英文 (CRITICAL 约束块 + ❌/✅ 示例)
- 文件 2: `app/services/storyboard_director.py` — L323-365 新增 `_contains_chinese()` + 增强 `_atmosphere_to_str()` 防御中文 (str/dict 两个分支均处理，含中文跳过 + WARN 日志)
- 新建: `tests/test_atmosphere_chinese_defense.py` — 22 case (5 _contains_chinese + 8 中文防御 + 9 Wave10.1 regression)
- 验证: py_compile 2 文件 PASS + 22/22 新单测 + 10/10 Wave10.1 回归 + 7/7 b58 回归 + 0 越权

---

## 2026-05-14

### TASK-RISK-NEW-2-CONFIG-UNIFY — IMAGE_GENERATION_TIMEOUT 配置统一 ✅ [2026-05-14 23:40 — Sonnet 4.6]

- 文件 1: `app/config.py` L33 — `IMAGE_GENERATION_TIMEOUT: int = 120` → `int = 210` + Wave 11.4 注释
- 文件 2: `app/services/seedream_generator.py` L103 — `SEEDREAM_TIMEOUT_SEC = 210` → `= settings.IMAGE_GENERATION_TIMEOUT` (从 settings 读)
- NB2 路径: 未动 (image_generator.py 不消费 IMAGE_GENERATION_TIMEOUT, grep 全项目确认)
- 验证: py_compile 2 文件 PASS + 56/56 regression PASS + 0 越权

### TASK-WAVE11.4-TIMEOUT-210 — SEEDREAM_TIMEOUT_SEC 180→210 ✅ [2026-05-14 22:40 — Sonnet 4.6]

- 文件: `app/services/seedream_generator.py` L103
- 改前: `SEEDREAM_TIMEOUT_SEC = 180`
- 改后: `SEEDREAM_TIMEOUT_SEC = 210  # Wave 11.4 调研: 防 177s long-tail 偶发超时, +30s buffer`
- 验证: py_compile PASS + 56/56 regression PASS + grep 0 匹配 180 + 0 越权

---

### TASK-WAVE11.2-T18G-T18E — Wave 11.2 404 风暴 + preview API 修复 ✅ [2026-05-14 19:30 — Sonnet 4.6 xhigh]

**修复 2 个 RISK（0 文件冲突，0 越权）**

| RISK | 文件 | 行号 | 改动 |
|------|------|------|------|
| T18-G (P1) | `app/api/chapters.py` | L415-446 (story) + L568-574 (storyboard) | 无数据时 200+empty (取代 404) |
| T18-E (P1) | `app/api/projects.py` | L1556-1660 | 新增 `GET /{project_id}/preview` 聚合端点 |
| 回归更新 | `tests/test_status_authoritative.py` | L317-326 | test name → `test_truly_no_data_returns_empty` |
| 新单测 | `tests/test_wave11_2_backend_fixes.py` | 新建 259 行 | 22 单测 (12 T18-G + 7 T18-E + 3 not-found 不变) |

**验证**: py_compile 3 文件 PASS + **22/22 单测 PASS** + **134/134 regression PASS** + ⚠️ L1878-1890 未动 ✅

---

### TASK-WAVE11.3-T17-5-ETA — Wave 11.3 ETA 算法全面深挖修复 ✅ [2026-05-14 ~19:00 — Sonnet 4.6 xhigh]

**修复 RISK-T17-5: ETA 算法根因 + stage-switch reset + 单测覆盖**

| 改动 | 文件 | 行号 |
|------|------|------|
| 新增 `calculate_eta_remaining_sec()` helper | `app/services/job_manager.py` | L18-148 |
| stage-switch ETA 单调 guard reset (`_last_stage` + reset on switch) | `app/services/job_manager.py` | L375-395 |
| progress_callback 用新 helper 替换内联逻辑 | `app/services/job_manager.py` | L411-428 |
| 新建 `tests/test_eta_calculation.py` | `tests/test_eta_calculation.py` | 全文 |

**验证**: py_compile PASS + **50/50 unit test PASS** + regression 7/7 PASS + 0 越权

**chapters.py 集成 snippet**: 见 PM 群聊消息（Wave 11.3 完成通知）

---

### TASK-WAVE11.1-T18F-T17-9 — Wave 11.1 P0 角色一致性双修 ✅ [2026-05-14 17:30 — Sonnet 4.6]

**修 2 个 P0 角色一致性 RISK**:

| RISK | 文件 | 改动 |
|------|------|------|
| T18-F (P0) | `app/api/chapters.py` L1878-1890 | regenerate_shot: 每角色传 portrait + fullbody 两张（之前只传 1 张）|
| T17-9 (P0) | `app/api/projects.py` L1288-1309 | adjust_character: 传 existing portrait 作 portrait_ref 给 generate_character_reference（之前 4 参数无 portrait_ref）|

**验证**: py_compile 2 文件 PASS + 82/82 regression PASS (含 test_shot_regenerate_persistence/test_architecture/test_status_authoritative 等) + 0 越权

---

### TASK-WAVE11.1-T18H-SHOTVALIDATOR-COMPRESSION — Wave 11.1 P1 ShotValidator 5MB 压缩修复 ✅ [2026-05-14 17:10 — Sonnet 4.6 xhigh]

**修 1 个 RISK (T18-H)**:
- **图片压缩**: `_compress_for_claude()` 在 base64 编码前压缩 PNG 至 < 4.5MB（PIL JPEG 多级 quality + 降分辨率兜底）
- **日志格式修复**: Exception 时 reason 改为 `"API_ERROR_SKIPPED"` 或 `"IMAGE_TOO_LARGE_SKIPPED"`（不再粘贴完整 error stack），WARNING level logger
- **metric 跟踪**: `validator_skipped_count` 模块级计数器，每次 fail-open 跳过时递增

**改动**:
- `app/services/shot_validator.py`: 新增 import logging + logger + validator_skipped_count + Exception handler 改写
- `tests/test_shot_validator_compression.py`: 新建，9 case

**验证**: py_compile PASS + 9/9 单测 PASS + 42/42 regression PASS + 0 越权

---

### TASK-WAVE10-P1A-BACKEND-FIXES — Wave 10 Phase 1A 4 RISK 双修 ✅ [2026-05-14 — Sonnet 4.6 xhigh]

**修 4 个 RISK**:
- T16-4 (P0 CRITICAL): B58 ConfirmScenes merge 而非 replace，保留 action_beats
- T16-6 (P0): Pipeline 失败时 chapter.status 写 "failed" 不 "completed"（job_manager L373 修复）
- T16-8 (P2): _strip_markdown_json_fence() 新增 + UX-2 解析前显式调用
- T16-10 (P1): 顺解（GET /story 已返完整 scenes，根因是 T16-4 使 DB 简化）

**新单测 21/21 PASS + 60 regression PASS**

---

## 2026-05-13 21:50

### TASK-WAVE9-P2-BACKEND-STATUS-AUTHORITATIVE — DEC-030 Wave 9 Phase 2 主任务 ✅ [2026-05-13 21:50 — Opus 4.7 xhigh]

**DEC-030 (Ben 方案 A) 落地: backend status endpoint 成为 frontend state 的 single source of truth。顺解 4 RISK (T15-3 + T15-7 + T15-8 + T15-9)。**

**改动 5 个文件**:

| 文件 | 位置 | 改动 |
|------|------|------|
| `app/schemas/chapter.py` | L1-50 | 新增 `HydrateHints` class（endpoint / display_field / expected_data_shape）+ `ChapterStatus` 加 6 字段（ui_phase / hydrate_hints / characters_confirmed / scenes_confirmed / storyboard_ready / outline_ready）|
| `app/api/chapters.py` | L19 import + L27-156 helpers + L264-279 no-job 路径 + L336-356 with-job 路径 + L407-426 /story 顺序调整 | (1) 新增 `_derive_ui_phase()` 8-phase 状态机 (2) 新增 `_build_hydrate_hints()` 4 endpoint 映射 (3) status endpoint 两个返回路径都填 6 新字段 (4) GET /story 优先检查 scenes_json，顺解 T15-3 |
| `app/services/job_manager.py` | L139-189 helper + L371 wiring | 新增 `increment_failed_shot_count(job_id)` async helper（短 session + 非阻塞 + max(0,..)防负数）；run_story_generation_task 调 pipeline.run 加 `job_id=job_id` |
| `app/services/pipeline_orchestrator.py` | L317 signature + L1276-1287 single fail + L1359-1372 gather exception | `pipeline.run()` 加 `job_id: Optional[int] = None`；Stage 5 单 shot 失败 + gather exception 两 path 都立即 await `increment_failed_shot_count(job_id)` |
| `tests/test_status_authoritative.py` (新建, 535 行) | — | 5 大类 44 单测：ui_phase 派生 (18) / hydrate_hints (9) / GET /story scenes_review (5) / mid-stage failed_count async mock (4) / schema 退化检测 (8) |

**验证 (按 feedback_carpet_review_deep_dive 8 维度全 PASS)**:

- ✅ py_compile 4 文件 PASS
- ✅ test_status_authoritative.py 44/44 PASS
- ✅ test_shot_regenerate_persistence.py 9/9 PASS（PR-A regression 不退化）
- ✅ test_architecture.py 7/7 PASS（不退化）
- ✅ test_wave6_full_regression.py 32/32 PASS（不退化）
- ✅ test_d2_eta_parallel.py 7/7 PASS（不退化）
- ✅ 总计 **99/99 PASS** (44 new + 16 regression core + 39 wave6/d2)
- ✅ 调用链路 9 层 verify: pipeline.run(job_id) → _generate_one_shot fail path → increment_failed_shot_count → DB commit
- ✅ 0 越权: frontend / storyboard_director.py / storyboard_prompts.py / `.team-brain/team_ben/` 未碰

**关键设计决策**:

1. **`ui_phase` 8 phase 状态机** — 完整覆盖 input → outline_review → char_review[_pending] → scene_review[_pending] → storyboard_running → shot_generating → completed
2. **`hydrate_hints` 4 endpoint 映射** — char_review → /characters / scene_review → **/story（顺解 T15-3，不是 /storyboard）** / shot_generating+completed → /storyboard / 其他 → None
3. **GET /story 顺序调整** — 原 chapter.status='generating_story' 直接 404 → 改为先检查 chapter.scenes_json 非空（Stage 3 已完成）。R4-2 阶段 frontend hydrate /story 立刻拿到 scenes 数据，永久治本 T15-3
4. **mid-stage failed_count 通过 job_id 透传** — 不污染 progress_callback 语义，单一封闭传递路径；pipeline.run(job_id=N) → Stage 5 失败 → increment_failed_shot_count(N) → DB 实时更新；T15-9 mid-stage 实时反映

**顺解 RISK 状态**:
- ✅ T15-3 P0 CRITICAL: GET /story 在 scenes_ready 阶段真返 scenes
- ✅ T15-7 P1: backend ETA 计算正确（frontend Wave 9 P2 自己改 stage 切换重置 ref，backend 不变）
- ✅ T15-8 P0 UX: backend 提供 ui_phase + characters/scenes_confirmed，frontend Wave 9 P2 改 subPhase 派生
- ✅ T15-9 P2: mid-stage failed_shot_count 实时累加 + partial_failure 即时反映

**API 契约变更**:
- `GET /chapters/{n}/status` response 加 6 字段（向后兼容 — 老 frontend 不读这 6 字段也能工作）
- `GET /chapters/{n}/story` 在 scenes_ready 阶段返 200 + scenes（之前 404）
- `pipeline.run()` 加 `job_id: Optional[int] = None` 参数（job_manager 已 wiring）

**待 PM**:
1. 重启 backend 让改动生效（Python 模块缓存）
2. 追加 TEAM_CHAT 完成段（PM 代写，见 backend-progress/current.md 底部 paste）
3. PENDING.md 标 T15-3 + T15-9 ✅
4. Spawn Wave 9 Phase 2 Frontend agent（Opus xhigh ~3h）— Frontend 用 ui_phase + hydrate_hints 改造 state 派生

---

## 2026-05-13 21:30

### TASK-WAVE9-P3-BACKEND-STORYBOARD-SCHEMA-FIX — RISK-T15-14 ✅ [2026-05-13 21:30 — Sonnet 4.6 xhigh]

**test15 实测暴露：Shot 21/22 的 characters_in_scene=None, shot_type=None 字段空（LLM 偶尔遗漏顶层字段）。**

**改动 1 文件，新建 1 单元测试**:

| 文件 | 位置 | 改动 |
|------|------|------|
| `app/services/storyboard_director.py` | `_build_scene_prompt` JSON 示例 | 加 `shot_type` / `camera_angle` / `characters_in_scene` 字段 + REQUIRED 说明块 |
| `app/services/storyboard_director.py` | `_build_prompt` JSON 示例 | 同步加三个字段到全剧本模式 JSON 示例 |
| `app/services/storyboard_director.py` | `_validate_storyboard` post-process | 三字段 fallback 逻辑（从 camera.shot_size/camera.angle/characters_visible 派生）|
| `tests/test_storyboard_director_schema_fix.py` | 新建 | 13 个单元测试（RISK-T15-14 回归 + Shot 21/22 场景）|

**验证**:
- ✅ py_compile storyboard_director.py PASS
- ✅ `pytest tests/test_storyboard_director_schema_fix.py` 13/13 PASS
- ✅ 0 越权（不改 chapters.py / pipeline_orchestrator.py / frontend）

**根因**:
- `_build_scene_prompt` 和 `_build_prompt` 的 JSON 示例中，顶层 `shot_type`/`camera_angle`/`characters_in_scene` 字段缺失 → LLM 不知道要输出 → 偶尔漏填
- 下游消费方（统计/frontend 显示）读 storyboard.shots[].characters_in_scene 时拿到 None

**修复策略**:
1. Prompt 强化：JSON 示例加三字段 + 在 REQUIRED FIELDS 段落明确说明不得省略
2. Post-process 补救：`_validate_storyboard` 检测 None 时从 camera.shot_size / camera.angle / character_direction.characters_visible 派生填充

---

## 2026-05-13 21:00

### TASK-WAVE9-P1-PRA-REGENERATE-FIX — RISK-T15-12 + T15-13 双修 ✅ [2026-05-13 21:00 — Sonnet 4.6 xhigh]

**test15 实测暴露：Shot 22 重生成功后 status 仍显 22/23、5_image_results.json 仍失败、ApiCost project_id=None。一次 PR 双修 3 个问题。**

**改动 1 文件，新建 1 单元测试**:

| 文件 | 行号 | 改动 |
|------|------|------|
| `app/api/chapters.py` | L1771 | `generate_shot_image_phase2_safe` 调用加 `project_id=project.id` 参数（RISK-T15-13b）|
| `app/api/chapters.py` | L1829-1860 | 成功后回写 `5_image_results.json`：找 shot_id 条目 → success=True, error=None, image_path/url/generation_time 更新（RISK-T15-13a）|
| `app/api/chapters.py` | L1862-1880 | 成功后查最新 GenerationJob → `failed_shot_count = max(0, count-1)` + `partial_failure = (count > 0)` + commit（RISK-T15-12）|
| `tests/test_shot_regenerate_persistence.py` | 新建 | 9 个单元测试覆盖 3 个修复点的 happy path + 边界 case |

**验证**:
- ✅ py_compile chapters.py PASS
- ✅ `pytest tests/test_shot_regenerate_persistence.py` 9/9 PASS
- ✅ `pytest tests/test_architecture.py` 7/7 PASS（无退化）
- ✅ 0 越权（不改 pipeline_orchestrator.py / frontend / team_ben）

**根因**:
- RISK-T15-12: chapters.py regenerate endpoint 成功 path 缺少 DB job 更新（成功后没扣 failed_shot_count）
- RISK-T15-13a: regenerate endpoint 成功后没读写 5_image_results.json
- RISK-T15-13b: `generate_shot_image_phase2_safe()` 调用未传 `project_id` → seedream_generator `_kwargs.get("project_id")` = None → ApiCostLogger 记 None

---

## 2026-05-13

### TASK-WAVE7-ROUND2 ETA 调用点修复 ✅ [2026-05-13 — Sonnet 4.6 xhigh]

**PM Explore 审查发现 Task 3 ETA 动态算法是死代码：signature 加了新参数，但调用方 0 传参 = 用 default 值 = 跟静态 ETA 一样。Round 2 彻底修复 3 个调用点。**

**改动 3 文件**:

| 文件 | 改动 | 说明 |
|------|------|------|
| `app/api/chapters.py` L143-195 | fallback 路径真传 3 个新参数 | 从 `chapter.storyboard_json` 解析 actual_shot_count（兜底 18），从 `project.confirmed_outline_json/raw_outline_json` 解析 unique_location_count（兜底 2），从 `settings.IMAGE_MAX_CONCURRENT` 拿 max_concurrent（兜底 3）|
| `app/services/job_manager.py` L207-256 | progress_callback 闭包新增 3 个 mutable state 变量 + 新可选参数 | `_dyn_shot_count[18]` + `_dyn_location_count[2]` + `_dyn_max_concurrent[3]`，callback 收到新参数时更新，`_est()` 调用时真传值 |
| `app/services/pipeline_orchestrator.py` L854 + L1327 | image_preparation 和 image_generation 两处 progress_callback 传入 actual_shot_count / unique_location_count / max_concurrent | Stage 4 完成后立即传 shot_count + outline.unique_locations count + settings.IMAGE_MAX_CONCURRENT |

**单元测试** `tests/test_d2_eta_parallel.py` 新增 3 个 Round 2 case（合计 7/7 PASS）:

| Test | 入参 | 期望 image_gen ETA | 验证目的 |
|------|------|--------------------|---------|
| `test_estimate_remaining_dynamic_shot_count_18` | 18 shots, concurrent=3 | 360s | dynamic 与静态基线一致 |
| `test_estimate_remaining_dynamic_shot_count_26` | 26 shots, concurrent=3 | 520s | 26 > 18，dynamic 真生效 |
| `test_estimate_remaining_dynamic_max_concurrent_1` | 18 shots, concurrent=1 | 1080s | serial vs parallel ETA 不同 |

**测试加载方式**: 从 pipeline_orchestrator.py 源码 exec() 提取 3 个纯 Python 函数，绕过 pydantic_settings/google-genai 等 SDK 依赖（与 wave6 regression 静态分析方式互补）。

**验证**: py_compile 4 文件全通过 + pytest test_d2_eta_parallel.py 7/7 PASS + pytest test_architecture.py 7/7 PASS（无退化）

### TASK-WAVE7-BACKEND ✅ [2026-05-13 — Sonnet 4.6 xhigh]

**5 任务完成（RISK-T14 波次修复）**

| 任务 | 优先级 | 文件 | 改动 |
|------|--------|------|------|
| **Task 1** RISK-T14-7 GET /chapters/1/story 条件修复 | 🔴 P0 | `app/api/chapters.py` | Stage 3 完成（scenes_json 非空）即返 200 + scenes，不再等 full_script |
| **Task 2** RISK-T14-5-v2 Pipeline mid-stage update | 🟡 P1 | `app/services/pipeline_orchestrator.py` | Stage 2/3 启动时立即 update jobs；R4-1/R4-2 每 30s update；角色参考图每张完成后 update |
| **Task 3** RISK-T14-4 ETA 算法重写 | 🟡 P1 | `app/services/pipeline_orchestrator.py` | 新增 `build_stage_durations(actual_shot_count, unique_location_count, max_concurrent)` 动态计算；`estimate_remaining()` 改用动态字典；character_ready/scenes_ready 设为 0（不含 R4 等待时间） |
| **Task 4** RISK-T14-9 移除 O-2 截断（DEC-028） | 🟡 P1 | `app/services/storyboard_director.py` | 移除 18/36/60 shots 截断逻辑，LLM 生成多少跑多少 |
| **Task 5** RISK-T14-13-backend confirm-outline warnings | 🟡 P1 | `app/api/projects.py` | 返回 `inconsistency_warnings: [{type, message, affected_field}]` + 保留旧 `warnings` 字段兼容 |

**验收**: ✅ py_compile 4 文件 PASS + pytest test_architecture 7/7 PASS + test_d2_eta_parallel 4/4 PASS + 0 越权

---

## 2026-05-12

### TASK-T13-BACKEND-FIRSTBATCH ✅ [2026-05-12 17:30 — Sonnet 4.6 xhigh，PM 代写]

**5 任务一次性完成**（PM 16:30 派 → 17:30 完成 = 1h）

| 任务 | 优先级 | 文件 | 改动 |
|------|--------|------|------|
| **A1** DB pool 配置根治 BUG-T13-MYSQL-STALE + DB-POOL-EXHAUSTION | 🔴 P0 | `app/database.py` | 加 `pool_size=10, max_overflow=20`（原有 `pool_pre_ping=True, pool_recycle=1800` 已存在）|
| **A2-backend** POST /api/_client_log endpoint | 🔴 P0 | `app/api/client_log.py` (新建) + `app/api/__init__.py` | prefix=`/api`，无 auth，写 `logs/client.log` 追加每行一条 JSON |
| **D1** UX-2 LLM JSON 解析修复 | 🟡 P2 | `app/api/projects.py` confirm_outline | 替换 3 行自定义 ` ``` ` split 为 `_llm_helpers.extract_json_from_llm_response`（4 策略容错） |
| **D2** ETA 并行加速修复 | 🟡 P2 | `app/services/pipeline_orchestrator.py` | `STAGE_DURATIONS["image_generation"]` 420→360（18×60/3，注释解释 max_concurrent=3） |
| **C1-backend** confirm-scenes alias | 🔴 P0 | `app/api/projects.py` | 新增 project-level alias `POST /{project_id}/confirm-scenes` 转发 chapter_number=1，原 chapter-level 兼容 |

**新建测试**: `tests/test_d2_eta_parallel.py`（4 断言）

**验收**: ✅ py_compile 全 6 文件 + pytest 4/4 PASS + 0 越权 + 共享文档完整无冲突

**PENDING.md 已标 ✅**: 5 个 bug + TASK-CLIENT-LOG-PIPE backend 部分（17:30 backend agent 自己 Edit）

详见 TEAM_CHAT.md [2026-05-12 17:30] @backend → @pm 段。

---

### B59-hotfix — BUG-LLM-JSON-PARSE-MARKDOWN-UNCLOSED ✅ [2026-05-12]

**根因**: LLM 长输出（13443字符）被 max_tokens 截断，结尾 ``` 缺失，正则匹配失败 → Stage 2 crash
**新建**: `app/services/_llm_helpers.py` — 通用 `extract_json_from_llm_response()`，4 策略容错（未闭合 ``` 优先）
**修改**: 4 个 LLM 服务 `_extract_json` 全部委托给 helper
**验收**: py_compile 5/5 + pytest 7/7 + 32/32 + mock 6/6

### B58-followup HOTFIX — BUG-CLOTHING-SCHEMA-HAIKU-STR ✅ [2026-05-12]

**根因**: Haiku adjust prompt 缺 clothing schema 约束 → str 输出 → Stage 3 crash
**修改**: screenplay_writer.py (×2) + storyboard_service.py (×3) + projects.py Haiku prompt + schema 验证
**验收**: py_compile 3/3 + pytest 7/7 + 32/32 + manual test

---

## 2026-05-11

### Wave 6 — 5 bug 一次性闭环 ✅ [2026-05-11 19:00-20:30]

**任务来源**: PM 派活（Founder 4 决策：场景确认要倒计时 / Shot 重试 P2 修 / 一次性 7 bug 全修 / Backend 用 Opus 4.7 xhigh）

**5 bug 全完成**:

| Bug | 优先级 | 状态 |
|-----|--------|------|
| BUG-B52-CASCADE-V2-INCOMPLETE | 🔴 P0 | ✅ |
| BUG-SCENES-CONFIRM-MISSING | 🔴 P0 | ✅ |
| BUG-MUREKA-BLOCK-EVENT-LOOP | 🟡 P1 | ✅ |
| BUG-ETA-DISAPPEAR-AT-STAGE-EDGE | 🟡 P1 | ✅ |
| BUG-SHOT-RETRY-NETWORK-FRAGILE | 🟢 P2 | ✅ |

**变更文件（9 个）**:

1. `alembic/versions/005_add_scenes_confirmed_to_projects.py` (新建)
2. `app/models/project.py` (加 `scenes_confirmed` 列)
3. `app/schemas/project.py` (加 `scenes_confirmed` 字段)
4. `app/api/projects.py` (serialize 暴露 + `ConfirmScenesRequest` schema + `POST /confirm-scenes` 端点 + `start_generation` 重置)
5. `app/services/pipeline_orchestrator.py` (B52-fix v3 reload + R4-2 wait loop + STAGE_DURATIONS 完善 + estimate_remaining 兜底)
6. `app/services/job_manager.py` (progress_callback 计算 ETA + 单调 guard + 写 job.estimated_seconds)
7. `app/api/chapters.py` (status 端点优先用 job.estimated_seconds)
8. `app/services/music_generation_service.py` (aiohttp async 改造 — Mureka 不阻塞 event loop)
9. `app/services/seedream_generator.py` (IncompleteRead 退避 2/8/30/60s + jitter)

**验证**:
- ✅ py_compile 全 9 文件
- ✅ pytest tests/test_architecture.py → 7/7
- ✅ smoke import 全通过（含 scenes_confirmed 字段 / STAGE_DURATIONS 完整 / _call_mureka 真 async / Seedream retry delays 正确 / ConfirmScenesRequest 正常）
- ✅ grep 真接通所有改动 — 详 current.md "验证清单"段

**关键决策**:
- B52 reload 只在 `confirmed=True` 时触发（超时不 reload，因为超时意味着用户没 adjust）
- 整体替换 in-memory characters（不做字段级合并）— chapter.characters_json 是 adjust 完整快照，未被 adjust 的角色保留原值，Shot 7 王阿姨黑发不会被误改
- R4-2 wait loop 与 R4-1 完全对称（2s 轮询 + 1800s 超时 + 每 30s 日志 + 超时自动继续 + reload scenes_json）
- Mureka 用 aiohttp（已是依赖）不用 to_thread（避免 SSL/certifi 上下文丢失）
- ETA 三处兜底协同：STAGE_DURATIONS 完整化 / estimate_remaining 不抛 KeyError / progress_callback 真计算 ETA + 写 job.estimated_seconds / chapters.py 优先读 job 字段
- Seedream 退避只改网络层 except，HTTP 5xx 退避保留（瞬时通常 2s 够）

**风险点**:
1. Alembic 005 必须先跑（PM 部署职责），否则 confirm-scenes 报 SQLAlchemy Column 错误
2. Backend 需要 kill+restart 让代码生效
3. R4-2 1800s 超时与 Frontend 60s 倒计时设计协同 — frontend 内自动 confirm，1800 是兜底
4. Frontend hydrate 应改读 `project.scenes_confirmed` 真字段（不再 heuristic）— @frontend 任务

**派活上下文**: PENDING.md 7 bug 完整证据 + spawn 派活信息

**Founder 4 决策**:
1. 场景确认页要倒计时（推荐 60s）→ Frontend 实现
2. Shot 重试 P2 修（顺手做）→ Backend 已修
3. 一次性 7 bug 全修，Tester 分轮验证
4. Backend 用 Opus 4.7 + xhigh thinking → 已按 Founder 要求执行

**Tester 等 3 agent 完成后 spawn**：详 PENDING.md 各 BUG-* 验收清单

---

### Wave 5 — 5 件 P0/P1 修复（历史欠账补完） ✅ [2026-05-11 16:30-18:01]

**任务来源**: PM Wave 5 派活（test11 实测发现 cascade 问题 + URL 不回弹）

**5 修复点**:

| Bug | 文件 | 行号 |
|-----|------|------|
| B52+B56 Haiku prompt 强化 | app/api/projects.py | L956-982 |
| B57 adjust 后重生 fullbody | app/api/projects.py | L1092-1126 |
| B52 cascade confirm_outline | app/api/projects.py | L571-600 |
| B57 regenerate_portrait 后重生 fullbody | app/api/projects.py | L1249-1298 |
| B49 characters_confirmed 暴露 | app/api/projects.py L204 + app/schemas/project.py L99 |  |
| B56 CharacterDesigner description 字段 | app/services/character_designer.py | L213 |
| B56 _validate_characters fallback | app/services/character_designer.py | L313-324 |
| B52 cascade Stage 4 physical_summary | app/services/storyboard_director.py | L1194-1199 |
| B51 v2 3 次重试 + fallback shot | app/services/storyboard_director.py | L549-671 |

**B52 真因链全修**（红发 cascade）:
```
Founder 改"红发"
→ /adjust Haiku prompt 改 description + physical [B52+B56 修 L956-982]
→ fullbody 同步重生 → 亚麻青 fullbody 参考图 [B57 adjust 修 L1092-1126]
→ Stage 4 physical_summary 优先读 description [B52 cascade Stage4 修]
→ Stage 5 Seedream 生新发色 shot
```

另两个同类入口也已修:
- `/regenerate-portrait` 后 fullbody 不重生 → B57 修 L1249-1298
- `confirm_outline` 时 description 不同步到 chapter.characters_json → B52 修 L571-600

**Wave 5 漏修点**：Pipeline in-memory `characters` 变量不 reload — 详见 Wave 6 B52-fix v3 (L5) 修复。

---

## 2026-05-09

### B33 user_selected_mood Stage A + B34 LLM 事务外 ✅ [2026-05-09 15:00-15:22]

**任务来源**: PM xhteam 派 B33 + B34

**B33 — user_selected_mood 移到 Stage A（项目创建时）**

9 个文件变更：

| 文件 | 行范围 | 变更摘要 |
|------|--------|---------|
| `alembic/versions/003_add_user_selected_mood_to_projects.py` | 新文件 | migration 003：`projects` 表加 `user_selected_mood VARCHAR(32) DEFAULT NULL` |
| `app/models/project.py` | 新增列 | `user_selected_mood: Mapped[Optional[str]]` DB 列定义 |
| `app/schemas/project.py` | ProjectCreate / ProjectDetail | `user_selected_mood: Optional[str] = None` 新增字段 |
| `app/api/projects.py` (create_project) | create 逻辑 | `project.user_selected_mood = data.user_selected_mood` 持久化到 DB |
| `app/api/projects.py` (generate_outline) | outline 注入 | 将 `user_selected_mood` 传给 `StoryOutlineGenerator.generate()` |
| `app/services/story_outline_generator.py` | generate() 签名 | 接收 `user_selected_mood` 参数，若有值注入 MANDATORY 约束块强制 LLM 设置 mood/visual_tone.overall_mood |
| `app/services/story_music_extractor.py` | extract_story_for_music | `overall_mood` 优先级链：user_selected_mood > confirmed_outline.user_selected_mood > visual_tone.overall_mood |
| `app/services/music_generation_service.py` | generate_bgm_for_chapter | 接收并透传 `user_selected_mood` 参数 |
| `app/api/projects.py` (start_generation) + `job_manager.py` + `pipeline_orchestrator.py` | pipeline 调用链 | `user_selected_mood` 全链透传：start_generation → _run_generation_in_background → run_story_generation_task → pipeline.run → generate_bgm_for_chapter |

**B33 调用链（完整）**:
```
POST /api/projects/ (ProjectCreate.user_selected_mood)
  → Project.user_selected_mood (DB 列)
    → generate_outline → story_outline_generator.generate(user_selected_mood)
       → LLM MANDATORY 约束注入 → outline.mood / visual_tone.overall_mood
    → start_generation → _run_generation_in_background(user_selected_mood)
       → run_story_generation_task(user_selected_mood)
          → pipeline.run(user_selected_mood)
             → generate_bgm_for_chapter(user_selected_mood)
                → extract_story_for_music(user_selected_mood)
                   → overall_mood 优先级链: user_selected_mood > confirmed_outline.user_selected_mood > visual_tone.overall_mood
```

**B34 — LLM 调用移出 DB 事务（generate_outline 端点）**

- 旧行为：`Depends(get_db)` session 在 MySQL autobegin 后持锁，LLM 调用 254s 期间 row-level lock 不释放，阻塞其他并发请求（B28 症状）
- 新行为：从 project 提取所有数据 → `await db.commit()` 释放 MySQL row-level lock → LLM 调用（无锁，254s） → 新短生命周期 session 写入 `raw_outline_json`
- 文件：`app/api/projects.py`（generate_outline 函数）

**验证结果**:
- 9 个文件全部通过 Python AST 语法检查
- `tests/test_architecture.py` 7 passed, 0 failed
- 无高风险文件（image_generator / storyboard_service / storyboard_prompts）被修改，无需跑角色一致性回归测试

**@PM 后续操作（PM 已全部完成）**:
- [x] `alembic upgrade head` 运行迁移 003（VPS 已升至 head=003）
- [x] kill + restart backend（PID 59918 已重启）
- [x] 通知 frontend 接入新 API 字段（frontend PID 60089 已重启）

---

### B31 BGM 切尾 4 秒 + B32 Haiku prompt 持久化 + 任务 3 mock 跑 ✅ [2026-05-09]

**B31** `app/services/ffmpeg_post_processor.py` — process_bgm 签名改 `target_duration_sec: Optional[float] = None`，不再裁到 target，只切末尾 4s 水印。input < 8s 跳过水印保护。新增返回字段 `input_duration_sec` / `watermark_trimmed_sec`。

**B32** `app/services/music_generation_service.py` — Step 5 调 Haiku 后，写 `bgm_prompt_chapter{N}.txt` 到 output_dir，同时 INFO 级别 log 打印完整 prompt 文本。

**任务 3** `test_output/manualtest/test8_bgm_haiku_dump/bgm_prompt_dump.txt` — test8 "行李箱里的她" 真调 Haiku 4.5 dump 完成（776 chars），悬疑桶调性词分析：必备词 2/7 精确命中（minor key / ambient drone），非精确命中还有 sparse/silence/muffled/no resolution/pulse，禁用词 0/6 无污染，结论良好。

---

## 2026-05-08

### B16 P1 Hotfix — regenerate_shot 保存失败 ✅ [2026-05-08]

**根因**: `regenerate_shot` 保存逻辑只检查 `image_data`（bytes/PIL），未检查 `pil_image` 字段。Seedream 实际返回 `{"pil_image": <PIL.Image>, "image_data": "<base64_str>", ...}`，走到 else 分支抛 500。

**修复**: `app/api/chapters.py` L1682-1710，新增三路判断：
1. `pil_image` 有 `.save` 方法 → 直接 PIL save（Seedream 主路径）
2. `image_data` 是 bytes → 直接写文件
3. `image_data` 是 str → base64 解码后写文件
4. else → 错误信息细化含 `type(pil_image)` + `type(image_data)` 便于调试

---

### P0+P1 批次 6 任务 ✅ [2026-05-08]

**B16** regenerate_shot 实现：char_refs + scene_refs + `generate_shot_image_phase2_safe()` + `?v={ts}` cache bust。`app/api/chapters.py`

**B8** _fix_inner_quotes 提取为模块级 `_fix_inner_quotes_shared()`，`_extract_json` 加 R4-4 修复，`_build_single_scene_prompt` 加 「」 约束。`app/services/screenplay_writer.py`

**B6** `GET /story` pending/generating_story/full_script=None 从 400 改为 404。`app/api/chapters.py`

**B18** `_validate_outline` 加 plot_point fallback（beat 按位置分配，duration 默认 30）；prompt 加 MANDATORY 字段完整性要求。`app/services/story_outline_generator.py`

**B19** `overall_mood` 改为强制枚举（8 值）；`_validate_outline` 加 fallback 映射。`app/services/story_outline_generator.py`

**B20** `_build_single_scene_prompt` 注入 `mood_sound_constraint` 块（8 情绪对应音效风格 + MANDATORY）。`app/services/screenplay_writer.py`

pytest: 7 passed, 10 skipped (pre-existing LONGTEXT/SQLite infra failure 不受影响)

---

### TASK-SCREENPLAY-SCENE-FAIL-RCA — Stage 3 Scene 11/14/16 失败根因分析 ✅ [2026-05-08]

**任务**: xuhuastorytest7 Stage 3 ScreenplayWriter 16 场戏中 3 场失败 (Scene 11/14/16) 的根因深挖。

**结论**: 根因是 `_extract_json()` 缺少 R4-4 内部引号修复逻辑（`_fix_inner_quotes`），导致 Claude 在 narration 字段内嵌入未转义双引号时 JSON.loads() 全部失败。

**证据链**:
1. Log 确认 3 次 API 调用均 HTTP 200 且有真实 chars 输出（2929/2747/2974 for S11，3556/2947/3207 for S14，4793/3730/3847 for S16）
2. Log 无 `(字数:X/Y)` 打印 → JSON parse 失败（非字数不足触发的重试路径）
3. Log 无 `(error:` 打印 → `_call_llm_with_retry` 成功，异常在 `_extract_json` 内部静默 swallow
4. `_extract_batch_json` 有 R4-4 `_fix_inner_quotes` (L574-615)，`_extract_json` 没有 — 功能不对等
5. 失败场景（PP11/14）描述本身含大量对话文字（'饿不饿？红烧肉'等），Claude 写 narration 时引用这些对话会用双引号，与 JSON 外部引号冲突

**文件**: `app/services/screenplay_writer.py`
- `_extract_json()` L1076-1103 — 缺少内部引号修复
- `_extract_batch_json()` L528-661 — 有完整修复逻辑（R4-4）

**推荐修复方案（已报 PM）**: 将 `_fix_inner_quotes` 逻辑提取为 `_shared_json_fix` 辅助方法，`_extract_json` 和 `_extract_batch_json` 共用。

---

## 2026-04-28

### R7-3 P1 portrait 重生静默失效 bug 修复 ✅ [2026-04-28 21:42]

**真因**: `adjust_character()` 调 Haiku 改写角色后，`updated_char` 里的 `physical`/`clothing`/`human` 字段为 **str** 类型（不是 dict，与原始 T7 数据格式一致，Haiku 忠实保留）。随后 `generate_character_reference()` → `_build_portrait_prompt()` → `character_builder._build_human_description()` 在 L100-102 对这些字段调 `.get()` 时触发 `'str' object has no attribute 'get'`，异常被 try/except 吞掉，portrait 静默失败。

**修复文件**: `app/services/character_prompt_builder.py`

**修复 2 处**:
1. `_build_human_description()` L100-112: 新增防御性类型检查，`human_raw/physical_raw/clothing_raw = character.get(...)` 后判断是否为 dict，若为 str 则直接追加 str 内容到 parts（跳过细粒度 `.get()` 调用）
2. `build_face_description()` L217: 同样防御性处理 `physical_raw`

**验收证据**:
- pytest 24/24 ✅（test_architecture + test_parallel_stage5）
- backend log: `[AdjustCharacter] ✅ 角色 char_001 已调整` + `R7-3: char_001 肖像已重生成` — 无任何异常
- portrait mtime: `1777379854.28` → `1777383723.85`（文件确实更新）
- DB `characters_json[0].portrait_url` = `/static/outputs/.../char_001_portrait.png` ✅
- DB `characters_json[0].updated_at` = `2026-04-28T13:42:03.852076Z` ✅

**严禁文件**: 未碰 image_generator.py / storyboard_prompts.py / seedream_generator.py / style_enforcer.py / storyboard_service.py ✅
**D.15 aspect_ratio 链路**: 无影响 ✅

---

### TASK-T6-FIXBATCH Wave 2.5 — D.15 P0 aspect_ratio 完整修复 ✅ [2026-04-28 17:00]

**根因**: pipeline_orchestrator.py 真生图调用 `aspect_ratio="2:3"` hardcoded，用户选的画幅完全无效。

**修复 4 文件 7 处**:
- `seedream_generator.py`: `_ASPECT_RATIO_TO_SIZE` 补 `3:4` + `4:3`（现 7 种）
- `pipeline_orchestrator.py`: `run()` 加 `aspect_ratio` 参数 + 3 处 hardcoded 全消除（真生图调用 + ARCH-1 width/height/aspect_ratio）
- `job_manager.py`: `run_story_generation_task()` 加 `aspect_ratio` 参数 + pipeline.run() 传值
- `projects.py`: `_run_generation_in_background()` + `start_generation()` 传 `project.aspect_ratio or "2:3"`

**验证**: pytest 292/292 passed ✅ | import check ✅ | PENDING.md D.15 标 ✅

---

### TASK-T6-FIXBATCH Wave 2 Agent F — ARCH-1 chapter_scene_images 写入 ✅ [2026-04-28 15:50]

**任务**: P1-7 ARCH-1 — pipeline 完成后批量写入 chapter_scene_images 表，让单 shot 重生成 / 局部编辑功能可用。

**评估完成（Step 1）**: grep 全代码库 19 处引用，逐引用分析 4 个问题，结论：全部兼容，无破坏性变更。

**实施方案**:
- `pipeline_orchestrator.run()` 加 `chapter_id: Optional[int] = None`（默认值，向后兼容）
- Stage 5 storyboard checkpoint 之后加 ARCH-1 块：DELETE 旧记录 + 批量 INSERT 成功 shots（image_url 不为空）
- 失败兜底：`except Exception: logger.warning`（非阻塞）
- `job_manager.py` 调用 `pipeline.run()` 时传入 `chapter_id=chapter_id`

**修改文件**:
- `app/services/pipeline_orchestrator.py` — run() 参数 + ARCH-1 批量写入块
- `app/services/job_manager.py` — pipeline.run() 加 chapter_id 参数

**验证**: pytest 211/211 ✅；import check ✅；禁改文件未碰 ✅

---

### TASK-T6-FIXBATCH Wave 1.1 Agent A + 修复 round 1 ✅ [2026-04-28 15:05]

**任务**: 5 项后端修复（P0-2 / P1-1 / P1-2 / P1-3 / P1-5）+ PM 审查后修复 round 1（2 处严重问题）

**修改文件**:
- `app/services/job_manager.py` — P0-2 stage='completed' + P1-2 单调 guard + estimated_remaining_seconds 参数
- `app/services/pipeline_orchestrator.py` — P1-1 stage callback 4处修正 + image_generation 入口 + STAGE_DURATIONS + estimate_remaining() + P1-3 freshness check（**30s buffer**）+ P1-5 character_design/6 分离点
- `app/services/reference_image_manager.py` — P1-3 generate_character_multi_refs() skip_portrait 参数
- `app/api/projects.py` — P1-3 adjust_character Step 7 (portrait重生+updated_at) + 新端点 POST /{id}/characters/{char_id}/regenerate-portrait
- `app/api/chapters.py` — **修复 round 1**: import estimate_remaining + /status ETA 替换为 stage-aware 逻辑（L21 + L143-156）

**验证**: pytest 7/7 ✅；语法验证 ✅；import check ✅；禁改文件未碰 ✅

---

## 2026-04-27

### TASK-T5-FIXBATCH-R6 子任务 1 ✅ [2026-04-27 17:30]

**任务**: 扩展 GET /api/projects/{project_id} 响应，加 `confirmed_outline` + `aspect_ratio` 字段

**修改文件**:
- `app/schemas/project.py` — 加 `from typing import Any`；ProjectDetail 新增 2 字段（带注释）
- `app/api/projects.py` — serialize_project_detail 新增 json.loads(confirmed_outline_json) + JSONDecodeError fallback None

**验证**:
- pytest 211/211 passed (test_architecture + test_parallel_stage5 + test_style_music_hints)
- ProjectDetail 实例化测试: confirmed_outline={'mood':'感人'} + aspect_ratio='2:3' 正确出现在 model_dump()

**影响**: GET /api/projects/{id} 和 GET /api/projects/（list）都自动带新字段。list 端点性能无影响（json.loads 每项执行一次，O(n) 不可避免）。

---

### TASK-PARALLEL-M1 Round 4 ✅ [2026-04-27 11:35]

**任务**: 修 Bug 1（dispatcher 没传 `**_kwargs_copy`） + Bug 5（ShotValidator 5MB 图片限制图压缩）

**Bug 1 修复**:
- 文件: `app/services/image_generator.py`
- 问题: L1392 dispatcher 调用 `generate_shot_image_seedream()` 时 `_kwargs_copy` 不传入 → project_id 无法到 log_api_cost → INSERT None
- 修复: 在调用末尾加 `**_kwargs_copy`（1行）
- 实证: api_cost_logs id=182-197 共 16 条 project_id=12（integer），旧代码 id<=181 全 None

**Bug 5 修复**:
- 文件: `app/services/shot_validator.py`
- 问题: Seedream PNG 超 Anthropic Claude 5MB 上限触发 fail-open
- 修复: 新增 `_compress_for_claude()` 函数 + validate_shot() 调用点
  - 策略: quality 85/75/65/55 → 分辨率 80%/60%/50% 渐进压缩
  - media_type 动态（image/jpeg 压缩后 / image/png 原图）

**验收**:
- pytest: 24/24 passed ✅
- driver 跑完: 16/16 shots project_id=integer ✅
- 耗时: 20.3 min, success=True, 成本 ~¥3.5

---


## 2026-04-25

### TASK-SHOT08-DIAGNOSIS ✅ [2026-04-25 13:48]

**背景**: Shot 8 在 Phase 3/4/回归测试三次都在同一位置卡死（4 角色 + 2 场景 = 6 refs，prompt 2023 字符）。PM 要求单独诊断根因 A/B/C。

**执行**: 方案 1（`bash -c` wrapper）成功，直接跑通。

**结论**: 根因 A — 累积态资源耗尽。单独跑 shot_8 成功（1664x2496 生图，78.6s，3218KB），排除 B/C。

**关键数据**:

| 指标 | 数值 |
|------|------|
| outcome | success |
| root_cause | A |
| mem_peak_mb | 290.45 MB |
| payload_bytes | 10,363,884 (~9.88 MB) |
| total_elapsed_sec | 81.603 s |
| api_call 耗时 | 78.648 s |
| http_status | null |
| exception_type | null |

**含义**: 前 7 个 shot 跑完后内存/socket/handle 未完全释放导致卡死。生产 FastAPI 每请求独立调用栈，天然隔离，无需修复生产代码。

**约束遵守**: 未碰 scripts/diagnose_shot8_seedream.py / app/services/* / 其他 agent 文件。仅写 test_output + 文档三件套。

**产物**: `test_output/manualtest/shot8_diagnosis_2026-04-25/` (diagnose.log, result.json, shot_08.png)

---

## 2026-04-23

### TASK-BUG-FIX-BATCH-1 Route B ✅ [2026-04-23 16:15]

**背景**: Founder 本地 Pipeline 测试发现 4 个 bug + chapter id=2 脏数据。PM 派 Route B。

**改动清单**:

| 文件 | 行号 | 改动 |
|------|------|------|
| `app/services/job_manager.py` | L201-205 | checkpoint_callback 加类型判断：`isinstance(data, (dict, list))` 才 json.dumps，其他直接 setattr |
| `app/services/pipeline_orchestrator.py` | L381-401 | SKIP 分支传 `project_id` + 完成后 `_save_json("4_storyboard.json")` + `checkpoint_callback("storyboard_json", storyboard)` |
| `app/services/pipeline_orchestrator.py` | L721-728 | Stage 6 BGM 后加 `await checkpoint_callback("credits_used", bgm_result.get("credits_used", 0))` |
| `app/services/pipeline_orchestrator.py` | L872-881 / L919-944 | `_run_stage5_skip_mode` 加 `project_id: Optional[str]` 参数 + shot 循环内写 `shot["image_url"] = "/static/outputs/{uuid}/images/shot_NN.png"` |
| `app/main.py` | L82-85 | `app.mount("/static/outputs", StaticFiles(directory=os.path.abspath("output")))` |
| DB `project_chapters` id=2 | — | UPDATE：bgm_url 去引号 + 改 URL，bgm_meta_version 去引号，credits_used 0→10 |

**验收**:
- pytest test_architecture: **7 passed in 0.04s** ✅
- backend 启动无 --reload: **Application startup complete** ✅
- /health: `{"status":"healthy"}` ✅
- /static/outputs bgm: **HTTP/1.1 200 OK** audio/mpeg ✅
- /static/outputs image: **HTTP/1.1 200 OK** image/png ✅
- DB chapter id=2 before/after: `'"./output/.../bgm.mp3"' '"mixed"' 0` → `'/static/outputs/.../bgm.mp3' 'mixed' 10` ✅

**约束遵守**: 未碰 🔴 警示文件 / 前端 / VPS / .env / DB schema / Ben 侧数据。本地 backend 无 `--reload`。

**待 PM 决策**:
- 其他 chapter 是否也有脏数据（全表扫 `WHERE bgm_url LIKE '"%'`）
- 新产出 chapter 的 bgm_url 仍是本地路径（music_generation_service 未改），是否派后续任务统一

---

### TASK-P0P1-LOGGING-FIX ✅ [2026-04-23 11:30]

**4 处日志治理改动落地**，3 文件：`pipeline_orchestrator.py` / `image_generator.py` / `api/chapters.py`

- **改动 1 (P0)**: `pipeline_orchestrator.py` L1074-1081 裸 `except:` → `except Exception as e: logger.exception(...) + pass` 保留原吞异常行为（forclaudeweb 写入失败不阻塞）
- **改动 2 (P0)**: `api/chapters.py` 3 个后台任务（`generate_images_task` L498 起 / `regenerate_single_image_task` L762 起 / `generate_audio_and_align_task` L1237 起）强化异常处理：
  - `asyncio.CancelledError` 独立 raise（用户取消不算 failed）
  - `Exception` 用 `logger.exception(...)` 输出 traceback
  - `chapter.error_message = traceback[:10000]` + `chapter.status = 'failed'`
  - `job.stage_message = f"{type}: {msg[:400]}"`
- **改动 3 (P0)**: `api/chapters.py` 9 个 GET 端点加 try/except: `/`, `/status`, `/story`, `/{chapter_number}`, `/images`, `/timeline`, `/audio`, `/voices`, `/bgm`。HTTPException 透传，其他异常 `logger.exception(...)` + 返 500 JSON 含 `{type}: {msg}`
- **改动 4 (P1)**: `image_generator.py` 65 处 print → logger 机械转换（L3 加 `import logging`，L16 加 `logger = logging.getLogger("xuhua")`）。分类规则：`❌/失败` → `error`，`⚠️/跳过/Warning` → `warning`，其余 → `info`

**验收 7 项全部 PASS**:
- `grep -n "except:" app/services/pipeline_orchestrator.py` → 0 ✅
- `grep -c "print(" app/services/image_generator.py` → 0（目标 ≤5）✅
- `grep -c "logger\." app/services/image_generator.py` → 65（目标 ≥60）✅
- `pytest tests/test_architecture.py -x -q` → 7 passed in 0.06s ✅
- `python3 -c "from app.api import chapters; from app.services import image_generator, pipeline_orchestrator"` → OK ✅
- `curl http://localhost:8000/health` → `{"status":"healthy"}`（本地 shell `bxgmyw2yw` 自动热重载）✅
- chapters.py GET 端点全部 try/except 包装（9 个）+ start-generation wrapper 语义等价的 BackgroundTasks 处理 ✅

**跳过角色一致性回归**（Founder 批准）:
- image_generator.py 本次是纯机械 print→logger 转换，0 行为变化
- 未碰 generate_image / generate_shot_image_phase2 / API 参数 / contents / prompt / 参考图
- pytest + import + /health 已足够

**额外发现**:
- chapters.py **没有** `start-generation` 端点（任务描述有误）— 实际用 FastAPI `BackgroundTasks.add_task`，3 个后台任务函数内部已强化，语义等价于 wrapper
- `regenerate_single_image_task` 原来失败不写 DB（用户看不到失败），本次新增写一条 `SceneImage(error_message=...)` — 行为改动但符合"让真实错误可见"意图

---

## 2026-04-22

### TASK-8631-UNIFY ✅ [2026-04-22 16:10]
- **13 处 `max_tokens=8631 → 16384`** 统一落地（5 个 Python 文件，用 `sed -i '' 's/8631/16384/g'` 批量替换后 grep 核验 0 命中）
- 实际修改行号（sed 原地替换不改变行号结构）：
  - `character_designer.py`: L84 (Claude) / L105 (Gemini)
  - `alignment_service.py`: L177 / L193 / L234 / L250（Claude 视觉 + Gemini 视觉 + Claude 文本 + Gemini 文本）
  - `story_outline_generator.py`: L196（Gemini fallback，补齐上次半改遗漏）
  - `storyboard_director.py`: L543 (调用) / L580 (函数默认参)
  - `screenplay_writer.py`: L236 (调用) / L663 (默认参) / L790 (Gemini config) / L800 (Claude)
- **自我纠错**:
  - 上次 TASK-LLM-TEMP-AUDIT-FIX Step 7 汇报"14 处 `8631` 出现" → **实际 13 处**（PM 独立地毯式 grep 核对发现偏差）
  - 上次汇报"story_outline_generator 已改 8631→16384" → **半改状态**（L178 Claude 已 16384，L196 Gemini fallback 仍 8631），本次 TASK-8631-UNIFY 补齐
- **验收**: `grep -rn "8631" app/` 返回 0；`pytest tests/test_architecture.py` 7 passed in 0.04s；`curl http://localhost:8000/health` → `{"status":"healthy"}`
- **近零风险**: Founder 已批准（token 上限独立决策通过），不涉及 🔴 警示文件，不改前端/prompt/tests

---

### TASK-LLM-TEMP-AUDIT-FIX ✅ [2026-04-22 15:36]
- **Step 1** `alignment_service.py` L175, L231: Claude `messages.create` × 2 → `temperature=0.2`
- **Step 2** `shot_validator.py` L125: Haiku `messages.create` → `temperature=0.2`
- **Step 3** `app/api/utils.py`:
  - L8: 新增 `from google.genai import types` import
  - L35, L144: Gemini `generate_content` → `config=types.GenerateContentConfig(temperature=0.2)` × 2
  - L55, L163: Claude Haiku `messages.create` → `temperature=0.2` × 2
- **Step 4** `story_generator.py` L303: sync Claude `max_tokens` 8192 → 16384（与 async 对齐）
- **Step 5** `screenplay_writer.py`:
  - L697: Stage 3 主 Claude `messages.create` → `temperature=0.8`
  - L725: Stage 3 备 Gemini config → `{"max_output_tokens": ..., "temperature": 0.8}`
  - L787: `_expand_narration_if_needed` Gemini config → 加 `"temperature": 0.8`
  - L798: `_expand_narration_if_needed` Claude `messages.create` → `temperature=0.8`
- **Step 6** `storyboard_director.py`:
  - L614: Stage 4 主 Claude → `temperature=0.8`
  - L642: Stage 4 备 Gemini config → `{"max_output_tokens": ..., "temperature": 0.8}`
- **Step 7** max_tokens=8631 调查：历史遗留（初始 commit acba309 就存在，无注释，无文档说明；2026-03-24 story_outline_generator 已 8631→16384，其他 Stage 未同步）。建议统一 16384 记入 PENDING
- **验收**: `pytest tests/test_architecture.py` 7 passed；6 模块 import OK；/health → `{"status":"healthy"}`

---

## 2026-04-21

### Wave 3 Step 5 — Stage D BGM REST API ✅ (2026-04-21)
- `app/api/chapters.py` L1530-1913 新增 4 端点
- GET bgm / POST regenerate (10 credits) / POST change-meta (5 credits) / PATCH volume
- asyncio.to_thread 包装 service 同步调用（避免阻塞 event loop）
- Bearer token 认证

### Wave 2 完成 — music_generation_service + orchestrator + DB migration ✅ (PM 实测 E2E PASS)
- `ffmpeg_post_processor.py` LUFS 改用 ebur128（-15.5 LUFS 验证通过）
- `music_generation_service.py` 新建（22K），8 步 flow 完整
- `chapter.py` 加 bgm_url/bgm_volume/bgm_meta_version/credits_used 4 列
- `alembic/versions/001_add_bgm_fields_to_chapters.py` migration（待 Ben/DevOps 跑 MySQL schema）
- `pipeline_orchestrator.py` Stage 6 加 BGM 生成（try/except 非阻塞）
- PM E2E: 年夜饭跑通，Mureka task 134387356336130
- PM 修 URL typo: MUREKA_QUERY_URL_TPL 少 `/query/` 段

### Wave 1 Step 1 — story_music_extractor.py ✅
- `app/services/story_music_extractor.py`
- `extract_story_for_music()` 从 outline + screenplay 提取 15 字段
- max_scenes 上限按 plot_point 优先级选取
- 5 个 parity 风险全覆盖
- PM 3 测试全 PASS

### Wave 1 Step 3 — ffmpeg_post_processor.py ✅ (部分)
- `app/services/ffmpeg_post_processor.py`
- `process_bgm()` FFmpeg 一次性 filter 链
- 切水印 4s + 裁剪 target duration + volume + 淡入淡出 + 静音检测
- 🟡 LUFS 检测返回 0.0 有 bug (loudnorm 单 pass 限制)，Wave 2 修
- PM 验证核心路径 PASS

### 方案 B Backend — clean_haiku_output() 输出清理 ✅
- `scripts/test_haiku_music_prompt_languages.py` 新增清理函数
- 正则去除 markdown fence + 非 <quotes> XML 标签
- BGM prompt 超 974 字符警告（Mureka 1024 边缘）
- 配合 @ai-ml v3.2 meta-prompt 精简（污染修复从 prompt 层迁到代码层）

---

## 2026-04-20

### TASK-MUSIC-LANG-AB-V2 Step 2 — 脚本加 --version 参数 ✅
- `scripts/test_haiku_music_prompt_languages.py` 加 `argparse --version v1|v2`
- 默认 v2，v1 保留向后兼容
- PM 实测 v2 3/3 BGM 成功，长度硬约束起作用（mixed 855→506 字符）

---

## 2026-04-18

### TASK-MUSIC-LANG-AB Step 2 — Haiku+Mureka A/B/C 测试脚本 ✅
- `scripts/test_haiku_music_prompt_languages.py` 新建（512 行）
- 3 套 BGM 全部生成成功（en/cn/mixed），PM 实际运行验证
- SSL fix：certifi 做 urllib 全局 default context（Python 3.11 framework 兼容）
- 未来 Pipeline 集成可复用 call_haiku + call_mureka 函数

### TASK-ENV-SETTINGS-SYNC-TEST — .env/Settings 漂移 CI 检查 ✅
- `tests/test_architecture.py` 新增 `test_env_example_matches_settings`
- AST 解析 Settings 类 + 文本解析 .env.example + 双向对比 + 白名单
- PM 实测: 正常 PASS + 故意制造漂移时精准捕获
- EP-016 防护状态 ❌→✅

### TASK-SETTINGS-FIX — Settings 类补齐 + 严格模式恢复 ✅
- `app/config.py` 补 `VOLCENGINE_API_KEY`、`VOLCENGINE_SECRET_KEY`、`MUREKA_API_KEY`
- 删除 `extra = "ignore"`
- PM 重启 backend 验证严格模式下启动正常（/health healthy）
- 新增 EP-016 到 ERROR_PATTERNS.md

---

## 2026-04-16

### TASK-MUREKA-BGM — "最后一投" BGM 生成 ✅
- Mureka API `POST /v1/instrumental/generate`（n=2, model=auto → mureka-9）
- Post-Rock → Orchestral prompt，耗时 ~58s
- 产出: `bgm_01.mp3`（2:55, 5.4M）+ `bgm_02.mp3`（3:23, 6.2M）
- 技术坑: curl 传中文 JSON 报 Invalid JSON → 改用 Python urllib + ensure_ascii=False (EP-015)

### TASK-MUREKA-BGM-2 — "外公的秋梨膏" BGM 生成 ✅
- Mureka API（n=1, model=auto → mureka-9）
- 合并版 Prompt 732 字符（含中英文），耗时 ~83s
- 产出: `bgm_01.mp3`（7.17 MB，3分54秒）

### TASK-MUREKA-BGM-3 — 4 个故事 BGM 批量生成 ✅
- 使用 `generate_bgm.py` 脚本顺序调 Mureka API（n=1 × 4）
- 年夜饭上的战争: Task 133510809518082, ~2:58, 5.5M, 133s
- 拿铁上的告白: Task 133511086538756, ~2:52, 5.2M, 133s
- 墨痕: Task 133511373848578, ~3:25, 6.3M, 118s
- 终点站前的余温: Task 133511616921601, ~3:39, 6.7M, 120s
- 各 music_prompt.md 末尾已追加生成结果表格

---

## 2026-04-14（PM 代更新）

### TASK-PROMPT-B-PRIME — B' 默认格式 ✅
- `app/config.py`: PROMPT_FORMAT = "b_prime"
- `app/services/image_generator.py`: _build_b_prime_prompt() + prompt_format 参数
- A 格式保留（legacy 切回），B' 跳过 StyleEnforcer.enforce_prompt()

### TASK-KI-FIX — 3 个 Shot 级 API 端点 ✅
- `app/api/chapters.py`: regenerate_shot(POST) + update_shot(PATCH) + delete_shot(DELETE)
- SKIP 模式返回现有图片，update 写回 DB，delete 软删除
- 共享 helper: _get_project_and_chapter() + _find_shot_in_storyboard()

### TASK-HE-BACKEND-1 — Pipeline Schema 验证 ✅
- `app/services/pipeline_schemas.py`: Pydantic CharacterSchema + ShotSchema
- `app/services/pipeline_orchestrator.py`: Stage 2→3 + Stage 4→5 验证调用

### TASK-STAGED-V2 — Haiku 集成到 regenerate 端点 ✅
- `app/api/chapters.py`: ShotRegenerateRequest + adjustment_intent 参数
- Haiku 4.5 修改 image_prompt → 写回 storyboard_json
- 错误处理: Haiku 失败 fallback 不阻塞

---

## 2026-04-13

### R6-1b + R6-2b confirm_outline 修复 ✅
- R6-1b: `raw["mood"] = user["mood"]` 新增，顶层 mood 字段同步更新（Pipeline 读此字段）
- R6-2b: 删除 selected_ending 替换 plot_points[-1] 的逻辑（前端 R6-2 已改为 append，后端无需替换）
- 改动文件: `app/api/projects.py`，syntax ✅

---

### R6 Backend ✅
- R6-5: max_wait 300→1800 (pipeline_orchestrator.py)
- R6-6: 风格日志 custom display_name (pipeline_orchestrator.py)

---

### TASK-LOG-AUDIT 日志覆盖审查 ✅
- 8 文件审查，7 文件加日志（零业务逻辑变更）
- LLM 调用: 响应长度+耗时。Pipeline: 入口参数+出口耗时。R4-1 轮询: 周期状态。API: 入口/出口
- 不打 LLM 完整 prompt/response（太长），不打高频轮询（flooding）

---

### MySQL 连接池修复 ✅
- `app/database.py` — `pool_recycle` 300→1800, `pool_pre_ping` 已有保持 True
- 背景: Pipeline 长运行导致 `Packet sequence number wrong` 500 错误
- Ben 确认可直接改

---

### TASK-PIPELINE-OPT-R4 Backend 完成 ✅

- R4-1 (P0): Pipeline 真正等用户确认 — characters_confirmed 字段 + 轮询循环(2s/5min) + confirm-characters 端点 + start-generation 重置 (project.py + pipeline_orchestrator.py + projects.py)
- R4-4 (P1): Stage 3 batch 可行 — 根因 LLM 未转义内部双引号，新增第 7 层修复 (screenplay_writer.py)
- DB 迁移: `ALTER TABLE projects ADD COLUMN characters_confirmed TINYINT(1) NOT NULL DEFAULT 0;`

---

## 2026-04-09

### TASK-PIPELINE-OPT-R3 Backend 完成 ✅

- B-1 (P0): character_ready 检查点修复 — 删除即时覆盖 + 5s sleep (pipeline_orchestrator.py)
- B-2 (P1): Stage 3 batch 诊断加强 — 保存原始响应 + 失败日志增强 (screenplay_writer.py)
- B-3 (P1): 短篇 29→~18 shots — min_shots 公式 + target_beats 公式修正 (story_outline_generator.py + screenplay_writer.py)

---

## 2026-04-08

### TASK-REAL-PIPELINE-UX Step 1 完成 ✅

- 1-A: Stage 5 跳过模式 (config.py + pipeline_orchestrator.py + .env)
- 1-B: generate-outline 返回 scenes (projects.py)
- 1-C: generation-result + 图片服务 2 端点 (projects.py)
- job_manager.py: generate_images=True + progress_callback + 存 storyboard_json

---

## 2026-04-07

### TASK-OUTLINE-MERGE-FIX 完成 ✅

- `projects.py` confirm_outline: Bug 1 summary 同时写 summary + logline; Bug 2 selected_ending 替换 plot_points[-1] description（方案 C）

---

## 2026-04-01

### TASK-PLOTPOINT-REORDER-FIX Backend 完成 ✅

- `projects.py`: plot_points 按 original_index 整体移动 dict（mood/setting 跟随排序）

### TASK-CONFIRM-OUTLINE-WIRE Step 2 完成 ✅

- `projects.py`: POST /projects/ 去 pipeline + confirm-outline 合并逻辑 + 新增 start-generation
- `pipeline_orchestrator.py`: run() +confirmed_outline → 有则跳过 Stage 1
- `job_manager.py`: run_story_generation_task +confirmed_outline → 有则用 PipelineOrchestrator 替代 StoryGenerator

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

---

## 2026-04-25 — round 2

### TASK-PARALLEL-M1 round 2 ✅ [2026-04-25 17:30]

**背景**: PM 审查 Phase 1 报告 3 隐忧，Founder 批准 Backend round 2 修复。

**执行**: 真实 venv 验证所有依赖可用，无需 stub。

**修复内容**:
1. conftest.py（14.6KB）删除 — venv 真实依赖足够，无需任何 stub
2. pipeline_orchestrator.py: PipelineCostTracker 创建前用 project_uuid 查 DB 拿 integer Project.id，传入 CostTracker + generate_shot_image_phase2_safe() 调用，ARCH-4 READ/INSERT 路径打通
3. seedream_generator.py: 从 **_kwargs 提取 project_id，传入 log_api_cost()，Seedream INSERT 路径携带真实 project_id

**验收**: pytest 24/24 passed in 0.78s（真实 venv，无 stub）

**修改文件**: conftest.py 删除 / pipeline_orchestrator.py +18行 / seedream_generator.py +2行



---

### TASK-T5-FIXBATCH 8 条后端修复 ✅ (2026-04-27 PM 代更归档)

**完成时间**: 2026-04-27 16:33 (~13 min agent 时间)
**验收状态**: ✅ 211/211 tests pass + T5 hot-fix 已跑

**完成内容**:
- [x] BE-3 P0 image_url 写回 storyboard
- [x] BE-4 P0 /chapters/{n}/storyboard 端点
- [x] BE-5 P0 bgm_url HTTP URL
- [x] BGM-1 P1 outline.music_hint
- [x] OBS-4 P1 用户情绪持久化
- [x] UX-10/11 P1 BGM + completed signal
- [x] UX-1/14 P1 Stage 2 portrait 提前
- [x] UX-2 A2 P2 outline 一致性 LLM check
- [x] Hot-fix T5 数据补 URL 让 Founder 立刻能看

**关键产出**:
| 文件 | 改动 |
|------|------|
| `app/services/pipeline_orchestrator.py` | BE-3/5 + BGM-1 + UX-10/11 + UX-1/14 |
| `app/api/chapters.py` | BE-4 |
| `app/api/projects.py` | OBS-4 + UX-2 A2 |
| `app/services/job_manager.py` | UX-10/11 |
| `scripts/hotfix_t5_urls.py` (新建) | T5 数据补 URL |


---

## 2026-04-30 11:00 Wave 5.1 归档（PM 代更，权限 600）

D.17 移除 fallback + prompt_safety_advisor.py + D.18 SIZE_BY_MODEL + O-2 cap + T-2 callback + R7-2 schema/endpoint + Alembic 002。详见 current.md 19:25 + Wave 5.2 已部署生产。

---

## D.19 + D.20 — P0 黑屏双重修复（Option C 永久解法）[2026-04-30 17:09-17:40]

**任务**: Founder T7 测试黑屏 root cause 止损（Frontend D.19/D.20 hotfix 配套永久解法）

### 修复 1: generate_outline 幂等保护

`POST /api/projects/{uuid}/generate-outline` 现在幂等:
- `raw_outline_json` 已存 → 直接返缓存，**不调 LLM**（省 ~¥0.3-0.5 + 30-60s/调用）
- 增加 `?force_regenerate=true` query param 供用户主动重生
- Log: `[GenerateOutline] 幂等: project {id} 已有 raw_outline，直接返已存数据（不调 LLM）`

**改动**: `app/api/projects.py`
- L382 签名加 `force_regenerate: bool = Query(default=False)` query param
- L393-409 幂等检查块（cached return path）
- L407 + L451 都调 `_map_outline_to_response` helper

### 修复 2: ProjectDetail.raw_outline 字段暴露

`GET /api/projects/{uuid}` 返回新字段:
- `raw_outline`: Stage 1 LLM 原始输出（pre-confirm 状态，供前端 hydrate 用）
- `confirmed_outline` 优先（用户 confirm）→ `raw_outline` 兜底（Stage 1 完成未 confirm）→ 都 null（等 Stage 1）

**改动**:
- `app/schemas/project.py` L83 — `raw_outline: dict[str, Any] | None = None` 字段定义
- `app/api/projects.py` L98-151 — `_map_outline_to_response()` helper extract（DRY 重构，幂等+正常路径共用）
- `app/api/projects.py` L163-176 — `serialize_project_detail()` 加 raw_outline_json 解析
- `app/api/projects.py` L198 — ProjectDetail 构建传 raw_outline

### 验收
- pytest 292 passed (1 pre-existing 与本任务无关)
- PM 11 角度地毯式 audit 全 PASS（含真 DB 测试 project_id=22 raw_outline 真返 title="纸条里的父亲", 8 keys）
- Backend pid 17:41 重启加载新代码 + frontend recovery 链路实测真跑通

### 给 frontend 的影响
- frontend D.20 hotfix v2 outline recovery 现在调幂等 generate-outline → 走 raw_outline_json 缓存 → 0 LLM 成本
- 也可改用 `project.raw_outline` 字段直接（snake_case，需 frontend 做 camelCase 映射）

### 部署
- 本地 backend pid 48766 (17:41 启动) — 已加载新代码
- VPS 部署: 等 DevOps Wave 5.x push + rsync (如未部署)

---

### 2026-05-09 17:00-17:30 — B35+B38+B39+B37+B41 修复 (PM 代写)

参考 backend-progress/current.md 17:00 段

---

### 2026-05-11 10:43 — B43+B44+B46+B41 修复批 ✅（PM 代写）

参考 backend-progress/current.md 10:43 段。AsyncAnthropic + alembic 004 + ChapterStatus 加 2 字段 + safety_advice 暴露 + CLAUDE.md DEPRECATED 标注。

---

### 2026-05-11 17:18 Wave 5 — B52+B56+B57+B51v2+B49 全闭环 ✅（PM 代写）

详见 backend-progress/current.md 17:18 段。5 文件 9 fix points，AST + pytest 全过。
