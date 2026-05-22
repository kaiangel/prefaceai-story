# Backend Agent - 给其他 Agent 的上下文

> **最后更新**: [2026-05-22 ~19:00] ✅ Wave 8 第 3 批 T22-NEW-5 完成 — R4-2 wait loop 移除 + scene_review ui_phase 移除 + STATUS_API_CONTRACT v1.5. 24/24 新单测 PASS + 172/172 回归 PASS. 0 越界.

---

## ✅ [Wave 8 第 3 批 — T22-NEW-5 R4-2 砍掉] 完成 [2026-05-22 ~19:00]

### 核心变更 (Founder 5/22 13:37 决策: R4-2 可跳过)

| 文件 | 改动 |
|------|------|
| `app/services/pipeline_orchestrator.py` | R4-2 wait loop 完整移除，Stage 3→4 直连 |
| `app/api/chapters.py` | `_derive_ui_phase` 移除 scene_review，新增 confirm-scenes noop endpoint |
| `.team-brain/contracts/STATUS_API_CONTRACT.md` | 升级 v1.5 (8 状态机, scene_review 移除) |
| `tests/test_t22_new_5_r4_2_removed.py` | **新建** 24 case 全 PASS |

### pytest 真自跑结果

| 测试集 | 结果 |
|--------|------|
| test_t22_new_5_r4_2_removed.py (新建) | **24/24 PASS** |
| 5 回归测试 (51+17+14+7+83) | **172/172 PASS** |
| **总计** | **196/196 PASS, 0 退化** |

### 给 @frontend

