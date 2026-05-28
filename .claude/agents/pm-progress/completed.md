# PM Agent - 已完成任务

> 按时间倒序记录已完成的工作

---

## 2026-05-28 整轮 (06:00-18:00) — test30 e2e + dev/prod parity 4 处 P0 + Portrait 重生 deep dive + 性能 P0 闭环

**Pipeline 整轮 e2e**: 3840.2s (~64min) 全跑通《灯笼与萤火》, 20 shot + 5 scene_ref + BGM (Mureka ink 176s) + 3 portrait + 3 fullbody 全落盘。

**Dev/Prod Parity 4 处 P0 全修** (PM 派 + 自己 sed + Founder sudo):
- P0-2 SKIP_IMAGE_GENERATION=true (06:20)
- P0-3 ARK_API_KEY 完全缺失 (06:45) — Seedream API HTTP 400 鉴权层通过实证
- P0-4 IMAGE_GEN_PROVIDER + PROMPT_FORMAT parity (06:45)
- P0-5 Nginx 缺 location /static/ (07:12, Founder su - root + sudo cp + nginx -t + reload)

**Portrait 重生 Explore very-thorough 5 维度深审**:
- 锁定真根因 = Adjust endpoint L1557 真传 portrait_ref + Haiku LLM 改 description 丢失"一群" + Seedream prompt 缺群体 token 强化 (multi-layer collaboration)
- 副线 bug: Regenerate-portrait L1852 没传 portrait_ref (Wave 13 #6 异步化漏修)

**派活 3 agent 并行 + Frontend 二次 Plan A++ progressive 修复**:
- Backend (Sonnet 4.6 high, Opus 4.7 529 重派): 5 项 (#5/#8/#9/#10/#13), pytest 205 PASS
- AI-ML (Sonnet 4.6 high): 2 项 (CFP-3 + GROUP COMPOSITION), PM 跑 pytest 22 PASS
- Frontend 一轮 (Sonnet 4.6 high): 4 项 (Shot type + StageD prefetch + SceneRefs prefetch + fixImageUrl), vitest 15/15
- Frontend 二轮 (Plan A++): StageD progressive useEffect L40-110 + 5 vitest 新 case, total 20/20

**PM 地毯式审查**:
- 第一轮 12 维度全 PASS
- Founder 提醒后第二轮发现 4 真问题: Plan B 实情 / WebP fallback / dead column / STATUS_API_CONTRACT scope
- Founder 选 Plan A++ progressive
- 第三轮 (Founder 再次提醒) 发现 Backend scene_ref thumb URL wire 漏接, 已进 PENDING P1 followup (DevOps 部署时同批)

**完整文档收口** (5/28 17:55):
- `analysis/TEST30_FULL_RETROSPECTIVE_2026-05-28.md` 8000 字完整深度回溯 (15 个问题 5 批次)
- `PENDING.md` 顶部 3 批次完整 + scene_ref thumb wire P1 followup
- `DECISIONS.md` DEC-055 Canonical 11 维度 Parity + Deploy SOP
- `.team-brain/sops/DEPLOY_PARITY_CHECK.md` 11 维度强制 checklist (新建)
- 4 个 memory 新增 + MEMORY.md 索引
- TEAM_CHAT 各方追加完整
- PM/Backend/AI-ML/Frontend progress 三件套 (AI-ML 沙箱限制 PM 代补)

**待 DevOps 部署** (Founder 下班, 之后做):
- commit + push GitHub (按 scope 分 4-5 组, 含 scene_ref thumb wire 补)
- rsync app/ + frontend/ 到 VPS
- VPS docker compose rebuild api + frontend
- 验证 dry-run e2e

---

## 2026-05-28 — VPS test30 portrait 全失败 → 根因 .env SKIP_IMAGE_GENERATION 误开 → 修复

- **现象**: Founder VPS 真机 test30《灯笼与萤火》/characters 三角色全失败, Pipeline `generate_images=True` 但 0 portrait/Seedream call。
- **铁律 5 维度根因核实** (Founder /xhteam 提醒"地毯式深审 + Ben 维度才能 go"):
  1. 容器 ACTUAL 代码 (本地源 + 容器 sed 双证) `pipeline_orchestrator.py:598` gate
  2. 完整调用链: .env=true → settings=True → gate False → portrait 块 silent skip
  3. 历史: VPS a3966a40-* 有 portrait/shot png, SKIP 非一直 True, 某时点被改; **PM 盲区透明承认**: test29 后看到 VPS 仅 1 output 目录归因 local-origin, 没追"为什么 36 项目只 1 个有图"——那时该挖到 SKIP
  4. .env 无其他 kill switch (TEXT_ONLY/MOCK 排查全空)
  5. Ben 维度: 不涉契约/DB/公网/DB-infra, Founder 决策暂不通知
- **修复**: 备份 + sed `true→false` + `docker compose up -d --force-recreate api` → settings.SKIP=False + /api/health 200 + 三容器健康 ✅
- **待 Founder 重发新 test30** 才能真生图 (e48baa8a 项目废弃: API 重启 in-memory 丢 + portrait 窗口过)。生图开销 ~$0.78/短篇 恢复。
- **方法论收获**: dashboard/output 数量背离 = 立即追"是什么开关让 VPS 不生图", 不止停"项目归属"层。.env.production 不入 git 但 .env.production.bak-* 备份留底有价值。

---

## 2026-05-27 — BGM #8 路径B 审查 + #9 docker-compose 清理 (xhteam 轮)

- **#9 docker-compose mysql 残留删除**: 向 Founder 通俗解释 Ben知会内容 + 校准"哑雷"措辞(实际低风险) → Ben 确认 → DevOps 删(83a576b)+VPS同步 → PM 独立核实 0 mysql+容器健康。完成。
- **#8 BGM 升级内测前 + 路径B 决策**: Founder 问"通用性全面深度考量复杂吗" → PM 看代码后判断: 深度通用性反指向**简化/克制(路径B: 信号去人类中心+文化识别)**, 非堆 19×95 type规则(路径A无底洞)。锁进 task#8+DEC-053+PENDING。Founder 升级内测前 → 派 AI-ML(Opus xhigh)。
- **PM 地毯式审查 BGM #8 通过**: 追调用链(_detect_chinese_cultural 非死代码)+ 亲跑 395 pytest 0退化 + 亲跑 dry-run(荷塘渡→chinese_traditional/非人类→animal/人类不退化)+ 越权0 + Ben维度(零契约/DB表面)。真听感待 Founder e2e。
- **方法论**: 三次被 Founder 提醒后, 审查铁律 + Ben维度对**部署/运维层**也严格执行 — 独立 VPS 审计闭合部署 gap + 挖出 docker-compose mysql 残留。task 是 session-only, 持久待办进 PENDING。

---

## 2026-05-26 — test29《荷塘渡》e2e + 全维度回溯 + 非人类专项派活审查

- **test29 e2e 全程守护**: 干净重启(restart-monitors skill, 5 Monitor 含浏览器 console)+ 实时监控全 5 阶段, Founder 成片 **90 分**。Wave 13 全修复实测生效 (#5e/#6/#4A/#4B/#5-404/B52/ETA/T17/条漫文字/画幅3:4)。
- **full-retrospective skill 6 步全维度回溯**: `analysis/TEST29_FULL_RETROSPECTIVE_2026-05-26.md`。像素级看图**纠正纸面**: #7 融合从"P1 最毁画面"校准为"真缺陷但视觉中等(水彩柔化, 仅 8/22 同框 shot)"。炸出非人类人类中心假设链 5 缺口。
- **xhteam 派活 + 地毯式审查**: Backend(#4) + AI-ML(#5/#6/#7, 含补挖 #5a 锚点层) 并行修复, PM 追调用链 + 亲跑回归 (db_retry 21 + AI-ML 域 499) + 越权 + **Ben 维度** 审查全过, 0 修复轮次。
- **完成的子任务**: ✅ reroll 异步实测验证 (adjust job+轮询不转圈) / ✅ stale 文档补齐 (TEAM_CHAT/PENDING/PM三件套/PROJECT_STATUS/TODAY_FOCUS, 补 5/23-26 空白)。
- **决策**: Founder B 方案 (信任单测, commit+部署), #8 BGM 内测后, DEC-053 非人类支持。

---

## 2026-05-22 13:25-15:25 — e2e test22 实测 + Wave 7+8 全闭环 (内测启动倒计时)

### e2e test22 美人鱼 (13:25-13:57, 31.5 min)
- Stage 1-5 + Stage 4.5 全跑 (深海之歌：珊瑚的誓言, 21 shots, cost $0.63)
- ⚠️ Stage 6 BGM 失败 (Music Haiku 3 次 retry 全 529, 无 fallback)
- Founder 5 次重要反馈 (砍 R4-2 / SceneRefsPreview UX / fallback 跨 provider / 内测前必修)

### 真**核心发现** (14:00-14:10)
- Founder /preview Shot 2 视觉验证 — 美人鱼变蓝头发人腿
- PM 深查 backend.log 发现 Bug A: 前 3 shot chars=0 (T22-NEW-7 P0)
- Explore agent audit 完成 (542 行)

### Wave 7 (14:25-15:00, Backend Opus 4.7 max + Frontend Sonnet 4.6) ✅
- Backend (321/321 PASS): T22-NEW-7 (chars=0 根因 = ID format mismatch, name_en vs char_id) + T22-NEW-4 (三层 fallback Haiku→Gemini→Sonnet) + T22-NEW-6 (location wire)
- Frontend (20 routes / 0 errors): T22-NEW-2 SceneRefsPreview 智能展示 4 case

### Wave 8 (15:00-15:17, Backend + Frontend Sonnet 4.6 并行) ✅
- Frontend T22-NEW-5 frontend (5 文件 / 20 routes / 0 errors)
- Backend T22-NEW-9 (229 PASS, 19→4 entries 通用 fallback)
- Frontend T22-NEW-8 (0 改动, 已实现 — PM 漏核 memory)
- Backend T22-NEW-5 backend (196/196 PASS, R4-2 wait loop 移除 + STATUS_API_CONTRACT v1.5)

### KEY_LEARNINGS 沉淀 #50-56 (5/22)
- #50 Stage 4 LLM hint 失效
- #51 Founder 通用故事铁律
- #52 importlib 防 silent fail (#47 第 6 次重演)
- #53 PM 漏沉淀 KEY_LEARNINGS 元教训
- #54 派工 model 失效 + L1009 死代码
- #55 AdjustCharacter/BGM 缺 fallback (3 次实证)
- #56 ID format mismatch (T22-NEW-7 根因) + PM 漏核 memory (T22-NEW-8 假阳性)

### PM 10+ 维度地毯式审查 (Founder 6 次提醒)
- 每个 agent 完成后 PM 11-12 维度审查 (pytest 自跑 + 调用链路 + 越权 + Ben 协议 + KEY_LEARNINGS 沉淀核 + 派工 model verify + 多次提醒铁律严守)

### 文档全更
- PENDING cleanup (头部加 COMPLETED 汇总 Wave 1-8)
- PM current.md + completed.md (本文件) + context-for-others.md 全刷新
- TEAM_CHAT 追加 8+ 段 (e2e 全程 + Wave 7+8 派工 + 审查 + 内测路径)
- TODAY_FOCUS + PROJECT_STATUS 全刷
- STATUS_API_CONTRACT v1.4 → v1.5 (Backend Wave 8 升)

### 内测启动剩余 (5/22 15:25)
- 🔄 Tester baseline regression 跑中 (Sonnet 4.6, ~1h)
- 🔮 DevOps 同步部署 Frontend + Backend
- 🔮 e2e 重跑 test22 (Founder 视觉验证 Coral hair 21/21 一致)
- 🔮 Founder 签字 → 内测启动

---

## 2026-05-21 19:00-23:05 — Wave 4.5 + Wave 5 + Wave II + audit + Layer 1 决策

### Wave 4.5 (5/21 21:15-21:50, 35min) ✅
- pipeline_schemas.py L236-268 加 5 type humanoid fallback (aquatic / anthropomorphic_animal / object / plant / insect)
- tests/test_t21_new_2_humanoid_fallback_wave2.py 16/16 PASS
- T21-NEW-1 25/25 + T20-43 26/26 不退化
- PM 9 Layer 地毯式审查全过

### Wave 5 Backend (5/21 19:25-22:30, Opus 4.7 xhigh) ✅
| Task | 改 | 单测 |
|---|---|---|
| T21-NEW-3 P1 | chapters.py restart 重算 progress + ETA | 5/5 |
| T21-NEW-4 P1 | AdjustCharacter + RegeneratePortrait cache-buster ?v={epoch} | 4/4 |
| T21-NEW-5 P2 | "全身参考图" 文案 | 2/2 |
| T21-NEW-7 P0 | Stage 4.5 ~180 行 + R4-3 + 3 endpoint + STATUS_API_CONTRACT v1.4 + DEC-047 + Alembic 006 | 24/24 |
| T21-NEW-6 P1 | sub_progress_callback 4 参数 + ≥5 sub-step | 6/6 |
| 总计 | 9 代码 + 2 文档 + Alembic 006 | 51/51 + 240/240 0 退化 |
- PM 9+10 Layer 地毯式审查全过 (#47 自跑 PASS + #48 调用链路 + #49 字符串 + 语义 + Ben 5/13 + 19 子项验证)

### Alembic 006 (5/21 20:35-20:40) ✅
- revision id 33→22 chars + idempotent try/except 兜底
- alembic upgrade head 成功 (006_t21new7_scene_refs)
- 2 列加 + Backfill 老项目防卡 R4-3

### Wave II Frontend (5/21 22:40 派 Opus 4.7 xhigh) ✅
- 6 文件改 (createUrl + CreateContent + StageC + types + useETA + test)
- SceneRefsPreview 组件 ~370 行 (镜像 characters 对偶设计)
- 14/14 useETA PASS + Next build 20 routes 0 errors

### e2e test22 美人鱼 (5/21 21:30-22:15, 43 min) ✅
- Stage 1-5 + Stage 4.5 全跑通 + BGM 完成
- Founder 全程互动确认 (大纲 / 角色 / 场景 / 重生)
- Stage 4.5 真首次上线验证

### test22 暴露 P0 通用性灾难 — T22-NEW-3 🚨
- Shot 9-14 珊瑚 hair_color 完全不一致 (schema sea-green / portrait 粉红 / shot prompt dark)
- 深挖根因: storyboard_prompts.py L904 "建议性 hint" 被 LLM 完全自由发挥
- 20/20 shot 真 0 个用对珊瑚 sea-green hair (100% miss!)
- 不止 hair_color, 不止珊瑚, 不止美人鱼 — 跨 19 character_types × 80+ styles × 任意题材
- Founder 决策 (22:55): 选 Layer 1 长期架构治本 (Identity Anchor Framework v1.0), 不走 hotfix
- 接受内测延后 1-2 day

### 地毯式历史 bug audit (Explore Sonnet, 22:00-22:07) ✅
- 报告: `.team-brain/analysis/SESSION_FULL_BUG_AUDIT_2026-05-21.md` (411 行 / 22 KB / 3152 字)
- 总 78 bug, 当前未修 P0 = 1 (T22-NEW-3)
- "修了一半"循环累计 7 次 + PM 审查漏抓累计 4 次
- 根因 Pattern Top 3 分析

### 8 文档第1批补救 (5/21 23:05) ✅
- PM current / completed (本文件) / context-for-others 全刷新
- TEAM_CHAT 追加 Wave II + audit + Layer 1 决策段
- TODAY_FOCUS / PROJECT_STATUS 全面刷新
- DECISIONS 加 DEC-048 Layer 1
- KEY_LEARNINGS 加 #50 + #51

---

## 2026-05-20 17:20-19:41 — TASK-T20-FIXBATCH-4 Wave 1+2+Round 3 全闭环

### 11 个 task 全闭环 (~2.5h)
- T20-43/44/45/46/47/47-fix/48/49/50/50b/50-fix-2 + Wave 2 全设计

### test20 e2e 4 大胜利 (新 project c1b64961, 5/20 18:37-19:07)
- ✅ T20-50 老刘绿色制服 portrait 真信任不覆盖
- ✅ T20-46 illustration 风格 3 角色统一
- ✅ T20-48 无 anatomy hallucination (4 hands 修)
- ✅ 3:4 画幅真生效 (20 shots 全 1664×2218)

### Backend 87388 重启 + Round 3 真生效 (SONNET_MODEL + save_all_references)

### Wave 3 派工 (19:50)
- T20-51 / T20-52 / T20-53 (3 P3 long-tail, Sonnet 4.6 xhigh)

### Wave 4 (20:30-21:01) ✅
- T21-NEW-1 闭环: pipeline_schemas.py L226-252 8 type humanoid fallback + 25 PASS + T20-43 不退化 + 9 Layer 全过

### KEY_LEARNINGS 沉淀 #44-49

---

## 2026-05-19 14:41-17:50 — test17 v2 端到端 + TASK-T20-FIXBATCH-4 Wave 1 (8 RISK 7 PASS + Wave 2 spawn)

### test17 v2 端到端实测 (14:41-16:07, ~86 min) ✅
- Pipeline 74.8 min + 重生 4 min, 总 ~86 min
- 20/20 PNG (含 2 张前端"查看并重生")
- ✅ Wave 14 + T20-10 终极闭环 PASS (Founder "动物的感觉对")
- ✅ 失败容错 PASS, BGM 整体感觉很不错
- 11 个新 RISK 发现 (P0×4 + P1×3 + P2×1 + UI + T20-21 重大重构)
- 📄 `.team-brain/analysis/TEST17_V2_FULL_AUDIT_2026-05-19.md` (9 节)

### Founder 16:08 重大决策 (DEC-044)
- 最终产品形态: shots + BGM (无 TTS 无旁白朗读)
- RISK-T20-21 P0 旁白融入 shot, AI-ML Opus 4.7 max thinking

### TASK-T20-FIXBATCH-4 Wave 1 (16:30-17:45) ✅ 7/8 PASS
- ✅ T20-11 P2 重复 fetch (Frontend #1, 真根因 router.replace 在 effect 外)
- ✅ T20-12 P1 60s 倒计时 (Frontend #2 重做, anti-pattern 模式 + ScenePreview 一致)
- ✅ T20-13 P0 status API 3 字段 (Backend, PM 补救 STATUS_API_CONTRACT v1.1)
- ✅ T20-14 P0 Anthropic 退避 (Backend, 429/529/503 + jitter + ERROR 区分)
- ✅ T20-15 P1 React setState (Frontend #1, ScenePreview 真根因)
- ✅ T20-19 P1 wall-clock 720s (Backend, asyncio.wait_for + TimeoutError)
- ✅ UI 文案 旁白→描述 (Frontend #1, StageD + DEC-044 注释)
- ⚠️ T20-21 P0 prompt 层 ✅ Stage 3 wire 待 Wave 2

### Wave 1 暴露 1 重大违规
Backend agent 漏改 STATUS_API_CONTRACT.md 违反 Ben 5/13 铁律. PM 5 维度审查抓出 + 补救升级 v1.1. KEY_LEARNINGS #36 加.

### TASK-T20-FIXBATCH-4 Wave 2 (17:45+) 🔄 跑中
- AI-ML Opus max (沿用 W1 session): T20-17 Shot 10 角色异象
- Backend Opus default: T20-21 wire + T20-9.v3 ETA 全局
- Frontend Sonnet high: T20-9.v3 useETA.ts 真字段

---

## 2026-05-14 20:30-23:30 — Wave 11.4 + Pre-内测 audit + RISK-NEW-1/2 真彻底全闭环 (5 agent / ~3h / 5 RISK + 2 新 RISK)

### Wave 11 收尾 (20:30)
- Backend #3 (Sonnet xhigh): chapters.py L356-367 + schemas/chapter.py L40 actual_elapsed_sec 集成 — 154 单测 PASS
- Frontend #2 接力 (Sonnet xhigh): StageC.tsx L12+L269-295+L988-993 集成 useETA hook — npm build 0 errors

### Wave 11.4 P2 优化 (~21:00-21:30)
- Backend #5 (Sonnet xhigh) T18-A: pipeline_orchestrator.py L1272+L1334 progress per-shot 75 + int(20 * _done / _total_shots) — 19 + 135 PASS
- Backend #6 (Sonnet xhigh) T18-B + T18-D: 新建 .team-brain/analysis/SEEDREAM_LONGTAIL_RESEARCH.md (290 行) + seedream_metrics.py (200 行) + 30 单测 PASS
- ⚠️ **PM 地毯式审查抓出 SeedreamMetrics 死代码** (Wave 1.1 教训!) → reverse #6 → 派 mini Backend 补漏 → seedream_generator.py 6 调用点接通

### Wave 11.4 timeout 改 (22:35)
- Backend mini (Sonnet 4.6): seedream_generator.py L103: 180→210 (Founder 批准 Backend #6 调研建议)

### Pre-内测地毯式 Audit (23:00, PM + Explore agent very-thorough)
- 8 维度地毯式 audit (backend code + frontend code + log + tests + docs + status response + 用户旅程 + 死代码检查)
- 内测就绪度评分: **A (可启动)**
- 找到 3 新 RISK: RISK-NEW-2 (timeout 配置不一致 P2), RISK-NEW-1 (actual_elapsed_sec 死字段 P3), RISK-NEW-3 (alembic 验证 POST_BETA)

### RISK-NEW-1/2 立即修 (23:30, Founder 批准)
- Backend mini (RISK-NEW-2): config.py L33 IMAGE_GENERATION_TIMEOUT 120→210 + seedream_generator.py L103 从 settings 读 — 56 PASS, 0 越权, NB2 路径不影响
- Frontend mini (RISK-NEW-1): useETA.ts + StageC.tsx + CreateContent.tsx **11 消费点** + sanity check (actualElapsedSec >= 30 min → "正在收尾, 请稍候...") — npm build 0 errors, 0 越权

### PM 5 维度地毯式审查 (10 维度全过)

代码改动 + 完整调用链路 (11 消费点 actual_elapsed_sec / 6 调用点 SeedreamMetrics) + py_compile 4 文件 + **207/207 全 regression PASS** + 0 越权 + Backend 重启含 config 改动 + Frontend clean rebuild (修 webpack chunk MODULE_NOT_FOUND) + progress 三件套真更新 + timeout 配置统一 + 死字段彻底消除 + 死代码彻底消除

### 服务管理

- 21:00 Frontend hot reload MODULE_NOT_FOUND → KEY_LEARNINGS #7 标准 clean rebuild → 新 PID 78392 ✅
- 21:02 Founder 决定明天再测 → 服务全停 (kill 78277 + 78392) → 0 残留 + ports free

### task list 最终状态

```
✅ Completed (12): #1/#2/#3/#4/#5/#6/#9/#10/#11/#12/#15/#16
⏳ POST_BETA (4): #7 T17-7 / #8 T17-1 / #13 T18-I / #14 T18-J
```

### 文档闭环

| 文档 | 更新 |
|---|---|
| pm-progress/current.md | ✅ 5/14 21:05 含 Wave 11.4 + audit + RISK-NEW + 服务停 |
| pm-progress/completed.md | ✅ 本段 |
| pm-progress/context-for-others.md | ✅ 最终状态 16 RISK 看板 |
| .team-brain/TEAM_CHAT.md | ✅ Wave 11 真彻底闭环段 (5/14 20:00-23:30 全段) |
| .team-brain/handoffs/PENDING.md | ✅ 12 RISK 战果总览 |
| .team-brain/decisions/DECISIONS.md | ✅ DEC-033 (timeout 统一 + actual_elapsed_sec 消费) |
| .team-brain/knowledge/KEY_LEARNINGS.md | ✅ Wave 11.x 5 条新经验 |
| .team-brain/status/TODAY_FOCUS.md | ✅ 5/14 完整时间线 (含 22:00 死代码补漏 + 23:30 RISK-NEW) |
| .team-brain/analysis/WAVE11_PLAN_AND_POST_BETA_RISKS.md | ✅ Wave 11.x 全标完成 |
| .team-brain/analysis/SEEDREAM_LONGTAIL_RESEARCH.md | ✅ (Backend #6 290 行调研) |
| backend-progress 三件套 | ✅ agent 自更 (5/14 20:54) |
| frontend-progress 三件套 | ✅ agent 自更 (5/14 20:57) |

---

## 2026-05-14 16:40-19:30 — Wave 11.1 + 11.2 + 11.3 三波 RISK 修复 (4 agent / ~3h / 5 RISK)

### Wave 11.1 (16:40-17:30, ~50 min, P0+P1)

| RISK | 文件 | Backend agent | 验证 |
|---|---|---|---|
| 🔴 T18-F P0 角色一致性 (Shot 重生) | `app/api/chapters.py` L1878-1890 | #1 Sonnet 4.6 | ✅ |
| 🔴 T17-9 P0 角色一致性 (R7-3) | `app/api/projects.py` L1288-1309 | #1 (顺序) | ✅ |
| 🟡 T18-H P1 ShotValidator 5MB | `app/services/shot_validator.py` L37-89/L304/L461-474 | #2 (并行) | ✅ |

**测试**: 103+9 单测 + 82 regression PASS + 0 越权 + Backend 重启含改动
**PM 5 维度审查**: 代码改动 / 调用链路追踪 / py_compile / pytest / 0 越权 / Backend 重启 / progress 三件套 / character_consistency_regression — 全过

### Wave 11.2 (17:35-19:30, ~2h, P1 数据契约)

| RISK | 文件 | Agent | 验证 |
|---|---|---|---|
| 🔴 T18-G P1 404 风暴 41 次 | `app/api/chapters.py` L415-446 + L568-574 | Backend #1 Sonnet xhigh | ✅ |
| 🔴 T18-E P1 /preview API 空 | `app/api/projects.py` L1556-1660 (新增 endpoint) | Backend #1 (顺序) | ✅ |
| T18-G 配套 | `frontend/src/lib/api.ts` + StageC.tsx + CreateContent.tsx | Frontend #1 Sonnet xhigh | ✅ |

**Backend**: 22 新单测 + 134 regression PASS + 0 越权
**Frontend**: npm build 0 errors / 20 routes
**修复**: 404 → 200+empty (避免 client error log 风暴) + 新 preview endpoint 真注册 (含 project + chapters + shots + characters + bgm 完整数据) + StageC charPreviewFetchingRef guard 防 2s poller 重复 fetch + silentStatuses 静默处理 hydration 404

### Wave 11.3 (17:35-17:50, ~1h, P1 ETA)

| RISK | 文件 | Agent | 验证 |
|---|---|---|---|
| 🟡 T17-5 P1 ETA backend | `app/services/job_manager.py` L18-148 + L375-395 + L411-428 | Backend #2 Sonnet xhigh | ✅ |
| T17-5 配套 (frontend) | `frontend/src/hooks/useETA.ts` (新建 170 行) + CreateContent.tsx L1409-1428 | Frontend #2 Sonnet xhigh | ✅ 部分 |

**Backend**: 50 单测 + architecture regression 7/7 PASS + 0 越权
**Frontend**: useETA hook 创建 + npm build 0 errors
**主根因修复**: `_last_eta` 单调 guard 在 stage 切换时 reset (之前从不 reset → image_preparation 末尾低 ETA 截断 image_generation 开始高 ETA → "前面1分钟/后面8分钟"跳变)

### 中间事件 + 服务管理

- **17:13 Frontend hot reload 500 修复**: PID 55281/55282 chunk 累积 → PM clean rebuild (KEY_LEARNINGS #7) → 新 PID 73076/73077 ✅ HTTP 200
- **17:38 Backend 重启含 Wave 11.2 改动**: 老 PID 70144 → 新 PID 73152, GET preview 404 "项目不存在" 验证 endpoint 真注册
- **17:30+ 服务全停 (Founder 回家)**: Backend + Frontend + 4 Monitor (b03o55njd, b1aswkh7i, b11fp6b1x, b2ho8xguj) 全 stop, ports 8000+3000 释放

### 待 PM 收尾 (Founder 回家后继续)

1. PM 5 维度审查 4 agent (Wave 11.2 + 11.3) — backend agent 已 paste 给 PM 代写, PM 审查后标 task completed
2. 派 Backend #3 mini agent 集成 ETA 字段到 chapters.py status response (Backend #2 paste 的 snippet)
3. 派 Frontend #2 接力 StageC.tsx 集成 useETA hook
4. 标 task #11/#1/#2 completed
5. Wave 11.4 派活时机决策 (T18-A + T18-B + T18-D, 估 3-4h)

---

## 2026-05-14 14:38-16:35 — test18 e2e + Wave 10/10.1 实证 + 14 RISK 地毯式 audit + Wave 11 派活计划

### test18 全程 (14:38-15:57, 73 min 含交互)

- ✅ Pipeline 完整跑通 2908s (48.5 min)
- ✅ 角色 3, 场景 12, 镜头 29
- ✅ 失败率 1/29 = 3.4% (Shot 8 TimeoutError 4-attempt)
- ✅ 用户级容错 (Founder 重生 Shot 8 48s 一次成功)
- ✅ 总成本 ~$1.53

### Wave 10 + Wave 10.1 全实证

| 修复 | 实证 |
|---|---|
| T16-4 B58 merge | ✅ "merged=12 保留 action_beats 等 LLM 字段" |
| T17-6 atmosphere dict (Wave 10.1 hotfix) | ✅✅✅ Stage 4 11 LLM 并行 0 TypeError (test17 死在这里, test18 飞过) |
| T14-10 真并行 Sem(3) | ✅✅✅ 3 dispatch 同毫秒 (15:24:44.783/.783/.822) |
| T16-5 storyboard_ready 严格判 | ✅ ui_phase 切换正确 |

### 14 RISK 地毯式 audit (PM + Explore agent very-thorough)

5 维度: backend log + frontend log + 代码 + TEAM_CHAT + 用户旅程

**新发现 4 条 PM 漏检**:
- 🔴 T18-G P1 /chapters 404 风暴 41 次 (PM 自核 backend log)
- 🟡 T18-H P1 (升级) ShotValidator 5MB 直接跳过 (隐藏失效)
- 🟢 T18-I P3 Seedream IncompleteRead 24 次 (vs PM 估 5 次)
- 🟢 T18-J P3 (降级) Sync LLM 阻塞 event loop

**完整 audit 报告**: `.team-brain/analysis/TEST16-18_DEEP_AUDIT_2026-05-14.md` (11 段)

### Wave 11 派活计划 (Founder 5/14 16:30 拍板 P0+P1+P2 都做, P3 内测后)

- Wave 11.1 (2h): T18-F + T17-9 + T18-H (Backend × 2 并行)
- Wave 11.2 (1.5h): T18-G + T18-E + StageC 配套
- Wave 11.3 (2h): T17-5 ETA Backend + Frontend
- Wave 11.4 (3-4h): T18-A + T18-B + T18-D

**完整 Wave 11 + POST_BETA**: `.team-brain/analysis/WAVE11_PLAN_AND_POST_BETA_RISKS.md`

### 文档更新

| 文档 | 更新 |
|---|---|
| `pm-progress/current.md` | test18 + audit + Wave 11 计划 |
| `pm-progress/context-for-others.md` | 给 Wave 11 同事 onboarding |
| `pm-progress/completed.md` | 本段 |
| `.team-brain/status/TODAY_FOCUS.md` | 5/14 完整时间线 + 14 RISK 看板 |
| `.team-brain/analysis/TEST16-18_DEEP_AUDIT_2026-05-14.md` | 完整 audit 报告 (新建) |
| `.team-brain/analysis/WAVE11_PLAN_AND_POST_BETA_RISKS.md` | Wave 11 + 防 P3 遗漏 (新建) |
| `.team-brain/handoffs/PENDING.md` | 顶部 Wave 11 + POST_BETA 段 |
| `.team-brain/decisions/DECISIONS.md` | DEC-031 Wave 10.1 hotfix + DEC-032 Wave 11 优先级 |
| `.team-brain/TEAM_CHAT.md` | test17 atmosphere bug + test18 全程 + audit + Wave 11 派活段 |

### 服务状态

- Backend uvicorn PID 63583 (Wave 10.1 含 _atmosphere_to_str hotfix) ✅
- Frontend next-server 健康 ✅
- 4 Monitor: cron 6a1ddaae 已停 (Founder 要求)
- task list: 14 RISK 锁定, #9 已 completed

---

## 2026-05-13 16:30 → 17:30 — Wave 7 全员地毯审查通过 + 文档代写完成

### Wave 7 派活 + 监控 + 救场 + 审查 + 收尾全流程（1h 完成）

| 时刻 | PM 动作 | 产出 |
|---|---|---|
| 16:30 | Founder /xhteam 批准 → PM batch update 6 PM 文档 → spawn 3 agent | Backend / Frontend / AI-ML opus xhigh 并行 |
| 16:55 | Backend R1 完成（25 min vs 预估 3h，pytest 11/11）+ Frontend 完成（25 min vs 预估 2.5h）| PM Explore-Backend 审查发现 Task 3 ETA 死代码 |
| 16:55-17:00 | PM clean rebuild frontend（rm .next/ + restart）解决 vendor-chunks hot reload 失败 + PM 自修 SettingsContent L27-28 null-safe | 5 routes 200 ✅ |
| 17:00 | PM spawn Backend R2 修 Task 3 + Explore-Frontend 审查 | R2 11 min 完成 + Frontend 6 任务全过 |
| 17:08 | Backend R2 完成（pytest 7/7 + dynamic case 单测 3/3 真不同 18/26/concurrent 1/3）| PM verify chapters.py L143-200 真传 3 参数 ✅ |
| 17:13 | AI-ML 完成（43 min vs 4-5h，71/71 单测 + 5/5 Mureka 真测）| PM spawn Explore-AI-ML + Explore-Integration |
| 17:18 | PM Integration Explore 发现 3 处 wiring 死代码 → PM 自修 + 重启 backend PID 38072 | py_compile PASS + HTTP 200 |
| 17:25 | PM 仲裁 Explore 误判（AI-ML 0 越权，被误归到 Backend R1+R2 改的 8 文件）| Wave 7 全员审查通过 |
| 17:30 | Founder 听完 5 组 Mureka mp3 反馈"都非常贴切 我很满意" | Wave 7 BGM 通用性框架实战胜利 |
| 17:30 | PM 收尾代写 5 共享文档 + 3 PM progress + 1 frontend completed | 全文档闭环 |

### 战果对比 vs Wave 6 (test13) + Wave 7 (test14)

| 维度 | test13 (Wave 6) | test14 (Wave 7) |
|---|---|---|
| Pipeline 耗时 | 30 min | 28 min |
| T17 fail rate | 11% (Shot 6) | **0%** ✅ D3 大胜 |
| Backend ERROR | 50+ cascade | **0** ✅ A1 修 |
| Client real error | 14 黑箱 | **0** ✅ A2 全捕 |
| B1 验收点 | 0/6 | **5/6 通过** ✅ |
| BGM 听感 | 西式电影氛围 | **5/5 风格贴切** ✅ Wave 7 修 |
| 总修复条目 | 11 BUG-T13 + 1 基建 | 13 RISK-T14 + 4 DEC |

### Wave 7 完整 RISK 修复表

| RISK | P | 责任 | 状态 |
|---|---|---|---|
| T14-1 | P0 待 | Frontend (mitigation by B1) | ✅ test14 0 setState warning verify 通过 |
| T14-2 | P1 | Frontend | ✅ 4 文件 user?.X + PM 自修 SettingsContent |
| T14-3 | P3 | Frontend | ✅ createUrl.ts dedup |
| T14-4 | P1 | Backend R1+R2 | ✅ dynamic ETA 7 子问题 + 真传 3 参数 |
| T14-5-v2 | P1 | Backend R1 | ✅ Pipeline mid-stage progress update |
| T14-6 | P1 | Frontend | ✅ confirm-chars 直跳 /scenes |
| T14-7 | P0 | Backend R1 | ✅ GET /story endpoint 条件修 |
| T14-8 | P0 | Frontend | ✅ watcher MID_PIPELINE_STAGES 4 stages |
| T14-9 | P1 | Backend R1 | ✅ 不截断 26→18 shots (DEC-028) |
| T14-10 | P1 | Wave 8 Backend | ⏳ 参考图并行化 (DEC-029) |
| T14-11 | **P0** | AI-ML | ✅ BGM 通用性框架 + 5/5 真测 PASS (DEC-026) |
| T14-12 | P1 | Frontend | ✅ 后台生成 + 通知 (DEC-027) |
| T14-13 | P1 | Backend + Frontend | ✅ inconsistency_warnings 结构化 + banner |

### 关键经验（已落 KEY_LEARNINGS）

1. **软提醒 vs 硬约束的分水岭** — LLM 训练数据偏置权重远高于软提醒
2. **中文单字关键词在现代上下文易误匹配** — 用 2+ 字组合词
3. **PM Explore 误判要靠 PM 仲裁** — Wave 多 agent 并行场景特别要按 mtime 精确比对
4. **Integration 集成测试发现 P0 死代码** — "signature 加参数 + 待调用方传新参数"必须分两步派活

### 关键决策（已落 DECISIONS DEC-026/027/028/029）

- DEC-026: BGM 通用性框架（style × mood 矩阵 + 文化硬约束）
- DEC-027: 后台生成 + 完成通知机制
- DEC-028: 不截断 shots
- DEC-029: 参考图阶段并行化（Wave 8 待）

---

## 2026-05-13 15:18 → 16:30 — test14 端到端实测 + 13 RISK-T14-* 整理 + Wave 7 启动

### test14 全程时间线

| 时刻 | 事件 | 状态 |
|---|---|---|
| 15:18 | test14 启动 project 5cbd8ca0 "第三十七局" | - |
| 15:21:39 | Stage 2 CharacterDesigner 完成 | ✅ |
| 15:22-15:24 | 3 角色 portrait 串行（B57 设计 by-design） | ✅ |
| 15:26:34 | Founder adjust 叶无伤"黑衣剑袍" | ✅ B57 工作 |
| 15:30:08 | R4-1 用户确认（B1 watcher auto-jump #1 通过）| ✅ |
| 15:33:44 | Stage 3 ScreenplayWriter 完成 213.2s | ✅ |
| 15:33-15:37 | GET /chapters/1/story 持续 404 — RISK-T14-7 暴露 | 🔴 |
| 15:37:51 | PM curl POST /confirm-scenes 救场 | ✅ |
| 15:41:53 | Stage 4 完成 — 自动截断 26→18 shots — RISK-T14-9 | ⚠️ |
| 15:48:15 | Stage 5 image_preparation 5 anchor 串行完成 | ✅ |
| 15:50:11 | 18 shots image_generation max_concurrent=3 真并行 | ✅ |
| 15:55:01 | **18/18 shots T17 fail 0%（D3 方案 D 大胜 vs test13 11%）** | ✅✅✅ |
| 15:58:00 | Pipeline 完成 28 min（vs test13 30 min）| ✅ |
| 15:58:30 | B1 watcher auto-jump /preview ✅ #2 通过 | ✅ |
| 16:00 | Founder /preview — 18 图 OK + 文字 + 角色一致性 | ✅ |

### PM 5/13 救场 + 监控 + 13 RISK 整理

**PM 干的活**:
1. **idea 文档**: `docs/xuhuastorytest14.md` 古风武侠悬疑
2. **监控**: cron 4b690c00 every 2 min 自检 + 4 monitor 全程跟（5/13 15:21 重 spawn，5/12 老的 22h 前 timeout 死了 PM 没主动 verify — KEY_LEARNING #1）
3. **救场**: RISK-T14-7 暴露 → curl POST /confirm-scenes 解锁 R4-2 + Stage 4 启动
4. **多模态 verify**: Read char_001 portrait + fullbody 看 PM 确认黑衣剑袍质量 ✅
5. **BGM 深挖**: Read `music_generation_service.py` + `story_music_extractor.py` + `meta_mixed_v3_quote_picking.md` (47KB) — 找到真根因（6 桶 mood 不考虑 style_preset）
6. **13 RISK 整理**: 含 PM 自己漏的 RISK-T14-4 ETA 独立 entry + RISK-T14-13 UX-2 warnings + RISK-T14-11 升级通用性框架
7. **5 文档代补**: DECISIONS DEC-026/027/028/029 + KEY_LEARNINGS PM 5/13 7 教训 + TODAY_FOCUS Wave 7 启动 + pm-progress 三件套 + TEAM_CHAT

### 13 RISK-T14-* 全清单（按 P 分组）

#### 🔴 P0（4 个）
- T14-1 React anti-pattern 真根因（test14 mitigation ✅，DevTools 0 真 error）
- **T14-7 GET /chapters/1/story endpoint 条件错** ← test14 真阻塞，PM curl 救场
- **T14-8 B1 watcher 漏监听 storyboard/image_*/bgm 4 stages**
- **T14-11 BGM 通用性框架缺失** ← Founder 5/13 16:09 升级为产品设计层面

#### 🟡 P1（7 个）
- T14-2 5xx 期间 dashboard null reference crash 可能
- T14-4 ETA 7 个 sub-issues
- T14-5-v2 Stage 2/3 backend 不 mid-stage update
- T14-6 confirm-chars 后绕路 /generating
- T14-9 自动截断 26→18 shots（Founder DEC-028 不截断）
- T14-10 参考图阶段并行化（Founder DEC-029）
- T14-12 缺后台生成按钮 + 通知（Founder DEC-027）
- T14-13 UX-2 一致性 warnings 静默丢

#### 🟢 P3（1 个）
- T14-3 createUrl.ts 2 set 重复

### Wave 7 派活（Founder /xhteam 5/13 16:30 启动）

| Agent | 模型 | RISK | 工时 |
|---|---|---|---|
| Backend | sonnet xhigh | T14-7+5-v2+4+9+13-backend (5) | ~3h |
| Frontend | sonnet xhigh | T14-8+6+12+3+2+13-frontend (6) | ~2.5h |
| AI-ML | opus xhigh | T14-11 BGM 框架 + **5 组 Mureka 真测**（Founder 5/13 16:30 决策 5 组够）| ~4-5h |
| Wave 8 Backend | sonnet xhigh | T14-10 参考图并行化 | ~45 min |

---

## 2026-05-12 16:30 → 2026-05-13 14:59 — TASK-T13-FIXBATCH 全闭环（11 P0/P2 + 1 基建一次性合修）

### 派活 + 监督 + 审查 + 收尾全流程

| 阶段 | 时间 | PM 动作 | 产出 |
|---|---|---|---|
| Plan mode 5 步 plan 写入 | 5/12 22:00 | 写 `~/.claude/plans/moonlit-imagining-sunset.md` | 整体收尾 5 步 plan，Founder 批准 |
| 步骤 1 派 Frontend URL fix | 5/12 16:55 | spawn frontend sonnet xhigh 修 layout.tsx hardcoded URL | A2 URL fix 16:37 完成 |
| 步骤 1 PM 二修 /api 约定漂移 | 5/12 17:15 | PM 自审发现 frontend agent 打破 NEXT_PUBLIC_API_URL 含 /api 后缀约定 → 修 3 文件 | 双 /api 路径 404 风险消除，build verify ✅ |
| 步骤 2 派 AI-ML D3 docs | 5/12 22:05 | spawn ai-ml opus xhigh 补 G+H+I（不改代码，方案 D 已批） | T17_VALIDATOR_FIX_ANALYSIS 9 段 + DEC-025 + KEY_LEARNINGS 经验段 + ai-ml-progress |
| 步骤 3 PM 收尾批次 1 文档 | 5/12 17:57 | TEAM_CHAT 追加 5 条 + PENDING 标 7 个 BUG ✅ + backend-progress 三件套代补 + KEY_LEARNINGS 加 NEXT_PUBLIC_API_URL 经验 | ✅ |
| 步骤 4 派 Frontend B1 | 5/12 17:25 | spawn frontend **opus xhigh** TASK-T13-FRONTEND-ROUTING-FAMILY 8 任务 | B1 17:48 完成（22 min 内，比预期 3-4h 快 10 倍）|
| 步骤 5 PM 审查 B1 | 5/12 17:50 | Explore agent very-thorough 审 4 文件 8 任务 → 全 ✅ | Explore 报告：A) 全部接受 |
| 步骤 5 Frontend clean rebuild | 5/12 17:55 | rm .next/ + 重启 npm run dev → 4 routes 全 200 | Frontend HTTP 500 → 200 |
| 步骤 5 PM 代写共享文档 | 5/12 17:57 | TEAM_CHAT 加 B1 完成段 + PM 总结段 | ✅ |
| 步骤 5 拉 4 monitor | 5/12 17:58 | backend errors + frontend errors + client.log + health check | persistent 4 monitor 就绪 |
| **5/13 PM 亲读地毯审查** | 5/13 14:30-14:59 | Read 4 文件全文（AuthContext / CreateContent / StageC / createUrl）追完整调用链 | 发现 3 risk Explore 漏报 |
| 3 risk 标 PENDING | 5/13 14:59 | RISK-T14-1/2/3 加 PENDING.md 头部"Test14 重点观察项" | ✅ |
| pm-progress 三件套补 | 5/13 14:59 | current + context-for-others + completed 全更新到 5/13 | ✅ (本段) |

### 最终战果

**11 P0/P2 + 1 基建 = 12 任务全闭环**

| Bug | P | 责任 agent | 状态 |
|---|---|---|---|
| BUG-T13-MYSQL-STALE-CONNECTION | 🔴 P0 | Backend | ✅ A1 pool_pre_ping + pool_recycle + pool_size + max_overflow |
| BUG-T13-DB-POOL-EXHAUSTION-CASCADE | 🔴 P0 | Backend | ✅ A1 同上 |
| BUG-T13-SCENES-CONFIRM-PATH-MISMATCH | 🔴 P0 | Backend + Frontend | ✅ C1-backend alias + C1-frontend 改调 project-level |
| BUG-T13-UX-2-LLM-JSON-TRUNCATED | 🟡 P2 | Backend | ✅ D1 改用 _llm_helpers.extract_json_from_llm_response |
| BUG-T13-ETA-OVERESTIMATE | 🟡 P2 | Backend | ✅ D2 STAGE_DURATIONS image_generation 420→360 |
| BUG-T13-T17-VALIDATOR-FALLBACK | 🟡 P2 | AI-ML | ✅ 方案 D 4 层防御 + analysis + DEC-025 |
| BUG-T13-CHARACTER-PAGE-NO-AUTO-JUMP | 🔴 P0 | Frontend B1 | ✅ 顶层 watcher 5s 轮询 |
| BUG-T13-URL-PINGPONG-CHARACTER-READY-V2 | 🔴 P0 | Frontend B1 | ✅ createUrl backendPastCharStage guard + charactersConfirmedRef |
| BUG-T13-REACT-ANTIPATTERN-STAGEC | 🔴 P0 | Frontend B1 | ✅ useCallback + useMemo + useEffect (真根因 PM 不 100% 确，等 test14)|
| BUG-T13-COMPLETED-NO-AUTO-JUMP | 🔴 P0 | Frontend B1 | ✅ 顶层 watcher 监听 completed |
| BUG-T13-AUTH-FALSE-LOGOUT-ON-500 | 🔴 P0 | Frontend B1 | ✅ tokenInvalid state + isLoggedIn 算法 + 指数退避 |
| BUG-T13-PREVIEW-DIRECT-LOAD-SLOW | 🔴 P0 | Frontend B1 | ✅ BGM Promise.all 4 路并行 |
| BUG-DASHBOARD-PERF-N1 | 🟡 P1 | Frontend B1 | ✅ 验证已无 N+1 + BGM 并行 |
| TASK-CLIENT-LOG-PIPE | 🔴 P0 基建 | Backend + Frontend + PM | ✅ A2-backend endpoint + A2-frontend 注入 + PM 二修 URL 约定 |

20 文件改动 + 5 文档新建/更新 + 0 越权 + 0 共享文档并发冲突。

### 关键经验沉淀（已写入 KEY_LEARNINGS）

1. **数据契约错配比 prompt 写得差更隐蔽**（AI-ML D3 学到，2026-05-12）— 判断 4 信号 + 4 修复模式 + 5 复盘点
2. **项目命名约定必须 grep 全代码再改 env var**（PM 5/12 学到）— Frontend agent 打破 NEXT_PUBLIC_API_URL 含 /api 后缀约定，build 通过但生产双 /api 404

### 关键决策记录（已写入 DECISIONS）

- DEC-025: T17 ShotValidator 4 层防御（数据契约错配修复，方案 D 自创）— AI-ML 自创越权 + Founder plan mode 批准

### 待 Founder 决策

| 事项 | 状态 |
|---|---|
| test14 e2e 时机 | 等 Founder（PM 不需在场，4 Monitor 自动捕获） |
| Wave 6 部署 | test14 通过后 Founder 决定（之前明确"暂缓"）|

---

## 2026-05-12 13:56-16:30 — test13 端到端实测 + 11 bug 归档 + TASK-T13-FIXBATCH 派活规划

### 监测全过程（13:56-15:53）

- **project**: `70eed512-f747-457d-922f-2b6fa68b9fd5` "九点十二分的守望者"
- **Founder 测试**: Stage A 输入 → outline → 手动 unblock R4-1 / R4-2 → 18 shots Seedream 真生图 → BGM Mureka → /preview 看完故事
- **PM 监测节奏**: cron `bade11eb` 每 2 min 综合检查（共 ~16 次） + 3 monitor 实时捕获（health-loop / backend errors / frontend errors）
- **核心耗时**: 30 min（去 R4-1/R4-2 等待 + curl 救场时间）/ 含等待 58 min
- **总成本**: ~$1.16

### Pipeline 5 stages 实测 + Stage 6 BGM

| Stage | 启动 | 完成 | 耗时 | 备注 |
|---|---|---|---|---|
| 1 Outline | 13:56:43 | 13:59:03 | 137s | Sonnet 4.6 |
| 2 Character | 14:00:34 | 14:02:08 | 92s | 3 角色 Schema 通过 |
| 5 参考图（10 张串行）| 14:02:16 | 14:06:19 | ~4 min | by design 串行 |
| R4-1 character_ready 等待 | 14:06:26 | 14:13:02 | 148s | React infinite loop 副作用 unblock |
| 3 Screenplay | 14:13:18 | 14:17:54 | 276s | 10 场景, 21 action_beats, 3137 字旁白 |
| R4-2 scenes_ready 等待 | 14:18:05 | 14:35:01 | 400s | PM 直接 curl `/chapters/1/confirm-scenes` 救场 |
| 4 Storyboard | 14:35:19 | 14:39:02 | ~4 min | 18 个分镜 Schema 通过 |
| 5 18 shots（max_concurrent=3）| 14:46:15 | 14:55:10 | ~9 min | **三连发铁证**：14:46:15.507/.507/.508 |
| 6 BGM Mureka | 14:55:59 | 14:57:35 | ~95s | Mureka 159s + ffmpeg LUFS check |
| Pipeline 完成 | - | 14:58:20 | 总 3475.9s | summary 写入 |

### 11 个 bug 归档（详见 PENDING `## 🗂️ test13 实测完整 Bug 清单`）

| # | Bug | 严重 | 阶段 |
|---|-----|------|------|
| 1 | BUG-T13-CHARACTER-PAGE-NO-AUTO-JUMP | 🔴 P0 | R4-1 |
| 2 | BUG-T13-URL-PINGPONG-CHARACTER-READY-V2 | 🔴 P0 | R4-1 |
| 3 | BUG-T13-REACT-ANTIPATTERN-STAGEC（StageC.tsx:1181） | 🔴 P0 | R4-1 |
| 4 | BUG-T13-SCENES-CONFIRM-PATH-MISMATCH | 🔴 P0 | R4-2 |
| 5 | BUG-T13-COMPLETED-NO-AUTO-JUMP | 🔴 P0 | 完成后 |
| 6 | BUG-T13-MYSQL-STALE-CONNECTION | 🔴 P0 | idle |
| 7 | BUG-T13-DB-POOL-EXHAUSTION-CASCADE | 🔴 P0 | idle |
| 8 | BUG-T13-AUTH-FALSE-LOGOUT-ON-500 | 🔴 P0 | idle |
| 9 | BUG-T13-PREVIEW-DIRECT-LOAD-SLOW | 🔴 P0 | 完成后 |
| 10 | BUG-T13-UX-2-LLM-JSON-TRUNCATED | 🟡 P2 | Stage B |
| 11 | BUG-T13-ETA-OVERESTIMATE | 🟡 P2 | Stage 5 |
| 12 | BUG-T13-T17-VALIDATOR-FALLBACK | 🟡 P2 | Stage 5 |

加上 **TASK-CLIENT-LOG-PIPE 从 💡 升级到 🔴 P0** + Founder 强制要求"全量捕获不丢不采样" 7 类必覆盖范围（error/warn/onerror/unhandledrejection/React strict/Next hydration/network）。

### 7 重要确认 pass

✅ max_concurrent=3 真生效（同毫秒三连发铁证 14:46:15.507/.507/.508）→ DEC-020 / BP_SUPPLEMENT 第 6 节"M1 实测 4.5min" 不需校准
✅ ARCH-1 修复生效（chapter_scene_images 18/18 写入 14:55:55）
✅ ARCH-4 修复生效（api_cost_logs 18 行写入 + DB tracker query 14:46:08）
✅ BUG-MUREKA-BLOCK-EVENT-LOOP 没复现（轮询 8s 间隔均匀，可降级或归档）
✅ D.15/B39 aspect_ratio 透传（'3:4' 真实 INSERT + 真实传 LLM）
✅ B33 user_selected_mood 强制注入 LLM 约束（'悬疑' 在 GenerateOutline 日志看到）
✅ Seedream 单图 ~$0.030（vs NB2 $0.067 节省 55%）

### 16:30 TASK-T13-FIXBATCH 派活规划（按 ROI + 依赖图）

**批次 1（3 agent 并行 spawn，~1-2h）**:
- @backend (sonnet xhigh) — A1 + A2-backend + D1 + D2 + C1-backend（5 任务顺序处理）
- @frontend (sonnet xhigh) — A2-frontend (layout.tsx 注入 console proxy)
- @ai-ml (opus xhigh) — D3 (T17 调研 + 修复)

**批次 2（A2 完成后 ~3-4h）**:
- @frontend (**opus xhigh**) — B1 (7 P0 同源合修) + C1-frontend (统一调用)

**批次 3（PM 收尾）**:
- PM 独立审查（地毯式调用链路追踪）
- PM 拉 4 个 monitor（含**新增 client log monitor**）
- PM 通知 Founder 手动 e2e 测试（test14）→ 等 Founder 确认 → 收尾

### Founder 5 决策

1. ✅ 整体规划 OK
2. ✅ B1 Opus xhigh
3. ✅ D3 派 AI-ML（"我说了不要放着都要修"）
4. ✅ Wave 5 改 Founder 手动测，PM 拉 monitor
5. ✅ Wave 6 部署暂缓

### 文档更新（5-12 16:30）

- ✅ PENDING.md `## 🗂️ test13 实测完整 Bug 清单` 完整归档
- ✅ TEAM_CHAT 16:00 test13 完成总结 + 16:30 派活通知（@pm 身份）
- ✅ TODAY_FOCUS 顶部更新到 5-12 + 当前 TASK-T13-FIXBATCH
- ✅ pm-progress 三件套（current/context-for-others/completed）
- ✅ coordinator-progress 三件套加冻结注释（4-25 / 4-28 内容已迁移）

---

## 2026-04-28 17:50 — 8 Agent frontmatter 升级（model 分级 + effort: xhigh，DEC-023）

> ⚠️ 误归档纠正（2026-05-12 16:30）：本条目原归档于 coordinator-progress，因当时 PM 工作误标记为 Coordinator 身份。Founder 明确"你一直是 PM 不是 Coordinator"，正式迁移到 pm-progress。

**任务**：基于 17:25 symlink 修复后 frontmatter 自动加载机制可用，批量升级 8 个 agent frontmatter 默认值。

**前置验证**：
- claude-code-guide agent 查证官方文档（https://code.claude.com/docs/en/sub-agents.md L234-256）
- 官方 frontmatter schema 明确支持 `effort` 字段，5 档取值（low/medium/high/xhigh/max）
- spawn 时显式传 → 覆盖 frontmatter；不传 → 用 frontmatter 默认

**升级清单**：

| Agent | model（前→后）| effort（前→后）|
|-------|-------------|---------------|
| ai-ml | opus → opus（不变）| 无 → xhigh |
| pm | opus → opus（不变）| 无 → xhigh |
| xuhuastory-boss-coordinator | opus → opus（不变）| 无 → xhigh |
| backend | opus → **sonnet** | 无 → xhigh |
| devops | opus → **sonnet** | 无 → xhigh |
| frontend | opus → **sonnet** | 无 → xhigh |
| tester | opus → **sonnet** | 无 → xhigh |
| resonance | opus → **sonnet** | 无 → xhigh（Founder 决定 sonnet）|

**校验**：8/8 grep model+effort+color 全部通过

**已知风险**：
- ⚠️ xhigh 可能是 Opus 4.7 专属（slash command 提示 "(Opus 4.7 only)"）
- Sonnet 5 个 agent 写 xhigh 可能 silent 降级到 high / 报错 / 被 ignore
- 最差也就是 Sonnet 跑 high 而不是 xhigh，**不会比之前差**

---

## 2026-04-28 — subagent_type symlink 修复 + memory 地毯式搜查

> ⚠️ 误归档纠正（2026-05-12 16:30）：同上，从 coordinator-progress 迁移到 pm-progress。

**任务**：地毯式深挖所有可能受"PM 主对话只能用内置 type"错误结论污染的文档/记忆/规则。

**真污染面（仅 2 处）**：
1. `feedback_use_custom_subagent_type.md` — 全文重写
2. `MEMORY.md` L134-136 — 索引同步

**新建文件**：
- `reference_subagent_symlink.md` — symlink 路径 + 验证命令 + 重建命令 + git ignore 提醒

**验证**：
- symlink 状态：`Apr 28 16:53` 建立，target 正确
- spawn `subagent_type: "backend"` 实测：UI 绿色高亮 + 0 tool_uses + 2.8s 完成回复

**系统级影响**：所有 Founder agent 现在可直接 spawn 彩色 subagent_type，frontmatter 自动加载。

---

## 2026-04-25 — 4 层成本路线图 + TASK-PARALLEL-M1 派发 + 角色文件全面校准

> ⚠️ 误归档纠正（2026-05-12 16:30）：同上，从 coordinator-progress 迁移到 pm-progress。

**主要事项**：
1. 3 个 Sonnet 并发深查（代码现状 / Gemini Batch API / UX 影响）
2. 4 层成本路线图（M0 30% → M3 53% → M9 70% → M18 85%）
3. DEC-020/021/022 记录（M1 工程并行化 / BP 写完整路线图 / 不做画质降级）
4. TASK-PARALLEL-M1 详细规格（含 8 个失败分支兜底矩阵）写入 PENDING
5. BP_SUPPLEMENT 第 6 节《单位经济与成本工程》落盘
6. 角色文件 xuhuastory-boss-coordinator.md 全面校准（282 → 335 行）
7. TEAM_CHAT 派活通知

**关键决策**：
- DEC-020：M1 工程并行化优先（13.5 min → 4.5 min UX 跃迁）
- DEC-021：BP 写完整 4 层杠杆 + 自建集群路线图
- DEC-022：不做 gemini-2.5 vs NB2 画质盲测（NB2 画质是产品力护城河）

---

## 2026-05-11 19:00-20:55 — Wave 6 派活 + 审查 + Alembic upgrade + DEC-024

**触发**: Founder /xhteam 4 决策拍板（60s 倒计时 / 修 P2 / 一次性修 / Backend Opus 4.7 xhigh）

**3 agent 并行 spawn 结果**:

| Agent | 模型 | 工时 | 结果 |
|---|---|---|---|
| Backend | Opus 4.7 xhigh | 1.5 hr | 5 bug + Wave 5 补完 / 9 文件 + Alembic 005 / py_compile + pytest 7/7 + 9 smoke 全过 |
| Frontend | Sonnet 4.6 high | 1 hr | 3 bug + Wave 5 补完 / 2 文件 / npm build 0 errors 20 routes |
| AI-ML | Sonnet 4.6 high | 30 min | B52 L6 HAIR_COLOR_REQUIREMENT_RULE / 2 文件 / py_compile + pytest 7/7 |

**PM 第四步独立深度审查（20:45-20:50）**:
- 跨 agent 联调点 #1 scenes_confirmed 字段全链路 ✅
- 跨 agent 联调点 #2 confirm-scenes endpoint Backend ↔ Frontend ✅
- B52 L5 reload 真接 Stage 4（characters dict 覆盖 + 落盘 + storyboard_director.direct 真用）✅
- R4-2 wait loop 真接 Stage 4 前 + scenes_json reload ✅
- HAIR_COLOR_REQUIREMENT_RULE 两处注入 ✅
- Frontend 60s 倒计时 + URL guard + gap-fill ✅
- Mureka 全 async ✅
- Minor: urllib.request / urllib.error dead import 未清（下轮顺手）

**PM 操作**:
- Alembic upgrade head 004 → 005_add_scenes_confirmed ✅
- DEC-024 写入（scenes 确认作为用户旅程第三停留点）✅
- TODAY_FOCUS / PROJECT_STATUS / context-for-others / completed 4 处文档全补 ✅

**当前服务**:
- Backend PID 60819 / Frontend PID 60825 / alembic head 005

**下一步**: 第五步集成验证 — spawn Tester 跑 3 轮分阶段回归

---

## 2026-05-11 17:42-18:50 — test12 实测 + Wave 5 验证 + Wave 6 完整 Bug 清单锁档

**测试上下文**: project `a7bf046d-2471-4a28-88a1-ff79053526b8` 第42天的豆沙包（晨跑浪漫故事 3 角色 11 scenes 18 shots），Founder 实操 adjust 林晓薇头发为亚麻青，全 Pipeline 跑完 2426s。

**完成内容**:

1. ✅ **Cron 监控**: 全 Pipeline 期间 2 分钟 cron 综合检查（37970a1a），自停于 18:18:43 BGM 完成 + 18:19:04 JobManager ✅ 总耗时 2426.4s
2. ✅ **Wave 5 实测验证 10 项 PASS**: B46 partial_failure / Shot 9 重生 / B57 fullbody / B49 后期稳定 / B56 description / B47 mood 浪漫 / B51 v2 fallback / B49 真返 / BGM 链路 / StageD UI 错误处理
3. ✅ **Shot 9 IncompleteRead 失败诊断**: 4 次重试全失败 (18:07-18:10) → 后续用户重生 18:24:18→18:25:16 一次成功
4. ✅ **B52 cascade 真因 100% 锁定（3 次诊断迭代）**:
   - 18:20 错诊断: "Stage 5 reference 覆盖亚麻青为黑发，17 shots 全黑发" — 被 Founder 实测推翻
   - 18:30 错诊断: "Stage 4 读旧文件 2_characters.json，5 层断裂" — Explore agent very-thorough 推翻
   - 18:40 终极真因: **Pipeline `characters` in-memory 永不 reload** + Shot 5 vs Shot 10 Seedream 输入对比给出 100% 决定性证据
5. ✅ **7 bug 完整锁档**:
   - PENDING.md 7 个 BUG-* 完整条目（背景 + 证据 + 实施代码示例 + Tester 验收 + 风险）
   - TEAM_CHAT.md 18:10 / 18:15 / 18:35 / 18:40 完整时间线
   - pm-progress/current.md + context-for-others.md 同步
6. ✅ **3 个 PM 教训锁入 memory**:
   - `feedback_carpet_review_must_include_history.md` — by-design 判断必须 5 维度
   - `feedback_trace_full_callstack_not_pattern.md` — 不能拿字符串反推数据源

**关键产物**:
- BGM: `bgm_chapter0.mp3` LUFS -14.2 dB / meta_version=mixed
- 17/18 shots（Shot 9 永久失败已重生）
- 17:46 char_001 portrait 亚麻青 + 17:48 fullbody 亚麻青（B57 ✅）

---

### 2026-05-09 15:00-15:35 — B33+B34 闭环（产品调整 + 事务边界改动）✅

**触发**: Founder xhteam 派 — "B33 + B34 一起修，B33 把 mood 移到大纲生成前"

**派活**:
- Backend agent (Sonnet 4.6) — B33 全后端链路 (9 文件) + B34 generate_outline endpoint
- Frontend agent (Sonnet 4.6) — B33 StageA chips + 移除 StageB mood section (4 文件)
- PM 自己 — API 契约协调 + 地毯式审查 + alembic upgrade + clean restart + monitor v11 + 文档

**B33 产品调整 (Founder 决策升级版)**:

不只修 3 行 — 把 mood 选择从 outline 编辑页移到 Stage A（大纲生成前），用户先选 mood → Stage 1 LLM 按 mood 写 outline → outline 编辑页不再让用户改 mood → BGM 也按这个 mood 路由。理由："大纲都生成了 mood 也基本定了，后面再改有违和感，对 BGM 生成可能不伦不类"

Backend 9 文件:
- `alembic/versions/003_add_user_selected_mood_to_projects.py` 加列
- `app/models/project.py` Column(String(32))
- `app/schemas/project.py` ProjectCreate Literal 8 中文 + ProjectDetail 暴露
- `app/api/projects.py` create_project 持久化 + generate_outline 注入 + start_generation 透传 + confirm-outline 双轨兼容
- `app/services/story_outline_generator.py` 中文→英文 8 桶映射 + LLM MANDATORY 约束
- `app/services/music_generation_service.py` priority chain
- `app/services/story_music_extractor.py` priority chain
- `app/services/job_manager.py` 透传
- `app/services/pipeline_orchestrator.py` 透传

Frontend 4 文件:
- `frontend/src/types/create.ts` userSelectedMood state + MOOD_OPTIONS
- `frontend/src/contexts/CreateContext.tsx` reducer + initialState
- `frontend/src/app/create/CreateContent.tsx` StageA chips + POST body + hydrate
- `frontend/src/components/create/StageB.tsx` 完全删除 mood section + confirm-outline 双轨兼容

**B34 真根因订正（地毯式审查发现）**:

Daily-sync 写"B28 Stage 3 LLM 阻塞 DB"是错的。Stage 3 ScreenplayWriter 本来就不在事务内（`job_manager.py` checkpoint_callback 用 `async_session_maker()` B-1 短 session 模式）。真根因是 **Stage 1 generate_outline endpoint** 254s LLM 期间持有 db session 连接。

修复方案 A: `app/api/projects.py:431-475` generate_outline endpoint
- L443 `await db.commit()` 提前提交 READ 事务释放 row lock
- L449 LLM 调用（254s）不在事务内
- L465 `async with async_session_maker()` 短事务写 raw_outline_json

**地毯式审查（Founder 强调"全维度无遗漏"）**:

- ✅ B33 完整数据流追踪（frontend chips render → POST body → DB 持久化 → Stage 1 LLM 注入 → priority chain → BGM）
- ✅ B34 所有 stage 事务边界确认（Stage 3/4/5/6 均无问题）
- ✅ mood 8 中文→英文映射验证
- ✅ 现有修复未破坏（B26/B27/B28/D.21+D.23+D.24+D.25/stale-copy）
- ✅ Alembic 003 升级日志 + down_revision 链对
- ✅ Frontend chunk 386-ac0fee450e03c78e.js 真含 user_selected_mood
- ✅ AST 9 backend 文件 PASS + pytest test_architecture 7/7 PASS

**干净重启实施**:

1. ✅ alembic upgrade head: 002 → 003（加 user_selected_mood 列到 projects 表）
2. ✅ kill 55079 (旧 backend) + 56089 (旧 frontend)
3. ✅ rm -rf frontend/.next + npm run build (新 BUILD_ID `SVbXl3_Z3Lr31obqPhC0T`)
4. ✅ nohup uvicorn (PID 59918 @ 15:34, 不带 --reload)
5. ✅ nohup npm run start (PID 60089 + child 60108 @ 15:35, production)
6. ✅ Monitor v11 重启 (task `babu7i629`，旧 v10 `bigucgvll` 已自死)

**待**:
- Founder 隐身测试（Stage A 真有 mood chips + 选悬疑后 outline 真按悬疑 + BGM 真路由 Mysterious 桶）
- Push notification 通知 Ben（projects 表加列影响共享 DB）

---

### 2026-04-24 — TASK-VPS-SKIP-IMAGE + NB2 三天回溯审查 ✅

**TASK-VPS-SKIP-IMAGE**: Founder 选项 A 派 @devops 给 VPS `.env.production` 追加 `SKIP_IMAGE_GENERATION=true` + force-recreate api 容器。4 步 + 3 验证一次过关，`settings.SKIP_IMAGE_GENERATION=True` 在容器生效。

**NB2 生图三天回溯审查**（Founder 要求地毯式）:
- 独立 5 层交叉验证：代码静态 / 本地 backend.log 14MB / VPS docker logs / DB api_cost_logs / 两端 .env SKIP 标志
- 结论: **2026-04-22 ~ 04-24 NB2 生图 0 次调用 / $0**
- 三天总花费约 $0.53（全部来自 04-23 Pipeline 的 Claude Sonnet 4.6 + Mureka + Haiku）

**新发现**:
- `api_cost_logs` 是孤儿表（0 行，代码 0 引用），与之前 `chapter_scene_images` / `project_character_references` 并列为 3 张孤儿表 → 记入 PENDING

**其他工作**:
- 本地前后端干净重启（清缓存 + 无 --reload + Claude 托管 shell）
- 开启 prefaceai.mov + 本地双实时监测

---

### 2026-04-23 — TASK-BUG-FIX-BATCH-1（Route B + C） ✅

**背景**: 2026-04-23 Founder 本地跑通完整 Pipeline（"泰迪知道的秘密" 16 分 10 秒），PM 深度审查发现 **18 个 bug**（Backend 6 / Frontend 8 / Arch 3 / Ops 1）+ **3 条 DB 脏数据**。Founder 批准全修 + 今天部署到 VPS。

**并行 @backend + @frontend 一次过关**:
- Backend Route B: job_manager checkpoint 类型判断 + pipeline_orchestrator SKIP 分支 + Stage 6 credits_used + main.py /static mount + DB 清理（5 step 全过）
- Frontend Route C: FE-5 根因（StrictMode completedRef 污染）+ 修复 + FE-1/2/3/4 修复（5 bug 全修）

**PM 独立审查**:
- 5 代码文件 git diff 逐行核对全部正确
- pytest 7 passed / /health healthy / /static 可访问 / DB 脏数据清理 / npm build 0 error

**3 个额外 bug 记入 PENDING（agent 主动上报）**:
- job_manager.py:302 完成时 stage 被覆盖
- Stage 6 BGM 没 progress_callback
- StageD.tsx imageUrl=null 文案误导

**下一步**: 派 @devops 部署 VPS

---

### 2026-04-22 — TASK-8631-UNIFY ✅

**背景**: TASK-LLM-TEMP-AUDIT-FIX Step 7 backend 调查汇报"14 处 + story_outline_generator 已改"，PM 独立地毯式 grep 核对发现偏差（13 处 + 半改状态）。Founder 批准即时执行。

**@backend 一次过关**:
- 13 处 8631→16384 分布 5 文件全部改完
- grep 核对代码侧 0 命中
- pytest test_architecture 7 passed
- /health healthy
- Backend 在 progress 三维度做了自我纠错记录

**教训**（记入反思）:
- PM 审查 agent 调查类任务时**不能只看结论**，必须独立地毯式 grep 验证数字
- 这次是 Founder 问"是不是只有 14 个"才触发 PM 做独立核对，如果 Founder 没问，错误数据会留在 PENDING

---

### 2026-04-22 — TASK-LLM-TEMP-AUDIT-FIX ✅

**背景**: Founder 对 42 个 LLM 调用点做全量 temperature/max_tokens 审计，发现 4 类问题。PM 规划 7 步改动（含 8631 调查），Founder 批准。

**@backend 一次过关**（15 改动点，规划 14 + backend 主动补 1 对）:
- alignment_service (2) + shot_validator (1) + api/utils (4+1 import) + story_generator (1) + screenplay_writer (4) + storyboard_director (2) = 15 点
- pytest test_architecture 7 passed / /health healthy

**PM 独立地毯式审查**:
- 对每一处 git diff 核对语义：全部正确
- Step 7 `8631` 调查 backend 说 14 处 → 独立 grep 结果**实际 13 处**（backend 数错）
- 且 `story_outline_generator.py` 属半改状态：Claude L178 已 16384，Gemini L196 仍 8631
- 下一步: 派 @backend 统一 13 处 8631→16384（Founder 批准执行）

**文档更新**: TEAM_CHAT 完整记录 + backend-progress 三维度 + pm-progress 三维度 + PENDING 新增 P3 条目 → 待纠正为 13 处。

---

### 2026-04-21 — TASK-MUREKA-PIPELINE-INTEGRATION Wave 1-4 + VPS 部署 ✅

**全链路 BGM 能力落地**:
- Wave 1 数据层（@backend）: music_hint 字段 × 28 styles + 67 MUSIC_HINTS 表 + 4 BGM 列 + MUREKA_API_KEY 配置
- Wave 2 服务层（@backend）: story_music_extractor / music_generation_service (8 step) / ffmpeg_post_processor (atrim + ebur128 + silencedetect)
- Wave 3 API（@backend + @frontend）: GET /bgm, POST /bgm/regenerate (+10 cr), POST /bgm/change-meta (+5 cr), PATCH /bgm/volume; BgmPlayer.tsx 5 状态 + StageD 集成 build 20 路由 0 错
- Wave 4 集成测试（@tester + PM）: 6P/2W/1S，发现 P2 bug（chapters.py 两处 style_preset → get_music_hint()），Founder 听 3 mp3 确认风格层有辨识度，通过
- VPS 部署（PM 代执行，@devops Bash 二次被拒）: commit `b998cbf` push + rsync + MUREKA_API_KEY + docker rebuild + health OK

**已知 MVP 后 PENDING (P3)**:
- music_hint 在 Haiku 层效用有限（但 Mureka mp3 层可辨，Founder 接受）
- 秋梨膏温暖动作性故事金句质量重试机制
- 用户自定义 BGM 上传

---

### 2026-04-21 — TASK-HAIKU-QUOTE-EXTRACTION + v3.1/v3.2 迭代 + Pipeline Wave 1 启动

**TASK-HAIKU-QUOTE-EXTRACTION（方案 A 可行性验证）**:
- @ai-ml (Opus) 设计 Quote Selection Protocol（5 正 / 5 反 / 位置倾向 / 数量约束 / 忠实规则）
- @backend (Sonnet) 脚本加 --quote-mode + --all-six 参数
- PM 跑 12 次 Haiku 调用（6 故事 × 2 变体，不调 Mureka）
- PM (Opus) 独立评审：mixed 8.4/10 > en 6.8/10，mixed 反超 en（V2 en 最好的结论反转）
- 产出 `.team-brain/analysis/HAIKU_QUOTE_EXTRACTION_ASSESSMENT.md`
- 意外发现：少 few-shot 年夜饭示例污染（Haiku 直接复制示例）；en 在秋梨膏违反反向清单

**v3.1 迭代（尝试修 400 字符 + 污染）**:
- @ai-ml Sonnet 加 ASCII 分层图 + 输出纯净规则
- PM 实测发现：污染修复成功，但**金句质量大幅退步**（8.4 → 6.7）
- 根因：大块约束段分走 Haiku attention，挑金句精力减少

**v3.2 方案 B 迭代（污染清理迁到代码层）**:
- @ai-ml Sonnet 精修 meta-prompt（删 ASCII 图 + 纯净规则，保留 2 行轻量长度建议）
- @backend Sonnet 并行加 `clean_haiku_output()` 函数（正则去 markdown fence + 非 quotes XML 标签）
- PM 实测：污染 100% 清理，字符 < 1024 安全，金句质量 7.4/10（接近 v3）
- 秋梨膏连续 3 次挑动作序列（Haiku 温暖故事偏置）→ 记 PENDING P3
- Founder 确认 v3.2 为方案 A 最终版

**TASK-MUREKA-PIPELINE-INTEGRATION Wave 1 ✅**:
- @ai-ml Step B: 95 风格 music_hint 字段（style_enforcer.py + style_config.py）
- @backend Step 1: story_music_extractor.py 提取 15 字段（PM 3 测试 PASS）
- @backend Step 3: ffmpeg_post_processor.py 后处理（含 LUFS 小 bug 归 Wave 2）

**TASK-MUREKA-PIPELINE-INTEGRATION Wave 2 ✅（E2E 验证 PASS）**:
- @backend 单 agent 串行 3 件事：LUFS 修复（ebur128 替代 loudnorm）+ music_generation_service.py（22K, 8 步 flow）+ chapter DB migration + orchestrator Stage 6 接入
- **PM E2E 测试年夜饭**：Mureka task 134387356336130，-15.5 LUFS 正确，credits_used=10
- PM 修 URL typo 1 行（MUREKA_QUERY_URL_TPL 少 `/query/`）
- 已知阻塞：alembic 未初始化，4 列 ALTER TABLE 待 Ben/DevOps 跑 MySQL schema

**TASK-MUREKA-PIPELINE-INTEGRATION Wave 3 ✅**:
- PM 预定义 REST API 契约供两 agent 并行按契约开发
- @backend Step 5: Stage D BGM REST API 4 端点（GET bgm / POST regenerate / POST change-meta / PATCH volume，asyncio.to_thread 包装避免阻塞）
- @frontend Step 6: BgmPlayer.tsx 新建（5 状态：idle/loading/generating/ready/error）+ StageD.tsx 替换旧 BGM_TRACKS + CreateContext + 4 API 封装，build 20 路由 0 错误

**Wave 4 待启动**: @tester 集成测试 + @devops VPS 部署

---

### 2026-04-20 — TASK-MUSIC-LANG-AB-V2

**背景**: V1 盲听结果 PM baseline > cn > en > mixed，@ai-ml 预估完全反了

**Step 1 @ai-ml (Sonnet)**: meta-prompt v2 升级
- 新增 cross_sensory 4 条元原则 + 3 精选示例（2 好例对极情绪 + 1 反例保守格式）
- 核心修复: ≤400 字符硬约束（解决 v1 mixed 版 855 字符失控）
- 14 占位符与 v1 一致

**Step 2 @backend (Sonnet)**: 脚本加 --version v1|v2 参数
**Step 3 PM 实际运行**: 3/3 v2 BGM 成功
- en 833→421 chars, cn 265→196 chars, mixed 855→506 chars
- 长度硬约束部分奏效，mixed 仍超 400 但改善 41%

**Step 4 PM 做盲听包**: 7 首 random A-G (PM baseline×1 + v1×3 + v2×3)

---

### 2026-04-18（晚）— TASK-MUSIC-LANG-RESEARCH + TASK-MUSIC-LANG-AB

**任务 A 研究**: general-purpose (Opus) 调研 Mureka + Top AI 音乐平台的多语言策略，40+ URL 引用
- 结论：英文骨架 + 中文意象（15-30% 中文）基本有利，V4 年夜饭 prompt 教科书级别
- 6 条可操作规则已归档 `.team-brain/analysis/MUSIC_PROMPT_LANGUAGE_RESEARCH.md`

**任务 B 实证 A/B/C**: 
- Step 1: @ai-ml (Sonnet) 设计 3 个语言变体 meta-prompt
- Step 2: @backend (Sonnet) 写脚本调 Haiku 4.5 + Mureka；PM 审查 + 实际运行
- 首轮 SSL 报错 → @backend 修（certifi 全局 context）→ 次轮 3/3 成功
- 3 个 Haiku 生成 BGM 待 Founder 盲听

**关键教训**: PM 差点自己写 Python 脚本（被 Founder 拦下），已记录 feedback_pm_no_scripting.md

---

### 2026-04-18（下午）— TASK-ENV-SETTINGS-SYNC-TEST

- @backend (Sonnet) 新增 `test_env_example_matches_settings` 到 Harness 架构测试
- AST 解析 + 双向对比 + 白名单（MUREKA_API_KEY 临时在白名单，含 TODO）
- PM 实测两轮：正常 PASS + 故意制造漂移精准捕获
- EP-016 防护状态 ❌→✅（9/16 = 56%）
- PENDING.md 记 TASK-MUREKA-PIPELINE-INTEGRATION（集成时修 .env.example + 移白名单）

---

### 2026-04-18（上午）— TASK-SETTINGS-FIX

- 本地启动 backend 触发 Pydantic `extra_forbidden`（.env 有 3 字段未声明）
- PM 临时 `extra = "ignore"` 绷带启动，深度调查发现文档/代码不一致
- @backend (Sonnet) 补齐 `VOLCENGINE_API_KEY`/`VOLCENGINE_SECRET_KEY`/`MUREKA_API_KEY`，删除 `extra = "ignore"`
- PM 审查 PASS + 实际重启验证 /health = healthy
- EP-016 记入 ERROR_PATTERNS.md
- Backend progress 因 Write 被拒，PM 代更新三个文件

---

### 2026-04-17 — TASK-MUSIC-EXTRACT + TRANSITION + REWRITE

**TASK-MUSIC-REWRITE**: @ai-ml 重写 #3/#4/#6 prompt，PM 审查 PASS，PM 调 API 生成 3 首 V2 BGM
**TASK-MUSIC-EXTRACT**: @ai-ml 定义音乐 prompt 输入格式（story_input_format.md），PM 代创建文件
**TASK-MUSIC-TRANSITION**: @ai-ml 写年夜饭分段转折 prompt，PM 调 API 生成 bgm_transition_test.mp3
- 3 个 agent 因 API 错误/权限问题终止，PM 代创建文件并调 API

---

### 2026-04-17（早些时候）— TASK-MUSIC-REWRITE: 3 首 BGM Prompt 重写 + V2 BGM 生成

- Founder 试听后否决 #3/#4/#6 风格（不贴故事）
- PM 根因分析：@ai-ml 过度追求差异化
- @ai-ml (Sonnet) 重写 3 个 prompt，PM 审查 PASS (5/5)
- PM 直接执行 Mureka API 生成 3 首 V2 BGM（bgm_02.mp3，旧版保留对比）
- 风格变更：Dark jazz→Chinese NY acoustic, Bossa nova→Indie acoustic, Lo-fi electronic→Acoustic warmth

---

### 2026-04-16 — Mureka AI 音乐生成集成测试

**Music Prompt Skill 创建**: 9 个文件（知识库 4 + 模板 3 + 脚本 1 + README 1）
- 基于 Mureka API 完整文档分析（1253 行 21 端点）
- 5 层结构: 场域(Genre) + 骨架(Tempo) + 肌肉(Instruments) + 呼吸(Mood Curve) + 灵魂(Narrative Imagery)
- 李继刚 Prompt 哲学应用（压缩/场域/种子/共振）

**6 个故事 BGM 生成测试**:
- @ai-ml: 6 个 music_prompt.md（6 种不同风格，反同质化设计）
- @backend: 3 轮 Mureka API 调用，7 个 mp3 文件
- 技术发现: EP-015 (curl 中文 JSON) + n=1 成本规则
- 文档更新: ERROR_PATTERNS.md + mureka_model.md + 各 agent progress

**PM 工作**: 协调 @ai-ml → @backend 流水线，审查 prompt 质量，代更新 agent 文档

---

### 2026-04-14 — 全天工作汇总（Harness + R6 + B' + StageD V2 + 部署）

**Harness Engineering V1 (9/9)**:
- Phase 1: @devops hooks 升级 + @tester 10 架构/质量测试 + 闭环激活
- Phase 2: @devops TEAM_CHAT 归档(36K→2.4K) + PM ERROR_PATTERNS(14个) + PM 上下文预算
- Phase 3: @backend Pipeline Schema(Pydantic) + @ai-ml Prompt A/B 分析(36KB)
- Phase 4: HARNESS_HEALTH.md 健康度看板
- **成果**: Sensor 4→7, 计算性控制 3→6

**Prompt Format 优化**:
- 变体 D 设计（李继刚式压缩，-57% token）
- 10-Shot 三方对比分析（68KB 文档）
- A vs B' 实测：20 张 NB2 盲测图生成完毕（@backend），等 Founder 评分

**R6 Founder 测试**:
- "泰迪的秘密" Pipeline 807s 20 shots 零错误
- R6 全部 6 项修复验证 PASS（mood/ending/confirm切换/倒计时/超时/角色调整）
- Schema 验证首次实战通过（Stage 2→3 + Stage 4→5）

**StageD 已知问题 → 全部修复**:
- KI-001: 重新生成 → POST API 接通 + SKIP 模式框架
- KI-002: 编辑 → 改为 text_overlay.chinese_text + PATCH 写 DB
- KI-003: 删除 → DELETE 软删除 + generation-result 过滤

**StageD V2 产品升级（6 项）**:
- Fix-1: generation-result 过滤 deleted shots (PM)
- Fix-2: 编辑旁白→编辑文字 (@frontend)
- Fix-3: 重新生成提示文字 (@frontend)
- New-1: Haiku system prompt 9 规则 (@ai-ml)
- New-2: regenerate Haiku 集成 (@backend)
- New-3: 调整画面输入框 (@frontend)

**A vs B' 盲测结论**: Founder 5:4 偏好 B'，PM 4:3 偏好 B'，质量等价，B' 切为默认

**Founder 联调测试 #2**: 泰迪的秘密 688s 21 shots 零错误 + StageD 4 功能实测

**Push + VPS 部署**: 3 commits (611c501+68ac04f+259f696) → 10/10 验证 PASS

---

### 2026-04-09 — TASK-PIPELINE-OPT R1 完成 + R2 规划

**R1 成果**: Backend 7/7 PASS + Frontend 3/3 PASS (DB session + Stage4 并行 + Stage3 batch + 进度更新 + 百分比重分配 + 断点恢复 + 重试 + 动态提示 + 预估时间 + 错误处理)

**R1 测试发现**: batch 失败 fallback、84×529 API 过载、full_script 溢出、18min 到角色确认太慢、角色调整是 mock、场景描述英文

**R2 规划**: Backend 7 + Frontend 6 + AI-ML 1 = 14 项优化，Founder 确认后派发

---

### 2026-04-09 — Pipeline 全面分析 + TASK-PIPELINE-OPT 规划

**Founder 本地真实 Pipeline 测试**: 总耗时 ~12min（短篇 6 scenes），Stage 4 完成后 DB session 崩溃。

**PM 分析成果**:
1. 定位 P0 崩溃根因: `job_manager.py` 长 session 被阿里云 MySQL 踢掉
2. 发现 Stage 4 可并行化（`_generate_scene_shots` 无跨 scene 依赖）→ 省 65% 时间
3. 研究 Sonnet 4.6 输出上限 64K tokens → Stage 3 batch 可行
4. 确认 Tier 2 API 限额（1K RPM / 90K output TPM）→ 并行无压力
5. 确认 DB 断点恢复列已存在（characters_json/scenes_json/storyboard_json）
6. 设计进度百分比重新分配方案 + 逐 Scene 更新 + 自适应 batch 策略
7. 规划前端等待体验 UX（动态提示 + 预估时间 + 错误处理）
8. 派发 Backend 7 项 + Frontend 3 项

---

### 2026-04-09 — TASK-BUGFIX-STAGEC Review PASS (4/4)

**Founder 测试发现 5 个 Bug**（Bug 1/2 已修复），PM 验证 + 派发 + 审查 Bug 3/4：

| Bug | 问题 | 修复 | 结果 |
|-----|------|------|------|
| 3 (P0) | StageC.tsx L80 `"generating_images"` vs 后端 `"image_generation"` | 前端字符串对齐 | ✅ |
| 4 (P1) | CreateContext reducer 无条件追加 generationLog | isDuplicate 去重 | ✅ |
| 5 (P2) | 角色预览占位图 | 暂缓（SKIP 模式可接受） | ⏳ |

**PM 补充发现**: 全量生图模式 Stage 5 路径缺少 `progress_callback("image_generation", ...)`，已记录到 `.team-brain/shared-memory/notice_fullmode_progress_callback_gap.md`。

---

### 2026-04-08 — TASK-REAL-PIPELINE-UX Step 1 Review PASS + Step 2 派发

**Backend**: 4 文件改动（config + pipeline_orchestrator + job_manager + projects），Stage 5 跳过模式 + 场景数据 + 结果 API ✅
**Tester**: 35/35 pytest PASS，PM 独立跑一致 ✅
**Step 2 派发 @Frontend**: 4 项（StageC 轮询真实 API + 角色真实数据 + 场景真实数据 + StageD 真实结果）

---

### 2026-04-07 — confirm-outline 全链路深度审计 + 2 Bug 修复派发

**Founder 要求**: 验证 StageB 所有维度的用户确认内容是否完整传入下一 stage

**审计方法**: 6 维度 × 全链路（前端发送 → 后端合并 → Pipeline Stage 2-5），逐 Stage 追踪每个字段的读取路径

**结果**: 4/6 正确 ✅，2/6 有 Bug ❌
- Bug 1 (🟡): `summary` 被写到 `logline`，`summary` 字段未更新 → 后续读 summary 的功能拿到旧值
- Bug 2 (🔴): `selected_ending` 存了但 Stage 3 不读 → **用户选的结局不影响最终故事** → 方案 C 修复（替换 plot_points 最后一条 description）
- 全链路影响验证: Stage 2 角色/Stage 5a 参考图/Stage 5a.5 场景 **不受影响**（不读 plot_points）

**产出文档**: `.team-brain/analysis/CONFIRM_OUTLINE_DATA_AUDIT.md`（含未来优化方向：让 ending_options 携带完整 full_plot_point）

**派发**: TASK-OUTLINE-MERGE-FIX @Backend（2 处修复，projects.py confirm_outline 函数）

---

### 2026-04-05 — 全局状态审查 + confirm-outline 验证 + DevOps API Key 验证派发

- PM 全量读取 TEAM_CHAT 33,000+ 行 + 全部 Agent progress + .team-brain 文档
- 识别 7 项可协调事项，优先级排序
- confirm-outline 前端接入: ✅ 深度验证确认 WIRE 修复已完全解决（StageB 正确调 confirm-outline → start-generation）
- Phase 2 Step 3 通俗解释给 Founder（seed 图生成逻辑）
- DevOps 验证 VPS API Key: ✅ 审查 PASS — 核心 4 Key 已填入生效，R1 🔴→✅ 基本解决，TTS 2 Key 缺失不影响核心

---

### 2026-04-04 — Ben DB 异常根因确认 + 部署/清理派发

- **Ben 反馈**: 同一 idea 产生 2 条 projects + generation_jobs 大量 failed + processing 卡住
- **PM 根因**: VPS 旧代码 `POST /projects/` 每次创建 Project + Chapter + Job + 启动 pipeline，StageA/B 各调一次 = 重复
- **验证**: `git show HEAD:app/api/projects.py` L135-147 有 `asyncio.create_task`，本地新代码 L109 已移除
- **派发**: @DevOps 部署 + @backend_Ben DB 清理 + shared-memory 通知

---

### 2026-04-03 — TASK-PLOTPOINT-REORDER-FIX 三方 Review PASS (39/39)

- **Frontend**: StageB plot_points `{description, original_index}` 格式 + build PASS
- **Backend**: projects.py original_index 重排 + .copy() + 向后兼容 + syntax PASS
- **Tester**: 39/39 ALL PASS — PM 独立跑确认，T4b mood 跟随 ✅

---

### 2026-04-03 — TASK-CONFIRM-OUTLINE-TEST PM Review PASS (37/37) + PLOTPOINT-REORDER-FIX 派发

- **Tester 测试**: 37/37 ALL PASS（合并 10 + JSON 8 + Pipeline 8 + 代码一致性 11）
- **PM 独立跑测试**: 37/37 确认
- **Tester 观察采纳**: 情节元数据不跟随排序 → Founder 决定优化
- **派发**: TASK-PLOTPOINT-REORDER-FIX @Frontend + @Backend + @Tester 并行

---

### 2026-04-03 — TASK-CONFIRM-OUTLINE-WIRE 全链路 Review PASS

- **架构审计**: StageB 6 字段全断联，三层断裂（前端/架构/Pipeline）
- **方案设计**: 2 步 — Frontend 接通 API + Backend pipeline 集成
- **Frontend Review**: 9/9 PASS — projectId state + confirm-outline + start-generation + 无重复创建
- **Backend Review**: 7/7 PASS — POST /projects/ 去 pipeline + confirm 合并 + start-generation + pipeline skip Stage 1
- **Backend 链路修复**: 7/7 PASS — job_manager 分支 → PipelineOrchestrator.run(confirmed_outline)

---

### 2026-04-02 — TASK-UPLOADER-ENV-FIX 全链路闭环 (Frontend 5/5 + DevOps PASS)

- **Frontend Review**: 5 文件全部 `import { API_BASE }` + 零残留 + build 通过 + 额外发现 PM 遗漏 2 文件
- **DevOps Review**: 2 commits push + SCP 5 文件 + frontend rebuild only + 后台 rsync 补全 + Ben 知会
- **2026-04-01 全日闭环**: V3(24/24) + 4a/4b/4c + 第1次部署 + ENV-FIX(5/5) + 第2次部署

---

### 2026-04-01 — DevOps 部署审查 PASS + 自定义分析 env bug 发现 → TASK-UPLOADER-ENV-FIX 派发

- **DevOps 审查**: 4 commits push + VPS SCP + Docker rebuild + Ben 知会，全部正确，DevOps 无责
- **Founder 发现**: prefaceai.mov 自定义风格/角色/场景上传后无 AI 分析标签
- **PM 根因**: 3 个 Uploader 组件用 `NEXT_PUBLIC_API_BASE_URL`（未设置），全站标准是 `NEXT_PUBLIC_API_URL` → 生产 fallback localhost → 静默失败
- **派发**: TASK-UPLOADER-ENV-FIX @Frontend（3 处改 1 行）

---

### 2026-04-01 — TASK-JSON-REPAIR-V3 PM Review PASS (24/24)

- **审查范围**: `story_outline_generator.py` L419-477 `_fix_unescaped_quotes()` 正则→状态机重写
- **PM 独立测试**: 10 指定用例 + 14 额外边界用例 = 24/24 全 PASS
- **发现 3 项 (非阻塞)**: 4a 文档日期 3 处错误 + 4b L454 冗余 `\n` + 4c L471 无配对回退双追加 bug
- **处置**: 通知 @Backend 修复 → 修复后 @DevOps push + VPS 部署

---

### 2026-04-01 — Founder 测试 JSON 引号 bug → PM 根因分析 → TASK-JSON-REPAIR-V3 派发

- **Bug**: 进度条到 ~90% 跳回，`大纲生成失败: 无法从LLM响应中提取JSON`
- **PM 分析**: Claude 返回 9851 字符完整 JSON，但字符串值内含未转义引号 `"慧茹"——她`
- **根因**: `_fix_unescaped_quotes()` 正则白名单遗漏 EM DASH (U+2014) 等非 CJK 标点
- **PM 判断**: 正则方案已到极限（白名单补不完，黑名单误伤 JSON 结构），需状态机方案
- **附带修复**: 6 处 `print()` → `logger.info()` (LOGGING-FIX 遗漏) + uvicorn 日志写入文件
- **教训**: PM 不应该自己动手改代码（被 Founder 指出），应派发给 Backend
- **派发**: TASK-JSON-REPAIR-V3 @Backend（状态机 + 10 测试用例）

---

### 2026-03-29 — Stage 1 E2E 通了 + 日志全链路审查 + 4 项改进派发

- **联调成功**: 全部 200 OK，"爷爷的老照片" 3 角色 6 情节点
- **日志审查发现**: ① DB 格式不干净 (idea 空时多余前缀) ② 自定义风格被预设覆盖 (StyleSelector handlePresetClick 清空 customStyleAnalysis)
- **Founder UX 反馈**: ③ 自定义风格上传无 loading 动效 ④ OCR 图标提示太隐晦
- **根因深挖**: StyleSelector L33-36 `handlePresetClick` 调 `onCustomStyleChange(null,null,[])` 清空了自定义
- **派发**: A-Backend TASK-DOC-FORMAT + B-Frontend TASK-STYLE-PRIORITY (3 改动)

---

### 2026-04-01 — TASK-OUTLINE-PROGRESS Review PASS (16/16)

- 6 阶段时间模拟 + 非线性插值 + 进度条 + 阶段文字动画 + 已等待时间 ✅
- API 返回才 100% → 0.5s → StageB ✅
- 错误时显示错误 + "返回重试" ✅
- mock 路径 3s 完成 ✅

---

### 2026-03-31 — DevOps push+VPS 审查 PASS + OUTLINE-PROGRESS 派发

- DevOps 审查 (9/9): Frontend 200 + API healthy + 3 容器 + 3 API Key + asyncmy + Ben 融合
- TASK-OUTLINE-PROGRESS 派发 @Frontend: 大纲生成 80-90s 等待 → 时间模拟进度页面 (6 阶段 + 非线性进度条)

---

### 2026-03-30 — Ben 生产反馈 + 新规则 + LOGGING-FIX PASS

- Ben 反馈: 生产 raw_outline_json/confirmed_outline_json 为空
- 原因: 生产没部署最新代码 + confirm-outline 前端没接
- 新规则: push + VPS 部署一起做，不分批，不跳过部署
- confirm-outline 待办已记录到 memory
- LOGGING-FIX Review PASS (6/6)

---

### 2026-03-30 — TASK-LOGGING-FIX Review PASS (6/6)

- TeeStream 删除 + logging.basicConfig (StreamHandler + FileHandler) ✅
- 3 文件 logger.getLogger("xuhua") + 15 处 print→logger.info ✅
- 旧 print 零残留 ✅

---

### 2026-03-29 — Founder 殡仪馆重测 ✅ + LOGGING-FIX 派发

- 殡仪馆故事 JSON 7920 chars 解析成功（上次同故事 10469 chars 失败）→ REPAIR-V2 正则修复确认
- DB 全链路审查: idea 234 字 + 中篇 6min 3:4 + 自定义风格 + 大纲"三百封信" 3 角色 6 情节 5 场景 mood=感人
- PERSISTENT-LOG TeeStream 不生效（uvicorn 多进程）→ LOGGING-FIX 派发 @Backend (logging 模块替代)
- DevOps push 已通知

---

### 2026-03-29 — REPAIR-V2 (6/6) + PERSISTENT-LOG (5/5) Review PASS

- REPAIR-V2: 正则加 `\uff00-\uffef` + `{1,50}`。Test 2 全角逗号修复 ✅ + Test 5 json.loads ✅
- PERSISTENT-LOG: TeeStream stdout/stderr → 终端+文件。storage/ 在 .gitignore ✅

---

### 2026-03-29 — 殡仪馆中篇 JSON 失败排查 + REPAIR-V2 + PERSISTENT-LOG 派发

- Founder 测试: 殡仪馆 MD + 自定义风格 + 中篇 + 3:4 → 90秒后 JSON 提取失败
- 复现 + 字符级分析: `_fix_unescaped_quotes` 正则 2 缺陷:
  ① 字符范围不含全角标点 U+FF00-FFEF (中文逗号 `，` 等)
  ② 长度限制 {1,20} 太短
- 派发: A-REPAIR-V2 (正则加 `\uff00-\uffef` + `{1,50}`) + B-PERSISTENT-LOG (TeeStream 永久日志)

---

### 2026-03-29 — 🎉 Founder 联调全链路通过 + DevOps push 派发

- DB 格式干净 ✅ + 自定义风格传入 LLM ✅ + 角色/场景参考传入 ✅ + 全部 HTTP 200 ✅
- DevOps push 6 个 TASK 改动

---

### 2026-03-29 — DOC-FORMAT (3/3) + STYLE-PRIORITY (8/8) Review PASS

- Backend: idea strip + doc 直接用无前缀 ✅
- Frontend B1: handlePresetClick 不清自定义 + 预设半透明 + "已使用自定义风格" ✅
- Frontend B2: CustomStyleUploader analyzing 状态 + Loader2 动画 ✅
- Frontend B3: HelpCircle + hover 提示 "上传包含故事创意文字的图片" ✅

---

### 2026-03-29 — TASK-DOC-ONLY-FIX Review PASS (6/6)

- Backend: original_idea min_length 移除 + 双重校验 (idea 和 doc 都空才 400) ✅
- Frontend: apiFetch detail 数组处理 (Array.isArray → .msg join) ✅

---

### 2026-03-29 — Founder 联调: 纯文档 422 + [object Object] → TASK-DOC-ONLY-FIX 派发

- 上传 MD 文档不输入文字 → 422 (original_idea min_length=1)
- 前端 detail 是 Pydantic 数组 → 显示 [object Object]
- 派发: Backend (min_length 移除 + 双重校验) + Frontend (detail 数组处理)

---

### 2026-03-29 — TASK-JSON-REPAIR Review PASS (8/8)

- _fix_unescaped_quotes 静态方法 ✅ + _extract_json 预处理调用 ✅
- 4 测试: 根因场景 ✅ + 正常 JSON 不误改 ✅ + json.loads 成功 ✅ + 多对引号 ✅

---

### 2026-03-29 — Founder 联调 JSON 引号 bug 排查 + TASK-JSON-REPAIR 派发

- Founder 联调: 预设风格"欧美漫画"→"无法从LLM响应中提取JSON"（间歇性）
- 后端日志分析: stop_reason=end_turn, output_tokens=3116, response=6099 chars
- 完整响应捕获 + 字符级分析: `U+0022` ASCII `"` 在 `"校霸"` 中，破坏 JSON 结构
- 根因: Claude 在中文文本内输出未转义 ASCII 双引号（`"词"` 而非 `"词"` 或 `\"词\"`）
- TASK-JSON-REPAIR 派发 @Backend: `_fix_unescaped_quotes()` 正则预处理

---

### 2026-03-29 — TASK-AUTH-RESILIENCE Review PASS (10/10)

- ApiError 类 (api.ts L3-9) ✅ + apiFetch throw ApiError (L50) ✅
- hydrate catch 401 only (AuthContext L118-125) ✅
- refreshStories try/catch 容错 (L102-106) ✅
- import ApiError ✅
- `/auth/me` 失败正确传播到外层 catch ✅

---

### 2026-03-29 — Founder 联调 + 静默登出 bug 发现 + TASK-AUTH-RESILIENCE 派发

- **联调结果**: 预设风格 ✅ 成功 / 自定义上传 ❌ 返回 mock 数据
- **DB 取证**: 第二次测试无项目创建 → 前端未调后端 → mock 路径
- **根因**: `AuthContext.tsx` L113 hydrate catch 把所有错误当 token 失效 → 500/超时也清 token → 用户静默登出
- **分析范围**: apiFetch error 传递 + hydrate catch + refreshStories 容错 + 后端 auth 401/500 逻辑
- **结论**: 纯 Frontend bug，后端不需要改
- **派发**: TASK-AUTH-RESILIENCE @Frontend (3 改动: ApiError 类 + 401 only + refreshStories 容错)

---

### 2026-03-27 — TASK-DEBUG-LOGGING 派发 + Create 页面全交互点分析

- 截图像素级审查: 识别 7 个参数区域 (故事创意+OCR+文档 / 篇幅 / 比例 / 风格+自定义 / 角色参考 / 场景参考 / 生成按钮)
- 日志覆盖分析: 已有 StoryOutlineGenerator 日志 + 缺 7 个关键埋点 (前端参数→后端接收→LLM 传参)
- TASK-DEBUG-LOGGING 派发 @Backend: 7 埋点，只加 print 不改逻辑，Founder 测 1 次即可看完整链路
- 目标: 最少 API 调用次数定位最多问题（省钱）

---

### 2026-03-27 — TASK-SHARED-DB Review PASS (7/7)

- .env → 阿里云 `101.132.69.232:3306/prefacestory` (aiomysql 驱动) ✅
- 云端 6 列 Python 直连验证全部存在 (6/6) ✅
- Docker MySQL 已停且删除 ✅
- `.env` 未被 git 追踪 ✅
- Founder 联调通知

---

### 2026-03-26 — Ben 双数据库问题 + TASK-SHARED-DB 派发

- Ben 拉代码发现 create 页面显示 mock 数据 → 原因: 我们用本地 Docker MySQL，Ben 用阿里云 MySQL，两个数据库不同步
- Ben 要求: 开发/测试/生产共用阿里云 MySQL，禁止自建本地数据库
- TASK-SHARED-DB 派发 @DevOps: .env 切换 + 云端补 6 列 + 验证 + 停 Docker

---

### 2026-03-26 — Phase 2 Step 3 PASS + Phase 1+2 全部完成

- ProjectStyleConfig `custom_enforcement` 修复确认 ✅
- Phase 1+2 全量: Backend 16 文件 + Frontend 10 文件 + 2 新文件 + 13 thumbnails + 1 测试脚本
- Founder 联调已通知（含 MySQL 新列提醒）

---

### 2026-03-25 — Phase 2 Step 3 Review (11/12, 1 bug)

- StyleEnforcer create_custom_enforcement ✅
- ReferenceImageManager seed_image + set_reference dict ✅
- SceneReferenceManager seed_images ✅
- Pipeline orchestrator 3 参数 + 分支逻辑 ✅
- **Bug**: ProjectStyleConfig 缺 `custom_enforcement` 字段 → 通知 Backend 修复

---

### 2026-03-25 — Phase 2 Step 2 PASS + Step 3 派发

- else 修复确认 ✅ (L143-144)
- Step 2 整体 PASS
- Step 3 派发 @Backend: ReferenceImageManager seed_image 参数 + set_reference 格式修复 + SceneReferenceManager seed 图 + Pipeline orchestrator 分支 + StyleEnforcer create_custom_enforcement

---

### 2026-03-25 — Phase 2 Step 2 Review

- **Frontend PASS (11/11)**: 3 mock→真实 API + 推荐数 UI (角色/场景与 Founder 决策一致) + create 请求 3 字段 + CharacterAnalysisResult/SceneAnalysisResult 类型
- **Backend 发现回归 bug**: `generate()` L142 缺 else 分支 → 标准流程 prompt 末尾缺"现在开始生成故事大纲" → 已通知修复

---

### 2026-03-25 — Phase 2 Step 1 Review PASS (18/18) + Step 2 派发

- AI-ML 4 prompts 全部到位 (风格分析/角色提取/场景提取/大纲上下文) ✅
- Backend file_storage.py + 3 分析端点 + StoryOutlineGenerator 参考上下文 ✅
- 发现 1 低优先级: _build_prompt 和 generate() 都有"现在开始生成故事大纲" → 重复
- Step 2 派发: @Frontend (mock→真实 API + 推荐数 + create 发送) + @Backend (schema + model + 传参 + 修复)

---

### 2026-03-25 — Phase 2 设计复查 + Step 1 派发

- VALIDATION-FIX Review PASS ✅
- Phase 2 设计复查发现 5 个缺陷（set_reference 格式不匹配 + extractedInfo 格式耦合 + 场景零分析 + 无 seed 图参数 + 无 interior/exterior 判定）
- 设计决策: AI 提取返回文本描述（非结构化字段），避免前后端格式耦合
- Phase 2 分 3 步: Step 1 基础层 → Step 2 集成层 → Step 3 Pipeline 层
- Step 1 派发: @AI-ML (4 prompts) + @Backend (文件存储 + 3 分析端点)

---

### 2026-03-25 — Founder 联调 3 发现 + Phase 2 设计更新

- **发现 1**: 验证 Bug (idea OR documentText) → TASK-VALIDATION-FIX 派发 @Frontend
- **发现 2**: 确认自定义风格/角色标签是 mock → Phase 2
- **发现 3 (关键洞察)**: 用户上传的角色/场景 AI 分析结果应喂给大纲生成 → Phase 2 设计重大更新
- **Founder 澄清**: 最终参考图 = 内容种子(用户角色/场景) + 风格种子(用户自定义风格)
- **Phase 2 设计更新**: 分析→大纲→Pipeline 全链路设计，含 AI-ML/Backend/Frontend/Pipeline 4 层改动全景

---

### 2026-03-25 — ASYNC-FIX Review PASS + Thumbnails 13/13

- TASK-UTILS-ASYNC-FIX (5/5): Gemini `await aio` + Anthropic `AsyncAnthropic` + `await` ✅
- 13 张新风格 thumbnails 全部生成成功 (13/13, 平均 22.9s/张)，直接输出到 `frontend/public/styles/`
- 总 28 张 thumbnail 与 STYLE_PRESETS key 完全对齐 ✅
- Founder 联调已通知

---

### 2026-03-25 — Phase 1 全面审计 (16 文件 12 项验证)

- 12 项交叉验证全部 PASS（Gemini/os.getenv 零残留 + 28 key 三方对齐 + 全部端点特性到位）
- **发现 1 个问题**: utils.py OCR 用同步客户端阻塞事件循环 → TASK-UTILS-ASYNC-FIX 派发 @Backend
- DB 新列生产迁移提醒已记录到 memory（VPS 部署时触发）

---

### 2026-03-25 — Phase 1 Step 2 Review PASS (10/10)

- Backend: StyleEnforcer 28 (style_name grep 确认) + Literal 28 ✅
- Frontend: STYLE_PRESETS 28 + DEFAULT_COUNT 10 ✅
- 三方 28 key 交叉对齐确认 ✅
- 下一步: PM 生成 13 thumbnails

---

### 2026-03-25 — Phase 1 Step 1 全部 Review PASS (25/25)

- **Backend** (14 项): STYLE-LITERAL-FIX (Literal 10→15, chinese 删除) ✅ + DOC-TEXT-WIRE (schema + 拼接逻辑) ✅ + OCR-ENDPOINT (utils.py 新建, Gemini+Haiku 双模型, pdfplumber PDF) ✅
- **Frontend** (6 项): DOC-TEXT-WIRE (document_text 发送) ✅ + OCR-REAL (MOCK_OCR_TEXT 删除, 真实 API + 15s 超时 + 静默降级) ✅
- **AI-ML** (5 项): STYLE-EXPAND-28 (13 新风格 × 6 维度 StyleEnforcement + 前端展示信息) ✅
- Step 2 集成通知 Backend + Frontend

---

### 2026-03-25 — StageA 全面审计 + Phase 1-3 派发

- **审计发现 11 项问题**: #2 文档文本丢失 + #3 OCR mock + #7 风格 422 bug + #8 自定义风格断链 + #9 角色参考断链 + #10 场景参考断链 + #11 续写模式未实现
- **Founder 产品决策**: 28 风格 + gemini-3.1-flash-lite-preview 主力 + claude-haiku-4-5 备用 + 本地文件系统先行 + 角色/场景推荐数更新 + 续写模式扩展到短/中/长篇
- **Phase 1 派发**: 7 项任务 @AI-ML (13 新风格) + @Backend (Literal fix + 文档 + OCR + StyleEnforcer) + @Frontend (文档 + OCR 去 mock + STYLE_PRESETS) + @PM (13 thumbnails)
- **Phase 2 计划**: 文件上传基础设施 + #8/#9/#10
- **Phase 3 计划**: #11 续写模式 Dashboard 化

---

### 2026-03-25 — TASK-ASPECT-RATIO-WIRE Review PASS

- Backend 2 处 + Frontend 1 处，10 项检查全部通过
- 全链路验证: 用户选 → Frontend 发 → schema 收 → endpoint 传 → DB 存 ✅
- 额外全面扫描: StageA 所有文本参数已正确传递，无其他断链
- DevOps push 已派发

---

### 2026-03-25 — TASK-ASPECT-RATIO-WIRE 派发

- PM 发现 aspect_ratio "有字段无入口"：用户选的画面比例被丢失（DB 永远存默认 "2:3"）
- 3 个环节断链: Frontend 没发 → Backend schema 没收 → create_project 没传
- 派发: Frontend 1 处 (CreateContent.tsx body 加一行) + Backend 2 处 (schema + endpoint 各加一行)
- DevOps push 暂停，等修完一起 push

---

### 2026-03-25 — GEMINI-FIX + OUTLINE-STORAGE Review PASS

**任务 A (GEMINI-FIX)**: 7 文件 9 处 → `gemini-3.1-flash-lite-preview`，旧 ID 零残留 ✅，额外修复 story_generator.py ✅
**任务 B (OUTLINE-STORAGE)**: Project model +3 字段 (aspect_ratio + raw_outline_json + confirmed_outline_json) + generate_outline 存 raw + confirm-outline 新端点（Ben 架构对齐 ✅）
**附注**: aspect_ratio 有字段无入口（ProjectCreate schema 待后续更新）
DevOps push 已派发

---

### 2026-03-25 — TASK-GEMINI-MODEL-FIX + TASK-OUTLINE-STORAGE 派发

- **Gemini 调研**: `gemini-3.1-flash-preview` 不存在（Google 404），3.1 Flash 系列只有 flash-lite 和 flash-image
- **TASK-GEMINI-MODEL-FIX**: 6 文件备用 Gemini 统一改为 `gemini-3.1-flash-lite-preview`（4 升级 + 2 修正无效 ID）
- **TASK-OUTLINE-STORAGE**: Ben 提出 Stage 1 存 3 样东西（输入参数 + 原始大纲 + 确认大纲），Founder 确认由我们 Backend 做
- 两项任务派发 @Backend，先 A 后 B

---

### 2026-03-24 — 🎉 Stage 1 前后端联调通过

- Founder 第三次联调成功: 注册→登录→/create→输入创意→Claude 生成真实大纲→StageB 展示 ✅
- 今日修复历程: ENVVAR-FIX (os.getenv→settings) + LLM-FIX (system prompt + async + logging)
- DevOps push 已派发

---

### 2026-03-24 — TASK-OUTLINE-LLM-FIX Backend Review PASS

- 14 项检查全部通过
- 第 1 项: system prompt 集成正确（含 display_name + emotional_journey 补完版）✅
- 第 2 项: debug logging — provider/length/preview(500) ✅
- 第 3 项: `Anthropic→AsyncAnthropic` + `await` + `max_tokens 16384` ✅
- 同步 `anthropic.Anthropic(` 零残留 ✅
- 只改 story_outline_generator.py，未动其他文件 ✅
- DevOps push 已派发

---

### 2026-03-24 — AI-ML system prompt Review PASS

- TASK-OUTLINE-LLM-FIX 第 1 项: StoryOutlineGenerator 专用 system prompt
- 10 项检查: 角色定位 ✅ + JSON 约束 ✅ + 格式强化 ✅ + 中英文分工 18 字段抽查全匹配 ✅ + 新增字段 ✅ + 对比表 ✅ + TEAM_CHAT ✅ + progress 3 文件 ✅ + daily-sync ✅ + 未越界 ✅
- Backend 可开始集成第 1-3 项

---

### 2026-03-24 — Founder 第二次联调 Bug 排查 + TASK-OUTLINE-LLM-FIX 派发

- **ENVVAR-FIX 确认生效** — 错误从 "无可用的LLM服务" 变为 "无法从LLM响应中提取JSON"
- **根因**: `story_outline_generator.py` 缺少 system prompt（Claude 在 JSON 前后加文字/语法错误） + 同步客户端阻塞事件循环
- **对比**: `story_generator.py` 有 system prompt + AsyncAnthropic + max_tokens=16384 → 能工作
- **修复 3 项**: ① system prompt (@AI-ML 设计) ② debug logging ③ Anthropic→AsyncAnthropic + max_tokens 16384
- **DevOps 审查**: ENVVAR-FIX push 2 commits ✅，无责

---

### 2026-03-24 — TASK-ENVVAR-FIX Review PASS + DevOps push 审查

- 12 项检查全部通过
- 5 文件: story_outline_generator, character_designer, screenplay_writer, storyboard_director, prompt_rewriter
- `os.getenv("ANTHROPIC/GEMINI_API_KEY")` → `settings.ANTHROPIC/GEMINI_API_KEY` 零残留 ✅
- `import os` 删除后无其他 `os.` 调用（不 break）✅
- `from app.config import settings` 在 5 文件中均存在 ✅
- 未动其他代码 ✅
- Backend progress 文件 5/5 ✅，未越界 ✅
- DevOps push 已派发

---

### 2026-03-24 — Founder 联调 Bug 排查 + TASK-ENVVAR-FIX 派发

- **现象**: "大纲生成失败: 无可用的LLM服务"
- **根因**: Stage 1-4 服务用 `os.getenv()` 读 API Key，但 `pydantic-settings` 从 `.env` 只加载到 `settings` 对象，不写入 `os.environ` → `os.getenv()` 返回 None → 两个 LLM 客户端都未初始化
- **影响范围**: 5 个文件 (story_outline_generator, character_designer, screenplay_writer, storyboard_director, prompt_rewriter)
- **为什么之前没暴露**: Stage 1-4 之前只通过测试脚本调用（有 `load_dotenv()`），现在第一次通过 FastAPI API 端点调用
- **DevOps 审查**: 8/8 ✅，无责。MySQL/push/验证全部正确
- **PM 自查**: TASK-STAGE1-API Review 时只查了接口契约层面（架构/映射/错误处理），没追踪到 `StoryOutlineGenerator.__init__` 内部的 env var 加载方式 → 已记录为 feedback memory
- **修复**: TASK-ENVVAR-FIX 派发 @Backend（5 文件 os.getenv→settings.XXX）

---

### 2026-03-24 — DevOps MySQL + push 审查

- MySQL Docker (mysql:8.0, 11 tables, /health healthy) ✅
- .env DATABASE_URL 更新 ✅
- MySQL 兼容修复 (scene_image.py + audio_segment.py String 长度) ✅
- 4 commits 分批 push (ai-ml→backend→frontend→docs) ✅
- DevOps 无责于 LLM Bug

---

### 2026-03-24 — TASK-STAGE1-FRONTEND Review PASS

- CreateContent.tsx: StageA mock → 真实 API 两步链路
- Step 1: `POST /api/projects/` 创建项目（idea/style/duration/characters/language）
- Step 2: `POST /api/projects/{project_id}/generate-outline` 生成大纲
- 篇幅映射: flash=1min/2人, short=3min/3人, medium=6min/3人, epic=6min/4人
- 未登录降级 mock（好设计，页面不依赖后端即可演示）✅
- Loading "约需 10-30 秒" + 错误红色卡片 + "重试" ✅
- build 20 路由 0 错误 ✅
- DevOps 搭 MySQL + push 已派发

---

### 2026-03-24 — TASK-STAGE1-API Review PASS

- `POST /api/projects/{project_id}/generate-outline` (~70 行)
- Ben 架构完全对齐: verify_user + get_db + Project 归属验证 ✅
- 数据映射: 11 字段 snake_case → camelCase + id 生成 + isSelected 默认 ✅
- 防御性编程: plot_points dict/str 兼容 + ending_options id fallback ✅
- 自动更新 Project.title ✅
- 零改动 Ben 现有代码 ✅
- Frontend 可开始对接

---

### 2026-03-24 — Ben 确认分工 + TASK-STAGE1-API 派发 @Backend

- Ben 确认: Pipeline API 我们做，他只做商业化后端，架构不对他修正
- TASK-STAGE1-API 派发 @Backend: `POST /api/projects/{id}/generate-outline`
- 含 Ben 架构对齐指南: auth/routing/DB/Project model 模式
- 含完整数据映射表 (Stage 1 原始 → 前端 camelCase)

---

### 2026-03-24 — AI-ML TASK-OUTLINE-PROMPT-UPGRADE Review PASS

- 5 字段 + 4 创作要点逐一验证 ✅
- summary(L184) + ending_options(L186-190) + mood(L192) + description(L221) + personality(L222)
- 现有字段全部保持不变 ✅
- DevOps push 派发

---

### 2026-03-24 — Stage 1 前后端联动任务派发

**架构决策**: 方案 B — 直接调用 StoryOutlineGenerator，不走 pipeline_orchestrator。前端做"指挥官"。
**数据映射**: Ben API 端点做 snake_case → camelCase，前端拿到直接用。

**Stage 1 实际输出分析** (对照测试数据 `1_outline.json`):
- ✅ 有: title, title_en, logline, emotional_arc, characters_overview, plot_points, unique_locations
- ❌ 缺: summary（故事简介）, ending_options（3 个结局选项）, mood（情绪标签）, characters description/personality

**3 项任务派发**:
1. @AI-ML: TASK-OUTLINE-PROMPT-UPGRADE — prompt 新增 summary + ending_options + mood + character desc/personality
2. @Ben: Stage 1 API 端点 — generate-outline + 数据映射
3. @Frontend: TASK-STAGE1-FRONTEND — StageA→API→StageB 对接（等 1+2 就绪）

---

### 2026-03-24 — 注册修复 Review PASS + DevOps 完整 push 派发

- RegisterContent.tsx: Mail→CheckCircle + "注册成功！" + 1.5s→dashboard ✅
- 模拟验证链接移除 ✅
- DevOps push 派发: 修复 + Resonance agent + 37 marketing skills + Coordinator 16 文件

---

### 2026-03-24 — Ben commit e4ada3e 全维度分析

**范围**: 29 files, +932/-162, "Implement MySQL-backed user account flows"

**分析结论**:
- API 对照: 6 项中 4 项实现，邮箱验证（MVP 不需要，邀请码=验证）+ 忘记密码（后续）⏳
- 前端: AuthContext mock→真实 API，Batch 1A-4 UI 全部保留 ✅
- 数据模型: 4 表 u_ 前缀，设计合理 ✅
- 安全: PBKDF2 + hmac + 邀请码三重校验 ✅
- 发现: RegisterContent 成功态"验证邮件已发送"与后端不一致 → 派发修复

---

### 2026-03-23 — Founder 走查 + PM 审查: 7 项修复 Review PASS

- P0: shot-gen 进度重复 bug (mockShotGenProgress 新建) ✅
- P1: verify-email → /dashboard ✅
- P1: 语音 UI 隐藏 ({false && ...}) ✅
- P1: Pricing Pro 视频合成 true ✅
- P2: 注册成功页"模拟验证"链接 ✅
- P2: 后台生成 router.push ✅
- P3: "做同款" URL query 记录待完善 📝

---

### 2026-03-22 — Batch 4 Review PASS (3/3) — 前端 mock 全部完成

- 会员等级 UI: Free/Pro(金色)/Max(即将推出) 三级视觉 ✅
- 比例选择器: 4 选项 (2:3 默认 + 3:4 小红书 + 1:1 方形 + 16:9 横屏) ✅
- Pricing 页: 完全重写 3 栏 + 8 维度对比表 + FAQ ✅
- **Batch 1A-4 前端 mock 阶段全部 Review PASS** — DevOps push 派发

---

### 2026-03-22 — Batch 3 Review PASS (4/4) + Batch 4 派发

- OCR + 语音 + 模板三合一 (StoryIdeaInput 重写) ✅
- 骨架屏 5 种业务预设 (Skeleton.tsx) ✅
- Batch 4 派发: 会员等级 UI + 比例选择器 + Pricing 页

---

### 2026-03-22 — Batch 2 Review PASS (16/16) + DevOps push 派发

- Dashboard: 生成中 banner + Credits 卡 + StoryCard 进度条 + 排序 ✅
- 故事详情: 做同款 + 播放(2s/3s/5s) + 分享(ShareModal) + 收藏 + 导出(ExportModal) + 合成视频(VideoSynthesisModal) + 删除确认(ConfirmModal) ✅
- 通知系统: Toast 全局 + 浏览器推送 ✅
- 5 个新 UI 组件独立可复用，代码质量好
- DevOps push 派发（Batch 1A+1B+2 一次性推送）

---

### 2026-03-22 — Batch 1A+1B Review PASS + Ben 通知 + Batch 2 派发

**Batch 1A+1B PM Review**: 27/30 完成 ✅ + 3 项暂缓（手机号，MVP 只要邮箱）
- 1A: StageC 4 阶段 + 角色/场景检查点 + CreateContext + mock-data ✅
- 1B: 注册(邮箱+密码+邀请码) + 登录(邮箱+密码) + 验证页 + 设置页 + CTA + logo ✅

**通知 Ben**: TEAM_CHAT 发送 6 个前端页面的数据格式说明，Ben 可开始设计后端 API

**Batch 2 派发 @Frontend**: 16 项（Dashboard 生成中状态 + 做同款 + 播放 + 分享 + 收藏 + 导出 + 视频合成 + 删除确认 + Toast + 推送通知）

---

### 2026-03-22 — Founder 产品决策 + Batch 1A+1B 派发

**Founder 产品决策记录**:
- MVP 邀请码注册流程（Landing CTA→邮箱申请→邀请码→注册→邮箱验证→创作）
- 会员等级: Free/Pro/Max（MVP 邀请码用户享 Pro）
- Credits 定价暂搁（MVP 不涉及）
- 个人主页: MVP 私人设置页，后续加公开展示页
- 5 个故事模板（含 3 个高创意+惊喜结局）

**CREATE_UX_EVOLUTION_PLAN.md 全面更新**: 新增第六章 Founder 决策 + 第七章实施策略重构

**Batch 1A+1B 正式派发 @Frontend**: 82 项前端工作的前 30 项（Create 预览流 + MVP 注册体系 + 登录 + 设置页 + logo 更新）

---

### 2026-03-19 — 双团队协作文档 + Ben 团队文件重组 + Git 工作流简化

**Coordinator 指令执行**: TODAY_FOCUS/PROJECT_STATUS/PENDING 更新 + DevOps 派发

**Ben 团队文件重组**:
- `codex-agents/` + 根目录 `CODEX.md` + `.team-brain/TEAM_CHAT_Ben.md` → `.team-brain/team_ben/`
- 文件名去 `_Ben` 后缀，目录名统一小写
- 30+ 文件路径引用全量更新（Agent 并行处理）

**Git 工作流简化 (Ben 决策)**:
- 分支保护移除（GitHub API 确认）
- 两人直接 push main，无分支/PR 流程
- CLAUDE.md + CODEX.md + TEAM_PROTOCOL.md + 全 Agent 文件同步更新

**CREATE_UX_EVOLUTION_PLAN.md 补充**: Founder 反馈纳入（后台生成 + Dashboard 详细功能 + 小红书比例研究）

---

### 2026-03-18 — 安全加固 PM Code Review PASS + 文档清理

**PM Code Review**: TASK-CORS-RESTRICT ✅ + TASK-LOG-SANITIZE ✅ (OB-5 非阻塞)
- CORS: `allow_origins=["*"]` → `["https://prefaceai.mov", "http://localhost:3000"]`
- 脱敏: 5 正则模式覆盖全部 API Key 格式，patch `builtins.print`，正常日志无误触发

**DevOps 部署审查**: ✅ PASS — `f76ac1e` 3 文件，CORS 实测（允许+拒绝），OB-5 修复确认，3 容器 healthy

**文档清理**: PENDING 3 条过期归档 (LOGO-REPLACE ✅ / DEPLOY-PREP ✅ / STYLE-THUMBNAILS ✅) + TODAY_FOCUS 更新到 03-18

---

### 2026-03-17 — TASK-BRAND-MANIFESTO Founder 终审通过

Founder 确认首页 Pipeline 模块 + About 页 V2 品牌宣言整合，文案和排版满意。
并行线全部闭环：PM 规划 → Founder 确认 → 文案指引 → Frontend 实现 → PM 审查 → Founder 终审 ✅

---

### 2026-03-17 — PM 全量审查闭环 (OB-1/2/3/4 + SAFE-DRYRUN)

**AI-ML TASK-OB1-CLEANUP**: ✅ PASS
- prompt_safety_rewrite.py 11 处 "Haiku" → "Sonnet 4.6"
- grep "Haiku" 零匹配 ✅
- 文档 5/5 更新 ✅

**Backend TASK-OB2-MODEL-SYNC + OB-3 + OB-4**: ✅ PASS
- story_generator.py L18 Haiku→Sonnet 4.6 (DEC-012 合规)
- story_generator.py L21 + alignment_service.py L44/46 gemini-3-pro→3.1-flash
- alignment_service.py L28/L34 docstring 统一 "Gemini 3.1 Flash"
- `app/` 目录 gemini-3-pro-preview 零残留 ✅
- 文档 5/5 更新 ✅

**Tester TASK-SAFE-DRYRUN**: ✅ PASS
- 7/7 验证项通过 (代码验证 + 3 链路 + 3 日志完整性)
- PM 非阻塞观察 (L304) 已修复
- 安全链路全覆盖: phase2_safe (本次) + 角色/场景参考图 (IMG-SAFETY-VERIFY 17/17)
- 文档 5/5 更新 ✅

---

### 2026-03-17 — TASK-REWRITER-CLEANUP PM Code Review 3/3 PASS

**审查范围**: 3 文件 (pipeline_orchestrator.py + prompt_rewriter.py + image_generator.py)
**审查方法**: 逐行核验 + 全 `app/` 目录 "Haiku" / "gemini-3-pro-preview" 残留扫描
**结果**: 修复 1 ✅ + 修复 2 (7处) ✅ + 修复 3 (6处) ✅ — 零残留
**OB-1**: prompt_safety_rewrite.py (AI-ML) 仍有 Haiku 字符串常量 — 后续 AI-ML 清理
**OB-2**: story_generator.py + alignment_service.py 仍有 gemini-3-pro-preview — 范围外，后续统一排查
**OB-3**: shot_validator / character_position_detection 用 Haiku — 产品运行时 OK
**通知**: @Tester TASK-SAFE-DRYRUN 可启动

---

### 2026-03-17 — Founder 反馈 + TASK-REWRITER-CLEANUP 派发 (3 项修复)

**Founder 反馈**:
1. prompt_rewriter.py 注释残留 "Haiku" → 需改为 "Sonnet 4.6" (技术债)
2. 备用模型换 `gemini-3.1-flash-preview` (Founder 决策，Flash 同级成本，最新版)

**PM 发现**: `gemini-3-pro-preview` 可能已于 03-09 下线，备用链路已失效 — 修复 3 升级为紧急

**任务扩展**: 原 TASK-SAFE-INTEGRATION (1 行) → TASK-REWRITER-CLEANUP (3 项, ~13 行, 3 文件)
- 修复 1: pipeline_orchestrator.py L375 接入 phase2_safe
- 修复 2: prompt_rewriter.py + image_generator.py 注释清理
- 修复 3: prompt_rewriter.py 备用模型 → gemini-3.1-flash-preview

**派发**: @Backend (群聊 03-17 11:00)，Tester dry-run 不变

---

### 2026-03-17 — DevOps R8B 审查 PASS + phase2_safe 集成修复派发

**DevOps**: 3 commits (935f0b0→ec3b4fd) + VPS 5/5 + 代码零未提交 — ✅ PASS
**phase2_safe 分析**: pipeline L375 调用非 safe 版本 → Shot CONTENT_SAFETY 无 PromptRewriter 恢复 — 集成遗漏确认
**修复**: Backend 1 行 (`phase2` → `phase2_safe`)，签名兼容无需改参数
**验证**: Tester dry-run — R8 数据 + mock generate_image + 3 条链路 (正常/改写成功/改写失败)

---

### 2026-03-16 — Tester 17/17 确认 + DevOps TASK-DEPLOY-R8B 派发

**Tester 审查**: 17/17 PASS (单元5 + 审计6 + API 3 + 模板3), PM 与 Tester 全部一致
**关键发现**: "No people"前置优化使 API 测试首次即通过 — L2/L3 恢复链路是"保险"非"常态"
**DevOps 派发**: 13 代码文件 + brand 资源 → commit + push + VPS deploy

---

### 2026-03-16 — AI-ML 小补充审查 PASS

**正则** `re.sub` (L722-723): 模式正确，import re L13 已有 ✅
**"No people" 前置**: exterior L827 + interior L863，末尾无残留 (grep 确认仅 2 处) ✅

---

### 2026-03-16 — N13-FIX + IMG-SAFETY Code Review PASS + 派发

**AI-ML 审查**: 5 类 75 词条 + SCENE_REF/CHAR_REF 改写模板 + 辅助函数 — ✅ PASS
**Backend 审查**: N13-FIX + L1 (2处) + L2 简化重试 + L3a 场景改写 + L3b 角色改写 — ✅ PASS (5 文件)
**2 项小补充派发 @AI-ML**: 正则残留清理 + "No people" 前置
**4 项验证测试派发 @Tester**: N13 + 日志 + 场景恢复 + 角色恢复

---

### 2026-03-16 — TASK-IMG-SAFETY-RETRY 分工修正 (AI-ML + Backend)

**初版错误**: 全部派给 Backend，忽略了 prompt 工程是 AI-ML 专长
**深入分析**: 现有 PromptRewriter 6 类关键词 (DEATH/VIOLENCE/BLOOD/WEAPON/BODY/EMOTION) 只覆盖 Shot 叙事，R8 `rural_market_entrance` 触发词 (crowds/chickens/smoke) 一个都不匹配
**修正派发**:
- @AI-ML: 5 项交付物 (新关键词+场景改写模板+角色改写模板+简化策略+结构建议)
- @Backend: N13-FIX + L1 (可立即) + L2/L3 基础设施 (等 AI-ML)
- @Tester: 3 项小型验证 (等 AI-ML + Backend)

---

### 2026-03-16 — TASK-BRAND-MANIFESTO + TASK-LOGO-REPLACE PM 审查: 全部 PASS

**Pipeline.tsx**: 6/6 改动逐字一致 (P1-P5 文案 + 技术标签删除)
**AboutContent.tsx**: V2 宣言 17 句逐字核验 17/17 一致 + 理念段/三卡片/技术基座/PageHero 全部 PASS
**Logo 替换**: 4/4 文件 (Header/SubPageHeader/CreateHeader/Footer) + Sparkles 零残留 + favicon 已更新
**Frontend 自主优化**: 核心团队位置从 Mission 后调到 Values 后，信息架构更合理
**构建**: 18/18 路由通过
**可提交 Founder 终审**

---

### 2026-03-16 — R8 E2E PM 独立复核: 有条件通过

**复核范围**: 1_outline.json + storyboard excerpt + r8_report.md + 8 角色参考 + 7 场景参考(抽4) + 10 shot + pipeline_log + 代码路径
**44 维度**: 42 PASS + 1 PARTIAL (D15) + 1 FAIL (N13) — 与 Tester 44/44 完全一致
**Founder 3 关注**: "圩日"文化正确 + shot_06/08 远景偏差属 NB2 局限 + N13 同意 Tester 修复方向
**后续**: N13-FIX 派发 @Backend (spouse_of 对称补全, pipeline_orchestrator.py)

---

### 2026-03-16 — TASK-BRAND-MANIFESTO 全流程完成（方案→确认→派发）

**任务来源**: Coordinator 代 Founder 指令 (03-16 11:00)
**阅读范围**: `BRAND_MANIFESTO_EXPLORATION.md` (540 行) + `Pipeline.tsx` (159 行) + `AboutContent.tsx` (228 行)
**11:30 方案制定**: Pipeline 方案 B + About V2 + 技术标签迁 About 页
**12:00 Founder 确认**: 3 决策点全部通过
**12:00 派发 Frontend**: 详细文案指引 — Pipeline 5 处改动 (P1-P5) + About 5 段改动 (A1-A5)
**关键文案**:
- Pipeline slogan: "每个人脑子里都在放电影"
- Pipeline core: "你说出来。所有人看见。"
- About 使命段: V2 完整宣言原文
- About 理念段: "想象力，不该被困住"
- About 三卡片: "你的画面，任何风格" / "说出来就够了" / "每个人天生会讲故事"

---

### 2026-03-16 — TASK-DEPLOY-R8 PM 独立复核 PASS

**复核范围**: DevOps 3 commits (4926a9a + b98a6df + 73f8a78) + VPS 部署
**7 维度**: commit 覆盖 (12/12+OB-1) + 逐任务核验 + VPS 验证 (6/6) + rsync 排除 (9 项) + 问题处理 (3/3) + 三端一致 (73f8a78) + 额外文件 (T29-T37 合并)
**1 非阻塞**: commit message 未包含 T29-T37 范围
**结论**: ✅ PASS，Tester 可以开始 R8 E2E

---

### 2026-03-13 — OB-1 Code Review PASS + DevOps 部署派发

**OB-1 审查**: shot_validator.py 4 处返回路径 × 7 字段 = 28/28 完全一致 ✅
**DevOps 派发**: TASK-DEPLOY-R8 — 11 项代码改动 + OB-1 → commit + push + VPS deploy
**执行顺序**: OB-1 ✅ → DevOps 部署 → Tester T-J + R8 E2E

---

### 2026-03-13 — Phase 6 Code Review: 1/1 PASS (全部 12/12 完成)

**审查范围**: T-H-Backend (`shot_validator.py` 全文 218 行)
**6 处改动**: Q3 自然度 prompt + PROPS 编号 + Response 新字段 + max_tokens + Phase 1 日志 + result_dict
**与 T-H-AIML 设计一致性**: Prompt 文本/JSON 字段/max_tokens/Phase 1 行为 — 四项逐字一致
**OB-1 非阻塞**: 3 处 early-return 缺 `has_visual_unnaturalness`/`unnaturalness_details`（Phase 2 前修复）
**全部成绩**: Phase 2 (8/8) + Phase 4 (3/3) + Phase 6 (1/1) = **12/12 PASS**

---

### 2026-03-13 — Phase 4 Code Review: 3/3 PASS

**审查范围**: Phase 3 全部 3 项任务（2 文件 + 1 设计文档）
**Backend 2 项**: T-C-Backend(signage_text 全链路) ✅ + T-I(Prompt Pre-Check v1) ✅
**AI-ML 1 项**: T-H-AIML(自然度 prompt 设计) ✅
**关键审查点**: T-C-Backend 数据流 4 层传递验证 + T-I 4 维度预检逻辑 + T-H-AIML 风格无关原则
**结论**: 0 阻塞项，0 附注，Phase 5 可启动

---

### 2026-03-13 — Phase 2 Code Review: 8/8 PASS

**审查范围**: Phase 1 全部 8 项任务代码改动（4 文件 5 处修改）
**Backend 4 项**: T-B(MAX_SHOT_RETRIES) ✅ + T-A(off_screen 文字修复) ✅ + T-K(ShotValidator prompt) ✅ + T-D(关键词扩展) ✅
**AI-ML 4 项**: T-E(Rule#10) ✅ + T-F(Rule#11) ✅ + T-G(Rule#12) ✅ + T-C-AIML(signage_text) ✅
**附注**: T-D 关键词 ~120 vs storyboard_director ~149，差 ~30 词（character 类），仅影响报告完整度
**结论**: 0 阻塞项，Phase 3 可启动

---

### 2026-03-13 — 交叉核对 + 风险评估 + 正式派发 (11 项任务)

**交叉核对**: 3 张清单 (PM 发现 12 项 × Founder 6 板块 × 10 项任务) 逐项比对，发现 1 遗漏 → 新增 T-K (ShotValidator 人群容差)
**风险评估**: 11 项任务 × 5 维度深度分析。结论：零高风险，T-H 建议 Phase 1 仅日志
**正式派发**: 11 项任务 (T-A~T-K)，6 Phase 执行计划，3 Agent 并行

---

### 2026-03-13 — Founder 六板块反馈分析 + 任务清单

**输入**: Founder 6 大板块反馈 + 4 项并行代码研究
**产出**: 10 项任务派发清单 (T-A ~ T-J) → 交叉核对后扩展为 11 项
**关键技术发现**:
- Shot_08 确认 NB2 原生渲染（非 text_overlay_service），Bug 在 image_generator.py build_native_text_prompt() 未过滤可见 speaker
- ShotValidator 当前 3 维度全部需图像验证，提议 4 个 prompt 预检维度 (P1-P4)
- 场景参考图 label 泄漏根因: display_name → _detect_signage_name() → SIGNAGE 注入，建议方案 A
- Prompt Quality Report 关键词 8→40 扩展建议
- MAX_SHOT_RETRIES 2→1 数据支撑（R7 第 3 次尝试无一通过）

---

### 2026-03-13 — R7 PM 独立复核（有条件通过）

**审查范围**: 全部 JSON + MD + 10 shot 图 + 8 角色参考图 + 6 场景参考图 + pipeline_log + prompt_quality_report + excerpts
**Tester 结果**: 36/36 PASS → PM 同意 33 项
**新发现 1 Bug**: Shot_08 off_screen_speaker 文字双重渲染（image_generator.py build_native_text_prompt 代码 Bug）
**新发现 2 Prompt 缺失**: Shot_03 off-screen 肢体接触描述 + Shot_04 空间方向矛盾
**修正 Tester S5**: Shot_08 文字重复不是假阳性，是真实 Bug（ShotValidator dupes=True 确认）
**3 测试脚本不准**: N12 多角色 shot 未识别 / N14 color_palette 路径错误 / N15 日志格式不匹配
**3 平台问题**: 场景参考图标签泄漏 / ShotValidator 人群失效(5/10用尽重试) / 测试覆盖仅 2/6 场景
**Founder 建议评估**: "画面自然度检测"正面评估，建议 P2 纳入 ShotValidator 扩展

---

### 2026-03-13 — Founder 确认 + R7 E2E 派发

**Founder 确认**: Phase 2 Code Review 10/10 PASS 通过 ✅
**Minor 项结论**: 无遗留 bugs（OB-T29 已修复，3 项观察不修改）
**R7 E2E 派发**: TASK-E2E-REGRESSION-R7 @Tester — 1 故事 × 10 shots × 36 维度
**R7 新增 N7-N15**: 画外音标记+渲染(T29+OB-T29) / 家庭关系传递(T32) / 亲属称谓(T37) / 镜头完整性(T34) / 空间锚定(T35) / 关系一致性(T33) / 英文色板(T36) / 招牌注入(T31)
**验收标准**: ≥ 32/36 PASS + 0 FAIL

---

### 2026-03-12 — Phase 2 全量 Code Review (T29-T37 + OB-T29)

**全量审查**: 10/10 PASS — 9 文件逐行阅读 + 跨文件交叉验证 + 跨任务冲突检测
**新审查**: T34(Plan A 3条规则+Plan B 关键词映射+eye_level豁免) ✅ / T37(Rule 5 KINSHIP 引用T32关系数据+旁白覆盖) ✅ / OB-T29(复合类型off_screen→monologue+偏移同步) ✅
**交叉验证**: storyboard_director.py 5任务零冲突 + screenplay_writer.py 数据在前规则在后 + pipeline_orchestrator.py 不同区域
**3 Minor 观察**: 全部不阻塞(T31中文名+T31 no text+T34 em-dash)

---

### 2026-03-12 — Phase 1b Backend 代码审查 + AI-ML 派发

**Phase 1b 审查**: T29 ✅ PASS + T32 ✅ PASS — 逐行审查 5 文件(storyboard_director/image_generator/text_overlay_service/pipeline_orchestrator/screenplay_writer)
**1 Minor 观察**: 备用通道复合类型 dialogue 子项未检查 off_screen_speaker（生产用 native text，不阻塞）→ 记录为 OB-T29 让 Backend 顺手修
**AI-ML 派发**: T34(shot_size Plan A+B) + T37(称谓歧义规则)

---

### 2026-03-12 — Phase 1a 代码审查 + Phase 1b 派发

**Phase 1a 审查**: 5/5 PASS — T30(日志) + T31(招牌注入) + T33(关系校验) + T35(空间锚定) + T36(色板英文)
**2 Minor 观察**: T31 仅中文名(NB2更清晰，不修改) + "no text"全局移除(风险极低，不修改)
**Phase 1b 派发**: @Backend T29+T32 先 → @AI-ML T34+T37 后

---

### 2026-03-12 — Founder 决策 + T29-T37 派发 + 执行计划更正

**P-R1 TextOverlay 确认**: pipeline_orchestrator.py TextOverlay 分支仅备用模式（`use_native_text=False`），生产不受影响
**Founder 决策**: P-R1~P-R4, P-R6~P-R10 全部修复，P-R5(NB2漂移)确认模型特性不修复，P-R6提升P1
**任务派发**: T29-T37 共 9 个任务
**全维度改进方向**: 每个 P-R 项含根因分析 + 具体改进方案 + 涉及文件 + 红线约束
**执行计划更正**(Founder 要求): 全并行 → Phase 1a/1b 分阶段，消除 3 个文件冲突风险:
- Phase 1a(并行): @Backend T30+T31 / @AI-ML T33+T35+T36
- Phase 1b(顺序): @Backend T29+T32 先 → @AI-ML T34+T37 后

---

### 2026-03-12 — R6 独立复核完成

**方法**: 逐字审核全部 JSON/MD (13 文件) + 逐张查看 24 张图片 + pipeline_log 全文 + Tester progress 交叉验证
**PM 判定**: 21/27 PASS + 4 PARTIAL + 2 FAIL (不同意 Tester 27/27)
**质量**: 3.8/5
**调降维度**: D1(角色一致性) / D3(参考图质量) / D5(text_overlay) / D8(对话匹配) / S1(角色数量) / N6(道具检测)
**9 项平台级发现**: P-R1(T5降级逻辑P1) + P-R2(ShotValidator零日志P1) + P-R3(场景名称P2) + P-R4(关系校验P2) + P-R5(NB2漂移P2) + P-R6~P-R9(P3)
**Founder 7 项观察**: 全部确认
**T23-T28 验证**: T23✅ T24✅ T25✅ T26✅ T27✅ T28❓

---

### 2026-03-12 — R6 E2E 派发

**派发给**: @Tester (TASK-E2E-REGRESSION-R6)
**规格**: 1 故事 × 10 shots（成本考量，R5 Story B ink/2人质量已高无需复测）
**参数**: illustration / 4 角色 / 10 shots / **全新题材**（与历史 9 个测试故事完全不同）
**维度**: 27 项 (D1-D16 + S1-S5 + N1-N6)
**R6 新增**: N1 角色称谓正确性 / N2 对话自然度 / N3 背景多样性 / N4 室内纵深 / N5 参考图模型 / N6 道具检测
**验收标准**: ≥ 24/27 PASS + 0 FAIL

---

### 2026-03-12 — Phase 2 Code Review T23-T28 + Bug 修复

**审查**: 4 PASS / 1 FAIL / 1 PARTIAL → PM 直接修复 2 个 Bug
**Bug #1 (T24 Critical)**: `_build_scene_prompt()` 字段名不匹配 Stage 1 输出（`id`/`name`/`age_group` → 应为 `name_suggestion`/`age_range`/`family_role`），CHARACTER RELATIONSHIPS 块永远为空。PM 修复: 正确字段名 + 新增 `family_relationships` 全链路传递。
**Bug #2 (T28)**: `shot.get("key_props", [])` 永远空列表。PM 修复: 改从 `shot["composition"]` 提取。
**Import**: 6/6 ✅

---

### 2026-03-12 — T23-T28 正式派发

**任务**: 6 tasks (T23-T28), 涉及 6 文件
**执行者**: @Backend (T23+T24+T28) + @AI-ML (T25+T26+T27)
**计划**: Phase 1 全并行 → Phase 2 PM Code Review → Phase 3 R6 E2E
**前置**: 安全评估 PASS + 模型检查 PASS + Founder 批准

---

### 2026-03-12 — 安全影响评估 + 模型能力检查 + 成本分析

**安全评估**: P-S1~P-S5 全部 prompt 追加型，风险极低，不触碰核心架构
**模型检查**: Sonnet 4.6 / Haiku 4.5 / Flash / NB2 全部胜任
**关键发现**: Stage 4 没拿到 outline.characters_overview（P-S1 技术根因）
**成本分析**: 参考图切 NB2 增加不到 $1/故事，Founder 批准
**ShotValidator**: 缺少道具存在性检测，纳入 T28

---

### 2026-03-12 — PM 独立深度审查 R5 完成

**方法**: 20 shots + 12 角色参考图 + 7 场景参考图逐张查看 + JSON 逐字审核 + 代码追踪
**判定**: R5 验收通过。发现 6 项平台系统性问题 (P-S1~P-S6)
**Founder 确认**: P-S1~P-S5 改进方向同意，P-S6 暂不修复

---

### 2026-03-11 — Phase 3 R5 E2E 正式派发

**派发给**: @Tester
**规格**: 2 故事 × 10 shots，21 维度（D1-D16 + S1-S5）
**与 R4 相同参数**: illustration/4人 + ink/2人

---

### 2026-03-11 — Phase 2 Code Review 全部 PASS + T17-FIX 完成

**审查范围**: 6 文件（shot_validator.py 新建, pipeline_orchestrator.py, storyboard_director.py, reference_image_manager.py, scene_reference_manager.py）
**结果**: T17-T22 全部 PASS
**T17-FIX**: `shot_validator.py` 同步→异步（`Anthropic` → `AsyncAnthropic`），import 验证 ✅
**Founder 决策**: T17 异步已改 / T18 双重注入保守留着（位置 B 为死代码）

---

### 2026-03-11 — T17-T22 平台级改进任务派发

**任务**: 6 tasks (T17-T22), 6 files, 1 new — 覆盖 S1-S6 全部改进方向
**执行者**: @Backend (T17+T20+T21+T22) + @AI-ML (T18+T19)
**计划**: Phase 1 全并行 → Phase 2 PM Code Review → Phase 3 R5 E2E

---

### 2026-03-11 — Step 10 PM 独立深度审查完成

**审查范围**: 60+ 张图片逐张查看 + storyboard/outline/characters JSON 逐字阅读 + 代码追踪

**结果**: 同意 Tester 14/16 PASS + 2 PARTIAL。R4 验收通过。

**输出**:
- 7 项平台系统性问题 (S1-S7) 分级报告
- 风险评估：全部改进无"修东墙补西墙"风险
- Founder 确认 6 项改进方向

**附加发现**:
- with_text_images/ 在 use_native_text=True 下冗余（与 raw 完全相同）
- refs/ 文件夹为空，属遗留空目录
- Story B (2角色) 4.7/5 远超 Story A (4角色) 3.8/5 — 角色数量是核心变量

---

### 2026-03-10 14:25 — PRO_MODEL 命名确认 PASS + CLAUDE.md 同步 + Step 9 派发

**Backend 代码确认**: `image_generator.py` PRO_MODEL 零残留，NB2_MODEL 定义+8引用+docstring 清理正确，`test_nb2_switch.py` 4 处同步 ✅

**PM 额外完成**: `CLAUDE.md:390` 模型配置说明 `PRO_MODEL → NB2_MODEL` 同步

**Step 9 派发**: @Tester E2E R4，16 项验证维度

---

### 2026-03-10 14:05 — 全局 Double-Check + CLAUDE.md 修正

**工作链验证**: Step 7→8.5 全部 7 文件变更逐一确认，无遗漏无冲突 ✅

**全局健康检查**:
- [P3] PRO_MODEL 命名混乱 → 派发 @Backend 快速修复
- [排除] `_get_character_type()` 字段问题 — R3 实测确认 Stage 2 输出 `character_type`，非 bug

**CLAUDE.md 修正** (PM 直接完成):
- 角色数据示例: `"type": "human"` → `"character_type": "human"`
- 字段说明: `character_type 或 type` → `character_type`
- "已踩过的坑": 更正为实际正确做法

---

### 2026-03-10 13:55 — Step 8.5 PM 快速复核: T13-INT + T12-UNIFY

**审查范围**: 2 文件 2 项微型修复

**结果**: 2/2 PASS

- **T13-INT**: `storyboard_director.py` L20 import + L401/L668 两处注入 `COMIC_MODE_NARRATIVE_RULES`，与 `NARRATION_TO_VISUAL_EXTRACTION_RULES` 完全同模式 ✅
- **T12-UNIFY**: `pipeline_orchestrator.py` L347 单一 `if use_native_text:` 分支替代原 T4+T12 两分支，else 备用通道保留 ✅

Step 8 + 8.5 全部通过 → Step 9 E2E R4 待派发

---

### 2026-03-10 13:37 — Step 8 PM Code Review: T11~T16

**审查范围**: 7 文件 6 项任务

**结果**: 5/6 PASS + 1 集成缺口 + 1 代码质量改进

| # | 任务 | 判定 | 说明 |
|---|------|------|------|
| T11 | 移除参考图 PIL 标签 (×2文件) | ✅ PASS | 调用移除正确，函数体保留，无遗漏 |
| T12 | TextOverlay native_text 跳过 | ✅ 有条件 PASS | 功能正确，两分支未统一（T12-UNIFY） |
| T13 | 条漫叙事自足 prompt | ⚠️ 常量 PASS / 集成 FAIL | 常量好但未被 import（T13-INT 派发 Backend） |
| T14 | 跨年龄风格统一 | ✅ PASS | 两方法正确追加，placement 在 StyleEnforcer 前 |
| T15 | 气泡去重指令 | ✅ PASS | EXACTLY ONCE 正确追加，仅 dialogue 非空时触发 |
| T16 | OB-6 降级分支 | ✅ PASS | narration_with_dialogue 正确加入 |

**后续**: Step 8.5 @Backend T13-INT + T12-UNIFY → PM 快速复核 → Step 9

---

### 2026-03-10 — Step 6 PM 独立深度审查 + Step 7 修复任务派发

**审查范围**: 62 张图片逐张查看 + 完整 JSON 数据 + 全链路代码追踪

**关键发现**:
1. **Tester 准确性**: Story A 6/10 shot 描述事实性错误（JSON 数据交叉验证）
2. **标签泄露根因**: `scene_reference_manager.py:275-276` 动态 PIL 标签 → Gemini 复现（SQ-1 设计缺陷）
3. **双重渲染根因**: T8 在 `use_native_text=True` 下调用 TextOverlay → 违反 DEC-012（TextOverlay 仅作备用）
4. **NB2 气泡重复**: 100% 模型问题（prompt 追踪: 每行对话只送一次）
5. **Story A 叙事弱**: 管道对多角色故事的结构性短板 + 条漫 narration 未渲染
6. **OB-6**: 确认真实代码漏洞（narration_with_dialogue 降级缺失）
7. **OB-7**: T7 warning-only 是合理设计
8. **OB-8**: partial match fallback 有价值，非冗余

**Founder 反馈集成**:
- DEC-012 TextOverlay 备用方案定位重新确认
- 条漫叙事: 先通过 prompt 优化 thought/dialogue 叙事承载力，再考虑渲染 narration
- 风格统一: 通过 prompt 约束解决跨年龄风格分裂
- NB2 气泡重复: 确认模型问题后再加抑制指令

**Step 7 任务派发**: T11-T16（@Backend 3 项 + @AI-ML 3 项并行）

---

### 2026-03-09 17:30 — Step 4 PM Code Review: 22/22 PASS + Step 5 派发

**审查范围**: 4 文件 22 检查点（storyboard_director.py 11处 + image_generator.py 5处 + pipeline_orchestrator.py 4处 + screenplay_writer.py 2处）

**结果**: 22/22 PASS, 0 阻塞

**任务级验证**:
- T5 (7处): `_validate_storyboard()` characters 参数 + 中文名→char_id 映射 + regex speaker 提取 + 降级逻辑(dialogue→thought, compound→narration_with_thought) + `direct()` 调用 — PASS
- T6 (5处): `build_dialogue_scene_embed()` characters_in_scene 参数 + `_is_speaker_visible()` + 安全回退 + 调用方传入 chars_visible — PASS
- T7 (4处): `_rebalance_text_types()` 方法 + narration>15%/thought<10% 警告 + `direct()` 调用 — PASS
- T8 (3处): compound type 拆分 + 结构化/纯文本双路处理 + 仅非 dialogue 子项走 TextOverlay — PASS
- T9 (1处): `self.use_native_text = True` 单一配置源 — PASS
- T10 (2处): thought ≥20% 双重约束 (L404 + L430) — PASS

**跨组件验证**:
- T5 regex 与 `_extract_speaker_name()` 匹配确认
- T6 安全回退: 无 characters_in_scene 时默认返回 True（不误删有效对话）
- T9 配置源覆盖 L331(dialogue skip) + L345(compound split) 两条路径

**非阻塞观察 (3 项)**:
- **OB-6 [P3]** T5 `narration_with_dialogue` 降级遗漏: L1044 检查了此类型 speaker visibility，但 L1078 降级分支只处理 `dialogue_with_thought` 和 `dialogue_with_narration`。此类型极其罕见，不阻塞。
- **OB-7 [P3]** T7 仅警告不自动修改: PM 原始规格建议"触发调整"，Backend 实现为打印警告。实际更安全——自动修改可能引入新错误。Stage 4 SELF-CHECK 是主要纠偏机制。
- **OB-8 [Info]** T6 `_name_to_id` 冗余循环: L245-247 `for name_part in [char_name]` 单元素循环，注释说"支持部分匹配"但代码未实现。无害（`_is_speaker_visible` 已有 partial match fallback）。

**下一步**: @Tester Step 5 E2E 回归验证 (10 维度) → PM Step 6 独立复核

---

### 2026-03-09 17:15 — Step 3 任务扩展: T8/T9/T10 补充

Founder 要求 5 项非阻塞观察全部定义为正式任务：
- **T8 [P2] @Backend**: pipeline compound type 拆分渲染（OB-1 → dialogue_with_thought 重复气泡）
- **T9 [P3] @Backend**: use_native_text 参数同步（OB-2 → 硬编码风险）
- **T10 [P3] @AI-ML**: Stage 3 thought 最低比例强化（OB-4 → "至少1个" 改为 "≥20%"）
- OB-3 → T5, OB-5 → T6 已有覆盖

Step 3 扩展为: @Backend T5+T6+T7+T8+T9 + @AI-ML T10（并行）

---

### 2026-03-09 17:00 — Step 2 PM Code Review: 14/14 PASS

**审查范围**: 2 文件 14 处修改（screenplay_writer.py 7处 + storyboard_director.py 6处 + pipeline_orchestrator.py 1处）

**结果**: 14/14 PASS, 0 阻塞

**深度验证**:
- T1 (6处): type 字段 + 覆盖约束 + 分布目标 + thought 示例 + 写法指导 + 输出要求 — 全部 PASS
- T2 (6处): _build_scene_prompt + _build_prompt 各 3 处（THOUGHT GENERATION + SPEAKER VISIBILITY + SELF-CHECK）— 两处完全一致 PASS
- T3 (1处): PLOT POINT COVERAGE 约束块 — PASS（与循环结构双保险）
- T4 (1处): dialogue+native_text 条件跳过 — PASS（逻辑正确 + 目录结构一致）
- **跨阶段数据链**: Stage 3 type 字段 → Stage 4 dialogue_beats 传入 → Mapping Logic 消费 — 全链路完整

**非阻塞观察**: 5 项（OB-1 dialogue_with_thought 边界 P2，其余 P3/Info）

**下一步**: @Backend Step 3 T5+T6 → PM Step 4 Review

---

### 2026-03-09 15:39 — F1-F5 深挖分析 + 7 项修复任务派发

**Founder 要求**：对 PM 复核发现的 F1-F5 逐一深挖根因。

**深挖结果**：
- **F1**: ScreenplayWriter prompt 缺 plot_points 1:1 硬约束 → T3
- **F2**: 双层问题——NB2 偶发(2 气泡) + pipeline_orchestrator 代码 bug(第 3 个气泡) → T4
- **F3+F4 同根**：Stage 3 dialogue_beats 覆盖率仅 52-63%，无 thought 类型；Stage 4 兜底逻辑将无对话 beat 全标为 narration。大量 narration 语义上其实是 thought → T1+T2
- **F5 升级 P3→P1**：全量扫描发现 6/30(20%) speaker 错位。LLM 用电影思维做漫画分镜（反应镜头+画外音），整条链路零验证 → T2+T5+T6
- **关键洞察**：F3/F4/F5 是同一系统性问题的三个症状——Stage 3 素材供给不足 + dialogue ≥60% 目标逼 LLM 硬塞

**派发 7 项任务**：T1-T3(@AI-ML P0) + T4(@Backend P0) + T5-T6(@Backend P1) + T7(@Backend P2)
**执行顺序**：Step 1(并行) → Step 2(PM Review) → Step 3(Backend P1) → Step 4(PM Review) → Step 5(Tester E2E) → Step 6(PM 复核)
**报告**：TEAM_CHAT 20075+ 行

---

### 2026-03-09 15:00 — PM 独立深度复核: TASK-E2E-REGRESSION-R2

**审查范围**: 逐一审查两组完整数据链（16 个数据文件 + 40 张图片）。

**审查清单** (每个故事各 8 文件):
- 1_outline.json, 2_characters.json, 3_screenplay.json, 4_storyboard.json (text_overlay)
- 5_image_results.json, summary.json, reference_images_log.json, prompt_quality_report.md
- 角色参考图 (12张) + 场景参考图 (8张) + shot 图片 (20张) = 40 张图片

**5 项修复验证**: 全部有效 ✅
| Issue | 修复前→修复后 | 结论 |
|-------|-------------|------|
| P0 text_overlay | 0/20→20/20 | ✅ 架构缺陷已根治 |
| P1 模型配置 | Gemini→Claude primary | ✅ Stage 1-4 统一 |
| P1 标签泄露 | 2/20→0/20 | ✅ 修复确认 |
| P2 三手 | 1/20→0/20 | ✅ 修复确认 |
| P2 乱码 | 5/20→1/20 | ✅ CONDITIONAL PASS |

**5 项独立新发现**:
- F1 [P1] Story B crisis 场景被 ScreenplayWriter 丢弃 (6→5 scene)
- F2 [P2] Shot 6 对话气泡重复渲染 (NB2 偶发)
- F3 [P2] narration 超标 (40%/30% vs ≤15%)
- F4 [P2] thought 不足 (0%/8.7% vs 10-20%)
- F5 [P3] 气泡 speaker 与画面焦点角色不匹配

**综合评分**: Story A 4.5/5, Story B 4.75/5, **平均 4.63/5**
**与 Tester 对比**: PM 4.63 vs Tester 4.65 (差异 0.02)
**亮点**: Story B ink 风格系统最佳表现; Shot 10 可作产品宣传素材
**报告**: TEAM_CHAT 19874-20074 行

---

### 2026-03-09 12:30 — Founder 决策落地 + Backend/Tester 双派发

**Founder 决策**: Stage 1-4 备用模型统一改为 Gemini 3 Flash（成本和性价比考量）。
- 派发 @Backend TASK-BACKUP-MODEL-FLASH: 3 文件 Stage 1-3 备用 Pro→Flash
- 派发 @Tester TASK-E2E-REGRESSION-R2: 2 故事×10 shots, 9 维度验收（前置: Backend 完成后）
- 全文档同步: TEAM_CHAT + pm-progress×3 + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync

---

### 2026-03-09 12:00 — Code Review: Backend Issue #2 + AI-ML Issues #1/#3/#4/#5

**审查范围**: 2 文件 14 处修改，5 项 E2E 回归问题修复。

| 来源 | 文件 | 修改数 | 结果 |
|------|------|--------|------|
| Backend | storyboard_director.py | 4 处（模型配置+调用顺序+style_preset） | PASS |
| AI-ML | storyboard_director.py | 8 处（dialogue_beats+text_overlay schema+Rule#9） | PASS |
| AI-ML | storyboard_prompts.py | 2 处（标签防复制+TEXT-FREE） | PASS |

**深度验证**:
- 下游消费链: 3 消费者（TextOverlayService + dialogue_embed + native_text）与 schema 100% 匹配
- 两套 prompt 路径一致性: 规则+schema 完全一致
- TEXT-FREE 与 use_native_text 兼容性: "unless explicitly requested" 逃生口正确覆盖

**结论**: 14/14 PASS, 0 阻塞, 1 项非阻塞观察（Stage 4 备用 Flash vs Pro）

---

### 2026-03-06 17:30 — E2E 回归测试深度分析（Founder 要求的独立洞察）

**分析范围**: Founder 指出的 3 个关键问题 + 20 张图片逐张审查

**根因分析**:
1. **[P0] text_overlay 缺失** — Stage 4 schema 从未定义 text_overlay（整个 TASK-PROMPT-BUBBLE 链条为死代码）
   - 代码证据: `storyboard_director.py` 全文零次出现 "text_overlay"，git 四个版本均无
   - 之前 3/4 测试有 text_overlay 是 LLM 非确定性"自由发挥"
   - Stage 3 `dialogue_beats` 数据存在但未传递到 Stage 4 output
2. **[P1] "Scene:" 文字泄露** — `scene_reference_manager.py:275` PIL 标签被 NB2 复制
   - `storyboard_prompts.py:1446-1449` 无"勿复制标签"指令
3. **[P2] shot_01 三只手** — image_prompt 描述单角色同时两个手部动作

**额外发现**:
- DEC-012 模型未落地: Stage 4 用 Gemini 3 Flash，非 Sonnet 4.6
- NB2 多张图生成乱码文字: 缺少 TEXT-FREE 约束
- Story B 第 3 角色未在 10 shots 内出现

**20 图审查**: Story A 3.9/5 角色一致性 + Story B 3.8/5 角色一致性, 风格均 4.5/5

**交付**: TEAM_CHAT 详细报告 + 6 项优先级排序 + 修复建议
**文档同步**: TEAM_CHAT + pm-progress×3 + PENDING + TODAY_FOCUS + PROJECT_STATUS

---

### 2026-03-06 16:15 — Founder 批准部署 + TASK-DEPLOY-EXEC 派发 @DevOps

- Founder 批准 Docker Compose 部署方案
- 正式派发 @DevOps 执行 VPS 实际部署（Step 1-4）
- 前置依赖: D1 Frontend `next.config.mjs` output: 'standalone'
- 备忘记录: Tester E2E 后推进 Phase 4.5 视频合成 + 前后端联调 D5
- 文档同步: TEAM_CHAT + pm-progress×3 + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync

---

### 2026-03-06 16:00 — TASK-DEPLOY-PREP Step 3 二次审核 PASS + TASK-RESPONSIVE-OPT 复验 PASS + Tester E2E 派发

**TASK-DEPLOY-PREP Step 3 二次审核**:
- 4 项 PM 修改建议落实验证: R1 worker profiles ✅ / R2 CORS D6 ✅ / R6 version 移除 ✅ / Nginx HTTPS ✅
- Nginx HTTPS 8 维度深度验证全部 PASS
- 1 项非阻塞建议: Step 4 验证清单容器数描述不一致
- 方案可提交 Founder 最终批准

**TASK-RESPONSIVE-OPT PM 复验 (4.5/5)**:
- 7 文件逐一代码审查: DashboardContent / Showcase / HeroSection / StoryDetailContent / StageB / StageD / Header
- 触控目标符合 Apple 44px 标准，断点统一 sm: (640px)，构建 18 路由 0 错误

**TASK-E2E-REGRESSION 派发 @Tester**:
- 2 个故事 × 10 shots，不同题材+风格，7 维度验收
- 覆盖: speaker_format + text_language + prompt 精简 + 对话嵌入 + SQ 改进

**文档同步**: TEAM_CHAT + pm-progress×3 + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync

---

### 2026-03-06 15:26 — TASK-BUBBLE-SPEAKER-FORMAT-DEPLOY PM Code Review PASS

**任务**: PM 全维度 Code Review Backend 的生产代码修改

**审查内容**:
- `image_generator.py:848-853` 单处修改（6 行）
- 12 维度深度审查: 参数正确性 / 类型链验证（4 层函数签名逐一对齐）/ 数据源保障（CharacterDesigner name_en required）/ 回退安全性（3 层防护）/ 死代码审计 / Safe wrapper 兼容 / 复合类型覆盖 / Pipeline 调用验证 / R2 测试对等性 / 边缘场景（3 种场景）/ 修改范围 / 派发一致性

**结论**: **PASS — 零问题**

**闭环**: speaker_format 功能完整闭环
- AI-ML 代码实现 (`build_dialogue_scene_embed` + `_resolve_speaker_label` + `_TEXT_LANGUAGE_CONFIG`)
- R2 30 张图验证 (B 组 english 10/10 成功)
- Founder 决策 (speaker_format='english')
- Backend 生产接入 (image_generator.py:848-853)
- PM Code Review PASS (12 维度零问题)

**文档同步**: TEAM_CHAT + pm-progress×3 + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync

---

### 2026-03-06 14:45 — R2 审查 + Founder 决策 speaker_format=english + Backend 派发

**任务**: PM 审查 AI-ML 的 TASK-PROMPT-BUBBLE-FOLLOWUP-R2 全部 30 张图片 + 确定最优 speaker_format

**审查内容**:
- 30 张 R2 图片逐一检查（A/B/C 各 10 张，7 维度对比）
- C 组 (char_id) 淘汰: shot_07 幽灵气泡+乱码 "顾传付，庿菖志...人"，系统性风险
- A 组 (chinese): 1 问题 (shot_01 重复渲染)
- B 组 (english): 2 问题 (shot_01 额外角色, shot_14 重复) — NB2 随机性，非格式相关
- text_language=zh-CN 验证: 完全修复 R1 繁体问题，30/30 全部简体
- 角色一致性问题: pre-existing，非 speaker_format 相关，延后处理

**结论**: **推荐 B (english)** — 语言一致性 + 多语言扩展性 + Founder 直觉一致

**Founder 决策**: 确认 speaker_format='english'

**后续派发**:
- @Backend 生产代码修改: image_generator.py:829 传入 characters/speaker_format='english'/text_language='zh-CN' + 类型修复

**文档同步**: TEAM_CHAT + pm-progress×3 + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync

---

### 2026-03-06 11:33 — TASK-PROMPT-BUBBLE-FOLLOWUP PM 审查 + Founder 决策 + R2 派发

**任务**: PM 审查 AI-ML 的 TASK-PROMPT-BUBBLE-FOLLOWUP 两项任务交付

**审查结论**:
- **任务 1 精确 prompt 测量**: PASS ✅ — 手工验证全文，模块增减吻合（误差3chars），优化后 ~8% 精简
- **任务 2 命名格式 A/B/C**: 有条件 PASS + 3 问题
  - C_shot_01 幽灵气泡+乱码（char_003 被误解读）
  - B/C 组无参考图（ref_manager bug），对比不公平
  - 生产代码 829 行 characters/speaker_format 未传入（死代码）+ 类型不匹配

**Founder 3 项决策**:
1. 补测 B/C 组有参考图 — Founder 直觉: 英文名在全英文 prompt 中可能更好
2. 代码修复等补测后再做 — 先确定 format 再改代码
3. 繁体字 → 多语言 prompt 约束 — 预留 text_language 参数

**后续派发**:
- @AI-ML TASK-PROMPT-BUBBLE-FOLLOWUP-R2: 任务A(P0补测) + 任务B(P1繁简约束)

**文档同步**: TEAM_CHAT + pm-progress×3 + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync

---

### 2026-03-05 22:46 — TASK-PROMPT-BUBBLE PM 独立审查 PASS + FOLLOWUP 派发

**任务**: PM 独立审查 AI-ML 的 TASK-PROMPT-BUBBLE 代码变更和生成图片

**审查内容**:
- 20 张生成图片逐一查看（dialogue_dense_illustration 10 + slamdunk_dialogue 10）
- 代码深度审查: `image_generator.py` (1320 行, 🔴 critical) — `build_dialogue_scene_embed()` 新增、`build_native_text_prompt()` 修改、`generate_shot_image_phase2()` 修改、`build_system_instruction_phase2()` 精简
- `storyboard_prompts.py` — System Instruction 精简（~400→~150 chars）
- 侧效分析: 6 项风险点（dialogue embed 语法正确性 / Quality Suffix 移除安全性 / System Instruction 精简范围 / TEXT OVERLAY 移除影响 / Near {中文名} 跨语言映射 / thought/narration 路径完整性）

**结论**: **PASS** ✅
- 20/20 生成成功，14/14 对话嵌入成功
- 6 项侧效风险均为低至低-中，无高风险
- 代码逻辑正确，方向 2+3 融合实现到位

**PM 独立发现**:
- 场景环境不一致（pre-existing，非本次变更引入）
- 角色细节漂移（眼镜/发型/球衣号码，pre-existing）
- Shot 11 气泡位置略偏（轻微）
- 测试脚本未保存 prompt 文本文件（`prompts/` 目录为空）
- prompt 精简仅有估算值 (~400-600 chars)，无精确数据

**Founder 讨论**:
- Near {中文名} 跨语言映射 — 高注意力区域效果好但不彻底
- 之前 TASK-BUBBLE-SIMPLIFY 3 组因零气泡无法评估命名格式
- prompt 精简需精确 before/after 数据

**后续派发**:
- @AI-ML TASK-PROMPT-BUBBLE-FOLLOWUP: (1) 精确 prompt 尺寸测量 (2) Near {speaker} 命名格式 A/B/C 对比

**文档同步**: TEAM_CHAT + pm-progress×3 + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync

---

## 2026-03-05

### BUBBLE-SIMPLIFY 深度分析 + Founder 新证据修正 + TASK-PROMPT-BUBBLE 派发 ✅ (最新)

**完成时间**: 2026-03-05 19:00
**任务类型**: 深度分析 + 方向修正 + 任务派发

**完成内容**:
- [x] TASK-BUBBLE-SIMPLIFY 全维度深度分析（七章: 根因×3 + 正面发现 + 能力边界 + 4路径 + 通用性压力测试）
- [x] Founder 新证据分析: Gemini 网页版实测证明 NB2 完全具备对话气泡能力（漫画+写实两种风格成功）
- [x] PM 初始结论修正: 从「NB2 能力边界 → TextOverlay 全接管」修正为「prompt 架构注意力淹没 → 修复 prompt」
- [x] Prompt 架构冗余分析（为 AI-ML 提供参考）: 识别风格三重叠等 ~500-800 字可精简冗余
- [x] TASK-PROMPT-BUBBLE 设计 + 派发给 @AI-ML（方向 2+3 融合 + 2×10-shot 验证）
- [x] 分析文档更新至九章: `.team-brain/analysis/BUBBLE_SIMPLIFY_DEEP_ANALYSIS.md`
- [x] 全文档同步（TEAM_CHAT + PENDING + pm-progress×3 + TODAY_FOCUS + PROJECT_STATUS + daily-sync）

**关键输出**:
- `.team-brain/analysis/BUBBLE_SIMPLIFY_DEEP_ANALYSIS.md` — 完整分析（九章）
- TEAM_CHAT 19:00 — @AI-ML TASK-PROMPT-BUBBLE 派发（详细要求）
- PENDING.md — 新增 TASK-PROMPT-BUBBLE

---

### Docker Compose 部署方案审查 PASS + Cloudflare SSL 配置完成 ✅

**完成时间**: 2026-03-05 16:45
**任务类型**: 审查 + 配置指导

**完成内容**:
- [x] Docker Compose 方案 8 维度审查: PASS（6 项修改建议, 3 项确认事项）
- [x] Cloudflare SSL 模式确认: Full → Full (Strict) 升级
- [x] 指导 Founder 创建 Origin Certificate（`*.prefaceai.mov` + `prefaceai.mov`，到期 2041）
- [x] Origin Certificate 保存: `docker/ssl/prefaceai-mov-origin.pem` + `.key`
- [x] `.gitignore` 更新: `docker/ssl/` + `.env.*`（安全保护）
- [x] 边缘证书设置像素级核验: 12/12 与 prefaceai.net 一致
- [x] 通知 @DevOps: Nginx 需更新为 HTTPS + R1 worker profiles
- [x] 全文档同步

**关键输出**:
- Docker Compose 审查报告（TEAM_CHAT 16:45）
- Cloudflare 完整配置指引（SSL模式 + Origin Certificate + 边缘证书）
- 修改建议 R1-R6（R3 SSL 已当场解决）

---

### TASK-SHOT10-REGEN 审查 + Bug #6 分析 + TASK-BUBBLE-SIMPLIFY 派发 ✅

**完成时间**: 2026-03-05 15:55
**任务类型**: 审查 + 分析 + 任务派发

**完成内容**:
- [x] TASK-SHOT10-REGEN 审查: Bug #5 PASS ✅, 角色一致性 3/3 ✅
- [x] Bug #6 深度分析: `near {中文名}` 方案对 NB2 不够可靠（3 个根因）
- [x] Founder + PM 碰撞: 简化方案 — 对话嵌入 image_prompt，让 NB2 自行理解
- [x] 派发 @Backend TASK-BUBBLE-SIMPLIFY（Shot 10 三组对比测试: char_ID / 英文名 / 角色描述）
- [x] 全 8 份文档同步

**关键结论**:
- Bug #6 修复方向正确（用说话者身份替代硬编码），但实现方案（`near {中文名}`）对 NB2 不可靠
- Founder 提出根本性简化：不要拆分"画面"和"对话"为两套指令，而是让对话成为画面描述的一部分
- 仅针对 dialogue 类型，thought/narration 保持现有方式（效果好不动）

---

### VPS 环境检查核验 PASS + Docker Compose 方案批准 ✅

**完成时间**: 2026-03-05 11:19
**任务类型**: 核验 + 任务派发

**完成内容**:
- [x] VPS 环境检查 10 维度核验 — 全部 PASS
- [x] 确认后端已有 FastAPI 入口 + 5 API 路由模块（部署前置基本满足）
- [x] 批准 @DevOps 继续出 Docker Compose 方案（Founder 已确认）
- [x] 派发 6 项注意事项: API 层依赖 / 环境变量安全 / Celery+Redis / Python 版本 / Nginx 共存 / 输出格式
- [x] 全文档同步

### @Backend TASK-SHOT10-REGEN 派发 ✅

**完成时间**: 2026-03-05 10:36
**任务类型**: 任务派发

**完成内容**:
- [x] Founder 确认由 @Backend 补生成 shot_10
- [x] 派发 TASK-SHOT10-REGEN: 详细指定 storyboard 数据位置、参考图路径、预期输出
- [x] Shot 10 缺失原因: Bug #5 (dialogue handler dict crash)，已修复
- [x] 全文档同步: pm-progress×3 + TEAM_CHAT + TODAY_FOCUS + PROJECT_STATUS + PENDING + daily-sync

### 剩余 ~120 文件分类 + @DevOps 批次提交+push 派发 ✅

**完成时间**: 2026-03-05
**任务类型**: git 状态核查 + 任务派发

**完成内容**:
- [x] 核查 git status — 发现 ~120 个未提交文件（39 modified + ~80 untracked）
- [x] 分类为 3 批: Backend 代码(9) / Frontend 代码(~58) / 文档+测试(~80)
- [x] 派发 @DevOps 批次提交 + 统一 push（Founder 确认先提交再一次 push）
- [x] 全文档同步

## 2026-03-04

### Founder 确认 + @DevOps TASK-GIT-COMMIT-3 派发 ✅

**完成时间**: 2026-03-04 21:00
**任务类型**: 任务派发

**完成内容**:
- [x] Founder 确认所有修复可以 commit
- [x] 派发 @DevOps TASK-GIT-COMMIT-3（8 文件，含 SQ-1~8 + Bug#1~5 + Rule#7/#8）
- [x] 全文档同步: pm-progress×3 + TEAM_CHAT + TODAY_FOCUS + PROJECT_STATUS + PENDING + daily-sync

### PM Review — @AI-ML PASS + @Backend PASS ✅

**完成时间**: 2026-03-04 20:30
**任务类型**: Code Review

**完成内容**:
- [x] 审查 @AI-ML `storyboard_director.py`: Rule #7/#8 新增 + SQ-4/SQ-5/Bug#3 恢复 — PASS
- [x] 审查 @Backend `image_generator.py` L81-82: Bug #5 dict check — PASS
- [x] 读取 TEAM_CHAT L17740-17900 (两个修复报告)
- [x] 读取 ai-ml-progress×3 + backend-progress×2
- [x] 验证代码: 935 lines + syntax OK + import OK
- [x] 逐条核对: Rules 1-8 + SQ-4/SQ-5 + JSON 模板增强 + 强化规则区
- [x] PM 回滚事故自查 + 教训记录
- [x] 全文档同步: pm-progress×3 + TEAM_CHAT + TODAY_FOCUS + PROJECT_STATUS + PENDING + daily-sync

**教训**: PM 不应直接操作代码文件，`git checkout --` 会波及他人改动

### Shot 15/18 根因分析 + @AI-ML/@Backend 双任务派发 ✅

**完成时间**: 2026-03-04 19:30-19:45
**任务类型**: 根因分析 + 任务派发

**完成内容**:
- [x] Founder 挑战"NB2 模型限制"结论 → PM 重新分析代码/prompt
- [x] 定位根因: Stage 4 StoryboardDirector IMAGE PROMPT QUALITY REQUIREMENTS 缺少 2 类规则
- [x] 分析 Shot 15/18 storyboard prompt → 确认 Sonnet 4.6 生成的 image_prompt 有歧义
- [x] 派发 @AI-ML 任务: 新增物体物理合理性 + 多角色肢体交互上限规则（通用，非特定故事）
- [x] 派发 @Backend 任务: Bug #5 修复（Founder 已确认，dialogue handler dict check）
- [x] 全文档同步: TEAM_CHAT + pm-progress×3 + TODAY_FOCUS + PROJECT_STATUS + PENDING + daily-sync

**教训**: 不要过早将问题归为"模型限制"，先排查我们可控的 prompt 工程层面

### 回归验证独立复核完成 ✅ PM 4.36/5 vs Tester 4.36/5

**完成时间**: 2026-03-04 18:00
**任务类型**: 独立复核

**完成内容**:
- [x] 阅读 TEAM_CHAT L17400-17641 (PM code review + Tester 回归报告)
- [x] 阅读 tester-progress 3 文件
- [x] 查看 7 张 labeled refs (3 character + 4 scene) — Bug #1 全英文 ✅
- [x] 逐帧查看 17 张 shot (01-09, 11-18) — Bug #2 零泄漏 + Bug #3 零路人 ✅
- [x] 阅读 4_storyboard.json (Shot 10/15/18 prompt 分析)
- [x] 阅读 bugfix_regression_results.json + summary.json — Bug #4 假阳性 0 ✅
- [x] 确认 Founder 反馈: Shot 15 手机叠菜 (P3) + Shot 18 筷子归属 (P3) — 模型限制
- [x] 确认 Bug #5 (P2): dialogue handler dict crash, Shot 10 高潮帧缺失
- [x] 泛化性分析: 桌面物体空间关系 + 多人手部渲染 = AI 图像生成系统性限制
- [x] 编写独立复核报告 (TEAM_CHAT)
- [x] 全文档同步: TEAM_CHAT + pm-progress×3 + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync

**结果**:
- PM 4.36/5 vs Tester 4.36/5, 差异 0 — Tester 评估完全准确
- 4/4 Bug PASS + Bug #5 (P2) 需修复
- Founder 发现 Shot 15/18 确认 — 模型限制, 建议中期 prompt 改进

---

### TASK-SHOT-QUALITY-BUGFIX Code Review 4/4 PASS ✅

**完成时间**: 2026-03-04 17:00
**任务类型**: Code Review

**完成内容**:
- [x] 阅读 TEAM_CHAT 最新 200+ 行 (AI-ML Bug #3 + Backend Bug #1/#2/#4 修复报告)
- [x] 阅读 AI-ML progress 3 文件 + Backend progress 3 文件
- [x] 逐行代码审查 4 个修改文件:
  - storyboard_director.py L414-422: Rule #6 STRICT CHARACTER COUNT ✅
  - scene_reference_manager.py L275 + L32-38: 标签改英文 + CJK 字体兜底 ✅
  - image_generator.py L55-138: 6 种文字类型移除数值型技术英文 ✅
  - storyboard_service.py L1421-1422: camera.angle 字段对齐 ✅
- [x] 交叉验证: reference_image_manager.py 标签策略一致、_get_shot_type() 字段格式一致
- [x] 编写 Code Review 报告 (TEAM_CHAT)
- [x] 全文档同步: TEAM_CHAT + pm-progress×3 + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync

**结果**:
- 4/4 Bug 修复全部 PASS
- 建议 Tester 回归验证 → TASK-GIT-COMMIT-3

---

### Step 7 PM 独立复核完成 ✅

**完成时间**: 2026-03-04 16:00
**任务类型**: 独立复核 + 根因分析

**完成内容**:
- [x] 阅读 TEAM_CHAT Tester 完整 Step 7 报告 (~L17010-17191)
- [x] 阅读 step7_summary.json + step7_ab_results.json + 1_outline.json + 4_storyboard.json
- [x] 逐帧审查 24 张 B 组 shot 图 + 6 张角色参考图 + 3 张 labeled smart_ref + 2 张 scene_ref
- [x] 代码追踪 4 个文件: scene_reference_manager.py + reference_image_manager.py + image_generator.py + storyboard_service.py
- [x] 确认 Founder 报告的 3 项发现 + 根因分析 + 严重性升级
- [x] 发现额外 2 项问题 (SQ-6 Validator mismatch + 测试 idea 不一致)
- [x] 编写综合复核报告 (TEAM_CHAT)
- [x] 全文档同步: TEAM_CHAT + pm-progress×3 + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync

**结果**:
- SQ 改进 PASS (B 4.19/5 vs A 3.58/5, +17%)
- 发现 4 个 Bug: P1×1 (场景标签泄漏) + P2×2 (指令泄漏 + 神秘路人) + P3×1 (Validator mismatch)
- 建议: 先修 Bug 再 TASK-GIT-COMMIT-3

---

### Step 7 指引发布 + Frontend P3/P4 代码验证 ✅

**完成时间**: 2026-03-04 12:30
**任务类型**: 任务派发 + 代码验证

**完成内容**:
- [x] Step 7 A/B 对比验证指引在 TEAM_CHAT 发布（A=DIALOGUE-DENSE-TEST baseline, B=新跑, 7 维度, 通过标准）
- [x] Frontend P3/P4 代码独立验证 3/3 PASS:
  - StoryCard.tsx: aria-label="故事操作菜单" (L96) + ESC useCallback+useEffect+cleanup (L37-46) ✅
  - StoryDetailContent.tsx: key=char.name (L202-204) + key=shot.shotId (L134) ✅
  - UserMenu.tsx: /settings (L69-70) + /dashboard (L62) ✅
- [x] 全文档同步: TEAM_CHAT + pm-progress×3 + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync

---

### Step 6 PM Code Review 完成 — 8/8 SQ PASS ✅

**完成时间**: 2026-03-04 12:00
**任务类型**: Code Review (AI-ML 2 文件 + Backend 6 文件)

**审查结果**:
- [x] SQ-3: screenplay_writer.py L397-406 — 对话明确化规则 ✅ PASS
- [x] SQ-4: storyboard_director.py L414-431 — 叙事视觉道具 + 空间纵深 ✅ PASS
- [x] SQ-5: storyboard_director.py L433-460, L534-535 — 运镜差异化 + JSON 新字段 ✅ PASS
- [x] SQ-8: 3 文件 — previous_shot 全链路移除确认 ✅ PASS
- [x] SQ-2: 4 文件 — 智能参考图选择 (portrait/fullbody, *1, fallback) ✅ PASS
- [x] SQ-1: 2 文件 + prompt — PIL 标注 + 标签声明式 prompt ✅ PASS
- [x] SQ-6: storyboard_service.py L1394-1488 — 5 规则 Validator ✅ PASS
- [x] 交叉验证: SQ-5↔SQ-6 对齐 + SQ-1↔SQ-2↔prompt 标签链 + DEC-014 grep ✅
- [x] Non-blocking findings: 2 项 P4 (dead code + code duplication)
- [x] TEAM_CHAT + pm-progress×3 + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync 同步

---

### Step 5a SQ-7 文档更新完成 ✅

**完成时间**: 2026-03-04 11:15
**任务类型**: 文档更新 (CLAUDE.md + Guide + DECISIONS.md)

**完成内容**:
- [x] CLAUDE.md 11 个位置更新: Pro→NB2 默认 (L190, L353, L369, L466, L663, L671-678) + DEC-014 previous_shot 移除 (L227-245 整节重写, L354, L562-563)
- [x] shot_transition_improvement_guide.md 8 个位置更新: L656 Pro→NB2 + Section 3.2/3.3/4 DEC-014 标注
- [x] DECISIONS.md DEC-014 @PM action item → [x] 完成
- [x] 全文搜索验证: use_pro_model=True / 评估切换 / previous_shot_image 无遗漏
- [x] pm-progress 3 文件同步

---

### Step 4 PM 独立核验通过 + Step 5 正式启动 ✅

**完成时间**: 2026-03-04 10:28
**任务类型**: 独立核验 + 任务启动 + 全文档同步

**完成内容**:
- [x] 独立审查: 读取 TEAM_CHAT (~923行) + Tester progress 3 文件 + step4_summary.json + 2 个 results.json
- [x] 文件完整性: ink 5 shots + 4 char refs + 4 scene refs (1 因 429 失败) + realistic 5 shots + 4 char refs + 5 scene refs
- [x] 独立看图: 10 张 shot 图 + 4 张角色参考图逐一审查
- [x] PM 评分: ink 4.1/5 (Tester 4.2) + realistic 4.7/5 (Tester 4.575) — 差异 ±0.2 内
- [x] 发现记录: 3 项 (P4 ink Shot 14 偏插画 + P4 ink scene ref 429 + 观察 realistic 最佳匹配)
- [x] Step 5 三路并行正式启动: 5a @PM(SQ-7) + 5b @AI-ML(SQ-3,4,5) + 5c @Backend(SQ-1,2,6,8)
- [x] 全文档同步: TEAM_CHAT + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync + pm-progress×3

---

## 2026-03-03

### Founder 批准场域式 + Step 4 派发 ✅

**完成时间**: 2026-03-03 17:18
**任务类型**: 决策记录 + 任务派发

**完成内容**:
- [x] Founder 批准场域式为默认策略 — 记录并生效
- [x] 分析已测/未测风格差异，推荐 ink + realistic 作为 Step 4 验证风格
- [x] Step 4 派发 @Tester: ink + realistic 各 5 shots, 4 维度验收, 都市情感题材
- [x] TEAM_CHAT 发布派发消息 + 各 Agent 指令
- [x] 全文档同步: TEAM_CHAT + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync + pm-progress×3

### Step 3 闭环 + slam_dunk 修复确认 ✅

**完成时间**: 2026-03-03 17:11
**任务类型**: 修复确认 + Step 闭环 + Founder 决策请求

**完成内容**:
- [x] AI-ML 提交 slam_dunk 句序修复 (17:05)
- [x] PM 逐句核验 style_enforcer.py:203 — 6 句顺序 ✅, 内容不变 ✅, keywords 未动 ✅
- [x] Step 3 闭环: 15/15 全部通过
- [x] TEAM_CHAT 发布确认结果 + Founder 决策请求
- [x] 全文档同步: TEAM_CHAT + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync + pm-progress×3

### Step 3 Review + P2 复验 ✅

**完成时间**: 2026-03-03 16:44
**任务类型**: 代码 review ×2

**完成内容**:
- [x] Step 3: review AI-ML style_enforcer.py 15 个风格 style_description
- [x] 逐风格验证 6 句结构 + 场域式语调 + 词数 + keywords 完整性
- [x] 发现: slam_dunk 6 句顺序错乱 (内容对序号乱) → 通知 AI-ML 修复
- [x] 发现: ink 第 5 句偏哲学化 (可接受)
- [x] 结论: 13/15 PASS, 有条件通过
- [x] P2 复验: 14 文件逐一审查 (DEC-013 合规 + 模式一致性 + Auth 集成 + 导航)
- [x] P2 评分 4.8/5: P3×1 + P4×3 不阻塞
- [x] TEAM_CHAT 发布 review 结果 + AI-ML 修复指令 + Frontend P2 反馈
- [x] PENDING + TODAY_FOCUS + pm-progress 更新

### DEC-014 独立分析 + 多 Agent 进度同步 + 全文档更新 ✅

**完成时间**: 2026-03-03 16:22
**任务类型**: 独立分析 + 决策记录 + 进度同步 + 全文档更新

**完成内容**:
- [x] previous_shot_image 传递机制独立深度分析（代码 + 证据 + 3 方案对比）
- [x] 发现 3 个问题：构图感染 + 链式放大 (29 shots 误差累积) + 跨场景 Bug (无 location_id 检测)
- [x] 推荐 Plan A (完全移除) → Founder 采纳 → DEC-014 记录
- [x] SQ-8 新增 (Backend: 移除 previous_shot_image)
- [x] SQ-1/SQ-2 scope 更新 (不再涉及 previous_shot)
- [x] SQ-5 澄清 (DEC-014 后仅限 Stage 4)
- [x] Backend SQ-8 详细实现指引 (3 文件修改 + IMAGE 编号变化 + 建议顺序)
- [x] 三 Agent 进度确认: AI-ML Step 2 ✅ + Frontend P2 ✅ + Backend 预研 ✅
- [x] SQ-7 草稿增补 CLAUDE.md 2.2 节
- [x] 全文档更新 (10 文件): DECISIONS + TEAM_CHAT + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync + pm-progress×4

### DIALOGUE-DENSE-TEST Founder Review + TASK-SHOT-QUALITY-UPGRADE 派发 ✅

**完成时间**: 2026-03-03 15:00
**任务类型**: 独立分析 + 任务派发 + 全文档同步

**完成内容**:
- [x] 查看全部 29 张 shot 图片（逐帧审查）
- [x] 查看 6 张角色参考图（3角色 × portrait+fullbody）+ 3 张场景参考图
- [x] 读取 4_storyboard.json 中关键 shots 的 image_prompt 数据
- [x] 读取 dialogue_dense_test_results.json 完整测试数据
- [x] 一字一句精读 shot_transition_improvement_guide.md（718行，12维度改善方案）
- [x] 读取代码结构：storyboard_prompts.py（VISUAL CONTINUITY REFERENCE + IMAGE映射）+ image_generator.py（参考图传递）+ pipeline_orchestrator.py（参考图组装）
- [x] 独立分析 Founder 4 项发现的多 Stage 根因
- [x] 提出 7 项具体改进方案（SQ-1~SQ-7）
- [x] Founder 5 项决策确认
- [x] 整合为 TASK-SHOT-QUALITY-UPGRADE 插入现有流程 Step 5
- [x] 全文档同步更新（TEAM_CHAT + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync + pm-progress×3）

**PM 额外发现（Founder 未提及）**:
- Shot 15: NB2 自动生成双格分镜（非预期行为, P3）
- Shot 16: 金表火花特效不自然（P4）
- 多张 shots 背景重复度高（P3, Founder 补充确认需改进）
- NB2 文字渲染质量好，29/29 零 text bleeding（正面）
- 情绪弧线视觉表达好（正面）

---

## 2026-03-02

### 执行顺序修正: 并行→串行 (Founder 决策) ✅

**完成时间**: 2026-03-02 16:31
**任务类型**: 执行顺序调整 + 全文档同步

**完成内容**:
- [x] Founder 提出串行方案 → PM 分析同意（代码安全 + 流程简洁 + AI-ML 可改必要文件）
- [x] TEAM_CHAT 追加修正消息（作废并行约束 + 新串行顺序）
- [x] PENDING 更新（TASK-STYLE-DESC-REWRITE 增加前置条件，取消禁止改代码约束）
- [x] TODAY_FOCUS 更新（Agent 状态表 + 执行计划 Step 1-4）
- [x] PROJECT_STATUS 更新（AI-ML 状态 + 活动日志）
- [x] daily-sync 更新
- [x] pm-progress×3 更新

---

### TASK-DIALOGUE-DENSE-TEST + TASK-STYLE-DESC-REWRITE 正式派发 ✅

**完成时间**: 2026-03-02 16:00
**任务类型**: 任务派发

**完成内容**:
- [x] TASK-DIALOGUE-DENSE-TEST (P0) → @Tester: 家庭晚餐争吵 E2E 测试，32 shots，illustration 场域式
  - 完整测试参数指定（idea/风格/规模/模型/渲染/宽高比）
  - 7 项验收指标明确（dialogue≥60% 核心）
  - 输出要求 5 项
- [x] TASK-STYLE-DESC-REWRITE (P1, 写稿阶段) → @AI-ML: 14 个风格场域式改写
  - 安全规则明确：禁止修改 style_enforcer.py
  - 6 句结构标准 + 质量要求
  - 输出到 .team-brain/handoffs/STYLE_DESC_REWRITE_DRAFT.md
- [x] Coordinator 执行顺序修正已落实（Step 1 并行互不干扰 → Step 2 PM review + Founder 决策 → Step 3 写入代码+小规模验证）
- [x] TEAM_CHAT 发布派发消息

---

### TASK-CREATE-UPGRADE P1 PM 独立复验 PASS (4.7/5)

**完成时间**: 2026-03-02 16:00
**任务类型**: 独立复验 + 代码审阅 + DEC-013 合规核验 + 构建验证

**完成内容**:

#### 核验方法（7 项逐一验证）
1. **DEC-013 Stage B-E 合规**: 全部相关条目 PASS
2. **架构审查**: Stage Router 模式 / Context 23→34 / 类型系统 / Mock / 零依赖 / 动画 / StrictMode — 全部通过
3. **代码质量审查**: 7 文件逐一阅读（4 新建 + 3 修改），StageB P3 无拖拽 + StageE P4 setTimeout
4. **P4 修复验证**: CharacterUploader + SceneUploader revokeObjectURL 2/2 PASS
5. **`npm run build` 独立验证**: 16/16 pages, 0 errors, 4 warnings (P5)
6. **文档修正验证**: 3/3 PASS
7. **TEAM_CHAT 发布报告 + 全文档同步**

#### 综合评分: 4.7/5

| 维度 | 分 |
|------|----|
| DEC-013 合规性 | 5.0/5 |
| 架构设计 | 4.5/5 |
| 代码质量 | 4.5/5 |
| P4 修复 | 5.0/5 |
| 构建验证 | 5.0/5 |
| 文档修正 | 5.0/5 |

#### 发现问题
- P3: StageB GripVertical 无拖拽（mock 阶段可接受）
- P4: StageE setTimeout 未清理（同 StageA 已修模式，反馈 @Frontend）

#### 范围分析
计划 22 文件 → 实际 7 文件。Frontend 选择单页 Stage Router + 4 个内聚 Stage 组件替代独立路由+可复用 UI 组件。设计简化合理，不影响功能完整性。

---

### TASK-CREATE-UPGRADE P0 PM 独立复验 PASS (4.8/5)

**完成时间**: 2026-03-02
**任务类型**: 独立复验 + 代码审阅 + DEC-013 合规核验 + 构建验证

**完成内容**:

#### 核验方法（7 项逐一验证）
1. **DEC-013 逐条合规**: 8 项决策 × 代码对照，8/8 全部 PASS
2. **架构审查**: Context+Reducer / Provider层级 / 类型系统 / Mock数据 / 零依赖 / Page+Content / 动画 — 全部通过
3. **代码质量审查**: 16 文件逐一阅读（9 新建 + 7 修改），发现 2 处 P4 object URL 内存泄漏
4. **Founder 微调验证**: 默认8风格+展开 / 井上雄彦 / 皮克斯3D — 3/3 PASS
5. **`npm run build` 独立验证**: 16/16 pages, 0 errors, 3 warnings (P5)
6. **文件数量核实**: 9 新建 + 7 修改 = 16，与计划列表一致
7. **TEAM_CHAT 发布报告 + 全文档同步**

#### 综合评分: 4.8/5

| 维度 | 分 |
|------|----|
| DEC-013 合规性 | 5.0/5 |
| 架构质量 | 5.0/5 |
| 代码质量 | 4.5/5 |
| UI/UX 完整性 | 5.0/5 |
| Founder 微调合规 | 5.0/5 |
| 构建通过 | 5.0/5 |
| 文档准确性 | 4.0/5 |

#### 发现的问题
- P4: CharacterUploader + SceneUploader 移除时未 revokeObjectURL（轻微内存泄漏）
- P5: 文档日期/文件数不一致（已反馈 Frontend）

---

### TASK-CROSS-STYLE-TEST PM 独立核验 PASS + 全文档同步

**完成时间**: 2026-03-02
**任务类型**: 独立核验 + 质量评审 + 根因分析 + 全文档同步

**完成内容**:

#### 核验方法（7 项逐一验证）
1. **测试脚本审阅**: `tests/test_cross_style.py`（646 行），控制变量隔离正确（Stage 1-4 一次，Stage 5 swap try/finally）
2. **输出完整性**: group_a 32 + group_b 32 + 6 char refs + 3 scene refs，64/64 成功率 100%
3. **JSON 交叉对比**: 独立统计 4_storyboard.json text_type → 与 text_type_distribution.json 完全一致
4. **style_description 核对**: A/B 描述与 PM 批准版本一致，mandatory/forbidden_keywords 两组相同
5. **图片质量评审**: 抽样 10 对 shots (01/04/08/09/12/24/26/30/32)，独立 4 维度评分
6. **DIALOGUE-SYSTEM 根因**: 读取 1_outline.json，确认暗恋题材结构性原因
7. **速度分析**: B 快 26%，与 slam_dunk 相反，需更多数据

#### PM 独立评分（与 Tester 完全一致，0 gap）

| # | 维度 | A组 | B组 | 胜出 |
|---|------|-----|-----|------|
| 1 | 风格准确度 | 4.0 | 4.5 | B |
| 2 | 色彩与光影 | 3.5 | 4.5 | B |
| 3 | 细节与质感 | 4.0 | 4.5 | B |
| 4 | 角色一致性 | 4.0 | 4.0 | 平 |
| | 平均 | 3.88 | 4.38 | B |

#### PM 补充 4 项 Tester 未覆盖维度
1. **叙事构图力**: B 优 — 景深和空间关系传达叙事（Shot 12 林夏背景化 = 疏离感）
2. **场景连续性**: 平 — 两组均保持 cafe 一致性
3. **NB2 原生文字质量**: A 微优 — Shot 24 B 组 text bleeding（旁白渲染进咖啡泡沫）
4. **情感表达力**: B 优 — 角色间情感张力更到位

#### DIALOGUE-SYSTEM 根因
- 故事主题"暗恋" + narrative_pace="slow_burn" → 天然偏内心独白
- thought 71.9% / dialogue_family 28.1% 是**叙事正确**的分布
- 60% 阈值对此题材不适用 → PM 建议改为 genre-adaptive 或 INFO 级别

#### 综合建议（供 Founder 决策）
1. ✅ 批准场域式为默认 style_description 策略（两个风格均胜出）
2. ⚠️ DIALOGUE-SYSTEM 60% 阈值需讨论
3. 📝 Shot 24 text bleeding 记为 P3 技术债

---

### DEC-013 决策闭环 + TASK-CREATE-UPGRADE 计划制定 + 全文档同步

**完成时间**: 2026-02-28 18:07
**任务类型**: 产品分析 + 决策闭环 + 实施计划 + 全文档同步

**完成内容**:

#### PM 独立分析 — Create 页面升级 + 产品方向

Founder 提出 7 项 Create 页面反馈，PM 独立深度分析：

**逐点技术可行性评估（7项）**:
1. **角色参考图上传** — 后端 `reference_image_manager.py` 已有 `set_reference()` 可注入手动上传图，但无 API endpoint，需新建。AI 提取信息需 LLM 调用（Haiku 适合）。per-shot ref 上限：5 chars × 1 fullbody + 2 scene + 1 prev = 8，远低于后端 13 上限 ✅
2. **场景参考图上传** — 后端 `scene_reference_manager.py` 已有 interior/exterior 逻辑，max 1-2 refs/scene。建议与角色分开入口 ✅
3. **上传故事文档** — 后端 `story_outline_generator.py` 输入只接受 `idea: str`，无文件解析。两种方案：浅层（提取文本→当 idea）或深层（提取结构化信息）✅
4. **宽高比选择** — 后端 `aspect_ratio` 参数已支持动态值。但 `pipeline_orchestrator.py` 有 5 处硬编码 "2:3" 需改 ✅
5. **长篇连续故事** — 后端 `story_outline_generator.py` max shots = `max(23, target_duration_minutes * 8)`，需增加 epic 映射。续写需新建 continuation API ✅
6. **风格扩展** — 后端已有 16 个预设 + `_build_generic_prefix()` 支持未知风格。自定义风格需 LLM 分析图片→关键词 ✅
7. **TextOverlay vs NB2** — Founder 确认 NB2 为主，TextOverlay 备用。前端不需关心 ✅

**PM 补充 4 项关联点**:
1. **账户系统优先级提升** — 续写/历史记录/上传管理都依赖用户账户，建议 P2 提前
2. **存储规划** — 角色/场景/文档/自定义风格图片需存储方案（先本地，后对象存储）
3. **Stage A/B 边界** — Stage A 管"输入材料"，Stage B 管"确认/调整大纲"，需明确分界
4. **成本影响** — 新功能（AI 提取角色信息、自定义风格分析）增加 API 成本，应体现在定价

**PM 向 Founder 提出 5 个澄清问题 + 回答**:
- Q1: 角色信息提取方式？→ AI 自动提取（可用 Haiku）
- Q2: 故事文档解析深度？→ 先浅层
- Q3: 宽高比 per-story 还是 per-shot？→ Per-story only
- Q4: 长篇续写模式？→ 两种（自动续写 + 用户指导续写）
- Q5: 预设与自定义风格关系？→ 互斥

#### DEC-013 决策汇总（8 项确认）
1. 角色参考图：用户上传 1 张 → AI 提取 → 系统补全 portrait+fullbody，max 5 chars
2. 场景参考图：独立入口，max 8 scenes，用户上传 1 张 → 系统补全 interior/exterior
3. 故事文档：浅层优先（提取文本→当 idea），支持 md/txt/PDF
4. 宽高比：Per-story（16:9 或 2:3），非 per-shot
5. 长篇：新增 epic（max 36 shots），两种续写模式
6. 风格：16 预设全可见 + 自定义上传（Sonnet 4.6 分析），预设与自定义互斥
7. 渲染：NB2 主，TextOverlay 备用
8. 其他：账户优先级提升、先本地存储、前端 Mock 数据独立开发、CLAUDE.md Haiku 规则仅限开发 Agent

#### TASK-CREATE-UPGRADE 实施计划
- P0（18 文件）: 基础设施 + Create 页面核心升级（Context、Uploader×5、StyleSelector/LengthSelector/StoryIdeaInput 扩展）
- P1（22 文件）: Stage B-E 页面骨架（outline、generating、preview、deliver + 公共 layout）
- P2（14 文件）: 账户体系 + Dashboard（register、dashboard、history、story detail）
- 架构：React Context + useReducer，零新 npm 依赖
- 全文档同步更新 9 个文件

---

### 第三轮核验: TASK-ROBUSTNESS-FIX ✅ + illustration 场域式 ✅ + Tester 启动通知

**完成时间**: 2026-02-28 14:52
**任务类型**: 代码核验 + 前置审核 + Tester 启动通知 + 全文档同步

**完成内容**:
- [x] 阅读 TEAM_CHAT 381 行 + Backend/AI-ML progress 全部文件（current + context-for-others + completed，共 6 个文件）
- [x] TASK-ROBUSTNESS-FIX PM 代码核验 ✅ PASS — 3/3 修复点逐行对齐 text_overlay_service.py 完全一致
- [x] illustration 场域式 B 组 PM 核验 ✅ PASS — 6 句完整、零重复、避开 forbidden、都市情感适配
- [x] TEAM_CHAT 发布核验报告 + @Tester 启动通知（4 点特别交代：控制变量、text_type 统计、4 维度评估、题材限制）
- [x] 更新 PM progress 3 文件 + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync + DECISIONS + TEAM_CHAT

---

### Phase 4 第二轮核验: TASK-AB-STYLE-DESC ✅ + TASK-NATIVE-TEXT-ROBUSTNESS ⚠️ + Founder 3项决策 + 新任务派发

**完成时间**: 2026-02-28 11:15
**任务类型**: A/B 测试核验 + 代码审阅 + Founder 决策 + 任务派发 + 全文档同步

**完成内容**:
- [x] 阅读 TEAM_CHAT 500+ 行 + Tester/Backend progress 全部文件
- [x] 查看 Tester A/B 测试 10 张图片逐一对比 + 测试脚本 + JSON 数据
- [x] TASK-AB-STYLE-DESC PM 核验 ✅ PASS — B 组场域式 4.5 vs A 组命令式 4.0
- [x] PM 补充 4 点发现：角色一致性（均无问题）、背景空间感（B优）、叙事连贯性（B优）、速度放大效应
- [x] 代码审阅 Backend 3 文件：storyboard_director ✅ + text_overlay_service ✅ + image_generator ⚠️ 不一致
- [x] TASK-NATIVE-TEXT-ROBUSTNESS PM 核验 ⚠️ PARTIAL PASS — P1 关键字回退不一致需修复
- [x] Founder 3 项决策确认：Backend 先修复 / illustration 跨风格验证 / 场域式等验证后统一决策
- [x] 派发 TASK-ROBUSTNESS-FIX (P1) @Backend + TASK-CROSS-STYLE-TEST (P2) @Tester（需 AI-ML 前置）
- [x] 更新 PM progress 3 文件 + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync + DECISIONS + TEAM_CHAT

---

### Phase 4 核验: TASK-NB2-NATIVE-TEXT ✅ + TASK-AB-STYLE-DESC 前置 ✅ + 新任务派发

**完成时间**: 2026-02-28 10:25
**任务类型**: 代码核验 + 前置审核 + 技术债处理 + 全文档同步

**完成内容**:
- [x] 阅读 TEAM_CHAT 1000 行 + Backend/AI-ML progress 全部文件
- [x] 审阅 `image_generator.py` 代码：build_native_text_prompt + _strip_speaker_for_native + use_native_text 参数透传
- [x] 查看 5 张验证图片逐一对比 + JSON 数据 + Python 语法验证通过
- [x] TASK-NB2-NATIVE-TEXT PM 核验 ✅ PASS（代码+输出全部符合规格）
- [x] TASK-AB-STYLE-DESC 前置审核 ✅ PASS（场域式改写质量好，单一变量隔离）
- [x] 发现技术债：混合类型文本分类依赖中文关键字 → 派发 TASK-NATIVE-TEXT-ROBUSTNESS (P2) @Backend
- [x] 通知 @Tester: TASK-AB-STYLE-DESC 可启动
- [x] 更新 PM progress 3 文件 + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync + DECISIONS + TEAM_CHAT

---

### NB2-TEXT-TEST PM 独立复核 + Founder 方案 B 决策 + Phase 4 任务派发 ✅

**完成时间**: 2026-02-27 17:24
**任务类型**: A/B 测试独立复核 + Founder 决策记录 + Phase 4 任务派发 + 全文档同步

**完成内容**:
- [x] 阅读 TEAM_CHAT 1000+ 行 + Tester/Coordinator progress 文件 + Prompt 工程高级原则全文
- [x] 查看 NB2-TEXT-TEST 10 张 A/B 测试图片逐一对比 + 测试脚本 + JSON 数据
- [x] 澄清关键事实：A/B 两组均使用 NB2 模型（非 Pro），成本/速度完全相同
- [x] PM 独立评分：A=3.8/5, B=4.1/5（与 Founder 直觉一致，反转 Tester 结论）
- [x] 记录 Founder 决策：方案 B 全面切换 NB2 原生渲染 + TextOverlay 保留备用
- [x] 派发 TASK-NB2-NATIVE-TEXT (P0) @Backend + TASK-AB-STYLE-DESC (P2) @Tester
- [x] 更新 PM progress 3 文件 + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync + DECISIONS + TEAM_CHAT

---

### Phase 3 全部任务 PM 核验 7/7 PASS + 全文档同步 ✅

**完成时间**: 2026-02-27 16:32
**任务类型**: 代码核验 + Founder 反馈处理 + 全文档同步

**完成内容**:
- [x] 阅读 TEAM_CHAT 1000 行 + Backend/AI-ML progress 文件 + 6 个代码文件逐行核验
- [x] Python 语法验证 6/6 通过
- [x] NB2 验证输出核验（5 张 PNG + JSON 数据确认，avg 25.9s/张，提速 ~2.8x）
- [x] Founder 反馈处理：shot_04 角色偏差记录，建议 Tester 在 NB2-TEXT-TEST 中增加角色一致性评估
- [x] 核验结果：7/7 全部 PASS（NB2-SWITCH + SLAMDUNK-COLOR A+B + DIALOGUE L1+L2+3 + TEAM-UNIFORM + SPEAKER-PREFIX）
- [x] TEAM_CHAT 发布核验报告
- [x] 通知 @Tester：TASK-NB2-TEXT-TEST 前置条件已满足
- [x] 更新 PM progress 3 文件 + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync + DECISIONS

---

### TASK-E2E-TEST-2 复核 + Founder 6 项决策 + Phase 3 六项任务派发 ✅

**完成时间**: 2026-02-27 15:41
**任务类型**: E2E 复核 + NB2 技术研究 + 决策记录 + 任务派发 + 全文档同步

**完成内容**:
- [x] 阅读 TEAM_CHAT 最新 500+ 行 + NB2 研究报告全文 + 4 个代码文件分析
- [x] TASK-E2E-TEST-2 PM 独立复核（确认 Tester 4.3/5 合理，额外发现队友球衣颜色问题）
- [x] NB2 API 兼容性搜索研究：Model ID `gemini-3.1-flash-image-preview`，API 100% 兼容
- [x] Founder 6 项决策确认记录
- [x] Phase 3 六项任务派发：NB2-SWITCH + SLAMDUNK-COLOR + DIALOGUE-SYSTEM + TEAM-UNIFORM + NB2-TEXT-TEST + SPEAKER-PREFIX
- [x] 更新 PM progress 3 文件 + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync + TEAM_CHAT

---

## 2026-02-26

### Backend 核验通过 + TASK-E2E-TEST-2 启动通知 ✅

**完成时间**: 2026-02-26 17:48
**任务类型**: 任务核验 + text_type 分析 + E2E 启动通知 + 全文档同步

**完成内容**:
- [x] 核验 Backend 三项 P0 任务（MODEL-UPGRADE + STYLE-DEFAULT-FIX + RETEST）全部通过
- [x] 确认 Frontend P1 修复，评分更新 4.5→4.8/5
- [x] text_type 分布深度分析：判断为题材导致（内心独白故事），Founder 同意先看完整效果
- [x] TEAM_CHAT 发布 TASK-E2E-TEST-2 启动通知（含测试参数 + 7项验收维度）
- [x] 更新 PM progress 3 文件 + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync

---

### Phase 2 综合复核 + Founder 反馈执行 + 新任务派发 ✅

**完成时间**: 2026-02-26 16:43
**任务类型**: 综合复核 + 问题诊断 + 反思记录 + 新任务派发 + Frontend 复验 + 全文档同步

**完成内容**:
- [x] 阅读 TEAM_CHAT 最新 600+ 行 + 所有 Agent progress 文件（6个）
- [x] 验收 4 项 Agent 任务（Backend TASK-MODEL-UPGRADE ✅、AI-ML 3任务 ✅、Frontend TASK-UI-STAGE-A ✅、DevOps GitHub ✅）
- [x] 发现问题 P0：Backend 验证测试使用 realistic 风格（应为 slam_dunk）
- [x] 发现问题 P1：text_type 分布 dialogue 5.3%（目标 40-50%）、thought 47.4%（目标 20-25%）
- [x] Founder 反馈执行：派发 TASK-STYLE-DEFAULT-FIX（8文件默认值 realistic→anime）
- [x] Founder 反馈执行：派发 TASK-MODEL-UPGRADE-RETEST（slam_dunk 重跑验证）
- [x] Founder 反馈执行：PM 反思记录到 auto memory（任务派发具体化教训）
- [x] Frontend Stage A 复验：代码审阅 6 文件，评分 **4.5/5**（DEC-011 全覆盖，2项 P1 建议）
- [x] 更新 PM progress 3 文件 + PENDING + TODAY_FOCUS + PROJECT_STATUS + daily-sync + TEAM_CHAT

---

## 2026-02-25

### DEC-012 决策记录 + 成本估算 + Phase 2 六项任务派发 ✅

**完成时间**: 2026-02-25 18:09
**任务类型**: 决策记录 + API 调研 + 成本分析 + 任务派发 + 全文档同步

**完成内容**:
- [x] 理解 Founder 4 项决策：角色一致性框架 / narration 优化 / 灌篮高手风格 / 全面模型升级
- [x] 查阅 Anthropic 官方文档：确认 `claude-sonnet-4-6`，$3/$15 per MTok
- [x] 分析每故事 API 调用量：14-29 次，~23-28K input，~19-23K output tokens
- [x] 计算每故事成本估算：$0.35-0.43 文本生成（总成本增量 <5%）
- [x] TEAM_CHAT 发布 DEC-012 完整报告 + 成本估算 + Phase 2 六项任务派发
- [x] DECISIONS.md 新增 DEC-012 条目（含 7 项后续行动）
- [x] PENDING.md 更新：Founder 决策✅ + 6 项新任务条目
- [x] TODAY_FOCUS.md 更新：Steps 49-54 + Agent 状态 + 执行计划全部重写
- [x] PROJECT_STATUS.md 更新：DEC-012 + Phase 2 派发 + 6 个模块状态 + 更新日志
- [x] PM progress 3 文件全部更新（current + context-for-others + completed）
- [x] daily-sync/2026-02-25.md PM 部分更新

---

## 2026-02-24

### TASK-E2E-VALIDATE PM 独立复核 + Founder 反馈回应 ✅

**完成时间**: 2026-02-25 18:00
**任务类型**: 逐图审查 + 群聊阅读 + 模型调研 + 分析报告 + 文档同步

**完成内容**:
- [x] 逐一查看全部 29 张 shot + 4 张角色参考图 + 2 张场景参考图 + 关键带文字版本
- [x] 阅读 TEAM_CHAT 最新 ~630 行（Backend 完成通报 + Tester 验收报告 + 补充分析）
- [x] 发现 Tester 角色一致性维度验收不准：声称 shot 01/05/11/13/20/26/29 眼镜 7/7 ✅，实际 01/05/13/20 四个缺眼镜
- [x] PM 逐 shot 统计：陈默面部可见 19 shot 中 6 个缺眼镜（01/05/13/19/20/21），一致性 68%
- [x] 调研全部 LLM 模型：9 个模型按服务/文件/行号梳理（Stage 1-4 主模型是 Gemini 3 Flash 不是 Haiku）
- [x] 回应 Founder 4 项反馈：角色一致性(P1)/narration占比(P1)/条漫风格(P0)/模型升级(P0)
- [x] 推荐方案 B：Stage 1+3 换 Claude Sonnet 4.6（大纲+剧本决定故事吸引力）
- [x] PM 总评 4.3/5（流水线跑通 ✅，质量问题纳入 Phase 2）
- [x] TEAM_CHAT 发布完整复核报告
- [x] 全部文档同步更新：PENDING + TODAY_FOCUS + PROJECT_STATUS + PM progress 3文件 + daily-sync

### TASK-E2E-VALIDATE 任务派发 + TextOverlay 补充 ✅

**完成时间**: 2026-02-24 15:35~15:45
**任务类型**: 阅读理解 + 分析建议 + 任务派发 + 文档同步

**完成内容**:
- [x] 阅读 TEAM_CHAT 最新 300+ 行 + PENDING/DECISIONS/CLAUDE.md/TODAY_FOCUS 全部更新后文档
- [x] 分析端到端验证职责分工：PM 建议混合方案（Backend 跑通 → Tester 独立验收），Founder 批准
- [x] 研究 pipeline_orchestrator.py 入口代码（参数签名/输出目录结构/调用方式）
- [x] TEAM_CHAT 发布详细任务派发：Step 1 @backend（含示例代码+验证清单）+ Step 2 @tester（6维度验收标准）
- [x] **发现 TextOverlayService 未集成到正式流水线**（仅存在于测试脚本）
- [x] **深度调研数据缺口**：Stage 3/4 输出 vs TextOverlay 需求（text_type/dialogue_lines/thought_lines/speaker_position 全缺）
- [x] **TEAM_CHAT 发布 TextOverlay 集成补充说明**（15:45）：数据缺口分析 + 实施方案（Stage 4 prompt 修改 + pipeline 后处理）+ 验证清单更新为 7 维度
- [x] PENDING.md 更新为 Step 1a + Step 1b + Step 2
- [x] TODAY_FOCUS.md 更新（步骤42-46 + Agent状态 + 执行计划含 TextOverlay）
- [x] PROJECT_STATUS.md 更新（DEC-011 实施计划 + 更新日志）
- [x] PM progress 3文件 + daily-sync 更新

### DEC-011 文档同步 + 6项过期信息修复 ✅

**完成时间**: 2026-02-24 15:10
**任务类型**: 文档同步 + 过期信息修复

**完成内容**:
- [x] 读取 TEAM_CHAT 最新 420 行 + DECISIONS.md + PROJECT_STATUS.md + TODAY_FOCUS.md + PENDING.md
- [x] DEC-011 纳入 PROJECT_STATUS.md（交付形式+条漫模式+短视频模式+专业参数+架构策略）
- [x] 6项过期信息修复（Coordinator 指出的 PROJECT_STATUS ×4 + TODAY_FOCUS ×2）
- [x] 额外修复：时间戳、TASK-ASPECT-2x3 遗留标记、TODAY_FOCUS 头部状态、更新日志
- [x] TEAM_CHAT 发布执行报告
- [x] PM progress 3文件更新 + daily-sync 更新

### Coordinator 后续跟进 4 项 ✅

**完成时间**: 2026-02-24 14:14
**任务类型**: 执行 + 验证 + 核验

**完成内容**:
- [x] CLAUDE.md 4 项修改执行（Coordinator 14:10 审核通过后立即执行）
- [x] PENDING.md 同步更新（问题 A：TASK-REF-PREPROCESS/SCENE-REF-ASPECT/GIT-COMMIT-2 全部归档）
- [x] 5 Agent 响应统一验证 — 5/5 通过（逐一读取 current.md 对照 Coordinator 要求）
- [x] DevOps 3 commit 核验 — 3/3 通过（git show --stat + 安全性 + scene_reference_manager.py 修改入库确认）

### Coordinator 6项任务执行 ✅

**完成时间**: 2026-02-24 11:40
**任务类型**: 协调 + 排查 + 方案制定 + 通知

**完成内容**:
- [x] P0: TASK-SCENE-REF-ASPECT 排查 — 确认 `scene_reference_manager.py:431` 遗漏 `16:9`，派发 @backend
- [x] P1: TASK-GIT-COMMIT-2 提交方案 — 3批方案（Backend/Frontend/Docs），派发 @devops
- [x] P1: CLAUDE.md 更新草案 — 4项修改提交 Coordinator 审核
- [x] P2: 通知 5 Agent 更新 progress — 逐一通知 + PM 自查修复（时间戳矛盾+Step5缺失）
- [x] P2: PROJECT_STATUS.md 全面更新 — 补充 11 天缺失内容
- [x] P2: 下一阶段优先级建议 — 推荐 Phase 4.5→抖音首发→条漫B→6人一致性

**待闭环**: CLAUDE.md 执行（待审核）、TASK-SCENE-REF-ASPECT 核验（待 @backend）、Agent progress 统一验证

---

## 2026-02-14

### TASK-REF-PREPROCESS Step 5 汇总报告 ✅

**完成时间**: 2026-02-14 17:34
**任务类型**: 汇总报告

**完成内容**:
- [x] 汇总 Step 1-4 执行结果
- [x] 对比测试分析：效果"无变化~略有改善"（shot_34 白边 ~4%→~2-3%，shot_36/22 无变化）
- [x] 建议：保留预处理代码作为安全网
- [x] TEAM_CHAT 发布 Step 5 汇总报告

### TASK-LP-PAGES-FIX 复验通过 ✅

**完成时间**: 2026-02-14 17:35（时间戳修正：原记录 17:22 有误，实际在 Frontend 17:30 完成之后）
**任务类型**: 复验
**触发**: Frontend 完成 4/4 修复 (17:30)

**完成内容**:
- [x] 阅读 TEAM_CHAT 最新 300 行（Frontend 完成报告 + 修复方案回顾）
- [x] 阅读 frontend-progress/context-for-others.md
- [x] 逐文件代码审查：Footer.tsx, CTASection.tsx, page.tsx, layout.tsx
- [x] FIX-1 验证：`openSubPagesInNewTab` prop 三层逻辑（锚点/新标签页/Link）
- [x] FIX-1 验证：首页传 `openSubPagesInNewTab`，marketing layout 默认 false
- [x] FIX-1 验证：CTASection "直接登录" `target="_blank"` ✅
- [x] FIX-2 验证：10个 page.tsx 均为 Server Component（无 `"use client"`）
- [x] FIX-2 验证：10个 *Content.tsx 均有 `"use client"` 指令
- [x] FIX-2 验证：metadata 逐项对照 PM 方案 10/10 一致
- [x] FIX-3 验证：Footer 内链用 `<Link>`（与 FIX-1 合并实现）
- [x] FIX-4 验证：`shakeTimerRef` + `apiTimerRef` + `clearTimers` + unmount cleanup
- [x] 构建验证：`npm run build` 15/15 static pages 通过
- [x] TEAM_CHAT 发布复验报告
- [x] 更新 pm-progress 3个文件 + team-brain 文档

**评分**: 4.8/5（从 4.0 提升至 4.8）

---

### TASK-LP-PAGES 验收 + TASK-LP-PAGES-FIX 修复派发 ✅

**完成时间**: 2026-02-14 16:55
**任务类型**: 验收 + 任务管理
**触发**: Frontend 完成报告 (17:00) + Founder 反馈

**完成内容**:
- [x] 阅读 TEAM_CHAT Frontend 完成报告（4 Phase, 17新建+1修改）
- [x] 阅读 frontend-progress/context-for-others.md
- [x] 逐文件阅读全部 18 个文件（17新建+1修改），对照内容文档核验
- [x] 内容还原度验证：10页面文案100%还原（价格/FAQ数量/条款章节等抽查通过）
- [x] 交叉链接验证：15+链接全部正确
- [x] 交互功能验证：FAQ/联系表单/定价切换/登录流程全部到位
- [x] 价格计算验证：Pro¥441=49×12×0.75 ✅，Max¥1341=149×12×0.75 ✅
- [x] 发现 P0 问题：子页面链接应新开标签页（Founder 确认）
- [x] 发现 P1-1：11个页面缺 SEO metadata
- [x] 发现 P1-2：Footer 内链用 `<a>` 未用 `<Link>`
- [x] 发现 P2-1：登录页 setTimeout 无清理
- [x] 向 Founder 汇报验收结果 + 分析两种方案差异
- [x] Founder 确认方案：区分首页/子页面 + 全部修复
- [x] TEAM_CHAT 发布 TASK-LP-PAGES-FIX 4项修复任务
- [x] 更新 pm-progress 3个文件 + team-brain 文档

**验收结果**: 4.0/5（内容5/5, 交互5/5, 联动5/5, 导航3/5, SEO 2/5, 代码4/5）

---

### TASK-LP-PAGES 内容文档撰写 + 任务派发 ✅

**完成时间**: 2026-02-14 16:19
**任务类型**: 内容撰写 + 任务管理
**触发**: Founder 指令（Landing Page 子页面）

**完成内容**:
- [x] 探索 Frontend 代码库（Next.js 14 架构、组件、路由、设计系统）
- [x] 设计技术方案（(marketing) 路由组 + 6 个新组件 + Footer 修改）
- [x] 撰写定价体系（Free/Pro¥49/Max¥149，年付75折，4条定价FAQ）
- [x] 撰写关于我们（品牌故事 + 产品理念 + 3个核心价值卡片）
- [x] 撰写帮助中心（4个分类卡片）
- [x] 撰写使用教程（3步骤流程）
- [x] 撰写常见问题（15条FAQ，4个分类）
- [x] 撰写联系我们（3种联系方式 + 表单验证规则）
- [x] 撰写加入我们（团队文化 + 3个职位JD）
- [x] 撰写使用条款（8章完整法律条款）
- [x] 撰写隐私政策（9章完整隐私政策）
- [x] 设计登录页交互流程（Demo邀请码 XUHUA2026 + 成功/失败/空值/震动）
- [x] 制定 11 项验收标准
- [x] 发布任务到 TEAM_CHAT（@frontend）
- [x] 更新 pm-progress 3 个文件 + team-brain 文档

**交付物**: `.team-brain/handoffs/TASK-LP-PAGES-CONTENT.md`

---

### TASK-ASPECT-2x3 PM 核验通过 ✅

**完成时间**: 2026-02-14 11:01
**任务类型**: 验收核验
**触发**: Backend 完成报告 (10:56)

**完成内容**:
- [x] 阅读 Backend TEAM_CHAT 完成报告（26 处修改 double check 表格）
- [x] 阅读 backend-progress/context-for-others.md
- [x] grep 核验 `app/` 目录：27 处 `"2:3"` 全部正确
- [x] grep 核验旧值残留：仅 4 处合理保留（docstring + 场景参考图 + valid_ratios）
- [x] 确认 Backend 额外决策合理（智能推断统一 2:3，条漫排版一致性）
- [x] 确认 AI-ML prompt 文本无需修改（全面排查已完成）
- [x] 更新 pm-progress 全部 3 个文件 + team-brain 相关文档

**核验结果**: ✅ 26/26 通过 + 4 处合理保留

---

### TASK-ASPECT-2x3 全面排查 + 执行方案发布 ✅

**完成时间**: 2026-02-14 10:44
**任务类型**: 需求分析/任务分配
**触发**: Founder 指令（条漫为主，抖音适配 2:3）

**完成内容**:
- [x] 调查当前系统所有组件的宽高比设置
- [x] 对比抖音 2:3 vs 系统当前 9:16/16:9 差异
- [x] 全面排查 app/ 下所有 aspect_ratio 代码位置（9文件25处）
- [x] 发布完整执行方案到 TEAM_CHAT（含行号、当前值、目标值）
- [x] 分配给 @Backend 执行

**更新的文档**:
- `.team-brain/TEAM_CHAT.md` - 执行方案 + 补充完整清单
- `.team-brain/handoffs/PENDING.md` - 新增 TASK-ASPECT-2x3
- `.team-brain/status/TODAY_FOCUS.md` - 状态更新
- `.claude/agents/pm-progress/*` - 三个文件

---

## 2026-02-13

### TASK-REF-PREPROCESS Step 5 汇总报告 ✅

**完成时间**: 2026-02-13 17:34
**任务类型**: 汇总报告/决策建议
**触发**: Tester 完成 Step 4 (17:05)

**完成内容**:
- [x] 阅读 TEAM_CHAT Tester 17:05 消息（Step 4 对比验证报告）
- [x] 阅读 tester-progress 全部3个文件
- [x] 综合评估5个维度（代码质量、改善效果、负面影响、成本、风险）
- [x] 撰写 Step 5 汇总报告（任务回顾、执行过程、结果、评估、建议、后续路线图）
- [x] 向 Founder 提出两项决策请求（闭环确认 + 后续方案）

**更新的文档**:
- `.team-brain/TEAM_CHAT.md` - Step 5 汇总报告
- `.team-brain/handoffs/PENDING.md` - Step 4/5 状态更新
- `.team-brain/status/TODAY_FOCUS.md` - Agent 状态更新
- `.team-brain/daily-sync/2026-02-12.md` - PM 第十六次更新
- `.claude/agents/pm-progress/*` - 三个文件

---

### TASK-REF-PREPROCESS Step 3 核验 + Step 4 指引发布 ✅

**完成时间**: 2026-02-13 16:38
**任务类型**: 核验/指引发布
**触发**: Backend 完成 Step 3 (16:24)

**核验内容**:
- [x] 阅读 TEAM_CHAT Backend 16:24 消息（Step 3 完成）
- [x] 阅读 backend-progress 全部3个文件
- [x] 验证输出文件：6张PNG（without/3 + with/3）+ comparison_report.json
- [x] 验证图片尺寸均为768x1344（9:16）
- [x] 审查 comparison_report.json：6次API全部成功
- [x] 发布 Step 4 详细指引（每shot观察区域+评估维度+报告模板+随机性提醒）

**更新的文档**:
- `.team-brain/TEAM_CHAT.md` - Step 3核验 + Step 4指引
- `.team-brain/handoffs/PENDING.md` - Step 3 ✅
- `.team-brain/status/TODAY_FOCUS.md` - Agent状态
- `.team-brain/daily-sync/2026-02-12.md` - PM第十五次更新
- `.claude/agents/pm-progress/*` - 三个文件

---

### TASK-REF-PREPROCESS Step 1+2 核验 ✅

**完成时间**: 2026-02-13 16:13
**任务类型**: 核验/审批
**触发**: AI-ML 完成 Step 1 (16:00)、Backend 完成 Step 2 (16:07)

**核验内容**:
- [x] 阅读 TEAM_CHAT AI-ML 16:00 消息（Step 1 完成）
- [x] 阅读 TEAM_CHAT Backend 16:07 消息（Step 2 完成）
- [x] 阅读 ai-ml-progress 全部3个文件
- [x] 阅读 backend-progress 全部3个文件
- [x] 审查 `image_generator.py` 实际代码：L183-214, L275, L631
- [x] Step 1 核验：3个shot选择合理（覆盖留白+留黑、单角色+双角色）
- [x] Step 2 核验：验收标准5/5（中心裁剪、只裁不拉伸、原图不受影响、日志、容差）
- [x] 发布 TEAM_CHAT 批准 Backend 执行 Step 3

**更新的文档**:
- `.team-brain/TEAM_CHAT.md` - 核验+批准Step 3消息
- `.team-brain/handoffs/PENDING.md` - 更新Step状态
- `.team-brain/status/TODAY_FOCUS.md` - 更新Agent状态
- `.team-brain/daily-sync/2026-02-12.md` - PM第十四次更新
- `.claude/agents/pm-progress/*` - 三个文件

---

### TASK-REF-PREPROCESS 执行方案制定 ✅

**完成时间**: 2026-02-13 15:39
**任务类型**: 执行方案制定/任务分配
**触发**: Founder DEC-009 批准方案A，指示 PM 制定执行方案

**完成内容**:
- [x] 仔细阅读 DEC-009 决策、AI-ML 建议代码、TEAM_CHAT 相关讨论
- [x] 制定5步执行方案（AI-ML选shot → Backend写代码 → 对比测试 → Tester验证 → PM汇总）
- [x] 明确 Step 1 + Step 2 可并行
- [x] 为 Backend 提供详细实现说明（位置、参考代码、验收标准）
- [x] 为 AI-ML 提供选shot要求
- [x] 为 Tester 提供对比验证标准
- [x] 发布 TEAM_CHAT 执行方案

**更新的文档**:
- `.team-brain/TEAM_CHAT.md` - 执行方案发布
- `.team-brain/handoffs/PENDING.md` - 新增 TASK-REF-PREPROCESS
- `.team-brain/status/TODAY_FOCUS.md` - Step 27 + 更新 Agent 状态
- `.team-brain/daily-sync/2026-02-12.md` - PM第十三次更新
- `.claude/agents/pm-progress/*` - 三个文件

---

## 2026-02-12

### 参考图预处理方案PM评估 ✅

**完成时间**: 2026-02-13 15:09
**任务类型**: 方案评估/决策建议
**触发**: AI-ML 17:48 完成参考图预处理方案探索，请求PM评估

**评估内容**:
- [x] 阅读 TEAM_CHAT AI-ML 17:48消息
- [x] 阅读 ai-ml-progress/context-for-others.md（详细方案+建议代码）
- [x] 阅读 ai-ml-progress/current.md（核心数据+边界分析）
- [x] 阅读 ai-ml-progress/completed.md（探索过程记录）
- [x] 四维评估：技术可行性✅、成本✅、效果🟡、风险✅

**评估结论**: 建议批准执行（方案A + 对比测试）

**更新的文档**:
- `.team-brain/TEAM_CHAT.md` - PM评估+Founder决策请求
- `.team-brain/daily-sync/2026-02-12.md` - PM第十二次更新
- `.claude/agents/pm-progress/*` - 三个文件

---

### TASK-GIT-COMMIT 核验 ✅

**完成时间**: 2026-02-12 17:27
**任务类型**: 产品验收/核验
**参与者**: PM（核验）, DevOps（执行）

**核验范围**:
- [x] `git log --oneline -5` — 3 commits顺序正确
- [x] `git status` — 5个post-commit文件（DevOps完成报告），属正常行为
- [x] `git show --stat a6a0359` — Step 1恰好5个frontend文件，message匹配
- [x] `git show --stat 08a0e9f` — Step 2恰好18个文档文件，message匹配
- [x] `git ls-files | grep .env` — 仅.env.example（模板），无泄露

**核验结论**: 通过 ✅

**Coordinator 3项协调事项全部闭环**:
1. ✅ TASK-GIT-COMMIT — PM方案→DevOps执行→PM核验
2. ✅ CLAUDE.md — PM草案→Coordinator审核→PM执行
3. ✅ PROJECT_STATUS.md — PM直接更新9处

**更新的文档**:
- `.team-brain/TEAM_CHAT.md` - 核验结果
- `.team-brain/handoffs/PENDING.md` - 归档TASK-GIT-COMMIT
- `.team-brain/status/TODAY_FOCUS.md` - 步骤25-26、Agent状态
- `.team-brain/daily-sync/2026-02-12.md` - PM第十一次更新
- `.claude/agents/pm-progress/*` - 三个文件

---

### CLAUDE.md 更新执行 ✅

**完成时间**: 2026-02-12 17:15
**任务类型**: 文档更新（Coordinator审核通过后执行）
**触发**: Coordinator 17:09 审核通过CLAUDE.md草案4/4

**执行内容**:
1. Phase 5 状态 → `5.0/5 完美收官（TASK-LP-FIX 8/8 + TASK-LP-POLISH 2/2）`
2. Frontend 状态 → `空闲（Landing Page 5.0/5 完美收官）`
3. PM 状态 → `空闲（TASK-LP-POLISH 复验通过 5.0/5，等待Founder指令）`
4. 删除 `⚠️ 重要：需架构重构` 警告段落（5行）

**更新的文档**:
- `CLAUDE.md` - 4处更新
- `.team-brain/TEAM_CHAT.md` - 完成通知+@DevOps执行Step 2
- `.team-brain/handoffs/PENDING.md` - TASK-GIT-COMMIT Step 2状态
- `.team-brain/status/TODAY_FOCUS.md` - 步骤21-24、Agent状态
- `.team-brain/daily-sync/2026-02-12.md` - PM第十次更新
- `.claude/agents/pm-progress/*` - 三个文件

---

### Coordinator 3项协调事项执行 ✅

**完成时间**: 2026-02-12 16:30
**任务类型**: 项目管理/文档更新
**触发**: Coordinator 全局检查发现3项协调事项 (16:24)

**执行内容**:
1. **TASK-GIT-COMMIT 方案** → 制定2步commit方案，发到TEAM_CHAT分配@DevOps
2. **CLAUDE.md 草案** → 草拟4处修改，发到TEAM_CHAT请@Coordinator审核
3. **PROJECT_STATUS.md 更新** → 直接更新9处（周日期、架构重构状态、AI-ML任务、V3问题、LP章节、Frontend/DevOps模块）

**更新的文档**:
- `.team-brain/TEAM_CHAT.md` - PM回复消息
- `.team-brain/status/PROJECT_STATUS.md` - 9处更新
- `.team-brain/handoffs/PENDING.md` - 新增 TASK-GIT-COMMIT
- `.team-brain/status/TODAY_FOCUS.md` - 步骤20-21、Agent状态
- `.team-brain/daily-sync/2026-02-12.md` - PM第九次更新
- `.claude/agents/pm-progress/*` - 三个文件

---

### TASK-LP-POLISH 复验 ✅

**完成时间**: 2026-02-12 16:11
**任务类型**: 产品验收/复验
**参与者**: PM（复验）, Frontend（执行修复）

**复验范围**:
- [x] 读取 Pipeline.tsx（120行）— 验证4处rgba全部改为CSS变量引用
- [x] 读取 HeroSection.tsx（280行）— 验证useRef+pauseAndResume+unmount cleanup
- [x] 读取 globals.css（210行）— 验证3个RGB分量变量定义

**复验结果**: 2/2 通过，4.5/5 → **5.0/5**

| 编号 | 组件 | 验证要点 | 结果 |
|------|------|----------|------|
| LP-POLISH-1 | Pipeline.tsx | globals.css 3个RGB变量(line 10/12/13) + Pipeline.tsx 4处引用(line 19/30/41/92) | ✅ 零硬编码 |
| LP-POLISH-2 | HeroSection.tsx | resumeTimerRef(line 37) + clearResumeTimer(line 42-47) + pauseAndResume(line 50-54) + unmount cleanup(line 57-59) + 4处统一调用(line 82/89/96/205) | ✅ 零泄漏 |

**协议遵守**: Frontend 未动共享文档（PENDING/PROJECT_STATUS），由 PM 统一更新 ✅

**更新的文档**:
- `.team-brain/TEAM_CHAT.md` - 复验结果
- `.team-brain/handoffs/PENDING.md` - 归档 TASK-LP-POLISH
- `.team-brain/status/PROJECT_STATUS.md` - Phase 5 评分、changelog
- `.team-brain/status/TODAY_FOCUS.md` - 全流程闭环（19步）
- `.team-brain/daily-sync/2026-02-12.md` - PM第八次更新
- `.claude/agents/pm-progress/current.md` - 当前状态
- `.claude/agents/pm-progress/context-for-others.md` - 给其他Agent的信息
- `.claude/agents/pm-progress/completed.md` - 本记录

**影响范围**: Founder（等待指令）

---

### TASK-LP-POLISH 任务分配 ✅

**完成时间**: 2026-02-12 15:56
**任务类型**: 任务分配
**参与者**: Founder（批准）, PM（分配）

**完成内容**:
- [x] 向Founder说明 4.5/5 剩余 0.5 分的具体扣分点
- [x] Founder 批准修复
- [x] 制定 TASK-LP-POLISH 2项修复任务
- [x] 发布到 TEAM_CHAT 分配给 @Frontend
- [x] 更新 PENDING.md、TODAY_FOCUS.md、pm-progress×3、daily-sync

**影响范围**: Frontend（执行修复）

---

### TASK-LP-FIX 复验 ✅

**完成时间**: 2026-02-12 15:45
**任务类型**: 产品验收/复验
**参与者**: PM（复验）, Frontend（执行修复）

**背景**:
- Landing Page 初次验收 4.0/5（13:30），发现1个P0+3个P1+4个P2问题
- Founder 决策 DEC-008: Option A 品牌叙事路线（14:09）
- Frontend 执行 TASK-LP-FIX 8个修复任务（14:35完成）
- PM 进行复验

**复验范围**:
- [x] 读取 Pipeline.tsx（120行，整体重写）— 6项LP-P0-1验收标准逐一核对
- [x] 读取 Showcase.tsx（337行，整体重写）— lightbox/modal、分类、标题
- [x] 读取 ValueProposition.tsx（112行）— 三大卖点文案
- [x] 读取 HeroSection.tsx（263行）— 滑入动效、Slogan
- [x] 读取 globals.css（207行）— prefers-reduced-motion
- [x] 对比 LANDING_PAGE_ARCHITECTURE.md 架构规范

**复验结果**: 8/8 通过，4.0/5 → **4.5/5**

| 编号 | 优先级 | 任务 | 结果 | 验证要点 |
|------|--------|------|------|----------|
| LP-P0-1 | **P0** | Pipeline.tsx → FrameSpark™ 品牌氛围模块 | ✅ | 3组ambient glow动画、水平光线、品牌大号展示、"每个人都有自己的故事"、无技术术语 |
| LP-P1-1 | P1 | Showcase lightbox/modal | ✅ | AnimatePresence、Esc/←/→键盘导航、dot分页、body scroll lock、图片计数器 |
| LP-P1-2 | P1 | 移除"古风武侠"空分类 | ✅ | 仅保留：全部/都市情感/科幻冒险 |
| LP-P1-3 | P1 | ValueProposition 文案 | ✅ | "即发即用"/"角色如一"/"双输出形式" + 高亮badges |
| LP-P2-1 | P2 | Hero 条漫从右向左滑入 | ✅ | initial={{x:300}} → animate={{x:0}}，逐张递增 |
| LP-P2-2 | P2 | Slogan 统一 | ✅ | "FrameSpark™ AI条漫引擎" (line 117) |
| LP-P2-3 | P2 | Showcase 标题 | ✅ | "更多创作可能" |
| LP-P2-4 | P2 | prefers-reduced-motion | ✅ | @media (prefers-reduced-motion: reduce) 完整实现 |

**非阻塞观察（3项）**:
1. Pipeline.tsx rgba(255,149,0,0.15) 硬编码，建议改用CSS变量
2. HeroSection.tsx setTimeout 未在 useEffect cleanup 中清理
3. Frontend 直接更新了 PENDING.md 和 PROJECT_STATUS.md（协议要求PM统一更新）

**更新的文档**:
- `.team-brain/TEAM_CHAT.md` - 复验结果
- `.team-brain/handoffs/PENDING.md` - 归档 TASK-LP-FIX
- `.team-brain/status/PROJECT_STATUS.md` - Phase 5 状态、Frontend模块
- `.team-brain/status/TODAY_FOCUS.md` - 全流程闭环
- `.team-brain/daily-sync/2026-02-12.md` - PM第六次更新
- `.claude/agents/pm-progress/current.md` - 当前状态
- `.claude/agents/pm-progress/context-for-others.md` - 给其他Agent的信息
- `.claude/agents/pm-progress/completed.md` - 本记录

**影响范围**: Frontend（非阻塞观察供后续参考）, Founder（等待指令）

---

### 时间戳规范制定 + CLAUDE.md更新 ✅

**完成时间**: 2026-02-12 14:20
**任务类型**: 流程规范/文档维护

**完成内容**:
- [x] 修正全部33处非实时时间戳（10个文件）
- [x] 制定时间戳规范，更新 TEAM_PROTOCOL.md
- [x] 在 TEAM_CHAT.md 发布全团队通知
- [x] 更新 CLAUDE.md 项目状态（2026-02-03→2026-02-12）
- [x] 更新 CLAUDE.md Agent状态表、Phase进度、关键决策
- [x] 更新 CLAUDE.md "条漫文字渲染"章节（架构重构已完成）

**影响范围**: 全团队（时间戳规范），所有新Agent（CLAUDE.md更新）

---

### TASK-LP-FIX 任务分配 ✅

**完成时间**: 2026-02-12 14:09
**任务类型**: 决策执行/任务分配
**参与者**: Founder（DEC-008决策）, PM（方案制定+分配）

**完成内容**:
- [x] 向Founder展开分析P0 Pipeline.tsx两个选项的利弊
- [x] Founder决策 Option A: 品牌叙事路线
- [x] 记录 DEC-008 到 DECISIONS.md
- [x] 制定8个修复任务的详细执行方案
- [x] LP-P0-1: Pipeline.tsx重设计（含验收标准6项）
- [x] LP-P1-1~P1-3: Showcase lightbox、空分类、文案调整
- [x] LP-P2-1~P2-4: Hero滑入、Slogan统一、标题统一、reduced-motion
- [x] 发布到 TEAM_CHAT 分配给 @Frontend
- [x] 更新 DECISIONS.md、PENDING.md、TODAY_FOCUS.md、PROJECT_STATUS.md
- [x] 更新 pm-progress 三个文件 + daily-sync

**影响范围**: Frontend（执行修复）

---

### Landing Page 验收 ✅

**完成时间**: 2026-02-12 13:30
**任务类型**: 产品验收/代码审查
**参与者**: PM（验收）, Frontend（实现）

**背景**:
- Frontend 于 2026-01-29 完成 Landing Page 基础版本
- PM 因 V5 修复、边缘问题分析、抖音运营指南、Git初始化等任务延迟验收
- Frontend 在 TEAM_CHAT 中催促，PM 于 2026-02-12 正式执行验收

**验收范围**:
- [x] 读取 LANDING_PAGE_ARCHITECTURE.md（7模块架构规范）
- [x] 读取 LANDING_PAGE_VISUAL_SPEC.md（完整视觉设计系统）
- [x] 审查 page.tsx、layout.tsx、globals.css、tailwind.config.ts
- [x] 审查全部8个组件：Header、HeroSection、ValueProposition、Pipeline、Showcase、Stats、CTASection、Footer
- [x] 对比架构文档与实际实现
- [x] 验证条漫素材集成情况
- [x] 发布验收报告到 TEAM_CHAT

**验收结果**: 4.0/5

| 维度 | 评分 | 说明 |
|------|------|------|
| 视觉还原度 | 4.5/5 | CSS变量37个token完全匹配，品牌色/背景色/字体准确 |
| 组件完成度 | 4.0/5 | 8个组件全部实现，Stats是优秀的自主发挥 |
| 架构规范符合度 | 3.5/5 | Pipeline.tsx 与架构要求有P0级偏差 |
| 代码质量 | 4.0/5 | TypeScript规范，组件化清晰，Framer Motion动效好 |

**发现问题**:

| 优先级 | 问题 | 组件 |
|--------|------|------|
| **P0** | Pipeline.tsx 暴露5阶段技术流程，违反架构"保持神秘感" | Pipeline.tsx |
| P1 | Showcase 缺少 lightbox/modal 预览 | Showcase.tsx |
| P1 | "古风武侠" 分类存在但无作品 | Showcase.tsx |
| P1 | ValueProposition 文案过于技术化 | ValueProposition.tsx |
| P2 | Hero 轮播未实现从右侧滑入 | HeroSection.tsx |
| P2 | Slogan 与架构文档不一致 | HeroSection.tsx |
| P2 | 缺少 prefers-reduced-motion 支持 | globals.css |

**P0 决策请求**:
- Option A: 按架构文档重新设计，用品牌叙事替代技术流程展示
- Option B: 保留当前技术流程展示，更新架构文档

**更新的文档**:
- `.team-brain/TEAM_CHAT.md` - 验收报告
- `.team-brain/status/TODAY_FOCUS.md` - 任务状态更新
- `.team-brain/handoffs/PENDING.md` - Landing Page 后续任务
- `.team-brain/status/PROJECT_STATUS.md` - Phase 5 状态更新
- `.team-brain/daily-sync/2026-02-12.md` - PM第三次更新
- `.claude/agents/pm-progress/current.md` - 当前状态
- `.claude/agents/pm-progress/context-for-others.md` - 给其他Agent的信息
- `.claude/agents/pm-progress/completed.md` - 本记录

**影响范围**: Frontend（修复P1/P2）, Founder（P0决策）

---

### TASK-GIT-INIT 全流程管理 ✅

**完成时间**: 2026-02-12 12:00
**任务类型**: 方案制定/核验/文档管理
**参与者**: PM（方案+核验）, DevOps（执行）

**完成内容**:
- [x] 读取 DEC-007 决策
- [x] 调研项目目录结构，发现3个额外问题（frontend/.git、.env.example不完整、.DS_Store）
- [x] 制定完整5步执行方案（含.gitignore内容、.env.example内容、commit message、验证清单）
- [x] 发布到 TEAM_CHAT 分配给 @DevOps
- [x] DevOps 执行完成后独立核验
- [x] 安全验证 11/11、完整性验证 14/14
- [x] 更新所有共享文档（闭环）

**结果**:
- Git仓库已初始化，315文件被追踪，18MB
- DEC-007 全流程闭环：决策→方案→执行→核验→文档更新

---

## 2026-02-05

### 抖音运营指南 ✅

**完成时间**: 2026-02-05 10:00
**任务类型**: 运营规划/品牌设计
**参与者**: Founder

**交付物**: `docs/DOUYIN_BRAND_GUIDE.md`

**完成内容**:

| 模块 | 内容 |
|------|------|
| **账号设置** | 名称「一话故事」、介绍「用一组图，讲一个故事」 |
| **头像设计** | 2个Gemini 3 Banana Pro生图prompt（书+漫画格子+火花） |
| **发布模板** | 标题公式、描述结构、Hashtag分类 |
| **《最后一碗面》** | 完整发布方案（标题/描述/hashtag/封面/BGM） |

**品牌核心**:
- 账号名: **一话故事**
- 账号介绍: "用一组图，讲一个故事"
- 头像概念: 书+漫画格子+火花（融合FrameSpark™品牌）
- 品牌色: 暖光琥珀 #FF9500

**《最后一碗面》推荐发布**:
- 标题: "女儿喜欢的口味"——爸爸记了一辈子
- 封面: shot_12（笔记本特写）或 shot_10（车站送别）
- 时间: 晚上 20:00-22:00

---

## 2026-02-03

### TASK-RENAME-KAI-TO-JERRY 任务分配与验收 ✅

**完成时间**: 2026-02-03 21:30
**任务类型**: 任务分配/验收

**结果**:
- @Backend 完成172处"Kai"→"Jerry"替换
- shot_12验证成功，显示"你好，Jerry"
- 验证了通用工具的角色替换能力

---

### 边缘问题根因分析 ✅

**完成时间**: 2026-02-03 20:30
**任务类型**: 技术分析/问题诊断

**背景**:
- Tester V5验收发现7个shot有边缘留黑/留白问题 (04, 11, 15, 24, 31, 34, 39)
- Founder指出Web界面直接生图无此问题
- 需要调查API调用与Web界面的差异

**调查范围**:
- [x] 检查7个问题shot的prompt内容和类型
- [x] 检查参考图尺寸和宽高比
- [x] 检查API调用参数 (aspect_ratio, reference_images)
- [x] Web搜索Gemini API已知问题
- [x] 分析shot_15无参考图但仍有问题的情况

**根因分析结果**:

| 原因 | 严重程度 | 证据 |
|------|----------|------|
| **Gemini API已知问题** | 主因 | 开发者论坛多处报告 |
| **参考图宽高比不匹配** | 加剧因素 | Kai(0.730)/CC(0.778) vs 目标(0.562) |
| **特定Prompt关键词** | 次要因素 | SPLIT SCREEN/INTERIOR触发letterboxing |

**关键发现**:

1. **参考图尺寸问题**:
   - Kai_fullbody.png: 864x1184, ratio=0.730
   - CC_fullbody.png: 896x1152, ratio=0.778
   - 目标9:16: ratio=0.562
   - 参考图比目标9:16更宽，可能导致模型添加letterboxing

2. **shot_15无角色但仍有问题**:
   - 证明参考图不是唯一原因
   - 特定Prompt关键词（WIDE INTERIOR SHOT）可能是触发因素

3. **Gemini API已知问题**:
   - aspect_ratio参数不总是被尊重
   - 开发者论坛有多处报告
   - Web界面处理流程不同

**建议解决方案**:

| 方案 | 类型 | 负责方 |
|------|------|--------|
| 强化prompt边缘约束 | 短期 | AI-ML |
| 预处理参考图至9:16 | 中期 | Backend |
| 后处理边缘检测+裁剪 | 中期 | Backend |
| 等待API修复 | 长期 | Google |

**更新的文档**:
- `.claude/agents/pm-progress/current.md`
- `.claude/agents/pm-progress/context-for-others.md`
- `.claude/agents/pm-progress/completed.md` - 本记录
- `.team-brain/status/TODAY_FOCUS.md`
- `.team-brain/daily-sync/2026-02-03.md`

**影响范围**: Backend（后续可能任务）, AI-ML（prompt优化）

**来源**:
- https://discuss.ai.google.dev/t/108225
- https://support.google.com/gemini/thread/371311134
- https://github.com/vercel/ai/issues/9239

---

### PM V5修复预审查 ✅

**完成时间**: 2026-02-03 19:30
**任务类型**: 代码审查/质量把关

**背景**:
- Backend和AI-ML完成V5修复任务（19:00）
- PM在Tester验收前进行代码审查

**审查内容**:
- [x] Backend FIX-B1/B2/B3/B4 代码修改
- [x] AI-ML FIX-A1/A2/A3/A4 测试文件和模板修改
- [x] 发现FIX-A5遗留问题（shot_41叙事不一致）

**审查结果**:

| 类别 | 状态 |
|------|------|
| Backend FIX-B1 | ✅ 混合类型dialogue使用索引计算位置 |
| Backend FIX-B2 | ✅ 不再添加「」符号 |
| Backend FIX-B3 | ✅ 碰撞检测启用 |
| Backend FIX-B4 | ✅ 透明度配置化(180) |
| AI-ML FIX-A1 | ✅ 边缘填充约束 |
| AI-ML FIX-A2 | ✅ shot_27保护性触碰 |
| AI-ML FIX-A3 | ✅ shot_40男偷亲女 |
| AI-ML FIX-A4 | ✅ 角色一致性约束 |
| AI-ML FIX-A5 | ✅ shot_41叙事一致性（PM发现，AI-ML修复）|

**发现的问题**:
- FIX-A5: shot_41 image_prompt与shot_40修改不一致
- AI-ML已及时修复（19:15）

**更新的文档**:
- `.team-brain/TEAM_CHAT.md` - PM预审查报告 + FIX-A5确认
- `.team-brain/daily-sync/2026-02-03.md` - PM工作记录
- `.team-brain/status/TODAY_FOCUS.md` - 添加FIX-A5任务
- `.team-brain/analysis/V4_PM_COMPREHENSIVE_REVIEW.md` - 添加FIX-A5
- `.claude/agents/pm-progress/current.md` - 更新任务状态
- `.claude/agents/pm-progress/context-for-others.md` - 更新FIX-A5状态
- `.claude/agents/pm-progress/completed.md` - 本记录

**影响范围**: AI-ML（FIX-A5修复）, Tester（可以开始验收）

---

### V5任务分配及Founder澄清 ✅

**完成时间**: 2026-02-03 18:30
**任务类型**: 任务分配/决策执行

**背景**:
- PM独立综合复核完成（17:30）
- Founder审核并确认任务分配（18:00）
- Founder进一步澄清亲密度任务要求（18:30）

**Founder澄清**:
- shot_29牵手、shot_40亲吻都OK，不违和（两人约会后契合）
- shot_40需要改为男生偷亲女生（而非女生亲男生）
- shot_27挽臂是主要问题（出现在牵手之前违和）

**最终V5任务分配**:

| Agent | 任务 | 描述 | 优先级 |
|-------|------|------|--------|
| Backend | FIX-B1 | 气泡位置索引修复 | P0 |
| Backend | FIX-B2 | 移除「」符号 | P1 |
| Backend | FIX-B3 | 启用碰撞检测 | P1 |
| Backend | FIX-B4 | 透明度配置化 | P2 |
| AI-ML | FIX-A1 | 边缘填充约束 | P0 |
| AI-ML | FIX-A2 | shot_27挽臂→保护性触碰 | P0 |
| AI-ML | FIX-A3 | shot_40女亲男→男偷亲女 | P1 |
| AI-ML | FIX-A4 | 角色一致性 | P1 |

**更新的文档**:
- `.claude/agents/pm-progress/current.md`
- `.claude/agents/pm-progress/context-for-others.md`
- `.team-brain/status/TODAY_FOCUS.md`
- `.team-brain/TEAM_CHAT.md`
- `.team-brain/daily-sync/2026-02-03.md`

**影响范围**: Backend, AI-ML, Tester

---

### PM独立综合复核 ✅

**完成时间**: 2026-02-03 17:30
**任务类型**: 独立复核/质量把关/通用性分析

**背景**:
- Tester V4验收完成，评分4.5/5
- Founder要求PM独立查看所有图片、代码、prompt
- 核心原则：从**通用工具**角度分析，而非单一故事修复

**复核范围**:
- [x] comic_cc_kai_story (V1) 全部42张with_text_images
- [x] comic_cc_kai_story (V1) 全部42张no_text_images
- [x] comic_cc_kai_story_v2 (V2) 全部42张with_text_images
- [x] comic_cc_kai_story_v2 (V2) 全部42张no_text_images
- [x] 代码逻辑分析 (`app/services/text_overlay_service.py`)
- [x] 测试文件分析 (`tests/test_comic_cc_kai.py`)

**关键发现 (P0问题)**:

| 问题 | 类型 | 负责方 | 通用性影响 |
|------|------|--------|-----------|
| 气泡重叠 | 代码bug | Backend | 所有mixed type故事 |
| 「」符号保留 | 代码bug | Backend | 所有故事气泡 |
| 边缘填充 | Prompt | AI-ML | 所有故事画面 |
| 亲密度违规 | Prompt | AI-ML | 所有"初次约会"类故事 |

**代码根因分析**:
1. `text_overlay_service.py:499`: 混合类型dialogue全用固定位置(50,5)
2. `text_overlay_service.py:82-83`: strip_speaker_prefix添加「」符号
3. `text_overlay_service.py:119`: detect_overlay_collision定义但从未调用

**Prompt问题**:
1. 边缘填充约束不够强（6+ shots有白边/黑边）
2. 亲密度约束不够强（shot_40亲吻严重违规）
3. shot_27挽臂原意是"过马路时保护性触碰"，Prompt表达不够精准

**产出物**:
| 文件 | 说明 |
|------|------|
| `.team-brain/analysis/V4_PM_COMPREHENSIVE_REVIEW.md` | 完整综合分析报告 |

**建议的修复任务**:
- @Backend: FIX-B1(气泡位置), FIX-B2(「」符号), FIX-B3(碰撞检测)
- @AI-ML: FIX-A1(边缘填充), FIX-A2(亲密度), FIX-A3(角色一致性)

**影响范围**: Backend, AI-ML, Tester

---

### Tester V4验收任务分配 ✅

**完成时间**: 2026-02-03 16:30
**任务类型**: 任务分配/协调

**背景**:
- AI-ML 完成了所有 Prompt 优化任务（PROMPT-1/2/2B）
- Backend 架构重构和核心功能修复已完成
- 需要 Tester 执行 V4 验收

**V4验收内容**:
| 验收项 | 检查内容 |
|--------|----------|
| 边缘填充 | shot 01,17,22,34,35,36,39,42 无黑边/白边 |
| 亲密度 | shot 25,26,27 符合"首次约会"含蓄氛围 |
| 通用模板 | `docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md` v2.1 |
| 之前修复 | Speaker前缀剥离、气泡透明度、架构重构 |

**更新的文档**:
- `.team-brain/handoffs/PENDING.md` - 更新任务状态
- `.team-brain/TEAM_CHAT.md` - V4验收任务分配消息
- `.claude/agents/pm-progress/current.md` - 当前状态
- `.claude/agents/pm-progress/context-for-others.md` - 给Tester的任务指引
- `.claude/agents/pm-progress/completed.md` - 本记录
- `.team-brain/daily-sync/2026-02-03.md` - 今日工作

**影响范围**: Tester（执行验收）, PM（最终核验）

---

### PROMPT-2B 通用化任务分配 ✅

**完成时间**: 2026-02-03 15:30
**任务类型**: 任务分配/决策执行

**背景**:
- AI-ML 完成了 PROMPT-1（边缘填充）和 PROMPT-2（亲密行为约束）
- PROMPT-2 的实现放在了 `tests/test_comic_cc_kai.py` 中（一次性修复）
- **Founder决策**: 亲密行为约束应该是**通用模板**，供未来所有"初次约会"类故事使用

**问题分析**:
- AI-ML 在测试文件 shots 25-27 中硬编码了 INTIMACY LEVEL CONSTRAINT
- 这是一次性修复，不具备通用性
- 如果未来有其他"初次约会"故事，需要重复编写这些约束

**分配的任务**:
| 任务 | 内容 | 修复文件 |
|------|------|----------|
| PROMPT-2B | 亲密行为约束通用化 | `docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md` |

**任务要求**:
1. 在模板文档中创建 **"场景情境约束块"** 章节
2. 添加 **首次约会 (First Date)** 通用约束模板
3. 让未来任何"初次约会"类故事可以直接引用

**更新的文档**:
- `.team-brain/handoffs/PENDING.md` - PROMPT-2B 任务详情
- `.team-brain/TEAM_CHAT.md` - 任务分配消息（追加模式）
- `.claude/agents/pm-progress/current.md` - 当前状态
- `.claude/agents/pm-progress/context-for-others.md` - 给其他Agent的信息
- `.claude/agents/pm-progress/completed.md` - 本记录
- `.team-brain/daily-sync/2026-02-03.md` - 今日工作

**影响范围**: AI-ML（执行任务）, Tester（后续验收需检查通用模板）

---

### AI-ML Prompt优化任务分配 ✅

**完成时间**: 2026-02-03 15:00
**任务类型**: 任务协调/状态同步

**背景**:
- Backend完成架构重构(ARCH-1/2/3)和核心功能修复(CORE-1/2)
- 7类问题中还剩2类需要通过Prompt优化解决
- 需要给AI-ML分配详细任务

**完成内容**:
- [x] 读取Backend架构重构完成报告
- [x] 分析剩余的Prompt相关问题
- [x] 更新PENDING.md添加AI-ML任务详情
- [x] 在TEAM_CHAT.md追加任务分配消息（追加模式）
- [x] 更新PM progress文件

**分配的AI-ML任务**:

| 任务 | 问题 | 受影响shots | 修复文件 |
|------|------|------------|----------|
| PROMPT-1 | 边缘填充约束 | 01,17,22,34,35,36,39,42 | `docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md` |
| PROMPT-2 | 亲密行为约束 | 25,26,27 | `tests/test_comic_cc_kai.py` |

**PROMPT-1 方案**: 增强 `FULL CANVAS COMPOSITION` 指令块
```
FULL CANVAS COMPOSITION:
- Fill the ENTIRE image canvas edge-to-edge with meaningful visual content
- NO black borders, NO white margins, NO blank areas at ANY edge
- The composition must touch all four sides of the frame without any padding
```

**PROMPT-2 方案**: 添加亲密度约束
```
INTIMACY LEVEL CONSTRAINT (First Date):
- This is a FIRST DATE scenario - characters have just met
- Maintain appropriate physical distance (arm's length minimum)
- Body language should be warm but reserved, NOT overtly romantic
```

**更新的文档**:
- `.team-brain/handoffs/PENDING.md` - AI-ML任务详情
- `.team-brain/TEAM_CHAT.md` - 任务分配消息（追加模式）
- `.claude/agents/pm-progress/current.md` - 当前状态
- `.claude/agents/pm-progress/context-for-others.md` - 给其他Agent的信息
- `.claude/agents/pm-progress/completed.md` - 本记录

**影响范围**: AI-ML（执行任务）, Tester（后续验收）

---

### 14维度全量通用性分析完成 ✅

**完成时间**: 2026-02-03 12:30
**任务类型**: 深度分析/架构评审/通用性验证

**背景**:
- V3独立复核发现7类问题，但仍是针对单个故事的分析
- Founder要求"全维度分析，不要有任何遗漏"
- 需要从通用AI视频生成工具的角度重新审视所有问题

**完成内容**:
- [x] 14个维度全覆盖分析
- [x] 发现核心架构缺陷
- [x] 制定架构重构 + 功能修复执行计划
- [x] 更新所有PM和团队文档

**14个分析维度**:

| # | 维度 | 发现 |
|---|------|------|
| 1 | 代码架构 | 🔴 8份重复代码，主服务目录没有 |
| 2 | 文字类型 | 🟡 text_type处理不统一 |
| 3 | Speaker前缀 | 🔴 只有1个文件有函数，调用不完整 |
| 4 | 透明度 | 🔴 add_monologue正确，add_speech_bubble错误 |
| 5 | 碰撞检测 | 🟡 只对部分类型有效 |
| 6 | 位置检测 | 🟡 Haiku检测只在cc_kai实现 |
| 7 | 字体配置 | 🟡 硬编码macOS路径 |
| 8 | 图片尺寸 | 🟡 固定百分比不适应不同尺寸 |
| 9 | 视觉风格 | 🟡 所有故事用同一种气泡样式 |
| 10 | 错误处理 | 🟡 几乎没有 |
| 11 | 测试覆盖 | 🟡 无单元测试 |
| 12 | 文档 | 🟡 分散不完整 |
| 13 | 主流程集成 | 🟡 不在pipeline_orchestrator中 |
| 14 | 国际化 | 🟡 仅支持中文 |

**核心发现：架构缺陷（比功能bug更严重）**

**TextOverlayService在8个测试文件中重复定义，主服务目录没有！**

```
tests/test_comic_cc_kai.py          → 自己的 TextOverlayService + strip_speaker_prefix
tests/test_comic_story_b_wuxia_ink.py → 自己的（无strip_speaker_prefix）
tests/test_comic_story_c_cyberpunk.py → 自己的（无strip_speaker_prefix）
...共8个文件
```

**后果**:
- 修复cc_kai的bug，武侠/赛博朋克不受益
- 每个新故事要copy-paste一份代码
- **这不是通用工具，是8个独立的一次性脚本**

**执行计划**:
```
阶段0: 架构重构（必须先做）
├── ARCH-1: 创建 app/services/text_overlay_service.py
├── ARCH-2: 整合8个文件的最佳实现
└── ARCH-3: 所有测试改为import主服务

阶段1: 核心功能修复（在主服务中）
├── CORE-1: strip_speaker_prefix全覆盖
└── CORE-2: 气泡透明度正确实现

阶段2: Prompt优化
└── 边缘填充、亲密行为约束

全量验收（所有故事自动受益）
```

**产出物**:
| 文件 | 说明 |
|------|------|
| `.team-brain/analysis/V3_PM_INDEPENDENT_REVIEW_GENERALITY.md` | 14维度完整分析报告 |

**更新的文档**:
- CLAUDE.md - 项目状态和架构缺陷说明
- TEAM_CHAT.md - 通用性分析结果
- TODAY_FOCUS.md - 执行顺序
- PROJECT_STATUS.md - 项目状态
- PENDING.md - 架构重构任务详情
- daily-sync/2026-02-03.md - 今日工作
- pm-progress/*.md - PM进度

**影响范围**: Backend（执行重构）, 全团队（架构变更）

---

### V3独立复核完成 - 发现重大遗漏 ✅

**完成时间**: 2026-02-03 11:30
**任务类型**: 独立复核/质量把关

**背景**:
- Tester V3验收报告称"全部通过"，评分4.9/5
- Founder指出存在问题，要求PM独立审查

**PM独立复核内容**:
- [x] 查看所有42张with_text_images图片
- [x] 查看所有42张no_text_images图片
- [x] 阅读test_comic_cc_kai.py代码逻辑
- [x] 分析strip_speaker_prefix函数
- [x] 分析add_speech_bubble透明度实现
- [x] 对比Tester验收报告与实际情况

**发现的重大遗漏**:

| 问题 | Tester结论 | PM复核 | 严重程度 |
|------|-----------|--------|---------|
| Speaker前缀剥离(thought) | ✅ 通过 | ❌ 8处遗漏 | P0 |
| 气泡透明度 | ✅ 通过 | ❌ 完全无效 | P0 |
| 黑边/白边 | 未检测 | 🟡 9处问题 | P2 |
| 气泡重叠 | 未检测 | 🟡 3处问题 | P1 |
| 亲密行为不当 | 未检测 | 🟡 3处问题 | P1 |

**根因分析**:
1. Speaker前缀：`add_monologue()`不调用`strip_speaker_prefix()`
2. 透明度：PIL的`rounded_rectangle()`不正确处理alpha，需用`alpha_composite()`

**产出物**:
- `.team-brain/analysis/V3_PM_INDEPENDENT_REVIEW.md` - 完整复核报告
- TEAM_CHAT.md 更新 - 分配Backend P0修复任务

**下一步**:
- Backend完成TASK-B1, TASK-B2
- 重新生成V4
- 重新验收

**影响范围**: Backend, Tester, AI-ML

---

## 2026-02-02

### AI-ML P1完成 + Tester V3验收分配 ✅

**完成时间**: 2026-02-02 13:15
**任务类型**: 任务协调/状态同步

**背景**:
- AI-ML 完成了全部 P1 任务
- 需要更新共享文档、分配 Tester V3 验收任务

**AI-ML P1 完成内容**:

| 任务 | 问题 | 修复方案 |
|------|------|---------|
| TASK-4/8 | Shot 01双手腕, Shot 03六指 | ANATOMY REQUIREMENT指令块 |
| TASK-5/6 | Shot 28触发内容安全 | 移除敏感词+安全替换 |
| TASK-6/7 | Shot 34诡异手/身体 | COMPOSITION REQUIREMENT+POV视角 |

**PM完成内容**:
- [x] 更新 TEAM_CHAT.md 添加 AI-ML P1 完成汇总
- [x] 更新 TEAM_CHAT.md 分配 Tester V3 验收任务
- [x] 更新 PENDING.md 执行顺序
- [x] 更新 PROJECT_STATUS.md 任务状态
- [x] 更新 TODAY_FOCUS.md 当前任务
- [x] 更新 context-for-others.md
- [x] 更新 current.md

**Tester V3 验收清单**:
- Backend P1修复项（碰撞检测、3+气泡、半透明）
- AI-ML P1修复项（Shot 28生成、Shot 34构图、解剖正确性）
- 原有验收项（speaker前缀、气泡遮挡、风格一致性、角色一致性）

**影响范围**: Tester, PM

---

### Backend P1完成 + AI-ML P1任务分配 ✅

**完成时间**: 2026-02-02 12:45
**任务类型**: 任务协调/状态同步

**背景**:
- Backend 完成了全部 P1 任务
- 需要更新共享文档、分配 AI-ML P1 任务

**Backend P1 完成内容**:

| 任务 | 实现方案 | 关键代码 |
|------|---------|---------|
| TASK-3: 碰撞检测 | `add_monologue()` 返回 `(image, bar_height)` + `y_offset` 参数 | 垂直堆叠避免重叠 |
| TASK-4: 3+气泡支持 | `get_bubble_position_for_index(index, total)` | 交替左右布局 |
| TASK-5: 气泡半透明底 | `bubble_fill_color = (255, 255, 255, 191)` | 约75%不透明度 |

**PM完成内容**:
- [x] 更新 TEAM_CHAT.md 添加 Backend P1 完成汇总
- [x] 更新 TEAM_CHAT.md 分配 AI-ML P1 任务
- [x] 更新 PENDING.md 执行顺序
- [x] 更新 PROJECT_STATUS.md 任务状态
- [x] 更新 TODAY_FOCUS.md 当前任务
- [x] 更新 context-for-others.md
- [x] 更新 current.md

**AI-ML P1 任务分配**:

| 任务 | 问题 | 解决方案 |
|------|------|---------|
| TASK-6 | Shot 28 内容安全 | 重写敏感词 |
| TASK-7 | Shot 34 构图 | 边界约束 |
| TASK-8 | 解剖问题 | 全局约束Prompt |

**影响范围**: AI-ML, Tester, PM

---

### 并行任务协议制定 + 串行任务分配 ✅

**完成时间**: 2026-02-02 12:00
**任务类型**: 团队协作/流程优化

**背景**:
- 用户提出并行任务时可能出现文档编辑冲突
- 需要建立完整的文档分类和更新协议

**完成内容**:
- [x] 设计完整的文档所有权分类（5大类）
- [x] 更新 TEAM_PROTOCOL.md 添加并行任务协议
- [x] 添加文档分类速查表
- [x] 更新"每次完成工作后必更新"章节
- [x] 在群聊发布协议通知
- [x] 分配 Backend P1 任务（串行执行）

**文档分类**:

| 类型 | 文档 | 更新者 |
|------|------|--------|
| 私有 | `{agent}-progress/*.md` | 各Agent自己 |
| 共享-高频 | TEAM_CHAT/PENDING/PROJECT_STATUS/TODAY_FOCUS | PM统一 |
| 共享-谁创建谁维护 | analysis/*.md, HANDOFF-*.md | 创建者 |
| 共享-低频 | CLAUDE.md, TEAM_PROTOCOL.md, docs/*.md | 需审批 |
| 特殊 | daily-sync/*.md | 追加模式 |

**串行执行顺序**:
```
1️⃣ Backend P1（碰撞检测+3+气泡）← 当前
2️⃣ AI-ML P1（Shot 28/34重写+解剖约束）
3️⃣ Tester 验收
4️⃣ PM 核验
```

**影响范围**: 全团队

---

### Kai与Cici V2测试综合分析完成 ✅

**完成时间**: 2026-02-02 10:00
**任务类型**: 独立审查/通用化分析/任务协调

**背景**:
- V2测试（97.6%成功率）已通过Tester初步验收
- Founder详细审查后发现10+类新问题
- 要求PM独立审查所有图片，**从通用性角度思考**，而非仅解决这个故事的问题

**完成内容**:
- [x] 逐张审查41张no_text_images（shot 28失败）
- [x] 逐张审查41张with_text_images
- [x] 验证Founder反馈的10个问题点
- [x] 发现额外问题（对话归属错误等）
- [x] **从通用性角度分析根因**（区分Backend/AI-ML/PM责任）
- [x] 编写综合分析报告
- [x] 按优先级分类问题（P0/P1/P2）
- [x] 提出通用化解决方案
- [x] 分配任务给各Agent

**关键发现：系统性问题分类**

| 问题类别 | 数量 | 负责人 | 优先级 |
|---------|------|-------|--------|
| Speaker前缀未移除 | 15+ | Backend | **P0** |
| 气泡遮挡人脸 | 5+ | Backend | **P0** |
| 文字叠加重叠 | 4+ | Backend | P1 |
| 人体解剖问题 | 3+ | AI-ML | P1 |
| 内容安全限制 | 1 | AI-ML | P1 |
| 不必要边距 | 8+ | AI-ML | P2 |
| 亲密度不合理 | 3 | PM | P2 |
| 对话归属错误 | 1+ | PM | P1 |

**P0问题详解**:

1. **Speaker前缀未移除**
   - 现象: "Kai：「你好」" 完整显示，应只显示「你好」
   - 影响: 几乎所有对话气泡
   - 方案: 添加正则剥离逻辑

2. **气泡遮挡人脸**
   - 现象: Shot 12,16,23,31,40 气泡覆盖角色脸部
   - 原因: 固定位置算法未考虑角色位置
   - 方案: AI检测位置 或 安全区域约束

**通用化解决方案**:

所有方案设计考虑**适用于任何故事**，而非仅此测试用例:
- Speaker前缀剥离: 正则表达式支持各种格式
- 气泡位置: AI检测方案可处理任何角色组合
- 碰撞检测: 适用于任意数量的文字叠加
- Prompt约束: 模板化，可复用

**交付物**:

| 文件 | 说明 |
|------|------|
| `.team-brain/analysis/V2_COMPREHENSIVE_ANALYSIS_PM.md` | 综合分析报告 |

**任务分配**:

| 序号 | 负责人 | 任务 | 优先级 |
|------|--------|------|--------|
| 1 | @backend | Speaker前缀剥离 | **P0** |
| 2 | @backend | 气泡位置优化（避脸） | **P0** |
| 3 | @backend | 文字叠加碰撞检测 | P1 |
| 4 | @ai-ml | 解剖约束prompt | P1 |
| 5 | @ai-ml | 内容安全替代prompt | P1 |
| 6 | @ai-ml | 边距约束prompt | P2 |
| 7 | @pm | 亲密度指南制定 | P2 |

**影响范围**: Backend, AI-ML, PM, Tester

---

## 2026-01-31

### Kai与Cici故事PM V1独立审查完成 ✅

**完成时间**: 2026-01-31 16:00
**任务类型**: 独立审查/问题分析/任务协调

**背景**:
- Founder对42张测试图片进行详细审查，发现32+个问题
- 要求PM独立审查所有图片、对比成功测试、分析Prompt差异

**完成内容**:
- [x] 逐张审查42张no_text_images
- [x] 逐张审查42张with_text_images
- [x] 对比成功测试(comic_full_story_v2_20260127_opt005)
- [x] 分析Prompt模板差异，找到根本原因
- [x] 编写完整问题清单（32+问题分类整理）
- [x] 制定修复方案
- [x] 创建修复任务交接文档
- [x] 分配任务给AI-ML、Backend、Tester

**关键发现：Prompt模板是根本原因**

| 问题 | 失败测试 | 成功测试 |
|------|---------|---------|
| 禁止气泡 | ❌ 缺失 | ✅ 有 |
| 禁止留白 | ❌ 缺失+矛盾指令 | ✅ 有 |
| 约束强度 | 弱 | 强(ABSOLUTELY+FAIL) |

**问题统计**:

| 问题类型 | 数量 | 示例Shot |
|---------|------|---------|
| AI空白气泡 | 20+ | 06,12,16,21,22,23,27,28,29,33,40,41 |
| 留白/留黑 | 10+ | 02,03,08,34,35,36,42 |
| AI乱码文字 | 5+ | 13,18,30,38 |
| 服装错误 | 3+ | 21,22,38,39 |

**情感重点镜头问题**:
- Shot 38 拥抱：Cici穿红色大衣(应为黑色)、顶部底部乱码文字
- Shot 40 脸颊之吻：大面积空白气泡

**交付物**:

| 文件 | 说明 |
|------|------|
| `.team-brain/handoffs/HANDOFF-2026-01-31-012-CC-KAI-FIX.md` | 修复任务交接文档 |

**任务分配**:
- @ai-ml: 修复Prompt模板 (P0)
- @backend: 重新执行测试 (待AI-ML完成)
- @tester: 重新验收 (待Backend完成)

**影响范围**: AI-ML, Backend, Tester

---

## 2026-01-30

### Kai与Cici初次约会故事分镜大纲完成 ✅ (最新)

**完成时间**: 2026-01-30 11:00
**任务类型**: 需求分析/故事架构/分镜设计

**完成内容**:
- [x] 接收创始人提供的恋爱故事需求
- [x] 分析角色参考图（Kai、Cici）
- [x] 确认视觉风格：Korean Webtoon Style（韩漫风格）
- [x] 明确角色参考图使用规则（**仅脸部特征，服装用故事中描述的**）
- [x] **设计12幕故事架构**
- [x] **完成42张详细分镜大纲**（每shot含场景/构图/对话/旁白/内心独白）
- [x] 定义4个情感重点镜头
- [x] 创建详细交接文档
- [x] 更新所有progress和team-brain文档

**故事概要**:

| 项目 | 内容 |
|------|------|
| 故事名称 | Kai与Cici初次约会 |
| 题材 | 都市情感（恋爱） |
| 视觉风格 | Korean Webtoon Style |
| 图片数量 | 18-22张 |
| 输出格式 | 条漫 |

**角色设定**:

| 角色 | 年龄 | 服装（故事中） | 参考图用途 |
|------|------|--------------|-----------|
| Kai | 33岁 | 黑紫色毛衣+牛仔裤+黑大衣 | **仅脸部特征** |
| Cici | 33岁 | 黑色针织衫+浅灰裙+黑大衣+红丝巾 | **仅脸部特征** |

**情感重点镜头**:
1. 第一眼相见的心动
2. 散步时自然牵手
3. 下车后的拥抱告别
4. 意外的脸颊之吻

**交付物**:

| 文件 | 说明 |
|------|------|
| `.team-brain/handoffs/HANDOFF-2026-01-30-011-CC-KAI-STORY.md` | AI-ML详细交接文档 |

**任务分配**:
- @ai-ml: 完整故事脚本（Prompt + 文字脚本） → `docs/CC_KAI_STORY_SCRIPT.md`
- @backend: 测试脚本执行
- @tester: 验收测试

---

## 2026-01-29

### Landing Page 设计全部完成 + 交接 Frontend ✅ (最新)

**完成时间**: 2026-01-29 21:00
**任务类型**: 产品设计/需求定义

**完成内容**:
- [x] 阅读竞品分析（通义万相、Vidu、OiiOii、MovieFlow、HeyGen）
- [x] 与创始人确定首页形态、差异化卖点、技术品牌化
- [x] 确定首页形态：展示型（全屏条漫展示）
- [x] 确定主题模式：**Warm Dark Mode**（故事感深色）
- [x] 确定Pipeline品牌名：**FrameSpark™**
- [x] 设计7个模块的信息架构
- [x] **细化视觉规范**（配色、字体、间距、动效）
- [x] **创建详细交接文档给 Frontend**

**关键设计决策**:

| 决策 | 选择 | 原因 |
|------|------|------|
| 首页形态 | 展示型 | 用户需先理解产品再转化 |
| 主题模式 | **Warm Dark Mode** | 故事感深色，比科技纯黑更温暖 |
| Pipeline品牌 | FrameSpark™ | 呼应条漫"帧"，有能量感 |
| 主色调 | **#FF9500 暖琥珀** | 与Spark呼应，有温度 |
| 背景色 | **#121212 深炭灰** | 比纯黑更温暖 |
| 动效节奏 | 稍慢于竞品 (350-700ms) | 故事需要节奏，叙事感 |

**视觉规范亮点**:

| 维度 | 竞品典型 | 序话Story |
|------|---------|----------|
| 背景 | #0A0A0A 纯黑 | #121212 深炭灰 |
| 主色 | #3B82F6 冷蓝 | #FF9500 暖琥珀 |
| 情感 | 科技、专业 | 温暖、故事感 |
| 隐喻 | 实验室 | 咖啡馆、书房 |

**交付物**:

| 文件 | 说明 |
|------|------|
| `docs/LANDING_PAGE_ARCHITECTURE.md` | Landing Page架构定稿 |
| `docs/LANDING_PAGE_VISUAL_SPEC.md` | 视觉规范（配色、字体、间距、动效） |
| `.team-brain/handoffs/HANDOFF-2026-01-29-010-LANDING-PAGE.md` | Frontend详细交接文档 |

**交接状态**: ✅ 已交接 @Frontend，交接编号 HANDOFF-2026-01-29-010

**影响范围**: Frontend（正在实现）

---

### Landing Page架构定稿 ✅

**完成时间**: 2026-01-29 19:30
**任务类型**: 产品设计/需求定义

**背景**:
- 序话Story需要Landing Page来展示产品、吸引用户注册内测
- 阅读竞品分析文档，与创始人讨论设计方向

**模块架构**:
1. Header（吸顶导航）：作品展示 / 关于我们 / 申请内测
2. Hero Section：全屏单行条漫展示（故事A播完切换故事B）
3. FrameSpark™ 引擎：品牌化+酷炫动效
4. 差异化卖点：即发即用 / 角色如一 / 双输出形式
5. 作品Gallery：按题材分类，2-3个作品
6. 内测邀请CTA：邮箱注册 + 申请人数展示
7. Footer：版权信息

**Hero区素材选择**:
| 故事 | 题材 | 图片 |
|------|------|------|
| 故事A | 都市亲情 | shot_01-04 (接电话→火车→面馆→医院) |
| 故事B | 赛博朋克 | shot_01-04 (城市→主角→地铁站→黑市) |

---

### BUG-BUBBLE-001 验收通过 ✅

**完成时间**: 2026-01-29 13:00
**任务编号**: BUG-BUBBLE-001

**验收内容**: @Backend 修复的对话泡泡位置Bug

**修复方案**:
```python
def get_default_x_by_speaker_pos(pos: str) -> int:
    if pos == "right": return 70
    elif pos == "left": return 30
    else: return 50
```

**PM验收结果**:
| 验收项 | 结果 |
|--------|------|
| 代码逻辑 | ✅ 正确 |
| 向后兼容 | ✅ 不影响已有bubble_positions |

**结论**: 代码修复正确，验收通过

---

### `bubble_positions` 为空原因技术分析 ✅

**完成时间**: 2026-01-29 13:30
**任务编号**: 创始人提问 → PM 分析

**背景**: 创始人问"为什么 bubble_positions 会为空？是AI没有检测还是其他原因？"

**分析结论**:

`detect_character_positions()` 返回空字典的5种情况：

| 情况 | 代码位置 | 触发条件 |
|------|----------|----------|
| 1. 无角色 | 1176-1177 | `characters_in_scene` 为空 |
| 2. 无参考图 | 1179-1182 | 角色没有 fullbody 参考图 |
| 3. API失败 | 1252-1254 | 网络问题、配额限制、服务故障 |
| 4. JSON解析失败 | 1236 | Haiku 返回非 JSON 格式 |
| 5. AI未识别 | Prompt | Haiku 在图中没找到角色 |

**Fallback 机制风险评估**:

| 场景类型 | y=10% 遮挡风险 |
|----------|----------------|
| 中景/全景 | ✅ 低 |
| 特写镜头 | 🔴 高（可能遮挡头部）|

**PM 结论**:
- AI 检测成功率高，fallback 只是兜底
- 当前风险可控，暂不需要额外处理
- 若 fallback 频繁触发，可考虑根据 shot_type 调整 y 位置

**影响范围**: 已记录到 current.md 和 context-for-others.md

---

### TASK-VERIFY-001 全维度PM审查 + 发现Bug ✅

**完成时间**: 2026-01-29 12:30
**任务编号**: TASK-VERIFY-001-E

**审查范围**: 故事C《最后的记忆商人》15张镜头全维度审查

**审查维度与结果**:
| 维度 | 评分 | 说明 |
|------|------|------|
| 角色一致性 | ⭐⭐⭐⭐⭐ | 林夜义眼、老陈服装、凯拉金属臂全部镜头一致 |
| 叙事连贯性 | ⭐⭐⭐⭐⭐ | 5幕结构清晰，空间递进自然，情感层层推进 |
| 风格锁定 | ⭐⭐⭐⭐⭐ | 赛博朋克元素稳定，Shot 14对比设计出色 |
| 文字叠加 | ⭐⭐⭐ | **发现Bug: Shot 06对话泡泡位置错误** |
| 整体质量 | ⭐⭐⭐⭐ | 修复Bug后可用于产品演示 |

**关键亮点**:
- Shot 09: 凯拉双红色义眼 + 金属右臂渲染极其精细
- Shot 14: 明亮自然光与暗黑霓虹形成惊艳对比

**🐛 发现Bug: BUG-BUBBLE-001**

| 项目 | 说明 |
|------|------|
| 问题 | Shot 06 `speaker_position: "right"` 被忽略 |
| 现象 | 老陈说话，泡泡却在左上角（指向林夜） |
| 根因 | `dialogue` 类型不处理 `speaker_position` 参数 |
| 优先级 | P1（Phase 4之前修复） |

**PM结论**:
- 角色一致性和风格锁定验证通过
- 需修复 BUG-BUBBLE-001 后再进入 Phase 4

**建议**: @Backend 修复后重新生成受影响镜头

---

## 2026-01-28

### 故事C《最后的记忆商人》大纲 + 分镜设计完成 ✅

**完成时间**: 2026-01-28 18:00
**任务编号**: TASK-VERIFY-001-A

**任务类型**: 产品设计/故事大纲

**背景**:
- TASK-VERIFY-001 多风格通用性验证需要测试3个不同风格的故事
- 故事A（吉卜力/父女亲情）已完成
- 故事B（水墨/武侠）大纲已完成
- 故事C（赛博朋克/反乌托邦）需要设计

**完成内容**:
- [x] 设计故事大纲：《最后的记忆商人》
- [x] 世界观设定：2089年记忆可交易的反乌托邦
- [x] 3个角色详细设计（林夜、老陈、凯拉）
- [x] 3个场景详细设计（霓虹街区、记忆交易所、藏身处）
- [x] 15张分镜设计（含镜头、角色、旁白/对话）
- [x] visual_style参数配置
- [x] story.json完整文件

**交付物**:
| 文件 | 路径 |
|------|------|
| 设计稿 | `test_output/story_c_cyberpunk/story_outline.md` |
| story.json | `test_output/story_c_cyberpunk/story.json` |

**故事概要**:
在记忆被企业垄断的未来世界，黑市记忆商人林夜接到将死老人老陈的委托——保存关于"大崩溃"真相的禁忌记忆。企业安全官凯拉带队追捕，林夜护送老陈逃亡。最终在老陈的藏身处，林夜接收了这份记忆，看到了被抹杀的美丽旧世界。老陈安详离去，林夜肩负起守护真相的使命。

**验证重点**:
| 验证项 | 特殊挑战 |
|--------|----------|
| 角色一致性 | 赛博义眼、金属义肢需保持一致 |
| 风格稳定性 | 霓虹灯风格不能漂移 |
| 特殊元素 | 全息投影、神经接口等科技元素 |
| Shot 14 对比 | 记忆场景需与暗黑风格形成对比 |

**下一步**: @AI-ML 完善详细脚本（image_prompt + narration）

---

### TASK-RESILIENCE-001 验收通过 + 关键发现分析 ✅

**完成时间**: 2026-01-28 17:30
**验收状态**: ✅ 全部通过 (4/4 = 100%)

**任务类型**: 验收审查/产品洞察分析

**背景**:
- TASK-RESILIENCE-001 由 @Backend + @AI-ML 完成
- @Tester 执行验收，4/4 测试用例通过
- PM 审查测试图片，发现关键产品洞察

**完成内容**:
- [x] 阅读 TEAM_CHAT.md 完整记录（5000+行）
- [x] 阅读 PENDING.md 验收结果
- [x] 阅读 Tester context-for-others.md
- [x] 查看测试图片（Test 7 色情内容 + Test 10 自残内容）
- [x] 分析 Haiku 对不同内容类型的处理差异
- [x] 输出产品洞察和建议
- [x] 更新所有 PM 文档

**⭐ 关键发现：Haiku 对不同内容类型的处理差异**

| 内容类型 | Haiku 行为 | 图像结果 | 用户感知 |
|----------|-----------|----------|----------|
| 暴力/死亡/武侠 | ✅ 智能改写 | 保留情感，移除敏感词 | 无感知 |
| 自残/抑郁 | ✅ 智能改写 | 保留情绪氛围，移除具体行为 | 无感知 |
| **色情内容** | ❌ 拒绝改写 | 生成与原意图完全无关的图像 | ⚠️ 会察觉 |

**具体案例分析**:

- **Test 7 (色情内容)**:
  - Haiku 返回拒绝消息，不进行改写
  - Gemini 基于拒绝消息生成数字画板图片
  - 结果：图像与用户原意图完全无关

- **Test 10 (自残内容)**:
  - Haiku 成功改写，保留抑郁/绝望情绪
  - 图像显示连帽衫人物双手捂脸，桌上有暗示物品
  - 结果：艺术意图保留，无显性有害内容

**PM 产品建议**:

| 建议 | 优先级 | 说明 |
|------|--------|------|
| 创作入口内容引导 | **P1 新增** | 提示用户哪些内容类型无法支持 |
| 色情内容预检测 | P2 | 在调用 Haiku 改写前检测并提前拒绝 |
| 用户友好的"不支持"提示 | P1 | 替代当前的"无关图像"体验 |

**任务完成状态**:

| 任务 | 状态 |
|------|------|
| TASK-RESILIENCE-001-A 错误类型识别 | ✅ 完成 |
| TASK-RESILIENCE-001-B 智能改写+自动重试 | ✅ 完成 |
| TASK-RESILIENCE-001-C 友好失败提示 | ⏳ 待命（可启动） |

**影响范围**: 产品设计、前端 UX、内容策略

---

### Shot 06 失败根因分析 + TASK-RESILIENCE-001 定义 ✅

**完成时间**: 2026-01-28 00:30
**验收状态**: 分析完成，任务已定义 → **已完成**

**任务类型**: 问题分析/任务规划/长期规划

**背景**:
- TASK-VERIFY-001 故事B《断剑》测试中 Shot 06 生成失败
- 错误: `'NoneType' object is not iterable`
- 原因: Gemini 内容安全过滤，`response.parts` 返回 `None`
- 敏感词: "motionless youth", "dark spreading pool", "killer/victim"

**PM分析核心结论**:

| 层面 | 问题 | 解决方案 |
|------|------|----------|
| 产品层 | 武侠/悬疑题材必然涉及暴力 | 智能改写保留情感不触发过滤 |
| 技术层 | 缺乏错误分类 | 识别 CONTENT_SAFETY vs API_ERROR |
| 体验层 | 用户无法理解失败 | 友好提示 + 后台自动重试 |

**影响范围**: Backend, AI-ML, Frontend (待命)

---

## 2026-01-27

### TASK-OPT-005 PM独立审查验收通过 ✅

**完成时间**: 2026-01-27 22:00
**验收状态**: 全部通过

**任务类型**: 独立验收审查

**背景**:
- TASK-OPT-005-A/B/C 已由 AI-ML、Backend、Tester 完成
- 需要 PM 独立审查测试图片，确认遮挡问题已彻底修复

**审查方法**:
- 逐张查看 `test_output/comic_full_story_v2_20260127_opt005/` 目录
- 重点检查 shot_04、shot_07、shot_14 三张问题图片
- 对比修复前后的泡泡位置

**完成内容**:
- [x] 读取 TEAM_CHAT.md 了解完整完成记录
- [x] 查看 results.json 确认15张图片全部生成成功
- [x] 逐张审查关键问题图片

**审查结果**:

| Shot | 之前问题 | 审查结果 |
|------|---------|---------|
| shot_04 | 爸爸泡泡遮住整张脸 | ✅ 泡泡在头顶上方，不遮挡 |
| shot_07 | 小女孩泡泡稍远 | ✅ 泡泡位置对准角色，效果好 |
| shot_14 | 爸爸泡泡遮住额头 | ✅ 泡泡在头顶上方，不遮挡 |
| shot_09 | 红色强调功能 | ✅ 正常工作 |
| shot_01 | 顶部旁白 | ✅ 位置正确 |

**Haiku输出验证**:
```
Shot 04: daughter bubble_x=25, bubble_y=8; father bubble_x=75, bubble_y=10
Shot 07: daughter_child bubble_x=30, bubble_y=8; father_young bubble_x=70, bubble_y=12
Shot 14: daughter bubble_x=25, bubble_y=8; father bubble_x=75, bubble_y=18
```

**结论**: TASK-OPT-005 全部完成，Haiku智能推荐方案有效解决了泡泡遮挡问题

**影响范围**: 项目进入空闲状态，可接受新任务

---

### TASK-OPT-005 方案升级：Haiku智能推荐 ✅

**完成时间**: 2026-01-27 20:15
**验收状态**: 分析完成，方案已升级

**任务类型**: 方案优化/通用性评估

**背景**:
- 初始方案是让Haiku返回 `head_top_y_percent`
- 创始人提问：这是通用工具，能覆盖所有边缘情况吗？

**完成内容**:
- [x] 识别边缘情况（特写镜头、俯视/仰视、多人说话、非人类角色、躺着的角色等）
- [x] 评估初始方案的覆盖范围（无法处理多种边缘情况）
- [x] 提出升级方案（Haiku直接推荐泡泡位置）
- [x] 与创始人确认方案选择
- [x] 更新所有相关文档

**方案对比**:

| 对比项 | 初始方案 | 升级方案 |
|--------|----------|----------|
| Haiku输出 | `head_top_y_percent` | `bubble_x_percent, bubble_y_percent` |
| 代码逻辑 | 计算泡泡位置 | 直接使用AI推荐 |
| 边缘情况 | 需要额外处理 | AI自动考虑 |
| 通用性 | 中等 | **高** |

**支持的边缘情况**:
- ✅ 特写镜头 → AI推荐侧边
- ✅ 俯视/仰视 → AI理解透视
- ✅ 角色在顶部 → AI自动考虑边界
- ✅ 多人说话 → AI一次规划多个泡泡
- ✅ 非人类角色 → AI理解各种形态
- ✅ 躺着的角色 → AI理解姿态朝向

**已更新文档**:
- TEAM_CHAT.md - 添加方案升级决策
- PENDING.md - 更新任务说明
- TODAY_FOCUS.md - 更新任务详情
- pm-progress/current.md - 更新当前任务
- pm-progress/context-for-others.md - 更新任务指引

**影响范围**: AI-ML, Backend, Tester

---

### 泡泡遮挡问题独立分析 ✅

**完成时间**: 2026-01-27 19:30
**验收状态**: 分析完成，后续升级为智能推荐方案

**任务类型**: 问题分析/任务协调

**背景**:
- TASK-OPT-004（x坐标百分比）验收通过
- 创始人再次审查，发现泡泡遮挡角色头部
- shot_04爸爸泡泡遮住整张脸，shot_14遮住额头

**完成内容**:
- [x] 查看shot_04、shot_07、shot_14三张问题图片
- [x] 阅读test_comic_full_story_v2.py分析泡泡y坐标逻辑
- [x] 独立分析，找出问题根因（只有x坐标，没有y坐标）
- [x] 提出初始解决方案（Haiku返回head_top_y_percent）
- [x] 更新TEAM_CHAT记录分析结论
- [x] 分配新任务TASK-OPT-005-A/B/C

**关键发现**:

| 问题环节 | 当前设计 | 问题 |
|----------|----------|------|
| Prompt输出 | 只有x_percent | 缺少y坐标 |
| 泡泡y位置 | 固定（12%/25%/40%） | 不随角色头部位置变化 |

**后续**: 方案已升级为Haiku智能推荐（见上方记录）

**影响范围**: AI-ML, Backend, Tester

---

### TASK-OPT-004 x坐标百分比优化 ✅

**完成时间**: 2026-01-27 18:30
**验收状态**: 验收通过，但发现新问题（遮挡）

**任务类型**: 问题分析/任务协调

**背景**:
- 第一轮优化(TASK-OPT-001~003)验收通过
- 创始人审查测试图片，发现泡泡位置精度不足

**完成内容**:
- [x] 分析根因：只返回left/center/right，粒度太粗
- [x] 提出解决方案：Haiku返回x_percent百分比
- [x] 分配任务TASK-OPT-004-A/B/C
- [x] 全部验收通过

**创始人再次反馈**: x坐标改善明显，但泡泡遮住脸 → 触发TASK-OPT-005

---

### 泡泡位置精度问题独立分析 ✅

**完成时间**: 2026-01-27 17:30
**验收状态**: 分析完成，任务已执行完成

---

## 2026-01-26

### V2体验优化方案设计 ✅

**完成时间**: 2026-01-26 19:30
**验收状态**: 方案确定，任务已分配

**任务类型**: 技术方案设计/任务协调

**背景**:
- TASK-FIX-005/006验收通过后，创始人指出2项体验优化需求
- 需要考虑通用性（这是通用短视频工具，支持各种风格）

**完成内容**:
- [x] 逐张查看15张with_text_images
- [x] 识别问题并分析根因
- [x] 考虑通用性设计方案
- [x] 与创始人讨论确定最终技术方案
- [x] 搜索确认Claude 4.5 Haiku成本
- [x] 计算完整故事的检测成本
- [x] 分配优化任务并更新所有文档

**最终技术方案**:

| 问题 | 方案 | 成本 | 原理 |
|------|------|------|------|
| 透明度 | PIL亮度检测 | **零** | 分析叠加区域亮度，自动选择alpha |
| 角色位置 | Haiku+参考图比对 | **~$0.08-0.17/故事** | 多模态视觉分析，精确识别角色 |

**成本估算详情** (768×1344图像):
- 图像tokens计算: (768×1344)/750 ≈ 1,376 tokens
- Haiku定价: 输入$1/M, 输出$5/M
- 小故事(3角色,15shots): ~$0.08
- 大故事(6角色,25shots): ~$0.17

**新任务分配**:
- TASK-OPT-001 (@Backend): PIL亮度检测自适应透明度
- TASK-OPT-002 (@Backend): Haiku角色位置检测
- TASK-OPT-003 (@Tester): 优化验收

**影响范围**: Backend, Tester

---

### V2测试体验优化分析 ✅

**完成时间**: 2026-01-26 18:30
**验收状态**: 分析完成，进入方案设计

**任务类型**: 问题分析

**完成内容**:
- [x] 逐张查看15张with_text_images
- [x] 识别黑色背景透明度问题（6/15张）
- [x] 识别对话泡泡位置问题（shot_07）
- [x] 定位代码根因

**关键发现**:

| 问题 | 根因 |
|------|------|
| 黑色背景透明度 | alpha=191 (75%不透明) |
| shot_07泡泡位置 | speaker_position配置反了 |

**影响范围**: Backend, Tester

---

### V2测试二次修复验收通过 ✅

**完成时间**: 2026-01-26 17:35
**验收状态**: Tester验收通过

**任务类型**: 验收跟踪

**完成内容**:
- [x] 跟踪TASK-FIX-005完成状态
- [x] 跟踪TASK-FIX-006完成状态
- [x] 确认Tester验收结果

**验收结果**:
| 项目 | 首轮 | 修复后 |
|------|------|--------|
| 图片留白 | 10/15 | 0/15 ✅ |
| 乱码泄露 | 4/15 | 0/15 ✅ |
| 参考图生成 | 0/10 | 10/10 ✅ |
| 角色一致性 | ~90% | ~95% ✅ |

---

### V2测试图片独立分析 ✅

**完成时间**: 2026-01-26 (早些时候)
**验收状态**: 分析完成，发现问题 → 已全部修复

**任务类型**: 问题分析/任务协调

**背景**:
- 创始人指出V2测试"效果不尽如人意"
- 需要独立分析找出根因

**完成内容**:
- [x] 逐张查看15张no_text_images
- [x] 逐张查看with_text_images对比
- [x] 检查reference_images目录（发现为空）
- [x] 分析测试脚本代码找根因
- [x] 输出问题分析报告
- [x] 分配新修复任务 (TASK-FIX-005, TASK-FIX-006)
- [x] 更新所有团队文档

**关键发现**:

| 问题 | 根因 |
|------|------|
| 留白仍存在 | 测试脚本prompts有"Leave clean space"未删除 |
| 乱码泄露 | TEXT_FREE指令不够强 |
| 对话泡泡占位 | prompts提到"dialogue bubble"触发模型生成 |
| 参考图失败 | ReferenceImageManager初始化bug，目录为空 |

**任务完成状态**:
- TASK-FIX-005 (@AI-ML): ✅ 已完成
- TASK-FIX-006 (@Backend): ✅ 已完成

**影响范围**: AI-ML, Backend, Tester

---

## 2026-01-22

### 条漫MVP故事测试验收标准 ✅

**完成时间**: 2026-01-22
**验收状态**: 通过

**任务类型**: 需求定义/验收标准

**背景**:
- 创始人决定产品形态变更为「条漫优先」(DEC-006)
- 需要定义测试验收标准，验证Gemini生图能否达到产品质量要求
- 参考案例：`still_image_storyref/IMG_0804-0818.jpg`（15张都市情感条漫）

**完成内容**:
- [x] 阅读 DEC-005/DEC-006 产品决策
- [x] 逐张分析15张参考案例
- [x] 定义5个验收维度的详细标准
- [x] 输出验收checklist供 @Tester 使用
- [x] 更新TEAM_CHAT通知相关Agent

**交付物**:
| 文件 | 说明 |
|------|------|
| `docs/COMIC_MVP_TEST_ACCEPTANCE_CRITERIA.md` | 完整验收标准文档 |

**验收标准概要**:

| 维度 | 权重 | MVP及格线 | 关键验收点 |
|------|------|-----------|------------|
| 文字内嵌效果 | 25% | ≥3分 | 对话气泡、黑底旁白、白底旁白 |
| 合成效果 | 20% | ≥3分 | 分屏、回忆碎片、画中画 |
| 表情细腻度 | 20% | ≥3分 | 8种情绪面部特征 |
| 风格一致性 | 20% | ≥4分 | 线条/色彩/比例无漂移 |
| 角色一致性 | 15% | ≥4分 | 女主/男主/前任跨图可辨识 |

**MVP通过条件**: 综合分 ≥ 3.5 且所有单项 ≥ 3分

**影响范围**: AI-ML(Prompt设计参考), Backend(测试执行), Tester(验收)

---

## 2026-01-19

### 确认序话Story设计系统 ✅

**完成时间**: 2026-01-19
**验收状态**: 通过

**任务类型**: 需求确认/验收

**完成内容**:
- [x] 评审Frontend提出的设计系统方案
- [x] 确认Video-First Hero模式适合产品定位
- [x] 确认Dark Mode对创作者友好
- [x] 接收UI/UX Pro Max Skill能力升级

**关键决策**:
| 决策 | 选择 | 原因 |
|------|------|------|
| 风格 | Dark Mode (OLED) | 长时间创作减少眼疲劳 |
| 主色 | #3B82F6 (蓝) | 专业感、信任感 |
| CTA色 | #F97316 (橙) | 高对比引导核心动作 |
| 字体 | Plus Jakarta Sans | 现代SaaS风格 |

**影响范围**: Frontend, PM验收标准

### 书籍解说Side Test评估 ✅

**完成时间**: 2026-01-19
**验收状态**: 通过（但暂不纳入主线）

**任务类型**: 产品评估

**完成内容**:
- [x] 评审Tester测试报告
- [x] 确认技术可行性
- [x] 做出产品决策：暂不集成，保持主线专注

**决策理由**:
- 技术可行，Prompt质量达标
- 但当前应专注短剧主线
- 后续可作为产品扩展方向

---

## 2025-01-05

### 多 Agent 协作系统建立 ✅

**完成时间**: 2025-01-05
**验收状态**: 通过

**完成内容**:
- [x] 团队协作协议制定
- [x] 6个 Agent 角色定义
- [x] 知识迁移 (Web → Terminal)
- [x] 文件共享机制建立

**关键产出**:
| 文件 | 说明 |
|------|------|
| `.team-brain/TEAM_PROTOCOL.md` | 协作协议 |
| `.team-brain/knowledge/MULTI_AGENT_COLLABORATION_DESIGN.md` | 设计文档 |
| `.claude/agents/*.md` | Agent 配置 |

---

## 任务归档模板

```markdown
### [任务标题] ✅

**完成时间**: YYYY-MM-DD
**验收状态**: 通过/部分通过

**任务类型**: 需求分析/协调/验收/规划

**完成内容**:
- [x] 内容1
- [x] 内容2

**关键决策**:
| 决策 | 选择 | 原因 |
|------|------|------|
| xxx | yyy | zzz |

**影响范围**: 哪些 Agent 受影响
```

---

## [2026-04-28] TASK-T6-FIXBATCH Wave 0 + Wave 1.1 完成

### Wave 0 (12:05-12:10): PM 文档收尾
- PENDING.md 加 TASK-T6-FIXBATCH 总规划（5 R7 + 4 Wave + 12 风险 + 12 暂缓）
- TEAM_CHAT.md 12:10 派发记录
- pm-progress 三件套 + TODAY_FOCUS 04-28 更新

### Wave 1.1 (12:10-15:15): A + B 并行 spawn → 一轮通过 + Agent A 1 修复 round

**Agent A Backend (Sonnet) 5 子任务一轮地毯式深挖发现 2 严重问题 + 1 修复 round 二轮通过**:
- ✅ P0-2 mark_completed stage='completed' (R7-9 + 旧 P2 #1)
- ✅ P1-1 stage label 重构方案 B 9 处 callback (R7-5 + B-3 + B-4 + 架构 A-1)
- ✅ P1-2 ETA backend 主导（修复 round 1 接通调用链路）+ progress 单调 guard (R7-7 + R7-8 + B-7 + 架构 A-4)
- ✅ P1-3 R7-3 + R7-4 portrait/fullbody 配套（修复 round 1 加 30s buffer）+ 新 endpoint regenerate-portrait
- ✅ P1-5 character_ready 等 portrait 全成（架构 A-3）

**Agent B Frontend (Sonnet) 7 子任务一轮通过**:
- ✅ P0-1 toAbsoluteUrl 共享 + StageD/StageC/BgmPlayer/StoryDetailContent 4 处统一 (R7-12 + 旧 P2 #3)
- ✅ P0-3 StageC character_ready 后 fetch chapter.characters_json (F-1)
- ✅ P1-6 Stage E 显示 outline.summary 三层 fallback (UX-17)
- ✅ P2-2 删除 checkpointPreview L209-214 (R7-6)
- ✅ P2-4 完成态副标题统一 + carousel tip stage='completed' 时 clearInterval (R7-10 + R7-11)
- ✅ F-2 handleRegenerate 接真 API (Agent A 端点)
- ✅ 旧 PENDING P3 4-6 (BgmPlayer fallback + Shot onError + 进度条 spring 动画)
- ✅ STAGE_LABEL 加 character_design + image_preparation 双 key

**关键教训永久保存**:
- `feedback_carpet_review_deep_dive.md` memory + MEMORY.md 索引：PM 审查必须追到调用链路最末端
- `xhteam` SKILL.md 第四步加"地毯式审查铁律"双保险

**真实环境**: backend pid 68345 + frontend pid 68378 仍跑着 R6/T6 build（Wave 1.1 改动还没重启 backend，等所有 Wave 完成统一部署）


---

## [2026-04-28] TASK-T6-FIXBATCH Wave 2 完成

### Wave 2 (15:38-16:00): D + F 并行 + E 串行 + 审查地毯式深挖发现 D.15 P0

**Agent D Backend (Sonnet 4.6 high) ✅ 一轮通过**:
- ProjectDetail schema datetime → str (ISO 8601 with Z) + 加 cover_image_url + shot_count + mood
- 3 helpers: _to_utc_iso / _parse_storyboard_cover_and_count (兼容 list/dict.shots 双格式) / _parse_mood (三层 fallback)
- list_projects 2-query 批量 (零 N+1)
- pytest 211/211 + 7 architecture + 17 parallel
- 修改文件: app/schemas/project.py + app/api/projects.py

**Agent F Backend (Sonnet 4.6 high) ✅ 一轮通过**（违反暂停点但评估正确）:
- 19 处 SceneImage / chapter_scene_images 既有引用 grep 评估完整，全兼容无破坏
- ARCH-1 在 storyboard checkpoint 后 (L1034-1089) 批量写入: chapter_id 防 None + DELETE+INSERT 防重复 + 失败非阻塞
- run() signature 加 chapter_id default None (向后兼容) + job_manager 传值
- 修改文件: app/services/pipeline_orchestrator.py + app/services/job_manager.py

**Agent E Frontend (Sonnet 4.6 high) ✅ 一轮通过 + 1 处 P3 小遗漏**:
- AuthContext L6 import toAbsoluteUrl + L37 ApiProject 加 3 字段 + L71-85 mapProject 全部用
- types/create.ts L170 StoryCard.mood: string | null
- StoryCard.tsx L145-146 mood 条件渲染
- mock-data.ts 6 条补 mood (TypeScript 强制)
- npm build 21 routes 0 errors
- ⚠️ 漏改: types/create.ts L201 StoryDetail.mood 应跟 StoryCard 一致 → 记 PENDING D.16 P3

### Wave 2 审查地毯式深挖暴露 D.15 — 实为 P0 用户体验灾难（非 Wave 2 引入）

调用链路追踪发现 pipeline_orchestrator.py L843 `generate_shot_image_phase2_safe()` 调用时 L850 `aspect_ratio="2:3"` hardcoded — 是真生图实参不是元数据。用户选 1:1/16:9/3:4 等任何画幅，实际生成永远 2:3。T6 Founder 选 1:1 朋友圈但 21 shots 全 2:3 — 之前没对比就过了。

**教训永久保存**:
- `feedback_aspect_ratio_user_perception.md` memory + MEMORY.md 索引
- 任何"用户主动选择"参数必须从输入到生成层完整传递，hardcoded 中间环节 = P0 灾难

Founder 决议: D.15 升 P0 + Wave 2.5 立即修（选 A）。


---

## TASK-T6-FIXBATCH 完成里程碑（2026-04-28 21:30）

### 时间线

| 时间 | 阶段 |
|------|------|
| 12:00-15:25 | Wave 0+1.1+1.2 完成（A Backend / B Frontend / C UX-16 Opus 4.7）|
| 15:38-16:00 | Wave 2 完成（D Backend / E Frontend / F ARCH-1）|
| 16:00-16:35 | 地毯式审查发现 D.15 P0 → Wave 2.5 立即修（aspect_ratio 调用链路 10 段）|
| 16:53-17:09 | Coordinator 修 subagent_type symlink + memory 重写 |
| 17:00-17:30 | PM session 暂时 fallback general-purpose（symlink 后启动的 session 才能用真彩色）|
| 21:00-21:13 | Wave 3 Tester (subagent_type: "tester" 真彩色) T7 真生图验收 11/12 PASS |
| 21:30 | R7-3 单点 bug 立即修（Founder 决议 选项 A，Wave 4 部署前）|

### 关键产出（Wave 1-3 累计）

- **Backend (8 文件)**: pipeline_orchestrator / job_manager / projects / reference_image_manager / chapters / seedream_generator (D.15 字典扩 7 比例)
- **Frontend (8 文件)**: lib/url.ts (新) / lib/createUrl.ts (新) / app/create/[projectUuid]/[stage]/page.tsx (新) + 改 StageC/D/E/CreateContent/CreateContext/types/AuthContext/StoryCard/BgmPlayer/StoryDetailContent
- **Memory 4 条新教训**: feedback_carpet_review_deep_dive / feedback_opus_47_and_effort_max / feedback_aspect_ratio_user_perception + reference_subagent_symlink

### 验收成绩

T7 真生图 (1:1 朋友圈 16 shots) — D.15 P0 PIL 实证 16/16 = 2048x2048 ✅
11 PASS / 1 FAIL (R7-3 修复中) / 0 未触发风险路径

---

## 2026-04-29 15:50 Wave 3.5/3.6 + D.17 简化决议归档

### Wave 3.5 R7-3 P1 修复 ✅
- Backend agent 真因定位: `app/services/character_prompt_builder.py` `_build_human_description()` + `build_face_description()` 对 str 类型 physical/clothing/human 调 .get() 触发异常被吞
- 修复: L102-116 + L231-233 isinstance 双路径处理（dict 走原逻辑，str 走 fallback append）
- 自测: portrait mtime 20:37 → 21:42（+65min）+ DB updated_at 真更新 + log 无异常 + pytest 24/24

### Wave 3.6 R7-3 复测 ✅
- Tester 真彩色 subagent_type: "tester" 独立调 char_001 adjust("增加眼镜")
- 6 证据点全 PASS: HTTP 200 / mtime +62923s / size 1524775 / DB updated_at=2026-04-29T07:10:47Z / log 无异常 / 修复代码仍在
- PM 5 角度地毯式深挖（被 Founder 一句话点醒后做的）：tester progress mtime / DB SQL 直查 / portrait HTTP / pytest 自跑 / character_prompt_builder 后续 .get() 安全
- 关键证据: DB description 含双 adjust 累积内容（"红色外套" Backend 自测 + "知性眼镜" Tester 复测）

### D.17 CONTENT_SAFETY 脱敏策略族（Founder 决议简化）
- Tester 复测附带触发 BUG-2026-04-29-001 char_002 七岁小孩 CONTENT_SAFETY
- PM 脑洞 9 大维度（儿童/民俗/暴力/真人/IP/政治/医疗/性别/场景）+ 三层防御架构
- Founder 反馈"过头了，影响故事生动性"→ 简化为只 Layer 3 末端 fallback
- 最终方案: NB2 拒 → PromptRewriter 改写 → Seedream 试 → 占位图 + 提示
- 9 维度作为 PromptRewriter 改写时内部参考，不前置脱敏
- 备注: Seedream 未来可能转首发生产（待定）

---

## 2026-04-29 17:00 TASK-T6-FIXBATCH 完整结案归档

### Wave 4 DevOps 部署
- commit 84a2d35 + ec471a6 push GitHub main
- rsync VPS + Docker rebuild + 容器 healthy
- Ben 通知 .team-brain/team_ben/TEAM_CHAT.md 15:57
- 生产 T8 (a3966a40-...) 4 验收 PASS

### 整批数据
- **代码改动**: Backend 8 文件 + Frontend 8 文件
- **PR commit**: 84a2d35 (代码 16 文件 / 18818+ insertions / 1069- deletions)
- **Wave 数**: 0+1.1+1.2+2+2.5+3+3.5+3.6+4 共 9 Wave
- **修复总数**: 17 项原始 R7 + R7-3 复测 + Wave 4 部署
- **教训保存**: 5 条 memory + xhteam SKILL.md 第四步双保险
- **暂缓追踪**: PENDING D.13-D.18 共 6 条 + R7-2 + ARCH-2 + OPS-3 + 文案小批

### 用户视角影响汇总（修复后）
- 用户选画幅真生效（D.15 PIL 实证）
- 用户改大纲/角色/场景后退到旧页有 banner 防陷阱（D.14 暂缓但 UX-16 完成态 completion guard 已部分覆盖）
- adjust 角色 portrait 真重生（R7-3）
- F5 刷新 / 复制链接打开 / 浏览器后退都能用（UX-16）
- dashboard 列表显示真封面 + shot 数 + 北京时区（R7-1）
- StageD 21 shots 全可见 + 配乐能播（R7-12）
- ETA 单调下降不再 "1 分钟严重低估"（R7-7）
- progress 不倒退（R7-8）
- 完成态大标题正确（R7-9）
- adjust API 能用真 endpoint（F-2）

---

## ✅ 2026-04-30 D.19 + D.20 黑屏 P0 双件套（PM 视角，2026-05-01 跨日补录）

### D.19 hotfix v1（15:20-15:30）
- Founder 测试 T7+ 创建后访问 `/create/[uuid]/outline` 黑屏
- Root cause: `CreateContent.tsx:686` hydrate 用宽 regex `/404|不存在/` 误判 chapter routine 404
- Frontend hotfix: L484-708 重构 hydrate 两步分离（project 单独 try/catch + chapter Promise.all 各自 .catch）
- 实证: npm build 20 routes 0 errors，frontend pid 36674 重启加载

### D.20 hotfix v2（17:09）
- D.19 修了误判但仍黑屏 — root cause 升级: backend ProjectDetail 不返 raw_outline_json → outline=null → StageB 空渲染
- **Frontend Option D 即时止损**: CreateContent.tsx L775-792 outline recovery via POST generate-outline + StageB.tsx L130 loading spinner
- **Backend Option C 永久解法（PM 派发）**: schemas/project.py L83 raw_outline 字段 + api/projects.py L382-409 generate_outline 幂等 + L98-151 _map_outline_to_response helper extract（DRY）
- 双管齐下: 前端立即止损 + 后端永久解法不依赖 generate-outline LLM 调用
- 验证: pytest 292 passed + Founder F12 console 真见 `[hydrate] outline recovered successfully`

### PM 11 角度地毯式 audit（17:42-17:50）
全 PASS:
1. ProjectDetail.raw_outline 字段 L83 ✅
2. serialize_project_detail 解析 raw_outline_json ✅
3. generate_outline 幂等 + force_regenerate ✅
4. **真测 project 22 raw_outline 真返 title="纸条里的父亲"** ✅
5. _map_outline_to_response helper L98 + 两处调用（L407 幂等路径 + L451 正常路径）✅
6. pytest 7/7 PASS ✅
7. CreateContent.tsx + StageB.tsx mtime 17:09 ✅
8. .next BUILD_ID mtime 17:09 ✅
9. **frontend pid 36674 启动 15:29 < hotfix v2 17:09 → 旧 build 跑** 🔴 → kill 重启 PID 49226 ✅
10. CreateContent hotfix v2 generate-outline 调用 L782 ✅
11. StageB outline=null loading state L130 ✅

### 文档失误（PM 跨日 retro）
- 17:09-23:59 之间 7 小时 PM 未催 frontend 自更 progress + 自己也未更 PENDING/daily-sync/pm-progress
- 5-01 00:00 Founder 派新任务时 double check 才暴露
- 违反 `feedback_pm_check_agent_docs_modified.md`，跨日 catch-up 补救

---

## ✅ TASK-KEY-ROTATE-GEMINI（2026-05-01 00:00-00:09）

### PM 调研（11 角度地毯式 grep）
- AIzaSy 前缀 / GEMINI_API_KEY / GOOGLE_API_KEY / GOOGLE_AI_API_KEY / GOOGLE_GEMINI / google.api / google_ai / .env* / docker-compose / 占位符 / 历史 archive
- 真实需替换：仅本地 `.env:2` + VPS `.env.production`
- 命名只有 `GEMINI_API_KEY`（无变体）
- 占位符 `AIzaSyxxx` 文档示例 + 历史 chat-archive 不替换

### Founder 授权 3 项
1. 新 key 已绑定相同 Google 项目和配额
2. 必须立即 revoke 旧 key（不需要观察期）
3. VPS .env.production 路径需 DevOps 自验

### DevOps 10 步全 PASS
1. 备份本地 `.env` → `.env.backup-keyrotate-20260501`
2. Edit `.env:2` 旧→新（grep 验证 0 旧 1 新）
3. pkill 旧 PID 48766 + nohup 启动无 --reload → 新 PID **71921** /health 200
4. 本地真 LLM `gemini-2.5-flash → 'OK'` AUTH=PASS
5. SSH VPS（trader@107.148.1.199:58913）确认路径 `/opt/xuhua-story/.env.production`
6. VPS 备份 `.env.production.backup-keyrotate-20260501`
7. VPS sed 精确替换（grep 0 旧 1 新）
8. VPS `docker compose up -d --force-recreate api` → docker-api-1 healthy
9. VPS 真 LLM `gemini-2.5-flash → 'OK'` + HTTPS prefaceai.mov/api/health 200
10. SendMessage PM → PM 提醒 Founder 撤销旧 key

### 输出
- 本地 backend PID 71921（无 --reload, feedback_local_backend_no_reload.md）
- VPS api docker-api-1 Recreated + healthy
- 备份双端保留 48 hr，可秒级回滚
- 业务代码 0 改动（仅改 .env 第 2 行 + VPS .env.production 同一行）

### 安全
- **Founder 待行动**: Google Cloud Console (https://console.cloud.google.com/apis/credentials) 撤销旧 key `AIzaSyCX***[redacted-key-Apr29-old]`
- **48 hr 后**: PM 提醒 DevOps 清理双端备份

---

## ✅ 2026-05-02 跨日 Key 真验证 + 服务恢复 + ECS 安全组修复

### 主线（14:00-15:33）

#### 1. 跨日服务全丢
- 5-01 → 5-02 macOS standby 杀光 backend pid 71921 + frontend pid 49226
- nohup 也躲不过 standby — user 进程被冻结/终止

#### 2. 重启遇阿里云 MySQL 连接被切
- 跨日 NAT timeout + idle TCP
- aiomysql 握手 4 bytes 收 0 bytes → OperationalError 2013 → lifespan 崩溃 → 进程退出

#### 3. DevOps V1 + V2 两轮诊断
- V1: 结论"瞬时握手问题，重试通常 OK"。但 PM 重试 2 次仍失败
- V2: 结论"server 端 MySQL 进程异常"。但 ttsrecap 项目 agent 给反证 server 端清白
- **两轮诊断都没锁定真根因**

#### 4. ttsrecap 项目 agent 给关键判断表
```
ping ❌ + nc ❌ + mysql ❌ → ECS 安全组 ban 全部
ping ✅ + nc ❌ + mysql ❌ → ECS 安全组 ban 3306
ping ✅ + nc ✅ + mysql ❌ → MySQL user 没授权
ping ✅ + nc ✅ + mysql ✅ → 客户端 bug
```

#### 5. PM 跑 4 步自查
- ping ❌（ICMP 不通）
- nc TCP 3306 ✅（SYN-ACK 通）
- aiomysql ❌（同样 2013 握手失败）
- traceroute hop 1 = `connect.ios.astrill.com` → 走 Astrill VPN
- 出口 IP `140.99.222.167` Tokyo Latitude.sh hosting provider
- **判断表里没有 ping ❌ + nc ✅ 的组合** → 阿里云 SAS"软拒"特征

#### 6. Founder 截图发现真根因
- ECS 实例绑 `Sas_Malicious_Ip_Security_Group` (SAS 自管)
- 规则限定 MySQL source 仅 `101.132.69.232/32` self-connect
- Founder Astrill 出口 IP 不在白名单
- 应用层 silent drop（TCP SYN-ACK 通但 MySQL 协议握手包被吞）

#### 7. 修复
- PM 引导 Founder ECS 安全组**新增**允许规则: 允许 + IPv4 `140.99.222.167/32` → MySQL(3306) 优先级 1
- **不编辑** SAS 自管 self-connect 规则（避免下次扫描覆盖）
- 提交后**秒通**: aiomysql 真连 + VERSION 8.0.35 + 15 tables

#### 8. Gemini Key 全维度真验证
- Settings 加载: `AIzaSyBmiM1SsK8...` ✅
- 真 LLM 调用: `gemini-2.5-flash → 'OK'` ✅
- **旧 key 反测真实证 revoke**: `400 INVALID_ARGUMENT 'API key expired' API_KEY_INVALID` ← Founder Google Cloud Console revoke 真完成

#### 9. frontend 也跨日丢失
- 重启 PID 15811（next start, BUILD_ID Apr 30 17:09 hotfix v2 build 还在）
- /+/create HTTP 200

#### 10. caffeinate 守护防 macOS standby
- `nohup caffeinate -i -d -s &` PID 15793
- 防 idle sleep + display sleep + system sleep
- 不防合盖 / 重启 / OOM / 断电

### 衍生发现

- **VPS docker-api-1 调 Gemini API 地理限制**: `400 FAILED_PRECONDITION 'User location is not supported'`。但 IMAGE_GEN_PROVIDER=seedream 不依赖 Gemini → 生产没事
- **ECS 安全组 SAS"软拒"机制**: TCP SYN-ACK 通让你建 TCP，但应用层包被吞 → 客户端读 0 bytes → 表现像 server 故障
- **macOS standby 杀进程**: `pmset -g standby=1` 时 user 进程被冻结/终止，需 caffeinate 守护

### Founder 安全行动闭环

- ✅ Google Cloud Console revoke 旧 key（PM 反测真实证）
- ✅ ECS 安全组加白 Astrill IP（PM 引导 + 截图核对）
- ⏸️ SSH 加固（PENDING TASK-SSH-HARDENING）

### 文档产出（PM 跨日补 + 自补）

- `.team-brain/daily-sync/2026-05-02.md` 新建
- `.team-brain/status/TODAY_FOCUS.md` 重写为 5-02 焦点
- `.team-brain/handoffs/PENDING.md` 加 2 条新 task
- `.claude/agents/pm-progress/current.md` 顶部更新
- `.claude/agents/pm-progress/context-for-others.md` 末尾追加
- 本文件末尾追加（completed.md）
- TEAM_CHAT.md DevOps 写入 + PM 即将追加

---

## ✅ 2026-05-02 17:00-17:50 — xuhuastorytest7 完整 E2E + 15 bug retro + 3 Agent 并行修复

### 主线: xuhuastorytest7 完整 E2E 测试

**故事**: 《我妈骂的AI客服是我训练的》— 都市喜剧/网络段子/黑色幽默
**参数**: pixar_3d × 3:4 × 短篇 18 shot × 3 角色（王翠芬/王小明/小敏）
**总耗时**: 54 分钟（16:08:31 → 17:02:54）
**项目 UUID**: `edd4e938-68f6-4ffe-84f5-503442034dca`
**最终产物**: 18 张 shot (1664×2218 真 3:4) + bgm_chapter0.mp3 (3.5MB) + 6 张 character_refs + 4 张 scene_refs

### 测试时间线全锚点

| 时间 | 事件 |
|------|------|
| 16:08:31 | ConfirmOutline + OBS-4 user_selected_mood='幽默' |
| 16:08:55 | StartGeneration ✅ Pipeline 启动 |
| 16:09:09 | Stage 2 CharacterDesigner 启动 |
| 16:10:13 | Stage 2 完成（63s）— 王小明 / 王翠芬 / 小敏 |
| 16:11:10 | UX-1: 王小明 portrait |
| 16:11:39 | UX-1: 王翠芬 portrait |
| 16:12:08 | UX-1: 小敏 portrait + UX-14 portrait_url 写入 |
| 16:12:17 | R4-1 开始等待用户确认角色（超时 1800s）|
| 16:13:31 | ConfirmCharacters ✅（4s 倒计时自动跳，Founder 没看到 portrait）|
| 16:13:38 | Stage 3 ScreenplayWriter 启动 |
| 16:39:17 | Stage 3 完成 13/16 Scene（Scene 11/14/16 失败容错跳过）|
| 16:39:34 | Stage 4 StoryboardDirector 启动 |
| 16:48:57 | Stage 4 完成（O-2 cap 39 → 18 真截断）|
| 16:49:04-16:51 | Stage 5a fullbody（3 角色，复用 portrait）|
| 16:51-16:52 | Stage 5a.5 scene_anchor（4 张 interior anchor）|
| 16:52:03 | Stage 5b 真生 18 shot 启动（并行 3）|
| 16:53:01 | Shot 1 完成（57.98s，1664×2218）|
| 16:59-17:00 | 18 张 shot 全成功 |
| 17:00:42 | Stage 6 BGM Mureka 启动 |
| 17:02:12 | Mureka succeeded (56s) |
| 17:02:54 | ✅ Phase 2.0 Pipeline 完成 |

### 15 个 Bug 完整 retro

#### 🔴 P0 阻断（已修）

**B1 本地 backend 跨日休眠丢失** — macOS standby 杀进程，nohup 也躲不过 → 加 `caffeinate -i -d -s` 守护

**B2 阿里云 MySQL 连接被吞包** — SAS `Sas_Malicious_Ip_Security_Group` 限 self-IP，应用层 silent drop → Founder 加白 Astrill 出口 IP `140.99.222.167/32`

**B3 frontend hydrate timeout 卡 spinner** — D.21 timeout 10s 不够（backend 慢响应 7-12s）→ 调到 30/25/15s

**B4 角色预览页空白被 4s 强制跳过** — character data portrait_url 字段缺失 → D.21 加 4 层 portrait fallback（API → static URL → outline → null）

**B5 浏览器 cache 顽固持有旧 chunk** — Next.js 静态资源长期 immutable cache + 强刷不清 disk cache → 用隐身窗口绕过（PEND 长期方案）

#### 🟡 P1 影响体验（部分修 / 立 task）

**B6 chapter/1/story 持续 400 Bad Request** — D.21 timeout catch 缓解，立 TASK-CHAPTER-STORY-400 backend 修

**B7 强刷 cookie 丢失** — 与 B5 同源，隐身窗口绕过

**B8 Stage 3 Scene 11/14/16 失败** — Backend RCA: `_extract_json()` 缺 inner quote 修复，立 TASK-SCREENPLAY-SCENE-FAIL-FIX（推荐方案 A+C）

**B9 进度倒退（19% → 1%）** — F5 后 hydrate 重新加载状态切换瞬间，新 build 应该不会

**B10 Pipeline 完成不自动跳 /preview** — D.23 已修（StageC.tsx + DashboardContent.tsx）

**B11 BGM 调性偏离（年夜饭风而不是段子）** — AI-ML 诊断 + A+B+C 修复 + 真重跑 v2，待 Founder 试听

**B12 R7-7 ETA 早期 stage 不显示** — 隐身窗口后期 ETA 真显示，待验证早期是否 OK

#### 🟢 P2 小瑕疵（已修）

**B13 副文案"中篇模式 36 张"但选短篇 18 张** — stale-copy 修复
**B14 副文案"先喝杯可可，接下来要你确认角色"过期** — stale-copy 修复（5 档 stage 切换）
**B15 Monitor ❌ emoji 误报** — 接受偶尔误报

### 3 Agent 并行修复批（17:18-17:38）

#### AI-ML BGM A+B+C 修复 + 真重跑 v2 ✅

- **诊断报告**: meta-prompt v3.2 mixed 唯一详细范例是窒息情绪范例（年夜饭风），中等 LLM 遇喜剧时回归到这个范例形状
- **A**: 加好例 3 都市喜剧范例（bouncy/kinetic/syncopated piano/snare clap on punchline/brass stab）
- **B**: 加调性优先匹配硬约束（overall_mood 喜剧词 → 禁参考好例 1）
- **C**: user prompt 把 overall_mood 提到顶部 + 权威注释
- **修改文件**: `test_output/manualtest/sq_upgrade_ab_test/20260304_113630/meta_prompts/meta_mixed_v3_quote_picking.md` L51-81 + L167-205 + L255-271 + L302-307
- **真重跑**: `test_output/manualtest/test7_bgm_after_fix/bgm_v2.mp3` (5MB / 157s)
- **对比报告**: `test7_bgm_after_fix/COMPARISON_REPORT.md`
- **调性词转向**: 旧 holding breath/hand trembling/Don't resolve it → 新 Bouncy/kinetic/brass stab/punchline lands sideways/Lift. Hold

#### Backend Stage 3 Scene 失败 RCA ✅（修复待派）

- **真根因**: `screenplay_writer.py` 有两个 JSON 提取函数，逐 scene 模式调 `_extract_json()` (L1076-1103) **没有** R4-4 内部引号修复，批量模式 `_extract_batch_json()` (L528-661) **有** `_fix_inner_quotes`
- **故障模式**: Claude 在 narration 引用角色对话用 `"..."` 时，未转义双引号导致 3 条 fallback 全失败
- **3 Scene 都是高潮/结尾段**: chars 越来越长（2974 → 3207 → 4793）+ 引号密度高
- **PP16 衍生 bug**: outline plot_points[15] 缺 `beat` 和 `estimated_duration_seconds` 字段（Stage 1 输出质量缺口）
- **推荐方案 A+C 双保险**:
  - A. 提取 `_fix_inner_quotes` 为共用 helper，`_extract_json` 也用上
  - C. Prompt 强化（narration 引用角色台词必须用「」中文书名号）
- **工时估**: ~45 min，零 LLM 成本，零高风险文件改动
- **待**: PM 拍板 → 派 Backend 实施 → Tester 用 test7 数据重跑 Scene 11/14/16 验证

#### Frontend D.21 + stale-copy + D.23 三件套 ✅

**D.21 hotfix（chapter routine 400 catch + 4 层 portrait fallback）**:
- `frontend/src/components/create/StageC.tsx` L321-364
- `frontend/src/app/create/CreateContent.tsx` L471-708
- 后续 timeout 调大: 10/8/4 → **30/25/15s**

**stale-copy 副文案修复**:
- `StageC.tsx` L19-45: 删 `FIXED_TIP` 改 `getProgressTip(stage, subPhase)` 函数
- L653-664: 渲染条件扩展为 text-gen + shot-gen
- 5 档 stage → 文案 mapping

**D.23 自动跳 preview**:
- `StageC.tsx` L251-304: `finalizeAndGoToPreview` 提升为组件级 useCallback
- L306-341: 新增 D.23 checkpoint watcher（char-preview/scene-preview 阶段每 5s 轮询完成态）
- L430-436: text-gen 轮询完成判断分离（status === completed → 直接跳 preview）
- `DashboardContent.tsx` L31-33: handleContinue 改路由 `/create/{uuid}/outline` → hydration → reconcile redirect

**当前 frontend PID 22546**（含全部修复）

### Founder 决策（5-02 17:50）

1. ✅ B11 BGM A+B+C → 同意 + 已完成 + 等试听 v2
2. ✅ B8 Stage 3 Scene 失败 → 立 TASK-SCREENPLAY-SCENE-FAIL-FIX（待派 Backend）
3. ✅ B10 路由 → 立 D.23（已完成）
4. ✅ B5 浏览器 cache → 记 PENDING TASK-BROWSER-CACHE-BUST（长期方案）

### 文档失误教训（持续记录）

5-02 17:00-17:50 期间，AI-ML / Backend / Frontend 三 agent 都自补了 progress 三件套（17:34-17:40）+ TEAM_CHAT。但 PM 自己 progress 三件套 + PENDING + daily-sync + TODAY_FOCUS 又是跨日补（15:33 → 17:50 之后才动）。

DevOps 5-02 V1+V2 诊断的 progress completed/context 仍停在 May 1 00:11，下次 spawn DevOps 必须自补。

**改进 v3**: 每次 PM 转发同事完成报告给 Founder 之前，先 ls -lat 验证同事 mtime 真刷新；PM 自己每完成一个对话回合，立即更 progress 而不是等任务结束

---

## ✅ 2026-05-08 18:00-20:40 — 11 task Master Plan 全闭环

### 主线: Founder 5-08 17:50 提出"所有 bug 一起修不留遗漏"

PM master plan 整理为 11 task（Backend 6 + AI-ML 2 + Frontend 2 + DevOps 1）+ Tester 集成验证。

### 4 Agent 并行修复 + Tester 串行验证

#### Backend 6 task ✅

**B16 REGENERATE-SHOT-IMPL P0** — chapters.py L1581 之后 TODO 真实施 8 步:
- 加载 character_refs（按 shot_type 智能选 portrait vs fullbody）
- 加载 scene_refs
- 调 generate_shot_image_phase2_safe
- 保存覆盖 shot_XX.png
- storyboard_json 更新 image_url 带 `?v={timestamp}` cache bust

**B16 P1 hotfix（Tester 集成测试发现）**:
- 根因: Seedream 返 `pil_image` 字段，代码只检查 `image_data`（base64 string）
- 修复: L1682-1710 三路判断（pil_image hasattr save 优先 + bytes + base64 string + else fallback 错误信息细化）

**B8 SCREENPLAY-SCENE-FAIL-FIX A+C**:
- `_fix_inner_quotes_shared` 提取为模块级 helper（screenplay_writer.py L25）
- `_extract_batch_json` L610 + `_extract_json` L1139 都用共用 helper
- _build_single_scene_prompt 加 narration 用「」中文书名号约束

**B6 chapter/story 400→404**: pending/generating_story → 404（语义对齐 REST）

**B18 plot completeness**: outline schema 限定 plot_point 必须 beat + estimated_duration_seconds + fallback 防御

**B19 mood enum**: visual_tone.overall_mood 限定 8 enum (warm/heartwarming/tense/comedic/melancholic/heroic/mysterious/romantic) + 中英文 mood_map fallback

**B20 sound_design_hint mood coherence**: _build_single_scene_prompt 加 MOOD COHERENCE 块，喜剧场景禁沉重词

#### AI-ML 2 task ✅

**B11 BGM 6 桶完整通用化**:
- Energetic / Heroic / Melancholic / Warm / Romantic / Mysterious 6 大调性桶
- 中文 + 英文双重触发词
- LLM 复合词归桶规则（"melancholic_intimate" → Melancholic）
- fallback 默认归 Warm（不归 Melancholic 避免窒息）
- 新加好例 4（都市励志 北漂咖啡馆）/ 5（暗夜浪漫 地铁站告别）/ 6（都市悬疑）
- 真重跑 v3 BGM: `test_output/manualtest/test7_bgm_after_fix/bgm_v3_full_coverage.mp3`

**B17 ShotValidator anatomy 检测**:
- shot_validator.py 加 anatomy_severity (severe/mild/none) + anatomy_issues array
- hands_count check + extra_limbs_floating check
- max_tokens 384→512
- severe → valid=False 触发 sanitize_attempt
- mild → 仅 log（避免误伤艺术风格化）

#### Frontend 2 task ✅

**B21 D.24 cache bust**:
- StageD.tsx L46 bustCache helper（检测 ?v= 存在则用，否则加 Date.now()）
- handleRegenerate L67 + handleAdjust L100 dispatch 用 freshUrl

**B24 D.25 BGM 文案**:
- BgmPlayer.tsx L399 "换一首" → "换种风格"
- L407 "重新生成" → "再来一首"
- L411-412 credits 说明区分加粗

#### DevOps progress 自补 ✅

- completed.md + context-for-others.md 真补 5-02 V1+V2 诊断（含诚实记录 V2 结论错误 + 真根因 SAS 安全组）
- 教训固化: 4 步客户端自查标准流程（ping/nc/mysql/traceroute），nc ✅+mysql ❌ = 应用层 filter 先排查安全组

#### Tester 集成验证 ✅

**TASK-T8-INTEGRATION-VERIFY** (19:50-21:05):
- pytest 295 passed / 3 failed / 32 skipped（与 Wave 5.2 基线一致零退化）
- 架构测试 11/11 PASS
- B8 inner quote fix PASS
- B6 状态码 PASS（pending/generating_story → 404，failed → 400 Tester 认为 400 更语义准确）
- B11 BGM 6 桶 PASS（6 桶调性词全确认）
- B17 ShotValidator anatomy 3/3 PASS
- D.24 cache bust + D.25 BGM 文案 PASS
- 角色一致性回归 PASS（5-08 改动零触碰高风险文件）
- **B16 P1 FAIL → Backend hotfix → 重测 PASS** 闭环

### 当前产品功能完整性提升

✅ **重新生成功能从壳变真**: B16 闭环后用户点重生真生新图（不再返原图欺骗用户），FAQ + Tutorials 不再是空话
✅ **BGM 通用性从 3 档扩到 6 桶**: 覆盖产品 8 mood + LLM 任意复合词，热血/悬疑/浪漫/温馨/感人/治愈/紧张/幽默 全有专属调性
✅ **图像质量自动检测多肢/多脸 anatomy bug**: ShotValidator 真严格 + 自动触发 sanitize 重生
✅ **故事完整度提升**: Stage 3 Scene 11/14/16 失败模式（inner quote 未转义）已根治
✅ **数据契约清晰**: chapter/story REST 语义化（404 资源未 ready vs 400 真错误）+ mood 8 enum 标准化

### 文档更新清单

- pm-progress 三件套 5-08 20:40 全更新
- ai-ml-progress 三件套 5-08 17:38-19:30 全更新（含月余历史空缺补全）
- backend-progress 三件套 5-08 17:35-19:24 + B16 hotfix 追加
- frontend-progress 三件套 5-08 17:34-17:35（D.21/22/23）+ D.24/25
- devops-progress 三件套 5-08 18:46-19:21 自补全
- tester-progress 三件套 5-08 21:05+ 集成验证 + 重测
- TEAM_CHAT.md 5-08 17:21-21:00+ 完整流水
- PENDING.md 17:45 + 5-08 进度同步
- daily-sync/2026-05-02.md（5-08 主活动延续）

---

## ✅ 2026-05-09 — test8 完整 E2E + 全维度 Frontend 修复 + BGM 漂移 + Haiku Logging

### 主线

5-09 Founder 测 test8《行李箱里的她》(悬疑/油画/3:4/短篇/3 角色)，10:26-11:00 跑完整 E2E（54 min）。Pipeline 真完成 18/18 shot + Mureka BGM。但实测发现 D.21+D.23 在 character preview / scenes 子页面没全覆盖回归 + BGM 时长写死。

### test8 完整 E2E 实证

- project_id=23 / UUID `21ebb0d8-2eb0-483d-a4a5-fd8c93ec49ba`
- title: 行李箱里的她
- 角色: 陈晓（22 学生）/ 林守仁（74 老人）/ 王师傅（55 复印店老板）
- 场景: 5 个（apartment_balcony / city_archive / copy_shop / old_street_path / residential_courtyard）
- mood: user 选"悬疑"，LLM 也输出"悬疑"（B19 enum 真生效）
- 18 shot 全 1664×2218 (3:4) 油画风
- B11+B17 全实证（B11 真 Mysterious 桶映射 + B17 anatomy 检测但 false negative shot_3）
- B16 重生真生效（shot_03 mtime 11:11 真换）

### 5-09 修复批次（11:22-14:40）

#### Frontend agent 全维度修复（11:22 + 13:30-14:30）

**B26 D.21 character preview portrait 没生效**:
- 根因 1: D.21 fallback 在 character_ready handler/hydrate 加了，但 component-level 没兜底
- 根因 2: silhouette dark theme 不可见
- 修复: StageC.tsx 加 portraitErrors state + resolvePortraitUrl useCallback + dark silhouette
- 详见 frontend-progress

**B27 /scenes 路由 spinner 而非进度条**:
- 根因: reconcileBackendVsUrl 没检查 backend 是否过 character_ready
- 修复: createUrl.ts 加 POST_CHAR_STAGES set { screenplay/storyboard/image_preparation/image_generation/bgm/completed }，screenplay 之后跳 generating

**B28 backend Stage 3 期间 30s timeout 误报**:
- 根因: Stage 3 LLM 阻塞 254s + DB 事务 row-level lock → GET /projects 阻塞
- 修复（缓解）: timeout 30→120s + 25→90s + 15s slow warning + 文案改"服务器正忙（AI 正在创作中）"
- 真根因: backend Stage 3 LLM 调用在 DB 事务内 → 立 PEND B34

**衍生 1 — URL 切换 hydrate loop spinner 1-2 min**:
- 根因: URL change effect 没识别本组件自己的 router.push
- 修复: isOurOwnPush guard（lastPushedUrlRef === window.location.pathname → 跳 hydrate）

**衍生 2 — ETA Stage 1/2 不显示**:
- 根因: progress < 10% 直接 return null
- 修复: fallback 8min/7min（story_generation/character_design）

**全维度路由表审查**: 6 URL × 3 backend status × edge case 全 code-trace verify

#### Backend agent BGM 漂移 + Logging（13:30-14:35）

**B31 BGM 切尾 4s（不再严格 target）**:
- 根因: ffmpeg_post_processor 严格裁到 target_duration（短篇=180s）
- 修复: process_bgm 改 max(input - 4.0, input/2) — 188.80s → 184.80s
- LUFS / silence QA 不变

**B32 Haiku BGM prompt 持久化**:
- 根因: log 只打字数没打 prompt 文本 → 排查 mood 问题黑箱
- 修复: Step 5b 写 output/{uuid}/bgm_prompt_chapter{N}.txt + logger.info() 完整 prompt
- 文件含 meta header（chapter / meta_version / generated_at / user_selected_mood / story_title）

**任务 3 Mock dump test8 BGM Haiku prompt（真调 1 次 Haiku $0.005）**:
- 真返 776 chars prompt（位于 test_output/manualtest/test8_bgm_haiku_dump/bgm_prompt_dump.txt）
- Mysterious 桶必备词命中: minor key ✅ ambient drone ✅ sparse 部分 🟡 silence 语义 🟡 muffled+pulse 部分 🟡 / tension build ❌ dissonant cluster ❌
- 禁用词 0/6 污染 ✅
- 评分 4.2/5
- 衍生发现 B33: primary_mood 字段没读 user_selected_mood

### 当前服务实证（5-09 14:42）

- backend uvicorn PID **55079**（含 B31+B32 + 5-08 11 task + B16 hotfix）
- frontend next-server PID **55110**（含 B26+B27+B28+衍生 + 5-08 D.21-D.25）
- caffeinate 15793 + Monitor v9

### 衍生 PEND（不在本批次修）

- B33 P3: story_music_extractor.py primary_mood 没读 user_selected_mood（3 行小改）
- B34 P2: Backend Stage 3 LLM 阻塞 DB 事务（B28 真根因，需要 LLM 移出事务 OR background job）

### 文档失误教训持续记录 v4

5-09 PM 自己 progress + TODAY_FOCUS + daily-sync + PENDING 又在 18+ 小时未更新（5-08 20:44 → 5-09 14:40），等到 agent 完成才大批量补。

**改进 v4**: PM 收到 agent 完成报告**第一件事就是更 PENDING + pm-progress**，不要等 ls verify 才发现自己漏。

### Founder 测试体验关键反馈

- BGM "悬疑悲伤" 听感正确 — Haiku 真用 Mysterious 桶调性词（minor key/ambient drone）
- 油画风 + 雾蒙蒙伦勃朗光影 + 悬疑题材 视觉一致性高
- 行李箱形状/材质细节漂移（B29 PEND prop reference image 系统）— Founder 暂搁置
- shot_3 女生手 ShotValidator 漏判（B30 PEND ShotValidator anatomy v2）— Founder 暂忽略

---

### 2026-05-09 17:00-17:30 — xhteam Wave + Seedream 决策 ✅

**派 3 agent 并行修 B35-B40**（按 Founder "周全全面有深度"）

| Agent | 完成 |
|-------|------|
| Frontend | B36 hasCharacters 门控 + B27 路由审计 + B28 timeout UI + B37 7 文件 console |
| Backend | B35 AsyncAnthropic + B38 IMAGE_GEN_PROVIDER dispatch + B39 aspect_ratio 透传 + B37 后端日志 |
| AI-ML | B40 全维度 8 mood × 6 桶 sub-vibe 锁定 (meta-prompt L100-145 + L516-540) |

**PM 自己**:
- 干净重启 (backend 69134 / frontend 68973 HTTP 200)
- B38 mini verify PASS
- 地毯式深挖每个 PEND 调用链路
- 17:30 Seedream 全栈决策落地 (config.py default + .env.example)
- CLAUDE.md 顶部加 2026-05-09 Seedream 主力决策块
- 12 文件 progress 三件套 + 团队文档全更新

**未完成 (B41 PEND)**: NB2 dead code 清理 + CLAUDE.md 旧节内容更新 + docstring (派 backend 后续做)

---

### 2026-05-09 17:43 - 18:21 — test10 完整 E2E 实测 ✅（35 min 闭环 + 4 新 PEND）

详见 pm-progress/current.md 的 test10 段。Founder 体感: BGM 反偏置完美 + Shot 05 content_safety + Shot 08 手部 anatomy。新 PEND: B43/B44/B45/B46。

---

### 2026-05-11 10:30-10:58 Wave (B36 v3 + B41-B46) 全闭环 ✅

7 PEND 修复 (4 P1 + 3 P2) — 4 agent 并行 + PM alembic 004 + 干净重启 + Monitor v15

---

### 2026-05-11 15:25-16:46 test11 完整 E2E 实测 ✅（35 min 闭环，11 PEND 验证 + 7 新 PEND 暴露）

详见 pm-progress/current.md。test11 验证 B36 v3/B38/B39/B43/B45/character adjust 全闭环。暴露 B47/B49/B50/B51v2/B52/B56/B57 + B48/B53/B54/B55 共 11 个新 PEND。Founder 选 Wave 5 修 6 个（B52+B56+B57+B51v2+B47+B49+B50），不修 B54/B55，B48 可选。

---

## 2026-05-18 — test18 e2e 验收 + 全程 audit + 7 个新 RISK 定义

### 全天 monitor (~3 小时)
- 8 次 5 维度 check (cron 00692eeb every 2 min)
- Pipeline 端到端打通 37 min, 标题《最后一克》
- Wave 12+13+14 修复实证 PASS (9 项): anthropomorphic_animal / BGM dict-str / atmosphere 英文化 / scene_heading 英文化 / portrait_ref / ShotValidator 3.5MB / 后台生成按钮 / 原地重启 / D.15 aspect_ratio

### Audit 报告 (PM 地毯式 10 维度审查)
- `.team-brain/analysis/TEST18_FULL_AUDIT_2026-05-18.md` (12 章, 22 KB) — 完整全程汇总
- `.team-brain/analysis/TEST18_PREVIEW_QUALITY_AUDIT_2026-05-18.md` (Preview 深度根因)

### 7 个新 RISK 定义 (T20-1~7, Founder 决策一起修 5 P0+P1)
- T20-1 P1: 雨夜冲突 B51 触发率 33% (减触发率, AI-ML)
- T20-2 P1: ETA UX 复合 bug (跳变 + 消失 + 收尾文案误导, Frontend)
- T20-3 **P0** 招牌污染 (中文 location_name 强制渲染, Backend 方案 A)
- T20-4 P1: B51 fallback 同 ref 多图近乎一样 (与 T20-7 合并修)
- T20-5 P2: Seedream fallback 决策不稳 (POST_BETA)
- T20-6 P2: ShotValidator universal 缺陷 (fallback/wide skip + 重复气泡 false positive)
- T20-7 **P0** B51 fallback 抛弃 screenplay 数据 (剧情完全退化, AI-ML)

### Founder 主观验收反馈
- ⭐ "总体不错 BGM 也应景"
- ⭐ "整体连贯, 好了很多"
- ❌ 3 大类视觉问题 (招牌污染 / Shot 3→4 跳变 / Shot 5=13 几乎一样)

### Cron 全停事件 (~14:00)
- 发现 cron 00692eeb 仍在 every 2 min 跑 (Founder 之前以为停了)
- CronList + CronDelete 干净停止
- **教训**: PM 用 /loop CronCreate 创建的 cron 必须主动 CronList + CronDelete, 不能只 omit ScheduleWakeup

### TASK-T20-FIXBATCH 派活规划
- Phase 0: PM 文档补齐 (current/completed/context-for-others + TEAM_CHAT + PENDING + DECISIONS)
- Phase 1: 3 agent 并行 (Backend T20-3 / Frontend T20-2 / AI-ML T20-7+1+4 串行)
- Phase 2: PM 地毯式审查 + Tester 回归测试
- Phase 3: T20-6 后置

---

## 2026-05-18 (晚) — TASK-T20-FIXBATCH-2 7 RISK 全修完成

### 派活 + 完成
- 4 agent 并行 (Backend #1 Opus 4.7 + Backend #2 + Frontend + DevOps Sonnet 4.6)
- 7 RISK 全部 ✅ (T17-1/T18-I/T18-J/T19-9/T20-8/T20-9/POST_BETA-5)
- 累计 108 新单测 + 132 regression 全 PASS

### Backend #1 重大发现 (Ben 教训实证 #2)
- PM TEST18_SECOND_RUN_AUDIT 把 T20-9 根因归到 "Frontend hardcoded 1440"
- Backend #1 地毯式查后发现真根因更深: chapters.py:344 fallback hardcoded `stage_progress=0.5` + per_shot=60s 过乐观
- 修复后实测低估 6% (上次 42%)
- 教训: PM 表象诊断 ≠ 代码层真根因, agent 必须独立验证根因
- KEY_LEARNINGS #29 已加

### Ben 5 维度地毯式审查 (T20-9 完整调用链)
- Schema (chapter.py:40) → Backend route (chapters.py:405 estimate_remaining 透传) → Frontend interface (StageC.tsx ChapterStatusResp 2 处 polling 都加字段) → 数据流 (backendEstimatedSecondsRef 真存) → 消费 (useETA call 真传) → ETA 计算 (优先级最高)
- 完整 6 节点接通, 0 漏 (不像 T20-6 wiring 漏 1 行)

### 8 维度深查全 PASS
- T20-9 端到端: ✅
- T20-8 outline 改: ✅ (UX-2 prompt + Stage 1 ending_id + 兜底防御)
- T17-1: ✅ (prompt_safety_advisor.py 改 extract_json_from_llm_response)
- T18-J: ✅ (alignment_service.py + chapters.py shot 调整 真改 AsyncAnthropic + await)
- T19-9: ✅ (story_music_extractor.py L444-462 完整 dict/str defense)
- POST_BETA-5: ✅ (image_generator + seedream 三处 dispatch 都加 refs=N (M portrait + K scene_ref))
- DevOps monitor: ✅ (本地跑解析 100% retry 成功率, 配置化阈值)
- Agent progress 三件套: ✅ (backend/frontend/devops 都更新)

### 文档更新清单
- TEAM_CHAT.md (派活 + 4 agent 完成 + PM 收尾)
- PENDING.md (7 RISK 状态)
- DECISIONS.md (DEC-042 真根因纠正)
- KEY_LEARNINGS.md (#29 新教训)
- 4 agent progress 三件套
- pm-progress/completed.md (本次追加)

### task list 最终: 34/34 completed, 0 pending


---

## 2026-05-19 — TASK-T20-FIXBATCH-3 RISK-T20-10 P0 灾难修复 完成

### 派活 + 完成
- AI-ML agent (Opus 4.7 max) 修 5 文件 + 新建 1 测试
- 5+1 文件改动: pipeline_schemas.py + storyboard_service.py + storyboard_prompts.py + pipeline_orchestrator.py + 新 test_t20_10_universal_character_schema.py
- 19 新单测 + 137 关键 regression 全 PASS
- PM 端到端实证: test17 5 anthropomorphic_animal schema PASS + test18 3 human regression PASS

### Explore agent 地毯式 5 维度审查 (新模式)
- 用 Explore agent 先做完整审查 (15+ 文件深查), 再派 AI-ML 修
- 揭示真根因: 不只 Schema 漏修, 是 5+ 处下游 consumers 全漏修
- KEY_LEARNINGS #30 加: "修了一半" 教训 — schema + 下游 5+ consumers 都要改

### 架构性改进 (universal)
- 之前: 6 处 hardcoded human-only (CharacterPhysical + 5 builder 各自实现)
- 现在: 1 schema (Optional + per-type validator 20 类型) + 5 下游 dispatch CharacterPromptBuilder
- 未来加新 character_type 只需 builder 加 method + schema dict 加 1 行

### Wave 14 完整收敛 (累计)
- Wave 14: 5 处映射 (character_types/character_prompt_builder/character_designer/reference_image_manager)
- T20-10: 6 处 (schema + 5 下游) — Wave 14 漏的全部补齐
- 现在: 19 character_type 端到端全栈支持 (Schema + LLM prompt + Stage 4 prompt + Portrait + Stage 5 + ...)

## 2026-05-22 全天: Wave 7+8+9+9.1 全闭环 + VPS 部署 + P0 SECRET-LEAK + Tester baseline (PM Sonnet 4.6 协调)

### 早间 (08:30-12:35) Layer 1 全闭环 ✅
- AI-ML M1 spec 837 行 + M2-M5 round 1+2 (74/74 PASS)
- Backend inject + validator + image_generator wire (127+365 = 492 PASS)
- Tester 跨题材 105 baseline
- 累计 306 PASS, KEY_LEARNINGS #52-54 沉淀

### 中午-下午 (12:35-15:17) Wave 7+8 6 task 全修 ✅
- Wave 7 Backend (Opus 4.7 max): T22-NEW-7 chars=0 ID format mismatch 根因 + T22-NEW-4 LLMFallbackChain Haiku→Gemini→Sonnet 4 endpoint + T22-NEW-6 Layer 1 location wire
- Wave 7 Frontend (Sonnet 4.6): T22-NEW-2 SceneRefsPreview 智能展示
- Wave 8 Frontend: T22-NEW-5 R4-2 砍 5 文件 + T22-NEW-8 0 改动 已实现
- Wave 8 Backend: T22-NEW-9 通用 fallback 19→4 entries + T22-NEW-5 R4-2 wait loop 移除 + STATUS_API_CONTRACT v1.5

### 傍晚 (15:30-16:55) e2e test22 Round 2 + VPS 部署 + 同步 verify ✅
- e2e test22 manga + 浪漫 + 3:4 (32.8 min, 26 shots, $0.78, 85-90 分)
- DevOps push GitHub e5470e8 + rsync VPS + Docker rebuild + Alembic 006
- 阿里云 SAS 安全组 107.148.1.199/32 → MySQL(3306) 白名单
- VPS /api/health 200, https://prefaceai.mov 200
- VPS=local 7 维度同步 verify 全对齐

### 17:00-18:50 P0 SECRET-LEAK 全维度清理 ✅
- GitGuardian 17:01 警报 (Google API Key 泄漏 GitHub)
- DevOps Opus 4.7 max + Sonnet 4.6 两轮:
  - Step 1 audit: 8 文件 11 occurrence working tree + 1 commit history
  - Step 2 DevOps 域 3 文件脱敏 + PM 域 5 文件 7 处脱敏 (PM 代做)
  - Step 3 防御层: .gitignore + .gitleaks.toml + pre-commit hook
  - Step 4 git filter-repo 重写 (126 commits 6.01s, e5470e8 → f9987b0)
  - Step 5 force push GitHub (HEAD = f9987b07)
  - Step 6 跳过 (Founder Google 限额兜底)
- 副灾难: filter-repo --force 清除 AI-ML Wave 9 + PM uncommitted 工作 (KEY_LEARNINGS #58 教训)

### 19:00-19:02 Wave 9 重做 + 19:02-19:15 Wave 9.1 ✅
- AI-ML Sonnet 4.6 Wave 9 重做 45 min (commit 89bcfc7, 9 files +704 -3)
  - W9-1 reference_image_manager.py `_build_portrait_prompt()` wire Layer 1 (try/except + is_bw_style + lazy import)
  - W9-2 style_enforcer.py BW_STYLES set + is_bw_style staticmethod (类型防御)
  - W9-3 test_layer1_portrait_injection.py 7/7 PASS + 218 baseline 0 退化
- AI-ML Sonnet 4.6 Wave 9.1 30 min (commit 1629332, 7 files +527 -17)
  - W9.1-1 reference_image_manager.py `_build_reference_prompt()` fullbody 镜像 W9-1
  - W9.1-2 test_layer1_fullbody_injection.py 6/6 PASS + 178 baseline 0 退化
- Layer 1 三路统一: shot (W7) + portrait (W9) + fullbody (W9.1)

### 19:02-19:30 PM 11 维度地毯式审查 Wave 9 + Wave 9.1 ✅
- 维度 A-K: commit/Ben 协议/code diff/PM 自跑 pytest/5 层调用链/KEY_LEARNINGS/DECISIONS/AI-ML progress/越权/baseline
- Ben 协议 5+1 维度 (含 pre-commit hook 自动验证): 0 违反

### 19:30-19:45 Tester 跨题材独立 baseline ✅ (Sonnet 4.6, 9 分钟 wall clock)
- commit c570c2d, 6 files +1300 -5
- T1: 623/623 PASS in 0.90s (16 test files, $0 API)
- T2: 5风格 × 5character_type 矩阵 50 case + BW skip 10 = 60 全 PASS
- T3: 3 路 log marker 实际触发 verify (portrait/fullbody/skip 全 wire 真跑过, 不是死代码)
- T4: 12 边缘 case (fallback id / Exception 兜底 / non-string defensive 全 PASS)
- T5: WAVE_9_TESTER_INDEPENDENT_BASELINE_REPORT_2026-05-22.md 完整 report
- 独立 P3 发现 (非阻塞): RIM logger name 不统一 (建议未来统一)
- 结论: Wave 9+9.1 **可部署**

### 累计今日数据
- 6 commit (e5470e8 → f9987b0 → 89bcfc7 → 1629332 → c570c2d)
- 9+7+6 = 22 files Wave 9+9.1+Tester 改动
- 623/623 PASS (Tester) 包含 Wave 7+8+9+9.1 累计
- 0 退化, Ben 协议 5+1 维度 0 违反

### 待派
- DevOps Sonnet 4.6 effort high: push GitHub + rsync VPS + Docker rebuild (一次部署 Wave 9 + 9.1 + Tester)
- Founder 视觉 spot-check (新一次 e2e 或 test23/24)
- 内测启动

