# Frontend 状态速览（供其他Agent参考）

> 更新时间: 2026-05-25 [Wave 13 #6 前端] regenerate-portrait (reroll) 改异步轮询 完成

## Wave 13 #6 前端 (2026-05-25) ✅ regenerate-portrait 异步轮询

**1 文件改 (StageC.tsx), build 0 errors, tsc 0, eslint 0, npm test 15/15, 0 越权**

### 给 @tester (复测点)
- **reroll (角色卡 → 调整 → 留空提交) 现在异步**: POST `regenerate-portrait` → 202 + job_id → 轮询 GET `/characters/adjust-jobs/{job_id}` → completed 刷新 portrait
- 复测: ① reroll **不再转圈卡死** (loading 显 backend stage_message + progress%) ② 轮询拿到新 portrait_url, 角色卡刷新 (cache-buster, 同路径覆盖也能看到新图) ③ failed → toast error 提示
- adjust (带文字调整) **行为不变** (回归点: 仍记录 adjustment + description + portrait)

### 给 @backend (契约对接确认)
- 已对接 Backend Wave 13 #6 异步 `regenerate-portrait` (§9.7.4): POST 202 + GET adjust-jobs 复用 §9.7.2 轮询端点
- 前端严格按 §9.7.4 字段消费: `kind="regenerate_portrait"` 区分, `result.portrait_url/fullbody_url` cache-buster, fullbody null 非阻塞
- 0 新 API 需求 / 0 schema / 0 契约改动 (纯对接已有异步端点)

### 给 @devops (部署注意)
- StageC.tsx 非 root layout, dev HMR 可正常 reload; 部署正常 build 即可 (无 layout.tsx 类 inline script 限制)

---

## Wave 13 #4 + #5 + #9 (2026-05-25) ✅

**3 项完成 (6 文件改 + 2 新建, build 0 errors, npm test 15/15 PASS, 0 越权)**

### 给 @tester (前端现在有测试框架了 + e2e 验证点)
- **🆕 vitest 已装**: `npm test` (= `vitest run`) 跑前端单测; `npm run test:watch` 监听模式。配置 `vitest.config.ts` (jsdom + `@` alias) + `vitest.setup.ts` (含 @testing-library/jest-dom)。可写 `*.test.ts` / `*.test.tsx` (含 React 组件测试, jsdom env)
- `useETA.test.ts` 现 15/15 PASS via `npm test` (原来无 runner 跑不起来)
- e2e 验证点:
  1. **确认流程中** (URL /outline /characters /scenes) hydrate 超时 → 显"正在自动重试…确认环节马上回来", **无"返回工作台"按钮** (8s 自动 reload, 上限 3 次); 纯生成/preview 阶段仍有"返回工作台"
  2. **后台生成按钮**: 确认前全程 (story_generation→storyboard→scene_image_preparation) **不显示**; 仅场景确认后 (image_generation/bgm) 一致显示 (修"忽有忽无"闪烁)
  3. **404 分级实测**: pre-confirm chapter 404 (status/story/storyboard/bgm/scene-references) 在 client.log 记 `level: 'routine-404'` (不再误记 network)。**注意 layout.tsx 改动需重启 dev/重新 build, dev HMR 不刷新 root layout inline script**

### 给 @devops (client.log Monitor 去噪 + 部署注意)
- **#5 routine-404 真正生效了**: 之前 Wave B 的 regex 因模板字符串吃反斜杠失效 (`//chapters/d+/`变行注释), 已改纯字符串检查。Monitor 可把 `routine-404` 视同 routine 过滤
- **🆕 `proxy-init` level**: 页面加载时 POST 一条 `level: 'proxy-init'` 记 proxy 版本号 (`w13-404-v2`), 用于确认浏览器加载的 client-log proxy 版本 (非错误, Monitor 可忽略/用于版本核对)
- **部署注意**: layout.tsx 是 root layout, 改它的 inline script 必须重新 build + 浏览器硬刷新, Next dev HMR 不更新已加载 tab 的 inline script

### 给 @backend (无新增 API 依赖)
- 本批 0 新 API / 0 schema / 0 STATUS_API_CONTRACT 改动 (纯前端 UX + 日志分级 + 测试基建)
- #4B 依赖既有字段 `scenes_confirmed` (hydrate 已读, 无新需求)

---

## TASK-TEST26-FRONTEND-4 (2026-05-24) ✅

**4 项前端修复完成 (5 文件改, build 0 errors, 0 越权)**

## TASK-TEST26-FRONTEND-4 (2026-05-24) ✅

**4 项前端修复完成 (5 文件改, build 0 errors, 0 越权)**

### 给 @backend (adjust 异步 §9.7 对接确认)
- Frontend `handleApplyAdjustment` (StageC.tsx) 已按 STATUS_API_CONTRACT §9.7 改异步轮询:
  - POST `/projects/{id}/characters/{char_id}/adjust` → 读 `job_id` (期望 202)
  - 轮询 GET `/projects/{id}/characters/adjust-jobs/{job_id}` 每 2s → 读 `status`/`progress`/`stage_message`/`result`/`error`
  - completed → `result.portrait_url` + `result.character.description_zh` 刷新角色卡 (cache-buster)
  - 404 = 过期/未注册 → 重试 (不当失败)
- **依赖确认**: backend adjust 端点须真返 202+job_id, adjust-jobs 须真返 §9.7.2 字段名. 若字段名/路径有出入请同步 @frontend
- reroll (adjust 留空) 仍走同步 `regenerate-portrait` (§9.7.3 本轮未异步化, 未动)

### 给 @tester (e2e 验证点)
1. 角色页填描述点"重新生成": loading 显 "AI 重绘中 X%" (不裸 spinner), 完成自动刷新头像, **POST adjust 只发 1 次** (旧 bug 发 3 次)
2. adjust 失败: toast "调整失败：{error}"
3. /generating Stage 1-4: ETA "预计还需约 N 分钟" 随时间递减 (不冻结)
4. tab 挂起后看 client.log: 无 error-level "NETWORK_ERROR 96min" (改 warn)
5. /outline 停留: pre-confirm 404 记 `level: 'routine-404'` (非 network/error)

### 给 @devops (client.log Monitor 去噪)
- layout.tsx fetch wrapper 新增 `level: 'routine-404'` bucket (pre-confirm chapter 404 专用)
- api.ts NETWORK_ERROR: tab 挂起 (elapsed>120s 或 document.hidden) → console.warn; 真网络错 → console.error
- Monitor 去噪可把 `routine-404` 视同 routine warn 过滤

---

## T22-NEW-8 StageB confirm-outline wire 审查 (2026-05-22) ✅

**结论**: 已实现, 0 代码修改

StageB.tsx `handleConfirm` (L152-255) 已调用 `POST /projects/${projectId}/confirm-outline`, 发送用户编辑后的完整大纲 state. PENDING.md 引用的 `chapters/1/confirm-outline` 端点不存在. npm run build 20 routes 0 errors 通过.

**给 @PM**: T22-NEW-8 任务描述中的 endpoint URL (chapters/1/confirm-outline) 有误, 正确端点是 project-level confirm-outline (projects.py L518). 该端点已被 StageB.tsx 正确调用. 建议 PM 将 T22-NEW-8 标注为已完成.

---

## T22-NEW-5 R4-2 scene_review 前端删除 (2026-05-22) ✅

**状态**: 完成 (5 文件改, build 20 routes 0 errors). 等待 Backend Wave 8 同步部署.

### 给 @backend (最重要)

**Frontend 已完成 R4-2 前端侧删除. Backend Wave 8 必须同步做:**
1. `pipeline_orchestrator.py` — 删除 R4-2 wait loop (ui_phase=scene_review 阻塞逻辑)
2. `STATUS_API_CONTRACT.md` — 升级至 v1.5 (删除 `scene_review` ui_phase 条目)
3. `chapters.py` — 清理 `confirm-scenes` endpoint (或标注废弃)

**部署铁律**: 前端不可单独上线. 必须与 Backend Wave 8 同时部署.

### 改动汇总

| 文件 | 改动 |
|------|------|
| `frontend/src/types/create.ts` | `GenerationSubPhase` 删 `"scene-preview"` |
| `frontend/src/lib/createUrl.ts` | 删 `scene_review: "scenes"` + `"scenes"` case → `"scene-refs-preview"` |
| `frontend/src/app/create/CreateContent.tsx` | 删 `scene_review` mapping + `isSceneReview` block + race guard |
| `frontend/src/components/create/StageC.tsx` | 删 handlers + render block + 更新 D.23 watcher |
| `frontend/src/components/create/StageB.tsx` | D.14 progressStage `"scene-preview"` → `"scene-refs-preview"` |

### 保留完整 (0 破坏)

- ✅ R4-1: `character_review` / `char-preview` / CharacterPreview 组件
- ✅ R4-3: `scene_references_review` / `scene-refs-preview` / SceneRefsPreview 组件
- ✅ /outline 页面

---

## T22-NEW-2 SceneRefsPreview 卡片智能展示 (2026-05-22) ✅

**状态**: 完成 (1 文件改 StageC.tsx, build 20 routes 0 errors)

### 4 种 case 真 cover (视觉无空洞)

| Case | 布局 | 标签 | 按钮适配 |
|------|------|------|---------|
| 内景+外景都有 | grid-cols-2 双图 | 无 | 重生内景+重生外景+重生全部 |
| 只有内景 (洞穴/海底) | 全宽单图 | "(室内场景，无室外画面)" | 重生内景+重生此场景 (无重生外景) |
| 只有外景 (海面/沙滩) | 全宽单图 | "(室外场景，无室内画面)" | 重生外景+重生此场景 (无重生内景) |
| 都无 (异常) | 统一错误提示 | "场景图生成失败，请重新生成" | 重新生成场景图 |

### 给 @pm / @tester
- 0 越权, 0 改 backend / STATUS_API_CONTRACT / PENDING / DECISIONS
- build 20 routes 0 errors (0 新增 warning)
- 60s 倒计时 + cache-buster + hydrate + poll 全不动

---

## T21-NEW-7 Wave II Frontend — 场景视觉确认页面 (2026-05-21)

**状态**: ✅ 完成 (5 文件改 + 0 越权, 14/14 useETA 单测 PASS, build 20 routes 0 errors)

### Founder DEC-047 决方案 D 真落地

镜像 characters 页面对偶设计 — 场景参考图真预览 + 编辑 + 重生 + 60s 倒计时. 与 ScenePreview (R4-2 情节文字确认) 严格区分: scene-refs-preview (R4-3) 看真场景参考图.

### 改动汇总

| 文件 | 主要改动 |
|------|---------|
| `frontend/src/types/create.ts` | `GenerationSubPhase` 加 `scene-refs-preview` |
| `frontend/src/lib/createUrl.ts` | `UI_PHASE_TO_URL` 加 `scene_references_review: "scenes"` + `deriveUrlStageFromState` 加 subPhase |
| `frontend/src/hooks/useETA.ts` | `STAGE_BUDGET_SECONDS` 加 `scene_image_preparation=180` + `scene_references_ready=0` + `REVIEW_STAGES` 加 `scene_references_ready` |
| `frontend/src/app/create/CreateContent.tsx` | `ChapterStatusResp` 加 2 新字段 + Watcher `phaseToSubPhase` 加新 ui_phase + `isSceneRefsReview` force-route 分支 |
| `frontend/src/components/create/StageC.tsx` | 加 `SceneRefsPreview` 组件 (~370 行) + 在 render switch 加新 subPhase 分支 + D.23 watcher 加 scene-refs-preview + STAGE_LABEL/STAGE_SUBTITLE 加新 stage 文案 |
| `frontend/src/hooks/useETA.test.ts` | 加 5 新 T21-NEW-7 测试 (6a-6e, 全 PASS) |

### 给 @backend

- 消费 STATUS_API_CONTRACT v1.4 真完整: ui_phase=scene_references_review + 2 新字段 (scene_references_ready/scene_references_confirmed) + 3 endpoint
- frontend 严格不算 ui_phase, 从 backend status response 真读 (Ben 5/13 backend authoritative)
- 0 backend 文件修改 (T21-NEW-7 Wave I 已完成)
- 重启 backend 必须真跑 Alembic 006 (2 列 + Backfill)

### 给 @pm

- 14/14 useETA 单测 PASS (含 5 新 T21-NEW-7 测试)
- tsc 0 errors / lint 0 新增 warning / build 20 routes 0 errors
- 0 越权 (仅改 frontend/src/{types,lib,hooks,app/create,components/create})
- 0 修改共享文档 (.team-brain/*) — paste 给 PM 代写
- 严格镜像 CharacterPreview / ScenePreview 对偶设计 (60s 倒计时 + 编辑 + 重生 + anti-pattern fix)

### 给 @tester (test22 验证 fairytale 美人鱼)

| 验证项 | 期望 |
|------|------|
| Stage 4.5 跑中 | ui_phase=storyboard_running → URL /generating + 显示 "正在准备场景视觉" + ETA |
| Stage 4.5 完成 R4-3 | ui_phase=scene_references_review → URL /scenes + SceneRefsPreview 卡片 + 60s 倒计时 |
| GET /scene-references | hydrate 真 scene_references list (每 location 含 interior_url+exterior_url+description_zh+meta) |
| 编辑 + 重生 | textarea 改描述 → 调 POST regenerate-reference 真生新图 + cache-buster ?v={epoch} URL 真避免浏览器 cache |
| 重生 3 按钮 | 重生内景 / 重生外景 / 重生全部 真独立工作 |
| 60s 自动确认 | 倒计时到 0 → 自动调 POST confirm-scene-references → router 跳 /generating |
| 手动确认 | "确认场景, 继续生成画面" 按钮 → 立即跳 /generating + 后台 POST confirm-scene-references |
| Stage 5 真启动 | confirm 后 backend ui_phase → shot_generating, frontend Watcher 派生 subPhase=shot-gen, /generating 显进度 |

### 给 @resonance

- 内测启动后, scene-refs-preview 页面是用户体验亮点 — "我可以真看场景图, 不像别家黑盒生成" 强宣传点

---

> 更新历史: 2026-05-20 [T20-44] useETA.ts 真消费 estimated_remaining_seconds 完成

## T20-44 Frontend ETA Fix (2026-05-20)

**状态**: ✅ 完成 (3 文件, 0 越权)

### 改动汇总

| 文件 | 主要改动 |
|------|---------|
| `frontend/src/hooks/useETA.ts` | T20-44: P1 backend authoritative bypass smoothing |
| `frontend/src/components/create/StageC.tsx` | text-gen poller >= 0 fix; BGM log guard |
| `frontend/src/hooks/useETA.test.ts` | test 4 updated for T20-44 new behavior (9 PASS) |

### 给 @backend

- 0 API 契约改动
- STATUS_API_CONTRACT v1.3 §1.4 已消费 (backend ETA 直接用)
- BGM 阶段 `shots_completed == shots_total` 处理: frontend 已 guard, 不再合成假 "已生成 X/Y" 条目

### 给 @tester (test21 验证)

| RISK | 验证场景 |
|------|----------|
| T20-44 | 跑 Pipeline image_generation 阶段, backend ETA ~790s, frontend 应显 "约 13-14 分钟" (不是 "3 分钟") |
| T20-44 | BGM 阶段应显 "正在生成配乐..." 不显 "已生成 27/27 个片段" |
| T20-44 | ETA 偏差 ≤ ±20% vs backend estimated_remaining_seconds 真值 |

### 给 @pm

- tsc 0 errors, lint 0 新增, build 0 errors, dev server 200
- 0 越权 (仅改 frontend/src/hooks + frontend/src/components/create)
- Wave 1-4 修复不退化 (useETA T20-9.v3 priority chain / StageC pollers / BGM display)

---

---

## Wave 4 — TASK-T20-FIXBATCH-5: 3 P2 UX 修复 (2026-05-19 22:55)

**状态**: ✅ 完成 (3 文件, 0 越权)

### 改动汇总

| 文件 | 主要改动 |
|------|---------|
| `frontend/src/components/create/StageC.tsx` | T20-24 + T20-25 + 部分 T20-11.v2 |
| `frontend/src/app/create/CreateContent.tsx` | T20-25 + T20-11.v2 |
| `frontend/src/lib/api.ts` | T20-11.v2 fetchBgmInfo 加 options |

### T20-24 — Progress Bar 第一次 poll 立即 fire

- text-gen + shot-gen poller body 抽 named function (`runTextGenPoll` / `runShotGenPoll`)
- `void runTextGenPoll(); pollRef.current = setInterval(runTextGenPoll, 2000)` 立即 fire + 持续
- 修了 "0% 卡 2s" Founder 实证
- 同步加 silentStatuses=[404] (Stage 2 早期防御)

### T20-25 — confirm-characters 后跳错修复

- `handleConfirmCharacters`: push `/generating` (不 `/scenes`), subPhase=text-gen (符 Wave 9 contract)
- Watcher `isCharReview` URL force 加 `!charactersConfirmedNow` gate (Wave 9 path 与 legacy 对齐)
- Watcher subPhase 派生加 `charactersConfirmedNow` / `scenesConfirmedNow` gate (防 stale ui_phase 覆盖)
- 新流程: /characters → /generating (progress bar 显 Stage 3 进度) → /scenes (Stage 3 done)

### T20-11.v2 — /outline 页面 polling silentStatuses

- CreateContent Watcher status poll → silentStatuses=[404]
- Hydrate status poll → silentStatuses=[404]
- `fetchBgmInfo` 加 options 参数 + hydrate 传 silentStatuses=[404]
- D.23 watcher (StageC checkpoint) status poll → silentStatuses=[404]
- 预期 /outline 4 min 停留 console.warn 从 ~50 → ~0

### 给 @backend

- 0 API 契约改动
- 0 schema 改动
- STATUS_API_CONTRACT v1.2 字段消费不变

### 给 @tester (Wave 5 验证)

| RISK | 验证场景 |
|------|----------|
| T20-24 | 跑 Pipeline, 进 /generating 立即观察 progress bar 真接 5-10% (不 0%) |
| T20-25 | 走 confirm-characters → 应直接 /generating 显进度 → Stage 3 done 跳 /scenes |
| T20-11.v2 | 进 /outline 停留 5 min, client.log chapters/* 404 warn 数从 ~50 → ~0 |

### 给 @pm

- tsc 0 errors, lint 0 新增, dev server 200
- 0 越权 (仅 frontend/src/{components,app,lib} 内)
- Wave 1+2 修复全保留 (useETA / anti-pattern / 60s 倒计时 / T20-11 hydrate guard)

---

## Wave 18 — T20-9.v3 ETA 全局重审 Frontend (2026-05-19)

**状态**: ✅ 完成 (2 文件, 0 越权)

**改动文件**:
- `frontend/src/hooks/useETA.ts`
  - 新增接口: `shotsTotal`, `shotsCompleted`, `shotsFailed` (STATUS_API_CONTRACT v1.1)
  - Priority chain: estimatedRemainingSeconds > shots公式 > backendEtaSec > budget fallback
  - Frontend fallback 公式: `(shots_total - shots_completed) * per_shot_real / 3`
  - 滑动窗口 per_shot_real: 最近 5 次 shot 完成间隔实测均值 (fallback 80s)
  - **删除 "正在收尾"**: isReallyWrappingUp + WRAPPING_UP_PROGRESS_THRESHOLD 已移除
  - **Terminal UX 修复**: progress>=95% 仍显具体 ETA 数字 (Founder 反馈修复)
- `frontend/src/components/create/StageC.tsx`
  - shot-gen poller type: 加 `shots_total?`, `shots_completed?`, `shots_failed?`
  - 3 个新 ref: `backendShotsTotalRef`, `backendShotsCompletedRef`, `backendShotsFailedRef`
  - useETA call: 透传 3 个新字段
  - 日志合成: **message regex 已替换** → 用 shots_completed 直接比较 (T20-9.v3 要求)
  - RF-4: 接受 estimated_remaining_seconds >= 0 (旧 > 0)

**给 @backend**: STATUS_API_CONTRACT v1.1 字段 shots_total/completed/failed 前端已消费. T20-13 依赖已就绪.

**给 @tester**:
e2e 验证点 (T20-9.v3 完成后):
1. image_generation stage: ETA 显示具体分钟数 (而非 "正在收尾" 或 "即将完成")
2. progress >= 95% 仍显 "预计还需约 N 分钟"
3. stage = bgm: ETA 仍显示 (STAGE_BUDGET_SECONDS[bgm]=180s)
4. completion: stage=completed 或 progress>=100 → etaText = null (ETA 消失)
5. console log "[useETA] T20-9.v3 fallback": 当 backend estimatedRemainingSeconds 为 null 时出现
6. Wave 1 不退化: CharacterPreview 60s 倒计时 / ScenePreview anti-pattern / hydrate guard

**给 @pm**: tsc 0 errors, lint 0 新增 error, dev server 200

---

## Wave 17.5 — TASK-T20-FIXBATCH-4 T20-12 重做 (2026-05-19)

**状态**: ✅ T20-12 重做完成 (1 文件, 0 越权)

**背景**: Wave 1 前一 session 执行了方案 C (完全删除倒计时). Founder 16:55 决策是方案 A (升级 20s → 60s). 本 session 重做.

**改动文件 (1)**:
- `frontend/src/components/create/StageC.tsx` CharacterPreview 区域 (L1279-1515)
  - **T20-12 重做**: 恢复 60s 倒计时 (从 20s 升级, 与 /scenes B58 一致)
  - **countdown + paused state** 恢复
  - **定时器 useEffect**: B36 gate (无 characters 不启) + D.14 gate (locked 停止) + paused gate
  - **副作用 useEffect**: countdown===0 时触发 handleConfirmWithApi (T20-15 anti-pattern 修复模式)
  - **handleAdjust**: 恢复 setPaused(true) (调整时暂停倒计时)
  - **倒计时 badge**: 圆形边框 + 数字 + "秒后自动继续" (与 ScenePreview 一致)

**给 @backend**: 0 影响 — API 契约不变

**给 @tester**:
e2e 验证点 (T20-12 重做后):
1. /characters 进入后显示 60s 圆形倒计时徽章 + "秒后自动继续"
2. 60s 倒计时归 0 自动触发 confirm-characters 进入 /scenes
3. 用户点"调整 / 重生"时 badge 隐藏 (paused=true), 倒计时暂停
4. DevTools console: 无 "Cannot update CreateProvider while rendering CharacterPreview" 警告
5. ScenePreview 不退化: /scenes 60s 倒计时仍正常 (T20-15 fix 完好)
6. T20-11 不退化: /create → /outline 无 30s 二次载入

**给 @pm**: tsc 0 errors, lint 0 新增 warning, dev server 200, /create HTTP 200

---

## Wave 17 — TASK-T20-FIXBATCH-4 Wave 1 (2026-05-19)

**状态**: ✅ 4 项任务串行完成 (但 T20-12 方案执行有误, Wave 17.5 已重做)

**改动文件 (3)**:
- `frontend/src/components/create/StageC.tsx`
  - **T20-15**: ScenePreview 拆分 setCountdown 反模式 (setInterval 内不再调 onConfirm) — 副作用 (dispatch) 改到独立 useEffect 监听 countdown===0 — 保留
- `frontend/src/app/create/CreateContent.tsx`
  - **T20-11**: hydrate effect 加 in-session skip guard — 保留
- `frontend/src/components/create/StageD.tsx`
  - **DEC-044**: 预览页 "旁白（只读）" → "描述（只读）" — 保留

**给 @ai-ml (T20-21 owner)**:
- StageD 显示字段仍读 `currentShot.narrationSegment`. 你重构后 narration_segment 变短不影响显示
- 如果你新增 `caption` / `description` 字段想替代 narration_segment, 告知 frontend 改一行即可

---

## Wave 16 — RISK-T20-9 P0 useETA backend authoritative (2026-05-18)

**状态**: ✅ 完成。useETA.ts 优先级反转，StageC.tsx 新字段，useETA.test.ts +5 单测

**改动文件 (3)**:
- `frontend/src/hooks/useETA.ts`
  - 新增 `estimatedRemainingSeconds?: number | null` 字段 (top priority, accepts >= 0)
  - backendEtaSec 降级为 legacy fallback (> 0 only, deprecated)
  - 优先级链: estimatedRemainingSeconds >= 0 → backendEtaSec > 0 → STAGE_BUDGET
  - STAGE_BUDGET image_generation=1440 保留作为 last resort
- `frontend/src/components/create/StageC.tsx`
  - useETA 调用新增 `estimatedRemainingSeconds: backendEstimatedSecondsRef.current`
  - 保留 `backendEtaSec: backendEstimatedSecondsRef.current` (legacy)
- `frontend/src/hooks/useETA.test.ts`
  - 追加 5 个 T20-9 单测 (priority / fallback / zero / smoothing / no-jitter)

**给 @backend #1**: 等你确认 `estimated_remaining_seconds` 字段名后，前端无需追加改动。
  当前 `backendEstimatedSecondsRef` 已读 status.estimated_remaining_seconds，
  一旦你的动态算法 (actual_shot_count × 60 / max_concurrent) 上线，
  前端 estimatedRemainingSeconds 自动使用准确值，不再走 hardcoded 1440s。

**给 @tester**: 期望测试场景 (在 Backend #1 的 T20-9 backend 上线后):
  - 19 shots 故事: ETA 显示 ~6 min (380s)，不再显示 ~24 min (1440s) 倒计时
  - image_generation 阶段: ETA 准确对应实际剩余 shots × 生成时间
  - 5 shots 故事: ETA 显示 ~2 min，不再显示 ~24 min

**Wave 15 修复 (保留)**:
  - Stage 4→5 切换: ETA 平滑递减 (不跳变)
  - image_generation 最后阶段: "还需不到 1 分钟" → "即将完成"（不消失）
  - bgm 阶段: 正常显示"正在收尾，请稍候..."

---

## Wave 15 — RISK-T20-2 ETA UX 三修 (2026-05-18)

**状态**: ✅ 完成 (已并入 Wave 16)

---

## Wave 13 — RISK-T19-3 storyboard progress 真值显示 (2026-05-15 17:30)

**状态**: ✅ 完成。StageC.tsx 三处修改，storyboard 阶段不再 reset progress 到 0%

**改动文件 (1)**:
- `frontend/src/components/create/StageC.tsx`
  - L164-171: 新增 `generationProgressRef` (live ref 替代 mount-time `initialProgressRef`)
  - L324-327: 删除失效的 `initialProgressRef` 声明，替换为注释
  - L449-468: text-gen effect START_GENERATION 守卫用 `generationProgressRef.current > 0`
  - L1050-1063: subtitle 用 `resolveSubtitle(currentStage)` 全阶段统一（不再区分 shot-gen vs text-gen）

**根因**: Watcher 把 storyboard_running → "text-gen"，text-gen effect 用 mount-time ref (=0) 判断 → 误发 START_GENERATION → progress reset 0%

**给 @pm**: Wave 13 RISK-T19-3 完成，npm build 0 errors / 20 routes。请代写 TEAM_CHAT 通知。

---

## Wave 12 mini — RISK-T17-7 "后台生成"按钮触发时机扩展 (2026-05-15 16:45)

**状态**: ✅ 完成。StageC.tsx L1148 按钮条件扩展：shot-gen + storyboard 阶段均显示

**改动文件 (1)**:
- `frontend/src/components/create/StageC.tsx`
  - L1144-1163: 按钮显示条件从 `shot-gen only` 扩展为 `shot-gen OR (text-gen + currentStage="storyboard")`

**给 @pm**: Wave 12 mini RISK-T17-7 完成，npm build 0 errors / 20 routes。请代写 TEAM_CHAT 通知。

---

## Wave 12 — RISK-T19-2 + RISK-T17-8 配套 (2026-05-15)

**状态**: ✅ 完成。StageC failed UI 友好化 + 原地重启按钮 + collapsible tech details

**改动文件 (1)**:
- `frontend/src/components/create/StageC.tsx`
  - L5: 新增 `RefreshCw`, `ChevronDown`, `ChevronUp`, `RotateCcw` imports
  - L209-220: `showTechDetails`, `restartLoading`, `restartError` 3个新状态
  - L915-950: `handleRestartFromFailedStage` async handler (POST endpoint)
  - L952-960: `useEffect` 将完整 technical error 记录到 `console.error`
  - L1021: 错误副标题改为"生成遇到问题"(不再显示原始 Pydantic trace)
  - L1157-1220: 新 `isError` UI 块 (友好提示 + 原地重启主按钮 + 返回重试次按钮 + 折叠技术详情)

**给 @backend (Backend #2)**: Frontend 期望:
```
POST /api/projects/{project_id}/chapters/1/restart-from-failed-stage
Body: {} (empty or omit)
Response: { success: true, restarted_from_stage: 4 }
```
接口就绪后自动 work，无需前端改代码。当前如果 endpoint 不存在，前端会显示 restartError 提示用户改用"返回重试"。

**给 @pm**: Wave 12 frontend 完成，npm build 0 errors / 20 routes。请代写 TEAM_CHAT 通知。

---

## RISK-NEW-1 — useETA 消费 actual_elapsed_sec (死字段闭环) (2026-05-14)

**状态**: ✅ 完成。useETA 接口扩展 + sanity check 逻辑 + StageC 两个 poller 解析 + CreateContent 类型 + npm build 0 errors

**改动文件 (3)**:
- `frontend/src/hooks/useETA.ts`
  - `UseETAInput` 新增 `actualElapsedSec?: number | null`
  - hook 函数签名扩展
  - sanity check: `actualElapsedSec >= 1800` → etaText = "正在收尾，请稍候..." (不是数字 ETA)
- `frontend/src/components/create/StageC.tsx`
  - `backendActualElapsedSecRef = useRef<number | null>(null)` 声明
  - text-gen poller: `actual_elapsed_sec` 类型 + 写入 ref
  - shot-gen poller: `actual_elapsed_sec` 类型 + 写入 ref
  - `useETA` 调用新增 `actualElapsedSec: backendActualElapsedSecRef.current`
- `frontend/src/app/create/CreateContent.tsx`
  - `ChapterStatusResp` 新增 `actual_elapsed_sec?: number | null`

**给 @backend**: `actual_elapsed_sec` 字段现在真被前端消费 (11 个消费点)。无需改后端接口，字段已在 chapters.py L367 返回。

**给 @pm**: RISK-NEW-1 完成，`actual_elapsed_sec` 不再是死字段。npm build 0 errors / 20 routes ✅

---

## Wave 11.3 收尾 — StageC.tsx 集成 useETA hook (2026-05-14) — Frontend #2 接力完成

**状态**: ✅ 完成。useETA 真 import + estimatedMinutes IIFE 真替换 + npm build 0 errors

**改动文件 (1)**:
- `frontend/src/components/create/StageC.tsx`
  - L12: `import { useETA } from "@/hooks/useETA"` 新增
  - L269-295: Wave 9 useEffect 简化 (移除 lastEtaSecondsRef reset) + useETA hook 调用替换旧 estimatedMinutes IIFE
  - L988-993: ETA render 改用 `etaText !== null` + `{etaText}`

**给 @backend**: `actual_elapsed_sec` 字段现已被前端消费 (RISK-NEW-1 完成)

---

## Wave 11.2 RISK-T18-G 404 storm 修复 (2026-05-14) — Frontend #1 完成

**状态**: ✅ 完成。

**修改文件 (3)**:
- `frontend/src/lib/api.ts`: 新增 `ApiFetchOptions` interface + `silentStatuses` 参数支持
- `frontend/src/components/create/StageC.tsx`: `charPreviewFetchingRef` guard (4处) + silentStatuses (1处)
- `frontend/src/app/create/CreateContent.tsx`: 2处 hydration call 加 `{ silentStatuses: [400, 404] }`

**给 @backend**:
- Backend #1 可确认 `/chapters/1/story` + `/chapters/1/storyboard` by-design 在早期阶段返 404 — 前端现已静默处理，不再记录到 client-log
- 如 Backend #1 改为 200+empty body，前端现有代码也能正确处理（response JSON 为 {}，chars/scenes 为空数组）

**给 @pm** (TEAM_CHAT paste 内容见下方):
- RISK-T18-G frontend fix 完成，client.log 404 风暴已封堵
- `npm run build` 0 errors / 20 routes ✅
- Frontend #2 可开始接力 Wave 11.3 useETA 集成到 StageC.tsx

---

## Wave 11.3 RISK-T17-5 Frontend ETA hook (2026-05-14) — 独立阶段完成

**状态**: ✅ useETA hook 就绪，等 Frontend #1 完成 Wave 11.2 StageC.tsx 后接力集成

**给 @pm**:
- 新建 `frontend/src/hooks/useETA.ts` (RISK-T17-5 wave 11.3 配套 ETA hook)
- 修了 `CreateContent.tsx` atmosphere 类型错误（pre-existing build error，Wave 10 遗留）
- `npm run build` 0 errors / 20 routes
- StageC.tsx 集成 **等 Frontend #1 完成后接力**（顺序冲突保护）

**给 @backend (Backend #2 ETA contract)**:
- `useETA` hook 已设计好接收 `backendEtaSec: number | null` 参数（来自 `estimated_remaining_seconds` 字段）
- 当 `backendEtaSec > 0` → hook 直接用 backend 值，前端不自己算
- 当 `backendEtaSec = null` → hook 用 stage-based budget fallback（稳定，不跳变）
- Backend #2 改好 `job_manager.py` ETA 算法后，已有字段 `estimated_remaining_seconds` 就自动 work

**给 @frontend (Frontend #1)**:
- StageC.tsx Wave 11.2 改完后通知 PM，PM 再通知 Frontend #2（本 agent）接力集成 useETA
- 集成位置: StageC.tsx 的 `estimatedMinutes` 计算 IIFE + `backendEstimatedSecondsRef` + `lastEtaSecondsRef`
- 接力后替换为: `const { etaText } = useETA({ stage: currentStage, progress: state.generationProgress, backendEtaSec: backendEstimatedSecondsRef.current })`

**可用 hook 接口**:
```typescript
import { useETA } from "@/hooks/useETA";
const { etaText, etaSeconds } = useETA({
  stage: currentStage,           // string | null
  progress: state.generationProgress, // 0-100
  backendEtaSec: backendEstimatedSecondsRef.current, // number | null
});
// etaText: "预计还需约 8 分钟" | null
// etaSeconds: number | null (for testing)
```

---

## Wave 10 Phase 1B frontend 完成 (2026-05-14) — test16 RISK-T16-4/-7/-9/-3 闭环

**给 @backend (Wave 10 Phase 1B 配合确认)** ⭐⭐⭐⭐⭐:

RISK-T16-4 的完整修复需要前端 + 后端都到位:

- **前端已完成**: `handleConfirmScenes` 改为 full spread — POST `modified_scenes` 现在携带 `action_beats` + `narration` + `location_id` 等所有 Stage 3 字段（不再只有 4 字段）
- **后端 Phase 1A (B58 修复) 期望**: `POST /projects/{id}/confirm-scenes` 应 merge（不是完全替换）`chapter.scenes_json`，保留 Stage 3 原始字段
- 如后端 Phase 1A 已完成，前端 + 后端双保险，T16-4 完全关闭
- 如后端 Phase 1A 未完成，前端 full spread 也能单独解决大部分情况（因为前端发送的 payload 本身已完整）

**关键变化**:
- `PreviewScene` 类型现在有 index signature `[key: string]: unknown`，允许任意 LLM 字段透传
- Watcher `isSceneReview` 分支：现在会 fetch `/chapters/1/story` 并 dispatch 完整 scenes（含 action_beats）
- `ChapterStoryResp.scenes` 类型扩展，含所有 Stage 3 字段

**给 @pm**:
- 改了 4 文件：types/create.ts / StageC.tsx / CreateContent.tsx / StageD.tsx，全部 frontend 域
- 0 越权 / npm run build 不需要（hot reload 自动生效）
- 关键 grep 验收见 current.md 末尾验证清单
- 请追加 TEAM_CHAT 通知 + PENDING T16-4/-7/-9/-3 标 ✅

**给 @tester (test17 验收)**:
1. **T16-4 e2e**: 跑完整流程，场景确认后 Stage 4 应正常生成 shots（不再空白）；DevTools Network 查看 confirm-scenes POST body 应含 `action_beats` 字段
2. **T16-7 e2e**: 模拟 pipeline 失败（shots.length=0）→ 应显示错误 UI "故事生成遇到问题" + 两个按钮（不再空白屏）
3. **T16-9 UX**: /scenes 页面轮播提示第 2 条应为"场景已生成，请确认是否符合预期"（不再"可以修改每个场景的氛围描述"）
4. **T16-3 UX**: 断网（DevTools → Network → Offline）→ 应显示 amber 横幅（不弹红色错误页）；恢复网络 → amber 横幅消失，继续正常 polling

**给 @devops**:
- 4 文件改动均为 .tsx，Next.js dev hot reload 自动生效
- 如需重启 frontend：`kill $(lsof -ti:3000)` + `cd frontend && npm run dev`（不需要 npm run build）
- 无 backend 联动需求（合同已在 backend Phase 1A 处理）

---

## TASK-WAVE9-P2-FRONTEND-STATE-DERIVATION 完成 (2026-05-13 23:xx) — DEC-030 frontend 闭环

**给 @backend (Wave 9 P2 Backend authoritative status 落地确认)** ⭐⭐⭐⭐⭐:

Frontend 现在已经全面读 Wave 9 P2 backend status 新字段（ui_phase + hydrate_hints + characters_confirmed + scenes_confirmed + failed_shot_count + partial_failure）。具体路径：

1. **createUrl.reconcileBackendVsUrl**: 新增 `uiPhase` 参数，优先映射；老 backend（无字段）走 legacy heuristic
2. **CreateContent hydrate 路径**: `status.characters_confirmed` / `status.scenes_confirmed` 优先于 `project.characters_confirmed` / `project.scenes_confirmed`
3. **CreateContent Watcher**: 5s tick 内派生 generationSubPhase from status.ui_phase（防止 PM 直 POST 绕过 frontend 时 subPhase 卡死）
4. **StageC pollers (text-gen + shot-gen + checkpoint watcher)**: 三处 status fetch 全部加新字段类型 + completed 检测多源化 + char_review 触发 char-preview

**关键变化**:
- Backend 改 ui_phase=char_review → 5s 内 frontend Watcher dispatch 切 subPhase=char-preview + URL 跳 /characters
- Backend 改 ui_phase=shot_generating → 5s 内 frontend subPhase=shot-gen + URL 跳 /generating + "后台生成" 按钮显示
- Backend 改 ui_phase=completed → 5s 内 frontend 跳 /preview（或同 tick StageC poller 立即跳）

**对 hydrate_hints 的当前使用**: 仅类型化（接收并丢弃，不主动调用 endpoint），因为现有 parallel fetch（status + storyboard + story + bgm）已经覆盖所有阶段，hint 主要是文档化用途。如果未来要做 hydrate URL 精简化，hints 字段已就位。

**给 @pm**:
- 改了 3 文件：createUrl.ts / CreateContent.tsx / StageC.tsx，全部 frontend 域，未碰 backend/AI-ML/DevOps
- 0 越权 / npm run build 0 errors / 20 routes / pre-existing warnings only
- 7 维度审查 checklist：见 frontend-progress/current.md 末尾
- Wave 9 P2 frontend 闭环完成，PM 可启动审查 + e2e 跑 test16
- 请追加 TEAM_CHAT 通知 + PENDING T15-3/-7/-8 标 frontend 端也 ✅

**给 @tester (test16 验收)**:
1. 验收 ui_phase 派生：跑全流程，DevTools console 查看 `[createUrl] Wave9: derived from uiPhase=...` log 每 5s 出现一次
2. 验收 RISK-T15-7 ETA reset：进入 image_generation 阶段时 backend ETA=350s，frontend 应显示 ~6 min（不再压成 1 min）；console log `[StageC] Wave9: stage transition ... — resetting lastEtaSecondsRef`
3. 验收 RISK-T15-8 subPhase 派生：PM 直接 POST /confirm-scenes（绕过 frontend）→ 5s 内 console log `[Watcher] Wave9: ui_phase=shot_generating → derived subPhase=shot-gen` + "后台生成" 按钮显示
4. 验收 RISK-T15-3 顺解：在 scene_review 阶段刷新页面 → frontend hydrate /story 应返 scenes 数据，/scenes checkpoint 正常显示
5. 回归：Wave 7 RISK-T14-8 仍工作（scenes confirmed + URL=/scenes + storyboard stage → force /generating）
6. 回归：RISK-T15-1 + T15-2 仍工作（POST_CHAR_STAGES 不含 screenplay/storyboard + "后台生成" 仅 shot-gen 显示）

**给 @devops**:
- npm build 0 errors，可以 rsync 部署
- 无 backend 联动需求（contract 已在 Wave 9 P2 Backend 完成）
- 等 PM 审查通过 + Founder e2e 后再部署

---

## RISK-T15-11 window.onerror 增强完成 (2026-05-13)

**layout.tsx** window.onerror + resource/media error 区分修复:
- 新增 `window.onerror` handler: JS 错误带完整 source/line/col/stack
- 改进 `addEventListener('error')`: 有 e.error 则跳过（已由 onerror 处理）；无 e.error → 媒体/resource 错误 → 提取 tagName/src/MediaError.code
- 改进 `unhandledrejection`: reason 是 Event 对象时提取 type/isTrusted/targetSrc/MediaError.code
- PM e2e: DevTools `throw new Error("test")` → client.log level=uncaught + stack 非空

---

## test15 紧急双修完成 (2026-05-13)

**RISK-T15-2 (P0 CRITICAL)**: `createUrl.ts` POST_CHAR_STAGES 移除 screenplay+storyboard。
- 根因：reconcile() 把 screenplay/storyboard 判为"已过 scenes checkpoint"，永远把用户从 /scenes 踢到 /generating
- 修复后：storyboard 阶段时 POST_CHAR_STAGES.has(backendStage) === false → /scenes 页面不再被踢走 → scenes_ready=true 时 watcher 正常跳 /scenes

**RISK-T15-1 (P0 UX)**: `StageC.tsx` 3 处文案+按钮修正
- "后台生成"按钮仅 shot-gen 阶段显示（text-gen 分支删除）
- 早期 stage subtitle 改为"请稍候"（原"可以选择后台生成"会误导用户）

**改动文件 (2)**:
- `frontend/src/lib/createUrl.ts` L118-131
- `frontend/src/components/create/StageC.tsx` L106-115, L120, L940-950

---

## TASK-WAVE7-FRONTEND 6 任务完成 (2026-05-13)

**修复了 1 P0 + 4 P1 + 1 P3**:
- RISK-T14-8 (P0): CreateContent watcher 加 MID_PIPELINE_STAGES → storyboard/image_* + scenes_confirmed + URL=/scenes → force /generating
- RISK-T14-6 (P1): StageC handleConfirmCharacters 加 router.replace('/scenes')，无需等 watcher
- RISK-T14-12 (P1): "后台生成"按钮扩展到 text-gen；Notification API 权限请求；dashboard 30s polling + ✨ badge + Browser Notification
- RISK-T14-3 (P3): createUrl.ts 两个相同 Set 合并为模块级 POST_CHAR_STAGES
- RISK-T14-2 (P1): 所有 user.X 改为 user?.X（4 文件）
- RISK-T14-13-frontend (P1): StageB confirm-outline 捕获 inconsistency_warnings，黄色非阻塞 banner

**改动文件 (10)**:
- `frontend/src/app/create/CreateContent.tsx`
- `frontend/src/components/create/StageC.tsx`
- `frontend/src/components/create/StageB.tsx`
- `frontend/src/app/dashboard/DashboardContent.tsx`
- `frontend/src/components/dashboard/StoryGrid.tsx`
- `frontend/src/components/dashboard/StoryCard.tsx`
- `frontend/src/lib/createUrl.ts`
- `frontend/src/contexts/AuthContext.tsx`
- `frontend/src/app/settings/SettingsContent.tsx`
- `frontend/src/components/dashboard/UserMenu.tsx`

**给 @backend**:
- RISK-T14-13: 前端期望 `POST /projects/{id}/confirm-outline` 响应体可含 `inconsistency_warnings?: Array<{type, message, affected_field?}>` 字段。有此字段且非空时前端显示警告 banner，用户确认后再单独调 start-generation。如 backend 暂不返回此字段，前端逻辑正常（无 warnings 直接走原流程）。
- RISK-T14-12: Dashboard 每 30s 自动调 GET /projects/ 轮询。之前没有 dashboard 轮询，现在会有额外流量，低频可接受。

**给 @tester (Wave 7 验收)**:
1. RISK-T14-8: backend stage='storyboard'/'image_preparation'/'image_generation'/'bgm' + scenes_confirmed=true + URL=/scenes → 5s 内自动跳 /generating
2. RISK-T14-6: 角色预览页点"确认角色，继续" → URL 立即变为 /scenes（不再等 5s watcher）
3. RISK-T14-12 a: /generating 页 text-gen 阶段（非 error）显示"后台生成，去做别的"按钮；点击弹浏览器 Notification 权限对话框
4. RISK-T14-12 b: 点"后台生成"进 dashboard；另一个 tab 里后台生成完成（shot_count 从 0 变 >0）→ 30s 内 dashboard 刷新 + 对应卡片出现 "✨ 新故事完成" badge
5. RISK-T14-2: 模拟 backend 5xx（停 mysql）刷新 dashboard/settings → 不崩溃（user?.X 安全）
6. RISK-T14-13: 后端 confirm-outline 返回含 inconsistency_warnings 的响应 → StageB 显示黄色 banner，列出 warning messages；点"知悉并继续"正常进入生成流程；点"返回修改"关闭 banner 回到编辑

**给 @pm**: TASK-WAVE7-FRONTEND 6 件全完成，npm run build 0 errors / 20 routes。需 kill+restart frontend。

---

## TASK-T13-FRONTEND-ROUTING-FAMILY 8 任务完成 (2026-05-12 ~22:50)

**修复了 7 P0 + 1 P1 + 1 P0 (C1)**:
- BUG-T13-REACT-ANTIPATTERN-STAGEC (P0)
- BUG-T13-CHARACTER-PAGE-NO-AUTO-JUMP (P0)
- BUG-T13-URL-PINGPONG-CHARACTER-READY-V2 (P0)
- BUG-T13-COMPLETED-NO-AUTO-JUMP (P0)
- BUG-T13-AUTH-FALSE-LOGOUT-ON-500 (P0)
- BUG-T13-PREVIEW-DIRECT-LOAD-SLOW (P0)
- DASHBOARD-PERF-N1 (P1) — 验证已 OK + 加 BGM 并行
- C1-frontend (P0) — 改调 project-level confirm-scenes alias

**改动文件 (4)**:
- `frontend/src/contexts/AuthContext.tsx` — tokenInvalid state + isLoggedIn 改算法 + 5xx 背景重试
- `frontend/src/app/create/CreateContent.tsx` — 顶层 status watcher useEffect (5s) + BGM 并行 hydrate
- `frontend/src/components/create/StageC.tsx` — useCallback 稳定 props + console 移到 useEffect + portraitMap + ref-based closure 修复 + handleConfirmScenes 改 project-level alias
- `frontend/src/lib/createUrl.ts` — reconcile 加 backendPastCharStage guard 防 ping-pong

**给 @backend**:
- C1-frontend 已用新 alias `POST /projects/{uuid}/confirm-scenes`（不再调 chapter-level）
- 顶层 watcher 5s 间隔轮询 `/chapters/1/status`（注意有额外流量但不大）
- AuthContext: 5xx 时 token 仍保留，前端会指数退避重试 `/auth/me`（2/4/8/16/30s）

**给 @devops**:
- npm build 成功（0 errors / 20 routes）
- 部署需 kill+restart frontend（PID/build dir 改动）
- 注意不影响后端任何契约/路由

**给 @tester (Founder e2e test14)**:
- 关键验收：
  1. 登录态正常时，进 /generating，backend 到 character_ready → 5s 内自动跳 /characters
  2. 同上，到 status='completed' → 5s 内自动跳 /preview
  3. 模拟 backend 5xx（如临时停 mysql）刷新页面，frontend 不被踢回 /login，loading 后 backend 恢复自动加载
  4. 直接打开 /create/{uuid}/preview，5 秒内显示成品（不是几分钟）
  5. CharacterPreview 渲染时 DevTools Console 无 React "setState during render" warning
  6. CharacterPreview portrait 仍正常显示（portraitMap 重构）
  7. 用户点"确认场景，继续" → POST 走 `/projects/{uuid}/confirm-scenes`（不带 chapter）

**风险**：
- StageC.tsx CharacterPreview 改了 portrait 渲染逻辑（portraitMap），需重点回归
- AuthContext 改了 isLoggedIn 计算，需测登录/登出/401/5xx 4 路径
- 顶层 watcher 5s 间隔轮询是新增行为（之前只有 StageC 内部 2s）

---

## TASK-T13-FRONTEND-A2-URL-FIX — Console Proxy URL 修复 (2026-05-12)

**给 @backend**:
- POST 目标已改为环境变量驱动：dev=`http://localhost:8000/api/_client_log`，生产=`https://prefaceai.mov/api/_client_log`
- 之前 hardcoded `localhost` 导致生产 CORS 失败，现已修复
- backend A2-backend 端点（POST /api/_client_log）已就绪后可 verify: `console.error('test')` → `tail logs/client.log`

**给 @devops**:
- 生产 Docker build 时 `.env.production` 已包含 `NEXT_PUBLIC_API_URL=https://prefaceai.mov`
- `next build` 会自动读 `.env.production`，无需额外 build arg
- `.env.local` 已创建（gitignore，本地 dev 用），`.env.production` 安全入仓库

**给 @tester**:
- 验收方法: 本地 dev 环境，浏览器 console 执行 `console.error('urlfix-test')` → `tail -1 logs/client.log` 应看到 level=error, args 含 "urlfix-test"
- 生产验收: 部署后访问产品域名，触发任意前端错误 → VPS `tail logs/client.log` 验证

---

## A2-frontend — Console Proxy 注入完成 (2026-05-12 16:37 — URL 已修复)

**给 @backend**:
- `POST http://localhost:8000/api/_client_log` 是前端 POST 目标。Body 格式:
```json
{
  "level": "error" | "warn" | "uncaught" | "promise-reject" | "network",
  "ts": "ISO 8601",
  "args": ["string..."],
  "url": "location.href",
  "source": "filename (uncaught/network)",
  "line": 123,    // uncaught only
  "col": 45,      // uncaught only
  "stack": "stack trace (uncaught/promise-reject)"
}
```
- endpoint 就绪后 verify: `console.error('test')` → `tail logs/client.log` 看到记录
- **fetch 已重写**：所有 `fetch()` 调用都被 wrapped；防无限循环检测 `/_client_log` 路径绕过

**给 @ai-ml / @tester / @pm**:
- 批次 1 完成后 PM 应 `tail -F logs/client.log` 拉起 monitor，实时看所有浏览器 console errors + warnings + unhandled promise rejections + 400+ 网络失败
- monitor pattern: `tail -F xuhua_story/logs/client.log | grep --line-buffered -E "error|warn|uncaught|promise-reject|network"`

**给 B1 frontend agent (Opus xhigh，批次 2 spawn 后)**:
- A2-frontend 已完成，console proxy 就绪
- 修 React anti-pattern (StageC.tsx:1181 setState in render) 时**先看 `logs/client.log`** 拿真实 error stack trace 定位根因
- 修 7 P0 路由家族时同样可以靠 client log 验证修复效果

**风险/注意**:
1. `dangerouslySetInnerHTML` 在 Next.js App Router Server Component layout 注入，hydration 时执行，时机正确（在 React/Next 初始化之前），能捕获 hydration warnings
2. fetch 重写在 IIFE 里，只在浏览器端运行，SSR 不受影响
3. Backend endpoint 不在线时，fetch 失败 silent catch，不影响前端任何功能
4. `window.fetch` wrap 顺序：`<script>` 在 `<body>` 顶部，AuthProvider 之前，确保第一个 fetch 之前已就位

---

---

## Wave 6 — 3 个 Bug 修复（2026-05-11）

**给 @backend**:
- Wave 6 前端已 ready，等后端联调：
  1. `GET /projects/{uuid}` 需包含 `scenes_confirmed: bool` 字段（已加到 `ProjectDetailResp` 类型）
  2. `POST /api/projects/{uuid}/chapters/1/confirm-scenes` 端点（参照 confirm-characters，接受 `{ modified_scenes }` body）
- 前端 hydrate 现已读 `project.scenes_confirmed === true`（不再用 ADVANCED_STAGES heuristic）
- 前端 handleConfirmScenes 现在调真实 API（失败静默继续，不阻塞用户）

**给 @tester (Wave 6 验收)**:
1. BUG-SCENES-CONFIRM-MISSING: 新 test → Stage 2 后看到 /characters → 确认 → Stage 3 完成后真停留 /scenes 页面（60s 倒计时）
2. BUG-URL-PINGPONG: 确认角色后 URL 不再反复跳 /characters → /scenes → /generating → /characters
3. BUG-PROGRESS-LIST-SKIP-SHOT: 跑新 test，18 shots UI 列表显示 1~18 全部条目，不跳号
4. ScenePreview 确认按钮文案变"确认场景，继续"
5. `npm run build` 0 errors（已验证）

**给 @pm**: Wave 6 前端 3 件全完成 + Wave 5 progress 补完。npm run build 0 errors, 20 routes。待 Backend 联调 confirm-scenes 端点 + scenes_confirmed 字段。

---

---

## B33 frontend — 情绪基调移到 Stage A (2026-05-09)

**给 @backend**:
- POST `/projects/` 新增 `user_selected_mood` 字段（中文字符串或 null）。Backend 需加到 `ProjectCreate` schema，保存到 `projects.user_selected_mood` 列，GET `/projects/{id}` 返回此字段。
- POST `/projects/{id}/confirm-outline` body 里的 `outline.user_selected_mood` 也带来了此值（与 Stage A 一致），Backend 可一并保存到 `confirmed_outline_json.user_selected_mood`（已有字段，复用即可）。
- **不需要 backend 完成即可验证前端改动** — 前端发出 user_selected_mood，backend 如果暂不支持直接忽略此字段也不会报错。

**给 @tester**:
- 验收点 1：新建项目 Stage A 页面有 8 个情绪基调 chip（温馨/紧张/幽默/感人/治愈/热血/悬疑/浪漫），可单选，再次点击取消。
- 验收点 2：POST /projects/ Network Tab 请求 body 含 `"user_selected_mood": "悬疑"` 等（或 null 若未选）。
- 验收点 3：StageB 大纲编辑页不再有"情绪基调"区域。

**给 @pm**: B33 frontend 部分完成，npm run build 20 routes 0 errors。需 kill+restart frontend（新 chunk 含 user_selected_mood 字段）。Backend B33 部分（schema + DB 列 + 返回字段）待 @backend 实施。

---

## P0 全维度修复: B26/B27/B28 + 衍生问题 (2026-05-09)

**已修复 (4 bugs)**:
- **B26**: `StageC.tsx` CharacterPreview 新增 `resolvePortraitUrl()` component-level static fallback + silhouette visibility 增强（dark theme 可见）+ `onError` handler
- **B27**: `createUrl.ts` `reconcileBackendVsUrl()` 新增 `POST_CHAR_STAGES` — URL=/scenes 且 backend 已过 character_ready 时重定向 /generating
- **B28**: `CreateContent.tsx` PROJECT_FETCH_TIMEOUT_MS: 30s → 120s + HYDRATE_CHAPTER_TIMEOUT_MS: 25s → 90s + hydrateSlowWarning 15s 提示 + 更友好 timeout 错误文案
- **衍生1 (spinner loop)**: `CreateContent.tsx` 新增 `isOurOwnPush` guard — state→URL push 不再触发 re-hydration
- **衍生3 (ETA 缺失)**: `StageC.tsx` ETA `progress < 10` 时按 stage 给默认值 (story_generation:8min, character_design:7min)

**未修 (已标注原因)**:
- 衍生2 (progress 倒退 F5): 需 StageC refactor，放下期

**验收**: npm run build 0 errors (20 routes)

**给 @devops**: 需 kill+restart frontend（杀掉当前 next server + npm run dev）
**给 @tester**: 验收重点 — 
  1. 角色预览页 portrait 应可见（非空白/纯黑剪影）
  2. F5 刷新到 /scenes 且 backend 在 screenplay stage → 应自动跳 /generating（而非卡着看 spinner）
  3. Stage 3 LLM 254s 运行期间 frontend 不应误报 "加载项目失败"，15s 后应出现慢服务提示
  4. ETA 在 story_generation/character_design 阶段应显示（约 7-8 分钟）

---

## Logging 加固 — B26/B27/B28 诊断准备 (2026-05-09)

**任务**: 不修 bug，只加结构化 console.log，让下次 frontend bug 诊断 5x 更快

**修改文件 (2)**:
- `frontend/src/components/create/StageC.tsx`
- `frontend/src/app/create/CreateContent.tsx`

**Log 覆盖维度 (10 条 log)**:

| 前缀 | 位置 | 内容 |
|------|------|------|
| `[StageC] subPhase changed:` | StageC useEffect | subPhase + currentStage + URL，每次切换打印 |
| `[D.21] character_ready:` | StageC character_ready handler | chapterCharacters 数量 + portraitByName keys |
| `[D.21] resolvePortraitForCharacter` | StageC character_ready per-char | charId + name，进入 fallback chain |
| `[D.21] step 1/2/3 + FINAL` | StageC per-char | API url / static url / outline url / final 决定值 |
| `[D.21][hydrate] portraitById/ByName keys:` | CreateContent.tsx | hydrate 路径 portrait lookup map |
| `[D.21][hydrate] resolvePortraitForCharacter` | CreateContent.tsx per-char | 同 StageC 版本，hydrate 路径 |
| `[hydrate] project fetch start` | CreateContent.tsx Step 1 | projectUuid + timeout=30000ms |
| `[hydrate] project fetch result` | CreateContent.tsx Step 1 | 耗时 ms + OK vs TIMEOUT/NULL |
| `[hydrate] chapter fetch start/done` | CreateContent.tsx Step 2 | parallel 3 fetch 耗时 + status.status/stage/progress + storyboard/story char count |
| `[Router] reconcile decision:` | CreateContent.tsx reconcile | urlStage/backendStatus/stage/reconciledStage/reason |
| `[Router] hydrate redirect/no redirect` | CreateContent.tsx hydration effect | from/to/newUrl 或 "no redirect needed" |

**验收**: npm run build 0 errors (20 routes, warnings pre-existing only)
**@devops**: 需 kill+restart frontend 让新 build 生效
**@tester**: 验收 B26 时开 DevTools Console → 过滤 `[D.21]` 查看 portrait resolution 过程；过滤 `[Router]` 查看路由决策；过滤 `[hydrate]` 查看 fetch 耗时

---

---

## D.25 B24 TASK-BGM-BUTTON-COPY (2026-05-08)

- BGM 按钮文案已更新: "换一首" → "换种风格"；"重新生成" → "再来一首"
- 两个按钮均加了 `title` tooltip，鼠标悬停即可看到语义解释
- credits 说明文字改为加粗区分版，用户可秒懂价差
- **@backend**: 无需配合，纯 UI 改动
- **@tester**: 验收点 — BGM 区域两个按钮显示"换种风格"和"再来一首"，hover 显示 tooltip，credits 文字正确

---

## D.24 B21 TASK-REGENERATE-FRONTEND-CACHE-BUST (2026-05-08)

- StageD.tsx 新增 `bustCache(url)` 工具函数，handleRegenerate + handleAdjust 均已调用
- 向后兼容: backend 返回带 `?v=` 的 URL 直接使用；不带则前端追加 `?v=Date.now()`
- **@backend B16**: 你的 regenerate endpoint 如果在返回 imageUrl 时已加 `?v={timestamp}`，前端会直接用，不会二次追加版本号
- **@devops**: 需重启 frontend（kill next server + npm run dev）让新 build 生效
- **@tester**: 验收点 — 重新生成镜头后，浏览器 Network Tab 应发起新 HTTP 请求（不应是 304 from cache）

---

## D.23 TASK-AUTO-ROUTE-PREVIEW (2026-05-08)

- **修复**: pipeline 完成后自动跳 /preview（B10 路由 bug）
- **3 路径全覆盖**: (1) text-gen 轮询 completed → finalizeAndGoToPreview；(2) char/scene-preview 新增 checkpoint watcher 每 5s 检测；(3) dashboard 进入 completed 项目 → handleContinue 路由到 /create/{uuid}/outline 触发 hydration
- **核心代码**: `StageC.tsx` finalizeAndGoToPreview 提升为 useCallback + D.23 checkpoint watcher effect；`DashboardContent.tsx` handleContinue 路由修正
- **不变**: D.21 D.22 修复、lib/url.ts、lib/createUrl.ts
- **@devops**: 需重启 frontend（kill next server + npm run dev）
- **@tester**: 验收点 — pipeline 完成时 URL 自动跳到 /create/{uuid}/preview，不需要手动改 URL；从 dashboard 点已完成项目"继续"也直接进 /preview

---

## D.22 TASK-FRONTEND-STALE-COPY (2026-05-08)

- **修复**: `StageC.tsx` 副文案从固定字符串 `FIXED_TIP` 改为 `getProgressTip(stage, subPhase)` 动态函数
- **Stage mapping**: story_generation/character_design → 可可+确认角色提示；screenplay/storyboard → 剧本准备好；image_preparation/image_generation → 画面生成中；bgm/music → 最后一步；character_ready → 不显示
- **显示条件**: `subPhase === "text-gen" || subPhase === "shot-gen"`，内容由 currentStage 决定（过了角色确认就不再出现"确认角色"字眼）
- **不变**: D.21 修复、禁改文件（lib/url.ts / lib/createUrl.ts）
- **@devops**: 需重启 frontend（kill next server + npm run dev 或 restart）
- **@tester**: 验收点 — 在 storyboard 阶段（~65%）不应显示"确认角色"字眼；在 image_generation 阶段显示"画面正在生成"；bgm 阶段显示"最后一步"

---

## D.21 Hotfix (2026-05-08)

- `/chapters/1/story` 400 (status=pending/generating_story) 在 StageC.tsx character_ready handler + hydrateProjectFromBackend 里均已正确 catch+warn（不再静默失败）
- 新增 `buildStaticPortraitUrl(charId)` fallback：`/static/outputs/{projectUuid}/character_refs/{char_id}_portrait.png`，当 /story API 不可用时直接读 static 文件
- 新增 `withTimeout(promise, ms, fallback)` helper：project fetch 10s / chapter fetches 8s / bgm 4s 超时保护，避免 backend DB 慢时永久 spinner
- portrait_url fallback chain: API data → static URL → outline data → null
- **不变**: D.19/D.20 outline 修复链路；lib/url.ts、lib/createUrl.ts 禁改文件
- **@devops**: 需重启 frontend（kill PID 15811 + npm run dev 或重启 next server）
- **@tester**: 验收点 — character preview 显示真实 portrait 图（不应是全剪影）；切换阶段 spinner 不超过 15s（timeout fallback 后自动显示 generating 阶段）

---

> 更新时间: 2026-04-28 16:30

---

## TASK-T6-FIXBATCH Wave 2 Agent E R7-1 完成 (2026-04-28 16:30)

### 对其他 Agent 的影响

- **@backend**: 无新契约依赖。前端已对接 `GET /api/projects/` 新增 4 字段（cover_image_url / shot_count / mood / ISO 时间）。
- **@tester (T7)**: 新增验收点：
  1. Dashboard 列表卡片显示真封面图（非 logo 占位）
  2. 卡片 shot 数徽章显示真实数值（非 "0 shots"）
  3. 卡片时间显示北京时区（UTC+8），不再 -8h 错位
  4. Dashboard stats "总画面数" 显示真实累加值（非 0）
  5. 有 mood 的故事卡片在风格标签旁显示 mood 文字
- **@pm**: Wave 2 Agent E R7-1 frontend 完成，npm build 21 routes 0 errors。R7-1 整体（D backend + E frontend）均完成。
- **@devops**: 部署时无新 env / 无新 build flag，可直接 rsync + rebuild。

### 已修复文件

- `frontend/src/contexts/AuthContext.tsx` — `ApiProject` 接口 + `mapProject()` 完整读 4 字段
- `frontend/src/types/create.ts` — `StoryCard.mood: string | null`
- `frontend/src/components/dashboard/StoryCard.tsx` — mood badge 条件渲染
- `frontend/src/lib/mock-data.ts` — mock stories 补 mood

---

## TASK-T6-FIXBATCH Wave 1.2 UX-16 完成 (2026-04-28 15:06)

### 对其他 Agent 的影响

- **@backend**: 无新契约依赖。hydrate 用的是 5 个**已有** endpoint（GET /projects/{id}, /chapters/1/status, /chapters/1/storyboard, /chapters/1/story, /chapters/1/bgm）。
- **@tester (Wave 3 T7)**: 新增 P0-4 验收路径：
  1. **F5 刷新**: 任意 stage `/create/{uuid}/{stage}` 刷新后正确还原（不丢 state）
  2. **浏览器后退**: 在 /preview 后退应**自动 redirect 回 /preview**（completion guard 防止用户回到 stale generating）；在 /generating 后退到 /outline 回到 StageB
  3. **复制链接打开**: 同账号复制 `/create/{uuid}/preview` 到新 tab 应直接显示 StageD 预览
  4. **跨 stage 切换**: /create → /outline → /generating → /characters → /scenes → /generating → /preview → /delivery，URL 实时更新，浏览器历史每 stage 1 条
  5. **invalid stage**: `/create/{uuid}/typo-stage` 返回 404（isUrlStage 校验生效）
- **@pm**: Wave 1.2 Agent C (Opus 4.7) 完成，npm build 21 routes 0 errors。可启动 Wave 2（Agent D 后端 dashboard 字段 + Agent F ARCH-1）。
- **@devops**: 部署时注意新增了一条 dynamic route，无新 env / 无新 build flag 要求。

### 新 URL 结构

```
/create                                  → Stage A（输入页，未创建项目）
/create/[projectUuid]/outline            → Stage B（确认大纲）
/create/[projectUuid]/characters         → StageC sub-phase char-preview（角色确认）
/create/[projectUuid]/scenes             → StageC sub-phase scene-preview（场景确认）
/create/[projectUuid]/generating         → StageC text-gen / shot-gen（等待页）
/create/[projectUuid]/preview            → Stage D（成片预览）
/create/[projectUuid]/delivery           → Stage E（交付选项）
```

### 新增共享工具

- **`frontend/src/lib/createUrl.ts`** — URL ↔ state 工具
  - `UrlStage` type + `URL_STAGES` 枚举
  - `isUrlStage(value)` 类型守卫
  - `deriveUrlStageFromState(currentStage, subPhase)` — state → URL
  - `stateFromUrlStage(urlStage)` — URL → state
  - `reconcileBackendVsUrl({ urlStage, backendStatus, backendStage, charactersConfirmed, scenesConfirmed })` — 决策树
  - `buildCreateUrl(projectUuid, stage)` — 拼 URL

### 新 reducer action

- **`HYDRATE_FROM_BACKEND`** — 一次性还原 CreateState（merge 到 initialState 保 default，bgmPlayer 单独保留），用于 URL deep link / F5 刷新

### 反馈环避免（关键）

state ↔ URL 同步采用 3 层防护：
1. `lastPushedUrlRef` echo guard
2. `derivedFromState === urlStage` 短路
3. completion guard（generationStatus === "complete" 时不允许后退到 generating/characters/scenes/outline）

---

## TASK-T6-FIXBATCH Wave 1.1 Agent B 完成 (2026-04-28 14:30)

### 对其他 Agent 的影响

- **@backend Agent A**: F-2 前端已接好 `/projects/{id}/characters/{charId}/regenerate-portrait` 端点调用。P1-3 端点 ready 后 F-2 自动生效，无需前端再改。
- **@backend Agent A**: P0-3 character_ready handler 已改为 fetch `/projects/{projectId}/chapters/1/story`（API `storyResp.characters`），portrait_url 从 chapter.characters_json 读取。P1-5 "portrait 全成才设 character_ready" 完成后，前端可正确显示所有 portrait。
- **@tester Agent G (T7)**: 关键验收点：
  1. StageD 21 shots 全可见 + 配乐可播（P0-1，R7-12）
  2. StageC character_ready 后 1-2s 内 portrait 显示（P0-3，F-1）
  3. Stage E 显示 outline.summary 而非 original_idea（P1-6）
  4. 100% 后 carousel tip 停止旋转（P2-4）
  5. 完成态副标题不再冲突（P2-4）
  6. 角色卡刷新按钮（F-2）— 依赖 Agent A P1-3 端点
- **@pm**: 前端 Wave 1.1 Agent B 全部完成，npm build 0 errors。F-2 功能等待 Agent A P1-3 端点上线后自动生效。

### 新增共享工具

- **`frontend/src/lib/url.ts`** — `toAbsoluteUrl(url)` 共享函数
  - 将 `/static/...` 转为 `http://127.0.0.1:8000/static/...`
  - 自动 strip 引号（`"url"` → `url`，P3-4 fix）
  - 已引用：StageD / BgmPlayer / StageC / StoryDetailContent

### 关键 API 依赖（已确认）

- `GET /api/projects/{id}/chapters/1/story` — `storyResp.characters[].portrait_url`（P0-3 用）
- `POST /api/projects/{id}/characters/{charId}/regenerate-portrait` — `{ portrait_url, success }`（F-2 用，等 Agent A P1-3）
- STAGE_LABEL map 已加：`character_design`、`image_preparation`（等 Agent A P1-1 推这两个 stage）

---

## TASK-BUG-FIX-BATCH-1 Route C 完成 (2026-04-23 16:10)

### 对其他 Agent 的影响

- **@backend**: 我提出 2 个后端改进建议（非本次任务必须，但体验会更好）:
  1. `job_manager.py:302` 任务完成时 stage 写死 `"story_generation"` 覆盖了实际最后的 stage。建议保留 `image_generation` 或新增 `"completed"`。前端 resolvePhaseTitle 在 completed 状态已跳转，影响有限，但 completion 前最后一 tick 会闪烁。
  2. `pipeline_orchestrator.py:687-730` Stage 6 BGM 生成期间无 `progress_callback`，前端卡在 90% 几分钟。建议 BGM 开始加 `await progress_callback("bgm", 95, "正在谱曲...")`。

- **@tester**: 测试 FE-5 修复是否生效 — 完整跑 Pipeline 到 completed，前端应该 <= 2s 内跳转 StageD 预览。可用浏览器 DevTools Console 查看 `[FE-5] /generation-result roundtrip` 时长。

- **@pm**: 决定是否把 2 个 backend 改进建议（上面）派发给 @backend。

### 前端关键改动

- **FE-5 核心 fix**: `StageC.tsx:312` 在 shot-gen useEffect 入口显式 `completedRef.current = false`；`StageC.tsx:390` 完成触发器从 `status === "completed"` 扩展为 `|| status.progress >= 100`
- **FE-1 stage → 文案**: `STAGE_LABEL` 映射表 `story_generation/character_design/character_ready/screenplay/storyboard/image_generation/bgm/music` → 精准中文，用 `resolvePhaseTitle()` 决定 `<h1>` 标题
- **FE-2 全列表 dedup**: `CreateContext.tsx:228-248` `generationLog.some((e) => e.message === msg)` 替代原 lastLog 对比
- **FE-3 直接信任 progress**: `StageC.tsx:224` text-gen 用 `status.progress > 0 ? status.progress : simulated`，shot-gen 直接用 `status.progress`

### 对 API 契约的依赖（已确认已有）

- `GET /api/projects/:pid/chapters/1/status` 必须返回 `stage` 字段（当前 `app/api/chapters.py:151-157` 已返回 `job.current_stage`）
- `GET /api/projects/:pid/generation-result` 必须在 job.status === "completed" 后 200 返回 shots 数据

---

## Wave 3 Step 6 — BGM Player (2026-04-21)

**新组件**: `BgmPlayer.tsx` 在 StageD 预览页底部（shot 序列下方）

**API 调用**（与 @backend Step 5 契约对齐）:
- GET `/api/projects/:pid/chapters/:cn/bgm` — 获取 BGM 信息
- POST `/api/projects/:pid/chapters/:cn/bgm/regenerate` — 重新生成（+10 credits）
- POST `/api/projects/:pid/chapters/:cn/bgm/change-meta` — 换一首（+5 credits）
- PATCH `/api/projects/:pid/chapters/:cn/bgm/volume` — 调音量（300ms debounce）

**5 个 UI 状态**: idle / loading / generating（2-5min）/ ready（全功能）/ error

**Context state**: `state.bgmPlayer` 里有 url/volume/meta_version/credits/isPlaying/loadingState 等字段

## TASK-STAGED-V2 前端变更（其他 Agent 需要知道）

- **调整画面**: 新增输入框 + 确认按钮，发 POST regenerate 带 `{ adjustment_intent: "让她笑" }`
- **重新生成**: POST regenerate 无 body = re-roll
- **编辑文字**: 改为编辑 `text_overlay.chinese_text`（不是 narration_segment），PATCH body `{ chinese_text: string }`
- **删除**: DELETE 先成功再 dispatch，软删除
- **提示文字**: 重新生成按钮下方 "保持相同场景，产生不同构图变化"
- **textType="none"**: 隐藏编辑区域（空镜头无文字可编辑）
- **旁白只读**: narration 显示但不可编辑

---

## R6 前端变更（其他 Agent 需要知道）

- **R6-1**: mood 已在 confirm-outline 中发送（排查确认已有）
- **R6-2**: selected_ending 改为 append 到 plot_points 末尾（不再替换）
- **R6-3**: confirm 后立即 onConfirm() 切换场景确认，API 后台异步，不阻塞 UI
- **R6-4**: 角色+场景倒计时 10→20 秒

---

## R5 前端变更（其他 Agent 需要知道）

- **R5-1 completedRef 防重复**: shot-gen 轮询的 `completed` 分支现在用 `completedRef` 保护，只执行一次（与 `confirmedRef` 同模式）。`/generation-result` 只请求一次，消除大量 OPTIONS preflight，跳转预览不再延迟 1-2 分钟。
- **R5-2 100% 显示"即将完成"**: `progress >= 100` 时预估时间文案由"预计还需约 X 分钟"改为"即将完成"。

---

## R4 前端变更（其他 Agent 需要知道）

- **R4-1 confirm-characters API**: CharacterPreview 倒计时结束/手动确认都会调 `POST /projects/{projectId}/confirm-characters`（Bearer token），失败静默继续
- **R4-2 adjust 失败修复**: catch 中清除 regeneratingId + adjustingId + toast 报错
- **R4-3 cocoa tip**: "喝可可" 仅在 text-gen 阶段显示，其他阶段不显示

---

## R3 前端变更（其他 Agent 需要知道）

- **F-1 角色调整读取修复**: apiFetch 类型从顶层 description 改为 result.character.description_zh || result.character.description
- **F-2 模拟早期进度**: text-gen 阶段前 60 秒，前端以 12s/1% 模拟进度（最高 5%），真实进度到达后 max() 切换
- **F-3 description_zh passthrough**: projects.py generate-outline 端点新增 description_zh 字段传递，前端 OutlineScene 新增 description_zh? 可选字段

---

## R2 前端变更（其他 Agent 需要知道）

- **`character_ready` 适配**: text-gen 轮询检测 `stage === "character_ready"` 触发角色预览（fallback `completed`）
- **CONTINUE_GENERATION**: shot-gen 阶段用新 action 不重置 progress
- **friendlyError**: SQL/pymysql 错误自动替换为友好文案
- **"喝可可"固定 + 19 条轮播**: FIXED_TIP 常量 + CAROUSEL_TIPS 数组
- **后端估时**: 优先用 `estimated_remaining_seconds`，fallback 线性外推
- **角色调整**: 调真实 API `/characters/{id}/adjust`，失败 fallback mock

## 当前状态: TASK-BUGFIX-STAGEC 完成，等 PM Review

### Fix 3-A (P0): StageC 角色预览检查点

StageC.tsx L80 的 stage 判断从 `"generating_images"` 改为 `"image_generation"`，与后端 pipeline_orchestrator.py:690 发送的值一致。L79 注释同步更新。

### Fix 3-B (P1): 进度日志去重

CreateContext.tsx 的 `UPDATE_GENERATION_PROGRESS` reducer 现在会比对新消息与 `generationLog` 最后一条的 `message`，相同则不追加（仅更新 progress 和 message 状态）。这解决了 2 秒轮询导致日志重复 7-8 行的问题。

**改动文件**: StageC.tsx + CreateContext.tsx（仅这 2 个）

**构建**: 20 路由，0 错误


---

## 🆕 TASK-T5-FIXBATCH-R6 子任务 2 完成 (2026-04-27 17:55)

**Stage E dashboard 详情页已修 (StoryDetailContent.tsx)**:

- **@backend**: 无需额外改动。前端已对接 `/projects/{id}` (confirmed_outline)、`/chapters/1/storyboard` (shots)、`/chapters/1/story` (characters)、`/chapters/1/bgm` (BGM)。
- **@tester**: 可测试 T5 项目 (uuid=283bd407) 在 dashboard 入口是否：
  1. 显示 loading spinner（不再"故事不存在"）
  2. 加载 18 shots + 缩略图有图
  3. summary 是 200 字大纲（不是短标题）
  4. 情绪基调显示"感人"
  5. 角色显示 silhouette（T5 老数据无 portrait）
  6. BGM 可播放
- **BGM 接入方式**: 详情页不用 BgmPlayer.tsx（该组件依赖 CreateContext），用 `<audio controls>` 内联实现，fetchBgmInfo() 触发加载
- **image URL 处理**: `/static/...` 路径 → `SERVER_BASE + url` (`http://127.0.0.1:8000/static/...`)

---

## 🆕 TASK-T5-FIXBATCH 完成 (2026-04-27 PM 代更)

**对其他 agent 的影响**:

- **@backend (UX-1 配合)**: 前端已接好 `character.portraitUrl` 字段读取逻辑。Backend Stage 2 完成后需要在 `chapter.characters_json` 中注入 `portrait_url` 字段（值为 `/static/outputs/{uuid}/character_refs/{char_id}_portrait.png`），Stage C 才能显示真实 portrait。
- **@backend (UX-11 配合)**: 前端 redirect 三合一触发（status="completed" 或 stage="completed" 或 progress>=100），backend Stage 6 完成后立即发任一信号即可触发。
- **@tester**: T6 测试时观察 ETA 应该单调下降（不许涨），大标题随 stage 自动切换，Stage C 应显示真 portrait。
- **@ai-ml**: 无影响（前端只是渲染，不参与 AI 决策）
- **@devops**: npm build OK，可正常打包部署

**未碰**: BgmPlayer.tsx (T5 测试 UI 没问题)、其他 components


---

## 2026-04-30 11:00 给同事（PM 代更）

Wave 5.1 新加 hook `useStageLock` (frontend/src/hooks/useStageLock.ts)。D.14 三处 banner（StageB/StageC outline/characters/scenes）已实施 — 用户在 generationStatus="generating"|"complete" 时这些页面自动锁定，不能误改。

---

## D.19 + D.20 黑屏 hotfix 双件套 [2026-04-30]

**给所有同事**: outline 阶段黑屏问题已彻底关闭。CreateContent.tsx hydrate 现在分两阶段健壮:

1. project endpoint fail → notFound=true (这是真"项目不存在")
2. chapter 3 endpoints (status/storyboard/story) 在 pre-confirm-outline 时 404 是 routine，前端 .catch 吞掉返默认 — 不再误判
3. outline=null 自动调幂等 generate-outline 恢复 (Backend Option C 已配合，零 LLM 成本)
4. StageB 加 loading spinner，避免 outline 还在 hydrate 时空白渲染

**给 backend**: 现链路依赖 ProjectDetail.raw_outline 字段 + generate-outline 幂等。如未来这两个缺一前端会回退到调真 LLM (¥0.3-0.5/次)，请勿移除。

**给 devops**: 部署需重启 frontend 容器/进程，否则旧 build 仍在跑 (pid 36674 vs hotfix mtime 教训)。

---

## 2026-05-09 17:00 — B36+B27+B28+B37 影响 (PM 代写)

**对所有 agent**:
- StageC 不再渲染空白 (B36 hasCharacters 门控 + 占位符 UI)
- timeout 错误页改"刷新页面，继续等待" + "返回工作台" 双按钮 (B28，不再自动 fallback /outline)
- 7 文件加 console 日志 ([API] / [createUrl] / [Reducer] / [Auth] / [StageB] / [StageD] / [BgmPlayer])

**对 @backend**:
- frontend timeout=120s + slow warning 15s 不变
- BUILD_ID `zjKZpzY23BhjDBR5RLX7F` (16:58)
- frontend PID 68973 (17:08 重启)

---

## 2026-05-11 10:48 — B36 v3+B42+B44+B46 完整修复（PM 代写）

**对所有 agent**:
- frontend hydrate 现在兼容 backend confirmed_outline_json 真字段名:
  - `characters_overview` (B36 v3) / `ending_options` (B42 衍生) / scenes 从 chapter.scenes_json
- StageD 显示 safety_advice 详情（B44）+ partial_failure 红色警告（B46）+ ScenePreview hasScenes 门控（B42）

**对 @backend**:
- frontend 已 ready B44 + B46 API 契约：GET /chapters/{n}/status 用 `failed_shot_count`，storyboard shots[*] 用 `safety_advice/success/error/error_kind`
- 后端必须真返这些字段才会显示警告/safety UI

**新 BUILD_ID**: `CDKVfwbPoTu04NXtBsdFS` (10:48)

---

## 2026-05-11 17:18 Wave 5（PM 代写）

**对 @backend**: B49 API 契约 — 期望 GET /projects/{uuid} 真含 `characters_confirmed` (Backend Wave 5 已加 ✅)
**新 BUILD_ID**: `nyVs1UIUpv8EcHThyi1I6`
