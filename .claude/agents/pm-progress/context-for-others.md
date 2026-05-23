# PM Agent - 给其他 Agent 的信息

> **最后更新**: 2026-05-23 17:30
> **当前阶段**: Wave 10 全完成 (P0+P2+P3+L) — 剩 L-3/L-4 Founder + 可选 VPS 第 3 次部署

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
