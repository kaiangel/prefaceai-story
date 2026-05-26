# Project Status

> **Updated**: 2026-05-26 17:55 (PM — test29 e2e 90分 + 非人类专项修复)
>
> **5/23-5/26 进展补记**: Wave 13 内测前 FIXBATCH 全修复 (5/25) → test29《荷塘渡》e2e 跑通 Founder 90分 (5/26), Wave 13 全部实测生效 → 炸出「非人类人类中心假设链」5缺口, 当场修 #4(Packet retry, Backend)+#5/#6/#7(非人类消费层专项, AI-ML, 含补挖 #5a 锚点层), PM 地毯式+Ben维度审查通过, #8(BGM)内测后。**Wave13+test29 全未 commit (HEAD=68e4211), 待 e2e 视觉复测(test30) + commit + VPS 部署(知会 Ben)。** 详见 `analysis/TEST29_FULL_RETROSPECTIVE_2026-05-26.md`。

## Phase 状态

| Phase | 状态 | 备注 |
|-------|------|------|
| Phase 1-4 | ✅ 完成 | Pipeline + 角色一致性 + 音画对齐 + 条漫文字 |
| Phase 4.5 | 🔄 WIP | 视频合成 |
| Phase 5 | ✅ LP 完成 | Landing Page + 10 子页面 |
| Phase 6 | 🟡 启动 10% | Git + DB + Layer 1 完成 + 内测准备 |

## 当前热点: Wave 7 P0 修 (5/22 内测启动卡点)

### Wave 状态总览

| Wave | 时段 | 状态 |
|---|---|---|
| Wave 1+2+Round 3 (T20 全 P0/P1) | 5/20 17:20-19:41 | ✅ 11 task 闭环 |
| Wave 3 (3 P3 long-tail) | 5/20 19:50- | ✅ 完成 |
| Wave 4 (T21-NEW-1 8 type fallback) | 5/20 20:30-21:01 | ✅ 25/25 PASS |
| Wave 4.5 (5 type humanoid fallback wave2) | 5/21 21:15-21:50 | ✅ 16/16 PASS |
| Wave 5 Backend (Stage 4.5 + 4 task) | 5/21 19:25-22:30 | ✅ 51/51 + 240/240 |
| Wave II Frontend (Stage 4.5 SceneRefsPreview) | 5/21 22:40- | ✅ 14/14 + 0 errors |
| Wave 6 Layer 1 Identity Anchor v1.0 | 5/22 早间 | ✅ 306 PASS (AI-ML 74 + Backend 127+365 + Tester 105) |
| Wave 7 (T22-NEW-7/4/6 P0 + T22-NEW-2 P2) | 5/22 14:25- | 🔄 派工中 |
| Wave 8 (内测后, T22-NEW-5 + T22-NEW-1) | 内测后 | 🔮 待派 |

## 当前未修

| # | Task | 严重度 | Owner | 状态 |
|---|------|--------|-------|------|
| 1 | T22-NEW-7 Layer 1 chars=0 | 🔴🔴 P0 | Backend Opus 4.7 max | 🔄 Wave 7 修中 |
| 2 | T22-NEW-4 fallback 4 endpoint | 🟡 P0 升级 | Backend Opus 4.7 max | 🔄 Wave 7 修中 |
| 3 | T22-NEW-6 Layer 1 location wire | 🟡 P2 | Backend Sonnet 4.6 | 🔄 Wave 7 修中 |
| 4 | T22-NEW-2 SceneRefsPreview UX | 🟡 P2 | Frontend Sonnet 4.6 | 🔄 Wave 7 修中 |
| 5 | T22-NEW-5 R4-2 砍 | 🟡 P2 | 推 Wave 8 | 🔮 内测后 |
| 6 | T22-NEW-1 test isolation | 🟢 P3 | Wave 6+ | 🔮 long-tail |

## 内测启动状态

- ✅ Layer 1 Identity Anchor Framework v1.0 (5/22 上午完成)
- 🔄 Wave 7 P0 修 (~5-6h, 5/22 14:25 启动)
- 🔮 e2e 重跑 test22 视觉验证 (Wave 7 后)
- 🔮 Founder 签字 → 内测启动 (5/22 晚 or 5/23)

## 关键文档

- `.team-brain/analysis/SESSION_FULL_BUG_AUDIT_2026-05-21.md` — 历史 78 bug audit
- `.team-brain/analysis/E2E_TEST22_LAYER1_FULL_AUDIT_2026-05-22.md` — 5/22 e2e Layer 1 audit
- `.team-brain/handoffs/PENDING.md` — Wave 7 全 task 详情
- `.team-brain/contracts/STATUS_API_CONTRACT.md` — v1.4 (Wave 7 不变)
- `.team-brain/decisions/DECISIONS.md` — DEC-047 Stage 4.5 + DEC-048 Layer 1
- `.team-brain/knowledge/KEY_LEARNINGS.md` — #47-55 (5/22 新加 #50-55)
- `docs/CHARACTER_IDENTITY_FRAMEWORK.md` v1.0 — Layer 1 实施依据
