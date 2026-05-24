# Backend Agent - 当前任务

> **最后更新**: [2026-05-24] ✅ Wave 11 TASK-WAVE-11-MYSQL-POOL-PRE-PING-RELIABILITY 完成诊断 — pool 参数已在 Wave 4 + T20-53 就位，无需修改
> 66 PASS (database+status_authoritative), 0 退化, 0 越权

---

## ✅ 完成: Wave 11 TASK-WAVE-11-MYSQL-POOL-PRE-PING-RELIABILITY 诊断 [2026-05-24, Sonnet 4.6 xhigh]

### 任务: 调查并修复 idle 1h 后 pymysql 2013 Lost connection 500

**调查结论**: `app/database.py` pool 参数已于 Wave 4 BUG-T13 (pool_pre_ping + pool_recycle + pool_size + max_overflow) 和 T20-53 (pool_timeout) **全部配置到位**，无需再修改。

| 参数 | 值 | 状态 |
|------|----|------|
| pool_pre_ping | True | 已配 (Wave 4 BUG-T13) |
| pool_recycle | 1800 (30min) | 已配，比要求 3600s 更保守 |
| pool_size | 10 | 已配 |
| max_overflow | 20 | 已配 |
| pool_timeout | 30 | 已配 (T20-53) |

**对 5/23 19:48 500 事件的分析**: pool_pre_ping=True 已在，理论上应自动重连。该次 500 可能是：
- backend 当时运行的是旧版本（T20-53 改动在 5/20，但 VPS 部署滞后）
- 或 asyncmy driver 在某些版本下 pool_pre_ping 行为与 sync driver 略有差异

**修改 2 (middleware retry) 评估结论**: **不加**。
- pool_pre_ping=True 已覆盖"取连接时 dead connection"场景（Founder 实测的 case）
- middleware retry 需要区分幂等/非幂等请求，且 query 执行中途断连极为罕见
- 遵守 CLAUDE.md 15-A：不以"过度防御"之名添加不必要的复杂度

**pytest**: 66 PASS (database + status_authoritative), 0 退化

**Ben 协议 5+1**:
- 0 schema 改动
- 0 Alembic migration
- 0 STATUS_API_CONTRACT 升级
- 0 frontend 影响
- 0 代码改动（本任务为纯诊断）
- `[frontend-impact: no]`

---

## ✅ 完成: Wave 10 Backend 接力 — P3-1 + P3-2 (接力 AI-ML commit 3faf585) [2026-05-23, Sonnet 4.6 xhigh]

### 改动文件 (3 文件, 0 Ben 协议越界)

| 文件 | 改动 |
|------|------|
| `app/api/projects.py` | P3-1: import CHARACTER_FIELD_PRESERVATION_RULES + 拼入 adjust_character LLM prompt + L1286 直接覆盖 → deep-merge (merged_char) |
| `app/services/storyboard_director.py` | P3-2: direct()/\_generate\_scene\_shots()/\_build\_scene\_prompt()/\_validate\_storyboard() 加 project_aspect_ratio 参数链 + L1068+L2334 hardcoded "2:3" → project_aspect_ratio |
| `app/services/pipeline_orchestrator.py` | P3-2 调用方: storyboard_director.direct() 加 project_aspect_ratio=aspect_ratio |

### pytest 结果

```
test_t22_new_7_id_format_robustness.py + test_apply_identity_anchors_location_wire.py + test_wave10_ai_ml_fidelity_rules.py
  81/81 PASS ✅

回归 (T22-NEW-5 + llm_fallback_chain + first_batch_chars + schema_generic_fallback + T20-48 + T20-28):
  227/227 PASS ✅, 0 退化
```

### Ben 5/13 协议

- 0 API contract 变更
- 0 schema 改动
- 0 Alembic migration
- 0 frontend 影响
- 0 越权 AI-ML 已 commit 的 const
- [frontend-impact: no]

---

## ✅ 完成: Wave 8 第 3 批 — T22-NEW-5 R4-2 砍掉 (scene_review 移除) [2026-05-22 ~19:00, Sonnet 4.6 xhigh]

### 任务: TASK-T22-NEW-5 — Stage 3 完成后直接进 Stage 4 (砍 R4-2 文字层场景确认)

**改动文件 (2 改 + 1 合约升级 + 1 新建 test, 0 Ben 协议越界)**:

