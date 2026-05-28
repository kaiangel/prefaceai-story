# Today's Focus

> **Updated**: 2026-05-28 17:55 (test30 整轮 e2e + 4 处 parity + portrait deep dive + 性能 P0 Plan A++ 代码闭环, 等 DevOps 部署)

## 当前阶段: 代码层完整闭环, Founder 下班, DevOps 部署待安排 (含 scene_ref thumb URL wire P1 followup)

### 5/28 整轮成果

✅ **Pipeline e2e** 3840.2s 跑通《灯笼与萤火》, 20 shot + BGM 全落盘
✅ **Dev/Prod Parity 4 处 P0**: SKIP / ARK / IMAGE_GEN_PROVIDER+PROMPT_FORMAT / Nginx /static/ 全修
✅ **Portrait 重生 Explore very-thorough 5 维度深审**: Adjust + Regenerate 双 endpoint, LLM CFP-3 + Seedream GROUP COMPOSITION
✅ **性能 P0 Plan A++ progressive enhancement**: Backend thumbnail + WebP + Frontend StageD progressive (thumb 2s 秒切 + 后台升清)
✅ **DEC-055 + Deploy SOP 11 维度** 锁定永不再犯
✅ **15 个问题完整深度回溯** (analysis/TEST30_FULL_RETROSPECTIVE_2026-05-28.md, 8000 字)
✅ **4 个 memory + MEMORY.md** 索引

### 待 DevOps 部署 (Founder 下班, 之后做)

1. **B**ackend scene_ref thumb URL wire 补 (~20 min, PENDING 顶部 P1 followup) — 与本批同部署
2. commit 按 scope 分 4-5 组 (Backend / AI-ML / Frontend / 文档 / scene_ref wire 补)
3. rsync app/ + frontend/ 到 VPS
4. VPS docker compose rebuild api + frontend
5. 验证: portrait 重生 refs=1 / shot 三件套 (png+webp+thumb) / 前端 preview 页 thumb 2s 秒切 + 自动升清

### P2 内测后

- CDN 国内化 (等 Ben 讨论)
- WebP fallback PNG 兜底 (96%+ 浏览器覆盖)
- chapter_scene_images.thumbnail_path dead column 处理
- STATUS_API_CONTRACT 加 §X "shot 数据字段" 一节

---
（以下为 5/28 早 历史）

## (历史) 当前阶段: P0-2 修完, 等 Founder 重发新 test30《灯笼与萤火》真生图

### 5/28 凌晨最重要

1. **P0-2 VPS test30 portrait 全失败根治**: Founder VPS 真机 test30 /characters 三角色全失败, Pipeline `generate_images=True` 但 0 portrait。PM 铁律 5 维度核实 (容器代码 + 完整调用链 + 历史证据 + 其他 flag 排查 + Ben 维度), 锁定根因 = `.env.production` 误开 `SKIP_IMAGE_GENERATION=true`。Founder go 后 sed + force-recreate api 修复, 容器 settings=False + /api/health 200 ✅。**待 Founder 重发新 test30 真生图** (e48baa8a 项目废弃: API 重启 in-memory 丢 + portrait 窗口已过)。
2. **PM 盲区透明承认**: test29 后看到 VPS 仅 1 output 目录归因 "其他 35 个 local-origin", 没追 "为什么 36 项目里只 1 个有图" — 那时该挖到 SKIP 模式。下次 dashboard/output 数量背离立即追 "是什么开关让 VPS 不生图"。
3. **Ben 暂不通知** (Founder 决策, 本轮)。SKIP toggle 不涉契约/DB/公网/DB-infra, 纯本机 feature toggle。

### 仍在工作区待 commit+部署 (内测前)

- **#8 BGM 路径B** (story_music_extractor.py 文化识别 universal 信号 + character_type 降软提示)。PM 审查通过 (395 pytest + dry-run), 等 DevOps 下一批一起 push 部署。真听感 Founder e2e。

### 5/27 历史
- ✅ P0 SQLAlchemy 2.0.50 部署 (ping TypeError 120→0) + dev/prod parity (DEC-054 canonical DB 栈)

---
（以下为 5/26 历史）

## (历史) 当前阶段: test29 后 — 非人类通用性专项修复 (待 e2e 视觉验证 + 部署)

### 今日 (5/26) 最重要的三件事

