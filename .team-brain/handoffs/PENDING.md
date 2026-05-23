# 待处理交接事项

> 所有 Agent 开工前必查，完成后删除对应条目
> **⚠️ 文档更新协议**: 共享文档由PM统一更新，详见 `.team-brain/TEAM_PROTOCOL.md`

---

## 📊 当前剩余 task (5/23 17:30 update)

### 🟡 等 Founder (2 项 spot-check + 决策)
- **L-3** 跑 test25 (manga + supernatural 银发狐妖) + test26 (cyberpunk + ai_entity 出租车 AI) e2e
  - 完成 ABC 完整跨题材覆盖 (test22 manga + test27 ink 已跑, 还差 test25+26)
  - Founder 视觉验证 cross-genre Layer 1 一致性
- **L-4** 视觉 spot-check test27 31 shots + ink 古风 BGM
  - 重点: char_001 月老 mythological + char_002 李慕白 棕色长袍 + char_003 苏璃 跨 31 shots Layer 1 一致

### 🟡 可选 (Founder 决定时机)
- **TASK-WAVE-10-DEPLOY-VPS** — DevOps 第 3 次部署 Wave 10 到 VPS
  - Wave 10 commit 3faf585 + 28e33a7 改了 app/ (AI-ML 4 const + Backend wire), 需 VPS rebuild
  - e938eaa 只改 tests/ — VPS 不需 (test 不进 production container)
  - 0204b8c + 0ad9beb + 4e4a4cf + d02e14b 都只是文档/工具 — VPS 不需
  - 实际 VPS 需 push 4 commit 但只 rebuild api (含 3faf585 + 28e33a7)
- **CLAUDE.md L210/L241/L283 同步** — Founder 改 "传入仅 fullbody" → "smart selection" (AI-ML P2-2 verify 发现过时)

### ✅ 已完成 (5/22 + 5/23, 累计 10 commit)

**5/22**:
- TASK-T22-NEW-10-PORTRAIT-LAYER1-WIRE ✅ (89bcfc7, Wave 9 portrait Layer 1)
- TASK-T22-NEW-10-FULLBODY-LAYER1-WIRE (DEC-049-3) ✅ (1629332, Wave 9.1 fullbody Layer 1)
- TASK-WAVE-9-TESTER-INDEPENDENT-BASELINE ✅ (c570c2d, 623/623 PASS)
- TASK-SECRET-LEAK-REMEDIATION ✅ Step 1-5 (filter-repo + force push)
- Wave 7+8 ✅ 6 task 全闭环

**5/23 Wave 10**:
- **TASK-GEMINI-KEY-ROTATE-AFTER-GOOGLE-REVOKE** ✅ PM 自做 5 min (Founder Google Cloud 生成第 3 把 + 私聊 + PM sed .env + verify md5 + API 200)
- **TASK-T22-NEW-1-TEST-ISOLATION-EXTENDED** (P2-1) ✅ Tester e938eaa (44 PASS, 27 errors → 0)
- **Stage 5 portrait/fullbody verify** (P2-2) ✅ AI-ML 3faf585 (= by-design RIM smart selection)
- **TASK-WAVE-10-UNKNOWN-CHARACTER-TYPE-WARN** (P3-1) ✅ AI-ML 3faf585 + Backend 28e33a7 接力 (CHARACTER_FIELD_PRESERVATION_RULES + deep-merge)
- **TASK-WAVE-10-STORYBOARD-ASPECT-RATIO** (P3-2) ✅ AI-ML + Backend (ASPECT_RATIO_FIDELITY_RULES + project_aspect_ratio 透传)
- **TASK-WAVE-10-RIM-LOGGER-UNIFY** (P3-3) ✅ AI-ML (xuhua 统一)
- **TASK-WAVE-10-SEEDREAM-CHARS-COUNT** (P3-4) ✅ AI-ML (CHARACTER_COUNT_FIDELITY_RULES 禁矛盾措辞)
- **TASK-WAVE-10-KEY-PROPS-CONSTRAINT** (P3-5) ✅ AI-ML (KEY_PROPS_CONSTRAINT_RULES MAX 3 × 50 char)
- **L-1 DEC-050 finalize SECRET_HANDLING_PROTOCOL** ✅ PM 0204b8c (5 部分)
- **L-2 mysql memory verify** ✅ PM 0204b8c (memory 标 ✅ 已用阿里云 MySQL)
- **Layer 0 SECRET SCANNER** ✅ PM 0ad9beb (4 模式拦截, 实测 verify)

### 🔮 长期 (memory + Phase 6+)
- `project_mysql_migration.md` — ✅ 已完成 5/23 17:00 (memory 已 update)
- `project_schema_humanoid_fallback_remaining.md` — Wave 8 T22-NEW-9 已根治, memory 可标 ✅
- `project_confirm_outline_not_wired.md` — Wave 8 T22-NEW-8 验证已实现, memory 可标 ✅
