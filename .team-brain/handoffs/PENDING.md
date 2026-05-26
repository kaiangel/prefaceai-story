# 待处理交接事项

> 所有 Agent 开工前必查，完成后删除对应条目
> **⚠️ 文档更新协议**: 共享文档由PM统一更新，详见 `.team-brain/TEAM_PROTOCOL.md`

---

## 🔧 test29 派活中 — 非人类通用性专项 + Packet retry (5/26, Founder 全派内测前)

来源: test29《荷塘渡》e2e (90分) 全维度回溯 `analysis/TEST29_FULL_RETROSPECTIVE_2026-05-26.md`。**核心主题: 数据层 Stage 2 已通用化, 消费层全人类中心**。Founder 决策全派内测前, Backend(#4) ‖ AI-ML(#5/#6/#7) 并行无冲突。

- 🟡 **#4 [Backend, Opus default, 内测前]**: Packet sequence — `app/middleware/db_retry.py` `_is_transient_connection_error` 加认 "packet sequence number wrong"(连接握手腐败)。根因: tab挂起→突发并发→新建连接 aiomysql 认证握手(connection.py:844)被公网/VPN截断→`pymysql.err.InternalError`, #5d 只认 2013/2006/2003+OSError 漏接。方案A 外科式(GET幂等已gated+retry重checkout干净连接+自愈已证)。次要可选: 前端 tab-resume serialize 轮询。孤立文件零冲突。
- 🟡 **#5 [AI-ML, Opus xhigh, 内测前]**: 非人类 type prompt builder 字段错配 — `character_prompt_builder.py:787 _build_aquatic_description`(及 _build_plant/insect/object 等) 从 `character['aquatic']` 读但 Stage 2 数据在 `physical`→空→golden 丢→金爷红。修: 各非人类 type builder 改读 `physical`(或 `character.get(type) or physical` fallback)。落地记忆 `project_schema_humanoid_fallback_remaining` 那条"5 type 待修"。
- 🟡 **#7 [AI-ML, Opus xhigh, 内测前]**: Seedream 融合非人类角色 — 金爷(鱼)+小蒲(草)焊成一只(草从鱼背长出, shot 10/15 像素确认), 自然度检查误判"intentional surrealist"放行。仅 8/22 同框 shot 受影响, 水彩柔化→90分。修: 多角色 shot prompt 强制"two SEPARATE distinct beings, NOT fused" + 自然度检查对非预期融合不洗白。
- 🟡 **#6 [AI-ML/Backend, 与#7联动]**: ShotValidator 视觉计数对非人类判 0→8/22 FAIL+重试(总耗时 44min/$1.14, vs 基线 +73%)。**#7 是真实成因之一**(确实没2独立角色)。修: 先修#7→图里真有2角色→计数过半; ShotValidator 计数对非人类 type 放宽/跳过(类 T20-6 environmental)。
- 🟢 **#8 [AI-ML/Backend, 内测后]**: BGM 提取器无人类时 `character_dominant_type` 默认 'human' + watercolor 误归 western_realistic。P3 低影响(仅微调 BGM 基调)。
- 📌 **新观察 [内测后评估]**: 结局 shot 出现剧本未设定的人类旁观者(撑船老人+第三人称旁白), 疑 by-design 叙事框架。

**验收红线**: #5 修后人类既有故事不退化; #7 修后非人类双角色 mini 验证不融合; 碰 storyboard_prompts.py/image_generator.py 必过角色一致性回归(@tester)。**Wave 13 仍未 commit, 本轮叠加工作区, 禁 destructive git**。

---

## 🟢 Wave 13 内测前 FIXBATCH — PM 审查通过, 待 Tester + DevOps (5/25, DEC-052)

代码全部写完仍在工作区未 commit (HEAD=68e4211=Wave12)。**PM 地毯式审查全绿无 blocker** (5+1 Ben 协议 + 完整调用栈):
- Backend #5d (MySQL retry middleware) + #6 (regenerate-portrait 异步) + #5e (clothing 旁路防崩) ✅
- Frontend #4A/#4B (确认流程 UX) + #5 (404 真根因) + #6 (reroll 异步轮询) + #9 (vitest 基建) ✅
- AI-ML #5b (schema 5 type 核实, 0 代码改动) ✅
- 🔑 §9.7.4 regenerate-portrait 三方契约逐字段对齐 (Backend ⟺ Frontend ⟺ 契约 v1.6) ✅
- 详见 DECISIONS DEC-052 + INTERNAL_BETA_READINESS_CHECKLIST_2026-05-25.md 顶部

**下一步**:
1. ⏳ **Tester 第二道** (并行进行中): pytest 30 新 (db_retry 14 + clothing_bypass 12 + regenerate_async 4) + vitest 15 + 全量回归 0 退化 + 独立核对 §9.7.4 字段
2. ⏳ **DevOps Wave 2** (双绿后): commit 分组 (见下) + push GitHub + VPS 第 5 次部署。⚠️ layout.tsx 须 rebuild + 浏览器硬刷新 (root layout inline script HMR 不刷新)
3. 📌 **PM 待办**: 更新 memory `project_schema_humanoid_fallback_remaining` 状态 (physical 维度 Wave 8 已根治, 5 type 不会因 physical 崩 — #5b 核实结论)

**DevOps commit 分组建议** (commit message scope 教训, 覆盖完整范围):
- **commit 1 (Backend, frontend-impact API 变更)**: `app/middleware/db_retry.py`(新) + `app/main.py` + `app/database.py` + `app/api/projects.py` + `app/services/character_designer.py` + `tests/test_wave13_db_retry_middleware.py` + `tests/test_wave13_clothing_bypass.py` + `tests/test_wave13_regenerate_portrait_async.py`
  - msg 覆盖: #5d MySQL retry middleware + pool_recycle 600s / #6 regenerate-portrait 异步化 (202+job) / #5e clothing 旁路防崩 (非穿衣 type 降 warning) + prompt 指引
- **commit 2 (Frontend)**: `frontend/src/app/create/CreateContent.tsx` + `frontend/src/app/layout.tsx` + `frontend/src/components/create/StageC.tsx` + `frontend/src/hooks/useETA.test.ts` + `frontend/vitest.config.ts`(新) + `frontend/vitest.setup.ts`(新) + `frontend/package.json` + `frontend/package-lock.json`
  - msg 覆盖: #4A 确认流程 hydrate 超时守卫 / #4B 后台生成按钮 scenesConfirmed 守卫 / #5 404 分级真根因 (模板字符串吃反斜杠) / #6 reroll 异步轮询 / #9 vitest 基建
- **commit 3 (契约+文档)**: `.team-brain/contracts/STATUS_API_CONTRACT.md` (§9.7.4) + 各 progress 三件套 + PENDING/DECISIONS/checklist/TEAM_CHAT
  - ⚠️ VPS 部署须含 DB 新列 Alembic (#5c, projects 表 3 列) — 与之前部署一致确认

---

## 📊 Wave 11 收尾计划 (5/24 update)

### 阶段 1: 清 P3 代码 ✅ 全完成
- Step 1 ✅ **DEC-051 fallback 红线** — CLAUDE.md 15-A (commit 17b6e28)
- Step 2 ✅ **MySQL pool** (commit 3b8956b, no-op 诊断) — 本地 pool_pre_ping+pool_recycle=1800+pool_size=10 早在 Wave 4 已配。5/23 500 = VPS 部署滞后, 阶段 2 部署修复
- Step 3 ✅ **LP image LCP priority** (commit 648b81c) — Showcase.tsx 1 行精确匹配
### 阶段 2: 🟡 **TASK-WAVE-11-DEPLOY-VPS** — DevOps 第 3 次部署 (3 commit: 3faf585 AI-ML + 28e33a7 Backend + 648b81c Frontend, VPS c570c2d → 648b81c)
### 阶段 3: 🟡 test26 e2e (cyberpunk + ai_entity, ABC 收官) + Founder spot-check + 内测启动

### 🔴 P1 内测前必修 (5/24 test26 新发现)
- **TASK-STYLE-ANTI-ANIME-FORBIDDEN** — 6 个非动漫画风 style 缺 anti-anime forbidden_keywords → 画风分叉
  - 实证: test26 cyberpunk 老周(写实)/陈明(动漫) 同框割裂
  - 🔴 必修: cyberpunk / ink / watercolor / ukiyo_e + 🟡 pixel / pastel_dream / children_book
  - by-design 不动: cartoon/ghibli/manga/korean_webtoon/chibi/illustration (本身动漫插画类)
  - 根因: style_enforcer.py forbidden_keywords 缺 anti-anime (对比 vintage_film L361 有完整防护)
  - 修法: 给缺陷 style 补 forbidden (anime/cartoon/cel-shaded等), AI-ML 逐个甄别不可一刀切 (ink 不能禁 painting)
  - 派: AI-ML (style_enforcer.py) + Tester (test26/27 复测画风统一)
  - 时机: 内测启动**前** (内测用户不会手动调 prompt, 必须系统锁死)
  - 本次 workaround: Founder 手动在调整框加写实关键词 (已用)
  - 详见: `.team-brain/analysis/STYLE_ANTI_ANIME_FORBIDDEN_GAP_2026-05-24.md` (全28 style 扫描表)
- **TASK-ETA-STAGE-LEVEL-GRANULARITY** (P2, 5/24 test26 发现) — ETA 30min 不变 + progress 不动
  - 根因: progress 只在 stage 边界更新, stage 内部(画像/shots 生成耗时步骤)不更新 → 依赖 progress 的 ETA 冻住
  - 关键: Stage 5 生图 ETA 准(按 shot 动态), 问题集中 Stage 1-4
  - 修法: ① 前端 ETA 接 simulatedTimer 时间插值平滑递减 (改动小, 立竿见影) ② 后端 Stage 1-4 加 sub-progress (根治)
  - 派: Frontend (插值) + Backend (sub-progress)
- **TASK-ADJUST-API-ASYNC** (P2, 5/24 test26 发现, 内测前) — adjust API 同步阻塞 90s → 前端 loading 卡死
  - 现象: 陈明"重新生成"点击后一直转圈, 后端图已生成完前端 loading 不解除, POST adjust 出现 3 次(疑超时重试)
  - 根因: /characters/{id}/adjust 同步阻塞 (调整文字+重生 portrait+fullbody 共 90s 才返回 200)
  - 影响: 用户以为卡住/重复点击, 内测用户会困惑
  - 修法: adjust 改异步(返 202 + 前端轮询 job), 或前端 loading 加 "AI 重绘约需 90s" 超时提示
  - 派: Backend (异步化) + Frontend (loading 提示)

### 🟢 P3 观察/轻微 (5/24 test26 回溯发现, 详见 TEST26_FULL_RETROSPECTIVE_2026-05-24.md)
- **MySQL 2003 transient** — 本地连阿里云**已反复 2 轮**(21:00-21:03 + 22:21, 后者含 TimeoutError 连接超时)均自愈。坐实本机网络层到阿里云不稳(IP/网络抖动)。生产VPS内网不受影响。**已反复=不是偶发** → 升级: 查阿里云 MySQL 安全组白名单是否限本机 IP段 / 本机网络稳定性(Ben + Founder)
- **NETWORK_ERROR elapsed 计时异常** — 报 96min/18min 不合理, 疑前端 tab 后台挂起累计计时 bug (Frontend 可选修)
- **404 日志分级不一致** — chapters/1/status 等确认前 404 部分记 error 部分记 routine warn (Frontend 统一)
- **良性不处理**: Invalid HTTP request×5 (uvicorn 拒畸形请求) / Failed to find Server Action x (Next dev 热重载)
- **前端测试框架缺失** (Wave 12 审查发现) — 项目无 vitest/jest/jsdom 依赖, useETA.test.ts (pre-existing) 跑不起来。长期补前端单测基建 (P3, Frontend)
- **regenerate-portrait 未异步化** (Wave 12 Backend 提及) — adjust 已异步, 但 regenerate-portrait 端点仍同步 ~60s, 同类问题。同 pattern 可加 (P2, Backend, 内测前或后)
- **🔴🔴 [根因已修正] 每个确认环节切换前端 10-30s 才显示 — 性能核心 (P2→内测前必修, 5/25 test28 Founder 核心体感)**
  - ⚠️ **根因修正**: 之前"拉全列表 N+1"判断**错误已纠正**。实测真根因: 前端 hydrate 调**单项目** GET /projects/{uuid}, 但 ① **阿里云 MySQL 公网往返 333-684ms/次(TCP实测)** ② hydrate **并发5请求**(project+chapter status/story/storyboard/bgm) ③ chapter **大JSON字段**(storyboard 20shots) → 叠加 10-30s
  - **生产判断**: 本地连公网MySQL特有, **生产VPS内网(<1ms)大幅改善** — 内测前须在VPS实测确认生产速度, 不能用本地公网延迟判断
  - 方案: ①生产VPS内网(最大头) ②合并hydrate为聚合端点(减round-trip) ③chapter status不拉storyboard全文(大字段按需) ④连接池复用
  - 派: Backend(聚合端点+大字段按需) + DevOps(VPS实测生产速度)。详见 TEST28_FULL_RETROSPECTIVE_2026-05-25.md P2-1
- **404 分级 Frontend Wave B 修复实测未生效 (P3, 5/25 test28 深挖)** — layout.tsx L195 正则匹配 status/story/storyboard/bgm→routine-404, 但 test28 实测 0 routine-404 + 18 仍 network level。修复未生效(可能 api.ts 另一路径记 network)。教训: 代码审查通过≠实测生效。派 Frontend 复查+e2e验证
- **[历史误判,作废] 原 "characters/scenes 确认页 hydrate 拉全列表慢" 分析 (下条) — 根因已被上条修正, 保留供对照**
- **🔴 characters/scenes 确认页 hydrate 拉全列表慢 → 超时兜底页 (UX 回归, P2, 5/25 test28, Founder 重点指出)**
  - 现象 1: characters 确认页加载弹"AI 正在努力创作中 + 返回工作台"兜底页 (CreateContent.tsx L1149 setHydrateError + L1621-1656 兜底 UI)
  - 现象 2: 刷新后"正在加载你的故事"~30s 才出角色预览
  - 同根因: **characters 确认页 hydrate 调 GET /api/projects/ 拉全部 44 项目 + chapters JOIN**, 项目累积越多越慢 (>120s 超时弹兜底 / <120s 撑出 30s 慢)
  - **Founder 核心 UX 点**: 确认流程中(角色/场景未确认完, 后面还要确认场景)**不该出现"返回工作台"兜底页** — 会打断流程, 体验割裂。确认中超时应继续等待/重试, 保持流程内
  - **"之前都是好的"判断**: 最可能是项目累积(44测试项目)放大了一直存在的查询性能问题, 但**值得查的回归疑点**: characters 确认页为何拉「全列表」而非「当前单项目」GET /api/projects/{id} — 若某次改动引入全列表拉取 = 真回归点
  - 两层修法: ① 根治 characters 确认页只查当前项目不拉全列表 (Frontend hydrate + 可能 Backend 加单项目端点) ② UX: 确认流程中 hydrate 超时不给"返回工作台"兜底, 改"继续等待/重试" (Frontend CreateContent L1149/L1621)
  - 调查方向: git blame CreateContent hydrate 拉全列表的引入时间 + 对比之前确认页 hydrate 逻辑
  - 派: Frontend (确认页 hydrate 改单项目 + 兜底 UX) + Backend (查询优化, 若需单项目端点)。关联 DASHBOARD-PERF-N1
  - 本地 workaround: 清理累积测试项目可缓解 (但生产多用户同样会遇到, 必须根治)
- **"后台生成去做别的"按钮缺场景确认守卫 (UX, P2, 5/25 test28, Founder 指出)**
  - 现象: storyboard(Stage 4 分镜)阶段就显示"后台生成去做别的"按钮, 但场景(R4-3)还没确认 → 用户点了离开会卡在 R4-3 场景确认没人点(Pipeline 等 1800s 超时)
  - 设计意图(StageC.tsx L110): "user cannot leave until both characters AND scenes are confirmed"
  - 已部分修: 副标题文案 STAGE_SUBTITLE storyboard="AI 正在创作故事，请稍候"(不带"后台生成"字样, RISK-T15-1) + Stage 4.5 文案也不带(T21-NEW-7 v1.4)
  - 🔴 漏修: "后台生成去做别的"**按钮**(handleBackground StageC L951 跳 dashboard)的**显示守卫**没同步 — 文案隐藏了但按钮还显示
  - 修法: 后台生成按钮加 ui_phase/scenes_confirmed 守卫, 只在场景确认后阶段(image_generation/image_preparation/bgm/music)显示, 与 STAGE_SUBTITLE 文案逻辑一致
  - **更新 (Founder 二次指出)**: 实际是按钮"忽有忽无" — storyboard 有 → scene_image_preparation 没(已隐藏) → 场景确认后又有。用户看到按钮闪烁出现/消失 = **比单纯早显示更困惑**。根因: 各 stage 显示守卫不统一 (scene_preparation 隐藏对了 storyboard 漏隐藏)。修法统一: 确认前全程(story_generation/character_design/screenplay/storyboard/scene_image_preparation)隐藏, 场景确认后(image_generation/image_preparation/bgm/music)一致显示
  - 派: Frontend (StageC 按钮显示条件)
  - 关联: 与"确认流程超时不该给返回工作台兜底"同类 UX 原则 — 确认流程中(角色/场景未确认完)不让用户离开

### ✅ Wave 12 FIXBATCH 完成 (5/24, test26 回溯全部问题修复)
- P1 style 画风 (AI-ML): cyberpunk/pastel_dream/gothic 补 anti-anime forbidden[:8]+介质 mandatory[:5]; 实测校准 (pastel🔴/ink·watercolor·ukiyo_e🟢守住)
- P2-1 adjust 异步化 (Backend+Frontend): 202+job轮询, 三方契约对齐 STATUS_API_CONTRACT v1.6 §9.7, 修陈明转圈
- P2-2 ETA 粒度 (Backend sub-progress + Frontend 插值)
- P3 (Frontend): NETWORK_ERROR计时 + 404分级
- 三 agent 地毯式审查全通过 (含 Ben DEC-030 gap PM 代补)
- ⏳ 待: PM 重启 backend + Tester Wave C 跨style画风+adjust端到端复测 → 部署 VPS → 内测

### 长期 (非本计划)
- **单场景故事成片视觉单薄 — 大纲阶段是否引导多场景 (产品考量, 5/25 test28 Founder 提出)**
  - 现象: test28《午夜钟魂》idea 是密闭空间(古董行单场景), LLM 正确识别 1 物理场景, 但 20 shots 全在同一空间 → 视觉丰富度受限
  - 非 bug: Pipeline 忠实按 idea 生成。是 idea 设定 (单场景密闭剧) 的固有取舍
  - 产品考量: 内测用户写单场景 idea 时成片可能单薄。是否在 Stage 1 大纲/Stage 3 剧本阶段检测单场景 → 建议/引导用户加场景 (空间转换提升张力), 或提示"单场景故事"预期
  - 权衡: 单场景剧是合理叙事形式 (独幕剧/密闭惊悚), 不应强制多场景, 但可"提示+建议"非强制
  - 派: PM 产品决策 + 可能 AI-ML (大纲 prompt 引导多场景) — 内测后排期
- ShotValidator chars=N/M Seedream 反复 FAIL — 模型限制, 长期 prompt 迭代
- **ShotValidator 手部畸形判定阈值 — 决定【暂不修】(5/25 test28 Shot 19, Founder+PM 权衡裁决)**
  - 现象: Shot 19 多指/手指畸形, retry 第3次 ShotValidator(Haiku)判 PASS 但人眼看手仍畸形 (判 PASS ≠ 人眼无瑕疵)
  - **决策: 暂不收紧 ShotValidator (Founder 5/25 拍板, PM 同意)**
  - 理由 (核心非"难", 是副作用权衡): 手部畸形是 Seedream 高频问题, 若收紧严判"手指略畸形=FAIL" → 大量 shot 触发 retry(20张可能半数) → Pipeline 时间/成本翻倍 + 模型局限致 retry 后仍畸形 → 陷"判FAIL→retry→还FAIL"循环甚至卡住。**过度 retry 比漏判轻微瑕疵更糟**
  - 当前阈值合理: 抓"明显多手(3+hands)"FAIL + 放过"手指略不自然" = 抓大放小, 是成本-质量正确平衡点
  - 兜底策略: ① 用户层手动重生(按需, 成本可控) ✅ 正解 ② 长期靠 Seedream 模型进步 ③ 不靠验证器严判(全局 retry 成本失控)
  - 教训保留: 不能只信 ShotValidator PASS, 人眼复核仍必要 (手部=LLM 视觉盲区)
  - 重新评估触发: 若 Seedream 手部能力显著退化 / 用户大量反馈手部问题, 再议
- CLAUDE.md untracked — 待 Founder 决定是否 git add (本地生效不影响功能)

---

## 📊 (历史) 当前剩余 task (5/23 17:30 update)

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

### 🟢 P3 长期 (Wave 11+ 待修)
- **TASK-WAVE-11-MYSQL-POOL-PRE-PING-RELIABILITY** (5/23 19:48 Founder dashboard 实测发现)
  - 现象: backend idle ~1h 后 Founder GET /api/projects/ → 500 (pymysql.err.OperationalError 2013 'Lost connection during query'), 浏览器 NETWORK_ERROR TypeError Failed to fetch 131s 超时
  - 自动恢复: 第 2 次调用 backend 已 reconnect (SQLAlchemy pool_pre_ping 工作)
  - 影响: 用户 idle 后第 1 次操作可能 500 + 浏览器 131s 卡死 = 极差体验
  - 待查 + 修法:
    1. SQLAlchemy `create_async_engine(pool_pre_ping=True, pool_recycle=3600)` 是否已配 (推测没有)
    2. 加 connection-level retry middleware (FastAPI middleware) 自动 retry 1 次 transient MySQL error
    3. 或/和: 加 frontend retry on NETWORK_ERROR (一次失败重发一次, 比 131s 超时友好)
  - 文件: `app/database.py` (engine 配置) + `app/main.py` (middleware) + `frontend/src/lib/api.ts` (apiFetch retry)
- **TASK-WAVE-11-LP-IMAGE-LCP-PRIORITY** (5/23 17:50 Founder 测试发现, "之后要修别忘了")
  - 现象: Next.js dev console warn `Image with src "/comics/story-a/shot_01.png" was detected as the Largest Contentful Paint (LCP). Please add the "priority" property if this image is above the fold.`
  - URL: localhost:3000/ (LP 主页, above the fold)
  - 不阻塞功能, 但影响首屏加载性能 (LCP 指标)
  - 修法: 找 LP 主页 `<Image>` 组件用 `/comics/story-a/shot_01.png` 的, 加 `priority` prop
  - 文件可能在: `frontend/src/app/page.tsx` 或 `frontend/src/components/landing/*`

### 🔮 长期 (memory + Phase 6+)
- `project_mysql_migration.md` — ✅ 已完成 5/23 17:00 (memory 已 update)
- `project_schema_humanoid_fallback_remaining.md` — Wave 8 T22-NEW-9 已根治, memory 可标 ✅
- `project_confirm_outline_not_wired.md` — Wave 8 T22-NEW-8 验证已实现, memory 可标 ✅
