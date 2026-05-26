# PM Agent - 当前任务

> **最后更新**: 2026-05-26 16:30 (test29 e2e 90分 + 全维度回溯 + 非人类专项派活中)
> **状态**: 🔧 test29 派活进行中 — Backend(#4) ‖ AI-ML(#5/#6/#7) 并行, 待 spawn

## test29《荷塘渡》e2e 完成 + 全维度回溯 + 派活 (5/26)

Founder 真机 e2e 跑通 (watercolor + 红锦鲤金爷 aquatic + 菖蒲小蒲 plant + 荷塘 concept, 专踩非人类盲区)。**成片 90 分**。Wave 13 修复全部实测生效 (#5e/#6/#4A/#4B/#5-404/B52/ETA/T17/条漫文字/画幅 3:4)。回溯 `analysis/TEST29_FULL_RETROSPECTIVE_2026-05-26.md` (full-retrospective skill, 像素级看图)。

**5 bug 同一主线「非人类人类中心假设链」**(数据层 Stage 2 已通用, 消费层全人类中心):
- #4 Packet sequence (Backend, db_retry 漏接 InternalError) — 内测前
- #5 非人类 builder 读 character[type] 但数据在 physical→金爷红 (AI-ML) — 内测前
- #7 Seedream 融合鱼草+自然度洗白 (AI-ML, 像素+90分校准为视觉中等, 8/22 同框 shot) — 内测前
- #6 ShotValidator 非人类计数 0 (AI-ML/Backend, #7 是成因, +73%成本/时间) — 联动#7
- #8 BGM 默认 human (P3) — 内测后

**派活 (Founder 全派内测前, 并行无冲突)**: Backend Opus default #4 (孤立文件) ‖ AI-ML Opus xhigh #5/#6/#7 (非人类消费层专项, 一 agent 连贯避免撞文件) → Tester Sonnet high 回归 (角色一致性+人类不退化+Wave13不退化)。

**进度**: ✅ Backend(#4) + AI-ML(#5/#6/#7) 已完成并通过 PM 地毯式审查（追调用链+亲跑回归 db_retry 21+AI-ML域 499 passed+越权+Ben维度）。AI-ML 补挖出 **#5a 锚点层**（identity_anchor_prompts，比回溯点的 builder 更关键）。Ben 维度: test29 改动零前端/契约表面、不碰 DB 边界，但 **#4 是 DB-infra→部署前需知会 Ben**。
**待办**: ⏳ #5/#7 视觉真证需 Founder e2e 复测(test30)最终验收 → 通过后 commit+部署(连同 Wave13, 知会 Ben)。⚠️ Wave 13+test29 全未 commit, 叠加工作区, 禁 destructive git。

---

## (历史) Wave 13 集成关口 — PM 地毯式审查 ✅ 全绿无 blocker (5/25, DEC-052)
> **状态**: 🟢 Wave 13 FIXBATCH 代码全审查通过, 待 Tester 第二道 + DevOps 部署

## Wave 13 集成关口 — PM 地毯式审查 ✅ 全绿无 blocker (5/25, DEC-052)

代码全部写完仍在工作区未 commit (HEAD=68e4211)。PM 5+1 Ben 协议 + 完整调用栈审查全部改动:

| 项 | 文件 | verdict |
|---|---|---|
| #5d MySQL retry middleware | db_retry.py(新)+main.py+database.py | ✅ 4 重约束代码可证 (transient-only/幂等GET/限1次/不掩盖真错误) |
| #6 regenerate-portrait 异步 | api/projects.py | ✅ §9.7.4 三方契约逐字段对齐 |
| #5e clothing 旁路防崩 | character_designer.py | ✅ 崩溃点 (design L144 在 fallback 外) 消除, 0 删 fallback |
| #4A 确认流程超时守卫 | CreateContent.tsx | ✅ inConfirmationFlow 自动重试 8s×3 |
| #4B 后台按钮守卫 | StageC.tsx | ✅ scenesConfirmed 单信号 |
| #5 404 真根因 | layout.tsx | ✅ 模板字符串吃反斜杠, 纯字符串源码层根治 |
| #6 reroll 异步轮询 | StageC.tsx | ✅ 复用 pollCharacterJob helper |
| #9 vitest 基建 | vitest.config/setup+package+useETA.test | ✅ console.assert override throw |
| #5b schema 5 type | 0 代码改动 | ✅ 核实可信 |

**关键调用栈验证 (非 grep 反推)**:
- #5d: `_is_transient_connection_error` 走完整异常链, main.py wire 顺序 CORS 最外层正确
- #5e: design() LLM fallback try/except L99-134, `_validate_characters` L144 调在 fallback **外** → 放宽前非穿衣 type 残缺 clothing raise 冲垮 pipeline; 放宽后 char_type_val 默认 human 走严格, 非穿衣 7 type 降 warning → 崩溃点消除
- #6: POST 202 {success,job_id,status,char_id,message} ⟺ Frontend kickoff; GET job result {success,char_id,portrait_url,fullbody_url,message} ⟺ Frontend result.X; kind="regenerate_portrait" ⟺ CharacterJob.kind — 四者逐字段一致

**待办**:
1. ⏳ Tester 第二道 (pytest 30+vitest 15+回归0退化+独立核对§9.7.4) → 双绿
2. ⏳ DevOps commit 3 组 + push + VPS 第 5 次部署 (见 PENDING; layout.tsx 须 rebuild+硬刷新)
3. 📌 PM 更新 memory `project_schema_humanoid_fallback_remaining` (physical 已根治, #5b 核实)

文档已更: DECISIONS DEC-052 / PENDING / TODAY_FOCUS / checklist / TEAM_CHAT / pm-progress 三件套

---
（以下为规划阶段历史）

## Wave 13 内测前 FIXBATCH (5/25, Founder 批准除#8全修)

### test28 e2e 完成 + 全维度回溯 (Wave 12 修复全验证)
- test28《午夜钟魂》gothic+object/灵魂: gothic画风修复✅ + adjust异步✅ + 3:4✅ + 20shots✅
- 回溯详见 analysis/TEST28_FULL_RETROSPECTIVE_2026-05-25.md + 清单 handoffs/INTERNAL_BETA_READINESS_CHECKLIST_2026-05-25.md
- 🔑 同源洞察: P2-1性能 + MySQL idle 都是本地公网MySQL(333ms), 生产VPS内网改善
- 新 skill: full-retrospective

### 4 波规划 (11 项除#8)
| Wave | 任务 | 负责 | 状态 |
|---|---|---|---|
| 1 | #1 Wave12复测 + #5b schema 5type核实 | Tester + AI-ML | ⏳ 待 Founder 确认 spawn |
| 2 | #2 VPS部署+DB迁移+实测基线 | DevOps | ⏳ |
| 3 | #3 hydrate聚合 + #5d MySQL retry + #6 regenerate异步 (Backend) / #4 UX + #5 404 + #9 vitest (Frontend) | Backend + Frontend | ⏳ |
| 4 | #10 CLAUDE.md git add + #10b test25 + e2e收官 | PM + Founder | ⏳ |

副作用: #5d retry 直接改(无副作用) / #3 合并端点严格测(有回归风险) / #7 安全组 Founder 有权限待查

---
（以下为 Wave 12 历史）

## Wave 12 FIXBATCH (5/24 22:30, Founder 批准)

## Wave 12 FIXBATCH (5/24 22:30, Founder 批准)

### test26《深夜小七》(cyberpunk + ai_entity) 全程跑通 + 全维度回溯
- ✅ Pipeline 1-6 全过, 24/24 shots, ShotValidator 24 PASS/0 FAIL, Layer 1 ABC 四象限收官
- 回溯挖出 8 问题 (详见 .team-brain/analysis/TEST26_FULL_RETROSPECTIVE_2026-05-24.md + STYLE_ANTI_ANIME_FORBIDDEN_GAP_2026-05-24.md)

### 派工 (文件零冲突)
| 任务 | 负责 | 模型 | Wave | 状态 |
|---|---|---|---|---|
| P1 style 画风漂移系统评估+分层修复 (style_enforcer.py) | AI-ML | Opus 4.7 xhigh | A | ✅ 审查通过 (只动3style/实测校准/275回归) |
| P2-1 adjust 异步化 + P2-2 sub-progress (api/projects+pipeline_orchestrator) | Backend | Opus 4.7 xhigh | A | ✅ 审查通过 (fallback真保留/15测试/Ben gap PM代补§9.7) |
| 前端跟进 (adjust loading+ETA插值+P3) | Frontend | Opus 4.7 xhigh | B | ✅ 审查通过 (契约三方对齐/ETA插值逻辑正确/越权0/tsc0) |
| 跨 style + adjust/ETA 复测 | Tester | Sonnet 4.6 high | C | ⏳ 待 PM 先重启 backend (52534=旧代码) |

### Wave B 审查 + Wave 12 收尾 (23:50)
- Frontend ✅: adjust 轮询三方契约对齐 + ETA 插值逻辑人工审查正确 (测试跑不了用代码审查替代)
- 🟡 useETA.test.ts 项目无 vitest (pre-existing), 记 P3 前端测试框架缺失
- ⏳ Wave C 前置: 本地 backend PID 52534 (17:03) = Wave 12 前旧代码, Tester 复测前 PM 须重启加载

### Wave A 审查结论 (23:00)
- AI-ML ✅ + Backend ✅ 地毯式通过 (代码层验证 fallback 非注释 + sub-progress per-char + 实测图 + 回归)
- Ben 维度: 共享DB边界✅ + frontend-impact✅, 🟡 DEC-030 adjust-jobs 契约 PM 代补 STATUS_API_CONTRACT v1.6 §9.7
- AI-ML 实测校准纸面: pastel_dream🟡→🔴上调 / ink·watercolor·ukiyo_e🔴→🟢下调 (介质锚点已守住)

协作点: adjust 异步契约 + progress 数据格式, PM 协调 (Backend 先定 Frontend 跟)。
不在本轮: MySQL 2003 (Ben 安全组) / Invalid HTTP + Server Action x (良性)。

---
（以下为 Wave 11 历史）

## Wave 11 收尾计划 (5/24)

## Wave 11 收尾计划 (5/24)

### 阶段 1: 清 P3 代码 ✅
- Step 1 ✅ DEC-051 fallback 红线 CLAUDE.md 15-A (17b6e28)
- Step 2 ✅ MySQL pool (3b8956b no-op 诊断, Wave 4 已配, VPS 部署修复)
- Step 3 ✅ LP image LCP priority (648b81c, Showcase.tsx surgical)
### 阶段 2: ✅ VPS 第 3 次部署 (5234707, c570c2d → 648b81c)
- PM 6 维度地毯式审查通过 (含亲自 SSH VPS 独立复核 md5 100% 一致 + Ben 提醒逐条 + Wave10 const 8 + pool 3)
- 🟡 唯一发现: DevOps completed.md 漏更, PM 代补归档
- 5/23 MySQL 500 修复 (VPS pool_pre_ping 升级到位)
### 阶段 3: 🟡 等 Founder — test26 e2e (cyberpunk ABC 收官, 服务最新不需重启只拉监控) + spot-check test25/26/27 + 内测启动

### DEC-051 karpathy-guidelines 评估裁决 (5/24)
- 不引入独立 skill (85% 已覆盖 + ETH 实验无提升)
- 全局 CLAUDE.md 5/24 已加 Simplicity + Surgical 保留
- 唯一补强 15-A fallback 红线 (禁 agent 借简化删 LLMFallbackChain/T20-14/ShotValidator/Layer1 兜底)
- ⚠️ 发现 CLAUDE.md untracked (本地生效但没进 git, pre-existing 状态, 待 Founder 决定是否 git add)

---

## (历史) Wave 10 全完成 (5/23 14:30-17:30)
> **下一步**: Founder 决策 — L-3/L-4 跑 test25/26 + spot-check test27 / DevOps 第 3 次部署 Wave 10 / 内测启动

## Wave 10 全完成 (5/23 14:30-17:30)

### Founder 5/23 14:30 决策: P0 现在做 + P2 + P3 + L 都要做不要遗漏

### 派工 + 完成 (~3h)

| 任务 | Agent / 模型 | commit | 结果 |
|---|---|---|---|
| 🔴 P0 Gemini key rotation | PM 自做 (5 min) | 0ad9beb (前置 secret scanner) + .env sed | md5 verify + API 200 + backend 重启 PID 54357 ✅ |
| 🟡 P2-1 test isolation | Tester Sonnet 4.6 effort high | e938eaa | mock pollution + outdated tests 修, 44 PASS (27 errors → 0) |
| 🟡 P2-2 Stage 5 portrait/fullbody | AI-ML (合并 commit) | 3faf585 | verify = **by-design** (RIM smart selection based on shot_type) |
| 🟢 P3-1 UNKNOWN warn | AI-ML + Backend 接力 | 3faf585 + 28e33a7 | CHARACTER_FIELD_PRESERVATION_RULES 4461 chars + deep-merge wire |
| 🟢 P3-2 storyboard aspect_ratio | AI-ML + Backend 接力 | 3faf585 + 28e33a7 | ASPECT_RATIO_FIDELITY_RULES + project_aspect_ratio 11 occurrence |
| 🟢 P3-3 RIM logger 统一 xuhua | AI-ML | 3faf585 | reference_image_manager.py L25 + L873 |
| 🟢 P3-4 chars=N/M Seedream | AI-ML | 3faf585 | CHARACTER_COUNT_FIDELITY_RULES 3207 chars (禁矛盾措辞) |
| 🟢 P3-5 missing_props prompt | AI-ML | 3faf585 | KEY_PROPS_CONSTRAINT_RULES 2718 chars (MAX 3 props × 50 char) |
| 🔮 L-1 DEC-050 finalize | PM 自做 | 0204b8c | SECRET_HANDLING_PROTOCOL 5 部分 |
| 🔮 L-2 mysql memory verify | PM 自做 | 0204b8c | 已用阿里云 MySQL, memory 标 ✅ 已完成 |
| 🔮 L-3 跑 test25 + test26 | Founder 自做 | - | 🟡 等 Founder |
| 🔮 L-4 视觉 spot-check test27 | Founder 自做 | - | 🟡 等 Founder |

### PM 11 维度地毯式审查 (5/23 17:30) ✅

按 memory feedback_carpet_review_deep_dive + feedback_trace_full_callstack_not_pattern + Ben 协议 5+1:
- A commit metadata + B Ben 协议 5+1 + C+D code diff + E PM 自跑 pytest 138 PASS (用 venv 修正后) + F 5 层调用链路 (4 const → import → 拼接 / project_aspect_ratio 11 occurrence / merged_char 12 occurrence) + G+H KEY_LEARNINGS+DECISIONS + I progress 三件套全更新 (5/23 17:07-17:21) + J 0 越权
- 🟡 1 小问题: Tester e938eaa 缺 [frontend-impact:] label (tests/ 不在 watched files, 非违规但建议补)

### PM 自己今日失误 (Wave 10 期间) — 永久教训

1. **PM 自跑 pytest 用 system python** (没 fastapi) 误判 Tester 失败 — 必须用 `venv/bin/python3 -m pytest`, 否则触发 ModuleNotFoundError
2. **PENDING + TODAY_FOCUS + PM progress** 多次没及时更新 (Founder 5+ 次提醒) — 每个 spawn 后立即更新

## 今日全程战果汇总 (5/22 + 5/23)

### 5/22 (16h+)
- 早间 08:30-12:35: Layer 1 全闭环
- 中午-下午 12:35-15:17: Wave 7+8 6 task 全修
- 傍晚 15:30-16:55: e2e test22 Round 2 + VPS 部署 + 同步 verify
- 17:00-18:50: P0 SECRET-LEAK + filter-repo 灾难
- 19:00-19:45: Wave 9 重做 + Wave 9.1 + Tester
- 19:45-19:50: DevOps 第 2 次部署 (PM 代做)
- 19:50-20:01: 清理监控 + 重启服务 + Fresh 监控
- 20:05-20:59: e2e test27 (53 min, ink + 浪漫 + 3:4) — Wave 7+8+9+9.1 15+ 项实战 verify
- 20:18: 🚨 Google 主动 revoke Gemini key, Pipeline 自动 fallback Claude

### 5/23 (~3h)
- 14:00-14:30: PM 全维度回溯文档 (12 章节)
- 14:30-14:35: Founder 决策 + 提供新 Gemini key + 模型升级建议
- 14:35-16:35: PM 自做 key rotation + secret scanner + commit + push (3 commit)
- 16:35-17:30: Wave 10 spawn 4 域并行 (AI-ML Opus 4.7 + Tester Sonnet 4.6 + Backend Sonnet 4.6 接力 + PM 自做 L-1+L-2) — 4 commit

### 累计 commit chain (今日 10 commit)
```
d02e14b  docs(Wave9): audit + gitleaks + 故事 idea
4e4a4cf  docs(test27+retrospective): test25-27 + PENDING + 5/22 全天回溯
0ad9beb  feat(secret-scanner): pre-commit hook Layer 0 (Wave 10 P0)
3faf585  fix(Wave10-AI-ML): 6 项 P2-2 + P3-1/2/3/4/5
e938eaa  fix(test-isolation): T22-NEW-1 修 test_status_authoritative
28e33a7  fix(Wave10-backend): wire P3-1+P3-2 接力 AI-ML 3faf585
0204b8c  docs(Wave10): DEC-050 finalize + L-2 mysql memory verify
```

GitHub HEAD = local HEAD = 0204b8c

## 剩余 (Founder 决策)

1. L-3 跑 test25 (manga + supernatural 银发狐妖) + test26 (cyberpunk + ai_entity 出租车 AI) e2e
2. L-4 视觉 spot-check test27 31 shots + ink 古风 BGM
3. (可选) DevOps 第 3 次部署 Wave 10 到 VPS (AI-ML 3faf585 + Backend 28e33a7 改了 app/ 需 rebuild)
4. CLAUDE.md L210/L241/L283 "传入仅 fullbody" → "smart selection" (Founder 改, AI-ML P2-2 verify 发现)