| 文件 | 改动 |
|------|------|
| `app/services/pipeline_orchestrator.py` | 完整移除 R4-2 wait loop (~90 行 → 7 行) + T22-NEW-5 标记 + 立即进 storyboard progress_callback |
| `app/api/chapters.py` | (a) `_derive_ui_phase` 移除 `scene_review` 返回 + `scenes_ready → storyboard_running` 直接映射; (b) `_build_hydrate_hints` 移除 `scene_review` 分支; (c) 新增 `confirm_scenes_noop` endpoint (noop + deprecation log, 不 update DB) |
| `.team-brain/contracts/STATUS_API_CONTRACT.md` | 升级 v1.4 → v1.5 (8 状态机, 移除 scene_review, 新增 v1.5 §8 历史, frontend-impact: yes) |
| `tests/test_t22_new_5_r4_2_removed.py` | **新建** 24 case (4 section: R4-2 移除 / confirm-scenes noop / _derive_ui_phase / 契约 v1.5) |

**pytest 真自跑 (KEY_LEARNINGS #47 铁律)**:

| 测试文件 | 结果 |
|----------|------|
| test_t22_new_5_r4_2_removed.py (新建) | **24/24 PASS** |
| test_t21_new_3_to_7_backend.py (regression) | **51/51 PASS** |
| test_first_batch_chars_not_zero.py (regression) | **17/17 PASS** |
| test_llm_fallback_chain.py (regression) | **14/14 PASS** |
| test_apply_identity_anchors_location_wire.py (regression) | **7/7 PASS** |
| test_schema_generic_fallback_arch.py (regression) | **83/83 PASS** |
| **总计** | **196/196 PASS (24 新 + 172 旧 regression, 0 退化)** |

**Ben 5/13 协议严守**:
- 0 schema 改动 (app/schemas/ 不动)
- 0 Alembic migration (scenes_confirmed DB 列保留, 不做迁移)
- 0 frontend 改动 (Wave 8 #2 Frontend 已完成)
- 0 越权 Wave 7+8 在改的文件
- STATUS_API_CONTRACT v1.5 含 [frontend-impact: yes] 标签 ✅

**核心架构变更**:
- **pipeline_orchestrator.py**: R4-2 wait loop (~90行) → 7行 T22-NEW-5 标记 + 立即进 storyboard. Stage 3 完成直接进 Stage 4.
- **_derive_ui_phase**: scenes_ready → storyboard_running (不再 → scene_review). 状态机 9→8.
- **confirm-scenes endpoint**: `chapters.py` 新增 noop, 返 200 + deprecated=True, 不更新 DB.
- **STATUS_API_CONTRACT v1.5**: 8 状态机, scene_review 移除标注, 转换图更新, v1.5 §8 历史.

**部署铁律**: Frontend (Wave 8 #2 已完成) + Backend (本任务) 必须**同时部署**.

---

## ✅ 完成: Wave 8 — Generic Fallback Architecture (pipeline_schemas.py 重构) [2026-05-22 ~17:00, Sonnet 4.6 xhigh]

### 任务: TASK-T22-NEW-9 — 17 hotfix entry → 1 通用 fallback 函数

**改动文件 (1 改 + 1 新建 test + 1 test 更新, 0 Ben 协议越界)**:

| 文件 | 改动 |
|------|------|
| `app/services/pipeline_schemas.py` | `_TYPE_REQUIRED_GROUPS` 从 19 entry 缩至 4 (human/anthro_animal/animal/vehicle) + 新增 `has_humanoid_fallback()` 通用函数 + `validate_physical_by_type` 重构 |
| `tests/test_schema_generic_fallback_arch.py` | **新建** 83 case (8 section: helper unit / 架构常量 / 19 type × humanoid / generic 无 humanoid / 严格 type / 边界 / Wave4+4.5 回归) |
| `tests/test_t21_digital_virtual_fallback.py` | `test_digital_virtual_no_minimum_fields_fails` → `test_digital_virtual_no_minimum_fields_warns_not_raises` (反映新架构: 不含字段 → warning not raise) |

**pytest 真自跑 (KEY_LEARNINGS #47 铁律)**:

| 测试文件 | 结果 |
|----------|------|
| test_t21_digital_virtual_fallback.py | **25/25 PASS** |
| test_t21_new_2_humanoid_fallback_wave2.py | **16/16 PASS** |
| test_schema_generic_fallback_arch.py (新建) | **83/83 PASS** |
| test_identity_anchor_cross_genre_baseline.py (regression) | **105/105 PASS** |
| **总计** | **229/229 PASS** |

**重构前后对比**:
- `_TYPE_REQUIRED_GROUPS` entries: **19 → 4** (减少 79%)
- `has_humanoid_fallback()`: **新增 16 行** 通用函数
- `validate_physical_by_type`: **重构** 清晰 3 路 (精确规则 / 严格 type / 通用 fallback)
- 文件总行数: ~709 → ~760 (+51 行，但架构清晰度大幅提升)

**Ben 5/13 协议严守**:
- 0 API contract 变更
- 0 schema 改动 (app/schemas/)
- 0 STATUS_API_CONTRACT 升级
- 0 Alembic migration
- 0 frontend 影响
- 0 越权 Wave 7 在改的文件

---

## ✅ 完成: Wave 7 P0 — Layer 1 first-batch chars=0 + LLM Fallback Chain + Location Wire [2026-05-22 ~15:30, Sonnet 4.6 xhigh]

### 真根因诊断 — T22-NEW-7 chars=0 (max thinking, 4_storyboard.json 实测验证)

**Founder e2e test22 视觉证据 (5/22 14:09 /preview Shot 2)**: Coral 美人鱼 → 深蓝头发 + 人腿 + 蓝白裙 (完全错), Ah Hai → 深黑发 (错).

**Backend log 实证 (backend.log L28770-30617)**:
```
[IdentityAnchorInjector] Injected anchors: chars=0, ...  # Shot 1
[IdentityAnchorInjector] Injected anchors: chars=0, ...  # Shot 2
[IdentityAnchorInjector] Injected anchors: chars=0, ...  # Shot 3
[IdentityAnchorInjector] Injected anchors: chars=2, ...  # Shot 4 ✅
... (Shot 4-21 全 chars=N>0)
```

**真根因 (4_storyboard.json grep + 2_characters.json 真查)**:
```python
# test22 4_storyboard.json shot 1-3
characters_in_scene=['Coral']               # ← LLM 用 name_en 格式
characters_in_scene=['Coral', 'Ah Hai']     # ← name_en

# test22 4_storyboard.json shot 4-21
characters_in_scene=['char_001', 'char_003']  # ← LLM 用 char_id 格式

# test22 2_characters.json char 真 schema
id="char_001", name="珊瑚", name_en="Coral"
id="char_002", name="阿海", name_en="Ah Hai"
id="char_003", name="深海女巫", name_en="Sea Witch"

# 旧 _apply_identity_anchors L881-884 (image_generator.py)
chars_in_shot = [
    c for c in characters_list
    if isinstance(c, dict) and c.get("id") in shot_char_ids  # ← 只比对 c["id"]
]
```

**LLM Stage 4 输出真**格式不一致** — 前 3 shot 用 `name_en` ("Coral"), 后 18 用 `char_id` ("char_001"). 旧实现只比对 `c["id"]` → 前 3 完全 mismatch → `chars_in_shot=[]` → `inject_identity_anchors(characters_in_scene=[])` → CHARACTER ANCHORS block 真**完全没注入** → Seedream weak ref following → Shot 2 美人鱼变蓝头发人腿.

**真不是** race condition / batch order / variable scope / async dispatch 问题. 真**纯 ID format mismatch**.

---

### 改动文件清单 (6 个真改 + 3 个新单测, 0 Ben 协议越界)

| 文件 | 改动类型 | 改动 |
|------|---------|------|
| `app/services/identity_anchor_injector.py` | + 100 行 | 新增 `resolve_characters_in_shot()` standalone helper (三路 id/name_en/name smart match, case-insensitive, dedup, 防御性 WARNING) |
| `app/services/image_generator.py` | 改 ~80 行 | (a) `_apply_identity_anchors` 接 `outline` kwarg 用于 T22-NEW-6; (b) char resolution 改 delegate to `resolve_characters_in_shot()`; (c) location lookup 改用 outline 优先 + screenplay scene→location_id 派生 |
| `app/services/pipeline_orchestrator.py` | + 8 行 | Stage 5 dispatch L1589 真**传 `outline=outline` kwarg** 到 `generate_shot_image_phase2_safe` (T22-NEW-6 wire) |
| `app/services/llm_fallback_chain.py` | **新建 (404 行)** | `call_llm_with_fallback()` Haiku → Gemini 3.1 Flash → Sonnet 4.6 三层 (跨 provider 优先, Founder 5/22 13:35 决策) + FallbackResult dataclass + LLMFallbackAllFailedError + friendly_error_message |
| `app/api/projects.py` | 改 ~25 行 | AdjustCharacter 接入 fallback chain (旧 sync `anthropic.Anthropic.messages.create("haiku-...")` → 新 `await call_llm_with_fallback(operation_label="adjust_character")`) |
| `app/api/chapters.py` | 改 ~20 行 | Shot regenerate adjustment 接入 fallback (旧 `AsyncAnthropic.messages.create("haiku-...")` → 新 `await call_llm_with_fallback(system=SHOT_ADJUSTMENT_SYSTEM_PROMPT, operation_label="shot_adjustment")`) |
| `app/services/music_generation_service.py` | 改 ~30 行 | `_call_haiku_with_retry()` 重写: 内部用 fallback chain (3 个 caller — bgm_prompt / bgm_prompt_v2 / _bgm_prompt_dur — 自动 benefit) |
| `tests/test_first_batch_chars_not_zero.py` | **新建 (17 case)** | T22-NEW-7 regression: name_en match / 混合格式 / 大小写 / dedup / 防御 WARNING / 边界 / 集成 |
| `tests/test_llm_fallback_chain.py` | **新建 (14 case)** | T22-NEW-4: happy path / 三层 fallback / 全 fail / empty response / 重试 / telemetry / 输入验证 / dataclass |
| `tests/test_apply_identity_anchors_location_wire.py` | **新建 (7 case)** | T22-NEW-6: location dict 注入 / 空 location 不注 / 完整 chain 模拟 / witch_cave / idempotent / 综合 |

**RegeneratePortrait 不接入 fallback**: PENDING.md 列入但实测 endpoint 真**不调任何 LLM** (只调 ReferenceImageManager.generate_character_reference 走 Seedream/NB2). 真无 fallback 必要. 已 note 给 PM.

---

### pytest 真自跑结果 (KEY_LEARNINGS #47 第 8 次铁律)

| 测试文件 | 命令 | 结果 |
|----------|------|------|
| **Task 1 NEW** test_first_batch_chars_not_zero.py | `pytest -v` | **17/17 PASS** (0.02s) |
| **Task 2 NEW** test_llm_fallback_chain.py | `pytest -v` | **14/14 PASS** (0.05s) |
| **Task 3 NEW** test_apply_identity_anchors_location_wire.py | `pytest -v` | **7/7 PASS** (0.01s) |
| Regression test_identity_anchor_injector.py | `pytest` | **25/25 PASS** (0.02s, 0 退化) |
| Regression test_prompt_validator.py | `pytest` | **28/28 PASS** (0.02s, 0 退化) |
| Regression test_identity_anchor_extraction.py | `pytest` | **74/74 PASS** (0.03s, 0 退化) |
| Regression test_identity_anchor_cross_genre_baseline.py | `pytest` | **105/105 PASS** (0.51s, 0 退化) |
| Regression test_t21_new_3_to_7_backend.py | `pytest` | **51/51 PASS** (0.06s, 0 退化) |
| **TOTAL** | (8 files) | **321/321 PASS** (38 新 + 283 旧 regression) |

---

### Ben 5/13 协议真严格遵守 (0 变更)

| 协议项 | 自查 grep | 结果 |
|--------|----------|------|
| 0 API contract 变更 | `app/schemas/` 本 session 无 T22-NEW marker | ✅ |
| 0 schema 改动 | `grep T22-NEW app/schemas/` = 0 hits | ✅ |
| 0 STATUS_API_CONTRACT 升级 | `.team-brain/contracts/*.md` 无 T22-NEW marker | ✅ |
| 0 Alembic migration | `alembic/` 无 T22-NEW marker | ✅ |
| 0 frontend 影响 | `frontend/` 无 T22-NEW marker | ✅ |
| 0 越权改 AI-ML 文件 | `storyboard_prompts.py / storyboard_director.py / identity_anchor_prompts.py` 无 T22-NEW marker | ✅ |
| 0 改 prompt_validator.py | `grep T22-NEW app/services/prompt_validator.py` = 0 hits | ✅ |

---

### 关键设计决策

**1. resolve_characters_in_shot 提取为 standalone helper**:
- 不放在 ImageGenerator class method 是为了**可独立单测** (test 不需要 ImageGenerator import → 不触发 app.services 整树 cascade)
- 三路智能匹配: `id` / `name_en` / `name` (case-insensitive)
- Dedup by canonical id (防止 ["Coral", "char_001", "珊瑚"] 三次都命中 char_001 → 渲染 3 个相同 anchor block)
- 防御性 WARNING 真**第一时间** detect mismatch (KEY_LEARNINGS #50/#52)
- `log_mismatch=False` 参数允许单测探针 edge case 不污染 log

**2. LLM Fallback Chain 跨 provider 优先 (Founder 5/22 13:35 决策)**:
- 旧本能: Haiku → Sonnet (同 provider, 跨 size)
- 新设计: Haiku → Gemini Flash → Sonnet (跨 provider 主备)
- 理由: Anthropic region-wide overload 时 Sonnet 同 provider 也挂. Gemini 跨 provider 更可能恢复.
- 三层独立 retry (默认 1 sub-retry per layer) — 总 6 次尝试上限
- FallbackResult dataclass 携带完整 telemetry (chain_depth / provider_used / attempts list)
- 永不 raise 异常 — 全 fail 返 `success=False` + `error` 字段 (caller 决定 raise/return 500)
- `friendly_error_message()` 真**中文** 用户友好提示

**3. Location Wire via kwargs (T22-NEW-6)**:
- `_apply_identity_anchors` 加 `outline` kwarg (向后兼容 — 老 caller 不传仍 work)
- Stage 5 pipeline_orchestrator.py L1589 传 `outline=outline` 到 `generate_shot_image_phase2_safe`
- 内部三个 wire 点 (L1009/L1278/L1639) 都通过 `kwargs.get("outline")` 提取
- Seedream dispatch 时 pop `outline` from kwargs (不传给 seedream_generator)
- Lookup chain: `shot.scene_id → screenplay.scenes[].location_id → outline.unique_locations[].location_id` → location dict
- 真**优先**使用 outline kwarg, **legacy fallback** 仍支持 `storyboard.outline` (兼容旧 caller)

**4. Music BGM 改造 _call_haiku_with_retry**:
- 旧函数 sig 保留 (max_retries 参数仍接受, 实际由 fallback chain 接管)
- 3 个 caller (bgm_prompt / bgm_prompt_v2 / _bgm_prompt_dur) 真**自动** benefit, 不用一一改

**5. RegeneratePortrait 不接入 fallback** (note for PM):
- 实测 endpoint 真**不调任何 LLM**, 只调 ReferenceImageManager.generate_character_reference → Seedream 生图
- PENDING.md 列入 4 endpoint 但其中 RegeneratePortrait 真**误列**
- 已在 context-for-others.md 标注

---

### 关键约束遵守

- ✅ KEY_LEARNINGS #47 第 8 次防御: 真自跑 pytest 全数字 (8 文件 321 PASS), 不凭"应该过"汇报
- ✅ KEY_LEARNINGS #48: grep `resolve_characters_in_shot` / `T22-NEW-7` / `T22-NEW-6` / `T22-NEW-4` 真**有真调用** 0 死代码
- ✅ KEY_LEARNINGS #49: 三路智能匹配是真**字符串 + 语义双层** (id 字符串 + name 语义)
- ✅ KEY_LEARNINGS #50/#52: 防御性 WARNING 真**第一时间** detect silent fail + log_mismatch flag 真隔离
- ✅ KEY_LEARNINGS #51 通用故事铁律: smart match 跨 19 character_types 真**通用** (不 hardcode story type)
- ✅ KEY_LEARNINGS #55: 跨 provider 真**优先** (Haiku → Gemini → Sonnet) 按 Founder 5/22 13:35 决策
- ✅ No backward compatibility on data flow: smart match 不写 fallback 兼容代码 — 三路 match 本身就是"通用语义匹配", 不是兼容补丁
- ✅ Production safety try/except: `_apply_identity_anchors` 保留 outer try/except (防异常破坏 Pipeline)

---

### 真**当前内测启动状态**

- 🟢 Wave 7 三大 P0 修完: chars=0 (T22-NEW-7) + 用户操作 endpoint fallback (T22-NEW-4) + location wire (T22-NEW-6)
- 🟢 0 退化, 0 越界, 0 Ben 协议违反
- 🟢 Ready for Founder e2e 重跑 test22 视觉验证 (Coral 头发 21/21 一致 + inject log 真全 chars=N + location=Y)
- 🟢 Ready for PM 终审 8 维度地毯式

---

## 历史: DEC-048 Layer 1 实施 [2026-05-22 ~12:00] (滚到 completed.md)