1. **test29《荷塘渡》e2e 跑通, Founder 90 分** — Wave 13 全修复实测生效 (#5e/#6/#4A/#4B/#5-404/B52/ETA/T17/条漫文字/画幅3:4)。全维度回溯 `analysis/TEST29_FULL_RETROSPECTIVE_2026-05-26.md`。
2. **炸出「非人类人类中心假设链」5 缺口 + 当场修复 4 个** — Backend #4(Packet retry) + AI-ML #5/#6/#7(非人类消费层专项, 含补挖的 #5a 锚点层)。PM 地毯式审查 + Ben 维度全过, db_retry 21 + AI-ML 域 499 pytest passed。#8(BGM)内测后。
3. **待最终验收** — #5/#7 视觉真证 (golden 真出金色/鱼草不融合/人类不退化) 需 Founder e2e 复测(test30)。Wave13+test29 全未 commit, 禁 destructive git。

### 待 Founder 决策
e2e 复测(test30) vs 直接 commit+部署 vs 先 commit Wave13。#4 是 DB-infra→部署前知会 Ben。

---

## (历史) Wave 13 内测前 FIXBATCH — 集成关口 (内测启动倒计时)

### 今日产品层面最重要的三件事 (5/25)

1. **Wave 13 集成关口双绿** — PM 第一道审查 ✅ 全绿无 blocker (DEC-052); 等 Tester 第二道 (pytest 30新+vitest 15+回归) → DevOps 第 5 次部署。内测启动前最后一道代码关。
2. **§9.7.4 前后端契约对齐确认** — regenerate-portrait 同步→异步, Backend 202+job_id ⟺ Frontend pollCharacterJob ⟺ 契约逐字段一致 ✅ (Ben 纠验机制核心, 最易断裂处已核对无误)。
3. **clothing 旁路 P1 防崩** — 内测用户选 object/aquatic/plant/insect 等非穿衣 type 角色不再冲垮 pipeline (#5e), 守护通用性生命线。

### Wave 13 各项 PM verdict

| 项 | 负责 | verdict |
|---|---|---|
| #5d MySQL retry middleware | Backend | ✅ 4 重约束代码可证 |
| #6 regenerate-portrait 异步 | Backend | ✅ §9.7.4 三方对齐 |
| #5e clothing 旁路防崩 | Backend | ✅ 崩溃点消除 0 删 fallback |
| #4A 确认流程超时守卫 | Frontend | ✅ |
| #4B 后台按钮 scenesConfirmed | Frontend | ✅ |
| #5 404 真根因 (吃反斜杠) | Frontend | ✅ 源码层根治 |
| #6 reroll 异步轮询 | Frontend | ✅ |
| #9 vitest 基建 | Frontend | ✅ |
| #5b schema 5 type 核实 | AI-ML | ✅ 0 代码改动 |

**下一步**: Tester 双绿 → DevOps commit 3 组 (见 PENDING) + push + VPS 第 5 次部署 (layout.tsx 须 rebuild+硬刷新)。

---

## (历史) 当前阶段: DevOps 第 2 次部署 (内测启动倒计时)

### 今日 (5/22) 全程战果

| 时段 | 内容 | 结果 |
|---|---|---|
| 08:30-12:35 | Layer 1 Identity Anchor Framework v1.0 全闭环 | 306 PASS |
| 12:35-13:57 | e2e test22 Round 1 + 5 P0 audit | chars=0 P0 暴露 |
| 14:25-15:17 | Wave 7+8 6 task 全修 | 786+ PASS |
| 15:30-16:08 | e2e test22 Round 2 (manga + 浪漫 + 3:4) | 85-90 分 |
| 16:08-16:55 | DevOps VPS 部署 + VPS=local 同步 verify | 7 维度对齐 |
| 17:01 | 🚨 GitGuardian P0 警报 | DevOps 派工 |
| 17:05-18:50 | P0 SECRET-LEAK Step 1-5 完成 | HEAD = f9987b0 |
| 18:45-18:50 | 🚨 副灾难: filter-repo 清除 AI-ML 1.5h Wave 9 工作 | AI-ML 重做 |
| 19:00-19:02 | AI-ML Sonnet 4.6 Wave 9 重做 + self-commit | 89bcfc7 (7/7 + 218) |
| 19:02-19:15 | AI-ML Sonnet 4.6 Wave 9.1 fullbody | 1629332 (6/6 + 178) |
| 19:15-19:30 | PM 11 维度审查 Wave 9 + 9.1 (各 Ben 协议 5+1) | ✅ 通过 |
| 19:30-19:45 | Tester 独立 baseline (Sonnet 4.6, 9 min wall clock) | c570c2d (623/623 PASS 0.90s) |
| 19:45+ | DevOps 第 2 次部署待派 | 🟡 即将派 |

## DevOps 部署待派 (5/22 19:45)

| Agent | 任务 | ETA |
|---|---|---|
| DevOps | Sonnet 4.6 effort high: push GitHub (89bcfc7+1629332+c570c2d) + rsync VPS + Docker rebuild api + verify | ~30 min |

## 后续流程

1. DevOps 第 2 次部署完成
2. Founder 视觉 spot-check (e2e test22 第 3 次 / test23 现代悬疑 / test24 古风武侠)
3. 内测启动

## 重要教训今日新增

- **KEY_LEARNINGS #57**: 跨路径 wire 一致性 (shot ✅ portrait ❌ = "半吊子一致") — AI-ML 5/22
- **KEY_LEARNINGS #58**: destructive git 前必须 commit/stash (filter-repo --force 灾难) — PM 5/22 沉淀
- **DEC-049**: Layer 1 三路统一 (DEC-049-1 portrait + DEC-049-2 BW_STYLES + DEC-049-3 fullbody) ✅ 全实施

## Wave 9 + 9.1 + Tester 三批 commit 总览

```
89bcfc7  fix(Wave9):    portrait Layer 1 wire (9 files +704 -3, 7/7 + 218 baseline)
1629332  fix(Wave9.1):  fullbody Layer 1 wire (7 files +527 -17, 6/6 + 178 baseline)
c570c2d  test(Wave9+9.1): Tester 跨题材独立 baseline (6 files +1300 -5, 623/623 PASS in 0.90s)
```

Layer 1 三路统一: shot path (W7) + portrait path (W9) + fullbody path (W9.1)
