# PM Agent - 给其他Agent的信息

> **最后更新**: 2026-05-22 15:25
> **当前阶段**: Wave 7+8 全闭环 (6 task, 786+ PASS) — Tester baseline regression 跑中, 等内测启动

---

## 内测启动状态 (5/22 15:25)

✅ **6 个 P0/P2 task 全修齐** (5/22 14:25-15:17):
- Wave 7 Backend (Opus 4.7 max): T22-NEW-7 (chars=0 ID format mismatch 根因修) + T22-NEW-4 (Haiku→Gemini→Sonnet 三层 fallback 4 endpoint) + T22-NEW-6 (Layer 1 location wire)
- Wave 7 Frontend (Sonnet 4.6): T22-NEW-2 (SceneRefsPreview 智能展示)
- Wave 8 Frontend (Sonnet 4.6): T22-NEW-5 frontend (砍 R4-2 5 文件) + T22-NEW-8 (0 改动 已实现)
- Wave 8 Backend (Sonnet 4.6): T22-NEW-9 (通用 fallback 架构 19→4 entries) + T22-NEW-5 backend (R4-2 wait loop 移除 + STATUS_API_CONTRACT v1.5)

🟡 **进行中**: Tester Sonnet 4.6 跨题材 baseline regression (~1h)
🔮 **剩余**: DevOps 同步部署 + e2e 重跑 test22 + Founder 视觉验证 → 内测启动

## 关键架构改造 (Wave 6-8 累计)

### Layer 1 Identity Anchor Framework v1.0 (DEC-048)
- AI-ML M1 spec: `.claude/agents/ai-ml-progress/context-for-others.md` (837 行)
- Backend 实施: `app/services/identity_anchor_injector.py` (400+ 行) + `app/services/prompt_validator.py` (260 行)
- 5 维 anchor (character/style/location/props/time) 强注入 Stage 5 image_prompt
- **关键 fix (5/22 Wave 7)**: `resolve_characters_in_shot()` 三 key fuzzy match (id/name_en/name) 修 ID format mismatch

### 三层 LLM Fallback Chain (T22-NEW-4 Wave 7)
- `app/services/llm_fallback_chain.py` 新建 (404 行)
- `call_llm_with_fallback(operation_label, ...)` Haiku 4.5 → Gemini 3.1 Flash → Sonnet 4.6
- 跨 provider 优先 (Anthropic overload 时 Gemini 接管)
- 接入: AdjustCharacter + Shot Regenerate + Music BGM (RegeneratePortrait 不需要, 不调 LLM)
- log: `[LLMFallbackChain] op=X chain_depth=N provider_used=Y SUCCESS via FALLBACK`

### 通用 Schema Fallback 架构 (T22-NEW-9 Wave 8)
- `pipeline_schemas.py` 重构: `_TYPE_REQUIRED_GROUPS` 19→4 entries (减 79%)
- 新增: `has_humanoid_fallback()` / `_HUMANOID_FALLBACK_FIELDS` / `_STRICT_TYPES` / `_ANTHRO_ANIMAL_APPEARANCE_FIELDS`
- 通用 fallback: 任何 character 含 humanoid 外貌字段 → 视为有效拟人形态
- 严格 2 type: animal + vehicle_character (不接受 humanoid fallback)
- 行为变更: `_warns_not_raises` (Pipeline 不阻塞)

### 砍 R4-2 文字层场景确认 (T22-NEW-5 Wave 8)
- Backend: `pipeline_orchestrator.py` R4-2 wait loop 完整移除 (Stage 3 → 直接 Stage 4)
- Backend: `chapters.py` `confirm-scenes` endpoint noop + deprecation log (向后兼容)
- Backend: `_derive_ui_phase` 移除 scene_review (scenes_ready → storyboard_running 直连)
- Contract: STATUS_API_CONTRACT v1.4→v1.5 (8 状态机, scene_review 移除)
- Frontend: 5 文件改 (types/createUrl/CreateContent/StageC/StageB)
- **部署铁律**: Frontend + Backend 必须**同时部署**

### Stage 4.5 Scene Image Preparation (DEC-047 Wave 5)
- 在 Stage 4 storyboard 后, Stage 5 前插入 Stage 4.5
- 提前生成 interior/exterior 场景参考图 → 用户在 R4-3 视觉确认
- T21-NEW-7 优化: Stage 5 复用 Stage 4.5 scene_ref_manager (省 5+ min)
- DB: `projects.scene_references_confirmed` + `project_chapters.scene_references_json` (Alembic 006)

## 给所有 agent 的重要提醒 (5/22 update)

### 1. STATUS_API_CONTRACT v1.5 (T22-NEW-5 升级)
- 8 ui_phase 状态机 (scene_review 移除)
- `_derive_ui_phase` 真**不再返** scene_review
- 转换图: Stage 3 完成 → 直接 storyboard_running (不再 scenes_ready 等待)
- 改任何 backend 监控字段必须 commit message 含 `[frontend-impact: yes/no]` label

### 2. Layer 1 Identity Anchor 强注入 (Wave 6+7)
- `image_generator._apply_identity_anchors` 真**自动**调 `inject_identity_anchors` + `PromptValidator`
- 真**重要**: shot 真`characters_in_scene` 字段真**可以是** char_id / name_en / name 任意, Backend 真**三 key fuzzy match**
- 添新 character_type 真**不需要** hotfix (Wave 8 通用 fallback)

### 3. 三层 Fallback Chain (T22-NEW-4)
- 任何调 LLM 真**应该**用 `llm_fallback_chain.call_llm_with_fallback(operation_label, ...)`
- 不要直接调 anthropic.Anthropic 真**裸调** (除 Pipeline Stage 1-5 真**已有 T20-14 fallback**)

### 4. 本地 backend 禁用 --reload
uvicorn --reload + 阿里云远程 MySQL = metadata lock 死锁。用 `nohup uvicorn ... --port 8000` 不带 --reload。

### 5. 单一画幅铁律 (D.15) + 单一生图模型铁律 (D.17)
全 Pipeline 用 Seedream (`doubao-seedream-5-0-260128`), 严禁 NB2/Seedream 运行时混用。

### 6. 高风险文件回归测试
改 `image_generator.py` / `storyboard_prompts.py` / `storyboard_service.py` / `pipeline_schemas.py` 必须跑回归测试 (Wave 7+8 累计 786+ test)。

## 关键文档路径

- `.team-brain/handoffs/PENDING.md` — 头部新加 COMPLETED 汇总 (Wave 1-8) + 剩余 task 真**0 P0**
- `.team-brain/contracts/STATUS_API_CONTRACT.md` v1.5
- `.team-brain/decisions/DECISIONS.md` — DEC-047 Stage 4.5 + DEC-048 Layer 1 (DEC-049 候选: T22-NEW-9 通用 fallback 架构)
- `.team-brain/knowledge/KEY_LEARNINGS.md` — #44-56 (5/22 新加 #50-56)
- `.team-brain/analysis/E2E_TEST22_LAYER1_FULL_AUDIT_2026-05-22.md` — 5/22 e2e Layer 1 audit
- `.team-brain/analysis/SESSION_FULL_BUG_AUDIT_2026-05-21.md` — 5/21 历史 78 bug audit
- `docs/CHARACTER_IDENTITY_FRAMEWORK.md` v1.0 — Layer 1 spec