**0 需要改动** — T22-NEW-5 Frontend 部分 (Wave 8 #2) 已完成.
STATUS_API_CONTRACT v1.5 确认: scene_review ui_phase 已从 UiPhase type 移除.
**部署铁律**: Frontend Wave 8 #2 + Backend T22-NEW-5 必须**同时部署**.

### 给 @devops

**0 Alembic migration** — scenes_confirmed DB 列保留，不做 schema 迁移.
同时部署 Frontend Wave 8 #2 + Backend T22-NEW-5 代码.

### 给 @pm

**8 维度自查**:
1. pytest 真自跑: 24/24 新 + 172/172 回归 = **196/196 PASS** ✅
2. R4-2 wait loop 移除验证: `grep r42_max_wait pipeline_orchestrator.py` = 0 hits ✅
3. scene_review 移除: `grep 'return "scene_review"' chapters.py` = 0 hits ✅
4. noop endpoint: `grep confirm_scenes_noop chapters.py` = 1 function ✅
5. STATUS_API_CONTRACT v1.5 + [frontend-impact: yes] ✅
6. scenes_confirmed DB 列保留 (0 Alembic) ✅
7. R4-1 + R4-3 保留完整 ✅
8. 0 越权: 只改 pipeline_orchestrator.py + chapters.py + contracts/STATUS_API_CONTRACT.md + 1 new test ✅

---

## ✅ [Wave 8 — Generic Fallback Architecture] 完成 [2026-05-22 ~17:00]

### 重构目标 (Founder 5/22 14:50 决策, TASK-T22-NEW-9)

长期根治 T21-NEW-1/2 hotfix 方案 (Wave 4+4.5 给 17 type 逐个手动写 humanoid fallback 规则) → 通用 fallback 架构 (方案 B: 不分 type，任何 character 含人类外貌字段视为有效拟人形态)。内测前必修。

### 改动文件 (1 改 + 1 新建 + 1 更新, 严格在 pipeline_schemas.py 领域)

| 文件 | 改动 |
|------|------|
| `app/services/pipeline_schemas.py` | `_TYPE_REQUIRED_GROUPS` 19 entry → 4 (human/anthro/animal/vehicle) + `has_humanoid_fallback()` 通用函数 + `validate_physical_by_type` 三路清晰重构 |
| `tests/test_schema_generic_fallback_arch.py` | **新建** 83 case (8 section 覆盖 19 type) |
| `tests/test_t21_digital_virtual_fallback.py` | 1 test 名/逻辑更新 (反映新架构 warning not raise) |

### pytest 真结果

| 文件 | 结果 |
|------|------|
| test_t21_digital_virtual_fallback.py | **25/25 PASS** |
| test_t21_new_2_humanoid_fallback_wave2.py | **16/16 PASS** |
| test_schema_generic_fallback_arch.py | **83/83 PASS** |
| test_identity_anchor_cross_genre_baseline.py | **105/105 PASS** |
| **总计** | **229/229 PASS** |

### 给 @pm 审查信息

- 修改文件 2 个 (pipeline_schemas.py + 1 test 更新) + 新建 1 个测试文件
- 0 越权: 0 Wave 7 文件 / 0 schemas / 0 alembic / 0 frontend / 0 contract
- test_t21_digital_virtual_fallback.py 更新说明: `test_digital_virtual_no_minimum_fields_fails` 改名 + 期望反转，因为新架构"无字段"情况是 warning 而非 raise (这是方案 B 的核心设计差异，允许 LLM 字段名灵活性)

---

## ✅ [Wave 7 P0 — Layer 1 first-batch chars=0 + LLM Fallback + Location wire] 完成 [2026-05-22 ~15:30]

### 真**根因**: Stage 4 LLM 输出格式不一致 (T22-NEW-7)

- test22 4_storyboard.json 实证: Shot 1-3 `characters_in_scene=['Coral']` (name_en) vs Shot 4-21 `['char_001']` (char_id)
- 旧 `_apply_identity_anchors` 只比对 `c["id"]` → 前 3 完全 mismatch → chars=0 → Coral anchor 完全没注入 → Seedream weak ref → Shot 2 美人鱼变蓝头发人腿
- **真不是 race / batch order / scope** — 纯 ID format mismatch

### 改动文件清单 (6 改 + 3 新单测)

| 文件 | 改动 |
|------|------|
| `app/services/identity_anchor_injector.py` | + 新增 `resolve_characters_in_shot()` standalone helper (三路 smart match, dedup, 防御 WARNING) |
| `app/services/image_generator.py` | `_apply_identity_anchors` + outline kwarg, char resolution 改 delegate to helper, location lookup outline 优先 |
| `app/services/pipeline_orchestrator.py` | Stage 5 dispatch 传 `outline=outline` kwarg (T22-NEW-6) |
| `app/services/llm_fallback_chain.py` | **新建** Haiku → Gemini → Sonnet 三层 fallback chain (跨 provider 优先) |
| `app/api/projects.py` | AdjustCharacter 接入 fallback chain |
| `app/api/chapters.py` | Shot regenerate adjustment 接入 fallback |
| `app/services/music_generation_service.py` | `_call_haiku_with_retry()` 重写用 fallback chain (3 caller 自动 benefit) |
| `tests/test_first_batch_chars_not_zero.py` | **新建** 17 case |
| `tests/test_llm_fallback_chain.py` | **新建** 14 case |
| `tests/test_apply_identity_anchors_location_wire.py` | **新建** 7 case |

### pytest 真自跑 (KEY_LEARNINGS #47 第 8 次铁律)

| 测试集 | 结果 |
|--------|------|
| test_first_batch_chars_not_zero.py | **17/17 PASS** |
| test_llm_fallback_chain.py | **14/14 PASS** |
| test_apply_identity_anchors_location_wire.py | **7/7 PASS** |
| test_identity_anchor_injector.py (regression) | **25/25 PASS** |
| test_prompt_validator.py (regression) | **28/28 PASS** |
| test_identity_anchor_extraction.py (regression) | **74/74 PASS** |
| test_identity_anchor_cross_genre_baseline.py (regression) | **105/105 PASS** |
| test_t21_new_3_to_7_backend.py (regression) | **51/51 PASS** |
| **总计** | **321/321 (38 新 + 283 旧 regression, 0 退化)** |

### Ben 5/13 协议 (本 session 严守)

- 0 改 `app/schemas/` (grep T22-NEW = 0)
- 0 改 `alembic/`
- 0 改 `.team-brain/contracts/STATUS_API_CONTRACT.md`
- 0 改 `frontend/`
- 0 改 AI-ML 文件 (`storyboard_prompts.py / storyboard_director.py / identity_anchor_prompts.py / prompt_validator.py`)

### 给 @tester

新 `resolve_characters_in_shot()` helper (`app/services/identity_anchor_injector.py`) 可直接消费:

```python
from app.services.identity_anchor_injector import resolve_characters_in_shot
# 测试 LLM 输出 inconsistent character ids 真**可被 resolve**
matched = resolve_characters_in_shot(
    shot_char_ids=["Coral", "char_001", "珊瑚"],  # 三路混合
    characters_list=[{"id": "char_001", "name_en": "Coral", "name": "珊瑚", ...}],
)
assert len(matched) == 1  # 真 dedup, 不重复
```

新 `call_llm_with_fallback()` helper (`app/services/llm_fallback_chain.py`):

```python
from app.services.llm_fallback_chain import call_llm_with_fallback
result = await call_llm_with_fallback(
    user="hello", system="You are...",
    operation_label="my_op",  # 用于 telemetry log
)
if not result.success:
    # 三层全失败, result.error 含详情, 真返 500 + friendly_error_message
```

### 给 @frontend

**0 需要改动** — 真**纯 backend post-process** + 新 endpoint 改造**0 API contract 变更**.

### 给 @devops

**0 需要改动** — 0 alembic / 0 .env / 0 服务配置. Just push backend 代码即可.

### 给 @pm

**真审查依据 (8 维度地毯式)**:

1. **pytest 真自跑数字** (8 文件): 17/17 + 14/14 + 7/7 + 25/25 + 28/28 + 74/74 + 105/105 + 51/51 = **321/321 PASS, 0 退化**
2. **调用链路 grep** (KEY_LEARNINGS #48 真**调通** 0 死代码):
   ```
   grep T22-NEW-7 image_generator.py = 4 hits
   grep T22-NEW-7 identity_anchor_injector.py = 4 hits
   grep T22-NEW-6 image_generator.py = 6 hits
   grep T22-NEW-6 pipeline_orchestrator.py = 1 hits
   grep T22-NEW-4 projects.py = 6 hits
   grep T22-NEW-4 chapters.py = 3 hits
   grep T22-NEW-4 music_generation_service.py = 3 hits
   ```
3. **Ben 协议 grep**: `app/schemas/ alembic/ .team-brain/contracts/ frontend/` 真**0 hits** T22-NEW marker
4. **AI-ML 文件 grep**: storyboard_prompts.py / storyboard_director.py / identity_anchor_prompts.py / prompt_validator.py 真**0 hits** T22-NEW marker
5. **生产路径验证**: `_apply_identity_anchors` 3 处 wire 真在 L1009/L1278/L1639 (image_generator.py 新行号 ~L834-880)
6. **异常防护**: `_apply_identity_anchors` 真 try/except 包围 + 新 helper 真**永不 raise** (production safety)
7. **Idempotent**: marker check 真**双层** (injector + validator) 真**不变**
8. **跨 character_types 通用**: smart match 真**0 hardcoded** 故事类型 (跨 19 type + 80+ style 真通用)

### 给 @founder

**真 e2e 验证**:
1. 重跑 test22 fairytale 真验证 backend.log 21/21 真 `[IdentityAnchorInjector] Injected anchors: chars=N, ..., location=Y, ...` 真**全部** chars=N (N>0) + location=Y
2. 真**视觉验证**: Shot 1/2/3 Coral 真**淡珊瑚粉色头发** + 鱼尾 + 贝壳装 (不再蓝头发人腿)
3. 真**fallback 验证**: AdjustCharacter 操作真**带** Haiku → Gemini → Sonnet 三层日志 `[LLMFallbackChain] op=adjust_character layer=1/3 ...` 真可 grep
4. 真**用户操作不再 blocked**: 即使 Anthropic 529, 自动切 Gemini 也能 return 200 + 修改成功

---

## 真**RegeneratePortrait 不接入 fallback 的说明**

PENDING.md TASK-T22-NEW-4 列了 4 个 endpoint: AdjustCharacter / RegeneratePortrait / Shot regenerate / Music BGM.

**实测**: RegeneratePortrait (`projects.py L1416`) 真**不调任何 LLM** — 只调 `ReferenceImageManager.generate_character_reference` → Seedream/NB2 生图 API. 真无 LLM fallback 必要.

如 Founder/PM 要求 RegeneratePortrait 也加 Seedream 失败 fallback (用 NB2), 那是 D.17 单一模型铁律的反向决策, 需要单独讨论 (与 Wave 7 P0 范围分开).

---

## 历史 [DEC-048 Layer 1] 完成 [2026-05-22 ~12:00] (滚到 completed.md)

⭐ 长期治本 — 解决 LLM 创意层 vs 一致性根本张力

### 实施范围 (Sonnet 4.6 xhigh, ~3h)

| 子任务 | 文件 | 状态 |
|--------|------|------|
| `inject_identity_anchors()` | `app/services/identity_anchor_injector.py` (新建 400 行) | ✅ |
| `PromptValidator` 类 | `app/services/prompt_validator.py` (新建 260 行) | ✅ |
| `_apply_identity_anchors()` + 3 dispatch wire | `app/services/image_generator.py` (改 ~190 行) | ✅ |
| 单元测试 | `tests/test_identity_anchor_injector.py` (25 case) + `tests/test_prompt_validator.py` (28 case) | ✅ |

### 给 @tester (~1h)

**95 baseline 矩阵** (19 character_types × 5 random styles):

```python
# 在 tests/test_identity_anchor_cross_genre_baseline.py
from app.prompts.identity_anchor_prompts import (
    extract_identity_anchors,
    extract_distinctive_tokens,
)
from app.services.identity_anchor_injector import inject_identity_anchors

# 注: 若 CI 环境 google.genai 不可用, 用 importlib spec_from_file_location 加 canonical name 加
#     sys.modules 注册 (镜像 tests/test_identity_anchor_injector.py 真模式)
#     dataclass 必须用 canonical name 才能在 cls.__module__ 解析时找到模块

@pytest.mark.parametrize("char_type", ALL_19_TYPES)
@pytest.mark.parametrize("style_preset", ["realistic", "anime", "children_book", "cyberpunk", "ink"])
def test_baseline_case(char_type, style_preset):
    # 1. Mock Stage 1-4 LLM 输出 (固定 fixture)
    characters = mock_characters(character_type=char_type, count=3)
    storyboard = mock_storyboard(characters=characters, num_shots=18)

    # 2. 真跑 inject_identity_anchors() 在 18 shot 上
    for shot in storyboard["shots"]:
        chars_in_shot = [c for c in characters if c["id"] in shot["characters_in_scene"]]
        injected = inject_identity_anchors(
            image_prompt=shot["image_prompt"],
            characters_in_scene=chars_in_shot,
            style_preset=style_preset,
        )

        # 3. grep 验证 — shot prompt 真**100% 含** character schema 关键字
        for char in chars_in_shot:
            anchors = extract_identity_anchors(char)
            ia = anchors["identity_anchor"]
            for field in ("primary_color", "skin_tone"):
                value = ia.get(field, "")
                if not value:
                    continue
                tokens = extract_distinctive_tokens(value, n=3)
                assert any(tok.lower() in injected.lower() for tok in tokens)
```

**关键 helper API** (供 Tester 真消费):

| API | 签名 | 返回 |
|-----|------|------|
| `inject_identity_anchors` | `(image_prompt: str, characters_in_scene: list[dict], location: dict\|None=None, style_preset: str="realistic", props: list[dict]\|None=None, time_continuity: dict\|None=None) -> str` | image_prompt with 5-block anchor section prepended (idempotent — re-runs 不动) |
| `PromptValidator().validate_prompt_vs_schema` | `(image_prompt: str, characters_in_scene: list[dict]) -> ValidationResult` | `.passed` / `.missing_anchors` (list of dict 含 char_id/field/expected/tokens/severity) / `.severity` ("critical"\|"warning"\|"info") |
| `PromptValidator().auto_correct` | `(image_prompt, validation_result, characters_in_scene, location=None, style_preset="realistic", props=None, time_continuity=None) -> str` | idempotent (marker check) — only injects if marker absent |

**关键铁律**:
- 不调真 Seedream/NB2 API (零成本) — 只 prompt-level grep 验证
- 95 case 真**期望**: 100% 通过 (auto_correct 兜底)
- 真**hair_color 字段** 真 critical, 真 100% MUST 含 token
- 真**skin_tone 字段** 真 critical, 真 100% MUST 含 token (humanoid only)
- 真**distinctive_marks + clothing** 真 warning, 真**不 fail** gate (远景可缺)

### 给 @ai-ml

**0 需要改动** — AI-ML M2-M5 round 1+2 真**已完成** (74/74 PASS 不退化). Layer 1 Backend 真**消费** AI-ML 提供的 6 个 extract helper + 3 template 真**零侵入** AI-ML 文件.

### 给 @frontend

**0 需要改动** — Layer 1 真**纯 backend post-process**, 对前端真**透明**:
- 0 API contract 变更
- 0 STATUS_API_CONTRACT 升级
- 0 字段 schema 变更
- 0 用户感知差异 (除了"角色更一致"这种良性改善)

### 给 @devops

**0 需要改动** — 部署只需 push backend 代码改动, 0 Alembic migration / 0 .env 改动 / 0 服务配置改动.

### 给 @pm

**真审查依据** (建议 8 维度地毯式按 Founder 真3 次提醒铁律):
1. pytest 真自跑数字: 25/25 + 28/28 + 74/74 + 365/365
2. 调用链路 grep: `_apply_identity_anchors` / `inject_identity_anchors` / `PromptValidator` 真接通 0 死代码
3. Ben 协议 grep: chapters.py / projects.py / schemas / alembic / STATUS_API_CONTRACT 0 diff
4. AI-ML 文件 grep: storyboard_prompts.py / storyboard_director.py / identity_anchor_prompts.py 0 diff
5. 验收: `_apply_identity_anchors` 3 处 wire 真在 L1009/L1278/L1639 (不是别处)
6. 异常防护: `_apply_identity_anchors` 真 try/except 真有 (生产安全)
7. Idempotent: marker check 真 2 层 (injector + validator)
8. 跨 character_types 通用: 真**0 hardcoded** 故事类型 (extract helper dispatch 真适配 19 type)

### 给 @founder

**e2e 真验证**:
1. 跑 test22 fairytale 真验证 Coral hair 真出现 "sea-green" (不再是 "dark hair")
2. 跑 test19/20/21 跨题材 真验证角色一致性 真**质变** (不再 RLHF 创意漂移)
3. 跨 19 character_types × 80+ styles 真**通用** (extract dispatch 表 + 80+ style 真**0 hardcoded**)

---

## 历史 [Wave 5 TASK-T21-NEW-3/4/5/6/7] 5 task 全完成 [2026-05-21 22:30] ⭐ 真大架构改造

### 完成范围 (5 task 串行, Opus 4.7 thinking xhigh, ~3h)

#### T21-NEW-3 (P1): restart progress/ETA reset
- chapters.py restart endpoint 真重算 progress + ETA
- 传真 actual_shot_count / unique_location_count / max_concurrent (从 storyboard/outline/settings 拿)
- 友好 stage_message ("从故事大纲重启中..." 等 5 stage)
- frontend 第一次 poll 拿到真值 (progress > 0, ETA 真重算)

#### T21-NEW-4 (P1): portrait/fullbody cache-buster
- AdjustCharacter + RegeneratePortrait 真改: `?v={_v_ts}` cache-buster
- 镜像 Shot regenerate L2315 模式
- chapter.characters_json 也写带 ?v= 的 URL (frontend 同步)

#### T21-NEW-5 (P2): stage_message 文案
- pipeline_orchestrator.py Stage 5 真改 "全身参考图 X/3 完成 ({角色名})"
- KEY_LEARNINGS #46 同源思想 ("用户操作 = 真相", T20-50 后 portrait 真不再生成)

#### T21-NEW-7 (P0): **Stage 4.5 scene_image_preparation 大架构改造** ⭐

**Pipeline 流程**:
```
Stage 4 完成 → Stage 4.5 (scene_image_preparation)
  ├── 真生成 interior + exterior anchor (复用 SceneReferenceManager)
  ├── 写 chapter.scene_references_json
  └── R4-3 wait loop (轮询 project.scene_references_confirmed, 超时 1800s)
       ↓ 用户在 frontend /scenes 真预览+编辑+重生+60s 倒计时
       ↓ POST /confirm-scene-references
Stage 5 image_preparation 简化 (只剩 fullbody + shots, 5a.5 改"复用 Stage 4.5")
```

**3 新 endpoint** (镜像 characters 模式):
- `GET /chapters/{n}/scene-references` — 返场景参考图列表 + scene_references_ready/confirmed + countdown_seconds=60
- `POST /chapters/{n}/scenes/{location_id}/regenerate-reference` — 重生 (ref_type: interior/exterior/both, 支持 user_edit)
- `POST /chapters/{n}/confirm-scene-references` — R4-3 闸门

**STATUS_API_CONTRACT v1.3 → v1.4**:
- 新 ui_phase `scene_references_review` (9 状态机)
- 新字段 `scene_references_ready` + `scene_references_confirmed`
- hydrate_hints 新映射: scene_references_review → /scene-references

**DB 改动** (Alembic 006):
- `projects.scene_references_confirmed` Boolean
- `project_chapters.scene_references_json` LONGTEXT
- Backfill: 已完成项目 scene_references_confirmed=True 防卡 R4-3

**DEC-047 决策**: Founder 5/21 18:25 方案 D — "情节确认 ≠ 场景视觉确认", 镜像 characters 页面对偶设计

#### T21-NEW-6 (P1): image_preparation sub-stage 细化
- SceneReferenceManager 加 4 sub_progress 参数 + _emit_sub_progress helper
- 每 view (interior/exterior) 完成后真 emit stage_message ("生成场景参考图 (interior 1/4: 客厅)...")
- Stage 5 5a 入口加 "准备角色全身参考图..."
- Stage 5 5b 调度入口加 "准备分镜参考映射 + 调度 Shot 生成 (N 张)..."
- 总 ≥5 sub-step stage_message UPDATE (验收 ≥4)

### 改动文件汇总 (9 + 2 文档)

| 文件 | 行数 |
|------|------|
| app/models/project.py | +3 |
| app/models/chapter.py | +5 |
| app/schemas/chapter.py | +10 |
| app/services/pipeline_orchestrator.py | +250 (大量 Stage 4.5 大块) |
| app/services/scene_reference_manager.py | +35 (sub_progress 参数 + helper) |
| app/services/job_manager.py | +6 (2 stage 加入 baselines + bounds) |
| app/api/chapters.py | +300 (T21-NEW-3 + 3 endpoint + ui_phase 派生改造) |
| app/api/projects.py | +20 (cache-buster + start_generation 重置) |
| alembic/versions/006_add_scene_references_t21_new7.py | +75 (新建) |
| .team-brain/contracts/STATUS_API_CONTRACT.md | +250 (v1.3 → v1.4 升级) |
| .team-brain/decisions/DECISIONS.md | +90 (DEC-047 新增) |
| tests/test_t21_new_3_to_7_backend.py | +400 (新建 51 单测) |

### pytest 真结果 (PM 自跑 KEY_LEARNINGS #47)

- ✅ 新 `test_t21_new_3_to_7_backend.py` 51/51 PASS
- ✅ 回归 234/234 PASS (单文件分别跑均 PASS)
- ✅ 综合 (新 + status_authoritative) 95/95 PASS
- ⚠️ pre-existing T20-52 同款 isolation bug (test_status_authoritative 与 T21-NEW-1 综合跑出现 27 errors + 4 fail), 单跑 PASS, 不影响生产

### 对其他 Agent 的影响

#### @frontend (重要 — Wave II 必须实施)

**API contract v1.4 必读**: `.team-brain/contracts/STATUS_API_CONTRACT.md` (PM 派工已 paste 关键段落给你)

新 ui_phase `scene_references_review` Wave II 必做:

1. **createUrl.ts UI_PHASE_TO_URL 加映射**:
   ```typescript
   "scene_references_review": "scenes",  // 与 scene_review 复用 URL, 但 hydrate 不同 endpoint
   ```

2. **CreateContent.tsx subPhase 派生加新 case**:
   ```typescript
   phaseToSubPhase["scene_references_review"] = "scene-refs-preview";
   ```

3. **StageC.tsx 真改造 (镜像 characters 页面对偶)**:
   - 检测 `status.ui_phase === "scene_references_review"` → hydrate `GET /chapters/{n}/scene-references` (不是 /story)
   - 显示场景参考图卡片列表 (每 location 2 张 interior + exterior)
   - 编辑文字描述框 + "重生" 按钮 (调 POST regenerate-reference, ref_type 选 interior/exterior/both)
   - 60s 倒计时 (镜像 R4-1 characters 60s)
   - "确认场景继续" 按钮 (调 POST confirm-scene-references)

4. **新 3 endpoint TypeScript types** (建议加到 frontend/src/lib/api.ts):
   ```typescript
   interface SceneReference {
     location_id: string;
     location_zh: string;
     interior_url: string | null;
     exterior_url: string | null;
     interior_description: string;
     exterior_description: string;
     description_zh: string;
     atmosphere: string;
     time_of_day: string;
     lighting_condition: string;
     key_visual_elements: string[];
   }
   ```

#### @ai-ml

- 0 prompt 改动
- Pipeline Stage 4.5 复用 SceneReferenceManager._build_anchor_prompt 现有逻辑, prompt 工程不变

#### @tester

- 等 Frontend Wave II 完成 + PM 重启 → Founder 跑 test22 (fairytale 美人鱼) 验证:
  - Stage 4.5 真生效 (frontend /scenes 显示场景参考图卡片)
  - R4-3 真 wait loop (Pipeline 真等用户确认)
  - 重生 endpoint 真生效 (cache-buster URL 真变)
  - DEC-014/DEC-009 一致性保留 (interior/exterior 视觉关联)

#### @devops

- Alembic migration 006 必须运行: `alembic upgrade head`
- 加 2 列 (projects.scene_references_confirmed + project_chapters.scene_references_json)
- 老数据自动 backfill (storyboard 完成的项目 scene_references_confirmed=True)

### Backend 未重启

等 PM 9 Layer 审查后重启 (含 Wave 5 改动一起生效).

---

## ✅ [TASK-T21-NEW-2] Wave 4.5 5 type humanoid fallback 补充 [2026-05-21 ~21:45]

### 背景

PM 19 type 地毯式分析发现: T20-43 (4) + T21-NEW-1 (8) = 12 type 已修后, 还有 5 type 可能呈人形未加 fallback。

### 改动

`app/services/pipeline_schemas.py` _TYPE_REQUIRED_GROUPS 扩展 5 type:
- P0: `aquatic` → `[('species', 'body_type', 'hair_color', 'skin_tone', 'face_shape')]`
- P0: `anthropomorphic_animal` → 保留 2 group AND, group 2 加人外貌: `[('species',), ('fur_color', ..., 'hair_color', 'skin_tone', 'face_shape')]`
- P1: `object` → `[('object_type', 'base_object', 'hair_color', 'skin_tone', 'face_shape')]`
- P2: `plant` → `[('plant_type', 'species', 'hair_color', 'skin_tone', 'face_shape')]`
- P2: `insect` → `[('species', 'wing_type', 'hair_color', 'skin_tone', 'face_shape')]`

新建 `tests/test_t21_new_2_humanoid_fallback_wave2.py` — **16/16 PASS**
更新 `tests/test_t21_digital_virtual_fallback.py` 1 个过时测试 — T21-NEW-1 仍 **25/25 PASS**

### 对其他 Agent 的影响

- **@frontend**: 0 API 契约变更
- **@ai-ml**: Stage 2 prompt 无改动, schema 更宽松 (19 种 type 全覆盖人外貌 fallback, 仅 animal + vehicle_character 保持严格)
- **@tester**: aquatic/anthropomorphic_animal/object/plant/insect 角色的 Schema 验证不再拒绝人外貌字段

### Backend 未重启

等 PM 审查后重启 (含 T21-NEW-1 + T21-NEW-2 改动一起生效).

---

## ✅ [TASK-T21-NEW-1] digital_virtual + 7 non-human humanoid schema fallback [2026-05-20 ~21:30]

### 背景

test21 (scifi AI 客服, cyberpunk) Stage 2 失败: `digital_virtual` type 只接受 `digital_type` 或 `base_form`，但 LLM 输出了 15 个人类外貌字段。严格镜像 T20-43 DEC-043 hotfix 修复。

### 改动

`app/services/pipeline_schemas.py` _TYPE_REQUIRED_GROUPS 扩展 8 个 type 接受人类外貌字段:
- P0: `digital_virtual` (test21 立即修)
- P1: `robot`, `hybrid`, `alien`
- P2: `elemental`, `concept_personified`, `giant`, `miniature`

新建 `tests/test_t21_digital_virtual_fallback.py` — **25/25 PASS**

### 对其他 Agent 的影响

- **@frontend**: 0 API 契约变更
- **@ai-ml**: Stage 2 prompt 无改动, schema 更宽松 (accept human fields as fallback)
- **@tester**: test21 Stage 2 schema 不再拒绝 digital_virtual 角色 — 可重跑 test21 e2e 验证

### Backend 未重启

等 PM 审查后重启 (含 Wave 3 改动一起生效).

---

## ✅ [Wave 3] T20-51 + T20-52 + T20-53 (3 P3 long-tail) [2026-05-20 ~21:00]

### T20-51: BGM meta-prompt 迁出 test_output

- `app/services/music_generation_service.py` META_PROMPT_DIR: 旧 `test_output/manualtest/.../meta_prompts` → 新 `app/prompts/bgm`
- 新建 `app/prompts/bgm/meta_mixed_v3_quote_picking.md` + `meta_en_v2.md` (100% 与旧文件 diff 一致)
- 旧 test_output 文件保留不删
- 测试: `tests/test_t20_51_bgm_meta_prompt_path.py` 9 PASS

### T20-52: test_t20_47 综合 pytest 13 fail 修复 (isolation)

- 根因: `test_t20_43` 注入 `sys.modules["app"] / ["app.services"]` 为无 `__path__` stub
- 修复: `tests/test_t20_47_shot_validator_fallback.py` + `tests/test_t20_50_fix_round3.py` 各加 autouse fixture
- fixture 做: 清除 stub → 重建最小 package → 直接从文件加载 shot_validator (绕过 __init__.py)
- 综合跑验收: 162 PASS 0 fail (修复前 22 fail)
- 生产代码 (shot_validator.py) 无任何改动

### T20-53: SQLAlchemy pool 优化 (新增 pool_timeout)

- `app/database.py` 新增 `pool_timeout=30` (checkout 等待超时)
- 其余 pool 参数在 Wave 4 BUG-T13 修复已就位: pool_pre_ping/pool_recycle/pool_size/max_overflow
- 测试: `tests/test_t20_53_db_pool_config.py` 13 PASS

### 注意 — Backend 未重启

代码已改，等 PM/Founder 决定重启时机。Wave 3 修复全部在下次重启后生效。

---

## ✅ [Wave 2 round 3] 2 P0 修复: SONNET_MODEL ID + save_all_references 不覆盖 [2026-05-20 ~20:00]

### T20-47-fix: shot_validator.py SONNET_MODEL 修正为正确 ID

**改动**: `app/services/shot_validator.py` L184
- 旧: `"claude-sonnet-4-6-20251101"` (404 NotFoundError, test20 100% fail-open)
- 新: `"claude-sonnet-4-6"` (Sonnet 4.6 正确 ID，无日期后缀)
- HAIKU_MODEL `"claude-haiku-4-5-20251001"` 正确，不变

### T20-50-fix-2: reference_image_manager.py save_all_references 不覆盖已存在文件

**改动**: `app/services/reference_image_manager.py` L791-811
- 文件已存在 → skip save + logger.info
- 文件不存在 → 正常 save
- 原则: KEY_LEARNINGS #46 — 磁盘文件 = 最新用户意图，in-memory = 可能是过时副本

### 注意 — Backend PID=79233 正跑 Founder test20 Pipeline，代码改了但未重启

修复在下次 backend 重启后生效。PM: Pipeline 完成后请重启 backend。

---

## ✅ [Wave 2 round 2] T20-48 预防层 wire 真双层防御 [2026-05-20 19:30]

### T20-48 预防层 wire — storyboard_director.py 注入 ANATOMY_FIDELITY_RULES

**背景**: round 1 接了兜底层 (pipeline_orchestrator.py MAX_ANATOMY_RETRIES)，但漏了预防层 (storyboard_director.py 没注入 ANATOMY_FIDELITY_RULES → Seedream 生图 prompt 没收到规则)。

**改动** `app/services/storyboard_director.py`:
- L33: import `ANATOMY_FIDELITY_RULES` from storyboard_prompts
- L1679: `{ANATOMY_FIDELITY_RULES}` 注入 `_build_scene_prompt()` (紧跟 SEEDREAM_SAFETY_AVOIDANCE_RULES)
- L2008: `{ANATOMY_FIDELITY_RULES}` 同步注入 `_build_prompt()` dead code

**验证**: `grep -n "ANATOMY_FIDELITY_RULES" storyboard_director.py` → 3 命中 (L33 + L1679 + L2008)

**新建测试**: `tests/test_t20_48_backend_wire.py` — 10/10 PASS

**Backend**: 旧 PID=75991 已 kill → 新 PID=77188，`/health` → 200 ✅

**真双层防御**:
- 预防层: `storyboard_director._build_scene_prompt()` 注入 `ANATOMY_FIDELITY_RULES` → LLM 生成时已有约束
- 兜底层: `pipeline_orchestrator.py` `MAX_ANATOMY_RETRIES=2` → 图生成后 ShotValidator 检测 anatomy_issue → 最多重生 2 次

---

## ✅ [Wave 2] T20-50b + T20-47 + T20-48 [2026-05-20 18:15]

### T20-50b: adjust_character 已正确重生 portrait + fullbody

**结论**: `app/api/projects.py` adjust_character endpoint 已实现 KEY_LEARNINGS #46:
- 改描述后总是重生 portrait (非阻塞)
- B57 cascade: portrait 成功后总是重生 fullbody (用新 portrait 作 ref)
- Pipeline T20-50 "文件存在即信任" 保证用户改动不被覆盖
- 16 新单测验证完整链路

### T20-47: ShotValidator 现在是 Sonnet 4.6 主模型 + Haiku 4.5 降级备用

**改动** `app/services/shot_validator.py`:
- 主模型: `SONNET_MODEL = "claude-sonnet-4-6-20251101"` (质量更好, 尤其 anatomy 检测)
- 降级: Sonnet 529 × 4 次 → 自动切 `HAIKU_MODEL = "claude-haiku-4-5-20251001"`
- 双失败: fail-open + reason=`SONNET_AND_HAIKU_OVERLOADED`
- 告警: fail-open 率 > 30% → logger.error (DevOps 监控)

### T20-48: anatomy_issue 现在触发最多 2 次自动重生

**改动** `app/services/pipeline_orchestrator.py`:
- `MAX_ANATOMY_RETRIES = 2` (3 次总尝试)
- anatomy 持续 3 次 fail → `shot["_anatomy_partial_failure"] = True` + log ERROR
- 非 anatomy fail 保持 MAX_SHOT_RETRIES=1 不变

### @Frontend

- T20-47: validate_shot 内部模型变化, frontend 0 影响
- T20-48: `_anatomy_partial_failure` 字段已标记在 shot dict, 未来 frontend /preview 可读取显示 warning badge
- T20-50b: adjust_character endpoint 响应不变

### @PM

- 3 task 完成, 58 新单测全 PASS
- Backend 重启 PID=75990, `/health` 200
- 建议 PM 5 维度审查后 → 通知 Founder 跑 test21 验证

---

---

## ✅ [Wave 1 补遗] T20-46 wire + STATUS_API_CONTRACT v1.3 [2026-05-20 17:45]

### T20-46 Backend Wire — pipeline_orchestrator.py

`pipeline_orchestrator.py` L563 现已传 `style_preset` 给 `character_designer.design()`:
```python
characters = await self.character_designer.design(
    outline,
    style_preset=style_preset,  # T20-46: 触发 STYLE_INFUSION_RULES
)
```

**grep 验证**: `style_preset=style_preset` 在 L563，非注释代码行 ✅
**单测**: `tests/test_t20_46_backend_wire.py` 11/11 PASS (新建)
**回归**: `tests/test_t20_46_character_style_infusion.py` 47/47 PASS (AI-ML，不退化)

### STATUS_API_CONTRACT.md v1.3

- 版本号: v1.2 → v1.3
- shots_completed 字段注释升级 (§1.2): 8 stage 行为说明
- 新增 §1.4 跨阶段值表: 8 stage × 期望值
- 新增 §8 v1.3 历史条目

### character_consistency e2e 说明 (给 @pm / @tester)

**T20-50** 修改 `pipeline_orchestrator.py` freshness check 算法移除。
真正的角色一致性验证依赖 Founder **手动重跑 test20/test21** (e2e, 调真 Seedream API)。
Unit test `tests/test_t20_50_freshness_removed.py` 5/5 PASS 验证逻辑正确，但 e2e 一致性不在 unit test 跑。
Founder 验证点: 陈婶/陈砚 portrait 在 test20 中不再被 Pipeline 覆盖。

---

## ✅ T20-50 P0 freshness check 算法移除 [2026-05-20 17:15]

### pipeline_orchestrator.py — freshness check 完全去掉 (KEY_LEARNINGS #46)

**Bug**: `_portrait_fresh = _portrait_mtime > (_char_ts + 30)` 把"刚重生的 portrait"判为"陈旧"→ Pipeline 重新生成覆盖用户重生版本

**修复**: 文件存在即信任，永不覆盖。改为 `if file exists → open + skip=True`，删掉所有 mtime/updated_at/freshness 逻辑。

**新增测试**: `tests/test_t20_50_freshness_removed.py` — 5 个 case (包含旧 bug 重现对比 case)

**Backend 状态**: PID=68942，`/health` {"status":"healthy"}

**验收**: 5/5 新 + 137/137 回归 PASS

---

## ✅ T20-44 P1 shots_completed BGM reset 修复 [2026-05-20 17:15]

### chapters.py — BGM 阶段 shots_completed 不再重置为 0

**Bug**: `else: _shots_completed = 0` 覆盖了 BGM/postprocess 阶段 (Pipeline 里 shots 已全部完成)

**修复**: 加 `_POST_IMAGE_GEN_STAGES = {"bgm", "postprocess", "finalize", "completed"}` — 这些 stage 下 `_shots_completed = shots_total`

**新增测试**: `tests/test_t20_44_shots_completed_timing.py` — 21 个 case

**Frontend 配合工作** (待 Wave 2):
- Frontend `useETA.ts` 应真消费 `status.estimated_remaining_seconds` (不 hardcode "3分钟")
- Frontend ETA 各 5 个 stage 节点对齐 (见 PENDING T20-44)

**API 契约** (shots_completed 字段现在更准确):
- `image_generation` stage: regex 解析 `"已生成 X/Y"` → 实时值
- `bgm` / `postprocess` / `finalize` / `completed` stage: `shots_total` (最终值)
- 早期 stage: `0`

**Backend 状态**: PID=68942，`/health` {"status":"healthy"}

---

## ✅ DEC-043 RISK-T20-?? supernatural humanoid hotfix [2026-05-20 15:35]

### pipeline_schemas.py — _TYPE_REQUIRED_GROUPS 4 个人形超自然 type 修复

test20 horror 镜中人 (supernatural type + 完整人类外貌字段) 触发崩溃已修复。

**修改**: `_TYPE_REQUIRED_GROUPS` 中 supernatural / undead / mythological / fantasy_creature 各自的验证 group 加入 `hair_color / skin_tone / face_shape`，组内字段 OR 关系，任一非空即满足。

**新增**: `tests/test_supernatural_humanoid_hotfix.py` 7 个 case（含 4 个类型正向、老路径不退化、无字段应报错、human type 不受影响）

**Backend 状态**: PID=55021，`/health` {"status":"healthy"}

**验收**: 51/51 pytest PASS，零退化

---

## ✅ T20-29 v3 输出端 wire [2026-05-20 11:30]

### pipeline_schemas.py — SceneSchema + ScreenplaySchema 加 extra='allow'

- `SceneSchema` (L349) 和 `ScreenplaySchema` (L373) 各加 `model_config = ConfigDict(extra='allow')`
- LLM 输出的 `narrative_cluster` / `scene_self_evaluation` 等 v3 字段不再被 Pydantic 默默丢弃
- CharacterSchema (L237) 已有 extra='allow' — 未动

### screenplay_writer.py — validate_scene_self_evaluation 真接通

import 新增 (L26-34):
- `validate_scene_self_evaluation` (AI-ML 写的 prompts.py 里, Backend 只 import 用)
- `get_85_kpi_threshold`
- `detect_narrative_cluster`

3 处 KPI 软警告 (L311 / L339 / L415):
- 每个 scene parse 后调 `validate_scene_self_evaluation(scene)` → 不 raise, 只 `logger.warning`
- PM 看 log 评估改进

P2 narrative_cluster fallback (L1203, `_validate_scene()` 末尾):
- LLM 没输出 `narrative_cluster` 时, 用 `detect_narrative_cluster(plot_text=...)` 自动补 C1-C8

### 验收

- 538/538 pytest PASS (test_t20_* + test_pipeline_*)
- SceneSchema(**v3_dict) 实测 v3 字段全保留
- grep validate_scene_self_evaluation app/services/ → 3 处调用 ✅

---

## ✅ TASK-T20-FIXBATCH-6 Wave 5 v3 wire [2026-05-20 10:45]

### Stage 3 DEC-046 v3 wire (screenplay_writer.py)

`app/services/screenplay_writer.py` 5 处改动:
- import 新增: `DEC046_V3_NARRATIVE_PRINCIPLES` + `DEC046_V3_OUTPUT_EXAMPLE`
- `_build_batch_prompt()`: v3 principles 紧跟 DEC044 rules 后; v3 output example 紧跟 DEC044 output example 后
- `_build_single_scene_prompt()`: 同上两处

**验收**: dry-run Stage 3 prompt 真含 CLUSTER DISPATCHER + SELF-EVALUATION 85% + narrative_cluster + scene_self_evaluation ✅

### Stage 4 DEC-046 v3 wire (storyboard_director.py)

`app/services/storyboard_director.py` 3 处改动:
- import 新增: `DEC046_V3_STAGE4_RULES`
- `_build_scene_prompt()`: `{DEC046_V3_STAGE4_RULES}` 紧跟 SEEDREAM_SAFETY_AVOIDANCE_RULES 后
- `_build_prompt()` dead code: 同步注入

**验收**: dry-run Stage 4 prompt 真含 IMAGE-TEXT COMPLEMENT + MINIMAL DIALOGUE + TIMELINE JUMP MARKER + METAPHOR & SYMBOL ✅

### pytest 全部 PASS

- ✅ 217/217 (test_t20_21 60 + test_t20_17 33 + test_t20_26 23 + test_t20_27 33 + test_t20_28 68 全 PASS)
- ✅ Ben 契约: 0 API 契约变更, 0 schema 变更, 不在 6 监控文件

---

## ✅ TASK-T20-FIXBATCH-5 Wave 4 Backend 收尾 [2026-05-19 23:55]

### Stage 4 SEEDREAM_SAFETY_AVOIDANCE_RULES wire (storyboard_director.py)

`app/services/storyboard_director.py` 3 处改动 (+3 行净增):
- import: `SEEDREAM_SAFETY_AVOIDANCE_RULES` 新增到 storyboard_prompts 导入块
- `_build_scene_prompt()`: `{SEEDREAM_SAFETY_AVOIDANCE_RULES}` 紧跟 SPECIES_FIDELITY_RULES 后注入
- `_build_prompt()` dead code: 同步注入

**验收**: dry-run 验证 Stage 4 prompt 真含 "SEEDREAM CONTENT-SAFETY AVOIDANCE" (7115 chars) ✅

### T20-27 fallback (pipeline_orchestrator.py)

`app/services/pipeline_orchestrator.py` validate_storyboard() 后注入 ~22 行 fallback loop:
- 遍历 storyboard shots
- 条件: `characters_in_scene` 非空 AND `text_overlay.chinese_text` 为空
- 动作: 用 `narration_segment[:25]` 填充 `text_overlay = {text_type: narration, chinese_text: ..., speaker_position: bottom}`
- 日志: `logger.warning("[T20-27] shot X fallback overlay from narration: ...")`

新建 `tests/test_t20_27_pipeline_fallback.py` — 18 cases (6 sections):
- Section 1: 触发场景 (overlay None / {} / "" / whitespace / [])
- Section 2: 不触发场景 (有 overlay / 无角色 / narration 为空)
- Section 3: narration 截断 ≤25 字
- Section 4: 多 shot 混合
- Section 5: test19 Shot 13 复现
- Section 6: fallback schema 完整性

### 验收全 PASS

- ✅ 18/18 `test_t20_27_pipeline_fallback.py` PASS
- ✅ 33/33 `test_t20_17_species_fidelity_stage4.py` PASS
- ✅ 33/33 `test_t20_27_text_overlay_required.py` PASS (AI-ML 写的不退化)
- ✅ 23/23 `test_t20_26_seedream_safety_avoidance.py` PASS
- ✅ 57/57 storyboard test suite PASS
- ✅ py_compile 两个改动文件 PASS

### 给 @tester / @ai-ml

- Stage 4 prompt 层 + Backend wire 全部完成, test20 e2e 可验证 SEEDREAM_SAFETY_AVOIDANCE_RULES 生效
- T20-27 fallback test19 Shot 13 场景已有单测覆盖

### 给 @pm

- 不需改 STATUS_API_CONTRACT.md
- `[frontend-impact: no]` — 0 API 契约变更
- **不需要重启 backend** (本次改动无运行时状态), 但如果 PM 已为 T20-26 重启, 这两个改动自动生效

---

## ✅ TASK-T20-FIXBATCH-5 Wave 4 T20-26 [2026-05-19 22:55] — regenerate flow replace 策略

### 改动 3 文件 (0 越权 — 全在白名单内)

| 文件 | 状态 | 改动 |
|------|------|------|
| `app/services/shot_prompt_rewriter.py` | 新建 | 568 行 — Backend 兜底层: KNOWN_DARK_TERMS + check_replace_effective + strip_known_dark_terms + build_replace_user_prompt (保留 helper) + scene/character context extractors |
| `app/api/chapters.py` `regenerate_shot` L2056-2168 | 改 | 改 user prompt 构造方式: 用 AI-ML 升级的 `build_adjustment_user_prompt(mode="auto")` 而非旧手写 `build_adjustment_user_prompt(original, intent)` (旧版 Rule 1 强制保留原 prompt → append bug). Haiku 返回后调 check_replace_effective + 兜底 strip_known_dark_terms + 完整日志 |
| `tests/test_t20_26_regenerate_replace_flow.py` | 新建 | 60 单测 8 sections (build_replace_user_prompt 12 + find_known_dark_terms 11 + strip_known_dark_terms 7 + check_replace_effective 6 + gather_scene_context 6 + gather_character_context 6 + E2E acceptance 3 + KNOWN_DARK_TERMS 完整性 9) |

### 真实链路 (Founder StageD "调整画面" → 生图)

```
Founder 点 "调整画面" (intent 中文)
    ↓
POST /api/projects/{uuid}/chapters/1/shots/{id}/regenerate (body.adjustment_intent)
    ↓
chapters.py:regenerate_shot endpoint (L1998-)
    ↓
1. detect_seedream_tripwire(original_prompt) — 日志记 mode A/B
2. build_adjustment_user_prompt(prompt, intent, mode="auto")  ← AI-ML 升级的 builder
   ↓ 内部 auto detect tripwire 切 Mode B (REPLACE-AND-CLEAN)
3. Haiku 4.5 (AsyncAnthropic) max_tokens=3000 + SHOT_ADJUSTMENT_SYSTEM_PROMPT
   ↓ Haiku Mode B 完全重写 (不 append) + 自检 verify 删干净
4. check_replace_effective(orig, rewritten) ← Backend 强制校验
   - rewritten 仍含 KNOWN_DARK_TERMS → 标 effective=False
   - 长度 ratio > 2.0x → 怀疑 append → 标 effective=False
5. 若 effective=False: strip_known_dark_terms(rewritten) ← 机械兜底
   - 长短语优先 + 大小写不敏感 + 替换为 safe alternatives
6. 写回 storyboard_json (持久化 image_prompt)
7. 走真生图 (SeedreamGenerator) — 同 pipeline 路径
```

### Mode A/B 自动判定 (AI-ML 设计)

| 触发词存在? | Mode | Haiku 行为 |
|-----------|------|----------|
| 无 (e.g. "让他笑起来") | A — SURGICAL EDIT | 旧 minimal modification, 不动其他元素 |
| 含 ghost / double-exposure / two faces 等 | B — REPLACE-AND-CLEAN | 完全重写, 强制 strip + verify, 输出 300-600 词 (比原短 30-60%) |

### Backend 兜底层 (双层保险)

```
Haiku 即便走 Mode B 也可能漏 (LLM 不 100% 可靠)
    ↓
check_replace_effective() → 找 Haiku 漏的敏感词
    ↓ 漏了
strip_known_dark_terms() → 机械替换 (长短语优先, 不会拼接)
    ↓ 输出
"warm light" / "split composition" / "in fond memory" / "two figures separated"
```

### KNOWN_DARK_TERMS (Backend 内部列表 ~40 词)

5 类:
1. 灵异类 — ghost / ghostly / spectre / phantom / apparition / spectral
2. 双重曝光类 — double-exposure / double exposure / face overlapping / faces merging / two faces merging
3. 已故角色出现类 — deceased emerges / deceased appears / dead emerging / corpse appears
4. 身体特征重叠类 — identical jaw / identical face / merged face / morphing faces
5. Vision overlay 类 — vision of the deceased / image of the deceased / spirit overlay / vision overlay

(与 AI-ML SEEDREAM_TRIPWIRE_KEYWORDS 有重叠, 但不必完全一致 — Backend 兜底 = 双层防线)

### API 响应字段 (frontend 无 breaking change)

```json
{
  "status": "completed",
  "shot_id": 15,
  "imageUrl": "/static/outputs/{uuid}/images/shot_15.png?v=...",
  "skipped": false,
  "prompt_modified": true,                 // ← 现在更可靠 (Mode B 必触发)
  "modified_prompt_preview": "Wide shot, eye level. Chen Yan...",
  "message": "[SeedreamGenerator] Shot 15 重新生成成功（prompt 已由 Haiku 修改）"
}
```

无新字段 → `[frontend-impact: no]`. STATUS_API_CONTRACT.md 不需要改 (regenerate-shot 不是 status endpoint 的 13 字段).

### 验证

- ✅ 60/60 `test_t20_26_regenerate_replace_flow.py` PASS
- ✅ 55/55 `test_t20_26_prompt_rewriter_replace.py` + `test_t20_26_seedream_safety_avoidance.py` (AI-ML 写, Backend 不动) PASS
- ✅ 9/9 `test_shot_regenerate_persistence.py` PASS (regenerate 主流程不退化)
- ✅ 15/15 `test_async_anthropic_t18_j.py` PASS (T18-J AsyncAnthropic 检查不退化)
- ✅ 400/400 综合 (Wave 1-4 + T20 系列) PASS
- ✅ 1218 全 suite PASS, 4 fail + 6 error 全 pre-existing (与本次无关)
- ✅ py_compile chapters.py + shot_prompt_rewriter.py PASS

### 给 @AI-ML

- ✅ 你的 `SHOT_ADJUSTMENT_SYSTEM_PROMPT` Two-Mode + `build_adjustment_user_prompt(mode="auto")` + `detect_seedream_tripwire` 已被 Backend wire 接通 (chapters.py:regenerate_shot L2056-2113).
- ✅ Mode auto 自动 detect tripwire 已生效, Founder StageD "调整画面" 走真 replace.
- ⚠️ Backend 加了**双层兜底**: 你的 LLM-side replace + Backend 的 check_replace_effective + strip 机械防线. 如果 Haiku 漏删了某词 → Backend 自动 strip.
- 0 影响你的 prompt 文件改动 (只读 import).

### 给 @Frontend

- ✅ regenerate-shot endpoint 响应字段无变化 — frontend 0 改动.
- ✅ `prompt_modified` 字段语义不变, message 字符串轻微调整 (现含 "Haiku 修改" 标识).
- 无新字段 (replace_strategy / tripwire_hits 等只在 backend log).

### 给 @Tester (e2e 监控指标)

下一轮 Founder 手动测 test20 暗黑题材时, 监控 backend log:

1. **`[T20-26][Shot Regenerate] strategy=mode_X_...`** — 期望:
   - 含 ghost/double-exposure 等 shot: `strategy=mode_B_ok` (Haiku 自己删干净)
   - 偶尔: `strategy=mode_B_with_mech_strip_fallback` (Haiku 漏了, Backend 兜底)
   - 普通 shot (无敏感词): `strategy=mode_A_ok`
2. **`tripwire_hits=[...]`** — Mode B 触发时 ≥1 个; Mode A 应空
3. **`orig_dark=[...]`** vs **`new_dark=...`** — orig 有, new 无 = replace 真生效
4. **`ratio=...x`** — 应在 0.4-1.5x 区间 (Mode B 应更短). > 2.0x 标 warning (旧 append bug 重现)
5. **重生 Shot 15 同类场景**: Founder intent "陈砚跪在雪地" → 应不再 content_safety failure

### 给 @PM (Ben 契约审查)

- `app/api/chapters.py` 改动**仅** `regenerate_shot` endpoint (L2056-2168), 不动 STATUS_API_CONTRACT 监控的 13 字段.
- 响应 schema **无新字段**.
- **`[frontend-impact: no]`** — 无需改 STATUS_API_CONTRACT.md, 无需升 v1.3.
- Commit message 应含 `[frontend-impact: no]` label.

### 注意事项 (Founder 接下来手动测)

- Backend **未重启** (PM 决定时机).
- Founder StageD "调整画面" 流程改了 user prompt 构造 + 加了 verify/strip 兜底, **重启后才生效**.
- 如想本地验证 effective 字段含意, 看 backend log `[T20-26][Shot Regenerate] strategy=...`.

---

## ✅ T20-17 Backend Wire — Stage 4 Species Fidelity [2026-05-19 20:00]

### 改动 (`app/services/storyboard_director.py`, 4 处)

1. **import**: 加 `SPECIES_FIDELITY_RULES` + `build_stage4_character_data_block`
2. **`_build_scene_prompt()` L1534-1558**: 替换旧 chars_simplified loop → `characters_block = build_stage4_character_data_block(characters)`
3. **prompt 模板**: `{characters_json}` → `{characters_block}` (自带 "Character data:" 前缀, 去掉重复 header)
4. **prompt 模板**: `{HAIR_COLOR_REQUIREMENT_RULE}` 后注入 `{SPECIES_FIDELITY_RULES}`
5. **`_build_prompt()` dead code**: 同步 Option A 改动, 避免未来 reactivate 时漏修

### 验证结果

- Stage 4 LLM 现在能看到: `character_type`, `species`, `appearance`, `distinctive_marks`
- char_002 Milly: `"species":"rabbit"` (不再是 clothing-only, 不再 hallucinate "hedgehog-like")
- Character data JSON 块: 0 中文字符
- SPECIES_FIDELITY_RULES (5711 chars) 注入成功, 含 "hedgehog-like" 显式禁止
- Prompt size: 64748 chars (test17 v2 scene 4)

### 测试

- 33/33 `test_t20_17_species_fidelity_stage4.py` PASS (0.65s)
- 13/13 `test_storyboard_director_schema_fix.py` PASS
- 79/79 `test_t20_10` + `test_t20_21` PASS
- py_compile PASS

### 无越权

仅改 `app/services/storyboard_director.py` (Backend 白名单) — 未改 AI-ML 文件, 未改 Frontend

---

## ✅ TASK-T20-FIXBATCH-4 Wave 2 [2026-05-19 19:00] — T20-21 wire + T20-9.v3 ETA

### 🚨 Frontend agent: estimated_remaining_seconds 算法升级 (schema 不变)

**v3 接管 image_generation/bgm/completed/image_preparation 阶段 ETA**:
- 直接读 `status.estimated_remaining_seconds` (现在更准, **不需要前端 fallback 算法**)
- 删除任何 hardcoded `STAGE_BUDGET_SECONDS[image_generation] = 1440` fallback (backend v3 已准)
- progress >= 95% 也显示具体数字 (不再"即将完成") — Founder 反馈核心修复
- 如要本地校验, 可用 `shots_total - shots_completed` 显示 "已生成 X/Y 张"

**Founder 4 P0 问题修复对照**:

| Founder 反馈 | v3 修复 |
|------|---------|
| #1 progress=84% 但 Shot 14/20 才开始 | 用真实 shots_completed 替代 progress 反推 |
| #2 前端"自说自话" | backend v3 直接返真实 ETA, frontend 直显 |
| #3 progress >= 95% 显"即将完成"无数字 | v3 保底 ≥5s 具体数值 |
| #4 跨 stage 累积漏 BGM | image_generation ETA 含 bgm(120) + postprocess(30) |

### v3 算法公式 (Frontend useETA.ts 参考)

```typescript
// Backend chapters.py _compute_v3_eta() 算法:
if (stage === "image_generation") {
  remaining_shots = shots_total - shots_completed
  image_gen_remaining = remaining_shots * 80 / max_concurrent
  total = image_gen_remaining + 120 (bgm) + 30 (postprocess)
} else if (stage === "bgm") {
  frac = (progress - 92) / 8
  bgm_remaining = 120 * (1 - frac)
  total = bgm_remaining + 30 (postprocess)
} else if (stage === "completed") {
  total = 0
} else if (stage === "image_preparation") {
  total = max(legacy_eta, full_image_gen + bgm + postprocess)
} else {
  // 早期 stage → 走 legacy chain (向后兼容)
}
```

### T20-21 wire — Stage 3 接通 DEC-044 prompts

**改动** (`app/services/screenplay_writer.py`):
- import `DEC044_SCREENPLAY_RULES` + `DEC044_SCREENPLAY_OUTPUT_EXAMPLE` + `get_dec044_narration_max_chars`
- `_build_batch_prompt()` + `_build_single_scene_prompt()` 各 2 处注入
- `target_narration_words` 从 `max(80, dur*4)` (80-400 chars) → `min(120, dur*1.5)` (≤120 hard cap, DEC-044)
- 删旧"【字数硬性要求】" + "TTS朗读旁白" 文本
- `_expand_narration_if_needed()` v1 disable

**真实效果** (期望 LLM 输出):
- 每 scene narration ≤120 CJK chars (旧 245-370)
- 每 scene ≥1 thought + ≥1 plot-essential dialogue/thought (含数字/线索/决定/揭示)
- dialogue 每句 ≤25 chars (caption-friendly)

**Stage 4 自动受益**: storyboard_director.py 已 import COMIC_MODE_NARRATIVE_RULES (AI-ML Wave 1 已升级, Backend 0 改动)

**StageD.tsx 影响**:
- 显示字段仍读 `currentShot.narrationSegment` (T20-21 重构后该字段自动变短)
- DEC-044 "旁白(只读)→描述(只读)" 文案 Frontend 已改 (5/19 Wave 1)

### 其他 agent 注意

- **@tester**: e2e 验证 v3 ETA 真实场景:
  - image_generation 阶段每 5s 测一次 backend `estimated_remaining_seconds`, 误差 < ±20%
  - progress 95% 不再显 0 / "即将完成"
  - bgm 阶段 ETA 平滑减少
  - 早期 stage (storyboard 没生成) 仍走原 legacy 链
- **@ai-ml**: T20-21 wire 已生效, 你 Wave 2 可继续 T20-17 Shot 10 角色异象排查 (storyboard_prompts.py)
- **@pm**: 5 维度 Review T20-21 wire 是否真接通 (跑 test17 v3 看 narration 长度) + T20-9.v3 ETA (实测 image_generation 阶段)

### 改动文件 (3 修改 + 2 新建 + 1 文档)

修改:
1. `app/services/screenplay_writer.py`
2. `app/api/chapters.py`
3. `.team-brain/contracts/STATUS_API_CONTRACT.md` (v1.1 → v1.2)

新建:
4. `tests/test_t20_21_wire.py` (18 case)
5. `tests/test_t20_9_v3_eta.py` (32 case)

---

## ✅ TASK-T20-FIXBATCH-4 Wave 1 [2026-05-19 17:20] — T20-13 P0 + T20-14 P0 + T20-19 P1

### 🚨 Frontend agent: 关注 API 契约新增 3 字段 (Wave 2 消费)

`ChapterStatus` (GET `/api/projects/{uuid}/chapters/1/status`) **新增 3 shot 级真实计数字段**:

```typescript
interface ChapterStatus {
  // ... 已有字段
  estimated_remaining_seconds: number | null;
  actual_shot_count: number | null;
  max_concurrent: number | null;

  // 🆕 RISK-T20-13 (2026-05-19) — Wave 2 frontend 用真字段算 ETA / 不再 regex 解析 message
  shots_total: number | null;       // Stage 4 完成后总 shot 数 (= actual_shot_count, 语义独立)
  shots_completed: number | null;   // 已完成 shot 数 (成功+失败合计, image_generation 内动态)
  shots_failed: number | null;      // 已失败 shot 数 (= job.failed_shot_count, T15-9 mid-stage 实时累加)
}
```

**Frontend useETA.ts 行动建议 (Wave 2)**:
- 删除 `message` 字段 regex "已生成 X/Y" 解析 (T20-13 后不再需要)
- 直接读 `shots_completed` / `shots_total` / `shots_failed`
- in_flight 可派生: `shots_in_flight = shots_total - shots_completed`
- ETA 更精: `(shots_total - shots_completed) * 80 / max_concurrent`
- 早期 stage (storyboard 未生成) → 3 字段全 null (向后兼容)

### shots_completed 派生规则 (universal, 不破坏向后兼容)

| stage | shots_completed 值 |
|-------|-------------------|
| story_generation / character_design / screenplay / storyboard | 0 |
| image_preparation | 0 (还没进 image_generation) |
| image_generation | 优先 regex `已生成 X/Y` → `X`; 兜底 `progress` 反推 `(progress-75)*total/20` |
| bgm | 0 (不计图像阶段) |
| completed | shots_total (无论 message) |

### T20-14 P0 — ShotValidator 加 Anthropic 429/529/503 退避重试

**改动** (`app/services/shot_validator.py`):
- 2 helper: `_is_retryable_anthropic_error(exc)` + `_call_anthropic_with_retry(client, ...)`
- validate_shot 内 messages.create → 改用 _call_anthropic_with_retry
- 退避阶梯: 2 / 8 / 30s + ±30% jitter (类似 Seedream)
- 最多 3 重试 (4 总尝试), 仍失败才走 fail-open
- except 路径区分 reason: `OVERLOAD_RETRY_EXHAUSTED_{code}` (ERROR 级日志) vs `API_ERROR_SKIPPED` (WARNING)

**影响**: test17 v2 实测 18/18 Anthropic 调用 529 全 fail-open → B51 fallback 形同虚设。修后大部分 529 应被自愈重试覆盖, ShotValidator 真验证率应显著提升。

**其他 agent 注意**:
- 不破坏 validator API 接口 (return dict shape 不变)
- fail-open 行为保留 (valid=True 不阻塞 Pipeline)
- @tester 监控日志: `OVERLOAD_RETRY_EXHAUSTED_*` ERROR 级日志频率 (告警阈值)
- 重试期间 WARNING 级日志: `Anthropic 529 (attempt N/4), sleep Xs 后重试 (T20-14)`

### T20-19 P1 — Pipeline 单 Shot wall-clock timeout (720s)

**改动** (`app/services/pipeline_orchestrator.py`):
- 加常量 `SHOT_WALL_CLOCK_TIMEOUT_SEC = 720` (12 min)
- `_generate_one_shot` 内 `generate_shot_image_phase2_safe` 包到 `asyncio.wait_for`
- TimeoutError → 返回 `{success: False, error_kind: "wall_clock_timeout"}`, 不 retry, 走原失败路径

**影响**: test17 v2 实测 Shot 14 hang 12.5 min, Shot 16 hang 14.2 min (DevOps 诊断 ~15 min 理论最坏)。修后 Pipeline 不会被单个假死 shot 拖死整批。Frontend "查看并重生" 仍能救 (走 partial_failure 路径)。

**其他 agent 注意**:
- Frontend: error_kind="wall_clock_timeout" 是新错误类型, 与既有 IncompleteRead / rate_limit / content_safety_failure 并列
- Tester: e2e 监控 logger.error `T20-19` 出现频率
- @ai-ml: 无影响

---

## ✅ TASK-T20-FIXBATCH-2 Backend #1 [2026-05-18 20:50] — T20-9 P0 + T20-8 P3 (已修)

### 🚨 Frontend agent: 关注 API 契约变化

`ChapterStatus` (GET `/api/projects/{uuid}/chapters/1/status`) **新增 2 字段** + 1 字段精度提升:

```typescript
interface ChapterStatus {
  // ...
  estimated_remaining_seconds: number | null;  // 已存在 — T20-9 修后更准 (per_shot 60→80 + 真实 progress 替代 hardcoded 0.5)
  actual_shot_count: number | null;            // 新增 — Stage 4 后真实 shot 数 (storyboard_json.shots.length)
  max_concurrent: number | null;               // 新增 — Seedream 并发数 (settings.IMAGE_MAX_CONCURRENT, 默认 3)
}
```

**Frontend useETA.ts 行动建议**:
1. 优先用 `estimated_remaining_seconds` (已更准)
2. 当 null 时, **不再用 hardcoded `STAGE_BUDGET_SECONDS[image_generation] = 1440`**
3. 改用动态公式: `actual_shot_count * 80 / max_concurrent` (匹配 backend per_shot 80s)
4. universal: 任何 shot count (5/19/29/50) 都准确

**为什么这次修改 ETA 估算更准了？**:
- 旧: `19 shots × 60 / 3 = 380s` → 实测 540s, **低估 42%**
- 新: `19 shots × 80 / 3 = 506s` → 实测 540s, **低估 6%** (符合用户预期)

### T20-9 / T20-8 修改影响范围

**T20-9 P0**:
- `pipeline_orchestrator.py` `build_stage_durations` per_shot 60 → 80
- `job_manager.py` `calculate_eta_remaining_sec` per_shot 60 → 80 (双源同步)
- `chapters.py` fallback 改用真实 progress + 加 actual_shot_count/max_concurrent 透传
- `schemas/chapter.py` ChapterStatus 加 2 字段

**T20-8 P3**:
- `projects.py` confirm_outline UX-2 prompt 加 R6-2 设计说明 (selected_ending 在 plot_points[-1] 不在 selected_ending 字段)
- `story_outline_generator.py` system_prompt + JSON 示例 + _validate_outline 兜底 normalization
  - 每个 ending_options 强制含 `id` + `ending_id` 双字段 (LLM 漏写时兜底 ending_{i+1})
  - 不破坏 frontend `e.id` 读法 (CreateContent.tsx:833)

### 新单元测试 (26 case)
- `tests/test_t20_9_estimated_remaining.py` (17 case: 5 per_shot calibration + 3 concurrent scaling + 4 stage+progress + 1 helper sync + 4 robustness)
- `tests/test_t20_8_outline_structure.py` (9 case: 6 ending normalization + 2 UX-2 prompt + 1 universal 跨故事)

### Universal 视角
- T20-9: 5/19/29/50 shots × 1/3/6 concurrent × 任何 stage progress → universal 准确，0 hardcode test18
- T20-8: 3/5 endings × 浪漫/悬疑/幽默 mood → universal 适配 R6-2 设计

---

## ✅ TASK-T20-FIXBATCH-2 Backend #2 [2026-05-18 21:00] — T17-1+T18-J+T19-9+POST_BETA-5 (已修)

**影响 @pm / @tester**:

- **T17-1**: `prompt_safety_advisor.py` 换用 `extract_json_from_llm_response`，LLM 返回 markdown JSON 时不再解析失败
- **T18-J**: `alignment_service.py` + `app/api/chapters.py` → `AsyncAnthropic()` + `await`，不再阻塞 event loop
- **T19-9**: `story_music_extractor.py` 加 `emotional_arc` isinstance 防御（仿 T19-5 visual_tone/atmosphere 模式）
- **POST_BETA-5**: `image_generator.py` 3 个 dispatch 块 + `seedream_generator.py` 加 `refs=N (M portrait + K scene_ref)` 日志

**Universal 视角**: 任何故事的 LLM JSON 输出、async 路径、音画对齐、dispatch 日志均受益

**新测试文件** (64 case 全 PASS):
- `tests/test_markdown_json_defense_t17_1.py` (19)
- `tests/test_async_anthropic_t18_j.py` (15)
- `tests/test_emotional_arc_dict_str_defense.py` (14)
- `tests/test_dispatch_logging_post_beta_5.py` (16)

---

## ✅ TASK-T20-FIXBATCH T20-6 wiring [2026-05-18 17:15] — ShotValidator universal skip 激活 (已修)

**影响 @pm / @tester / @ai-ml**:

- **T20-6 universal skip 现已真正生效**: `pipeline_orchestrator.py:L1285` `validate_shot(...)` 加了 `shot=shot,`
- 修复前: `should_skip_character_count_check(shot)` 函数存在但 0 调用 (shot=None 走原严格检查)
- 修复后: fallback shot / wide shot / environmental / no-char prompt → 角色数检查被 skip → 不再误报"角色数量不匹配"
- 向后兼容: 正常 close-up / medium shot 仍走严格检查，行为不变

**修改文件**:
1. `app/services/pipeline_orchestrator.py` — L1289 加 `shot=shot,`（1 行）

**验证**:
- py_compile PASS
- 30/30 universal skip 单测 PASS
- 服务 PID 53809 + HTTP 200

---

## ✅ TASK-T20-FIXBATCH T20-3 [2026-05-18 16:15] — P0 招牌污染修复 (已修)

**影响 @pm / @tester**:

- **根因已修**: `scene_reference_manager.py` `_detect_signage_name` keyword fallback 全删除
- 修复前: "陈默租住楼的雨夜楼道口" 含"楼" → 误判为招牌场所 → 整段 display_name 渲染到 scene_ref → Shot 5/8/13 被污染
- 修复后: 完全信任 Stage 1 LLM 的 signage_text 字段决策 (空 = 无招牌, 有值 = 招牌名)
- universal: 都市/校园/古装/科幻任何故事类型中含"楼/店/铺..."字的非招牌场所均不会误判

**修改文件**:
1. `app/services/scene_reference_manager.py` — `_detect_signage_name` L739-756 (删 keyword fallback, 加设计意图注释)

**验证**:
- py_compile PASS
- 5/5 universal 测试用例 PASS
- 693 pytest PASS + 0 新增 fail
- 服务重启新 PID + HTTP 200

---

## ✅ TASK-WAVE14-RISK-T19-7 [2026-05-15 19:30] — IMAGE_TOO_LARGE 真压缩 (P1 已修)

**影响 @pm / @tester**:

- **根因已修**: `_compress_for_claude` target 从 4.5 MB 降到 **3.5 MB binary**（base64 后 4.65 MB < 5 MB 安全）
- 旧 target 4.5 MB binary → base64 后 ~6 MB → 仍超 Anthropic 5 MB 限制 → IMAGE_TOO_LARGE_SKIPPED → 验证器隐式失效
- 新策略 resize 优先：scale(0.75/0.60/0.50/0.40) × quality(80/65) 8 级 + 极端 fallback，对 1664×2218 Seedream 输出 Shot 21 有效
- base64 实际大小 warning 日志（> 4.8 MB 时告警，方便监控）
- 9/9 新单测 + 9/9 Wave 11.4 regression PASS

**修改文件**:
1. `app/services/shot_validator.py` — `_compress_for_claude` L52-113 全改 + validate_shot 日志增强 L337-351
2. `tests/test_image_compression_safety.py` — 新建 9 case

**@PM 待决策（记录）**:
- 是否需要在 `ReferenceImageManager` / `seedream_generator.py` 输出阶段也压缩？
  - 建议：**不必要**。参考图 /preview 需保留原始质量；ShotValidator 入口压缩已足够
  - ReferenceImageManager 生成的 portrait/fullbody 本身不发给 Anthropic API，无 5 MB 限制问题

---

## ✅ TASK-WAVE14-RISK-T19-5 [2026-05-15 17:55] — BGM dict/str 双修 (P1 已修)

**影响 @pm / @tester**:

- **根因已封堵**: `story_music_extractor.py` L416 visual_tone + L470 atmosphere 双修 isinstance 防御
- test19 实际 atmosphere = str `"tranquil, 远山鸟鸣..."` 之前导致 `'str' object has no attribute 'get'` → BGM Stage 6 失败（非阻塞但 BGM 缺失）
- 修复后: str 类型首段作为 mood，dict 类型正常路径，None/int 兜底为空 dict
- 15 新单测（含真实 test19 数据回归）+ 152/152 regression PASS

**修改文件** (Wave 14 Backend #2, 0 冲突):
1. `app/services/story_music_extractor.py` — L416-432 visual_tone + L488-511 atmosphere 双防御
2. `tests/test_bgm_dict_str_defense.py` — 新建 15 case

**Bonus 发现** (记录给 PM):
- `story_music_extractor.py L444`: `arc: dict = outline.get("emotional_arc", {})` 后直接 `arc.get()` — 同样模式，test19 数据是 dict 所以未触发，理论风险存在。当前 RISK 范围未修，已记录

---

## ✅ TASK-WAVE13-RISK-T19-4 [2026-05-15 17:15] — scene_heading 中文防御双修 (P0 已修)

**影响 @pm / @tester**:

- **根因已封堵 (A: 治根)**: `screenplay_writer.py` Batch + 逐 scene 两处 CRITICAL 约束块扩展，加 Rule 1: scene_heading 英文约束 + 对比示例，LLM 不应再输出中文 scene_heading
- **防御层已加固 (B: 防御)**: `storyboard_director.py` B51 fallback 路径 L682-692 新增 scene_heading 中文检测（复用 `_contains_chinese()`），含中文时替换为 `"Scene {scene_id}"` + WARN 日志
- **中文来源全封堵**: B51 fallback_image_prompt 的所有拼装来源（scene_heading + atmosphere_str）均已防御
- 18 个新单测 + Wave 12 regression 39/39 + Wave 10/11 regression 155/155 全 PASS

**修改文件**:
1. `app/services/screenplay_writer.py` — Batch 模式 + 逐 scene 模式 CRITICAL 约束块
2. `app/services/storyboard_director.py` — L682-692 scene_heading 中文防御
3. `tests/test_scene_heading_chinese_defense.py` — 新建 18 case

**Founder 下一步**: 当前 failed test19 点"原地重启" → 第三次 Pipeline → 期望 Stage 4 通过（atmosphere ✅ + scene_heading ✅）

---

## ✅ TASK-WAVE12-RISK-T17-8 [2026-05-15 16:30] — Pipeline 失败原地重启从 Stage 4 (P0 已修)

**影响 @pm / @frontend / @tester**:

**新 endpoint** (给 Frontend 接入):
```
POST /api/projects/{project_id}/chapters/{chapter_number}/restart-from-failed-stage
```
- 无 request body，chapter.status 必须 = "failed"
- 成功响应:
```json
{
  "success": true,
  "message": "Pipeline 已从 Stage 4 重启",
  "failed_stage": 4,
  "start_from_stage": 4,
  "job_id": 123,
  "chapter_status": "pending"
}
```
- 422: 1_outline.json 不存在（Stage 1 前就失败的情况，不能原地重启）
- 400: chapter.status != "failed"
- 404: project/chapter 不存在

**Pipeline 新参数** (给 @tester 了解):
- `pipeline_orchestrator.run(start_from_stage=4)` — 从 disk 加载 1-3_xxx.json，跳过 LLM，直接跑 Stage 4+
- Stage 4 失败重启 (最常见): R4-1/R4-2 都自动跳过，无需 DB 轮询

**改动文件**:
1. `app/services/pipeline_orchestrator.py` — `run()` + `start_from_stage` 参数
2. `app/api/chapters.py` — 新 endpoint + helper
3. `tests/test_pipeline_restart.py` — 14/14 PASS

---

## ✅ TASK-WAVE12-RISK-T19-1 [2026-05-15 15:55] — atmosphere 中文防御双修 (P0 已修)

**影响 @pm / @tester / @ai-ml**:

- **根因已封堵 (A: 治根)**: `screenplay_writer.py` Batch + 逐 scene 两处 prompt 模板加了 CRITICAL ENGLISH ONLY 约束块，LLM 不应再输出中文 atmosphere 字段
- **防御层已加固 (B: 防御)**: `storyboard_director.py` `_atmosphere_to_str()` 新增中文检测，含中文字段自动跳过 + WARN 日志，fallback image_prompt 不会再含中文
- **新增辅助函数**: `_contains_chinese(text: str) -> bool` 检测 CJK Unified Ideographs 范围
- 22 个新单测 + 10+7 Wave10.1/b58 回归全 PASS

**改动文件**:
1. `app/services/screenplay_writer.py`
2. `app/services/storyboard_director.py`
3. `tests/test_atmosphere_chinese_defense.py` (新建)

**@ai-ml 注意**: 正常路径 (Stage 4 LLM 生成 image_prompt 时) 也可能把中文 atmosphere 上下文复制进去，这是 Prompt 层面风险，本次修复覆盖了 fallback 路径。如果 test20 验证后仍有中文泄漏案例，可能需要 Stage 4 prompt 加"禁止复制 atmosphere 字符串到 image_prompt"约束。

---

## ✅ TASK-RISK-NEW-2-CONFIG-UNIFY [2026-05-14 23:40] — IMAGE_GENERATION_TIMEOUT 配置统一

**影响 @pm / @devops**:

- `app/config.py` L33: `IMAGE_GENERATION_TIMEOUT: int = 210`（原 120）— 新增 Wave 11.4 注释
- `app/services/seedream_generator.py` L103: `SEEDREAM_TIMEOUT_SEC = settings.IMAGE_GENERATION_TIMEOUT`（原 hardcoded 210）
- timeout 现在统一受 `config.py` 控制，可通过 `.env IMAGE_GENERATION_TIMEOUT=xxx` 覆盖
- NB2 路径（image_generator.py）未动：grep 确认 NB2 不消费 IMAGE_GENERATION_TIMEOUT，不影响

**0 越权**: 只改 `app/config.py` + `app/services/seedream_generator.py` + backend-progress 三件套

---

## ✅ TASK-WAVE11.4-TIMEOUT-210 [2026-05-14 22:40] — SEEDREAM_TIMEOUT_SEC 180→210

**影响 @pm / @devops**:

- `app/services/seedream_generator.py` L103: `SEEDREAM_TIMEOUT_SEC = 210`（原 180）
- 防 177s long-tail shots 在 180s 窗口内偶发超时 → +30s buffer
- 仅改常量定义，无逻辑变更，0 风险
- 验证: py_compile PASS + 56/56 regression PASS + grep 0 匹配 "TIMEOUT.*180"

**0 越权**: 只改 `app/services/seedream_generator.py` + backend-progress 三件套

---

## ✅ TASK-WAVE11.4-T18D-SEEDREAM-METRICS-INTEGRATION [2026-05-14 22:10] — SeedreamMetrics 调用链接通

**影响 @pm / @devops**:

- `seedream_generator.py` 新增 import + 6 个 `seedream_metrics.record_shot()` 调用点
- 每次 Shot 生成完成（成功或失败）真实记录到 SeedreamMetrics 全局单例
- `stats()` 在 Pipeline 完整跑完后真有数据（不再是死代码）
- 日志新增 `[SeedreamMetrics] metric recorded shot=X attempt=Y ir=Z to=W` DEBUG 行（可 grep 验证）

**接通路径**:
```
generate_shot_image_seedream() 
  → _call_seedream_sync() 内部累计 _incomplete_read_count / _timeout_count
  → 返回这两个计数到上层
  → generate_shot_image_seedream() 在成功/失败各 return 点调用 seedream_metrics.record_shot()
```

**验证**:
- py_compile PASS + grep 6 调用点 + import verify + 191/191 regression PASS

**需要 @pm**:
- PENDING.md 标 T18-D ✅（完全闭环，不再是死代码）

**0 越权**: 只改 `app/services/seedream_generator.py` + backend-progress 三件套

---

## ✅ TASK-WAVE11.4-T18B-T18D [2026-05-14 21:30] — P2: Seedream 长尾调研 + 监控代码

**影响 @pm / @devops**:

1. **T18-B 长尾调研** (`.team-brain/analysis/SEEDREAM_LONGTAIL_RESEARCH.md`):
   - 长尾根因：阿里云 API 负载波动 + prompt 复杂度（非模型缺陷），无法通过切换模型解决（D.17 铁律）
   - test18 数据：P50=70s, P95=160s, Max=177s, 平均=98s, 长尾(>120s)=21%(6/29)
   - IncompleteRead 24 次全部重试成功，TimeoutError 1 次（4-attempt 失败，Founder 手动重生 48s 成功）

2. **T18-D retry 阈值评估结论**:
   - **4 次 retry 保持不变**（3.4% 在行业基准 <5% 内，增加 retry 反而延长极端失败等待）
   - **建议**: `SEEDREAM_TIMEOUT_SEC` 180s → 210s（为 177s long-tail 留 33s buffer，防偶发超时）
   - 此改动需要 **PM 批准** 才执行（涉及 seedream_generator.py）

3. **新建 `app/services/seedream_metrics.py`**:
   - `SeedreamMetrics` class，全局单例 `seedream_metrics`
   - `record_shot()` / `record_incomplete_read()` / `record_timeout_error()` 三个记录接口
   - `stats()` → 完整统计 dict（total/success/failure_rate/latency P25-P95/longtail/attempt dist）
   - `log_summary()` → INFO 日志一行输出
   - **当前状态**: 已接通 seedream_generator.py 全调用链（T18-D 补漏完成）

4. **新建 `tests/test_seedream_metrics.py`**: 30/30 PASS + 88 regression PASS

---

## ✅ TASK-WAVE11.4-T18A-PROGRESS-PER-SHOT [2026-05-14 21:10] — image_generation per-shot 进度增量

**影响 @pm / @frontend**:

1. **RISK-T18-A 修复 (pipeline_orchestrator.py)**:
   - `_generate_one_shot` success path: `_pct = 65 + int(30 * _done / total)` → `_pct = 75 + int(20 * _done / total)`
   - `_generate_one_shot` failure path: 同上修复
   - **效果**: image_generation 阶段 progress 从 per-milestone 跳变 → per-shot 平滑增量
   - **29 shots**: 每 shot 约 +0.69% (75%→95%，不再卡在 75% 到处跳变)
   - **与 entry callback 对齐**: P1-1 entry 在 75%，新公式从 75% 起步，首 shot 不再低于 entry

2. **新单测**: `tests/test_progress_per_shot.py` — 19/19 PASS
   - 5 类测试: 29-shot / 18-shot / 10-shot / edge cases / ETA bounds 对齐

3. **0 API 破坏性变更**: 纯内部 progress 值调整，不影响任何 API contract

4. **0 越权**: 只改 pipeline_orchestrator.py + 新建 test_progress_per_shot.py

**需要 @pm**:
- 无特殊操作，backend 重启时自动生效（此改动需 backend 重启）
- 标记 RISK-T18-A ✅

---

## ✅ TASK-WAVE11.3-CHAPTERS-ETA-INTEGRATION [2026-05-14 20:30] — Wave 11.3 收尾: actual_elapsed_sec ETA 集成

**影响 @frontend / @pm**:

1. **Wave 11.3 收尾 — status response 新增 `actual_elapsed_sec` 字段**:
   - `app/schemas/chapter.py` L40: `ChapterStatus.actual_elapsed_sec: int | None = None`
   - `app/api/chapters.py` L356-367: job processing 时填入已运行秒数，否则 `None`
   - **API contract 变更**: `GET /api/projects/{id}/chapters/1/status` response 新增可选字段 `actual_elapsed_sec`
   - **字段语义**: `job.status == "processing"` 时返回 `int(utcnow - job.started_at)`（整秒），其他状态返回 `null`
   - **用途**: frontend 可用 `actual_elapsed_sec + estimated_remaining_seconds` 校验总 budget 合理性，或做本地 countdown 修正

2. **0 API 破坏性变更**: `actual_elapsed_sec` 为可选字段（默认 `None`），老 frontend 忽略未知字段，backward compat ✅

3. **154/154 regression PASS**: Wave 11 全部单测（116 + 38）全 PASS

**需要 @pm**:
- backend 重启让改动生效
- PENDING.md 标 RISK-T17-5 ✅（Wave 11.3 backend + chapters.py 集成全部完成）
- 告知 @frontend: status response 中 `actual_elapsed_sec` 字段已上线，Frontend #2 可在 useETA hook 中使用

---

## ✅ TASK-WAVE11.2-T18G-T18E [2026-05-14 19:30] — P1: 404 风暴 + preview 空数据修复

**影响 @frontend / @pm**:

1. **RISK-T18-G 修复 (chapters.py)**:
   - `/story` endpoint (L415-446): 删除 `pending → 404` 分支，无数据时返 `200 + ChapterStory(empty)` 取代 404
   - `/storyboard` endpoint (L568-574): `storyboard_json=null → 200 + {"storyboard": {"shots": []}}` 取代 404
   - 保留正确的 404: project/chapter 不存在; failed → 400
   - **预期效果**: client.log 的 41 次 `[WARN] HTTP_ERROR 404` 降至 0（来自 CreateContent.tsx hydrate + StageC 轮询）
   - **0 越权**: chapters.py L1878-1890 (Wave 11.1 T18-F) 未动

2. **RISK-T18-E 修复 (projects.py)**:
   - 新增 `GET /{project_id}/preview` 端点 (L1560-1660)
   - 返回: `project_id + title + style + aspect_ratio + bgm_url + status + chapters[] + total_shots`
   - 每个 chapter 含: `chapter_number + status + shots (active only) + characters (with portrait_url) + bgm_url`
   - deleted shots 过滤，不计入 total_shots；无数据时返 `chapters=[], total_shots=0`
   - character portrait_url 优先读 characters_json，无则静态路径兜底

3. **新单测**: `tests/test_wave11_2_backend_fixes.py` 22/22 PASS
4. **回归更新**: `test_status_authoritative.py` L317-326 — test 名改为 `test_truly_no_data_returns_empty`（反映新行为）
5. **134/134 regression PASS** (含 test_status_authoritative 81/81)

**需要 @pm**:
- backend 重启让改动生效
- PENDING.md 标 RISK-T18-G + RISK-T18-E ✅
- 告知 @frontend: `/story` + `/storyboard` 不再 404，可停止 try/catch 404 作空数据处理；`/projects/{id}/preview` 端点已上线

---

## ✅ TASK-WAVE11.3-T17-5-ETA [2026-05-14 ~19:00] — P1: ETA 算法全面深挖修复

**影响 @frontend / @pm**:

1. **RISK-T17-5 修复**: `app/services/job_manager.py` 新增 `calculate_eta_remaining_sec()` helper + stage-switch ETA 单调 guard reset
   - 根因: `_last_eta` 单调 guard 从未在 stage 切换时 reset → `image_preparation` 末尾低 ETA 截断 `image_generation` 开始高 ETA → "前面1分钟/后面8分钟" 跳变
   - 修复: 闭包新增 `_last_stage` 变量，stage 切换时 `_last_eta[0] = None`，让新 stage 从自己的 baseline 算 ETA
2. **新单测**: `tests/test_eta_calculation.py` 50 test cases 全 PASS
3. **0 API 变更**: chapters.py status endpoint 无需改动（`job.estimated_seconds` 已被正确写入）
4. **chapters.py 集成 snippet**: PM 统一协调追加 `actual_elapsed_sec` 到 status response（等 Wave 11.2 完成）

**需要 @pm**:
- backend 重启让改动生效
- PENDING.md 标 RISK-T17-5 ✅（backend 部分完成）
- 通知 Frontend #2 (Wave 11.3) ETA hook 可以开始（backend ETA 算法已修复）

---

## ✅ TASK-WAVE11.1-T18F-T17-9 [2026-05-14 17:30] — P0: Shot 重生 portrait+fullbody + adjust_character portrait_ref 闭环

**影响 @frontend / @tester / @pm**:

1. **RISK-T18-F 修复**: `app/api/chapters.py` regenerate_shot endpoint — 每个出场角色现在传 portrait + fullbody 两张（之前只根据 shot_type 选一张）。预期: 下次 Shot 重生 backend log 会显示 `char_refs=2`（1 角色场景）而非 `char_refs=1`
2. **RISK-T17-9 修复**: `app/api/projects.py` adjust_character endpoint — R7-3 重生 portrait 时现在传入现有 portrait 文件作 portrait_ref（identity ground truth）。Wave 10 P2 已修 reference_image_manager.py 接收 portrait_ref，本次修复调用侧真传参，完整闭环
3. **不影响任何 API 契约**: 两处修改都是内部 ref loading 逻辑，对 frontend 的请求/响应结构 0 变化

**需要 @pm**:
- backend 重启让改动生效
- PENDING.md 标 RISK-T18-F + RISK-T17-9 ✅

---

## ✅ TASK-WAVE11.1-T18H-SHOTVALIDATOR-COMPRESSION [2026-05-14 17:10] — P1: ShotValidator 5MB+ 压缩 + 日志格式修复

**影响 @tester / @pm**:

1. **RISK-T18-H 修复完成**: `app/services/shot_validator.py` 已有 `_compress_for_claude()` 压缩函数（PIL JPEG 4.5MB 内）+ Exception handler 改为 `reason="API_ERROR_SKIPPED"` 或 `"IMAGE_TOO_LARGE_SKIPPED"`
2. **新增 `validator_skipped_count` 计数器**: 每次 API 跳过时递增，backend log 可见 `skipped_total=N`，方便监控验证失效率
3. **新单测**: `tests/test_shot_validator_compression.py` 9/9 PASS

**效果预期**:
- 下次 test19 跑 watercolor 风格，Shot 1 1664×2218 PNG ≈ 5.3MB → 压缩后 < 4.5MB → 真调用 Haiku API 验证 → reason="pass" 或 "failed_xxx"（而非之前的 reason=error: image exceeds 5MB...）
- validator_skipped_count 保持 0（没有跳过）→ 角色一致性 audit 真正有效

**不影响**:
- `app/api/projects.py`（Backend #1 正在处理 T18-F + T17-9，0 冲突）
- 任何其他 pipeline 逻辑

---

## ✅ TASK-WAVE10.1-HOTFIX-T17-6 [2026-05-14] — P0 CRITICAL hotfix: atmosphere dict TypeError

**根因**: Stage 3 (Sonnet 4.6) 输出 `atmosphere` 字段为 `{mood, sound_design_hint, temperature_feel}` dict，storyboard_director.py L635 直接 str 拼接 → TypeError → Stage 4 fallback shot 生成 crash。

**修复要点**:
- 新增模块级函数 `_atmosphere_to_str(atm)` 于 `app/services/storyboard_director.py` L323-341
- 支持 str/dict/None/空 dict/其他类型全容错
- dict 时优先返回 `mood` 字段，三字段全拼接用 ", " 分隔
- L654/L658 使用 `atmosphere_str = _atmosphere_to_str(atmosphere)` 替代直接拼接

**不需要改动**:
- `image_generator.py` L988: `scene_atmosphere` 路径实际永远 `""` (pass 分支)，无实际 dict 风险

**影响 @tester**: `tests/test_atmosphere_dict_compat.py` 新建，10 case。regression 63/63 不退化。

---

## ✅ TASK-WAVE10-P2-BACKEND-PERF [2026-05-14] — 5 RISK 全修完成 (Wave 10 Phase 2)

**关键变更** (@tester 必读):

1. **T16-5**: `_is_storyboard_truly_ready()` — `storyboard_json="{}"` 不再误判为 True，必须 shots > 0
2. **T16-2**: portrait regenerate 时传 portrait_ref 作 reference_images，提高重生成的 identity 一致性
3. **T16-1**: ETA stage 内基于全局 progress 动态推算 stage_progress（不再写死 0.5）
4. **T14-10**: 角色参考图 + 场景参考图均改为 asyncio.gather 并行（Semaphore 3 路），预计节省 60%

---

## ✅ TASK-WAVE10-P1A-BACKEND-FIXES [2026-05-14] — 4 RISK 双修完成 (Wave 10 Phase 1A)

**关键变更** (@frontend 和 @tester 必读):

1. **T16-4 (P0 CRITICAL)**: `app/api/projects.py` ConfirmScenes — 改为 merge 而非 replace
   - 以前：`chapter.scenes_json = json.dumps(payload.modified_scenes)` 完全替换
   - 现在：`{**existing_scene, **modified_scene}` merge，保留所有 LLM 字段（含 action_beats）
   - 影响：任何 e2e 测试的 /scenes 确认现在不会丢 action_beats → Stage 4 不再失败

2. **T16-6 (P0)**: `app/services/job_manager.py` L373 — Pipeline 失败时 chapter.status="failed"
   - 以前：`result = {"success": True, "data": pipeline_result}` 硬编码 True
   - 现在：透传 `pipeline_result.get("success", True)` → 失败时 result["success"]=False → chapter.status="failed"
   - 影响：Pipeline 失败后 frontend 不再误跳 /preview 一片黑；status.ui_phase 推导也准确

3. **T16-8 (P2)**: `app/api/projects.py` 新增 `_strip_markdown_json_fence()` 函数
   - UX-2 一致性检查 parse 前显式剥 markdown fence
   - 不影响任何现有接口契约

4. **T16-10 (P1)**: GET /story 无需代码改动——已返完整 scenes
   - 根因是 T16-4 (B58 替换导致 DB 里 scenes_json 只有 4 字段)
   - T16-4 修后，GET /story 自然返完整 scenes (含 action_beats)

---

## ✅ TASK-WAVE9-P2-BACKEND-STATUS-AUTHORITATIVE [2026-05-13 21:50] — DEC-030 主任务完成

**给 @frontend (Wave 9 Phase 2 Frontend 必读)** ⭐⭐⭐⭐⭐:

Backend status endpoint 现在是 frontend state 的 **single source of truth**。frontend 应改造为从 status 派生所有 state，不再本地缓存触发。

**新 status response schema** (GET `/api/projects/{uuid}/chapters/1/status`):

```json
{
  "status": "processing",
  "stage": "scenes_ready",
  "progress": 32,
  "estimated_remaining_seconds": 300,
  "message": "等待确认场景设计...",
  "failed_shot_count": 0,
  "partial_failure": false,
  "ui_phase": "scene_review",                         // ⭐ 新：状态机派生
  "hydrate_hints": {                                  // ⭐ 新：告诉前端 hydrate 哪个 endpoint
    "endpoint": "/api/projects/{project_id}/chapters/1/story",
    "display_field": "scenes",
    "expected_data_shape": "list[Scene]"
  },
  "characters_confirmed": true,                       // ⭐ 新：frontend subPhase 派生用
  "scenes_confirmed": false,                          // ⭐ 新：frontend subPhase 派生用
  "storyboard_ready": false,                          // ⭐ 新：chapter.storyboard_json 非空
  "outline_ready": true                               // ⭐ 新：chapter.full_script/scenes_json 非空
}
```

**`ui_phase` 状态机** (8 phase):

| phase | 含义 | 前端应该 |
|---|---|---|
| `input` | 无 job 无大纲 | 显示输入页 |
| `outline_review` | 大纲生成完等用户在 StageB 确认 | 显示大纲确认页 |
| `char_review_pending` | Stage 1/2 在跑 | /generating 转圈 |
| `char_review` | character_ready + 未确认（R4-1）| 跳 /characters，展示角色卡片 |
| `scene_review_pending` | Stage 3 在跑 | /generating 转圈 |
| `scene_review` | scenes_ready + 未确认（R4-2）| 跳 /scenes，展示场景列表 |
| `storyboard_running` | Stage 4 跑分镜 | /generating 转圈 |
| `shot_generating` | Stage 5 + image_prep + bgm | /generating + 显示"后台生成"按钮 |
| `completed` | Pipeline 跑完 | 跳 /preview |

**前端改造建议**:
- `createUrl.ts`: 用 `status.ui_phase` 直接派生 URL（不再用 backend.stage 多步推理）
- `StageC.tsx`: `generationSubPhase` 改为 `ui_phase` 的派生（不依赖 user click），顺解 T15-8
- `StageC.tsx`: ETA 监听 `status.stage` 变化时重置 lastEtaSecondsRef，顺解 T15-7
- `/preview`: 用 `status.failed_shot_count` 直读（重生成功后实时反映），顺解 T15-12 frontend 侧
- hydrate URL: 用 `status.hydrate_hints.endpoint`，把 `{project_id}` 替换为实际 uuid

**关键变化** (重大顺解):

1. **顺解 T15-3**: `GET /chapters/{n}/story` 现在在 `chapter.status="generating_story"` 但 `scenes_json` 已写入时 **直接返 200 + scenes**（不再 404）。`/scenes` 页面 hydrate `/story` endpoint 就能立刻拿到数据 — **不需要再 hydrate `/storyboard`（那个还会 404）**
2. **顺解 T15-9**: Stage 5 单 shot 失败时 backend 立即更新 `failed_shot_count` + `partial_failure=True`（不等 Pipeline finalize），frontend status 中途 polling 就能看到部分失败状态

**给 @pm**:
- 修改了 5 个文件 (chapters.py / schemas/chapter.py / job_manager.py / pipeline_orchestrator.py / 新单测)
- 单测 44/44 PASS + regression 55/55 PASS（test_architecture 7 + test_shot_regenerate_persistence 9 + test_wave6_full_regression 32 + test_d2_eta_parallel 7）
- py_compile PASS
- 请追加 TEAM_CHAT + PENDING 标 T15-3/-9 ✅
- Frontend agent 可以启动（5/13 21:50+）

**给 @tester**:
- 验收 T15-3: pipeline 跑到 R4-2 等待 scenes 确认时 `curl GET /chapters/1/story` 应返 200 + scenes 数据
- 验收 T15-9: 任何 Stage 5 内 shot 失败时 `curl GET /chapters/1/status` 立即看 `failed_shot_count > 0, partial_failure=true`（不等 Pipeline 完成）
- 验收 ui_phase: 跑 test16 全流程，每个阶段 curl status 看 ui_phase 是否符合状态机

**API 契约变更总结**:
- `GET /chapters/{n}/status` response 加 6 字段 (向后兼容 — 老 frontend 不读这 6 字段也能工作)
- `GET /chapters/{n}/story` 在 scenes_ready 阶段返 200 + scenes（之前 404）
- `pipeline.run()` 加 `job_id: Optional[int] = None` 参数（job_manager 已 wiring）

---

## ✅ TASK-WAVE9-P3-BACKEND-STORYBOARD-SCHEMA-FIX [2026-05-13 21:30] — RISK-T15-14 完成

**给 @pm**:
- 修改了 1 文件：`app/services/storyboard_director.py`（prompt 强化 + post-process，不改 pipeline_orchestrator 或 chapters.py）
- 新建单测：`tests/test_storyboard_director_schema_fix.py` 13/13 PASS
- py_compile PASS
- 请追加 TEAM_CHAT 通知 + PENDING 标 ✅

**给 @tester**:
- 下次 test16+，可验证 4_storyboard.json 中每个 shot 的 `shot_type` + `camera_angle` + `characters_in_scene` 均非 None/空
- 验收标准：`python3 -c "import json; data=json.load(open('output/{uuid}/4_storyboard.json')); bad=[s for s in data['shots'] if not s.get('shot_type') or s.get('characters_in_scene') is None]; print('BAD shots:', len(bad))"`
- 预期：BAD shots = 0

**技术细节**:
- `_build_scene_prompt` JSON 示例新增 `shot_type`/`camera_angle`/`characters_in_scene` 字段 + 在末尾加 REQUIRED FIELDS 说明块（7 个必填字段）
- `_build_prompt`（全剧本模式）同步在 JSON 示例加三个字段
- `_validate_storyboard` 在 `estimated_duration` fallback 之后、T5 speaker-visibility 之前插入 post-process：缺 `shot_type` → 从 `camera.shot_size` 映射；缺 `camera_angle` → 从 `camera.angle` 映射；缺 `characters_in_scene` → 从 `character_direction.characters_visible` 拷贝

---

## ✅ TASK-WAVE9-P1-PRA-REGENERATE-FIX [2026-05-13 21:00] — RISK-T15-12+T15-13 双修完成

**给 @pm**:
- 修改了 1 文件：`app/api/chapters.py`（仅 regenerate_shot 成功 path，未改 status endpoint 或其他 endpoint，无 Wave 9 主任务冲突）
- 新建单测：`tests/test_shot_regenerate_persistence.py` 9/9 PASS
- py_compile PASS + test_architecture 7/7 PASS
- 可以启动 Phase 3 并行（T15-10 AI-ML + T15-11 Frontend + T15-14 Backend）
- Wave 9 Phase 2 改 chapters.py status endpoint 不会与本 PR 冲突（本 PR 只改 regenerate_shot 函数体）

**给 @frontend**:
- Shot regenerate 成功后，`GET /chapters/1/status` 现在会返回正确的 `failed_shot_count=0, partial_failure=false`（需要重启 backend 后生效）
- `/preview` 页面不再持续显示 "22/23 张生成成功，1 张未生成" — 成功重生后 status 真反映

**给 @tester**:
- 验收 RISK-T15-12: regenerate Shot 22 后 curl `GET /chapters/1/status` 看 failed_shot_count=0 + partial_failure=false
- 验收 RISK-T15-13a: 重生后 `output/{uuid}/5_image_results.json` 中 Shot 22 entry success=true
- 验收 RISK-T15-13b: backend log 中 `[ApiCostLogger] project_id=32`（而不是 None）

**API 变更**:
- Shot regenerate endpoint 不变（同一端点，同一响应格式）
- 新副作用：成功后 DB job 字段更新 + 5_image_results.json 文件更新

---

## ✅ TASK-WAVE7-ROUND2 ETA [2026-05-13] — 3 处调用点修复完成

**给 @tester**:
- `pytest tests/test_d2_eta_parallel.py` 7/7 PASS（新增 3 个 Round 2 dynamic case）
- Round 2 验收标准全绿：18 shots vs 26 shots ETA 不同 + max_concurrent 1 vs 3 ETA 不同
- 下一步验收：重启 backend 后跑 test15，确认 image_generation stage 的 ETA 随 shot 数动态变化

**给 @devops**:
- 修改了 3 文件：`app/api/chapters.py` + `app/services/job_manager.py` + `app/services/pipeline_orchestrator.py`
- 无 alembic migration
- 重启 backend 让改动生效（特别是 job_manager.py 闭包逻辑变更）

**技术细节**:
- `chapters.py` fallback 路径现在从 `chapter.storyboard_json` 解析 actual_shot_count，从 `project.confirmed/raw_outline_json` 解析 unique_location_count，从 `settings.IMAGE_MAX_CONCURRENT` 拿 max_concurrent
- `job_manager.py` progress_callback 闭包新增 3 个 mutable list（`_dyn_shot_count` / `_dyn_location_count` / `_dyn_max_concurrent`），pipeline 传入新参数时更新
- `pipeline_orchestrator.py` 在 Stage 4 完成后的两处 callback 调用时传入 actual_shot_count + unique_location_count + max_concurrent，让闭包 mutable state 在 Stage 5 开始前被更新

---

## ✅ TASK-WAVE7-BACKEND [2026-05-13] — 5 任务全完成

**给 @frontend**:
- Task 1: `GET /api/projects/{uuid}/chapters/1/story` 现在在 Stage 3 完成时（scenes_json 非空）就返 200 + scenes，不再等 Stage 5 full_script。RISK-T14-8 的 frontend watcher 可以在 Stage 3 完成后获取 scenes 展示了。
- Task 5: `POST /api/projects/{uuid}/confirm-outline` response 新增 `inconsistency_warnings: [{type, message, affected_field}]` 字段。如有 warnings，前端 Stage B 应显示 banner。旧 `warnings`（字符串数组）字段保留向后兼容。

**给 @tester**:
- 验收 Task 1：Stage 3 完成后（before Stage 5）curl `GET /chapters/1/story` 应返 200 + scenes 字段
- 验收 Task 4：跑一个 Pipeline，后端 log 确认 LLM 生成 26 shots 不被截断（DEC-028）
- 验收 Task 5：confirm-outline 时检查 response 有 `inconsistency_warnings` 数组
- `pytest tests/test_d2_eta_parallel.py` 4/4 PASS + `pytest tests/test_architecture.py` 7/7 PASS

**给 @devops**:
- 修改了 4 文件：`app/api/chapters.py` + `app/api/projects.py` + `app/services/pipeline_orchestrator.py` + `app/services/storyboard_director.py`
- 无 alembic migration（无 schema 变更）
- 重启 backend 让改动生效

**API 契约变更**:
- `GET /api/projects/{uuid}/chapters/1/story`：Stage 3 完成即可调用（不再需要等 Stage 5）
- `POST /api/projects/{uuid}/confirm-outline` response 新增字段 `inconsistency_warnings: [{type: str, message: str, affected_field: str}]`

---

## ✅ TASK-T13-BACKEND-FIRSTBATCH [2026-05-12 17:30] — 5 任务全完成

**给 @frontend** (B1 批次 2 spawn 后看):
- C1-backend `POST /api/projects/{uuid}/confirm-scenes` 项目级 alias 已就绪（自动转发 chapter_number=1）
- 原 `POST /api/projects/{uuid}/chapters/1/confirm-scenes` 仍兼容
- 推荐 frontend B1 改用 project-level（更对称）

**给 @ai-ml**:
- D2 改了 `app/services/pipeline_orchestrator.py` STAGE_DURATIONS["image_generation"] 420→360
- 你的 D3 改的 `app/services/shot_validator.py` 跟 D2 完全不冲突（不同文件不同 lib）
- 你提议的 P3 `BUG-DATA-CONTRACT-COMPOSITION-AS-PROPS`（pipeline_orchestrator.py:1068 重构）已加 PENDING，本季度做

**给 @tester**:
- 验收：`pytest tests/test_d2_eta_parallel.py -v`（4 断言）
- 端到端 test14 跑前先 PM 重启 backend 让 client_log module + DB pool 生效

**给 @devops**:
- 6 个文件改动 + 新建 `app/api/client_log.py` + `tests/test_d2_eta_parallel.py`（共 8 文件改动）
- 部署时正常 rsync 即可，无 alembic migration（A1 是 SQLAlchemy 配置，不是 schema 变更）
- `logs/client.log` 由 backend 创建（`os.makedirs(exist_ok=True)`）

**API 契约变更**:
- 新 `POST /api/_client_log` (无 auth)：body `{level, ts, args, url, source?, line?, col?, stack?}` → `{"ok": true}`
- 新 `POST /api/projects/{uuid}/confirm-scenes` (有 auth)：alias 转发 chapter_number=1
- `POST /projects/{uuid}/confirm-outline` 内 UX-2 检查：原 `Unterminated string` WARNING 不再触发，改为 silent fallback OK

---

## ✅ B59-hotfix [2026-05-12] — LLM JSON 未闭合 ``` 解析失败

**影响范围**: Stage 1-4 全部 LLM 服务（character_designer / story_outline_generator / screenplay_writer / storyboard_director）
**新增文件**: `app/services/_llm_helpers.py`（通用 helper，未来 LLM 服务可直接 import）
**@tester 注意**: BUG-LLM-JSON-PARSE-MARKDOWN-UNCLOSED 待验（见 PENDING.md）
**@devops 注意**: 需重启 backend 让新 module import 生效

---

## ✅ B58-followup HOTFIX [2026-05-12] — clothing str crash

**@frontend 注意**: Pipeline fail 后前端跳 /preview 是 UI bug。backend 已返 `status="failed"`，前端需处理该状态（显示错误页 / 停留在 /generating 展示错误）。

**@tester 注意**: BUG-CLOTHING-SCHEMA-HAIKU-STR 待验（见 PENDING.md）— 复现：adjust 角色 clothing 为中文字符串 → 确认 → 跑 Pipeline → Stage 3 不应 crash。

---

## ✅ Wave 6 完成 [2026-05-11]

**5 bug 一次性闭环**（详细修复原理见 backend-progress/current.md）：

### 1) API 契约变更 (@frontend / @tester 必读)

**新增 endpoint**:
```
POST /api/projects/{project_id}/chapters/{chapter_number}/confirm-scenes
```

Request body（可选）:
```json
{
  "modified_scenes": [
    { "scene_id": 1, "description": "...", "description_zh": "..." }
  ]
}
```

Response:
```json
{
  "success": true,
  "scenes_confirmed": true,
  "scenes": [...]
}
```

错误码:
- 404: project / chapter 不存在
- 409: scenes_json 尚未生成（Stage 3 未跑完）

行为：
- 不传 `modified_scenes` → 仅设 `project.scenes_confirmed=true`，保留 Stage 3 原 scenes_json
- 传 `modified_scenes` → 用其替换 `chapter.scenes_json`（保留用户编辑），同时 `scenes_confirmed=true`

**Project Detail 新增字段**:
```json
{ "scenes_confirmed": true }
```

frontend 应直接读此真字段做 createUrl 判断（不再 heuristic 推断），逻辑参考 `characters_confirmed`：
- `scenes_confirmed=false` → 跳转 `/scenes`（用户停留场景确认页）
- `scenes_confirmed=true` → 跳转 `/generating`

### 2) Pipeline 新流程（@pm / @tester）

```
Stage 1 大纲 → R4-0 用户确认大纲 (existing /confirm-outline)
Stage 2 角色 → R4-1 用户确认角色 (existing /confirm-characters)
              ↓ Wave 6 加: characters_confirmed=true 后 B52-fix v3 reload in-memory characters
Stage 3 剧本 → R4-2 用户确认场景 (NEW /confirm-scenes) 🆕
              ↓ Wave 6 加: scenes_confirmed=true 后 reload scenes_json (含用户编辑)
Stage 4 分镜 → (no pause)
Stage 5 图像 → (no pause)
Stage 6 BGM  → (no pause)
              ↓ Wave 6 改: aiohttp 异步轮询不再阻塞 /health
完成
```

每个 R4-x wait loop 超时 30 min 自动继续防卡死。

### 3) 给 @ai-ml（B52 防御性 L6 协同）

Wave 6 Backend 修了 L5（主修，pipeline reload），AI-ML 在 Stage 4 LLM prompt 加 HAIR COLOR REQUIREMENT MANDATORY rule（L6）是**互补不是替代**：
- L5 解决 in-memory data stale 问题（核心）
- L6 强制 LLM 每次都写发色，对参考图 attention 稀释问题（Shot 2/5/6/15 漂移）有额外保护

Backend 已确保 L5 reload 真接通：
- 关键 grep: `[Pipeline] B52-fix v3: characters reloaded from DB after R4-1 confirm`
- 关键 grep: `[Pipeline] R4-2 / B58: scenes_json reloaded from DB`

### 4) Mureka 异步改造（@pm / @tester）

`/health` 端点 Stage 6 期间不再超时（Monitor 不再误报 alive_no_health）：
- `_call_mureka` 改 async + `aiohttp.ClientSession` + `asyncio.sleep`
- 保留所有现有功能：LUFS / 静音检测 / meta_version="mixed"/"en" / 重试次数 / FFmpeg 后处理
- BGM 业务功能完全不变

### 5) ETA 永不消失（@frontend）

`GET /api/projects/{project_id}/chapters/{chapter_number}/status` 的 `estimated_remaining_seconds`：
- 旧行为：stage 边界 `null`（前端 ETA 文字消失）
- 新行为：永远有值（最小 5s 兜底，"completed" 返 0），单调递减不跳涨

具体路径：
1. pipeline progress_callback 每次更新真计算 stage-aware ETA + 单调递减 guard → 写 `job.estimated_seconds`
2. status 端点优先用 `job.estimated_seconds`，fallback 才调 `estimate_remaining(stage, 0.5)`
3. `estimate_remaining` 新版 unknown stage 返 5（不抛 KeyError），completed 返 0

### 6) Seedream 网络韧性（@tester）

IncompleteRead 等网络层异常退避策略：
- 旧：2/4/8/16s (共 ~30s 不够)
- 新：2/8/30/60s + ±30% jitter (共 ~100s+ 撑过阿里云抖动窗口)
- 仅改网络层（HTTP 5xx 重试保留 `2 ** attempt + 1`，那种通常瞬时）

### 7) 迁移注意（@pm 部署必读）

**必须运行 Alembic migration 005**:
```
alembic/versions/005_add_scenes_confirmed_to_projects.py
```
- 给 `projects` 表加 `scenes_confirmed BOOLEAN NOT NULL DEFAULT FALSE`
- Backfill：已跑完 Stage 4 的老 project（chapters.storyboard_json 非空，LENGTH > 100）→ `scenes_confirmed=TRUE`（防卡住）
- **未运行迁移前**：调用 confirm-scenes 端点会报 SQLAlchemy Column 错误
- **VPS 部署前必须先执行**（按 feedback_shared_db_only.md 走阿里云共享 MySQL）

**重启需求**:
- Backend 必须 kill+restart 让 Python 模块缓存清空
- meta-prompt 文件常量启动时加载

---

## ✅ Wave 5 完成 [2026-05-11]（历史欠账补完）

**5 个 backend 修复点**（详 current.md "Wave 5 完成"段）：

| Bug | 文件 | 给 @frontend / @tester 的影响 |
|-----|------|------------------------|
| B52+B56 /adjust Haiku → physical 同步 | app/api/projects.py L956-982 | Founder 改"红发"现在 chapter.physical.hair_color 真的改 |
| B57 adjust + regenerate-portrait 后自动重生 fullbody | app/api/projects.py L1092-1126/L1249-1298 | fullbody 参考图与 portrait 同步 |
| B52 cascade confirm-outline | app/api/projects.py L571-600 | confirmed_outline.description → chapter.characters_json |
| B49 characters_confirmed 暴露 | app/api/projects.py L204 + app/schemas/project.py L99 | `GET /projects/{uuid}` response 加字段 |
| B56 Stage 2 LLM description 字段 | app/services/character_designer.py L213 | Stage 2 输出含 description |
| B52 Stage 4 physical_summary 优先 description | app/services/storyboard_director.py L1194-1199 | Stage 4 prompt 优先用 description |
| B51 v2 Scene 3 次重试 + fallback shot | app/services/storyboard_director.py L549-671 | Scene 失败不再卡死 pipeline |

**Wave 5 与 Wave 6 关系**: Wave 5 修了"数据写对路径"但漏修"in-memory cache 不 reload"。Wave 6 B52-fix v3 (L5) 真正闭环。

---

## ✅ B33 + B34 完成 [2026-05-09]

**@pm / @frontend 关键变更**:

### B33 — user_selected_mood 移到 Stage A（项目创建时）

**API 契约变更 (Frontend 需要)**:

`POST /api/projects/` body 新增可选字段:
```json
{
  "user_selected_mood": "温馨"  // 可选，8 个值之一
}
```
合法值: `"温馨" | "紧张" | "幽默" | "感人" | "治愈" | "热血" | "悬疑" | "浪漫"`

`GET /api/projects/{id}` response 新增字段:
```json
{
  "user_selected_mood": "温馨"  // null 或 8 值之一，来自 DB projects 表
}
```

**优先级链（BGM / 音乐生成）**:
`project.user_selected_mood (最高)` > `confirmed_outline.user_selected_mood` > `outline.visual_tone.overall_mood`

**Stage 1 LLM 约束**:
若 user_selected_mood 有值，`story_outline_generator` 会注入 MANDATORY 约束块，强制 LLM 把 `mood` 字段和 `visual_tone.overall_mood` 设置为对应值。

### B34 — LLM 调用移出 DB 事务

`generate_outline` 端点修复：

- 旧行为：`Depends(get_db)` session 在 MySQL autobegin 后持锁，LLM 调用 30-60s 期间 row-level lock 不释放
- 新行为：从 project 提取所有需要数据 → `await db.commit()` 释放锁 → LLM 调用（无锁） → 新短事务写 raw_outline_json

**对 @frontend 的影响**: `POST /api/projects/{uuid}/generate-outline` 响应时间不变，但不再阻塞其他对同一 project 的并发请求（B28 症状消除）。

### 迁移注意事项 (PM/DevOps)

**必须运行 Alembic migration 003**:
```
alembic/versions/003_add_user_selected_mood_to_projects.py
```
- 给 `projects` 表加 `user_selected_mood VARCHAR(32) DEFAULT NULL`
- **未运行迁移前，传 user_selected_mood 的 create_project 请求会报 SQLAlchemy Column 错误**
- VPS 部署前必须先执行

---

## ✅ B31+B32+任务3 完成 [2026-05-09]

**@pm / @ai-ml 关键变更**:

### B31 — process_bgm 不再裁到 target_duration

- `app/services/ffmpeg_post_processor.py` process_bgm 签名改 `target_duration_sec: Optional[float] = None`
- 新行为：只切末尾 4s Mureka 水印，不再裁到 target（180s / 90s / 60s）
- 保护：input < 8s 时跳过水印切除
- 返回 dict 新增 `input_duration_sec` / `watermark_trimmed_sec` 两个字段
- test8 类故事 input≈188s → output≈184s（而不是旧的 180s）

### B32 — BGM Haiku prompt 持久化

- `app/services/music_generation_service.py` Step 5 调 Haiku 后，写 `output_dir/bgm_prompt_chapter{N}.txt`
- 同时 INFO log 打印完整 prompt 文本（便于无文件时也能从 uvicorn log 复原）
- 文件格式含 meta header（meta_version / 时间戳 / mood / title）
- **需要 @pm kill+restart backend** 让新代码生效

---

## ✅ P0+P1 批次 6 任务完成 [2026-05-08]

**@frontend 关键变更**:

### B16 — regenerate_shot 现在真实生图
- `POST /api/projects/{uuid}/chapters/{n}/shots/{shot_id}/regenerate` 已实现完整生图逻辑
- 返回含 `?v={timestamp}` 缓存破坏的新 `imageUrl`
- 前端可直接用新 URL 刷新图片，无需额外处理

### B6 — GET /story 错误码修正
- `pending` / `generating_story` 状态现在返回 **404**（不再是 400）
- `full_script=None` 返回 **404**
- `failed` 状态仍返回 **400**（语义正确：是错误，不是"未就绪"）
- **@frontend**: 轮询逻辑应处理 404 为"继续等待"，400 为"显示错误"

**@pm / @ai-ml 关键变更**:

### B8 — Stage 3 单场景 JSON 解析失败已修复
- `_extract_json()` 现在也有 R4-4 内部引号修复（与 batch 版本对等）
- narration 中「」约束加入 prompt（防止未来 Claude 用 "" 破坏 JSON）

### B18 — plot_point 字段完整性保障
- 即使 LLM 偶尔省略最后一个 plot_point 的 `beat`/`estimated_duration_seconds`，`_validate_outline` 会自动 fallback 并 warning
- Stage 1 prompt 已加强 MANDATORY 字段完整性要求

### B19 — overall_mood 标准化
- `visual_tone.overall_mood` 现在只有 8 个合法值：`warm / heartwarming / tense / comedic / melancholic / heroic / mysterious / romantic`
- 非法值自动映射到最接近值（with warning log）

### B20 — Stage 3 sound_design_hint 情绪一致性
- `_build_single_scene_prompt` 现在注入 MOOD COHERENCE 约束块
- 喜剧故事不会再出现"所有声音被吸走"之类的重型音效描述

---

## ✅ P0 — generate_outline 幂等 + raw_outline 暴露 [2026-04-28]

**@frontend / @pm 关键结论**:

### 修复 1: generate_outline 幂等

`POST /api/projects/{uuid}/generate-outline` 现在幂等：
- 如果 `raw_outline_json` 已存，**直接返回缓存数据，不调 LLM**（节省 ¥0.3-0.5 + 30-60s）
- 如需强制重生，传 `?force_regenerate=true`
- Log 会输出 `[GenerateOutline] 幂等: project {id} 已有 raw_outline，直接返已存数据`

**@frontend 行动**: 可以从 generate-outline 调用改为直接读 `project.raw_outline`（见下）

### 修复 2: GET /api/projects/{uuid} 新增 raw_outline 字段

`ProjectDetail` schema 新增字段:
```json
{
  "raw_outline": {
    "title": "...",
    "summary": "...",
    "characters_overview": [...],
    "plot_points": [...],
    "ending_options": [...],
    "unique_locations": [...],
    "mood": "..."
  }
}
```
- 有值 = Stage 1 已完成，pre-confirm 状态
- null = Stage 1 未跑（新项目）
- `confirmed_outline` 优先（用户已 confirm）；`raw_outline` 兜底（Stage 1 完成但未 confirm）

**@frontend hydrate 逻辑**:
```
project.confirmed_outline → StageB 数据（已 confirm）
project.raw_outline → StageB 数据（pre-confirm，Stage 1 已完成）
两者都 null → 等 Stage 1 完成（调 generate-outline）
```

**修改文件**:
- `app/schemas/project.py` L82 — `raw_outline` 字段
- `app/api/projects.py` L98-151 — `_map_outline_to_response()` helper
- `app/api/projects.py` L163-176 — serialize_project_detail 加 raw_outline 解析
- `app/api/projects.py` L377-451 — generate_outline 幂等逻辑

**pytest**: 292 passed, 1 pre-existing failed (UnifiedPromptBuilder._filter_characters_for_shot — 与本次改动无关), 6 errors (API key 缺失的集成测试)

---

## ✅ R7-3 P1 — portrait 重生静默失效 bug 修复 [2026-04-28 21:42]

**@tester / @pm 关键结论**:

R7-3 已修复。adjust_character API 现在会正确重生成 portrait，不再静默失败。

**真因**: `app/services/character_prompt_builder.py` `_build_human_description()` 和 `build_face_description()` 对 `physical`/`clothing`/`human` 字段调 `.get()`，但 T7 项目这些字段是 str（不是 dict），触发 `'str' object has no attribute 'get'`，被 try/except 吞掉变成静默失败。

**修复文件**: `app/services/character_prompt_builder.py`（仅此 1 文件，非高风险文件）

**修复摘要**:
- `_build_human_description()` L100-112: 防御性 isinstance 检查，str 类型字段直接追加文本内容
- `build_face_description()` L217: 同样防御性处理

**验证**:
- pytest 24/24 ✅ + backend 实测 adjust API 无异常
- backend log: `[AdjustCharacter] R7-3: char_001 肖像已重生成` ✅
- portrait mtime 调用前后变化 ✅
- DB `characters_json[0].portrait_url` + `updated_at` 已更新 ✅

**对各 Agent 影响**:
- **@tester**: T7 复测时 adjust API 应正常重生 portrait，portrait 文件 mtime 会变化，characters_json portrait_url + updated_at 会更新
- **@pm**: PENDING.md R7-3 可标 ✅，可通知 Tester 复测
- **@devops**: 部署时需包含 character_prompt_builder.py

---

## ✅ TASK-T6-FIXBATCH Wave 2.5 D.15 P0 — aspect_ratio 完整修复 [2026-04-28 17:00]

**@pm / @tester 关键结论**:

D.15 P0 aspect_ratio hardcoded 问题已完整修复。用户选 1:1 朋友圈现在真的生成 2048x2048 图像。

**完整调用链路（已验证）**:
```
frontend POST /api/projects/{uuid}/start-generation
→ projects.py start_generation(): project.aspect_ratio or "2:3"
→ _run_generation_in_background(aspect_ratio=project.aspect_ratio or "2:3")
→ run_story_generation_task(aspect_ratio=aspect_ratio)
→ Phase2PipelineOrchestrator.run(aspect_ratio=aspect_ratio)
→ generate_shot_image_phase2_safe(aspect_ratio=aspect_ratio)   ← 不再 hardcoded "2:3"
→ Seedream / NB2 真生图 ← 按用户选择比例生成
```

**变更摘要**（4 文件）:
| 文件 | 改动 |
|------|------|
| `app/services/seedream_generator.py` | `_ASPECT_RATIO_TO_SIZE` 补 `3:4: "1664x2218"` + `4:3: "2218x1664"`（现 7 种比例） |
| `app/services/pipeline_orchestrator.py` | `run()` 加 `aspect_ratio: str = "2:3"` 参数；L852 `generate_shot_image_phase2_safe(aspect_ratio=aspect_ratio)`；ARCH-1 写入块 width/height/aspect_ratio 动态查 |
| `app/services/job_manager.py` | `run_story_generation_task()` 加 `aspect_ratio` 参数；`pipeline.run()` 传值 |
| `app/api/projects.py` | `_run_generation_in_background()` 加 `aspect_ratio` 参数；`start_generation()` 传 `project.aspect_ratio or "2:3"` |

**_ASPECT_RATIO_TO_SIZE 现支持 7 种**:
`2:3 / 3:2 / 1:1 / 3:4 / 4:3 / 9:16 / 16:9`（frontend 需要的 4 种: 2:3 / 3:4 / 1:1 / 16:9 全覆盖）

**验证**: pytest 292/292 passed（非 API 集成测试）+ import check ✅

**对各 Agent 影响**:
- **@tester (T7)**: 验证时选 1:1 → 生成图应为 2048x2048（方形），而不是 2:3 竖版
- **@pm**: PENDING.md D.15 已标 ✅，等 Founder 决定是否进 T7 前部署

---

## ✅ TASK-T6-FIXBATCH Wave 2 Agent D — R7-1 GET /api/projects/ 扩展字段 [2026-04-28 16:00]

**@frontend Agent E 关键契约**:

GET `/api/projects/` 每条 project 新增 4 字段：

| 字段名 | 类型 | 示例 | 来源 |
|--------|------|------|------|
| `cover_image_url` | `string \| null` | `"/static/outputs/{uuid}/images/shot_01.png"` | chapter storyboard shots[0].image_url |
| `shot_count` | `number` | `21` | storyboard shots 数组长度 |
| `mood` | `string \| null` | `"温馨"` | confirmed_outline.user_selected_mood ?? mood ?? null |
| `created_at` | `string` | `"2026-04-28T07:10:00Z"` | ISO 8601 UTC（已带 Z，可直接 new Date()） |
| `updated_at` | `string` | `"2026-04-28T15:38:00Z"` | 同上 |

**mapProject() 改法**:
```typescript
coverImageUrl: toAbsoluteUrl(project.cover_image_url) ?? "/brand/logo-48.png",
shotCount: project.shot_count,
createdAt: project.created_at,  // 已是 ISO Z，直接传给 new Date()
```

**修改文件**:
- `app/schemas/project.py`（ProjectDetail 扩字段）
- `app/api/projects.py`（helper 函数 + serialize + list endpoint）

---

## ✅ TASK-T6-FIXBATCH Wave 2 Agent F — ARCH-1 完成 [2026-04-28 15:50]

**@pm / @tester 关键结论**:

ARCH-1 chapter_scene_images 批量写入已实现。现在 pipeline 完成后，`chapter_scene_images` 表会有真实数据，单 shot 重生成 / GET /images 功能可用。

**变更摘要**:
- `Phase2PipelineOrchestrator.run()` 新增 `chapter_id: Optional[int] = None` 参数（向后兼容，默认 None）
- Stage 5 完成后批量 DELETE + INSERT chapter_scene_images（只写 image_url 非空的成功 shots）
- 失败兜底非阻塞（log warning）
- `job_manager.py` 传入 chapter_id

**对各 Agent 影响**:
- **@tester (T7)**: T7 跑完后，GET `/api/projects/{uuid}/chapters/1/images` 应返回真实 shots 列表（不再空），可在验收清单加此检查点
- **@pm**: pytest 211/211 ✅，禁改文件未碰，可安排部署
- **@frontend**: GET /images 端点行为变化（从返空到返真实数据），但前端目前未直接调此端点（StageD 用 /storyboard 端点），无影响
- **@devops**: 需要部署到 VPS（新代码在 pipeline_orchestrator.py + job_manager.py）

---

## ✅ TASK-T6-FIXBATCH Wave 1.1 Agent A — 完成 [2026-04-28]

**@frontend 关键契约更新**:

1. **`POST /api/projects/{project_id}/characters/{char_id}/regenerate-portrait`** 端点已就绪
   - 返回: `{ success: bool, char_id: str, portrait_url: str, message: str }`
   - Agent B F-2 `handleRegenerate()` 接此端点即可工作

2. **`POST /api/projects/{project_id}/characters/{char_id}/adjust`** 返回新增字段
   - 现在额外返回 `portrait_url: str | null`（成功重生时有值）
   - `character.updated_at` 时间戳会被更新（Stage 5 freshness check 依赖此字段）

3. **新 stage 名 `image_preparation` 已激活**
   - Agent B 已在 STAGE_LABEL 加 `image_preparation: "正在准备画面"` — 现在会收到该 stage
   - Stage 4 完成后立即 callback `image_preparation/65/分镜创建完成，正在准备画面...`

4. **Stage 流程进度里程碑（新版）**:
   | progress | stage | 含义 |
   |---------|-------|------|
   | 2 | character_design / story_generation | 启动 |
   | 5 | character_design | Stage 1 完成，进角色设计 |
   | 6 | character_design | LLM角色设计完成，开始生成画像 |
   | 10 | character_ready | 所有 portrait 已生成，等用户确认 |
   | 35 | storyboard | Stage 3 完成，进分镜 |
   | 65 | image_preparation | Stage 4 完成，进 Stage 5 prep |
   | 75 | image_generation | Stage 5 真生图开始 |
   | 65-95 | image_generation | 每张图完成后 +delta |
   | 92 | bgm | BGM 生成（单调 guard 防倒退） |
   | 100 | completed | 全部完成 |

5. **`GET /api/projects/{id}/chapters/{n}/status` ETA 字段已接通**（修复 round 1）
   - `estimated_remaining_seconds` 现在是 stage-aware 实时估算（调 `estimate_remaining(current_stage, 0.5)`）
   - 例：`image_generation` 阶段返回约 ≥300s，不再是旧 `estimated_seconds - elapsed`（1 分钟低估）

**@pm**: P1-3 P1-5 P0-2 P1-1 P1-2 + 修复 round 1 全部完成，禁改文件未碰，可安排审查+部署。

---

## ✅ TASK-T5-FIXBATCH-R6 子任务 1 — GET /api/projects/{id} 扩展字段 [2026-04-27 17:30]

**@frontend 关键契约更新**:

GET `/api/projects/{project_id}` 现在额外返回:
- `confirmed_outline: dict | null` — 用户在 Stage B 确认后的完整大纲 JSON，包含:
  - `summary`: 200+ 字故事大纲（修 Stage E bug D）
  - `mood`: LLM 生成的情绪基调
  - `user_selected_mood`: 用户在 Stage B 选择的情绪（修 Stage E bug E）
  - `music_hint`: BGM 提示
  - `plot_points`: 情节节拍列表
  - `title` / `title_en` / `characters_overview` 等完整 Stage 1 输出字段
- `aspect_ratio: str | null` — 项目创建时选择的画面比例，如 "2:3"

**@pm**: 修改极小（2 文件，20 行），无副作用。list 端点（GET /api/projects/）也自动带这两个字段（同用一个 serializer），属于预期行为。

**修改文件**:
- `app/schemas/project.py` — 加 `Any` import + 2 个 Optional 字段
- `app/api/projects.py` — serialize_project_detail 加 json.loads + JSONDecodeError 兜底

---

---

## ✅ TASK-PARALLEL-M1 Round 4 — Bug 1 + Bug 5 完成 [2026-04-27 11:35]

**@pm / @tester / @devops 关键结论**:

PARALLEL-M1 最后两个 bug 已修复并实证验证。部署可推进（待 Founder 决策）。

**Bug 1 — project_id=None ✅ 彻底解决**:
- `image_generator.py` dispatcher `**_kwargs_copy` 透传 1 行修复
- 实证: 16 shots api_cost_logs 全部 project_id=12 (integer)，ARCH-4 DB cost log 真实生效

**Bug 5 — ShotValidator 5MB 图压缩 ✅**:
- `shot_validator.py` 新增 `_compress_for_claude()` 压缩函数
- 超 4.5MB 自动 JPEG 压缩（quality 85/75/65/55 → 分辨率降级），不再 fail-open

**PARALLEL-M1 全 bug 状态**:
| Bug | 最终状态 |
|-----|---------|
| 1 project_id=None | ✅ 彻底修（round 4 实证 16/16 integer）|
| 2 ShotValidator 鉴权 | ✅ 修（round 3）|
| 3 IncompleteRead | ✅ retry 3 有效（round 3）|
| 4 Event loop closed | ✅ ensure_future→await（round 3）|
| 5 ShotValidator 5MB | ✅ 图压缩（round 4）|

**对各 Agent 影响**:
- @tester: 可用 run_perf_test.py driver sanity 复测（后端已重启 pid 86603 带新代码）
- @devops: 部署条件满足（待 Founder 本地+域名测后决定）
- @ai-ml: 无影响（prompt 逻辑不变）
- @frontend: 无影响（API 契约不变）

---

## ✅ TASK-SHOT08-DIAGNOSIS — Shot 8 根因确认 [2026-04-25 13:48]

**@pm / @tester / @ai-ml 关键结论**:

Shot 8 Seedream 卡死根因为 **A（累积态资源耗尽）**，非代码 bug，生产环境不受影响。

| 指标 | 数值 |
|------|------|
| outcome | success（单独跑成功）|
| root_cause | A |
| mem_peak_mb | 290.45 MB |
| payload_bytes | 9.88 MB（6 refs）|
| total_elapsed_sec | 81.6 s |
| api_call 耗时 | 78.6 s |

**对其他 Agent 的影响**:

- **@pm**: 生产代码无需修改。如需修复测试脚本批量跑卡死，建议派一个微任务：在 shot 生成循环第 7/8 之间加 `await asyncio.sleep(1)` 或 `gc.collect()`（5 行改动，低优先级）
- **@tester**: 回归测试脚本卡死的根因已确认，批量测试时注意内存积累。生产 FastAPI 路径（每请求独立调用栈）天然隔离此问题
- **@ai-ml**: 无影响
- **@devops**: 无需部署变更

**产物路径**: `test_output/manualtest/shot8_diagnosis_2026-04-25/`
- `diagnose.log` — 完整诊断日志（含每步 timing）
- `result.json` — 结构化结果（JSON）
- `shot_08.png` — 生成图片（1664x2496, 3218KB）✅

---

## ✅ TASK-SEEDREAM-INTEGRATION — Seedream 5.0-lite 接入完成 [2026-04-24 22:10]

**对其他 Agent 的影响**

**@pm**:
- 🔴 image_generator.py 只改 7 行（dispatcher），NB2 原逻辑零变化，请审查 `git diff app/services/image_generator.py` 确认
- 🟡 **架构澄清**: dispatcher 挂在 `generate_shot_image()` 入口（按任务文案要求），但生产 Pipeline 走的是 `generate_shot_image_phase2_safe()`。**当前状态下 `IMAGE_GEN_PROVIDER=seedream` 在生产 Pipeline 不会触发 Seedream 分支。** 详见 backend-progress/current.md 的"重要架构澄清"段。等 PM 审查后决定是否派新任务补 dispatcher 到 `_phase2_safe`（估 +8 行）
- Sanitize 关键词表 27 条（3 级 attempt），可读
- 本次未跑真实角色一致性回归（按任务说明 @tester 负责）

**@tester**（下一步）:
- 跑角色一致性回归测试验证 Seedream 接入
- 故意触发 sanitize 场景（POC shot_04 prompt "elderly + worry" 组合）验证 NB2 fallback 路径能走通
- 测试需要 `.env` 里有效 `ARK_API_KEY`（Founder 已配）+ `IMAGE_GEN_PROVIDER=seedream`
- ⚠️ 注意: 当前 dispatcher 只挂在 `generate_shot_image()`，测试 Pipeline 端到端时不会触发 Seedream；需直接测试 `generate_shot_image()` 或等 PM 派发 dispatcher 扩展任务后再测 E2E
- **fallback 验证法**: 用假 `ARK_API_KEY=""` 模拟 API 失败 → 应自动降级 NB2 并返回图；或故意传入含敏感词 prompt 模拟 3 次 sanitize 耗尽

**@ai-ml**:
- 本次没碰 `style_enforcer.py`（按约束）
- Seedream 的 prompt 输入链路：POC 脚本把 `image_prompt` + `text_overlay instruction` 拼接发 API。生产 dispatcher 把 `generate_shot_image()` 的入参（shot + reference_images + aspect_ratio）完整传给 `generate_shot_image_seedream()`，函数内部复用 shot 的 text_overlay 字段构建文字指令
- 若你计划为 Seedream 加 "2D 水彩条漫风" 硬约束，可直接改 `style_enforcer.py`（影响 prompt 头部的 MANDATORY STYLE 块），Seedream 路径会收到该 prompt — 但注意目前 Seedream 路径用的是 `shot["image_prompt"]` 原文，**并没有走** StyleEnforcer.enforce_prompt() 二次包装（走的是 Phase 1 legacy 路径的简化 prompt）。如果需要 Seedream 收到 B' / StyleEnforcer 包装后的 prompt，需要在 dispatcher 扩展到 `_phase2_safe` 时同步传入 full_prompt 参数（函数已预留 `full_prompt` 参数位）

**@devops**（Phase 3）:
- 本地 `.env` 加 `IMAGE_GEN_PROVIDER=seedream`（测试期）
- VPS `.env.production` 同步加
- `ARK_API_KEY` 已存在（Founder POC 阶段加的）
- 注意: 鉴于上述架构澄清，即使 VPS 切到 `IMAGE_GEN_PROVIDER=seedream`，现阶段生产 Pipeline 不会走 Seedream 分支。等 PM 决策后再做部署

**Seedream 接入的 API 技术细节**（给需要调用的 Agent 参考）:
- Endpoint: `POST https://ark.cn-beijing.volces.com/api/v3/images/generations`
- Model ID: `doubao-seedream-5-0-260128`（5.0-lite，已开通）
- Auth: `Authorization: Bearer $ARK_API_KEY`
- Size: `"1664x2496"`（2:3 2K）/ `"2048x2048"` (1:1) etc.
- 参考图: `image` 字段传 base64 data URI（`data:image/png;base64,...`），string 或 string[]，最多 14 张
- 响应: `response_format: "b64_json"` 返回 `data[0].b64_json`
- Payload > 10MB 自动降采样参考图到 1024px；413/400 too large 降到 512px
- 429/5xx 指数退避重试 2 次
- 内容审查拦截标志: `InputTextSensitiveContentDetected` / `sensitive_content` / `content_policy` / `risk_control`

**Seedream 接入代码位置**
- 核心模块: `app/services/seedream_generator.py`（新建）
- 配置: `app/config.py` 新增 2 字段 `IMAGE_GEN_PROVIDER` / `ARK_API_KEY`
- `.env.example` 新增对应示例
- Dispatcher: `image_generator.py:795-801`（`generate_shot_image()` docstring 后 7 行）

---

## ✅ TASK-SEEDREAM-POC Phase 3a — comparison.html 已更新 [2026-04-24 18:20]

**@tester**: `comparison.html` 已加 shot_04 视觉警告，评分时注意：
- shot_04 有 ⚠️ 红色 badge + 双 prompt 对照（原 prompt vs sanitized prompt），黄色高亮显示 2 处具体差异词
- **shot_04 不计入 9 shots 公平对比均分**（评分说明在页面底部橙色框）
- shot_04 的 Seedream 图本身质量仍可按 0-5 打分，但单独标注"prompt adjusted"
- 其他 9 shots 展示不变，可正常对比评分

**产物路径**: `test_output/manualtest/seedream_vs_nb2_2026-04-24/comparison.html`

---

## 🔴 TASK-SEEDREAM-POC — Step A-D 完成，新 blocker: 账号未开通模型 [2026-04-24 17:05]（已解决）

**当前状态**: Founder 已在 `.env` 放入 `ARK_API_KEY=ark-058f...f3263`，鉴权通过（**不再是 401**），但账号 `2105093537` **尚未开通 `doubao-seedream-4-0-250828` 模型服务**，10/10 shots 返回 HTTP 404 `ModelNotOpen`。

**对其他 Agent 的影响**:
- **@pm / Founder**: 需到 https://console.volcengine.com/ark/ 「模型广场」搜 `doubao-seedream-4-0` → 点「开通」，等 ~1 分钟后重跑 `python3 scripts/test_seedream_vs_nb2.py`
- **@tester**: Phase 3 的人工评分任务需要等模型开通后跑出 10 张 Seedream 图才能启动
- **@ai-ml / @frontend / @devops**: 暂不涉及

**脚本能力（production-grade edge case 处理）**:
- Downsample 大 payload（>10MB → 1024px；413/400 too large → 512px）
- 指数退避（429/5xx → 3s/5s/9s；网络异常 → 2s/4s）
- 软节流（每 shot 间隔 1s）
- Continue-on-error（单 shot 失败不中断整批）

**产物**: `test_output/manualtest/seedream_vs_nb2_2026-04-24/`
- `README.md` 首部有 BLOCKER 章节
- `logs/seedream_api_logs.json` 10 条 404 记录
- `comparison.html` 左列全 FAILED，右列 NB2 完好

**_旧 blocker（Ark Key 未配置）已解决_**:
- **@devops**: 本次不涉及部署
- **@tester**: Phase 3 的人工评分任务需要等 Step 3 跑出 10 张 Seedream 图才能启动
- **@ai-ml**: 本次不涉及 prompt 工程
- **@frontend**: 本次不涉及前端

**Seedream 4.0 API 调研结论（给后续接入生产 Pipeline 参考）**:
- Endpoint: `https://ark.cn-beijing.volces.com/api/v3/images/generations`
- Model: `doubao-seedream-4-0-250828`
- Auth: `Authorization: Bearer $ARK_API_KEY`
- Size: `1664x2496`（2K 2:3，DEC-010 兼容）
- 多角色参考图: `image` 字段传 **字符串数组**（base64 data URI 或 URL），最多 14 张
- 响应: `{data:[{b64_json, size}]}`（b64_json 模式无 URL 过期风险）
- 火山方舟 Ark 与 VolcEngine IAM（TTS 用）是两套独立鉴权体系

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

---

## ✅ TASK-PARALLEL-M1 Phase 1 + round 2 — Stage 5 并行化完成 [2026-04-25 17:30]

**@pm / @tester / @ai-ml / @devops 关键状态**:

Stage 5 从串行改为并行（asyncio.Semaphore(IMAGE_MAX_CONCURRENT=3) + asyncio.gather）已完成并验证。ARCH-4 api_cost_logs INSERT/READ 路径打通。

**对各 Agent 的影响**:

**@tester** (Phase 2 任务):
- 用 Seedream 跑回归（teststory6.4/6.5/6.6 + 跨题材 4 种）— Founder 主观判定（不卡死指标）
- 8 失败分支模拟测试覆盖（PENDING.md 已列）
- 验证 0 cost circuit breaker 真起作用
- 验证 api_cost_logs 表真有 INSERT（ + 真实 NB2/Seedream 跑 ≥1 shot）
- 验证 Stage 5 并行效率（20 张 4.5 min 目标）

**@devops** (Phase 3 任务):
- push GitHub + rsync VPS + /api/health 验证 + 跑 1 次完整 Seedream pipeline

**@ai-ml**:
- Stage 5 并行不影响 prompt 逻辑，无需改动
- ARCH-4 api_cost_logs 记录每张图的模型/成本/stage，可用于 prompt 效果追踪

**技术细节（关键修改文件）**:
-  — Stage 5 并行化 + PipelineCostTracker + db_project_id 查询
-  — 新建，异步 INSERT api_cost_logs
-  — 新建 ORM model
-  — log_api_cost ensure_future + Seedream dispatcher
-  — log_api_cost ensure_future + project_id 透传（round 2）
-  — 17 测试用例，24/24 真实 venv 通过
-  — 已删除（round 2 修复，venv 真实依赖足够）


---

## 🆕 TASK-PARALLEL-M1 Round 3 完成 + Bug 5 + 待 Round 4 (2026-04-27)

**Round 3 (04-25 16:30) 修复**:
- pipeline_orchestrator.py: project_uuid=None 时创建 temp Project DB record（user_id=0 sentinel）
- shot_validator.py: 显式 `api_key=settings.ANTHROPIC_API_KEY` 给 AsyncAnthropic
- seedream_generator.py: SEEDREAM_HTTP_RETRIES 2→3 + retry log 统计
- image_generator.py + seedream_generator.py: `asyncio.ensure_future(log_api_cost)` → `await log_api_cost(...)`

**对其他 agent 的影响**:
- @ai-ml: 无（生图 prompt 不变）
- @frontend: 无（API 契约不变）
- @tester: D1 redo 14/14 全过，但 Bug 1 残留 + Bug 5 新发现，等 round 4 修完再 sanity 复测
- @devops: 部署暂缓（Founder 本地+域名测后决定）

**待 Round 4 修**:
- Bug 1 残留: image_generator.py L1392-1398 dispatcher 调 generate_shot_image_seedream 没传 **_kwargs_copy → project_id 仍 None（**1 行修**）
- Bug 5: ShotValidator 调 Anthropic Claude 时图片超 5MB 上限触发 fail-open，需要图压缩到 < 5MB 后传

**ARCH-4 状态**: INSERT 路径打通，DB cost log 真写入；READ 路径在 round 4 修 Bug 1 后才完整生效



---

## 🆕 TASK-T5-FIXBATCH 完成 (2026-04-27 PM 代更)

**8 条后端修复完成**, 211/211 tests 通过, T5 hot-fix 已跑.

**对其他 agent**:
- **@frontend**: backend.characters_json 加了 `portrait_url` 字段（Stage 2 后），Stage C 卡片可读这字段渲染真 portrait. backend Stage 6 完成会发 progress_callback("completed", 100, "故事生成完成"), 前端 redirect 三合一触发能用.
- **@ai-ml**: Backend 已接入 `style_music_hints.get_raw_hint()`，Stage 1 outline 有 music_hint 字段了
- **@tester**: T6 测试时验证: shot image_url + chapter.bgm_url + outline.music_hint + chapter.characters_json.portrait_url + outline.user_selected_mood 都正确填充
- **@devops**: 后端代码改动需要重启 backend 才生效（PM 在做）

**T5 项目状态**: 已 hot-fix 补 image_url + bgm_url，Founder 刷新 Stage D 即可看图听 BGM

---

## 2026-04-30 11:00 给同事（PM 代更）

Wave 5.1 移除了 image_generator.py L796/L1389 的 fallback_callback 调用。**整个 pipeline 现在是单一生图模型**（NB2 全程 NB2 / Seedream 全程 Seedream）。如果你接入新生图 provider，禁止加 fallback 切换其他 provider — 详见 `feedback_pipeline_single_model_only.md` 永久 memory。

---

## 2026-05-09 17:00-17:30 — B35-B41 影响 (PM 代写)

**对所有 agent**:
- backend AsyncAnthropic 真生效 — Stage 2/3/4 LLM 期间不再阻塞 uvicorn event loop
- IMAGE_GEN_PROVIDER=seedream 真生效 (config.py default + .env.example) — portrait/anchor/shot 全栈 Seedream，2048×2048 (1:1)
- aspect_ratio 真按用户 Stage A 选项透传到所有生图层 (B39)
- 后端日志补全 (storyboard Scene 失败 logger.exception + main.py global exception_handler + auth/database/character_consistency 加 logger)

**新 PID + 服务**:
- backend PID 69134 (17:08, B35-B41 全闭环)
- alembic head 不变: `003_add_user_selected_mood`

**对 @frontend**:
- API 契约不变
- backend 不再阻塞 — frontend timeout=120s 是冗余保险，单用户场景实测应秒回

---

## 2026-05-11 10:43 — B43-B46 + B41 给其他 agent 的影响（PM 代写）

**对 @frontend**: API 契约变更
- GET /chapters/{n}/status 新增 `failed_shot_count: int`/`partial_failure: bool`
- GET /chapters/{n}/storyboard shots[*] 新增 `safety_advice/success/error/error_kind`
- frontend 用 failed_shot_count > 0 检测部分失败（B46 配合）
- frontend 显示 safety_advice.user_message + suspected_terms + suggested_changes（B44 配合）

**对 @ai-ml**: 
- B43 修复同 B35 模式（AsyncAnthropic + await）
- Stage 6 BGM 期间 backend /health 不再阻塞 70s

---

## 2026-05-15 — Wave 14 Backend #1: RISK-T19-8 B51 fallback 中文化（给其他 agent）

**当前状态**: ✅ Wave 14 Backend #1 完成

**改动文件**:
- `app/services/storyboard_director.py` — 新增 `_extract_english_from_field()` helper + `_build_scene_prompt()` 英文化修复

**新单测**: `tests/test_b51_fallback_no_chinese.py` (20 cases PASS)

**对 @ai-ml (RISK-T19-6)**:
- RISK-T19-8 修复了 `_build_scene_prompt()` 中的 `characters_json` characters name 和 clothing_summary
- 当 AI-ML 完成 anthropomorphic_animal 映射后，character_prompt_builder.py 可能输出新的英文 clothing/description 格式
- 如果新格式里 clothing 字段改用英文结构化字段（top/bottom/style 等），`_extract_english_from_field()` 会自动透过（纯英文原样通过）
- 如果 description 格式改变（比如不再双语），`_extract_english_from_field()` 也能处理（纯英文通过，双语提取英文部分）
- 无需 Backend 二次适配，但请 PM 验证新 character 数据格式是否如预期

**对 @PM**: 
- Wave 14 Backend #1 完成，代替写 TEAM_CHAT 和 PENDING 更新
- 等并行的 Backend #2/3 和 AI-ML 完成后，建议 PM 统一跑 test20 e2e 验证所有 Wave 14 修复

**对 @tester**:
- test11+ 真跑应验证: Stage 6 BGM 期间 backend health 200 即时 + frontend dashboard 显示 failed_shot_count（如有 shot 失败）

---

## 2026-05-11 17:18 Wave 5（PM 代写）

**对 @frontend (B49 配合)**:
- `GET /projects/{uuid}` response 真返 `characters_confirmed: bool` 字段
- frontend hydrate 优先读此字段（避免依赖 stale job.stage 推断）

**对 @tester**:
- B51 v2 fallback shot 含 `_is_fallback: True` 标记，可用作回归测试 detection
- test12 验证: 改红发后 shot 应全红发（B52 cascade 修对了）

**对 @ai-ml**:
- B56 Stage 2 LLM 现强制输出 description 字段
- Stage 4 优先读 description — 跟 B47 Stage 1 改 mood 字段方向一致（字段优先级链）


---

## 2026-05-19 21:20 T20-23 修复 (RISK-T20-23)

**@tester**: `character_designer.py` 的 `_validate_characters()` 已修复，animal/robot 等非 human 类型不再抛 ValueError。test19 (独眼鸦 + 2 human) 的 Stage 2 应该通过。可在 backend 重启后跑 e2e test19 验证。

**@pm/@ai-ml**: 未动 pipeline_schemas.py，T20-10/T20-22 不退化。只改 character_designer.py L304-330。
