# Backend Agent - 当前任务

> **最后更新**: [2026-05-26] ✅ test29 #4 Packet sequence 修复 — `db_retry.py` 加认 "packet sequence number wrong" 为 transient — 21 测 PASS (14 旧 + 7 新), 78 相关域 PASS, 0 退化 (Opus 4.7 default)

---

## ✅ 完成: test29 回溯 #4 — Packet sequence 握手腐败漏接修复 [2026-05-26, Opus 4.7 default]

### 任务背景 (test29 回溯 #4, analysis/TEST29_FULL_RETROSPECTIVE_2026-05-26.md)
- 浏览器 tab 挂起→恢复时突发并发轮询 `chapters/N/status`, 连接池被迫同时新建多条连接, 每条走 MySQL 认证握手 (aiomysql/connection.py:844 `_request_authentication`→:629 `_read_packet`)
- 公网+Astrill VPN 并发握手被截断 → `pymysql.err.InternalError: Packet sequence number wrong - got N expected M` → 3 次 500 (15:46:00/31/44), 前端 retry-on-resume 自愈
- **#5d retry 为何漏接**: 此 `InternalError` 虽是 `DBAPIError` 子类 (isinstance 命中分支 1), 但既无 `connection_invalidated` 也不含 2013/2006/2003 码 → `_is_transient_connection_error` 判 False → 不重试 → 500

### 改动文件 (1 改 + 1 测扩展, 孤立, 0 越界 AI-ML prompt 层)
| 文件 | 改动 |
|------|------|
| `app/middleware/db_retry.py` | 新增 `_TRANSIENT_MESSAGE_FRAGMENTS = ("packet sequence number wrong",)` 常量 + `_matches_transient_message_fragment()` (小写匹配) + `_matches_transient_signature()` (统一码匹配 OR 消息片段)。分支 1 的 2 处 `_matches_transient_code` 改调 `_matches_transient_signature`。docstring 同步说明 #4 |
| `tests/test_wave13_db_retry_middleware.py` | +7 case: packet seq 判 transient / 大小写不敏感 / 经 __cause__ 链 / InternalError 不含短语不误伤 / 业务错含 'packet' 单词不误伤 / GET 重试 1 次自愈 / POST 不重试 |

### #5d 4 重安全约束全保持 (0 破坏)
1. **仅幂等 GET/HEAD 重试** — `_IDEMPOTENT_METHODS` 未动, POST/PUT/PATCH/DELETE 仍直接放行 (test: POST packet seq 只调 1 次)
2. **限 1 次** — `_MAX_RETRIES=1` 未动
3. **业务错绝不重试** — packet sequence 是连接握手层错误 (aiomysql 认证阶段), 不与 ValueError/HTTPException/SQL 语法 ProgrammingError 混淆; 片段足够具体 (完整短语 "packet sequence number wrong"), 业务消息含单词 'packet' 不命中 (test 证)
4. **不掩盖真错误** — 非 transient 立即原样抛; 重试后仍失败原样抛
- retry 自愈机制: GET 重跑 `call_next` → `Depends(get_db)` 重新 checkout 干净连接 → 重做握手大概率成功 (test29 15:46:44 后 0 错误已证)

### 匹配精度判断 (无误伤风险)
- 短语 "packet sequence number wrong" 是 pymysql 握手腐败的**专有错误字符串**, 不出现在任何业务/SQL 语义错误中
- 小写匹配处理大小写差异 (pymysql 输出 "Packet sequence number wrong")
- 走完整异常链 `__cause__`/`__context__`, 深埋时仍识别
- 实测: 含 'packet' 业务单词 (`"invalid network packet count"`) + 不含短语的 InternalError (1364 字段错) 均判 False

### 测试 (venv/bin/python3)
- `test_wave13_db_retry_middleware.py`: **21 PASS** (14 旧 + 7 新)
- 相关域回归 (db_retry + t20_53_db_pool_config + status_authoritative): **78 PASS, 0 退化**
- `app.main` import OK (中间件 wire 未动)

