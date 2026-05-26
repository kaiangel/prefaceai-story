# 内测前就绪清单 (Internal Beta Readiness)

> 2026-05-25 PM 整理: 汇总 Wave 12 + test26/test28 回溯全部待办, 分层标注阻塞性。
> 来源: PENDING.md + TEST26/TEST28_FULL_RETROSPECTIVE。

---

## ✅ Wave 13 FIXBATCH PM 审查通过 (2026-05-25, 集成关口第一道, DEC-052)

代码全部写完待 commit (HEAD=68e4211)。PM 5+1 Ben 协议 + 完整调用栈地毯式审查全部改动 → **全绿无 blocker**:
- **#5d** MySQL retry middleware (db_retry.py + main.py wire + database.py recycle 600s): ✅ 4 重约束代码可证 (transient-only / 幂等 GET-only / 限1次 / 不掩盖真错误), wire 顺序 CORS 最外层正确
- **#6** regenerate-portrait 异步化: ✅ **§9.7.4 三方契约逐字段对齐** (Backend return ⟺ Frontend pollCharacterJob ⟺ 契约), kind="regenerate_portrait" 区分, DEC-051 fallback 全保留
- **#5e** clothing 旁路防崩: ✅ 非穿衣 7 type 降 warning, 穿衣 type 仍 raise, 崩溃点 (design() L144 在 LLM fallback 之外) 消除, 0 删 fallback
- **#5b** schema 5 type 核实: ✅ 0 代码改动, physical 已根治 (memory 待更), clothing 旁路交 #5e 修
- **#4A/#4B/#5/#9** (Frontend): ✅ 确认流程超时守卫 / 后台按钮 scenesConfirmed 单信号 / 404 真根因 (模板字符串吃反斜杠) 源码层根治 / vitest 基建
- 待 Tester 第二道 (pytest 30新+vitest 15+回归0退化+独立核对§9.7.4) 双绿 → DevOps 第 5 次部署
- 详见 DECISIONS DEC-052

---

## 🔴 第一批: Wave 12 收尾 (代码已改完审查通过, 待上线验证) — 阻塞内测

| # | 任务 | 派 | 工作量 | 状态 |
|---|---|---|---|---|
| 1 | **Tester Wave C 复测** — 跨 style 画风统一(cyberpunk/pastel/gothic 改后) + adjust 端到端不转圈 + ETA 不冻结 | Tester | ~1-2h (含生图) | ⏳ 待 (需先重启 backend 已做) |
| 2 | **VPS 部署 Wave 12** — style_enforcer + adjust异步 + sub-progress + 前端, 含 DB 新列 Alembic 迁移确认 | DevOps | ~40min | ⏳ 待 (Tester 通过后) |

Wave 12 已改完 (P1 style 画风 + P2 adjust 异步 + P2 ETA + P3 NETWORK_ERROR), 三 agent 审查通过。**只差复测 + 部署上线**。

---

## 🔴 第二批: test28 新发现必修 — 阻塞内测 (核心体验)

