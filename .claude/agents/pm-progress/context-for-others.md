# PM Agent - 给其他 Agent 的信息

> **最后更新**: 2026-05-26 18:10 (test29 e2e 90分 + 非人类专项修复审查通过 + B 方案部署中)
> **当前阶段**: test29 修复 (#4/#5/#6/#7) 审查通过 → DevOps commit+push (Ben 闸门) → 部署

## 🚀 test29 修复 + Wave 13 一起部署 (5/26, Founder B 方案)

test29《荷塘渡》e2e 90分, Wave 13 全实测生效。炸出非人类人类中心假设链 5 缺口, 当场修 #4/#5/#6/#7 (PM 地毯式+Ben维度审查通过), #8 内测后。回溯 `analysis/TEST29_FULL_RETROSPECTIVE_2026-05-26.md`。

### 给各 agent 的状态
- **@DevOps**: Founder B 方案 — commit (Wave13+test29 全部, 分组+message 全覆盖) + push GitHub **先停**; Founder 知会 Ben 后 PM 放行 → rsync VPS + Docker rebuild + #5c Alembic + layout.tsx rebuild 硬刷。⚠️ 含 #4 DB-infra = Ben 域。
- **@Backend**: #4 Packet retry 审查通过 (21 pytest)。⚠️ **你的 completed.md 漏更 #4, 请补**。
- **@AI-ML**: #5(含补挖 #5a 锚点层)/#6/#7 审查通过 (499 pytest)。非人类消费层专项落地, memory `project_schema_humanoid_fallback_remaining` prompt 层已解。
- **@Tester**: 本轮单测已 PM 亲跑 (db_retry 21 + AI-ML 域 499)。#5/#7 视觉真证待 Founder e2e 复测 (test30, 可选, Founder 选了不复测先信任单测)。
- **全体**: Wave13+test29 全未 commit, DevOps commit 前继续禁 destructive git。

### 非人类支持关键认知 (改图像/角色/校验/BGM 的 agent 必读)
数据层 Stage 2 把所有 type 属性写 `physical`, 消费层须从 `physical` 读 (非 `character[type]`)。多角色 shot 须强制角色分离 (no fusion)。ShotValidator 计数已通用化 (含非人类)。见 DEC-053。

---
（以下为 Wave 13 历史）

> **(历史) 最后更新**: 2026-05-25 (Wave 13 集成关口第一道 ✅)
> **(历史) 当前阶段**: Wave 13 FIXBATCH PM 审查全绿 (DEC-052) — 待 Tester 双绿 + DevOps 第 5 次部署

## 🟢 Wave 13 内测前 FIXBATCH — PM 审查通过 (5/25, DEC-052)

代码全部写完仍在工作区未 commit (HEAD=68e4211)。**PM 5+1 Ben 协议 + 完整调用栈审查全绿无 blocker**。

### 给各 agent 的状态
- **@Tester**: 第二道复测进行中 — pytest 30 新 (db_retry 14 + clothing_bypass 12 + regenerate_async 4) + vitest 15 + 全量回归 0 退化 + 独立核对 §9.7.4 前后端字段。用 `venv/bin/python3 -m pytest`。已知 pre-existing fail (非本批): test_supernatural_missing_all_fields_fails (Wave 8 warn-not-raise) / b51 case9-10 / async_anthropic_t18_j / 4 ERROR (需 key)
- **@DevOps**: 双绿后 commit 3 组 (Backend / Frontend / 契约+文档, 见 PENDING 完整文件清单) + push + VPS 第 5 次部署。⚠️ layout.tsx root layout inline script HMR 不刷新, 须 rebuild + 浏览器硬刷新; DB 新列 Alembic (#5c) 确认
- **@Backend**: #5d/#6/#5e 审查通过, §9.7.4 三方契约对齐无误。注: db_retry.py / character_designer.py 注释引用旧行号 (L82-118/L127), 实际 L99-134/L144 — 仅注释陈旧逻辑对, 非 blocker, 可下次顺带订正
- **@Frontend**: #4A/#4B/#5/#6/#9 审查通过。#5 404 真根因 (模板字符串吃反斜杠) 源码层根治, 部署后须在 client.log 确认 proxy-init version=w13-404-v2 (真实浏览器加载新版)
- **@AI-ML**: #5b 核实通过 (0 代码改动)。clothing 旁路已由 Backend #5e 修

### 关键契约提醒 (§9.7.4, 所有改 regenerate/adjust 的 agent 必读)
regenerate-portrait 已异步 (同步→202+job_id), 复用 adjust 轮询端点 GET /characters/adjust-jobs/{job_id}, 用 `kind` 字段区分 (adjust | regenerate_portrait)。result shape: {success, char_id, portrait_url, fullbody_url, message}。STATUS_API_CONTRACT v1.6 §9.7.4 已落地。

---
（以下为 Wave 10 历史）

> **(历史) 最后更新**: 2026-05-23 17:30
> **(历史) 当前阶段**: Wave 10 全完成 (P0+P2+P3+L) — 剩 L-3/L-4 Founder + 可选 VPS 第 3 次部署

## Wave 10 完成数据 (5/23 14:30-17:30, 3h)

- 4 域并行: AI-ML Opus 4.7 (6 项) + Tester Sonnet 4.6 (P2-1) + Backend Sonnet 4.6 接力 (P3-1+P3-2 wire) + PM 自做 (L-1+L-2)
- 4 commit: 3faf585 + e938eaa + 28e33a7 + 0204b8c
- 138 PASS, 0 fail (PM 用 venv 自跑 verify)
- Ben 协议 5+1 全守住

## 给所有 agent 的重要提醒 (Wave 10 新加)

### 1. Layer 0 SECRET SCANNER (commit 0ad9beb)
- `scripts/pre-commit-frontend-impact.sh` 含 4 模式拦截: `AIzaSy[33char]` / `sk-ant-` / `sk-` / `AKLT`
- 拦截 staged 文件内容 (不只 file name)
- 白名单: `[redacted-key]` / `xxx` / `***` 占位符
- **任何 commit 含真 key → exit 1**
- 强制启用 (新开发环境 `bash scripts/install_pre_commit_hook.sh`)

### 2. DEC-050 SECRET_HANDLING_PROTOCOL (commit 0204b8c)
- 文档脱敏铁律 + Pre-commit Layer 0 + Key Rotation 流程 + Destructive Git 前 commit/stash + Google 自动 revoke 行为
- 详见 `.team-brain/decisions/DECISIONS.md` DEC-050

### 3. Wave 10 AI-ML 4 个新 const (commit 3faf585, app/prompts/storyboard_prompts.py)
- `CHARACTER_FIELD_PRESERVATION_RULES` (4461 chars) — AdjustCharacter LLM mandatory fields 8 项 (含 character_type)
- `ASPECT_RATIO_FIDELITY_RULES` (2750 chars) — storyboard 用 project's aspect_ratio
- `CHARACTER_COUNT_FIDELITY_RULES` (3207 chars) — Seedream chars=N 强化 (禁 visible 矛盾措辞)
- `KEY_PROPS_CONSTRAINT_RULES` (2718 chars) — key_props MAX 3 × 50 char

### 4. Backend 接力 wire (commit 28e33a7)
- `api/projects.py` AdjustCharacter: lazy import CHARACTER_FIELD_PRESERVATION_RULES + 拼到 LLM prompt + deep-merge `merged_char = dict(target_char); merged_char.update(updated_char)`
- `storyboard_director.py` + `pipeline_orchestrator.py`: 加 `project_aspect_ratio: str` 参数 + 透传 + L1068 + L2334 fallback 改用 project.aspect_ratio

### 5. RIM logger 统一 xuhua (commit 3faf585)
- `reference_image_manager.py` L25 + L873 logger `getLogger(__name__)` → `getLogger("xuhua")`
- 跟 `identity_anchor_injector.py` 一致, 便于 log 聚合

### 6. P2-2 Stage 5 portrait/fullbody = by-design (AI-ML verify)
- RIM smart selection: close-up/medium-shot ≤ 2 角色 → portrait, 其余 → fullbody
- 不是 bug, memory CLAUDE.md L210/L241/L283 "传入仅 fullbody" 描述过时, Founder 需同步

### 7. Stage 5 单角色 shot test27 实测看到 `refs=2 (1 portrait + 1 scene_ref)` 是正确 (by-design)

### 8. Pipeline 跑 LLM 的 fallback chain
- Gemini key revoke 后 Pipeline 自动 fallback Claude (T20-14 内置)
- 5/23 已 rotate 第 3 把 key (PM 自做), Pipeline 现在用新 key
- LLMFallbackChain (T22-NEW-4) Haiku → Gemini → Sonnet 仍工作

## 文档路径

- `.team-brain/handoffs/PENDING.md` — Wave 10 全标 ✅
- `.team-brain/decisions/DECISIONS.md` DEC-050 (5/23 finalize)
- `.team-brain/knowledge/KEY_LEARNINGS.md` #57 (跨路径 wire) + #58 (destructive git)
- `.team-brain/analysis/E2E_TEST22_TEST27_FULL_DEEP_RETROSPECTIVE_2026-05-22.md` (12 章节回溯)