### Ben 协议 5+1
- 0 schema 改动 / 0 Alembic migration / 0 STATUS_API_CONTRACT 升级 / 0 frontend 影响 ([frontend-impact: no], 透明重试用户无感)
- 不碰 AI-ML prompt 层 (character_prompt_builder/ShotValidator/image_generator 一律没动 — #5/#6/#7 是 AI-ML 域)

---

## ✅ 完成: Wave 13 内测前 FIXBATCH #5d + #6 + #5e [2026-05-25, Opus 4.7 xhigh]

### 任务背景 (test28 回溯 + VPS 实测)
- **#5d**: idle 后阿里云 MySQL 2013 lost connection, 用户离开看片再回来第 1 次操作 500。pool_pre_ping 在公网 + ping 超时 (Errno60) 没完全防住
- **#6**: regenerate-portrait 端点仍同步 ~60s 转圈 (adjust 已 Wave 12 异步, regenerate 同类问题)
- **#5e**: `_validate_characters` (character_designer.py L619) clothing 必填对【所有 type 一刀切】, 真 object/aquatic/plant/insect 天然没衣服 → Stage 2 raise, 在 LLM fallback 之外 + orchestrator 无 retry → 冲垮 pipeline (AI-ML #5b 挖出, PM verify 属实)

### 改动文件 (3 改 + 2 新测 + 1 新 middleware)
| 文件 | 改动 |
|------|------|
| `app/middleware/db_retry.py` | 🆕 `DBConnectionRetryMiddleware` — transient MySQL connection 错误自动重试 (仅幂等 GET/HEAD, 限 1 次) + `_is_transient_connection_error` 检测器 |
| `app/main.py` | wire DBConnectionRetryMiddleware (加在 CORS 之前 → CORS 在最外层, 保证重抛错误仍带 CORS 头) |
| `app/database.py` | pool_recycle 1800s → 600s (主动回收 idle 连接, 赶在云端 idle-timeout 前重建) |
| `app/api/projects.py` | regenerate-portrait 改异步 (202+job_id, 复用 adjust_job_manager kind="regenerate_portrait" + 同一轮询端点) + 后台 worker `_run_regenerate_portrait_in_background` + core `_regenerate_portrait_core` |
| `app/services/character_designer.py` | #5e A: `NON_CLOTHING_TYPES` 常量 + `_validate_characters` 对非穿衣 type clothing 缺字段降 warning 不 raise (同 anthropomorphic_animal physical warning pattern); #5e B: `_build_prompt` 加 NON-CLOTHING CHARACTER TYPES CLOTHING RULES 指引 (object/aquatic/plant/insect 等填 n/a) |
| `tests/test_wave13_db_retry_middleware.py` | 🆕 14 case (transient 检测 + 端到端中间件: GET 重试1次/POST不重试/业务错不重试/限1次) |
| `tests/test_wave13_clothing_bypass.py` | 🆕 12 case (非穿衣 type 不崩 + human 仍 raise surgical) |
| `tests/test_wave13_regenerate_portrait_async.py` | 🆕 4 case (端点 202 + 后台函数存在 + job 生命周期) |

### #5d retry 如何防副作用 (4 重约束, 代码可证)
1. **只 transient connection 错误**: `_is_transient_connection_error()` 走完整异常链, 只认 SQLAlchemy OperationalError/InterfaceError/DBAPIError (connection_invalidated 或 orig 含 2013/2006/2003) + OSError(ETIMEDOUT/ECONNRESET/ECONNREFUSED/EPIPE)。业务错 (ValueError/HTTPException/ProgrammingError SQL语法) 绝不重试 (实测 test 证)
2. **只幂等 GET/HEAD**: `_IDEMPOTENT_METHODS = {GET, HEAD}`, POST/PUT/PATCH/DELETE 直接放行不重试 (防重复写, 实测 POST transient 只调 1 次)
3. **限 1 次**: `_MAX_RETRIES = 1` (实测一直 transient 失败 → 共 2 次调用后放弃)
4. **不掩盖真错误**: 非 transient 立即原样抛; 重试后仍失败原样抛 (交全局 handler 转 500)
- 重试机制: GET 重跑 `call_next` → `Depends(get_db)` 重新 checkout 新连接 → pool_pre_ping ping 验证 / pool_recycle 已回收 idle → 拿健康连接成功

### #6 regenerate 异步契约 (Frontend 依赖, 同 adjust pattern)
**POST** `/api/projects/{project_id}/characters/{char_id}/regenerate-portrait` (status **202**, 原 200 同步)
- 立即返回: `{ "success": true, "job_id": "<uuid>", "status": "pending", "char_id": "char_001", "message": "..." }`
- 快速校验仍同步返 404/400 (项目不存在/未生成大纲/角色不存在)
**GET** `/api/projects/{project_id}/characters/adjust-jobs/{job_id}` (复用 adjust 轮询端点, job.kind="regenerate_portrait")
- result 完成时含 `{ success, char_id, portrait_url, fullbody_url, message }` (与旧同步返回体一致)
- ⚠️ 契约已 paste 给 PM 代改 STATUS_API_CONTRACT (regenerate job 契约)

### #5e A 防崩范围
- `NON_CLOTHING_TYPES = {animal, aquatic, plant, insect, object, elemental, vehicle_character}` — 缺 clothing 子字段降 warning 不 raise
- 不含 human / anthropomorphic_animal / 超自然人形 (supernatural/undead/mythological/fantasy_creature) / robot / alien 等穿衣 type → 仍严格校验 (surgical, 不破坏现有)
- #5e B prompt 在 character_designer.py (我的域) 直接加, 无需协调 AI-ML

### fallback 红线 (DEC-051) 全保留
- #6 regenerate: B57 同步重生 fullbody + 非阻塞 except 兜底全保留, 异步化只改调用方式
- #5e A: 只放宽非穿衣 type 的 clothing 校验, 0 删 fallback

### 测试 (venv/bin/python3)
- 新增 30 case 全 PASS (14 retry + 12 clothing + 4 regenerate)
- adjust job manager 回归 15 PASS
- 相关域 (character/clothing/designer/schema/adjust/regenerate/pipeline) 560 PASS
- ⚠️ 已知 pre-existing fail (非我改动): `test_supernatural_missing_all_fields_fails` (Wave 8 CharacterSchema warn-not-raise, AI-ML 已标过时建议更新断言) / b51 case9-10 (T20-17 storyboard_director name_en) / async_anthropic_t18_j (grep chapters.py 结构) / 4 ERROR (真实 API 集成测试需 key/网络)

---

## ✅ 完成: Wave 12 P2-1 (adjust 异步化) + P2-2 (Stage 1-4 sub-progress) [2026-05-24, Opus 4.7 xhigh]

### 任务背景 (test26 实证)
- **P2-1**: `/characters/{char_id}/adjust` 同步阻塞 90s (LLM 重写 + portrait 重生 + fullbody 重生 串行) → 前端 fetch 死等转圈, POST 重试 3 次
- **P2-2**: progress 只在 stage 边界更新, Stage 2 portrait loop (6 角色 × ~30s) 期间 progress 冻结在 6% → ETA 冻结

### 改动文件 (3 改 + 2 新)
| 文件 | 改动 |
|------|------|
| `app/services/adjust_job_manager.py` | 🆕 进程内 adjust/regenerate job 注册表 (in-memory, asyncio.Lock, TTL 清理) |
| `app/api/projects.py` | adjust_character 改异步 (202+job_id) + 新增 GET adjust-jobs/{job_id} 轮询端点 + 后台 worker `_run_adjust_character_in_background` + 核心逻辑 `_adjust_character_core` |
| `app/services/pipeline_orchestrator.py` | P2-2: Stage 2 portrait loop 每角色推 sub-progress (band 6→9) |
| `tests/test_wave12_adjust_async_job.py` | 🆕 15 case (job manager 契约 + P2-2 公式) |

### 架构决策 — P2-1 异步 job 存储用 in-memory (不新建 DB 表)
- adjust 是短命 (~90s) UI 操作, 角色数据变更 (portrait_url/fullbody_url/outline/characters_json) 已由现有逻辑 DB 持久化, job 只跟踪瞬态 status/progress/result
- 新建 DB 表 = Alembic migration = backend_Ben 领域 (DB/架构) + 跨团队协调, 对 90s UI 操作过重
- 单 uvicorn worker (docker/Dockerfile.api 无 --workers), in-memory 可行 (与现有 start-generation asyncio.create_task 同进程假设一致)
- 进程重启时未完成 job 丢失 → 用户重点一次即可 (角色当前状态已在 DB)

### 异步契约 (Frontend Wave B 依赖)
**POST** `/api/projects/{project_id}/characters/{char_id}/adjust` (status 202)
- Body: `{ "adjustment": "想让他胖一点" }`
- 立即返回: `{ "success": true, "job_id": "<uuid>", "status": "pending", "char_id": "char_002", "message": "..." }`
- 快速校验仍同步返 404/400/500 (项目不存在/未生成大纲/角色不存在/无 ANTHROPIC_KEY)

**GET** `/api/projects/{project_id}/characters/adjust-jobs/{job_id}` (轮询)
- 返回:
```json
{
  "job_id": "<uuid>", "char_id": "char_002", "kind": "adjust",
  "status": "pending|processing|completed|failed",
  "progress": 0-100,
  "stage_message": "正在重新绘制肖像...",
  "result": { "success": true, "character": {...}, "char_id": "char_002",
              "portrait_url": "/static/.../char_002_portrait.png?v=123",
              "fullbody_url": "/static/.../char_002_fullbody.png?v=123",
              "message": "角色已调整" } | null,
  "error": "AI 服务暂时不可用..." | null
}
```
- `status=completed` → `result` 含最终角色数据 (与旧同步端点返回体一致, 字段名不变)
- `status=failed` → `error` 含友好错误信息
- job 不存在/过期/越权 → 404
- progress 节点: 5 (分析) → 15 (重写) → 30 (保存) → 40 (重绘肖像) → 70 (重绘全身) → 100 (完成)

### P2-2 progress 数据格式 (Frontend ETA 插值依赖)
- progress 字段语义不变 (ChapterStatus.progress 0-100), 仅 Stage 2 内部新增递增节点
- character_design band = (6,10): 现在每完成 1 个角色画像推一次 (6,7,8,9 across N chars)
- stage_message 格式: `正在生成角色画像 (2/6: 苏晨)...`
- Frontend 仍走现有 GET /chapters/{n}/status 轮询, `actual_elapsed_sec` 已存在可用于 stage 内插值
- Stage 1 (outline) / Stage 3 (screenplay batch ≤8 scenes) 是单次 opaque LLM 调用, 后端无法诚实细分 → 由 Frontend 时间插值 (Wave B option ①) 兜底, 后端不造假进度

### fallback 全保留 (DEC-051 红线, 0 删除)
- ✅ LLMFallbackChain (Haiku→Gemini→Sonnet) via call_llm_with_fallback
- ✅ B58-followup clothing dict fallback
- ✅ B57 fullbody 同步重生 (用新 portrait 作参考)
- ✅ portrait_ref RISK-T17-9 fix (传现有 portrait 锁 identity)
- ✅ portrait + fullbody 非阻塞 except 兜底
- 异步化只改「调用方式」, 逻辑从旧端点逐行迁移到 `_adjust_character_core`

### pytest: 252 PASS, 0 退化
- test_wave12_adjust_async_job (新) 15 + adjust_regen 14 + status_authoritative + eta_calculation + v3_eta + d2_eta + progress_per_shot + pipeline_failure + pipeline_fallback + character_designer_validate + llm_fallback_chain = 252 PASS / 2 skip

### Ben 协议 5+1
- 0 schema 改动 / 0 Alembic migration / 0 STATUS_API_CONTRACT 升级
- ⚠️ **API 契约变更**: adjust 端点行为变 (同步→异步 202+job), Frontend 必须改 → `[frontend-impact: yes]`
- 不碰 .env / app/database/ / .team-brain/team_ben / frontend / style_enforcer

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