| # | 任务 | 派 | 工作量 | 备注 |
|---|---|---|---|---|
| 3 | **P2-1 性能: 每环节 10-30s 才显示** — ①DevOps VPS 实测生产速度(内网MySQL,确认是否仍慢) ②Backend 合并 hydrate 聚合端点(减并发round-trip) ③Backend chapter status 不拉 storyboard 全文(大字段按需) | DevOps + Backend | DevOps ~30min / Backend 中等 | 实测真根因=本地公网MySQL 333ms, **生产VPS内网大幅改善, 须先VPS实测再定还修多少** |
| 4 | **P2-2+P2-3 确认流程 UX (合并)** — ①"返回工作台"兜底页: 确认流程中(角色/场景未确认完)超时改"继续等待"不给返回工作台 ②"后台生成"按钮: 确认前全程隐藏, 仅场景确认后一致显示(修忽有忽无) | Frontend | 中等 | 同一 UX 原则: 确认流程中不让用户离开/困惑 |
| 5 | **P3-1 404 分级 Wave B 未生效复查** — layout.tsx routine-404 实测 0 生效(18仍network), 复查为何未生效 + e2e 验证 | Frontend | ~小 | Wave 12 改了但实测没生效, 代码审查≠实测 |
| 5b | ✅ **schema 5 type physical 核实完成 (Wave13 AI-ML)** — physical 维度 Wave 8 已根治 (has_humanoid_fallback 通用 fallback, 路径3 warn-not-raise), aquatic/object/plant/insect 选了**不会因 physical 崩**。PENDING"已根治"对, memory"待修"过时(待 PM 更新). **但挖出 clothing 旁路 P1 见 5e** | AI-ML 已完成 | — | ✅ 0代码改动纯核实 |
| 5e | **🔴 clothing 旁路崩溃点 (Wave13 #5b 挖出, PM 追调用栈 verify 属实)** — character_designer._validate_characters(L619) 对【所有 type 一刀切】要求 clothing top/bottom/footwear/style, 真 object(钟)/aquatic(鱼)/plant/insect 天然没衣服 → Stage2 raise。致命: 在 LLM fallback try/except 【之外】(L127, fallback在L83/L103) + orchestrator L576 design() 【无 retry】→ 冲垮 pipeline。test28 没暴露(灵魂是 supernatural 人形)。修法: A(推荐)非穿衣 type clothing 缺字段降 warning 不 raise(同 anthropomorphic physical warning pattern) + B(源头)Stage2 prompt 给4type加 clothing 指引(AI-ML 配合文案) | Backend (Wave3, Opus4.7 xhigh) | 中等 | **真P1**: 内测用户选这些 type 角色崩 pipeline |
| 5c | **DB 新列 VPS Alembic 迁移确认** — projects 表 aspect_ratio/raw_outline_json/confirmed_outline_json 3 列, VPS 部署 Wave 12 时必须 alembic upgrade 确认这些列在 VPS DB (否则查询报列不存在) | DevOps | ~部署时确认 | 与 #2 部署一起, 独立强调防遗漏 |
| 5d | **🔴 MySQL idle 后 2013 lost connection — 第1次操作 500 (5/25 12:13 实测复现, 之前清单漏了)** — idle 1h+ 后连接被阿里云服务端断, pool_pre_ping 实测没完全防住(公网+ping本身超时 Errno60)。原 PENDING TASK-WAVE-11-MYSQL-POOL-PRE-PING-RELIABILITY 复现。修: ①connection-level retry middleware(transient 2013/2003 自动retry 1次, app/main.py) ②pool_recycle 缩短(主动回收idle连接) ③生产VPS内网减少失效 | Backend + DevOps | 中等 | **影响内测**: 用户idle后(看片离开再回)第1次操作500+卡顿。生产内网改善但仍需retry兜底 |

---

## 🟡 第三批: 内测前建议修 (体验提升, 非阻塞)

| # | 任务 | 派 | 工作量 | 备注 |
|---|---|---|---|---|
| 6 | **regenerate-portrait 异步化** — adjust 已异步, 但 regenerate-portrait 端点仍同步 ~60s 转圈, 同类问题 | Backend | ~小 (同 adjust pattern) | 内测用户也会用"重新生成", 建议一起异步化 |
| 7 | **MySQL 2003 transient → 阿里云安全组白名单** — 本地反复2轮自愈, 查安全组是否限本机IP段 | Ben + Founder | 查证 | 生产VPS内网不受影响, 本地开发体验 + 排除隐患 |

---

## 🟢 内测后 / 待决策 (不阻塞)

| # | 任务 | 派 | 备注 |
|---|---|---|---|
| 8 | 单场景成片丰富度 — 大纲阶段是否引导多场景 (提示非强制) | PM + AI-ML | 产品考量, idea 取舍 |
| 9 | 前端测试框架缺失 (无 vitest, useETA.test 跑不起来) | Frontend | 测试基建, 长期 |
| 10 | CLAUDE.md untracked — 是否 git add | Founder 决定 | 本地生效不影响功能 |
| 10b | **test25 补跑 (illustration + supernatural 银发狐妖)** — L-3 遗留, test22/26/27/28 跑了, test25 似未跑 | Founder e2e | 1 轮 e2e | ABC 多题材已覆盖, test25 补全 illustration 风格验证 (非阻塞, 可内测后) |
| 10c | Wave 10 commit L210/L283 CLAUDE.md 同步 — 实际 L241+L301 已更新 SQ-2 智能选择, **此项已完成核对无需做** | — | — | ✅ 核对已完成 |

---

## ⚪ 决定不修 / 模型限制 (有兜底)

| # | 项 | 决策 |
|---|---|---|
| 11 | Shot 19 手部畸形 / ShotValidator 手部判定 | **暂不修** (收紧致过度retry, 用户手动重生兜底) |
| 12 | ShotValidator chars=N/M 反复 FAIL | 模型限制, 长期 prompt 迭代 |
| 13 | Invalid HTTP request / Server Action x | 良性, 不处理 |

---

## 内测启动建议路径

```
1. Tester Wave C 复测 (#1) → 通过
2. VPS 部署 Wave 12 (#2) + DevOps VPS 实测性能 (#3 的 ①)
   → 关键: VPS 实测确认 P2-1 性能在生产(内网)是否还慢, 决定 #3 ②③ 修多少
3. Frontend 修确认流程 UX (#4) + 404 复查 (#5)  [可与 2 并行]
4. (建议) Backend regenerate-portrait 异步 (#6)
5. 再跑 1 轮 e2e 验证 (用 full-retrospective skill 回溯) → 内测启动
6. #7 MySQL 安全组 Ben 并行查
```

**内测前最小必做**: #1 #2 #3(VPS实测) #4 #5 (第一批+第二批)。#6 #7 建议。#8-13 内测后/不修。
